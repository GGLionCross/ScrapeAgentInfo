from python_utils import cprint, get_last_id_in_csv_file, get_todays_date
from selenium_utils import Base, Proxy, Wait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from .common.agents import Agents
import json
import os
import urllib.parse

# Class for scraping kw.com
class KellerWilliams:
    __BASE_URL = "https://www.kw.com"

    # Column Headers
    __COL_LOCATION = "Location"
    __COL_SOURCE = "Source"
    __COL_SCRAPE_DATE = "Scrape Date"
    __COL_ID = "Id"
    __COL_NAME_FULL = "Full Name"
    __COL_NAME_FIRST = "First Name"
    __COL_NAME_LAST = "Last Name"
    __COL_PHONE = "Phone"
    __COL_EMAIL = "Email"

    def __init__(self, user_data_path, profile_path, locations = [], timeout_default=10):
        # Set up proxy
        self.proxy = Proxy()
        self.proxy.start_server()
        self.proxy.start_client()

        # Set up selenium
        options = {
            "user_data_path": user_data_path,
            "profile_path": profile_path,
            "proxy_url": self.proxy.proxy_url()
        }
        base = Base(options=options)
        self.driver = base.initialize_driver()

        # Selenium helper classes
        self.actions = ActionChains(self.driver)
        self.wait = Wait(self.driver, timeout_default)

        self.locations = locations

    def transform_location(self, location):
        # Transforms 'Los Angeles, CA' to 'CA/Los%20Angeles/'
        # This transformation is necessary for getting to the right
        #   webpage within realtor.com
        city, state = location.split(", ")
        return urllib.parse.quote(f"{state}/{city}")
  
    def search_location(self, location):
        base_url = f"{KellerWilliams.__BASE_URL}/agent/search"
        location_url = self.transform_location(location)
        self.driver.get(f"{base_url}/{location_url}")

    def get_agent_count(self):
        xpath = "//div[contains(@class,'totalCount')]"
        element = self.wait.for_element_located((By.XPATH, xpath))
        count = ''.join(filter(str.isdigit, element.text))
        count = int(count)
        return count
  
    def load_all_agents(self):
        agent_count = self.get_agent_count()

        # Grab agent cards on page
        xp_agents = "//div[@class='AgentCard']"
        agents = self.wait.for_all_elements_located((By.XPATH, xp_agents))

        # If current agents on page is less than index, scroll down.
        while agent_count > len(agents):
            # Scroll down to last agent loaded and load more agents if needed
            self.actions.move_to_element(agents[-1]).perform()
            agents = self.driver.find_elements(By.XPATH, xp_agents)

        return
    
    def get_agent_urls(self, har):
        # Filter the HAR data for network requests that have "graphql" in the url
        urls = []
        for entry in har["log"]["entries"]:
            if "graphql" in entry["request"]["url"]:
                try:
                    content = json.loads(entry["response"]["content"]["text"])
                    query = content["data"]["SearchAgentQuery"]
                    results = query["result"]["agents"]["edges"]

                    for result in results:
                        urls.append(result["node"]["id"])
                except:
                    continue
        return urls
    
    def load_agent_profile(self, profile_url):
        base_url = f"{KellerWilliams.__BASE_URL}/agent"
        url = f"{base_url}/{profile_url}"
        loaded = False
        while loaded == False:
            self.driver.get(url)
            try:
                xpath = "//div[@class='AgentContent__name']"
                self.wait.for_element_located((By.XPATH, xpath))
                loaded = True
            except:
                loaded = False

    def get_agent_name(self):
        xpath = "//div[@class='AgentContent__name']"
        name = self.wait.for_element_located((By.XPATH, xpath))
        return name.get_attribute("textContent")

    def get_agent_phone(self):
        try:
            xpath = "//div[@class='AgentInformation__phoneMobileNumber']"
            phone = self.driver.find_element(By.XPATH, xpath)
            return phone.get_attribute("textContent")
        except:
            return ""
  
    def get_agent_email(self):
        try:
            xpath = "//a[@aria-label='Agent E-mail']"
            email = self.driver.find_element(By.XPATH, xpath)
            return email.get_attribute("textContent")
        except:
            return ""
  
    def scrape(self):
        cprint(f"Scraping <g>{KellerWilliams.__BASE_URL}<w>...")

        # Record scrape_date so we know how "fresh" the data is
        scrape_date = get_todays_date()

        # Iterate over locations
        for loc in self.locations:
            agents = Agents([
                KellerWilliams.__COL_LOCATION,
                KellerWilliams.__COL_SOURCE,
                KellerWilliams.__COL_SCRAPE_DATE,
                KellerWilliams.__COL_ID,
                KellerWilliams.__COL_NAME_FULL,
                KellerWilliams.__COL_NAME_FIRST,
                KellerWilliams.__COL_NAME_LAST,
                KellerWilliams.__COL_PHONE,
                KellerWilliams.__COL_EMAIL
            ])

            # Start recording HAR data before loading the page
            # so we can grab the first query
            self.proxy.start_har(f"kw_{loc}")

            self.search_location(loc)

            agent_count = self.get_agent_count()

            # Check if urls are saved in agent_urls/kw and confirm if array length matches agent count
            if agents.are_urls_saved("kw", loc) and len(agents.get_saved_urls("kw", loc)) == agent_count:
                cprint(f"Pulling agent urls (<c>agent_urls/kw/{loc}.json<w>)...")
                urls = agents.get_saved_urls("kw", loc)
            else:
                cprint(f"<c>Retrieving agent urls from webpage...")

                urls = []

                # Load all agent queries
                self.load_all_agents()

                # Get the HAR data after loading all agents
                har = self.proxy.har()

                # Get the list of urls to iterate over
                urls = self.get_agent_urls(har)
                

                cprint(f"<y>len(urls): {len(urls)}")

                # Save the links so we won't have to search for them again
                cprint(f"Saving agent urls (<c>agent_urls/kw/{loc}.json<w>)...")
                agents.save_urls("kw", loc, urls)

            # Create file for writing
            file_name = f"agent_data/kw/{loc}.csv"
            os.makedirs("agent_data/kw", exist_ok=True)
            output = open(file_name, "a+", encoding="utf-8")

            # Grab the last id of the CSV file
            last_id = get_last_id_in_csv_file(file_name, KellerWilliams.__COL_ID)

            if last_id == -1:
                cprint(f"<c>{loc} - Agent 0 / { len(urls) }")
                output.write(agents.get_headers_as_csv_string())
            elif last_id + 1 != len(urls):
                cprint(f"<c>{loc}<w> - <y>Continuing from Agent {last_id + 1}")
            
            for i in range(0, len(urls)):
                self.load_agent_profile(urls[i])

                # Gather info on agent profile page
                full_name = self.get_agent_name()
                first_name = full_name.split(" ")[0]
                last_name = full_name.split(" ")[-1]
                phone = self.get_agent_phone()
                email = self.get_agent_email()

                # Add agent info to instance of Agents data object
                agent = {
                    KellerWilliams.__COL_LOCATION: loc,
                    KellerWilliams.__COL_SOURCE: KellerWilliams.__BASE_URL,
                    KellerWilliams.__COL_SCRAPE_DATE: scrape_date,
                    KellerWilliams.__COL_ID: i,
                    KellerWilliams.__COL_NAME_FULL: full_name,
                    KellerWilliams.__COL_NAME_FIRST: first_name,
                    KellerWilliams.__COL_NAME_LAST: last_name,
                    KellerWilliams.__COL_PHONE: phone,
                    KellerWilliams.__COL_EMAIL: email
                }
                output.write(agents.get_agent_as_csv_string(agent))
                cprint(f"<c>{loc} - Agent {i + 1} / {agent_count}")

    def close(self):
        self.driver.close()
        self.driver.quit()
        self.proxy.close()

      
  