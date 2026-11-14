"""Inside one part: its operations drawing, its blackbox card and, for an AI agent, its run. Drawn from the register.

    python -I part_inside.py REGISTER OUT.html [PART_ID ...]

`block(M, pid)` is the panel's content for one part, for a page that has already numbered its steps. Read from the
register only:
- participation.csv: the operations the part performs each process step with (`operation`, `;` separated);
- subjects.csv: the part's name, kind and the interactions it makes (`from_id`, `to_id`, `step_hint`, and the
  optional `operation`: which of its operations makes the call);
- agent-system.csv: for an AI agent, its run, the run's actions, its agent parts and its dependencies, and the
  run's control flow in `next`;
- method/agent-questions.csv: the questions asked of an agent.
A link from an operation to a part it calls is drawn as a call only where the interaction's `operation` names it.
Otherwise it is derived from a shared process step and drawn "via the step": the part made the call during a step
the operation serves, not necessarily by that operation. No code structure is drawn, and no owner or responder.
Standard library only.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import capability_views as cv  # noqa: E402
import step_sequence as ss  # noqa: E402
import view_questions as vq  # noqa: E402

GAP = ss.GAP
W, ROWH, OPX = 760, 30, 14


def split(v):
    return [o.strip() for o in (v or "").split(";") if o.strip()]


def drawn_steps(M):
    return [x["step"] for f in M["flows"] for st in f["_stages"] for x in st["_steps"]]


def interactions(M, pid):
    """The interactions the part makes, in register order."""
    return [r for r in M["R"]["subjects"] if r.get("kind") == "relationship" and r.get("from_id") == pid
            and r.get("to_id") in M["subj"]]


def operations(M, pid):
    """[(operation, [steps it serves, in drawn order])]: the part's operations from participation, in the order of the
    first step each serves; then any operation an interaction names that serves no drawn step."""
    order = drawn_steps(M)
    pos = {s: i for i, s in enumerate(order)}
    serves = {}
    for p in M["R"]["participation"]:
        if p.get("subject_id") != pid:
            continue
        for op in split(p.get("operation")):
            serves.setdefault(op, [])
            if p.get("step") in pos and p["step"] not in serves[op]:
                serves[op].append(p["step"])
    for r in interactions(M, pid):
        for op in split(r.get("operation")):
            serves.setdefault(op, [])
    out = [(op, sorted(st, key=pos.get)) for op, st in serves.items()]
    return sorted(out, key=lambda o: pos.get(o[1][0], len(pos)) if o[1] else len(pos) + 1)


def calls(M, pid, op, steps):
    """[(called part, "call" or "via the step")] for one operation: a call where the interaction names the operation;
    via the step where it does not, and the interaction is made on a step the operation serves."""
    out = {}
    for r in interactions(M, pid):
        if op in split(r.get("operation")):
            out[r["to_id"]] = "call"
        elif set(steps) & set(cv.ids(r.get("step_hint"))):
            out.setdefault(r["to_id"], "via the step")
    return list(out.items())


def called(M, pid):
    """Every part the part calls, components before external dependencies, in register order."""
    seen = list(dict.fromkeys(r["to_id"] for r in interactions(M, pid)))
    return sorted(seen, key=lambda x: M["subj"][x].get("level") == "external dependency")


def serves_text(M, steps):
    """The stages whose steps the operation serves, by name: "Stage 2: " and the stage's name; more than two stages read
    "Stages 1 to 4", with "every stage of the flow" where that is so. Steps in more than one flow are read flow by flow,
    each under its flow's name, since a stage's number is only its order within its flow. The steps themselves are lit
    on the map."""
    if not steps:
        return "serves no process step on record"
    stages = list(dict.fromkeys(M["step"][s].get("stage") for s in steps))
    flows = list(dict.fromkeys(M["flow_of_stage"].get(k) for k in stages))

    def order(k):
        o = str(M["stage"].get(k, {}).get("order", ""))
        return (0, int(o)) if o.isdigit() else (1, o)

    def of_flow(flow, named):
        mine = sorted((k for k in stages if M["flow_of_stage"].get(k) == flow), key=order)
        st = [M["stage"].get(k, {}) for k in mine]
        if len(st) <= 2 and not named:
            return "; ".join(f'Stage {x.get("order", "")}: {x.get("name", "")}' for x in st)
        if len(st) == 1:
            return f'Stage {st[0].get("order", "")}'
        every = set(mine) >= {k for k, f in M["flow_of_stage"].items() if f == flow and k in M["stage"]}
        if every:
            return "every stage" if named else f'Stages {st[0].get("order", "")} to {st[-1].get("order", "")}, every stage of the flow'
        if len(st) == 2:
            return f'Stages {st[0].get("order", "")} and {st[1].get("order", "")}'
        return f'Stages {st[0].get("order", "")} to {st[-1].get("order", "")}'
    if len(flows) == 1:
        return of_flow(flows[0], False)
    name = {f["flow_id"]: f.get("name", "") for f in M["flows"]}
    return "; ".join(f'{name.get(f, f)}: {of_flow(f, True)}' for f in flows)


def _mid(pid):
    return "pi" + re.sub(r"[^A-Za-z0-9]", "_", pid)


def box_style(M, x):
    s = M["subj"][x]
    if s.get("level") == "external dependency":
        return ' style="stroke-dasharray:8 4"'
    return ""


# ---------------------------------------------------------------- the operations drawing

def mono_lines(text, chars, n=3):
    """A name in a fixed-width face, broken after a slash or an underscore where it is longer than a line."""
    pieces = re.findall(r"[^/_\s]*[/_]|[^/_\s]+\s*|\s+", text or "")
    lines, cur = [], ""
    for pc in pieces:
        if cur and len(cur) + len(pc) > chars:
            lines.append(cur.rstrip())
            cur = ""
        while len(pc) > chars:
            lines.append(pc[:chars])
            pc = pc[chars:]
        cur += pc
    if cur.strip():
        lines.append(cur.rstrip())
    if len(lines) > n:
        lines = lines[:n - 1] + [lines[n - 1][:chars - 1] + "…"]
    return lines or [""]


def drawing(M, pid):
    """One row per operation: the operation, the process steps it serves, then a line across the columns of the parts
    this part calls, with a dot on each column the operation calls: filled for a call the register names, open on a
    dotted line for one made via the step."""
    E = cv.esc
    ops = operations(M, pid)
    targets = called(M, pid)
    name = M["subj"][pid].get("name", "")
    OPW, SVX, SVW, CX = 204, 230, 164, 400
    colw = min(120, (W - CX - 10) / max(1, len(targets)))
    cx = {x: CX + colw * (i + .5) for i, x in enumerate(targets)}
    heads = {x: (cv.wrap(M["subj"][x].get("name", ""), colw - 10, 11.5, 3),
                 cv.wrap(M["subj"][x].get("part_kind", ""), colw - 10, 10, 2)) for x in targets}
    top = 44
    head_h = max([20 + 13 * len(n) + 11 * len(k) for n, k in heads.values()] or [30])
    out = [f'<text x="{OPX}" y="{top + head_h - 6}" class="tagt">OPERATION</text>',
           f'<text x="{SVX}" y="{top + head_h - 6}" class="tagt">SERVES</text>']
    if targets:
        out.append(f'<text x="{CX}" y="{top - 6}" class="tagt">CALLS</text>')
    for x in targets:
        nm, kd = heads[x]
        out.append(f'<g class="head" data-called="{E(x)}"><rect x="{cx[x] - colw / 2 + 3:g}" y="{top}" width="{colw - 6:g}" '
                   f'height="{head_h}" rx="3" class="bx"{box_style(M, x)}/>'
                   + "".join(f'<text x="{cx[x]:g}" y="{top + 16 + 13 * j}" class="nm" style="font-size:11.5px">{E(ln)}</text>'
                             for j, ln in enumerate(nm))
                   + "".join(f'<text x="{cx[x]:g}" y="{top + 18 + 13 * len(nm) + 11 * j}" class="kd" style="font-size:10px">'
                             f'{E(ln)}</text>' for j, ln in enumerate(kd)) + "</g>")
    y = top + head_h + 12
    rows = []
    for op, steps in ops:
        lines = mono_lines(op, int((OPW - 16) / 7.3))
        sv = cv.wrap(serves_text(M, steps), SVW - 8, 11.5, 4)
        h = max(ROWH, 14 * max(len(lines), len(sv)) + 10)
        mid_y = y + h / 2
        g = [f'<g class="oprow" data-op="{E(op)}" data-steps="{E(" ".join(steps))}" tabindex="0" role="button" '
             f'aria-label="{E(op + ": light the process steps it serves on the map")}"><title>{E(op)}</title>'
             f'<rect x="{OPX}" y="{y}" width="{OPW}" height="{h}" rx="9" class="bx"/>']
        g += [f'<text x="{OPX + 8}" y="{y + 15 + 14 * j}" class="op">{E(ln)}</text>' for j, ln in enumerate(lines)]
        g.append(f'<line x1="{OPX + OPW}" y1="{mid_y:g}" x2="{SVX - 4}" y2="{mid_y:g}" class="ar"/>')
        g += [f'<text x="{SVX}" y="{mid_y + 4 - 7 * (len(sv) - 1) + 14 * j:g}" class="tv">{E(ln)}</text>'
              for j, ln in enumerate(sv)]
        mine = dict(calls(M, pid, op, steps))
        if mine:
            last = max(cx[x] for x in mine)
            sure = [cx[x] for x, how in mine.items() if how == "call"]
            start = SVX + SVW
            if sure:
                g.append(f'<line x1="{start}" y1="{mid_y:g}" x2="{max(sure):g}" y2="{mid_y:g}" class="ar"/>')
                start = max(sure)
            if last > start:
                g.append(f'<line x1="{start:g}" y1="{mid_y:g}" x2="{last:g}" y2="{mid_y:g}" class="ar unrec"/>')
            for x, how in mine.items():
                g.append(f'<circle cx="{cx[x]:g}" cy="{mid_y:g}" r="5" class="{"dot" if how == "call" else "qm"}" '
                         f'data-to="{E(x)}" data-how="{E(how)}"/>')
        else:
            g.append(f'<text x="{SVX + SVW}" y="{mid_y + 4:g}" class="tv dim">calls nothing on record</text>')
        rows.append("".join(g) + "</g>")
        y += h + 6
    bottom = y + 6
    guides = [f'<line x1="{cx[x]:g}" y1="{top + head_h:g}" x2="{cx[x]:g}" y2="{bottom - 6:g}" class="ll"/>' for x in targets]
    if not ops:
        rows.append(f'<text x="{OPX}" y="{top + head_h + 24}" class="tv dim">The register names no operation this part '
                    'performs a process step with.</text>')
        bottom = max(bottom, top + head_h + 40)
    H = bottom + 6
    return (f'<svg class="seq inside" viewBox="0 0 {W} {H:g}" role="img" '
            f'aria-label="{E(name + ": its operations, the process steps each serves, the parts each calls")}">'
            f'<rect x="2" y="4" width="{W - 4}" height="{H - 8:g}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">{E(name)}: inside</text>{"".join(out + guides + rows)}</svg>')


# ---------------------------------------------------------------- an AI agent's run

def agent_rows(M, pid):
    return M["agent_rows"].get(pid, [])


def reaches(M, pid, op_row):
    """What one run action reaches through the agent parts that perform it: their dependencies, and any other part
    they are shared with (a tool that runs in another component)."""
    rows = agent_rows(M, pid)
    parts = {r.get("id"): r for r in rows if r.get("element") == "agent part"}
    deps = {r.get("id"): r for r in rows if r.get("element") == "dependency"}
    out = []
    for ap in cv.ids(op_row.get("performed_by")):
        p = parts.get(ap)
        if not p:
            continue
        on = [d for d in cv.ids(p.get("uses")) if d in deps]
        out += [deps[d].get("name", "") for d in on]
        covered = {x for d in on for x in cv.ids(deps[d].get("subject_id"))}
        host = ss.inside(M).get(pid)  # a part shared with the component it runs inside is inside it, not reached
        out += [M["subj"][x].get("name", "") for x in cv.ids(p.get("subject_id"))
                if x not in (pid, host) and x in M["subj"] and x not in covered]
    return list(dict.fromkeys(out))


EDGE = "stroke:var(--m-ink2);stroke-width:1.4;fill:none"


def run_moves(M, pid):
    """The run's control flow as the register records it in `next`: [(from, to, guard)], from "start" (the run row) or an
    action id, to an action id or "end". Only moves between the agent's own actions are kept."""
    rows = agent_rows(M, pid)
    ops = {r.get("id") for r in rows if r.get("element") == "action"}
    out = []
    for r in rows:
        src = "start" if r.get("element") == "run" else r.get("id") if r.get("element") == "action" else None
        for dst, guard in cv.next_moves(r.get("next")) if src else []:
            if dst in ops or (dst == "end" and src != "start"):
                out.append((src, dst, guard))
    return out


