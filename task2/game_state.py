from entities import Tank,Wall,Bullet,Base,Entity
from config import Player,Action,GRID_COLS,GRID_ROWS,MOVE_TO_DIRECTION,BULLET_SPEED

def is_inside(row,col):
        return (row>-1 and row <GRID_ROWS) and (col>-1 and col<GRID_COLS)
class GameState:
    walls: dict[tuple[int, int], Wall]
    bullets:list[Bullet]    
    tanks: dict[Player,Tank]
    bases: dict[Player,Base]
    def __init__(self,tanks,bases,walls,bullets=None,current_player=Player.MAX,step_count=0):
        self.tanks = tanks
        self.bases = bases
        self.walls=walls
        self.bullets=bullets if bullets is not None else []
        self.step_count=step_count
        self.current_player=current_player
        self.grid_rows = GRID_ROWS 
        self.grid_cols = GRID_COLS
    def copy(self):
        tanks_copy = {p: t.copy() for p, t in self.tanks.items()}
        bases_copy = {p: b.copy() for p, b in self.bases.items()}
        walls_copy = {pos: w.copy() for pos, w in self.walls.items()}
        bullets_copy = [b.copy() for b in self.bullets]
        return GameState(tanks_copy, bases_copy, walls_copy, bullets_copy, self.current_player, self.step_count)
    
    def get_legal_actions(self,player:Player):
        if not self.tanks[player].is_alive():
            return []
        return [Action.MOVE_DOWN,Action.MOVE_LEFT,Action.MOVE_RIGHT,Action.MOVE_UP,Action.STAY,Action.FIRE]
    
    def get_entity_at(self,row, col):
        if (row,col)in self.walls:
            return self.walls[(row,col)]

        for bullet in self.bullets: 
            if (row,col)== bullet.position:
                return bullet
        for tank in  self.tanks.values():
            if tank.position == (row,col):
                return tank
        for base in  self.bases.values():
                    if base.position == (row,col):
                        return base        
        return None
    def is_blocked(self, row, col):
        if not is_inside(row, col):
            return True
        return self.get_entity_at(row, col) is not None
    def get_current_tank(self):
        return self.tanks[self.current_player]
    def apply_action(self,action):
        new_state= self.copy()
        current_tank=new_state.get_current_tank()

        if action == Action.STAY:
            pass
        if action in [Action.MOVE_UP,Action.MOVE_DOWN,Action.MOVE_LEFT,Action.MOVE_RIGHT]:
            current_tank.direction = MOVE_TO_DIRECTION[action]
            new_row=current_tank.position[0] + MOVE_TO_DIRECTION[action].value[0]
            new_col=current_tank.position[1] + MOVE_TO_DIRECTION[action].value[1]
            if not new_state.is_blocked(new_row,new_col):
                current_tank.position = (new_row,new_col)
        elif action == Action.FIRE:
            new_bullet=Bullet(new_state.current_player,current_tank.direction,current_tank.position)
            new_state.bullets.append(new_bullet)
        if new_state.current_player == Player.MIN:
            new_state._move_bullets()   
            new_state.current_player = Player.MAX
        else:
            new_state.current_player = Player.MIN
        return new_state
    
    def _move_bullets(self):
        for n_square in range(BULLET_SPEED):
            moving_intent = {}
            bullets_to_del = set()

            for bullet in self.bullets:
                new_position = (bullet.position[0] + bullet.direction.value[0],
                                bullet.position[1] + bullet.direction.value[1])
                if not is_inside(new_position[0], new_position[1]):
                    bullets_to_del.add(bullet)   # đạn ra ngoài biên → xoá
                    continue
                if new_position not in moving_intent:
                    moving_intent[new_position] = []
                moving_intent[new_position].append(bullet)

            for pos, bullets_at_pos in moving_intent.items():
                if len(bullets_at_pos) > 1:
                    for bullet in bullets_at_pos:
                        bullets_to_del.add(bullet)
                    continue
                bullet = bullets_at_pos[0]
                if bullet in bullets_to_del:
                    continue                     # đã bị xoá ở bước này rồi
                obj = self.get_entity_at(pos[0], pos[1])
                if obj is not None:
                    if isinstance(obj, Entity):
                        obj.take_damage()
                        if not obj.is_alive():
                            if isinstance(obj, Tank):
                                self.tanks.pop(obj.playerID, None)
                            if isinstance(obj, Wall):
                                self.walls.pop(obj.position, None)
                            if isinstance(obj, Base):
                                self.bases.pop(obj.playerID, None)
                    else:
                        bullets_to_del.add(obj)
                    bullets_to_del.add(bullet)
                else:
                    bullet.position = pos        

            # Lọc sau mỗi bước để không xử lý lại đạn đã chết
            self.bullets = [b for b in self.bullets if b not in bullets_to_del]
    def is_terminal(self):
        # Kiểm tra an toàn xem Tank và Base có tồn tại trong từ điển không trước khi gọi is_alive()
        max_tank_alive = Player.MAX in self.tanks and self.tanks[Player.MAX].is_alive()
        min_tank_alive = Player.MIN in self.tanks and self.tanks[Player.MIN].is_alive()
        
        max_base_alive = Player.MAX in self.bases and self.bases[Player.MAX].is_alive()
        min_base_alive = Player.MIN in self.bases and self.bases[Player.MIN].is_alive()
        
        return not max_tank_alive or not min_tank_alive or not max_base_alive or not min_base_alive

    def get_utility(self, depth_remaining: int):
        max_tank_alive = Player.MAX in self.tanks and self.tanks[Player.MAX].is_alive()
        min_tank_alive = Player.MIN in self.tanks and self.tanks[Player.MIN].is_alive()
        
        max_base_alive = Player.MAX in self.bases and self.bases[Player.MAX].is_alive()
        min_base_alive = Player.MIN in self.bases and self.bases[Player.MIN].is_alive()
        
        max_win = not min_tank_alive or not min_base_alive
        min_win = not max_tank_alive or not max_base_alive
        
        if max_win and min_win:
            return 0.0
        if max_win:
            return 10000.0 + depth_remaining
        if min_win:
            return -10000.0 - depth_remaining
        return 0.0
            
