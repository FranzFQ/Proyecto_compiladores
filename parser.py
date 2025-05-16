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
from collections import defaultdict

class Parser:
  def __init__(self, flow_graph: dict):
    self.flow_graph = flow_graph
    self.ind_functions = {}
    self.code = {}
    self.current_graph = None

  def generate_code(self) -> str:
      self.set_ind_functions()
      for func_name, connections in self.ind_functions.items():
          self.current_graph = self.synthesize_conn(connections)
          if func_name == 'start':
              self.code['main'] = self.parse('main')
          else:
              self.code[func_name] = self.parse(func_name)

      codegen = ""
      main_code = ""

      for key, value in self.code.items():
         if key == 'main':
            main_code = value
         else:
            codegen += value + "\n"
      
      codegen += main_code + "\n"

      return codegen
          
  def parse(self, name: str, current_id=None, on_loop=False, convergence=None, expecting=None, visited=None) -> str:
      code = ""
      if current_id is None:
         current_id, value = next(iter(self.current_graph.items()))
         return self.parse(name, current_id)
      else:
         if visited is None:
            visited = set()

         if current_id in visited:
            return code
         else:
            visited.add(current_id)

         looping = False
         if not on_loop:
            looping = self.verify_loop(current_id)
         else:
            looping = on_loop  

         if expecting is not None:
            if str(id(expecting)) == current_id:
                return code 

         if convergence is not None:
            if current_id == str(id(convergence)):
               return code   
          
         identity = self.current_graph[current_id]
         node = identity[0]
         edges = identity[1]

         is_last = False

         if len(edges) == 0:
            is_last = True

         if node.shape_type == 'start_end':
            if node.text == 'start':
                code += f"""
                int {name}() 
                {{ 
                  {self.parse(name, str(id(edges[0])), looping, visited=visited)} 
                }}"""
            elif node.text == 'end':
               code += "return 0;"
            else:
               code += f"""
               int {node.text} 
               {{ 
                 {self.parse(name, str(id(edges[0])), looping, visited=visited)} 
               }}"""
         elif node.shape_type == 'process':
              if is_last:
                code += f"""{node.text};"""
                return code;
              code += f"""{node.text}; 
              {self.parse(name, str(id(edges[0])), looping, visited=visited)}"""

         elif node.shape_type == 'input_output':
              frac = node.text.split(' ')
              if len(frac) != 2:
                  raise ValueError("Invalid input/output format")
              else:
                  if frac[0] == 'read':
                    if is_last:
                      code += f"""print({frac[1]});"""
                      return code;
                    code += f"""print({frac[1]});
                    {self.parse(name, str(id(edges[0])), looping, visited=visited)}"""
                  elif frac[0] == 'write':
                    if is_last:
                      code += f"""input({frac[1]});"""
                      return code;
                    code += f"""input({frac[1]});
                    {self.parse(name, str(id(edges[0])), looping, visited=visited)}"""
                  else:
                    raise ValueError("Invalid input/output format")
         elif node.shape_type == 'decision' and on_loop:
            code += f"""while ({node.text}) {{
              {self.parse(name, str(id(edges[0])), looping, expecting=node, visited=visited)}
            }}
            {self.parse(name, str(id(edges[1])), False)}"""
         elif node.shape_type == 'decision' and not on_loop:
            conv = self.get_convergence(current_id)
            code += f"""if ({node.text}) {{
              {self.parse(name, str(id(edges[0])), convergence=conv, visited=visited)}
            }} else {{
              {self.parse(name, str(id(edges[1])), convergence=conv, visited=visited)}
            }}
            """ 
            if conv is not None:
               code += f"""{self.parse(name, conv)}"""
         print(code)  
         return code
           
  def verify_loop(self, current_id: str) -> bool:
      found = False
      for key, value in self.current_graph.items():
          if found:
              edges = value[1]
              for edge in edges:
                  if str(id(edge)) == current_id:
                      return True
          if key == current_id:
              found = True
      return False 

  from collections import defaultdict

  def get_convergence(self, current_id: str):
      visit_count = defaultdict(set)  
      routes = self.current_graph[current_id][1]

      for route_id, destino in enumerate(routes):
          self.dfs(destino, self.current_graph, route_id, visit_count, set())

      for node, linked_routes in visit_count.items():
          if len(linked_routes) >= 2:
              return node  

      return None

  def dfs(self, node, graph, route_id, visit_count, local_visited):
      if node in local_visited:
          return
      local_visited.add(node)
      visit_count[node].add(route_id)

      for siguiente in graph[node][1]:
          self.dfs(siguiente, graph, route_id, visit_count, local_visited.copy())  

  def synthesize_conn(self, connections: list) -> dict:
      synth_dict = {}
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
            synth_dict[str(id(from_item))] = (from_item, identity_from)

         if to_item not in visited_nodes:
            for _conn in connections:
                if to_item == _conn.from_item:
                    identity_to.append(_conn.to_item)
       
            visited_nodes.append(to_item)
            synth_dict[str(id(to_item))] = (to_item, identity_to)
      
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

  

