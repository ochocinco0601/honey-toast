"""One business flow of one register, as the three objects the viewer page draws it from: DATA, EXTRA and FLOWDRAW.

Made to read any register: a missing CSV reads as no rows, a missing
column as "", step ids sort as numbers where they are numbers. The flow's stages, steps and parts come from the stage
kit's own model (capability_views, one_canvas), from the copy of it carried in kit_copy/.
"""
import csv
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUSINESS = ("business health", "business impact")
COMPONENT = ("application", "technology", "agentic")  # measures that sit on a component's row
CHAIN_N = 8
OTHER_TEAMS = (3, 4, 7)  # Instrumented, Dashboards built, Team prepared

KIT_DIR = HERE / "kit_copy"  # the stage kit's model code, carried with the viewer (kit_copy/FROM.txt)
cv = oc = home = None


def load_kit():
    """The stage kit's model code, from the copy carried in kit_copy/ (see kit_copy/FROM.txt), never an installed kit."""
    global cv, oc, home
    if cv is not None:
        return
    sys.path.insert(0, str(KIT_DIR))
    import capability_views  # noqa: E402
    import one_canvas  # noqa: E402
    import home as home_mod  # noqa: E402  (the milestones: COLS and FILLED_WHEN)
    cv, oc, home = capability_views, one_canvas, home_mod


def short_name(row):
    """A shorter name for tight spaces: a short_name column if the register carries one, without its "proposed:"
    mark; otherwise "", and the full name stands."""
    v = ((row or {}).get("short_name") or "").strip()
    return v[len("proposed:"):].strip() if v.lower().startswith("proposed:") else v


class Row(dict):
    def __missing__(self, key):
        return ""


def rows(reg, name):
    p = Path(reg) / name
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return [Row({k: (v or "") for k, v in r.items() if k is not None}) for r in csv.DictReader(f)]


def nkey(s):
    s = str(s).strip()
    return (0, int(s), "") if s.isdigit() else (1, 0, s)


def to_int(s):
    s = str(s or "").strip()
    return int(s) if s.isdigit() else None


def ops(cell):
    return {o.strip() for o in (cell or "").split(";") if o.strip()}


def way_words(text):
    """A stage's entry or exit cell, cleaned for reading: no "implicit:", no lifecycle codes such as (L03) or L01."""
    t = re.sub(r"\bimplicit:\s*", "", text or "")
    t = re.sub(r"\s*\((?:[^()]*\bL\d+[^()]*)\)", "", t)
    t = re.sub(r"\s*\bL\d+(?:\s*[-–]\s*L\d+)?\b", "", t)
    t = re.sub(r"\s+", " ", t).strip(" ;,.:")
    return t[:1].upper() + t[1:]


def cut_to_flow(reg, flow):
    """Keep only the one flow, its stages and their steps, so the kit's model holds that flow alone."""
    def keep(name, ok):
        p = reg / name
        if not p.exists():
            return []
        with open(p, encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            kept, fields = [x for x in r if ok(x)], r.fieldnames
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fields)
            w.writeheader()
            w.writerows(kept)
        return kept
    keep("flows.csv", lambda x: x.get("flow_id") == flow)
    stages = {x["stage"] for x in keep("stages.csv", lambda x: x.get("flow") == flow)}
    keep("steps.csv", lambda x: x.get("stage") in stages)


def kit_model(reg, flow):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "reg"
        shutil.copytree(reg, work, ignore=shutil.ignore_patterns("*.html", "*.png", "out", "pages"))
        cut_to_flow(work, flow)
        return oc.number_steps(oc.prune(cv.model(cv.load(work))))


