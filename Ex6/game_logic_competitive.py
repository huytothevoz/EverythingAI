from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional, Tuple

# Ex6 mở rộng từ logic Sokoban ở Ex1 nên dùng lại luôn các helper cơ bản.
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from Ex1.game_logic import DIRECTION_VECTORS, Position, add_position, is_corner_deadlock_at


@dataclass(frozen=True)
class CompetitiveGameState:
    """State cho Sokoban 2 agent cạnh tranh.

    So với GameState ở Requirement 1, state mới bổ sung:
    - vị trí của agent thứ hai,
    - owner của từng box,
    - số turn còn lại.
    """

    agent1_pos: Position
    agent2_pos: Position
    boxes: FrozenSet[Position]
    # Lưu owner dạng tuple để state vẫn immutable/hashable giống GameState ở Ex1.
    box_owners: Tuple[Tuple[Position, int], ...]
    steps_left: int

    def get_owner_dict(self) -> Dict[Position, int]:
        """Chuyển tuple owner -> dict để truy vấn/cập nhật dễ hơn."""
        return dict(self.box_owners)

    def __lt__(self, other: "CompetitiveGameState") -> bool:
        """Dùng khi hai state có cùng priority trong heapq."""
        return (self.agent1_pos, self.agent2_pos, self.boxes) < (
            other.agent1_pos,
            other.agent2_pos,
            other.boxes,
        )


