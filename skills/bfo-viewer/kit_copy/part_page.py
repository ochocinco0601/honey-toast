"""A part's own page (a component, a store, a broker or an AI agent), written by one_canvas.py beside the map as
part-<part>/PART.html, for every part a process step relies on.

In the frame of the flow, stage and process step pages (page_style.frame_head, frame_sections): a trail back to the
map, the flow's page, the stage's page and the process step it was opened from (a link from a process step's page
names that step in its fragment, #s:<step>; opened from the map, the first process step it serves), the title naming
the kind ("Part: ..." or "Agent: ..."), then:
- the process steps and outcomes that rely on it, each once, by stage (and by flow where it serves several), the one
  it was opened from in bold; then the drawing in the part form (part_inside): one row per operation, the process steps
  it serves, the calls in those steps and its measures, a square per measure under its layer's word; a process step it
  takes part in with no operation named is a dashed row; a part with no operation (a store, a broker) has its process
  steps as its rows; the whole part's measures at the drawing's top right;
- for an AI agent, one run of the agent (part_inside.run_drawing);
- the card (part_inside.card, without the operations the drawing shows);
- the measures, in the shared table (stage_flow_views.measures_table), in the part's own layers only: application and
  technology, and agentic for an agent; the business layers are counted on cases, on the other pages.
Every measure on the drawing is one row of the table. Every word is 13 px or larger; nothing tells the reader what
to do."""
import json
import re

import capability_views as cv
import flow_page as fp
import page_style as ps
import part_inside as pi
import stage_flow_views as sfv
import step_page as stp

FILE = "PART.html"
RUN_HEAD = "One run of the agent"
WHOLE = "The whole part"
E = cv.esc
W = 1160  # the drawing's width
OPX, OPW, SVX, SVW, CLX, CLW, MKX, MKW = 14, 270, 304, 480, 800, 150, 966, 180
LH, FS = 18, 13
MONO = 14.6  # the size cv.wrap measures a 13 px code face at: its characters are wider


def steps_served(M, pid):
    """The process steps and outcomes the part takes part in, from its participation rows with or without an
    operation, each once: by flow, stage, then process steps before outcomes."""
    got = dict.fromkeys(p["step"] for p in M["R"]["participation"] if p.get("subject_id") == pid
                        and p.get("step") in M["step"] and M["step"][p["step"]].get("stage") in M["stage"])
    return sorted(got, key=lambda x: order(M, x))


def has_page(M, pid):
    """Whether the build writes a page for this part: a part or dependency some process step relies on."""
    return pid in pi.parts(M) and bool(steps_served(M, pid))


def href(M, pid):
    """Where a part's page sits, relative to the map page."""
    return f"part-{pid}/{FILE}"


def title(M, pid):
    """The page's title, "Part: ..." or "Agent: ...", which the side panel's link to it also reads."""
    s = M["subj"][pid]
    return f'{"Agent" if M["family"](s) == "agent" else "Part"}: {s.get("name", pid)}'


def stage_of(M, sid):
    return M["stage"][M["step"][sid]["stage"]]


def order(M, sid):
    st = stage_of(M, sid)
    flows = [f["flow_id"] for f in M["flows"]]
    fi = flows.index(st.get("flow")) if st.get("flow") in flows else len(flows)
    o = str(st.get("order", ""))
    return (fi, int(o) if o.isdigit() else 99, cv.is_outcome(M, sid), M.get("_step_label", {}).get(sid, ""), sid)


def opening(M, pid):
    """The process step the page opens at: the first process step it serves, else its first outcome."""
    xs = steps_served(M, pid)
    return next((x for x in xs if not cv.is_outcome(M, x)), xs[0])


def bare_steps(M, pid):
    """The process steps and outcomes it takes part in with no operation named."""
    with_op = {x for _, st in pi.operations(M, pid) for x in st}
    return [x for x in steps_served(M, pid) if x not in with_op]


def by_stage(M, pid):
    """[((flow, stage), [steps])], in order, process steps before outcomes within each."""
    out = {}
    for x in steps_served(M, pid):
        st = M["step"][x]["stage"]
        out.setdefault((M["stage"][st].get("flow"), st), []).append(x)
    return list(out.items())


def part_layers(M, agent):
    """The part's own layers, in the method's order: what it does and what it runs on, and an agent's judgement."""
    return [L["layer"] for L in M["R"]["method"]["layers"]
            if L["layer"] in ("application", "technology") or (agent and L["layer"] == "agentic")]


def flows_of(M, pid):
    return list(dict.fromkeys(stage_of(M, x).get("flow") for x in steps_served(M, pid)))


def step_link(M, sid):
    """A process step's page, or for an outcome its stage's page with the outcome picked, from the part's folder."""
    return f"../{stp.href(M, sid)}" if stp.has_page(M, sid) else f'../stage-{M["step"][sid]["stage"]}/STAGE.html#s:{sid}'


