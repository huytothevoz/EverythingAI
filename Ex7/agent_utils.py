from __future__ import annotations

import os
import sys
import time
from typing import List, Tuple

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from Ex2.search_algorithms import chebyshev_distance, first_action_from_parent
from Ex6.game_logic_competitive import CompetitiveGameState, CompetitiveSokobanGame

# 4 action di chuyển giống Ex1/Ex6; Stay chỉ dùng làm fallback / mô phỏng đối thủ đứng yên.
ACTIONS = ("Up", "Down", "Left", "Right")
STAY = "Stay"


def build_deadline(time_limit_ms: int, safety_margin_ms: int = 180) -> float:
    """Tạo deadline cho một lần decision.

    Đề cho tối đa 1000 ms / decision. Ta chừa safety margin đủ rộng để phần return,
    Python overhead và GUI không làm vượt ngưỡng sát 1000 ms.
    """
    usable_ms = max(1, time_limit_ms - safety_margin_ms)
    return time.perf_counter() + usable_ms / 1000.0


def get_agent_position(state: CompetitiveGameState, agent_id: int):
    """Lấy vị trí agent theo ID để tránh lặp if/else ở nhiều nơi."""
    return state.agent1_pos if agent_id == 1 else state.agent2_pos


def get_agent_score(game: CompetitiveSokobanGame, state: CompetitiveGameState, agent_id: int) -> int:
    """Lấy điểm của đúng agent cần xét."""
    scores = game.get_scores(state)
    return scores["agent1"] if agent_id == 1 else scores["agent2"]


def simulate_single_agent_action(
    game: CompetitiveSokobanGame,
    state: CompetitiveGameState,
    agent_id: int,
    action: str,
) -> CompetitiveGameState:
    """Mô phỏng 1 action của đúng một agent trong lúc search.

    Agent còn lại được xem là đứng yên (Stay).
    Quan trọng: vẫn gọi apply_joint_actions() của Ex6, vì vậy Requirement 7
    không viết lại luật tường, box, ownership hay collision.
    """
    if agent_id == 1:
        return game.apply_joint_actions(state, action, STAY)
    return game.apply_joint_actions(state, STAY, action)


def legal_actions(
    game: CompetitiveSokobanGame,
    state: CompetitiveGameState,
    agent_id: int,
    include_stay: bool = True,
) -> List[str]:
    """Lấy các action hợp lệ cho agent đang search.

    Ngoài việc action phải làm thay đổi state, ta còn prune corner-deadlock bằng
    đúng helper mà Ex6 đã kế thừa từ Requirement 1.
    """
    result: List[str] = []
    current_pos = get_agent_position(state, agent_id)

    for action in ACTIONS:
        next_state = simulate_single_agent_action(game, state, agent_id, action)
        next_pos = get_agent_position(next_state, agent_id)

        # Action không làm thay đổi vị trí agent hay box => không có ích cho search.
        if next_pos == current_pos and next_state.boxes == state.boxes:
            continue

        # Nếu action vừa đẩy box vào corner deadlock thì bỏ khỏi successor của agent.
        moved_boxes = set(next_state.boxes) - set(state.boxes)
        if any(game.is_corner_deadlock(box_pos) for box_pos in moved_boxes):
            continue

        result.append(action)

    if include_stay:
        result.append(STAY)

    return result


def competitive_heuristic(
    game: CompetitiveSokobanGame,
    state: CompetitiveGameState,
    agent_id: int,
) -> float:
    """Heuristic cho bài toán cạnh tranh, giá trị càng nhỏ càng tốt.

    Đây KHÔNG phải viết lại heuristic của Task 2.
    Ta tái sử dụng *chebyshev_distance()* của Task 2 rồi bổ sung yếu tố cạnh tranh:
    1. Chênh lệch điểm với đối thủ.
    2. Khoảng cách box chưa hoàn thành -> goal gần nhất.
    3. Khoảng cách agent -> box cần xử lý.
    4. Số box trên goal đang thuộc đối thủ.

    Heuristic này dùng cho GBFS/A* của Requirement 7, còn Task 4 vẫn verify
    heuristic single-agent của Requirement 2.
    """
    scores = game.get_scores(state)
    own_key = "agent1" if agent_id == 1 else "agent2"
    opp_key = "agent2" if agent_id == 1 else "agent1"
    own_score = scores[own_key]
    opp_score = scores[opp_key]

    # Score là mục tiêu quan trọng nhất nên đặt trọng số lớn.
    score_term = 30.0 * (opp_score - own_score)

    unfinished_boxes = [box for box in state.boxes if box not in game.red_points]

    if unfinished_boxes:
        # Tổng khoảng cách mỗi box chưa hoàn thành tới goal gần nhất.
        box_goal_term = 0.0
        for box in unfinished_boxes:
            box_goal_term += min(
                chebyshev_distance(box, goal)
                for goal in game.red_points
            )

        # Khuyến khích agent đi gần một box chưa hoàn thành.
        agent_pos = get_agent_position(state, agent_id)
        agent_box_term = min(
            chebyshev_distance(agent_pos, box)
            for box in unfinished_boxes
        )
    else:
        box_goal_term = 0.0
        agent_box_term = 0.0

    # Box của đối thủ đang nằm trên goal vẫn có thể bị phá rồi giành lại.
    owners = state.get_owner_dict()
    opponent_owned_goals = 0
    for box in state.boxes:
        if box in game.red_points:
            owner = owners.get(box, 0)
            if owner not in (0, agent_id):
                opponent_owned_goals += 1

    return (
        score_term
        + box_goal_term
        + 0.35 * agent_box_term
        + 4.0 * opponent_owned_goals
    )


# Re-export helper này để agent1.py / agent2.py vẫn import từ agent_utils cho dễ đọc.
# Thực chất implementation nằm ở Ex2 để toàn project dùng chung logic truy vết.
def get_first_action(parent, start, target) -> str:
    """Lấy action đầu tiên của kế hoạch; nếu không có thì trả Stay."""
    return first_action_from_parent(parent, start, target, default_action=STAY)
