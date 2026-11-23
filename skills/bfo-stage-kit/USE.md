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
  `~/.claude/projects/`) for the folders from the register up to, not including, your home folder or the drive's root. It reads which files were opened, the commands run, the
  content of the files the run and its helpers wrote, each helper's first prompt, and the words you typed, to
  confirm a correction is yours; it writes nothing there and sends nothing anywhere. If you started Claude Code outside the register's folder (in a folder beside it or below
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
  open the address the run gives you yourself. Nothing is sent off the machine. To stop the server on Windows, the
  run asks Windows for the command line of the one process it recorded (a hidden PowerShell call,
  `Get-CimInstance Win32_Process`) and, once that confirms it is the run's own server, ends it with
  `taskkill /PID <n> /F`.
- Helper agents. The run reads each part of the code, and checks each finding, with Claude Code subagents launched
  from your own session. The kit also has a second way, used only if you or a session run `readers.py run` or
  `judges.py run` by command, never by the skill's own steps: it starts separate headless Claude Code processes
  (`claude -p`), several at once (`parallel` in the register's `run-settings.json`), each for up to 90 minutes (a
  reader or fixer) or 30 minutes (a judge). A reader may read, search, write and edit files, a judge read, search
  and write; both are refused the shell, other agents and the web. Keeping their writes to their own folders rests
  on their prompt and on the check of their session records afterwards, and a `claude -p` judge fails that check
  (`split-run-formats.md`).
