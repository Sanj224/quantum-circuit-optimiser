# Will be used to calculate the metrics from the ZX diagram 
import pyzx as zx
import math

# Qubit count
def circuit_qubit_count(circuit):
    """Count only qubits that are actually used (have gates on them)"""
    used_qubits = set()
    for instruction in circuit.data:
        for qubit in instruction.qubits:
            used_qubits.add(circuit.qubits.index(qubit))
    
    return len(used_qubits) if used_qubits else circuit.num_qubits

# Number of gates
def circuit_gate_count(circuit):
    return len(circuit.data)

# Number of two qubit gates
def circuit_two_qubit_gate_count(circuit):
    return sum(1 for instruction in circuit.data if instruction.operation.num_qubits == 2)

# Number of T gates
def circuit_t_gate_count(circuit):
    return sum(1 for instruction in circuit.data if instruction.operation.name == 't')

# Number of Clifford gates
def circuit_clifford_gate_count(circuit):
    clifford_gates = {'h', 'x', 'y', 'z', 's', 'sdg', 'cx', 'cy', 'cz', 'swap', 'id', 'i'}
    return sum(1 for instruction in circuit.data if instruction.operation.name in clifford_gates)


def circuit_depth(circuit):
    """Calculate the depth of a quantum circuit"""
    return circuit.depth()

# Qubit count
def graph_qubit_count(graph):
    return graph.qubit_count()

# Number of gates (vertices excluding inputs/outputs)
def graph_gate_count(graph):
    return sum(1 for v in graph.vertices() if graph.type(v) not in [zx.VertexType.BOUNDARY])

# Number of two qubit gates (edges between non-boundary vertices)
def graph_two_qubit_gate_count(graph):
    count = 0
    for edge in graph.edges():
        v1, v2 = edge
        if graph.type(v1) != zx.VertexType.BOUNDARY and graph.type(v2) != zx.VertexType.BOUNDARY:
            count += 1
    return count

# Number of T gates (Z or X spiders with phase = pi/4 or -pi/4)
def graph_t_gate_count(graph):
    count = 0
    for v in graph.vertices():
        if graph.type(v) in [zx.VertexType.Z, zx.VertexType.X]:
            phase = graph.phase(v)
            if abs(phase - 0.25) < 1e-10 or abs(phase + 0.25) < 1e-10 or abs(phase - 1.75) < 1e-10:
                count += 1
    return count

# Number of Clifford gates
def graph_clifford_gate_count(graph):

    count = 0
    
    # Count Clifford spiders (phases that are multiples of π/2)
    for v in graph.vertices():
        if graph.type(v) in [zx.VertexType.Z, zx.VertexType.X]:
            phase = graph.phase(v)
            # Check if phase is a multiple of 0.5 (which represents π/2 in PyZX)
            if abs(phase - round(phase * 2) / 2) < 1e-10:
                count += 1
        elif graph.type(v) == zx.VertexType.H_BOX:
            count += 1
    
    # Count Hadamard edges
    for edge in graph.edges():
        if graph.edge_type(edge) == zx.EdgeType.HADAMARD:
            count += 1
    
    return count

