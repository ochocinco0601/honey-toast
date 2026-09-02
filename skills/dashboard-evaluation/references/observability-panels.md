# Instance: Observability Panels

> This is the **observability instantiation** of the engine in `../SKILL.md`. Read `../SKILL.md` first — the chain, the design method, the two faces,
> and the acceptance gates are defined there and are not repeated. This file
> supplies what's specific to observability: the domain vocabulary for each chain
> position, the sequenced triage chain, the production machinery to build a panel
> at scale, and the resolved multi-workflow layout opinions.

---

## 1. The observability narrowing

For observability surfaces, the general chain takes a fixed shape — five
positions. Every panel projects some subset of these:

| # | Position | The question it answers | Example (SRE) | Example (business) |
|---|----------|------------------------|---------------|--------------------|
| 1 | **Who cares** | Who has the responsibility? | On-call SRE | VP of Origination |
| 2 | **Why they care** | What responsibility creates the need? | Keep checkout API available | Loans processed within SLA |
| 3 | **What they expect** | What's the target/threshold? | p99 < 200ms, errors < 0.1% | Completion within window |
| 4 | **How it's measured** | What metric resolves the uncertainty? | Latency percentiles, 5xx rate | On-time completion rate |
| 5 | **What it's about** | The thing observed, at what altitude? | Checkout API (application) | Origination process (business) |

The "someone" is **anyone with a responsibility that creates an expectation about
something measurable.**

### The observability diagnostic (the engine's general diagnostic, in this skin)

| # | Position | Ask | Healthy | Common failure |
|---|----------|-----|---------|----------------|
| 1 | Who cares | Stakeholders named? | Named with role context | Implied by the title, or absent |
| 2 | Why they care | Drivers/expectations stated? | Explicit expectation per stakeholder | "Everyone knows why uptime matters" |
| 3 | What they expect | Targets defined? | Numeric threshold with owner | Traffic light with invisible threshold |
| 4 | How it's measured | Current state shown *against* target? | value + target + delta + status | Raw number, no context (is 409 bad?) |
| 5 | What it's about | Altitude clear? | Named layer + appropriate framework | Business labels on infrastructure data |

**Bonus — impact chain.** When health degrades, does the surface show what happens
next (customers affected, revenue at risk, compliance exposure, operational
backlog)? Absence here is the *"system healthy but business failing"* blind spot —
the most expensive gap.

---

## 1b. Occasions — which question set applies

**Name the occasion before you use any question set.** The same subject generates
different questions depending on *when and why* someone is asking. A surface built
for one occasion and read on another fails without any individual panel being
wrong — and that mismatch is the most common structural finding on a real
dashboard.

Nine occasions, each with its own governing prior art and its own recurring
question:

| # | Occasion | Governing prior art | The recurring question |
|---|----------|--------------------|------------------------|
| 1 | **Incident triage** | ITIL 4 Incident Management; Google SRE incident response; OODA | "Something is wrong — what do I do?" |
| 2 | **Routine monitoring / readiness** | Google SRE *Monitoring Distributed Systems* (symptom-based, golden signals); ITIL 4 Monitor & Event Management | "Is everything healthy right now — are we ready for the day?" |
| 3 | **Change validation** | DORA (change failure rate, time to restore); SRE release engineering and canary analysis | "Did this change degrade anything?" |
| 4 | **Capacity planning** | Google SRE capacity planning and demand forecasting | "Will we have enough? When do we run out?" |
| 5 | **Compliance & audit** | COSO ERM; OpenSLO / SLODLC conformance; regulatory obligation | "Can we prove we met our obligations, and what is the exposure?" |
| 6 | **Trend analysis** | SRE error-budget burn; DORA trend; Tufte small multiples | "Are we getting better or worse?" |
| 7 | **Coverage & maturity** | CNCF Observability Maturity Model; DORA capability self-assessment | "What is unmonitored, and how mature is our observability?" |
| 8 | **Cost & efficiency** | FinOps Framework unit economics; SRE efficiency and utilization | "What does this cost, and is resource use efficient?" |
| 9 | **Toil & operational burden** | Google SRE *Eliminating Toil*; ISA-18.2 / IEC 62682 alarm rate and alarm flood | "How much manual burden and alert noise does this generate?" |

Each occasion crosses the three altitudes (§3.2), so a question set is an
occasion **and** an altitude — "readiness at the business altitude" asks something
different from "readiness at the technology altitude."

