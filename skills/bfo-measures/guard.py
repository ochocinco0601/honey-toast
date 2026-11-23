"""The run's guard: every script that launches agents or changes the map's state asks it first, and it refuses an
action whose preconditions do not hold. The order of mapping is held here in code, not by the session remembering it.

require(reg, action, **detail) returns None when the action may go ahead, else the reason in one line. The caller
prints `REFUSED: <reason>. Nothing was launched.` (or written) and exits 2. It fails closed: with no go recorded, no
reader, judge or merge runs. Run control (next.py) passes through the same checks, so an action is refused whether
the session typed it or run control chose it.

Two kinds of precondition:
  data   what the register itself must hold: a go, the lead's stages and process steps, the pick of how far each
         stage goes where the flow is read by stage, every reader back before the merge, the merge before judging
  order  where run control has got to (case.json, the flow's sub-state): an action is allowed only once run control
         has reached its step. A register no run control has written (an earlier release) is held by the data checks
         alone.

The kit mode is read from the register: the go records which skill took it (go.KIT), and a run control call made
with --by-kit records it too, so a later call that leaves the flag off still stops for the person's pick.
Python standard library only."""
import pathlib

ORDER = ["lead steps", "impact", "pick", "units", "readers", "merge", "re-reads", "sweep", "lead rows",
         "judge round 1", "fixers", "judge round 2", "draw", "check", "mapping ends"]
# The fast map (go.py --fast, fast_map.py): one mapping agent reads the code and writes every unit's rows, then the
# merge, the checks by script and the drawing; no readers, re-reads or judges.
FAST_ORDER = ["lead steps", "impact", "pick", "units", "fast read", "merge", "lead rows", "fast check", "fast draw",
              "mapping ends"]
STAGE_KIT = "bfo-stage-kit"


def order(reg):
    """The order of mapping for the flow worked now: FAST_ORDER when its go chose the fast map, else ORDER."""
    import settings
    try:
        return FAST_ORDER if settings.load(reg).get("mapping") == "fast" else ORDER
    except ValueError:
        return ORDER
# the step of run control each action belongs to: allowed once run control has reached it
STEP_OF = {"read": "readers", "retry": "readers", "reread": "re-reads", "fix": "fixers", "stop": "check",
           "merge": "merge", "judge 1": "judge round 1", "judge 2": "judge round 2"}
NEXT = "call run control (next.py) and do the one action it prints"


def _go(reg):
    import go
    return go.load(reg)


def _flow_id(reg, s):
    import go
    return go.flow_id_of(reg, s)


def _rows(p):
    import tables
    return tables.dicts(p)


def lead_written(reg, flow):
    """True when the flow has stages and process steps: the readers place their parts in those steps."""
    reg = pathlib.Path(reg)
    stages = {(r.get("stage") or "").strip() for r in _rows(reg / "stages.csv") if (r.get("flow") or "").strip() == flow}
    stages.discard("")
    return bool(stages) and any((r.get("stage") or "").strip() in stages for r in _rows(reg / "steps.csv"))


def run_by_kit(reg, s=None):
    """True when the stage kit runs this flow's mapping, read from the register (the go's KIT)."""
    import go
    s = _go(reg) if s is None else s
    return bool(s) and s.get(go.KIT) == STAGE_KIT


def pick_owed(reg, s=None):
    """True when the person's pick of how far each stage goes is owed before any service is read: a flow read by
    stage, run by the stage kit, with no pick recorded."""
    import go
    s = _go(reg) if s is None else s
    return bool(s and s.get(go.BY_STAGE) and run_by_kit(reg, s) and not s.get("depth"))


def at_or_past(reg, flow, step):
    """True or False from the case record: whether run control has reached `step` for the flow; None when no run
    control has written this flow (an earlier release's register), so only the data checks hold it."""
    import case
    f = case.flow(reg, flow)
    if not f:
        return None
    if f.get("state") in ("mapped", case.ENDED):
        return True
    sub, steps = f.get("sub"), order(reg)
    if sub not in steps or step not in steps:
        return None if not sub else False
    return steps.index(sub) >= steps.index(step)


def _order(reg, flow, action):
    step = STEP_OF[action]
    if step not in order(reg):
        return f"the flow is mapped fast (go.py --fast), and its order has no '{step}': {NEXT}"
    past = at_or_past(reg, flow, step)
    if past is False:
        import case
        sub = case.flow(reg, flow).get("sub") or "the start"
        return f"run control is at '{sub}' for {flow}, not yet at '{step}': {NEXT}"
    return None


