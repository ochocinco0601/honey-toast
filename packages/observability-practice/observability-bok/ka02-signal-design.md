# KA02 — Signal Design & Instrumentation

**Category:** Core Practice

**Lifecycle stage:** Implement

**Primary owner:** Developer

**Question this KA answers:** How do we instrument the signals that matter?

---

## 1. Purpose & Scope

This KA covers how business context becomes measurable. [KA01](ka01-business-context.md) defines what "healthy" means. KA02 translates that into signals — the specific measurements that tell you whether expectations are being met. Signal design is the bridge between business intent and technical telemetry.

**What's in scope:**

- Signal type taxonomy — the four-layer model applied to signal classification
- Signal-to-function mapping — semantic binding between signals and the business functions they serve
- Instrumentation strategy — where and how signals are emitted
- Signal hierarchy and dependencies — how signals relate to each other
- Semantic conventions — naming, tagging, and attribute standards
- Telemetry pillars — metrics, logs, traces, profiles as distinct signal categories
- Data cardinality and dimensionality — the tension between investigative power and cost

**What's out of scope:**

- Defining what to measure ([KA01](ka01-business-context.md)) — KA02 assumes business context exists
- Platform tooling and pipeline architecture ([KA06](ka06-platform-tooling.md)) — KA02 designs signals, [KA06](ka06-platform-tooling.md) implements the collection infrastructure
- Quality enforcement ([KA03](ka03-standards-quality.md)) — KA02 produces signal designs, [KA03](ka03-standards-quality.md) validates them
- Visualization ([KA04](ka04-monitoring-visualization.md)) — KA02 produces the data, [KA04](ka04-monitoring-visualization.md) renders it

---

## 2. Domain Knowledge

### Signal Type Taxonomy

The four-layer model ([KA01](ka01-business-context.md)) classifies signals by business meaning. KA02 adds the measurement dimension — how each layer's signals are technically expressed:

| Layer | Signal Types | Measurement Pattern |
|-------|-------------|-------------------|
| Business Health | `sli_ratio`, `sli_threshold` | Business outcome metrics: fill rate %, pass rate %, on-time rate |
| Business Impact | `business_impact` | Consequence quantification: customers_affected, dollars_at_risk, compliance_cases, ops_minutes_added |
| Application | `sli_ratio`, `sli_threshold` | Workflow metrics: validation rates, batch completion, error rates |
| System | `sli_ratio`, `sli_threshold` | Infrastructure metrics: uptime %, latency, CPU, memory |

**Two measurement types for Business Health, Application, and System:**

- **sli_ratio** — good events / total events. "99.5% of page loads complete in < 2 seconds." Requires a numerator query (good events) and denominator query (total events).
- **sli_threshold** — metric vs. absolute limit. "Average response time stays below 500ms." Requires a measurement query, operator (lt/gt/lte/gte/eq), value, and unit.

**Business Impact is structurally different:** Business impact signals don't have SLO targets or thresholds. They activate when a Business Health signal breaches its target, quantifying the consequence across four categories. They are event-driven, not continuously measured.

**Per-layer health dimensions.** Beyond its measurement type, every signal carries a health-dimension classification from the framework native to its layer:

| Layer | Framework | Dimensions |
|-------|-----------|-----------|
| Business Health | APQC process performance | Effectiveness, Efficiency, Adaptability |
| Application | Golden Signals — or RED for request-driven services | Latency, Errors, Traffic, Saturation (Golden Signals); Rate, Errors, Duration (RED) |
| System | USE | Utilization, Saturation, Errors |
| Agent Workflow *(conditional stratum — provisional name)* | Agent Decision *(provisional)* | Correctness, Grounding, Traceability, Drift — Escalation/Autonomy held as a candidate |

The framework follows from the layer, with one exception: at the Application layer the framework itself is a per-signal fit choice — Golden Signals is the general-purpose vocabulary, RED (≈ Golden Signals minus Saturation) fits request-driven services. The dimension within the framework is a judgment call by the signal's owner, captured with the signal definition. This vocabulary gives every layer an established industry frame for asking "which aspect of health does this signal watch?" The Agent Decision framework is the one row without an industry-canonical set behind it — see the stratum's status note below.

