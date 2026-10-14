# Filling a register for one capability

For a language model drafting from the source material it is given. The run never stops to ask a person: what
the sources do not state, the model infers plausibly and labels `proposed:` with its basis, and a person confirms
or corrects those rows afterwards. The result is a filled register (the tables in
`register-template/`, defined in `register-template/REGISTER.md`) from which `one_canvas.py` draws the
design-for-operations map, and from which `flow_outputs.py` generates each stage's slice, measures, alert and
runbook.

These are design-time views. You are describing what the capability is and where it could be seen, not reading
a running system. Nothing you write is a live value.

**This procedure is the method's procedure, applied to a register.** The method is
`reference/assigning-business-work-to-levels.md` (cited below as *Assigning*, with its Step number)
and `reference/what-each-level-can-report.md` (cited as *Rules*). Where a step below says what to do,
the method says why. The terms are defined in `reference/vocabulary.md`, and the measure layers in `reference/four-layers.md`. One thing is built first, and everything else is read off it: **the case's lifecycle**,
the states one case passes through and the moves between them. Stages and alerts are drafted from it with the
basis of each cited; steps, parts, measures and the runbook are each derived from it by a stated rule. Either
way a later check has something to compare them with.

Three sources feed a register: the **code**, the **documents** (runbooks, architecture pages, service catalogue
entries, the business's own process descriptions), and anything people have said that was written down (notes,
tickets, recorded answers). Code shows what carries each move. Owners, responders, promises and volumes that no
source states are inferred and labelled `proposed:`; volumes stay named for the operators to measure.

## Before you start

1. Copy the CSV files in `register-template/` (not `REGISTER.md`) to a folder named for the capability. As you
   do each step below, add a row to `how-made.csv`: what went in, which files came out, and who did it (a tool,
   a model drafting, a person confirming, or by hand).
2. Decide what you will read. List each source in `sources.csv` with pass `1`, and keep the
   summary in `about.csv` → `sources_examined`, so a reader knows what "not assessed" covers. If the code has no
   version history, list it as the folder as found, with the date you read it.
3. If a code reader is available (the design-for-operations fact extractor, or your platform's equivalent), run
   it over the repository with a service map you write: one entry per deployable. It gives calls between those
   deployables and, where its rules cover the language, emission sites (logs, metrics, spans), each with a file and
   line. Its reach differs by language and by kind of fact, so read in its own documentation what it covers: a
   language it cannot parse, or a kind it has no rule for, yields nothing, and nothing is not absence. What it did
   not find is not looked for: read the services and deployment files it found nothing in, and cite what you read.
4. Name the configuration you describe: which optional components are switched on. Describe the one that runs
   in production, or, where several do, the one that carries the capability's AI agent. Write it in
   `about.csv` → `what_it_is`. If no source says which runs in production, describe the fullest one the
   repository defines, and write `proposed:` and why.

## Step 1. Declare the frame (*Assigning* Step 0; *Rules*, Rule 0)

Five declarations, written before anything else and never inferred silently:

| Declaration | Where it goes | The rule |
|---|---|---|
| The case | `flows.csv` → `case` | One individual business item: one order, one application, one appointment. Never a system, a team, a batch, a request or a basket. A flow has one kind of case |
| The delivering application | `about.csv` → `delivering_application` | The deployables that make up the application, named. Step 5 separates component from external dependency on membership of this set, so write it now |
| Whose expectation | `flows.csv` → `expectation_of` | The party counting on the outcome |
| The starting event | `flows.csv` → `starts_at` | **The act that first creates the case's record.** Cite the line that creates it. This is also where the party begins counting on an outcome: before it there is nothing for them to wait on |
| The ending outcome | `flows.csv` → `ends_at` | Where the party has what they were waiting for, or definitively does not. Name both endings. **The flow runs to that outcome even where the code stops sooner:** an order is delivered, not "Shipped"; the stretch after the last state the system records is added by the reference-model check in Step 3, drawn as not assessed |

**Everything before the case exists belongs to another flow.** Browsing, filling a basket, signing in, filling
in a form: real work, and set aside for this one. Write each in `set-aside.csv` with kind `other flow` and the
evidence, so a reader sees it was looked at. If the business would call something before the record its start,
say so in that row; it is a finding about where the record is created, not a stage of this flow. **Each piece of
work set aside as `other flow` is also a row in `flows.csv` now**, with its own case and no stages: the capability
carries it, and it is walked separately (Step 8).

If several kinds of case are plausible, name them, pick one, say why. If the source holds no case at all,
stop: draft the capability alone and say the rest would be fabricated.

`case_identifier`: the field that names one case, and every place it is lost. Read the code for it.

## Step 2. Build the case's lifecycle (*Assigning* Steps 1 and 4)

Walk one case from the line that creates it to each ending, through the code, and write `lifecycle.csv`: **one
row per move**, the act that takes the case from one state to the next. Walk the case, not the code's
structure: a call graph shows every hop and hides every wait.

For each move, record:

- `from_state` and `to_state`: the case's states, named as the system records them where it does (a status
  value, a table, a flag) and cited. Where the system records no state but the case plainly waits, name the
  state in words and write `implicit:`. The first row's `from_state` is `(none)`: it is the creation move.
- `from_kind`: whether the case **parks** in `from_state` (`park`) or is still inside an act (`in act`).
  **A case parks when nothing is progressing it and the next move needs a trigger that is not already in
  motion**: a timer or schedule, a person, an outside party, or the customer. A message already sent to a
  consumer that will act on it without any further trigger is the act still working, like a call out and back:
  `in act`. A poll that picks cases up on a schedule is a timer: the case is parked until it runs. Write which
  trigger in `park_because`.
