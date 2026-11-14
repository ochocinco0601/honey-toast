"""The operator view of a run: where it stands, what it needs from the person, and what is wrong, at a glance.
    python operator_page.py <register folder> [--out <file>]     writes <reg>/operator.html (or --out)
The listener (page_ask.py) draws the same page on each request for <run>/operator.html, so an open tab, which
reloads itself every 15 seconds while it is shown, follows the run with no step of the run's own. The work folder's own <work>/operator.html, the page the start
step opens, leads to the newest run's view, and before any run folder exists draws the first look under way.
Four panels, the same in every state: the title and the run's status; Progress, the run's whole path read from the
Status table of RUN.md (each row a step, in its order, named as the kit's status line names it to the person with
the record's own name kept beside it, rows that are not numbered phases tagged as the person's decisions, contiguous
rows the pick left out folded into one line, finished steps told by what they hold, in flows, stages, steps and
services, and linked to the pages they left; process mapping, while it runs, told by how far the record shows it is:
services read, calls left unmatched, findings judged in the latest round, flagged ones changed, and nothing where the
record cannot say; a flow the run chose itself, because the request named none, told as chosen by the run with its
reason, never as the person's decision); Required action, the choice the record says the run waits on
(depth.json's open choice, whichever row is current), or how to resume it, or what the run is doing for the person
and when they are next needed; Issues, one line each with what clears it. Times are the ones the record holds
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
    for p in (reg.parent / "run-started.json", reg / "_run-state" / "run-started.json", reg / "run-started.json"):
        t = _iso((_json(p) or {}).get("started"))
        if t:
            return t
    return None


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
         ("Define measures", False, ("4 ",)), ("Approve measures", True, ("Review of the measures",)),
         ("Design alerts", False, ("5 ", "5a ")), ("Approve alerts", True, ("Review of the alerts",)),
         ("Write runbooks", False, ("5b ",)), ("Verify against the code", False, ("6 ",)),
         ("Report", False, ("7 ",)), ("Next flow", False, ()))
# The decision each step asks for, as "Next needed at step N, ..." says it.
ASKS = {2: "choose the flow", 4: "choose the depth", 6: "approve the measures", 8: "approve the alerts",
        12: "choose the next flow"}
DEPTH_WORDS = {"none": "map only", "measure": "to measures", "alerting": "to alerts", "runbooks": "to runbooks"}


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


def read(reg, now=None, starting=False):
    """The operator view's content, read from the register folder: no file is written. `starting`: the work folder
    before any run folder is in it, drawn as a run whose first look is under way."""
    reg = pathlib.Path(reg)
    now = now or dt.datetime.now(dt.timezone.utc).astimezone()
    scope = _json(reg / "scope.json") or {}
    depth = _json(reg / "depth.json") or {}
    rows = [STARTING_ROW] if starting else status_rows(_text(reg / "RUN.md"))
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
            s["said"] = {2: scope.get("flow") or "", 4: depth_said(scope, reg) or ""}.get(n, "Approved")
            why = chosen_by_run(reg, scope) if n == 2 and not starting else None
            if why:  # the run took this decision itself: never shown as the person's
                s["said"], s["by_run"] = f"{s['said']} · chosen by the run, {why}", True
        elif n == 3 and state == DOING and not starting:
            s["said"] = mapping_progress(reg, scope)
        elif n == 3 and done:
            bits = [_plural(counts[f], NOUNS[f]) for f in ("stages.csv", "subjects.csv") if counts.get(f)]
            s["said"] = "Map: " + ", ".join(bits) if bits else "Map"
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
        steps.append(s)
    # contiguous steps the pick left out fold into one line, numbered as a range
    folded = []
    for s in steps:
        if s["state"] == NOT_PICKED and folded and folded[-1]["state"] == NOT_PICKED and s["numbers"][0] != 12:
            folded[-1]["numbers"].append(s["numbers"][0])
            folded[-1]["title"] += ", " + s["title"]
        else:
            folded.append(s)
    steps = folded
    current = next((k for k, s in enumerate(steps) if s["state"] not in (DONE, NOT_PICKED)), None)
    for k, s in enumerate(steps):
        s["current"] = k == current
    cur = steps[current] if current is not None else None
    last = last_write(reg)
    times = [t for t in [last, reported] + [decision_time(r[0], scope) for r in rows if is_decision(r[0])] if t]
    last_any = max(times, key=lambda t: t.timestamp()) if times else None
    age_min = (now.timestamp() - last.timestamp()) / 60 if last else None
    blocked = [s for s in steps if s["state"] == BLOCKED]
    choice = depth.get("open_choice") or None
    if blocked:
        status = "blocked"
    elif choice:  # the record says the run waits on the person's choice, whichever row is current
        status = "waiting"
    elif cur is None:
        status = "finished"
    elif cur["decision"] and cur["state"] != DOING:
        status = "waiting"
    elif age_min is not None and age_min <= RUNNING_MINUTES:
        status = "running"
    elif age_min is not None and age_min <= STALE_MINUTES:
        status = "quiet"
    else:
        status = "paused"
    if starting:
        status = "running"
    nxt = next((s["numbers"][0] for s in steps[(current or 0) + (1 if cur and not cur["decision"] else 0):]
                if s["numbers"][0] in ASKS and s["state"] == "to do"), None)
    resume = {"folder": workspace(reg), "phrase": f"continue the run on {capability(reg, depth)}"}
    if status == "waiting":
        at = cur["numbers"][0] if cur else 12
        what = (choice or {}).get("task") or ASKS.get(at) or cur["title"]
        action = {"kind": "decide", "step": at, "what": what[:1].lower() + what[1:],
                  "on_page": (choice or {}).get("milestone") in ON_PAGE if choice else False,
                  "resume": resume if age_min is None or age_min > STALE_MINUTES else None}
    elif status in ("paused", "blocked"):
        action = dict(resume, kind="resume")
    else:
        action = {"kind": "none", "next": nxt, "ask": ASKS.get(nxt)}
    if cur is not None and status == "paused" and cur["state"] == "to do":
        cur["said"] = cur["said"] or "On resume"
    jobs = job_counts(reg) if status in ("running", "quiet") else None
    if cur is not None and cur["state"] == DOING and jobs:
        cur["said"] = f'{jobs["done"]} of {jobs["all"]} done' + (f' · {jobs["blocked"]} blocked' if jobs["blocked"] else "")
    issues = []
    for s in blocked:
        issues.append({"what": f"Step {s['numbers'][0]}, {s['title']}, is blocked: "
                               f"{s['why'] or 'the record gives no reason'}",
                       "clears": "Fixing what the reason names, then resuming the run", "bad": True})
    if off:
        issues.append({"what": f"Map not verified: {len(off)} of {len(rr)} statements failed the code check",
                       "clears": "Step 10, when the run resumes", "bad": True})
    if any(r[0].startswith("7 ") and r[1] == DOING for r in rows) and not reported and \
            (_json(reg / "done-check.json") or {}).get("done") is False:
        issues.append({"what": "The final check says the run is not done yet",
                       "clears": "Step 11, the final check passing on the map as it is", "bad": False})
    return {"title": STARTING_TITLE if starting else capability(reg, depth), "flow": scope.get("flow"), "started": when(started_at(reg)),
            "last": when(local(last_any)) if last_any else None,
            "last_ago": ago(now, last_any) if last_any else None, "recent": bool(last_any) and
            (now.timestamp() - last_any.timestamp()) < 3600,
            "status": status, "steps": steps, "current": current, "action": action, "issues": issues,
            "left": left, "quiet_min": int(age_min) if status == "quiet" else None}


ICON = {DONE: "i-ok", "decided": "i-youdone", DOING: "i-run", BLOCKED: "i-bad", NOT_PICKED: "i-skip",
        "to do": "i-todo", "next": "i-next", "you": "i-you"}
BADGE = {"running": ("b-run", "i-run", "Running"), "quiet": ("b-off", "i-info", "No recent write"),
         "paused": ("b-you", "i-pause", "Paused · action required"), "waiting": ("b-you", "i-you", "Waiting on you"),
         "blocked": ("b-bad", "i-bad", "Blocked"), "finished": ("b-ok", "i-ok", "Finished")}


def step_html(s, status, waiting):
    ns = s["numbers"]
    num = f"{ns[0]}–{ns[-1]}" if len(ns) > 1 else str(ns[0])
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
    desc = [said] if said else []
    if st == BLOCKED and s["why"]:
        desc.append(E(s["why"]))
    if s["current"] and waiting:
        desc.append("Waiting on you")
    spin = " spin" if st == DOING and status == "running" and not waiting else ""
    d = f'<span class="d">{" · ".join(desc)}</span>' if desc else ""
    return (f'<li class="{cls}"><svg class="ic{spin}"><use href="#{ic}"/></svg>{title}{num}. {E(s["title"])}{tag}'
            f'</span>{d}<span class="t">{E(s["time"] or "")}</span></li>')


def copy_cmd(text, path=False):
    return (f'<span class="cmd{" path" if path else ""}"><code>{E(text)}</code><button class="btn sm" type="button" '
            f'data-copy="{E(text)}">Copy</button></span>')


def resume_html(r):
    return (f'<ol><li>In VS Code, open {copy_cmd(r["folder"], True)}</li>'
            f'<li>In a Claude Code tab there, type {copy_cmd(r["phrase"])}</li></ol>')


def action_html(m):
    a = m["action"]
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
    if m["status"] == "quiet":
        lead += (f' <span class="note">No write for {m["quiet_min"]} min: check the run\'s Claude Code tab before '
                 'resuming it.</span>')
    return f'<div class="panel"><div class="panel-h"><h3>Required action</h3></div><div class="act">{lead}</div></div>'


def issues_html(issues):
    if not issues:
        inner = '<div class="none">None</div>'
    else:
        inner = '<ul class="ann">' + "".join(
            f'<li><svg class="ic"><use href="#{"i-bad" if i["bad"] else "i-warn"}"/></svg><span class="h">'
            f'{E(i["what"])}</span><span class="clr"><b>Clears</b>{E(i["clears"])}</span></li>' for i in issues) + "</ul>"
    return (f'<div class="panel"><div class="panel-h"><h3>Issues</h3><span class="r">most severe first</span></div>'
            f'{inner}</div>')


def render(reg, now=None, starting=False):
    """The page. `starting`: the work folder before any run folder is in it (read's `starting`)."""
    reg = pathlib.Path(reg)
    m = read(reg, now, starting)
    cls, ic, word = BADGE[m["status"]]
    spin = " spin" if m["status"] == "running" else ""
    sub = ['<span>Mapping run</span>']
    sub.append(f'<span>Started <b>{E(m["started"])}</b></span>' if m["started"]
               else '<span>Started <b class="nr">not recorded</b></span>')
    if m["last"] and m["recent"]:
        sub.append(f'<span>Last activity <b>{E(m["last_ago"])}</b></span>')
    elif m["last"]:
        sub.append(f'<span>Last activity <b>{E(m["last"])}</b> ({E(m["last_ago"])})</span>')
    else:
        sub.append('<span>Last activity <b class="nr">not recorded</b></span>')
    flow = f' <span>· {E(m["flow"])}</span>' if m["flow"] else ""
    waiting = m["status"] == "waiting"
    steps = "".join(step_html(s, m["status"], waiting) for s in m["steps"])
    if not starting and not (reg / "RUN.md").is_file():
        steps = '<li class="step off"><span class="n">No run record (RUN.md) in this folder yet</span></li>'
    # the run's home once drawn; before it, the work page at the listener's root, which shows the sources and progress
    home_href, home_name = ("index.html", "Home") if (reg / "index.html").is_file() else ("/", "The run at work")
    drawn = ("No run folder yet: the first look over the system is under way." if starting
             else f"Drawn from the run's record in {E(reg.name)}.")
    body = f"""<div class="page"><div class="screen">
<div class="nav"><span class="sys">{E(m["title"])}</span><a class="go" href="{home_href}">{home_name}</a><a class="go on" href="{FILE}" aria-current="page">Run status</a></div>
<div class="head"><div class="titlerow"><h1>{E(m["title"])}{flow}</h1><span class="badge {cls}"><svg class="ic{spin}"><use href="#{ic}"/></svg>{E(word)}</span></div>
<div class="sub">{"".join(sub)}</div></div>
<div class="body"><nav class="rail" aria-label="Steps"><h2>Progress</h2><ol class="steps">{steps}</ol></nav>
<div class="main">{action_html(m)}{issues_html(m["issues"])}</div></div></div>
<p class="foot">{drawn} This page reloads itself every 15 seconds.</p></div>"""
    return PAGE.replace("<!--TITLE-->", E("Run status · " + m["title"])).replace("<!--BODY-->", body)


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
.head{padding:18px 22px 16px;border-bottom:1px solid var(--line-soft);display:grid;gap:10px}
.titlerow{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.titlerow h1{font-size:22px;font-weight:700;margin:0}.titlerow h1 span{font-weight:500;color:var(--fg2)}
.badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:3px 10px 3px 7px;font-size:12.5px;font-weight:600;white-space:nowrap}
.b-run,.b-you{background:var(--run-bg);color:var(--run)}.b-bad{background:var(--bad-bg);color:var(--bad)}
.b-off{background:var(--off-bg);color:var(--fg2)}.b-ok{background:var(--ok-bg);color:var(--ok)}
.sub{color:var(--fg2);font-size:13px;display:flex;flex-wrap:wrap;gap:4px 22px}.sub b{color:var(--fg);font-weight:600}
.nr{color:var(--fg3);font-weight:400}
.body{display:grid;grid-template-columns:minmax(300px,420px) minmax(0,1fr)}
.rail{border-right:1px solid var(--line-soft);background:var(--sunk);padding:12px 0}
.rail h2{font-size:13px;font-weight:600;color:var(--fg2);margin:0 0 6px;padding:4px 18px}
.steps{list-style:none;margin:0;padding:0}
.step{display:grid;grid-template-columns:22px minmax(0,1fr) auto;gap:2px 10px;align-items:start;padding:7px 18px}
.step .n{grid-column:2;font-size:13.5px;font-weight:500}
.step .d{grid-column:2;font-size:12px;color:var(--fg2);overflow-wrap:anywhere}
.step .t{grid-column:3;grid-row:1;font-size:12px;color:var(--fg3);font-variant-numeric:tabular-nums;white-space:nowrap}
.step .ic{grid-row:1/3;margin-top:1px}
.step.cur{background:var(--surface);box-shadow:inset 3px 0 0 var(--run)}
.step.curbad{box-shadow:inset 3px 0 0 var(--bad)}
.step.off .n{color:var(--fg3);font-weight:400}
.dec{font-size:11px;font-weight:600;color:var(--fg3);border:1px solid var(--line);border-radius:3px;padding:0 4px;margin-left:4px;vertical-align:1px}
.live{margin:8px 18px 0;padding:8px 10px;border:1px solid var(--line);border-radius:6px;background:var(--surface);font-size:12.5px}
.key{margin:10px 18px 0;font-size:12px;color:var(--fg3)}
.ic{width:18px;height:18px;flex:none}
.main{padding:18px 22px 24px;display:grid;gap:20px;min-width:0;align-content:start}
.panel{border:1px solid var(--line);border-radius:8px;overflow:hidden}
.panel-h{display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--sunk);border-bottom:1px solid var(--line-soft)}
.panel-h h3{margin:0;font-size:14px;font-weight:600}.panel-h .r{margin-left:auto;font-size:12.5px;color:var(--fg2)}
.act{padding:14px 16px;font-size:14px;display:grid;gap:8px}
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
@media (max-width:820px){.body{grid-template-columns:minmax(0,1fr)}.rail{border-right:0;border-bottom:1px solid var(--line-soft)}
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
<script>document.addEventListener("click",function(e){var b=e.target.closest("[data-copy]");if(b&&navigator.clipboard)navigator.clipboard.writeText(b.dataset.copy)});setInterval(function(){if(document.visibilityState==="visible")location.reload()},15000);</script>
</body></html>
"""


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
