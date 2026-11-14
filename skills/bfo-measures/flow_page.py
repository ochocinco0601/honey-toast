"""A flow's own page, written by one_canvas.py beside the map as flow-<id>/FLOW.html.

The flow as a value stream: its stages start to end, each stage's other ways out leaving at that stage, nothing below
stage. Under each stage, and under the end for the whole flow, a "Measured here" lane: one square per business measure
counted on cases, by layer and state, wrapping to a new row as they need. Then the flow's card (one case, starts, ends, serves, delivers), then the measures
in the shared spreadsheet-style table (stage_flow_views.measures_table): Layer, Measure, State, On, Alert, a band per
layer in layer order, each row opening to its form. A lane box picked filters the measures to that place.

Every word is 13 px or larger at natural size, and nothing tells the reader what to do. The page wears the shared
style (page_style.py); its own rules draw on those tokens. It takes the model already pruned and numbered."""
import html

import capability_views as cv
import flow_outputs as fo
import page_style as ps
import stage_flow_views as sfv
import view_questions as vq

FILE = "FLOW.html"  # a flow's own page, in its own folder beside the map, as a stage's STAGE.html is
LAYERS = sfv.MEASURED  # the layers counted on cases: is the expectation met, for how many not
NO_STAGES = "The register orders no stages for this flow."
E = html.escape


def href(flow_id):
    """Where a flow's page sits, relative to the map page."""
    return f"flow-{flow_id}/{FILE}"


def title(M, flow_id):
    """The page's title, "Flow: ...", which the side panel's link to it also reads."""
    f = next((x for x in M["flows"] if x["flow_id"] == flow_id), {})
    return "Flow: " + f.get("name", flow_id)


tail_words = sfv.tail_words  # what tells each of several moves apart


def ways_out(M, st):
    """A stage's other ways out: each final state an other outcome ends a case in, with what tells its moves apart."""
    by_state = {}
    for _, m in sfv.exits(M, st["stage"]):
        s = fo.state(m.get("to_state"))
        if m.get("path") != "main" and sfv.is_final(M, s):
            by_state.setdefault(s, [])
            if m["move"] not in by_state[s]:
                by_state[s].append(m["move"])
    return [(sfv.state_name(s), tail_words(moves)) for s, moves in by_state.items()]


def gap_for(gaps, element, question):
    return next((g for g in gaps if g.get("element") == element and g.get("question") == question), None)


def flow_measures(M, flow_id, stages):
    """The business measures counted on cases that apply to this flow: at one of its steps or stages, or the flow."""
    stage_of_step = {x["step"]: x["stage"] for x in M["R"]["steps"]}
    ids = {st["stage"] for st in stages}
    return sfv.case_measures(M, lambda m: m.get("flow") == flow_id or m.get("stage") in ids
                             or stage_of_step.get(m.get("step")) in ids)


def stage_name(st):
    return f'Stage {st.get("order", "")}: {st.get("name", "")}'


def where(M, stages, m):
    """The lane a measure sits in (a stage id, or "end" for the flow's own), and the place its row names: its short
    label, with its stage since the rows are not grouped under stages here ("Stage 2 · Process step 2.1",
    "Stage 2 · Cancelled: because payment failed", "Stage 2", "Flow"), and its full name."""
    by_id = {st["stage"]: st for st in stages}
    st_of = {x["step"]: x["stage"] for x in M["R"]["steps"]}
    if m.get("step") and st_of.get(m["step"]) in by_id:
        full = fo.relabel_prose(M["_step_label"], M["R"]["steps"], cv.step_title(M, m["step"]))
        st = by_id[st_of[m["step"]]]
        short = sfv.on_label(M, m["step"])
        if not short.startswith("Process step"):  # a process step's label already names its stage
            short = f'Stage {st.get("order", "")} · {short}'
        return st_of[m["step"]], short, full
    if m.get("stage") in by_id:
        st = by_id[m["stage"]]
        return m["stage"], f'Stage {st.get("order", "")}', stage_name(st)
    f = next((x for x in M["flows"] if x["flow_id"] == stages[0].get("flow")), {}) if stages else {}
    return "end", "Flow", "Flow: " + (f.get("name", "") or f.get("flow_id", ""))


