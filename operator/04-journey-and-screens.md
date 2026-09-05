# 04 — User Journey, Screen Map & Wireframes

## Part 1 — The user journey, minute by minute

### T+0:00 — Arrival
Invite-only. The landing page has one field: an invite code or an email for the waitlist. No pricing page, no feature grid, no "book a demo". The founder was sent here by another founder. Scarcity is the acquisition strategy and the brand simultaneously.

Copy on the page — one line, no hero illustration:

> **You know 3,000 people. You can remember 150.**
> The Operator reads your inbox and gives you the map.

### T+0:20 — Auth
"Continue with Google." One button. Login and data grant are **separated**: this first grant is login + `contacts.readonly` only. Gmail is asked for *after* the founder states a goal — because a founder who has just told you they want to reach ACME will grant Gmail access; a founder on a cold signup screen will not.

This ordering is the single highest-leverage decision in onboarding.

### T+0:45 — The one question
Full-screen, dark, single input, nothing else on screen:

```
        Who do you need to reach?

        ┌────────────────────────────────────────────┐
        │  ACME, Hotel Group Iberia, Kostas Petrou   │
        └────────────────────────────────────────────┘

        Companies or people. Three is enough.
                                          [ CONTINUE ]
```

No profile forms, no company setup, no "what industry are you in", no persona quiz. One question, because it is the question the product exists to answer and it primes the wow.

### T+1:10 — The grant, with a reason
```
  To find your routes into ACME, I need to read
  who you've emailed — not to send anything.

  ✓ Read email metadata and thread content
  ✓ Read your calendar
  ✗ Never send without your explicit approval
  ✗ Never share your data with anyone

  Revoke in one click. Delete everything in one click.

                        [ CONNECT GMAIL ]
```

Explicitly naming what you *won't* do converts better than any trust badge.

### T+1:30 → T+5:00 — The build (never a blank spinner)
Progressive, honest, and **the founder watches their own life scroll past.** This is dead time turned into a trust-building performance:

```
  BUILDING YOUR MAP

  ████████████████░░░░░░░░  62%

  ✓ 41,209 messages scanned
  ✓ 3,847 people identified
  ✓ 612 filtered as noise
  ▸ Scoring 2,104 real relationships…

  "Found: 214 exchanges with Maria K. since 2019"
  "Found: 8 people who now work somewhere new"
```

Live-ticking specifics. This is where the product first feels alive. Never show a percentage without a fact next to it.

### T+5:00 — **THE WOW** (full detail in [10-build-plan.md §15](10-build-plan.md))
Not a dashboard. A single, quiet, undeniable screen:

```
  ALEX — here is what you actually have.

  2,104 real relationships.   68 strong.   17 going cold.

  ──────────────────────────────────────────────────

  YOUR ROUTE INTO ACME

  YOU ──── MARIA K. ──── DIMITRIS V. ──── ACME
           214 emails      CTO, ACME
           last: 11d ago    Maria cc'd him
                            on 3 threads, Mar 2024

  Confidence: HIGH — Maria has made 3 introductions
  for you before. Two became customers.

           [ SEE THE EVIDENCE ]   [ PREPARE THE ASK ]

  ──────────────────────────────────────────────────

  Also: 2 routes into Hotel Group Iberia.
        No route to Kostas Petrou yet — but Maria
        knows 2 people at his last company.
```

Note the last line. **Admitting the miss is what makes the hits credible.** A product that finds everything is lying.

### T+6:30 — First recommendation, unprompted
Below the fold, one card, not ten:

```
  ◆ 9 relationships that were strong 18 months ago
    are now silent. Together they connect you to
    340 people, including 4 at companies on your list.

                                    [ SHOW ME ]
```

This is the **Dormant Value Report**. It requires zero forward-looking prediction, it is 100% verifiable, and no other product on earth can show it to them.

### T+8:00 — First agent action
The founder clicks `PREPARE THE ASK`. The Operator drafts an intro request **to Maria**, not to the CEO — the correct social protocol, which itself signals competence:

```
  DRAFT — to Maria K.

  Subject: Small ask — Dimitris at ACME

  Maria — hope Lisbon went well.

  Quick one: I'm trying to get in front of Dimitris V.
  at ACME about [ ← one line from you ]. I saw you were
  on a thread with him last March. Would you be
  comfortable making an intro? Totally fine if not.

  Happy to send you a forwardable blurb.

  — Alex

  ⓘ Written from your last 50 sent emails. You write short,
    you open with context, you always give an out.

  [ EDIT ]   [ REGENERATE ]   [ APPROVE & SEND ]
```

