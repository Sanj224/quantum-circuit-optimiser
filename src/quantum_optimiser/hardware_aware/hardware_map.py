"""
In this file we define a class for the hardware map, along with a set of functions required for routing circuits
"""

import networkx as nx
from ..multimetric import metrics
from qiskit import QuantumCircuit
import random
from itertools import combinations

class hardware_map:
  def __init__(self, qubits, connections):
    self.qubits = qubits
    self.connections = connections
    ## Quick Error handling: check that the number of qubits are valid and that there are no self loops
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

    #Ensure that the graph is connected
    if not nx.is_connected(self.mapping):
      raise IndexError("All your qubits must be connected")
      
  
  def find_shortest_path(self, qubit1, qubit2):
    """
    Finds the shortest distance between two qubits in a map
    Will be used as a heuristic to inform hardware aware optimisation
    """
    return (nx.shortest_path(self.mapping, qubit1, qubit2)) 
 
  def conflicts(self, circuit):
      """
      Find all the two qubit gates that are between non adjacent qubits
      """
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
    """
    Add swap gates to each qubit that is part of an illegal two qubit operation
    """
    new_circuit = QuantumCircuit(self.qubits, circuit.num_clbits)

    logical_to_physical = list(range(self.qubits))
    physical_to_logical = list(range(self.qubits))

    def do_swap(pa, pb):
        new_circuit.swap(new_circuit.qubits[pa], new_circuit.qubits[pb])
        la = physical_to_logical[pa]
        lb = physical_to_logical[pb]
        logical_to_physical[la], logical_to_physical[lb] = pb, pa
        physical_to_logical[pa], physical_to_logical[pb] = lb, la

    for instruction in circuit.data:
        if instruction.operation.num_qubits == 1:
            l0 = circuit.qubits.index(instruction.qubits[0])
            p0 = logical_to_physical[l0]
            new_circuit.append(instruction.operation, [new_circuit.qubits[p0]], instruction.clbits)

        elif instruction.operation.num_qubits == 2:
            l0 = circuit.qubits.index(instruction.qubits[0])
            l1 = circuit.qubits.index(instruction.qubits[1])
            p0 = logical_to_physical[l0]
            p1 = logical_to_physical[l1]

            path = self.find_shortest_path(p0, p1)
            for j in range(len(path) - 2):
                do_swap(path[j], path[j + 1])

            p0 = logical_to_physical[l0]
            p1 = logical_to_physical[l1]
            new_circuit.append(
                instruction.operation,
                [new_circuit.qubits[p0], new_circuit.qubits[p1]],
                instruction.clbits
            )

        else:
            new_circuit.append(instruction)

    # Restore only the logical qubits the circuit actually used
    for logical in range(circuit.num_qubits):
        while logical_to_physical[logical] != logical:
            phys = logical_to_physical[logical]
            do_swap(phys, logical)

    return new_circuit


  def heuristic(self, circuit):
    """
    Estimate swap cost by simulating make_compatible's routing
    without building an actual circuit.
    """
    logical_to_physical = list(range(self.qubits))
    physical_to_logical = list(range(self.qubits))
    swap_count = 0
    def do_swap(pa, pb):
        nonlocal swap_count
        swap_count += 1
        la = physical_to_logical[pa]
        lb = physical_to_logical[pb]
        if la < len(logical_to_physical):
            logical_to_physical[la] = pb
        if lb < len(logical_to_physical):
            logical_to_physical[lb] = pa
        physical_to_logical[pa], physical_to_logical[pb] = lb, la

    for instruction in circuit.data:
        if instruction.operation.num_qubits == 2:
            l0 = circuit.qubits.index(instruction.qubits[0])
            l1 = circuit.qubits.index(instruction.qubits[1])
            p0 = logical_to_physical[l0]
            p1 = logical_to_physical[l1]

            path = self.find_shortest_path(p0, p1)
            for j in range(len(path) - 2):
                do_swap(path[j], path[j + 1])

    # count finalisation swaps
    for logical in range(circuit.num_qubits):
        while logical_to_physical[logical] != logical:
            phys = logical_to_physical[logical]
            do_swap(phys, logical)

    return swap_count

  def is_compatible(self, circuit):
    """
    Check that no two qubit operation in a circuit violates the connectivity
    """
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