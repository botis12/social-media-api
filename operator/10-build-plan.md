# 10 — Build Plan, First 10 Actions, and the Wow Moment

## Part 1 — The 16-week roadmap

Assumed team: **you + 1 senior full-stack engineer + 1 designer (half-time for 8 weeks)**. Budget breakdown in [12-risks-and-verdict.md](12-risks-and-verdict.md).

### Week 0 — Do not write code (5 days)
The **Concierge Test**. Ten founders you can reach. Signed one-pager giving you read access to their mailbox (or an mbox export). You run the graph analysis by hand — Python notebook, no product. You deliver a PDF: their network map, their 10 dormant strong ties, and three routes into companies they name. **Charge €500.**

Kill criteria: fewer than 6 pay, or fewer than 4 act on a route within 14 days, or more than 3 say "my real relationships are on WhatsApp." Any of those and you stop and rethink — that is €100k saved and it is the highest-ROI week in this plan.

In parallel, on day 1: create the Google Cloud project, submit OAuth verification, and start the CASA engagement. It runs in the background for the next 8–12 weeks. See [09-security.md](09-security.md).

### Weeks 1–2 — Ingestion
- Repo, CI, Fly/Neon/Vercel, Clerk auth, Sentry/PostHog.
- Google OAuth with incremental scopes; encrypted token storage.
- Gmail backfill: chunked, resumable, quota-throttled. Calendar + Contacts sync.
- Noise filter and identity resolution. **Spend real time here** — graph precision determines everything downstream, and a graph polluted with newsletters is worse than no graph.
- **Milestone:** ingest your own mailbox end to end and eyeball the person list. If it's full of `noreply@`, nothing else matters yet.

### Weeks 3–4 — The graph
- Relationship strength, percentile normalisation, tempo model, cooling detection.
- Edge inference from co-recipients and co-attendance.
- Path finding (≤2 hops, scored, with evidence).
- pgvector embeddings for threads and person summaries.
- Eval harness + first golden sets.
- **Milestone:** `POST /v1/paths/find` returns a correct, evidence-backed route on 5 real mailboxes. **This is the make-or-break week.** If paths are wrong or obvious, the product thesis is wrong.

### Weeks 5–6 — Onboarding and the Reveal
- Landing, invite, goal question, scoped consent, live progress screen.
- The Reveal screen and the Dormant Value Report.
- Person detail page.
- **Milestone:** a founder who has never seen the product goes from click to Reveal in under 6 minutes and says something involuntary.
- **Ship to the 10 concierge founders.** Real users, week 6.

### Weeks 7–8 — The agent
- LLM gateway with task-based routing, cost metering, prompt caching.
- 11 tools, typed. Recipes for `find_path`, `prepare_intro`, `draft_reply`.
- Approval flow: `agent_action` state machine, tokens, 30s undo, audit log.
- `send_email` execution through the founder's Gmail.
- **Milestone:** a design partner sends a real, product-drafted intro request and a real human replies.

### Weeks 9–10 — Signals and retention
- Signal detectors: job change, cooling, ball-in-court, dormant return, new path unlocked.
- Daily Brief generation + email delivery + the **suppression rule** (no news, no send).
- TODAY screen.
- **Milestone:** 10 partners receiving briefs; measure brief→click. If it's under 30%, your ranking is wrong — fix ranking before building anything new.

### Weeks 11–12 — Meetings and the desktop overlay
- Meeting brief generation at T–30, calendar-triggered.
- Post-meeting outcome capture + follow-up drafting.
- Tauri shell: global hotkey, command palette, menubar pill.
- **Milestone:** partners report opening the overlay before meetings without being reminded.

### Weeks 13–14 — Harden and instrument
- Deal Threads (commercial classifier, user-entered value, stall detection).
- Full permission settings UI; panic button; privacy/export/delete flows.
- Outcome tracking: introductions, states, conversions. **Wire this properly — it is the moat.**
- Load, quota, and failure testing. Pen test.
- Eval scores against the ship bars in [07 §2.5](07-tech-and-models.md).

### Weeks 15–16 — Price and sell
- Stripe, trial mechanics, billing.
- Convert design partners to paid. This is the real test.
- Expand to 40–60 invited founders (still under the 100 cap).
- **Milestone:** ≥30% of activated partners paying, and ≥1 reported outcome per user per month.

### What slips first if you're behind
In order: desktop overlay → Deal Threads → post-meeting follow-up → company pages. **Never cut:** path finding, the Reveal, approval mechanics, the daily brief suppression rule.

---

## Part 2 — The first 10 agent actions that make it feel magical

