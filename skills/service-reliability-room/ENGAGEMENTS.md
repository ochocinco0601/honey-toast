# Engagements: what the room is being used for decides the engagement

**These are read after the first look, not from the request's words.** Pointed at a capability, the room's first piece of work is the fixed start in `OPERATING-MODEL.md` (what it is, what it is part of, whether its business flow observability has been done), agreed with the person before anything else (SKILL.md, step 1). A request's label ("production readiness", "backfill") names where the person wants to end up; the engagement below is chosen, provisionally, once the looks show where the capability really stands, and chosen again if the work contradicts it. It sets the situation questions and practice that inform the five the person agrees (SKILL.md, step 2); it never replaces them.

The room is used four ways. Each is a different engagement, with its own situation to understand, practice, seats, outputs and finish:

1. **Design for operations:** making a capability observable and operable while it is designed or built, or recovering that design for one that never had it.
2. **Production readiness:** getting a capability ready to be supported, before launch, as a backfill for one already live with too little behind it, or before a change.
3. **Triage:** helping with an event happening now: an error, an alert, a health question.
4. **Learning:** taking an incident, a postmortem or a failure-mode review back to the business flow's observability, to find which measurement was missing or needs to change, and writing it back.

In the field's terms these are the phases of the ITIL v3 service lifecycle after strategy: service design, service transition, service operation, continual service improvement (ITIL 4 replaced the lifecycle with the service value system; the v3 phases remain the common reference). The SRE engagement model (*SRE* book ch. 32) covers the first two: early engagement and the production readiness review. Where the person's own published method names a lifecycle or practice areas (for example an observability body of knowledge with stages such as define, implement, enforce, observe, respond, and an incident-response area with its own triage method), the agreed looks find it and the room works to it and uses its names: define falls in design; implement and enforce (conformance before production) in readiness; observe and respond in triage; respond's feedback to definition in learning.

An ask lands in one of these, often two (an error in hand that becomes a postmortem; a backfill that finds the flow was never designed). The engagement sets what the room must understand before it plans, the practice it works to, its seats and work skills, its outputs and when it is done. The rungs (SKILL.md) order what gets built inside an engagement.

**In every engagement:**
- **Before the five are agreed, only what the agreed looks can answer, or mark unknown.** Journeys, measures, thresholds and causes come from the work and go in the report.
- **Start from the capability's existing record** where one exists: its business flow register, home pages, open items.
- **Where the team file does not record it, ask (once, in the proposal of the five, with a proposed default) where the team keeps such pages, and who will accept the result.** Done includes the person holding the result as one page they can open (SKILL.md, step 7).
- **Real work where it has access, drafts where it does not.** Where the person's Claude Code can reach a tool (a monitoring tool, a dashboard, a ticketing system), the room does the work there, within what the owner approves. Where only people can reach it (often alert routing, the event pipeline, paging, change records), it drafts the change, says who must make it, and records whether it has been shown to work.
- **Signal layers.** Where the person's method classifies signals by layer (for example business impact, business health, application, system), every measure, health condition and gap is placed on a layer.
- **Agent steps.** Where the flow has a step taken by an AI agent: what it decides, where its inputs, outputs, prompts and model versions are recorded, how long that evidence is kept, and whether that tool feeds the alert pipeline. A wrong decision with healthy systems (the confidently-wrong failure) is its own failure mode.

## 1. Design for operations

