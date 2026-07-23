# KA01 — Business Context & Service Definition

**Category:** Core Practice

**Lifecycle stage:** Define

**Primary owner:** Product Owner

**Question this KA answers:** What does "healthy" mean in business terms?

---

## 1. Purpose & Scope

This KA covers the foundational layer of observability: defining what matters to the business before any signal is designed, any dashboard is built, or any alert is configured. Without business context, signals are just data. With it, every metric connects to a stakeholder, an expectation, and a consequence.

**What's in scope:**

- Identifying who depends on a service and what they expect
- Mapping business functions into observable units
- Defining service boundaries (what constitutes "a service" for observability)
- Classifying impact by category (customer, financial, compliance, operational)
- Constructing service profiles — the structured artifact that captures all of the above
- Defining SLOs and error budgets that translate expectations into quantitative targets

**What's out of scope:**

- Signal design and instrumentation ([KA02](ka02-signal-design.md)) — KA01 defines WHAT to measure, [KA02](ka02-signal-design.md) defines HOW
- Platform tooling and data source selection ([KA06](ka06-platform-tooling.md))
- Live monitoring and dashboards ([KA04](ka04-monitoring-visualization.md)) — those consume KA01's output
- Functional requirements for the application itself — business observability captures observability requirements alongside functional requirements, not instead of them

---

## 2. Domain Knowledge

### The Four-Layer Model

Observability signals organize into four layers, presented outside-in — business-first. The first two are the business observability contribution — the business context layer this methodology exists to add. The last two are traditional monitoring.

| Layer | Question | Owner |
|-------|----------|-------|
| Business Health | Is the stakeholder expectation being met? | Product Owner |
| Business Impact | How bad is it when we fail? | PO + Ops/Compliance |
| Application | Is the workflow executing correctly? | Dev / QA |
| System | Is the platform operational? | SRE / Platform |

Application and System validate the mechanism (up, fast, correct). Business Health validates the intended outcome. Business Impact quantifies the consequence when outcomes miss. A service can be green on Application and System (workflows running, infrastructure healthy) while failing on Business Health (business outcomes not met). That gap is why the business layers exist.

Every signal traces back to a business reason through the semantic chain:

```
[Stakeholder] has an [Expectation]
  which is measured by a [Business Health Signal] with a target and formula
    supported by [Application Signals] and [System Signals]
      if the expectation is breached → [Business Impact Signal]: category + magnitude
        → [Alert] → [Owner + Next Action]
```

[KA04](ka04-monitoring-visualization.md) consumes this ordering when it renders views: business context leads every view — status lists at the portfolio levels, stakeholder expectations opening Service Detail — with mechanism detail below. See [KA04](ka04-monitoring-visualization.md)'s business-first sequencing for the exact Service Detail order.

### Stakeholder Identification & Expectations

A stakeholder expectation captures who cares about a service and what happens to the business if the service fails them. Each expectation has:

- **Stakeholder** — a specific group, not a generic label. "Mortgage applicants" not "customers." "Loan processors" not "internal users." The specificity matters because different stakeholders have different expectations for the same service.
- **Expectation statement** — what the stakeholder expects, in active voice with a quality or timing constraint. "Wire transfers complete on scheduled closing date." "Credit checks return valid scores within acceptable timeframe."
- **Impact category** — one of four fixed categories: Customer Experience, Financial, Legal/Compliance Risk, Operational ([IN-06](instruments/in-06-stakeholder-expectation-template.md) carries the recorded field values).
- **Impact description** — the specific consequence when the expectation is not met, prefixed with its category: "Customer Impact: Homebuyers cannot complete purchase on scheduled date."
- **Priority** — CRITICAL, HIGH, MEDIUM, or LOW, reflecting business criticality.

Each service gets 3-5 stakeholder context rows. This is forced prioritization — the PO must decide what matters most, not list everything. A typical service has 1-2 CRITICAL/HIGH and 1-2 MEDIUM expectations, spanning at least two stakeholder types (e.g., customer + business unit).

Each row reads as a complete story: "As [stakeholder], I expect [X]. If broken: [impact]."