- `move`: the act, in the case's terms ("stock is confirmed for the order"), never the performer.
- `path`: `main`, `alternative` (another ending the design allows: rejected, cancelled) or `exception`.
- `travels_by`: how the move reaches the case: `in-process`, `call` (HTTP, gRPC), `message` (name the event and
  the broker), `outbox` (written with the state, relayed later), `poll` (a worker on a schedule), `timer`,
  `person`. A move that takes several hops lists them in order, `;` separated.
- `carried_by`: the parts that carry the act out. `needs`: the stores, brokers and outside services the move
  cannot complete without. **Write each part as its subject id and name (`S04 Ordering API`)**, giving it the id now
  that becomes its `subjects.csv` row in Step 5. Every output is generated from these two columns, so a part named
  here and nowhere in `subjects.csv` fails the check.
- `timing`: what the code assumes about time for this move (a grace period, a poll interval, a timeout, a retry
  schedule), cited. Leave blank if nothing is assumed. **A retry or timeout counts only where the code applies it:**
  read the call site, not only the setting (a policy configured but wrapped around the wrong call never fires).
- `if_not`: what happens to the case if the move does not happen: retried by what, until when; left in
  `from_state` with nothing to move it; lost; failed back to the party. Cite it. This is the summary; Step 11 reads
  every hop's failure modes one by one, and where that reading finds the summary wrong, correct it here.
- `recovery`: `moves on`, `stranded`, `not created` or blank, as in step-impact.csv (Step 10).
- `irreversible`: `yes` where the move cannot be undone (money taken, goods shipped, a filing made).

Parallel moves get `parallel with <move>` in `order_note`; a move back to an earlier state gets `loops to
<state>`. Exceptions the code does not handle are written as `if_not`, not invented as moves. **A failure the code
does handle by telling the party** (an error page, a refusal returned to the caller) is a move: path
`exception`, into an ending named for it (`implicit: order failed back, shopper told`). Every way a case can leave
its stage then has a row, and a step (Step 4).

**An act that changes no state of the case** (emptying a basket, sending an email) is still a row, with `to_state`
the same as `from_state`. Its `from_state` is the earliest state it happens in: if it runs inside the same request
or transaction as another move, it takes that move's `from_state`, and so sits in that move's stage. Nothing waits
on it, so it never opens or closes a stage.

**A move that can leave from several states** (a cancellation allowed until payment) is one row per state it can
leave from, each cited to the guard that allows it.

## Step 3. Cut the stages from the lifecycle (*Assigning* Step 4)

**Draft the stages by judgment and say what each cut rests on.** A stage ends in a value item for the party in
`expectation_of`: something they would recognise as done (*Assigning*, Step 4). Consider the parks, the
`irreversible` moves, a status the business uses, the domain's standard process and the documents. None of them
forces or forbids a boundary. Do not cut by service, sub-agent, deployable, a status the system exposes, or
message.

- Stage 1 runs from the starting event. A stage holds its entry state and the moves out of it.
- `entry`: the state the case is in when it enters. `exit`: the state it is in when it leaves (the next stage's
  entry, or an ending). Both are states read off the lifecycle. In `source`, cite the rows and what the cut rests
  on, or write `proposed:` with the reason.
- Name each stage for what it achieves for the case, verb first, two or three words. The state at the boundary
  is the exit criterion, not the name.
- `promise`: a stated bound if a source gives one. Otherwise `proposed:` and a bound read from the
  lifecycle's `timing` for the stage's moves, cited: what the application's own design assumes. If the design
  assumes nothing, write `proposed: none assumed by the code` and say what would set one. A stage with no bound
  is a finding about the flow, not a reason to stop.
- `arrivals_per_period`: `not stated: measured by the operators`, unless they give it.
- Do not merge or split to reach a count.

**Then check the cut against the domain's reference model** (APQC's process classification, SCOR, the domain's
standard process), from the starting event to the ending only. A stretch the reference model expects inside
that frame that no lifecycle row carries is added as a stage or step with no participation, drawn as not
assessed. A stretch the reference model puts before the case exists is set aside (Step 1).

## Step 4. Write the steps from the moves (*Assigning* Step 5; *Rules*, Rule 0)

**Each step is one move, or several moves with no park between them that make one outcome the business would
recognise.** No park between moves is needed to merge them, and is not enough: work that never waits is still
several steps where it makes several outcomes the business would recognise. Hops between components inside one
outcome are one step: they are mechanism, recorded in Step 6.

- Name the step as its outcome, without its performer: "Stock is confirmed for the order", not "Catalog API
  confirms stock", never "POST /items returns 201".
- **Every stage's last step is the move that takes the case out of it**, into the next stage's entry or an
  ending. One step per way out: the main move, and each alternative or exception ending. A stage with no step
  whose `to_state` is its exit is cut wrong: go back to Step 2.
- `right_outcome`: what a right outcome is for one case, stated or `proposed:` (the state the case should be in
  after it, with the values it should carry).
- A step carried only in part gets `qualifier` `partial: <what is missing>`; one carried by a stand-in (a
  hard-coded value, a simulated call) gets `stub: <what stands in>`. A step nothing carries stays, with no
  participation rows.
- Write the lifecycle row ids each step comes from in `source`, with the code citation.

## Step 5. List the parts from the lifecycle (*Assigning* Step 6; *Rules*, Rules 0 and 2)

Every part named in `carried_by` or `needs` gets one `element` row in `subjects.csv`. Nothing else does.

- **Component or external dependency** is membership of the delivering application (Step 1): `level`
  `component` if it is part of it, `external dependency` if the application only calls, waits on or fails over to
  it. Not the company boundary, and not whether it is open source.
- **Application component or system component** is its layer, in `band`. Services, workers, front ends and AI
  agents are application components: `band` `application`. **Databases, caches, message brokers, search
  indexes, file stores, hosts and runtimes, and platform services are system components: `band` `technology`**, even when the application owns
  them. A system component is measured with its kind's set at the technology layer, never as an application
  component. `part_kind` from `method/part-kinds.csv` decides the set; an AI agent is a component with
  `part_kind` `LLM agent`.
