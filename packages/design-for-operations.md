# Design for Operations

*A repeatable method for taking a business capability from architecture to observability.*

## What this is

A sequence of passes an operations team runs against a capability to arrive at monitoring that reflects what the systems actually do. Each pass produces an artefact and ends at a human checkpoint, so a team can stop part-way and still hold something useful.

Each pass names the input it needs and who has to supply it. Nothing here assumes a particular team owns the work.

**On everything stated as a rule below.** Each one is a default with its reason attached, and the reason is the part that matters. Where the reason doesn't hold for you, vary the rule deliberately. What this guards against is a team inheriting a constraint nobody chose and paying for it as though it were the cost of the method.

## The spine: four questions

The passes are not open-ended discovery. They gather what a named set of views requires, and those views are defined before any code is read. The four below cover the common case and are a starting set, not a fixed one — add or drop to match what your operation actually has to answer. What carries the weight is that the set is settled before discovery starts, not that there are four of them.

| View | Question it answers | Relation it displays |
|---|---|---|
| Impact | Where in the process did this break, and who is affected? | Sequence over time |
| Cause | What is broken underneath it? | Dependency |
| Throughput | Is work getting through at the expected volume? | Flow of work |
| Trend | Is it getting worse? | Change over time |

Two consequences follow, and both matter more than the table itself.

**The four questions are acceptance criteria for every earlier pass.** A pass is complete when it has gathered what these views need — not when the system has been described. This also supplies a stopping condition: the method is done when each view can be populated.

**No view may imply it answers another.** The characteristic failure is a diagram drawn in process shape whose arrows are then read as dependency claims — so when a stage goes red, people trace along process arrows looking for a cause that was never on those edges. Put the question on the view itself, in the title, so the scope is legible without anyone reading a definition.

## How far to take it

Depth is not a rigour dial. It is a coverage choice on two axes the spine already defines — **how many flows**, and **how many views**. Narrow either one and every pass gets cheaper automatically, because the acceptance criteria shrank. Nothing else has to change.

| Run | Coverage | What you hold | What you cannot claim |
|---|---|---|---|
| Proof | 1 flow × 1 view | A worked example, and evidence the approach survives contact with the code | Anything about the other flows |
| Pilot | 1 flow × all 4 views | A monitored flow, plus a template the next flow inherits | Coverage |
| Practice | N flows × 4 views | The capability — lineage maintained, drift caught when code moves | — |

These are named points on a continuous grid, not tiers with entry requirements — two flows and two views is a perfectly legitimate cell, it just doesn't have a name. State the cell before starting. Most of the argument about whether the method is too heavy dissolves once someone has to say which one they are in. The per-pass checkpoints are the other stopping points: each is a place to hold what exists and go no further.

## Framing commitments

These shape every pass. They are the part worth arguing about before starting.

**The unit of work is the flow, not the system.** Systems are what you own; flows are what break. C4 names this distinction directly: the static views describe structure, the dynamic view describes a path across it. Operations lives on the dynamic view.

**Operations is a viewpoint, not an afterthought.** Rozanski and Woods name the *operational viewpoint* alongside functional, information, concurrency, development and deployment — the architectural view concerned with how a system is run, administered and supported once live. This method is a way of constructing that viewpoint when nobody constructed it up front.

**Process, dependency, and data movement are different relations, not different drawings of one thing.** They share nodes but not edges. A dependency can sit entirely outside the process sequence; state can move between stages with no process relationship. Merging them into a single picture produces something that looks complete and misleads under pressure. This is the source of most dashboard disagreements, and it is a design fault rather than a communication failure.

**Every claim carries lineage.** Borrowing the premise of data lineage rather than its machinery: each element in a finished view traces back through stage, signal, traced path, to a location in the code — and the chain is walkable in both directions. Forward, it is how views get built. Backward, it is how a number gets defended when challenged, and how you detect which views became wrong when code moved. Requirements traceability matrices are the closest established analogue.

