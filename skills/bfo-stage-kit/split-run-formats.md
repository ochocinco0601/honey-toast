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
  prompts/                   the agents' prompt files and launcher files (below)
  merge/unmatched-calls.csv  written by merge.py
  merge/summary.json         written by merge.py
  merge/ids.csv              the finished flows' merge resolution, written at a flow's finish (below)
  job/jobs.csv               written only by jobs.py
  job/lock.json              written only by jobs.py
  job/events.log             written only by jobs.py, one line per change, appended
  job/timings.csv            written only by timings.py, rewritten whole throughout the run (below)
  run.html                   the sponsor's page, written only by run_page.py
```

## run-settings.json

```json
{"judges": 3, "judge_rounds": 2, "unit_lines": 4000, "parallel": 6, "merge_rereads": 50,
 "lock_stale_minutes": 20, "relaunches": 2, "on_change": "python run_page.py {reg}", "reading": "path"}
```

`reading` is how a flow read by stage reads its units: `path` (the default) reads the path of the stages taken past
mapped only, from starting points derived by script (`path_reading.py`), and lists every other file `not read` with
`off this stage's path`; `full` reads every line of every unit, as before. Changing it is the one change that switches
back.

`relaunches` is how many times an agent an API error stopped (its transcript ends on Claude Code's API error reply,
or on retries of a failed request with nothing after them) before its owed output was written is launched afresh
for the same prompt; 0 is none. Past it, run control stops on a problem it names to the person.

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
| `files.csv` | `path,status,reason` (no `row_id`) | every file the unit owes (`reading_check.owed_files`, listed in the reader's prompt: the files of the unit's paths but test code, generated and build output, vendored, binary, lock and minified files), and any other file the reader lists: `status` is `cited` or `not relevant`, or, when the unit reads a stage's path, `not read` with the reason `off this stage's path` (never counted as read, never cited); `reason` required for `not relevant` (`test code` for a test file) |

`source` cells (and any free text) cite code as `path:line` or `path:first-last`, paths relative to `<ws>`, exactly as
the kit's reading check parses them. A row whose claim is an inference starts its claim cell with `proposed:`.

## A finished flow's unit rows, and correcting them

A unit is per deployable, so every flow that crosses it reuses `units/<unit>/`. A later flow's reader appends rows
with new `row_id`s and never edits or deletes a finished flow's row. When a flow is finished, its unit rows are kept
under `earlier-flows/<flow id>/judged/units/<unit>/<table>.csv` (`go.py`, at the next go; never `files.csv`), and the
done check is NOT DONE on any of them changed or gone, unless the change is recorded:

- `corrections.csv` and `corrections-applied.csv` have a column `unit`, last: blank for a row of a root table, the
  unit's id for a row of `units/<unit>/<table>.csv`. For a unit row, `row` is its `row_id`.
- Every correction to a unit's row (a cell, a removal, an added row) is the person's, and takes `--words "<their
  words>"`: go.py refuses it without them, and refuses words the person did not type into a session after the go (a
  user turn of a main session's transcript, never a tool result; `--transcripts DIR` names where to look, else the
  workspace's Claude Code project folders), naming the transcripts it searched. A change the lead finds a unit row
  needs goes to that unit's fixer (`readers.py prompt ... <unit> --mode stop --reason "..."`), never through a
  correction.
- `go.py --apply-correction <id> --value <v> --words "<their words>"` changes the cell in
  `units/<unit>/<table>.csv`, found by `row_id`, and records it with their words. The freeze matches a recorded correction on (unit, table, row), so a correction to one unit's row never
  applies to another unit's row, nor to a root row.
- `go.py --apply-correction <id> --removed` removes the row (a root row by its key, a unit row by its `row_id`) and
  records the removal: `column` blank, `before` the row as it was (JSON), `after` `(row removed)`. It takes no
  `--value`. The freeze accepts a finished row gone only when its removal is recorded so. In a split run the root
  `subjects.csv` and `participation.csv` are the merge's output, so a removal of one of their rows is refused: the
  unit row it comes from is removed, and the merge withdraws the map's row and records it.
