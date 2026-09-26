
from dataclasses import dataclass
from typing import Tuple, FrozenSet

Position = Tuple[int,int] #Tọa độ
#Class lưu trạng thái hiện tại của game
@dataclass(frozen=True) # đối tượng không thể bị thay đổi sao khi tạo
class GameState:
    agent_pos:Position 
    boxes: FrozenSet[Position]
    def __lt__(self, other):
        """Hàm để so sánh 2 vị trí khi chúng có cùng cost"""
        return self.agent_pos < other.agent_pos
#Bản đồ trò chơi
class SokobanGame:
    wall:set
    red_points:set
    initial_state:GameState

    def __init__(self,map_file_path:str):
        """Đọc map từ file -> phân loại % A B D C lưu tọa độ tương ứng"""
        self.walls=set() #vị trí của các bức tường
        self.red_points=set()  #vị trí các điểm đỏ(điểm đẩy hộp dô)
        temp_agent_pos = None
        temp_boxes = set()
        map=[]
        with open(map_file_path,"r") as f: 
            for line in f:
                row = list(line.rstrip("\n")) #Chỉ xóa kí tự xuống dòng không xóa kí tự khoảng trắng ở đầu
                map.append(row)
            #Duyệt từng phần tử trong ma trận
            for i,row in enumerate(map):
                for j,element in enumerate(row):
                    if element=="%":
                        self.walls.add((i,j))
                    elif element=="A":
                        temp_agent_pos=(i,j)
                    elif element=="B":
                        temp_boxes.add((i,j))
                    elif element=="D":
                        self.red_points.add((i,j))
                    elif element=="C":
                        temp_boxes.add((i,j))
                        self.red_points.add((i,j))
                    else:
                        continue
        if temp_agent_pos is None:
            raise ValueError("Bản đồ đang không có nhân vật")
        self.initial_state = GameState(
                agent_pos=temp_agent_pos, 
                boxes=frozenset(temp_boxes)
            )
    #Kiểm tra deadlock(hộp bị đẩy vào góc vuông)
    def is_corner_deadlock(self, box_pos) -> bool:
        """Kiểm tra xem cái hộp có bị kẹt vào góc tường không"""
        #Nếu góc đó chính là red_point đến thì không sao
        if box_pos in self.red_points:
            return False
            
        r, c = box_pos
        
        #Tường ở các hướng
        wall_up = (r - 1, c) in self.walls
        wall_down = (r + 1, c) in self.walls
        wall_left = (r, c - 1) in self.walls
        wall_right = (r, c + 1) in self.walls
        
        #Bị kẹt nếu có 2 bức tường vây quanh tạo thành góc vuông
        if (wall_up and wall_left) or (wall_up and wall_right) or (wall_down and wall_left) or (wall_down and wall_right):
            return True
            
        return False
    #Goal test        
    def is_goal_reached(self,state:GameState):
        """Nếu toàn bộ box đã có cùng tọa độ với điểm đỏ thì trả về True"""
        return self.red_points==state.boxes 
    def get_successors(self,state:GameState):
        """Trả về các hướng đi hợp lệ và trạng thái sau khi thực hiện các hướng đi đó(successors)"""
        actions={"Up":(-1,0),"Down":(1,0),"Left":(0,-1),"Right":(0,1)} #Cách di chuyển
        successors = []
        #Lấy những action hợp lệ
        agent_i, agent_j=state.agent_pos
        
        for action, (change_i,change_j) in actions.items():
            #Tọa độ mới của agent nếu đi theo hướng đang duyệt trong loop
            agent_i_new=agent_i+change_i
            agent_j_new=agent_j+change_j
            agent_pos_new=(agent_i_new,agent_j_new)

            #Nếu hướng đi trùng vị trí với walls sẽ không đi được
            if agent_pos_new in self.walls:
                continue
            #Trường hợp đi vào vị trí của box(đẩy hộp)
            if agent_pos_new in state.boxes:
                #Tọa độ hộp sau khi đẩys
                box_new_i=agent_i_new+change_i
                box_new_j=agent_j_new+change_j
                box_pos_new=(box_new_i,box_new_j)
                #Nếu hướng đi sẽ đẩy hộp vào vị trí walls hoặc hộp khác cũng sẽ không đi được
                if box_pos_new in self.walls or box_pos_new in state.boxes:
                    continue
                #Nếu hướng đi vào deadlock sẽ cũng không được
                if self.is_corner_deadlock(box_pos_new):
                    continue
                #Đẩy hộp thành công
                new_boxes=set(state.boxes)        
                new_boxes.remove(agent_pos_new) #Xóa hộp ở vị trí cũ
                new_boxes.add(box_pos_new)      #Thêm hộp vào vị trí mới

                #Tạo gameState mới
                state_new=GameState(agent_pos=agent_pos_new,boxes=frozenset(new_boxes))
            #Trường hợp phía trước là ô trống
            else:
                state_new=GameState(agent_pos=agent_pos_new,boxes=frozenset(state.boxes))
                
            successors.append((action, state_new, 1))
        
        return successors
    def apply_action(self, state: GameState, action: str):
        """Nhận vào State hiện tại và một lệnh hành động từ đó hành động"""
        for act, next_state, cost in self.get_successors(state):
            if act == action: #Nếu hướng đi nằm trong successor thì thực hiện hướng đi và trả về trạng thái mới
                return next_state  
        return state  #Nếu hướng đi không nawmgf trong successor(không hợp) lệ thì đứng im(giữ nguyên trạng thái)     
        