"""How a case moves: through one stage, and through a flow end to end. Drawn from the register.

    python -I stage_flow_views.py REGISTER OUT.html [STAGE_OR_FLOW_ID ...]

`block(M, stage_id, docs)` is a stage's panel content and `flow_block(M, flow_id, docs)` a flow's, for a page that
has already numbered its steps. Read from the register only:
- lifecycle.csv: each move's from and to state, its path (main or not) and whether it can be undone;
- steps.csv: the moves each process step makes (its `source`), so a stage's moves are its own steps' moves;
- stages.csv and flows.csv: entry, promise, case, start, end, who expects it, what it delivers;
- case-attributes.csv: what is at stake for a case; measures.csv: the measures proposed for alerting.
A stage is drawn as a state machine: the states a case can be in while in the stage, the numbered steps that act on
it there, a loop for each move that leaves the case where it was, and the moves that take it out, solid for an expected
outcome and dashed for an other outcome, each saying where it leads: the stage it enters, or that it ends the flow. A
flow is drawn as its stages left to right in order, each with its promise, joined by the moves the register records
between them, so a move past a stage is an arc of its own. No owner or responder is drawn.
Standard library only.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import capability_views as cv  # noqa: E402
import flow_outputs as fo  # noqa: E402
import step_sequence as ss  # noqa: E402

GAP = ss.GAP
W = 760


# ---------------------------------------------------------------- reading the register

def moves(M):
    return {m.get("move_id"): m for m in ss.lifecycle(M)}


def steps_of(M, stage_id):
    st = M["stage"].get(stage_id)
    return [x["step"] for x in st["_steps"]] if st else []


def stage_moves(M, stage_id):
    """[(step, move)] for every move the stage's own steps cite, in reading order."""
    return [(sid, m) for sid in steps_of(M, stage_id) for m in ss.moves_of(M, sid)]


def inside_states(M, stage_id):
    """The states a case can be in while in the stage: where its own moves start, in order of first use."""
    return list(dict.fromkeys(fo.state(m.get("from_state")) for _, m in stage_moves(M, stage_id)
                              if fo.state(m.get("from_state")) != "(none)"))


def owner_step(M):
    """{move: step} for every move a drawn step cites."""
    return {m.get("move_id"): sid for sid in M["step"] for m in ss.moves_of(M, sid)}


def flow_stages(M, flow_id):
    f = next((f for f in M["flows"] if f["flow_id"] == flow_id), None)
    return f["_stages"] if f else []


def stage_of_state(M, flow_id):
    """{state: stage} for each state a stage's moves start from."""
    out = {}
    for st in flow_stages(M, flow_id):
        for s in inside_states(M, st["stage"]):
            out.setdefault(s, st)
    return out


def is_final(M, s):
    """A state no move starts from: a case there has nothing left to happen to it."""
    return s != "(none)" and all(fo.state(m.get("from_state")) != s for m in moves(M).values())


def entering(M, stage_id):
    """[(move, step or None)] for moves into the stage's states from outside them, including the starting event."""
    inside = set(inside_states(M, stage_id))
    own = owner_step(M)
    flow = M["stage"][stage_id].get("flow", "")
    return [(m, own.get(m.get("move_id"))) for m in moves(M).values()
            if m.get("flow", flow) in (flow, "") and fo.state(m.get("to_state")) in inside
            and fo.state(m.get("from_state")) not in inside]


def exits(M, stage_id):
    """[(step, move)] for the stage's moves that take a case out of its states."""
    inside = set(inside_states(M, stage_id))
    return [(sid, m) for sid, m in stage_moves(M, stage_id)
            if not fo.side_move(m) and fo.state(m.get("to_state")) not in inside]


def leads_to(M, stage_id, m):
    """Where a way out of the stage takes the case, from the move's to-state alone: ("stage", the stage whose moves
    start from that state), ("end", None) when nothing more happens to a case there, or (None, None) when the register
    places the state in no stage."""
    t = fo.state(m.get("to_state"))
    nxt = stage_of_state(M, M["stage"][stage_id].get("flow", "")).get(t)
    if nxt and nxt["stage"] != stage_id:
        return "stage", nxt
    if is_final(M, t):
        return "end", None
    return None, None


def leads_said(M, stage_id, m, full=False):
    """"→ Stage 3" (with the stage's name, in full), "ends the flow", or "" where the register says nothing."""
    kind, nxt = leads_to(M, stage_id, m)
    if kind == "stage":
        return f'→ Stage {nxt.get("order", "")}' + (f': {nxt.get("name", "")}' if full else "")
    return "ends the flow" if kind == "end" else ""


