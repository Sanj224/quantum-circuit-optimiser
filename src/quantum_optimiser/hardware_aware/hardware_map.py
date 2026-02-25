## Contains a class that represents the hardware constraints of the graph
import networkx as nx
from ..multimetric import metrics
from qiskit import QuantumCircuit

class hardware_map:
  def __init__(self, qubits, connections,qubit_info,gate_info):
    self.qubits = qubits
    self.connections = connections
    ## Quick Error handling
    for connection in connections: 
      if connection[0] > qubits or connection[1] > qubits:
        raise IndexError(f"Connections out of bound, all qubit indices must be between 1 and {qubits}")
      if connection[0] == connection [1]:
        raise IndexError("Qubits cannot be connected to each other")
    ## Construct the graph using networkx
    qubit_list = []
    for i in range (self.qubits):
      qubit_list.append(i)
    self.mapping = nx.Graph()
    self.mapping.add_nodes_from(qubit_list)    
    self.mapping.add_edges_from(self.connections) 

    if not nx.is_connected(self.mapping):
      raise IndexError("All your qubits must be connected")
      
  
  def find_shortest_path(self, qubit1, qubit2):
    """
    Finds the shortest distance between two qubits in a map
    Will be used as a heuristic to inform hardware aware optimisation
    """
    return (nx.shortest_path(self.mapping, qubit1, qubit2)) 
 
  def conflicts(self, circuit):
      edges, indices = metrics.find_two_qubit(circuit)
      conflict_edges, conflict_indices = [], []
      for i, edge in enumerate(edges):
          qubit1, qubit2 = edge[0], edge[1]
          path = self.find_shortest_path(qubit1, qubit2)
          distance = len(path) - 2
          if distance != 0:
              conflict_edges.append(edge)
              conflict_indices.append(indices[i])
      return conflict_edges, conflict_indices
 

  def make_compatible(self, circuit):

    edges, indices = self.conflicts(circuit)

    new_circuit = QuantumCircuit(circuit.num_qubits,circuit.num_clbits)
    for i in range (len(circuit.data)):
      if i in indices:
        edge_loc = indices.index(i)
        edge = edges[edge_loc]
        path = self.find_shortest_path(edge[0],edge[1])
        for j in range (len(path)-2):
          new_circuit.swap(path[j],path[j+1])
        instruction = circuit.data[i]
        new_instruction = instruction.replace(qubits=[new_circuit.qubits[path[j+1]],new_circuit.qubits[path[j+2]]])
        new_circuit.append(new_instruction)

        for j in range ((len(path)-2),0,-1):
          new_circuit.swap(path[j-1],path[j])
          
      else:
        new_circuit.append(circuit.data[i])
    return new_circuit
      


  def heuristic(self, circuit):
    edges,_= metrics.find_two_qubit(circuit)
    distance  = 0 
    for edge in edges:
      qubit1, qubit2 = edge[0], edge[1]
      distance = distance +(len(self.find_shortest_path(qubit1,qubit2)) -2)

    return distance*2

  def is_compatible(self, circuit):
    if self.heuristic(circuit) == 0:
      return True
    else:
      return False
   
