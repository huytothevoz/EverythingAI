import time
from agents.base_agent import BaseAgent
from config import Player, Action
from game_state import GameState
from evaluation import evaluate 

class SearchAgent(BaseAgent):
    def __init__(self, max_depth=3, use_alpha_beta=True, use_heuristic=True, name="SearchAgent"):
        super().__init__(name)
        self.max_depth = max_depth
        self.use_alpha_beta = use_alpha_beta
        self.use_heuristic = use_heuristic

    def _move_ordering(self, state: GameState, legal_actions: list[Action], maximizing: bool):
        #Sắp xếp nước đi ưu tiên FIRE và các action chủ động lên đầu để cắt tỉa mạnh hơn
        scored = []
        for action in legal_actions:
            next_state = state.apply_action(action)
            # Ưu tiên hành động FIRE
            priority = 1 if action == Action.FIRE else 0
            # Hoặc chấm điểm nhanh bằng heuristic nếu có
            score = evaluate(next_state) if self.use_heuristic else 0
            scored.append((action, priority, score))
        
        #Sắp xếp: Ưu tiên action có priority cao trước, sau đó đến score theo góc nhìn maximizing
        scored.sort(key=lambda x: (x[1], x[2]), reverse=maximizing)
        return [item[0] for item in scored]

    def _search(self, state: GameState, depth: int, alpha: float, beta: float):
        self.nodes_expanded += 1

        #Suy ra maximizing từ state.current_player thay vì truyền tham số thừa
        maximizing = (state.current_player == Player.MAX)

        #Kiểm tra điều kiện terminal
        if state.is_terminal() or depth == 0:
            if state.is_terminal():
                return state.get_utility(depth), None
            # e, g) Nếu đạt độ sâu giới hạn (cutoff) nhưng chưa terminal:
            if self.use_heuristic:
                return evaluate(state), None
            else:
                return 0.0, None

        legal_actions = state.get_legal_actions(state.current_player)
        if not legal_actions:
            return (evaluate(state) if self.use_heuristic else 0.0), None

        #Sắp xếp nước đi tối ưu
        ordered_actions = self._move_ordering(state, legal_actions, maximizing)
        best_action = None

        if maximizing:
            max_val = -float('inf')
            for action in ordered_actions:
                next_state = state.apply_action(action)
                val, _ = self._search(next_state, depth - 1, alpha, beta) # b) Đổi tên biến tránh trùng built-in eval
                
                if val > max_val:
                    max_val = val
                    best_action = action
                
                if self.use_alpha_beta:
                    alpha = max(alpha, val)
                    if beta <= alpha:
                        self.pruned_count += 1  # a) Thống kê số nhánh cắt tỉa
                        break
            return max_val, best_action
        else:
            min_val = float('inf')
            for action in ordered_actions:
                next_state = state.apply_action(action)
                val, _ = self._search(next_state, depth - 1, alpha, beta)
                
                if val < min_val:
                    min_val = val
                    best_action = action
                
                if self.use_alpha_beta:
                    beta = min(beta, val)
                    if beta <= alpha:
                        self.pruned_count += 1  
                        break
            return min_val, best_action

    def choose_action(self, state: GameState):
        # Reset lại thống kê cho lượt đi mới
        self.nodes_expanded = 0
        self.pruned_count = 0
        start_time = time.time()

        _, best_action = self._search(state, self.max_depth, -float('inf'), float('inf'))

        self.execution_time = time.time() - start_time
        return best_action

def create_minimax_agent(depth=3):
    return SearchAgent(max_depth=depth, use_alpha_beta=False, use_heuristic=False, name="Minimax")

def create_alphabeta_agent(depth=3):
    return SearchAgent(max_depth=depth, use_alpha_beta=True, use_heuristic=False, name="AlphaBeta")

def create_heuristic_minimax_agent(depth=3):
    return SearchAgent(max_depth=depth, use_alpha_beta=False, use_heuristic=True, name="Minimax-Heuristic")

def create_heuristic_alphabeta_agent(depth=3):
    return SearchAgent(max_depth=depth, use_alpha_beta=True, use_heuristic=True, name="AlphaBeta-Heuristic")