"""The views of one capability as one canvas: the map drawn once, with its panels beside it.

    python -I one_canvas.py REGISTER OUT.html

The kit's page of the capability; it reuses capability_views.py for reading and checking the register. The map starts
at the flow: five columns, each stage's steps folded to a count that opens in place with
the parts carrying them and the dependencies those parts call; pointing at a box lights its chain, and a click opens its panels in the
rail. Standard library only, no network.
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
import flow_page as fp  # noqa: E402
import page_style as ps  # noqa: E402
import step_sequence as ss  # noqa: E402
import step_page as stp  # noqa: E402
import part_page as ptp  # noqa: E402
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
    """A step nothing performs and whose only basis is a reference model is not drawn, where its stage keeps another
    step. A stage is never dropped: the register gives it its flow, so a stage whose every step is of that kind keeps
    them, drawn as not assessed. Any code, document or person evidence keeps the step, drawn as not assessed.
    Returns M."""
    bare = {sid for sid, st in M["step"].items() if not cv.carried(st) and not evidenced(st)}
    out = [sid for sid in M["step"] if sid in bare and any(
        x["step"] not in bare for x in M["stage"].get(M["step"][sid].get("stage"), {}).get("_steps", []))]
    M["_left_out"] = [(sid, M["step"][sid].get("name", "")) for sid in out]
    M["_left_out_stage_of"] = {sid: M["step"][sid].get("stage") for sid in out}
    M["_left_out_stages"] = []  # kept for its readers: no stage is left out
    for sid in out:
        st = M["step"].pop(sid)
        stage = M["stage"].get(st.get("stage"))
        if stage:
            stage["_steps"] = [x for x in stage["_steps"] if x["step"] != sid]
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


def node_steps(M):
    """Per stage and flow box, the steps inside it."""
    out = {}
    for f in M["flows"]:
        for st in f["_stages"]:
            out["g:" + st["stage"]] = {x["step"] for x in st["_steps"]}
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


def rail_measures(M, pid):
    """A part's Measures: its own; for an AI agent, also the measures of the calls it makes, which the part view does
    not list, after its own so its own keep their numbers."""
    own = part_measures(M, pid)
    if M["family"](M["subj"][pid]) != "agent":
        return own
    seen = {m.get("handle") for m in own}
    return own + [m for m in cv.agent_measures(M, M["subj"][pid]) if m.get("measure") and m.get("handle") not in seen]


def relied_measures(M, pid):
    """What a step relying on the part is shown: its measures not scoped to one step or stage, which a step lists as its own."""
    return [m for m in part_measures(M, pid) if not m.get("stage") and not m.get("step")]


def relied_here(M, pid, steps):
    """The part's relied-on measures that bear on these steps: those whose operation the part performs one of them
    with, and those the register ties to no step (a measure of the whole part, or an operation no step names)."""
    steps = set(steps)
    return [m for m in relied_measures(M, pid) if not op_steps(M, pid, m) or steps & set(op_steps(M, pid, m))]


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
    via_of = lambda pids, steps, skip=(): [m for p in pids for m in relied_here(M, p, steps) if m.get("handle") not in skip]
    at_op = at_operation(M)
    for sid in M["step"]:
        ms = own_at_step(M, sid, at_op)
        via = via_of(rel[sid], {sid}, {m.get("handle") for m in ms})
        out["s:" + sid] = with_any({L: status_with(ms, via, L) for L in Ls}, ms, via)
    for s in M["comps"] + M["deps"] + M["persons"] + [k for ks in M["dep_parts"].values() for k in ks]:
        ms = M["m_part"].get(s["subject_id"], [])
        out["p:" + s["subject_id"]] = with_any({L: status(ms, L) for L in Ls}, ms)
    parts, under = node_parts(M, rel), node_steps(M)
    for key, ms in node_measures(M).items():
        via = via_of(parts.get(key, ()), under.get(key, ()))
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

COLUMN_TERMS = {'INTENDED FLOW': 'Intended flow', 'STAGE': 'Stage', 'PROCESS STEP': 'Process step', 'PART': 'Part', 'EXTERNAL DEPENDENCY': 'External dependency'}


def glossary_terms(M):
    """Every entry the page's glossary holds, by its word: what a column name's hover shows, its definition and then
    its related terms, spelled out in words ("also called participant; narrower: Component")."""
    def rel(r):
        return cv.relations_in_words([x for x in html.unescape(r).split(" · ") if x])
    return {w: html.unescape(re.sub(r"<[^>]+>", "", d_)) + (f" ({rel(r)})" if r else "") for w, d_, r in
            re.findall(r'<tr><th>([^<]+)</th><td>(.*?)</td><td class="rel">(.*?)</td>',
                       cv.words(M, set(M["stage"]), folded=True))}


# ---------------------------------------------------------------- the map screen

FIT_ZOOM = 1  # Fit draws the map at its natural size: it scrolls in its frame and never shrinks below its type sizes

def part_group(M, s):
    """A part's layer, which colours it: an AI agent, a person, or its band (application or technology)."""
    fam = M["family"](s)
    if fam in ("agent", "person"):
        return fam
    return "tec" if s.get("band") == "technology" else "app"


def map_parts(M):
    """Every part the register names: (components and people, external dependencies and their own parts)."""
    parts = M["comps"] + [p for p in M["persons"] if p not in M["comps"]]
    deps = []
    for d in M["deps"]:
        deps += [d] + M["dep_parts"].get(d["subject_id"], [])
    return parts, deps


def stage_chain(M, st):
    """Below one stage, along the chain: per step the parts carrying it, then per part the external dependencies it
    calls, and the dependencies called in one of the stage's steps. Returns (parts in register order,
    [(step, part)], dependencies in register order, [(part, dependency)])."""
    order = {sid: i for i, sid in enumerate(M["subj"])}
    steps = [x["step"] for x in st["_steps"]]
    sp = list(dict.fromkeys((x["step"], p) for x in st["_steps"] for p, _ in x["_parts"] if p in M["subj"]))
    ext = set(M["ext"])  # an external dependency carrying a step sits in its own column, joined to that step
    parts = sorted({p for _, p in sp if p not in ext}, key=lambda p: order.get(p, 0))
    pd = list(dict.fromkeys((p, d) for p in parts for d in sorted(M["uses"].get(p, ())) if d in ext))
    deps = {d for _, d in pd} | {d for _, d in sp if d in ext} | {d for d in ext if set(steps) & cv.steps_of(M, d)}
    return parts, sp, sorted(deps, key=lambda d: order.get(d, 0)), pd


def map_drawn(M):
    """The parts the map draws: those on some stage's chain."""
    out = set()
    for st in M["stage"].values():
        parts, _, deps, _ = stage_chain(M, st)
        out |= set(parts) | set(deps)
    return out


def map_screen(M):
    """The capability's map started at the flow: five columns in the kit's words, the
    flows in the register's order; each stage's steps folded to a count that opens in place, and with them the parts
    that carry those steps and the external dependencies those parts call, each on its stage's row and joined along
    the chain. At rest nothing is faded and no line runs to a part; pointing at a box lights its chain. Capabilities
    stay in the model and on each flow's card: capability to flow is a many-to-many cross-map, which a line from one
    capability box to a flow misstates."""
    E = cv.esc
    wires, out, r = [], [], 2

    def box(cls, key, title, sub="", ident=""):
        return (f'<a href="#" class="bx {cls}" id="{E(ident)}" data-k="{E(key)}"'
                + (f' data-node="{E(key)}"' if key[:2] in ("f:", "g:") else "")
                + f'><span class="t">{E(title)}</span>' + (f'<span class="s">{E(sub)}</span>' if sub else "") + "</a>")

    def chip(gid, sid):
        x = M["subj"][sid]
        return (f'<li><a href="#" class="pt {part_group(M, x)}" id="m-p-{E(gid)}-{E(sid)}" data-k="p:{E(sid)}" '
                f'data-part="{E(sid)}"><span class="t">{E(x.get("name", ""))}</span>'
                f'<span class="s">{E(cv.kind_label(M, x))}</span></a></li>')

    for fi, f in enumerate(M["flows"]):
        fid, n = f["flow_id"], len(f["_stages"])
        fstart = " fstart" if fi else ""
        sub = plural(n, "stage") if n else "not broken into stages in the register"
        out.append(f'<div class="cell{fstart}" style="grid-column:1;grid-row:{r} / span {max(1, n)}">'
                   + box("flow", "f:" + fid, f.get("name", ""), sub, f"m-f-{fid}") + "</div>")
        for si, st in enumerate(f["_stages"]):
            gid, cls = st["stage"], fstart if si == 0 else ""
            items = "".join(
                f'<li><a href="{E(stp.href(M, x["step"]) if stp.has_page(M, x["step"]) else "#")}" class="st" id="m-s-{E(x["step"])}" data-k="s:{E(x["step"])}" data-step="{E(x["step"])}">'
                f'{E(cv.step_title(M, x["step"], short=True))}</a>'
                + ("" if cv.carried(x) else ' <span class="na">not assessed</span>') + "</li>"
                for x in st["_steps"])
            parts, sp, deps, pd = stage_chain(M, st)
            out.append(f'<div class="cell{cls}" style="grid-column:2;grid-row:{r}">'
                       + box("stage", "g:" + gid, f'Stage {st.get("order")}: {st.get("name", "")}', "", f"m-g-{gid}") + "</div>")
            out.append(f'<div class="cell{cls}" style="grid-column:3;grid-row:{r}">'
                       f'<details class="steps" id="m-d-{E(gid)}" data-k="g:{E(gid)}" data-row="{E(gid)}">'
                       f'<summary>{fold_count(M, st["_steps"])}</summary><ul>{items}</ul></details></div>')
            if not parts:  # not found is not absent: the row says none is on record
                out.append(f'<div class="cell chain{cls}" style="grid-column:4;grid-row:{r}">'
                           f'<div class="fold none" data-k="g:{E(gid)}">no part on record</div></div>')
            for col, ids, word in ((4, parts, "part"), (5, deps, "external dependency")):
                if not ids:
                    continue
                said = plural(len(ids), word).replace("dependencys", "dependencies")
                out.append(f'<div class="cell chain{cls}" data-of="{E(gid)}" style="grid-column:{col};grid-row:{r}">'
                           f'<div class="fold" data-k="g:{E(gid)}">{said}</div>'
                           f'<ul class="chips">{"".join(chip(gid, p) for p in ids)}</ul></div>')
            wires += [[f"m-f-{fid}", f"m-g-{gid}"], [f"m-g-{gid}", f"m-d-{gid}"]]
            wires += [[f"m-s-{s}", f"m-p-{gid}-{p}"] for s, p in sp]
            wires += [[f"m-p-{gid}-{p}", f"m-p-{gid}-{d}"] for p, d in pd if d in deps]
            r += 1
        if not n:
            r += 1

    heads = "".join(f'<div class="ch" tabindex="0" role="button" data-term="{E(t)}">{E(t)}</div>' for t in COLUMN_TERMS.values())
    return (f'<div class="mapframe"><div class="map" id="map">'
            f'<svg class="wires" aria-hidden="true"></svg>{heads}{"".join(out)}</div></div>'
            f'<script type="application/json" id="map-wires">{json.dumps(wires)}</script><!-- /map -->')