**Honest confidence split.** Occasion 1 is the one worked in depth: its seven-step
chain (§2) is validated across 21 worked examples spanning 8 domains and all three
altitudes. **Occasions 2–9 are derived from the named prior art above and have not
been walked.** Their governing questions are sound; their step-by-step
decompositions are not established the way §2's is. Say which you are using, and
do not present a derived question set as a proven one.

**Two consequences for a diagnostic run.**

1. **Choose the coverage question set from the occasion, not by habit.** Running
   §2's triage chain against a readiness surface will report gaps that are not
   gaps — the surface was never answering those questions. Judging a dashboard by
   the wrong occasion's ruler is a defect in the *review*, not the dashboard.
2. **A surface serving several occasions at once is a finding.** Name the
   occasions and expect the recommendation to be a split, rather than more panels.

---

## 2. The diagnostic chain, in observability wording

This section instantiates the general **diagnostic chain** (see `../SKILL.md`) for
observability — it is the incident triage flow (ITIL 4 Incident Management). Each
step is the same need→uncertainty→decision from the general pattern; only the
wording is observability-specific. A dashboard panel is **one** way to answer a step
— an alert, a query, a runbook, or a dependency map are others. The rest of this
file is what to do when the answer-surface *is* a panel.

| Step (general move) | Observability question | Decision it unlocks |
|---------------------|------------------------|---------------------|
| Detect | **Is it healthy?** | act or move on |
| Localize | **What specifically?** | narrow focus |
| Assess | **What's the business impact?** | urgency |
| Diagnose | **Why is it red?** | remedy / root cause |
| Scope | **What else is affected?** | blast radius |
| Assign | **Who do I call?** | escalate / ownership |
| Remediate | **What's the fix?** | resolve (runbook) |

The consumer does **not** need to know the machinery behind the answer. They need it
to carry enough context to decide and move to the next step.

---

## 3. Production machinery

How a walked chain becomes a *buildable* panel spec, every field traceable to a
named standard. Use it when you move from "what should this show" to "what exactly
do I render, from what data."

**Governing standards (name them — they carry the rules):** ISO/IEC/IEEE 42010
(viewpoints/concerns), ArchiMate 3.2 (the element graph), OpenSLO
(targets/thresholds), ITIL 4 (the triage flow), APQC / Google Golden Signals / USE
(health dimensions by altitude), Nagios (worst-child health propagation), COSO ERM
(exhaustive impact categories), Tufte / Few / Norman (rendering).

### 3.1 The traversal architecture

Every panel's data is a traversal through a fixed graph of ArchiMate elements.
Positions 1–4 are the **motivation core** — *altitude-independent,* identical at
every level. Positions 5–6 are the **subject extension** —
*altitude-parameterized.* Positions 7–9 are optional branches.

```
Motivation core  (altitude-INDEPENDENT — proven across all altitudes):

  [1] Stakeholder ──Association──▶ [2] Driver ──Realization──▶
  [3] Requirement ──Realization──▶ [4] Outcome ──Influence(±)──▶

Subject extension  (altitude-PARAMETERIZED — type binding per altitude):

  [5] Subject ──Access/Serving──▶ [6] Object

Optional branches:

  [5] ──Assignment──▶ [7] BusinessRole ──Assignment──▶ [8] BusinessActor   (ownership / "who do I call")
  [3] ──Association──▶ [9] Runbook (BusinessObject)                         (the fix)
```

Mapping to §1: position 1 = *who cares*, 2 = *why*, 3 = *what they expect* (carries
the target), 4 = *the measured outcome*, 5–6 = *what it's about.*

### 3.2 Altitude bindings

Only positions 5–6 change by altitude. Three bindings, all proven:

| Altitude | Position 5 (Subject) | Position 6 (Object) | Relationship 5→6 |
|----------|----------------------|---------------------|------------------|
| **Business** | `archimate:BusinessProcess` | `archimate:BusinessObject` | `archimate:Access` |
| **Application** | `archimate:ApplicationService` | `archimate:BusinessProcess` | `archimate:Serving` |
| **Technology** | `archimate:TechnologyService` | `archimate:ApplicationService` | `archimate:Serving` |

### 3.3 Health dimensions by altitude

What "healthy" *means* depends on altitude — use the altitude-appropriate
framework:

| Altitude | Health framework | Dimensions |
|----------|------------------|------------|
| **Business** | APQC Process Performance | Effectiveness, Efficiency, Adaptability |
| **Application** | Google Golden Signals | Latency, Errors, Traffic, Saturation |
| **Technology** | USE Method | Utilization, Saturation, Errors |

### 3.4 Projection rules — one traversal, many panels

