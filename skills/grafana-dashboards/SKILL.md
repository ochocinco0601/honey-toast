---
name: grafana-dashboards
description: Create, clone, modify, re-lay-out or bulk-change Grafana dashboards (Grafana 13, classic and v2 JSON) without regressions. Every change is declared first, made by editing the JSON Grafana returned, checked by scripts that fail on any undeclared change, any declared change not made and any panel whose numbers move unexpectedly, saved with a conflict check and verified live. Earlier fixes are re-checked, and a short design brief keeps a dashboard coherent as it grows. Use for any create, edit, clone, move, resize, rename, add or remove panel, row or variable, query change or bulk edit on Grafana dashboards.
---

# Changing Grafana dashboards without regressions

Skill version: 1.3 (2026-10-02). Tested against Grafana Enterprise 13.0.10.
Beside this file: `LOCAL.md`, your organisation's conventions and references, which outranks the
defaults here; `reference.md`, the occasional cases (creating, cloning, the MCP-only route, Grafana's
own tools, library panels, dashboards managed from files or git, an undone fix, traps);
`FOUNDATIONS.md`, every Grafana behaviour this skill relies on and where it came from; and
`MAINTAINING.md`, how to change the skill and where to record what goes wrong.

| What goes wrong | Why | The check |
|---|---|---|
| Something nobody touched breaks or moves | The dashboard is regenerated instead of edited | Declare the change; `dashcheck.py check` fails on anything outside it |
| The changed panel shows wrong or no data | The JSON is valid but the query is wrong | Panel numbers before and after, from code, over one fixed time range |
| A fix comes undone later | A later save carries an older copy | Every earlier saved change is re-checked before a new one |
| The assistant goes round in circles | Too much at once; guessing instead of looking | One change per pass, numbers checked before saving, two failed attempts and stop |
| The dashboard drifts into a ball of mud | Each change is right on its own | A design brief that structural changes must fit |

**Two rules hold everywhere.** Any change outside the declaration is a regression until the user
says otherwise. Dashboard JSON moves between Grafana and files only by a tool (`dashio.py`,
`curl`), never by you retyping a tool result: a copying slip lands in both the before and the after
copy, so no comparison can see it, and then it goes live.

## Setup, once per session

Commands below write `$SKILL` for the folder holding this file; the scripts need only Python 3.

- **Read `LOCAL.md` first.** It says which folders you may change, the naming and layout
  conventions, the approved data sources, who owns what, and which internal references to look up.
  An entry still showing `[YOUR ORGANIZATION: ...]` is unknown: ask, never guess.
- **First use on a Grafana instance, or after it is upgraded:** run
  `python $SKILL/dashio.py probe <work>/probe-<date>.md <folder uid you may use>`. It tries, on a
  throwaway dashboard it creates and deletes, the behaviours this skill relies on, and records the
  result. If any check does not hold, stop and tell the user: the skill's safety depends on it.
  Record the date and result under "Last probe" in `LOCAL.md`.
- **When something here turns out to be wrong** (Grafana behaves differently, a path does not
  match, a step cannot be followed): tell the user, find the fact it rested on in `FOUNDATIONS.md`,
  and add a line to the field notes in `MAINTAINING.md`. Change the skill only as `MAINTAINING.md`
  describes, and show the user the change before using it.

- **HTTP API from the terminal** (full checks): `GRAFANA_URL`, and `GRAFANA_TOKEN` holding a
  service account token with edit rights on the folders concerned. A service account rather than the
  user's own login, so the assistant's saves show under their own name in the version history
  (`GRAFANA_USER`/`GRAFANA_PASSWORD` only where tokens are not available). For an organisation other
  than the first set `GRAFANA_NAMESPACE=org-<id>` (from `LOCAL.md`; without it every call returns 404); a company certificate authority goes in
  `SSL_CERT_FILE`, a proxy in `HTTPS_PROXY`/`NO_PROXY`. Confirm with
  `python $SKILL/dashio.py history <uid>`. If something is missing, tell the user once what to set:
  it is what makes the checks possible.
- **Only an MCP server**: follow "When you only have an MCP server" in `reference.md`.
- Tell the user in one line which route you are on.

## Working folder

`~/grafana-dashboard-work/` unless the user names another, outside any application repository;
never commit dashboard files to the workspace's repository without asking. A new session looks
there first, and every report ends with the folder's path.

