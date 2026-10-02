from __future__ import annotations

import os
import sys
from typing import Dict, Optional, Tuple

import pygame

# Root project để tìm assets.
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Hỗ trợ cửa sổ native
def ensure_native_window_chrome() -> None:
    if sys.platform != "win32":
        return

    try:
        import ctypes

        hwnd = pygame.display.get_wm_info().get("window")
        if not hwnd:
            return

        GWL_STYLE = -16
        WS_CAPTION = 0x00C00000
        WS_THICKFRAME = 0x00040000
        WS_MINIMIZEBOX = 0x00020000
        WS_MAXIMIZEBOX = 0x00010000
        WS_SYSMENU = 0x00080000
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020

        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        style |= WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
        )
    except Exception:
        # Lỗi native window không làm dừng game.
        pass


# Theme dùng chung
class Theme:
    """Các hằng số chung; kích thước thực tế sẽ scale theo cửa sổ."""

    FPS = 60
    AUTO_STEP_SEC = 0.35

    # Kích thước tham chiếu để tính responsive.
    DESIGN_W = 1200
    DESIGN_H = 850
    BASE_CELL = 72

    TEXT = (45, 52, 67)
    TEXT_DIM = (103, 112, 130)
    WHITE = (255, 255, 255)
    CARD = (250, 252, 255)
    CARD_BORDER = (212, 222, 236)
    SHADOW = (0, 0, 0, 45)

    BTN_BLUE = (73, 135, 243)
    BTN_ORANGE = (255, 111, 77)
    BTN_PINK = (241, 89, 124)
    BTN_TEXT = (255, 255, 255)

    SUCCESS = (40, 167, 86)
    FAIL = (219, 72, 72)
    GOLD = (255, 215, 70)
    GOLD_DARK = (214, 146, 17)


