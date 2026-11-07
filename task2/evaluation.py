from config import Player
from game_state import GameState

def evaluate(state: GameState, perspective: Player = Player.MAX) -> float:
    # 1. Kiểm tra an toàn sự tồn tại của Tank và Base bằng .get() để tránh KeyError
    max_tank = state.tanks.get(Player.MAX)
    min_tank = state.tanks.get(Player.MIN)
    max_base = state.bases.get(Player.MAX)
    min_base = state.bases.get(Player.MIN)
    
    max_tank_alive = max_tank is not None and max_tank.is_alive()
    min_tank_alive = min_tank is not None and min_tank.is_alive()
    max_base_alive = max_base is not None and max_base.is_alive()
    min_base_alive = min_base is not None and min_base.is_alive()
    
    # Điều kiện thắng/thua tuyệt đối
    if not min_base_alive or not min_tank_alive:
        score = 99999.0  # MAX thắng lớn
    elif not max_base_alive or not max_tank_alive:
        score = -99999.0 # MIN thắng / MAX thua
    else:
        # 2. Đánh giá chênh lệch HP của Tank và Base
        max_tank_hp = max_tank.hp if max_tank else 0
        min_tank_hp = min_tank.hp if min_tank else 0
        max_base_hp = max_base.hp if max_base else 0
        min_base_hp = min_base.hp if min_base else 0
        
        tank_hp_score = (max_tank_hp - min_tank_hp) * 100
        base_hp_score = (max_base_hp - min_base_hp) * 200
        
        # 3. Đánh giá khoảng cách từ Tank MAX đến Base địch
        if max_tank and min_base:
            max_tank_pos = max_tank.position
            min_base_pos = min_base.position
            distance_to_enemy_base = abs(max_tank_pos[0] - min_base_pos[0]) + abs(max_tank_pos[1] - min_base_pos[1])
            position_score = -distance_to_enemy_base * 10 
        else:
            position_score = 0
        
        # Tổng điểm thô từ góc nhìn MAX
        score = tank_hp_score + base_hp_score + position_score

    # 4. Điều chỉnh theo góc nhìn (perspective) thực tế của thuật toán
    if perspective == Player.MIN:
        score = -score  # Đảo dấu nếu đang xét từ góc nhìn của MIN
        
    return float(score)