'use strict';

const $ = (id) => document.getElementById(id);
const RECENT_KEY = 'seira:recent';
const PREF_FACES = { '-1': '🙁', 0: '😐', 1: '😀' };
const WEIGHT_LABELS = { 1: 'εύκολη', 2: 'κανονική', 3: 'βαριά' };

let state = null;
let absent = new Set();

/* ── δίκτυο ─────────────────────────────────────────────── */

async function apiCall(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: body ? { 'content-type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Κάτι πήγε στραβά.');
  return data;
}

function toast(message, isError = false) {
  const el = $('toast');
  el.textContent = message;
  el.classList.toggle('error', isError);
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.hidden = true; }, 3200);
}

/** Τυλίγει μια ενέργεια: ανανεώνει την κατάσταση ή δείχνει το σφάλμα. */
async function run(promise, onDone) {
  try {
    state = await promise;
    renderBoard();
    if (onDone) onDone();
  } catch (err) {
    toast(err.message, true);
  }
}

/* ── πρόσφατοι πίνακες ──────────────────────────────────── */

function readRecent() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY)) || [];
  } catch {
    return [];
  }
}

function remember(code, name) {
  const list = readRecent().filter((item) => item.code !== code);
  list.unshift({ code, name });
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(list.slice(0, 6)));
  } catch { /* private mode */ }
}

function renderRecent() {
  const list = readRecent();
  $('recent').hidden = list.length === 0;
  $('recent-list').replaceChildren(...list.map((item) => {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = `/${item.code}`;
    a.textContent = `${item.name} · ${item.code}`;
    a.addEventListener('click', (event) => {
      event.preventDefault();
      openBoard(item.code);
    });
    li.append(a);
    return li;
  }));
}

/* ── πλοήγηση ───────────────────────────────────────────── */

function showHome() {
  state = null;
  $('view-board').hidden = true;
  $('view-home').hidden = false;
  history.pushState({}, '', '/');
  renderRecent();
}

function showBoard(data, push) {
  state = data;
  absent = new Set();
  remember(data.board.code, data.board.name);
  $('view-home').hidden = true;
  $('view-board').hidden = false;
  if (push) history.pushState({ code: data.board.code }, '', `/${data.board.code}`);
  renderBoard();
}

async function openBoard(code, { push = true } = {}) {
  try {
    showBoard(await apiCall('GET', `/api/boards/${encodeURIComponent(code)}`), push);
  } catch (err) {
    toast(err.message, true);
    showHome();
  }
}

/* ── απόδοση ────────────────────────────────────────────── */

function renderBoard() {
  $('board-title').textContent = state.board.name;
  $('board-code').textContent = state.board.code;
  $('board-sub').textContent =
    `${state.people.length} άτομα · ${state.tasks.length} αγγαρείες · ${state.rounds.length} γύροι`;

  renderCurrentRound();
  renderAbsent();
  renderPrefs();
  renderLoads();
  renderTasks();
  renderHistory();
}

function renderCurrentRound() {
  const round = state.rounds[0];
  const container = $('current-round');
  $('delete-round').hidden = !round;

  if (!round) {
    $('current-title').textContent = 'Αυτή τη φορά';
    container.replaceChildren(el('p', 'empty', 'Δεν έχει βγει σειρά ακόμα. Πάτα «Βγάλε τη σειρά».'));
    return;
  }

  $('current-title').textContent = round.label;
  const prefs = state.prefs;

  container.replaceChildren(...round.assignments.map((assignment) => {
    const score = prefs[`${assignment.personId}:${assignment.taskId}`] || 0;
    const box = el('div', 'assignment');
    box.append(
      el('span', 'mark', PREF_FACES[score]),
      el('div', 'who', assignment.personName),
      el('div', 'what', assignment.taskName)
    );
    return box;
  }));
}

function renderAbsent() {
  $('absent-list').replaceChildren(...state.people.map((person) => {
    const chip = el('button', 'chip', person.name);
    chip.type = 'button';
    chip.setAttribute('aria-pressed', String(absent.has(person.id)));
    chip.addEventListener('click', () => {
      if (absent.has(person.id)) absent.delete(person.id);
      else absent.add(person.id);
      chip.setAttribute('aria-pressed', String(absent.has(person.id)));
    });
    return chip;
  }));
}

