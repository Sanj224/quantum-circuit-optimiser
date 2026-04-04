"""
This file contains a library of cost functions
"""

import numpy as np

def _compute_stats(circuit,hardware=None):
    """
    Compute all the metrics of the circuit
    If a hardware is specified, compute the routing overhead
    """
    two_qubit = 0
    t_gates = 0
    used_qubits = set()
    if hardware is not None:
        h= hardware.heuristic(circuit)
    else:
        h=0
    for instruction in circuit.data:
        op = instruction.operation
        for qubit in instruction.qubits:    
            used_qubits.add(circuit.qubits.index(qubit))
        if op.num_qubits == 2:
            two_qubit += 1
        if op.name == 't':
            t_gates += 1

    return {
        'q':  len(used_qubits) if used_qubits else circuit.num_qubits,
        'g2': two_qubit+h,
        'g':  len(circuit.data)+h,
        't':  t_gates,
        'd':  circuit.depth(),
    }



def naive_loss(circuit, hardware=None):
    s = _compute_stats(circuit,hardware)
    return 0.2*s['q'] + 0.2*s['g2'] + 0.2*s['g'] + 0.2*s['d'] + 0.2*s['t']


def informed_loss(circuit, hardware=None):
    s = _compute_stats(circuit,hardware)
    return 0.1*s['q'] + 0.4*s['g2'] + 0.1*s['g'] + 0.1*s['d'] + 0.3*s['t']


def log_weighted_loss(circuit, hardware=None):
    s = _compute_stats(circuit,hardware)
  
    return (
        0.5 * s['q'] +
        7.0 * (s['g2']) +
        0.2 * np.log1p(s['g']) +
        2.0 * np.log1p(s['t']) +
        3.0 * np.log1p(s['d'])
    )


def quadratic_loss_circuit(circuit, hardware=None):
    s = _compute_stats(circuit,hardware)
    return (
        0.05  * s['q'] +
        0.10  * (s['g2'] ** 2) +
        0.01  * (s['g']  ** 2) +
        0.005 * (s['d']  ** 2) +
        0.12  * (s['t']  ** 2)
    )


def cost_function_from_circuit(circuit_cost_fn, converter=None, hardware=None):
    """
    Create a wrapper for a specified cost function so that we can directly apply it to a diagram
    """
    if converter is None:
        from .. import integration as _integration
        converter = _integration.pyzx_to_qiskit

    def wrapper(diagram):
        try:
            circuit = converter(diagram)
            return circuit_cost_fn(circuit, hardware)
        except Exception as e:
            "If we fail, set the cost to infinity"
            import traceback
            traceback.print_exc()
            return float('inf')

    return wrapper