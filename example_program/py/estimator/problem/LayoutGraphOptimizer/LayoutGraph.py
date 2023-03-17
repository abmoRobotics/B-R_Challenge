import networkx as nx
import matplotlib.pyplot as plt
from typing import List
from itertools import product
from more_itertools import distinct_permutations
import sys
from copy import deepcopy

class Path():
    """A more sohisticated path class that can be used to store a path in the graph and
    provides additional functionality and operators.
    """
    def __init__(self, nodes: list):
        """Construct a path from a list of nodes

        Args:
            nodes (list): List of nodes that define the path
                Note that nodes must be gives as [{'pos': (0, 0), 'type': 'b', 'weight': 3, 'name': '2_0'}, ...]
        """
        self.nodes = nodes
        self.node_names = [node['name'] for node in nodes]
        self.cost = sum([n['weight'] for n in self.nodes])
    
    def __str__(self) -> str:
        node_names_str = ' > '.join(self.node_names)
        return f"Path: {node_names_str}; Cost: {self.cost}"

    def __getitem__(self, key: int) -> dict:
        return self.nodes[key]

    def __len__(self) -> int:
        return len(self.nodes)

    def count_type(self, type: str) -> int:
        """Count the number of nodes of a specific type in the path

        Args:
            type (str): Type of node to count

        Returns:
            int: Number of nodes of the given type
        """
        return len([n for n in self.nodes if n['type'] == type])

