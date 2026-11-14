# Known gaps

## The session's own words

- **A message that asks you something can open with a status line saying nothing waits on you.** Read the
  question itself: when a message asks you something, the run is waiting on your answer.

- **A system whose name looks like the kit's shorthand can be refused before the run has recorded it.** Until the
  first look writes the system's names down, the check on the session's own words knows only the kit's words: a
  system called "Unit Manager" or "Receipts" is named in quotes, and one whose name looks like an id ("S3 uploader")
  may have to be described rather than named in that first message.
- **A unit of stock, a receipt, a cash register or a merge of baskets in the session's own sentences** is refused
  unless the register itself uses those words, so the session says them another way.

## The home screen

- **A topic tick that could not be put back is counted, not named.** Words are quoted on the line at the top; a
  tick is only counted ("1 tick"), and the line says what it was about is gone even where that place now asks for
  your choice.
- **Clear in one drop-down can leave a later milestone without its earlier ones.** For example: tick Alerts, then
  Runbooks in its own drop-down, then Clear in the Alerts drop-down. Runbooks stays ticked alone. A Done is then
  refused with the reason and nothing is recorded; tick the earlier milestones and send again.
- **Two answers on their way at once, the first refused:** a change made after the second press can be taken as
  sent. It needs a refused answer, which the page does not cause on its own.
- **A browser set to send no page address with its requests files every answer under the work folder, not the
  run's own folder,** so the session is not told of it; the page still says it was saved. Say "read it" in the chat
  and the session reads it from there.
- **If your browser unloads the page's tab to save memory, or closes without warning, a tab you close later may not
  be opened again.** Open the address the session gives you in the chat to bring it back.
- **Stopping the page's listener at a run's end stops the page of any other run in the same work folder.** Run
  `wait_on_page.py` for that run again to bring its page back.
- **The kit's instructions do not yet describe Clear, the line about ticks and words put back, or the quoted
  words,** so a session asked why words did not come back answers from the page's own line, not from the
  instructions.

## Picking how far each stage goes

- **Taking stages further on a finished register is not supported yet.** Nothing routes a run started on a register
  whose run is done back to the pick of how far each stage goes: it maps again into a new folder, and a second go
  would record its scope without the earlier pick. Until it is, pick every stage's depth in the one run, at the pick.
- **Taking a stage less far than already picked is refused,** because the pages already written for it would stay.

## The reviews

- **The review of the alerts accepts a go on alerts the person was not shown.** The review of the measures refuses
  a go until the measures have been shown (`brief.py measures`), and refuses one on measures that changed since. The
  review of the alerts refuses only a go on alerts that changed since they were shown: where they were never shown,
  it takes the go. Show the alerts before recording the answer on them. Making that review as strict is for the
  later work on choosing the alerts.
- **A register migrated from an earlier release can have measures that do not say which flow they were proposed
  for.** Where the migration cannot place a measure, `for_flow` is left blank and the inspection of the measures
  (rule 6) reports each one; the rows are filled the next time that register is run.
- **Migrating an older register can give a part's measure the wrong flow.** Where a measure has no stage, the
  one-time fill of `for_flow` (`reconcile.py --migrate`) takes the flow whose kept copy first held it, ordered by
  when each flow's go was given. On a register where a flow was taken up again and finished again before the
  migration, that order can name a later flow. The fill runs once and lists each row it filled: on such a
  register, check those rows and correct any that name the wrong flow.
- **The check of the alerts does not look at an alert placed on a process step.** It reads a stage's alerts by the
  stage they name, so for an alert on one of the stage's process steps it does not check the moves it says it
  watches, and its warnings about what the stage's alerts cover leave that alert out. Read each such alert's moves
  against the moves of its stage yourself.

## How far to trust a run

Check the parts: a process step's dependency on a database can be left out, or a mobile app drawn as a web front end
(the eShop example below still has this one). Check hardest what the code does under failure: what a test would
show, where a restore leads, and what a log really records. Treat the runbook as a draft for the code owners to correct before anyone
relies on it.

