# KA11 — Organizational Capability

**Category:** Management Practice
**Primary owner:** Leadership / Practice Lead
**Question this KA answers:** Do we have the right people, skills, and structure?

---

## 1. Purpose & Scope

This KA covers the people dimension of observability. Roles, team structure, skills, staffing, and culture. KA11 determines the ceiling for everything else — the best methodology, platform, and strategy won't matter if the organization can't execute. KA11 is what determines whether [KA12](ka12-adoption-enablement.md)'s adoption efforts succeed or stall.

**What's in scope:**
- Role definitions and responsibilities — PO, Developer, SRE, Platform, PE
- Team structure and interaction — how teams are organized for observability work
- Skills and competency development — what people need to know, growth paths
- Staffing and capacity — resource allocation for the practice
- Culture and mindset — shifting from reactive to proactive, business-outcome orientation

**What's out of scope:**
- How people adopt specific practices ([KA12](ka12-adoption-enablement.md)) — KA11 builds capability, [KA12](ka12-adoption-enablement.md) drives adoption
- How stakeholders are engaged ([KA10](ka10-stakeholder-engagement.md)) — KA11 builds organizational muscle, [KA10](ka10-stakeholder-engagement.md) engages outward
- Strategic direction ([KA09](ka09-strategy-program.md)) — KA11 is constrained by available capability

---

## 2. Domain Knowledge

### Role Definitions & Responsibilities

Business observability defines four primary roles, each owning specific layers and lifecycle stages:

| Role | Primary Layer Ownership | Lifecycle Contribution |
|------|----------------------|----------------------|
| **Product Owner** | Business Health, Business Impact | Define: business context, stakeholder expectations, SLO targets |
| **Developer** | Application | Implement: signal queries, data sources, instrumentation |
| **Platform/SRE** | System | Observe + Respond: monitoring, alerting, threshold configuration, incident response |
| **PE / Practice Lead** | Cross-cutting | All stages: methodology, governance, scaling, adoption |

The three-actor ownership model for Business Health signals ([KA02](ka02-signal-design.md)) is the most concrete instantiation: PO creates (what and why), Developer implements (how), Platform configures (when to alert). One record, three contributors.

### Team Structure & Interaction

One team model is documented: a leadership partnership where the practice lead works with product leads to embed the methodology in their teams. The common scaling constraint: the embedded-support model doesn't scale — teams need to adopt independently.

Team Topologies (Skelton & Pais) provides the analytical framework but hasn't been applied to observability team design. The key question: is the observability practice a platform team, an enabling team, or a complicated-subsystem team? The answer likely varies by maturity — enabling team early (teaching), platform team at scale (self-service).

### Skills & Competency Development

Onboarding a first service is the primary skill development mechanism — POs learn by doing. In the current process that means walking the motivation-chain elicitation ([KA12](ka12-adoption-enablement.md)): the PO who traverses stakeholder → expectation → signal for their own service has applied the four-layer model, not read about it. The earlier onboarding tool's learn mode (progressive disclosure of methodology concepts at each form step) remains the interactive training surface for the same purpose.

The domain context transfer document is skill development for AI agents — bringing them to practitioner-level understanding.

### Staffing & Capacity

A capacity model states how many services, how many teams, and what level of practice-lead support per team. The scaling constraint is explicit — embedded support must transition to independent team adoption to reach double-digit team counts.

### Culture & Mindset

The fundamental culture shift business observability drives: from reactive ("alert fires, we respond") to proactive ("we've defined what healthy looks like before anything breaks"). The "implicit → explicit" shift — business health requirements exist in POs' heads; the methodology makes them structured and measurable.

The technical reductionism pattern: technologists default to "show me the dependency map" when they hear "observability." The cultural shift: observability is about business outcomes, not just system topology. The map needs labels (health definitions) to be meaningful.

Prior art: Kotter's change management framework applies — establish urgency tied to a named problem, build a coalition of champions, and link new practice to visible wins before scaling. The cultural shift succeeds when a demonstrated case ("we defined health, caught the drift early, avoided the outage") replaces methodology advocacy.

---

## 3. Practices & Processes

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Stakeholder needs | [KA10](ka10-stakeholder-engagement.md) | Understanding what capabilities the organization needs |
| Strategic priorities | [KA09](ka09-strategy-program.md) | Available capability constrains strategic ambition |
| Adoption feedback | [KA12](ka12-adoption-enablement.md) | Where teams struggle reveals capability gaps |

