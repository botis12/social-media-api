# 11 — Positioning, Naming & Pricing

## 11.1 One-line description

> **The Operator reads your inbox and shows you the shortest real path to anyone you need to reach.**

Concrete, demoable, no category jargon, and it survives being repeated by a founder to another founder over coffee — which is the only distribution channel that matters for your first 100 users.

## 11.2 Homepage

**Headline:**
> ## You know 3,000 people. You can remember 150.

**Subheadline:**
> The Operator turns your email into a map of who you actually know — then finds the route to the person you need, and writes the ask.

**Below the fold, one screenshot: the Reveal.** No feature grid, no logo wall you don't have, no "powered by AI" badge. One CTA: `REQUEST AN INVITE`.

Why this headline: it states a fact the reader instantly recognises as true about themselves, and it creates the gap that the product closes. It contains no AI vocabulary, which in 2026 is a differentiator by itself.

## 11.3 Five positioning options

| # | Position | Line | Pros | Cons |
|---|---|---|---|---|
| 1 | **The warm-path engine** ⭐ | "The shortest path to anyone you need." | Sharpest. Demoable in 90s. Directly tied to revenue. Nobody owns it. | Might read as narrow to investors. It isn't — it's a wedge. |
| 2 | **Relationship intelligence for founders** | "Affinity, for you — not your firm." | Proven category; the buyer already understands it. | Fights a well-funded incumbent's language. Sounds like a CRM. |
| 3 | **The chief of staff** | "Your first hire, at 1/40th the cost." | Emotionally resonant. Premium framing. | Crowded, vague, and every AI assistant claims it. Sets an expectation you cannot meet in V1. |
| 4 | **The founder's terminal** | "Bloomberg for your business." | Matches the aesthetic. Justifies premium pricing. | Implies market data you don't have. Aesthetic promise without substance is fatal here. |
| 5 | **Your network, finally usable** | "Ten years of contacts. Zero of them searchable." | Broad, immediately legible. | Sounds like a personal CRM — the exact trap in [02](02-competition.md). |

**Recommendation: #1, with #3 as the emotional register in the copy.** Lead with the specific capability, let the feeling do the atmosphere. "The shortest path to anyone you need" is what you sell; "chief of staff" is how it feels.

## 11.4 The name

**Problem with THE OPERATOR:** OpenAI shipped a product called Operator. You will lose that search term permanently, and every investor conversation will start with "isn't that OpenAI's thing?" The word is also over-indexed in the AI-agent space generally.

**But "Operator" is a great name for the *agent*.** So: give the product an ownable name, and call the agent the Operator inside it. *"Ask the Operator."* You keep the language you love and the trademark you need.

Ten candidates:

| Name | Read | Notes |
|---|---|---|
| **MERIDIAN** ⭐ | Navigation, position-fixing, the line you're on | Premium, calm, non-AI, ownable. `meridian.so`. My first choice. |
| **PROXIMA** | Nearest — literally "the closest one" | Direct semantic match to warm paths. Slight astronomy cliché. |
| **KEEL** | The thing that keeps you upright and pointed | Short, strong, unusual, memorable. Very brandable. |
| **THE DESK** | A trading desk; a chief of staff's desk | Understated, institutional, no AI smell. Weak SEO. |
| **CONSIGLIERE** | The trusted advisor who knows everyone | Enormous personality. Mafia connotation is a real risk for enterprise. |
| **VANTAGE** | A position from which you can see | Clean; somewhat used in finance. |
| **WARM** | Warm introductions, warm network | Beautifully simple, instantly explains the product. Hard to trademark; generic. |
| **ORBIT** | Who is in your orbit | Friendly, memorable. Used by a few small SaaS products. |
| **ARDEN** | Neutral, human, premium (a name, not a word) | Zero baggage, ages well, easy to trademark. |
| **SIXTH** | Six degrees of separation | Clever, short, mnemonic. Slightly cute. |

**Recommendation: MERIDIAN, with the agent named the Operator.** "Open Meridian. Ask the Operator to find a route into ACME." That reads like a real product from a real company.

Do a trademark search in EUIPO class 9/42 before you commit to anything. Budget half a day.

## 11.5 Pricing

### The reasoning
Your instinct toward tiers is premature. At V1 you do not know what people pay for, and every tier you ship is a decision you have to unwind later. **Ship one price.** Tiering is a month-9 optimization.

**Do not offer a free tier.** Three reasons, all decisive: (a) your COGS is ~$20 one-time + ~$16/user/month ([07 §2.4](07-tech-and-models.md)) — free users cost real money before they show any intent; (b) the positioning is exclusive, and free destroys that instantly; (c) the value is legible in six minutes, so a free tier buys you nothing a trial doesn't.

The value anchor is not "software." It is: **one warm introduction that turns into a customer.** For a founder that's €10k–€200k. At €249/mo you're asking for ~€3k/year against an asset worth multiples of that on a single hit. That's an easy conversation. At €49/mo you'd be *less* believable, not more — a product claiming to run your network for the price of a Netflix bundle isn't credible.

### V1 pricing — ship exactly this

| | **THE OPERATOR** |
|---|---|
| **€249 / month**, or **€2,490 / year** (2 months free) | |
| Everything. Full graph, unlimited paths, daily brief, meeting briefs, agent execution, desktop overlay. | |
| **14-day trial. No card required to start; card required to connect Gmail.** | |

That card-at-Gmail-connect mechanic is deliberate: it filters tyre-kickers at the exact moment intent is highest, and it protects you from paying ingestion COGS for people who were never going to buy.

### Month 9+, once you have data

| Tier | Price | Who | What's gated |
|---|---|---|---|
| **Operator** | €249/mo | Solo founder | The V1 product |
| **Executive** | €599/mo | Founder with real deal volume | External radar, unlimited execution, priority ingestion, custom signal rules, phone support |
| **Firm** | €449/seat/mo, min 3 | Small funds, agencies, BD teams | Shared graph across seats, "who at our firm knows X" — this is where the real money is, and it's a straight shot at Affinity's mid-market |
| **Circle** | invite / equity | The network product | Cross-account routing, opt-in. Post-PMF only. |

**The Firm tier is where the business becomes large.** A three-person fund at €449/seat is €16k/year, and that buyer has a budget line for exactly this. But you cannot start there: the multi-user permission model is a different product, and you must earn the single-player experience first.

### What I would not do
- No usage-based pricing (unpredictable bills kill trust in a product that acts on your behalf).
- No per-action or per-introduction pricing (it makes founders ration the core loop — catastrophic for retention).
- No lifetime deals, ever.
- No annual-only. Founders want out-clauses; give them one and they'll stay anyway.