```
<work>/<uid>/DESIGN.md            the design brief, when there is one
<work>/<uid>/LOG.md               one line per pass: date | folder | DESIGN.md item | what changed |
                                  check results | confirmed by | generation
<work>/<uid>/changes/003-p99/     before.json allow.txt after.json live.json
                                  values_before.json values_after.json attempts.md released.txt
```

Number change folders `001`, `002`, ..., the next always one above the highest, never reusing a
number. A pass counts as an earlier change once it was saved
(`live.json` exists); a refused or abandoned pass is ignored.

## Every change

A *pass* is one thing the user asked for, however many fields it touches: a new variable and the
panels that use it are one pass. Several requests are several passes, each saved and checked before
the next. If step 1 finds an earlier fix undone, settle that with the user first.

1. **Fetch** into a new change folder: `python $SKILL/dashio.py get <uid> changes/<n>/before.json`.
   From `<work>/<uid>/`, run `python $SKILL/dashcheck.py held changes changes/<n>/before.json`.
   On FAIL, stop and follow "When a fix has come undone" in `reference.md`.
2. **Declare** in `allow.txt` the paths that will change, one per line, as `dashcheck.py` prints
   them; `python $SKILL/dashcheck.py paths before.json panel-2` lists the paths containing `panel-2`.
   v2 examples: a title `elements.panel-2.spec.title`; a query
   `elements.panel-2.spec.data.spec.queries[refId=A].spec.query.spec.expr`; a query variable's
   query `variables[name=job].spec.query.spec.query`; an added or removed variable
   `variables[name=region].*`; a resize
   `layout.spec.rows[title=Details].spec.layout.spec.items[el=panel-2].spec.height` (a row without a
   header has an empty title, `rows[title=]`); a tag added `tags*`. Classic examples: `panels[id=4].targets[refId=A].expr`,
   `templating.list[name=env].query`. `*` matches anything; a leading `?` marks a path that may stay
   unchanged. For a structural pass, the first line is a `#` comment naming the `DESIGN.md` item it
   serves. Show the declaration to the user before saving unless the pass changes one display
   property of one panel, or the dashboard's title, tags or description.
3. **Edit, never regenerate.** Copy `before.json` to `after.json` and change only the declared
   fields with a short script (load the JSON, set the fields, write it back). Address panels by
   element name (v2) or `id` (classic), never by position.
4. **Check the JSON:** `python $SKILL/dashcheck.py check before.json after.json --allow-file allow.txt`
   must print `RESULT: PASS`. For each `!!` line, undo it, or, if it is truly needed, add it to the
   declaration and tell the user why. Never widen the declaration to make it pass. "Declared but did
   not change" means the edit missed. Problems "already present before the change" go in the report
   and are not fixed now.
5. **Check the numbers before saving**, when the pass touches a query, a variable or a data source.
   Pick a fixed range in absolute UTC times (for live data, ending at least 15 minutes ago so late
   data cannot move the numbers). Run `python $SKILL/dashio.py values before.json values_before.json
   --from <t1> --to <t2>` and the same for `after.json` (it runs the queries from the file, with each
   variable at its saved value; nothing is saved). Then `python $SKILL/dashcheck.py values
   values_before.json values_after.json --changed <panel> <panel> ...`, naming the declared panels
   and every panel `check` listed under "panels using the changed variables".
   - `!!` fails: a panel outside the change whose numbers moved, or a changed panel that is empty or
     erroring after the change.
   - `??` goes to the user as before and after numbers, with the question whether they are right.
     The user's yes is the check: a valid query can still count the wrong thing. "Numbers unchanged"
     means the change does not show in numbers (a legend, an alias, a display setting): give the
     step 7 link instead.
   - `..` is a panel outside the change that was already empty or failing: report it; this pass did
     not cause it.
   - A capture error naming a variable with no saved value: set a value in a scratch copy, capture
     from that, and discard it.
6. **Save:** `python $SKILL/dashio.py put after.json "<the declaration in one line>"`. `CONFLICT`
   means a save happened after your fetch: start again in a new folder from step 1. Never force a
   save and never remove `metadata.resourceVersion`; without it Grafana 13 saves over whatever is
   there.
7. **Verify live:** `python $SKILL/dashio.py get <uid> live.json`, then
   `python $SKILL/dashcheck.py check after.json live.json`; report any difference, since it is
   something Grafana changed on save. A change to how a panel looks (unit, decimals, thresholds,
   colours, overrides, transformations) cannot show in numbers: give the user
   `<GRAFANA_URL>/d/<uid>?viewPanel=<panel>&from=<t1>&to=<t2>` to look at. For a resize or move, give
   the dashboard link and say what now sits beside it.
