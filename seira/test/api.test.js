'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { openDb } = require('../server/db');
const { createServer } = require('../server/index');

async function withServer(run) {
  const store = openDb(':memory:');
  const server = createServer(store);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;

  const call = async (method, path, body) => {
    const res = await fetch(base + path, {
      method,
      headers: body ? { 'content-type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    return { status: res.status, body: await res.json() };
  };

  try {
    await run(call, base);
  } finally {
    await new Promise((resolve) => server.close(resolve));
    store.close();
  }
}

const newBoard = (call) =>
  call('POST', '/api/boards', {
    name: 'Σπίτι Ιπποκράτους',
    people: ['Άννα', 'Βασίλης', 'Γιώργος'],
    tasks: [
      { name: 'Πιάτα', weight: 2 },
      { name: 'Σκούπα', weight: 1 },
      { name: 'Μπάνιο', weight: 3 },
    ],
  });

test('creates a board with a shareable code', async () => {
  await withServer(async (call) => {
    const { status, body } = await newBoard(call);
    assert.equal(status, 200);
    assert.match(body.board.code, /^[A-Z0-9]{6}$/);
    assert.equal(body.people.length, 3);
    assert.equal(body.tasks.length, 3);
    assert.deepEqual(body.rounds, []);
    assert.ok(body.people.every((person) => person.load === 0));
  });
});

test('rejects boards without enough people, tasks, or with duplicates', async () => {
  await withServer(async (call) => {
    const noPeople = await call('POST', '/api/boards', { name: 'Χ', people: ['Άννα'], tasks: ['Πιάτα'] });
    assert.equal(noPeople.status, 400);

    const noTasks = await call('POST', '/api/boards', { name: 'Χ', people: ['Άννα', 'Βασίλης'], tasks: [] });
    assert.equal(noTasks.status, 400);

    const dupes = await call('POST', '/api/boards', {
      name: 'Χ',
      people: ['Άννα', 'άννα'],
      tasks: ['Πιάτα'],
    });
    assert.equal(dupes.status, 400);

    const badWeight = await call('POST', '/api/boards', {
      name: 'Χ',
      people: ['Άννα', 'Βασίλης'],
      tasks: [{ name: 'Πιάτα', weight: 9 }],
    });
    assert.equal(badWeight.status, 400);
  });
});

test('draws a round that covers every task exactly once', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const { status, body } = await call('POST', `/api/boards/${board.board.code}/rounds`, {});

    assert.equal(status, 200);
    assert.equal(body.rounds.length, 1);
    assert.equal(body.rounds[0].label, 'Γύρος 1');

    const assignments = body.rounds[0].assignments;
    assert.equal(assignments.length, 3);
    assert.equal(new Set(assignments.map((a) => a.taskId)).size, 3);
    assert.equal(new Set(assignments.map((a) => a.personId)).size, 3);
    assert.ok(assignments.every((a) => a.personName && a.taskName));

    // Ο φόρτος του γύρου είναι τα βάρη 1 + 2 + 3.
    assert.equal(body.people.reduce((total, person) => total + person.load, 0), 6);
  });
});

test('a stated preference is honoured in the next round', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;
    const anna = board.people[0];
    const bathroom = board.tasks.find((task) => task.name === 'Μπάνιο');

    const { body: withPref } = await call('POST', `/api/boards/${code}/prefs`, {
      personId: anna.id,
      taskId: bathroom.id,
      score: 1,
    });
    assert.equal(withPref.prefs[`${anna.id}:${bathroom.id}`], 1);

    const { body } = await call('POST', `/api/boards/${code}/rounds`, {});
    const bathroomAssignment = body.rounds[0].assignments.find((a) => a.taskId === bathroom.id);
    assert.equal(bathroomAssignment.personId, anna.id);
  });
});