- **A part with no step it performs or supports is set aside**, in `set-aside.csv` with kind `out of scope part`
  and the evidence that named it: monitoring, platform tooling, a service no move uses. It is not deleted and not
  left out silently.
- A job that handles many cases per run (a polling worker, a nightly batch) is a component; its runs are its own
  measure, shown under the cases it failed to move.
- `carries_case_id` on every part the case passes through: `yes:`, `partly:` or `no:`, with where it is carried
  or lost (*Rules*, Rule 2).
- A front end served from inside another deployable is still its own component; say where it is deployed in
  `source`.
- A person who carries out a move: a `person` row, no level. It is the method's set-aside role, bound to its step.
- `application_id`: the name the component is registered under in the organisation's configuration database, from that
  record; blank where no source states one. `repository`: the code repository it is built from, from its build or
  deployment definition, with the path inside it where one repository builds several components; `not built here:`
  and the image for a component run from someone else's image.
- `owner` and `responder`: from a source that states them, with the date it was true; otherwise inferred from what
  the sources show (who builds and deploys the part) and written `proposed:` with that basis.

## Step 6. Record who carries out each step

For every step, in `participation.csv`, from the lifecycle rows it came from: each part in `carried_by`
**performs** it; each part in `needs` **supports** it (the step blocks or goes wrong without it, including a
database constraint that enforces the step's rule). The part that carries the move out of a stage performs that
stage's last step. Every part in `carried_by` performs; none leads. The generated outputs name all of them, so the
part that changes the case's state and the part that decides (a stock checker, a payment service) are both shown. `records` (only reads or writes the step's trace) may be added for a part that also performs
or supports some step; a part whose only involvement is `records` is set aside (Step 5). Write the activity in
a few words with the file and line in brackets. Name the `operation` that does the step: the agent tool, HTTP route or message handler
the part offers, read from its declaration (the tool's name, the route's method and path). Where the cited line
is not itself a declaration (a status value, a shared service function), follow the move's `travels_by` to what the
caller invokes. The operation is what a caller calls, not the code structure behind it, so it survives a refactor. A part that shows the step's result to the party performs the
step whose outcome is that the party sees it.

Then add an `interaction` row (`kind` relationship) in `subjects.csv` for each hop in `travels_by`: `from_id`,
`to_id`, and the steps it happens within in `step_hint`. Where the code shows which of the calling part's operations
make the call (the route or tool whose handler calls it), name them in `operation`, as `participation.csv` names
them, and cite the line; leave it blank where the call is made once for a session or a connection. `band` `application` between components, `technology`
for a part's call to the store or broker it runs on. A message published through a broker is two hops: the
publisher to the broker, the broker to the consumer. Number the hops of one step in `sequence` in the order they
happen, only for calls made once, one after another, on one way. Leave `sequence` blank, and say why in the
citation, for a call repeated per item, made in parallel, not waited for, or made only on one branch.

**How far to go into an outside service** depends on what you can get for it: nothing beyond its address, it
stays one external dependency seen from the calling side; its code or documents, add the parts your calls reach
as `external dependency` rows with `part_of` set to the service (one level only); its owner has a map, put the
address in `map_link`.

## Step 7. Describe each AI agent as its own system

For each `LLM agent` component, add a block to `agent-system.csv`. If the capability has none, leave it with its
header only and write a `how-made.csv` row naming where you looked.

1. **The run:** one decision for one case, or one request answered. Name the business steps it serves.
2. **Its steps:** what one run does (take the request, decide the next move, call a tool, retrieve, write the
   answer, check the answer).
3. **Its parts:** the sequencing code; the decider (the model, its prompt and its rules); its tools; what it
   retrieves from; the checks that stop an answer outside policy. Link each to the subject ids that carry it. A
   part looked for and not found gets a row with a blank `subject_id`, and `what_it_is` says where you looked.
4. **Its dependencies:** the model provider and the systems its tools call. Fill `uses` on each part.

An agent's conversation is a flow of its own only when it is one case's path the business would name, with its
own start and end; otherwise the parts it uses carry steps of an existing flow, recorded as participation rows
(Step 6) like any other part's.

## Step 8. Name the capability, twice (*Assigning* Steps 2 and 7)

1. **From the walk:** what the whole path is for, what the business is thereby able to do, named apart from how
   it is built. The narrowest ability this flow delivers.
2. **From the sources, in a pass that has not seen the walk:** what the documents say the organisation is able
   to do (a separate session or subagent given only the documents).

Write `capabilities.csv`: one row per capability, with both routes in `basis`. If they agree, say both
produced it. If they disagree, keep both rows and say so; do not smooth them into one. A capability the sources
name that the walk does not deliver is kept, delivered by no flow. Fill `flows.csv` → `delivers`.

If an AI agent serves several flows, the register covers the lowest capability that holds all of them. List the
other flows the capability carries in `flows.csv`; each is its own frame and walk, and a flow not yet walked has
no stages.

## Step 9. Propose the measures, question first (*Rules*, the form and Rule 1)

This step proposes **candidate** measures: what could show whether the capability works. It does not choose which
are wanted, and it sets no targets or thresholds. Choosing measures and making them service level indicators with
objectives is done later, by people. The candidates are accounted for with three mechanisms adapted from a service onboarding practice, whose question set is published in the same collection as this
kit (`packages/observability-practice/the-instrument-sud-v2.yaml`), so that a thin
stage or an unmeasured agent step is caught rather than left unnoticed.

Work down the levels, asking the question first and then naming the measure:

1. **The flow** (its case subject, `flow` set, `step` and `stage` blank): cases started, finished, still open;
   finished on time and right; still open past the promise.
