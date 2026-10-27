# The register: one capability, described in tables

A register describes one business capability as it is carried out: its flows, their stages and steps, the parts
that carry each step, what those parts rely on, any AI agent among them, the measures that could show whether it
works, and what a failure costs, counted in cases. It is a design-time description. It holds no live values.

Copy this folder, fill it by following `../FILL-STEPS.md`, and draw it with `python ../one_canvas.py <folder> <folder>/views.html`.

`RUN.md` is not a table. It is the run's record: what the run will produce, and each phase's status, with the
files that prove it done or the reason it is blocked. `python ../run_status.py <folder>` says whether the run is done.

## Rules that apply to every table

- **Every row says where it came from.** Put a citation in `source`, `source_ref` or `basis`: a file and line
  (`src/loans/ApplicationService.java:42`), a document and section, or a person asked, with role and date
  (`asked: underwriting team lead, 2026-10-07`). If a descriptive cell already cites its source in brackets, that counts.
  `--check` warns, in the tables it reads for drawing (not `about`, `how-made`, `sources`, `lifecycle`,
  `failure-modes`, `remedies` or `set-aside`), about a row whose `source`, `source_ref`, `basis` and `activity` are all empty and whose cells
  hold none of these: a file name with a line (`Order.cs:57`), `asked:`, `§`, or a web address.
- **Not found is not absent.** If you looked for something and did not find it, leave the cell blank or leave the
  row out. Never write "none" or "no owner" as a value. The views draw a blank as *not assessed*.
- **Proposed is labelled.** A value you drafted with no source to confirm it starts with `proposed:`.
- **Ids are short and stable** (`C1`, `F1`, `ST1`, `S01`). An expectation's id is lowercase (`e1`, `e2`). Fields
  that list ids separate them with `;`.
- Columns are read by name, and the tables below define them: the template's CSV files carry the same headers.
  `--check` errors on a table that lacks a column defined here, unless its description begins *Optional*, and
  warns about a column defined nowhere here, which the programs ignore. A missing table file is not checked.
- **A column with a closed list of values declares it** with a `One of:` list ending its description: the values in
  backticks, or a `../method/` file whose first column holds them. `--check` warns on a value outside the list; a
  blank cell is always allowed, and in a `;` separated column each value is checked.

## What a finding in a register changes

The checks guard what this definition declares: the tables, their columns, the values a column allows, the ids
one table names in another, and the questions each view must answer. They guard consistency, never whether the
register is true to the code; the walk of the sources does that. So **a finding in a register adds no check.** It
leads to one of two things:

- **A declaration that was missing.** The finding shows a column, a value or a relationship the model already
  defines that this file does not declare. The declaration is added here, and the check reads it from here.
- **A content judgment.** The finding is about what was written, not its shape. It becomes wording in FILL-STEPS,
  and review catches it.

The list of checks grows only when this definition grows. Every check is listed in `../CHECKS.md`, one row each,
and every check in the code has a row there.

## The tables

### about.csv: one row

| Column | What goes in it |
|---|---|
| system | The name the business uses for the system or estate that carries the capability |
| what_it_is | Two or three sentences: what the system does, for whom |
| modelled_from | How this register was made: from what, by what method, and what is proposed |
| sources_examined | Everything you read or asked, so a reader knows what "not assessed" covers |
| as_of | The date the register describes |

### lifecycle.csv: the case's states and the moves between them

Built first (FILL-STEPS Step 2). One row per move: the act that takes one case from one state to the next.
Stages, steps, parts, measures and the runbook are read off it.

