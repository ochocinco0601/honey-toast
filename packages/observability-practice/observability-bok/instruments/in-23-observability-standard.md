# IN-23 — Observability Standard (One Content, Three Forms)

**Type:** Definition
**State:** Current — the agent-workflow vocabulary is provisional (industry still converging)
**Lifecycle position:** Define → Respond (the standard every stage tests against)

---

## Purpose

A team lead asks: "We have dashboards and alerts — is our monitoring actually *good*?" This instrument is the written answer: the definition of what good looks like for a business function, concrete enough that you can hold your own monitoring next to it and see where you stand. Deficiency reads as an unfilled position against the definition — never as a judgment of your work or anyone else's.

## The Content

The definition has four parts: the canonical signal sets per layer, the chain, the computation rule, and the rhythm criteria.

**Canonical signal sets** — what to measure at each layer:

| Layer | The question it answers | Canonical set | Grounding |
|---|---|---|---|
| Business health | is the stakeholder expectation met? | Effectiveness · Efficiency · Adaptability | adapted from APQC (American Productivity & Quality Center) process measurement practice |
| Business impact | what does a breach cost? | Customer · Financial · Legal/Risk · Operational | this BOK's synthesis, informed by COSO impact categories and business-impact-analysis practice (ISO 22301) |
| Application | is the workflow behaving? | Latency · Errors · Traffic · Saturation | Four Golden Signals (Google SRE); RED method (Wilkie) for request-driven services |
| System | is the substrate sound? | Utilization · Saturation · Errors | USE method (Gregg) |
| Agent workflow *(when a step is software that can be confidently wrong)* | is the decision right, and how would we know? | Correctness · Grounding · Traceability · Drift *(provisional; Escalation/Autonomy a candidate)* | this BOK's provisional synthesis — OpenTelemetry GenAI conventions, NIST AI Risk Management Framework, evaluation taxonomies (industry converging, not converged) |

The application and system sets are industry-canonical. The business-layer sets are this BOK's synthesis of the named prior art.

**The chain** — the BOK's semantic chain, which every monitored function must be able to walk in both directions:

```
stakeholder → expectation → business health signal (supported by process and system signals)
  → on breach: business impact signal → alert → owner + next action
```

Who cares; what they expect; the measurement that tells you whether it's met, on a stated target, with the mechanism signals that explain it; what a breach costs them, quantified; and who acts on what when it fires. Good = every position filled with recorded content, at every layer that applies. Deficiency = a position that cannot be filled when walked.

**The computation rule** — status at every layer is computed from that layer's own signals, never attested by a person. A green that no signal computes is not a green. Layers do not derive status from one another: a green mechanism never computes a green business outcome — that gap (healthy System and Application, failing Business Health) is the blind spot the methodology exists to make visible.

**The rhythm criteria** — a recurring operational review counts as a rhythm when it (a) covers the inventory, (b) runs on a cadence, (c) is owned, and (d) is repeatable. Fewer than all four is an event, not a rhythm.

## The Three Forms

The definition is carried in three forms, and it takes all three:

| Form | Job | What happens when it's missing |
|---|---|---|
| A — the Model | teaches by example | records decay into attestation — statuses nobody computed |
| B — the Record | captures each function | the definition stays a textbook nobody applies |
| C — the Test | verifies against reality | records decay into form-filling — boxes ticked, incident questions unanswerable |

## Form A — the Model

One real business function, worked through the layers with the chain filled, shown beside an empty copy of the same positions. Compare your own function to the worked column; the empty column is yours to fill — your blanks are your placement.

The worked column below is drawn from a real service record produced by this practice — a payments transaction-acceptance service — not invented for this page:

| Chain position | Worked: payment acceptance | Yours |
|---|---|---|
| Stakeholder | Bank customers (critical) — also compliance, finance, operations, each with their own chain | |
| Expectation | "Payments complete successfully and quickly" | |
| Impact if breached | Immediate, total payment inability — sole path, no fallback; trust and account-closure risk (customer category) | |
| Signal — business health | Transaction success rate ≥ 99.5% over rolling 30 days, computed from request telemetry (effectiveness); processing duration p95 (efficiency); volume capacity headroom (adaptability) | |
| Signals — application beneath | Payment validation pass rate; dependency latency (balance check p95); each with warning/critical thresholds | |
| Signals — system beneath | Service availability, resource utilization/saturation/errors under the application signals | |
| Playbook | Each signal names its owner, alert severities, and response — failure modes recorded with their detection signal | |

A status rolls up only by computation: the business-health tile is green because the success-rate signal says so, which is measurable because the application and system signals beneath it exist.

## Form B — the Record

Each function gets its own record of exactly these positions: identity and tier, stakeholders and their expectations, impact categories, signals per layer with targets and owners — every answer carrying its source, and open gaps recorded rather than hidden. The record templates are this catalog's Definition instruments ([IN-04](in-04-service-profile-template.md) through [IN-09](in-09-signal-specification-format.md)); the facilitated conversation that fills them is [IN-19](in-19-discovery-dialogue-protocol.md).

## Form C — the Test

Rehearse the incident before it happens: walk the questions production actually asks — *who is affected right now? what does it cost? which signal says so? who acts?* — against the record. Good monitoring = every question finds a recorded answer at the layer where it belongs. Every question that can't be answered names its missing chain position, and that is the finding. At the review level, apply the four rhythm criteria to each recurring operational review.

Prior art: game days (chaos engineering), Google DiRT, tabletop exercises (NIST SP 800-84).

## Producing a Placement

Two ways to use the standard:

- **Self-comparison (no prerequisites):** bring your monitoring as it exists. Walk each chain position at each layer against the worked example. Your unfilled positions, per layer, are your placement.
- **Recorded placement:** once a function has a Form B record, the placement is durable and computable — and [IN-01](in-01-service-maturity-model.md) translates filled positions into a maturity stage.

Either way the output is a map of filled and unfilled positions — a distance from the definition, on the definition's own terms.

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA01 — Business Context](../ka01-business-context.md) | The chain's top positions: stakeholder, expectation, impact |
| [KA02 — Signal Design](../ka02-signal-design.md) | The canonical signal sets are its per-layer vocabularies |
| [KA03 — Standards & Quality](../ka03-standards-quality.md) | This instrument is the standard the enforcement stage applies |
| [KA04 — Monitoring & Visualization](../ka04-monitoring-visualization.md) | The computation rule governs every status surface |
| [KA05 — Incident Response](../ka05-incident-response.md) | Form C asks [KA05](../ka05-incident-response.md)'s questions before the incident does |

## Usage Context

**When to reach for this instrument:**
- Design or review time for any critical flow — "when this breaks silently, how will anyone know?"
- Evaluating an existing monitoring surface — walk the chain positions against it
- Standing up or auditing a recurring operational review — apply the rhythm criteria

**Related instruments:**
- [IN-01 Service Maturity Model](in-01-service-maturity-model.md) — translates a placement into a maturity stage
- [IN-04 Service Profile Template](in-04-service-profile-template.md) — Form B's root record
- [IN-05 Signal Definition Template](in-05-signal-definition-template.md) — Form B's signal rows
- [IN-06 Stakeholder Expectation Template](in-06-stakeholder-expectation-template.md) — Form B's chain top
- [IN-19 Discovery Dialogue Protocol](in-19-discovery-dialogue-protocol.md) — the conversation that fills Form B
