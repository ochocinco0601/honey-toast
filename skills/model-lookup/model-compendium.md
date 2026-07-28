# Originated Models — Compendium

**What this is.** A self-contained catalogue of the conceptual models a practice has
built — the typed-slot structures that give messy reality a place to go. Each model's actual
slots and relation are inlined, so this file is useful on its own, with no other documents.

**How to use it.** When you're working something and reaching for structure, scan this for a
model that already fits — by **subject** (a domain a model covers), by **shape** (the
arrangement you're reaching for — the shape transfers across domains), or by **the seam** (work
that has both structure and behavior-over-time). Name the fit — one model, a composition, or
none — and use the inlined detail.

**One entry is held.** The business semantic chain is **under review** and marked so — its
shape is settled; its exact slot list is provisional.

---

## The shapes — the arranging vocabulary

Every model below is a small fixed set of **typed slots + a relation**. The *shape* is how the
slots are arranged. Sequence, Stack, Set, and Web/graph recur; the behavioral (Trajectory) shape is the growth edge, rarely built.

1. **Sequence (chain)** — ordered stages; each produces/enables the next. *Test:* reordering breaks it.
2. **Stack (layers)** — levels ordered by altitude or bindingness; each layer has its own consumer. *Test:* you can say **why** layer N sits above N−1.
3. **Set (typed roles / facets)** — a fixed vocabulary of named roles every instance fills; order doesn't matter, **completeness** does. *Grid sub-form:* two crossed facet-axes generate cells.
4. **Trajectory (behavioral)** — states + events + transitions over time. **Rarely represented in this catalogue — that thinness is itself a finding.**
5. **Web / graph** *(candidate shape)* — typed entities joined by typed relations with cardinality (ER diagrams, ontologies).

