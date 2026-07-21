# KA04 — Monitoring, Visualization & Correlation

**Category:** Core Practice

**Lifecycle stage:** Observe

**Primary owner:** Platform / SRE

**Question this KA answers:** What views make health visible?

---

## 1. Purpose & Scope

This KA covers how signals become visible and actionable. Once business context is defined ([KA01](ka01-business-context.md)), signals are designed ([KA02](ka02-signal-design.md)), and standards are enforced ([KA03](ka03-standards-quality.md)), KA04 is where health becomes observable — through dashboards, real-time monitoring, cross-signal correlation, and the investigation workflows that turn alerts into understanding.

**What's in scope:**

- Dashboard design — consistent patterns across executive, operational, and team views
- Real-time monitoring — continuous observation of signal streams, threshold alerting
- Cross-signal correlation — connecting signals across services, layers, and tools
- Topology and dependency visualization — making service relationships visible
- Business health views — aggregate views showing business outcomes, not just system metrics
- Exploratory analysis — the hypothesis-driven investigation that distinguishes observability from monitoring

**What's out of scope:**

- Signal design and instrumentation ([KA02](ka02-signal-design.md)) — KA04 visualizes what [KA02](ka02-signal-design.md) produces
- Standards enforcement and quality gates ([KA03](ka03-standards-quality.md))
- Incident response and triage procedures ([KA05](ka05-incident-response.md)) — KA04 surfaces the signals, [KA05](ka05-incident-response.md) acts on them
- Platform tooling selection and pipeline architecture ([KA06](ka06-platform-tooling.md)) — KA04 uses whatever [KA06](ka06-platform-tooling.md) provides

---

## 2. Domain Knowledge

### Dashboard Design & Standards

Business observability dashboards follow a business-first information architecture. The core principle: visual prominence must match data reliability.

**Define success, store success, display failure.** Signal definitions are authored and stored in success terms — "Fill Rate ≥ 90%" is how a PO defines an expectation. For business audiences, the display inverts to failure/impact terms at rendering time: the business view shows the failure rate ("0.5% fail — and rising") because failure is what demands action, and a number that grows as things get worse is intuitively readable. The same source renders two views: an SLO/success view for the team that owns the service, a failure-framed business view for stakeholders and executives. The conversion happens in the generator, never in the stored record.

**Dashboard hierarchy** — five levels, each serving a different audience and question:

| Level | Audience | Question | Pattern |
|-------|----------|----------|---------|
| Product Lines | Executive | Is anything red? | Status list with trend sparklines and coverage, one row per product line |
| Products | Director | Which product area needs attention? | Status list with trend sparklines and coverage, one row per product |
| Services | Manager/Product Owner | Which service is degraded? | Status list with trend sparklines and coverage, one row per service |
| Service Detail | Product Owner/Developer/SRE | What's happening with this service? | Full context: stakeholder expectations, operational signals, impact estimates, SLI |
| Signal Detail | Developer/SRE | What's the signal showing? | Time series, threshold lines, investigation entry point |

Navigation is drill-down: Product Lines → Products → Services → Service Detail → Signal Detail. Each click narrows focus. A dashboard guide panel provides context at every level without leaving the view. (Column layouts and panel specifications live in [IN-15](instruments/in-15-dashboard-generation-methodology.md) and [IN-22](instruments/in-22-executive-dashboard-patterns.md).)

**Business-first sequencing** at the Service Detail level:

1. **Stakeholder expectations** — always exist (PO provides). Who cares and what they need.
2. **Operational signals** — the actual diagnostic truth. What's the current health?
3. **Business impact estimates** — reference context with uncertainty language ("~", "Estimated Impact"). Directionally useful but not primary decision driver.
4. **SLI** — the goal. May be blank for many services early in adoption.

This order reflects early-adoption reality: most services have operational signals but not yet SLIs. Putting SLI first creates an "idealized state" view that doesn't match what teams actually have. Putting stakeholder expectations first ensures every service detail view starts with business context — even before any signal exists.

