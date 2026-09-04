# 01 — Product Strategy

## 1.1 The core problem, stated honestly

Founders do not lack task managers, dashboards, or chat interfaces. They have too many. What they actually lack is a specific, painful thing:

> **They cannot see their own network, and they cannot convert it on demand.**

Every founder has, sitting in their inbox, a graph of 2,000–8,000 real human relationships accumulated over a decade. That graph contains routes into almost every company they want to reach. They cannot access it. They remember maybe 150 people. They forget who introduced them to whom. They let strong ties decay into nothing. When they need to reach the CEO of ACME, they open LinkedIn, see "3rd degree", and send a cold email that fails.

That is the wedge. It is narrow, painful, recurring, and — crucially — **it requires data the founder already owns and has never been able to use.**

Your brief has this in it (Screens 3, 4, and the ACME example) but buries it under seven other pillars. Strategy is subtraction. **The warm-path engine is the company. Everything else is a feature of it.**

## 1.2 What THE OPERATOR actually is

**A relationship graph derived automatically from a founder's email and calendar, made queryable by goal, with an agent that prepares and (on approval) executes the reach-out.**

The product loop you wrote is correct and I'd keep it verbatim:

```
SIGNAL → INTELLIGENCE → RECOMMENDATION → ACTION → OUTCOME → MEMORY
```

but with one hard constraint layered on: **every link in that chain must be evidence-backed and inspectable.** Not "84% fit". Instead: "Maria K. — 214 emails with you since 2019, last exchange 11 days ago, she cc'd ACME's VP Ops on a thread in March 2024, and she has made 3 introductions for you that converted." Every number in the UI must have a "why" behind a click that shows *actual artifacts* — thread subjects, dates, participants.

This is the difference between a product founders trust and a product founders test twice and abandon. The category is not "AI that tells me things." It's **"a system of record for the part of my business I've never had a record of."** LLMs are the extraction and drafting layer. The graph is the product.

## 1.3 The four pillars I would keep, and the four I would cut or defer

| Your pillar | Verdict | Why |
|---|---|---|
| Relationship Intelligence | **KEEP — this is the core** | Only defensible asset. Compounds. Hard to copy without the data. |
| Warm-path routing / Introductions | **KEEP — this is the killer feature** | The one thing nothing else on the market does well for individuals. Directly maps to money. |
| Meeting Brief | **KEEP** | Cheapest possible daily habit loop. High perceived intelligence, low technical risk. |
| Daily Brief | **KEEP but reframe** | Not "news". A daily *state-of-your-network* digest driven by decay and momentum. |
| Opportunity Detection (with € values) | **REFRAME → Deal Threads** | Auto-assigning euro values is a trust bomb. See 1.4. |
| RADAR (external web) | **DEFER to V2, narrow to Network Radar in V1** | Generic monitoring is a commodity and generates noise, which is the one thing that kills a daily-open product. |
| Network Graph visualization | **DEMOTE to a view, not a screen** | Force-directed graphs are beautiful demo objects and useless work objects. Ship it as a *path visualizer* scoped to one query, not a global map. |
| Agentic Execution (send email, book meeting) | **KEEP but scope brutally** | Drafting is easy. *Sending* is where liability, trust and value all concentrate. Ship prepare-first, execute-on-approval, and only for two action types in V1. |

## 1.4 The single biggest change: kill the euro-value hallucination

Your Screen 5 wireframe reads:

```
🔥 €80K — HOTEL GROUP · Fit: 91%
```

An LLM reading an email thread cannot know a deal is worth €80K. It will confabulate. The founder will see €80K, know it's actually €14K, and every other number in your product becomes suspect — including the relationship scores you *can* compute correctly. **One fabricated number poisons the whole surface.**

Replace with **Deal Threads**, which are computed from things that are *actually observable*:

- Thread contains commercial language (quote, proposal, pricing, SOW, contract, invoice) — classifier, not generator.
- Thread has ≥2 participants from an external domain.
- Thread has momentum: N messages in M days, then silence.
- **Ball-in-court detection**: who sent last, and how long ago. This is the highest-value, lowest-risk signal in the entire product and almost nobody does it well.

