# KA10 — Stakeholder Engagement & Communication

**Category:** Management Practice

**Primary owner:** Practice Lead

**Question this KA answers:** How do we engage stakeholders across altitudes?

---

## 1. Purpose & Scope

This KA covers how the observability practice engages with stakeholders across altitudes. Champion networks, cross-altitude communication, facilitation, advocacy, and campaign intelligence. KA10 creates the organizational pull that makes adoption ([KA12](ka12-adoption-enablement.md)) possible — without engagement creating demand, enablement kits sit on a shelf.

**What's in scope:**

- Champion networks — identifying, enabling, and sustaining advocates
- Cross-altitude communication — framing the same work for executive, director, and team audiences
- Facilitation and meeting design — running effective governance sessions and workshops
- Advocacy and positioning — building organizational support
- Campaign intelligence — understanding the organizational landscape

**What's out of scope:**

- Strategy and program management ([KA09](ka09-strategy-program.md)) — KA10 enables, [KA09](ka09-strategy-program.md) directs
- Adoption execution ([KA12](ka12-adoption-enablement.md)) — KA10 creates pull, [KA12](ka12-adoption-enablement.md) delivers the product
- Organizational capability building ([KA11](ka11-organizational-capability.md)) — KA10 communicates, [KA11](ka11-organizational-capability.md) builds

---

## 2. Domain Knowledge

### Champion Networks

Champions are advocates distributed across the organization who carry the observability message into their own contexts. An effective champion network typically convenes as a recurring cross-LOB working group — regular participants from multiple lines of business and platform teams.

Champions are identified in context — who's aligned, who's skeptical, who's absent — through ongoing terrain mapping. A common gap: champion enablement. Identifying champions is more mature than equipping them; organizations rarely package "here's how to talk about observability to your team" for a champion to carry back.

### Cross-Altitude Communication

The same work must be framed differently for different audiences:

| Altitude | Audience | What they need to hear |
|----------|----------|----------------------|
| Enterprise (CIO / technology leadership) | Executive leadership | Business outcomes: faster business-impact assessment during incidents (who is affected, what's at risk — the dimension this work directly moves), change confidence, regulatory compliance |
| Director (MD/VP) | Senior line leadership | Operational outcomes: team efficiency, the adoption model (central production, franchise-style adoption), service-provider accountability |
| LOB (Leads/POs) | Product teams | Practical value: "here's what this does for YOUR service, in one short session" |
| IC (Dev/SRE) | Individual contributors | Technical integration: "here's how your signals connect to the business" |

Altitudes propagate on different clocks: a compact framing can be picked up verbatim at director altitude while the structural model behind it takes longer to land at enterprise altitude.

### Facilitation & Meeting Design

Two facilitation artifact patterns:

- **Recurring champions-group agenda template** — meeting structure with agenda framing, participant tracking, contribution documentation
- **FMEA facilitation script** — a 2-hour facilitation script for failure mode and effects analysis sessions with development teams

### Advocacy & Positioning

The first positioning message is decided: **"this isn't new work — it's structured thinking for existing work."** Teams already identify stakeholders, define what working means, and respond to incidents; the practice assigns structure to those existing activities. Presenting it as an additional layer on top of existing work triggers the bandwidth objection that kills adoption; the structured-thinking framing removes it. This message leads every audience framing in the altitude table above.

Business observability positioning follows a "service, not advocacy" posture — demonstrated through working artifacts and evidence rather than presentations and pitches. A worked reference case (one flow through the methodology), an onboarding simulation, and a factory model for artifact production are examples of advocacy through demonstration.

A terrain presentation maps business needs to lifecycle stages. This is advocacy infrastructure — showing "here's the territory, here's where we are, here's where the gaps are."

### Campaign Intelligence

Understanding the organizational landscape: who's doing what, what initiatives are in flight, where alliances and tensions exist.

Stakeholder-analysis artifacts include:

- Leadership communication analysis — what reply patterns and timing reveal about position and priority
- Meeting extractions with room readings, influence patterns, and commitment tracking across recurring sessions
- Multi-tier messaging matched to specific audiences (enterprise / cross-team / LOB)

Campaign intelligence accumulates as instance-specific artifacts — one extraction per meeting, one room-read per stakeholder group. The analytical approach (meeting extraction, room reading, commitment tracking) hardens into methodology when applied across multiple campaigns and patterns emerge.

---

## 3. Practices & Processes

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Strategic priorities | [KA09](ka09-strategy-program.md) | What to communicate and advocate for |
| Practice state and metrics | [KA13](ka13-continuous-improvement.md) | Evidence for stakeholder conversations |
| Adoption results | [KA12](ka12-adoption-enablement.md) | Success stories for advocacy |

| Output | To | Purpose |
|--------|-----|---------|
| Organizational pull | [KA12](ka12-adoption-enablement.md) (Adoption) | Stakeholder engagement creates demand for adoption |
| Stakeholder needs | [KA11](ka11-organizational-capability.md) (Org Capability) | Engagement surfaces capability requirements |
| Strategic feedback | [KA09](ka09-strategy-program.md) (Strategy) | Stakeholder reactions inform strategic adjustments |

---

## 4. Roles & Responsibilities

| Activity | Practice Lead | Leadership | Champions |
|----------|:---:|:---:|:---:|
| Champion identification | **Own** | Sponsor | — |
| Cross-altitude framing | **Own** | Review (exec altitude) | Adapt (LOB altitude) |
| Meeting facilitation | **Own** or co-facilitate | Host (governance) | Participate |
| Advocacy through demonstration | **Own** | Endorse | Carry to teams |
| Campaign intelligence | **Own** | — | Contribute (local context) |

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA10 knowledge — a practitioner doing stakeholder engagement work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-06 Stakeholder Expectation Template](instruments/in-06-stakeholder-expectation-template.md) | Definition | Structured stakeholder engagement — captures who cares and what they need |
| [IN-14 Documentation Factory](instruments/in-14-documentation-factory.md) | Production | Generates stakeholder documentation from business observability data |
| [IN-21 Terrain Presentation](instruments/in-21-terrain-presentation.md) | Communication | Maps observability needs to lifecycle stages for stakeholder audiences |
| [IN-20 Portfolio Maturity View](instruments/in-20-portfolio-maturity-view.md) | Communication | Executive visualization of portfolio progression — a stakeholder communication artifact |
| [IN-22 Executive Dashboard Patterns](instruments/in-22-executive-dashboard-patterns.md) | Communication | Design patterns for executive audiences — communication channel, not just visualization |

