import os
import queue
import threading
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from unittest.mock import ANY, patch

from boards import make_assignment_board, make_demo_board
from kakuro_gui import KakuroGUI, _RunCancelled, _RunControl, build_grid_layout
from kakuro_solver import SolverEvent


class GridLayoutTests(unittest.TestCase):
    def test_assignment_grid_is_derived_from_backend_runs(self):
        board = make_assignment_board()
        clues, white_cells = build_grid_layout(board)

        self.assertEqual(len(white_cells), 48)
        self.assertEqual(len(board.runs), 28)
        self.assertEqual(len(clues), 22)
        self.assertEqual(clues[(1, 1)]["across"], 22)
        self.assertEqual(clues[(0, 2)]["down"], 44)
        self.assertFalse(white_cells & set(clues))


class RunControlTests(unittest.TestCase):
    def test_callback_publishes_without_waiting_for_ui_playback(self):
        control = _RunControl()
        output = queue.Queue()
        event = SolverEvent(kind="assignment", message="test", cell=(1, 1), value=5)
        worker = threading.Thread(
            target=control.publish, args=(event, output), daemon=True
        )
        worker.start()
        worker.join(timeout=1)
        self.assertFalse(worker.is_alive())
        self.assertEqual(output.get_nowait(), ("event", event))

    def test_cancelled_callback_stops_without_publishing(self):
        control = _RunControl()
        output = queue.Queue()
        event = SolverEvent(kind="assignment", message="test", cell=(1, 1), value=5)
        control.cancel()

        with self.assertRaises(_RunCancelled):
            control.publish(event, output)
        self.assertTrue(output.empty())


class SolverPlaybackTests(unittest.TestCase):
    def setUp(self):
        self.gui = KakuroGUI(make_demo_board())

    def tearDown(self):
        if self.gui._control is not None:
            self.gui._control.cancel()
        pygame.quit()

    def click(self, rect):
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center
        )
        self.gui._handle_event(event)

    def test_backtracking_restores_domain_changes(self):
        cell = (1, 1)
        neighbor = (1, 2)
        self.gui._process_solver_event(
            SolverEvent(
                kind="assignment",
                message="assignment event",
                cell=cell,
                value=5,
            )
        )
        self.gui._process_solver_event(
            SolverEvent(
                kind="domain_reduced",
                message="Decision: domain restricted",
                cell=cell,
                before=tuple(range(1, 10)),
                after=(5,),
            )
        )
        self.gui._process_solver_event(
            SolverEvent(
                kind="domain_reduced",
                message="domain reduced",
                cell=neighbor,
                before=tuple(range(1, 10)),
                after=(2, 3),
                run_id="A1",
            )
        )
        self.gui._process_solver_event(
            SolverEvent(
                kind="backtrack",
                message="backtrack event",
                cell=cell,
                value=5,
            )
        )

        self.assertEqual(self.gui.domains[cell], set(range(1, 10)))
        self.assertEqual(self.gui.domains[neighbor], set(range(1, 10)))
        self.assertNotIn(cell, self.gui.assignments)

    def test_start_pause_step_and_resume_solve_on_worker(self):
        self.click(self.gui.start_rect)
        self.assertEqual(self.gui.status, "Đang giải")

        self.click(self.gui.pause_rect)
        self.assertTrue(self.gui.paused)
        before = self.gui._event_count
        self.click(self.gui.step_rect)

        deadline = time.monotonic() + 2
        while self.gui._event_count == before and time.monotonic() < deadline:
            self.gui._poll_messages()
            time.sleep(0.005)
        self.assertEqual(self.gui._event_count, before + 1)
        self.assertTrue(self.gui.paused)

        self.click(self.gui.pause_rect)
        self.assertFalse(self.gui.paused)
        self.gui.speed = 30
        deadline = time.monotonic() + 8
        while self.gui.status not in {"Đã tìm thấy nghiệm", "Không tìm thấy nghiệm", "Lỗi solver"}:
            self.gui._release_playback_event()
            self.gui._poll_messages()
            if time.monotonic() >= deadline:
                self.fail("Solver did not finish during event playback.")
            time.sleep(0.005)

        self.assertEqual(self.gui.status, "Đã tìm thấy nghiệm")
        self.assertEqual(len(self.gui._solution), 4)
        self.assertEqual(self.gui._stats["solutions_found"], 1)
        self.assertEqual(self.gui._event_count, len(self.gui._event_lines))
        self.gui._draw()

    def test_settings_change_before_start(self):
        self.click(self.gui.propagation_rect)
        self.assertEqual(self.gui.propagation, "forward_checking")
        self.click(self.gui.lcv_rect)
        self.assertFalse(self.gui.use_lcv)

    def test_start_passes_selected_solver_configuration(self):
        self.gui.propagation = "forward_checking"
        self.gui.use_mrv = False
        self.gui.use_degree = False
        self.gui.use_lcv = True
        with patch("kakuro_gui.KakuroSolver") as solver_factory:
            solver_factory.return_value.solve.return_value = None
            solver_factory.return_value.stats.as_dict.return_value = {
                "elapsed_ms": 1.0,
                "expanded_nodes": 0,
                "assignments_tried": 0,
                "backtrack_count": 0,
                "propagation_calls": 0,
                "propagation_revisions": 0,
                "domain_values_removed": 0,
                "contradictions": 0,
                "solutions_found": 0,
            }
            self.click(self.gui.start_rect)
            self.gui._worker.join(timeout=1)
            self.gui._poll_messages()

        solver_factory.assert_called_once_with(
            self.gui.board,
            propagation="forward_checking",
            use_mrv=False,
            use_degree=False,
            use_lcv=True,
            event_callback=ANY,
        )

    def test_reset_cancels_worker_and_restores_initial_state(self):
        self.click(self.gui.start_rect)
        self.click(self.gui.pause_rect)
        worker = self.gui._worker
        self.gui.domains[(1, 1)] = {5}
        self.click(self.gui.reset_rect)

        worker.join(timeout=1)
        self.assertFalse(worker.is_alive())
        self.assertEqual(self.gui.status, "Đã đặt lại")
        self.assertEqual(self.gui.domains[(1, 1)], set(range(1, 10)))
        self.assertEqual(self.gui._event_count, 0)
        self.assertTrue(self.gui._messages.empty())

    def test_speed_slider_changes_playback_rate(self):
        old_speed = self.gui.speed
        self.gui._handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=(self.gui.speed_track.right, self.gui.speed_track.centery),
            )
        )
        self.assertGreater(self.gui.speed, old_speed)
        self.assertLessEqual(self.gui.speed, 30)


if __name__ == "__main__":
    unittest.main()