def trail(M, sid, map_name):
    st = stage_of(M, sid)
    f = next((x for x in M["flows"] if x["flow_id"] == st.get("flow")), {})
    return [(ps.MAP, f"../{map_name}"), (fp.title(M, st.get("flow", "")), f'../{fp.href(st.get("flow", ""))}'),
            (fp.stage_name(st), f'../stage-{M["step"][sid]["stage"]}/STAGE.html'),
            (cv.step_title(M, sid), step_link(M, sid))]


def crumbs(M, sid, map_name, pid):
    """The trail when the page is opened from process step `sid`, ending at the part itself."""
    return re.search(r'<p class="trail">(.*?)</p>', ps.frame_head(trail(M, sid, map_name), title(M, pid)), re.S).group(1)


def measures(M, pid, agent):
    """The part's measures, each with its layer as the method names it and its place: an operation's row, or the
    whole part."""
    import one_canvas as oc  # it imports this module; importing it back only here avoids a cycle
    R = M["R"]
    names = [op for op, _ in pi.operations(M, pid)]
    out = []
    for m in oc.relied_measures(M, pid):
        m = dict(m, layer=cv.layer_of(R, m.get("layer")) or m.get("_layer", ""))
        hit = next((op for op in names if op in oc.ops(m.get("operation"))), None)
        m["_at"] = f"op:{names.index(hit)}" if hit else "part"
        out.append(m)
    return out


def calls_in(M, pid, op, steps):
    """The parts it calls in these process steps: those the register ties to the operation, then those it records the
    part calling in one of these steps."""
    named = [c for c, how in pi.calls(M, pid, op, steps) if how == "call"] if op else []
    hinted = [r["to_id"] for r in pi.interactions(M, pid) if set(cv.ids(r.get("step_hint"))) & set(steps)]
    return list(dict.fromkeys(named + hinted))


def short_name(M, x):
    """A called part by its name, without the register's parenthesis on what it runs on (the card keeps that)."""
    return re.sub(r"\s*\(.*\)\s*$", "", M["subj"][x].get("name", x))


def wrap(text, px):
    return cv.wrap(text, px, FS, 10 ** 6)