### KA-Specific Artifacts

| Artifact type | What it contains |
|--------------|-----------------|
| Campaign documentation | Stakeholder-engagement strategy, champion roster, framing constraints |
| Meeting extractions | Room readings, contribution tracking, commitment tracking across recurring sessions |
| FMEA facilitation guide | A facilitation script for failure-mode sessions with dev teams |
| Domain context transfer | Cross-altitude domain framing in a self-contained form |
| Training package orchestration | Persona × domain coverage matrix |
| Scope boundary framing | Reusable framing for "what business observability is and isn't" conversations |

### Techniques

- **Service, not advocacy** — demonstrate through working artifacts rather than pitching through presentations
- **Chat-based framing contribution** — compact frames that land verbatim in others' artifacts (a leader restating your phrase in their own language is a propagation signal)
- **Room reading methodology** — power/status mapping, agreement vs surface alignment, positioning analysis, commitment reliability assessment
- **Contribution tracking** — documenting what was offered, what landed, what didn't, and why

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA09](ka09-strategy-program.md) — Strategy & Program Management | KA10 **enables** [KA09](ka09-strategy-program.md) | Stakeholder engagement makes strategy executable |
| [KA12](ka12-adoption-enablement.md) — Adoption & Enablement | KA10 **enables** [KA12](ka12-adoption-enablement.md) | Engagement creates the pull that adoption needs |
| [KA11](ka11-organizational-capability.md) — Organizational Capability | KA10 **informs** [KA11](ka11-organizational-capability.md) | Stakeholder needs inform capability requirements |

### External References

| Reference | Relevance |
|-----------|-----------|
| Daniel Pink, *To Sell is Human* | Persuasive communication principles — applied in stakeholder comms |
| Rogers, *Diffusion of Innovations* | How innovations spread through organizations — champion networks |
| Kotter, *Leading Change* | Creating urgency and coalition — organizational change mechanics |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA10.1](ka10-stakeholder-engagement.md#champion-networks) Champion Networks | **Seeded** | Champion identification practice documented. Champion enablement playbook not yet produced. |
| [KA10.2](ka10-stakeholder-engagement.md#cross-altitude-communication) Cross-Altitude Communication | **Seeded** | Multiple altitude framing instances. Not extracted into reusable guidance. |
| [KA10.3](ka10-stakeholder-engagement.md#facilitation-meeting-design) Facilitation & Meeting Design | **Current** | Recurring-meeting agenda template + FMEA 2-hour facilitation script. Practitioner-actionable. |
| [KA10.4](ka10-stakeholder-engagement.md#advocacy-positioning) Advocacy & Positioning | **Seeded** | "Service not advocacy" posture documented. No reusable positioning methodology. |
| [KA10.5](ka10-stakeholder-engagement.md#campaign-intelligence) Campaign Intelligence | **Seeded** | Analysis is present but the analytical approach is not yet extracted. |

**KA10 summary:** 1/5 Current, 4 Seeded. Campaign intelligence is present as analysis but not yet extracted into reusable methodology.

### Adjacent Technique — Consequence Before Capability

When eliciting stakeholder needs for resilience, DR, or availability: start from business consequence (what fails for whom if this is unavailable), not desired capability (what feature the team wants). The BIA-shaped elicitation technique — a convergence across reliability engineering, risk management, business-continuity planning, domain-driven design, and adjacent disciplines — produces more actionable requirements than capability-first asking.
