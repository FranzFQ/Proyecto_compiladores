'''
class ConnectionNode:
    def __init__(self, from_item, to_item, line_item):
        self.from_item = from_item
        self.to_item = to_item
        self.line_item = line_item
        self.next = None

    item(att):
      self.text
      self.shape_type

func_node(att):
  curr.text
  curr.shape_type

'start_end'
'process'
'decision'
'connector'
'input_output'

'''


class Parser:
  def __init__(self, flow_graph: dict):
    self.flow_graph = flow_graph
    self.ind_functions = {}
    self.code = {}
    self.current_graph = None

  def generate_code(self):
      self.set_ind_functions()
      for func_name, connections in self.ind_functions.items():
          self.current_graph = self.synthesize_conn(connections)
          print(self.current_graph)
          if func_name == 'start':
              self.parse('main')
          else:
              self.parse(func_name)

  def parse(self, name: str, *kwargs):
      pass

  def synthesize_conn(self, connections: list) -> dict:
      synth_dict = []
      visited_nodes = []
      for conn in connections:
         identity_from = []
         identity_to = []
         from_item = conn.from_item
         to_item = conn.to_item        

         if from_item not in visited_nodes:
            for _conn in connections:
                if from_item == _conn.from_item:
                    identity_from.append(_conn.to_item)
            
            visited_nodes.append(from_item)
            synth_dict[id(from_item)] =  (from_item, identity_from)

         if to_item not in visited_nodes:
            for _conn in connections:
                if to_item == _conn.from_item:
                    identity_to.append(_conn.to_item)

         
            visited_nodes.append(to_item)
            synth_dict[id(to_item)] = (to_item, identity_to)
      
      return synth_dict
     

  def search_id(self, id_: str):
    for key, value in self.flow_graph.items():
      if key == 'conn':
        break
      else:
        for item in value:
          if str(id(item)) == id_:
            return key

  def set_ind_functions(self):
    current = self.flow_graph['conn'].head
    while current:
      func_name = self.search_id(str(id(current.from_item)))
      if func_name not in self.ind_functions:
        self.ind_functions[func_name] = []
      self.ind_functions[func_name].append(current)
      current = current.next

  

