from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

DEFAULT_SINGLE_MAP = os.path.join(ROOT, "Ex1", "testmap.txt")
DEFAULT_COMP_MAP = os.path.join(ROOT, "Ex6", "competitive_map.txt")


def ask_int(prompt: str, default: int) -> int:
    """Đọc số nguyên dương; input rỗng/sai thì dùng default."""
    value = input(f"{prompt} [{default}]: ").strip()
    if not value:
        return default

    try:
        value = int(value)
        return value if value > 0 else default
    except ValueError:
        return default


def ask_map_path(prompt: str, default_path: str) -> str:
    """Cho user nhập path layout như đề yêu cầu.

    - Enter: dùng default map.
    - Path tương đối: tính từ project root.
    - Path tuyệt đối: dùng trực tiếp.
    """
    while True:
        raw = input(f"{prompt}\nEnter để dùng mặc định [{default_path}]: ").strip()
        if not raw:
            return default_path

        # VS Code/Windows đôi khi user paste path có dấu nháy.
        raw = raw.strip('"').strip("'")
        candidate = raw if os.path.isabs(raw) else os.path.join(ROOT, raw)
        candidate = os.path.abspath(candidate)

        if os.path.isfile(candidate):
            return candidate

        print(f"Không tìm thấy layout file: {candidate}")


def pause():
    input("\nNhấn Enter để quay lại menu...")


def run_requirement1():
    from Ex1.game_logic import SokobanGame

    map_path = ask_map_path("Nhập path layout cho Requirement 1", DEFAULT_SINGLE_MAP)
    game = SokobanGame(map_path)
    state = game.initial_state
    successors = game.get_successors(state)

    print("\nREQUIREMENT 1 - STATE SPACE FORMULATION")
    print(f"Map: {map_path}")
    print(f"Initial agent position: {state.agent_pos}")
    print(f"Initial boxes: {sorted(state.boxes)}")
    print(f"Goal positions: {sorted(game.red_points)}")
    print(f"Wall count: {len(game.walls)}")
    print(f"Goal test ban đầu: {game.is_goal_reached(state)}")
    print("Các action hợp lệ từ initial state (đúng wording đề):")

    for action, next_state, cost in successors:
        print(
            f"  - {action:<5} -> agent={next_state.agent_pos}, "
            f"boxes={sorted(next_state.boxes)}, cost={cost}"
        )


def run_requirement2():
    """Chạy UCS hoặc A* của Ex2 trên layout do user chọn."""
    from Ex1.game_logic import SokobanGame
    from Ex2.search_algorithms import a_star_search, ucs_search

    map_path = ask_map_path("Nhập path layout cho Requirement 2", DEFAULT_SINGLE_MAP)
    game = SokobanGame(map_path)
    algo = input("Chọn thuật toán (ucs / astar) [astar]: ").strip().lower() or "astar"
    search_fn = ucs_search if algo == "ucs" else a_star_search
    name = "UCS" if algo == "ucs" else "A*"

    actions, cost, expanded = search_fn(game)

    print(f"\nREQUIREMENT 2 - {name}")
    print(f"Map: {map_path}")
    print(f"Solution actions: {actions}")  # North/East/West/South theo đề.
    print(f"Total cost: {cost}")
    print(f"Expanded nodes: {expanded}")


def run_requirement3():
    """Ex3 gọi lại đúng UCS/A* ở Ex2 để benchmark time và space."""
    from Ex3.experiments import main as experiments_main

    print("\nREQUIREMENT 3 - BENCHMARK UCS VS A*")
    experiments_main()


def run_requirement4():
    """Ex4 kiểm tra admissibility/consistency của heuristic đang dùng trong Ex2."""
    from Ex4.verify_heuristic import main as verify_main

    print("\nREQUIREMENT 4 - VERIFY HEURISTIC")
    verify_main()


def run_requirement5():
    try:
        from Ex5.sokoban_ui import main as run_ui
    except ModuleNotFoundError as exc:
        if exc.name == "pygame":
            print("\nChưa cài pygame. Hãy chạy: python -m pip install -r requirements.txt")
            return
        raise

    map_path = ask_map_path("Nhập path layout cho Requirement 5", DEFAULT_SINGLE_MAP)
    run_ui(map_path)


