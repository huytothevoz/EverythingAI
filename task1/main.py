import argparse
import csv
import json
import platform
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from nqueens import NQueens, CNFEncoder, SATSolver, MinConflictsSolver


def experiment(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for n in args.sizes:
        p = NQueens(n)
        encoder = CNFEncoder(p)
        clause_count = encoder.clause_count()
        clauses = None
        encoding = None
        if 'glucose3' in args.algorithms:
            start = perf_counter()
            clauses = encoder.encode()
            encoding = perf_counter()-start
            if len(clauses) != clause_count:
                raise RuntimeError('Generated clause count disagrees with the formula')
        for trial in range(args.trials):
            for name in args.algorithms:
                result = (SATSolver().solve(p, clauses) if name == 'glucose3' else
                          MinConflictsSolver(name == 'max_conflict', args.steps,
                                             args.restarts).solve(p, args.seed+trial))
                records.append(dict(n=n, algorithm=name, trial=trial,
                                    seed=args.seed+trial, clauses=clause_count,
                                    encoding_seconds=encoding,
                                    success=result.solution is not None,
                                    **asdict(result)))
        print(f'N={n}: completed {args.trials} trials per algorithm', flush=True)
    with (out/'raw.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    summary = []
    for n in args.sizes:
        for name in args.algorithms:
            group = [r for r in records if r['n'] == n and r['algorithm'] == name]
            times = [r['seconds'] for r in group]
            summary.append(dict(n=n, algorithm=name, clauses=group[0]['clauses'],
                                trials=len(group), success_rate=sum(r['success'] for r in group)/len(group),
                                mean_seconds=statistics.mean(times),
                                median_seconds=statistics.median(times),
                                stdev_seconds=statistics.stdev(times) if len(times)>1 else 0,
                                mean_steps=statistics.mean(r['steps'] for r in group),
                                median_steps=statistics.median(r['steps'] for r in group),
                                trials_with_restart=sum(r['attempts'] > 1 for r in group)))
    with (out/'summary.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    (out/'environment.json').write_text(json.dumps(dict(
        platform=platform.platform(), processor=platform.processor(),
        python=sys.version, parameters=vars(args)), indent=2), encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Task 1 - N Queens')
    sub = parser.add_subparsers(dest='command', required=True)
    solve = sub.add_parser('solve')
    solve.add_argument('-n', type=int, default=8)
    solve.add_argument('--html', type=Path, help='Save a visual chessboard as an HTML file')
    algorithms = ['glucose3', 'standard', 'max_conflict']
    solve.add_argument('--algorithm', choices=algorithms, default='glucose3')
    cnf = sub.add_parser('cnf', help='Generate a DIMACS file for the given board size')
    cnf.add_argument('-n', type=int, default=4)
    cnf.add_argument('--output', required=True, type=Path)
    bench = sub.add_parser('benchmark')
    bench.add_argument('--sizes', nargs='+', type=int, default=[4, 8, 16, 32, 64])
    bench.add_argument('--trials', type=int, default=20)
    bench.add_argument('--algorithms', nargs='+', choices=algorithms, default=algorithms)
    bench.add_argument('--output', default=str(Path(__file__).parent/'results'))
    for cmd in (solve, bench):
        cmd.add_argument('--seed', type=int, default=2026)
        cmd.add_argument('--steps', type=int, default=10000)
        cmd.add_argument('--restarts', type=int, default=4)
    args = parser.parse_args(argv)
    if args.command in ('solve', 'cnf') and args.n < 1:
        parser.error('N must be a positive integer')
    if args.command == 'cnf':
        clauses = CNFEncoder(NQueens(args.n)).write_dimacs(args.output)
        print(f'{args.n**2} variables, {clauses} clauses: {args.output}')
        return
    if args.steps < 0 or args.restarts < 0:
        parser.error('Budgets must be nonnegative')
    if args.command == 'benchmark':
        if args.trials < 1 or any(n < 4 for n in args.sizes):
            parser.error('Experiments require N >= 4 and trials >= 1')
        args.sizes = list(dict.fromkeys(args.sizes))
        args.algorithms = list(dict.fromkeys(args.algorithms))
        experiment(args)
    else:
        p = NQueens(args.n)
        result = (SATSolver().solve(p) if args.algorithm == 'glucose3' else
                  MinConflictsSolver(args.algorithm == 'max_conflict', args.steps,
                                     args.restarts).solve(p, args.seed))
        print(json.dumps(asdict(result), indent=2))
        if result.solution is not None:
            if args.html is None:
                print(p.board(result.solution))
            else:
                p.write_html(result.solution, args.html)
                print(f'Board saved to {args.html.resolve()}')
        elif args.algorithm == 'glucose3':
            print('UNSAT')
        else:
            print('Search budget exhausted; this does not prove UNSAT.')


if __name__ == '__main__':
    main()
