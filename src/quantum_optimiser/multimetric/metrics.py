# Will be used to calculate the metrics from the ZX diagram 

# Qubit count
def qubitCount(circuit):
    return len(circuit.qubits)

# Number of gates
def gateCount(circuit):
    return len(circuit.gates)

# Number of two qubit gates
def twoQubitGateCount(circuit):
    return len([gate for gate in circuit.gates if gate.numQubits == 2])

# Number of T gates

# Number of clifford gates

# fidelity

# Coupling Map


