# The register: one capability, described in tables

A register describes one business capability as it is carried out: its flows, their stages and steps, the parts
that carry each step, what those parts rely on, any AI agent among them, the measures that could show whether it
works, and what a failure costs, counted in cases. It is a design-time description. It holds no live values.

Copy this folder, fill it by following `../FILL-STEPS.md`, and draw it with `python ../capability_views.py <folder> --out <folder>/views.html`.

## Rules that apply to every table

- **Every row says where it came from.** Put a citation in `source`, `source_ref` or `basis`: a file and line
  (`src/loans/ApplicationService.java:42`), a document and section, or a person asked, with role and date
  (`asked: underwriting team lead, 2026-10-07`). If a descriptive cell already cites its source in brackets, that counts.
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
| as_of | The date the register describes |

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
| promise | A bound for this stage, if one is stated |
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
| qualifier | Blank, or `partial: <what is missing>`, or `stub: <what stands in>` when the step is only partly carried out. If only one way is partial, name the way: `stub: the chat way uses a fixed list` |
| source | Citation, including the reference model a step came from if the code does not name it |

A step that nothing carries out stays in the table. Give it no rows in participation.csv; it is drawn as
*not assessed*.

### subjects.csv: parts, people, the case, and the interactions between parts

| Column | What goes in it |
|---|---|
| subject_id | `S01`, ... for elements; `R01`, ... for interactions |
| kind | `element` or `relationship` |
| band | Architecture layer: `business`, `application` or `technology` |
| level | `component` (a deployable part inside the system), `external dependency` (relied on, run by someone else), or blank for a person, a case or an interaction |
| part_kind | One of the kinds in `../method/part-kinds.csv`. If none fits, add a row there with its family and that family's set (copy it from another row of the same family), and say so in `source` |
| name | The part's name as its owners use it |
| owner, owner_as_of | The team accountable for it, and the date that was true. Blank if no source states it |
| responder, responder_as_of | Who is called when it breaks, and the date. Blank if no source states it |
| from_id, to_id | For an interaction: the calling subject and the called subject |
| step_hint | For an interaction: the step or steps it happens within, `;` separated. Blank for a call made only at start-up |
| sequence | For an interaction: its place in the order of calls within its step (1, 2, 3). For a call made in several steps, one `step:order` pair per step (`6:2; 8:1`). Blank if the order is not known |
| part_of | For a part of an outside service: the subject id of that external dependency. Its parts are drawn inside its box |
| map_link | For an external dependency: the address of its owner's own map, if one exists |
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

### step-impact.csv: what a failure at a step costs

| Column | What goes in it |
|---|---|
| step | The step id |
| impact_category | From `../method/impact.csv` |
| unit | What is counted, in cases ("applications stuck before underwriting") |
| recovery | `moves on` (cases continue once the cause is fixed), `stranded` (they wait until someone acts), or `not created` (the request fails and no case is kept; the person must start again). Blank if no source shows it. A step nothing carries may still have a row: what its not happening costs is knowable |
| cause | Blank when the cost holds whatever stops the step. When the row describes what one part's failure does (a wrong answer, a stale list), the subject id of that part. A step can have several rows. The failure view shows a row only for its own cause, or a blank-cause row |
| note | Why, with a citation |

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
| what | A repository at a commit, a document by title and date, a person by role, or a tool's output file |
| kind | `code`, `document`, `person` or `tool output` |
| as_of | The date the source describes, or the date you were told |
| pass | The pass that first read it |
| note | One line: what it covers, and what it does not |
