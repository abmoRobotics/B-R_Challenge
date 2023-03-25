import networkx as nx
import numpy as np
import random
from .LayoutGraph import LayoutGraph, Path, Combination
from sys import maxsize

NUM_SHUTTLES = 15

def random_layout(board_dimensions: tuple, variant_mixes: dict) -> LayoutGraph:
    """TODO: Create a random layout with the given dimensions and node types"""
    
    num_cells = board_dimensions[0]*board_dimensions[1] # The number of cells in the area where stations can be placed
    
    node_types = []
    for mix in variant_mixes:
        for type in variant_mixes[mix]:
            if variant_mixes[mix][type] > 0 and type not in node_types: node_types.append(type)
    
    # Select a random number of stations to place
    num_stations = random.randrange(len(node_types), min(NUM_SHUTTLES, num_cells))
    
    station_types = [node for node in node_types]
    for _ in range(num_stations-len(node_types)):
        station_types.append(random.choice(node_types))
    
    idx_placements = random.sample(range(num_cells), num_stations)

    nodes = ['null' for _ in range(num_cells)]
    for i, idx_placement in enumerate(idx_placements):
        nodes[idx_placement] = station_types[i]
    
    layout = {'nodes': nodes,
              'length_x': board_dimensions[0],
              'length_y': board_dimensions[1]}
    
    return layout

def find_optimal_station_amounts(board_dimensions: tuple, production_order: dict, placement_costs: dict, processing_times: dict) -> dict:
    # Determine how many station visits for each type are required by the production order
    station_visits = {station_type: 0 for station_type in production_order['mix_a']['mix']}
    for mix_type, items in production_order.items():
        for station_type, val in items['mix'].items():
            station_visits[station_type] += items['amount']*val
    
    # Connversion to numpy vectors and matrices
    PC_vec = np.array([placement_costs[station] for station in placement_costs])
    PT_vec = np.array([processing_times[station] for station in processing_times if station != 'null'])
    SV_mat = np.diag([station_visits[station] for station in station_visits])
    
    optimal_stations = {'amounts': (), 
                       'cost': maxsize}
    max_stations = min(NUM_SHUTTLES, board_dimensions[0]*board_dimensions[1])
    # Go through the possible station distributions based on the maximum number of stations allowed
    for b in range(1, max_stations+1): # Blue stations
        for y in range(1, max_stations+1-b):
            for g in range(1, max_stations+1-b-y):
                x_vec = np.array([b, y, g])
                
                # Calculating the cost for the given station distribution
                cost = np.dot(x_vec, PC_vec) + max( np.divide(np.matmul(SV_mat, PT_vec), x_vec) )
                
                # If the cost is the lowest so far, save it
                if cost < optimal_stations['cost']: 
                    optimal_stations['amounts'] = (b, y, g)
                    optimal_stations['cost'] = cost
  
    return optimal_stations
    

def find_paths(layout, weights, prod_order) -> dict:
    """TODO: Find all paths for a given production order"""

    raise NotImplementedError("This function is not implemented yet.")

def calculate_costs(paths, prod_order, layout, station_placement_cost):
    """TODO: Create a cost function that takes the paths and the layout and returns the overall cost of the production order"""

    raise NotImplementedError("This function is not implemented yet.")

def get_movement_instructions_from_path(path: Path):
    """Get the movement instructions and start position for a given path"""
    # Movement instructions are like ["f", "l", "f", "r", "f"]
    # Path is a path object

    # Calculate the difference between the x and y coordinates of two consecutive nodes
    # If the current node is the start node, then the robot needs to move forward
    # If the current node is not the start node, then the robot needs to move forward, left or right
    # If the next node is the end node, then the robot needs to move forward
    # If the difference in position is (0, 1), then the robot needs to move forward
    # If the difference in position is (0, -1), then the robot needs to move backward
    # If the difference in position is (1, 0), then the robot needs to move right
    # If the difference in position is (-1, 0), then the robot needs to move left

    # Check validity of path with start and end node
    if (path[0]['type'] != 'start' and 'start' not in path[0]['name']) or path[-1]['type'] != 'end':
        raise ValueError('Path does not start with start node or end with end node')
        

    movement_instructions = []

    # Iterate through the path nodes and compare the position of the current node with the next node
    for i in range(0, len(path)-1):

        # Get the current node
        current_node = path[i]

        next_node = path[i + 1]

        # If the current node is the end node, then the robot needs to move forward to reach the end position
        if next_node['type'] == 'end':
            movement_instructions.append('f')
            break
        

        # Get the current node position and the next node position
        current_node_position = current_node['pos']
        next_node_position = next_node['pos']

        # Calculate the difference between the x and y coordinates of the two nodes
        x_diff = next_node_position[0] - current_node_position[0]
        y_diff = next_node_position[1] - current_node_position[1]

        # If the first node is the start node, then the robot needs to move forward
        #if i == 0:
        #    movement_instructions.append('f')
        # If the first node is not the start node, then the robot needs to move forward, left or right
        #else:
        # If the difference in position is (0, 1), then the robot needs to move forward
        if x_diff == 0 and y_diff == 1:
            movement_instructions.append('f')
        # If the difference in position is (0, -1), then the robot needs to move backward
        elif x_diff == 0 and y_diff == -1:
            movement_instructions.append('b')
        # If the difference in position is (1, 0), then the robot needs to move right
        elif x_diff == 1 and y_diff == 0:
            movement_instructions.append('r')
        # If the difference in position is (-1, 0), then the robot needs to move left
        elif x_diff == -1 and y_diff == 0:
            movement_instructions.append('l')
    
    # Calculate the start row as the direct position under the first node in the path (ignore the start node in the graph)
    start_row = path[0]['pos'][0]
    
    return movement_instructions, start_row

def get_best_combinations(combination_list: list[Combination], n) -> list[Combination]:
    """Return a list of the n best combinations from the "combination_list" based on cost 
    and sorted from best to worst.
    """
    if len(combination_list) < n: n = len(combination_list)
    
    sorted_combination_list = sorted(combination_list, key=lambda x: x.cost)
    
    return sorted_combination_list[0:n]

def get_best_combination(combinations: list[Combination]) -> Combination:
    return min(combinations, key=lambda x : x.cost)

def get_worst_combination(combinations: list[Combination]) -> Combination:
    return max(combinations, key=lambda x : x.cost)

def flatten(l: list[list]) -> list:
    return [item for sublist in l for item in sublist]

