"""The views of one capability as one canvas: the map drawn once, with its panels beside it.

    python -I one_canvas.py REGISTER OUT.html

The kit's page of the capability; it reuses capability_views.py for reading, checking and drawing the map. The map is drawn
once with every stage opened; clicking a box opens its panels. Standard library only,
no network.
"""
import json
import pathlib
import html
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import capability_views as cv  # noqa: E402
import flow_outputs as fo  # noqa: E402
import step_sequence as ss  # noqa: E402
import part_inside as pi  # noqa: E402
import stage_flow_views as sfv  # noqa: E402

NS = "not stated"
FILE = re.compile(r"[\w-]+/[\w./-]+|\b\w+\.(?:java|js|ts|go|py|cs|razor|sql|properties|ya?ml|json|md|xml|html|proto)\b")


# ---------------------------------------------------------------- steps the map leaves out

def evidenced(step):
    """Code, document or person evidence for a step: a cited line, a named file, an asked person, a section."""
    return any(cv.CITE.search(v) or FILE.search(v) for k, v in step.items() if isinstance(v, str) and not k.startswith("_"))


def number_steps(M):
    """Each stage's steps in reading order, labelled as every output labels them (flow_outputs.step_labels). Returns M."""
    M["_step_label"] = fo.step_labels(M["R"]["stages"], M["R"]["steps"], ss.lifecycle(M))
    order = list(M["_step_label"])
    for st in [s for f in M["flows"] for s in f["_stages"]]:
        st["_steps"] = sorted(st["_steps"], key=lambda x: order.index(x["step"]) if x["step"] in order else len(order))
    return M


def prune(M):
    """A step nothing performs and whose only basis is a reference model is not drawn; a stage left with no step
    goes with it. Any code, document or person evidence keeps the step, drawn as not assessed. Returns M."""
    out = [sid for sid, st in M["step"].items() if not cv.carried(st) and not evidenced(st)]
    M["_left_out"] = [(sid, M["step"][sid].get("name", "")) for sid in out]
    M["_left_out_stage_of"] = {sid: M["step"][sid].get("stage") for sid in out}
    M["_left_out_stages"] = []
    for sid in out:
        st = M["step"].pop(sid)
        stage = M["stage"].get(st.get("stage"))
        if stage:
            stage["_steps"] = [x for x in stage["_steps"] if x["step"] != sid]
    emptied = {M["R"]["steps"][i].get("stage") for i in range(len(M["R"]["steps"])) if M["R"]["steps"][i].get("step") in out}
    for k in [k for k in emptied if k in M["stage"] and not M["stage"][k]["_steps"]]:
        M["_left_out_stages"].append((k, M["stage"].pop(k).get("name", "")))
        for f in M["flows"]:
            f["_stages"] = [x for x in f["_stages"] if x["stage"] != k]
    return M


# ---------------------------------------------------------------- one flow's view

# ---------------------------------------------------------------- what each lens reads, computed here

def layers(M):
    return [r["layer"] for r in M["R"]["method"]["layers"]]


def status(ms, layer=None):
    ms = [m for m in ms if layer is None or m["_layer"] == layer]
    emitted = [m for m in ms if m.get("exists") == "yes"]
    if any(not (m.get("defect") or "").strip() for m in emitted):
        return "measured"
    if emitted:
        return "defective"
    return "proposed" if ms else "none"


def relied_on(M):
    """Per step, the parts a click on it lights: what the step relies on."""
    ch = cv.chain(M)
    return {sid: {p[2:] for p in ch.get("s:" + sid, ()) if p.startswith("p:")} for sid in M["step"]}


def node_parts(M, rel):
    """Per stage and flow box, the parts its steps rely on."""
    out = {}
    for f in M["flows"]:
        for st in f["_stages"]:
            out["g:" + st["stage"]] = set().union(*[rel.get(x["step"], set()) for x in st["_steps"]])
        out["f:" + f["flow_id"]] = set().union(*[out["g:" + st["stage"]] for st in f["_stages"]])
    return out


def op_steps(M, pid, m):
    """The steps the part performs with an operation the measure names, in step order."""
    mo = ops(m.get("operation")) - {"reply"}
    hit = {p["step"] for p in M["R"]["participation"] if p.get("subject_id") == pid and p.get("step") in M["step"]
           and mo & ops(p.get("operation"))} if mo else set()
    return sorted(hit, key=lambda x: (len(x), x))


def part_measures(M, pid):
    """A part's measures, as its panel and its readiness row list them: the model's own list, calls to it included,
    by layer, then by the first step they serve, so a number means one measure in both."""
    order = {L: i for i, L in enumerate(layers(M))}
    key = lambda m: (order.get(m["_layer"], len(order)), [(len(x), x) for x in op_steps(M, pid, m)[:1]])
    return sorted((m for m in M["m_part"].get(pid, []) if m.get("measure")), key=key)


def relied_measures(M, pid):
    """What a step relying on the part is shown: its measures not scoped to one step or stage, which a step lists as its own."""
    return [m for m in part_measures(M, pid) if not m.get("stage") and not m.get("step")]


def ops(v):
    return {o.strip() for o in (v or "").split(";") if o.strip()}


def at_operation(M):
    """Per step, a part's measures that name an operation the part performs that step with: the step's own."""
    out = {}
    for m in M["R"]["measures"]:
        mo = ops(m.get("operation"))
        if not mo or m.get("step") or m.get("stage") or not m.get("measure"):
            continue
        for p in M["R"]["participation"]:
            if p.get("subject_id") == m.get("subject_id") and p.get("step") in M["step"] and mo & ops(p.get("operation")):
                out.setdefault(p["step"], {})[m.get("handle")] = dict(m, _layer=cv.layer_of(M["R"], m.get("layer")) or "")
    return {k: list(v.values()) for k, v in out.items()}


def own_at_step(M, sid, at_op=None):
    """A step's own measures: those set on the step, then a part's measures for the operation it performs the step with."""
    at_op = at_operation(M) if at_op is None else at_op
    mine = list(M["m_at_step"].get(sid, []))
    seen = {m.get("handle") for m in mine}
    return mine + [m for m in at_op.get(sid, []) if m.get("handle") not in seen]


def status_with(own, via, layer=None):
    """A box's own state; where it has none, 'via' when a part it relies on has a measure there."""
    s = status(own, layer)
    return "via" if s == "none" and status(via, layer) != "none" else s


def with_any(per_layer, own, via=()):
    """The box's shade under "any layer": misleading in any one layer outranks measured in another."""
    worst = "defective" if "defective" in per_layer.values() else status_with(own, list(via))
    return dict(per_layer, any=worst)


def coverage(M):
    """Per drawn box, per layer: measured (the code emits it), proposed (on record, not emitted), via (only on a part
    the box relies on) or nothing proposed."""
    out, Ls = {}, layers(M)
    rel = relied_on(M)
    via_of = lambda pids, skip=(): [m for p in pids for m in relied_measures(M, p) if m.get("handle") not in skip]
    at_op = at_operation(M)
    for sid in M["step"]:
        ms = own_at_step(M, sid, at_op)
        via = via_of(rel[sid], {m.get("handle") for m in ms})
        out["s:" + sid] = with_any({L: status_with(ms, via, L) for L in Ls}, ms, via)
    for s in M["comps"] + M["deps"] + M["persons"] + [k for ks in M["dep_parts"].values() for k in ks]:
        ms = M["m_part"].get(s["subject_id"], [])
        out["p:" + s["subject_id"]] = with_any({L: status(ms, L) for L in Ls}, ms)
    parts = node_parts(M, rel)
    for key, ms in node_measures(M).items():
        via = via_of(parts.get(key, ()))
        out[key] = with_any({L: status_with(ms, via, L) for L in Ls}, ms, via)
    return out


