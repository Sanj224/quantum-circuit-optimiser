"""
This file contains a set of sample hardwares
"""

from . import hardware_map
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

  
# Testing hardware
connections = [[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,0]]
linkedHardware= hardware_map.hardware_map(9,connections)


#  IBM's 127 qubit processor: Sherbrooke
backend = FakeSherbrooke()
connections = list(backend.coupling_map.get_edges())
num_qubits = backend.num_qubits
sherbrooke = hardware_map.hardware_map(num_qubits, connections)

# Google's Sycamore 53-qubit processor
sycamore_connections = [
    # Row 0
    (0, 1),
    # Row 1
    (1, 2), (2, 3),
    # Row 2
    (3, 4), (4, 5), (5, 6), (6, 7),
    # Row 3
    (7, 8), (8, 9), (9, 10), (10, 11), (11, 12),
    # Row 4
    (12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18),
    # Row 5
    (18, 19), (19, 20), (20, 21), (21, 22), (22, 23), (23, 24), (24, 25),
    # Row 6
    (25, 26), (26, 27), (27, 28), (28, 29), (29, 30), (30, 31),
    # Row 7
    (31, 32), (32, 33), (33, 34), (34, 35), (35, 36),
    # Row 8
    (36, 37), (37, 38), (38, 39), (39, 40),
    # Row 9
    (40, 41), (41, 42), (42, 43),
    # Row 10
    (43, 44), (44, 45),
    # Row 11
    (45, 46),
    # Vertical connections between rows
    (0, 3), (1, 4), (2, 5), (3, 6), (4, 7), (5, 8), (6, 9),
    (7, 12), (8, 13), (9, 14), (10, 15), (11, 16), (12, 17),
    (13, 18), (14, 19), (15, 20), (16, 21), (17, 22), (18, 23),
    (19, 25), (20, 26), (21, 27), (22, 28), (23, 29), (24, 30),
    (25, 31), (26, 32), (27, 33), (28, 34), (29, 35), (30, 36),
    (31, 37), (32, 38), (33, 39), (34, 40),
    (36, 41), (37, 42), (38, 43),
    (40, 44), (41, 45),
    (43, 46),
    (46, 47), (47, 48), (48, 49), (49, 50), (50, 51), (51, 52),
    (44, 47), (45, 48), (46, 49), (47, 50), (48, 51), (49, 52),
]

sycamore = hardware_map.hardware_map(53, sycamore_connections)