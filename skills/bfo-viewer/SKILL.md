---
name: bfo-viewer
description: Show the person their business flow observability work as one page in their browser - a portfolio of their applications, each application's business flows along the 8 milestones, and each flow's map with its measures - built from the registers the bfo-stage-kit and bfo-mapping skills write. Use when asked to "open the flow viewer", "show me the portfolio", "show my business flows", to see where the applications' flows stand, or to rebuild that page after a stage kit run. Not for a stage kit run in progress (the run has its own pages). Viewing only - deciding and changing anything happens in the chat, with the stage kit. Never edits a register.
---

# BFO viewer: the person's business flows, on one page

## The job this serves

The person takes their applications' business flows from a map to supported in production with the stage kit
(`bfo-stage-kit`, which maps with `bfo-mapping`), one flow per run, across many applications. Between runs they need to
see where everything stands: which applications have a run, which flows are mapped, how far each flow has got along
the 8 milestones, and what a flow's map and measures look like, so they can choose what to take up next with the kit.
This skill is the looking step. It receives the registers the kit wrote (folders holding `flows.csv`, normally under
`bfo-work/` in the workspace) and, optionally, a `portfolio.csv` placing the applications in the organisation. It hands
the person one HTML page, opened in their browser, and one line saying what it shows and where the file is. Done is
the person looking at their current work, all of it, and taking any decision or change back to the chat and the kit;
the page decides nothing and nothing here changes a register.

## What to do

`<skill>` is this folder. Python 3.9 or later, standard library only; it does not need the stage kit installed.

1. **Find the folder.** The folder the person names, else `bfo-work/` at the workspace root. If neither holds a
   register (a folder with `flows.csv`, or one level down), say so in one line and point them to the stage kit to
   make one; write nothing.
2. **Build the page:** `python "<skill>/viewer.py" "<folder>" --out "<folder>/viewer.html"`. If the folder the person
   named is itself a register (it holds `flows.csv`), write the page beside it instead, never into it:
   `--out "<its parent>/viewer.html"`, with no portfolio (it would list every other application as not mapped). A
   `portfolio.csv` in the folder given is read without naming it; add `--portfolio "<file>"` for one kept elsewhere.
   It prints the page's path followed by the counts drawn, then one line per flow or measure it could not draw.
3. **Open it in their browser** (the `--out` path, not the printed line):
   `python -c "import pathlib,sys,webbrowser; webbrowser.open(pathlib.Path(sys.argv[1]).resolve().as_uri())" "<page>"`
4. **Say in one line** what it shows (how many applications and flows drawn, as printed) and the file's path. Mention
   lines it could not draw only if there are any, briefly, with the register they came from.
5. **When they act on what they see** (map another flow, take a flow further, fix something shown wrong), that is the
   stage kit's work: load `bfo-stage-kit` (or `bfo-mapping` for a map only) and carry on there.

**Rebuild after a stage kit run:** run steps 2 to 4 again. The page is a snapshot; it never updates itself. A new
run of an application that already had one is written to a new register folder, `<application>-<yyyy-mm-dd>`, so the
page then lists the application twice, or a `portfolio.csv` row keeps pointing at the older run. When the folder holds
more than one register for the same application, say so in the same line. With the person's yes, point that
application's `register` cell in `portfolio.csv` at the newest folder. The older run still shows, as an application
of its own, for as long as it sits in the folder the page is built from; moving it elsewhere is the person's call,
never this skill's.

## The portfolio file (optional)

Without one, every register is listed with its division, line of business and sub-line shown as "not recorded". If
the person wants their applications placed, offer to fill `portfolio.csv` beside the registers (in `bfo-work/`) with
them: columns `application_id,application,division,line_of_business,sub_line,register,mock`, one row per application.
`register` is the register's folder name, blank for an application with no run yet (it is then listed as not mapped).
Leave `mock` blank (`yes` marks an invented row). Ask them for the organisation's names; never invent a division or
line of business. Then rebuild. This file is the only thing this skill writes besides the page.

## Never

- Edit, move or rewrite anything in a register. A wrong or missing thing on the page is fixed in the register through
  the stage kit, then the page is rebuilt.
- Treat the page as a place to decide or record. Viewing only: the person's decisions are made in the chat.
