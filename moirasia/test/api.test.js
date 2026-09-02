'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { openDb } = require('../server/db');
const { createServer } = require('../server/index');

/** Start the real server on an ephemeral port with an in-memory database. */
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

const newGroup = (call) =>
  call('POST', '/api/groups', { name: 'Νάξος', members: ['Άννα', 'Βασίλης', 'Γιώργος'] });

test('creates a group and returns a shareable code', async () => {
  await withServer(async (call) => {
    const { status, body } = await newGroup(call);
    assert.equal(status, 200);
    assert.match(body.group.code, /^[A-Z0-9]{6}$/);
    assert.equal(body.members.length, 3);
    assert.equal(body.totalCents, 0);
    assert.deepEqual(body.settlements, []);
  });
});

test('rejects a group with fewer than two people or duplicate names', async () => {
  await withServer(async (call) => {
    const tooFew = await call('POST', '/api/groups', { name: 'Μόνος', members: ['Άννα'] });
    assert.equal(tooFew.status, 400);

    const dupes = await call('POST', '/api/groups', { name: 'Χ', members: ['Άννα', 'άννα'] });
    assert.equal(dupes.status, 400);
  });
});

test('adds an expense and computes who pays whom', async () => {
  await withServer(async (call) => {
    const { body: group } = await newGroup(call);
    const [anna, vasilis, giorgos] = group.members;

    const { status, body } = await call('POST', `/api/groups/${group.group.code}/expenses`, {
      description: 'Σούπερ μάρκετ',
      amount: '30,00',
      payerId: anna.id,
      participantIds: [anna.id, vasilis.id, giorgos.id],
    });

    assert.equal(status, 200);
    assert.equal(body.totalCents, 3000);
    assert.equal(body.expenses[0].payerName, 'Άννα');
    assert.equal(body.settlements.length, 2);
    for (const transfer of body.settlements) {
      assert.equal(transfer.toName, 'Άννα');
      assert.equal(transfer.amountCents, 1000);
    }
  });
});

test('accepts both "12.50" and 12.5 as amounts', async () => {
  await withServer(async (call) => {
    const { body: group } = await newGroup(call);
    const code = group.group.code;
    const payerId = group.members[0].id;

    await call('POST', `/api/groups/${code}/expenses`, { description: 'Α', amount: '12.50', payerId });
    const { body } = await call('POST', `/api/groups/${code}/expenses`, {
      description: 'Β',
      amount: 12.5,
      payerId,
    });
    assert.equal(body.totalCents, 2500);
  });
});

test('an expense with no participants listed is shared by everyone', async () => {
  await withServer(async (call) => {
    const { body: group } = await newGroup(call);
    const { body } = await call('POST', `/api/groups/${group.group.code}/expenses`, {
      description: 'Βενζίνη',
      amount: '9',
      payerId: group.members[1].id,
    });
    assert.equal(body.expenses[0].participantIds.length, 3);
    assert.equal(body.balances.find((b) => b.memberId === group.members[1].id).balanceCents, 600);
  });
});

test('rejects bad amounts, unknown payers and outside participants', async () => {
  await withServer(async (call) => {
    const { body: group } = await newGroup(call);
    const code = group.group.code;
    const payerId = group.members[0].id;

    const zero = await call('POST', `/api/groups/${code}/expenses`, { description: 'Χ', amount: '0', payerId });
    assert.equal(zero.status, 400);

    const words = await call('POST', `/api/groups/${code}/expenses`, { description: 'Χ', amount: 'πολλά', payerId });
    assert.equal(words.status, 400);

    const stranger = await call('POST', `/api/groups/${code}/expenses`, { description: 'Χ', amount: '5', payerId: 9999 });
    assert.equal(stranger.status, 400);

    const outsider = await call('POST', `/api/groups/${code}/expenses`, {
      description: 'Χ',
      amount: '5',
      payerId,
      participantIds: [payerId, 9999],
    });
    assert.equal(outsider.status, 400);
  });
});

test('deletes an expense and recomputes the settlement', async () => {
  await withServer(async (call) => {
    const { body: group } = await newGroup(call);
    const code = group.group.code;

    const { body: withExpense } = await call('POST', `/api/groups/${code}/expenses`, {
      description: 'Ταβέρνα',
      amount: '60',
      payerId: group.members[0].id,
    });
    const expenseId = withExpense.expenses[0].id;

    const { status, body } = await call('DELETE', `/api/groups/${code}/expenses/${expenseId}`);
    assert.equal(status, 200);
    assert.equal(body.expenses.length, 0);
    assert.equal(body.totalCents, 0);
    assert.deepEqual(body.settlements, []);

    const again = await call('DELETE', `/api/groups/${code}/expenses/${expenseId}`);
    assert.equal(again.status, 404);
  });
});

test('adds a member later and keeps them out of older expenses', async () => {
  await withServer(async (call) => {
    const { body: group } = await newGroup(call);
    const code = group.group.code;

    await call('POST', `/api/groups/${code}/expenses`, {
      description: 'Πρωινό',
      amount: '30',
      payerId: group.members[0].id,
    });

    const { body } = await call('POST', `/api/groups/${code}/members`, { name: 'Δήμητρα' });
    assert.equal(body.members.length, 4);
    assert.equal(body.balances.find((b) => b.name === 'Δήμητρα').balanceCents, 0);

    const dupe = await call('POST', `/api/groups/${code}/members`, { name: 'δήμητρα' });
    assert.equal(dupe.status, 400);
  });
});

test('unknown group codes and endpoints answer with a clean error', async () => {
  await withServer(async (call) => {
    assert.equal((await call('GET', '/api/groups/ZZZZZZ')).status, 404);
    assert.equal((await call('GET', '/api/nope')).status, 404);
  });
});

test('serves the single page app for deep links', async () => {
  await withServer(async (call, base) => {
    const res = await fetch(`${base}/K7M2QX`);
    assert.equal(res.status, 200);
    assert.match(res.headers.get('content-type'), /text\/html/);
    assert.match(await res.text(), /Μοιρασιά/);
  });
});
