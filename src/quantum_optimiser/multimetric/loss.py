from . import metrics


# Add up all the metrics
def naive_loss(circuit):
    a = metrics.circuit_qubit_count(circuit)
    b = metrics.circuit_two_qubit_gate_count(circuit)
    c = metrics.circuit_gate_count(circuit)
    d = metrics.circuit_clifford_gate_count(circuit)
    e = metrics.circuit_t_gate_count(circuit)
    return 0.2*a+0.2*b+0.2*c+0.2*d+0.2*e

def informed_loss(circuit):
    a = metrics.circuit_qubit_count(circuit)
    b = metrics.circuit_two_qubit_gate_count(circuit)
    c = metrics.circuit_gate_count(circuit)
    d = metrics.circuit_clifford_gate_count(circuit)
    e = metrics.circuit_t_gate_count(circuit)
    return 0.1*a+0.2*b+0.1*c+0.1*d+0.5*e

def naive_loss_diagram(diagram):
    
    a = metrics.graph_qubit_count(diagram)
    b = metrics.graph_two_qubit_gate_count(diagram)
    c = metrics.graph_gate_count(diagram)
    d = metrics.graph_clifford_gate_count(diagram)
    e = metrics.graph_t_gate_count(diagram)
    return 0.2*a+0.2*b+0.2*c+0.2*d+0.2*e

def informed_loss_diagram(diagram):
    a = metrics.graph_qubit_count(diagram)
    b = metrics.graph_two_qubit_gate_count(diagram)
    c = metrics.graph_gate_count(diagram)
    d = metrics.graph_clifford_gate_count(diagram)
    e = metrics.graph_t_gate_count(diagram)
    return 0.1*a+0.2*b+0.1*c+0.1*d+0.5*e

