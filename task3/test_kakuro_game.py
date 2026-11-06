import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import kakuro_game
from boards import make_demo_board
from kakuro_game import KakuroPlayGUI, PlaySession
from kakuro_gui import KakuroGUI
from main import MainMenu


class PlaySessionTests(unittest.TestCase):
    def setUp(self):
        self.session = PlaySession(make_demo_board())
        self.a, self.b, self.c, self.d = (1, 1), (1, 2), (2, 1), (2, 2)

    def test_incomplete_run_is_valid_until_a_rule_is_violated(self):
        self.assertTrue(self.session.enter_value(self.a, 1))
        self.assertEqual(self.session.evaluate_run(self.session.board.runs[0]).status, "valid")
        self.assertTrue(self.session.enter_value(self.b, 1))
        self.assertEqual(self.session.evaluate_run(self.session.board.runs[0]).status, "invalid")

    def test_entry_that_makes_sum_exceed_clue_is_invalid(self):
        self.session.enter_value(self.a, 3)
        self.session.enter_value(self.b, 2)
        state = self.session.evaluate_run(self.session.board.runs[0])
        self.assertFalse(state.valid)
        self.assertFalse(state.completed)

    def test_delete_and_undo_restore_previous_value(self):
        self.session.enter_value(self.a, 1)
        self.session.erase(self.a)
        self.assertNotIn(self.a, self.session.values)
        self.assertTrue(self.session.undo())
        self.assertEqual(self.session.values[self.a], 1)

    def test_hint_gives_one_local_deduction_without_filling_it(self):
        self.session.enter_value(self.a, 1)
        hint = self.session.hint()
        self.assertIn("A1", hint)
        self.assertIn("2", hint)
        self.assertEqual(self.session.hint_count, 1)
        self.assertEqual(self.session.hint_cell, self.b)
        self.assertNotIn(self.b, self.session.values)

    def test_check_distinguishes_valid_invalid_and_completed_runs(self):
        self.session.enter_value(self.a, 1)
        self.session.enter_value(self.b, 2)
        result = self.session.check()
        self.assertEqual(result["A1"].status, "completed")
        self.assertEqual(result["A2"].status, "valid")
        self.assertFalse(self.session.won)

        self.session.enter_value(self.c, 2)
        result = self.session.check()
        self.assertEqual(result["D1"].status, "invalid")

    def test_winning_requires_all_cells_and_all_run_constraints(self):
        for cell, value in zip((self.a, self.b, self.c, self.d), (1, 2, 3, 4)):
            self.session.enter_value(cell, value)
        self.assertTrue(self.session.won)
        self.assertTrue(all(state.completed for state in self.session.run_states.values()))
        self.session.check()
        self.assertEqual(self.session.check_count, 1)

    def test_clear_undo_and_restart_reset_gameplay_state(self):
        self.session.enter_value(self.a, 1)
        self.session.toggle_note(self.b, 3)
        self.session.clear_entries()
        self.assertFalse(self.session.values)
        self.assertFalse(any(self.session.notes.values()))
        self.assertTrue(self.session.undo())
        self.assertEqual(self.session.values[self.a], 1)
        self.assertEqual(self.session.notes[self.b], {3})

        self.session.check()
        self.session.hint()
        self.session.restart()
        self.assertFalse(self.session.values)
        self.assertFalse(self.session.won)
        self.assertEqual(self.session.check_count, 0)
        self.assertEqual(self.session.hint_count, 0)


class PlayModeUITests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def click(self, app, rect):
        app._handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
        )

    def test_play_mode_has_no_solver_dependency(self):
        app = KakuroPlayGUI(make_demo_board())
        self.assertNotIn("KakuroSolver", vars(kakuro_game))
        self.assertFalse(app.session.values)
        app._draw()

    def test_assignment_puzzle_starts_empty_with_all_white_cells_editable(self):
        app = KakuroPlayGUI()
        self.assertEqual(len(app.white_cells), 48)
        self.assertEqual(len(app.clues), 22)
        self.assertFalse(app.session.values)
        self.assertEqual(len(app.session.board.runs), 28)
        app._draw()

    def test_keyboard_entry_notes_navigation_and_restart(self):
        app = KakuroPlayGUI(make_demo_board())
        app.selected_cell = (1, 1)
        app._handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
        self.assertEqual(app.session.values[(1, 1)], 1)

        app._handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        self.assertEqual(app.selected_cell, (1, 2))
        app._handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n))
        app._handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2))
        self.assertEqual(app.session.notes[(1, 2)], {2})

        self.click(app, app.buttons["restart"])
        self.assertFalse(app.session.values)
        self.assertFalse(any(app.session.notes.values()))

    def test_check_button_highlights_invalid_run_and_hint_selects_cell(self):
        app = KakuroPlayGUI(make_demo_board())
        app.session.enter_value((1, 1), 1)
        app.session.enter_value((1, 2), 1)
        self.click(app, app.buttons["check"])
        self.assertEqual(app.session.check_count, 1)
        self.assertIn((1, 1), app.invalid_cells)
        self.assertIn((1, 2), app.invalid_cells)

        app.session.clear_entries()
        app.session.enter_value((1, 1), 1)
        self.click(app, app.buttons["hint"])
        self.assertEqual(app.session.hint_count, 1)
        self.assertEqual(app.selected_cell, (1, 2))

    def test_mode_menu_and_both_modes_can_return_to_menu(self):
        menu = MainMenu()
        menu._handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.buttons["play"].center)
        )
        self.assertEqual(menu.choice, "play")

        menu = MainMenu()
        menu._handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.buttons["how"].center)
        )
        self.assertEqual(menu.page, "how")
        menu._handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.back_button.center)
        )
        self.assertEqual(menu.page, "menu")
        menu._handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.buttons["about"].center)
        )
        self.assertEqual(menu.page, "about")
        menu._draw()

        play = KakuroPlayGUI(make_demo_board())
        self.click(play, play.menu_button)
        self.assertTrue(play.return_to_menu)

        solve = KakuroGUI(make_demo_board())
        self.click(solve, solve.mode_rect)
        self.assertTrue(solve.return_to_menu)


if __name__ == "__main__":
    unittest.main()
