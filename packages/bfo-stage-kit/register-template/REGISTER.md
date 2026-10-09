# The register: one capability, described in tables

A register describes one business capability as it is carried out: its flows, their stages and steps, the parts
that carry each step, what those parts rely on, any AI agent among them, the measures that could show whether it
works, and what a failure costs, counted in cases. It is a design-time description. It holds no live values.

Copy this folder, fill it by following `../FILL-STEPS.md`, and draw it with `python ../capability_views.py <folder> --out <folder>/views.html`.

## Rules that apply to every table

- **Every row says where it came from.** Put a citation in `source`, `source_ref` or `basis`: a file and line
  (`src/loans/ApplicationService.java:42`), a document and section, or a person asked, with role and date
  (`asked: underwriting team lead, 2026-10-07`). If a descriptive cell already cites its source in brackets, that counts.
  `--check` warns, in the tables it reads for drawing (not `lifecycle`, `failure-modes`, `remedies` or
  `set-aside`), about a row whose `source`, `source_ref`, `basis` and `activity` are all empty and whose cells
  hold none of these: a file name with a line (`Order.cs:57`), `asked:`, `§`, or a web address.
- **Not found is not absent.** If you looked for something and did not find it, leave the cell blank or leave the
  row out. Never write "none" or "no owner" as a value. The views draw a blank as *not assessed*.
- **Proposed is labelled.** A value you drafted with no source to confirm it starts with `proposed:`.
- **Ids are short and stable** (`C1`, `F1`, `ST1`, `S01`). Fields that list ids separate them with `;`.
- Columns are read by name. Extra columns are allowed and ignored by the drawing program.

## The tables

### about.csv: one row

| Column | What goes in it |
|---|---|
| system | The name the business uses for the system or estate that carries the capability |
| what_it_is | Two or three sentences: what the system does, for whom |
| modelled_from | How this register was made: from what, by what method, and what is proposed |
| sources_examined | Everything you read or asked, so a reader knows what "not assessed" covers |
| delivering_application | The deployables that make up the application delivering the capability, named. A part in this set is a component; a part outside it is an external dependency |
| as_of | The date the register describes |

### lifecycle.csv: the case's states and the moves between them

Built first (FILL-STEPS Step 2). One row per move: the act that takes one case from one state to the next.
Stages, steps, parts, measures and the runbook are read off it.

| Column | What goes in it |
|---|---|
| move_id | `L01`, `L02`, ... in the order a case meets them on the main path, then alternatives |
| flow | The flow id |
| from_state | The state the case is in before the move, as the system records it (cited), or `implicit: ` and the state in words. `(none)` for the move that creates the case |
| from_kind | `park` (nothing is progressing the case; the next move needs a trigger not already in motion) or `in act` (the act is still working: a message on its way to a consumer that will act on it, a call out and back) |
| park_because | For a park: what the next move waits on: `timer`, `schedule`, `person`, `outside party`, `customer` |
| move | The act, in the case's terms, never naming its performer |
| to_state | The state the case is in after the move |
| path | `main`, `alternative` (another ending the design allows) or `exception` |
| order_note | Blank, `parallel with <move_id>` or `loops to <state>` |
| travels_by | How the move reaches the case: `in-process`, `call`, `message` (name the event and broker), `outbox`, `poll`, `timer`, `person`; several hops in order, `;` separated |
| carried_by | The parts that carry the act out, by name or subject id |
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
| expectation_of | Whose expectation the flow meets |
| promise | The expectation stated as a bound, or `none stated; proposed: ...` |
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
| promise | A bound for this stage, if one is stated; else `proposed: ` and a bound from what the application does |
| arrivals_per_period | Cases arriving per period at this stage. The operators' measured value; `not stated: measured by the operators` until they give it |
| source | Citation |

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
| qualifier | Blank, or `partial: <what is missing>`, or `stub: <what stands in>` when the step is only partly carried out. If only one way is partial, name the way: `stub: the chat way uses a fixed list` |
| source | Citation, including the reference model a step came from if the code does not name it |

