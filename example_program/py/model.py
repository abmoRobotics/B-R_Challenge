import json, sys
import networkx as nx
from estimator.problem.LayoutGraphOptimizer.utils import get_movement_instructions_from_path, get_best_combination, flatten
from estimator.problem.LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path, Combination
from estimator.problem.Shuttle.shuttle import Shuttle, ShuttleManager
from estimator.problem.find_paths import VARIANT_MIXES
from re import findall
from typing import List
class Model:
    def __init__(self, graph: LayoutGraph, combinations: dict):
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

        # New approach for shuttles
        n_shuttles = 15
        self.new_shuttles = ShuttleManager(n_shuttles)

    def get_initial_mixes(self, columns):
        # TODO: Implement your own method
        mixes = []
        mix_count = {mix: 0 for mix in self.combinations}
        for col in range(columns):
            shuttle: Shuttle = self.new_shuttles.get_shuttle_by_id(col)
            
            try:
                shuttle.set_initial_mix_set(True)
            except:
                shuttle.set_movements([])
            
            # Find the best mix for the given start column
            above_node_type = self.graph.G.nodes[f'{col}_0']['type']
            mix_least_cost = sys.maxsize
            for mix in self.combinations:
                if above_node_type != 'null'\
                   and (above_node_type not in VARIANT_MIXES[mix] or VARIANT_MIXES[mix][above_node_type] == 0): continue
                
                for combination in self.combinations[mix]:
                    tempCost = self.graph.get_cost(combination, col, only_length=True)
                    if tempCost < mix_least_cost or (tempCost == mix_least_cost and mix_count[mix] < mix_count[best_mix]):
                        mix_least_cost = tempCost
                        best_mix = mix
                        best_combination = combination
            mix_count[best_mix] += 1
            
            mixes.append({
                "shuttleId": str(shuttle.get_id()),
                "mixId": best_mix,
                "stationsToVisit": self.convert_combination_to_stations(best_combination)
            })
        
        return mixes
    
    def get_next_mix (self, shuttleId):
        '''Get the next mix with the least orders currently in progress (least WIP)'''
        mix = None
        mix_least_WIP = sys.maxsize
        for order in self.finished_orders:
            if (order['started'] < order['quantity']) and (order['started'] - order['completed']) < mix_least_WIP: 
                mix_least_WIP = order['started'] - order['completed']
                mix = order['id']


        self.new_shuttles.get_shuttle_by_id(shuttleId).set_current_pos('start')
        self.new_shuttles.get_shuttle_by_id(shuttleId).set_current_mix(mix)
        return mix
    
    def get_current_mix (self, shuttleId):
        return self.new_shuttles.get_shuttle_by_id(shuttleId).get_current_mix()
    
    def get_initial_move(self, shuttleId):
        return self.new_shuttles.get_shuttle_by_id(shuttleId).get_next_move()
    
    def get_initial_moves (self, columns, paths):
        moves = []
        for i in range(columns):
            shuttle = self.new_shuttles.get_shuttle_by_id(i)
            movements, _ = get_movement_instructions_from_path(paths[i])
            shuttle.set_movements(movements)
            moves.append({
                "shuttleId": str(shuttle.get_id()),
                "move": shuttle.get_next_move()
            })

        return moves
    def get_next_move (self, shuttleId):
        direction = None
        if self.new_shuttles.get_shuttle_by_id(shuttleId).get_current_mix() != ('' or None):
            direction = self.new_shuttles.get_shuttle_by_id(shuttleId).get_next_move()
        return direction
    
    def get_current_move (self, shuttleId):
        direction = None
        if self.new_shuttles.get_shuttle_by_id(shuttleId).get_current_mix() != ('' or None):
            direction = self.new_shuttles.get_shuttle_by_id(shuttleId).get_current_move()
        return direction

    def is_move_reset(self, shuttleId):
        return self.new_shuttles.get_shuttle_by_id(shuttleId).is_move_reset()
    
    def get_stations_to_visit (self, mixId) -> list[str]:
        """Get a list of stations to visit for a given mix
        Parameters:
            mixId {string} -- The mix id
        Returns: 
            stations_to_visit {list} -- A list of stations to visit
        """
        best_combination = get_best_combination(self.combinations[mixId])
        
        return self.convert_combination_to_stations(best_combination)


    def convert_combination_to_stations(self, combination: Combination) -> list[str]:
        stations_to_visit = []
        for node in combination.nodes:
            stations_to_visit.append(f'{node[0]}_{node[1]}')
            
        return stations_to_visit
    
    def find_optimal_path_from_stations (self, stations_to_visit, start_node = 'start') -> list[Path]:
        """Find the segmented optimal path from a list of stations to the next station
        
        Arguments:
            stations {list} -- A list of stations
            
        Returns:
            path {Path} -- The path consisting of the nodes to visit
        """
        
        # Remove nodes that are not available for the route.
        reduced_graph = self.graph.reduce(stations_to_visit)
        
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
                nodes_shortest_path = nx.shortest_path(reduced_graph.G, current_station, next_station, weight='weight')
                
                # Remove the nodes from the handover position to the chosen start lane
                if i == 0: 
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
            path_nodes += nodes_shortest_path[:-1] # Remove the last node since it is the next station
            segment_indices.append(len(path_nodes))
        
        path_nodes.append(stations_to_visit[-1]) # Add the last station to the path# Add the end node to the path
        
        # Convert to actual nodes in the networkx format
        path_nodes = [self.graph.G.nodes[node] for node in path_nodes]
        
        # Obtain the path segments from the full path
        path_node_segments = []
        for i in range(len(segment_indices)-1):
            segment = path_nodes[segment_indices[i]+1:segment_indices[i+1]+1]
            if i == 0: segment.insert(0, path_nodes[0]) # Insert the start node for the first segment
            
            path_node_segments.append(Path(segment))
        
        return path_node_segments
    
    def set_next_movement (self, shuttleId, mixId, movements):
        shuttle = self.new_shuttles.get_shuttle_by_id(shuttleId)
        shuttle.set_current_mix(mixId) # set current mix
        shuttle.set_movements(movements) # set movements
        shuttle.set_initial_mix_set(True) # set initial mix 
        shuttle.reset_movement() # reset movement
    
    def setOnce (self, once):
        self.once = once

    def getOnce (self):
        return self.once

    def set_finished_orders (self, finished_orders):
        self.finished_orders = finished_orders

    def get_finished_orders (self):
        return self.finished_orders
    
