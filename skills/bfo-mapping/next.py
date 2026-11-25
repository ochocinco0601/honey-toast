"""Run control for mapping one flow: decide the next action from the case record and the files on disk.

Usage: python next.py <register folder> <flow id> [--by-kit] [--test] [--event stop "<the person's words>" | --event launcher-done <file>
                                                     | --event chat "<the person's words>"
                                                     | --event retry "<the person's words>"
                                                     | --event leave-unread|correct "<the person's words>"
                                                     | --event choices]

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
import os
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
    # brief.py's advice is for the session writing a message, never part of what the person is sent
    err = "".join(x for x in p.stderr.splitlines(True) if not x.startswith(ADVICE_LEAD))
    return p.returncode, (p.stdout + err).strip()


ADVICE_LEAD = "ADVICE, for you and not the person"  # brief.ADVICE's opening words


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


IDENTITY_STATE = "identity/judging.json"  # {"judged": [ids and workloads applied], "listed": [...], "launches": n}


def _read_identity(reg):
    """What each deployable is called, read once from its deployment and configuration files (identity.py) before any
    reader or mapping agent, so the merge folds by it and writes the root identifiers.csv."""
    import identity
    if (reg / identity.DIR / "identifiers.csv").is_file():
        return
    rows, unmatched = identity.write(reg, judges.workspace(reg))
    case.log(reg, "read identity", identifiers=len(rows), unmatched=len(unmatched))


def _identity_judged(reg, flow, sub):
    """After the merge: the parts no identity rule placed, judged as a draft by ONE general-purpose agent, on the
    prompt upgrade_identity.judge_prompt wrote. Its done mark (written last) is its finish: then the merge runs again,
    which applies its identity/merges.csv and judged identifiers. No mark, not done: it is handed over again."""
    import upgrade_identity as ui
    if not (reg / "identity" / "identifiers.csv").is_file():
        return None
    p = reg / IDENTITY_STATE
    try:
        st = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    judged = set(st.get("judged") or [])
    mark = reg / ui.JUDGED_DONE
    if st.get("listed") and mark.is_file():
        judged |= set(st["listed"])
        mark.unlink()
        p.write_text(json.dumps({"judged": sorted(judged), "listed": [], "launches": 0}), encoding="utf-8")
        case.log(reg, "applying the identity judgments", cases=st["listed"])
        failed = _code(reg, sub, ["merge.py", str(reg)])
        if failed:
            return failed
    cands, unmatched = ui.cases(reg)
    new = sorted(({r["subject_id"] for r in cands} | {w.get("workload") or "" for w in unmatched}) - judged - {""})
    if not new:
        return None
    launches = int(st.get("launches") or 0) + 1 if st.get("listed") else 1
    import settings
    if launches > int(settings.load(reg).get("relaunches") or 2) + 1:
        # never a loop the person cannot see: the judgments are a draft, so the run goes on with these parts apart
        p.write_text(json.dumps({"judged": sorted(judged | set(new)), "listed": [], "launches": 0,
                                 "unjudged": sorted(set(st.get("unjudged") or []) | set(new))}), encoding="utf-8")
        case.log(reg, "identity judging agent wrote no done mark; going on without its judgments, the parts kept apart",
                 cases=new, launches=launches - 1)
        return None
    ui.judge_prompt(reg, only=set(new), mark=True, workspace=judges.workspace(reg))
    p.write_text(json.dumps({"judged": sorted(judged), "listed": new, "launches": launches}), encoding="utf-8")
    case.log(reg, "identity judging agent handed over", cases=new, launches=launches)
    prompt = (f"Read {(reg / ui.JUDGE_PROMPT).resolve().as_posix()} and do exactly what it says. "
              "Reply with one line.")
    return {"kind": "agent", "sub": sub, "agent_type": "general-purpose", "units": [],
            "agents": [{"name": "identity-judge", "agent_type": "general-purpose", "units": [], "prompt": prompt}],
            "at_once": 1, "launches": launches,
            "then": "launch the one agent listed with the Agent tool, subagent_type general-purpose, with its prompt "
                    "as its whole prompt; wait for its reply, then call this again: run control applies its judgments "
                    f"once it has written {ui.JUDGED_DONE}, and hands it over again until it has"
                    + (f" (handed over {launches} times so far)" if launches > 1 else "")}


def _lead_duplicates(reg):
    """In a fast run, the lead's own part rows (subjects.csv) that name a service the mapping agent maps (a deployable
    of units.csv): the merged map would hold it twice. Nothing in a full run, whose lead rows are checked otherwise."""
    if not fast(reg):
        return []
    import fast_map
    import register_layout as layout
    units = _rows(reg / layout.UNITS_CSV)
    planned = {(r.get("unit") or "").strip() for r in _rows(reg / fast_map.FOLDER / fast_map.PLAN)}
    survey = _rows(reg / "survey.csv")
    if planned:  # only the services the fast map reads: one it does not read (a stage left mapped only) is the lead's
        read = [r for r in units if (r.get("unit") or "").strip() in planned]
        mapped = {(r.get(k) or "").strip().lower() for r in read for k in ("unit", "deployable")}
        paths = {p.strip().strip("/").lower() for r in read for p in (r.get("paths") or "").split(";") if p.strip()}
        mapped |= {(r.get("service") or "").strip().lower() for r in survey  # the same service by its survey name
                   if (r.get("path") or "").strip().strip("/").lower() in paths}
    else:
        mapped = {(r.get("deployable") or "").strip().lower() for r in units}
        mapped |= {(r.get("service") or "").strip().lower() for r in survey}
    import go
    keys = {go._name_key(m) for m in mapped} - {""}  # letters and digits only: `Orders`, `orders-1`, `orders_1` alike

    def maps(r):
        return go._name_key(r.get("name") or "") in keys
    # once merged, the root holds the mapping agents' own service rows; the lead's rows are the merge's input
    lead = reg / layout.LEAD_ROWS / "subjects.csv"
    where = "merge/lead-rows/subjects.csv" if lead.is_file() else "subjects.csv"
    return [f"{where} {r.get('subject_id', '').strip()} names the service '{r.get('name', '').strip()}', which "
            "the mapping agent maps: remove it, and name the service by its name in the lifecycle (the mapping "
            "agent writes its row)" for r in _rows(lead if lead.is_file() else reg / "subjects.csv") if maps(r)]


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
    elif sub == "merge":  # a reader relaunched with the merge's reason
        out = [(u, layout.prompts_dir(reg, u) / readers.MERGE_FIX) for u in judges._units(reg)
               if (layout.prompts_dir(reg, u) / readers.MERGE_FIX).is_file()]
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


FORM_REFUSED = "REFUSED: a question in the message is not in the question form"  # brief.py say's card-form refusal


def _say_kit(reg, f):
    """The kit's own message, sent once say has refused it and the refusal is written down as a kit finding: say
    --kit takes it, every refusal of its text printed as advice, which _run leaves out. (code, printed)."""
    return _run(["brief.py", "say", "--kit", str(reg), str(f)])


def _kit_defect(reg, template, fn, out):
    """A message the kit wrote refused by its own word check or its question-form check is a kit defect: written down
    as kit facts only (the template and the line that builds its text, never what was refused). Any other failure of
    `say` is not: None. Called from the stop function itself, whose line it names."""
    import brief
    import inspect
    import kit_findings
    if not out.startswith((brief.WORDS_REFUSED, FORM_REFUSED)):
        return None
    call = sys._getframe(1).f_lineno
    src, first = inspect.getsourcelines(fn)
    built = max((first + i for i, x in enumerate(src) if x.strip().startswith("text = ") and first + i < call),
                default=call)
    p, _ = kit_findings.record(reg, f"say-refused-{template}", "next.py", built)
    return f"written down in {p}: a problem in the kit itself; never change the kit's files" if p else None


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
    finding = None
    if code != 0:  # the kit's own message: its refusal is a kit finding, and the message goes out with advice
        finding = _kit_defect(reg, "agents-lost", _lost_stop, out)
        code, out = _say_kit(reg, f)
    case.log(reg, "agents lost", sub=sub, prompts=[pathlib.Path(p).as_posix() for _, p, _ in gone], states=sorted(
        str(x) for x in states))
    if code != 0:
        return {"kind": "code", "sub": sub, "ok": False, "command": ["python", "brief.py", "say", str(reg), str(f)],
                "said": out, "kit_finding": finding}
    a = {"kind": "stop", "stop": "agents lost", "sub": sub, "message": out, "said": lines,
         "records_with": "next.py --event retry \"<their words>\" on their word to try again; else "
                         "next.py --event chat"}
    if finding:
        a["kit_finding"] = finding
    return a


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
        if state == "ran a shell" and sub in ("readers", "merge"):
            import provenance
            provenance.undo_breaches(reg, u)
        if sub == "merge" and state == "finished":  # still refused after its one relaunch: not reset by a try again
            continue
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


def _fast_set_aside(reg, flow, sub):
    """None when no mapping agent's rows are refused. Else the person's choices (_stuck) when a unit was refused again
    after its relaunch, or {"kind": "set aside", "units"} when run control set the refused writers' tables aside
    (fast_map.set_aside_refused) so the mapping agent is launched again for those units."""
    import fast_map
    checked = _correction_checked(reg, flow, sub)
    if checked:
        return checked
    owed, stuck, why = fast_map.set_aside_refused(reg)
    o2, s2, w2 = fast_map.set_aside_bad_ids(reg)  # row ids that break the unit format: written again before the merge
    writer = bool(stuck)  # a writer refused for who it is: no correction of the rows makes its work count
    # changed outside the kit, or not this flow's to write again: not a row the lead's correction can put right
    outside = any(fast_map.OUTSIDE_MARK in w or "is not read in this flow" in w for w in w2)
    owed, stuck, why = sorted(set(owed) | set(o2)), sorted(set(stuck) | set(s2)), why + w2
    if stuck:
        said = (f"REFUSED: the mapping agent's rows for {', '.join(stuck)} were refused again after it was launched "
                f"once more: {'; '.join(why)}. Nothing was launched.")
        case.log(reg, "fast read held", said=said)
        return _stuck(reg, flow, sub, stuck, "writer" if writer else "outside" if outside else "rows", said, why)
    if owed:
        case.log(reg, "set aside a refused mapping agent's rows", units=owed)
        return {"kind": "set aside", "units": owed}
    return None


def _merge_stale(reg):
    """Whether the merged root tables are no longer what a merge of the unit folders gives now."""
    import merge
    return any("not what a merge" in p for p in merge.check(reg)[1])


def _drawn_map_wrong(reg, flow):
    """[why the fast map of the flow worked now, which run control counts as drawn, does not hold]: a unit owed again,
    a merge older than the units, or the map's own check (capability_views.py --check) failing. Empty when it holds,
    and for a flow finished before the one worked now (a later flow's units change the merge by design)."""
    import capability_views as cv
    import fast_map
    import go
    cur = go.load(reg) or {}
    if (go.flow_id_of(reg, cur) or cur.get("flow", "")) != flow or not (pathlib.Path(reg) / "subjects.csv").is_file():
        return []
    import merge
    wrong = [f"a unit is owed again: {u}" for u in fast_map.unfinished(reg)]
    wrong += [p for p in merge.check(reg)[1] if "not what a merge" in p]
    return wrong or [e for e in cv.check(cv.load(reg))[0] if e.startswith(("subjects.csv", "participation.csv"))]


def _back_to_fast_read(reg, flow):
    """Units set aside after the merge: the run steps back to the fast read, so their rewrite is merged and checked
    afresh before the drawing, never judged again on the merge of the rows set aside."""
    case.set_flow(reg, flow, state="mapping", sub="fast read")
    return _fast_read(reg, flow, "fast read")


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
    aside = {}
    for r in fast_map.set_aside(reg):
        for u in r.get("units") or []:
            aside[u] = aside.get(u, 0) + 1
    for u in missing:
        rec = got.setdefault(u, {"launches": 0, "listed": 0, "stalled": 0})
        now = len(fast_map.listed(reg, u, read_only=True))
        if aside.get(u, 0) > rec.get("aside", 0):  # its tables were set aside for a relaunch: not a launch in vain
            rec["aside"], rec["listed"] = aside[u], 0
        elif rec["launches"] and now <= rec["listed"]:
            rec["stalled"] += 1
        rec["listed"] = max(rec["listed"], now)
        if rec["stalled"] > cap:
            stuck.append(u)
        else:
            rec["launches"] += 1
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(got, indent=1), encoding="utf-8")
    return stuck