def node_measures(M):
    """The measures on each stage as a whole (stage set, no step) and each flow as a whole (business subject, no stage, no step)."""
    R = M["R"]
    lay = lambda m: dict(m, _layer=cv.layer_of(R, m.get("layer")) or "")
    business = {sid for sid, x in M["subj"].items() if x.get("band") == "business"}
    one_flow = len(M["flows"]) == 1
    out = {}
    for f in M["flows"]:
        out["f:" + f["flow_id"]] = [lay(m) for m in R["measures"] if not m.get("stage") and not m.get("step")
                                    and m.get("subject_id") in business and (m.get("flow") == f["flow_id"] or (one_flow and not m.get("flow")))]
        for st in f["_stages"]:
            out["g:" + st["stage"]] = [lay(m) for m in R["measures"] if m.get("stage") == st["stage"] and not m.get("step")]
    return out


# ---------------------------------------------------------------- the page

def the_map(M, mid="c", what="every flow", fold=None):
    """The map with everything open, or folded (fold: see cv.business_map) to the thing in focus."""
    parts, bottom, _ = cv.business_map(M, "map", mid, opened=set(M["stage"]), calls="click", key=False, fold=fold)
    said = ("every stage opened into its steps, and every part that carries one" if fold is None else
            "folded: the thing in focus open, everything else one line that says how much it holds")
    svg = cv.wrap_svg(f"{M['system']}: {what}, {said}",
                      cv.VW, bottom + 10, [cv.defs(mid)] + parts,
                      "", "map fade-links")
    svg = re.sub(r'<a href="[^"]*"[^>]*>(.*?)</a>', r"\1", svg, flags=re.S)  # the page stays self-contained
    for old, new in (("owner, responder: not assessed", "owner, responder: " + NS), ("responder not assessed", "responder " + NS),
                     ("owner not assessed", "owner " + NS), ("run by: not assessed", "run by: " + NS),
                     ("owner and responder not assessed", "owner and responder " + NS)):
        svg = svg.replace(old, new)  # an empty owner cell reads as the tables read it
    heads = "|".join(re.escape(k) for k in COLUMN_TERMS)
    return re.sub(r'<text ([^>]*)class="k">(' + heads + r')</text>',  # a column's name opens its meaning where it stands
                  lambda m: (f'<g class="term" tabindex="0" role="button" data-term="{cv.esc(COLUMN_TERMS[m.group(2)])}">'
                             f'<text {m.group(1)}class="k term">{m.group(2)}</text></g>'), svg)

COLUMN_TERMS = {'CAPABILITY': 'Capability', 'INTENDED FLOW': 'Intended flow', 'STAGE': 'Stage', 'PROCESS STEP': 'Process step', 'PART': 'Part', 'EXTERNAL DEPENDENCY': 'External dependency'}


def glossary_terms(M):
    """Every entry the page's glossary holds, by its word: what a column name's hover shows."""
    return {w: html.unescape(re.sub(r"<[^>]+>", "", d_)) for w, d_ in
            re.findall(r"<tr><th>([^<]+)</th><td>(.*?)</td>", cv.words(M, set(M["stage"]), folded=True))}


MAP_LINE = "Click any box to light its chain and open its details. ▸ opens a folded line."


def map_line():
    """One plain line above the map, in place of a key: every mark is written on the box, and ▸ marks a folded line."""
    return f'<p class="mapline">{cv.esc(MAP_LINE)}</p>'


def fold_keys(M):
    """The folded maps the page carries: on load, each capability group opened, each flow and each stage in focus."""
    return ([""] + ["c:" + r["capability_id"] for r in M["kids"].get("", [])]
            + ["f:" + f["flow_id"] for f in M["flows"]] + ["g:" + s for s in M["stage"]])


def folded_maps(M):
    """Each folded map as an inert template the page swaps in on a click; the open map is the page's own."""
    return "".join(f'<template data-fold="{cv.esc(k or "load")}">{the_map(M, "c", fold=k)}</template>' for k in fold_keys(M))


def stage_docs(reg):
    """Each stage's generated alerts and runbook pages, where the register folder holds them: {stage: {doc: path}}."""
    out = {}
    for d_ in sorted(reg.glob("stage-*")) if reg else []:
        docs = {name: f"{d_.name}/{f}" for name, f in (("Alerts", "ALERT.html"), ("Runbook", "RUNBOOK.html"))
                if (d_ / f).exists()}
        if docs:
            out[d_.name[len("stage-"):]] = docs
    return out


# ---------------------------------------------------------------- the measures panel

def watched(m):
    """Whether operations monitoring collects an emitted measure, as the register's `watched` says, with its source."""
    w = (m.get("watched") or "").strip().lower()
    if not (m.get("exists") or "").lower().startswith("yes") or not w:
        return ""
    src = (m.get("watched_source") or "").strip()
    return w + (": " + src if src else "")


def panel_data(M, docs=None):
    """Per node, the kit's measures form: rows as flow_outputs prints them, layers from method/layers.csv."""
    R = M["R"]
    method = {"measure-forms": fo.read_csv(fo.HERE / "method" / "measure-forms.csv"),
              "agent-questions": fo.read_csv(fo.HERE / "method" / "agent-questions.csv")}
    business = {sid for sid, x in M["subj"].items() if x.get("band") == "business"}

    def row(m):
        e = (m.get("exists") or "").strip().lower()
        return {"id": m.get("handle", ""), "title": m.get("measure", ""),
                "layer": cv.layer_of(R, m.get("layer")) or m.get("layer", ""),
                "state": ("defective" if (m.get("defect") or "").strip() else "exists") if e.startswith("yes") else "proposed",
                "defect": (m.get("defect") or "").strip(),
                "alert": (m.get("alert") or "").strip().lower().startswith("yes"),
                "answers": m.get("question_it_answers", ""), "kind": fo.kind_of(method, m),
                "counted_on": m.get("counted_on", ""), "how": m.get("counted_how", ""),
                "exists_today": ("yes: " + (m.get("source_ref") or "")) if e.startswith("yes") else "no, proposed",
                "watched": watched(m), "runbook": entry(m)}

    def entry(m):  # an alerting measure's own entry in its stage's runbook
        st = m.get("stage") or M["step"].get(m.get("step"), {}).get("stage", "")
        page_ = (docs or {}).get(st, {}).get("Runbook")
        return f'{page_}#alert-{m.get("handle", "")}' if page_ and (m.get("alert") or "").strip().lower().startswith("yes") else ""

    ms = R["measures"]
    at_op = at_operation(M)

    def at(steps):  # the step or steps a part's measure serves, as the map names them
        if len(steps) == 1:
            return cv.step_title(M, steps[0])
        return "; ".join(cv.step_title(M, x) for x in steps)
    one_flow = len(M["flows"]) == 1
    out = {"flows": {}, "stages": {}, "steps": {}, "parts": {}}
    for f in M["flows"]:
        mine = [m for m in ms if not m.get("stage") and not m.get("step") and m.get("subject_id") in business
                and (m.get("flow") == f["flow_id"] or (one_flow and not m.get("flow")))]
        out["flows"][f["flow_id"]] = {"name": f.get("name", ""), "measures": [row(m) for m in mine]}
        for st in f["_stages"]:
            out["stages"][st["stage"]] = {"name": f'Stage {st.get("order")}: {st.get("name", "")}', "flow": f["flow_id"],
                                          "measures": [row(m) for m in ms if m.get("stage") == st["stage"] and not m.get("step")]}
            for x in st["_steps"]:
                out["steps"][x["step"]] = {"name": cv.step_title(M, x["step"]), "stage": st["stage"], "flow": f["flow_id"],
                                           "qualifier": cv.plain_qualifier(x.get("qualifier", "")) if cv.carried(x) else "",
                                           "measures": [row(m) for m in own_at_step(M, x["step"], at_op)]}
    for sid, x in M["subj"].items():
        if x.get("kind") != "element" or sid in business:
            continue
        out["parts"][sid] = {"name": x.get("name", ""), "kind": cv.kind_label(M, x),
                             "measures": [dict(row(m), n=i, at=at(op_steps(M, sid, m))) for i, m in enumerate(part_measures(M, sid), 1)]}
    order = {sid: i for i, sid in enumerate(M["subj"])}

    def via(pids, skip=()):  # the measures of each part relied on, under its name, in the part's own form
        rows = {p: [row(m) for m in relied_measures(M, p) if m.get("handle") not in skip] for p in pids if p in out["parts"]}
        return [{"part": p, "name": out["parts"][p]["name"], "measures": rows[p]}
                for p in sorted(rows, key=lambda p: order.get(p, 0)) if rows[p]]
    rel = relied_on(M)
    nodes = node_parts(M, rel)
    for sid, nd in out["steps"].items():
        nd["via"] = via(rel.get(sid, ()), {r["id"] for r in nd["measures"]})
    for gid, nd in out["stages"].items():
        nd["via"] = via(nodes.get("g:" + gid, ()))
    for fid, nd in out["flows"].items():
        nd["via"] = via(nodes.get("f:" + fid, ()))
    with (fo.HERE / "method" / "layers.csv").open(encoding="utf-8", newline="") as fh:
        import csv as _csv
        out["layers"] = [{"layer": r["layer"], "heading": r["layer"][:1].upper() + r["layer"][1:] + ": " + r["question_it_asks"]}
                         for r in _csv.DictReader(fh)]
    out["threshold"] = "Threshold: " + fo.THRESHOLD.replace("*", "")
    out["docs"] = docs or {}
    out["terms"] = glossary_terms(M)
    return out



