---
name: design-for-operations
description: >
  Run design for operations on one business process flow — recover from evidence
  what implements it, draft the business account from reference models, reconcile
  the accounts, and emit a practitioner's-draft observability specification:
  signals, healthy, ownership, and what cannot be seen, every claim labeled. Use
  when the business process is not yet known or instrumentable: the run supplies
  what monitoring assumes and rarely has. The model drafts everything
  and takes a position on everything; the human ratifies at the end. Use when the
  user says "run design for operations on [X]", "derive the business process flow
  for [X]", "recover what [X] actually does and what to monitor", "what can we see
  on [X]", or points at a codebase or estate and asks where the business process
  breaks.
---

# Design for Operations — the runnable instrument

The method is `reference/design-for-operations.md`; the target it aims at is
`reference/what-good-looks-like.md`. This skill is what an agent runs: an instrument, an output
contract, a worked example, and a verification discipline, producing a draft that a human
ratifies at the end.

**The unit a run covers:** one business process flow. Systems are what you own; business process
flows are what break.

## Standing rules

These are settled. Do not re-derive them mid-run.

- **Practitioner's draft.** Discipline applied, position taken on everything. A judgment cell is
  drafted in the accountable role's voice and labeled — never left as a secretary's blank. The
  only empty form is `gapped` with a reason.
- **The human ratifies at the end.** Where the human sits is a setting of the method, and its
  current value is at the end; the function-not-performer rule below is what makes it movable.
  It is known going in that the output is a draft. Judging conditions 4, 6 and 7 (rulings,
  healthy, tolerance and ownership) are the draft boundary under this setting, not gaps. **A run
  never moves the setting.**
- **Function, not performer.** Every phase below is a contract — in, out, labels. Tool, model, or
  human can perform any of them; this skill states the default. A run needs no other humans to
  complete.
- **Sources compose.** Code, what actually ran, a stated architecture, an industry reference
  model — used together. More sources held at once is more corroboration; disagreement between
  them is a finding. Independence is a property of the sources, recorded per claim
  (`drafted_from`), never staged as a blind fork.
- **Structure is extracted, never read — and the measurement behind that is narrow, so do not
  generalize it.** A model asserting **cross-service** structure from flattened source scored 0%
  precision and recall; on **locally evidenced** claims the same study scored 74–93% (De Luca et
  al. 2026, arXiv:2606.26927). The rule is about relationships spanning services, not about
  every use of a model on code. Structure
  comes from a tool with file and line, or it is `gapped`. A model sorts and labels what the
  tool found; it may not add a connection it "saw."
- **Scope is fixed for the run.** Mainframe subjects are declined, not worked around. Who must act
  on the findings is out of scope: the run produces a specification and a queue, not
  obligations. A method question arriving mid-run is answered from
  `reference/design-for-operations.md`; a run that produces a document about the method instead
  of the specification has failed.

## Provenance labels — on every claim, no exceptions

| Label | Meaning |
|---|---|
| `extracted` | A tool produced it, with file and line. Verifiable without trusting a model |
| `proposed` | A model drafted it — inference or role-voice judgment, awaiting ratification |
| `ratified` | A named person accepted it. Recorded, with who and when |
| `gapped` | Could not be determined. Carries the reason and what would close it |

An absent field cannot distinguish "asked, none found" from "never asked" — write the empty form.

**A verbatim quotation from a document is `extracted`** when it carries a resolvable location —
anyone can open the file and check the string, so the verification story holds and no model
judgment produced it. What the quotation *means* is `proposed`.

**`gapped` is a provenance label, and it is not the only empty-looking value in a run.** The
signal dispositions (exists and watched · exists and unwatched · cannot be produced), `unowned`
on a boundary, and `not exercised` on a phase are content values in their own vocabularies. A
cell can be `extracted` and say "cannot be produced" — the label is how the claim was
established, never what it says.

No checker verifies labels or citations. The contract holds by convention: treat any citation
that does not resolve as a defect to record, and never read a `proposed` location as if it were
`extracted`.