#### The Agent Workflow stratum — conditional, provisional

Some services contain an **agentic step**: software that makes a judgment call — review this package, decide whether the case proceeds. Traditional signal design rests on an assumption so old it is invisible: software is deterministic, so the specification is the answer key — "wrong" shows up as errors, latency, or saturation, and the layers above already catch it. An agentic step breaks that assumption. It can satisfy every mechanism expectation — fast, error-free, saturation nominal — and have decided wrongly. That is a failure surface no classic signal watches, which is why it enters the taxonomy as a stratum with its own question (*are the discretionary steps deciding well?*) rather than as a field on existing signals.

**The design frame: treat the step as a new hire with discretion.** What would an accountable owner insist on knowing about a person doing that job?

| The worry about the hire | Dimension | What measuring it takes |
|---|---|---|
| Are their calls right? | **Correctness** | An answer key — a **golden set** (cases with known answers, re-run per release) or a **judge** (a second opinion sampling live decisions). Traditional monitoring never needed one; determinism made the spec the key. |
| Did they decide from the actual case file, or from what they imagined? | **Grounding** | Checking outputs against the inputs they claim to rest on — the fabrication check. |
| Can they show their work? | **Traceability** | Reconstructing the decision: which decider (model + prompt + ruleset version), what inputs, what steps. |
| Are they still the person you vetted? | **Drift** | Comparing today's input mix and decision distribution against the validated baseline. |
| Do they know when *not* to decide? | **Escalation/Autonomy** *(candidate — not yet in the set)* | Abstention/deferral rate when uncertain or out of policy. |

Most of this is familiar machinery under new names: offline vs. online evals are synthetics vs. real-user monitoring; decision provenance is deploy versioning applied to the decider; drift is baseline monitoring where the watched quantity is a decision distribution instead of CPU. The genuinely new obligation is the answer key — **the practice must now supply the reference that determinism used to supply for free.** An agent correctness signal is otherwise an ordinary `sli_ratio` ("agreement ≥ 98% on the labelled set") that sits as diagnostic descent under the Business Health signal it explains, exactly like an Application signal.

**Status honesty (deliberate, not an oversight).** The stratum activates conditionally — most services never have a qualifying step. Its name and its dimension set are explicitly provisional: the industry sources (OpenTelemetry GenAI semantic conventions, NIST AI Risk Management Framework, evaluation taxonomies) are converging, not converged. Two questions are held open on purpose, to be ruled as real evidence accrues — onboardings and the operational history that follows them: whether the decision-quality set is **complete** (Escalation/Autonomy is the named candidate; policy/authorization scope a known edge), and whether agent-**operational** concerns — per-decision cost, content refusals (a refusal is a decision, not a machinery error), model fallbacks (a fallback changes the decider) — need an operational vocabulary beside the decision-quality one. Until then, no worked examples appear in the BOK (exemplars render from onboarded records rather than constructed content), and the stratum's machinery advances unevenly by design: the onboarding instrument elicits it and the interview record serializes it; adopting the layer downstream requires extending monitoring surfaces and data models to accept it.

### Signal-to-Function Mapping

Every signal must have a semantic binding to the business function it serves. This is the traceability requirement — no signal exists without business justification, and no stakeholder expectation exists without a signal measuring it.

Two relationship types bind the business layers directly to expectations:

- **Business Health signal → verifies → stakeholder expectation.** "This health signal measures whether this expectation is being met." This mapping is structural — it is produced by the capture itself when the signal is defined inside its stakeholder's chain ([KA01](ka01-business-context.md)), never reconnected as a separate mapping exercise.
- **Business Impact signal → quantifies → stakeholder expectation.** "This impact signal measures the consequence when this expectation is breached."

The mechanism layers bind differently. Application and System signals do not map directly to expectations — they support the Business Health signals they help explain. Each carries a **causal link** ("which Business Health signal does this diagnostic explain?") and, for Application signals, a grounding to the **sub-capability** it watches. Their business justification flows through the Business Health signal they support, which in turn traces to an expectation.

