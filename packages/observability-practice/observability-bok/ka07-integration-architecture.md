# KA07 — Integration & Architecture

**Category:** Enabling Practice
**Primary owner:** Architecture / Platform
**Question this KA answers:** How does observability connect to enterprise systems?

---

## 1. Purpose & Scope

This KA covers how observability connects to adjacent enterprise systems and initiatives. CMDB, CI/CD pipelines, regulatory frameworks, business service frameworks, and the architectural decisions that determine whether observability fits into the enterprise or sits beside it. KA07 is the integration surface — where the business observability practice meets the rest of the enterprise.

**What's in scope:**
- CMDB and service registry integration — connecting observability to configuration management
- CI/CD pipeline integration — embedding observability into software delivery
- Regulatory and compliance frameworks — alignment with permit-to-operate, audit
- Adjacent initiative alignment — business service frameworks, business journey mapping, BIAN
- Enterprise architecture positioning — where observability sits in TOGAF, BIAN, ITIL

**What's out of scope:**
- Internal platform architecture ([KA06](ka06-platform-tooling.md)) — KA07 is about external integration, [KA06](ka06-platform-tooling.md) is about internal platform
- Data governance ([KA08](ka08-data-governance.md)) — KA07 is the integration surface, [KA08](ka08-data-governance.md) is the governance model

---

## 2. Domain Knowledge

### CMDB & Service Registry Integration

The CMDB application ID is the primary join key between the business observability catalog and enterprise systems. Every service entry has an `app_id` field (required, FK) that ties it to the CMDB entry.

**The CMDB granularity problem:** In large enterprises, a single CMDB application ID commonly aggregates dozens of separate code repositories spanning multiple business capabilities. Application sunrise — registering a new application — is often burdensome enough that teams deploy new capabilities inside existing app IDs instead. As a result, "restore Application X" in a critical-path inventory may encompass several distinct business capabilities — only some of which are actually critical.

Business observability addresses this through service definition pattern #2 ("Capability within an Application") — defining health at the business capability level even when the CMDB entry is at the monolithic application level. The business observability service registry complements the CMDB, not duplicates it.

IT service management integration (e.g., ServiceNow) is documented for one reference implementation. An org-hierarchy reference table provides the organizational context — product line, product, service — for every service.

### CI/CD Pipeline Integration