def drawing(M, pid, here, ms, layers):
    """The part form: a row per operation (or, for a part with none, per process step), with its process steps, the
    calls in them and its measures; the whole part's measures at the top right. (svg, {place: name})."""
    name = M["subj"][pid].get("name", pid)
    ops = pi.operations(M, pid)
    names = [op for op, _ in ops]
    key = lambda x: order(M, x)  # noqa: E731
    flows = flows_of(M, pid)
    if ops:
        rows = [(op, sorted(st, key=key)) for op, st in ops]
        if bare_steps(M, pid):
            rows.append((None, bare_steps(M, pid)))
    else:
        rows = [(None, [x]) for x in steps_served(M, pid)]
    rows.sort(key=lambda r: min([key(x) for x in r[1]] or [(99,)]))
    svx, svw = (SVX, SVW) if ops else (OPX, SVW + SVX - OPX)
    anycall = any(calls_in(M, pid, op, st) for op, st in rows)
    if not anycall:
        svw = CLX + CLW - svx
    outs = any(cv.is_outcome(M, x) for x in steps_served(M, pid))
    place = {"part": WHOLE}
    out = [f'<text x="{OPX}" y="26" class="pn">{E(name)}</text>']
    head = [m for m in ms if m["_at"] == "part"]
    ph, pw, draw = sfv.mark_pill(head, "part", wmax=MKW + 40, layers=layers)
    out.append(f'<text x="{W - 26 - pw:g}" y="26" class="colh" text-anchor="end">Measures of the whole part</text>')
    out.append(draw(W - 14 - pw, 8))
    y = max(58, 8 + ph + 22)
    cols = ([(OPX, "Operation")] if ops else []) + [
        (svx, "Process steps and outcomes that rely on it" if outs else "Process steps that rely on it")]
    cols += ([(CLX, "Calls in these steps")] if anycall else []) + ([(MKX, "Its measures")] if ops else [])
    out += [f'<text x="{x}" y="{y}" class="colh">{E(t)}</text>' for x, t in cols]
    y += 12
    for op, steps in rows:
        at = f"op:{names.index(op)}" if op else "noop"
        place[at] = op or "No operation on record"
        opl = cv.wrap(op, OPW - 20, MONO, 10 ** 6) if op else ["No operation on record"]  # breaks at its humps and seams
        svl, fl = [], None
        for x in steps:  # where the part serves several flows, each flow's name heads its steps: stage numbers restart
            if len(flows) > 1 and stage_of(M, x).get("flow") != fl:
                fl = stage_of(M, x).get("flow")
                fname = next((f.get("name", fl) for f in M["flows"] if f["flow_id"] == fl), fl)
                svl += [(None, ln) for ln in wrap(fname, svw - 10)]
            words = f'Stage {stage_of(M, x).get("order", "")} · {cv.step_title(M, x)}'
            svl += [(x, ln) for ln in wrap(words, svw - 10 - (12 if len(flows) > 1 else 0))]
        if not steps:
            svl = [("", "no process step on record")]
        called = calls_in(M, pid, op, steps)
        cll = [ln for c in called for ln in wrap(short_name(M, c), CLW - 10)] or (["none on record"] if anycall else [])
        mine = [m for m in ms if m["_at"] == at]
        mh, mw, mdraw = sfv.mark_pill(mine, at, wmax=MKW, layers=layers) if ops and op else (0, 0, None)
        h = max(LH * max(len(opl) if ops else 0, len(svl), len(cll), 1) + 16, mh + 10, 34)
        if not ops:  # a store's or a broker's rows are its process steps, one under another
            h = LH * max(len(svl), len(cll), 1) - 4
        g = []
        if ops:
            g.append(f'<rect x="{OPX}" y="{y}" width="{OPW}" height="{h}" rx="9" class="{"opbox" if op else "opbox none"}"/>')
            g += [f'<text x="{OPX + 10}" y="{y + 21 + LH * j}" class="{"op" if op else "opnone"}">{E(ln)}</text>'
                  for j, ln in enumerate(opl)]
            g.append(f'<line x1="{OPX + OPW}" y1="{y + 16}" x2="{svx - 8}" y2="{y + 16}" class="ar"/>')
        for j, (x, ln) in enumerate(svl):
            ty = y + 21 + LH * j
            if x is None:
                g.append(f'<text x="{svx}" y="{ty}" class="fl">{E(ln)}</text>')
            elif not x:
                g.append(f'<text x="{svx}" y="{ty}" class="bp-gp">{E(ln)}</text>')
            else:
                cls = "sv here" if x == here else "sv"
                g.append(f'<a href="{E(step_link(M, x))}"><text x="{svx + (12 if len(flows) > 1 else 0)}" y="{ty}" '
                         f'class="{cls}" data-s="{E(x)}">{E(ln)}</text></a>')
        g += [f'<text x="{CLX}" y="{y + 21 + LH * j}" class="{"cl" if called else "bp-gp"}">{E(ln)}</text>'
              for j, ln in enumerate(cll)]
        if mdraw:
            g.append(mdraw(MKX, y + 2))
        out.append(f'<g class="oprow">{"".join(g)}</g>')
        y += h + 10
    H = y + 6
    return (f'<svg class="partdraw" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="{E(name)}: its operations, the process steps each serves, the parts each calls, and where each '
            f'is measured">' + "".join(out) + "</svg>"), place


def relied(M, pid, here):
    """What relies on it, once each, by stage: above the drawing, which repeats a process step under each operation."""
    flows = flows_of(M, pid)
    lines, last = [], None
    for (fl, sid), xs in by_stage(M, pid):
        st = M["stage"][sid]
        if len(flows) > 1 and fl != last:
            lines.append(f'<li class="flowh">{E(next((f.get("name", fl) for f in M["flows"] if f["flow_id"] == fl), fl))}</li>')
            last = fl
        items = ", ".join(f'<a href="{E(step_link(M, x))}" class="{"sv here" if x == here else "sv"}" data-s="{E(x)}">'
                          f'{E(cv.step_title(M, x))}</a>' for x in xs)
        lines.append(f'<li{" class=sub" if len(flows) > 1 else ""}><b>Stage {E(str(st.get("order", "")))}: '
                     f'{E(st.get("name", ""))}</b>: {items}</li>')
    return f'<ul class="relied">{"".join(lines)}</ul>'


def run(M, pid):
    """One run of the agent: the kit's activity diagram where the register records the run's order, else its name with
    the order not on record and its operations."""
    return f'<h2 class="sec">{E(RUN_HEAD)}</h2><div class="insideout runbox">{pi.run_drawing(M, pid)}</div>'


OPEN_JS = """<script>
(function () {  // opened from a process step's page (#s:<step>): the trail ends at that step, and it is the one in bold
  var T = JSON.parse(document.getElementById('part-trails').textContent);
  function go() {
    var m = /^#s:(.+)$/.exec(decodeURIComponent(location.hash)); if (!m || !T[m[1]]) return;
    document.querySelector('main.partpage > .trail').innerHTML = T[m[1]];
    document.querySelectorAll('.partpage [data-s]').forEach(function (el) { el.classList.toggle('here', el.dataset.s === m[1]); });
  }
  window.addEventListener('hashchange', go);
  go();
})();
</script>"""

