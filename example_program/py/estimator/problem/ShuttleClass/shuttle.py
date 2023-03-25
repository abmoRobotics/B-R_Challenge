class Shuttle:
    def __init__(self, shuttle_id, current_mix='', current_move_pos=-1, movements=None, current_pos=None):
        self.shuttle_id = shuttle_id
        self.current_mix = current_mix
        self.current_move_pos = current_move_pos
        self.movements = movements
        self.current_position = (0, 0)


    def set_movements(self, movements):
        self.movements = movements
        self.current_move_pos = -1

    def set_current_pos(self, current_pos):
        self.current_pos = current_pos

    def get_current_pos(self):
        return self.current_pos

    def get_next_move(self):
        if self.current_move_pos + 1 < len(self.movements):
            self.current_move_pos += 1
            return self.movements[self.current_move_pos]
        else:
            return None

    def reset_movement(self):
        self.current_move_pos = -1
    
    def update_position(self, new_position):
        self.current_position = new_position

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
            return 'b