Embedding observability into the software delivery pipeline. The quality gate concept ([KA03.1](ka03-standards-quality.md#quality-gates-pipeline-integration)) provides the mechanism: the Service Status evaluation could be integrated into CI/CD as a deployment gate — "this service's observability score must be above N before deploying to production."

Pipeline integration draws on OpenTelemetry CI/CD patterns and observability-as-code practice. The industry OaC pattern — *generated monitoring artifacts* (alert rules, dashboard configs) versioned alongside application code, changed through the same review process, deployed through the same pipeline — is the target architecture; in the reference implementation, pipeline integration is not yet established (KA07.2 is audited Missing below). The pattern's scope matters: it applies to the generated operational artifacts. The observability *definitions* themselves (expectations, signals, business context) live in the PO-owned system of record and change through the definition workflow — that separate, PO-driven path is by design, not a gap the pipeline closes.

### Regulatory & Compliance Frameworks

Observability intersects regulatory requirements through:

- **BIA (Business Impact Analysis)** — regulatory frameworks assess recovery requirements. Business observability's Business Impact quantification provides complementary real-time impact data that complements point-in-time BIA assessments.
- **Permit-to-operate (PTO)** — deployment governance that requires operational readiness evidence. The business observability operational readiness checklist (dashboard, runbook, alerts, escalation) contributes to PTO evidence.
- **Audit requirements** — audit trail fields (created_at, modified_at) on all service definitions, combined with schema versioning and migration history, provide change traceability.

BIAN-style functional decomposition provides industry-specific architectural positioning. In banking, 251 BIAN service domain specifications inform how observability services map to functional categories.

### Adjacent Initiative Alignment

Business observability typically operates alongside several enterprise initiatives:

- **Business service frameworks** — authoritative topology maps of what supports what. The frameworks are topology; business observability is semantics. The frameworks map the chain from products to applications. Business observability defines what "healthy" means at each node. Neither waits for the other. Useful framing: the service framework is the fire-escape plan; business observability is the smoke detector.
- **Business journey mapping** — end-to-end customer experience flows spanning multiple services. Business observability provides health definitions at each step; journey mapping provides the flow context.
- **BIAN (Banking Industry Architecture Network)** — canonical functional decomposition of banking capabilities. Business observability uses BIAN-informed categories for service classification (e.g., a `functionalCategory` field on each service).

### Enterprise Architecture Positioning

Where observability sits in the enterprise architecture landscape:

| Framework | Observability Positioning |
|-----------|-------------------------|
| BIAN | Service domains provide functional categorization. Where BIAN applies, business observability maps services to BIAN categories for shared vocabulary — BIAN is not required; any business service can be measured whether BIAN-aligned or not. |
| ITIL 4 | Monitoring and Event Management practice. Business observability adds business context that ITIL's practice doesn't define. |
| TOGAF | Application and Technology layers. Business observability operates at the Business Architecture layer — defining business health for technology services. |
| COBIT | Monitor, Evaluate, and Assess domain. Business observability provides the structured definitions COBIT requires. |

---

## 3. Practices & Processes

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Quality gate standards | [KA03](ka03-standards-quality.md) | Standards that integration enforces in CI/CD |
| Architecture constraints | Enterprise Architecture | Determines where observability fits |
| CMDB data, service registries | Enterprise systems | Service identification, org mapping |
| Business service framework data | Regulatory/resiliency teams | Critical path identification, prioritization |

| Output | To | Purpose |
|--------|-----|---------|
| Integration designs | [KA06](ka06-platform-tooling.md) (Platform) | How the platform connects to enterprise systems |
| Compliance evidence | [KA03](ka03-standards-quality.md) (Standards) | Regulatory alignment evidence |
| Architecture positioning | [KA09](ka09-strategy-program.md) (Strategy) | Where observability fits in enterprise strategy |

---

## 4. Roles & Responsibilities

| Activity | Architecture | Platform/SRE | Practice Lead |
|----------|:---:|:---:|:---:|
| Enterprise architecture alignment | **Own** | Contribute | Inform |
| CMDB integration design | Contribute | **Own** | — |
| CI/CD pipeline integration | Contribute | **Own** | — |
| Regulatory mapping | Contribute | — | **Own** |
| Adjacent initiative coordination | Contribute | — | **Own** |

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA07 knowledge — a practitioner doing integration and architecture work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-04 Service Profile Template](instruments/in-04-service-profile-template.md) | Definition | CMDB app ID mapping — connects services to enterprise configuration management |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| Business service framework reference | Service hierarchy, critical-path inventory, relationship to business observability, CMDB granularity analysis |
| BIAN evaluation | Full BIAN integration research with service-domain specifications |
| Industry frameworks landscape | BIAN, ITIL, COBIT, TOGAF positioning |
| Integration business view | Business function → technology capability mapping |
| Synthetics integration reference | Worked ServiceNow integration example |

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA03](ka03-standards-quality.md) — Standards & Quality | KA07 **enables** [KA03](ka03-standards-quality.md) | Architectural integration makes quality gate enforcement possible |
| [KA08](ka08-data-governance.md) — Data Management & Governance | KA07 **informs** [KA08](ka08-data-governance.md) | Integration points determine governance scope |
| [KA09](ka09-strategy-program.md) — Strategy & Program Management | KA07 **constrains** [KA09](ka09-strategy-program.md) | Enterprise architecture constrains strategic options |
| [KA06](ka06-platform-tooling.md) — Platform & Tooling | KA07 is **enabled by** [KA06](ka06-platform-tooling.md) | Platform and tooling provide the runtime that makes integration architecture executable |
| [KA01](ka01-business-context.md) — Business Context | KA07 **feeds** [KA01](ka01-business-context.md) | CMDB and service-hierarchy data provide the raw material for service identification |

### External References

| Reference | Relevance |
|-----------|-----------|
| BIAN Service Domains | Banking functional decomposition — 251 specifications |
| ITIL 4 Monitoring & Event Management | Enterprise service management context for observability |
| TOGAF ADM | Enterprise architecture method — where observability fits |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA07.1](ka07-integration-architecture.md#cmdb-service-registry-integration) CMDB & Service Registry Integration | **Current** | The reference implementation documents a working ServiceNow integration and registry mapping tables. CMDB granularity problem documented on-page. |
| [KA07.2](ka07-integration-architecture.md#cicd-pipeline-integration) CI/CD Pipeline Integration | **Missing** | Quality gate concept exists but no pipeline integration design. External: OTel CI/CD patterns. |
| [KA07.3](ka07-integration-architecture.md#regulatory-compliance-frameworks) Regulatory & Compliance Frameworks | **Seeded** | A BIAN evaluation exists in the reference implementation. Business service framework pattern documented on-page. A reusable compliance-mapping methodology has not yet been authored. |
| [KA07.4](ka07-integration-architecture.md#adjacent-initiative-alignment) Adjacent Initiative Alignment | **Seeded** | Business service frameworks and journey mapping are treated strategically on-page. Not yet operationalized into integration design. |
| [KA07.5](ka07-integration-architecture.md#enterprise-architecture-positioning) Enterprise Architecture Positioning | **Current** | BIAN, ITIL, COBIT, TOGAF positioning documented. |

**KA07 summary:** 2/5 Current, 2 Seeded, 1 Missing. [KA07.2](ka07-integration-architecture.md#cicd-pipeline-integration) (CI/CD Pipeline Integration) is the Missing topic — the mechanism to embed observability quality gates into the delivery pipeline.
