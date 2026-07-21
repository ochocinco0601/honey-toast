# IN-02 — Industry Maturity Arc

**Type:** Assessment

**State:** Seeded

**Lifecycle position:** Cross-cutting (organizational-level assessment, not per-service)

---

## Purpose

An executive asks "where are we compared to the industry?" or a practice lead needs to position the organization's observability capability within a recognized maturity framework. This instrument provides a 5-stage organizational arc synthesized from published industry maturity models (Gartner, Forrester, DORA, and major vendor frameworks), with the Stage 2→3 boundary identified as where most organizations stall.

## The Five Stages

| Stage | Name | Capability | Industry position |
|-------|------|-----------|-------------------|
| 1 | **Reactive Monitoring** | Basic uptime checks, manual investigation, siloed tools | Starting point — most legacy monitoring |
| 2 | **Structured/Technical Observability** | Standardized instrumentation, centralized platforms, metrics/logs/traces correlated | Where most mature organizations operate today |
| 3 | **Correlated/Business-Aware** | Signals connected to business context, stakeholder-defined health, business impact quantified | **Business observability operates here** — the transition most organizations haven't made |
| 4 | **AI-Assisted/Predictive** | Anomaly detection, predictive alerts, automated correlation across services | Emerging in vendor tooling, rare in practice |
| 5 | **Autonomous/Self-Healing** | Automated remediation, self-tuning thresholds, closed-loop operations | Aspirational — limited real-world examples |

## Two Orthogonal Dimensions

The research identifies two independent maturity axes:

- **Process maturity (CMM dimension):** Consistency of execution — are practices standardized, repeatable, accountable?
- **Capability maturity (observability dimension):** What you can see and measure — technical sophistication to business-aware

An organization can be high on one and low on the other. Standardized basic monitoring (high process, low capability) is not the same as ad hoc sophisticated observability (low process, high capability). The destination is high on both.

## Inputs

- Current observability tool landscape and coverage
- Observability practice maturity indicators across KAs (from [KA11](../ka11-organizational-capability.md)/[KA13](../ka13-continuous-improvement.md) assessments)
- Industry benchmark data (Gartner, Forrester, DORA reports)

## Outputs

- **Organizational stage placement** — where the organization sits on the 5-stage arc
- **Dimension assessment** — separate process maturity and capability maturity scores
- **Gap analysis** — what's required to advance to the next stage
- **Strategic positioning** — how to frame current state and target state for leadership

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA09 — Strategy & Program](../ka09-strategy-program.md) | Stage placement informs strategic direction and investment justification |
| [KA11 — Organizational Capability](../ka11-organizational-capability.md) | Organizational capability determines what stage is achievable |
| [KA13 — Continuous Improvement](../ka13-continuous-improvement.md) | Arc position is a practice-level maturity indicator |

## Usage Context

**When to reach for this instrument:**

- Strategic planning — positioning observability investment against industry benchmarks
- Executive presentations — "here's where we are, here's where we're going, here's what the industry looks like"
- Investment justification — demonstrating the Stage 2→3 gap and the business value of crossing it

**Related instruments:**

- [IN-01 Service Maturity Model](in-01-service-maturity-model.md) — per-service progression (tactical); this instrument is organizational (strategic)
- [IN-03 Division Maturity Assessment](in-03-division-maturity-assessment.md) — applies this arc to a specific technology division
