# Design for Operations

*A reference for deriving business-grounded observability from what systems actually do.*

---

## What this method does

This method takes one business capability and produces a monitoring specification for it: which crossings matter, which signals to place, what healthy means, and what cannot be measured at all.

It composes established practices. **Recovering the structure** — software architecture reconstruction, or process mining and distributed tracing where runtime evidence exists. **Reconciling it against a stated architecture** — the software reflexion model. **Drafting the business layer** — from published reference models: BIAN, APQC's process classification framework, ACORD, eTOM, MISMO. **Selecting what matters** — critical user journeys. **Specifying measurement** — service level indicators and objectives, and the golden signals. **Keeping it from decaying** — architectural fitness functions.

**Two of the passes below have no established name** — tailoring an industry reference model to a firm, and the inventory of what starts work. **Unnamed is not unstudied, and the two absences cash out differently.** The entry-point inventory is performed inside security's attack-surface work: inherit that apparatus by reading — borrow the checklists, change the done-condition from exposure to completeness. The tailoring is performed tacitly wherever these models are adopted: inherit it by staffing — a modeller carries it, no literature does. **What is bare either way is the practice under this purpose, so a failure mode found here is worth writing down: for this purpose, nobody else has.**

The question it answers — is the business process working — is the one business activity monitoring names. **It sits on top of monitoring organised by system, not in place of it.** Per-service signals remain what tells you whether each part is healthy; they cannot tell you whether the journey across them completed.

## What this write-up assumes

The passes below are written for one configuration: the code as the source of structure, an industry model as the source of the business layer, in an estate where architecture documentation exists but cannot be trusted and where the people who could explain the systems have limited time or have dispersed. **Those are the conditions this write-up was drafted against, not conditions the method requires.**

The common case is an operations team doing the work, with architects and application teams consulted rather than running it. That is a default, not a requirement. Each pass names the input it needs and who has to supply it, and nothing here depends on a particular team owning the whole.

It is written to be worked from, not read through. The four concerns and the vocabulary are the parts to internalise; the passes are the parts to have open while working.

**On everything stated as a rule below.** Each is a default with its reason attached, and the reason is the part that matters. Where the reason does not hold for you, vary the rule deliberately. What this guards against is a team inheriting a constraint nobody chose and paying for it as though it were the cost of the method.

### What else there is, and when to open it

This document is the method. One companion carries the target it aims at:
[`what-good-looks-like.md`](what-good-looks-like.md) — three stacked views over one capability,
and what each may **not** claim. Open it before starting, so "done" is settled before the method
is judged.

### The standing of this document

The form here follows the Google SRE book, and the difference in standing should be stated rather than hidden: that book codified a practice already proven by years of operation. This document's standing splits in two, and the split follows its own vocabulary.

Nothing here is bespoke at the component level — that was a design constraint. Every borrowed element is established practice with its own empirical record: architecture reconstruction, realisation links, boundary-based signal placement, symptom-based paging, reference-model drafting, lineage. Part VIII names each record and where it stops applying. Those claims are *derived* — their source is the industry's practice, not this method.

What has not yet been run end to end is the *composition*: this sequence of passes, the joins between the borrowed parts, the four concerns as a stopping condition, the placement of the checkpoints. Those claims are *proposed* — reasoned, but awaiting their first full run. And composition is exactly where methods fail even when every component is proven; that is this document's own central thesis about layers and joins, and it applies to the method itself.

Pass 7 is the upgrade mechanism. Each capability the method is run against either confirms a composition claim, revises it, or kills it. Expect this document to be revised, and distrust any version of it that has stopped being.

### What a prior-art check found

Two things this document treated as its own turned out to be established practice, and both are now
named where they are used: **pass 4 is an instance of traceability link recovery**, and **the four
questions are competency questions**. Two positions it stated as findings are published findings —
that code shows what can happen and a person supplies the rest, and that static and runtime evidence
disagree usefully.

What survived is narrower than what was claimed, and one survivor is unreliable: a trace that
terminates in a displayed measurement is the sharpest remaining claim, and it has not been
independently checked. **Do not build on it without re-checking.**

## Part I — The problem

### Instrumentation coverage is not observability

The characteristic enterprise failure is this: instrumentation is mandated per component, every component complies, and the organisation declares the observability problem solved. Then an incident arrives and nobody can answer the only questions that matter — where in the business process did this break, and who is affected.

The mandate is not wrong; it is misdescribed. It treats a precondition as an outcome. Metrics, logs, and traces are raw material. The failure is one of composition, not coverage: no component knows what stage it serves, and no per-component requirement can fix that in principle. Traces are paths, but unnamed ones — you can watch a request traverse six services and still not know which business outcome it was pursuing.

### Business process flows are what break; systems are what you own

Teams build and own systems. Business capabilities cross them. When something breaks in a way the business notices, it breaks as a business process flow — a work item that stalls between systems, a payment that enters one side and never emerges from the other. Monitoring organised by system answers "is my box healthy" and structurally cannot answer "is the business process working," because the business process was never a first-class object in the monitoring at all.

This is Conway's Law surfacing in observability: the business process flows that matter most cross boundaries nobody owns end to end, and the monitoring inherits the org chart.

### The models are wrong, and that is workable

