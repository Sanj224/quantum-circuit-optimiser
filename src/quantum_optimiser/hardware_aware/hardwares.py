from . import hardware_map
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke


# Testing hardware
conns = [[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,0]]
linkedHardware= hardware_map.hardware_map(9,conns)


# IBM's 127 qubit processor: Sherbrooke
backend = FakeSherbrooke()
connections = list(backend.coupling_map.get_edges())
num_qubits = backend.num_qubits
sherbrooke = hardware_map.hardware_map(num_qubits, connections)

