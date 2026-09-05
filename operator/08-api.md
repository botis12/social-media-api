# 08 — API Design

REST + SSE. No GraphQL (one client, known queries). All routes under `/v1`. Auth via Clerk session JWT → `user_id` set as `app.user_id` in the Postgres session, which activates RLS.

Conventions: cursor pagination (`?cursor=&limit=`), `X-Request-Id` on everything, `Idempotency-Key` required on all POSTs that cause side effects, `409` on idempotency replay with the original result.

## Auth & onboarding
```
POST   /v1/auth/session                      exchange Clerk token → app session
GET    /v1/me                                user + profile + onboarding state
PATCH  /v1/me/profile                        goals, ICP, brief_hour, working hours

GET    /v1/oauth/google/start?scopes=...     → consent URL (incremental scopes)
GET    /v1/oauth/google/callback             stores encrypted refresh token
POST   /v1/onboarding/targets                { targets: ["ACME", "Kostas Petrou"] }
POST   /v1/onboarding/start-ingest           enqueues backfill
GET    /v1/onboarding/progress               SSE: {pct, messages, people, facts[]}
GET    /v1/onboarding/reveal                 the wow payload (see below)
```

`GET /v1/onboarding/reveal` — the single most important response in the product:
```json
{
  "totals": { "people": 2104, "strong": 68, "cooling": 17, "companies": 412 },
  "primary_route": {
    "target": { "label": "ACME", "company_id": "..." },
    "path_id": "...",
    "hops": [ { "person": {...}, "evidence": {...} } ],
    "confidence": "high",
    "why": "Maria has made 3 introductions for you before. Two converted."
  },
  "other_routes": [ ... ],
  "no_route_for": [ { "label": "Kostas Petrou", "nearest": {...} } ],
  "dormant_value": {
    "count": 9, "reach": 340,
    "people": [ { "person": {...}, "was_strength": 88, "silent_days": 540 } ]
  }
}
```

## Graph
```
GET    /v1/people?q=&tier=&temperature=&company_id=&cursor=
GET    /v1/people/{id}                       full dossier
PATCH  /v1/people/{id}                       user overrides: title, exclude, notes
POST   /v1/people/{id}/notes
GET    /v1/people/{id}/interactions?cursor=
GET    /v1/people/{id}/paths                 what this person unlocks

GET    /v1/companies?q=&watchlisted=
GET    /v1/companies/{id}

GET    /v1/relationships?tier=strong&temperature=cooling
GET    /v1/graph/neighborhood?person_id=&depth=2    for the path visualiser only
```

## Paths & targets — the hero endpoints
```
GET    /v1/targets
POST   /v1/targets                           { label, person_id?, company_id?, why? }
PATCH  /v1/targets/{id}                      status transitions
DELETE /v1/targets/{id}

POST   /v1/paths/find                        { target: {...}, max_hops: 2, refresh: false }
       → 200 { paths: [ { hops[], score, confidence, evidence[] } ] }
GET    /v1/paths/{id}                        cached path + full evidence
GET    /v1/paths/{id}/evidence               the raw interactions behind each hop
```

`POST /v1/paths/find` should answer in **< 800ms p95** from cache and < 4s cold. It is the demo. Treat its latency as a product requirement, not an engineering detail.

## Threads & search
```
GET    /v1/threads?commercial=true&ball_in_court=user&stalled_gt=7&cursor=
GET    /v1/threads/{id}
PATCH  /v1/threads/{id}                      { deal_value_cents, currency, stage }  ← user only
GET    /v1/search?q=&types=people,threads,companies    hybrid retrieval
```

## Signals, brief, meetings
```
GET    /v1/signals?state=new&severity_gte=2
POST   /v1/signals/{id}/dismiss
POST   /v1/signals/{id}/act                  → creates an agent_action

GET    /v1/brief/today
GET    /v1/brief/{date}
POST   /v1/brief/{id}/feedback               { item_id, useful: bool }   ← ranking training data

GET    /v1/meetings?from=&to=
GET    /v1/meetings/{id}/brief               generates on demand if missing
POST   /v1/meetings/{id}/outcome             { outcome, note }
POST   /v1/meetings/{id}/followup            → drafts follow-up
```

## The agent
```
POST   /v1/agent/messages                    SSE stream
       body: { conversation_id?, text, mode: "suggest"|"prepare"|"execute" }
       events: token · tool_call · tool_result · action_proposed · done · error

GET    /v1/agent/conversations
GET    /v1/agent/conversations/{id}
POST   /v1/agent/tools/{tool}/invoke         direct tool call (used by UI buttons,
                                             bypasses the LLM entirely — fast + free)
```

`POST /v1/agent/tools/find_paths/invoke` is how the **[ FIND A PATH ]** button works. Do not route deterministic UI actions through the model. This keeps the product fast and cheap, and it's the difference between a product and a chat wrapper.

## Actions & approvals
```
GET    /v1/actions?state=awaiting_approval
GET    /v1/actions/{id}
PATCH  /v1/actions/{id}                      edit the draft → new payload_hash, new token
POST   /v1/actions/{id}/approve              { approval_token }  → queued (30s undo window)
POST   /v1/actions/{id}/cancel               works during the undo window
POST   /v1/actions/{id}/reject               { reason }          → feeds learning
GET    /v1/actions/{id}/result

GET    /v1/introductions
PATCH  /v1/introductions/{id}                { state, outcome_note, outcome_value_cents }
```

## Permissions, integrations, privacy
```
GET    /v1/permissions
PATCH  /v1/permissions/{scope_kind}/{scope_key}   { level, constraints }
POST   /v1/permissions/panic                      → all levels to READ, cancel queued actions

GET    /v1/integrations
POST   /v1/integrations/{id}/resync
DELETE /v1/integrations/{id}                      revoke at Google + purge tokens

GET    /v1/privacy/exclusions
POST   /v1/privacy/exclusions                     { domains[], emails[] }
POST   /v1/privacy/export                         async → signed R2 URL
DELETE /v1/account                                hard delete, ≤24h, emailed confirmation

GET    /v1/activity?cursor=                       the audit log, in plain language
```

`POST /v1/permissions/panic` — one button, always reachable, drops the agent to READ and cancels everything queued. You will never use it. Its existence is what makes founders willing to enable EXECUTE.

## Webhooks & internal
```
POST   /v1/webhooks/google/pubsub            Gmail push notifications
POST   /v1/webhooks/stripe
GET    /internal/health · /internal/ready · /internal/metrics
```

## Error shape
```json
{ "error": { "code": "recipient_not_in_graph",
             "message": "I won't email someone you've never corresponded with.",
             "detail": { "email": "ceo@acme.com" },
             "request_id": "req_..." } }
```
User-facing `message` is written in the Operator's voice, always. Error copy is product copy.
