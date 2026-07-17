# Perspective — SaaS / Third-Party

**State:** Seeded

The context where observed systems are operated by someone else. Salesforce, Workday, payment processors, fraud-detection vendors, identity providers, cloud-managed services whose internals are opaque to the operating organization. Observation without code access.

## What distinguishes this perspective

- **No code-level instrumentation.** You cannot add OTel spans to Salesforce. Observability for SaaS must come from API-level signals, vendor-emitted telemetry, and synthetic probing.
- **Vendor telemetry is partial and schema-variable.** Different vendors emit different signals on different cadences with different schemas. Bringing these into a unified observability model requires translation.
- **Synthetics carry disproportionate weight.** For third-party services, synthetic transactions that probe the vendor's surface are often the most reliable signal of availability and performance from the consumer's perspective.
- **Shared responsibility is explicit.** The vendor owns their infrastructure; you own your integration, your authentication, your data. Observability must scope which layer is responsible for each failure mode.

## KA Variations under this perspective

| KA | Variation |
|----|-----------|
| [KA02 Signal Design](../ka02-signal-design.md) | Signals sourced from API response codes, vendor webhook events, synthetic probes. Semantic conventions ([KA02.5](../ka02-signal-design.md#semantic-conventions)) extended with vendor-identifier metadata. |
| [KA04 Monitoring & Visualization](../ka04-monitoring-visualization.md) | Monitoring centers on consumer-side experience (what the integration produces) more than vendor-side internals (which are opaque). |
| [KA05 Incident Response](../ka05-incident-response.md) | Escalation paths include the vendor — playbooks must encode vendor support contacts, SLA terms, escalation procedures. |
| [KA06 Platform & Tooling](../ka06-platform-tooling.md) | Observability tooling must support API monitoring, synthetic transaction platforms, webhook receivers. Less emphasis on tracing, more on endpoint monitoring. |
| [KA07 Integration & Architecture](../ka07-integration-architecture.md) | API contract observability — treating the vendor API as a first-class observed interface. |

## Known gaps in this perspective

- A methodology for modeling shared responsibility in service profiles — how to distinguish "our failure" from "vendor failure" from "integration failure."
- Patterns for composing business SLOs when a critical business step depends on a vendor SLA you don't control.

## External references

- Google SRE Workbook — SLOs over dependencies you don't operate
- Alex Hidalgo, *Implementing Service Level Objectives* — composing objectives across vendor boundaries

## Why this perspective matters

A growing share of critical business steps run on systems no internal team can instrument. Practice that assumes code access silently excludes them; this perspective keeps vendor-operated steps inside the observability discipline.
