// 与界面无关的规则。随机数状态随存档和撤销一起恢复。
export class Random {
  constructor(seed = Date.now() ^ Math.floor(Math.random() * 0xffffffff)) {
    this.state = seed >>> 0 || 1;
  }
  next() {
    let x = this.state;
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    this.state = x >>> 0;
    return this.state / 0x100000000;
  }
}

export function mergeLine(line) {
  const values = line.filter(Boolean), result = [];
  let score = 0;
  for (let i = 0; i < values.length; i++) {
    if (values[i] === values[i + 1]) {
      const value = values[i] * 2;
      result.push(value);
      score += value;
      i++;
    } else result.push(values[i]);
  }
  while (result.length < 4) result.push(0);
  return { line: result, score };
}

export function canMove(board) {
  return board.some((row, r) => row.some((v, c) =>
    !v || (c < 3 && v === row[c + 1]) || (r < 3 && v === board[r + 1][c])));
}

function validateState(data) {
  if (!data || !Array.isArray(data.board) || data.board.length !== 4 ||
      data.board.some(row => !Array.isArray(row) || row.length !== 4 ||
        row.some(v => !Number.isSafeInteger(v) || v < 0 || (v !== 0 && (v < 2 || !Number.isInteger(Math.log2(v)))))) ||
      !Number.isSafeInteger(data.score) || data.score < 0 ||
      typeof data.won !== 'boolean' || typeof data.gameOver !== 'boolean' ||
      !Number.isInteger(data.rngState) || data.rngState < 1 || data.rngState > 0xffffffff) {
    throw new Error('存档格式错误');
  }
  const board = data.board.map(row => [...row]);
  if (data.gameOver !== !canMove(board) || data.won !== board.flat().some(v => v >= 2048)) {
    throw new Error('存档状态错误');
  }
  return {
    board,
    score: data.score,
    won: data.won,
    gameOver: data.gameOver,
    rngState: data.rngState,
    clearUsed: data.clearUsed ?? false
  };
}

export class Game2048 {
  constructor(seed) {
    this.rng = new Random(seed);
    this.reset();
  }
  reset() {
    this.board = Array.from({ length: 4 }, () => [0, 0, 0, 0]);
    this.score = 0;
    this.won = false;
    this.gameOver = false;
    this.lastMoveScore = 0;
    this.clearUsed = false;
    this.history = [];
    this.spawnTile();
    this.spawnTile();
  }
  spawnTile() {
    const empty = [];
    this.board.forEach((row, r) => row.forEach((v, c) => { if (!v) empty.push([r, c]); }));
    if (!empty.length) return false;
    const [r, c] = empty[Math.floor(this.rng.next() * empty.length)];
    this.board[r][c] = this.rng.next() < 0.9 ? 2 : 4;
    return true;
  }
  snapshot() {
    return { board: this.board.map(row => [...row]), score: this.score, won: this.won,
      gameOver: this.gameOver, rngState: this.rng.state, clearUsed: this.clearUsed };
  }
  restore(state) {
    this.board = state.board.map(row => [...row]);
    this.score = state.score;
    this.won = state.won;
    this.gameOver = state.gameOver;
    this.rng.state = state.rngState;
    this.clearUsed = state.clearUsed ?? false;
    this.lastMoveScore = 0;
  }
  move(direction) {
    if (!['left', 'right', 'up', 'down'].includes(direction)) throw new Error('未知方向');
    if (this.gameOver) return false;
    const next = this.board.map(row => [...row]);
    let gained = 0;
    for (let i = 0; i < 4; i++) {
      const positions = Array.from({ length: 4 }, (_, j) => {
        if (direction === 'left') return [i, j];
        if (direction === 'right') return [i, 3 - j];
        if (direction === 'up') return [j, i];
        return [3 - j, i];
      });
      const merged = mergeLine(positions.map(([r, c]) => this.board[r][c]));
      gained += merged.score;
      positions.forEach(([r, c], j) => { next[r][c] = merged.line[j]; });
    }
    this.lastMoveScore = 0;
    if (next.every((row, r) => row.every((v, c) => v === this.board[r][c]))) {
      this.gameOver = !canMove(this.board);
      return false;
    }
    this.history.push(this.snapshot());
    this.board = next;
    this.score += gained;
    this.lastMoveScore = gained;
    this.won ||= this.board.flat().some(v => v >= 2048);
    this.spawnTile();
    this.gameOver = !canMove(this.board);
    return true;
  }
  undo() {
    if (!this.history.length) return false;
    this.restore(this.history.pop());
    return true;
  }
  /** 删除棋盘上 value 最小的前 count 个方块，返回实际删掉的个数。 */
  removeSmallest(count) {
    const values = this.board.flat().filter(v => v > 0);
    if (!values.length) return 0;
    const minVal = Math.min(...values);
    const positions = [];
    this.board.forEach((row, r) => {
      row.forEach((v, c) => {
        if (v === minVal) positions.push([r, c]);
      });
    });
    for (let i = positions.length - 1; i > 0; i--) {
      const j = Math.floor(this.rng.next() * (i + 1));
      [positions[i], positions[j]] = [positions[j], positions[i]];
    }
    positions.slice(0, count).forEach(([r, c]) => {
      this.board[r][c] = 0;
    });
    return Math.min(count, positions.length);
  }
  revive() {
    if (!this.gameOver) return false;
    if (!this.removeSmallest(3)) return false;
    this.gameOver = false;
    this.lastMoveScore = 0;
    // 复活着删掉的方块不可恢复：清掉撤销栈，否则 undo 会把游戏结束前的局面搬回来，
    // 而那个局面的 gameOver 是 true，又不弹结束框，玩家会被卡死。
    this.history = [];
    return true;
  }
  clearTiles() {
    if (this.clearUsed) return false;
    if (!this.removeSmallest(3)) return false;
    this.clearUsed = true;
    this.lastMoveScore = 0;
    return true;
  }
  toJSON() {
    return { version: 1, ...this.snapshot(), history: this.history.map(s => ({ ...s, board: s.board.map(r => [...r]) })) };
  }
  load(data) {
    if (!data || data.version !== 1 || !Array.isArray(data.history)) throw new Error('存档版本错误');
    const current = validateState(data);
    const history = data.history.map(validateState);
    this.restore(current);
    this.history = history;
  }
}
