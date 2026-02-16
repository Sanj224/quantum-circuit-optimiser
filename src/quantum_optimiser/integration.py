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
  pyzx_circuit = Circuit.from_graph(diagram)
  qasm_circuit = Circuit.to_qasm(pyzx_circuit)
  circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
  return circuit


def can_convert_to_circuit(diagram):
    """
    Check if a ZX diagram can be converted to a circuit.
    Returns True if conversion succeeds, False otherwise.
    """
    try:
        pyzx_circuit = Circuit.from_graph(diagram)
        qasm_circuit = Circuit.to_qasm(pyzx_circuit)
        circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
        return True
    except Exception:
        return False

