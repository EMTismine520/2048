"""验证仅播放用户选定的合并音效，不实际输出声音。"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from sound import SoundManager


class SoundTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Mock()
        self.sound = SoundManager(self.root)
        self.backend = SimpleNamespace(
            PlaySound=Mock(), SND_FILENAME=0x20000, SND_ASYNC=1, SND_NODEFAULT=2
        )
        backend_patch = patch.dict(sys.modules, {"winsound": self.backend})
        backend_patch.start()
        self.addCleanup(backend_patch.stop)

    def test_merge_uses_selected_wav_asynchronously(self) -> None:
        expected = Path(__file__).resolve().parents[1] / "audio_review" / "win_A.wav"
        self.assertTrue(expected.is_file())
        self.sound.play("merge")
        self.backend.PlaySound.assert_called_once_with(str(expected), 0x20003)
        self.root.bell.assert_not_called()

    def test_other_events_are_silent(self) -> None:
        for event in ("move", "undo", "win", "game_over", "unknown"):
            self.sound.play(event)
        self.backend.PlaySound.assert_not_called()
        self.root.bell.assert_not_called()

    def test_disabled_or_missing_sound_is_silent(self) -> None:
        self.sound.enabled = False
        self.sound.play("merge")
        self.sound.enabled = True
        with patch.object(Path, "is_file", return_value=False):
            self.sound.play("merge")
        self.backend.PlaySound.assert_not_called()
        self.root.bell.assert_not_called()

    def test_unavailable_backend_does_not_play_system_bell(self) -> None:
        with patch.dict(sys.modules, {"winsound": None}):
            self.sound.play("merge")
        self.backend.PlaySound.side_effect = RuntimeError("unavailable audio device")
        self.sound.play("merge")
        self.root.bell.assert_not_called()


if __name__ == "__main__":
    unittest.main()