A step that nothing carries out stays in the table. Give it no rows in participation.csv; it is drawn as
*not assessed*.

### subjects.csv: parts, people, the case, and the interactions between parts

| Column | What goes in it |
|---|---|
| subject_id | `S01`, ... for elements; `R01`, ... for interactions |
| kind | `element` or `relationship` |
| band | Architecture layer: `business`, `application` or `technology`. A service, worker, front end or AI agent is an application component (`application`); a database, cache, message broker, search index, file store, host or runtime, or platform service is a system component (`technology`), even when the application owns it. An interaction takes `application` when it joins components, and `technology` when it is a part's call to the store or platform it runs on |
| level | `component` (a deployable part inside the system), `external dependency` (relied on, run by someone else), or blank for a person, a case or an interaction |
| part_kind | One of the kinds in `../method/part-kinds.csv`. If none fits, use the nearest kind and say so in `source` ("nearest kind: a content delivery network"). The lists in `../method/` are not edited during a run |
| name | The part's name as its owners use it |
| owner, owner_as_of | The team accountable for it, and the date that was true. Where no source states it, inferred from what the sources show and written `proposed:` with the basis |
| responder, responder_as_of | Who is called when it breaks, and the date. Where no source states it, `proposed:` with the basis |
| from_id, to_id | For an interaction: the calling subject and the called subject |
| step_hint | For an interaction: the step or steps it happens within, `;` separated. Blank for a call made only at start-up |
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
| way | Blank when the step has only one way of being carried. When it can be carried more than one way (a web form or a chat assistant; an automated route or a person), name each way with a short label and list on every row of that step the ways the row belongs to: `chat` for a part only the chat way uses, `form; chat` for a part both use. The step still happens while any one way is whole, and the failure view says so |
| activity | What it does in that step, with a citation in brackets |

### agent-system.csv: each AI agent as its own system

One block of rows per agent. The views draw the agent with its own run, steps, parts and dependencies, joined to
the business steps it serves.

| Column | What goes in it |
|---|---|
| agent | The subject id of the agent's component in subjects.csv |
| id | `A0` for the run; `AS1`, ... steps; `AP1`, ... parts; `AD1`, ... dependencies |
| element | `run`, `step`, `part` or `dependency` |
| name | Its name |
| what_it_is | One line. For a part you looked for and did not find, say where you looked |
| subject_id | For a part or dependency: the subject id(s) in subjects.csv that carry it. Blank for a part nothing was found carrying: it is drawn as not assessed |
| performed_by | For a step: the part id(s) that perform it. Blank: not assessed |
| uses | For a part: the dependency id(s) it calls |
| serves_business_step | For the run or a step: the business step id(s) it performs or supports |
| source_ref | Citation |

The parts an agent usually has: the code that sequences its steps, the decider (the model with its prompt and
rules), its tools, what it retrieves from, and the checks that stop an answer outside policy.

### measures.csv: what could show whether it works

Design-time: each row is a measure someone could take. It is proposed unless the code already emits it.

| Column | What goes in it |
|---|---|
| handle | `M01`, ... |
| subject_id | What it is about: a part, an interaction, or the case subject of a flow (with `step` blank, a measure of the whole flow) |
| step | The step it is about, if one |
| stage | For a measure of a whole stage (its case subject, `step` blank): the stage id. Counts the cases in the stage, the oldest one's age, the time through, or those past the stage's promise |
| flow | For a measure of a whole flow (its case subject, `step` blank): the flow id. Required when two flows share one case subject, or the measure is counted for neither |
| measure | Its name |
| question_it_answers | The question, first |
| layer | `business health`, `business impact`, `application`, `technology` or `agentic` (`../method/layers.csv`) |
| counted_on | `cases`, `events`, `requests`, `resources` or `runs`. Business measures count cases |
| counted_how | One line: what one count is |
| form | Its form, from `../method/measure-forms.csv` where one fits; blank where none does |
| exists | `yes` if the system already emits it, else `no`. A log line counts. So does a framework's built-in metric switched on by a dependency or setting: cite that line. Emitted but not collected anywhere is still `yes`; say so in `source_ref` |
| agent_question | For a measure of an agent: the row of `../method/agent-questions.csv` it answers |
| source | `declared` (found in the code) or `proposed` |
| source_ref | Citation of the emitting line, or of what the proposal rests on. A defect found in an existing measure (a panel that counts the wrong thing) is written here |
| pages | `yes` on the measure, or measures, a stage's alert fires on: a measure of that stage, counted on cases (the cases past its promise). Blank on every other measure. The alert and the runbook are generated from this column, so nothing else may claim to page |