Where architecture models exist — C4 diagrams, architecture-description languages, configuration-management database entries — they describe intent at the moment someone wrote them, and nothing forces an update when reality moves. Application teams will confirm the models are stale; this is normal, not scandalous.

The method treats this as material rather than obstacle. Code is source; everything else is corroboration. Code cannot be stale relative to itself. A contradiction between the code and a secondary artefact is not noise to be cleaned before the real work starts — it is a finding, and often the most valuable one produced. Drift is the deliverable.

---

## Part II — Principles

Each principle is stated with the failure it prevents. A principle without its counterexample reads as style preference and gets dropped under pressure.

**The unit of work is the business process flow, not the system.**
Otherwise the monitoring reproduces the org chart, and the incidents that cross team boundaries — the expensive ones — remain invisible until a customer reports them.

**Operations is a viewpoint, not an afterthought.**
Rozanski and Woods name the *operational viewpoint* alongside functional, information, concurrency, development and deployment — the architectural view concerned with how a system is run, administered and supported once live. This method is a way of constructing that viewpoint when nobody constructed it up front. Without that framing the work reads as monitoring cleanup somebody should have done earlier, and it gets funded like cleanup.

**Code is source; everything else is corroboration.**
Otherwise effort goes into reconciling documents with each other, producing agreement between two artefacts that are both wrong.

**The evidence is static by choice — and the choice has to be made rather than inherited.**
These passes read code. Two established routes recover the same picture from runtime instead: distributed tracing, where the service map draws itself from live traffic, and process mining, which derives the actual business process from event logs the systems already emit. Static reading shows what the code *can* do; runtime evidence shows what it *does* do, and misses paths that did not execute. They disagree, and the disagreement is a finding. **This is a published result, not a position taken here:** the business process recovery literature treats the hybrid as the remedy — models recovered statically are repaired against event logs, and running logs are combined with static analysis precisely because neither alone is complete. Where tracing already exists it is usually the cheaper first look, and a team that never considered it pays to read code it could have watched.

**The accuracy bar is fitness for signal placement.**
A corrected model must be right about what exists, what calls what, and where boundaries sit. It does not need the semantic rigour architects demand of their own artefacts. State this bar explicitly to anyone — human or agent — doing correction work, or effort drains into naming conventions instead of topology.

**Every claim carries lineage, walkable in both directions.**
Dashboard claim → stage → signal → traced path → location in code. Forward, it builds: each link is evidence for the next. Backward, it defends: someone challenges a number on a dashboard, and you walk to the file instead of arguing from memory. And it converts silent decay into a detectable event — observability estates rot because dashboards keep rendering after the code has moved, with nothing connecting the two. When a traced path changes, lineage names which dashboard claims are now suspect.

**Every claim is tagged derived or proposed.**
Derived has a citation and is wrong only if the code changed. Proposed is inference. The two cannot share a voice in one artefact, because plausibility without provenance is indistinguishable from evidence at reading speed. Uncited output — human or agent — is net-negative, not merely imperfect: disproving it costs more than producing it did.

**It is a draft-generation method with review gates, not a discovery method.**
Never ask a human to produce from nothing what a machine can propose for them to judge — recognition beats recall at every layer. Drafts are generatable; nothing is authoritative until someone says yes. The scarce resource is business attention, and this is how it is spent well.

**The business layer is normative; the application and technology layers are derivable.**
What the business process *should* be is a human claim. What the systems *do* is extractable. The two meet at the realisation links — which application behaviour realises which stage — and that mapping is where the drift lives, because the layers are usually roughly right in isolation and nobody maintains the joins. The missing join is the actual deliverable.

**Code tells you what can happen, never what does.**
This is a category error, not a limitation — no amount of better reading extracts runtime facts from static text. Observed volume comes from telemetry. Expected volume is a business fact supplied by a person. A method that claims to derive throughput from code is lying about one of the two.
**Established, not local:** the business process recovery literature states the same limit as its own limitation — manual activities, process participants and concurrent tasks are not derivable from source, which is why recovered models do not reflect the original behaviour without a second source.

**A falsely-assigned boundary is worse than a visibly unowned one.**
An unowned boundary named as unowned is an actionable finding. The same boundary with a plausible name attached makes the organisational gap disappear from the artefact while leaving it entirely present in reality — and stops the escalation that was the only fix.

**Under-pruning is not the conservative choice.**
Everything downstream of pruning is expensive per business process flow. An unpruned list multiplies that cost through every remaining pass. Keeping a business process flow "to be safe" is a spending decision, and should be defended as one.

**No view may imply it answers another view's question.**
The characteristic failure: a diagram drawn in business process shape whose arrows are read as dependency claims. A stage goes red, responders trace along business process arrows hunting a cause that was never on those edges. Views state their question on their face.

---

## Part III — The three views and the four concerns

### The three views

The primary decomposition is by layer, and it is not this method's invention — it is ArchiMate's carving: business, application, technology. It is also what industry tooling already splits along. Each view is stated here with what it answers *and what it may not claim*, because the misreadings live in the second half.

