"""How far the work on each flow has gone, as data: depth.json in the register folder, for the home screen.

Usage: python depth.py <register folder>                    write depth.json
       python depth.py <register folder> --recommend "<stage id>=none|measure|alerting|runbooks: <one-line reason>; ..."
                                                            at the pick of how far each stage goes: record the
                                                            recommendation per stage, then write depth.json

Per flow: what it is; each milestone (Identified, Mapped, Measures defined, Alerts defined, Runbooks written) with a
status of `not started`, `draft` or `reviewed`, what it covers and the pages the kit already draws for it; each
stage with the person's pick, its map facts, steps, parts and holes, its measure items, alerts and runbook entries;
and every measure of the flow counted once by handle. Then the open choice, derived from the run's current stop
(RUN.md) and what is recorded (orientation.json, scope.json, the recommendation at the pick, the register): the
milestone it is for, the task line, its items (each with a name, recommended yes or no, a one-line reason, a
status and `opts`, the ticks offered), the add line, and `choice_id`, a hash of what the person is asked.

Nothing here is "done" or "reached": what the run writes is a draft, and `reviewed` is only where the person gave a
go (the review of the alerts). A milestone or concern the person's pick leaves out says `not picked` in `picked`;
one with no pick recorded says `no pick recorded`; one picked and not yet worked says `not started` in `status`.
Exit 0 written, 2 refused. Python standard library only."""
import contextlib
import hashlib
import io
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brief  # noqa: E402
import capability_views as cv  # noqa: E402
import flow_outputs as fo  # noqa: E402
import go  # noqa: E402
import register_layout as layout  # noqa: E402

VERSION = 1
FILE = "depth.json"
RECOMMENDATION = "depth-recommendation.json"  # the session's recommendation at the pick, per stage
KEYS = ("version", "register", "capability", "stop", "flows", "open_choice")

NOT_STARTED, DRAFT, REVIEWED = "not started", "draft", "reviewed"
PICKED, NOT_PICKED, NO_PICK = "picked", "not picked", "no pick recorded"
MILESTONES = ("Identified", "Mapped", "Measures defined", "Alerts defined", "Runbooks written")
# The ticks offered at the pick of how far each stage goes, in order, and the depth the furthest one ticked records
# (go.py --depth); no tick is mapped only. One place: depth.json offers them and go.py --answers reads them back.
DEPTH_OPTS = {"Measures defined": "measure", "Alerts defined": "alerting", "Runbooks written": "runbooks"}
FLOW_OPT = "Mapped"  # the one tick per flow at the go: this flow is mapped first
CONCERNS = (("measures", "measure", "MEASURES.md", "STAGE.html"), ("alerts", "alerting", "ALERT.md", "ALERT.html"),
            ("runbooks", "runbooks", "RUNBOOK.md", "RUNBOOK.html"))
REACHES = {"none": (), "measure": ("measure",), "alerting": ("measure", "alerting"),
           "runbooks": ("measure", "alerting", "runbooks")}


def quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a)


def table(reg, name):
    p = pathlib.Path(reg) / f"{name}.csv"
    return cv.read_csv(p) if p.is_file() else []


def capability_name(reg, o):
    if o and (o.get("capability") or {}).get("name"):
        return o["capability"]["name"]
    caps = table(reg, "capabilities")
    root = next((c for c in caps if not (c.get("parent") or "").strip()), caps[0] if caps else None)
    if root:
        return root.get("name")
    about = table(reg, "about")
    return about[0].get("system") if about else None


def stop_of(reg):
    """(the activity now, or None; the run's current stop as the person reads it: `no run record`, `draft complete`, or
    the phase now), from RUN.md."""
    if not (pathlib.Path(reg) / "RUN.md").is_file():
        return None, "no run record"
    st = brief.state(reg)
    if st is None:
        return None, "not started"
    current = st[0]
    return current, ("draft complete" if current is None else brief.short(current))  # a draft, never "finished"


def page(reg, rel):
    return rel if (pathlib.Path(reg) / rel).is_file() else None