def model(reg, flow):
    """The flow as the page draws it (its stages, steps, components and measures), read from any register."""
    reg = Path(reg)
    M = kit_model(reg, flow)
    label = M["_step_label"]
    f = M["flows"][0]
    moves = {r["move_id"]: r for r in rows(reg, "lifecycle.csv")}
    life = {}
    for s in rows(reg, "steps.csv"):
        ids = [i for i in re.findall(r"L\d+", s["source"]) if i in moves]
        if ids:
            life[s["step"]] = {"from": [moves[i]["from_state"] for i in ids], "to": moves[ids[0]]["to_state"]}

    names, notes = {}, []
    reg_stages = {r["stage"]: r for r in rows(reg, "stages.csv")}
    step_rows = {r["step"]: r for r in rows(reg, "steps.csv")}
    codes = lambda sid_: set(re.findall(r"L\d+", step_rows.get(sid_, Row())["source"]))
    main_path = lambda sid_: any(moves.get(c, {}).get("path") == "main" and moves[c].get("to_state", "").strip()
                                 for c in re.findall(r"L\d+", step_rows.get(sid_, Row())["source"])[:1])
    stages, wires, drawn_steps, part_copy, step_stage = [], [], set(), {}, {}
    for st in f["_stages"]:
        gid = st["stage"]
        items = [{"id": f"m-s-{x['step']}", "step": x["step"], "name": x.get("name", ""), "label": label.get(x["step"], "")}
                 for x in st["_steps"]]
        for x in items:
            drawn_steps.add(x["step"])
            step_stage[x["step"]] = gid
            x["kind"] = ("step" if x["label"].startswith("Process step") else
                         "ok" if x["label"] == "Expected outcome" else "fail")
        for x in items:
            n = x["label"].replace("Process step ", "") if x["kind"] == "step" else ""
            names[x["id"]] = (f"Process step {n}: " if n else
                              ("Expected outcome: " if x["kind"] == "ok" else "Other outcome: ")) + x["name"]
            x["n"] = n
        parts, sp, deps, _ = oc.stage_chain(M, st)
        part_boxes = []
        for p in parts:
            pid = f"m-p-{gid}-{p}"
            part_copy.setdefault(p, []).append(pid)
            subj = M["subj"][p]
            part_boxes.append({"id": pid, "sid": p, "name": subj.get("name", p), "kind": cv.kind_label(M, subj)})
        wires += [[f"m-s-{s}", f"m-p-{gid}-{p}"] for s, p in sp]
        names[f"m-g-{gid}"] = f"Stage {st.get('order')}: {st.get('name', '')}"
        # the stage read as a way in, its process steps, and its ways out
        eid, entry = f"m-in-{gid}", reg_stages.get(gid, Row())["entry"]
        names[eid] = "Way in: " + way_words(entry)
        real = [x for x in items if x["kind"] == "step"]
        exits = []
        if not real:
            # a stage always shows its work. With no act, each row whose lifecycle move ends the stage on the
            # main path is drawn as the stage's process step N.1; the stage's recorded exits become its ways out
            real = [x for x in items if x["kind"] == "ok" and main_path(x["step"])]
            if not real and items:
                # no lifecycle to tell which: the expected outcome (else the first row) stands as the stage's step
                real = [next((x for x in items if x["kind"] == "ok"), items[0])]
                notes.append(f"stage {gid}: no process step recorded; its outcome '{real[0]['name']}' is drawn as its step")
            for i, x in enumerate(real, 1):
                x["kind"], x["n"] = "step", f"{st.get('order')}.{i}"
                names[x["id"]] = f"Process step {x['n']}: {x['name']}"
            rows_codes = set().union(*[codes(x["step"]) for x in items if x not in real]) if items else set()
            raw = reg_stages.get(gid, Row())["exit"]
            for k, part in enumerate([q for q in re.split(r";\s*or\s+", raw) if q.strip()] if real and moves else []):
                cs = set(re.findall(r"L\d+", part))
                if cs & rows_codes:
                    continue  # an exit an Other outcome row already stands for keeps that row, with its measures
                is_main = any(moves.get(c, {}).get("path") == "main" for c in cs)
                exits.append({"id": f"m-out-{gid}-{k + 1}", "kind": "ok" if is_main else "fail",
                              "name": way_words(part), "full": part.strip(), "exit": True})
                names[exits[-1]["id"]] = "Way out: " + way_words(part)
            exits.sort(key=lambda x: x["kind"] != "ok")
        outs = [x for x in items if x not in real]
        outs.sort(key=lambda x: x["kind"] != "ok")
        ways = exits + [{k: x[k] for k in ("id", "kind", "name")} for x in outs]
        stages.append({"id": f"m-g-{gid}", "num": str(st.get("order") or len(stages) + 1), "name": st.get("name", ""),
                       "stepcol": [{k: x[k] for k in ("id", "kind", "n", "name")} for x in real],
                       "ways_out": ways, "parts": part_boxes,
                       "way_in": {"id": eid, "words": way_words(entry), "full": entry}})
    names[f"m-f-{flow}"] = f"Intended flow: {f.get('name', '')}"
    wire_set = {tuple(w) for w in wires}

    subjects = {r["subject_id"]: r for r in rows(reg, "subjects.csv")}
    part_rows = rows(reg, "participation.csv")
    alert_rows = rows(reg, "alerts.csv")
    alerts = {a["handle"]: a["alert"] for a in alert_rows if a["alert"].strip().lower().startswith("yes")}
    ms, unplaced = [], []
    for m in rows(reg, "measures.csv"):
        if (m["flow"] or m["for_flow"]) != flow:
            continue
        comp = subjects.get(m["taken_at"], Row())["name"] if m["taken_at"] else ""
        if not comp and m["layer"] in COMPONENT:
            comp = subjects.get(m["subject_id"], Row())["name"]
        rec = {"h": m["handle"], "name": m["measure"], "q": m["question_it_answers"], "yes": m["exists"] == "yes",
               "layer": m["layer"], "comp": comp, "defect": m["defect"], "form": m["form"],
               "rec": m["taken_from"], "sig": m["instrumented_signature"], "at": m["counted_at"],
               "ref": m["source_ref"], "exp": m["exporter_name"], "watched": m["watched"],
               "alert": alerts.get(m["handle"], "none" if (reg / "alerts.csv").exists() else ""), "how": m["counted_how"],
               "op": m["operation"], "steps": [], "subject": m["subject_id"], "step": m["step"], "stage": m["stage"]}
        if m["layer"] in BUSINESS:
            if m["step"]:
                rec.update(el=f"m-s-{m['step']}", steps=[m["step"]])
                ok = m["step"] in drawn_steps
            elif m["stage"]:
                rec.update(el=f"m-g-{m['stage']}")
                ok = f"m-g-{m['stage']}" in names
            else:
                rec.update(el=f"m-f-{flow}")
                ok = True
        elif m["layer"] in COMPONENT:
            pid = m["subject_id"]
            ok = pid in part_copy
            served = sorted({p["step"] for p in part_rows if p["subject_id"] == pid and p["step"] in drawn_steps
                             and ops(m["operation"]) & ops(p["operation"])}, key=nkey) if m["operation"] else []
            line = next(((f"m-s-{s}", f"m-p-{step_stage[s]}-{pid}") for s in served
                         if (f"m-s-{s}", f"m-p-{step_stage[s]}-{pid}") in wire_set), None)
            rec.update(steps=served, el=part_copy.get(pid, [None])[0])
            if line:
                rec.update(frm=line[0], el=line[1])
        else:
            ok = False
        if ok:
            ms.append(rec)
        else:
            unplaced.append(m["handle"])
    about = rows(reg, "about.csv")
    return {"flow": f.get("name", ""), "flow_id": flow, "system": about[0]["system"] if about else "",
            "stages": stages, "m": ms, "unplaced": unplaced, "wires": wires, "label": names, "notes": notes}