VALUE_WORDS = {"part_kind": "kind of part", "carries_case_id": "answer to whether it carries the case's id"}
STUCK = "stuck"  # in a flow's case record: {"units", "kind", "shown"}, the choices put to the person
CORRECTING = "correcting"  # in a flow's case record: {"units", "kind", "shown"}, the person chose the lead's correction
CAUSE = {
    "rows": "the agent mapping it wrote findings the map's rules refuse, and did the same again after it was sent "
            "back once with the reason",
    "writer": "the agent that mapped it is not one whose work the map can count (it used a tool it is not allowed, or "
              "is not the kit's mapping agent), and the same happened again after it was sent back once",
    "stalled": "the agent mapping it made no progress, each time it was sent back",
    "outside": "its findings were changed after its mapping agent wrote them, by something other than the kit (a "
               "script or a hand edit), so they cannot be counted, and that happened again after it was written once "
               "more",
}


def _stalled_resettable(reg, units):
    import fast_map
    p = pathlib.Path(reg) / fast_map.FOLDER / FAST_LAUNCHES
    got = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    return [u for u in units if (got.get(u) or {}).get("resets", 0) < fast_map.MAX_RESETS]


def _reset_stalled(reg, units):
    """The person's "try again" on units held by the stall cap: each one's count of launches without progress starts
    again (once, fast_map.MAX_RESETS), so its mapping agent is launched again."""
    import fast_map
    p = pathlib.Path(reg) / fast_map.FOLDER / FAST_LAUNCHES
    got = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    done = []
    for u in _stalled_resettable(reg, units):
        rec = got.setdefault(u, {"launches": 0, "listed": 0, "stalled": 0})
        rec["stalled"] = 0
        rec["resets"] = rec.get("resets", 0) + 1
        done.append(u)
    if done:
        p.write_text(json.dumps(got, indent=1), encoding="utf-8")
    return done


