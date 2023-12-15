from python_utils import cprint, get_last_id_in_csv_file, get_todays_date
from selenium_utils import Base, Wait
from selenium.webdriver.common.by import By
from classes.scraper_classes.common.agents import Agents
import os

# Class for scraping realtor.com
class RealtorCom:
    __BASE_URL = 'https://www.realtor.com'

    # Column Headers
    __COL_LOCATION = "Location"
    __COL_SOURCE = "Source"
    __COL_SCRAPE_DATE = "Scrape Date"
    __COL_ID = "Id"
    __COL_NAME_FULL = "Full Name"
    __COL_NAME_FIRST = "First Name"
    __COL_NAME_LAST = "Last Name"
    __COL_PHONE = "Phone"
    __COL_BROKERAGE = "Brokerage"

    def __init__(self, user_data_path, profile_path, locations = [], timeout_default=10):
        options = {
        'user_data_path': user_data_path,
        'profile_path': profile_path
        }
        base = Base(options=options)
        self.driver = base.initialize_driver()
        self.wait = Wait(self.driver, timeout_default)
        self.locations = locations

    def close(self):
        self.driver.close()
        self.driver.quit()

    def transform_location(self, location):
        # Transforms "Los Angeles, CA" to "los-angeles_ca"
        # This transformation is necessary for getting to the right
        #   webpage within realtor.com
        loc = location.lower()
        loc = loc.replace(', ', '_')
        loc = loc.replace(' ', '-')
        return loc
    
    def search_location(self, location):
        base_url = f'{RealtorCom.__BASE_URL}/realestateagents'
        location_url = self.transform_location(location)
        self.driver.get(f'{base_url}/{location_url}')
    
    def get_agent_count(self):
        xpath = '//*[@id="fullpage-wrapper result-wrapper hidden-xs hidden-xxs"]/div/div[1]/span/span'
        agent_count = self.driver.find_element(By.XPATH, xpath)
        count = filter(str.isdigit, agent_count.get_attribute('textContent'))
        count = ''.join(count)
        return int(count)

    def get_page_count(self):
        xpath = '//div[@role="navigation"]/a[position() = last() - 1]'
        last_page = self.driver.find_element(By.XPATH, xpath)
        return int(last_page.get_attribute('textContent'))
    
    def get_agents_on_page(self):
        xpath = '//div[@data-testid="component-agentCard"]'
        return self.driver.find_elements(By.XPATH, xpath)
    
    def next_page(self, location, page):
        try:
            xpath = '//a[text()="Next"]'
            next = self.driver.find_element(By.XPATH, xpath)
            next.click()
        except:
            base_url = f'{RealtorCom.__BASE_URL}/realestateagents'
            location_url = self.transform_location(location)
            self.driver.get(f'{base_url}/{location_url}/pg-{page}')

    def scrape(self):
        cprint(f'<g>Scraping {RealtorCom.__BASE_URL}...')

        # Record scrape_date so we know how "fresh" the data is
        scrape_date = get_todays_date()
        
        # Iterate over locations
        for loc in self.locations:
            self.search_location(loc)

            agents = Agents([
                RealtorCom.__COL_LOCATION,
                RealtorCom.__COL_SOURCE,
                RealtorCom.__COL_SCRAPE_DATE,
                RealtorCom.__COL_ID,
                RealtorCom.__COL_NAME_FULL,
                RealtorCom.__COL_NAME_FIRST,
                RealtorCom.__COL_NAME_LAST,
                RealtorCom.__COL_PHONE,
                RealtorCom.__COL_BROKERAGE
            ])

            agent_count = self.get_agent_count()

            cprint(f'<c>Found {agent_count} agents for {loc}.')

            try:
                page_count = self.get_page_count()
            except:
                cprint(f'<c>{loc} - 0 pages')
                continue

            # Create file for writing
            file_name = f"agent_data/realtor_com/{loc}.csv"
            os.makedirs("agent_data/realtor_com", exist_ok=True)
            output = open(file_name, "a+", encoding="utf-8")

            # Grab the last id of the CSV file
            last_id = get_last_id_in_csv_file(file_name, RealtorCom.__COL_ID)

            if last_id == -1:
                cprint(f"<c>{loc} - Agent 0 / {agent_count}")
                output.write(agents.get_headers_as_csv_string())
            elif last_id + 1 != agent_count:
                cprint(f"<c>{loc} - Continuing from Agent {last_id + 1}")

            i = 0
            # Iterate over pages
            for p in range(1, page_count + 1):
                cprint(f'<c>{loc} - Page: {p} / {page_count}')
                agents_on_page = self.get_agents_on_page()

                # Iterate over agents
                for a in agents_on_page:

                    if i < last_id:
                        i += 1
                        continue
                    
                    cprint(f"<c>{loc} - Agent {i + 1} / {agent_count}")

                    name_xpath = './/div[contains(@class, "agent-name")]'
                    full_name = a.find_element(By.XPATH, name_xpath).get_attribute('textContent')
                    first_name = full_name.split(' ')[0]
                    last_name = full_name.split(' ')[-1]
                    try:
                        brokerage_xpath = './/div[contains(@class, "agent-group")]/span'
                        brokerage = a.find_element(By.XPATH, brokerage_xpath).get_attribute('textContent')
                    except:
                        brokerage = ''
                    try:
                        phone_xpath = './/div[contains(@class, "agent-phone")]'
                        phone = a.find_element(By.XPATH, phone_xpath).get_attribute('textContent')
                    except:
                        phone = ''
                    agent = {
                        RealtorCom.__COL_LOCATION: loc,
                        RealtorCom.__COL_SOURCE: RealtorCom.__BASE_URL,
                        RealtorCom.__COL_SCRAPE_DATE: scrape_date,
                        RealtorCom.__COL_ID: i,
                        RealtorCom.__COL_NAME_FULL: full_name,
                        RealtorCom.__COL_NAME_FIRST: first_name,
                        RealtorCom.__COL_NAME_LAST: last_name,
                        RealtorCom.__COL_PHONE: phone,
                        RealtorCom.__COL_BROKERAGE: brokerage
                    }
                    
                    output.write(agents.get_agent_as_csv_string(agent))

                    i += 1

                # After iterating over agents, go to next page
                if p < page_count:
                    self.next_page(loc, p + 1)

            cprint(f'<g>Finished scraping {RealtorCom.__BASE_URL}.')