What the done check proves about reading, and what it does not. It proves that every cited line was opened by the
run with the Read tool, or produced by the code reader, and that a sample of rows was re-read by an agent that wrote
none of them and found true. It does not prove that every line opened was understood: a row can cite lines that
were read and still misstate them, and the sample of ten finds that only where it lands. A redraw keeps the rows
that failed and draws new ones for the rest, so a fix is followed by fresh rows. The record it reads is
Claude Code's own session transcripts; their layout is Claude Code's, not the kit's, and a release of Claude Code that
changes it would leave the check finding no record (it then says so and fails, never passes). The code reader finds
only the coding patterns its rules cover, and joins a call between services only where its rules resolve every hop
to the service it reaches (`fact-extractor/README.md`, "The join"); other calls rest on the run's reading. The
instructions say such a call cites both ends, the call and the operation that receives it; no check holds that yet.

## Naming where a measure is counted

- **The check knows product names from a fixed list.** A product written with a capital in the middle of a word
  (such as a middleware or monitoring product) passes only when the list holds it; one it does not hold is taken for
  a name only the code knows, and the run is not done until the run declares it in the register's
  `product-names.csv`, with where its vendor or the sources write it so. The run vouches for each name it declares;
  check the declared names when you review the register.

## At scale

On a stage that many services carry, an alert's entry is long even when written as sweeps, and listed part by
part it is several times longer.

- **An entry is still long at that size.** Sweeps, shared dependencies first, and a called service's databases
  reached through its tests shorten it, but at that size it is still a long walk. A called service with no test of it
  answering with an error or slowly keeps its databases as tests of their own.
- **Nothing checks a sweep's command.** The check confirms only that a sweep's parts are of one kind, each in a
  listed move. Whether its command reaches every part and names the one that matched is the drafter's to verify.
- **What checking every finding cannot see.** Mapping reads each service in its own reading unit, and every row
  that cites code is checked against its cited lines by readers who wrote none of it. That check sees only the rows
  written and the lines they cite:
  - **Missing rows.** A step, part or call no reader wrote is never judged. Only the reading check (every file of a
    unit opened, or listed as not relevant with the reason) and the map's inspection bear on what is missing.
    Nothing cross-checks the lifecycle against the participation rows either: a service the lifecycle names as
    carrying a step can have no participation row for that step, and nothing flags it (for example, a step whose
    lifecycle names a shipping service as a carrier, with no participation row for it).
  - **Claims true at the cited lines and false given code elsewhere.** A judge judges a row against the lines it
    cites, so a claim those lines support but code elsewhere contradicts (an override, a later branch, a setting
    that changes it) passes.
  - **Rows with no citation** are not judged: they are labelled `proposed:` or name what no code could show.
  - **A row still in doubt after the last round** stays on the map labelled disputed, shown as not confirmed by the
    code, never as fact.
  - **The flow-level rows are written by the session that talks to you, and nothing checks who fixes them.** The
    case, its lifecycle, stages, process steps, Business Impact and the like are the session's own rows, by design.
    The rule that a flagged row is fixed only by a separate fixer is checked for the services' rows, never for these:
    if the session edits a flagged flow-level row itself, the edit is judged again like any fix, but nothing records
    that it was not a fixer's.
  - **"No hand-written rows" for the services' rows rests on Claude Code's transcripts, against a careless session,
    not a determined one.** A service's row is written by a reader or fixer launched on a prompt the kit wrote, or
    changed by a correction in words you typed into the session; the check refuses the session's own Writes, shell
    writes, agents it dictated a prompt to, and words you never typed. It does not stop anyone who edits the record
    files by hand: `corrections-applied.csv` or `prompts/emitted.txt` changed by hand would pass.
  - **A problem in a service's row found by the map's own inspection goes to that service's fixer**, which reads the
    code again and changes or adds the row, or says the code does not show it. One the code does not show is named to
    you as still open when mapping stops.
- **No limit on how much of the computer a run uses.** A run launches its readers and judges many at once, and
  nothing holds them back when the computer runs short of memory, so a run on a large capability may leave the
  computer slow. Claude Code itself stops work running in background shells when the computer is low on memory.
- **No rule for one flow carried by parallel sets of services.**
- **Several repositories are not yet proven on a large capability.** Citations from the workspace root are checked
  against `sources.csv`; a capability spread over many repositories is not yet proven. A shared library's version is cited from
  the service's manifest, and nothing checks that the cited version is the one deployed.

`USE.md` says how to scope a run on a large capability.

## Open in the eShop example

