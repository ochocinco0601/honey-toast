"""Run control for mapping one flow: decide the next action from the case record and the files on disk.

Usage: python next.py <register folder> <flow id> [--by-kit] [--test] [--event stop "<the person's words>" | --event launcher-done <file>
                                                     | --event chat "<the person's words>"]

Prints one action as JSON. The session does what it says and calls this again; it never decides the next step itself.
  judgment  a bounded task for the model: `task`, `write` (the tables it may write), `contract` (the checks it must
            pass), `findings` (what the last check said); hand back by calling this again
  fanout    launch one general-purpose agent per line of `pointer_lines`, at most `cap` launchers at once, then end
            the turn; call this again on each launcher's reply (--event launcher-done)
  wait      agents are still running; nothing to launch: end the turn and call this again on the next reply
  code      a step this script ran itself (`ran`), or one too long to run here (`command`, `wait`)
  stop      a point where the run waits on the person: `stop`, `message` (written for them), `records_with`
  notify    a line the session sends as it is

The order is mapping's, one flow at a time: lead steps, units listed, readers, merge, re-reads of calls between units,
lead rows, judge round 1, fixers, judge round 2, the map drawn, the check, mapping ends; run by the stage kit
(--by-kit), mapping is never ended here and the map stop hands the flow back to the kit for its pick. The case keeps where the flow is (case.py);
every agent the run launches is a record there, opened before launch and closed when its unit's work is on disk.
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
import tables  # noqa: E402

ENDED = case.ENDED
LEAD_WRITE = ["flows", "lifecycle", "stages", "steps", "subjects", "participation"]
LEAD_RULES = ["case", "stages-connect", "reachable", "grounded", "cited"]
LEAD_ROWS_WRITE = ["set-aside", "agent-system", "capabilities", "step-impact", "case-attributes"]
ORDER = ["lead steps", "units", "readers", "merge", "re-reads", "lead rows", "judge round 1", "fixers",
         "judge round 2", "draw", "check", "mapping ends"]
MESSAGES = "case-messages"
RUNNING = ("still running", "queued")


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


def _check_lead_rows(reg, flow):
    import map_record
    R = map_record.load(reg)
    out = [] if R.get("capabilities") else ["no capability named"]
    import check_map
    out += [f"{r['title']}: {'; '.join(r['items'])}" for r in check_map.inspect(reg, flow)
            if r["rule"] == "impact" and not r["passed"]]
    return out


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


def _fanout(reg, flow, sub, kind, rnd, units, lines):
    ptr = _pointers(lines)
    if ptr:
        for u in units:
            case.open_record(reg, flow, u, kind, rnd)
        return {"kind": "fanout", "sub": sub, "pointer_lines": ptr, "cap": judges.launcher_cap(reg),
                "said": [x for x in lines if x not in ptr]}
    if _running(lines):
        return {"kind": "wait", "sub": sub, "said": lines}
    for r in case.records(reg):
        if r["status"] == "open" and r["flow"] == flow and r["kind"] == kind and r["round"] == rnd:
            case.close_record(reg, r["id"])
    return None


def _judgment(sub, task, write, contract, findings):
    return {"kind": "judgment", "sub": sub, "task": task, "write": write, "contract": contract, "findings": findings}


def _step(reg, flow, sub):
    """The action this sub-state still owes, or None when it is done."""
    reg = pathlib.Path(reg)
    if sub == "lead steps":
        found = _check_lead(reg, flow)
        return _judgment(sub, "Steps 1 to 4 of the mapping steps: the case, its lifecycle, the stages and the process "
                         "steps, and the lead's own parts", LEAD_WRITE, LEAD_RULES, found) if found else None
    if sub == "units":
        if (reg / layout.UNITS_CSV).is_file():
            return None
        return _code(reg, sub, ["units.py", str(reg)], lambda: (reg / layout.UNITS_CSV).is_file())
    if sub == "readers":
        owed, _ = readers.in_scope(reg)
        if not owed:
            return _fanout(reg, flow, sub, "reader", 1, [], [])
        return _fanout(reg, flow, sub, "reader", 1, owed, readers.emit(reg, owed, "read"))
    if sub == "merge":
        return _code(reg, sub, ["merge.py", str(reg)])
    if sub == "re-reads":
        if not _unmatched(reg):
            return None
        a = _fanout(reg, flow, sub, "re-read", 1, sorted({c["call"].split("/", 1)[0] for c in _unmatched(reg)}),
                    readers.emit(reg, [], "reread"))
        return a or _code(reg, sub, ["merge.py", str(reg)])
    if sub == "lead rows":
        found = _check_lead_rows(reg, flow)
        return _judgment(sub, "Steps 7, 8 and 10: the parts set aside, the AI agents, the capability and Business "
                         "Impact; a row added to the parts after the merge goes in merge/lead-rows/",
                         LEAD_ROWS_WRITE, ["impact"], found) if found else None
    if sub in ("judge round 1", "judge round 2"):
        rnd = int(sub[-1])
        units = judges._units(reg) if rnd == 1 else _flagged_units(reg)
        lines = []
        for u in units:
            lines += judges.emit(reg, u, rnd, "flagged" if rnd == 2 else None)
        a = _fanout(reg, flow, sub, "judge", rnd, units, lines)
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
    flow when the stage kit runs mapping (the kit takes the flow on, and ending it would count it finished)."""
    if sub == "mapping ends":
        return by_kit
    return sub in ("fixers", "judge round 2") and not _flagged_units(reg)


