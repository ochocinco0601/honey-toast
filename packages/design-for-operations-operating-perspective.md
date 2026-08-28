# Design for Operations

Deriving business-grounded observability for a business capability, in an estate whose architecture
documentation cannot be trusted and whose original engineers have dispersed.

**This names practices rather than explaining them.** Every named practice is an access key: load it
and its literature comes with it. What is stated at length is only what a name does not supply —
the boundaries, the done-conditions, and the places the world's shelf is empty.

**It is a draft-generation method with review gates, not a discovery method.** Nothing produced is
authoritative until a named person accepts it. The gates are not ceremony; they are what separates
this from a fluent, cited, expensive-to-disprove narrative.

**Three constraints hold across every pass.**

- **Cite every derived claim to a file and function**, and verify the citations mechanically rather
  than trusting them.
- **Keep derived and proposed apart.** Anything inferred is tagged proposed until a human accepts
  it. Inference and evidence never share a voice.
- **Record every acceptance as a dated name against the element it covers.** A gate nobody can
  point at afterwards did not happen, and the next pass cannot check whether the one before it
  finished.

---

## The problem, as a discrimination

Instrumentation coverage is a precondition mistaken for an outcome. Per-component mandates cannot
answer *where in the business process did this break, and who is affected*, because no component
knows what stage it serves. Traces are paths, but unnamed ones.

**The unit of work is the business process flow, not the system.** Systems are what teams own;
business process flows are what break. Conway's Law surfaces here — the flows that matter cross
boundaries nobody owns end to end, and the monitoring inherits the org chart.

Architecture models describe intent at the moment someone wrote them. Treat the gap as material:
code is source, everything else is corroboration, and a contradiction between them is a finding.

---

## Three views, and what each may not claim

The carving is ArchiMate's — business, application, technology. **The second column is the part that
is not obvious and the part that gets violated.**

| View | Answers | May **not** claim |
|---|---|---|
| **Business process** | Impact and scope: where the break is in business terms, what is cut off, what still flows | **Cause** — its arrows are sequence, not dependency, so there is nothing on it to follow toward a reason. **Severity** — a red stage does not say whether that is ten transactions or ten thousand |
| **Application process** | Where: which application step failed, including retry and failure branches the stage knows nothing about | **Cause.** It localises the failure; it cannot terminate in one. Cause runs along dependency edges, which live on the technology view |
| **Technology** | Why: hosts, databases, network, message infrastructure, certificates, external endpoints | **Who is affected** |

**Severity has one home and it is not a view.** A red stage carries no magnitude; magnitude comes
from the throughput concern, which needs expected volume as a business fact. If that fact is never
supplied, impact is answerable as *where* and never as *how much* — say so rather than inferring
magnitude from a stage colour.

**Process, dependency and data movement are different relations, not different drawings of one
thing.** They share nodes and not edges. Merging them yields something that looks complete and
misleads under pressure — a diagram drawn in process shape whose arrows are then read as dependency
claims. Put the question on the view, in its title.

---

## Four concerns, used as a stopping condition

**Impact · Cause · Throughput · Trend.** Settled before discovery starts.

They **bound what every pass gathers**: a pass gathers what these require, not what would describe
the system. That is also the stopping condition for the method as a whole.

**They do not say when a pass is finished.** Each pass carries its own *Done when* line, and that is
an acceptance by a named person. Scope and authority are separate tests and both must hold — the
concerns can be satisfied by a draft nobody has accepted.

The device is **competency questions** (Grüninger & Fox, 1995, ontology engineering): fix in advance
the questions the artifact must answer, bound scope by them, judge completeness by answerability
rather than by coverage of the domain. The same move appears independently as priority intelligence
requirements, and as audit objectives stated as questions.

---

## Vocabulary that must not collapse

| Split | What it prevents |
|---|---|
| **Intended flow** / **observed flow** | Design-time authored versus runtime measured. van der Aalst's *de jure* / *de facto* |
| **Sequence flow** (BPMN) / **dependency relationship** | Nothing traverses a dependency edge. "Dependency flow" is not a thing |
| **Observed volume** / **expected volume** | Telemetry versus business fact. Conflating them is how throughput gets claimed from code |
| **Stage** (business) / **step** (application) | Health composes upward: signal → stage → business process flow |
| **Derived** / **proposed** / **could not determine** | The third is not the second. An operator most needs to see what you could not establish |

---

## What code cannot yield

Static reading shows what the code *can* do; runtime evidence shows what it *does* and misses paths
that did not execute. **They disagree, and the disagreement is a finding, not an error to resolve.**

