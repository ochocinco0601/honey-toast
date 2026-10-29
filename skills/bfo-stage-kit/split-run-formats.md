# Interfaces of the split run: the files its modules hand each other

Every module of the split run reads and writes exactly these files, and a change to any of them is made here first.

`<reg>` is the run's register folder (for example `bfo-work/sockshop-split/`). `<ws>` is the workspace root that holds
the code and `bfo-work/` (code citations are paths relative to it). All files are UTF-8 CSV with a header row, written
with Python's `csv` module, unless named otherwise. Root-level `*.csv` of `<reg>` are the map's tables, which the kit's
existing checks read; nothing below is written at the root except the merged tables by `merge.py`.

## Layout

```
<reg>/
  run-settings.json          settings for this run (below)
  RUN.md, PLAN.md            as today; PLAN.md lists the units
  <table>.csv                the map's tables; written by the lead (flow-level tables) and by merge.py (the rest)
  units/units.csv            the reading units (below)
  units/<unit>/              one folder per unit, written only by that unit's reader (and by the re-read of an
                             unmatched call: the caller's calls.csv row, and one added operations.csv row)
  judging/<unit>/            verdict files, one per judge per row per round (below)
  judging/judgements.csv     collected by judges.py
  merge/unmatched-calls.csv  written by merge.py
  merge/summary.json         written by merge.py
  job/jobs.csv               written only by jobs.py
  job/lock.json              written only by jobs.py
  job/events.log             written only by jobs.py, one line per change, appended
  run.html                   the sponsor's page, written only by run_page.py
```

## run-settings.json

```json
{"judges": 3, "judge_rounds": 2, "unit_lines": 4000, "parallel": 6, "merge_rereads": 50,
 "lock_stale_minutes": 20, "on_change": "python run_page.py {reg}"}
```

`on_change` is run by `jobs.py` (cwd = the folder holding `jobs.py`'s caller's kit, placeholders `{reg}` and `{job}`)
after every state change; empty means none. Any key may be missing; the defaults above are held once, in
`settings.py`, and every module reads the file through it. The paths and column lists on this page are held once, in
`register_layout.py`.

## units/units.csv

`unit,deployable,repository,paths,files,lines,reader_facts,calls,called_by,note`

- `unit`: id, `[a-z0-9-]+`, unique (for example `orders`, `front-end-1`). The lead's flow-level tables are the unit
  `flow`, whose folder is `<reg>` itself (see Row keys).
- `paths`: `;`-separated folders or files under `<ws>` that the unit covers; a unit cut from a deployable lists the
  part it covers. Together the units of one deployable cover all of it.
- `calls`, `called_by`: `;`-separated unit ids. `reader_facts`: count of code-reader facts in the unit's paths.

## units/<unit>/ (a reader's output)

Every table has a first column `row_id`, unique in the unit and never reused (`orders-1`, `orders-2`, ...). A fix edits
a row in place; a row withdrawn is deleted and its id not reused.

| File | Columns after `row_id` | What a row is |
|---|---|---|
| `subjects.csv` | the register's `subjects.csv` columns | an **element** (`kind=element`) of this unit: the service and anything it alone owns (its store, its queue). `subject_id` is unit-local (`orders.svc`, `orders.db`). Relationship rows are never written here; `merge.py` makes them from `calls.csv` |
| `operations.csv` | `part,protocol,operation,source` | an operation this unit's part serves: `protocol` one of `http`, `message`, `rpc`; `operation` as served, for http `METHOD /full/path` with path parameters as `{name}`, for message the queue or topic consumed |
| `calls.csv` | `from_part,protocol,to_unit,to_part,via,operation,within,sequence,step_hint,carries_case_id,source` | a call going out of this unit's part. `protocol` one of `http`, `message`, `rpc`, `db`, `cache`. For a call to another unit: `to_unit` set, `to_part` blank, `operation` as the caller writes it (`METHOD url-or-path`, or the queue/topic published to). For a call to a store, broker or other part with no unit: `to_part` names that part (a unit-local subject_id of this unit, or `external:<name>`), `to_unit` blank. `via` names the broker of a message call (`external:<name>` or a subject_id), else blank. `within`: the calling part's own operation or operations (`; `-separated) the call is made within, spelled as in this unit's operations.csv and participation.csv, never `proposed:`; blank too, with what was traced named in `source`, when the operation cannot be traced (`operation` is the one called); blank for a call no operation of the part makes (a scheduled or startup trigger), with the trigger named in `source`. `sequence`: the call's order within its process step as `<step>:<n>`, `; `-separated when the call is made in several steps, each step one of `step_hint`; `<step>` a step id from steps.csv; blank when the call repeats per item, runs in parallel or is not waited for, or is made on only one branch; within one step no two of the unit's calls share a number. `step_hint`: the step ids the call is made in, `; `-separated |
| `participation.csv` | the register's `participation.csv` columns | which part takes part in which process step; `subject_id` unit-local |
| `files.csv` | `path,status,reason` (no `row_id`) | every file of the unit's paths: `status` is `cited` or `not relevant`; `reason` required for `not relevant` |

