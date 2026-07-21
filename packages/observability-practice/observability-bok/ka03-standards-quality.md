# KA03 — Standards & Quality Assurance

**Category:** Core Practice

**Lifecycle stage:** Enforce

**Primary owner:** Platform / Engineering

**Question this KA answers:** How do we ensure standards before production?

---

## 1. Purpose & Scope

This KA covers how observability standards are enforced before production. Signal design ([KA02](ka02-signal-design.md)) produces signal definitions. KA03 validates that those definitions meet quality standards before they reach dashboards and alerting systems. Without enforcement, observability debt accumulates — signals exist but are incomplete, inconsistent, or untrustworthy.

**What's in scope:**

- Quality gates embedded in CI/CD and service onboarding workflows
- Observability readiness criteria — what "production-ready" means for observability
- Compliance and regulatory alignment — permit-to-operate, audit requirements
- Template and blueprint standards — reusable patterns teams follow
- Validation and verification — automated checks against schema and quality

**What's out of scope:**

- Signal design ([KA02](ka02-signal-design.md)) — KA03 enforces what [KA02](ka02-signal-design.md) produces
- Platform tooling ([KA06](ka06-platform-tooling.md)) — KA03 defines standards, [KA06](ka06-platform-tooling.md) implements the enforcement infrastructure
- Data governance ([KA08](ka08-data-governance.md)) — KA03 is the enforcement arm, [KA08](ka08-data-governance.md) governs the broader data management practice

---

## 2. Domain Knowledge

### Quality Gates & Pipeline Integration

The Service Status evaluation ([IN-08](instruments/in-08-service-status-template.md)) is the primary quality gate. It computes a completeness score (0-100) across five dimensions for every service:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Layer Coverage | 20% | Does the service have signals across all 4 layers? |
| Signal Completeness | 30% | For each signal, are required fields filled? |
| Threshold Coverage | 15% | Do health signals have alert/page thresholds? |
| Traceability Coverage | 20% | Does every stakeholder have at least one linked signal? |
| Operational Readiness | 15% | Are dashboard, runbook, alert targets, and escalation defined? |

The score is computed on every access — never stored. A service that adds a signal immediately sees its score change. This is the observability equivalent of a code coverage metric — it tells you how complete your observability definition is.

**Progressive scoring matters:** A newly created service scores 0%. As the PO adds stakeholders, signals, traceability mappings, and operational config, the score rises. Teams see progress incrementally rather than facing a "you must complete everything" barrier.

### Observability Readiness Criteria

"Production-ready" for observability means four operational elements are in place:

1. **Alert notification targets** — who gets notified when thresholds breach
2. **Dashboard URL** — where the team goes to see service health
3. **Runbook URL** — the documented response procedure
4. **Escalation policy** — who to contact when the first responder can't resolve

Each is a boolean check. The operational readiness dimension scores the percentage of these four that are configured. A service with all four is operationally ready. A service with zero is "defined but not operational."

### Compliance & Regulatory Alignment

Observability intersects regulatory requirements in two ways:

1. **Permit-to-operate (PTO)** — enterprise production-deployment governance typically requires evidence that operational capabilities exist. Business observability definitions contribute to the evidence base — "this service has defined health signals, alert thresholds, and a runbook."
2. **Enterprise critical-products frameworks** — regulatory compliance frameworks often define structured recovery capabilities for the most critical products. Business observability provides the health-definition layer that complements recovery-planning frameworks.

Compliance integration attaches to business observability through the legal-risk impact category, audit-trail fields on every signal, and alignment with enterprise critical-product frameworks. The operational discipline: every signal that serves a regulated expectation has audit trail, and every impact category that includes legal-risk has threshold review at the cadence the regulation requires.

### Template & Blueprint Standards

Reusable patterns teams follow when defining observability for their services. The concept of "standards and guidance" — documented approaches that ensure consistency across teams without requiring each team to invent their own patterns.

**Established template families:**

- Stakeholder context guidance — sentence templates, quality checklists, and prompt templates for generating stakeholder expectations
- Discovery template — structured approach for initial service analysis
- Case study template — documenting the onboarding experience for a specific service
- CSV templates — service, expectations, signals, impact, and operational input feeding the system of record

**What's missing:** A unified blueprint library. A recurring stakeholder ask is "standard practices, guidelines, recommendations" — and the typical response is "the templates exist, but scattered." Teams need a single "here are the standards" artifact a lead can hand to POs. This is typically the most stakeholder-visible gap in KA03.

### Validation & Verification

Automated checks that observability artifacts meet schema and quality:

