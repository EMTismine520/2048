"""存档和撤销的单元测试；音效测试位于 test_sound.py。"""

import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game import Game2048
from storage import SaveManager


class PersistenceTests(unittest.TestCase):
    def set_board(self, game: Game2048, board: list[list[int]]) -> None:
        game.board = [row[:] for row in board]
        game.score = 0
        game.won = False
        game.game_over = False
        game.last_move_score = 0
        game._history.clear()

    def test_undo_restores_board_score_and_flags(self) -> None:
        game = Game2048(random.Random(10))
        self.set_board(game, [[2, 2, 0, 0], [4, 0, 0, 0], [0] * 4, [0] * 4])
        before = game.snapshot()
        with patch.object(game, "_spawn_tile"):
            self.assertTrue(game.move("left"))
        self.assertTrue(game.can_undo())
        self.assertTrue(game.undo())
        self.assertEqual(game.snapshot(), before)
        self.assertFalse(game.can_undo())
        self.assertFalse(game.undo())

    def test_multiple_undo_and_new_move_drop_future_branch(self) -> None:
        game = Game2048(random.Random(11))
        self.set_board(game, [[2, 2, 0, 0], [0] * 4, [0] * 4, [0] * 4])
        with patch.object(game, "_spawn_tile"):
            game.move("left")
            game.move("right")
            self.assertTrue(game.undo())
            self.assertTrue(game.undo())
            self.assertFalse(game.undo())
            game.move("left")
            self.assertTrue(game.can_undo())

    def test_undo_restores_random_sequence_for_repeat_move(self) -> None:
        game = Game2048(random.Random(111))
        self.set_board(game, [[2, 2, 0, 0], [0] * 4, [0] * 4, [0] * 4])
        initial_state = game.rng.getstate()
        self.assertTrue(game.move("left"))
        first_result = game.snapshot()
        self.assertTrue(game.undo())
        self.assertEqual(game.rng.getstate(), initial_state)
        self.assertTrue(game.move("left"))
        self.assertEqual(game.snapshot(), first_result)

    def test_json_round_trip_preserves_rng_and_undo_history(self) -> None:
        game = Game2048(random.Random(12))
        with patch.object(game, "_spawn_tile"):
            game.move("left")
        restored = Game2048.from_dict(game.to_dict(), rng=random.Random(99))
        self.assertEqual(restored.snapshot(), game.snapshot())
        self.assertEqual(restored.can_undo(), game.can_undo())
        with patch.object(game, "_spawn_tile"), patch.object(restored, "_spawn_tile"):
            self.assertEqual(game.move("down"), restored.move("down"))
        self.assertEqual(restored.snapshot(), game.snapshot())

    def test_save_manager_loads_and_ignores_corrupt_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            manager = SaveManager(path)
            source = Game2048(random.Random(13))
            source.score = 123
            manager.save(source)
            target = Game2048(random.Random(14))
            self.assertTrue(manager.load(target))
            self.assertEqual(target.to_dict(), source.to_dict())
            path.write_text("{broken", encoding="utf-8")
            target.score = 456
            self.assertFalse(manager.load(target))
            self.assertEqual(target.score, 456)

    def test_invalid_semantic_save_does_not_partially_replace_game(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            target = Game2048(random.Random(16))
            original = target.snapshot()
            data = target.to_dict()
            data["board"] = [[2, 2, 2, 2]]
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertFalse(SaveManager(path).load(target))
            self.assertEqual(target.snapshot(), original)

    def test_save_file_is_valid_utf8_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            game = Game2048(random.Random(15))
            SaveManager(path).save(game)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 1)
            self.assertEqual(len(data["board"]), 4)

    def test_bad_history_and_rng_leave_entire_game_unchanged(self) -> None:
        game = Game2048(random.Random(21))
        before = game.to_dict()
        for invalid in ({"history": [None]}, {"rng_state": []}, {"rng_state": [3, [], None]}):
            with self.subTest(invalid=invalid):
                data = game.to_dict()
                data["score"] = 999
                data.update(invalid)
                with self.assertRaises(ValueError):
                    game.load_dict(data)
                self.assertEqual(game.to_dict(), before)

    def test_invalid_move_preserves_history_and_undo_after_loss(self) -> None:
        game = Game2048(random.Random(22))
        self.set_board(game, [[4, 2, 4, 0], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
        before = game.to_dict()
        with patch.object(game.rng, "choice", return_value=(0, 0)), patch.object(game.rng, "random", return_value=0.0):
            self.assertTrue(game.move("right"))
        self.assertTrue(game.game_over)
        history_length = len(game._history)
        self.assertFalse(game.move("left"))
        self.assertEqual(len(game._history), history_length)
        self.assertTrue(game.undo())
        self.assertEqual(game.to_dict(), before)


if __name__ == "__main__":
    unittest.main()