**The business process view** shows the business process flow in the business's vocabulary: stages, in sequence, with health. It answers **impact and scope** — where the break is in business terms, what is cut off, what is still flowing. This is the object of what the industry has variously called business activity monitoring (Gartner's term, circa 2002), business transaction monitoring, and more recently business observability — New Relic's Pathpoint being the direct structural ancestor. Its audience includes people who will never open a technical tool. What it may not claim: it cannot answer cause — its arrows are sequence, not dependency, so there is nothing on it to follow toward a reason. And it cannot express severity: a red stage does not say whether that is ten transactions or ten thousand.

**The application process view** (ArchiMate: process realisation) shows the steps that realise those stages, including the retry and failure branches the stage knows nothing about. It answers **where** — which application step failed. This is the native territory of application performance monitoring, distributed tracing, and service maps — the mature tooling category. Its audience is responders. What it may not claim: it localises the failure but cannot *terminate* in cause. Cause runs along dependency edges, which live on the technology view; this view is where a responder narrows the search before descending to it.

**The technology view** displays the dependency relation — hosts, databases, network, message infrastructure, certificates, external endpoints. It answers **why**. This is where the dependencies that sit outside any business process sequence live, and it is the territory of infrastructure monitoring. What it may not claim: nothing on it says who is affected.

The views are joined by the realisation links from Part II, and kept separate because they answer different questions to different audiences. The industry has strong tooling for the second and third views and an emerging category for the first.

**On the joins — a claim this document has had to narrow.** An earlier version said the industry had almost nothing for them. That is false of the knowledge and true only of the products. Establishing a link between a coarse stage and the code that carries it out is studied under traceability link recovery, feature location and business rule mining. What remains genuinely thin is narrower: a trace that *terminates in a displayed measurement* and can mark it suspect when the source moves — the only claim no named practice covers, and the least trustworthy verdict in the check. Traceability tooling stops before runtime; measurement tooling carries no lineage back to source. See "What a prior-art check found" above, including why that particular finding needs re-checking.

### The four concerns

Each view is then interrogated, and the interrogations reduce to four concerns.

**A concern is what you interrogate a view *for*.** That is why the same concern is read from more than one view — Trend from all three — and why `the trend view` is a category error rather than a loose phrase: it names an interrogation as though it were a thing to look at. None of the four is novel; each stands in for an established practice.

**Using the set as the completeness criterion is not novel either, and it has a name: competency questions** (Grüninger & Fox, 1995, ontology engineering). The move is exactly this one — fix in advance the questions the finished artefact must be able to answer, use them to bound scope, and evaluate completeness by whether they can be answered rather than by coverage of the domain. The same device appears independently in intelligence production as priority intelligence requirements, and in performance auditing as objectives stated as questions, where sufficiency of evidence is judged against the questions rather than against coverage of the auditee. Three unrelated disciplines converging on one move is stronger evidence than any single citation.

The four below cover the common case and are a starting set, not a fixed one — add or drop to match what the operation actually has to answer. What carries the weight is that the set is settled before discovery starts, not that there are four of them.

The naming follows ISO/IEC/IEEE 42010: a view is a representation produced from a viewpoint, and a viewpoint *frames concerns*. Three views exist here — business process, application process, technology.

| Concern | What it asks | Read from which view | Relation it reads | Established practice it stands in for |
|---|---|---|---|---|
| **Impact** | Where in the business process did this break, and who is affected? | Business process | **Business process** | Blast-radius assessment; customer-facing SLIs; business activity monitoring. ITIL's *impact* is a rating derived from this, paired with urgency to set priority |
| **Cause** | What is broken underneath it? | Technology, localised via the application process view | **Dependency** | Dependency mapping and service maps; root-cause analysis; fault localisation |
| **Throughput** | Is work getting through at the expected volume? | Business process | *n/a — a measure over the business process relation, not a relation* | Traffic in the golden signals; the rate in RED (rate, errors, duration); flow metrics from value-stream management |
| **Trend** | Is it getting worse? | All three | *n/a — a time axis over any relation, not a relation* | Service-level-objective burn rate; error-budget consumption; degradation and anomaly detection |

**Two of the four are not relation-scoped at all, and the table says so rather than forcing a value.** Throughput is a measure taken over the business process relation; Trend is a time axis applicable to any of them. Only Impact and Cause read a relation directly. Putting a measure and a time axis on a relation axis is the same failure the next section argues against — more than one kind of claim on one axis.

**The four concerns are acceptance criteria for every pass.** A pass is complete when it has gathered what the concerns need — not when the system has been described. This supplies the stopping condition for the whole method: discovery without a target has no completion criterion — you can always trace one more path — so naming the concerns up front converts them from outputs into acceptance criteria. It also changes what you ask an agent for: "describe this system" is unbounded generation; "gather what these four concerns require" is bounded retrieval with a checkable result.

### Reading the views without being misled

This is the most load-bearing distinction in the method, and the one most people cannot see, so it gets the full argument rather than just the rule.

**Business process, dependency, and data movement are different relations over the same nodes** — not three drawings of one thing. Business process is sequence over time. Dependency is what needs what in order to function. Data movement is where state travels. They share nodes and do not share edges, which is exactly what makes the conflation easy to fall into and damaging when it happens.

Concretely: a dependency can sit entirely outside the business process sequence — a certificate authority, a configuration service, an identity provider are steps in no business process, and any of them can stop the business process dead. Data can move between stages that have no business process relationship. Business process steps can be adjacent in sequence while sharing no dependency at all.