| Column | What goes in it |
|---|---|
| move_id | `L01`, `L02`, ... in the order a case meets them on the main path, then alternatives |
| flow | The flow id |
| from_state | The state the case is in before the move, as the system records it (cited), or `implicit: ` and the state in words. `(none)` for the move that creates the case |
| from_kind | `park` (nothing is progressing the case; the next move needs a trigger not already in motion) or `in act` (the act is still working: a message on its way to a consumer that will act on it, a call out and back). One of: `park`, `in act`. |
| park_because | For a park: what the next move waits on: `timer`, `schedule`, `person`, `outside party`, `customer` |
| move | The act, in the case's terms, never naming its performer |
| to_state | The state the case is in after the move |
| path | `main`, `alternative` (another ending the design allows) or `exception`. One of: `main`, `alternative`, `exception`. |
| order_note | Blank, `parallel with <move_id>` or `loops to <state>` |
| travels_by | How the move reaches the case: `in-process`, `call`, `message` (name the event and broker), `outbox`, `poll`, `timer`, `person`; several hops in order, `;` separated |
| carried_by | The parts that carry the act out, by name or subject id |
| started_by | Optional. On a move that can happen at any time while the case is in a stage (a cancel, a withdrawal): who starts it, in words, cited: the flow's customer, a role, an outside party, `timer`, or `the software`. The stage's drawing names it, and draws a message from the customer only where this names the customer |
| needs | The stores, brokers and outside services the move cannot complete without |
| timing | What the code assumes about time for this move (grace period, poll interval, timeout, retries), cited |
| if_not | What happens to the case if the move does not happen, cited |
| recovery | `moves on`, `stranded`, `not created`, or blank (as in step-impact.csv) |
| irreversible | `yes` where the move cannot be undone, else blank |
| source | Citation |

### set-aside.csv: what was looked at and is not part of this flow

A thing a source names that is not a level of this flow is recorded here, not left out, so a reader can tell
what was read and excluded from what was never opened.

