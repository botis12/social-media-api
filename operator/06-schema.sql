-- THE OPERATOR — PostgreSQL 16 + pgvector schema (V1)
-- Design rules:
--   1. Every row that contains user data carries user_id. RLS enforces isolation.
--   2. The model never writes SQL; tools are user_id-scoped in application code AND at the DB layer.
--   3. Append-only where it matters (audit_log, agent_action transitions).
--   4. Raw message bodies are stored separately from metadata so we can drop them without losing the graph.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================ IDENTITY

CREATE TABLE app_user (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             CITEXT UNIQUE NOT NULL,
    name              TEXT,
    timezone          TEXT NOT NULL DEFAULT 'Europe/Athens',
    brief_hour        SMALLINT NOT NULL DEFAULT 7,
    status            TEXT NOT NULL DEFAULT 'onboarding'
                      CHECK (status IN ('onboarding','active','paused','deleting')),
    plan              TEXT NOT NULL DEFAULT 'trial',
    trial_ends_at     TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at        TIMESTAMPTZ
);

-- Founder context that drives every prompt. One row per user.
CREATE TABLE user_profile (
    user_id           UUID PRIMARY KEY REFERENCES app_user(id) ON DELETE CASCADE,
    company_name      TEXT,
    one_liner         TEXT,               -- what the business does, in their words
    goals             JSONB DEFAULT '[]', -- [{goal, horizon, created_at}]
    icp               TEXT,
    voice_exemplars   JSONB DEFAULT '[]', -- [{subject, body}] from their sent mail
    voice_notes       TEXT,               -- derived: "short, context-first, always offers an out"
    edit_patterns     JSONB DEFAULT '[]', -- learned from draft→sent diffs
    excluded_domains  TEXT[] DEFAULT '{}',
    excluded_emails   CITEXT[] DEFAULT '{}',
    working_hours     JSONB DEFAULT '{"start":"09:00","end":"19:00","days":[1,2,3,4,5]}',
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================ INTEGRATIONS & PERMISSIONS

CREATE TABLE integration (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    provider          TEXT NOT NULL CHECK (provider IN ('google_gmail','google_calendar','google_contacts')),
    external_account  CITEXT NOT NULL,
    scopes            TEXT[] NOT NULL,
    -- envelope-encrypted refresh token; DEK wrapped by KMS. Never plaintext, never logged.
    token_ciphertext  BYTEA NOT NULL,
    token_dek_wrapped BYTEA NOT NULL,
    token_key_version INT  NOT NULL DEFAULT 1,
    status            TEXT NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active','expired','revoked','error')),
    sync_cursor       TEXT,               -- Gmail historyId / Calendar syncToken
    backfill_state    JSONB DEFAULT '{}', -- {page_token, done_through, pct}
    last_sync_at      TIMESTAMPTZ,
    last_error        TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, provider, external_account)
);

CREATE TABLE permission (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    scope_kind        TEXT NOT NULL CHECK (scope_kind IN ('integration','tool')),
    scope_key         TEXT NOT NULL,      -- 'google_gmail' | 'send_email' | 'draft_email'
    level             TEXT NOT NULL DEFAULT 'prepare'
                      CHECK (level IN ('none','read','suggest','prepare','execute')),
    constraints       JSONB DEFAULT '{}', -- {max_per_day:10, hours:[9,19], require_known_recipient:true}
    granted_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    granted_via       TEXT,               -- 'default' | 'onboarding' | 'inline_upgrade'
    UNIQUE (user_id, scope_kind, scope_key)
);

-- ============================================================ ENTITIES

CREATE TABLE company (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    primary_domain    CITEXT,
    domains           CITEXT[] DEFAULT '{}',
    country           TEXT,
    summary           TEXT,
    summary_embedding VECTOR(1536),
    is_watchlisted    BOOLEAN NOT NULL DEFAULT false,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, primary_domain)
);
CREATE INDEX ON company USING gin (name gin_trgm_ops);
CREATE INDEX ON company (user_id, is_watchlisted);

