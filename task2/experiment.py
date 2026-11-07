import time
from config import AgentType, Player, Direction
from agent_loader import load_agent
from game_state import GameState
from entities import Tank, Base, Wall
from evaluation import evaluate # Đảm bảo import hàm evaluate để chấm điểm cuối trận

def create_sample_game_state():
    tanks = {
        Player.MAX: Tank(playerID=Player.MAX, position=(6, 11), direction=Direction.UP, hp=100),
        Player.MIN: Tank(playerID=Player.MIN, position=(6, 1), direction=Direction.DOWN, hp=100)
    }
    
    bases = {
        Player.MAX: Base(playerID=Player.MAX, position=(6, 12), hp=100), # Base nhà mình ở phía dưới
        Player.MIN: Base(playerID=Player.MIN, position=(6, 0), hp=100)   # Base địch ở phía trên
    }
    
    # Tạo hệ thống 1 loại tường (Wall) bố trí giống cấu trúc chướng ngại vật trong ảnh
    walls = {}
    
    # 1. Xây tường bảo vệ xung quanh Base MAX (phía dưới) và Base MIN (phía trên)
    for x in range(5, 8):
        walls[(x, 11)] = Wall(position=(x, 11))
    walls[(5, 12)] = Wall(position=(5, 12))
    walls[(7, 12)] = Wall(position=(7, 12))
    
    for x in range(5, 8):
        walls[(x, 1)] = Wall(position=(x, 1))
    walls[(5, 0)] = Wall(position=(5, 0))
    walls[(7, 0)] = Wall(position=(7, 0))

    # 2. Xây các khối tường chướng ngại vật ở giữa bản đồ (tạo hành lang trái/phải/giữa)
    obstacle_coords = [
        # Khối chắn bên trái
        (2, 3), (3, 3), (4, 3),
        (2, 6), (3, 6), (4, 6),
        (2, 9), (3, 9), (4, 9),
        
        # Khối chắn bên phải
        (8, 3), (9, 3), (10, 3),
        (8, 6), (9, 6), (10, 6),
        (8, 9), (9, 9), (10, 9),
        
        # Một số tường rải rác khu vực trung tâm
        (6, 4), (6, 8)
    ]
    
    for coord in obstacle_coords:
        walls[coord] = Wall(position=coord)

    bullets = []
    
    # Trả về GameState hoàn chỉnh với kích thước bàn cờ ví dụ 13x13
    return GameState(
        tanks=tanks, 
        bases=bases, 
        walls=walls, 
        bullets=bullets, 
        current_player=Player.MAX, 
        step_count=0
    )

class BenchmarkExperiment:
    def __init__(self, depth=3, max_steps=50):
        self.depth = depth
        self.max_steps = max_steps
        self.agent_types = [
            AgentType.MINIMAX,
            AgentType.ALPHABETA,
            AgentType.MINIMAX_HEURISTIC,
            AgentType.ALPHABETA_HEURISTIC
        ]

    def run_match_simulation(self, agent_type: AgentType, initial_state: GameState):
        agent = load_agent(agent_type, depth=self.depth)
        current_state = initial_state.copy()
        
        total_time = 0.0
        total_nodes = 0
        total_pruned = 0
        steps_taken = 0
        
        print(f"Đang chạy: {agent.name}...")

        while not current_state.is_terminal() and steps_taken < self.max_steps:
            action = agent.choose_action(current_state)
            
            total_time += agent.execution_time
            total_nodes += agent.nodes_expanded
            total_pruned += agent.pruned_count
            
            if action is not None:
                current_state = current_state.apply_action(action)
            
            steps_taken += 1

        # Xác định kết quả trận đấu
        utility = current_state.get_utility(depth_remaining=0)
        
        if utility > 0:
            result = "MAX WIn"
        elif utility < 0:
            result = "MIN Win"
        else:
            result = "HÒA / HẾT BƯỚC"

        # Tính điểm số từ góc nhìn của MAX và MIN tại trạng thái kết thúc
        final_score_max = evaluate(current_state, perspective=Player.MAX)
        final_score_min = evaluate(current_state, perspective=Player.MIN)

        avg_time = (total_time / steps_taken) * 1000 if steps_taken > 0 else 0
        avg_nodes = total_nodes / steps_taken if steps_taken > 0 else 0
        avg_pruned = total_pruned / steps_taken if steps_taken > 0 else 0

        return {
            "name": agent.name,
            "result": result,
            "steps": steps_taken,
            "score_max": final_score_max,
            "score_min": final_score_min,
            "avg_time_ms": avg_time,
            "avg_nodes": avg_nodes,
            "avg_pruned": avg_pruned
        }

    def run_all_benchmarks(self):
        initial_state = create_sample_game_state()
        results = []

       
        print(f"Thí nghiệm: (Depth={self.depth})")
       

        for agent_type in self.agent_types:
            res = self.run_match_simulation(agent_type, initial_state)
            results.append(res)

        # In bảng tổng hợp mở rộng có thêm cột điểm số của MAX và MIN
        print("\n" + "=" * 10)
        print(f"{'Thuật toán':<22} | {'Kết quả':<14} | {'Bước':<6} | {'Điểm MAX':<10} | {'Điểm MIN':<10} | {'ms/nước':<10} | {'Nodes/bước':<10} | {'Cắt tỉa':<8}")
        print("-" * 10)
        for r in results:
            print(f"{r['name']:<22} | {r['result']:<14} | {r['steps']:<6} | {r['score_max']:<10.1f} | {r['score_min']:<10.1f} | {r['avg_time_ms']:<10.2f} | {r['avg_nodes']:<10.1f} | {r['avg_pruned']:<8.1f}")
        print("=" * 10 + "\n")

if __name__ == "__main__":
    experiment = BenchmarkExperiment(depth=4, max_steps=1000)
    experiment.run_all_benchmarks()