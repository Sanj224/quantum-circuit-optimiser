# Will be used to calculate the metrics from the circuit
# Qubit count
def qubitCount(circuit):
    return len(circuit.qubits)

# Number of gates
def gateCount(circuit):
    return len(circuit.gates)

# Number of two qubit gates
def twoQubitGateCount(circuit):
    return len([gate for gate in circuit.gates if gate.num_qubits == 2])

# Number of clifford gates
def cliffordGateCount(circuit): 