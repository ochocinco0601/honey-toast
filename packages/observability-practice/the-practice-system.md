# The Practice System — who consumes observability work, and how to slot an ask

This is a companion to the Observability Body of Knowledge, co-located with it. The BOK is the **depth substrate** — what good observability looks like. This document is the **delivery model** — who consumes observability work, at which altitude, and how to slot an incoming question so you produce the form that consumer can act on. Read it before producing.

> **Not the Four-Layer Model.** The BOK's [Four-Layer Model](observability-bok/the-methodology.md#the-four-layer-model) stratifies one service's *signals* — Business Health, Business Impact, Application, System. The practice system below stratifies the *practice's consumers* — leadership, team leads, engineers, learners, and the producers themselves. Different object (signals vs. consumers), different purpose. When something says "layer," context tells you which model is meant; this document always means the consumer layers.

## Why this matters before you produce anything

Observability practice is one system serving very different consumers — a leadership review and an engineer's Tuesday afternoon are the same practice at different altitudes. **No single artifact serves the whole system.** Each consumer has a different job, and therefore needs a different *form* of the same knowledge.

The most common failure in delivering observability work is not weak content — it is **handing a consumer the wrong layer's form.** A body of knowledge is a producer-facing substrate. Hand it unchanged to an engineer who needs to finish a task today, and it will "bounce" — not because the content is wrong, but because it is the wrong form for that consumer. Reception problems are almost always layer mismatches, not content defects. Diagnosing that correctly is the first thing this model buys you.

## The five layers

| # | Layer | Consumer | Their job | Typical forms |
|---|-------|----------|-----------|---------------|
| 1 | **Positions / Strategy** | Leadership, review boards, architecture governance | Decide and defend: "are we ready? what's our approach?" | Position papers, readiness matrices, acceptance bars, one-pagers |
| 2 | **Standards** | Team leads, architects, quality/toll-gate processes | Know what's required of my team | Standards, blueprints, gate criteria (this BOK's standard: [IN-23](observability-bok/instruments/in-23-observability-standard.md)) |
| 3 | **BAU / Daily work** | Engineers with today's task | Get it done: onboard, instrument, find my tool, respond | Golden paths, how-tos, templates and other [instruments](observability-bok/instruments/README.md), runbooks; plus *adopted* external canon for depth (SRE books, OpenTelemetry docs, vendor academies) |
| 4 | **Learning** | People becoming capable | Come up to speed on the practice | Training, explainers, curriculum |
| 5 | **Knowledge substrate** | The *producers* of layers 1–4 | Keep everything one story | **A role, not an artifact** — whatever the upper layers pull depth and consistency from. This BOK is the current occupant. What must be singular is the consistency *discipline* (check new positions and standards against prior ones), not the container. |

## How the layers relate

- **Flow.** Positions (1) set direction → standards (2) make it enforceable → daily surfaces (3) make it doable → what daily work discovers feeds back into the substrate (5). Learning (4) rides alongside. Investment in the substrate (5) follows *pull* from the upper layers, never completeness for its own sake — the substrate keeps only as much depth as production actually reaches into.
- **Different consumer = different form.** This is the load-bearing property. The same knowledge is re-cut per layer; a layer-3 consumer must receive a layer-3 form even when the content originates in layer 5.
- **Single-layer execution is the decay signature.** A cleanup done only at layer 3, with no standing standard at layer 2, re-accumulates. Work done at layer 3 with no position at layer 1 loses to the first pushback. When an initiative stalls or regresses, look for the *missing layer* before adding more effort at the layer it already occupies.

## Slotting an ask

When a question arrives, name the layer *first*, then work the question at that altitude. The three-second test:

> **Who consumes the answer, and what do they do with it?**
> Decide → **1** · impose on their team → **2** · finish today's task → **3** · get smarter → **4** · keep the whole story consistent → **5**.

Two rules make the test reliable:

1. **Slot the ask in front of you, never the initiative or the meeting.** Initiatives are multi-layer by design; one status meeting can switch layers several times in ten minutes. Place the single artifact or question you are actually holding.
2. **Say the slot out loud** ("this is a layer-1 position ask") so it can be corrected cheaply before you invest in the wrong form. Then work at that altitude and hold the neighboring layers without dragging them in.

## The shape is generic; this instance is observability

The five layers are the enterprise-governance pattern **policy → standard → procedure**, extended with a learning track and a producing substrate. That shape fits any practice domain — security hygiene, SDLC, platform engineering. *This* instance is observability. The value of recognizing the shape is that **decay signatures read across domains**: "a cleanup with no standing standard" is the same disease everywhere, and naming it inside a neighboring practice is a contribution the model makes portable.

## Prior-art grounding

The layers are not invented here — each is established practice. The *arrangement* into one practice system is this document's composition.

| Layer / element | Named prior art |
|---|---|
| The 1 → 2 → 3 hierarchy | Policy → Standard → Procedure → Guideline hierarchy (enterprise governance canon; ISO/IEC 27001 practice; COBIT governance-vs-management) |
| One strategy pitched per altitude | Hoshin Kanri — objectives cascade to measures to initiatives, same content per level (see [KA09](observability-bok/ka09-strategy-program.md)) |
| Layer 3 forms | Platform-engineering paved road / golden path (Team Topologies, platform-as-product); Diataxis *how-to* type; KCS (Knowledge-Centered Service) — articles authored demand-driven from real incoming questions |
| Layer 3 / 4 split | Diataxis working-vs-learning distinction |
| Layer 4 canon | Adopt-don't-author — Google SRE Book/Workbook, OpenTelemetry docs, vendor academies; write only the local delta |
| Layer 5 pattern | The body-of-knowledge structural pattern itself (BABOK / PMBOK / SWEBOK); single-sourcing / structured authoring (DITA) — one source fabric, many cut deliverables |

## How this document is used

1. A question arrives → name the consumer → that names the layer → that names the form and the fitness test.
2. Work at that altitude; hold the neighbors, don't drag them in.
3. When something delivered doesn't land, check for a layer mismatch *before* concluding the content is wrong.
4. When an initiative decays, look for the missing layer.

## Content state

**Current** — the model, the slotting test, and the decay signature are actionable from this document. Mapping specific artifacts to layers is done per artifact by the reader, using the three-second test above.