### step-impact.csv: what a failure at a step costs

| Column | What goes in it |
|---|---|
| step | The step id |
| impact_category | From `../method/impact.csv` |
| unit | What is counted, in cases ("applications stuck before underwriting") |
| recovery | `moves on` (cases continue once the cause is fixed), `stranded` (they wait until someone acts), or `not created` (the request fails and no case is kept; the person must start again). Blank if no source shows it. A step nothing carries may still have a row: what its not happening costs is knowable |
| cause | Blank when the cost holds whatever stops the step. When the row describes what one part's failure does (a wrong answer, a stale list), the subject id of that part. A step can have several rows. The failure view shows a row only for its own cause, or a blank-cause row |
| note | Why, with a citation. For a case acknowledged and then lost, which fits no `recovery` value, begin with `lost after acknowledgement:` and leave `recovery` blank |

### failure-modes.csv: what can stop each move of an alerted stage (FMEA)

FILL-STEPS Step 11. One row per failure mode of one or more moves, read hop by hop against
`../method/hop-failures.csv`. The runbook is generated from these rows: each row is one test, under the branch for
the state its move leaves from. `flow_outputs.py --check` fails the run while any hop, carrier or need of a move of
the stage has no row.

| Column | What goes in it |
|---|---|
| mode_id | `FM01`, ... |
| moves | The lifecycle rows it can stop, `;` separated. One row may serve several moves when the part, the mode, the test and the ending are the same for each |
| hop | A hop kind from `../method/hop-failures.csv` that every listed move travels by, or `needs` for a store, broker or outside service the move needs |
| mode | The catalogue mode for that hop kind, or `other` for one the catalogue lacks (say what in `failure`) |
| part | The subject id that fails: one of the move's `carried_by`, or for `needs` one of its `needs`. Nothing outside the lifecycle row |
| failure | What goes wrong here, read from the code, cited. For a mode the design rules out: `not possible here:` and the citation |
| recovery | What happens to the case: `moves on`, `stranded`, `not created`. Read for this mode, not copied: a consumer that is down leaves a message that moves on later, a consumer that throws and acknowledges strands it |
| test | The one action that tells this mode apart, runnable as written: the query with its table and columns, the log text exactly as the code writes it, the command |
| measures | The measure handles the test reads, `;` separated |
| expected | What the test shows when this mode is not the cause |
| seen | What it shows when it is. On a state column, list every value the code can leave other than the healthy one |
| ending | `restore`, `cannot restore`, `expected condition`, `already known`, `nothing wrong`, `self-healed`, `degraded within tolerance`, `outside`, or `not possible` |
| remedy | A `remedies.csv` id. Required for `restore`, and for a `stranded` case (a re-drive, or the stated `none exists`) |
| source | Citation |

### remedies.csv: what a responder can do

| Column | What goes in it |
|---|---|
| remedy | `R1`, ... |
| kind | `restore` (bring a part back), `re-drive` (move stranded cases on), `roll back` (undo a change), `none exists` (say so, and what to record), `do not` (an action that looks like a fix and is not) |
| action | What to do, runnable as written, in the configuration `about.csv` names |
| expected | What the responder sees when it worked |
| if_different | Where to go when it did not |
| needs_approval | `yes` where the action changes production data or configuration under change control |
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
| step | The step's number in FILL-STEPS.md (`0` for Before you start) |
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
| as_of | The date the source describes, or the date you were told |
| pass | The pass that first read it |
| note | One line: what it covers, and what it does not |
