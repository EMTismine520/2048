// 把游戏状态画到 DOM 上。只负责"显示"，不判断规则，也不改游戏状态。

/** 重建棋盘。整块替换比逐个 diff 简单，4x4 的开销可以忽略。 */
export function renderBoard(boardElement, board) {
  boardElement.replaceChildren();
  for (const row of board) {
    const rowElement = document.createElement("div");
    rowElement.className = "board-row";
    rowElement.setAttribute("role", "row");
    for (const [column, value] of row.entries()) {
      rowElement.append(renderTile(value, column));
    }
    boardElement.append(rowElement);
  }
}

function renderTile(value, column) {
  const tile = document.createElement("div");
  tile.className = "tile";
  tile.setAttribute("role", "gridcell");
  tile.setAttribute("aria-colindex", String(column + 1));
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
  return tile;
}

export function renderScore(scoreElement, score) {
  scoreElement.textContent = String(score);
}

/** 同步按钮可用状态，和 game.mjs 里的规则字段一一对应。 */
export function renderControls({ undo, clear, historyLength, clearUsed }) {
  undo.disabled = historyLength === 0;
  clear.disabled = clearUsed;
}

/** 加分时在分数框右上角飘一个 "+n"。 */
export function showGain(element, points) {
  if (!points) return;
  element.textContent = `+${points}`;
  element.classList.remove("show");
  void element.offsetWidth;
  element.classList.add("show");
}

/** 同时写状态文字和屏幕阅读器播报区。 */
export function setStatus({ status, announcement }, message) {
  status.textContent = message;
  announcement.textContent = message;
}
