# 12 — Why This Fails, and What I'd Actually Do

## Part 1 — The honest risk register

Ranked by probability × severity. I've put the ones people don't want to hear first.

### 1. Your users' real relationships are not in email. **(High probability, fatal)**
This is the one that worries me most, and it is specific to your market. European — especially Greek, Southern European, and generally non-US — founders run their most important relationships on **WhatsApp**. Deals get done in voice notes. Introductions happen in group chats. Email is where invoices and formal documents go.

WhatsApp has no read API. There is no compliant path. If 50% of a founder's strongest ties are invisible to you, your graph is not just incomplete — it is *confidently wrong*, which is worse. The product will show them a route through a colleague they email weekly while missing the friend they message daily.

**Test this in Week 0, before anything else.** In the Concierge Test, ask each founder: "Of your ten most valuable relationships, how many do you primarily email?" If the median answer is below 6, the product needs a different substrate (calendar-first? a manual capture layer? a different geography?) and you need to know that in week 0, not month 4.

### 2. It's a feature, not a company. **(High probability, severe)**
Superhuman, Shortwave, Attio, Granola and Google itself can all ship "who's going cold" and "find a warm path" as a feature. Google in particular already has every byte of the data.

**Why they might not:** Google won't because it's a tiny market with enormous privacy sensitivity inside their most-scrutinized product. Superhuman won't because it requires them to become a CRM. Attio won't because they sell to teams. Granola might — watch them.

**Your only real defence** is outcome memory (§1.7 in [01](01-strategy.md)) and, eventually, the cross-account network. Neither exists in V1. So for the first year you are defended by nothing but speed and focus. Be honest with yourself about that.

### 3. Founders are a terrible B2B market. **(Certain, moderate)**
There aren't many of them. They churn when the company dies (~20%/year baseline mortality). They're distracted, they don't onboard properly, and they're price-sensitive in ways that don't match their spending. Every "tool for founders" company eventually discovers its real market is agencies, funds, or salespeople.

**Plan for it.** Design the schema so the Firm tier is a straight extension, and pay attention if BD people, recruiters, or small funds start asking for access. That's not a distraction — that's the market telling you where the money is.

### 4. One wrong number and the trust is gone. **(Moderate probability, fatal)**
This product's entire value is being right about the user's life. A hallucinated €80K opportunity, an intro path through someone they had a falling-out with, or an email drafted referencing a meeting that never happened — any one of these, once, and they stop believing the true things too.

This is why [§1.4](01-strategy.md) kills auto-valuation and why [§5.6](05-agent-architecture.md) mandates a citation-verification pass. **Precision over recall, everywhere, always.** Show three routes you're sure of, not fifteen you're guessing at.

### 5. The Google verification / CASA timeline. **(High probability, moderate)**
Covered in [09-security.md](09-security.md). 4–12 weeks and €3–15k, recurring annually, and it gates your growth past 100 users. It is survivable *if you start it in week 1*. It is a company-killer if you discover it in month 4 with a waitlist and no way to serve it.

### 6. Retention decay after the novelty. **(Moderate–high, severe)**
The Reveal is a one-time hit. Week 5 is where products like this die: the founder has seen their network, acted on two routes, and now the daily brief starts repeating itself because nothing new happened.

**The counter is the suppression rule** — no news, no brief — plus continuous signal generation from job changes and thread movement. But be realistic: if a founder's world generates two genuine signals a week, you have a weekly product with monthly pricing. Measure week-6 DAU obsessively. If it collapses, the answer is probably *fewer, better* notifications and repositioning around meetings (which recur reliably) rather than signals (which don't).

### 7. Cold-start quality variance. **(Certain, moderate)**
A founder with 10 years of Gmail gets a spectacular Reveal. A founder who switched domains 18 months ago gets a thin one. The second founder churns immediately and tells people it doesn't work.

**Mitigation:** detect thin graphs during ingestion and change the experience — offer mbox import from old accounts, or decline them politely. **Turning away a user you'd disappoint is cheaper than the word of mouth.** This is a real, counterintuitive product decision and it's correct.

### 8. The creepiness threshold. **(Moderate, severe if hit)**
"I scored my relationships with an AI" is one screenshot away from being a bad news cycle. A leaked strength score, an intro request that visibly reveals the founder was coached, or an email containing "confidence: 84%" — any of these is a reputational event in a market where your entire distribution is word of mouth among people who all know each other.

Hard rules: never show a person their own score; never let internal metrics into outbound text (enforced by regex, not by prompt); never let one user query another's contacts; write the copy so the founder always sounds like themselves.

### 9. Prompt injection via inbox. **(Moderate, severe)**
You are feeding attacker-controlled text into a model with send capability. Covered in [09 §9.4](09-security.md). The recipient allow-list is the control that actually saves you; everything else is defence in depth.

