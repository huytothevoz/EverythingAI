from dataclasses import dataclass
from typing import FrozenSet, Tuple

Position = Tuple[int, int]  # (row, column)

# Một quy ước hướng đi dùng chung cho toàn project.
DIRECTION_VECTORS = {
    "North": (-1, 0),
    "East": (0, 1),
    "West": (0, -1),
    "South": (1, 0),
}


def add_position(pos: Position, delta: Position) -> Position:
    """Cộng vector di chuyển vào một tọa độ."""
    return pos[0] + delta[0], pos[1] + delta[1]


def is_corner_deadlock_at(box_pos: Position, walls: set, red_points: set) -> bool:
    """Kiểm tra box có bị kẹt ở góc tường hay không."""
    if box_pos in red_points:
        return False

    r, c = box_pos
    wall_north = (r - 1, c) in walls
    wall_south = (r + 1, c) in walls
    wall_west = (r, c - 1) in walls
    wall_east = (r, c + 1) in walls

    return (
        (wall_north and wall_west)
        or (wall_north and wall_east)
        or (wall_south and wall_west)
        or (wall_south and wall_east)
    )


@dataclass(frozen=True)
class GameState:
    """State gồm vị trí agent và vị trí các box."""

    agent_pos: Position
    boxes: FrozenSet[Position]

    def __lt__(self, other):
        """Hỗ trợ heapq khi hai state có cùng priority."""
        return self.agent_pos < other.agent_pos


class SokobanGame:
    """Mô hình state-space của Sokoban single-agent."""

    def __init__(self, map_file_path: str):
        self.walls = set()
        self.red_points = set()
        temp_agent_pos = None
        temp_boxes = set()

        with open(map_file_path, "r", encoding="utf-8") as f:
            map_data = [list(line.rstrip("\n")) for line in f]

        # Đọc các thành phần ban đầu từ layout.
        for row, line in enumerate(map_data):
            for col, element in enumerate(line):
                pos = (row, col)

                if element == "%":
                    self.walls.add(pos)
                elif element == "A":
                    temp_agent_pos = pos
                elif element == "B":
                    temp_boxes.add(pos)
                elif element == "D":
                    self.red_points.add(pos)
                elif element == "C":
                    # C là box đã nằm trên goal.
                    temp_boxes.add(pos)
                    self.red_points.add(pos)

        if temp_agent_pos is None:
            raise ValueError("Bản đồ đang không có nhân vật A")

        self.initial_state = GameState(
            agent_pos=temp_agent_pos,
            boxes=frozenset(temp_boxes),
        )

    def is_corner_deadlock(self, box_pos: Position) -> bool:
        return is_corner_deadlock_at(box_pos, self.walls, self.red_points)

    def is_goal_reached(self, state: GameState) -> bool:
        """Hoàn thành khi tất cả box nằm đúng trên các goal."""
        return self.red_points == state.boxes

    def get_successors(self, state: GameState):
        """Sinh các state hợp lệ sau một bước di chuyển."""
        successors = []

        for action, delta in DIRECTION_VECTORS.items():
            agent_pos_new = add_position(state.agent_pos, delta)

            # Agent không đi xuyên tường.
            if agent_pos_new in self.walls:
                continue

            if agent_pos_new in state.boxes:
                box_pos_new = add_position(agent_pos_new, delta)

                # Chỉ đẩy khi ô phía sau box còn trống.
                if box_pos_new in self.walls or box_pos_new in state.boxes:
                    continue

                # Bỏ state có box kẹt ở góc không phải goal.
                if self.is_corner_deadlock(box_pos_new):
                    continue

                new_boxes = set(state.boxes)
                new_boxes.remove(agent_pos_new)
                new_boxes.add(box_pos_new)
                state_new = GameState(agent_pos_new, frozenset(new_boxes))
            else:
                state_new = GameState(agent_pos_new, state.boxes)

            # Mỗi move hoặc push có cost bằng 1.
            successors.append((action, state_new, 1))

        return successors

    def apply_action(self, state: GameState, action: str) -> GameState:
        """Áp dụng action hợp lệ; action sai thì giữ nguyên state."""
        for valid_action, next_state, _ in self.get_successors(state):
            if valid_action == action:
                return next_state

        return state
