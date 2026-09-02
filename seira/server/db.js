'use strict';

const { DatabaseSync } = require('node:sqlite');
const crypto = require('node:crypto');
const path = require('node:path');
const fs = require('node:fs');

// Χωρίς 0/O και 1/I, για να διαβάζεται ο κωδικός στο τηλέφωνο.
const CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const CODE_LENGTH = 6;

const SCHEMA = `
CREATE TABLE IF NOT EXISTS boards (
  id         INTEGER PRIMARY KEY,
  code       TEXT NOT NULL UNIQUE,
  name       TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people (
  id       INTEGER PRIMARY KEY,
  board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
  name     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  id       INTEGER PRIMARY KEY,
  board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
  name     TEXT NOT NULL,
  weight   REAL NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS prefs (
  person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
  task_id   INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  score     INTEGER NOT NULL,
  PRIMARY KEY (person_id, task_id)
);

CREATE TABLE IF NOT EXISTS rounds (
  id         INTEGER PRIMARY KEY,
  board_id   INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
  idx        INTEGER NOT NULL,
  label      TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
  round_id  INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
  task_id   INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
  PRIMARY KEY (round_id, task_id)
);

CREATE INDEX IF NOT EXISTS idx_people_board ON people(board_id);
CREATE INDEX IF NOT EXISTS idx_tasks_board ON tasks(board_id);
CREATE INDEX IF NOT EXISTS idx_rounds_board ON rounds(board_id);
`;

function openDb(file) {
  if (file !== ':memory:') fs.mkdirSync(path.dirname(file), { recursive: true });
  const db = new DatabaseSync(file);
  db.exec('PRAGMA foreign_keys = ON;');
  db.exec(SCHEMA);
  return new Store(db);
}

function randomCode() {
  let code = '';
  for (const byte of crypto.randomBytes(CODE_LENGTH)) {
    code += CODE_ALPHABET[byte % CODE_ALPHABET.length];
  }
  return code;
}

class Store {
  constructor(db) {
    this.db = db;
  }

  close() {
    this.db.close();
  }

  createBoard(name, peopleNames, tasks) {
    const createdAt = new Date().toISOString();
    const insertBoard = this.db.prepare(
      'INSERT INTO boards (code, name, created_at) VALUES (?, ?, ?)'
    );

    let code;
    let boardId;
    for (let attempt = 0; ; attempt++) {
      code = randomCode();
      try {
        boardId = Number(insertBoard.run(code, name, createdAt).lastInsertRowid);
        break;
      } catch (err) {
        if (attempt >= 5) throw err;
      }
    }

    for (const personName of peopleNames) this.addPerson(boardId, personName);
    for (const task of tasks) this.addTask(boardId, task.name, task.weight);

    return this.getBoardByCode(code);
  }

  getBoardByCode(code) {
    const row = this.db
      .prepare('SELECT id, code, name, created_at FROM boards WHERE code = ?')
      .get(code);
    return row ? { id: row.id, code: row.code, name: row.name, createdAt: row.created_at } : null;
  }

  getPeople(boardId) {
    return this.db
      .prepare('SELECT id, name FROM people WHERE board_id = ? ORDER BY id')
      .all(boardId)
      .map((row) => ({ id: row.id, name: row.name }));
  }

  addPerson(boardId, name) {
    const id = Number(
      this.db.prepare('INSERT INTO people (board_id, name) VALUES (?, ?)').run(boardId, name)
        .lastInsertRowid
    );
    return { id, name };
  }

  removePerson(boardId, personId) {
    return (
      this.db
        .prepare('DELETE FROM people WHERE id = ? AND board_id = ?')
        .run(personId, boardId).changes > 0
    );
  }

  getTasks(boardId) {
    return this.db
      .prepare('SELECT id, name, weight FROM tasks WHERE board_id = ? ORDER BY id')
      .all(boardId)
      .map((row) => ({ id: row.id, name: row.name, weight: row.weight }));
  }

  addTask(boardId, name, weight = 1) {
    const id = Number(
      this.db
        .prepare('INSERT INTO tasks (board_id, name, weight) VALUES (?, ?, ?)')
        .run(boardId, name, weight).lastInsertRowid
    );
    return { id, name, weight };
  }

  removeTask(boardId, taskId) {
    return (
      this.db.prepare('DELETE FROM tasks WHERE id = ? AND board_id = ?').run(taskId, boardId)
        .changes > 0
    );
  }

  /** @returns {Map<string, number>} "personId:taskId" -> score */
  getPrefs(boardId) {
    const rows = this.db
      .prepare(
        `SELECT prefs.person_id, prefs.task_id, prefs.score
         FROM prefs
         JOIN people ON people.id = prefs.person_id
         WHERE people.board_id = ?`
      )
      .all(boardId);
    return new Map(rows.map((row) => [`${row.person_id}:${row.task_id}`, row.score]));
  }

  setPref(personId, taskId, score) {
    if (score === 0) {
      this.db.prepare('DELETE FROM prefs WHERE person_id = ? AND task_id = ?').run(personId, taskId);
      return;
    }
    this.db
      .prepare(
        `INSERT INTO prefs (person_id, task_id, score) VALUES (?, ?, ?)
         ON CONFLICT (person_id, task_id) DO UPDATE SET score = excluded.score`
      )
      .run(personId, taskId, score);
  }

  /** Γύροι, νεότεροι πρώτα. */
  getRounds(boardId) {
    const rounds = this.db
      .prepare('SELECT id, idx, label, created_at FROM rounds WHERE board_id = ? ORDER BY idx DESC')
      .all(boardId);

    const assignmentsOf = this.db.prepare(
      'SELECT task_id, person_id FROM assignments WHERE round_id = ? ORDER BY task_id'
    );

    return rounds.map((round) => ({
      id: round.id,
      index: round.idx,
      label: round.label,
      createdAt: round.created_at,
      assignments: assignmentsOf
        .all(round.id)
        .map((row) => ({ taskId: row.task_id, personId: row.person_id })),
    }));
  }

  addRound(boardId, { index, label, assignments }) {
    const roundId = Number(
      this.db
        .prepare('INSERT INTO rounds (board_id, idx, label, created_at) VALUES (?, ?, ?, ?)')
        .run(boardId, index, label, new Date().toISOString()).lastInsertRowid
    );

    const insert = this.db.prepare(
      'INSERT INTO assignments (round_id, task_id, person_id) VALUES (?, ?, ?)'
    );
    for (const assignment of assignments) {
      insert.run(roundId, assignment.taskId, assignment.personId);
    }
    return roundId;
  }

  deleteRound(boardId, roundId) {
    return (
      this.db.prepare('DELETE FROM rounds WHERE id = ? AND board_id = ?').run(roundId, boardId)
        .changes > 0
    );
  }
}

module.exports = { openDb, Store, randomCode };
