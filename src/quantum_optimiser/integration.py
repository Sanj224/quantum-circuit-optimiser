# Since PyZX cannot convert qiskit circuits directly, this script will convert a qiskit circuit to a PyZX circuit

import pyzx
from qiskit import QuantumCircuit, qasm3
from pyzx.circuit import Circuit

def qiskitToPyZX(qc):
  qasmCircuit = qasm3.dumps(qc)
  return Circuit.from_qasm(qasmCircuit)

# this function will convert a PyZX circuit back to a qiskit circuit
# def pyzxToQiskit(circuit): 

