from typing import List
from copy import deepcopy
class Shuttle:
    def __init__(self, shuttle_id, current_move_pos=-1, movements=None, current_pos=None):
        self.shuttle_id = shuttle_id
        self._current_mix = None
        self.current_mix_tester = None
        self.current_move_pos = deepcopy(current_move_pos)
        self.movements = movements
        self.current_position = ['0_start']
        self.visited_processing_stations = []
        self.initial_mix_set = False

    
    def processing_done(self, processing_type):
        """ Function to update the current mix of the shuttle after processing is done.
        
        Args:
            processing_type (str): The type of processing that was done e.g. 'b', 'y', 'g'."""
        self._current_mix[processing_type] -= 1

    def update_position(self, movement_command: str):
        current_position = self.current_position[0]
        x, y = current_position.split('_')
        if y == 'start' and movement_command == 'f':
            y = 0
        elif movement_command == 'f':
            y = int(y) + 1
        elif movement_command == 'b':
            y = int(y) - 1
        elif movement_command == 'r':
            x = int(x) + 1
        elif movement_command == 'l':
            x = int(x) - 1

        # Update the current position
        self.current_position = [f'{x}_{y}']

    def set_start_position(self, x_pos: int, y_pos: int):
        self.current_position = [f'{x_pos}_{y_pos}']

    def set_movements(self, movements):
        """ Function to set the movements of the shuttle, also resets the current move position.
        
        Args:
            movements (List[str]): The movements of the shuttle e.g. ['f', 'r', 'f', 'f']"""
        self.movements = deepcopy(movements)
        self.current_move_pos = -1
    
    def reverse_movement(self):
        """ Function to reverse the movement of the shuttle."""
        self.current_move_pos -= 1


    def get_current_position(self):
        return self.current_position[0]

    def get_id(self):
        return self.shuttle_id

    def get_current_mix(self):
        return self._current_mix

    def set_current_mix(self, _current_mix):
        self._current_mix = deepcopy(_current_mix)

    def get_initial_move(self):
        self.current_move_pos += 1
        return self.movements[self.current_move_pos]

    def get_next_move(self):
        if self.current_move_pos + 1 < len(self.movements) and self._current_mix != ('' or None):
            self.current_move_pos += 1
            return self.movements[self.current_move_pos]
        else:
            return None

    def get_current_move(self):
        if self.current_move_pos < len(self.movements) and self._current_mix != ('' or None):
            return self.movements[self.current_move_pos]
        else:
            return None
    
    def reset_movement(self):
        self.current_move_pos = -1

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
        if shuttle_id == 7 or shuttle_id == '5':
            a= 1
            # print(f'Getting shuttle with id {shuttle_id}')
        for shuttle in self.shuttles:
            if shuttle.get_id() == int(shuttle_id):
                return shuttle
        return None