def tools_of(M, pid, op_row):
    """The agent's own operations (its participation rows) that the agent parts performing one run action name,
    in their name or what they are: a run's "call a tool" joined to the operations it calls. Derived, never a column."""
    rows = agent_rows(M, pid)
    parts = {r.get("id"): r for r in rows if r.get("element") == "agent part"}
    text = " ".join(f'{parts[a].get("name", "")} {parts[a].get("what_it_is", "")}'
                    for a in cv.ids(op_row.get("performed_by")) if a in parts)
    return [op for op, _ in operations(M, pid) if re.search(r"(?<![\w/])" + re.escape(op) + r"(?![\w/])", text)]


def act_side(M, pid, r, parts):
    """(the action's name, "· not assessed" where its agent part was looked for and not found, and the lines beside
    it: the agent parts that perform it and what those reach)."""
    mine = [parts[a] for a in cv.ids(r.get("performed_by")) if a in parts]
    unfound = bool(mine) and not any(cv.ids(p.get("subject_id")) for p in mine)
    side = [f"by {', '.join(p.get('name', '') for p in mine)}" if mine else NO_PART]
    called = tools_of(M, pid, r)
    if called:
        side.append("calls " + ", ".join(called))
    reach = reaches(M, pid, r)
    if reach:
        side.append("reaches " + ", ".join(reach))
    return r.get("name", "") + (" · not assessed" if unfound else ""), unfound, side