def map_chain(M):
    """What pointing at a box on the map lights: the kit's chain (cv.chain), except that a component or a person
    lights, of the other parts, only the external dependencies it calls, not the parts sharing its steps or called
    beside it, so its one chain reads on its own. The map starts at the flow, so no capability is in it."""
    ch = cv.chain(M)
    ext = set(M["ext"])
    out = {}
    for k, lit in ch.items():
        if k.startswith("c:"):
            continue
        lit = [x for x in lit if not x.startswith("c:")]
        if k.startswith("p:") and k[2:] not in ext:
            calls = set(M["uses"].get(k[2:], ()))
            calls |= {x["subject_id"] for d in calls for x in M["dep_parts"].get(d, [])}
            lit = [x for x in lit if not x.startswith("p:") or x[2:] in calls]
        out[k] = lit
    return ('<script type="application/json" id="map-chain">'
            + json.dumps(out, separators=(",", ":"), sort_keys=True).replace("</", "<" + chr(92) + "/") + "</script>")


def off_chain(M):
    """The parts no step's chain reaches, named in one closed line under the map."""
    drawn = map_drawn(M)
    names = [x.get("name", "") for x in sum(map_parts(M), []) if x["subject_id"] not in drawn]
    if not names:
        return ""
    return (f'<details class="leftout"><summary>Not on any process step\'s chain: {cv.esc("; ".join(names))}</summary>'
            f'<p class="note">No process step in the register is carried by these parts, and no part carrying a process step calls '
            f'them.</p></details>')


def map_counts(M):
    """The line under the title: what the map holds, in the map's words."""
    parts, deps = map_parts(M)
    return " · ".join([plural(len(M["flows"]), "flow"), plural(len(M["stage"]), "stage"), fold_count(M, [{"step": x} for x in M["step"]]),
                       plural(len(parts), "part"), plural(len(deps), "external dependency").replace("dependencys", "dependencies")])


MAP_CSS = """
/* map screen: begin */
/* The map screen: five columns in the kit's words, from the flow
   down; overview first, steps folded to counts so every word stays at 13px or more at Fit; nothing faded at rest; pointing at a box lights
   its chain and fades the rest. Tokens are prefixed --m- so the block can be lifted onto a shared style sheet. */
.pagehead h1{font:700 30px/1.15 var(--m-sans);margin:0 auto 4px 0}
p.mapcount{font:17px/1.45 var(--m-sans);color:var(--m-ink2);margin:0 0 14px}
.mapfig{background:var(--m-page);border-radius:10px;padding:14px 16px 20px;color:var(--m-ink);font:15px/1.45 var(--m-sans);min-width:0}
.maptools{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:6px;margin:0 0 12px}
.maptools button{font:600 14px var(--m-sans);color:var(--m-ink);background:var(--m-col);border:1px solid var(--m-line);border-radius:999px;padding:4px 14px;cursor:pointer}
.maptools button:hover{border-color:var(--m-acc)}
.maptools button:focus-visible{outline:2px solid var(--m-acc);outline-offset:2px}
.mapframe{overflow:auto;max-width:100%}
.mapfig .map{position:relative;display:grid;min-width:740px;
grid-template-columns:minmax(130px,1fr) minmax(150px,1.15fr) minmax(130px,.85fr) minmax(140px,1.3fr) minmax(130px,1fr);
column-gap:22px;row-gap:10px;align-items:start}
.mapfig svg.wires{position:absolute;left:0;top:0;pointer-events:none;overflow:visible}
.mapfig svg.wires path{fill:none;stroke:var(--m-link);stroke-width:1.6;transition:opacity .15s}
.mapfig .ch{grid-row:1;font:700 13px var(--m-sans);letter-spacing:.07em;text-transform:uppercase;color:var(--m-ink2);padding-bottom:4px;border-bottom:2px solid var(--m-line);margin-bottom:14px;cursor:help}
.mapfig .ch:focus-visible{outline:2px solid var(--m-acc);outline-offset:2px}
.mapfig .cell{position:relative;display:grid;gap:10px;align-content:start}
.mapfig .cell.fstart{margin-top:30px}
.mapfig .bx{display:grid;gap:2px;text-decoration:none;color:var(--m-ink);background:var(--f);border:2px solid var(--s);border-radius:10px;padding:9px 12px;transition:opacity .15s,box-shadow .15s}
.mapfig .bx .t{font-size:15px;font-weight:600;line-height:1.3}
.mapfig .bx .s{font-size:13px;color:var(--m-ink2)}
.mapfig .bx:hover,.mapfig .bx:focus-visible,.mapfig .bx.on{box-shadow:0 0 0 3px var(--m-acc);outline:none}
.mapfig .flow{--f:var(--m-bus);--s:var(--m-bus-s);border-width:3px;padding:12px 14px}
.mapfig .flow .t{font-size:18px;font-weight:700}
.mapfig .stage{--f:var(--m-col);--s:var(--m-line);border-width:1px;border-left:6px solid var(--m-bus-s);min-height:44px;align-content:center}
.mapfig details.steps{margin:0;background:var(--m-col);border:1px solid var(--m-line);border-radius:10px;padding:9px 12px;min-height:44px;transition:opacity .15s}
.mapfig details.steps summary{cursor:pointer;font-size:14px;font-weight:600;color:var(--m-ink)}
.mapfig details.steps ul{margin:8px 0 0;padding:0;list-style:none;display:flex;flex-direction:column;gap:6px;font-size:13px;color:var(--m-ink2)}
.mapfig details.steps li{margin:0}
.mapfig a.st{display:block;color:var(--m-ink);text-decoration:none;background:var(--m-page);border:1px solid var(--m-line);border-left:5px solid var(--m-bus-s);border-radius:8px;padding:5px 10px;line-height:1.35;transition:opacity .15s}
.mapfig a.st:hover,.mapfig a.st:focus-visible,.mapfig a.st.on{box-shadow:0 0 0 2px var(--m-acc);outline:none}
.mapfig .na{font-size:13px;color:var(--m-ink3);font-style:italic}
.mapfig .chain .fold{background:var(--m-col);border:1px dashed var(--m-line);border-radius:10px;padding:9px 12px;min-height:44px;font-size:14px;font-weight:600;color:var(--m-ink2);transition:opacity .15s}
.mapfig .chain ul.chips{display:none;list-style:none;margin:0;padding:0;gap:8px;flex-direction:column;align-items:flex-start}
.mapfig .chain.open .fold{display:none}.mapfig .chain.open ul.chips{display:flex}
.mapfig a.pt{display:grid;gap:1px;text-decoration:none;color:var(--m-ink);background:var(--f);border:1px solid var(--s);border-left:5px solid var(--s);border-radius:8px;padding:5px 10px;transition:opacity .15s}
.mapfig a.pt .t{font-size:14px;font-weight:600;line-height:1.3}.mapfig a.pt .s{font-size:13px;color:var(--m-ink2)}
.mapfig a.pt:hover,.mapfig a.pt:focus-visible,.mapfig a.pt.on{box-shadow:0 0 0 2px var(--m-acc);outline:none}
.mapfig a.pt.app{--f:var(--m-app);--s:var(--m-app-s)}.mapfig a.pt.agent{--f:var(--m-agt);--s:var(--m-agt-s)}
.mapfig a.pt.tec{--f:var(--m-tec);--s:var(--m-tec-s)}.mapfig a.pt.person{--f:var(--m-per);--s:var(--m-per-s)}
.mapfig .chain .fold:not(.none){cursor:pointer}.mapfig .chain .fold.none{border-style:solid;font-weight:400;font-style:italic;color:var(--m-ink3)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .mapframe{color-scheme:dark}}
:root[data-theme="dark"] .mapframe{color-scheme:dark}
.mapfig .map.focus [data-k]:not(.lit){opacity:.18}
.mapfig .map.focus svg.wires path:not(.lit){opacity:.12}
.canvas.idle{grid-template-columns:minmax(0,1fr) 0 0}.canvas.idle>.divider,.canvas.idle>.rail{display:none}
/* map screen: end */
"""