### 10. You build the platform instead of the wedge. **(High probability — this is the founder-behaviour risk)**
Your brief describes eight screens, five integrations, a network graph, an opportunity engine, external radar and a permission matrix. It is a beautiful V3. Built as a V1 in four months it will be shallow on every axis and excellent on none, and the demo will feel like a mockup.

**The discipline this whole document is arguing for: build one thing that works impossibly well.**

### 11. The unit economics only work at premium pricing. **(Moderate, moderate)**
~$20 ingestion + ~$16/month COGS means a €49/mo product has thin margins after Stripe and support, and a free tier is a money incinerator. This is fine — it forces the premium positioning you wanted anyway — but it means **you cannot pivot down-market later** without re-architecting the model routing. Know that going in.

### 12. Adverse selection. **(Moderate, mild)**
The founders most excited by "network intelligence" are sometimes the ones with the weakest networks — the ones hoping software will manufacture relationships they don't have. Your best users are well-connected people who are *disorganised*, not poorly-connected people who are hopeful. Screen for it in the invite process; it changes who you should recruit.

---

## Part 2 — Final recommendation: €100k, 4 months

### The budget
```
2 engineers (you + 1 senior), 4 months, EU rates      €64,000
Designer, half-time, 8 weeks                          €10,000
Google CASA assessment + OAuth verification           €8,000
Legal — DPIA, LIA, privacy policy, DPA, TM search      €6,000
Infrastructure + model spend (4 months, ~60 users)     €5,000
Pen test (week 14)                                     €5,000
Buffer                                                 €2,000
                                                     ─────────
                                                      €100,000
```
Note what's absent: no marketing, no sales, no ads, no content. Your first 100 users come from founders showing each other the Reveal. If that doesn't happen, spending money on acquisition would only buy you a faster failure.

### What I would build
Exactly the MUST HAVE list in [03-mvp.md](03-mvp.md), on the 16-week plan in [10-build-plan.md](10-build-plan.md). Concretely, five things:

1. **The graph** — ingestion, identity resolution, strength, tempo, path finding. Six weeks. It is the product.
2. **The Reveal** — onboarding that ends in a verifiable, specific, surprising truth about their own network. Two weeks.
3. **Prepare + approve + send** — one agent loop, executed properly, with real approval mechanics and a real audit log. Two weeks.
4. **The daily brief and meeting brief** — the two habits. Three weeks.
5. **The desktop overlay** — the always-there surface. Two weeks.

### What I would ignore
External web radar. The network graph visualisation. Opportunity valuation. Team features. Mobile. Every integration beyond Google. Documents. The chat interface as a general assistant. Tiered pricing. A marketing site beyond one page. SOC 2. The Private Circle.

All of these are good ideas. **All of them are wrong for the next four months.**

### What I would test first — in this order

**Test 1 (Week 0, €0): Does the graph exist?**
Ten founders, mbox exports, a Python notebook, €500 each. Deliver the network map, the dormant ties, and three routes. Metrics: how many pay; how many find a route they didn't know; how many act within 14 days; and — critically — **how many say their real relationships are on WhatsApp.**
> **Kill if:** <6 pay, or <4 act, or >3 say WhatsApp.

**Test 2 (Week 4): Is the path finder actually right?**
Run it across 5 mailboxes. Have each founder grade the top-3 routes: *correct and useful* / *correct but obvious* / *wrong*.
> **Kill if:** "correct and useful" is under 50%, or "wrong" is over 15%. A path finder that suggests routes through people the founder barely knows is worse than nothing, and no amount of UI polish rescues it.

**Test 3 (Week 8): Will they let it act?**
Of activated partners, how many approve and send a real drafted message in their first week?
> **Warning if:** under 50%. It means the drafts aren't good enough to sound like them, and drafting quality is the gate on the entire execution half of the product.

**Test 4 (Week 12): Does it survive the novelty?**
Week-6 weekday open rate among partners who onboarded in week 6.
> **Warning if:** under 40%. Then stop building features and fix the signal→action ratio in the brief. Retention is not a feature problem.

**Test 5 (Week 16): Will they pay €249?**
Conversion of activated partners.
> **Green light if:** ≥30%. Then raise, hire, and go build the Firm tier.

### The one-sentence version

> Spend week zero proving founders will pay €500 for a hand-made map of their own network; spend twelve weeks making that map automatic and beautiful; spend four weeks making it act; and refuse to build anything else until someone has closed a deal through a route the product found.

### What earns this the right to exist

Not the aesthetic, and not the agent. It's this: **every founder is sitting on a decade of relationships they cannot see, and there is no product that makes them visible and actionable.** If you build only that, and it is right often enough to be trusted, you have something. If you build the eight-screen platform, you have a beautiful demo and a dead company.

Build the map. Everything else is a feature of the map.