## What ships beside this file

| File | Role in a run |
|---|---|
| `reference/design-for-operations.md` | The method — views, concerns, vocabulary, the seven passes. The reasoning source |
| `reference/what-good-looks-like.md` | The target: three stacked views over one capability, and what each may **not** claim |
| `JUDGING-INSTRUMENT.md` | Acceptance: seven conditions, each a field's own done-condition |
| `fact-extractor/README.md` | **Phase 1's built default** — Semgrep rules, a runner, a coverage reconciliation, a join, a precision sampler and a conformance check. How to run it, what it reports about itself, what it cannot reach |
| `INTEGRATION.md` | How to fit a different extractor to Phase 1, and how to score the fit instead of asserting it |
| `adapter/adapter.py` | Turns a finished run into a dependency graph and an ordered business process, in the format stated at the top of the file, as source material for onboarding a service |
| `view/render_run.py` | **Phase 8's render step.** Turns a finished run into one self-contained page — no network, no third-party package, no CLI on PATH. `--check` reports which inputs a run is missing and which phase owes each |
| `example/PLACING-AN-ORDER.md` | The shape of the output document, from one complete run. Right-shaped — **not** the quality target. If your subject is the same application, this file is also the prior answer, and reading it contaminates the run |
| `example/RATIFICATION-QUEUE.md` · `example/JUDGING-SCORE.md` · `example/VV-REPORT.md` | The queue, the score and the verification report from that same run — the other three files a run produces |

Paths are relative to the directory that holds this skill.

## Vocabulary that binds every output

- **Business process flow**, always written out. Never a bare "flow"; never "business step".
- **Stage** — a business-meaningful segment of a business process flow. The stage test: would a
  business person name it, and would they care if it stopped? **Step** — an application-level
  action within a stage.
- **Convergence / divergence / absence** — the three results of reconciling an account against
  extracted structure.
- **Signal disposition** — exists and watched · exists and unwatched · cannot be produced.
- Three views (business process, application process, technology) and four concerns (impact,
  cause, throughput, trend), as the method defines them. A view is never named after a concern.

## The run

Every phase: **In → Out**, performer, labels. Each phase heading names the method pass it
performs — the run's numbering and the method's do not align one-to-one. Work products land in a
run directory named for the subject. Findings about the instrument itself are classified and
recorded, whatever the mode (see the V&V discipline at the end).

### Phase 0 — Frame the run *(run setup — no method pass)*

- **Subject:** one business process flow, named. If the user brought a system or an estate, the
  candidate business process flows are drafted and the user picks one. The drafted candidate
  list is kept in the run directory — Phase 5 consumes it.
- **Coverage cell**, stated before starting (method Part V): Proof (1 business process flow × 1
  concern) · Pilot (1 × all 4 concerns) · or an in-between cell — the method holds unnamed cells
  legitimate; **stating** the cell is the obligation.
- **Source inventory:** which of code, runtime evidence, stated architecture, industry reference
  model, recordings and documents are reachable. An absent source changes what the result is
  worth; it never blocks the run. Record the inventory in the run directory.
- **Mode:** normal, or V&V (first run of this skill, and after any instrument change).
- Read `example/PLACING-AN-ORDER.md` in full before writing anything — shape, not content.
  **If the subject is one that already has a run, the prior specification is also the prior
  answer**: reading it contaminates this run, which then corroborates nothing. Record the
  contamination in the framing and expect judging condition 2 to fail on that ground — it has
  happened, and that is exactly what it cost.
- **Out:** the framed run — subject, cell, source inventory, mode, candidate list — recorded in
  the run directory. Performer: model orchestrating, with the user's pick.

### Phase 1 — Extract structure *(method pass 1)*

**This phase is a contract, and the tool that satisfies it is a choice — not a fixture.** Stated
that way because it was got wrong once: an early version of this skill named one hand-written
script as *the* performer, which contradicts the function-not-performer rule and implied that a
few hundred lines of pattern matching is the engineering answer for a real estate. It is not.

