# 05 — Agent Architecture

## 5.0 The governing principle

**Do not build a general ReAct agent that free-roams over tools.** That architecture is right for exploratory coding assistants and wrong here: your agent touches a founder's real relationships and can send real email. Latency, determinism and blast radius all matter more than flexibility.

Use a **two-track architecture**:

- **Track A — Recipes (90% of traffic).** Deterministic, typed pipelines with LLM-filled slots. `find_path`, `prepare_intro`, `meeting_brief`, `daily_brief`, `draft_reply`, `detect_cold`. Each is code that calls the model at specific, narrow points. Predictable cost, predictable latency, testable, no runaway loops.
- **Track B — Planner (10%).** A bounded tool-use loop for open-ended questions ("summarize everything I know about the hospitality vertical"). Hard caps: 8 steps, 60s, 40k context tokens, read-only tools unless the recipe layer escalates.

A router (cheap classifier + regex/intent match) picks the track. Most "AI agent" products fail because they put everything on Track B and then can't explain why the same question gives different answers on Tuesday.

## 5.1 The loop

```
                 ┌──────────────────────────────────────────┐
                 │  TRIGGER                                 │
                 │  user message · cron · webhook · calendar │
                 └────────────────────┬─────────────────────┘
                                      ▼
                        ┌─────────────────────────┐
                        │  ROUTE                  │  intent → recipe | planner
                        └────────────┬────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │  RETRIEVE               │  graph-first, then vector
                        │  entities → edges →     │  → rerank → assemble
                        │  threads → summaries    │
                        └────────────┬────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │  PLAN                   │  typed ActionPlan
                        └────────────┬────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │  PERMISSION GATE        │  READ|SUGGEST|PREPARE|EXECUTE
                        └────────┬───────┬────────┘
                        allowed  │       │  needs approval
                                 ▼       ▼
                    ┌────────────────┐  ┌──────────────────┐
                    │ EXECUTE        │  │ QUEUE FOR HUMAN  │
                    │ idempotent     │  │ (expires in 24h) │
                    └───────┬────────┘  └────────┬─────────┘
                            │                    │ approved
                            ▼◄───────────────────┘
                        ┌─────────────────────────┐
                        │  OBSERVE                │  did it work? reply? bounce?
                        └────────────┬────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │  WRITE MEMORY + AUDIT   │
                        └─────────────────────────┘
```

Every arrow crossing into EXECUTE writes an `agent_action` row first. **No side effect happens without a durable, user-visible record that precedes it.**

## 5.2 Tools (V1 — exactly these, no more)

| Tool | Level | Signature | Notes |
|---|---|---|---|
| `search_people` | READ | `(query, filters{strength,cooling,company,domain}) → Person[]` | Hybrid: trigram name + vector on profile |
| `get_person` | READ | `(person_id) → PersonDossier` | Includes edges, last N interactions, intro history |
| `find_paths` | READ | `(target: {person_id|company|free_text}, max_hops=2) → Path[]` | The hero tool. Returns evidence, never bare scores |
| `search_threads` | READ | `(query, {person_ids, date_range, commercial_only}) → Thread[]` | Hybrid BM25 + vector |
| `get_thread` | READ | `(thread_id) → Message[]` | Full bodies; the only tool that returns raw content |
| `get_calendar` | READ | `(range) → Event[]` | |
| `find_availability` | READ | `(duration, constraints) → Slot[]` | Respects working hours + buffers |
| `draft_email` | PREPARE | `(to, intent, context_ids[], tone) → Draft` | Always cites which context it used |
| `draft_intro_request` | PREPARE | `(connector_id, target_id, ask) → Draft` | Addresses the *connector*, not the target |
| `add_to_watchlist` | SUGGEST | `(entity) → Target` | |
| `create_reminder` | SUGGEST | `(subject, when, why) → Reminder` | |
| **`send_email`** | **EXECUTE** | `(draft_id, approval_token) → MessageId` | Requires a fresh approval token, single use |
| **`create_calendar_event`** | **EXECUTE** | `(event, approval_token) → EventId` | Requires approval token |

Rules: every tool is (1) typed with Pydantic, (2) scoped to `user_id` at the query layer — never by prompt instruction, (3) rate-limited, (4) audit-logged with arguments and a hash of the result, (5) returns entity IDs so the UI can render real, clickable objects rather than model prose.

**The model never sees another user's data because the model never issues SQL. It calls functions that take `user_id` from the session, not from the model.** This is the single most important security property in the system.

## 5.3 Memory

Four layers, deliberately distinct:

