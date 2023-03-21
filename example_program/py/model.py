import json, sys
import networkx as nx
from estimator.problem.LayoutGraphOptimizer.utils import get_movement_instructions_from_path, get_best_combination, flatten
from estimator.problem.LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path, Combination
from estimator.problem.find_paths import VARIANT_MIXES
from re import findall

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

    def get_initial_mixes(self, columns):
        # TODO: Implement your own method
        mixes = []
        mix_count = {mix: 0 for mix in self.combinations}
        for col in range(columns):
            shuttle = self.shuttles[col]
            
            try:
                #shuttle['movements'] = self.movements[shuttle['currentMix']][str(col)]['0']['instr']
                shuttle['initialMixSet'] = True
            except:
                shuttle.movements = []
            
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
                "shuttleId": shuttle['shuttleId'],
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

        for shuttle in self.shuttles:
            if shuttle['shuttleId'] == shuttleId:
                shuttle['currentMovePos'] = -1
                shuttle['currentMix'] = mix

        return mix
    
    def get_current_mix (self, shuttleId):
        # TODO: Implement your own method
        mix = None
        for shuttle in self.shuttles:
            if (shuttle['id'] == shuttleId):
                mix = shuttle['currentMix']

        return mix
    
    def get_initial_move(self, shuttleId):
        # TODO: Implement your own method
        moves = None
        for shuttle in self.shuttles:
            if (shuttle['shuttleId'] == shuttleId):
                shuttle['currentMovePos'] += 1
                moves = shuttle['movements'][shuttle['currentMovePos']]

        return moves
    
    def get_initial_moves (self, columns, paths):
        # TODO: Implement your own method
        moves = []
        for j in range(columns):
            shuttle = self.shuttles[j]
            test = paths[j]
            shuttle['movements'], _ = get_movement_instructions_from_path(paths[j])
            shuttle['currentMovePos'] += 1
            moves.append({
                "shuttleId": shuttle['shuttleId'],
                "move": shuttle['movements'][shuttle['currentMovePos']]
            })

        return moves
    
    def get_next_move (self, shuttleId):
        # TODO: Implement your own method
        direction = None
        for shuttle in self.shuttles:
            if shuttle['shuttleId'] == shuttleId and shuttle['currentMix'] != '' and shuttle['currentMix'] is not None:
                shuttle['currentMovePos'] += 1
                try:
                    direction = shuttle['movements'][shuttle['currentMovePos']]
                except:
                    print ('get_move_error')

        return direction
    
    def get_current_move (self, shuttleId):
        # TODO: Implement your own method
        direction = None
        for shuttle in self.shuttles:
            if shuttle['shuttleId'] == shuttleId and shuttle['currentMix'] != '' and shuttle['currentMix'] is not None:
                try:
                    direction = shuttle['movements'][shuttle['currentMovePos']]
                except:
                    print ('get_move_error')

        return direction

    def is_move_reset(self, shuttleId):
        # TODO: Implement your own method
        isMoveReset = False
        for shuttle in self.shuttles:
            if shuttle['shuttleId'] == shuttleId:
                isMoveReset = (shuttle['currentMovePos'] != -1 or not shuttle['intialMixSet'])
        
        return isMoveReset
    
    def get_station_pos(self, stationId: str) -> tuple:
        translation = [7, -1]
        newPos = [0, 0]
        
        orignalPos = [int(i) for i in findall(r"\d", stationId)]
        
        newPos[0] = -orignalPos[1] + translation[0]
        newPos[1] = orignalPos[0] + translation[1]
        
        return tuple(newPos)
    
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
    
    def find_optimal_path_from_stations (self, stations_to_visit, start_node = "start") -> list[Path]:
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
            nodes_shortest_path = nx.shortest_path(reduced_graph.G, current_station, next_station, weight='weight')    
            
            # Remove the nodes from the handover position to the chosen start lane
            if i == 0: 
                startIdx = next(idx-1 for idx, node in enumerate(nodes_shortest_path) if node[-1] == '0')
                nodes_shortest_path = nodes_shortest_path[startIdx:]
            
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

    def get_start_station (self, mixId):
        # TODO: Implement your own method
        optimalCost = sys.maxsize
        optimalStartingPos = None
        optimalPos = None
        for startingPos, startingData in self.movements[mixId].items():
            for idx, movementData in startingData.items():
                if optimalCost > movementData['cost']:
                    optimalCost = movementData['cost']
                    optimalPos = idx
                    optimalStartingPos = startingPos

        return { 'cost': optimalCost, 'pos': optimalPos, 'start': optimalStartingPos }
    
    def set_next_movement (self, shuttleId, mixId, movements):
        # TODO: Implement your own method
        for shuttle in self.shuttles:
            if (shuttle['shuttleId'] == shuttleId):
                shuttle['currentMix'] = mixId
                shuttle['movements'] = movements
                shuttle['intialMixSet'] = True
                shuttle['currentMovePos'] = -1
    
    def setOnce (self, once):
        self.once = once

    def getOnce (self):
        return self.once

    def set_finished_orders (self, finished_orders):
        self.finished_orders = finished_orders

    def get_finished_orders (self):
        return self.finished_orders
    
