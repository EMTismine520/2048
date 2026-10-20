const assert = require("node:assert/strict");
const test = require("node:test");
const { canMove, Game2048, mergeLine } = require("../douyin-miniapp/utils/game");

function gameWith(board) {
  const game = new Game2048(42);
  game.board = board.map(row => row.slice());
  game.history = [];
  game.score = 0;
  game.won = board.some(row => row.some(value => value >= 2048));
  game.gameOver = false;
  game.lastMoveScore = 0;
  return game;
}

test("initializes two reproducible 2 or 4 tiles", () => {
  const first = new Game2048(42);
  const second = new Game2048(42);
  assert.deepEqual(first.board, second.board);
  const tiles = first.board.flat().filter(Boolean);
  assert.equal(tiles.length, 2);
  assert.ok(tiles.every(value => value === 2 || value === 4));
});

test("merges zero-spaced and consecutive values once", () => {
  assert.deepEqual(mergeLine([2, 0, 2, 0]), { line: [4, 0, 0, 0], score: 4 });
  assert.deepEqual(mergeLine([2, 2, 2, 2]), { line: [4, 4, 0, 0], score: 8 });
  assert.deepEqual(mergeLine([2, 2, 4, 0]), { line: [4, 4, 0, 0], score: 4 });
});

test("moves correctly in all four directions", () => {
  const initial = [[2, 2, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]];
  const expected = {
    left: [[4, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    right: [[0, 0, 0, 4], [0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0]],
    up: [[4, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    down: [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [4, 2, 0, 0]],
  };
  for (const [direction, target] of Object.entries(expected)) {
    const game = gameWith(initial);
    game.spawnTile = () => true;
    assert.equal(game.move(direction), true, direction);
    assert.deepEqual(game.board, target, direction);
    assert.equal(game.score, 4, direction);
  }
});

test("scores multiple merges and spawns one tile", () => {
  const game = gameWith([[2, 2, 4, 4], [8, 8, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  assert.equal(game.move("left"), true);
  assert.deepEqual(game.board[0], [4, 8, 0, 0]);
  assert.deepEqual(game.board[1], [16, 0, 0, 0]);
  assert.equal(game.score, 28);
  assert.equal(game.lastMoveScore, 28);
  assert.equal(game.board.flat().filter(Boolean).length, 4);
});

test("invalid move does not change score or history", () => {
  const game = gameWith([[2, 0, 0, 0], [4, 0, 0, 0], [8, 0, 0, 0], [16, 0, 0, 0]]);
  const before = game.snapshot();
  assert.equal(game.move("left"), false);
  assert.deepEqual(game.snapshot(), before);
  assert.equal(game.history.length, 0);
});

test("undo restores state and random sequence", () => {
  const game = gameWith([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  const before = game.toJSON();
  assert.equal(game.move("left"), true);
  assert.equal(game.undo(), true);
  assert.deepEqual(game.toJSON(), before);
  assert.equal(game.undo(), false);
});

test("shows victory at 2048 and allows continuing", () => {
  const game = gameWith([[1024, 1024, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  game.spawnTile = () => true;
  assert.equal(game.move("left"), true);
  assert.equal(game.won, true);
  assert.equal(game.gameOver, false);
  assert.equal(game.move("right"), true);
  assert.equal(game.won, true);
});

test("detects a locked board and rejects later moves", () => {
  const game = gameWith([[2, 2, 8, 16], [32, 64, 128, 256], [512, 1024, 2048, 4096], [8192, 16384, 32768, 65536]]);
  assert.equal(game.move("left"), true);
  assert.equal(game.gameOver, true);
  assert.equal(canMove(game.board), false);
  assert.equal(game.move("right"), false);
});

test("serializes and restores valid data, rejecting corrupt saves", () => {
  const game = gameWith([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  game.move("left");
  const restored = new Game2048(99);
  restored.load(JSON.parse(JSON.stringify(game.toJSON())));
  assert.deepEqual(restored.toJSON(), game.toJSON());
  assert.throws(() => restored.load({ version: 1, ...game.snapshot(), history: [{ board: [[1]], rngState: -1 }] }));
  assert.deepEqual(restored.toJSON(), game.toJSON());
});