| Column | What goes in it |
|---|---|
| item | What it is, by the name the source uses |
| kind | `other flow` (work before the case exists, or another case's path), `out of scope part` (a part that performs or supports no step of this flow), `role`, `rule or policy`, `target`, `form or document`, `team`, `other` |
| attaches_to | The step, stage or flow it relates to, if any |
| why | Why it is set aside |
| source | Citation |

### capabilities.csv: the capability tree, any depth

| Column | What goes in it |
|---|---|
| capability_id | `C1`, `C2`, ... |
| name | What the business is able to do, named apart from how it is built |
| parent | The capability it sits inside; blank for the root |
| basis | Why it is a capability and where the name came from |

### flows.csv: one row per intended flow

| Column | What goes in it |
|---|---|
| flow_id | `F1`, `F2`, ... |
| name | One case's path, named as the business would say it ("Originating a loan") |
| case | What one case is, and where it is recorded |
| starts_at, ends_at | The event that starts one case and the outcome that ends it |
| delivers | The capability ids this flow delivers, `;` separated. A flow can deliver several; a capability can be delivered by several flows |
| customer | The party the flow serves: its role name only; a citation for it goes in `source` |
| bound_in_code | Optional. Fill it only where the application's own code sets a timer, deadline or overdue rule for one case, end to end: `proposed: ` and the limit, cited to the code that sets it. Leave it empty otherwise, never `none assumed`: few applications set one, and an empty cell owes nothing, no gap and no question. A limit a document or a person states goes in `expectations.csv` → `objective`, never here; the parties' expectations are what the flow's card leads with. Where it is filled, the page shows it as "Time limit in the code" |
| case_identifier | Which field names one case, and where it is lost |
| source | Citation |

### stages.csv: ordered stretches of each flow

| Column | What goes in it |
|---|---|
| stage | `ST1`, `ST2`, ... unique across the register |
| flow | The flow id it belongs to |
| order | 1, 2, 3 within its flow |
| name | The stretch, as the business would name it |
| entry, exit | What is true when a case enters and leaves it |
| bound_in_code | Optional. Fill it only where the application's own code sets a timer, deadline or overdue rule for this stage: `proposed: ` and the limit, cited to the code that sets it. Leave it empty otherwise, never `none assumed`: few applications set one, and an empty cell owes nothing, no gap and no question. A limit a document or a person states, or one the business shows the party, goes in `expectations.csv` → `objective`, never here; the parties' expectations are the stage card's main content. Where it is filled, the page shows it as "Time limit in the code", and the receipt asks the stage `past the time limit` |
| arrivals_per_period | Cases arriving per period at this stage. The operators' measured value; `not stated: measured by the operators` until they give it |
| source | Citation |

### expectations.csv: whom the flow serves, and what each party counts on

FILL-STEPS Step 3a. One row per party per expectation, of the whole flow or of one stage: the flow's stakeholder
register. A party is someone the flow's outcome serves or binds: the customer named in `flows.csv`, a regulator, a
sponsor. A person who carries out a step is a party only where a document or a person states what they expect of
the flow. A measure names the expectations it is evidence of in `measures.csv` → `expectation`.

| Column | What goes in it |
|---|---|
| expectation_id | `e1`, `e2`, ... lowercase, unique across the register |
| flow | The flow id |
| stage | The stage id, or blank for an expectation of the whole flow |
| party | Who holds the expectation, by the role name the business uses. The customer is written exactly as `flows.csv` → `customer` writes it. `proposed: ` and the basis where no document or person names the party (a persona in the code, an authorisation role, a rule the code enforces) |
| expectation | What the party counts on, in the party's own words where a source has them, quoted and cited: a document, a person, text the system shows the party, or a rule the code enforces. Otherwise `proposed: ` and the expectation |
| satisfied_when | The satisfaction condition: what one case shows when the expectation is met (its state, the record written, the values it carries), testable on one case. `proposed: ` unless a document or a person states it, as for `right_outcome` |
| objective | A bound, only where a document or a person states one, including text the business shows the party ("1-2 weeks" on a status screen). Written as stated: two bounds shown stay two, never summed. A rule the code enforces counts only where the code names its authority. Never drafted: blank where nothing states one, and never `proposed:` |
| objective_source | Where `objective` is set: the citation of the statement, such as the line that shows the text to the party. For a rule the code enforces, the code line and the authority it names. Required when `objective` is set |
| source | Citation for the row. A party inferred from the rules the code enforces adds `only the obligations this code enforces were read` |

### steps.csv: business outcomes inside each stage

A step is one act inside a stage, with an outcome the business would recognise, that happened or did not. Write
it as the outcome ("The credit file is pulled"), never as the code that does it. Rows are read in file order
within each stage.

| Column | What goes in it |
|---|---|
| step | A number or short id, unique across the register |
| stage | The stage id it belongs to |
| name | The outcome |
| business_subject | The subject id of the case it acts on (a `case` row in subjects.csv) |
| right_outcome | What a right outcome is for this step, for one case; `proposed: ` when no one stated it |
| qualifier | Blank, or `partial: <what is missing>`, or `stub: <what stands in>` when the step is only partly carried out, saying which part falls short: `stub: the chat assistant uses a fixed list` |
| source | Citation, including the reference model a step came from if the code does not name it |

A step that nothing carries out stays in the table. Give it no rows in participation.csv; it is drawn as
*not assessed*.

### subjects.csv: parts, people, the case, and the interactions between parts

| Column | What goes in it |
|---|---|
| subject_id | `S01`, ... for elements; `R01`, ... for interactions |
| kind | `element` or `relationship` |
| band | Architecture layer: `business`, `application` or `technology`. A service, worker, front end or AI agent is an application component (`application`); a database, cache, message broker, search index, file store, host or runtime, or platform service is a system component (`technology`), even when the application owns it. An interaction takes `application` when it joins components, and `technology` when it is a part's call to the store or platform it runs on. One of: `business`, `application`, `technology`. |
| level | `component` (any deployable the flow runs through whose code can be had, whoever owns it), `external dependency` (relied on, and its code cannot be had), or blank for a person, a case or an interaction |
| part_kind | One of the kinds in `../method/part-kinds.csv`. If none fits, use the nearest kind and say so in `source` ("nearest kind: a content delivery network"). The lists in `../method/` are not edited during a run |
| name | The part's name as its owners use it |
| purpose | For a part (a row with level `component` or `external dependency`): what this part does in this flow, in one sentence, with a citation in brackets, read from the same source as the row (`Takes the shopper's order and keeps it (src/orders/api.py:12)`). Required on every part row; blank for a person, the case and an interaction. The page's *Inside this part* card prints it |
| application_id | Optional. For a component: the reference name it is registered under in the organisation's configuration database (an application id or configuration item), read from that record. Blank where no source states one |
| repository | For a component: the code repository it is built from, read from its build or deployment definition, with the path inside it where one repository builds several components (`shop-repo: services/payment`). For a component run from someone else's image: `not built here:` and the image. Blank for a person, the case, an interaction or an external dependency |
| owner, owner_as_of | The team accountable for it, and the date that was true. Where no source states it, inferred from what the sources show and written `proposed:` with the basis |
| responder, responder_as_of | Who is called when it breaks, and the date. Where no source states it, `proposed:` with the basis |
| from_id, to_id | For an interaction: the calling subject and the called subject |
| step_hint | For an interaction: the step or steps it happens within, `;` separated. Blank for a call made only at start-up |
| operation | Optional, for an interaction: the operation or operations of the calling part whose requests make the call, `;` separated, written as `participation.csv` writes them, with the code line in `source`. Blank: the page joins the call to the operation through the step it happens within, and draws it "via the step" |
| sequence | For an interaction: its place in a strict order of calls within its step (1, 2, 3). One number if its place is the same in every step it is in, else one `step:order` pair per step (`6:2; 8:1`). Blank if the order is not known, or the call is repeated per item, made in parallel, not waited for, or made only on one branch. Two calls never share a number in one step |
| part_of | For a part of an outside service (a row with level `external dependency`): the subject id of that service. One level: never another part. Its parts are drawn inside its box |
| map_link | For an external dependency, or a part of one: the address of its owner's own map, if one exists |
| carries_case_id | `yes: ...`, `partly: ...` or `no: ...`, with where it is carried or lost |
| source | Citation |

Use `part_kind` `case` for the business object one case is recorded as (if nothing records it, the case as the business names it, with `carries_case_id` `no: not recorded`), `person` for a person who carries out a
step, and `interaction` for a relationship row. An AI agent is a component with `part_kind` `LLM agent`.

### participation.csv: who carries out each step

| Column | What goes in it |
|---|---|
| subject_id | A part, person or external dependency |
| step | The step id |
| involvement | `performs`, `supports` or `records` (see `../method/involvement.csv`) |
| operation | Optional. The named behaviour of the part that does this step: an agent tool, an HTTP route (`PATCH /api/orders/{id}`), a message handler; what a caller invokes, read from the tool or route declaration. Several, `;` separated, where the step uses more than one. One operation may do several steps. Blank for a person, or where the part offers no named operation (a database, a store). Write an HTTP route as its method and path (`POST /chatclient`) or as `route` and its pattern (`route /api/genai/**`): on an AI agent's row, that form is how the receipt tells the route a caller invokes from a tool the agent's model calls, and only a route is asked the application set. A handler of another kind on an agent's row (a message consumer, a gRPC method) is not recognised yet |
| activity | What it does in that step, with a citation in brackets |
| decision_point | Optional. On an AI agent's row only: whether its tool is a decision point (FILL-STEPS Step 9). `yes:` where the agent chooses a value that becomes the case's outcome or a person's basis for deciding it (a recommendation, a decision type, a condition's text, the inputs to a risk computation); `no:` where the call only records what a person stated or asked for. Then why, naming the arguments the model fills in, with the citation of the tool's signature. A tool that computes by fixed rules is a decision point only through the arguments the agent chose to pass it: say which. A tool whose class depends on the conversation (it records an item the person named, but chooses one the person only described) is `yes:`, and the reason says when the call carries the agent's choice, and whether telemetry can tell those calls apart. One agent's tool is classed the same way on every row. Blank for every other part |
| reply_decision_point | On an AI agent's row only: whether the agent's reply to a person at this step is a decision point (FILL-STEPS Step 9). Its operation is the agent's turn, not a tool, so it is classed here on the agent's own row, beside its tool, which keeps its own class in `decision_point`. `yes:` where the person relies on the reply, as when it reports or explains a result (a recommendation, a risk assessment, a check's outcome); `no:` where it only confirms what the person asked, asks for more, or the agent replies to no person at this step. Then why, with the citation of the prompt or the code that shapes the reply. Each reply relied on is a decision point keyed by the agent and the operation on its row: `S04 reply to uw_render_decision` for a reply reporting a tool's result, `S03 reply on POST /` for the reply of a run a route starts (an agent with no tool), `S04 reply at step 17` for a row naming no operation; never one for all of an agent's replies. Required on every agent row; blank for every other part |

### agent-system.csv: each AI agent as its own system

One block of rows per agent. The views draw the agent with its own run, actions, agent parts and dependencies,
joined to the process steps it serves.

| Column | What goes in it |
|---|---|
| agent | The subject id of the agent's component in subjects.csv |
| id | `A0` for the run; `AS1`, ... actions; `AP1`, ... agent parts; `AD1`, ... dependencies |
| element | `run`, `action`, `agent part` or `dependency`. An action is one act inside the run (a model call, a call to a tool, a check), as in a UML activity; "operation" is kept for a tool or route a part offers (`participation.csv` `operation`). A register made before this release says `operation` here: run `reconcile.py --migrate` on a copy; an agent part is a piece of the agent's own machinery (its model, its tools, its guardrails, its orchestration) |
| name | Its name |
| what_it_is | One line. For a part you looked for and did not find, say where you looked |
| subject_id | For a part or dependency: the subject id(s) in subjects.csv that carry it. Blank for a part nothing was found carrying: it is drawn as not assessed |
| performed_by | For an action: the part id(s) that perform it. Blank: not assessed |
| uses | For a part: the dependency id(s) it calls |
| serves_business_step | For the run or an action: the business step id(s) it performs or supports |
| source_ref | Citation |
| decision_point | Optional. On an action row only, and only for a model call whose output a later call of the chain relies on, where no tool's or reply's decision point in `participation.csv` holds it (a room description written by a first call and fed to a second): `yes:` and why, with the citation of the call that reads it. The receipt keys it by the agent and the action's id (`S03 AS2`) (FILL-STEPS Step 9). Blank on every other row; `no:` with the reason where you looked and it is not one |
| next | Optional. The run's control flow, read from the code that sequences it (the orchestration's graph or loop). On the run row: the action or actions a run starts with. On an action row: the actions a run may go on to after it, `;` separated, or `end` where a run can end there. Name an earlier action where the run repeats (the model decides again after a tool call). Where there is more than one, a condition in square brackets may follow each, in plain words (`AS3 [a tool call]; AS6 [an answer]`). The page draws the run as an activity diagram from it, a move only where it is recorded; blank, it says the order is not on record |

