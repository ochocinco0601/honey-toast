---
name: bfo-stage-kit
description: Describe one business flow of an application from its code, and for one stage of it propose what to measure, what to alert on, and a runbook per alert, then draw the whole flow as one map. Use when asked to map a business flow or business capability for operations, to work out what to monitor or alert on for a flow, or to write runbooks for a flow's alerts, starting from the code and sources the person points at (repositories, documents, diagrams, process descriptions) and following the flow's calls into any code the run can get. Design time only - it reads code, documents and recorded answers, never a running system. Use this rather than the older capability-views skill, which draws an earlier form of the same map and writes no alerts or runbooks.
---

# Business flow observability: one flow, one stage

This folder is the kit. Everything below calls it **the skill folder**. Wherever `FILL-STEPS.md` writes
`<skill>`, it means this folder, and the folders it names (`register-template/`, `reference/`, `method/`) are
inside this folder too.

## The run

A run is eight phases, done in order. Each has an **In → Out**, and the files it names are what prove it done. The
work goes in the **register folder**, `bfo-work/<application>/` at the workspace root (in a multi-root workspace,
the first folder), never in the skill folder;
it is `<your-folder>` in `FILL-STEPS.md`. Run the kit's scripts from the skill folder, exactly as `FILL-STEPS.md`
writes them, with `<skill>` replaced by the skill folder's path.

**The very first act is to look for earlier work.** Search the whole workspace, not only `bfo-work/`, for every
folder holding `steps.csv` or `lifecycle.csv`, leaving out the skill folder. A folder whose `RUN.md` has the section
*Earlier registers* was made by this version of the kit: if its phases are not all done, this run resumes it (below).
**Every other one is an earlier register: a tool's output, never a source and never a base.** The run never writes
into it, never copies the template over it, and never starts from it: it walks fresh from the code and the person's
sources into a new register folder (`bfo-work/<application>-<yyyy-mm-dd>/` when `bfo-work/<application>/` is taken),
lists each earlier register in `RUN.md` → *Earlier registers* → *Found*, and reconciles each with the new register in
Phase 7. If the stage to cover is not named, prefer one an earlier register has `stage-<id>/` work for, so the
re-derivation can be compared.

**Then `RUN.md`, and nothing else starts before it.** Before reading any code or writing any other file, create the
register folder, copy `register-template/RUN.md` into it, and write its section *What this run will produce* in your
own words, from this file: the application, the flow and the stage (or how you will pick them), and, phase by phase,
what the phase does and the files it must leave. Then set Phase 0 to *doing*.

