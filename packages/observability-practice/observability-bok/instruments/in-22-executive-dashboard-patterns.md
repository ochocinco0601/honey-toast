# IN-22 — Executive Dashboard Patterns

<table style="border: 1px solid var(--md-typeset-table-color, #ddd); border-left: 4px solid var(--md-primary-fg-color, #673ab7); border-collapse: collapse; margin: 1em 0; font-size: 0.95em;">
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Type</th>
    <td style="padding: 0.4em 0.9em;">Communication</td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">State</th>
    <td style="padding: 0.4em 0.9em;"><a href="index.html#content-state-key">Current</a></td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Lifecycle position</th>
    <td style="padding: 0.4em 0.9em;">Observe</td>
  </tr>
</table>

---

## Purpose

An executive needs to see business health — not infrastructure metrics, not raw signal data, but "are the things the business cares about working?" Executive Dashboard Patterns define the design principles for dashboards consumed by leadership: altitude-appropriate views, business-first rendering, impact-oriented tiles, and stakeholder-meaningful language.

## Inputs

- Dashboard generation methodology ([IN-15](in-15-dashboard-generation-methodology.md)) for structural consistency
- Service profiles with stakeholder expectations ([IN-04](in-04-service-profile-template.md), [IN-06](in-06-stakeholder-expectation-template.md)) for business context
- Org-hierarchy structure — product lines and products — for rollup views
- Executive audience needs (what decisions they make from dashboard data)

## Outputs

- **Design patterns** for executive-level dashboards:
  - Business health tiles — expectation attainment ("is the stakeholder expectation being met?"), not system uptime. **Expectation** is the primary vocabulary for this audience; the service-level objective (SLO) is the technical mapping behind the tile, not its label
  - Impact tiles (Business Impact layer consequences — customers affected, dollars at risk)
  - Rollup views by product or product line
  - Trend overlays (are things getting better or worse?)
- **Anti-patterns** — what executive dashboards should NOT include (raw metrics, technical jargon, infrastructure detail)
- **Rendering rules** — business-first layout, stakeholder language, failure-framed state descriptions (definitions are stored in success terms; the business-facing view displays failure rates and who is affected, because failure is what demands action), color coding standards

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA04 — Monitoring & Visualization](../ka04-monitoring-visualization.md) | Executive dashboards are a specific [KA04.1](../ka04-monitoring-visualization.md#dashboard-design-standards) (Dashboard Design) and [KA04.5](../ka04-monitoring-visualization.md#business-health-views) (Business Health Views) pattern |
| [KA10 — Stakeholder Engagement](../ka10-stakeholder-engagement.md) | Dashboards are a communication channel — design must match the audience |

## Usage Context

**When to reach for this instrument:**

- Designing dashboards for director+ audiences
- Reviewing existing dashboards for executive appropriateness
- Establishing dashboard standards for a new organizational rollup
- Demonstrating business observability value to leadership through concrete visualizations

**Related instruments:**

- [IN-15 Dashboard Generation Methodology](in-15-dashboard-generation-methodology.md) — executive patterns are a subset of the broader methodology
- [IN-11 Dashboard Factory](in-11-dashboard-factory.md) — the factory produces executive dashboard panels when configured for leadership audience
- [IN-20 Portfolio Maturity View](in-20-portfolio-maturity-view.md) — portfolio view is often presented alongside executive dashboards
