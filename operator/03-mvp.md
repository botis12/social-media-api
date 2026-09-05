# 03 — The Exact V1

**Definition of V1:** the smallest system that can make a founder say *"it found a route I didn't know I had"* within 10 minutes of signup, and keep earning one open per weekday for 60 days.

**Constraint:** 4 months, ~€100k, ≤100 design partners (which is also the Google unverified-app ceiling — see [09-security.md](09-security.md)).

---

## MUST HAVE (this is the whole build)

### A. Ingestion & graph (the engine — ~40% of engineering)
1. **Google OAuth** for login + Gmail read + Calendar read + Contacts read.
2. **Historical backfill**: 24 months of mail headers + threads, 24 months of calendar. Incremental sync thereafter via Gmail History API + Calendar sync tokens.
3. **Identity resolution**: emails → Person entities (alias merging, domain → Company, dedupe by name+domain, name normalisation).
4. **Noise filter**: strip newsletters, no-reply, transactional, bulk (List-Unsubscribe header, sender entropy, reply-ratio). This must be aggressive — graph precision matters more than recall.
5. **Relationship strength scoring** + **per-pair tempo model** (see [05-agent-architecture.md §5.7](05-agent-architecture.md)).
6. **Path finding**: ≤2 hops, ranked, with evidence.
7. **pgvector index** over thread summaries and person profiles.

### B. The five surfaces
8. **TODAY** — 3 moves max, plus the compact state-of-network strip.
9. **OPERATOR** — chat + tools, with the path-routing flow as the hero.
10. **PEOPLE** — person detail page (relationship intelligence, not a contact card). List view is secondary and search-first.
11. **PATHS / target watchlist** — "companies & people I'm trying to reach" + live routes into them. *This is the screen that replaces your Network graph in V1.*
12. **MEETING BRIEF** — auto-generated 30 min before any external calendar event.

### C. Agent (narrow)
13. **Tool set (11 tools)**: search_people, get_person, find_paths, search_threads, get_thread, get_calendar, find_availability, draft_email, draft_intro_request, create_reminder, add_to_watchlist.
14. **Permission model**: READ / SUGGEST / PREPARE / EXECUTE, default PREPARE for everything that touches the outside world.
15. **Two executable actions only**: `send_email` (after explicit approval, from the founder's own Gmail) and `create_calendar_event` (after approval). Nothing else executes in V1.
16. **Audit log** of every tool call, every approval, every send — user-visible.

### D. Retention loop
17. **Daily Brief** at a user-set hour, delivered as email + in-app. Max 5 items, at least one of which must be *new information* (a job change, a new path, a newly stalled thread) or the brief is not sent at all.
18. **Ball-in-court + going-cold detection** feeding TODAY and the brief.
19. **Job-change detection** (domain/signature delta).

### E. Non-negotiable plumbing
20. Encrypted token storage (envelope encryption, KMS).
21. Per-user data deletion that actually deletes, in < 24h.
22. Sentry + PostHog + a structured event log for the activation funnel.
23. An **eval harness** with a golden set for the extraction and drafting prompts, from week 3 onward.

---

## NICE TO HAVE (build only if a must-have lands early)

- Floating **desktop overlay** (Tauri, global hotkey). Very high value for retention; medium risk. Target week 12–14 — I'd cut a nice-to-have elsewhere to protect this one.
- **Deal Threads** view (commercial thread classifier + user-entered value + stall detection). Strong candidate for promotion to MUST if the Concierge Test shows founders care more about deals than intros.
- Post-meeting **follow-up draft** prompt.
- Voice/tone learning from the founder's own sent mail (few-shot from their last 50 sent messages — cheap, high perceived magic).
- Path visualiser (a small, single-query graph render, not a global map).
- Slack notification of the daily brief.
- Document upload + summarize.

## DO NOT BUILD YET (V2+, and say no confidently)

| Deferred | Revisit when |
|---|---|
| External web RADAR | You have 50 retained users and a curated watchlist per user |
| Global network graph visualisation | Never, unless users ask twice |
| Cross-user "Private Circle" network | Post-PMF, with a lawyer and an explicit consent flow |
| Team / multi-seat / shared intelligence | 100 paying single users first |
| Opportunity auto-valuation | You have ≥500 user-labelled deal values to train on |
| Mobile app | Web push covers V1 |
| Non-Google mail (Outlook/M365) | You'll need it for EU corporate; it's a 3-week add, do it in month 6 |
| WhatsApp / Signal / Telegram | No compliant API path exists. Test the *impact* of its absence in the Concierge Test instead |
| CRM / Slack / Notion / LinkedIn integrations | Only if a design partner blocks renewal on it |
| Autonomous (unapproved) sending | Only after ≥1,000 approved sends with a <2% edit rate |
| Documents/proposal comparison | It's a ChatGPT feature; it fails the §2.3 test |

---

## The V1 success criteria (write these on a wall)

| Metric | Target | Why this one |
|---|---|---|
| OAuth → first path shown | **< 6 minutes** | If the wow is slow, there is no wow |
| Design partners who find ≥1 *unknown* route in week 1 | **≥ 70%** | This validates the core thesis |
| Weekday open rate, week 4 | **≥ 55%** | Habit formed or not |
| Approved agent actions / user / week | **≥ 3** | Are they letting it act |
| Brief → click-through | **≥ 40%** | Is the brief signal or noise |
| Paid conversion after 14-day trial | **≥ 30% of activated** | Willingness to pay for intelligence |
| **Reported outcomes** (intro made / meeting booked / deal advanced) | **≥ 1 per user per month** | The only metric that makes this a company |

If the last one is zero after 8 weeks with real users, the thesis is wrong and no amount of UI will save it.