def how_made(M, checked):
    rows = M["R"]["how-made"]
    if not rows:
        return f'<p class="note">This register does not record how it was made. The check: {checked[0]} errors, {checked[1]} warnings.</p>'
    trs = "".join(f'<tr><td>{cv.esc(r.get("pass"))}.{cv.esc(r.get("step"))}</td><th>{cv.esc(r.get("name"))}</th>'
                  f'<td>{cv.esc(r.get("went_in"))}</td><td>{cv.esc(r.get("came_out"))}</td><td>{cv.esc(r.get("done_by"))}</td>'
                  f'<td>{cv.esc(r.get("note"))}</td></tr>' for r in rows)
    return ('<section class="words"><h2>How this map was made</h2><table><thead><tr><th>Step</th><th>Name</th><th>Went in</th>'
            f'<th>Came out</th><th>Done by</th><th>Note</th></tr></thead><tbody>{trs}</tbody></table>'
            f'<p class="note">The check: {checked[0]} errors, {checked[1]} warnings.</p></section>')


CSS = """
:root{--cov-m:#A9C08A;--cov-p:#F1C6B4;--cov-b:#E8E4DA}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--cov-m:#4F6439;--cov-p:#7A4634;--cov-b:#33322E}}
:root[data-theme="dark"]{--cov-m:#4F6439;--cov-p:#7A4634;--cov-b:#33322E}
main{max-width:1440px}
.fig[hidden]{display:none!important}
.canvas{--rail:320px;display:grid;grid-template-columns:minmax(0,1fr) 14px var(--rail);column-gap:0;row-gap:14px;align-items:start}.divider{align-self:stretch;position:relative;cursor:col-resize;touch-action:none;outline:none}.divider::before{content:"";position:absolute;top:0;bottom:0;left:6px;width:2px;border-radius:1px;background:var(--g300)}.divider:hover::before,.divider.dragging::before{background:var(--g500)}.divider:focus-visible::before{left:5px;width:4px;background:var(--slate)}.rail{position:sticky;top:8px;display:grid;gap:12px;max-height:96vh;overflow:auto}.panel{background:var(--paper);border:1px solid var(--g300);border-radius:6px;padding:12px;font-size:13px;}.panel h3{font:600 12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--g500);margin:0 0 6px}
.side{background:var(--paper);border:1px solid var(--g300);border-radius:6px;padding:12px;font-size:13px}
.side h3{font:600 12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--g500);margin:10px 0 6px}
.lenses{display:flex;flex-wrap:wrap;gap:4px}
.lenses button{font:13px var(--sans);color:var(--slate);background:var(--paper);border:1px solid var(--g400);border-radius:4px;padding:3px 9px;cursor:pointer}
.lenses button[aria-pressed="true"]{background:var(--slate);color:var(--paper)}
.side select{font:13px var(--sans);margin-top:6px;max-width:100%}
.sw{display:inline-block;width:14px;height:12px;border:1px solid var(--g500);vertical-align:-1px;margin-right:6px}
.key div{margin:2px 0}
#readout ul{padding-left:18px;margin:4px 0}#readout ul.lines{list-style:none;padding-left:0}#readout .trail{font-size:13px;margin:0 0 6px}#readout .crumb{font:inherit;color:var(--clay-d);background:none;border:0;padding:0;cursor:pointer;text-decoration:underline}#readout .here{font-weight:600}#readout h4{font-size:13px;margin:10px 0 2px}#readout dl{display:grid;grid-template-columns:max-content 1fr;gap:2px 8px;font-size:12.5px;margin:4px 0 8px}#readout dt{color:var(--g500)}#readout dd{margin:0;min-width:0;overflow-wrap:anywhere}#readout pre{white-space:pre-wrap;margin:0}
#readout li{margin-bottom:4px}#readout li.at{margin:8px 0 2px;font-weight:600;color:var(--g600)}.warn-state{color:var(--clay-d);font-weight:600}.warn-tag{color:var(--clay-d)}#readout details.via>ul.lines{padding-left:16px;border-left:1px solid var(--g300);margin-left:4px}
.note{font-size:13px;color:var(--g600)}
.tables{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:16px;margin-top:18px}
.tables h2{margin-top:10px}
table.readiness,table.agent{border-collapse:collapse;width:100%;font-size:13px;background:var(--paper);border:1px solid var(--g200)}
table.readiness th,table.readiness td,table.agent th,table.agent td{text-align:left;vertical-align:top;padding:5px 8px;border-top:1px solid var(--g200)}
table.readiness thead th,table.agent thead th{font:11px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--g500)}
.tag{font:11px var(--mono);color:var(--g500)}.ref{color:var(--g500);font-size:12px}
details{margin:6px 0}summary{cursor:pointer}
.words table{max-width:none}
.words summary{cursor:pointer}.words summary h2{display:inline-block;border-top:none;margin:20px 0 6px;padding-top:0}
.words td{word-break:break-word}
table.readiness tr[hidden]{display:none}table.readiness ol.nums{margin:0;padding-left:20px}table.readiness ol.nums li{margin:0}table.readiness .crumb{font:inherit;font-weight:600;color:var(--clay-d);background:none;border:0;padding:0;cursor:pointer;text-align:left;text-decoration:underline}table.readiness tr.here>*{background:var(--g200)}table.readiness tr.here>th{box-shadow:inset 3px 0 0 var(--clay)}
.mapline{font-size:12.5px;color:var(--g600);margin:0 0 6px;padding-right:300px}
svg.map g.fold{cursor:pointer}svg.map g.fold:focus{outline:none}svg.map g.fold:focus-visible rect.bx{stroke:var(--clay)}
svg.map g.term{cursor:help}svg.map g.term:focus-visible text{fill:var(--clay-d)}svg.map text.term{fill:var(--slate)}
.termtip{position:absolute;z-index:5;max-width:22rem;background:var(--paper);border:1px solid var(--g400);border-radius:4px;padding:6px 8px;font-size:13px;box-shadow:0 2px 6px rgba(0,0,0,.15)}
.showall{font:13px var(--sans);color:var(--slate);background:var(--paper);border:1px solid var(--g400);border-radius:4px;padding:3px 9px;cursor:pointer}
#stagedocs{margin-top:8px}
.pagehead{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 16px}.pagehead h1{margin-right:auto}
details.glossary{margin:0}details.glossary[open]{flex-basis:100%;order:2}
.casemoves .trail{font-size:13px;margin:0 0 6px}.casemoves .here{font-weight:600}section.case[hidden]{display:none}details.glossary>summary{display:inline-block;font:13px var(--sans);color:var(--clay-d);text-decoration:underline;cursor:pointer}
details.glossary[open]>summary{margin-bottom:6px}

@media (max-width:1100px){.canvas,.tables{grid-template-columns:minmax(0,1fr)}.divider{display:none}.rail{position:static;max-height:none}}
.panel .seqhead{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.panel .seqhead h3{margin:0 0 6px}
.panel .widen{font:12px var(--sans);color:var(--slate);background:var(--paper);border:1px solid var(--g400);border-radius:4px;padding:2px 8px;cursor:pointer}
.panel .widen[aria-pressed="true"]{background:var(--slate);color:var(--paper)}
.canvas.wide-seq{--rail:min(900px,62vw)}
.canvas.wide-seq .fig{overflow:auto}
.canvas:not(.wide-seq) #readout .m-wide,.canvas.wide-seq #readout .m-narrow{display:none}
#readout table.mtable{border-collapse:collapse;width:100%;font-size:12.5px;margin:2px 0 8px}#readout table.mtable th,#readout table.mtable td{text-align:left;vertical-align:top;padding:4px 6px;border-top:1px solid var(--g200)}
#readout table.mtable{table-layout:fixed}#readout col.c-m{width:44%}#readout col.c-s{width:17%}#readout col.c-o{width:19%}#readout col.c-a{width:20%}#readout table.mtable td{overflow-wrap:anywhere}
#readout table.mtable thead th{font:11px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--g500);border-top:0}#readout table.mtable tr.at td{font-weight:600;color:var(--g600);padding-top:8px}
#readout table.mtable tr.layer th{font-size:13px;font-weight:600;color:var(--slate);padding-top:12px;border-top:1px solid var(--g400)}#readout table.mtable tr.nil td,#readout table.mtable .tally{color:var(--g600)}
#readout table.mtable .why{display:block;color:var(--clay-d);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#readout table.mtable tr[hidden]{display:none}
#readout table.mtable .mmore{font:inherit;color:var(--clay-d);background:none;border:0;padding:0 0 0 14px;cursor:pointer;text-decoration:underline}
#readout table.mtable .mopen{font:inherit;color:var(--slate);background:none;border:0;padding:0;cursor:pointer;text-align:left}#readout table.mtable .mopen::before{content:"▸ ";color:var(--g500)}#readout table.mtable .mopen[aria-expanded="true"]::before{content:"▾ "}
#readout table.mtable tr.mform>td{border-top:0;padding:0 6px 6px 22px}#readout tr.mform[hidden]{display:none}
#seqout .trail{font-size:13px;margin:0 0 6px}#seqout .crumb{font:inherit;color:var(--clay-d);background:none;border:0;padding:0;cursor:pointer;text-decoration:underline}#seqout .here{font-weight:600}
.rail [hidden]{display:none!important}#rail-prompt{margin:0}
#seqout section.seq[hidden]{display:none}
#insideout section.inside[hidden]{display:none}#insideout .trail{font-size:13px;margin:0 0 6px}#insideout .here{font-weight:600}
#insideout .seqfig{background:var(--paper);border:1px solid var(--g200);border-radius:4px;margin:0 0 6px;overflow-x:auto}
#insideout svg.seq{display:block;width:100%;height:auto;min-width:0;cursor:default;touch-action:auto}
#seqout .seqfig{background:var(--paper);border:1px solid var(--g200);border-radius:4px;margin:0 0 6px;overflow-x:auto}
#seqout svg.seq{display:block;width:100%;height:auto;min-width:0;cursor:default;touch-action:auto}
#seqout .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 10px;margin:6px 0;font-size:12.5px}
#seqout .card dt{color:var(--g500);font-weight:600}#seqout .card dd{margin:0;overflow-wrap:anywhere}
#seqout .card ol,#seqout .card ul{margin:0;padding-left:18px}#seqout .card li{margin:0 0 3px}
#seqout details{font-size:12px;color:var(--g600)}#seqout details ul{padding-left:18px;margin:4px 0}
.canvas:not(.wide-seq) #seqout .card dl{grid-template-columns:minmax(0,1fr)}
svg.seq .frame{fill:none;stroke:var(--g500);stroke-width:1.1}
svg.seq .tag{fill:var(--g200);stroke:var(--g500);stroke-width:1.1}
svg.seq .tagt{font:600 12px var(--sans);fill:var(--slate)}
svg.seq .nm{font-family:var(--serif);font-size:13px;fill:var(--slate);text-anchor:middle}
svg.seq .kd{font-family:var(--sans);font-size:11px;fill:var(--g500);text-anchor:middle}
svg.seq .ll{stroke:var(--g400);stroke-width:1.1;stroke-dasharray:4 4}
svg.seq .ar{stroke:var(--g600);stroke-width:1.4;fill:none}
svg.seq .ar.unrec{stroke:var(--g400);stroke-width:1.3;stroke-dasharray:2 3}
svg.seq .op{font-family:var(--mono);font-size:12px;font-weight:600;fill:var(--slate)}
svg.seq .tv{font-family:var(--sans);font-style:italic;font-size:12px;fill:var(--g600)}
svg.seq .tv.dim{fill:var(--g500);font-size:11.5px}
svg.seq .h{paint-order:stroke;stroke:var(--paper);stroke-width:5px;stroke-linejoin:round}
svg.seq .hopc{fill:var(--paper);stroke:var(--g600);stroke-width:1.3}
svg.seq .hopt{font:700 11px var(--sans);fill:var(--slate);text-anchor:middle}
svg.seq .num{font:700 13px var(--sans);fill:var(--clay-d)}
svg.seq .qm{fill:var(--paper);stroke:var(--g400);stroke-width:1.3;stroke-dasharray:2 2}
svg.seq .qt{font:700 11px var(--sans);fill:var(--g500);text-anchor:middle}
svg.seq .til{font:700 15px var(--sans);fill:var(--clay-d)}
svg.seq .dot{fill:var(--slate)}
svg.seq .core{fill:none;stroke:var(--slate);stroke-width:1.6}
svg.seq .sep{stroke:var(--g500);stroke-width:1.1;stroke-dasharray:6 4}
svg.seq .guard{font-family:var(--sans);font-size:12px;fill:var(--slate)}
"""