def flow_measures(R, fid, stage_ids, step_ids):
    """Every measure of the flow, once by handle: on one of its steps or stages, on the flow, on its case, or on a
    part one of its steps uses."""
    parts = {p["subject_id"] for p in R["participation"] if p["step"] in step_ids}
    cases = {s.get("business_subject") for s in R["steps"] if s["step"] in step_ids}
    out = {}
    for m in R["measures"]:
        on = ((m.get("step") in step_ids) or (m.get("stage") in stage_ids) or (m.get("flow") == fid) or
              (not m.get("step") and not m.get("stage") and not m.get("flow") and
               (m.get("subject_id") in parts or m.get("subject_id") in cases)))
        if on and m.get("handle"):
            out.setdefault(m["handle"], m)
    return out


def measure_item(m):
    return {"handle": m["handle"], "measure": m.get("measure"), "level": fo.level(m), "layer": m.get("layer"),
            "counts": m.get("question_it_answers"), "exists_today": m.get("exists") == "yes",
            "taken_from": m.get("taken_from") or None, "counted_at": m.get("counted_at") or None}


def receipt_item(r, gapped):
    key = (r["element"], r["question"])
    state = "measured" if r["covered"] else "gapped" if key in gapped else "neither"
    return {"element": r["element"], "question": r["question"], "what": r["what"], "state": state,
            "gap_kind": gapped.get(key) if state == "gapped" else None, "measures": list(r["by"])}


def holes(VM, st):
    """The view questions of a stage and its steps not answered: each against its item, empty or gapped by kind."""
    import view_questions as vq
    out = []
    for q in [q for q in vq.QUESTIONS if q.startswith("stage:")]:
        got, kind = vq.status(VM, q, st["stage"])
        if got != "answered":
            out.append({"item": st.get("name"), "of": "stage", "question": q, "state": got, "gap_kind": kind})
    for x in st.get("_steps") or []:
        for q in [q for q in vq.QUESTIONS if q.startswith("step:")]:
            got, kind = vq.status(VM, q, x["step"])
            if got != "answered":
                out.append({"item": x.get("name"), "of": "step", "question": q, "state": got, "gap_kind": kind})
    return out


def alerts_reviewed(reg, scope):
    """Whether the person's go on the alerts covers the alerts as they are now."""
    r = (scope or {}).get("alerts_reviewed") or {}
    return bool(r) and r.get("alerts") == go.alert_fingerprint(reg)


def stage_record(reg, R, fid, st, depth, scope, rec, gapped, vm):
    sid = st["stage"]
    M = quiet(fo.build, R, fid, sid)
    pick = depth.get(sid, "none") if depth is not None else None
    reaches = REACHES.get(pick, ()) if pick is not None else None
    out = {"stage": sid, "name": st.get("name"),
           "order": int(st["order"]) if str(st.get("order", "")).isdigit() else None,
           "pick": pick if pick is not None else NO_PICK,
           "recorded_depth": pick,  # the depth go.py recorded (scope.json), or None: never read from the outputs
           "entry": st.get("entry"), "exit": st.get("exit"),
           "expects": [{"party": e.get("party"), "expectation": e.get("expectation")} for e in R["expectations"]
                       if e.get("stage") == sid],
           "steps": [{"step": s["step"], "name": s.get("name"), "right_outcome": s.get("right_outcome")}
                     for s in M["steps"]],
           "parts": [{"part": p, "name": fo.name(M, p),
                      "role": "carries a step" if any(p in M["performers"][s["step"]] for s in M["steps"])
                      else "needed by a step"} for p in M["parts"]],
           "holes": holes(*vm) if vm else []}
    concerns = {}
    for key, level, own_file, page_file in CONCERNS:
        picked = NO_PICK if reaches is None else (PICKED if level in reaches else NOT_PICKED)
        written = (pathlib.Path(reg) / f"stage-{sid}" / own_file).is_file()
        concerns[key] = {"status": DRAFT if written else NOT_STARTED, "picked": picked,
                         "page": page(reg, f"stage-{sid}/{page_file}") if written else None}
    reached = {m["handle"] for m in R["measures"] if m.get("handle") and any(s == sid for s, _ in fo.reach(R, m))}
    concerns["measures"].update(handles=sorted(reached), count=len(reached),
                                defined=[measure_item(m) for m in R["measures"] if m.get("handle") in reached],
                                items=[receipt_item(r, gapped) for r in rec if sid in r["stages"]])
    alerts = fo.stage_alerts(M)
    expect = {e.get("expectation_id"): e.get("expectation") for e in R["expectations"]}
    if concerns["alerts"]["status"] == DRAFT and alerts_reviewed(reg, scope) and pick in ("alerting", "runbooks"):
        concerns["alerts"]["status"] = REVIEWED
    concerns["alerts"].update(
        count=len(alerts),
        items=[{"handle": m["handle"], "measure": m.get("measure"), "watches": m.get("question_it_answers"),
                "guards": [expect[e] for e in re.split(r"\s*;\s*", m.get("expectation") or "") if e in expect],
                "signal": brief.signal_kind(m.get("layer")), "layer": m.get("layer"), "level": fo.level(m),
                "exists_today": m.get("exists") == "yes", "why": fo.basis(m)} for m in alerts],
        considered_not_proposed=sorted(reached - {m["handle"] for m in alerts}))
    entries, rows = [], []
    if concerns["runbooks"]["status"] == DRAFT:  # the check at the stage's depth
        errors, _ = quiet(fo.check, M, {"alerting": "alerts", "runbooks": "runbooks"}.get(pick, "all"))
        for m in alerts:
            why = [e for e in errors if e.startswith(f"measures.csv {m['handle']}:")]
            entries.append({"handle": m["handle"], "heading": fo.entry_heading(m), "passes": not why, "reasons": why})
        rows = [{"move": o["move"], "what": o["what"], "written": o["met"]}
                for mv in M["stage_moves"] for o in fo.required_failure_rows(M, mv)]
    concerns["runbooks"].update(count=len(entries), entries=entries, failure_rows=rows)
    out.update(concerns)
    return out