**The contract.** In: the source of the systems the subject runs on. Out: structural facts —
entry points (inbound routes, scheduled jobs, message consumers), calls between deployables,
configuration bindings, durable-state writes and reads — **each carrying a file and line**,
labeled `extracted`. Performed **deterministically**: the same source gives the same answer, and
a person can check any fact without trusting a model. The model sorts and labels what the tool
found; **it never adds a connection it "saw" by reading source** — measured at 0% precision and
recall when tried.

**Choosing the tool is an engineering decision made per estate, from established practice.**
Multi-language code analysis is a solved field with named tooling; this method composes it rather
than reinventing it. If the estate already owns a code-analysis tool, it is very likely the better
instrument: read `INTEGRATION.md`, fit it, and score the fit with `fact-extractor/contract.py` and
`acceptance/accept.py`. Whichever tool performs the phase, record its name, version and exact
invocation in the run directory.

**The built default is `fact-extractor/`** — Semgrep rules plus a thin runner, covering C#, Java,
Python, Go and JavaScript/TypeScript by rule, each fact carrying file and line from the tool
itself. Its README says what is measured and what is not. The invocation is part of the contract:

```
python fact-extractor/run.py <repo-root> --service-map src/a=a src/b=b ... > fact-base.json
python fact-extractor/coverage.py <repo-root> fact-base.json > coverage.json
python fact-extractor/join.py     <repo-root> fact-base.json > join.json
```

Two rules decide whether it works at all, and getting either wrong yields a confidently empty
result that reads as a finding rather than a mistake:

- **Scan root is the repository root**, never a subdirectory. Service-map keys are
  repo-root-relative, so a `src/` root makes every one of them miss silently.
- **A service map is required** — one `<source-path>=<deployable-name>` pair per deployable.
  Without it the join returns nothing. A load generator or a test harness is not a deployable
  and does not go in the map.

Sanity-check before proceeding: zero facts, or zero edges, on a codebase that obviously has them
means the invocation is wrong. Re-check the two rules **before** recording anything.

- **Check the selected tool covers the subject before running, and say so in the framing.** An
  unsupported language returns nothing *by construction*, which looks identical to "this system
  has no structure." Name what the subject is built from, what the tool reads, and record the
  remainder as `gapped` with the missing support named — never report an empty extraction as
  evidence.
- **Mainframe is out of scope.** A mainframe subject is declined, not worked around.

**The run tells you when it did not read the estate. Act on it in the same run — do not report it.**
`run.py` emits a `reach` block naming every declared deployable that produced no facts, how much
source each one has, and which file types nothing read. **A run whose `reach.complete` is false is
not finished and its output is not presentable.** Work each silent deployable before going on:

1. **Read the size first.** A hundred lines and no facts is a thin launcher whose behaviour is all
   framework — a Spring Cloud config, discovery or admin server is two annotations and a `main`,
   and zero facts is the correct answer. Record that and move on. Thousands of lines and no facts
   means nothing read it.
2. **For each large one, run the loop below** — ask the tool what it can parse, author rules from
   the framework's documentation, confirm by opening matches, write the rule back marked
   provisional. On one polyglot reference application this turned six unread deployables into
   zero and an estate that yielded no dependencies into one that yielded sixteen.
3. **Only where the parser genuinely cannot read it** does a deployable stay silent — and then it
   is recorded as `gapped` with the language named and with which other source covers that part.

**Handing the reach block to a person as advice is the failure this replaces.** The check exists so
nobody has to notice; leaving its output for someone else to act on puts the noticing back.

**A rule you author is not trusted because you wrote it.** Run it against *other* subjects before
accepting it. A rule authored for one estate's Express routes matched 124 test-framework selectors
on the next estate it met, all filed as inbound routes. **What transfers between estates is
coverage, not precision.**

**When the subject contains something the rules do not cover — a different language, or a
familiar language used in an unfamiliar way.** This happens on every real estate; on one reference
application it happened four times. Do not stop at recording a gap. Work it:

