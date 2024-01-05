from python_utils import cprint, get_last_id_in_csv_file, get_todays_date
from selenium_utils import SeleniumBase
from selenium.webdriver.common.by import By
from classes.scraper_classes.common.agents import Agents
import os
import re


# Class for scraping compass.com
class CompassScraper:
    __BASE_URL = "https://www.compass.com"

    # Column Headers
    __COL_LOCATION = "Location"
    __COL_SOURCE = "Source"
    __COL_SCRAPE_DATE = "Scrape Date"
    __COL_ID = "Id"
    __COL_NAME_FULL = "Full Name"
    __COL_NAME_FIRST = "First Name"
    __COL_NAME_LAST = "Last Name"
    __COL_DRE = "DRE"
    __COL_PHONE = "Phone"
    __COL_EMAIL = "Email"

    def __init__(
        self, chrome_options: dict, locations: list, timeout_default: int = 10
    ):
        self.__b = SeleniumBase(
            chrome_options=chrome_options, timeout_default=timeout_default
        )
        self.__dr = self.__b.get_driver()
        self.__loc = locations

    def transform_location(self, location):
        # Transforms 'Los Angeles, CA' to 'los-angeles_ca'
        # This transformation is necessary for getting to the right
        #     webpage within realtor.com
        loc = location.lower()
        loc = loc.replace(", ", "-")
        loc = loc.replace(" ", "-")
        return loc

    def search_location(self, location):
        self.__dr.get(f"{CompassScraper.__BASE_URL}/agents/")
        input = self.__dr.find_element(By.ID, "downshift-0-input")
        input.send_keys(location)
        location_url = f"locations/{self.transform_location(location)}"
        link = self.__b.wait_until_clickable(
            (By.XPATH, f"//ul//a[contains(@href, '{location_url}')]")
        )
        link.click()

    def get_agent_count(self):
        agent_count = self.__dr.find_element(
            By.XPATH, "//h1[contains(@class, 'searchResults-count')]"
        )
        return agent_count.get_attribute("textContent").split(" ")[0]

    def get_page_count(self):
        last_page = self.__dr.find_element(By.XPATH, "//nav/button[last() - 1]")
        return int(last_page.get_attribute("aria-label").split(" ")[-1])

    def get_agents_on_page(self):
        return self.__dr.find_elements(By.XPATH, "//div[@class='agentCard']")

    def next_page(self):
        next = self.__dr.find_element(By.XPATH, "//nav/button[last()]")
        next.click()

    def scrape(self):
        cprint("<g>Scraping compass.com...")

        # Record scrape_date so we know how "fresh" the data is
        scrape_date = get_todays_date()

        # Iterate over locations
        for loc in self.__loc:
            self.search_location(loc)
            agents = Agents(
                [
                    CompassScraper.__COL_LOCATION,
                    CompassScraper.__COL_SOURCE,
                    CompassScraper.__COL_SCRAPE_DATE,
                    CompassScraper.__COL_ID,
                    CompassScraper.__COL_NAME_FULL,
                    CompassScraper.__COL_NAME_FIRST,
                    CompassScraper.__COL_NAME_LAST,
                    CompassScraper.__COL_DRE,
                    CompassScraper.__COL_PHONE,
                    CompassScraper.__COL_EMAIL,
                ]
            )

            try:
                page_count = self.get_page_count()
            except:
                cprint(f"<c>{loc} - 0 pages")
                continue

            # Create file for writing
            file_name = f"agent_data/compass/{loc}.csv"
            os.makedirs("agent_data/compass", exist_ok=True)
            output = open(file_name, "w", encoding="utf-8")

            id = 0
            # Iterate over pages
            for p in range(1, page_count + 1):
                cprint(f"<c>{loc} - Page: {p} / {page_count}")
                agents_on_page = self.get_agents_on_page()

                # Iterate over agents
                for a in agents_on_page:
                    full_name = a.find_element(
                        By.XPATH, ".//div[contains(@class, 'agentCard-name')]"
                    ).get_attribute("textContent")
                    full_name = full_name.strip()
                    first_name = full_name.split(" ")[0]
                    last_name = full_name.split(" ")[-1]
                    try:
                        phone = a.find_element(
                            By.XPATH, ".//a[contains(@class, 'agentCard-phone')]"
                        ).get_attribute("textContent")
                        phone = phone.strip()
                        phone = re.sub("M:\s+", "", phone)
                    except:
                        phone = ""
                    try:
                        email = a.find_element(
                            By.XPATH, ".//a[contains(@class, 'agentCard-email')]"
                        ).get_attribute("textContent")
                        email = email.strip()
                    except:
                        email = ""
                    try:
                        dre = a.find_element(
                            By.XPATH, ".//div[contains(@class, 'agentCard-title')]"
                        )
                        dre = dre.get_attribute("textContent")
                        dre = dre.split("DRE# ")
                        dre = dre[1]
                    except:
                        dre = ""
                    agent = {
                        CompassScraper.__COL_LOCATION: loc,
                        CompassScraper.__COL_SOURCE: CompassScraper.__BASE_URL,
                        CompassScraper.__COL_SCRAPE_DATE: scrape_date,
                        CompassScraper.__COL_ID: id,
                        CompassScraper.__COL_NAME_FULL: full_name,
                        CompassScraper.__COL_NAME_FIRST: first_name,
                        CompassScraper.__COL_NAME_LAST: last_name,
                        CompassScraper.__COL_DRE: dre,
                        CompassScraper.__COL_PHONE: phone,
                        CompassScraper.__COL_EMAIL: email,
                    }

                    output.write(agents.get_agent_as_csv_string(agent))
                    id += 1

                if p < page_count:
                    self.next_page()

        cprint("<g>Finished scraping compass.com!")

    def close(self):
        self.__dr.close()
        self.__dr.quit()
