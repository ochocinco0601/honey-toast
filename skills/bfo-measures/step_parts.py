"""The parts of the step under way and a count, for the run status page's progress column: read from the files the run
writes as it goes, never from what the lead says. One helper for every step whose files show its parts:

  1  discovery    each source the person gave: done once its record is written (a code source once the survey lists
                  its repository; any other once every part first-look/parts.csv owes has its record)
  3  mapping      each unit of the fast map's reading plan, done once its files.csv is written and not left
                  unfinished; while a round of checks is open, each unit's checks returned of those selected
  5, 7, 9         each stage picked that far, done once its MEASURES.md, ALERT.md or RUNBOOK.md is written
  10 verify       the checks, as in mapping, while a round is open

Every other step (the decisions, the report, the next flow) shows no parts: nothing the run writes counts them.
Times are this flow's: a file written before its go (or before the first look's window) never counts as done."""
import csv
import datetime as dt
import io
import json
import pathlib
import re

DONE, WORKING, TODO = "done", "reading", "to do"
MAX_SHOWN = 12  # parts listed under the step; the rest are counted in one line


def _text(p):
    try:
        return pathlib.Path(p).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return ""


def _csv(p):
    t = _text(p)
    return list(csv.DictReader(io.StringIO(t))) if t else []


def _json(p):
    try:
        return json.loads(_text(p) or "null")
    except ValueError:
        return None


def _when(v):
    try:
        t = dt.datetime.fromisoformat(str(v))
    except (TypeError, ValueError):
        return None
    return t.timestamp() if t.tzinfo else None


def _since(p, t0):
    try:
        return p.is_file() and (t0 is None or p.stat().st_mtime >= t0)
    except OSError:
        return False


def _plural(n, one, many):
    return f"{n} {one if n == 1 else many}"


def discovery(reg):
    """(summary, [(source, state)]) of the first look, or None before it has listed its sources."""
    sources = [r for r in _csv(reg / "sources.csv") if (r.get("source_id") or "").strip()]
    if not sources:
        return None
    mode = _json(reg / "first-look" / "mode.json") or {}
    t0 = _when(mode.get("window_start"))
    owed = {}
    for r in _csv(reg / "first-look" / "parts.csv"):
        sid, part = (r.get("source_id") or "").strip(), (r.get("part") or "").strip()
        if sid:
            owed.setdefault(sid, []).append(sid if part in ("", "whole") else f"{sid}-{part}")
    surveyed = {(r.get("repository") or "").strip().lower() for r in _csv(reg / "survey.csv")} \
        if _since(reg / "survey.csv", t0) else set()
    parts = []
    for r in sources:
        sid = r["source_id"].strip()
        if (r.get("kind") or "").strip().lower() == "code":
            done = (r.get("repository") or "").strip().lower() in surveyed
        else:
            keys = owed.get(sid) or [sid]
            done = all(_since(reg / "first-look" / f"{k}.json", t0) for k in keys)
        parts.append(((r.get("what") or sid).strip(), DONE if done else WORKING))
    found = []
    o = _json(reg / "orientation.json") or {}
    flows = o.get("flows") if isinstance(o.get("flows"), list) else None
    if flows is None:  # before the orientation: the flows the readers' records name so far
        names = set()
        for f in (reg / "first-look").glob("*.json"):
            if f.name != "mode.json" and _since(f, t0):
                for x in (_json(f) or {}).get("leads") or []:
                    if isinstance(x, dict) and x.get("kind") == "flow" and (x.get("name") or "").strip():
                        names.add(x["name"].strip().lower())
        flows = sorted(names)
    services = [r for r in _csv(reg / "survey.csv") if (r.get("kind") or "service") == "service"] \
        if _since(reg / "survey.csv", t0) else []
    if flows:
        found.append(_plural(len(flows), "flow", "flows"))
    if services:
        found.append(_plural(len(services), "service", "services"))
    n = sum(1 for _, s in parts if s == DONE)
    summary = f"Reading {_plural(len(parts), 'source', 'sources')}: {n} done"
    return summary + (f" · {', '.join(found)} so far" if found else ""), parts


