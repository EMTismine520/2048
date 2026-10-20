// 2048 规则模块，不依赖抖音页面 API，便于单元测试。
class Random {
  constructor(seed) {
    const initial = seed === undefined ? (Date.now() ^ Math.floor(Math.random() * 0xffffffff)) : seed;
    this.state = initial >>> 0 || 1;
  }

  next() {
    let value = this.state;
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    this.state = value >>> 0;
    return this.state / 0x100000000;
  }
}

function mergeLine(line) {
  const values = line.filter(Boolean);
  const result = [];
  let score = 0;
  for (let index = 0; index < values.length; index += 1) {
    if (values[index] === values[index + 1]) {
      const merged = values[index] * 2;
      result.push(merged);
      score += merged;
      index += 1;
    } else {
      result.push(values[index]);
    }
  }
  while (result.length < 4) result.push(0);
  return { line: result, score };
}

function canMove(board) {
  return board.some((row, rowIndex) => row.some((value, columnIndex) => (
    value === 0
      || (columnIndex < 3 && value === row[columnIndex + 1])
      || (rowIndex < 3 && value === board[rowIndex + 1][columnIndex])
  )));
}

function isTileValue(value) {
  return Number.isSafeInteger(value)
    && value >= 0
    && (value === 0 || (value >= 2 && Number.isInteger(Math.log2(value))));
}

function validateState(data) {
  if (!data || !Array.isArray(data.board) || data.board.length !== 4
      || data.board.some(row => !Array.isArray(row) || row.length !== 4 || row.some(value => !isTileValue(value)))
      || !Number.isSafeInteger(data.score) || data.score < 0
      || typeof data.won !== "boolean" || typeof data.gameOver !== "boolean"
      || !Number.isInteger(data.rngState) || data.rngState < 1 || data.rngState > 0xffffffff) {
    throw new Error("存档格式错误");
  }
  const board = data.board.map(row => row.slice());
  if (data.gameOver !== !canMove(board) || data.won !== board.some(row => row.some(value => value >= 2048))) {
    throw new Error("存档状态错误");
  }
  return {
    board,
    score: data.score,
    won: data.won,
    gameOver: data.gameOver,
    rngState: data.rngState,
  };
}

class Game2048 {
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
    this.history = [];
    this.spawnTile();
    this.spawnTile();
  }

  spawnTile() {
    const empty = [];
    this.board.forEach((row, rowIndex) => row.forEach((value, columnIndex) => {
      if (value === 0) empty.push([rowIndex, columnIndex]);
    }));
    if (!empty.length) return false;
    const [row, column] = empty[Math.floor(this.rng.next() * empty.length)];
    this.board[row][column] = this.rng.next() < 0.9 ? 2 : 4;
    return true;
  }

  snapshot() {
    return {
      board: this.board.map(row => row.slice()),
      score: this.score,
      won: this.won,
      gameOver: this.gameOver,
      rngState: this.rng.state,
    };
  }

  restore(state) {
    this.board = state.board.map(row => row.slice());
    this.score = state.score;
    this.won = state.won;
    this.gameOver = state.gameOver;
    this.rng.state = state.rngState;
    this.lastMoveScore = 0;
  }

  move(direction) {
    if (["left", "right", "up", "down"].indexOf(direction) === -1) {
      throw new Error("未知方向");
    }
    if (this.gameOver) return false;

    const next = this.board.map(row => row.slice());
    let gained = 0;
    for (let index = 0; index < 4; index += 1) {
      const positions = Array.from({ length: 4 }, (_, offset) => {
        if (direction === "left") return [index, offset];
        if (direction === "right") return [index, 3 - offset];
        if (direction === "up") return [offset, index];
        return [3 - offset, index];
      });
      const merged = mergeLine(positions.map(([row, column]) => this.board[row][column]));
      gained += merged.score;
      positions.forEach(([row, column], offset) => {
        next[row][column] = merged.line[offset];
      });
    }

    this.lastMoveScore = 0;
    const unchanged = next.every((row, rowIndex) => row.every((value, columnIndex) => value === this.board[rowIndex][columnIndex]));
    if (unchanged) {
      this.gameOver = !canMove(this.board);
      return false;
    }

    this.history.push(this.snapshot());
    this.board = next;
    this.score += gained;
    this.lastMoveScore = gained;
    this.won = this.won || this.board.some(row => row.some(value => value >= 2048));
    this.spawnTile();
    this.gameOver = !canMove(this.board);
    return true;
  }

  undo() {
    if (!this.history.length) return false;
    this.restore(this.history.pop());
    return true;
  }

  revive() {
    if (!this.gameOver) return false;
    const values = this.board.flat().filter(v => v > 0);
    if (!values.length) return false;
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
    positions.slice(0, 3).forEach(([r, c]) => {
      this.board[r][c] = 0;
    });
    this.gameOver = false;
    this.lastMoveScore = 0;
    return true;
  }

  toJSON() {
    return {
      version: 1,
      ...this.snapshot(),
      history: this.history.map(state => ({ ...state, board: state.board.map(row => row.slice()) })),
    };
  }

  load(data) {
    if (!data || data.version !== 1 || !Array.isArray(data.history)) throw new Error("存档版本错误");
    const current = validateState(data);
    const history = data.history.map(item => validateState(item));
    this.restore(current);
    this.history = history;
  }
}

module.exports = { Random, mergeLine, canMove, Game2048 };