FOLD_JS = """<script>
(function () {  // folding: the thing in focus open, its neighbours one line each; Show all opens everything
  var svg = document.querySelector('svg.map'); if (!svg) return;
  var T = {}, now = '', ALL = svg.cloneNode(true);
  document.querySelectorAll('template[data-fold]').forEach(function (t) { T[t.dataset.fold] = t; });
  ALL.querySelectorAll('g.sel[data-node^="f:"], g.sel[data-node^="g:"]').forEach(function (g) { g.dataset.open = g.dataset.node; });
  function show(k) {
    var src = k === 'all' ? ALL : T[k] && T[k].content.querySelector('svg');
    if (!src || k === now) return;
    now = k;
    svg.setAttribute('viewBox', src.getAttribute('viewBox'));
    svg.setAttribute('aria-label', src.getAttribute('aria-label'));
    svg.replaceChildren.apply(svg, Array.prototype.map.call(src.childNodes, function (n) { return n.cloneNode(true); }));
    svg.dispatchEvent(new CustomEvent('mapswap'));
  }
  show('load');
  window.cvFold = show;
  svg.addEventListener('click', function (ev) {  // capture: the map is swapped before the click lights its chain
    if (svg.dataset.dragged) return;
    var g = ev.target.closest('[data-open]'); if (g) show(g.dataset.open);
  }, true);
  svg.addEventListener('keydown', function (ev) {
    var g = ev.target.closest && ev.target.closest('g.fold');
    if (g && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); g.dispatchEvent(new MouseEvent('click', {bubbles: true})); }
  });
  document.querySelectorAll('[data-showall]').forEach(function (b) { b.addEventListener('click', function () { show('all'); }); });
})();
</script>"""