def flow_record(reg, R, f, o_flow, scope, scoped, VM):
    fid = f.get("flow_id")
    stages = sorted([s for s in R["stages"] if s.get("flow") == fid],
                    key=lambda s: int(s.get("order") or 0)) if fid else []
    depth = scope.get("depth") if scoped and isinstance((scope or {}).get("depth"), dict) else None
    aside = next((a.get("why") for a in table(reg, "set-aside") if (a.get("kind") or "").strip() == "other flow"
                  and (a.get("attaches_to") or "").strip() == fid), None) if fid else None
    out = {"flow": fid, "name": f.get("name"), "what": (o_flow or {}).get("what"), "case": f.get("case"),
           "starts": f.get("starts_at"), "ends": f.get("ends_at"), "serves": f.get("customer"),
           "identified": True, "mapped": bool(stages), "why_not_mapped": None if stages else (aside or "not mapped yet"),
           "pick": NO_PICK if depth is None else PICKED}
    rec = fo.receipt(R, fid) if stages else []
    gapped = fo.gap_rows(R, rec)[2] if stages else {}
    vf = next((x for x in (VM or {}).get("flows", []) if x.get("flow_id") == fid), None) if fid else None
    vm = {s["stage"]: (VM, s) for s in (vf or {}).get("_stages") or []}
    st = [stage_record(reg, R, fid, s, depth, scope, rec, gapped, vm.get(s["stage"])) for s in stages]
    out["stages"] = st
    stage_ids = {s["stage"] for s in stages}
    step_ids = {s["step"] for s in R["steps"] if s.get("stage") in stage_ids}
    ms = flow_measures(R, fid, stage_ids, step_ids) if stages else {}
    out["measures"] = {"count": len(ms), "exist_today": sum(1 for m in ms.values() if m.get("exists") == "yes"),
                       "items": [measure_item(m) for m in ms.values()],
                       "flow_items": [receipt_item(r, gapped) for r in rec if not r["stages"]]}

    def across(name, key):
        worked = [s for s in st if s[key]["status"] != NOT_STARTED]
        status = (NOT_STARTED if not worked else
                  REVIEWED if all(s[key]["status"] == REVIEWED for s in worked) else DRAFT)
        p = {s[key]["picked"] for s in st}
        picked = (NO_PICK if p <= {NO_PICK} else PICKED if PICKED in p else NOT_PICKED)
        return {"milestone": name, "status": status, "covers": ", ".join(s["name"] for s in worked) or None,
                "pages": [s[key]["page"] for s in worked if s[key]["page"]], "picked": picked}
    out["milestones"] = [
        {"milestone": "Identified", "status": DRAFT, "covers": "found by a first look at the system", "pages": []},
        {"milestone": "Mapped", "status": DRAFT if stages else NOT_STARTED,
         "covers": f"{len(stages)} stages, {len(step_ids)} steps" if stages else None,
         "pages": [p for p in ["views.html"] if stages and page(reg, p)]}] + [
        across(n, k) for n, k in (("Measures defined", "measures"), ("Alerts defined", "alerts"),
                                  ("Runbooks written", "runbooks"))]
    return out


