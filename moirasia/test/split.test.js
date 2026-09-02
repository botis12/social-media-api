'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { splitEvenly, computeBalances, settle } = require('../server/split');

test('splitEvenly divides exactly when it can', () => {
  assert.deepEqual(splitEvenly(3000, 3), [1000, 1000, 1000]);
});

test('splitEvenly hands out the leftover cents and never loses one', () => {
  const shares = splitEvenly(1000, 3);
  assert.deepEqual(shares, [334, 333, 333]);
  assert.equal(shares.reduce((a, b) => a + b, 0), 1000);
});

test('splitEvenly rejects nonsense input', () => {
  assert.throws(() => splitEvenly(100, 0));
  assert.throws(() => splitEvenly(-1, 2));
  assert.throws(() => splitEvenly(10.5, 2));
});

test('computeBalances: one payer, everybody shares', () => {
  const members = [{ id: 1 }, { id: 2 }, { id: 3 }];
  const balances = computeBalances(members, [
    { amountCents: 3000, payerId: 1, participantIds: [1, 2, 3] },
  ]);
  assert.equal(balances.get(1), 2000);
  assert.equal(balances.get(2), -1000);
  assert.equal(balances.get(3), -1000);
});

test('computeBalances: an expense can exclude some members', () => {
  const members = [{ id: 1 }, { id: 2 }, { id: 3 }];
  const balances = computeBalances(members, [
    { amountCents: 1000, payerId: 1, participantIds: [1, 2] },
  ]);
  assert.equal(balances.get(1), 500);
  assert.equal(balances.get(2), -500);
  assert.equal(balances.get(3), 0);
});

test('balances always add up to zero, even with awkward amounts', () => {
  const members = [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }];
  const expenses = [
    { amountCents: 1000, payerId: 1, participantIds: [1, 2, 3] },
    { amountCents: 777, payerId: 2, participantIds: [1, 2, 3, 4] },
    { amountCents: 5, payerId: 3, participantIds: [3, 4] },
    { amountCents: 12345, payerId: 4, participantIds: [1, 4] },
  ];
  const total = [...computeBalances(members, expenses).values()].reduce((a, b) => a + b, 0);
  assert.equal(total, 0);
});

test('settle clears every debt with at most n-1 payments', () => {
  const balances = new Map([[1, 2000], [2, -1000], [3, -1000]]);
  const transfers = settle(balances);

  assert.ok(transfers.length <= 2);
  const settled = new Map(balances);
  for (const t of transfers) {
    settled.set(t.fromId, settled.get(t.fromId) + t.amountCents);
    settled.set(t.toId, settled.get(t.toId) - t.amountCents);
  }
  for (const value of settled.values()) assert.equal(value, 0);
});

test('settle returns nothing when everybody is even', () => {
  assert.deepEqual(settle(new Map([[1, 0], [2, 0]])), []);
});

test('settle handles a random mess without leaving a cent behind', () => {
  const members = Array.from({ length: 8 }, (_, i) => ({ id: i + 1 }));
  const expenses = Array.from({ length: 40 }, (_, i) => ({
    amountCents: ((i * 977) % 9871) + 1,
    payerId: (i % 8) + 1,
    participantIds: members.map((m) => m.id).filter((id) => (id + i) % 3 !== 0),
  })).filter((e) => e.participantIds.length > 0);

  const balances = computeBalances(members, expenses);
  const transfers = settle(balances);
  assert.ok(transfers.length <= members.length - 1);

  const settled = new Map(balances);
  for (const t of transfers) {
    settled.set(t.fromId, settled.get(t.fromId) + t.amountCents);
    settled.set(t.toId, settled.get(t.toId) - t.amountCents);
    assert.ok(t.amountCents > 0);
  }
  for (const value of settled.values()) assert.equal(value, 0);
});
