from python_utils import cprint, get_config
from selenium.webdriver.common.by import By
from selenium_utils import Base
from classes.Agents import Agent, Agents

def transform_location(location):
  # Transforms 'Los Angeles, CA' to 'los-angeles_ca'
  # This transformation is necessary for getting to the right
  #   webpage within realtor.com
  loc = location.lower()
  loc = loc.replace(", ", "_")
  loc = loc.replace(" ", "-")
  return loc

def main():
  cprint("<g>Running ScrapeAgentInfo...")
  config = get_config()

  USER_DATA_PATH = config["chrome_options"]["user_data_path"]
  PROFILE_PATH = config["chrome_options"]["profile_path"]
  LOCATIONS = config["locations"]
  OUTPUT_CSV = config["output_csv"]
  URL_REALTOR_AGENTS = "https://www.realtor.com/realestateagents/"

  base = Base(user_data_path=USER_DATA_PATH, profile_path=PROFILE_PATH)
  driver = base.initialize_driver()

  def search_location_on_realtor(location):
    driver.get(f"{URL_REALTOR_AGENTS}/{transform_location(location)}")
  
  def get_page_count():
    last_page = driver.find_element(By.XPATH, "//div[@role='navigation']/a[position() = last() - 1]")
    return int(last_page.text)
    
  def get_agents_on_page():
    return driver.find_elements(By.XPATH, "//div[@data-testid='component-agentCard']")
  
  def next_page(location, page):
    try:
      next = driver.find_element(By.XPATH, "//a[text()='Next']")
      next.click()
    except:
      driver.get(f"{URL_REALTOR_AGENTS}/{transform_location(location)}/pg-{page}")

  # Iterate over locations
  for loc in LOCATIONS:
    search_location_on_realtor(loc)
    agents = Agents()
    try:
      page_count = get_page_count()
    except:
      cprint(f"<c>{loc} - 0 pages")
      continue

    # Iterate over pages
    for p in range(1, page_count + 1):
      cprint(f"<c>{loc} - Page: {p} / {page_count}")
      agents_on_page = get_agents_on_page()

      # Iterate over agents
      for a in agents_on_page:
        name = a.find_element(By.XPATH, ".//div[contains(@class, 'agent-name')]").get_attribute("textContent")
        try:
          brokerage = a.find_element(By.XPATH, ".//div[contains(@class, 'agent-group')]/span").get_attribute("textContent")
        except:
          brokerage = ""
        try:
          phone = a.find_element(By.XPATH, ".//div[contains(@class, 'agent-phone')]").get_attribute("textContent")
        except:
          phone = ""
        try:
          sold = a.find_element(By.XPATH, ".//div[contains(text(), 'Sold')]/span").get_attribute("textContent")
        except:
          sold = ""
        agents.add_agent(Agent(loc, name, brokerage, phone, sold))

      if p < page_count:
        next_page(loc, p + 1)

    
    if OUTPUT_CSV:
      f = open(f"agent_files/{loc}.csv", "w", encoding="utf-8")
      f.write(agents.get_agents_as_string())
    else:
      f = open(f"agent_files/{loc}.txt", "w")
      f.write(agents.get_agents_as_string(csv=False))
    f.close()

if __name__ == "__main__":
  main()