JS = """<script>
(function () {
  var svg = document.querySelector('svg.map'), readout = document.getElementById('readout');
  var key = function (g) { return g.dataset.node || (g.dataset.step ? 's:' + g.dataset.step : 'p:' + g.dataset.part); };
  document.querySelectorAll('[data-showall]').forEach(function (b) {
    b.addEventListener('click', function () {
      document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'})); stageDocs(''); view('');
      readout.innerHTML = '<p class="note">Click a process step, a part, a stage or a flow to see its measures.</p>';
      document.querySelectorAll('section.seq, section.inside').forEach(function (x) { x.hidden = true; });
      ['seq-empty', 'inside-empty'].forEach(function (id) { var e = document.getElementById(id); if (e) e.hidden = false; });
    });
  });
  var esc = function (s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; };
  var P = JSON.parse(document.getElementById('panel-data').textContent);
  var tip = document.createElement('div'); tip.className = 'termtip'; tip.hidden = true; document.body.appendChild(tip);
  var ev0 = '';
  document.addEventListener('click', function () { ev0 = 'click'; }, true);
  function term(g) {  // a column's name shows its glossary entry where it stands
    var r = g.getBoundingClientRect(), w = g.dataset.term;
    if (!tip.hidden && tip.dataset.term === w && ev0 === 'click') { tip.hidden = true; return; }
    tip.dataset.term = w; tip.innerHTML = '<b>' + esc(w) + '</b>: ' + esc(P.terms[w] || '');
    tip.style.left = (window.scrollX + r.left) + 'px'; tip.style.top = (window.scrollY + r.bottom + 4) + 'px'; tip.hidden = false;
  }
  function terms() {
    svg.querySelectorAll('g.term').forEach(function (g) {
      g.addEventListener('click', function (ev) { ev.stopPropagation(); term(g); });
      g.addEventListener('mouseenter', function () { if (tip.hidden || tip.dataset.term !== g.dataset.term) term(g); });
      g.addEventListener('mouseleave', function () { tip.hidden = true; });
      g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); term(g); } });
    });
  }
  terms(); svg.addEventListener('mapswap', terms);  // a folded map swapped in brings its own column names
  document.addEventListener('click', function (ev) { if (!ev.target.closest('g.term')) tip.hidden = true; });
  var docsBox = document.getElementById('stagedocs'), prompt = document.getElementById('rail-prompt');
  var VIEWS = {'s:': '.seqpanel', 'p:': '.insidepanel', 'g:': '.casepanel[data-kind="stage"]', 'f:': '.casepanel[data-kind="flow"]'};
  function view(k) {  // one view at a time: the one for the kind clicked, plus Measures; nothing clicked, one line
    if (prompt) prompt.hidden = !!k;
    document.querySelectorAll('aside.measpanel').forEach(function (x) { x.hidden = !k; });
    if (docsBox) docsBox.hidden = k !== 'g:';
    Object.keys(VIEWS).forEach(function (v) { document.querySelectorAll('aside' + VIEWS[v]).forEach(function (x) { x.hidden = v !== k; }); });
  }
  view('');
  function stageDocs(st) {  // the stage's alerts and runbook, once anything in a stage is chosen
    if (!docsBox) return;
    var d = st && P.docs[st];
    docsBox.innerHTML = d ? '<b>' + esc(P.stages[st].name) + '</b>: ' + Object.keys(d).map(function (k) {
      return '<a href="' + esc(d[k]) + '">' + esc(k) + '</a>'; }).join(' · ') : st ? esc(P.stages[st].name) + ': no alerts or runbook generated for this stage yet.' : '';
  }
  function mlabel(m) { return (m.n ? m.n + '. ' : '') + esc(m.title) + (m.state === 'defective' ? ' <b class="warn-state">(exists, but misleading)</b>' : esc(' (' + (m.state === 'exists' ? 'exists' : 'proposed') + ')')) + (m.alert ? ' <b>proposed alert</b>' : ''); }
  function mtitle(m) { return (m.n ? m.n + '. ' : '') + esc(m.title) + (m.alert ? ' <b>proposed alert</b>' : ''); }
  function mstate(m) { return m.state === 'defective' ? '<b class="warn-state">' + esc('exists, but misleading') + '</b>' : esc(m.state === 'exists' ? 'exists' : 'proposed'); }
  function mrow(m, on, fold) {  // widened: the same measure line as a table row; opening it gives the same form
    var f = fold ? ' data-in="' + fold + '" hidden' : '';
    return '<tr class="mrow"' + f + '><td><button type="button" class="mopen" aria-expanded="false">' + mtitle(m) + '</button>' +
      (m.state === 'defective' && m.defect ? '<span class="why">Why misleading: ' + esc(m.defect) + '</span>' : '') + '</td><td>' + mstate(m) + '</td><td>' + esc(on) + '</td><td>' +
      (m.runbook ? '<a href="' + esc(m.runbook) + '">this alert&rsquo;s entry in the runbook</a>' : 'none') + '</td></tr><tr class="mform"' + (fold ? ' data-in="' + fold + '"' : '') + ' hidden><td colspan="4">' + detail(m) + '</td></tr>';
  }
  function tally(ms) {  // the states of the folded rows, in words
    var n = {};
    ms.forEach(function (m) { var s = m.state === 'defective' ? 'exists, but misleading' : m.state === 'exists' ? 'exists' : 'proposed'; n[s] = (n[s] || 0) + 1; });
    return ['exists, but misleading', 'exists', 'proposed'].filter(function (s) { return n[s]; }).map(function (s) { return n[s] + ' ' + s; }).join(' · ');
  }
  function detail(m) {
    var rows = [['Answers', esc(m.answers)], ['Kind', esc(m.kind)], ['Counted on', esc(m.counted_on)],
      ['Counted how', /^(oc |psql|curl|kubectl)|-- psql/.test(m.how) ? '<pre>' + esc(m.how) + '</pre>' : esc(m.how)], ['Exists today', esc(m.exists_today)]].concat(m.watched ? [['Watched', esc(m.watched)]] : []).concat(m.defect ? [['Why misleading', esc(m.defect)]] : []).concat(m.runbook ? [['Its alert', '<a href="' + esc(m.runbook) + '">this alert&rsquo;s entry in the runbook</a>']] : []);
    return '<dl>' + rows.map(function (r) { return '<dt>' + r[0] + '</dt><dd>' + r[1] + '</dd>'; }).join('') + '</dl>';
  }
  function crumb(label, node) { return node ? '<button type="button" class="crumb" data-go="' + esc(node) + '">' + esc(label) + '</button>' : '<span class="here">' + esc(label) + '</span>'; }
  function openNode(node) {
    var k = node.slice(0, 2), id = node.slice(2), nd, trail;
    stageDocs(k === 'g:' ? id : '');
    if (k === 's:') { nd = P.steps[id]; if (!nd) return false; trail = [crumb(P.flows[nd.flow].name, 'f:' + nd.flow), crumb(P.stages[nd.stage].name, 'g:' + nd.stage), crumb(nd.name)]; }
    else if (k === 'g:') { nd = P.stages[id]; if (!nd) return false; trail = [crumb(P.flows[nd.flow].name, 'f:' + nd.flow), crumb(nd.name)]; }
    else if (k === 'f:') { nd = P.flows[id]; if (!nd) return false; trail = [crumb(nd.name)]; }
    else if (k === 'p:') { nd = P.parts[id]; if (!nd) return false; trail = [crumb(nd.kind), crumb(nd.name)]; }
    else return false;
    view(k);
    document.dispatchEvent(new CustomEvent('cvpick', {detail: node}));  // a pick not on the folded map still reaches its view
    var out = '<p class="trail">' + trail.join(' <span class="sep">›</span> ') + '</p>';
    if (nd.qualifier) out += '<p class="note">' + esc(nd.qualifier) + '</p>';
    var line = function (m) { return '<li><details><summary>' + mlabel(m) + '</summary>' + detail(m) + '</details></li>'; }, any = nd.measures.length > 0;
    var narrow = '', wide = '', self = {'s:': 'this step', 'p:': 'this part', 'g:': 'this stage', 'f:': 'this flow'}[k], nf = 0;
    P.layers.forEach(function (L) {
      var inL = function (m) { return m.layer === L.layer; }, ms = nd.measures.filter(inL);
      var vs = (nd.via || []).map(function (v) { return {name: v.name, ms: v.measures.filter(inL)}; }).filter(function (v) { return v.ms.length; });
      wide += '<tr class="layer"><th colspan="4" scope="colgroup">' + esc(L.heading) + '</th></tr>';
      if (!ms.length && !vs.length) { wide += '<tr class="nil"><td colspan="4">No measure for ' + self + '</td></tr>'; return; }
      any = true;
      var last = '', lastW = '';
      wide += ms.map(function (m) { var head = m.at && m.at !== lastW ? '<tr class="at"><td colspan="4">' + esc(m.at) + '</td></tr>' : ''; lastW = m.at || lastW; return head + mrow(m, self); }).join('') +
        vs.map(function (v) {  // every part relied on is counted: its first row, the rest folded with their states
          var rest = v.ms.slice(1), f = 'mf' + (nf++);
          return mrow(v.ms[0], v.name) + (rest.length ? '<tr class="more"><td colspan="4"><button type="button" class="mmore" data-fold="' + f + '" aria-expanded="false">' +
            esc('… ' + rest.length + ' more on ' + v.name) + '</button> <span class="tally">' + tally(rest) + '</span></td></tr>' +
            rest.map(function (m) { return mrow(m, v.name, f); }).join('') : ''); }).join('');
      narrow += '<h4>' + esc(L.heading) + '</h4><ul class="lines">' + ms.map(function (m) {
        var head = m.at && m.at !== last ? '<li class="note at">' + esc(m.at) + '</li>' : ''; last = m.at || last;
        return head + line(m); }).join('') + (vs.length ? '<li class="note">On a part it relies on:</li>' : '') + vs.map(function (v) {
        return '<li><details class="via"><summary>' + esc(v.name + ' (' + v.ms.length + (v.ms.length === 1 ? ' measure' : ' measures')) + (function (d) { return d ? ', <b class="warn-state">' + d + ' ' + esc('exists, but misleading') + '</b>' : ''; })(v.ms.filter(function (m) { return m.state === 'defective'; }).length) + ')' +
          '</summary><ul class="lines">' + v.ms.map(line).join('') + '</ul></details></li>'; }).join('') + '</ul>';
    });
    if (narrow) out += '<div class="m-narrow">' + narrow + '</div><div class="m-wide"><table class="mtable"><colgroup><col class="c-m"><col class="c-s"><col class="c-o"><col class="c-a"></colgroup>' +
      '<thead><tr><th scope="col">Measure</th><th scope="col">State</th><th scope="col">On</th><th scope="col">Alert</th></tr></thead><tbody>' + wide + '</tbody></table></div>';
    out += any ? '<p class="note">' + esc(P.threshold) + '</p>' : '<p class="note">none</p>';
    readout.innerHTML = out;
    return true;
  }
  var nodeOf = function (g) { return g.dataset.node || (g.dataset.step ? 's:' + g.dataset.step : 'p:' + g.dataset.part); };
  svg.addEventListener('click', function (ev) {
    var g = ev.target.closest('g.sel');
    if (g) openNode(nodeOf(g));
  });
  readout.addEventListener('click', function (ev) {
    var o = ev.target.closest('button.mopen');
    if (o) { var f = o.closest('tr').nextElementSibling, on = f.hidden; f.hidden = !on; o.setAttribute('aria-expanded', on); return; }
    var mo = ev.target.closest('button.mmore');
    if (mo) {  // the folded rows of one part: shown, or folded again with their forms closed
      var open = mo.getAttribute('aria-expanded') !== 'true'; mo.setAttribute('aria-expanded', open);
      readout.querySelectorAll('tr[data-in="' + mo.dataset.fold + '"]').forEach(function (r) {
        if (r.classList.contains('mrow')) { r.hidden = !open; r.querySelector('.mopen').setAttribute('aria-expanded', false); } else r.hidden = true; });
      return;
    }
    var b = ev.target.closest('button.crumb'); if (!b) return;
    var node = b.dataset.go, k = node.slice(0, 2), id = node.slice(2);
    var g = svg.querySelector(k === 'g:' || k === 'f:' ? 'g.sel[data-node="' + node + '"]' : k === 's:' ? 'g.sel[data-step="' + id + '"]' : 'g.sel[data-part="' + id + '"]');
    if (g) g.dispatchEvent(new MouseEvent('click', {bubbles: true})); else openNode(node);
  });
})();
</script>"""