**`RUN.md` is kept as you go.** At the end of each phase, set it to *done* with the files that prove it, and the
next to *doing*. A phase that cannot be done is set to *blocked* with the reason (for example "python is not on
the path") and what would unblock it, and the run says so in the chat. No phase is skipped silently, and the run
never stops without saying where it stands. **If `RUN.md` already exists**, because the run is resuming or a new
chat has started, read it first and continue from the first phase that is not done.

0. **Frame and gather** (FILL-STEPS "Before you start").
   In: whatever the person points at in their request (repositories, pages, diagrams, process descriptions,
   documents, notes), and what is already in the workspace. Out: the register's CSV files, copied from
   `register-template/` by `python "<skill>/start_register.py" "<your-folder>"`, never by hand: it copies only into
   a folder holding no CSV file, keeps the `RUN.md` already there, and refuses to write over an existing table;
   `sources.csv` with one row per source, pass `1`, and in `note` the step that will use it
   (the table in "Before you start"); `about.csv` → `sources_examined` and `what_it_is`; the first rows of
   `how-made.csv`; and `RUN.md` → *Sources*, listing what was gathered and what is still missing.
   **First, prove the scripts run:** `python "<skill>/run_status.py" "<your-folder>"`. It says NOT DONE at this
   point, and that is expected. If the command itself fails (no python, a version older than 3.9), set Phase 0
   *blocked* with the error and stop there: every later phase ends in a script, so nothing is drafted that cannot be
   generated.
   **Get every source with your own tools**, whatever its form: you already know how to clone a repository and how
   to read a page, a diagram or a PDF. Put each repository you fetch at the workspace root, as its own folder, because
   every citation starts with that folder. **Every repository the run uses is a folder of the open workspace** (a
   multi-root workspace when there are several), never a temporary folder: the environment's code tools reach only the
   open workspace. If you cannot add folders to the workspace yourself, set Phase 0 *blocked*, name the repositories,
   and tell the person to open them as one multi-root workspace and start again; write the same in `RUN.md`. A source you cannot reach (no access, a dead link) is listed under
   *still missing* in `RUN.md` with what you tried, and the run goes on: a missing source changes what the map is
   worth, never whether the run continues.
   **Check the repository set is complete**, without being asked: (a) for every reference the code makes that no
   folder in the workspace answers (a host or service name, a client package, a queue or topic, an image, a
   configuration key, a URL), search the code host with the person's own access (repository search, code search
   across the organisation) for the repository behind it; (b) search the other way too, for repositories that call,
   consume from or deploy this flow's services; (c) repeat on what the new repositories reference, until a pass finds
   nothing new. Record each repository found in `sources.csv` with the search that found it, and add it to the
   workspace as a further folder, read-only; what is found and cannot be had goes under *still missing*. `RUN.md`'s
   Phase 0 line answers "Is this the complete set of repositories?" with that evidence, and Phase 0 is not done while
   a reference is unresolved and unsearched. If the person's request says to use only the sources they name, do not
   search: list each unresolved reference under *still missing* instead.
   **This phase lists and places; it does not read everything.** Read each source only far enough to say what it
   is and which step uses it. Code is read in full from Phase 1 on, every service the flow touches, as the rules for
   the whole run below say.
   Keep the documents identifiable as a set: Step 8 hands them, without the walk, to a separate pass.
1. **The case and its lifecycle** (Steps 1 and 2).
   In: the sources. Out: `flows.csv` (the case, whose expectation, start and end), `lifecycle.csv`. Pick the main business flow, the one whose case the business most
   depends on, unless the person named one, and write it into `RUN.md`.
2. **Stages, process steps, parts and agents** (Steps 3 to 7).
   In: the lifecycle. Out: `stages.csv`, `steps.csv`, `subjects.csv`, `participation.csv`, `set-aside.csv`,
   `agent-system.csv`. Choose this run's stage for Phase 5 and write it into `RUN.md` as `stage-<id>`: the stage
   the person named; else, if the register already has `stage-<id>` folders, the next stage with none; else the
   stage where a case most often waits or can be left stranded.
3. **The capability** (Step 8).
   In: the walk so far, and the documents read apart from it. Out: `capabilities.csv`.
4. **Measures and costs** (Steps 9 and 10).
   In: the register so far. Out: `measures.csv`, `measure-gaps.csv`, `step-impact.csv`, `case-attributes.csv`.
5. **One stage's failure modes, alerts and runbook** (Step 11).
   In: the register and the chosen stage. Out: `failure-modes.csv`, `remedies.csv`, and `stage-<id>/` holding
   `STRUCTURE.md`, `MEASURES.md`, `ALERT.md`, `RUNBOOK.md`, `ALERT.html` and `RUNBOOK.html`, written by
   `flow_outputs.py --out`. It writes the last four only when its check passes, so a missing runbook means the
   check failed: fix the register. A stage no proposed alert reaches (on the stage, its process steps, the parts they use
   or the flow) gets no `ALERT.md` or `ALERT.html`, and its runbook says so; the check notes it, and does not fail. Regenerate every other `stage-<id>/` already in the folder, each with its own check.
6. **Check and draw** (Step 12).
   In: the register. Out: the three checks of Step 12 run, every failure fixed in the step that produced it;
   `views.html` and `how-this-map-was-made.html` in the register folder, written by `one_canvas.py`.