**The failure mode, narrated.** Business process shape reads well to leadership, so the diagram gets drawn in business process shape. Under incident pressure, the arrows get read as dependency claims — an arrow *looks* like causation, and a person tracing back from a red box follows whatever arrows are in front of them. They trace upstream hunting the cause, and the cause is not there, because it was never on a business process edge. The merged diagram is not merely incomplete; it is actively misleading at precisely the moment its accuracy matters most, and it fails in a way that looks like the responder's fault rather than the diagram's.

**The fix is separation, not more detail.** Adding dependency edges to a business process diagram produces something unreadable and still ambiguous, because a reader cannot tell which relation a given edge expresses. Each view carries one relation and declares its question on its face — in the title, so the scope is legible without anyone reading a definition. And the set is not limited to three: control flow and value flow are distinct relations again. The general principle: any diagram must be a single relation, or it lies.

**Impact and cause are two questions, not one.** Both get called triage, and treating them as one activity is why bridge calls go in circles. Impact — what has stopped, who is affected, what is the scope — is answered from the business process view, and the inference is available from sequence alone: a failed stage blocks everything downstream while everything upstream keeps accepting work that is about to pile up. Cause — what is failing and what do I act on — is answered from the technology view, because causation runs along dependency edges. These are not phases of one activity done in order; they are asked *simultaneously, by different people, for different purposes*. The executive on the bridge needs the first and cannot use the second; the responder needs the second and is wasting time deriving the first. This is also why the views cannot be ranked — neither is the real one with the other as summary; either alone leaves someone in the room unserved.

The practical consequence: retire the phrase "what's broken" from incident language, because it resolves to two different sentences depending on who is asking. "Credit ordering has stopped and no new applications can progress" and "the bureau endpoint is timing out" are both correct answers to it, and neither substitutes for the other.

The same split settles alerting: one collapsed view cannot serve both alerting modes even in principle. Leading indicators are read from the technology view and lagging ones from the business process view, because causes precede symptoms and causes run along dependency edges.

**Trend is structurally different from the other three.** It is the only question whose job is to fire before anything is broken, which is why it cannot be folded into the others as a time axis.

---

## Part IV — Vocabulary

Precision here is what makes disagreement possible. These terms are otherwise used loosely, and every loose use eventually surfaces as a dashboard that misleads.

**Business process flow** — a path through the estate that realises a business outcome. The unit of observability. Its design-time form is the **intended business process flow**; its runtime form, recovered from telemetry, is the **observed business process flow**.
**Stage** — a business-meaningful segment of a business process flow. What the impact concern is read from.
**Step** — an application-level action within a stage. Exists at the altitude of the code — the level of granularity a description sits at — not the business.

**The stage test** — would a business person name it, and would they care if it stopped? If nobody in the business would name it, it is a step, not a stage, regardless of technical importance. Stages sit at whatever altitude the business talks at, not at the granularity of the code — this is what settles granularity arguments, by anchoring to a person rather than a structure.

**Convergence** — the model and the code agree. The part you stop checking, and the number that answers "how wrong was our architecture." Reporting it is what separates a reconciliation from a complaint.
**Divergence** — the code does something the model does not show. Usually means the code moved.
**Absence** — the model claims something the code does not do. Usually means the model described an intent never built — or the business believes something about its own business process that stopped being true.

**Declared sequence** — ordering written down as data because something needed it to execute: a business process engine definition, a job dependency graph, a pipeline dependency graph, a status enum with transitions. Wherever something had to declare sequence to execute, the business process flow comes free; where sequence is implicit in code, you pay for it.

**Derived / proposed** — the provenance tag on every claim. Derived cites a location; proposed is inference awaiting review.

**Observed volume / expected volume** — telemetry versus business fact. Different sources, never conflated.

**Leading / lagging** — leading says impact is coming; lagging says it has arrived. Different urgency, different routing. Pure symptom-based alerting always pages late — it cannot see work marching towards a cliff, where real impact exists but has not yet been realised.

**BPMN's two altitudes** — an analyst's BPMN diagram is business layer; an executable BPMN definition deployed to an engine is application layer. Same notation, different object. Comparing them is itself a drift check — and an executable definition cannot drift from behaviour, because it *is* the behaviour.

---

## Part V — The method

Seven passes. Each produces an artefact and ends at a human checkpoint, so a team can stop part-way and still hold something useful.

### How far to take it

Depth is not a rigour dial. It is a coverage choice on two axes Part III already defines — **how many business process flows**, and **how many concerns**. Narrow either one and every pass gets cheaper automatically, because the acceptance criteria shrank. Nothing else has to change.

| Run | Coverage | What you hold | What you cannot claim |
|---|---|---|---|
| **Proof** | 1 business process flow × 1 concern | A worked example, and evidence the approach survives contact with the code | Anything about the other business process flows |
| **Pilot** | 1 business process flow × all 4 concerns | A monitored business process flow, plus a template the next one inherits | Coverage |
| **Practice** | N business process flows × 4 concerns | A held practice — lineage maintained, drift caught when code moves | — |

These are named points on a continuous grid, not tiers with entry requirements — two business process flows and two concerns is a perfectly legitimate cell, it just does not have a name. State the cell before starting. Most of the argument about whether the method is too heavy dissolves once someone has to say which one they are in.

