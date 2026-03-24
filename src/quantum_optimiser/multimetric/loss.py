from . import metrics
from .. import integration
import math
import numpy as np

def _compute_stats(circuit,hardware=None):
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
        'g2': two_qubit,
        'g':  len(circuit.data),
        't':  t_gates,
        'd':  circuit.depth(),
        'swap': h
    }


def _normalise(s, baseline):
    """Normalise stats relative to baseline — 1.0 means unchanged, 0.0 means fully reduced."""
    return {
        k: s[k] / baseline[k] if baseline[k] > 0 else 0.0
        for k in s
    }


def naive_loss(circuit, hardware=None, baseline=None):
    s = _compute_stats(circuit)
    if baseline is not None:
        s = _normalise(s, baseline)
    return 0.2*s['q'] + 0.2*s['g2'] + 0.2*s['g'] + 0.2*s['d'] + 0.2*s['t']


def informed_loss(circuit, hardware=None, baseline=None):
    s = _compute_stats(circuit)
    if baseline is not None:
        s = _normalise(s, baseline)
    return 0.1*s['q'] + 0.4*s['g2'] + 0.1*s['g'] + 0.1*s['d'] + 0.3*s['t']


def log_weighted_loss(circuit, hardware=None, baseline=None):
    s = _compute_stats(circuit,hardware)
    if baseline is not None:
        s = _normalise(s, baseline)
    return (
        0.5 * s['q'] +
        2.0 * s['swap'] +
        7.0 * (s['g2']) +
        0.2 * np.log1p(s['g']) +
        2.0 * np.log1p(s['t']) +
        3.0 * np.log1p(s['d'])
    )


def quadratic_loss_circuit(circuit, hardware=None, baseline=None):
    s = _compute_stats(circuit)
    if baseline is not None:
        s = _normalise(s, baseline)
    return (
        0.05  * s['q'] +
        0.10  * (s['g2'] ** 2) +
        0.01  * (s['g']  ** 2) +
        0.005 * (s['d']  ** 2) +
        0.12  * (s['t']  ** 2)
    )


def cost_function_from_circuit(circuit_cost_fn, converter=None, hardware=None, baseline=None):
    if converter is None:
        from .. import integration as _integration
        converter = _integration.pyzx_to_qiskit

    def wrapper(diagram):
        try:
            circuit = converter(diagram)
            return circuit_cost_fn(circuit, hardware, baseline)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return float('inf')

    return wrapper