MAP_JS = """<script>
(function () {  // the map screen: pointing lights a box's chain and fades the rest; a click opens the box's page in the rail
  var map = document.getElementById('map'); if (!map) return;
  var svg = map.querySelector('svg.wires'), CHAIN = {}, WIRES = [], held = null, z = """ + str(FIT_ZOOM) + """;
  try { CHAIN = JSON.parse(document.getElementById('map-chain').textContent); } catch (e) {}
  try { WIRES = JSON.parse(document.getElementById('map-wires').textContent); } catch (e) {}
  function draw() {  // the lines: flow to stage, stage to its steps; none from a stage to a part
    var m = map.getBoundingClientRect(), NS = 'http://www.w3.org/2000/svg';
    svg.innerHTML = ''; svg.setAttribute('width', 0); svg.setAttribute('height', 0);
    svg.setAttribute('width', map.scrollWidth); svg.setAttribute('height', map.scrollHeight);
    WIRES.forEach(function (w) {
      var a = document.getElementById(w[0]), b = document.getElementById(w[1]); if (!a || !b) return;
      var p = a.getBoundingClientRect(), q = b.getBoundingClientRect(); if (!p.width || !q.width) return;
      var x1 = (p.right - m.left) / z, y1 = (p.top + Math.min(p.height, 44 * z) / 2 - m.top) / z;
      var x2 = (q.left - m.left) / z, y2 = (q.top + Math.min(q.height, 44 * z) / 2 - m.top) / z, mx = (x1 + x2) / 2;
      var e = document.createElementNS(NS, 'path');
      e.setAttribute('d', 'M' + x1 + ' ' + y1 + ' C' + mx + ' ' + y1 + ' ' + mx + ' ' + y2 + ' ' + x2 + ' ' + y2);
      e.dataset.a = a.dataset.k; e.dataset.b = b.dataset.k; svg.appendChild(e);
    });
    paint();
  }
  var now = null;
  function paint() {
    var lit = now ? new Set([now].concat(CHAIN[now] || [])) : held;
    map.classList.toggle('focus', !!lit);
    if (!lit) return;
    map.querySelectorAll('[data-k]').forEach(function (el) {
      var on = lit.has(el.dataset.k);
      if (el.tagName === 'DETAILS') on = on || !!Array.prototype.some.call(el.querySelectorAll('[data-k]'), function (s) { return lit.has(s.dataset.k); });
      el.classList.toggle('lit', on);
    });
    svg.querySelectorAll('path').forEach(function (p) { p.classList.toggle('lit', lit.has(p.dataset.a) && lit.has(p.dataset.b)); });
  }
  function point(el) { now = el ? el.dataset.k : null; paint(); }
  map.addEventListener('mouseover', function (ev) { var el = ev.target.closest('[data-k]'); if (el !== null || now) point(el); });
  map.addEventListener('mouseleave', function () { point(null); });
  map.addEventListener('focusin', function (ev) { point(ev.target.closest('[data-k]')); });
  map.addEventListener('focusout', function () { point(null); });
  map.addEventListener('click', function (ev) {
    var f = ev.target.closest('.chain .fold');  // a row's folded parts open with its steps
    if (f) { var d = document.getElementById('m-d-' + f.parentNode.dataset.of); if (d) d.open = true; return; }
    var el = ev.target.closest('a[data-k]'); if (!el) return;
    ev.preventDefault();
    map.querySelectorAll('.on').forEach(function (x) { x.classList.remove('on'); }); el.classList.add('on');
    if (window.cvOpen) window.cvOpen(el.dataset.k);
  });
  window.cvHold = function (keys) {  // a view in the rail lights these on the map until Escape; their steps open
    held = keys && keys.length ? new Set(keys) : null;
    if (held) map.querySelectorAll('details.steps').forEach(function (d) {
      if (d.querySelector('[data-k]') && Array.prototype.some.call(d.querySelectorAll('[data-k]'), function (s) { return held.has(s.dataset.k); })) d.open = true; });
    now = null; paint();
  };
  window.cvMark = function (key) {  // the box whose page the rail shows
    map.querySelectorAll('.on').forEach(function (x) { x.classList.remove('on'); });
    var el = key && map.querySelector('a[data-k="' + key.replace(/"/g, '') + '"]'); if (el) el.classList.add('on');
  };
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { held = null; now = null; paint(); } });
  map.querySelectorAll('details.steps').forEach(function (d) { d.addEventListener('toggle', function () {  // a stage's parts and dependencies open with its steps
    map.querySelectorAll('.chain[data-of="' + d.dataset.row + '"]').forEach(function (c) { c.classList.toggle('open', d.open); });
    draw(); }); });
  document.querySelectorAll('[data-showall]').forEach(function (b) { b.addEventListener('click', function () {
    map.querySelectorAll('details.steps').forEach(function (d) { d.open = true; }); }); });
  document.querySelectorAll('[data-collapseall]').forEach(function (b) { b.addEventListener('click', function () {
    map.querySelectorAll('details.steps').forEach(function (d) { d.open = false; }); }); });
  document.querySelectorAll('[data-zoom]').forEach(function (b) { b.addEventListener('click', function () {
    var k = b.dataset.zoom;
    z = k === 'in' ? Math.min(2, z * 1.25) : k === 'out' ? Math.max(0.5, z / 1.25) : """ + str(FIT_ZOOM) + """;
    map.style.zoom = z === 1 ? '' : String(z); draw(); }); });
  if (window.ResizeObserver) new ResizeObserver(draw).observe(map); else window.addEventListener('resize', draw);
  draw();
})();
</script>"""


def toolbar():
    """The map's toolbar: zoom in and out, Fit (the map at its natural size), Show all, Collapse all."""
    return ('<div class="maptools"><button type="button" data-zoom="in" aria-label="Zoom in">+</button>'
            '<button type="button" data-zoom="out" aria-label="Zoom out">&minus;</button>'
            '<button type="button" data-zoom="fit">Fit</button>' + SHOW_ALL + COLLAPSE_ALL + "</div>")


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

WHOLE_PART = "A measure of the whole part"  # the register's own words for a part measure with no operation
NO_STEP = "Its operation is not one this part performs a process step with"
NO_ALERT_THRESHOLD = (fo.THRESHOLD.split("*")[1] + " No alert is proposed on this measure. Any value it is judged "
                      "against, a number in its name included, is the operators' to set.")


def gap_layer(R, question):
    """The layer a measure-gaps.csv question is about, read off flow_outputs' coverage receipt: the time limit and a
    stage's questions are the first layer the receipt lets answer them (business health), a step's two are the
    business layer after it (business impact), application and technology name their own layer, and a run metric or
    an agent question is agentic. None for a question the receipt does not ask."""
    if question == "the time limit" or question in fo.STAGE_ASKS:
        return fo.STAGE_ASKS.get(question, (fo.BUSINESS,))[0][0]
    if question in fo.STEP_QUESTIONS:
        return fo.BUSINESS[1]
    if question in fo.LAYERS:
        return question
    if question in fo.RUN_QUESTIONS or question in {a["agent_question"] for a in R.get("agent-questions", [])}:
        return "agentic"
    return None


GAP_LABELS = fo.GAP_KINDS  # measure-gaps.csv `kind` -> the words the panel opens a gap with
NO_AGENT = GAP_LABELS["does not apply"] + ": no AI agent in this flow."  # the agentic layer of an app with none


def no_agent_lines(M, P):
    """In an application with no AI agent, every box's agentic layer reads once that the layer does not apply, a gap
    of the kit's own "does not apply" kind; a gap the register records there still wins."""
    if M["agents"]:
        return
    for kind in ("flows", "stages", "steps", "parts"):
        for nd in P[kind].values():
            if not any(m["layer"] == "agentic" for m in nd["measures"]):
                nd.setdefault("gaps", {}).setdefault("agentic", cv.esc(NO_AGENT))


def measure_names(R):
    return {m["handle"]: "“" + (m.get("measure") or "") + "”" for m in R["measures"] if m.get("handle")}


def id_names(R):
    """Each register id a reason may name (a measure, a part, a stage, a flow), as the page names it."""
    names = measure_names(R)
    names.update({s["subject_id"]: s.get("name", "") for s in R["subjects"] if s.get("subject_id")})
    names.update({s["stage"]: s.get("name", "") for s in R["stages"] if s.get("stage")})
    names.update({f["flow_id"]: f.get("name", "") for f in R["flows"] if f.get("flow_id")})
    return names


def gap_label(M, g):
    """The words a gap opens with, from its `kind`: a gap counted by another measure names that measure, the first
    the reason names by id (flow_outputs --check fails a `counted by` gap whose reason names none)."""
    kind = fo.norm(g.get("kind")).lower()
    if kind not in GAP_LABELS:
        return "No measure"  # --check fails a gap with no kind, but a register is drawn whatever the check says
    if kind != "counted by":
        return GAP_LABELS[kind]
    handles = measure_names(M["R"])
    first = next((w for w in re.findall(r"[\w-]+", g.get("why") or "") if w in handles), None)
    return GAP_LABELS[kind] + (" " + handles[first] if first else "")


def gap_text(M, g):
    """A gap's line: the label of its kind, then its reason in plain words, every register id named by what it names,
    and no sources: register provenance stays off the engineer's page."""
    names = id_names(M["R"])
    why = g.get("why") or ""
    words = re.sub(r"\s*\(:\d[\d\s,–-]*\)", "", ss.plain(why))
    if names:
        ids = re.compile(r"(?<![\w-])(" + "|".join(re.escape(i) for i in sorted(names, key=len, reverse=True)) + r")(?![\w-])")
        words = ids.sub(lambda m: names[m.group(1)], words)
    words = re.sub(r"\b[Ss]teps? (\d+)\b",  # a step by the title the map gives it
                   lambda m: "“" + cv.step_title(M, m.group(1)) + "”" if m.group(1) in M["step"] else m.group(0), words)
    words = words.strip()
    return cv.esc(gap_label(M, g) + ": " + words + ("" if words.endswith((".", "!", "?")) else "."))


def gap_lines(M, P):
    """Per box of the panel, per layer, each measure-gaps.csv gap there, labelled by its kind. A gap on a component, or on
    one of its operations, shows under that part."""
    path = pathlib.Path(M["R"].get("_path") or "") / "measure-gaps.csv"
    if not M["R"].get("_path") or not path.exists():
        return
    R = dict(M["R"], **{"agent-questions": fo.read_csv(fo.HERE / "method" / "agent-questions.csv")})
    for g in fo.read_csv(path):
        el, layer = (g.get("element") or "").split(), gap_layer(R, fo.norm(g.get("question")))
        kind = next((k for k in ("flows", "stages", "steps", "parts") if el and el[0] in P[k]), None)
        if not (kind and layer and fo.norm(g.get("why")) and fo.norm(g.get("source"))):
            continue
        got = P[kind][el[0]].setdefault("gaps", {})
        got[layer] = (got[layer] + " " if layer in got else "") + gap_text(M, g)


