"""Task 1 (N-Queens): thư viện + menu tương tác.

Chạy `python task1.py` để mở menu.
Notebook vẫn import được: from task1 import solve_one, benchmark
"""
import csv
import statistics
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from nqueens import NQueens, CNFEncoder, SATSolver, MinConflictsSolver

ALGORITHMS = ('glucose3', 'standard', 'max_conflict')
DEFAULT_SIZES = (4, 8, 16, 32, 64)
DEFAULT_OUTPUT = Path(__file__).resolve().parent / 'benchmark-output'
LABELS = {
    'glucose3': 'Glucose3 (SAT)',
    'standard': 'Min-Conflicts (standard)',
    'max_conflict': 'Min-Conflicts (max-conflict)',
}


# ---------- Thư viện (gọi được từ notebook / test) ----------

def solve_one(problem, algorithm, clauses=None, seed=2026,
              steps=10000, restarts=4, initial_rows=None):
    """Chạy 1 solver trên 1 bài toán, trả về Result."""
    if algorithm not in ALGORITHMS:
        raise ValueError(f'Thuật toán không hợp lệ: {algorithm}')
    if algorithm == 'glucose3':
        return SATSolver().solve(problem, clauses)
    solver = MinConflictsSolver(heuristic=(algorithm == 'max_conflict'),
                                max_steps=steps, restarts=restarts)
    return solver.solve(problem, seed, initial_rows)


def benchmark(sizes=DEFAULT_SIZES, trials=20,
              algorithms=ALGORITHMS, seed=2026,
              steps=10000, restarts=4, output=DEFAULT_OUTPUT):
    sizes = tuple(dict.fromkeys(sizes))
    algorithms = tuple(dict.fromkeys(algorithms))
    if not sizes or any(type(n) is not int or n < 4 for n in sizes):
        raise ValueError('Benchmark cần ít nhất một N nguyên và N >= 4.')
    if type(trials) is not int or trials < 1:
        raise ValueError('Số lượt chạy phải là số nguyên dương.')
    if not algorithms or any(name not in ALGORITHMS for name in algorithms):
        raise ValueError('Cần chọn ít nhất một thuật toán hợp lệ.')
    out = Path(output)
    records = []
    for n in sizes:
        problem = NQueens(n)
        encoder = CNFEncoder(problem)
        clause_count = encoder.clause_count()
        clauses, encoding_seconds = None, None
        if 'glucose3' in algorithms:
            start = perf_counter()
            clauses = encoder.encode()
            encoding_seconds = perf_counter() - start
            if len(clauses) != clause_count:
                raise RuntimeError('Số mệnh đề sinh ra không khớp công thức')
        for trial in range(trials):
            trial_seed = seed + trial
            for name in algorithms:
                result = solve_one(problem, name, clauses,
                                   trial_seed, steps, restarts)
                records.append(dict(
                    n=n, algorithm=name, trial=trial, seed=trial_seed,
                    clauses=clause_count, encoding_seconds=encoding_seconds,
                    success=result.solution is not None,
                    **asdict(result)))
        print(f'  N={n}: xong {trials} lượt / thuật toán')

    summary = _summarize(records, sizes, algorithms)
    out.mkdir(parents=True, exist_ok=True)
    _write_results(out, records, summary)
    return records, summary


def _summarize(records, sizes, algorithms):
    summary = []
    for n in sizes:
        for name in algorithms:
            group = [r for r in records if r['n'] == n and r['algorithm'] == name]
            times = [r['seconds'] for r in group]
            summary.append(dict(
                n=n, algorithm=name, clauses=group[0]['clauses'], trials=len(group),
                success_rate=sum(r['success'] for r in group) / len(group),
                mean_seconds=statistics.mean(times),
                median_seconds=statistics.median(times),
                stdev_seconds=statistics.stdev(times) if len(times) > 1 else 0,
                mean_steps=statistics.mean(r['steps'] for r in group),
                median_steps=statistics.median(r['steps'] for r in group),
                trials_with_restart=sum(r['attempts'] > 1 for r in group)))
    return summary


def _write_results(out, records, summary):
    for filename, rows in (('raw.csv', records), ('summary.csv', summary)):
        with (out / filename).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


# ---------- Hàm hỗ trợ menu ----------

def _ask(prompt, default):
    raw = input(f'  {prompt} [{default}]: ').strip()
    return default if raw == '' else raw


def _ask_int(prompt, default, minimum=1):
    while True:
        try:
            value = int(_ask(prompt, default))
        except ValueError:
            print('  ! Cần nhập số nguyên.')
            continue
        if value < minimum:
            print(f'  ! Giá trị phải >= {minimum}.')
            continue
        return value


# ---------- Các hành động của menu ----------

def _do_solve(algorithm):
    n = _ask_int('Nhập N', 8)
    problem = NQueens(n)
    print(f'  Đang giải N={n} bằng {LABELS[algorithm]}...')
    result = solve_one(problem, algorithm)
    if result.solution is not None:
        print(problem.board(result.solution))
        print(f'  Thời gian: {result.seconds * 1000:.3f} ms')
        if result.steps:
            print(f'  Số bước: {result.steps} (khởi tạo {result.attempts} lần)')
    elif algorithm == 'glucose3':
        print(f'  Bàn cờ N={n} vô nghiệm (UNSAT).')
    else:
        print('  Không tìm được nghiệm (hết ngân sách).')


def _do_benchmark():
    trials = _ask_int('Số trials mỗi N', 20)
    raw = _ask('Các N (cách nhau bởi dấu phẩy)', '4,8,16,32,64')
    try:
        sizes = list(dict.fromkeys(int(x.strip()) for x in raw.split(',')))
    except ValueError:
        print('  ! Danh sách N không hợp lệ. Ví dụ: 4,8,16.')
        return
    if any(n < 4 for n in sizes):
        print('  ! Benchmark yêu cầu mọi N >= 4.')
        return
    print(f'  Chạy: N={sizes}, trials={trials}')
    benchmark(sizes=sizes, trials=trials)
    print(f'  Xong. Xem raw.csv và summary.csv trong {DEFAULT_OUTPUT}')


# ---------- Menu chính ----------

MENU = [
    ('Giải bằng Glucose3 (SAT)', lambda: _do_solve('glucose3')),
    ('Giải bằng Min-Conflicts (standard)', lambda: _do_solve('standard')),
    ('Giải bằng Min-Conflicts (max-conflict)', lambda: _do_solve('max_conflict')),
    ('Chạy benchmark đầy đủ', _do_benchmark),
]


def main():
    while True:
        print()
        print('=' * 44)
        print('  N-QUEENS - TASK 1')
        print('=' * 44)
        for i, (label, _) in enumerate(MENU, start=1):
            print(f'  {i}. {label}')
        print('  0. Thoát')
        print('-' * 44)
        choice = input('  Chọn: ').strip()

        if choice == '0':
            print('  Tạm biệt.')
            return
        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
            print('  ! Lựa chọn không hợp lệ.')
            continue
        try:
            MENU[int(choice) - 1][1]()
        except Exception as exc:
            print(f'  ! Lỗi: {exc}')


if __name__ == '__main__':
    main()
