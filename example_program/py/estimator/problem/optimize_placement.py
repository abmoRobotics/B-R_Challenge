import random
from tqdm import tqdm
from LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path
from LayoutGraphOptimizer.utils import *
from find_paths import VARIANT_MIXES


###### CONSTANTS ######

# Set colors for nodes when drawing graph. Note that each you need to define the color for each 
#   node type (including null) as well as the start and end nodes.
COLOR_MAP = {
    'start': 'black',
    'b': 'blue',
    'y': 'darkgoldenrod',
    'g': 'green',
    'end': 'black',
    'null': 'grey'
}

# Production Order: we need to manufacture each mix a certain amount of times and have
# to find an optimal placement of the processing stations to minimize the total cost
PROD_ORDER = {
    'mix_a': {
        'amount': 5,
        'mix': {
            'b': 2,
            'y': 3,
            'g': 0
        }
    },
    'mix_b': {
        'amount': 6,
        'mix': {
            'b': 1,
            'y': 1,
            'g': 0
        }
    },
    'mix_c': {
        'amount': 3,
        'mix': {
            'b': 0,
            'y': 2,
            'g': 2
        }
    }
}

# We are setting a certain cost for the placement of stations. The more stations are placed of each type
# onto the layout, the more costly the entire configuration will be. So with more stations in the layout
# you might be able to produce your variant mixes faster, but will face a higher initial cost of placement.
STATION_PLACEMENT_COST = {
    'b': 10,
    'y': 10,
    'g': 10
}

# Define the processed time for each station, which in graph terminology is the weights for each node type (including null).
# Here, we assign a cost the the 'null' station (which is a position in the layout without a processing station) to
# penalize longer paths over empty positions on the board.
STATION_PROCESSING_TIME = {
    'b': 3,
    'y': 3,
    'g': 5,
    'null': 1
}

##### MAIN #####

EPOCHS = 100    # How many iterations of samples should be taken from the solution space (if we brute force it)
SIZE_X = 4      # Size of the layout
SIZE_Y = 4      # Size of the layout
BOARD_DIMENSIONS = (SIZE_X, SIZE_Y)

node_types = get_node_types(VARIANT_MIXES)

### FOR TESTING ###
# station_amounts = find_optimal_station_amounts(BOARD_DIMENSIONS, PROD_ORDER, STATION_PLACEMENT_COST, STATION_PROCESSING_TIME)

# randomLayout = random_layout(BOARD_DIMENSIONS, node_types)
# randomGraph  = LayoutGraph(randomLayout, STATION_PROCESSING_TIME)
# randomCost = estimate_layout_cost(randomGraph, PROD_ORDER, STATION_PLACEMENT_COST, num_combinations=3)
# randomGraph.plot(COLOR_MAP)

# adjustedLayout = adjust_layout(randomLayout, node_types, 3)
# adjustedGraph = LayoutGraph(adjustedLayout, STATION_PROCESSING_TIME)
# adjustedCost = estimate_layout_cost(adjustedGraph, PROD_ORDER, STATION_PLACEMENT_COST, num_combinations=3)
# adjustedGraph.plot(COLOR_MAP)
###################

itr = 0
bestCost = maxsize
prevBestCost = 0
bestGraphs = []
while itr < 5: # abs(bestCost - prevBestCost) > 1
    randomGraphs = bestGraphs
    prevBestCost = bestCost
    
    # Iterate through samples and find the best solution. Can you think of a better way to find the best solution using less naive optimization methods?
    for epoch in tqdm(range(0, EPOCHS)):
        if itr == 0:
            # Sample from solution space or create a random layout
            newLayout = random_layout(BOARD_DIMENSIONS, node_types)
        else:
            tempGraph, _ = random.choice(bestGraphs)
            newLayout = adjust_layout(tempGraph.layout, node_types, 1)
        
        # Create a graph based on the new layout
        newGraph = LayoutGraph(newLayout, STATION_PROCESSING_TIME)
        
        # Calculate the costs for the paths. What do we want to minizine? You might need to come up with a useful metric here.
        graphCost = estimate_layout_cost(newGraph, PROD_ORDER, STATION_PLACEMENT_COST)
        
        # Save the results somehow
        randomGraphs.append((newGraph, graphCost))

    # Keep the best graphs
    bestGraphs = sorted(randomGraphs, key=lambda x: x[1])
    nKeep = min(EPOCHS, 10) # Keeping the 10 best
    bestGraphs = bestGraphs[0:nKeep]
    bestCost = bestGraphs[0][1]
    
    print(bestCost)
    
    itr += 1

# Find the best result based on the production cost and save it to a file
bestGraph = min(bestGraphs, key=lambda x : x[1])