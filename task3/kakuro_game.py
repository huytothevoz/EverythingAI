"""Kakuro Play Mode: independent player state, rules, hints, and Pygame UI."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import pygame

from boards import make_assignment_board
from kakuro_gui import COLORS, GRID_SIZE, build_grid_layout
from kakuro_solver import Cell, KakuroBoard, RunConstraint
from display_utils import initial_window_size


@dataclass(frozen=True)
class RunState:
    status: str
    valid: bool
    completed: bool


class PlaySession:
    """Owns player-entered values and checks Kakuro rules without solving."""

    def __init__(self, board: Optional[KakuroBoard] = None) -> None:
        self.board = board or make_assignment_board()
        self.white_cells = set(self.board.cells)
        self.runs_by_cell: Dict[Cell, Tuple[RunConstraint, ...]] = {
            cell: tuple(run for run in self.board.runs if cell in run.cells)
            for cell in self.board.cells
        }
        self.values: Dict[Cell, int] = {}
        self.notes: Dict[Cell, Set[int]] = {cell: set() for cell in self.board.cells}
        self._history: List[Tuple[Dict[Cell, int], Dict[Cell, Set[int]]]] = []
        self.check_count = 0
        self.hint_count = 0
        self.started_at = time.monotonic()
        self.elapsed_before_pause = 0.0
        self.paused_at: Optional[float] = None
        self.won = False
        self.last_hint = ""
        self.hint_cell: Optional[Cell] = None
        self.checked = False
        self.run_states: Dict[str, RunState] = {}
        self.refresh_validation()

    @property
    def elapsed_seconds(self) -> float:
        if self.paused_at is not None:
            return self.elapsed_before_pause
        return self.elapsed_before_pause + time.monotonic() - self.started_at

    def pause_clock(self) -> None:
        if self.paused_at is None:
            self.elapsed_before_pause += time.monotonic() - self.started_at
            self.paused_at = time.monotonic()

    def resume_clock(self) -> None:
        if self.paused_at is not None:
            self.started_at = time.monotonic()
            self.paused_at = None

    def _save_history(self) -> None:
        self._history.append(
            (dict(self.values), {cell: set(items) for cell, items in self.notes.items()})
        )
        if len(self._history) > 200:
            self._history.pop(0)

    def enter_value(self, cell: Cell, value: int) -> bool:
        if cell not in self.white_cells or not 1 <= value <= 9:
            return False
        self._save_history()
        self.values[cell] = value
        self.notes[cell].clear()
        self.last_hint = ""
        self.hint_cell = None
        self.checked = False
        self.refresh_validation(self.runs_by_cell[cell])
        return True

    def erase(self, cell: Cell) -> bool:
        if cell not in self.white_cells:
            return False
        if cell not in self.values and not self.notes[cell]:
            return False
        self._save_history()
        self.values.pop(cell, None)
        self.notes[cell].clear()
        self.last_hint = ""
        self.hint_cell = None
        self.checked = False
        self.refresh_validation(self.runs_by_cell[cell])
        return True

    def toggle_note(self, cell: Cell, value: int) -> bool:
        if cell not in self.white_cells or not 1 <= value <= 9 or cell in self.values:
            return False
        self._save_history()
        if value in self.notes[cell]:
            self.notes[cell].remove(value)
        else:
            self.notes[cell].add(value)
        return True

    def undo(self) -> bool:
        if not self._history:
            return False
        self.values, self.notes = self._history.pop()
        self.last_hint = ""
        self.hint_cell = None
        self.checked = False
        self.refresh_validation()
        return True

    def clear_entries(self) -> bool:
        if not self.values and not any(self.notes.values()):
            return False
        self._save_history()
        self.values.clear()
        self.notes = {cell: set() for cell in self.white_cells}
        self.last_hint = ""
        self.hint_cell = None
        self.checked = False
        self.refresh_validation()
        return True

    def restart(self) -> None:
        self.values.clear()
        self.notes = {cell: set() for cell in self.white_cells}
        self._history.clear()
        self.check_count = 0
        self.hint_count = 0
        self.started_at = time.monotonic()
        self.elapsed_before_pause = 0.0
        self.paused_at = None
        self.won = False
        self.last_hint = ""
        self.hint_cell = None
        self.checked = False
        self.refresh_validation()

    def evaluate_run(self, run: RunConstraint) -> RunState:
        filled = [self.values[cell] for cell in run.cells if cell in self.values]
        complete = len(filled) == len(run.cells)
        valid_tuples = [
            candidate
            for candidate in run.valid_tuples
            if all(
                cell not in self.values
                or candidate[index] == self.values[cell]
                for index, cell in enumerate(run.cells)
            )
        ]
        if not valid_tuples:
            return RunState("invalid", False, False)
        if complete:
            return RunState("completed", True, True)
        return RunState("valid", True, False)

    def refresh_validation(
        self,
        affected_runs: Optional[Tuple[RunConstraint, ...]] = None,
    ) -> None:
        runs = self.board.runs if affected_runs is None else affected_runs
        self.run_states.update({
            run.run_id: self.evaluate_run(run) for run in runs
        })
        won_now = (
            self.white_cells <= self.values.keys()
            and all(state.completed for state in self.run_states.values())
        )
        now = time.monotonic()
        if won_now and not self.won and self.paused_at is None:
            self.elapsed_before_pause += now - self.started_at
            self.paused_at = now
        elif not won_now and self.won and self.paused_at is not None:
            self.started_at = now
            self.paused_at = None
        self.won = won_now

    def check(self) -> Dict[str, RunState]:
        self.check_count += 1
        self.checked = True
        self.refresh_validation()
        return dict(self.run_states)

    def hint(self) -> str:
        self.hint_count += 1
        self.last_hint = ""
        self.hint_cell = None
        unfinished = [
            run for run in self.board.runs
            if not self.run_states[run.run_id].completed
        ]
        for run in unfinished:
            missing = [cell for cell in run.cells if cell not in self.values]
            if len(missing) != 1:
                continue
            remaining = run.target - sum(self.values[cell] for cell in run.cells if cell in self.values)
            used = {self.values[cell] for cell in run.cells if cell in self.values}
            cell = missing[0]
            if 1 <= remaining <= 9 and remaining not in used:
                direction = "ngang" if run.direction == "across" else "dọc"
                self.hint_cell = cell
                self.last_hint = (
                    f"Dãy {direction} {run.run_id} chỉ còn ô "
                    f"({cell[0] + 1},{cell[1] + 1}); clue còn thiếu {remaining}."
                )
                return self.last_hint

        candidates = [
            (sum(cell not in self.values for cell in run.cells), run)
            for run in unfinished
            if any(cell not in self.values for cell in run.cells)
        ]
        if candidates:
            _, run = min(candidates, key=lambda item: (item[0], item[1].run_id))
            self.hint_cell = next(cell for cell in run.cells if cell not in self.values)
            remaining = run.target - sum(
                self.values[cell] for cell in run.cells if cell in self.values
            )
            missing_count = sum(cell not in self.values for cell in run.cells)
            direction = "ngang" if run.direction == "across" else "dọc"
            self.last_hint = (
                f"Thử xét dãy {direction} {run.run_id}: còn {remaining} "
                f"điểm cho {missing_count} ô trống; các số trong dãy không được trùng."
            )
        else:
            self.last_hint = "Bảng đã điền hết; hãy kiểm tra lại các dãy được đánh dấu."
        return self.last_hint

    def invalid_cells(self) -> Set[Cell]:
        result: Set[Cell] = set()
        for run in self.board.runs:
            if not self.run_states[run.run_id].valid:
                result.update(cell for cell in run.cells if cell in self.values)
                result.update(cell for cell in run.cells if cell not in self.values)
        return result

    def completed_cells(self) -> Set[Cell]:
        result: Set[Cell] = set()
        for run in self.board.runs:
            if self.run_states[run.run_id].completed:
                result.update(run.cells)
        return result


class KakuroPlayGUI:
    """Keyboard-and-mouse Play Mode, independent of the CSP solver."""

    def __init__(self, board: Optional[KakuroBoard] = None) -> None:
        pygame.init()
        pygame.display.set_caption("Kakuro | Play Mode")
        self.screen = pygame.display.set_mode(
            initial_window_size((980, 760)), pygame.RESIZABLE
        )
        pygame.key.start_text_input()
        self.clock = pygame.time.Clock()
        self.session = PlaySession(board)
        self.clues, self.white_cells = build_grid_layout(self.session.board)
        self.running = True
        self.return_to_menu = False
        self.selected_cell = min(self.white_cells) if self.white_cells else None
        self.notes_mode = False
        self.message = "Chọn ô trắng rồi nhập số từ 1 đến 9."
        self.message_color = COLORS["muted"]
        self.font = pygame.font.SysFont("segoeui", 17)
        self.small_font = pygame.font.SysFont("segoeui", 14)
        self.tiny_font = pygame.font.SysFont("segoeui", 11)
        self.title_font = pygame.font.SysFont("segoeui", 29, bold=True)
        self.cell_font = pygame.font.SysFont("segoeui", 26, bold=True)
        self.clue_font = pygame.font.SysFont("segoeui", 15, bold=True)
        self.buttons: Dict[str, pygame.Rect] = {}
        self._last_key_digit: Optional[int] = None
        self.cell_size = 58
        self.grid_x = 60
        self.grid_y = 150
        self._layout()
        self._update_run_highlights()

    def _layout(self) -> None:
        width, height = self.screen.get_size()
        toolbar_y = height - 90
        horizontal_gap = 24
        self.cell_size = max(
            24,
            min(
                58,
                (height - 210) // GRID_SIZE,
                (width - 48 - horizontal_gap - 320) // GRID_SIZE,
            ),
        )
        board_size = self.cell_size * GRID_SIZE
        self.grid_y = max(120, min(150, toolbar_y - board_size - 24))
        panel_width = min(380, max(280, width - 48 - board_size - horizontal_gap))
        content_width = board_size + horizontal_gap + panel_width
        self.grid_x = max(24, (width - content_width) // 2)
        panel_x = self.grid_x + board_size + horizontal_gap
        names = ("check", "hint", "undo", "clear", "restart", "mode")
        button_gap = 8
        button_width = min(112, max(56, (width - 48 - 5 * button_gap) // 6))
        button_group_width = 6 * button_width + 5 * button_gap
        button_start_x = max(24, (width - button_group_width) // 2)
        self.buttons = {
            name: pygame.Rect(
                button_start_x + index * (button_width + button_gap),
                toolbar_y,
                button_width,
                46,
            )
            for index, name in enumerate(names)
        }
        panel_height = min(350, board_size)
        panel_y = self.grid_y + (board_size - panel_height) // 2
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self.menu_button = pygame.Rect(width - 186, 36, 154, 38)

    def _set_message(self, message: str, color: Tuple[int, int, int] = COLORS["muted"]) -> None:
        self.message = message
        self.message_color = color

    def _update_run_highlights(self) -> None:
        if self.session.checked:
            self.invalid_cells = self.session.invalid_cells()
            self.completed_cells = self.session.completed_cells()
        else:
            self.invalid_cells = {
                cell
                for run in self.session.board.runs
                if not self.session.run_states[run.run_id].valid
                for cell in run.cells
            }
            self.completed_cells = set()

    def _select_cell(self, cell: Cell) -> None:
        if cell in self.white_cells:
            self.selected_cell = cell

    def _move_selection(self, key: int) -> None:
        if not self.white_cells:
            return
        if self.selected_cell is None:
            self.selected_cell = min(self.white_cells)
            return
        row, col = self.selected_cell
        candidates = []
        for other_row, other_col in self.white_cells:
            delta_row, delta_col = other_row - row, other_col - col
            if key == pygame.K_LEFT and delta_row == 0 and delta_col < 0:
                candidates.append((abs(delta_col), other_row, other_col))
            elif key == pygame.K_RIGHT and delta_row == 0 and delta_col > 0:
                candidates.append((abs(delta_col), other_row, other_col))
            elif key == pygame.K_UP and delta_col == 0 and delta_row < 0:
                candidates.append((abs(delta_row), other_row, other_col))
            elif key == pygame.K_DOWN and delta_col == 0 and delta_row > 0:
                candidates.append((abs(delta_row), other_row, other_col))
        if candidates:
            _, next_row, next_col = min(candidates)
            self.selected_cell = (next_row, next_col)

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            self._layout()
            return
        if event.type == pygame.TEXTINPUT:
            text = event.text
            if len(text) == 1 and text in "123456789":
                value = int(text)
                if value == self._last_key_digit:
                    self._last_key_digit = None
                else:
                    self._enter_digit(value)
                    self._update_run_highlights()
            return
        if event.type == pygame.KEYDOWN:
            digit = self._digit_from_event(event)
            self._last_key_digit = None
            if event.key == pygame.K_ESCAPE:
                self.return_to_menu = True
                self.running = False
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                self._move_selection(event.key)
            elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                if self.selected_cell is not None and self.session.erase(self.selected_cell):
                    self._set_message("Ô đã được xóa.", COLORS["accent"])
            elif event.key == pygame.K_n:
                self.notes_mode = not self.notes_mode
                self._set_message(
                    "Đang bật ghi chú." if self.notes_mode else "Đã tắt ghi chú.",
                    COLORS["accent"],
                )
            elif digit is not None and self.selected_cell is not None:
                self._last_key_digit = digit
                self._enter_digit(digit)
            self._update_run_highlights()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.menu_button.collidepoint(event.pos):
                self.return_to_menu = True
                self.running = False
                return
            for name, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    self._handle_action(name)
                    return
            cell = self._cell_at(event.pos)
            if cell is not None:
                self._select_cell(cell)

    def _enter_digit(self, value: int) -> None:
        if self.selected_cell is None:
            return
        if self.notes_mode:
            if self.session.toggle_note(self.selected_cell, value):
                self._set_message(f"Đã thêm/bỏ ghi chú {value}.", COLORS["accent"])
        elif self.session.enter_value(self.selected_cell, value):
            self._set_message(
                f"Đã nhập {value} vào ô ({self.selected_cell[0] + 1},"
                f"{self.selected_cell[1] + 1}).",
                COLORS["accent"],
            )
            if self.session.won:
                self._set_message("Chúc mừng! Bạn đã giải đúng Kakuro.", COLORS["green"])

    @staticmethod
    def _digit_from_event(event: pygame.event.Event) -> Optional[int]:
        text = getattr(event, "unicode", "") or ""
        if len(text) == 1 and text in "123456789":
            return int(text)

        key_digits = {
            pygame.K_1: 1,
            pygame.K_2: 2,
            pygame.K_3: 3,
            pygame.K_4: 4,
            pygame.K_5: 5,
            pygame.K_6: 6,
            pygame.K_7: 7,
            pygame.K_8: 8,
            pygame.K_9: 9,
            pygame.K_KP1: 1,
            pygame.K_KP2: 2,
            pygame.K_KP3: 3,
            pygame.K_KP4: 4,
            pygame.K_KP5: 5,
            pygame.K_KP6: 6,
            pygame.K_KP7: 7,
            pygame.K_KP8: 8,
            pygame.K_KP9: 9,
        }
        return key_digits.get(event.key)

    def _handle_action(self, name: str) -> None:
        if name == "check":
            states = self.session.check()
            invalid_count = sum(not state.valid for state in states.values())
            completed_count = sum(state.completed for state in states.values())
            if self.session.won:
                self._set_message("Chúc mừng! Mọi dãy đều hợp lệ.", COLORS["green"])
            elif invalid_count:
                self._set_message(
                    f"Có {invalid_count} dãy vi phạm; ô liên quan đã được tô đỏ.",
                    COLORS["red"],
                )
            else:
                self._set_message(
                    f"Lựa chọn hiện tại hợp lệ; {completed_count}/{len(states)} dãy đã hoàn tất.",
                    COLORS["green"],
                )
        elif name == "hint":
            hint = self.session.hint()
            self._set_message(hint, COLORS["orange"])
            if self.session.hint_cell is not None:
                self.selected_cell = self.session.hint_cell
        elif name == "undo":
            if self.session.undo():
                self._set_message("Đã hoàn tác thao tác gần nhất.", COLORS["accent"])
            else:
                self._set_message("Chưa có thao tác để hoàn tác.", COLORS["muted"])
        elif name == "clear":
            if self.session.clear_entries():
                self._set_message("Đã xóa các số và ghi chú của bạn.", COLORS["accent"])
            else:
                self._set_message("Bảng chưa có dữ liệu để xóa.", COLORS["muted"])
        elif name == "restart":
            self.session.restart()
            self.selected_cell = min(self.white_cells) if self.white_cells else None
            self.notes_mode = False
            self._set_message("Puzzle đã khởi động lại.", COLORS["accent"])
        elif name == "mode":
            self.return_to_menu = True
            self.running = False
        self._update_run_highlights()

    def _cell_at(self, position: Tuple[int, int]) -> Optional[Cell]:
        x, y = position
        col = (x - self.grid_x) // self.cell_size
        row = (y - self.grid_y) // self.cell_size
        cell = (int(row), int(col))
        return cell if cell in self.white_cells else None

    def _draw_text(
        self,
        text: str,
        position: Tuple[int, int],
        color: Tuple[int, int, int],
        font: Optional[pygame.font.Font] = None,
    ) -> pygame.Rect:
        surface = (font or self.font).render(text, True, color)
        rect = surface.get_rect(topleft=position)
        self.screen.blit(surface, rect)
        return rect

    def _draw(self) -> None:
        self._layout()
        self.screen.fill(COLORS["background"])
        self._draw_text("KAKURO", (self.grid_x, 25), COLORS["accent"], self.small_font)
        self._draw_text("Play Mode", (self.grid_x, 44), COLORS["text"], self.title_font)
        self._draw_text(
            "Tự suy luận · Không có đáp án tự điền",
            (self.grid_x + 2, 91),
            COLORS["muted"],
            self.small_font,
        )
        self._draw_button(self.menu_button, "← Chọn chế độ", COLORS["panel_alt"])
        self._draw_board()
        self._draw_side_panel()
        self._draw_toolbar()
        pygame.display.flip()

    def _draw_board(self) -> None:
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cell = (row, col)
                rect = pygame.Rect(
                    self.grid_x + col * self.cell_size,
                    self.grid_y + row * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                if cell in self.white_cells:
                    self._draw_play_cell(cell, rect)
                elif cell in self.clues:
                    self._draw_clue(cell, rect)
                else:
                    pygame.draw.rect(self.screen, COLORS["empty_cell"], rect)
                    pygame.draw.rect(self.screen, COLORS["border"], rect, 1)

    def _draw_play_cell(self, cell: Cell, rect: pygame.Rect) -> None:
        fill = COLORS["white_cell"]
        if cell in self.invalid_cells:
            fill = (255, 215, 218)
        elif cell in self.completed_cells:
            fill = (207, 244, 224)
        pygame.draw.rect(self.screen, fill, rect)
        selected = cell == self.selected_cell
        pygame.draw.rect(
            self.screen,
            COLORS["accent"] if selected else COLORS["border"],
            rect,
            3 if selected else 1,
        )
        value = self.session.values.get(cell)
        if value is not None:
            surface = self.cell_font.render(str(value), True, COLORS["white_text"])
            self.screen.blit(surface, surface.get_rect(center=rect.center))
        elif self.session.notes[cell]:
            text = " ".join(str(item) for item in sorted(self.session.notes[cell]))
            surface = self.tiny_font.render(text, True, COLORS["accent_dark"])
            self.screen.blit(surface, surface.get_rect(center=rect.center))

    def _draw_clue(self, cell: Cell, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, COLORS["black_cell"], rect)
        pygame.draw.line(
            self.screen,
            COLORS["border"],
            (rect.left + 2, rect.bottom - 2),
            (rect.right - 2, rect.top + 2),
            2,
        )
        clue = self.clues[cell]
        if "across" in clue:
            self._draw_text(
                str(clue["across"]),
                (rect.x + 4, rect.y + 3),
                COLORS["clue_across"],
                self.clue_font,
            )
        if "down" in clue:
            surface = self.clue_font.render(str(clue["down"]), True, COLORS["clue_down"])
            self.screen.blit(surface, surface.get_rect(bottomright=(rect.right - 4, rect.bottom - 3)))
        pygame.draw.rect(self.screen, COLORS["border"], rect, 1)

    def _draw_side_panel(self) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], self.panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLORS["border"], self.panel_rect, 1, border_radius=12)
        x, y = self.panel_rect.x + 18, self.panel_rect.y + 18
        self._draw_text("TRẠNG THÁI", (x, y), COLORS["muted"], self.small_font)
        status = "CHIẾN THẮNG!" if self.session.won else (
            "CẦN KIỂM TRA LẠI" if self.invalid_cells else "ĐANG CHƠI"
        )
        status_color = COLORS["green"] if self.session.won else (
            COLORS["red"] if self.invalid_cells else COLORS["accent"]
        )
        self._draw_text(status, (x, y + 28), status_color, self.title_font)
        self._draw_text(f"Thời gian: {self._format_time(self.session.elapsed_seconds)}", (x, y + 78), COLORS["text"])
        self._draw_text(f"Số đã nhập: {len(self.session.values)}/{len(self.white_cells)}", (x, y + 108), COLORS["text"])
        self._draw_text(f"Check: {self.session.check_count}    Hint: {self.session.hint_count}", (x, y + 137), COLORS["text"])
        if self.selected_cell is not None:
            self._draw_text(
                f"Ô chọn: ({self.selected_cell[0] + 1},{self.selected_cell[1] + 1})",
                (x, y + 171),
                COLORS["muted"],
            )
        pygame.draw.line(
            self.screen,
            COLORS["border"],
            (x, y + 207),
            (self.panel_rect.right - 18, y + 207),
            1,
        )
        self._draw_text("ĐIỀU KHIỂN", (x, y + 225), COLORS["muted"], self.small_font)
        instructions = (
            "Click ô trắng rồi gõ phím 1–9 để nhập số.",
            "Dùng phím mũi tên để chuyển ô đang chọn.",
            "Backspace/Delete xóa ô; N bật/tắt ghi chú.",
        )
        for index, instruction in enumerate(instructions):
            self._draw_text(
                instruction,
                (x, y + 254 + index * 24),
                COLORS["muted"],
                self.small_font,
            )

    def _draw_toolbar(self) -> None:
        labels = {
            "check": "Check",
            "hint": "Hint",
            "undo": "Undo",
            "clear": "Clear",
            "restart": "Restart",
            "mode": "Modes",
        }
        colors = {
            "check": COLORS["accent_dark"],
            "hint": COLORS["panel_alt"],
            "undo": COLORS["panel_alt"],
            "clear": COLORS["panel_alt"],
            "restart": COLORS["panel_alt"],
            "mode": COLORS["panel_alt"],
        }
        for name, rect in self.buttons.items():
            self._draw_button(rect, labels[name], colors[name])
        notes_text = "Notes: ON" if self.notes_mode else "Notes: OFF"
        footer_y = self.screen.get_height() - 34
        self._draw_text(notes_text, (42, footer_y), COLORS["accent"], self.small_font)
        message_x = 220
        available_width = max(0, self.screen.get_width() - message_x - 16)
        message = self.message
        while message and self.tiny_font.size(message)[0] > available_width:
            message = message[:-1]
        if message != self.message and len(message) > 3:
            message = message[:-3] + "..."
        self._draw_text(message, (message_x, footer_y), self.message_color, self.tiny_font)

    def _draw_button(
        self,
        rect: pygame.Rect,
        label: str,
        color: Tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(self.screen, color, rect, border_radius=9)
        pygame.draw.rect(self.screen, COLORS["border"], rect, 1, border_radius=9)
        text = self.font.render(label, True, COLORS["text"])
        self.screen.blit(text, text.get_rect(center=rect.center))

    @staticmethod
    def _format_time(seconds: float) -> str:
        total = int(seconds)
        return f"{total // 60:02}:{total % 60:02}"

    def run(self) -> bool:
        while self.running:
            self.clock.tick(60)
            for event in pygame.event.get():
                self._handle_event(event)
            self._draw()
        pygame.key.stop_text_input()
        return self.return_to_menu


def main() -> None:
    from main import main as application_main

    application_main()


if __name__ == "__main__":
    main()
