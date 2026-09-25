"""
Sokoban Pygame UI - Requirement 5 (Object-Oriented Design & Indie Pop Theme)
- Thiết kế theo mô hình OOP (Lớp Theme, CellRenderer, SokobanUI)
- Hiển thị bản đồ (Tường, Hộp gỗ Crate, Đích Magic Pad, Robot Agent)
- Chạy thuật toán UCS / A* và hiển thị lời giải từng bước
- Controls: Space (Play/Pause), Left/Right (Step prev/next), R (Reset)
"""

import os
import sys
import pygame
import time

# === IMPORT CÁC MODULE TỪ Ex1 VÀ Ex2 ===
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from Ex1.game_logic import SokobanGame, GameState
from Ex2.search_algorithms import a_star_search, ucs_search


class Theme:
    """Quản lý bảng màu và cấu hình giao diện Indie Pop"""
    CELL_SIZE = 64
    PANEL_HEIGHT = 180
    FPS = 60
    ANIMATION_SPEED = 0.35

    # Bảng màu
    BG = (245, 240, 230)
    FLOOR = (232, 225, 210)
    FLOOR_GRID = (218, 210, 192)
    WALL = (120, 140, 160)
    WALL_TOP = (150, 172, 195)
    WALL_SHADOW = (85, 102, 120)

    # Thùng gỗ (Crate)
    CRATE_MAIN = (220, 150, 80)
    CRATE_DARK = (180, 110, 50)
    CRATE_LIGHT = (245, 185, 120)
    CRATE_NAIL = (100, 80, 70)

    # Thùng đã vào đích (Mint Box)
    BOX_DONE = (72, 199, 142)
    BOX_DONE_DARK = (45, 150, 105)
    BOX_DONE_RIBBON = (255, 225, 100)

    # Đích đến
    GOAL_OUTER = (240, 120, 160)
    GOAL_INNER = (255, 180, 205)

    # Robot Agent
    ROBOT_BODY = (235, 240, 245)
    ROBOT_DARK = (170, 185, 200)
    ROBOT_SCREEN = (40, 45, 60)
    ROBOT_EYE = (80, 220, 255)
    ROBOT_ANT = (255, 90, 90)

    # Panel & Buttons
    PANEL_BG = (255, 255, 255)
    PANEL_BORDER = (220, 215, 200)
    TEXT = (45, 55, 72)
    TEXT_DIM = (115, 125, 140)
    BTN_UCS = (92, 148, 252)
    BTN_ASTAR = (168, 85, 247)
    BTN_RESET = (251, 113, 133)
    SUCCESS = (34, 197, 94)
    FAIL = (239, 68, 68)