The `ⓘ` line is important: showing *why* the draft sounds like them converts a suspicious founder into a believer.

Approval is a real, deliberate, two-second action. It sends from their own Gmail, threaded correctly, and lands in their Sent folder. **The founder must be able to verify in Gmail that the product did exactly what it said.**

### T+8:30 — The loop closes
```
  ✓ Sent to Maria K. — 10:42
    I'll watch for a reply and tell you when she answers.
```

Now the product has an open commitment with the founder, which is the strongest possible reason to come back tomorrow.

### Day 2, 07:30 — First Daily Brief
Email + in-app. Five items, max. If there is nothing new, **it does not send** — and the app says "Nothing today. That's the point." This restraint is what separates you from every newsletter product that trained users to ignore it.

### Day 4 — First outcome
Maria replies. The Operator detects the reply on that thread, links it to the `introduction` record, and asks:

```
  Maria replied. Did she make the intro?
  [ YES ]  [ NOT YET ]  [ NO ]
```

`YES` → the Operator increments Maria's intro-success record, offers to prepare the follow-up to Dimitris, and — critically — **learns**. Twelve months of this is the moat.

---

## Part 2 — Complete V1 screen map

| # | Screen | Route | Purpose | Priority |
|---|---|---|---|---|
| 0 | Landing / invite | `/` | Scarcity + one promise | P0 |
| 1 | Onboarding: goal | `/onboarding/goal` | The one question | P0 |
| 2 | Onboarding: connect | `/onboarding/connect` | Scoped consent | P0 |
| 3 | Onboarding: building | `/onboarding/building` | Live trust performance | P0 |
| 4 | **The Reveal** | `/onboarding/reveal` | The wow | P0 |
| 5 | **TODAY** | `/today` | Home. 3 moves + state of network | P0 |
| 6 | **OPERATOR** | `/operator` | Agent chat + tools | P0 |
| 7 | **PATHS** | `/paths` | Watchlist targets + live routes | P0 |
| 8 | Path detail | `/paths/[targetId]` | Ranked routes + evidence | P0 |
| 9 | **PEOPLE** (search-first) | `/people` | Search, filters: strong / cooling / new | P0 |
| 10 | Person detail | `/people/[id]` | Relationship intelligence | P0 |
| 11 | **MEETING BRIEF** | `/meetings/[id]` | Who / context / objective / questions / risks | P0 |
| 12 | **DAILY BRIEF** | `/brief/[date]` | The 5 things | P0 |
| 13 | Approval / action detail | `/actions/[id]` | Review, edit, approve, send | P0 |
| 14 | Activity & audit log | `/activity` | Every tool call and send, reversible where possible | P0 |
| 15 | Company detail | `/companies/[id]` | Who we know there, threads, routes | P1 |
| 16 | Deal Threads | `/threads` | Stalled commercial threads, ball-in-court | P1 |
| 17 | Settings: permissions | `/settings/permissions` | Per-tool READ/SUGGEST/PREPARE/EXECUTE | P0 |
| 18 | Settings: integrations | `/settings/integrations` | Connect, resync, revoke | P0 |
| 19 | Settings: privacy & data | `/settings/privacy` | Export, delete, excluded domains/people | P0 |
| 20 | Settings: profile & voice | `/settings/profile` | Goals, ICP, tone samples, brief time | P1 |
| 21 | Command palette (⌘K) | overlay | Global; the desktop overlay's twin | P0 |
| 22 | Desktop overlay | Tauri | Hotkey command center | P1 (target wk 12) |

**Deliberately absent:** dashboard, reports, pipeline board, notifications inbox, global graph, contact-create form, task manager.

---

## Part 3 — Wireframes

Design tokens assumed throughout: near-black ground (`#0A0A0B`), one warm accent (`#C9A227` muted gold) used **only** for the single highest-priority action on screen, IBM Plex Mono / SF Mono for all numerals, generous negative space, no cards-in-cards, no gradients, no glass. Density in the data, calm in the chrome.

### SCREEN 5 — TODAY