def step_leads(M, stage_id, sid):
    """Where one step's ways out of the stage lead, in reading order: "→ Stage 4, → Stage 5 or ends the flow"."""
    d = list(dict.fromkeys(x for s, m in exits(M, stage_id) if s == sid for x in [leads_said(M, stage_id, m)] if x))
    return ", ".join(d[:-1]) + " or " + d[-1] if len(d) > 1 else "".join(d)


def alerts(M, stage_id):
    """The measures proposed for alerting that belong to the stage, directly or through one of its steps."""
    return [m for m in M["R"]["measures"]
            if (m.get("alert") or "").strip().lower().startswith("yes")
            and (m.get("stage") or M["step"].get(m.get("step"), {}).get("stage", "")) == stage_id]


# ---------------------------------------------------------------- the words a reader sees

def state_name(s):
    """A state as the register's value, in sentence case: IN_REVIEW reads "In review"."""
    s = (s or "").replace("_", " ").strip()
    return s[:1].upper() + s[1:].lower() if s.isupper() else s


def states_in_prose(M, text):
    """Register prose with each lifecycle state's value read as a state name."""
    known = sorted({fo.state(m.get(k)) for m in moves(M).values() for k in ("from_state", "to_state")} - {"(none)"},
                   key=len, reverse=True)
    for s in known:
        text = re.sub(rf"\b{re.escape(s)}\b", state_name(s).lower(), text)
    return text


def tidy(text):
    """Text with a citation taken out: no doubled spaces, no space left before a comma, no trailing comma."""
    return re.sub(r"\s+([,;.])", r"\1", re.sub(r"\s+", " ", text or "")).strip(" ,;.")


def headline(M, text):
    """A register value's lead clause, as the runbook writer reads one: citations out, the part before the first
    colon, steps by their labels, states by their names."""
    t = tidy(fo.strip_parens(text or "").split(":")[0])
    t = fo.relabel_prose(M["_step_label"], M["R"]["steps"], t)
    return states_in_prose(M, t)


def promise(M, text):
    """(the promise's lead, whether it is proposed). "proposed: 2 minutes ..." reads as proposed."""
    v = fo.strip_parens(text or "").strip()
    none_said = re.match(r"\s*none stated\s*;\s*", v, re.I)
    if none_said:
        v = v[none_said.end():]
    body, prop = ss.unproposed(v)
    body = re.split(r"(?<=\w)\.\s+(?=[A-Z])|;\s", tidy(body))[0]
    body = states_in_prose(M, fo.relabel_prose(M["_step_label"], M["R"]["steps"], body))
    return tidy(body), prop


def promise_text(M, text):
    body, prop = promise(M, text)
    if not body or body.lower().startswith("none stated"):
        return "none stated"
    return body + (" (proposed)" if prop else "")


def duration(M, text):
    """The promise's length alone ("5 days"), for a box with no room for the rest."""
    body, prop = promise(M, text)
    m = re.search(r"\d+(?:\s*[-–]\s*\d+)?\s+(?:business\s+)?(?:minutes?|hours?|days?|weeks?|months?)", body)
    if not m:
        return "none stated"
    return m.group(0) + (" (proposed)" if prop else "")


def move_said(M, sid, m):
    """A move as the reader sees it: by the step that makes it, and where it takes the case when that step makes more
    than one move."""
    many = len({fo.state(x.get("to_state")) for x in ss.moves_of(M, sid)}) > 1
    return cv.step_title(M, sid) + (f", to {state_name(fo.state(m.get('to_state'))).lower()}" if many else "")


# ---------------------------------------------------------------- a stage, as a state machine

def _arrow_defs(mid):
    return (f'<defs><marker id="{mid}" viewBox="0 0 8 8" refX="7.5" refY="4" markerWidth="7" markerHeight="7" '
            'orient="auto"><path d="M0,0 L8,4 L0,8 z" style="fill:var(--g600)"/></marker></defs>')


