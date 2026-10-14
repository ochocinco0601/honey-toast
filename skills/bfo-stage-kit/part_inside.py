"""Inside one part: its operations drawing, its whitebox card and, for an AI agent, its run. Drawn from the register.

    python -I part_inside.py REGISTER OUT.html [PART_ID ...]

`block(M, pid)` is the panel's content for one part, for a page that has already numbered its steps. Read from the
register only:
- participation.csv: the operations the part performs each process step with (`operation`, `;` separated);
- subjects.csv: the part's name, kind and the interactions it makes (`from_id`, `to_id`, `step_hint`, and the
  optional `operation`: which of its operations makes the call);
- agent-system.csv: for an AI agent, its run, the run's operations, its agent parts and its dependencies;
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
    "Stages 1 to 4", with "every stage of the flow" where that is so. The steps themselves are lit on the map."""
    if not steps:
        return "serves no process step on record"
    stages = list(dict.fromkeys(M["step"][s].get("stage") for s in steps))
    st = [M["stage"].get(k, {}) for k in stages]
    if len(st) <= 2:
        return "; ".join(f'Stage {x.get("order", "")}: {x.get("name", "")}' for x in st)
    flow = M["flow_of_stage"].get(stages[0])
    every = set(stages) >= {k for k, f in M["flow_of_stage"].items() if f == flow and k in M["stage"]}
    return f'Stages {st[0].get("order", "")} to {st[-1].get("order", "")}' + (", every stage of the flow" if every else "")


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
    """What one run operation reaches through the agent parts that perform it: their dependencies, and any other part
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


def run_drawing(M, pid):
    """One run: its operations as the register lists them, each with the agent parts that perform it and what those
    reach. The register holds no order between them, no repeats and no exit, so none is drawn."""
    E = cv.esc
    rows = agent_rows(M, pid)
    run = next((r for r in rows if r.get("element") == "run"), {})
    ops = [r for r in rows if r.get("element") == "operation"]
    parts = {r.get("id"): r for r in rows if r.get("element") == "agent part"}
    if not ops:
        return '<p class="note">The register names no operation inside this agent\'s run.</p>'
    cx, AW = 150, 250
    y = 44
    out = []
    for r in ops:
        mine = [parts[a] for a in cv.ids(r.get("performed_by")) if a in parts]
        unfound = bool(mine) and not any(cv.ids(p.get("subject_id")) for p in mine)
        name = cv.wrap(r.get("name", "") + (" · not assessed" if unfound else ""), AW - 20, 12.5, 3)
        h = 14 * len(name) + 18
        style = ' style="stroke-dasharray:3 2"' if unfound else ""
        out.append(f'<g class="act" data-op="{E(r.get("id"))}"><rect x="{cx - AW / 2:g}" y="{y}" width="{AW}" height="{h}" '
                   f'rx="12" class="bx"{style}/>' + "".join(f'<text x="{cx}" y="{y + 17 + 14 * j}" class="nm">{E(ln)}</text>'
                                                             for j, ln in enumerate(name)))
        side = [f"by {', '.join(p.get('name', '') for p in mine)}" if mine else f"by: {GAP}"]
        reach = reaches(M, pid, r)
        if reach:
            side.append("reaches " + ", ".join(reach))
        lines = [ln for s in side for ln in cv.wrap(s, 300, 11.5, 2)]
        out += [f'<text x="{cx + AW / 2 + 12:g}" y="{y + 13 + 14 * j}" class="tv dim">{E(ln)}</text>' for j, ln in enumerate(lines)]
        out.append("</g>")
        y += max(h, 14 * len(lines) + 4) + 10
    again = {}
    for r in ops:
        for d in reaches(M, pid, r):
            again.setdefault(d, []).append(r.get("name", ""))
    notes = [f"The order a run takes these operations, which it repeats and how many times, and what ends it: {GAP}."]
    notes += [f"{d} is reached by more than one operation in a run: {'; '.join(n)}." for d, n in again.items() if len(n) > 1]
    ny = y + 16
    for n in notes:
        for ln in cv.wrap(n, W - 40, 11.5, 3):
            out.append(f'<text x="14" y="{ny}" class="tv dim">{E(ln)}</text>')
            ny += 14
        ny += 4
    H = ny + 6
    title = "One run: " + (run.get("name") or GAP)
    return (f'<svg class="seq inside run" viewBox="0 0 {W} {H:g}" role="img" aria-label="{E(title)}, its operations">'
            f'<rect x="2" y="4" width="{W - 4}" height="{H - 8:g}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">{E(cv.wrap(title, W - 40, 12, 1)[0])}</text>{"".join(out)}</svg>')


def questions(M, pid):
    agent = M["subj"][pid]
    qms = cv.agent_measures(M, agent)

    def state(m):
        if m.get("exists") != "yes":
            return "proposed"
        d = (m.get("defect") or "").strip()
        return "exists, but misleading: " + ss.plain(d) if d else "emitted by the code"
    def listed(q):  # one measure kept once per decision point it is asked at: named once, with how many
        got = {}
        for m in qms:
            if m.get("agent_question") == q:
                k = f'{m.get("measure")} ({state(m)})'
                got[k] = got.get(k, 0) + 1
        return "; ".join(k if n == 1 else f"{k}, at {n} decision points" for k, n in got.items())
    trs = "".join(
        f'<tr><th>{cv.esc(q["question"])}</th><td>'
        + (cv.esc(listed(q["agent_question"])) or '<span class="ref">none on record</span>')
        + f'</td><td>{cv.esc(q["status"])}</td></tr>' for q in M["R"]["method"]["agent-questions"])
    return ('<table class="agent"><thead><tr><th>Question</th><th>On record in this register</th>'
            f'<th>How settled in the method</th></tr></thead><tbody>{trs}</tbody></table>')


# ---------------------------------------------------------------- the card

def card(M, pid):
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
    rows = [("Kind", E(s.get("part_kind", "")) or GAP),
            ("Purpose", GAP),
            ("Its operations, and the process steps each serves", f"<ul>{op_li}</ul>" if op_li else GAP),
            ("Depends on", f"<ul>{dep_li}</ul>" if dep_li else "nothing on record"),
            ("Where it sits", E(ss.where_it_sits(M, pid, ins)))]
    if hosted:
        rows.append(("Runs inside it", E(", ".join(M["subj"][a].get("name", "") for a in hosted))))
    if M["family"](s) == "agent":
        ar = agent_rows(M, pid)
        aps = "".join(f'<li>{E(r.get("name", ""))}: {E(ss.plain(r.get("what_it_is", "")))}</li>'
                      for r in ar if r.get("element") == "agent part")
        ads = [r.get("name", "") for r in ar if r.get("element") == "dependency"]
        rows.insert(4, ("Agent parts", f"<ul>{aps}</ul>" if aps else GAP))
        if ads:
            rows[3] = ("Depends on", (f"<ul>{dep_li}</ul>" if dep_li else "")
                       + f'<p>Through its agent parts: {E(", ".join(dict.fromkeys(ads)))}</p>')
    body = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return f'<div class="card"><dl>{body}</dl></div>'


def sources(M, pid):
    """Where it comes from, with the register's codes and citations, folded away."""
    E = cv.esc
    lis = [f'<li>{E(p.get("step"))}: {E(p.get("involvement", ""))}' + (f', {E(p["operation"])}' if p.get("operation") else "")
           + (f'; {E(p.get("activity"))}' if p.get("activity") else "") + "</li>"
           for p in M["R"]["participation"] if p.get("subject_id") == pid]
    lis += [f'<li>{E(r.get("subject_id"))}: to {E(r.get("to_id"))}, steps {E(r.get("step_hint") or "none")}'
            + (f', operation {E(r["operation"])}' if r.get("operation") else ", operation not named") + f'; {E(r.get("source"))}</li>'
            for r in interactions(M, pid)]
    lis += [f'<li>{E(r.get("id"))} {E(r.get("element"))}: {E(r.get("what_it_is"))}; {E(r.get("source_ref"))}</li>'
            for r in agent_rows(M, pid)]
    return f'<details class="cites"><summary>Where this comes from</summary><ul>{"".join(lis)}</ul></details>'


