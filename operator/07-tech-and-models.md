# 07 — Tech Architecture & AI Model Strategy

## Part 1 — The stack

Your instincts are right on frontend and database. I'd change two things (jobs and auth) and add one (a desktop shell).

```
┌───────────────────────────────────────────────────────────────────┐
│ CLIENTS                                                           │
│  Next.js 15 (App Router, RSC) · TypeScript · Tailwind · shadcn/ui  │
│  Tauri v2 desktop shell — global hotkey overlay + menubar pill     │
│  → Vercel                                                          │
└───────────────────────────┬───────────────────────────────────────┘
                            │  REST + SSE (streaming agent turns)
┌───────────────────────────▼───────────────────────────────────────┐
│ API — FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2 + Alembic   │
│  ├─ /agent      routing, tools, streaming                          │
│  ├─ /graph      people, paths, relationships                       │
│  ├─ /signals    radar, brief                                       │
│  └─ /actions    approvals, execution                               │
│  → Fly.io (2 regions: fra + iad), autoscaled                       │
└──────┬────────────────────────────────────┬───────────────────────┘
       │                                    │
┌──────▼──────────────────┐       ┌─────────▼─────────────────────┐
│ WORKERS — Procrastinate │       │ LLM GATEWAY (in-process)      │
│ (Postgres-backed queue) │       │ provider-agnostic router,     │
│  backfill · sync ·      │       │ retries, fallback, cost meter,│
│  edges · signals ·      │       │ prompt cache, eval hooks      │
│  briefs · outcomes      │       └─────────┬─────────────────────┘
└──────┬──────────────────┘                 │
       │                     ┌──────────────┼──────────────┐
┌──────▼──────────────────┐  │              │              │
│ PostgreSQL 16 + pgvector│  ▼              ▼              ▼
│  → Neon (branching for  │ Anthropic    OpenAI/other   Exa / Brave
│    safe migrations)     │ (reasoning,  (embeddings,   (web research,
│  RLS per user           │  drafting,   fallback)       V2 radar)
└─────────────────────────┘  tool use)
```

### Decisions and why