### Business Function Mapping

Business functions decompose into observable units using an enterprise business service hierarchy. A typical structure:

```
Operating Segment → Business Group → Products/Services → Service Offerings → Enablers
```

Business observability does not depend on an enterprise service framework as a prerequisite. It picks the service boundary based on where health is meaningful, not where the service framework or CMDB drew the organizational box. Three service definition patterns exist:

1. **CMDB Application** — one app, one service (e.g., "Wire Transfer Engine")
2. **Capability within an Application** — one function inside a large app (e.g., "Appraisal Order Processing" within a large lending platform). This pattern exists because in large-enterprise configuration management databases (CMDBs), a single application ID commonly aggregates dozens of separate code repositories — the CMDB entry is an organizational artifact, not an architectural unit.
3. **Business Capability spanning Applications** — stakeholder-meaningful process across multiple apps (e.g., "Mortgage Origination" spanning credit check, appraisal, underwriting, closing, funding)

The service definition resolves THROUGH adoption, not BEFORE it. The discipline: "We don't need a perfect definition of a service — we need a clear definition of what 'working' means for something we care about."

**How big should a service be?** The scoping discipline is a two-boundary rule. The Product Owner defines **3–7 key health indicators** per service — a human-cognition bound consistent with Google SRE's "five or fewer" SLO guidance. Developers define **20–50 detailed diagnostic signals** beneath them, mapped to telemetry. The boundary applies to what the PO defines and monitors, not to what the system captures underneath — rich diagnostic telemetry below the PO's indicators is expected, not a scoping violation. The count is design feedback: more than 7 PO-level indicators suggests the service boundary is too wide and should decompose (often into pattern 2 capabilities).

### Impact Category Classification

Four fixed categories classify the type of business damage when an expectation is not met:

| Category | What it measures | Example |
|----------|-----------------|---------|
| Customer Experience | External customers unable to complete transactions or receive service | Homebuyers cannot complete purchase on scheduled date |
| Financial | Revenue at risk, transaction volume affected, recovery costs | Lost transaction revenue and potential customer churn |
| Legal/Compliance Risk | Regulatory violations, compliance breaches, enforcement actions | US Fair Credit Reporting Act (FCRA) 30-day timing requirement violation |
| Operational | Manual workarounds, reduced team capacity, escalation volume | Customer service overwhelmed with payment failure inquiries |

Business Impact quantifies these categories with concrete metrics: `customers_affected`, `dollars_at_risk`, `compliance_cases`, `ops_minutes_added`. Each metric attaches to a specific category, producing executive-readable impact statements.

### Service Profile Construction

A service profile is the structured artifact that captures business context for a single service. It is the root entity — stakeholders, signals, traceability, and operational config all attach to it.

A profile captures:

- **Service identity** — name, business purpose, tier (1 = most critical, 6 = least), org placement, CMDB application ID, functional category informed by banking-industry service taxonomies (e.g., BIAN)
- **Stakeholder expectations** — who cares and what they need, classified by impact category (3-5 rows per service, forced prioritization)
- **Health signals** — what "working" looks like, quantified as SLOs with targets, time windows, and budgeting methods
- **Impact signals** — what failure costs, quantified across the four impact categories
- **Signal-to-stakeholder traceability** — every signal maps to the stakeholder expectation it serves, ensuring no signal exists without business justification and no stakeholder expectation exists without a signal measuring it. Traceability is a data-model relationship produced by the capture structure itself — each signal is captured inside its stakeholder's chain — not a documentation convention maintained by hand
- **Operational readiness** — dashboard URL, runbook URL, alert notification targets, escalation policy

Completeness is measured by the Service Status evaluation — a computed score (0-100) across five dimensions: layer coverage, signal completeness, threshold coverage, traceability coverage, and operational readiness (definitions and weights in [KA03](ka03-standards-quality.md)). A score below threshold means the profile has known gaps; the score always reflects current state.

With AI-assisted pre-population from existing team documentation, a first profile is well under an hour; subsequent profiles are faster because the patterns are established and team familiarity compounds.