8. **Log and report** in a few lines: the declaration, the check results, the numbers the user
   confirmed or the link they looked at (whichever applied), the new generation, how to roll back
   (Dashboard settings, Versions, Restore), and the working folder. Add the line to `LOG.md`,
   creating it if needed; the `DESIGN.md` item is `-` for a pass that is not structural.

**Light path.** A pass that touches no query, variable or data source (title, description, unit,
thresholds, colours, links, layout) skips step 5: the JSON check already proves nothing else
changed, and step 7's link covers how it looks.

## Changing many dashboards

Write the edit once, as one script that every dashboard's `before.json` goes through, so each gets
the identical change. Run the first dashboard through every step and show the user. Then the rest,
one change folder each, the same declaration, the light path where it applies, and the numbers check
for each if queries change. Stop at the first FAIL and report. Finish with a table: dashboard,
check result, numbers, new generation. A change applied the same way everywhere needs no design
brief.

## Holding the whole picture

Each pass can be right on its own while the dashboard drifts into a ball of mud: panels nobody can
say the purpose of, rows that overlap, three variables doing one job. Single-change checks cannot see
that; a design every change answers to can (conceptual integrity, in Brooks's term).

- **The design brief**, `DESIGN.md`, kept short. First line `Owner: <name>`; then who reads the
  dashboard and when; the questions it answers, in the order a reader asks them; each row and what it
  is for; the variables and what each selects; naming and sizing conventions; what does not belong
  here. It is needed when creating a dashboard and before a *structural* pass (one that adds or
  removes a panel, row or variable, or serves a new reader), not for a fix inside existing panels. If
  there is none at that point, draft one from what the dashboard shows, mark it `proposed` and show
  the owner. The owner decides what it says; you propose.
- **Structural passes name their place in it** (step 2). If a pass fits nothing in the brief, stop
  and say so: it belongs on another dashboard, or the brief changes first, and that is the owner's
  call.
- **A design review** by a fresh assistant chat that made none of the changes, given only `DESIGN.md`
  and a fresh fetch, going panel by panel: keep, fix or remove, with a reason each (the
  dashboard-evaluation skill does this). It runs when the owner asks; `LOG.md` records the date of
  the last one, and after a few structural passes since then you may suggest one.

## Adding or changing a variable

- **Order matters.** A variable used in another variable's query must come before it. `check` shows
  a reorder of existing variables as `variables.(order)`; adding or removing one is not a reorder.
- **Change the panels in the same pass.** Declare every panel that should filter by the new variable;
  every other panel stays unchanged. `check` lists the panels using a changed variable; include them
  in the numbers check.
- **Multi-value and All.** Inside a regex or a `=~` matcher write `${var:regex}`, not `$var`, or the
  query breaks as soon as two values are selected. If the variable allows several values or All,
  capture numbers with one value, several and All, each set in a scratch copy.
- **The default is a decision.** The saved `current` value is what everyone sees on opening, and what
  any link without this variable gets. Set it deliberately and declare it.
- **The variable's own query** is not run by these scripts. Ask the user to open the variable's edit
  view and check the preview of values, or run it with an MCP query tool, and say which; an empty
  drop-down passes every other check.
- Panels or rows repeated by the variable multiply with it; check how many appear with All.

## Layout, naming and organisation

- **Position is part of the change.** Moving or resizing a panel is a declared change to the layout
  paths concerned. Moving a panel between rows removes it from one row's items and adds it to
  another's; declare both. Renaming a row shows as the old row removed and a new one added; declare
  both titles with `.*`.
- **Every panel must be placed.** `check` fails when a panel sits in no layout (it disappears from
  the dashboard) or the layout points at a panel that does not exist.
- **Overlaps** are reported as warnings; fix them unless the user wants them.
- **Naming and grouping:** follow `DESIGN.md`; the dashboard-evaluation skill judges each panel
  against its reader's question. Without either: a title says what is measured and for what, the unit
  goes in the unit setting rather than the title, what a reader needs first goes top left, a summary
  row comes first and detail rows below, the same kind of panel gets the same size.

## Staying out of circles

- One pass at a time, checked and saved before the next starts. Read only what the pass needs.
- When a panel is wrong, look at what its query returns before changing anything.
- **Record every failed attempt** in the change folder's `attempts.md`: what you tried, what came
  back. **After two on the same thing, stop**, report them and your best explanation, and ask. The
  count lives in the file, so a new session continues it rather than starting again.