1. **Separate the two failures first, because they have different answers.** Ask the tool what
   it can parse (`semgrep show supported-languages`). **Cannot parse it** → nothing here will
   work; record `gapped` naming the language, and say which other source covers that part.
   **Can parse it, no rule exists** → writable, continue.
2. **Author candidate patterns from the framework's own documentation**, not from reading the
   subject's source for structure. Then test each against the subject.
3. **Confirm by opening cited locations. Never by the count looking right.** A pattern once
   returned six matches on a file with six attributes, and they were six unrelated expressions on
   different lines. A count that agrees by coincidence is the failure mode this whole method
   exists to catch.
4. **Three syntax traps, so they are not rediscovered.** A bare Java annotation is not a
   standalone pattern — attach it to the declaration it decorates. A C# attribute matches
   *without* its brackets: `HttpGet(...)`, not `[HttpGet]`. And **a rule keyed on a construct the
   parser fails on will never match** even though the rest of the file reads fine — key it on
   something else in the same file, which is how a hosted worker is found through its method
   body when its class declaration cannot be parsed.
5. **Label honestly.** Facts from a rule whose matches you have not opened are `proposed`, not
   `extracted`. The label is about how the claim was established, and an unconfirmed rule has
   not established anything.
6. **Then check your own work two ways.** Run the coverage check — a service that writes durable
   state or calls out but shows no entry point has an unmodelled idiom, not an absent entry
   point. And look for a declarative source that enumerates the same population — a protocol
   definition, an API description — and reconcile against it by name.
7. **Write the rule back — marked `provisional: true` — and report that you did.** A rule
   authored under fire improves every later run's recall while carrying its author's precision
   unexamined: verified on this estate, it becomes a silent default on the next. So it enters
   the library with `metadata.provisional: true`, the estate and date that produced it, and
   what it was checked against. **The runner then counts every fact resting on an unratified
   rule and reports it on every run** — the announcement is generated, not remembered.
8. **Route it as an instrument change, because that is what it is.** A run that had to invent a
   rule found the instrument lacking. It goes in the V&V report, gets a line in Gotchas, and
   **goes in the ratification queue** — an authored rule is a judgment call that outlives the
   run, which makes it more consequential than the per-run drafts around it, not less. It stops
   being provisional when someone rules on it, and not before.

**The honest limit, stated so a run does not overclaim.** Opening a rule's matches proves it is
not matching junk. It does **not** prove the rule finds every instance of the idiom — that is a
different question, and only a declarative source answers it. **A category with a new rule and
no declarative source stays `unmeasured`.** Say so rather than reporting it as covered.

- **Sources compose** where the extractor cannot reach — runtime evidence, a stated
  architecture, the industry reference model, or people. A run states which it used, up front.
  What the extractor reads and what it cannot, in three tiers: `fact-extractor/README.md`.
- Genuine zero output on a covered language, invocation confirmed, is an INSTRUMENT finding
  plus `gapped` structure cells. **Never substitute model reading**, and never quietly widen
  what the tool claims to have found.

### Phase 2 — Draft the business account *(method pass 3)*

- **In:** industry reference model for the sector, whatever stated architecture or documents
  exist, and declared sequences where they can be had — a business process engine definition, a
  status enum, a job graph. **The extractor does not produce declared sequences.** A
  declared-sequence artifact the run was pointed at may be read by the model and enters
  `proposed` with file and line — never `extracted`, and never as a cross-service connection,
  which stays tool-only. **Out:** stages in business words, in order, each carrying
  `drafted_from` and `proposed`, plus open questions.
- **The order is the point of this phase, and it comes from knowing the business — not from
  anywhere else.** A credit request precedes closing documents in lending; stock is checked
  before goods ship. That is domain knowledge, and drafting it here is why the method can state
  a sequence at all. **It is `proposed` and it stays `proposed` for the whole run.** No later
  phase promotes it, because no later phase has a source that could.
- **Performer: model**, drafting. Apply the stage test: would a business person name it, and
  would they care if it stopped?
- Expected failure profile is structurally right and locally wrong — that is the profile a
  reviewer corrects fastest. Say so in the draft.