**Architecture material is an input, not a prerequisite.** Where models exist they save time and give you something to reconcile against. Where they don't, the passes still run against the code and the runtime. The method must not be hostage to the presence or quality of an architecture practice.

**The evidence is static, by choice.** These passes read code. Two other established routes recover the same picture from runtime instead — distributed tracing, where the service map draws itself from live traffic, and process mining, which derives the actual process from event logs the systems already emit. Static reading shows what the code *can* do; runtime evidence shows what it *does* do, and misses paths that did not execute. They disagree, and the disagreement is a finding. Choose deliberately rather than by default; where tracing already exists, it is usually the cheaper first look.

**The accuracy bar is fitness for signal placement.** A corrected model needs to be right about what components exist, what calls what, and where boundaries sit — not carry the semantic rigour an architecture practice demands of its own artefacts. State this bar explicitly to anyone doing correction work, or effort drains into naming conventions instead of topology.

**Discovery is mechanical; selection is judgement.** Different activities, run separately. Conflating them is how you get a plausible narrative that nothing in the code supports.

## The passes

The numbering is a default order, not a dependency graph. What genuinely constrains sequence is narrow: 2 needs 1, 3 needs 2, 4 needs 2, 6 needs 4. Everything else can move.

The move worth considering first: **pruning can run before tracing.** If the business can name the flows that matter up front, trace only those and never discover the surface you would have thrown away. That is usually the cheaper path. The order below assumes you cannot get that input early — which is common, because "which flows matter" is often a question people can only answer once they see candidates. Judge which situation you are in rather than inheriting the answer.

### 1. Surface discovery

Enumerate everything that initiates work from outside the capability: synchronous entry points, message consumers, scheduled and batch triggers, any other externally-originated invocation. No interpretation, no clustering, no significance judgements.

Capture expected volume per entry point while here. It is cheap now and it is the throughput view's entire basis — without it, "is work getting through" has no referent.

*Serves:* throughput, and the root of every lineage chain.
*Artefact:* inventory table — entry point, trigger mechanism, expected volume, code location.
*Checkpoint:* completeness. The characteristic failure is a whole class of trigger being invisible to whatever discovery technique was used.

### 2. Forward trace

For each entry point, trace to durable state changes and outbound calls. This converts an inventory into a topology: what an entry point touches is the shape of its dependency footprint.

*Serves:* cause, directly. This pass is the dependency view.
*Artefact:* per-entry-point dependency map, every claim carrying a code citation.
*Checkpoint:* traceability. A claim that can't be traced to a specific location is a claim to discard, not to investigate later — at Pilot depth and above, where the output has to survive being challenged months later. At Proof depth, an untraced claim the team recognises is worth keeping and marking as such; citation discipline is what makes a result defensible, not what makes it true.

### 3. Reconcile

Where architecture material exists, compare it against the traced topology and produce a discrepancy list: what the model asserts, what the code does, where the evidence sits. Where none exists, this pass produces the map instead of correcting one.

Drift is the finding, not an obstacle to it. A discrepancy list is also far easier for application teams to review than a diagram — discrete claims to confirm or reject rather than a picture to eyeball.

The technique has a name: this is a **software reflexion model** (Murphy, Notkin & Sullivan, 1995). You state the high-level model you believe is true, map its entities to source, and compute the difference. It returns three results, not two:

- **Convergence** — the model and the code agree. This is the part you stop checking, and the number that says how much of the existing model survived.
- **Divergence** — the code does something the model does not show.
- **Absence** — the model claims something the code does not do.

Classifying each discrepancy is more useful than a flat list, because the three have different causes and different remedies — divergences usually mean the code moved, absences often mean the model described an intent that was never built. Report convergence explicitly; without it there is no answer to "how wrong was our architecture."

The technique is iterative and built to be stopped early — its stated aim is a model good enough to reason about the task at hand, not a correct one. The wider discipline is **Software Architecture Reconstruction (SAR)**, an established field dating to the SEI's work in the late nineties; **architecture erosion and drift** (Perry & Wolf, 1992) is the name for why the gap exists at all. Recent work applies language models to the recovery step specifically, recovering both static and behavioural views.