def require(reg, action, units=(), unit=None):
    """None when `action` may go ahead now; else why not, in one line. Actions: read, retry (a reader), reread,
    fix, stop (a fixer), merge, judge 1, judge 2 (with `unit`, the judged unit or "flow")."""
    reg = pathlib.Path(reg).resolve()
    s = _go(reg)
    if action == "merge" and not s:  # a merge of unit folders with no go orders nothing the person decides
        return None
    if not s:
        return ("no go is recorded: nothing is read, merged or judged before the person picks the flow "
                "(go.py --flow)")
    flow = _flow_id(reg, s)
    if action in ("read", "retry"):
        import go
        open_ = go.searches_open(reg)
        if open_:
            return (f"the person has not answered {len(open_)} search(es) the first look proposed (item "
                    f"{', '.join(str(x['n']) for x in open_)}): send the follow-up go.py printed, record their answer "
                    "with go.py --searches, then launch")
        if not lead_written(reg, flow):
            return (f"the lead's stages and process steps for {flow or 'the flow'} are not written: the readers place "
                    "their parts in those steps, so Steps 1 to 4 come first")
        if pick_owed(reg, s):
            return ("the person has not picked how far each stage goes: no service is read in depth before that "
                    "pick (brief.py depth, then go.py --depth)")
        bad = _order(reg, flow, action)
        if bad:
            return bad
        import readers
        owed, done = readers.in_scope(reg)
        allowed = set(owed) | set(done)
        off = [u for u in units if u not in allowed]
        if off:
            return (f"not owed a reader for this flow: {', '.join(off)} (only the services of the stages taken past "
                    "mapped only are read; readers.py prompt --in-scope lists them)")
        return None
    if action == "merge":
        if pick_owed(reg, s):
            return "the person has not picked how far each stage goes: the merge comes after the readers, after that pick"
        bad = _order(reg, flow, action)
        if bad:
            return bad
        if at_or_past(reg, flow, "merge") is not None:  # run control is in use: no reader of this flow still owed
            import readers
            owed, _ = readers.in_scope(reg)
            if owed and at_or_past(reg, flow, "lead rows") is False:
                return (f"{len(owed)} reading unit(s) not yet read for this flow ({', '.join(owed[:5])}): every "
                        "reader is back first")
        return None
    if action in ("judge 1", "judge 2") and "fast check" in order(reg):  # selective checking (selective.py)
        import selective
        if action == "judge 2":
            return "a fast map is checked in one round, one checker per selected row (selective.py)"
        sel = selective.selected(reg)
        if sel is None:
            return ("no rows are selected for checking yet: the measures are drafted first, then selective.py "
                    "select picks the rows they rest on")
        if unit not in sel:
            return f"no row of {unit} is one a proposed measure, alert or failure mode rests on (selective.py select)"
        return None
    if action in ("judge 1", "judge 2"):
        bad = _order(reg, flow, action)
        if bad:
            return bad
        import register_layout as layout
        if action == "judge 1":
            if unit == "flow" and not (reg / layout.SUMMARY_JSON).is_file():
                return "the map is not merged yet: the lead's rows are judged after the merge"
            if unit not in (None, "flow") and not (reg / layout.UNITS / unit / layout.FILES_CSV).is_file():
                return f"the unit {unit} has not been read: a unit is judged once its reader is back"
            return None
        if not (reg / layout.JUDGEMENTS_CSV).is_file():
            return "round 1 is not collected (judges.py collect): round 2 judges only what round 1 flagged"
        import case
        running = [r for r in case.records(reg) if r.get("status") == "open" and r.get("kind") in ("fixer", "stop-fixer")
                   and r.get("flow") == flow]
        if running:
            return f"{len(running)} fixer(s) still running: round 2 starts once every fixer is back"
        return None
    if action in ("reread", "fix", "stop"):
        return _order(reg, flow, action)
    raise ValueError(action)


def depth_problem(reg, flow, shown_needed=True):
    """Why a pick of how far each stage goes cannot be recorded now, or None: Business Impact must be written for the
    flow's process steps, and the pick must have been put to the person (brief.py depth marks it)."""
    reg = pathlib.Path(reg)
    stages = {(r.get("stage") or "").strip() for r in _rows(reg / "stages.csv") if (r.get("flow") or "").strip() == flow}
    steps = {(r.get("step") or "").strip() for r in _rows(reg / "steps.csv") if (r.get("stage") or "").strip() in stages}
    rated = {(r.get("step") or "").strip() for r in _rows(reg / "step-impact.csv")}
    if steps and not (steps & rated):
        return ("Business Impact is written for none of this flow's process steps: the person sees what is at stake "
                "in each stage before picking (FILL-STEPS Step 10)")
    if shown_needed and run_by_kit(reg) and not pick_shown(reg, flow):  # the pick is a stop only the stage kit makes
        return ("the pick of how far each stage goes was never put to the person: render it with brief.py depth and "
                "record what they answer")
    return None


PICK_SHOWN = "case-messages/pick-shown.json"


def mark_pick_shown(reg, flow):
    import datetime
    import json
    p = pathlib.Path(reg) / PICK_SHOWN
    p.parent.mkdir(parents=True, exist_ok=True)
    got = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    got[flow] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    p.write_text(json.dumps(got, indent=1), encoding="utf-8")


def pick_shown(reg, flow):
    import json
    p = pathlib.Path(reg) / PICK_SHOWN
    try:
        return bool(json.loads(p.read_text(encoding="utf-8")).get(flow))
    except (OSError, ValueError, AttributeError):
        return False
