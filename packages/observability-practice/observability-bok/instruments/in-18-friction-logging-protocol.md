# IN-18 — Friction Logging Protocol

<table style="border: 1px solid var(--md-typeset-table-color, #ddd); border-left: 4px solid var(--md-primary-fg-color, #673ab7); border-collapse: collapse; margin: 1em 0; font-size: 0.95em;">
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Type</th>
    <td style="padding: 0.4em 0.9em;">Adoption</td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">State</th>
    <td style="padding: 0.4em 0.9em;"><a href="index.html#content-state-key">Seeded</a></td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Lifecycle position</th>
    <td style="padding: 0.4em 0.9em;">Cross-cutting (captures adoption pain points at any stage)</td>
  </tr>
</table>

---

## Purpose

A team encounters friction during onboarding or ongoing practice execution — confusing templates, unclear guidance, tool limitations, process bottlenecks. The Friction Logging Protocol provides a structured format for capturing these pain points in real time, so they feed methodology improvement rather than being lost as anecdotal complaints.

## Inputs

- Practitioner experience during any adoption activity (onboarding, pilot, first service, scaling)
- Observer notes (if a facilitator is present)
- Timestamp and context (which step, which instrument, which service)

## Outputs

- **Structured friction entries** — what happened, where, severity, category (methodology / tooling / knowledge gap / process)
- **Pattern analysis** — recurring friction points across teams and sessions
- **Improvement backlog** — friction entries prioritized by frequency and severity, feeding [KA13](../ka13-continuous-improvement.md) improvement cycles

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA12 — Adoption & Enablement](../ka12-adoption-enablement.md) | Friction logging is part of [KA12.3](../ka12-adoption-enablement.md#pilot-design-execution) (Pilot Design) — every pilot includes it |
| [KA13 — Continuous Improvement](../ka13-continuous-improvement.md) | Friction data feeds [KA13.3](../ka13-continuous-improvement.md#lessons-learned-knowledge-capture) (Lessons Learned) and [KA13.5](../ka13-continuous-improvement.md#evolution-adaptation) (Evolution) |

## Usage Context

**When to reach for this instrument:**

- During onboarding simulation ([IN-16](in-16-onboarding-simulation.md)) — built into the experience
- During pilot execution — facilitator logs friction alongside participants
- During any "first time" experience with an instrument or workflow
- Post-incident — when incident response reveals methodology friction

**Related instruments:**

- [IN-16 Onboarding Simulation](in-16-onboarding-simulation.md) — friction logging is embedded in the simulation
- [IN-19 Discovery Dialogue Protocol](in-19-discovery-dialogue-protocol.md) — friction during discovery dialogues is a common capture point
