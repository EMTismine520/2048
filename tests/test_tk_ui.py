"""实际 Tk 控件的冒烟测试；没有图形环境时自动跳过。"""

import random
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from game import Game2048
from storage import SaveManager
from ui import GameUI


class TkWidgetTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"当前环境无法创建 Tk 窗口：{error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.save_path = Path(temporary.name) / "state.json"
        self.game = Game2048(random.Random(42))
        self.ui = GameUI(self.root, self.game, save_path=str(self.save_path), sound_enabled=False)
        self.root.update_idletasks()

    def test_initial_widgets_and_score(self) -> None:
        self.assertEqual(self.root.title(), "2048 · 数字合成游戏")
        self.assertEqual(self.ui.score_label.cget("text"), "0")
        self.assertEqual(len(self.ui.board_canvas.find_all()), 18)
        self.assertEqual(self.ui.restart_button.cget("text"), "重新开始")

    def test_large_number_font_fits_cell(self) -> None:
        width = self.ui.BOARD_SIZE / self.game.SIZE - 2 * self.ui.CELL_MARGIN - 10
        for value in (2, 16, 128, 1024, 2048, 8192, 65536, 131072):
            with self.subTest(value=value):
                self.assertLessEqual(self.ui._tile_font(value).measure(str(value)), width)
                self.assertLessEqual(self.ui._tile_font(value).metrics("linespace"), width)

    def test_draw_updates_numbers_and_score(self) -> None:
        self.game.board = [[2048, 4096, 131072, 0], [0] * 4, [0] * 4, [0] * 4]
        self.game.score = 99999
        self.ui._draw_board()
        canvas = self.ui.board_canvas
        texts = [canvas.itemcget(item, "text") for item in canvas.find_all() if canvas.type(item) == "text"]
        self.assertEqual(texts, ["2048", "4096", "131072"])
        self.assertEqual(self.ui.score_label.cget("text"), "99999")
        self.assertEqual(len(canvas.find_all()), 19)

    def test_restart_button_resets_model_and_widgets(self) -> None:
        self.game.score = 99999
        self.game.won = True
        self.game.game_over = True
        self.ui.restart_button.invoke()
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.ui.score_label.cget("text"), "0")
        self.assertEqual(len(self.ui.board_canvas.find_all()), 18)

    def test_startup_restores_save_and_close_persists_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            source = Game2048(random.Random(17))
            source.score = 321
            SaveManager(path).save(source)
            root = tk.Tk()
            root.withdraw()
            try:
                restored = GameUI(root, save_path=str(path), sound_enabled=False)
                self.assertTrue(restored.loaded_from_save)
                self.assertEqual(restored.game.snapshot(), source.snapshot())
                restored.game.score = 654
                restored.close()
            finally:
                try:
                    root.destroy()
                except tk.TclError:
                    pass
            check = Game2048(random.Random(18))
            self.assertTrue(SaveManager(path).load(check))
            self.assertEqual(check.score, 654)

    def test_undo_button_and_reopen_restore_exact_progress(self) -> None:
        self.game.board = [[2, 2, 0, 0], [0] * 4, [0] * 4, [0] * 4]
        before = self.game.to_dict()
        self.assertTrue(self.game.move("left"))
        after = self.game.to_dict()
        self.ui._draw_board()
        self.assertEqual(self.ui.undo_button.cget("state"), "normal")
        self.ui.undo_button.invoke()
        self.assertEqual(self.game.to_dict(), before)
        self.assertEqual(self.ui.undo_button.cget("state"), "disabled")
        self.assertTrue(self.game.move("left"))
        self.assertEqual(self.game.to_dict(), after)
        self.ui._save_game()
        reopened_root = tk.Tk()
        reopened_root.withdraw()
        try:
            reopened = GameUI(reopened_root, save_path=str(self.save_path), sound_enabled=False)
            self.assertEqual(reopened.game.to_dict(), after)
            reopened.undo_button.invoke()
            self.assertEqual(reopened.game.to_dict(), before)
        finally:
            reopened_root.destroy()

    def test_window_fits_requested_layout(self) -> None:
        # 隐藏窗口尚未映射，检查配置的最小客户区尺寸。
        width, height = self.root.minsize()
        self.assertGreaterEqual(width, self.root.winfo_reqwidth())
        self.assertGreaterEqual(height, self.root.winfo_reqheight())

    def test_layout_and_tile_fonts_at_high_dpi(self) -> None:
        for scaling in (1.0, 2.0, 3.0):
            with self.subTest(scaling=scaling):
                root = tk.Tk()
                root.withdraw()
                try:
                    root.tk.call("tk", "scaling", scaling)
                    ui = GameUI(root, Game2048(random.Random(42)))
                    root.update_idletasks()
                    width, height = root.minsize()
                    self.assertGreaterEqual(width, root.winfo_reqwidth())
                    self.assertGreaterEqual(height, root.winfo_reqheight())
                    for value in (2, 2048, 131072):
                        self.assertLessEqual(ui._tile_font(value).measure(str(value)), 86)
                        self.assertLessEqual(ui._tile_font(value).metrics("linespace"), 86)
                finally:
                    root.destroy()


if __name__ == "__main__":
    unittest.main()