def run_list(M, pid, run, ops, parts):
    """A run whose order the register does not record: its name, with the order said to be not on record, then its
    actions as a plain list, with no start, end or edge, so nothing reads as a sequence."""
    E = cv.esc
    lis = "".join(f'<li><b>{E(name)}</b> <span class="ref">{E("; ".join(side))}</span></li>'
                  for name, _, side in (act_side(M, pid, r, parts) for r in ops))
    return (f'<div class="seq inside run"><p class="runname"><b>One run: {E(run.get("name") or GAP)}</b> '
            f'<span class="nr">· {NO_ORDER_SAID}</span></p><ul>{lis}</ul></div>')


def side_points(cx, top, d, n, side):
    """n points spread down one side of a diamond whose top is at `top` and half-size `d`: its side vertex for one."""
    sign = -1 if side == "L" else 1
    out = []
    for i in range(n):
        dy = 2 * d * (i + 1) / (n + 1)
        out.append((cx + sign * (d - abs(dy - d)), top + dy))
    return out


def run_drawing(M, pid):
    """One run as a UML activity diagram: an initial node, the run's actions in register order, a final
    node, and the control flow the register records in `next`: a decision node where an action has several next moves,
    a merge node where several moves enter one, an edge drawn back up where the run repeats. Each condition sits on its
    own edge where the edge leaves the decision, as UML places a guard. A move that skips ahead runs on the left, a move
    back up on the right, each on its own lane and entering or leaving a node at its own point, the shorter inside, so
    no two moves share a line. No edge is drawn that the register does not record; what it does not record is said
    under the drawing. Beside each action: the agent parts that perform it and what those reach. A run with no
    recorded order is listed, not drawn."""
    E = cv.esc
    rows = agent_rows(M, pid)
    run = next((r for r in rows if r.get("element") == "run"), {})
    ops = [r for r in rows if r.get("element") == "action"]
    parts = {r.get("id"): r for r in rows if r.get("element") == "agent part"}
    if not ops:
        return '<p class="note">The register names no action inside this agent\'s run.</p>'
    moves = run_moves(M, pid)
    if not moves:
        return run_list(M, pid, run, ops, parts)
    seq = ["start"] + [r.get("id") for r in ops] + ["end"]
    pos = {k: i for i, k in enumerate(seq)}
    indeg, outdeg = {}, {}
    for a, b, _ in moves:
        outdeg[a] = outdeg.get(a, 0) + 1
        indeg[b] = indeg.get(b, 0) + 1
    straight = {}  # a move to the very next node goes straight down, one per source
    for a, b, g in moves:
        if pos[b] == pos[a] + 1 and a not in straight:
            straight[a] = (b, g)
    routed = [(a, b, g) for a, b, g in moves if straight.get(a) != (b, g)]
    span = lambda m: (abs(pos[m[1]] - pos[m[0]]), pos[m[0]])
    lanes = {"L": sorted([m for m in routed if pos[m[1]] > pos[m[0]]], key=span),  # skips ahead, the shortest inside
             "R": sorted([m for m in routed if pos[m[1]] <= pos[m[0]]], key=span)}  # back up
    side_of = {m: s for s, ms in lanes.items() for m in ms}
    lane_no = {m: i for ms in lanes.values() for i, m in enumerate(ms)}
    # the moves leaving and entering each node, per side, in the order that keeps one lane off another's line
    exits, entries = {}, {}
    for m in routed:
        exits.setdefault((m[0], side_of[m]), []).append(m)
        entries.setdefault((m[1], side_of[m]), []).append(m)
    for (k, s), ms in exits.items():  # going down on the left, the outer leaves higher; going up on the right, lower
        ms.sort(key=lambda m: -lane_no[m] if s == "L" else lane_no[m])
    for (k, s), ms in entries.items():  # coming down on the left, the outer enters lower; coming up on the right, higher
        ms.sort(key=lambda m: lane_no[m] if s == "L" else -lane_no[m])
    count = lambda table, k: max([len(table.get((k, s), [])) for s in "LR"])
    D, LANE, AW, GAPY, CH = 10, 14, 240, 26, 6.4  # CH: the width of one character of a condition
    guard_w = lambda m: CH * (len(m[2]) + 2) if m[2] else 0
    left = 24 + LANE * len(lanes["L"])
    for m in lanes["L"]:  # a condition leaving on the left reads leftwards from its point, inside the frame
        if m[0] in outdeg and outdeg[m[0]] > 1:
            n = count(exits, m[0])
            left = max(left, guard_w(m) + (D if n < 2 else 8 * (n + 1)) + 12 - AW / 2)
        else:
            left = max(left, guard_w(m) + 20)
    cx = left + AW / 2
    lane_x = {m: (left - LANE * (lane_no[m] + 1) if side_of[m] == "L" else left + AW + LANE * (lane_no[m] + 1))
              for m in routed}
    sx = left + AW + 14 + LANE * len(lanes["R"])
    mk = _mid(pid) + "-ad"
    out = [f'<defs><marker id="{mk}" viewBox="0 0 8 8" refX="7.5" refY="4" markerWidth="7" markerHeight="7" orient="auto">'
           '<path d="M0,0 L8,4 L0,8 z" style="fill:var(--m-ink2)"/></marker></defs>']
    arrow = f' marker-end="url(#{mk})"'

    def diamond(kind, at, y, d):
        out.append(f'<g class="ad-node" data-kind="{kind}" data-at="{E(at)}"><path d="M{cx:g} {y:g} l{d:g} {d:g} '
                   f'l{-d:g} {d:g} l{-d:g} {-d:g} z" class="bx"/></g>')
    start_pt, end_pt = {}, {}  # move -> the point it leaves from / enters at
    port = {}  # node -> (top y, bottom y)
    y = 44
    for k in seq:
        top = y
        merge = k != "start" and indeg.get(k, 0) > 1
        if merge:
            d = D if count(entries, k) < 2 else 6 * (count(entries, k) + 1)
            diamond("merge", k, y, d)
            for s in "LR":
                for m, pt in zip(entries.get((k, s), []), side_points(cx, y, d, len(entries.get((k, s), [])), s)):
                    end_pt[m] = pt
            y += 2 * d + 12
            out.append(f'<line x1="{cx:g}" y1="{y - 12:g}" x2="{cx:g}" y2="{y:g}" class="ar"{arrow}/>')
        if k == "start":
            out.append(f'<g class="ad-node" data-kind="initial" data-at="start"><circle cx="{cx:g}" cy="{y + 8:g}" r="8" '
                       'class="dot"/></g>')
            h, half = 16, 8
        elif k == "end":
            out.append(f'<g class="ad-node" data-kind="final" data-at="end"><circle cx="{cx:g}" cy="{y + 10:g}" r="10" '
                       f'class="bx"/><circle cx="{cx:g}" cy="{y + 10:g}" r="6" class="dot"/></g>')
            h, half = 20, 10
        else:
            r = next(o for o in ops if o.get("id") == k)
            full, unfound, side = act_side(M, pid, r, parts)
            name = cv.wrap(full, AW - 20, 12.5, 3)
            lines = [ln for s in side for ln in cv.wrap(s, W - sx - 14, 11.5, 2)]
            h = max(14 * len(name) + 18, 14 * len(lines) + 4)
            half = AW / 2
            style = ' style="stroke-dasharray:3 2"' if unfound else ""
            out.append(f'<g class="act" data-op="{E(k)}"><rect x="{left:g}" y="{y:g}" width="{AW}" height="{h:g}" rx="12" '
                       f'class="bx"{style}/>' + "".join(f'<text x="{cx:g}" y="{y + 17 + 14 * j:g}" class="nm">{E(ln)}</text>'
                                                        for j, ln in enumerate(name))
                       + "".join(f'<text x="{sx:g}" y="{y + 13 + 14 * j:g}" class="tv dim">{E(ln)}</text>'
                                 for j, ln in enumerate(lines)) + "</g>")
        if not merge:  # a single move in enters the node's side in its upper part
            for s in "LR":
                for m in entries.get((k, s), []):
                    end_pt[m] = (cx - half if s == "L" else cx + half, y + (h / 2 if k in ("start", "end") else h / 3))
        y += h
        if k != "end" and outdeg.get(k, 0) > 1:
            out.append(f'<line x1="{cx:g}" y1="{y:g}" x2="{cx:g}" y2="{y + 18:g}" class="ar"{arrow}/>')
            y += 18  # room for a condition above a line leaving the decision
            d = D if count(exits, k) < 2 else 8 * (count(exits, k) + 1)
            diamond("decision", k, y, d)
            for s in "LR":
                for m, pt in zip(exits.get((k, s), []), side_points(cx, y, d, len(exits.get((k, s), [])), s)):
                    start_pt[m] = pt
            y += 2 * d
        else:  # a single move out leaves the node's side in its lower part
            for s in "LR":
                for m in exits.get((k, s), []):
                    start_pt[m] = (cx - half if s == "L" else cx + half, y - (h / 2 if k in ("start", "end") else h / 3))
        port[k] = (top, y)
        y += GAPY
    labels = []  # drawn over every line, so no line crosses a condition
    for a, (b, g) in straight.items():
        y1, y2 = port[a][1], port[b][0]
        out.append(f'<path class="ad-edge" data-from="{E(a)}" data-to="{E(b)}" data-back="no" d="M{cx:g} {y1:g} V{y2:g}" '
                   f'style="{EDGE}"{arrow}/>')
        if g:
            labels.append(f'<text class="guard h" data-from="{E(a)}" data-to="{E(b)}" x="{cx + 8:g}" y="{y1 + 13:g}">'
                          f'[{E(g)}]</text>')
    for m in routed:
        a, b, g = m
        (x1, y1), (x2, y2), lane = start_pt[m], end_pt[m], lane_x[m]
        back = "yes" if side_of[m] == "R" else "no"
        out.append(f'<path class="ad-edge" data-from="{E(a)}" data-to="{E(b)}" data-back="{back}" '
                   f'd="M{x1:g} {y1:g} H{lane:g} V{y2:g} H{x2:g}" style="{EDGE}"{arrow}/>')
        if g:
            gx, anchor = (x1 - 4, "end") if side_of[m] == "L" else (x1 + 4, "start")
            labels.append(f'<text class="guard h" data-from="{E(a)}" data-to="{E(b)}" x="{gx:g}" y="{y1 - 7:g}" '
                          f'style="text-anchor:{anchor}">[{E(g)}]</text>')
    out += labels
    names = {r.get("id"): r.get("name", "") for r in ops}
    notes = [] if outdeg.get("start") else ["Where a run starts: not on record."]
    notes += [f"After “{names[k]}”: not on record." for k in seq[1:-1] if not outdeg.get(k)]
    again = {}
    for r in ops:
        for d in reaches(M, pid, r):
            again.setdefault(d, []).append(r.get("name", ""))
    notes += [f"{d} is reached by more than one action in a run: {'; '.join(n)}." for d, n in again.items() if len(n) > 1]
    ny = y + 8
    for n in notes:
        for ln in cv.wrap(n, W - 40, 11.5, 3):
            out.append(f'<text x="14" y="{ny:g}" class="tv dim">{E(ln)}</text>')
            ny += 14
        ny += 4
    H = ny + 6
    title = "One run: " + (run.get("name") or GAP)
    return (f'<svg class="seq inside run" viewBox="0 0 {W} {H:g}" role="img" aria-label="{E(title)}, as an activity diagram">'
            f'<rect x="2" y="4" width="{W - 4}" height="{H - 8:g}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">{E(cv.wrap(title, W - 40, 12, 1)[0])}</text>{"".join(out)}</svg>')