def checking(reg, t0):
    """(summary, [(unit, "n of m returned")]) of the latest round of checks written since the go, or None."""
    try:
        import judges
        got = judges.settings(reg)
        n_judges = int(got["judges"])
    except Exception:  # noqa: BLE001 - a settings file mid-write, or a kit without judges: no parts this time
        return None
    folder = reg / "judging"
    rounds = {}
    for d in folder.iterdir() if folder.is_dir() else ():
        for p in d.glob("r*-rows.csv") if d.is_dir() else ():
            m = re.match(r"r(\d+)-rows\.csv$", p.name)
            if m and _since(p, t0):
                rounds.setdefault(int(m.group(1)), []).append((d.name, p))
    if not rounds:
        return None
    rnd = max(rounds)
    parts, total, back = [], 0, 0
    for unit, p in sorted(rounds[rnd]):
        rows = _csv(p)
        done = sum(1 for r in rows if all(_since(folder / unit / judges.verdict_name(
            rnd, j, r.get("table", ""), r.get("row", ""), r.get("hash", "")), t0) for j in range(1, n_judges + 1)))
        parts.append((unit, f"{done} of {len(rows)} judged"))
        total, back = total + len(rows), back + done
    return f"Checking {_plural(total, 'finding', 'findings')}: {back} judged", parts


def mapping(reg, t0):
    """(summary, [(unit, state)]) of the fast map's reading plan, or None (a full map's progress is said in its line)."""
    plan = [(r.get("unit") or "").strip() for r in _csv(reg / "fast" / "reading-plan.csv")]
    units = list(dict.fromkeys(u for u in plan if u))
    if not units:
        return None
    marked = {}
    for f in sorted((reg / "fast" / "mappers").glob("*/mapper-status.csv")) + [reg / "fast" / "mapper-status.csv"]:
        for r in _csv(f):
            marked[(r.get("unit") or "").strip()] = (r.get("status") or "").strip().lower()
    parts = [(u, DONE if _since(reg / "units" / u / "files.csv", t0) and marked.get(u) != "unfinished" else WORKING)
             for u in units]
    n = sum(1 for _, s in parts if s == DONE)
    return f"Mapping {_plural(len(units), 'unit', 'units')}: {n} done", parts


OUTPUT = {5: ("Measures", "MEASURES.md", ("measure", "alerting", "runbooks")),
          7: ("Alerts", "ALERT.md", ("alerting", "runbooks")),
          9: ("Runbooks", "RUNBOOK.md", ("runbooks",))}


def stages(reg, n, scope, t0):
    """(summary, [(stage, state)]) for the stages picked as far as step `n`'s output, or None when none is."""
    what, file, depths = OUTPUT[n]
    picked = [st for st, d in (scope.get("depth") or {}).items() if d in depths]
    if not picked:
        return None
    names = {(r.get("stage") or "").strip(): (r.get("name") or "").strip() for r in _csv(reg / "stages.csv")}
    parts = [(f"{st} {names.get(st, '')}".strip(), DONE if _since(reg / f"stage-{st}" / file, t0) else TODO)
             for st in picked]
    done = sum(1 for _, s in parts if s == DONE)
    return f"{what} for {_plural(len(picked), 'stage', 'stages')} picked: {done} done", parts


def of(reg, n, scope, now=None):
    """{"summary", "parts"} for step `n` (its number on the page's list of twelve) from the run's files, or None."""
    reg = pathlib.Path(reg)
    t0 = _when((scope or {}).get("given"))
    try:
        if n == 1:
            got = discovery(reg)
        elif n in (3, 10):
            got = checking(reg, t0) or (mapping(reg, t0) if n == 3 else None)
        elif n in OUTPUT:
            got = stages(reg, n, scope or {}, t0)
        else:
            got = None
    except OSError:
        got = None
    if not got:
        return None
    summary, parts = got
    return {"summary": summary, "parts": parts}


UNFINISHED = "not finished"


def settled(got, run):
    """The parts as the page may say them for a run in this state (run_state.of, the one state the badge, the title
    and the watchdog read): a part still under way is said to be "reading" only while the run is in motion (working
    or quiet); stopped, waiting or finished, it is "not finished" (a stopped run must never look busy)."""
    import run_state
    if got is None or run in run_state.IN_MOTION:
        return got
    summary = re.sub(r"^(Reading|Mapping|Checking) ", "", got["summary"])  # no verb of work under way
    return dict(got, summary=summary[:1].upper() + summary[1:],
                parts=[(name, s if s == DONE else UNFINISHED) for name, s in got["parts"]])


def html_list(got, escape):
    """The parts as the short list under the step: the first MAX_SHOWN, then one line counting the rest."""
    shown = got["parts"][:MAX_SHOWN]
    items = "".join(f'<li class="{escape(s.replace(" ", "-"))}"><span>{escape(name)}</span> '
                    f'<span class="ps">{escape(s)}</span></li>' for name, s in shown)
    more = len(got["parts"]) - len(shown)
    if more > 0:
        items += f'<li class="more">and {more} more</li>'
    return f'<ul class="parts">{items}</ul>'