```
┌──────────────────────────────────────────────────────────────────────────┐
│  THE OPERATOR                                    Tue 4 Feb · 08:14   ⌘K  │
│  ─────────────────────────────────────────────────────────────────────── │
│                                                                          │
│                                                                          │
│   GOOD MORNING, ALEX                                                     │
│   Three moves worth making today.                                        │
│                                                                          │
│                                                                          │
│   ── 01 ──────────────────────────────────────────────────────────────   │
│                                                                          │
│   Maria hasn't replied about the ACME intro                              │
│   Sent 4 days ago. Her median reply time to you is 1.2 days.             │
│                                                                          │
│   [ DRAFT A NUDGE ]        [ LEAVE IT ]                                  │
│                                                                          │
│   ── 02 ──────────────────────────────────────────────────────────────   │
│                                                                          │
│   Dimitris V. left ACME. He's now at Northwind.                          │
│   Detected from his new sending domain, 2 days ago.                      │
│   Your route into ACME is now stale — but you have a new                 │
│   route into Northwind.                                                  │
│                                                                          │
│   [ SEE ROUTES ]           [ CONGRATULATE HIM ]                          │
│                                                                          │
│   ── 03 ──────────────────────────────────────────────────────────────   │
│                                                                          │
│   You owe Hotel Group Iberia a reply — 9 days                            │
│   Thread: "Q1 supply proposal" · 4 participants                          │
│   They sent last. This is the oldest ball in your court.                 │
│                                                                          │
│   [ OPEN THREAD ]          [ DRAFT REPLY ]                               │
│                                                                          │
│   ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│   2,104 relationships    68 strong    17 cooling    5 targets            │
│   14:00 — Nikos P. (Hotel Iberia)              Brief ready →             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

Notes: no charts. No euro number unless the founder entered one. Every claim carries its evidence inline ("her median reply time is 1.2 days") because that's what makes it feel like intelligence rather than a reminder app.

### SCREEN 6 — OPERATOR

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← TODAY                    OPERATOR                                ⌘K   │
│  ─────────────────────────────────────────────────────────────────────── │
│                                                                          │
│   YOU                                                                    │
│   I want a meeting with the CEO of ACME.                                 │
│                                                                          │
│   OPERATOR                                                               │
│   ⟢ searched 2,104 people · 3 paths found · 0.9s                         │
│                                                                          │
│   ACME's CEO is Elena R. Three routes:                                   │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐     │
│   │ 1 · MARIA K. → ELENA R.                              HIGH      │     │
│   │   You↔Maria: 214 emails, 6 meetings, last 11d ago              │     │
│   │   Maria↔Elena: 31 emails, co-attended 2 events 2024            │     │
│   │   Maria has made 3 intros for you. 2 converted.                │     │
│   │                                            [ EVIDENCE ]        │     │
│   ├────────────────────────────────────────────────────────────────┤     │
│   │ 2 · JOHN M. → ACME CFO → ELENA R.                    MEDIUM    │     │
│   │   2 hops inside ACME. Slower, but John owes you one.           │     │
│   ├────────────────────────────────────────────────────────────────┤     │
│   │ 3 · COLD OUTREACH                                    LOW       │     │
│   │   You share 1 event with Elena (Athens, Oct 2023).             │     │
│   └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│   Maria is the route. She's warm, she's proven, and she                  │
│   replies to you in ~1 day. I'd ask her, not Elena.                      │
│                                                                          │
│   [ PREPARE THE INTRO REQUEST ]   [ TRY ROUTE 2 ]   [ WHY NOT COLD? ]    │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────── │
│  │ Ask the Operator…                                          PREPARE ▾│  │
└──────────────────────────────────────────────────────────────────────────┘
```

Notes: the tool trace line (`⟢ searched 2,104 people · 3 paths found · 0.9s`) is deliberate — visible work builds trust and it's cheap. The permission mode (`PREPARE ▾`) lives in the composer, so the founder always knows what the agent is currently allowed to do without leaving the screen.

