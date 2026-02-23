from . import metrics
from .. import integration
import math
import numpy as np
# Add up all the metrics

def naive_loss(circuit, hardware=None):
    a = metrics.circuit_qubit_count(circuit)
    b = metrics.circuit_two_qubit_gate_count(circuit)
    if hardware is not None:
        b = b + hardware.heuristic(circuit)
    c = metrics.circuit_gate_count(circuit)
    d = metrics.circuit_depth(circuit)
    e = metrics.circuit_t_gate_count(circuit)
    return 0.2*a+0.2*b+0.2*c+0.2*d+0.2*e

def informed_loss(circuit, hardware=None):
    a = metrics.circuit_qubit_count(circuit)
    b = metrics.circuit_two_qubit_gate_count(circuit)
    if hardware is not None:
        b = b + hardware.heuristic(circuit)

    c = metrics.circuit_gate_count(circuit)
    d = metrics.circuit_depth(circuit)
    e = metrics.circuit_t_gate_count(circuit)
    return 0.1*a+0.2*b+0.1*c+0.1*d+0.5*e


def log_weighted_loss(circuit, hardware=None):
    import numpy as np
    
    q = metrics.circuit_qubit_count(circuit)
    g2 = metrics.circuit_two_qubit_gate_count(circuit)
    if hardware is not None:
        g2 = g2 + hardware.heuristic(circuit)

    g = metrics.circuit_gate_count(circuit)
    t = metrics.circuit_t_gate_count(circuit)
    d = circuit.depth()
    
    return (
        1.0 * q +
        3.0 * np.log1p(g2) +      
        0.2 * np.log1p(g) +
        8.0 * np.log1p(t) +       
        0.5 * np.log1p(d)
    )

def quadratic_loss_circuit(circuit,hardware=None):
    q = metrics.circuit_qubit_count(circuit)
    g2 = metrics.circuit_two_qubit_gate_count(circuit)
    if hardware is not None:
        g2 = g2 + hardware.heuristic(circuit)

    g = metrics.circuit_gate_count(circuit)
    d = metrics.circuit_depth(circuit)
    t = metrics.circuit_t_gate_count(circuit)

    w_q  = 0.05
    w_g2 = 0.08
    w_g  = 0.01
    w_d = 0.005
    w_t  = 0.12

    return (
        w_q  * q +
        w_g  * g +
        d * (w_d**2) +
        w_g2 * (g2 ** 2) +
        w_t  * (t ** 2)
    )


def cost_function_from_circuit(circuit_cost_fn, converter=None,hardware=None):
    """
    Wraps a circuit-based cost function to work with diagrams.
    """
    if converter is None:
        from .. import integration as _integration  
        converter = _integration.pyzx_to_qiskit
    
    call_count = [0]
    
    def wrapper(diagram):
        call_count[0] += 1
        try:
            circuit = converter(diagram)
            cost = circuit_cost_fn(circuit,hardware)
            return cost
        except Exception as e:
            print(f"ERROR in cost function (call {call_count[0]}): {e}")
            import traceback
            traceback.print_exc()
            return float('inf')
    
    return wrapper
