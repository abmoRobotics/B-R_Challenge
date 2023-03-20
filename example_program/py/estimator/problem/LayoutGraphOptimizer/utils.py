import networkx as nx
import numpy as np
import random

from .LayoutGraph import LayoutGraph, Path, Combination


def random_layout(length_x, length_y, node_types):
    """TODO: Create a random layout with the given dimensions and node types"""

    raise NotImplementedError("This function is not implemented yet.")

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
    if path[0]['type'] != 'start' or path[-1]['type'] != 'end':
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
        if i == 0:
            movement_instructions.append('f')
        # If the first node is not the start node, then the robot needs to move forward, left or right
        else:
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
    start_row = path[1]['pos'][0]
    
    return movement_instructions, start_row

def get_sorted_best_combinations(combination_list: list[Combination], n) -> list[Combination]:
    """Return a list of the n best combinations from the "combination_list" based on cost 
    and sorted from best to worst.
    """
    if len(combination_list) < n: n = len(combination_list)
    
    sorted_combination_list = sorted(combination_list, key=lambda x: x.cost)
    
    return sorted_combination_list[0:n]

def get_best_combination(combinations: list[Combination]) -> Combination:
    return min(combinations, key=lambda x : x.cost)
