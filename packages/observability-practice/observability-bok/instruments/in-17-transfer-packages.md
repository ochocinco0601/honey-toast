# IN-17 — Transfer Packages

**Type:** Adoption

**State:** Seeded

**Lifecycle position:** Cross-cutting (enables teams to run the practice independently)

---

## Purpose

A team has completed onboarding and needs to run the practice without the practice lead in the room. Transfer Packages are self-contained artifact bundles — templates, guidance, examples, and AI agent configurations — that make adoption portable across lines of business (LOBs) and teams.

The package is the *enablement surface* of franchise-shaped adoption, not a standalone instance: the adopting team learns the practices and owns its inputs, but its service profiles still flow through the shared production capability, and its definitions are validated against the spec before its services go live ([KA12](../ka12-adoption-enablement.md#scaling-patterns) carries the adoption architecture). "Give each LOB their own packaged instance to run locally" is a common misreading of what a transfer package is for.

## Inputs

- Methodology artifacts (service profile templates, signal definitions, stakeholder guidance)
- Team-specific configuration (org hierarchy data, relevant reference scenarios)
- AI agent setup instructions (for enterprise Copilot-style integration)

## Outputs

- **Self-contained artifact bundle** — everything a team needs to adopt the practice
- **AI agent configuration** — setup instructions the receiving AI agent reads and executes (SETUP.md pattern)
- **Reference examples** — completed service profiles from similar services the team can model from
- **LOB-portable packaging** — generic enough to work across organizational boundaries

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA12 — Adoption & Enablement](../ka12-adoption-enablement.md) | This instrument is the primary [KA12.2](../ka12-adoption-enablement.md#transfer-packages-enablement-kits) (Transfer Packages) implementation |

## Usage Context

**When to reach for this instrument:**

- After onboarding ([IN-16](in-16-onboarding-simulation.md)) — the team takes this away
- Scaling to a new LOB — package adapted for the target organization
- Air-gap transfer — self-contained bundles that work across organizational boundaries

**Related instruments:**

- [IN-16 Onboarding Simulation](in-16-onboarding-simulation.md) — the onboarding experience that precedes package handoff
- [IN-04 Service Profile Template](in-04-service-profile-template.md) — included in the package as the primary template