NO_MEASURE = "No measure on record"  # the kit's words for a layer with nothing on record
NO_PART = "by no agent part found"  # a run operation whose agent part was looked for and not found
NO_ORDER_SAID = "order not on record"  # a run whose order the register does not record
SAYS_NOTHING = "a component of this system"  # where a part sits when the register places it nowhere more exactly


def question_gaps(M, pid):
    """measure-gaps.csv rows on one agent, or on one of its actions: [(action id or "", question id, row)]."""
    import one_canvas as oc  # the page imports this module; importing it back only here avoids a cycle
    path = pathlib.Path(M["R"].get("_path") or "") / "measure-gaps.csv"
    if not M["R"].get("_path") or not path.exists():
        return []
    out = []
    for g in oc.fo.read_csv(path):
        el = (g.get("element") or "").split(None, 1)
        if el and el[0] == pid and oc.fo.norm(g.get("why")):
            out.append((el[1] if len(el) > 1 else "", oc.fo.norm(g.get("question")), g))
    return out


def measures_cell(M, pid, q, gaps):
    """How many of the agent's measures answer one question, and in what state; or that none is on record; then any gap
    measure-gaps.csv records for it, by its kind and reason."""
    import one_canvas as oc
    ms = [m for m in cv.agent_measures(M, M["subj"][pid]) if m.get("agent_question") == q]
    states = {"exist": 0, "exist but misleading": 0, "proposed": 0}
    for m in ms:
        if not (m.get("exists") or "").strip().lower().startswith("yes"):
            states["proposed"] += 1
        else:
            states["exist but misleading" if (m.get("defect") or "").strip() else "exist"] += 1
    said = [f"{n} {w.replace('exist', 'exists', 1) if n == 1 else w}" for w, n in states.items() if n]
    if len(said) == 1 and len(ms) > 1:
        said = ["all " + said[0].split(" ", 1)[1]]
    out = [cv.esc(f"{len(ms)} measure{'' if len(ms) == 1 else 's'}: {', '.join(said)}.")] if ms else []
    out += [(cv.esc(f"At {op}: ") if op else "") + oc.gap_text(M, g) for op, qq, g in gaps if qq == q]
    return " ".join(out) or cv.esc(NO_MEASURE)