def stage_drawing(M, stage_id):
    """Three bands: where a case comes in, the states it can be in while in the stage (each listing the numbered steps
    that act on the case there), and the states its ways out lead to."""
    E = cv.esc
    st = M["stage"][stage_id]
    mid = "sfv" + re.sub(r"[^A-Za-z0-9]", "_", stage_id)
    inside = inside_states(M, stage_id)
    by_state = {s: [] for s in inside}
    within, loops = [], {}
    for sid, m in stage_moves(M, stage_id):
        a, b = fo.state(m.get("from_state")), fo.state(m.get("to_state"))
        if a == "(none)":
            continue
        if fo.side_move(m):
            if sid not in by_state[a]:
                by_state[a].append(sid)
            loops.setdefault((a, sid), m)
        elif b in by_state:
            within.append((sid, m))
    moved = {sid for sid, _ in stage_moves(M, stage_id)}
    loose = [sid for sid in steps_of(M, stage_id) if sid not in moved]
    if inside and loose:
        by_state[inside[0]] += loose
    out_edges = exits(M, stage_id)
    targets = list(dict.fromkeys(fo.state(m.get("to_state")) for _, m in out_edges))

    IX, IW, LX, TX = 150, 230, 430, 600
    TW = W - TX - 22
    top, parts = 44, []
    name = f'Stage {st.get("order", "")}: {st.get("name", "")}'
    if not inside:
        return no_moves_drawing(M, stage_id, name)
    y, box = top, {}
    for s in inside:
        acts = [cv.wrap(cv.step_title(M, sid), IW - 20, 11.5, 5) for sid in by_state[s]]
        h = 30 + sum(14 * len(a) + 4 for a in acts) + (8 if acts else 0)
        box[s] = (y, h)
        g = [f'<g class="state" data-state="{E(s)}"><rect x="{IX}" y="{y}" width="{IW}" height="{h}" rx="12" class="bx"/>'
             f'<text x="{IX + IW / 2}" y="{y + 19}" class="nm">{E(state_name(s))}</text>']
        if acts:
            g.append(f'<line x1="{IX}" y1="{y + 27}" x2="{IX + IW}" y2="{y + 27}" class="ll"/>')
        yy = y + 42
        for sid, a in zip(by_state[s], acts):
            g += [f'<text x="{IX + 10}" y="{yy + 14 * j}" class="act" data-act="{E(sid)}">{E(ln)}</text>'
                  for j, ln in enumerate(a)]
            lm = loops.get((s, sid))
            if lm:  # the step's move leaves the case where it was: a self-transition, beside the step it is labelled by
                dash = "" if lm.get("path") == "main" else " alt"
                g.append(f'<g class="self{dash}" data-act="{E(sid)}" data-state="{E(s)}"><title>{E(cv.step_title(M, sid))}'
                         f'</title><path d="M{IX},{yy - 10} C{IX - 22},{yy - 16} {IX - 22},{yy + 8} {IX - 1},{yy + 2}" '
                         f'class="ar{dash}" marker-end="url(#{mid})"/></g>')
            yy += 14 * len(a) + 4
        parts.append("".join(g) + "</g>")
        y += h + 40
    inside_bottom = y - 40
    for k, (sid, m) in enumerate(within):
        a, b = fo.state(m.get("from_state")), fo.state(m.get("to_state"))
        down = box[b][0] > box[a][0]
        ya = box[a][0] + (box[a][1] if down else 0)
        yb = box[b][0] + (0 if down else box[b][1])
        x = IX + 30 + 16 * k
        dash = "" if m.get("path") == "main" else " alt"
        lab = cv.wrap(cv.step_title(M, sid), IW - 50, 10.5, 4)
        parts.append(f'<g class="move{dash}" data-act="{E(sid)}"><line x1="{x}" y1="{ya:g}" x2="{x}" y2="{yb:g}" '
                     f'class="ar{dash}" marker-end="url(#{mid})"/>'
                     + "".join(f'<text x="{x + 8}" y="{(ya + yb) / 2 - 6 * (len(lab) - 1) + 12 * j + 4:g}" class="lbl">'
                               f'{E(ln)}</text>' for j, ln in enumerate(lab)) + "</g>")
    for k, (m, sid) in enumerate(entering(M, stage_id)):
        b = fo.state(m.get("to_state"))
        yb = box[b][0] + 14 + 10 * k
        if sid and M["step"].get(sid, {}).get("stage") == stage_id:
            said = cv.step_title(M, sid)
        elif sid:
            other = M["stage"].get(M["step"][sid].get("stage"), {})
            said = f'from Stage {other.get("order", "")}: {M["step"][sid].get("name", "")}'
        else:
            continue
        lab = cv.wrap(said, IX - 34, 10.5, 6)
        parts.append(f'<g class="enter" data-act="{E(sid)}"><circle cx="16" cy="{yb:g}" r="6" class="dot"/>'
                     f'<line x1="22" y1="{yb:g}" x2="{IX - 1}" y2="{yb:g}" class="ar" marker-end="url(#{mid})"/>'
                     + "".join(f'<text x="10" y="{yb + 20 + 12 * j:g}" class="lbl">{E(ln)}</text>'
                               for j, ln in enumerate(lab)) + "</g>")
    ordered = [(sid, m) for t in targets for sid, m in out_edges if fo.state(m.get("to_state")) == t]
    leaving = {}
    for sid, m in ordered:
        leaving.setdefault(fo.state(m.get("from_state")), []).append(m.get("move_id"))

    def start_y(m):  # the ways out of one state leave its right edge spread top to bottom, in drawing order
        a = fo.state(m.get("from_state"))
        if a not in box:
            return top + 14
        y0, h = box[a]
        ids = leaving[a]
        return y0 + 14 + (h - 28) * ids.index(m.get("move_id")) / max(1, len(ids) - 1) if len(ids) > 1 else y0 + 14
    ty, rows = top, []
    for t in targets:
        mine = [(sid, m) for sid, m in out_edges if fo.state(m.get("to_state")) == t]
        labs = [cv.wrap(move_said(M, sid, m), TX - LX - 14, 10.5, 4) for sid, m in mine]
        hs = [max(28, 12 * len(lab) + 14) for lab in labs]
        sub = leads_said(M, stage_id, mine[0][1], full=True)
        sub_l = cv.wrap(sub, TW - 16, 10.5, 5) if sub else []
        h = max(sum(hs), 30 + 12 * len(sub_l))
        g = [f'<g class="target" data-state="{E(t)}"><rect x="{TX}" y="{ty}" width="{TW}" height="{h}" rx="12" class="bx"/>'
             f'<text x="{TX + TW / 2}" y="{ty + 19}" class="nm">{E(state_name(t))}</text>']
        g += [f'<text x="{TX + TW / 2}" y="{ty + 33 + 12 * j}" class="kd">{E(ln)}</text>' for j, ln in enumerate(sub_l)]
        if is_final(M, t):
            cy = ty + h / 2
            g.append(f'<line x1="{TX + TW}" y1="{cy:g}" x2="{TX + TW + 8}" y2="{cy:g}" class="ar"/>'
                     f'<circle cx="{TX + TW + 14}" cy="{cy:g}" r="6" class="end"/>'
                     f'<circle cx="{TX + TW + 14}" cy="{cy:g}" r="3" class="dot"/>')
        parts.append("".join(g) + "</g>")
        yy = ty
        for (sid, m), lab, hh in zip(mine, labs, hs):
            ys = start_y(m)
            ye = yy + hh - 6
            dash = "" if m.get("path") == "main" else " alt"
            rows.append(f'<g class="move{dash}" data-act="{E(sid)}" data-to="{E(t)}" data-path="{E(m.get("path", ""))}">'
                        f'<path d="M{IX + IW},{ys:g} H{IX + IW + 12} L{LX},{ye:g} H{TX - 1}" class="ar{dash}" '
                        f'marker-end="url(#{mid})"/>'
                        + "".join(f'<text x="{LX + 4}" y="{ye - 4 - 12 * (len(lab) - 1 - j):g}" class="lbl">{E(ln)}</text>'
                                  for j, ln in enumerate(lab)) + "</g>")
            yy += hh
        ty += h + 12
    H = max(inside_bottom + 70, ty - 12 + 20)
    return (f'<svg class="seq casemoves" viewBox="0 0 {W} {H:g}" role="img" '
            f'aria-label="{E(name + ": the states a case can be in, the steps that act on it, and the ways out")}">'
            f'{_arrow_defs(mid)}<rect x="2" y="4" width="{W - 4}" height="{H - 8:g}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">{E(name)}: how a case moves through it</text>'
            f'{"".join(parts + rows)}</svg>')


