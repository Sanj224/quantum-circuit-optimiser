"""
This file contains the functions to handle conversions between the circuit representation
and its corresponding ZX diagram
"""
import pyzx
from qiskit import QuantumCircuit, qasm3, qasm2
from pyzx.circuit import Circuit
from qiskit import transpile
from qiskit.compiler import transpile
   
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
    #See if the diagram can be converted by spider level transformations
    pyzx_circuit =Circuit.from_graph(diagram)
    qasm_circuit = Circuit.to_qasm(pyzx_circuit)
    circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
    
  except:
    #If not, try to extract it using pyzx.extract
    pyzx_circuit = pyzx.extract.extract_circuit(diagram.copy(), optimize_czs=False, optimize_cnots=0, quiet=True)
    pyzx_circuit = Circuit.to_basic_gates(pyzx_circuit)
    pyzx_circuit = Circuit.split_phase_gates(pyzx_circuit)
    qasm_circuit = Circuit.to_qasm(pyzx_circuit)
    circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
  #Transpile the circuit back to our gate set
  circuit = transpile(circuit,basis_gates=["cx", "h", "t", "tdg", "s", "sdg", "x", "y", "z","rz","swap"],optimization_level=0)
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