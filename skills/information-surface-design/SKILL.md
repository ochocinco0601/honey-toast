---
name: information-surface-design
description: >
  Design or evaluate ANY information surface — a dashboard, a panel, an intake
  form, a status report, a triage view, a navigation hierarchy, a ticket queue —
  so that it collapses need → uncertainty → decision. Use when designing a new
  surface someone will act on, diagnosing why an existing surface isn't useful,
  deciding what a view must show, or any time a person needs information in order
  to decide something. Triggers on "design a dashboard/form/report/view", "what
  should this show", "why isn't this useful", "evaluate this surface", "this
  dashboard doesn't help", or any work where a surface exists to support a
  decision. Observability panels are one worked instance (see
  references/observability-panels.md), not the limit of this skill.
---

# Information Surface Design — The JTBD Chain

> **What this is.** A lens for designing and evaluating any information surface.
> It is not a template library and not a tool to run — it is a way of reasoning
> that you apply whenever someone needs a surface to make a decision. The deep
> claim is small and general; the value is that it holds across *every* kind of
> surface, not just dashboards.
>
> **Prior art.** Christensen *Jobs To Be Done* — full form *When [circumstance],
> I want to [job], so I can [outcome]*. The "one idea" below works the
> [job]→[outcome] (consumption) side; step 4 of the method adds the [circumstance]
> (supply) side — what the consumer can actually put in. Basili *GQM*
> (goal → question → metric).

---

## The one idea

**Any information surface is hired to collapse a chain of uncertainty so a person
can make a decision.**

```
  someone has a NEED  ──▶  they face UNCERTAINTY  ──▶  something RESOLVES it  ──▶  they make a DECISION
   (a responsibility      ("what I don't yet know     (the surface carries        ("act or wait,
    creates a need to      that I need to know to      enough context to            approve or reject,
    know something")       act")                       collapse the gap")           escalate or accept")
```

This describes what a surface is *for* — whether its author knows it or not,
whether it achieves it or not. A surface does not exist to "show information." It
exists to **collapse a specific uncertainty behind a specific decision.** If you
can't name the decision, you can't design the surface — you can only decorate it.

**Decisions chain.** Each resolved uncertainty creates the next need. That is why
triage flows, navigation hierarchies, intake funnels, and drill-downs all share
one shape: every answered question is the next hiring moment.

---

## The diagnostic chain — a general pattern

When the work is **triage or troubleshooting**, the needs don't arrive one at a
time — they arrive in a canonical *sequence*, each one a need→uncertainty→decision,
each handing off to the next. This is the "decisions chain" above, made concrete.
It is the single most reusable instance of this engine.

| Step | The diagnostic move | The decision it unlocks | Hands off to |
|------|--------------------|------------------------|--------------|
| 1 | **Detect** — is there a problem? | act or move on | localize |
| 2 | **Localize** — what, specifically? | narrow focus | assess |
| 3 | **Assess** — what are the stakes? | urgency | diagnose |
| 4 | **Diagnose** — why? | remedy / root cause | scope |
| 5 | **Scope** — what else is affected? | blast radius | assign |
| 6 | **Assign** — who owns it? | escalate | remediate |
| 7 | **Remediate** — what's the fix? | resolve | close (or detect again) |

**The order is the point — it's the connective tissue.** Each step resolves an
uncertainty the next one depends on: you can't weigh the stakes before you've
localized the problem; you can't remediate before you've diagnosed it. Skipping or
reordering a link is where triage goes wrong. The sequence isn't a checklist — it's
a dependency chain.

Two things make this pattern carry far more value than any single surface:

- **It's artifact-agnostic.** A dashboard panel is *one* way to answer a step — but
  so is an alert, a query, a runbook, a dependency map, an on-call engineer's mental
  model, or a postmortem. Don't collapse the question into one answer-surface.
- **It's a coverage spec, not just a flow.** Point it at an entire observability
  *system* (not one surface) and ask: does our tooling answer all seven? Most orgs
  answer "is it healthy?" and "why?" well, and leave "what are the stakes?" and
  "what else is affected?" as blind spots. The chain names the gaps.

The shape generalizes past observability — software debugging, security incident
response, even clinical triage run the same detect → localize → assess → diagnose →
scope → assign → remediate sequence. Observability is the instance with the most
worked detail; see `references/observability-panels.md`.

---

## The design method (the core practice)

When you get a vague description — *"I need to see X"*, *"this report isn't
useful"*, *"what should this form capture"* — do not jump to layout. Walk this.
Steps 2–4 are where human judgment lives.

1. **Start with the vague description.** Stay in it. Don't design yet.
2. **Walk the chain.** For the person described, articulate:
   - **Need** — what responsibility creates the requirement to know something?
   - **Uncertainties** — what don't they know? *Enumerate — there are usually
     several, layered.* They may not know the aggregate state, the structure
     (what the parts are), the relationships (how parts affect each other), which
     part is the problem, or the consequence. **Order matters** — some
     uncertainties must resolve before others become meaningful.
   - **Decision** — what action does resolving these enable?
3. **Articulate for review.** Write the chain out plainly. Is the need grounded
   in a real responsibility? Are the uncertainties specific enough to test? Is the
   decision concrete? Aim for *plausible*, not perfect.
