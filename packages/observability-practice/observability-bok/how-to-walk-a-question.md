# How to walk a question through the BOK

**When to use this:** you have an observability question — *"we need better X," "how do we decide Y," "where's the gap in Z"* — and you want to know where the question sits, what it depends on, and where the chain breaks.

This guide walks one real example. Apply the same pattern to your own question.

## Example question

*"We need better signal correlation."*

## Step 1 — Locate the starting point

Find the Knowledge Area (KA) the question most directly addresses.

Correlation is a monitoring and analysis activity, so it sits in [KA04 Monitoring, Visualization & Correlation](ka04-monitoring-visualization.md) — specifically topic *[KA04.3](ka04-monitoring-visualization.md#cross-signal-correlation) Cross-Signal Correlation.*

## Step 2 — Follow the first dependency

Open [KA04](ka04-monitoring-visualization.md) and find its *Connected KAs* section (Section 6 on every KA page). [KA04](ka04-monitoring-visualization.md) lists several dependencies; follow the one your question leans on most directly — for correlation, that is [KA02 Signal Design & Instrumentation](ka02-signal-design.md).

That dependency is structural: you cannot correlate signals that were not designed to relate to each other.

## Step 3 — Follow the next dependency

Open [KA02](ka02-signal-design.md). Its *Connected KAs* section points back to [KA01 Business Context & Service Definition](ka01-business-context.md).

You cannot design signals without knowing which stakeholder expectations the signals are meant to serve. [KA01](ka01-business-context.md) has no further upstream dependency — the walk terminates there.

## Step 4 — Check content state at each stop

Every KA page has a *Content State & Gaps* section (Section 7). For each KA on the walk, note which topics are Current, Seeded, or Missing.

The pattern for this question, read from the actual pages:

- **[KA04.3](ka04-monitoring-visualization.md#cross-signal-correlation) Cross-Signal Correlation** — Seeded (research and patterns exist; no unified methodology — [KA04](ka04-monitoring-visualization.md)'s own audit calls this its primary gap)
- **[KA02.2](ka02-signal-design.md#signal-to-function-mapping) Signal-to-Function Mapping** — Current (semantic binding documented)
- **[KA01.1](ka01-business-context.md#stakeholder-identification-expectations) Stakeholder Identification & Expectations** — Current

## Step 5 — Read the walk

Look at the pattern across the three stops:

> [KA04](ka04-monitoring-visualization.md) wants to correlate → the correlation topic itself is the thin spot → [KA02](ka02-signal-design.md) and [KA01](ka01-business-context.md) beneath it are solid

**Interpretation.** The chain holds underneath — the gap is at the starting topic itself. The foundations correlation needs (designed signals bound to business functions, named stakeholder expectations) are Current; what's missing is the correlation methodology.

**Investment target.** [KA04.3](ka04-monitoring-visualization.md#cross-signal-correlation) — a unified correlation methodology. Build the missing capability on the solid base; don't rework upstream content that the walk just showed you is sound.

## What the walk produced

Four outputs a flat search would not have given:

1. A specific KA as the starting point, not "observability in general"
2. A named dependency chain of three KAs, ordered
3. Content state at each step
4. An investment conclusion not visible from [KA04](ka04-monitoring-visualization.md) alone — the upstream chain is solid, so the gap is genuinely at correlation itself, not a symptom of weak foundations (a flat search could have sent you off to rework signal design first)

## Pattern for your own question

1. **Locate** — find the KA that most directly addresses the question.
2. **Follow** — open the KA page; follow *Connected KAs* upstream (toward Define) until you reach a KA with no further upstream dependency.
3. **Check state** — at each stop, read *Content State & Gaps*.
4. **Read the walk** — look at the pattern. A break is wherever a weaker state sits under load: upstream of a stronger topic, or at your starting topic itself.
5. **Name the investment target** — the break is where additional work produces the most leverage. If the weakness is upstream, fix it before adding capability downstream; if the walk shows solid upstream, invest at your starting topic with confidence.

## When the walk surprises you

If the dependency chain lands somewhere you didn't expect, or the break is at a KA you weren't thinking about, trust the walk. That's the BOK doing its job — it shows dependencies that a direct view of any single KA doesn't.

If the chain doesn't work — you can't find a clean starting KA, or the cross-references point somewhere that doesn't make sense — that's a structural signal. The taxonomy may need iteration. See [Contributing](contribute.md) for how structural feedback flows back.