### SLO Definition & Error Budget Allocation

SLOs translate stakeholder expectations into quantitative targets. An SLO has:

- A **target** (e.g., 99.5%) — the percentage at which the expectation is "met"
- A **time window** (e.g., 30 days rolling) — the measurement period
- A **budgeting method** — Occurrences (% of events), Timeslices (% of time intervals), or RatioTimeslices (ratio within each interval), per the OpenSLO specification's taxonomy
- A **rationale** — why this target, not higher or lower

Error budgets make reliability trade-offs explicit. If the SLO is 99.5% over 30 days, the error budget is 0.5% — roughly 3 hours and 36 minutes of allowed downtime. When the budget is consumed, the team prioritizes reliability over new features. When budget remains, the team has room for velocity. "Error budget" is bridge vocabulary from the SRE side: useful when working with SRE-fluent teams, not a term the practice asks Product Owners to adopt — POs speak expectations and health signals; the budget mechanics live with the teams that operate them.

Health signals are the measurement mechanism for SLOs. Each Business Health signal is either:

- **sli_ratio** — good events / total events (e.g., 99.5% of page loads complete in < 2 seconds)
- **sli_threshold** — metric vs. absolute limit (e.g., average response time stays below 500ms)

The PO defines the SLO (what and why). The Developer implements the signal (how to measure it). The Platform Engineer configures alert/page thresholds (when to notify). This three-actor ownership model is the defining characteristic of Business Health signals.

---

## 3. Practices & Processes

### The Service Definition Workflow

```
1. Establish service context → PO names the service, its business purpose, org placement,
                               dependencies, and business-process participation
2. Walk stakeholder chains   → for each stakeholder, one complete chain: who they are, what
                               they expect, and the Business Health signal that measures each
                               expectation — captured together, so signal-to-expectation
                               traceability is structural (produced by the capture itself,
                               never reconnected in a separate mapping step)
3. Apply the coverage gate   → before leaving a stakeholder's chain: does every expectation
                               have a signal measuring it?
4. Define impact             → PO creates Business Impact signals quantifying failure
                               consequences, linked to the stakeholder concerns they assess
5. Evaluate and verify       → Service Status score shows completeness across 5 dimensions,
                               and the capture instrument runs verification — cross-reference
                               integrity checks plus an independent content check against the
                               source material — before the profile is presented for review
```

The capture order follows the PO's reasoning path — stakeholder by stakeholder, expectation to signal — not entity type by entity type. Each chain produces structured output that feeds the next step. The PO's work in steps 1-4 produces the business context that Developers ([KA02](ka02-signal-design.md)) and Platform Engineers ([KA03](ka03-standards-quality.md), [KA04](ka04-monitoring-visualization.md)) need to do their work.

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| CMDB application inventory | Enterprise systems | Service identification, app ID mapping |
| Business service framework data (where available) | Regulatory/resiliency teams | Service prioritization, critical path identification |
| Existing Confluence/Jira content | Product teams | AI-assisted pre-population of profiles |
| Stakeholder conversations | PO domain knowledge | Expectation statements, impact assessment |

| Output | To | Purpose |
|--------|-----|---------|
| Service profile (complete) | [KA02](ka02-signal-design.md) (Signal Design) | Business context determines what signals to design |
| Stakeholder expectations | [KA05](ka05-incident-response.md) (Incident Response) | Business context determines incident severity and triage priority |
| Impact categories | [KA04](ka04-monitoring-visualization.md) (Monitoring & Visualization) | Dashboard presentation and executive tile content |
| SLO targets | [KA08](ka08-data-governance.md) (Data Governance) | Data governance requirements tied to business criticality |

### The Lifecycle Feedback Loop

KA01 is the "Define" stage, but it is not a one-time activity. The observability lifecycle feeds back from Respond ([KA05](ka05-incident-response.md)) to Define (KA01): incidents reveal business context gaps. A postmortem that discovers "we didn't know who the affected stakeholders were" is a KA01 gap, not a [KA05](ka05-incident-response.md) failure. The service profile is evergreen — defined once, reviewed when the service changes significantly or when incidents expose gaps.