def key(M, pid):
    """The drawing's key, with a row only for the marks this part's drawing uses."""
    targets = called(M, pid)
    agent = M["family"](M["subj"][pid]) == "agent"
    rows = ["Each row is one operation the part performs (a tool, a route or a handler), the stages whose steps it "
            "serves, and the parts it calls. Click an operation to light, on the map, the process steps it serves: "
            "what stops if it fails. The card below names them.",
            "Columns: the parts this part calls. Filled dot on a column: the register says this operation makes the call.",
            "Open dot on a dotted line: via the step. The part makes the call during a process step this operation serves; "
            "the register does not say this operation makes it."
            + (" The run below shows which of the agent's own operations reach each part." if agent else "")]
    if any(M["subj"][x].get("level") == "external dependency" for x in targets):
        rows.append("Long-dashed box: an external dependency, run by someone else.")
    return ('<details class="seqkey" open><summary>Key to the drawing</summary><ul>'
            + "".join(f"<li>{cv.esc(r)}</li>" for r in rows) + "</ul></details>")


RUN_KEY = ('<details class="seqkey"><summary>Key to the run</summary><ul>'
           "<li>Rounded box: one operation inside a run, as the register lists them. Beside it: the agent parts that "
           "perform it, and what those reach.</li>"
           "<li>Short-dashed box, not assessed: the agent part that would perform it was looked for and not found.</li>"
           f"<li>No arrows: the order a run takes its operations, which it repeats and what ends it are {GAP}.</li>"
           "</ul></details>")