*Serves:* the credibility of everything downstream.
*Artefact:* reflexion model — convergences, divergences, absences — plus a corrected model at the accuracy bar above, in whatever DSL the architects already use, so it renders through their existing tooling.
*Checkpoint:* application-team confirmation on the discrepancies, not on the corrections.

### 4. Derive candidate flows and their stages

Cluster entry points into flows, then decompose each flow into stages. The stage is the load-bearing unit: it is what the impact view displays, and health composes upward from signals to stage to flow.

This pass reaches outside the code for its organising principle even though the evidence for each flow stays inside it. Two directions converge, and running both is a useful cross-check: bottom-up, entry points sharing downstream state are probably serving the same flow; top-down, the outcomes the capability owes its consumers each imply a flow that must exist. Event Storming is the established practice for the top-down direction when it needs facilitating.

*Serves:* impact.
*Artefact:* candidate flows, each expressed as stages, with entry points and traced paths attached to each stage.
*Checkpoint:* every candidate verified against the code. The failure mode is a flow that reads well and isn't there.

### 5. Prune

Reduce candidates to the flows whose failure someone would notice and care about. This pass requires business input rather than technical input, and normally yields a shorter list than anyone expects.

What survives is a **critical user journey** in Google SRE's sense — a flow through the product that carries the business value, ordered by impact. Use the term, because it arrives already wired to the next pass: CUJ selects the journey, the SLI measures it, the SLO sets the threshold. Naming it anything else means building that bridge by hand.

Everything downstream is expensive per flow, so under-pruning is not the conservative choice. And because everything *upstream* is expensive per flow too, run this pass earlier wherever the business can answer without seeing candidates first — see the note above the passes.

*Artefact:* the critical flow set, with rationale for inclusion recorded.
*Checkpoint:* business owner agreement on what made the cut and what didn't.

### 6. Place signals

For each surviving flow: identify the boundaries it crosses, place instrumentation there, define what healthy means, and name the owner of the response.

Boundaries are the default place for signals because they are where independent failure occurs and where ownership changes hands. That reasoning is what to check against: anywhere else failure is independent or ownership changes is equally a candidate, and a stage with no boundary in it can still be worth measuring on its own. Independently deployable units are the usual granularity — the container level, in C4 terms. The Google SRE golden signals (latency, traffic, errors, saturation) are the standard starting vocabulary for what to measure at each. Health definition is SLI/SLO work: the indicator is what you measure, the objective is the threshold separating acceptable from not.

Flow-level monitoring of this kind is a named market category, not a novel construction — **business activity monitoring** and **business transaction management**, where a transaction is defined by an entry point plus its processing path across systems. Worth knowing if the capability is being bought rather than built.

*Serves:* all four views, each drawing a different projection of the same signal set.
*Artefact:* per-flow observability specification — stages, boundaries, signals, thresholds, owner, response — with lineage intact to pass 2 citations.
*Checkpoint:* every named owner has accepted the assignment.

### 7. Assign ownership across boundaries

Separated from pass 6 deliberately, because it is where the method most often stalls and it is not a field to fill in.

Flows crossing boundaries that no single team owns end-to-end is the common finding. It is a Conway's Law observation — the gap in the flow mirrors a gap in the organisation, and no amount of instrumentation closes it. Surface these explicitly as unowned rather than assigning them to whoever is nearest; a falsely-assigned boundary is worse than a visibly unowned one, because it stops the escalation that would have fixed it.

*Artefact:* ownership map, with unowned boundaries named as such.
*Checkpoint:* unowned boundaries escalated, not absorbed.

### 8. Feed back

Incidents and near-misses are evidence about the previous passes. A missed detection means a signal gap or a threshold set wrong; a failure nobody anticipated means the trace or the pruning was incomplete. Route these back to the pass they indict rather than treating them as one-off tuning.

