"""
This file contains all the methods that return the metrics of a given circuit
"""

def circuit_qubit_count(circuit):
    """Count only qubits that are actually used (have gates on them)"""
    used_qubits = set()
    for instruction in circuit.data:
        # Go through each instruction/ gate and add the qubits involved
        for qubit in instruction.qubits:
            used_qubits.add(circuit.qubits.index(qubit))
    
    return len(used_qubits) if used_qubits else circuit.num_qubits


def circuit_gate_count(circuit,hardware=None):
    """
    Count the number of gates in the circuit
    If a hardware is specified, count the number of extra gates required for routing
    """
    if hardware == None:
        return len(circuit.data)
    else: 
        return (len(circuit.data) + hardware.heuristic(circuit))


def circuit_two_qubit_gate_count(circuit,hardware=None):
    """
    Count the number of two qubit gates in the circuit
    If a hardware is specified, count the number of extra gates required for routing
    """
    if hardware == None:
        return sum(1 for instruction in circuit.data if instruction.operation.num_qubits == 2)
    else: 
        return ((sum(1 for instruction in circuit.data if instruction.operation.num_qubits == 2)) + hardware.heuristic(circuit))


def circuit_t_gate_count(circuit):
    """Calculate the number of t gates in a circuit"""
    return sum(1 for instruction in circuit.data if instruction.operation.name == 't')


def circuit_depth(circuit):
    """Calculate the depth of a quantum circuit"""
    return circuit.depth()


def find_two_qubit(circuit):
    """
    Find the location of all the two qubit gates in the circuit and what qubits they act on
    This will be needed for hardware routing
    """
    qubit_pairs = []
    instruction_index=[]
    index = 0
    for instruction in circuit.data:
        if instruction.operation.num_qubits >= 2:
            instruction_index.append(index)
            qubits = []
            for qubit in instruction.qubits:
                qubits.append(circuit.qubits.index(qubit))
            qubit_pairs.append(qubits)
        index = index + 1 
    return qubit_pairs, instruction_index
            
  

