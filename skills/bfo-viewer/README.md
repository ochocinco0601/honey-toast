# BFO viewer

A standalone page for looking at the registers that the business flow observability stage kit (`bfo-stage-kit`)
writes, with no run in progress. It has three screens: **Portfolio**, then an application's **Business flows** along the
8 milestones, then a flow's **Flow map** (the moving case, Repeat, overview / waterfall, measures by kind, a card per
measure). It only shows things. Deciding happens in the chat with the assistant.

It is a skill as well as a program: installed as `.claude/skills/bfo-viewer/`, Claude Code builds and opens the page
when you say "open the flow viewer", "show me the portfolio" or "show my business flows" (`SKILL.md`). It can also be
run by hand, as below.

## Using the page

- **Portfolio.** Each application's row shows its milestones and **Last updated**: the newest modified time of any file
  in its register. Click a heading to sort; Last updated sorts newest first. A register copied by git or a file
  transfer takes the time of the copy.
- **Flow map.** **Pause** and **Controls** sit at the right of the Flow map heading. Controls opens a panel with
  Repeat, View, **Size** (Fit, 100%, 125%, 150%), **Speed** (0.25x to 2x), **Measures** and a filter for one kind of
  measure. Size and Speed are remembered between flows and visits. At 100% and above the map keeps its size, the
  browser's zoom enlarges it, the card scrolls sideways with the names kept in view, and the card follows the moving
  case unless you have just scrolled it yourself.
- **Measures on the map.** One mark per kind of measure where it applies, with a number beside it when there is more
  than one; click a mark for those measures' cards. The **Key** (top right) explains every mark and colour.

## Install

Copy this folder to `.claude/skills/bfo-viewer/` (or anywhere, to run it by hand). Python 3.9 or later, standard library only.
It does not need the stage kit installed, and works whichever kit release wrote the registers.

## Run it

```
python viewer.py [FOLDER_OR_REGISTER ...] [--portfolio FILE] [--out PAGE]
```

- A folder that holds `flows.csv` is a register. For any other folder, the viewer reads every register one level down.
  With no folder given, it reads `./bfo-work`, where the stage kit keeps its runs.
- It writes one HTML file that opens from disk, with no server needed. The default is `<first folder>/viewer.html`.
- It prints the page's path, then one line for each flow or measure it could not draw, with the reason. A bad register
  never stops the page.
- To see it on the stage kit's own example, from this folder:
  `python viewer.py ../bfo-stage-kit/example-eshop --out viewer.html`

## The portfolio file (optional)

The viewer reads `portfolio.csv` from the folder it scans (beside the registers), or the file named with `--portfolio`.
The file is a CSV with the columns `application_id,application,division,line_of_business,sub_line,register,mock`.
Each row is one application.

- `register` is the register's folder name. Leave it blank for an application with no run yet.
- `mock` set to `yes` marks a row as invented. The EXAMPLE tag then shows on it.

Registers that the file does not list still appear, with division, line of business and sub-line shown as "not
recorded". With no file at all, every register is listed this way.

## The stage kit code it carries

The viewer carries its own copy of the stage kit's model code in `kit_copy/`, so it draws a flow the way the kit does
without depending on the kit release installed beside it. `kit_copy/FROM.txt` names the kit release it was copied from.
The copy changes only when the viewer is released again, on purpose and tested, never automatically.

## Files

| File | What it does |
|---|---|
| `SKILL.md` | What Claude Code does when you ask to see your business flows. |
| `viewer.py` | Finds the registers, joins them to the portfolio file and writes the page. |
| `flow_model.py` | Builds the data for each flow (`DATA`, `EXTRA` and `FLOWDRAW`), tolerant of missing files and columns. |
| `viewer.template.html` | The page the data is written into. |
| `kit_copy/` | The stage kit's model code the viewer runs on, and `FROM.txt` naming where it came from. |
