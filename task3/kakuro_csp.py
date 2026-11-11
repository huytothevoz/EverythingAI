"""
Mô hình Kakuro dưới dạng CSP (Constraint Satisfaction Problem).

Trong CSP, ta cần xác định ba thành phần:
- Variables (biến): mỗi ô trắng là một biến X(row, column).
- Domains (miền): mỗi biến nhận một chữ số từ 1 đến 9.
- Constraints (ràng buộc): mỗi run ngang/dọc phải có tổng đúng clue và
  không được lặp chữ số.

Với một run gồm các biến X1, ..., Xn và clue T, ràng buộc có thể viết:
    X1 + ... + Xn = T
    AllDifferent(X1, ..., Xn)

Các ô được lưu bằng tọa độ bắt đầu từ 0. Mô-đun này chỉ mô tả và kiểm tra
bài toán; thuật toán tìm kiếm nằm riêng trong kakuro_solver.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations
from typing import Dict, FrozenSet, Mapping, Optional, Sequence, Set, Tuple

Cell = Tuple[int, int]
DomainMap = Dict[Cell, Set[int]]
Assignment = Dict[Cell, int]
DIGITS: FrozenSet[int] = frozenset(range(1, 10))


class KakuroError(Exception):
    """Lỗi cơ sở cho mô hình Kakuro hoặc cấu hình solver."""


class InvalidBoardError(KakuroError):
    """Dữ liệu run/bảng Kakuro không hợp lệ hoặc không thể thỏa mãn."""


@dataclass(frozen=True)
class RunConstraint:
    """Một nhóm ô trắng bị ràng buộc bởi cùng một clue Kakuro."""

    run_id: str
    cells: Tuple[Cell, ...]
    target: int
    direction: str = "unknown"
    _valid_tuples: Tuple[Tuple[int, ...], ...] = field(
        init=False, repr=False, compare=False
    )

    def __init__(
        self,
        run_id: str,
        cells: Sequence[Cell],
        target: int,
        direction: str = "unknown",
    ) -> None:
        normalized_cells = tuple((int(row), int(col)) for row, col in cells)
        object.__setattr__(self, "run_id", str(run_id))
        object.__setattr__(self, "cells", normalized_cells)
        object.__setattr__(self, "target", int(target))
        object.__setattr__(self, "direction", str(direction).lower())

        self._validate_shape()
        valid = self._generate_valid_tuples()
        if not valid:
            raise InvalidBoardError(
                f"Run {run_id!r} has no valid digit combination "
                f"(length={len(normalized_cells)}, target={target})."
            )
        object.__setattr__(self, "_valid_tuples", valid)

    def _validate_shape(self) -> None:
        if not self.run_id:
            raise InvalidBoardError("A run must have a non-empty run_id.")
        if not 1 <= len(self.cells) <= 9:
            raise InvalidBoardError(
                f"Run {self.run_id!r} must contain 1..9 white cells."
            )
        if len(set(self.cells)) != len(self.cells):
            raise InvalidBoardError(
                f"Run {self.run_id!r} contains a duplicated cell."
            )
        for row, col in self.cells:
            if row < 0 or col < 0:
                raise InvalidBoardError(
                    f"Cell coordinates must be non-negative: {(row, col)}."
                )
        if self.direction not in {"across", "down", "unknown"}:
            raise InvalidBoardError(
                "direction must be 'across', 'down', or 'unknown'."
            )

    def _generate_valid_tuples(self) -> Tuple[Tuple[int, ...], ...]:
        """Tạo các bộ số thỏa clue và không lặp để dùng khi kiểm tra hỗ trợ."""
        length = len(self.cells)
        return tuple(
            values
            for values in permutations(range(1, 10), length)
            if sum(values) == self.target
        )

    @property
    def valid_tuples(self) -> Tuple[Tuple[int, ...], ...]:
        """Các cách gán có thứ tự hợp lệ cho toàn bộ ô trong run."""
        return self._valid_tuples

    def is_satisfied(self, assignment: Mapping[Cell, int]) -> bool:
        """True khi mọi ô đã gán, đủ chữ số 1..9, khác nhau và tổng đúng."""
        if any(cell not in assignment for cell in self.cells):
            return False
        values = tuple(assignment[cell] for cell in self.cells)
        return (
            all(value in DIGITS for value in values)
            and len(set(values)) == len(values)
            and sum(values) == self.target
        )

    def accepts_partial(self, assignment: Mapping[Cell, int]) -> bool:
        """Kiểm tra phép gán dở dang còn ít nhất một cách hoàn tất hợp lệ."""
        return any(
            all(
                cell not in assignment or assignment[cell] == candidate[index]
                for index, cell in enumerate(self.cells)
            )
            for candidate in self.valid_tuples
        )


class KakuroBoard:
    """Dữ liệu bất biến của bảng: các run, ô trắng, clue và số cho sẵn."""

    def __init__(
        self,
        runs: Sequence[RunConstraint],
        givens: Optional[Mapping[Cell, int]] = None,
        name: str = "Kakuro puzzle",
        require_crossing_runs: bool = True,
    ) -> None:
        if not runs:
            raise InvalidBoardError("A Kakuro board must contain at least one run.")

        self.name = name
        self.runs: Tuple[RunConstraint, ...] = tuple(runs)
        self.givens: Dict[Cell, int] = dict(givens or {})
        self.cells: Tuple[Cell, ...] = tuple(
            sorted({cell for run in self.runs for cell in run.cells})
        )

        self._validate_unique_run_ids()
        self._validate_givens()
        self._validate_cell_coverage(require_crossing_runs)

        self.runs_by_cell: Dict[Cell, Tuple[RunConstraint, ...]] = {
            cell: tuple(run for run in self.runs if cell in run.cells)
            for cell in self.cells
        }

    def _validate_unique_run_ids(self) -> None:
        ids = [run.run_id for run in self.runs]
        if len(ids) != len(set(ids)):
            raise InvalidBoardError("Run IDs must be unique.")

    def _validate_givens(self) -> None:
        cell_set = set(self.cells)
        for cell, value in self.givens.items():
            if cell not in cell_set:
                raise InvalidBoardError(
                    f"Given cell {cell} does not occur in any run."
                )
            if value not in DIGITS:
                raise InvalidBoardError(
                    f"Given value for {cell} must be an integer from 1 to 9."
                )

    def _validate_cell_coverage(self, require_crossing_runs: bool) -> None:
        for cell in self.cells:
            directions = {
                run.direction for run in self.runs if cell in run.cells
            }
            if require_crossing_runs and not (
                "across" in directions and "down" in directions
            ):
                raise InvalidBoardError(
                    f"Cell {cell} must belong to one across and one down run. "
                    f"Found directions: {sorted(directions)}."
                )

    def describe(self) -> str:
        """Tóm tắt số biến và ràng buộc để tiện trình bày mô hình."""
        return (
            f"{self.name}: {len(self.cells)} variables, "
            f"{len(self.runs)} run constraints."
        )


class KakuroCSP:
    """Mô hình đầy đủ gồm variables, domains, constraints và constraint graph.

    Constraint graph là đồ thị có mỗi ô trắng là một đỉnh. Hai đỉnh nối với
    nhau nếu hai ô cùng thuộc ít nhất một run và vì vậy bị ràng buộc với nhau.
    """

    def __init__(self, board: KakuroBoard) -> None:
        self.board = board
        self.variables: Tuple[Cell, ...] = board.cells
        self.constraints: Tuple[RunConstraint, ...] = board.runs

        # Lưu đồ thị theo danh sách kề; neighbors vẫn là tên tiện dụng cho solver.
        self.constraint_graph: Dict[Cell, Set[Cell]] = {
            cell: set() for cell in self.variables
        }
        for run in self.constraints:
            for cell in run.cells:
                self.constraint_graph[cell].update(
                    other for other in run.cells if other != cell
                )
        self.neighbors = self.constraint_graph

    def initial_domains(self) -> DomainMap:
        """Mỗi ô bắt đầu có 1..9; ô đã cho sẵn bị cố định thành một giá trị."""
        domains: DomainMap = {
            cell: set(DIGITS) for cell in self.variables
        }
        for cell, value in self.board.givens.items():
            domains[cell] = {value}
        return domains

    def is_complete(self, assignment: Mapping[Cell, int]) -> bool:
        """Phép gán đầy đủ khi đã có giá trị cho mọi ô trắng."""
        return len(assignment) == len(self.variables)

    def is_consistent(self, assignment: Mapping[Cell, int]) -> bool:
        """Kiểm tra phép gán một phần còn có thể hoàn tất hợp lệ hay không.

        Mỗi run phải còn ít nhất một bộ giá trị hợp lệ khớp với các số đã gán.
        Đây là kiểm tra tính nhất quán cục bộ trên các ràng buộc Kakuro.
        """
        return (
            all(cell in self.variables for cell in assignment)
            and all(
                assignment.get(cell, value) == value
                for cell, value in self.board.givens.items()
            )
            and all(
                run.accepts_partial(assignment)
                for run in self.constraints
            )
        )

    def validate_solution(self, assignment: Mapping[Cell, int]) -> bool:
        """Kiểm tra nghiệm hoàn chỉnh trên tất cả run và các số cho sẵn."""
        return (
            self.is_complete(assignment)
            and all(run.is_satisfied(assignment) for run in self.constraints)
            and all(
                assignment.get(cell) == value
                for cell, value in self.board.givens.items()
            )
        )


def make_tiny_example_board() -> KakuroBoard:
    """Tạo ví dụ 2x2 nhỏ để minh họa giao nhau của các ràng buộc.

    A + B = 3, C + D = 7; A + C = 4, B + D = 6.
    Nghiệm duy nhất là A=1, B=2, C=3, D=4.
    """
    return KakuroBoard(
        name="Tiny 2x2 Kakuro example",
        runs=[
            RunConstraint("A1", [(1, 1), (1, 2)], 3, "across"),
            RunConstraint("A2", [(2, 1), (2, 2)], 7, "across"),
            RunConstraint("D1", [(1, 1), (2, 1)], 4, "down"),
            RunConstraint("D2", [(1, 2), (2, 2)], 6, "down"),
        ],
    )
