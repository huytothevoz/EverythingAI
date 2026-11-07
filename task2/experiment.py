import time
from config import AgentType, Player, Direction,HP_BASE,HP_TANK,HP_WALL
from agent_loader import load_agent
from game_state import GameState
from entities import Tank, Base, Wall
from evaluation import evaluate # Đảm bảo import hàm evaluate để chấm điểm cuối trận
def create_sample_game_state():
    # 1. Khởi tạo Tanks và Bases ở 2 góc đối diện
    tanks = {
        Player.MAX: Tank(playerID=Player.MAX, position=(16, 16), direction=Direction.UP, hp=HP_TANK),
        Player.MIN: Tank(playerID=Player.MIN, position=(3, 3), direction=Direction.DOWN, hp=HP_TANK)
    }
    
    bases = {
        Player.MAX: Base(playerID=Player.MAX, position=(18, 18), hp=HP_BASE), # Góc dưới phải
        Player.MIN: Base(playerID=Player.MIN, position=(1, 1), hp=HP_BASE)    # Góc trên trái
    }
    
    walls = {}
    
    for coord in [(0, 2), (0, 3), (2, 0), (3, 0), (2, 2)]:
        walls[coord] = Wall(position=coord)
        
    # Bảo vệ MAX Base (18,18)
    for coord in [(19, 17), (19, 16), (17, 19), (16, 19), (17, 17)]:
        walls[coord] = Wall(position=coord)

    min_side_walls = [
        (5, 5), (5, 6), (5, 7), (5, 8),
        (8, 5), (9, 5), (10, 5),
        (4, 10), (5, 10), (6, 10), (7, 10), (7, 11), (7, 12)
    ]
    
    max_side_walls = [
        (14, 14), (14, 13), (14, 12), (14, 11),
        (11, 14), (10, 14), (9, 14),
        (15, 9), (14, 9), (13, 9), (12, 9), (12, 8), (12, 7)
    ]
    center_walls = [
        (8, 8), 
        (8, 11), (9, 11), (10, 11), (11, 11),
        (11, 8), (11, 9), (11, 10)
    ]

    all_walls = min_side_walls + max_side_walls + center_walls + [(1, 0), (1, 3), (4, 0), (4, 1), (4, 2), 
            (18, 19), (18, 16), (15, 19), (15, 18), (15, 17),
            (0, 10), (1, 9), (2, 8), (3, 7), (4, 6), (6, 11),
            (19, 9), (18, 10), (17, 11), (16, 12), (15, 13), (13, 8),
            (6, 0), (11, 18), (4, 9), (15, 10)]


    # Gộp tất cả các bức tường vào dictionary
    for coord in all_walls:
        walls[coord] = Wall(position=coord)

    bullets = []
    
    # Trả về GameState hoàn chỉnh
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