def value_stream(M, f, stages, fm, gaps):
    """The stages left to right with their other ways out, the end, and the measured-here lane under them."""
    wrap = cv.wrap
    W, SX, GAP, BH, TOP = 1160, 70, 34, 78, 20
    n = len(stages)
    BW = (W - SX - GAP * n - 10) / (n + 1)
    MID = TOP + BH / 2
    svg = [f'<circle cx="16" cy="{MID}" r="9" class="ev"/>',
           f'<line x1="25" y1="{MID}" x2="{SX - 3}" y2="{MID}" class="fl" marker-end="url(#a)"/>']
    low = TOP + BH
    OUT_Y = TOP + BH + 46
    for i, st in enumerate(stages):
        x = SX + i * (BW + GAP)
        nm = wrap(st.get("name", ""), BW - 24, 15, 3)
        svg.append(f'<a href="{E(stage_href(st["stage"]))}"><g class="stg" data-stage="{E(st["stage"])}"><rect x="{x:g}" y="{TOP}" width="{BW:g}" height="{BH}" rx="8" class="sb"/>'
                   f'<rect x="{x:g}" y="{TOP}" width="7" height="{BH}" rx="3" class="sbar"/>'
                   f'<text x="{x + 18:g}" y="{TOP + 22}" class="sno">Stage {E(str(st.get("order", "")))}</text>'
                   + "".join(f'<text x="{x + 18:g}" y="{TOP + 42 + 18 * j}" class="snm">{E(ln)}</text>' for j, ln in enumerate(nm))
                   + "</g></a>")
        svg.append(f'<line x1="{x + BW + 2:g}" y1="{MID}" x2="{x + BW + GAP - 3:g}" y2="{MID}" class="fl" marker-end="url(#a)"/>')
        outs = ways_out(M, st)
        cx = x + 18
        if outs:
            y = OUT_Y
            svg.append(f'<line x1="{cx:g}" y1="{TOP + BH}" x2="{cx:g}" y2="{y - 3}" class="fl alt" marker-end="url(#a)"/>')
            for state, why in outs:
                svg.append(f'<text x="{cx - 4:g}" y="{y + 16}" class="onm">{E(state)}</text>')
                y += 24
                for w in why:
                    for j, ln in enumerate(wrap(w, BW - 10, 13, 3)):
                        svg.append(f'<text x="{cx + (10 if j else 0):g}" y="{y + 12}" class="lb">{"· " if not j else ""}{E(ln)}</text>')
                        y += 18
                y += 8
            low = max(low, y)
        else:
            g = gap_for(gaps, st["stage"], "stage: other outcomes")
            if g and g.get("kind") == "does not apply":
                svg.append(f'<text x="{cx - 4:g}" y="{TOP + BH + 22}" class="lb">No other way out</text>')
            if g and g.get("kind") == "no record":
                svg.append(f'<line x1="{cx:g}" y1="{TOP + BH}" x2="{cx:g}" y2="{OUT_Y - 3}" class="fl gap"/>')
                svg.append(f'<text x="{cx - 4:g}" y="{OUT_Y + 16}" class="gp">Other ways out: no record</text>')
                low = max(low, OUT_Y + 26)
    ex = SX + n * (BW + GAP)
    end_txt = wrap(sfv.headline(M, f.get("ends_at", "")), BW - 16, 15, 3)
    eh = max(BH, 20 + 20 * len(end_txt))
    unrec = stages[-1].get("exit", "").strip().lower().startswith("implicit")
    svg.append(f'<rect x="{ex:g}" y="{MID - eh / 2:g}" width="{BW:g}" height="{eh}" rx="18" class="eb{" unrec" if unrec else ""}"/>'
               + "".join(f'<text x="{ex + BW / 2:g}" y="{MID + 5 - 10 * (len(end_txt) - 1) + 20 * j:g}" class="enm">{E(ln)}</text>'
                         for j, ln in enumerate(end_txt)))
    if unrec:
        svg.append(f'<text x="{ex + BW / 2:g}" y="{MID + eh / 2 + 20:g}" class="gp" text-anchor="middle">not recorded</text>')
        low = max(low, MID + eh / 2 + 30)

    LANE, KX = low + 34, 150
    svg.append(f'<text x="0" y="{LANE - 12}" class="lanet">MEASURED HERE</text><line x1="0" y1="{LANE - 4}" x2="{W}" y2="{LANE - 4}" class="lane"/>')
    deepest = LANE
    for key, x in [(st["stage"], SX + i * (BW + GAP)) for i, st in enumerate(stages)] + [("end", ex)]:
        y = LANE + 10
        mine = [m for m in fm if where(M, stages, m)[0] == key]
        svg.append(f'<g class="mark" data-at="{E(key)}" tabindex="0">')
        if not mine:
            svg.append(f'<rect x="{x:g}" y="{y}" width="{BW:g}" height="34" rx="6" class="mnone"/>'
                       f'<text x="{x + 12:g}" y="{y + 22}" class="gp">No measure</text>')
            y += 34
        else:
            body, h = sfv.layer_rows(mine, x, y, BW)  # a square per measure, at any count, wrapping inside the box
            svg.append(f'<rect x="{x:g}" y="{y}" width="{BW:g}" height="{h:g}" rx="6" class="mbox"/>' + body)
            y += h
        svg.append("</g>")
        deepest = max(deepest, y)
    H = deepest + 20
    return (f'<svg class="vs" viewBox="0 0 {W} {H:g}" width="{W}" height="{H:g}" role="img" '
            f'aria-label="{E(f.get("name", ""))}: its stages from start to end, the other ways out of each, and the measures under each">'
            '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" class="ah"/></marker></defs>' + "".join(svg) + "</svg>")


