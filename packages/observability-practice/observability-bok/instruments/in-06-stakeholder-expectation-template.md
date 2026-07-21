# IN-06 — Stakeholder Expectation Template

**Type:** Definition

**State:** Current

**Lifecycle position:** Define

---

## Purpose

A Product Owner asks "how do I capture who cares about this service and what they need?" This template captures stakeholder expectations — 3-5 rows per service, each one a complete story: "As [stakeholder], I expect [X]. If broken: [impact]." The forced prioritization (3-5, not unlimited) ensures the Product Owner decides what matters most.

## Inputs

- Registered service (from [IN-04](in-04-service-profile-template.md))
- Product Owner domain knowledge of stakeholders and their expectations
- AI-assisted pre-population from existing documentation (optional — accelerates first draft)

## The record

One row per expectation. Fields:

| Field | Meaning | Required |
|-------|---------|----------|
| `context_id` | Unique identifier (e.g., CTX001) | Yes |
| `service_id` | The service this expectation belongs to (from [IN-04](in-04-service-profile-template.md)) | Yes |
| `stakeholder` | Who cares — free-form description (e.g., Mortgage Applicants) | Yes |
| `expectationStatement` | What they expect, in their words | Yes |
| `impactCategory` | One of: customer_experience, financial, legal_risk, operational | Yes |
| `impactDescription` | The consequence if the expectation breaks, prefixed with its category for parsing (e.g., "Financial Impact: closing delays") | Yes |
| `priority` | CRITICAL, HIGH, MEDIUM, or LOW | Yes |
| `created_by`, `modified_by` | Audit trail | Auto-generated |

**Worked example** — one expectation on a tier-1 funding service:

| Field | Value |
|-------|-------|
| `stakeholder` | Mortgage Applicants |
| `expectationStatement` | Closing funds available on the scheduled closing date |
| `impactCategory` | financial |
| `impactDescription` | Financial Impact: closing delays for home purchases |
| `priority` | CRITICAL |

## Outputs

- 3-5 completed expectation records per service — the expectations that signal definitions ([IN-05](in-05-signal-definition-template.md)) measure
- **Impact classification** — consequences categorized and described in a form that Business Impact signals quantify
- Impact descriptions written here provide the content executive dashboard tiles render — a downstream consequence worth writing them for

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA01 — Business Context](../ka01-business-context.md) | This instrument captures [KA01.1](../ka01-business-context.md#stakeholder-identification-expectations) (Stakeholder Identification) and [KA01.4](../ka01-business-context.md#impact-category-classification) (Impact Classification) |
| [KA05 — Incident Response](../ka05-incident-response.md) | Stakeholder expectations determine incident severity and triage priority |
| [KA10 — Stakeholder Engagement](../ka10-stakeholder-engagement.md) | Expectation capture is a structured form of stakeholder engagement |

## Usage Context

**When to reach for this instrument:**

- Immediately after service registration ([IN-04](in-04-service-profile-template.md)) — this is the Product Owner's next action
- During discovery dialogues ([IN-19](in-19-discovery-dialogue-protocol.md)) — the conversation produces expectation rows
- When stakeholder needs change — expectations are evergreen, updated when the business changes

**Related instruments:**

- [IN-04 Service Profile Template](in-04-service-profile-template.md) — service must exist before expectations can be captured
- [IN-05 Signal Definition Template](in-05-signal-definition-template.md) — signals measure whether expectations are met
- [IN-19 Discovery Dialogue Protocol](in-19-discovery-dialogue-protocol.md) — the facilitation guide for the conversation that produces these rows
- [IN-01 Service Maturity Model](in-01-service-maturity-model.md) — completing expectations moves a service toward Contextualized
- [IN-23 Observability Standard](in-23-observability-standard.md) — expectations fill the top positions of the standard's chain
