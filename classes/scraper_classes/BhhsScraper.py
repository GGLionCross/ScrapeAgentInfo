from python_utils import cprint, get_last_id_in_csv_file, get_todays_date
from classes.Exceptions import BadUrl, RestartScrape
from selenium_utils import SeleniumBase, check_url, exponential_backoff
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from .common import Agents
from math import ceil
import json
import os
import re
import time
import urllib.parse


class BhhsScraper:
    __BASE_URL = "https://www.bhhs.com"
    __VIEW_PER_PAGE = 50

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
        self,
        chrome_options: dict,
        browsermob_proxy_path: str,
        locations: list,
        timeout_default: int = 10,
    ):
        self.__b = SeleniumBase(
            chrome_options=chrome_options,
            bmp_options={"browsermob_proxy_path": browsermob_proxy_path},
            timeout_default=timeout_default,
        )
        self.__dr = self.__b.initialize_driver()
        self.__bmp = self.__b.get_bmp()
        self.__loc = locations

        # Count the number of retries
        self.__retries = 0

    def close(self):
        self.__b.close()

    def transform_location(self, location):
        return urllib.parse.quote(location)

    def search_location(self, location):
        query = f"agent-search-results?city={self.transform_location(location)}"
        url = f"{BhhsScraper.__BASE_URL}/{query}"
        exponential_backoff(self.__dr, url, max_retries=5)
        xp_result_count = (
            "//div[contains(@class,'cmp-search-results-sub-header__results')]/span"
        )
        self.__b.wait_for_element((By.XPATH, xp_result_count))

    def set_view_per_page(self, selection):
        xp_vpp = "//label[text()='View per page']/following-sibling::section/div"
        select = self.__dr.find_element(By.XPATH, xp_vpp)
        select.click()

        xp_option = f"ul/li[@data-value='{selection}']"
        select.find_element(By.XPATH, xp_option).click()

        # Wait 2 seconds to wait for links to populate
        time.sleep(2)

    def get_agent_count(self):
        xp_count = (
            "//div[contains(@class,'cmp-search-results-sub-header__results')]/span"
        )
        count = self.__dr.find_element(By.XPATH, xp_count)
        count = count.get_attribute("textContent").split(" ")[0]
        return int(count)

    def load_all_agents(self, count):
        xp_next = "//a[contains(@class, 'cmp-search-results-pagination__arrow--next')]"
        btn_next = self.__dr.find_element(By.XPATH, xp_next)
        for _ in range(ceil(count / BhhsScraper.__VIEW_PER_PAGE)):
            btn_next.click()

        # Wait 2 seconds to ensure all requests are captured
        time.sleep(2)

    def get_agent_urls(self, har):
        urls = []
        for entry in har["log"]["entries"]:
            if "solrAgentSearchServlet" in entry["request"]["url"]:
                try:
                    content = json.loads(entry["response"]["content"]["text"])
                    results = content["value"]
                    for result in results:
                        urls.append(result["BhhsWebsiteUrl"])
                except:
                    continue
        return urls

    def go_to_profile(self, profile_url):
        # Multiple requests in a short amount of time could give an error
        # Exponential backoff could be a solution to this error
        exponential_backoff(self.__dr, profile_url)

        try:
            # Wait for agent name
            xpath = "//h1[@class='cmp-agent__name']/a"
            self.__b.wait_for_element((By.XPATH, xpath))
        except TimeoutException:
            if check_url(self.__dr, profile_url):
                xp_error = "//h2[contains(text(), '404 Error')]"
                try:
                    # If we receive a 404 Error with same url
                    xp_error = "//h2[contains(text(), '404 Error')]"
                    self.__dr.find_element(By.XPATH, xp_error)
                    cprint("<y>Received 404 Error. Skipping...")
                    raise BadUrl
                except NoSuchElementException:
                    # If bot genuinely fails and we are on the correct link, restart scraper
                    raise TimeoutException
            else:
                # If bot didn't fail but we got redirected, skip this profile
                cprint("<y>Redirected.")
                cprint(f"F: <c>{profile_url}")
                cprint(f"T: <r>{self.__dr.current_url}")
                cprint("<y>Skipping...")
                raise BadUrl

    def get_agent_name(self):
        xpath = "//h1[@class='cmp-agent__name']/a"
        element = self.__dr.find_element(By.XPATH, xpath)
        return element.get_attribute("textContent")

    def get_agent_dre(self):
        try:
            xpath = "//ul[contains(@class,'cmp-agent-details__license')]"
            element = self.__dr.find_element(By.XPATH, xpath)
            text = element.get_attribute("data-license")
            result = re.search(r"\d+", text)
            return "#" + result.group(0)
        except:
            return ""

    def get_agent_phone(self):
        try:
            xpath = "//a[contains(@class,'cmp-agent-details__phone-number')]"
            element = self.__dr.find_element(By.XPATH, xpath)
            return element.get_attribute("textContent")
        except:
            return ""

    def get_agent_email(self):
        try:
            xpath = "//a[contains(@class,'cmp-agent-details__mail')]"
            element = self.__dr.find_element(By.XPATH, xpath)
            return element.get_attribute("textContent")
        except:
            return ""

    def scrape(self):
        cprint(f"Scraping <g>{BhhsScraper.__BASE_URL}<w>...")

        # Record scrape_date so we know how "fresh" the data is
        scrape_date = get_todays_date()

        # Iterate over locations
        for loc in self.__loc:
            cprint(f"Scraping agents for location: <c>{loc}<w>...")
            agents = Agents(
                [
                    BhhsScraper.__COL_LOCATION,
                    BhhsScraper.__COL_SOURCE,
                    BhhsScraper.__COL_SCRAPE_DATE,
                    BhhsScraper.__COL_ID,
                    BhhsScraper.__COL_NAME_FULL,
                    BhhsScraper.__COL_NAME_FIRST,
                    BhhsScraper.__COL_NAME_LAST,
                    BhhsScraper.__COL_DRE,
                    BhhsScraper.__COL_PHONE,
                    BhhsScraper.__COL_EMAIL,
                ]
            )

            page_loaded = False
            while not page_loaded:
                try:
                    self.search_location(loc)

                    # There should be a count on the page
                    # eg. Los Angeles comes up with "1805 Results"
                    count = self.get_agent_count()
                    page_loaded = True

                    # If any of the above fails, refresh the page
                except:
                    page_loaded = False

            # Check if urls are saved in agent_urls/bhhs and confirm if array length matches agent count
            if (
                agents.are_urls_saved("bhhs", loc)
                and len(agents.get_saved_urls("bhhs", loc)) == count
            ):
                cprint(f"Pulling agent urls (<c>agent_urls/bhhs/{loc}.json<w>)...")
                urls = agents.get_saved_urls("bhhs", loc)
            else:
                cprint(f"<c>Retrieving agent urls from webpage...")
                # Start recording HAR data before changing the view per page
                # so we can grab the first query
                self.__bmp.start_har(f"bhhs_{loc}")

                # Set view per page so we don't have to iterate over so many requests
                self.set_view_per_page(BhhsScraper.__VIEW_PER_PAGE)

                # Load all agent queries
                self.load_all_agents(count)

                # Get the HAR data after loading all agents
                har = self.__bmp.har()

                # Get the list of urls to iterate over
                urls = self.get_agent_urls(har)

                # Save the links so we won't have to search for them again
                cprint(f"Saving agent urls (<c>agent_urls/bhhs/{loc}.json<w>)...")
                agents.save_urls("bhhs", loc, urls)

            # Create file for writing
            file_name = f"agent_data/bhhs/{loc}.csv"
            os.makedirs("agent_data/bhhs", exist_ok=True)
            output = open(file_name, "a+", encoding="utf-8")

            # Grab the last id of the CSV file
            last_id = get_last_id_in_csv_file(file_name, BhhsScraper.__COL_ID)

            if last_id == -1:
                cprint(f"<c>{loc} - Agent 0 / { len(urls) }")
                output.write(agents.get_headers_as_csv_string())
            elif last_id + 1 != len(urls):
                cprint(f"<c>{loc} - Continuing from Agent {last_id + 1}")

            # for i in range(last_id + 1, 5): # For testing
            for i in range(last_id + 1, len(urls)):
                # Skip empty urls
                if not urls[i]:
                    cprint(
                        f"<c>{loc}<w> - <y>Agent { i + 1 } / { len(urls) } (empty url)"
                    )
                    continue

                try:
                    self.go_to_profile(urls[i])
                    self.__retries = 0
                except BadUrl:
                    self.__retries = 0
                    continue
                except TimeoutException:
                    if self.__retries >= 3:
                        cprint(
                            f"Scrape failed <r>3<w> times. Skipping url (<y>{urls[i]}<w>)..."
                        )
                        self.__retries = 0
                        continue
                    else:
                        cprint(
                            f"<y>Scrape failed to load. Restarting ({self.__retries + 1})..."
                        )
                        self.__retries += 1
                    raise RestartScrape

                # Gather info on agent profile page
                full_name = self.get_agent_name()
                first_name = full_name.split(" ")[0]
                last_name = full_name.split(" ")[-1]
                dre = self.get_agent_dre()
                phone = self.get_agent_phone()
                email = self.get_agent_email()

                # Put all the agent agents into a props object
                agent = {
                    BhhsScraper.__COL_LOCATION: loc,
                    BhhsScraper.__COL_SOURCE: BhhsScraper.__BASE_URL,
                    BhhsScraper.__COL_SCRAPE_DATE: scrape_date,
                    BhhsScraper.__COL_ID: i,
                    BhhsScraper.__COL_NAME_FULL: full_name,
                    BhhsScraper.__COL_NAME_FIRST: first_name,
                    BhhsScraper.__COL_NAME_LAST: last_name,
                    BhhsScraper.__COL_DRE: dre,
                    BhhsScraper.__COL_PHONE: phone,
                    BhhsScraper.__COL_EMAIL: email,
                }

                output.write(agents.get_agent_as_csv_string(agent))

                cprint(f"<c>{loc}<w> - <y>Agent { i + 1 } / { len(urls) }")
                # End of iterating through agent profiles

            # End of iterating through locations

        cprint(f"Finished scraping <g>{BhhsScraper.__BASE_URL}<w>.")