def recommendation(reg):
    got = brief.load(pathlib.Path(reg), RECOMMENDATION)
    return got if isinstance(got, dict) else {}


def choice_id(stop, c):
    """A stable hash of what the person is asked: the stop (the run record's phase), the milestone, the task line,
    and each item's key, name, recommendation and options. Reasons, statuses and the add line's wording do not change it."""
    body = {"stop": stop, "milestone": c["milestone"], "task": c["task"],
            "items": [[i.get("key"), i["name"], i["recommended"], i.get("recommended_opt"), i["opts"]]
                      for i in c["items"]]}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def scoped_flow_id(R, scope):
    """The flow this run picked and mapped, by what the run recorded: the flow id recorded at the pick, else the
    flow of the stages the person's pick names, else the flow named at the go, else the one flow walked. Never a guess between
    two walked flows: the walk may name the flow afresh."""
    if not scope:
        return None
    if scope.get("flow_id") in {f["flow_id"] for f in R["flows"]}:
        return scope["flow_id"]
    of = {s["stage"]: s.get("flow") for s in R["stages"]}
    named = list(scope["depth"] if isinstance(scope.get("depth"), dict) else ()) + list(scope.get("stage_ids") or [])
    by_stage = {of[x] for x in named if x in of}
    if len(by_stage) == 1:
        return by_stage.pop()
    fid = next((f["flow_id"] for f in R["flows"] if scope.get("flow") and f.get("name") == scope["flow"]), None)
    if fid is None:
        walked = list(dict.fromkeys(s.get("flow") for s in R["stages"]))
        fid = walked[0] if len(walked) == 1 else None
    return fid


def flow_stages(R, fid):
    return sorted((s for s in R["stages"] if s.get("flow") == fid), key=lambda s: int(s.get("order") or 0))


def open_choice(reg, R, o, scope, current, stop):
    """The choice now waiting on the person, or None: at the go, which flow is mapped first; at the pick, how far each
    stage goes; at the review, the alerts proposed."""
    if current == 0 and o:
        rec = o.get("recommendation") or {}
        items = [{"key": f.get("name"), "name": f.get("name"), "recommended": f.get("name") == rec.get("flow"),
                  "reason": rec.get("why") if f.get("name") == rec.get("flow") else f.get("what"),
                  "status": "proposed", "opts": [FLOW_OPT]} for f in o.get("flows") or []]
        c = {"milestone": "Mapped", "task": "Choose the flow to map first", "items": items,
             "add": "Add a flow the first look did not find"}
    elif current == brief.DEPTH_PICK:
        said, items = recommendation(reg), []
        for s in flow_stages(R, scoped_flow_id(R, scope)):
            r = said.get(s["stage"]) or {}
            d = r.get("depth")
            items.append({"key": s["stage"], "name": s.get("name"),
                          "recommended": None if d is None else d != "none",
                          "recommended_opt": next((k for k, v in DEPTH_OPTS.items() if v == d), None),
                          "reason": r.get("why"), "status": "proposed", "opts": list(DEPTH_OPTS)})
        c = {"milestone": "Measures defined", "task": "Pick how far each stage goes", "items": items,
             "add": "Add a stage the map missed"}
    elif current == brief.REVIEW:
        fid, depth, shown = scoped_flow_id(R, scope), (scope or {}).get("depth") or {}, {}
        for s in flow_stages(R, fid):
            if depth and depth.get(s["stage"]) not in ("alerting", "runbooks"):
                continue
            for m in fo.stage_alerts(quiet(fo.build, R, fid, s["stage"])):
                shown.setdefault(m["handle"], m)
        items = [{"key": h, "name": m.get("measure"), "recommended": True, "reason": fo.basis(m),
                  "status": "proposed", "opts": ["Accept", "Reject"]} for h, m in shown.items()]
        c = {"milestone": "Alerts defined", "task": "Review the alerts proposed", "items": items,
             "add": "Make any other measure an alert"}
    else:
        return None
    if not c["items"]:  # an empty choice would record a pick the person was never shown: none is offered
        return None
    c["choice_id"] = choice_id(current, c)  # the phase, not its wording: rewording the status line moves no page
    return c


