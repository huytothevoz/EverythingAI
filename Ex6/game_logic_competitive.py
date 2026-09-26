from dataclasses import dataclass
from typing import Tuple, FrozenSet, Dict, Optional

Position = Tuple[int, int]

@dataclass(frozen=True)
class CompetitiveGameState:
    agent1_pos: Position
    agent2_pos: Position
    boxes: FrozenSet[Position]
    #box_owners: Mapping từ vị trí thùng -> ID của Agent sở hữu (1 hoặc 2)
    box_owners: Tuple[Tuple[Position, int], ...]
    steps_left: int  # Số bước n còn lại

    def get_owner_dict(self) -> Dict[Position, int]:
        """Chuyển đổi tuple sang dict để dễ truy vấn"""
        return dict(self.box_owners)

    def __lt__(self, other):
        return (self.agent1_pos, self.agent2_pos) < (other.agent1_pos, other.agent2_pos)


class CompetitiveSokobanGame:
    walls: set
    red_points: set
    initial_state: CompetitiveGameState
    max_steps: int

    def __init__(self, map_file_path: str, max_steps: int = 50):
        self.walls = set()
        self.red_points = set()
        self.max_steps = max_steps
        
        agent1_pos = None
        agent2_pos = None
        temp_boxes = set()

        with open(map_file_path, "r") as f:
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

        if not agent1_pos or not agent2_pos:
            raise ValueError("Bản đồ phải có đủ 2 Agent (A/1 và 2)!")
        initial_owners = []
        for box in temp_boxes:
            initial_owners.append((box, 0)) #0: Chưa thuộc về ai

        self.initial_state = CompetitiveGameState(
            agent1_pos=agent1_pos,
            agent2_pos=agent2_pos,
            boxes=frozenset(temp_boxes),
            box_owners=tuple(initial_owners),
            steps_left=self.max_steps
        )
    #Hàm tính điểm riêng
    def get_scores(self, state: CompetitiveGameState):
        """
        Tính điểm riêng cho từng Agent dựa trên số thùng đan nằm trên red point
        và người sở hữu thùng đó là ai.
        """
        owners_dict = state.get_owner_dict()
        score_agent1 = 0
        score_agent2 = 0
        unclaimed_on_target = 0

        for box in state.boxes:
            if box in self.red_points:
                owner = owners_dict.get(box, 0)
                if owner == 1:
                    score_agent1 += 1
                elif owner == 2:
                    score_agent2 += 1
                else:
                    #Thùng nằm sẵn trên đích từ ban đầu chưa ai đẩy
                    unclaimed_on_target += 1 
        return {
            "agent1": score_agent1,
            "agent2": score_agent2,
            "unclaimed": unclaimed_on_target,
            "total_on_target": score_agent1 + score_agent2 + unclaimed_on_target
        }

    def get_winner(self, state: CompetitiveGameState) -> Optional[int]:
        """Xác định Agent chiến thắng khi hết số bước """
        scores = self.get_scores(state)
        if scores["agent1"] > scores["agent2"]:
            return 1
        elif scores["agent2"] > scores["agent1"]:
            return 2
        else:
            return 0  

    
    #Di chuyển và cập nhật người sỡ hữu thùng
    def _try_move_agent(self, agent_id: int, agent_pos: Position, other_agent_pos: Position, 
                        action: str, current_boxes: set, current_owners: Dict[Position, int]):
        """
        Di chuyển Agent và cập nhật vị trí thùng + người sở hữu thùng.
        """
        dirs = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
        if action not in dirs:
            return agent_pos, current_boxes, current_owners, False

        di, dj = dirs[action]
        new_pos = (agent_pos[0] + di, agent_pos[1] + dj)

        #Tránh đâm tường hoặc đâm vào Agent kia
        if new_pos in self.walls or new_pos == other_agent_pos:
            return agent_pos, current_boxes, current_owners, False

        #Trường hợp đẩy thùng
        if new_pos in current_boxes:
            box_new_pos = (new_pos[0] + di, new_pos[1] + dj)
            #Kiểm tra vật cản phía sau thùng[cite: 1]
            if (box_new_pos in self.walls or 
                box_new_pos in current_boxes or 
                box_new_pos == other_agent_pos):
                return agent_pos, current_boxes, current_owners, False
            #Cập nhật danh sách thùng
            updated_boxes = set(current_boxes)
            updated_boxes.remove(new_pos)
            updated_boxes.add(box_new_pos)
            #Cập nhật thông tin sở hữu thùng
            updated_owners = dict(current_owners)
            previous_owner = updated_owners.pop(new_pos, 0)
            #Nếu thùng mới được đẩy VÀO điểm đích
            if box_new_pos in self.red_points:
                updated_owners[box_new_pos] = agent_id
            #Nếu thùng bị đẩy RA KHỎI điểm đích
            else:
                updated_owners[box_new_pos] = previous_owner
            return new_pos, updated_boxes, updated_owners, True
        # Di chuyển vào ô trống
        return new_pos, current_boxes, current_owners, True

    def apply_joint_actions(self, state: CompetitiveGameState, action1: str, action2: str) -> CompetitiveGameState:
        """
        Thực hiện hành động đồng thời cho cả 2 Agent.
        """
        if state.steps_left <= 0:
            return state

        boxes = set(state.boxes)
        owners = state.get_owner_dict()

        #Thử tính nước đi riêng cho từng Agent
        next_a1, boxes_a1, owners_a1, valid1 = self._try_move_agent(
            1, state.agent1_pos, state.agent2_pos, action1, boxes, owners
        )
        next_a2, boxes_a2, owners_a2, valid2 = self._try_move_agent(
            2, state.agent2_pos, state.agent1_pos, action2, boxes, owners
        )

        #Xử lý va chạm đồng thời khi cả 2 cùng muốn vào 1 ô
        if valid1 and valid2 and next_a1 == next_a2:
            #hai Agent đụng nhau
            next_a1, next_a2 = state.agent1_pos, state.agent2_pos
            final_boxes = state.boxes
            final_owners = state.box_owners
        else:
            final_boxes = set(state.boxes)
            final_owners = dict(owners)

            #Nếu Agent 1 di chuyển hợp lệ
            if valid1:
                final_boxes = boxes_a1
                final_owners = owners_a1
            else:
                next_a1 = state.agent1_pos

            #Nếu Agent 2 di chuyển hợp lệ
            if valid2:
                #Trường hợp đặc biệt: Cả 2 cùng hợp lệ và đẩy 2 thùng khác nhau
                if valid1:
                    #Gộp kết quả đẩy thùng của Agent 2 vào Agent 1
                    final_boxes = boxes_a1.intersection(boxes_a2).union(
                        boxes_a1 - state.boxes, boxes_a2 - state.boxes
                    )
                    final_owners.update(owners_a2)
                else:
                    final_boxes = boxes_a2
                    final_owners = owners_a2
            else:
                next_a2 = state.agent2_pos

            #Chuyển đổi dict về tuple để lưu vào frozen state
            final_owners_tuple = tuple(final_owners.items())

        return CompetitiveGameState(
            agent1_pos=next_a1,
            agent2_pos=next_a2,
            boxes=frozenset(final_boxes),
            box_owners=tuple(final_owners_tuple if 'final_owners_tuple' in locals() else state.box_owners),
            steps_left=state.steps_left - 1
        )