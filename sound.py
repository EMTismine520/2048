"""仅在合并时播放指定的本地 WAV 音效。"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SoundManager:
    """Windows 异步播放合并音效；不可播放时保持静音。"""

    MERGE_SOUND_PATH = Path(__file__).resolve().parent / "audio_review" / "win_A.wav"

    def __init__(self, root: Any, enabled: bool = True) -> None:
        self.root = root
        self.enabled = enabled

    def play(self, event: str) -> None:
        if not self.enabled or event != "merge" or not self.MERGE_SOUND_PATH.is_file():
            return
        try:
            import winsound

            winsound.PlaySound(
                str(self.MERGE_SOUND_PATH),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
        except (ImportError, RuntimeError, AttributeError, OSError):
            pass