The depth chosen changes what the checkpoints are for. Citation discipline is the clearest case: at Pilot and above, a claim that cannot be traced to a location is a claim to discard, because the output has to survive being challenged months later. At Proof, an untraced claim the team recognises is worth keeping and marking as such. Citation is what makes a result defensible, not what makes it true.

The per-pass checkpoints are the other stopping points: each is a place to hold what exists and go no further.

### The order of the passes

The numbering is a default order, not a dependency graph. What genuinely constrains sequence is narrow: pass 2 needs pass 1; pass 4 needs passes 1 and 3; pass 6 needs passes 4 and 5. Pass 3 needs only the declared sequences pass 1 turned up. Everything else can move.

The move worth considering first: **pruning can run before tracing.** If the business can name the business process flows that matter up front, trace only those and never discover the surface you would have thrown away. That is usually the cheaper path. The order below assumes you cannot get that input early — which is common, because "which business process flows matter" is often a question people can only answer once they see candidates. Judge which situation you are in rather than inheriting the answer.

### Pass 1 — Discover the surface

Find the entry points and the runtime topology: what accepts work from outside, what the deployed units are, what talks to what. The activating question for sequence is mechanical: *what declares sequence?* Search for business process definitions, job graphs, dependency graphs, status enums with transitions — classify these, extract business process flows from them, and only then trace the remainder by reading code, because declared sequence is cheap and implicit sequence is expensive.

Hunt specifically for what bypasses the engine. Paths that route around the process engine are invisible to everyone including the audit trail, which makes them the least understood and most dangerous part of the estate.

*Artefact:* entry-point inventory and topology sketch, every element cited to a location.
*Checkpoint:* an application-team reviewer confirms nothing major is missing.
*Characteristic failure:* treating the inventory as complete because the reading is finished. Completeness is confirmed by a person, not by exhaustion.

### Pass 2 — Reconcile against existing models

Compare the derived topology against whatever architecture material exists — C4, DSL, CMDB. A list of discrete claims is far easier for an application team to review than a diagram: confirm or reject, item by item, rather than eyeballing a picture. Where no architecture material exists, this pass produces the map instead of correcting one.

The technique has a name: this is a **software reflexion model** (Murphy, Notkin & Sullivan, 1995). You state the high-level model you believe is true, map its entities to source, and compute the difference. It returns three results, not two:

- **Convergence** — the model and the code agree.
- **Divergence** — the code does something the model does not show.
- **Absence** — the model claims something the code does not do.

Classifying each discrepancy beats a flat list, because the three have different causes and different remedies — divergences usually mean the code moved, absences often mean the model described an intent never built. **Report convergence explicitly.** Without it there is no answer to "how wrong was our architecture," and the pass reads as an indictment of the architects rather than a measurement.

The technique is iterative and built to be stopped early: its stated aim is a model good enough to reason about the task at hand, not a correct one. That is the same bar this method sets, arrived at independently.

The wider discipline is **Software Architecture Reconstruction** — an established field since the SEI's work in the late nineties. **Architecture erosion and drift** (Perry & Wolf, 1992) is the name for why the gap exists at all: erosion from violating architectural principles, drift from insensitivity to them. Adopting this vocabulary connects the work to its literature, and gives the finding a name that is not anyone's fault.

*Artefact:* the reflexion model — convergences, divergences, absences — plus a corrected model at the accuracy bar, in whatever DSL the architects already use, so it renders through their existing tooling.
*Checkpoint:* application teams have confirmed or rejected each discrepancy. Confirmation is on the discrepancies, not on the corrections.
*Characteristic failure:* polishing the model to architectural standards. The bar is fitness for signal placement.

### Pass 3 — Draft the business layer

The business process view does not have to be excavated from code, and mostly cannot be. It can be drafted — from industry reference models — published, competitor-maintained catalogues of a sector's own capabilities and business processes, such as BIAN in banking or MISMO in mortgage, from the declared sequences found in pass 1, and from world knowledge of how the domain works — then corrected by a business reviewer.

The expected failure profile of a drafted layer is *structurally right and locally wrong*, and that is the ideal one: local divergences are what a reviewer spots fastest and cares most about. The review question is not "is this accurate" — which no one can answer wholesale — but "would you name it this way," which a business person can answer authoritatively about their own domain.

*Artefact:* the draft business process, every step tagged proposed until reviewed.
*Checkpoint:* a business owner has walked it and corrected the names, order, and omissions.
*Characteristic failure:* skipping the review because the draft looks convincing. A convincing unreviewed draft is exactly the artefact the derived/proposed rule exists to catch.

### Pass 4 — Derive business process flows and build the realisation mapping

Connect the layers: which traced paths realise which stages. This mapping — the realisation links — is the deliverable the whole method exists to produce.

**This pass is an instance of traceability link recovery**, not a construction of this method. That field studies exactly this problem: establishing candidate links between a coarse-grained, independently-authored natural-language artefact and fine-grained code units, handling the vocabulary gap and the granularity gap between them, and emitting ranked candidates anchored to code locations for human confirmation. Adjacent named practices are feature location and business rule mining. Use the vocabulary — it is the access key to thirty years of work on the failure modes of this pass.

