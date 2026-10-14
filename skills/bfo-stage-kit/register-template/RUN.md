# Run record

This file is the run's record. It is written before anything else in the run, and updated at the end of every
phase. A run that resumes, or a new chat, reads it first and continues from the first phase that is not done.

## What this run will produce

Write this section yourself, in your own words, before you read any code or write any other file. Do not copy the
skill's text. Saying it back is how the run checks it has understood the skill.

- **Application:** _write the application this run describes._
- **Flow:** _write the flow, or, if the person did not name one, how you will pick it. Fill it in at the end of
  Phase 1._
- **Stage for Step 11:** _write the stage, or, if the person did not name one, how you will pick it. Write it as
  `stage-<id>` once the stages are cut (Phase 2)._
- **Phase by phase:** _for each phase in `SKILL.md`, one line: what it does, and the files it must leave in this
  folder before it counts as done._

## Status

Status is one of: to do, doing, done, blocked. **Done** names the files that prove it. **Blocked** says why (for
example "python is not on the path") and what would unblock it. No phase is skipped: a phase that cannot be done is
blocked, with its reason.

| Phase | Status | Proved by (files, when done) | Blocked because |
|---|---|---|---|
| 0 Frame and gather | to do | | |
| 1 The case and its lifecycle | to do | | |
| 2 Stages, steps, parts and agents | to do | | |
| 3 The capability | to do | | |
| 4 Measures and costs | to do | | |
| 5 One stage's failure modes, alerts and runbook | to do | | |
| 6 Check and draw | to do | | |
| 7 Done check and report | to do | | |

## Sources

Written at the end of Phase 0, and added to by any later phase that meets something new.

- **Gathered:** each source by its `sources.csv` id, and the step that uses it.
- **Still missing:** each source pointed at or found that could not be reached, with how it was identified and
  what was tried. The report's *What would make this map fuller* starts from this list.

## Earlier registers

Written at the start of the run, and filled in by Phase 7's reconciliation. An earlier register is never written to
and is never this run's starting point. A register folder whose `RUN.md` has this section was made by this version
of the kit; one without it is an earlier register.

- **Found:** the path of each register already in the workspace when the run began, or "none".
- **Reconciled:** for each, the path of `reconcile.py`'s report, and its counts: unchecked (not added), carried
  from a person, re-open in a document, not supported, not assessed, disagreements, and Step 11 work not carried.
  Name each row, each not supported with the reason, and each disagreement. Nothing listed here is in the new
  register: it is for a person to read.