*Known divergence:* the canonical four-layer model orders dashboard content Business Health first among signal layers. This Service Detail sequencing deliberately departs from that for the early-adoption case (the business-first intent is carried by stakeholder expectations leading the view). Whether the canonical order gains an explicit adoption-phase exception or this sequencing conforms is an open reconciliation decision — until it is ruled, this page names the divergence instead of hiding it.

**Signal trust hierarchy:**

- **SLI (highest)** — actual measurement of user-facing service health. This IS what's happening.
- **Operational signals (high)** — component health measurements. These components ARE functioning/failing.
- **Business impact estimates (lower)** — calculated from assumptions. Directionally useful, not perfectly accurate. Must communicate uncertainty: prefix with "~", use "Estimated Impact" not "Current Impact."

The lower trust rank applies to model-derived *estimates*, not to the Business Impact layer itself. Measured Business Impact signals (customers affected, dollars at risk, computed from real events) are what drives incident severity and executive prioritization — that decision role is unchanged; what earns caution is any impact number calculated from assumptions rather than measured.

### Real-Time Monitoring

Real-time monitoring is the continuous observation of signal streams against thresholds. In a business observability context, monitoring produces alerts when:

- A Business Health signal drops below its SLO target — the business outcome is not being met
- A System or Application signal crosses its alerting threshold — infrastructure or application degradation
- A Business Impact signal activates — quantifying the consequence of a Business Health breach

The monitoring pipeline connects business observability definitions to operational tools:

- **Business observability defines** what to monitor, thresholds, and alert routing (system of record)
- **Monitoring platforms render** the live view (e.g., Grafana, Splunk, AppDynamics, Datadog)
- **Incident-management tools route** alerts to the right team (e.g., BigPanda, PagerDuty)

Business observability is not the monitoring tool. It produces the blueprints — what panels to create, what thresholds to set, what business context to display. The monitoring platforms render the live view. Both are necessary.

**Synthetics** — proactive monitoring that tests service health without waiting for real user traffic. Synthetics verify that the observation pipeline itself is working, not just the service being observed.

### Cross-Signal Correlation

Correlation connects signals across services, layers, and tools to surface patterns that no single signal reveals. This is where the [four-layer model](the-methodology.md)'s value becomes operational — a Business Health miss correlated with System/Application degradation points to root cause; a Business Health miss without System/Application degradation points to a business logic problem.

**What correlation answers:**

- When Business Health drops, which System/Application signals moved? (mechanism identification)
- When multiple services degrade simultaneously, is there a shared dependency? (blast radius)
- When an alert fires, what changed in the last 30 minutes? (change correlation)
- When business impact is high for one service, are adjacent services also affected? (cascade detection)

**The cross-layer half of correlation is settled practice.** Seven named correlation patterns define how to read the combination of layer states — the combination, not any single-layer alert, is the decision surface, because individual alerts without cross-layer context produce either false urgency or false silence:

| Pattern | Layer states | Reading |
|---------|-------------|---------|
| All Clear | all healthy | Baseline — no action |
| Silent Business Failure | System/Application healthy, Business Health degraded | The pattern that justifies business observability — invisible to traditional monitoring. Investigate business logic, configuration, upstream data |
| Infrastructure Noise | System degraded, nothing propagated | Real alert, no incident — monitor, don't escalate |
| Infrastructure Cascade | System degradation propagating to Application and Business Health | Root cause in infrastructure — classic incident response |
| Application Failure | Application degraded, System healthy | Application defect — mechanism broken, platform fine |
| Multi-Layer Degradation | multiple layers degraded | Major incident — prioritize by Business Impact |
| Contained Application Issue | Application degraded, Business Health still healthy | Defect absorbed by redundancy — fix without escalation |

What remains unsolved is the cross-**service**, cross-**tool** half: correlating signals across service boundaries and platforms. Most enterprises lack a unified methodology there; the operational symptom is multi-tool triage — responders pivoting across dashboards and platforms to correlate what should be a single view. Event correlation draws on the SLI triage investigation framework and pathpoint patterns for hierarchical navigation.

### Topology & Dependency Visualization

Making service relationships visible — which services depend on which, how business processes flow across service boundaries, where a failure in one service affects others.

Three approaches:

