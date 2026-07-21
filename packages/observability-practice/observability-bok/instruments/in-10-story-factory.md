# IN-10 — Story Factory

**Type:** Production

**State:** Seeded

**Lifecycle position:** Define → Implement (bridges business context to development work)

---

## Purpose

A Product Owner has completed a service profile with stakeholder expectations and signal definitions. The team needs user stories to plan implementation work. The Story Factory turns the profile data into structured user stories — a factory here is a generation procedure, implementable as deterministic tooling or an AI-executed method, so one Product Owner action produces development-ready stories without manual story writing.

## Inputs

- Completed service profile (from [IN-04](in-04-service-profile-template.md))
- Stakeholder expectations (from [IN-06](in-06-stakeholder-expectation-template.md))
- Signal definitions (from [IN-05](in-05-signal-definition-template.md))

## Outputs

- **User stories organized by actor and layer** — Product Owner stories for enriching the Business Health and Business Impact definitions the profile stubs (targets, rationale, severity choices — progressive-enrichment work, not re-defining what the input already carries), Developer stories for Application-layer implementation, Platform stories for System-layer configuration
- **Acceptance criteria** — derived from service-level objective (SLO) targets, signal specifications, and stakeholder expectations
- **Story-to-signal traceability** — every story traces to the signal or expectation it implements

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA01 — Business Context](../ka01-business-context.md) | Consumes service profile and expectation data to generate stories |
| [KA02 — Signal Design](../ka02-signal-design.md) | Signal definitions drive Developer story content |

## Usage Context

**When to reach for this instrument:**

- Sprint planning — generating implementation stories from service profiles
- Backlog creation — producing the initial set of observability stories for a service
- Validation — checking that all signals and expectations have corresponding implementation stories

**Related instruments:**

- [IN-04 Service Profile Template](in-04-service-profile-template.md) — primary input
- [IN-05 Signal Definition Template](in-05-signal-definition-template.md) — signal inputs
- [IN-06 Stakeholder Expectation Template](in-06-stakeholder-expectation-template.md) — expectation inputs