- `go.py --apply-correction <id> --added --words "<their words>" --value "<the row>"` with a `unit` adds a unit row
  the person states, and only that: it is refused without their words. go.py writes the row into
  `units/<unit>/<table>.csv` itself, from `--value` (one CSV line in the table's columns, its `row_id` the one the
  correction's `row` names), and refuses a row already in the file: no other hand writes it first. The record holds
  the row's content and their words: `column` blank, `before` blank, `after` the row (JSON), `words` their words.
  provenance.py accepts that row only while it holds that content, with any later recorded correction to it (or as
  a later Edit the transcripts show changed it), credits it to the person's words, and counts it as a row of the flow
  worked now: judged, and its unit owed the reading check. A recorded addition with no `words` fails the unit: no
  typed reader or fixer wrote the row, and nobody stands behind it. A row the lead finds missing is never added so.
- `corrections-applied.csv` has a column `words`, last: the person's words on the change (required on every unit correction; given on a root
  correction when there are any), blank otherwise.
- `units/units.csv` is what `units.py` derives: for every service the go took in (and every service surveyed after the
  go that it did not leave out: code got for an external dependency, owed its reader like any other), the units, their deployable and
  the paths each covers are exactly those `units.py` lists (a finished flow's list kept as it is, from
  `earlier-flows/<flow id>/judged/units/units.csv`). The done check and `go.py --mapping-ends` name any difference
  and refuse, so a service of the go's scope never goes without a unit and its reader.
- The one change a finished unit row may take unrecorded is the `disputed: ` label on a call's `operation`, put there
  by the re-read of that unmatched call, and only while merge.py's re-read check resolves that call.

## Who wrote a unit's tables (provenance.py)

Every cell of `units/<unit>/*.csv` (never `files.csv`) is accounted for by a write the transcripts show, or the unit
fails, whatever wrote it: a shell by absolute path or by `cd` and a relative one, a script, another tool.

- **Writers.** Every session that wrote into `units/<unit>/` with Write, Edit or MultiEdit, judged by the tool's
  resolved `file_path` and never by a shell command's text, is a `bfo-unit-reader` subagent (the kit's
  `agents/bfo-unit-reader.md`, whose tools hold no shell, so it cannot run one): its transcript
  `<main>/subagents/agent-<id>.jsonl` has `agent-<id>.meta.json` beside it reading `"agentType":"bfo-unit-reader"`.
  A main session (the lead's own Write), a `general-purpose` subagent or a fork fails the unit. No meta file, or no `agentType`, fails it with "no
  agent type recorded (Claude Code older than the meta files?)".
- **Two kinds of writer.** The unit's reader or a fixer of it writes under `units/<unit>/` only, and its Reads are
  the unit's reading (`reading_check.py --unit`). The re-read of an unmatched call writes `units/<a>/calls.csv` and
  `units/<b>/operations.csv` of one other unit, nothing else; it changes at most one row of the calls file and adds
  at most one row to the operations file, changing none there. It is credited for provenance and never as either
  unit's reader. A session that wrote only `units/<a>/calls.csv` is of the first kind, unless all it changed there
  is `disputed: ` put at the start of a call's claim cell: that is the re-read on the calling side alone, likewise
  never a reader (fixers never write the label; `collect` does). Any other set of writes fails every unit it wrote
  into.
- **No shell.** A reader or fixer whose transcript shows a shell call (Bash or PowerShell, even a read-only one) is
  left out: its writes are not replayed and its Reads credit nothing, so the unit fails while anything it wrote is on
  disk, naming it. `readers.py prompt <reg> <unit> --mode read|fix --again` relaunches it: each table it wrote is put
  back as the unit's clean writers left it (on a reused unit, the finished rows with their recorded corrections and
  removals; a table nothing clean wrote, and `files.csv`, removed), then its prompt is written afresh. Once the
  relaunched agent's writes account for every cell, the one left out is named in a note only.
- **Launched on a prompt a kit script wrote.** A reader, fixer or re-read is launched with the pointer line of a
  prompt `readers.py` or `judges.py` wrote under `<reg>/prompts/`, and nothing else as its first message. Each such
  file is recorded in `prompts/emitted.txt` by the hash of its bytes, every version kept. A writer whose first message
  is anything else (a prompt the lead composed inline), or points at a file no kit script wrote or one changed since,
  is left out as a shell run is, named with why, and relaunched the same way (`--again`).
