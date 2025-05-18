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
from collections import defaultdict, deque
import copy

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
          
  def parse(self, name: str, current_id=None, on_loop=False, 
            convergence=deque(), expecting=deque(), visited=None) -> str:
      if current_id is None:
         current_id, value = next(iter(self.current_graph.items()))
         return self.parse(name=name, current_id=current_id, visited=[])
      else:
         if current_id in visited:
            if not on_loop:
               return ""
         else:
            visited.append(current_id)

         looping = False
         if not on_loop:
            looping = self.verify_loop(current_id)
         else:
            looping = on_loop  

         if len(expecting) > 0:
            last = expecting.pop()
            if last == current_id and looping:
                return "" 
            else:
               expecting.append(last)

         if len(convergence) > 0:
            last = convergence.pop()
            if current_id == last:
               return ""
            else:
               convergence.append(last)   
          
         identity = self.current_graph[current_id]
         node = identity[0]
         edges = identity[1]

         is_last = False

         if len(edges) == 0:
            is_last = True

         if node.shape_type == 'start_end':
            if node.text == 'start':
                return f"""
                int {name}() 
                {{ 
                  {self.parse(name, str(id(edges[0])), 
                  looping, convergence=convergence, 
                  expecting=expecting, visited=visited)} 
                }}"""
            elif node.text == 'end':
               return "return 0;"
            else:
               return f"""
               int {node.text} 
               {{ 
                 {self.parse(name, str(id(edges[0])), 
                  looping, convergence=convergence, expecting=expecting, visited=visited)} 
               }}"""
         elif node.shape_type == 'process':
              if is_last:
                return f"""{node.text};"""
              return f"""{node.text}; 
              {self.parse(name, str(id(edges[0])), looping, 
              convergence=convergence, expecting=expecting, visited=visited)}"""

         elif node.shape_type == 'input_output':
              frac = node.text.split(' ', 1)
              if len(frac) != 2:
                  raise ValueError("Invalid input/output format")
              else:
                  if frac[0] == 'read':
                    if is_last:
                      return f"""print({frac[1]});"""
                    return f"""print({frac[1]});
                    {self.parse(name, str(id(edges[0])), looping, 
                                convergence=convergence, expecting=expecting, visited=visited)}"""
                  elif frac[0] == 'write':
                    if is_last:
                      return f"""input({frac[1]});"""
                    code += f"""input({frac[1]});
                    {self.parse(name, str(id(edges[0])), looping, 
                                convergence=convergence, expecting=expecting, visited=visited)}"""
                  else:
                    raise ValueError("Invalid input/output format")
         elif node.shape_type == 'decision' and looping:
            expecting.append(current_id)
            return f"""while ({node.text}) {{
              {self.parse(name, str(id(edges[0])), looping, 
                          expecting=expecting, convergence=convergence, visited=visited)}
            }}
            {self.parse(name, str(id(edges[1])), False, visited=visited)}"""
         elif node.shape_type == 'decision' and not looping:
            conv = self.get_convergence(current_id)
            if len(edges) < 2:
               raise ConnectionError("No hay conexiones suficientes en la decision")
         
            if conv is not None:
              old_convergence = copy.copy(convergence)
              convergence.append(conv)
              return f"""if ({node.text}) {{
                  {self.parse(name, str(id(edges[0])), on_loop=looping, 
                              convergence=convergence, expecting=expecting, visited=visited)}
                }} else {{
                  {self.parse(name, str(id(edges[1])), on_loop=looping, 
                              convergence=convergence, expecting=expecting, visited=visited)}
                }}
                {self.parse(name, current_id=str(id(edges[1])), on_loop=looping, 
                            convergence=old_convergence, expecting=expecting, visited=visited)}
            """
            else:
               return f"""if ({node.text}) {{
                  {self.parse(name, str(id(edges[0])), on_loop=looping, 
                              convergence=convergence, expecting=expecting, visited=visited)}
                }} else {{
                  {self.parse(name, str(id(edges[1])), on_loop=looping, 
                              convergence=convergence, expecting=expecting, visited=visited)}
                }}"""
               
           
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
  
  def loop_expecting_nodes(self, original_id: str, current_id: str, l: list = []):
      if original_id == current_id:
         return l
      else:
         l.append(current_id)
         self.loop_expecting_nodes(original_id, self.current_graph[current_id][1][0], l)


  def get_convergence(self, current_id: str):
      visit_count = defaultdict(set)  
      routes = self.current_graph[current_id][1]

      for route_id, destiny in enumerate(routes):
          self.dfs(destiny, self.current_graph, route_id, visit_count, set())

      for node, linked_routes in visit_count.items():
          if len(linked_routes) >= 2:
              return node  

      return None

  def dfs(self, node, graph, route_id, visit_count, local_visited):
    node_id = str(id(node)) if not isinstance(node, str) else node

    if node_id in local_visited:
        return
    local_visited.add(node_id)
    visit_count[node_id].add(route_id)

    for next_node in graph[node_id][1]:
        next_id = str(id(next_node))
        self.dfs(next_id, graph, route_id, visit_count, local_visited.copy())  

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

  

