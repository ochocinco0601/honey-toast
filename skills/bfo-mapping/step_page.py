"""A process step's own page, written by one_canvas.py beside its stage's page as stage-<stage>/step-<step>/STEP.html.

In the frame of the flow and stage pages (page_style.frame_head, frame_sections): a trail back to the map, the flow's
page and the stage's page, the title naming the kind ("Process step 2.2: ..."), then three sections:
- the calls that carry it: the kit's UML sequence drawing (step_sequence.drawing), each part's measures inside its
  head, under its name and kind, a square per measure under its layer's word; a part's measure of one operation under
  the arrow that carries that operation; the process step's own
  measures a pill beside the frame's name; a part used by several stages of the flow says which. The square key ends
  the heading line. A box picked opens a panel beside the drawing with that box's measures, by layer and name, with
  their state, and filters the table; nothing is open on load;
- the card, folded: trigger, what happens in the parts' own words, outcomes, if it does not happen, timeouts and
  recovery, with where it comes from behind its own fold (step_sequence.card, readable);
- the measures, in the shared spreadsheet-style table (stage_flow_views.measures_table), every layer the method names.
Every measure on the drawing is one row of the table. Every word is 13 px or larger; nothing tells the reader what
to do. Only process steps get a page: an outcome is drawn on its stage's page."""
import html
import re

import capability_views as cv
import flow_page as fp
import page_style as ps
import stage_flow_views as sfv
import step_sequence as ss

FILE = "STEP.html"
E = cv.esc
LH, SQ, PITCH = 16, sfv.SQ, sfv.PITCH


def has_page(M, sid):
    """Whether the build writes a page for this step: a process step of a stage, never an outcome."""
    st = M["step"].get(sid)
    return bool(st) and st.get("stage") in M["stage"] and M.get("_step_label", {}).get(sid, "").startswith("Process step")


def href(M, sid):
    """Where a process step's page sits, relative to the map page."""
    return f'stage-{M["step"][sid]["stage"]}/step-{sid}/{FILE}'


def title(M, sid):
    """The page's title, "Process step 2.2: ...", which the side panel's link to it also reads."""
    return f'{M["_step_label"][sid]}: {M["step"][sid].get("name", "")}'


def norm(op):
    """An operation's name as two spellings of it compare equal: placeholders and spaces aside."""
    return re.sub(r"\s+", "", ss.norm_op(op or ""))


def _ops(v):
    return {o.strip() for o in (v or "").split(";") if o.strip()} - {"reply"}


def layer_order(M):
    return [L["layer"] for L in M["R"]["method"]["layers"]]


def measures(M, sid, sc):
    """(the process step's own measures, {part: its measures that bear on this step}), each with its layer as the
    method names it. A part's are those a step relying on it is shown (one_canvas.relied_here)."""
    import one_canvas as oc  # it imports this module; importing it back only here avoids a cycle
    R = M["R"]
    own = [dict(m, layer=cv.layer_of(R, m.get("layer")) or m.get("layer", ""))
           for m in R.get("measures", []) if m.get("step") == sid and m.get("measure")]
    parts = {pid: [dict(m, layer=cv.layer_of(R, m.get("layer")) or m.get("_layer", ""))
                   for m in oc.relied_here(M, pid, [sid])] for pid in sc["pids"]}
    return own, parts


def placed(M, sc, parts):
    """({(sender, receiver, label): [(part, measure)]}, {id(measure)}): each part's measure that names an operation,
    under the first arrow drawn that carries that operation to the part, else from it. A measure no arrow carries
    stays in its part's head."""
    msgs = [m for m in list(ss.walk(sc["items"])) + list(ss.walk(sc.get("norec", []))) if m.get("label")]
    where, done = {}, set()
    for pid, ms in parts.items():
        for m in ms:
            mo = {norm(o) for o in _ops(m.get("operation"))}
            if not mo:
                continue
            hits = [x for x in msgs if norm(x["label"]) in mo]
            hit = next((x for x in hits if x.get("to") == pid), None) or next((x for x in hits if x.get("frm") == pid), None)
            if hit:
                where.setdefault((hit.get("frm"), hit.get("to"), hit["label"]), []).append((pid, m))
                done.add(id(m))
    return where, done


