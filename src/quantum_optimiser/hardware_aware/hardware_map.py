## Contains a class that represents the hardware map in the form of a graph 
## Add a gate set??? 
from typing import List, Tuple
import networkx as nx

class hardware_map:
  def __init__(self, qubits: int, connections: List[Tuple[int,int]]):
    self.qubits = qubits
    self.connections = connections
    ## Quick Error handling
    for connection in connections: 
      if connection[0] > qubits or connection[1] > qubits:
        raise IndexError(f"Connections out of bound, all qubit indices must be between 1 and {qubits}")
      if connection[0] == connection [1]:
        raise IndexError("Qubits cannot be connected to each other")
    
    ## Construct the graph using networkx
    self.mapping = nx.Graph()
    self.mapping.add_edges_from(self.qubits)    
    self.mapping.add_vertices_from(self.connections)
      
  
  def find_shortest_distance(self, qubit1: int, qubit2: int):
    """
    Finds the shortest distance between two qubits in a map
    Will be used as a heuristic to inform hardware aware optimisation
    """
    return(nx.shortest_path(self.mapping, qubit1, qubit2))
  
  def is_compatible(self, circuit):
    """
    Given a circuit, is it comptabile on the hardware
    """
    return True
  
  def make_compatible(self,circuit):
    """
    Given a circuit, adjust it such that it is compatible with the given hardware
    """

    return circuit