def build(reg):
    """depth.json's content for the register at `reg`."""
    reg = pathlib.Path(reg)
    R = fo.load(reg)
    o = brief.load(reg, layout.ORIENTATION)
    scope = go.load(reg)
    current, stop = stop_of(reg)
    VM = None
    if R["stages"]:
        import view_questions as vq
        VM = quiet(vq.load, reg)
    scoped = scoped_flow_id(R, scope)
    o_flows = {f.get("name"): f for f in (o or {}).get("flows") or []}
    flows = [flow_record(reg, R, f, o_flows.get(f.get("name")), scope, f["flow_id"] == scoped, VM) for f in R["flows"]]
    known = {f.get("name") for f in R["flows"]}
    flows += [flow_record(reg, R, {"name": n}, of, scope, False, None) for n, of in o_flows.items() if n not in known]
    return {"version": VERSION, "register": reg.name, "capability": capability_name(reg, o), "stop": stop,
            "flows": flows, "open_choice": open_choice(reg, R, o, scope, current, stop)}


def write(reg):
    """depth.json, then the home screen drawn again from it where one is drawn already, so a page open on it
    reloads with the choice now open."""
    got = build(reg)
    (pathlib.Path(reg) / FILE).write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                          newline="\n")
    import home  # imports this module, so here, not at the top
    if (pathlib.Path(reg) / home.FILE).is_file():
        try:
            home.write(reg)
        except Exception as e:  # noqa: BLE001 - depth.json stands; only the page is behind
            print(f"WARNING: {home.FILE} not drawn again ({type(e).__name__}: {e}); run python home.py \"{reg}\"",
                  file=sys.stderr)
    return got


def write_quietly(reg):
    """depth.json written where a step of the run has just changed what it says (a stop rendered, a pick recorded).
    The step's own work stands if it cannot be written; the reason goes to stderr, naming the file."""
    try:
        return write(reg)
    except Exception as e:  # noqa: BLE001 - the message or the record is done; only the page's data is missing
        print(f"WARNING: {FILE} not written ({type(e).__name__}: {e}); run python depth.py \"{reg}\"",
              file=sys.stderr)
        return None


def record_recommendation(reg, text):
    """The session's recommendation at the pick, per stage: `ST2=measure: why; ST3=runbooks: why`."""
    known = {(r.get("stage") or "").strip() for r in table(reg, "stages")} - {""}
    got = {}
    for part in [p for p in re.split(r"\s*;\s*", text or "") if p.strip()]:
        head, _, why = part.partition(":")
        sid, _, d = head.partition("=")
        sid, d = sid.strip(), d.strip().lower()
        if sid not in known:
            return f"not a stage in stages.csv: {sid or '(none)'}"
        if d not in go.DEPTHS:
            return f"{sid}: {d or 'nothing'} is not one of {', '.join(go.DEPTHS)}"
        if not why.strip():
            return f"{sid}: give a one-line reason after a colon"
        got[sid] = {"depth": d, "why": why.strip()}
    if not got:
        return "--recommend names no stage"
    (pathlib.Path(reg) / RECOMMENDATION).write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n",
                                                    encoding="utf-8", newline="\n")
    return got


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args, recommend = list(argv), None
    if "--recommend" in args:
        i = args.index("--recommend")
        recommend = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    if len(args) != 1 or not pathlib.Path(args[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    reg = pathlib.Path(args[0])
    if recommend is not None:
        got = record_recommendation(reg, recommend)
        if isinstance(got, str):
            print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
            return 2
    d = write(reg)
    c = d["open_choice"]
    print(f"Written: {FILE} ({len(d['flows'])} flows; open choice: "
          f"{c['task'] + ', ' + c['choice_id'] if c else 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
