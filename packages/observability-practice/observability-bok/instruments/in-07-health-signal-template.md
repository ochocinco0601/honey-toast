# IN-07 — Health Signal Template

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
    <td style="padding: 0.4em 0.9em;">Define → Implement</td>
  </tr>
</table>

---

## Purpose

A Developer asks "what exactly do I measure and how?" After the Product Owner defines what signals are needed ([IN-05](in-05-signal-definition-template.md)), the Developer and Platform Engineer enrich the same signal record with the measurement specifics — data source, queries, thresholds, and alerting parameters. This is where business intent becomes technical specification: one record, three contributors.

## Inputs

- Signal definitions with service-level objective (SLO) targets (from [IN-05](in-05-signal-definition-template.md))
- Available metric sources and telemetry infrastructure (Platform Engineer knowledge)
- Technical feasibility assessment from the Developer

## The record

The measurement-detail fields of the signal record — the Developer's and Platform Engineer's halves of the same row [IN-05](in-05-signal-definition-template.md) begins. Which fields apply follows the signal type:

| Field | Meaning | Filled by |
|-------|---------|-----------|
| `data_source_type` | Where the measurement comes from (metrics platform, log store, database query) | Developer |
| `query_numerator`, `query_denominator` | The two queries of a ratio signal (successes over attempts), each with a plain-language description field | Developer |
| `threshold_operator`, `threshold_value`, `threshold_unit` | The comparison of a threshold signal (e.g., `<`, 500, ms) | Developer |
| `query_builder` | How the query was authored, for maintainability | Developer |
| `technical_owner` | Who maintains the measurement | Developer |
| `sloTargetRationale`, `sloNotes` | Why the target is what it is | Developer + Product Owner |
| `timeWindowType`, `timeSliceTarget`, `timeSliceWindow` | Rolling vs. calendar windows and time-slice evaluation detail | Developer |
| `alertingThreshold`, `pageThreshold` | Burn-rate levels that raise an alert vs. page a human. The severity semantics — what warrants an alert vs. a page — are explicit Product Owner choices; Platform configures the values | Product Owner (severity choice) + Platform Engineer (configuration) |
| `health_warning_threshold`, `health_critical_threshold` | Where signal health turns warning and critical on dashboards. Ownership follows the layer: business judgment for the business layers, operational expertise for the mechanism layers | Product Owner (Business Health, Business Impact) / Developer-SRE (Application, System) |

Validation is type-conditional and runs at update time, not creation time — a ratio signal without its numerator is a stub awaiting enrichment, not an error.

## Outputs

- A signal record complete enough to implement: source, query, thresholds, and evaluation windows filled in
- Alerting parameters that the Alert Factory ([IN-12](in-12-alert-factory.md)) consumes to generate alert rules
- A signal-to-infrastructure mapping — which data sources serve each signal

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA02 — Signal Design](../ka02-signal-design.md) | This instrument records the measurement details; guidance for *choosing* an instrumentation approach is [KA02.3](../ka02-signal-design.md#instrumentation-strategy)'s territory |
| [KA06 — Platform & Tooling](../ka06-platform-tooling.md) | Metric sources and pipeline architecture determine what's measurable |

## Usage Context

**When to reach for this instrument:**

- After signal definitions exist ([IN-05](in-05-signal-definition-template.md)) — the Developer translates Product Owner intent into measurement details
- When migrating signals between monitoring platforms
- When optimizing signal performance (query efficiency, cardinality management)

**Related instruments:**

- [IN-05 Signal Definition Template](in-05-signal-definition-template.md) — provides the "what"; this instrument specifies the "how"
- [IN-09 Signal Specification Format](in-09-signal-specification-format.md) — feature-spec depth for complex signal behaviors
- [IN-12 Alert Factory](in-12-alert-factory.md) — consumes this template's output to generate alert rules