class CellRenderer:
    """Lớp chuyên trách vẽ từng đối tượng đồ họa trên bản đồ"""

    @staticmethod
    def draw_cell(screen, x, y, cell_type, cell_size):
        rect = pygame.Rect(x, y, cell_size, cell_size)
        cx, cy = x + cell_size // 2, y + cell_size // 2

        # 1. Sàn nhà
        if cell_type in ["floor", "goal", "box", "box_done", "agent", "agent_on_goal"]:
            pygame.draw.rect(screen, Theme.FLOOR, rect)
            pygame.draw.rect(screen, Theme.FLOOR_GRID, rect, 1)

        # 2. Tường 3D Block
        if cell_type == "wall":
            pygame.draw.rect(screen, Theme.WALL_SHADOW, rect, border_radius=6)
            front_rect = pygame.Rect(x, y + 6, cell_size, cell_size - 6)
            pygame.draw.rect(screen, Theme.WALL, front_rect, border_radius=6)
            top_rect = pygame.Rect(x, y, cell_size, cell_size - 10)
            pygame.draw.rect(screen, Theme.WALL_TOP, top_rect, border_radius=6)

        # 3. Đích đến (Magic Goal Pad)
        elif cell_type == "goal":
            pygame.draw.circle(screen, Theme.GOAL_OUTER, (cx, cy), cell_size // 3 + 2)
            pygame.draw.circle(screen, Theme.GOAL_INNER, (cx, cy), cell_size // 3 - 3)
            pygame.draw.circle(screen, Theme.GOAL_OUTER, (cx, cy), cell_size // 8)

        # 4. Hộp gỗ thường (Wood Crate)
        elif cell_type == "box":
            m = 5
            box_r = pygame.Rect(x + m, y + m, cell_size - 2*m, cell_size - 2*m)
            pygame.draw.rect(screen, Theme.CRATE_DARK, box_r, border_radius=8)
            inner_r = pygame.Rect(x + m + 3, y + m + 3, cell_size - 2*m - 6, cell_size - 2*m - 6)
            pygame.draw.rect(screen, Theme.CRATE_MAIN, inner_r, border_radius=6)
            
            # Khung chéo X
            pygame.draw.line(screen, Theme.CRATE_DARK, (box_r.left + 4, box_r.top + 4), (box_r.right - 4, box_r.bottom - 4), 3)
            pygame.draw.line(screen, Theme.CRATE_DARK, (box_r.left + 4, box_r.bottom - 4), (box_r.right - 4, box_r.top + 4), 3)
            pygame.draw.line(screen, Theme.CRATE_LIGHT, (inner_r.left + 2, inner_r.top + 2), (inner_r.right - 2, inner_r.top + 2), 2)
            
            # 4 Đinh sắt
            corners = [(box_r.left + 5, box_r.top + 5), (box_r.right - 5, box_r.top + 5),
                       (box_r.left + 5, box_r.bottom - 5), (box_r.right - 5, box_r.bottom - 5)]
            for c in corners:
                pygame.draw.circle(screen, Theme.CRATE_NAIL, c, 2)

        # 5. Hộp đã vào đích (Mint Box)
        elif cell_type == "box_done":
            m = 5
            box_r = pygame.Rect(x + m, y + m, cell_size - 2*m, cell_size - 2*m)
            pygame.draw.rect(screen, Theme.BOX_DONE_DARK, box_r, border_radius=8)
            inner_r = pygame.Rect(x + m + 3, y + m + 3, cell_size - 2*m - 6, cell_size - 2*m - 6)
            pygame.draw.rect(screen, Theme.BOX_DONE, inner_r, border_radius=6)
            
            # Ruy-băng
            pygame.draw.line(screen, Theme.BOX_DONE_RIBBON, (cx, box_r.top + 2), (cx, box_r.bottom - 2), 5)
            pygame.draw.line(screen, Theme.BOX_DONE_RIBBON, (box_r.left + 2, cy), (box_r.right - 2, cy), 5)
            pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 5)
            pygame.draw.circle(screen, Theme.BOX_DONE_RIBBON, (cx, cy), 3)

        # 6. Robot Agent
        elif cell_type in ["agent", "agent_on_goal"]:
            if cell_type == "agent_on_goal":
                pygame.draw.circle(screen, Theme.GOAL_OUTER, (cx, cy), cell_size // 3 + 4)

            # Ăng-ten
            pygame.draw.line(screen, Theme.ROBOT_DARK, (cx, cy - cell_size // 4), (cx, cy - cell_size // 2 + 2), 3)
            pygame.draw.circle(screen, Theme.ROBOT_ANT, (cx, cy - cell_size // 2 + 2), 4)

            # Thân Robot
            body_radius = cell_size // 3
            pygame.draw.circle(screen, Theme.ROBOT_DARK, (cx, cy + 2), body_radius)
            pygame.draw.circle(screen, Theme.ROBOT_BODY, (cx, cy), body_radius)

            # Màn hình mắt LED
            screen_r = pygame.Rect(cx - 14, cy - 8, 28, 16)
            pygame.draw.rect(screen, Theme.ROBOT_SCREEN, screen_r, border_radius=5)
            pygame.draw.circle(screen, Theme.ROBOT_EYE, (cx - 6, cy - 1), 3)
            pygame.draw.circle(screen, Theme.ROBOT_EYE, (cx + 6, cy - 1), 3)
            pygame.draw.circle(screen, Theme.ROBOT_DARK, (cx - body_radius, cy), 4)
            pygame.draw.circle(screen, Theme.ROBOT_DARK, (cx + body_radius, cy), 4)


class SokobanUI:
    """Lớp chính điều khiển giao diện Pygame và xử lý luồng sự kiện"""

    def __init__(self, map_path):
        self.game = SokobanGame(map_path)
        self.rows, self.cols = self._parse_map_dimensions()

        pygame.init()
        self._init_window_dimensions()
        
        self.screen = pygame.display.set_mode((self.window_w, self.window_h))
        pygame.display.set_caption("Sokoban AI Solver - OOP & Indie Pop Edition")

        self._init_fonts()
        self.clock = pygame.time.Clock()

        # Trạng thái ứng dụng
        self.current_state = self.game.initial_state
        self.solution_actions = []
        self.solution_states = []
        self.current_step = 0
        self.is_playing = False
        self.is_paused = False
        self.last_step_time = 0
        self.algorithm_name = ""
        self.nodes_expanded = 0
        self.solve_status = ""

        # Tọa độ căn giữa bản đồ
        self.offset_x = (self.window_w - self.map_pixel_w) // 2
        self.offset_y = 15

        self._init_ui_elements()

    def _parse_map_dimensions(self):
        all_positions = self.game.walls | self.game.red_points | set(self.game.initial_state.boxes) | {self.game.initial_state.agent_pos}
        max_row = max(pos[0] for pos in all_positions) + 1
        max_col = max(pos[1] for pos in all_positions) + 1
        return max_row, max_col

    def _init_window_dimensions(self):
        info = pygame.display.Info()
        max_w = info.current_w - 100
        max_h = info.current_h - 150

        self.cell_size = Theme.CELL_SIZE
        self.map_pixel_w = self.cols * self.cell_size
        self.map_pixel_h = self.rows * self.cell_size

        while self.map_pixel_w > max_w or (self.map_pixel_h + Theme.PANEL_HEIGHT) > max_h:
            self.cell_size -= 4
            self.map_pixel_w = self.cols * self.cell_size
            self.map_pixel_h = self.rows * self.cell_size
            if self.cell_size < 24:
                break

        min_panel_width = 600
        self.window_w = max(self.map_pixel_w + 60, min_panel_width)
        self.window_h = self.map_pixel_h + Theme.PANEL_HEIGHT + 30

    def _init_fonts(self):
        try:
            self.font_large = pygame.font.SysFont("Segoe UI", 20, bold=True)
            self.font_small = pygame.font.SysFont("Segoe UI", 15, bold=False)
            self.font_btn = pygame.font.SysFont("Segoe UI", 16, bold=True)
        except:
            self.font_large = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 20)
            self.font_btn = pygame.font.Font(None, 20)

    def _init_ui_elements(self):
        btn_w, btn_h = 140, 40
        btn_y = self.map_pixel_h + 30
        btn_gap = 24
        total_btn_w = 3 * btn_w + 2 * btn_gap
        btn_start_x = (self.window_w - total_btn_w) // 2

        self.btn_ucs_rect = pygame.Rect(btn_start_x, btn_y, btn_w, btn_h)
        self.btn_astar_rect = pygame.Rect(btn_start_x + btn_w + btn_gap, btn_y, btn_w, btn_h)
        self.btn_reset_rect = pygame.Rect(btn_start_x + 2 * (btn_w + btn_gap), btn_y, btn_w, btn_h)

        self.panel_rect = pygame.Rect((self.window_w - 580) // 2, btn_y + btn_h + 15, 580, Theme.PANEL_HEIGHT - 25)

    def reset_state(self):
        self.current_state = self.game.initial_state
        self.solution_actions = []
        self.solution_states = []
        self.current_step = 0
        self.is_playing = False
        self.is_paused = False
        self.algorithm_name = ""
        self.nodes_expanded = 0
        self.solve_status = ""

    def run_solver(self, algo_name):
        self.current_state = self.game.initial_state
        self.solution_actions = []
        self.solution_states = []
        self.current_step = 0
        self.is_playing = False
        self.is_paused = False
        self.algorithm_name = algo_name

        self.solve_status = "Đang tính toán lời giải..."
        self.draw_frame()
        pygame.display.flip()

        if algo_name == "UCS":
            result = ucs_search(self.game)
        else:
            result = a_star_search(self.game)

        actions, cost, expanded = result
        self.nodes_expanded = expanded

        if actions is None:
            self.solve_status = "Thất bại - Không tìm được đường đi!"
            return

        self.solution_actions = actions
        self.solution_states = [self.game.initial_state]
        state = self.game.initial_state
        for action in self.solution_actions:
            state = self.game.apply_action(state, action)
            self.solution_states.append(state)

        self.solve_status = f"Thành công! Chi phí: {cost} bước"
        self.is_playing = True
        self.is_paused = False
        self.last_step_time = time.time()

    def go_to_step(self, step):
        if self.solution_states and 0 <= step < len(self.solution_states):
            self.current_step = step
            self.current_state = self.solution_states[step]

    def _draw_button(self, text, rect, color, hover=False):
        shadow_rect = pygame.Rect(rect.x, rect.y + 3, rect.width, rect.height)
        pygame.draw.rect(self.screen, (200, 195, 180), shadow_rect, border_radius=10)

        draw_rect = rect.copy()
        if hover:
            draw_rect.y -= 2

        pygame.draw.rect(self.screen, color, draw_rect, border_radius=10)

        highlight_rect = pygame.Rect(draw_rect.x + 4, draw_rect.y + 2, draw_rect.width - 8, 3)
        pygame.draw.rect(self.screen, (255, 255, 255, 120), highlight_rect, border_radius=2)

        text_surface = self.font_btn.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=draw_rect.center)
        self.screen.blit(text_surface, text_rect)

    def _draw_map(self):
        for i in range(self.rows):
            for j in range(self.cols):
                pos = (i, j)
                x = self.offset_x + j * self.cell_size
                y = self.offset_y + i * self.cell_size

                if pos in self.game.walls:
                    CellRenderer.draw_cell(self.screen, x, y, "wall", self.cell_size)
                elif pos == self.current_state.agent_pos and pos in self.game.red_points:
                    CellRenderer.draw_cell(self.screen, x, y, "agent_on_goal", self.cell_size)
                elif pos == self.current_state.agent_pos:
                    CellRenderer.draw_cell(self.screen, x, y, "agent", self.cell_size)
                elif pos in self.current_state.boxes and pos in self.game.red_points:
                    CellRenderer.draw_cell(self.screen, x, y, "box_done", self.cell_size)
                elif pos in self.current_state.boxes:
                    CellRenderer.draw_cell(self.screen, x, y, "box", self.cell_size)
                elif pos in self.game.red_points:
                    CellRenderer.draw_cell(self.screen, x, y, "goal", self.cell_size)
                else:
                    is_playable = False
                    for di in range(-1, 2):
                        for dj in range(-1, 2):
                            neighbor = (i + di, j + dj)
                            if neighbor in self.game.walls or neighbor in self.game.red_points:
                                is_playable = True
                                break
                        if is_playable:
                            break
                    if is_playable:
                        CellRenderer.draw_cell(self.screen, x, y, "floor", self.cell_size)

    def _draw_panel(self):
        pygame.draw.rect(self.screen, Theme.PANEL_BG, self.panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, Theme.PANEL_BORDER, self.panel_rect, width=2, border_radius=16)

        x_start = self.panel_rect.x + 24
        y_start = self.panel_rect.y + 16

        algo_text = self.algorithm_name if self.algorithm_name else "Chưa chọn"
        algo_surface = self.font_large.render(f"Thuật toán: {algo_text}", True, Theme.TEXT)
        self.screen.blit(algo_surface, (x_start, y_start))

        status = self.solve_status if self.solve_status else "Nhấn nút UCS hoặc A* để bắt đầu"
        status_color = Theme.TEXT_DIM
        if "Thành công" in status:
            status_color = Theme.SUCCESS
        elif "Thất bại" in status:
            status_color = Theme.FAIL

        if self.is_paused:
            status += "  [TẠM DỪNG]"

        status_surface = self.font_small.render(status, True, status_color)
        self.screen.blit(status_surface, (x_start, y_start + 32))

        step_text = f"Bước: {self.current_step} / {len(self.solution_actions)}"
        step_surface = self.font_small.render(step_text, True, Theme.TEXT)
        self.screen.blit(step_surface, (x_start, y_start + 58))

        if self.nodes_expanded:
            nodes_surface = self.font_small.render(f"Số node đã duyệt: {self.nodes_expanded:,}", True, Theme.TEXT_DIM)
            self.screen.blit(nodes_surface, (x_start, y_start + 82))

        # Phím tắt
        help_y = y_start + 112
        help_texts = ["SPACE: Dừng/Tiếp tục", "← →: Tua lùi/tới", "R: Reset"]
        for idx, ht in enumerate(help_texts):
            chip_rect = pygame.Rect(x_start + idx * 190, help_y, 175, 26)
            pygame.draw.rect(self.screen, (240, 236, 225), chip_rect, border_radius=6)
            
            ht_surface = self.font_small.render(ht, True, Theme.TEXT)
            ht_rect = ht_surface.get_rect(center=chip_rect.center)
            self.screen.blit(ht_surface, ht_rect)

    def draw_frame(self):
        self.screen.fill(Theme.BG)
        self._draw_map()

        mouse_pos = pygame.mouse.get_pos()
        self._draw_button("UCS", self.btn_ucs_rect, Theme.BTN_UCS, self.btn_ucs_rect.collidepoint(mouse_pos))
        self._draw_button("A*", self.btn_astar_rect, Theme.BTN_ASTAR, self.btn_astar_rect.collidepoint(mouse_pos))
        self._draw_button("Reset", self.btn_reset_rect, Theme.BTN_RESET, self.btn_reset_rect.collidepoint(mouse_pos))

        self._draw_panel()

    def run(self):
        """Vòng lặp chính của ứng dụng"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_ucs_rect.collidepoint(event.pos):
                        self.run_solver("UCS")
                    elif self.btn_astar_rect.collidepoint(event.pos):
                        self.run_solver("A*")
                    elif self.btn_reset_rect.collidepoint(event.pos):
                        self.reset_state()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.solution_actions:
                        self.is_paused = not self.is_paused
                        if not self.is_paused:
                            self.last_step_time = time.time()
                    elif event.key == pygame.K_LEFT and self.solution_states:
                        self.is_paused = True
                        self.go_to_step(self.current_step - 1)
                    elif event.key == pygame.K_RIGHT and self.solution_states:
                        self.is_paused = True
                        self.go_to_step(self.current_step + 1)
                    elif event.key == pygame.K_r:
                        self.reset_state()

            # Animation cập nhật theo thời gian
            if self.is_playing and not self.is_paused and self.solution_states:
                now = time.time()
                if now - self.last_step_time >= Theme.ANIMATION_SPEED:
                    if self.current_step < len(self.solution_actions):
                        self.current_step += 1
                        self.current_state = self.solution_states[self.current_step]
                        self.last_step_time = now
                    else:
                        self.is_playing = False

            self.draw_frame()
            pygame.display.flip()
            self.clock.tick(Theme.FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    map_file_path = os.path.join(current_dir, "..", "Ex1", "testmap.txt")

    if not os.path.exists(map_file_path):
        print(f"Không tìm thấy file bản đồ: {map_file_path}")
        sys.exit(1)

    app = SokobanUI(map_file_path)
    app.run()