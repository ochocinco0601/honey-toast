# KA09 — Strategy & Program Management

**Category:** Management Practice
**Primary owner:** Leadership / Practice Lead
**Question this KA answers:** How does observability align with enterprise direction?

---

## 1. Purpose & Scope

This KA covers how observability aligns with enterprise strategy. Program structure, theme prioritization, operating model design, roadmap management, assumption-based planning, and investment justification. KA09 is where "what we're building" connects to "why the enterprise cares."

**What's in scope:**
- Enterprise alignment — connecting observability to business strategy, OKRs
- Program structure and governance — working groups, decision rights, cadence
- Theme prioritization — identifying and sequencing strategic themes
- Operating model design — centralized, federated, or hybrid
- Roadmap and altitude cascade — translating strategy through levels to team actions
- Assumption-based planning — managing uncertainty in strategic plans
- Investment justification — making the business case for observability

**What's out of scope:**
- Stakeholder engagement tactics ([KA10](ka10-stakeholder-engagement.md)) — KA09 sets strategy, [KA10](ka10-stakeholder-engagement.md) engages people
- Organizational capability ([KA11](ka11-organizational-capability.md)) — KA09 plans, [KA11](ka11-organizational-capability.md) builds capability
- Adoption execution ([KA12](ka12-adoption-enablement.md)) — KA09 prioritizes, [KA12](ka12-adoption-enablement.md) delivers

---

## 2. Domain Knowledge

### Enterprise Alignment

One workable cascade structure — the reference program's — uses four Key Results:

- **KR1:** Methodology validation — framework proven on real services
- **KR2:** Implementation — services instrumented across layers
- **KR3:** Cross-org adoption — multiple lines of business using the methodology
- **KR4:** Enterprise integration — methodology positioned within enterprise architecture

Each KR has quantified measures, milestones, and dependencies. The OKR structure connects practice-level work to enterprise-level outcomes.

### Program Structure & Governance

A recurring governance structure for an emerging observability practice is a **champions working group** — a recurring meeting of regular participants from multiple LOBs and platform teams, convened by senior line leadership, co-facilitated by a practice lead. The group produces upward-facing deliverables for executive audiences.

A champions group is not a formal program management office — it's a pre-PMO structure being pushed toward more disciplined output as the practice matures. Inflection points typically occur when sponsoring leadership formalizes the output form (e.g., requiring a workstream vision document for executive review).

### Theme Prioritization

Hoshin Kanri provides the cascade pattern: an X-matrix translates enterprise strategies (north) through objectives (east) to improvement priorities (south) to measures/evidence (west). This is the cascade mechanism.

### Operating Model Design

A factory model for business observability practice defines how work is produced at scale:

- **5 production lines:** Story, Dashboard, Alert, Playbook, Documentation
- **3 input personas:** PO (business context), Developer (technical), Platform (operational)
- **1 PO action → 5+ automated outputs** — the scale multiplier

For the business-observability practice itself, the operating-model shape is decided along two separate architectures: **production is central** — one shared factory produces every team's artifacts, CI/CD-shaped (nobody argues each team should run its own build infrastructure) — and **adoption is franchise** — each line of business takes on the practices, contributes its own inputs, and is validated against the spec before going live. Collapsing the two into a single centralized-vs-federated axis is the documented trap.

For the *enterprise observability landscape* beyond the practice, a candidate operating-model pattern is **service-provider federation**: named providers own specific capabilities across the enterprise (e.g., one provider owns business-service mapping, another owns holistic views, a third owns anomaly detection as a service). This is one candidate among several; what tends to land across operating-model debates is the principle **"common where possible, custom where needed"** — capabilities teams can share go in the common platform, with LOB specificity carried in the outputs.

### Roadmap & Altitude Cascade

Hoshin Kanri provides the cascade mechanism: enterprise strategy → division goals → team actions. In the reference program, annual objectives cascade into quarterly milestones.

### Assumption-Based Planning

Load-bearing assumptions, signposts that indicate assumptions are breaking, and hedging actions when they do. One instance pattern: a division-level maturity assessment that includes explicit director-level assumptions.

Prior art: ABP (Dewar, *Assumption-Based Planning*) — identify assumptions, classify by importance and vulnerability, track signposts, prepare hedging actions.

### Investment Justification & Value Demonstration

Making the business case: connecting observability outcomes to business value. A worked case study in the reference implementation (a credit-check service) demonstrates the pattern — faster business-impact assessment during incidents expressed in dollar terms, faster detection in customer impact terms.

Published industry maturity models provide ROI benchmarks. The dimensional decomposition approach: attribute value to the specific dimension the investment moves, not claiming credit for aggregate metrics.

Dimensional value attribution is the discipline: claim value for the specific dimension the investment moves, not the aggregate metric the entire organization contributes to. MTTR is the canonical counter-example — a multi-phase aggregate (detection, diagnosis, impact assessment, resolution, communication) that no single initiative honestly claims. Business observability's honest dimension within it is **business-impact assessment speed** ("which customers are affected, what revenue is at risk, what to prioritize" — from >30 minutes to <10). Other honest dimensions: detection latency to avoided impact, proactive identification to risk reduction. "Reduce MTTR" as a claimed outcome is the dishonest form — it claims phases the investment doesn't touch.

---

## 3. Practices & Processes

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Enterprise strategy, OKRs | Enterprise leadership | Alignment targets |
| Stakeholder engagement feedback | [KA10](ka10-stakeholder-engagement.md) | Understanding organizational readiness |
| Organizational capability assessment | [KA11](ka11-organizational-capability.md) | Realistic planning given available capability |
| Practice metrics | [KA13](ka13-continuous-improvement.md) | Evidence for investment justification |