def data_of(M):
    """window.DATA: the flow's stages and its measures."""
    keys = ("h", "name", "q", "layer", "yes", "el", "comp", "defect", "form")
    return {"stages": [{k: s[k] for k in ("id", "num", "name", "stepcol", "ways_out", "parts", "way_in")} for s in M["stages"]],
            "measures": [{k: m[k] for k in keys} for m in M["m"]], "wires": M["wires"], "label": M["label"]}


def extra_of(M):
    """window.EXTRA: per handle, the fields of the measure's card that the register holds."""
    out = {}
    for m in M["m"]:
        others = [f"m-s-{s}" for s in m["steps"]]
        others = [i for i in others if i != m["el"] and i in M["label"]]  # the other process steps and outcomes it serves, without the one it sits on
        out[m["h"]] = {"rec": m["rec"], "sig": m["sig"], "at": m["at"], "ref": m["ref"], "exp": m["exp"],
                       "watched": m["watched"], "alert": m["alert"], "form": m["form"],
                       "also": [M["label"][i] for i in others], "src": "", "code": "", "how": m["how"]}
    return out


def flowdraw_of(reg, flow, M):
    """window.FLOWDRAW: the drawing's data. Returns (FLOWDRAW, notes)."""
    reg = Path(reg)
    subj = {r["subject_id"]: r for r in rows(reg, "subjects.csv") if r["kind"] == "element"}
    rels = [r for r in rows(reg, "subjects.csv") if r["kind"] == "relationship" and r["from_id"] in subj and r["to_id"] in subj]
    part = rows(reg, "participation.csv")
    notes = []

    steps = [(si, x) for si, st in enumerate(M["stages"]) for x in st["stepcol"]]
    data_steps = []
    for si, x in steps:
        sid = x["id"].replace("m-s-", "")
        involve = {}
        for p in part:
            if p["step"] == sid and p["subject_id"] in subj and involve.get(p["subject_id"]) != "performs":
                involve[p["subject_id"]] = p["involvement"]
        ordered = sorted((r for r in rels if sid in [h.strip() for h in r["step_hint"].split(";")]),
                         key=lambda r: to_int(r["sequence"]) if to_int(r["sequence"]) is not None else 99)
        edges = [[r["from_id"], r["to_id"], to_int(r["sequence"])] for r in ordered]
        for a, b, _ in edges:
            involve.setdefault(a, "supports")
            involve.setdefault(b, "supports")
        targets = {b for _, b, _ in edges}
        roots = [n for n in involve if n not in targets and (any(e[0] == n for e in edges) or not edges)]
        roots.sort(key=lambda n: involve[n] != "performs")
        outside = not involve and not M["stages"][si]["parts"]
        data_steps.append({"id": x["id"], "sid": sid, "stage": si, "n": x["n"], "involve": involve, "edges": edges,
                           "roots": roots, "outside": outside})

    lanes = []

    def visit(n, edges, seen=()):
        if n not in lanes:
            lanes.append(n)
        for a, b, _ in edges:
            if a == n and b not in seen:
                visit(b, edges, seen + (n,))
    for d in data_steps:
        for r in d["roots"]:
            visit(r, d["edges"])
        for n in d["involve"]:
            if n not in lanes:
                lanes.append(n)
    band = {n: "external" if subj[n]["level"] == "external dependency" else subj[n]["band"] for n in lanes}
    lanes.sort(key=lambda n: {"business": 0, "application": 1, "technology": 2}.get(band[n], 3))
    LN = {n: i for i, n in enumerate(lanes)}

    place = {}
    stage_ix = {s["id"].replace("m-g-", ""): i for i, s in enumerate(M["stages"])}
    out_stage = {o["id"].replace("m-s-", ""): i for i, s in enumerate(M["stages"]) for o in s["ways_out"]}
    sid_ix = {d["sid"]: i for i, d in enumerate(data_steps)}
    for m in M["m"]:
        n, st, sg, h = m["subject"], m["step"], m["stage"], m["h"]
        if n not in LN:
            if st in sid_ix:
                place[h] = [["step", sid_ix[st]]]
            elif st and st in out_stage:  # on a way out: no box on the drawing; the panel lists it under its stage
                place[h] = [["out", out_stage[st]]]
            elif sg in stage_ix:
                place[h] = [["stage", stage_ix[sg]]]
            else:
                place[h] = [["flow"]]
            continue
        ln = LN[n]
        if st:
            place[h] = [["cell", sid_ix[st], ln]] if st in sid_ix else [["lane", ln]]
            continue
        want = ops(m["op"])
        hits = sorted({p["step"] for p in part if p["subject_id"] == n and want & ops(p["operation"])}, key=nkey)
        cols = [sid_ix[x] for x in hits if x in sid_ix]
        place[h] = [["cell", c, ln] for c in cols] or [["lane", ln]]

    flow_row = next((r for r in rows(reg, "flows.csv") if r["flow_id"] == flow), Row())
    stage_row = {r["stage"]: r for r in rows(reg, "stages.csv")}
    step_row = {r["step"]: r for r in rows(reg, "steps.csv")}

    def named(row, full):
        full = full or row["name"]
        return {"full": full, "short": short_name(row) or full}
    gid = lambda s: s["id"].replace("m-g-", "")
    out = {
        "flow": {"id": flow, **named(flow_row, flow_row["name"] or M["flow"])},
        "stages": [{"id": s["id"], "num": s["num"], **named(stage_row.get(gid(s), Row()), stage_row.get(gid(s), Row())["name"] or s["name"])}
                   for s in M["stages"]],
        "lanes": [{"sid": n, "label": subj[n]["name"].split(" (")[0] or n, "band": band[n]} for n in lanes],
        "steps": [{"id": d["id"], "stage": d["stage"], "n": d["n"], "outside": d["outside"],
                   **named(step_row.get(d["sid"], Row()), step_row.get(d["sid"], Row())["name"]),
                   "marks": [[LN[n], v == "performs"] for n, v in d["involve"].items()],
                   "edges": [[LN[a], LN[b], q] for a, b, q in d["edges"]],
                   "roots": [LN[r] for r in d["roots"]]} for d in data_steps],
        "place": place,
    }
    return out, notes