- **The flow worked now.** When a flow is finished (`earlier-flows/<id>/judged/`), a session counts only when its
  first timestamped transcript line is after the go of the flow worked now (`scope.json` `given`); a `given` that is
  not a date and time, or none recorded, fails the unit. So does one not later than the finished flow's own go (its
  record under `other_flows`, which must hold that go as a date and time), so a go backdated with `go.py --given`
  never lets the finished flow's sessions count. A finished flow taken up again (`go.py`, `taken_up` recorded) counts
  only sessions after the later of its own go and that time. A finished flow's pass is its judged snapshot, never
  re-checked from its transcripts.
- **The replay.** Each table is replayed from the latest finished flow's judged snapshot of it (the flow
  `started_from` names), else from empty: every successful Write, Edit and MultiEdit of the flow's sessions on it, in
  transcript timestamp order (a write with no timestamp fails the unit), the byte order mark stripped and line endings
  normalised. An Edit whose old text is not in the file as replayed, nor in it as Python's csv module writes it out
  again, is tried once more on the replayed rows with the unit's recorded corrections applied, since `go.py
  --apply-correction` rewrites the file outside any transcript; the corrected cells keep the session that set them
  before. Found in neither, it stops the replay, naming the session. The replayed rows, by `row_id`, equal the file's,
  cell by cell, except for a unit correction recorded in `corrections-applied.csv` (a cell changed, the row removed,
  or a row added that still holds its recorded content) and `collect`'s `disputed: ` label at the start of the claim
  cell of a row its verdicts make disputed.
- `files.csv` is written whole by each flow's reader with Write; it is never judged, never a source of rows, and left
  out of the replay.
- Prompt files are written under `<reg>/prompts/`, never under `units/` (below).

## prompts/ (the agents' prompts, written by judges.py emit and readers.py prompt)

The run's agents are subagents launched through launchers (themselves `general-purpose` subagents): readers,
fixers and re-reads as `bfo-unit-reader`, the kit's reader agent with no shell among its tools, which must be
installed where Claude Code finds agents (`.claude/agents/` of the folder it starts in, or `~/.claude/agents/`;
`readers.py prompt` refuses until the copy it would use is the kit's); judges as `general-purpose`:

```
<reg>/prompts/<unit>/<verdict file stem>.md   one judge's prompt (judges.py emit)
<reg>/prompts/<unit>/read.md, retry.md, fix.md one reading unit's reader or fixer (readers.py prompt --mode ...)
<reg>/prompts/flow/fix-<table>.md             the fixer of one lead table's flagged rows (readers.py prompt flow
                                              --mode fix)
<reg>/prompts/<unit>/reread-<row_id>.md       the re-read of one unmatched call of the unit (readers.py prompt
                                              --mode reread)