def _stuck(reg, flow, sub, units, kind, said, why):
    """A mapping agent stuck after its relaunch: the lead's correction task when the person chose it,
    else a stop that puts numbered choices to the person in plain words, each saying what happens next. They answer
    with the number or in their own words; nothing they must remember. Every set of choices has a way on."""
    import fast_map
    f = case.flow(reg, flow)
    chose = f.get(CORRECTING) or {}
    if kind == "rows" and chose and set(units) <= set(chose.get("units") or []):
        told = (f"The person said: '{chose['words']}'; where their words name a value, write that value. "
                if (chose.get("words") or "").strip() else "")
        return _judgment(sub, told + "The person chose that you correct these rows yourself. Put right each problem "
                         "named below, changing only the rows it names, so the rows meet the unit rules, each change with "
                         "`python <skill>/fast_map.py fix <register> <unit> <table> <row_id> <column> \"<value>\"` "
                         "(or `--remove` in place of the column and value; `--row \"<the whole row as one CSV line>\"` "
                         "for a row that does not parse, each cell that holds a comma in double quotes; `--nth 2` for "
                         "a second row with the same id), never with Write, Edit or a script: a unit changed any other way is set aside and "
                         "written again by its mapping agent. Then call this again. If you cannot put them right, "
                         "call this again with --event choices, which puts the choices to the person again",
                         [f"units/{u}/ (the rows named only, through fast_map.py fix)" for u in units],
                         ["fast_map.py check"], why)
    retry = (_stalled_resettable(reg, units) if kind == "stalled" else fast_map.can_reset(reg, units))
    retry = retry and set(units) <= fast_map.planned(reg)  # only a unit of this flow's plan has an agent to send
    who = _names(reg, units)
    import question_card as qc
    choices = []  # (event, verb, what happens): each choice names who acts
    named = []
    if kind == "rows" and _correctable(reg, units, why):
        values = [m for u in units for m in fast_map.value_misses(reg, u)]
        choices.append(("correct", "Tell me, or let me fix them", "you give the right value, or I correct only what "
                        "the map's check names; mapping goes on once they pass") if values else
                       ("correct", "Let me fix them", "I correct only what the map's check names; mapping goes on "
                        "once they pass"))
        named = list(dict.fromkeys((VALUE_WORDS.get(c, c.replace('_', ' ')), v, ", ".join(allowed))
                                   for u in units for _, _, c, v, allowed in fast_map.value_misses(reg, u)))
    if retry:
        told = "" if kind == "stalled" else ", told what was wrong"
        choices.append(("retry", "Retry", f"I send the mapping agent once more{told}; if it is stuck again, you get "
                                          "these choices without this one"))
    choices.append(("leave-unread", "Skip it", f"the map shows {who} as not read, with your words; its steps get no "
                                               "measures or alerts"))
    choices.append(("stop", "Stop mapping", "what is mapped so far is kept"))

    def card(with_values=True):
        return qc.card(
            title=f"Mapping {who} is stuck: how shall I go on?",
            fields=[("Cause", CAUSE[kind])],
            table=(("What was written", "Value", "Allowed"), named) if with_values and named else None,
            after=[("Affects", f"the part of the map {who} carries")],
            why="the map cannot count those findings as they are",
            choices=[(verb, what) for _, verb, what in choices],
            recommended=(1, {"correct": "it changes only what the check names", "retry": "it costs one more try"}
                         .get(choices[0][0], "the rest of the map goes on")))
    lines = card().splitlines()
    text = "\n".join(lines)
    folder = pathlib.Path(reg) / MESSAGES
    folder.mkdir(exist_ok=True)
    msg = folder / f"mapping-held-{sub.replace(' ', '-')}.md"
    msg.write_text(text, encoding="utf-8")
    code, out = _run(["brief.py", "say", str(reg), str(msg), "--kit"])
    if code != 0 and kind == "rows" and named:  # the value lines name the kit's columns: the choices alone
        text = card(with_values=False)
        msg.write_text(text, encoding="utf-8")
        code, out = _run(["brief.py", "say", str(reg), str(msg)])
    finding = None
    if code != 0:  # a message of the kit's that say refuses is a kit defect, written down; it goes out with advice
        finding = _kit_defect(reg, "mapping-held", _stuck, out)
        code, out = _say_kit(reg, msg)
    if code != 0:
        return {"kind": "code", "sub": sub, "ok": False, "command": ["python", "brief.py", "say", str(reg), str(msg)],
                "said": out, "kit_finding": finding}
    shown = out
    case.set_flow(reg, flow, **{STUCK: {"units": list(units), "kind": kind, "shown": shown, "text": text,
                                        "choices": [ev for ev, _, _ in choices], "sub": sub, "said": said,
                                        "why": list(why)}, CORRECTING: {}})
    records = {str(i): f'next.py --event {ev} "<their words>"' for i, (ev, _, _) in enumerate(choices, 1)}
    return {"kind": "stop", "stop": "mapping held", "sub": sub, "message": shown, "said": said, "why": why,
            "units": list(units), "choices": [{"n": i, "event": ev, "label": f"{verb}: {what}"}
                                              for i, (ev, verb, what) in enumerate(choices, 1)],
            "records_with": ("send the message as printed; take their answer by its number or its words to one "
                             "choice and call " + "; ".join(f"{n} -> {c}" for n, c in records.items())
                             + "; an answer that fits none: ask again in plain words; never ask them for a command "
                             "or a set phrase")}


