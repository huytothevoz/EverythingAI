"""Main menu and entry point for the Kakuro CSP project."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import pygame

from kakuro_game import KakuroPlayGUI
from kakuro_gui import COLORS, KakuroGUI


def _initial_window_size(
    desired_size: Tuple[int, int],
    margins: Tuple[int, int] = (32, 96),
) -> Tuple[int, int]:
    """Choose a startup size that leaves room for desktop borders and taskbars."""
    desktop_sizes = pygame.display.get_desktop_sizes()
    if desktop_sizes:
        desktop_width, desktop_height = desktop_sizes[0]
    else:
        display_info = pygame.display.Info()
        desktop_width, desktop_height = display_info.current_w, display_info.current_h

    return (
        min(desired_size[0], max(1, desktop_width - margins[0])),
        min(desired_size[1], max(1, desktop_height - margins[1])),
    )


class MainMenu:
    """Resizable application menu with game, solver, help, and project pages."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("KAKURO — CSP PUZZLE SOLVER")
        self.screen = pygame.display.set_mode(
            _initial_window_size((960, 720)), pygame.RESIZABLE
        )
        self.clock = pygame.time.Clock()
        self.running = True
        self.page = "menu"
        self.choice: Optional[str] = None
        self.font = pygame.font.SysFont("segoeui", 20)
        self.body_font = pygame.font.SysFont("segoeui", 17)
        self.small_font = pygame.font.SysFont("segoeui", 14)
        self.title_font = pygame.font.SysFont("segoeui", 39, bold=True)
        self.subtitle_font = pygame.font.SysFont("segoeui", 18)
        self.buttons: Dict[str, pygame.Rect] = {}
        self.back_button = pygame.Rect(30, 30, 120, 42)
        self._layout()

    def _layout(self) -> None:
        width, height = self.screen.get_size()
        button_width = min(390, max(260, width - 100))
        button_height = 54
        gap = 14
        total_height = 5 * button_height + 4 * gap
        start_y = max(235, (height - total_height) // 2 + 35)
        self.buttons = {
            name: pygame.Rect(
                (width - button_width) // 2,
                start_y + index * (button_height + gap),
                button_width,
                button_height,
            )
            for index, name in enumerate(("play", "solve", "how", "about", "exit"))
        }

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.choice = "exit"
            self.running = False
            return
        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            self._layout()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.page != "menu":
                self.page = "menu"
            else:
                self.choice = "exit"
                self.running = False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.page != "menu":
            if self.back_button.collidepoint(event.pos):
                self.page = "menu"
            return
        for name, rect in self.buttons.items():
            if not rect.collidepoint(event.pos):
                continue
            if name in {"play", "solve", "exit"}:
                self.choice = name
                self.running = False
            else:
                self.page = name
            return

    def _draw_text(
        self,
        text: str,
        position: Tuple[int, int],
        color: Tuple[int, int, int],
        font: Optional[pygame.font.Font] = None,
    ) -> pygame.Rect:
        surface = (font or self.body_font).render(text, True, color)
        rect = surface.get_rect(topleft=position)
        self.screen.blit(surface, rect)
        return rect

    def _draw(self) -> None:
        width = self.screen.get_width()
        self._layout()
        self.screen.fill(COLORS["background"])
        if self.page == "menu":
            self._draw_menu(width)
        else:
            self._draw_info_page(width)
        pygame.display.flip()

    def _draw_menu(self, width: int) -> None:
        title = self.title_font.render("KAKURO", True, COLORS["text"])
        self.screen.blit(title, title.get_rect(center=(width // 2, 95)))
        subtitle = self.subtitle_font.render(
            "CSP PUZZLE SOLVER", True, COLORS["accent"]
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(width // 2, 140)))
        description = self.small_font.render(
            "503043 · Introduction to Artificial Intelligence",
            True,
            COLORS["muted"],
        )
        self.screen.blit(description, description.get_rect(center=(width // 2, 181)))

        labels = {
            "play": ("Play Game", COLORS["accent_dark"]),
            "solve": ("AI Solver", COLORS["panel_alt"]),
            "how": ("How to Play", COLORS["panel_alt"]),
            "about": ("About Project", COLORS["panel_alt"]),
            "exit": ("Exit", COLORS["panel_alt"]),
        }
        for name, rect in self.buttons.items():
            label, color = labels[name]
            self._draw_button(rect, label, color)

    def _draw_info_page(self, width: int) -> None:
        self._draw_button(self.back_button, "← Main Menu", COLORS["panel_alt"])
        if self.page == "how":
            title = "How to Play"
            lines = [
                "Fill every white square with a digit from 1 to 9.",
                "Digits cannot repeat within a horizontal or vertical run.",
                "The run total must match its clue when all its cells are filled.",
                "",
                "Play Game: click a white cell and press 1–9 to enter a digit.",
                "Use arrow keys to move; Backspace/Delete clears a cell.",
                "Press N for pencil notes. Check, Hint, Undo and Restart",
                "are available in the toolbar. Escape returns to the menu.",
                "",
                "AI Solver visualizes CSP events. Start, Pause/Resume and Step",
                "control the playback; Reset restarts the current solve.",
            ]
        else:
            title = "About Project"
            lines = [
                "KAKURO — CSP PUZZLE SOLVER",
                "503043 · Introduction to Artificial Intelligence",
                "",
                "The backend models white cells as Variables, digits 1–9 as",
                "Domains, and Kakuro runs as sum/all-different Constraints.",
                "",
                "AI Solver uses the existing backtracking CSP solver with",
                "GAC or Forward Checking and optional MRV, Degree and LCV.",
                "Play Game is independent: it checks player entries and does",
                "not invoke the solver or reveal a complete solution.",
                "",
                "Puzzle data is loaded from boards.py.",
            ]

        title_surface = self.title_font.render(title, True, COLORS["text"])
        self.screen.blit(
            title_surface,
            title_surface.get_rect(center=(width // 2, 145)),
        )
        max_width = max(300, width - 100)
        y = 220
        for text in lines:
            if not text:
                y += 14
                continue
            wrapped = self._wrap_text(text, max_width)
            for line in wrapped:
                self._draw_text(line, (50, y), COLORS["muted"], self.body_font)
                y += 31

    def _wrap_text(self, text: str, width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if self.body_font.size(candidate)[0] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def _draw_button(
        self,
        rect: pygame.Rect,
        label: str,
        color: Tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["border"], rect, 1, border_radius=10)
        text = self.font.render(label, True, COLORS["text"])
        self.screen.blit(text, text.get_rect(center=rect.center))

    def run(self) -> Optional[str]:
        while self.running:
            self.clock.tick(60)
            for event in pygame.event.get():
                self._handle_event(event)
            self._draw()
        return self.choice


def main() -> None:
    while True:
        choice = MainMenu().run()
        if choice == "play":
            return_to_menu = KakuroPlayGUI().run()
        elif choice == "solve":
            return_to_menu = KakuroGUI().run()
        else:
            break
        if not return_to_menu:
            break
    pygame.quit()


if __name__ == "__main__":
    main()