<reg>/prompts/launch/<name>-<i>.md            one launcher: its instructions, then one pointer line per agent
```

- A **pointer line** is `Read <prompt file> and do exactly what it says. Reply with one line.`, the prompt file's path
  absolute with `/`. It is the whole prompt of one agent.
- A **launcher file** holds at most 150 pointer lines (`judges.LAUNCHER_MAX`: a launcher's own context grows about
  1,200 tokens per agent it launches). It tells the launcher to launch each line once as a `bfo-unit-reader` subagent (a
  readers' launcher) or a `general-purpose` one (a judges' launcher), never a fork nor any other type, in the foreground, at most `parallel` at once, and to reply, once every agent has finished, with one
  line `launched <n>, finished <n>`. Names: `judges-<unit>-r<n>-<i>`, `judges-flow-r<n>-<table>-<i>` (the unit `flow`
  is always split by lead table), `readers-<mode>-<i>`. Readers, fixers and re-reads share launchers. Writing a name
  removes that name's earlier launcher files except a launcher still running, which is left as it is, byte for byte,
  its name taken by no new file.
- `emit` and `prompt` print a count line naming how many launchers the lead keeps running at once
  (`judges.launcher_cap`: 20 // (`parallel` + 1), since each launcher is a subagent holding up to `parallel` more and
  a session holds at most 20), the agents held and why, then one pointer line per launcher; the lead launches each as
  a `general-purpose` subagent. `emit` writes a judge only for a verdict file not on disk; `prompt --mode fix` writes a
  fixer only for a unit, or lead table, with flagged rows; `prompt --in-scope` adds every unit of a service the go took
  in whose `files.csv` is not newer than the go.
- **Run again, neither launches an agent twice** (`judges.Launches`). A session was given a prompt file when its
  transcript's first message is the file's pointer line and it started after the file was last written and after the
  go of the flow worked now. An agent is held, never printed, while it is listed in a launcher still running (given
  its pointer, with no reply line yet), whether started or not; while it is still running; and once it finished, for
  the same prompt (a fixer given the same rows with other reasons is the same fixer). One still running when its
  launcher has replied stopped without replying, and is printed again, its prompt rewritten so the stopped session no
  longer counts. A held prompt file is never rewritten. `--again` says the lead's session is gone (a crash, a
  restart): every agent and launcher still named running died, so those agents, and those that ran a shell, are
  printed again; a finished one never is. A judge that finished without its verdict file is named; deleting its
  prompt file launches it afresh.
- Every prompt names the workspace (`Workspace: <ws> ...`, `--ws`, else the register's grandparent): citations are
  relative to it, whatever folder the session runs in. Every reader and fixer prompt ends with the tool rule: `Use no
  shell (no Bash, no PowerShell). Write only with the Write and Edit tools, and only under your own unit folder
  <reg>/units/<unit>/` (a `flow` fixer: `only to your own table <reg>/<table>.csv`; a re-read: `only to
  <reg>/units/<a>/calls.csv and <reg>/units/<b>/operations.csv`), then `Reply with one line.` A re-read's prompt opens
  by naming its kind: `You are a re-read of one unmatched call, not the reader of a unit`.

## Row keys (what a judge judges)

A row is `(<unit>, <table>, <row key>)`. In a unit folder the row key is `row_id`. The unit `flow` is the lead's
rows: an allowlist of mapping's lead tables at the root (`flows`, `lifecycle`, `stages`, `steps`, `set-aside`,
`agent-system`, `capabilities`, `step-impact`, `case-attributes`; `judges.FLOW_TABLES`) and the lead's own `subjects`
and `participation` rows in `merge/lead-rows/`; never the measures step's tables (`measures`, `measure-gaps`,
`expectations`, `alerts` and the rest) nor the merged root `subjects` and `participation`. Its key is `go.row_key`'s:
the key columns of `go.ROW_KEYS` joined by ` · ` where that names the table (`step-impact`: `1 · revenue`), else the
first column's value; `#2`, `#3` are added to repeats in file order. `files.csv` is never judged. A row with no code
citation is not judged and is counted as such.

Only the flow worked now's rows are judged, collected, labelled and counted. A row is a finished flow's when the
latest finished flow's judged snapshot holds it as it is now, recorded corrections applied and `disputed: ` set aside:
a unit row matched by `row_id` (`provenance.current_rows`), a row of the unit `flow` by its whole content. The judged
snapshot is `earlier-flows/<id>/judged/`, written when a flow is kept (`go.keep_judged_rows`): the unit tables
(`units/<unit>/`), mapping's lead tables at the root, `capabilities` and `set-aside` included, and
`merge/lead-rows/`.

A fixer of the unit `flow` (`readers.py prompt <reg> flow --mode fix`, one per lead table with flagged rows) is a
`bfo-unit-reader` subagent that writes that one table and nothing else, and runs no shell; `judges.py --check <reg>
flow` fails one that does not, naming it, until a clean fixer of the same table is launched after it. The lead's own
writes to the root tables (a main session) are not a fixer's and are not checked so.

## judging/<unit>/ (verdict files)

One file per judge per row per round, at the row's content as it was judged:
`judging/<unit>/r<round>-j<n>-<table>-<name key>-<row hash>.csv`, one data row:

`unit,table,row,round,judge,flow,row_hash,verdict,reason`