4. **Name what the consumer can supply — the circumstance.** The chain so far is
   the *consumption* side: what the consumer needs *out*. Turn it around — in their
   actual circumstance, what can they put *in*?
   - **Inputs** — what data, telemetry, or context is actually available to populate
     the surface?
   - **Access** — what's reachable in their environment, under what constraint
     (air-gapped, regulated, permissioned)?
   - **Expertise** — what can this consumer act on *without* becoming an expert?

   This is Christensen's *[circumstance]* — the half a consumption-only chain drops,
   and it's load-bearing: **a surface whose decision needs inputs the consumer can't
   supply is undesignable** — decoration, in the sense above. **When the constraint
   binds** — they can't supply or act on what the decision needs — it stops being a
   design question and becomes a *function-allocation* one (Sheridan & Verplank
   levels of automation; Fitts's list): who does what, the tool or the human?
   Allocate it explicitly; don't ship a surface that silently assumes inputs that
   aren't there.
5. **Think through what satisfies the job.** Given the enumerated uncertainties,
   what must the surface show to resolve them — and in what structure? A **naive**
   consumer needs the structure taught by the layout; an **expert** needs only
   isolation. Design for the actual consumer.
6. **Produce or evaluate** (the two faces, below).

---

## Two faces: generative and diagnostic

The chain runs in both directions. **Default to diagnostic** when asked to "look
at" or "review" a surface — what does the chain reveal is *missing*? — not
taxonomic ("is this an example of the chain?").

- **Generative** — build the surface; verify every chain position is filled.
- **Diagnostic** — walk the chain against an existing surface; each unfilled
  position is a specific, nameable gap, not a vague "could be better."

### The general diagnostic

| Ask | Healthy | Common failure |
|-----|---------|----------------|
| Is the **need** named? | Whose responsibility, deciding what | Implied by the title, or absent |
| Are the **uncertainties** enumerated and ordered? | The specific unknowns, in dependency order | One vague "status" that hides several questions |
| Is the **decision** concrete? | A named action the surface unlocks | "Awareness" — no action it serves |
| Does the surface **collapse** each uncertainty? | Context sufficient to decide | Data displayed *near* the question but not answering it |

---

## When does a surface actually land? (acceptance gates)

Two gates, both required, on any surface:

- **Combinatorial meaning.** Domain-specific terms must appear *alongside enough
  plain-language framing* — a measurement, a threshold, a consequence, an
  affected party — that the combination conveys meaning to someone ignorant of
  the term. The surface does not *teach* the term; it surrounds it with context
  so an outsider gets the gist.

  | Poor | Lands |
  |------|-------|
  | `TRID` | **TRID — Closing Disclosure delayed past 3-day window — 7 customers affected** |
  | `409 incidents` | **409 incidents — 6× normal — payment auth degraded since 14:20** |

- **Handoff.** The surface must surface enough context that the consumer can reach
  the *next* decision in the chain. A surface that answers one question but gives
  no path to the next breaks the flow.

---

## Instances (where this bites)

The chain is universal; each instance is the chain wearing a domain's skin. The
engine above is constant — the instance supplies the domain vocabulary, the
specific positions, and any production machinery.

| Instance | Who has the need | The decision | Where it lives |
|----------|------------------|--------------|----------------|
| **Observability panels** *(deepest worked instance)* | Operator / stakeholder during triage | Act, escalate, investigate, accept | `references/observability-panels.md` |
| **Request intake** | A receiver triaging incoming requests | Accept, defer, redirect, decompose | your intake surface |
| **Service onboarding (SUD)** | A practitioner profiling a service | How to structure the service profile | the SUD instrument |
| **Status report / briefing** | A leader deciding where to spend attention | Fund, intervene, stay the course | briefing discipline |

**To add an instance:** name the domain vocabulary for each chain position, the
diagnostic in that vocabulary, and any production machinery. Don't re-derive the
engine — it's done.

> **Observability panels** are the most fully developed instance — they carry a
> sequenced triage chain, a full ArchiMate production traversal, altitude-specific
> health frameworks, projection rules, and resolved multi-workflow layout
> opinions. Load `references/observability-panels.md` when the surface is an
> observability dashboard or panel. Everything there is *this engine, instantiated*
> — read this file first. It is also the most heavily validated instance, which is
> why its patterns are stated as defaults rather than suggestions.

---

## Quick reference

- A surface collapses: **need → uncertainty → decision.** Name the decision first.
- Method: vague description → walk the chain (need / uncertainties / decision) →
  articulate → **name what the consumer can supply (inputs / access / expertise)** →
  think through what satisfies → produce or evaluate.
- Supply side: a surface whose decision needs inputs the consumer can't supply is
  undesignable. When the constraint binds, it's a *function-allocation* question
  (who does what — tool or human), not a design one.
- Done when: domain terms are surrounded by plain context (combinatorial meaning)
  AND the surface points to the next decision (handoff).
- Two faces: generative (build it) and diagnostic (walk the chain, name the gaps).
- Naive consumer needs structure visible upfront; expert needs only isolation.
- Reach for an instance file when the surface has a domain (observability →
  `references/observability-panels.md`).