CREATE TABLE person (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    display_name      TEXT,
    normalized_name   TEXT,
    primary_email     CITEXT,
    company_id        UUID REFERENCES company(id) ON DELETE SET NULL,
    title             TEXT,
    seniority         TEXT,               -- inferred: founder|c_level|vp|director|ic|unknown
    location          TEXT,
    -- rolling semantic memory about this person
    summary           TEXT,
    summary_embedding VECTOR(1536),
    summary_stale     BOOLEAN NOT NULL DEFAULT true,
    -- classification
    kind              TEXT NOT NULL DEFAULT 'human'
                      CHECK (kind IN ('human','automated','bulk','unknown')),
    is_excluded       BOOLEAN NOT NULL DEFAULT false,
    first_seen_at     TIMESTAMPTZ,
    last_seen_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON person (user_id, company_id);
CREATE INDEX ON person USING gin (normalized_name gin_trgm_ops);
CREATE INDEX ON person USING hnsw (summary_embedding vector_cosine_ops);

-- one person, many addresses (alias resolution)
CREATE TABLE person_email (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    person_id         UUID NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    email             CITEXT NOT NULL,
    is_primary        BOOLEAN NOT NULL DEFAULT false,
    first_seen_at     TIMESTAMPTZ,
    last_seen_at      TIMESTAMPTZ,
    UNIQUE (user_id, email)
);

-- employment history — this is what makes job-change detection possible
CREATE TABLE person_affiliation (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    person_id         UUID NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    company_id        UUID NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    title             TEXT,
    started_at        TIMESTAMPTZ,
    ended_at          TIMESTAMPTZ,
    evidence          JSONB,              -- {source:'domain_change', from:'acme.com', to:'northwind.io'}
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON person_affiliation (user_id, person_id, ended_at);

-- ============================================================ THE GRAPH

-- Edge between the founder and a person (from_person_id IS NULL means "the user").
-- Symmetric storage: one row per unordered pair, with directional counters inside.
CREATE TABLE relationship (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    a_person_id       UUID REFERENCES person(id) ON DELETE CASCADE,  -- NULL = the founder
    b_person_id       UUID NOT NULL REFERENCES person(id) ON DELETE CASCADE,

    edge_type         TEXT NOT NULL DEFAULT 'direct'
                      CHECK (edge_type IN ('direct','inferred_thread','inferred_meeting','inferred_stated')),

    strength          SMALLINT,           -- 0..100, percentile-normalized within this user's graph
    strength_raw      REAL,
    tier              TEXT GENERATED ALWAYS AS (
                        CASE WHEN strength >= 80 THEN 'strong'
                             WHEN strength >= 55 THEN 'medium'
                             WHEN strength >= 30 THEN 'weak'
                             ELSE 'peripheral' END) STORED,

    message_count     INT NOT NULL DEFAULT 0,
    sent_count        INT NOT NULL DEFAULT 0,
    received_count    INT NOT NULL DEFAULT 0,
    meeting_count     INT NOT NULL DEFAULT 0,
    thread_count      INT NOT NULL DEFAULT 0,
    cc_only_count     INT NOT NULL DEFAULT 0,

    first_contact_at  TIMESTAMPTZ,
    last_contact_at   TIMESTAMPTZ,
    last_direction    TEXT CHECK (last_direction IN ('inbound','outbound')),

    tempo_median_days REAL,               -- personal cadence for this pair
    reply_latency_p50 REAL,               -- their median hours to answer you
    temperature       TEXT DEFAULT 'ok'   -- ok | cooling | cold
                      CHECK (temperature IN ('ok','cooling','cold','new')),

    intro_asked_count INT NOT NULL DEFAULT 0,
    intro_made_count  INT NOT NULL DEFAULT 0,

    computed_at       TIMESTAMPTZ,
    -- NULLS NOT DISTINCT (PG15+) is required: a_person_id IS NULL means "the founder",
    -- and without it Postgres would allow duplicate founder-edges.
    UNIQUE NULLS NOT DISTINCT (user_id, a_person_id, b_person_id)
);
CREATE INDEX ON relationship (user_id, strength DESC);
CREATE INDEX ON relationship (user_id, temperature) WHERE temperature IN ('cooling','cold');
CREATE INDEX ON relationship (user_id, b_person_id);
CREATE INDEX ON relationship (user_id, a_person_id);

-- ============================================================ INTERACTIONS

CREATE TABLE thread (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    provider_thread_id TEXT NOT NULL,
    subject           TEXT,
    participant_count SMALLINT,
    message_count     SMALLINT,
    started_at        TIMESTAMPTZ,
    last_message_at   TIMESTAMPTZ,
    last_direction    TEXT CHECK (last_direction IN ('inbound','outbound')),
    -- commercial classification (NOT a value prediction)
    is_commercial     BOOLEAN DEFAULT false,
    commercial_stage  TEXT,               -- intro|scoping|proposal|negotiation|closed|dormant
    stalled_days      INT,
    ball_in_court     TEXT CHECK (ball_in_court IN ('user','them','none')),
    -- user-entered, never model-generated
    deal_value_cents  BIGINT,
    deal_currency     TEXT DEFAULT 'EUR',
    summary           TEXT,
    summary_embedding VECTOR(1536),
    UNIQUE (user_id, provider_thread_id)
);
CREATE INDEX ON thread (user_id, ball_in_court, last_message_at);
CREATE INDEX ON thread (user_id, is_commercial, stalled_days DESC);
CREATE INDEX ON thread USING hnsw (summary_embedding vector_cosine_ops);

-- Metadata for every message. Cheap, keeps the graph alive even if bodies are purged.
CREATE TABLE interaction (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    kind              TEXT NOT NULL CHECK (kind IN ('email','meeting','note','call')),
    thread_id         UUID REFERENCES thread(id) ON DELETE CASCADE,
    provider_id       TEXT,
    direction         TEXT CHECK (direction IN ('inbound','outbound','internal')),
    occurred_at       TIMESTAMPTZ NOT NULL,
    subject           TEXT,
    snippet           TEXT,               -- ≤300 chars, safe to show anywhere
    participant_ids   UUID[] NOT NULL DEFAULT '{}',
    from_person_id    UUID REFERENCES person(id) ON DELETE SET NULL,
    is_bulk           BOOLEAN DEFAULT false,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, kind, provider_id)
);
CREATE INDEX ON interaction (user_id, occurred_at DESC);
CREATE INDEX ON interaction USING gin (participant_ids);
CREATE INDEX ON interaction (user_id, thread_id, occurred_at);

-- Bodies, separated so retention/deletion policy can differ. Chunked + embedded.
CREATE TABLE message_chunk (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    interaction_id    UUID NOT NULL REFERENCES interaction(id) ON DELETE CASCADE,
    seq               SMALLINT NOT NULL,
    content           TEXT NOT NULL,
    content_tsv       TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    embedding         VECTOR(1536),
    token_count       SMALLINT
);
CREATE INDEX ON message_chunk USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON message_chunk USING gin (content_tsv);
CREATE INDEX ON message_chunk (user_id, interaction_id);

CREATE TABLE meeting (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    provider_event_id TEXT NOT NULL,
    title             TEXT,
    starts_at         TIMESTAMPTZ NOT NULL,
    ends_at           TIMESTAMPTZ,
    location          TEXT,
    is_external       BOOLEAN DEFAULT false,
    attendee_ids      UUID[] DEFAULT '{}',
    brief_id          UUID,
    outcome           TEXT,               -- user-reported: well | badly | no_show | rescheduled
    outcome_note      TEXT,
    UNIQUE (user_id, provider_event_id)
);
CREATE INDEX ON meeting (user_id, starts_at);

CREATE TABLE meeting_brief (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    meeting_id        UUID NOT NULL REFERENCES meeting(id) ON DELETE CASCADE,
    who               JSONB, context JSONB, objective TEXT,
    questions         JSONB, risks JSONB, tactics TEXT,
    cited_ids         UUID[] DEFAULT '{}',   -- every claim traces to an interaction
    generated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    model             TEXT, cost_usd NUMERIC(10,5)
);

-- ============================================================ GOALS, SIGNALS, ACTIONS

CREATE TABLE target (               -- "who I'm trying to reach"
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    label             TEXT NOT NULL,
    person_id         UUID REFERENCES person(id) ON DELETE SET NULL,
    company_id        UUID REFERENCES company(id) ON DELETE SET NULL,
    why               TEXT,
    status            TEXT NOT NULL DEFAULT 'open'
                      CHECK (status IN ('open','routing','contacted','met','won','abandoned')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE path (                 -- a computed route, cached with its evidence
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    target_id         UUID NOT NULL REFERENCES target(id) ON DELETE CASCADE,
    hops              UUID[] NOT NULL,    -- ordered person_ids, founder implicit at index -1
    score             REAL NOT NULL,
    confidence        TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
    evidence          JSONB NOT NULL,     -- per-hop: counts, dates, thread ids, inferred flag
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_stale          BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX ON path (user_id, target_id, score DESC);

CREATE TABLE signal (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    kind              TEXT NOT NULL,      -- job_change | cooling | ball_in_court | dormant_return
                                          -- | new_path | thread_stalled | new_participant
    severity          SMALLINT NOT NULL DEFAULT 2,   -- 1 low .. 3 high
    person_id         UUID REFERENCES person(id) ON DELETE CASCADE,
    company_id        UUID REFERENCES company(id) ON DELETE CASCADE,
    thread_id         UUID REFERENCES thread(id) ON DELETE CASCADE,
    headline          TEXT NOT NULL,
    detail            TEXT,
    evidence          JSONB NOT NULL,     -- the rows that produced it. Never empty.
    source            TEXT NOT NULL DEFAULT 'internal',  -- internal | web (V2)
    detected_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at        TIMESTAMPTZ,
    state             TEXT NOT NULL DEFAULT 'new'
                      CHECK (state IN ('new','surfaced','acted','dismissed','expired')),
    dedupe_key        TEXT,
    UNIQUE (user_id, dedupe_key)
);
CREATE INDEX ON signal (user_id, state, severity DESC, detected_at DESC);

CREATE TABLE agent_action (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    conversation_id   UUID,
    tool              TEXT NOT NULL,
    required_level    TEXT NOT NULL,
    payload           JSONB NOT NULL,
    payload_hash      TEXT NOT NULL,
    result            JSONB,
    external_ref      TEXT,               -- gmail message id, calendar event id
    idempotency_key   TEXT UNIQUE,
    state             TEXT NOT NULL DEFAULT 'proposed'
                      CHECK (state IN ('proposed','awaiting_approval','approved','executing',
                                       'succeeded','failed','cancelled','expired')),
    approval_token_hash TEXT,
    approved_at       TIMESTAMPTZ,
    expires_at        TIMESTAMPTZ,
    executed_at       TIMESTAMPTZ,
    error             JSONB,
    -- learning signal
    was_edited        BOOLEAN,
    edit_diff         JSONB,
    cited_ids         UUID[] DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON agent_action (user_id, state, created_at DESC);

CREATE TABLE introduction (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    connector_id      UUID NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    target_id         UUID REFERENCES person(id) ON DELETE SET NULL,
    target_ref        UUID REFERENCES target(id) ON DELETE SET NULL,
    path_id           UUID REFERENCES path(id) ON DELETE SET NULL,
    agent_action_id   UUID REFERENCES agent_action(id) ON DELETE SET NULL,
    direction         TEXT NOT NULL DEFAULT 'requested'
                      CHECK (direction IN ('requested','offered','received')),
    state             TEXT NOT NULL DEFAULT 'asked'
                      CHECK (state IN ('asked','accepted','declined','made','met','converted','dead')),
    asked_at          TIMESTAMPTZ, responded_at TIMESTAMPTZ, made_at TIMESTAMPTZ,
    outcome_note      TEXT,
    outcome_value_cents BIGINT            -- user-entered only
);
CREATE INDEX ON introduction (user_id, connector_id, state);

CREATE TABLE brief (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    brief_date        DATE NOT NULL,
    items             JSONB NOT NULL,     -- [{rank, signal_id, headline, detail, cta}]
    recommended       JSONB,
    sent_at           TIMESTAMPTZ,
    opened_at         TIMESTAMPTZ,
    clicked_count     INT DEFAULT 0,
    suppressed_reason TEXT,               -- set when we deliberately did NOT send
    UNIQUE (user_id, brief_date)
);

CREATE TABLE document (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    title             TEXT, mime TEXT, storage_key TEXT,
    source            TEXT,               -- upload | email_attachment
    person_id         UUID REFERENCES person(id) ON DELETE SET NULL,
    company_id        UUID REFERENCES company(id) ON DELETE SET NULL,
    summary           TEXT, summary_embedding VECTOR(1536),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================ AUDIT (append-only, hash-chained)

CREATE TABLE audit_log (
    id                BIGSERIAL PRIMARY KEY,
    user_id           UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor             TEXT NOT NULL,      -- user | agent | system
    event             TEXT NOT NULL,      -- tool_call | model_call | approval | send | data_access
    subject_type      TEXT, subject_id UUID,
    detail            JSONB NOT NULL,     -- args, entity ids, model, tokens, cost, latency
    ip                INET, user_agent TEXT,
    prev_hash         TEXT,
    row_hash          TEXT NOT NULL
);
CREATE INDEX ON audit_log (user_id, at DESC);
CREATE INDEX ON audit_log (user_id, event, at DESC);

-- ============================================================ ROW LEVEL SECURITY

DO $$
DECLARE t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'user_profile','integration','permission','company','person','person_email',
    'person_affiliation','relationship','thread','interaction','message_chunk','meeting',
    'meeting_brief','target','path','signal','agent_action','introduction','brief',
    'document','audit_log']
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', t);
    EXECUTE format($f$CREATE POLICY tenant_isolation ON %I
                      USING (user_id = current_setting('app.user_id', true)::uuid);$f$, t);
  END LOOP;
END $$;
