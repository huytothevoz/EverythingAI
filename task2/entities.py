from config import BULLET_DAMAGE,HP_BASE,HP_TANK,HP_WALL,Player
#FILE chứa các thực thể được định nghĩa trong trò chơi
#Vì mọi thứ(trừ đạn) đều có trạng thái máu, vị trí nên kế thừa class Entity
class Entity:
    def __init__(self,hp,position):
        self.position:tuple[int,int] = position 
        self.hp:int = hp
    def take_damage(self):
        self.hp -= BULLET_DAMAGE
    def is_alive(self) ->bool:
        return self.hp>0
    def copy(self):
        return Entity(self.hp,self.position)

class Tank(Entity):
    def __init__(self, position, direction, playerID, hp=HP_TANK):
        super().__init__(hp, position)
        self.direction = direction
        self.playerID = Player(playerID)
    def copy(self):
        return Tank(self.position,self.direction,self.playerID,self.hp)
    
class Wall(Entity):
    def __init__(self, position, hp=HP_WALL):
        super().__init__(hp, position)  
    def copy(self):
        return Wall(self.position,self.hp)
    
class Base(Entity):
    def __init__(self, position,playerID, hp=HP_BASE):
        super().__init__(hp, position)
        self.playerID=Player(playerID)
    def copy(self):
        return Base(self.position,self.playerID,self.hp)
    
class Bullet:
    def __init__(self,owner,direction,position):
        self.owner = Player(owner)
        self.direction = direction 
        self.position = position
    def copy(self): 
        return Bullet(self.owner,self.direction,self.position)