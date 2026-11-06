import unittest

from boards import make_demo_board
from kakuro_solver import KakuroBoard, KakuroSolver, RunConstraint


class SolveModeConfigurationTests(unittest.TestCase):
    def test_every_propagation_configuration_solves_and_reports_events(self):
        for propagation in ("gac", "forward_checking", "none"):
            with self.subTest(propagation=propagation):
                events = []
                solver = KakuroSolver(
                    make_demo_board(),
                    propagation=propagation,
                    event_callback=events.append,
                )
                solution = solver.solve()

                self.assertIsNotNone(solution)
                self.assertTrue(solver.csp.validate_solution(solution))
                self.assertGreater(solver.stats.expanded_nodes, 0)
                self.assertGreater(solver.stats.assignments_tried, 0)
                self.assertEqual(solver.stats.solutions_found, 1)
                self.assertTrue(any(event.kind == "assignment" for event in events))
                self.assertTrue(any(event.kind == "solution_found" for event in events))
                if propagation != "none":
                    self.assertGreater(solver.stats.propagation_calls, 0)
                    self.assertTrue(any(event.kind == "domain_reduced" for event in events))

    def test_backtracking_configuration_emits_real_backtrack_events(self):
        board = KakuroBoard(
            [
                RunConstraint("A1", [(1, 1), (1, 2)], 3, "across"),
                RunConstraint("A2", [(2, 1), (2, 2)], 7, "across"),
                RunConstraint("D1", [(1, 1), (2, 1)], 5, "down"),
                RunConstraint("D2", [(1, 2), (2, 2)], 7, "down"),
            ]
        )
        events = []
        solver = KakuroSolver(
            board,
            propagation="none",
            use_mrv=False,
            use_degree=False,
            use_lcv=False,
            event_callback=events.append,
        )

        self.assertIsNone(solver.solve())
        self.assertGreater(solver.stats.backtrack_count, 0)
        self.assertGreater(solver.stats.contradictions, 0)
        self.assertTrue(any(event.kind == "backtrack" for event in events))


if __name__ == "__main__":
    unittest.main()