**The seam move** (how shapes compose): model the structure first (name the types, pick the
shape), then watch for the *strain* — the moment the shape you have starts demanding another —
and add the next shape **at the seam**, don't rebuild. Common strains: *Sequence → Trajectory*
("what happens as state flows through this chain over time?"); *Stack → Set/Grid* ("what maps to
what across the layers?"); *Set → Stack* (the facets turn out to have their own ordering).

---

## Shape 1 — Sequence (chain)

### Business semantic chain — *flagship* · **⚠ UNDER REVIEW**
- **For:** the core causal spine — how a business expectation connects, step by step, to what you observe and who acts.
- **Status:** **use the shape, treat the exact slots as provisional.** The shape (Sequence) is not in question.
- **Slots (working form):** Stakeholder → Expectation → Business-Health Signal → (supported by) Application/System Signals → (if breached) Business-Impact Signal → Alert → Owner + Next Action. A motivation/realization lens runs over it: the first half (through the Signal) is *why we care and what we observe*; the tail is *response*.
- **Relation:** ordered causation; each link enables the next; reordering breaks the meaning.

### JTBD chain
- **For:** why an observability consumer needs what they need — the reasoning path behind a dashboard or signal.
- **Slots (general):** Need → Uncertainty → Resolution → Decision (each resolution creates the next need). **Observability narrowing:** Responsibility → Expectation → Measurement → the specific thing measured, at a specific altitude.
- **Relation:** ordered production; some uncertainties must resolve before others become meaningful.

### Implementation Architecture
- **For:** the build-order dependency of an implementation, foundation to aggregation.
- **Slots (5, "cannot skip"):** Business Context → Requirements Translation → Technical Implementation → Operational Artifacts → Enterprise Aggregation.
- **Relation:** strict dependency chain — each layer depends on the previous. Named "layers" but behaves as a *sequence* (dependency order, not altitude) — reads as **both Sequence and Stack**.

### A/B/C infrastructure dependency
- **For:** the maturity order in which observability infrastructure must be built.
- **Slots (3, depends-on):** A. Structured Data Model → B. Factory Pipeline → C. CI/CD Integration.
- **Relation:** enablement order — you cannot embed observability in CI/CD (C) without a factory (B); you cannot run the factory without structured definitions (A). (Codify → automate → embed.)

### Observability lifecycle
- **For:** the phase arc of standing up observability.
- **Slots (5):** Define → Implement → Enforce → Observe → Respond.
- **Relation:** ordered phases — a **phase sequence, not a behavioral trajectory** (no true states/events/transitions).

---

## Shape 2 — Stack (layers)

### Four-Layer signal model — *canonical, single source of truth*
- **For:** organizing all observability signals by business meaning, business-first.
- **Slots (4, outside-in):** **Business Health** (outcome attainment — "is the expectation being met?", Product Owner) · **Business Impact** (consequence quantification — "how bad when we fail?", PO + Ops) · **Application** (workflow correctness — "is the workflow executing correctly?", Dev/QA) · **System** (infrastructure health — "is the platform operational?", SRE). Plus a **conditional Agent Workflow** stratum (decision quality — activates only for agentic steps that can be *confidently wrong*; not a 5th unconditional layer).
- **Relation:** stack ordered by business-first priority; each layer has its own owner, question, examples. Cross-cut facet: **Business-first layers** (Business Health, Business Impact — this stack's additions) vs **Traditional** (Application, System).
- **Note:** always use full layer names, never numbers (numbering implies an inside-out reading order).

### Consumer layers
- **For:** which *form* of knowledge a given consumer needs — the same content re-rendered per audience.
- **Slots (5):** Positions/strategy · Standards · BAU/daily work · Learning · Knowledge substrate. Each: distinct consumer, job, artifact form. Established-name mapping: Policy · Standard · Procedure · Tutorial · Body of Knowledge.
- **Relation:** stratification by altitude/bindingness; **"different consumer = different form"**; single-layer execution is the decay signature.

### Separation of Concerns
- **For:** what can vary independently in the system — keeping stable foundations apart from volatile implementation.
- **Slots (5):** Methodology · Data Model · Production Systems · Use Cases · Workflows.
- **Relation:** layers by **abstraction / bindingness** (Methodology most stable), each with its own owner. **Distinct from Implementation Architecture** — this is the *abstraction* axis (what varies independently); that one is the *dependency* axis (what can't be skipped).

### Three-Signal model — *superseded*
- **For:** (historical) the predecessor typology of signal types.
- **Slots (3):** Traditional (System + Process subtypes) · Business Health · Business Impact.
- **Status:** **superseded by the Four-Layer model.** Shape is actually a typed **Set** (a typology), not a stack. Kept only to point at its successor.

---

## Shape 3 — Set (typed roles / facets; grid = two crossed axes)

### Knowledge-capture / task-decomposition schema
- **For:** breaking one activity into the fixed elements every piece of work is made of.
- **Slots (7, canonical):** ACTION · ARTIFACT · SCHEMA · PROCEDURE · ROLE · VERIFICATION · EXAMPLES.
- **Relation:** a typed set — completeness matters, order doesn't. (A 6-field projection that drops EXAMPLES is the same model.)

### Action Framework
- **For:** assigning observability thinking to each standard SDLC action (a distinct model from the 7-element schema — do not conflate).
- **Slots (4 dimensions):** WHO · WHAT LENS · WHAT GETS CAPTURED · HOW IT CONNECTS.
- **Relation:** each standard action (define SLOs, write queries, configure alerts, build dashboards, …) crossed with the 4 dimensions → cells. Grid sub-form.

### Signal Correlation
- **For:** reading the *combination* of layer states as a single decision surface.
- **Slots (7 named states):** All Clear · Silent Business Failure · Infrastructure Noise · Infrastructure Cascade · Process Failure · Multi-Layer Degradation · Contained Process Issue.
- **Relation:** grid — each state is a cell crossing three layer-axes (System × Process × Business Health) with values Healthy/Degraded/Critical; each carries a Meaning + Action + Urgency.

### Component Decomposition *(grid)*
- **For:** deriving system components from the onboarding workflow.
- **Slots:** 8-step workflow (Service Basics → Stakeholder Expectations → Business Signals → SLO Signals → Technical Signals → Business Impact → Technical Impact → Preview & Validate) × 4 orthogonal concerns (Database Schema Boundaries · Responsibility Boundaries · Workflow Dependencies · Component Value Realization) → Components A–E (Service Registry · Business Context · Signal Specifications · Impact Measurement · Artifact Generation).
- **Relation:** grid (Component E hangs downstream of the grid as an output).

### OKR Dimensional Decomposition
- **For:** decomposing an aggregate metric into named dimensions and claiming only the one your work moves.
- **Slots (method + flagship example):** the *method* — a metric = an aggregate of distinct phases/contributors/mechanisms; decompose, then claim the dimension you move. *Flagship (MTTR):* Detection → Diagnosis → Business Impact Assessment → Resolution → Communication (a business-observability practice claims **Business Impact Assessment**).
- **Relation:** **single-axis** facet decomposition (not a two-axis grid).

---

## Shape 4 — Trajectory (behavioral)

**Empty — and that emptiness is a finding, not a gap.** The models here are structural
(sequence / stack / set) almost exclusively. The behavioral family — states + events +
transitions over time — is the **growth edge**. *The seam to watch:* the business semantic chain
is structural, but "signal degrades → impact becomes real → expectation breached → propagation"
is a **trajectory running on it** — modeled almost nowhere.

---

## Shape 5 — Web / graph *(candidate shape)*

**Heterogeneous:** true node-edge graphs vs controlled vocabularies carrying typed distinctions
but no graph structure. Whether this is one shape, or splits, is still open.

### Domain Object Model — *true graph*
- **For:** the entity/relationship map of the observability domain.
- **Slots (entities):** an organizational hierarchy (product line → product → team) · a service hierarchy (CMDB Application · Service) · Signal Definition · Stakeholder Expectation · Signal History · Dashboard · Alert · Playbook.
- **Relation:** typed relations with **cardinality** — Contains, Belongs-to, Maps-to (the Application ↔ Service many-to-many), Defines, Produces, Displayed-in, Owned-by, Triggers, Monitors, Notifies. Two independent hierarchies joined many-to-many. Full ER diagram.

### Knowledge Graph Schema — *true graph*
- **For:** a bi-temporal knowledge graph of work state.
- **Slots (node types):** goal · workstream · track · thread · artifact · question · decision · argument · constraint · capability (grouped: work-breakdown / issue-argument / infra). **Edge types:** depends-on · gates · produces · responds-to · supports · objects-to · constrains · informs (each with a direction convention).
- **Relation:** typed directed nodes+edges; required fields per node/edge; bi-temporal validity (valid-from / valid-until).

### Semantic concept model — *requirements, not yet built*
- **For:** (specified) a concept scheme with broader/narrower lineage and cross-scheme discovery.
- **Slots (of the specified model):** SKOS — Concept, ConceptScheme; prefLabel/altLabel/definition/scopeNote; broader/narrower/related/inScheme/exactMatch/closeMatch.
- **Status:** a requirements draft, not an instantiated model — it *specifies* a graph to build. Included so the intent isn't lost.

### System Vocabulary — *controlled vocabulary (not a graph)*
- **For:** the ubiquitous language for the observability domain objects.
- **Slots:** term sets by facet — Organizational Hierarchy · Service Hierarchy · CMDB-to-service mapping · Signal Terminology · Stakeholder Terms · Artifacts · Process Terms. Each: preferred term / alternatives / definition / example.
- **Relation:** a typed **Set** (glossary with synonym control), not node-edge.

### Work Structure Vocabulary — *controlled vocabulary (not a graph)*
- **For:** the ubiquitous language for *how work is organized* (the meta level).
- **Slots:** term sets — Knowledge Management System (= Body of Knowledge + Practice Distribution) · Abstraction Level (Schema / Instance) · Knowledge Work · Lineage · Software Engineering Practice (Spec / Spec-Driven Development / Builder Distance).
- **Relation:** a typed **Set**; companion to the System Vocabulary ("how" vs "what").

---

## Composite / whole-system models (multi-shape)

### Operational Factory Model
- **For:** the production system that turns structured business context into observability artifacts at scale.
- **Slots:** Raw Materials (structured data model / templates) → **5 parallel Production Lines** (Story · Dashboard · Alert · Playbook · Documentation Factory) → Quality Control (lineage/field/template/cross-ref validation) → Finished Products.
- **Relation:** a **sequence backbone** (Inputs → Transform → QC → Outputs) with a **set** of parallel lines fanning out from one shared core data model. Analogs: CI/CD, "the factory is the product."

### Partnership Operating Model
- **For:** how a human/AI/repository partnership operates — roles, contract, failure modes, interventions.
- **Slots:** **Partners (3):** the Human (domain truth + fit-judgment) · the AI (craft + technical detail) · the Repository (shared memory). **Contract:** the AI owns craft, the human owns domain truth. **Information Architecture (4 destinations):** Reference docs · standing instructions · issue tracker · memory. Plus failure modes, an operating protocol, and a set of thinking layers a session must hold.
- **Relation:** a **set of typed-role sets** with one embedded sequence (workstream phases).

### Business Journey Mapping
- **For:** observability across a multi-stage business journey (not one service).
- **Slots (5 layers):** Journey Definition Model · Domain Event Backbone · Boundary Instrumentation · Journey Correlation Engine · Observation Layer.
- **Relation:** a **stack** (each layer feeds the next, own ownership), embedding a journeys-as-directed-graphs element.

### Motivation-Chain Onboarding Instrument
- **For:** eliciting a service profile by walking the product owner's reasoning path.
- **Slots:** a **6-phase workflow** (Service Context → Stakeholder Motivation Chains → Business Impact → Developer Diagnostics → Platform Infrastructure → Operational Context), closing with a verification pass, walking a per-stakeholder motivation chain (Stakeholder → Driver → Coverage gate → per-signal Requirement → Outcome).
- **Relation:** a **sequence (chain)** whose order is load-bearing, composing an embedded Stack (the four layers) and typed Sets (standard signal-dimension frameworks).

---

## Reading notes

- **The held entry (semantic chain):** shape is solid, slots provisional. Don't build on its exact slot list — use the shape.
- **Grain:** each entry is slots + relation + what-it's-for. Deeper worked examples are not inlined.
- **The shapes are the index; the models are the contents.** A new model you build should land here, tagged by shape.