| Layer | Contents | Store | Refresh |
|---|---|---|---|
| **Founder profile** | Goals, targets, ICP, writing voice exemplars, do-not-contact list, preferences learned from edits | `user_profile` row + JSONB | On change; voice re-derived monthly |
| **Entity semantic memory** | Per-person and per-company rolling summary ("Nikos: procurement, direct, budget gated on Feb board") | `person.summary` + embedding | Regenerated when ≥N new interactions or ≥30 days |
| **Episodic memory** | Threads, messages, meetings, with embeddings | `interaction`, `message_chunk` | On ingest |
| **Outcome memory** | Every agent action, approval, edit, send, and its consequence | `agent_action`, `introduction`, `outcome` | On event |

The layer everyone forgets is **outcome memory**, and it's the one that compounds. Record: was the draft edited before sending (and the diff), did the recipient reply, how fast, did the intro convert. After ~6 months this is training data no competitor has.

**Edit-diff learning is the cheapest high-value feedback loop in the product.** If a founder deletes your closing line every time, stop writing it. Store diffs; feed the last 20 as few-shot examples in the drafting prompt.

## 5.4 Retrieval — graph first, vectors second

Naive RAG over an inbox is a bad idea: chunk-level semantic search returns plausible-but-wrong threads and blows context. The correct order:

```
1. RESOLVE     free text → entity IDs (people, companies) via trigram + alias table
2. TRAVERSE    graph query: edges, shared threads, meetings, intro history   ← structured, exact
3. RANK        deterministic scoring over the traversal result
4. VECTOR      only now: pgvector search *filtered to the resolved entity IDs*
5. RERANK      cross-encoder or a cheap-model rerank over ≤50 candidates
6. ASSEMBLE    typed context blocks with hard token budgets per block
```

Context budget for a drafting call, enforced in code:

```
person dossier            ≤ 1,200 tok
last 5 interaction summaries ≤ 1,500 tok
2 full recent messages    ≤ 1,500 tok
founder voice exemplars   ≤ 1,000 tok
task instruction          ≤   400 tok
                          ─────────────
                          ≤ 5,600 tok
```

Fixed budgets are why the product is fast and cheap. Unbounded context is why most agent products are neither.

## 5.5 Permissions

Four levels, exactly as you specified, applied per (integration × action):

| Level | Meaning | Default in V1 |
|---|---|---|
| **READ** | Access approved data | ON for Gmail, Calendar, Contacts |
| **SUGGEST** | Recommend an action; no artifact created | ON |
| **PREPARE** | Create a draft/proposal; nothing leaves the system | ON |
| **EXECUTE** | Perform the side effect | **OFF for everything** |

