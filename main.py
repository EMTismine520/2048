"""2048 桌面小游戏启动入口。"""

import tkinter as tk

from ui import GameUI


def main() -> None:
    root = tk.Tk()
    GameUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