1. **Business view** — maps the integration landscape from a business perspective: which business functions depend on which technology capabilities
2. **Terrain visualization** — renders the observability landscape as an interactive portfolio view: capabilities, coverage, fit assessment across services
3. **Pathpoint patterns** — hierarchical navigation from business journey through service stages to individual signals. Represents end-to-end business flows as visual paths (implementation: Grafana pathpoint plugin).

**The relationship to service-topology frameworks:** Enterprise service frameworks (e.g., banking-industry service-domain taxonomies such as BIAN) map topology — what supports what, from products down to applications and third parties. Business observability adds the semantic layer on top: what "healthy" means at each node. Topology without health definitions is just a map. Health definitions without topology can't show cascade effects. Both are needed.

### Business Health Views

Aggregate views showing business outcome health, not just system metrics. This is the executive and director audience — they need to know "is the business healthy?" not "is the server up?"

A business health view hierarchy (product lines → products → services) is itself a presentation pattern: at the top, a product line shows aggregate status across all its products; a product shows aggregate status across its services. Color coding (healthy/degraded/critical) with short-horizon sparklines gives trend at a glance.

**Key design principles for business health views:**

- Status dots and color coding must reflect business health (Business Health layer signals), not system health (System layer signals)
- Coverage metrics (e.g., "N of M services have definitions") show how much of the portfolio has observability definitions — making gaps visible
- Sparklines show trend, not just current state — a service that's been degraded for 6 hours is different from one that just turned red

### Exploratory Analysis & Hypothesis-Driven Investigation

The capability that distinguishes observability from monitoring: asking novel questions about system behavior without pre-defining the queries. Monitoring tells you THAT something is wrong. Observability helps you figure out WHY.

**The SLI triage investigation framework** defines five phases:

1. **Foundation analysis** — map current capabilities to investigation needs, identify available data sources and telemetry layers
2. **Investigation pattern research** — temporal analysis (regression detection, change points, comparative windows), dimensional breakdowns (dependencies, geography, customer segments, transaction flows), root cause tools (error heatmaps, log pattern clustering, trace exemplars)
3. **Workflow design** — triage decision trees based on regression type, investigation templates by failure mode (sudden drop, gradual degradation, intermittent, business logic)
4. **Framework documentation** — visualization taxonomy grouped by purpose, integration architecture for drill-down navigation
5. **Scenario validation** — test framework against real incidents

For services onboarded with the current capture instrument, investigation starts from the signal's **descent link** — the structural investigation path (signal → process step → sub-capability → component → diagnostics) assembled at definition time ([KA05](ka05-incident-response.md#playbook-design-execution)) — with the failure-mode templates below supplying what to check along it.

**Investigation templates by failure mode:**

- **Sudden drop** — circuit breaker patterns, dependency failures. Look for: change events, deployment timestamps, upstream service health.
- **Gradual degradation** — resource exhaustion, data growth. Look for: trend lines, capacity thresholds, queue depths.
- **Intermittent issues** — network problems, race conditions. Look for: error distribution patterns, time-of-day correlation, geographic distribution.
- **Business logic failures** — the business-observability-specific pattern: System/Application layers green, Business Health red. Look for: business rule changes, configuration drift, data quality issues.

---

## 3. Practices & Processes

### The Visualization Workflow

```
1. Define health         → KA01 produces service profiles with stakeholder expectations and SLOs
2. Design signals        → KA02 translates expectations into measurable signals
3. Enforce standards     → KA03 validates signal quality before production
4. Build dashboards      → KA04 renders signals as business-first views at 5 hierarchy levels
5. Configure monitoring  → KA04 sets up real-time alerting against thresholds
6. Investigate           → KA04 provides exploratory analysis when alerts fire
7. Respond               → KA05 takes action based on what KA04 surfaces
```