The parts an agent usually has: the code that sequences its actions, the decider (the model with its prompt and
rules), its tools, what it retrieves from, and the checks that stop an answer outside policy.

### measures.csv: what could show whether it works

Design-time: each row is a measure someone could take. It is proposed unless the code already emits it.

| Column | What goes in it |
|---|---|
| handle | `M01`, ... |
| subject_id | What it is about: a part, an interaction, or the case subject of a flow (with `step` blank, a measure of the whole flow) |
| step | The step it is about, if one |
| stage | For a measure of a whole stage (its case subject, `step` blank): the stage id. Counts the cases in the stage, the oldest one's age, the time through, or those past the stage's time limit |
| flow | For a measure of a whole flow (its case subject, `step` blank): the flow id. Required when two flows share one case subject, or the measure is counted for neither |
| measure | Its name |
| question_it_answers | The question, first |
| layer | `business health`, `business impact`, `application`, `technology` or `agentic` (`../method/layers.csv`) |
| counted_on | `cases`, `events`, `requests`, `resources` or `runs`. Business measures count cases |
| counted_how | One line: what one count is |
| form | Its form, from `../method/measure-forms.csv` where one fits; blank where none does. One of: the forms in `../method/measure-forms.csv`. |
| exists | `yes` if the system already emits it, else `no`. A log line counts. So does a framework's built-in metric switched on by a dependency or setting: cite that line. Emitted but not collected anywhere is still `yes`; whether anything collects it goes in `watched` |
| agent_question | For a measure of an agent: the row of `../method/agent-questions.csv` it answers |
| source | `declared` (found in the code) or `proposed` |
| source_ref | Citation of the emitting line, or of what the proposal rests on. Only that: what an emitted measure counts wrong goes in `defect` |
| alert | `yes:` and the basis, on each measure drafted as a proposed alert, at any level: the flow, a stage, a step or a part. Whether to alert, and on what, is the team's decision; the register drafts. The alert is drafted on every stage its measure reaches (a step's stage, every stage of a flow, each stage a part serves in `participation.csv`), and the runbook generator works that stage's tests for it, which fits best a stage's measure counted on cases (the cases past its time limit, or the cases leaving it wrongly). The basis is free text: why this measure would show the expectation broken. The expectation it guards is named by id in `expectation`, and the moves it counts go in `counted_moves`; an id written in the basis is never read as one. Blank on every other measure. Whether an alert pages a person, opens a ticket or shows on a dashboard is the operators' decision. The alerts and the runbook are generated from this column |
| counted_moves | On a measure proposed for alerting that counts cases leaving the stage: the lifecycle moves (`L..`) whose cases it counts, by id, `;` separated (`L25; L26`). Each is a move of that stage in `lifecycle.csv`. The runbook entry works the tests of the states those moves leave from. Blank on a measure of cases waiting and on every measure not proposed for alerting. `flow_outputs.py --check` fails on an alert of cases leaving with it blank, and on an id not in `lifecycle.csv` or not a move of the stage |
| expectation | Optional. The expectations this measure is evidence of, by id, `;` separated (`e2; e5`), in the same form as `counted_moves`. **Required on every measure with `alert` set**: the expectation the alert guards. Optional on every other measure. A measure at `business health` or `business impact`, of the flow, a stage or a step, that names an expectation is its indicator (FILL-STEPS Step 9, mechanism 2). Each id is an `expectation_id` in `expectations.csv`. `--check` fails on an alerting measure with it blank, a register without the column included, and on an id `expectations.csv` does not hold |
| operation | For an application or agentic measure: the operation or operations it counts, `;` separated, written exactly as `participation.csv` writes them (`uw_render_decision`, `PATCH /api/orders/{id}`); `reply` and the operation for a measure of an agent's reply (`reply; uw_render_decision`, `reply; POST /`), or `reply` alone for a reply at the step in `step`; the action's id in `agent-system.csv` (`AS2`) for a model output a later call relies on. Blank for a measure of the whole part. The receipt (FILL-STEPS Step 9) reads it |
| receipt_question | The receipt question or questions it answers (FILL-STEPS Step 9), `;` separated. For a measure of a step: `did it happen`, `was its outcome right`. For a measure of a stage: `in the stage`, `oldest's age`, `time through`, `past the time limit`. For an agent's `operating health` measure: `run duration`, `failed tool calls`, `tokens`, `refusals`, `fallbacks to a person`. Blank where the receipt reads the measure without it (the flow's time limit, an operation, a component, a decision point). The receipt reads it. One of, for each: `did it happen`, `was its outcome right`, `in the stage`, `oldest's age`, `time through`, `past the time limit`, `run duration`, `failed tool calls`, `tokens`, `refusals`, `fallbacks to a person`. |
| defect | Only where `exists` is `yes`: in one line, what the emitted measure counts wrong, with its citation (a duration split evenly across a batch, a label that never varies, a counter nothing increments, a panel serving generated data). Blank where no defect is known. `flow_outputs.py --check` fails on a defect written on a measure that is not emitted |
| watched | Optional. Only where `exists` is `yes`: whether operations monitoring collects the emitted measure (FILL-STEPS Step 9). `yes` where a scrape configuration, collector, exporter, log shipper or monitoring dashboard takes it; `in the app only` where an application screen shows it and nothing collects it; `no` where nothing does (a metric nothing scrapes, a log nothing ships); `unknown` where no such configuration is within reach. Never settled by reading the emitting code. Blank on a proposed measure. The page shows it in an opened measure, as Watched |
| watched_source | Optional. Where `watched` is set: the collection or dashboard configuration read, with its citation, or the words `no inventory reachable`, which only `unknown` may rest on. `flow_outputs.py --check` fails on a value outside `yes`, `in the app only`, `no`, `unknown`, on `watched` with no source, and on `watched` written on a measure that is not emitted |
| taken_from | The kind of record the measure is counted from. Where `exists` is `yes`, the kind of the line cited in `source_ref`; on a proposed measure, the kind it would be taken from. Decide it from what the measure counts, never from the tools at hand (FILL-STEPS Step 9). One of: `metric`, `log or event record`, `trace`, `the edge`, `external probe`, `client-side instrumentation`, `the case's own record`, `a message log kept with the state`, `configuration`, `platform lifecycle events`, `another organisation's record`. |

