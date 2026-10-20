// 键盘与滑动手势的解析。纯函数部分不碰 DOM，可以用 node --test 直接测。

const KEY_DIRECTIONS = {
  arrowleft: "left", a: "left",
  arrowright: "right", d: "right",
  arrowup: "up", w: "up",
  arrowdown: "down", s: "down"
};

/** 触发一次移动所需的最小滑动距离（像素）。 */
export const SWIPE_THRESHOLD = 24;

export function keyToDirection(key) {
  return KEY_DIRECTIONS[String(key).toLowerCase()] ?? null;
}

/** 把一段位移解析成方向；位移不足阈值时返回 null。 */
export function swipeToDirection(dx, dy, threshold = SWIPE_THRESHOLD) {
  if (Math.max(Math.abs(dx), Math.abs(dy)) < threshold) return null;
  return Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "right" : "left") : (dy > 0 ? "down" : "up");
}

/** 绑定方向键 / WASD 移动，Z 撤销，R 重开。isBlocked 返回 true 时忽略按键。 */
export function bindKeyboard({ onDirection, onUndo, onRestart, isBlocked = () => false }) {
  document.addEventListener("keydown", event => {
    if (isBlocked()) return;
    const key = event.key.toLowerCase();
    const direction = keyToDirection(key);
    if (direction) {
      event.preventDefault();
      onDirection(direction);
    } else if (key === "z") {
      event.preventDefault();
      onUndo();
    } else if (key === "r") {
      event.preventDefault();
      onRestart();
    }
  });
}

/** 在棋盘上识别滑动手势，onDirection 只在实际触发移动时被调用。 */
export function bindSwipe(element, onDirection) {
  let pointerStart = null;
  element.addEventListener("pointerdown", event => {
    pointerStart = { x: event.clientX, y: event.clientY, id: event.pointerId };
    element.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  });
  element.addEventListener("pointerup", event => {
    if (!pointerStart || event.pointerId !== pointerStart.id) return;
    const { x, y } = pointerStart;
    pointerStart = null;
    const direction = swipeToDirection(event.clientX - x, event.clientY - y);
    if (!direction) return;
    onDirection(direction);
    event.preventDefault();
  });
  element.addEventListener("pointercancel", () => { pointerStart = null; });
}

/** 绑定方向按钮，data-direction 即方向。 */
export function bindDirectionButtons(onDirection) {
  document.querySelectorAll("[data-direction]").forEach(button => {
    button.addEventListener("click", () => onDirection(button.dataset.direction));
  });
}