def questions(M, pid):
    """The questions asked of an agent: per question, how many of its measures answer it, or that none is on record, or
    the gap the register records; and how each is settled in the method."""
    gaps = question_gaps(M, pid)
    trs = "".join(f'<tr><th>{cv.esc(q["question"])}</th><td>{measures_cell(M, pid, q["agent_question"], gaps)}</td>'
                  f'<td>{cv.esc(q["status"])}</td></tr>' for q in M["R"]["method"]["agent-questions"])
    return ('<table class="agent"><thead><tr><th>Question</th><th>Its measures</th><th>How settled in the method</th>'
            f'</tr></thead><tbody>{trs}</tbody></table>')


# ---------------------------------------------------------------- the card

def card(M, pid, ops_row=True):
    """The part's card: its kind, purpose, operations (left out with `ops_row` False, for a page that draws them),
    what it depends on, where it sits where that says more than "a component of this system", and for an AI agent the
    agent parts found and the dependencies they reach that the list above does not name."""
    E = cv.esc
    s = M["subj"][pid]
    ins = ss.inside(M)
    ops = operations(M, pid)
    op_li = "".join(f'<li><code>{E(op)}</code>: '
                    + (E(cv.step_title(M, st[0])) if len(st) == 1 else
                       "<ul>" + "".join(f"<li>{E(cv.step_title(M, x))}</li>" for x in st) + "</ul>" if st else
                       "serves no process step on record")
                    + "</li>" for op, st in ops)
    dep = [(r["to_id"], r) for r in interactions(M, pid)]
    dep_li = "".join(f'<li>{E(M["subj"][x].get("name", ""))} <span class="ref">({E(M["subj"][x].get("part_kind", ""))}'
                     + ("" if cv.ids(r.get("step_hint")) else ", at start-up") + ")</span></li>"
                     for x, r in dict((x, r) for x, r in dep).items())
    hosted = [a for a, c in ins.items() if c == pid]
    purpose = vq.purpose(M, pid)
    sits = ss.where_it_sits(M, pid, ins)
    rows = [("Kind", E(s.get("part_kind", "")) or GAP),
            ("Purpose", cv.prose(M, purpose) or GAP)]
    if ops_row:
        rows.append(("Its operations, and the process steps each serves",
                     f"<ul>{op_li}</ul>" if op_li else vq.said(M, "part: operations", pid, GAP)))
    dep_at = len(rows)
    rows.append(("Depends on", f"<ul>{dep_li}</ul>" if dep_li else vq.said(M, "part: depends on", pid, "nothing on record")))
    if sits != SAYS_NOTHING:
        rows.append(("Where it sits", cv.prose(M, sits)))
    if hosted:
        rows.append(("Runs inside it", E(", ".join(M["subj"][a].get("name", "") for a in hosted))))
    if M["family"](s) == "agent":
        ar = agent_rows(M, pid)
        found = [r for r in ar if r.get("element") == "agent part" and cv.ids(r.get("subject_id"))]
        aps = "".join(f'<li>{E(r.get("name", ""))}: {cv.prose(M, ss.plain(r.get("what_it_is", "")))}</li>' for r in found)
        used = {d for r in found for d in cv.ids(r.get("uses"))}
        named = {x for x, _ in dep}
        ads = [r.get("name", "") for r in ar if r.get("element") == "dependency" and r.get("id") in used
               and not set(cv.ids(r.get("subject_id"))) & named]
        rows.insert(dep_at + 1, ("Agent parts", f"<ul>{aps}</ul>" if aps else GAP))
        if ads:
            rows[dep_at] = ("Depends on", (f"<ul>{dep_li}</ul>" if dep_li else "")
                            + f'<p>Through its agent parts: {E(", ".join(dict.fromkeys(ads)))}</p>')
    body = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return f'<div class="card"><dl>{body}</dl></div>'