7. **Reconcile, done check and report.**
   **First, reconcile each earlier register** that `RUN.md` → *Earlier registers* names (skip this when it says
   none): `python "<skill>/reconcile.py" "<earlier register>" "<your-folder>"`. The script matches rows by what they
   say, classes each earlier row by its citation, checks each code citation against the files the new walk read, and
   writes `reconciliation-<name>.md` in your folder. It never writes to the earlier register. **In this release the
   reconciliation only reports: add nothing from it to the new register.** The new register is the fresh walk alone.
   Copy the report's counts and names, list by list (matches, *unchecked: not added*, not supported, not assessed,
   disagreements, carried from a person, re-open in the document, dropped), into `RUN.md` → *Earlier registers* →
   *Reconciled*, and say in the report to the person that they are for a person to read, not added. Then work
   through *Claims beside their cited lines* one row at a time: read the claim beside the lines it cites and write
   that row's verdict (supported, not supported, or not assessed) and the reason, as the report asks. The script
   only checks that a citation resolves; whether the line says what the row claims is this step's.
   Then the done check. In: the register folder. Run `python "<skill>/run_status.py" "<your-folder>"`. It lists every output the run
   owes and ends DONE or NOT DONE. **The run is done only when it says DONE**; never say so on your own reading.
   DONE also needs every field a view requires answered or gapped (FILL-STEPS Step 12). If it says NOT DONE, go
   back to the phase that owes the missing file or writes the empty field, or mark that phase blocked with the reason.
   Out: `RUN.md` with every phase done or blocked, and the report to the person: the register folder, the flow and
   stage, the check results, the stages that still have no Step 11, each earlier register and what its reconciliation found (added,
   carried forward, not supported, not assessed, disagreements, each named), anything you could not do, and the output of
   `run_status.py` pasted as it is. End the report with **What would make this map fuller**: the deployables the map
   stops at (every part under *still missing*, and every external dependency with no source of its own), then the
   `proposed:` rows counted by the kind of source that would settle them, read off the table in FILL-STEPS "Before
   you start".

## Rules for the whole run

- Read `FILL-STEPS.md`, then `register-template/REGISTER.md` and the reference files `FILL-STEPS.md` cites in
  `reference/`, before Phase 1. Look at `example-eshop/` only to see what a finished register and its outputs look
  like. It is a different application and never a source of facts.
- Step 11 covers one stage per run, and a flow is covered when every stage has had one.
- **Follow the code past the workspace.** When a move calls a deployable whose code is not here, identify it from
  what the call shows (an address, a client package, a queue or topic name, an image) and get it with your own
  tools if you can reach it: it is a pass-1 source like the others. Fetch it only with access the person already has, and read-only: never request access, enter credentials, or change anything at the source. Record every fetched source in `RUN.md` *Sources* with what referenced it and why. If the person's request says to use only the sources they name, do not fetch: list it under *still missing* instead. With its code it is a component, whoever owns
  it, and you read the operations this flow calls and what those call (FILL-STEPS Step 5); how far into an outside
  service to go is Step 6's. If you cannot reach it, it stays a part cited by how you identified it, an external
  dependency, and goes under *still missing* in `RUN.md`.
- **Read in full every service the flow touches.** Steps 1 to 10 cover the whole flow: the lifecycle, the parts and
  the measures read every service the flow runs through, whatever stage it carries. Only Step 11 is per stage, as
  above. A run is cut shorter only when the person asks for it (`USE.md`). `KNOWN-GAPS.md` "At scale" says what is
  still open at size.
- **Talk to the person in names, not ids.** In every message and report, name parts, process steps and stages by their
  names ("the Ordering API", "Accept the order"), never by register id. An id may follow a name in
  brackets only where the person must find a row in a file.
- Do not stop to ask the person anything. Where the sources do not say something, infer it and label it
  `proposed:` with the reason.
- Never edit a generated file: fix the register and generate again.

## What the person gets

`USE.md` in the skill folder is written for the person running this. It explains what comes out, how to read it,
and what to check before taking it to anyone. `KNOWN-GAPS.md` lists what the kit is known to get wrong. Point the
person at both when you finish.