**Expected volume is a business fact supplied by a person.** A method claiming to derive throughput
from code is lying about one of the two. Name the role that owes it and record the answer; where
nobody can supply it, record *could not determine* rather than leaving throughput silently open —
otherwise the stopping condition never fires and the work stalls instead of terminating.

**Where source is unreadable** — a vendor black box, a runtime with nothing in version control —
the static route is unavailable, not the method. Route that component through runtime evidence, and
mark its stages as evidenced differently from the rest.

---

## The passes

Order constraints are narrow: **2 needs 1 · 4 needs 1 and 3 · 6 needs 4 and 5 · 7 needs 2.** Everything else
moves. **Pruning can run before tracing** if the business can name the flows that matter up front —
usually cheaper, and the default order only assumes it cannot.

**1 · Discover the surface**
*Activates:* static analysis tooling — CodeQL, Semgrep, tree-sitter, SCIP/LSIF. The question is *what declares sequence?* — process definitions, job graphs, status enums with transitions. Hunt what bypasses the engine.
*Ships as:* **Tool** for the extractors, **Text** for what they add up to. Architecture reconstruction has no end-to-end product; commercial substrate exists but you build and run the extraction. The practice has no name for this purpose, and the non-HTTP trigger surface is uncovered.
*Produces:* entry-point inventory and topology sketch, every element cited to a location.
*Done when:* an application-team reviewer confirms nothing major is missing. **Completeness is confirmed by a person, never by exhaustion.**

**2 · Reconcile against existing models**
*Activates:* **software reflexion model** (Murphy, Notkin & Sullivan, 1995) — convergence, divergence, absence. Report convergence explicitly, or there is no answer to *how wrong was our architecture*. Wider field: **software architecture reconstruction**; **architecture erosion and drift** (Perry & Wolf, 1992).
*Ships as:* **Text.** Technique published; tool support research-grade. Building it is yours.
*Produces:* the reflexion model, plus a corrected model in whatever DSL the architects already use. **The bar is fitness for signal placement** — right about what exists, what calls what, and where boundaries sit, and not carrying the semantic rigour architects demand of their own artefacts. State that bar to anyone doing correction work, human or agent, or effort drains into naming conventions instead of topology.
*Done when:* application teams have confirmed or rejected each discrepancy — on the discrepancies, not the corrections.

**3 · Draft the business layer**
*Activates:* sector reference models — APQC, BIAN, ACORD, eTOM, MISMO. **Event Storming** where the derivation needs facilitating.
*Ships as:* **Tool** for the models; the tailoring activity has no established name.
*Produces:* the draft business process, every step tagged proposed until reviewed.
*Done when:* a business owner has walked it and corrected the names, the order, and the omissions. **A convincing unreviewed draft is exactly what the derived/proposed rule exists to catch.**

**4 · Derive flows and build the realisation mapping**
*Activates:* **traceability link recovery** (Antoniol et al.); **feature location**; **business rule mining** (OMG ADM/KDM). Recording the link: the **realisation** relationship in ArchiMate. Vocabulary-based recovery assumes shared naming between the coarse artifact and the code — where the estate is old enough that no shared vocabulary exists, the dynamic and execution-trace branches of feature location are the ones that work.
*Ships as:* **Tool** for recording. Establishing the link is studied, though the coarse artifact here is a business procedure never written to be implemented — named in the literature as a harder and less-studied case.
*Produces:* flows with stages, each stage mapped to the application steps that realise it, all links cited. **Plus the correlation identity** — the business key that travels with a work item across services, and where it is lost. Without one, a stage can be shown red and *who is affected* cannot be answered at all; that is a finding to surface, not a step to skip.
*Done when:* **both a technical and a business reviewer accept the mapping.** The claim spans code and business meaning and no single reviewer can check both.

**5 · Prune**
*Activates:* **critical user journeys** (Google SRE) — the term wires straight into the next pass: CUJ selects, SLI measures, SLO thresholds. **Do not derive criticality cold.** In a regulated firm a **business impact analysis** already exists, signed and periodically reviewed, and an operational-resilience regime may already require a register of important business services with impact tolerances set. Start from those and reconcile, rather than producing a rival list nobody signed.
*Ships as:* **Procedure.**
*Produces:* the pruned list, each survivor with its reason and **each cut with its reason.** When this pass runs after pass 4 it prunes derived flows; when it runs first it prunes candidates the business named, and pass 1 then traces only those.
*Done when:* the business owner has accepted the list — **including the cuts.** Under-pruning is not the conservative choice; it is a cost multiplied through every remaining pass.