def sources(M, pid):
    """Where it comes from, with the register's codes and citations, folded away."""
    E = cv.esc
    lis = [f'<li>{E(p.get("step"))}: {E(p.get("involvement", ""))}' + (f', {E(p["operation"])}' if p.get("operation") else "")
           + (f'; {E(p.get("activity"))}' if p.get("activity") else "") + "</li>"
           for p in M["R"]["participation"] if p.get("subject_id") == pid]
    lis += [f'<li>{E(r.get("subject_id"))}: to {E(r.get("to_id"))}, process steps {E(r.get("step_hint") or "none")}'
            + (f', operation {E(r["operation"])}' if r.get("operation") else ", operation not named") + f'; {E(r.get("source"))}</li>'
            for r in interactions(M, pid)]
    lis += [f'<li>{E(r.get("id"))} {E(r.get("element"))}: {E(r.get("what_it_is"))}; {E(r.get("source_ref"))}</li>'
            for r in agent_rows(M, pid)]
    return f'<details class="cites"><summary>Where this comes from</summary><ul>{"".join(lis)}</ul></details>'


def key(M, pid):
    """The drawing's key, with a row only for the marks this part's drawing uses."""
    targets = called(M, pid)
    rows = ["Each row is one operation the part performs (a tool, a route or a handler), the stages whose process steps it "
            "serves, and the parts it calls. An operation picked lights, on the map, the process steps it serves: "
            "what stops if it fails.",
            "Columns: the parts this part calls. Filled dot on a column: the register says this operation makes the call.",
            "Open dot on a dotted line: via the process step. The part makes the call during a process step this operation serves; "
            "the register does not say this operation makes it."]
    if any(M["subj"][x].get("level") == "external dependency" for x in targets):
        rows.append("Long-dashed box: an external dependency, run by someone else.")
    return ('<details class="seqkey"><summary>Key to the drawing</summary><ul>'
            + "".join(f"<li>{cv.esc(r)}</li>" for r in rows) + "</ul></details>")


