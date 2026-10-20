import assert from "node:assert/strict";
import test from "node:test";
import { keyToDirection, swipeToDirection, SWIPE_THRESHOLD } from "../web/input.mjs";

test("keyToDirection recognizes arrow keys", () => {
  assert.equal(keyToDirection("ArrowLeft"), "left");
  assert.equal(keyToDirection("ArrowRight"), "right");
  assert.equal(keyToDirection("ArrowUp"), "up");
  assert.equal(keyToDirection("ArrowDown"), "down");
});

test("keyToDirection recognizes WASD", () => {
  assert.equal(keyToDirection("a"), "left");
  assert.equal(keyToDirection("d"), "right");
  assert.equal(keyToDirection("w"), "up");
  assert.equal(keyToDirection("s"), "down");
});

test("keyToDirection is case-insensitive", () => {
  assert.equal(keyToDirection("A"), "left");
  assert.equal(keyToDirection("ARROWUP"), "up");
});

test("keyToDirection returns null for unrecognized keys", () => {
  assert.equal(keyToDirection("z"), null);
  assert.equal(keyToDirection("Enter"), null);
});

test("swipeToDirection detects horizontal swipes", () => {
  assert.equal(swipeToDirection(100, 10), "right");
  assert.equal(swipeToDirection(-100, 10), "left");
});

test("swipeToDirection detects vertical swipes", () => {
  assert.equal(swipeToDirection(10, 100), "down");
  assert.equal(swipeToDirection(10, -100), "up");
});

test("swipeToDirection returns null below threshold", () => {
  assert.equal(swipeToDirection(20, 10), null);
  assert.equal(swipeToDirection(-10, 20), null);
  assert.equal(swipeToDirection(SWIPE_THRESHOLD - 1, 0), null);
});

test("swipeToDirection respects custom threshold", () => {
  assert.equal(swipeToDirection(10, 5, 8), "right");
  assert.equal(swipeToDirection(5, 10, 8), "down");
  assert.equal(swipeToDirection(7, 3, 8), null);
});

test("swipeToDirection picks dominant axis", () => {
  assert.equal(swipeToDirection(100, 50), "right");
  assert.equal(swipeToDirection(50, 100), "down");
});
