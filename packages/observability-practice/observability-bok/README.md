# Observability Body of Knowledge (O-BOK)

A map of the observability domain built on one commitment: **define what business health means first, then derive the signals from it.**

It's a reference to look things up in — a working draft, not a finished standard. Every page states what's filled in and what isn't.

---

## Start with your question

### Running the practice

*Define → Implement → Enforce → Observe → Respond. Responding feeds back into defining.*

| Your question | Where it's answered |
|---|---|
| What does "healthy" mean in business terms? | [Business Context & Service Definition](ka01-business-context.md) |
| How do we instrument the signals that matter? | [Signal Design & Instrumentation](ka02-signal-design.md) |
| How do we ensure standards before production? | [Standards & Quality Assurance](ka03-standards-quality.md) |
| What views make health visible? | [Monitoring, Visualization & Correlation](ka04-monitoring-visualization.md) |
| When something fails, what do we do? | [Incident Management & Response](ka05-incident-response.md) |

### Making it possible

| Your question | Where it's answered |
|---|---|
| What technology makes observability possible? | [Platform & Tooling](ka06-platform-tooling.md) |
| How does observability connect to enterprise systems? | [Integration & Architecture](ka07-integration-architecture.md) |
| How do we maintain data coherence at scale? | [Data Management & Governance](ka08-data-governance.md) |

### Making it stick

| Your question | Where it's answered |
|---|---|
| How does observability align with enterprise direction? | [Strategy & Program Management](ka09-strategy-program.md) |
| How do we engage stakeholders across altitudes? | [Stakeholder Engagement & Communication](ka10-stakeholder-engagement.md) |
| Do we have the right people, skills, and structure? | [Organizational Capability](ka11-organizational-capability.md) |
| How do teams adopt and sustain observability practices? | [Adoption & Enablement](ka12-adoption-enablement.md) |
| Is the observability practice itself getting better? | [Continuous Improvement](ka13-continuous-improvement.md) |

---

## Or pick up a tool

The pages above explain what you need to understand. These are what you fill out and use — **[24 instruments in the full catalog →](instruments/README.md)**

| Your question | What you'll find |
|---|---|
| Where are we? | [Assessment](instruments/README.md#assessment-instruments) — maturity models and assessments |
| What do I fill out? | [Definition](instruments/README.md#definition-instruments) — templates plus the written standard |
| What gets produced? | [Production](instruments/README.md#production-instruments) — generators for dashboards, alerts, playbooks |
| How do teams get started? | [Adoption](instruments/README.md#adoption-instruments) — onboarding and pilot tools |
| How do we show progress? | [Communication](instruments/README.md#communication-instruments) — stakeholder reporting tools |

---

## Or start from your platform

Same knowledge, bent by where your workload runs. **[Browse all →](perspectives/README.md)**

| If you work on... | Read |
|---|---|
| Container platforms, service mesh, OTel-native instrumentation | [Cloud-Native](perspectives/cloud-native.md) |
| SMF/RMF records, batch telemetry, transaction monitors | [Mainframe](perspectives/mainframe.md) |
| Cross-platform correlation — and the seam between platforms | [Hybrid / Integration](perspectives/hybrid-integration.md) |
| API-level observability and vendor telemetry you ingest | [SaaS / Third-Party](perspectives/saas-third-party.md) |
| Services with a judgment-making software step | [Agentic](perspectives/agentic.md) — decision-quality signals *(provisional)* |

---

## New to this?

| You want to... | Go to |
|---|---|
| Meet the approach — the four-layer model, the semantic chain | [The Methodology](the-methodology.md) — in plain terms |
| See one real question answered end to end | [How to Walk a Question](how-to-walk-a-question.md) — a worked example |
| Check whether this covers what you need | [Questions the BOK Answers](questions-the-bok-answers.md) — full scope, and what's out of scope |
| Know why it's built this way | [About](about.md) — prior art and rationale |
| Add something | [Contributing](contribute.md) — where contributions land |

## Producing something for an audience

This is source material, not a deliverable. Don't hand a Knowledge Area to a stakeholder. Take the depth from here, then cut the form that fits who's receiving it — see the companion [The Practice System](../the-practice-system.md).

## Maintaining it

Structure, editing rules, how elements are added and retired, and a test suite an agent can run: [Maintaining the BOK](maintaining-the-bok.md) · the mental model behind the three-part structure: [How the BOK is Organized](how-the-bok-is-organized.md) · machine-readable registry: [`observability-bok.yaml`](../observability-bok.yaml)