def panel_data(M, docs=None):
    """Per node, the kit's measures form: rows as flow_outputs prints them, layers from method/layers.csv."""
    R = M["R"]
    method = {"measure-forms": fo.read_csv(fo.HERE / "method" / "measure-forms.csv"),
              "agent-questions": fo.read_csv(fo.HERE / "method" / "agent-questions.csv")}
    business = {sid for sid, x in M["subj"].items() if x.get("band") == "business"}

    def row(m):
        cls, said = sfv.measure_state(m)  # one rule for a measure's state, the static pages' own
        return {"id": m.get("handle", ""), "title": m.get("measure", ""),
                "layer": cv.layer_of(R, m.get("layer")) or m.get("layer", ""),
                "state": "defective" if cls == "exists" and (m.get("defect") or "").strip() else cls,
                "defect": (m.get("defect") or "").strip(),
                "alert": (m.get("alert") or "").strip().lower().startswith("yes"),
                "answers": m.get("question_it_answers", ""), "kind": fo.kind_of(method, m),
                "counted_on": m.get("counted_on", ""), "how": m.get("counted_how", ""),
                "exists_today": ("yes: " + (m.get("source_ref") or "")) if cls == "exists" else "no, " + said,
                "runbook": entry(m), "guards": guards(m)}

    expectations = {r.get("expectation_id", "").strip(): r for r in sfv.expectations(M)}

    def guards(m):  # the expectations a measure is evidence of, by party and in the party's words
        rows = [expectations[i.strip()] for i in (m.get("expectation") or "").split(";") if i.strip() in expectations]
        return "; ".join(f"{sfv.labelled(M, r.get('party', ''))}: {sfv.labelled(M, r.get('expectation', ''))}"
                         for r in rows)

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
        out["flows"][f["flow_id"]] = {"name": f.get("name", ""), "title": fp.title(M, f["flow_id"]), "measures": [row(m) for m in mine]}
        for st in f["_stages"]:
            out["stages"][st["stage"]] = {"name": f'Stage {st.get("order")}: {st.get("name", "")}', "flow": f["flow_id"],
                                          "label": f'Stage {st.get("order")}',
                                          "measures": [row(m) for m in ms if m.get("stage") == st["stage"] and not m.get("step")]}
            for x in st["_steps"]:
                out["steps"][x["step"]] = {"name": cv.step_title(M, x["step"]), "stage": st["stage"], "flow": f["flow_id"],
                                           "unassessed": not cv.carried(x),
                                           "measures": [row(m) for m in own_at_step(M, x["step"], at_op)]}
    for sid, x in M["subj"].items():
        if x.get("kind") != "element" or sid in business:
            continue
        out["parts"][sid] = {"name": x.get("name", ""), "kind": cv.kind_label(M, x),
                             "measures": [dict(row(m), n=i, at=at(op_steps(M, sid, m))) for i, m in enumerate(rail_measures(M, sid), 1)]}
    order = {sid: i for i, sid in enumerate(M["subj"])}

    def where(p, m, steps):  # the steps of these a relied-on measure serves, or what the register says instead
        here = [x for x in op_steps(M, p, m) if x in steps]
        if here:
            return at(here)
        return WHOLE_PART if not ops(m.get("operation")) else NO_STEP

    def via(pids, steps, skip=()):  # each part relied on: only its measures that bear on these steps, under its name
        rows = {p: [dict(row(m), at=where(p, m, steps)) for m in relied_here(M, p, steps) if m.get("handle") not in skip]
                for p in pids if p in out["parts"]}
        def of(p):  # how many relied-on measures the part has in each layer, so a layer's list says how many it leaves out
            n = {}
            for m in relied_measures(M, p):
                L = row(m)["layer"]
                n[L] = n.get(L, 0) + 1
            return n
        return [{"part": p, "name": out["parts"][p]["name"], "measures": rows[p], "of": of(p)}
                for p in sorted(rows, key=lambda p: order.get(p, 0)) if rows[p]]
    rel, under = relied_on(M), node_steps(M)
    nodes = node_parts(M, rel)
    for sid, nd in out["steps"].items():
        nd["via"] = via(rel.get(sid, ()), {sid}, {r["id"] for r in nd["measures"]})
    for gid, nd in out["stages"].items():
        nd["via"] = via(nodes.get("g:" + gid, ()), under["g:" + gid])
    for fid, nd in out["flows"].items():
        nd["via"] = via(nodes.get("f:" + fid, ()), under["f:" + fid])
    # the rail's header: a part's stages and flows (the steps relying on it), a dependency's reliers, a capability's group
    used = {}
    for sid, ps in rel.items():
        for q in ps:
            used.setdefault(q, set()).add(sid)
    deps = {d["subject_id"] for d in M["deps"]}
    for pid, nd in out["parts"].items():
        nd["title"] = f'External dependency: {nd["name"]}' if pid in deps else ptp.title(M, pid)  # as its page or the map names it
        steps = (used.get(pid, set()) | cv.steps_of(M, pid)) & set(out["steps"])
        nd["stages"] = [g for g in out["stages"] if any(out["steps"][x]["stage"] == g for x in steps)]
        nd["flows"] = [f for f in out["flows"] if any(out["steps"][x]["flow"] == f for x in steps)]
        if pid in deps:
            fam = {pid} | {k["subject_id"] for k in M.get("dep_parts", {}).get(pid, [])}
            nd["relied_by"] = [c for c in out["parts"] if c not in fam and fam & M["uses"].get(c, set())]

    def group(cid):  # the top of the capability's tree: its group, or none for a group itself
        top, seen = cid, set()
        while M["cap"].get(top, {}).get("parent") in M["cap"] and top not in seen:
            seen.add(top)
            top = M["cap"][top]["parent"]
        return top if top != cid else ""
    out["caps"] = {cid: {"name": c.get("name", ""), "group": group(cid)} for cid, c in M["cap"].items()}
    with (fo.HERE / "method" / "layers.csv").open(encoding="utf-8", newline="") as fh:
        import csv as _csv
        out["layers"] = [{"layer": r["layer"], "name": r["layer"][:1].upper() + r["layer"][1:], "question": r["question_it_asks"]}
                         for r in _csv.DictReader(fh)]
    out["threshold"] = fo.THRESHOLD.replace("*", "")  # an alerting measure's own Threshold line, as the kit's alert form words it
    out["threshold_none"] = NO_ALERT_THRESHOLD  # every other measure's Threshold line: the same operator value, no alert
    out["docs"] = docs or {}
    out["flowpages"] = {f["flow_id"]: fp.href(f["flow_id"]) for f in M["flows"]}  # each flow's own page, as its pick links it
    out["steppages"] = {sid: stp.href(M, sid) for sid in M["step"] if stp.has_page(M, sid)}  # each process step's own page
    out["partpages"] = {pid: ptp.href(M, pid) for pid in M["subj"] if ptp.has_page(M, pid)}  # each part's own page
    out["drawn"] = DRAWN  # what each own page opens on, which the link to it under the panel's title reads
    out["terms"] = glossary_terms(M)
    gap_lines(M, out)
    no_agent_lines(M, out)
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
.canvas{--rail:320px;display:grid;grid-template-columns:minmax(0,1fr) 14px var(--rail);column-gap:0;row-gap:14px;align-items:start}.divider{align-self:stretch;position:relative;cursor:col-resize;touch-action:none;outline:none}.divider::before{content:"";position:absolute;top:0;bottom:0;left:6px;width:2px;border-radius:1px;background:var(--m-line)}.divider:hover::before,.divider.dragging::before{background:var(--m-ink3)}.divider:focus-visible::before{left:5px;width:4px;background:var(--m-ink)}.rail{position:sticky;top:8px;display:grid;gap:12px;max-height:96vh;overflow:auto}.panel{background:var(--m-col);border:1px solid var(--m-line);border-radius:6px;padding:12px;font-size:13px;}.panel h3{font:600 13px var(--m-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--m-ink3);margin:0 0 6px}
.side{background:var(--m-col);border:1px solid var(--m-line);border-radius:6px;padding:12px;font-size:13px}
.side h3{font:600 13px var(--m-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--m-ink3);margin:10px 0 6px}
.lenses{display:flex;flex-wrap:wrap;gap:4px}
.lenses button{font:13px var(--m-sans);color:var(--m-ink);background:var(--m-col);border:1px solid var(--m-link);border-radius:4px;padding:3px 9px;cursor:pointer}
.lenses button[aria-pressed="true"]{background:var(--m-ink);color:var(--m-col)}
.side select{font:13px var(--m-sans);margin-top:6px;max-width:100%}
.sw{display:inline-block;width:14px;height:12px;border:1px solid var(--m-ink3);vertical-align:-1px;margin-right:6px}
.key div{margin:2px 0}
#readout ul{padding-left:18px;margin:4px 0}#readout ul.lines{list-style:none;padding-left:0}#readout .mof{margin:0 0 6px}#readout h4{font-size:13px;margin:10px 0 2px}#readout dl{display:grid;grid-template-columns:max-content 1fr;gap:2px 8px;font-size:13px;margin:4px 0 8px}#readout dt{color:var(--m-ink3)}#readout dd{margin:0;min-width:0;overflow-wrap:anywhere}#readout pre{white-space:pre-wrap;margin:0}
#readout li{margin-bottom:4px}#readout li.at{margin:8px 0 2px;font-weight:600;color:var(--m-ink2)}.warn-state{color:var(--m-acc);font-weight:600}.warn-tag{color:var(--m-acc)}#readout details.via>ul.lines{padding-left:16px;border-left:1px solid var(--m-line);margin-left:4px}
.note{font-size:13px;color:var(--m-ink2)}
.tables{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:16px;margin-top:18px}
.tables h2{margin-top:10px}
table.readiness,table.agent{border-collapse:collapse;width:100%;font-size:13px;background:var(--m-col);border:1px solid var(--m-page)}
table.readiness th,table.readiness td,table.agent th,table.agent td{text-align:left;vertical-align:top;padding:5px 8px;border-top:1px solid var(--m-page)}
table.readiness thead th,table.agent thead th{font:13px var(--m-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--m-ink3)}
.tag{font:13px var(--m-mono);color:var(--m-ink3)}.ref{color:var(--m-ink3);font-size:13px}
details{margin:6px 0}summary{cursor:pointer}
.words table{max-width:none}
.words summary{cursor:pointer}.words summary h2{display:inline-block;border-top:none;margin:20px 0 6px;padding-top:0}
.words td{word-break:break-word}
table.readiness tr[hidden]{display:none}table.readiness ol.nums{margin:0;padding-left:20px}table.readiness ol.nums li{margin:0}table.readiness .crumb{font:inherit;font-weight:600;color:var(--m-acc);background:none;border:0;padding:0;cursor:pointer;text-align:left;text-decoration:underline}table.readiness tr.here>*{background:var(--m-page)}table.readiness tr.here>th{box-shadow:inset 3px 0 0 var(--m-acc)}
.termtip{position:absolute;z-index:5;max-width:22rem;background:var(--m-col);border:1px solid var(--m-link);border-radius:4px;padding:6px 8px;font-size:13px;box-shadow:0 2px 6px rgba(0,0,0,.15)}
.railhead{position:sticky;top:0;z-index:3;background:var(--m-col);margin:0 0 4px;padding:0 0 8px;border-bottom:1px solid var(--m-line)}.railhead[hidden]{display:none}.railhead .railclose{position:absolute;top:0;right:0;font:400 24px/1 var(--m-sans);color:var(--m-ink2);background:none;border:0;padding:2px 6px;cursor:pointer}.railhead .railclose:hover,.railhead .railclose:focus-visible{color:var(--m-ink)}.railhead .trail,.railhead h2{padding-right:36px}.railhead .trail{font-size:13px;margin:0;color:var(--m-ink2)}.railhead .crumb{font:inherit;color:var(--m-acc);background:none;border:0;padding:0;cursor:pointer;text-decoration:underline}.railhead h2{font-size:20px;line-height:1.25;margin:2px 0 4px;border-top:none;padding-top:0}#stagedocs{margin:0}.rail a{color:var(--m-acc)}
.pagehead{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 16px}.pagehead h1{margin-right:auto}
details.glossary{margin:0}details.glossary[open]{flex-basis:100%;order:2}
section.case[hidden]{display:none}details.glossary>summary{display:inline-block;font:13px var(--m-sans);color:var(--m-acc);text-decoration:underline;cursor:pointer}
details.glossary[open]>summary{margin-bottom:6px}