2. **Each stage** (its case subject, `stage` set): cases in the stage now, the age of the oldest, the time to get
   through, and cases past the stage's promise. Counted from the case's state changes at the stage's entry and
   exit. A stage measure counts cases, never requests. Mark each in `receipt_question` with the candidates it
   answers (`in the stage`, `oldest's age`, `time through`, `past the promise`); one measure may answer two.
3. **Each step that matters** (one event per case): did it happen for this case, and was its outcome right. The
   steps that matter are each stage's **exits**, read from its moves in `lifecycle.csv` (a step whose move takes
   the case out of the stage, by the main move and by every alternative or exception ending, never the step that
   happens to be listed last), the flow's first step, every step with a step-impact row, and every step an AI
   agent serves (its participation rows, and its `agent-system.csv` run and operations). Mark each step measure in
   `receipt_question` with the question it answers.
4. **Each part, its kind's set** (`method/part-kinds.csv`), at its layer: `application` for an application
   component, `technology` for a system component. An external dependency is asked the same sets from the
   calling side. An application component is asked **per operation** (mechanism 3). Every component that takes part
   in a step is asked, whatever its involvement: a store whose only rows are `records` (a basket store a restart
   empties) is asked its set like one that performs. An AI agent is read at two grains (below): its judgment at
   each **decision point**, and its operation at its **runs**. **An agent whose own component also serves a route**
   (the agent is the deployable, and a caller reaches it by an HTTP route) is asked both: the agent questions, and
   the application set for each route on its rows, keyed like any operation (`S06 POST /chatclient`). Hosting an
   agent does not take the component's route out of the application layer. The receipt tells a route from a tool
   by how `operation` is written, a method and a path (`POST /chatclient`) or `route` and a pattern; a handler of
   another kind on an agent's row (a message consumer, a gRPC method) is not recognised yet, so write its
   application candidate or gap by hand and say so in `why`.

### The agentic layer: the decision point and the run

**Class each tool first.** On every participation row of an agent, write `decision_point`. A tool call is a
decision point, `yes:`, when the agent chooses a value that becomes the case's outcome or a person's basis for
deciding it: a recommendation, a decision type, a condition's text, the inputs to a risk computation. A call that
only records what a person stated or asked for is an action, `no:`: entering the borrower's details, acknowledging
a disclosure. Class it by reading what the tool's arguments carry, and cite the signature. A tool that computes by
fixed rules is a decision point only through the arguments the agent chose to pass it; say which. One agent's tool
is classed one way on every row. The check fails on an agent row not classed, and on a tool classed both ways.

**A tool whose class depends on the conversation is a decision point.** The same call can record an item the
person named, or choose one the person only described (an add-to-basket call given a product's name against one
given "something warm for winter"; an add-pet call with the owner the person named against the owner the model
picked from a list). One class per row stays: write `yes:`, and the reason says **when** the call carries the
agent's choice. Where telemetry can tell the two kinds of call apart, the candidates count only the judged calls,
and say how in `counted_how`. Where it cannot, the reason says so, and every call is counted. The receipt cannot
split the two; the reason is where the difference is kept.

**Then class each reply.** The agent's reply to a person is a decision point when the person relies on it: it
reports or explains a result, such as a recommendation, a risk assessment or a check's outcome.
Its operation is the agent's turn, not a tool, so a tool computed by fixed rules (classed `no:`) can still be
reported by a reply that is a decision point. On the agent's row for that step, write `reply_decision_point`:
`yes:` where the person relies on the reply, `no:` where it only confirms what the person asked, asks for more, or
replies to no person at that step, and why, citing the prompt or the code that hands the tool's result to the
model. The check fails on an agent row whose reply is not classed. Each reply classed `yes:` is a decision point keyed, like a tool's, by the agent
and the operation whose result it reports, element `S04 reply to uw_render_decision`, listing every step it spans: a
judge sampling the agent's replies after that operation is one measure whichever of those steps the case is in. Its
candidates name `reply` and the operation in `operation` (`reply; uw_render_decision`). A row naming no tool keys its
reply by its step (`S04 reply at step 17`), with `reply` in `operation` and the step in `step`. **An agent with no
tools** still has its reply as a decision point, keyed by the agent and the route that runs it: element
`S03 reply on POST /`, candidates naming `reply; POST /`. The receipt writes `reply on` where the row's operation
is a route and `reply to` where it is a tool.

**A model output a later call relies on is its own decision point.** Where the agent's chain writes something
with one model call and a later call decides from it (a description of a room written from a photo, then fed to
the call that chooses products), that first output is a judgment no tool or reply holds. Class it on the operation row
of `agent-system.csv` that makes the call, in `decision_point`: `yes:` and why, citing the line that feeds it on.
It is keyed by the agent and its place in the chain, element `S03 AS2`, and asked the same questions; its
candidates name the step's id in `operation` (`AS2`). Only a step row classed `yes:` is asked. Do not class a step
whose output a tool's or a reply's decision point already holds: the model's choice of a tool's arguments is that
tool's decision point. Grounding comes first:
does the reply say what the tool returned (a judge sampling replies against the tool's output, NIST AI 600-1
MS-2.5-003). Correctness, traceability and drift take the forms below. Correctness comes from the person's
agreement with the reply itself, never from a record of something else, such as agreement with a rule's result.
Where nothing records that agreement, propose a labelled set or a judge, or write a gap. Traceability comes from
the run and tool-call record: a record of the turn that carries the case, holding the tool's result beside the
reply.

**At each decision point** (`yes:`), the agent questions of grain `decision point` in
`method/agent-questions.csv`. Write each candidate for that tool, naming it in `operation`, from what that tool
writes, in these forms:

- **correctness**, from the person's agreement with or override of that decision, where a record keeps it: NIST AI
  600-1, *Generative Artificial Intelligence Profile*, MS-4.2-004, *"Monitor and document instances where human
  operators … override the GAI's decisions"* (nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf). Where no record
  keeps it, a judge or a labelled set re-run per release, or a gap.
