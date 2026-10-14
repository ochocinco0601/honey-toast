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
- The application's code open in the workspace. Where it spans several repositories, add each as a folder of one
  workspace.
- This folder, `bfo-stage-kit/`, in one of two places:
  - **as a skill** (the simpler way): copy it to `.github/skills/bfo-stage-kit/` in the workspace, or to
    `~/.copilot/skills/bfo-stage-kit/` for every workspace. Then ask Copilot in agent mode in your own words, for
    example *Map the main business flow of this application for operations*. The skill's `SKILL.md` tells it what
    to do, and the register goes to `bfo-work/<application>/` at the workspace root;
  - **or in the workspace**, used with the prompt below. The register then goes to `bfo-stage-kit/work/<application>/`.

## The prompt

Without the skill, copy it as it is into Copilot Chat in agent mode:

```text
Follow bfo-stage-kit/FILL-STEPS.md from start to finish for the application whose code is in this workspace.
First read bfo-stage-kit/register-template/REGISTER.md and the reference files FILL-STEPS.md cites in
bfo-stage-kit/reference/. Look at bfo-stage-kit/example-eshop/ only to see what a finished register and its
outputs look like; it is a different application and never a source of facts.
Pick the application's main business flow: the one whose case the business most depends on. Do Step 11 first for the
stage of that flow where a case most often waits, or can be left stranded, and say which stage you chose and why.
Write the register into a new folder bfo-stage-kit/work/ named for the application, and generate the outputs with
flow_outputs.py exactly as Step 11 says.
Do not stop to ask me anything. Where the code does not say something, infer it and label it proposed: with the
reason. Never edit a generated file: fix the register and generate again.
When you finish, tell me the folder, the flow and stage you chose, the check results, and anything you could not do.
```

**Every stage, one per run.** The map, the measures and the coverage check cover the whole flow in the first run.
The failure modes, alerts and runbook (Step 11) are written for one stage per run, to keep each run's reading
bounded. A flow is covered when every stage has had its Step 11: run it again on the same register for each of the
others, saying *Do Step 11 for stage <id> next, in the register in <folder>*. The first run takes the stage where a
case most often waits or can be left stranded, because that is where cases are lost first; to set the order
yourself, add one sentence at the end: *The stage I want first is …*.

**A capability served by many services or repositories.** With many services in one repository the run still
passes its check; across several repositories it has not been tried yet. Either way, read
`KNOWN-GAPS.md` first: the runbook for a stage that many services carry is long. Two things help now:
- add: *For this run's stage, read the code of the services that carry it in full. For the flow's other services,
  read only what you need to place them, and gap their measures with the reason "not read in this run".* The runs
  for the other stages read their own services in full and replace those gaps.
- open each repository as a folder of one workspace, and write every citation as a path from the workspace root, so
  that no file is ambiguous between repositories.

The run takes a while. If the model stops partway, say *continue from where you stopped, following FILL-STEPS.md*.

## If you ran an earlier version of this kit

The register from that run is kept: it is the folder of CSV files the run wrote in `bfo-stage-kit/work/`, named for
the application. Before you replace the kit folder with this one, move that register folder out
of `bfo-stage-kit/` (to `bfo-work/` at the workspace root), so replacing the kit does not delete it. Then copy this
into Copilot Chat in agent mode, as it is:

```text
A register made with an earlier version of the bfo-stage-kit is in this workspace: a folder of CSV files including
steps.csv, measures.csv and failure-modes.csv, under bfo-work/ or bfo-stage-kit/work/. Find it and tell me its path.
The kit is the folder that holds flow_outputs.py, in .github/skills/bfo-stage-kit/ or bfo-stage-kit/.
Run the kit's flow_outputs.py on that register with --check, for the flow and stage that the register's stage-
folders are named for, as Step 12 of the kit's FILL-STEPS.md shows. For each failure, read the kit's KNOWN-GAPS.md,
find the note that begins "A register filled with an earlier version of this kit" for that failure, and change the
register as the note says, from the code in this workspace. Re-run the check after each change until it reports
0 errors. Then generate the stage files for every stage the register has a stage- folder for, and the map with the
kit's one_canvas.py into views.html in the register folder, with the commands FILL-STEPS.md gives.
Do not stop to ask me anything. Never edit a generated file: fix the register and generate again.
When you finish, tell me the register's path, what you changed and why, and the check results.
```

## What comes out

In `bfo-work/<application>/` at the workspace root when the kit is installed as a skill, or in
`bfo-stage-kit/work/<application>/` when it is used with the prompt:

- the register, a set of CSV files: the model, row by row, each row cited;
- `stage-<id>/` holding the four files above;
- `views.html`, the same model drawn as one map, which opens in a browser: click a step, a part, a stage or the
  flow to light its chain and see its measures. `how-this-map-was-made.html` beside it says how the map was made, for whoever builds or checks it; each stage's
  `RUNBOOK.html` and `ALERT.html` sit in `stage-<id>/` beside it.

`example-eshop/` is a finished example of all of it, for the stage "Accept the order" of eShop's order flow.

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
