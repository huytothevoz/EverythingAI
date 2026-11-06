import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import main as application


class MainMenuTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def click(self, menu, name):
        menu._handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=menu.buttons[name].center,
            )
        )

    def test_all_required_main_menu_entries_and_information_screens(self):
        menu = application.MainMenu()
        self.assertEqual(set(menu.buttons), {"play", "solve", "how", "about", "exit"})
        menu._draw()

        self.click(menu, "how")
        self.assertEqual(menu.page, "how")
        menu._draw()
        menu._handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.back_button.center)
        )
        self.assertEqual(menu.page, "menu")

        self.click(menu, "about")
        self.assertEqual(menu.page, "about")
        menu._draw()
        menu._handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.back_button.center)
        )

        self.click(menu, "play")
        self.assertEqual(menu.choice, "play")
        menu = application.MainMenu()
        self.click(menu, "solve")
        self.assertEqual(menu.choice, "solve")
        menu = application.MainMenu()
        self.click(menu, "exit")
        self.assertEqual(menu.choice, "exit")

    def test_application_routes_between_modes_and_returns_to_main_menu(self):
        with (
            patch.object(application, "MainMenu") as menu_factory,
            patch.object(application, "KakuroPlayGUI") as play_factory,
            patch.object(application, "KakuroGUI") as solve_factory,
            patch.object(application.pygame, "quit") as pygame_quit,
        ):
            menu_factory.return_value.run.side_effect = ["play", "solve", "exit"]
            play_factory.return_value.run.return_value = True
            solve_factory.return_value.run.return_value = True

            application.main()

        self.assertEqual(menu_factory.call_count, 3)
        play_factory.assert_called_once_with()
        solve_factory.assert_called_once_with()
        pygame_quit.assert_called_once_with()

    def test_quit_event_exits_menu_without_launching_a_mode(self):
        menu = application.MainMenu()
        menu._handle_event(pygame.event.Event(pygame.QUIT))
        self.assertFalse(menu.running)
        self.assertEqual(menu.choice, "exit")


if __name__ == "__main__":
    unittest.main()
