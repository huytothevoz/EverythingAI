"""Pygame interface for visualizing the Kakuro CSP solver."""

from __future__ import annotations

import queue
import threading
import time
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple

import pygame

from boards import make_assignment_board
from kakuro_solver import Cell, KakuroBoard, KakuroSolver, SolverEvent

Color = Tuple[int, int, int]

WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 900
GRID_SIZE = 9
CELL_SIZE = 58
GRID_X = 276
GRID_Y = 150
PANEL_X = 820
PANEL_WIDTH = 590

COLORS: Dict[str, Color] = {
    "background": (12, 18, 32),
    "sidebar": (17, 26, 44),
    "panel": (22, 32, 52),
    "panel_alt": (27, 39, 62),
    "border": (48, 63, 88),
    "text": (235, 241, 250),
    "muted": (150, 164, 186),
    "white_cell": (235, 241, 248),
    "white_text": (25, 38, 57),
    "black_cell": (27, 35, 51),
    "empty_cell": (9, 14, 25),
    "accent": (83, 169, 255),
    "accent_dark": (40, 108, 183),
    "green": (72, 196, 142),
    "red": (255, 104, 119),
    "orange": (255, 177, 82),
    "clue_across": (255, 192, 106),
    "clue_down": (112, 190, 255),
    "domain_removed": (250, 116, 128),
}


class _RunCancelled(Exception):
    """Internal signal used to stop a worker after Reset."""


class _RunControl:
    """Cancel the solver worker without blocking its event callback."""

    def __init__(self) -> None:
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()

    def publish(self, event: SolverEvent, output: queue.Queue) -> None:
        if self._cancelled.is_set():
            raise _RunCancelled
        output.put(("event", event))


def build_grid_layout(
    board: KakuroBoard,
) -> Tuple[Dict[Cell, Dict[str, int]], Set[Cell]]:
    """Derive clue squares and white cells from the backend's run constraints."""
    white_cells = set(board.cells)
    clues: Dict[Cell, Dict[str, int]] = {}
    for run in board.runs:
        row, col = run.cells[0]
        clue_cell = (row, col - 1) if run.direction == "across" else (row - 1, col)
        clues.setdefault(clue_cell, {})[run.direction] = run.target

    if any(not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE)
           for row, col in white_cells | set(clues)):
        raise ValueError("The assignment board has cells or clues outside the 9x9 grid.")
    if white_cells & set(clues):
        raise ValueError("A clue square overlaps a white Kakuro cell.")
    return clues, white_cells


