# Known gaps

## How far to trust a run

Check the parts: a step's dependency on a database can be left out, or a mobile app drawn as a web front end
(the eShop example below still has this one). Check hardest what the code does under failure: what a test would
show, where a restore leads, and what a log really records. Treat the runbook as a draft for the code owners to correct before anyone
relies on it.

## At scale

- **The runbook grows with the number of services until it stops being usable.** A test is written for each failure
  mode of each part a stage relies on, and nothing groups the tests (one "is any of these services down" check) or
  orders them by likelihood. For a stage that twenty services carry, one alert's entry can list close to a hundred
  tests. Nothing checks either that an alert can see the failures its tests explain.
- **Nothing splits the work.** The coverage receipt covers the whole flow, whichever stage is chosen. The
  verification pass re-reads every cited line. The procedure gives no rule for reading part of the code, or for
  sharing the run between sessions. Rows filled in bulk with generic citations still pass the check.
- **Several things multiply the rows silently.** Describing the fullest configuration can mean one database per
  service. There is no rule for how deep to follow the services a call reaches through other calls. One flow carried
  by parallel sets of services has no representation.
- **Several repositories.** A citation is a path inside its repository, so the same file name in two repositories is
  ambiguous unless the path starts at the workspace root. Nothing records which version of a shared library a
  service uses, and `sources.csv` needs one row per repository and commit.

`USE.md` says how to scope a run on a large capability until these are fixed.

## Open in the eShop example

- **M28** is named for orders cancelled because payment failed, but it counts the Payment Processor's publish
  attempts. That line is written even when the publish fails, so it also counts stranded orders.
- **ClientApp** is drawn as a web front end. It is the mobile app.
- **FM44 and FM46** (the ordering database or the broker down, in the shared tests) lead to the re-drive R1, which
  cannot run while either is down. FM11 and FM14, the same checks in the `Submitted` branch, lead to the real
  restores, R5 and R4. When a database reaches its connection limit, FM45 and FM49 say restore while FM13 says
  escalate.
- **R1** sends orders back to `Submitted`, so the ones already in `StockConfirmed` pass through payment again, with
  no guard. It is safe only because payment is simulated, and the runbook does not say so.
- **Log tests use `az containerapp logs show --tail 300`.** By the time someone is paged, the failure lines may
  have rolled out of those 300. The procedure requires "a search over the alert's window ... never a tail of the
  last lines" (FILL-STEPS Step 11); the example's log tests tail 300 lines instead.

Failure-mode ids (`FM..`) are the register's; each runbook test names the mode it comes from.

## Open in the kit

- The generated "What changed" test sends any change, an unplanned restart included, to a rollback through the
  change-approval path or the change owner. An unplanned restart has no change to roll back: escalate to the owner of the part that restarted.
- A register filled with an earlier version of this kit names the alerting column of `measures.csv` `pages`.
  Rename it to `alert`; until then no measure is proposed for alerting and no alert or runbook is written.
- A register filled with an earlier version of this kit fails `--check` until it has rows for the two newest
  failure modes, `call: callee answers wrongly` and `needs: answers stale or wrong`, and no alert or runbook is
  written until then. Add the rows (a `not possible here:` row with its reason is enough where the mode cannot
  cause what the stage's alerts count), and state the basis of each measure proposed for alerting as `yes:` and the reason.
- A register filled with an earlier version of this kit fails `--check` until its measure step's receipt is
  complete: every element FILL-STEPS Step 9 accounts for (the flow and each stage at business health, each step
  that matters asked both questions, each operation, each system component, each agent's decision points) is
  covered by a candidate in `measures.csv` or has a row in `measure-gaps.csv` saying why not (an earlier register
  has no `measure-gaps.csv`: copy it from `register-template/` first). That is intended:
  the failure lists the elements nobody had looked at. Mark the existing step measures in `receipt_question` and the
  operations they count in `operation` first; many elements are already covered.
- A register filled with an earlier version of this kit has no `receipt_question` column: add it, an empty `defect` column to `measures.csv` and a `decision_point` column to
  `participation.csv`. It then fails `--check` until each stage's four candidates are marked or gapped (`in the
  stage`, `oldest's age`, `time through`, `past the promise`),
  each agent row is classed `yes:` or `no:` in `decision_point`, and each agent's five run metrics are covered or
  gapped. Defect prose in `source_ref` moves to `defect`. Add a `reply_decision_point` column to
  `participation.csv` too: the check then fails until each agent row's reply is classed `yes:` or `no:`.
- A register filled with an earlier version of this kit names the acts inside an agent's run `step` and its pieces `part` in
  `agent-system.csv`'s `element` column: rename `step` to `operation` and `part` to `agent part`. The check fails on
  the old values.
- A register filled with an earlier version of this kit may name a runbook section (`§2`) in a remedy's text in
  `remedies.csv`, or in `failure`, `test`, `expected` or `seen` in `failure-modes.csv`. The check fails on it: write
  the action itself (`Escalate`, `Roll back`) in its place, and the runbook points it at its section. A remedy that
  names a measure proposed for alerting (`M13`) fails the same way: write the action, not the measure.
- A register filled with an earlier version of this kit has no `operation` column in `participation.csv`, and then
  the receipt asks no question of any operation: the check passes with per-operation coverage skipped. Add the
  column and fill each row from the code with the route, tool or handler that performs the step; then name in
  `measures.csv` `operation` the operations each measure counts.
- No worked example shows a stage whose work never waits (a chain of synchronous calls that succeeds or fails within
  seconds), where the alerts count cases leaving wrongly (Step 9). The eShop example's stage waits, and proposes an alert on
  both kinds of loss.
- `flow_outputs.py --check` tests the register's structure and coverage. It cannot tell whether a citation says what
  the row claims: that is the verification pass in Step 11, which the assistant runs on its own work. That pass does
  not catch every wrong citation, so someone who did not draft the register checks a sample afterwards (USE.md,
  'Before you take it to anyone').
- **The runbook's tests have not been run.** Step 11 asks for each test to be checked against one known case, and an
  assistant working from the code alone has no case to run it on. Until the code's engineers have run each test once,
  on a case whose answer they know, read every test as a proposal.
