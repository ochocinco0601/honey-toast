"""Run control for mapping one flow: decide the next action from the case record and the files on disk.

Usage: python next.py <register folder> <flow id> [--by-kit] [--test] [--event stop "<the person's words>" | --event launcher-done <file>
                                                     | --event chat "<the person's words>"
                                                     | --event retry "<the person's words>"]

Prints one action as JSON. The session does what it says and calls this again; it never decides the next step itself.
  judgment  a bounded task for the model: `task`, `write` (the tables it may write), `contract` (the checks it must
            pass), `findings` (what the last check said); hand back by calling this again
  fanout    launch one general-purpose agent per line of `pointer_lines`, at most `cap` launchers at once, then end
            the turn; call this again on each launcher's reply (--event launcher-done)
  wait      agents are still running; nothing to launch: end the turn and call this again on the next reply
  code      a step this script ran itself (`ran`), or one too long to run here (`command`, `wait`)
  stop      a point where the run waits on the person: `stop`, `message` (written for them), `records_with`;
            `stop` "agents lost" is a step whose agents stopped without their work (an API error each time they were
            launched, past run-settings.json `relaunches`, or a finish without it): the run never moves past it; on
            the person's word to try again, call this with --event retry, which launches them afresh
  notify    a line the session sends as it is
  agent     (the fast map only) launch one agent of `agent_type` with `prompt` as its whole prompt, wait for its
            reply, then call this again

The order is mapping's, one flow at a time: lead steps, Business Impact, the pick, units listed, readers, merge,
re-reads of calls between units, lead rows, judge round 1, fixers, judge round 2, the map drawn, the check, mapping
ends. A flow read by stage (go.BY_STAGE, every go since release 9.5) stops for the person's pick of how far each stage
goes before any reader starts, when the stage kit runs it (--by-kit), and its readers read only the services of the
stages taken further; the mapping skill run alone has no pick and reads no service in depth. Run by the stage kit,
mapping is never ended here and the map stop hands the flow back to the kit; a stage taken further after the map
stop opens the reading again for its services. The case keeps where the flow is (case.py);
every agent the run launches is a record there, opened before launch and closed when its unit's work is on disk.
On every call, whatever it decides (a launch, a launcher's reply, a wait, a stop), it rewrites job/timings.csv, one
row per agent attempt, timed from the agents' own transcripts (timings.py); a failure there is logged and never
changes the action.
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import case  # noqa: E402
import judges  # noqa: E402
import readers  # noqa: E402
import register_layout as layout  # noqa: E402
import run_md  # noqa: E402
import tables  # noqa: E402

ENDED = case.ENDED
LEAD_WRITE = ["flows", "lifecycle", "stages", "steps", "subjects", "participation"]
LEAD_RULES = ["case", "stages-connect", "reachable", "grounded", "cited"]
IMPACT_WRITE = ["step-impact", "case-attributes"]
LEAD_ROWS_WRITE = ["set-aside", "agent-system", "capabilities", "step-impact", "case-attributes",
                   "merge/lead-rows/subjects", "merge/lead-rows/participation", "merge/lead-rows/placeholders",
                   "measure-gaps"]
import guard  # noqa: E402
ORDER = guard.ORDER  # one order, read by run control and by every script it guards
FAST_ORDER = guard.FAST_ORDER  # the fast map (go.py --fast): one mapping agent, then merge, checks and drawing
NOT_READ_WHY = "not read in this run: no call the code reader found reaches it from a stage taken further"
MESSAGES = "case-messages"
RUNNING = ("still running", "queued")


def order(reg):
    return guard.order(reg)


def fast(reg):
    """Whether the flow worked now is mapped fast (run-settings.json `mapping`, recorded at the go)."""
    return guard.order(reg) is FAST_ORDER


def _lock_refusal(reg):
    import run_lock
    refusal, _ = run_lock.hold(reg)
    return refusal


def _run(cmd):
    p = subprocess.run([sys.executable, *cmd], cwd=HERE, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def _code(reg, sub, cmd, done=lambda: True):
    """Run a short code step here; None when it worked, or the failure as the action, so a run never passes over a
    step that failed."""
    code, out = _run(cmd)
    case.log(reg, f"ran {cmd[0]}", code=code, said=out[-400:])
    if code == 0 and done():
        return None
    return {"kind": "code", "sub": sub, "ok": False, "command": ["python", *cmd], "said": out}


def _pointers(lines):
    head = judges.POINTER.split("{}")[0]
    return [x for x in lines if x.startswith(head)]


def _running(lines):
    return any(any(w in x for w in RUNNING) for x in lines)


def _check_lead(reg, flow):
    """What the lead's own steps still lack, from the map's own inspection (the rules the lead's rows answer)."""
    import map_record
    R = map_record.load(reg)
    if not any(f.get("flow_id") == flow for f in R["flows"]):
        return [f"no row for {flow} in the flows"]
    stages = [s for s in R["stages"] if s.get("flow") == flow]
    if not stages or not [s for s in R["steps"] if s.get("stage") in {x["stage"] for x in stages}]:
        return ["no stages or no process steps for the flow"]
    import check_map
    return [f"{r['title']}: {'; '.join(r['items'])}" for r in check_map.inspect(reg, flow)
            if r["rule"] in LEAD_RULES and not r["passed"]]


def _check_impact(reg, flow):
    import check_map
    return [f"{r['title']}: {'; '.join(r['items'])}" for r in check_map.inspect(reg, flow)
            if r["rule"] == "impact" and not r["passed"]]


def _check_lead_rows(reg, flow):
    import map_record
    R = map_record.load(reg)
    out = [] if R.get("capabilities") else ["no capability named"]
    import check_map
    out += [f"{r['title']}: {'; '.join(r['items'])}" for r in check_map.inspect(reg, flow)
            if r["rule"] in ("impact", "parts") and not r["passed"]]
    return out + _lead_parts_now_read(reg)


def _redraw_stale(reg, flow, sub):
    """After a merge: every stage output already drawn whose register tables have changed since (run_status.stale) is
    drawn again by flow_outputs.py, so a later merge never leaves the person stale pages. None when all worked."""
    import run_status
    reg = pathlib.Path(reg)
    for folder in sorted(p for p in reg.glob("stage-*") if p.is_dir()):
        stage = folder.name[len("stage-"):]
        if any(run_status.stale(reg, f.relative_to(reg).as_posix()) for f in folder.iterdir() if f.is_file()):
            failed = _code(reg, sub, ["flow_outputs.py", str(reg), flow, stage, "--out", str(folder)])
            if failed:
                return failed
    return None


def _lead_duplicates(reg):
    """In a fast run, the lead's own part rows (subjects.csv) that name a service the mapping agent maps (a deployable
    of units.csv): the merged map would hold it twice. Nothing in a full run, whose lead rows are checked otherwise."""
    if not fast(reg):
        return []
    import register_layout as layout
    mapped = {(r.get("deployable") or "").strip().lower() for r in _rows(reg / layout.UNITS_CSV)}
    mapped |= {(r.get("service") or "").strip().lower() for r in _rows(reg / "survey.csv")}
    mapped -= {""}
    # once merged, the root holds the mapping agents' own service rows; the lead's rows are the merge's input
    lead = reg / layout.LEAD_ROWS / "subjects.csv"
    where = "merge/lead-rows/subjects.csv" if lead.is_file() else "subjects.csv"
    return [f"{where} {r.get('subject_id', '').strip()} names the service '{r.get('name', '').strip()}', which "
            "the mapping agent maps: remove it, and name the service by its name in the lifecycle (the mapping "
            "agent writes its row)" for r in _rows(lead if lead.is_file() else reg / "subjects.csv")
            if (r.get("name") or "").strip().lower() in mapped]


def _fast_questions_owed(reg, flow):
    """The view questions mapping owes (run_status.mapping_owed), which a fast run's lead answers or gaps after the
    merge, before the map is drawn, so the done check does not find them empty after the measures."""
    import run_status
    return [why for what, _, why in run_status.mapping_owed(reg, flow) if what == "questions"]


def _needs_from_calls(reg, flow):
    """A fast run's lead writes the lifecycle before the mapping agents find the calls, so after the merge each call
    placed under a step whose callee none of that step's moves carries or needs is the lead's to settle (add the callee
    to the move's needs, or correct the call's step_hint), by flow_outputs' one rule, for every stage of the flow."""
    import flow_outputs
    try:
        R = flow_outputs.load(str(reg))
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for st in [s["stage"] for s in R.get("stages", []) if s.get("flow") == flow]:
        try:
            out += flow_outputs.needs_from_calls_failures(flow_outputs.build(R, flow, st))
        except (KeyError, ValueError, IndexError):  # a stage the map does not yet hold whole is checked by the draw
            continue
    return list(dict.fromkeys(out))


def _rows(p):
    import csv
    p = pathlib.Path(p)
    if not p.is_file():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


READING_LINE = "- **Read in depth:**"
REACH_WHY = "reach_why"  # in a flow's record: why the sweep read every service the go took in
PLACEHOLDERS = "merge/lead-rows/placeholders.csv"  # subject_id and flow of each part row the lead wrote at the level of the
# service for a service no reader read: the only rows ever named for removal once a reader covers that service


def _sweep(reg):
    """After the merge: the surveyed services a reader's recorded call reaches from a step of a stage taken further,
    not yet read for this flow (go.recorded_reach), are added to the flow's record (go.REACHED), so they are owed a
    reader; True when any was added, and run control goes back to the units and the readers. It loops until no call
    reaches a service not read: only then the lead's rows and the judging start. Nothing for a flow not read by stage."""
    import go
    s = _by_stage(reg)
    if not s:
        return False
    read = go.services_read(reg, s) or set()
    outs = {n.strip().lower() for n in s.get("services_out") or [] if n.strip()}
    consumers, lost = go.published_reach(reg, s)
    unresolved = go.unresolved_reach(reg, s)
    new = (go.recorded_reach(reg, s) | consumers) - read - outs
    if lost or unresolved:  # a reach the kit cannot resolve to one surveyed service: read every service of the go
        took = {n.strip().lower() for n in s.get("services_in") or [] if n.strip()}
        new |= took - read
        said = [f"a message with no consumer found: {t}" for t in sorted(set(lost))] + unresolved
        why = ("every service the go took in is read: a call or message from a stage taken further reaches what "
               "matches no single surveyed service: " + "; ".join(said))
        if s.get(REACH_WHY) != why:
            s[REACH_WHY] = why
            go.save(reg, s)
            _record_reading(reg)
    if not new:
        return False
    s[go.REACHED] = sorted(go.reached(s) | new)
    go.save(reg, s)
    case.log(reg, "a reader's call reaches services not read: read them", reached=sorted(new))
    _record_reading(reg)
    return True


def _record_reading(reg):
    """The run record's line saying which services the flow reads in depth and why (go.stage_reading), written
    when the units are listed, after the pick: a pick that reads every service because a part could not be told
    apart says so there."""
    import re
    import go
    s = _by_stage(reg)
    p = pathlib.Path(reg) / "RUN.md"
    if not s or not p.is_file():
        return
    _, why = go.stage_reading(reg, s)
    if go.reached(s):
        why += "; and, reached by a call a reader recorded from those stages: " + ", ".join(sorted(go.reached(s)))
    if s.get(REACH_WHY):
        why += "; " + s[REACH_WHY]
    line = f"{READING_LINE} {why}"
    text = p.read_text(encoding="utf-8")
    if READING_LINE in text:
        text = re.sub(rf"^{re.escape(READING_LINE)}.*$", lambda m: line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    run_md.write(p, text)
    case.log(reg, "reading in depth", why=why)


def _lead_parts_now_read(reg):
    """In a flow read by stage, each part the lead wrote at the level of the service (merge/lead-rows/subjects.csv)
    that a reader now covers, because a stage reaching it was taken further: its reader's rows replace the lead's. Only
    rows the lead marked as such placeholders (PLACEHOLDERS, by subject_id) are candidates, and one is named only when
    a reader's row of band application is for the same surveyed service (go.service_of: its name, else the path its
    repository names). A store, a broker or any reader's row is never named."""
    if not _by_stage(reg):
        return []
    import go
    reg = pathlib.Path(reg)
    flow = go.flow_id_of(reg, go.load(reg))
    # only the flow worked now's own placeholders: a finished flow's rows are never removed (later flows add, change none)
    marked = {(r.get("subject_id") or "").strip() for r in tables.dicts(reg / PLACEHOLDERS)
              if flow and (r.get("flow") or "").strip() == flow} - {""}
    if not marked:
        return []
    lead = [r for r in tables.dicts(reg / layout.LEAD_ROWS / "subjects.csv")
            if (r.get("subject_id") or "").strip() in marked]
    lead_keys = {((r.get("subject_id") or "").strip(), (r.get("name") or "").strip()) for r in lead}
    families = go.part_families()
    readers = [r for r in tables.dicts(reg / "subjects.csv") if (r.get("kind") or "").strip() == "element"
               and (r.get("band") or "").strip() == "application"
               and not go.recorded_not_a_service(r, families)
               and ((r.get("subject_id") or "").strip(), (r.get("name") or "").strip()) not in lead_keys]
    by_service = {}
    for r in readers:
        svc = go.service_of(reg, r)
        if svc is not None:
            by_service.setdefault(svc, []).append((r.get("subject_id") or "").strip())
    out = []
    for r in lead:
        svc = go.service_of(reg, r)
        if svc in by_service:
            name = (r.get("name") or "").strip() or (r.get("subject_id") or "").strip()
            out.append(f"{name} ({(r.get('subject_id') or '').strip()}), the lead's placeholder for {svc}, stands beside "
                       f"its reader's row ({', '.join(by_service[svc])}): remove it from merge/lead-rows/ (subjects, "
                       "participation and placeholders.csv) and its 'not read' gaps in measure-gaps.csv, then merge "
                       "again")
    return out


def _by_stage(reg):
    """The go of the flow worked now, when it is read by stage (go.BY_STAGE), else None."""
    import go
    s = go.load(reg)
    return s if s and s.get(go.BY_STAGE) else None


def _pick_owed(reg, by_kit):
    """Whether run control stops for the pick of how far each stage goes before any code is read in depth: only for a
    flow read by stage, run by the stage kit, whose pick is not recorded yet. In a fast map the pick decides which
    stages get a step-level map, so which code the mapping agent reads and how long it takes; in the full path it
    also decides the measures, alerts and runbooks. The mapping skill run alone has no pick."""
    s = _by_stage(reg)
    return bool(s and by_kit and not s.get("depth"))


def _pick_stop(reg, flow):
    return {"kind": "stop", "stop": "pick", "sub": "pick",
            "then": "the stage kit's SKILL.md: the pick of how far each stage goes, now, before any service is read in "
                    "depth (brief.py depth; recorded with go.py --depth), then call this again",
            "records_with": "go.py --depth"}


def _unmatched(reg):
    return tables.dicts(pathlib.Path(reg) / layout.UNMATCHED_CSV)


def _flagged_units(reg):
    return [u for u in judges._units(reg) if readers._flagged(reg, u)]


def _owed(reg, flow):
    import check_map
    import run_status
    out = list(run_status.questions_owed_mapped_only(reg))
    if run_status.undrawable(reg):
        out.append(run_status.cannot_draw_reason(run_status.undrawable(reg)))
    out += [reason for _, _, reason in check_map.open_items(reg, flow)]
    return out


def _fanout(reg, flow, sub, kind, rnd, units, lines, lost=None):
    ptr = _pointers(lines)
    if ptr:
        for u in units:
            case.open_record(reg, flow, u, kind, rnd)
        return {"kind": "fanout", "sub": sub, "pointer_lines": ptr, "cap": judges.launcher_cap(reg),
                "said": [x for x in lines if x not in ptr]}
    if _running(lines):
        return {"kind": "wait", "sub": sub, "said": lines}
    gone = lost() if lost else []
    if gone:  # nothing left to launch or running, and work still owed: the run stops here, its records kept open
        return _lost_stop(reg, sub, gone, lines)
    for r in case.records(reg):
        if r["status"] == "open" and r["flow"] == flow and r["kind"] == kind and r["round"] == rnd:
            case.close_record(reg, r["id"])
    return None


def _lost(reg, sub):
    """The agents of this step whose owed output is not on disk: [(their unit, their prompt file, their state)]. A
    reader owes its unit's files.csv for the flow worked now (readers.in_scope); a judge, its verdict file."""
    reg = pathlib.Path(reg)
    out = []
    if sub == "readers":
        out = [(u, layout.prompts_dir(reg, u) / "read.md") for u in readers.in_scope(reg)[0]]
    elif sub in ("judge round 1", "judge round 2"):
        rnd = int(sub[-1])
        n = judges.settings(reg)["judges"]
        for u in (judges._units(reg) if rnd == 1 else _flagged_units(reg)):
            for row in judges.scope(reg, u, rnd, n, "flagged" if rnd == 2 else None):
                for j in range(1, n + 1):
                    v = judges.verdict_path(reg, row, rnd, j)
                    if not v.is_file():
                        out.append((u, layout.prompts_dir(reg, u) / f"{v.stem}.md"))
    if not out:
        return []
    seen = judges.Launches(reg)
    return [(u, f, seen.state(f)) for u, f in out]


def _names(reg, units):
    """The services the units are code of (units.csv `deployable`), as the person knows them."""
    by = {(r.get("unit") or "").strip(): (r.get("deployable") or "").strip() or (r.get("unit") or "").strip()
          for r in tables.dicts(pathlib.Path(reg) / layout.UNITS_CSV)}
    got = list(dict.fromkeys(by.get(u, u) for u in units))
    return got[0] if len(got) == 1 else ", ".join(got[:-1]) + " and " + got[-1]


def _lost_stop(reg, sub, gone, lines):
    """The stop on a step whose agents stopped without their work, rendered through brief.py say like the map stop."""
    states = {st for _, _, st in gone}
    if sub == "readers":
        what = (f"Mapping has stopped before the map is put together: the code of {_names(reg, [u for u, _, _ in gone])} "
                "was not read to the end, so the map would be missing what that code does.")
    else:
        n = len(gone)
        what = (f"Mapping has stopped before the map is finished: {n} {'check' if n == 1 else 'checks'} of its "
                "findings against the code did not finish, so the map would show those findings as if checked.")
    why = []
    if states & {"errored", "gave up"}:
        why.append(f"Each try broke off on an error from the service that runs the model, and it was tried "
                   f"{judges.relaunch_cap(reg) + 1} times.")
    if "finished" in states or None in states:
        why.append("A try finished without writing down what it found.")
    if "ran a shell" in states:
        why.append("A try used a tool it is not allowed, so its work cannot be counted.")
    text = " ".join([what] + why + ["Nothing already done is lost. Say \"try again\" and it is done again."])
    folder = pathlib.Path(reg) / MESSAGES
    folder.mkdir(exist_ok=True)
    f = folder / f"agents-lost-{sub.replace(' ', '-')}.md"
    f.write_text(text, encoding="utf-8")
    code, out = _run(["brief.py", "say", str(reg), str(f)])
    case.log(reg, "agents lost", sub=sub, prompts=[pathlib.Path(p).as_posix() for _, p, _ in gone], states=sorted(
        str(x) for x in states))
    if code != 0:
        return {"kind": "code", "sub": sub, "ok": False, "command": ["python", "brief.py", "say", str(reg), str(f)],
                "said": out}
    return {"kind": "stop", "stop": "agents lost", "sub": sub, "message": out, "said": lines,
            "records_with": "next.py --event retry \"<their words>\" on their word to try again; else "
                            "next.py --event chat"}


def _retry(reg, sub):
    """The person said to try again: tries of agents an API error stopped count from now, and the prompt file of each
    agent of this step that stopped, finished or ran a shell without its work is removed, so it is launched afresh; a
    reader that ran a shell first has what it wrote put back (provenance.undo_breaches, as readers.py --again does)."""
    import datetime
    reg = pathlib.Path(reg)
    (reg / layout.PROMPTS).mkdir(parents=True, exist_ok=True)
    (reg / layout.PROMPTS / judges.RETRY_FROM).write_text(
        datetime.datetime.now(datetime.timezone.utc).isoformat(), encoding="utf-8")
    for u, f, state in _lost(reg, sub):
        if state == "ran a shell" and sub == "readers":
            import provenance
            provenance.undo_breaches(reg, u)
        if state in ("finished", "errored", "gave up", "ran a shell"):
            pathlib.Path(f).unlink(missing_ok=True)


def _readers_held(reg, owed):
    """Why the readers owed cannot be launched now, or None: the checks a direct readers.py call makes (guard.py, the
    reader agent installed, the units' code under the folder their prompts name), so run control never launches past
    them."""
    return (guard.require(reg, "read", units=owed) or readers.reader_agent_problem(reg)
            or readers.workspace_problem(reg, owed))


def _judges_held(reg, units, rnd):
    """Why this round's judges cannot be launched now, or None: the checks a direct judges.py emit makes (the judge
    agent installed, every cited file under the folder the prompts name)."""
    return next((h for u in units for h in [judges.launch_problem(reg, u, rnd, "flagged" if rnd == 2 else None)]
                 if h), None)


def _judgment(sub, task, write, contract, findings):
    return {"kind": "judgment", "sub": sub, "task": task, "write": write, "contract": contract, "findings": findings}


def _fast_set_aside(reg, sub):
    """None when no mapping agent's rows are refused. Else {"kind": "code", ...} that stops for the person when a unit
    was refused again after its relaunch, or {"kind": "set aside", "units"} when run control set the refused writers'
    tables aside (fast_map.set_aside_refused) so the mapping agent is launched again for those units."""
    import fast_map
    owed, stuck, why = fast_map.set_aside_refused(reg)
    o2, s2, w2 = fast_map.set_aside_bad_ids(reg)  # row ids that break the unit format: written again before the merge
    owed, stuck, why = sorted(set(owed) | set(o2)), sorted(set(stuck) | set(s2)), why + w2
    if stuck:
        said = (f"REFUSED: the mapping agent's rows for {', '.join(stuck)} were refused again after it was launched "
                f"once more: {'; '.join(why)}. Nothing was launched.")
        case.log(reg, "fast read held", said=said)
        return {"kind": "code", "sub": sub, "ok": False, "said": said}
    if owed:
        case.log(reg, "set aside a refused mapping agent's rows", units=owed)
        return {"kind": "set aside", "units": owed}
    return None


FAST_LAUNCHES = "launches.json"  # fast/: {unit: {"launches", "listed", "stalled"}}, kept by _fast_stalled


def _fast_stalled(reg, missing):
    """Record a launch of each unit in `missing` and return the units that have now been launched again without
    progress (their files.csv lists no more files than at the launch before) more times than run-settings.json
    `relaunches` allows. A unit that progresses (a split share read) is never held by the cap."""
    import fast_map
    import settings
    cap = int(settings.load(reg).get("relaunches") or 2)
    p = pathlib.Path(reg) / fast_map.FOLDER / FAST_LAUNCHES
    got = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    stuck = []
    for u in missing:
        rec = got.setdefault(u, {"launches": 0, "listed": 0, "stalled": 0})
        now = len(fast_map.listed(reg, u, read_only=True))
        if rec["launches"] and now <= rec["listed"]:
            rec["stalled"] += 1
        rec["listed"] = max(rec["listed"], now)
        if rec["stalled"] > cap:
            stuck.append(u)
        else:
            rec["launches"] += 1
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(got, indent=1), encoding="utf-8")
    return stuck


def _fast_read(reg, flow, sub):
    """The mapping agent still owed (fast read), or None when every unit of the plan is written by a writer that is
    not refused."""
    import fast_map
    held = _fast_set_aside(reg, sub)
    if held and held.get("kind") == "code":
        return held
    if not (reg / fast_map.FOLDER / fast_map.GROUPS).is_file():
        got = fast_map.plan(reg, flow, judges.workspace(reg))
        case.log(reg, "ran fast_map plan", **got)
    owed = sorted({r["unit"] for r in fast_map.rows(reg / fast_map.FOLDER / fast_map.PLAN)})
    missing = fast_map.unfinished(reg)
    if not missing:
        return None
    import go
    absent = go.fast_agent_problem(reg)
    if absent:
        said = f"REFUSED: {absent}. Nothing was launched."
        case.log(reg, "fast read held", said=said)
        return {"kind": "code", "sub": sub, "ok": False, "said": said}
    stuck = _fast_stalled(reg, missing)
    if stuck:
        said = (f"REFUSED: the mapping agents made no progress on {', '.join(stuck)} after being launched again as "
                "many times as run-settings.json relaunches allows: its tables list no more files than before. "
                "Nothing was launched. Look at the unit's status note in fast/mappers/ for why.")
        case.log(reg, "fast read held", said=said)
        return {"kind": "code", "sub": sub, "ok": False, "said": said}
    # one mapping agent per service, or per share of one; a relaunch names only the units still owed
    launch = fast_map.write_prompt(reg, flow, judges.workspace(reg),
                                   only=set(missing) if len(missing) < len(owed) else None)
    import settings
    at_once = int(settings.load(reg).get("parallel") or 6)
    agents = [{"name": g, "agent_type": fast_map.AGENT, "units": us,
               "prompt": f"Read {p.as_posix()} and do exactly what it says. Reply with one line."}
              for g, p, us in launch]
    return {"kind": "agent", "sub": sub, "agent_type": fast_map.AGENT, "agents": agents, "units": missing,
            "then": f"launch every agent listed, each with the Agent tool, subagent_type {fast_map.AGENT}, with its "
                    f"prompt as its whole prompt, all in one message (at most {at_once} at once; launch the rest as "
                    "each returns), wait for every reply, then call this again"}


def _step(reg, flow, sub):
    """The action this sub-state still owes, or None when it is done."""
    reg = pathlib.Path(reg)
    if sub == "lead steps":
        found = _check_lead(reg, flow) + _lead_duplicates(reg)
        task = ("Steps 1 to 4 of the mapping steps: the case, its lifecycle, the stages and the process steps, and the "
                "lead's own parts")
        if fast(reg):
            task += ("; in the fast map a surveyed service is never your own part: name it by its service name in "
                     "the lifecycle's carried_by and needs, with no subjects.csv row or id (each mapping agent writes "
                     "its service's row)")
        if _by_stage(reg):
            task += ("; and a subjects.csv row, with its part_kind (method/part-kinds.csv) and level, for each part a "
                     "move names that is not a surveyed service: a store, a broker, an external dependency, a person. "
                     "The pick reads every service the go took in while a part on a picked stage is neither a surveyed "
                     "service nor recorded as such a kind")
        return _judgment(sub, task, LEAD_WRITE, LEAD_RULES, found) if found else None
    if sub == "impact":
        found = _check_impact(reg, flow)
        return _judgment(sub, "Step 10 of the mapping steps: Business Impact for every stage, from the lifecycle's "
                         "if_not and recovery, before the pick of how far each stage goes", IMPACT_WRITE, ["impact"],
                         found) if found else None
    if sub == "pick":
        return None
    if sub == "sweep":
        return None  # decided in _decide: newly reached services send the run back to the readers
    if sub == "fast read":
        return _fast_read(reg, flow, sub)
    if sub == "fast check":
        import fast_map
        refused = _fast_set_aside(reg, sub)
        if refused:  # a refused mapping agent: its units are launched again, never handed to the person to relaunch
            return refused if refused.get("kind") == "code" else _fast_read(reg, flow, "fast read")
        found, _ = fast_map.check(reg, flow, judges.workspace(reg))
        return _judgment(sub, "Put right what the fast map's rule check found: a cited range that does not exist, in "
                         "the unit row or your own row it names; or, for a unit the mapping agent did not write, launch "
                         "it again (fast read)", LEAD_WRITE + ["units/<unit>/ (the row named only)"],
                         ["fast_map.py check"], found) if found else None
    if sub == "fast draw":
        import fast_map
        a = _code(reg, sub, ["fast_map.py", "draw", str(reg), flow], lambda: (reg / fast_map.PAGE).is_file())
        if a:
            return a
        refused = fast_map.register_refusals(reg)
        if refused:  # rows only a mapping agent may write: set its units aside and launch it again with the reason
            owed, stuck, why = fast_map.set_aside_bad_ids(reg, refused)
            if stuck:
                said = (f"REFUSED: the mapping agent's rows for {', '.join(stuck)} were refused again by the map's "
                        f"check after it was launched once more: {'; '.join(why)}. Nothing was launched.")
                case.log(reg, "fast draw held", said=said)
                return {"kind": "code", "sub": sub, "ok": False, "said": said}
            case.log(reg, "set aside units the map's check refused", units=owed)
            return _fast_read(reg, flow, "fast read")
        return (_code(reg, sub, ["capability_views.py", str(reg), "--check"])
                or _code(reg, sub, ["one_canvas.py", str(reg), str(reg / "views.html")]))
    if sub == "units":
        _record_reading(reg)
        if (reg / layout.UNITS_CSV).is_file():
            return None
        return _code(reg, sub, ["units.py", str(reg)], lambda: (reg / layout.UNITS_CSV).is_file())
    if sub == "readers":
        owed, _ = readers.in_scope(reg)
        if not owed:
            return _fanout(reg, flow, sub, "reader", 1, [], [])
        held = _readers_held(reg, owed)
        if held:  # the checks a direct call makes hold here too: run control never launches past them
            case.log(reg, "readers held", said=held)
            return {"kind": "code", "sub": sub, "ok": False, "said": f"REFUSED: {held}. Nothing was launched."}
        return _fanout(reg, flow, sub, "reader", 1, owed, readers.emit(reg, owed, "read"),
                       lambda: _lost(reg, sub))
    if sub == "merge":
        return _code(reg, sub, ["merge.py", str(reg)]) or _redraw_stale(reg, flow, sub)
    if sub == "re-reads":
        if not _unmatched(reg):
            return None
        a = _fanout(reg, flow, sub, "re-read", 1, sorted({c["call"].split("/", 1)[0] for c in _unmatched(reg)}),
                    readers.emit(reg, [], "reread"))
        return a or _code(reg, sub, ["merge.py", str(reg)])
    if sub == "lead rows" and fast(reg):
        found = (_check_lead_rows(reg, flow) + _lead_duplicates(reg) + _fast_questions_owed(reg, flow)
                 + _needs_from_calls(reg, flow))
        task = ("After the fast map's merge: Steps 7, 8 and 10 (the parts set aside, the AI agents, the capability and "
                "Business Impact) and the case as a part; your own part rows are the case, the people who act and "
                "parts no service holds, never a service the mapping agent maps (remove any such row and use the "
                "mapping agent's). Then answer or gap every view question listed: a part's operations or what it "
                "depends on, answered from the mapping agent's rows where it read the part; gapped in "
                "measure-gaps.csv, kind 'not read', why "
                f"'{NOT_READ_WHY}', only for a part no step of a stage taken further involves or an external "
                "dependency seen only by its calls (the done check allows 'not read' for those alone); the flow's "
                "delivers and a stage's cannot-be-undone answered from the "
                "lifecycle and the map. You wrote the lifecycle before the mapping agents found the calls: for each "
                "call listed whose step's moves do not name its callee, add the callee to that move's needs in "
                "lifecycle.csv, or correct the call's step_hint. A row added to the parts after the merge goes in "
                "merge/lead-rows/; merge again")
        return _judgment(sub, task, LEAD_ROWS_WRITE, ["impact", "parts"], found) if found else None
    if sub == "lead rows":
        found = _check_lead_rows(reg, flow)
        task = ("Steps 7, 8 and 10: the parts set aside, the AI agents, the capability and Business Impact; a row "
                "added to the parts after the merge goes in merge/lead-rows/")
        if _by_stage(reg):
            task += ("; and each part a move names whose service no reader read (go.stage_reading: no stage taken "
                     "further reaches it; a part of a stage taken further is always read): "
                     "its row in merge/lead-rows/subjects.csv (level, band, part_kind, repository and purpose, cited to "
                     "what the first look read) and its performs or supports rows in merge/lead-rows/participation.csv "
                     "from the lifecycle's carried_by and needs, with no operation, and its subject_id in "
                     f"{PLACEHOLDERS} (columns subject_id and flow, this flow's id); then gap its 'part: operations' and "
                     f"'part: depends on' in measure-gaps.csv, kind 'not read', why '{NOT_READ_WHY}'; merge again")
        return _judgment(sub, task, LEAD_ROWS_WRITE, ["impact", "parts"], found) if found else None
    if sub in ("judge round 1", "judge round 2"):
        rnd = int(sub[-1])
        units = judges._units(reg) if rnd == 1 else _flagged_units(reg)
        held = _judges_held(reg, units, rnd)
        if held:  # the checks a direct judges.py emit makes hold here too
            case.log(reg, "judges held", said=held)
            return {"kind": "code", "sub": sub, "ok": False, "said": f"REFUSED: {held}. Nothing was launched."}
        lines = []
        for u in units:
            lines += judges.emit(reg, u, rnd, "flagged" if rnd == 2 else None)
        a = _fanout(reg, flow, sub, "judge", rnd, units, lines, lambda: _lost(reg, sub))
        if a is None:
            judges.collect(reg)
            case.log(reg, f"collected round {rnd}")
        return a
    if sub == "fixers":
        units = _flagged_units(reg)
        if not units:
            return None
        a = _fanout(reg, flow, sub, "fixer", 1, units, readers.emit(reg, units, "fix"))
        return a or _code(reg, sub, ["merge.py", str(reg)])
    if sub == "draw":
        return (_code(reg, sub, ["capability_views.py", str(reg), "--check"])
                or _code(reg, sub, ["one_canvas.py", str(reg), str(reg / "views.html")]))
    if sub == "check":
        found = _owed(reg, flow)
        return _judgment(sub, "Answer in the register, or write its gap with the reason, each question the end of "
                         "mapping still owes; a reason only a unit's rows can clear goes to that unit's fixer "
                         "(readers.py prompt ... --mode stop)", ["the lead's own tables"], ["run_status --mapping",
                                                                                            "check_map"],
                         found) if found else None
    if sub == "mapping ends":
        code, out = _run(["go.py", str(reg), "--mapping-ends", flow])
        case.log(reg, "ran go.py --mapping-ends", code=code, said=out[-400:])
        if code != 0:
            return _judgment(sub, "Put right what ending the flow refused, then hand back", ["the lead's own tables"],
                             ["go.py --mapping-ends"], [out])
        return None
    raise ValueError(sub)


def _skip(reg, flow, sub, by_kit=False):
    """A sub-state with nothing to do on this run: round 2 and the fixers when round 1 flagged nothing; ending the
    flow when the stage kit runs a full mapping (the kit takes the flow on to its measures, and ending it would count
    it finished). A fast map goes on to the measures under the kit like a full one when a stage was taken past mapped
    only; with every stage mapped only it has no step after the map, so run control ends it then."""
    if sub == "mapping ends":
        return by_kit and (not fast(reg) or _further(reg))
    return sub in ("fixers", "judge round 2") and not _flagged_units(reg)


def _inspection(reg, flow):
    import check_map
    return check_map.counted(reg, flow, check_map.open_items(reg, flow))


def _further(reg):
    """The stages the person took past mapped only, in the flow worked now's pick."""
    import go
    return sorted(sid for sid, d in ((go.load(reg) or {}).get("depth") or {}).items() if d not in ("none", "", None))


def _map_stop(reg, flow, ended, by_kit=False):
    """The map stop, rendered through brief.py say, which puts the status line and the page's address around it and
    refuses ids and kit words; a refusal is handed back, never sent."""
    import map_record as mr
    if fast(reg) and not ended:
        import fast_map
        text = ("The fast map is drawn: " + fast_map.summary(reg, flow) + ". " + fast_map.NOT_DONE)
        folder = pathlib.Path(reg) / MESSAGES
        folder.mkdir(exist_ok=True)
        f = folder / f"map-stop-{flow}.md"
        f.write_text(text, encoding="utf-8")
        code, out = _run(["brief.py", "say", str(reg), str(f)])
        if code != 0:
            return {"kind": "code", "sub": "map stop", "ok": False,
                    "command": ["python", "brief.py", "say", str(reg), str(f)], "said": out}
        if by_kit and _further(reg):
            return {"kind": "stop", "stop": "map", "message": out, "records_with": "next.py --event chat",
                    "then": ("back to the stage kit's SKILL.md: the measures for the stages taken further ("
                             + ", ".join(_further(reg)) + "), drafted from the fast map's rows; then selective.py "
                             "check before the measures review, which then shows each measure's rows as checked, "
                             "flagged or not checked")}
        return {"kind": "stop", "stop": "map", "message": out, "records_with": "next.py --event chat",
                "then": ("the flow is finished: this message is its report. Then, with flows left, the stage kit's "
                         "SKILL.md 'Then the next flow' (brief.py next --after, sent at the end of this message), "
                         "and go.py --report-sent once it is sent" if by_kit else
                         "the fast map is handed over: every stage was left mapped only")}
    if flow not in {f["flow_id"] for f in mr.load(reg)["flows"]}:
        text = "Mapping stopped before the flow's own rows were written, so there is no map yet and nothing to inspect."
    else:
        first = ("The map is drawn as it stands and is not checked against the code: you stopped the checks, so what "
                 "was not yet checked is shown as not checked." if ended else "The map is drawn.")
        text = first + "\n\n" + _inspection(reg, flow)
    folder = pathlib.Path(reg) / MESSAGES
    folder.mkdir(exist_ok=True)
    f = folder / f"map-stop-{flow}.md"
    f.write_text(text, encoding="utf-8")
    code, out = _run(["brief.py", "say", str(reg), str(f)])
    if code != 0:
        return {"kind": "code", "sub": "map stop", "ok": False,
                "command": ["python", "brief.py", "say", str(reg), str(f)], "said": out}
    a = {"kind": "stop", "stop": "map", "message": out, "records_with": "next.py --event chat"}
    if by_kit:
        a["then"] = "back to the stage kit's SKILL.md for the pick of how far each stage goes"
    return a


def _kit(reg, by_kit):
    """Whether the stage kit runs this mapping: the flag, recorded on the go the first time it is given, or the
    record the go already holds; so a later call that leaves --by-kit off still stops for the person's pick."""
    import go
    s = go.load(reg)
    if by_kit and s and not s.get(go.KIT):
        s[go.KIT] = guard.STAGE_KIT
        go.save(reg, s)
    return by_kit or guard.run_by_kit(reg, s)


def decide(reg, flow, event=None, by_kit=False, test=False):
    reg = pathlib.Path(reg)
    try:
        refusal = _lock_refusal(reg)
        if refusal:
            return {"kind": "stop", "stop": "held", "message": refusal, "records_with": "start.py --release"}
        by_kit = _kit(reg, by_kit)
        return _decide(reg, flow, event, by_kit, test)
    finally:
        _timings(reg, event[0] if event else "")


def _timings(reg, why=""):
    """Rewrite job/timings.csv (timings.refresh) on every call, whatever it decides: a launch, a launcher's reply, a
    wait, and every stop (mapping ends, the person's stop, agents lost), so the run's timing record is current while a
    step runs and holds when the run stops or crashes. It never changes the action: a failure to write it is logged to
    events.log, never raised, and nothing is printed (this script's output is the action)."""
    try:
        import timings
        timings.refresh(reg, why=f"next.py {why}".strip())
    except Exception:  # noqa: BLE001  (an import failure: the record is for evaluation; run control goes on)
        try:
            case.log(reg, "timings.csv not written", said="timings.py could not be loaded")
        except Exception:  # noqa: BLE001
            pass


def _decide(reg, flow, event, by_kit, test):
    f = case.flow(reg, flow)
    if event:
        kind, payload = event
        case.log(reg, f"event {kind}", payload=payload)
        if kind == "stop":
            case.decide(reg, "redirect", f"mapping {flow}, at {f.get('sub') or 'the start'}", payload, "chat", test=test)
            put_back = case.restore_open(reg, "stopped at the person's word")
            case.set_flow(reg, flow, state=ENDED)
            case.draw_run_md(reg)
            a = _map_stop(reg, flow, True, by_kit)
            a["put_back"] = put_back
            return a
        if kind == "retry":
            _retry(reg, f.get("sub") or "")
        if kind == "chat":
            return _judgment(f.get("sub"), "Read the person's words: a topic to talk about, a redirect, a stop, or an answer "
                             "to the open question. Say back your reading in one line before anything that discards "
                             "work; for a stop call this again with --event stop and their words",
                             [], ["say back first"], [payload])
    if f.get("state") == "mapped" and by_kit and not fast(reg) and _by_stage(reg) and readers.in_scope(reg)[0]:
        # a stage taken further after its flow was mapped: its services are read, merged and judged before its measures
        case.set_flow(reg, flow, state="mapping", sub="units")
        case.log(reg, "a stage taken further: reading its services", owed=readers.in_scope(reg)[0])
        f = case.flow(reg, flow)
    if f.get("state") in (ENDED, "mapped"):
        return _map_stop(reg, flow, f.get("state") == ENDED, by_kit)
    steps = order(reg)
    sub = f.get("sub") if f.get("sub") in steps else steps[0]
    for s in steps[steps.index(sub):]:
        if s != f.get("sub"):
            case.set_flow(reg, flow, state="mapping", sub=s)
            f = case.flow(reg, flow)
        if _skip(reg, flow, s, by_kit):
            continue
        if s == "pick" and _pick_owed(reg, by_kit):
            case.draw_run_md(reg)
            return _pick_stop(reg, flow)
        if s == "sweep" and _sweep(reg):
            case.set_flow(reg, flow, state="mapping", sub="units")
            return _decide(reg, flow, None, by_kit, test)
        a = _step(reg, flow, s)
        if a is not None:
            case.draw_run_md(reg)
            return a
    case.set_flow(reg, flow, state="mapped", sub="")
    case.draw_run_md(reg)
    return _map_stop(reg, flow, False, by_kit)


def main(argv):
    by_kit = "--by-kit" in argv
    test = "--test" in argv  # a test standing in for the person: its answers are kept as a test's
    argv = [a for a in argv if a not in ("--by-kit", "--test")]
    if len(argv) < 2:
        print(__doc__)
        return 2
    event = None
    if "--event" in argv:
        i = argv.index("--event")
        event = (argv[i + 1], argv[i + 2] if len(argv) > i + 2 else "")
        argv = argv[:i]
    print(json.dumps(decide(argv[0], argv[1], event, by_kit, test), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
