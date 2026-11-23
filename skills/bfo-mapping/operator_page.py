"""The operator view of a run: where it stands, what it needs from the person, and what is wrong, at a glance.
    python operator_page.py <register folder> [--out <file>]     writes <reg>/operator.html (or --out)
The listener (page_ask.py) draws the same page on each request for <run>/operator.html, so an open tab, which
reloads itself every 15 seconds while it is shown, follows the run with no step of the run's own. The work folder's own <work>/operator.html, the page the start
step opens, leads to the newest run's view, and before any run folder exists draws the first look under way.
Four panels, the same in every state: the title and the run's status; Progress, the run's whole path read from the
Status table of RUN.md (each row a step, in its order, named as the kit's status line names it to the person with
the record's own name kept beside it, rows that are not numbered phases tagged as the person's decisions, every
step on its own line, the ones the pick left out too, finished steps told by what they hold, in flows, stages, steps and
services, and linked to the pages they left; process mapping, while it runs, told by how far the record shows it is:
services read, calls left unmatched, findings judged in the latest round, flagged ones changed, and nothing where the
record cannot say; a flow the run chose itself, because the request named none, told as chosen by the run with its
reason, never as the person's decision); Required action, the choice the record says the run waits on
(depth.json's open choice, whichever row is current), or how to resume it, or what the run is doing for the person
and when they are next needed, and no Required action and no badge on a register opened to carry on (its say-back
of kind resume waiting) while nothing else waits on the person; Issues, one line each with what clears it. Times are the ones the record holds
(scope.json for the person's decisions and the report sent, RUN.lock for the run's last write, run-started.json for
the start); a step the record keeps no time for says so and is never given one. It only reads: no lock is taken and no file of the register is written,
except the page itself when run from the command line. Python standard library only."""
import datetime as dt
import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

FILE = "operator.html"
RUNNING_MINUTES = 10  # a write this recent: the run is at work
try:
    import run_lock
    STALE_MINUTES = run_lock.STALE_MINUTES
except ImportError:  # pragma: no cover - the kit always ships it
    STALE_MINUTES = 240
E = html.escape
DONE, NOT_PICKED, DOING, BLOCKED = "done", "not picked", "doing", "blocked"
IDLE = "idle"  # a register opened to carry on, with no run under way and nothing waiting on the person
FILE_RE = re.compile(r"[\w.\-/]+\.(?:csv|json|md|html)\b")
# The person's decisions the run records with a time (go.py writes them into scope.json), by the row they close.
DECISION_TIMES = (("review of the alerts", ("alerts_reviewed", "given")),
                  ("review of the measures", ("measures_reviewed", "given")),
                  ("pick of", ("depth_picked", "given")),
                  ("go", ("given",)))
# What the person decided, where scope.json keeps it, by the row it closes.
DECISION_SAID = (("review of the alerts", ("alerts_reviewed", "words")),
                 ("review of the measures", ("measures_reviewed", "words")),
                 ("pick of", ("depth_picked", "words")),
                 ("go", ("flow",)))
try:  # the kit's own names for the run's steps, the ones its status line gives the person
    import brief
except ImportError:  # pragma: no cover - the kit always ships it
    brief = None
# What a step's tables hold, told as a count of the things in them; a table not named here is not counted.
NOUNS = {"flows.csv": ("flow", "flows"), "stages.csv": ("stage", "stages"), "steps.csv": ("step", "steps"),
         "subjects.csv": ("service", "services"), "measures.csv": ("measure", "measures"),
         "alerts.csv": ("alert", "alerts"), "failure-modes.csv": ("failure mode", "failure modes")}
PAGE_NAMES = {"views.html": "Map", "how-this-map-was-made.html": "How the map was made"}
# The home page takes the answer to these choices; any other is given in the run's chat.
ON_PAGE = ("Mapped", "Measures defined")


def _text(p):
    try:
        return pathlib.Path(p).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _json(p):
    try:
        return json.loads(_text(p) or "null")
    except ValueError:
        return None


def _csv(p):
    import csv
    import io
    t = _text(p)
    return list(csv.DictReader(io.StringIO(t))) if t else []


def _iso(s):
    try:
        return dt.datetime.fromisoformat(str(s))
    except (TypeError, ValueError):
        return None


def when(t):
    """Wed 11 Nov, 17:11"""
    return f"{t:%a} {t.day} {t:%b}, {t:%H:%M}" if t else None


def clock(t):
    """17:11, as the progress rail gives a step's time"""
    return f"{t:%H:%M}" if t else None


