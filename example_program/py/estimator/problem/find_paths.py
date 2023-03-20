from copy import deepcopy
from LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path
from LayoutGraphOptimizer.utils import *
import json


# Define a placement layout of types of processing stations (b, y, g) and null (no station). A position on the grid is a node.
LAYOUT = {
    'nodes': [
        'b', 'null','y','null','y','null','g',
        'y', 'null', 'y','null','null','null', 'y',
        'null','null','null','null','null','null','g',
        'null','null','null','null','null','null','b',
        'g', 'null','g','null', 'null','null','null',
        'g', 'null','g','null', 'b','null','null'
    ],
    'length_x': 7,
    'length_y': 6
}

# Define weights (i.e. processing time) for each node type (including null)
WEIGHTS = {
    'b': 3,
    'y': 3,
    'g': 5,
    'null': 1,
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
VARIANT_MIXES = {
    'mix_a': {
        'g': 2,
        'y': 1,
        'b': 0
     },
    'mix_b': {
        'g': 0,
        'y': 0,
        'b': 1
     },
    'mix_c': {
        'g': 1,
        'y': 0,
        'b': 1
     },
    'mix_d': {
        'g': 0,
        'y': 1,
        'b': 1
     }
}

# Create a global graph from layout and weights
print('Creating graph...')
graphGlobal = LayoutGraph(LAYOUT, WEIGHTS)

# Calculate the best combinations of stations for the different mixes
combinations = {}
for mix_type in VARIANT_MIXES:
    # Obtaining all the valid combinations and corresponding cost
    combinations[mix_type] = graphGlobal.get_all_valid_combinations(VARIANT_MIXES[mix_type])
    
    # Keep only the 50 best combinations in order from best to worst
    combinations[mix_type] = get_sorted_best_combinations(combinations[mix_type], 50)

### FOR TESTING ###
best_combination = get_best_combination(combinations['mix_a'])

path = []
for pos in best_combination.nodes:
    path.append(graphGlobal.G.nodes[f'{pos[0]}_{pos[1]}'])

graphGlobal.update_weights(Path(path), combinations)
### FOR TESTING ###


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

# ONLY COMMENT IN WHEN WE WANT TO STORE THE MOVEMENTS
#json_object = json.dumps(store_movements, indent=2)
#with open("example_program/py/data/board.movements.json", "w") as outfile:
#    outfile.write(json_object)

# Plot the graph (without paths)
graphGlobal.plot(COLOR_MAP)