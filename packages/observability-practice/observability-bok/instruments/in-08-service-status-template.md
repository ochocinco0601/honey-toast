# IN-08 — Service Status Template

<table style="border: 1px solid var(--md-typeset-table-color, #ddd); border-left: 4px solid var(--md-primary-fg-color, #673ab7); border-collapse: collapse; margin: 1em 0; font-size: 0.95em;">
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Type</th>
    <td style="padding: 0.4em 0.9em;">Definition</td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">State</th>
    <td style="padding: 0.4em 0.9em;"><a href="index.html#content-state-key">Current</a></td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Lifecycle position</th>
    <td style="padding: 0.4em 0.9em;">Enforce → Observe</td>
  </tr>
</table>

---

## Purpose

A platform lead asks "is this service production-ready for observability?" This instrument is two things deliberately bundled: a record you fill in — the operational infrastructure that must be in place for observability to function — and an evaluation the system computes from the whole service definition. The record tracks operational configuration; the score measures overall definition completeness.

## Inputs

- Service profile (from [IN-04](in-04-service-profile-template.md)) and signal definitions (from [IN-05](in-05-signal-definition-template.md))
- Dashboard URLs (once built via [IN-11](in-11-dashboard-factory.md)/[IN-15](in-15-dashboard-generation-methodology.md))
- Runbook/playbook URLs (once built via [IN-13](in-13-playbook-factory.md))
- Alert notification channel configuration and escalation policy assignments

## The record

One row per service — the fill-in half:

| Field | Meaning | Required |
|-------|---------|----------|
| `service_id` | The service this configuration belongs to (from [IN-04](in-04-service-profile-template.md)) | Yes |
| `dashboardUrl` | Where the service's dashboard lives | Yes |
| `runbookUrl` | Where responders find the runbook/playbook | Yes |
| `alertNotificationTargets` | Who alerts notify (channels, roles) | Yes |
| `alertingConfigured` | Whether alerting is live for this service | Yes |
| `lastValidated`, `reviewDate` | When the configuration was last checked and when it is next due | No |
| `status`, `notes` | Lifecycle status and free-form operational notes | No |
| `created_by`, `modified_by` | Audit trail | Auto-generated |

## Outputs

- **Operational readiness record** — dashboard, runbook, alert targets, and escalation per service
- **Service Status evaluation score** (0-100) — computed on every access, never stored, across five dimensions ([KA03.1](../ka03-standards-quality.md) is the single source for definitions and weights):

  | Dimension | Weight | What it measures |
  |-----------|--------|-----------------|
  | Layer Coverage | 20% | Does the service have signals across all [four layers](../the-methodology.md)? |
  | Signal Completeness | 30% | For each signal, are required fields filled? |
  | Threshold Coverage | 15% | Do health signals have alert/page thresholds? |
  | Traceability Coverage | 20% | Does every stakeholder have at least one linked signal? |
  | Operational Readiness | 15% | Are dashboard, runbook, alert targets, and escalation defined? |

- **Gap identification** — which dimensions are incomplete

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA03 — Standards & Quality](../ka03-standards-quality.md) | The evaluation score is the primary quality gate — [KA03.1](../ka03-standards-quality.md#quality-gates-pipeline-integration) (Quality Gates & Pipeline Integration); the readiness record fills [KA03.2](../ka03-standards-quality.md#observability-readiness-criteria)'s (Observability Readiness Criteria) checklist |
| [KA06 — Platform & Tooling](../ka06-platform-tooling.md) | Operational infrastructure (dashboards, alerts) is platform-provided |

## Usage Context

**When to reach for this instrument:**

- Before declaring a service "production-ready" for observability
- During periodic service health reviews
- When an incident reveals operational gaps (missing runbook, misconfigured alerts)

**Related instruments:**

- [IN-04 Service Profile Template](in-04-service-profile-template.md) — the service must exist
- [IN-05 Signal Definition Template](in-05-signal-definition-template.md) — signal definitions drive four of the five score dimensions
- [IN-01 Service Maturity Model](in-01-service-maturity-model.md) — a complete Service Status evaluation contributes to reaching Operationalized stage
