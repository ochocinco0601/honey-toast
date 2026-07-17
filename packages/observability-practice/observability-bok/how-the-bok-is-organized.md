# How the BOK is Organized

This page explains the mental model behind the Observability Body of Knowledge — how it's structured, why it's structured that way, and what that structure makes possible.

## Three structural elements

The BOK has three peer structural elements: Knowledge Areas, Practice Instruments, and Perspectives. Knowledge Areas organize *what you need to understand* (invariant across platforms). Practice Instruments organize *what you pick up and use*. Perspectives organize *how both vary by platform-type or workload context*.

## Three axes, one spine

The BOK organizes along three axes — knowledge, instruments, and perspectives — connected by a lifecycle spine.

### Axis 1 — Knowledge Areas

A **Knowledge Area (KA)** is a major division of the observability domain — what practitioners need to understand. There are 13, grouped into three tiers.

- **Core Practice** — the five lifecycle stages: *Define, Implement, Enforce, Observe, Respond.* These are [KA01](ka01-business-context.md) through [KA05](ka05-incident-response.md).
- **Enabling Practice** — cross-cutting infrastructure that every lifecycle stage depends on: Platform & Tooling ([KA06](ka06-platform-tooling.md)), Integration & Architecture ([KA07](ka07-integration-architecture.md)), Data Management & Governance ([KA08](ka08-data-governance.md)).
- **Management Practice** — the organizational layer: Strategy ([KA09](ka09-strategy-program.md)), Stakeholder Engagement ([KA10](ka10-stakeholder-engagement.md)), Organizational Capability ([KA11](ka11-organizational-capability.md)), Adoption & Enablement ([KA12](ka12-adoption-enablement.md)), Continuous Improvement ([KA13](ka13-continuous-improvement.md)).

This axis answers: *where does this topic sit?*

### Axis 2 — Practice Instruments

A **Practice Instrument** is a concrete tool a practitioner picks up and uses — templates, assessments, factories (generation procedures that turn definition records into artifacts), protocols. There are 23, grouped into five types by the kind of action they support.

- **Assessment** (3) — *where are we?*
- **Definition** (7) — *what do I fill out?*
- **Production** (6) — *what gets produced?*
- **Adoption** (4) — *how do teams get started?*
- **Communication** (3) — *how do we show progress?*

This axis answers: *what can I pick up and use?*

Instruments are peers of Knowledge Areas, not children. A single instrument usually draws from several KAs — it can't be filed under one.

### The spine — the observability lifecycle

The Core Practice Knowledge Areas run a lifecycle:

```
Define → Implement → Enforce → Observe → Respond
 KA01      KA02        KA03      KA04      KA05
```

Dependencies flow left to right:

- You cannot **observe** what you haven't **instrumented.**
- You cannot **instrument** what you haven't **defined.**
- Business context (the Define stage) scopes everything downstream.

Every observability question, wherever it seems to arrive, traces back through this chain. The spine is what makes the BOK *walkable* — it establishes the dependency order that lets a reader reason about where an issue originates, not just where it manifests.

## Perspectives — the third peer

A **Perspective** is a platform-type or context-type lens that bends how Knowledge Areas and Instruments apply. Mainframe instrumentation is structurally different from cloud-native instrumentation — same KAs, different techniques. A perspective names those variations without fragmenting the underlying KAs.

Current perspectives: Cloud-Native, Mainframe, Hybrid / Integration-Oriented, SaaS / Third-Party (platform-type), and Agentic (workload-type — services containing a judgment-making software step). Perspectives are not KAs (they don't own distinct knowledge) and not Instruments (they don't do one thing); they're lenses that bend the existing KAs.

This axis answers: *how does this vary in my platform or workload context?*

## Use modes

The three structural elements plus the spine give the BOK four reader modes:

- **Locate** — use Knowledge Areas to answer *where does this topic sit?*
- **Act** — use Practice Instruments to pick up a tool for a specific task.
- **Vary** — use Perspectives to find platform- or workload-specific guidance for a KA or Instrument.
- **Walk** — use the spine plus cross-references to trace dependencies through the chain, checking content state at each stop.

The fourth mode is where the BOK earns its keep. See [How to walk a question](how-to-walk-a-question.md) for a worked example.

## Content states

Every topic and every instrument carries one of three states:

- **Current** — practitioner-actionable from the page alone. Not merely *a file mentions the topic* — a practitioner could read this and act.
- **Seeded** — named gap with prior art. The structure declares the topic; content is queued or partial.
- **Missing** — acknowledged absence. The structure declares where the content should live; the content doesn't yet exist.

A Seeded topic is useful information. It tells a reader: *this exists in the domain, we know it belongs here, we haven't built it yet.* An honest negative is more useful than a silent absence.

## What this structure makes possible

Three capabilities a flat wiki doesn't offer:

- **Dependency walks.** From any starting topic, cross-references trace through the lifecycle to the upstream concepts the topic depends on. A search engine finds nodes; the BOK shows edges.
- **State-aware reasoning.** Every node on a walk shows its content state. A reader sees where the chain is solid and where it breaks — and can direct investment accordingly.
- **Predictable navigation.** Every topic has a home determined by the organizing principle. A reader can predict where a new concept will live without searching.

## Design choices this structure takes

A few places where the organization takes an opinionated position:

- **Business context first.** Observability work often starts with telemetry and adds business meaning later. The BOK reverses that — [KA01](ka01-business-context.md) Business Context is the entry point; signals and instrumentation are downstream.
- **Instruments as peers, not children.** Techniques and tools could be filed under their most-related KA. Instead, they live in a parallel catalog, because real instruments draw from several KAs at once.
- **Structure over completeness.** The BOK declares Seeded and Missing topics rather than hiding them. The structure communicates intent even where content is thin.
- **Human-readable, machine-readable.** The primary reader is a practitioner. The markdown pages and accompanying YAML layer are also machine-readable, so the dependency structure can be traversed programmatically — a secondary benefit, not the primary design target.

For the prior art these choices adopt from, and the full rationale, see [About This BOK](about.md).