A measure is a candidate: something that could show whether the capability works. Choosing which are wanted, and
setting any target or threshold, is done later by people; the register holds none unless a source states one.

### measure-gaps.csv: elements with no candidate, and why

The coverage receipt (FILL-STEPS Step 9) asks every element of every start-set its questions. An element no
candidate in `measures.csv` answers gets a row here. A gap is not a measure: it says why none is proposed, so a
reader can tell an element looked at and left without a candidate from one never looked at.
`flow_outputs.py --check` fails on an element with neither, and on a row here with no `why`, no `source` or no
`kind` from the closed list.

The same table gaps a question a view asks and the register cannot answer: a step's trigger or timeouts, a part's
operations or what it depends on, a stage's other outcomes or the moves that cannot be undone, an alert's own tests.
The card then prints the gap's kind and reason instead of "not in the map yet", and `run_status.py` counts it gapped,
not empty. The `question` is the view question's id, exactly: `step: trigger`, `step: timeouts`, `part: operations`,
`part: depends on`, `stage: other outcomes`, `stage: cannot be undone`, `alert: its own tests`,
`expectation: indicator`. The `element` is the step id, the part's subject id, the stage id, the alert measure's
handle, or the expectation's id (`e3`). The other view questions take no gap:
they are answered, or counted only.

