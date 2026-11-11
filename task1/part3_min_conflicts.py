"""Part 3: standard and max-conflict variable selection."""
from random import Random
from time import perf_counter

from board import Result


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


if __name__ == '__main__':
    from sys import argv
    from main import main

    arguments = argv[1:]
    if arguments and arguments[0] == 'benchmark':
        main(['benchmark', *arguments[1:], '--algorithms', 'standard', 'max_conflict'])
    else:
        main(['solve', '--algorithm', 'standard', *arguments])