CASE_JS = """<script>
(function () {  // how a case moves: the stage or the flow last clicked on the map
  var svg = document.querySelector('svg.map'); if (!svg) return;
  function show(node) {
    document.querySelectorAll('aside.casepanel').forEach(function (p) {
      var hit = false;
      p.querySelectorAll('section.case').forEach(function (s) { var on = s.dataset.case === node; s.hidden = !on; hit = hit || on; });
      p.querySelector('.case-empty').hidden = hit;  // a panel showing nothing says what to click
    });
  }
  svg.addEventListener('click', function (ev) {
    var g = ev.target.closest('g.sel[data-node]'); if (g) show(g.dataset.node);
  });
  document.addEventListener('cvpick', function (ev) { if (/^[fg]:/.test(ev.detail)) show(ev.detail); });
  document.querySelectorAll('[data-showall]').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('section.case').forEach(function (s) { s.hidden = true; });
      document.querySelectorAll('.case-empty').forEach(function (e) { e.hidden = false; });
    });
  });
})();
</script>"""


INSIDE_JS = """<script>
(function () {  // inside this part: the part last clicked on the map
  var out = document.getElementById('insideout'); if (!out) return;
  var empty = document.getElementById('inside-empty');
  function show(pid) {
    var hit = false;
    out.querySelectorAll('section.inside').forEach(function (s) { var on = s.dataset.inside === pid; s.hidden = !on; hit = hit || on; });
    empty.hidden = hit;
  }
  document.querySelectorAll('svg.map').forEach(function (m) {
    m.addEventListener('click', function (ev) {
      out.querySelectorAll('g.oprow.on').forEach(function (r) { r.classList.remove('on'); });
      var fig = m.closest('.fig'); if (fig && fig.hidden) return;
      var g = ev.target.closest('g.sel[data-part]'); if (g) show(g.dataset.part);
    });
  });
  document.addEventListener('cvpick', function (ev) { if (ev.detail.slice(0, 2) === 'p:') show(ev.detail.slice(2)); });
  out.addEventListener('click', function (ev) {  // an operation lights, on the map, the part and the process steps it serves
    var row = ev.target.closest('g.oprow'), map = document.querySelector('svg.map'); if (!row || !map) return;
    var was = row.classList.contains('on');
    document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}));  // the map forgets its own pick, so its next click lights again
    if (was) return;
    var pid = row.closest('section.inside').dataset.inside;
    var steps = new Set((row.dataset.steps || '').split(' ').filter(Boolean));
    if (window.cvFold && Array.from(steps).some(function (s) { return !map.querySelector('g.sel[data-step="' + s + '"]'); })) window.cvFold('all');
    row.classList.add('on');
    map.classList.add('picked');
    map.querySelectorAll('g.sel').forEach(function (x) {
      var on = x.dataset.step ? steps.has(x.dataset.step) : x.dataset.part === pid && !x.dataset.node;
      if (!on) x.classList.add('off');
    });
    map.querySelectorAll('.link').forEach(function (l) {
      if (l.dataset.dep || !(steps.has(l.dataset.step) && l.dataset.part === pid)) l.classList.add('off');
    });
    map.querySelectorAll('.tree, .call').forEach(function (x) { x.classList.add('off'); });
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') out.querySelectorAll('g.oprow.on').forEach(function (r) { r.classList.remove('on'); });
    var row = ev.target.closest && ev.target.closest('g.oprow');
    if (row && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); row.dispatchEvent(new MouseEvent('click', {bubbles: true})); }
  });
})();
</script>"""


