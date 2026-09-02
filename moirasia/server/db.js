'use strict';

const { DatabaseSync } = require('node:sqlite');
const path = require('node:path');
const fs = require('node:fs');

// Ambiguous characters (0/O, 1/I) are left out so a code is easy to read aloud.
const CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const CODE_LENGTH = 6;

const SCHEMA = `
CREATE TABLE IF NOT EXISTS groups (
  id         INTEGER PRIMARY KEY,
  code       TEXT NOT NULL UNIQUE,
  name       TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS members (
  id       INTEGER PRIMARY KEY,
  group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  name     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
  id           INTEGER PRIMARY KEY,
  group_id     INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  payer_id     INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  description  TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expense_participants (
  expense_id INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
  member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  PRIMARY KEY (expense_id, member_id)
);

CREATE INDEX IF NOT EXISTS idx_members_group ON members(group_id);
CREATE INDEX IF NOT EXISTS idx_expenses_group ON expenses(group_id);
`;

/**
 * Open (and migrate) the database. Pass ':memory:' for tests.
 * @param {string} file
 */
function openDb(file) {
  if (file !== ':memory:') {
    fs.mkdirSync(path.dirname(file), { recursive: true });
  }
  const db = new DatabaseSync(file);
  db.exec('PRAGMA foreign_keys = ON;');
  db.exec(SCHEMA);
  return new Store(db);
}

function randomCode() {
  const bytes = require('node:crypto').randomBytes(CODE_LENGTH);
  let code = '';
  for (const byte of bytes) code += CODE_ALPHABET[byte % CODE_ALPHABET.length];
  return code;
}

class Store {
  constructor(db) {
    this.db = db;
  }

  close() {
    this.db.close();
  }

  /**
   * @param {string} name
   * @param {string[]} memberNames
   */
  createGroup(name, memberNames) {
    const createdAt = new Date().toISOString();
    const insertGroup = this.db.prepare(
      'INSERT INTO groups (code, name, created_at) VALUES (?, ?, ?)'
    );

    let code;
    let groupId;
    // Codes are random; retry on the (very unlikely) collision.
    for (let attempt = 0; ; attempt++) {
      code = randomCode();
      try {
        groupId = Number(insertGroup.run(code, name, createdAt).lastInsertRowid);
        break;
      } catch (err) {
        if (attempt >= 5) throw err;
      }
    }

    const insertMember = this.db.prepare('INSERT INTO members (group_id, name) VALUES (?, ?)');
    for (const memberName of memberNames) insertMember.run(groupId, memberName);

    return this.getGroupByCode(code);
  }

  getGroupByCode(code) {
    const group = this.db
      .prepare('SELECT id, code, name, created_at FROM groups WHERE code = ?')
      .get(code);
    if (!group) return null;
    return { id: group.id, code: group.code, name: group.name, createdAt: group.created_at };
  }

  getMembers(groupId) {
    return this.db
      .prepare('SELECT id, name FROM members WHERE group_id = ? ORDER BY id')
      .all(groupId)
      .map((m) => ({ id: m.id, name: m.name }));
  }

  addMember(groupId, name) {
    const id = Number(
      this.db.prepare('INSERT INTO members (group_id, name) VALUES (?, ?)').run(groupId, name)
        .lastInsertRowid
    );
    return { id, name };
  }

  getExpenses(groupId) {
    const rows = this.db
      .prepare(
        `SELECT id, payer_id, description, amount_cents, created_at
         FROM expenses WHERE group_id = ? ORDER BY id DESC`
      )
      .all(groupId);

    const participantsOf = this.db.prepare(
      'SELECT member_id FROM expense_participants WHERE expense_id = ? ORDER BY member_id'
    );

    return rows.map((row) => ({
      id: row.id,
      payerId: row.payer_id,
      description: row.description,
      amountCents: row.amount_cents,
      createdAt: row.created_at,
      participantIds: participantsOf.all(row.id).map((p) => p.member_id),
    }));
  }

  addExpense(groupId, { description, amountCents, payerId, participantIds }) {
    const createdAt = new Date().toISOString();
    const expenseId = Number(
      this.db
        .prepare(
          `INSERT INTO expenses (group_id, payer_id, description, amount_cents, created_at)
           VALUES (?, ?, ?, ?, ?)`
        )
        .run(groupId, payerId, description, amountCents, createdAt).lastInsertRowid
    );

    const link = this.db.prepare(
      'INSERT INTO expense_participants (expense_id, member_id) VALUES (?, ?)'
    );
    for (const memberId of participantIds) link.run(expenseId, memberId);

    return {
      id: expenseId,
      payerId,
      description,
      amountCents,
      createdAt,
      participantIds: [...participantIds].sort((a, b) => a - b),
    };
  }

  deleteExpense(groupId, expenseId) {
    const result = this.db
      .prepare('DELETE FROM expenses WHERE id = ? AND group_id = ?')
      .run(expenseId, groupId);
    return result.changes > 0;
  }
}

module.exports = { openDb, Store, randomCode };
