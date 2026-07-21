# IN-11 — Dashboard Factory

**Type:** Production

**State:** Seeded

**Lifecycle position:** Observe

---

## Purpose

A Platform Engineer needs dashboards for a service that has completed signal definition and instrumentation. The Dashboard Factory turns service profile and signal data into monitoring dashboards — a factory here is a generation procedure, implementable as deterministic tooling or an AI-executed method — with consistent styling, layout patterns, and data binding, without manual dashboard construction per service.

## Inputs

- Service profile with stakeholder expectations (from [IN-04](in-04-service-profile-template.md), [IN-06](in-06-stakeholder-expectation-template.md))
- Signal definitions with service-level objective (SLO) targets and formulas (from [IN-05](in-05-signal-definition-template.md), [IN-07](in-07-health-signal-template.md))
- Dashboard generation methodology rules (from [IN-15](in-15-dashboard-generation-methodology.md))

## Outputs

- **Service-level dashboards** — Business Health at top, Business Impact tiles, Application- and System-layer mechanism panels at bottom
- **Executive dashboard panels** — aggregated views rolled up by product or product line (org hierarchy)
- **Consistent styling** — follows established UI/UX patterns, color coding, layout rules

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA04 — Monitoring & Visualization](../ka04-monitoring-visualization.md) | This instrument produces [KA04.1](../ka04-monitoring-visualization.md#dashboard-design-standards) (Dashboard Design) output and [KA04.5](../ka04-monitoring-visualization.md#business-health-views) (Business Health Views) |

## Usage Context

**When to reach for this instrument:**

- A service reaches Instrumented stage and needs production dashboards
- New signals are added to an existing service
- Dashboard standards are updated and existing dashboards need regeneration

**Related instruments:**

- [IN-15 Dashboard Generation Methodology](in-15-dashboard-generation-methodology.md) — the rules this factory follows
- [IN-22 Executive Dashboard Patterns](in-22-executive-dashboard-patterns.md) — design patterns for the executive-level output
- [IN-05 Signal Definition Template](in-05-signal-definition-template.md) — signal data drives panel content