def no_moves_drawing(M, stage_id, name):
    """A stage whose register records no moves: its numbered steps in order, and no states or ways out."""
    E = cv.esc
    y, rows = 52, []
    for sid in steps_of(M, stage_id):
        lines = cv.wrap(cv.step_title(M, sid), W - 60, 11.5, 3)
        rows += [f'<text x="24" y="{y + 14 * j}" class="act" data-act="{E(sid)}">{E(ln)}</text>'
                 for j, ln in enumerate(lines)]
        y += 14 * len(lines) + 6
    rows.append(f'<text x="24" y="{y + 10}" class="tv dim">The register records no moves for this stage, so the '
                'states a case can be in and its ways out are not drawn.</text>')
    H = y + 30
    return (f'<svg class="seq casemoves" viewBox="0 0 {W} {H}" role="img" aria-label="{E(name + ": its steps")}">'
            f'<rect x="2" y="4" width="{W - 4}" height="{H - 8}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">{E(name)}: how a case moves through it</text>{"".join(rows)}</svg>')


STAGE_KEY = ('<details class="seqkey" open><summary>Key to the drawing</summary><ul>'
             "<li>Rounded box: a state a case can be in. Inside it, the numbered process steps that act on the case "
             "while it is there.</li>"
             "<li>Loop on a box's left edge: the step beside it acts on the case and leaves it in that state.</li>"
             "<li>Filled dot: where a case comes into the stage. Ringed dot: nothing more happens to a case in that "
             "state.</li>"
             "<li>Solid arrow: an expected outcome. Dashed arrow: an other outcome.</li>"
             "<li>Under a state a case leaves to: where it goes next, the stage it enters (→ Stage N) or that it ends "
             "the flow.</li>"
             "</ul></details>")


