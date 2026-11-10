from collections import deque
from config import Player, GRID_ROWS, GRID_COLS, BULLET_SPEED
from game_state import GameState

def bfs_distance(start, goal, walls):
    """Tính khoảng cách ngắn nhất, cho phép đi xuyên tường nhưng bị phạt nặng"""
    if start == goal: return 0
    # Hàng đợi lưu (tọa độ, chi phí)
    q = deque([(start, 0)])
    visited = {start: 0}
    
    while q:
        (r, c), cost = q.popleft()
        
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            
            if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                # Nếu đi vào tường, chi phí tăng thêm 10 (tượng trưng cho việc phải bắn 10 phát)
                move_cost = 10 if (nr, nc) in walls else 1
                new_cost = cost + move_cost
                
                if (nr, nc) == goal:
                    return new_cost
                
                if (nr, nc) not in visited or new_cost < visited[(nr, nc)]:
                    visited[(nr, nc)] = new_cost
                    q.append(((nr, nc), new_cost))
                    
    return 99

def evaluate(state: GameState, perspective: Player = Player.MAX) -> float:
    max_tank = state.tanks.get(Player.MAX)
    min_tank = state.tanks.get(Player.MIN)
    max_base = state.bases.get(Player.MAX)
    min_base = state.bases.get(Player.MIN)
    
    max_tank_alive = max_tank is not None and max_tank.is_alive()
    min_tank_alive = min_tank is not None and min_tank.is_alive()
    max_base_alive = max_base is not None and max_base.is_alive()
    min_base_alive = min_base is not None and min_base.is_alive()
    
    if not min_base_alive or not min_tank_alive:
        score = 99999.0 
    elif not max_base_alive or not max_tank_alive:
        score = -99999.0
    else:
        max_tank_hp = max_tank.hp if max_tank else 0
        min_tank_hp = min_tank.hp if min_tank else 0
        max_base_hp = max_base.hp if max_base else 0
        min_base_hp = min_base.hp if min_base else 0
        
        tank_hp_score = (max_tank_hp - min_tank_hp) * 100
        base_hp_score = (max_base_hp - min_base_hp) * 200
        
        position_score = 0
        if max_tank and min_base:
            d_max = bfs_distance(max_tank.position, min_base.position, state.walls)
            position_score -= d_max * 15
        if min_tank and max_base:
            d_min = bfs_distance(min_tank.position, max_base.position, state.walls)
            position_score += d_min * 15
        
        # Đánh giá mối đe dọa từ đạn đang bay
        bullet_score = 0
        for bullet in state.bullets:
            sign = 1 if bullet.owner == Player.MAX else -1
            dr, dc = bullet.direction.value
            r, c = bullet.position
            for step in range(1, BULLET_SPEED + 1):
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS) or (nr, nc) in state.walls:
                    break
                hit = False
                for pid, tank in state.tanks.items():
                    if tank.position == (nr, nc) and pid != bullet.owner:
                        bullet_score += sign * 50
                        hit = True
                        break
                if hit: break
                for pid, base in state.bases.items():
                    if base.position == (nr, nc) and pid != bullet.owner:
                        bullet_score += sign * 100
                        hit = True
                        break
                if hit: break
                
        score = tank_hp_score + base_hp_score + position_score + bullet_score

    if perspective == Player.MIN:
        score = -score  
        
    return float(score)