class KakuroGUI:
    """Interactive, event-by-event visualization of the existing CSP solver."""

    def __init__(self, board: Optional[KakuroBoard] = None) -> None:
        pygame.init()
        pygame.display.set_caption("Kakuro CSP | AI Learning Lab")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.board = board or make_assignment_board()
        self.clues, self.white_cells = build_grid_layout(self.board)

        self.font = pygame.font.SysFont("segoeui", 17)
        self.small_font = pygame.font.SysFont("segoeui", 13)
        self.tiny_font = pygame.font.SysFont("segoeui", 10)
        self.heading_font = pygame.font.SysFont("segoeui", 23, bold=True)
        self.title_font = pygame.font.SysFont("segoeui", 29, bold=True)
        self.cell_font = pygame.font.SysFont("segoeui", 25, bold=True)
        self.clue_font = pygame.font.SysFont("segoeui", 15, bold=True)

        self.propagation = "gac"
        self.use_mrv = True
        self.use_degree = True
        self.use_lcv = True
        self.speed = 8.0
        self.running = True
        self.paused = True
        self.status = "Sẵn sàng"
        self.status_detail = "Nhấn Bắt đầu để khởi chạy solver."
        self.error_message = ""
        self.return_to_menu = False

        self._run_id = 0
        self._control: Optional[_RunControl] = None
        self._worker: Optional[threading.Thread] = None
        self._messages: queue.Queue = queue.Queue()
        self._deferred_message = None
        self._playback_permits = 0
        self._last_release = 0.0
        self._event_count = 0
        self._event_lines: List[Tuple[str, Color]] = []
        self._event_scroll = 0
        self._domain_undo: List[Tuple[Cell, Set[int]]] = []
        self._decision_frames: List[Tuple[Cell, int]] = []
        self._last_removed: Dict[Cell, Set[int]] = {}
        self._last_event_kind: Optional[str] = None
        self._stats: Optional[Mapping[str, float | int]] = None
        self._solution: Optional[Mapping[Cell, int]] = None
        self._reset_view()
        self._make_controls()

    def _make_controls(self) -> None:
        self.propagation_rect = pygame.Rect(28, 230, 194, 44)
        self.mrv_rect = pygame.Rect(30, 308, 24, 24)
        self.degree_rect = pygame.Rect(30, 353, 24, 24)
        self.lcv_rect = pygame.Rect(30, 398, 24, 24)
        self.start_rect = pygame.Rect(275, 788, 112, 48)
        self.pause_rect = pygame.Rect(399, 788, 128, 48)
        self.step_rect = pygame.Rect(539, 788, 104, 48)
        self.reset_rect = pygame.Rect(655, 788, 104, 48)
        self.mode_rect = pygame.Rect(276, 82, 142, 36)
        self.speed_track = pygame.Rect(905, 807, 220, 8)
        self.speed_handle = pygame.Rect(0, 0, 18, 24)
        self.dragging_speed = False

    def _reset_view(self) -> None:
        self.domains: Dict[Cell, Set[int]] = {
            cell: set(range(1, 10)) for cell in self.board.cells
        }
        for cell, value in self.board.givens.items():
            self.domains[cell] = {value}
        self.assignments: Dict[Cell, int] = dict(self.board.givens)
        self.active_cell: Optional[Cell] = None
        self.selected_cell: Optional[Cell] = self.board.cells[0] if self.board.cells else None
        self.highlighted_run: Set[Cell] = set()
        self._event_count = 0
        self._event_lines = []
        self._event_scroll = 0
        self._domain_undo = []
        self._decision_frames = []
        self._last_removed = {}
        self._last_event_kind = None
        self._stats = None
        self._solution = None
        self.error_message = ""

    def start(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            return
        self._run_id += 1
        run_id = self._run_id
        self._messages = queue.Queue()
        self._deferred_message = None
        self._playback_permits = 0
        self._reset_view()
        self._control = _RunControl()
        control = self._control
        output = self._messages
        self.paused = False
        self.status = "Đang giải"
        self.status_detail = "Đang chờ sự kiện solver đầu tiên."
        self._last_release = time.monotonic()

        def solve_in_background() -> None:
            try:
                solver = KakuroSolver(
                    self.board,
                    propagation=self.propagation,
                    use_mrv=self.use_mrv,
                    use_degree=self.use_degree,
                    use_lcv=self.use_lcv,
                    event_callback=lambda event: control.publish(event, output),
                )
                solution = solver.solve()
                output.put(("done", run_id, solution, solver.stats.as_dict()))
            except _RunCancelled:
                return
            except Exception as exc:
                output.put(("error", run_id, exc))

        self._worker = threading.Thread(
            target=solve_in_background,
            name=f"kakuro-solver-{run_id}",
            daemon=True,
        )
        self._worker.start()

    def reset(self) -> None:
        if self._control is not None:
            self._control.cancel()
        self._run_id += 1
        self._control = None
        self._worker = None
        self._messages = queue.Queue()
        self._reset_view()
        self.paused = True
        self.status = "Đã đặt lại"
        self.status_detail = "Bảng và miền đã trở về trạng thái ban đầu."

    def toggle_pause(self) -> None:
        if not self._solver_is_active():
            return
        self.paused = not self.paused
        self._playback_permits = 0
        self.status = "Đã tạm dừng" if self.paused else "Đang giải"
        self.status_detail = (
            "Nhấn Tiếp tục hoặc Bước để xem sự kiện kế tiếp."
            if self.paused else "Sự kiện được phát theo tốc độ đã chọn."
        )
        self._last_release = time.monotonic()

    def step(self) -> None:
        if not self._solver_is_active():
            return
        self.paused = True
        self._playback_permits = 1
        self.status = "Đang chạy từng bước"
        self.status_detail = "Mỗi lần bấm sẽ xử lý đúng một SolverEvent."

    def _release_playback_event(self) -> None:
        if self.paused or not self._solver_is_active():
            return
        now = time.monotonic()
        interval = 1.0 / max(self.speed, 0.5)
        if now - self._last_release >= interval and self._playback_permits == 0:
            self._last_release = now
            self._playback_permits = 1

    def _poll_messages(self) -> None:
        for _ in range(100):
            if self._deferred_message is not None:
                message = self._deferred_message
                self._deferred_message = None
            else:
                try:
                    message = self._messages.get_nowait()
                except queue.Empty:
                    break
            kind = message[0]
            if kind == "event":
                if self.paused and self._playback_permits == 0:
                    self._deferred_message = message
                    break
                if self.paused:
                    self._playback_permits -= 1
                self._process_solver_event(message[1])
            elif message[1] == self._run_id and kind == "done":
                _, _, solution, stats = message
                self._solution = solution
                self._stats = stats
                self.paused = True
                if solution is None:
                    self.status = "Không tìm thấy nghiệm"
                    self.status_detail = "Các ràng buộc hiện tại không có phép gán hợp lệ."
                else:
                    self.status = "Đã tìm thấy nghiệm"
                    self.status_detail = "Nghiệm đã được xác nhận bởi validate_solution()."
            elif message[1] == self._run_id and kind == "error":
                _, _, exc = message
                self.paused = True
                self.status = "Lỗi solver"
                self.status_detail = str(exc)
                self.error_message = repr(exc)

    def _process_solver_event(self, event: SolverEvent) -> None:
        self._event_count += 1
        self._last_event_kind = event.kind
        self.active_cell = event.cell
        if event.cell is not None:
            self.selected_cell = event.cell
        self.highlighted_run = set()
        if event.run_id is not None:
            run = next((item for item in self.board.runs if item.run_id == event.run_id), None)
            if run is not None:
                self.highlighted_run = set(run.cells)

        if event.kind == "domain_reduced" and event.cell is not None:
            if event.run_id is None and event.message.startswith("Decision:"):
                self._decision_frames.append((event.cell, len(self._domain_undo)))
            self._domain_undo.append((event.cell, set(event.before)))
            self.domains[event.cell] = set(event.after)
            removed = sorted(set(event.before) - set(event.after))
            self._last_removed[event.cell] = set(removed)
            label = "[GAC]" if self.propagation == "gac" else (
                "[FC]" if self.propagation == "forward_checking" else "[MIỀN]"
            )
            text = (
                f"Ô {self._cell_text(event.cell)}: "
                f"{self._set_text(event.before)} → {self._set_text(event.after)}"
            )
            if removed:
                text += f" (loại {self._set_text(removed)})"
            if event.run_id:
                text += f" · dãy {event.run_id}"
            self._add_event(label, text, COLORS["accent"])
        elif event.kind == "variable_selected" and event.cell is not None:
            domain = self.domains.get(event.cell, set())
            label = "[MRV]" if self.use_mrv else "[CHỌN BIẾN]"
            if self.use_mrv and self.use_degree:
                label = "[MRV / DEGREE]"
            self._add_event(
                label,
                f"Chọn ô {self._cell_text(event.cell)}, miền có {len(domain)} giá trị.",
                COLORS["accent"],
            )
        elif event.kind == "assignment" and event.cell is not None and event.value is not None:
            self.assignments[event.cell] = event.value
            self._add_event(
                "[GÁN]",
                f"Thử gán ô {self._cell_text(event.cell)} = {event.value}.",
                COLORS["orange"],
            )
        elif event.kind == "contradiction":
            detail = f"Mâu thuẫn ở dãy {event.run_id}" if event.run_id else "Mâu thuẫn khi kiểm tra phép gán."
            if event.cell is not None:
                detail += f", ô {self._cell_text(event.cell)}."
            else:
                detail += "."
            self._add_event("[MÂU THUẪN]", detail, COLORS["red"])
        elif event.kind == "backtrack":
            if event.cell is not None:
                if self._decision_frames:
                    frame_cell, marker = self._decision_frames.pop()
                    if frame_cell == event.cell:
                        while len(self._domain_undo) > marker:
                            cell, old_domain = self._domain_undo.pop()
                            self.domains[cell] = old_domain
                            self._last_removed[cell] = set()
                if event.cell not in self.board.givens:
                    self.assignments.pop(event.cell, None)
                self._add_event(
                    "[QUAY LUI]",
                    f"Hủy lựa chọn tại ô {self._cell_text(event.cell)}"
                    + (f" = {event.value}." if event.value is not None else "."),
                    COLORS["orange"],
                )
            else:
                self._add_event("[QUAY LUI]", "Solver quay lui để thử nhánh khác.", COLORS["orange"])
        elif event.kind == "solution_found":
            self._add_event("[NGHIỆM]", "Phép gán thỏa mãn mọi dãy Kakuro.", COLORS["green"])
        elif event.kind == "search_failed":
            self._add_event("[KẾT THÚC]", "Không có nghiệm thỏa các ràng buộc của bảng.", COLORS["red"])
        else:
            self._add_event(f"[{event.kind.upper()}]", event.message, COLORS["muted"])

        self.status_detail = f"Đã phát {self._event_count} sự kiện solver."

    def _add_event(self, tag: str, message: str, color: Color) -> None:
        self._event_lines.append((f"{tag} {message}", color))
        if len(self._event_lines) > 2000:
            self._event_lines = self._event_lines[-2000:]

    @staticmethod
    def _cell_text(cell: Cell) -> str:
        return f"({cell[0] + 1},{cell[1] + 1})"

    @staticmethod
    def _set_text(values: Iterable[int]) -> str:
        return "{" + ", ".join(str(value) for value in sorted(values)) + "}"

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            if self._control is not None:
                self._control.cancel()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.return_to_menu = True
                self.running = False
                if self._control is not None:
                    self._control.cancel()
            elif event.key == pygame.K_SPACE:
                self.toggle_pause()
            elif event.key == pygame.K_RIGHT:
                self.step()
            elif event.key == pygame.K_r:
                self.reset()

        if event.type == pygame.MOUSEWHEEL:
            event_rect = pygame.Rect(PANEL_X + 16, 300, PANEL_WIDTH - 32, 272)
            if event_rect.collidepoint(pygame.mouse.get_pos()):
                self._event_scroll = max(
                    0, min(len(self._event_lines), self._event_scroll + event.y * 3)
                )

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_speed = False
        if event.type == pygame.MOUSEMOTION and self.dragging_speed:
            self._set_speed_from_mouse(event.pos[0])

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos
        if self.mode_rect.collidepoint(pos):
            self.return_to_menu = True
            self.running = False
            if self._control is not None:
                self._control.cancel()
        elif self.speed_track.inflate(24, 30).collidepoint(pos):
            self.dragging_speed = True
            self._set_speed_from_mouse(pos[0])
        elif self.propagation_rect.collidepoint(pos):
            if self._solver_is_active():
                return
            choices = ("gac", "forward_checking", "none")
            self.propagation = choices[(choices.index(self.propagation) + 1) % len(choices)]
        elif pygame.Rect(28, self.mrv_rect.y - 6, 194, 44).collidepoint(pos):
            if self._solver_is_active():
                return
            self.use_mrv = not self.use_mrv
        elif pygame.Rect(28, self.degree_rect.y - 6, 194, 44).collidepoint(pos):
            if self._solver_is_active():
                return
            self.use_degree = not self.use_degree
        elif pygame.Rect(28, self.lcv_rect.y - 6, 194, 44).collidepoint(pos):
            if self._solver_is_active():
                return
            self.use_lcv = not self.use_lcv
        elif self.start_rect.collidepoint(pos):
            self.start()
        elif self.pause_rect.collidepoint(pos):
            self.toggle_pause()
        elif self.step_rect.collidepoint(pos):
            self.step()
        elif self.reset_rect.collidepoint(pos):
            self.reset()
        else:
            cell = self._cell_at(pos)
            if cell in self.white_cells:
                self.selected_cell = cell

    def _set_speed_from_mouse(self, mouse_x: int) -> None:
        fraction = (mouse_x - self.speed_track.left) / self.speed_track.width
        self.speed = round(0.5 + max(0.0, min(1.0, fraction)) * 29.5, 1)

    def _solver_is_active(self) -> bool:
        return (
            (self._worker is not None and self._worker.is_alive())
            or self._deferred_message is not None
            or not self._messages.empty()
            or self.status in {"Đang giải", "Đã tạm dừng", "Đang chạy từng bước"}
        )

    def _cell_at(self, pos: Tuple[int, int]) -> Optional[Cell]:
        x, y = pos
        col = (x - GRID_X) // CELL_SIZE
        row = (y - GRID_Y) // CELL_SIZE
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return int(row), int(col)
        return None

    def _draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: Color,
        font: Optional[pygame.font.Font] = None,
    ) -> pygame.Rect:
        surface = (font or self.font).render(text, True, color)
        rect = surface.get_rect(topleft=(x, y))
        self.screen.blit(surface, rect)
        return rect

    def _draw(self) -> None:
        self.screen.fill(COLORS["background"])
        pygame.draw.rect(self.screen, COLORS["sidebar"], (0, 0, 248, WINDOW_HEIGHT))
        self._draw_header()
        self._draw_sidebar()
        self._draw_board()
        self._draw_right_panel()
        self._draw_controls()
        pygame.display.flip()

    def _draw_header(self) -> None:
        self._draw_text("KAKURO", 28, 28, COLORS["accent"], self.small_font)
        self._draw_text("CSP Solver Lab", 28, 48, COLORS["text"], self.title_font)
        self._draw_text("TRỰC QUAN HÓA RÀNG BUỘC", 276, 45, COLORS["muted"], self.small_font)
        self._draw_button(self.mode_rect, "← Chọn chế độ", COLORS["panel_alt"])
        status_color = COLORS["green"] if self._solution is not None else (
            COLORS["red"] if self.error_message or self.status == "Không tìm thấy nghiệm"
            else COLORS["accent"]
        )
        status_rect = pygame.Rect(1170, 36, 238, 38)
        pygame.draw.rect(self.screen, COLORS["panel"], status_rect, border_radius=18)
        pygame.draw.circle(self.screen, status_color, (1190, 55), 5)
        self._draw_text(self.status, 1203, 45, COLORS["text"], self.small_font)

    def _draw_sidebar(self) -> None:
        self._draw_text("CẤU HÌNH", 28, 126, COLORS["muted"], self.small_font)
        self._draw_text("Thuật toán", 28, 154, COLORS["text"], self.heading_font)
        self._draw_text("Propagation", 30, 204, COLORS["muted"], self.small_font)
        pygame.draw.rect(self.screen, COLORS["panel_alt"], self.propagation_rect, border_radius=9)
        pygame.draw.rect(self.screen, COLORS["border"], self.propagation_rect, 1, border_radius=9)
        label = {"gac": "GAC", "forward_checking": "Forward Checking", "none": "None"}[
            self.propagation
        ]
        self._draw_text(label, 43, 242, COLORS["text"], self.font)
        self._draw_text("Heuristics", 30, 281, COLORS["muted"], self.small_font)
        for rect, enabled, title, subtitle in (
            (self.mrv_rect, self.use_mrv, "MRV", "Miền nhỏ nhất trước"),
            (self.degree_rect, self.use_degree, "Degree", "Ưu tiên nhiều láng giềng"),
            (self.lcv_rect, self.use_lcv, "LCV", "Ít hạn chế miền nhất"),
        ):
            pygame.draw.rect(
                self.screen,
                COLORS["accent"] if enabled else COLORS["panel_alt"],
                rect,
                border_radius=5,
            )
            pygame.draw.rect(self.screen, COLORS["border"], rect, 1, border_radius=5)
            if enabled:
                self._draw_text("✓", rect.x + 4, rect.y + 1, COLORS["background"], self.font)
            self._draw_text(title, 66, rect.y - 3, COLORS["text"], self.font)
            self._draw_text(subtitle, 66, rect.y + 20, COLORS["muted"], self.tiny_font)
        pygame.draw.line(self.screen, COLORS["border"], (28, 460), (220, 460), 1)
        self._draw_text("MÔ HÌNH CSP", 28, 482, COLORS["muted"], self.small_font)
        self._draw_text(f"{len(self.board.cells)} biến", 28, 516, COLORS["text"], self.font)
        self._draw_text(f"{len(self.board.runs)} dãy ràng buộc", 28, 543, COLORS["text"], self.font)
        self._draw_text("Mỗi ô trắng là một biến.", 28, 590, COLORS["muted"], self.small_font)
        self._draw_text("Mỗi dãy có tổng và các số", 28, 611, COLORS["muted"], self.small_font)
        self._draw_text("không lặp lại.", 28, 631, COLORS["muted"], self.small_font)
        self._draw_text("BÀI 08 · CONSTRAINT", 28, 705, COLORS["accent"], self.tiny_font)
        self._draw_text("SATISFACTION PROBLEMS", 28, 723, COLORS["muted"], self.tiny_font)

    def _draw_board(self) -> None:
        grid_rect = pygame.Rect(GRID_X - 4, GRID_Y - 4, GRID_SIZE * CELL_SIZE + 8, GRID_SIZE * CELL_SIZE + 8)
        pygame.draw.rect(self.screen, COLORS["panel"], grid_rect, border_radius=11)
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cell = (row, col)
                x = GRID_X + col * CELL_SIZE
                y = GRID_Y + row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                if cell in self.white_cells:
                    self._draw_white_cell(cell, rect)
                elif cell in self.clues:
                    self._draw_clue_cell(cell, rect)
                else:
                    pygame.draw.rect(self.screen, COLORS["empty_cell"], rect)
                    pygame.draw.rect(self.screen, COLORS["border"], rect, 1)

    def _draw_white_cell(self, cell: Cell, rect: pygame.Rect) -> None:
        is_active = cell == self.active_cell
        is_selected = cell == self.selected_cell
        is_conflict = cell in self.highlighted_run and self._last_event_kind == "contradiction"
        fill = (255, 225, 222) if is_conflict else COLORS["white_cell"]
        pygame.draw.rect(self.screen, fill, rect)
        pygame.draw.rect(
            self.screen,
            COLORS["red"] if is_conflict else (
                COLORS["accent"] if is_active or is_selected else COLORS["border"]
            ),
            rect,
            3 if is_active or is_selected or is_conflict else 1,
        )
        if cell in self.assignments:
            text = self.cell_font.render(str(self.assignments[cell]), True, COLORS["white_text"])
            self.screen.blit(text, text.get_rect(center=(rect.centerx, rect.centery + 1)))
            if cell not in self.board.givens:
                pygame.draw.circle(
                    self.screen, COLORS["green"], (rect.right - 8, rect.top + 8), 3
                )
        else:
            self._draw_text(
                f"{cell[0] + 1},{cell[1] + 1}",
                rect.x + 4,
                rect.y + 3,
                (112, 128, 150),
                self.tiny_font,
            )
            domain = self.domains.get(cell, set())
            if len(domain) < 9:
                self._draw_text(
                    f"|D|={len(domain)}",
                    rect.x + 4,
                    rect.bottom - 15,
                    COLORS["accent_dark"],
                    self.tiny_font,
                )

    def _draw_clue_cell(self, cell: Cell, rect: pygame.Rect) -> None:
        clue = self.clues[cell]
        pygame.draw.rect(self.screen, COLORS["black_cell"], rect)
        pygame.draw.line(
            self.screen,
            COLORS["border"],
            (rect.left + 2, rect.bottom - 2),
            (rect.right - 2, rect.top + 2),
            2,
        )
        if "across" in clue:
            self._draw_text(
                str(clue["across"]),
                rect.x + 5,
                rect.y + 4,
                COLORS["clue_across"],
                self.clue_font,
            )
        if "down" in clue:
            text = self.clue_font.render(str(clue["down"]), True, COLORS["clue_down"])
            self.screen.blit(text, text.get_rect(bottomright=(rect.right - 5, rect.bottom - 4)))
        pygame.draw.rect(self.screen, COLORS["border"], rect, 1)

    def _draw_right_panel(self) -> None:
        self._draw_panel((PANEL_X, 126, PANEL_WIDTH, 154), "MIỀN GIÁ TRỊ")
        cell = self.selected_cell or self.active_cell
        if cell is None:
            domain_label = "Chọn một ô trắng để xem miền."
        else:
            domain = self.domains.get(cell, set())
            domain_label = f"Ô {self._cell_text(cell)}  ·  {len(domain)} giá trị"
        self._draw_text(domain_label, PANEL_X + 18, 163, COLORS["muted"], self.small_font)
        self._draw_domain_chips(cell, PANEL_X + 18, 190)
        self._draw_text("Đỏ = giá trị đã bị loại gần nhất", PANEL_X + 18, 244, COLORS["muted"], self.tiny_font)

        self._draw_panel((PANEL_X, 294, PANEL_WIDTH, 278), "SOLVER EVENTS")
        if not self._event_lines:
            self._draw_text(
                "Các sự kiện thật từ SolverEvent sẽ xuất hiện ở đây.",
                PANEL_X + 18,
                336,
                COLORS["muted"],
                self.small_font,
            )
        else:
            self._draw_event_log()

        self._draw_panel((PANEL_X, 586, PANEL_WIDTH, 158), "THỐNG KÊ SOLVER")
        self._draw_stats()

    def _draw_panel(self, rect_tuple: Tuple[int, int, int, int], title: str) -> None:
        rect = pygame.Rect(rect_tuple)
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=12)
        pygame.draw.rect(self.screen, COLORS["border"], rect, 1, border_radius=12)
        self._draw_text(title, rect.x + 17, rect.y + 13, COLORS["muted"], self.small_font)

    def _draw_domain_chips(self, cell: Optional[Cell], x: int, y: int) -> None:
        if cell is None:
            return
        current = self.domains.get(cell, set())
        removed = self._last_removed.get(cell, set())
        for value in range(1, 10):
            rect = pygame.Rect(x + (value - 1) * 58, y, 48, 38)
            color = COLORS["accent_dark"] if value in current else COLORS["panel_alt"]
            text_color = COLORS["text"] if value in current else COLORS["muted"]
            pygame.draw.rect(self.screen, color, rect, border_radius=7)
            if value in removed and value not in current:
                pygame.draw.line(self.screen, COLORS["domain_removed"], (rect.x + 7, rect.centery), (rect.right - 7, rect.centery), 2)
            self._draw_text(str(value), rect.x + 18, rect.y + 8, text_color, self.font)

    def _draw_event_log(self) -> None:
        area = pygame.Rect(PANEL_X + 16, 330, PANEL_WIDTH - 32, 226)
        clip = self.screen.get_clip()
        self.screen.set_clip(area)
        visible: List[Tuple[str, Color]] = []
        y = area.y
        line_height = 22
        max_lines = area.height // line_height
        end = max(0, len(self._event_lines) - self._event_scroll)
        start = max(0, end - max_lines)
        visible = self._event_lines[start:end]
        for text, color in visible:
            wrapped = self._wrap_text(text, area.width - 6, self.small_font)
            for line in wrapped:
                if y + line_height > area.bottom:
                    break
                self._draw_text(line, area.x + 3, y, color, self.small_font)
                y += line_height
        self.screen.set_clip(clip)

    def _wrap_text(self, text: str, width: int, font: pygame.font.Font) -> List[str]:
        words = text.split()
        lines: List[str] = []
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def _draw_stats(self) -> None:
        labels = (
            ("Thời gian", "elapsed_ms", "ms"),
            ("Nodes mở rộng", "expanded_nodes", ""),
            ("Lần thử gán", "assignments_tried", ""),
            ("Quay lui", "backtrack_count", ""),
            ("Propagation calls", "propagation_calls", ""),
            ("Giá trị bị loại", "domain_values_removed", ""),
            ("Mâu thuẫn", "contradictions", ""),
            ("Số nghiệm", "solutions_found", ""),
        )
        for index, (label, key, unit) in enumerate(labels):
            col = index % 2
            row = index // 2
            x = PANEL_X + 18 + col * 280
            y = 624 + row * 28
            value = "—" if self._stats is None else str(self._stats.get(key, "—"))
            if key == "elapsed_ms" and self._stats is not None:
                value = f"{float(self._stats.get(key, 0)):.3f}"
            self._draw_text(label, x, y, COLORS["muted"], self.tiny_font)
            self._draw_text(f"{value} {unit}".rstrip(), x + 143, y - 2, COLORS["text"], self.small_font)

    def _draw_controls(self) -> None:
        pygame.draw.rect(self.screen, COLORS["sidebar"], (248, 766, WINDOW_WIDTH - 248, 134))
        pygame.draw.line(self.screen, COLORS["border"], (248, 766), (WINDOW_WIDTH, 766), 1)
        self._draw_button(self.start_rect, "Bắt đầu", COLORS["accent_dark"])
        self._draw_button(
            self.pause_rect,
            "Tiếp tục" if self.paused and self.status == "Đã tạm dừng" else "Tạm dừng",
            COLORS["panel_alt"],
        )
        self._draw_button(self.step_rect, "Bước  →", COLORS["panel_alt"])
        self._draw_button(self.reset_rect, "Đặt lại", COLORS["panel_alt"])
        self._draw_text("TỐC ĐỘ SỰ KIỆN", 805, 786, COLORS["muted"], self.tiny_font)
        pygame.draw.rect(self.screen, COLORS["border"], self.speed_track, border_radius=4)
        fraction = (self.speed - 0.5) / 29.5
        fill_width = int(self.speed_track.width * fraction)
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            pygame.Rect(self.speed_track.x, self.speed_track.y, fill_width, self.speed_track.height),
            border_radius=4,
        )
        self.speed_handle.center = (self.speed_track.x + fill_width, self.speed_track.centery)
        pygame.draw.rect(self.screen, COLORS["text"], self.speed_handle, border_radius=6)
        self._draw_text(f"{self.speed:g} sự kiện/giây", 1145, 801, COLORS["text"], self.small_font)
        self._draw_text("Phím tắt: Space tạm dừng · → bước · R đặt lại", 805, 835, COLORS["muted"], self.tiny_font)
        if self.error_message:
            self._draw_text("Chi tiết lỗi: " + self.error_message[:70], 276, 744, COLORS["red"], self.tiny_font)
        else:
            self._draw_text(self.status_detail[:96], 276, 744, COLORS["muted"], self.tiny_font)

    def _draw_button(self, rect: pygame.Rect, label: str, color: Color) -> None:
        pygame.draw.rect(self.screen, color, rect, border_radius=9)
        pygame.draw.rect(self.screen, COLORS["border"], rect, 1, border_radius=9)
        text = self.font.render(label, True, COLORS["text"])
        self.screen.blit(text, text.get_rect(center=rect.center))

    def run(self) -> bool:
        while self.running:
            self.clock.tick(60)
            for event in pygame.event.get():
                self._handle_event(event)
            self._release_playback_event()
            self._poll_messages()
            self._draw()
        if self._control is not None:
            self._control.cancel()
        return self.return_to_menu


def main() -> None:
    from main import main as application_main

    application_main()


if __name__ == "__main__":
    main()