function renderPrefs() {
  const table = $('prefs-table');
  const head = document.createElement('tr');
  head.append(el('th', '', ''));
  for (const task of state.tasks) head.append(el('th', '', task.name));

  const rows = state.people.map((person) => {
    const tr = document.createElement('tr');
    tr.append(el('td', '', person.name));

    for (const task of state.tasks) {
      const key = `${person.id}:${task.id}`;
      const score = state.prefs[key] || 0;

      const button = el('button', 'pref-btn', PREF_FACES[score]);
      button.type = 'button';
      button.dataset.score = String(score);
      button.title = `${person.name} — ${task.name}`;
      button.setAttribute('aria-label', `Προτίμηση: ${person.name}, ${task.name}`);
      button.addEventListener('click', () => {
        const next = score === 0 ? 1 : score === 1 ? -1 : 0; // 😐 → 😀 → 🙁 → 😐
        run(apiCall('POST', `/api/boards/${state.board.code}/prefs`, {
          personId: person.id,
          taskId: task.id,
          score: next,
        }));
      });

      const td = document.createElement('td');
      td.append(button);
      tr.append(td);
    }
    return tr;
  });

  const thead = document.createElement('thead');
  thead.append(head);
  const tbody = document.createElement('tbody');
  tbody.append(...rows);
  table.replaceChildren(thead, tbody);
}

function renderLoads() {
  const maxLoad = Math.max(1, ...state.people.map((person) => person.load));

  $('load-list').replaceChildren(...state.people.map((person) => {
    const li = document.createElement('li');
    const bar = el('div', 'bar');
    const fill = document.createElement('span');
    fill.style.width = `${Math.round((person.load / maxLoad) * 100)}%`;
    bar.append(fill);

    const remove = el('button', 'remove-btn', '×');
    remove.type = 'button';
    remove.title = 'Αφαίρεση';
    remove.setAttribute('aria-label', `Αφαίρεση: ${person.name}`);
    remove.addEventListener('click', () =>
      run(apiCall('DELETE', `/api/boards/${state.board.code}/people/${person.id}`))
    );

    li.append(
      el('span', 'name', person.name),
      bar,
      el('span', 'load-value', `${person.load} (${person.count})`),
      remove
    );
    return li;
  }));
}

function renderTasks() {
  $('task-list').replaceChildren(...state.tasks.map((task) => {
    const li = document.createElement('li');
    const remove = el('button', 'remove-btn', '×');
    remove.type = 'button';
    remove.title = 'Αφαίρεση';
    remove.setAttribute('aria-label', `Αφαίρεση: ${task.name}`);
    remove.addEventListener('click', () =>
      run(apiCall('DELETE', `/api/boards/${state.board.code}/tasks/${task.id}`))
    );

    li.append(
      el('span', 'name', task.name),
      el('span', 'weight-tag', WEIGHT_LABELS[task.weight] || `βάρος ${task.weight}`),
      remove
    );
    return li;
  }));
}

