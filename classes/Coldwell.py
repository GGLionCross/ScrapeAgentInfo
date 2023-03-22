from python_utils import cprint
from selenium_utils import Base, Proxy, Wait
from selenium.webdriver.common.by import By
from classes.Agents import Agent, Agents
import datetime
import os
import re

class Coldwell:
    __BASE_URL = "https://www.coldwellbanker.com"
    
    # Column Headers
    __COL_LOCATION = "Location"
    __COL_SOURCE = "Source"
    __COL_SCRAPE_DATE = "Scrape Date"
    __COL_NAME_FULL = "Full Name"
    __COL_NAME_FIRST = "First Name"
    __COL_NAME_LAST = "Last Name"
    __COL_DRE = "DRE"
    __COL_PHONE = "Phone"
    __COL_SOLD = "# Sold"
    __COL_RATING = "Rating / 5"
    __COL_REVIEWS = "# Reviews"

    def __init__(self, user_data_path, profile_path, locations = [], output_csv = False, timeout_default=10):
        # ! Page loads really slowly. May need to implement a different load strategy such as "eager".
        # ! Do more research!
        options = {
            "user_data_path": user_data_path,
            "profile_path": profile_path
        }
        capabilities = {
            "page_load_strategy": "eager"
        }
        base = Base(options=options, capabilities=capabilities)
        self.driver = base.initialize_driver()
        self.wait = Wait(self.driver, timeout_default)
        self.locations = locations
        self.output_csv = output_csv

    def search_location(self, location):
        cprint("<y>Page can take a minute to load...")
        base_url = f"{Coldwell.__BASE_URL}/real-estate-agents/city"
        url = f"{base_url}/{location['id']}"
        self.driver.get(url)
        cprint(f"Loading <c>{location['city']}<w> agents...")

    def get_profile_urls(self):
        xpath = "//a[@class='agent-link']"
        links = self.wait.for_all_elements_located((By.XPATH, xpath))
        urls = []
        cprint(f"Retrieving <y>{len(links)}<w> links...")
        for i in range(0, len(links)):
            urls.append(links[i].get_attribute("href"))
            if (i + 1) % 100 == 0 or i + 1 == len(links):
                cprint(f"Retrieved <y>{i + 1} / {len(links)}<w> links.")
        return urls
    
    def go_to_profile(self, profile_url):
        self.driver.get(profile_url)

        # Wait for agent name
        xpath = "//h1[@itemprop='name']"
        self.wait.for_element_located((By.XPATH, xpath))

    def get_agent_name(self):
        xpath = "//h1[@itemprop='name']"
        element = self.driver.find_element(By.XPATH, xpath)
        return element.get_attribute("textContent")
    
    def get_agent_dre(self):
        try:
            xpath = "//div[@class='agent-heading']/span"
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.get_attribute("textContent")
            result = re.search(r"#\d+", text)
            return result.group(0)
        except:
            return ""
        
    def get_agent_phone(self):
        try:
            xpath = "//div[@itemprop='telephone']/a"
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.get_attribute("textContent")

            # Change format from ###.###.#### to (###) ###-####
            pattern = re.compile(r"(\d{3})\.(\d{3})\.(\d{4})")
            result = pattern.sub(r"(\1) \2-\3", text)
            return result
        except:
            return ""
    
    def get_agent_sold(self):
        try:
            xpath = "//h2[text()='Sold Homes']/following-sibling::p"
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.get_attribute("textContent")
            result = re.search(r"\d+(?=\shomes)", text)
            return result.group(0)
        except:
            return ""
    
    def get_agent_rating(self):
        try:
            xpath = "//span[@itemprop='ratingValue']"
            element = self.driver.find_element(By.XPATH, xpath)
            return element.get_attribute("textContent")
        except:
            return ""
        
    def get_agent_reviews(self):
        try:
            xpath = "//h3[@id='showingHeading']"
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.get_attribute("textContent")
            result = re.search(r"\d+", text)
            return result.group(0)
        except:
            return ""


    def scrape(self):
        cprint(f"Scraping <g>{Coldwell.__BASE_URL}<w>...")

        # Make sure scrape date is uniform among all records for this run
        scrape_date = datetime.date.today()
        
        # Format date to mm/dd/yyyy
        scrape_date = scrape_date.strftime("%m/%d/%Y")

        # Iterate over locations
        for loc in self.locations:
            cprint(f"Scraping agents for location: <c>{loc['city']}<w>...")
            data = Agents([
                Coldwell.__COL_LOCATION,
                Coldwell.__COL_SOURCE,
                Coldwell.__COL_SCRAPE_DATE,
                Coldwell.__COL_NAME_FULL,
                Coldwell.__COL_NAME_FIRST,
                Coldwell.__COL_NAME_LAST,
                Coldwell.__COL_DRE,
                Coldwell.__COL_PHONE,
                Coldwell.__COL_SOLD,
                Coldwell.__COL_RATING,
                Coldwell.__COL_REVIEWS
            ])

            self.search_location(loc)

            # Get the list of urls to iterate over
            urls = self.get_profile_urls()

            cprint(f"<c>{loc['city']}<w> - <y>Agent 0 / { len(urls) }")
            for i in range(0, len(urls)):
                self.go_to_profile(urls[i])

                # Gather info on agent profile page
            
                full_name = self.get_agent_name()
                first_name = full_name.split(" ")[0]
                last_name = full_name.split(" ")[-1]
                dre = self.get_agent_dre()
                phone = self.get_agent_phone()
                sold = self.get_agent_sold()
                rating = self.get_agent_rating()
                reviews = self.get_agent_reviews()

                # Put all the agent data into a props object
                props = {
                    Coldwell.__COL_LOCATION: loc["city"],
                    Coldwell.__COL_SOURCE: Coldwell.__BASE_URL,
                    Coldwell.__COL_SCRAPE_DATE: scrape_date,
                    Coldwell.__COL_NAME_FULL: full_name,
                    Coldwell.__COL_NAME_FIRST: first_name,
                    Coldwell.__COL_NAME_LAST: last_name,
                    Coldwell.__COL_DRE: dre,
                    Coldwell.__COL_PHONE: phone,
                    Coldwell.__COL_SOLD: sold,
                    Coldwell.__COL_RATING: rating,
                    Coldwell.__COL_REVIEWS: reviews
                }

                # Pass the props to the Agent class
                data.add_agent(Agent(props))

                cprint(f"<c>{loc['city']}<w> - <y>Agent { i + 1 } / { len(urls) }")

            # Write all of agent data for each location into a csv/txt file
            os.makedirs("agent_files/coldwell", exist_ok=True)

            if self.output_csv:
                f = open(f"agent_files/coldwell/{loc['city']}.csv", "w", encoding="utf-8")
                f.write(data.get_agents_as_csv_string())
            else:
                f = open(f"agent_files/coldwell/{loc['city']}.txt", "w")
                f.write(data.get_agents_as_txt_string())
            f.close()
        
        cprint(f"Finished scraping <g>{Coldwell.__BASE_URL}<w>.")
