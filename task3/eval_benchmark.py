"""
Chạy thử solver trên bảng 9x9 đề bài đưa ra và thực hiện in ra thống kê.
So sánh GAC và Forward Checking.
"""
from time import perf_counter

from boards import make_assignment_board
from kakuro_solver import KakuroSolver, format_solution


def run_case(label, propagation="gac", mrv=True, degree=True, lcv=True):
    board = make_assignment_board()
    solver = KakuroSolver(
        board,
        propagation=propagation,
        use_mrv=mrv,
        use_degree=degree,
        use_lcv=lcv,
    )

    started = perf_counter()
    solution = solver.solve()
    wall_time_ms = (perf_counter() - started) * 1000

    valid = solution is not None and solver.csp.validate_solution(solution)
    stats = solver.stats.as_dict()

    print(f"\n[{label}]")
    print(f"Propagation : {propagation}")
    print(f"MRV/Degree/LCV: {mrv}/{degree}/{lcv}")
    print(f"Có lời giải  : {solution is not None}")
    print(f"Lời giải hợp lệ?: {valid}")
    print(f"Thời gian giải (ms): {wall_time_ms:.3f}")
    print(f"Nút mở rộng   : {stats['expanded_nodes']}")
    print(f"Số lần thử gán: {stats['assignments_tried']}")
    print(f"Số lần quay lui: {stats['backtrack_count']}")
    print(f"Số miền bị cắt: {stats['domain_values_removed']}")
    print(f"Số mâu thuẫn  : {stats['contradictions']}")

    if solution is not None and valid:
        print("Bảng kết quả (các ô trắng):")
        print(format_solution(solution))

    return valid, stats


def main():
    print("KAKURO CSP - ĐÁNH GIÁ TEST CASE BẢNG 9*9")

    results = []
    results.append(("GAC + MRV + Degree + LCV",
                    run_case("GAC + heuristic đầy đủ", "gac", True, True, True)))
    results.append(("Forward Checking + heuristics",
                    run_case("Forward Checking", "forward_checking", True, True, True)))

    print("-Abstract-")
    for name, (valid, stats) in results:
        print(
            f"{name:38} | valid={valid!s:5} | "
            f"time={stats['elapsed_ms']:9.3f} ms | "
            f"nodes={stats['expanded_nodes']:5} | "
            f"backtracks={stats['backtrack_count']:5}"
        )

    if not all(valid for _, (valid, _) in results):
        raise SystemExit("Có cấu hình không tìm được lời giải hợp lệ.")


if __name__ == "__main__":
    main()
