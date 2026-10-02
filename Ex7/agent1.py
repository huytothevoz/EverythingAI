# Agent 1: GBFS

from __future__ import annotations

import heapq
import itertools
import os
import sys
import time
from typing import Dict, Tuple

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from Ex6.game_logic_competitive import CompetitiveGameState, CompetitiveSokobanGame
from Ex7.agent_utils import (
    STAY,
    build_deadline,
    competitive_heuristic,
    get_agent_score,
    get_first_action,
    legal_actions,
    simulate_single_agent_action,
)

AGENT_ID = 1
MAX_SEARCH_DEPTH = 12
SAFETY_MARGIN_MS = 180


def choose_action(
    game: CompetitiveSokobanGame,
    state: CompetitiveGameState,
    time_limit_ms: int = 1000,
) -> str:
    """Chọn 1 action bằng time-bounded GBFS.

    GBFS chỉ ưu tiên h(n), nên node nào có competitive_heuristic nhỏ hơn sẽ
    được mở trước. Agent chỉ thực hiện action đầu tiên rồi turn sau re-plan.
    """
    if state.steps_left <= 0:
        return STAY

    deadline = build_deadline(time_limit_ms, SAFETY_MARGIN_MS)
    start_score = get_agent_score(game, state, AGENT_ID)

    counter = itertools.count()
    start_h = competitive_heuristic(game, state, AGENT_ID)
    pq = [(start_h, next(counter), 0, state)]

    parent: Dict[CompetitiveGameState, Tuple[CompetitiveGameState, str]] = {}
    best_depth = {state: 0}
    visited = set()

    best_state = state
    best_h = start_h

    while pq and time.perf_counter() < deadline:
        h_value, _, depth, current = heapq.heappop(pq)

        if current in visited:
            continue
        visited.add(current)

        if h_value < best_h:
            best_h = h_value
            best_state = current

        # Nếu search tìm được state giúp Agent 1 tăng điểm thì dùng kế hoạch đó.
        if get_agent_score(game, current, AGENT_ID) > start_score:
            return get_first_action(parent, state, current)

        if depth >= MAX_SEARCH_DEPTH or current.steps_left <= 0:
            continue

        for action in legal_actions(game, current, AGENT_ID, include_stay=False):
            # Kiểm tra deadline ngay trong vòng sinh successor để không vượt 1000 ms.
            if time.perf_counter() >= deadline:
                break
            child = simulate_single_agent_action(game, current, AGENT_ID, action)
            child_depth = depth + 1

            if child == current:
                continue

            # Với GBFS, giữ depth tốt nhất từng thấy cho cùng một state.
            if child_depth >= best_depth.get(child, 10**9):
                continue

            best_depth[child] = child_depth
            parent[child] = (current, action)
            child_h = competitive_heuristic(game, child, AGENT_ID)
            heapq.heappush(pq, (child_h, next(counter), child_depth, child))

    # Hết time/depth budget: dùng action đầu của state tốt nhất đã tìm được.
    action = get_first_action(parent, state, best_state)
    if action != STAY:
        return action

    # Nếu search chưa tạo được plan thì lấy một legal action làm fallback.
    actions = legal_actions(game, state, AGENT_ID, include_stay=True)
    return actions[0] if actions else STAY
