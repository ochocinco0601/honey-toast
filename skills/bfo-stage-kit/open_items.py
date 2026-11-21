"""The draft's open items, and the person's decisions on them: one record per flow, worked out from the stage checks,
which every surface (the status line, the stop messages, the resume, the home page, the run status page, the final
check) and every gate (the next flow, the runbooks, the reviews' go) reads, so no two of them can disagree.

A stage's check that fails is never hidden, never approved and never blocks the person: its items are the draft's open
items. For each flow and each concern (measures, alerts, runbooks) the record holds the items open now, by stage, as
the stage's own check finds them (flow_outputs.stage_open, the receipt rule among its rules), each counted once however
many stages or concerns find it, and the person's decisions on them: the go on each review, with the items it was
given on; each fix the run made after a go, told and never reviewed again; and their word to go on with items still
open ("next flow"), with the items it covered. Everything here is the flow's own: another flow's items and decisions
are in that flow's record.

Usage: python open_items.py <register folder> [flow id]  (prints the record, for a session or a reviewer)"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

CONCERNS = ("measures", "alerts", "runbooks")
PART = {"measures": "measures", "alerts": "alerts", "runbooks": "all"}  # flow_outputs.check's part for each
DEPTHS = {"measures": ("measure", "alerting", "runbooks"), "alerts": ("alerting", "runbooks"), "runbooks": ("runbooks",)}
REVIEW = {"measures": "measures_reviewed", "alerts": "alerts_reviewed"}  # the go on each concern, in the flow's record
LEFT = "open_left"  # the person's word to go on with these items still open (go.record_open_left)


def stage_items(R, flow_id, stage, measured, concern):
    """The open items of one stage for one concern, in plain words, as its own check finds them: [] when it passes.
    The alerts check runs the measures' rules too, so an item it shares with the measures is found by both; the
    runbooks' own items are those their check adds to the alerts'. The one computation the record, the reviews and
    the runbooks gate all use."""
    import flow_outputs as fo
    got = fo.open_items(fo.stage_open(R, flow_id, stage, measured, PART[concern]), R)
    if concern == "runbooks":
        alerts = set(stage_items(R, flow_id, stage, measured, "alerts"))
        got = [x for x in got if x not in alerts]
    return got


def _flow(reg, flow):
    """(the flow's record in scope.json, whether it is the flow worked now)."""
    import go
    cur = go.load(reg)
    if flow is None:
        return cur, True
    if isinstance(flow, dict):
        return flow, bool(cur) and flow.get("flow") == cur.get("flow")
    s = go.record_of(reg, flow)
    if s is not None and go.flow_id_of(reg, s) != flow:
        s = next((x for x in go.load_all(reg) if go.flow_id_of(reg, x) == flow), None)
    return s, bool(s) and bool(cur) and s.get("flow") == cur.get("flow")


def _reached(reg, sid, concern, rows, now):
    """Whether the run has reached this concern for the stage: a flow finished earlier has reached every one its pick
    names; the flow worked now, the ones its run record has come to (the measures once proposed for the stage, the
    alerts once their stage is written, the runbooks once theirs is)."""
    if not now:
        return True
    lead, page = {"measures": ("4 ", "MEASURES.md"), "alerts": ("5a ", "ALERT.md"),
                  "runbooks": ("5b ", "RUNBOOK.md")}[concern]
    state = rows.get(lead)
    if state == "done":
        return True
    written = (pathlib.Path(reg) / f"stage-{sid}" / page).is_file()
    return written and (concern == "measures" or state is None)


def empty(fid="", name="", unreadable=False):
    return {"flow": fid, "name": name, "now": False, "unreadable": unreadable, "stages": [], "items": [], "by_stage": {},
            "concerns": {c: {"by_stage": {}, "items": [], "go": None} for c in CONCERNS},
            "fixed": [], "left": None, "left_open": False, "held_runbooks": []}


def of_flow(reg, flow=None):
    """The record of one flow (its id, its record in scope.json, or the flow worked now when None): its open items now,
    by concern and by stage, and the person's decisions on them. `left_open` is true when there are items and the
    person's word to go on covers every one; `held_runbooks` are the stages whose runbooks wait on open alert items."""
    import flow_outputs as fo
    import go
    reg = pathlib.Path(reg)
    s, now = _flow(reg, flow)
    if not s:
        return empty()
    fid = go.flow_id_of(reg, s)
    out = empty(fid, s.get("flow", ""))
    out["now"] = now
    for c, key in REVIEW.items():
        r = s.get(key) or None
        if r:
            out["concerns"][c]["go"] = {"words": r.get("words", ""), "given": r.get("given", ""),
                                        "test": bool(r.get("test")), "open_at_go": list(r.get("open") or []),
                                        "fixed": list(r.get("fixed") or [])}
    out["fixed"] = list(s.get("open_fixed") or [])
    out["left"] = s.get(LEFT) or None
    depth = s.get("depth") if isinstance(s.get("depth"), dict) else {}
    if not fid or not depth:
        return out
    try:
        R = fo.load(reg)
    except Exception:  # noqa: BLE001 - a register the generator cannot read is reported by its other checks
        return out
    rows = go.row_states(reg) if now else {}
    measured = {x for x, d in depth.items() if d != "none"}
    order = [st["stage"] for st in R["stages"] if st.get("flow") == fid]
    for sid in order:
        d = depth.get(sid, "none")
        for c in CONCERNS:
            if d not in DEPTHS[c]:
                continue
            if c == "runbooks" and out["concerns"]["alerts"]["by_stage"].get(sid):
                out["held_runbooks"].append(sid)  # its runbooks wait on the alerts' open items
                continue
            if not _reached(reg, sid, c, rows, now):
                continue
            try:
                got = stage_items(R, fid, sid, measured, c)
            except Exception:  # noqa: BLE001 - a stage the generator cannot build is reported by its other checks
                continue
            if got:
                out["concerns"][c]["by_stage"][sid] = got
    for c in CONCERNS:
        con = out["concerns"][c]
        con["items"] = list(dict.fromkeys(x for v in con["by_stage"].values() for x in v))
        for sid, v in con["by_stage"].items():
            out["by_stage"].setdefault(sid, [])
            out["by_stage"][sid] += [x for x in v if x not in out["by_stage"][sid]]
    out["stages"] = [sid for sid in order if out["by_stage"].get(sid)]
    out["items"] = list(dict.fromkeys(x for sid in out["stages"] for x in out["by_stage"][sid]))
    left = set((out["left"] or {}).get("items") or [])
    out["left_open"] = bool(out["items"]) and set(out["items"]) <= left
    return out


def every_flow(reg):
    """The record of each flow started in this register, in the order they were started."""
    import go
    return [of_flow(reg, s) for s in go.load_all(reg)]


def main(argv):
    if not argv:
        sys.exit(__doc__)
    print(json.dumps(of_flow(pathlib.Path(argv[0]), argv[1] if len(argv) > 1 else None), indent=1,
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
