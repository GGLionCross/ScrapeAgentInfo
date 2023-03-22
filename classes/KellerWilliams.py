from python_utils import cprint
from selenium_utils import Base, Proxy, Wait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from classes.Agents import Agent, Agents
import json
import os
import urllib.parse

# Class for scraping kw.com
class KellerWilliams:
    def __init__(self, user_data_path, profile_path, locations = [], output_csv = False, timeout_default=10):
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
        self.output_csv = output_csv

    def transform_location(self, location):
        # Transforms 'Los Angeles, CA' to 'CA/Los%20Angeles/'
        # This transformation is necessary for getting to the right
        #   webpage within realtor.com
        city, state = location.split(", ")
        return urllib.parse.quote(f"{state}/{city}")
  
    def search_location(self, location):
        base_url = "https://www.kw.com/agent/search"
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
    
    def load_agent_profile(self, profile_url):
        base_url = "https://www.kw.com/agent"
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
        cprint("Scraping <g>https://www.kw.com/<w>...")

        # Iterate over locations
        for loc in self.locations:
            data = Agents([
                "Location",
                "Full Name",
                "First Name",
                "Last Name",
                "Phone",
               "Email",
                "Source"
            ])

            # HAR options
            # Source: https://medium.com/@jiurdqe/how-to-get-json-response-body-with-selenium-amd-browsermob-proxy-71f10335c66
            har_options = {
                "captureHeaders": True,
                "captureContent": True,
                "captureBinaryContent": True
            }

            # Start recording HAR data before loading the page
            #   so we can grab all the agent data
            self.proxy.start_har(f"kw_{loc}", har_options)

            self.search_location(loc)

            # Scroll all the way to the bottom to load all the agents
            self.load_all_agents()

            # Get agent count for displaying progress
            agent_count = self.get_agent_count()

            # Get the HAR data after loading all agents
            har = self.proxy.har()

            # Filter the HAR data for network requests that have "graphql" in the url
            profile_urls = []
            for entry in har["log"]["entries"]:
                if "graphql" in entry["request"]["url"]:
                    try:
                        content = json.loads(entry["response"]["content"]["text"])
                        query = content["data"]["SearchAgentQuery"]
                        results = query["result"]["agents"]["edges"]

                        for result in results:
                            profile_urls.append(result["node"]["id"])
                    except:
                        continue
            
            for i in range(0, len(profile_urls)):
                self.load_agent_profile(profile_urls[i])

                # Gather info on agent profile page
                full_name = self.get_agent_name()
                first_name = full_name.split(" ")[0]
                last_name = full_name.split(" ")[-1]
                phone = self.get_agent_phone()
                email = self.get_agent_email()

                # Add agent info to instance of Agents data object
                props = {
                    "Location": loc,
                    "Full Name": full_name,
                    "First Name": first_name,
                    "Last Name": last_name,
                    "Phone": phone,
                    "Email": email,
                    "Source": "https://www.kw.com/"
                }
                data.add_agent(Agent(props))
                cprint(f"<c>{loc} - Agent {i + 1} / {agent_count}")
            
            # Write all of agent data for each location into a csv/txt file
            os.makedirs("agent_files/kw", exist_ok=True)

            if self.output_csv:
                f = open(f"agent_files/kw/{loc}.csv", "w", encoding="utf-8")
                f.write(data.get_agents_as_csv_string())
            else:
                f = open(f"agent_files/kw/{loc}.txt", "w")
                f.write(data.get_agents_as_txt_string())
            f.close()



      
  