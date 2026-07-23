# IN-01 — Service Maturity Model

<table style="border: 1px solid var(--md-typeset-table-color, #ddd); border-left: 4px solid var(--md-primary-fg-color, #673ab7); border-collapse: collapse; margin: 1em 0; font-size: 0.95em;">
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Type</th>
    <td style="padding: 0.4em 0.9em;">Assessment</td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">State</th>
    <td style="padding: 0.4em 0.9em;"><a href="index.html#content-state-key">Current</a></td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Lifecycle position</th>
    <td style="padding: 0.4em 0.9em;">Spans Define → Observe</td>
  </tr>
</table>

---

## Purpose

A practitioner asks "how far along is this service?" or an executive asks "where is our portfolio?" This instrument provides the answer — a 4-stage progression that measures how much of the observability lifecycle has been applied to each service.

## The Four Stages

| Stage | What it means | Who did the work | Lifecycle coverage |
|-------|--------------|------------------|-------------------|
| **Identified** | Service exists on the map — name, purpose, organizational placement captured | Governance / Registry | Pre-lifecycle (service is known but no observability work has been done) |
| **Contextualized** | Product Owner has defined stakeholder expectations, impact categories, and service-level objective (SLO) targets | Product Owner | Define ([KA01](../ka01-business-context.md) complete) |
| **Instrumented** | Developer has implemented signals, mapped telemetry, and signals are live | Developer | Define + Implement ([KA01](../ka01-business-context.md) + [KA02](../ka02-signal-design.md) complete) |
| **Operationalized** | Signals are in production use — alerts firing, dashboards consumed, validated through incident response | Platform / SRE | Define + Implement + Enforce + Observe ([KA01](../ka01-business-context.md) through [KA04](../ka04-monitoring-visualization.md) engaged) |

Each stage requires the previous — a service cannot be Instrumented without being Contextualized first, because signal design depends on business context.

## Inputs

- Service registry or configuration management database (CMDB) inventory (for Identified count)
- Service profile completeness data (for Contextualized assessment)
- Signal implementation status (for Instrumented assessment)
- Production operational state — live dashboards, active alerts, incident history (for Operationalized assessment)

## Outputs

- **Per-service stage assignment** — where each service sits on the 4-stage progression
- **Portfolio distribution** — count and percentage of services at each stage, by product line
- **Stage transition tracking** — services that moved stages in the current period
- **Blocker analysis** — what's preventing services from advancing to the next stage

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA01 — Business Context](../ka01-business-context.md) | Contextualized stage = [KA01](../ka01-business-context.md) knowledge applied |
| [KA02 — Signal Design](../ka02-signal-design.md) | Instrumented stage = [KA02](../ka02-signal-design.md) knowledge applied |
| [KA03 — Standards & Quality](../ka03-standards-quality.md) | Operationalized stage requires [KA03](../ka03-standards-quality.md) enforcement |
| [KA04 — Monitoring & Visualization](../ka04-monitoring-visualization.md) | Operationalized stage requires [KA04](../ka04-monitoring-visualization.md) dashboards and alerts active |
| [KA09 — Strategy & Program](../ka09-strategy-program.md) | Portfolio distribution informs strategic prioritization |
| [KA13 — Continuous Improvement](../ka13-continuous-improvement.md) | Stage transitions are a key practice metric |

## Usage Context

**When to reach for this instrument:**

- Quarterly portfolio reviews — "show me where we are"
- Objectives-and-key-results (OKR) reporting — stage transitions as a key result
- Stakeholder communications — demonstrating adoption progress
- Adoption planning — identifying where services are stuck and what would unblock them

**Related instruments:**

- [IN-03 Division Maturity Assessment](in-03-division-maturity-assessment.md) — uses the service maturity model as one input dimension
- [IN-20 Portfolio Maturity View](in-20-portfolio-maturity-view.md) — the communication instrument that visualizes this assessment's output
- [IN-23 Observability Standard](in-23-observability-standard.md) — the definition of good; its filled chain positions are what the maturity stages translate
