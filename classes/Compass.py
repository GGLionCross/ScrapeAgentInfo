from python_utils import cprint
from selenium_utils import Base, Wait
from selenium.webdriver.common.by import By
from classes.Agents import Agent, Agents
import os
import re

# Class for scraping compass.com
class Compass:
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
    loc = loc.replace(", ", "-")
    loc = loc.replace(" ", "-")
    return loc

  def search_location(self, location):
    self.driver.get("https://www.compass.com/agents/")
    input = self.driver.find_element(By.ID, "downshift-0-input")
    input.send_keys(location)
    location_url = f"locations/{self.transform_location(location)}"
    link = self.wait.until_clickable((By.XPATH, f"//ul//a[contains(@href, '{location_url}')]"))
    link.click()
  
  def get_agents_on_page(self):
    return self.driver.find_elements(By.XPATH, "//div[@class='agentCard']")
  
  def next_page(self):
    next = self.driver.find_element(By.XPATH, "//nav/button[last()]")
    next.click()
  
  def scrape(self):
    cprint("<g>Scraping compass.com...")

    # Iterate over locations
    for loc in self.locations:
      self.search_location(loc)
      agents = Agents([
        "Location",
        "Name",
        "First Name",
        "Last Name",
        "Brokerage",
        "Phone",
        "Email"
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
          full_name = a.find_element(By.XPATH, ".//div[contains(@class, 'agentCard-name')]").get_attribute("textContent")
          full_name = full_name.strip()
          first_name = full_name.split(" ")[0]
          last_name = full_name.split(" ")[-1]
          try:
            brokerage = a.find_element(By.XPATH, ".//div[contains(@class, 'agentCard-title')]").get_attribute("textContent")
          except:
            brokerage = ""
          try:
            phone = a.find_element(By.XPATH, ".//a[contains(@class, 'agentCard-phone')]").get_attribute("textContent")
            phone = phone.strip()
            phone = re.sub("M:\s+", "", phone)
          except:
            phone = ""
          try:
            email = a.find_element(By.XPATH, ".//a[contains(@class, 'agentCard-email')]").get_attribute("textContent")
            email = email.strip()
          except:
            email = ""
          props = {
            "Location": loc,
            "Name": full_name,
            "First Name": first_name,
            "Last Name": last_name,
            "Brokerage": brokerage,
            "Phone": phone,
            "Email": email
          }
          agents.add_agent(Agent(props))

        if p < page_count:
          self.next_page()

      os.makedirs("agent_files/compass.com", exist_ok=True)

      if self.output_csv:
        f = open(f"agent_files/compass.com/{loc}.csv", "w", encoding="utf-8")
        f.write(agents.get_agents_as_csv_string())
      else:
        f = open(f"agent_files/compass.com/{loc}.txt", "w")
        f.write(agents.get_agents_as_txt_string())
      f.close()
    cprint("<g>Finished scraping compass.com!")
