'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { solveAssignment, planRound } = require('../server/assign');

const sum = (cost, chosen) => chosen.reduce((total, col, row) => total + cost[row][col], 0);

/** Ωμή δύναμη: δοκιμάζει κάθε πιθανή ανάθεση. Μόνο για μικρούς πίνακες. */
function bruteForce(cost) {
  const n = cost.length;
  const m = cost[0].length;
  let best = Infinity;

  // Χωρίς κλάδεμα: τα κόστη μπορεί να είναι αρνητικά, οπότε ένα ακριβό
  // ξεκίνημα μπορεί κάλλιστα να καταλήξει στη φθηνότερη λύση.
  const walk = (row, used, total) => {
    if (row === n) {
      best = Math.min(best, total);
      return;
    }
    for (let col = 0; col < m; col++) {
      if (used[col]) continue;
      used[col] = true;
      walk(row + 1, used, total + cost[row][col]);
      used[col] = false;
    }
  };

  walk(0, new Array(m).fill(false), 0);
  return best;
}

test('solveAssignment picks the obvious cheapest pairing', () => {
  const cost = [
    [1, 9, 9],
    [9, 1, 9],
    [9, 9, 1],
  ];
  assert.deepEqual(solveAssignment(cost), [0, 1, 2]);
});

test('solveAssignment avoids the greedy trap', () => {
  // Η άπληστη επιλογή (γραμμή 0 -> στήλη 0) κοστίζει 1 + 10 = 11· η σωστή, 8.
  const cost = [
    [1, 2],
    [10, 7],
  ];
  const chosen = solveAssignment(cost);
  assert.equal(sum(cost, chosen), 8);
});

test('solveAssignment handles negative costs (τα «το προτιμώ»)', () => {
  const cost = [
    [-4, 0],
    [0, -4],
  ];
  assert.equal(sum(cost, solveAssignment(cost)), -8);
});

test('solveAssignment works with more columns than rows', () => {
  const cost = [
    [5, 1, 8, 9],
    [7, 6, 2, 3],
  ];
  const chosen = solveAssignment(cost);
  assert.equal(new Set(chosen).size, 2);
  assert.equal(sum(cost, chosen), 3);
});

test('solveAssignment matches brute force on 200 random matrices', () => {
  let seed = 7;
  const rand = (max) => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return (seed / 2147483648) * max;
  };

  for (let trial = 0; trial < 200; trial++) {
    const n = 1 + Math.floor(rand(5));
    const m = n + Math.floor(rand(3));
    const cost = Array.from({ length: n }, () =>
      Array.from({ length: m }, () => Math.round(rand(40)) - 12)
    );
    assert.equal(sum(cost, solveAssignment(cost)), bruteForce(cost), `trial ${trial}`);
  }
});

test('solveAssignment rejects fewer columns than rows', () => {
  assert.throws(() => solveAssignment([[1, 2], [3, 4], [5, 6]]));
  assert.deepEqual(solveAssignment([]), []);
});

/* ── planRound ─────────────────────────────────────────── */

const people = [{ id: 1 }, { id: 2 }, { id: 3 }];
const tasks = [
  { id: 10, weight: 1 },
  { id: 20, weight: 2 },
  { id: 30, weight: 3 },
];
const noLoads = new Map(people.map((p) => [p.id, 0]));

test('planRound gives everyone exactly one task when the counts match', () => {
  const plan = planRound({
    people,
    tasks,
    prefs: new Map(),
    loads: noLoads,
    streaks: new Map(),
    roundIndex: 0,
  });

  assert.equal(plan.length, 3);
  assert.equal(new Set(plan.map((a) => a.personId)).size, 3);
  assert.deepEqual(plan.map((a) => a.taskId).sort(), [10, 20, 30]);
});

test('planRound respects strong preferences', () => {
  const prefs = new Map([
    ['1:30', 1], // ο 1 θέλει τη βαριά
    ['2:10', 1],
    ['3:20', 1],
  ]);
  const plan = planRound({
    people,
    tasks,
    prefs,
    loads: noLoads,
    streaks: new Map(),
    roundIndex: 0,
  });

  const byTask = new Map(plan.map((a) => [a.taskId, a.personId]));
  assert.equal(byTask.get(30), 1);
  assert.equal(byTask.get(10), 2);
  assert.equal(byTask.get(20), 3);
});