# Quản lý asset
class AssetManager:
    """Load và cache asset dùng chung cho Task 5 và Task 8."""

    def __init__(self) -> None:
        asset_dir = os.path.join(PARENT_DIR, "assets")
        self.original: Dict[str, pygame.Surface] = {
            "background": self._load(os.path.join(asset_dir, "background_voxel.png"), alpha=False),
            "floor": self._load(os.path.join(asset_dir, "floor_tile.png"), alpha=False),
            "wall": self._load(os.path.join(asset_dir, "wall_tile.png"), alpha=False),
            "water_dispenser": self._load(os.path.join(asset_dir, "water_dispenser.png"), alpha=True),
            "agent1": self._load(os.path.join(asset_dir, "agent1_office_male.png"), alpha=True),
            "agent2": self._load(os.path.join(asset_dir, "agent2_office_female.png"), alpha=True),
        }
        self.scaled_cache: Dict[Tuple[str, Tuple[int, int]], pygame.Surface] = {}

    @staticmethod
    def _load(path: str, alpha: bool) -> pygame.Surface:
        image = pygame.image.load(path)
        return image.convert_alpha() if alpha else image.convert()

    def get_scaled(self, key: str, size: Tuple[int, int]) -> pygame.Surface:
        """Scale ảnh và lưu vào cache."""
        safe_size = (max(1, int(size[0])), max(1, int(size[1])))
        cache_key = (key, safe_size)

        if cache_key not in self.scaled_cache:
            self.scaled_cache[cache_key] = pygame.transform.smoothscale(
                self.original[key],
                safe_size,
            )

        return self.scaled_cache[cache_key]

    def get_tinted_water_dispenser(
        self,
        size: int,
        color: Tuple[int, int, int],
        label: Optional[str] = None,
    ) -> pygame.Surface:
        """Tạo water dispenser có màu theo owner."""

        base = self.get_scaled(
            "water_dispenser",
            (size, size)
        ).copy()

        overlay = pygame.Surface(
            (size, size),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            overlay,
            (*color, 80),
            pygame.Rect(
                0,
                size - max(12, size // 4),
                size,
                max(12, size // 4)
            ),
            border_radius=8
        )

        pygame.draw.rect(
            overlay,
            (*color, 120),
            pygame.Rect(
                4,
                4,
                size - 8,
                size - 8
            ),
            width=max(2, size // 18),
            border_radius=12
        )

        base.blit(overlay, (0, 0))

        if label:
            font = pygame.font.Font(
                None,
                max(14, size // 4)
            )

            text = font.render(
                label,
                True,
                Theme.WHITE
            )

            bg = pygame.Surface(
                (
                    text.get_width() + 10,
                    text.get_height() + 4
                ),
                pygame.SRCALPHA
            )

            bg.fill((0, 0, 0, 100))

            base.blit(
                bg,
                (
                    size - bg.get_width() - 6,
                    size - bg.get_height() - 6
                )
            )

            base.blit(
                text,
                (
                    size - text.get_width() - 11,
                    size - text.get_height() - 8
                )
            )

        return base


# Base UI
class ResponsiveSokobanUIBase:
    def __init__(
        self,
        rows: int,
        cols: int,
        window_title: str,
        header_subtitle: str,
        initial_width_ratio: float = 0.72,
        initial_height_ratio: float = 0.78,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.window_title = window_title
        self.header_subtitle = header_subtitle
        self.initial_width_ratio = initial_width_ratio
        self.initial_height_ratio = initial_height_ratio

        # Mở cửa sổ ở giữa màn hình.
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        pygame.display.set_caption(window_title)

        initial_size = self._choose_initial_window_size()
        self.screen = pygame.display.set_mode(initial_size, pygame.RESIZABLE)
        ensure_native_window_chrome()

        self.clock = pygame.time.Clock()
        self.assets = AssetManager()

        self.window_w, self.window_h = self.screen.get_size()
        self._recalculate_layout(self.window_w, self.window_h, recreate_window=False)

    def _choose_initial_window_size(self) -> Tuple[int, int]:
        """Chọn kích thước cửa sổ ban đầu theo desktop."""
        info = pygame.display.Info()
        desktop_w = max(800, info.current_w)
        desktop_h = max(600, info.current_h)

        width = min(1240, int(desktop_w * self.initial_width_ratio))
        height = min(820, int(desktop_h * self.initial_height_ratio))

        # Kích thước ban đầu, người dùng vẫn có thể resize.
        width = max(680, width)
        height = max(520, height)
        return width, height

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _init_fonts_for_scale(self, scale: float) -> None:
        """Scale font theo cửa sổ."""
        self.font_title = pygame.font.SysFont("Segoe UI", max(18, int(32 * scale)), bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", max(11, int(18 * scale)), bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", max(11, int(16 * scale)))
        self.font_small = pygame.font.SysFont("Segoe UI", max(9, int(14 * scale)))
        self.font_button = pygame.font.SysFont("Segoe UI", max(13, int(20 * scale)), bold=True)
        self.font_chip_title = pygame.font.SysFont("Segoe UI", max(9, int(13 * scale)), bold=True)
        self.font_chip_value = pygame.font.SysFont("Segoe UI", max(11, int(18 * scale)), bold=True)

    def _get_panel_layout_settings(self) -> Tuple[int, int]:
        """Subclass trả (panel_height, help_height)."""
        raise NotImplementedError

    def _recalculate_layout(self, width: int, height: int, recreate_window: bool = True) -> None:
        self.window_w = max(320, int(width))
        self.window_h = max(300, int(height))

        if recreate_window:
            self.screen = pygame.display.set_mode(
                (self.window_w, self.window_h),
                pygame.RESIZABLE,
            )
            ensure_native_window_chrome()

        self.ui_scale = self._clamp(
            min(self.window_w / Theme.DESIGN_W, self.window_h / Theme.DESIGN_H),
            0.50,
            1.18,
        )
        self._init_fonts_for_scale(self.ui_scale)

        self.outer = max(6, int(22 * self.ui_scale))
        self.card_pad = max(5, int(12 * self.ui_scale))
        self.gap = max(4, int(10 * self.ui_scale))
        self.header_h = max(48, int(66 * self.ui_scale))
        self.button_h = max(34, int(48 * self.ui_scale))
        self.chip_h = max(38, int(56 * self.ui_scale))

        self.panel_h, self.help_h = self._get_panel_layout_settings()
        self.show_help = self.help_h > 0

        # Phần chiều cao dành cho header, panel và control.
        reserved_h = (
            self.outer
            + self.header_h
            + self.gap
            + 2 * self.card_pad
            + self.gap
            + self.button_h
            + self.gap
            + self.panel_h
            + (self.gap + self.help_h if self.show_help else 0)
            + self.outer
        )

        available_board_h = max(24, self.window_h - reserved_h)
        available_board_w = max(24, self.window_w - 2 * self.outer - 2 * self.card_pad)

        cell_by_w = available_board_w // max(1, self.cols)
        cell_by_h = available_board_h // max(1, self.rows)
        preferred = int(Theme.BASE_CELL * self.ui_scale)
        self.cell_size = max(8, min(preferred, cell_by_w, cell_by_h))

        self.map_pixel_w = self.cols * self.cell_size
        self.map_pixel_h = self.rows * self.cell_size

        self.header_rect = pygame.Rect(
            self.outer,
            self.outer,
            max(10, self.window_w - 2 * self.outer),
            self.header_h,
        )

        board_card_w = self.map_pixel_w + 2 * self.card_pad
        board_card_h = self.map_pixel_h + 2 * self.card_pad
        self.board_card = pygame.Rect(
            (self.window_w - board_card_w) // 2,
            self.header_rect.bottom + self.gap,
            board_card_w,
            board_card_h,
        )
        self.board_x = self.board_card.x + self.card_pad
        self.board_y = self.board_card.y + self.card_pad

        # Ba nút điều khiển dùng chung.
        button_area_w = min(
            max(220, self.window_w - 2 * self.outer),
            max(300, int(600 * self.ui_scale)),
        )
        button_gap = max(4, int(16 * self.ui_scale))
        button_w = max(52, (button_area_w - 2 * button_gap) // 3)
        total_button_w = 3 * button_w + 2 * button_gap
        button_x = (self.window_w - total_button_w) // 2
        button_y = self.board_card.bottom + self.gap

        self.btn_left = pygame.Rect(button_x, button_y, button_w, self.button_h)
        self.btn_middle = pygame.Rect(
            button_x + button_w + button_gap,
            button_y,
            button_w,
            self.button_h,
        )
        self.btn_right = pygame.Rect(
            button_x + 2 * (button_w + button_gap),
            button_y,
            button_w,
            self.button_h,
        )

        self.panel_rect = pygame.Rect(
            self.outer,
            self.btn_left.bottom + self.gap,
            max(10, self.window_w - 2 * self.outer),
            self.panel_h,
        )

        if self.show_help:
            self.help_rect = pygame.Rect(
                self.outer,
                self.panel_rect.bottom + self.gap,
                max(10, self.window_w - 2 * self.outer),
                self.help_h,
            )
        else:
            self.help_rect = pygame.Rect(0, 0, 0, 0)

    # Hàm vẽ dùng chung
    def _draw_background(self) -> None:
        bg = self.assets.get_scaled("background", (self.window_w, self.window_h))
        self.screen.blit(bg, (0, 0))

        # Lớp phủ nhẹ để chữ dễ đọc.
        veil = pygame.Surface((self.window_w, self.window_h), pygame.SRCALPHA)
        veil.fill((255, 255, 255, 24))
        self.screen.blit(veil, (0, 0))

    def _font_that_fits(
        self,
        text: str,
        max_width: int,
        start_size: int,
        min_size: int,
        bold: bool = True,
    ) -> pygame.font.Font:
        """Giảm font tới khi text vừa chiều rộng."""
        size = max(min_size, start_size)
        while size > min_size:
            font = pygame.font.SysFont("Segoe UI", size, bold=bold)
            if font.size(text)[0] <= max_width:
                return font
            size -= 1
        return pygame.font.SysFont("Segoe UI", min_size, bold=bold)

    def _draw_header(self) -> None:
        """Vẽ header dùng chung."""
        radius = max(10, int(20 * self.ui_scale))
        pygame.draw.rect(self.screen, Theme.WHITE, self.header_rect, border_radius=radius)
        pygame.draw.rect(
            self.screen,
            Theme.CARD_BORDER,
            self.header_rect,
            width=2,
            border_radius=radius,
        )

        pad = max(8, int(14 * self.ui_scale))
        pill_h = max(30, self.header_rect.height - 2 * pad)

        # Ẩn subtitle nếu header quá hẹp.
        desired_pill_w = int(330 * self.ui_scale)
        max_pill_w = max(150, self.header_rect.width - 2 * pad)
        pill_w = min(desired_pill_w, max_pill_w)

        pill = pygame.Rect(
            self.header_rect.x + pad,
            self.header_rect.y + (self.header_rect.height - pill_h) // 2,
            pill_w,
            pill_h,
        )
        pygame.draw.rect(self.screen, (255, 206, 71), pill, border_radius=max(8, pill_h // 3))
        pygame.draw.rect(
            self.screen,
            (193, 131, 25),
            pill,
            width=max(1, int(2 * self.ui_scale)),
            border_radius=max(8, pill_h // 3),
        )

        title_text = "OFFICE SOKOBAN"
        title_font = self._font_that_fits(
            title_text,
            max_width=max(40, pill.width - 2 * pad),
            start_size=max(18, int(32 * self.ui_scale)),
            min_size=12,
        )
        title = title_font.render(title_text, True, (136, 53, 18))
        self.screen.blit(title, title.get_rect(center=pill.center))

        subtitle_x = pill.right + pad
        subtitle_w = self.header_rect.right - pad - subtitle_x

        # Chỉ vẽ subtitle khi còn đủ chỗ.
        if subtitle_w >= 170:
            subtitle_font = self._font_that_fits(
                self.header_subtitle,
                max_width=subtitle_w,
                start_size=max(11, int(18 * self.ui_scale)),
                min_size=9,
                bold=True,
            )
            subtitle = subtitle_font.render(self.header_subtitle, True, Theme.TEXT_DIM)
            self.screen.blit(
                subtitle,
                (subtitle_x, self.header_rect.centery - subtitle.get_height() // 2),
            )

    def _draw_button(
        self,
        rect: pygame.Rect,
        text: str,
        color: Tuple[int, int, int],
    ) -> None:
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        draw_rect = rect.move(0, -2 if hover else 0)
        shadow = rect.move(0, max(2, int(4 * self.ui_scale)))

        pygame.draw.rect(
            self.screen,
            Theme.SHADOW,
            shadow,
            border_radius=max(6, int(14 * self.ui_scale)),
        )
        pygame.draw.rect(
            self.screen,
            color,
            draw_rect,
            border_radius=max(6, int(14 * self.ui_scale)),
        )
        pygame.draw.rect(
            self.screen,
            Theme.WHITE,
            draw_rect,
            width=max(1, int(2 * self.ui_scale)),
            border_radius=max(6, int(14 * self.ui_scale)),
        )

        font = self._font_that_fits(
            text,
            max_width=max(20, rect.width - 12),
            start_size=max(13, int(20 * self.ui_scale)),
            min_size=9,
        )
        label = font.render(text, True, Theme.BTN_TEXT)
        self.screen.blit(label, label.get_rect(center=draw_rect.center))

    def _draw_goal_marker(self, x: int, y: int) -> None:
        """Goal marker dùng chung trên floor tile."""
        cx = x + self.cell_size // 2
        cy = y + self.cell_size // 2
        outer = max(3, self.cell_size // 4)
        inner = max(2, self.cell_size // 8)

        pygame.draw.circle(self.screen, Theme.GOLD, (cx, cy), outer)
        pygame.draw.circle(
            self.screen,
            Theme.WHITE,
            (cx, cy),
            max(1, outer - max(1, self.cell_size // 16)),
        )
        pygame.draw.circle(self.screen, Theme.GOLD, (cx, cy), inner)
        pygame.draw.circle(
            self.screen,
            Theme.GOLD_DARK,
            (cx, cy),
            outer,
            width=max(1, self.cell_size // 22),
        )

    def _draw_chip(self, rect: pygame.Rect, title: str, value: str) -> None:
        radius = max(5, int(12 * self.ui_scale))
        pygame.draw.rect(self.screen, Theme.WHITE, rect, border_radius=radius)
        pygame.draw.rect(
            self.screen,
            Theme.CARD_BORDER,
            rect,
            width=1,
            border_radius=radius,
        )

        left = rect.x + max(5, int(11 * self.ui_scale))
        title_surface = self.font_chip_title.render(title, True, Theme.TEXT_DIM)

        # Giảm font nếu value quá dài.
        value_font = self._font_that_fits(
            value,
            max_width=max(20, rect.width - 2 * (left - rect.x)),
            start_size=max(11, int(18 * self.ui_scale)),
            min_size=8,
        )
        value_surface = value_font.render(value, True, Theme.TEXT)

        self.screen.blit(
            title_surface,
            (left, rect.y + max(3, int(6 * self.ui_scale))),
        )
        self.screen.blit(
            value_surface,
            (
                left,
                rect.bottom - value_surface.get_height() - max(3, int(6 * self.ui_scale)),
            ),
        )

    def _draw_help_bar(self, help_text: str) -> None:
        if not self.show_help:
            return

        radius = max(5, int(11 * self.ui_scale))
        pygame.draw.rect(self.screen, Theme.CARD, self.help_rect, border_radius=radius)
        pygame.draw.rect(
            self.screen,
            Theme.CARD_BORDER,
            self.help_rect,
            width=1,
            border_radius=radius,
        )

        font = self._font_that_fits(
            help_text,
            max_width=max(30, self.help_rect.width - 16),
            start_size=max(9, int(14 * self.ui_scale)),
            min_size=8,
            bold=False,
        )
        surface = font.render(help_text, True, Theme.TEXT)
        self.screen.blit(surface, surface.get_rect(center=self.help_rect.center))

    # Xử lý resize
    def _handle_resize_event(self, event: pygame.event.Event) -> None:
        """Tính lại layout sau khi resize."""
        if event.type == pygame.VIDEORESIZE:
            self._recalculate_layout(event.w, event.h, recreate_window=True)
            return

        # Đồng bộ lại kích thước surface sau resize.
        surface = pygame.display.get_surface()
        if surface is not None:
            self.screen = surface
            width, height = surface.get_size()
            self._recalculate_layout(width, height, recreate_window=False)
