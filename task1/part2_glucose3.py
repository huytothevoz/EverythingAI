"""Part 2: solve the N-Queens CNF using PySAT Glucose3."""
from time import perf_counter

from board import Result
from part1_cnf import CNFEncoder


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


if __name__ == '__main__':
    from sys import argv
    from main import main

    arguments = argv[1:]
    if arguments and arguments[0] == 'benchmark':
        main(['benchmark', *arguments[1:], '--algorithms', 'glucose3'])
    else:
        main(['solve', *arguments, '--algorithm', 'glucose3'])