def milestones(reg, flows_with):
    """Each flow's 8 milestones: 2 done, 1 under way, 0 not yet. From depth.json when the register has one."""
    reg = Path(reg)
    cols = [c[0] for c in home.COLS]
    filled = {cols[k]: v for k, v in home.FILLED_WHEN.items()}
    dj = {}
    p = reg / "depth.json"
    if p.exists():
        try:
            dj = {f["flow"]: f for f in json.loads(p.read_text(encoding="utf-8")).get("flows", [])}
        except (ValueError, KeyError, TypeError, AttributeError):
            dj = {}
    alerts = {a["handle"] for a in rows(reg, "alerts.csv") if a["alert"].strip().lower().startswith("yes")}
    alert_any = {a["handle"] for a in rows(reg, "alerts.csv")}
    out = {}
    for fid, info in flows_with.items():
        if fid in dj:
            st = {m.get("milestone"): (m.get("status") or "not started") for m in dj[fid].get("milestones", [])}
            ch = []
            for i, c in enumerate(cols):
                s = st.get(c, "not started")
                ch.append(0 if i in OTHER_TEAMS else 2 if s in filled.get(c, ()) else 0 if s == "not started" else 1)
            # never contradict what the page shows: measures (or alert rows) on screen are at least under way
            if info["measures"] and ch[2] == 0:
                ch[2] = 1
            if alert_any & set(info["measures"]) and ch[5] == 0:
                ch[5] = 1
        else:
            ch = [2, 2 if info["stages"] else 0, 2 if info["measures"] else 0, 0, 0,
                  2 if alerts & set(info["measures"]) else 0, 0, 0]
        out[fid] = ch
    return out