**What is genuinely harder here than in the literature:** that work assumes the coarse artefact is the system's *own specification*, written with the intent of being implemented. A business process authored by people who were not describing software, and never meant it to be implementable, is a harder and less-studied case, and the many-to-many mismatch between one stage and several application steps across several systems is not the canonical setup. Expect the published techniques to degrade here rather than fail — and expect to need more human confirmation than the papers report.

A CMDB typically collapses capability and service into one name; this pass is where they come apart.

Candidate business process flows come bottom-up from entry points and declared sequence; the business layer from pass 3 gives them names and altitude.

*Artefact:* business process flows with stages, each stage mapped to the application steps that realise it, all links cited.
*Checkpoint:* both a technical and a business reviewer accept the mapping — the claim spans code and business meaning, and no single reviewer can check both.
*Characteristic failure:* forcing every traced path into a stage. Paths that serve no stage are findings too.

### Pass 5 — Prune

Filter the business process flows to the ones whose failure the business would notice and act on. This is judgement, informed by the business owner, incident history, and frontline support channels — the last being unmediated business vocabulary: actor, step in the business's own words, and proof it mattered, with frequency as a free priority ranking. (Caveat: support channels are biased toward the visible and human-facing; batch failures nobody sees never appear there.)

What survives is a **critical user journey** in Google SRE's sense — a business process flow through the product that carries the business value, ordered by impact. Use the term. It arrives already wired to the next pass: the CUJ selects the journey, the SLI measures it, the SLO sets the threshold. Naming it anything else means building that bridge by hand.

Work business-first and thin, then go application-deep only on the survivors. And because everything *upstream* of pruning is expensive per business process flow too, run this pass earlier wherever the business can answer without seeing candidates first — see "The order of the passes" above.

*Artefact:* the pruned business process flow list, each survivor with the reason it survived, each cut with the reason it was cut.
*Checkpoint:* the business owner has accepted the list — including the cuts.
*Characteristic failure:* under-pruning. It is not the conservative choice; it is a cost multiplied through every remaining pass.

### Pass 6 — Place signals, define healthy, assign ownership

For each surviving business process flow: signals at the boundaries, where a step crosses to another system or into durable state — the points where independent failure occurs and where ownership changes hands. That reasoning is what to check against, not the boundary rule itself: anywhere else failure is independent or ownership changes is equally a candidate, and a stage with no boundary in it can still be worth measuring on its own. Instrument an internal step only if it has caused an incident before; history beats theory. Instrumenting everything produces five red lights that all mean the same thing — perfectly correlated signals carry the information of one, with five times the noise.

Monitoring at the level of the whole business process flow is a named market category, not a novel construction — **business activity monitoring** and **business transaction management**, where a transaction is defined by an entry point plus its processing path across systems. Worth knowing before building, because some of this can be bought.

Alert routing follows the layer split. The signal lives at the application step and rolls up: the business process view shows consequence, the application process view shows location. Page on the business stage — that is the symptom someone cares about; the application process view is what the responder opens next, not what wakes them. Otherwise you page twice for one problem. This is Ewaschuk's "page on symptoms, not causes," and its honest limit is stated in the next paragraph.

Leading and lagging indicators get different treatment because they warrant different responses. Lagging — the step failed, the transaction did not complete — means act now, and pages. Leading — queue depth climbing, retry rate rising, latency creeping toward timeout, error budget burning faster than the month can absorb — means investigate before it becomes lagging, and routes at lower urgency: a ticket or a nudge, not a phone call at three in the morning. This is the trend concern earning its keep — the marching-towards-a-cliff case, where real impact exists but has not yet been realised, is precisely what pure symptom-based paging cannot catch.

Classify every wanted signal into three dispositions: it exists and is watched; it exists and nothing watches it (a coverage gap); nothing could produce it (an instrumentation gap — a build ask, not a failure). This converts an unbounded question into schedulable work.

Ownership means: who gets paged, and who can decide — not who built it. Expect the circularity: the people who know what the signals should be have dispersed; the people on the hook can act but cannot define. The exit is the code as a third source — it does not know what *should* be signalled, but it knows what *can* be. Where a boundary has no owner, record it as unowned. Do not attach a plausible name.

*Artefact:* an observability specification per business process flow — boundaries, signals, dispositions, thresholds, owner, response — with an ownership map alongside it, unowned boundaries named as such.
*Checkpoint:* every named owner has accepted the assignment, and every unowned boundary has been escalated rather than absorbed.
*Characteristic failure:* false assignment, and quiet omission of gaps. Both make the artefact look better by making it lie.

Ownership is the part of this pass that most often stalls it, and the reason is that it is not a field to fill in. A business process flow crossing boundaries no single team owns end to end is a Conway's Law observation — the gap in the business process flow mirrors a gap in the organisation, and no amount of instrumentation closes it. The escalation is the fix, and it exits the technical domain. Budget for that rather than treating it as an obstacle to the real work.

### Pass 7 — Feed back

Incidents and near-misses are evidence about the earlier passes. A missed detection indicts a signal or threshold; a failure nobody anticipated indicts the trace or the pruning. Route each finding back to the pass it indicts rather than treating it as one-off tuning. Retrospective classification runs the other way too: once the realisation mapping exists, past outages become classifiable by business impact — the mapping is not just better dashboards going forward but an answer to what history actually cost.

