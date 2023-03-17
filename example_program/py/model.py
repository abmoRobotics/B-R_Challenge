import json, sys

class Model:
    def __init__(self):
        f = open('example_program/py/data/board.movements.json')
        movements = json.load(f)
        f = open('example_program/py/data/board.shuttles.json')
        shuttles = json.load(f)
        self.movements = movements
        self.shuttles = shuttles
        self.finished_orders = {}
        self.once = 0


    def get_initial_mixes(self, columns):
        # TODO: Implement your own method
        mixes = []
        for col in range(columns):
            shuttle = self.shuttles[col]
            
            try:
                shuttle['movements'] = self.movements[shuttle['currentMix']][str(col)]['0']['instr']
                shuttle['initialMixSet'] = True
            except:
                shuttle.movements = []
            mixes.append({
                "shuttleId": shuttle['shuttleId'],
                "mixId": shuttle['currentMix']
            })
                    
        return mixes
    
    def get_next_mix (self, shuttleId):
        # TODO: Implement your own method 
        mix = None
        for order in self.finished_orders:
            # order = self.finished_orders[j]
            if (order['started'] < order['quantity']):
                mix = order['id']
                break

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
    
    def get_initial_moves (self, columns):
        # TODO: Implement your own method
        moves = []
        for j in range(columns):
            shuttle = self.shuttles[j]
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
    
    def set_next_movement (self, shuttleId, mixId, startStation):
        # TODO: Implement your own method
        for shuttle in self.shuttles:
            if (shuttle['shuttleId'] == shuttleId):
                shuttle['currentMix'] = mixId
                shuttle['movements'] = self.movements[mixId][startStation['start']][startStation['pos']]['instr']
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