---

## 4. Roles & Responsibilities

| Activity | Product Owner | Developer | Platform/SRE | Leadership |
|----------|:---:|:---:|:---:|:---:|
| Name and scope the service | **Own** | Inform | — | — |
| Identify stakeholders | **Own** | — | — | Validate |
| Write expectation statements | **Own** | Review | — | — |
| Classify impact categories | **Own** | — | — | Validate |
| Set SLO targets | **Own** | Advise (feasibility) | Advise (operational) | Approve (critical) |
| Construct service profile | **Own** | Contribute (tech fields) | Contribute (ops fields) | — |
| Review profile completeness | **Own** | — | — | Periodic review |

The PO is the primary actor. Developers advise on technical feasibility of SLOs ("can we measure this?"). Platform/SRE advises on operational implications ("can we alert on this?"). Leadership validates that the right stakeholders and impact categories are captured for high-tier services.

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA01 knowledge — a practitioner doing business context work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-01 Service Maturity Model](instruments/in-01-service-maturity-model.md) | Assessment | Measures how far a service has progressed — Contextualized stage = KA01 knowledge applied |
| [IN-04 Service Profile Template](instruments/in-04-service-profile-template.md) | Definition | Captures service identity, purpose, tier, org placement — the root entity |
| [IN-05 Signal Definition Template](instruments/in-05-signal-definition-template.md) | Definition | Defines health signals with SLO targets — translates KA01 expectations into measurable signals |
| [IN-06 Stakeholder Expectation Template](instruments/in-06-stakeholder-expectation-template.md) | Definition | Captures who cares and what happens when the service fails them |
| [IN-09 Signal Specification Format](instruments/in-09-signal-specification-format.md) | Definition | Reference spec for signal types and ownership model |
| [IN-10 Story Factory](instruments/in-10-story-factory.md) | Production | Generates user stories from service profiles — 1 PO action → development-ready stories |
| [IN-13 Playbook Factory](instruments/in-13-playbook-factory.md) | Production | Generates playbooks from service context and impact categories |
| [IN-16 Onboarding Simulation](instruments/in-16-onboarding-simulation.md) | Adoption | Guided walkthrough of a PO's first service profile — walks through KA01's service definition workflow |
| [IN-19 Discovery Dialogue Protocol](instruments/in-19-discovery-dialogue-protocol.md) | Adoption | Facilitation guide for the PO conversation that produces a service profile |
| [IN-24 First-Process Run Plan](instruments/in-24-first-process-run-plan.md) | Adoption | Sequences KA01 capture into a team's first executable walk — session order, roles, outputs |
| [IN-23 Observability Standard](instruments/in-23-observability-standard.md) | Definition | The written definition of good — the chain positions KA01 content must fill |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| Four-Layer Model reference | Layer definitions, semantic chain, comparative view, domain walkthroughs, acceptance checklist |
| Stakeholder context guidance | Field completion guide, sentence templates, AI agent prompt template, quality checklist |
| Service registration specification | Data model, business rules, API spec for service identity |
| Stakeholder expectations specification | Data model, business rules, API spec for stakeholder capture |
| Health Signals specification | Signal types, three-actor ownership, polymorphic data model |
| Service Status specification | Completeness evaluation: 5 dimensions, weighted scoring |
| Enterprise service hierarchy reference | Service taxonomy (e.g., BIAN service domains), critical-path mapping, regulatory prioritization |
| Scope boundary framing | Reusable "what business observability is and isn't" articulation |

### Techniques

