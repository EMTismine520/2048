// 装配层：把 game/storage/sound/dialog/render/input 连起来，只放"谁调谁"。
import { Game2048 } from "./game.mjs";
import { createWebStore, saveGame, loadGame, loadSoundEnabled, saveSoundEnabled } from "./storage.mjs";
import { createSoundController } from "./sound.mjs";
import { createDialog } from "./dialog.mjs";
import { renderBoard, renderScore, renderControls, showGain, setStatus } from "./render.mjs";
import { bindKeyboard, bindSwipe, bindDirectionButtons } from "./input.mjs";

const byId = id => document.getElementById(id);
const elements = {
  board: byId("board"), score: byId("score"), gain: byId("gain"),
  status: byId("status"), announcement: byId("announcement"),
  undo: byId("undo"), restart: byId("restart"), clear: byId("clear"), sound: byId("sound"),
  dialog: byId("dialog"), dialogTitle: byId("dialog-title"),
  dialogDescription: byId("dialog-description"),
  dialogPrimary: byId("dialog-primary"), dialogSecondary: byId("dialog-secondary")
};

const store = createWebStore();
const sound = createSoundController();
const game = new Game2048();
const dialog = createDialog(elements, {
  onPrimary: kind => (kind === "win" ? continueAfterWin() : newGame()),
  onSecondary: kind => (kind === "game-over" ? revive() : newGame())
});

function paint() {
  renderBoard(elements.board, game.board);
  renderScore(elements.score, game.score);
  renderControls({ undo: elements.undo, clear: elements.clear,
    historyLength: game.history.length, clearUsed: game.clearUsed });
}

function save(message) {
  if (!saveGame(store, game)) {
    setStatus(elements, "浏览器未允许保存进度");
    return false;
  }
  if (message) setStatus(elements, message);
  return true;
}

function focusBoard() {
  elements.board.focus({ preventScroll: true });
}

function updateSoundButton() {
  const on = sound.enabled;
  elements.sound.textContent = on ? "音效 开" : "音效 关";
  elements.sound.setAttribute("aria-pressed", String(on));
  elements.sound.setAttribute("aria-label", `合并音效：${on ? "开启" : "关闭"}`);
}

function performMove(direction) {
  if (dialog.isOpen() || game.gameOver) return;
  const wasWon = game.won;
  const changed = game.move(direction);
  paint();
  if (!changed) {
    if (game.gameOver) {
      save();
      setStatus(elements, "本局结束 · 重新开始后继续");
      dialog.show("game-over", { score: game.score });
    }
    return;
  }
  paint();
  save("进度已自动保存");
  showGain(elements.gain, game.lastMoveScore);
  if (game.lastMoveScore) sound.play();
  if (!wasWon && game.won) dialog.show("win");
  else if (game.gameOver) dialog.show("game-over", { score: game.score });
}

function continueAfterWin() {
  dialog.close();
  // 合成 2048 的那一步可能同时把棋盘走死，这时继续挑战就是重新开始。
  if (game.gameOver) dialog.show("game-over", { score: game.score });
}

function newGame() {
  game.reset();
  dialog.close();
  paint();
  save("新局已开始 · 进度自动保存");
  focusBoard();
}

function undo() {
  if (dialog.isOpen()) return;
  if (!game.undo()) return;
  dialog.close();
  paint();
  save("已撤销一步 · 进度已保存");
  focusBoard();
}

function revive() {
  if (!game.revive()) return;
  dialog.close();
  paint();
  save("已复活 · 删除了3个最小方块");
  focusBoard();
}

elements.restart.addEventListener("click", newGame);
elements.undo.addEventListener("click", undo);
elements.clear.addEventListener("click", () => {
  if (!game.clearTiles()) return;
  paint();
  save("已清除 · 删除了3个最小方块");
  focusBoard();
});
elements.sound.addEventListener("click", () => {
  const enabled = sound.toggle();
  saveSoundEnabled(store, enabled);
  updateSoundButton();
  setStatus(elements, enabled ? "合并音效已开启" : "合并音效已关闭");
});
bindDirectionButtons(performMove);
bindKeyboard({
  onDirection: performMove,
  onUndo: undo,
  onRestart: newGame,
  isBlocked: () => dialog.isOpen()
});
bindSwipe(elements.board, direction => {
  if (!dialog.isOpen() && !game.gameOver) performMove(direction);
});

sound.setEnabled(loadSoundEnabled(store));
updateSoundButton();
if (loadGame(store, game)) {
  setStatus(elements, game.gameOver ? "已恢复结束的本局" : "已恢复上次进度");
}
paint();
if (game.gameOver) setTimeout(() => dialog.show("game-over", { score: game.score }), 0);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(() => {});