def stage_card(M, stage_id, docs=None):
    E = cv.esc
    st = M["stage"][stage_id]
    ins = []
    for m, sid in entering(M, stage_id):
        if sid and M["step"].get(sid, {}).get("stage") != stage_id:
            other = M["stage"].get(M["step"][sid].get("stage"), {})
            ins.append(f'from Stage {other.get("order", "")}: {cv.step_title(M, sid)}')
        elif sid:
            ins.append(cv.step_title(M, sid))
    out_edges = exits(M, stage_id)
    main_ = list(dict.fromkeys(sid for sid, m in out_edges if M["_step_label"].get(sid) == "Expected outcome"))
    other = list(dict.fromkeys(sid for sid, m in out_edges if M["_step_label"].get(sid) == "Other outcome"))
    undo = [move_said(M, sid, m) for sid, m in stage_moves(M, stage_id)
            if (m.get("irreversible") or "").strip().lower().startswith("yes")]
    flow = st.get("flow", "")
    stake = [a.get("what_is_at_stake", "") for a in M["R"].get("case-attributes", [])
             if a.get("flow") in (flow, "") and a.get("what_is_at_stake")]
    page_ = (docs or {}).get(stage_id, {}).get("Runbook")
    al = [(f'<a href="{E(page_)}#alert-{E(m.get("handle", ""))}">{E(m.get("measure", ""))}</a>' if page_
           else E(m.get("measure", ""))) for m in alerts(M, stage_id)]

    def ul(xs, raw=False):
        return "<ul>" + "".join(f"<li>{x if raw else E(x)}</li>" for x in xs) + "</ul>" if xs else ""

    def ending(sid):  # an outcome by its step's name, and where it leads
        to = step_leads(M, stage_id, sid)
        return M["step"][sid].get("name", "") + (f" ({to})" if to else "")
    rows = [("Promise", E(promise_text(M, st.get("promise", "")))),
            ("A case enters", ul(ins) or GAP),
            ("Expected outcomes", ul([ending(x) for x in main_]) or GAP),
            ("Other outcomes", ul([ending(x) for x in other]) or "none on record"),
            ("Cannot be undone", ul(undo) or "nothing on record"),
            ("At stake", ul(stake) or GAP),
            ("Its alerts", ul(al, raw=True) or "none proposed")]
    return '<div class="card"><dl>' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl></div>"


def stage_sources(M, stage_id):
    E = cv.esc
    st = M["stage"][stage_id]
    lis = [f'<li>{E(k)}: {E(st.get(k, ""))}</li>' for k in ("entry", "exit", "promise", "source") if st.get(k)]
    lis += [f'<li>{E(m.get("move_id"))}: {E(m.get("from_state"))} to {E(m.get("to_state"))}, {E(m.get("path"))}'
            + (", irreversible" if (m.get("irreversible") or "").lower().startswith("yes") else "")
            + f'; step {E(sid)}; {E(m.get("source", ""))}</li>' for sid, m in stage_moves(M, stage_id)]
    return f'<details class="cites"><summary>Where this comes from</summary><ul>{"".join(lis)}</ul></details>'


def block(M, stage_id, docs=None):
    """One stage's panel content: its state machine and key, its card, and where it comes from."""
    key = STAGE_KEY if inside_states(M, stage_id) else ""
    return (f'<div class="seqfig">{stage_drawing(M, stage_id)}</div>{key}'
            f'{stage_card(M, stage_id, docs)}{stage_sources(M, stage_id)}')


# ---------------------------------------------------------------- a flow, its stages in order

def flow_moves(M, flow_id):
    """{(i, j): [(step, move)]} for the moves that take a case out of the flow's i-th stage and into its j-th, counted
    in the flow's order. The stage entered is the one whose moves start from the move's to-state."""
    stages = flow_stages(M, flow_id)
    at = {st["stage"]: k for k, st in enumerate(stages)}
    out = {}
    for i, st in enumerate(stages):
        for sid, m in exits(M, st["stage"]):
            kind, nxt = leads_to(M, st["stage"], m)
            if kind == "stage" and nxt["stage"] in at:
                out.setdefault((i, at[nxt["stage"]]), []).append((sid, m))
    return out