SEQ_JS = """<script>
(function () {  // the step panel: the step last clicked on the map, drawn in order with its card
  var out = document.getElementById('seqout'); if (!out) return;
  var empty = document.getElementById('seq-empty'), canvas = document.querySelector('.canvas');
  var panel = out.closest('.seqpanel'), rail = out.closest('.rail');
  function show(sid) {
    var hit = false;
    out.querySelectorAll('section.seq').forEach(function (s) { var on = s.dataset.seq === sid; s.hidden = !on; hit = hit || on; });
    empty.hidden = hit;
    if (hit && rail && getComputedStyle(rail).position === 'sticky' && panel.offsetTop - rail.scrollTop > rail.clientHeight - 80)
      rail.scrollTop = panel.offsetTop - 8;
  }
  document.querySelectorAll('svg.map').forEach(function (m) {
    m.addEventListener('click', function (ev) {
      var fig = m.closest('.fig'); if (fig && fig.hidden) return;
      var g = ev.target.closest('g.sel[data-step]'); if (g) show(g.dataset.step);
    });
  });
  document.addEventListener('cvpick', function (ev) { if (ev.detail.slice(0, 2) === 's:') show(ev.detail.slice(2)); });
  document.querySelectorAll('[data-widen]').forEach(function (b) {
    b.addEventListener('click', function () {  // the map keeps its scale and scrolls in its column; it is never zoomed for the reader
      var map = document.querySelector('svg.map'), w = map && map.getBoundingClientRect().width;
      var on = canvas.classList.toggle('wide-seq');
      if (map) { if (on && w > 0) map.style.width = w + 'px'; else map.style.removeProperty('width'); }
      document.querySelectorAll('[data-widen]').forEach(function (w) {
        w.setAttribute('aria-pressed', on); w.textContent = on ? 'Narrow this panel' : 'Widen this panel';
      });
    });
  });
  out.addEventListener('click', function (ev) {
    var b = ev.target.closest('button.crumb'); if (!b) return;
    var node = b.dataset.go, k = node.slice(0, 2), id = node.slice(2);
    var svg = document.querySelector('svg.map'); if (!svg) return;
    var g = svg.querySelector(k === 's:' ? 'g.sel[data-step="' + id + '"]' : 'g.sel[data-node="' + node + '"]');
    if (g) g.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  });
})();
</script>"""


def seq_panel(M):
    """The step, in order: a panel of its own beside the measures panel, empty until a step is clicked; each step's
    sequence drawing and scenario card drawn once, shown by the click on the step."""
    crumb = lambda label, node: (f'<button type="button" class="crumb" data-go="{cv.esc(node)}">{cv.esc(label)}</button>'
                                 if node else f'<span class="here">{cv.esc(label)}</span>')
    blocks = []
    for f in M["flows"]:
        for st in f["_stages"]:
            for x in st["_steps"]:
                trail = ' <span class="sep">&rsaquo;</span> '.join([
                    crumb(f.get("name", ""), "f:" + f["flow_id"]), crumb(f'Stage {st.get("order")}: {st.get("name", "")}', "g:" + st["stage"]),
                    crumb(cv.step_title(M, x["step"]), "")])
                blocks.append(f'<section class="seq" data-seq="{cv.esc(x["step"])}" hidden><p class="trail">{trail}</p>'
                              f'{ss.block(M, x["step"])}</section>')
    return ('<aside class="panel seqpanel" hidden><div class="seqhead"><h3>How this step is carried out</h3>'
            '<button type="button" class="widen" data-widen aria-pressed="false">Widen this panel</button></div>'
            '<div id="seqout"><p class="note" id="seq-empty">Click a step on the map to see its interactions in order, '
            'and its scenario card.</p>' + "".join(blocks) + "</div></aside>")


def case_panels(M, docs):
    """How a case moves: through a stage (its state machine and card) and end to end (the stages in order and the
    flow's card), each a panel of its own, empty until a stage or a flow is clicked."""
    def panel(title, kind, blocks, empty):
        return (f'<aside class="panel casepanel" data-kind="{kind}" hidden><div class="seqhead"><h3>{cv.esc(title)}</h3>' +
                f'<button type="button" class="widen" data-widen aria-pressed="false">Widen this panel</button></div>'
                f'<div class="casemoves"><p class="note case-empty">{empty}</p>' + "".join(blocks) + "</div></aside>")
    stages = [f'<section class="case" data-case="g:{cv.esc(st["stage"])}" hidden><p class="trail"><span class="here">'
              f'Stage {cv.esc(st.get("order", ""))}: {cv.esc(st.get("name", ""))}</span></p>{sfv.block(M, st["stage"], docs)}</section>'
              for f in M["flows"] for st in f["_stages"]]
    flows = [f'<section class="case" data-case="f:{cv.esc(f["flow_id"])}" hidden><p class="trail"><span class="here">'
             f'{cv.esc(f.get("name", ""))}</span></p>'
             + (sfv.flow_block(M, f["flow_id"], docs) if f["_stages"] else
                '<p class="note">The register does not break this flow into stages, so there is no order of stages '
                'to draw.</p>') + '</section>'
             for f in M["flows"]]
    return (panel("How a case moves through this stage", "stage", stages, "Click a stage on the map to see where a case "
                  "can be in it, what happens to it there, and how it leaves.") +
            panel("How a case moves end to end", "flow", flows, "Click a flow on the map to see its stages in order, "
                  "each with its promise."))


def kind_said(M, p, block):
    """Inside a part, every kind is named as the map names it (cv.kind_label): a part of the agent family is an
    "AI agent" on its card, in what it depends on and in its drawing."""
    for k in {x.get("part_kind", "") for x in M["subj"].values() if x.get("part_kind") and M["family"](x) == "agent"}:
        k = cv.esc(k)
        for a, b in (("<dd>{}</dd>", "<dd>AI agent</dd>"), ('class="ref">({}', 'class="ref">(AI agent'), (">{}</text>", ">AI agent</text>")):
            block = block.replace(a.format(k), b)
    return block


def inside_panel(M, drawn=None):
    """Inside this part: a panel of its own beside the measures panel, empty until a part is clicked; each part's
    operations, card and, for an AI agent, its run, drawn once and shown by the click on the part."""
    blocks = [f'<section class="inside" data-inside="{cv.esc(p)}" hidden><p class="trail"><span class="here">'
              f'{cv.esc(M["subj"][p].get("name", ""))}</span></p>{kind_said(M, p, pi.block(M, p))}</section>'
              for p in pi.parts(M) if drawn is None or p in drawn]
    blocks += [f'<section class="inside" data-inside="{cv.esc(x["subject_id"])}" hidden><p class="trail"><span class="here">'
               f'{cv.esc(x.get("name", ""))}</span></p><p class="note">A person: no operations or parts inside to draw. '
               f'The process steps they carry out light on the map, and their measures are in Measures.</p></section>'
               for x in M["persons"] if drawn is None or x["subject_id"] in drawn]
    return ('<aside class="panel insidepanel" hidden><div class="seqhead"><h3>Inside this part</h3>'
            '<button type="button" class="widen" data-widen aria-pressed="false">Widen this panel</button></div>'
            '<div id="insideout" class="insideout"><p class="note" id="inside-empty">Click a part on the map to see its '
            'operations, the process steps each serves, and the parts it calls.</p>' + "".join(blocks) + "</div></aside>")


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