- **grounding**, from checking the decision against the inputs it claims to rest on: the values the tool wrote,
  recomputed from the case's own records (NIST AI 600-1 MS-2.5-003, sources checked in ongoing monitoring).
- **traceability**, from a run and tool-call record that carries the case: which decider, which inputs, which
  case (the OpenTelemetry GenAI `invoke_agent` and `execute_tool` spans carry the agent's id and version, the
  conversation and the tool; OpenTelemetry semantic conventions for generative AI, `docs/gen-ai/gen-ai-agent-spans.md`
  and `gen-ai-spans.md`, status Development). A record keyed only by session does not carry the case: say so.
- **drift**, from that decision point's inputs and outputs compared with a validated baseline, and the agent's
  configuration (model, prompt, rules) compared with the one vetted (NIST AI 100-1, MEASURE 2.4, functionality and
  behaviour monitored in production).

A measure that names no tool answers for none of its decision points: the grain is the judgment. A measure listing
every tool the agent has is not a decision-point candidate; write one per tool, against what that tool records.

**At the run**, every agent, whatever its tools are classed: the agent question of grain `run`, `operations`. One
run is one invocation of the agent: a request in, the model and tool calls it makes, an answer out. Each of five
metrics is its own element, covered by an `agentic` measure of the agent with `agent_question` `operations` marked
for it in `receipt_question`, or gapped:

| Run metric | The field's form (OpenTelemetry GenAI semantic conventions, repository `open-telemetry/semantic-conventions-genai`, status Development: `docs/gen-ai/gen-ai-metrics.md`, `gen-ai-token-metrics.md`, `gen-ai-agent-spans.md`) |
|---|---|
| `run duration` | `gen_ai.invoke_agent.duration` per run; a model call's duration (`gen_ai.client.inference.duration`) is not a run's |
| `failed tool calls` | `execute_tool` spans and calls per run, with `error.type` set |
| `tokens` | input and output token usage per run (`gen-ai-token-metrics.md`) |
| `refusals` | a run ended by a guardrail or the model declining: the finish reason, a shield's block |
| `fallbacks to a person` | a run handed to a person, or ended telling the person to try later (NIST AI 600-1 MG-3.2-006: monitoring that triggers human intervention) |

These are recorded at the agentic layer of the agent (`layer` `agentic`) as operational evidence, not judgments of whether it decided well. **Escalation and
policy scope** stay `candidate` and are not asked; where an application emits a refusal per tool call by its role
or authorisation check, propose one `policy scope` candidate from it.

**A measure emitted but counting the wrong thing gets `defect`**: one line saying what it counts wrong, with the
citation (a per-tool duration that is the batch's time split evenly; a label that never varies; a counter nothing
increments; a summary serving generated data while its source is off). `source_ref` keeps only the emitting line.
`defect` is written only where `exists` is `yes`: a proposed measure is not yet counting anything.

`exists` is `yes` only where the system already emits it: cite the emitting line, or the setting that switches on
a framework's built-in metric, in `source_ref`, and write `declared` in `source`. A log line counts, if it is
written once per case: read where it is written and what triggers it. Everything else is `exists` `no`, `source`
`proposed`.

**A measure can be emitted and never collected.** On every measure whose `exists` is `yes`, write `watched`:
`yes` where operations monitoring collects it, `in the app only` where an application screen shows it and nothing
collects it, `no` where nothing does (a metrics endpoint no scrape configuration lists), or `unknown`; and
`watched_source`, the collection configuration or screen read, with its citation. Watched is never settled by reading the
emitting code. Where no collection configuration is within reach, write `unknown` and `no inventory reachable`; only
`unknown` may rest on that. The page shows `watched` in an opened measure. Business measures count cases. No thresholds or targets unless a document or person states them, and
then only as that source states them.

### The three mechanisms

**1. The coverage receipt**. Every element
of every start-set below is either **covered** by at least one candidate in `measures.csv` or **gapped**: a row in
`measure-gaps.csv` saying why no candidate is proposed, with its source. There is no third state. A gap is not a
measure, so it is never a `measures.csv` row with the measure left blank. `flow_outputs.py --check` recomputes the
receipt from the register for the whole flow, whichever stage it is run for, and fails on every element that is
neither covered nor gapped. A gap row with no `why` or no `source` does not count.