def reach(M, pid, sid):
    """"serves Stages 1–4" for a part whose process steps serve more than one stage of this step's flow, else ""."""
    flow = M["stage"][M["step"][sid]["stage"]].get("flow")
    orders = sorted({int(M["stage"][M["step"][p["step"]]["stage"]].get("order") or 0)
                     for p in M["R"]["participation"]
                     if p.get("subject_id") == pid and p.get("step") in M["step"]
                     and M["stage"].get(M["step"][p["step"]].get("stage"), {}).get("flow") == flow})
    if len(orders) < 2:
        return ""
    if orders == list(range(orders[0], orders[-1] + 1)):
        return f"serves Stages {orders[0]}–{orders[-1]}"
    return "serves Stages " + ", ".join(str(o) for o in orders)


def head_marks(M, ms, w, said, on_calls, layers):
    """(height, draw(cx, y)): what a head holds under its name and kind, centred: its reach, then each layer's word
    with a square per measure wrapping inside `w`; "No measure" when it has none, here or on a call below."""
    per = max(1, int((w + PITCH - SQ) // PITCH))
    plan, h = [], 6
    for ln in cv.wrap(said, w, 13, 10 ** 6) if said else []:
        plan.append(("kd", ln, h))
        h += LH
    for L in layers:
        mine = [m for m in ms if m["layer"] == L]
        if not mine:
            continue
        plan.append(("ml", L.split()[-1].capitalize(), h + 6))
        h += LH + 6
        for k in range(0, len(mine), per):
            plan.append(("row", mine[k:k + per], h))
            h += PITCH
    if not ms and not on_calls:
        plan.append(("gp", "No measure", h + 4))
        h += LH
    h += 8

    def draw(cx, y):
        out = []
        for kind, v, dy in plan:
            if kind == "row":
                x0 = cx - (len(v) * PITCH - (PITCH - SQ)) / 2
                out += [sfv.square(m, x0 + PITCH * i, y + dy) for i, m in enumerate(v)]
            else:
                cls = {"kd": "kd hm", "ml": "hl", "gp": "hg"}[kind]
                out.append(f'<text x="{cx:g}" y="{y + dy + 12:g}" class="{cls}" text-anchor="middle">{E(v)}</text>')
        return "".join(out)
    return h, draw


def arrow_marks(got):
    """(height, draw(x, y)): the squares under an arrow, one mark per part, in a row."""
    def draw(x, y):
        out, dx = [], x
        for pid in dict.fromkeys(p for p, _ in got):
            ms = [m for p, m in got if p == pid]
            out.append(f'<g class="mark oncall" data-at="{E(pid)}" tabindex="0">'
                       + "".join(sfv.square(m, dx + PITCH * i, y) for i, m in enumerate(ms)) + "</g>")
            dx += PITCH * len(ms) + 8
        return "".join(out)
    return SQ, draw


def drawing(M, sid, sc, own, parts, layers):
    """The kit's sequence drawing with every measure where it counts, drawn at its natural size."""
    where, done = placed(M, sc, parts)
    pending = dict(where)

    def head(x, w):
        ms = [m for m in parts.get(x, []) if id(m) not in done]
        return head_marks(M, ms, w, reach(M, x, sid), sum(1 for m in parts.get(x, []) if id(m) in done), layers)

    def arrow(m):
        got = pending.pop((m.get("frm"), m.get("to"), m.get("label")), None)
        return arrow_marks(got) if got else None
    tag = sfv.mark_pill(own, "step", wmax=300, layers=layers)
    import one_canvas as oc  # it imports this module; importing it back only here avoids a cycle

    def link(x):  # a part's own page, opened at this process step
        h = oc.part_href(M, x)
        return f"../{h}#s:{sid}" if h else ""
    svg = ss.drawing(M, sc, "sp" + re.sub(r"[^A-Za-z0-9]", "_", sid),
                     {"head": head, "arrow": arrow, "tag": tag, "at": lambda x: x, "link": link, "numbers": False})
    w, h = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups()
    return svg.replace('<svg class="seq"', f'<svg class="seq" width="{w}" height="{h}"', 1)


def side(M, sid, own, parts, order, label, layers):
    """The panel beside the drawing: one section per box, hidden until its box is picked."""
    question = {r["layer"]: r["question_it_asks"] for r in M["R"]["method"]["layers"]}
    places = [("step", f"{label} itself", "", own)] + [
        (pid, M["subj"][pid].get("name", pid), reach(M, pid, sid), parts.get(pid, [])) for pid in order]
    secs = []
    for at, name, said, ms in places:
        body = []
        for L in layers:
            mine = [m for m in ms if m["layer"] == L]
            if mine:
                body.append(f'<h4>{E(L.capitalize())} <span>{E(question.get(L, ""))}</span></h4><ul>'
                            + "".join(f'<li><span class="dot {sfv.measure_state(m)[0]}"></span><span><b>{E(m["measure"])}</b>'
                                      f'<i>{E(sfv.measure_state(m)[1])}</i></span></li>' for m in mine) + "</ul>")
        secs.append(f'<section class="sidep" data-at="{E(at)}" hidden><h3>{E(name)}'
                    + (f'<span class="reachn">{E(said)}</span>' if said else "") + "</h3>"
                    + ("".join(body) or '<p class="none">No measure on record</p>') + "</section>")
    return '<aside class="side" hidden>' + "".join(secs) + "</aside>"


SIDE_JS = """<script>
(function () {  // a box picked opens its measures; picked again, or the filters cleared, it closes. The drawing keeps its
  // natural width: the panel opens beside it only where both fit the column, else as a sheet at the window's right edge
  var aside = document.querySelector('aside.side'), beside = document.querySelector('.beside'); if (!aside) return;
  var secs = aside.querySelectorAll('.sidep'), svg = beside.querySelector('svg.seq'), GAP = 16, SIDE = 300;
  function fits() {
    var natural = parseFloat(svg.getAttribute('width')) || svg.getBoundingClientRect().width, room = beside.clientWidth;
    return natural + GAP + SIDE <= room;
  }
  function sync() {
    var on = document.querySelector('svg .mark.on'), at = on ? on.dataset.at : null, by = !!at && fits();
    aside.hidden = !at; beside.classList.toggle('open', by); aside.classList.toggle('sheet', !!at && !by);
    secs.forEach(function (s) { s.hidden = s.dataset.at !== at; });
  }
  window.addEventListener('resize', function () { if (!aside.hidden) sync(); });
  document.querySelectorAll('svg .mark').forEach(function (g) {
    g.addEventListener('click', sync);
    g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') setTimeout(sync, 0); });
  });
  var all = document.querySelector('p.shown button.all'); if (all) all.addEventListener('click', sync);
})();
</script>"""

CSS = """
main.steppage{background:var(--m-page);min-height:100vh}
html:has(main.steppage),html:has(main.steppage) body{background:var(--m-page)}
.steppage .beside{display:grid;grid-template-columns:minmax(0,max-content);gap:16px;align-items:start}
.steppage .beside.open{grid-template-columns:max-content minmax(300px,1fr)}
.steppage .beside.open .side{max-width:340px}
.steppage .side.sheet{position:fixed;top:0;right:0;bottom:0;width:340px;max-height:none;z-index:20;border-radius:0;border-width:0 0 0 1px;box-shadow:-8px 0 24px rgba(0,0,0,.3)}
.steppage .seqfig{background:var(--m-col);border-radius:6px;overflow-x:auto;max-width:100%}
.steppage svg.seq{display:block;max-width:none;height:auto}
.steppage svg.seq .kd{font-size:13px}
.steppage svg.seq .hl{font:700 13px var(--m-sans);fill:var(--m-ink2)}
.steppage svg.seq .hm{fill:var(--m-ink2)}
.steppage svg.seq a.partlink text{fill:var(--m-acc);text-decoration:underline}.steppage svg.seq a.partlink:hover text{text-decoration-thickness:2px}
.steppage svg.seq .bp-ml{font:700 13px var(--m-sans);fill:var(--m-ink2)}
.steppage svg.seq .bp-gp{font:italic 13px var(--m-sans);fill:var(--m-bus-s)}
.steppage svg.seq .hg{font:italic 13px var(--m-sans);fill:var(--m-bus-s)}
.steppage svg .mark .hit{fill:transparent;stroke:none;pointer-events:all}
.steppage svg .mark:hover .hit,.steppage svg .mark:focus-visible .hit,.steppage svg .mark.on .hit{stroke:var(--m-acc);stroke-width:2.5}
.steppage svg .mark.oncall:hover rect.dot,.steppage svg .mark.oncall.on rect.dot{stroke:var(--m-acc);stroke-width:2}
.steppage .side{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto;background:var(--m-col);border:1px solid var(--m-line);border-radius:10px;padding:12px 14px}
.steppage .side[hidden]{display:none}
.steppage .side{overflow-wrap:anywhere;overflow-x:hidden}.steppage .sidep h3{font:700 16px/1.3 var(--m-sans);letter-spacing:0;text-transform:none;color:var(--m-ink);margin:0 0 6px}.steppage .sidep .reachn{display:block;font-size:13px;font-weight:400;color:var(--m-ink2)}
.steppage .sidep h4{font-size:14px;margin:12px 0 4px}.steppage .sidep h4 span{font-weight:400;color:var(--m-ink2);margin-left:6px}
.steppage .sidep ul{list-style:none;margin:0;padding:0}.steppage .sidep li{display:flex;gap:8px;align-items:flex-start;margin:6px 0;font-size:14px}
.steppage .sidep li .dot{flex:none;margin-top:4px}.steppage .sidep li i{display:block;font-style:normal;font-size:13px;color:var(--m-ink2)}
.steppage .sidep .none{font-style:italic;color:var(--m-ink2);margin:0}
.steppage .card{background:var(--m-col);border:1px solid var(--m-line);border-radius:10px;padding:16px 18px}
.steppage .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:10px 16px;margin:0}
.steppage .card dt{font-weight:700;color:var(--m-ink2)}.steppage .card dd{margin:0}
.steppage .card ul,.steppage .card ol{margin:0;padding-left:20px}.steppage .card li{margin:0 0 3px}
.steppage details.cites{font-size:13px;color:var(--m-ink2);margin:8px 0 0}.steppage details.cites ul{padding-left:18px;margin:4px 0}
"""


def page(M, sid, map_name):
    """A process step's own page. `map_name` is the map page's file name, two folders up."""
    import one_canvas as oc  # it imports this module; importing it back only here avoids a cycle
    stg = M["stage"][M["step"][sid]["stage"]]
    f = next((x for x in M["flows"] if x["flow_id"] == stg.get("flow", "")), {})
    system = M["system"].split(" (")[0]
    label = M["_step_label"][sid]
    name = M["step"][sid].get("name", "")
    trail = [(ps.MAP, f"../../{map_name}"), (fp.title(M, stg.get("flow", "")), f'../../{fp.href(stg.get("flow", ""))}'),
             (fp.stage_name(stg), f"../{oc.STAGE_FILE}")]
    sc = ss.scenario(M, sid)
    own, parts = measures(M, sid, sc)
    order, _ = ss.order_lifelines(M, sc)
    layers = [L for L in layer_order(M) if L in sfv.MEASURED or any(m["layer"] == L for ms in [own, *parts.values()] for m in ms)]
    svg = drawing(M, sid, sc, own, parts, layers)
    rows = [dict(m, _at="step") for m in own] + [dict(m, _at=pid) for pid in order for m in parts.get(pid, [])]
    rank = {pid: i for i, pid in enumerate(order)}
    names = {"step": f"{label} itself", **{pid: M["subj"][pid].get("name", pid) for pid in order}}
    table = sfv.measures_table(
        M, rows,
        lambda m: ("step", sfv.on_label(M, sid), cv.step_title(M, sid)) if m["_at"] == "step" else (m["_at"], names[m["_at"]], names[m["_at"]]),
        lambda m: rank.get(m["_at"], -1), layers=layers, stay=True)
    drawn = f'<div class="beside"><div class="seqfig">{svg}</div>{side(M, sid, own, parts, order, label, layers)}</div>'
    card = ss.card(M, sc, readable=True) + ss.sources(M, sc)
    body = ps.frame_head(trail, title(M, sid)) + ps.frame_sections("step", drawn, card, table, sfv.key_html(), card_open=False)
    return ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY. Builder: one_canvas.py -->\n<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(label)}: {E(name)} · {E(system)}</title><style>{cv.CSS}{oc.CSS}{sfv.MEASURE_CSS}{CSS}</style></head><body>'
            f'<main class="steppage frame">{body}</main>{sfv.names_json(names)}{sfv.TABLE_JS}{SIDE_JS}</body></html>\n')