RAIL_PROMPT = "Click anything on the map. Its details open here."


def side(M, docs):
    """Above the panels: the way out of a focus, the one line shown while nothing is chosen, and a stage's alerts and
    runbook once a stage is chosen."""
    hint = ('<div id="stagedocs" class="note" hidden></div>' if docs else "")
    return ('<aside class="side"><button type="button" class="showall" data-showall>Show all</button>'
            f'<p class="note" id="rail-prompt">{RAIL_PROMPT}</p>{hint}</aside>')

def left_out(M):
    """The map's Not drawn line: the left-out steps and stages."""
    mine = list(M.get("_left_out", []))
    if not mine:
        return ""
    steps = "; ".join(f'{M["_step_label"].get(sid) or "Step " + sid}: {name}' for sid, name in mine)
    gone = [name for k, name in M["_left_out_stages"]]
    stages = (" Stage(s) left with no step, also not drawn: " + "; ".join(gone) + ".") if gone else ""
    return (f'<details class="leftout"><summary>Not drawn: steps nothing performs whose only basis is a reference model: {cv.esc(steps)}</summary>'
            f'<p class="note">Judged from each step\'s own source text, as the register has no per-step source ids: a step '
            f'with no performer is left out unless its source cites a code line, names a file, a document section or a '
            f'person asked. Any such evidence keeps it, drawn as not assessed.{cv.esc(stages)}</p></details>')




MADE_FILE = "how-this-map-was-made.html"


def made_page(M, reg_label, checked):
    """How the map was made, for whoever builds or checks it: written beside the page, never on it."""
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>{cv.esc(M['system'])}: how this map was made</title>\n<style>{cv.CSS}{CSS}</style></head><body><main>"
            f"<h1>{cv.esc(M['system'])}: how this map was made</h1>"
            f'<p class="note">Drawn from the register {cv.esc(reg_label)}.</p>{how_made(M, checked)}</main></body></html>\n')

DIVIDER_JS = """<script>
(function () {  // the divider between the map and the rail: drag, arrow keys, double-click to reset; it never zooms the map
  var bar = document.querySelector('.canvas > .divider'); if (!bar) return;
  var canvas = bar.parentNode, rail = canvas.querySelector('.rail'), MAP = 360, RAIL = 280, STEP = 24, moved = false;
  function key() { return canvas.classList.contains('wide-seq') ? 'one-canvas.rail-wide' : 'one-canvas.rail'; }  // one width per panel mode
  function stored() { try { var v = parseFloat(localStorage.getItem(key())); return v > 0 ? v : null; } catch (e) { return null; } }
  function keep(v) { try { if (v === null) localStorage.removeItem(key()); else localStorage.setItem(key(), String(Math.round(v))); } catch (e) {} }
  function room() { return canvas.clientWidth - bar.offsetWidth; }
  function aria() {
    var r = room();
    bar.setAttribute('aria-valuemax', Math.round(r - RAIL));
    bar.setAttribute('aria-valuenow', Math.round(r - rail.offsetWidth));  // the map's width, in pixels
  }
  function set(v) {
    if (v === null) canvas.style.removeProperty('--rail');
    else canvas.style.setProperty('--rail', Math.max(RAIL, Math.min(v, room() - MAP)) + 'px');
    aria();
  }
  function apply() { if (bar.offsetParent !== null) set(stored()); }  // hidden where the rail stacks under the map
  apply();
  window.addEventListener('resize', apply);
  new MutationObserver(apply).observe(canvas, {attributes: true, attributeFilter: ['class']});  // Widen / Narrow this panel
  bar.addEventListener('pointerdown', function (ev) {
    if (ev.button !== 0) return;
    ev.preventDefault(); bar.setPointerCapture(ev.pointerId); bar.classList.add('dragging'); bar.focus(); moved = false;
  });
  bar.addEventListener('pointermove', function (ev) {
    if (!bar.hasPointerCapture(ev.pointerId)) return;
    moved = true; set(canvas.getBoundingClientRect().right - ev.clientX - bar.offsetWidth / 2);
  });
  function drop() { if (!bar.classList.contains('dragging')) return; bar.classList.remove('dragging'); if (moved) keep(rail.offsetWidth); }
  bar.addEventListener('pointerup', drop);
  bar.addEventListener('pointercancel', drop);
  bar.addEventListener('dblclick', function () { set(null); keep(null); });
  bar.addEventListener('keydown', function (ev) {
    var d = ev.key === 'ArrowLeft' ? STEP : ev.key === 'ArrowRight' ? -STEP : 0; if (!d) return;
    ev.preventDefault(); ev.stopPropagation(); set(rail.offsetWidth + d); keep(rail.offsetWidth);
  });
})();
</script>"""


def page(M, reg_label, build_cmd, checked, docs=None):
    n_na = sum(1 for x in M["step"].values() if not cv.carried(x))
    svg = the_map(M, "c")
    drawn = set(re.findall(r'data-part="([^"]+)"', svg))
    head = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n"
            f"     Source: {reg_label}\n     Builder: one_canvas.py\n     Build: {build_cmd}\n-->\n")
    return (head + "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{cv.esc(M['system'])} one canvas</title>\n<style>{cv.CSS}{CSS}{pi.CSS}{sfv.CSS}</style></head><body><main>"
            f"<div class=\"pagehead\"><h1>{cv.esc(M['system'].split(' (')[0])}</h1>{cv.words(M, set(M['stage']), folded=True)}</div>"
            f'<p class="lede">{plural(len(M["flows"]), "flow")}, {plural(len(M["stage"]), "stage")}, '
            f'{plural(len(M["step"]), "process step")} '
            f'({n_na} not assessed). Design-time only; no live values.</p>'
            f'<div class="canvas"><figure><div class="fig">{cv.ZOOM}{map_line()}{svg}</div>{left_out(M)}</figure>'
            f'<div class="divider" role="separator" aria-orientation="vertical" aria-label="Resize the map and the panels" '
            f'title="Drag to resize; double-click to reset" tabindex="0" aria-valuemin="360" aria-valuenow="0"></div>'
            f'<div class="rail">{side(M, docs)}'
            f'<aside class="panel measpanel" aria-live="polite" hidden><div class="seqhead"><h3>Measures</h3>'
            f'<button type="button" class="widen" data-widen aria-pressed="false">Widen this panel</button></div><div id="readout"><p class="note">Click a process step, '
            f'a part, a stage or a flow to see its measures.</p></div></aside>'
            f'{seq_panel(M)}{inside_panel(M, drawn)}{case_panels(M, docs)}</div></div>'
            f'<script type="application/json" id="panel-data">{json.dumps(panel_data(M, docs)).replace("</", "<" + chr(92) + "/")}</script>'
            + folded_maps(M) + "</main>" + cv.chain_data(M) + FOLD_JS + cv.SCRIPT + JS + SEQ_JS + DIVIDER_JS + INSIDE_JS + CASE_JS + "</body></html>\n")

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    reg, out = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    R = cv.load(reg)
    err, warn = cv.check(R)
    if err:
        for x in err:
            print("error:", x)
        return 1
    M = number_steps(prune(cv.model(R)))
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = "python -I one_canvas.py " + " ".join(argv)
    said = lambda text: fo.relabel_prose(M["_step_label"], M["R"]["steps"], text)
    out.write_text(said(page(M, reg.as_posix(), cmd, (len(err), len(warn)), stage_docs(reg))), encoding="utf-8")
    (out.parent / MADE_FILE).write_text(made_page(M, reg.as_posix(), (len(err), len(warn))), encoding="utf-8")
    for st, docs_ in stage_docs(reg).items():  # the stage's pages travel with the map page, at the paths it links
        for rel in docs_.values():
            (out.parent / rel).parent.mkdir(parents=True, exist_ok=True)
            if (reg / rel).resolve() != (out.parent / rel).resolve():  # a page written inside the register needs no copy
                shutil.copy2(reg / rel, out.parent / rel)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
