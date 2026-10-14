# What changed in each release

Newest first. Each release replaces the one before it. If you ran an earlier release, see USE.md, "If you ran an
earlier version of this kit": a new run leaves your earlier register untouched and checks it against the code.

## Release 2 — 2026-10-14 (afternoon)

### What you will notice

- **An earlier register is checked, never trusted.** Point the kit at a workspace where an earlier run left a
  register, and it leaves that register exactly as it is and walks the code afresh into a new folder. Then a script
  compares the two row by row: what the earlier one has is kept only if the code, the document or the person it
  cites supports it, and the report lists what was added, carried forward, not supported, not assessed, and where
  the two disagree. **In this release the comparison only reports: nothing from the earlier register is added to the
  new one.** Rows whose cited code line still exists are headed *Unchecked: not added*, because a line existing does
  not show it supports the row; a person reads them. Adding checked rows comes in the next release. A new register is only ever started in an empty folder; the starting script refuses to copy
  over existing files. This replaces the in-place upgrade prompt that USE.md used to give.

- **The run checks it has every repository.** In Phase 0 it searches your code host, with your own access, for
  the repository behind every reference the code makes that the workspace doesn't answer, and for repositories
  that call or deploy this flow's services, and repeats until nothing new turns up. Each one found is recorded
  with the search that found it and added to the workspace; `RUN.md` answers "Is this the complete set of
  repositories?".
- **The run follows a workflow and keeps a record.** Before it does anything, the assistant writes `RUN.md` in the
  register folder. It restates what the run will produce, phase by phase, and then marks each phase to do, doing,
  done or blocked. A new chat reads `RUN.md` first and carries on from where the run stopped. If something stops a
  phase, such as Python not being available, the phase is marked blocked and the reason is given. Nothing is skipped
  without saying so.
- **Done is checked, not claimed.** `run_status.py` lists every file the run should have produced, the HTML pages
  included, and prints DONE or NOT DONE. The final report pastes its output, so a run that stopped before drawing the
  map can't report success.
- **Fullness counts.** Under DONE / NOT DONE, `run_status.py` prints how full the register is: steps and measures
  per stage, the share of elements left as gaps (split by kind), steps with an operation named, parts with an inside
  view, and tests per alert.
- **Gathering sources (Phase 0).** Name in your request what the run should read: repositories, pages, diagrams,
  process descriptions, notes. The assistant gets them with its own tools and lists each in `sources.csv` with the
  step that uses it. When the code calls a service whose code isn't in the workspace, the assistant fetches it, but
  only with access you already have, and read-only. It never requests access, never enters credentials, and never
  changes anything at the source. Every fetched source is recorded with what referenced it. To keep the run to
  exactly what you named, say "use only the sources I name".
- **What would make this map fuller.** The final report ends with the services the map stops at, and the guesses
  (`proposed:`) grouped by the kind of source that would settle them.
- **A component is any service the flow runs through whose code can be had**, whatever application or team it
  belongs to. An external dependency is one whose code can't be had, such as a vendor or a service you have no access
  to. Inside a component, the run reads only the operations this flow calls and what they call.
- **The worked example is full.** The eShop example now covers all four stages, with operations, inside views,
  measures on every stage, and runbook entries kept short. It is the shape to follow.
- **The page.**
  - The map fills the window, and you can collapse it again.
  - Drawings in the side panel are at reading size.
  - Measures are grouped by layer.
  - Where nothing is measured, the panel says why: "Does not apply", "Counted by …", "No record to count" or "Not
    assessed".
- **Runbooks at scale.** Tests that check the same thing are grouped, shared parts are checked first, and the
  runbook author can set the order of tests. The "is it up" checks always come first.
- **Every stage.** Running the kit for a later stage updates and rechecks every stage already done.
- **A run can't report DONE on a thin map.** Each view has a fixed set of questions it must answer: for a step, which
  moves make it up, what starts it, what happens if it doesn't, and how long it is allowed; for a part, what it is for,
  its operations and what it depends on; for a stage, its promise, how a case enters, its outcomes and what can't be
  undone; for the flow, what one case is, when it starts and ends, and who expects what. `run_status.py` counts each
  question as answered, gapped or empty, and prints NOT DONE, naming each question, while a required one is empty.
  On a first run, a question left as "not read" doesn't count either.
- **An empty answer has to say why.** Where the code doesn't hold an answer, the run writes a gap row with its kind
  (does not apply, counted by, no record), and the views show the reason instead of "not in the map yet".
- **Owner and responder are counted, never required.** They are filled when known.
- **"Inside this part" says what each part is for**, from the code.
- **Repositories are opened as folders of your workspace, and the run uses your environment's code tools.** Every
  repository, including ones the run fetches, must be a folder of the open workspace; if the run can't add them, it
  stops, names them and asks you to open them as one multi-root workspace. It then uses whatever code-intelligence
  tools are on offer (call graph, cross-repository trace, failure-handling and unreferenced-code analysis) as sources.

