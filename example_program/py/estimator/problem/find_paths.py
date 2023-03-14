from copy import deepcopy
from LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path
from LayoutGraphOptimizer.utils import get_movement_instructions_from_path
import json


# Define a placement layout of types of processing stations (b, y, g) and null (no station). A position on the grid is a node.
LAYOUT = {
    'nodes': [
        'b', 'b', 'b', 'y',
        'b', 'b', 'y', 'y',
        'y', 'null', 'null', 'g',
        'y', 'null', 'null', 'g'
    ],
    'length_x': 4,
    'length_y': 4
}

# Define weights (i.e. processing time) for each node type (including null)
WEIGHTS = {
    'b': 3,
    'y': 3,
    'g': 5,
    'null': 1
}

# Set colors for nodes, which is needed for plotting the graph. Note that each you need to define the color for each 
#   node type (including null) as well as the 'start' and 'end' node types.
COLOR_MAP = {
    'start': 'black',
    'b': 'blue',
    'y': 'darkgoldenrod',
    'g': 'green',
    'end': 'black',
    'null': 'grey'
}

# Variant Mix A: How many of each type of node should be traversed?
VARIANT_MIX_A = {
    'b': 1,
    'y': 0,
    'g': 2
}

VARIANT_MIXES = {
    'A': {
        'b': 1,
        'y': 0,
        'g': 2
     },
    'B': {
        'b': 0,
        'y': 2,
        'g': 1
     },
    'C': {
        'b': 1,
        'y': 1,
        'g': 0
     },
    'D': {
        'b': 1,
        'y': 2,
        'g': 1
     }
}

# Create a global graph from layout and weights
print('Creating graph...')
graphGlobal = LayoutGraph(LAYOUT, WEIGHTS)

# Create mix specific graphs
graphMixes = {}
for mix in VARIANT_MIXES:
    graphMixes[mix] = deepcopy(graphGlobal)
    graphMixes[mix].reduce_graph(VARIANT_MIXES[mix])
    graphMixes[mix].plot_graph(COLOR_MAP)
    


# Call the algorithm to find the shortest or all paths for the variant mix

# Print found paths

# Get the movement instructions for the paths
#   Like so: movement_instructions_mix_a, start_row = get_movement_instructions_from_path(path)

# Example:
# first store the id of the mix
# then store the value of the starting position/column on the starting row
# then store the value of iterable choices ( 0 - n ) and then store the instructions and the cost
# accordingly:
store_movements = {
#   "mix_a": {
#     "1": {
#       "0": {
#         "instr": [ "f", "r", "r", "f", "r", "f", "f", "f", "l", "l", "f", "f" ],
#         "cost": 21
#       },
#       "1": {
#         "instr": [ "f", "r", "r", "f", "r", "f", "f", "l", "f", "l", "f", "f" ],
#         "cost": 21
#       }
#     }
#   },
#   "mix_b": {
#     "0": {
#       "0": {
#         "instr": ["f", "r", "f", "f", "r", "r", "r", "r", "f", "f", "f", "f" ],
#         "cost": 13
#       }
#     },
#     "1": {
#       "0": {
#         "instr": ["f", "f", "f", "r", "r", "r", "r", "f", "r", "f", "f", "f" ],
#         "cost": 13
#       }
#     }
#   }
}
json_object = json.dumps(store_movements, indent=2)
with open("example_program/py/data/board.movements.json", "w") as outfile:
    outfile.write(json_object)

# Plot the graph (without paths)
graphGlobal.plot_graph(COLOR_MAP)