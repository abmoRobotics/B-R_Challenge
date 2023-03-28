import sys
import networkx as nx
import matplotlib.pyplot as plt
from itertools import product
from more_itertools import distinct_permutations
from copy import deepcopy
import heapq
import math

class Combination():
    """Defines a simple datastructure that represents a combination"""
    def __init__(self, nodes: list, cost: int = sys.maxsize):
        self.nodes = nodes
        self.cost = cost


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

                # NEW
                if 0 < y < layout['length_y'] - 1:
                    indx_bottom = (y+1) * layout['length_x'] + x
                    node_color_bottom = layout['nodes'][indx_bottom]
                    self.G.add_edge(f"{x}_{y}", f"{x}_{y-1}", weight=weights[node_color_bottom])


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
            #if x < layout['length_x'] - 1: self.G.add_edge(f"{x}_start", f"{x+1}_start", weight=0) # Right
            self.G.add_edge(f"{x}_start", f"{x}_0", weight=weights[layout['nodes'][x]]) # Up
        
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

    def _size(self) -> int:
        """Get the size of the graph in bytes"""
        return sys.getsizeof(self)
    
    def get_cost(self, combination: Combination, startColumn = -1, only_length = False) -> int:
        """Return the cost of a given combination based on Manhattan distance between stations"""
        cost = 0
        
        # Set the initial previous position, either in same column as first position in combination
        # or in the specified start column
        prevNode = (combination.nodes[0][0], -1) if startColumn == -1 else (startColumn, -1)
        for node in combination.nodes:
            # Adds the cost of moving to the node
            cost += self.manhattan_distance(prevNode, node) if prevNode != node else 2
            
            # Adds the cost of processing at the node
            if not only_length: cost += self.G.nodes[f"{node[0]}_{node[1]}"]['weight']
            
            # We traverse the nodes 
            prevNode = node
        
        # Add shortest distance to goal lane
        cost += abs(self.layout['length_y'] - prevNode[1])
        
        return cost
    
    def manhattan_distance(self, pos1, pos2) -> int:
        """Find the Manhattan distance between pos1 and pos2"""
        return abs(pos2[0] - pos1[0]) + abs(pos2[1] - pos1[1])
    
    def is_valid(self, combination: Combination, mix: dict) -> bool:
        """Return whether or not a given combination is valid based on the mix"""
        temp_mix = mix.copy()
        
        # Check that combination is logical (i.e. doesn't move backwards)
        sorted_combination = sorted(combination.nodes, key=lambda x: x[1])
        if combination.nodes != sorted_combination: return False
        
        # Check that the station types in the combination matches that of the mix
        for pos in combination.nodes:
            type = self.G.nodes[f"{pos[0]}_{pos[1]}"]['type']
            
            if type in temp_mix and temp_mix[type] > 0:
                temp_mix[type] -= 1
            else: return False
        
        return True
    
        # This function is used as an heuristic for knn to find the nearest(cheapest) neighbors.
    def heuristic_for_knn(self, point1, point2):
        """ Right now the heuristic is just the Euclidean distance between two points."""
        # heuristic = math.sqrt(sum((p1 - p2) ** 2 for p1, p2 in zip(point1, point2)))
        heuristic = 0
        for i in range(len(point1)):
            heuristic += (point1[i] - point2[i]) ** 2
        # Here we penalize the shuttle for moving to the same station.
        if heuristic == 0: heuristic = 2 
        # Here we disallow the shuttle to move backwards, because it is not allowed to do so.
        if point1[1] > point2[1]: heuristic = sys.maxsize

        return heuristic
    
    def knn(self, point, points, k):
        """ Returns the k nearest neighbors of a point.
        
        Args:
            point: The point for which we want to find the k nearest neighbors.
            points: The list of points from which we want to find the k nearest neighbors.
            k: The number of nearest neighbors to find.
            
        Returns:
            The k nearest neighbors of the point.
        """
        # Euclidean distance is our heuristic for finding the nearest neighbors or the "best/cheapest" next step, so we use a min-heap.
        distances = [(self.heuristic_for_knn(point, other_point), other_point) for other_point in points] 
        heapq.heapify(distances)    # This is a min-heap, so the smallest distance will be at the top.
        return [heapq.heappop(distances)[1] for _ in range(min(k, len(distances)))] # Return the k nearest neighbors

    def cartesian_product(self, k=None, *iterables):
        """ Returns the Cartesian product of the iterables.
        
        Args:
            k: The number of nearest neighbors to find for each point. k scales the number of combinations by k^N, where N is the number of iterables.
            *iterables: The iterables to take the Cartesian product of.
            
        Returns:
            The Cartesian product of the iterables.
        """
        if not iterables:
            return [[]] # If there are no iterables, return an empty list.
        else:
            results = [] # The list of combinations.
            for item in iterables[0]: # For each item in the first iterable.
                if len(iterables) > 1: 
                    neighbors = self.knn(item, iterables[1], k) if k is not None else iterables[1]
                    for sub_product in self.cartesian_product(k, *([neighbors] + list(iterables[2:]))): 
                        results.append([item] + sub_product)

                else:
                    results.append([item]) 
            return results   

    
    def get_all_valid_combinations(self, mix: dict, k: int) -> list[Combination]:
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
            list_iter = [p for p in self.cartesian_product(k, *station_permutation)]
            for item in list_iter:
                # Convert the item to the correct datatype
                item = list(item)

                # Only keep the valid combinations (i.e. those that don't go backwards) and assign the cost
                if not self.is_valid(Combination(item), mix): continue # TODO: Can be removed because we already check this in the heuristic

                final_combinations.append(Combination(item, self.get_cost(Combination(item))))

        # Return the list containing all the combinations
        return final_combinations
        
    def update_weights(self, path: Path, mix_combinations: dict, reset_weights: bool = False):
        """Update the graph and combination weights based on a path. The added (or subtracted if 
        reset_weights is true) weights correspond to the weight of the given node type in that position"""
        # Determine the sign corresponding to whether we are about to start the path (reset_weights = false)
        # or have just ended the path (reset_weights)
        sign = 1 if not reset_weights else -1
        
        # Go through the nodes and the corresponding edges in the path and the different combinations
        for node in path.nodes:
            if self.G.nodes[node['name']]['type'] not in self.weights: continue
            
            # Update the node weight (if sign is 1 we add the weight and if sign is -1 we subtract the weight)
            weight = self.weights[node['type']]
            self.G.nodes[node['name']]['weight'] += sign*weight
            
            # Update the edges going into this node to this weight
            in_edges = self.G.in_edges(node['name'])
            for edge in in_edges:
                self.G.edges[edge]['weight'] += sign*weight

            # If the node is not a station, just continue to next node
            if node['type'] in ('null', 'start', 'end'): continue
            
            # Update the weights of the combinations that include atleast one node from the path
            for mix in mix_combinations:
                for combination in mix_combinations[mix]:
                    if node['pos'] in combination.nodes:
                        combination.cost += sign*weight*combination.nodes.count(node['pos'])
        
    def reduce(self, stations_to_visit: list[str], current_position=None):
        """Return the reduced graph including free nodes and the nodes contained in the stations to visit"""
        reduced_graph = deepcopy(self)
        
        remove_nodes = []
        for node in self.G:
            # Getting the position and type of the node
            type = self.G.nodes[node]['type']
            pos = self.G.nodes[node]['name']
            
            # If the node is start, end, or free station or it is included in the combination, it should be part of the graph
            if ((type in ('null', 'start', 'end') or node in stations_to_visit) or (current_position == pos)): continue
            
            remove_nodes.append(node)


        reduced_graph.G.remove_nodes_from(remove_nodes)
        
        return reduced_graph
    
    # TODO: Figure out where to call this function
    def reduce_and_remove_edge(self, stations_to_vist: list[str], current_pos: str, invalid_pos: str):
        
        reduced_graph = self.reduce(stations_to_vist)
        edge = (current_pos, invalid_pos)
        reduced_graph.G.remove_node(edge)
        return reduced_graph


    def plot(self, color_map: dict):
        """Plot the graph with the node positions as given in the layout"""

        pos = nx.get_node_attributes(self.G,'pos')
        colors = nx.get_node_attributes(self.G,'type')

        # Create list of colors based on node types by iterating through nodes
        colors = [color_map[self.G.nodes[node]['type']] for node in self.G]

        # Draw the graph
        nx.draw_networkx(self.G, with_labels=True, font_color='white', node_size=1000, node_color=colors, font_size=8, pos=pos)
        plt.show()
    