def _correctable(reg, units, why):
    """Whether the lead's correction can carry out what holds `units`: every problem the unit rules find in each names
    one of its rows (fast_map.py fix addresses a row by its id), and, where they find none (the map's check of the
    merged rows held it), the reasons given name a row of each. A choice the kit cannot carry out is never put."""
    import fast_map
    for u in units:
        found = fast_map.unit_problems(reg, u)
        if any(not _named_rows(u, [p]) for p in found):
            return False
        if not found and not _named_rows(u, why):
            return False
    return True


CORRECTION_COPY = "correcting"  #fast/correcting/<unit>/: the unit's tables as they were when the person chose
UNIT_FILES = ("subjects", "operations", "calls", "participation", "files")


def _named_rows(unit, why):
    """The row ids of `unit` the held step's problems name: the only rows the lead's correction may change."""
    import re
    return sorted(set(re.findall(rf"\b{re.escape(unit)}-[\w.-]*\w", " ".join(why))))


def _correction_breaches(reg, chose):
    """What the lead's correction changed beyond the rows named: a row not named that is changed or gone, or rows
    added or removed. Compared with the copy taken when the person chose the correction."""
    import fast_map
    reg = pathlib.Path(reg)
    out = []
    for u in chose.get("units") or []:
        named = set((chose.get("named") or {}).get(u) or [])
        for t in UNIT_FILES:
            old = fast_map.rows(reg / fast_map.FOLDER / CORRECTION_COPY / u / f"{t}.csv")
            new = [dict(r) for r in fast_map.rows(reg / "units" / u / f"{t}.csv")]
            free = sum((r.get("row_id") or "").strip() in named for r in old)
            for r in old:
                if (r.get("row_id") or "").strip() in named:
                    continue
                if r in new:
                    new.remove(r)
                else:
                    out.append(f"{u}'s {t} row {(r.get('row_id') or '').strip() or '(no id)'} was changed or "
                               "removed, and the check did not name it")
            if len(new) > free:  # a named row may be removed (fast_map.py fix --remove), never one added
                out.append(f"{u}'s {t} table has {len(new)} row(s) in place of the {free} the check named: rows were "
                           "added")
    return out


def _correction_checked(reg, flow, sub):
    """While the person's choice of the lead's correction is open: a refusal, as a task naming what to put back, when
    the correction changed more than the rows named; once the units' rows meet the unit rules again, the choice is
    closed (a later hold on them puts the choices to the person again). None otherwise."""
    import fast_map
    f = case.flow(reg, flow)
    chose = f.get(CORRECTING) or {}
    if not chose.get("units"):
        return None
    breaches = _correction_breaches(reg, chose)
    if breaches:
        case.log(reg, "the lead's correction changed rows not named", units=chose["units"], said=breaches)
        return _judgment(sub, "REFUSED: your correction changed rows the check did not name. Put each back exactly as "
                         f"it was (the copy is in {fast_map.FOLDER}/{CORRECTION_COPY}/<unit>/), keep only the "
                         "changes to the rows named, then call this again",
                         [f"units/{u}/ (the rows named only)" for u in chose["units"]], ["fast_map.py check"],
                         breaches)
    if chose.get("sub") == "fast draw":  # held by the map's check of the merged rows: closed at the drawing
        return None
    if not any(fast_map.unit_problems(reg, u) for u in chose["units"]):
        _correction_holds(reg, flow, chose)
    return None


def _correction_holds(reg, flow, chose):
    case.set_flow(reg, flow, **{CORRECTING: {}})
    case.log(reg, "the lead's correction holds", units=chose["units"])


ANSWER_EVENTS = {"retry": "try again", "leave-unread": "leave unread", "correct": "correct the rows"}


