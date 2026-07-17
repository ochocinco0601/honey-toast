# KA06 — Platform & Tooling

**Category:** Enabling Practice
**Primary owner:** Platform Engineering
**Question this KA answers:** What technology makes observability possible?

---

## 1. Purpose & Scope

This KA covers the technology landscape that makes observability possible. Tool selection, telemetry pipeline architecture, consolidation strategy, platform operations, observability-as-code, and the economics of running an observability platform at enterprise scale. KA06 is cross-cutting — it enables all core practice KAs ([KA01](ka01-business-context.md)-[KA05](ka05-incident-response.md)) by providing the infrastructure they depend on.

**What's in scope:**
- Tool landscape and selection — evaluating and managing observability tools
- Telemetry pipeline architecture — collection, routing, enrichment, storage
- Consolidation vs best-of-breed strategy — single vendor vs specialized tools
- Platform operations — running the observability platform itself
- Observability-as-code — IaC patterns for observability configuration
- Observability economics — cost management, data volume, licensing

**What's out of scope:**
- What to monitor ([KA01](ka01-business-context.md)-[KA02](ka02-signal-design.md)) — KA06 provides the HOW, not the WHAT
- Quality standards ([KA03](ka03-standards-quality.md)) — KA06 implements enforcement infrastructure
- Dashboard design patterns ([KA04](ka04-monitoring-visualization.md)) — KA06 provides the rendering tools

---

## 2. Domain Knowledge

### Tool Landscape & Selection

A typical enterprise observability tool portfolio spans log platforms (Splunk), APM (AppDynamics, Dynatrace), synthetics (ThousandEyes), metrics/visualization (Grafana), event management (BigPanda), and others. Each tool serves different signal types and audiences. A well-designed business observability data model abstracts over tool selection through a `data_source` field — a signal can come from any supported platform.

Research on 11 industry observability maturity models (AWS, Grafana, Splunk, New Relic, Honeycomb, Dynatrace, DORA, and others) shows convergence on a common maturity arc: reactive → proactive → predictive. The industry is stuck at the transition from "technical observability" to "business-aware" — only 15-20% of organizations have crossed it.

**Self-service tool discovery** is a recurring enterprise gap: an app owner who can describe their application cannot easily determine which observability tools apply, what's already configured, and what's missing. This is a navigation problem layered on the tool evaluation framework.

### Telemetry Pipeline Architecture

A reference implementation documents one complete pipeline — synthetic monitoring (e.g., ThousandEyes) → OTLP → Prometheus → Mimir → Grafana. This demonstrates the full chain from synthetic monitoring through data collection, storage, and visualization.

A reference business observability pipeline: CSV input → SQLite database → ORM → Grafana dashboards. Schema-driven: changes to the data model propagate through migrations, ORM, and dashboard generators.

**Pipeline health is observability's observability.** Operating experience with platform disaster recovery surfaces a critical insight: an observability platform that is unobserved in steady state cannot be trusted in DR. Required steady-state health signals: ingest pipeline freshness, scheduled-search success rate, synthetic-event round-trip, alert delivery round-trip.

### Consolidation vs Best-of-Breed

The enterprise strategy question: one observability platform for everything, or specialized tools for different needs?

The practical framing that resolves most real-world instances: **common where possible, custom where needed.** Duplication and customization are different. Capabilities that teams can share (e.g., anomaly detection as a service) belong in the common platform. Line-of-business specificity lives in the *outputs*, not in who owns the capability: LOB-specific dashboards and domain-specific playbooks are tenant-specific products of the shared production capability — one factory, many tenants, unique outputs per tenant — with the LOB owning its inputs (service context, expectations), not its own production machinery.

### Platform Operations

Running the observability platform itself — availability, capacity, cost. A reference architecture pattern: SQLite database, ORM layer, migration pipeline, Grafana rendering, with schema-driven UI metadata generation.

**Platform-resilience patterns from operating experience:**
- Platform failure modes split into read-path (correct but slow) and write-path (fast but stale). Data-delayed is strictly worse because it corrupts truth, not throughput.
- Gray failure taxonomy: region loss (rare/total), platform degradation (recurring/gray-zone), catastrophic loss (very rare/total). Classical DR solves for mode 1. Mode 2 is where most operational harm occurs.
- Meta-observability: the platform needs its own SLOs, decomposed into freshness × query performance dimensions.

### Observability-as-Code

Infrastructure-as-code patterns for observability configuration. Dashboards, alerts, and routing defined as code rather than manually configured through UIs.

A reference pipeline implements this partially: schema-driven dashboard generation, ORM-based data access, migration scripts for schema evolution. The pattern: change the schema definition → regenerate artifacts.

### Observability Economics & Cost Optimization

