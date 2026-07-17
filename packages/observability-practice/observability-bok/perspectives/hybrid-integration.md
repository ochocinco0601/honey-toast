# Perspective — Hybrid / Integration-Oriented

**State:** Seeded

The context where multiple platform types participate in a single business flow. A customer-facing transaction that originates in a cloud-native UI, authenticates through a SaaS identity provider, authorizes against a mainframe system of record, posts to a distributed ledger, and notifies the customer through a third-party messaging service — all within one logical business operation.

## What distinguishes this perspective

- **No single observability platform sees the full flow.** Cloud tools see the cloud portion. Mainframe tools see the mainframe portion. The seam between them is typically unobserved or weakly observed.
- **Metadata parity is a first-order concern.** Correlation across platform boundaries requires shared identifiers (transaction ID, session ID, business event ID) that survive the platform handoff. Without metadata parity, cross-platform correlation breaks down.
- **Trace propagation crosses technology boundaries.** Distributed tracing context (OTel trace IDs) must survive the boundary from cloud to mainframe to SaaS and back. Where it doesn't, the trace breaks and investigative observability ([KA04.6](../ka04-monitoring-visualization.md#exploratory-analysis-hypothesis-driven-investigation)) fails at exactly the points practitioners most need it.
- **Ownership ambiguity is high.** When a failure occurs at the seam between platforms, which team owns investigation? Hybrid observability requires explicit ownership across boundaries.

## KA Variations under this perspective

| KA | Variation |
|----|-----------|
| [KA02 Signal Design](../ka02-signal-design.md) | Semantic conventions ([KA02.5](../ka02-signal-design.md#semantic-conventions)) must include platform-boundary metadata — which platform emitted the signal, which platform it traversed into. |
| [KA04 Monitoring & Visualization](../ka04-monitoring-visualization.md) | Cross-signal correlation ([KA04.3](../ka04-monitoring-visualization.md#cross-signal-correlation)) is the primary capability — less about visualizing each platform's signals, more about stitching them into a coherent business flow. |
| [KA05 Incident Response](../ka05-incident-response.md) | Cross-platform triage — which platform "caused" a failure vs. which platform "experienced" the symptom. Ownership routing must cover the seam cases. |
| [KA07 Integration & Architecture](../ka07-integration-architecture.md) | The defining KA for this perspective. Configuration-management (CMDB) integration across platform types. Enterprise architecture decisions about where platform boundaries sit. |
| [KA08 Data Governance](../ka08-data-governance.md) | Shared naming conventions across platforms — without them, data coherence collapses at the boundary. |

## The seam problem

A pattern that recurs in practice: each individual platform is well-observed within its own domain, but the *seams between platforms* — where a transaction crosses from cloud to mainframe, or from internal to SaaS — are the least observed and most failure-prone. The hybrid perspective centers on closing those seams through shared identifiers, shared semantic conventions, and unified correlation capability.

## Known gaps in this perspective

- A reusable methodology for establishing metadata parity across platform types during observability rollout.
- Cross-platform SLO composition — how to derive a business-flow SLO from component SLOs that live on different platforms.

## External references

- W3C Trace Context specification — the propagation standard cross-platform correlation depends on
- OpenTelemetry context propagation documentation

## Why this perspective matters

Business flows cross platforms even when teams and tools do not. Guidance that stops at a platform boundary leaves the seams — where failures concentrate — unobserved.
