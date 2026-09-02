'use strict';

const $ = (id) => document.getElementById(id);
const euro = new Intl.NumberFormat('el-GR', { style: 'currency', currency: 'EUR' });
const money = (cents) => euro.format(cents / 100);

const RECENT_KEY = 'moirasia:recent';

let state = null; // last group state from the server
let selectedParticipants = new Set();

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

/* ── πρόσφατες παρέες (τοπικά) ──────────────────────────── */

function readRecent() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY)) || [];
  } catch {
    return [];
  }
}

function rememberGroup(code, name) {
  const list = readRecent().filter((item) => item.code !== code);
  list.unshift({ code, name });
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(list.slice(0, 6)));
  } catch { /* private mode: δεν πειράζει */ }
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
      openGroup(item.code);
    });
    li.append(a);
    return li;
  }));
}

/* ── πλοήγηση ───────────────────────────────────────────── */

function showHome() {
  state = null;
  $('view-group').hidden = true;
  $('view-home').hidden = false;
  history.pushState({}, '', '/');
  renderRecent();
}

async function openGroup(code, { push = true } = {}) {
  try {
    const data = await apiCall('GET', `/api/groups/${encodeURIComponent(code)}`);
    state = data;
    rememberGroup(data.group.code, data.group.name);
    $('view-home').hidden = true;
    $('view-group').hidden = false;
    if (push) history.pushState({ code: data.group.code }, '', `/${data.group.code}`);
    renderGroup();
  } catch (err) {
    toast(err.message, true);
    showHome();
  }
}

/* ── απόδοση παρέας ─────────────────────────────────────── */

function renderGroup() {
  $('group-title').textContent = state.group.name;
  $('group-code').textContent = state.group.code;
  $('group-total').textContent = money(state.totalCents);

  renderPayerOptions();
  renderParticipants();
  renderExpenses();
  renderSettlements();
  renderBalances();
  renderMembers();
}

function renderPayerOptions() {
  const select = $('expense-payer');
  const previous = select.value;
  select.replaceChildren(...state.members.map((member) => {
    const option = document.createElement('option');
    option.value = String(member.id);
    option.textContent = member.name;
    return option;
  }));
  if (state.members.some((m) => String(m.id) === previous)) select.value = previous;
}

function renderParticipants() {
  const ids = new Set(state.members.map((m) => m.id));
  // Καθαρίζουμε επιλογές μελών που δεν υπάρχουν πια· by default όλοι μέσα.
  selectedParticipants = new Set([...selectedParticipants].filter((id) => ids.has(id)));
  if (selectedParticipants.size === 0) selectedParticipants = new Set(ids);

  $('participant-list').replaceChildren(...state.members.map((member) => {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'chip';
    chip.textContent = member.name;
    chip.setAttribute('aria-pressed', String(selectedParticipants.has(member.id)));
    chip.addEventListener('click', () => {
      if (selectedParticipants.has(member.id)) selectedParticipants.delete(member.id);
      else selectedParticipants.add(member.id);
      chip.setAttribute('aria-pressed', String(selectedParticipants.has(member.id)));
    });
    return chip;
  }));
}

function renderExpenses() {
  const list = $('expense-list');
  if (state.expenses.length === 0) {
    list.replaceChildren(emptyItem('Δεν υπάρχουν έξοδα ακόμα.'));
    return;
  }

  const nameOf = new Map(state.members.map((m) => [m.id, m.name]));

  list.replaceChildren(...state.expenses.map((expense) => {
    const li = document.createElement('li');

    const main = document.createElement('div');
    main.className = 'expense-main';
    const title = document.createElement('strong');
    title.textContent = expense.description;
    const meta = document.createElement('span');
    meta.className = 'expense-meta';
    const forWhom = expense.participantIds.length === state.members.length
      ? 'όλους'
      : expense.participantIds.map((id) => nameOf.get(id) || '—').join(', ');
    meta.textContent = `${expense.payerName} πλήρωσε · για ${forWhom}`;
    main.append(title, meta);

    const right = document.createElement('div');
    right.className = 'expense-right';
    const amount = document.createElement('span');
    amount.className = 'amount';
    amount.textContent = money(expense.amountCents);
    const remove = document.createElement('button');
    remove.className = 'delete-btn';
    remove.type = 'button';
    remove.title = 'Διαγραφή';
    remove.setAttribute('aria-label', `Διαγραφή: ${expense.description}`);
    remove.textContent = '×';
    remove.addEventListener('click', () => deleteExpense(expense.id));
    right.append(amount, remove);

    li.append(main, right);
    return li;
  }));
}

