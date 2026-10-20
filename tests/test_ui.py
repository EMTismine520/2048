"""界面事件测试；无需打开窗口或实际弹出对话框。"""

import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from game import Game2048
from ui import GameUI


class UIEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ui = GameUI.__new__(GameUI)
        self.ui.root = Mock()
        self.ui.game = Game2048(random.Random(42))
        self.ui._dialog_open = False
        self.ui._draw_board = Mock()
        self.ui.sound = Mock()

    def press(self, keysym: str, char: str = "") -> str | None:
        return self.ui._on_key_press(SimpleNamespace(keysym=keysym, char=char))

    def set_board(self, board: list[list[int]]) -> None:
        self.ui.game.board = [row[:] for row in board]

    def test_arrow_and_wasd_mapping(self) -> None:
        cases = {
            "Left": "left", "Right": "right", "Up": "up", "Down": "down",
            "a": "left", "d": "right", "w": "up", "s": "down",
            "A": "left", "D": "right", "W": "up", "S": "down",
        }
        for key, direction in cases.items():
            with self.subTest(key=key), patch.object(self.ui.game, "move", return_value=True) as move:
                self.assertEqual(self.press(key), "break")
                move.assert_called_once_with(direction)

    def test_unrelated_key_is_ignored(self) -> None:
        with patch.object(self.ui.game, "move") as move:
            self.assertIsNone(self.press("space", " "))
        move.assert_not_called()

    def test_z_key_undoes_and_redraws(self) -> None:
        self.set_board([[2, 2, 0, 0], [0] * 4, [0] * 4, [0] * 4])
        before = self.ui.game.snapshot()
        with patch.object(self.ui.game, "_spawn_tile"):
            self.ui.game.move("left")
        self.assertNotEqual(self.ui.game.snapshot(), before)
        self.ui._on_key_press(SimpleNamespace(keysym="z", char="z"))
        self.assertEqual(self.ui.game.snapshot(), before)
        self.ui._draw_board.assert_called()

    def test_sound_and_save_run_after_valid_move(self) -> None:
        storage = Mock()
        sound = Mock()
        self.ui.storage = storage
        self.ui.sound = sound
        self.set_board([[2, 2, 0, 0], [0] * 4, [0] * 4, [0] * 4])
        with patch.object(self.ui.game, "_spawn_tile"):
            self.press("Left")
        storage.save.assert_called_once_with(self.ui.game)
        sound.play.assert_called_once_with("merge")

    def test_win_dialog_appears_once_and_play_continues(self) -> None:
        self.set_board([[1024, 1024, 0, 0], [2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        with patch.object(self.ui.game, "_spawn_tile"), patch("ui.messagebox.showinfo") as show:
            self.press("Left")
            show.assert_called_once()
            self.assertEqual(show.call_args.args[0], "恭喜你！")
            self.press("Right")
            self.assertEqual(show.call_count, 1)
        self.assertTrue(self.ui.game.won)
        self.assertFalse(self.ui.game.game_over)
        self.assertFalse(self.ui._dialog_open)
        self.ui.sound.play.assert_called_once_with("merge")

    def test_move_without_merge_is_silent(self) -> None:
        self.set_board([[0, 2, 0, 0], [0] * 4, [0] * 4, [0] * 4])
        with patch.object(self.ui.game, "_spawn_tile"):
            self.press("Left")
        self.ui.sound.play.assert_not_called()

    def test_multiple_merges_play_once_and_undo_is_silent(self) -> None:
        self.set_board([[2, 2, 4, 4], [8, 8, 0, 0], [0] * 4, [0] * 4])
        with patch.object(self.ui.game, "_spawn_tile"):
            self.press("Left")
        self.assertEqual(self.ui.game.last_move_score, 28)
        self.ui.sound.play.assert_called_once_with("merge")
        self.ui.sound.play.reset_mock()
        self.ui.undo()
        self.ui.undo()
        self.ui.sound.play.assert_not_called()

    def test_invalid_move_and_restart_are_silent(self) -> None:
        self.set_board([[2, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4])
        self.press("Left")
        self.press("r")
        self.ui.sound.play.assert_not_called()

    def test_game_over_dialog_and_move_lock(self) -> None:
        self.set_board([[4, 2, 4, 0], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
        rng = Mock()
        rng.choice.return_value = (0, 0)
        rng.random.return_value = 0.0
        self.ui.game.rng = rng
        with patch("ui.messagebox.showinfo") as show:
            self.press("Right")
            show.assert_called_once()
            self.assertEqual(show.call_args.args[0], "游戏结束")
            with patch.object(self.ui.game, "move") as move:
                self.assertEqual(self.press("Left"), "break")
            move.assert_not_called()
            self.assertEqual(show.call_count, 1)
        self.ui.sound.play.assert_not_called()

    def test_locked_board_without_prior_flag_shows_game_over(self) -> None:
        self.set_board([[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
        with patch("ui.messagebox.showinfo") as show:
            self.press("Left")
        self.assertTrue(self.ui.game.game_over)
        show.assert_called_once()

    def test_restart_shortcut_resets_state_and_win_notification(self) -> None:
        for key in ("r", "R"):
            with self.subTest(key=key):
                self.ui.game.score = 100
                self.ui.game.won = True
                self.ui.game.game_over = True
                self.assertEqual(self.press(key), "break")
                self.assertEqual(self.ui.game.score, 0)
                self.assertFalse(self.ui.game.won)
                self.assertFalse(self.ui.game.game_over)
                self.assertEqual(sum(value != 0 for row in self.ui.game.board for value in row), 2)
                self.set_board([[1024, 1024, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
                with patch("ui.messagebox.showinfo") as show:
                    self.press("Left")
                show.assert_called_once()

    def test_dialog_blocks_reentrant_moves_and_restart(self) -> None:
        self.ui._dialog_open = True
        with patch.object(self.ui.game, "move") as move, patch.object(self.ui.game, "reset") as reset:
            self.assertEqual(self.press("Left"), "break")
            self.assertEqual(self.press("r"), "break")
            self.ui.new_game()
        move.assert_not_called()
        reset.assert_not_called()

    def test_dialog_guard_is_cleared_after_error(self) -> None:
        self.set_board([[1024, 1024, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        with patch("ui.messagebox.showinfo", side_effect=RuntimeError("dialog failed")):
            with self.assertRaises(RuntimeError):
                self.press("Left")
        self.assertFalse(self.ui._dialog_open)


if __name__ == "__main__":
    unittest.main()
