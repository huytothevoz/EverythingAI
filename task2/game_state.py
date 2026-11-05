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
        tanks_copy={Player.MAX:self.tanks[Player.MAX].copy(),Player.MIN:self.tanks[Player.MIN].copy()}
        bases_copy={Player.MAX:self.bases[Player.MAX].copy(),Player.MIN:self.bases[Player.MIN].copy()}
        walls_copy={pos:wall.copy() for pos, wall in self.walls.items()}
        bullets_copy=[b.copy() for b in self.bullets]
        return GameState(tanks_copy,bases_copy,walls_copy,bullets_copy,self.current_player, self.step_count)
    
    def get_legal_actions(self,player:Player):
        if not self.tanks[player].is_alive():
            return []
        return [Action.STAY,Action.FIRE,Action.MOVE_DOWN,Action.MOVE_LEFT,Action.MOVE_RIGHT,Action.MOVE_UP]
    
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
    def is_blocked(self,row,col):
        if self.get_entity_at(row,col) is None:
            return False
        return True
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
        #Đạn bay 3 ô per 1 cycle
        #Nếu có vật thể trên đường đi thì hit vật thể đó trước và đạn biến mất
        for n_square in range(BULLET_SPEED):
            bullets_to_del=[]
            for bullet in self.bullets:
                new_position=(bullet.position[0] + bullet.direction.value[0],bullet.position[1] + bullet.direction.value[1])
                if not is_inside(new_position[0],new_position[1]):
                    bullets_to_del.append(bullet)
                    continue
                if self.get_entity_at(new_position[0],new_position[1]) is not None:
                    obj=self.get_entity_at(new_position[0],new_position[1])
                    #Nếu vật thể là Thực thể (không phải đạn)
                    if isinstance(obj,Entity):
                        obj.take_damage()
                        if not obj.is_alive():
                            if isinstance(obj,Tank):
                              self.tanks.pop(obj.playerID)
                            if isinstance(obj,Wall):
                              self.walls.pop(obj.position)
                            if isinstance(obj,Base):
                              self.bases.pop(obj.playerID)
                   #Sử lý va chạm đạn
                    else:
                        bullets_to_del.append(obj)
                    bullets_to_del.append(bullet)
                        
                else:
                    bullet.position=new_position
            self.bullets = [b for b in self.bullets if b not in bullets_to_del]
    
            