test('planRound favours whoever has done the least', () => {
  const twoPeople = [{ id: 1 }, { id: 2 }];
  const oneTask = [{ id: 10, weight: 1 }];
  const plan = planRound({
    people: twoPeople,
    tasks: oneTask,
    prefs: new Map(),
    loads: new Map([[1, 9], [2, 0]]),
    streaks: new Map(),
    roundIndex: 0,
  });
  assert.equal(plan[0].personId, 2);
});

test('planRound avoids repeating the same task back to back', () => {
  const twoPeople = [{ id: 1 }, { id: 2 }];
  const twoTasks = [{ id: 10, weight: 1 }, { id: 20, weight: 1 }];
  const plan = planRound({
    people: twoPeople,
    tasks: twoTasks,
    prefs: new Map(),
    loads: new Map([[1, 1], [2, 1]]),
    streaks: new Map([['1:10', 1], ['2:20', 1]]),
    roundIndex: 1,
  });

  const byTask = new Map(plan.map((a) => [a.taskId, a.personId]));
  assert.equal(byTask.get(10), 2);
  assert.equal(byTask.get(20), 1);
});

test('planRound covers every task even when people are fewer', () => {
  const twoPeople = [{ id: 1 }, { id: 2 }];
  const fiveTasks = [10, 20, 30, 40, 50].map((id) => ({ id, weight: 1 }));
  const plan = planRound({
    people: twoPeople,
    tasks: fiveTasks,
    prefs: new Map(),
    loads: new Map([[1, 0], [2, 0]]),
    streaks: new Map(),
    roundIndex: 0,
  });

  assert.equal(plan.length, 5);
  assert.deepEqual(plan.map((a) => a.taskId).sort((a, b) => a - b), [10, 20, 30, 40, 50]);
  const perPerson = plan.reduce((acc, a) => acc.set(a.personId, (acc.get(a.personId) || 0) + 1), new Map());
  // 5 αγγαρείες σε 2 άτομα: 3 και 2, ποτέ 4 και 1.
  assert.deepEqual([...perPerson.values()].sort(), [2, 3]);
});

test('over many rounds the load stays balanced', () => {
  const group = [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }];
  const chores = [
    { id: 10, weight: 1 },
    { id: 20, weight: 2 },
    { id: 30, weight: 3 },
  ];
  const loads = new Map(group.map((person) => [person.id, 0]));
  let streaks = new Map();

  for (let round = 0; round < 24; round++) {
    const plan = planRound({
      people: group,
      tasks: chores,
      prefs: new Map(),
      loads,
      streaks,
      roundIndex: round,
    });
    const pairs = new Set(plan.map((a) => `${a.personId}:${a.taskId}`));
    streaks = new Map([...pairs].map((key) => [key, (streaks.get(key) || 0) + 1]));
    for (const assignment of plan) {
      const weight = chores.find((task) => task.id === assignment.taskId).weight;
      loads.set(assignment.personId, loads.get(assignment.personId) + weight);
    }
  }

  const values = [...loads.values()];
  const spread = Math.max(...values) - Math.min(...values);
  assert.ok(spread <= 3, `η διαφορά φόρτου έμεινε ${spread}`);
});

test('a long streak eventually beats a preference', () => {
  const twoPeople = [{ id: 1 }, { id: 2 }];
  const twoTasks = [{ id: 10, weight: 1 }, { id: 20, weight: 1 }];
  const prefs = new Map([['1:10', 1]]); // ο 1 προτιμά την 10

  const withShortStreak = planRound({
    people: twoPeople,
    tasks: twoTasks,
    prefs,
    loads: new Map([[1, 0], [2, 0]]),
    streaks: new Map([['1:10', 1]]),
    roundIndex: 1,
  });
  assert.equal(withShortStreak.find((a) => a.taskId === 10).personId, 1);

  const withLongStreak = planRound({
    people: twoPeople,
    tasks: twoTasks,
    prefs,
    loads: new Map([[1, 0], [2, 0]]),
    streaks: new Map([['1:10', 4]]),
    roundIndex: 1,
  });
  assert.equal(withLongStreak.find((a) => a.taskId === 10).personId, 2);
});
