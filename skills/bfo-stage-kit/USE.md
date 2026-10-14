# Using the kit

**What it does.** An assistant follows this kit over an application's code and describes one business flow of it:
the case it carries (one order, one application), the states the case passes through, and the stages they fall
into. For one stage, it then produces four files you can take to the engineers who own the code:

| File | What it is |
|---|---|
| `STRUCTURE.md` | The stage drawn: its steps, the order a case takes through them, the alternative endings, and every part that carries each step or is needed by it |
| `MEASURES.md` | What could be measured for the stage, each step and each part, by layer (business health, business impact, application, system), marked *exists* or *proposed* |
| `ALERT.md` | The measures proposed for alerting on the stage: what each counts, what it rests on, and the values the operators must set |
| `RUNBOOK.md` | What the responder to an alert does: a short entry per alert (what fired, the opening checks, what to contain first, its own tests in order, each saying what a match means), then one shared section for the stage with every test written once, the causes the alerts share, the restores, and whom to escalate to |

Every claim cites the code as `file:line`. Anything the code does not state (owners, promises, volumes) is written
`proposed:` with the reason. The engineers can check both.

## What you need

- VS Code with GitHub Copilot Chat in **agent mode**, so the model can read files and run terminal commands.
- Python 3.9 or later on the path. Nothing else is installed.
- The code, or where it is: name the repositories, pages, diagrams and process descriptions in your request, and
  the run gets them. Code already open in the workspace is read too; where it spans several repositories, add each
  as a folder of one workspace. When the code calls a service whose code is not there, the run searches your code host for the repository behind it (and for repositories that call or deploy the flow's services) and gets that code too, with access you already have and read-only: it never requests access, enters credentials, or changes anything at the source, and `RUN.md` lists every source it fetched with what referenced it and why. To keep it to the sources you name, say *use only the sources I name*: it then neither searches nor fetches, and lists the rest under *still missing*.
- Every repository open as a folder of one workspace (a multi-root workspace when there are several), never in a
  temporary folder: the run's code tools reach only the open workspace, and a run that can't add them stops and asks.
  Keep your own working folder as the first folder of the workspace, so the skill, your notes and the register stay
  in reach (a skill is found in every folder's `.github/skills/`, and the first folder wins on a duplicate name),
  and add the repositories after it; or install the skill in `~/.copilot/skills/`.
- This folder, `bfo-stage-kit/`, in one of two places:
  - **as a skill** (the simpler way): copy it to `.github/skills/bfo-stage-kit/` in the workspace, or to
    `~/.copilot/skills/bfo-stage-kit/` for every workspace. Then ask Copilot in agent mode in your own words, for
    example *Map the main business flow of this application for operations*. The skill's `SKILL.md` tells it what
    to do, and the register goes to `bfo-work/<application>/` at the workspace root;
  - **or in the workspace**, used with the prompt below. The register then goes to `bfo-stage-kit/work/<application>/`.

## The prompt

Without the skill, copy it as it is into Copilot Chat in agent mode:

```text
Run bfo-stage-kit/SKILL.md for the application whose code is in this workspace, and any repositories,
documents or diagrams I name here, following its calls into any other code you can get, with
bfo-stage-kit/work/<application>/ as the register folder in place of bfo-work/<application>/. Its first act is
RUN.md; follow its phases to the end and finish only when run_status.py says DONE.
Do not stop to ask me anything. When you finish, tell me the folder, the flow and stage, the check results,
anything you could not do, and paste run_status.py's output.
```

To point it at sources, add one line at the end (optional): *These are the sources: …*, naming the repositories,
pages, diagrams and process descriptions.

**Every stage, one per run.** The map and the measures cover the whole flow in the first run. The coverage check
fails a run only on its own stage and the flow; what only other stages hold is a warning until their own runs, so
one stage's run passing does not mean the flow is covered. The failure modes, alerts and runbook (Step 11) are
written for one stage per run, to keep each run's reading bounded. A flow is covered when every stage has had its
Step 11 and its check passes: run it again on the same register for each of the
others, saying *Do Step 11 for stage <id> next, in the register in <folder>*. Each such run regenerates and checks
every stage already done, and is not finished until all of their checks pass. The first run takes the stage where a
case most often waits or can be left stranded, because that is where cases are lost first; to set the order
yourself, add one sentence at the end: *The stage I want first is …*.

**A capability served by many services or repositories.** The same instructions hold at any size; FILL-STEPS
covers what changes with the number of services. Tests of many parts of one kind become one sweep over all of them,
shared dependencies are tested first, and a called service's own databases are reached through its tests. Citations
are checked by sample, and every citation starts at the workspace root. The check errors only on the run's own
stage and the flow; another stage's gaps wait for that stage's run. A capability spread over several repositories is not
yet proven at that size. By default a run reads every service the flow touches. Two more things
help:
- only for a run that has to be cut, add: *For this run's stage, read the code of the services that carry it in full. For the flow's other services,
  read only what you need to place them, and gap their measures with the reason "not read in this run".* The runs
  for the other stages read their own services in full and replace those gaps.
- open each repository as a folder of one workspace, and list each in `sources.csv` with its commit.

Read `KNOWN-GAPS.md` for what is still open at that size.

The run takes a while. If the model stops partway, say *continue from where you stopped, following FILL-STEPS.md*.

**Where a run stands.** `RUN.md` in the register folder records each phase of the run as to do, doing, done or
blocked, with the files that prove it or the reason it is blocked. Whether the run is done is said by
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
assessed and disagreed. Alerts and runbooks from the earlier run are not carried: each stage gets its own new run.

The earlier in-place upgrade prompt is retired (CHANGELOG, Release 2).

## What comes out

In `bfo-work/<application>/` at the workspace root when the kit is installed as a skill, or in
`bfo-stage-kit/work/<application>/` when it is used with the prompt:

- the register, a set of CSV files: the model, row by row, each row cited;
- `stage-<id>/` holding the four files above;
- `views.html`, the same model drawn as one map, which opens in a browser: click a step, a part, a stage or the
  flow to light its chain and see its measures. `how-this-map-was-made.html` beside it says how the map was made, for whoever builds or checks it; each stage's
  `RUNBOOK.html` and `ALERT.html` sit in `stage-<id>/` beside it.

`example-eshop/` is a finished example of all of it, for every stage of eShop's order flow: "Place the order", "Accept the order", "Ship the order" and "Deliver the order".

## How to read it

1. **Start with `STRUCTURE.md`.** The diagram is Mermaid. VS Code's Markdown preview draws it from VS Code
   1.121 on; on an older version, install the Markdown Preview Mermaid Support extension. Arrows between steps follow one case; several arrows out of one step are
   alternatives. Check the stage's start and end, and the parts on each step, against what you know.
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
  `<kit>` is the folder the kit was copied to (`.github/skills/bfo-stage-kit` or `~/.copilot/skills/bfo-stage-kit` as a
  skill, `bfo-stage-kit` with the prompt) and
  `<register folder>` is the folder named above.
  It should report 0 errors.
- Open three or four `file:line` citations from the runbook and confirm the code says what the row says.
- The runbook's tests have not been run. Ask the code's engineers to run each one once, on a case whose answer they
  know, before anyone relies on it.
- Read `KNOWN-GAPS.md`: what the kit is known to get wrong.
- Take it as a draft for the engineers to correct. A correction goes back into the register, and the outputs are
  generated again. Tell the model what is wrong and which register row holds it.