| Output | To | Purpose |
|--------|-----|---------|
| Strategic priorities | [KA12](ka12-adoption-enablement.md) (Adoption) | Which teams/services to target |
| Program structure | [KA10](ka10-stakeholder-engagement.md) (Engagement) | Governance forums for stakeholder engagement |
| Investment case | Enterprise leadership | Budget and resource justification |

---

## 4. Roles & Responsibilities

| Activity | Practice Lead / PE | Leadership (MD/VP) | Platform Lead |
|----------|:---:|:---:|:---:|
| Enterprise alignment | **Own** | Validate + sponsor | Contribute |
| Program governance design | Contribute | **Own** | Contribute |
| Theme prioritization | **Own** | Approve | Contribute |
| Operating model design | **Own** | Approve | Contribute |
| Investment justification | **Own** (build case) | **Own** (approve/present) | Contribute (cost data) |

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA09 knowledge — a practitioner doing strategy and program work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-02 Industry Maturity Arc](instruments/in-02-industry-maturity-arc.md) | Assessment | Positions the organization against industry benchmarks for strategic planning |
| [IN-03 Division Maturity Assessment](instruments/in-03-division-maturity-assessment.md) | Assessment | Division-level maturity assessment informing resource allocation |
| [IN-01 Service Maturity Model](instruments/in-01-service-maturity-model.md) | Assessment | Portfolio distribution informs strategic prioritization and resource allocation |
| [IN-20 Portfolio Maturity View](instruments/in-20-portfolio-maturity-view.md) | Communication | Executive visualization of portfolio progression — informs strategic prioritization |
| [IN-21 Terrain Presentation](instruments/in-21-terrain-presentation.md) | Communication | Maps observability needs to lifecycle stages — supports strategic positioning |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| OKR set with KRs and rationale | Key Results with quantified measures and a worked case study demonstrating value |
| OKR methodology analysis | Restructured KR formulations, cross-org dependency mapping |
| Factory operating model | Production lines, scale multiplier, strategic alignment |
| X-matrix | Hoshin Kanri cascade: strategy → objectives → priorities → measures |
| Hoshin Kanri research | Altitude cascade methodology |
| Champions-group documentation | Structure, meeting extractions, commitment tracking |
| Maturity model research | Industry sources, convergence findings, ROI benchmarks |

### Techniques

- **Hoshin Kanri altitude cascade** — enterprise → division → team. Same work framed at three altitudes.
- **X-matrix** — four-quadrant visual: strategies (N), objectives (E), priorities (S), measures (W). Correlation dots show which strategies drive which objectives.
- **Factory model framing** — "1 PO action → 5+ outputs" communicates scale value to leadership.
- **Dimensional value attribution** — claim value for the specific dimension the investment moves, not aggregate metrics.

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA10](ka10-stakeholder-engagement.md) — Stakeholder Engagement | KA09 **depends on** [KA10](ka10-stakeholder-engagement.md) | Strategy requires stakeholder engagement to land |
| [KA12](ka12-adoption-enablement.md) — Adoption & Enablement | KA09 **feeds** [KA12](ka12-adoption-enablement.md) | Strategic decisions drive adoption priorities |
| [KA07](ka07-integration-architecture.md) — Integration & Architecture | KA09 is **constrained by** [KA07](ka07-integration-architecture.md) | Strategy operates within enterprise architecture constraints |
| [KA11](ka11-organizational-capability.md) — Organizational Capability | KA09 is **constrained by** [KA11](ka11-organizational-capability.md) | Capability maturity bounds what strategy can commit to |
| [KA13](ka13-continuous-improvement.md) — Continuous Improvement | KA09 is **informed by** [KA13](ka13-continuous-improvement.md) | Improvement findings adjust strategic direction |
| [KA01](ka01-business-context.md) — Business Context | KA09 is **informed by** [KA01](ka01-business-context.md) | Aggregate business context feeds strategic prioritization |
| [KA04](ka04-monitoring-visualization.md) — Monitoring & Visualization | KA09 is **informed by** [KA04](ka04-monitoring-visualization.md) | Portfolio health views inform strategic decisions |

### External References

| Reference | Relevance |
|-----------|-----------|
| Hoshin Kanri (Lean management) | Altitude cascade, X-matrix, strategy deployment |
| ABP — Dewar, *Assumption-Based Planning* | Managing uncertainty in strategic plans |
| Gartner Observability Market Research | Industry benchmarks for investment justification |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA09.1](ka09-strategy-program.md#enterprise-alignment) Enterprise Alignment | **Current** | Annual OKRs with 4 KRs, quantified measures. Actionable. |
| [KA09.2](ka09-strategy-program.md#program-structure-governance) Program Structure & Governance | **Seeded** | Champions-group structure documented as an instance. Not yet extracted into a reusable governance model. |
| [KA09.3](ka09-strategy-program.md#theme-prioritization) Theme Prioritization | **Seeded** | Hoshin research + working X-matrix. Not reusable methodology. |
| [KA09.4](ka09-strategy-program.md#operating-model-design) Operating Model Design | **Current** | Factory model: 5 production lines, practitioner-actionable. |
| [KA09.5](ka09-strategy-program.md#roadmap-altitude-cascade) Roadmap & Altitude Cascade | **Seeded** | An annual cascade exists. No long-term roadmap methodology. |
| [KA09.6](ka09-strategy-program.md#assumption-based-planning) Assumption-Based Planning | **Seeded** | One ABP instance. Not reusable methodology. |
| [KA09.7](ka09-strategy-program.md#investment-justification-value-demonstration) Investment Justification | **Seeded** | Evidence assembled. Not organized as reusable methodology. |

**KA09 summary:** 2/7 Current, 5 Seeded. Strategic content is rich but instance-specific. The consistent gap: real strategic work has been done but hasn't been extracted into reusable methodology.