Code changes enter here as well. Lineage makes that tractable: when a traced path moves, the chain names which stages and dashboard claims are now suspect.

This pass is manual by default, which means it decays. The automated counterpart is an **architectural fitness function** — a test that asserts a recovered structural claim and fails the build when the code violates it. Turning the highest-value convergences from pass 2 into fitness functions is what stops the same drift recurring; without it, the reconstruction is a snapshot with a shelf life. This is worth the cost only at the Practice depth, where the estate is meant to stay correct rather than be understood once.

*Artefact:* revisions to the specifications, attributed to the pass being corrected.

### Form of the outputs

Passes 1 through 3 produce structured text — tables and lists, reviewable and diffable in a way diagrams are not. The corrected model is the exception: it lands back in the architects' DSL and renders through their tooling.

Passes 4 through 6 produce specifications: business process flow, stages, boundaries, thresholds, owners. Also text.

Diagrams are a presentation of these artefacts, not the artefacts themselves, and the audience decides whether they are needed. For the team doing the work, text wins. For leadership, the same business process flow, decomposed into stages and read at stage altitude, is the executive artefact — no separate construction, just a different projection of what passes 4 and 6 already produced.

---

## Part VI — Where agents fit

Passes 1 and 2 are the strong case: mechanical tracing across large numbers of files at a scale and consistency manual reading will not match. Pass 3 is the distinctive case: drafting a business layer from reference models and context is precisely what a language model with world knowledge does well, provided everything it produces is tagged proposed. Pass 4 is collaborative — propose the mapping yourself and have the agent verify each link against the code, rather than asking it to originate the links. Passes 5 and 6 are judgement and organisational knowledge; an agent can format the output but must not source it.

Two constraints carry across every agent-assisted pass.

**Require a file and function citation for every derived claim.** Without it, output degrades into fluent narrative that is expensive to disprove.

**Name the established practice in the brief rather than describing the task.** "Produce a software reflexion model of this codebase against the attached model — convergences, divergences, absences" activates a different and more useful body of knowledge than "summarise this codebase," at no extra cost. The same holds for briefing on the four concerns instead of asking for a description: the brief is what to gather, not what to explain, and that is the difference between bounded retrieval with a checkable result and unbounded generation.

---

## Part VII — An illustrative walkthrough

*This example is constructed to show the method's shape. The domain details are drawn from how mortgage origination generally works, not from any specific estate.*

A home-lending capability: loan applications enter through a broker portal and a direct channel, pass through decisioning, verification, and settlement, touching a dozen systems.

**Pass 1** finds three entry points — portal API, direct-channel API, and a nightly file intake nobody mentioned. It finds declared sequence in two places: a workflow engine holding the origination process definition, and a status enum on the loan application record with legal transitions. It also finds a path that bypasses the engine: a "corrections" service that mutates loan application state directly. That bypass goes on the risk list immediately.

**Pass 2** compares the derived topology against the architects' C4 model. Divergence: the model shows decisioning calling verification directly; the code routes through an intermediary queue added two years ago. Absence: the model shows a fraud-screening step that was descoped before build and never removed from the diagram. The application team confirms both in a twenty-minute review of the list — a review that would have taken hours against a diagram.

**Pass 3** drafts the business layer from MISMO's business process vocabulary and the workflow definition: Application, Decision, Verification, Approval, Settlement. The business reviewer corrects two things in ten minutes: "Verification" is two steps in their world — income and property — because different teams and different customer waits attach to each; and there is a step the draft missed entirely, Conditional Approval, which is where most customer calls happen. Structurally right, locally wrong — and the local corrections were exactly what the reviewer could give authoritatively.

**Pass 4** maps stages to steps. Settlement, one business stage, turns out to be realised by eleven application steps across four systems — and one boundary in the middle, between the lender and the title-services integration, belongs to no team. It is recorded as unowned.

**Pass 5** prunes fourteen candidate business process flows to five. The close call: bulk broker re-pricing, technically heavy, but the business owner confirms failures there surface as complaints within an hour through the broker desk — the support channel already covers it, so it is cut, with the reason recorded.

**Pass 6** places signals at stage boundaries. The stalled-work case drives the leading indicators: loan applications entering Conditional Approval and not leaving within the business's stated expectation — an expected-volume fact no code contains, supplied by the business owner during the same review. Three wanted signals land in disposition three: nothing emits them today. They become build asks with named owners. The business process view goes up with the impact concern stated in its title. The unowned settlement boundary stays visibly unowned on it; four weeks later, that visibility — not the method — is what gets it assigned.

**Pass 7** is waiting for its first incident.

---

## Part VIII — Prior art

What each is borrowed for, and where it stops applying.