class LayoutGraph():
    """Class that represents a graph model of a layout and provides methods
    to find shortest paths for specific variant mixes to be manufactured.
    """

    def __init__(self, layout: dict, weights: dict):
        """Construct a graph from a layout and weights

        Args:
            layout (dict): Dictionary that defines the layout following a predefined schema (see README.md)
            weights (dict): Dictionary of weights that defines the cost of traversing a node of a specific type
        """
        self.layout = layout
        self.weights = weights

        self.G = nx.DiGraph()

        # Terminology and naming rules:
        # x: column index / x-position cartesian (from 0 to length_x - 1)
        # y: row index / y-position cartesian (from 0 to length_y - 1)
        # node: node at position (x, y) with name f"{x}_{y}" and color type as given in layout['nodes']
        # cost: cost of traversing a path from start to end node (sum of weights of traversed nodes)

        # Iterate through nodes and add them to the graph
        for y in range(0, layout['length_y']):
            for x in range(0, layout['length_x']):
                indx = y * layout['length_x'] + x
                node_color = layout['nodes'][indx]
                node_name= f"{x}_{y}"
                self.G.add_node(node_name, pos=(x, y), type=node_color, weight=weights[node_color], name=node_name)


        # Iterate through nodes and add edges to the graph
        for y in range(0, layout['length_y']):
            for x in range(0, layout['length_x']):
                indx = y * layout['length_x'] + x
                node_color = layout['nodes'][indx]

               # Add edge to the right
                if x < layout['length_x'] - 1:
                    indx_right = y * layout['length_x'] + x + 1
                    node_color_right = layout['nodes'][indx_right]
                    self.G.add_edge(f"{x}_{y}", f"{x+1}_{y}", weight=weights[node_color_right])
                
                # Add edge to the bottom
                if y < layout['length_y'] - 1:
                    indx_bottom = (y+1) * layout['length_x'] + x
                    node_color_bottom = layout['nodes'][indx_bottom]
                    self.G.add_edge(f"{x}_{y}", f"{x}_{y+1}", weight=weights[node_color_bottom])

                # Add edge to the left
                if x > 0:
                    indx_left = y * layout['length_x'] + x - 1
                    node_color_left = layout['nodes'][indx_left]
                    self.G.add_edge(f"{x}_{y}", f"{x-1}_{y}", weight=weights[node_color_left])

        # Add nodes and edges for starting lane
        for x in range(0, layout['length_x']):
            self.G.add_node(f"{x}_start", pos=(x, -1), type='null', weight=0, name=f"{x}_start")
        
        for x in range(0, layout['length_x']):
            if x > 0: self.G.add_edge(f"{x}_start", f"{x-1}_start", weight=0) # Left
            if x < layout['length_x'] - 1: self.G.add_edge(f"{x}_start", f"{x+1}_start", weight=0) # Right
            self.G.add_edge(f"{x}_start", f"{x}_0", weight=0) # Up
        
        # Add start and end node
        self.G.add_node('start', pos=(layout['length_x'], -1), type='start', weight=0, name='start')
        self.G.add_node('end', pos=(round(layout['length_x']/2) - 1, layout['length_y']), type='end', weight=0, name='end')

        # Add edges from start to first node in start lane
        # for x in range(0, layout['length_x']):
        #     self.G.add_edge('start', f"{x}_0", weight=0)
        self.G.add_edge('start', f"{layout['length_x']-1}_start", weight=0)
        
        # Add edges from last row to end
        for x in range(0, layout['length_x']):
            self.G.add_edge(f"{x}_{layout['length_y']-1}", 'end', weight=0)

    def _get_path_with_attributes(self, path: list) -> list:
        """Helper function to get the attributes of a path"""
        return [self.G.nodes(data=True)[p] for p in path]

    def _get_size_of_graph(self):
        """Get the size of the graph in bytes"""
        return sys.getsizeof(self)
    
    def get_cost_of_combination(self, combination: List[tuple], startColumn = -1) -> int:
        """Return the cost of a given combination based on Manhattan distance between stations"""
        cost = 0
        
        # Set the initial previous position, either in same column as first position in combination
        # or in the specified start column
        prevPos = (combination[0][0], -1) if startColumn == -1 else (startColumn, -1)
        for pos in combination:
            cost += self.manhattan_distance(prevPos, pos) if prevPos != pos else 2
            #cost += self.G.nodes[f"{pos[0]}_{pos[1]}"]['type']
            
            prevPos = pos
        
        # Add shortest distance to goal lane
        cost += abs(self.layout['length_y'] - prevPos[1])
        
        return cost
    
    def manhattan_distance(self, pos1, pos2) -> int:
        """Find the Manhattan distance between pos1 and pos2"""
        return abs(pos2[0] - pos1[0]) + abs(pos2[1] - pos1[1])
    
    def is_combination_valid(self, combination: List[tuple], mix: dict) -> bool:
        """Return whether or not a given combination is valid based on the mix"""
        temp_mix = mix.copy()
        
        # Check that combination is logical (i.e. doesn't move backwards)
        sorted_combination = sorted(combination, key=lambda x: x[1])
        if list(combination) != sorted_combination: return False
        
        # Check that the station types in the combination matches that of the mix
        for pos in combination:
            node_type = self.G.nodes[f"{pos[0]}_{pos[1]}"]['type']
            
            if node_type in temp_mix and temp_mix[node_type] > 0:
                temp_mix[node_type] -= 1
            else: return False
        
        return True
    
    def get_all_valid_combinations_for_mix(self, mix: dict) -> List[tuple]:
        """Find all the different combinations of stations for the given mix"""
        # Order the possible stations on the board by station type
        stations_in_mix = {station_type: [] for station_type in mix}
        for node in self.G.nodes:
            node_type = self.G.nodes[node]['type']
            if node_type in mix:
                stations_in_mix[node_type].append(self.G.nodes[node]['pos'])
        
        # Initialising lists for combinations
        station_samples = []
        station_permutations = []
        final_combinations = []
        
        # Insert the amount of samples we need for each type as the station positions for that type
        # Example: b=1, g=2 -> [(xb_1, yb_1,), ...], [(xg_1, yg_1,), ...], [(xg_1, yg_1,), ...]
        for station_type in mix:
                for _ in range(mix[station_type]):
                    station_samples.append(stations_in_mix[station_type])
        
        # Obtain the distinct permutations of the sample positions from before
        # Example: b=1, g=2 -> [b, g, g], [g, b, g], [g, g, b]
        list_iter = distinct_permutations(station_samples)
        for item in list_iter:
            station_permutations.append(item)
        
        # Obtain all the combinations from the possible stations for each station type and for each permutation
        # Example (one permutation): b = 1, g = 2 and b=[(1, 2), (4, 3)], g=[(3, 2), (4, 6), (6, 5)] ->
        # [(1, 2), (3, 2), (4, 6)], [(1, 2), (3, 2), (6, 5)], [(1, 2), (4, 6), (6, 5)], [(4, 3), (3, 2), (4, 6)], [(4, 3), (3, 2), (6, 5)], [(4, 3), (4, 6), (6, 5)]
        for station_permutation in station_permutations:
            list_iter = [p for p in product(*station_permutation)]
            for item in list_iter:
                final_combinations.append(item)
        
        # Only keep the valid combinations (i.e. those that don't go backwards) and assign the cost
        final_combinations = [(combination, self.get_cost_of_combination(combination))\
                               for combination in final_combinations if self.is_combination_valid(combination, mix)]

        # Return the list containing all the combinations
        return final_combinations
    
    def get_sorted_best_combinations(self, combination_list: List[tuple], n) -> List[tuple]:
        """Return a list of the n best combinations from the "combination_list" based on cost 
        and sorted from best to worst.
        """
        if len(combination_list) < n: n = len(combination_list)
        
        sorted_combination_list = sorted(combination_list, key=lambda x: x[1])
        
        return sorted_combination_list[0:n]

    def find_all_paths_for_mix(self, mix: dict, cutoff: int = None) -> List[Path]:
        """TODO: Find all paths for a given mix"""

        raise NotImplementedError("This function is not implemented yet.")
        
    def find_shortest_paths_for_mix(self, mix: dict, cutoff: int = None) -> List[Path]:
        """TODO: Find the shortest paths for a given mix"""
        
        raise NotImplementedError("This function is not implemented yet.")
    
    def plot_graph(self, color_map: dict):
        """Plot the graph with the node positions as given in the layout"""

        pos = nx.get_node_attributes(self.G,'pos')
        colors = nx.get_node_attributes(self.G,'type')

        # Create list of colors based on node types by iterating through nodes
        colors = [color_map[self.G.nodes[node]['type']] for node in self.G]

        # Draw the graph
        nx.draw_networkx(self.G, with_labels=True, font_color='white', node_size=1000, node_color=colors, font_size=8, pos=pos)
        plt.show()

    
    def reduce_graph(self, combination: List[tuple]):
        """Return the reduced graph including free nodes and the nodes contained in the combination"""
        reduced_graph = deepcopy(self)
        
        remove_nodes = []
        for node in self.G:
            # Getting the position and type of the node
            pos = self.G.nodes[node]['pos']
            type = self.G.nodes[node]['type']
            
            # If the node is start, end, or free station or it is included in the combination, it should be part of the graph
            if (type == 'null' or type == 'start' or type == 'end' or pos in list(combination[0])): continue
            
            remove_nodes.append(node)

        reduced_graph.G.remove_nodes_from(remove_nodes)
        
        return reduced_graph
        
            
        
    # def find_best_combinations_for_mix(self, mix: dict, n: int) -> List[List[str]]:
    #     """Find the n best combinations for the mix in order from best to worst"""
    #     combination_list = []
    #     stations_in_mix = {}
    #     stations_in_mix['type'] = {station_type: [] for station_type in mix}
    #     stations_in_mix['row'] = {i: [] for i in range(self.layout['length_x'])}
        
    #     # Append the positions of the stations from the graph
    #     for node in self.G.nodes:
    #         node_type = self.G.nodes[node]['type']
    #         if node_type in mix:
    #             stations_in_mix['type'][node_type].append(self.G.nodes[node]['pos'])
                
    #             row = self.G.nodes[node]['pos'][1]
    #             stations_in_mix['row'][row].append((node_type, self.G.nodes[node]['pos']))
        
    #     # NOT DONE
        
    #     return combination_list