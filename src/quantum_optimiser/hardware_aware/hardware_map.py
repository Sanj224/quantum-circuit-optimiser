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
    new_circuit = QuantumCircuit(self.qubits, circuit.num_clbits)

    _, conflict_indices = self.conflicts(circuit)
    conflict_set = set(conflict_indices)

    for i, instruction in enumerate(circuit.data):
        if i in conflict_set:
            q0 = circuit.qubits.index(instruction.qubits[0])
            q1 = circuit.qubits.index(instruction.qubits[1])
            flipped = q0 > q1
            start, end = (q0, q1) if not flipped else (q1, q0)
            path = self.find_shortest_path(start, end)
            # Swap qubits into adjacent positions
            for j in range(len(path) - 2):
                new_circuit.swap(path[j], path[j + 1])
            # Apply gate preserving original control/target order
            if not flipped:
                new_circuit.append(
                    instruction.operation,
                    [new_circuit.qubits[path[-2]], new_circuit.qubits[path[-1]]],
                    instruction.clbits
                )
            else:
                new_circuit.append(
                    instruction.operation,
                    [new_circuit.qubits[path[-1]], new_circuit.qubits[path[-2]]],
                    instruction.clbits
                )
            # Swap back
            for j in reversed(range(len(path) - 2)):
                new_circuit.swap(path[j], path[j + 1])
        else:
            new_circuit.append(instruction)

    return new_circuit

  def heuristic(self, circuit):
    """
    Estimate the number of swap gates required to make the circuit compatible
    """
    swap_count = 0

    _, conflict_indices = self.conflicts(circuit)
    conflict_set = set(conflict_indices)

    for i, instruction in enumerate(circuit.data):
        if i in conflict_set:
            q0 = circuit.qubits.index(instruction.qubits[0])
            q1 = circuit.qubits.index(instruction.qubits[1])
            path = self.find_shortest_path(q0, q1)
            # swap there and back, so multiply by 2
            swap_count += (len(path) - 2) * 2

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

    _, conflict_indices = self.conflicts(circuit)
    if not conflict_indices:
        return None

    def gate_routing_cost(q0, q1):
        return max(0, len(self.find_shortest_path(q0, q1)) - 2) * 2

    def window_routing_cost(data, qubit_map):
        """Total routing cost of all 2q gates in data, under current qubit_map."""
        cost = 0
        for inst in data:
            if len(inst.qubits) == 2:
                q0 = qubit_map[circuit.qubits.index(inst.qubits[0])]
                q1 = qubit_map[circuit.qubits.index(inst.qubits[1])]
                cost += gate_routing_cost(q0, q1)
        return cost

    def find_best_swaps(window_data):
        """
        Greedily find a sequence of swaps that reduces routing cost of
        2q gates in window_data. Returns list of (p, q) physical qubit swaps.
        """
        n = circuit.num_qubits
        qubit_map = list(range(n))  # logical -> physical
        swap_sequence = []

        for _ in range(n_attempts):
            current_cost = window_routing_cost(window_data, qubit_map)
            if current_cost == 0:
                break

            best_swap = None
            best_cost = current_cost

            # Generate candidates: first edge on shortest path for each conflicting gate
            candidates = set()
            for inst in window_data:
                if len(inst.qubits) == 2:
                    p0 = qubit_map[circuit.qubits.index(inst.qubits[0])]
                    p1 = qubit_map[circuit.qubits.index(inst.qubits[1])]
                    if gate_routing_cost(p0, p1) > 0:
                        path = self.find_shortest_path(p0, p1)
                        if len(path) >= 2:
                            candidates.add((path[0], path[1]))
                            candidates.add((path[-2], path[-1]))

            # Score each candidate swap
            for pa, pb in candidates:
                trial_map = qubit_map.copy()
                # Find logical qubits at these physical positions and swap them
                la = trial_map.index(pa)
                lb = trial_map.index(pb)
                trial_map[la], trial_map[lb] = trial_map[lb], trial_map[la]

                cost = window_routing_cost(window_data, trial_map)
                if cost < best_cost:
                    best_cost = cost
                    best_swap = (pa, pb, la, lb)

            if best_swap is None:
                break

            pa, pb, la, lb = best_swap
            qubit_map[la], qubit_map[lb] = qubit_map[lb], qubit_map[la]
            swap_sequence.append((pa, pb))

        return swap_sequence, qubit_map

    def apply_window(a, b, swap_sequence, final_qubit_map):
        """
        Emit: gates before window, swap-in, remapped window gates, swap-out, gates after.
        """
        new_circuit = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)

        for inst in circuit.data[:a]:
            new_circuit.append(inst)

        # Swap-in
        for pa, pb in swap_sequence:
            new_circuit.swap(pa, pb)

        # Window gates remapped to physical positions under final_qubit_map
        for inst in circuit.data[a:b]:
            new_qubits = [
                new_circuit.qubits[final_qubit_map[circuit.qubits.index(q)]]
                for q in inst.qubits
            ]
            new_circuit.append(inst.operation, new_qubits, inst.clbits)

        # Swap-out: reverse the swap sequence to restore qubit order
        for pa, pb in reversed(swap_sequence):
            new_circuit.swap(pa, pb)

        for inst in circuit.data[b:]:
            new_circuit.append(inst)

        return new_circuit

    # Find candidate windows: at least 2 two-qubit gates, centred on conflict indices
    best_circuit = None
    best_cost = self.heuristic(circuit)

    seen_windows = set()
    for ci in conflict_indices:
        for padding in range(0, min(4, n_attempts)):
            a = max(0, ci - padding)
            b = min(len(circuit.data), ci + padding + 1)
            if (a, b) in seen_windows:
                continue
            seen_windows.add((a, b))

            window_data = circuit.data[a:b]
            two_qubit_gates = [inst for inst in window_data if len(inst.qubits) == 2]
            if len(two_qubit_gates) < 2:
                continue

            swap_sequence, final_qubit_map = find_best_swaps(window_data)
            if not swap_sequence:
                continue

            candidate = apply_window(a, b, swap_sequence, final_qubit_map)
            candidate_cost = self.heuristic(candidate)
            if candidate_cost < best_cost:
                best_cost = candidate_cost
                best_circuit = candidate

    return best_circuit