def measures_of(reg, flow):
    return [m["handle"] for m in rows(reg, "measures.csv") if (m["flow"] or m["for_flow"]) == flow]


def first_sentence(t):
    t = (t or "").strip()
    m = re.match(r"(.+?[.!?])(\s|$)", t)
    return m.group(1) if m else t


def register(reg):
    """Everything the viewer shows of one register. Never raises for one bad flow: its reason is in 'error'."""
    load_kit()
    reg = Path(reg)
    about = rows(reg, "about.csv")
    name = about[0]["system"] if about and about[0]["system"] else ""
    if not name and (reg / "depth.json").exists():
        try:
            name = json.loads((reg / "depth.json").read_text(encoding="utf-8")).get("capability", "")
        except ValueError:
            pass
    flows_rows = rows(reg, "flows.csv")
    stage_flows = {r["flow"] for r in rows(reg, "stages.csv")}
    info = {r["flow_id"]: {"stages": r["flow_id"] in stage_flows, "measures": measures_of(reg, r["flow_id"])} for r in flows_rows}
    chains = milestones(reg, info)
    flows, problems = [], []
    for r in sorted(flows_rows, key=lambda r: nkey(r["flow_id"].lstrip("F"))):
        fid = r["flow_id"]
        fl = {"id": fid, "name": r["name"] or fid, "short": short_name(r) or r["name"] or fid, "chain": chains[fid],
              "data": None, "extra": None, "flowdraw": None, "error": ""}
        if info[fid]["stages"]:
            try:
                M = model(reg, fid)
                if not M["stages"]:
                    raise ValueError("the kit's model holds no stage for it")
                fd, notes = flowdraw_of(reg, fid, M)
                if not fd["steps"] or not fd["lanes"]:
                    raise ValueError("no process step or no component to draw")
                fl.update(data=data_of(M), extra=extra_of(M), flowdraw=fd)
                if M["unplaced"]:
                    problems.append(f"{reg.name} {fid}: {len(M['unplaced'])} measure(s) not placed on the drawing "
                                    f"({', '.join(M['unplaced'][:8])}{'...' if len(M['unplaced']) > 8 else ''})")
                problems += [f"{reg.name} {fid}: {n}" for n in M["notes"] + notes]
            except Exception as e:  # noqa: BLE001  one flow that cannot be drawn never stops the page
                fl["error"] = f"{type(e).__name__}: {e}"
                problems.append(f"{reg.name} {fid}: not drawn: {fl['error']}")
        flows.append(fl)
    return {"register": reg.name, "name": name or reg.name, "what": first_sentence(about[0]["what_it_is"]) if about else "",
            "flows": flows}, problems