def measures_table(M, f, stages, fm):
    """The flow's measures in the shared table: the flow's own rows first in each band, then each stage's in the
    stages' order."""
    order = {st["stage"]: k for k, st in enumerate(stages)}
    by_id = {st["stage"]: st for st in stages}
    rank = lambda m: (order.get(where(M, stages, m)[0], -1), int(m["step"]) if m.get("step", "").isdigit() else 0)  # noqa: E731
    return sfv.measures_table(M, fm, lambda m: where(M, stages, m), rank,
                              lambda m: stage_href(where(M, stages, m)[0]) if where(M, stages, m)[0] in by_id else "")


def stage_href(stage_id):
    """A stage's own page, from a flow's page."""
    return f"../stage-{stage_id}/STAGE.html"


def card(M, f):
    """One case, starts, ends, serves (each party's expectation and its met-when), delivers."""
    G = sfv.GAP
    dl = vq.flow_delivers(M, f)
    P = lambda t: cv.prose(M, t)  # noqa: E731
    rows = [("One case", P(sfv.headline(M, f.get("case", ""))) or G),
            ("Starts", P(sfv.headline(M, f.get("starts_at", ""))) or G),
            ("Ends", P(sfv.headline(M, f.get("ends_at", ""))) or G)]
    serves = "".join(f'<li><b>{cv.marked(M, sfv.labelled(M, r.get("party", "")))}</b> expects '
                     f'{cv.marked(M, sfv.labelled(M, r.get("expectation", ""))) or G}.'
                     f'<div class="mw">{P("Met when: " + (sfv.labelled(M, r.get("satisfied_when", "")) or G) + ".")}</div></li>'
                     for r in sfv.by_party(M, f["flow_id"]))
    rows.append(("Serves", f"<ul>{serves}</ul>" if serves else P(sfv.headline(M, f.get("customer", ""))) or G))
    rows.append(("Delivers", "<ul>" + "".join(f"<li>{P(x)}</li>" for x in dl if x) + "</ul>" if any(dl) else G))
    return '<dl class="card">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"