### Phase 3 — Reconcile the accounts *(method pass 2, plus pass 4's stage-to-code binding)*

- **In:** Phases 1 and 2, plus any stated architecture. **Out:** every **stage** from Phase 2
  classified — **convergence / divergence / absence** — against the extracted structure. The
  stage is the unit; where a stated architecture also exists, its named entities and edges are
  classified the same way as a second pass. The classification is mechanical once the mapping
  exists; the mapping from stated entities to source is `proposed`.
- **An absence is bounded by the tool's reach, and says so.** The extractor is pattern-fitted;
  an unmatched stage means *these patterns found nothing*, not *the code does not do it*. Label
  an absence `proposed` and name the pattern class that would have had to match. Only where
  that class is known-covered for the subject's language and shape does an absence become
  `extracted`.
- **Classification is about whether a stage EXISTS here. It is never about the order.** A stage
  classified `convergence` means the code does this thing, at these lines. **It does not mean the
  code confirms this thing happens when Phase 2 said it does.** Nothing in an extraction can
  confirm that: reading source establishes that a step *can* hand to another, never that it
  *always* does. Static sequence reconstruction admits transitions that never occur and is
  undecidable in general; the discipline that confirms a real sequence consumes the record of a
  system that ran.
- **The specific sentence that must never be written**, because a run wrote it: *"the chain is
  A → B → C, readable from the handler names."* That is a model reading English in class names
  and presenting it as corroboration from code — the move the tool-only rule forbids, measured at
  zero precision for cross-service claims. **The order needed no support; it already had Phase
  2.** Borrowing a second source it has not earned is how a `proposed` order gets read as an
  `extracted` one. The example run's verification report records it as I4.
- **What a code rule can legitimately contribute, when one exists.** That stage A's
  implementation *can* hand to stage B's — one hop, a file and line at each end. That is real
  corroboration for a drafted order. **Composing those hops into a claimed sequence is the same
  violation by a longer route:** every consumer of an event is a possible successor, and a
  branch is indistinguishable from an alternative.
- **Report convergence explicitly.** Without it there is no answer to "how wrong was our
  architecture," and the output reads as an indictment instead of a measurement.

### Phase 4 — Rule on each difference (practitioner's draft) *(the investigate step of pass 2's loop — not method pass 4)*

- **In:** every divergence and absence. **Out:** a drafted ruling per difference, in the
  accountable role's voice — stale belief, wrong draft, or real hole — with the reasoning,
  labeled `proposed`.
- A difference is a question, not a verdict. A drafted ruling corrects whichever account it
  indicts; re-run Phase 3 classification until the two accounts stabilize. The borrowed
  practice is a loop, not a pass.
- **Ask the ruling question of convergent stages too.** A service can consume the right event,
  decide an outcome and publish the right downstream event while performing none of the work the
  stage names. Structurally it converges; functionally it is hollow. The example run found two
  such stages, and every mechanical check passed on both. Convergence is not evidence of
  function.
- The ratification queue starts here: every drafted ruling lists the role that would ratify it.

### Phase 5 — Select what matters *(method pass 5)*

- **In:** the candidate business process flows — Phase 0's kept candidate list where an estate
  arrived, plus any the run surfaced — with incident history and frontline channels where they
  exist. **Out:** survivors each with the reason it survived, cuts each with the reason it was
  cut — labeled `proposed`.
- On a single-candidate subject, record **not exercised** — one candidate, nothing to cut
  between. Do not manufacture a selection.
- **A candidate the run surfaces mid-way does not join the subject.** Phase 0 closed the
  subject; record the new candidate in this phase's output as a seed for the next run, with
  where it surfaced. Widening scope mid-run is how a bounded run becomes an unbounded one.

### Phase 6 — Specify observation *(method pass 6)*

**In:** survivors with bound stages and boundaries (Phases 3–5). **Out:** the cells below,
labeled. Performer: model drafts; every cell awaits ratification.

Per stage of each survivor, at its boundaries (where a step crosses systems or into durable
state):