def _not_a_choice(reg, flow, held, line):
    """The held choices again, opened by one plain line saying why the answer was not taken."""
    folder = pathlib.Path(reg) / MESSAGES
    folder.mkdir(exist_ok=True)
    msg = folder / "mapping-held-again.md"
    msg.write_text(f"{line}\n\n{held.get('text') or ''}", encoding="utf-8")
    code, out = _run(["brief.py", "say", str(reg), str(msg)])
    if code != 0:  # the kit's own message: sent with its refusal as advice, never held
        code, out = _say_kit(reg, msg)
    return {"kind": "stop", "stop": "mapping held", "sub": held.get("sub") or "", "units": held.get("units") or [],
            "message": out if code == 0 else msg.read_text(encoding="utf-8"), "said": held.get("said") or "",
            "not taken": line,
            "choices": [{"n": i, "event": ev, "label": ""} for i, ev in enumerate(held.get("choices") or [], 1)],
            "records_with": "send the message as printed; take their answer to one choice and call next.py with that "
                            "choice's --event and their words; never ask them for a command or a set phrase"}


def _stuck_answer(reg, flow, kind, words, test):
    """The person's answer to the choices of a stuck mapping agent, checked against the choices put to them before
    anything is recorded: try again resets the units' counts once, leave unread records them as a gap with their words
    (and sends a register already merged back to the merge, so their rows are merged out), correct hands the named
    rows to the lead, choices puts them again. An answer that is not one of the choices returns them again, with one
    line saying why; nothing is recorded."""
    import fast_map
    f = case.flow(reg, flow)
    held = f.get(STUCK) or {}
    if kind == "choices":
        if f.get(CORRECTING):
            case.set_flow(reg, flow, **{STUCK: f[CORRECTING], CORRECTING: {}})
        return None
    if not held.get("units"):
        if kind == "retry":
            return None  # a try again at another stop (agents lost): not an answer to these choices
        return {"kind": "code", "sub": f.get("sub") or "", "ok": False,
                "said": "REFUSED: no choice is waiting on the person; call run control without --event."}
    if kind not in (held.get("choices") or []):
        why = ("Sending the agent once more was already used for this service, so that choice is not open now."
               if kind == "retry" else
               "Correcting the findings myself is not open here, because the agent's work cannot be counted, "
               "whatever is corrected." if kind == "correct" else "That answer is not one of the choices.")
        return _not_a_choice(reg, flow, held, why)
    units, why = held["units"], held.get("kind")
    case.decide(reg, "mapping held", held.get("shown") or "", words, "chat", test=test, choice=ANSWER_EVENTS[kind],
                units=units)
    if kind == "retry":
        done = _reset_stalled(reg, units) if why == "stalled" else fast_map.reset_set_aside(reg, units, words)
        case.log(reg, "the person's try again reset", units=done)
        case.set_flow(reg, flow, **{STUCK: {}, CORRECTING: {}})
    elif kind == "leave-unread":
        fast_map.leave_unread(reg, units, words)
        case.log(reg, "left unread on the person's word", units=units)
        steps = order(reg)
        now = f.get("sub") or ""
        if now in steps and "merge" in steps and steps.index(now) > steps.index("merge"):
            case.set_flow(reg, flow, **{STUCK: {}, CORRECTING: {}, "sub": "merge"})  # merged again, without them
        else:
            case.set_flow(reg, flow, **{STUCK: {}, CORRECTING: {}})
    elif kind == "correct":
        import shutil
        for u in units:
            dest = pathlib.Path(reg) / fast_map.FOLDER / CORRECTION_COPY / u
            if dest.exists():
                shutil.rmtree(dest)
            if (pathlib.Path(reg) / "units" / u).is_dir():
                shutil.copytree(pathlib.Path(reg) / "units" / u, dest)
        # the rows the reasons name, and every row the unit rules name now (the reasons given are cut to five)
        named = {u: sorted(set(_named_rows(u, held.get("why") or []))
                           | set(_named_rows(u, fast_map.unit_problems(reg, u)))) for u in units}
        case.set_flow(reg, flow, **{STUCK: {}, CORRECTING: dict(held, named=named, words=words)})
    return None


def _fast_read(reg, flow, sub):
    """The mapping agent still owed (fast read), or None when every unit of the plan is written by a writer that is
    not refused."""
    import fast_map
    held = _fast_set_aside(reg, flow, sub)
    if held and held.get("kind") != "set aside":
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
        return _stuck(reg, flow, sub, stuck, "stalled", said, [said])
    # one mapping agent per service, or per share of one; a relaunch names only the units still owed
    launch = fast_map.write_prompt(reg, flow, judges.workspace(reg),
                                   only=set(missing) if len(missing) < len(owed) else None)
    agents = [{"name": g, "agent_type": fast_map.AGENT, "units": us,
               "prompt": f"Read {p.as_posix()} and do exactly what it says. Reply with one line."}
              for g, p, us in launch]
    # every mapper the session has room for at once: one held back is the step's whole tail
    room = _agent_room(reg)
    at_once = min(len(agents), room)
    first = (f"all {len(agents)} in one message, none held back" if at_once == len(agents) else
             f"the first {at_once} in one message (the session has room for {room} more agents now), then each of "
             "the rest, in order, as each running one returns")
    return {"kind": "agent", "sub": sub, "agent_type": fast_map.AGENT, "agents": agents, "units": missing,
            "at_once": at_once,
            "then": f"launch the agents listed, each with the Agent tool, subagent_type {fast_map.AGENT}, with its "
                    f"prompt as its whole prompt: {first}. A launch Claude Code refuses with \"Concurrent subagent "
                    "limit reached\" is expected here: its error says not to retry, but this step owes that agent, "
                    "so launch the refused one again as each running one returns, never dropping it. Wait for every "
                    "reply, then call this again: run control launches any mapper still owed"}