test('a rejected preference (-1) is avoided', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;
    const anna = board.people[0];
    const bathroom = board.tasks.find((task) => task.name === 'Μπάνιο');

    await call('POST', `/api/boards/${code}/prefs`, {
      personId: anna.id,
      taskId: bathroom.id,
      score: -1,
    });

    const { body } = await call('POST', `/api/boards/${code}/rounds`, {});
    const bathroomAssignment = body.rounds[0].assignments.find((a) => a.taskId === bathroom.id);
    assert.notEqual(bathroomAssignment.personId, anna.id);
  });
});

test('rejects invalid preference values and strangers', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;

    const badScore = await call('POST', `/api/boards/${code}/prefs`, {
      personId: board.people[0].id,
      taskId: board.tasks[0].id,
      score: 5,
    });
    assert.equal(badScore.status, 400);

    const stranger = await call('POST', `/api/boards/${code}/prefs`, {
      personId: 9999,
      taskId: board.tasks[0].id,
      score: 1,
    });
    assert.equal(stranger.status, 400);
  });
});

test('someone marked absent is left out of that round', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;
    const away = board.people[1];

    const { body } = await call('POST', `/api/boards/${code}/rounds`, { absentIds: [away.id] });
    const assignments = body.rounds[0].assignments;

    assert.equal(assignments.length, 3);
    assert.ok(assignments.every((a) => a.personId !== away.id));
    assert.equal(body.people.find((person) => person.id === away.id).load, 0);
  });
});

test('everyone absent is refused', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const { status } = await call('POST', `/api/boards/${board.board.code}/rounds`, {
      absentIds: board.people.map((person) => person.id),
    });
    assert.equal(status, 400);
  });
});

test('load evens out over several rounds and undo rolls it back', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;

    let latest = board;
    for (let round = 0; round < 6; round++) {
      latest = (await call('POST', `/api/boards/${code}/rounds`, {})).body;
    }

    assert.equal(latest.rounds.length, 6);
    const loads = latest.people.map((person) => person.load);
    assert.equal(loads.reduce((a, b) => a + b, 0), 36); // 6 γύροι x βάρος 6
    assert.ok(Math.max(...loads) - Math.min(...loads) <= 3);

    const newest = latest.rounds[0];
    const { body: afterUndo } = await call('DELETE', `/api/boards/${code}/rounds/${newest.id}`);
    assert.equal(afterUndo.rounds.length, 5);
    assert.equal(afterUndo.people.reduce((total, person) => total + person.load, 0), 30);

    const again = await call('DELETE', `/api/boards/${code}/rounds/${newest.id}`);
    assert.equal(again.status, 404);
  });
});

test('people and tasks can be added and removed, with floors enforced', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;

    const { body: withPerson } = await call('POST', `/api/boards/${code}/people`, { name: 'Δήμητρα' });
    assert.equal(withPerson.people.length, 4);

    const dupe = await call('POST', `/api/boards/${code}/people`, { name: 'δήμητρα' });
    assert.equal(dupe.status, 400);

    const { body: withTask } = await call('POST', `/api/boards/${code}/tasks`, {
      name: 'Σκουπίδια',
      weight: 1,
    });
    assert.equal(withTask.tasks.length, 4);

    const { body: fewerTasks } = await call('DELETE', `/api/boards/${code}/tasks/${withTask.tasks[0].id}`);
    assert.equal(fewerTasks.tasks.length, 3);

    // Κάτω όριο: 2 άτομα, 1 αγγαρεία.
    let people = withPerson.people;
    for (let i = 0; i < 2; i++) {
      people = (await call('DELETE', `/api/boards/${code}/people/${people[0].id}`)).body.people;
    }
    assert.equal(people.length, 2);
    const tooFew = await call('DELETE', `/api/boards/${code}/people/${people[0].id}`);
    assert.equal(tooFew.status, 400);
  });
});

test('removing a person keeps old rounds readable', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;

    const { body: afterRound } = await call('POST', `/api/boards/${code}/rounds`, {});
    const assigned = afterRound.rounds[0].assignments[0].personId;

    const { body } = await call('DELETE', `/api/boards/${code}/people/${assigned}`);
    assert.equal(body.people.length, 2);
    assert.ok(body.rounds[0].assignments.every((a) => a.personId !== assigned));
  });
});