The Service Status evaluation ([IN-08](instruments/in-08-service-status-template.md)) measures traceability coverage — what percentage of stakeholder expectations have at least one linked signal. An unmapped stakeholder is a gap that the evaluation makes visible.

### Instrumentation Strategy

Where and how signals are emitted. Three patterns:

1. **Code-level instrumentation** — signals emitted from application code. The Developer adds measurement points (counters, gauges, histograms) at relevant locations. Most Application and Business Health signals use this pattern.
2. **Pipeline instrumentation** — signals derived from data flowing through processing pipelines. Batch job completion rates, message queue depths, ETL success rates.
3. **Agent-based instrumentation** — external agents that observe system behavior without modifying application code. Infrastructure metrics (System), synthetic monitoring, log-based signal extraction.

**The three-actor ownership model** is the defining characteristic of signal implementation:

- PO creates the signal definition (name, business description, SLO target)
- Developer implements it (signal type, queries, data source)
- Platform Engineer configures alerting (thresholds, severity, routing)

This split is reflected in the data model — a single signal record accumulates fields from all three actors over time. The PO can create a signal before the Developer has written any queries. This is by design — the PO's business context should not be blocked by technical implementation.

### Signal Hierarchy & Dependencies

Signals don't exist in isolation. They form hierarchies and dependency chains:

- **Business Health signals depend on System/Application signals.** A business health signal ("fill rate is above 90%") depends on system signals ("platform is up") and application signals ("workflow is executing correctly"). When Business Health degrades, the investigation path goes to System/Application.
- **Business Impact signals depend on Business Health signals.** Business impact activates WHEN business health breaches a threshold. No Business Health breach, no Business Impact activation.
- **Leading vs lagging indicators.** Some signals predict problems (queue depth growing = leading). Others confirm problems after the fact (error rate increase = lagging).
- **Composite signals.** Aggregate health across multiple measurements — an overall service health score derived from several individual signals.

### Semantic Conventions

Naming, tagging, and attribute standards that carry business context with telemetry. Without conventions, every team invents its own naming scheme and cross-service analysis becomes impossible.

A domain vocabulary provides controlled terminology for business observability entities. Signal naming follows paired patterns: `signal_name` (machine-friendly), `signal_display_name` (human-readable). An `observability_layer` field classifies every signal into one of the four layers ([IN-05](instruments/in-05-signal-definition-template.md) carries the field set).

OpenTelemetry semantic conventions provide the industry standard for span attributes and naming. Business observability adds a layer-classification attribute (e.g., `observability_layer` on each signal) that makes System/Application/Business Health/Business Impact mechanically filterable across the telemetry pillars — preserving business meaning through distributed traces.

### Telemetry Pillars — Metrics, Logs, Traces, Profiles

The industry-standard signal categories, classified by data shape rather than business meaning:

| Pillar | What it captures | Characteristic |
|--------|-----------------|----------------|
| **Metrics** | Aggregated numeric measurements | Time series, pre-aggregated, low cardinality per metric |
| **Logs** | Discrete event records | Structured or unstructured text, high volume |
| **Traces** | Distributed request flows | Spans across services, causal relationships |
| **Profiles** | Resource consumption snapshots | CPU, memory, allocation patterns at a point in time |

