# IN-03 — Division Maturity Assessment

**Type:** Assessment

**State:** Seeded

**Lifecycle position:** Cross-cutting (division-level assessment combining service and organizational maturity)

---

## Purpose

A division leader asks "how mature is our observability practice across our portfolio?" This instrument applies a two-dimension assessment matrix to a technology division — combining service-level progression ([IN-01](in-01-service-maturity-model.md)) with organizational capability indicators — to produce a portfolio-wide maturity picture.

## The Two Dimensions

| Dimension | What it measures | Source |
|-----------|-----------------|--------|
| **Technical maturity** | How far services have progressed through the maturity stages (Identified → Operationalized) | Aggregated from [IN-01](in-01-service-maturity-model.md) (Service Maturity Model) |
| **Organizational maturity** | Process consistency, role clarity, standards adoption, practice sustainability | Assessed against [IN-02](in-02-industry-maturity-arc.md)'s process-maturity dimension — consistency, repeatability, accountability |

The two dimensions are independent — a division can have technically mature services (good instrumentation) but immature organizational practices (ad hoc, person-dependent), or vice versa.

## Inputs

- Service maturity data from [IN-01](in-01-service-maturity-model.md) across the division's portfolio
- CMDB application inventory (total service count for coverage calculation)
- Organizational indicators: documented practices, role assignments, standard adoption rates
- Existing assessment data (Gartner, internal audit findings)

## Outputs

- **2x2 matrix placement** — technical vs. organizational maturity for the division
- **Service distribution** — count of services at each maturity stage across the division
- **Coverage metric** — percentage of division services with any observability engagement
- **Capability gaps** — specific areas where technical or organizational maturity lags
- **Recommended focus areas** — where investment would have the highest maturity impact

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA09 — Strategy & Program](../ka09-strategy-program.md) | Assessment outputs drive division-level strategy and resource allocation |
| [KA11 — Organizational Capability](../ka11-organizational-capability.md) | Organizational dimension directly assesses [KA11](../ka11-organizational-capability.md) topics |
| [KA13 — Continuous Improvement](../ka13-continuous-improvement.md) | Assessment is a periodic practice improvement activity |

## Usage Context

**When to reach for this instrument:**

- Annual or semi-annual division-level maturity reviews
- Investment planning — justifying observability resources based on assessed gaps
- Cross-division comparison — showing relative maturity across technology divisions
- Enterprise rollup — aggregating division assessments into an enterprise maturity picture

**Related instruments:**

- [IN-01 Service Maturity Model](in-01-service-maturity-model.md) — provides the technical maturity dimension data
- [IN-02 Industry Maturity Arc](in-02-industry-maturity-arc.md) — provides the organizational maturity framework
- [IN-20 Portfolio Maturity View](in-20-portfolio-maturity-view.md) — visualizes the assessment output for stakeholders
