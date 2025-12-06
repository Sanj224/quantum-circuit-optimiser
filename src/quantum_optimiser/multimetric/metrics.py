# Will be used to calculate the metrics from the ZX diagram 

# Qubit count
def qubit_count(circuit):
    return circuit.num_qubits

# Number of gates
def gate_count(circuit):
    return len(circuit.data)

# Number of two qubit gates
def two_qubit_gate_gount(circuit):
    return sum(1 for instruction in circuit.data if instruction.operation.num_qubits == 2)
# Number of T gates

def t_gate_count(circuit):
    return sum(1 for instruction in circuit.data if instruction.operation.name == 't')

# Number of Clifford gates
def cliffordGateCount(circuit):
    clifford_gates = {'h', 'x', 'y', 'z', 's', 'sdg', 'cx', 'cy', 'cz', 'swap', 'id', 'i'}
    return sum(1 for instruction in circuit.data if instruction.operation.name in clifford_gates)
# fidelity

# Coupling Map


