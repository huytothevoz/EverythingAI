# Requirement 7 - chạy hai agent cạnh tranh bằng terminal.

from __future__ import annotations

import argparse
import os
import sys
import time

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from Ex6.game_logic_competitive import CompetitiveSokobanGame
from Ex7.agent1 import choose_action as agent1_choose_action
from Ex7.agent2 import choose_action as agent2_choose_action


def render_ascii(game: CompetitiveSokobanGame, state):
    points = (
        game.walls
        | game.red_points
        | set(state.boxes)
        | {state.agent1_pos, state.agent2_pos}
    )
    rows = max(r for r, _ in points) + 1
    cols = max(c for _, c in points) + 1
    owners = state.get_owner_dict()

    lines = []
    for r in range(rows):
        row = []
        for c in range(cols):
            pos = (r, c)

            if pos in game.walls:
                row.append("%")
            elif pos == state.agent1_pos:
                row.append("1")
            elif pos == state.agent2_pos:
                row.append("2")
            elif pos in state.boxes:
                owner = owners.get(pos, 0)
                row.append("R" if owner == 1 else "G" if owner == 2 else "B")
            elif pos in game.red_points:
                row.append("D")
            else:
                row.append(" ")

        lines.append("".join(row))

    return "\n".join(lines)


def run_match(
    map_path: str,
    steps: int = 30,
    time_limit_ms: int = 1000,
    verbose_board: bool = False,
):
    game = CompetitiveSokobanGame(map_path, max_steps=steps)
    state = game.initial_state

    print("\nREQUIREMENT 7: COMPETITIVE AGENTS")
    print("Agent 1: GBFS | Agent 2: A* | time limit = 1000 ms / decision")
    print(f"Map: {map_path}")
    print(f"Max turns: {steps}\n")

    if verbose_board:
        print(render_ascii(game, state))
        print()

    turn = 0
    while state.steps_left > 0:
        turn += 1

        # Hai agent đều được truyền chính state hiện tại trước turn.
        start = time.perf_counter()
        action1 = agent1_choose_action(game, state, time_limit_ms)
        t1_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        action2 = agent2_choose_action(game, state, time_limit_ms)
        t2_ms = (time.perf_counter() - start) * 1000

        # Chỉ sau khi cả hai đã chọn xong mới apply simultaneous action ở Ex6.
        state = game.apply_joint_actions(state, action1, action2)
        scores = game.get_scores(state)

        print(
            f"Turn {turn:02d} | "
            f"A1={action1:5} ({t1_ms:7.2f} ms) | "
            f"A2={action2:5} ({t2_ms:7.2f} ms) | "
            f"Score {scores['agent1']}-{scores['agent2']}"
        )

        if verbose_board:
            print(render_ascii(game, state))
            print()

    winner = game.get_winner(state)
    final_scores = game.get_scores(state)

    print("\n-- FINAL RESULT --")
    print(
        f"Final score: Agent 1 {final_scores['agent1']} - "
        f"{final_scores['agent2']} Agent 2"
    )

    if winner == 0:
        print("Winner: DRAW")
    else:
        print(f"Winner: Agent {winner}")

    return state


def default_map_path() -> str:
    """Competitive map thuộc Requirement 6 nên lấy từ Ex6."""
    return os.path.join(PARENT_DIR, "Ex6", "competitive_map.txt")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", dest="map_path", default=default_map_path())
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--show-board", action="store_true")
    args = parser.parse_args()

    run_match(
        args.map_path,
        max(1, args.steps),
        verbose_board=args.show_board,
    )


if __name__ == "__main__":
    main()