- **Signal**, with the three-way disposition — exists and watched · exists and unwatched ·
  **cannot be produced**. The cannot-be-produced call is decidable from extracted evidence:
  nothing emits the data. **The watched/unwatched split is not** — it needs a telemetry or
  dashboard inventory from the monitoring platform, which no phase of this run produces.
  Without one, say so: the signal is producible, and whether anything watches it is `gapped`
  with that reason. **Do not settle it by reading code** — that is the failure the tool-only
  rule exists to prevent. The cannot-be-produced list is usually the most valuable output.
- **Healthy**, drafted from whatever expectation source exists (a stated objective, an
  industry norm, incident history) and labeled `proposed` — or `gapped` naming what is
  missing. Expected volume is a business fact; code cannot produce it and this run never
  pretends to.
- **Owner**, from ownership evidence as a `proposed` candidate — or `unowned`. A falsely
  assigned owner is worse than a visibly unowned one. Never attach a plausible name.
- **Too broken**, per survivor: how much broken is too much, and who owns that number — the
  plain rendering of impact tolerance. Drafted from expectation sources where any exist, else
  `gapped` naming what is missing. This is judging condition 7's input; without this cell
  Phase 8 cannot score it honestly.

### Phase 7 — Assemble and account *(assembly of the passes' artefacts)*

- **In:** everything Phases 1–6 emitted. **Out:** the specification document — the business
  process flow, what implements each stage, what can be seen, what cannot — in the shape of
  `example/PLACING-AN-ORDER.md`, every claim labeled. Alongside it, `stages.json` in the shape
  of `example/stages.json`: the stages in order, each with its bound components and its ruling,
  which is what the adapter reads after the run. And `observation.json` in the shape of
  `example/observation.json`: Phase 6's cells, per stage and per signal, each carrying its label. The
  disposition as two pairs, `producible` with the file and line that shows it, and `watched` with the
  inventory consulted or the words `no inventory reachable`; healthy; owner; and per business process
  flow the too-broken cell and Phase 2's business account. The adapter reads it (`--observation`) to
  seed onboarding under the label table in its docstring. A seed is never source material.
- **Coverage accounting:** declare the start-set (stages, boundaries, wanted signals); every
  element ends `covered` or `gapped` with reason and provenance. **No third state.**
- **The vocabulary above binds the specification and the judging score** — they are the
  method's product. Working papers and phase records are not bound by it; the run's README says
  which files are which.

### Phase 8 — Judge, then present *(acceptance — not a method pass; pass 7 feed-back needs a running estate and sits outside a run)*

- Score the run against `JUDGING-INSTRUMENT.md` — all seven conditions, evidence quoted from
  the run's own output.
- **The score is not self-graded alone.** Before presenting, have the specification read cold by
  a reviewer that did not produce it — a second agent, a second session, or a person — and land
  its findings beside the run. Trails drift exactly when independent reading stops, and that is
  not fixed by being more careful.
- Expected profile: conditions 1–3 and 5 met or honestly not-exercised by the machine half;
  conditions 4, 6, 7 land as **drafted, awaiting ratification** — that is the design, not a
  failure.
- **The ratification queue is a file:** `RATIFICATION-QUEUE.md` in the run directory — every
  `proposed` cell grouped by the role whose yes it needs. Rulings are recorded there (who,
  when, accept or reject), and the specification's labels flip to `ratified` from that record —
  the queue file is what makes `ratified` producible at all.
- **Render the run as one page** — `python view/render_run.py <run-directory>`, which writes
  `READ-THIS-RUN.html` beside the run's documents. Rendering is not a pass and establishes
  nothing: it reads `observation.json` and `stages.json` from Phase 7 and the fact base from
  Phase 1, and shows what they already say. `--check` on the same run reports which of those
  three a run is missing and which phase owes it; a run that cannot be rendered has a Phase 7
  output missing, which is a finding about the run rather than about the renderer.
  **The page distinguishes a stage no code implements from a stage the code carries that
  nothing can measure.** Those are different findings and a run that collapses them misreports
  itself — measured on Bank of Anthos, where seven absence stages read as unwatchable ones.