Ordered by (perceived magic ÷ effort). Every one is evidence-backed; none require prediction.

**1. Find the route.** *"Get me to the CEO of ACME."* → 3 ranked paths with the actual email counts, dates and threads behind each hop. The founding demo.

**2. Prepare the intro request.** Drafts to the *connector*, not the target — the correct social move — in the founder's voice, referencing the specific thread where the connector and target co-occurred. The competence signal.

**3. The dormant value report.** *"9 people who were strong 18 months ago are silent. Together they reach 340 people, 4 of them at your targets."* Zero prediction, 100% verifiable, and nothing else can show it.

**4. Job-change alert with the outreach already written.** *"Dimitris left ACME for Northwind two days ago."* + a two-line congratulations draft. The highest-conversion outreach trigger in business, delivered before LinkedIn tells them.

**5. Ball-in-court sweep.** *"You owe 6 people replies. The oldest is 21 days and it's a €-thread."* Ranked by relationship value × age. Pure recovered revenue.

**6. The meeting brief.** Who, where you left it, what they said last time that they've forgotten they said, three questions, two risks. Generated at T–30 without being asked. The daily habit.

**7. Personalized cooling detection.** *"You and Petros normally speak every 40 days. It's been 94."* Per-relationship tempo. Everyone else ships a global 30-day rule; this one line makes founders say "how does it know that."

**8. Reply drafted with real memory.** *"Draft the reply to Nikos"* → and it opens by answering the margin question he asked nine days ago, because it read the thread. Not a summary — the actual next message.

**9. "Who should I talk to this week?"** Ranked by relationship value × decay × relevance to open targets, with a one-line reason each. This is the chief-of-staff moment.

**10. The unresolved-offer finder.** *"Two months ago Maria offered to introduce you to two more hotel groups. You never replied."* Extracting unaccepted offers from historical mail is cheap, and it recovers money the founder already left on the table. In testing this reliably produces the loudest reaction of anything on this list.

Note what is **not** here: summarizing documents, generating content, answering general questions, scheduling. Those are commodity. Everything above requires the graph.

---

## Part 3 — THE WOW MOMENT

### The design constraint
It must land **within 6 minutes of signup**, be **impossible to fake without their data**, require **zero forward-looking prediction** (so it cannot be wrong), and be **verifiable in 5 seconds** — the founder must be able to check it and find it true.

That rules out the daily brief (needs time), radar (needs the future), and chat (they've seen chat).

### The moment: **THE REVEAL**

The founder answered one question at signup — *who do you need to reach?* Four minutes later, the loading screen resolves into:

```
        ALEX — here is what you actually have.

        2,104 real relationships.   68 strong.   17 going cold.

        ─────────────────────────────────────────────────────

        YOUR ROUTE INTO ACME

        YOU ──── MARIA K. ──── DIMITRIS V. ──── ACME
                 214 emails      CTO
                 6 meetings      Maria cc'd him on
                 last: 11d ago   3 threads, Mar 2024

        HIGH confidence. Maria has made 3 introductions
        for you before. Two of them became customers.

              [ SEE THE EVIDENCE ]   [ PREPARE THE ASK ]

        ─────────────────────────────────────────────────────

        And something you probably didn't know:

        Two months ago Maria offered to introduce you to
        two more hotel groups. You never replied.

                                        [ SHOW ME ]
```

### Why this works, mechanically

1. **It answers the exact question they typed 4 minutes earlier.** Not a generic tour — *their* question, which they are still holding in their head.
2. **Every number is checkable.** "214 emails" — they can search Gmail and confirm. The moment they verify one number, they believe all of them. Do not put a single unverifiable claim on this screen.
3. **The last block is the kill shot.** "You never replied" is not intelligence *about* their network — it's a fact about their own behaviour that they had forgotten and that cost them money. Nobody has ever shown them that. It reframes the product from "a tool" to "a thing that catches what I drop."
4. **It admits what it doesn't know.** Include the honest miss ("no route to Kostas Petrou yet"). Founders are professional bullshit detectors. Admitting a gap is what makes the hits credible.
5. **The only CTA is an action, not a tour.** `PREPARE THE ASK` moves them straight from insight to execution, which is the entire product loop, experienced in under ten minutes.

### The sentence you're engineering for

> *"Wait — how does it know that? …that's actually right."*

Both halves matter. Surprise alone is a parlour trick. Surprise plus verification is trust, and trust is what gets them to grant EXECUTE.

### The demo version
For sales calls, the same thing, live, on the prospect's own inbox, in six minutes, while they watch. Founders sell this to each other after seeing it once. **That is your entire go-to-market for the first 100 users** — no ads, no content, no outbound.
