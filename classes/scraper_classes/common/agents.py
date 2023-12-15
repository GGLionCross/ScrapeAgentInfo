
from python_utils import load_json, write_json
import json
import os

class Agents:
    def __init__(self, columns):
        self.agents = []
        self.columns = columns
  
    def add_agent(self, agent):
        # agent = {
        #     "Location": "..."
        #     "Scrape Date": "..."
        #     "Index": "..."
        #     "Full Name Name": "..."
        #     "First Name": "..."
        #     "Last Name": "..."
        #     ...
        # }
        self.agents.append(agent)

    def get_headers_as_csv_string(self):
        headers = ""
        # ex. "Location","Name","First Name","Last Name","Phone"\n
        for i in range(0, len(self.columns)):
            headers += f"\"{self.columns[i]}\""
            headers += "," if i < len(self.columns) - 1 else "\n"

        return headers
    
    def get_agent_as_csv_string(self, agent):
        agent_string = ""
        for i in range(0, len(self.columns)):
            agent_string += f"\"{agent[self.columns[i]]}\""
            agent_string += "," if i < len(self.columns) - 1 else "\n"
        return agent_string

    def get_all_agents_as_csv_string(self):
        agents = ""
        
        agents += self.get_headers_as_csv_string()
    
        for agent in self.agents:
            for i in range(0, len(self.columns)):
                agents += f"\"{getattr(agent, self.columns[i])}\""
                agents += "," if i < len(self.columns) - 1 else "\n"
        
        return agents
    
    # Returns whether or not the urls are saved within a json file
    def are_urls_saved(self, folder, location):
        if os.path.exists(f"agent_urls/{folder}/{location}.json"):
            return True
        else:
            return False
    
    # Returns saved urls that are within a json file
    def get_saved_urls(self, folder, location):
        return load_json(f"agent_urls/{folder}/{location}.json")
    
    # Save urls within a json file
    def save_urls(self, folder, location, urls):
        # Format of json object
        # [
        #     ...
        # ]

        os.makedirs(f"agent_urls/{folder}", exist_ok=True)
        with open(f"agent_urls/{folder}/{location}.json", "w") as f:
            write_json(f, urls)