@media (max-width:1100px){.canvas,.tables{grid-template-columns:minmax(0,1fr)}.divider{display:none}.rail{position:static;max-height:none}}
.panel .seqhead{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.panel .seqhead h3{margin:0 0 6px}
.panel .widen{font:13px var(--m-sans);color:var(--m-ink);background:var(--m-col);border:1px solid var(--m-link);border-radius:4px;padding:2px 8px;cursor:pointer}
.panel .widen[aria-pressed="true"]{background:var(--m-ink);color:var(--m-col)}
.canvas.wide-seq{--rail:min(900px,62vw)}
/* stage drawing names: begin */
/* stage_flow_views.py still draws with these names; they point at the map screen's tokens until it uses them */
.casemoves{--paper:var(--m-col);--slate:var(--m-ink);--g200:var(--m-page);--g500:var(--m-ink3);--g600:var(--m-ink2);--ivory:var(--m-col);--clay-d:var(--m-acc);--sans:var(--m-sans);--serif:var(--m-sans)}
/* stage drawing names: end */
.rail .casemoves .card dl,.rail .casemoves details{font-size:13px}
.canvas:not(.wide-seq) #readout .m-wide,.canvas.wide-seq #readout .m-narrow{display:none}
#readout table.mtable{border-collapse:collapse;width:100%;font-size:13px;margin:2px 0 8px}#readout table.mtable th,#readout table.mtable td{text-align:left;vertical-align:top;padding:4px 6px;border-top:1px solid var(--m-page)}
#readout table.mtable{table-layout:fixed}#readout col.c-m{width:44%}#readout col.c-s{width:17%}#readout col.c-o{width:19%}#readout col.c-a{width:20%}#readout table.mtable td{overflow-wrap:anywhere}
#readout table.mtable thead th{font:13px var(--m-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--m-ink3);border-top:0}#readout table.mtable tr.at td{font-weight:600;color:var(--m-ink2);padding-top:8px}
#readout table.mtable tr.layer th{color:var(--m-ink);padding:20px 0 0;border-top:1px solid var(--m-link)}#readout table.mtable tbody tr.layer:first-child th{border-top:0;padding-top:4px}
#readout .lname,#readout .lband{display:block;background:var(--m-page);color:var(--m-ink);font:600 14px var(--m-sans);border-radius:3px;padding:3px 8px;margin:0}
#readout .lq{display:block;font:400 13px var(--m-sans);color:var(--m-ink2);margin:3px 8px 4px}
#readout .lgroup{border-bottom:1px solid var(--m-link);padding-bottom:6px;margin:0 0 16px}#readout .lgroup>ul.lines,#readout .lgroup>div.nil{margin:2px 0 0 16px}#readout div.nil{color:var(--m-ink2);font-size:13px}
#readout li.relies,#readout table.mtable tr.relies td{font:600 13px var(--m-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--m-ink3);margin:8px 0 2px}
#readout table.mtable tr.mrow>td:first-child,#readout table.mtable tr.at td,#readout table.mtable tr.more td,#readout table.mtable tr.nil td{padding-left:16px}#readout table.mtable tr.relies td{padding:8px 6px 2px 16px}#readout table.mtable tr.nil td,#readout table.mtable .tally{color:var(--m-ink2)}
#readout table.mtable .why{display:block;color:var(--m-acc);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#readout table.mtable tr[hidden]{display:none}
#readout table.mtable .mmore{font:inherit;color:var(--m-acc);background:none;border:0;padding:0 0 0 14px;cursor:pointer;text-decoration:underline}
#readout table.mtable .mopen{font:inherit;color:var(--m-ink);background:none;border:0;padding:0;cursor:pointer;text-align:left}#readout table.mtable .mopen::before{content:"▸ ";color:var(--m-ink3)}#readout table.mtable .mopen[aria-expanded="true"]::before{content:"▾ "}
#readout table.mtable tr.mform>td{border-top:0;padding:0 6px 6px 32px}#readout table.mtable>tbody{border-bottom:1px solid var(--m-link)}#readout tr.mform[hidden]{display:none}
.rail [hidden]{display:none!important}#rail-prompt{margin:0}
#seqout section.seq[hidden]{display:none}
#insideout section.inside[hidden]{display:none}
.rail>*{min-width:0}.rail .seqfig{overflow-x:auto;overflow-y:hidden}
#insideout .seqfig{background:var(--m-col);border:1px solid var(--m-page);border-radius:4px;margin:0 0 6px;overflow-x:auto}
#insideout svg.seq{display:block;width:100%;height:auto;min-width:0;cursor:default;touch-action:auto}
#seqout .seqfig{background:var(--m-col);border:1px solid var(--m-page);border-radius:4px;margin:0 0 6px;overflow-x:auto}
#seqout svg.seq{display:block;width:100%;height:auto;min-width:0;cursor:default;touch-action:auto}
#seqout .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 10px;margin:6px 0;font-size:13px}
#seqout .card dt{color:var(--m-ink3);font-weight:600}#seqout .card dd{margin:0;overflow-wrap:anywhere}
#seqout .card ol,#seqout .card ul{margin:0;padding-left:18px}#seqout .card li{margin:0 0 3px}
#seqout details{font-size:13px;color:var(--m-ink2)}#seqout details ul{padding-left:18px;margin:4px 0}
.canvas:not(.wide-seq) #seqout .card dl{grid-template-columns:minmax(0,1fr)}
.canvas:not(.wide-seq) .insideout .card dl{grid-template-columns:minmax(0,1fr)}
.canvas:not(.wide-seq) .casemoves .card dl{grid-template-columns:minmax(0,1fr)}
svg.seq .frame{fill:none;stroke:var(--m-ink3);stroke-width:1.1}
svg.seq .tag{fill:var(--m-page);stroke:var(--m-ink3);stroke-width:1.1}
svg.seq .tagt{font:600 12px var(--m-sans);fill:var(--m-ink)}
svg.seq .nm{font-family:var(--m-sans);font-size:13px;fill:var(--m-ink);text-anchor:middle}
svg.seq .kd{font-family:var(--m-sans);font-size:11px;fill:var(--m-ink3);text-anchor:middle}
svg.seq .ll{stroke:var(--m-link);stroke-width:1.1;stroke-dasharray:4 4}
svg.seq .ar{stroke:var(--m-ink2);stroke-width:1.4;fill:none}
svg.seq .ar.unrec{stroke:var(--m-link);stroke-width:1.3;stroke-dasharray:2 3}
svg.seq .op{font-family:var(--m-mono);font-size:12px;font-weight:600;fill:var(--m-ink)}
svg.seq .tv{font-family:var(--m-sans);font-style:italic;font-size:12px;fill:var(--m-ink2)}
svg.seq .tv.dim{fill:var(--m-ink3);font-size:11.5px}
svg.seq .h{paint-order:stroke;stroke:var(--m-col);stroke-width:5px;stroke-linejoin:round}
svg.seq .hopc{fill:var(--m-col);stroke:var(--m-ink2);stroke-width:1.3}
svg.seq .hopt{font:700 11px var(--m-sans);fill:var(--m-ink);text-anchor:middle}
svg.seq .num{font:700 13px var(--m-sans);fill:var(--m-acc)}
svg.seq .qm{fill:var(--m-col);stroke:var(--m-link);stroke-width:1.3;stroke-dasharray:2 2}
svg.seq .qt{font:700 11px var(--m-sans);fill:var(--m-ink3);text-anchor:middle}
svg.seq .til{font:700 15px var(--m-sans);fill:var(--m-acc)}
svg.seq .dot{fill:var(--m-ink)}
svg.seq .core{fill:none;stroke:var(--m-ink);stroke-width:1.6}
svg.seq .sep{stroke:var(--m-ink3);stroke-width:1.1;stroke-dasharray:6 4}
svg.seq .guard{font-family:var(--m-sans);font-size:12px;fill:var(--m-ink)}
"""

JS = """<script>
(function () {
  var map = document.getElementById('map'), readout = document.getElementById('readout');
  function closeRail() {  // Show all, the panel's close control and Escape: the panel closed, the map let go
    document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'})); railHead(''); view('');
    readout.innerHTML = ''; if (window.cvMark) window.cvMark('');
    document.querySelectorAll('section.seq, section.inside, section.case').forEach(function (x) { x.hidden = true; });
  }
  document.querySelectorAll('[data-showall], .railclose').forEach(function (b) { b.addEventListener('click', closeRail); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && ev.isTrusted) closeRail(); });
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
    map.querySelectorAll('.ch[data-term]').forEach(function (g) {
      g.addEventListener('click', function (ev) { ev.stopPropagation(); term(g); });
      g.addEventListener('mouseenter', function () { if (tip.hidden || tip.dataset.term !== g.dataset.term) term(g); });
      g.addEventListener('mouseleave', function () { tip.hidden = true; });
      g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); term(g); } });
    });
  }
  terms();
  document.addEventListener('click', function (ev) { if (!ev.target.closest('.ch[data-term]')) tip.hidden = true; });
  var head = document.getElementById('railhead'), canvas = document.querySelector('.canvas');
  var VIEWS = {'s:': '.seqpanel', 'p:': '.insidepanel', 'g:': '.casepanel[data-kind="stage"]', 'f:': '.casepanel[data-kind="flow"]'};
  function view(k) {  // one view at a time: the one for the kind clicked, then Measures; nothing clicked, no rail
    if (canvas) canvas.classList.toggle('idle', !k);
    var rail = document.querySelector('.rail');  // stacked under the map on a narrow window: bring the opened page into view
    if (k && rail && getComputedStyle(rail).position !== 'sticky' && rail.getBoundingClientRect().top > window.innerHeight - 80)
      rail.scrollIntoView({block: 'start'});
    document.querySelectorAll('aside.measpanel').forEach(function (x) { x.hidden = !k || k === 'c:'; });  // a capability: its header only
    Object.keys(VIEWS).forEach(function (v) { document.querySelectorAll('aside' + VIEWS[v]).forEach(function (x) { x.hidden = v !== k; }); });
  }
  view('');
  function railHead(name, trail, st, fl, sp_, pt_, kind) {  // the rail names its subject once: the trail up the chain, the name, then links to what opens from it, named by what each is, never by the name above
    if (!head) return;
    head.hidden = !name;
    if (!name) return;
    var t = document.getElementById('railtrail'), docs = document.getElementById('stagedocs'), d = st && P.docs[st];
    t.innerHTML = trail.join(' <span class="sep">›</span> ');  // where the box is: Map, each level above, the box itself
    t.hidden = !trail.length;
    document.getElementById('railname').textContent = name;
    docs.innerHTML = !st ? '' : (d && d[P.stages[st].name] ? '' : esc(P.stages[st].label) + ': ') + Object.keys(d || {}).map(function (k) {
      return '<a href="' + esc(d[k]) + '">' + esc(kind === 'g:' && k === P.stages[st].name ? P.drawn['g:'] : k) + '</a>'; }).concat(d && (d.Alerts || d.Runbook) ? [] : ['no alerts or runbook yet']).join(' · ');  // always names its stage: its page's link, by its title
    docs.hidden = !st;
    if (sp_ && P.steppages[sp_]) { docs.innerHTML = '<a href="' + esc(P.steppages[sp_]) + '">' + esc(P.drawn['s:']) + '</a> · ' + docs.innerHTML; docs.hidden = false; }  // a process step: its own page
    if (pt_ && P.partpages[pt_]) { docs.innerHTML = '<a href="' + esc(P.partpages[pt_]) + '">' + esc(P.drawn['p:']) + '</a>' + (docs.innerHTML ? ' · ' + docs.innerHTML : ''); docs.hidden = false; }  // a part: its own page
    if (fl && P.flowpages[fl]) { docs.innerHTML = '<a href="' + esc(P.flowpages[fl]) + '">' + esc(P.drawn['f:']) + '</a>'; docs.hidden = false; }  // a flow: its own page
  }
  function mword(m) { return m.state === 'defective' ? 'exists, but misleading' : m.state === 'exists' ? 'exists' : m.state === 'nc' ? 'cannot be counted' : 'proposed'; }  // the static pages' words for a state
  function mlabel(m) { return (m.n ? m.n + '. ' : '') + esc(m.title) + (m.state === 'defective' ? ' <b class="warn-state">(' + mword(m) + ')</b>' : esc(' (' + mword(m) + ')')) + (m.alert ? ' ' + alertLink(m) : ''); }
  function alertLink(m) { return m.runbook ? '<a class="alert" href="' + esc(m.runbook) + '"><b>proposed alert</b></a>' : '<b>proposed alert</b>'; }  // the same entry the widened Alert cell opens
  function mtitle(m) { return (m.n ? m.n + '. ' : '') + esc(m.title) + (m.alert ? ' <b>proposed alert</b>' : ''); }
  function mstate(m) { return m.state === 'defective' ? '<b class="warn-state">' + esc(mword(m)) + '</b>' : esc(mword(m)); }
  function mrow(m, on, fold) {  // widened: the same measure line as a table row; opening it gives the same form
    var f = fold ? ' data-in="' + fold + '" hidden' : '';
    return '<tr class="mrow"' + f + '><td><button type="button" class="mopen" aria-expanded="false">' + mtitle(m) + '</button>' +
      (m.state === 'defective' && m.defect ? '<span class="why">Why misleading: ' + esc(m.defect) + '</span>' : '') + '</td><td>' + mstate(m) + '</td><td>' + esc(on) + '</td><td>' +
      (m.runbook ? '<a href="' + esc(m.runbook) + '">this alert&rsquo;s entry in the runbook</a>' : 'none') + '</td></tr><tr class="mform"' + (fold ? ' data-in="' + fold + '"' : '') + ' hidden><td colspan="4">' + detail(m) + '</td></tr>';
  }
  function tally(ms) {  // the states of the folded rows, in words
    var n = {};
    ms.forEach(function (m) { var s = mword(m); n[s] = (n[s] || 0) + 1; });
    return ['exists, but misleading', 'exists', 'proposed', 'cannot be counted'].filter(function (s) { return n[s]; }).map(function (s) { return n[s] + ' ' + s; }).join(' · ');
  }
  function detail(m) {
    var rows = [['Answers', esc(m.answers)], ['Kind', esc(m.kind)], ['Counted on', esc(m.counted_on)],
      ['Counted how', /^(oc |psql|curl|kubectl)|-- psql/.test(m.how) ? '<pre>' + esc(m.how) + '</pre>' : esc(m.how)], ['Exists today', esc(m.exists_today)]].concat(m.guards ? [['Expectation it guards', esc(m.guards)]] : []).concat(m.defect ? [['Why misleading', esc(m.defect)]] : []).concat([['Threshold', esc(m.alert ? P.threshold : P.threshold_none)]]).concat(m.runbook ? [['Its alert', '<a href="' + esc(m.runbook) + '">this alert&rsquo;s entry in the runbook</a>']] : []);
    return '<dl>' + rows.map(function (r) { return '<dt>' + r[0] + '</dt><dd>' + r[1] + '</dd>'; }).join('') + '</dl>';
  }
  var MAPC = '<button type="button" class="crumb" data-close>Map</button>';  // the trail's first crumb: the map, nothing picked
  function crumb(label, node) { return node ? '<button type="button" class="crumb" data-go="' + esc(node) + '">' + esc(label) + '</button>' : esc(label); }
  var OF = {'f:': 'Of this flow, and of the parts its process steps rely on', 'g:': 'Of this stage, and of the parts its process steps rely on',
    's:': 'Of this process step, and of the parts it relies on', 'p:': 'Of this part'};  // whose measures these are
  function either(xs) { return xs.join(', '); }  // several flows, or several reliers: one place in the trail
  function openNode(node) {
    var k = node.slice(0, 2), id = node.slice(2), nd, trail, st = '';
    if (k === 's:') { nd = P.steps[id]; if (!nd) return false; trail = [crumb(P.flows[nd.flow].title, 'f:' + nd.flow), crumb(P.stages[nd.stage].name, 'g:' + nd.stage)]; st = nd.stage; }
    else if (k === 'g:') { nd = P.stages[id]; if (!nd) return false; trail = [crumb(P.flows[nd.flow].title, 'f:' + nd.flow)]; st = id; }
    else if (k === 'f:') { nd = P.flows[id]; if (!nd) return false; trail = []; }
    else if (k === 'p:') {  // a part: its flow, and its stage's documents when it is used in one stage only; a dependency: the parts relying on it
      nd = P.parts[id]; if (!nd) return false;
      if (nd.relied_by) trail = nd.relied_by.length ? [either(nd.relied_by.map(function (q) { return crumb(P.parts[q].title, 'p:' + q); }))] : [];
      else { trail = nd.flows.length ? [either(nd.flows.map(function (f) { return crumb(P.flows[f].title, 'f:' + f); }))] : []; st = nd.stages.length === 1 ? nd.stages[0] : ''; }
    }
    else if (k === 'c:') {  // a capability: its group above it, and nothing else in the rail
      nd = P.caps[id]; if (!nd) return false;
      view(k); railHead(nd.name, [MAPC].concat(nd.group ? [crumb(P.caps[nd.group].name, 'c:' + nd.group)] : [], [esc(nd.name)]), '');
      document.dispatchEvent(new CustomEvent('cvpick', {detail: node}));
      return true;
    }
    else return false;
    trail = [MAPC].concat(trail, [esc(nd.title || nd.name)]);
    view(k); railHead(nd.name, trail, st, k === 'f:' ? id : '', k === 's:' ? id : '', k === 'p:' ? id : '', k);
    document.dispatchEvent(new CustomEvent('cvpick', {detail: node}));  // a pick not on the folded map still reaches its view
    var out = '<p class="note mof">' + OF[k] + '</p>';
    var line = function (m) { return '<li><details><summary>' + mlabel(m) + '</summary>' + detail(m) + '</details></li>'; };
    var narrow = '', wide = '', self = {'s:': 'this process step', 'p:': 'this part', 'g:': 'this stage', 'f:': 'this flow'}[k], nf = 0;
    var RELIES = k === 's:' ? 'On parts it relies on' : 'On parts its process steps rely on', NONE = 'No measure on record';
    var UNASSESSED = 'Not assessed: no part carrying this process step was found in the sources examined.';
    P.layers.forEach(function (L) {  // each layer its own group: a band with its name, its question beneath, a rule closing it
      var inL = function (m) { return m.layer === L.layer; }, ms = nd.measures.filter(inL);
      var vs = (nd.via || []).map(function (v) { return {name: v.name, of: v.of[L.layer] || 0, ms: v.measures.filter(inL)}; }).filter(function (v) { return v.ms.length; });
      wide += '<tr class="layer"><th colspan="4" scope="colgroup"><span class="lname">' + esc(L.name) + '</span><span class="lq">' + esc(L.question) + '</span></th></tr>';
      narrow += '<section class="lgroup"><h4 class="lband">' + esc(L.name) + '</h4><p class="lq">' + esc(L.question) + '</p>';
      if (!ms.length && !vs.length) {  // not found is not absent: a layer the run gapped says why, one it did not says only that none is on record
        var gap = (nd.gaps || {})[L.layer], nil = nd.unassessed ? UNASSESSED : gap || NONE;  // each gap opens with its kind
        wide += '<tr class="nil"><td colspan="4">' + nil + '</td></tr>'; narrow += '<div class="nil">' + nil + '</div></section>'; return; }
      var last = '', lastW = '';
      wide += ms.map(function (m) { var head = m.at && m.at !== lastW ? '<tr class="at"><td colspan="4">' + esc(m.at) + '</td></tr>' : ''; lastW = m.at || lastW; return head + mrow(m, self); }).join('') +
        (vs.length ? '<tr class="relies"><td colspan="4">' + RELIES + '</td></tr>' : '') +
        vs.map(function (v) {  // every part relied on is counted: its first row, the rest folded with their states
          var rest = v.ms.slice(1), f = 'mf' + (nf++);
          var on = function (m) { return v.name + ': ' + m.at; };  // which of this box's steps the measure serves, or the register's word for none
          return mrow(v.ms[0], on(v.ms[0])) + (rest.length ? '<tr class="more"><td colspan="4"><button type="button" class="mmore" data-fold="' + f + '" aria-expanded="false">' +
            esc('… ' + rest.length + ' more on ' + v.name) + '</button> <span class="tally">' + tally(rest) + '</span></td></tr>' +
            rest.map(function (m) { return mrow(m, on(m), f); }).join('') : ''); }).join('');
      narrow += '<ul class="lines">' + ms.map(function (m) {
        var head = m.at && m.at !== last ? '<li class="note at">' + esc(m.at) + '</li>' : ''; last = m.at || last;
        return head + line(m); }).join('') + (vs.length ? '<li class="relies">' + RELIES + '</li>' : '') + vs.map(function (v) {
        var at = '';  // headed by the step each serves, as this box's own measures are
        return '<li><details class="via"><summary>' + esc(v.name + ' (' + v.ms.length + ' of its ' + v.of + (v.of === 1 ? ' measure' : ' measures') + ' here') + (function (d) { return d ? ', <b class="warn-state">' + d + ' ' + esc('exists, but misleading') + '</b>' : ''; })(v.ms.filter(function (m) { return m.state === 'defective'; }).length) + ')' +
          '</summary><ul class="lines">' + v.ms.map(function (m) { var head = m.at !== at ? '<li class="note at">' + esc(m.at) + '</li>' : ''; at = m.at; return head + line(m); }).join('') + '</ul></details></li>'; }).join('') + '</ul></section>';
    });
    out += '<div class="m-narrow">' + narrow + '</div><div class="m-wide"><table class="mtable"><colgroup><col class="c-m"><col class="c-s"><col class="c-o"><col class="c-a"></colgroup>' +
      '<thead><tr><th scope="col">Measure</th><th scope="col">State</th><th scope="col">On</th><th scope="col">Alert</th></tr></thead><tbody>' + wide + '</tbody></table></div>';
    readout.innerHTML = out;
    return true;
  }
  window.cvOpen = openNode;  // the map's click opens the box's page here
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
  });
  if (head) head.addEventListener('click', function (ev) {  // the trail clicks up the chain, as a click on the map would
    var b = ev.target.closest('button.crumb'); if (!b) return;
    if (b.hasAttribute('data-close')) { closeRail(); return; }
    if (window.cvMark) window.cvMark(b.dataset.go);
    openNode(b.dataset.go);
  });
})();
</script>"""


CASE_JS = """<script>
(function () {  // how a case moves: the stage or the flow last clicked on the map
  function show(node) {
    document.querySelectorAll('section.case').forEach(function (s) { s.hidden = s.dataset.case !== node; });
  }
  document.addEventListener('cvpick', function (ev) { if (/^[fg]:/.test(ev.detail)) show(ev.detail); });
  document.querySelectorAll('[data-showall]').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('section.case').forEach(function (s) { s.hidden = true; });
    });
  });
})();
</script>"""


INSIDE_JS = """<script>
(function () {  // inside this part: the part last clicked on the map
  var out = document.getElementById('insideout'); if (!out) return;
  var panel = out.closest('aside');
  function show(pid) {  // a person has nothing inside: no panel
    var any = false;
    out.querySelectorAll('section.inside').forEach(function (s) { s.hidden = s.dataset.inside !== pid; any = any || !s.hidden; });
    if (panel) panel.hidden = !any;
  }
  document.addEventListener('cvpick', function (ev) {
    out.querySelectorAll('g.oprow.on').forEach(function (r) { r.classList.remove('on'); });
    if (window.cvHold) window.cvHold(null);
    if (ev.detail.slice(0, 2) === 'p:') show(ev.detail.slice(2));
  });
  out.addEventListener('click', function (ev) {  // an operation lights, on the map, the part and the process steps it serves
    var row = ev.target.closest('g.oprow'); if (!row) return;
    var was = row.classList.contains('on');
    document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}));  // the map lets go of what it held
    if (was) return;
    var pid = row.closest('section.inside').dataset.inside;
    var steps = (row.dataset.steps || '').split(' ').filter(Boolean);
    row.classList.add('on');
    if (window.cvHold) window.cvHold(['p:' + pid].concat(steps.map(function (s) { return 's:' + s; })));
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
  var canvas = document.querySelector('.canvas');
  var panel = out.closest('.seqpanel'), rail = out.closest('.rail');
  function show(sid) {
    var hit = false;
    out.querySelectorAll('section.seq').forEach(function (s) { var on = s.dataset.seq === sid; s.hidden = !on; hit = hit || on; });
    if (hit && rail && getComputedStyle(rail).position === 'sticky' && panel.offsetTop - rail.scrollTop > rail.clientHeight - 80)
      rail.scrollTop = panel.offsetTop - 8;
  }
  document.addEventListener('cvpick', function (ev) { if (ev.detail.slice(0, 2) === 's:') show(ev.detail.slice(2)); });
  document.querySelectorAll('[data-widen]').forEach(function (b) {
    b.addEventListener('click', function () {  // the map keeps its scale and scrolls in its frame; it is never zoomed for the reader
      var on = canvas.classList.toggle('wide-seq');
      document.querySelectorAll('[data-widen]').forEach(function (w) {
        w.setAttribute('aria-pressed', on); w.textContent = on ? 'Narrow this panel' : 'Widen this panel';
      });
    });
  });
})();
</script>"""

RAIL_FIG_JS = """<script>
(function () {  // a drawing in the rail is never zoomed out for the reader: its smallest text keeps the panel's body size,
  // and a drawing wider than the panel at that size scrolls inside its own frame
  document.querySelectorAll('.rail .seqfig').forEach(function (f) {
    var svg = f.querySelector('svg'); if (!svg) return;
    var vb = (svg.getAttribute('viewBox') || '').split(/[\\s,]+/).map(Number), w = vb[2];
    var sizes = [].map.call(svg.querySelectorAll('text'), function (t) { return parseFloat(getComputedStyle(t).fontSize) || 0; })
      .filter(function (s) { return s > 0; });
    var body = parseFloat(getComputedStyle(f.closest('.panel') || f.parentNode).fontSize) || 13;
    if (w > 0 && sizes.length && !svg.style.width) svg.style.minWidth = Math.ceil(w * body / Math.min.apply(null, sizes)) + 'px';
  });
})();
</script>"""


def seq_panel(M):
    """The step, in order: a panel of its own beside the measures panel, empty until a step is clicked; each step's
    sequence drawing and scenario card drawn once, shown by the click on the step."""
    blocks = []
    for f in M["flows"]:
        for st in f["_stages"]:
            for x in st["_steps"]:
                blocks.append(f'<section class="seq" data-seq="{cv.esc(x["step"])}" hidden>{ss.block(M, x["step"])}</section>')
    return ('<aside class="panel seqpanel" hidden><div class="seqhead"><h3>How this process step is carried out</h3>'
            '<button type="button" class="widen" data-widen aria-pressed="false">Widen this panel</button></div>'
            '<div id="seqout">' + "".join(blocks) + "</div></aside>")


def case_panels(M, docs):
    """How a case moves: through a stage (its state machine and card) and end to end (the stages in order and the
    flow's card), each a panel of its own, empty until a stage or a flow is clicked."""
    def panel(title, kind, blocks):
        return (f'<aside class="panel casepanel" data-kind="{kind}" hidden><div class="seqhead"><h3>{cv.esc(title)}</h3>' +
                f'<button type="button" class="widen" data-widen aria-pressed="false">Widen this panel</button></div>'
                f'<div class="casemoves">' + "".join(blocks) + "</div></aside>")
    stages = [f'<section class="case" data-case="g:{cv.esc(st["stage"])}" hidden>'
              f'{sfv.stage_card(M, st["stage"], docs)}{sfv.stage_sources(M, st["stage"])}</section>'
              for f in M["flows"] for st in f["_stages"]]
    flows = [f'<section class="case" data-case="f:{cv.esc(f["flow_id"])}" hidden>'
             + (sfv.flow_block(M, f["flow_id"], docs) if f["_stages"] else
                '<p class="note">The register does not break this flow into stages, so there is no order of stages '
                'to draw.</p>') + '</section>'
             for f in M["flows"]]
    return panel("How a case moves through this stage", "stage", stages) + panel("How a case moves end to end", "flow", flows)


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
    blocks = [f'<section class="inside" data-inside="{cv.esc(p)}" hidden>{kind_said(M, p, pi.block(M, p))}</section>'
              for p in pi.parts(M) if drawn is None or p in drawn]
    return ('<aside class="panel insidepanel" hidden><div class="seqhead"><h3>Inside this part</h3>'
            '<button type="button" class="widen" data-widen aria-pressed="false">Widen this panel</button></div>'
            '<div id="insideout" class="insideout">' + "".join(blocks) + "</div></aside>")


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def fold_count(M, steps):
    """"2 process steps · 4 outcomes": a stage's endings are unnumbered and are not process steps."""
    ends = sum(1 for x in steps if cv.is_outcome(M, x["step"]))
    acts = len(steps) - ends
    return " · ".join(([plural(acts, "process step")] if acts or not ends else []) + ([plural(ends, "outcome")] if ends else []))


DRAWN = {"f:": "Value stream", "g:": "Process diagram", "s:": "Sequence diagram", "p:": "Operations"}  # each kind's own page, by its drawing
SHOW_ALL = '<button type="button" class="showall" data-showall>Show all</button>'
COLLAPSE_ALL = '<button type="button" class="collapseall" data-collapseall>Collapse all</button>'


def rail_head():
    """The rail names its subject once, above every panel: the trail back up the chain, the thing clicked in large
    type, and for anything in a stage that stage's Alerts and Runbook. Filled by railHead in JS."""
    return ('<header id="railhead" class="railhead" hidden>'
            '<button type="button" class="railclose" aria-label="Close">\u00d7</button><p class="trail" id="railtrail"></p>'
            '<h2 id="railname"></h2><p class="note" id="stagedocs" hidden></p></header>')

def left_out(M):
    """The map's Not drawn line: the left-out steps and stages."""
    mine = list(M.get("_left_out", []))
    if not mine:
        return ""
    steps = "; ".join(f'{M["_step_label"].get(sid) or "Process step " + sid}: {name}' for sid, name in mine)
    stages = (" A stage whose every process step is of this kind keeps them all, drawn as not assessed, so no stage the "
              "register gives a flow is dropped.")
    return (f'<details class="leftout"><summary>Not drawn: process steps nothing performs whose only basis is a reference model: {cv.esc(steps)}</summary>'
            f'<p class="note">Judged from each process step\'s own source text, as the register has no per-step source ids: a process step '
            f'with no performer is left out unless its source cites a code line, names a file, a document section or a '
            f'person asked. Any such evidence keeps it, drawn as not assessed.{cv.esc(stages)}</p></details>')




MADE_FILE = "how-this-map-was-made.html"


def made_page(M, reg_label, checked):
    """How the map was made, for whoever builds or checks it: written beside the page, never on it."""
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>{cv.esc(M['system'])}: how this map was made</title>\n<style>{cv.CSS}{CSS}</style></head><body><main>"
            f"<h1>{cv.esc(M['system'])}: how this map was made</h1>"
            f'<p class="note">Drawn from the register {cv.esc(reg_label)}.</p>{how_made(M, checked)}</main></body></html>\n')

