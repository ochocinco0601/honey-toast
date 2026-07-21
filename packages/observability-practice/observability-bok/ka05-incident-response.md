# KA05 — Incident Management & Response

**Category:** Core Practice

**Lifecycle stage:** Respond

**Primary owner:** SRE / Ops

**Question this KA answers:** When something fails, what do we do?

---

## 1. Purpose & Scope

This KA covers what happens when things break. [KA04](ka04-monitoring-visualization.md) surfaces the signals. KA05 acts on them — triage, escalation, playbook execution, postmortems, and the feedback loop that turns incidents into improved definitions. KA05 completes the observability lifecycle (Define → Implement → Enforce → Observe → **Respond**) and feeds back to [KA01](ka01-business-context.md) (Define), making the lifecycle iterative rather than linear.

**What's in scope:**

- Triage and severity determination — business-context-aware incident assessment
- Escalation and team composition — who gets called, role-based response
- Playbook design and execution — pre-built response procedures tied to signal patterns
- Postmortem and learning — structured incident review and improvement actions
- Feedback to definition — incidents reveal gaps in business context, completing the lifecycle loop

**What's out of scope:**

- Monitoring and alerting configuration ([KA04](ka04-monitoring-visualization.md)) — KA05 starts when the alert has already fired
- Platform tooling for incident management ([KA06](ka06-platform-tooling.md)) — BigPanda, PagerDuty are tools; KA05 is the practice
- Organizational incident management processes ([KA11](ka11-organizational-capability.md)) — team structure and rotation are organizational capability

---

## 2. Domain Knowledge

### Triage & Severity Determination

Business-context-aware triage uses the four-layer model to assess severity:

1. **Which layers are affected — read the combination, not the single alert.** The named cross-layer correlation patterns ([KA04](ka04-monitoring-visualization.md#cross-signal-correlation)) are the triage decision surface. A Business Health breach with System/Application green is **Silent Business Failure** — a business logic problem, the pattern traditional monitoring cannot see. A System breach propagating through Application to Business Health is **Infrastructure Cascade** — classic infrastructure incident with business impact. And System degraded with nothing propagated is **Infrastructure Noise** — a real alert that warrants monitoring, not escalation. Half the patterns exist to *suppress* false urgency; triage that knows only the escalate-side patterns over-responds to noise. For services with an agentic step, Silent Business Failure has a second investigation branch: the step may be *confidently wrong* — deciding badly while every mechanism signal is green — so the descent continues into the Agent Workflow stratum ([KA02](ka02-signal-design.md#signal-type-taxonomy)).
2. **What's the business impact?** Business Impact signals quantify: how many customers affected, how much revenue at risk, what compliance exposure. This drives severity — not just "is it down?" but "how bad is it for the business?"
3. **Who's the stakeholder?** The stakeholder expectations from [KA01](ka01-business-context.md) tell you who cares. A CRITICAL expectation from a regulatory body is higher severity than a MEDIUM expectation from an internal team.

A structured triage framework provides the decision tree:

- **Severity assessment** — % deviation from SLO, impact scope (single service vs cascade), stakeholder priority
- **Investigation path selection** based on regression pattern (sudden drop, gradual degradation, intermittent, business logic)
- **Escalation criteria** — when the first responder needs help, who to contact

### Escalation & Team Composition

Who gets called depends on the layer affected and the severity. A reference escalation model:

| Affected Layer | First Responder | Escalation Path |
|---------------|----------------|----------------|
| Business Impact | Incident commander | Cross-functional response: PO + Dev + SRE + leadership |
| Business Health | PO + Dev on-call | Business escalation + technical investigation |
| Application | Developer on-call | App team → Dev lead → Architecture |
| System | Platform/SRE | Infrastructure team → Platform lead |

### Playbook Design & Execution

Playbooks are pre-built response procedures tied to signal patterns and business context. A playbook answers: "This alert fired. Now what?"

**Investigation templates by failure mode** (from the triage framework):

- **Sudden drop** — check for: deployment events, circuit breaker activation, upstream dependency failure. Start with: change timeline, dependency health map.
- **Gradual degradation** — check for: resource exhaustion, data growth, queue backlog. Start with: trend analysis, capacity metrics, queue depths.
- **Intermittent issues** — check for: network instability, race conditions, timeout patterns. Start with: error distribution by time/geography, retry rates.
- **Business logic failure** — the business-observability-specific pattern: System/Application healthy, Business Health failing. Check for: business rule changes, configuration drift, data quality issues, upstream data staleness.
- **Confidently-wrong decision** *(services with an agentic step — the agent-stratum variant of Silent Business Failure)* — System/Application healthy, Business Health failing, and the failing function contains a judgment step. Check for: correctness against the eval reference (golden-set or judge agreement over the affected window), grounding failures (outputs unfaithful to inputs), a changed decider (model/prompt/ruleset version — note that a silent fallback changes the decider), input-mix or decision-distribution drift. Start with: the Agent Workflow descent under the breached Business Health signal, then decision provenance for the affected window.

**The structural investigation path.** For services onboarded with the current capture instrument, every signal carries an assembled **descent link**: signal → layer → business-process step(s) → sub-capability → component → endpoint → diagnostic signals → what to check when the diagnostics are healthy. This is the investigation path the on-call engineer follows when a signal degrades — produced at definition time and reviewed by the on-call engineer, so investigation starts from structure rather than from zero. The failure-mode templates above complement it: the descent link says *where* to look; the failure-mode checklist says *what* to look for.

A complete playbook artifact is a runbook tied to specific alert conditions with step-by-step response procedures.

### Postmortem & Learning

Structured incident review that captures what happened, why, and what to improve. The learning loop that prevents the same incident from recurring.

Prior art: Google SRE blameless postmortem methodology — focus on systemic causes rather than individual blame, timeline reconstruction, action items with owners and deadlines. Applied to business observability, postmortems additionally interrogate the stakeholder-expectation chain: was the right expectation measured? Was the impact category correctly classified? Did the signal catch the condition in time?

### Feedback to Definition

The lifecycle feedback loop: incidents reveal gaps in business context definitions ([KA01](ka01-business-context.md)). This is the mechanism that makes the observability lifecycle iterative:

- A postmortem discovers "we didn't know who the affected stakeholders were" → [KA01](ka01-business-context.md) gap: missing stakeholder definition
- An incident reveals "we had no signal for this failure mode" → [KA02](ka02-signal-design.md) gap: missing signal design
- Triage took too long because "the dashboard didn't show the relevant context" → [KA04](ka04-monitoring-visualization.md) gap: visualization missing business context
- Alert fatigue caused missed escalation because "too many low-priority alerts" → [KA03](ka03-standards-quality.md) gap: threshold quality

The operational mechanism to institute: postmortem review triggers explicit service profile updates when incidents reveal missing context — a specific stakeholder wasn't captured, an impact category was undercounted, a threshold was too lenient. Without this trigger, the feedback loop runs on memory, not process.

---

## 3. Practices & Processes

### The Incident Response Workflow

```
1. Alert fires          → KA04 monitoring detects threshold breach
2. Triage               → Assess severity using Business Health/Business Impact business context
3. Investigate           → Follow failure-mode-specific investigation template
4. Escalate (if needed) → Role-based escalation per layer and severity
5. Resolve               → Execute playbook, restore service health
6. Postmortem            → Structured review: timeline, causes, actions
7. Feed back             → Update KA01 definitions, KA02 signals, KA04 dashboards
```

### Inputs and Outputs

| Input | From | Used for |
|-------|------|----------|
| Alerts, monitoring data | [KA04](ka04-monitoring-visualization.md) | Trigger and context for incident response |
| Stakeholder expectations, impact categories | [KA01](ka01-business-context.md) | Severity determination, stakeholder notification |
| Playbooks, runbooks | [KA03](ka03-standards-quality.md) (templates) | Pre-built response procedures |
| Team structure, skills | [KA11](ka11-organizational-capability.md) | Who's available and capable for response |

| Output | To | Purpose |
|--------|-----|---------|
| Incident learnings | [KA01](ka01-business-context.md) (Business Context) | **The lifecycle feedback loop** — incidents reveal definition gaps |
| Postmortem action items | [KA02](ka02-signal-design.md), [KA03](ka03-standards-quality.md), [KA04](ka04-monitoring-visualization.md) | Signal design improvements, standard updates, dashboard fixes |
| Incident metrics | [KA13](ka13-continuous-improvement.md) (Continuous Improvement) | MTTR, incident frequency, resolution patterns |

---

## 4. Roles & Responsibilities

| Activity | Product Owner | Developer | Platform/SRE | Incident Commander |
|----------|:---:|:---:|:---:|:---:|
| Triage and severity assessment | Informed (business context) | Participate | **Own** | **Own** (high sev) |
| Technical investigation | — | **Own** (Application/Business Health) | **Own** (System) | Coordinate |
| Stakeholder communication | **Own** | — | — | Coordinate |
| Playbook execution | — | Execute | Execute | Direct |
| Postmortem facilitation | Participate | Participate | Participate | **Own** |
| Feed back to definitions | **Own** (update profiles) | **Own** (update signals) | **Own** (update thresholds) | — |

---

## 5. Tools, Artifacts & Techniques

### Practice Instruments (from [catalog](instruments/README.md))

These instruments operationalize KA05 knowledge — a practitioner doing incident response work reaches for these.

| Instrument | Type | What it does for this KA |
|-----------|------|-------------------------|
| [IN-06 Stakeholder Expectation Template](instruments/in-06-stakeholder-expectation-template.md) | Definition | Stakeholder expectations determine incident severity and triage priority |
| [IN-12 Alert Factory](instruments/in-12-alert-factory.md) | Production | Generates alert rules that trigger incident response |
| [IN-13 Playbook Factory](instruments/in-13-playbook-factory.md) | Production | Generates response playbooks from service context and signal patterns |
| [IN-23 Observability Standard](instruments/in-23-observability-standard.md) | Definition | Form C rehearses KA05's incident questions against the record before incidents ask them |

### KA-Specific Artifact Types

| Artifact type | What it contains |
|--------------|-----------------|
| SLI triage framework | 5-phase investigation, failure-mode templates, decision tree |
| Worked incident playbook | Complete playbook artifact for a specific incident class (e.g., batch-job reconciliation) |
| Foundational principles | Lifecycle feedback concept — incidents feed definition updates |

### Techniques

- **Business-context-aware triage** — use Business Health/Business Impact signals and stakeholder priorities to determine severity, not just technical indicators
- **Failure-mode investigation templates** — sudden drop, gradual degradation, intermittent, business logic. Each has a starting checklist.
- **Lifecycle feedback** — every postmortem should check: "what was missing from our definitions that would have prevented or accelerated this?"

---

## 6. Connected KAs & External References

### Adjacent Knowledge Areas

| KA | Relationship | What flows |
|----|-------------|-----------|
| [KA04](ka04-monitoring-visualization.md) — Monitoring & Visualization | KA05 **depends on** [KA04](ka04-monitoring-visualization.md) | Response depends on monitoring detecting the problem |
| [KA01](ka01-business-context.md) — Business Context | KA05 **feeds back** to [KA01](ka01-business-context.md) | Incidents reveal business context gaps — completes the lifecycle loop |
| [KA11](ka11-organizational-capability.md) — Organizational Capability | KA05 **depends on** [KA11](ka11-organizational-capability.md) | Effective response requires the right people with the right skills |
| [KA13](ka13-continuous-improvement.md) — Continuous Improvement | KA05 **feeds** [KA13](ka13-continuous-improvement.md) | Incident learnings feed continuous improvement — postmortem findings become practice changes |

### External References

| Reference | Relevance |
|-----------|-----------|
| Google SRE Book — Postmortem chapter | Blameless postmortem methodology |
| PagerDuty Incident Response documentation | Incident commander model, escalation patterns |
| ITIL Incident Management | Enterprise incident management framework |

---

## 7. Content State & Gaps

### Per-Topic Content Audit

| Topic | State | Notes |
| ------- | ------- | ------- |
| [KA05.1](ka05-incident-response.md#triage-severity-determination) Triage & Severity Determination | **Current** | Actionable triage framework with business-context-aware severity. |
| [KA05.2](ka05-incident-response.md#escalation-team-composition) Escalation & Team Composition | **Seeded** | One team structure example. No escalation matrix or role-based response model. |
| [KA05.3](ka05-incident-response.md#playbook-design-execution) Playbook Design & Execution | **Seeded** | Investigation templates exist but not formatted as standard playbook templates. |
| [KA05.4](ka05-incident-response.md#postmortem-learning) Postmortem & Learning | **Missing** | External prior art: Google SRE blameless postmortem methodology. |
| [KA05.5](ka05-incident-response.md#feedback-to-definition) Feedback to Definition | **Seeded** | Concept documented. No operational mechanism for systematic feedback. |

**KA05 summary:** 1/5 Current, 3 Seeded, 1 Missing. Weakest core practice KA. Incident response is the least developed lifecycle stage. The lifecycle feedback loop (KA05 → [KA01](ka01-business-context.md)) is conceptually established but not operationally implemented.
