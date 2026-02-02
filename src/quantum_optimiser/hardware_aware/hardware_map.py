## Contains a class that represents the hardware map in the form of a graph 
## Add a gate set??? 
import networkx as nx
from ..multimetric import metrics
from qiskit import QuantumCircuit

class hardware_map:
  def __init__(self, qubits, connections):
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
    # Get all the two qubit gates that are causing issues, as well as their indices
    edges,indices= metrics.find_two_qubit(circuit)
    conflict_edges, conflict_indices = [],[]
    for edge in edges:
      qubit1, qubit2 = edge[0], edge[1]
      path = self.find_shortest_path(qubit1,qubit2)
      distance =  len(path) - 2
      if distance != 0:
        conflict_edges.append(edge)
        conflict_indices.append(indices[edges.index(edge)])
    return conflict_edges, conflict_indices
 

  def make_compatible(self, circuit):
    edges, indices = self.conflicts(circuit)
    new_circuit = QuantumCircuit(circuit.num_qubits,circuit.num_clbits)
    for i in range (len(circuit.data)):
      if i in indices:
        edge_loc = indices.index(i)
        edge = edges[edge_loc]
        path = self.find_shortest_path(edge[0],edge[1])
        print (path)
        for j in range (len(path)-2):
          print("swapping", path[j],path[j+1])
          new_circuit.swap(path[j],path[j+1])
        gate = circuit.data[i].operation.name
        print(circuit.data[i].qubits.index[1])
        print(gate)
        new_circuit.append(circuit.data[i])
        print(new_circuit)

        for j in range (reversed((len(path)-2))):
          new_circuit.swap(path[j+1],path[j])
          
      else:
        new_circuit.append(circuit.data[i])
    return new_circuit
      


  def heuristic(self, circuit):
    #CHANGE THE NAME OF THIS FUNCTION
    edges,_= metrics.find_two_qubit(circuit)
    distance  = 0 
    for edge in edges:
      qubit1, qubit2 = edge[0], edge[1]
      distance = distance +(len(self.find_shortest_path(qubit1,qubit2)) -2)

    return distance

  def is_compatible(self, circuit):
    """
    Given a circuit, is it comptabile on the hardware, need to check that no extra gates are required
    """
    if self.heuristic(circuit) == 0:
      return True
    else:
      return False
   

## Construct a set of default hardware
## TO-DO: Make sure to research existing ones

connections = [[0,1],[0,2],[0,3],[0,4],[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
defaultHardware = hardware_map(5,connections)

conns = [[0,1],[1,2],[2,3],[3,4]]
linkedHardware= hardware_map(5,conns)