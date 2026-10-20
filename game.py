"""2048 游戏规则，不依赖图形界面。"""

from __future__ import annotations

import random
from typing import Any


class Game2048:
    """维护棋盘、分数，以及本局的胜利和结束状态。"""

    SIZE = 4
    DIRECTIONS = frozenset({"left", "right", "up", "down"})

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng if rng is not None else random.Random()
        self.board: list[list[int]] = []
        self.score = 0
        self.won = False
        self.game_over = False
        self.last_move_score = 0
        self._history: list[dict[str, Any]] = []
        self.reset()

    def reset(self) -> None:
        """开始新局，并在不同的空位生成两个初始方块。"""
        self.board = [[0] * self.SIZE for _ in range(self.SIZE)]
        self.score = 0
        self.won = False
        self.game_over = False
        self.last_move_score = 0
        self._history.clear()
        self._spawn_tile()
        self._spawn_tile()

    def move(self, direction: str) -> bool:
        """执行一次移动；仅在棋盘发生变化时返回 True 并生成新方块。"""
        if direction not in self.DIRECTIONS:
            raise ValueError(f"未知方向：{direction!r}")
        if self.game_over:
            return False

        next_board = [row[:] for row in self.board]
        gained = 0
        for index in range(self.SIZE):
            positions = self._line_positions(direction, index)
            line = [self.board[row][column] for row, column in positions]
            merged, line_score = self._merge_line(line)
            gained += line_score
            for (row, column), value in zip(positions, merged):
                next_board[row][column] = value

        if next_board == self.board:
            self.last_move_score = 0
            self.game_over = not self.can_move()
            return False

        self._history.append(self._state_snapshot())
        self.board = next_board
        self.score += gained
        self.last_move_score = gained
        self.won = self.won or any(
            value >= 2048 for row in self.board for value in row
        )
        self._spawn_tile()
        self.game_over = not self.can_move()
        return True

    def can_undo(self) -> bool:
        """是否存在可以恢复的上一步状态。"""
        return bool(self._history)

    def undo(self) -> bool:
        """恢复最近一次有效移动前的状态。"""
        if not self._history:
            return False
        self._restore_snapshot(self._history.pop(), restore_rng=True)
        self.last_move_score = 0
        return True

    def revive(self) -> bool:
        """删除3个最小值的方块以继续游戏；仅在游戏结束时可用。"""
        if not self.game_over:
            return False

        # 找出最小的非零值
        min_value = min(
            (value for row in self.board for value in row if value),
            default=0
        )
        if min_value == 0:
            return False

        # 收集所有等于最小值的位置
        positions = [
            (row, col)
            for row in range(self.SIZE)
            for col in range(self.SIZE)
            if self.board[row][col] == min_value
        ]

        # 随机删除最多3个
        self.rng.shuffle(positions)
        for row, col in positions[:3]:
            self.board[row][col] = 0

        self.game_over = False
        self.last_move_score = 0
        return True

    def snapshot(self) -> dict[str, Any]:
        """返回不含随机数和撤销历史的可序列化当前状态。"""
        return {
            "board": [row[:] for row in self.board],
            "score": self.score,
            "won": self.won,
            "game_over": self.game_over,
        }

    def to_dict(self) -> dict[str, Any]:
        """返回可写入 JSON 的完整存档，包括撤销历史和随机数状态。"""
        return {
            "version": 1,
            **self.snapshot(),
            "history": [self._copy_snapshot(item) for item in self._history],
            "rng_state": self._json_ready(self.rng.getstate()),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], rng: random.Random | None = None) -> "Game2048":
        """从存档创建游戏；存档结构不合法时抛出 ValueError。"""
        game = cls(rng=rng)
        game.load_dict(data)
        return game

    def load_dict(self, data: dict[str, Any]) -> None:
        """将合法存档载入当前实例。"""
        if not isinstance(data, dict) or data.get("version", 1) != 1:
            raise ValueError("不支持的存档版本")
        current = self._validate_snapshot(data)
        history = data.get("history", [])
        if not isinstance(history, list):
            raise ValueError("撤销历史格式错误")
        validated_history = [self._validate_snapshot(item) for item in history]
        rng_state = None
        if "rng_state" in data:
            rng_state = self._parse_rng_state(data["rng_state"])

        # 所有字段都验证成功后才修改当前实例，损坏存档不会污染正在玩的状态。
        self.board = current["board"]
        self.score = current["score"]
        self.won = current["won"]
        self.game_over = current["game_over"]
        self._history = validated_history
        if rng_state is not None:
            self.rng.setstate(rng_state)
        self.last_move_score = 0

    def _state_snapshot(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        snapshot["rng_state"] = self._json_ready(self.rng.getstate())
        return snapshot

    @staticmethod
    def _copy_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
        copied = {
            "board": [row[:] for row in snapshot["board"]],
            "score": snapshot["score"],
            "won": snapshot["won"],
            "game_over": snapshot["game_over"],
        }
        if "rng_state" in snapshot:
            copied["rng_state"] = Game2048._json_ready(snapshot["rng_state"])
        return copied

    def _restore_snapshot(self, snapshot: dict[str, Any], restore_rng: bool = False) -> None:
        validated = self._validate_snapshot(snapshot)
        self.board = validated["board"]
        self.score = validated["score"]
        self.won = validated["won"]
        self.game_over = validated["game_over"]
        if restore_rng and "rng_state" in snapshot:
            try:
                self.rng.setstate(self._tuple_from_json(snapshot["rng_state"]))
            except (TypeError, ValueError, OverflowError):
                raise ValueError("随机数状态格式错误") from None

    @classmethod
    def _validate_snapshot(cls, snapshot: Any) -> dict[str, Any]:
        if not isinstance(snapshot, dict):
            raise ValueError("游戏状态格式错误")
        board = snapshot.get("board")
        if (
            not isinstance(board, list)
            or len(board) != cls.SIZE
            or any(not isinstance(row, list) or len(row) != cls.SIZE for row in board)
            or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for row in board for value in row)
        ):
            raise ValueError("棋盘格式错误")
        score = snapshot.get("score")
        won = snapshot.get("won")
        game_over = snapshot.get("game_over")
        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            raise ValueError("分数格式错误")
        if not isinstance(won, bool) or not isinstance(game_over, bool):
            raise ValueError("游戏状态格式错误")
        validated = {
            "board": [row[:] for row in board],
            "score": score,
            "won": won,
            "game_over": game_over,
        }
        if "rng_state" in snapshot:
            cls._parse_rng_state(snapshot["rng_state"])
            validated["rng_state"] = cls._json_ready(snapshot["rng_state"])
        return validated

    @classmethod
    def _parse_rng_state(cls, value: Any) -> tuple[Any, ...]:
        try:
            state = cls._tuple_from_json(value)
            if not isinstance(state, tuple) or len(state) != 3:
                raise ValueError("随机数状态长度错误")
            random.Random().setstate(state)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("随机数状态格式错误") from None
        return state

    @staticmethod
    def _json_ready(value: Any) -> Any:
        if isinstance(value, tuple):
            return [Game2048._json_ready(item) for item in value]
        if isinstance(value, list):
            return [Game2048._json_ready(item) for item in value]
        return value

    @staticmethod
    def _tuple_from_json(value: Any) -> Any:
        if isinstance(value, list):
            return tuple(Game2048._tuple_from_json(item) for item in value)
        return value

    def can_move(self) -> bool:
        """存在空格或横向、纵向相邻同值方块时，仍可继续移动。"""
        for row in range(self.SIZE):
            for column in range(self.SIZE):
                value = self.board[row][column]
                if value == 0:
                    return True
                if column + 1 < self.SIZE and value == self.board[row][column + 1]:
                    return True
                if row + 1 < self.SIZE and value == self.board[row + 1][column]:
                    return True
        return False

    def _spawn_tile(self) -> bool:
        empty = [
            (row, column)
            for row in range(self.SIZE)
            for column in range(self.SIZE)
            if self.board[row][column] == 0
        ]
        if not empty:
            return False
        row, column = self.rng.choice(empty)
        self.board[row][column] = 2 if self.rng.random() < 0.9 else 4
        return True

    @classmethod
    def _line_positions(cls, direction: str, index: int) -> list[tuple[int, int]]:
        if direction == "left":
            return [(index, column) for column in range(cls.SIZE)]
        if direction == "right":
            return [(index, column) for column in range(cls.SIZE - 1, -1, -1)]
        if direction == "up":
            return [(row, index) for row in range(cls.SIZE)]
        return [(row, index) for row in range(cls.SIZE - 1, -1, -1)]

    @staticmethod
    def _merge_line(line: list[int]) -> tuple[list[int], int]:
        """从靠近移动方向的一侧合并；本次新生成的方块不再合并。"""
        values = [value for value in line if value]
        result: list[int] = []
        score = 0
        index = 0
        while index < len(values):
            if index + 1 < len(values) and values[index] == values[index + 1]:
                value = values[index] * 2
                result.append(value)
                score += value
                index += 2
            else:
                result.append(values[index])
                index += 1
        result.extend([0] * (len(line) - len(result)))
        return result, score