CSS = """
main.partpage{background:var(--m-page);min-height:100vh}
html:has(main.partpage),html:has(main.partpage) body{background:var(--m-page)}
.partpage .drawbox{background:var(--m-col);border:1px solid var(--m-line);border-radius:6px;overflow-x:auto;max-width:100%;width:max-content;box-sizing:border-box}
.partpage svg.partdraw{display:block;max-width:none}
.partpage svg.partdraw text{font:13px var(--m-sans);fill:var(--m-ink)}
.partpage svg.partdraw .pn{font-weight:700;font-size:15px}
.partpage svg.partdraw .colh{font-weight:700;fill:var(--m-ink2)}
.partpage svg.partdraw .opbox{fill:var(--m-app);stroke:var(--m-app-s);stroke-width:1.2}
.partpage svg.partdraw .opbox.none{fill:none;stroke:var(--m-ink3);stroke-dasharray:4 4}
.partpage svg.partdraw .op{font-family:var(--m-mono)}.partpage svg.partdraw .opnone{fill:var(--m-ink2);font-style:italic}
.partpage svg.partdraw a text.sv{fill:var(--m-acc);text-decoration:underline}.partpage svg.partdraw a text.sv.here{font-weight:700}
.partpage svg.partdraw .fl{font-weight:600;fill:var(--m-ink2)}
.partpage svg.partdraw .ar{stroke:var(--m-ink3);stroke-width:1.2}
.partpage svg .bp-ml{font:700 13px var(--m-sans);fill:var(--m-ink2)}.partpage svg .bp-gp{font:italic 13px var(--m-sans);fill:var(--m-bus-s)}
.partpage ul.relied{list-style:none;margin:4px 0 12px;padding:0;font-size:15px;line-height:1.6}
.partpage ul.relied a.here{font-weight:700}.partpage ul.relied li.flowh{font-weight:700;color:var(--m-ink2);margin-top:4px}
.partpage ul.relied li.sub{padding-left:16px}
.partpage .runbox{background:var(--m-col);border:1px solid var(--m-line);border-radius:6px;padding:12px 14px;font-size:15px}
.partpage .runbox .runname{margin:0 0 6px}.partpage .runbox .nr{color:var(--m-ink2);font-weight:400}
.partpage .runbox ul{margin:0;padding-left:20px}.partpage .runbox li{margin:3px 0}.partpage .runbox .ref{color:var(--m-ink2)}
.partpage .runbox svg.seq{display:block;width:100%;max-width:1160px;height:auto}
.partpage .card{background:var(--m-col);border:1px solid var(--m-line);border-radius:10px;padding:16px 18px}
.partpage .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:10px 16px;margin:0}
.partpage .card dt{font-weight:700;color:var(--m-ink2)}.partpage .card dd{margin:0}
.partpage .card ul{margin:0;padding-left:20px}.partpage .card li{margin:0 0 3px}.partpage .card p{margin:4px 0 0}
.partpage .card .ref{color:var(--m-ink2)}
"""


def page(M, pid, map_name):
    """A part's own page. `map_name` is the map page's file name, one folder up."""
    import one_canvas as oc  # it imports this module; importing it back only here avoids a cycle
    s = M["subj"][pid]
    agent = M["family"](s) == "agent"
    kind = "Agent" if agent else "Part"
    name = s.get("name", pid)
    system = M["system"].split(" (")[0]
    here = opening(M, pid)
    layers = part_layers(M, agent)
    ms = measures(M, pid, agent)
    svg, place = drawing(M, pid, here, ms, layers)
    rank = {"part": -1, **{f"op:{i}": i for i in range(len(place))}}
    table = sfv.measures_table(M, ms, lambda m: (m["_at"], place[m["_at"]], place[m["_at"]]),
                               lambda m: rank.get(m["_at"], 99), layers=layers, stay=True, on_max=300, on_break=True)
    drawn = relied(M, pid, here) + f'<div class="drawbox">{svg}</div>' + (run(M, pid) if agent else "")
    card = oc.kind_said(M, pid, pi.card(M, pid, ops_row=False))
    body = ps.frame_head(trail(M, here, map_name), title(M, pid)) + ps.frame_sections("part", drawn, card, table, sfv.key_html())
    trails = {x: crumbs(M, x, map_name, pid) for x in steps_served(M, pid)}
    return ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY. Builder: one_canvas.py -->\n<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(kind)}: {E(name)} · {E(system)}</title><style>{cv.CSS}{oc.CSS}{pi.CSS}{sfv.MEASURE_CSS}{CSS}</style>'
            f'</head><body><main class="partpage frame">{body}</main>{sfv.names_json(place)}'
            f'<script type="application/json" id="part-trails">{json.dumps(trails).replace("</", "<" + chr(92) + "/")}</script>'
            f"{sfv.TABLE_JS}{OPEN_JS}</body></html>\n")
