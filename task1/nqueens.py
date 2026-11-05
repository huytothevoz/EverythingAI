"""N-Queens: pairwise CNF and reproducible Min-Conflicts."""
from dataclasses import dataclass
from itertools import combinations
from random import Random
from time import perf_counter


@dataclass
class Result:
    solution: list[int] | None
    seconds: float
    steps: int = 0
    attempts: int = 1


class NQueens:
    def __init__(self, n):
        if not isinstance(n, int) or n < 1:
            raise ValueError('N must be a positive integer')
        self.n = n

    def valid(self, rows):
        n = self.n
        return (rows is not None and len(rows) == n
                and all(isinstance(r, int) and 0 <= r < n for r in rows)
                and len(set(rows)) == n
                and len({r-c for c, r in enumerate(rows)}) == n
                and len({r+c for c, r in enumerate(rows)}) == n)

    def board(self, rows):
        return '\n'.join(' '.join('Q' if rows[c] == r else '.'
                                for c in range(self.n)) for r in range(self.n))


class CNFEncoder:
    def __init__(self, problem):
        self.n = problem.n

    def variable(self, r, c):
        return r * self.n + c + 1

    def encode(self):
        n = self.n
        clauses = []
        groups = []
        for r in range(n):
            row = [self.variable(r, c) for c in range(n)]
            clauses.append(row)
            groups.append(row)
        groups.extend([self.variable(r, c) for r in range(n)] for c in range(n))
        for offset in range(-n+1, n):
            groups.append([self.variable(r, c) for r in range(n)
                           for c in range(n) if r-c == offset])
        for total in range(2*n-1):
            groups.append([self.variable(r, c) for r in range(n)
                           for c in range(n) if r+c == total])
        for group in groups:
            clauses.extend([-a, -b] for a, b in combinations(group, 2))
        return clauses

    def clause_count(self):
        n = self.n
        return n + n*n*(n-1) + n*(n-1)*(2*n-1)//3


class SATSolver:
    def solve(self, problem, clauses=None):
        from pysat.solvers import Glucose3
        if clauses is None:
            clauses = CNFEncoder(problem).encode()
        # Loading and CNF generation are excluded from solve-only timing.
        with Glucose3(bootstrap_with=clauses) as solver:
            start = perf_counter()
            sat = solver.solve()
            seconds = perf_counter() - start
            model = solver.get_model() if sat else None
        rows = None
        if model is not None:
            rows = [-1] * problem.n
            for literal in model:
                if literal > 0:
                    r, c = divmod(literal-1, problem.n)
                    rows[c] = r
            if not problem.valid(rows):
                raise RuntimeError('Invalid SAT solution')
        return Result(rows, seconds)


class MinConflictsSolver:
    """One variable per column. Heuristic selects a maximum-conflict queen."""
    def __init__(self, heuristic=False, max_steps=10000, restarts=4):
        if max_steps < 0 or restarts < 0:
            raise ValueError('Budgets must be nonnegative')
        self.heuristic = heuristic
        self.max_steps = max_steps
        self.restarts = restarts

    def solve(self, problem, seed=0):
        start = perf_counter()
        rng = Random(seed)
        n = problem.n
        steps = 0
        for attempt in range(self.restarts+1):
            rows = [rng.randrange(n) for _ in range(n)]
            rc, down, up = [0]*n, [0]*(2*n-1), [0]*(2*n-1)

            def update(c, r, delta):
                rc[r] += delta
                down[r-c+n-1] += delta
                up[r+c] += delta

            def conflicts(c, r):
                return rc[r] + down[r-c+n-1] + up[r+c]

            for c, r in enumerate(rows):
                update(c, r, 1)
            for step in range(self.max_steps+1):
                scores = [conflicts(c, r)-3 for c, r in enumerate(rows)]
                bad = [c for c in range(n) if scores[c] > 0]
                if not bad:
                    if not problem.valid(rows):
                        raise RuntimeError('Invalid local-search solution')
                    return Result(rows, perf_counter()-start, steps, attempt+1)
                if step == self.max_steps:
                    break
                if self.heuristic:
                    highest = max(scores[c] for c in bad)
                    bad = [c for c in bad if scores[c] == highest]
                c = rng.choice(bad)
                update(c, rows[c], -1)
                costs = [conflicts(c, r) for r in range(n)]
                best = min(costs)
                rows[c] = rng.choice([r for r in range(n) if costs[r] == best])
                update(c, rows[c], 1)
                steps += 1
        return Result(None, perf_counter()-start, steps, self.restarts+1)
