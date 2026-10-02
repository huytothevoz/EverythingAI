from __future__ import annotations

import os
import sys
import time
from typing import List, Tuple

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from Ex1.game_logic import DIRECTION_VECTORS
from Ex2.search_algorithms import chebyshev_distance, first_action_from_parent
from Ex6.game_logic_competitive import CompetitiveGameState, CompetitiveSokobanGame

# Dùng cùng tên action với single-agent.
ACTIONS = tuple(DIRECTION_VECTORS.keys())
STAY = "Stay"


def build_deadline(time_limit_ms: int, safety_margin_ms: int = 180) -> float:
    """Tạo deadline và chừa một khoảng an toàn trước giới hạn thời gian."""
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
    """Mô phỏng một agent đi, agent còn lại đứng yên."""
    if agent_id == 1:
        return game.apply_joint_actions(state, action, STAY)
    return game.apply_joint_actions(state, STAY, action)


def legal_actions(
    game: CompetitiveSokobanGame,
    state: CompetitiveGameState,
    agent_id: int,
    include_stay: bool = True,
) -> List[str]:
    """Lấy các action hợp lệ và bỏ nước đi gây corner deadlock."""
    result: List[str] = []
    current_pos = get_agent_position(state, agent_id)

    for action in ACTIONS:
        next_state = simulate_single_agent_action(game, state, agent_id, action)
        next_pos = get_agent_position(next_state, agent_id)

        # Bỏ action không làm thay đổi state.
        if next_pos == current_pos and next_state.boxes == state.boxes:
            continue

        # Bỏ nước đi làm box kẹt ở góc.
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
    """Heuristic cạnh tranh: ưu tiên điểm số rồi xét khoảng cách box và agent."""
    scores = game.get_scores(state)
    own_key = "agent1" if agent_id == 1 else "agent2"
    opp_key = "agent2" if agent_id == 1 else "agent1"
    own_score = scores[own_key]
    opp_score = scores[opp_key]

    # Điểm số được ưu tiên cao nhất.
    score_term = 30.0 * (opp_score - own_score)

    unfinished_boxes = [box for box in state.boxes if box not in game.red_points]

    if unfinished_boxes:
        # Khoảng cách box chưa hoàn thành tới goal gần nhất.
        box_goal_term = 0.0
        for box in unfinished_boxes:
            box_goal_term += min(
                chebyshev_distance(box, goal)
                for goal in game.red_points
            )

        # Ưu tiên agent tiếp cận box chưa hoàn thành.
        agent_pos = get_agent_position(state, agent_id)
        agent_box_term = min(
            chebyshev_distance(agent_pos, box)
            for box in unfinished_boxes
        )
    else:
        box_goal_term = 0.0
        agent_box_term = 0.0

    # Tính thêm các goal đang thuộc đối thủ.
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


# Wrapper dùng chung cho hai agent.
def get_first_action(parent, start, target) -> str:
    """Lấy action đầu tiên của kế hoạch; nếu không có thì trả Stay."""
    return first_action_from_parent(parent, start, target, default_action=STAY)
