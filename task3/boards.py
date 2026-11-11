"""
boards.py
=========
Du lieu cac bang Kakuro dung cho Task 3.

Toa do (row, column) bat dau tu 0.
Moi RunConstraint la mot day o trang theo chieu ngang (across)
hoac doc (down). So ghi tren o goi y la tong cua day tuong ung.
"""
from kakuro_csp import KakuroBoard, RunConstraint


def make_assignment_board() -> KakuroBoard:
    "Clue lấy từ bảng 9x9 từ đề bài"
    runs = [
        # Ngang (Across): clue nam o ben trai day o trang.
        RunConstraint("A1", [(1, 2), (1, 3), (1, 4)], 22, "across"),
        RunConstraint("A2", [(1, 6), (1, 7)], 3, "across"),
        RunConstraint("A3", [(2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8)], 28, "across"),
        RunConstraint("A4", [(3, 1), (3, 2)], 14, "across"),
        RunConstraint("A5", [(3, 5), (3, 6), (3, 7), (3, 8)], 20, "across"),
        RunConstraint("A6", [(4, 1), (4, 2)], 17, "across"),
        RunConstraint("A7", [(4, 4), (4, 5), (4, 6), (4, 7)], 22, "across"),
        RunConstraint("A8", [(5, 2), (5, 3), (5, 4), (5, 5)], 28, "across"),
        RunConstraint("A9", [(5, 7), (5, 8)], 12, "across"),
        RunConstraint("A10", [(6, 1), (6, 2), (6, 3), (6, 4)], 14, "across"),
        RunConstraint("A11", [(6, 7), (6, 8)], 6, "across"),
        RunConstraint("A12", [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)], 39, "across"),
        RunConstraint("A13", [(8, 2), (8, 3)], 16, "across"),
        RunConstraint("A14", [(8, 5), (8, 6), (8, 7)], 8, "across"),

        # Doc (Down): clue nam phia tren day o trang.
        RunConstraint("D1", [(1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2)], 44, "down"),
        RunConstraint("D2", [(1, 3), (2, 3)], 16, "down"),
        RunConstraint("D3", [(1, 4), (2, 4)], 9, "down"),
        RunConstraint("D4", [(1, 6), (2, 6), (3, 6), (4, 6)], 15, "down"),
        RunConstraint("D5", [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7)], 44, "down"),
        RunConstraint("D6", [(2, 5), (3, 5), (4, 5), (5, 5)], 11, "down"),
        RunConstraint("D7", [(2, 8), (3, 8)], 14, "down"),
        RunConstraint("D8", [(3, 1), (4, 1)], 17, "down"),
        RunConstraint("D9", [(4, 4), (5, 4), (6, 4), (7, 4)], 12, "down"),
        RunConstraint("D10", [(5, 3), (6, 3), (7, 3), (8, 3)], 29, "down"),
        RunConstraint("D11", [(5, 8), (6, 8)], 7, "down"),
        RunConstraint("D12", [(6, 1), (7, 1)], 12, "down"),
        RunConstraint("D13", [(7, 5), (8, 5)], 7, "down"),
        RunConstraint("D14", [(7, 6), (8, 6)], 12, "down"),
    ]
    return KakuroBoard(runs, name="Assignment Kakuro 9x9")


def make_demo_board() -> KakuroBoard:
    """Bang nho 2x2 de thu nhanh solver."""
    runs = [
        RunConstraint("A1", [(1, 1), (1, 2)], 3, "across"),
        RunConstraint("A2", [(2, 1), (2, 2)], 7, "across"),
        RunConstraint("D1", [(1, 1), (2, 1)], 4, "down"),
        RunConstraint("D2", [(1, 2), (2, 2)], 6, "down"),
    ]
    return KakuroBoard(runs, name="Tiny 2x2 demonstration")