- **When:** the capability is being designed or built, or is live and nobody can say what its business flow is or what to measure. "What should we monitor on X", "what can we see on X", "make X observable".
- **Practice:** design for operations; operability as a design requirement (ITIL service design, including availability management's failure analysis); failure mode and effects analysis (IEC 60812) for what has not yet failed; the person's method's definition stage (business context, stakeholder expectations, signal design).
- **The situation to establish:**
  - Is the business flow written down anywhere (a process map, an existing register), or only implied by the code? Which repositories and teams implement it?
  - What telemetry exists per component (logs, metrics, traces, health endpoints), and which tools hold it?
  - Is there any recorded statement of what the business expects of it (targets, obligations, stakeholder expectations)? Usually there is not; the room then drafts proposed expectations for the product owner to ratify.
  - Does the team or organization have a failure-mode analysis framework or existing failure-mode inventories (including shared dependencies across several capabilities)?
  - Who owns the design decisions, and is there still time to change the code?
- **Seats and work skills:** `srr-observability` running the business flow observability activities, the default spine (`OPERATING-MODEL.md`), with `bfo-stage-kit` (maps one flow and drafts each stage's measures, failure modes, alerts and runbooks into a register) or `design-for-operations` (recovers the flow from evidence and drafts its observability specification), whichever the team file lists; `srr-transition` for what the developers have already recorded.
- **Outputs:** the business flow with its stages and the code behind each; per stage, the stakeholder expectation (proposed where none exists), the measures on each signal layer and what healthy means; the failure modes per stage and shared dependency, each with the measure that would detect it or a gap; what cannot be seen today, as instrumentation requests to the developers with the proposed change.
- **Done:** every stage has a proposed expectation and a proposed health measure or a filed request that would make one possible; every known failure mode has a detecting measure or a recorded gap; the owner has the requests.
- **Hands on to:** readiness, once instrumented.

## 2. Production readiness

- **When:** a capability is about to go live, is live with too little behind it (backfill), or a change is about to land. A test or demo system is treated as pre-launch. "Get X ready", "X went live with almost nothing", "we're adding Y to X".
- **Practice:** the production readiness review (*SRE* book ch. 32); service transition with acceptance criteria, knowledge transfer and early life support (ITIL); the reliability hierarchy for order (*SRE* book part III); the person's method's enforce stage and the team's runbook standard.
- **Scope, stated in the readiness summary:** the room covers the review's monitoring, alerting, emergency response (runbooks, triage, escalation) and dependency areas, and what the change or release gate asks of those. Where the person's ask includes them, it also covers expected volumes and baselines (for an agent, its normal call and error rates). Capacity planning and the running of change management itself are named as outside this engagement, with who owns them, not silently dropped.
- **The situation to establish:**
  - Live or not; any go-live or change date; which change or release gate this readiness feeds (an approval, an attestation, a permit to operate) and what that gate asks for.
  - Per rung, what the agreed looks found: health views and health-check pages; alerts, the tool each comes from, and whether that source reaches the event pipeline and paging at all; runbooks and component pages and where they live; owners and on-call.
  - The team's alert tiers or ordering, if it has one (for example component up, then integration, then functional).
  - What the team has already gathered (pages, spreadsheets, baseline sheets), and by whom.
  - What depends on this capability, and what it depends on, so gaps can be ranked.
  - Which tools the room can read, and which changes only people can make.
- **Seats and work skills:** `srr-observability` running the business flow observability activities, the default spine (`OPERATING-MODEL.md`), through `bfo-stage-kit` where the flow is not yet mapped from its code; `srr-transition` alongside and launched first, for what is already recorded, feeding the flow work; `srr-alerting`; `srr-runbooks`, to the team's runbook standard where found, otherwise the `runbook-basics` skill where the team has it; `srr-review`; the tabletop walk (SKILL.md, step 6).
- **Outputs:**
  - where it stands on each rung, per journey;
  - a health-check page per capability for health questions that do not start from an alert: the question, the views to open, what normal looks like, where to look next;
  - component pages, each with its dependencies, failure modes and triage, entered from the alert index and from the health check, not only from an alert;
  - alerts per broken expectation, in the team's tiers, each with whom it reaches, how, and the test that proves it;
  - a runbook entry per alert, in the team's form, walked;
  - requests to the developers;
  - shortfalls as owned items, ranked by tier and by what depends on them;
  - a readiness summary against the team's runbook standard and readiness criteria, mapped to what the change gate asks for.
- **Done:** at the end point the person set, each journey has a health check, component pages, alerts drafted or live with their route named and whether the source reaches the pipeline, and a walked runbook entry per alert; every gap is an owned item. Proven only when the team fires an alert and it reaches someone.
- **Hands on to:** triage (the team runs it with these); learning, for shortfalls.

## 3. Triage

- **When:** an event happening now: an error, an alert, an incident ticket, or a health question with no event behind it. "I've got this error", "this alert fired and nobody knows what it means", "what's the health of X?"
- **Practice:** the person's method's triage where it has one (for example: read which signal layers are affected in combination, not the single alert; judge business impact; identify the stakeholder; pick the investigation path by pattern: sudden drop, gradual degradation, intermittent, business logic, confidently-wrong decision); effective troubleshooting, stop the bleeding before finding the cause (*SRE* book ch. 12); the criteria for declaring an incident (*SRE* book ch. 14); ITIL incident management, and event management for a health question.
- **The situation to establish, fast and read-only:**
  - The entry point: the ticket or alert, and what the team's triage surface already shows for it (correlated alerts, related changes, a generated summary). Where the room cannot reach it, the person pastes it once.
  - What was seen, where and when; whether it is still happening; which signal layers it shows on.
  - Where it sits in the business flow, as far as the room's map reaches: stage, step, component, dependency.
  - What changed recently (deploys, configuration, model or prompt versions), and for a claimed fix, whether its diff changes what fails.
  - Whether an alert, health check, component page or runbook entry already covers it.
  - Who owns the component and who is on call.
  - Evidence that expires: any source that keeps it briefly (an AI observability tool with a short retention, for example); capture it now.
- **Seats and work skills:** `srr-investigation` first, read-only; `srr-observability` for a health question, from the capability's health-check page where one exists.
- **Outputs:**
  - **First, as soon as known and revised as evidence arrives:** how bad it is on the business layers, the mitigation to try first (for a recent change, rolling it back through the organization's emergency change process), any workaround, whether it meets the criteria to declare an incident or raise it to the organization's major-incident process, and whom to engage.
  - Then what the evidence shows, with what is confirmed kept apart from what is a hypothesis.
  - Then where the event belongs: a missing measure, an alert, a runbook branch, a correction to the room's map, or outside the map (a stage, step or dependency the flow never modelled).
  - Where the cause is understood and a workaround exists: a known error for problem management, as a request to the developers and a runbook branch.
- **Not the room's job:** running the incident. A large event runs through the organization's own major-incident process; the room supplies evidence to the person in it.
- **Done:** service restored and verified by the person or the team, or the event handed to whoever holds the incident; the event placed and handed on.
- **Hands on to:** learning, always.

## 4. Learning

- **When:** after an incident, including one that never became a ticket; a postmortem to be taken back to the flow; a re-run of the failure-mode review for a stage an incident hit; a second pass after "you missed something"; alerts that page with no action or no longer match the flow.
- **Practice:** the person's method's feedback to definition (incidents reveal gaps in business context, signal design, visualization and threshold quality); the blameless postmortem (*SRE* book ch. 15; *SRE Workbook* ch. 10); problem management (ITIL); continual service improvement (ITIL).
- **The situation to establish:**
  - The record: the incident ticket or postmortem if one exists; otherwise the timeline is rebuilt after the go from logs, change records and the people involved.
  - The flow's register for the affected flow: its stages, and per stage the stakeholder expectations, measures, failure modes, alerts and runbook entries recorded today. If there is none, the flow has not been through design, and the engagement starts there.
  - Where the event sits in that flow: stage, step, dependency.
  - Impact at that stage: the transactions or customers affected and for how long, judged against the stage's recorded stakeholder expectation; if none exists, one is proposed.
  - Detection: what detected it (an alert, a customer contact, staff) and when, against when it started; which of the stage's measures moved and when, or that none did.
  - Where platform and change events are recorded (restarts, deploys, configuration, model or prompt versions), and whether the room can read them.
  - Action items from earlier postmortems on this flow: each with its owner, due date and whether it is done.
- **Seats and work skills:** `srr-investigation` for the timeline, trigger and contributing factors; `bfo-stage-kit`, taking the postmortem as a new-pass source on the affected stage (its fill steps, "when something new arrives"): each gap becomes a cited measure, failure-mode or remedy row, and the stage's measures, alert and runbook drafts are regenerated, with the incident's own values (time to detect, counts) kept in the incident record; `srr-observability`, `srr-alerting` and `srr-runbooks` for what the regenerated drafts need; `runbook-basics` in its iterate mode for pages outside the kit.
- **Outputs:**
  - **The timeline, the trigger kept apart from the contributing factors,** what went well, what went wrong and where the team got lucky, without blame.
  - **A measurement gap analysis for the affected stage,** classifying each detection failure, with evidence from the record, and naming the practice area it feeds back to:
    - outside the map: the stage, step or dependency was never modelled (business context);
    - no measure existed for what failed (signal design);
    - a measure existed but no alert was defined on it (signal design);
    - an alert was defined but its condition or threshold missed the failure (standards and threshold quality);
    - the alert fired but did not reach the right responder, or was not acted on (incident response: routing and escalation);
    - the stakeholder or expectation that should have set severity was missing (business context);
    - the view the responder used lacked the context to see it (monitoring and visualization);
    - the runbook entry was missing or wrong (incident response: playbooks).
  - **Each gap written back into the flow's register** as cited rows, and the stage's drafts regenerated. Where the stage's customers were not affected, the new detector raises a ticket rather than a page.
  - **Action items** with owner, priority, type (mitigate, prevent, detect) and due date, tracked to done, including the earlier ones still open.
- **Done:** each detection failure is classified with evidence; each gap is a cited row in the flow's register with its drafts regenerated; each action item has an owner, priority and due date.
- **Hands on to:** design or readiness, closing the loop.

## In the proposal of the five (SKILL.md, step 2)

Name the engagement or engagements and why, in the person's own method's names where it has them. Then the situation as that engagement defines it, from its questions, with what the agreed looks found and what is still unknown. Then the five, in the person's terms (what they will get, how far it goes, when they will be asked to look); the kinds of output with their shape, what is out of scope and where it ends are recorded behind them, not put to the person row by row. Asks that fit none of the four, such as a standard, a training kit or a summary for leadership, are another audience's ask (SKILL.md, "An ask for another audience").
