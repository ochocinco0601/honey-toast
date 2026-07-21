# KA12 — Adoption & Enablement

**Category:** Management Practice

**Primary owner:** Practice Lead

**Question this KA answers:** How do teams actually adopt and sustain observability practices?

---

## 1. Purpose & Scope

This KA covers the gap between "the methodology exists" and "teams are using it." A body of knowledge that isn't adopted is an artifact. Adoption is how structured observability practice reaches teams — through onboarding flows, transfer packages, pilot programs, scaling patterns, and AI-mediated distribution.

**What's in scope:**

- First experience and onboarding — what a team does on day one
- Transfer packages that teams can adopt without a principal engineer in the room
- Pilot design — how to run a controlled test with success criteria and feedback
- Scaling from pilot to division to enterprise
- AI agents as the distribution mechanism for methodology (practice distribution)

**What's out of scope:**

- The methodology itself ([KA01](ka01-business-context.md)-[KA05](ka05-incident-response.md)) — KA12 distributes it, doesn't define it
- Stakeholder engagement and organizational politics ([KA10](ka10-stakeholder-engagement.md)) — KA12 depends on [KA10](ka10-stakeholder-engagement.md) creating the pull
- Organizational capability and team structure ([KA11](ka11-organizational-capability.md)) — KA12 is constrained by [KA11](ka11-organizational-capability.md)'s ceiling
- Strategy and program management ([KA09](ka09-strategy-program.md)) — KA12 executes what [KA09](ka09-strategy-program.md) prioritizes

---

## 2. Domain Knowledge

### Onboarding & First Experience

The first interaction a team has with business observability determines whether they adopt it. **The current onboarding process is the motivation-chain instrument** — an agent-walked elicitation that takes source material plus the Product Owner's knowledge and produces a validated Service Understanding Document. Its shape:

1. **Service context** — identity, purpose, dependencies, business-process participation, sub-capabilities
2. **Stakeholder chains** — one complete chain per stakeholder: who they are, what they expect, and the Business Health signal measuring each expectation, with a per-chain coverage gate (every expectation → a signal) before moving on
3. **Business impact** — Business Impact signals quantifying failure consequences, linked to the stakeholder concerns they assess
4. **Developer diagnostics** — Application signals causally linked to the Business Health signals they explain, grounded to sub-capabilities
5. **Platform infrastructure** — System signals
6. **Operational context and gaps** — informed by the complete chain picture

The layer of every signal is structural — derived from where in the chain it is captured, never asked as a question — and traceability is produced by the capture nesting itself, never reconnected afterward. A conditional stratum activates only when a workflow step is software that can be *confidently wrong* (an agentic decision point). Verification is mandatory, not optional: cross-reference integrity checks, a generated entity page, and an independent content check against the sources, all before the result reaches human review.

The training surface walks the same capture content in an entity-by-entity step order (service basics → stakeholder expectations → business signals and SLO configuration → technical signals → impact → preview and export). That order predates the motivation-chain restructuring ([IN-16](instruments/in-16-onboarding-simulation.md)), and two of its modes are worth keeping by design:

- **Learn mode** — progressive disclosure with explanations, "why this matters" content, good/bad examples at each step. For POs encountering the methodology for the first time.
- **Fast mode** — minimized instructional content for experienced users. Same forms, less guidance.

A worked example service should ship with the capture surface, loadable in one step, so a Product Owner sees what a completed service looks like before filling in their own.

A first service profile is a short session with AI-assisted pre-population. The methodology proves itself through use — the PO who completes one profile understands the four-layer model because they just applied it, not because they read about it.

