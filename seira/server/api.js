'use strict';

const { planRound } = require('./assign');

const MAX_NAME_LENGTH = 40;
const MAX_PEOPLE = 25;
const MAX_TASKS = 25;
const WEIGHTS = [1, 2, 3]; // εύκολη / κανονική / βαριά αγγαρεία

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function cleanName(value, field) {
  if (typeof value !== 'string') throw new ApiError(400, `Το πεδίο «${field}» είναι υποχρεωτικό.`);
  const name = value.trim().replace(/\s+/g, ' ');
  if (!name) throw new ApiError(400, `Το πεδίο «${field}» δεν μπορεί να είναι κενό.`);
  if (name.length > MAX_NAME_LENGTH) {
    throw new ApiError(400, `Το «${field}» ξεπερνά τους ${MAX_NAME_LENGTH} χαρακτήρες.`);
  }
  return name;
}

function cleanWeight(value) {
  if (value === undefined || value === null || value === '') return 1;
  const weight = Number(value);
  if (!WEIGHTS.includes(weight)) throw new ApiError(400, 'Το βάρος πρέπει να είναι 1, 2 ή 3.');
  return weight;
}

function noDuplicates(names, what) {
  const seen = new Set(names.map((name) => name.toLocaleLowerCase('el')));
  if (seen.size !== names.length) throw new ApiError(400, `Υπάρχουν διπλά ονόματα στα ${what}.`);
}

function loadBoard(store, code) {
  const board = store.getBoardByCode(String(code || '').toUpperCase());
  if (!board) throw new ApiError(404, 'Δεν βρέθηκε πίνακας με αυτόν τον κωδικό.');
  return board;
}

/** Συσσωρευμένος φόρτος (άθροισμα βαρών) και πλήθος αγγαρειών ανά άτομο. */
function computeHistory(people, tasks, rounds) {
  const weightOf = new Map(tasks.map((task) => [task.id, task.weight]));
  const loads = new Map(people.map((person) => [person.id, 0]));
  const counts = new Map(people.map((person) => [person.id, 0]));

  for (const round of rounds) {
    for (const assignment of round.assignments) {
      if (!loads.has(assignment.personId)) continue;
      loads.set(assignment.personId, loads.get(assignment.personId) + (weightOf.get(assignment.taskId) || 1));
      counts.set(assignment.personId, counts.get(assignment.personId) + 1);
    }
  }

  return { loads, counts };
}

/**
 * Πόσους συνεχόμενους γύρους (από τον πιο πρόσφατο και πίσω) κρατάει κάποιος
 * την ίδια αγγαρεία.
 *
 * @param {{assignments:{taskId:number, personId:number}[]}[]} rounds νεότεροι πρώτα
 * @returns {Map<string, number>} "personId:taskId" -> μήκος σερί
 */
function computeStreaks(rounds) {
  const streaks = new Map();
  if (rounds.length === 0) return streaks;

  const keysOf = (round) =>
    new Set(round.assignments.map((assignment) => `${assignment.personId}:${assignment.taskId}`));

  // Μετράνε μόνο τα ζευγάρια του πιο πρόσφατου γύρου, όσο πίσω κρατάνε.
  const active = keysOf(rounds[0]);

  for (const round of rounds) {
    const pairs = keysOf(round);
    for (const key of [...active]) {
      if (pairs.has(key)) streaks.set(key, (streaks.get(key) || 0) + 1);
      else active.delete(key);
    }
    if (active.size === 0) break;
  }

  return streaks;
}

/** Ό,τι χρειάζεται το frontend για να ζωγραφίσει τον πίνακα, σε μία απάντηση. */
function boardState(store, board) {
  const people = store.getPeople(board.id);
  const tasks = store.getTasks(board.id);
  const prefs = store.getPrefs(board.id);
  const rounds = store.getRounds(board.id);
  const { loads, counts } = computeHistory(people, tasks, rounds);

  const personName = new Map(people.map((person) => [person.id, person.name]));
  const taskName = new Map(tasks.map((task) => [task.id, task.name]));

  return {
    board: { code: board.code, name: board.name, createdAt: board.createdAt },
    people: people.map((person) => ({
      ...person,
      load: loads.get(person.id) || 0,
      count: counts.get(person.id) || 0,
    })),
    tasks,
    prefs: Object.fromEntries(prefs),
    rounds: rounds.map((round) => ({
      ...round,
      assignments: round.assignments.map((assignment) => ({
        ...assignment,
        personName: personName.get(assignment.personId) || '—',
        taskName: taskName.get(assignment.taskId) || '—',
      })),
    })),
  };
}

