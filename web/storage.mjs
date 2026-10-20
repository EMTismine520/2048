// 存档与偏好设置。所有函数都接收一个存储对象，测试时注入内存版即可，不依赖浏览器。
export const SAVE_KEY = "2048-web-save-v1";
export const SOUND_KEY = "2048-web-sound-enabled";

/** 内存存储：给测试用，也可作为禁用 localStorage 时的降级方案。 */
export function createMemoryStore() {
  const map = new Map();
  return {
    getItem: key => (map.has(key) ? map.get(key) : null),
    setItem: (key, value) => { map.set(key, String(value)); },
    removeItem: key => { map.delete(key); }
  };
}

/**
 * 取当前环境的 localStorage。隐私模式或用户禁用存储时返回 null，
 * 调用方据此提示"浏览器未允许保存进度"，而不是静默丢失进度。
 */
export function createWebStore() {
  try {
    const store = globalThis.localStorage;
    store.setItem("__2048_probe__", "1");
    store.removeItem("__2048_probe__");
    return store;
  } catch {
    return null;
  }
}

export function saveGame(store, game) {
  if (!store) return false;
  try {
    store.setItem(SAVE_KEY, JSON.stringify(game.toJSON()));
    return true;
  } catch {
    return false;
  }
}

/** 读档成功返回 true；没有存档或存档损坏返回 false，损坏时顺带清掉坏数据。 */
export function loadGame(store, game) {
  if (!store) return false;
  let raw = null;
  try {
    raw = store.getItem(SAVE_KEY);
  } catch {
    return false;
  }
  if (!raw) return false;
  try {
    game.load(JSON.parse(raw));
    return true;
  } catch {
    try { store.removeItem(SAVE_KEY); } catch { /* 存储不可用时忽略损坏存档。 */ }
    return false;
  }
}

export function loadSoundEnabled(store) {
  try {
    return !store || store.getItem(SOUND_KEY) !== "0";
  } catch {
    return true;
  }
}

export function saveSoundEnabled(store, enabled) {
  if (!store) return false;
  try {
    store.setItem(SOUND_KEY, enabled ? "1" : "0");
    return true;
  } catch {
    return false;
  }
}
