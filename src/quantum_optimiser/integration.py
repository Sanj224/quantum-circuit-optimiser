# Since PyZX cannot convert qiskit circuits directly, this script will convert a qiskit circuit to a PyZX circuit

import pyzx
from qiskit import QuantumCircuit, qasm3, qasm2
from pyzx.circuit import Circuit

def qiskit_to_pyzx(qc):
  qasm_circuit = qasm3.dumps(qc)
  circuit = Circuit.from_qasm(qasm_circuit)
  graph = circuit.to_graph()
  return graph

# this function will convert a PyZX circuit back to a qiskit circuit
def pyzx_to_qiskit(diagram): 
  pyzx_circuit = Circuit.from_graph(diagram)
  qasm_circuit = Circuit.to_qasm(pyzx_circuit)
  circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
  return circuit


