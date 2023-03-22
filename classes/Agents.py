class Agent:
  def __init__(self, props):
    # props = { "name"="John Smith" }
    for key, value in props.items():
      setattr(self, key, value)

class Agents:
  def __init__(self, columns):
    self.agents = []
    self.columns = columns
  
  def add_agent(self, agent : Agent):
    self.agents.append(agent)

  def get_agents_as_csv_string(self):
    agents = ""
    # ex. "Location","Name","First Name","Last Name","Phone"\n
    for i in range(0, len(self.columns)):
      agents += f"\"{self.columns[i]}\""
      agents += "," if i < len(self.columns) - 1 else "\n"
    
    for agent in self.agents:
      for i in range(0, len(self.columns)):
        agents += f"\"{getattr(agent, self.columns[i])}\""
        agents += "," if i < len(self.columns) - 1 else "\n"
    
    return agents

  def get_agents_as_txt_string(self):
    agents = ""

    # If csv == False, format as .txt file using tabs
    # ex. Location\tName\tFirst Name\tLast Name\tPhone\n
    for i in range(0, len(self.columns)):
      agents += f"{self.columns[i]}"
      agents += "\t" if i < len(self.columns) - 1 else "\n"
    
    for agent in self.agents:
      for i in range(0, self.columns):
        agents += f"{getattr(agent, self.columns[i])}"
        agents += "\t" if i < len(self.columns) - 1 else "\n"
    
    return agents
