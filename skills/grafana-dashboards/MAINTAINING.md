# Maintaining this skill

For whoever changes it: a person, or an assistant asked to. Read this before changing anything.

## What is here

| File | What it is | How it is checked |
|---|---|---|
| `SKILL.md` | The everyday procedure the assistant follows | A trial run (below) |
| `reference.md` | The occasional cases: creating, cloning, MCP-only, gcx, undone fixes, traps | A trial run |
| `LOCAL.md` | Your organisation's conventions and references; outranks the defaults | Kept by the team |
| `FOUNDATIONS.md` | Every Grafana behaviour the skill relies on, with source and how far it was checked | `dashio.py probe`, and the per-row checks |
| `dashcheck.py` | Offline checks: the declared-change comparison, numbers comparison, earlier changes held | `tests/` (run below) |
| `dashio.py` | Everything that talks to Grafana: get, put, create, history, version, values, probe | `dashio.py probe`, and a trial on a scratch dashboard |
| `new-dashboard.json` | A starter v2 dashboard that Grafana 13 accepts | Create it once on a scratch name |
| `tests/` | Tests for `dashcheck.py`; `fixtures/` holds Grafana responses (`v2_*`) and hand-written examples (`v1_*`, `v_*`) | `python -m pytest -q tests`, from this folder |

## What it is for

The failures it exists to stop: things nobody touched breaking or moving, changed panels showing
wrong or no data, problems when adding variables, naming and layout, fixes coming undone, the
assistant going round in circles, and dashboards drifting into a ball of mud. Each Grafana behaviour
it relies on is either checked on a live instance or traced to Grafana's source; `FOUNDATIONS.md`
says which, and how far.

## Changing it

1. **Write down what went wrong first**, before changing anything, in the field notes below: what
   was asked, what happened (as reported, including anything the reporter was unsure of), and which
   file or `FOUNDATIONS.md` row it touches. Then change the smallest thing that fixes it.
2. **Guidance** (what the assistant should do): edit `SKILL.md` for the everyday path, `reference.md`
   for an occasional case, `LOCAL.md` for anything specific to your organisation. Keep `SKILL.md`
   short: it is read on every change.
3. **A check** (`dashcheck.py`): add a test that fails first, using a real response saved with
   `dashio.py get` into `tests/fixtures/`, then change the script until `python -m pytest -q tests`
   passes. With no Grafana reachable, derive the fixture from an existing one, say so in a comment
   in the test, and replace it with a real response when one can be fetched.
4. **Talking to Grafana** (`dashio.py`) or **a Grafana behaviour**: update the `FOUNDATIONS.md` row,
   then run `python dashio.py probe` and the operation you changed against a scratch dashboard. If
   no Grafana is reachable, set the row's Checked column to `source only` and write the owed check
   in the field note; it is done on the next run against a real instance.
5. **Trial it.** Give a fresh assistant chat only this folder and a small real request on a copy of
   a dashboard, and read where it hesitated or improvised. That is where the text is unclear. An
   assistant that made the change cannot be its own trial: it asks the user to open the fresh chat,
   and records the trial as owed until it is done.
6. **Record it.** Bump the version line at the top of `SKILL.md` once per maintenance session,
   however many fixes it holds, and add a changelog line below, naming any check still owed. An
   assistant that changes this skill shows the change to the user before it is used.

`LOCAL.md` is the team's own file: filling in or correcting an entry there is not a change to the
skill and needs no version bump.

**If a newer version of the skill arrives from elsewhere**, keep `LOCAL.md` and the field notes, and
compare your own changes with it before replacing files.

## Field notes

What went wrong in real use, newest first. One line each:
date | what was asked | what went wrong | file or FOUNDATIONS row | fixed in version

- (none yet)

## Changelog

- **1.3 (2026-10-02)**: `MAINTAINING.md`, `FOUNDATIONS.md`, `LOCAL.md`; `dashio.py probe` for the
  first run on an instance; tests travel with the skill; a 404 names the namespace in use.
- **1.2 (2026-10-02)**: everyday procedure in `SKILL.md`, occasional cases in `reference.md`; bulk
  changes; lighter design brief; undone fixes reported from the history without a named cause;
  `released.txt`; past versions fetchable; clones get their own internal id; starter dashboard.
- **1.1 (2026-10-01)**: Grafana 13 v2 dashboards; `dashio.py` for every transfer; numbers check;
  variables, layout and naming; the design brief.
- **1.0 (2026-10-01)**: declare, edit in place, check, save with a version check.