| Layer | Choice | Why (and what I rejected) |
|---|---|---|
| Frontend | **Next.js 15 + TS + Tailwind + shadcn** | Your call, and it's right. Use RSC for the read-heavy screens (TODAY, PEOPLE) and client components only for the agent stream. shadcn because you will restyle every primitive — a themed component library (MUI, Chakra) fights the design language in §DESIGN. |
| Desktop | **Tauri v2** | ~600KB binary vs Electron's 100MB, native global hotkey, Rust shell wrapping the same Next build. This is the retention surface; don't skip it. |
| Backend | **FastAPI + Pydantic v2** | Your call, right for this. The tool layer *is* Pydantic models; you get JSON Schema for the LLM tool definitions for free from the same types that validate execution. That's a genuine architectural win over a TS backend. |
| ORM | **SQLAlchemy 2.0 + Alembic** | Boring. You need real migrations and raw SQL escape hatches for the graph queries. Skip anything that hides SQL. |
| DB | **Postgres 16 + pgvector on Neon** | Your call. Neon over Supabase specifically for **branching** — you will re-run the whole graph pipeline over production-shaped data dozens of times, and a branch makes that a 3-second operation. HNSW indexes. Single node is fine to ~5M vectors. |
| Jobs | **Procrastinate** (Postgres-backed) | **This is my main change to your stack.** Celery+Redis adds a broker, a result backend, and a class of "task ran twice" bugs you don't need. Procrastinate puts the queue in the Postgres you already have: transactional enqueue (a job and the row it depends on commit together), no extra service, one connection string. Move to Temporal only if you later need multi-day durable workflows with human-in-the-loop timers — which, note, is exactly what approvals are, so revisit at ~1,000 users. |
| Cache / rate limits | **Upstash Redis** | Only for rate limiting, Gmail API quota tracking and SSE fan-out. Not for jobs. |
| Auth | **Clerk** | **Second change.** You wrote "recommend the best V1 option" — it's Clerk, and it is not close. Google-only social login, sessions, MFA, org support when you need teams, and 3 hours of integration. Do NOT roll your own, and do NOT use Supabase Auth just because you're using Postgres. Critically: **keep app login separate from the Google *data* grant.** Clerk handles who you are; your own OAuth flow handles the Gmail refresh token, because you need incremental scopes, your own consent screen copy, and control of the token lifecycle. |
| Secrets | **Cloud KMS envelope encryption** (GCP KMS or AWS KMS) | Per-integration DEK, wrapped by a KMS key, ciphertext in Postgres. See [09-security.md](09-security.md). |
| Email delivery | **Resend** | For the daily brief only. Founder-to-recipient mail always goes through *their* Gmail, never yours — deliverability and trust both demand it. |
| Files | **Cloudflare R2** | Zero egress fees, S3 API. |
| Observability | **Sentry + PostHog + Axiom** | PostHog for the activation funnel (it's the only metric that matters in month 1), Axiom for structured LLM call logs. Add **Langfuse** for prompt/trace/eval — worth it from week 3. |
| Payments | **Stripe** + Stripe Tax | EU VAT/MOSS will otherwise eat a week. |
| Deploy | Vercel (web) + Fly.io (api/workers) + Neon (db), GitHub Actions CI | ~€300/mo at V1 scale. Do not touch Kubernetes. Do not build a monorepo abstraction. Two apps, one DB. |

**Data residency:** run Neon and Fly in `eu-central` (Frankfurt). Your first 100 users are European founders; "your data never leaves the EU" is a free sales asset, and retrofitting it later is painful.

**What I'd deliberately not use in V1:** LangChain/LlamaIndex (you need 11 typed tools and a retrieval function — a framework here is pure liability and a debugging tax), a vector DB (pgvector is enough by an order of magnitude), Kafka/event streaming, a feature store, microservices, GraphQL, a monorepo build system.

---

## Part 2 — AI model strategy

### 2.1 The principle

**Route by task, not by loyalty.** The workload here splits cleanly into three very different jobs, and using one model for all three is how you end up either broke or dumb:

| Job | Volume | Quality bar | Latency | Right tier |
|---|---|---|---|---|
| **Bulk extraction** — classify every message, extract entities, detect commercial intent, parse signatures | ~10⁴ calls/user | "good enough, consistent" | async | **Cheapest capable** |
| **Reasoning & drafting** — path explanations, meeting briefs, emails in the founder's voice, agent tool use | ~10² calls/user/mo | "must be excellent" | 1–6s | **Frontier** |
| **Research** — external enrichment, V2 radar | ~10¹/user/mo | factual, cited | 10–60s | **Search-native** |

### 2.2 Honest comparison

I'll compare capability tiers rather than pretend to precise cross-vendor benchmarks; verify prices at build time, they move.

| Dimension | Claude (Anthropic) | OpenAI | Grok (xAI) |
|---|---|---|---|
| **Reasoning on messy human context** | Strongest of the three in my experience for "read this thread and tell me what's actually going on socially." This is the core task. | Very strong, competitive. | Adequate; not the differentiator. |
| **Tool use / structured output** | Excellent, and `strict: true` tool schemas + Pydantic gives you validated args end-to-end. Adaptive thinking is well suited to the planner track. | Excellent. Mature function calling. | Weaker track record for reliable multi-tool sequences. |
| **Drafting in a specific human's voice** | Best of the three. Least likely to produce "I hope this email finds you well." This matters enormously — a draft that sounds like an AI is worse than no draft. | Good, but has stronger default-register pull toward generic business English. | Uneven; risk of tonal drift you don't want in outbound email. |
| **Summarization / extraction at low cost** | Haiku 4.5 at $1/$5 per MTok is strong for the price. | Competitive small-model tier; benchmark both on *your* golden set. | Not a reason to choose it. |
| **Real-time / social web knowledge** | Web search tool available; general web. | Web search available. | **Genuinely differentiated on X/Twitter-native, recent signal.** For "did this person just announce something publicly", this is a real edge. |
| **Speed** | Haiku 4.5 for bulk; Opus 5 fast mode exists for latency-sensitive interactive turns. | Comparable. | Comparable. |
| **Cost** | Opus 5 $5/$25, Sonnet 5 $2/$10, Haiku 4.5 $1/$5 per MTok. 1M context on Opus/Sonnet 5. | Similar order of magnitude; verify. | Typically cheaper; not decisive at your volumes. |
| **Reliability / enterprise posture** | Strong; matters when you're asking founders to hand over their inbox. | Strong. | Least mature. Also consider brand fit: some EU founders will react badly to xAI in your privacy policy. |

### 2.3 The recommended architecture

**Do not choose one model. Build a gateway and route.**

```
                         ┌────────────────────┐
   task, context ───────►│   LLM GATEWAY      │
                         │  route · retry ·   │
                         │  fallback · cache ·│
                         │  cost meter · eval │
                         └─────────┬──────────┘
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
  BULK TIER                  REASONING TIER             RESEARCH TIER
  claude-haiku-4-5           claude-opus-5              Exa / Brave search
  $1 / $5 per MTok           $5 / $25 per MTok          + Grok for X-native
                             (Sonnet 5 $2/$10 for       signal (V2 only)
                              mid-tier tasks)
```

Task → model map:

| Task | Model | Rationale |
|---|---|---|
| Message classification (human/bulk/commercial) | `claude-haiku-4-5` | 10⁴ volume. Cheap, consistent, async. |
| Signature & job-title extraction | `claude-haiku-4-5` | Structured output, `strict: true`. |
| "X introduced me to Y" relation extraction | `claude-sonnet-5` | Higher value per extraction; worth the step up. |
| Thread & person rolling summaries | `claude-sonnet-5` | Quality feeds everything downstream. |
| **Path explanation** | `claude-opus-5` | The wow moment. Never cheap out here. |
| **Meeting brief** | `claude-opus-5`, effort `high` | Highest perceived-intelligence surface. |
| **Email drafting in founder's voice** | `claude-opus-5` | Voice fidelity is the whole game. |
| Agent chat / planner loop | `claude-opus-5`, adaptive thinking, streamed | Tool-use reliability. |
| Citation verifier (anti-hallucination pass) | `claude-haiku-4-5` | Cheap, narrow, runs on every generation. |
| Embeddings | third-party embedding model, 1536-dim | Pin the model; a change means a full re-embed. Store `embedding_model_version` per row. |
| Web research (V2) | Exa/Brave + Grok for X-native | Search API for retrieval, LLM for synthesis. |

**Abstraction, concretely** — keep it thin. Not a framework, one interface:

```python
class LLMProvider(Protocol):
    async def complete(self, *, task: TaskSpec, messages: list[Msg],
                       tools: list[ToolSpec] | None = None) -> LLMResult: ...

# TaskSpec carries: task_name, tier, max_tokens, effort, schema, cache_policy,
# and the eval_set it is graded against. The *task* picks the model, not the caller.
```

Every call site names a **task**, never a model. Model choice lives in one config table, which means switching a task to a different provider is a config change plus an eval run — not a refactor. That is the entire point of provider-agnosticism, and most teams get it wrong by abstracting the SDK instead of the task.

### 2.4 Cost model (verify against real usage in week 6)

For a founder with ~40,000 messages in the 24-month window:

**One-time backfill.** Aggressive pre-filtering is what makes this viable: only ~15% of messages are human, conversational and non-bulk. Extract at *thread* level, not message level → ~6,000 threads × (~2k input, ~200 output) on Haiku 4.5:

```
input   12.0M tok × $1/MTok  =  $12
output   1.2M tok × $5/MTok  =   $6
embeddings (~15M tok)        =  ~$2
                              ───────
                              ≈ $20 per user, once
```

**Ongoing, per user per month:**

```
incremental extraction (~1,800 threads, Haiku)      ≈ $ 5
daily briefs (22 × Sonnet 5, heavily cached)        ≈ $ 1
meeting briefs (~40 × Opus 5)                       ≈ $ 3
drafts (~60 × Opus 5)                               ≈ $ 3
agent chat (~100 turns, Sonnet/Opus mix, cached)    ≈ $ 4
                                                     ──────
                                                     ≈ $16 / user / month
```

At €249/mo that is **~6% COGS** — healthy, and it means you can afford Opus 5 on every surface the founder actually looks at. **Do not degrade the visible surfaces to save $3.** Degrade the invisible ones.

Three levers if costs run hot: (1) prompt caching on the stable prefix of every recipe — the founder profile and voice exemplars are identical across calls, and this is a large win; (2) batch the backfill (50% discount, and it's async by nature); (3) tighten the pre-filter before touching model tiers.

### 2.5 Evals — non-negotiable from week 3

You cannot ship a product whose core value is "it says true things about my life" without measuring whether it does. Four golden sets, ~50 examples each, built from your own inbox and design partners' (with consent):

| Eval | Metric | Bar to ship |
|---|---|---|
| `commercial_thread` classification | F1 | ≥ 0.85 |
| `intro_extraction` ("A introduced me to B") | precision | ≥ 0.90 (recall can be low; false intros are worse than missed ones) |
| `meeting_brief` | human rubric 1–5 on accuracy, specificity, actionability | ≥ 4.0 mean, **0 factual errors** |
| `draft_voice` | blind A/B vs. the founder's real emails | ≥ 40% indistinguishable |

Track **edit rate** on drafts in production as the north-star quality metric. It's free, it's honest, and it tells you more than any benchmark.
