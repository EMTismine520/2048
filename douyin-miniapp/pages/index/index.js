const { Game2048 } = require("../../utils/game");

const SAVE_KEY = "douyin-2048-save-v1";
const SOUND_KEY = "douyin-2048-sound-enabled";

function tileClass(value) {
  if (!value) return "tile empty";
  if (value > 2048) return "tile tile-large";
  return `tile tile-${value}`;
}

function boardRows(board) {
  return board.map(row => row.map(value => ({
    value,
    label: value ? String(value) : "",
    className: tileClass(value),
  })));
}

Page({
  data: {
    boardRows: [],
    score: 0,
    canUndo: false,
    won: false,
    gameOver: false,
    showWinDialog: false,
    showGameOverDialog: false,
    soundEnabled: true,
    status: "进度自动保存在此设备",
    gain: 0,
  },

  onLoad() {
    this.touchStart = null;
    this.game = new Game2048();
    this.audio = null;
    this.loadSoundPreference();
    this.createAudio();
    if (!this.loadGame()) this.syncView("新局已开始 · 进度自动保存");
  },

  onShow() {
    if (this.game) this.syncView();
  },

  onHide() {
    this.saveGame();
  },

  onUnload() {
    this.saveGame();
    if (this.audio && typeof this.audio.destroy === "function") this.audio.destroy();
  },

  createAudio() {
    try {
      this.audio = tt.createInnerAudioContext();
      this.audio.src = "/assets/win_A.wav";
      this.audio.autoplay = false;
    } catch (error) {
      this.audio = null;
    }
  },

  loadSoundPreference() {
    try {
      const stored = tt.getStorageSync(SOUND_KEY);
      this.setData({ soundEnabled: stored !== "0" });
    } catch (error) {
      this.setData({ soundEnabled: true });
    }
  },

  saveSoundPreference() {
    try {
      tt.setStorageSync(SOUND_KEY, this.data.soundEnabled ? "1" : "0");
    } catch (error) {
      // 存储失败不影响当前局游玩。
    }
  },

  saveGame() {
    if (!this.game) return false;
    try {
      tt.setStorageSync(SAVE_KEY, this.game.toJSON());
      return true;
    } catch (error) {
      this.setData({ status: "进度暂时无法保存" });
      return false;
    }
  },

  loadGame() {
    try {
      const stored = tt.getStorageSync(SAVE_KEY);
      if (!stored) return false;
      this.game.load(typeof stored === "string" ? JSON.parse(stored) : stored);
      this.syncView(this.game.gameOver ? "已恢复结束的本局" : "已恢复上次进度");
      if (this.game.gameOver) this.setData({ showGameOverDialog: true });
      return true;
    } catch (error) {
      try { tt.removeStorageSync(SAVE_KEY); } catch (removeError) { /* 忽略损坏存档清理失败。 */ }
      this.game = new Game2048();
      return false;
    }
  },

  syncView(status) {
    if (!this.game) return;
    const payload = {
      boardRows: boardRows(this.game.board),
      score: this.game.score,
      canUndo: this.game.history.length > 0,
      won: this.game.won,
      gameOver: this.game.gameOver,
      gain: this.game.lastMoveScore || 0,
    };
    if (status !== undefined) payload.status = status;
    this.setData(payload);
  },

  playMergeSound() {
    if (!this.data.soundEnabled || !this.audio) return;
    try {
      this.audio.stop();
      this.audio.seek(0);
      this.audio.play();
    } catch (error) {
      // 音频设备或自动播放策略失败时保持静音。
    }
  },

  move(direction) {
    if (this.data.showWinDialog || this.data.showGameOverDialog || this.game.gameOver) return;
    const wasWon = this.game.won;
    const changed = this.game.move(direction);
    this.syncView();
    if (!changed) {
      if (this.game.gameOver) {
        this.saveGame();
        this.setData({ status: "本局结束 · 可撤销或重新开始", showGameOverDialog: true });
      }
      return;
    }
    this.saveGame();
    this.setData({ status: "进度已自动保存" });
    if (this.game.lastMoveScore) this.playMergeSound();
    if (!wasWon && this.game.won) {
      this.setData({ showWinDialog: true });
    } else if (this.game.gameOver) {
      this.setData({ showGameOverDialog: true });
    }
  },

  onDirectionTap(event) {
    this.move(event.currentTarget.dataset.direction);
  },

  onKeyDown(event) {
    const key = String(event.key || event.code || "").toLowerCase();
    const directions = {
      arrowleft: "left", a: "left", arrowright: "right", d: "right",
      arrowup: "up", w: "up", arrowdown: "down", s: "down",
    };
    if (directions[key]) this.move(directions[key]);
    else if (key === "z") this.onUndo();
    else if (key === "r") this.onRestart();
  },

  onTouchStart(event) {
    const touch = event.touches && event.touches[0];
    if (touch) this.touchStart = { x: touch.clientX, y: touch.clientY };
  },

  onTouchMove() {
    // catchtouchmove prevents the page from跟随手势滚动。
  },

  onTouchEnd(event) {
    if (!this.touchStart) return;
    const touch = event.changedTouches && event.changedTouches[0];
    if (!touch) return;
    const dx = touch.clientX - this.touchStart.x;
    const dy = touch.clientY - this.touchStart.y;
    this.touchStart = null;
    if (Math.max(Math.abs(dx), Math.abs(dy)) < 24) return;
    const direction = Math.abs(dx) > Math.abs(dy)
      ? (dx > 0 ? "right" : "left")
      : (dy > 0 ? "down" : "up");
    this.move(direction);
  },

  onUndo() {
    if (this.data.showWinDialog) return;
    if (!this.game.undo()) return;
    this.setData({ showGameOverDialog: false });
    this.syncView("已撤销一步 · 进度已保存");
    this.saveGame();
  },

  onRestart() {
    this.game.reset();
    this.setData({ showWinDialog: false, showGameOverDialog: false });
    this.syncView("新局已开始 · 进度自动保存");
    this.saveGame();
  },

  onToggleSound() {
    const soundEnabled = !this.data.soundEnabled;
    this.setData({ soundEnabled, status: soundEnabled ? "合并音效已开启" : "合并音效已关闭" });
    this.saveSoundPreference();
  },

  onContinueWin() {
    this.setData({ showWinDialog: false });
    if (this.game.gameOver) this.setData({ showGameOverDialog: true });
  },

  onDialogRestart() {
    this.onRestart();
  },

  onDialogUndo() {
    this.onUndo();
  },

  onRevive() {
    if (!this.game.revive()) return;
    this.setData({ showGameOverDialog: false });
    this.syncView("已复活 · 删除了3个最小方块");
    this.saveGame();
  },

  noop() {},
});
