"""使用 Tkinter 实现的 2048 中文桌面界面。"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

from game import Game2048
from sound import SoundManager
from storage import SaveManager


BACKGROUND = "#faf8ef"
BOARD_BACKGROUND = "#bbada0"
EMPTY_TILE = "#cdc1b4"
TEXT_DARK = "#776e65"
TEXT_LIGHT = "#f9f6f2"
ACCENT = "#8f7a66"

TILE_COLORS = {
    2: ("#eee4da", TEXT_DARK),
    4: ("#ede0c8", TEXT_DARK),
    8: ("#f2b179", TEXT_LIGHT),
    16: ("#f59563", TEXT_LIGHT),
    32: ("#f67c5f", TEXT_LIGHT),
    64: ("#f65e3b", TEXT_LIGHT),
    128: ("#edcf72", TEXT_LIGHT),
    256: ("#edcc61", TEXT_LIGHT),
    512: ("#edc850", TEXT_LIGHT),
    1024: ("#edc53f", TEXT_LIGHT),
    2048: ("#edc22e", TEXT_LIGHT),
}

KEY_DIRECTIONS = {
    "Left": "left",
    "a": "left",
    "A": "left",
    "Right": "right",
    "d": "right",
    "D": "right",
    "Up": "up",
    "w": "up",
    "W": "up",
    "Down": "down",
    "s": "down",
    "S": "down",
}


class GameUI:
    """把 Game2048 状态绘制到窗口，并处理键盘和按钮事件。"""

    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 690
    BOARD_SIZE = 448
    CELL_MARGIN = 8

    def __init__(
        self,
        root: tk.Tk,
        game: Game2048 | None = None,
        save_path: str | None = None,
        sound_enabled: bool = True,
    ) -> None:
        self.root = root
        self.storage = SaveManager(save_path)
        self.game = game if game is not None else Game2048()
        self.loaded_from_save = game is None and self.storage.load(self.game)
        self.sound = SoundManager(root, enabled=sound_enabled)
        self._dialog_open = False
        self._tile_fonts: dict[int, tkfont.Font] = {}
        self.font_family = self._choose_font_family()
        self._build_window()
        self._draw_board()
        # 绘制完成后再按实际字体尺寸确定窗口大小，防止高 DPI 下裁切。
        self.root.update_idletasks()
        width = max(self.WINDOW_WIDTH, self.root.winfo_reqwidth())
        height = max(self.WINDOW_HEIGHT, self.root.winfo_reqheight())
        self.root.minsize(width, height)
        self.root.geometry(f"{width}x{height}")
        self.root.bind_all("<KeyPress>", self._on_key_press)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _choose_font_family(self) -> str:
        available = set(tkfont.families(root=self.root))
        for family in ("Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC", "SimHei", "Arial"):
            if family in available:
                return family
        return "TkDefaultFont"

    def _build_window(self) -> None:
        self.root.title("2048 · 数字合成游戏")
        self.root.configure(bg=BACKGROUND)
        self.root.resizable(False, False)
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")

        content = tk.Frame(self.root, bg=BACKGROUND, padx=26, pady=22)
        content.pack(fill="both", expand=True)

        header = tk.Frame(content, bg=BACKGROUND)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="2048",
            bg=BACKGROUND,
            fg=TEXT_DARK,
            font=(self.font_family, 40, "bold"),
        )
        title.pack(side="left", anchor="center")

        score_box = tk.Frame(
            header,
            bg=BOARD_BACKGROUND,
            padx=20,
            pady=6,
            highlightthickness=0,
        )
        score_box.pack(side="right", anchor="center")
        tk.Label(
            score_box,
            text="得分",
            bg=BOARD_BACKGROUND,
            fg="#eee4da",
            font=(self.font_family, 11, "bold"),
        ).pack()
        self.score_label = tk.Label(
            score_box,
            text="0",
            bg=BOARD_BACKGROUND,
            fg="white",
            font=(self.font_family, 21, "bold"),
        )
        self.score_label.pack()

        instruction_row = tk.Frame(content, bg=BACKGROUND)
        instruction_row.pack(fill="x", pady=(11, 14))
        tk.Label(
            instruction_row,
            text="合并方块，挑战 2048！",
            bg=BACKGROUND,
            fg=TEXT_DARK,
            font=(self.font_family, 13, "bold"),
        ).pack(side="left")

        button_row = tk.Frame(instruction_row, bg=BACKGROUND)
        button_row.pack(side="right")

        self.undo_button = tk.Button(
            button_row,
            text="撤销一步",
            command=self.undo,
            bg="#a58b73",
            fg="white",
            activebackground="#8d745d",
            activeforeground="white",
            font=(self.font_family, 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            takefocus=False,
        )
        self.undo_button.pack(side="left", padx=(0, 8))

        self.restart_button = tk.Button(
            button_row,
            text="重新开始",
            command=self.new_game,
            bg=ACCENT,
            fg="white",
            activebackground="#766451",
            activeforeground="white",
            font=(self.font_family, 11, "bold"),
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            takefocus=False,
        )
        self.restart_button.pack(side="left")

        self.board_canvas = tk.Canvas(
            content,
            width=self.BOARD_SIZE,
            height=self.BOARD_SIZE,
            bg=BOARD_BACKGROUND,
            highlightthickness=0,
        )
        self.board_canvas.pack()

        tk.Label(
            content,
            text="方向键 / WASD 移动 · Z 撤销 · R 重新开始",
            bg=BACKGROUND,
            fg=TEXT_DARK,
            font=(self.font_family, 10),
            pady=16,
        ).pack()

        self.status_label = tk.Label(
            content,
            text="已恢复上次进度 · 按 Z 撤销一步" if self.loaded_from_save else "进度自动保存 · 按 Z 撤销一步",
            bg=BACKGROUND,
            fg=TEXT_DARK,
            font=(self.font_family, 9),
        )
        self.status_label.pack()

    def _tile_font(self, value: int) -> tkfont.Font:
        if value not in self._tile_fonts:
            size = 38 if value < 128 else 33 if value < 1024 else 27
            tile_font = tkfont.Font(root=self.root, family=self.font_family, size=size, weight="bold")
            max_size = self.BOARD_SIZE / Game2048.SIZE - 2 * self.CELL_MARGIN - 10
            while (
                tile_font.measure(str(value)) > max_size
                or tile_font.metrics("linespace") > max_size
            ) and size > 1:
                size -= 1
                tile_font.configure(size=size)
            self._tile_fonts[value] = tile_font
        return self._tile_fonts[value]

    def _draw_board(self) -> None:
        canvas = self.board_canvas
        canvas.delete("all")
        cell_size = self.BOARD_SIZE / Game2048.SIZE

        for row in range(Game2048.SIZE):
            for column in range(Game2048.SIZE):
                value = self.game.board[row][column]
                left = column * cell_size + self.CELL_MARGIN
                top = row * cell_size + self.CELL_MARGIN
                right = (column + 1) * cell_size - self.CELL_MARGIN
                bottom = (row + 1) * cell_size - self.CELL_MARGIN
                if value:
                    fill, foreground = TILE_COLORS.get(value, ("#3c3a32", TEXT_LIGHT))
                else:
                    fill, foreground = EMPTY_TILE, TEXT_DARK
                canvas.create_rectangle(
                    left,
                    top,
                    right,
                    bottom,
                    fill=fill,
                    outline=fill,
                )
                if value:
                    canvas.create_text(
                        (left + right) / 2,
                        (top + bottom) / 2,
                        text=str(value),
                        fill=foreground,
                        font=self._tile_font(value),
                    )

        self.score_label.configure(text=str(self.game.score))
        self._update_controls()

    def _update_controls(self) -> None:
        button = getattr(self, "undo_button", None)
        if button is not None:
            button.configure(state=tk.NORMAL if self.game.can_undo() else tk.DISABLED)

    def _save_game(self) -> bool:
        storage = getattr(self, "storage", None)
        if storage is None:
            return False
        status = getattr(self, "status_label", None)
        try:
            storage.save(self.game)
        except OSError:
            if status is not None:
                status.configure(text="存档未保存，请检查文件夹写入权限", fg="#c00000")
            return False
        if status is not None:
            status.configure(text="进度已自动保存 · 按 Z 撤销一步", fg=TEXT_DARK)
        return True

    def _play_sound(self, event: str) -> None:
        sound = getattr(self, "sound", None)
        if sound is not None:
            sound.play(event)

    def _on_key_press(self, event: tk.Event) -> str | None:
        if self._dialog_open:
            return "break"
        key = (event.char or "").lower()
        if event.keysym.lower() == "r" or key == "r":
            self.new_game()
            return "break"
        if event.keysym.lower() == "z" or key == "z":
            self.undo()
            return "break"

        direction = KEY_DIRECTIONS.get(event.keysym)
        if direction is None and event.char:
            direction = KEY_DIRECTIONS.get(event.char)
        if direction is None:
            return None
        if self.game.game_over:
            return "break"

        previously_won = self.game.won
        changed = self.game.move(direction)
        if changed:
            self._draw_board()
            self._save_game()
            if self.game.last_move_score:
                self._play_sound("merge")
        elif self.game.game_over:
            self._draw_board()
            self._save_game()

        # Tk 的模态对话框会运行嵌套事件循环，提示期间暂不处理游戏按键。
        self._dialog_open = True
        try:
            if not previously_won and self.game.won:
                messagebox.showinfo(
                    "恭喜你！", "你合成了 2048！\n关闭此提示后可以继续挑战。", parent=self.root
                )
            if self.game.game_over:
                if messagebox.askyesno(
                    "游戏结束",
                    f"最终得分：{self.game.score}\n\n是否使用复活？\n将删除3个最小的方块",
                    parent=self.root,
                ):
                    self.game.revive()
                    self._draw_board()
                    self._save_game()
        finally:
            self._dialog_open = False
        return "break"

    def new_game(self) -> None:
        if self._dialog_open:
            return
        self.game.reset()
        self._draw_board()
        self._save_game()

    def undo(self) -> None:
        """撤销一步并保存恢复后的状态。"""
        if self._dialog_open:
            return
        if not self.game.undo():
            self._update_controls()
            return
        self._draw_board()
        self._save_game()

    def close(self) -> None:
        """窗口关闭前保存当前游戏。"""
        self._save_game()
        self.root.destroy()