- **Schema validation** — CSV data must match the system-of-record template format. Field types, required fields, enum values are validated at import.
- **Completeness validation** — the Service Status evaluation checks signal completeness per signal type (required fields vary: ratio needs numerator + denominator, threshold needs operator + value + unit).
- **Traceability validation** — both directions of the semantic chain: every stakeholder expectation should have at least one linked signal (unmapped stakeholders are flagged), and every business-layer signal should trace to a stakeholder expectation it serves (an orphan signal — one with no expectation behind it — is as much a chain violation as an unmeasured expectation).
- **Scoping check** — a heuristic warning when a service carries more than 7 PO-defined key health indicators, suggesting the service boundary may need decomposition ([KA01](ka01-business-context.md)'s two-boundary rule). Total signal count is not the boundary — 20–50 developer-defined diagnostic signals beneath the PO's indicators are expected, not a violation. Guidance, not a hard block.

---

## 3. Practices & Processes

### The Enforcement Workflow

```
1. PO completes service profile  → KA01 output: stakeholders, expectations
2. Dev implements signals         → KA02 output: queries, data sources
3. Quality gate evaluates         → KA03: Service Status score computed
4. Gaps visible                   → Score shows what's missing, per dimension
5. Team fills gaps                → Iterate until quality threshold met
6. Operational readiness          → Dashboard, runbook, alerts, escalation configured
7. Production-ready               → Service has passed all quality dimensions
```

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Signal definitions | [KA02](ka02-signal-design.md) | Subject of quality validation |
| Service profiles | [KA01](ka01-business-context.md) | Completeness assessment |
| Governance policies | [KA08](ka08-data-governance.md) | Standards that enforcement upholds |

| Output | To | Purpose |
|--------|-----|---------|
| Quality scores | [KA04](ka04-monitoring-visualization.md) (dashboards) | Coverage metrics visible in portfolio views |
| Validation results | [KA12](ka12-adoption-enablement.md) (adoption) | Quality gate is part of the onboarding workflow |
| Compliance evidence | [KA07](ka07-integration-architecture.md) (integration) | Standards compliance feeds regulatory evidence |

---

## 4. Roles & Responsibilities

| Activity | Product Owner | Developer | Platform/SRE | Practice Lead |
|----------|:---:|:---:|:---:|:---:|
| Define quality standards | — | Contribute | Contribute | **Own** |
| Implement quality gates | — | — | **Own** | Review |
| Review service completeness | **Own** (their services) | — | — | Review (portfolio) |
| Maintain templates | — | — | — | **Own** |
| Compliance mapping | — | — | Contribute | **Own** |

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA03 knowledge — a practitioner doing standards and quality work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-01 Service Maturity Model](instruments/in-01-service-maturity-model.md) | Assessment | Operationalized stage requires KA03 enforcement — standards applied before production |
| [IN-08 Service Status Template](instruments/in-08-service-status-template.md) | Definition | Tracks operational readiness — the quality gate that measures completeness across 5 dimensions |
| [IN-15 Dashboard Generation Methodology](instruments/in-15-dashboard-generation-methodology.md) | Production | Codifies dashboard standards — ensures consistency across all generated dashboards |
| [IN-23 Observability Standard](instruments/in-23-observability-standard.md) | Definition | The standard KA03 enforcement applies — placement as distance from the definition |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| Service Status specification | 5-dimension evaluation, weighted scoring, progressive completeness |
| Stakeholder context guidance | Quality checklist, sentence templates, AI prompt template |
| Structured input templates | Structured CSV templates capturing a complete service profile, with schema validation |
| Enterprise service-hierarchy reference | Regulatory context: enterprise critical-products frameworks, business impact analysis, compliance alignment |

### Techniques

- **Progressive completeness scoring** — quality gate that shows progress, not just pass/fail. Encourages incremental improvement.
- **Per-dimension visibility** — teams see exactly which dimension is low, not just an aggregate score. "Your traceability is 33%" is actionable; "your score is 45" is not.
- **Scoping heuristic** — warn when PO-defined key health indicators exceed 7 (the decomposition signal), not on total signal count. Not a hard block — the PO sees guidance, not an error.

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA02](ka02-signal-design.md) — Signal Design | KA03 **depends on** [KA02](ka02-signal-design.md) | Standards enforce what signal design specifies |
| [KA07](ka07-integration-architecture.md) — Integration & Architecture | KA03 **enables** [KA07](ka07-integration-architecture.md) | Quality gates integrate into CI/CD and enterprise architecture |
| [KA08](ka08-data-governance.md) — Data Management & Governance | KA03 **governs** for [KA08](ka08-data-governance.md) | Standards are the enforcement arm of governance |
| [KA04](ka04-monitoring-visualization.md) — Monitoring & Visualization | KA03 **feeds** [KA04](ka04-monitoring-visualization.md) | Quality-validated signals reach production dashboards |

### External References

| Reference | Relevance |
|-----------|-----------|
| ITIL Service Management (quality assurance practices) | Standards enforcement as a practice discipline |
| ISO 22301 (Business Continuity) | BIA framework — compliance requirements for operational readiness |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA03.1](ka03-standards-quality.md#quality-gates-pipeline-integration) Quality Gates & Pipeline Integration | **Current** | Actionable quality gate: 5-dimension evaluation with weighted scoring. |
| [KA03.2](ka03-standards-quality.md#observability-readiness-criteria) Observability Readiness Criteria | **Current** | Concrete 4-item checklist (dashboard, runbook, alerts, escalation). |
| [KA03.3](ka03-standards-quality.md#compliance-regulatory-alignment) Compliance & Regulatory Alignment | **Seeded** | Conceptually mapped (legal-risk category, audit-trail fields). Not yet a repeatable compliance-mapping methodology. |
| [KA03.4](ka03-standards-quality.md#template-blueprint-standards) Template & Blueprint Standards | **Seeded** | Individual templates exist but are scattered. No unified blueprint library yet — the most stakeholder-visible gap. Promoting to Current requires a unified blueprint library that standardizes template families across [KA01](ka01-business-context.md)–[KA02](ka02-signal-design.md). |
| [KA03.5](ka03-standards-quality.md#validation-verification) Validation & Verification | **Current** | Concrete validation criteria: schema, completeness, traceability, scoping. |

**KA03 summary:** 3/5 Current, 2 Seeded. [KA03.4](ka03-standards-quality.md#template-blueprint-standards) (Template & Blueprint Standards) is the gap that matters most to stakeholders — the typical "standards and guidance" ask does not have a unified artifact answer.