def flow_drawing(M, flow_id):
    """The stages left to right in their order, each with its promise, joined by the moves the register records between
    them: an arrow to the next stage, an arc over the stages a case can go straight past, an arc under for a move back.
    The expected path ends in a state of its own; under each stage, the states its other outcomes end a case in."""
    E = cv.esc
    f = next(x for x in M["flows"] if x["flow_id"] == flow_id)
    stages = flow_stages(M, flow_id)
    if not stages:
        return ""
    mid = "sfvf" + re.sub(r"[^A-Za-z0-9]", "_", flow_id)
    n = len(stages)
    SX, GAPX, EW = 40, 20, 104
    ends = [fo.state(m.get("to_state")) for _, m in exits(M, stages[-1]["stage"]) if m.get("path") == "main"]
    end_state = next((s for s in ends if is_final(M, s)), ends[0] if ends else "")
    BW = (W - SX - 14 - GAPX * n - (EW if end_state else 0)) / n
    BH = 96
    arcs = flow_moves(M, flow_id)

    def bx(i):
        return SX + i * (BW + GAPX)

    def path_of(ms):
        return "main" if any(m.get("path") == "main" for _, m in ms) else "alternative"

    def arc_said(i, j, ms):
        if j > i:
            o = [s.get("order", "") for s in stages[i + 1:j]]
            said = f"skips Stage {o[0]}" if len(o) == 1 else f"skips Stages {o[0]} to {o[-1]}"
        else:
            said = f'back to Stage {stages[j].get("order", "")}'
        names = dict.fromkeys(M["step"].get(sid, {}).get("name", "")
                              for sid, m in sorted(ms, key=lambda x: x[1].get("path") != "main"))
        return said + ": " + "; ".join(x for x in names if x)

    def arc_g(i, j, ms, d, lines, lx, ly):
        p = path_of(ms)
        dash = "" if p == "main" else " alt"
        return (f'<g class="arc{dash}" data-from="{E(stages[i]["stage"])}" data-to="{E(stages[j]["stage"])}" '
                f'data-path="{p}"><path d="{d}" class="ar{dash}" marker-end="url(#{mid})"/>'
                + "".join(f'<text x="{lx:g}" y="{ly + 12 * k:g}" class="lbl">{E(ln)}</text>' for k, ln in enumerate(lines))
                + "</g>")

    over = sorted(((i, j) for i, j in arcs if j > i + 1), key=lambda ij: (ij[1] - ij[0], ij[0]))
    bands, room = [], 0
    for k, (i, j) in enumerate(over):  # the shortest arc nearest the boxes; each its own band
        x1, x2 = bx(i) + BW * 0.7 - 10 * k, bx(j) + BW * 0.3 + 10 * k
        lines = cv.wrap(arc_said(i, j, arcs[(i, j)]), x2 - x1 - 8, 10.5, 5)
        bands.append((i, j, x1, x2, lines, room))
        room += 12 * len(lines) + 22
    top = 46 + room
    mid_y = top + BH / 2
    parts = [f'<circle cx="18" cy="{mid_y:g}" r="6" class="dot"/>'
             f'<line x1="24" y1="{mid_y:g}" x2="{SX - 1}" y2="{mid_y:g}" class="ar" marker-end="url(#{mid})"/>']
    leave_y = top + BH + 28
    lowest = leave_y
    for i, st in enumerate(stages):
        x = bx(i)
        nm = cv.wrap(f'Stage {st.get("order", "")}: {st.get("name", "")}', BW - 12, 11.5, 4)
        pr = cv.wrap(duration(M, st.get("promise", "")), BW - 12, 10.5, 2)
        g = [f'<g class="stage" data-stage="{E(st["stage"])}"><rect x="{x:g}" y="{top}" width="{BW:g}" height="{BH}" '
             'rx="3" class="bx"/>']
        g += [f'<text x="{x + 6:g}" y="{top + 16 + 13 * j}" class="sn">{E(ln)}</text>' for j, ln in enumerate(nm)]
        g += [f'<text x="{x + 6:g}" y="{top + BH - 10 - 12 * (len(pr) - 1 - j)}" class="lbl">{E(ln)}</text>'
              for j, ln in enumerate(pr)]
        leaves = list(dict.fromkeys(fo.state(m.get("to_state")) for _, m in exits(M, st["stage"])
                                    if m.get("path") != "main" and is_final(M, fo.state(m.get("to_state")))))
        if leaves:
            lab = cv.wrap(", ".join(state_name(s) for s in leaves), BW - 4, 10.5, 3)
            g.append(f'<line x1="{x + BW / 2:g}" y1="{top + BH}" x2="{x + BW / 2:g}" y2="{leave_y - 2}" class="ar alt" '
                     f'marker-end="url(#{mid})"/>')
            g += [f'<text x="{x + BW / 2:g}" y="{leave_y + 12 + 12 * j}" class="kd">{E(ln)}</text>'
                  for j, ln in enumerate(lab)]
            lowest = max(lowest, leave_y + 12 * len(lab) + 6)
        parts.append("".join(g) + "</g>")
        if (i, i + 1) in arcs:
            d = f"M{x + BW:g},{mid_y:g} H{x + BW + GAPX - 1:g}"
            parts.append(arc_g(i, i + 1, arcs[(i, i + 1)], d, [], 0, 0))
    for i, j, x1, x2, lines, below in bands:  # read after the stages they pass over
        ya = top - 16 - below
        d = (f"M{x1:g},{top} V{ya + 6:g} Q{x1:g},{ya:g} {x1 + 6:g},{ya:g} H{x2 - 6:g} Q{x2:g},{ya:g} {x2:g},{ya + 6:g} "
             f"V{top - 1}")
        parts.append(arc_g(i, j, arcs[(i, j)], d, lines, x1 + 4, ya - 4 - 12 * (len(lines) - 1)))
    back = sorted(((i, j) for i, j in arcs if j < i), key=lambda ij: (ij[0] - ij[1], ij[1]))
    for k, (i, j) in enumerate(back):  # a move back to an earlier stage runs under the boxes and what leaves them
        x1, x2 = bx(i) + BW * 0.3 - 10 * k, bx(j) + BW * 0.7 + 10 * k
        lines = cv.wrap(arc_said(i, j, arcs[(i, j)]), x1 - x2 - 8, 10.5, 5)
        yb = lowest + 14
        d = (f"M{x1:g},{top + BH} V{yb - 6:g} Q{x1:g},{yb:g} {x1 - 6:g},{yb:g} H{x2 + 6:g} Q{x2:g},{yb:g} {x2:g},{yb - 6:g} "
             f"V{top + BH + 1}")
        parts.append(arc_g(i, j, arcs[(i, j)], d, lines, x2 + 4, yb + 14))
        lowest = yb + 12 * len(lines) + 8
    if end_state:
        x = bx(n)
        lab = cv.wrap(state_name(end_state), EW - 8, 11.5, 2)
        parts.append(f'<line x1="{x - GAPX:g}" y1="{mid_y:g}" x2="{x - 1:g}" y2="{mid_y:g}" class="ar" '
                     f'marker-end="url(#{mid})"/>'
                     f'<g class="flowend" data-state="{E(end_state)}"><rect x="{x:g}" y="{mid_y - 22:g}" width="{EW}" '
                     f'height="44" rx="12" class="bx"/>'
                     + "".join(f'<text x="{x + EW / 2:g}" y="{mid_y + 4 - 7 * (len(lab) - 1) + 13 * j:g}" class="nm">'
                               f'{E(ln)}</text>' for j, ln in enumerate(lab))
                     + f'<line x1="{x + EW / 2:g}" y1="{mid_y + 22:g}" x2="{x + EW / 2:g}" y2="{mid_y + 30:g}" class="ar"/>'
                     f'<circle cx="{x + EW / 2:g}" cy="{mid_y + 36:g}" r="6" class="end"/>'
                     f'<circle cx="{x + EW / 2:g}" cy="{mid_y + 36:g}" r="3" class="dot"/></g>')
    H = lowest + 16
    return (f'<svg class="seq casemoves" viewBox="0 0 {W} {H:g}" role="img" '
            f'aria-label="{E(f.get("name", "") + ": its stages in order, each with its promise, and the moves between them")}">'
            f'{_arrow_defs(mid)}<rect x="2" y="4" width="{W - 4}" height="{H - 8:g}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">{E(f.get("name", ""))}: how a case moves end to end</text>'
            f'{"".join(parts)}</svg>')