RUN_KEY = ('<details class="seqkey"><summary>Key to the run</summary><ul>'
           "<li>A UML activity diagram. Filled dot: a run starts. Ringed dot: a run ends.</li>"
           "<li>Rounded box: one action inside a run, in the order the register lists them. Beside it: the agent "
           "parts that perform it, and what those reach.</li>"
           "<li>Diamond under a box: a decision, where a run takes one of several next moves. Diamond over a box: a "
           "merge, where several moves lead into it. A line back up, on the right: the run repeats. A line on the "
           "left: a move that skips ahead. [In brackets], where a move leaves a decision: the condition on that move, "
           "as the register gives it.</li>"
           "<li>Short-dashed box, not assessed: the agent part that would perform it was looked for and not found.</li>"
           "<li>A move is drawn only where the register records it; what it does not record is said under the "
           "drawing.</li>"
           "</ul></details>")


def block(M, pid):
    """One part's panel content: its drawing and key, for an AI agent its run, its card, and where it comes from."""
    s = M["subj"][pid]
    out = [f'<div class="seqfig">{drawing(M, pid)}</div>', key(M, pid)]
    if M["family"](s) == "agent":
        drawn = bool(run_moves(M, pid))
        out += ['<h4>One run</h4>', f'<div class="{"seqfig" if drawn else "runlist"}">{run_drawing(M, pid)}</div>']
        out += [RUN_KEY] if drawn else []
    out.append(card(M, pid))
    if M["family"](s) == "agent":
        out += ["<h4>The agentic layer: the questions asked of it</h4>", questions(M, pid)]
    out.append(sources(M, pid))
    return "".join(out)


