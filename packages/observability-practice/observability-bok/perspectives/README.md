# Perspectives Catalog

**What this is:** Platform-type and context-type lenses that bend how Knowledge Areas and Practice Instruments apply. Where KAs organize *what* you need to understand and Instruments organize *what you can do*, Perspectives organize *how the answer varies by platform context*.

**Pattern:** Adapted from BABOK v3 Perspectives chapter (IIBA) — perspectives are not Knowledge Areas (they don't own distinct knowledge) and not Instruments (they don't do one thing). They're lenses that describe how existing KAs and Instruments adapt for specific contexts.

**Why this exists:** Observability practice is not uniform. Mainframe instrumentation is structurally different from cloud-native instrumentation. Hybrid environments face a distinct correlation problem neither pure-cloud nor pure-mainframe do. SaaS observation without code access uses different techniques entirely. The Knowledge Areas hold the invariant structure (stakeholder → expectation → signal → response). The Perspectives hold the variation.

---

## The Perspectives

| Perspective | What it covers | State |
|---|---|---|
| [Cloud-Native](cloud-native.md) | Container platforms, service mesh, OpenTelemetry-native instrumentation | **Seeded** |
| [Mainframe](mainframe.md) | SMF/RMF records, batch-job telemetry, transaction monitors (CICS/IMS) | **Seeded** |
| [Hybrid / Integration-Oriented](hybrid-integration.md) | Cross-platform correlation, metadata parity, trace propagation across boundaries | **Seeded** |
| [SaaS / Third-Party](saas-third-party.md) | Instrumentation without code access, API-level observability, vendor telemetry ingestion | **Seeded** |
| [Agentic](agentic.md) | Services containing a judgment-making software step — the conditional Agent Workflow stratum *(provisional vocabulary)*, decision-quality signals, the answer-key obligation | **Current** |

---

## How perspectives interact with Knowledge Areas

A perspective page is not a parallel KA — it's an annotation layer. Each perspective names the KAs whose techniques vary most under that lens, and describes the variation. A reader with a question like "how do we observe mainframe batch jobs?" enters through the Mainframe perspective and is routed to the relevant KA topics with the platform-specific framing applied.

## What this structure makes possible

Three things a flat KA list doesn't:

- **Cross-platform coherence.** The Four-Layer Model, the stakeholder-expectation chain, and the signal taxonomy stay invariant across perspectives. A stakeholder expectation is a stakeholder expectation whether the service runs on a mainframe or a Kubernetes cluster.
- **Platform-specific guidance.** A mainframe practitioner reading [KA02](../ka02-signal-design.md) Signal Design needs the mainframe variation (SMF records, batch patterns). A cloud-native practitioner needs OTel guidance. The perspectives page delivers that without fragmenting the KAs.
- **Honest scoping of what's covered.** A Seeded perspective page is itself the useful information: "this exists in the domain, we know it belongs here, the content is queued."

## What this structure does NOT do

- It does not introduce new Knowledge Areas. The 13 KAs and the Four-Layer Model are perspective-invariant.
- It does not duplicate KA content. Perspectives name variations; KAs hold the core knowledge.
- It does not resolve the variation exhaustively. A practitioner facing a novel platform (e.g., edge IoT) may find partial guidance and known gaps — which is the honest answer to "can we do X on Y platform."