CSS = """
main.flowpage{background:var(--m-page);min-height:100vh}
html:has(main.flowpage),html:has(main.flowpage) body{background:var(--m-page)}
.flowpage .vsbox{background:var(--m-col);border:1px solid var(--m-line);border-radius:10px;padding:18px 18px;overflow-x:auto;overflow-y:hidden;width:max-content;max-width:100%;box-sizing:border-box}
.flowpage .note{color:var(--m-ink2);margin:0}
svg.vs{display:block;max-width:none}
svg.vs .sb{fill:var(--m-bus);stroke:var(--m-bus-s);stroke-width:1.5}
svg.vs a:hover .sb,svg.vs a:focus-visible .sb{stroke:var(--m-acc);stroke-width:2.5}
svg.vs .sbar{fill:var(--m-bus-s)}
svg.vs .sno{font:700 13px var(--m-sans);fill:var(--m-ink2)}
svg.vs .snm{font:600 15px var(--m-sans);fill:var(--m-ink)}
svg.vs .eb{fill:var(--m-col);stroke:var(--m-ink);stroke-width:2.5}
svg.vs .eb.unrec{stroke-dasharray:7 5}
svg.vs .enm{font:600 15px var(--m-sans);fill:var(--m-ink);text-anchor:middle}
svg.vs .ev{fill:var(--m-col);stroke:var(--m-ink);stroke-width:1.6}
svg.vs .fl{stroke:var(--m-ink3);stroke-width:2;fill:none}
svg.vs .fl.alt{stroke:var(--m-bad);stroke-dasharray:6 4}
svg.vs .fl.gap{stroke:var(--m-bus-s);stroke-dasharray:2 4}
svg.vs .ah{fill:var(--m-ink3)}
svg.vs .lb{font:13px var(--m-sans);fill:var(--m-ink2)}
svg.vs .onm{font:700 14px var(--m-sans);fill:var(--m-bad)}
svg.vs .gp{font:italic 13px var(--m-sans);fill:var(--m-bus-s)}
svg.vs .lane{stroke:var(--m-line);stroke-width:2}
svg.vs .lanet{font:700 13px var(--m-sans);letter-spacing:.07em;fill:var(--m-ink2)}
svg.vs .ml{font:700 13px var(--m-sans);fill:var(--m-ink2)}
dl.card{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:10px 16px;margin:0;background:var(--m-col);border:1px solid var(--m-line);border-radius:10px;padding:16px 18px}
dl.card dt{font-weight:700;color:var(--m-ink2)}
dl.card dd{margin:0}
dl.card ul{margin:0;padding-left:18px}
dl.card .mw{display:block;color:var(--m-ink2);font-size:14px;margin-top:2px}
"""

def page(M, flow_id, map_href, gaps=()):
    """A flow's own page: the trail back to the map (opening it with the flow lit), the flow's name, its value stream
    with the measured-here lane, its card, and its measures. `gaps` is the register's measure-gaps rows."""
    f = next(x for x in M["flows"] if x["flow_id"] == flow_id)
    stages = sfv.flow_stages(M, flow_id)
    system = M["system"].split(" (")[0]
    trail = [(ps.MAP, map_href)]
    if stages:
        fm = flow_measures(M, flow_id, stages)
        drawn = f'<div class="vsbox seqfig">{value_stream(M, f, stages, fm, gaps)}</div>'
        names = {**{st["stage"]: stage_name(st) for st in stages}, "end": title(M, flow_id)}
        measures = measures_table(M, f, stages, fm)
    else:
        drawn = f'<p class="note">{NO_STAGES}</p>'
        names, measures = {}, '<p class="note">No measure on record</p>'
    return ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY. Builder: one_canvas.py -->\n<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(f.get("name", flow_id))} · {E(system)}</title><style>{cv.CSS}{sfv.MEASURE_CSS}{CSS}</style></head><body><main class="flowpage frame">'
            + ps.frame_head(trail, title(M, flow_id))
            + ps.frame_sections("flow", drawn, card(M, f), measures, sfv.key_html()) + '</main>'
            f"{sfv.names_json(names)}{sfv.TABLE_JS}</body></html>\n")
