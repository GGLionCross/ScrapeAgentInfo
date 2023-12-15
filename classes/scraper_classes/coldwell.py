from python_utils import cprint, get_last_id_in_csv_file, get_todays_date
from selenium_utils import SeleniumBase, Proxy, exponential_backoff
from selenium.webdriver.common.by import By
from .common import Agents
import json
import os
import re
import urllib

class Coldwell:
    __BASE_URL = 'https://www.coldwellbanker.com'
    
    # Column Headers
    __COL_LOCATION = 'Location'
    __COL_SOURCE = 'Source'
    __COL_SCRAPE_DATE = 'Scrape Date'
    __COL_ID = 'Id'
    __COL_NAME_FULL = 'Full Name'
    __COL_NAME_FIRST = 'First Name'
    __COL_NAME_LAST = 'Last Name'
    __COL_DRE = 'DRE#'
    __COL_PHONE_M = 'Mobile #'
    __COL_PHONE_O = 'Office #'
    __COL_EMAIL = 'Email'
    __COL_URL = 'Url'

    def __init__(self, user_data_path, profile_path, locations=[], timeout_default=10):
        # Set up proxy
        self.proxy = Proxy()
        self.proxy.start_server()
        self.proxy.start_client()

        options = {
            'user_data_path': user_data_path,
            'profile_path': profile_path,
            'proxy_url': self.proxy.proxy_url()
        }
        capabilities = {
            'acceptInsecureCerts': True
        }
        base = SeleniumBase(options=options, capabilities=capabilities)
        self.base = base
        self.driver = base.get_driver()

        self.timeout_default = timeout_default
        self.locations = locations

    def close(self):
        self.driver.close()
        self.driver.quit()
        self.proxy.close()

    def transform_location(self, location):
        # Transforms "Los Angeles, CA" to "CA/Los%20Angeles/"
        # This transformation is necessary for getting to the right
        #   webpage within realtor.com
        city, state = location.lower().split(', ')
        city = '-'.join(city.split(' '))
        return urllib.parse.quote(f'{state}/{city}')

    def search_location(self, location):
        url = f'{Coldwell.__BASE_URL}/city/'
        url += f'{self.transform_location(location)}/agents'
        exponential_backoff(self.driver, url)
        cprint(f'Loading <c>{location}<w> agents...')

    def get_agent_count(self):
        xp_ctn_count = '//div[@id="header-container"]//h1'
        ctn_count = self.base.wait_for_element((By.XPATH, xp_ctn_count))
        count = ctn_count.get_attribute('textContent')
        count = count.split(' ')[0]
        return int(count)

    def request_all_agents(self):
        # Grab last page number from button
        xp_last = '//nav/ul/li[last() - 1]/button'
        btn_last = self.driver.find_element(By.XPATH, xp_last)
        i_last_page = btn_last.get_attribute('aria-label')
        i_last_page = int(i_last_page.split(' ')[-1])

        # for i in range(2, 3): # Test a single page
        for i in range(2, i_last_page + 1):
            cprint(f'<c>Page {i - 1} / {i_last_page}')
            # Next page
            xp_pg = f'//nav/ul/li/button[@aria-label="Go to page {i}"]'
            btn_pg = self.driver.find_element(By.XPATH, xp_pg)
            btn_pg.click()
            xp_cur = f'//nav/ul/li/button[@aria-label="page {i}"]'
            self.base.wait_for_element((By.XPATH, xp_cur))

        # Go back to page 1 to load first agents.json
        cprint(f'<c>Page {i_last_page} / {i_last_page}')
        xp_pg = f'//nav/ul/li/button[@aria-label="Go to page 1"]'
        btn_pg = self.driver.find_element(By.XPATH, xp_pg)
        btn_pg.click()
        xp_cur = f'//nav/ul/li/button[@aria-label="page 1"]'
        self.base.wait_for_element((By.XPATH, xp_cur))

        return
    
    def transform_phone_number(self, phone_number):
        # Remove the "+1"
        formatted_number = phone_number[2:]

        # Format the phone number in the desired pattern
        formatted_number = '({}) {}-{}'.format(
            formatted_number[:3],
            formatted_number[3:6],
            formatted_number[6:]
        )

        return formatted_number

    def get_agent_data_from_har(self, har):
        # Filter the HAR data for network requests that have 'graphql' in the url
        data = []
        for entry in har['log']['entries']:
            if 'agents.json' in entry['request']['url']:
                content = json.loads(entry['response']['content']['text'])
                results = content['pageProps']['results']['agents']

                for result in results:
                    phone_m = '' if 'cellPhoneNumber' not in result else self.transform_phone_number(result['cellPhoneNumber'])
                    phone_o = '' if 'businessPhoneNumber' not in result else self.transform_phone_number(result['businessPhoneNumber'])
                    email = '' if 'emailAddress' not in result else result['emailAddress']
                    data.append({
                        Coldwell.__COL_NAME_FULL: result['fullName'],
                        Coldwell.__COL_PHONE_M: phone_m,
                        Coldwell.__COL_PHONE_O: phone_o,
                        Coldwell.__COL_EMAIL: email,
                        Coldwell.__COL_URL: f'{Coldwell.__BASE_URL}{result["url"]}'
                    })
        return data
    
    def go_to_profile(self, profile_url):
        # Multiple requests in a short amount of time could give an error
        # Exponential backoff could be a solution to this error
        exponential_backoff(self.driver, profile_url)
    
    def get_agent_dre(self):
        try:
            xpath = '//div[contains(text(), "CalRE")]'
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.get_attribute('textContent')
            result = re.search(r'\d+', text)
            return result.group(0)
        except:
            return ''
        
    def get_agent_phone(self):
        try:
            xpath = '//div[@itemprop="telephone"]/a'
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.get_attribute('textContent')

            # Change format from ###.###.#### to (###) ###-####
            pattern = re.compile(r'(\d{3})\.(\d{3})\.(\d{4})')
            result = pattern.sub(r'(\1) \2-\3', text)
            return result
        except:
            return ''

    def scrape(self):
        cprint(f'Scraping <g>{Coldwell.__BASE_URL}<w>...')

        # Record scrape_date so we know how 'fresh' data is
        scrape_date = get_todays_date()

        # Iterate over locations
        for loc in self.locations:
            cprint(f'Scraping agents for location: <c>{loc}<w>...')
            agents = Agents([
                Coldwell.__COL_LOCATION,
                Coldwell.__COL_SOURCE,
                Coldwell.__COL_SCRAPE_DATE,
                Coldwell.__COL_ID,
                Coldwell.__COL_NAME_FULL,
                Coldwell.__COL_NAME_FIRST,
                Coldwell.__COL_NAME_LAST,
                Coldwell.__COL_DRE,
                Coldwell.__COL_PHONE_M,
                Coldwell.__COL_PHONE_O,
                Coldwell.__COL_EMAIL,
                Coldwell.__COL_URL
            ])

            self.search_location(loc)
            agent_count = self.get_agent_count()

            agent_data = []
            # Check if urls are saved in agent_urls/coldwell and confirm if array length matches agent count
            if agents.are_urls_saved("coldwell", loc):
                agent_data = agents.get_saved_urls("coldwell", loc)
            if len(agent_data) == agent_count:
                cprint(f"Pulling agent data (<c>agent_urls/coldwell/{loc}.json<w>)...")
            else:
                cprint(f"<c>Retrieving agent data from network requests...")

                # Start recording HAR data before requesting agents
                self.proxy.start_har(Coldwell.__BASE_URL)

                self.request_all_agents()

                agent_data = self.get_agent_data_from_har(self.proxy.har())

                if len(agent_data) != agent_count:
                    cprint(f"<y>Warning: len(agent_data) != agent_count")
                    cprint(f"<y>{loc} - len(agent_data): {len(agent_data)}")
                    cprint(f"<y>{loc} - agent_count: {agent_count}")
                    continue
                else:
                    agents.save_urls("coldwell", loc, agent_data)

            # Create file for writing
            file_name = f'agent_data/coldwell/{loc}.csv'
            os.makedirs('agent_data/coldwell', exist_ok=True)
            output = open(file_name, 'a+', encoding='utf-8')

            # Grab the last id of the CSV file
            last_id = get_last_id_in_csv_file(file_name, Coldwell.__COL_ID)

            if last_id == -1:
                cprint(f'<c>{loc} - Agent 0 / { agent_count }')
                output.write(agents.get_headers_as_csv_string())
            elif last_id + 1 != agent_count:
                cprint(f'<c>{loc} - Continuing from Agent {last_id + 1}')

            for i in range(last_id + 1, agent_count):
                self.go_to_profile(agent_data[i][Coldwell.__COL_URL])

                # Gather info on agent profile page
                full_name = agent_data[i][Coldwell.__COL_NAME_FULL]
                first_name = full_name.split(' ')[0]
                last_name = full_name.split(' ')[-1]
                dre = self.get_agent_dre()

                # Put all the agent agents into a props object
                agent = {
                    Coldwell.__COL_LOCATION: loc,
                    Coldwell.__COL_SOURCE: Coldwell.__BASE_URL,
                    Coldwell.__COL_SCRAPE_DATE: scrape_date,
                    Coldwell.__COL_ID: i,
                    Coldwell.__COL_NAME_FULL: full_name,
                    Coldwell.__COL_NAME_FIRST: first_name,
                    Coldwell.__COL_NAME_LAST: last_name,
                    Coldwell.__COL_DRE: dre,
                    Coldwell.__COL_PHONE_M: agent_data[i][Coldwell.__COL_PHONE_M],
                    Coldwell.__COL_PHONE_O: agent_data[i][Coldwell.__COL_PHONE_O],
                    Coldwell.__COL_EMAIL: agent_data[i][Coldwell.__COL_EMAIL],
                    Coldwell.__COL_URL: agent_data[i][Coldwell.__COL_URL]
                }

                output.write(agents.get_agent_as_csv_string(agent))

                cprint(f'<c>{loc} - Agent { i + 1 } / { agent_count }')
                # End of iterating through agent profiles
            
            # End of iterating through locations
        
        cprint(f'Finished scraping <g>{Coldwell.__BASE_URL}<w>.')