test('unknown codes and endpoints answer cleanly', async () => {
  await withServer(async (call) => {
    assert.equal((await call('GET', '/api/boards/ZZZZZZ')).status, 404);
    assert.equal((await call('GET', '/api/nope')).status, 404);
    assert.equal((await call('GET', '/api/health')).status, 200);
  });
});

test('serves the single page app for deep links', async () => {
  await withServer(async (call, base) => {
    const res = await fetch(`${base}/K7M2QX`);
    assert.equal(res.status, 200);
    assert.match(res.headers.get('content-type'), /text\/html/);
    assert.match(await res.text(), /Σειρά/);
  });
});

test('computeStreaks counts only consecutive rounds from the newest', () => {
  const { computeStreaks } = require('../server/api');

  // Νεότεροι γύροι πρώτα: ο 1 κρατάει την 10 δύο γύρους, μετά αλλάζει.
  const streaks = computeStreaks([
    { assignments: [{ personId: 1, taskId: 10 }, { personId: 2, taskId: 20 }] },
    { assignments: [{ personId: 1, taskId: 10 }, { personId: 2, taskId: 20 }] },
    { assignments: [{ personId: 1, taskId: 20 }, { personId: 2, taskId: 10 }] },
    { assignments: [{ personId: 1, taskId: 10 }, { personId: 2, taskId: 20 }] },
  ]);

  assert.equal(streaks.get('1:10'), 2);
  assert.equal(streaks.get('2:20'), 2);
  assert.equal(streaks.get('1:20'), undefined);
  assert.deepEqual([...computeStreaks([]).keys()], []);
});

test('nobody keeps the same chore for many rounds in a row', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;

    let latest = board;
    for (let round = 0; round < 8; round++) {
      latest = (await call('POST', `/api/boards/${code}/rounds`, {})).body;
    }

    // Για κάθε αγγαρεία, πόσο μεγάλο είναι το μεγαλύτερο σερί ίδιου ατόμου.
    for (const task of latest.tasks) {
      const byRound = latest.rounds
        .map((round) => round.assignments.find((a) => a.taskId === task.id)?.personId)
        .reverse();

      let longest = 1;
      let current = 1;
      for (let i = 1; i < byRound.length; i++) {
        current = byRound[i] === byRound[i - 1] ? current + 1 : 1;
        longest = Math.max(longest, current);
      }
      assert.ok(longest <= 3, `η «${task.name}» έμεινε ${longest} γύρους στο ίδιο άτομο`);
    }
  });
});

test('load keeps balancing even when preferences lock a pattern', async () => {
  await withServer(async (call) => {
    const { body: board } = await newBoard(call);
    const code = board.board.code;
    const [anna, vasilis] = board.people;
    const dishes = board.tasks.find((task) => task.name === 'Πιάτα');
    const bathroom = board.tasks.find((task) => task.name === 'Μπάνιο');

    await call('POST', `/api/boards/${code}/prefs`, { personId: anna.id, taskId: bathroom.id, score: 1 });
    await call('POST', `/api/boards/${code}/prefs`, { personId: vasilis.id, taskId: dishes.id, score: -1 });

    let latest = board;
    for (let round = 0; round < 10; round++) {
      latest = (await call('POST', `/api/boards/${code}/rounds`, {})).body;
    }

    // Ο Βασίλης δεν πλένει ποτέ πιάτα...
    assert.ok(
      latest.rounds.every((round) =>
        round.assignments.every((a) => !(a.taskId === dishes.id && a.personId === vasilis.id))
      )
    );

    // ...αλλά ούτε κάποιος φορτώνεται μόνιμα: ο φόρτος ανά άτομο έχει σημασία
    // μόνο αν συνδέεται με το βάρος της αγγαρείας.
    const loads = latest.people.map((person) => person.load);
    assert.ok(
      Math.max(...loads) - Math.min(...loads) <= 4,
      `διαφορά φόρτου: ${JSON.stringify(latest.people.map((p) => [p.name, p.load]))}`
    );
  });
});
