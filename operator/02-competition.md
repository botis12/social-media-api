# 02 — Competitive Analysis

The market is split into two camps, and neither one holds the position you want.

```
                 GRAPH / RELATIONSHIP DEPTH
                            ▲
        Affinity ●          │
        4Degrees ●          │        ◆ THE OPERATOR
        Clay.earth ●        │          (the empty quadrant)
        Dex ●               │
                            │
        Attio ●             │
   ─────────────────────────┼──────────────────────────►
        Folk ●              │      Lindy ●   AGENCY /
        HubSpot ●           │      Zapier Agents ●  EXECUTION
                            │      ChatGPT/Claude agents ●
                            │      Martin ●
                            │      Superhuman AI ●
```

**Camp A — the graph without agency.** They know who you know. They do nothing with it.
**Camp B — the agency without the graph.** They can act. They have no idea who you are or who matters.

The empty quadrant is real. It's also empty for a reason: doing both requires deep OAuth access *and* earning permission to act on someone's behalf, which is a hard trust ladder to climb. That difficulty is your moat, if you survive it.

---

## 2.1 The closest existing products

### Affinity — *the most important company to study*
Relationship intelligence for VC and PE firms. Ingests the whole firm's email + calendar, computes relationship strength scores, surfaces who at the firm knows whom, auto-builds deal records.

- **Strong:** The graph math is proven at scale. "Who at our firm can intro us to X" is a solved product inside Affinity. Deep enterprise trust, 10+ years of data.
- **Weak:** Firm-oriented, not individual. Enterprise pricing (five figures/yr, seat minimums). The UX is a deal-flow CRM — tables, pipelines, fields. Zero agentic execution; it tells you the path, you do all the work. Not sold to, priced for, or shaped for founders.
- **How you avoid being a clone:** Affinity answers *"who at my firm knows this person"*. You answer *"what is my next move, and shall I make it for you."* They optimize for pipeline hygiene; you optimize for a single reach-out. Never build their pipeline table.

### Clay (clay.earth) — *the closest consumer analog*
Personal CRM that ingests email, calendar, and social; enriches contacts; nudges you to keep in touch.