Escalation is earned, not configured up-front: after the founder approves the same *class* of action N times with a low edit rate, offer the upgrade inline ("You've approved 8 intro requests without edits. Let me send these automatically?"). Include a **standing kill switch** and an **undo window** (queue sends for 30 seconds, cancellable — cheap, and it's the single feature that makes people brave enough to enable EXECUTE).

Additional hard constraints that are not user-configurable in V1:
- Never email a recipient not already in the founder's graph.
- Never send more than 10 emails/day autonomously.
- Never send outside working hours.
- Never send to a domain on the founder's exclusion list.
- Never include a relationship score, or any internal metric, in outbound text. (Prompt-level *and* regex-level output filter. If Maria ever receives an email containing "confidence: 84%", the company is over.)

## 5.6 Approvals, errors, audit

**Approvals.** An `agent_action` in `awaiting_approval` carries a signed, single-use, 24h-TTL approval token bound to a hash of the exact payload. If the founder edits the draft, the hash changes and a new token is issued. This prevents both replay and "approve one thing, send another."

**Errors.** Classify and behave differently:

| Class | Example | Behaviour |
|---|---|---|
| Transient | Gmail 429/503 | Retry with jitter, ≤5 attempts, exponential |
| Auth | token revoked | Halt all jobs for that integration, notify the founder once, never retry-loop |
| Validation | recipient not in graph | Fail closed, surface to user with the reason |
| Model | malformed tool args, refusal | One repair attempt with the schema error, then fall back to a deterministic template; never silently produce prose in place of a tool call |
| Semantic | drafted email references a thread that doesn't exist | Caught by a **citation check**: every factual claim in a draft must map to a retrieved `interaction_id`. Unciteable claims are stripped before the founder sees them |

That last one is the anti-hallucination mechanism and it belongs in code, not in the prompt. Post-generation, run a verifier pass: extract claims → check each against retrieved IDs → drop or flag. Cheap model, ~200ms, and it is the difference between a product that's trusted and one that isn't.

**Audit.** Append-only `audit_log`, hash-chained (each row stores `prev_hash`), covering: every tool call with arguments, every retrieval (entity IDs only, not content), every model call (provider, model, tokens, latency, cost), every approval, every side effect with the external ID returned. Surfaced to the user at `/activity` in plain language. This is a compliance requirement *and* a trust feature — let them see it.

## 5.7 The graph math (this is the actual IP — specify it, don't hand-wave it)

### Relationship strength
Compute per directed pair, then symmetrize. Raw features:

```
v   = log(1 + message_count)                    volume
r   = exp(-Δt_days / halflife_pair)             recency (see tempo below)
m   = log(1 + meeting_count) * 1.6              meetings weigh ~2x email
b   = 1 - |sent - received| / (sent + received)  reciprocity balance
i   = min(inbound_initiations / total_threads, 1) they start conversations
l   = clamp(1 - median_reply_latency_hrs / 72)   they answer you fast
d   = log(1 + mean_thread_depth)                 real dialogue, not broadcast
c   = 1 - (cc_only_messages / message_count)     direct, not cc'd
p   = penalty: newsletter | no-reply | bulk | one-way → ×0.05
```

```
raw = (0.22v + 0.20r + 0.18m + 0.12b + 0.10i + 0.08l + 0.06d + 0.04c) * p
```

Then — and this matters more than the weights — **normalize to a percentile within that founder's own graph**:

```
strength = round(100 * percentile_rank(raw, all_raw_for_user))
```

A founder who sends 400 emails a day and one who sends 20 must both get a meaningful 0–100. Absolute thresholds are the reason competitors' scores feel arbitrary. Tiers: 80+ STRONG, 55–79 MEDIUM, 30–54 WEAK, <30 PERIPHERAL.

### Tempo & the "going cold" detector
Per pair, compute the distribution of inter-contact intervals:

```
tempo_median = median(gaps between contacts, last 24 months)
cooling if:  days_since_last > 2.0 * tempo_median  AND  strength >= 55
cold    if:  days_since_last > 3.5 * tempo_median  AND  strength >= 55
halflife_pair = clamp(tempo_median * 3, 30, 540)   # feeds `r` above
```

This is why it feels personal. A weekly friend at 3 weeks silent is *cooling*; a twice-a-year mentor at 3 weeks silent is fine. Every competitor ships a global 30-day rule; this one line of math is a visible, demoable differentiator.

### Path scoring
Edge cost as negative log-probability, then shortest path (Dijkstra over ≤2 hops, beam width 50):

```
P(hop A→B) = σ( 1.4*strength_norm(A,B)
              + 0.7*intro_willingness(B)      # historical: intros made / asked
              + 0.5*topic_affinity(B, target) # cosine(person summary, target)
              - 0.4*staleness(A,B)
              - 0.3*inferred_edge_penalty )   # co-occurrence only, no direct mail

P(path) = Π P(hop)
confidence = HIGH ≥0.55 · MEDIUM 0.25–0.55 · LOW <0.25
```

Return the top 3 paths **with the evidence rows that produced each term**. Never return a bare number.

### Edge inference (the hard part)
Direct edges (A emailed B) are certain. The valuable edges are second-hop, and you infer them from:
- **Co-recipients** on a thread (strongest inferable signal — weight by thread size; a 2-person cc is strong, a 40-person blast is worthless: `1/log(1+n_participants)`).
- **Co-attendance** on a calendar event (very strong; small meetings especially).
- **Forwarded/quoted headers** in message bodies.
- **Signature-block mentions** and explicit intro language ("copying Dimitris who runs…") — an extraction task worth spending a real model on, because "X introduced me to Y" is the highest-value fact in the entire corpus.

Always label inferred edges as inferred in the UI. See the `⚠` in the [Path Detail wireframe](04-journey-and-screens.md).

## 5.8 Background jobs

| Job | Cadence | Notes |
|---|---|---|
| `backfill_mailbox` | once, on connect | Chunked, resumable, checkpointed per Gmail page token |
| `sync_incremental` | every 5 min | Gmail History API + Calendar sync tokens |
| `recompute_edges` | nightly + on 50 new interactions | Incremental, only touched pairs |
| `detect_signals` | hourly | Job change, cooling, ball-in-court, new path unlocked |
| `generate_daily_brief` | per user, at their hour | **Skips if <2 items clear the bar** |
| `generate_meeting_brief` | T–30min | Scheduled at calendar sync time |
| `observe_outcomes` | every 15 min | Did the sent mail get a reply; close the loop |
| `expire_approvals` | hourly | 24h TTL |
