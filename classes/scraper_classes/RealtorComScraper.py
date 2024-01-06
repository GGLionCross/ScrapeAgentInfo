from python_utils import cprint, get_last_id_in_csv_file, get_todays_date
from selenium_utils import SeleniumBase
from selenium.webdriver.common.by import By
from classes.scraper_classes.common.agents import Agents
import os


# Class for scraping realtor.com
class RealtorComScraper:
    __BASE_URL = "https://www.realtor.com"
    __PREFIX__ = "realtor_com"

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

    def __init__(
        self,
        chrome_options: dict,
        cookies: list,
        bmp_options: dict,
        locations: list,
        timeout_default: int = 10,
    ):
        self.__b = SeleniumBase(
            chrome_options=chrome_options,
            bmp_options=bmp_options,
            timeout_default=timeout_default,
        )
        self.__dr = self.__b.get_driver()
        self.__bmp = self.__b.get_bmp()
        self.__loc = locations
        self.__cookies = cookies

    def close(self):
        self.__b.close()

    def transform_location(self, location):
        # Transforms "Los Angeles, CA" to "los-angeles_ca"
        # This transformation is necessary for getting to the right
        #   webpage within realtor.com
        loc = location.lower()
        loc = loc.replace(", ", "_")
        loc = loc.replace(" ", "-")
        return loc

    def search_location(self, location):
        base_url = f"{RealtorComScraper.__BASE_URL}/realestateagents"
        loc_transformed = self.transform_location(location)
        loc_url = f"{base_url}/{loc_transformed}"
        self.__b.set_referer(loc_url)
        self.__b.visit_with_delay(loc_url)

    def get_agent_count(self, responses: list):
        # Get HAR data after loading all page requests
        print(responses)
        return

    def get_page_count(self):
        xpath = '//div[@role="navigation"]/a[position() = last() - 1]'
        last_page = self.__dr.find_element(By.XPATH, xpath)
        return int(last_page.get_attribute("textContent"))

    def get_agents_on_page(self):
        xpath = '//div[@data-testid="component-agentCard"]'
        return self.__dr.find_elements(By.XPATH, xpath)

    def next_page(self, location, page):
        try:
            xpath = '//a[text()="Next"]'
            next = self.__dr.find_element(By.XPATH, xpath)
            next.click()
        except:
            base_url = f"{RealtorComScraper.__BASE_URL}/realestateagents"
            location_url = self.transform_location(location)
            self.__dr.get(f"{base_url}/{location_url}/pg-{page}")

    def scrape(self):
        cprint(f"<g>Scraping {RealtorComScraper.__BASE_URL}...")

        # Record scrape_date so we know how "fresh" the data is
        scrape_date = get_todays_date()

        # Iterate over locations
        for loc in self.__loc:
            # Record network traffic on page load
            self.__bmp.start_har(f"{RealtorComScraper.__PREFIX__}_{loc}")

            self.search_location(loc)

            # self.__b.add_cookies(self.__cookies)

            self.__bmp.wait_for_response("search?")

            responses = self.__bmp.get_responses("search?")

            agent_count = self.get_agent_count(responses)

            return
            agents = Agents(
                [
                    RealtorComScraper.__COL_LOCATION,
                    RealtorComScraper.__COL_SOURCE,
                    RealtorComScraper.__COL_SCRAPE_DATE,
                    RealtorComScraper.__COL_ID,
                    RealtorComScraper.__COL_NAME_FULL,
                    RealtorComScraper.__COL_NAME_FIRST,
                    RealtorComScraper.__COL_NAME_LAST,
                    RealtorComScraper.__COL_PHONE,
                    RealtorComScraper.__COL_BROKERAGE,
                ]
            )

            cprint(f"<c>Found {agent_count} agents for {loc}.")

            try:
                page_count = self.get_page_count()
            except:
                cprint(f"<c>{loc} - 0 pages")
                continue

            # Create file for writing
            file_name = f"agent_data/{RealtorComScraper.__PREFIX__}/{loc}.csv"
            os.makedirs(f"agent_data/{RealtorComScraper.__PREFIX__}", exist_ok=True)
            output = open(file_name, "a+", encoding="utf-8")

            # Grab the last id of the CSV file
            last_id = get_last_id_in_csv_file(file_name, RealtorComScraper.__COL_ID)

            if last_id == -1:
                cprint(f"<c>{loc} - Agent 0 / {agent_count}")
                output.write(agents.get_headers_as_csv_string())
            elif last_id + 1 != agent_count:
                cprint(f"<c>{loc} - Continuing from Agent {last_id + 1}")

            i = 0
            # Iterate over pages
            for p in range(1, page_count + 1):
                cprint(f"<c>{loc} - Page: {p} / {page_count}")
                agents_on_page = self.get_agents_on_page()

                # Iterate over agents
                for a in agents_on_page:
                    if i < last_id:
                        i += 1
                        continue

                    cprint(f"<c>{loc} - Agent {i + 1} / {agent_count}")

                    name_xpath = './/div[contains(@class, "agent-name")]'
                    full_name = a.find_element(By.XPATH, name_xpath).get_attribute(
                        "textContent"
                    )
                    first_name = full_name.split(" ")[0]
                    last_name = full_name.split(" ")[-1]
                    try:
                        brokerage_xpath = './/div[contains(@class, "agent-group")]/span'
                        brokerage = a.find_element(
                            By.XPATH, brokerage_xpath
                        ).get_attribute("textContent")
                    except:
                        brokerage = ""
                    try:
                        phone_xpath = './/div[contains(@class, "agent-phone")]'
                        phone = a.find_element(By.XPATH, phone_xpath).get_attribute(
                            "textContent"
                        )
                    except:
                        phone = ""
                    agent = {
                        RealtorComScraper.__COL_LOCATION: loc,
                        RealtorComScraper.__COL_SOURCE: RealtorComScraper.__BASE_URL,
                        RealtorComScraper.__COL_SCRAPE_DATE: scrape_date,
                        RealtorComScraper.__COL_ID: i,
                        RealtorComScraper.__COL_NAME_FULL: full_name,
                        RealtorComScraper.__COL_NAME_FIRST: first_name,
                        RealtorComScraper.__COL_NAME_LAST: last_name,
                        RealtorComScraper.__COL_PHONE: phone,
                        RealtorComScraper.__COL_BROKERAGE: brokerage,
                    }

                    output.write(agents.get_agent_as_csv_string(agent))

                    i += 1

                # After iterating over agents, go to next page
                if p < page_count:
                    self.next_page(loc, p + 1)

            cprint(f"<g>Finished scraping {RealtorComScraper.__BASE_URL}.")