- **Forced prioritization** — 3-5 stakeholder rows per service. Not all stakeholders, the most important ones.
- **Sentence templates** — three templates for expectation statements ensure consistency: "[Service output] + [action verb] + [quality/timing constraint]", "[Service action] + [completion verb] + [timing/quality constraint]", "[Service] + [maintains/meets] + [standard/requirement]"
- **AI-assisted pre-population** — an AI agent prompt template generates initial stakeholder rows from service context. The PO reviews and adjusts rather than writing from scratch.
- **Progressive completeness** — the Service Status evaluation scores profiles across 5 dimensions. Teams see what's complete and what's missing, advancing incrementally rather than requiring full completeness before any value is delivered.

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA02](ka02-signal-design.md) — Signal Design & Instrumentation | KA01 **feeds** [KA02](ka02-signal-design.md) | Business context determines what signals to design. A Developer cannot design signals without knowing what "healthy" means. |
| [KA05](ka05-incident-response.md) — Incident Management & Response | KA01 **feeds** [KA05](ka05-incident-response.md) | Business context determines incident severity. [KA05](ka05-incident-response.md) **feeds back** to KA01 — incidents reveal gaps in business context definitions. |
| [KA08](ka08-data-governance.md) — Data Management & Governance | KA01 **informs** [KA08](ka08-data-governance.md) | Business context determines data governance requirements — what needs to stay current, what's critical. |
| [KA07](ka07-integration-architecture.md) — Integration & Architecture | KA01 **depends on** [KA07](ka07-integration-architecture.md) | CMDB, service registry, and enterprise service-hierarchy data provide the raw material for service identification. |
| [KA09](ka09-strategy-program.md) — Strategy & Program Management | KA01 **informs** [KA09](ka09-strategy-program.md) | Aggregate business context across services feeds strategic prioritization and investment justification. |
| [KA04](ka04-monitoring-visualization.md) — Monitoring & Visualization | KA01 **feeds** [KA04](ka04-monitoring-visualization.md) | Business context determines dashboard content — expectations, impact categories, targets. |
| [KA13](ka13-continuous-improvement.md) — Continuous Improvement | KA01 **feeds** [KA13](ka13-continuous-improvement.md) | Service Understanding Documents capture understanding that runs ahead of the data model (schema-ahead content). When multiple SUDs capture the same concept without a matching data model field, that's a grounded signal for capability evolution — not speculative feature planning but documented understanding waiting for schema support. KA01 is the sensing mechanism; [KA13](ka13-continuous-improvement.md) is where the growth signal is acted on. |
| [KA12](ka12-adoption-enablement.md) — Adoption & Enablement | KA01 is **implemented by** [KA12](ka12-adoption-enablement.md) | Adoption & enablement operationalizes business-context definitions in team practice — the onboarding workflow is KA01 practice delivered to Product Owners. |

### External References

| Reference | Relevance |
|-----------|-----------|
| Google SRE Book (Beyer, Jones, Petoff, Murphy) | SLO/SLI framework, error budget concept |
| *Implementing Service Level Objectives* (Hidalgo) | Practical SLO implementation patterns |
| BIAN Service Domains | Functional category taxonomy for service classification |
| Ben Sigelman (LightStep/ServiceNow) | Change-based framing: observability primarily about detecting change — accelerate planned changes, respond to unplanned changes |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA01.1](ka01-business-context.md#stakeholder-identification-expectations) Stakeholder Identification & Expectations | **Current** | Practitioner guidance doc is actionable. Spec validates data model supports it. Sentence templates and AI prompt template included. |
| [KA01.2](ka01-business-context.md#business-function-mapping) Business Function Mapping | **Current** | Enterprise service-hierarchy reference pattern documented. Actionable for service scoping. |
| [KA01.3](ka01-business-context.md) Service Definition & Boundaries | **Current** | Three service patterns documented. Scope boundary principle established. |
| [KA01.4](ka01-business-context.md#impact-category-classification) Impact Category Classification | **Current** | Four categories defined with examples, impact description format with category prefix. Business Impact quantification documented. |
| [KA01.5](ka01-business-context.md#service-profile-construction) Service Profile Construction | **Current** | End-to-end: what a profile contains, how completeness is measured (5-dimension evaluation). API spec, data model, and BDD scenarios available. |
| [KA01.6](ka01-business-context.md#slo-definition-error-budget-allocation) SLO Definition & Error Budget | **Current** | Spec-level: sloTarget, 3 budgeting methods, time windows. Referenced: Google SRE, Hidalgo. |

**KA01 summary:** 6/6 topics Current. This is the strongest KA — production-spec quality across all topics.
