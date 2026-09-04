# THE OPERATOR — Founding Dossier

A complete product, technical and go-to-market plan. Written to be argued with, not admired.

| # | Document | Covers |
|---|---|---|
| 01 | [Product strategy](01-strategy.md) | The strongest version, and what I'd change |
| 02 | [Competitive analysis](02-competition.md) | Who exists, where they're weak, what NOT to build |
| 03 | [MVP scope](03-mvp.md) | Must / Nice / Do-not-build-yet |
| 04 | [User journey + screens + wireframes](04-journey-and-screens.md) | Signup → wow → first outcome, every V1 screen |
| 05 | [Agent architecture](05-agent-architecture.md) | Loop, tools, memory, permissions, graph math |
| 06 | [Data model](06-data-model.md) · [schema.sql](06-schema.sql) | PostgreSQL + pgvector |
| 07 | [Tech + AI model strategy](07-tech-and-models.md) | Stack, routing, unit economics |
| 08 | [API design](08-api.md) | Endpoints |
| 09 | [Security & compliance](09-security.md) | OAuth, CASA, GDPR, agent blast radius |
| 10 | [Build plan + first 10 actions + the wow moment](10-build-plan.md) | Week-by-week |
| 11 | [Positioning + pricing](11-gtm.md) | Naming, messaging, price |
| 12 | [Risks + final recommendation](12-risks-and-verdict.md) | Why this fails; what I'd do with €100k |

---

## TL;DR — the nine things I would change about your concept

1. **The product is not "founder intelligence". It is a warm-path engine with a memory.**
   One sentence has to survive: *"Tell me who you want to reach. I'll tell you the shortest real path and prepare the ask."* Everything else in your brief is a feature of that sentence, or it's cut.

2. **Kill auto-valued opportunity detection in V1.** An AI that tells a founder "€80K opportunity, 91% fit" from reading email is a hallucination factory. The first time it's wrong about money, you lose the account. Replace with **Deal Threads**: detect conversations that *look commercial and have stalled*, let the founder attach the number. Confidence scores describe **staleness and momentum**, never revenue.

3. **RADAR should start inside the founder's own data, not on the open web.** Web monitoring at V1 = a worse Google Alerts with a €249 price tag. The defensible signals are ones only you can see: someone changed employer (visible in their email domain/signature), a dormant strong tie resurfaced, a new decision-maker joined a live thread, a competitor's domain appeared in your customer's inbox thread. External web radar is V2 and capped at a curated watchlist of ≤20 entities.

4. **Widget-first is right; a browser widget is wrong.** For a founder, "always available" means a **global hotkey overlay** (Raycast/Spotlight shape), which means a desktop shell (Tauri). Ship the web app first, ship the desktop overlay by week 12, and treat the overlay as the retention product.

5. **The wow moment must be built from the past, not the future.** Day 1 you have zero forward signal but five years of their inbox. The wow is the **Network Reveal + Dormant Value Report**, computed in the 90 seconds after Gmail OAuth. Detail in [10-build-plan.md](10-build-plan.md).

6. **`gmail.readonly` is a Google *restricted* scope.** That means CASA Tier 2 assessment, a security questionnaire, and 4–12 weeks of latency, before you can exceed 100 users. This is the single most underestimated line item in your plan and it must start in Week 1. See [09-security.md](09-security.md).

7. **Your target market may not live in email.** Greek/EU founders run their real relationships on WhatsApp. WhatsApp has no read API. If half your users' strongest ties are invisible to you, the graph is a lie and the product dies quietly. **This must be the first thing you test, before writing product code.**

8. **"Operator" is taken.** OpenAI shipped a product called Operator. Do not fight that for search or mindshare. Recommendation: name the *product* something ownable, name the *agent* "the Operator." See [11-gtm.md](11-gtm.md).

9. **Don't build until you've run the Concierge Test.** Ten founders, manual graph analysis, €500 each, one week. If six pay and four act on a route within fourteen days, build. If not, you've saved €100k. See [12-risks-and-verdict.md](12-risks-and-verdict.md).