`source` cells (and any free text) cite code as `path:line` or `path:first-last`, paths relative to `<ws>`, exactly as
the kit's reading check parses them. A row whose claim is an inference starts its claim cell with `proposed:`.

## Row keys (what a judge judges)

A row is `(<unit>, <table>, <row key>)`. In a unit folder the row key is `row_id`. In the unit `flow` (`<reg>` root
tables written by the lead) the key is the first column's value, with `#2`, `#3` added to repeats in file order.
`files.csv` is never judged. A row with no code citation is not judged and is counted as such.

## judging/<unit>/ (verdict files)

One file per judge per row per round:
`judging/<unit>/r<round>-j<n>-<table>-<row key with every char outside [A-Za-z0-9_-] replaced by _>.csv`, one data row:

`unit,table,row,round,judge,verdict,reason`

`verdict` is `says`, `does not say` or `unclear`; anything but `says` flags the row. The file is written by the judge
session itself with the Write tool, and that session writes nothing else.

## judging/judgements.csv (judges.py collects)

`unit,table,row,round,judges,says,flagged,state,reasons`

One line per row, for its latest round. `state`: `pending` (fewer than `judges` verdicts this round), `passed` (all
say), `flagged` (any flag, rounds left), `disputed` (flagged in round `judge_rounds`). `reasons`: the flagging judges'
reasons joined with ` | `.

A `disputed` row has `disputed: ` put at the start of its claim cell in the unit's table by `judges.py` (claim cell: the
first of `purpose`, `activity`, `operation`, `name`, `move`, `failure`, `measure` the table has, else the second
column). It overrides `proposed:` (`disputed: proposed: ...`).

## merge/ (merge.py writes)

- The map's root tables `subjects.csv` and `participation.csv` are rewritten from the unit folders plus the lead's own
  rows: elements numbered `S01...` in units.csv order, relationships `R01...` made from `calls.csv`, every unit-local
  id replaced. `row_id` is dropped. Same unit folders in, same map out, row for row. A relationship's `operation` is
  its call's `within` and its `sequence` the call's `sequence`, as written.
- `calls.csv` carries `within` and `sequence` because without them the merged map cannot say which request of the
  calling part a call belongs to, nor its order, and the views' questions about interactions go unanswered. A
  calls.csv without the two columns still merges, with them blank.
- `unmatched-calls.csv`: `call,from_unit,to_unit,protocol,operation,source,why`; `call` is `<unit>/<row_id>`.
- `summary.json`: `{"units": n, "rows": n, "elements": n, "relationships": n, "calls": n, "matched": n,
  "unmatched": n, "found_by_reader": n, "proposed": n}`.

## job/jobs.csv (jobs.py writes; everyone else only reads)

`item,step,state,tries,reason,session,updated`

`state`: `to do`, `running`, `done`, `blocked`. `reason`: the last failed check's output (first 300 characters) or
the reason given to `block`. `updated`: ISO time. The kit's steps per unit are `read`, `judge`, `fix`; the run has one
item `run` with step `merge`; an unmatched call adds item `call:<unit>/<row_id>` with step `reread`.

## job/lock.json

`{"session": "<id>", "last": "<ISO time>"}`

## What run_page.py reads

`RUN.md`, `PLAN.md`, `run-settings.json`, `units/units.csv`, `job/jobs.csv`, `job/lock.json`,
`judging/judgements.csv`, `merge/unmatched-calls.csv`, `merge/summary.json`, and whether `views.html` exists. Each may
be missing; the page says what is not there yet. From `RUN.md` it shows the Go line's state and the Scope line's words.
Once every step in `job/jobs.csv` is done, it also runs the kit's done check (`run_status.py`, which reads the whole
register and the session transcripts): the page says finished only when that check says DONE, and otherwise lists the
check's reasons. A unit with no line for a step in `job/jobs.csv`, while it has a later one (the flow unit has no read
step), shows a dash for that step.