The same data chain answers many questions by varying **which positions project
onto the panel.** "Is it healthy?" projects measurement + target. "What's the
business impact?" projects stakeholder + consequence. *Same data, different
display.* Define the traversal once, add questions cheaply via new projections.
Seven proven patterns:

1. **One-to-one, single altitude** — one subject, one panel.
2. **One-to-many fan-out** — one parent projects to many children.
3. **Aggregation (worst-child)** — children roll up to one tile via Nagios
   worst-case propagation.
4. **Same-altitude decomposition** — parent → children via ArchiMate Composition
   (full context for degraded children, name-only for healthy).
5. **Cross-altitude composition** — application → business via Serving; no new
   element types.
6. **Vendor-boundary projection** — traversal crosses an org/vendor boundary.
7. **Comparison / small multiples** — cohort comparison across peer subjects.

### 3.5 Coloring a tile

Use the **two-threshold pattern** (Nagios): a warning threshold and a critical
threshold, both explicit, both from OpenSLO. Never render a traffic light whose
thresholds are invisible (fails diagnostic position 3).

### 3.6 The grounding rule (non-negotiable)

**Every field on a panel must trace to named prior art, or be explicitly marked as
a gap.** Use element types and field names from published specs, in their real
namespaces (`archimate:name`, `openslo:target`, `dcterms:source`). When a concept
is needed but no framework is identified, label it `prior-art-unresolved` with a
pointer — do not silently invent. **Tie-breaker** when multiple standards apply:
(1) a framework already adopted in the practice or estate you are working in
→ (2) native domain framework →
(3) simplicity → (4) wide adoption.

---

## 4. Formed design opinions — multi-workflow business apps

These are layout opinions **already resolved against real cases.** They are the
current "what good looks like" for the case these were worked against:
**real business applications that contain multiple workflows.** Treat them as
defaults. *Status:* Proven = held up in worked cases; Reasoned = argued from the model,
not yet tested in a build; Hypothesis = plausible, untested. Don't present a
Hypothesis as settled fact.

### The governing case

A real business application is rarely one process. A lending app spans
origination → underwriting → closing → servicing; an originations flow is itself
6+ sequential steps. The naive reader's job is *"is the business healthy, and if
not, where?"* **A single rolled-up health tile destroys that** — it says
"something's wrong" but not "where, in which flow, with what downstream effect." So:

> **Lay the surface out as workflows, and within each workflow as ordered steps.
> Carry health per-workflow and per-step — not one aggregate tile. The naive
> reader needs the structure *visible upfront*, not hidden behind a roll-up they
> must drill to reconstruct.**

### The opinions

| # | Opinion | Layout implication | Status |
|---|---------|--------------------|--------|
| 1 | **Sequential steps, not parallel peers.** A step-3 failure *blocks* steps 4–6. | Left-to-right pipeline; give a gated step a distinct **BLOCKED** state vs **DEGRADED** (own failure) vs **HEALTHY**. | Proven |
| 2 | **A step's health rule is a business decision, not a roll-up.** One step may depend on several services with *different* criticality (fraud down = blocking; credit-risk down = degraded-but-proceed). | Each step owns an explicit composition rule (blocking / degradable / optional), authored once by the process owner, applied mechanically. Don't worst-case everything to red. | Reasoned |
| 3 | **Structure visible upfront for naive readers.** | First view shows *all* steps (the pipeline), not "1 CRITICAL · 2 WARNING" cards that hide the flow. | Proven |
| 4 | **Journey is per-workflow, owned, its own view.** Each workflow has a name, a business question, an owner, ordered steps. | Each workflow gets its own view/section — never all workflows compressed into one generic "journey." | Reasoned |
| 5 | **Journey is a *perspective on* a service, not a replacement.** Service home answers "is this service healthy?"; journey view answers "where in the flow is the problem?" | Service home is the hub (health + context, always on); the flow view is reachable *from* it, for process-shaped services. | Reasoned |
| 6 | **Heterogeneous steps stay coherent when self-contained.** Steps measure different things (success rate vs timeliness vs coverage). | Don't fuse into one score. Each step is a self-contained micro-panel with its own labeled measurement; the step's outcome label is load-bearing. | Proven |
| 7 | **Enumerate up to ~7, aggregate above.** (Few's data density + Miller's 7±2.) | ≤7 items: show all equally. >7: headline aggregation + grouped/collapsible detail. | Proven |
| 8 | **Signal → stakeholder → impact must be visually direct.** "This signal is critical" is half the meaning; whose expectation and what cost is the other half. | Carry stakeholder + impact inline with each signal (chips/badges), not in a separate section. | Reasoned |
| 9 | **Health is scoped to the *need*; a signal's role is contextual.** The same signal can be *outcome* for one need and *diagnostic* for another. | Label a signal with its role in context ("Outcome for *detection*"), not a fixed global label. | Hypothesis |