def _agent_room(reg):
    """How many agents Claude Code will start now: its limit on agents running at once in a session
    (CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS, else judges.SESSION_LIMIT) less those the run has running; at least one."""
    import agents_now
    try:
        limit = int(os.environ.get("CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS") or judges.SESSION_LIMIT)
    except ValueError:
        limit = judges.SESSION_LIMIT
    running = int((agents_now.gather(reg) or {}).get("at_work") or 0)
    return max(1, limit - running)


def _merge_refused(reg, flow, sub, failed):
    """A full mapping's merge that refused a unit's rows (merge.py `PROBLEM: units/<unit>...`): the reader of each unit
    named is relaunched once with the merge's reason (readers.py retry, which the guard allows at the merge), as the
    fast map relaunches its mapping agent. A unit whose relaunched reader is back and still refused, or a failure
    naming no unit, is returned as the failed step, saying who acts next."""
    import re
    known = {(r.get("unit") or "").strip() for r in tables.dicts(reg / layout.UNITS_CSV)}
    by = {}
    for line in (failed.get("said") or "").splitlines():
        m = re.match(r"PROBLEM: (units/([^/\s:]+)\S*.*)$", line.strip())
        if m and m.group(2) in known:
            by.setdefault(m.group(2), []).append(m.group(1))
    if not by:
        return failed
    seen = judges.Launches(reg)
    state = {u: seen.state(layout.prompts_dir(reg, u) / readers.MERGE_FIX) for u in by}
    done = {u: s for u, s in state.items() if s in MERGE_FIX_ENDED}
    fresh = [u for u in sorted(by) if u not in done]
    if fresh:  # each unit refused for the first time gets its one relaunch, whatever the others' state
        held = _readers_held(reg, fresh)
        if held:
            case.log(reg, "merge fix held", said=held)
            return {**failed, "said": f"{failed['said']}\nREFUSED: the reader of {_names(reg, fresh)} cannot be "
                                      f"launched again with the merge's reason: {held}. Nothing was launched. Put "
                                      "that right and call run control again; if it is not yours to put right, tell "
                                      "the person what it says."}
        lines = readers.emit(reg, fresh, "retry", reason={u: "\n".join(by[u]) for u in fresh})
        a = _fanout(reg, flow, sub, "reader", 1, fresh, lines)
        if a is not None:
            case.log(reg, "relaunched readers with the merge's reason", units=fresh)
            return a
        done.update({u: state[u] or "finished" for u in fresh})
    _close_open(reg, flow, "reader", units=done)
    said = [failed["said"]]
    refused = sorted(u for u, s in done.items() if s == "finished")
    erred = sorted(u for u, s in done.items() if s == "gave up")
    shell = sorted(u for u, s in done.items() if s == "ran a shell")
    if refused:
        said.append(f"REFUSED: the merge still refuses the rows of {_names(reg, refused)} after its reader was launched "
                    "once more with the merge's reason. Tell the person what the merge refuses, in their terms; on "
                    "their word to stop mapping here, next.py --event stop \"<their words>\".")
    if erred or shell:
        why = ([f"the reader of {_names(reg, erred)}, launched again with the merge's reason, stopped on an error "
                "from the service that runs the model each time it was tried"] if erred else []) + (
               [f"the reader of {_names(reg, shell)}, launched again with the merge's reason, used a tool it is not "
                "allowed, so its work is not counted"] if shell else [])
        said.append("REFUSED: " + "; and ".join(why) + ". Tell the person; on their word to try again, next.py --event "
                    "retry \"<their words>\" launches it afresh; on their word to stop mapping here, next.py --event "
                    "stop \"<their words>\".")
    case.log(reg, "merge held", units=sorted(done))
    return {**failed, "said": "\n".join(said) + "\nNothing was launched."}


MERGE_FIX_ENDED = ("finished", "gave up", "ran a shell")
STEPPED_BACK = "stepped_back"  # in a flow's case record: the end-of-mapping refusal run control last stepped back on


