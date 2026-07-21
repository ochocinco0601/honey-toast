# IN-12 — Alert Factory

**Type:** Production

**State:** Seeded

**Lifecycle position:** Observe → Respond

---

## Purpose

The Alert Factory turns signal definitions into alert configurations. A factory here is a generation procedure — implementable as deterministic tooling or an AI-executed method. A platform team defining alerts manually per signal produces inconsistency — severity mappings drift, routing rules duplicate, escalation patterns diverge across services. The factory pattern inverts this: one signal definition produces a validated alert configuration that conforms to enterprise standards.

## Inputs

- Signal definitions — thresholds, burn rates, measurement windows
- Service profile — ownership (who receives the alert), impact category (how severe)
- Stakeholder expectations — which expectations a signal serves (drives routing priority)
- Severity-mapping rules — how service-level objective (SLO) burn rates translate to alert severity levels
- Notification-routing policy — role-based targets (Product Owner, Developer on-call, Platform, Leadership)
- Playbook references (from [IN-13](in-13-playbook-factory.md)) — the playbook covering each alert's response, feeding the alert-to-playbook linkage

## Outputs

- Alert configurations in the target platform's format (PagerDuty, BigPanda, native platform alerting)
- Severity assignments consistent with signal impact category and burn rate
- Routing rules tied to service ownership, not hand-coded per alert
- Escalation timing derived from impact severity, not improvised per alert
- Generated linkage from each alert to the playbook covering the response

## Generation Approach

1. Read signal definition (threshold, time window, measurement method)
2. Look up service profile for ownership and impact category
3. Apply severity-mapping rules (e.g., `burn_rate > 14.4x` → P1; `burn_rate > 2x sustained` → P3)
4. Resolve routing from service ownership table
5. Attach cross-layer context — alert logic accounts for the state of the other layers, per the named correlation patterns ([KA04](../ka04-monitoring-visualization.md#cross-signal-correlation)): suppress or downgrade a mechanism-layer alert when Business Health is green (Infrastructure Noise), escalate when degradation propagates (Infrastructure Cascade)
6. Emit platform-specific configuration (YAML, JSON, Terraform, API call)
7. Validate output — every signal with an SLO target produces at least one alert; every alert references a valid owner; severity is bounded by impact category

## Design Principles

- **No alert without a signal definition.** Ad-hoc alerts bypass the business-context chain and erode signal trust.
- **No alert without a playbook reference.** An alert that fires without structured response guidance is noise waiting to happen.
- **Severity follows business impact, not technical severity.** A disk-full alert on a tier-1 revenue-critical service is higher severity than a disk-full alert on a tier-6 internal tool — even though the technical condition is identical.
- **Routing follows ownership, not expertise.** Platform teams receive platform alerts. Service owners receive service alerts. Don't route service alerts to the platform team because "they know how to fix things."
- **No layer alerts alone.** A per-signal alert that ignores the other layers mass-produces exactly the false urgency (System red, business fine) and false silence (everything green but the outcome failing) the methodology exists to eliminate. The cross-layer combination is the decision surface; generated alert logic carries it.

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA04 — Monitoring & Visualization](../ka04-monitoring-visualization.md) | Alert rules are part of real-time monitoring ([KA04.2](../ka04-monitoring-visualization.md#real-time-monitoring)) |
| [KA05 — Incident Management](../ka05-incident-response.md) | Alerts trigger incident response — alert quality determines response quality |
| [KA02 — Signal Design](../ka02-signal-design.md) | Signal thresholds and burn rates are the primary factory input |

## Related Instruments

- [IN-07 Health Signal Template](in-07-health-signal-template.md) — provides threshold values and alert parameters
- [IN-13 Playbook Factory](in-13-playbook-factory.md) — alerts link to the playbooks that guide response