STAGE_FILE = "STAGE.html"  # a stage's own page, beside its RUNBOOK.html and ALERT.html


def with_stage_pages(M, docs):
    """The stage documents the rail links: each stage's own page first, named by its title, then its alerts and
    runbook where written."""
    return {st: {fp.stage_name(s): f"stage-{st}/{STAGE_FILE}", **(docs or {}).get(st, {})} for st, s in M["stage"].items()}


STAGE_PICK_JS = """<script>
(function () {  // opened as STAGE.html#s:<step>: that box picked, as a click on its mark picks it
  var m = /^#s:(.+)$/.exec(decodeURIComponent(location.hash)); if (!m) return;
  var g = [].filter.call(document.querySelectorAll('svg .mark'), function (x) { return x.dataset.at === m[1]; })[0];
  if (g) g.dispatchEvent(new MouseEvent('click', {bubbles: true}));
})();
</script>"""


STAGE_CSS = """
main.stagepage{background:var(--m-page);min-height:100vh}
html:has(main.stagepage),html:has(main.stagepage) body{background:var(--m-page)}
.stagepage .seqfig{background:var(--m-col);border:1px solid var(--m-line);border-radius:6px;padding:8px;overflow-x:auto;width:max-content;max-width:100%;box-sizing:border-box}
.stagepage .casemoves details{font-size:13px;color:var(--m-ink2);max-width:72rem}
.stagepage .card{background:var(--m-col);border:1px solid var(--m-line);border-radius:10px;padding:16px 18px}
.stagepage .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:10px 16px;margin:0}
.stagepage .card dt{font-weight:700;color:var(--m-ink2)}.stagepage .card dd{margin:0}.stagepage .card ul{margin:0;padding-left:18px}
"""


