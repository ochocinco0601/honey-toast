# Using the kit

**What it does.** An assistant follows this kit over an application's code and describes one business flow of it:
the case it carries (one order, one application), the states the case passes through, and the stages they fall
into. For each stage you take past mapping, it then produces the files your pick calls for (the structure and the
measures; then the alerts; then the runbooks), which you can take to the engineers who own the code:

| File | What it is |
|---|---|
| `STRUCTURE.md` | The stage drawn: its process steps, the order a case takes through them, the alternative endings, and every part that carries each process step or is needed by it |
| `MEASURES.md` | What could be measured for the stage, each process step and each part, by layer (business health, business impact, application, system), marked *exists* or *proposed* |
| `ALERT.md` | The measures proposed for alerting on the stage: what each counts, what it rests on, and the values the operators must set |
| `RUNBOOK.md` | What the responder to an alert does: a short entry per alert (what fired, the opening checks, what to contain first, its own tests in order, each saying what a match means), then one shared section for the stage with every test written once, the causes the alerts share, the restores, and whom to escalate to |

Every claim cites the code as `file:line`. Anything the code does not state (owners, promises, volumes) is written
`proposed:` with the reason. The engineers can check both.

## What you need

- Claude Code (the VS Code extension or the command line), so the model can read files, run terminal commands and
  launch helper agents. The run's done check reads Claude Code's own record of the session, so a run in another
  assistant never reaches DONE. What it reads: the session records Claude Code keeps on this machine (under
  `~/.claude/projects/`) for the folders from the register up to, not including, your home folder or the drive's root. It keeps only which files were opened and the commands run, writes nothing, and
  sends nothing anywhere. If you started Claude Code outside the register's folder (in a folder beside it or below
  it), set `BFO_TRANSCRIPTS` to that session's project folder under `~/.claude/projects/` (named after the folder the
  session was started in, every character other than a letter or digit written as a dash) before the done check.
- Python 3.9 or later on the path, and Semgrep for the code reader (`pip install semgrep`;
  `fact-extractor/semgrep_bin.py` says how it is found). The reader runs it with the kit's own rules, metrics and version check off, so it sends
  nothing anywhere; Semgrep keeps its own settings and log under `~/.semgrep/`. Nothing else is installed.
- A browser, for the run's page. To show it, the run starts a small web server on this machine only
  (`127.0.0.1`), with no window. It keeps running between the points where the run waits on you, and stops by
  itself shortly after the run's record shows the run has ended, even with the page still open; it also stops with
  the stop command the run prints, or after eight hours with no request. The run opens your browser on the page in
  one tab, and opens it again at a later stop if you closed that tab; set `BFO_NO_BROWSER=1` to turn that off and
  open the address the run gives you yourself. Nothing is sent off the machine.
