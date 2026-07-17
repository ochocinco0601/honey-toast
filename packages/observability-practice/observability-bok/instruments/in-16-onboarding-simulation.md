# IN-16 — Onboarding Simulation

**Type:** Adoption
**State:** Current
**Lifecycle position:** Define (guides a Product Owner through their first service profile)

---

## Purpose

A team is adopting the observability practice for the first time. The Product Owner needs to create their first [service profile](in-04-service-profile-template.md), and the experience needs to be guided — not "read the documentation and figure it out." The Onboarding Simulation is an interactive, browser-based walkthrough that takes a Product Owner through service definition step by step, with friction logging built in to capture adoption pain points.

**Where this sits relative to production onboarding:** the simulation is the *training surface*, built on the earlier form-based onboarding tool. Its step order (entity by entity: basics → expectations → signals → impact → preview) predates the current production onboarding process, which walks the capture as motivation chains — one chain per stakeholder, layer assignment structural, traceability produced by the chain nesting, verification mandatory ([KA12.1](../ka12-adoption-enablement.md#onboarding-first-experience) describes the active process). The simulation still teaches the same capture content and the four-layer model through use; a PO who completes it should expect the production process to walk the same material in chain order.

## Inputs

- A service the Product Owner wants to start with (real or reference scenario)
- Product Owner domain knowledge of stakeholders and expectations
- Access to the simulation environment

## Outputs

- **A completed (or partially completed) service profile** — real output from the first session
- **Friction log entries** — structured capture of where the Product Owner got stuck, confused, or needed help (feeds [IN-18](in-18-friction-logging-protocol.md))
- **Product Owner confidence assessment** — can they do the next service independently?
- **Methodology feedback** — what worked, what needs adjustment

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA12 — Adoption & Enablement](../ka12-adoption-enablement.md) | This instrument is the primary [KA12.1](../ka12-adoption-enablement.md#onboarding-first-experience) (Onboarding) implementation |
| [KA01 — Business Context](../ka01-business-context.md) | The simulation teaches [KA01](../ka01-business-context.md)'s service-definition content; its form-step order predates the current chain-ordered workflow |

## Usage Context

**When to reach for this instrument:**
- Team's first engagement with the observability practice
- Pilot kickoffs — controlled environment for first-time practitioners
- Methodology validation — testing whether the workflow is learnable

**Related instruments:**
- [IN-18 Friction Logging Protocol](in-18-friction-logging-protocol.md) — captures pain points during the simulation
- [IN-17 Transfer Packages](in-17-transfer-packages.md) — the team takes this away after onboarding
- [IN-19 Discovery Dialogue Protocol](in-19-discovery-dialogue-protocol.md) — the conversation guide that structures the Product Owner interaction within the simulation