function renderHistory() {
  const table = $('history-table');
  if (state.rounds.length === 0) {
    table.replaceChildren(el('caption', 'empty', 'Κανένας γύρος ακόμα.'));
    return;
  }

  const head = document.createElement('tr');
  head.append(el('th', '', 'Γύρος'));
  for (const task of state.tasks) head.append(el('th', '', task.name));

  const rows = state.rounds.map((round) => {
    const byTask = new Map(round.assignments.map((a) => [a.taskId, a.personName]));
    const tr = document.createElement('tr');
    tr.append(el('td', '', round.label));
    for (const task of state.tasks) tr.append(el('td', 'muted', byTask.get(task.id) || '—'));
    return tr;
  });

  const thead = document.createElement('thead');
  thead.append(head);
  const tbody = document.createElement('tbody');
  tbody.append(...rows);
  table.replaceChildren(thead, tbody);
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/* ── φόρμες αρχικής ─────────────────────────────────────── */

function addPersonInput(value = '') {
  const row = el('div', 'stack-row');
  const input = document.createElement('input');
  input.placeholder = 'Όνομα';
  input.maxLength = 40;
  input.value = value;
  const remove = el('button', '', '×');
  remove.type = 'button';
  remove.addEventListener('click', () => {
    if ($('person-inputs').children.length > 2) row.remove();
  });
  row.append(input, remove);
  $('person-inputs').append(row);
  return input;
}

function addTaskInput(value = '', weight = '2') {
  const row = el('div', 'stack-row');
  const input = document.createElement('input');
  input.placeholder = 'π.χ. Πιάτα';
  input.maxLength = 40;
  input.value = value;

  const select = document.createElement('select');
  for (const [level, label] of Object.entries(WEIGHT_LABELS)) {
    const option = document.createElement('option');
    option.value = level;
    option.textContent = label;
    select.append(option);
  }
  select.value = weight;

  const remove = el('button', '', '×');
  remove.type = 'button';
  remove.addEventListener('click', () => {
    if ($('task-inputs').children.length > 1) row.remove();
  });

  row.append(input, select, remove);
  $('task-inputs').append(row);
  return input;
}

/* ── γεγονότα ───────────────────────────────────────────── */

$('add-person-input').addEventListener('click', () => addPersonInput().focus());
$('add-task-input').addEventListener('click', () => addTaskInput().focus());

$('create-form').addEventListener('submit', async (event) => {
  event.preventDefault();

  const people = [...$('person-inputs').querySelectorAll('input')]
    .map((input) => input.value.trim())
    .filter(Boolean);

  const tasks = [...$('task-inputs').children]
    .map((row) => ({
      name: row.querySelector('input').value.trim(),
      weight: Number(row.querySelector('select').value),
    }))
    .filter((task) => task.name);

  try {
    const data = await apiCall('POST', '/api/boards', {
      name: $('board-name').value,
      people,
      tasks,
    });
    showBoard(data, true);
    toast(`Ο πίνακας δημιουργήθηκε · κωδικός ${data.board.code}`);
  } catch (err) {
    toast(err.message, true);
  }
});

$('join-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const code = $('join-code').value.trim().toUpperCase();
  if (code) openBoard(code);
});

$('draw-round').addEventListener('click', () => {
  run(
    apiCall('POST', `/api/boards/${state.board.code}/rounds`, { absentIds: [...absent] }),
    () => toast('Νέα σειρά!')
  );
});

$('delete-round').addEventListener('click', () => {
  const round = state.rounds[0];
  if (round) run(apiCall('DELETE', `/api/boards/${state.board.code}/rounds/${round.id}`));
});

$('person-form').addEventListener('submit', (event) => {
  event.preventDefault();
  run(
    apiCall('POST', `/api/boards/${state.board.code}/people`, { name: $('new-person').value }),
    () => { $('new-person').value = ''; }
  );
});

$('task-form').addEventListener('submit', (event) => {
  event.preventDefault();
  run(
    apiCall('POST', `/api/boards/${state.board.code}/tasks`, {
      name: $('new-task').value,
      weight: Number($('new-task-weight').value),
    }),
    () => { $('new-task').value = ''; }
  );
});

$('copy-link').addEventListener('click', async () => {
  const link = `${location.origin}/${state.board.code}`;
  try {
    await navigator.clipboard.writeText(link);
    toast('Ο σύνδεσμος αντιγράφηκε.');
  } catch {
    toast(link);
  }
});

$('back-home').addEventListener('click', showHome);
window.addEventListener('popstate', () => boot({ push: false }));

/* ── εκκίνηση ───────────────────────────────────────────── */

function boot({ push = true } = {}) {
  const code = location.pathname.replace(/^\/+|\/+$/g, '').toUpperCase();
  if (/^[A-Z0-9]{6}$/.test(code)) {
    openBoard(code, { push });
  } else {
    $('view-board').hidden = true;
    $('view-home').hidden = false;
    renderRecent();
  }
}

addPersonInput();
addPersonInput();
addTaskInput('', '2');
addTaskInput('', '2');
boot();