- `flow` and `row_hash`: the flow worked now (`go.flow_key`: its id in `flows.csv`, else its name made safe for a
  folder; blank before any go) and the row's hash, as the judge's prompt gives them in its data line. The judge writes
  them, so they are the judge's own record of what it judged: a verdict is current only when its `row_hash` is the
  row's hash now and its `flow` is the flow worked now, whatever its file name says. A verdict of another flow never
  counts toward this flow's rounds. The round record (`r<n>-rows.csv`) is checked against the `row_hash` the verdicts
  carry, not against their file names, which the lead's script chose. A file with the earlier seven columns is not a
  well-formed verdict file.
- `<row hash>`: the first 12 hex characters of the SHA-256 of the row's cells (padded to the header, `disputed: `
  stripped from each, so the label `collect` adds never makes a verdict stale), serialized as a JSON list. Because
  the cells are padded to the header, adding a column to a table makes every verdict of that table stale.
- `<name key>`: the row key with every char outside `[A-Za-z0-9_-]` replaced by `_`; a key longer than 40 characters
  is replaced by the first 12 hex characters of its own SHA-256, so a long composite key in a deep workspace stays
  under Windows' 260-character path limit. The key itself is always in the file's `row` column.
- A verdict file belongs to a row by its own `unit`, `table`, `row`, `round` and `flow` columns. Files are found by the
  anchored name `^r<round>-j<n>-<table>-<name key>-[0-9a-f]{12}\.csv$` and then matched on those columns, since the
  name key is lossy (`a/b` and `a_b`) and keys contain `-` (`M1`, `M1-retry`). A file that cannot be read is
  claimed by every row its name matches, and counts as a flag.
- Rounds are counted by the row's identity (unit, table, row key); the hash only says whether a verdict is current.
  Round n judges the rows whose round n-1 verdicts, at any hash, flagged them; a fix changes the hash, never the row's
  place in the rounds. A round is passed at n verdicts at the row's current hash. Verdicts at an older hash are listed
  as stale, never failed.
- `--check` of round n checks the rows in its scope, and every other row of the unit at its own latest round with
  verdicts, at its current content. So a row edited with no flag in between, added, or re-keyed, at any time, is
  NOT DONE until it is judged again: in the round where it stands, or round 1 for a row with no verdicts. A row flagged
  in round n and fixed is due in round n+1, except in round `judge_rounds`, where it is judged again in that round and
  stays disputed. A round with verdict files and no row in scope fails (old names, or rows re-keyed or withdrawn).
  Verdict files of a row that no longer exists are otherwise not read.

`verdict` is `says`, `does not say` or `unclear`; anything but `says` flags the row. The file is written by the judge
session itself with the Write tool, and that session writes nothing else. A Write or Edit whose tool result is an
error is not a write. The file's **effective writer** is the session whose successful Write content, parsed as CSV
(BOM and line endings normalized, `disputed: ` stripped), equals the file on disk; when several do, the latest by
transcript timestamp. Other sessions that wrote the path are superseded. A superseded writer whose own Write was a
well-formed verdict naming this row, round and judge, from a clean session (only that file, no shell, every cited line
opened), fails the check: a clean verdict was replaced, by a re-rolled judge, say. Any other superseded writer (one
that ran a shell, wrote a malformed file) is named in a note. A verdict file no successful Write matches (overwritten
by a shell or an Edit) fails. A judge is relaunched onto the same path (`judges.py run --again`) only after the failing
file is removed, never by having the new judge Read it: the new judge must not see the old verdict, and the Write tool
refuses to overwrite a file the session has not read. `--again` never removes a failing file no transcript found here
wrote: it refuses, naming the file, since its verdict could be a flag. Nor does it remove a file whose clean verdict
was replaced: a relaunch would only replace it again. It names the file and the clean judge's session, whose Write
content, in its transcript, is restored to the file by hand.

Every judge, under `emit` or `run`, must be a `general-purpose` subagent, read from its meta file as for a unit's
writers (`provenance.agent_type`): a fork, a main session, or no agent type recorded fails its verdict with the cause
named. A `claude -p` judge (`judges.py run`) has no meta file, so it fails this check.