### Changed in the register

- `participation.csv` → `way` is no longer read: the step drawing ignores it, and the check warns while the column is
  there. Remove it.
- `capability_views.py --check` compares every table's columns with `register-template/REGISTER.md`. A table that
  lacks a column defined there is an error, one per table naming each missing column, unless the column's
  description begins *Optional*; a column defined nowhere there is a warning, since nothing reads it. A retired
  column (`way`, `delivering_application`, `step-impact.csv` → `cause`) keeps its own warning. A missing table file
  is not checked. The template's headers are tested against the same definition, so the two can't drift.

The check names each change. A run that finds an earlier register leaves it untouched and starts a new one (see
"Retired" below).

- The check now refuses a `subjects.csv` with no `repository` column, and a component with `repository` blank;
  only a `technology` component whose `source` says no repository defines it may stay blank.
- `sources.csv` gains `repository` (the workspace folder a code source is) and `commit`. Every citation starts
  with a repository listed there. `subjects.csv` → `repository` (since release 1) is filled for every component,
  from its build or deployment definition.
- `measures.csv` gains `counted_moves`. On an alert of cases leaving a stage, it lists the moves the alert counts.
- `measure-gaps.csv` gains `kind`: `does not apply`, `counted by`, `no record` or `not read`.
- `failure-modes.csv` gains an optional `order`.
- `about.csv` loses `delivering_application`.
- `subjects.csv` has a new column, `purpose`: what the part does in this flow, in one sentence, cited. The check fails
  without it.
- `measure-gaps.csv` accepts gaps on view questions, with the `question` values FILL-STEPS lists (for example
  `step: trigger`, `part: operations`). A step no part carries may gap its moves as `no record`, saying where it was
  looked for.
- `lifecycle.csv`: every hop in `travels_by` has a description (what starts the step is read from the first one), and
  `irreversible` is `yes` or `no`, never blank.
- A register from an earlier release fails DONE until these are filled. KNOWN-GAPS says how.

### Fixed

- **The comparison with an earlier register reads it the way it was written.** A part named `Name (repository)`
  matches `Name`. A citation into a copy of a repository outside the workspace is checked in that repository. An
  `asked:` answer covers only its own field and is printed with its value. A document named in a field is re-opened
  at the section it names. Each row's claim is printed beside its cited lines, with a verdict and reason left blank
  for the assistant to fill in.
- The copy-and-paste prompt in USE.md now runs the whole workflow, so it draws the map. Before, it stopped after the
  stage files.
- An alert proposed on a measure the code doesn't emit yet now says it fires on "No data" until the measure exists.
- An alert's counted moves come from their own column, never from its written explanation.

### Retired: upgrading an earlier register in place

Until this release, USE.md gave a prompt that upgraded an earlier register in place, and KNOWN-GAPS.md carried these
notes for it. An upgraded row looks verified and is not, so the route is retired; an earlier register is now
reconciled against the code instead. The notes, as they stood:

- A register filled with an earlier version of this kit names the alerting column of `measures.csv` `pages`.
  Rename it to `alert`; until then no measure is proposed for alerting and no alert or runbook is written.