- The register's `run-settings.json` is as trusted as a script: after every command that changes the run's state,
  the kit runs its `on_change` command through the shell (by default the kit's own `python run_page.py {reg}`).
  `capability_views.py` run without `--out` writes its page to `out/` inside the kit's own folder.
- The code, or where it is: name the repositories, pages, diagrams and process descriptions in your request, and
  the run gets them. Code already in the workspace is read too, and so is code cloned into a folder of its own beside
  it (a `repos/` folder, say): the run records where each repository is. You can start with as much or as little as you have: a name, some repositories, all of them, documents. For what is not there (the repositories behind references nothing in the workspace answers, those that call this flow's services, a service the code calls whose code is not there), the run says what it cannot find and proposes where to look, and searches only where you agree. It searches and fetches with access you already have and read-only: it never requests access, enters credentials, or changes anything at the source, and `RUN.md` lists every source it fetched with what referenced it and why. What you do not agree to search is listed under *still missing*. To keep it to the sources you name, say *use only the sources I name*: it then neither fetches nor searches, and lists the rest under *still missing*.
- The repositories side by side in one folder, never in a temporary folder: inside your working folder, or in a
  folder of their own beside it (`repos/`, say). No multi-root workspace is needed; the run records each
  repository's folder in `sources.csv` and tells its readers and checkers where the code is. Repositories spread over
  different folders are refused, because every citation starts with its repository's folder name.
- This folder, `bfo-stage-kit/`, in one of two places:
  - **as a skill** (the simpler way): copy it to `~/.claude/skills/bfo-stage-kit/` for every workspace, or to
    `.claude/skills/bfo-stage-kit/` in the folder Claude Code starts in. Then ask Claude Code in your own words, for
    example *Map the main business flow of this application for operations*. The skill's `SKILL.md` tells it what
    to do, and the register goes to `bfo-work/<application>/` at the workspace root;
  - **or in the workspace**, used with the prompt below. The register then goes to `bfo-stage-kit/work/<application>/`.

  Either way, put the mapping skill (`bfo-mapping/`) and the measures skill (`bfo-measures/`) beside it, in the same
  folder as `bfo-stage-kit/`: the kit hands the mapping of the flow to the first and the proposing of the measures
  to the second, and runs neither itself.

  Then copy the kit's four agents from `bfo-stage-kit/agents/` into `.claude/agents/` in the folder Claude Code
  starts in (the folder you open Claude Code in, not the one above it), before you start Claude Code:
  `bfo-unit-reader.md` (reads one part of the code in the full reading), `bfo-source-reader.md` (reads one source at
  the first look), `bfo-flow-mapper.md` (reads one service's code for the fast map) and `bfo-row-judge.md` (checks one
  row of the map). A session loads agent types when it starts, and never from inside a skill's folder; if you copy
  them after starting, start a new session. None of their tools holds a shell. The run refuses to launch an agent of
  a type that is missing or is not the kit's own copy. Copy them again with every new build.

  Copy the whole folder, never part of it. Its `KIT-VERSION.txt` names the build it is (the release and date it was
  built from) and lists every file in it. At every start and resume the run prints which build it is running and,
  where your copy is missing a file, has one changed, has one from another version, or has no `KIT-VERSION.txt`,
  says so and stops before it touches your work: copy the whole folder again from its source, then start again.
  A whole copy of an older build is not caught this way; the build the run prints tells you which one you have.

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
anything you could not do, and what the done check found, in plain words.
```

To point it at sources, add one line at the end (optional): *These are the sources: …*, naming the repositories,
pages, diagrams and process descriptions.

**How far each stage goes is your pick, before any service is read in depth.** The run first writes the flow's
stages, the process steps in each, which services carry each step, and what is at stake if each step fails, in
minutes. Then it shows you the stages and asks how far each one goes: mapped only, measured, measured with alerts,
or on to runbooks. Only then does it read the code of the services the stages you take further reach, along their
path: from where the stage's steps start, every function a case passes through and what those call, the stores they
open, and each service's monitoring hooks; every other file is listed as not read. To read every line instead, set
`"reading": "full"` in the run's `run-settings.json`; a stage you leave mapped only keeps its steps and which services carry each, and what is inside those
services is marked not read. Taking a stage further later reads its services then, before its measures. You can take any number of stages to any depth, with the run's recommendation in front of you; a
flow can be mapped and left there. The checks follow each stage's depth: a stage you left mapped only is held to its
map and nothing more, and the run is done when every stage you took further passes at the depth you picked. Decide
how far each stage goes before the run moves on: you can take a stage further while the run is still under way, but
not back, and taking stages further on a run that has already finished is not supported yet (see KNOWN-GAPS.md).

**A capability served by many services or repositories.** The same instructions hold at any size; FILL-STEPS
covers what changes with the number of services. Tests of many parts of one kind become one sweep over all of them,
shared dependencies are tested first, and a called service's own databases are reached through its tests. Citations
are checked by sample, and every citation starts at the workspace root. The check holds each stage to the depth you
picked for it, and the flow to its own measures. A capability spread over several repositories is not
yet proven at that size. A run reads in full only the services of the stages you take past mapped only, so the
time to your pick does not grow with the size of the code. Two more things help:
- at the first brief, leave out any service the flow does not need: the go takes your word for it, and its parts are
  then gapped "not read in this run";
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

**The next flow joins the same map.** A register is the capability's one map. When a flow is finished and the first
look found more, the run offers the next flow, with the one it recommends and why, on the page and in the chat; the
flow you pick is added to the same register, beside the finished ones. A finished flow keeps everything: how far you
picked to take each stage, your words, your review of its alerts, its rows in the map and its pages. The done check
says NOT DONE if a row of a finished flow is changed or an id is used twice. A flow the first look missed can be
added at the offer, in your words, on the page or in the chat, and then picked like the others. To take a stage of a
finished flow further, say so between flows, at the offer of the next flow: that flow is taken up again, only the
work its new pick needs is done, its pages are checked and reported again, and then the offer comes back. While a
flow is under way, the run finishes it first. A finished flow is never mapped again. A register from Release 7
carries on the same way.

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

## If the kit is updated while a run is under way

A run this kit picks up that an older kit wrote (in a new chat, on a resume, or when you replace the kit mid-run) is
upgraded without asking you, because the upgrade changes no content and the new kit cannot run the old form. When
the run picks the work up, its start step does this before it writes its first message to you, and that message
says so; the backup goes to `bfo-backups` in your computer's temporary folder. Otherwise the
run backs the register folder up to a folder outside the workspace (a copy inside it would be taken for an earlier
register), runs `python "<skill>/reconcile.py" --migrate "<register>"` on the register itself, in place, and runs
the check again. It then restarts the page's listener, which otherwise keeps running the old kit:
`python "<skill>/listener.py" stop "<work folder>"`, then `python "<skill>/wait_on_page.py" "<register>"`. It tells
you in one line what it did and where the backup is. Where the upgrade finds AI agent rows not classed (an
older kit classed which of an agent's actions are its decisions after mapping; mapping does it now), that line says
how many, and that mapping re-reads the code behind each tool, reply and chained action and classes it before
the run is done: a re-walk, announced before it starts and going ahead unless you object, as a correction to
mapping. For what the CHANGELOG's effect lines still name: a fill from
the register's own citations runs on its own and is announced; a re-walk, which reads the code again, is announced
before it starts, saying what will be re-read and why, and goes ahead unless you object; only a failed check makes it
a question, so only if the check still fails does the run stop and ask you. This is the run's own register; the earlier register of the section above is still never written into.

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