## judging/<unit>/r<n>-rows.csv (the round record, judges.py emit writes)

`unit,table,row,hash,header,cells`

Every row in the round's scope when `emit` runs: its identity, its row hash, and its header and cells as JSON lists.
A row already recorded keeps its record once any verdict of the round names it, so the record is the round's
before-state; verdict files hold no cells, and the judged snapshot is taken after the fixes. It is derived: never
fingerprinted. `--check` checks it against the judges' own files: each recorded row's cells must hash to its recorded
hash, and that hash must be one the row's verdict files of that round carry; a record edited after its verdicts (to
hide a withdrawal, say) fails.

`--fix-check` classifies every row a round before the last flagged (read from the verdict files' own columns), from
its recorded cells and the row as it is now: `claim narrowed`, `citation changed`, `relabelled proposed`, `citation
dropped`, `withdrawn` (no row of that identity now: a key changed counts as withdrawn, and the new key is a new row,
unjudged), or `unchanged`; with no record, `not classified: no round record`. The counts are printed in plain words
(`Fixes of round 1's flagged rows: 2 claim narrowed, 1 withdrawn`). A relabel, a dropped citation or a withdrawal is
never counted as fixed. A fixer never changes a row's key columns.

## judging/judgements.csv (judges.py collects)

`unit,table,row,round,judges,says,flagged,state,reasons`

One line per row, for its latest round. `state`: `pending` (fewer than `judges` verdicts this round), `passed` (all
say), `flagged` (any flag, rounds left), `disputed` (flagged in round `judge_rounds`). `reasons`: the flagging judges'
reasons joined with ` | `.

A `disputed` row has `disputed: ` put at the start of its claim cell in the unit's table by `judges.py` (claim cell: the
first of `purpose`, `activity`, `operation`, `name`, `move`, `failure`, `measure` the table has, else the second
column). It overrides `proposed:` (`disputed: proposed: ...`). A disputed call the merge leaves unmatched is the
exception: `collect` leaves it unlabelled and its re-read labels it (merge.py), since a label with no session behind
it is one no re-read could ever resolve.

The done check runs after the last `collect`, so the last `disputed: ` label is on the map before its verdict is
stored.

## The stored verdicts and their fingerprint

`done-check.json` (run_status.py) and, at the end of mapping alone, `mapping-check.json` (go.py --mapping-ends:
`{"passed": true, "flow": <id>, "tables": ...}`) keep a verdict with the fingerprint of what it judged: the map's root
tables, `units/units.csv` and every unit's tables (never `files.csv`), and the verdict files under `judging/<unit>/`
(never `judgements.csv` nor a round record `r<n>-rows.csv`, which are derived). Each file is read as rows, so a
byte-order mark, line endings or quoting change nothing, and a `collect` with nothing new leaves it as it was; a new
`disputed: ` label changes it. A verdict holds only while the fingerprint is unchanged. In a split run no flow is
finished, and no next flow opens, unless its split checks passed: through the done check, or at the end of mapping
alone through `mapping-check.json`, which keeps the flow finished after its transcripts are gone.

## merge/ (merge.py writes)

- The map's root tables `subjects.csv` and `participation.csv` are rewritten from the unit folders plus the lead's own
  rows: elements numbered `S01...` in units.csv order, relationships `R01...` made from `calls.csv`, every unit-local
  id replaced. `row_id` is dropped. Same unit folders in, same map out, row for row. A relationship's `operation` is
  its call's `within` and its `sequence` the call's `sequence`, as written.
- `calls.csv` carries `within` and `sequence` because without them the merged map cannot say which request of the
  calling part a call belongs to, nor its order, and the views' questions about interactions go unanswered. A
  calls.csv without the two columns still merges, with them blank.