### SCREEN 7 — PATHS

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PATHS                                                    + ADD TARGET   │
│  ─────────────────────────────────────────────────────────────────────── │
│                                                                          │
│   ACME                                        3 routes    ● route open   │
│   Elena R., CEO                               Maria K. asked 4d ago      │
│   ────────────────────────────────────────────────────────────────────   │
│   HOTEL GROUP IBERIA                          2 routes    ● in progress  │
│   Nikos P., Head of Procurement               meeting today 14:00        │
│   ────────────────────────────────────────────────────────────────────   │
│   NORTHWIND                                   1 route     ◆ NEW          │
│   Dimitris V. joined 2 days ago               strongest route: direct    │
│   ────────────────────────────────────────────────────────────────────   │
│   KOSTAS PETROU                               0 routes    ○ no path      │
│   Nearest: Maria knows 2 people at his                                   │
│   former employer. [ EXPLORE ]                                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### SCREEN 8 — PATH DETAIL (this replaces your Network screen in V1)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← PATHS               ACME · Elena R., CEO                              │
│  ─────────────────────────────────────────────────────────────────────── │
│                                                                          │
│         ┌────────┐        ┌──────────┐        ┌──────────┐               │
│         │  YOU   │━━━━━━━━│ MARIA K. │━━━━━━━━│ ELENA R. │               │
│         └────────┘  ████  └──────────┘  ██░░  └──────────┘               │
│                    strong               medium                           │
│                                                                          │
│              └─────── JOHN M. ──── D. PAPPAS ────┘                       │
│                        ██░░           █░░░                               │
│                                                                          │
│   ─────────────────────────────────────────────────────────────────────  │
│   EVIDENCE — YOU ↔ MARIA                                                 │
│   214 messages · 6 meetings · first contact Mar 2019                     │
│   Her median reply to you: 1.2 days (yours to her: 0.7)                  │
│   Last: "Re: Lisbon" — 11 days ago                                       │
│                                                                          │
│   EVIDENCE — MARIA ↔ ELENA                                               │
│   3 threads where both appear (Mar 2024, Sep 2024, Jan 2025)             │
│   Co-attended: Hospitality Summit, Athens, Oct 2023                      │
│   ⚠ Inferred from shared threads. I have not seen them                   │
│     email each other directly.                                           │
│                                                                          │
│                       [ PREPARE THE INTRO REQUEST ]                      │
└──────────────────────────────────────────────────────────────────────────┘
```

The `⚠ inferred` disclosure is mandatory. Second-hop edges are weaker evidence and pretending otherwise is how you get a founder to make an embarrassing ask.

### SCREEN 10 — PERSON DETAIL

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← PEOPLE                                                                │
│                                                                          │
│   MARIA K.                                              ████████░░  82   │
│   Partner, Kalyx Ventures · Athens                      STRONG           │
│   Last contact 11 days ago · you replied last                            │
│                                                                          │
│   ─────────────────────────────────────────────────────────────────────  │
│   HISTORY          214 messages · 6 meetings · since Mar 2019            │
│   RHYTHM           you speak every ~18 days · currently on time          │
│   HOW YOU MET      intro from Petros L., Mar 2019 ("Re: Kalyx")          │
│   RECIPROCITY      she initiates 46% · she replies in ~1.2d              │
│                                                                          │
│   ─────────────────────────────────────────────────────────────────────  │
│   SHE INTRODUCED YOU TO                                                  │
│   Investor X (Sep 2021) → became investor                                │
│   Hotel Group Iberia (Feb 2024) → became customer                        │
│   Dimitris V. / ACME (Mar 2024) → no outcome recorded                    │
│                                                                          │
│   SHE UNLOCKS                                                            │
│   4 of your 5 targets are ≤2 hops through her.                           │
│   She is your single highest-leverage relationship.                      │
│                                                                          │
│   ─────────────────────────────────────────────────────────────────────  │
│   RECENT CONTEXT                                                         │
│   11d — "Re: Lisbon" — she's moving her fund's ops to Lisbon in Q2       │
│   2mo — "Iberia intro" — she offered to intro to two more hotel groups   │
│         ⚠ You never followed up on this.                                 │
│                                                                          │
│   [ DRAFT A MESSAGE ]   [ FIND A PATH THROUGH HER ]   [ ADD A NOTE ]     │
└──────────────────────────────────────────────────────────────────────────┘
```

The line `⚠ You never followed up on this` is, in my view, the single most valuable string in the entire product. It's pure recovered value from data they already had.