KA04 is the Observe stage — it depends on everything upstream ([KA01](ka01-business-context.md)-[KA03](ka03-standards-quality.md)) and feeds directly into Respond ([KA05](ka05-incident-response.md)).

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Stakeholder expectations, impact categories | [KA01](ka01-business-context.md) | Dashboard context panels, business health views |
| Signal definitions, SLO targets, data sources | [KA02](ka02-signal-design.md) | Dashboard panels, alerting thresholds |
| Quality-validated signals | [KA03](ka03-standards-quality.md) | Only signals that pass quality gates reach dashboards |
| Platform tooling (Grafana, Splunk, etc.) | [KA06](ka06-platform-tooling.md) | The rendering infrastructure for dashboards and monitoring |

| Output | To | Purpose |
|--------|-----|---------|
| Alerts (threshold breaches) | [KA05](ka05-incident-response.md) (Incident Response) | Triggers triage and response |
| Investigation findings | [KA05](ka05-incident-response.md) (Incident Response) | Root cause identification during incidents |
| Coverage gaps (visible in dashboards) | [KA01](ka01-business-context.md), [KA13](ka13-continuous-improvement.md) | Services without observability definitions are visible |
| Health trend data | [KA09](ka09-strategy-program.md) (Strategy) | Portfolio health informs strategic prioritization |

---

## 4. Roles & Responsibilities

| Activity | Product Owner | Developer | Platform/SRE | Leadership |
|----------|:---:|:---:|:---:|:---:|
| Define what goes on dashboards | **Own** (business context) | — | **Own** (technical signals) | Review (exec views) |
| Build dashboard panels | — | Contribute | **Own** | — |
| Set health/alert thresholds — Business Health, Business Impact | **Own** (business judgment) | Advise | — | — |
| Set health/alert thresholds — Application, System | — | **Own** | **Own** (operational expertise) | — |
| Deploy threshold configuration to the platform | — | — | **Own** | — |
| Investigate during incidents | — | **Participate** | **Own** | Informed |
| Review business health views | Review | — | — | **Own** (consume) |
| Define exploratory analysis patterns | — | Contribute | **Own** | — |

Platform/SRE is the primary actor for KA04. The PO contributes business context (what to show, who cares). Developers contribute signal implementation. Leadership consumes business health views.

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA04 knowledge — a practitioner doing monitoring and visualization work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-01 Service Maturity Model](instruments/in-01-service-maturity-model.md) | Assessment | Operationalized stage requires active dashboards and alerts (KA04 fully engaged) |
| [IN-11 Dashboard Factory](instruments/in-11-dashboard-factory.md) | Production | Generates monitoring dashboards from service profile and signal data |
| [IN-12 Alert Factory](instruments/in-12-alert-factory.md) | Production | Generates alert rules from signal thresholds and escalation policies |
| [IN-15 Dashboard Generation Methodology](instruments/in-15-dashboard-generation-methodology.md) | Production | Systematic approach to dashboard production — styling, layout, data binding, validation |
| [IN-22 Executive Dashboard Patterns](instruments/in-22-executive-dashboard-patterns.md) | Communication | Design patterns for executive-level business health dashboards |
| [IN-23 Observability Standard](instruments/in-23-observability-standard.md) | Definition | The computation rule for every status surface — green computed from below |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| Dashboard design principles | Signal trust hierarchy, visual prominence rules, business-first sequencing, early-adoption reality adjustments |
| Dashboard level patterns | Product Lines → Products → Services → Service Detail hierarchy, column layouts, sparklines, navigation |
| Executive dashboard guide | Platform-specific patterns (e.g., Grafana) for executive audiences |
| SLI triage framework | 5-phase investigation framework, failure-mode patterns, visualization catalog |
| Integration business view | Business function → technology capability mapping |
| Pathpoint knowledge base | Hierarchical navigation patterns, business journey visualization |
| Worked business-health-view example | Interactive walkthrough of a single service traced across the hierarchy |

### Techniques