function renderSettlements() {
  const list = $('settlement-list');
  if (state.settlements.length === 0) {
    list.replaceChildren(emptyItem(
      state.totalCents === 0 ? 'Πρόσθεσε έξοδα για να δεις τη μοιρασιά.' : 'Είστε πάτσι! 🎉'
    ));
    return;
  }

  list.replaceChildren(...state.settlements.map((transfer) => {
    const li = document.createElement('li');
    const text = document.createElement('span');
    text.append(
      strong(transfer.fromName),
      span(' → ', 'arrow'),
      strong(transfer.toName)
    );
    const amount = document.createElement('span');
    amount.className = 'amount';
    amount.textContent = money(transfer.amountCents);
    li.append(text, amount);
    return li;
  }));
}

function renderBalances() {
  $('balance-list').replaceChildren(...state.balances.map((balance) => {
    const li = document.createElement('li');
    li.append(document.createTextNode(balance.name));
    const amount = document.createElement('span');
    amount.className = `amount ${balance.balanceCents >= 0 ? 'positive' : 'negative'}`;
    amount.textContent = (balance.balanceCents > 0 ? '+' : '') + money(balance.balanceCents);
    li.append(amount);
    return li;
  }));
}

function renderMembers() {
  $('member-list').replaceChildren(...state.members.map((member) => {
    const li = document.createElement('li');
    li.textContent = member.name;
    return li;
  }));
}

const strong = (text) => { const el = document.createElement('strong'); el.textContent = text; return el; };
const span = (text, className) => { const el = document.createElement('span'); el.className = className; el.textContent = text; return el; };
const emptyItem = (text) => { const li = document.createElement('li'); li.className = 'empty'; li.textContent = text; return li; };

/* ── ενέργειες ──────────────────────────────────────────── */

async function deleteExpense(id) {
  try {
    state = await apiCall('DELETE', `/api/groups/${state.group.code}/expenses/${id}`);
    renderGroup();
  } catch (err) {
    toast(err.message, true);
  }
}

function addMemberInput(value = '') {
  const row = document.createElement('div');
  row.className = 'member-row';
  const input = document.createElement('input');
  input.placeholder = 'Όνομα';
  input.maxLength = 40;
  input.value = value;
  const remove = document.createElement('button');
  remove.type = 'button';
  remove.textContent = '×';
  remove.title = 'Αφαίρεση';
  remove.addEventListener('click', () => {
    if ($('member-inputs').children.length > 2) row.remove();
  });
  row.append(input, remove);
  $('member-inputs').append(row);
  return input;
}

/* ── σύνδεση γεγονότων ──────────────────────────────────── */

$('add-member-input').addEventListener('click', () => addMemberInput().focus());

$('create-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const members = [...$('member-inputs').querySelectorAll('input')]
    .map((input) => input.value.trim())
    .filter(Boolean);

  try {
    const data = await apiCall('POST', '/api/groups', {
      name: $('group-name').value,
      members,
    });
    state = data;
    rememberGroup(data.group.code, data.group.name);
    $('view-home').hidden = true;
    $('view-group').hidden = false;
    history.pushState({ code: data.group.code }, '', `/${data.group.code}`);
    renderGroup();
    toast(`Η παρέα δημιουργήθηκε · κωδικός ${data.group.code}`);
  } catch (err) {
    toast(err.message, true);
  }
});

$('join-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const code = $('join-code').value.trim().toUpperCase();
  if (code) openGroup(code);
});

$('expense-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    state = await apiCall('POST', `/api/groups/${state.group.code}/expenses`, {
      description: $('expense-description').value,
      amount: $('expense-amount').value,
      payerId: Number($('expense-payer').value),
      participantIds: [...selectedParticipants],
    });
    $('expense-description').value = '';
    $('expense-amount').value = '';
    renderGroup();
    $('expense-description').focus();
  } catch (err) {
    toast(err.message, true);
  }
});

$('toggle-all').addEventListener('click', () => {
  const all = state.members.map((m) => m.id);
  selectedParticipants = selectedParticipants.size === all.length ? new Set() : new Set(all);
  renderParticipants();
});

$('member-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    state = await apiCall('POST', `/api/groups/${state.group.code}/members`, {
      name: $('new-member').value,
    });
    $('new-member').value = '';
    renderGroup();
  } catch (err) {
    toast(err.message, true);
  }
});

$('copy-link').addEventListener('click', async () => {
  const link = `${location.origin}/${state.group.code}`;
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
  if (/^[A-Z0-9]{6}$/.test(code)) openGroup(code, { push });
  else {
    $('view-group').hidden = true;
    $('view-home').hidden = false;
    renderRecent();
  }
}

addMemberInput();
addMemberInput();
boot();