### SCREEN 11 — MEETING BRIEF (auto-generated T–30min)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  14:00 · NIKOS P. · Hotel Group Iberia · 45 min · Zoom       in 28 min   │
│  ─────────────────────────────────────────────────────────────────────── │
│                                                                          │
│   WHO                                                                    │
│   Nikos P. — Head of Procurement, Hotel Group Iberia (2 yrs).            │
│   You've met twice. Introduced by Maria K., Feb 2024.                    │
│   Relationship: MEDIUM (61) · warming                                    │
│                                                                          │
│   WHERE YOU LEFT IT                                                      │
│   9 days ago he sent the Q1 supply proposal and asked for               │
│   your margin structure. You have not replied.                           │
│   In Nov he said budget decisions happen "after the board                │
│   meets in February." The board met last week.                           │
│                                                                          │
│   OBJECTIVE                                                              │
│   Leave with a decision date and the name of whoever signs.              │
│                                                                          │
│   ASK THESE                                                              │
│   1. How did the February board discussion land on supply?               │
│   2. Who signs this, and what do they need to see?                       │
│   3. What would make this a Q1 decision instead of Q2?                   │
│                                                                          │
│   RISKS                                                                  │
│   · Your 9-day silence on the margin question. Address it                │
│     in the first 60 seconds — don't let him raise it.                    │
│   · He's mentioned a competitor's pricing twice since Dec.               │
│                                                                          │
│   TACTICS                                                                │
│   He writes in bullets and replies in under an hour. Direct,             │
│   operational, low on preamble. Lead with the margin answer.             │
│                                                                          │
│                   [ OPEN THE THREAD ]      [ FULL HISTORY ]              │
└──────────────────────────────────────────────────────────────────────────┘
```

After the meeting ends, a single line appears on TODAY: `How did Nikos go? [ WELL ] [ BADLY ] [ PREPARE FOLLOW-UP ]`.

### SCREEN 12 — DAILY BRIEF (email + in-app, identical content)

```
┌──────────────────────────────────────────────────────────────────────────┐
│   TUESDAY 4 FEBRUARY                                                     │
│   THE FIVE THINGS                                                        │
│                                                                          │
│   01   Dimitris V. left ACME for Northwind — 2 days ago.                 │
│        Your ACME route is stale. Northwind is now direct.                │
│                                                                          │
│   02   Maria hasn't replied about the intro. 4 days;                     │
│        she normally answers in 1.2.                                      │
│                                                                          │
│   03   Hotel Iberia: 9 days, ball in your court. Meeting at 14:00.       │
│                                                                          │
│   04   Petros L. is cooling — 94 days, and you two normally              │
│        speak every 40. He's introduced you to 5 people.                  │
│                                                                          │
│   05   14:00 Nikos P. — brief is ready.                                  │
│                                                                          │
│   ─────────────────────────────────────────────────────────────────────  │
│   Two moves I'd make today:                                              │
│   → Reply to Iberia before 14:00.                                        │
│   → Nudge Maria.                                                         │
│                                    [ DO BOTH ]                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### SCREEN 13 — APPROVAL

```
┌──────────────────────────────────────────────────────────────────────────┐
│   APPROVE — SEND EMAIL                                                   │
│                                                                          │
│   TO      maria.k@kalyx.vc                                               │
│   FROM    alex@yourco.com  (your Gmail)                                  │
│   THREAD  new                                                            │
│   SUBJECT Small ask — Dimitris at ACME                                   │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐     │
│   │ Maria — hope Lisbon went well.                                 │     │
│   │                                                                │     │
│   │ Quick one: I'm trying to get in front of Dimitris V. at ACME   │     │
│   │ about our supply partnership. I saw you were on a thread with  │     │
│   │ him last March. Would you be comfortable making an intro?      │     │
│   │ Totally fine if not.                                           │     │
│   │                                                                │     │
│   │ Happy to send a forwardable blurb.                             │     │
│   │                                                                │     │
│   │ — Alex                                                         │     │
│   └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│   ⓘ WHY THIS DRAFT                                                       │
│     Tone matched to your last 50 sent messages (short, context           │
│     first, always offers an out). Asked Maria, not Elena —               │
│     asking the target directly wastes the warm route.                    │
│                                                                          │
│   [ EDIT ]   [ REGENERATE ]   [ CANCEL ]        [ APPROVE & SEND ]       │
│                                                                          │
│   ☐ Let me approve sends like this in one click from now on              │
└──────────────────────────────────────────────────────────────────────────┘
```

That last checkbox is how a user *earns their way up* the permission ladder themselves, rather than you asking them to configure a matrix.

### SCREEN 21/22 — COMMAND PALETTE & DESKTOP OVERLAY

Same component, two hosts. `⌘K` in the web app; a global hotkey (`⌥Space`) for the Tauri overlay. Opens over anything, centered, 620px, one input.

```
        ┌──────────────────────────────────────────────────┐
        │  ▸ how do I get to the CEO of ACME_               │
        ├──────────────────────────────────────────────────┤
        │  ⟢ 3 moves        ⟢ ball in your court: 2        │
        │  ⟢ 14:00 Nikos P. — brief ready                  │
        ├──────────────────────────────────────────────────┤
        │  Maria K.          strong · 11d                  │
        │  Nikos P.          medium · today 14:00          │
        │  Find a path…                                    │
        │  Draft an email…                                 │
        │  Who's going cold?                               │
        └──────────────────────────────────────────────────┘
```

The idle (unfocused) state of the desktop overlay is a 180×32px pill in the menu bar area:

```
   ● OPERATOR   3 moves · 2 owed · 14:00
```

No euro figure unless the founder has entered deal values. No red badges. No bounce animations. **A premium product never begs.**
