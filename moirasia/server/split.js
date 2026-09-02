'use strict';

/**
 * Pure money logic. Every amount is an integer number of cents so that no
 * rounding error can ever appear in a balance.
 */

/**
 * Split `amountCents` between `n` participants as evenly as possible.
 * The remainder cents are handed out one by one to the first participants,
 * so the shares always add up exactly to the original amount.
 *
 * @param {number} amountCents positive integer
 * @param {number} n number of participants (>= 1)
 * @returns {number[]} share per participant, same order as given
 */
function splitEvenly(amountCents, n) {
  if (!Number.isInteger(amountCents) || amountCents < 0) {
    throw new Error('amountCents must be a non-negative integer');
  }
  if (!Number.isInteger(n) || n < 1) {
    throw new Error('n must be a positive integer');
  }
  const base = Math.floor(amountCents / n);
  const remainder = amountCents % n;
  return Array.from({ length: n }, (_, i) => base + (i < remainder ? 1 : 0));
}

/**
 * Net balance per member: what they paid minus what they consumed.
 * Positive = the group owes them, negative = they owe the group.
 *
 * @param {{id:number}[]} members
 * @param {{amountCents:number, payerId:number, participantIds:number[]}[]} expenses
 * @returns {Map<number, number>} memberId -> balance in cents
 */
function computeBalances(members, expenses) {
  const balances = new Map(members.map((m) => [m.id, 0]));

  for (const expense of expenses) {
    if (!balances.has(expense.payerId)) continue;
    const participants = expense.participantIds.filter((id) => balances.has(id));
    if (participants.length === 0) continue;

    balances.set(expense.payerId, balances.get(expense.payerId) + expense.amountCents);

    const shares = splitEvenly(expense.amountCents, participants.length);
    participants.forEach((id, i) => {
      balances.set(id, balances.get(id) - shares[i]);
    });
  }

  return balances;
}

/**
 * Turn balances into the smallest practical list of payments.
 * Greedy: the biggest debtor always pays the biggest creditor. This clears at
 * least one person per transfer, so it never needs more than (people - 1)
 * payments — far fewer than everyone paying everyone.
 *
 * @param {Map<number, number>} balances
 * @returns {{fromId:number, toId:number, amountCents:number}[]}
 */
function settle(balances) {
  const debtors = [];
  const creditors = [];

  for (const [id, amount] of balances) {
    if (amount < 0) debtors.push({ id, amount: -amount });
    else if (amount > 0) creditors.push({ id, amount });
  }

  // Deterministic order: largest first, then by id so results are stable.
  const bySize = (a, b) => b.amount - a.amount || a.id - b.id;
  debtors.sort(bySize);
  creditors.sort(bySize);

  const transfers = [];
  let i = 0;
  let j = 0;

  while (i < debtors.length && j < creditors.length) {
    const amount = Math.min(debtors[i].amount, creditors[j].amount);
    if (amount > 0) {
      transfers.push({ fromId: debtors[i].id, toId: creditors[j].id, amountCents: amount });
    }
    debtors[i].amount -= amount;
    creditors[j].amount -= amount;
    if (debtors[i].amount === 0) i++;
    if (creditors[j].amount === 0) j++;
  }

  return transfers;
}

module.exports = { splitEvenly, computeBalances, settle };