**6 · Place signals, define healthy, assign ownership**
*Activates:* **golden signals** / **RED**; **SLI/SLO**; **OpenSLO**. Boundaries are the default placement because that is where independent failure occurs and ownership changes hands. Market category: **business activity monitoring**, **business transaction management**.
*Ships as:* **Tool** for signals and thresholds. **Text** for ownership — no method ships, and it needs authority to assign.
*Produces:* an observability specification per flow — boundaries, signals, thresholds, owner, response — plus an ownership map. Classify every wanted signal as *exists and watched* · *exists and unwatched* · *cannot be produced*.
*Done when:* every named owner has accepted, and **every unowned boundary is escalated rather than absorbed.** A falsely assigned boundary is worse than a visibly unowned one — it stops the escalation that would have fixed it. Never attach a plausible name.

**7 · Feed back**
*Activates:* **architectural fitness functions** (Ford, Parsons & Kua) — ArchUnit, NetArchTest, import-linter. Turn pass 2's convergences into assertions that fail the build.
*Ships as:* **Tool**, with a limit: that tooling is single-repository. The cross-boundary claims — the ones this method exists to establish — have no equivalent guard, so they decay unwatched.
*Produces:* revisions attributed to the pass being corrected.
*Done when:* a build fails on a violated structural claim. **Manual by default means it decays.**

---

## Coverage is a grid, not a rigour dial

Two axes: **how many flows** × **how many concerns**. Narrow either and every pass gets cheaper,
because the acceptance criteria shrank. **Proof** 1×1 · **Pilot** 1 × four · **Practice** N × four.
Named points on a continuum, not tiers. State the cell before starting — most of the argument about
whether the method is too heavy dissolves once someone has to say which one they are in.

---

## Where the world's shelf is empty

Three, and they decide build against buy.

- **Cross-repository call paths from static evidence alone, where no contract is declared.** Where
  interfaces are declared — OpenAPI, protobuf, a schema registry, or cross-repo indexes such as
  SCIP/LSIF — the edge resolves and this is not a gap. What stays unsolved is the undeclared call:
  a URL assembled from configuration, a queue name built at runtime. Vendors who sell the general
  case use live traffic instead. Where telemetry exists, route around it.
- **Capability as the unit of analysis.** Every product's unit is a repository, an application, or a
  service. The concept is fully owned; the tooling is not.
- **The non-HTTP trigger surface, as a named practice for this purpose.** Security has enumerated
  it for years — threat modelling and attack-surface analysis both cover schedulers, batch jobs,
  queue consumers and pollers, and that tooling is reusable. What is absent is the same inventory
  performed to find where *work* enters rather than where *attack* enters, which asks different
  questions of the same surface and keeps different fields. Borrow the tooling; expect no method.
  In a legacy estate that surface is where work actually enters.

**Three capabilities in this method ship as text only** — recovering topology, reconciling it, and
attaching accountability. **Text is not a lesser verdict on the knowledge; it is a cost that lands
on you.**

A fourth cost sits outside the method entirely. Making the practice held by a team rather than
performed by one person has no shipped method either, and it is the one most often skipped.

---

## Standing

**Components are borrowed and carry their own empirical record.** The **composition** — this
sequence, the joins between borrowed parts, the four concerns as a stopping condition — is a
**working draft under active development.** Treat it as a prototype: use it, expect it to change,
and expect the claim flagged unreliable below to change first. Composition is where methods fail when
every component is proven, which is this method's own thesis about layers and joins, applied to
itself.

**A prior-art check narrowed two claims to nothing.** Binding stages to code is traceability link
recovery. The four concerns are competency questions. Neither is original here.

**Three narrower claims survived, and one of them is unreliable.**

1. The coarse artifact is a business procedure never intended to be implemented — a hard case inside
   a named practice, not an uncovered one.
2. Per-element inferred-versus-confirmed marking on a process model. Established one discipline away
   — evidence codes in biological ontologies, W3C PROV — but BPMN carries no such attribute.
3. **A trace that terminates in a displayed measurement** and can mark it suspect when the source
   moves. Traceability tooling stops before runtime; measurement tooling carries no lineage back to
   source. **This claim is the least verified of the three. Do not build on it without checking it
   yourself.**

The third depends on treating a displayed measurement as a traceable artifact carrying a suspect
state — lineage in the data-lineage sense, borrowed as a premise rather than as machinery: every
element in a finished view traces back through stage, signal and cited path to a location in the
code, and the chain is walkable both ways. Forward it builds the views; backward it defends a number
under challenge and identifies which views went wrong when code moved.