- **Strong:** Beautiful. Effortless setup. Best-in-class "here's a person, here's their context" card. Cheap (~$20/mo).
- **Weak:** Fundamentally passive — a prettier Rolodex with reminders. No goal-directed routing ("get me to ACME" isn't a query it answers). No execution. No commercial context. Its own users describe the loop as "nice, but I forget to open it."
- **How you avoid being a clone:** Clay is organised around *people*. You are organised around *goals*. Their home screen is a list of contacts; yours is a list of moves. Do not build a contact list as your primary surface.

### Dex, Folk, Attio, 4Degrees
Personal/team CRMs with email-derived enrichment. Attio is the best-built modern CRM; Folk is the lightweight team version; 4Degrees is Affinity-lite for smaller funds.
- **Strong:** Data model flexibility, integrations, polish.
- **Weak:** All of them are **databases you maintain**. The unit of work is a record. Retention depends on discipline the founder does not have.
- **Avoid:** Custom fields, pipeline kanbans, list views, "add a contact" as a primary action. The moment you ship a records table you become an inferior Attio.

### Superhuman (+ AI) / Shortwave
Inbox-native AI. Shortwave in particular does strong semantic search over your whole mail history.
- **Strong:** Daily-use surface. Speed as a religion. Already has the OAuth grant you want.
- **Weak:** Everything is bounded by the inbox. "Who should I talk to this quarter" is not an email question. No relationship model, no goals, no outcomes.
- **Threat level: high.** Superhuman shipping "who's going cold" is a two-sprint feature. Your defence is that the *routing + outcome memory* layer is a different product, not a mail client feature — and that you're not asking anyone to switch mail clients.

### Granola / Circleback / Fireflies
Meeting memory. Granola is the one to watch: excellent product, strong founder adoption, and it is drifting from "notes" toward "people and context."
- **Strong:** Owns the highest-signal moment (the actual conversation). Loved.
- **Weak:** No pre-meeting intelligence worth the name, no network graph, no outreach.
- **Play:** Do **not** build transcription. Integrate later (V2), or let founders paste notes. Granola is a partner and an acquirer, not a target.

### UserGems / Champify / Common Room / Unify
GTM signal tools. UserGems is directly relevant: it tracks job changes of your existing contacts and alerts sales teams. That is *exactly* your highest-value radar signal.
- **Strong:** Proven that job-change alerts drive real pipeline. Enterprise contracts.
- **Weak:** Sold to revenue teams, priced per seat at enterprise level, requires a CRM as the substrate. Useless to a solo founder with no CRM.
- **Read:** Your job-change signal is validated by their existence. Your differentiation is that you don't require a CRM — you *are* the record.

### Lindy / Relay.app / Zapier Agents / n8n
Agent builders.
- **Strong:** Real execution across many tools. Flexible.
- **Weak:** They are IDEs. The user must decide what the automation should be. Zero context about the business. Configuration burden is the product's own worst enemy.
- **Avoid:** Never ship a workflow builder. The whole promise is that you already know what to do.

### ChatGPT / Claude with connectors, "Operator", Deep Research
The default competitor for every AI product.
- **Strong:** Free-ish, ubiquitous, improving fast, now with Gmail/Calendar connectors.
- **Weak:** Stateless across sessions in the way that matters. No persistent graph, no strength scoring, no continuous background computation, no outcome tracking. It answers questions; it doesn't watch.
- **This is your real benchmark.** The test for every feature you build: *"could a founder get 80% of this by pasting into Claude?"* If yes, cut it. Summarizing a document — yes, cut. Computing that Maria is your only 2-hop route into 4 of 9 watchlist companies — no, impossible. Build only what fails that test.

### Martin, Ohai, Cove and the "AI chief of staff" cohort
- **Strong:** Good positioning instincts, consumer polish.
- **Weak:** Mostly scheduling and reminders wearing a trench coat. Shallow. High churn. They have the aesthetic you want and none of the substance.
- **Lesson:** Aesthetic-led AI assistants churn hard at month 2 because the intelligence is thin. Yours must be *computed*, not *prompted*.

---

## 2.2 Where everyone is weak (your opening)

1. **Nobody makes the graph goal-addressable.** All of them let you browse people. None answer "get me to X."
2. **Nobody closes the loop on outcomes.** No product records that intro #47 happened, was accepted, and turned into a customer. So none of them ever get smarter about routing.
3. **Nobody uses per-relationship tempo.** Everyone ships a global "you haven't talked in 30 days" rule, which is noise for the 400 people you talk to yearly and useless for the 5 you talk to weekly.
4. **Nobody prepares the artifact.** The gap between "you should reach out to Maria" and a written, contextual, in-your-voice message is where 90% of intent dies.
5. **Ball-in-court is unsolved.** Every founder is leaking deals to threads where they owe a reply. It's trivially computable and nobody surfaces it well.

## 2.3 Features we should explicitly NOT build

| Do not build | Why |
|---|---|
| A pipeline/kanban CRM | You become a worse Attio, and you inherit the maintenance burden that kills CRMs. |
| A workflow/automation builder | Configuration is the enemy of the promise. |
| Meeting transcription | Solved, commoditized, expensive, and Granola will beat you. |
| A general chat assistant | You cannot out-ChatGPT ChatGPT. Chat is a command surface for *your* tools, not a general interface. |
| A mobile app in V1 | Founders act on this at a desk. Ship push notifications via web/desktop instead. |
| LinkedIn scraping / a LinkedIn extension | ToS violation, account bans for your users, and a permanent acquisition/diligence liability. Non-negotiable. |
| Slack, Notion, HubSpot, Stripe integrations | Each one adds surface and none add graph quality in V1. |
| A global force-directed network graph | It demos well and gets used twice. Ship a *path* visualizer instead. |
| Auto-sending anything without approval | One bad autonomous email ends the company's reputation among the 400 founders who matter. |
| Team/multi-seat features | Solve for one founder perfectly first. Multi-user changes the permission model completely. |
| Predicted deal values / revenue forecasting | See [01-strategy.md §1.4](01-strategy.md). Trust bomb. |
| Gamification, streaks, scores shown to third parties | Kills the premium positioning instantly, and a leaked "relationship score" is a social disaster. |

## 2.4 The one-line competitive stance

> Affinity for the person, not the firm — with hands.