FLOW_KEY = ('<details class="seqkey" open><summary>Key to the drawing</summary><ul>'
            "<li>Box: a stage, in order, with its promise. Filled dot: where a case starts.</li>"
            "<li>Arrow between stages: a case moves from one to the other. Solid: an expected outcome makes the move. "
            "Dashed: only an other outcome does.</li>"
            "<li>Arc over a stage: a case can go straight past it, to the stage the arc ends at.</li>"
            "<li>Dashed arrow down: an other outcome that ends the case in that stage.</li>"
            "<li>Rounded box with a ringed dot: where the expected path ends.</li>"
            "</ul></details>")


def flow_card(M, flow_id, docs=None):
    E = cv.esc
    f = next(x for x in M["flows"] if x["flow_id"] == flow_id)
    caps = {c.get("capability_id"): c.get("name", "") for c in M["R"].get("capabilities", [])}
    dl = [caps.get(c.strip(), "") for c in (f.get("delivers") or "").split(";") if c.strip()]
    books = []
    for st in flow_stages(M, flow_id):
        said = E(f'Stage {st.get("order", "")}: {st.get("name", "")}')
        page_ = (docs or {}).get(st["stage"], {}).get("Runbook")
        books.append(f'<a href="{E(page_)}">{said}</a>' if page_ else f"{said}: no runbook yet")
    rows = [("One case", E(headline(M, f.get("case", ""))) or GAP),
            ("Starts", E(headline(M, f.get("starts_at", ""))) or GAP),
            ("Ends", E(headline(M, f.get("ends_at", ""))) or GAP),
            ("Expected by", E(headline(M, f.get("expectation_of", ""))) or GAP),
            ("Promise", E(promise_text(M, f.get("promise", "")))),
            ("Delivers", "<ul>" + "".join(f"<li>{E(x)}</li>" for x in dl if x) + "</ul>" if any(dl) else GAP)]
    if books:
        rows.append(("Stage runbooks", "<ul>" + "".join(f"<li>{b}</li>" for b in books) + "</ul>"))
    return '<div class="card"><dl>' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl></div>"


