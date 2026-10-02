from __future__ import annotations

import os
import sys
from typing import Optional, Tuple

import pygame

# Thêm root project vào sys.path khi chạy trực tiếp menu_ui.py.
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from Ex5.ui_components import AssetManager, Theme, ensure_native_window_chrome


class VisualMenuUI:
    CARD_SINGLE = (76, 135, 244)
    CARD_COMP = (92, 181, 112)
    CARD_BORDER = (255, 255, 255)
    DARK = (38, 47, 62)
    LIGHT_TEXT = (248, 250, 255)
    MUTED = (102, 113, 132)

    def __init__(self) -> None:
        pygame.init()

        # Chọn kích thước ban đầu vừa màn hình thay vì cố định cứng.
        info = pygame.display.Info()
        screen_w = info.current_w or 1280
        screen_h = info.current_h or 800
        initial_w = min(1180, max(760, int(screen_w * 0.78)))
        initial_h = min(820, max(620, int(screen_h * 0.78)))

        self.screen = pygame.display.set_mode((initial_w, initial_h), pygame.RESIZABLE)
        pygame.display.set_caption("Office Sokoban - Game Menu")
        ensure_native_window_chrome()

        self.clock = pygame.time.Clock()
        self.assets = AssetManager()
        self.window_w, self.window_h = self.screen.get_size()

        # State hover để tạo hiệu ứng card nổi lên nhẹ.
        self.hover_mode: Optional[str] = None
        self._recalculate_layout(self.window_w, self.window_h)

    # P1 - Reponsive
    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _init_fonts(self) -> None:
        """Scale font theo cửa sổ để menu không bị tràn chữ khi resize."""
        scale = self._clamp(min(self.window_w / 1180, self.window_h / 820), 0.68, 1.18)
        self.ui_scale = scale

        self.font_title = pygame.font.SysFont("Segoe UI", max(25, int(40 * scale)), bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", max(14, int(18 * scale)))
        self.font_card_title = pygame.font.SysFont("Segoe UI", max(22, int(31 * scale)), bold=True)
        self.font_card_subtitle = pygame.font.SysFont("Segoe UI", max(13, int(17 * scale)), bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", max(12, int(15 * scale)))
        self.font_button = pygame.font.SysFont("Segoe UI", max(15, int(18 * scale)), bold=True)
        self.font_badge = pygame.font.SysFont("Segoe UI", max(11, int(13 * scale)), bold=True)

    def _recalculate_layout(self, width: int, height: int, recreate_window: bool = True) -> None:
        """Tính lại vị trí card khi cửa sổ full, normal hoặc snap nửa màn hình."""
        # Không ép window quay về size lớn; chỉ giữ mức tối thiểu đủ dùng.
        self.window_w = max(560, int(width))
        self.window_h = max(500, int(height))

        if recreate_window:
            self.screen = pygame.display.set_mode(
                (self.window_w, self.window_h),
                pygame.RESIZABLE,
            )
            ensure_native_window_chrome()

        self._init_fonts()

        margin = max(18, int(30 * self.ui_scale))
        self.margin = margin
        header_h = max(92, int(112 * self.ui_scale))
        footer_h = max(44, int(56 * self.ui_scale))

        self.header_rect = pygame.Rect(
            margin,
            margin,
            self.window_w - 2 * margin,
            header_h,
        )
        self.footer_rect = pygame.Rect(
            margin,
            self.window_h - footer_h - margin,
            self.window_w - 2 * margin,
            footer_h,
        )

        content_top = self.header_rect.bottom + margin
        content_bottom = self.footer_rect.top - margin
        content_h = max(250, content_bottom - content_top)
        content_w = self.window_w - 2 * margin

        # Window rộng -> 2 card ngang. Window hẹp -> 2 card xếp dọc.
        self.horizontal_cards = self.window_w >= 820
        card_gap = max(16, int(24 * self.ui_scale))

        if self.horizontal_cards:
            card_w = (content_w - card_gap) // 2
            card_h = content_h
            self.single_card = pygame.Rect(margin, content_top, card_w, card_h)
            self.comp_card = pygame.Rect(margin + card_w + card_gap, content_top, card_w, card_h)
        else:
            card_h = (content_h - card_gap) // 2
            self.single_card = pygame.Rect(margin, content_top, content_w, card_h)
            self.comp_card = pygame.Rect(margin, content_top + card_h + card_gap, content_w, card_h)


    # P2 - Hàm vẽ chung
    def _draw_background(self) -> None:
        """Reuse background voxel từ bộ asset của Task 5 / Task 8."""
        bg = self.assets.get_scaled("background", (self.window_w, self.window_h))
        self.screen.blit(bg, (0, 0))

        # Lớp tối nhẹ giúp card trắng/colored nổi lên rõ hơn.
        shade = pygame.Surface((self.window_w, self.window_h), pygame.SRCALPHA)
        shade.fill((24, 39, 61, 48))
        self.screen.blit(shade, (0, 0))

    def _draw_header(self) -> None:
        """Header của launcher; không lặp header Task 5 / Task 8."""
        shadow = self.header_rect.move(0, 5)
        pygame.draw.rect(self.screen, (0, 0, 0, 42), shadow, border_radius=24)
        pygame.draw.rect(self.screen, (255, 255, 255), self.header_rect, border_radius=24)
        pygame.draw.rect(self.screen, (217, 227, 239), self.header_rect, width=2, border_radius=24)

        title = self.font_title.render("OFFICE SOKOBAN", True, self.DARK)
        subtitle = self.font_subtitle.render(
            "Choose a game mode - AI Search & Competitive Agents",
            True,
            self.MUTED,
        )

        title_x = self.header_rect.x + max(18, int(26 * self.ui_scale))
        title_y = self.header_rect.y + max(10, int(16 * self.ui_scale))
        self.screen.blit(title, (title_x, title_y))

        # Chỉ vẽ subtitle nếu chiều ngang đủ; window hẹp thì ưu tiên title.
        if subtitle.get_width() <= self.header_rect.width - 2 * (title_x - self.header_rect.x):
            self.screen.blit(subtitle, (title_x, title_y + title.get_height() + 3))

    def _fit_image(self, key: str, rect: pygame.Rect, max_ratio: float = 0.48) -> pygame.Surface:
        """Scale agent theo card mà không làm méo ảnh."""
        max_side = max(56, int(min(rect.width, rect.height) * max_ratio))
        return self.assets.get_scaled(key, (max_side, max_side))

    def _draw_mode_card(
        self,
        rect: pygame.Rect,
        mode: str,
        title: str,
        subtitle: str,
        description: str,
        color: Tuple[int, int, int],
        agent_keys: Tuple[str, ...],
        badges: Tuple[str, ...],
    ) -> None:
        """Vẽ một card mode. Click toàn card đều mở game."""
        hovered = self.hover_mode == mode
        lift = max(2, int(5 * self.ui_scale)) if hovered else 0
        draw_rect = rect.move(0, -lift)

        shadow = rect.move(0, max(5, int(8 * self.ui_scale)))
        pygame.draw.rect(self.screen, (0, 0, 0, 60), shadow, border_radius=26)

        # Card dùng trắng mờ + accent màu ở trên để nhìn hiện đại nhưng dễ đọc.
        pygame.draw.rect(self.screen, (250, 252, 255), draw_rect, border_radius=26)
        pygame.draw.rect(
            self.screen,
            color if hovered else (220, 229, 240),
            draw_rect,
            width=max(2, int(3 * self.ui_scale)),
            border_radius=26,
        )

        accent_h = max(8, int(11 * self.ui_scale))
        accent = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, accent_h)
        pygame.draw.rect(self.screen, color, accent, border_radius=26)

        pad = max(14, int(22 * self.ui_scale))

        # Ảnh nhân vật nằm ở nửa trên của card.
        if len(agent_keys) == 1:
            img = self._fit_image(agent_keys[0], draw_rect)
            image_y = draw_rect.y + accent_h + max(8, int(12 * self.ui_scale))
            self.screen.blit(img, img.get_rect(center=(draw_rect.centerx, image_y + img.get_height() // 2)))
            text_start_y = image_y + img.get_height() + max(4, int(8 * self.ui_scale))
        else:
            max_side = max(50, int(min(draw_rect.width, draw_rect.height) * 0.36))
            img1 = self.assets.get_scaled(agent_keys[0], (max_side, max_side))
            img2 = self.assets.get_scaled(agent_keys[1], (max_side, max_side))
            image_y = draw_rect.y + accent_h + max(6, int(10 * self.ui_scale))
            gap = max(4, int(8 * self.ui_scale))
            total_w = img1.get_width() + img2.get_width() + gap
            start_x = draw_rect.centerx - total_w // 2
            self.screen.blit(img1, (start_x, image_y))
            self.screen.blit(img2, (start_x + img1.get_width() + gap, image_y))
            text_start_y = image_y + max_side + max(4, int(8 * self.ui_scale))

        # Với window thấp, giảm khoảng cách để text không rớt khỏi card.
        if draw_rect.height < 330:
            text_start_y = min(text_start_y, draw_rect.y + int(draw_rect.height * 0.50))

        title_surface = self.font_card_title.render(title, True, self.DARK)
        subtitle_surface = self.font_card_subtitle.render(subtitle, True, color)
        desc_surface = self.font_body.render(description, True, self.MUTED)

        self.screen.blit(title_surface, title_surface.get_rect(center=(draw_rect.centerx, text_start_y)))
        self.screen.blit(
            subtitle_surface,
            subtitle_surface.get_rect(center=(draw_rect.centerx, text_start_y + title_surface.get_height() + 6)),
        )

        desc_y = text_start_y + title_surface.get_height() + subtitle_surface.get_height() + 14
        if desc_y + desc_surface.get_height() < draw_rect.bottom - 78:
            self.screen.blit(desc_surface, desc_surface.get_rect(center=(draw_rect.centerx, desc_y)))

        # Badges giúp người dùng nhìn nhanh thuật toán của mode.
        badge_y = min(draw_rect.bottom - 70, desc_y + desc_surface.get_height() + 16)
        badge_surfaces = []
        for badge in badges:
            t = self.font_badge.render(badge, True, self.DARK)
            w = t.get_width() + 18
            h = t.get_height() + 9
            badge_surfaces.append((t, w, h))

        total_badge_w = sum(item[1] for item in badge_surfaces) + max(0, len(badge_surfaces) - 1) * 8
        bx = draw_rect.centerx - total_badge_w // 2
        for text_surface, bw, bh in badge_surfaces:
            badge_rect = pygame.Rect(bx, badge_y, bw, bh)
            pygame.draw.rect(self.screen, (240, 244, 249), badge_rect, border_radius=12)
            pygame.draw.rect(self.screen, (218, 226, 237), badge_rect, width=1, border_radius=12)
            self.screen.blit(text_surface, text_surface.get_rect(center=badge_rect.center))
            bx += bw + 8

        # Nút PLAY ở đáy card; click card hay nút đều dùng cùng mode.
        button_w = min(max(140, int(190 * self.ui_scale)), draw_rect.width - 2 * pad)
        button_h = max(38, int(46 * self.ui_scale))
        button_rect = pygame.Rect(0, 0, button_w, button_h)
        button_rect.centerx = draw_rect.centerx
        button_rect.bottom = draw_rect.bottom - max(12, int(18 * self.ui_scale))
        pygame.draw.rect(self.screen, color, button_rect, border_radius=15)
        pygame.draw.rect(self.screen, self.CARD_BORDER, button_rect, width=2, border_radius=15)
        play = self.font_button.render("PLAY", True, self.LIGHT_TEXT)
        self.screen.blit(play, play.get_rect(center=button_rect.center))

    def _draw_footer(self) -> None:
        pygame.draw.rect(self.screen, (255, 255, 255), self.footer_rect, border_radius=18)
        pygame.draw.rect(self.screen, (217, 227, 239), self.footer_rect, width=1, border_radius=18)
        text = "Click a mode  |  Keyboard: 1 = Single Agent, 2 = Competitive, ESC = Exit"
        surface = self.font_body.render(text, True, self.MUTED)

        # Tránh text tràn footer khi cửa sổ hẹp.
        if surface.get_width() > self.footer_rect.width - 24:
            text = "1: Single Agent   |   2: Competitive   |   ESC: Exit"
            surface = self.font_body.render(text, True, self.MUTED)

        self.screen.blit(surface, surface.get_rect(center=self.footer_rect.center))

    def draw_frame(self) -> None:
        self._draw_background()
        self._draw_header()

        self._draw_mode_card(
            self.single_card,
            "single",
            "1 AGENT",
            "Single-Agent Solver",
            "Visualize the Sokoban solution step by step",
            self.CARD_SINGLE,
            ("agent1",),
            ("UCS", "A*", "Task 5"),
        )
        self._draw_mode_card(
            self.comp_card,
            "competitive",
            "2 AGENTS",
            "Competitive Mode",
            "Two AI agents compete for water dispenser",
            self.CARD_COMP,
            ("agent1", "agent2"),
            ("GBFS", "A*", "Task 8"),
        )

        self._draw_footer()

    # P3 - Điều hướng T5/ T8

    def _restore_menu_window(self) -> None:
        """Khôi phục lại cửa sổ menu sau khi đóng Task 5 hoặc Task 8."""
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.window_w, self.window_h),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption("Office Sokoban - Game Menu")
        ensure_native_window_chrome()
        self.clock = pygame.time.Clock()

        # Pygame display được tạo lại nên ảnh convert() cũ có thể phụ thuộc display cũ.
        # Load lại AssetManager để chắc chắn tương thích sau khi quay về menu.
        self.assets = AssetManager()
        self._recalculate_layout(self.window_w, self.window_h, recreate_window=False)

    def _launch_single_agent(self) -> None:
        """Điều hướng tới Requirement 5, không copy bất kỳ logic solver nào."""
        from Ex5.sokoban_ui import main as run_single_agent

        pygame.quit()
        run_single_agent()
        self._restore_menu_window()

    def _launch_competitive(self) -> None:
        """Điều hướng tới Requirement 8, mặc định trận đấu 30 turns."""
        from Ex8.competitive_ui import main as run_competitive

        pygame.quit()
        run_competitive(max_steps=30)
        self._restore_menu_window()

    def _launch_mode(self, mode: str) -> None:
        if mode == "single":
            self._launch_single_agent()
        elif mode == "competitive":
            self._launch_competitive()

 #P4 - Event Loop
    def run(self) -> None:
        running = True
        window_resized_event = getattr(pygame, "WINDOWRESIZED", -9999)

        while running:
            mouse = pygame.mouse.get_pos()
            self.hover_mode = None
            if self.single_card.collidepoint(mouse):
                self.hover_mode = "single"
            elif self.comp_card.collidepoint(mouse):
                self.hover_mode = "competitive"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type in (pygame.VIDEORESIZE, window_resized_event):
                    width = getattr(event, "w", None) or getattr(event, "x", None) or self.screen.get_width()
                    height = getattr(event, "h", None) or getattr(event, "y", None) or self.screen.get_height()
                    self._recalculate_layout(width, height)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.single_card.collidepoint(event.pos):
                        self._launch_mode("single")
                    elif self.comp_card.collidepoint(event.pos):
                        self._launch_mode("competitive")

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        self._launch_mode("single")
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        self._launch_mode("competitive")
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            self.draw_frame()
            pygame.display.flip()
            self.clock.tick(Theme.FPS)

        pygame.quit()


def main() -> None:
    """Cho phép chạy trực tiếp: python menu_ui.py"""
    app = VisualMenuUI()
    app.run()


if __name__ == "__main__":
    main()
