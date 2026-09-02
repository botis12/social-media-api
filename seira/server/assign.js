'use strict';

/**
 * Ο πυρήνας της εφαρμογής: ανάθεση αγγαρειών σε άτομα με ελάχιστο συνολικό
 * "κόστος δυσαρέσκειας".
 *
 * Δεν είναι κλήρωση ούτε απλός κύκλος: λύνεται ως πρόβλημα ανάθεσης
 * (assignment problem) με τον αλγόριθμο Hungarian, ώστε να ισορροπούν
 * ταυτόχρονα τρία πράγματα — προτιμήσεις, δίκαιο μοίρασμα του φόρτου,
 * και αποφυγή επανάληψης της ίδιας αγγαρείας.
 */

const COST = {
  // Το «το προτιμώ» αντέχει έναν επαναλαμβανόμενο γύρο (-6 vs +5), όχι δύο.
  LIKE: -6,
  NEUTRAL: 0,
  DISLIKE: 8, // «το αποφεύγω»
  REPEAT: 5, // ανά συνεχόμενο γύρο στην ίδια αγγαρεία
  LOAD: 3, // ανά μονάδα φόρτου πάνω από τον ελαφρύτερο
  EXTRA_TASK: 25, // δεύτερη (τρίτη...) αγγαρεία στον ίδιο γύρο
};

/**
 * Hungarian algorithm (O(n^3), παραλλαγή με συντομότερα μονοπάτια).
 * Βρίσκει την ανάθεση κάθε γραμμής σε ξεχωριστή στήλη με το ελάχιστο άθροισμα.
 *
 * @param {number[][]} cost πίνακας γραμμές x στήλες, με γραμμές <= στήλες
 * @returns {number[]} για κάθε γραμμή, ο δείκτης της στήλης της
 */
function solveAssignment(cost) {
  const n = cost.length;
  if (n === 0) return [];
  const m = cost[0].length;
  if (m < n) throw new Error('Χρειάζονται τουλάχιστον όσες στήλες και γραμμές.');

  const INF = Infinity;
  const u = new Array(n + 1).fill(0); // δυναμικά «potentials» γραμμών
  const v = new Array(m + 1).fill(0); // ...και στηλών
  const p = new Array(m + 1).fill(0); // στήλη -> γραμμή
  const way = new Array(m + 1).fill(0);

  for (let i = 1; i <= n; i++) {
    p[0] = i;
    let j0 = 0;
    const minv = new Array(m + 1).fill(INF);
    const used = new Array(m + 1).fill(false);

    do {
      used[j0] = true;
      const i0 = p[j0];
      let delta = INF;
      let j1 = 0;

      for (let j = 1; j <= m; j++) {
        if (used[j]) continue;
        const cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
        if (cur < minv[j]) {
          minv[j] = cur;
          way[j] = j0;
        }
        if (minv[j] < delta) {
          delta = minv[j];
          j1 = j;
        }
      }

      for (let j = 0; j <= m; j++) {
        if (used[j]) {
          u[p[j]] += delta;
          v[j] -= delta;
        } else {
          minv[j] -= delta;
        }
      }
      j0 = j1;
    } while (p[j0] !== 0);

    do {
      const j1 = way[j0];
      p[j0] = p[j1];
      j0 = j1;
    } while (j0);
  }

  const rowToColumn = new Array(n).fill(-1);
  for (let j = 1; j <= m; j++) {
    if (p[j] > 0) rowToColumn[p[j] - 1] = j - 1;
  }
  return rowToColumn;
}

/**
 * Μικρή, σταθερή «ζαριά» ώστε οι ισοπαλίες να μη λύνονται πάντα υπέρ του ίδιου
 * ατόμου. Είναι ντετερμινιστική (ίδιος γύρος -> ίδιο αποτέλεσμα), άρα ελέγξιμη.
 */
function tieBreak(roundIndex, personId, taskId) {
  return (((roundIndex * 31 + personId * 17 + taskId * 7) % 11) / 11) * 0.9;
}

