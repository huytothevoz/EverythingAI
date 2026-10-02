from dataclasses import dataclass
from typing import FrozenSet, Tuple

Position = Tuple[int, int]  # Tọa độ (row, column)

# 4 hướng di chuyển dùng chung cho phần competitive (Requirement 6-8).
# Giữ tên Up/Down/Left/Right để không làm vỡ interface của agent ở Ex7.
DIRECTION_VECTORS = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}

# Requirement 1-2 yêu cầu output action là North/East/West/South.
# Vì vậy single-agent dùng đúng tên trong đề, còn vector vẫn giống nhau.
SINGLE_AGENT_ACTIONS = {
    "North": DIRECTION_VECTORS["Up"],
    "East": DIRECTION_VECTORS["Right"],
    "West": DIRECTION_VECTORS["Left"],
    "South": DIRECTION_VECTORS["Down"],
}

# Cho phép apply_action() hiểu cả tên cũ nếu một đoạn code cũ vẫn truyền Up/Down/Left/Right.
ACTION_ALIASES = {
    "Up": "North",
    "Right": "East",
    "Left": "West",
    "Down": "South",
}


def add_position(pos: Position, delta: Position) -> Position:
    """Cộng vector di chuyển vào tọa độ hiện tại."""
    return pos[0] + delta[0], pos[1] + delta[1]


def is_corner_deadlock_at(box_pos: Position, walls: set, red_points: set) -> bool:
    """Kiểm tra box có bị kẹt ở góc tường hay không.

    Helper này được Ex6/Ex7 dùng lại để project không copy-paste cùng
    một quy tắc deadlock ở nhiều Requirement.
    """
    # Nếu góc đó chính là goal thì box đứng ở đây là hợp lệ.
    if box_pos in red_points:
        return False

    r, c = box_pos
    wall_up = (r - 1, c) in walls
    wall_down = (r + 1, c) in walls
    wall_left = (r, c - 1) in walls
    wall_right = (r, c + 1) in walls

    # Box kẹt khi hai tường vuông góc bao quanh nó.
    return (
        (wall_up and wall_left)
        or (wall_up and wall_right)
        or (wall_down and wall_left)
        or (wall_down and wall_right)
    )


@dataclass(frozen=True)
class GameState:
    """Phần động của một state: vị trí agent và tập vị trí các box."""

    agent_pos: Position
    boxes: FrozenSet[Position]

    def __lt__(self, other):
        """Giúp heapq so sánh khi hai node có cùng priority."""
        return self.agent_pos < other.agent_pos


class SokobanGame:
    """Mô hình state-space cho Requirement 1.

    Thành phần tĩnh: walls, red_points.
    Thành phần động : GameState(agent_pos, boxes).
    """

    def __init__(self, map_file_path: str):
        """Đọc layout và tạo initial state từ các ký hiệu %, A, B, D, C."""
        self.walls = set()
        self.red_points = set()
        temp_agent_pos = None
        temp_boxes = set()
        map_data = []

        with open(map_file_path, "r", encoding="utf-8") as f:
            for line in f:
                # Chỉ bỏ newline; khoảng trắng là ô trống hợp lệ trong layout.
                map_data.append(list(line.rstrip("\n")))

        for i, row in enumerate(map_data):
            for j, element in enumerate(row):
                pos = (i, j)
                if element == "%":
                    self.walls.add(pos)
                elif element == "A":
                    temp_agent_pos = pos
                elif element == "B":
                    temp_boxes.add(pos)
                elif element == "D":
                    self.red_points.add(pos)
                elif element == "C":
                    # C = box đang nằm trên designated point.
                    temp_boxes.add(pos)
                    self.red_points.add(pos)

        if temp_agent_pos is None:
            raise ValueError("Bản đồ đang không có nhân vật A")

        self.initial_state = GameState(
            agent_pos=temp_agent_pos,
            boxes=frozenset(temp_boxes),
        )

    def is_corner_deadlock(self, box_pos: Position) -> bool:
        """Gọi helper dùng chung để phát hiện corner deadlock."""
        return is_corner_deadlock_at(box_pos, self.walls, self.red_points)

    def is_goal_reached(self, state: GameState) -> bool:
        """Goal test: toàn bộ box đã nằm đúng trên toàn bộ designated points."""
        return self.red_points == state.boxes

    def get_successors(self, state: GameState):
        """Sinh các successor hợp lệ theo Transition Model của Sokoban.

        Mỗi phần tử trả về có dạng (action, next_state, step_cost).
        Action dùng đúng wording của đề: North/East/West/South.
        """
        successors = []
        agent_pos = state.agent_pos

        for action, delta in SINGLE_AGENT_ACTIONS.items():
            agent_pos_new = add_position(agent_pos, delta)

            # Agent không đi xuyên tường.
            if agent_pos_new in self.walls:
                continue

            # Nếu phía trước là box thì cần kiểm tra push.
            if agent_pos_new in state.boxes:
                box_pos_new = add_position(agent_pos_new, delta)

                # Không thể đẩy box vào wall hoặc box khác.
                if box_pos_new in self.walls or box_pos_new in state.boxes:
                    continue

                # Prune corner deadlock để không search state chắc chắn vô nghiệm.
                if self.is_corner_deadlock(box_pos_new):
                    continue

                new_boxes = set(state.boxes)
                new_boxes.remove(agent_pos_new)
                new_boxes.add(box_pos_new)

                state_new = GameState(
                    agent_pos=agent_pos_new,
                    boxes=frozenset(new_boxes),
                )
            else:
                # Ô trống: chỉ agent thay đổi vị trí, box giữ nguyên.
                state_new = GameState(
                    agent_pos=agent_pos_new,
                    boxes=state.boxes,
                )

            # Đề bài dùng total cost; ở project mỗi primitive action có cost = 1.
            successors.append((action, state_new, 1))

        return successors

    def apply_action(self, state: GameState, action: str) -> GameState:
        """Áp dụng một action hợp lệ; action sai thì state giữ nguyên.

        Hỗ trợ cả North/East/West/South và alias Up/Right/Left/Down để
        các phần code cũ vẫn tương thích sau khi sửa output theo đề.
        """
        normalized_action = ACTION_ALIASES.get(action, action)

        for act, next_state, _ in self.get_successors(state):
            if act == normalized_action:
                return next_state

        return state