function createBoard(store, body) {
  const name = cleanName(body?.name, 'όνομα πίνακα');

  const people = (Array.isArray(body?.people) ? body.people : []).map((value) =>
    cleanName(value, 'όνομα ατόμου')
  );
  const tasks = (Array.isArray(body?.tasks) ? body.tasks : []).map((value) => {
    const task = typeof value === 'string' ? { name: value } : value || {};
    return { name: cleanName(task.name, 'όνομα αγγαρείας'), weight: cleanWeight(task.weight) };
  });

  if (people.length < 2) throw new ApiError(400, 'Χρειάζονται τουλάχιστον 2 άτομα.');
  if (people.length > MAX_PEOPLE) throw new ApiError(400, `Το πολύ ${MAX_PEOPLE} άτομα.`);
  if (tasks.length < 1) throw new ApiError(400, 'Χρειάζεται τουλάχιστον 1 αγγαρεία.');
  if (tasks.length > MAX_TASKS) throw new ApiError(400, `Το πολύ ${MAX_TASKS} αγγαρείες.`);

  noDuplicates(people, 'άτομα');
  noDuplicates(tasks.map((task) => task.name), 'αγγαρείες');

  return boardState(store, store.createBoard(name, people, tasks));
}

function addPerson(store, code, body) {
  const board = loadBoard(store, code);
  const name = cleanName(body?.name, 'όνομα ατόμου');
  const people = store.getPeople(board.id);

  if (people.length >= MAX_PEOPLE) throw new ApiError(400, `Το πολύ ${MAX_PEOPLE} άτομα.`);
  noDuplicates([...people.map((person) => person.name), name], 'άτομα');

  store.addPerson(board.id, name);
  return boardState(store, board);
}

function removePerson(store, code, personId) {
  const board = loadBoard(store, code);
  if (store.getPeople(board.id).length <= 2) {
    throw new ApiError(400, 'Πρέπει να μείνουν τουλάχιστον 2 άτομα.');
  }
  if (!store.removePerson(board.id, Number(personId))) {
    throw new ApiError(404, 'Το άτομο δεν βρέθηκε.');
  }
  return boardState(store, board);
}

function addTask(store, code, body) {
  const board = loadBoard(store, code);
  const name = cleanName(body?.name, 'όνομα αγγαρείας');
  const weight = cleanWeight(body?.weight);
  const tasks = store.getTasks(board.id);

  if (tasks.length >= MAX_TASKS) throw new ApiError(400, `Το πολύ ${MAX_TASKS} αγγαρείες.`);
  noDuplicates([...tasks.map((task) => task.name), name], 'αγγαρείες');

  store.addTask(board.id, name, weight);
  return boardState(store, board);
}

function removeTask(store, code, taskId) {
  const board = loadBoard(store, code);
  if (store.getTasks(board.id).length <= 1) {
    throw new ApiError(400, 'Πρέπει να μείνει τουλάχιστον 1 αγγαρεία.');
  }
  if (!store.removeTask(board.id, Number(taskId))) {
    throw new ApiError(404, 'Η αγγαρεία δεν βρέθηκε.');
  }
  return boardState(store, board);
}

function setPref(store, code, body) {
  const board = loadBoard(store, code);
  const personId = Number(body?.personId);
  const taskId = Number(body?.taskId);
  const score = Number(body?.score);

  if (![-1, 0, 1].includes(score)) throw new ApiError(400, 'Η προτίμηση πρέπει να είναι -1, 0 ή 1.');
  if (!store.getPeople(board.id).some((person) => person.id === personId)) {
    throw new ApiError(400, 'Το άτομο δεν ανήκει στον πίνακα.');
  }
  if (!store.getTasks(board.id).some((task) => task.id === taskId)) {
    throw new ApiError(400, 'Η αγγαρεία δεν ανήκει στον πίνακα.');
  }

  store.setPref(personId, taskId, score);
  return boardState(store, board);
}

function createRound(store, code, body) {
  const board = loadBoard(store, code);
  const people = store.getPeople(board.id);
  const tasks = store.getTasks(board.id);
  const rounds = store.getRounds(board.id);

  if (tasks.length === 0) throw new ApiError(400, 'Πρόσθεσε πρώτα μια αγγαρεία.');

  const absent = new Set((Array.isArray(body?.absentIds) ? body.absentIds : []).map(Number));
  const available = people.filter((person) => !absent.has(person.id));
  if (available.length === 0) throw new ApiError(400, 'Λείπουν όλοι — δεν μένει κανείς για τη σειρά.');

  const label = body?.label ? cleanName(body.label, 'ετικέτα γύρου') : `Γύρος ${rounds.length + 1}`;
  const { loads } = computeHistory(people, tasks, rounds);

  const assignments = planRound({
    people: available,
    tasks,
    prefs: store.getPrefs(board.id),
    loads,
    streaks: computeStreaks(rounds),
    roundIndex: rounds.length,
  });

  store.addRound(board.id, { index: rounds.length, label, assignments });
  return boardState(store, board);
}

function deleteRound(store, code, roundId) {
  const board = loadBoard(store, code);
  if (!store.deleteRound(board.id, Number(roundId))) {
    throw new ApiError(404, 'Ο γύρος δεν βρέθηκε.');
  }
  return boardState(store, board);
}

function getBoard(store, code) {
  return boardState(store, loadBoard(store, code));
}

module.exports = {
  ApiError,
  createBoard,
  getBoard,
  addPerson,
  removePerson,
  addTask,
  removeTask,
  setPref,
  createRound,
  deleteRound,
  computeHistory,
  computeStreaks,
};
