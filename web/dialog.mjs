// 游戏结束 / 胜利弹窗。文案集中在这里，切换平台或改措辞不用翻 app.mjs。

const DIALOGS = {
  win: {
    title: "恭喜你！",
    description: "你合成了 2048！\n关闭提示后可以继续挑战。",
    primary: "继续挑战",
    secondary: "再来一局"
  },
  "game-over": {
    title: "游戏结束",
    primary: "重新开始",
    secondary: "复活"
  }
};

const gameOverDescription = score => `最终得分：${score}\n\n点击"复活"删除3个最小方块继续游戏`;

/**
 * 创建弹窗控制器。show(kind, context) 中 game-over 需要 context.score 填描述。
 * onPrimary / onSecondary 收到当前的 kind，由调用方决定做什么。
 */
export function createDialog(elements, { onPrimary, onSecondary }) {
  const { dialog, title, description, primary, secondary } = elements;

  function close() {
    if (dialog.open) dialog.close();
    // dataset.kind 只是给按钮回调用的，关掉后必须清，否则"弹窗是否打开"会误判。
    delete dialog.dataset.kind;
  }

  function show(kind, context = {}) {
    const config = DIALOGS[kind];
    if (!config) throw new Error(`未知弹窗类型：${kind}`);
    title.textContent = config.title;
    description.textContent = config.description ?? gameOverDescription(context.score ?? 0);
    primary.textContent = config.primary;
    secondary.textContent = config.secondary;
    secondary.hidden = false;
    dialog.dataset.kind = kind;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.open = true;
    primary.focus();
  }

  primary.addEventListener("click", () => onPrimary(dialog.dataset.kind));
  secondary.addEventListener("click", () => onSecondary(dialog.dataset.kind));
  // 游戏结束必须二选一，不允许按 Esc 一关了事。
  dialog.addEventListener("cancel", event => {
    if (dialog.dataset.kind === "game-over") event.preventDefault();
  });

  return {
    show,
    close,
    /** 弹窗当前是否打开。dataset.kind 只在打开期间存在。 */
    isOpen: () => Boolean(dialog.dataset.kind)
  };
}
