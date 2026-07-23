# Practice Instruments Catalog

**What this is:** The concrete tools, templates, assessments, and models that practitioners pick up and use. Where the [Knowledge Areas](../) explain what you need to *understand*, this catalog shows what you can *do*.

This is the **Act** axis of the BOK. See [How the BOK is Organized](../how-the-bok-is-organized.md) for the full mental model.

**Pattern:** Adapted from BABOK v3 Techniques Chapter (IIBA) — instruments cataloged independently from Knowledge Areas, cross-referenced bidirectionally.

**How to use this catalog:**

- **PO looking for "what do I fill out?"** → Browse [Definition Instruments](#definition-instruments)
- **A principal engineer measuring portfolio state** → Browse [Assessment Instruments](#assessment-instruments)
- **Platform lead setting up production artifacts** → Browse [Production Instruments](#production-instruments)
- **Team onboarding to the practice** → Browse [Adoption Instruments](#adoption-instruments)
- **Preparing stakeholder communications** → Browse [Communication Instruments](#communication-instruments)

**Content state key:** **C** = Current (documented, usable) | **S** = Seeded (concept exists, not fully built) | **M** = Missing

---

## Assessment Instruments

Measurement and evaluation — "where are we?"

| ID | Instrument | Purpose | State |
|----|-----------|---------|-------|
| [IN-01](in-01-service-maturity-model.md) | Service Maturity Model | Measure how far each service has progressed through the observability lifecycle | **C** |
| [IN-02](in-02-industry-maturity-arc.md) | Industry Maturity Arc | Position the organization's observability capability against the industry 5-stage arc | **S** |
| [IN-03](in-03-division-maturity-assessment.md) | Division Maturity Assessment | Assess observability maturity across a technology division using two dimensions | **S** |

## Definition Instruments

Capture and specification — "what do I fill out?"

| ID | Instrument | Purpose | State |
|----|-----------|---------|-------|
| [IN-04](in-04-service-profile-template.md) | Service Profile Template | Capture a service's identity, business purpose, tier, and organizational placement | **C** |
| [IN-05](in-05-signal-definition-template.md) | Signal Definition Template | Define signals across the four layers, with SLO targets, formulas, and ownership | **C** |
| [IN-06](in-06-stakeholder-expectation-template.md) | Stakeholder Expectation Template | Capture who cares about a service and what happens when it fails them | **C** |
| [IN-07](in-07-health-signal-template.md) | Health Signal Template | Define signal measurement details — metric source, formula, threshold, time window | **C** |
| [IN-08](in-08-service-status-template.md) | Service Status Template | Track operational readiness — dashboard URLs, runbook links, alert targets, evaluation scores | **C** |
| [IN-09](in-09-signal-specification-format.md) | Signal Specification Format | Specify signal behavior at feature-spec depth — types, ownership model, data model | **C** |
| [IN-23](in-23-observability-standard.md) | Observability Standard (One Content, Three Forms) | The written definition of what good looks like — canonical signals per layer, chain positions, computation rule — rendered as model (teaches), record (captures), test (verifies) | **C** |

## Production Instruments

Artifact generation — "what gets produced?"

| ID | Instrument | Purpose | State |
|----|-----------|---------|-------|
| [IN-10](in-10-story-factory.md) | Story Factory | Generate user stories from service profiles and signal definitions | **S** |
| [IN-11](in-11-dashboard-factory.md) | Dashboard Factory | Generate monitoring dashboards from service profile and signal data | **S** |
| [IN-12](in-12-alert-factory.md) | Alert Factory | Generate alert rules from signal thresholds and escalation policies | **S** |
| [IN-13](in-13-playbook-factory.md) | Playbook Factory | Generate incident response playbooks from service context and signal patterns | **S** |
| [IN-14](in-14-documentation-factory.md) | Documentation Factory | Generate stakeholder documentation from service profiles and operational data | **S** |
| [IN-15](in-15-dashboard-generation-methodology.md) | Dashboard Generation Methodology | Systematic approach to producing dashboards — styling, layout, data binding, validation | **S** |

## Adoption Instruments

Onboarding and scaling — "how do teams get started?"

| ID | Instrument | Purpose | State |
|----|-----------|---------|-------|
| [IN-16](in-16-onboarding-simulation.md) | Onboarding Simulation | Guided walkthrough of a PO's first service profile — interactive, with friction logging | **C** |
| [IN-17](in-17-transfer-packages.md) | Transfer Packages | Self-contained artifact bundles teams adopt to run the practice independently | **S** |
| [IN-18](in-18-friction-logging-protocol.md) | Friction Logging Protocol | Structured capture of adoption pain points during pilot and onboarding | **S** |
| [IN-19](in-19-discovery-dialogue-protocol.md) | Discovery Dialogue Protocol | Facilitation guide for the PO conversation that produces a service profile | **S** |
| [IN-24](in-24-first-process-run-plan.md) | First-Process Run Plan | The executable path for a team's first process — prep, the facilitated session, measurement and response wiring, repeat | **S** |

## Communication Instruments

Stakeholder visibility — "how do we show progress?"

| ID | Instrument | Purpose | State |
|----|-----------|---------|-------|
| [IN-20](in-20-portfolio-maturity-view.md) | Portfolio Maturity View | Executive visualization of service progression across the portfolio | **C** |
| [IN-21](in-21-terrain-presentation.md) | Terrain Presentation | Stakeholder communication that maps observability needs to lifecycle stages | **S** |
| [IN-22](in-22-executive-dashboard-patterns.md) | Executive Dashboard Patterns | Design patterns for executive-level observability dashboards | **C** |

---

---

## Relationship to Knowledge Areas

Instruments are **peers** of Knowledge Areas, not children. Where KAs organize by domain topic (13 areas, 73 topics), instruments organize by practitioner action (5 types, 24 instruments). Navigation flows both directions:

- **KA → Instruments:** Each KA page's Section 5 lists which instruments operationalize that knowledge
- **Instruments → KAs:** Each instrument page lists which KAs it draws knowledge from

An instrument that spans several KAs (the service maturity model, [IN-01](in-01-service-maturity-model.md), draws from six) appears in each of those KA pages — a single catalog entry referenced from multiple locations.
