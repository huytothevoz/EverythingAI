import csv
import os
import sys
from collections import deque

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from Ex1.game_logic import SokobanGame
from Ex2.search_algorithms import chebyshev_heuristic, ucs_search


def reachable_states(game):
    """Liệt kê tất cả state có thể đạt được theo get_successors()."""
    queue = deque([game.initial_state])
    seen = {game.initial_state}
    states = []

    while queue:
        state = queue.popleft()
        states.append(state)
        for _, next_state, _ in game.get_successors(state):
            if next_state not in seen:
                seen.add(next_state)
                queue.append(next_state)
    return states


def optimal_remaining_cost(game, state):
    """Dùng UCS để lấy h*(state): optimal cost còn lại đến goal."""
    original_state = game.initial_state
    game.initial_state = state
    path, cost, _ = ucs_search(game)
    game.initial_state = original_state

    if path is None:
        return None
    return cost


def verify_consistency(game, states):
    checked_edges = 0
    violations = 0
    max_violation = 0

    for state in states:
        h_state = chebyshev_heuristic(state, game)
        for _, next_state, step_cost in game.get_successors(state):
            checked_edges += 1
            h_next = chebyshev_heuristic(next_state, game)
            violation = h_state - (step_cost + h_next)
            if violation > 0:
                violations += 1
                max_violation = max(max_violation, violation)

    return checked_edges, violations, max_violation


def verify_admissibility(game, states, sample_limit=None):
    if sample_limit is not None:
        states = states[:sample_limit]

    checked = 0
    unsolvable = 0
    violations = 0
    max_violation = 0

    for state in states:
        h_value = chebyshev_heuristic(state, game)
        optimal_cost = optimal_remaining_cost(game, state)

        if optimal_cost is None:
            unsolvable += 1
            continue

        checked += 1
        violation = h_value - optimal_cost
        if violation > 0:
            violations += 1
            max_violation = max(max_violation, violation)

    return len(states), checked, unsolvable, violations, max_violation


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)

    experiments = [
        ("testmap", os.path.join(root_dir, "Ex1", "testmap.txt"), None),
        ("benchmark_1box", os.path.join(root_dir, "Ex3", "maps", "benchmark_1box.txt"), None),
        # Map 2 hộp có nhiều state hơn nên lấy 100 state đầu cho kiểm tra admissibility.
        ("benchmark_2box", os.path.join(root_dir, "Ex3", "maps", "benchmark_2box.txt"), 100),
    ]

    rows = []
    for map_name, map_path, admissible_limit in experiments:
        game = SokobanGame(map_path)
        states = reachable_states(game)

        edges, con_violations, con_max = verify_consistency(game, states)
        sampled, solvable, unsolvable, adm_violations, adm_max = verify_admissibility(
            game, states, admissible_limit
        )

        row = {
            "map": map_name,
            "reachable_states": len(states),
            "consistency_edges_checked": edges,
            "consistency_violations": con_violations,
            "admissibility_states_sampled": sampled,
            "admissibility_solvable_checked": solvable,
            "admissibility_unsolvable_skipped": unsolvable,
            "admissibility_violations": adm_violations,
        }
        rows.append(row)

        print(f"\n[{map_name}]")
        print(f"Reachable states: {len(states)}")
        print(f"Consistency: checked {edges} edges, violations = {con_violations}, max = {con_max}")
        print(
            f"Admissibility: sampled {sampled}, finite h* checked {solvable}, "
            f"unsolvable skipped {unsolvable}, violations = {adm_violations}, max = {adm_max}"
        )

    output_path = os.path.join(current_dir, "heuristic_verification.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nĐã lưu kết quả: {output_path}")


if __name__ == "__main__":
    main()
