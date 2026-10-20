import assert from "node:assert/strict";
import test from "node:test";
import { Game2048 } from "../web/game.mjs";
import { createMemoryStore, saveGame, loadGame, loadSoundEnabled, saveSoundEnabled } from "../web/storage.mjs";

test("memory store acts like localStorage", () => {
  const store = createMemoryStore();
  assert.equal(store.getItem("key"), null);
  store.setItem("key", "value");
  assert.equal(store.getItem("key"), "value");
  store.removeItem("key");
  assert.equal(store.getItem("key"), null);
});

test("saveGame and loadGame round-trip preserves state", () => {
  const store = createMemoryStore();
  const game = new Game2048(42);
  game.move("left");
  game.move("up");
  const scoreBefore = game.score;
  assert.ok(saveGame(store, game));
  const restored = new Game2048();
  assert.ok(loadGame(store, restored));
  assert.equal(restored.score, scoreBefore);
  assert.deepEqual(restored.board, game.board);
  assert.equal(restored.history.length, game.history.length);
});

test("loadGame returns false when no save exists", () => {
  const game = new Game2048();
  assert.equal(loadGame(createMemoryStore(), game), false);
});

test("loadGame clears corrupt save and returns false", () => {
  const store = createMemoryStore();
  store.setItem("2048-web-save-v1", "{broken");
  const game = new Game2048();
  assert.equal(loadGame(store, game), false);
  assert.equal(store.getItem("2048-web-save-v1"), null);
});

test("sound preference defaults to enabled", () => {
  assert.ok(loadSoundEnabled(createMemoryStore()));
  assert.ok(loadSoundEnabled(null));
});

test("saveSoundEnabled and loadSoundEnabled round-trip", () => {
  const store = createMemoryStore();
  saveSoundEnabled(store, false);
  assert.equal(loadSoundEnabled(store), false);
  saveSoundEnabled(store, true);
  assert.ok(loadSoundEnabled(store));
});

test("saveGame returns false when store is null", () => {
  assert.equal(saveGame(null, new Game2048()), false);
});
