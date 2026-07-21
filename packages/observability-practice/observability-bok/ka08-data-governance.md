# KA08 — Data Management & Governance

**Category:** Enabling Practice

**Primary owner:** Practice Lead / Data Governance

**Question this KA answers:** How do we maintain data coherence at scale?

---

## 1. Purpose & Scope

This KA covers how the observability practice maintains data coherence at scale. Service catalog, naming standards, data quality, schema management, ownership accountability, and telemetry security. The hardest problem in any registry effort is keeping it current — KA08 is where that challenge lives.

**What's in scope:**

- Service catalog and capability registry — central inventory of services and metadata
- Naming standards and conventions — enterprise-wide naming consistency
- Data quality and currency — keeping the knowledge base current
- Schema management — data model evolution, versioning, migration
- Ownership and accountability — who maintains what
- Telemetry security, privacy, and access control

**What's out of scope:**

- Enforcement mechanisms ([KA03](ka03-standards-quality.md)) — KA08 defines governance, [KA03](ka03-standards-quality.md) enforces it
- Platform data storage ([KA06](ka06-platform-tooling.md)) — KA08 governs what's stored, [KA06](ka06-platform-tooling.md) manages how

---

## 2. Domain Knowledge

### Service Catalog & Capability Registry

The system-of-record is the service catalog that captures business observability data. Each service entry contains 15+ fields: identity (name, business purpose, tier), organizational context (org_id FK to the organizational hierarchy, app_id), ownership (product owner, technical owner), classification (functional category from BIAN-informed taxonomy, tags).

The catalog is the aggregate root — stakeholder expectations, signals, traceability mappings, and operational metadata all attach to service entries. Services with 3-4 stakeholder contexts each yield dozens of structured records capturing business context that previously existed only in people's heads.

### Naming Standards & Conventions

A domain vocabulary provides controlled terminology for business observability entities. Preferred terms, non-preferred alternatives, and disambiguation guidance ensure consistent language across sessions, documents, and team interactions.

Key naming conventions:

- **Service names:** `serviceName` (machine-friendly, kebab-case) + `displayName` (human-readable). Both required.
- **Signal names:** Same pattern — `signal_name` + `signal_display_name`.
- **Layer naming:** Prefer full names ("Business Health Signal," "System Signal") over L1/L2/L3/L4 shorthand — the shorthand collides with product-hierarchy notations used in many enterprise Product Operating Models.
- **Impact categories:** Four fixed values: `customer_experience`, `financial`, `legal_risk`, `operational`. No synonyms.

### Data Quality & Currency

The system of record tracks schema evolution through versioned migrations. Enhancement logs document what changed and why. CSV quality validation catches format issues at import.

**The currency challenge:** Service profiles degrade over time — stakeholders change, SLO targets need adjustment, new failure modes emerge. The Service Status evaluation ([KA03](ka03-standards-quality.md)) measures completeness at a point in time; keeping profiles current over time requires a separate mechanism. This is the "stale service catalog" problem every registry effort faces.

Two currency mechanisms: **reactive** — the postmortem feedback loop ([KA05](ka05-incident-response.md)) catches outdated definitions when incidents expose them. **Proactive** — scheduled profile reviews triggered by organizational change signals (team reorganization, product launches, SLO target changes). Mature practice runs both.

### Schema Management

Complete schema lifecycle documented:

- **Versioned DDL:** Schema definitions in SQL with version numbers
- **Migration scripts:** Transition scripts between schema versions
- **ORM layer:** Object-relational mapping for programmatic access
- **Propagation:** Schema changes must propagate to every downstream artifact — DDL, migrations, data access, import format, capture surfaces, dashboards, docs
- **Successor schema:** a designed next-generation schema is part of the lifecycle

A field-metadata registry is the source of truth for field definitions — schema changes require metadata regeneration.

### Ownership & Accountability

Audit trail fields (`created_at`, `modified_at`) exist on all records. The domain vocabulary defines role names (Product Owner, Developer, Platform Engineer). The three-actor ownership model for signals ([KA02](ka02-signal-design.md)) assigns specific field ownership per role.

The persistent accountability question: who keeps service X's profile current as team structures change? The PO creates the profile, but organizational changes (team moves, product pivots) can orphan profiles without a named steward to carry them forward. Audit fields (created_at, modified_at) detect staleness; an accountability model prevents it.

### Telemetry Security, Privacy & Access Control

