# Using the kit

**What it does.** An assistant follows this kit over an application's code and describes one business flow of it:
the case it carries (one order, one application), the states the case passes through, and the stages they fall
into. For one stage, it then produces four files you can take to the engineers who own the code:

| File | What it is |
|---|---|
| `STRUCTURE.md` | The stage drawn: its steps, the order a case takes through them, the alternative endings, and every part that carries each step or is needed by it |
| `MEASURES.md` | What could be measured for the stage, each step and each part, by layer (business health, business impact, application, system), marked *exists* or *proposed* |
| `ALERT.md` | The one alert that pages for the stage: what it counts, and the values the operators must set |
| `RUNBOOK.md` | What the person paged does: tests in order, each with where every result leads, the restores, and when to escalate |

Every claim cites the code as `file:line`. Anything the code does not state (owners, promises, volumes) is written
`proposed:` with the reason. The engineers can check both.

## What you need

- VS Code with GitHub Copilot Chat in **agent mode**, so the model can read files and run terminal commands.
- Python 3.9 or later on the path. Nothing else is installed.
- The application's code open in the workspace. Where it spans several repositories, add each as a folder of one
  workspace.
- This folder, `bfo-stage-kit/`, in the same workspace.

## The prompt

Copy it as it is into Copilot Chat in agent mode:

```text
Follow bfo-stage-kit/FILL-STEPS.md from start to finish for the application whose code is in this workspace.
First read bfo-stage-kit/register-template/REGISTER.md and the reference files FILL-STEPS.md cites in
bfo-stage-kit/reference/. Look at bfo-stage-kit/example-eshop/ only to see what a finished register and its
outputs look like; it is a different application and never a source of facts.
Pick the application's main business flow: the one whose case the business most depends on. Do Step 11 for the
stage of that flow where a case most often waits, or can be left stranded, and say which stage you chose and why.
Write the register into a new folder bfo-stage-kit/work/ named for the application, and generate the outputs with
flow_outputs.py exactly as Step 11 says.
Do not stop to ask me anything. Where the code does not say something, infer it and label it proposed: with the
reason. Never edit a generated file: fix the register and generate again.
When you finish, tell me the folder, the flow and stage you chose, the check results, and anything you could not do.
```

To choose the stage yourself, add one sentence at the end: *The stage I want is the one where …*, in your own words.

The run takes a while. If the model stops partway, say *continue from where you stopped, following FILL-STEPS.md*.

## What comes out

In `bfo-stage-kit/work/<application>/`:

- the register, a set of CSV files: the model, row by row, each row cited;
- `stage-<id>/` holding the four files above;
- `views.html`, the same model drawn as views, which opens in a browser.

`example-eshop/` is a finished example of all of it, for the stage "Accept the order" of eShop's order flow.

## How to read it

1. **Start with `STRUCTURE.md`.** The diagram is Mermaid. VS Code's Markdown preview draws it from VS Code
   1.121 on; on an older version, install the Markdown Preview Mermaid Support extension. Arrows between steps follow one case; several arrows out of one step are
   alternatives. Check the stage's start and end, and the parts on each step, against what you know.
2. **`ALERT.md`** says what pages and what it counts. The threshold, the window and the time limit are left for
   the operators to set.
3. **`RUNBOOK.md`**: section 0 restates the stage; section 4 is the walk. Each test row says what to look at, what
   a healthy result looks like and where it leads, what the failure looks like and its ending, and where anything
   else leads. Section 10 traces each test to the register row it came from.
4. **`MEASURES.md`** lists every measure. *Proposed* means nothing emits it today.

## Before you take it to anyone

- Run the check yourself: `python bfo-stage-kit/flow_outputs.py bfo-stage-kit/work/<application> <flow id> <stage id> --check`.
  It should report 0 errors.
- Open three or four `file:line` citations from the runbook and confirm the code says what the row says.
- Read `KNOWN-GAPS.md`: what the kit is known to get wrong.
- Take it as a draft for the engineers to correct. A correction goes back into the register, and the outputs are
  generated again. Tell the model what is wrong and which register row holds it.
