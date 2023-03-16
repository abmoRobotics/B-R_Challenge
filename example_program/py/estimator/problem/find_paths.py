from copy import deepcopy
from LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path
from LayoutGraphOptimizer.utils import get_movement_instructions_from_path
import json


# Define a placement layout of types of processing stations (b, y, g) and null (no station). A position on the grid is a node.
LAYOUT = {
    'nodes': [
        'b', 'null','y','null','y','null','g',
        'y', 'null', 'y','null','null','null', 'y',
        'null','null','null','null','null','null','g',
        'null','null','null','null','null','null','b',
        'g', 'null','g','null', 'null','null','null',
        'g', 'null','g','null', 'null','b','null'
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

# Create mix specific graphs
graphMixes = {}
combinations = {}
for mix_type in VARIANT_MIXES:
    # Reducing the graph corresponding to the given mix and plotting the result
    graphMixes[mix_type] = deepcopy(graphGlobal)
    graphMixes[mix_type].reduce_graph(VARIANT_MIXES[mix_type])
    #graphMixes[mix].plot_graph(COLOR_MAP)

    # Obtaining all the combinations for the mix and saving the corresponding cost
    combinations[mix_type] = graphGlobal.find_all_combinations_for_mix(VARIANT_MIXES[mix_type])
    for idx, combination in enumerate(combinations[mix_type]):
        if graphGlobal.is_combination_valid(combination, VARIANT_MIXES[mix_type]):
            combinations[mix_type][idx] = (combination, graphGlobal.get_cost_of_combination(combination))
        else:
            raise Exception('Not a valid combination for mix')

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
graphGlobal.plot_graph(COLOR_MAP)