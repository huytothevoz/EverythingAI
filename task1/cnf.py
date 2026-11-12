"""propositional constraints and DIMACS encoding."""
from itertools import combinations


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
        differences = [[] for _ in range(2*n-1)]
        sums = [[] for _ in range(2*n-1)]
        for r in range(n):
            for c in range(n):
                variable = self.variable(r, c)
                differences[r-c+n-1].append(variable)
                sums[r+c].append(variable)
        groups.extend(differences)
        groups.extend(sums)
        for group in groups:
            clauses.extend([-a, -b] for a, b in combinations(group, 2))
        return clauses

    def clause_count(self):
        n = self.n
        return n + n*n*(n-1) + n*(n-1)*(2*n-1)//3

    
