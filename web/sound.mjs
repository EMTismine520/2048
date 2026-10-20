// 合并音效：播放与开关状态的持有者。app.mjs 只管调用，不关心 Audio 细节。
const SOUND_URL = "./audio_review/win_A.wav";

export function createSoundController() {
  const audio = new Audio(SOUND_URL);
  audio.preload = "auto";
  let enabled = true;

  return {
    get enabled() { return enabled; },
    setEnabled(next) { enabled = !!next; },
    toggle() { enabled = !enabled; return enabled; },
    play() {
      if (!enabled) return;
      audio.currentTime = 0;
      const playing = audio.play();
      // 自动播放被浏览器拦截时静默忽略，不影响游戏。
      if (playing && typeof playing.catch === "function") playing.catch(() => {});
    }
  };
}
