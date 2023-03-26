from typing import List

class Shuttle:
    def __init__(self, shuttle_id, current_mix='', current_move_pos=-1, movements=None, current_pos=None):
        self.shuttle_id = shuttle_id
        self.current_mix = current_mix
        self.current_move_pos = current_move_pos
        self.movements = movements
        self.current_position = ['0_start']
        self.visited_processing_stations = []
        self.processing_stations = []
        self.initial_mix_set = False


    def set_processing_stations(self, processing_stations):
        self.processing_stations = processing_stations

    def get_processing_stations(self):
        return self.processing_stations

    def update_position(self, movement_command: str):
        current_position = self.current_position[0]
        x, y = current_position.split('_')

        #x = current_position[:split_index]
       # y = current_position[split_index + 1:]
        if y == 'start':
            y = 0
        elif movement_command == 'f':
            y = int(y) + 1
        elif movement_command == 'b':
            y = int(y) - 1
        elif movement_command == 'r':
            x = int(x) + 1
        elif movement_command == 'l':
            x = int(x) - 1


        # check if previous position was a processing station,
        # if so, add it to the list of visited processing stations
        if self.current_position[0] in self.processing_stations:
            index = self.processing_stations.index(self.current_position[0]) 
            self.processing_stations.pop(index)

        # Update the current position
        self.current_position = [f'{x}_{y}']




    def set_start_position(self, x_pos: int, y_pos: int):
        self.current_position = [f'{x_pos}_{y_pos}']

    def set_movements(self, movements):
        self.movements = movements
        self.current_move_pos = -1

    def set_current_pos(self, current_pos):
        self.current_pos = current_pos

    def get_current_position(self):
        return self.current_position[0]

    def get_id(self):
        return self.shuttle_id

    def get_current_mix(self):
        return self.current_mix

    def set_current_mix(self, current_mix):
        self.current_mix = current_mix

    def get_initial_move(self):
        self.current_move_pos += 1
        return self.movements[self.current_move_pos]

    def get_next_move(self):
        if self.current_move_pos + 1 < len(self.movements) and self.current_mix != ('' or None):
            self.current_move_pos += 1
            return self.movements[self.current_move_pos]
        else:
            return None

    def get_current_move(self):
        if self.current_move_pos < len(self.movements) and self.current_mix != ('' or None):
            return self.movements[self.current_move_pos]
        else:
            return None

    def reset_movement(self):
        self.current_move_pos = -1

    def get_movement(self, goal_position):
        x_diff = goal_position[0] - self.current_position[0]
        y_diff = goal_position[1] - self.current_position[1]

        if x_diff == 0 and y_diff == 0:
            return None
        elif x_diff > 0:
            return 'r'
        elif x_diff < 0:
            return 'l'
        elif y_diff > 0:
            return 'f'
        elif y_diff < 0:
            return 'b'

    
    def get_next_position(self):
        current_position = self.current_position[0]
        x, y = current_position.split('_')

        if y == 'start':
            y = 0
        elif self.get_current_move() == 'f':
            y = int(y) + 1
        elif self.get_current_move() == 'b':
            y = int(y) - 1
        elif self.get_current_move() == 'r':
            x = int(x) + 1
        elif self.get_current_move() == 'l':
            x = int(x) - 1

        return f'{x}_{y}'




    
    def is_move_reset(self):
        return self.current_move_pos == -1 or not self.initial_mix_set

    def set_initial_mix_set(self, initial_mix_set: bool):
        self.initial_mix_set = initial_mix_set



class ShuttleManager:
    def __init__(self, number_of_shuttles):
        # Create a list of shuttles
        for i in range(number_of_shuttles):
            self.shuttles: List[Shuttle] = [Shuttle(i) for i in range(number_of_shuttles)]

    def get_shuttle_by_id(self, shuttle_id):
        for shuttle in self.shuttles:
            if shuttle.get_id() == int(shuttle_id):
                return shuttle
        return None