Code changes enter here too. Lineage makes this tractable: when a traced path moves, the chain identifies which stages and views are now suspect.

This pass is manual by default, which means it decays. The automated counterpart is an **architectural fitness function** — a test that asserts a recovered structural claim and fails the build when the code violates it. Turning the highest-value convergences from pass 3 into fitness functions is what stops the same drift recurring; without it, the reconstruction is a snapshot with a shelf life. Worth doing only at the Practice rung.

*Artefact:* revisions attributed to the pass being corrected.

## Form of the outputs

Passes 1 through 3 produce structured text — tables and lists, reviewable and diffable in a way diagrams are not. The corrected model is the exception, landing back in the architects' DSL and rendering through their tooling.

Passes 4 through 7 produce specifications: flow, stages, boundaries, thresholds, owners. Also text.

Diagrams are a presentation of these artefacts, not the artefacts themselves, and the audience decides whether they are needed. For the team doing the work, text wins. For leadership, the same stage-decomposed flow viewed at stage altitude is the executive artefact — no separate construction, just a different projection of what pass 4 and 6 already produced.

## Where automated agents fit

Passes 1 and 2 are the strong case: mechanical tracing at a scale and consistency manual reading won't match. Pass 3 is a good case with supervision, particularly for generating the discrepancy list.

Pass 4 is collaborative — propose the clusters yourself and have the agent verify each against the code, rather than asking it to produce them. Passes 5 through 7 are judgement and organisational knowledge; an agent can format the output but shouldn't source it.

Two constraints carry across all agent-assisted passes. Require a file and function citation for every claim, or output degrades into fluent narrative that is expensive to disprove. And brief the agent on the four questions rather than asking it to describe the system — the brief is what to gather, not what to explain.

Naming the practice in the brief does most of the work. "Produce a software reflexion model of this codebase against the attached model — convergences, divergences, absences" activates a different and more useful body of knowledge than "summarise this codebase," at no extra cost.

## Prior art referenced

- **Software reflexion models** — Murphy, Notkin & Sullivan (1995; IEEE TSE 2001): stated model versus source, computing convergence, divergence and absence; explicitly a good-enough technique, iterative and stoppable
- **Architecture erosion and drift** — Perry & Wolf (1992): erosion from violating architectural principles, drift from insensitivity to them
- **Software Architecture Reconstruction (SAR)** — the named field for recovering architecture from implementation
- **Architectural drift analysis** — the ongoing-detection counterpart to one-time reconstruction
- **Architectural fitness functions** — Ford, Parsons & Kua, *Building Evolutionary Architectures*: automated tests that hold a structural claim; ArchUnit and equivalents as the implementation
- **C4 model** — static views versus the dynamic view; container as the unit of independent deployment and failure
- **Viewpoints and perspectives** — Rozanski & Woods: the *operational viewpoint* as the named architectural view for running, administering and supporting a live system
- **Critical user journey** — Google SRE: the flow carrying business value, ordered by impact, as the selection unit feeding SLI/SLO
- **Google SRE golden signals** — latency, traffic, errors, saturation as the default measurement set
- **SLI/SLO** — separating what is measured from the threshold defining acceptable
- **Business activity monitoring / business transaction management** — the named market category for flow-level monitoring; a transaction as entry point plus processing path across systems
- **Process mining** — van der Aalst: discovery, conformance checking and enhancement from event logs; the runtime counterpart to static reconstruction
- **Distributed tracing and service maps** — topology recovered from live traffic rather than from code
- **Event Storming** — facilitated derivation of flows from business outcomes
- **Conway's Law** — flows crossing unowned boundaries as an organisational finding, not a technical one
- **New Relic Pathpoint** — flow / stage / step / signal as a modelling structure with health composing upward; its documented method is top-down, which is the inverse of the reconstruction case
- **Data lineage** — premise borrowed, not mechanics: bidirectional provenance from view back to code
- **Requirements traceability matrix** — the established form for maintaining that bidirectional chain
- **ITIL service design to service operation** — the established enterprise framing for the same transition