def stage_page(M, stage_id, map_href, docs=None):
    """A stage's own page: the trail (the map, the flow's own page, then the stage selected on the map), the
    stage's name; the whole stage's measures with the state key, then its process diagram at its own size with each
    step's measures on it; the stage card; then the measures, which a mark picked filters to its place, as does
    #s:<step> in the address (STAGE_PICK_JS). `docs` is stage_docs' {stage: {doc: path from the map}}: the card links
    each alert to its entry in the runbook beside this page, where that runbook is written."""
    E = cv.esc
    here = {stage_id: {k: v.split("/")[-1] for k, v in (docs or {}).get(stage_id, {}).items()}}  # beside this page
    st = M["stage"][stage_id]
    f = next((x for x in M["flows"] if x["flow_id"] == st.get("flow", "")), {})
    name = fp.stage_name(st)
    trail = [(ps.MAP, map_href), (fp.title(M, st.get("flow", "")), f'../{fp.href(st.get("flow", ""))}')]
    d = sfv.stage_drawing(M, stage_id, whole=True, link=lambda sid: step_href(M, sid))
    steps = sfv.steps_of(M, stage_id)
    head = ps.frame_head(trail, name)
    if not steps:
        return _stage_html(M, name, head + ps.frame_sections("stage", f'<div class="casemoves"><div class="seqfig">{d}</div></div>',
                                                             sfv.stage_card(M, stage_id, here)))
    ms = sfv.stage_measures(M, stage_id)
    pos = {sid: k for k, sid in enumerate(steps)}
    names = {"stage": name, **{sid: cv.step_title(M, sid) for sid in steps}}
    short = f'Stage {st.get("order", "")}'
    table = sfv.measures_table(M, ms, lambda m: (m["step"], sfv.on_label(M, m["step"]), names[m["step"]]) if m.get("step") else ("stage", short, name),
                               lambda m: pos.get(m.get("step"), -1), lambda m: step_href(M, m.get("step", "")))
    body = head + ps.frame_sections("stage", f'<div class="casemoves"><div class="seqfig">{d}</div></div>',
                                    sfv.stage_card(M, stage_id, here), table, sfv.key_html())
    return _stage_html(M, name, body, sfv.names_json(names) + sfv.TABLE_JS + STAGE_PICK_JS)