| Output | To | Purpose |
|--------|-----|---------|
| Capable teams | [KA12](ka12-adoption-enablement.md) (Adoption) | Organizational capability determines adoption ceiling |
| Skilled responders | [KA05](ka05-incident-response.md) (Incident Response) | Right people with right skills enable effective response |
| Realistic constraints | [KA09](ka09-strategy-program.md) (Strategy) | Available capability constrains what strategy can promise |

---

## 4. Roles & Responsibilities

| Activity | Leadership | Practice Lead / PE | HR / Talent |
|----------|:---:|:---:|:---:|
| Define observability roles | Approve | **Own** | Review (JD alignment) |
| Design team structure | Approve | **Own** | — |
| Build competency paths | — | **Own** | Support (training infrastructure) |
| Capacity planning | Approve | **Own** (build model) | — |
| Culture and mindset shift | **Sponsor** | **Drive** | — |

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA11 knowledge — a practitioner doing organizational capability work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-02 Industry Maturity Arc](instruments/in-02-industry-maturity-arc.md) | Assessment | Organizational capability determines what stage on the 5-stage arc is achievable |
| [IN-03 Division Maturity Assessment](instruments/in-03-division-maturity-assessment.md) | Assessment | Organizational maturity dimension directly assesses KA11 topics (role clarity, standards adoption, sustainability) |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| OKR set with role descriptions | Role definitions per KR (PO, Dev, Platform) |
| Capacity model | Leadership partnership model, embedded-to-independent transition pattern |
| Domain context transfer | AI agent competency model (analogous to human skill development) |
| Maturity assessment | Technical-reductionism pattern, culture-shift observations from a reference LOB |

### Techniques

- **Learn-by-doing** — the onboarding workflow teaches the methodology through application, not training
- **AI agent as skill proxy** — domain context transfer creates a skilled agent that can support POs, reducing the human skill requirement
- **Part A → Part B transition** — embedded PE support first, independent adoption second. The scaling pattern for capability building.

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA05](ka05-incident-response.md) — Incident Response | KA11 **enables** [KA05](ka05-incident-response.md) | Right people with right skills enable effective response |
| [KA12](ka12-adoption-enablement.md) — Adoption & Enablement | KA11 **enables** [KA12](ka12-adoption-enablement.md) | Organizational capability determines adoption ceiling |
| [KA09](ka09-strategy-program.md) — Strategy & Program Management | KA11 **constrains** [KA09](ka09-strategy-program.md) | Available capability constrains strategic ambition |
| [KA10](ka10-stakeholder-engagement.md) — Stakeholder Engagement | KA11 is **informed by** [KA10](ka10-stakeholder-engagement.md) | Stakeholder engagement insights reveal where capability building is needed |

### External References

| Reference | Relevance |
|-----------|-----------|
| Skelton & Pais, *Team Topologies* | Team interaction modes, cognitive load, platform vs enabling teams |
| Kotter, *Leading Change* | Organizational change management for culture shifts |
| SFIA (Skills Framework for the Information Age) | IT competency framework — adaptable for observability roles |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA11.1](ka11-organizational-capability.md#role-definitions-responsibilities) Role Definitions & Responsibilities | **Seeded** | Roles described within OKR docs. No standalone role definitions. |
| [KA11.2](ka11-organizational-capability.md#team-structure-interaction) Team Structure & Interaction | **Seeded** | One team model (Business Health leads partnership). No Team Topologies application. |
| [KA11.3](ka11-organizational-capability.md#skills-competency-development) Skills & Competency Development | **Seeded** | Learning features designed. No role-specific competency paths. |
| [KA11.4](ka11-organizational-capability.md#staffing-capacity) Staffing & Capacity | **Seeded** | One capacity model for the current year. Not a reusable planning framework. |
| [KA11.5](ka11-organizational-capability.md#culture-mindset) Culture & Mindset | **Seeded** | Observable patterns noted. No change management methodology. |

**KA11 summary:** 0/5 Current, 5 Seeded. Most underdeveloped KA. Every topic has raw material — real instances from real work — but nothing has been extracted into practitioner-reusable form. The pattern: organizational capability work has been done through doing it (building teams, running meetings, onboarding POs), not through documenting how to do it.
