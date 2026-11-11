"""Các thuật toán tìm kiếm và lan truyền ràng buộc để giải Kakuro.

Mô hình biến, miền, ràng buộc và đồ thị được định nghĩa trong kakuro_csp.py.
File này dùng mô hình đó theo quy trình:
- Propagation: loại sớm giá trị không thể dẫn tới nghiệm.
- GAC: với từng run nhiều biến, mỗi giá trị còn lại phải có ít nhất một bộ
  giá trị hợp lệ hỗ trợ. Khi miền đổi, đưa các run giao với ô đó vào hàng đợi.
- Forward Checking: sau khi gán một ô, chỉ cập nhật các run chứa ô vừa gán.
- Backtracking: thử một giá trị, giải tiếp bài toán con; nếu mâu thuẫn thì
  bỏ nhánh đó và thử giá trị kế tiếp.
- MRV chọn ô có miền nhỏ nhất; Degree phá hòa bằng cách chọn ô có nhiều láng
  giềng chưa gán nhất; LCV thử giá trị làm mất ít lựa chọn của láng giềng nhất.

GAC ở đây áp dụng ý tưởng queue/revise của AC-3 cho ràng buộc nhiều biến;
đây không phải cài đặt AC-3 nhị phân thông thường. Các sự kiện của solver
được gửi tới callback để GUI trực quan hóa domain, gán số và quay lui.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import perf_counter
from typing import (
    Callable,
    Deque,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
)

from kakuro_csp import (
    Assignment,
    Cell,
    DomainMap,
    KakuroBoard,
    KakuroCSP,
    KakuroError,
    RunConstraint,
    make_tiny_example_board,
)

EventCallback = Optional[Callable[["SolverEvent"], None]]


@dataclass(frozen=True)
class SolverEvent:
    """Sự kiện do bộ giải phát ra để GUI có thể hiển thị.

    Attributes:
        kind: Loại sự kiện, ví dụ "domain_reduced", "assignment",
              "contradiction", "backtrack", "solution_found".
        message: Nội dung giải thích để người dùng đọc.
        cell: Ô bị ảnh hưởng, nếu có.
        value: Giá trị được gán hoặc bị loại, nếu có.
        before: Miền giá trị trước khi cập nhật, nếu có.
        after: Miền giá trị sau khi cập nhật, nếu có.
        run_id: Mã dãy gây ra cập nhật, nếu có.
        depth: Độ sâu tìm kiếm đệ quy hiện tại.
    """

    kind: str
    message: str
    cell: Optional[Cell] = None
    value: Optional[int] = None
    before: Tuple[int, ...] = ()
    after: Tuple[int, ...] = ()
    run_id: Optional[str] = None
    depth: int = 0


@dataclass
class SolverStats:
    """Các bộ đếm và thời gian của một lần gọi solve()."""

    elapsed_ms: float = 0.0
    expanded_nodes: int = 0
    assignments_tried: int = 0
    backtrack_count: int = 0
    propagation_calls: int = 0
    propagation_revisions: int = 0
    domain_values_removed: int = 0
    contradictions: int = 0
    solutions_found: int = 0

    def as_dict(self) -> Dict[str, float | int]:
        """Trả thống kê dưới dạng từ điển thuận tiện cho việc tuần tự hóa."""
        return {
            "elapsed_ms": round(self.elapsed_ms, 3),
            "expanded_nodes": self.expanded_nodes,
            "assignments_tried": self.assignments_tried,
            "backtrack_count": self.backtrack_count,
            "propagation_calls": self.propagation_calls,
            "propagation_revisions": self.propagation_revisions,
            "domain_values_removed": self.domain_values_removed,
            "contradictions": self.contradictions,
            "solutions_found": self.solutions_found,
        }


# Bộ giải

class KakuroSolver:
    """Bộ giải CSP bằng quay lui, lan truyền ràng buộc và heuristic Bài 08.

    Tham số:
        board: Mô hình KakuroBoard.
        propagation: "gac", "forward_checking" hoặc "none".
            "gac" đảm bảo nhất quán cung tổng quát trên các dãy nhiều biến.
        use_mrv: Có dùng heuristic Giá trị còn lại ít nhất (MRV) không.
        use_degree: Có dùng heuristic Degree để phá hòa khi MRV bằng nhau không.
        use_lcv: Có sắp xếp giá trị theo Giá trị ít ràng buộc nhất (LCV) không.
        event_callback: Hàm callback tùy chọn nhận các sự kiện SolverEvent.
        max_events: Số sự kiện tối đa gửi đến callback (None = không giới hạn).

    Có thể dùng lại một đối tượng bộ giải; mỗi lần gọi solve() sẽ đặt lại thống kê.
    """

    def __init__(
        self,
        board: KakuroBoard,
        propagation: str = "gac",
        use_mrv: bool = True,
        use_degree: bool = True,
        use_lcv: bool = True,
        event_callback: EventCallback = None,
        max_events: Optional[int] = 100_000,
    ) -> None:
        normalized = propagation.lower().replace("-", "_")
        if normalized not in {"gac", "forward_checking", "none"}:
            raise ValueError(
                "propagation must be 'gac', 'forward_checking', or 'none'."
            )
        if max_events is not None and max_events < 0:
            raise ValueError("max_events must be None or non-negative.")

        self.csp = KakuroCSP(board)
        self.propagation = normalized
        self.use_mrv = use_mrv
        self.use_degree = use_degree
        self.use_lcv = use_lcv
        self.event_callback = event_callback
        self.max_events = max_events

        self.stats = SolverStats()
        self._event_count = 0
        self._depth = 0

    @property
    def board(self) -> KakuroBoard:
        return self.csp.board

    def _emit(
        self,
        kind: str,
        message: str,
        cell: Optional[Cell] = None,
        value: Optional[int] = None,
        before: Iterable[int] = (),
        after: Iterable[int] = (),
        run_id: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> None:
        if self.event_callback is None:
            return
        if self.max_events is not None and self._event_count >= self.max_events:
            return
        event = SolverEvent(
            kind=kind,
            message=message,
            cell=cell,
            value=value,
            before=tuple(sorted(before)),
            after=tuple(sorted(after)),
            run_id=run_id,
            depth=self._depth if depth is None else depth,
        )
        self._event_count += 1
        self.event_callback(event)

    @staticmethod
    def _copy_domains(domains: Mapping[Cell, Set[int]]) -> DomainMap:
        return {cell: set(values) for cell, values in domains.items()}

    def _record_domain_change(
        self,
        cell: Cell,
        old_domain: Set[int],
        new_domain: Set[int],
        run: RunConstraint,
    ) -> None:
        removed = old_domain - new_domain
        if not removed:
            return
        self.stats.domain_values_removed += len(removed)
        self._emit(
            "domain_reduced",
            (
                f"Run {run.run_id}: domain of {cell} reduced from "
                f"{sorted(old_domain)} to {sorted(new_domain)}; "
                f"removed {sorted(removed)}."
            ),
            cell=cell,
            before=old_domain,
            after=new_domain,
            run_id=run.run_id,
        )

    # ----- Lan truyền ràng buộc: GAC / hàng đợi theo ý tưởng AC-3 ----------

    def enforce_gac(
        self,
        domains: DomainMap,
        initial_runs: Optional[Iterable[RunConstraint]] = None,
    ) -> bool:
        """Đảm bảo GAC trên ràng buộc dãy nhiều biến bằng hàng đợi.

        Một bộ ứng viên hỗ trợ một giá trị khi:
        - bộ đó thỏa tổng cần đạt và điều kiện các chữ số khác nhau;
        - giá trị ở mỗi vị trí thuộc miền hiện tại của ô tương ứng.

        Nếu miền của một ô thay đổi, các dãy khác chứa ô đó được đưa lại vào
        hàng đợi để kiểm tra. Đây là cách khái quát quy trình hàng đợi/kiểm tra
        lại của AC-3 từ cung nhị phân sang hỗ trợ giữa biến và dãy.
        """
        self.stats.propagation_calls += 1
        queue: Deque[RunConstraint] = deque(
            initial_runs if initial_runs is not None else self.csp.constraints
        )
        queued = {run.run_id for run in queue}

        while queue:
            run = queue.popleft()
            queued.discard(run.run_id)
            self.stats.propagation_revisions += 1

            compatible = [
                candidate
                for candidate in run.valid_tuples
                if all(
                    candidate[index] in domains[cell]
                    for index, cell in enumerate(run.cells)
                )
            ]

            if not compatible:
                self.stats.contradictions += 1
                self._emit(
                    "contradiction",
                    f"Run {run.run_id} has no compatible tuple.",
                    run_id=run.run_id,
                )
                return False

            for index, cell in enumerate(run.cells):
                supported = {candidate[index] for candidate in compatible}
                old_domain = set(domains[cell])
                new_domain = old_domain & supported

                if new_domain != old_domain:
                    domains[cell] = new_domain
                    self._record_domain_change(cell, old_domain, new_domain, run)

                    if not new_domain:
                        self.stats.contradictions += 1
                        self._emit(
                            "contradiction",
                            f"Domain of {cell} became empty.",
                            cell=cell,
                            before=old_domain,
                            after=new_domain,
                            run_id=run.run_id,
                        )
                        return False

                    # Đổi miền của một ô có thể làm mất giá trị hỗ trợ trong
                    # các dãy khác giao với ô đó.
                    for neighbor_run in self.board.runs_by_cell[cell]:
                        if (
                            neighbor_run.run_id != run.run_id
                            and neighbor_run.run_id not in queued
                        ):
                            queue.append(neighbor_run)
                            queued.add(neighbor_run.run_id)

        return True

    # ----- Lan truyền ràng buộc: Kiểm tra xuôi -----------------------------

    # Kiểm tra xuôi (Forward Checking): sau khi gán giá trị cho một ô, chỉ
    # kiểm tra các dãy chứa ô đó và loại các giá trị không còn tương thích
    # ở những ô chưa gán còn lại trong các dãy ấy.
    def forward_check(
        self,
        variable: Cell,
        domains: DomainMap,
    ) -> bool:
        """Kiểm tra xuôi sau khi biến được gán miền chỉ còn một giá trị.

        Chỉ kiểm tra các dãy có chứa biến vừa được gán. Với mỗi ô chưa gán
        khác trong các dãy đó, loại các giá trị không có bộ giá trị nào hỗ trợ.
        Cách này yếu hơn GAC đầy đủ và hữu ích làm mốc so sánh trong thí nghiệm.
        """
        self.stats.propagation_calls += 1
        if len(domains[variable]) != 1:
            raise ValueError("Forward checking expects a singleton domain.")

        affected_runs = self.board.runs_by_cell[variable]
        for run in affected_runs:
            compatible = [
                candidate
                for candidate in run.valid_tuples
                if all(
                    candidate[index] in domains[cell]
                    for index, cell in enumerate(run.cells)
                )
            ]
            if not compatible:
                self.stats.contradictions += 1
                self._emit(
                    "contradiction",
                    f"Forward checking: run {run.run_id} has no support.",
                    cell=variable,
                    run_id=run.run_id,
                )
                return False

            for index, cell in enumerate(run.cells):
                if cell == variable:
                    continue
                supported = {candidate[index] for candidate in compatible}
                old_domain = set(domains[cell])
                new_domain = old_domain & supported
                if new_domain != old_domain:
                    domains[cell] = new_domain
                    self._record_domain_change(cell, old_domain, new_domain, run)
                    if not new_domain:
                        self.stats.contradictions += 1
                        self._emit(
                            "contradiction",
                            f"Forward checking emptied domain of {cell}.",
                            cell=cell,
                            before=old_domain,
                            after=new_domain,
                            run_id=run.run_id,
                        )
                        return False
        return True

    # Nhất quán cung tổng quát (GAC): mỗi dãy Kakuro là ràng buộc nhiều biến,
    # nên ta kiểm tra các bộ giá trị hợp lệ cho toàn dãy. Giá trị nào không
    # xuất hiện trong bộ hợp lệ nào sẽ bị loại khỏi miền. Theo ý tưởng hàng
    # đợi của AC-3, miền thay đổi thì kiểm tra lại các dãy giao với ô đó.
    def _propagate(
        self,
        domains: DomainMap,
        newly_assigned: Optional[Cell] = None,
    ) -> bool:
        if self.propagation == "none":
            return self._domains_nonempty(domains)
        if self.propagation == "forward_checking":
            if newly_assigned is None:
                return self._domains_nonempty(domains)
            return self.forward_check(newly_assigned, domains)
        return self.enforce_gac(domains)

    @staticmethod
    def _domains_nonempty(domains: Mapping[Cell, Set[int]]) -> bool:
        return all(bool(values) for values in domains.values())

    # ----- Heuristic chọn biến ---------------------------------------------

    # MRV chọn trước biến có miền giá trị nhỏ nhất (fail-first), để sớm phát
    # hiện nhánh dễ mâu thuẫn. Nếu MRV hòa, heuristic Degree ưu tiên ô có
    # nhiều láng giềng chưa gán nhất.
    def _select_unassigned_variable(
        self,
        assignment: Mapping[Cell, int],
        domains: Mapping[Cell, Set[int]],
    ) -> Cell:
        unassigned = [
            cell for cell in self.csp.variables if cell not in assignment
        ]

        if not self.use_mrv:
            return unassigned[0]

        min_size = min(len(domains[cell]) for cell in unassigned)
        candidates = [
            cell for cell in unassigned if len(domains[cell]) == min_size
        ]

        if self.use_degree and len(candidates) > 1:
            # Chỉ đếm các láng giềng chưa được gán giá trị.
            max_degree = max(
                sum(
                    1 for neighbor in self.csp.neighbors[cell]
                    if neighbor not in assignment
                )
                for cell in candidates
            )
            candidates = [
                cell for cell in candidates
                if sum(
                    1 for neighbor in self.csp.neighbors[cell]
                    if neighbor not in assignment
                ) == max_degree
            ]

        # Phá hòa ổn định giúp các lần chạy cho kết quả nhất quán.
        return min(candidates)

    # ----- Heuristic sắp xếp giá trị ---------------------------------------

    def _lcv_score(
        self,
        variable: Cell,
        value: int,
        assignment: Mapping[Cell, int],
        domains: Mapping[Cell, Set[int]],
    ) -> int:
        """Đếm số giá trị ở các biến láng giềng bị loại nếu gán giá trị này."""
        trial = dict(assignment)
        trial[variable] = value
        eliminated = 0

        for run in self.board.runs_by_cell[variable]:
            position = run.cells.index(variable)
            supported = [
                candidate
                for candidate in run.valid_tuples
                if candidate[position] == value
                and all(
                    cell == variable
                    or (
                        cell not in assignment
                        and candidate[index] in domains[cell]
                    )
                    or (
                        cell in assignment
                        and trial[cell] == candidate[index]
                    )
                    for index, cell in enumerate(run.cells)
                )
            ]
            if not supported:
                return 10**9

            for index, cell in enumerate(run.cells):
                if cell == variable or cell in assignment:
                    continue
                supported_values = {
                    candidate[index] for candidate in supported
                }
                eliminated += len(domains[cell] - supported_values)

        return eliminated

    # LCV thử trước giá trị gây ít hạn chế nhất lên miền của các biến láng
    # giềng, với hy vọng tìm được lời giải mà không cần quay lui nhiều.
    def _order_domain_values(
        self,
        variable: Cell,
        assignment: Mapping[Cell, int],
        domains: Mapping[Cell, Set[int]],
    ) -> List[int]:
        values = sorted(domains[variable])
        if not self.use_lcv or len(values) <= 1:
            return values
        return sorted(
            values,
            key=lambda value: (
                self._lcv_score(variable, value, assignment, domains),
                value,
            ),
        )

    # ----- Tìm kiếm quay lui -----------------------------------------------

    # Tìm kiếm quay lui: lần lượt thử các giá trị của biến được chọn. Mỗi
    # nhánh dùng bản sao miền giá trị để không ảnh hưởng đến nhánh khác.
    # Nếu phát hiện mâu thuẫn, quay lui và thử giá trị tiếp theo.
    def _backtrack(
        self,
        assignment: Assignment,
        domains: DomainMap,
        depth: int,
    ) -> Optional[Assignment]:
        self._depth = depth
        self.stats.expanded_nodes += 1

        if self.csp.is_complete(assignment):
            if self.csp.validate_solution(assignment):
                self.stats.solutions_found += 1
                self._emit(
                    "solution_found",
                    "A complete assignment satisfies every Kakuro run.",
                    depth=depth,
                )
                return dict(assignment)
            self.stats.contradictions += 1
            self._emit(
                "contradiction",
                "Complete assignment failed final validation.",
                depth=depth,
            )
            return None

        variable = self._select_unassigned_variable(assignment, domains)
        values = self._order_domain_values(variable, assignment, domains)

        self._emit(
            "variable_selected",
            f"Selected variable {variable}; domain={sorted(domains[variable])}.",
            cell=variable,
            depth=depth,
        )

        for value in values:
            self.stats.assignments_tried += 1
            self._emit(
                "assignment",
                f"Try {variable} = {value}.",
                cell=variable,
                value=value,
                before=domains[variable],
                after={value},
                depth=depth,
            )

            new_assignment = dict(assignment)
            new_assignment[variable] = value
            new_domains = self._copy_domains(domains)
            old_domain = set(new_domains[variable])
            new_domains[variable] = {value}

            self._emit(
                "domain_reduced",
                f"Decision: domain of {variable} restricted to {{{value}}}.",
                cell=variable,
                value=value,
                before=old_domain,
                after={value},
                depth=depth,
            )

            # Kiểm tra ngay các dãy đã có đủ thông tin về phép gán/miền để
            # xác định quyết định này có gây mâu thuẫn hay không.
            if not self._propagate(new_domains, newly_assigned=variable):
                self.stats.backtrack_count += 1
                self._emit(
                    "backtrack",
                    f"Backtrack from {variable} = {value} after contradiction.",
                    cell=variable,
                    value=value,
                    depth=depth,
                )
                continue

            result = self._backtrack(
                new_assignment, new_domains, depth + 1
            )
            if result is not None:
                return result

            self.stats.backtrack_count += 1
            self._emit(
                "backtrack",
                f"Backtrack from {variable} = {value}; deeper branch failed.",
                cell=variable,
                value=value,
                depth=depth,
            )

        return None

    # ----- API công khai ---------------------------------------------------

    def solve(self) -> Optional[Assignment]:
        """Giải câu đố, trả về {ô: chữ số} hoặc None nếu không có lời giải.

        Phép gán trả về được đảm bảo vượt qua validate_solution(). Có thể xem
        thống kê trong solver.stats sau khi gọi hàm này.
        """
        self.stats = SolverStats()
        self._event_count = 0
        self._depth = 0
        started = perf_counter()

        domains = self.csp.initial_domains()

        # Kiểm tra tính nhất quán ban đầu. GAC đặc biệt hữu ích ở bước này vì
        # có thể thu hẹp miền trước khi đưa ra quyết định tìm kiếm đầu tiên.
        if self.propagation == "gac":
            consistent = self.enforce_gac(domains)
        else:
            consistent = self._domains_nonempty(domains)

        solution: Optional[Assignment] = None
        if consistent:
            solution = self._backtrack({}, domains, 0)

        self.stats.elapsed_ms = (perf_counter() - started) * 1000.0

        if solution is not None:
            # Kiểm tra cuối để đảm bảo không bao giờ trả về phép gán sai.
            if not self.csp.validate_solution(solution):
                raise RuntimeError("Internal error: solver returned invalid solution.")
        else:
            self._emit(
                "search_failed",
                "No solution exists under the supplied Kakuro constraints.",
                depth=0,
            )

        return solution

    def solve_or_raise(self) -> Assignment:
        """Hàm tiện ích, phát sinh KakuroError nếu câu đố không có lời giải."""
        result = self.solve()
        if result is None:
            raise KakuroError("The Kakuro puzzle has no solution.")
        return result

    def get_domains_snapshot(self, domains: Mapping[Cell, Set[int]]) -> Dict[Cell, Tuple[int, ...]]:
        """Trả ảnh chụp miền giá trị không thể sửa trực tiếp để GUI sử dụng."""
        return {cell: tuple(sorted(values)) for cell, values in domains.items()}


def format_solution(solution: Optional[Mapping[Cell, int]]) -> str:
    """Định dạng phép gán thành danh sách tọa độ/giá trị ổn định."""
    if solution is None:
        return "No solution."
    return "\n".join(
        f"  cell {cell}: {value}"
        for cell, value in sorted(solution.items())
    )


def _demo() -> None:
    board = make_tiny_example_board()
    print(board.describe())

    solver = KakuroSolver(
        board,
        propagation="gac",
        use_mrv=True,
        use_degree=True,
        use_lcv=True,
    )
    solution = solver.solve()

    print("\nSolution:")
    print(format_solution(solution))
    print("\nStatistics:")
    for key, value in solver.stats.as_dict().items():
        print(f"  {key}: {value}")

    if solution is not None:
        assert solver.csp.validate_solution(solution)


if __name__ == "__main__":
    _demo()
