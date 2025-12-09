from . import metrics


# Add up all the metrics
def naive_loss(circuit):
    a = metrics.circuit_qubit_count(circuit)
    b = metrics.circuit_two_qubit_gate_count(circuit)
    c = metrics.circuit_gate_count(circuit)
    d = metrics.circuit_clifford_gate_count(circuit)
    e = metrics.circuit_t_gate_count(circuit)
    return a+b+c+d+e

def informed_loss(circuit):
    a = metrics.circuit_qubit_count(circuit)
    b = metrics.circuit_two_qubit_gate_count(circuit)
    c = metrics.circuit_gate_count(circuit)
    d = metrics.circuit_clifford_gate_count(circuit)
    e = metrics.circuit_t_gate_count(circuit)
    return a+2*b+c+d+5*e