- **Google SRE — golden signals, and service level indicators and objectives (SLI/SLO)** — the default measurement set, and the separation of what is measured from the threshold defining acceptable. Stops at the business layer: golden signals are service-shaped, and composing them upward into business meaning is exactly what they do not do.
- **Critical user journey (Google SRE)** — the business process flow carrying business value, ordered by impact, as the selection unit that feeds the indicator and the objective. Borrowed as the output of pruning, because it connects that pass to the measurement vocabulary without a hand-built bridge.
- **C4 model** — the static/dynamic distinction; operations lives on the dynamic view. Container as the unit of independent deployment and failure. Stops at intent: C4 describes design, and this method exists because design drifts.
- **Viewpoints and perspectives (Rozanski & Woods)** — the *operational viewpoint* as the named architectural view for running, administering and supporting a live system. Stops at construction time: it assumes someone builds the viewpoint up front, which is the case this method does not have.
- **Software reflexion models (Murphy, Notkin & Sullivan, 1995; IEEE TSE 2001)** — stated model versus source, computing convergence, divergence and absence; explicitly a good-enough technique, iterative and stoppable. The direct mechanism of pass 2.
- **Traceability link recovery (Antoniol, Canfora, Casazza, De Lucia & Merlo, 2002; Hayes, Dekhtyar & Sundaram, 2006)** — establishing candidate links between a coarse, independently-authored natural-language artefact and fine-grained code, handling the vocabulary and granularity gaps, emitting ranked candidates anchored to code locations for human confirmation. **The direct mechanism of pass 4**, with a fine-grained variant and a business process model variant. Stops where the coarse artefact was not written to describe software — see the standing section.
- **Feature location / concept location (Rajlich & Wilde, 2002; survey: Dit, Revelle, Gethers & Poshyvanyk, 2013)** — locating the code implementing a unit of functionality described in domain terms. Stops at persistence: it is normally change-request-driven and its output is consumed and discarded, not maintained as a record.
- **Business rule mining (OMG Architecture-Driven Modernization; Knowledge Discovery Metamodel)** — recovering business-meaningful behaviour from source and configuration, each rule retaining a pointer to its originating code location. Stops at direction: it is bottom-up, code producing the rule, where pass 4 matches against a rule statement authored elsewhere.
- **Business process recovery from source code** — the named research line for deriving a process model from an implementation. Carries two findings this method also holds: manual activities and process participants are not derivable from source, and the remedy is hybrid — recovered models repaired against event logs.
- **Competency questions (Grüninger & Fox, 1995; carried into METHONTOLOGY, NeOn)** — fixing in advance the questions an artefact must answer, using them to bound scope, and judging completeness by whether they can be answered rather than by coverage. **The four concerns in Part III are an instance.** Stops at object: competency questions govern building a representation, not investigating an existing estate. The same device appears as priority intelligence requirements in intelligence production and as audit objectives-as-questions in performance auditing.
- **Software Architecture Reconstruction (SEI)** — the wider field for recovering architecture from implementation. Stops at meaning: SAR recovers structure, not business significance.
- **Architecture erosion and drift (Perry & Wolf, 1992)** — erosion from violating architectural principles, drift from insensitivity to them. Borrowed as the name for why the gap exists, which is what makes it a finding rather than an accusation.
- **Architectural drift analysis** — the ongoing-detection counterpart to one-time reconstruction.
- **Architectural fitness functions (Ford, Parsons & Kua, *Building Evolutionary Architectures*)** — automated tests that hold a structural claim; ArchUnit and equivalents as the implementation. The mechanism that stops pass 7 decaying. Stops at what can be asserted mechanically: most business-layer claims cannot.
- **Process mining (van der Aalst)** — discovery, conformance checking and enhancement from event logs; the runtime counterpart to static reconstruction. Stops where the logs stop: it sees only what executed and was recorded.
- **Distributed tracing and service maps** — topology recovered from live traffic rather than from code. Same limit, and the same value as a disagreeing second source.
- **Business activity monitoring / business transaction management** — the named market category for monitoring at the level of a whole business process flow; a transaction as entry point plus processing path across systems. Worth knowing because parts of this can be bought.
- **ArchiMate layering** — business, application, technology as distinct layers with realisation links between them. The realisation link is the load-bearing borrow.
- **BIAN / MISMO** — industry reference models that make the business layer draftable rather than discoverable. Stop at the local: every real business process deviates, and the deviations are the review.
- **Event Storming** — facilitated derivation of business process flows from business outcomes; the workshop-shaped alternative for the pruning conversation. Stops at provenance: it produces claims, not citations.
- **New Relic Pathpoint** — business process flow, stage, step and signal with health composing upward; the structural premise adopted here. Its documented method is top-down; this method is the inverse, built for the reconstruction case.
- **Conway's Law** — why the important business process flows cross unowned boundaries, and why ownership is a checkpoint with an escalation behind it rather than a column to fill in.
- **ITIL (service design → service operation)** — the established enterprise framing for the same transition; useful as a vocabulary bridge to governance functions.
- **Data lineage** — premise borrowed, mechanics not: bidirectional provenance from a dashboard claim back to code.
- **Requirements traceability matrix** — the established form for maintaining that bidirectional chain, and the closest analogue to what lineage is doing here.

---

## Part IX — Working from this document with a team

The document transfers the structure; the judgement transfers by working the passes together. The arrangement that fits: demonstrate the reconstruction passes while narrating the reasoning — including the dismissals and the wrong turns, which are where the judgement is visible; share the pruning and stage-naming passes, where they propose and you challenge with the stage test in hand; hand over signals and ownership, which are bounded by the artefacts already produced, and keep the ownership escalations, which exit the technical domain.

The four concerns are the part to put on the wall. Everything else is here when the pass needs it.
