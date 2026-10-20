import { Game2048 } from "./game.mjs";

const STORAGE_KEY = "2048-mobile-save-v1";
const SOUND_KEY = "2048-mobile-sound-enabled";
const boardElement = document.querySelector("#board");
const scoreElement = document.querySelector("#score");
const gainElement = document.querySelector("#gain");
const statusElement = document.querySelector("#status");
const announcementElement = document.querySelector("#announcement");
const undoButton = document.querySelector("#undo");
const restartButton = document.querySelector("#restart");
const clearButton = document.querySelector("#clear");
const soundButton = document.querySelector("#sound");
const dialog = document.querySelector("#dialog");
const dialogTitle = document.querySelector("#dialog-title");
const dialogDescription = document.querySelector("#dialog-description");
const dialogPrimary = document.querySelector("#dialog-primary");
const dialogSecondary = document.querySelector("#dialog-secondary");
const mergeSound = new Audio("./audio_review/win_A.wav");
mergeSound.preload = "auto";

let game = new Game2048();
let soundEnabled = true;
let pointerStart = null;

try { soundEnabled = localStorage.getItem(SOUND_KEY) !== "0"; } catch { /* 本地存储不可用时仍可游玩。 */ }

function setStatus(message) {
  statusElement.textContent = message;
  announcementElement.textContent = message;
}

function saveGame() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(game.toJSON()));
    return true;
  } catch {
    setStatus("浏览器未允许保存进度");
    return false;
  }
}

function loadGame() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return false;
    game.load(JSON.parse(raw));
    return true;
  } catch {
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* 本地存储不可用时忽略损坏存档。 */ }
    return false;
  }
}

function setSoundButton() {
  soundButton.textContent = soundEnabled ? "音效 开" : "音效 关";
  soundButton.setAttribute("aria-pressed", String(soundEnabled));
  soundButton.setAttribute("aria-label", `合并音效：${soundEnabled ? "开启" : "关闭"}`);
}

function playMergeSound() {
  if (!soundEnabled) return;
  mergeSound.currentTime = 0;
  const playing = mergeSound.play();
  if (playing && typeof playing.catch === "function") playing.catch(() => {});
}

function showGain(points) {
  if (!points) return;
  gainElement.textContent = `+${points}`;
  gainElement.classList.remove("show");
  void gainElement.offsetWidth;
  gainElement.classList.add("show");
}

function render() {
  boardElement.replaceChildren();
  for (const row of game.board) {
    const rowElement = document.createElement("div");
    rowElement.className = "board-row";
    rowElement.setAttribute("role", "row");
    for (const value of row) {
      const tile = document.createElement("div");
      tile.className = "tile";
      tile.setAttribute("role", "gridcell");
      tile.dataset.value = String(value);
      if (value) {
        tile.textContent = String(value);
        const digits = String(value).length;
        if (digits >= 3) tile.classList.add(`digits-${Math.min(digits, 6)}`);
        if (value > 2048) tile.classList.add("large");
        tile.setAttribute("aria-label", String(value));
      } else {
        tile.setAttribute("aria-label", "空格");
      }
      rowElement.append(tile);
    }
    boardElement.append(rowElement);
  }
  scoreElement.textContent = String(game.score);
  undoButton.disabled = game.history.length === 0;
  clearButton.disabled = game.clearUsed;
}

function closeDialog() {
  if (dialog.open) dialog.close();
}

function showDialog(kind) {
  if (kind === "win") {
    dialogTitle.textContent = "恭喜你！";
    dialogDescription.textContent = "你合成了 2048！\n关闭提示后可以继续挑战。";
    dialogPrimary.textContent = "继续挑战";
    dialogSecondary.textContent = "再来一局";
    dialogSecondary.hidden = false;
  } else {
    dialogTitle.textContent = "游戏结束";
    dialogDescription.textContent = `最终得分：${game.score}\n\n点击"复活"删除3个最小方块继续游戏`;
    dialogPrimary.textContent = "重新开始";
    dialogSecondary.textContent = "复活";
    dialogSecondary.hidden = false;
  }
  dialog.dataset.kind = kind;
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
  dialogPrimary.focus();
}