| Start-set | Element (`element` in measure-gaps.csv) | Question (`question`) | Covered by a candidate that is |
|---|---|---|---|
| The flow | its id (`F1`) | `the promise` | of the flow (stage and step blank), counted on cases, `business health`, form `cycle time` or `completion rate` |
| Every stage | its id (`ST2`) | `in the stage` | of the stage, counted on cases, `business health`, form `backlog`, marked `in the stage` in `receipt_question`: the cases in it now |
| | | `oldest's age` | the same, marked `oldest's age`: the age of the oldest case in it |
| | | `time through` | of the stage, counted on cases, `business health`, form `cycle time` or `completion rate`, marked `time through`: the time through, set against the promise |
| | | `past the promise` | of the stage, counted on cases, `business health` or `business impact`, form `backlog`, marked `past the promise`: the cases in it older than its promise |
| Every step that matters (item 3) | its step id (`7`) | `did it happen` | of the step, on its case subject, counted on cases, `business health` or `business impact`, with `did it happen` in `receipt_question` |
| | | `was its outcome right` | the same, with `was its outcome right` in `receipt_question` |
| Every operation (each `operation` in `participation.csv` of an application component that takes part in a step, whatever its involvement) | the component's id and the operation (`S03 PATCH /api/applications/{id}`) | `application` | of the component, `application`, with the operation, written as participation writes it, in `operation` |
| A component whose row names no operation | its id (`S12`) | `application` | of the component, `application` |
| Every route an agent's own component serves (an `operation` on an agent's row written as a route) | the agent's id and the route (`S06 POST /chatclient`) | `application` | of the agent's component, `application`, with the route in `operation` |
| Every system component (`band` `technology`) that takes part in a step, whatever its involvement | its id (`S08`) | `technology` | of the component, `technology` |
| Every decision point: an agent with a tool its participation rows class `yes:` in `decision_point` (the rows of one tool, at several steps, are one decision point) | the agent's id and the tool (`S04 uw_render_decision`); for a row naming no tool, `S04 at step 15` | each agent question in `method/agent-questions.csv` whose `status` is `provisional` and `grain` is `decision point` | of the agent, `agentic`, with that `agent_question` and the tool in `operation` (for a row naming no tool, that `step`) |
| Every reply relied on: an agent row classed `yes:` in `reply_decision_point`, one per agent and operation | the agent's id, `reply to` and the tool (`S04 reply to uw_render_decision`), or `reply on` and the route for an agent with no tool (`S03 reply on POST /`); a row naming no operation, `reply at step` and the step | the same agent questions | of the agent, `agentic`, with that `agent_question`, `reply` and the operation in `operation` (a row naming no operation: `reply` and that `step`) |
| Every model output a later call relies on: an agent's operation in `agent-system.csv` classed `yes:` in `decision_point` | the agent's id and the operation's id (`S03 AS2`) | the same agent questions | of the agent, `agentic`, with that `agent_question` and the operation's id in `operation` |
| Every agent that performs or supports a step, or whose `agent-system.csv` run serves one | its id (`S04`) | each run metric: `run duration`, `failed tool calls`, `tokens`, `refusals`, `fallbacks to a person` | of the agent, `agentic`, answering the agent question of grain `run` (`operations`), with the metric in `receipt_question` |

An agent question marked `candidate` is not asked until the agentic layer settles it. A tool classed `no:` is not a
decision point, and its agent is still asked at the run.

**2. The expectation chain** (that question set, q15b). Every
expectation has a business health candidate that would show it is met. The question set gives the reason: without it,
candidates default to *whatever the service's API behavior suggests rather than what stakeholders need to know*.
Here the expectations are the flow's promise, each stage's promise, and each step's `right_outcome`, so the
receipt asks `the promise` of the flow and `time through` and `past the promise` of every stage, and **"was its outcome right" is derived from the
step's `right_outcome`**: read that column, and name what one case would show if it did not hold (the state, the
values it should carry). Name the measure for what it counts (below). Where nothing records the values the right
outcome names, the gap says which record is missing.

**3. Signals per operation** (that question set, q40 to q43). Where
telemetry can tell a component's operations apart (a metric labelled by route or tool name, a log line naming the
handler), each operation gets its own application candidate, naming it in `operation`. Where it cannot, or one
candidate already answers for several, write the gap for each operation it folds in: `folded into M51:` and why.

**Kept from the kit, not from that practice:** the stage level, and the stage's exits read from its moves in place of a
"last step". **Not adopted:** that practice's targets, thresholds and authority, and its per-signal standing. Those
belong to choosing measures, which people do later. Nothing here is fixed: where the procedure misses an element
or asks a useless question, change it.

**Name a measure for what it counts.** A count of wrong outcomes is "Orders confirmed with an unknown item", never
"Stock confirmed rightly": a reader takes a rising count of a thing named "rightly" as good news.

**Propose the stage's measures for alerting, and say what each rests on.** An alert goes where the party in
`expectation_of` would see the stage's expectation broken. Mark each measure you propose for alerting in `alert`,
as `yes:` and its basis: the expectation it guards. Only a measure of the stage, counted on cases, is proposed. The
measures, the alerts and the runbook are generated from that column, so they cannot disagree. Whether an alert
pages a person, opens a ticket or shows on a dashboard is the operators' decision, not the register's.

A stage loses cases in three ways. Consider each, and propose a measure for each that would break the expectation:

- **Cases wait too long**: the cases in the stage past its promise. Where a move out of a park stops, they pile
  up here.
