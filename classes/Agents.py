class Agent:
  def __init__(self, location, name, brokerage, phone, sold):
    self.location = location
    self.name = name
    self.brokerage = brokerage
    self.phone = phone
    self.sold = sold

class Agents:
  def __init__(self):
    self.agents = []
  
  def add_agent(self, agent : Agent):
    self.agents.append(agent)
  
  def get_agents_as_string(self, csv=True):
    if csv:
      agents = "\"Location\",\"Name\",\"First Name\",\"Last Name\",\"Brokerage\",\"Phone\",\"Sold\"\n"
    else:
      agents = "Location\tName\tFirst Name\tLast Name\tBrokerage\tPhone\tSold\n"
    for a in self.agents:
      name_list = a.name.split()
      first = name_list[0]
      last = name_list[len(name_list) - 1]
      if csv:
        agents += f"\"{a.location}\",\"{a.name}\",\"{first}\",\"{last}\",\"{a.brokerage}\",\"{a.phone}\",\"{a.sold}\"\n"
      else:
        agents += f"{a.location}\t{a.name}\t{first}\t{last}\t{a.brokerage}\t{a.phone}\t{a.sold}\n"
    return agents