function preferenceCost(score) {
  if (score > 0) return COST.LIKE;
  if (score < 0) return COST.DISLIKE;
  return COST.NEUTRAL;
}

/**
 * Φτιάχνει τον πίνακα κόστους: μία γραμμή ανά αγγαρεία, μία στήλη ανά «θέση»
 * ατόμου. Κάθε άτομο παίρνει `capacity` θέσεις, ώστε να καλυφθούν όλες οι
 * αγγαρείες ακόμη κι όταν τα άτομα είναι λιγότερα από αυτές.
 */
function buildCostMatrix({ people, tasks, prefs, loads, streaks, roundIndex }) {
  const capacity = Math.ceil(tasks.length / people.length);
  const minLoad = Math.min(...people.map((person) => loads.get(person.id) || 0));
  const averageWeight =
    tasks.reduce((total, task) => total + (task.weight || 1), 0) / tasks.length;

  const slots = [];
  for (let copy = 0; copy < capacity; copy++) {
    for (const person of people) slots.push({ person, copy });
  }

  const matrix = tasks.map((task) =>
    slots.map(({ person, copy }) => {
      const score = prefs.get(`${person.id}:${task.id}`) || 0;
      const load = loads.get(person.id) || 0;

      // Η γνώμη μετράει λίγο περισσότερο στις βαριές αγγαρείες, αλλά όχι
      // τριπλάσια: αλλιώς ένα «το προτιμώ» καθηλώνει όλο τον πίνακα.
      const opinionScale = 1 + ((task.weight || 1) - 1) / 2;
      let cost = preferenceCost(score) * opinionScale;
      // Ο φόρτος πρέπει να δένει με το βάρος της αγγαρείας. Αν ήταν σκέτη
      // ποινή ανά άτομο, όταν τα άτομα είναι όσα και οι αγγαρείες θα ήταν
      // σταθερή σε κάθε συνδυασμό — δηλαδή θα ακυρωνόταν. Έτσι, όποιος έχει
      // κάνει πολλά σπρώχνεται προς τις ελαφριές αγγαρείες.
      cost += COST.LOAD * (load - minLoad) * ((task.weight || 1) / averageWeight);
      cost += COST.EXTRA_TASK * copy;
      // Όσο περισσότερους συνεχόμενους γύρους κρατάει κάποιος την ίδια
      // αγγαρεία, τόσο ακριβότερο γίνεται να του ξαναπέσει.
      cost += COST.REPEAT * (streaks.get(`${person.id}:${task.id}`) || 0);
      cost += tieBreak(roundIndex, person.id, task.id);

      return cost;
    })
  );

  return { matrix, slots };
}

/**
 * Παράγει τον επόμενο γύρο.
 *
 * @param {{id:number}[]} people διαθέσιμα άτομα
 * @param {{id:number, weight:number}[]} tasks
 * @param {Map<string, number>} prefs "personId:taskId" -> -1 | 0 | 1
 * @param {Map<number, number>} loads συσσωρευμένος φόρτος ανά άτομο
 * @param {Map<string, number>} streaks "personId:taskId" -> συνεχόμενοι γύροι στην ίδια αγγαρεία
 * @param {number} roundIndex
 * @returns {{taskId:number, personId:number}[]}
 */
function planRound({ people, tasks, prefs, loads, streaks, roundIndex }) {
  if (people.length === 0) throw new Error('Δεν υπάρχει διαθέσιμο άτομο.');
  if (tasks.length === 0) throw new Error('Δεν υπάρχει καμία αγγαρεία.');

  const { matrix, slots } = buildCostMatrix({
    people,
    tasks,
    prefs,
    loads,
    streaks: streaks || new Map(),
    roundIndex,
  });

  const chosen = solveAssignment(matrix);
  return tasks.map((task, index) => ({
    taskId: task.id,
    personId: slots[chosen[index]].person.id,
  }));
}

module.exports = { solveAssignment, buildCostMatrix, planRound, COST };