def _inspection(reg, flow):
    import check_map
    return check_map.counted(reg, flow, check_map.open_items(reg, flow))


def _map_stop(reg, flow, ended, by_kit=False):
    """The map stop, rendered through brief.py say, which puts the status line and the page's address around it and
    refuses ids and kit words; a refusal is handed back, never sent."""
    first = ("The map is drawn as it stands and is not checked against the code: you stopped the checks, so what "
             "was not yet checked is shown as not checked." if ended else "The map is drawn.")
    folder = pathlib.Path(reg) / MESSAGES
    folder.mkdir(exist_ok=True)
    f = folder / f"map-stop-{flow}.md"
    f.write_text(first + "\n\n" + _inspection(reg, flow), encoding="utf-8")
    code, out = _run(["brief.py", "say", str(reg), str(f)])
    if code != 0:
        return {"kind": "code", "sub": "map stop", "ok": False,
                "command": ["python", "brief.py", "say", str(reg), str(f)], "said": out}
    a = {"kind": "stop", "stop": "map", "message": out, "records_with": "next.py --event chat"}
    if by_kit:
        a["then"] = "back to the stage kit's SKILL.md for the pick of how far each stage goes"
    return a


def decide(reg, flow, event=None, by_kit=False, test=False):
    reg = pathlib.Path(reg)
    refusal = _lock_refusal(reg)
    if refusal:
        return {"kind": "stop", "stop": "held", "message": refusal, "records_with": "start.py --release"}
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
        if kind == "chat":
            return _judgment(f.get("sub"), "Read the person's words: a topic to talk about, a redirect, a stop, or an answer "
                             "to the open question. Say back your reading in one line before anything that discards "
                             "work; for a stop call this again with --event stop and their words",
                             [], ["say back first"], [payload])
    if f.get("state") in (ENDED, "mapped"):
        return _map_stop(reg, flow, f.get("state") == ENDED, by_kit)
    sub = f.get("sub") if f.get("sub") in ORDER else ORDER[0]
    for s in ORDER[ORDER.index(sub):]:
        if s != f.get("sub"):
            case.set_flow(reg, flow, state="mapping", sub=s)
            f = case.flow(reg, flow)
        if _skip(reg, flow, s, by_kit):
            continue
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
