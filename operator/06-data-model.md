# 06 — Data Model

Full DDL: **[06-schema.sql](06-schema.sql)** (PostgreSQL 16 + pgvector + pg_trgm).

## Entity relationships

```
app_user ─1:1─ user_profile
   │
   ├─1:N─ integration ──(encrypted tokens, sync cursors)
   ├─1:N─ permission ───(integration × tool → READ|SUGGEST|PREPARE|EXECUTE)
   │
   ├─1:N─ company ─1:N─ person ─1:N─ person_email
   │                      │
   │                      └─1:N─ person_affiliation ──► company   (job history)
   │
   ├─1:N─ relationship (a_person ⇄ b_person; a=NULL means the founder)
   │
   ├─1:N─ thread ─1:N─ interaction ─1:N─ message_chunk (embeddings)
   ├─1:N─ meeting ─1:1─ meeting_brief
   │
   ├─1:N─ target ─1:N─ path ──► [person, person, ...]
   ├─1:N─ signal
   ├─1:N─ agent_action ─1:N─ introduction
   ├─1:N─ brief
   ├─1:N─ document
   └─1:N─ audit_log (append-only, hash-chained)
```

## Twelve design decisions worth defending

1. **`person` is per-user, not global.** Alex's "Maria K." and Nikos's "Maria K." are separate rows even if the same human. Global identity resolution across users is a privacy hazard and a V2 problem (it's also the enabling step for the cross-user network — the schema allows adding a nullable `global_person_id` later without migration pain).

2. **`relationship.a_person_id IS NULL` means the founder.** Avoids a synthetic self-person row and makes "my edges" a single indexed predicate. Second-hop edges (person↔person) live in the same table with `edge_type='inferred_*'` — one traversal query serves both.

3. **`strength` is a percentile, not an absolute.** Recomputed nightly across the user's whole graph. See [05 §5.7](05-agent-architecture.md).

4. **`tempo_median_days` on the edge is the product's soul.** Cooling is `days_since_last > 2 × tempo_median`, not a global constant.

5. **`thread.deal_value_cents` is user-entered only.** Enforced by convention *and* by never exposing a write path from the agent. The classifier may set `is_commercial` and `commercial_stage`; it may never set a number.

6. **`ball_in_court` is a first-class column, not a derived query.** It powers TODAY, the brief, and Deal Threads. Computed on every thread update.

7. **Bodies live in `message_chunk`, metadata in `interaction`.** You can purge all bodies for a user (retention policy, or a nervous enterprise buyer) and the entire graph, all scores, and all signals survive. This separation will win you a deal one day.

8. **`signal.evidence` is `NOT NULL`.** A signal you cannot explain is a bug. This constraint enforces the product philosophy in the database.

9. **`signal.dedupe_key` unique per user.** The single most common failure mode of a signal product is telling someone the same thing four times. Make it impossible.

10. **`agent_action` is a state machine with an `idempotency_key`.** Retries, queue redeliveries and double-clicks cannot double-send. `payload_hash` + single-use `approval_token_hash` means an approval authorizes exactly one payload.

11. **`agent_action.edit_diff` and `was_edited`.** This is the learning loop. It costs nothing to store and it is the basis of the voice model, drafting evals, and eventually a real quality metric ("edit rate").

12. **`audit_log` is hash-chained.** `row_hash = H(prev_hash || payload)`. Cheap tamper-evidence that turns into a real answer during security review.

## Indexing notes

- HNSW on all `VECTOR(1536)` columns; `m=16, ef_construction=64` is fine at V1 scale (~100 users × ~50k chunks = 5M vectors — comfortably single-node).
- `participant_ids UUID[]` with a GIN index makes "every interaction involving these two people" a single fast query — this is the hot path for the person page and for path evidence.
- Trigram indexes on names for the resolve step of retrieval.
- Partial index on `relationship (user_id, temperature)` where cooling/cold — small, hot, hit by every brief run.

## Retention

| Data | Default | Configurable |
|---|---|---|
| Message bodies (`message_chunk`) | 24 months rolling | Yes — down to 3 months |
| Interaction metadata + graph | Life of account | No (it *is* the product) |
| Embeddings | Follows bodies | — |
| `audit_log` | 24 months | No (compliance) |
| Deleted account | Hard delete ≤ 24h, backups purged ≤ 35d | — |
