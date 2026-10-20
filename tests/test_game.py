"""运行方式：python -m unittest discover -v。"""

import random
import unittest
from unittest.mock import Mock, patch

from game import Game2048


class GameTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = Game2048(random.Random(42))

    def set_board(self, rows: list[list[int]]) -> None:
        self.game.board = [row[:] for row in rows]
        self.game.score = 0
        self.game.won = False
        self.game.game_over = False

    def test_initial_board(self) -> None:
        tiles = [value for row in self.game.board for value in row if value]
        self.assertEqual(len(self.game.board), 4)
        self.assertTrue(all(len(row) == 4 for row in self.game.board))
        self.assertEqual(len(tiles), 2)
        self.assertTrue(all(value in (2, 4) for value in tiles))
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.game_over)

    def test_seeded_random_is_reproducible(self) -> None:
        other = Game2048(random.Random(42))
        self.assertEqual(self.game.board, other.board)
        for direction in ("left", "down", "right", "up"):
            self.game.move(direction)
            other.move(direction)
            self.assertEqual(self.game.board, other.board)
            self.assertEqual(self.game.score, other.score)

    def test_merge_line_rules(self) -> None:
        cases = [
            ([0, 0, 0, 0], [0, 0, 0, 0], 0),
            ([0, 2, 0, 0], [2, 0, 0, 0], 0),
            ([2, 0, 2, 0], [4, 0, 0, 0], 4),
            ([2, 2, 2, 0], [4, 2, 0, 0], 4),
            ([2, 2, 2, 2], [4, 4, 0, 0], 8),
            ([2, 2, 4, 0], [4, 4, 0, 0], 4),
            ([4, 4, 8, 8], [8, 16, 0, 0], 24),
            ([2, 4, 8, 16], [2, 4, 8, 16], 0),
        ]
        for line, expected, score in cases:
            with self.subTest(line=line):
                self.assertEqual(Game2048._merge_line(line), (expected, score))

    def test_all_four_directions(self) -> None:
        initial = [[2, 2, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        cases = {
            "left": [[4, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            "right": [[0, 0, 0, 4], [0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0]],
            "up": [[4, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            "down": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [4, 2, 0, 0]],
        }
        for direction, expected in cases.items():
            with self.subTest(direction=direction):
                self.set_board(initial)
                with patch.object(self.game, "_spawn_tile") as spawn:
                    self.assertTrue(self.game.move(direction))
                self.assertEqual(self.game.board, expected)
                self.assertEqual(self.game.score, 4)
                spawn.assert_called_once_with()

    def test_score_accumulates(self) -> None:
        self.set_board([[2, 2, 2, 2], [4, 4, 8, 8], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.game.score = 100
        with patch.object(self.game, "_spawn_tile"):
            self.game.move("left")
        self.assertEqual(self.game.score, 132)

    def test_invalid_move_does_not_spawn_or_score(self) -> None:
        board = [[2, 0, 0, 0], [4, 0, 0, 0], [8, 0, 0, 0], [16, 0, 0, 0]]
        self.set_board(board)
        self.game.score = 12
        with patch.object(self.game, "_spawn_tile") as spawn:
            self.assertFalse(self.game.move("left"))
        spawn.assert_not_called()
        self.assertEqual(self.game.board, board)
        self.assertEqual(self.game.score, 12)
        self.assertFalse(self.game.game_over)

    def test_spawn_position_and_probability_boundary(self) -> None:
        for draw, expected in ((0.0, 2), (0.899999, 2), (0.9, 4), (0.999999, 4)):
            with self.subTest(draw=draw):
                self.set_board([[2, 4, 8, 16], [4, 8, 16, 32], [8, 16, 32, 64], [16, 32, 64, 0]])
                rng = Mock()
                rng.choice.return_value = (3, 3)
                rng.random.return_value = draw
                self.game.rng = rng
                self.assertTrue(self.game._spawn_tile())
                rng.choice.assert_called_once_with([(3, 3)])
                rng.random.assert_called_once_with()
                self.assertEqual(self.game.board[3][3], expected)

    def test_spawn_returns_false_on_full_board(self) -> None:
        self.set_board([[2] * 4 for _ in range(4)])
        rng = Mock()
        self.game.rng = rng
        self.assertFalse(self.game._spawn_tile())
        rng.choice.assert_not_called()
        rng.random.assert_not_called()

    def test_effective_move_adds_exactly_one_tile(self) -> None:
        self.set_board([[0, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertTrue(self.game.move("left"))
        self.assertEqual(sum(value != 0 for row in self.game.board for value in row), 2)
        self.assertIn(sum(map(sum, self.game.board)), (4, 6))

    def test_can_move_with_empty_space_or_adjacent_matches(self) -> None:
        boards = [
            [[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 0]],
            [[2, 2, 8, 16], [4, 8, 16, 32], [8, 16, 32, 64], [16, 32, 64, 128]],
            [[2, 4, 8, 16], [2, 8, 16, 32], [8, 16, 32, 64], [16, 32, 64, 128]],
        ]
        for board in boards:
            with self.subTest(board=board):
                self.set_board(board)
                self.assertTrue(self.game.can_move())

    def test_game_over_blocks_further_moves(self) -> None:
        board = [[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]]
        self.set_board(board)
        self.assertFalse(self.game.can_move())
        with patch.object(self.game, "_spawn_tile") as spawn:
            self.assertFalse(self.game.move("left"))
            self.assertTrue(self.game.game_over)
            self.assertFalse(self.game.move("down"))
        spawn.assert_not_called()
        self.assertEqual(self.game.board, board)

    def test_game_over_detected_after_new_tile(self) -> None:
        self.set_board([[4, 2, 4, 0], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
        rng = Mock()
        rng.choice.return_value = (0, 0)
        rng.random.return_value = 0.0
        self.game.rng = rng
        self.assertTrue(self.game.move("right"))
        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.can_move())

    def test_win_and_continue(self) -> None:
        self.set_board([[1024, 1024, 0, 0], [2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        with patch.object(self.game, "_spawn_tile"):
            self.assertTrue(self.game.move("left"))
            self.assertTrue(self.game.won)
            self.assertEqual(self.game.score, 2052)
            self.assertFalse(self.game.game_over)
            self.assertTrue(self.game.move("right"))
        self.assertTrue(self.game.won)
        self.assertIn(2048, self.game.board[0])

    def test_reset_clears_all_state(self) -> None:
        self.game.score = 999
        self.game.won = True
        self.game.game_over = True
        self.game.reset()
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.game_over)
        self.assertEqual(sum(value != 0 for row in self.game.board for value in row), 2)

    def test_unknown_direction_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.game.move("diagonal")

    def test_revive_removes_smallest_tiles(self) -> None:
        """测试复活功能删除最小值的方块"""
        self.set_board([
            [2, 4, 8, 16],
            [4, 8, 16, 32],
            [2, 2, 64, 128],
            [8, 16, 32, 64]
        ])
        self.game.game_over = True
        self.assertTrue(self.game.revive())
        self.assertFalse(self.game.game_over)
        # 应该删除了3个值为2的方块
        twos = sum(1 for row in self.game.board for value in row if value == 2)
        self.assertEqual(twos, 0)

    def test_revive_fails_when_not_game_over(self) -> None:
        """测试在非游戏结束状态下复活失败"""
        self.set_board([[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.game.game_over = False
        self.assertFalse(self.game.revive())

    def test_revive_with_fewer_than_3_min_tiles(self) -> None:
        """测试最小值方块少于3个时全部删除"""
        self.set_board([
            [2, 4, 8, 16],
            [2, 8, 16, 32],
            [4, 8, 64, 128],
            [8, 16, 32, 64]
        ])
        self.game.game_over = True
        self.assertTrue(self.game.revive())
        # 只有2个2，应该全部删除
        twos = sum(1 for row in self.game.board for value in row if value == 2)
        self.assertEqual(twos, 0)


if __name__ == "__main__":
    unittest.main()
