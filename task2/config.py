from enum import Enum
#Chỉ số máu của các vật thể
HP_TANK = 6
HP_BASE = 9
HP_WALL = 3
#Kích thước bản đồ
GRID_ROWS = 20
GRID_COLS = 20
#Sát thương đạn khi va chạm các vật thể, tốc độ đạn
BULLET_DAMAGE = 1 
BULLET_SPEED = 3 #
class Action(Enum):
    MOVE_UP = 1
    MOVE_DOWN = 2
    MOVE_LEFT = 3
    MOVE_RIGHT = 4
    FIRE = 5
    STAY = 6
#Vị trí là (row,col)
class Direction(Enum):
    UP = (-1,0)
    DOWN = (1,0)
    LEFT = (0,-1)
    RIGHT = (0,1)
class Player(Enum):
    MAX = 0
    MIN = 1
#Chuyển hành động ->hướng của hành động
MOVE_TO_DIRECTION = {
    Action.MOVE_UP: Direction.UP,
    Action.MOVE_DOWN: Direction.DOWN,
    Action.MOVE_LEFT: Direction.LEFT,
    Action.MOVE_RIGHT: Direction.RIGHT,
}
class AgentType(Enum):
    MINIMAX = "minimax"
    ALPHABETA = "alphabeta"
    MINIMAX_HEURISTIC = "minimax_heuristic"
    ALPHABETA_HEURISTIC = "alphabeta_heuristic"