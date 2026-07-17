# Observability Body of Knowledge (O-BOK)

An opinionated map of the observability domain, organized around business observability — defining business health first and deriving signals from it.

**Current working version — opinionated starting point, not canonical.**

**New here?** → [Start Here](start-here.md) routes you by need; the mental model lives in [How the BOK is Organized](how-the-bok-is-organized.md) and a worked traversal example in [How to Walk a Question](how-to-walk-a-question.md).

**What questions is this useful for?** → [Questions the BOK Answers](questions-the-bok-answers.md) — full scope, plus explicit scope boundaries.

**Other entry points:** [About](about.md) (prior art and rationale) · [Contributing](contribute.md) (practitioners) · [Maintaining the BOK](maintaining-the-bok.md) (stewards)

---

## Knowledge Areas

13 KAs across three categories. Core Practice runs the observability lifecycle — *Define → Implement → Enforce → Observe → Respond.*

### Core Practice — lifecycle stages

| KA | Name | Stage | Primary Owner |
|----|------|-----------|---------------|
| [KA01](ka01-business-context.md) | Business Context & Service Definition | Define | Product Owner |
| [KA02](ka02-signal-design.md) | Signal Design & Instrumentation | Implement | Developer |
| [KA03](ka03-standards-quality.md) | Standards & Quality Assurance | Enforce | Platform / Engineering |
| [KA04](ka04-monitoring-visualization.md) | Monitoring, Visualization & Correlation | Observe | Platform / SRE |
| [KA05](ka05-incident-response.md) | Incident Management & Response | Respond | SRE / Ops |

### Enabling Practice — cross-cutting infrastructure

| KA | Name |
|----|------|
| [KA06](ka06-platform-tooling.md) | Platform & Tooling |
| [KA07](ka07-integration-architecture.md) | Integration & Architecture |
| [KA08](ka08-data-governance.md) | Data Management & Governance |

### Management Practice — organizational layer

| KA | Name |
|----|------|
| [KA09](ka09-strategy-program.md) | Strategy & Program Management |
| [KA10](ka10-stakeholder-engagement.md) | Stakeholder Engagement & Communication |
| [KA11](ka11-organizational-capability.md) | Organizational Capability |
| [KA12](ka12-adoption-enablement.md) | Adoption & Enablement |
| [KA13](ka13-continuous-improvement.md) | Continuous Improvement |

---

## Practice Instruments Catalog

**[Browse the full catalog →](instruments/README.md)** — 23 instruments in 5 types.

| Type | Count | Question |
|------|-------|----------|
| [Assessment](instruments/README.md#assessment-instruments) | 3 | Where are we? |
| [Definition](instruments/README.md#definition-instruments) | 7 | What do I fill out? |
| [Production](instruments/README.md#production-instruments) | 6 | What gets produced? |
| [Adoption](instruments/README.md#adoption-instruments) | 4 | How do teams get started? |
| [Communication](instruments/README.md#communication-instruments) | 3 | How do we show progress? |

Instruments are peers of Knowledge Areas, not children. Each KA page Section 5 lists the instruments that operationalize its knowledge. Each instrument page lists the KAs it draws from.

---

## Perspectives

**[Browse Perspectives →](perspectives/README.md)** — platform-type and context-type lenses that bend how KAs and Instruments apply.

| Perspective | Covers |
|---|---|
| [Cloud-Native](perspectives/cloud-native.md) | Container platforms, service mesh, OTel-native instrumentation |
| [Mainframe](perspectives/mainframe.md) | SMF/RMF records, batch telemetry, transaction monitors |
| [Hybrid / Integration](perspectives/hybrid-integration.md) | Cross-platform correlation, the seam problem |
| [SaaS / Third-Party](perspectives/saas-third-party.md) | API-level observability, vendor telemetry ingestion |
| [Agentic](perspectives/agentic.md) | Services with a judgment-making software step — the conditional Agent Workflow stratum *(provisional)*, decision-quality signals |

Perspectives are the third peer alongside KAs and Instruments. Pattern: BABOK v3 Perspectives chapter.

---

## How to find what you need

| Want to... | Go to |
|---|---|
| Understand a concept | KA page — start with Section 1 (Purpose & Scope) |
| Find a tool for a task | [Instruments](instruments/README.md) — browse by type |
| Trace dependencies | KA page Section 6 (Connected KAs) |
| Check what's filled in | KA page Section 7 (Content State & Gaps) |
| See who owns what | KA page Section 4 (Roles & Responsibilities) |

For the mental model behind the structure, see [How the BOK is Organized](how-the-bok-is-organized.md); for a worked traversal example, see [How to Walk a Question](how-to-walk-a-question.md).

---

## Underneath

**Structural YAML:** [`observability-bok.yaml`](../observability-bok.yaml) — machine-readable definitions, cross-KA relationships, boundary rules, instrument registry.
