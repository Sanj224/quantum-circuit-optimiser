from . import hardware_map
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke


# Testing hardware
conns = [[0,1],[1,2],[2,3],[3,4]]
linkedHardware= hardware_map.hardware_map(5,conns)


# IBM's 127 qubit processor 
backend = FakeSherbrooke()
connections = list(backend.coupling_map.get_edges())
num_qubits = backend.num_qubits
sherbrooke = hardware_map.hardware_map(num_qubits, connections)