- **Cases leave wrongly**: cases leaving by an alternative or exception ending the expectation does not want (failed
  back, cancelled because a part failed), or left stranded, counted against the cases that entered. A stage whose
  work never waits loses cases mostly this way. Say which record counts one event per case at those exits; if none
  does, the measure is `proposed` and names the record it needs. **The basis names the moves (`L..`) the cases
  leave by**: the alert's runbook entry works the tests of the state those moves leave from. An ending the party wants
  (their own cancellation, a rule's refusal) is not a loss.
- **Cases leave with a wrong outcome**: the main ending, reached with the wrong values (a stale read, a wrong
  decision from a rules engine or a model). The step measures of item 3, "was its outcome right", count it. Propose
  one for alerting where a record shows the wrong outcome per case.

A measure not proposed for alerting is still read by the runbook's tests. The check warns where the stage's moves
show a kind of loss no proposed measure counts. Propose one, or say in the basis why not: a warning whose reason the
basis gives stands, and does not stop the outputs being written. Only errors do.

## Step 10. Record what a failure costs (*Rules*, Rule 3)

For each lifecycle move whose `if_not` hurts the case, a `step-impact.csv` row on the step it belongs to: the
category from `method/impact.csv`, the unit counted in cases, and `recovery` copied from the lifecycle. A case
acknowledged to the party and then lost fits no recovery value: leave `recovery` blank and begin `note` with
`lost after acknowledgement:` and the evidence. In `case-attributes.csv`, what is at stake in one case.

## Step 11. The failure modes, the alerts and the runbook for a stage (`reference/runbook-model.md`, "How to write one")

For each stage an alert is wanted on. The alerts and the runbook are **generated**, never written: what you write
is the worksheet they are generated from.

1. **The expectation** is the stage's promise (Step 3), and the right outcome of each step that takes a case out of
   the stage. **The alerts** fire on the measures marked in `alert` (Step 9). **The runbook has one short entry per
   alert**, which that alert's runbook link points at, **and one shared section for the stage**: the stage on one
   page, what is at stake, every test written once with the alerts that use it, the causes the alerts share, and
   restore, close and escalate. What the generator puts in each entry, from what you write:
   - **What fired**: the measure and its basis.
   - **Its cases and window**: for a measure of cases waiting, the cases past the bound, read from when the oldest of
     them entered the stage (the count lags its cause by up to the bound); for a measure of cases leaving, the cases
     that left by the moves its basis names, read from when the earliest of them entered the stage.
   - **Opening checks**: open incident, maintenance window, what changed in that window; then whether the count is
     falling.
   - **Contain first**: from where the counted cases are now. Waiting cases need no hold. A case that left by the
     main ending with a wrong outcome is held where it is. More cases leaving by an alternative or exception move
     are stopped by everyone who can make that move: each person in its `carried_by`, and whoever can sign in to a
     web front end in its `carried_by` that no main move of the stage uses (a back-office screen with its own login).
     So put every role that can make the move in `carried_by`, each a person row in `subjects.csv`. A move marked
     `irreversible` is said to be so. Every `do not` remedy is named here.
   - **Its tests**: the failure modes of the states its cases are in or left from, except one whose `measures` reads
     another proposed alert's count and not this one's: that test lists the other alert's cases, so it is the other
     alert's own. Its own count's tests come first. Each line says what a match means (the mode's `failure`, its
     citations dropped) and its ending; a match explains only the cases it lists, and the walk goes on for the rest.
     A test whose evidence lists no cases (a match in a log or a metric) explains no case by itself: the walk notes
     it, if the match falls inside the look-back, and goes on; a case no later test explains takes the ending of every
     test noted for it, each named in the hand-over, and where those endings differ the responder escalates rather
     than restores. For an alert that counts cases that already left wrongly, a falling count means only that no new
     cases are arriving: the recovering check never closes it.
   - **Linked tests**: where a mode's `failure` names another mode (`FM..`), it is linked to that mode; where it
     names a move (`L..`), it is linked to the modes that stop that move (those with `recovery` set). A link runs
     one way, from the mode whose text names the other, so name the cause a matching test should lead on to.
     **Write an `FM..` or `L..` id in `failure` only to make that link**; anywhere else, say the move or mode in
     words ("the booking record stays"), or the runbook sends the responder to a test that has nothing to do with it. An entry's
     linked tests are the ones its own tests link that it does not already work; a matching test's line says to
     run them too, on the same cases, and the shared section lists the same links, alert by alert. Each test's
     **Used by** names the alerts whose entries work it and those that link it. Name the other mode or move in
     `failure` where one cause leads to another, and write each test so it can be read on the cases of every alert
     that runs or links it: a linked test meets cases that may have left the stage.
   - **Escalation** goes to the owner of the failing part, the mode's `part`, as `subjects.csv` → `owner` records
     it; where that is blank, the runbook says *not in the map yet*. A party a remedy also escalates to
     (`remedies.csv` → `also_escalate_to`) gets its own row in the escalation table, *not in the map yet* where the
     register records no owner for it.
2. **List the failure modes, hop by hop (FMEA)**, in `failure-modes.csv`. For each move of the stage, take each hop
   kind in its `travels_by` and each mode `method/hop-failures.csv` lists for that kind; then each part in its
   `needs`, with the catalogue's `needs` modes; then make sure each part in its `carried_by` has a row. For each
   one, read the code: what happens to the case here, and how it recovers. Where the design rules a mode out, write
   the row with ending `not possible` and the citation. A mode the catalogue lacks is `other`. One row may serve
   several moves where the part, the test and the ending are the same. **A mode is a live test only where what it
   does to the case is something a measure the stage proposes for alerting counts.** Otherwise its ending is `not possible`,
   its `failure` begins `not possible here: as a cause of` what the stage's alerts count, and names the measure that
   does count it (a wrong outcome is counted by its step's measure, Step 9).
3. **Give each mode a test that tells it apart** from the others a responder meets in the same state: the exact
   query (table and columns as the code defines them), the log text as the code writes it, or the command. On a
   state column, `seen` lists every value the code can leave other than the healthy one. Name the measures it reads,
   adding them in Step 9 if they are missing. **A signal is only evidence where it is written:** a cancellation
   or deadline started by a caller shows at the caller, not in the callee's logs; a call made outside the request's
   trace context is not in its trace. Where a harmless cause gives the same signal as a fault (a party giving up
   looks like a slow part), the test says how to tell them apart, or the harmless ending is not used. **A test
   reads evidence that is still there when the responder arrives:** a search over the alert's window (the entry
   states it, and the runbook tells the responder to put it wherever a command asks for a time span in angle
   brackets, such as `--since=<window>`), by case id where the evidence carries one, never a tail of the last
   lines; and where a log may have
   rolled over, the test names the durable record (a row, a queue) that outlives it. Write the test so it can be
   read on the alert's own cases: a query that lists every case in a state is read only for the cases the alert
   counts. Where a test must see cases wherever they are now (a linked test meets cases that have left the stage),
   filter on `<case ids>`: the runbook tells the responder to put there the ids of the cases being worked.
   **A test is written once**: it serves every alert whose entry runs it.
   **A command cites the deployed value, never a code default**: the port the deployed process listens on, the log
   line as the deployed logging configuration emits it (a traceback's last line, not a window of lines after the
   message), the name the deployment gives a resource. Where a configuration switch changes the value, write the
   value for the configuration `about.csv` names and state the switch beside it.
   **Before a test goes into a runbook, check it against one known case**: a seeded or demo row, or a reproduced
   failure, whose answer is known. The query lists that case, the grep prints that line, the command shows that
   state; and the healthy case gives the expected result. A test that matches every instance of a wider event (every
   failed turn, every restart) is not its mode's test: make it specific, or say in `seen` what tells it apart.
   Record each check in `how-made.csv`.
4. **Give each mode its ending**, and each `restore` or `stranded` mode its remedy in `remedies.csv`. **A mode that
   leaves its case stranded ends in `restore` or `cannot restore`**, even when the refusal that stranded it is the
   application working as designed (a balance that may not go below zero): the responder's job is the stranded case,
   not the refusal, and the check holds you to it. For a stranded
   case, look for a re-drive **outside the code as well as in it**: an action that puts the case back into a state
   the application moves on from by itself (a status reset the poller re-sends), cited to the code that makes it
   safe. If there is none, write a `none exists` remedy saying so and what to record. Write the actions that look
   like fixes and are not as `do not`. **A remedy is written once for every alert whose tests end at it**, so its
   text names no alert and no alert's query: say what to record in words that hold for any of them. It names no
   runbook section either (write `Escalate`; the runbook points it at its escalation section); it may name another
   remedy (`R..`), and the runbook then writes that one too. Escalation goes to the failing part's owner; a party
   the responder must also tell (the owner of a regulation, say) goes in `also_escalate_to`, never in the action's
   prose.
5. **Describe one configuration.** A test and a remedy are written for the configuration `about.csv` names. Where the
   repository ships another that changes the answer (a different store), say so in the test. Values are written as
   the store holds them: a status kept as a number is tested as that number, with its name beside it.
6. **Verify every claim against the code before anything is generated.** Re-open each `file:line` the register
   cites, for the stage's rows and the frame (flows, stages, steps, participation, lifecycle, failure modes,
   remedies, measures, step impact), and read the line itself, not a listing of several files. For each: does the
   line say what the row claims, and does the behaviour hold when you follow the call (a retry wrapped around the
   call that fails, a state the code really writes, a log text exactly as written, a remedy the code really
   lacks, a restore that really reaches the fault: adding an instance helps only if callers spread their calls
   over instances)? Correct each row that fails, and write a `how-made.csv` row for the pass: how many claims were read and
   how many were corrected. This pass is the drafter's own; someone who did not draft the register still checks a sample of the citations afterwards (USE.md, "Before you take it to anyone").
