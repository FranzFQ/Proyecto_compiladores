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
import re

class Parser:
  def __init__(self, flow_graph: dict):
    self.flow_graph = flow_graph
    self.ind_functions = {}
    self.code = {}
    self.current_graph = None

  def generate_code(self) -> str:
      self.set_ind_functions()
      for func_name, connections in self.ind_functions.items():
          self.current_graph = connections
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
            convergence=None, expecting=deque(), visited=None) -> str:
      if current_id is None:
         current_id, value = next(iter(self.current_graph.items()))
         return self.parse(name=name, current_id=current_id, visited=[])
      else:

         looping = False
         if not on_loop:
            looping = self.verify_loop(current_id)
         else:
            looping = on_loop  

         if convergence is not None:
            if current_id == convergence:
               return ""

         if current_id in visited:
            if not on_loop:
               return ""
         else:
            visited.append(current_id)
  
         if len(expecting) > 0:
            last = expecting.pop()
            if last == current_id and looping:
                return "" 
            else:
               expecting.append(last)  
          
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
            elif node.text == 'end_function':
               return ""
            else:
               return f"""
               {self.format_function_init(node.text)} 
               {{ 
                 {self.parse(name, str(id(edges[0])), 
                  looping, convergence=convergence, expecting=expecting, visited=visited)} 
               }}"""

         elif node.shape_type == 'process':
              code = ""
              inst_list = node.text.split("\n")
              
              if is_last:
                for inst in inst_list:
                   code += f"{inst};\n"
                   return code

              for inst in inst_list:
                code += f"{inst};\n"
              code += f"""{self.parse(name, str(id(edges[0])), looping, convergence=convergence, expecting=expecting, visited=visited)}"""
              return code

         elif node.shape_type == 'input_output':
              frac = node.text.split(' ', 1)
              if len(frac) != 2:
                  raise ValueError("Invalid input/output format")
              else:
                  if frac[0] == 'write':
                    if is_last:
                      return f"""print({frac[1]});"""
                    return f"""print({frac[1]});
                    {self.parse(name, str(id(edges[0])), looping, 
                                convergence=convergence, expecting=expecting, visited=visited)}"""
                  elif frac[0] == 'read':
                    if is_last:
                      return f"""{frac[1]} = input();"""
                    return f"""{frac[1]} = input();
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
            {self.parse(name, str(id(edges[1])), False, visited=visited, convergence=convergence, expecting=expecting)}"""
         elif node.shape_type == 'decision' and not looping:
            conv = self.get_convergence(current_id)
            if len(edges) < 2:
               raise ConnectionError("No hay conexiones suficientes en la decision")
         
            if conv is not None:
              old_convergence = copy.copy(convergence)
              return f"""if ({node.text}) {{
                  {self.parse(name, str(id(edges[0])), on_loop=looping, 
                              convergence=conv, expecting=expecting, visited=visited)}
                }} else {{
                  {self.parse(name, str(id(edges[1])), on_loop=looping, 
                              convergence=conv, expecting=expecting, visited=visited)}
                }}
                {self.parse(name, current_id=str(conv), on_loop=looping, 
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
      return ""
               
           
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

  def set_ind_functions(self):
    self.remove_connectors()
    graph = self.synthesize_conn(self.flow_graph['conn'])
    visited = set()
    subgraphs = {}
    
    for node_key in graph:
        if node_key not in visited:
            subgraph = {}
            queue = deque()
            queue.append(node_key)
            visited.add(node_key)
            
            try:
                first_node_payload = graph[node_key][0]
                first_node_payload_text = first_node_payload.text
            except (AttributeError, IndexError) as e:
                first_node_payload_text = str(node_key)
            
            iteration_count = 0
            max_iterations = len(graph) * 2
            
            while queue and iteration_count < max_iterations:
                iteration_count += 1
                current_key = queue.popleft()
                
                if current_key not in graph:
                    continue
                
                subgraph[current_key] = graph[current_key]
                
                for neighbor in graph[current_key][1]:
                    if neighbor not in visited:
                        visited.add(str(id(neighbor)))
                        queue.append(str(id(neighbor)))
            
            if iteration_count >= max_iterations:
                print()
            
            subgraphs[first_node_payload_text] = subgraph
    
    self.ind_functions = subgraphs
    
    

  def remove_connectors(self):
     conn_list = []
     current = self.flow_graph['conn'].head
     while current:
        conn_list.append(current)
        current = current.next

     conn_from = None
     conn_to = None    
     for conn in conn_list:
        if conn.to_item.shape_type == 'connector':
           for _conn in conn_list:
              if _conn.from_item.shape_type == 'connector' and _conn.from_item.text == conn.to_item.text:
                 conn_from = conn
                 conn_to = _conn

     if conn_to and conn_from:
        conn_from.to_item = conn_to.to_item
        conn_list.remove(conn_to)

     self.flow_graph['conn'] = conn_list

  def format_function_init(self, _input: str) -> str:
    stripped = _input.strip()  
    if re.search(r'\w+\s*\(', stripped):
        return stripped
    return stripped + "()"

