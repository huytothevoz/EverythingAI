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
        start = perf_counter()
        encoder = CNFEncoder(p)
        clauses = encoder.encode()
        encoding = perf_counter()-start
        assert len(clauses) == encoder.clause_count()
        for trial in range(args.trials):
            for name in ('glucose3', 'standard', 'max_conflict'):
                result = (SATSolver().solve(p, clauses) if name == 'glucose3' else
                          MinConflictsSolver(name == 'max_conflict', args.steps,
                                             args.restarts).solve(p, args.seed+trial))
                records.append(dict(n=n, algorithm=name, trial=trial,
                                    seed=args.seed+trial, clauses=len(clauses),
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
        for name in ('glucose3', 'standard', 'max_conflict'):
            group = [r for r in records if r['n'] == n and r['algorithm'] == name]
            times = [r['seconds'] for r in group]
            summary.append(dict(n=n, algorithm=name, clauses=group[0]['clauses'],
                                trials=len(group), success_rate=sum(r['success'] for r in group)/len(group),
                                mean_seconds=statistics.mean(times),
                                median_seconds=statistics.median(times),
                                stdev_seconds=statistics.stdev(times) if len(times)>1 else 0,
                                mean_steps=statistics.mean(r['steps'] for r in group)))
    with (out/'summary.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    (out/'environment.json').write_text(json.dumps(dict(
        platform=platform.platform(), processor=platform.processor(),
        python=sys.version, parameters=vars(args)), indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Task 1 - N Queens')
    sub = parser.add_subparsers(dest='command', required=True)
    solve = sub.add_parser('solve')
    solve.add_argument('-n', type=int, default=8)
    solve.add_argument('--algorithm', choices=['glucose3', 'standard', 'max_conflict'], default='glucose3')
    bench = sub.add_parser('benchmark')
    bench.add_argument('--sizes', nargs='+', type=int, default=[4, 8, 16, 32, 64])
    bench.add_argument('--trials', type=int, default=20)
    bench.add_argument('--output', default=str(Path(__file__).parent/'results'))
    for cmd in (solve, bench):
        cmd.add_argument('--seed', type=int, default=2026)
        cmd.add_argument('--steps', type=int, default=10000)
        cmd.add_argument('--restarts', type=int, default=4)
    args = parser.parse_args()
    if args.steps < 0 or args.restarts < 0:
        parser.error('Budgets must be nonnegative')
    if args.command == 'benchmark':
        if args.trials < 1 or any(n < 4 for n in args.sizes):
            parser.error('Experiments require N >= 4 and trials >= 1')
        experiment(args)
    else:
        p = NQueens(args.n)
        result = (SATSolver().solve(p) if args.algorithm == 'glucose3' else
                  MinConflictsSolver(args.algorithm == 'max_conflict', args.steps,
                                     args.restarts).solve(p, args.seed))
        print(json.dumps(asdict(result), indent=2))
        if result.solution is not None:
            print(p.board(result.solution))
        elif args.algorithm == 'glucose3':
            print('UNSAT')
        else:
            print('Search budget exhausted; this does not prove UNSAT.')


if __name__ == '__main__':
    main()
