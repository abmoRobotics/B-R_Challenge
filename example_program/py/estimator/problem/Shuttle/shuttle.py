from typing import List
from copy import deepcopy
class Shuttle:
    """ Class to represent a shuttle.
    
    Args:
        shuttle_id (int): The id of the shuttle.
        current_move_pos (int): The current position in the movements list e.g. 2
        movements (List[str]): The movements of the shuttle e.g. ['f', 'r', 'f', 'f']
        current_pos (List[str]): The current position of the shuttle e.g. ['0_0'].

    Attributes:
        shuttle_id (int): The id of the shuttle.
        _current_mix (dict): The current mix of the shuttle e.g. {'b': 2, 'y': 1, 'g': 1}.
        current_move_pos (int): The current position in the movements list e.g. 2
        movements (List[str]): The movements of the shuttle e.g. ['f', 'r', 'f', 'f']
        current_position (List[str]): The current position of the shuttle e.g. ['0_0'].
        initial_mix_set (bool): Whether the initial mix has been set or not.

        """
    def __init__(self, shuttle_id, current_move_pos=-1, movements=None, current_pos=None):
        """ Constructor for the Shuttle class."""
        self.shuttle_id = shuttle_id
        self._current_mix = None
        self.current_mix_tester = None
        self.current_move_pos = deepcopy(current_move_pos)
        self.movements = movements
        self.current_position = ['0_start']
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
        """ Function to set the start position of the shuttle.
        
        Args:
            x_pos (int): The x position of the shuttle.
            y_pos (int): The y position of the shuttle."""
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
        """ Returns the current position of the shuttle.
        
        Returns:
            str: The current position of the shuttle of format 'x_y' e.g. '0_0'."""
        return self.current_position[0]

    def get_id(self):
        """ Returns the id of the shuttle.
        
        Returns:
            int: The id of the shuttle."""
        return self.shuttle_id

    def get_current_mix(self):
        """ Returns the orders left in the current mix of the shuttle.
        
        Returns:
            dict: The orders left in the current mix of the shuttle e.g. {'b': 2, 'y': 1, 'g': 1}"""
        return self._current_mix

    def set_current_mix(self, current_mix):
        """ Function to set the current mix of the shuttle.
        
        Args:
            current_mix (dict): The current mix of the shuttle e.g. {'b': 2, 'y': 1, 'g': 1}"""
        self._current_mix = deepcopy(current_mix)

    def get_initial_move(self):
        """ Returns the first movement of the shuttle, and updates the current move position.
        
        Returns:
            str: The first movement of the shuttle e.g. 'f'."""
        self.current_move_pos += 1
        return self.movements[self.current_move_pos]

    def get_next_move(self):
        """ Returns the next movement of the shuttle, and updates the current move position.
        
        Returns:
            str: The next movement of the shuttle e.g. 'f'."""
        if self.current_move_pos + 1 < len(self.movements) and self._current_mix != ('' or None):
            self.current_move_pos += 1
            return self.movements[self.current_move_pos]
        else:
            return None

    def get_current_move(self):
        """ Returns the current movement of the shuttle.
        
        Returns:
            str: The current movement of the shuttle e.g. 'f'."""
        if self.current_move_pos < len(self.movements) and self._current_mix != ('' or None):
            return self.movements[self.current_move_pos]
        else:
            return None
    
    def reset_movement(self):
        """ Updates the current move position to -1."""   
        self.current_move_pos = -1

    def get_next_position(self):
        """ Returns the next position of the shuttle.
        
        Returns:
            str: The next position of the shuttle of format 'x_y' e.g. '0_0'."""
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
        """ Returns whether the current move position is -1.
        
        Returns:
            bool: True if the current move position is -1, False otherwise."""
        return self.current_move_pos == -1 or not self.initial_mix_set

    def set_initial_mix_set(self, initial_mix_set: bool):
        self.initial_mix_set = initial_mix_set



class ShuttleManager:
    """ Class to manage the shuttles.
    
    Args:
        number_of_shuttles (int): The number of shuttles to create.
        
    Attributes:
        shuttles (List[Shuttle]): The list of shuttles.
        
    Methods:
        get_shuttle_by_id: Returns the shuttle with the given id."""
    def __init__(self, number_of_shuttles):
        """ Constructor for the ShuttleManager class"""
        for i in range(number_of_shuttles):
            self.shuttles: List[Shuttle] = [Shuttle(i) for i in range(number_of_shuttles)]

    def get_shuttle_by_id(self, shuttle_id: int) -> Shuttle:
        """ Returns the shuttle with the given id.
        
        Args:
            shuttle_id (int): The id of the shuttle.
        
        Returns:
            Shuttle: The shuttle with the given id or None if no shuttle with the given id exists."""
        for shuttle in self.shuttles:
            if shuttle.get_id() == int(shuttle_id):
                return shuttle
        return None

    def get_shuttle_by_position(self, position: str) -> Shuttle:
        """ Returns the shuttle at the given position.
        
        Args:
            position (str): A position on the grid.
        
        Returns:
            Shuttle: The shuttle at the given position or None if no shuttle with the given id exists."""
        for shuttle in self.shuttles:
            if shuttle.get_current_position() == position:
                return shuttle
        return None