**Self-service tool discovery** is a recurring enterprise onboarding gap. The practitioner framing: "I have an app ID — tell me which tools apply, what's configured, what's missing." App owners face fragmented documentation and cannot self-serve into the right observability tool. This is an unmet sub-topic within onboarding — a navigation/discovery layer that requires [KA06.1](ka06-platform-tooling.md#tool-landscape-selection) (Tool Landscape & Selection) to supply the underlying content.

### Transfer Packages & Enablement Kits

A transfer package is a self-contained artifact set that a team can adopt without the methodology author present. The portfolio includes:

**CSV-based transfer:**

- 5 structured CSV templates (services, stakeholder expectations, signal definitions, impact signals, operational metadata) that capture a service profile
- Templates match the system-of-record format — data entered here flows directly into the pipeline
- Filled examples alongside blank templates so teams can see what good data looks like

**Batch metadata extraction:**

- For services with existing batch jobs or scheduled processes, a specialized extraction package captures business observability metadata from existing documentation
- Includes SOP (standard operating procedure) for batch job onboarding
- Applicable to scheduled and reconciliation batch workloads

**Domain context transfer for AI agents:**

- A comprehensive onboarding document that brings an AI agent to practitioner-level understanding of the business observability domain
- Written for the instruction-following level typical of enterprise AI-assistant environments
- Covers: four-layer model, semantic flow, factory model, lifecycle, stakeholder context, terminology
- The agent reads this once and can then reason about observability conversations, not just retrieve facts

**AI-assistant capability transfer:**

- Portable skills (editorial governance, systems analysis, requirements, value analysis, and others) packaged for enterprise AI-assistant adoption
- Each skill includes a SETUP.md — imperative instructions the receiving AI agent reads and executes
- Evaluation methodology for assessing which skills transfer well and which lose too much capability

### Pilot Design & Execution

A pilot is a controlled test of the methodology with a specific team or service, producing structured feedback. Two pilot approaches have been documented:

**Simulation protocol:**

- A repeatable guided walkthrough run against real services
- Supports AI-assisted observation and assistance during the session
- Produces: CSV data files, session checkpoints (for resume), friction logs (what didn't work)
- Friction logging is real-time — issues are captured as they arise, not reconstructed afterward
- Triage during simulation: workaround and continue (log it) > complete blocker (pause and discuss) > need user context (ask, capture, continue)

**Batch-reconciliation pilot:**

- A batch-metadata extraction pattern for scheduled and reconciliation workloads
- Produces: dashboard panels, metadata definitions, structured records, alert definitions, playbooks, filled example CSVs, an onboarding SOP
- Exercises the full artifact chain: PO input → factory output (dashboard, alerts, playbook)

**What a pilot measures:**

- Time to complete first service profile (target: <30 minutes for PO sections)
- Friction points — where the workflow confused or blocked the user
- Data quality — did the PO produce stakeholder expectations and signals that are specific and actionable?
- Handoff quality — could a Developer pick up the PO's output and implement?

### Scaling Patterns

Moving from pilot to division to enterprise requires different mechanisms at each scale:

A typical annual target set references double-digit teams adopting the methodology, transitioning from practice-lead-embedded support to team-independent adoption. The scaling constraint: embedded-support models don't scale — teams need to adopt independently using transfer packages and AI-mediated tools.

**Scaling principles:**

- **Production is central; adoption is franchise.** Two different architectures, not one centralized-vs-federated axis. One shared factory produces every team's artifacts — CI/CD-shaped, the way nobody argues each team should run its own build infrastructure. Each line of business adopts franchise-style: it learns the practices, owns its inputs (service context, expectations), plugs into the central machinery, and is validated against the spec before its services go live. Collapsing the two — "give each LOB their own packaged instance to run locally" — is the trap to avoid.
- **Common where possible, custom where needed.** The methodology core is common across teams; the service-specific content is custom per team — carried in the outputs, not in per-team production machinery.
- **Self-serve over standing training programs.** The scaling question is not "how do we train 500 POs" but "how do we make the methodology self-serve." Franchise adoption still includes learning the practices — enablement kits and AI-mediated tools are how that learning scales without classroom dependency.

The adoption architecture names five design surfaces, all decided as the frame: an onboarding playbook (how an LOB gets from zero to first services live), certification (what makes an LOB's definitions trustworthy — what "done learning" means), service-level agreements between the LOB and the central capability, quality gates (central validation before an LOB's services move from draft to active), and exception handling (when an LOB's needs don't fit the standard practice). The operational playbook for moving from pilot-scale to enterprise-standard practice instantiates those surfaces with transfer packages, AI agents embedded in the tools practitioners already use, and a friction-logging discipline that surfaces adoption barriers as they arise.

### AI-Mediated Practice Distribution

The core insight: instead of training people in a methodology and hoping they apply it, embed the methodology in the tools people already use. AI agents become the distribution mechanism.

**How this works in practice:**

1. **Domain context transfer** — the AI agent reads a comprehensive onboarding document and achieves practitioner-level understanding of the business observability domain
2. **Portable skills** — methodology is encoded as agent skills (requirements, systems analysis, editorial governance) that the agent executes during normal work
3. **Pre-population** — the agent drafts service profiles from existing Confluence and Jira content, marked "NEEDS PO VALIDATION." The PO reviews and adjusts rather than writing from scratch.
4. **In-workflow guidance** — a capture surface can generate a context-specific AI prompt pre-filled with the service name and the data already entered. The PO takes that prompt to an AI assistant and gets a draft back, needing no prompt-engineering skill.

**Patterns in practice:**
1. **Methodology-as-agent-skills** — portable skills transfer (AI coding assistants), onboarding agents, domain context transfer documents
2. **Crowdsourced agent libraries** — centrally-resourced agent development for commonly prioritized use cases, distributed through a federation model

Both are instances of the same pattern: AI agents embedding observability practices into tools people already use. A crowdsourcing/federation model layered on top is itself a distribution pattern.

Prior art: The operating model concept — a Knowledge Management system where AI agents are the practice distribution mechanism. This BOK names the pattern "Practice Distribution Mechanism."

---

## 3. Practices & Processes

### The Adoption Funnel

```
1. Awareness      → Stakeholder engagement (KA10) creates pull — led by the decided first
                    message: "this isn't new work — it's structured thinking for existing work"
2. First touch    → Onboarding instrument or AI-assisted pre-population — "try it with one service"
3. Pilot          → Controlled test with friction logging — "does it work for your context?"
4. Pilot review   → Review pilot output, adjust methodology if needed — "what did we learn?"
5. Certification  → Central validation against the spec — the team's definitions reviewed
                    before its services move from draft to active. This gate is what makes
                    franchise adoption safe and makes "done" legible
6. Team adoption  → Transfer package deployed, team owns ongoing — "it's yours now"
7. Scale          → Pattern repeats across teams — "who's next?"
```

KA12 owns steps 2-7. Step 1 is [KA10](ka10-stakeholder-engagement.md) (Stakeholder Engagement). The funnel is not purely sequential — a strong pilot (step 3) generates awareness (step 1) for adjacent teams through demonstrated results.

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Service profiles, methodology content | [KA01](ka01-business-context.md)-[KA05](ka05-incident-response.md) | The substance being adopted |
| Stakeholder pull, champion networks | [KA10](ka10-stakeholder-engagement.md) | Creating demand — adoption without pull is pushing rope |
| Team structure, skill levels | [KA11](ka11-organizational-capability.md) | Understanding adoption ceiling — what's realistic for this team |
| Strategic priorities | [KA09](ka09-strategy-program.md) | Which teams/services to target first |

| Output | To | Purpose |
|--------|-----|---------|
| Adoption rate, time-to-value metrics | [KA13](ka13-continuous-improvement.md) (Continuous Improvement) | Measuring whether the practice is growing |
| Friction logs, pilot feedback | [KA01](ka01-business-context.md)-[KA05](ka05-incident-response.md) | Methodology improvements driven by real adoption experience |
| Configured AI agents in the enterprise environment | Teams | The scaled distribution mechanism |

---

## 4. Roles & Responsibilities

| Activity | Principal engineer / Practice Lead | Product Owner | Developer | Platform/SRE |
|----------|:---:|:---:|:---:|:---:|
| Design onboarding workflow | **Own** | Validate (usability) | — | — |
| Create transfer packages | **Own** | Review (content) | Review (tech) | Review (ops) |
| Run pilot | **Facilitate** | **Participate** | **Participate** | **Participate** |
| Capture friction & improve | **Own** | Report friction | Report friction | Report friction |
| Configure AI agents for the enterprise environment | **Own** | — | — | — |
| Scale to new teams | **Initiate** | **Own** (for their team) | — | — |

The principal engineer is the primary actor for designing and enabling adoption. Once a team adopts, the PO owns ongoing use within their service portfolio. The scaling shift: from principal-engineer-facilitated to PO-independent.

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA12 knowledge — a practitioner doing adoption and enablement work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-16 Onboarding Simulation](instruments/in-16-onboarding-simulation.md) | Adoption | Interactive walkthrough for a PO's first service profile — the primary [KA12.1](ka12-adoption-enablement.md#onboarding-first-experience) implementation |
| [IN-17 Transfer Packages](instruments/in-17-transfer-packages.md) | Adoption | Self-contained artifact bundles that make adoption portable across teams and LOBs |
| [IN-18 Friction Logging Protocol](instruments/in-18-friction-logging-protocol.md) | Adoption | Structured capture of adoption pain points during pilots and onboarding |
| [IN-19 Discovery Dialogue Protocol](instruments/in-19-discovery-dialogue-protocol.md) | Adoption | Facilitation guide for the PO conversation that produces a service profile |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| Lightweight onboarding implementation plan | Use cases, phases, persona test scripts, build system |
| Onboarding simulation protocol | Multi-step walkthrough with friction logging and session continuity |
| Domain context transfer | Full domain knowledge transfer for onboarding an AI agent |
| Batch metadata extraction package | Specialized onboarding for batch-job services with worked pilot |
| Training package orchestration | Persona coverage matrix, use-case framework, artifact evaluation |
| Portable capability transfer | Portable skills, AI-agent setup patterns, evaluation methodology |
| Structured input templates | CSV templates that capture a complete service profile |

### Techniques

- **Two-mode onboarding** — Learn mode (progressive disclosure) for first time, Fast mode for experienced users. Same tool, different information density.
- **Example-first** — a worked example that loads in one step. POs see the finished product before filling in their own.
- **Friction logging** — Real-time capture during pilots: issue, context, workaround, recommendation. 30 seconds per entry. Analyzed after completion, not during.
- **AI agent onboarding (SETUP.md pattern)** — AI-consumable setup documents the receiving agent reads and executes. Imperative steps, explicit branching, validation tests, troubleshooting.
- **AI-assistant prompt generator** — produces context-specific AI prompts including the user's already-entered data. No prompt engineering skill required from the PO.

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA01](ka01-business-context.md) — Business Context & Service Definition | KA12 **implements** [KA01](ka01-business-context.md) | Adoption is how business context definition reaches teams. The onboarding workflow IS the [KA01](ka01-business-context.md) practice delivered to POs. |
| [KA10](ka10-stakeholder-engagement.md) — Stakeholder Engagement & Communication | KA12 **depends on** [KA10](ka10-stakeholder-engagement.md) | Adoption needs pull. Without stakeholder engagement creating demand, enablement kits sit on a shelf. |
| [KA11](ka11-organizational-capability.md) — Organizational Capability | KA12 **depends on** [KA11](ka11-organizational-capability.md) | The adoption ceiling is set by organizational capability — team structure, skills, capacity. |
| [KA09](ka09-strategy-program.md) — Strategy & Program Management | KA12 **depends on** [KA09](ka09-strategy-program.md) | Strategic decisions drive adoption priorities — which teams, which services, what order. |
| [KA13](ka13-continuous-improvement.md) — Continuous Improvement | KA12 **feeds** [KA13](ka13-continuous-improvement.md) | Adoption metrics (rate, time-to-value, friction patterns) are key practice health indicators. |
| [KA06](ka06-platform-tooling.md) — Platform & Tooling | KA12 **depends on** [KA06](ka06-platform-tooling.md) | Tool selection knowledge ([KA06.1](ka06-platform-tooling.md#tool-landscape-selection)) is prerequisite for the self-service tool discovery onboarding layer. |

### External References

| Reference | Relevance |
|-----------|-----------|
| Rogers, *Diffusion of Innovations* | Adoption mechanics — relative advantage must be perceivable. Explains why posting a framework in chat doesn't equal adoption. |
| Kotter, *Leading Change* | Urgency connected to solution. Naming the problem without connecting a structured answer is the common adoption-stall pattern. |
| ITIL Service Catalog (self-service patterns) | Prior art for the tool discovery gap — app-ID-driven recommendation |
| GitLab Handbook model | "Handbook IS the process" — the closest existing implementation of methodology embedded in a shared artifact |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA12.1](ka12-adoption-enablement.md#onboarding-first-experience) Onboarding & First Experience | **Current** | Motivation-chain instrument documented as the active process (structural layers, coverage gates, mandatory verification); earlier 8-step tool workflow retained as the training surface. Gap: self-service tool discovery sub-topic. |
| [KA12.2](ka12-adoption-enablement.md#transfer-packages-enablement-kits) Transfer Packages & Enablement Kits | **Current** | CSV export, batch extraction, domain context transfer, AI-assistant capability transfer. Multiple packages across different adoption scenarios. |
| [KA12.3](ka12-adoption-enablement.md#pilot-design-execution) Pilot Design & Execution | **Current** | Simulation protocol with friction logging. A batch-metadata pilot pattern documented with the full artifact chain, across multiple workload domains. |
| [KA12.4](ka12-adoption-enablement.md#scaling-patterns) Scaling Patterns | **Seeded** | A typical annual target set references double-digit team adoption. Scaling constraint identified (embedded-support model doesn't scale). The adoption architecture is decided (production central / adoption franchise; five design surfaces named) — what doesn't exist is its enterprise instantiation, the operational playbook. **This is the primary gap in KA12.** |
| [KA12.5](ka12-adoption-enablement.md#ai-mediated-practice-distribution) AI-Mediated Practice Distribution | **Current** | Multiple mechanisms documented. Two enterprise-scale patterns in view: methodology-as-agent-skills and crowdsourced agent libraries. |

**KA12 summary:** 4/5 topics Current, 1 Seeded. The gap is [KA12.4](ka12-adoption-enablement.md#scaling-patterns) (Scaling Patterns) — the principles exist but the operational playbook for enterprise scaling doesn't.
