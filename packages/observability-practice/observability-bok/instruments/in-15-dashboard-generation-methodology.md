# IN-15 — Dashboard Generation Methodology

<table style="border: 1px solid var(--md-typeset-table-color, #ddd); border-left: 4px solid var(--md-primary-fg-color, #673ab7); border-collapse: collapse; margin: 1em 0; font-size: 0.95em;">
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Type</th>
    <td style="padding: 0.4em 0.9em;">Production</td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">State</th>
    <td style="padding: 0.4em 0.9em;"><a href="index.html#content-state-key">Seeded</a></td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Lifecycle position</th>
    <td style="padding: 0.4em 0.9em;">Observe</td>
  </tr>
</table>

---

## Purpose

A platform team needs to produce dashboards that follow consistent standards — styling, layout patterns, data binding conventions, business display rules, and executive design principles. This methodology governs how dashboards are built, whether manually or through the Dashboard Factory ([IN-11](in-11-dashboard-factory.md)).

## Inputs

- Dashboard styling standards (color palettes, typography, component patterns)
- Layout rules (business-first rendering: Business Health at top, Business Impact tiles, Application- and System-layer panels at bottom)
- Data binding conventions (signal-to-panel mapping, threshold visualization)
- Executive design principles (altitude-appropriate views, stakeholder framing)

## Outputs

- **Consistent dashboard standards** across all services and teams
- **Generation rules** that [IN-11](in-11-dashboard-factory.md) (Dashboard Factory) follows
- **Review criteria** for validating manually-built dashboards against the methodology
- **Enterprise deployment patterns** for dashboards within a consolidated visualization platform

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA04 — Monitoring & Visualization](../ka04-monitoring-visualization.md) | This instrument codifies [KA04.1](../ka04-monitoring-visualization.md#dashboard-design-standards) (Dashboard Design & Standards) |
| [KA03 — Standards & Quality](../ka03-standards-quality.md) | Dashboard standards are part of the broader quality framework |

## Usage Context

**When to reach for this instrument:**

- Building new dashboards — follow the methodology for consistency
- Reviewing existing dashboards — validate against the methodology
- Updating dashboard standards — changes land in this methodology so factory output and manual builds stay aligned
- Training teams on dashboard creation

**Related instruments:**

- [IN-11 Dashboard Factory](in-11-dashboard-factory.md) — the factory that applies this methodology
- [IN-22 Executive Dashboard Patterns](in-22-executive-dashboard-patterns.md) — executive-specific design patterns within this methodology