def step_href(M, sid):
    """A process step's own page, from its stage's page; "" for an outcome, which has none."""
    return f"step-{sid}/{stp.FILE}" if stp.has_page(M, sid) else ""


def part_href(M, pid):
    """A part's own page, from a stage's page; "" for a part no process step relies on, which has none."""
    return f"../{ptp.href(M, pid)}" if ptp.has_page(M, pid) else ""


def _stage_html(M, name, body, tail=""):
    E = cv.esc
    system = M.get("system", "").split(" (")[0]
    return ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY. Builder: one_canvas.py -->\n<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(name)}{" · " + E(system) if system else ""}</title><style>{cv.CSS}{CSS}{sfv.CSS}{sfv.MEASURE_CSS}{STAGE_CSS}</style></head><body>'
            f'<main class="stagepage frame">{body}</main>{tail}</body></html>\n')


HASH_JS = """<script>
(function () {  // the map opened at a box's fragment (#g:ST2): that box lit and its page in the rail, as a click on it
  function go() {
    var k = decodeURIComponent(location.hash.slice(1)); if (!/^[sgfpc]:/.test(k) || !window.cvOpen) return;
    if (!window.cvOpen(k)) return;
    if (window.cvMark) window.cvMark(k);
    var el = document.querySelector('#map a[data-k="' + k.replace(/"/g, '') + '"]');
    if (el && el.scrollIntoView) el.scrollIntoView({block: 'nearest', inline: 'nearest'});
  }
  window.addEventListener('hashchange', go);
  go();
})();
</script>"""


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
    """The capability's page: its name, what the map holds, the map, and the rail its boxes open."""
    drawn = map_drawn(M)
    head = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n"
            f"     Source: {reg_label}\n     Builder: one_canvas.py\n     Build: {build_cmd}\n-->\n")
    return (head + "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{cv.esc(M['system'])} one canvas</title>\n<style>{cv.CSS}{CSS}{pi.CSS}{sfv.CSS}{MAP_CSS}</style></head><body><main>"
            f"<div class=\"pagehead\"><h1>{cv.esc(M['system'].split(' (')[0])}</h1>{cv.words(M, set(M['stage']), folded=True)}</div>"
            f'<p class="mapcount">{cv.esc(map_counts(M))}</p>'
            f'<div class="canvas idle"><figure><div class="mapfig">{toolbar()}{map_screen(M)}</div>{left_out(M)}{off_chain(M)}</figure>'
            f'<div class="divider" role="separator" aria-orientation="vertical" aria-label="Resize the map and the panels" '
            f'tabindex="0" aria-valuemin="360" aria-valuenow="0"></div>'
            f'<div class="rail">{rail_head()}{seq_panel(M)}{inside_panel(M, drawn)}{case_panels(M, docs)}'
            f'<aside class="panel measpanel" aria-live="polite" hidden><div class="seqhead"><h3>Measures</h3>'
            f'<button type="button" class="widen" data-widen aria-pressed="false">Widen this panel</button></div><div id="readout"></div></aside>'
            f'</div></div>'
            f'<script type="application/json" id="panel-data">{json.dumps(panel_data(M, docs)).replace("</", "<" + chr(92) + "/")}</script>'
            + "</main>" + cv.chain_data(M) + map_chain(M) + MAP_JS + JS + SEQ_JS + DIVIDER_JS + INSIDE_JS + CASE_JS + RAIL_FIG_JS + HASH_JS + "</body></html>\n")


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
    docs = with_stage_pages(M, stage_docs(reg))
    out.write_text(said(page(M, reg.as_posix(), cmd, (len(err), len(warn)), docs)), encoding="utf-8")
    for st in M["stage"]:  # each stage's own page, beside its runbook and alert page, back to this map by its trail
        (out.parent / f"stage-{st}").mkdir(parents=True, exist_ok=True)
        (out.parent / f"stage-{st}" / STAGE_FILE).write_text(said(stage_page(M, st, "../" + out.name, stage_docs(reg))), encoding="utf-8")
    for pid in [x for x in M["subj"] if ptp.has_page(M, x)]:  # each part's own page, in its folder beside the map
        (out.parent / ptp.href(M, pid)).parent.mkdir(parents=True, exist_ok=True)
        (out.parent / ptp.href(M, pid)).write_text(said(ptp.page(M, pid, out.name)), encoding="utf-8")
    for sid in [x for x in M["step"] if stp.has_page(M, x)]:  # each process step's own page, beside its stage's
        (out.parent / stp.href(M, sid)).parent.mkdir(parents=True, exist_ok=True)
        (out.parent / stp.href(M, sid)).write_text(said(stp.page(M, sid, out.name)), encoding="utf-8")
    gaps = fo.load(reg).get("measure-gaps", [])
    for f in M["flows"]:  # each flow's own page, in its folder beside the map, back to this map by its trail
        (out.parent / fp.href(f["flow_id"])).parent.mkdir(parents=True, exist_ok=True)
        (out.parent / fp.href(f["flow_id"])).write_text(said(fp.page(M, f["flow_id"], "../" + out.name, gaps)), encoding="utf-8")
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
