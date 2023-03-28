from estimator.problem.find_paths import global_graph, reduced_combinations
import json
import sys
import networkx as nx
from estimator.problem.LayoutGraphOptimizer.utils import get_movement_instructions_from_path, get_best_combination, flatten
from estimator.problem.LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path, Combination
from estimator.problem.Shuttle.shuttle import Shuttle, ShuttleManager
from estimator.problem.find_paths import VARIANT_MIXES
from re import findall
from typing import List
from more_itertools import distinct_permutations
import matplotlib.pyplot as plt
import heapq
from copy import deepcopy
class Model:
    def __init__(self, graph: LayoutGraph, combinations: dict, variant_mixes: dict):
        f = open('example_program/py/data/board.movements.json')
        movements = json.load(f)
        f = open('example_program/py/data/board.shuttles.json')
        shuttles = json.load(f)
        self.movements = movements
        self.shuttles = shuttles
        self.finished_orders = {}
        self.once = 0
        self.graph = graph
        self.combinations = combinations
        self.variant_mixes = variant_mixes
        # New approach for shuttles
        n_shuttles = 15
        self.shuttleManager = ShuttleManager(n_shuttles)

    def get_initial_mixes(self, columns: int) -> List[dict]:
        # TODO: Implement your own method
        mixes = []
        mix_count = {mix: 0 for mix in self.combinations}
        for col in range(columns):
            shuttle: Shuttle = self.shuttleManager.get_shuttle_by_id(col)

            try:
                shuttle.set_initial_mix_set(True)
            except:
                shuttle.set_movements([])

            # Find the best mix for the given start column
            above_node_type = self.graph.G.nodes[f'{col}_0']['type']
            mix_least_cost = sys.maxsize
            for mix in self.combinations:
                if above_node_type != 'null'\
                   and (above_node_type not in VARIANT_MIXES[mix] or VARIANT_MIXES[mix][above_node_type] == 0):
                    continue

                for combination in self.combinations[mix]:
                    tempCost = self.graph.get_cost(combination, col, only_length=True)
                    if tempCost < mix_least_cost or (tempCost == mix_least_cost and mix_count[mix] < mix_count[best_mix]):
                        mix_least_cost = tempCost
                        best_mix = mix
                        best_combination = combination
            mix_count[best_mix] += 1

            # Set attribute for current mix to shuttle.
            shuttle.set_current_mix(self.variant_mixes[best_mix])
            
            # Append the mix to the list of mixes, with the shuttle id and the mix id
            mixes.append({
                "shuttleId": str(shuttle.get_id()),
                "mixId": best_mix,
                "stationsToVisit": self.convert_combination_to_stations(best_combination)
            })

        return mixes

    def get_next_mix(self, shuttleId: int) -> str:
        '''Get the next mix with the least orders currently in progress (least WIP)'''
        mix = None
        mix_least_WIP = sys.maxsize
        for order in self.finished_orders:
            if (order['started'] < order['quantity']) and (order['started'] - order['completed']) < mix_least_WIP:
                mix_least_WIP = order['started'] - order['completed']
                mix = order['id']

        self.shuttleManager.get_shuttle_by_id(shuttleId).set_current_mix(self.variant_mixes[mix])
        return mix

    def get_current_mix(self, shuttleId: int) -> str:
        """ Get the current mix for a given shuttle

        Args:
            shuttleId (int): The shuttle id

        Returns:
            mix (string): The current mix of the shuttle
            """
        return self.shuttleManager.get_shuttle_by_id(shuttleId).get_current_mix()

    def get_initial_moves(self, columns: int, paths: list) -> list:
        """ Get the initial moves for each shuttle,
        only to be called once at the start of the simulation.

        Args:
            columns (int): The number of columns
            paths (list): A list of paths for each shuttle

        Returns:
            moves (list): A list of moves for each shuttle
            """
        moves = []
        for i in range(columns):
            movements, _ = get_movement_instructions_from_path(paths[i])
            shuttle = self.shuttleManager.get_shuttle_by_id(i)
            shuttle.set_movements(movements)
            moves.append({
                "shuttleId": str(shuttle.get_id()),
                "move": shuttle.get_initial_move()
            })

        return moves

    def get_next_move(self, shuttleId: int):
        """ Get the next move for a given shuttle

        Args:
            shuttleId (int): The shuttle id

        Returns:
            move (string): The next move of the shuttle either 'f', 'b', 'l', 'r'
        """
        return self.shuttleManager.get_shuttle_by_id(shuttleId).get_next_move()

    def get_current_move(self, shuttleId: int):
        """ Get the current move for a given shuttle

        Args:
            shuttleId (int): The shuttle id

        Returns:
            move (string): The current move of the shuttle either 'f', 'b', 'l', 'r'
        """
        return self.shuttleManager.get_shuttle_by_id(shuttleId).get_current_move()

    def is_move_reset(self, shuttleId: int) -> bool:
        """ Check if the shuttle has reached the start position

        Args:
            shuttleId (int): The shuttle id

        Returns:
            is_reset (bool): True if the shuttle has reached the start position"""
        return self.shuttleManager.get_shuttle_by_id(shuttleId).is_move_reset()

    def get_stations_to_visit(self, mixId: int) -> list[str]:
        """Get a list of stations to visit for a given mix
        Parameters:
            mixId {string} -- The mix id
        Returns: 
            stations_to_visit {list} -- A list of stations to visit
        """
        best_combination = get_best_combination(self.combinations[mixId])

        return self.convert_combination_to_stations(best_combination)

    def convert_combination_to_stations(self, combination: Combination) -> list[str]:
        """ Convert a combination to a list of stations to visit

        Arguments:
            combination {Combination} -- The combination to convert

        Returns:
            stations_to_visit {list} -- A list of stations to visit"""
        stations_to_visit = []
        for node in combination.nodes:
            stations_to_visit.append(f'{node[0]}_{node[1]}')

        return stations_to_visit

    def find_optimal_path_from_stations(self, stations_to_visit: list, start_node='start', remove_edges=None, shuttle=None) -> list[Path]:
        """Find the segmented optimal path from a list of stations to the next station

        Args:
            stations {list} -- A list of stations
            start_node {str} -- The start node of the path

        Returns:
            path_nodes {list[Path]} -- A list of nodes in the path
        """
        current_position = None
        if shuttle is not None:
            current_position = shuttle.get_current_position()
        # Remove nodes that are not available for the route.
        reduced_graph = deepcopy(self.graph.reduce(stations_to_visit, current_position=current_position))
        if not remove_edges is None:
            reduced_graph.G.remove_edges_from(remove_edges)
        # Add start and end nodes to the list of stations to visit
        stations_to_visit = [start_node] + stations_to_visit + ['end']

        # Find the optimal path
        path_nodes = []
        segment_indices = [0]
        for i in range(len(stations_to_visit)-1):
            current_station = stations_to_visit[i]
            next_station = stations_to_visit[i+1]

            # Find the shortest path to the next station
            if current_station != next_station:
                try: 
                    nodes_shortest_path = nx.shortest_path(
                        reduced_graph.G, current_station, next_station, weight='weight')
                    # reduced_graph.G.remove_node(current_station)
                except nx.exception.NetworkXNoPath:
                    print(f'No path from {current_station} to {next_station}')
                    return "NO_PATH"


                # Remove the nodes from the handover position to the chosen start lane
                if i == 0 and shuttle == None:
                    startIdx = next(idx-1 for idx, node in enumerate(nodes_shortest_path) if node[-1] == '0')
                    nodes_shortest_path = nodes_shortest_path[startIdx:]

            # If the current and next station are identical go the side (with least cost) and back again
            else:
                tempCost = sys.maxsize
                for out_edge in reduced_graph.G.out_edges(current_station):
                    # If it is in the same row and so far has the lower cost, then save it
                    if out_edge[1][-1] == current_station[-1] and reduced_graph.G.nodes[out_edge[1]]['weight'] < tempCost:
                        tempCost = reduced_graph.G.nodes[out_edge[1]]['weight']
                        adjacent_node = out_edge[1]

                nodes_shortest_path = [current_station] + [adjacent_node] + [next_station]

            # Append the local path to the full path
            # Remove the last node since it is the next station
            path_nodes += nodes_shortest_path[:-1]
            segment_indices.append(len(path_nodes))

        # Add the last station to the path# Add the end node to the path
        path_nodes.append(stations_to_visit[-1])

        # Convert to actual nodes in the networkx format
        path_nodes = [self.graph.G.nodes[node] for node in path_nodes]

        # Obtain the path segments from the full path
        path_node_segments = []
        for i in range(len(segment_indices)-1):
            segment = path_nodes[segment_indices[i]+1:segment_indices[i+1]+1]
            if i == 0:
                # Insert the start node for the first segment
                segment.insert(0, path_nodes[0])

            path_node_segments.append(Path(segment))

        return path_node_segments

    def set_next_movement(self, shuttleId: int, mixId: int, movements: list):
        """ Set the next movement for a given shuttle,
        and set the initial mix to true.

        Args:
            shuttleId (int): The shuttle id 
            mixId (str): The mix id of the format: "mix_a", "mix_..."
            movements (list): A list of movements in the format: ["f", "b", "l", "r", "f", "b", "l", "r", ...]"""

        shuttle = self.shuttleManager.get_shuttle_by_id(shuttleId)
        shuttle.set_current_mix(self.variant_mixes[mixId])  # set current mix
        shuttle.set_movements(movements)  # set movements
        shuttle.set_initial_mix_set(True)  # set initial mix
        shuttle.reset_movement()  # reset movement

    def reset_move(self, shuttleId: int):
        """ Reset the movement of the shuttle
        
        Args:
            shuttleId (int): The shuttle id"""
        shuttle = self.shuttleManager.get_shuttle_by_id(shuttleId)
        shuttle.reset_movement()

    def update_position(self, shuttleId: int):
        """ Update the current position of the shuttle

        Args:
            shuttleId (int): The shuttle id"""

        shuttle = self.shuttleManager.get_shuttle_by_id(shuttleId)
        movement_command = shuttle.get_current_move()
        shuttle.update_position(movement_command)

    def set_start_position(self, shuttleId: int, x: int, y='start'):
        """ Set the start position of the shuttle

        Args:
            shuttleId (int): The shuttle id
            position (list): The start position of the shuttle"""

        shuttle = self.shuttleManager.get_shuttle_by_id(shuttleId)
        shuttle.set_start_position(x_pos=x, y_pos=y)

    def replan(self, shuttleId: int):
        """ Replan the path for the shuttle

        Args:
            shuttleId (int): The shuttle id"""

        shuttle: Shuttle = self.shuttleManager.get_shuttle_by_id(shuttleId)
        start_position = shuttle.get_current_position()

        edges_to_remove = [(shuttle.get_current_position(), shuttle.get_next_position())]

        stations = self.replan_combinations(shuttleId, remove_node=(shuttle.get_next_position()))

        path = self.find_optimal_path_from_stations(stations, start_node=start_position, remove_edges=edges_to_remove, shuttle=shuttle)

        if path == "NO_PATH":
            # Reverse movement step, because no movement occured.
            shuttle.reverse_movement()
            return "NO_PATH"
        
        path = flatten(path)

        movements, _ = get_movement_instructions_from_path(path)
        
        # Change shuttle attributes
        shuttle.set_movements(movements)
        shuttle.reset_movement()

    def replan_combinations(self, shuttleId: int, remove_node=None):
        """ Replan the combination path for the shuttle, if the shuttle is currently in the middle of a combination, and has to replan
        
        Args:
            shuttleId (int): The shuttle id
            
        Returns:
            list: A list of stations to visit in order to complete the order e.g. ['start', (0, 0), (0, 2), (0, 6), 'end'])]"""
        G = deepcopy(self.graph.G)

        shuttle: Shuttle = self.shuttleManager.get_shuttle_by_id(shuttleId)

        mix = shuttle.get_current_mix()
        
        stations_in_mix = {station_type: [node['pos'] for node in G.nodes.values() if node['type'] == station_type]
                           for station_type in mix}

        station_samples = [stations_in_mix[station_type] for station_type in mix for _ in range(mix[station_type])]
        
        # If finished plan from current position to end
        if station_samples == []:
            return []

        station_permutations = [item for item in distinct_permutations(station_samples)]

        current_position = shuttle.get_current_position()

        # format
        x, y = current_position.split('_')
        current_position = (int(x), int(y)) if y != 'start' else (int(x), -1)

        # TODO: FIX DUPLCIATE NAMES .. is fixed
        graphs = self.create_graph(station_permutations, source_pos=current_position, remove_node=remove_node)


        # Find the shortest path for each graph
        shortest_combination = [nx.shortest_path(graph, source='start', target='end', weight='weight') for graph in graphs]

        # Calculate the cost for each path
        costs = [(self.calculate_cost(graph, path), path, graph) for graph, path in zip(graphs, shortest_combination)]
        heapq.heapify(costs)    # min heap

        # Returns the station combination with the lowest cost
        best_combination = heapq.heappop(costs)
     
        # Convert of the new graph to the original names from the global graph
        graph, node_names = best_combination[2], best_combination[1][1:-1] # [1:-1] to remove start and end node
        combination = [graph.nodes[node_name]['original_name'] for node_name in node_names]


        # for graph in graphs:
        #     self.visualize_graph(graph)
        return combination
        

    def calculate_cost(self, graph, path):
        """ Simple function to calculate the cost of a path of combinations
        
        Args:
            graph (nx.DiGraph): The graph
            path (list): The path of combinations
        
        Returns:
            cost (int): The cost of the path"""
        cost = 0
        for i in range(len(path)-1):
            cost += graph[path[i]][path[i+1]]['weight']
        return cost
        
    def create_graph(self, permutation_list, source_pos = (0, 0), start_node="start", end_node="end", remove_node=None):
        """ Create a graph for each permutation
        
        Args:
            permutation_list (list): A list of distinct permutations
            source_pos (tuple): The position of the shuttle
            start_node (str): The start node (current position of the shuttle))
            end_node (str): The end node (the end station)
            
        Returns:
            graphs (list): A list of graphs generated from the permutations"""
        # right now there is created a graph for each permutation (probably not a good idea for scaling)
        graphs = [nx.DiGraph() for _ in permutation_list]

        # add start and end node
        for graph in graphs:
            graph.add_node(start_node, pos=source_pos, original_name='start')
            graph.add_node(end_node, pos=(3, 8), original_name='end')

        # This is very nested ......
        for i, permutation in enumerate(permutation_list):
            graph = graphs[i]
            for j, stations in enumerate(permutation):
                if j == 0:
                    for station in stations:
                        node_name = f'{j}_{station[0]}_{station[1]}'
                        graph.add_node(node_name, pos=station, original_name=f'{station[0]}_{station[1]}')
                        graph.add_edge(start_node, node_name, weight=self.heuristic(graph, start_node, node_name))
                else:
                    for station in stations:
                        for prev_station in permutation[j-1]:
                            node_name = f'{j}_{station[0]}_{station[1]}'
                            prev_node_name = f'{j-1}_{prev_station[0]}_{prev_station[1]}'
                            graph.add_node(node_name, pos=station, original_name=f'{station[0]}_{station[1]}')
                            graph.add_edge(prev_node_name, node_name, weight=self.heuristic(graph, prev_node_name, node_name))
            
            # connect last station to end node
            for last_station in permutation[-1]:
                last_node_name = f'{len(permutation)-1}_{last_station[0]}_{last_station[1]}'
                graph.add_edge(last_node_name, end_node, weight=self.heuristic(graph, last_node_name, end_node))

        nodes_to_remove = []
        if remove_node is not None:
            for graph in graphs:
                for node in graph.nodes:
                    if remove_node == graph.nodes[node]['original_name']:
                        nodes_to_remove.append(node)

        for node in nodes_to_remove:
            for graph in graphs:
                if node in graph.nodes:
                    graph.remove_node(node)

        return graphs
    
    def heuristic(self, graph, node, end_node):
        """ Calculate the heuristic for the djikstra algorithm
        
        Args:
            graph (nx.DiGraph): The graph
            node (tuple/str): The current node
            end_node (tuple/str): The end node
            
        Returns:
            metric (int): The heuristic value"""
        
        start_pos = graph.nodes[node]['pos']
        end_pos = graph.nodes[end_node]['pos']

        # metric is the manhattan distance right now.
        metric = abs(start_pos[0] - end_pos[0]) + abs(start_pos[1] - end_pos[1])
        if end_node == 'end':
            # only y coordinate is important
            metric = abs(start_pos[1] - end_pos[1])

        return metric
    
    def visualize_graph(self, graph):
        a = graph
        # Red if start or end node, else the type of the node.
        colors = ['r' if node in ('start', 'end') else self.graph.G.nodes[node[2:]]['type'] for node in graph.nodes()]

        pos = nx.get_node_attributes(graph ,'pos')
        nx.draw_networkx(graph, with_labels=True, font_color='white', node_size=1000, node_color=colors, font_size=8, pos=pos)
        plt.show()
        

    def processingDone(self, shuttleId: int, type1: str):
        
        shuttle: Shuttle = self.shuttleManager.get_shuttle_by_id(shuttleId)
        shuttle.processing_done(type1)

    def create_graphs(self):
        pass

    def setOnce(self, once):
        self.once = once

    def getOnce(self):
        return self.once

    def set_finished_orders(self, finished_orders):
        self.finished_orders = finished_orders

    def get_finished_orders(self):
        return self.finished_orders
    

if __name__ == "__main__":
    model = Model(global_graph, reduced_combinations, VARIANT_MIXES)
    
    # model.get_initial_mixes(7)
    # model.replan_combinations(0)
    # model.replan(0)