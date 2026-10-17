# Room runs

The ledger template. The live ledger is `./.claude/room/RUNS.md` in the working
session's folder — copy this file there on the first run, so a newer copy of the skill
never overwrites your history. A room that is not scored is a room nobody can tell is
working.

**The pre-answer exists before the seats are spawned, and is written here after they
report.** The orchestrator holds it in its own context until then, because this file is
one a seat can be pointed at, and a pre-answer a seat can read cannot score it. A
pre-answer formed after a report arrived is not a pre-answer; mark such a row as noise.

**The falsifier this table exists to expose:** if the reports keep coming back MATCHED,
the value is in asking the questions, not in the separate contexts — and the honest
product is a short checklist rather than a room. You will only notice that if these rows
are filled in honestly.

| # | Date | Target | Seat | Pre-answer | What came back | MATCHED / DIFFERED | Disposition | Changed |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |

**Column notes**

- **Target** — the artifact or decision the room was convened on, as a path.
- **Seat** — one row per seat, so a run of four seats is four rows. Repeat passes get a
  row each too, with the verdict recorded by `repeat.py record`.
- **Disposition** — `acted` · `user's call` · `back to a seat` · `to the record` ·
  `declined`. Never blank. A declined finding carries its reason in the same cell. A
  stage-gap finding is never `to the record`.
- **Changed** — the commit, or `nothing`. Score on the commit, not on the working tree.
  Name the session that made it only where authorship was established by asking;
  otherwise write "changed in this tree".

## What the room missed

Findings the room should have produced and did not, found afterwards by other means —
and seats nobody asked for (`ORCHESTRATOR.md` step 5, the second question). This section
is worth more than the table: it is the only place the instrument's blind spots become
visible.

| # | Run | What was missed | How it was found instead | Which seat should have caught it, or which seat is missing |
|---|---|---|---|---|
| | | | | |
