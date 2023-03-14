import networkx as nx
import matplotlib.pyplot as plt
from typing import List

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

        # Add start and end node
        self.G.add_node('start', pos=(round(layout['length_x']/2), -1), type='start', weight=0, name='start')
        self.G.add_node('end', pos=(round(layout['length_x']/2), layout['length_y']), type='end', weight=0, name='end')

        # Add nodes from start to first row
        for x in range(0, layout['length_x']):
            self.G.add_edge('start', f"{x}_0", weight=0)
        

        # Add nodes from last row to end
        for x in range(0, layout['length_x']):
            self.G.add_edge(f"{x}_{layout['length_y']-1}", 'end', weight=0)

    def _get_path_with_attributes(self, path: list) -> list:
        """Helper function to get the attributes of a path"""
        return [self.G.nodes(data=True)[p] for p in path]

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

    def reduce_graph(self, mix: dict):
        remove_nodes = []
        
        for node in self.G:
            node_type = self.G.nodes[node]['type']
            
            # If the node is start, end, or free station or it is included in the mix, it should be part of the graph
            if (node_type == 'null' or node_type == 'start' or node_type == 'end')\
                or (node_type in mix and mix[node_type] > 0):
                continue
            
            remove_nodes.append(node)
        
        self.G.remove_nodes_from(remove_nodes)