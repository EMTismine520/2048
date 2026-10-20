import assert from "node:assert/strict";
import test from "node:test";
import { canMove, Game2048, mergeLine } from "../web/game.mjs";

function gameWith(board) {
  const game = new Game2048(42);
  game.board = board.map(row => [...row]);
  game.history = [];
  game.score = 0;
  game.won = board.flat().some(value => value >= 2048);
  game.gameOver = false;
  game.lastMoveScore = 0;
  return game;
}

test("starts with two reproducible randomly placed 2 or 4 tiles", () => {
  const a = new Game2048(42), b = new Game2048(42);
  assert.deepEqual(a.board, b.board);
  const tiles = a.board.flat().filter(Boolean);
  assert.equal(tiles.length, 2);
  assert.ok(tiles.every(value => value === 2 || value === 4));
});

test("merges zero-spaced matches and prevents repeat merges", () => {
  assert.deepEqual(mergeLine([2, 0, 2, 0]), { line: [4, 0, 0, 0], score: 4 });
  assert.deepEqual(mergeLine([2, 2, 2, 2]), { line: [4, 4, 0, 0], score: 8 });
  assert.deepEqual(mergeLine([2, 2, 4, 0]), { line: [4, 4, 0, 0], score: 4 });
});

test("slides and merges correctly in each direction", () => {
  const board = [[2, 2, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]];
  const expected = {
    left: [[4, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    right: [[0, 0, 0, 4], [0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0]],
    up: [[4, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    down: [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [4, 2, 0, 0]],
  };
  for (const [direction, target] of Object.entries(expected)) {
    const game = gameWith(board);
    game.spawnTile = () => true;
    assert.equal(game.move(direction), true, direction);
    assert.deepEqual(game.board, target, direction);
    assert.equal(game.score, 4, direction);
  }
});

test("scores multiple merges and creates at most one extra tile", () => {
  const game = gameWith([[2, 2, 4, 4], [8, 8, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  assert.equal(game.move("left"), true);
  assert.deepEqual(game.board[0], [4, 8, 0, 0]);
  assert.deepEqual(game.board[1], [16, 0, 0, 0]);
  assert.equal(game.score, 28);
  assert.equal(game.lastMoveScore, 28);
  assert.equal(game.board.flat().filter(Boolean).length, 4);
});

test("invalid moves leave board, score, and undo history unchanged", () => {
  const game = gameWith([[2, 0, 0, 0], [4, 0, 0, 0], [8, 0, 0, 0], [16, 0, 0, 0]]);
  const before = game.snapshot();
  assert.equal(game.move("left"), false);
  assert.deepEqual(game.snapshot(), before);
  assert.equal(game.history.length, 0);
});

test("undo restores the board, score, and exact random sequence", () => {
  const game = gameWith([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  const before = game.toJSON();
  assert.equal(game.move("left"), true);
  assert.equal(game.undo(), true);
  assert.deepEqual(game.toJSON(), before);
  assert.equal(game.undo(), false);
});

test("spawns a 4 at the only empty position at the 10 percent boundary", () => {
  const game = gameWith([[2, 4, 8, 16], [4, 8, 16, 32], [8, 16, 32, 64], [16, 32, 64, 0]]);
  const rolls = [0, 0.9];
  game.rng.next = () => rolls.shift();
  assert.equal(game.spawnTile(), true);
  assert.equal(game.board[3][3], 4);
});

test("shows victory at 2048 and continues play", () => {
  const game = gameWith([[1024, 1024, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  game.spawnTile = () => true;
  assert.equal(game.move("left"), true);
  assert.equal(game.won, true);
  assert.equal(game.gameOver, false);
  assert.equal(game.move("right"), true);
  assert.equal(game.won, true);
});

test("detects a newly full locked board and rejects later moves", () => {
  const game = gameWith([[2, 2, 8, 16], [32, 64, 128, 256], [512, 1024, 2048, 4096], [8192, 16384, 32768, 65536]]);
  assert.equal(game.move("left"), true);
  assert.equal(game.gameOver, true);
  assert.equal(canMove(game.board), false);
  assert.equal(game.move("right"), false);
});

test("saves and resumes state and rejects corrupt save data", () => {
  const game = gameWith([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  game.move("left");
  const loaded = new Game2048(99);
  loaded.load(JSON.parse(JSON.stringify(game.toJSON())));
  assert.deepEqual(loaded.toJSON(), game.toJSON());
  assert.throws(() => loaded.load({ version: 1, ...game.snapshot(), history: [{ board: [[1]], rngState: -1 }] }));
  assert.deepEqual(loaded.toJSON(), game.toJSON(), "a bad save must not corrupt the current game");
});

test("revive removes up to 3 smallest tiles and clears undo history", () => {
  const game = gameWith([[2, 4, 8, 16], [2, 4, 8, 16], [2, 4, 8, 16], [2, 4, 8, 16]]);
  game.gameOver = true;
  game.history = [game.snapshot()];
  assert.equal(game.revive(), true);
  assert.equal(game.gameOver, false);
  const remaining = game.board.flat().filter(v => v === 2);
  assert.equal(remaining.length, 1, "should remove 3 of the 4 smallest (2s)");
  assert.equal(game.history.length, 0, "revive must clear undo stack");
});

test("revive fails when game is not over", () => {
  const game = gameWith([[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  assert.equal(game.revive(), false);
});

test("clearTiles removes 3 smallest and can only be used once", () => {
  const game = gameWith([[2, 4, 8, 2], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
  assert.equal(game.clearUsed, false);
  assert.equal(game.clearTiles(), true);
  const remaining = game.board.flat().filter(v => v === 2);
  assert.equal(remaining.length, 0, "all three 2s should be removed");
  assert.equal(game.clearUsed, true);
  assert.equal(game.clearTiles(), false, "second call must fail");
});