7. **Generate** the slice, the measures, the alerts and the runbook:

```
python "<skill>/flow_outputs.py" "<your-folder>" <flow> <stage> --out "<your-folder>/stage-<stage>"
```

It checks first, and writes `ALERT.md` and `RUNBOOK.md` only when the check passes: every hop, need and carrier of
every move covered; every mode's part in its move's lifecycle row; every test's measures in `measures.csv`; no two
modes in one state a responder cannot tell apart; a remedy for every restore and every stranded case; exactly the
measures marked in `alert` proposed for alerting. A failure is fixed in the step that produced it. **Never edit a generated file.**
`ALERT.md` gives each alert its runbook link, to its own entry in `RUNBOOK.md`.

## Step 12. Check and draw

Before drawing, run these against the register. Each one is a rule from above that a register can break:

- `flows.csv` → `starts_at` cites the line that creates the case's record, and the first lifecycle row's
  `from_state` is `(none)`.
- Every stage's `entry` is the previous stage's `exit` or the starting event (stage 1), its `exit` is the next
  stage's `entry` or an ending, and its `source` cites what each cut rests on or is `proposed:`.
- Every exit of every stage, main and alternative, has a step whose lifecycle `to_state` is that exit.
- Every element of the measure step's receipt (Step 9) is covered by a candidate in `measures.csv` or gapped in
  `measure-gaps.csv` with its reason and source. `flow_outputs.py --check` prints the receipt's count and an error
  for each element that is neither.
- Every `subjects.csv` row of `part_kind` database, cache, message broker, search index, file store, host or
  runtime, or platform service has `band` `technology`.
- Every component and external dependency has at least one `performs` or `supports` row; every other part named
  in the sources is in `set-aside.csv`.
- Every part in `lifecycle.csv` `carried_by` and `needs` is a subject id in `subjects.csv`.

```
python "<skill>/capability_views.py" "<your-folder>" --check
python "<skill>/one_canvas.py" "<your-folder>" "<your-folder>/views.html"
python "<skill>/flow_outputs.py" "<your-folder>" <flow> <stage> --check
```

`<skill>` is the folder `capability_views.py` is in. `one_canvas.py` writes the page, `how-this-map-was-made.html` beside it, and copies each stage's `RUNBOOK.html` and `ALERT.html` into `stage-<id>/` beside it. `--check` lists every id that points
nowhere, every value outside the closed lists, and every row with no citation. A failure in any check is fixed in
the step that produced it, and if the step's rule allowed it, in this procedure. A warning is not a failure: read
it, and either act on it or leave the reason in the row it names.

## When something new arrives

A map is updated, not rebuilt. When a source the register has not read turns up, make a new pass:

1. Add the source to `sources.csv` with the next pass number.
2. Read it against the lifecycle first: a state or move it shows that the lifecycle lacks is added there, and the
   stages, steps, parts and measures are re-derived from the changed rows by Steps 3 to 10. Where it names an
   owner, a responder, a promise or a volume, fill the blank, citing it.
3. Never delete a row because the new source is silent about it, and never overwrite one source with another.
   Where they disagree, keep the existing row and put both accounts in its citation cell, each with its citation,
   and write the disagreement in this pass's `how-made.csv` `note`: it is a finding for a person to settle.
4. Cite the new source in every row you add or change, add `how-made.csv` rows for the pass, and check and draw
   again.

## What good enough looks like

- The frame is declared, and the flow starts where the case is created.
- Every stage boundary cites what it rests on, and every stage ends with the step that moves the case out.
- Every part is tied to a step, and sits at its layer. Every part not tied to one is set aside, in the open.
- Owners, responders, volumes and stated promises are blank or proposed unless someone stated them. That is a
  finding the views make visible, not a gap in your work.