def _close_open(reg, flow, kind, units=None):
    for r in case.records(reg):
        if r["status"] == "open" and r["flow"] == flow and r["kind"] == kind and (units is None or r["unit"] in units):
            case.close_record(reg, r["id"])


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
        refused = _fast_set_aside(reg, flow, sub)
        if refused:  # a refused mapping agent: its units are launched again, never handed to the person to relaunch
            return refused if refused.get("kind") != "set aside" else _back_to_fast_read(reg, flow)
        found, _ = fast_map.check(reg, flow, judges.workspace(reg))
        return _judgment(sub, "Put right what the fast map's rule check found: a cited range that does not exist, in "
                         "the unit row or your own row it names (a unit row only with `python <skill>/fast_map.py fix "
                         "<register> <unit> <table> <row_id> <column> \"<value>\"`, never Write, Edit or a script: a "
                         "unit changed any other way is set aside and written again by its mapping agent); or, for a "
                         "unit the mapping agent did not write, call this again, which hands you its mapping agent to "
                         "launch (never launch one on your own: run control's launch is what lets it rewrite a unit)",
                         LEAD_WRITE + ["units/<unit>/ (the row named only, through fast_map.py fix)"],
                         ["fast_map.py check"], found) if found else None
    if sub == "short names":
        return _short_names(reg, flow, sub)
    if sub == "fast draw":
        import fast_map
        chose = case.flow(reg, flow).get(CORRECTING) or {}
        checked = _correction_checked(reg, flow, sub)
        if checked:
            return checked
        # a unit changed since the merge (the lead's correction, the list's spelling written back, or a unit written
        # again after it was set aside): merged again, so the map's check reads the units as they are
        if fast_map.normalise_units(reg) or chose.get("units") or _merge_stale(reg):
            a = _code(reg, sub, ["merge.py", str(reg)])
            if a:
                return a
        a = _code(reg, sub, ["fast_map.py", "draw", str(reg), flow], lambda: (reg / fast_map.PAGE).is_file())
        if a:
            return a
        refused = fast_map.register_refusals(reg)
        if chose.get("units") and not set(refused) & set(chose["units"]):
            _correction_holds(reg, flow, chose)
        if refused:  # rows only a mapping agent may write: set its units aside and launch it again with the reason
            owed, stuck, why = fast_map.set_aside_bad_ids(reg, refused)
            if stuck:
                said = (f"REFUSED: the mapping agent's rows for {', '.join(stuck)} were refused again by the map's "
                        f"check after it was launched once more: {'; '.join(why)}. Nothing was launched.")
                case.log(reg, "fast draw held", said=said)
                return _stuck(reg, flow, sub, stuck, "rows", said, why)
            case.log(reg, "set aside units the map's check refused", units=owed)
            return _back_to_fast_read(reg, flow)
        a = (_code(reg, sub, ["capability_views.py", str(reg), "--check"])
             or _code(reg, sub, ["one_canvas.py", str(reg), str(reg / "views.html")]))
        if a is None:  # the map is drawn: its phases are done, closed here so the run's record times them
            _close_mapping_rows(reg, flow)
        return a
    if sub == "units":
        _read_identity(reg)
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
        failed = _code(reg, sub, ["merge.py", str(reg)])
        if failed:
            return _merge_refused(reg, flow, sub, failed)
        _close_open(reg, flow, "reader")  # a reader relaunched with the merge's reason: its work is merged now
        return _identity_judged(reg, flow, sub) or _redraw_stale(reg, flow, sub)
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
                "lifecycle.csv, or correct the call's step_hint. A part a move names whose service the fast map does "
                "not read (its stage is left mapped only): its row in merge/lead-rows/subjects.csv (level, band, "
                "part_kind, repository and purpose, cited to what the first look read, with 'not read in this run' "
                "in its source) and its performs or supports rows in merge/lead-rows/participation.csv from the "
                "lifecycle's carried_by and needs, with no operation, and its subject_id in "
                f"{PLACEHOLDERS} (columns subject_id and flow, this flow's id); then gap its 'part: operations' and "
                f"'part: depends on' in measure-gaps.csv, kind 'not read', why '{NOT_READ_WHY}'. A row added to the "
                "parts after the merge goes in merge/lead-rows/; merge again")
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
        if code != 0 and "the split run's checks do not pass" in out and case.flow(reg, flow).get(STEPPED_BACK) != out:
            # a unit's rows changed after the merge (a stop fixer): the merge and the judging are owed again, so run
            # control walks them from the merge, once for each refusal
            case.set_flow(reg, flow, state="mapping", sub="merge", **{STEPPED_BACK: out})
            case.log(reg, "ending refused by the split checks: back to the merge", said=out[-400:])
            return {"kind": "step back", "sub": "merge"}
        if code != 0 and fast(reg):  # the fast map has no fixers: the guard refuses one
            return _judgment(sub, "Put right what ending the flow refused, then hand back: a reason on your own rows "
                             "in your own tables; a reason on a unit's row with `python <skill>/fast_map.py fix "
                             "<register> <unit> <table> <row_id> <column> \"<value>\"`, never Write, Edit or a script",
                             ["the lead's own tables", "a unit's row, through fast_map.py fix"],
                             ["go.py --mapping-ends"], [out])
        if code != 0:
            return _judgment(sub, "Put right what ending the flow refused, then hand back: a reason on your own rows "
                             "in your own tables; a reason only a unit's rows can clear goes to that unit's fixer "
                             "(readers.py prompt <register> <unit> --mode stop --reason \"<the reason, as printed>\")",
                             ["the lead's own tables", "a unit's rows, through its fixer (readers.py ... --mode stop)"],
                             ["go.py --mapping-ends"], [out])
        return None
    raise ValueError(sub)


def _short_names(reg, flow, sub):
    """A fast map's short names, before the map is drawn, so judged once whether or not measures follow: one judge
    reads all the flow's (judges.short_name_rows); a flag goes to the flow's fixer (readers.py fix, as in the full
    reading), and the corrected names are judged once more; still flagged then, they are disputed (judges.collect)."""
    rows = judges.short_name_rows(reg)
    if not rows:
        return None
    a = _fanout(reg, flow, sub, "judge", 1, ["flow"], judges.emit(reg, "flow", 1))
    if a:
        return a
    judges.collect(reg)
    if not judges.flagged_in(reg, rows, 1, judges.settings(reg)["judges"]):
        return None
    a = (_fanout(reg, flow, sub, "fixer", 1, ["flow"], readers.emit(reg, ["flow"], "fix"))
         or _fanout(reg, flow, sub, "judge", 2, ["flow"], judges.emit(reg, "flow", 2, "flagged")))
    if a:
        return a
    judges.collect(reg)
    return None


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
        text += "".join(f"\n\nThe second reading of {u} found {now} calls where an earlier reading found {most}. "
                        "Check those calls in the code before relying on this part of the map."
                        for u, now, most in fast_map.fewer_calls(reg))
        folder = pathlib.Path(reg) / MESSAGES
        folder.mkdir(exist_ok=True)
        f = folder / f"map-stop-{flow}.md"
        f.write_text(text, encoding="utf-8")
        code, out = _run(["brief.py", "say", str(reg), str(f)])
        finding = None
        if code != 0:  # the kit's own message: its refusal is a kit finding, and the message goes out with advice
            finding = _kit_defect(reg, "fast-map-stop", _map_stop, out)
            code, out = _say_kit(reg, f)
        if code != 0:
            return {"kind": "code", "sub": "map stop", "ok": False,
                    "command": ["python", "brief.py", "say", str(reg), str(f)], "said": out,
                    "kit_finding": finding}
        import kit_findings
        beside = kit_findings.line(reg)
        beside = f" Send beside the report, as it is: {beside}" if beside else ""
        if by_kit and _further(reg):
            return {"kind": "stop", "stop": "map", "message": out, "records_with": "next.py --event chat",
                    "then": ("back to the stage kit's SKILL.md: the measures for the stages taken further ("
                             + ", ".join(_further(reg)) + "), drafted from the fast map's rows; then selective.py "
                             "check before the measures review, which then shows each measure's rows as checked, "
                             "flagged or not checked" + beside)}
        return {"kind": "stop", "stop": "map", "message": out, "records_with": "next.py --event chat",
                "then": ("the flow is finished: this message is its report. Then, with flows left, the stage kit's "
                         "SKILL.md 'Then the next flow' (brief.py next --after, sent at the end of this message), "
                         "and go.py --report-sent once it is sent" + beside if by_kit else
                         "the fast map is handed over: every stage was left mapped only" + beside)}
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
    finding = None
    if code != 0:  # the kit's own message: its refusal is a kit finding, and the message goes out with advice
        finding = _kit_defect(reg, "map-stop", _map_stop, out)
        code, out = _say_kit(reg, f)
    if code != 0:
        return {"kind": "code", "sub": "map stop", "ok": False,
                "command": ["python", "brief.py", "say", str(reg), str(f)], "said": out,
                "kit_finding": finding}
    a = {"kind": "stop", "stop": "map", "message": out, "records_with": "next.py --event chat"}
    if finding:
        a["kit_finding"] = finding
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
        a = _decide(reg, flow, event, by_kit, test)
        _stop_record(reg, a)
        return a
    finally:
        _timings(reg, event[0] if event else "")


