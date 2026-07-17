# IN-05 — Signal Definition Template

**Type:** Definition
**State:** Current
**Lifecycle position:** Define → Implement

---

## Purpose

A Product Owner has defined a service and its stakeholder expectations. Now: "what signals will measure whether we're meeting those expectations?" This template captures signal definitions across the four layers (System, Application, Business Health, Business Impact) — each layer in its chain position: a **Business Health** signal measures each expectation; **Application** and **System** signals support and explain the Business Health signals (they link causally to what they help explain, not directly to expectations); a **Business Impact** signal quantifies the consequence when an expectation breaches.

## Inputs

- Registered service (from [IN-04](in-04-service-profile-template.md))
- Stakeholder expectations with impact categories (from [IN-06](in-06-stakeholder-expectation-template.md))
- Product Owner domain knowledge of what "healthy" looks like for this service
- Developer input on measurement feasibility

## The record

One row per signal. Core fields:

| Field | Meaning | Required |
|-------|---------|----------|
| `signal_id` | Unique identifier (e.g., SIG001) | Yes |
| `service_id` | The service this signal measures (from [IN-04](in-04-service-profile-template.md)) | Yes |
| `signal_name` | Technical name (e.g., funding-success-rate) | Yes |
| `signal_display_name` | Human-readable name for dashboards | Yes |
| `signal_type` | `sli_ratio`, `sli_threshold`, or `business_impact` | Yes |
| `observability_layer` | One of the four layers: System, Application, Business Health, Business Impact. **Structural, not chosen:** the layer follows from where in the capture chain the signal is defined — a signal measuring a stakeholder expectation is Business Health by definition, a diagnostic explaining one is Application or System. The field stores the assignment; it is never elicited as a free choice | Yes |
| `description_business` | What the signal means in business terms | No |
| `description_technical` | How it is measured | No |
| `sloTarget` | The service-level objective (SLO) target — for `sli_ratio` and `sli_threshold` signals; business-impact signals quantify consequence and carry no SLO target | Conditional |
| `timeWindow` | The measurement window the target applies to | Conditional |
| `budgetingMethod` | How the error budget is counted against the target (occurrences-based or time-based) | Conditional |

Type-specific measurement fields follow the signal type: ratio signals need a numerator and denominator, threshold signals need an operator, value, and unit — validated at update time, not creation time (three-actor progressive enrichment: the Product Owner creates the stub, the Developer fills in measurement, Platform configures alerting).

**Per-layer health dimensions.** The current capture model additionally classifies every signal by a layer-native dimension framework — APQC (Effectiveness / Efficiency / Adaptability) at Business Health; Golden Signals or RED as a per-signal fit choice at Application (RED for request-driven services); USE (Utilization / Saturation / Errors) at System. The framework follows from the layer; the dimension within it is a judgment call by the signal's owner, captured at onboarding and carried in the pipeline record (`healthDimensionFramework`, `healthDimension`). These fields travel with the signal definition from onboarding forward.

## Outputs

- One signal definition per measurement — the record dashboards, alerts, and playbooks are generated from
- **Signal-to-expectation traceability** — each signal maps to the stakeholder expectations it measures, recorded as expectation-signal mappings; coverage queries ("which expectations have no signal?") run against these

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA01 — Business Context](../ka01-business-context.md) | Stakeholder expectations determine what signals to define |
| [KA02 — Signal Design](../ka02-signal-design.md) | This instrument captures [KA02.1](../ka02-signal-design.md#signal-type-taxonomy) (Signal Type Taxonomy) and [KA02.2](../ka02-signal-design.md#signal-to-function-mapping) (Signal-to-Function Mapping) |

## Usage Context

**When to reach for this instrument:**
- After stakeholder expectations are captured ([IN-06](in-06-stakeholder-expectation-template.md)) — signals measure whether expectations are met
- When a new business function needs health monitoring
- When an incident reveals a gap in signal coverage (lifecycle feedback from [KA05 — Incident Response](../ka05-incident-response.md))

**Related instruments:**
- [IN-06 Stakeholder Expectation Template](in-06-stakeholder-expectation-template.md) — provides the expectations that signals measure
- [IN-07 Health Signal Template](in-07-health-signal-template.md) — captures the measurement details (metric source, formula)
- [IN-09 Signal Specification Format](in-09-signal-specification-format.md) — deeper spec-level detail for complex signals
- [IN-23 Observability Standard](in-23-observability-standard.md) — the canonical per-layer signal sets and chain positions these definitions serve