def block(M, pid):
    """One part's panel content: its drawing and key, for an AI agent its run, its card, and where it comes from."""
    s = M["subj"][pid]
    out = [f'<div class="seqfig">{drawing(M, pid)}</div>', key(M, pid)]
    if M["family"](s) == "agent":
        out += ['<h4>One run</h4>', f'<div class="seqfig">{run_drawing(M, pid)}</div>', RUN_KEY]
    out.append(card(M, pid))
    if M["family"](s) == "agent":
        out += ["<h4>The agentic layer: what it can report</h4>", questions(M, pid)]
    out.append(sources(M, pid))
    return "".join(out)


def parts(M):
    """The parts that get the panel: every element at a part's or a dependency's level, in register order."""
    return [x["subject_id"] for x in M["R"]["subjects"]
            if x.get("kind") == "element" and x.get("level") in ("component", "external dependency")]


CSS = """
.insideout h4{margin:10px 0 4px;font-size:13px}
.insideout .seqfig{background:var(--paper);border:1px solid var(--g200);border-radius:4px;margin:0 0 6px;overflow-x:auto}
.insideout svg.seq{display:block;width:100%;height:auto}
.insideout .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 10px;margin:6px 0;font-size:12.5px}
.insideout .card dt{color:var(--g500);font-weight:600}.insideout .card dd{margin:0;overflow-wrap:anywhere}
.insideout .card ul{margin:0;padding-left:18px}.insideout .card li{margin:0 0 3px}.insideout .card p{margin:4px 0 0}
.insideout details{font-size:12px;color:var(--g600)}.insideout details ul{padding-left:18px;margin:4px 0}
svg.seq.inside .bx{fill:var(--paper);stroke:var(--g600);stroke-width:1.2}
.insideout g.oprow{cursor:pointer}.insideout g.oprow:hover>rect.bx,.insideout g.oprow:focus-visible>rect.bx,.insideout g.oprow.on>rect.bx{stroke:var(--clay);stroke-width:2}
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
