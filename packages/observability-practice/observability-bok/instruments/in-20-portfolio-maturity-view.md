# IN-20 — Portfolio Maturity View

**Type:** Communication

**State:** Current

**Lifecycle position:** Cross-cutting (communicates portfolio state at any point)

---

## Purpose

An executive asks "show me where we are across the portfolio." This instrument visualizes the output of the Service Maturity Model ([IN-01](in-01-service-maturity-model.md)) — service distribution across stages, by product line, with stage transition tracking and blocker analysis. It translates assessment data into a format leadership can consume in a meeting.

## Inputs

- Service maturity assessments from [IN-01](in-01-service-maturity-model.md) (per-service stage assignments)
- Org-hierarchy structure — product lines and products (for grouping and rollup)
- Stage transition data (for trend visualization)
- Blocker analysis (for action-oriented narrative)

## Outputs

- **Portfolio distribution visualization** — count and percentage at each stage (Identified → Operationalized), by product line
- **KPI strip** — headline counts: services mapped, beyond Identified, instrumented and above, stage transitions
- **Service detail cards** — individual service progression with stage bar visualization
- **Blocker analysis section** — what's preventing services from advancing, organized by blocker type
- **Legend and methodology explanation** — so the audience understands what they're looking at

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA09 — Strategy & Program](../ka09-strategy-program.md) | Portfolio view informs strategic prioritization and resource allocation |
| [KA10 — Stakeholder Engagement](../ka10-stakeholder-engagement.md) | This is a [KA10.2](../ka10-stakeholder-engagement.md#cross-altitude-communication) (Cross-Altitude Communication) artifact — framing progress for leadership |
| [KA13 — Continuous Improvement](../ka13-continuous-improvement.md) | Stage transitions are practice metrics ([KA13.1](../ka13-continuous-improvement.md#practice-metrics-kpis)) |

## Usage Context

**When to reach for this instrument:**

- Quarterly business reviews — demonstrating adoption progress
- OKR reporting — stage transitions as key results
- Executive presentations — answering "where are we?"
- Investment justification — showing portfolio gaps that need resources

**Related instruments:**

- [IN-01 Service Maturity Model](in-01-service-maturity-model.md) — provides the assessment data this instrument visualizes
- [IN-03 Division Maturity Assessment](in-03-division-maturity-assessment.md) — division-level view that includes this portfolio perspective
- [IN-21 Terrain Presentation](in-21-terrain-presentation.md) — different communication framing (needs-based vs. progress-based)
