# IN-19 — Discovery Dialogue Protocol

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
    <td style="padding: 0.4em 0.9em;">Define</td>
  </tr>
</table>

---

## Purpose

A Platform Engineer sits down with a Product Owner to produce a service profile. The conversation needs structure — what to ask, in what order, how to probe for the right level of specificity, and how to translate the Product Owner's domain knowledge into structured business observability data. The Discovery Dialogue Protocol is a facilitation guide for this conversation.

**The conversation order is the motivation chain.** The current capture order follows the PO's reasoning path, not entity types: establish service context first, then walk one complete chain per stakeholder — who they are, what they expect, what signal measures each expectation — closing each chain with a coverage check (every expectation → a signal?) before moving to the next stakeholder. Impact, diagnostics, and infrastructure follow the chains. Eliciting expectations as one list and signals as another, then reconnecting them afterward, is the superseded sequence.

**Where the conversation sits:** when source material exists (architecture docs, Confluence, runbooks), capture is drafted from the sources and the conversation is *validation* — the PO confirms and corrects rather than dictating from scratch. The full facilitated dialogue is for the no-source case and for the chains only the PO's head holds.

## Inputs

- A service to profile (identified, named, with known organizational placement)
- Product Owner domain knowledge (the facilitator brings methodology; the Product Owner brings context)
- Existing documentation about the service (Confluence pages, Jira epics, architecture docs)

## Outputs

- **Structured service profile data** ready for entry into [IN-04](in-04-service-profile-template.md), [IN-05](in-05-signal-definition-template.md), [IN-06](in-06-stakeholder-expectation-template.md) templates
- **Stakeholder chains** — per stakeholder: expectations in sentence-template format with impact categories, each paired with the Business Health signal candidate that measures it (traceability comes from the chain, not from a later mapping exercise)
- **Business Impact signal candidates** — linked to the stakeholder concerns they assess
- **Open questions** — gaps the PO needs to follow up on with their team

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA01 — Business Context](../ka01-business-context.md) | This instrument facilitates [KA01](../ka01-business-context.md) knowledge capture — it's how business context gets extracted |
| [KA12 — Adoption & Enablement](../ka12-adoption-enablement.md) | Discovery dialogues are a core [KA12.1](../ka12-adoption-enablement.md#onboarding-first-experience) (Onboarding) activity |

## Usage Context

**When to reach for this instrument:**

- First-time service profiling — the principal engineer facilitates the PO's first service profile
- Complex services — where business context isn't obvious and requires structured exploration
- Cross-functional services — where multiple stakeholders need to contribute context

**Related instruments:**

- [IN-04 Service Profile Template](in-04-service-profile-template.md) — the dialogue produces data for this template
- [IN-06 Stakeholder Expectation Template](in-06-stakeholder-expectation-template.md) — the dialogue produces expectation rows
- [IN-16 Onboarding Simulation](in-16-onboarding-simulation.md) — the simulation incorporates discovery dialogue principles
- [IN-23 Observability Standard](in-23-observability-standard.md) — the definition of good the dialogue's record serves
- [IN-24 First-Process Run Plan](in-24-first-process-run-plan.md) — the run plan that places this dialogue inside a team's first working session