function performMove(direction) {
  if (dialog.open || game.gameOver) return;
  const wasWon = game.won;
  const changed = game.move(direction);
  render();
  if (!changed) {
    if (game.gameOver) {
      saveGame();
      setStatus("本局结束 · 重新开始后继续");
      showDialog("game-over");
    }
    return;
  }
  const saved = saveGame();
  if (saved) setStatus("进度已自动保存");
  showGain(game.lastMoveScore);
  if (game.lastMoveScore) playMergeSound();
  if (!wasWon && game.won) {
    showDialog("win");
  } else if (game.gameOver) {
    showDialog("game-over");
  }
}

function newGame() {
  game.reset();
  closeDialog();
  render();
  const saved = saveGame();
  if (saved) setStatus("新局已开始 · 进度自动保存");
  boardElement.focus({ preventScroll: true });
}

function undo() {
  if (dialog.open) return;
  if (!game.undo()) return;
  closeDialog();
  render();
  const saved = saveGame();
  if (saved) setStatus("已撤销一步 · 进度已保存");
  boardElement.focus({ preventScroll: true });
}

document.querySelectorAll("[data-direction]").forEach(button => {
  button.addEventListener("click", () => performMove(button.dataset.direction));
});
restartButton.addEventListener("click", newGame);
undoButton.addEventListener("click", undo);
clearButton.addEventListener("click", () => {
  if (game.clearTiles()) {
    render();
    saveGame();
    setStatus("已清除 · 删除了3个最小方块");
    boardElement.focus({ preventScroll: true });
  }
});
soundButton.addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  try { localStorage.setItem(SOUND_KEY, soundEnabled ? "1" : "0"); } catch { /* 只影响偏好记忆，不影响游戏。 */ }
  setSoundButton();
  setStatus(soundEnabled ? "合并音效已开启" : "合并音效已关闭");
});

dialogPrimary.addEventListener("click", () => {
  if (dialog.dataset.kind === "win") {
    closeDialog();
    if (game.gameOver) showDialog("game-over");
  } else newGame();
});
dialogSecondary.addEventListener("click", () => {
  if (dialog.dataset.kind === "game-over") {
    if (game.revive()) {
      closeDialog();
      render();
      saveGame();
      setStatus("已复活 · 删除了3个最小方块");
      boardElement.focus({ preventScroll: true });
    }
  } else {
    newGame();
  }
});
dialog.addEventListener("cancel", event => {
  if (dialog.dataset.kind === "game-over") event.preventDefault();
});

document.addEventListener("keydown", event => {
  if (dialog.open) return;
  const key = event.key.toLowerCase();
  const direction = { arrowleft: "left", a: "left", arrowright: "right", d: "right",
    arrowup: "up", w: "up", arrowdown: "down", s: "down" }[key];
  if (direction) {
    event.preventDefault();
    performMove(direction);
  } else if (key === "z") {
    event.preventDefault();
    undo();
  } else if (key === "r") {
    event.preventDefault();
    newGame();
  }
});

boardElement.addEventListener("pointerdown", event => {
  if (dialog.open || game.gameOver) return;
  pointerStart = { x: event.clientX, y: event.clientY, id: event.pointerId };
  boardElement.setPointerCapture?.(event.pointerId);
  event.preventDefault();
});
boardElement.addEventListener("pointerup", event => {
  if (!pointerStart || event.pointerId !== pointerStart.id) return;
  const dx = event.clientX - pointerStart.x;
  const dy = event.clientY - pointerStart.y;
  pointerStart = null;
  const distance = Math.max(Math.abs(dx), Math.abs(dy));
  if (distance < 24) return;
  const direction = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "right" : "left") : (dy > 0 ? "down" : "up");
  performMove(direction);
  event.preventDefault();
});
boardElement.addEventListener("pointercancel", () => { pointerStart = null; });

setSoundButton();
const restored = loadGame();
render();
if (restored) setStatus(game.gameOver ? "已恢复结束的本局" : "已恢复上次进度");
if (game.gameOver) setTimeout(() => showDialog("game-over"), 0);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(() => {});
