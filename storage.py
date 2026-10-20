"""2048 游戏存档读写。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from game import Game2048


class SaveManager:
    """以原子替换方式保存和读取本地游戏状态。"""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else Path(__file__).resolve().with_name("2048_save.json")

    def save(self, game: Game2048) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(json.dumps(game.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self.path)

    def load(self, game: Game2048) -> bool:
        """读取存档；文件不存在或损坏时保留当前游戏并返回 False。"""
        if not self.path.is_file():
            return False
        try:
            data: Any = json.loads(self.path.read_text(encoding="utf-8"))
            game.load_dict(data)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError, OverflowError):
            return False
        return True
