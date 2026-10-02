# Agent 2 dùng A*.

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

AGENT_ID = 2
MAX_SEARCH_DEPTH = 12
SAFETY_MARGIN_MS = 180


def choose_action(
    game: CompetitiveSokobanGame,
    state: CompetitiveGameState,
    time_limit_ms: int = 1000,
) -> str:
    """Chọn một action bằng A* trong giới hạn thời gian."""
    if state.steps_left <= 0:
        return STAY

    deadline = build_deadline(time_limit_ms, SAFETY_MARGIN_MS)
    start_score = get_agent_score(game, state, AGENT_ID)

    counter = itertools.count()
    start_h = competitive_heuristic(game, state, AGENT_ID)
    pq = [(start_h, next(counter), 0, state)]

    parent: Dict[CompetitiveGameState, Tuple[CompetitiveGameState, str]] = {}
    g_score = {state: 0}
    visited = set()

    best_state = state
    best_h = start_h

    while pq and time.perf_counter() < deadline:
        _, _, depth, current = heapq.heappop(pq)

        if current in visited:
            continue
        visited.add(current)

        h_current = competitive_heuristic(game, current, AGENT_ID)
        if h_current < best_h:
            best_h = h_current
            best_state = current

        if get_agent_score(game, current, AGENT_ID) > start_score:
            return get_first_action(parent, state, current)

        if depth >= MAX_SEARCH_DEPTH or current.steps_left <= 0:
            continue

        current_g = g_score[current]

        for action in legal_actions(game, current, AGENT_ID, include_stay=False):
            # Dừng sớm nếu gần hết thời gian.
            if time.perf_counter() >= deadline:
                break
            child = simulate_single_agent_action(game, current, AGENT_ID, action)

            if child == current:
                continue

            # Mỗi action có cost 1 như single-agent.
            tentative_g = current_g + 1

            if tentative_g >= g_score.get(child, 10**9):
                continue

            g_score[child] = tentative_g
            parent[child] = (current, action)

            child_h = competitive_heuristic(game, child, AGENT_ID)
            f_score = tentative_g + child_h
            heapq.heappush(pq, (f_score, next(counter), depth + 1, child))

    # Hết thời gian thì dùng state tốt nhất đã tìm được.
    action = get_first_action(parent, state, best_state)
    if action != STAY:
        return action

    actions = legal_actions(game, state, AGENT_ID, include_stay=True)
    return actions[0] if actions else STAY