- **Business-first dashboard sequencing** — stakeholder expectations first, operational signals second, impact estimates third, SLI fourth. Reflects what teams actually have, not idealized state.
- **Uncertainty communication** — "~" prefix, "Estimated Impact" labels for business impact calculations. Prevents executives from treating model outputs as ground truth.
- **Drill-down navigation** — Product Lines → Products → Services → Service Detail → Signal Detail. Each click narrows scope. Context preserved at every level.
- **12-hour sparklines** — 12 bars, one per hour, color = status. Shows trend at a glance without overwhelming the list view.
- **Investigation templates by failure mode** — sudden drop, gradual degradation, intermittent, business logic failure. Each has a starting checklist of what to look for.
- **Coverage metrics** — showing "N of M services have definitions" makes portfolio gaps visible at the executive level. Gaps are a feature, not a bug — they drive adoption ([KA12](ka12-adoption-enablement.md)).

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA02](ka02-signal-design.md) — Signal Design & Instrumentation | KA04 **depends on** [KA02](ka02-signal-design.md) | Visualization depends on instrumented signals. No signals, nothing to show. |
| [KA06](ka06-platform-tooling.md) — Platform & Tooling | KA04 **depends on** [KA06](ka06-platform-tooling.md) | Dashboards and monitoring are built on platform tooling (Grafana, Splunk, etc.) |
| [KA05](ka05-incident-response.md) — Incident Management & Response | KA04 **feeds** [KA05](ka05-incident-response.md) | Monitoring surfaces the events that trigger incident response. Investigation findings feed triage. |
| [KA01](ka01-business-context.md) — Business Context & Service Definition | KA04 **depends on** [KA01](ka01-business-context.md) | Business context determines dashboard content — stakeholder expectations, impact categories, SLO targets. |
| [KA03](ka03-standards-quality.md) — Standards & Quality Assurance | KA04 **depends on** [KA03](ka03-standards-quality.md) | Quality gates ensure only validated signals reach production dashboards. |
| [KA09](ka09-strategy-program.md) — Strategy & Program Management | KA04 **informs** [KA09](ka09-strategy-program.md) | Portfolio health views and coverage metrics inform strategic decisions. |

### External References

| Reference | Relevance |
|-----------|-----------|
| Charity Majors (Honeycomb) | Observability vs monitoring distinction — known-unknowns vs unknown-unknowns. Exploratory analysis ([KA04.6](ka04-monitoring-visualization.md#exploratory-analysis-hypothesis-driven-investigation)). |
| Ben Sigelman (LightStep/ServiceNow) | Distributed tracing for understanding, not just detection. Cross-signal correlation. |
| Stephen Few (*Information Dashboard Design*) | Dashboard design principles — visual prominence, signal-to-noise, cognitive load |
| Edward Tufte (*Visual Display of Quantitative Information*) | Data-ink ratio, sparklines, small multiples — foundational visualization principles |
| New Relic Pathpoint | Business journey visualization pattern — stages, steps, signals mapped to business flows |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA04.1](ka04-monitoring-visualization.md#dashboard-design-standards) Dashboard Design & Standards | **Current** | Rich, practitioner-actionable. Design principles, level patterns, trust hierarchy, early-adoption adjustments. |
| [KA04.2](ka04-monitoring-visualization.md#real-time-monitoring) Real-Time Monitoring | **Current** | Real pipeline documented. Synthetics reference, alert routing patterns. |
| [KA04.3](ka04-monitoring-visualization.md#cross-signal-correlation) Cross-Signal Correlation | **Seeded** | Cross-layer correlation is settled — seven named patterns documented on this page. The gap is cross-service/cross-tool correlation: no unified methodology for correlating across service boundaries and platforms. **This is the primary gap in KA04.** |
| [KA04.4](ka04-monitoring-visualization.md#topology-dependency-visualization) Topology & Dependency Visualization | **Current** | Three approaches documented (business view, terrain tool, pathpoint patterns). |
| [KA04.5](ka04-monitoring-visualization.md#business-health-views) Business Health Views | **Current** | Aggregate health view design principles + director deep dive worked example. |
| [KA04.6](ka04-monitoring-visualization.md#exploratory-analysis-hypothesis-driven-investigation) Exploratory Analysis | **Current** | Comprehensive 5-phase investigation framework. Failure mode templates. Visualization catalog. |

**KA04 summary:** 5/6 topics Current, 1 Seeded. The gap is [KA04.3](ka04-monitoring-visualization.md#cross-signal-correlation) (Cross-Signal Correlation) — the cross-layer patterns are settled, but there's no unified methodology for correlating signals across services and tools.
