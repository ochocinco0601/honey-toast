# IN-09 — Signal Specification Format

**Type:** Definition
**State:** Current
**Lifecycle position:** Define → Implement

---

## Purpose

A Developer or Platform Engineer needs spec-level detail for signal behavior beyond what the record templates ([IN-05](in-05-signal-definition-template.md), [IN-07](in-07-health-signal-template.md)) capture — the full definition of how a signal type behaves, validates, and gets tested. This page defines the format of such a specification: the sections a complete signal spec contains, so a team can write one for any signal type it introduces.

## Inputs

- The signal record templates in use ([IN-05](in-05-signal-definition-template.md), [IN-07](in-07-health-signal-template.md)) — the spec explains and validates what they capture
- The four-layer model and signal type taxonomy ([KA02](../ka02-signal-design.md) — the domain source for signal design knowledge)
- The three-actor ownership model (Product Owner defines, Developer implements, Platform operates)

## The format

A complete signal specification carries six sections:

| Section | What it contains |
|---------|-----------------|
| Business context | Which stakeholder expectations the signal type serves; the layer it lives on |
| Type definition | The signal type's discriminator value and where it fits the taxonomy (`sli_ratio`, `sli_threshold`, `business_impact`) |
| Data model | The type's fields, including which are type-specific (ratio: numerator/denominator queries; threshold: operator, value, unit) |
| Ownership | Which actor fills which fields, per the three-actor model |
| Business rules | Lifecycle and behavior rules — when the signal validates, what makes it complete, what state changes mean |
| Acceptance scenarios | Behavior-driven development (BDD) scenarios — given/when/then cases a correct implementation must pass |

## Outputs

- A written specification for each signal type the practice uses — the validation and testing authority the record templates implement in simplified form
- **Validation criteria** — what makes a signal definition complete and correct, testable per acceptance scenario

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA02 — Signal Design](../ka02-signal-design.md) | [KA02](../ka02-signal-design.md) owns the signal design knowledge (taxonomy, ownership model, validation approach); this format packages it per signal type |
| [KA01 — Business Context](../ka01-business-context.md) | Signal specs enforce business context requirements — every signal must trace to a stakeholder expectation |

## Usage Context

**When to reach for this instrument:**
- Introducing or modifying a signal type — write its spec in this format before changing the data model
- Onboarding developers who need signal behavior beyond the record-template level
- Resolving questions about signal ownership, lifecycle, or behavior rules

**Related instruments:**
- [IN-05 Signal Definition Template](in-05-signal-definition-template.md) — the record view a spec explains and validates
- [IN-07 Health Signal Template](in-07-health-signal-template.md) — measurement details that implement a spec's requirements
