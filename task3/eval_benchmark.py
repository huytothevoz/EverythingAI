"""
eval_benchmark.py
=================
Chay thu solver tren bang 9x9 trong de bai va in thong ke.

Khong bat buoc cai thu vien ben ngoai. Chay:
    python eval_benchmark.py

Ghi chu: che do "none" co the rat cham tren bang lon, vi khong loc mien
truoc khi thu cac nhanh. Mac dinh chi so sanh GAC va Forward Checking.
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
    print(f"Co loi giai  : {solution is not None}")
    print(f"Loi giai hop le: {valid}")
    print(f"Thoi gian (ms): {wall_time_ms:.3f}")
    print(f"Nut mo rong   : {stats['expanded_nodes']}")
    print(f"So lan thu gan: {stats['assignments_tried']}")
    print(f"So lan quay lui: {stats['backtrack_count']}")
    print(f"So mien bi cat: {stats['domain_values_removed']}")
    print(f"So mau thuan  : {stats['contradictions']}")

    if solution is not None and valid:
        print("Bang ket qua (chi hien cac o trang):")
        print(format_solution(solution))

    return valid, stats


def main():
    print("=" * 66)
    print("KAKURO CSP - DANH GIA TEST CASE 9x9")
    print("=" * 66)

    results = []
    results.append(("GAC + MRV + Degree + LCV",
                    run_case("GAC + heuristic day du", "gac", True, True, True)))
    results.append(("Forward Checking + heuristics",
                    run_case("Forward Checking", "forward_checking", True, True, True)))

    print("\n" + "=" * 66)
    print("TOM TAT")
    for name, (valid, stats) in results:
        print(
            f"{name:38} | valid={valid!s:5} | "
            f"time={stats['elapsed_ms']:9.3f} ms | "
            f"nodes={stats['expanded_nodes']:5} | "
            f"backtracks={stats['backtrack_count']:5}"
        )

    if not all(valid for _, (valid, _) in results):
        raise SystemExit("Co cau hinh khong tim duoc loi giai hop le.")


if __name__ == "__main__":
    main()
