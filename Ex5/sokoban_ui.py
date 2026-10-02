"""
Requirement 5 - Pygame GUI cho Sokoban.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional, Tuple

import pygame

# Cho phép chạy trực tiếp Ex5/sokoban_ui.py mà vẫn import được các Task trước.
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from Ex1.game_logic import SokobanGame
from Ex2.search_algorithms import a_star_search, ucs_search
from Ex5.ui_components import ResponsiveSokobanUIBase, Theme


class SokobanUI(ResponsiveSokobanUIBase):
    """Giao diện chính của Requirement 5."""

    def __init__(self, map_path: str):
        self.map_path = map_path
        self.game = SokobanGame(map_path)
        rows, cols = self._get_map_dimensions()

        # Base class lo cửa sổ, assets, resize, header, button, chip...
        super().__init__(
            rows=rows,
            cols=cols,
            window_title="Office Sokoban - Task 5",
            header_subtitle="Task 5 - Single Agent Visual Solver (UCS / A*)",
        )

        # State dùng để phát lại lời giải.
        self.current_state = self.game.initial_state
        self.solution_actions = []
        self.solution_states = [self.game.initial_state]
        self.current_step = 0
        self.is_playing = False
        self.is_paused = False
        self.last_step_time = time.time()
        self.algorithm_name = ""
        self.nodes_expanded = 0
        self.solve_status = "Chọn thuật toán để giải map"

    # PHẦN 1 - RESPONSIVE SETTINGS RIÊNG CỦA TASK 5
    def _get_map_dimensions(self) -> Tuple[int, int]:
        positions = (
            self.game.walls
            | self.game.red_points
            | set(self.game.initial_state.boxes)
            | {self.game.initial_state.agent_pos}
        )
        return max(r for r, _ in positions) + 1, max(c for _, c in positions) + 1

    def _get_panel_layout_settings(self) -> Tuple[int, int]:
        """Task 5 có 4 chip thông tin; hẹp thì tự chuyển thành 2x2."""
        self.chip_cols = 4 if self.window_w >= 700 else 2
        self.chip_rows = 1 if self.chip_cols == 4 else 2

        status_h = max(18, self.font_body.get_height())
        chip_block_h = self.chip_rows * self.chip_h + (self.chip_rows - 1) * self.gap

        panel_h = (
            self.gap
            + status_h
            + self.gap
            + chip_block_h
            + self.gap
        )

        # Khi window quá thấp thì ẩn help bar để ưu tiên board + control chính.
        help_h = max(24, int(32 * self.ui_scale)) if self.window_h >= 520 else 0
        return panel_h, help_h

    # PHẦN 2 - SOLVER / STATE PLAYBACK
    def reset_state(self) -> None:
        """Đưa game và animation về state ban đầu."""
        self.current_state = self.game.initial_state
        self.solution_actions = []
        self.solution_states = [self.game.initial_state]
        self.current_step = 0
        self.is_playing = False
        self.is_paused = False
        self.last_step_time = time.time()
        self.algorithm_name = ""
        self.nodes_expanded = 0
        self.solve_status = "Đã reset. Chọn UCS hoặc A*."

    def run_solver(self, algorithm: str) -> None:
        """Gọi trực tiếp UCS/A* ở Requirement 2 rồi dựng chuỗi state để animation."""
        self.reset_state()
        self.algorithm_name = algorithm
        self.solve_status = f"Đang chạy {algorithm}..."

        # Vẽ 1 frame trước khi search để người dùng thấy trạng thái đang chạy.
        self.draw_frame()
        pygame.display.flip()

        if algorithm == "UCS":
            actions, cost, expanded = ucs_search(self.game)
        else:
            actions, cost, expanded = a_star_search(self.game)

        self.nodes_expanded = expanded

        if actions is None:
            self.solve_status = "Không tìm thấy lời giải."
            return

        # Ex2 trả về action; Ex5 dùng apply_action của Ex1 để dựng các state trung gian.
        self.solution_actions = actions
        self.solution_states = [self.game.initial_state]

        state = self.game.initial_state
        for action in actions:
            state = self.game.apply_action(state, action)
            self.solution_states.append(state)

        self.solve_status = f"Hoàn tất {algorithm}: cost = {cost} bước."
        self.is_playing = True
        self.is_paused = False
        self.last_step_time = time.time()

    def go_to_step(self, step: int) -> None:
        """Nhảy tới một state trong solution để hỗ trợ Left/Right."""
        if 0 <= step < len(self.solution_states):
            self.current_step = step
            self.current_state = self.solution_states[step]

    # PHẦN 3 - RENDER RIÊNG CỦA SINGLE-AGENT
    def _draw_map(self) -> None:
        """Vẽ board bằng asset chung ở ui_components.py."""
        radius = max(8, int(22 * self.ui_scale))
        pygame.draw.rect(self.screen, Theme.CARD, self.board_card, border_radius=radius)
        pygame.draw.rect(
            self.screen,
            Theme.CARD_BORDER,
            self.board_card,
            width=2,
            border_radius=radius,
        )

        floor = self.assets.get_scaled("floor", (self.cell_size, self.cell_size))
        wall = self.assets.get_scaled("wall", (self.cell_size, self.cell_size))
        water_dispenser = self.assets.get_scaled("water_dispenser", (self.cell_size, self.cell_size))
        agent = self.assets.get_scaled("agent1", (self.cell_size, self.cell_size))

        for r in range(self.rows):
            for c in range(self.cols):
                pos = (r, c)
                x = self.board_x + c * self.cell_size
                y = self.board_y + r * self.cell_size

                if pos in self.game.walls:
                    self.screen.blit(wall, (x, y))
                    continue

                # Ô không phải wall đều dùng cùng floor asset.
                self.screen.blit(floor, (x, y))

                if pos in self.game.red_points:
                    self._draw_goal_marker(x, y)

                if pos in self.current_state.boxes:
                    if pos in self.game.red_points:
                        # Box đã được đưa vào designated point
                        completed_dispenser = self.assets.get_tinted_water_dispenser(
                            self.cell_size,
                            Theme.SUCCESS,
                        )
                        self.screen.blit(completed_dispenser, (x, y))
                    else:
                        # Box chưa vào designated point
                        self.screen.blit(water_dispenser, (x, y))

                if pos == self.current_state.agent_pos:
                    self.screen.blit(agent, (x, y))

    def _draw_info_panel(self) -> None:
        """Hiển thị thuật toán, số action, expanded nodes và map size."""
        radius = max(7, int(18 * self.ui_scale))
        pygame.draw.rect(self.screen, Theme.CARD, self.panel_rect, border_radius=radius)
        pygame.draw.rect(
            self.screen,
            Theme.CARD_BORDER,
            self.panel_rect,
            width=2,
            border_radius=radius,
        )

        status_color = Theme.TEXT_DIM
        if "Không" in self.solve_status:
            status_color = Theme.FAIL
        elif "Hoàn tất" in self.solve_status:
            status_color = Theme.SUCCESS

        status = self.solve_status
        if self.is_paused and self.solution_actions:
            status += " [PAUSE]"

        status_surface = self.font_body.render(status, True, status_color)
        self.screen.blit(
            status_surface,
            (self.panel_rect.x + self.gap, self.panel_rect.y + self.gap),
        )

        chips = [
            ("Thuật toán", self.algorithm_name or "Chưa chọn"),
            ("Action", f"{self.current_step}/{len(self.solution_actions)}"),
            ("Expanded", f"{self.nodes_expanded}" if self.nodes_expanded else "-"),
            ("Map", f"{self.rows}x{self.cols}"),
        ]

        chip_area_x = self.panel_rect.x + self.gap
        chip_area_w = self.panel_rect.width - 2 * self.gap
        chip_y = self.panel_rect.y + 2 * self.gap + status_surface.get_height()
        chip_w = max(
            42,
            (chip_area_w - (self.chip_cols - 1) * self.gap) // self.chip_cols,
        )

        for index, (title, value) in enumerate(chips):
            row = index // self.chip_cols
            col = index % self.chip_cols
            rect = pygame.Rect(
                chip_area_x + col * (chip_w + self.gap),
                chip_y + row * (self.chip_h + self.gap),
                chip_w,
                self.chip_h,
            )
            self._draw_chip(rect, title, value)

        self._draw_help_bar(
            "SPACE: Play/Pause  |  LEFT/RIGHT: Previous/Next step  |  R: Reset"
        )

    def draw_frame(self) -> None:
        self._draw_background()
        self._draw_header()
        self._draw_map()
        self._draw_button(self.btn_left, "Run UCS", Theme.BTN_BLUE)
        self._draw_button(self.btn_middle, "Run A*", Theme.BTN_ORANGE)
        self._draw_button(self.btn_right, "Reset", Theme.BTN_PINK)
        self._draw_info_panel()

    # PHẦN 4 - EVENT LOOP
    def run(self) -> None:
        running = True
        window_resized_event = getattr(pygame, "WINDOWRESIZED", -9999)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type in (pygame.VIDEORESIZE, window_resized_event):
                    self._handle_resize_event(event)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_left.collidepoint(event.pos):
                        self.run_solver("UCS")
                    elif self.btn_middle.collidepoint(event.pos):
                        self.run_solver("A*")
                    elif self.btn_right.collidepoint(event.pos):
                        self.reset_state()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.solution_actions:
                        self.is_paused = not self.is_paused
                        self.is_playing = True
                        self.last_step_time = time.time()
                    elif event.key == pygame.K_LEFT and self.solution_states:
                        self.is_paused = True
                        self.go_to_step(self.current_step - 1)
                    elif event.key == pygame.K_RIGHT and self.solution_states:
                        self.is_paused = True
                        self.go_to_step(self.current_step + 1)
                    elif event.key == pygame.K_r:
                        self.reset_state()

            # Nếu đang play và chưa pause thì tự chạy animation theo thời gian.
            if self.is_playing and not self.is_paused and self.solution_states:
                if time.time() - self.last_step_time >= Theme.AUTO_STEP_SEC:
                    if self.current_step < len(self.solution_actions):
                        self.current_step += 1
                        self.current_state = self.solution_states[self.current_step]
                        self.last_step_time = time.time()
                    else:
                        self.is_playing = False

            self.draw_frame()
            pygame.display.flip()
            self.clock.tick(Theme.FPS)

        # Chỉ đóng cửa sổ hiện tại rồi return.
        # Không sys.exit() vì UI có thể được gọi từ menu_ui.py hoặc main.py.
        pygame.quit()
        return


# PHẦN 5 - CHẠY TRỰC TIẾP TASK 5
def default_map_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "..", "Ex1", "testmap.txt")


def main(map_path: Optional[str] = None) -> None:
    if map_path is None:
        map_path = default_map_path()

    app = SokobanUI(map_path)
    app.run()


if __name__ == "__main__":
    main()