- A register filled with an earlier version of this kit fails `--check` until it has rows for the two newest
  failure modes, `call: callee answers wrongly` and `needs: answers stale or wrong`, and no alert or runbook is
  written until then. Add the rows; a `call` row names the part that is called, the callee whose answer the move
  waits on, one row per callee where a move makes several calls (a `not possible here:` row with its reason is enough where the mode cannot
  cause what the stage's alerts count), and state the basis of each measure proposed for alerting as `yes:` and the reason.
- A register filled with an earlier version of this kit fails `--check` until its measure step's receipt is
  complete: every element FILL-STEPS Step 9 accounts for (the flow and each stage at business health, each step
  that matters asked both questions, each operation, each system component, each agent's decision points) is
  covered by a candidate in `measures.csv` or has a row in `measure-gaps.csv` saying why not (an earlier register
  has no `measure-gaps.csv`: copy it from `register-template/` first). That is intended:
  the failure lists the elements nobody had looked at. Mark the existing step measures in `receipt_question` and the
  operations they count in `operation` first; many elements are already covered.
- A register filled with an earlier version of this kit has no `receipt_question` column: add it, empty `defect` and `operation` columns to `measures.csv` and a `decision_point` column to
  `participation.csv`. It then fails `--check` until each stage's four candidates are marked or gapped (`in the
  stage`, `oldest's age`, `time through`, `past the promise`),
  each agent row is classed `yes:` or `no:` in `decision_point`, and each agent's five run metrics are covered or
  gapped. Defect prose in `source_ref` moves to `defect`. Add a `reply_decision_point` column to
  `participation.csv` too: the check then fails until each agent row's reply is classed `yes:` or `no:`.
- A register filled with an earlier version of this kit names the acts inside an agent's run `step` and its pieces `part` in
  `agent-system.csv`'s `element` column: rename `step` to `operation` and `part` to `agent part`. The check fails on
  the old values.
- A register filled with an earlier version of this kit may name a runbook section (`§2`) in a remedy's `action`,
  `expected` or `if_different` in `remedies.csv`. The check fails on it: write
  the action itself (`Escalate`, `Roll back`) in its place, and the runbook points it at its section. A remedy that
  names a measure proposed for alerting (`M13`) fails the same way: write the action, not the measure.
- A register filled with an earlier version of this kit has no `operation` column in `participation.csv`. The column
  is optional: without it the receipt asks no question of any operation, and the check passes. To have each operation
  asked, add the column and fill each row from the code with the route, tool or handler that performs the step; then
  name in `measures.csv` `operation` the operations each measure counts.
- A register filled with an earlier version of this kit has no `counted_moves` column in `measures.csv`; the
  moves an alert counted were read from its basis. Add the column after `alert` and, for each alert of cases
  leaving the stage, fill it from the moves its basis says it counts, by id and `;` separated, as a person reads the
  basis (a move it names only to say it is not counted stays out). `--check` fails, and lists every alert that needs
  it, until each is filled. An alert of cases waiting leaves it blank.
- A register filled with an earlier version of this kit has a `delivering_application` column in `about.csv`, and
  may list as an external dependency a service the flow runs through only because another application owns it. The
  check warns on the column: remove it, since a component is now any deployable the flow runs through whose code
  the run can get (FILL-STEPS Step 5). For each external dependency whose code can be reached, get its repository,
  list it in `sources.csv`, and map it as a component, reading the operations this flow calls and what those call.
- A register filled with an earlier version of this kit has a `way` column in `participation.csv`. Nothing
  reads it any more, and the step drawing is the same with it or without it. The check warns on the column: remove it.
- A register filled with an earlier version of this kit may lack newer optional columns: `watched`,
  `watched_source` and `order` in `measures.csv`, `also_escalate_to` in `remedies.csv`, `decision_point` in
  `agent-system.csv`. Add each from `register-template/`; they may stay empty, and fill them from the code where
  it says.
- A register filled with an earlier version of this kit has no `kind` column in `measure-gaps.csv`, and
  `--check` fails until each row has one. Add the column after `question` and fill it on every gap row by reading
  its reason, as a person would: `does not apply` (ruled out by design), `counted by` (folded into another measure,
  whose id the reason names), `no record` (the code keeps nothing that could count it), or `not read` (not assessed
  in this run). `--check` lists every row that needs it; a row left blank or with any other value fails the same way.
- A register filled with an earlier version of this kit is NOT DONE until each field a view requires is answered
  or gapped (FILL-STEPS marks each one required at the step that writes it): a trigger in every hop's body, timing,
  `if_not`, `irreversible` as `yes` or `no`, each part's operations and dependencies, and the stage and flow
  fields. `run_status.py` names each empty one by element. Add a `purpose` column to `subjects.csv` after `name` and
  fill it for each component and external dependency from the code: what the part does in this flow, in one
  sentence, cited. `--check` fails until the column exists and every such row has one.
- A register filled with an earlier version of this kit may have no `repository` column in `subjects.csv`, with each
  component's repository written inside `name`, in parentheses. `--check` fails until the column exists and every
  component has one. Add the column after `application_id`, as in the template; move each repository out of `name`
  into it, so `name` is the plain name; and fill it for every component from its build or deployment definition, or
  `not built here:` and the image for one run from someone else's image. Shared infrastructure a parent component's
  deployment provisions (a database, a cache, a broker) takes the repository that defines it, with the path to the
  definition (`repo: path`). A row not separately built, such as an in-process sub-agent, is not a component: remove
  it and describe it in `agent-system.csv` inside its parent component's run. A `technology` component no repository
  defines stays blank, and its `source` says so and where it was looked for.
- A register filled with an earlier version of this kit may lack columns the tables now define, in any table, and
  `--check` fails with one error per table naming them. Add each missing column from the matching file in
  `register-template/`, in its place, and fill it as FILL-STEPS says at the step that writes it; a blank cell reads as
  not assessed. A column whose description in `register-template/REGISTER.md` begins *Optional* may stay out. Remove
  a column `--check` warns is defined nowhere, or move what it holds into the column it belongs in.

## Release 1 — 2026-10-14 (midday)

- The kit is a skill. Copy `skills/bfo-stage-kit/` to `.github/skills/` in your workspace (or `~/.copilot/skills/`)
  and ask the assistant in your own words.
- The map is one page: click a step, part, stage or the flow to light its chain and open its measures. It has
  views for how a step is carried out, what is inside a part, and how a case moves through a stage and end to end.
- Runbook and alert pages for each stage, as HTML beside the Markdown.
- USE.md explains how to bring a register made with the first version up to date.

## First version — 2026-10-09

- The first version: the procedure, the register template, the generator for one stage's structure, measures,
  alert and runbook, and a worked example.
