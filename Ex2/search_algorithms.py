import heapq
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from Ex1.game_logic import GameState, SokobanGame


def chebyshev_distance(pos1, pos2):
    """Tính khoảng cách Chebyshev giữa hai tọa độ."""
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))


def chebyshev_heuristic(state, game):
    """Ước lượng chi phí bằng Chebyshev từ box tới goal gần nhất."""
    if not state.boxes or not game.red_points:
        return 0

    total_h = 0
    for box in state.boxes:
        min_dist = min(
            chebyshev_distance(box, goal)
            for goal in game.red_points
        )
        total_h += min_dist
    return total_h


def reconstruct_actions(parent, goal_state):
    """Dựng lại danh sách action từ bảng parent."""
    path_actions = []
    current = goal_state

    while current in parent:
        previous_state, action = parent[current]
        path_actions.append(action)
        current = previous_state

    path_actions.reverse()
    return path_actions


def first_action_from_parent(parent, start_state, target_state, default_action="Stay"):
    """Lấy action đầu tiên trên đường từ start tới target."""
    if target_state == start_state:
        return default_action

    actions = reconstruct_actions(parent, target_state)
    return actions[0] if actions else default_action


def _finish_result(path_actions, cost, expanded, visited, max_frontier_size, return_stats):
    """Trả kết quả search, kèm thống kê khi được yêu cầu."""
    if not return_stats:
        return path_actions, cost, expanded

    stats = {
        "visited_states": len(visited),
        "max_frontier_size": max_frontier_size,
    }
    return path_actions, cost, expanded, stats


def a_star_search(game, start_state=None, return_stats=False):
    """A* search, hỗ trợ state bắt đầu tùy chọn và thống kê."""
    src = start_state if start_state is not None else game.initial_state

    pq = [(chebyshev_heuristic(src, game), src)]
    g_score = {src: 0}
    parent = {}
    visited = set()
    expanded = 0
    max_frontier_size = len(pq)

    while pq:
        _, u = heapq.heappop(pq)

        if u in visited:
            continue

        visited.add(u)
        expanded += 1

        if game.is_goal_reached(u):
            path_actions = reconstruct_actions(parent, u)
            return _finish_result(
                path_actions,
                g_score[u],
                expanded,
                visited,
                max_frontier_size,
                return_stats,
            )

        for action, v, weight in game.get_successors(u):
            tentative_g = g_score[u] + weight

            if tentative_g < g_score.get(v, float("inf")):
                g_score[v] = tentative_g
                parent[v] = (u, action)
                f_score = tentative_g + chebyshev_heuristic(v, game)
                heapq.heappush(pq, (f_score, v))
                max_frontier_size = max(max_frontier_size, len(pq))

    return _finish_result(
        None,
        0,
        expanded,
        visited,
        max_frontier_size,
        return_stats,
    )


def ucs_search(game, start_state=None, return_stats=False):
    """Uniform-Cost Search theo chi phí đã đi."""
    src = start_state if start_state is not None else game.initial_state

    pq = [(0, src)]
    g_score = {src: 0}
    parent = {}
    visited = set()
    expanded = 0
    max_frontier_size = len(pq)

    while pq:
        current_g, u = heapq.heappop(pq)

        if u in visited:
            continue

        visited.add(u)
        expanded += 1

        if game.is_goal_reached(u):
            path_actions = reconstruct_actions(parent, u)
            return _finish_result(
                path_actions,
                current_g,
                expanded,
                visited,
                max_frontier_size,
                return_stats,
            )

        for action, v, weight in game.get_successors(u):
            tentative_g = current_g + weight

            if tentative_g < g_score.get(v, float("inf")):
                g_score[v] = tentative_g
                parent[v] = (u, action)
                heapq.heappush(pq, (tentative_g, v))
                max_frontier_size = max(max_frontier_size, len(pq))

    return _finish_result(
        None,
        0,
        expanded,
        visited,
        max_frontier_size,
        return_stats,
    )


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_map = os.path.join(current_dir, "..", "Ex1", "example_map.txt")

    # Có thể chạy: python Ex2/search_algorithms.py path/to/layout.txt
    map_path = sys.argv[1] if len(sys.argv) > 1 else default_map
    game = SokobanGame(map_path)

    print("\n--- CHẠY THUẬT TOÁN A* ---")
    astar_path, astar_cost, astar_nodes = a_star_search(game)
    print(f"Số node duyệt: {astar_nodes}")
    print(f"Đường đi: {astar_path}")
    print(f"Total cost: {astar_cost}")

    print("\n--- CHẠY THUẬT TOÁN UCS ---")
    ucs_path, ucs_cost, ucs_nodes = ucs_search(game)
    print(f"Số node duyệt: {ucs_nodes}")
    print(f"Đường đi: {ucs_path}")
    print(f"Total cost: {ucs_cost}")
