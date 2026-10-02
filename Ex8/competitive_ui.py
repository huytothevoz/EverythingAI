"""
Requirement 8 - Competitive GUI cho Sokoban 2 agent.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional, Tuple

import pygame

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from Ex5.ui_components import ResponsiveSokobanUIBase, Theme
from Ex6.game_logic_competitive import CompetitiveSokobanGame
from Ex7.agent1 import choose_action as agent1_choose_action
from Ex7.agent2 import choose_action as agent2_choose_action


class CompetitiveUI(ResponsiveSokobanUIBase):
    """Giao diện chính của Requirement 8."""

    # Màu box đã hoàn thành của từng agent.
    OWNER1 = (255, 112, 88)
    OWNER2 = (80, 194, 114)
    OWNER0 = (245, 191, 64)

    def __init__(self, map_path: str, max_steps: int = 30):
        self.map_path = map_path
        self.game = CompetitiveSokobanGame(map_path, max_steps=max_steps)
        rows, cols = self._get_map_dimensions()

        # Dùng lại base UI của Task 5.
        super().__init__(
            rows=rows,
            cols=cols,
            window_title="Office Sokoban Competitive - Task 8",
            header_subtitle="Task 8 - Competitive Visual Mode (Agent 1 vs Agent 2)",
            initial_width_ratio=0.74,
            initial_height_ratio=0.78,
        )

        self.reset_state()

    # Thiết lập layout
    def _get_map_dimensions(self) -> Tuple[int, int]:
        state = self.game.initial_state
        positions = (
            self.game.walls
            | self.game.red_points
            | set(state.boxes)
            | {state.agent1_pos, state.agent2_pos}
        )
        return max(r for r, _ in positions) + 1, max(c for _, c in positions) + 1

    def _get_panel_layout_settings(self) -> Tuple[int, int]:
        """Đổi cách xếp panel theo chiều rộng."""
        self.chip_cols = 4 if self.window_w >= 720 else 2
        self.chip_rows = 1 if self.chip_cols == 4 else 2

        # Cửa sổ thấp thì ưu tiên board và control.
        self.show_legend = self.window_h >= 640 and self.window_w >= 720

        status_h = max(18, self.font_body.get_height())
        chip_block_h = self.chip_rows * self.chip_h + (self.chip_rows - 1) * self.gap
        legend_h = max(18, self.font_small.get_height() + 4) if self.show_legend else 0

        panel_h = (
            self.gap
            + status_h
            + self.gap
            + chip_block_h
            + (self.gap + legend_h if self.show_legend else 0)
            + self.gap
        )

        help_h = max(24, int(32 * self.ui_scale)) if self.window_h >= 560 else 0
        return panel_h, help_h

    # State và game loop
    def reset_state(self) -> None:
        """Reset trận đấu về state ban đầu."""
        self.history_states = [self.game.initial_state]
        self.history_actions = []
        self.history_times = []
        self.current_step = 0
        self.current_state = self.game.initial_state
        self.is_playing = False
        self.is_paused = True
        self.last_step_time = time.time()
        self.last_actions = ("-", "-")
        self.last_times = (0.0, 0.0)

    def go_to_step(self, step: int) -> None:
        """Di chuyển tới một state trong history."""
        if 0 <= step < len(self.history_states):
            self.current_step = step
            self.current_state = self.history_states[step]

            if step == 0:
                self.last_actions = ("-", "-")
                self.last_times = (0.0, 0.0)
            else:
                self.last_actions = self.history_actions[step - 1]
                self.last_times = self.history_times[step - 1]

    def compute_next_turn(self) -> None:
        """Cho hai agent chọn action từ cùng state đầu turn."""
        if self.current_state.steps_left <= 0:
            self.is_playing = False
            self.is_paused = True
            return

        state_before_turn = self.current_state

        # Agent 1 dùng GBFS.
        start = time.perf_counter()
        action1 = agent1_choose_action(self.game, state_before_turn, 1000)
        t1_ms = (time.perf_counter() - start) * 1000

        # Agent 2 dùng A* và nhận cùng state đầu turn.
        start = time.perf_counter()
        action2 = agent2_choose_action(self.game, state_before_turn, 1000)
        t2_ms = (time.perf_counter() - start) * 1000

        # Ex6 xử lý hai action đồng thời.
        next_state = self.game.apply_joint_actions(
            state_before_turn,
            action1,
            action2,
        )

        self.history_states.append(next_state)
        self.history_actions.append((action1, action2))
        self.history_times.append((t1_ms, t2_ms))

        self.current_step += 1
        self.current_state = next_state
        self.last_actions = (action1, action2)
        self.last_times = (t1_ms, t2_ms)

    def step_forward(self) -> None:
        """Đi tới state cũ hoặc tính thêm một turn."""
        if self.current_step < len(self.history_states) - 1:
            self.go_to_step(self.current_step + 1)
        else:
            self.compute_next_turn()

    # Vẽ competitive mode
    def _draw_board(self) -> None:
        """Vẽ map, hai agent và trạng thái các box."""
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
        agent1 = self.assets.get_scaled("agent1", (self.cell_size, self.cell_size))
        agent2 = self.assets.get_scaled("agent2", (self.cell_size, self.cell_size))

        owners = self.current_state.get_owner_dict()
        water_dispenser = self.assets.get_scaled("water_dispenser", (self.cell_size, self.cell_size))
        water_dispenser_neutral = self.assets.get_tinted_water_dispenser(self.cell_size, self.OWNER0, "OK")
        water_dispenser_1 = self.assets.get_tinted_water_dispenser(self.cell_size, self.OWNER1, "A1")
        water_dispenser_2 = self.assets.get_tinted_water_dispenser(self.cell_size, self.OWNER2, "A2")

        for r in range(self.rows):
            for c in range(self.cols):
                pos = (r, c)
                x = self.board_x + c * self.cell_size
                y = self.board_y + r * self.cell_size

                if pos in self.game.walls:
                    self.screen.blit(wall, (x, y))
                    continue

                self.screen.blit(floor, (x, y))

                if pos in self.game.red_points:
                    self._draw_goal_marker(x, y)

                if pos in self.current_state.boxes:
                    if pos not in self.game.red_points:
                        water_dispenser_img = water_dispenser
                    else:
                        owner = owners.get(pos, 0)
                        if owner == 1:
                            water_dispenser_img = water_dispenser_1
                        elif owner == 2:
                            water_dispenser_img = water_dispenser_2
                        else:
                            water_dispenser_img = water_dispenser_neutral

                    self.screen.blit(water_dispenser_img, (x, y))

                # Agent 1 là nam, Agent 2 là nữ.
                if pos == self.current_state.agent1_pos:
                    self.screen.blit(agent1, (x, y))
                elif pos == self.current_state.agent2_pos:
                    self.screen.blit(agent2, (x, y))

    def _draw_panel(self) -> None:
        """Vẽ điểm số, thời gian và chú thích owner."""
        radius = max(7, int(18 * self.ui_scale))
        pygame.draw.rect(self.screen, Theme.CARD, self.panel_rect, border_radius=radius)
        pygame.draw.rect(
            self.screen,
            Theme.CARD_BORDER,
            self.panel_rect,
            width=2,
            border_radius=radius,
        )

        scores = self.game.get_scores(self.current_state)
        turns_used = self.game.max_steps - self.current_state.steps_left
        winner = self.game.get_winner(self.current_state) if self.current_state.steps_left <= 0 else None

        if turns_used == 0:
            status = "Nhấn Play hoặc Step để bắt đầu trận đấu."
        elif winner == 0:
            status = "Kết thúc: Hòa"
        elif winner in (1, 2):
            status = f"Kết thúc: Agent {winner} thắng"
        else:
            status = f"Lượt gần nhất: A1={self.last_actions[0]} | A2={self.last_actions[1]}"

        status_surface = self.font_body.render(status, True, Theme.TEXT_DIM)
        self.screen.blit(
            status_surface,
            (self.panel_rect.x + self.gap, self.panel_rect.y + self.gap),
        )

        chips = [
            ("Turns", f"{turns_used}/{self.game.max_steps}"),
            ("Score", f"A1 {scores['agent1']} - {scores['agent2']} A2"),
            ("A1 time", f"{self.last_times[0]:.1f} ms"),
            ("A2 time", f"{self.last_times[1]:.1f} ms"),
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

        if self.show_legend:
            legend_y = (
                chip_y
                + self.chip_rows * self.chip_h
                + (self.chip_rows - 1) * self.gap
                + self.gap
            )
            legend_items = [
                (self.OWNER1, "Cam: box Agent 1"),
                (self.OWNER2, "Xanh: box Agent 2"),
                (self.OWNER0, "Vàng: chưa thuộc ai"),
            ]

            available = self.panel_rect.width - 2 * self.gap
            item_w = available // 3

            for i, (color, text) in enumerate(legend_items):
                lx = self.panel_rect.x + self.gap + i * item_w
                cy = legend_y + self.font_small.get_height() // 2
                pygame.draw.circle(
                    self.screen,
                    color,
                    (lx + 6, cy),
                    max(4, int(5 * self.ui_scale)),
                )
                label = self.font_small.render(text, True, Theme.TEXT)
                self.screen.blit(label, (lx + 16, legend_y))

        self._draw_help_bar(
            "SPACE: Play/Pause  |  LEFT: Backward  |  RIGHT: Step  |  R: Reset"
        )

    def draw_frame(self) -> None:
        self._draw_background()
        self._draw_header()
        self._draw_board()

        play_text = "Pause" if self.is_playing and not self.is_paused else "Play"
        self._draw_button(self.btn_left, play_text, Theme.BTN_BLUE)
        self._draw_button(self.btn_middle, "Step", Theme.BTN_ORANGE)
        self._draw_button(self.btn_right, "Reset", Theme.BTN_PINK)
        self._draw_panel()

    # Event loop
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
                        self.is_paused = not self.is_paused
                        self.is_playing = not self.is_paused
                        self.last_step_time = time.time()
                    elif self.btn_middle.collidepoint(event.pos):
                        self.is_paused = True
                        self.is_playing = False
                        self.step_forward()
                    elif self.btn_right.collidepoint(event.pos):
                        self.reset_state()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                        self.is_playing = not self.is_paused
                        self.last_step_time = time.time()
                    elif event.key == pygame.K_LEFT:
                        self.is_paused = True
                        self.is_playing = False
                        self.go_to_step(self.current_step - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.is_paused = True
                        self.is_playing = False
                        self.step_forward()
                    elif event.key == pygame.K_r:
                        self.reset_state()

            if self.is_playing and not self.is_paused:
                if self.current_state.steps_left <= 0:
                    self.is_playing = False
                    self.is_paused = True
                elif time.time() - self.last_step_time >= Theme.AUTO_STEP_SEC:
                    self.step_forward()
                    self.last_step_time = time.time()

            self.draw_frame()
            pygame.display.flip()
            self.clock.tick(Theme.FPS)

        # Đóng UI rồi quay về menu gọi nó.
        pygame.quit()
        return

# Chạy trực tiếp Task 8
def default_map_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "..", "Ex6", "competitive_map.txt")


def main(map_path: Optional[str] = None, max_steps: int = 30) -> None:
    if map_path is None:
        map_path = default_map_path()

    app = CompetitiveUI(map_path, max_steps=max_steps)
    app.run()


if __name__ == "__main__":
    main()