- `unmatched-calls.csv`: `call,from_unit,to_unit,protocol,operation,source,why`; `call` is `<unit>/<row_id>`.
  Each row is owed a re-read on both sides, and the run is NOT DONE until each is resolved: corrected, so the next
  merge matches it, or, when the called unit serves nothing that matches, its `operation` in the calling unit's
  calls.csv starts `disputed: `, written by a re-read the transcripts show (one call per re-read session). A call
  whose called side is not a unit (`to_unit` names none, or neither `to_unit` nor `to_part` is set) is resolved only by
  correcting it; one with no `to_unit` may be disputed on its calling side only, and is shown so. Above `merge_rereads`
  calls not resolved,
  the done check says to read again the units they call. `merge.py --reread-check <unit>/<row_id> <reg>` is the check
  for one call (merge.py's docstring holds the rule).
- `ids.csv`: the resolution record, written by go.py (merge.py `write_record`) when a flow is finished, never by a
  merge: `record,unit,local,row_id,broker,topic,removed,consumed` and then the whole output row (the `subjects.csv`
  columns). A recorded row no longer given stays in the record, `removed` `yes` when its removal is recorded: a
  tombstone, so its id is never given again. An element's record is its own row's (the same `row_id`); a local id a
  later reader gives to a new row is a new element, and a unit row whose own record is a tombstone fails `--check`.
  `consumed`: the corrections to the unit row already in the record row, so a correction re-matches a finished call
  once, never again in a later flow.
  `record` is `element` (keyed unit and unit-local id, `row_id` its row), `external` (`local` the `external:<name>`),
  `out of scope` (`local` the service), `call` (unit and its `row_id` in `local`) or `consumer` (`local` the consumer
  element's map id, `broker`, `topic`; one row per relationship). A later merge writes each recorded row as recorded,
  with the root corrections recorded to it applied, numbers new ids from one above the highest in `ids.csv` and the
  lead's rows, and records in `corrections-applied.csv` each change it makes to a finished row (a unit row
  corrected or removed, a service left out earlier and read now, a consumer's step_hint grown, a consumer withdrawn
  when its operation row is corrected or removed). A correction to a finished call re-matches it only when it changes
  `protocol`, `operation`, `to_unit`, `to_part` or `via`; any other cell corrected is carried onto the recorded row.
  `--check` fails on a `subject_id` used twice. merge.py's docstring holds the rule.
- Out of scope. A unit units.csv lists with no folder, whose deployable no flow's go so far took in (`services_in`
  of any flow in `scope.json`), is out of scope: not missing from the merge, not judged, and a call to it, or to a
  service no unit has that some go left out (`services_out`), goes to `out-of-scope-calls.csv` (the columns of
  `unmatched-calls.csv`), never to `unmatched-calls.csv`. A unit with a folder is always merged. A listed unit in
  some go's scope with no folder is missing: its reader has not run, and the run is NOT DONE.
- `summary.json`: `{"units": n, "rows": n, "elements": n, "relationships": n, "calls": n, "matched": n,
  "unmatched": n, "found_by_reader": n, "proposed": n}`.

## job/jobs.csv (jobs.py writes; everyone else only reads)

`item,step,state,tries,reason,session,updated`

`state`: `to do`, `running`, `done`, `blocked`. `reason`: the last failed check's output (first 300 characters) or
the reason given to `block`. `updated`: ISO time. The kit's steps per unit are `read`, `judge`, `fix`; the run has one
item `run` with step `merge`; an unmatched call adds item `call:<unit>/<row_id>` with step `reread`, whose check is
`python merge.py --reread-check {item} {reg}` (it takes the item as it is, `call:` and all).

## job/timings.csv (timings.py writes; rewritten whole)

`unit,step,attempt,agent,model,start,end,seconds,turns,input_tokens,output_tokens,cache_read_tokens,cache_creation_tokens,api_errors,longest_gap_seconds,gap_ends_on_error,outcome,prompt`

One row per agent attempt the run launched (readers, fixers, re-reads, judges, launchers, and the lead's own
helpers), read from the agent's own transcript. How each column is computed is in timings.py's docstring. It is kept
current with no one asking: next.py rewrites it each time run control is called (each launch, launcher reply, wait
and stop), and start.py, `readers.py --again` and `judges.py emit --again` rewrite it first when a run is picked up
after a crash or a restart. Launchers run no shell, so nothing writes it between run-control calls. A failure to write it is logged to events.log and
never stops the run. The command can still be run on its own at any time.

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