Observability telemetry can contain PII (user IDs in logs, request parameters), sensitive business data, and regulated information. In banking, this intersects with regulatory compliance.

Telemetry security policy covers log sanitization (PII, secrets, sensitive business data), dashboard access control tied to data classification, and data-residency requirements for telemetry in regulated industries.

Prior art: DMBOK Data Security KA, ITIL Information Security Management practice.

---

## 3. Practices & Processes

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Service profiles | [KA01](ka01-business-context.md) | The data being governed |
| Quality standards | [KA03](ka03-standards-quality.md) | Enforcement of governance decisions |
| Integration points | [KA07](ka07-integration-architecture.md) | Determining governance scope |

| Output | To | Purpose |
|--------|-----|---------|
| Governed data | [KA01](ka01-business-context.md)-[KA05](ka05-incident-response.md) (all core practices) | Clean, current, consistent data for all practices |
| Governance health metrics | [KA13](ka13-continuous-improvement.md) (Continuous Improvement) | Data quality is a key practice health indicator |
| Naming standards | [KA10](ka10-stakeholder-engagement.md) (Stakeholder Communication) | Consistent language across enterprise communications |

---

## 4. Roles & Responsibilities

| Activity | Practice Lead | Product Owner | Platform/SRE |
|----------|:---:|:---:|:---:|
| Define naming standards | **Own** | — | Review |
| Manage schema evolution | **Own** | — | Implement |
| Monitor data quality | **Own** | — | Automate |
| Maintain service catalog currency | Oversee | **Own** (per service) | — |
| Define security/privacy policy | **Own** | — | Implement |

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA08 knowledge — a practitioner doing data governance work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-04 Service Profile Template](instruments/in-04-service-profile-template.md) | Definition | Service registry — the root entity that data governance maintains |
| [IN-14 Documentation Factory](instruments/in-14-documentation-factory.md) | Production | Generated documents depend on the data quality this KA governs |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| System-of-record | Service catalog with schema fields, quick reference, import tooling |
| Domain vocabulary | Controlled terminology, naming conventions |
| Schema migration history | Versioned evolution of the data model with rationale for each change |
| Data quality validation rules | Known quality patterns, conditional validation, schema enforcement |
| Enhancement log | Schema change history with rationale |
| Schema evolution proposal | A designed successor schema as part of the lifecycle |

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA01](ka01-business-context.md) — Business Context | KA08 **governs** [KA01](ka01-business-context.md) | Governance ensures business context definitions stay coherent |
| [KA03](ka03-standards-quality.md) — Standards & Quality | KA08 **depends on** [KA03](ka03-standards-quality.md) | Standards enforce governance decisions |
| [KA13](ka13-continuous-improvement.md) — Continuous Improvement | KA08 **informs** [KA13](ka13-continuous-improvement.md) | Governance health is a key practice metric |
| [KA07](ka07-integration-architecture.md) — Integration & Architecture | KA08 is **informed by** [KA07](ka07-integration-architecture.md) | Integration architecture patterns shape data governance requirements |

### External References

| Reference | Relevance |
|-----------|-----------|
| DMBOK 2 (Data Management Body of Knowledge) | Data governance, data quality, metadata management |
| ITIL Information Security Management | Security governance for service management data |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA08.1](ka08-data-governance.md#service-catalog-capability-registry) Service Catalog & Capability Registry | **Current** | Service catalog with a 15+ field schema. |
| [KA08.2](ka08-data-governance.md#naming-standards-conventions) Naming Standards & Conventions | **Current** | Controlled vocabulary, practitioner-referenceable. |
| [KA08.3](ka08-data-governance.md#data-quality-currency) Data Quality & Currency | **Current** | Schema versioning, CSV quality validation, enhancement logging. |
| [KA08.4](ka08-data-governance.md#schema-management) Schema Management | **Current** | Complete schema lifecycle: DDL, migrations, ORM, propagation rules, next-version proposal. |
| [KA08.5](ka08-data-governance.md#ownership-accountability) Ownership & Accountability | **Seeded** | Audit fields exist. No standalone accountability model for service profile currency. |
| [KA08.6](ka08-data-governance.md#telemetry-security-privacy-access-control) Telemetry Security, Privacy & Access Control | **Seeded** | Security referenced in context. No telemetry security policy. |

**KA08 summary:** 4/6 Current, 2 Seeded. Data management infrastructure is strong. Gaps are organizational (accountability model) and security/privacy policy.