- **M28** is named for orders cancelled because payment failed, but it counts the Payment Processor's publish
  attempts. That line is written even when the publish fails, so it also counts stranded orders.
- **ClientApp** is drawn as a web front end. It is the mobile app.
- **RM1** sends orders back to `Submitted`, so the ones already in `StockConfirmed` pass through payment again, with
  no guard. It is safe only because payment is simulated, and the runbook does not say so.
- **Log tests use `az containerapp logs show --tail 300`.** By the time someone is paged, the failure lines may
  have rolled out of those 300. The procedure requires "a search over the alert's window ... never a tail of the
  last lines" (FILL-STEPS Step 11); the example's log tests tail 300 lines instead.

Failure-mode ids (`FM..`) are the register's; each runbook test names the mode it comes from.

## Open in the kit

- **The register's lock tells sessions apart, not the helpers inside one session.** A run is named by the session
  id Claude Code gives each session and the shells of its helpers. Two helpers one session starts at once carry the
  same id, so the lock does not stop them writing one register together. A second start step while a first look is
  under way is refused ("the first look is already running", until its brief, or for 45 minutes at most), but two
  helpers started from one start step are not, nor two helpers on one register after the brief.
  Two scripts write into the register without checking the lock: the code reader (`fact-extractor/run.py`), a
  separate program the kit runs as it is (`fact-extractor/README.md`, "The join"), and the page's listener, which
  writes only the answers the person sends.
- **The lock guards the kit's scripts, not the tables the assistant writes by hand.** A script that writes the
  register refuses another chat's fresh lock, but the assistant's own edits to the tables and to `RUN.md` check
  nothing. A chat that goes on after a refusal, or after being told another chat holds the work, can still
  overwrite by hand.
- **A register made before the kit's run record had its *Earlier registers* section is not picked up.** The start
  step tells this kit's runs by that section; an older register without it is treated as an earlier register, and
  the run starts fresh beside it and reconciles it at the end.
- **Where nothing names the run, the lock does not guard the register.** With neither Claude Code's session id nor
  `BFO_RUN` set, the run still goes on: the start step decides whether to pick up earlier work or start fresh, and
  every script writes. No lock is taken or checked, and `RUN.md` records once that it was not, and why. A script is
  refused only when a lock no older than four hours names a run and the script runs as a different, named run. A
  register this kit made that has no lock is never refused for lacking one.

- **Building the map copies each stage's runbook and alert pages already in the register folder.** After you change a
  register, or take up a new kit version, regenerate each stage's outputs before you build the map, or the map shows
  the old ones: `python <kit>/flow_outputs.py <register folder> <flow id> <stage id> --out <register folder>/stage-<stage id>`
  for every stage (the same command as the check in USE.md, "Before you take it to anyone", with `--out` in place of
  `--check`), then `python <kit>/one_canvas.py <register folder> <register folder>/views.html`.
- An earlier register is reconciled against the code, never built on (SKILL.md Phase 7). `reconcile.py` matches
  rows by what they say, so a row an earlier register worded differently is listed as a candidate or a disagreement
  rather than matched; and it checks that a cited line exists, not that it says what the row claims: the model reads
  each candidate at its line, and Step 11.6 reads every row added that way.
  Where a `--check` message names KNOWN-GAPS for a register made with an earlier version, the message says the
  fix itself; the in-place upgrade notes it once pointed at are history, in CHANGELOG.md, Release 2.
- The generated "What changed" test sends any change, an unplanned restart included, to a rollback through the
  change-approval path or the change owner. An unplanned restart has no change to roll back: escalate to the owner of the part that restarted.
- No worked example shows a stage whose work never waits (a chain of synchronous calls that succeeds or fails within
  seconds), where the alerts count cases leaving wrongly (the measures skill). The eShop example's stage waits, and proposes an alert on
  both kinds of loss.
- `flow_outputs.py --check` tests the register's structure and coverage. It cannot tell whether a citation says what
  the row claims: that is the verification pass in Step 11, which the assistant runs on its own work. That pass does
  not catch every wrong citation, so someone who did not draft the register checks a sample afterwards (USE.md,
  'Before you take it to anyone').
- **The runbook's tests have not been run.** Step 11 has the run write how to check each test against one known
  case, and never run it itself. Until the code's engineers have run each test once,
  on a case whose answer they know, read every test as a proposal.