HELD_STOPS = {"agents lost": "Mapping has stopped: agents of the run stopped without their work.",
              "mapping held": "Mapping is held: it needs your choice before it can go on."}
STEP_FAILED = "A step of the mapping failed, and the run stopped there."


def _stop_record(reg, a):
    """The kit's stop record (run_state.STOP), which the run status page and the watchdog read: written when run
    control's step failed or it stops on the person, cleared when it moves on. The person reads one plain sentence of
    the kit's own; what the step printed goes to the run's log only. Never raises."""
    try:
        import run_state
        if a.get("kind") == "code" and a.get("ok") is False:
            case.log(reg, "step failed", sub=a.get("sub"), said=str(a.get("said") or "")[-400:])
            run_state.record_stop(reg, STEP_FAILED, code=f"step-failed:{a.get('sub') or ''}")
        elif a.get("kind") == "stop" and a.get("stop") in HELD_STOPS:
            run_state.record_stop(reg, HELD_STOPS[a["stop"]],
                                  "Answer the run's last message in its chat; it lists your choices.",
                                  code=a["stop"].replace(" ", "-"))
        else:
            run_state.clear_stop(reg)
    except Exception:  # noqa: BLE001 - the record is for the person's notice; run control goes on without it
        pass


def _close_mapping_rows(reg, flow):
    """Set RUN.md's phases 1 to 3 done through run_md's logged writer, once a fast map is drawn: the lead writes their
    rows but no later step of a fast run closes them. A row already done is left as it is."""
    import run_md
    for lead in ("1 ", "2 ", "3 "):
        run_md.set_row(reg, lead, "done", flow=flow, by="run control")


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


def _note_failed(reg, flow, a):
    """Keep in the flow's case record what its step said when it failed (guard.FAILED), cleared once a step does not,
    so a script the guard refuses meanwhile names that step and its recovery instead of sending the session back to
    run control, which would return the same failure."""
    said = ""
    if a is not None and a.get("kind") == "code" and a.get("ok") is False:
        said = " ".join((a.get("said") or "the step's command failed").split())[-600:]
    if (case.flow(reg, flow).get(guard.FAILED) or "") != said:
        case.set_flow(reg, flow, **{guard.FAILED: said})


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
        if kind in ("retry", "leave-unread", "correct", "choices"):
            answered = _stuck_answer(reg, flow, kind, payload, test)
            if answered:
                return answered
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
    if f.get("state") == "mapped" and fast(reg):
        wrong = _drawn_map_wrong(reg, flow)
        if wrong:  # the units changed after the map was drawn, or its check fails: back into run control, never a stop
            case.log(reg, "the drawn fast map no longer holds: mapping again from the fast read", said=wrong)
            case.set_flow(reg, flow, state="mapping", sub="fast read")
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
            import go
            if (_by_stage(reg) or {}).get(go.HOW_FAR):  # answered at the go: recorded, not asked again
                import brief
                got = brief.depth_from_go(reg, flow)
                if isinstance(got, str):
                    return {"kind": "stop", "stop": "pick", "sub": "pick", "refused": got,
                            "then": f"the pick the go answered was refused ({got}): put it to the person as the stage "
                                    "kit's SKILL.md says (brief.py depth; recorded with go.py --depth), then call "
                                    "this again", "records_with": "go.py --depth"}
                case.draw_run_md(reg)
                continue
            case.draw_run_md(reg)
            return _pick_stop(reg, flow)
        if s == "sweep" and _sweep(reg):
            case.set_flow(reg, flow, state="mapping", sub="units")
            return _decide(reg, flow, None, by_kit, test)
        a = _step(reg, flow, s)
        if a is not None and a.get("kind") == "step back":
            return _decide(reg, flow, None, by_kit, test)
        _note_failed(reg, flow, a)
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
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if len(argv) < 2:
        print(__doc__)
        return 2
    argv[0] = str(pathlib.Path(argv[0]).resolve())  # helpers run from the kit's folder, so never a relative path
    event = None
    if "--event" in argv:
        i = argv.index("--event")
        event = (argv[i + 1], argv[i + 2] if len(argv) > i + 2 else "")
        argv = argv[:i]
    print(json.dumps(silent(decide(argv[0], argv[1], event, by_kit, test)), ensure_ascii=False))
    return 0


SILENT = guard.SILENT  # put on the action the session acts on when an agent returns, not only in SKILL.md
QUIET_KINDS = ("fanout", "wait", "agent", "judgment", "code")


def silent(action):
    """The action with `to_the_person` set to SILENT on every kind that is not a stop or a line to send."""
    if isinstance(action, dict) and action.get("kind") in QUIET_KINDS:
        action = dict(action, to_the_person=SILENT)
    return action


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
