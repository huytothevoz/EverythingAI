import unittest
from itertools import product
from nqueens import NQueens, CNFEncoder, SATSolver, MinConflictsSolver


class Tests(unittest.TestCase):
    def test_encoding_semantics(self):
        # Exhaust all 2^16 assignments: CNF iff a valid four-queen board.
        p = NQueens(4)
        clauses = CNFEncoder(p).encode()
        for bits in product((False, True), repeat=16):
            actual = all(any(bits[abs(v)-1] == (v > 0) for v in clause)
                         for clause in clauses)
            cells = [(i//4, i%4) for i, bit in enumerate(bits) if bit]
            expected = (len(cells) == 4 and len({c for r, c in cells}) == 4
                        and p.valid([next(r for r, col in cells if col == c)
                                     for c in range(4)]))
            self.assertEqual(actual, expected)

    def test_sat(self):
        for n in (1, 2, 3, 4, 8, 16):
            p = NQueens(n)
            self.assertEqual(SATSolver().solve(p).solution is not None, n not in (2, 3))
            encoder = CNFEncoder(p)
            self.assertEqual(len(encoder.encode()), encoder.clause_count())

    def test_local_search(self):
        for heuristic in (False, True):
            for n in (4, 8, 32):
                solver = MinConflictsSolver(heuristic)
                a = solver.solve(NQueens(n), 17)
                b = solver.solve(NQueens(n), 17)
                self.assertTrue(NQueens(n).valid(a.solution))
                self.assertEqual((a.solution, a.steps), (b.solution, b.steps))
            self.assertIsNone(MinConflictsSolver(heuristic, 10, 0).solve(NQueens(3)).solution)

    def test_validation(self):
        self.assertFalse(NQueens(4).valid([0, 1, 2, 3]))
        self.assertFalse(NQueens(4).valid([-1, 1, 2, 3]))
        with self.assertRaises(ValueError):
            NQueens(0)

    def test_hand_worked_max_conflict_move(self):
        initial_rows = [1, 3, 3, 2]
        result = MinConflictsSolver(True, max_steps=1, restarts=0).solve(
            NQueens(4), initial_rows=initial_rows
        )
        self.assertEqual(result.solution, [1, 3, 0, 2])
        self.assertEqual(result.steps, 1)
        self.assertEqual(initial_rows, [1, 3, 3, 2])


if __name__ == '__main__':
    unittest.main()
