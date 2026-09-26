import os
import heapq
import sys


parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from Ex1.game_logic import SokobanGame, GameState
def chebyshev_heuristic(state,game):
    """Hàm Heuristic Chebyshev:Tổng khoảng cách Chebyshev từ các hộp tới đích gần nhất"""
    total_h = 0
    for box in state.boxes:
        #Tìm đích gần cái hộp này nhất
        min_dist = min(max(abs(box[0] - goal[0]), abs(box[1] - goal[1])) for goal in game.red_points)
        total_h += min_dist
    return total_h
def a_star_search(game):
    src = game.initial_state
    
    pq = [(chebyshev_heuristic(src, game), src)]
    
    g_score = {}     
    g_score[src] = 0
    
    parent = {}
    visited = set()
    
    expanded = 0      
    while pq:
        f_score_u, u = heapq.heappop(pq)
        
        if u in visited:
            continue
            
        visited.add(u)
        expanded += 1
        
        # Nếu đã đẩy hết hộp vào đích
        if game.is_goal_reached(u):
            path_actions = []
            curr = u
            # Truy vết ngược lại để lấy danh sách hành động
            while curr in parent:
                prev_state, action = parent[curr]
                path_actions.append(action)
                curr = prev_state
                
            path_actions.reverse()
            # Trả về: Mảng các hành động, Chi phí (độ dài mảng), và Số node đã mở
            return path_actions, len(path_actions), expanded
        # Thay thế g.AL[u] bằng get_successors
        for action, v, weight in game.get_successors(u):
            tentative_g_score = g_score[u] + weight
            
            # get(v, infinity) nghĩa là nếu v chưa có trong g_score thì coi như g(v) = vô cực
            if tentative_g_score < g_score.get(v, float('inf')):
                g_score[v] = tentative_g_score
                f_score_v = tentative_g_score + chebyshev_heuristic(v, game)
                
                heapq.heappush(pq, (f_score_v, v))
                parent[v] = (u, action) # Lưu kèm hành động để lát nữa truy vết
    return None, 0, expanded # Không tìm thấy đường
def ucs_search(game):
    src = game.initial_state
    
    # 1. Khởi tạo: Hàng đợi ưu tiên chỉ chứa chi phí g(n) = 0 và State ban đầu
    pq = [(0, src)] 
    
    g_score = {}      
    g_score[src] = 0
    
    parent = {}
    visited = set()
    
    expanded = 0      # Đếm số node đã duyệt

    while pq:
        # Bốc ra trạng thái có tổng chi phí đi từ đầu g(n) nhỏ nhất
        current_g, u = heapq.heappop(pq)
        
        if u in visited:
            continue
            
        visited.add(u)
        expanded += 1
        # Nếu đã đẩy hết hộp vào đích
        if game.is_goal_reached(u):
            path_actions = []
            curr = u
            # Truy vết ngược lại
            while curr in parent:
                prev_state, action = parent[curr]
                path_actions.append(action)
                curr = prev_state
                
            path_actions.reverse()
            # Trả về chuỗi hành động, Tổng chi phí, và Số node đã mở
            return path_actions, len(path_actions), expanded

        # Duyệt qua các hướng đi hợp lệ
        for action, v, weight in game.get_successors(u):
            tentative_g_score = g_score[u] + weight
            
            # Nếu tìm được đường ngắn hơn đến v
            if tentative_g_score < g_score.get(v, float('inf')):
                g_score[v] = tentative_g_score
                
                # 2. Khác biệt cốt lõi: Chỉ nhét g(n) vào hàng đợi, không cộng h(n)
                heapq.heappush(pq, (tentative_g_score, v))
                parent[v] = (u, action)

    return None, 0, expanded # Không tìm thấy đường
if __name__ == "__main__":
    # 1. Lấy vị trí thư mục hiện tại đang chứa file search_algorithms.py (tức là thư mục Ex2)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Từ Ex2, nối đường dẫn lùi lại 1 bước (".."), rồi chui vào "Ex1", rồi trỏ tới file txt
    map_path = os.path.join(current_dir, "..", "Ex1", "example_map.txt")
    
    # 3. Nạp đường dẫn tuyệt đối chuẩn xác vào Game
    game = SokobanGame(map_path) 
    
    # Phần in kết quả giữ nguyên
    print("\n--- CHẠY THUẬT TOÁN A* ---")
    astar_path, astar_cost, astar_nodes = a_star_search(game)
    print(f"Số node duyệt: {astar_nodes}")
    print(f"Đường đi: {astar_path}")
    print("--- CHẠY THUẬT TOÁN UCS ---")
    ucs_path, ucs_cost, ucs_nodes = ucs_search(game)
    print(f"Số node duyệt: {ucs_nodes}")
    print(f"Đường đi: {ucs_path}")
    
    