def flow_sources(M, flow_id):
    E = cv.esc
    f = next(x for x in M["flows"] if x["flow_id"] == flow_id)
    lis = [f'<li>{E(k)}: {E(f.get(k, ""))}</li>'
           for k in ("case", "starts_at", "ends_at", "expectation_of", "promise", "delivers", "source") if f.get(k)]
    lis += [f'<li>{E(st["stage"])} promise: {E(st.get("promise", ""))}</li>' for st in flow_stages(M, flow_id)]
    return f'<details class="cites"><summary>Where this comes from</summary><ul>{"".join(lis)}</ul></details>'


def flow_block(M, flow_id, docs=None):
    """One flow's panel content: its stages in order and key, its card, and where it comes from."""
    d = flow_drawing(M, flow_id)
    fig = (f'<div class="seqfig">{d}</div>{FLOW_KEY}' if d else
           '<p class="note">The register orders no stages for this flow.</p>')
    return fig + flow_card(M, flow_id, docs) + flow_sources(M, flow_id)


CSS = """
.casemoves .seqfig{background:var(--paper);border:1px solid var(--g200);border-radius:4px;margin:0 0 6px;overflow-x:auto}
.casemoves svg.seq{display:block;width:100%;height:auto}
.casemoves .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 10px;margin:6px 0;font-size:12.5px}
.casemoves .card dt{color:var(--g500);font-weight:600}.casemoves .card dd{margin:0;overflow-wrap:anywhere}
.casemoves .card ul{margin:0;padding-left:18px}.casemoves .card li{margin:0 0 3px}
.casemoves details{font-size:12px;color:var(--g600)}.casemoves details ul{padding-left:18px;margin:4px 0}
svg.seq.casemoves .bx{fill:var(--paper);stroke:var(--g600);stroke-width:1.2}
svg.seq.casemoves .ar.alt{stroke-dasharray:6 4}
svg.seq.casemoves .act{font-family:var(--sans);font-size:11.5px;fill:var(--slate)}
svg.seq.casemoves .lbl{font-family:var(--sans);font-size:10.5px;fill:var(--g600)}
svg.seq.casemoves .sn{font-family:var(--serif);font-size:11.5px;fill:var(--slate)}
svg.seq.casemoves .end{fill:var(--paper);stroke:var(--slate);stroke-width:1.4}
"""


def main(argv=None):
    import one_canvas as oc  # the page imports this module; importing it back only here avoids a cycle
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    reg, out = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    R = cv.load(reg)
    err, _ = cv.check(R)
    if err:
        for x in err:
            print("error:", x)
        return 1
    M = oc.number_steps(oc.prune(cv.model(R)))
    docs = oc.stage_docs(reg)
    flows = [f["flow_id"] for f in M["flows"]]
    want = argv[2:] or [x for f in M["flows"] if f["_stages"] for x in [f["flow_id"]] + [s["stage"] for s in f["_stages"]]]
    missing = [x for x in want if x not in M["stage"] and x not in flows]
    if missing:
        print("not a stage or flow:", ", ".join(missing))
        return 1
    E = cv.esc
    secs = []
    for x in want:
        if x in M["stage"]:
            st = M["stage"][x]
            secs.append(f'<section class="casemoves"><h2>Stage {E(st.get("order", ""))}: {E(st.get("name", ""))}: '
                        f'how a case moves through this stage</h2>{block(M, x, docs)}</section>')
        else:
            f = next(f for f in M["flows"] if f["flow_id"] == x)
            secs.append(f'<section class="casemoves"><h2>{E(f.get("name", ""))}: how a case moves end to end</h2>'
                        f'{flow_block(M, x, docs)}</section>')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY. Builder: stage_flow_views.py -->\n<!doctype html>\n"
                   '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                   f'<title>{E(M["system"])}: how a case moves</title><style>{cv.CSS}{oc.CSS}{CSS}'
                   "main{max-width:68rem}</style></head><body><main>"
                   f'<h1>{E(M["system"])}: how a case moves</h1>{"".join(secs)}</main></body></html>\n', encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