class CompetitiveSokobanGame:
    """Mở rộng Sokoban ở Requirement 1 thành bài toán 2 agent cạnh tranh.

    Quy tắc chính:
    - Hai agent cùng chọn action từ *một state ban đầu của turn*.
    - Sau đó engine mới resolve hai action đồng thời.
    - Hai agent không được đứng cùng ô hoặc đi xuyên qua nhau.
    - Box trên goal vẫn có thể bị đối thủ đẩy ra rồi giành lại.
    """

    # Tái sử dụng 4 hướng đi từ Ex1, chỉ thêm Stay cho competitive mode.
    ACTIONS = {**DIRECTION_VECTORS, "Stay": (0, 0)}

    def __init__(self, map_file_path: str, max_steps: int = 50):
        self.walls = set()
        self.red_points = set()
        self.max_steps = max_steps

        agent1_pos = None
        agent2_pos = None
        temp_boxes = set()

        # Format map giữ gần giống Ex1:
        # % = wall, 1/A = agent1, 2 = agent2, B = box, D = goal, C = box-on-goal.
        with open(map_file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                row = list(line.rstrip("\n"))
                for j, element in enumerate(row):
                    pos = (i, j)
                    if element == "%":
                        self.walls.add(pos)
                    elif element in ("A", "1"):
                        agent1_pos = pos
                    elif element == "2":
                        agent2_pos = pos
                    elif element == "B":
                        temp_boxes.add(pos)
                    elif element == "D":
                        self.red_points.add(pos)
                    elif element == "C":
                        temp_boxes.add(pos)
                        self.red_points.add(pos)

        if agent1_pos is None or agent2_pos is None:
            raise ValueError("Bản đồ competitive phải có đủ 2 Agent (A/1 và 2)")

        # Owner = 0 nghĩa là box chưa thuộc về agent nào.
        self.initial_state = CompetitiveGameState(
            agent1_pos=agent1_pos,
            agent2_pos=agent2_pos,
            boxes=frozenset(temp_boxes),
            box_owners=tuple(sorted((box, 0) for box in temp_boxes)),
            steps_left=max_steps,
        )

    def is_corner_deadlock(self, box_pos: Position) -> bool:
        """Dùng lại đúng quy tắc corner deadlock của Requirement 1.

        Engine không bắt buộc cấm mọi deadlock khi chơi; hàm này chủ yếu để
        Requirement 7 có thể prune nước đi xấu trong lúc search.
        """
        return is_corner_deadlock_at(box_pos, self.walls, self.red_points)

    def get_scores(self, state: CompetitiveGameState) -> Dict[str, int]:
        """Tính điểm của hai agent từ box đang nằm trên goal."""
        owners = state.get_owner_dict()
        score1 = score2 = unclaimed = 0

        for box in state.boxes:
            if box not in self.red_points:
                continue

            owner = owners.get(box, 0)
            if owner == 1:
                score1 += 1
            elif owner == 2:
                score2 += 1
            else:
                unclaimed += 1

        return {
            "agent1": score1,
            "agent2": score2,
            "unclaimed": unclaimed,
            "total_on_target": score1 + score2 + unclaimed,
        }

    def get_winner(self, state: CompetitiveGameState) -> Optional[int]:
        """Trả 1 nếu Agent 1 thắng, 2 nếu Agent 2 thắng, 0 nếu hòa."""
        scores = self.get_scores(state)
        if scores["agent1"] > scores["agent2"]:
            return 1
        if scores["agent2"] > scores["agent1"]:
            return 2
        return 0

    def _apply_box_move(
        self,
        boxes: set[Position],
        owners: Dict[Position, int],
        box_from: Position,
        box_to: Position,
        agent_id: int,
    ) -> None:
        """Di chuyển một box và cập nhật owner của box đó."""
        boxes.remove(box_from)
        boxes.add(box_to)

        previous_owner = owners.pop(box_from, 0)

        # Nếu agent vừa đẩy box VÀO goal thì box được tính cho agent đó.
        if box_to in self.red_points:
            owners[box_to] = agent_id
        else:
            # Nếu box bị đẩy ra khỏi goal thì tạm giữ owner cũ.
            # Khi agent khác đẩy nó vào goal, owner sẽ được cập nhật lại.
            owners[box_to] = previous_owner

    def _invalid_intent(self, agent_id: int, action: str, agent_pos: Position) -> Dict[str, object]:
        """Tạo intent đứng im khi action không hợp lệ."""
        return {
            "agent_id": agent_id,
            "action": action,
            "valid": False,
            "end_pos": agent_pos,
            "box_from": None,
            "box_to": None,
            "pushed": False,
        }

    def _build_intent(
        self,
        agent_id: int,
        agent_pos: Position,
        other_agent_pos: Position,
        action: str,
        boxes: set[Position],
    ) -> Dict[str, object]:
        """Phân tích action thành "ý định" trước khi resolve đồng thời.

        Quan trọng: hàm này KHÔNG cập nhật state ngay.
        Cả Agent 1 và Agent 2 đều build intent từ cùng original state.
        """
        if action not in self.ACTIONS:
            action = "Stay"

        delta = self.ACTIONS[action]

        if action == "Stay":
            return {
                "agent_id": agent_id,
                "action": action,
                "valid": True,
                "end_pos": agent_pos,
                "box_from": None,
                "box_to": None,
                "pushed": False,
            }

        next_pos = add_position(agent_pos, delta)

        # Không đi xuyên tường hoặc đi thẳng vào vị trí hiện tại của agent kia.
        if next_pos in self.walls or next_pos == other_agent_pos:
            return self._invalid_intent(agent_id, action, agent_pos)

        # Nếu phía trước là box thì kiểm tra có đẩy được hay không.
        if next_pos in boxes:
            box_to = add_position(next_pos, delta)

            if box_to in self.walls or box_to in boxes or box_to == other_agent_pos:
                return self._invalid_intent(agent_id, action, agent_pos)

            return {
                "agent_id": agent_id,
                "action": action,
                "valid": True,
                "end_pos": next_pos,
                "box_from": next_pos,
                "box_to": box_to,
                "pushed": True,
            }

        # Đi vào ô trống.
        return {
            "agent_id": agent_id,
            "action": action,
            "valid": True,
            "end_pos": next_pos,
            "box_from": None,
            "box_to": None,
            "pushed": False,
        }

    @staticmethod
    def _same_cell_conflict(intent1: Dict[str, object], intent2: Dict[str, object]) -> bool:
        """Hai agent cùng muốn kết thúc ở một ô => cả hai bị hủy."""
        return bool(
            intent1["valid"]
            and intent2["valid"]
            and intent1["end_pos"] == intent2["end_pos"]
        )

    @staticmethod
    def _swap_conflict(
        state: CompetitiveGameState,
        intent1: Dict[str, object],
        intent2: Dict[str, object],
    ) -> bool:
        """Hai agent đổi chỗ cho nhau trong 1 turn => vi phạm 'cannot pass through'."""
        return bool(
            intent1["valid"]
            and intent2["valid"]
            and intent1["end_pos"] == state.agent2_pos
            and intent2["end_pos"] == state.agent1_pos
        )

    @staticmethod
    def _box_conflict(intent1: Dict[str, object], intent2: Dict[str, object]) -> bool:
        """Kiểm tra xung đột liên quan đến box khi hai action xảy ra đồng thời."""
        if not (intent1["valid"] and intent2["valid"]):
            return False

        box_from1, box_to1 = intent1["box_from"], intent1["box_to"]
        box_from2, box_to2 = intent2["box_from"], intent2["box_to"]

        # Cả hai cùng tác động một box.
        if box_from1 is not None and box_from1 == box_from2:
            return True

        # Hai box khác nhau nhưng cùng bị đẩy vào một destination.
        if box_to1 is not None and box_to1 == box_to2:
            return True

        # Agent bên này muốn đứng đúng ô mà box bên kia sẽ chiếm sau turn.
        if box_to1 is not None and intent2["end_pos"] == box_to1:
            return True
        if box_to2 is not None and intent1["end_pos"] == box_to2:
            return True

        return False

    def apply_joint_actions(
        self,
        state: CompetitiveGameState,
        action1: str,
        action2: str,
    ) -> CompetitiveGameState:
        """Thực hiện 2 action đồng thời và trả về CompetitiveGameState mới."""
        if state.steps_left <= 0:
            return state

        original_boxes = set(state.boxes)
        owners = state.get_owner_dict()

        # Cả hai intent được tính từ CHÍNH state trước turn.
        intent1 = self._build_intent(
            1,
            state.agent1_pos,
            state.agent2_pos,
            action1,
            original_boxes,
        )
        intent2 = self._build_intent(
            2,
            state.agent2_pos,
            state.agent1_pos,
            action2,
            original_boxes,
        )

        # Nếu có conflict đồng thời thì hủy cả hai intent.
        has_conflict = (
            self._same_cell_conflict(intent1, intent2)
            or self._swap_conflict(state, intent1, intent2)
            or self._box_conflict(intent1, intent2)
        )

        if has_conflict:
            intent1 = self._invalid_intent(1, str(intent1["action"]), state.agent1_pos)
            intent2 = self._invalid_intent(2, str(intent2["action"]), state.agent2_pos)

        final_boxes = set(original_boxes)
        final_owners = dict(owners)

        # Sau khi resolve conflict xong mới thật sự apply các box move.
        if intent1["valid"] and intent1["box_from"] is not None:
            self._apply_box_move(
                final_boxes,
                final_owners,
                intent1["box_from"],
                intent1["box_to"],
                1,
            )

        if intent2["valid"] and intent2["box_from"] is not None:
            self._apply_box_move(
                final_boxes,
                final_owners,
                intent2["box_from"],
                intent2["box_to"],
                2,
            )

        next_a1 = intent1["end_pos"] if intent1["valid"] else state.agent1_pos
        next_a2 = intent2["end_pos"] if intent2["valid"] else state.agent2_pos

        return CompetitiveGameState(
            agent1_pos=next_a1,
            agent2_pos=next_a2,
            boxes=frozenset(final_boxes),
            box_owners=tuple(sorted(final_owners.items())),
            steps_left=state.steps_left - 1,
        )
