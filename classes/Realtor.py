from python_utils import cprint
from selenium_utils import Base, Wait
from selenium.webdriver.common.by import By
from classes.Agents import Agent, Agents

# Class for scraping realtor.com
class Realtor:
  def __init__(self, user_data_path, profile_path, locations = [], output_csv = False, timeout_default=10):
    options = {
      "user_data_path": user_data_path,
      "profile_path": profile_path
    }
    base = Base(options=options)
    self.driver = base.initialize_driver()
    self.wait = Wait(self.driver, timeout_default)
    self.locations = locations
    self.output_csv = output_csv

  def transform_location(self, location):
    # Transforms 'Los Angeles, CA' to 'los-angeles_ca'
    # This transformation is necessary for getting to the right
    #   webpage within realtor.com
    loc = location.lower()
    loc = loc.replace(", ", "_")
    loc = loc.replace(" ", "-")
    return loc
  
  def search_location_on_realtor(self, location):
    base_url = "https://www.realtor.com/realestateagents"
    location_url = self.transform_location(location)
    self.driver.get(f"{base_url}/{location_url}")
  
  def get_page_count(self):
    xpath = "//div[@role='navigation']/a[position() = last() - 1]"
    last_page = self.driver.find_element(By.XPATH, xpath)
    return int(last_page.text)
  
  def get_agents_on_page(self):
    xpath = "//div[@data-testid='component-agentCard']"
    return self.driver.find_elements(By.XPATH, xpath)
  
  def next_page(self, location, page):
    try:
      xpath = "//a[text()='Next']"
      next = self.driver.find_element(By.XPATH, xpath)
      next.click()
    except:
      base_url = "https://www.realtor.com/realestateagents"
      location_url = self.transform_location(location)
      self.driver.get(f"{base_url}/{location_url}/pg-{page}")

  def scrape(self):
    cprint("<g>Scraping realtor.com...")
    
    # Iterate over locations
    for loc in self.locations:
      self.search_location_on_realtor(loc)
      agents = Agents([
        "Location",
        "Name",
        "First Name",
        "Last Name",
        "Brokerage",
        "Phone",
        "Sold"
      ])
      try:
        page_count = self.get_page_count()
      except:
        cprint(f"<c>{loc} - 0 pages")
        continue

      # Iterate over pages
      for p in range(1, page_count + 1):
        cprint(f"<c>{loc} - Page: {p} / {page_count}")
        agents_on_page = self.get_agents_on_page()

        # Iterate over agents
        for a in agents_on_page:
          name_xpath = ".//div[contains(@class, 'agent-name')]"
          full_name = a.find_element(By.XPATH, name_xpath).get_attribute("textContent")
          first_name = full_name.split(" ")[0]
          last_name = full_name.split(" ")[-1]
          try:
            brokerage_xpath = ".//div[contains(@class, 'agent-group')]/span"
            brokerage = a.find_element(By.XPATH, brokerage_xpath).get_attribute("textContent")
          except:
            brokerage = ""
          try:
            phone_xpath = ".//div[contains(@class, 'agent-phone')]"
            phone = a.find_element(By.XPATH, phone_xpath).get_attribute("textContent")
          except:
            phone = ""
          try:
            sold_xpath = ".//div[contains(text(), 'Sold')]/span"
            sold = a.find_element(By.XPATH, sold_xpath).get_attribute("textContent")
          except:
            sold = ""
          props = {
            "Location": loc,
            "Name": full_name,
            "First Name": first_name,
            "Last Name": last_name,
            "Brokerage": brokerage,
            "Phone": phone,
            "Sold": sold
          }
          agents.add_agent(Agent(props))

        if p < page_count:
          self.next_page(loc, p + 1)

      if self.output_csv:
        f = open(f"agent_files/Realtor.com/{loc}.csv", "w", encoding="utf-8")
        f.write(agents.get_agents_as_csv_string())
      else:
        f = open(f"agent_files/Realtor.com/{loc}.txt", "w")
        f.write(agents.get_agents_as_txt_string())
      f.close()
    cprint("<g>Finished scraping realtor.com!")