def ago(now, t):
    """An age with its unit spelled out: "12 seconds ago", "4 days ago"."""
    secs = max(int((now - t).total_seconds()), 0)
    mins = secs // 60
    n, unit = ((secs, "second") if mins < 1 else (mins, "minute") if mins < 60 else
               (mins // 60, "hour") if mins < 48 * 60 else (mins // (24 * 60), "day"))
    return f"{n} {unit}{'' if n == 1 else 's'} ago"


def status_rows(md):
    """[(phase, status, proved by, blocked because)] from RUN.md's Status table, in order."""
    out, inside = [], False
    for line in md.splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Status"
            continue
        if not inside or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("Phase", "") or set(cells[0]) <= set("-: "):
            continue
        cells += [""] * (4 - len(cells))
        out.append((cells[0], cells[1].lower(), cells[2], cells[3]))
    return out


def is_decision(name):
    return not name[:1].isdigit()


def _decided(name, scope, table):
    low = name.lower()
    for key, path in table:
        if (key in low) if " " in key else (key in low.split()):
            v = scope
            for k in path:
                v = v.get(k) if isinstance(v, dict) else None
            return v
    return None


def decision_time(name, scope):
    return _iso(_decided(name, scope, DECISION_TIMES))


def activity(name):
    """The kit's activity number for a row of RUN.md's Status table, or None."""
    for lead, act in (brief.ROWS if brief else ()):
        if name.startswith(lead):
            return act
    return None


def label(name):
    """The step as the person reads it: the kit's own name for it, else the record's without its phase number."""
    act = activity(name)
    if act is not None:
        s = brief.short(act)
        return s[:1].upper() + s[1:]
    return re.sub(r"^\d+[a-z]?\s+", "", name) or name


def _plural(n, nouns):
    return f"{n} {nouns[0] if n == 1 else nouns[1]}"


def tallies(reg, scope):
    """{table file: how many things it holds for the flow being worked}: stages, steps and services of that flow
    only, where the record names it."""
    fid = (scope or {}).get("flow_id")
    stages = [s for s in _csv(reg / "stages.csv") if not fid or s.get("flow") == fid]
    sids = {s.get("stage") for s in stages}
    steps = [s for s in _csv(reg / "steps.csv") if s.get("stage") in sids]
    step_ids = {s.get("step") for s in steps}
    apps = {r.get("subject_id") for r in _csv(reg / "subjects.csv")
            if r.get("kind") == "element" and r.get("band") == "application" and r.get("level") == "component"}
    used = {p.get("subject_id") for p in _csv(reg / "participation.csv") if p.get("step") in step_ids}
    measures = [m for m in _csv(reg / "measures.csv")
                if not fid or m.get("flow") == fid or m.get("stage") in sids or m.get("step") in step_ids]
    return {"flows.csv": len(_csv(reg / "flows.csv")), "stages.csv": len(stages), "steps.csv": len(steps),
            "subjects.csv": len(apps & used) if used else len(apps), "measures.csv": len(measures),
            "alerts.csv": len(_csv(reg / "alerts.csv")), "failure-modes.csv": len(_csv(reg / "failure-modes.csv"))}


def first_look(reg):
    """What the first look over the system found (orientation.json), told as counts, or None."""
    o = _json(reg / "orientation.json") or {}
    bits = [_plural(len(o[k]), n) for k, n in (("flows", ("flow", "flows")), ("services", ("service", "services")))
            if isinstance(o.get(k), list) and o[k]]
    return ", ".join(bits) if bits else None


def produced(reg, cell):
    seen, out = set(), []
    for f in FILE_RE.findall(cell or ""):
        if f in seen or not (reg / f).is_file():
            continue
        seen.add(f)
        out.append((f, f.endswith(".html")))
    return out


def workspace(reg):
    m = re.search(r"\*\*Register:\*\*\s*`([^`]+)`", _text(reg / "resume.md"))
    path = m.group(1) if m else str(reg)
    parts = re.split(r"[\\/]", path)
    if "bfo-work" in parts:
        sep = "\\" if "\\" in path else "/"
        return sep.join(parts[:parts.index("bfo-work")])
    return path


def started_at(reg):
    """When this run started, from its own records only: its run's start folder naming it, else the work folder's
    window-wide record (an earlier release's) while that one is this register's (agents_now.window_record_is), so a
    run never shows another run's start."""
    import agents_now
    reg = pathlib.Path(reg)
    for p in (reg / "_run-state" / "run-started.json", reg / "run-started.json"):
        t = _iso((_json(p) or {}).get("started"))
        if t:
            return t
    mine = (str(reg), str(reg.resolve()))
    for p in sorted(reg.parent.glob("_start-*/run-started.json")):
        d = _json(p) or {}
        if str(d.get("register") or "") in mine and _iso(d.get("started")):
            return _iso(d.get("started"))
    d = _json(reg.parent / "run-started.json") or {}
    return _iso(d.get("started")) if agents_now.window_record_is(reg, d) else None


def last_work(reg):
    """The last real work on the case: the newest entry of the case log, which only the run's own steps write (a page
    redraw or a touch of the lock never lands there)."""
    try:
        import case
        ats = [_iso(e.get("at")) for e in case.log_entries(reg) if e.get("by") != "listener"]
    except (ImportError, OSError, ValueError):
        return None
    ats = [t for t in ats if t and t.tzinfo]
    return max(ats, key=lambda t: t.timestamp()) if ats else None


def stamp(t, at="weekday"):
    """A moment as <time>, carried in UTC for the page's script to show in the browser's own zone with the zone
    named; without script it reads in UTC, "UTC" shown. `at`: "weekday" (Sun 15 Nov, 04:56) or "day" (15 Nov, 04:56)."""
    u = t.astimezone(dt.timezone.utc)
    text = (when(u) if at == "weekday" else f"{u.day} {u:%b}, {u:%H:%M}") + " UTC"
    return f'<time datetime="{u:%Y-%m-%dT%H:%M:%SZ}" data-at="{at}">{E(text)}</time>'


def newest_write(reg):
    """The newest file the run's own steps write as they work (first-look records, the survey, each unit's files,
    the checks' verdicts), as UTC, or None. Never the lock, a page or a redraw."""
    reg = pathlib.Path(reg)
    pats = ("first-look/*.json", "survey.csv", "units/*/files.csv", "judging/*/r*-j*.csv", "fast/mappers/*/*.csv")
    newest = None
    for pat in pats:
        for p in reg.glob(pat):
            try:
                t = p.stat().st_mtime
            except OSError:
                continue
            newest = t if newest is None or t > newest else newest
    return dt.datetime.fromtimestamp(newest, dt.timezone.utc) if newest else None


def last_write(reg):
    lock = _json(reg / "RUN.lock") or {}
    try:
        return dt.datetime.fromtimestamp(float(lock["touched"]), dt.timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None


def capability(reg, depth):
    name = (depth or {}).get("capability")
    if name:
        return name
    rows = _csv(reg / "capabilities.csv")
    return (rows[0].get("name") if rows else None) or reg.name


def job_counts(reg):
    rows = _csv(reg / "job" / "jobs.csv")
    if not rows:
        return None
    n = lambda s: sum(1 for r in rows if r.get("state") == s)  # noqa: E731
    return {"running": n("running"), "done": n(DONE), "blocked": n(BLOCKED), "all": len(rows)}


# The run's path as the operator view draws it: twelve numbered steps, the person's four
# decisions among them, each fed by the RUN.md rows (by their opening words) that carry it out.
STEPS = (("Discovery", False, ("0 ",)), ("Choose the flow", True, ("The go",)),
         ("Process mapping", False, ("1 ", "2 ", "3 ")), ("Choose the depth", True, ("Pick of how far",)),
         ("Define measures", False, ("4 ",)), ("Review the measures", True, ("Review of the measures",)),
         ("Design alerts", False, ("5 ", "5a ")), ("Review the alerts", True, ("Review of the alerts",)),
         ("Write runbooks", False, ("5b ",)), ("Verify against the code", False, ("6 ",)),
         ("Report", False, ("7 ",)), ("Next flow", False, ()))
# The decision each step asks for, as "Next needed at step N, ..." says it.
ASKS = {2: "choose the flow", 4: "choose the depth", 6: "review the draft measures", 8: "review the draft alerts",
        12: "choose the next flow"}
DEPTH_WORDS = {"none": "map only", "measure": "to measures", "alerting": "to alerts", "runbooks": "to runbooks"}
NEXT_TASK = "Choose the next flow to map"  # depth.py's open choice once a flow is finished (go.NEXT_TASK)


def recommended_next(reg, depth, left):
    """The flow recommended next, while it is still to map: the one Home's next-flow choice marks, else the session's
    recommendation at that stop (brief.py next), else None."""
    choice = depth.get("open_choice") or {}
    got = next((i.get("key") for i in choice.get("items") or [] if i.get("recommended")), None) \
        if choice.get("task") == NEXT_TASK else None
    if not got and brief:
        try:
            got = (brief.next_flow_recommended(reg) or {}).get("flow")
        except Exception:  # noqa: BLE001 - a record brief cannot read: no recommendation is shown
            got = None
    return got if got in left else None


def _merge(states):
    """One step's state from the states of the rows that carry it out."""
    states = [s for s in states if s]
    if not states:
        return "to do"
    if BLOCKED in states:
        return BLOCKED
    if all(s == NOT_PICKED for s in states):
        return NOT_PICKED
    if all(s in (DONE, NOT_PICKED) for s in states):
        return DONE
    if DOING in states or DONE in states:
        return DOING
    return "to do"


def depth_said(scope, reg):
    """"All 5 stages to measures · changed from map only", from the pick recorded and the run's recommendation."""
    picked = {k: v for k, v in ((scope or {}).get("depth") or {}).items() if v in DEPTH_WORDS}
    if not picked:
        return None

    def told(d):
        kinds = {}
        for v in d.values():
            kinds[DEPTH_WORDS[v]] = kinds.get(DEPTH_WORDS[v], 0) + 1
        if len(kinds) == 1:
            w, n = next(iter(kinds.items()))
            return f"All {n} stages {w}" if n > 1 else f"1 stage {w}"
        return ", ".join(f"{n} {'stage' if n == 1 else 'stages'} {w}" for w, n in kinds.items())
    said = told(picked)
    rec = {k: (v or {}).get("depth") for k, v in (_json(reg / "depth-recommendation.json") or {}).items()
           if isinstance(v, dict) and (v or {}).get("depth") in DEPTH_WORDS}
    if rec and {k: rec.get(k) for k in picked} != picked and set(rec) >= set(picked):
        was = told({k: rec[k] for k in picked})
        said += " · changed from " + (was.split(" ", 3)[-1] if was.startswith("All ") else was)
    return said


try:  # the split run's own names for its files: the verdicts and round records the progress reading counts
    import judges
except ImportError:  # pragma: no cover - the kit always ships it
    judges = None
# While process mapping runs, how far it is, in the person's words: the latest of these the record supports.
PROGRESS_FORMS = {"reading": "Reading the services · {n} of {of} read",
                  "reread": "Re-reading calls that did not match · {left} left",
                  "checking": "Checking the findings · round {rnd} · {n} of {of} judged",
                  "fixing": "Fixing flagged findings · {n} of {of} changed"}


def _since(p, t0):
    """The file is there and was written at or after `t0` (this flow's go), or `t0` is unknown."""
    try:
        return p.is_file() and (t0 is None or p.stat().st_mtime >= t0)
    except OSError:
        return False


def _checking(reg, t0):
    """The checking line, or the fixing line once its round is in and flagged rows are being fixed, or None: the latest
    round with a record written since the go, its rows judged when every check's verdict is in at the row as recorded."""
    folder = reg / "judging"
    if judges is None or not folder.is_dir():
        return None
    try:
        got = judges.settings(reg)
        n, last = int(got["judges"]), int(got["judge_rounds"])
    except Exception:  # noqa: BLE001 - a settings file mid-write: say nothing this time
        return None
    records = {}
    for d in folder.iterdir():
        for p in d.glob("r*-rows.csv") if d.is_dir() else ():
            m = re.match(r"r(\d+)-rows\.csv$", p.name)
            if m and _since(p, t0):
                records.setdefault(int(m.group(1)), []).append((d.name, p))
    if not records:
        return None
    rnd = max(records)
    judged, total, flagged = 0, 0, []
    for unit, p in records[rnd]:
        for r in _csv(p):
            total += 1
            paths = [folder / unit / judges.verdict_name(rnd, j, r.get("table", ""), r.get("row", ""), r.get("hash", ""))
                     for j in range(1, n + 1)]
            if all(_since(q, t0) for q in paths):
                judged += 1
                if any((judges.read_verdict(q) or {}).get("verdict") != "says" for q in paths):
                    flagged.append((unit, r.get("table"), r.get("row"), r.get("hash")))
    if not total:
        return None
    if judged == total and flagged and rnd < last:
        now = {}
        for unit in {f[0] for f in flagged}:
            now.update({(unit, x["table"], x["key"]): x["hash"] for x in judges.all_rows(reg, unit)})
        changed = sum(1 for u, t, k, h in flagged if now.get((u, t, k)) != h)
        return PROGRESS_FORMS["fixing"].format(n=changed, of=len(flagged))
    return PROGRESS_FORMS["checking"].format(rnd=rnd, n=judged, of=total)


def mapping_progress(reg, scope):
    """How far process mapping is, read from what the run writes as it maps, or "" where the record cannot say:
    the services read, the calls between them that did not match, the findings checked, the flagged ones fixed."""
    t0 = _iso(scope.get("given"))
    t0 = t0.timestamp() if t0 else None
    try:
        line = _checking(reg, t0)
        if line:
            return line
        if _since(reg / "merge" / "unmatched-calls.csv", t0):
            left = len(_csv(reg / "merge" / "unmatched-calls.csv"))
            if left:
                return PROGRESS_FORMS["reread"].format(left=left)
        wanted = {s.lower() for s in scope.get("services_in") or []}
        parts = {}
        for u in _csv(reg / "units" / "units.csv"):
            d = (u.get("deployable") or "").strip()
            if u.get("unit") != "flow" and d.lower() in wanted:
                parts.setdefault(d, []).append(u["unit"])
        launched = any(_since(reg / "prompts" / u / "read.md", t0) for us in parts.values() for u in us)
        if parts and launched:
            read_ = sum(1 for us in parts.values() if all(_since(reg / "units" / u / "files.csv", t0) for u in us))
            return PROGRESS_FORMS["reading"].format(n=read_, of=len(parts))
    except OSError:
        pass
    return ""


REQUEST_RE = re.compile(r'^- \*\*Request:\*\* "(.*)" \(the person, [^)]*\)\s*$', re.M)


def chosen_by_run(reg, scope):
    """Why the run chose the flow itself, or None when the person chose it: the go was recorded from their request,
    word for word, and the request names no flow, so the flow is the first look's recommendation. go.py records no
    flag for this; the page reads it from the request RUN.md keeps and the go's words."""
    m = REQUEST_RE.search(_text(reg / "RUN.md"))
    request, flow = (m.group(1).strip() if m else ""), (scope.get("flow") or "").strip()
    if not request or not flow or (scope.get("words") or "").strip() != request or flow.lower() in request.lower():
        return None
    why = ((_json(reg / "orientation.json") or {}).get("recommendation") or {}).get("why") or ""
    return "as your request named no flow" + (f": {why.strip()}" if why.strip() else "")


# Before the run has a folder, the start step's page: the first look under way, as step 1 of the twelve.
STARTING_ROW = ("0 First look over the system", DOING, "", "")
STARTING_TITLE = "Business flow observability run"


SAY_BACK = "say-back.json"  # say_back.py's: what the run understood, waiting on the person's Start
SAY_BACK_TITLE = "Check what I understood"


# Process mapping's sub-steps as run control keeps them in the case record, said in the person's words.
SUB_WORDS = {"lead steps": "Following one case from start to end", "units": "Reading the services",
             "readers": "Reading the services", "merge": "Putting what each service does together",
             "re-reads": "Re-reading the calls between services", "lead rows": "Naming what is at stake at each step",
             "judge round 1": "Checking every finding against the code", "fixers": "Correcting the findings flagged",
             "judge round 2": "Checking the corrected findings against the code",
             "check": "Checking the map is complete", "mapping ends": "Finishing the map"}
CASE_ROWS = (("1 ", "CASE"), ("2 ", "STRUCTURE"), ("3 ", "CAPABILITY"))


def mapping_from_case(reg, rows):
    """The run record's rows with mapping's three read from the case record, which run control keeps in their place
    (brief._mapping_from_case, the status line's reading); unchanged where the case holds no flow worked now."""
    if not brief:
        return rows
    acts = {lead: getattr(brief, name) for lead, name in CASE_ROWS}
    lead_of = lambda name: next((lead for lead in acts if name.startswith(lead)), None)  # noqa: E731
    now = dict(brief._mapping_from_case(reg, [(acts[lead_of(r[0])], r[1]) for r in rows if lead_of(r[0])]))
    return [(r[0], now.get(acts[lead_of(r[0])], r[1]), r[2], r[3]) if lead_of(r[0]) else r for r in rows]


def said_back(reg):
    """The say-back waiting on the person in this folder, or None."""
    sb = _json(pathlib.Path(reg) / SAY_BACK)
    return sb if isinstance(sb, dict) and sb.get("state") == "waiting" and sb.get("lines") else None


def s_no(steps, n):
    """The number step `n` is shown with: its place, where a fast map puts the pick before the map."""
    return next((s.get("shown", n) for s in steps if s["numbers"] == [n]), n) if n is not None else None


def step_clock(reg, scope, steps, now, starting):
    """A time on every step (step_times): a work step's span, or how long it has run so far; a decision's answer time
    with how long the run waited on the person; "time not recorded" where the run recorded none. Never raises."""
    try:
        import step_times as stt
        flow = scope.get("flow_id") or None
        raw = status_rows(_text(reg / "RUN.md")) if not starting and (reg / "RUN.md").is_file() else []
        changes = stt.seen_changes(reg, raw, flow, now) if raw else {}
        spans, pick_at = stt.mapping_spans(reg, flow)
        plan = stt._mtime(reg / "PLAN.md")
        floor = None  # the latest end of the steps above, in the page's order: no work step starts before it

        def later(t):
            nonlocal floor
            if t is not None and (floor is None or t.timestamp() > floor.timestamp()):
                floor = t
        for s in steps:
            n, st = s["numbers"][0], s["state"]
            if st not in (DONE, DOING) or s.get("say_back"):
                continue
            leads = next((ls for t, _, ls in STEPS if t == s["title"]), ())
            leads = [r[0] for r in raw if any(r[0].startswith(x) for x in leads)]
            if s["decision"]:
                answered = decision_time(s["rows"][0], scope) if s["rows"] else None
                asked = plan if n == 2 else pick_at if n == 4 else stt.row_span(changes, leads)[0]
                if s["time"] and answered and asked and answered >= asked:
                    s["time"] += f" · answered after {stt._mins(asked, answered)} min"
                later(answered)
                continue
            if n == 1:
                begun = stt.start_answer(reg)
                if not begun and started_at(reg):  # said under the title, so the time column stays short
                    s["note"] = "from the start step, includes the wait at the say-back"
                begun = begun or started_at(reg)
                s["time"] = s["time"] or (stt.span_text(begun, plan if st == DONE else None, now) if begun
                                          else "time not recorded")
                later(plan if st == DONE else None)
            elif n == 3 and spans:
                text, _, aside = stt.spans_text(spans, now).partition(" (")
                s["time"] = s["time"] or text
                if aside:  # "2 spans, the wait at the pick left out": under the title, not in the time column
                    s["note"] = aside.rstrip(")")
                later(spans[-1][1])
            else:
                a, b, about = stt.row_span(changes, leads)
                if a and floor and floor.timestamp() > a.timestamp():  # its row moved early (a fast map runs after
                    a = floor  # the pick): the step began when the work it waits on was done
                s["time"] = s["time"] or (stt.span_text(a, b if st == DONE else None, now, about) if a or b
                                          else "time not recorded")
                later(b if st == DONE else None)
    except Exception:  # noqa: BLE001  (a time is never worth losing the page for)
        pass


def read(reg, now=None, starting=False, transcripts=None):
    """The operator view's content, read from the register folder: no file is written. `starting`: the work folder
    before any run folder is in it, drawn as a run whose first look is under way, or, while the say-back waits on the
    person, not yet begun."""
    reg = pathlib.Path(reg)
    now = now or dt.datetime.now(dt.timezone.utc).astimezone()
    scope = _json(reg / "scope.json") or {}
    opened = open_record(reg)
    depth = _json(reg / "depth.json") or {}
    sb = said_back(reg)
    # a register opened to carry on: its say-back is not a step of a run, and no run is under way until it is answered
    carrying_on = bool(sb) and sb.get("kind") == "resume"
    sb = None if carrying_on else sb
    rows = ([(STARTING_ROW[0], "to do", "", "")] if sb else [STARTING_ROW]) if starting \
        else mapping_from_case(reg, status_rows(_text(reg / "RUN.md")))
    case_now = None if starting or not brief else brief.case_flow(reg)
    counts = tallies(reg, scope)
    reported = _iso(scope.get("report_sent"))
    left = list((scope.get("remains") or {}).get("flows") or [])
    rr = _csv(reg / "re-read.csv")
    off = [r for r in rr if (r.get("verdict") or "").strip().lower() != "says"]
    local = lambda t: t.astimezone(now.tzinfo) if t and t.tzinfo else t  # noqa: E731
    steps = []
    for n, (title, decision, leads) in enumerate(STEPS, 1):
        mine = [r for r in rows if any(r[0].startswith(lead) for lead in leads)]
        state = _merge([r[1] for r in mine]) if leads else ("to do" if left else NOT_PICKED)
        s = {"numbers": [n], "title": title, "decision": decision, "state": state, "time": None, "said": "",
             "link": None, "bad": False, "why": "; ".join(r[3] for r in mine if r[1] == BLOCKED and r[3]),
             "rows": [r[0] for r in mine], "by_run": False}
        done = state == DONE
        if n == 1 and done:
            s["said"], s["link"] = first_look(reg) or "", "index.html" if (reg / "index.html").is_file() else None
        elif decision and done:
            s["time"] = clock(local(decision_time(mine[0][0], scope))) if mine else None
            s["said"] = {2: scope.get("flow") or "", 4: depth_said(scope, reg) or ""}.get(n, "Reviewed")
            still = open_at_review(opened, n)
            if still:  # a go on a draft its own check fails: reviewed, never as if it passed
                s["said"] = f"Reviewed, with {_plural(len(still), ('open item', 'open items'))}"
            why = chosen_by_run(reg, scope) if n == 2 and not starting else None
            if why:  # the run took this decision itself: never shown as the person's
                s["said"], s["by_run"] = f"{s['said']} · chosen by the run, {why}", True
        elif n == 3 and (reg / "fast-map.html").is_file():  # the fast map (go.py --fast): drawn, labelled, unread
            import fast_map
            s["said"], s["link"] = "Fast map: " + fast_map.summary(reg, None), fast_map.PAGE
        elif n == 3 and state == DOING and not starting:
            s["said"] = mapping_progress(reg, scope) or SUB_WORDS.get((case_now or {}).get("sub") or "", "")
        elif n == 3 and done:
            bits = [_plural(counts[f], NOUNS[f]) for f in ("stages.csv", "subjects.csv") if counts.get(f)]
            s["said"] = "Map: " + ", ".join(bits) if bits else "Map"
            if (case_now or {}).get("state") == brief.CASE_ENDED:
                s["said"] += " · not checked: you stopped the checks"
            s["link"] = "views.html" if (reg / "views.html").is_file() else None
        elif n == 5 and done and counts.get("measures.csv"):
            s["said"] = _plural(counts["measures.csv"], NOUNS["measures.csv"]) + " proposed"
        elif n == 7 and done and counts.get("alerts.csv"):
            s["said"] = _plural(counts["alerts.csv"], NOUNS["alerts.csv"]) + " proposed"
        elif n == 9 and done and counts.get("failure-modes.csv"):
            s["said"] = _plural(counts["failure-modes.csv"], NOUNS["failure-modes.csv"]) + " written up"
        elif n == 10 and rr and state != "to do":
            s["said"] = f"{len(off)} of {len(rr)} failed" if off else f"{len(rr)} of {len(rr)} passed"
            s["bad"] = bool(off)
        elif n == 11 and reported:  # the report is out: the step is done, whatever the row still says
            s["state"], s["said"], s["time"] = DONE, "Sent", clock(local(reported))
        elif n == 12 and left:
            s["said"] = f"{len(left)} {'flow' if len(left) == 1 else 'flows'} not mapped"
            rec = recommended_next(reg, depth, left)
            s["said"] += f" · recommended next: {rec}" if rec else ""
        steps.append(s)
    if scope.get("mapping") == "fast":  # a fast map is drawn after the pick: the pick, then the map, numbered so
        k3, k4 = (next(k for k, s in enumerate(steps) if s["numbers"] == [n]) for n in (3, 4))
        steps[k3], steps[k4] = steps[k4], steps[k3]
        steps[k3]["shown"], steps[k4]["shown"] = 3, 4
    if sb:  # nothing is read before the person's Start: the say-back is the step now, before the run's own
        steps = [s for s in steps if s["numbers"] != [12]]  # no "next flow" before any flow is begun
        steps.insert(0,{"numbers": [0], "title": SAY_BACK_TITLE, "decision": True, "state": "to do", "time": None,
                         "said": "", "link": None, "bad": False, "why": "", "rows": [], "by_run": False,
                         "say_back": True})
    if not sb:
        step_clock(reg, scope, steps, now, starting)
    current = next((k for k, s in enumerate(steps) if s["state"] not in (DONE, NOT_PICKED)), None)
    for k, s in enumerate(steps):
        s["current"] = k == current
    cur = steps[current] if current is not None else None
    if cur is not None and cur["state"] == DOING and not starting:  # the step under way opens to its parts
        import step_parts
        got = step_parts.of(reg, cur["numbers"][0], scope, now)
        if got:  # a line the step already says from the run's record (the checking or fixing round) is kept
            cur["parts"] = got
            if not cur["said"] or cur["numbers"][0] != 3:
                cur["said"], cur["link"] = got["summary"], None
    last = last_write(reg)
    # Last activity: a real write of the run (its answers, its report, the case log, the first look's records, the
    # survey, a unit's files), never the lock, which a check or a page redraw touches; the panel's newest sign wins
    # below whenever the agents' records can be read
    times = [t for t in [reported, last_work(reg), newest_write(reg)]
             + [decision_time(r[0], scope) for r in rows if is_decision(r[0])] if t]
    last_any = max(times, key=lambda t: t.timestamp()) if times else None
    age_min = (now.timestamp() - last.timestamp()) / 60 if last else None
    try:  # agents launched and not finished are the run at work, though the lead writes nothing meanwhile
        import case
        working = case.at_work(reg, now.astimezone(dt.timezone.utc))
    except (ImportError, OSError, ValueError):
        working = []
    # who is working, from the agents' own transcripts: the badge, the "at work" words and the panel read this alone
    import agents_now
    seen = agents_now.gather(reg, now, transcripts)
    seen_badge = agents_now.badge(seen)
    if seen.get("count"):  # the first look's parts read, of its parts: the one count, on the row as on the panel
        for s in steps:
            if s["numbers"] == [1] and s["state"] == DOING:  # the panel's count, said on the row too
                s["said"] = (s["said"] + " · " if s.get("parts") else "") + seen["count"] + " read"
    blocked = [s for s in steps if s["state"] == BLOCKED]
    choice = depth.get("open_choice") or None
    # the next flow is an open case's next step, offered with the recommendation, never a wait on the person (an
    # unfinished case is not activity in motion); a review is a real stop on the person's word
    next_open = (choice or {}).get("task") == NEXT_TASK or bool(cur and cur["numbers"] == [12])
    choice = None if (choice or {}).get("task") == NEXT_TASK else choice
    # every step done and no flow left: the run has ended, so its quiet agents are finished. The next flow offered is
    # not an end (the lead may be starting it): there every agent shows as it is
    if not starting and cur is None:
        seen = agents_now.as_ended(seen)
        seen_badge = agents_now.badge(seen)
    signs = [r["last"] for r in ([seen.get("lead")] + list(seen.get("agents") or [])) if r and r.get("last")]
    if seen.get("readable") and signs:  # the newest sign the panel shows, with the run's answers and report: never a
        # lock touched by the page or a redraw
        events = signs + [t for t in [reported] + [decision_time(r[0], scope) for r in rows if is_decision(r[0])] if t]
        last_any = max(events, key=lambda t: t.timestamp())
    if blocked:
        status = "blocked"
    elif choice:  # the record says the run waits on the person's choice, whichever row is current
        status = "waiting"
    elif cur is None:
        status = "finished"
    elif cur["decision"]:  # a pick or review row is doing from the stop's message on: the run waits on the person
        status = "waiting"
    elif seen_badge == "quiet":  # the agents' own records: nothing at work, nothing stopped for good
        status = "quiet" if age_min is None or age_min <= STALE_MINUTES else "paused"
    elif seen_badge is not None:
        status = seen_badge
    elif (age_min is not None and age_min <= RUNNING_MINUTES) or working:  # records unreadable: the run's own files
        status = "running"
    elif age_min is not None and age_min <= STALE_MINUTES:
        status = "quiet"
    else:
        status = "paused"
    if next_open and status == "paused":
        status = IDLE  # nothing in motion and nothing waits on the person: no Required action, and no badge
    if sb:
        status = "waiting"
    elif starting:
        status = seen_badge if seen_badge not in (None, "quiet") else "running"
    elif carrying_on and status in ("running", "quiet", "paused", "finished"):
        status = IDLE  # nothing waits on the person: no Required action, and no badge
    nxt = next((s["numbers"][0] for s in steps[(current or 0) + (1 if cur and not cur["decision"] else 0):]
                if s["numbers"][0] in ASKS and s["state"] == "to do"), None)
    resume = {"folder": workspace(reg), "phrase": f"continue the run on {capability(reg, depth)}"}
    if sb:
        action = {"kind": "say_back", "lines": sb["lines"], "fingerprint": sb.get("fingerprint") or "",
                  "search": sb.get("search")}
    elif status == "waiting":
        at = cur["numbers"][0] if cur else 12
        # a stop on a pick or review is said in the status line's own words for it, so the two never disagree
        held = brief.WAITS.get(activity(cur["rows"][0])) if brief and cur and cur["decision"] and cur["rows"] else None
        what = held or (choice or {}).get("task") or ASKS.get(at) or cur["title"]
        action = {"kind": "decide", "step": s_no(steps, at), "what": what[:1].lower() + what[1:],
                  "on_page": (choice or {}).get("milestone") in ON_PAGE if choice else False,
                  "resume": resume if age_min is None or age_min > STALE_MINUTES else None}
    elif status in ("paused", "blocked"):
        action = dict(resume, kind="resume")
    else:
        action = {"kind": "none", "next": s_no(steps, nxt), "ask": ASKS.get(nxt)}
    if cur is not None and status == "paused" and cur["state"] == "to do":
        cur["said"] = cur["said"] or "On resume"
    jobs = job_counts(reg) if status in ("running", "quiet") else None
    if cur is not None and cur["state"] == DOING and jobs:
        cur["said"] = f'{jobs["done"]} of {jobs["all"]} done' + (f' · {jobs["blocked"]} blocked' if jobs["blocked"] else "")
    issues = []
    for s in blocked:
        issues.append({"what": f"Step {s_no(steps, s['numbers'][0])}, {s['title']}, is blocked: "
                               f"{s['why'] or 'the record gives no reason'}",
                       "clears": "Fixing what the reason names, then resuming the run", "bad": True})
    if off:
        issues.append({"what": f"Map not verified: {len(off)} of {len(rr)} statements failed the code check",
                       "clears": "Step 10, when the run resumes", "bad": True})
    if opened.get("unreadable"):
        issues.append({"what": "The draft's open items could not be checked: the stage checks cannot read the register",
                       "clears": "Running the stage checks again once the register reads", "bad": True})
    for n, what in ((6, "measures"), (8, "alerts")):
        still = open_at_review(opened, n)
        if still:
            how = "left open at your word" if opened["left_open"] else "recorded with your go"
            issues.append({"what": f"The draft {what} have {_plural(len(still), ('open item', 'open items'))}, {how}: "
                                   + "; ".join(still[:5]) + (f"; and {len(still) - 5} more" if len(still) > 5 else ""),
                           "clears": "The run puts each right, then the stage is checked again", "bad": False})
    if any(r[0].startswith("7 ") and r[1] == DOING for r in rows) and not reported and \
            (_json(reg / "done-check.json") or {}).get("done") is False:
        issues.append({"what": "The final check says the run is not done yet",
                       "clears": "Step 11, the final check passing on the map as it is", "bad": False})
    t0 = started_at(reg)
    m = {"title": STARTING_TITLE if starting else capability(reg, depth), "flow": scope.get("flow"), "started": when(t0),
            "started_at": t0 if t0 and t0.tzinfo else None, "last_at": last_any,
            "last_work": last_work(reg),
            "last": when(local(last_any)) if last_any else None,
            "last_ago": ago(now, last_any) if last_any else None, "recent": bool(last_any) and
            (now.timestamp() - last_any.timestamp()) < 3600,
            "status": status, "steps": steps, "current": current, "action": action, "issues": issues,
            # the same source as Last activity and the panel's rows: the newest sign, else the lock's touch
            "left": left, "quiet_min": (int((now.timestamp() - last_any.timestamp()) // 60) if last_any
                                        else int(age_min) if age_min is not None else None)
            if status == "quiet" else None,
            "at_work": sorted({case.AT_WORK.get(r["kind"], "agents are at work") for r in working}) if working else [],
            "agents": seen,
            "map_so_far": (map_so_far(reg, scope) if not starting and any(
                s["numbers"] == [3] and s["state"] == DOING for s in steps) else None)}
    import run_state  # the run's one state: the badge, the parts, the title, the banner, the notice, the watchdog
    m["run"] = run_state.of(m, reg)
    m["in_motion"] = bool(starting or m["run"]["state"] in run_state.IN_MOTION)
    if cur is not None and cur.get("parts"):  # a stopped run's parts never say they are being read
        import step_parts
        was = cur["parts"]["summary"]
        cur["parts"] = step_parts.settled(cur["parts"], m["run"]["state"])
        cur["said"] = (cur["said"] or "").replace(was, cur["parts"]["summary"], 1)
    return m


# The badge, by the run's one state (run_state.of); the page's own status only marks the first look still starting
RUN_BADGE = {"working": ("b-run", "i-run", "Running"), "quiet": ("b-you", "i-pause", "Quiet · no recent write"),
             "waiting": ("b-you", "i-you", "Waiting on you"), "stopped": ("b-bad", "i-bad", "Stopped · needs you"),
             "finished": ("b-ok", "i-ok", "Finished")}


ICON = {DONE: "i-ok", "decided": "i-youdone", DOING: "i-run", BLOCKED: "i-bad", NOT_PICKED: "i-skip",
        "to do": "i-todo", "next": "i-next", "you": "i-you"}
BADGE = {"running": ("b-run", "i-run", "Running"), "quiet": ("b-off", "i-info", "Quiet · no recent write"),
         "paused": ("b-you", "i-pause", "Paused · action required"), "waiting": ("b-you", "i-you", "Waiting on you"),
         "blocked": ("b-bad", "i-bad", "Blocked"), "finished": ("b-ok", "i-ok", "Finished"),
         "stopped": ("b-bad", "i-bad", "Stopped: no agent working"), "starting": ("b-off", "i-info", "Starting")}


def step_html(s, status, waiting):
    ns = s["numbers"]
    num = f"{ns[0]}–{ns[-1]}" if len(ns) > 1 else str(s.get("shown", ns[0]))
    if s.get("say_back"):
        return (f'<li class="step cur"><svg class="ic"><use href="#i-you"/></svg><span class="n">{E(s["title"])}'
                '<span class="dec">decision</span></span><span class="d">Waiting on you · nothing in the code is '
                'read before Start</span><span class="t"></span></li>')
    title = f'<span class="n" title="{E("; ".join(s["rows"]))}">' if s["rows"] else '<span class="n">'
    if s["state"] == NOT_PICKED:
        return (f'<li class="step off"><svg class="ic"><use href="#i-skip"/></svg>{title}{num}. {E(s["title"])}'
                f'</span><span class="d">{"Not picked" if ns[0] != 12 else "None left"}</span>'
                f'<span class="t"></span></li>')
    st = s["state"]
    ic = ICON.get(st, "i-todo")
    if st == DONE and s["decision"] and not s.get("by_run"):
        ic = ICON["decided"]
    if s["bad"]:
        ic = ICON[BLOCKED]
    if s["current"] and st == "to do":
        ic = ICON["you"] if (s["decision"] or waiting) else ICON["next"]
    if s["current"] and st == DOING and waiting:
        ic = ICON["you"]
    cls = "step" + ((" curbad" if st == BLOCKED or s["bad"] else " cur") if s["current"] else "")
    cls += " off" if st == "to do" and not s["current"] else ""
    tag = ' <span class="dec">decision</span>' if s["decision"] else ""
    said = E(s["said"])
    if s["said"] and s["link"]:
        said = f'<a href="{E(s["link"])}">{said}</a>'
    elif not s["said"] and s["link"]:
        said = f'<a href="{E(s["link"])}">Open</a>'
    time = s["time"] or ""
    # a time too long for the narrow column goes first on the line under the title, which keeps its width
    desc = ([E(time)] if len(time) > TIME_COLUMN else []) + ([said] if said else [])
    time = "" if len(time) > TIME_COLUMN else time
    if s.get("note"):
        desc.append(E(s["note"]))
    if st == BLOCKED and s["why"]:
        desc.append(E(s["why"]))
    if s["current"] and waiting:
        desc.append("Waiting on you")
    spin = " spin" if st == DOING and status == "running" and not waiting else ""
    d = f'<span class="d">{" · ".join(desc)}</span>' if desc else ""
    if s.get("parts"):  # the step under way, opened to its parts (step_parts.py)
        import step_parts
        d += step_parts.html_list(s["parts"], E)
    return (f'<li class="{cls}"><svg class="ic{spin}"><use href="#{ic}"/></svg>{title}{num}. {E(s["title"])}{tag}'
            f'</span>{d}<span class="t">{E(time)}</span></li>')


TIME_COLUMN = 28  # characters: "since 09:40 · 44 min so far" fits beside a title; "done by 08:09 · start not recorded" does not


def copy_cmd(text, path=False):
    return (f'<span class="cmd{" path" if path else ""}"><code>{E(text)}</code><button class="btn sm" type="button" '
            f'data-copy="{E(text)}">Copy</button></span>')


def resume_html(r):
    return (f'<ol><li>In VS Code, open {copy_cmd(r["folder"], True)}</li>'
            f'<li>In a Claude Code tab there, type {copy_cmd(r["phrase"])}</li></ol>')


def say_back_html(a):
    """The review step: the ask and Start first, then what the run understood, one line each, then one box for a
    correction with its own Send. Start never sends a correction."""
    rows = "".join(f'<tr><th scope="row">{E(x["label"])}</th><td><div class="v">{E(x["value"])}</div></td></tr>'
                   for x in a["lines"])
    if a.get("search"):  # the code is not open: one question about the search, and no Start until it is answered
        head = (f'<div class="sbh"><div><b>{E(a["search"]["question"])}</b>'
                '<span class="note">Nothing is searched or read until you say yes.</span></div>'
                '<span class="sbq"><button class="start" type="submit" name="act" value="search-yes">Yes</button>'
                '<button class="sec" type="submit" name="act" value="search-no">No</button></span></div>')
    else:
        head = ('<div class="sbh"><div><b>Check what I understood, then press Start.</b>'
                '<span class="note">Nothing in the code is read until you press Start.</span></div>'
                '<button class="start" type="submit" name="act" value="start">Start</button></div>')
    body = (f'<form class="sb" data-fp="{E(a["fingerprint"])}">{head}'
            f'<table class="sbt"><tbody>{rows}</tbody></table>'
            '<label class="sbl" for="sbc">Anything wrong? Say which line and what it should be</label>'
            '<textarea class="sbc" id="sbc" name="correction" rows="2" autocomplete="off"></textarea>'
            '<div class="sbb"><button class="sec" type="submit" name="act" value="correct">Send</button>'
            '<span class="note sbw" hidden>Send your correction first, or clear the box.</span></div>'
            '<p class="note sbs" role="status"></p></form>')
    return f'<div class="panel act-you"><div class="panel-h"><h3>Required action</h3></div><div class="act">{body}</div></div>'


def action_html(m):
    a = m["action"]
    if m["status"] == IDLE:
        return ""
    if a["kind"] == "say_back":
        return say_back_html(a)
    if a["kind"] == "decide":
        where = ('Give it on the <a href="index.html">home page</a>.' if a["on_page"]
                 else "Give it in the chat of the run's Claude Code tab.")
        body = f'<b>Needed now at step {a["step"]}, {E(a["what"])}.</b> <span>{where}</span>'
        if a.get("resume"):
            body += '<p class="note">If the run\'s Claude Code tab is closed:</p>' + resume_html(a["resume"])
        return f'<div class="panel act-you"><div class="panel-h"><h3>Required action</h3></div><div class="act">{body}</div></div>'
    if a["kind"] == "resume":
        body = "<b>Resume the run.</b>" + resume_html(a)
        return f'<div class="panel act-you"><div class="panel-h"><h3>Required action</h3></div><div class="act">{body}</div></div>'
    if a.get("next"):
        lead = f'<b>None now.</b> Next needed at step {a["next"]}, {E(a["ask"])}.'
    elif m["status"] == "finished":
        lead = "<b>None now.</b> Every step is done."
    else:
        lead = "<b>None now.</b>"
    if m.get("at_work"):
        said = "; ".join(m["at_work"])
        lead += f' <span class="note">Now: {E(said[:1].upper() + said[1:])}.</span>'
    if m["status"] == "quiet":
        lead += (f' <span class="note">Nothing heard for {m["quiet_min"]} min: check the run\'s Claude Code tab before '
                 'resuming it.</span>')
    return f'<div class="panel"><div class="panel-h"><h3>Required action</h3></div><div class="act">{lead}</div></div>'


NOT_STARTED = "not started"
PEOPLE_KINDS = ("case", "person")


def map_so_far(reg, scope):
    """[(line, what it says)] of the map as it grows, for the flow worked now, read from the register's tables at draw
    time: a table counts only when its file was written since this flow's go; one not reached says "not started"."""
    reg = pathlib.Path(reg)
    t0 = _iso(scope.get("given"))
    t0 = t0.timestamp() if t0 else None
    flow = scope.get("flow_id") or ""

    def rows(name):
        p = reg / name
        return _csv(p) if _since(p, t0) else None

    out = []
    stages = rows("stages.csv")
    mine = [r for r in stages or [] if not flow or (r.get("flow") or "").strip() in ("", flow)]
    mine.sort(key=lambda r: int(r["order"]) if str(r.get("order") or "").isdigit() else 0)
    out.append(("Stages written", f"{len(mine)} · " + " · ".join(r.get("name") or r.get("stage") or "" for r in mine)
                if mine else NOT_STARTED))
    ids = [(r.get("stage") or "").strip() for r in mine]
    steps = rows("steps.csv")
    own = [r for r in steps or [] if (r.get("stage") or "").strip() in ids]
    if steps is None or not own:
        out.append(("Steps written", NOT_STARTED))
    else:
        per = [sum((r.get("stage") or "").strip() == s for r in own) for s in ids]
        out.append(("Steps written", f"{len(own)} of the {len(ids)} stages ({', '.join(map(str, per))})"))
    impact = rows("step-impact.csv")
    if own and impact is not None:
        with_impact = {(r.get("step") or "").strip() for r in impact} & {(r.get("step") or "").strip() for r in own}
        out.append(("Business impact", f"{len(with_impact)} of {len(own)} steps"))
    else:
        out.append(("Business impact", NOT_STARTED))
    merged = _since(reg / "merge" / "summary.json", t0)
    found = {}
    for r in rows("subjects.csv") or []:
        found.setdefault((r.get("subject_id") or "").strip(), r)
    if not merged:
        for p in sorted((reg / "units").glob("*/subjects.csv")):
            if _since(p, t0):
                for r in _csv(p):
                    found.setdefault((r.get("subject_id") or "").strip(), r)
    elements = [r for k, r in found.items() if k and (r.get("kind") or "").strip() == "element"]
    people = [r for r in elements if (r.get("part_kind") or "").strip() in PEOPLE_KINDS]
    parts = [r for r in elements if r not in people]
    if parts:
        kinds = {}
        for r in parts:
            k = (r.get("part_kind") or "").strip() or "kind not given"
            kinds[k] = kinds.get(k, 0) + 1
        out.append(("Parts found", f"{len(parts)} (" + ", ".join(f"{n} {k}" for k, n in
                                                                 sorted(kinds.items(), key=lambda x: -x[1])) + ")"))
    else:
        out.append(("Parts found", NOT_STARTED))
    if people:
        out.append(("The case and the people who act", f"{len(people)}: " + ", ".join(
            r.get("name") or r.get("subject_id") for r in people)))
    return out


def map_so_far_html(m):
    lines = m.get("map_so_far")
    if not lines:
        return ""
    body = "".join(f'<tr><td>{E(k)}</td><td>{E(v)}</td></tr>' for k, v in lines)
    steps = dict(lines).get("Steps written", NOT_STARTED)
    link = ('<p class="note"><a href="map-so-far.html">Open the partial map</a>: drawn from what is written; any row '
            'the check refuses is left out and listed at its top.</p>' if steps != NOT_STARTED else
            '<p class="note">The map is drawn once a stage has steps.</p>')
    return ('<div class="panel"><div class="panel-h"><h3>Map so far</h3><span class="r">read from the run\'s tables '
            f'at each reload; rows may change before the map is checked</span></div><table class="who-now">{body}'
            f'</table>{link}</div>')


STATE_CLASS = {"working": "", "amber": " warn", "red": " bad", "finished": " done", "waiting on its agents": ""}


def working_html(m):
    """Who is working now: one row per agent at work, quiet or stopped, then a tally of the finished; read from the
    same account as the badge (agents_now), so the two never disagree. Never an empty table."""
    g = m.get("agents") or {}
    if not g:
        return ""
    head = '<div class="panel-h"><h3>Who is working now</h3>'
    if not g.get("readable"):
        return f'<div class="panel">{head}</div><div class="act"><span class="note">{E(g.get("reason") or "")}</span></div></div>'
    import agents_now
    rows = [r for r in ([g["lead"]] if g["lead"] else []) + g["agents"]
            if r["state"] not in (agents_now.FINISHED, agents_now.QUEUED)]
    queued = [r for r in g["agents"] if r["state"] == agents_now.QUEUED]
    now = dt.datetime.now(dt.timezone.utc).astimezone()

    def since(t):
        return f'{t.astimezone(now.tzinfo).strftime("%H:%M")}' if t else "-"

    body = "".join(
        f'<tr class="ag{STATE_CLASS.get(r["state"], "")}"><td>{E(r["on"] if r["kind"] != "lead" else "The lead")}'
        f'<span class="who">{E(r["who"]) if r["kind"] != "lead" else ""}</span></td><td>{E(r["now"])}</td>'
        f'<td>{E(r["last_action"] or "-")}</td><td>{since(r["last"])}</td><td>{E(r["words"])}</td></tr>'
        for r in rows)
    tally = (f'<p class="note">Finished: {g["finished"]}.</p>' if g["finished"] else "")
    if queued:  # one line for the launches not yet taken, by what they are on: rows only for work under way
        by = {}
        for r in queued:
            by[r["on"]] = by.get(r["on"], 0) + 1
        what = "checks" if all("judge" in (r["who"] or "") for r in queued) else "agents"
        tally = (f'<p class="note">{len(queued)} {what} queued: '
                 + ", ".join(f"{n} {E(on)}" for on, n in sorted(by.items(), key=lambda x: (-x[1], x[0])))
                 + "</p>" + tally)
    table = ('<table class="who-now"><thead><tr><th>On</th><th>Now</th><th>Last action</th><th>Last sign</th>'
             f'<th>State</th></tr></thead><tbody>{body}</tbody></table>' if rows
             else '<div class="none">No agent at work.</div>')
    r = f'<span class="r">{E(agents_now.words(g))}</span>'
    return f'<div class="panel">{head}{r}</div>{table}{tally}</div>'


def open_record(reg):
    """The flow worked now's record of open items and the person's decisions on them (open_items.of_flow)."""
    import open_items
    try:
        return open_items.of_flow(reg)
    except Exception:  # noqa: BLE001 - the page is drawn whatever the checks can read, and says what they could not
        return open_items.empty(unreadable=True)


def open_at_review(rec, n):
    """The open items now of the concern the person's go on the measures (step 6) or the alerts (step 8) covers,
    from the flow's record: a fix after the go clears them here as everywhere."""
    part = {6: "measures", 8: "alerts"}.get(n)
    return list(rec["concerns"][part]["items"]) if part and rec["concerns"][part]["go"] else []


def issues_html(issues):
    if not issues:
        inner = '<div class="none">None</div>'
    else:
        inner = '<ul class="ann">' + "".join(
            f'<li><svg class="ic"><use href="#{"i-bad" if i["bad"] else "i-warn"}"/></svg><span class="h">'
            f'{E(i["what"])}</span><span class="clr"><b>Clears</b>{E(i["clears"])}</span></li>' for i in issues) + "</ul>"
    return (f'<div class="panel"><div class="panel-h"><h3>Issues</h3><span class="r">most severe first</span></div>'
            f'{inner}</div>')


def render(reg, now=None, starting=False, transcripts=None):
    """The page. `starting`: the work folder before any run folder is in it (read's `starting`)."""
    reg = pathlib.Path(reg)
    m = read(reg, now, starting, transcripts)
    st = m["run"]  # the run's one state (run_state.of): badge, title, banner and notice all read it
    spin = " spin" if st["state"] == "working" else ""
    badge = ""
    shown = (BADGE["starting"] if m["status"] == "starting" else None if m["status"] == IDLE
             else BADGE["paused"] if m["status"] == "paused" and st["state"] == "waiting"  # waits on a resume
             else RUN_BADGE.get(st["state"]))
    if shown:
        cls, ic, word = shown
        badge = f'<span class="badge {cls}"><svg class="ic{spin}"><use href="#{ic}"/></svg>{E(word)}</span>'
    asking = m["action"]["kind"] == "say_back"  # before Start nothing has begun: no empty times are shown
    sub = [] if asking else ['<span>Mapping run</span>']
    if not asking and not m["in_motion"]:  # an unfinished case is not activity in motion
        t = m["last_work"]
        sub = [f'<span>Nothing in motion · last work <b>{stamp(t, "day")}</b></span>' if t
               else '<span>Nothing in motion · last work <b class="nr">not recorded</b></span>']
    elif m["started_at"]:
        sub.append(f'<span>Started <b>{stamp(m["started_at"])}</b></span>')
    elif m["started"]:
        sub.append(f'<span>Started <b>{E(m["started"])}</b></span>')
    elif not asking:
        sub.append('<span>Started <b class="nr">not recorded</b></span>')
    if asking or not m["in_motion"]:
        pass
    elif m["last"] and m["recent"]:
        sub.append(f'<span>Last activity <b>{E(m["last_ago"])}</b></span>')
    elif m["last"]:
        sub.append(f'<span>Last activity <b>{stamp(m["last_at"])}</b> ({E(m["last_ago"])})</span>')
    else:
        sub.append('<span>Last activity <b class="nr">not recorded</b></span>')
    flow = f' <span>· {E(m["flow"])}</span>' if m["flow"] else ""
    waiting = m["status"] == "waiting"
    steps = "".join(step_html(s, m["status"], waiting) for s in m["steps"])
    if not starting and not (reg / "RUN.md").is_file():
        steps = '<li class="step off"><span class="n">No run record (RUN.md) in this folder yet</span></li>'
    # the run's home once drawn; before it, the list of runs at the listener's root, which picks none of them
    home_href, home_name = ("index.html", "Home") if (reg / "index.html").is_file() else ("/", "All runs")
    import page_style as ps
    # the kit release on the run's own line, beside what kind of run it is: obvious, not a corner label
    sub.insert(1 if sub[:1] == ['<span>Mapping run</span>'] else 0, ps.kit_sub())
    up = (f'<a class="go" href="{ps.all_systems_href(home_href)}">{ps.ALL_SYSTEMS}</a>'
          if home_name == "Home" and ps.all_systems_above(reg) else "")
    drawn = ("" if asking
             else "No run folder yet: the first look over the system is under way. " if starting
             else f"Drawn from the run's record in {E(reg.name)}. ")
    import run_state
    alarm =(f'<div class="stopped-banner" role="alert" style="margin:0 0 12px;padding:12px 16px;border-radius:6px;'
             f'background:#B3261E;color:#fff;font-size:15px"><b>Stopped: this run needs you.</b> {E(st["reason"])} '
             f'<b>Next:</b> {E(st["next"])}</div>' if st["state"] == run_state.STOPPED else "")
    body = f"""<div class="page" data-run-state="{E(st['state'])}" data-run-key="{E(st.get('key') or '')}" data-run-why="{E(st.get('reason') or '')}">{alarm}<div class="screen">
<div class="nav">{up}<span class="sys">{E(m["title"])}</span><a class="go" href="{home_href}">{home_name}</a><a class="go on" href="{FILE}" aria-current="page">Run status</a>{ps.kit_label()}</div>
<div class="head"><div class="titlerow"><h1>{E(m["title"])}{flow}</h1>{badge}</div>
<div class="sub">{"".join(sub)}</div></div>
<div class="body{' ask' if m['action']['kind'] == 'say_back' else ''}"><nav class="rail" aria-label="Steps"><h2>Progress</h2><ol class="steps">{steps}</ol></nav>
<div class="main">{action_html(m)}{"" if asking else working_html(m)}{"" if asking else map_so_far_html(m)}{"" if asking else issues_html(m["issues"])}</div></div></div>
<p class="foot">{drawn}This page reloads itself every 15 seconds.</p></div>"""
    # where this page is saved (saved_pages.py), for the line it shows once its listener has gone
    saved = f'<meta name="saved" content="{E(str((reg / FILE).resolve()))}">' if (reg / "RUN.md").is_file() else ""
    return (PAGE.replace("<!--TITLE-->", E(run_state.title(st, m["title"]))).replace("<!--BODY-->", body + NOTICE.replace(
        "TOLD_RESET_MS", str(run_state.TOLD_RESET_SECONDS * 1000)))
            .replace("<title>", saved + "<title>", 1))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><!--TITLE--></title>
<style>
:root{--bg:#F6F5F1;--surface:#FFFFFF;--sunk:#F1EFE8;--line:#DAD7CD;--line-soft:#EEECE5;--fg:#1D1D1B;--fg2:#3D3B35;--fg3:#5A5850;
--accent:#1F4E8C;--ok:#2E7D4A;--ok-bg:#E6F0E9;--run:#1F4E8C;--run-bg:#E4ECF6;--you:#1F4E8C;--you-bg:#E4ECF6;--warn:#7A4B00;
--bad:#B4561F;--bad-bg:#F7EBE3;--off:#7A776E;--off-bg:#ECEAE3;--sans:"Segoe UI Variable Text","Segoe UI",system-ui,sans-serif;
--mono:Consolas,"Courier New",monospace;color-scheme:light}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:14px/1.45 var(--sans);margin:0;padding:0 0 48px}
.page{max-width:1400px;margin:0 auto;padding:0 16px;display:grid;gap:12px}
a{color:var(--accent);text-decoration:none} a:hover{text-decoration:underline}
.nav{display:flex;flex-wrap:wrap;align-items:center;gap:6px 18px;background:var(--surface);border-bottom:1px solid var(--line);padding:10px 22px;font-size:14px}
.nav .sys{font-weight:600}.nav .go{padding:4px 2px;border-bottom:2px solid transparent}.nav .go.on{border-bottom-color:var(--accent);font-weight:600}
.screen{background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-top:16px}
.head{padding:14px 18px 12px;border-bottom:1px solid var(--line-soft);display:grid;gap:6px}
.titlerow{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.titlerow h1{font-size:22px;font-weight:700;margin:0}.titlerow h1 span{font-weight:500;color:var(--fg2)}
.badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:3px 10px 3px 7px;font-size:12.5px;font-weight:600;white-space:nowrap}
.b-run,.b-you{background:var(--run-bg);color:var(--run)}.b-bad{background:var(--bad-bg);color:var(--bad)}
.b-off{background:var(--off-bg);color:var(--fg2)}.b-ok{background:var(--ok-bg);color:var(--ok)}
.sub{color:var(--fg2);font-size:13px;display:flex;flex-wrap:wrap;gap:4px 22px}.sub b{color:var(--fg);font-weight:600}
.nr{color:var(--fg3);font-weight:400}
.body{display:grid;grid-template-columns:minmax(250px,340px) minmax(0,1fr)}
.rail{border-right:1px solid var(--line-soft);background:var(--sunk);padding:8px 0}
.rail h2{font-size:13px;font-weight:600;color:var(--fg2);margin:0 0 6px;padding:2px 14px}
.steps{list-style:none;margin:0;padding:0}
.step{display:grid;grid-template-columns:20px minmax(0,1fr) auto;gap:1px 8px;align-items:start;padding:5px 14px}
.step .n{grid-column:2;font-size:13.5px;font-weight:500}
.step .d{grid-column:2/-1;font-size:12px;color:var(--fg2);overflow-wrap:break-word}
.step .t{grid-column:3;grid-row:1;font-size:12px;color:var(--fg3);font-variant-numeric:tabular-nums;text-align:right;max-width:15em}
.step .ic{grid-row:1/3;margin-top:1px}
.parts{grid-column:2/-1;list-style:none;margin:3px 0 0;padding:0;font-size:12px;display:grid;gap:1px}
.parts li{display:flex;justify-content:space-between;gap:8px;color:var(--fg2)}.parts .ps{color:var(--fg3);white-space:nowrap}
.parts li.done .ps{color:var(--ok)}.parts .more{color:var(--fg3)}
.step.cur{background:var(--surface);box-shadow:inset 3px 0 0 var(--run)}
.step.curbad{box-shadow:inset 3px 0 0 var(--bad)}
.step.off .n{color:var(--fg3);font-weight:400}
.dec{font-size:11px;font-weight:600;color:var(--fg3);border:1px solid var(--line);border-radius:3px;padding:0 4px;margin-left:4px;vertical-align:1px}
.live{margin:8px 18px 0;padding:8px 10px;border:1px solid var(--line);border-radius:6px;background:var(--surface);font-size:12.5px}
.key{margin:10px 18px 0;font-size:12px;color:var(--fg3)}
.ic{width:18px;height:18px;flex:none}
.main{padding:14px 16px 18px;display:grid;gap:14px;min-width:0;align-content:start}
.panel{border:1px solid var(--line);border-radius:8px;overflow:hidden}.panel>.note{padding:8px 12px;border-top:1px solid var(--line-soft)}
.who-now{width:100%;border-collapse:collapse;font-size:13px}.who-now th,.who-now td{text-align:left;padding:6px 10px;border-top:1px solid var(--line-soft);vertical-align:top}.who-now th{font-weight:600;color:var(--fg2);font-size:12px}.who-now .who{display:block;color:var(--fg3);font-size:11.5px}.who-now tr.warn td:last-child{color:var(--warn,#b26b00);font-weight:600}.who-now tr.bad td:last-child{color:var(--bad,#b3261e);font-weight:600}
.panel-h{display:flex;align-items:center;gap:10px;padding:8px 12px;background:var(--sunk);border-bottom:1px solid var(--line-soft)}
.panel-h h3{margin:0;font-size:14px;font-weight:600}.panel-h .r{margin-left:auto;font-size:12.5px;color:var(--fg2)}
.act{padding:10px 12px;font-size:14px;display:grid;gap:8px}
.act ol{margin:0;padding-left:18px;display:grid;gap:8px;font-size:13px}
.act-you{border-color:var(--you)}.act-you .panel-h{background:var(--you-bg)}
.cmd{display:inline-flex;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:4px 10px;font:13px var(--mono);max-width:100%}
.cmd code{overflow-wrap:anywhere}
.btn{margin-left:8px;font:12px var(--sans);border:1px solid var(--line);border-radius:4px;background:var(--sunk);cursor:pointer}
.note{font-size:12.5px;color:var(--fg2);margin:0}
.none{padding:12px 14px;color:var(--fg2);font-size:13px}
.ann{list-style:none;margin:0;padding:0}
.ann li{display:grid;grid-template-columns:22px minmax(0,1fr) minmax(160px,260px);gap:3px 14px;padding:12px 14px;border-top:1px solid var(--line-soft)}
.ann li:first-child{border-top:0}.ann .h{font-weight:600}
.ann .clr{font-size:12.5px;color:var(--fg2);border-left:1px solid var(--line-soft);padding-left:14px}
.ann .clr b{display:block;color:var(--fg3);font-weight:500;font-size:12px;margin-bottom:2px}
.foot{font-size:12px;color:var(--fg3);margin:0}
.sb{display:grid;gap:12px}
.sbt{border-collapse:collapse;width:100%}
.sbt th{text-align:left;vertical-align:top;font-weight:600;font-size:13px;color:var(--fg2);padding:10px 14px 10px 0;width:30%;border-top:1px solid var(--line-soft)}
.sbt td{padding:8px 0;border-top:1px solid var(--line-soft);display:grid;gap:6px}
.sbt tr:first-child th,.sbt tr:first-child td{border-top:0}
.sbt .v{font-size:14px;overflow-wrap:anywhere}
.sbh{display:flex;gap:12px 18px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.sbh b{display:block}
.sbq{display:flex;gap:10px}
.sbl{font-size:13px;color:var(--fg2);font-weight:600}
.sbc{font:13px var(--sans);padding:6px 8px;border:1px solid var(--line);border-radius:5px;background:var(--surface);color:var(--fg);width:100%;resize:vertical}
.sbc:focus{outline:2px solid var(--accent);outline-offset:1px}
.sbb{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.sb button{font:600 14px var(--sans);border-radius:6px;padding:8px 18px;cursor:pointer}
.sb .start{background:var(--accent);color:#fff;border:1px solid var(--accent);padding:9px 26px}
.sb .sec{background:var(--surface);color:var(--accent);border:1px solid var(--line)}
.sb button:disabled{opacity:.5;cursor:default}
@media (max-width:820px){.ask .main{order:-1}.sbt th{display:block;width:auto;padding:10px 0 2px}.sbt tr{display:block;border-top:1px solid var(--line-soft)}.sbt td{border-top:0;padding-top:2px}}
@media (max-width:640px){.body{grid-template-columns:minmax(0,1fr)}.rail{border-right:0;border-bottom:1px solid var(--line-soft)}
.ann li{grid-template-columns:22px minmax(0,1fr)}.ann .clr{grid-column:2;border-left:0;padding-left:0}}
@media (prefers-reduced-motion:no-preference){.spin{animation:spin 1.1s linear infinite;transform-origin:50% 50%}}
@keyframes spin{to{transform:rotate(360deg)}}
</style></head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="i-ok" viewBox="0 0 18 18"><circle cx="9" cy="9" r="8" fill="var(--ok)"/><path d="M5.2 9.3l2.4 2.4 5-5.2" stroke="#fff" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-run" viewBox="0 0 18 18"><circle cx="9" cy="9" r="7" fill="none" stroke="var(--run-bg)" stroke-width="2.4"/><path d="M9 2a7 7 0 0 1 7 7" fill="none" stroke="var(--run)" stroke-width="2.4" stroke-linecap="round"/></symbol>
<symbol id="i-next" viewBox="0 0 18 18"><circle cx="9" cy="9" r="7.2" fill="none" stroke="var(--run)" stroke-width="1.8"/><path d="M7.4 5.8l3.6 3.2-3.6 3.2" fill="none" stroke="var(--run)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-you" viewBox="0 0 18 18"><circle cx="9" cy="9" r="8" fill="var(--you)"/><circle cx="9" cy="6.6" r="2.3" fill="#fff"/><path d="M4.9 13.4c.6-2.2 2.2-3.3 4.1-3.3s3.5 1.1 4.1 3.3" fill="#fff"/></symbol>
<symbol id="i-youdone" viewBox="0 0 18 18"><circle cx="9" cy="9" r="8" fill="var(--ok)"/><circle cx="9" cy="6.6" r="2.3" fill="#fff"/><path d="M4.9 13.4c.6-2.2 2.2-3.3 4.1-3.3s3.5 1.1 4.1 3.3" fill="#fff"/></symbol>
<symbol id="i-bad" viewBox="0 0 18 18"><circle cx="9" cy="9" r="8" fill="var(--bad)"/><path d="M9 4.6v5.3" stroke="#fff" stroke-width="2" stroke-linecap="round"/><circle cx="9" cy="12.9" r="1.2" fill="#fff"/></symbol>
<symbol id="i-warn" viewBox="0 0 18 18"><path d="M9 1.8l7.6 13.4H1.4z" fill="var(--warn)" stroke="var(--warn)" stroke-linejoin="round" stroke-width="1.2"/><path d="M9 6.4v4.4" stroke="#fff" stroke-width="1.9" stroke-linecap="round"/><circle cx="9" cy="13" r="1.1" fill="#fff"/></symbol>
<symbol id="i-skip" viewBox="0 0 18 18"><circle cx="9" cy="9" r="7.2" fill="none" stroke="var(--off)" stroke-width="1.6"/><path d="M5.6 9h6.8" stroke="var(--off)" stroke-width="1.8" stroke-linecap="round"/></symbol>
<symbol id="i-todo" viewBox="0 0 18 18"><circle cx="9" cy="9" r="7.2" fill="none" stroke="var(--off)" stroke-width="1.6" stroke-dasharray="2.6 2.2"/></symbol>
<symbol id="i-info" viewBox="0 0 18 18"><circle cx="9" cy="9" r="8" fill="var(--off)"/><path d="M9 8.2v4.6" stroke="#fff" stroke-width="1.9" stroke-linecap="round"/><circle cx="9" cy="5.4" r="1.1" fill="#fff"/></symbol>
<symbol id="i-pause" viewBox="0 0 18 18"><circle cx="9" cy="9" r="8" fill="var(--you)"/><rect x="6" y="5.4" width="2.1" height="7.2" rx=".6" fill="#fff"/><rect x="9.9" y="5.4" width="2.1" height="7.2" rx=".6" fill="#fff"/></symbol>
</defs></svg>
<!--BODY-->
<script>(function(){var W={weekday:"short",day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",hourCycle:"h23",timeZoneName:"short"};
document.querySelectorAll("time[datetime]").forEach(function(el){var d=new Date(el.getAttribute("datetime"));if(isNaN(d))return;
try{var p={};new Intl.DateTimeFormat("en-US",W).formatToParts(d).forEach(function(x){p[x.type]=x.value});
el.textContent=(el.dataset.at==="weekday"?p.weekday+" ":"")+p.day+" "+p.month+", "+p.hour+":"+p.minute+" "+p.timeZoneName}catch(e){}})})();
document.addEventListener("click",function(e){var b=e.target.closest("[data-copy]");if(b&&navigator.clipboard)navigator.clipboard.writeText(b.dataset.copy)});
(function(){var f=document.querySelector("form.sb");if(!f)return;var fp=f.dataset.fp,k="sb-sent-"+fp,st=f.querySelector(".sbs");
function lock(t){st.textContent=t;f.querySelectorAll("button,input").forEach(function(x){x.disabled=true})}
try{if(sessionStorage.getItem(k))lock("Sent. The run carries on in its chat; this page follows it.")}catch(e){}
var box=f.querySelector(".sbc"),heads=f.querySelectorAll(".sbh button"),warn=f.querySelector(".sbw");
function typed(){var t=!!box.value.trim();heads.forEach(function(b){b.disabled=t});warn.hidden=!t}
box.addEventListener("input",typed);
f.addEventListener("submit",function(e){e.preventDefault();var act=(e.submitter&&e.submitter.value)||"start",c=box.value.trim();
if(act==="correct"&&!c){st.textContent="Say which line is wrong and what it should be first.";return}
if(act!=="correct"&&c){typed();return}
var said={start:"Sent. The run starts now; this page follows it.","search-yes":"Sent. The run looks for the code there, then shows these lines again with what it found.","search-no":"Sent. Nothing is searched; say in the run's chat where the code is.",correct:"Sent. The lines will be redrafted and shown here again."};
fetch("/answers",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({say_back:act==="correct"?{action:"correct",shown:fp,correction:c}:{action:act,shown:fp}})})
.then(function(r){if(!r.ok)throw r.status;try{sessionStorage.setItem(k,"1")}catch(e){}lock(said[act]||said.correct)})
.catch(function(){st.textContent="Could not send from this page. Say start, or your correction, in the run's chat instead."})})})();
function busy(){var f=document.querySelectorAll(".sbc");for(var i=0;i<f.length;i++)if(!f[i].disabled&&(f[i].value||f[i]===document.activeElement))return true;return false}
(function(){if(location.protocol==="file:")return;var failed=0,gone=false;
function ended(){if(gone)return;gone=true;var s=document.querySelector('meta[name="saved"]'),b=document.createElement("p");
b.className="ended";b.style.cssText="margin:12px auto 0;max-width:1400px;padding:10px 14px;border:1px solid #B4561F;border-radius:6px;background:#F7EBE3;font-size:14px";
b.textContent="This run's page server has stopped (the run finished, or Claude Code was closed), so this page no longer updates"+(s?"; its pages are saved: open "+s.content+" in your browser.":".");
document.body.insertBefore(b,document.body.firstChild)}
setInterval(function(){if(gone||document.visibilityState!=="visible"||busy())return;
fetch(location.href,{cache:"no-store"}).then(function(r){if(!r.ok)throw r.status;failed=0;location.reload()},function(){if(++failed>=2)ended()})},15000)})();</script>
</body></html>
"""
# One browser notice per stop (run_state, the state the title and banner show), keyed as the watchdog keys it: the
# stop's code, step and flow, never its words; told again only after the run works again. Permission asked once.
NOTICE = """<script>(function(){if(!("Notification" in window))return;var p=document.querySelector(".page[data-run-state]");
if(!p)return;var s=p.getAttribute("data-run-state"),key=p.getAttribute("data-run-key")||"",why=p.getAttribute("data-run-why")||"",
k="bfo-run-told:"+location.pathname,told=localStorage.getItem(k);
if(Notification.permission==="default"&&!localStorage.getItem("bfo-notice-asked")){localStorage.setItem("bfo-notice-asked","1");
Notification.requestPermission()}
var w="bfo-run-working:"+location.pathname;if(s!=="working")localStorage.removeItem(w);
if(s==="working"){var since=+localStorage.getItem(w)||Date.now();localStorage.setItem(w,since);
if(Date.now()-since>=TOLD_RESET_MS)localStorage.removeItem(k);return}
if(s==="stopped"&&told!==key){localStorage.setItem(k,key);if(Notification.permission==="granted")new Notification("Run stopped: it needs you",{body:why})}})();
</script>"""


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    reg = pathlib.Path(argv[0])
    out = pathlib.Path(argv[argv.index("--out") + 1]) if "--out" in argv else reg / FILE
    out.write_text(render(reg), encoding="utf-8")
    print(f"WROTE {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