The financial dimension of observability. Data volume costs, tool licensing, storage retention, sampling strategies, cost-per-signal economics. Directly connected to cardinality decisions ([KA02.7](ka02-signal-design.md#data-cardinality-dimensionality)) — high-cardinality data enables investigation but drives cost.

A common practitioner observation: logging and monitoring volume is often constrained by limits that feel arbitrary — forcing teams to reduce visibility even on critical production infrastructure. When practitioners describe limits as "arbitrary," it typically signals implicit cost policy rather than deliberate risk acceptance — the cost/coverage tradeoff has been made, but not surfaced as a decision.

Cost-optimization practice for business observability draws on FinOps Foundation cost-management patterns applied to the observability stack — continuous cost-per-signal measurement, retention tiering by impact category, sampling policies tied to signal type.

---

## 3. Practices & Processes

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Signal designs | [KA02](ka02-signal-design.md) | Determines what the platform must collect |
| Quality standards | [KA03](ka03-standards-quality.md) | Determines enforcement infrastructure |
| Architecture constraints | [KA07](ka07-integration-architecture.md) | Enterprise architecture determines integration points |

| Output | To | Purpose |
|--------|-----|---------|
| Collection infrastructure | [KA02](ka02-signal-design.md) | Signal designs are operationalized through platform tooling |
| Visualization tools | [KA04](ka04-monitoring-visualization.md) | Dashboards and monitoring built on platform capabilities |
| Integration capabilities | [KA07](ka07-integration-architecture.md) | Platform enables enterprise architecture integration |

---

## 4. Roles & Responsibilities

| Activity | Platform Engineering | Developer | Practice Lead |
|----------|:---:|:---:|:---:|
| Tool evaluation and selection | **Own** | Advise (dev experience) | Advise (strategy) |
| Pipeline architecture | **Own** | — | Review |
| Platform operations | **Own** | — | — |
| Cost management | **Own** | — | Inform (budget) |
| OaC framework | **Own** | Contribute (CI/CD integration) | — |

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA06 knowledge — a practitioner doing platform and tooling work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-07 Health Signal Template](instruments/in-07-health-signal-template.md) | Definition | Captures metric source and pipeline details that platform teams implement |
| [IN-08 Service Status Template](instruments/in-08-service-status-template.md) | Definition | Tracks operational infrastructure — dashboard URLs, alert configs, platform readiness |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| Maturity model research | Industry sources, convergence analysis across published maturity models |
| Synthetics reference pipeline | Complete worked pipeline (e.g., ThousandEyes → OTLP → Prometheus → Mimir → Grafana) |
| Platform pipeline documentation | Data-flow architecture, ORM layer, schema migration patterns |
| Systems architecture plan | Visualization-platform infrastructure architecture |
| Schema-driven generation pattern | OaC pattern: change the schema, regenerate artifacts downstream |

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA02](ka02-signal-design.md) — Signal Design | KA06 **implements** [KA02](ka02-signal-design.md) | Platform implements signal design decisions |
| [KA04](ka04-monitoring-visualization.md) — Monitoring & Visualization | KA06 **enables** [KA04](ka04-monitoring-visualization.md) | Platform provides tools for monitoring |
| [KA07](ka07-integration-architecture.md) — Integration & Architecture | KA06 **enables** [KA07](ka07-integration-architecture.md) | Platform must integrate with enterprise architecture |
| [KA12](ka12-adoption-enablement.md) — Adoption & Enablement | KA06 **enables** [KA12](ka12-adoption-enablement.md) | Tool selection knowledge underpins self-service tool discovery in onboarding |

### External References

| Reference | Relevance |
|-----------|-----------|
| FinOps Foundation | Cost management for cloud/observability infrastructure |
| OpenTelemetry project | Vendor-neutral telemetry collection and pipeline standard |
| Gartner Observability Research | Tool landscape, market dynamics, cost benchmarks |
| Huang et al., HotOS 2017 | "Gray failure" — named concept for partial platform degradation |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA06.1](ka06-platform-tooling.md#tool-landscape-selection) Tool Landscape & Selection | **Seeded** | Industry research + one real pipeline. No reusable evaluation framework. |
| [KA06.2](ka06-platform-tooling.md#telemetry-pipeline-architecture) Telemetry Pipeline Architecture | **Seeded** | Reference pipeline chain named (synthetic monitoring → OTLP → metrics store → visualization); architecture guidance not yet practitioner-actionable from the page. |
| [KA06.3](ka06-platform-tooling.md#consolidation-vs-best-of-breed) Consolidation vs Best-of-Breed | **Seeded** | Industry context and the "common where possible" principle documented. Operational evaluation criteria not yet extracted. |
| [KA06.4](ka06-platform-tooling.md#platform-operations) Platform Operations | **Current** | Platform architecture pattern documented, with DR failure-mode taxonomy. |
| [KA06.5](ka06-platform-tooling.md#observability-as-code) Observability-as-Code | **Seeded** | Individual patterns exist (schema-driven generation). No unified OaC framework. |
| [KA06.6](ka06-platform-tooling.md#observability-economics-cost-optimization) Observability Economics | **Seeded** | Brief concept content present in Section 2 (data-volume costs, tool licensing, retention tiering, sampling strategies, cost-per-signal economics). External prior art cited: FinOps Foundation. Practitioner-reported pattern — "arbitrary limits" signalling implicit cost policy — is evidence awaiting formalization. Promotion to Current requires a reusable cost-optimization methodology practitioners can apply. |

**KA06 summary:** 1/6 Current, 5 Seeded. KA06 is the dominant landing zone for real operational experience; as content matures, it should cover platform failure modes, platform SLOs, and platform self-monitoring.
