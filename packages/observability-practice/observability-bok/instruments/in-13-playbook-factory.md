# IN-13 — Playbook Factory

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
    <td style="padding: 0.4em 0.9em;">Respond</td>
  </tr>
</table>

---

## Purpose

The Playbook Factory turns service context and signal patterns into incident response procedures. A factory here is a generation procedure — implementable as deterministic tooling or an AI-executed method. Teams that write playbooks by hand produce inconsistent artifacts — some are detailed, some are outdated, some exist for one alert pattern but not the adjacent one. The factory pattern inverts this: service profile data plus signal definitions produce a validated playbook for every alert that can fire.

## Inputs

- Service profile — stakeholders, impact categories, tier, owners (shapes triage priority)
- Signal definitions — what fired, what it measures, what it means for the business
- Ownership model — who owns the signal, who escalates, who approves remediation
- Playbook template structure — standard sections for triage, investigation, remediation, communication
- Signal-to-playbook mapping — which signal patterns trigger which playbook sections

## Outputs

- Structured playbooks with consistent sections across services
- Service-context headers — who's impacted, what's at stake, whose expectation is breached
- Triage steps derived from signal type, impact category, and the cross-layer correlation pattern the alert scenario matches — the responder's starting point for diagnosis
- Escalation paths from ownership and organizational structure
- Communication templates pre-populated with stakeholder names and impact category language
- Linkage from every alert to the playbook that covers its response

## Generation Approach

1. Identify the signal pattern (which signal, which threshold, which layer)
2. Read the service profile for stakeholder impact and ownership
3. Apply the playbook template — populate sections from service context
4. Inject triage logic from signal type (ratio vs threshold, leading vs lagging) and from the named cross-layer correlation patterns ([KA04](../ka04-monitoring-visualization.md#cross-signal-correlation)) — the triage section opens with which pattern is in play: Silent Business Failure → business-domain investigation; Infrastructure Cascade → infrastructure root cause; Infrastructure Noise → monitor, don't escalate
5. Resolve escalation path from ownership model
6. Generate stakeholder communication templates with impact category language
7. Validate — every signal with a threshold has a playbook; every playbook references a valid owner; every playbook includes a communication section

## Design Principles

- **Context before procedure.** A playbook that starts with "check the logs" loses the responder. A playbook that starts with "Mortgage applicants cannot complete purchase — homebuyers on scheduled closing date, regulatory deadline at risk" centers the response on what matters.
- **Triage follows business impact.** Playbooks for tier-1 revenue-critical services trigger different response timelines than tier-6 internal tools. The factory encodes this from the service profile, not responder judgment.
- **Communication is part of response.** A playbook without stakeholder communication templates leaves the hardest question ("what do we tell customers?") to be answered under pressure.
- **Playbooks evolve with signals.** When a signal definition changes, the playbook regenerates. No orphaned playbooks referencing thresholds that no longer exist.

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA05 — Incident Management](../ka05-incident-response.md) | This instrument produces [KA05.3](../ka05-incident-response.md#playbook-design-execution) (Playbook Design & Execution) artifacts |
| [KA01 — Business Context](../ka01-business-context.md) | Service context determines playbook content — who to notify, what's at stake |
| [KA02 — Signal Design](../ka02-signal-design.md) | Signal patterns drive triage steps and investigation order |

## Related Instruments

- [IN-12 Alert Factory](in-12-alert-factory.md) — alerts trigger playbook execution; playbooks are linked from alert configurations
- [IN-06 Stakeholder Expectation Template](in-06-stakeholder-expectation-template.md) — stakeholder impact drives triage priority in playbooks
