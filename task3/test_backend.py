import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

from boards import make_assignment_board
from kakuro_solver import KakuroSolver


class AssignmentBackendTests(unittest.TestCase):
    def test_assignment_board_solves_to_a_valid_solution_with_real_events_and_stats(self):
        board = make_assignment_board()
        events = []
        solver = KakuroSolver(board, event_callback=events.append)

        solution = solver.solve()

        self.assertIsNotNone(solution)
        self.assertTrue(solver.csp.validate_solution(solution))
        self.assertEqual(len(solution), len(board.cells))
        self.assertEqual(solver.stats.solutions_found, 1)
        self.assertGreater(solver.stats.expanded_nodes, 0)
        self.assertGreater(solver.stats.propagation_calls, 0)
        self.assertGreater(solver.stats.domain_values_removed, 0)
        self.assertTrue(any(event.kind == "domain_reduced" for event in events))
        self.assertTrue(any(event.kind == "assignment" for event in events))
        self.assertTrue(any(event.kind == "solution_found" for event in events))


if __name__ == "__main__":
    unittest.main()