The card becomes:

```
◆ HOTEL GROUP · Proposal thread
  Stalled 9 days — they replied last, ball is in your court
  4 participants · started 22 Jan · last activity 3 Feb
  Value: [ + add ]                Owner: you
  → Draft the follow-up
```

The founder adds the value. Now your pipeline number (`€284K`) is *their* number, and it is real. You have turned a hallucination risk into a data-entry hook that also gives you the labelled training data to eventually predict value honestly. This is strictly better in every dimension.

**Rule for the whole product: the system may compute, count, rank and date. It may not invent quantities.**

## 1.5 The second biggest change: Radar starts inside, not outside

External radar ("Competitor X entered Greece") has three problems: (a) the data is public and commoditized, (b) relevance filtering is genuinely hard and failures are highly visible, (c) it produces a *feed*, and feeds train users to skim, which is the opposite of the behaviour you want.

**Network Radar** uses only first-party data and produces signals that are unambiguously true and unambiguously about *this* founder:

| Signal | How it's detected | Why it matters |
|---|---|---|
| **Job change** | Person's sending domain changes; signature block delta; new calendar invite domain | The single highest-conversion outreach trigger in existence. This alone justifies the product. |
| **Strong tie going cold** | Time since last contact > 2× the *personal* median interval for that pair | Personalized, not a global 30-day rule. Feels uncanny. |
| **New decision-maker in a live thread** | New participant added to an existing deal thread, seniority inferred from signature | Tells you the deal is escalating (or dying) before anyone says so. |
| **Dormant tie resurfaced** | Someone silent 6+ months emails you | Time-boxed reciprocity window. |
| **Ball in your court, aging** | Last message inbound, no reply, > personal response SLA | Direct revenue leakage. |
| **New path unlocked** | A newly-observed relationship creates a 2-hop route to a target on the founder's watchlist | This is the "holy shit" repeat moment. |

Every one of those is computed with SQL and a small classifier. Zero hallucination surface. Ship external web radar in V2, driven by an explicit watchlist the founder curates, and cap it at **three items per day, ever**. Scarcity is the feature.

## 1.6 What the founder feels

The emotional target you described — private club, Bloomberg terminal, chief of staff — is correct, but the mechanism for producing that feeling is not aesthetics. It's **specificity**. A product feels omniscient when it says something you know is true and didn't expect it to know. It feels cheap the moment it says something generically plausible.

So the design rule is: **prefer one specific, evidence-linked sentence over five confident summaries.**

Bad: *"Maria is a valuable connection in the hospitality sector."*
Good: *"Maria K. is your only 2-hop route into 4 of the 9 hotel groups on your watchlist. You last spoke 11 days ago. She has introduced you to 3 people; 2 became customers."*

## 1.7 Why this can be a company and not a feature

The honest answer is that it can only be a company if the graph compounds into something a competitor can't cold-start. Three compounding assets, in order of durability:

1. **Outcome memory.** You observe which introductions were made, whether they were accepted, and whether they converted. Nobody else sees this. After 12 months you can score path success probability empirically rather than heuristically. That's a real moat and it's the thing to instrument from day one, even before you can use it.
2. **Founder-specific voice + preference model.** Which people they always cc, tone by relationship tier, what they never say. Switching cost.
3. **Cross-user graph, opt-in only.** The "Private Circle" idea in your brief is the true end-game: if 500 founders opt in to expose *the existence* of an edge (not its content), you can route paths across accounts. That's a network effect and it's the only version of this that ends up being worth a billion. **But it is legally and socially delicate and must not be in V1.** Design the schema so it's possible; don't ship it.

## 1.8 The positioning sentence I'd fight for

> **The Operator turns your inbox into a map of who you actually know — and gets you to the person you need.**

Not "AI chief of staff." Not "founder OS." Those are category-less. This one is a promise you can demo in 90 seconds.
