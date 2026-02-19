from . import hardware_map

## Testing hardware

connections = [[0,1],[0,2],[0,3],[0,4],[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
defaultHardware = hardware_map.hardware_map(5,connections)

conns = [[0,1],[1,2],[2,3],[3,4]]
linkedHardware= hardware_map.hardware_map(5,conns)


