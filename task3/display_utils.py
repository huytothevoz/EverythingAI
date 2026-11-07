"""Helpers for opening Pygame windows within the available desktop size."""

from __future__ import annotations

from typing import Tuple

import pygame


def initial_window_size(
    desired_size: Tuple[int, int],
    margins: Tuple[int, int] = (32, 96),
) -> Tuple[int, int]:
    """Return a startup size that leaves room for desktop borders and taskbars."""
    desktop_sizes = pygame.display.get_desktop_sizes()
    if desktop_sizes:
        desktop_width, desktop_height = desktop_sizes[0]
    else:
        display_info = pygame.display.Info()
        desktop_width, desktop_height = display_info.current_w, display_info.current_h

    available_width = max(1, desktop_width - margins[0])
    available_height = max(1, desktop_height - margins[1])
    return min(desired_size[0], available_width), min(desired_size[1], available_height)