def parts(M):
    """The parts that get the panel: every element at a part's or a dependency's level, in register order."""
    return [x["subject_id"] for x in M["R"]["subjects"]
            if x.get("kind") == "element" and x.get("level") in ("component", "external dependency")]


CSS = """
.insideout h4{margin:10px 0 4px;font-size:13px}
.insideout .seqfig{background:var(--m-col);border:1px solid var(--m-page);border-radius:4px;margin:0 0 6px;overflow-x:auto}
.insideout svg.seq{display:block;width:100%;height:auto}
.insideout .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 10px;margin:6px 0;font-size:13px}
.insideout .card dt{color:var(--m-ink3);font-weight:600}.insideout .card dd{margin:0;overflow-wrap:anywhere}
.insideout .card ul{margin:0;padding-left:18px}.insideout .card li{margin:0 0 3px}.insideout .card p{margin:4px 0 0}
.insideout details{font-size:13px;color:var(--m-ink2)}.insideout details ul{padding-left:18px;margin:4px 0}
svg.seq.inside .bx{fill:var(--m-col);stroke:var(--m-ink2);stroke-width:1.2}
.insideout g.oprow{cursor:pointer}.insideout g.oprow:hover>rect.bx,.insideout g.oprow:focus-visible>rect.bx,.insideout g.oprow.on>rect.bx{stroke:var(--m-acc);stroke-width:2}
.insideout g.oprow:focus{outline:none}
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
    want = argv[2:] or parts(M)
    missing = [x for x in want if x not in M["subj"]]
    if missing:
        print("not a part:", ", ".join(missing))
        return 1
    secs = "".join(f'<section class="insideout"><h2>{cv.esc(M["subj"][x].get("name", ""))}: inside this part</h2>'
                   f'{block(M, x)}</section>' for x in want)
    import run_lock  # the register is written by one run at a time
    run_lock.guard(out.parent)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY. Builder: part_inside.py -->\n<!doctype html>\n"
                   '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                   f'<title>{cv.esc(M["system"])}: inside each part</title><style>{cv.CSS}{oc.CSS}{CSS}'
                   "main{max-width:68rem}</style></head><body><main>"
                   f'<h1>{cv.esc(M["system"])}: inside each part</h1>{secs}</main></body></html>\n', encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
