from copy import deepcopy
from .LayoutGraphOptimizer.LayoutGraph import *
from .LayoutGraphOptimizer.utils import *
import json

# Loading the board data
#f = open("example_program/py/data/board.feed.data_6x7_1.json")
f = open('example_program/py/data/board.feed.data.json')
feed = json.load(f)

# Set colors for nodes, which is needed for plotting the graph. Note that each you need to define the color for each 
#   node type (including null) as well as the 'start' and 'end' node types.
COLOR_MAP = {
    'start': 'black',
    'b': 'blue',
    'y': 'yellow',
    'g': 'green',
    'o': 'orange',
    'end': 'black',
    'null': 'grey'
}

mix_order = ['b', 'y', 'g', 'o']

# Define weights (i.e. processing time) for each node type (including null)
nodes = np.empty((feed['rows'], feed['columns'])).tolist()
WEIGHTS = {mix: 0 for mix in mix_order}
for idx, node in enumerate(feed['stations']):
    color = get_key_from_value(COLOR_MAP, node['color'])
    
    # To ensure the graph is turned the right way
    xIdx = idx % feed['columns']
    yIdx = (feed['rows'] - 1) - math.floor(idx / feed['columns'])
    nodes[yIdx][xIdx] = color
    
    if node['color'] not in WEIGHTS: WEIGHTS[color] = node['time']

# Define a placement layout of types of processing stations (b, y, g) and null (no station). A position on the grid is a node.
LAYOUT = {'nodes': flatten(nodes),
    'length_x': feed['columns'],
    'length_y': feed['rows']}

# The different variant mixes, including color and quantity
VARIANT_MIXES = {}
for mix in feed['orders']:
    VARIANT_MIXES[mix['id']] = {color: 0 for color in WEIGHTS if color != 'null'}
    for mix_color in mix['recipe']:
        color = get_key_from_value(COLOR_MAP, mix_color['color'])
        VARIANT_MIXES[mix['id']][color] = mix_color['quantity']


# Create a global graph from layout and weights
print('Creating graph...')
global_graph = LayoutGraph(LAYOUT, WEIGHTS)

# Calculate the best combinations of stations for the different mixes
reduced_combinations = {}
for mix_type in VARIANT_MIXES:
    # Obtaining all the valid combinations and corresponding cost
    reduced_combinations[mix_type] = global_graph.find_combinations(VARIANT_MIXES[mix_type], method="knn", k=3)
    
    # Keep only the 50 best combinations in order from best to worst
    reduced_combinations[mix_type] = get_best_combinations(reduced_combinations[mix_type], 50)

# ### FOR TESTING ###
# best_combination = get_best_combination(combinations['mix_a'])

# path = []
# for pos in best_combination.nodes:
#     path.append(global_graph.G.nodes[f'{pos[0]}_{pos[1]}'])

# global_graph.update_weights(Path(path), combinations)
# ### FOR TESTING ###


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
global_graph.plot(COLOR_MAP)