def run_requirement6():
    from Ex6.game_logic_competitive import CompetitiveSokobanGame

    max_steps = ask_int("Nhập số bước n", 10)
    game = CompetitiveSokobanGame(DEFAULT_COMP_MAP, max_steps=max_steps)
    state = game.initial_state

    print("\nREQUIREMENT 6 - COMPETITIVE MODEL")
    print(f"Map: {DEFAULT_COMP_MAP}")
    print(f"n = {max_steps}")
    print(f"Initial agent1: {state.agent1_pos} | agent2: {state.agent2_pos}")
    print(f"Initial boxes: {sorted(state.boxes)}")
    print(f"Goal positions: {sorted(game.red_points)}")
    print("Nhập 2 action để mô phỏng 1 turn (Up/Down/Left/Right/Stay).")

    while state.steps_left > 0:
        print(f"\nSteps left: {state.steps_left}")
        print(f"Current score: {game.get_scores(state)}")

        action1 = input("Action agent1 [Stay]: ").strip() or "Stay"
        action2 = input("Action agent2 [Stay]: ").strip() or "Stay"
        state = game.apply_joint_actions(state, action1, action2)

        print(
            f"After turn -> a1={state.agent1_pos}, "
            f"a2={state.agent2_pos}, boxes={sorted(state.boxes)}"
        )
        print(f"Scores: {game.get_scores(state)}")

        if input("Tiếp tục? (y/n) [y]: ").strip().lower() == "n":
            break


def run_requirement7():
    """Chạy hai agent của Ex7 trên competitive engine Ex6."""
    from Ex7.run_competitive import run_match

    print("\nREQUIREMENT 7 - COMPETITIVE AGENTS")
    run_match(
        DEFAULT_COMP_MAP,
        ask_int("Nhập số bước n", 30),
        verbose_board=False,
    )


def run_requirement8():
    """Task 8 ghép UI chung Ex5 + engine Ex6 + agents Ex7."""
    try:
        from Ex8.competitive_ui import main as run_ui
    except ModuleNotFoundError as exc:
        if exc.name == "pygame":
            print("\nChưa cài pygame. Hãy chạy: python -m pip install -r requirements.txt")
            return
        raise

    run_ui(DEFAULT_COMP_MAP, ask_int("Nhập số bước n", 30))


def run_visual_menu():
    try:
        from menu_ui import main as run_menu_ui
    except ModuleNotFoundError as exc:
        if exc.name == "pygame":
            print("\nChưa cài pygame. Hãy chạy: python -m pip install -r requirements.txt")
            return
        raise

    run_menu_ui()


MENU = {
    "1": run_requirement1,
    "2": run_requirement2,
    "3": run_requirement3,
    "4": run_requirement4,
    "5": run_requirement5,
    "6": run_requirement6,
    "7": run_requirement7,
    "8": run_requirement8,
    "9": run_visual_menu,
}


def main():
    while True:
        print("\n" + "=" * 60)
        print("         OFFICE SOKOBAN - AI MIDTERM PROJECT")
        print("=" * 60)
        print("1. Requirement 1 - State-space formulation")
        print("2. Requirement 2 - Run UCS / A*")
        print("3. Requirement 3 - Benchmark UCS vs A*")
        print("4. Requirement 4 - Verify heuristic")
        print("5. Requirement 5 - Open single-agent GUI")
        print("6. Requirement 6 - Competitive model demo")
        print("7. Requirement 7 - Run competitive agents")
        print("8. Requirement 8 - Open competitive GUI")
        print("9. Visual Game Menu - Choose 1 Agent / 2 Agents")
        print("0. Exit")

        choice = input("Chọn chức năng: ").strip()

        if choice == "0":
            break

        handler = MENU.get(choice)
        if handler is None:
            print("Lựa chọn không hợp lệ.")
            continue

        try:
            handler()
        except KeyboardInterrupt:
            print("\nĐã hủy thao tác hiện tại.")
        except Exception as exc:
            print(f"\nCó lỗi xảy ra: {exc}")

        if choice not in {"5", "8", "9"}:
            pause()


if __name__ == "__main__":
    main()