- Present to the human: the rendered page first, then the specification document, the judging
  score, the independent read, and the queue.
- **Record the run** in the run directory's README: subject and revision, tool and invocation,
  mode, the score. A run nobody can find is a run the next one cannot build on.
- **Done =** the document and queue exist in the run directory, the page renders and
  `--check` returns clean, the accounting has no third state, the score and independent read
  are recorded, and the run is recorded. Ratification is outside the run.

### After the run — onboarding

A finished run can be turned into two structured blocks — the dependency graph and the ordered
business process, in the format stated at the top of `adapter/adapter.py` — so a service can be
onboarded from recovered evidence rather than from prose somebody has to trust:

```
python adapter/adapter.py fact-base.json join.json stages.json > onboarding-blocks.json
```

The adapter refuses to invent a node to make an edge resolve, to carry a step whose components
are not in the graph, or to emit a stage the run did not rule on. It labels the one judgment it
makes — whether an edge is critical or degraded — as inferred from a stated rule, so a reviewer's
first job is to demote the ones that have a fallback the code does not declare.

## V&V discipline — first run, and after instrument changes

**Both modes classify and record every instrument finding** in the run's V&V report. The
difference: normal mode may then fix and continue; V&V mode never fixes — it reports and moves
on. **A run never edits this file, in either mode** — including Gotchas. Filing an issue and
adding the Gotchas line are done *after* the run, by whoever holds the instrument, from the run's
report. A run that edits the instrument it is testing has destroyed its own result:

| Class | Meaning | Destination |
|---|---|---|
| **INSTRUMENT** | A phase contract produced the wrong kind of output, named an input with no producer, or was ambiguous enough to need inventing | The run's V&V report — then, after the run, an issue and a Gotchas line |
| **CONTENT** | Right shape, wrong facts about the subject | The ratification queue |
| **EDGE** | The subject has a pattern no phase handles | Design backlog, recorded in the run report |

The V&V report lands beside the specification in the run directory. `example/VV-REPORT.md` is
one.

## Critical constraints

- **No method derivation.** A method question arriving mid-run is answered from the method
  reference and the run continues. The method document is never touched by a run.
- **No compliance scope.** Who must act on the findings is excluded. The run produces a
  specification and a queue, not obligations.
- **Vocabulary binds.** Business process flow written out. No bare "flow", no "business step",
  no concern-named views.
- **Uncited output is net-negative.** Every claim carries its label. Plausibility without
  provenance reads exactly like evidence.

## Gotchas — observed failures accrete here

Point-of-use anchors above carry the measured ones (extractor fitted to one subject,
model-read structure, declared sequences without a producer, the invocation's cost). A new
failure observed in any run lands here as one line with the run and date — added after the run,
never by the run.

- **On a subject with no real owners, the ratification queue comes back with no names** — the
  never-attach-a-plausible-name rule is doing its job. Draft every position anyway and record
  the roles as unfilled; the queue is still the output. *(first cold run, Bank of Anthos)*
- **Config-derived edges can describe two mutually exclusive deployment topologies at once** —
  seven of eleven edges came back `ambiguous_config`. No phase says which topology to reconcile
  against; pick one, say which, and record the other. *(same run)*
- **Two stages can bind to the same code location**, which Phase 6's per-boundary signal
  placement does not expect. Place one signal and note both stages. *(same run)*
- **A run will try to corroborate its drafted order from the code, and there is nothing there to
  corroborate it with.** On an estate whose services announce rather than call, handler class
  names spell the business process out in English and the temptation is severe. The order is
  Phase 2's and needs no second source; a sentence claiming the code confirms it is the
  tool-only rule broken. *(eShop order run)*
- **"The order cannot be recovered from source" is not the same statement as "the order cannot
  be known", and a run collapsed the two.** Findings about static sequence reconstruction bound
  what *code* yields. They say nothing about what domain knowledge yields, which is where the
  order comes from. *(same run)*