| Column | What goes in it |
|---|---|
| element | What is not covered, as the receipt names it: a flow id (`F1`), an expectation id (`e3`), a stage id (`ST2`), a step id (`7`), a component's id and an operation (`S03 PATCH /api/orders/{id}`), including the route an agent's own component serves (`S06 POST /chatclient`), a component's id (`S08`), every component whatever its involvement, `records` included, a decision point: an agent's id and the tool it calls (`S04 uw_render_decision`), or `S04 at step 15` for an agent row naming no tool, or an agent's reply classed `yes:` in `reply_decision_point` (`S04 reply to uw_render_decision`, `S03 reply on POST /`, `S04 reply at step 17`), or a model output a later call relies on, by the agent and its action in `agent-system.csv` (`S03 AS2`), or an agent's id for its runs (`S04`) |
| question | The question not answered: `the time limit` (flow, only where its `bound_in_code` is filled), `in the stage`, `oldest's age`, `time through`, `past the time limit` (stage, only where its `bound_in_code` is filled), `did it happen`, `was its outcome right` (step), `application` (an operation or component), `technology` (a system component), an agent question from `../method/agent-questions.csv` (decision point), or a run metric, `run duration`, `failed tool calls`, `tokens`, `refusals`, `fallbacks to a person` (an agent's runs), or `expectation: indicator` (an expectation in `expectations.csv`, by its id: `e3`) |
| kind | Which of four the gap is: `does not apply` (ruled out by design: the question cannot arise here, and `why` says why), `counted by` (folded into another measure, whose id `why` names: `folded into M51:`), `no record` (the code keeps nothing that could count it today), `not read` (not assessed in this run). The map labels the gap from it ("Does not apply", "Counted by" and the measure's name, "No record to count", "Not assessed") and never from the reason's wording; the run's status counts the gaps by it. `flow_outputs.py --check` fails on a row with it blank or not one of the four, and on a `counted by` row whose `why` names no measure of `measures.csv` |
| why | Why no candidate is proposed: the record that does not exist, the candidate it is folded into (`folded into M51:` and why), or why the question does not apply here. Cite the line |
| source | Citation |

### step-impact.csv: what a failure at a step costs

| Column | What goes in it |
|---|---|
| step | The step id |
| impact_category | From `../method/impact.csv` |
| unit | What is counted, in cases ("applications stuck before underwriting") |
| recovery | `moves on` (cases continue once the cause is fixed), `stranded` (they wait until someone acts), or `not created` (the request fails and no case is kept; the person must start again). Blank if no source shows it. A step nothing carries may still have a row: what its not happening costs is knowable |
| note | Why, with a citation. For a case acknowledged and then lost, which fits no `recovery` value, begin with `lost after acknowledgement:` and leave `recovery` blank |

### failure-modes.csv: what can stop each move of an alerted stage (FMEA)

FILL-STEPS Step 11. One row per failure mode of one or more moves, read hop by hop against
`../method/hop-failures.csv`. The runbook is generated from these rows: each row is one test, written once in the
stage's shared section, and run from the entry of every proposed alert whose cases are in, or left from, the state
its move leaves from. `flow_outputs.py --check` fails the run while any hop, carrier or need of a move of the stage
has no row.

| Column | What goes in it |
|---|---|
| mode_id | `FM01`, ... |
| moves | The lifecycle rows it can stop, `;` separated. One row may serve several moves when the part, the mode, the test and the ending are the same for each |
| hop | A hop kind from `../method/hop-failures.csv` that every listed move travels by, or `needs` for a store, broker or outside service the move needs |
| mode | The catalogue mode for that hop kind, or `other` for one the catalogue lacks (say what in `failure`) |
| part | The subject id that fails: one of the move's `carried_by`, or for `needs` one of its `needs`. Nothing outside the lifecycle row. A **sweep** lists several, `;` separated: parts of one `part_kind` with the same hop, mode and ending, each in a listed move. Its `test` is one command over all of them that names which matched |
| failure | What goes wrong here, read from the code, cited. For a mode the design rules out: `not possible here:` and the citation |
| recovery | What happens to the case: `moves on`, `stranded`, `not created`. Read for this mode, not copied: a consumer that is down leaves a message that moves on later, a consumer that throws and acknowledges strands it |
| test | The one action that tells this mode apart, runnable as written: the query with its table and columns, the log text exactly as the code writes it, the command |
| measures | The measure handles the test reads, `;` separated |
| expected | What the test shows when this mode is not the cause |
| seen | What it shows when it is. On a state column, list every value the code can leave other than the healthy one |
| ending | `restore`, `cannot restore`, `expected condition`, `already known`, `nothing wrong`, `self-healed`, `degraded within tolerance`, `outside`, or `not possible` |
| remedy | A `remedies.csv` id. Required for `restore`, and for a `stranded` case (a re-drive, or the stated `none exists`) |
| source | Citation |
| order | Optional, a whole number: within an alert's entry, after the checks that each part is up, tests run in this order, and a blank counts as 0. Give a test whose evidence lists cases a higher number than the tests that explain those cases |

### remedies.csv: what a responder can do

| Column | What goes in it |
|---|---|
| remedy | `RM1`, `RM2`, ... (interactions in subjects.csv are `R01`, ...) |
| kind | `restore` (bring a part back), `re-drive` (move stranded cases on), `roll back` (undo a change), `none exists` (say so, and what to record), `do not` (an action that looks like a fix and is not) |
| action | What to do, runnable as written, in the configuration `about.csv` names |
| expected | What the responder sees when it worked |
| if_different | Where to go when it did not |
| needs_approval | `yes` where the action changes production data or configuration under change control |
| also_escalate_to | Optional. A party the responder escalates to besides the failing part's owner, `;` separated: a subject id, or a role the register does not map (`the compliance owner`). The runbook gives each a row in its escalation table. Blank for most remedies |
| source | Citation. A re-drive outside the code (a state reset the application then re-sends from) cites the code that makes it safe |

### case-attributes.csv: what is at stake in one case

| Column | What goes in it |
|---|---|
| flow | The flow id |
| attribute | A field of one case (amount, account, application id) |
| what_is_at_stake | Why it matters |
| source_ref | Citation |

### how-made.csv: how this register was made

One row per step of `../FILL-STEPS.md` you did in each pass, written as you go. The page draws it as the workflow that produced
the map, so a reader can see what was done by a tool, what a model drafted, and what a person confirmed.

| Column | What goes in it |
|---|---|
| pass | The pass this row belongs to: `1` for the first fill, `2` for the first update, and so on (see sources.csv) |
| step | The step's number in FILL-STEPS.md (`0` for Before you start, `3a` for the step inserted after Step 3) |
| name | The step's name |
| went_in | What you worked from: the code at a commit, a document by title, a person by role, a tool's output file |
| came_out | The register files this step wrote, `;` separated (`flows.csv; stages.csv`) |
| done_by | One or more of `tool` (a program produced it; name it in `note`), `model drafting` (an AI assistant read the sources and wrote it), `person confirming` (a person checked and confirmed it), `by hand` (a person wrote it directly), `;` separated |
| note | One line: what the tool found or missed, what is drafted and unconfirmed, how long it took if you measured it |

### sources.csv: every source the register was made from

A map is never finished: a missing repository turns up, an architecture document arrives, someone explains the
business. Each arrival is a new pass over the same register. This table lists every source, and which pass
added it.

| Column | What goes in it |
|---|---|
| source_id | `SRC1`, `SRC2`, ... |
| what | A repository at a commit (with no version history, the folder as found), a document by title and date, a person by role, or a tool's output file |
| kind | `code`, `document`, `person` or `tool output` |
| repository | Optional: a register read from one repository may leave it out. For code: the repository's folder in the workspace, the first folder of every citation into it, and every citation is then checked to start with one listed here. For a `tool output` saved into the workspace (a dashboard or alert export): its folder. Blank for other kinds |
| commit | Optional. For code: the commit read, or `folder as found` with no version history |
| as_of | The date the source describes, or the date you were told |
| pass | The pass that first read it |
| note | One line: what it covers, and what it does not |
