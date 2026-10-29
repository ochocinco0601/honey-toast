# Run record

This file is the run's record. It is written before anything else in the run, and updated at the end of every
phase. A run that resumes, or a new chat, reads it first and continues from the first phase that is not done.

## What this run will produce

Write this section yourself, in your own words, before you read any code or write any other file. Do not copy the
skill's text. Saying it back is how the run checks it has understood the skill.

- **Application:** _write the application this run describes._
- **Flow:** _write the flow the person named, or "a decision in the plan". Fill it in from their answer at the go._
- **Stages and how far each goes:** _the person's pick after mapping, as `stage-<id>` and its depth for each stage
  (mapped only, measured, alerting, runbooks); "not yet picked" until then._
- **Phase by phase:** _for each phase in `SKILL.md`, one line: what it does, and the files it must leave in this
  folder before it counts as done._

## Status

Status is one of: to do, doing, done, blocked, not picked. **Done** names the files that prove it. **Blocked** says
why (for example "python is not on the path") and what would unblock it. **Not picked** is a phase the person's pick
of how far each stage goes leaves out, set by `go.py --depth`: it is passed over, never waited on. No phase is skipped: a phase that cannot be done is
blocked, with its reason.

| Phase | Status | Proved by (files, when done) | Blocked because |
|---|---|---|---|
| 0 Frame, gather, survey and plan | to do | | |
| The go on the plan | to do | | |
| 1 The case and its lifecycle | to do | | |
| 2 Stages, steps, parts and agents | to do | | |
| 3 The capability | to do | | |
| Pick of how far each stage goes | to do | | |
| 4 Measures and costs, for the stages picked | to do | | |
| 5a The picked stages' alerts | to do | | |
| Review of the alerts | to do | | |
| 5b The picked stages' failure modes and runbooks | to do | | |
| 6 Check and draw | to do | | |
| 7 Done check and report | to do | | |

## Plan and go

The run's plan is `PLAN.md` in this folder, written at the end of Phase 0 for the person who oversees the run. Nothing
is read in depth until the person's go is recorded here, word for word, with when it was given. A go given for a test
says so ("test go, given by ..."). If the person asks for changes, revise `PLAN.md` and wait again.

- **Plan:** PLAN.md
- **Go:** _the person's words, word for word, and when; blank until the go is given._
- **Scope:** _the flow the person picked at the go, then their words, written by `go.py`: `flow <name>; stages not
  yet picked (after the flow is mapped). In their words: "..."`; once they pick how far each stage goes, the stages
  with their depth. Blank until the go. The done check owes what that pick asks for; every other stage is reported
  as not yet covered._
- **Depth picked:** _the person's pick of how far each stage goes, after mapping, word for word, and when; written
  by `go.py --depth`. Blank until they pick. Nothing is measured before it._
- **Alerts reviewed:** _the person's answer on the proposed alerts, word for word, and when; written by `go.py
  --alerts-reviewed`. Blank until they answer. No runbook is written before it._

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