- The code, or where it is: name the repositories, pages, diagrams and process descriptions in your request, and
  the run gets them. Code already open in the workspace is read too; where it spans several repositories, add each
  as a folder of one workspace. You can start with as much or as little as you have: a name, some repositories, all of them, documents. For what is not there (the repositories behind references nothing in the workspace answers, those that call this flow's services, a service the code calls whose code is not there), the run says what it cannot find and proposes where to look, and searches only where you agree. It searches and fetches with access you already have and read-only: it never requests access, enters credentials, or changes anything at the source, and `RUN.md` lists every source it fetched with what referenced it and why. What you do not agree to search is listed under *still missing*. To keep it to the sources you name, say *use only the sources I name*: it then neither fetches nor searches, and lists the rest under *still missing*.
- Every repository open as a folder of one workspace (a multi-root workspace when there are several), never in a
  temporary folder: the run's code tools reach only the open workspace, and a run that can't add them is blocked: it names the
  repositories and tells you to open them as one multi-root workspace and start again.
  Keep your own working folder as the first folder of the workspace, so your notes and the register stay in reach,
  and add the repositories after it.
- This folder, `bfo-stage-kit/`, in one of two places:
  - **as a skill** (the simpler way): copy it to `~/.claude/skills/bfo-stage-kit/` for every workspace, or to
    `.claude/skills/bfo-stage-kit/` in the folder Claude Code starts in. Then ask Claude Code in your own words, for
    example *Map the main business flow of this application for operations*. The skill's `SKILL.md` tells it what
    to do, and the register goes to `bfo-work/<application>/` at the workspace root;
  - **or in the workspace**, used with the prompt below. The register then goes to `bfo-stage-kit/work/<application>/`.

## The prompt

Without the skill, copy it as it is into Claude Code:

```text
Run bfo-stage-kit/SKILL.md for the application whose code is in this workspace, and any repositories,
documents or diagrams I name here, following its calls into any other code you can get, with
bfo-stage-kit/work/<application>/ as the register folder in place of bfo-work/<application>/. Its first act is
RUN.md; follow its phases to the end and finish only when run_status.py says DONE.
Never stop to ask me a fact you can infer: infer it and mark it proposed. Bring me what is mine (which flow to
map, what to leave out, whether the sources are enough) with your proposal when it arises, starting with the plan,
shown whole in the chat. When you finish, tell me the folder, the flow and how far each stage went, the check results,
anything you could not do, and paste run_status.py's output.
```

To point it at sources, add one line at the end (optional): *These are the sources: …*, naming the repositories,
pages, diagrams and process descriptions.

**How far each stage goes is your pick, after the map.** The map covers the whole flow in the first run. Once it
is drawn, the run shows you its stages and asks how far each one goes: mapped only, measured, measured with alerts,
or on to runbooks. You can take any number of stages to any depth, with the run's recommendation in front of you; a
flow can be mapped and left there. The checks follow each stage's depth: a stage you left mapped only is held to its
map and nothing more, and the run is done when every stage you took further passes at the depth you picked. Decide
how far each stage goes before the run moves on: you can take a stage further while the run is still under way, but
not back, and taking stages further on a run that has already finished is not supported yet (see KNOWN-GAPS.md).

**A capability served by many services or repositories.** The same instructions hold at any size; FILL-STEPS
covers what changes with the number of services. Tests of many parts of one kind become one sweep over all of them,
shared dependencies are tested first, and a called service's own databases are reached through its tests. Citations
are checked by sample, and every citation starts at the workspace root. The check holds each stage to the depth you
picked for it, and the flow to its own measures. A capability spread over several repositories is not
yet proven at that size. By default a run reads every service the flow touches. Two more things
help:
- only for a run that has to be cut, add: *For the stages I take past mapping, read the code of the services that
  carry them in full. For the flow's other services, read only what you need to place them, and gap their measures
  with the reason "not read in this run".* Those gaps stay until those services are read; taking more stages further
  on a finished register is not supported yet (KNOWN-GAPS.md).
- open each repository as a folder of one workspace, and list each in `sources.csv` with its commit.

Read `KNOWN-GAPS.md` for what is still open at that size.

**The run introduces itself, then shows you the system before it reads in depth.** Its first message says what it
is for, how you will work together and what it needs from you. After a first, shallow look at the code it sends a
brief (it also keeps it as `PLAN.md`): what this work is; what the system does, for whom, and what one case is; every
business flow found so far, each with its stages; what it looked at and what is still open; the services and which to
include; where it recommends starting, and what then remains; and what it will do unless you say otherwise (the
services it will read, and how its findings will be checked against the code: in a single run, a reader who wrote
none of them re-reads a sample of ten; in a run split into reading units, independent checks read each finding). It asks one thing: which flow to start
with. Reply with the flow, or accept its recommendation, or say what to change. Nothing is read in depth before your answer. Every message opens with one line
saying where things stand; if you come back to a stopped run, it first tells you, in full, where the work is.

**Before any runbook, the run shows you the alerts it proposes and waits.** For each stage you picked it says what each alert counts, what it guards, whether it exists today, and why; you keep, drop, change or add alerts, or say go. Saying *continue* there is not a go on the alerts: say what you decide about them.

The run takes a while. If the model stops partway, say *continue from where you stopped, following FILL-STEPS.md*.

**Where a run stands.** `RUN.md` in the register folder records each phase of the run as to do, doing, done,
blocked or not picked, with the files that prove it or the reason it is blocked. *Not picked* is a phase your pick of
how far each stage goes leaves out: the run passes over it and does not wait on it. Whether the run is done is said by
`python <kit>/run_status.py <register folder>`, which lists every output the run owes and says DONE or NOT DONE.
The Fullness block it prints after that line counts how full the register is and judges nothing.

## If you ran an earlier version of this kit

Keep the register from that run: the folder of CSV files in `bfo-stage-kit/work/`, or in `bfo-work/` if you used the
kit as a skill. If it is inside `bfo-stage-kit/`, move it out (to `bfo-work/` at the workspace root) before you
replace the kit folder with this one, so replacing the kit does not delete it. Then run the kit as usual.

**The new run never builds on the earlier register, and never writes into it.** An earlier register is unchecked
output, so the run walks the code afresh into a new register folder. Once its own map is checked, the kit's
`reconcile.py` compares each earlier register with the new one, row by row. A row cited to code is checked against
the code the new run read, and added only if the code says it. A row cited to a document is checked in the document.
A row a person gave is carried forward, cited to that person, and any disagreement with the new run is listed for a
person to settle. A guess (`proposed:`) is dropped, and a row about code the new run did not read is marked not
assessed. `RUN.md` and the final report name each earlier register and what was added, carried, not supported, not
assessed and disagreed. Alerts and runbooks from the earlier run are not carried: each stage's alerts and runbooks are made again in the
new run.

The earlier in-place upgrade prompt is retired (CHANGELOG, Release 2).

## What comes out

In `bfo-work/<application>/` at the workspace root when the kit is installed as a skill, or in
`bfo-stage-kit/work/<application>/` when it is used with the prompt:

- the register, a set of CSV files: the model, row by row, each row cited;
- `stage-<id>/` for each stage taken past mapping, holding the files its depth calls for from the four above;
- `views.html`, the same model drawn as one map, which opens in a browser: point at a box to light its chain, open a
  stage's process steps to see the parts that carry them, and click a box to see its measures and drawings. `how-this-map-was-made.html` beside it says how the map was made, for whoever builds or checks it; each stage's
  `RUNBOOK.html` and `ALERT.html` sit in `stage-<id>/` beside it.

`example-eshop/` is a finished example of all of it, for every stage of eShop's order flow: "Place the order", "Accept the order", "Ship the order" and "Deliver the order".

## How to read it

1. **Start with `STRUCTURE.md`.** The diagram is Mermaid. VS Code's Markdown preview draws it from VS Code
   1.121 on; on an older version, install the Markdown Preview Mermaid Support extension. Arrows between process steps follow one case; several arrows out of one process step are
   alternatives. Check the stage's start and end, and the parts on each process step, against what you know.
2. **`ALERT.md`** says what is proposed for alerting and what it counts. The threshold, the window, the time limit,
   and whether an alert pages anyone, are left for the operators to set.
3. **`RUNBOOK.md`**: one entry per alert, which the alert's runbook link in `ALERT.md` points at, then the stage's
   shared section. An entry is the walk: the cases and window its tests are read on, the opening checks, what to
   contain first, and its own tests in order, each saying what a match means and its ending. S1 restates the stage;
   S4 writes each test once (what to look at, the healthy result, the failure and its ending, and which alerts use
   it); S5 lists the causes the alerts share; S8 names the owner of each part to escalate to. S11 traces each test to
   the register row it came from.
4. **`MEASURES.md`** lists every measure. *Proposed* means nothing emits it today.

## Before you take it to anyone

- Run the check yourself: `python <kit>/flow_outputs.py <register folder> <flow id> <stage id> --check`, where
  `<kit>` is the folder the kit was copied to (`~/.claude/skills/bfo-stage-kit` or `.claude/skills/bfo-stage-kit` as a
  skill, `bfo-stage-kit` with the prompt) and
  `<register folder>` is the folder named above.
  It should report 0 errors.
- Open three or four `file:line` citations from the runbook and confirm the code says what the row says.
- The runbook's tests have not been run. Ask the code's engineers to run each one once, on a case whose answer they
  know, before anyone relies on it.
- Read `KNOWN-GAPS.md`: what the kit is known to get wrong.
- Take it as a draft for the engineers to correct. A correction goes back into the register, and the outputs are
  generated again. Tell the model what is wrong and which register row holds it.
