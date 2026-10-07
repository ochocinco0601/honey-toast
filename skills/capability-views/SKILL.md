---
name: capability-views
description: >
  Early release (0.1). Draw the design-for-operations map and views of one business capability: its
  flows, stages and steps, the parts carrying each step, what they depend on, any AI agent as its own
  system, what each layer could report, and where a failure reaches. Works from the code, documents and
  people the user points it at, through a register of tables, and draws one self-contained HTML page with
  a bundled Python program. Use when the user asks to "draw a capability's map and views",
  "design-for-operations views for [capability]", "map [capability] from these repos", or brings a new source (a
  repository, a document, a person's answers) for a capability that already has a map. Design time only:
  it describes what the capability is and where it could be seen, never live readings.
---

# Capability views (early release 0.1)

**What this is.** A procedure you follow with the user to describe one business capability in a register
(a folder of CSV tables) and draw its views. Every part of it is a draft, and the page says so. A person
judges the result.

**The skill folder** is the folder this `SKILL.md` is in. Below, `<skill>` means its full path, and
`<run>` means the capability's run folder. Every file named below is relative to the skill folder:

| File | Use it for |
|---|---|
| [FILL-STEPS.md](./FILL-STEPS.md) | **The detailed steps for filling a register.** Phase 2 follows it step by step |
| [register-template/REGISTER.md](./register-template/REGISTER.md) | What every table and column means. Read it before writing any row |
| [register-template/](./register-template/) | The blank register, copied into each run folder |
| [method/](./method/) | The method's closed lists: part kinds, layers, agent questions, involvement, impact categories, measure forms |
| [capability_views.py](./capability_views.py) | The program that checks a register and draws the page. Python 3, standard library only |
| [registers/eshop/](./registers/eshop/) | A filled register for a public sample shop, to see what finished rows look like. Shape, not content |

## Words

- **Flow** means a business process flow: one case's path from start to end as designed. A capability is
  delivered by one or more flows; a flow is made of **stages**; a stage of **steps**. A step is a business
  outcome that happened or did not ("The order is placed"), never the code that does it.
- **Not assessed** means looked for and not found, or not looked at. It is drawn from a blank cell. It never
  means absent.

## Rules that hold in every phase

- **Every row cites where it came from**: a file and line, a document and section, or a person by role and
  date. These carry the provenance labels:

  | Label | How it is written in the register |
  |---|---|
  | extracted | A file and line produced by a tool (the code reader), in `source` or `source_ref` |
  | proposed | The value starts with `proposed:`, or `source` is `proposed` |
  | gapped | The cell is left blank. `about.csv` → `sources_examined` and `sources.csv` say what was read |
  | ratified | A person's yes, recorded as a `how-made.csv` row with `done_by` `person confirming`, naming who and when |

- **Never write "none", "n/a" or "no owner" into a cell.** Leave it blank.
- **Owners, responders, promises, volumes and thresholds come only from a document or a person.** Never
  infer them from code.
- **Calls between services come from a tool, or they are proposed.** An `interaction` row the code reader
  produced cites its file and line. One you wrote from reading code yourself gets `proposed:` in `source`.
  A model reading class or handler names is not evidence of how services connect.
- **These parts of the register are drafts in this release, and you present them as drafts:** the order of
  calls within a step (`sequence`), parts of an outside service (`part_of`), links to another owner's map
  (`map_link`), and how deep you went into an outside service. Fill them where the sources show them, and
  say they are drafts when you present the page.
- **`sequence` shows only a strict order.** One position number per call cannot show branches, parallel or
  asynchronous calls, loops or returns. Number the calls in a step only where they always run one after
  another. Where the code branches, runs calls in parallel or hands off asynchronously, leave `sequence`
  blank for those calls and say so in the `how-made.csv` row's `note`.
- **Do not change anything in the skill folder.** Everything you write goes in the run folder.

## The run folder

One folder per capability, at `capability-views/<capability-name>/` in the root of the workspace folder
open in VS Code, with the name in lowercase words joined by hyphens. It holds the register's tables, the
drawn page `views.html`, and anything a tool wrote (put tool output in `<run>/reader/`).

**If the folder already exists, this is a new pass over an existing map, not a new map.** Read its
`sources.csv` and `how-made.csv` first to see what earlier passes read and did, then follow "When
something new arrives" in [FILL-STEPS.md](./FILL-STEPS.md). Never rebuild a map that exists.

## Phase 0 — Frame the run

1. Ask the user, in one message, for whatever they have not already given:
   - the capability, in the business's own words;
   - the code: repository paths open in this workspace or on disk;
   - documents: runbooks, architecture pages, service catalogue entries, process descriptions;
   - people they can ask, by role.
2. Create the run folder by copying every file from `register-template/` into it, except `REGISTER.md`.
   Skip this if the folder exists.
3. List each source in `sources.csv` (the next pass number for a new pass), and write the first rows of
   `how-made.csv` as you go. FILL-STEPS "Before you start" says how.

## Phase 1 — Read the sources

- **Code, with a code reader where one is available.** If the design-for-operations skill is installed,
  its `fact-extractor/README.md` says how to run its reader over a repository with a service map; write
  its output into `<run>/reader/`. Its facts are `extracted`. If the reader is not installed, or Semgrep
  cannot run here, read the code yourself and cite file and line: those facts are `proposed`, and the
  `how-made.csv` row says the code was read by a model, not a tool.
- **What a reader did not reach** (a language it does not parse, a service that produced no facts) is read
  by hand, and the gap is written in that row's `note`.
- **Documents and people** give what code cannot: owners, responders, promises, volumes, tolerances, and
  the business's own names for the flows and stages. Ask the user the questions only people can answer, all
  at once, and carry on drafting while they answer.

## Phase 2 — Fill or update the register

Follow [FILL-STEPS.md](./FILL-STEPS.md) Steps 1 to 9 in order, writing one `how-made.csv` row per step.
Read [REGISTER.md](./register-template/REGISTER.md) for every column you fill. Look at
[registers/eshop/](./registers/eshop/) when you are unsure what a finished row looks like. Where the example
differs from REGISTER.md, REGISTER.md governs.

On a new pass, follow FILL-STEPS "When something new arrives" instead. Where two sources disagree, keep
both: add the new account as a second row, and write the disagreement in that pass's `how-made.csv`
`note`. A disagreement is a finding for a person to settle.

## Phase 3 — Check and draw

```
python "<skill>/capability_views.py" "<run>" --check
python "<skill>/capability_views.py" "<run>" --out "<run>/views.html"
```

Always pass `--out`. Without it the program writes inside the skill folder. Fix every error `--check`
reports and re-run it before drawing. Warnings are rows without a citation: cite them, or say why not.

Optional: `--open ST2,ST5` chooses which stages the map opens; `--fails <part>` chooses the failing part
in the "where a failure reaches" view.

## Phase 4 — Check and present

Open `views.html` and read the map first. Is this the capability? Are these its flows and stages? Does
each step have the parts you expected? Fix the register and draw again before presenting.

Then give the user, in this order:

1. **The page's path**, and one line on what it shows.
2. **What is not assessed**: the steps nothing was found carrying out, and the blank owners, responders and
   promises. Say which sources were read, so they know what "not found" covers.
3. **Where sources disagree**, from this pass's `how-made.csv` notes.
4. **What needs a person's yes**: every `proposed:` value that matters (flows, stages, promises, owners),
   grouped by the role who could confirm it. When someone confirms one, remove `proposed:` from the value,
   cite them, and add a `how-made.csv` row with `done_by` `person confirming`, naming who and when.
5. **The drafts** listed under the rules above, if the register uses any of them.

Say plainly that the page is a draft from an early release, and that it describes design, not a running
system.