### How this plugs into the method

These are the *answers* to Step 5 of the design method (vague → satisfy) for the
multi-workflow case: decompose into workflows (4), lay each out as an ordered
pipeline (1, 3), give each step a business-authored health rule (2, 6), keep
signal→impact inline (8), respect the ~7 boundary (7). The worked example below is
single-process; scale it by stacking one such chain per workflow step.

---

## 5. Worked example (end to end)

**Vague description:** *"What is the health of the Document Generation process?"*

**Step 1 — Narrow** (decide the axes before traversing):

| Axis | Choice | Catalog term |
|------|--------|--------------|
| Altitude | Business process | `archimate:BusinessProcess` |
| Health dimension | On-time delivery rate | APQC — Effectiveness |
| Time scope | Snapshot, rolling 24h | Snapshot |
| View type | RAG at-a-glance | Operational (Few) |

**Step 2 — Traverse** (business-altitude binding):

```
[1] Stakeholder  = Regulator
[2] Driver       = Regulatory Compliance
[3] Requirement  = "Closing Disclosure delivered within 3-day window"
                     dcterms:source           = "12 CFR 1026.19(f)(1)(ii)"
                     openslo:target           = 100
                     openslo:warningThreshold = 95
                     openslo:operator         = "gte"
[4] Outcome      = "CD on-time delivery rate"
                     openslo:indicator.metricSource = Prometheus
                     openslo:reportingWindow        = 24h rolling
[5] Subject      = Document Generation (archimate:BusinessProcess)
[6] Object       = Closing Disclosure (archimate:BusinessObject)   via archimate:Access
```

**Step 3 — Project** to the "is it healthy?" panel: measurement (4) + target (3) +
RAG status. When degraded, the impact projection adds stakeholder (1) + consequence.

**Step 4 — Render** so it passes the acceptance gates:

> **Document Generation — Closing Disclosure on-time delivery**
> 🔴 **93%** (target ≥ 95%) · rolling 24h
> **TRID — Closing Disclosure delayed past 3-day window — 7 customers affected**
> → *Next: why is it red?* (root-cause panel) · *Who do I call?* (ownership)

That last line satisfies **combinatorial meaning** (regulation + deadline + impact
+ count) and **handoff** (paths to triage steps 4 and 6). A consumer who has never
heard of TRID can still decide: red, regulatory deadline miss, 7 customers
affected — escalate.

---

## 6. Evaluating panels that already exist

§1–§5 are written from the generative side: the chain produces a panel. The
diagnostic side — a dashboard already exists, it has grown, and someone needs to
decide what stays — needs two more things, and each has its own file.

| Need | File | The move |
|------|------|----------|
| Is this panel drawn in the right form for the question it answers? | `panel-form-fitness.md` | Question shape → form, plus eight named tests with remedies (right-edge, threshold, naming, gauge, pie, lookup-vs-scan, altitude, dual-axis) |
| Can the reader use the surface at all? | `reading-the-render.md` | Judge the rendered dashboard as its reader sees it. Adversarial, default FAIL, ENGAGE/BOUNCE verdict |
| A grown dashboard needs a justified keep/fix/remove per panel | `dashboard-rationalization.md` | Alarm rationalization (ISA-18.2) applied to panels: the burden of proof sits on the panel. Consumes all three of the above |

**Run them in order.** The diagnostic in §1 comes first — a panel with no named
consumer and no named decision is not a form problem. Form fitness is the second
test, and it only applies to panels that survived the first. The render is a
separate evidence source, not a later step: it is the only place a whole class of
findings exists, and its verdict outranks the panel-level ones.

---

*Everything in this file is the engine in `../SKILL.md` instantiated for
observability. The engine generalizes; this is its most fully validated
application — demonstrated end-to-end across 21 worked examples spanning 8 domains
(including mortgage origination, card authorization, ACH, credit decisioning,
e-commerce checkout, and vendor-integrated flows), all three altitudes, and both
real-time and batch, with no structural exceptions. That is why the patterns in §4
are given as defaults, not suggestions.*

***Scope of that claim.** Those 21 walks are all incident triage — occasion 1 of
the nine in §1b. The chain, the traversal, the altitude bindings and the projection
rules are proven there. Occasions 2–9 carry sound governing questions from named
prior art and unwalked decompositions. When a run uses one of them, say so.*
