import csv
import os
import sys
from collections import deque

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from Ex1.game_logic import SokobanGame
from Ex2.search_algorithms import chebyshev_heuristic, ucs_search


def reachable_states(game):
    """Liệt kê toàn bộ state reachable theo transition model của Requirement 1."""
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
    """Dùng UCS để tính h*(s): optimal remaining cost từ state tới goal."""
    path, cost, _ = ucs_search(game, start_state=state)
    return None if path is None else cost


def verify_consistency(game, states):
    """Kiểm tra h(s) <= c(s,a,s') + h(s') trên mọi edge reachable."""
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


def sample_states_evenly(states, sample_limit=None):
    """Lấy mẫu trải đều trên toàn danh sách reachable state.

    Map nhỏ được kiểm tra toàn bộ. Với map lớn, sampling giúp thời gian chạy
    thực nghiệm hợp lý nhưng tránh thiên lệch do chỉ lấy 100 state đầu BFS.
    """
    if sample_limit is None or len(states) <= sample_limit:
        return list(states), "all"

    if sample_limit <= 1:
        return [states[0]], f"1/{len(states)} evenly sampled"

    last_index = len(states) - 1
    indices = {
        round(i * last_index / (sample_limit - 1))
        for i in range(sample_limit)
    }
    sampled = [states[i] for i in sorted(indices)]
    return sampled, f"{len(sampled)}/{len(states)} evenly sampled"


def verify_admissibility(game, states, sample_limit=None):
    """Kiểm tra thực nghiệm h(s) <= h*(s) trên toàn bộ hoặc tập state lấy mẫu."""
    sampled_states, sampling_mode = sample_states_evenly(states, sample_limit)

    checked = 0
    unsolvable = 0
    violations = 0
    max_violation = 0

    for state in sampled_states:
        h_value = chebyshev_heuristic(state, game)
        optimal_cost = optimal_remaining_cost(game, state)

        # State không tới được goal thì h*(s) = infinity; bỏ qua khi so finite cost.
        if optimal_cost is None:
            unsolvable += 1
            continue

        checked += 1
        violation = h_value - optimal_cost
        if violation > 0:
            violations += 1
            max_violation = max(max_violation, violation)

    return (
        len(sampled_states),
        checked,
        unsolvable,
        violations,
        max_violation,
        sampling_mode,
    )


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)

    experiments = [
        ("testmap", os.path.join(root_dir, "Ex1", "testmap.txt"), None),
        ("benchmark_1box", os.path.join(root_dir, "Ex3", "maps", "benchmark_1box.txt"), None),
        # Map 2 box có nhiều state: kiểm tra consistency toàn bộ, admissibility lấy 100 state trải đều.
        ("benchmark_2box", os.path.join(root_dir, "Ex3", "maps", "benchmark_2box.txt"), 100),
    ]

    rows = []
    for map_name, map_path, admissible_limit in experiments:
        game = SokobanGame(map_path)
        states = reachable_states(game)

        edges, con_violations, con_max = verify_consistency(game, states)
        (
            sampled,
            solvable,
            unsolvable,
            adm_violations,
            adm_max,
            sampling_mode,
        ) = verify_admissibility(game, states, admissible_limit)

        row = {
            "map": map_name,
            "reachable_states": len(states),
            "consistency_edges_checked": edges,
            "consistency_violations": con_violations,
            "consistency_max_violation": con_max,
            "admissibility_sampling": sampling_mode,
            "admissibility_states_sampled": sampled,
            "admissibility_solvable_checked": solvable,
            "admissibility_unsolvable_skipped": unsolvable,
            "admissibility_violations": adm_violations,
            "admissibility_max_violation": adm_max,
        }
        rows.append(row)

        print(f"\n[{map_name}]")
        print(f"Reachable states: {len(states)}")
        print(
            f"Consistency: checked {edges} edges, violations={con_violations}, "
            f"max_violation={con_max}"
        )
        print(
            f"Admissibility: {sampling_mode}, finite h* checked={solvable}, "
            f"unsolvable skipped={unsolvable}, violations={adm_violations}, "
            f"max_violation={adm_max}"
        )

    output_path = os.path.join(current_dir, "heuristic_verification.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("\nLưu ý: experiment hỗ trợ kiểm chứng, không thay thế lập luận lý thuyết.")
    print("Consistency: một action chỉ làm một box đổi tối đa 1 ô nên Chebyshev của box đó đổi tối đa 1;")
    print("với step cost = 1, điều này phù hợp h(s) <= 1 + h(s').")
    print(f"Đã lưu kết quả: {output_path}")
    return rows


if __name__ == "__main__":
    main()