The four-layer model ([KA02.1](ka02-signal-design.md#signal-type-taxonomy)) classifies by business meaning. The pillars classify by data shape. These are orthogonal — a single Business Health signal could be implemented as a metric (ratio of good/total events), derived from logs (counting error messages), or extracted from traces (measuring end-to-end latency).

A data model for business observability accommodates all pillars through a `data_source` abstraction (log platform, APM, synthetics, metrics, custom). The choice between pillars follows the signal's purpose: metrics when you need aggregates and trends, logs when you need discrete event records, traces when you need cross-service causality, profiles when you need resource-consumption evidence.

### Data Cardinality & Dimensionality

High-cardinality data (unique user IDs, request IDs, trace IDs) enables investigative observability — the ability to ask novel questions about specific cohorts, transactions, or paths. This is what distinguishes observability from monitoring ([KA04.6](ka04-monitoring-visualization.md#exploratory-analysis-hypothesis-driven-investigation)).

The tension: high cardinality enables investigation but drives cost ([KA06.6](ka06-platform-tooling.md#observability-economics-cost-optimization)). More unique values per dimension means more data to store, index, and query. Enterprise observability platforms typically impose cardinality limits that practitioners experience as constraints on what can be observed — often without explicit risk-acceptance framing behind them.

Prior art: Charity Majors (Honeycomb) on high-cardinality observability, Ben Sigelman (LightStep/ServiceNow) on distributed tracing.

---

## 3. Practices & Processes

### The Signal Design Workflow

```
1. Read service profile  → Developer receives KA01 output: stakeholder expectations, impact categories
2. Choose signal type    → sli_ratio or sli_threshold for Business Health; business_impact for Business Impact
3. Define measurement    → What query, what data source, what formula
4. Link the chain        → Business Health signals carry structural traceability from their
                           stakeholder chain (KA01); Application/System signals link causally to
                           the Business Health signals they help explain, and Application signals
                           ground to the sub-capability they diagnose
5. Validate quality      → KA03 gates: does the signal meet standards?
6. Deploy to platform    → KA06: signal flows through the telemetry pipeline
```

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Stakeholder expectations, SLO targets | [KA01](ka01-business-context.md) | Signal design starts from business context |
| Platform capabilities, data sources | [KA06](ka06-platform-tooling.md) | What's technically possible to instrument |
| Quality standards | [KA03](ka03-standards-quality.md) | What the signal must satisfy before production |

| Output | To | Purpose |
|--------|-----|---------|
| Implemented signals with queries | [KA04](ka04-monitoring-visualization.md) (Monitoring) | Signals become visible through dashboards |
| Signal quality metadata | [KA03](ka03-standards-quality.md) (Standards) | Quality gates validate signal completeness |
| Traceability mappings | [KA01](ka01-business-context.md) (Business Context) | Confirms business justification for every signal |

---

## 4. Roles & Responsibilities

| Activity | Product Owner | Developer | Platform/SRE |
|----------|:---:|:---:|:---:|
| Define what to measure (SLO targets) | **Own** | — | — |
| Choose signal type (ratio/threshold) | Advise | **Own** | — |
| Write queries and identify data sources | — | **Own** | Advise |
| Set up telemetry pipeline | — | — | **Own** |
| Link Application/System signals to the Business Health signals they explain | Review | **Own** | — |
| Configure alert/page thresholds | — | — | **Own** |

The Developer is the primary actor for KA02. The PO provides the "what and why" ([KA01](ka01-business-context.md)). The Developer provides the "how." Platform provides the infrastructure.

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA02 knowledge — a practitioner doing signal design work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-01 Service Maturity Model](instruments/in-01-service-maturity-model.md) | Assessment | Instrumented stage = KA02 knowledge applied (signals implemented) |
| [IN-05 Signal Definition Template](instruments/in-05-signal-definition-template.md) | Definition | Captures signal definitions with SLO targets — the primary KA02 output artifact |
| [IN-07 Health Signal Template](instruments/in-07-health-signal-template.md) | Definition | Captures measurement details — metric source, formula, threshold |
| [IN-09 Signal Specification Format](instruments/in-09-signal-specification-format.md) | Definition | Feature-spec reference for signal types, ownership model, data model |
| [IN-10 Story Factory](instruments/in-10-story-factory.md) | Production | Generates Developer stories from signal definitions for implementation planning |
| [IN-12 Alert Factory](instruments/in-12-alert-factory.md) | Production | Signal thresholds and burn rates are the primary alert-generation input |
| [IN-13 Playbook Factory](instruments/in-13-playbook-factory.md) | Production | Signal patterns drive generated triage steps and investigation order |
| [IN-23 Observability Standard](instruments/in-23-observability-standard.md) | Definition | The canonical per-layer signal sets KA02 signal design draws from |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| Four-Layer Model reference | Signal type taxonomy, layer definitions, implementation mapping |
| Health Signals specification | Polymorphic signal types, three-actor ownership, conditional validation |
| Impact Signals specification | Business impact signal data model |
| Signal traceability specification | Signal-to-stakeholder mapping: verifies/quantifies relationships |
| Domain vocabulary | Controlled terminology for signals, layers, and methodology entities |

### Techniques

- **Business-first signal design** — start from the stakeholder expectation, not the available telemetry. "What does this stakeholder need to know?" before "what can we measure?"
- **Three-actor progressive enrichment** — PO creates the stub (name, business description, target). Dev fills in the measurement (queries, data source). Platform configures alerting. One record, three contributors.
- **Type-specific validation** — conditional required fields based on signal type. Ratio signals need numerator + denominator. Threshold signals need operator + value + unit. Validated at update time, not creation time.

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA01](ka01-business-context.md) — Business Context | KA02 **depends on** [KA01](ka01-business-context.md) | Cannot design signals without business context. [KA01](ka01-business-context.md)'s output is KA02's input. |
| [KA06](ka06-platform-tooling.md) — Platform & Tooling | KA02 **depends on** [KA06](ka06-platform-tooling.md) | Signal designs are operationalized through platform tooling. |
| [KA03](ka03-standards-quality.md) — Standards & Quality | KA02 **feeds** [KA03](ka03-standards-quality.md) | Signal designs become the basis for quality standards. |
| [KA04](ka04-monitoring-visualization.md) — Monitoring & Visualization | KA02 **feeds** [KA04](ka04-monitoring-visualization.md) | Implemented signals become the data for dashboards and monitoring. |

### External References

| Reference | Relevance |
|-----------|-----------|
| Google SRE Book (Beyer et al.) | SLI/SLO framework, signal type patterns |
| Alex Hidalgo, *Implementing Service Level Objectives* | Practical SLO implementation, budgeting methods |
| Charity Majors (Honeycomb) | High-cardinality observability, investigative signal design |
| Ben Sigelman (LightStep/ServiceNow) | Distributed tracing, cardinality management |
| OpenTelemetry project | Semantic conventions, instrumentation patterns (referenced, not operationalized here) |
| OpenTelemetry GenAI semantic conventions | Agent-stratum traceability attributes (`gen_ai.*`) — decision provenance grounding |
| NIST AI Risk Management Framework | Agent Decision dimension grounding (Valid & Reliable → Correctness; Accountable & Transparent → Traceability) |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA02.1](ka02-signal-design.md#signal-type-taxonomy) Signal Type Taxonomy | **Current** | Complete four-layer taxonomy with examples, ownership, ordering, and per-layer health-dimension frameworks (APQC / Golden Signals-RED / USE). Conditional Agent Workflow stratum added with provisional Agent Decision vocabulary — completeness challenges stay open; onboardings and operational history can refute or extend the set, not prove it. |
| [KA02.2](ka02-signal-design.md#signal-to-function-mapping) Signal-to-Function Mapping | **Current** | Semantic binding documented: Business Health→verifies, Business Impact→quantifies. Traceability spec. |
| [KA02.3](ka02-signal-design.md#instrumentation-strategy) Instrumentation Strategy | **Seeded** | Spec defines fields but no practitioner guide for choosing an approach. |
| [KA02.4](ka02-signal-design.md#signal-hierarchy-dependencies) Signal Hierarchy & Dependencies | **Seeded** | Hierarchy implied in four-layer model. No explicit dependency guidance. |
| [KA02.5](ka02-signal-design.md#semantic-conventions) Semantic Conventions | **Seeded** | Domain vocabulary exists. No OTel-level semantic convention guidance. |
| [KA02.6](ka02-signal-design.md#telemetry-pillars-metrics-logs-traces-profiles) Telemetry Pillars | **Seeded** | Data model accommodates pillars. No pillar-specific decision guidance. |
| [KA02.7](ka02-signal-design.md#data-cardinality-dimensionality) Data Cardinality & Dimensionality | **Missing** | External prior art: Charity Majors, Ben Sigelman on high-cardinality observability. |

**KA02 summary:** 2/7 Current, 4 Seeded, 1 Missing. The four-layer taxonomy is strong. Implementation guidance is the consistent gap — practitioners know WHAT to measure ([KA01](ka01-business-context.md) is 6/6 Current) but not HOW to implement the measurement. KA02 is where the methodology transitions from PO-owned to Developer-owned, and the Developer-facing content is thinner.
