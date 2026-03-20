## Contains a class that represents the hardware constraints of the graph
import networkx as nx
from ..multimetric import metrics
from qiskit import QuantumCircuit
import random
from itertools import combinations

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
      new_circuit = QuantumCircuit(self.qubits, circuit.num_clbits)
      
      for i in range(len(circuit.data)):
          if i in indices:
              edge_loc = indices.index(i)
              edge = edges[edge_loc]
              path = self.find_shortest_path(edge[0], edge[1])
              
              for j in range(len(path) - 2):
                  new_circuit.swap(path[j], path[j + 1])
              instruction = circuit.data[i]
              new_instruction = instruction.replace(
                  qubits=[new_circuit.qubits[path[-2]], new_circuit.qubits[path[-1]]]
              )
              new_circuit.append(new_instruction)
              for j in range(len(path) - 2, 0, -1):
                  new_circuit.swap(path[j - 1], path[j])
          else:
              instruction = circuit.data[i]
              # remap qubits from old register to new circuit's register
              new_qubits = [new_circuit.qubits[circuit.qubits.index(q)] for q in instruction.qubits]
              new_instruction = instruction.replace(qubits=new_qubits)
              new_circuit.append(new_instruction)
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
    
  def try_qubit_permutation(self, circuit, n_attempts=10):
    if len(circuit.data) < 3:
      return None

    def perm_to_swaps(p):
      swaps, p = [], p.copy()
      for i in range(len(p)):
        while p[i] != i:
          j = p[i]
          swaps.append((i, j))
          p[i], p[j] = p[j], p[i]
      return swaps

    def window_cost(a, b, perm):
      cost = len(perm_to_swaps(perm)) * 4
      for inst in circuit.data[a:b]:
        if len(inst.qubits) == 2:
          q0 = perm[circuit.qubits.index(inst.qubits[0])]
          q1 = perm[circuit.qubits.index(inst.qubits[1])]
          cost += (len(self.find_shortest_path(q0, q1)) - 2) * 2
      return cost

    def apply_permutation_window(a, b, perm):
      swaps = perm_to_swaps(perm)
      new_circuit = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
      for inst in circuit.data[:a]:
        new_circuit.append(inst)
      for s1, s2 in swaps:
        new_circuit.swap(s1, s2)
      for inst in circuit.data[a:b]:
        new_qubits = [
          new_circuit.qubits[perm[circuit.qubits.index(q)]]
          for q in inst.qubits
        ]
        new_circuit.append(inst.operation, new_qubits, inst.clbits)
      for s1, s2 in reversed(swaps):
        new_circuit.swap(s1, s2)
      for inst in circuit.data[b:]:
        new_circuit.append(inst)
      return new_circuit

    n = circuit.num_qubits
    best_circuit = None
    best_cost = self.heuristic(circuit)

    for _ in range(n_attempts):
      a = random.randint(0, len(circuit.data) - 2)
      b = min(a + random.randint(2, 8), len(circuit.data))

      active = sorted(set(
        circuit.qubits.index(q)
        for inst in circuit.data[a:b]
        for q in inst.qubits
      ))
      if len(active) < 2:
        continue

      identity = list(range(n))
      baseline = window_cost(a, b, identity)

      pairs = list(combinations(active, 2))
      if len(pairs) > 8:
        pairs = random.sample(pairs, 8)

      for q1, q2 in pairs:
        perm = identity.copy()
        perm[q1], perm[q2] = perm[q2], perm[q1]
        if window_cost(a, b, perm) < baseline:
          full = apply_permutation_window(a, b, perm)
          full_cost = self.heuristic(full)
          if full_cost < best_cost:
            best_cost = full_cost
            best_circuit = full

    return best_circuit