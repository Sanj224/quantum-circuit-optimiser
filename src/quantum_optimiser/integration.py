"""
This file contains the functions to handle conversions between the circuit representation
and its corresponding ZX diagram
"""
import pyzx
from qiskit import QuantumCircuit, qasm3, qasm2
from pyzx.circuit import Circuit
from qiskit import transpile
from qiskit.compiler import transpile
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import InverseCancellation, CXCancellation, Optimize1qGates
from qiskit.circuit.library import SwapGate, HGate, CXGate

def qiskit_to_pyzx(qc):
    """
    This is a PyZX wrapper that turns a qiskit circuit to a pyzx diagram
    Args:
      qc: circuit to be converted
    Return:
      graph: corresponding ZX diagram 
    """
    # always decompose to basic gates PyZX understands
    # set the optimisation level to 0 so that qiskit does not do any optimisation
    qc = transpile(qc,basis_gates=["cx", "h", "t", "tdg", "s", "sdg", "x", "y", "z","rz","swap"],optimization_level=0)
    qasm_circuit = qasm2.dumps(qc)
    circuit = Circuit.from_qasm(qasm_circuit)
    graph = circuit.to_graph()
    return graph

def pyzx_to_qiskit(diagram): 
    """
      Convert a diagram to a circuit, if one exists. We do this by trying different conversions
      Args:
        diagram: ZX diagram to be tested
      Return:
        circuit: the corresponding circuit
    """
    try:
        pyzx_circuit = Circuit.from_graph(diagram)
        qasm_circuit = Circuit.to_qasm(pyzx_circuit)
        circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
    except Exception as e:
        pyzx_circuit = pyzx.extract.extract_circuit(diagram.copy(), optimize_czs=False, optimize_cnots=0, quiet=True)
        pyzx_circuit = Circuit.split_phase_gates(pyzx_circuit)
        pyzx_circuit = pyzx_circuit.to_basic_gates()
        qasm_circuit = Circuit.to_qasm(pyzx_circuit)
        circuit = QuantumCircuit.from_qasm_str(qasm_circuit)

    circuit = transpile(circuit, basis_gates=["cx", "h", "t", "tdg", "s", "sdg", "x", "y", "z", "rz", "swap"], optimization_level=0)

    #convert all rows of 3 cx into a swap
    circuit = fold_swaps(circuit)

    return circuit

def can_convert_to_circuit(diagram):
    """
    Check if a ZX diagram can be converted to a circuit by attempting to convert it
    Args:
      diagram: ZX diagram to test
    Return:
      boolean: True or False depending on whether diagram has a circuit 
    """
    copy = diagram.copy()
    # Work on a copy of the diagram so that we do not change the original diagram
    try:
        pyzx_to_qiskit(copy)
        return True
    except Exception:
         return False 

def fold_swaps(circuit):
    """Replace CX(a,b) CX(b,a) CX(a,b) patterns with SWAP(a,b)
    As pyzx decomposes swap gates, we need to reintroduce them"""
    new_circuit = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
    data = list(circuit.data)
    i = 0
    while i < len(data):
        if (i + 2 < len(data) and
            data[i].operation.name == 'cx' and
            data[i+1].operation.name == 'cx' and
            data[i+2].operation.name == 'cx'):
            
            a0, b0 = data[i].qubits
            a1, b1 = data[i+1].qubits
            a2, b2 = data[i+2].qubits
            
            # CX(a,b) CX(b,a) CX(a,b) = SWAP(a,b)
            if a0 == a2 and b0 == b2 and a0 == b1 and b0 == a1:
                new_circuit.swap(circuit.qubits.index(a0), circuit.qubits.index(b0))
                i += 3
                continue
        
        new_circuit.append(data[i])
        i += 1
    
    return new_circuit