'use strict';

const { computeBalances, settle } = require('./split');

const MAX_NAME_LENGTH = 40;
const MAX_DESCRIPTION_LENGTH = 80;
const MAX_MEMBERS = 30;
const MAX_AMOUNT_CENTS = 100_000_000; // 1.000.000 €

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function cleanName(value, field) {
  if (typeof value !== 'string') throw new ApiError(400, `Το πεδίο "${field}" είναι υποχρεωτικό.`);
  const name = value.trim().replace(/\s+/g, ' ');
  if (!name) throw new ApiError(400, `Το πεδίο "${field}" δεν μπορεί να είναι κενό.`);
  if (name.length > MAX_NAME_LENGTH) {
    throw new ApiError(400, `Το πεδίο "${field}" ξεπερνά τους ${MAX_NAME_LENGTH} χαρακτήρες.`);
  }
  return name;
}

/** Accepts euros as a number or a string ("12,50" and "12.50" both work). */
function parseAmountToCents(value) {
  const raw = typeof value === 'string' ? value.trim().replace(',', '.') : value;
  const euros = Number(raw);
  if (!Number.isFinite(euros)) throw new ApiError(400, 'Το ποσό δεν είναι έγκυρος αριθμός.');
  const cents = Math.round(euros * 100);
  if (cents <= 0) throw new ApiError(400, 'Το ποσό πρέπει να είναι μεγαλύτερο από 0.');
  if (cents > MAX_AMOUNT_CENTS) throw new ApiError(400, 'Το ποσό είναι υπερβολικά μεγάλο.');
  return cents;
}

function loadGroup(store, code) {
  const group = store.getGroupByCode(String(code || '').toUpperCase());
  if (!group) throw new ApiError(404, 'Δεν βρέθηκε παρέα με αυτόν τον κωδικό.');
  return group;
}

/** Full read model for a group: members, expenses, balances and who pays whom. */
function groupState(store, group) {
  const members = store.getMembers(group.id);
  const expenses = store.getExpenses(group.id);
  const balances = computeBalances(members, expenses);
  const transfers = settle(balances);
  const nameOf = new Map(members.map((m) => [m.id, m.name]));

  return {
    group: { code: group.code, name: group.name, createdAt: group.createdAt },
    members,
    expenses: expenses.map((e) => ({ ...e, payerName: nameOf.get(e.payerId) || '—' })),
    totalCents: expenses.reduce((sum, e) => sum + e.amountCents, 0),
    balances: members.map((m) => ({
      memberId: m.id,
      name: m.name,
      balanceCents: balances.get(m.id) || 0,
    })),
    settlements: transfers.map((t) => ({
      ...t,
      fromName: nameOf.get(t.fromId) || '—',
      toName: nameOf.get(t.toId) || '—',
    })),
  };
}

function createGroup(store, body) {
  const name = cleanName(body?.name, 'όνομα παρέας');
  const rawMembers = Array.isArray(body?.members) ? body.members : [];
  const members = rawMembers.map((m) => cleanName(m, 'όνομα μέλους'));

  if (members.length < 2) throw new ApiError(400, 'Χρειάζονται τουλάχιστον 2 άτομα.');
  if (members.length > MAX_MEMBERS) throw new ApiError(400, `Το πολύ ${MAX_MEMBERS} άτομα.`);

  const unique = new Set(members.map((m) => m.toLocaleLowerCase('el')));
  if (unique.size !== members.length) throw new ApiError(400, 'Υπάρχουν διπλά ονόματα.');

  const group = store.createGroup(name, members);
  return groupState(store, group);
}

function addMember(store, code, body) {
  const group = loadGroup(store, code);
  const name = cleanName(body?.name, 'όνομα μέλους');
  const members = store.getMembers(group.id);

  if (members.length >= MAX_MEMBERS) throw new ApiError(400, `Το πολύ ${MAX_MEMBERS} άτομα.`);
  if (members.some((m) => m.name.toLocaleLowerCase('el') === name.toLocaleLowerCase('el'))) {
    throw new ApiError(400, 'Υπάρχει ήδη μέλος με αυτό το όνομα.');
  }

  store.addMember(group.id, name);
  return groupState(store, group);
}

function addExpense(store, code, body) {
  const group = loadGroup(store, code);
  const members = store.getMembers(group.id);
  const memberIds = new Set(members.map((m) => m.id));

  const description = cleanName(body?.description, 'περιγραφή').slice(0, MAX_DESCRIPTION_LENGTH);
  const amountCents = parseAmountToCents(body?.amount);

  const payerId = Number(body?.payerId);
  if (!memberIds.has(payerId)) throw new ApiError(400, 'Ο πληρωτής δεν ανήκει στην παρέα.');

  const requested = Array.isArray(body?.participantIds) ? body.participantIds : [];
  // No participants given = the whole group shares it.
  const participantIds = requested.length
    ? [...new Set(requested.map(Number))]
    : members.map((m) => m.id);

  if (participantIds.some((id) => !memberIds.has(id))) {
    throw new ApiError(400, 'Κάποιο μέλος της μοιρασιάς δεν ανήκει στην παρέα.');
  }
  if (participantIds.length === 0) throw new ApiError(400, 'Επίλεξε τουλάχιστον ένα άτομο.');

  participantIds.sort((a, b) => a - b);
  store.addExpense(group.id, { description, amountCents, payerId, participantIds });
  return groupState(store, group);
}

function deleteExpense(store, code, expenseId) {
  const group = loadGroup(store, code);
  const id = Number(expenseId);
  if (!Number.isInteger(id) || !store.deleteExpense(group.id, id)) {
    throw new ApiError(404, 'Το έξοδο δεν βρέθηκε.');
  }
  return groupState(store, group);
}

function getGroup(store, code) {
  return groupState(store, loadGroup(store, code));
}

module.exports = {
  ApiError,
  createGroup,
  getGroup,
  addMember,
  addExpense,
  deleteExpense,
  groupState,
  parseAmountToCents,
};
