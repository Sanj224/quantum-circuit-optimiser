# Since PyZX cannot convert qiskit circuits directly, this script will convert a qiskit circuit to a PyZX circuit

import pyzx
from qiskit import QuantumCircuit, qasm3, qasm2
from pyzx.circuit import Circuit
from qiskit import transpile


def qiskit_to_pyzx(qc):
  """
  Turn a qiskit circuit to a pyzx diagram
  """
  qasm_circuit = qasm3.dumps(qc)
  circuit = Circuit.from_qasm(qasm_circuit)
  graph = circuit.to_graph()
  return graph

# this function will convert a PyZX circuit back to a qiskit circuit
def pyzx_to_qiskit(diagram): 
  """
  # this function will convert a PyZX circuit back to a qiskit circuit

  """
  try:
    pyzx_circuit =Circuit.from_graph(diagram)
    qasm_circuit = Circuit.to_qasm(pyzx_circuit)
    circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
    
  except:
    pyzx_circuit = pyzx.extract.extract_circuit(diagram.copy(), optimize_czs=False, optimize_cnots=0, quiet=True)
    pyzx_circuit = Circuit.to_basic_gates(pyzx_circuit)
    pyzx_circuit = Circuit.split_phase_gates(pyzx_circuit)
    qasm_circuit = Circuit.to_qasm(pyzx_circuit)
    qasm_circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
    circuit = transpile(qasm_circuit,basis_gates=["h","s","sdg","t","tdg","x","z","cx","cz"],optimization_level=0)
  return circuit


def can_convert_to_circuit(diagram):
    """
    Check if a ZX diagram can be converted to a circuit.
    Returns True if conversion succeeds, False otherwise.
    """
    copy = diagram.copy()
    try:
        pyzx_to_qiskit(copy)
        return True
    except Exception:
        return False

