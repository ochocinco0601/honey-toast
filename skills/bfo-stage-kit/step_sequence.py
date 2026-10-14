"""One process step in order: a UML sequence drawing and one scenario card, both drawn from the register.

one_canvas.py puts each step's drawing and card in a panel beside the map, shown when the step is clicked. Read from
the register only:
- lifecycle.csv: the move that carries the step (named in the step's own source), its hops in order (`travels_by`),
  `timing`, `if_not` and `recovery`;
- participation.csv: the parts that take part (the lifelines), the `operation` each performs the step with;
- subjects.csv: each part's name, kind and owner, and the interactions recorded for the step (`step_hint`, `sequence`);
- agent-system.csv: a part of an AI agent shared with one component (the agent runs inside that component), and the
  agent's own operations that call the same dependency (a call made more than once).
Where the register holds no order, no sender or no hand-off, the drawing and the card say so: not in the map yet.
Nothing is drawn that the register does not hold. Standard library only.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import capability_views as cv  # noqa: E402
import flow_outputs as fo  # noqa: E402
import view_questions as vq  # noqa: E402

GAP = "not in the map yet"


# ---------------------------------------------------------------- the register's words, without citations or codes

CODE = re.compile(r"^(?:\s*(?:(?i:see|as|and|or)\s+)?[A-Z]{1,3}\d+(?:\s*[-–]\s*[A-Z]{0,3}\d+)?\s*[,;]?)+\s*$")
PATH = re.compile(r"^[\w.-]+(?:/[\w.-]+)+(?:\.\w{1,5})?$")


def dead(seg):
    """A clause that is only a citation, a source path, a line range or a register code."""
    s = seg.strip()
    return (not s or bool(cv.CITE.search(s)) or bool(re.search(r"\.csv\b", s)) or bool(CODE.match(s))
            or bool(PATH.match(s)) or bool(re.fullmatch(r"[\d\s,–-]+", s)))


def _scan(text):
    """Top-level pieces: ('t', text) outside parentheses, ('p', inner text) for each parenthesised group."""
    out, depth, cur = [], 0, ""
    for ch in text:
        if ch == "(":
            if depth == 0:
                out.append(("t", cur))
                cur = ""
            else:
                cur += ch
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
            if depth == 0:
                out.append(("p", cur))
                cur = ""
            else:
                cur += ch
        else:
            cur += ch
    out.append(("p" if depth else "t", cur))
    return out


def _segments(text):
    """(clause, separator) pairs split at a top-level comma or semicolon followed by a space."""
    out, depth, cur = [], 0, ""
    for i, ch in enumerate(text):
        if ch in "({":
            depth += 1
        elif ch in ")}" and depth:
            depth -= 1
        if depth == 0 and ch in ",;" and (i + 1 == len(text) or text[i + 1] == " "):
            out.append((cur, ch))
            cur = ""
            continue
        cur += ch
    out.append((cur, ""))
    return out


def plain(text):
    """The register's words with every citation and register code taken out: a parenthesised group is cleaned and
    dropped when nothing is left, then each clause that is only a citation or a code is dropped."""
    out = ""
    for kind, v in _scan(text or ""):
        if kind == "t":
            out += v
        else:
            inner = plain(v)
            if inner:
                out += "(" + inner + ")"
            else:
                out = out.rstrip()
    res, sep_before = "", ""
    for seg, sep in _segments(out):
        if dead(seg):
            continue
        res += (sep_before + " " if res else "") + seg.strip()
        sep_before = sep or ","
    res = re.sub(r"(?:\s+(?:as in|by|as|see|in|from|of))?\s+L\d{2,3}\b", "", res)  # a move named in passing
    return re.sub(r"\s{2,}", " ", res).strip(" ,;")


def unproposed(v):
    """(the value without a leading `proposed:`, whether it had one)."""
    m = re.match(r"\s*proposed\s*:\s*", v or "", re.I)
    return ((v or "")[m.end():] if m else (v or "")), bool(m)


def where_it_sits(M, x, ins):
    """Where a lifeline runs, as far as the register places it: inside the part that hosts it, a component of this
    system, a person, or outside the system."""
    s = M["subj"][x]
    if x in ins:
        return "inside " + M["subj"][ins[x]].get("name", "")
    if s.get("level") == "external dependency":
        return "outside this system"
    if M["family"](s) == "person":
        return "a person"
    return "a component of this system"


# ---------------------------------------------------------------- reading the rows of one step

def lifecycle(M):
    if "_lifecycle" not in M:
        p = M["R"].get("_path")
        M["_lifecycle"] = cv.read_csv(pathlib.Path(p) / "lifecycle.csv") if p else []
    return M["_lifecycle"]


def moves_of(M, sid):
    """The moves the step's own source names, in that order."""
    rows = {r.get("move_id"): r for r in lifecycle(M)}
    return [rows[x] for x in dict.fromkeys(re.findall(r"\bL\d+\b", M["step"][sid].get("source", ""))) if x in rows]


def rows_of(M, sid):
    return [p for p in M["R"]["participation"] if p.get("step") == sid and p.get("subject_id") in M["subj"]]


def calls_of(M, sid):
    """The interactions recorded for the step."""
    return [r for r in M["R"]["subjects"] if r.get("kind") == "relationship" and sid in cv.ids(r.get("step_hint"))]


def inside(M):
    """{agent: component} for each AI agent one of whose own parts (agent-system.csv) is shared with exactly one
    component that is not an agent or a person: the agent runs inside that component."""
    out = {}
    for a in M["agents"]:
        hosts = set()
        for r in M["agent_rows"].get(a["subject_id"], []):
            got = cv.ids(r.get("subject_id"))
            if r.get("element") != "agent part" or a["subject_id"] not in got:
                continue
            for x in got:
                s = M["subj"].get(x, {})
                if x != a["subject_id"] and s.get("level") == "component" and M["family"](s) not in ("agent", "person"):
                    hosts.add(x)
        if len(hosts) == 1:
            out[a["subject_id"]] = hosts.pop()
    return out


def repeated(M, agent, sid, to):
    """The agent's own operations serving this step that call `to` through one of its parts: two or more is a call made
    more than once."""
    rows = M["agent_rows"].get(agent, [])
    parts = {r.get("id"): r for r in rows if r.get("element") == "agent part"}
    deps = {r.get("id"): r for r in rows if r.get("element") == "dependency"}
    run = next((r for r in rows if r.get("element") == "run"), {})

    def reaches(pid):
        p = parts.get(pid)
        if not p:
            return False
        return (to != agent and to in cv.ids(p.get("subject_id"))) or any(
            to in cv.ids(deps.get(d, {}).get("subject_id")) for d in cv.ids(p.get("uses")))
    names = [r.get("name", "") for r in rows if r.get("element") == "operation"
             and sid in cv.ids(r.get("serves_business_step") or run.get("serves_business_step"))
             and any(reaches(x) for x in cv.ids(r.get("performed_by")))]
    return names if len(names) > 1 else []


# ---------------------------------------------------------------- naming a part from the register's words

def _bare(name):
    return re.sub(r"\s*\([^()]*\)", "", name or "").strip().lower()


def _paren(name):
    m = re.search(r"\(([^()]*)\)", name or "")
    return m.group(1).strip().lower() if m else ""


def _no_paths(text):
    return re.sub(r"\S*/\S*", " ", text or "")


def resolve(M, pids, phrase):
    """The one part of the step a short phrase names ("UI", "the LLM endpoint", "agent"), or None."""
    p = re.sub(r"^(?:the|a|an|any|its)\s+", "", (phrase or "").strip().lower())
    p = re.sub(r"'s\b.*$", "", p).strip()
    if not p:
        return None

    def word(v):
        return re.search(r"\b" + re.escape(p) + r"\b", v or "") is not None
    tiers = [lambda s: p in (s["name"].lower(), _bare(s["name"]), _paren(s["name"])),
             lambda s: word(s["name"].lower()),
             lambda s: word((s.get("part_kind") or "").lower())]
    for t in tiers:
        hits = [x for x in pids if t(M["subj"][x])]
        if hits:
            return hits[0] if len(hits) == 1 else None
    return None


def mentions(M, pids, text):
    """The parts of the step a clause names, by name, by the name in its brackets or by its last word."""
    t = _no_paths(text).lower()
    out = []
    for x in pids:
        n = M["subj"][x].get("name", "")
        keys = {_bare(n), _paren(n)}
        words = _bare(n).split()
        if words and len(words[-1]) >= 4:
            keys.add(words[-1])
        if any(k and re.search(r"\b" + re.escape(k) + r"\b", t) for k in keys):
            out.append(x)
    return out


def norm_op(s):
    return re.sub(r"<[^<>]*>|\{[^{}]*\}", "{}", s or "")


def ops_in(rows, text):
    """[(operation, its parts)] for each operation of the step the clause names."""
    t = norm_op(text)
    found = {}
    for p in rows:
        for op in [o.strip() for o in (p.get("operation") or "").split(";") if o.strip()]:
            o = norm_op(op)
            hit = (re.search(r"(?<![\w/])" + re.escape(o) + r"(?!\w)", t) if re.fullmatch(r"\w+", o) else o in t)
            if hit:
                found.setdefault(op, [])
                if p["subject_id"] not in found[op]:
                    found[op].append(p["subject_id"])
    return list(found.items())


# ---------------------------------------------------------------- the hops of a move as messages

TO = re.compile(r"^(?P<a>[^,:;]+?)\s+to\s+(?P<b>[^,:;]+?)(?=\s+(?:over|with|by|for|through|via|from)\b|[:,;]|$)")


def hops(move):
    """[(hop number, kind, [alternative clauses], the whole clause)] from `travels_by`."""
    out = []
    for n, h in enumerate(fo.split_top(move.get("travels_by", "")), 1):
        m = re.match(r"\s*([\w-]+(?:\s[\w-]+)?)\s*\((.*)\)\s*$", h, re.S)
        kind, body = (m.group(1).strip().lower(), m.group(2)) if m else (h.strip().lower(), "")
        alts = [a for a in (plain(x) for part in fo.split_top(body, ";") for x in re.split(r",\s+or\s+", part)) if a]
        out.append((n, kind, alts, plain(body)))
    return out


def message(**kw):
    m = dict(kind="msg", frm=None, to=None, label="", op=False, desc="", hop=None, sub=[], loop=[], words="", num="")
    m.update(kw)
    return m


def clause_messages(M, sid, rows, pids, seq):
    """The messages of the step's hops, in order. Ends are named only where the register names them."""
    persons = [x for x in pids if M["family"](M["subj"][x]) == "person"]

    def fam(x):
        return M["family"](M["subj"][x])
    out = []
    for n, kind, text in seq:
        if kind == "person":
            who = mentions(M, persons, text)
            frm = who[0] if len(who) == 1 else (persons[0] if len(persons) == 1 else None)
            out.append(message(kind="person", frm=frm, label=text, hop=n) if frm else
                       message(kind="note", label=text, hop=n))
            continue
        ops = ops_in(rows, text)
        if kind in ("in-process", "timer"):
            if ops:
                op, owners = ops[0]
                agents = [x for x in owners if fam(x) == "agent"]
                hosts = [x for x in owners if x not in agents]
                if agents and hosts:
                    out.append(message(frm=agents[0], to=hosts[0], label=op, op=True, desc=text, hop=n))
                else:
                    out.append(message(kind="self", frm=owners[0], label=op, op=True, desc=text, hop=n))
                continue
            # in-process work runs in a part that performs the step: the one the clause names, else the one the
            # case was last passed to, else the one that made the last call (a store or a dependency only answers)
            doers = [p["subject_id"] for p in rows if p.get("involvement") != "supports"]
            named = [x for x in mentions(M, pids, text) if x in doers]
            prev = next((m for m in reversed(out) if m["kind"] in ("msg", "self", "found")), None)
            last = [x for x in ((prev["to"], prev["frm"]) if prev else ()) if x in doers]
            at = named[0] if len(named) == 1 else (last[0] if last else None)
            out.append(message(kind="self", frm=at, label=text, hop=n) if at else message(kind="note", label=text, hop=n))
            continue
        # a call, a message, an outbox relay or a poll: from a part to a part
        segs = [s.strip() for s, _ in _segments(text) if s.strip()]
        head, rest = (segs[0], segs[1:]) if segs else ("", [])
        m = TO.match(head)
        frm = to = None
        words, label = "", text
        if m and len(m.group("a").split()) <= 4:
            frm, to = resolve(M, pids, m.group("a")), resolve(M, pids, m.group("b"))
            label = ", ".join([head[m.end():].strip(" ,:")] + rest).strip(" ,")
            if not frm:
                words = m.group("a").strip()
        owners = [x for _, xs in ops for x in xs]
        if not to:
            hosts = [x for x in owners if fam(x) != "agent"]
            named = mentions(M, pids, text)
            to = (hosts or owners)[0] if owners else (named[0] if len(named) == 1 else None)
        if ops and to in owners:  # the operation labels the call; the rest of the clause, where it adds words, under it
            op = ops[0][0]
            label, desc, is_op = op, ("" if norm_op(label).strip() == norm_op(op) else label), True
        else:
            desc, is_op = "", False
        if not frm and not words:
            fm = re.search(r"\bfrom\s+((?:any|a|an|the)\s+)?([^,;]+)", _no_paths(text))
            if fm:
                frm = resolve(M, pids, fm.group(2))
                words = "" if frm else (fm.group(1) or "") + fm.group(2).strip()
            elif out and out[-1]["kind"] == "person":
                frm = out[-1]["frm"]
        if not to:
            out.append(message(kind="note", label=text, hop=n))
        elif not frm:
            out.append(message(kind="found", to=to, label=label, op=is_op, desc=desc, hop=n, words=words))
        else:
            out.append(message(frm=frm, to=to, label=label, op=is_op, desc=desc, hop=n))
        last = out[-1]
        if last["kind"] == "msg" and fam(last["frm"]) == "agent":
            last["loop"] = repeated(M, last["frm"], sid, last["to"])
    for i, m in enumerate(out):  # a person's act reaches the part that sends the next call
        if m["kind"] == "person":
            nxt = next((x for x in out[i + 1:] if x["kind"] in ("msg", "found", "self")), None)
            to = nxt.get("frm") if nxt else None
            if to and to != m["frm"]:
                m.update(kind="msg", to=to)
            else:
                m.update(kind="self")
    return out


def place_calls(M, sid, pids, msgs, calls):
    """Take out of `calls` each interaction a message draws. A clause of a message that names another part, with a
    recorded call to it from one of the message's ends, becomes that call, inside the hop, with no place of its own."""
    def take(a, b):
        r = next((r for r in calls if r.get("from_id") == a and r.get("to_id") == b), None)
        if r:
            calls.remove(r)
        return r
    for m in msgs:
        if m["kind"] in ("msg", "unplaced"):
            take(m["frm"], m["to"])
        if m["kind"] not in ("msg", "self", "found"):
            continue
        ends = [x for x in (m["frm"], m["to"]) if x]
        text = m["desc"] or m["label"]
        keep, subs = [], []
        for seg in [s.strip() for s, _ in _segments(text) if s.strip()]:
            hit = None
            for x in mentions(M, pids, seg):
                for e in ([] if x in ends else ends):
                    if take(e, x):
                        hit = message(kind="unplaced", frm=e, to=x, label=seg)
                        break
                if hit:
                    break
            if hit:
                subs.append(hit)
            else:
                keep.append(seg)
        if subs:
            m["sub"] = subs
            m["desc" if m["desc"] else "label"] = ", ".join(keep)


def hand_offs(M, sid, msgs, calls):
    """Between two messages, where the next sender is not the part the case was last passed to: the hand-off, as a
    recorded call when there is one, else a gap."""
    out, prev = [], None
    for m in msgs:
        if prev and m["frm"] and m["kind"] in ("msg", "self"):
            last_to = prev["to"] or prev["frm"]
            if last_to and m["frm"] not in (last_to, prev["frm"]) and M["family"](M["subj"][m["frm"]]) != "person":
                r = next((r for r in calls if r.get("from_id") == last_to and r.get("to_id") == m["frm"]), None)
                out.append(message(kind="unplaced" if r else "gap", frm=last_to, to=m["frm"]))
        out.append(m)
        if m["kind"] in ("msg", "self", "found"):
            prev = m
    return out


def call_label(M, sid, r):
    """A recorded call is labelled with what its receiver does in the step, in the register's words."""
    p = next((p for p in M["R"]["participation"] if p.get("step") == sid and p.get("subject_id") == r.get("to_id")), {})
    return plain(p.get("activity", ""))


def tail(M, sid, pids, calls):
    """The calls no hop draws: those with a recorded place in the step's order, in that order, then the rest in a
    coregion; a call to or from a part that does not take part in the step is said in words."""
    mine = list(calls)
    calls.clear()
    inside_ = [r for r in mine if r.get("from_id") in pids and r.get("to_id") in pids]
    ordered = sorted([r for r in inside_ if cv.seq_for(r, sid).isdigit()], key=lambda r: int(cv.seq_for(r, sid)))
    out = [message(frm=r["from_id"], to=r["to_id"], label=call_label(M, sid, r), num=cv.seq_for(r, sid)) for r in ordered]
    core = [r for r in inside_ if r not in ordered]
    if core:
        out.append({"kind": "core", "msgs": [message(frm=r["from_id"], to=r["to_id"], label=call_label(M, sid, r))
                                             for r in core]})
    for r in mine:
        if r not in inside_:
            a, b = M["subj"].get(r.get("from_id"), {}), M["subj"].get(r.get("to_id"), {})
            out.append(message(kind="note", label=f"a call from {a.get('name', '')} to {b.get('name', '')} is recorded "
                                                  f"for this step, and one of them taking part in it is {GAP}"))
    return out


def scenario(M, sid):
    """Everything one step's drawing and card show, from the register's rows."""
    rows = rows_of(M, sid)
    pids = list(dict.fromkeys(p["subject_id"] for p in rows))
    moves = moves_of(M, sid)
    distinct = list({re.sub(r"\{[^{}]*\}|\"[^\"]*\"", "", mv.get("travels_by", "")): mv for mv in moves}.values())
    calls = calls_of(M, sid)
    if not distinct:
        said = vq.gap_said(M, "step: moves", sid)
        items = [message(kind="note", label=f"how this step travels between its parts: {said}" if said
                         else f"how this step travels between its parts is {GAP}")]
        return dict(sid=sid, rows=rows, pids=pids, moves=moves, inside=inside(M),
                    items=items + tail(M, sid, pids, calls))
    chained = all(fo.state(b.get("from_state")) == fo.state(a.get("to_state")) for a, b in zip(distinct, distinct[1:]))
    groups = [distinct] if chained else [[mv] for mv in distinct]
    operands = []
    for g in groups:
        hl, n0 = [], 0
        for mv in g:
            hs = hops(mv)
            hl += [(n + n0, k, whole) for n, k, alts, whole in hs]
            n0 += len(hs)
        body = hand_offs(M, sid, clause_messages(M, sid, rows, pids, hl), calls)
        place_calls(M, sid, pids, body, calls)
        operands.append((g[0], body))
    items = operands[0][1] if len(operands) == 1 else [
        {"kind": "alt", "operands": [(f"the case is in {fo.state(mv.get('from_state'))}", b) for mv, b in operands]}]
    return dict(sid=sid, rows=rows, pids=pids, moves=moves, inside=inside(M), chained=chained,
                items=items + tail(M, sid, pids, calls))


# ---------------------------------------------------------------- the drawing

COLW, HEADW, HEADH, NESTH, X0, TOP = 150, 132, 58, 104, 64, 40


def walk(items):
    for it in items:
        if it["kind"] == "alt":
            for _, b in it["operands"]:
                yield from walk(b)
        elif it["kind"] == "core":
            yield from it["msgs"]
        else:
            yield it
            yield from it.get("sub", [])


def order_lifelines(M, sc):
    seen = []
    for m in walk(sc["items"]):
        for x in (m.get("frm"), m.get("to")):
            if x and x in sc["pids"] and x not in seen:
                seen.append(x)
    rest = sorted([x for x in sc["pids"] if x not in seen], key=lambda x: M["family"](M["subj"][x]) != "person")
    order = seen + rest
    ins = {a: c for a, c in sc["inside"].items() if a in order and c in order}
    for a, c in ins.items():  # an agent stands just right of the component it runs inside
        order.remove(a)
        order.insert(order.index(c) + 1, a)
    return order, ins


def drawing(M, sc, mid):
    E = cv.esc
    order, ins = order_lifelines(M, sc)
    xs = {x: X0 + HEADW / 2 + i * COLW for i, x in enumerate(order)}
    W = max(560, X0 + len(order) * COLW + 10)
    hosts = set(ins.values())
    head_h = {x: (NESTH if x in hosts or x in ins else HEADH) for x in order}
    heads = []
    for x in order:
        if x in ins:
            continue
        s, kids = M["subj"][x], [a for a, c in ins.items() if c == x]
        fam = M["family"](s)
        style = ' style="stroke-dasharray:8 4"' if s.get("level") == "external dependency" else ""
        w = HEADW + (xs[kids[-1]] - xs[x] if kids else 0)
        g = [f'<g class="head" data-lifeline="{E(x)}"><rect x="{xs[x] - HEADW / 2:g}" y="{TOP}" width="{w:g}" '
             f'height="{head_h[x]}" rx="{8 if fam == "person" else 3}" class="bx"{style}/>']
        lines = cv.wrap(s.get("name", ""), HEADW - 12, 12.5, 2)
        g += [f'<text x="{xs[x]:g}" y="{TOP + 18 + 14 * i}" class="nm">{E(ln)}</text>' for i, ln in enumerate(lines)]
        g.append(f'<text x="{xs[x]:g}" y="{TOP + 18 + 14 * len(lines)}" class="kd">{E(cv.kind_label(M, s))}</text>')
        for a in kids:
            sa, ay = M["subj"][a], TOP + 46
            al = cv.wrap(sa.get("name", ""), HEADW - 24, 12.5, 2)
            g.append(f'<g class="head inner" data-lifeline="{E(a)}" data-inside="{E(x)}">'
                     f'<rect x="{xs[a] - HEADW / 2 + 6:g}" y="{ay}" width="{HEADW - 12}" height="{NESTH - 52}" rx="3" '
                     'class="bx"/>'
                     + "".join(f'<text x="{xs[a]:g}" y="{ay + 17 + 14 * i}" class="nm">{E(ln)}</text>' for i, ln in enumerate(al))
                     + f'<text x="{xs[a]:g}" y="{ay + 17 + 14 * len(al)}" class="kd">{E(cv.kind_label(M, sa))}</text></g>')
        g.append("</g>")
        heads.append("".join(g))
    y0 = TOP + max(head_h.values(), default=HEADH) + 34

    def wrap(text, width, n=3):
        return cv.wrap(text, max(150, width), 12, n) if text else []

    def tx(x, y, lines, cls):
        return "".join(f'<text x="{x:g}" y="{y + 14 * i:g}" class="{cls} h">{E(ln)}</text>' for i, ln in enumerate(lines))

    def line(a, b, y, cls, data):
        end = b - 3 if b > a else b + 3
        mk = {"ar": "a", "ar unrec": "l"}[cls]
        dd = f' data-from="{E(data[0])}" data-to="{E(data[1])}"' if data else ""
        return f'<line x1="{a:g}" y1="{y:g}" x2="{end:g}" y2="{y:g}" class="{cls}"{dd} marker-end="url(#{mid}-{mk})"/>'

    def gutter(m, y):
        if m.get("num"):
            return f'<text x="{X0 - 34}" y="{y + 4:g}" class="num">{E(m["num"])}</text>'
        return ""

    def stepn(n, y):  # the item's number in the card's list of steps, so the two read as one
        n = str(n)
        r = 9 if "." not in n else 12
        return (f'<circle cx="{X0 - 30}" cy="{y:g}" r="{r}" class="hopc"/>'
                f'<text x="{X0 - 30}" y="{y + 4:g}" class="hopt stepn"'
                + ('' if "." not in n else ' style="font-size:9px"') + f'>{n}</text>')

    def one(m, y, right):
        """One message drawn from y down: (svg, the next y)."""
        k = m["kind"]
        if k == "note":
            ls = wrap(m["label"], right - X0, 3)
            return f'<g class="note">{tx(X0, y, ls, "tv dim")}</g>', y + 14 * len(ls) + 14
        if k == "gap":
            a, b = xs[m["frm"]], xs[m["to"]]
            ls = wrap(f'how the turn passes from {M["subj"][m["frm"]]["name"]} to {M["subj"][m["to"]]["name"]}: {GAP}',
                      max(abs(b - a) + 150, 280))
            ay, mx = y + 14 * len(ls) - 4, (a + b) / 2
            return (f'<g class="gap">{tx(min(a, b) + 6, y, ls, "tv dim")}{line(a, b, ay, "ar unrec", (m["frm"], m["to"]))}'
                    f'<circle cx="{mx:g}" cy="{ay:g}" r="8" class="qm"/><text x="{mx:g}" y="{ay + 4:g}" class="qt">?</text></g>',
                    ay + 26)
        cls = "op" if m["op"] else "tv"
        if k == "self" or (k == "msg" and m["frm"] == m["to"]):
            a = xs[m["frm"]]
            ls, dl = wrap(m["label"], right - a - 40), wrap(m["desc"], right - a - 40, 5)
            return (f'{gutter(m, y)}<g class="msg self" data-from="{E(m["frm"])}" data-to="{E(m["frm"])}">'
                    f'<path d="M{a:g} {y - 6:g} h22 v12 h-19" class="ar" marker-end="url(#{mid}-a)"/>'
                    f'{tx(a + 30, y, ls, cls)}{tx(a + 30, y + 14 * len(ls) + 2, dl, "tv dim")}</g>',
                    y + 14 * (len(ls) + len(dl)) + 22)
        if k == "found":
            a, b = X0 - 8, xs[m["to"]]
            ls, dl = wrap(m["label"], b - a - 20), wrap(m["desc"], max(b - a - 20, 300), 5)
            wl = wrap(f'from {m["words"]}: sender {GAP}' if m["words"] else f"sender {GAP}", max(b - a - 20, 300))
            ay = y + 14 * len(ls) - 4
            return (f'{gutter(m, ay)}<g class="found" data-to="{E(m["to"])}">{tx(a + 12, y, ls, cls)}'
                    f'<circle cx="{a:g}" cy="{ay:g}" r="4.5" class="dot"/>{line(a, b, ay, "ar", None)}'
                    f'{tx(a + 12, ay + 18, wl + dl, "tv dim")}</g>', ay + 18 + 14 * len(wl + dl) + 10)
        a, b = xs[m["frm"]], xs[m["to"]]
        lx = min(a, b) + 8
        width = max(abs(b - a) - 16, right - lx - 10 if abs(b - a) < 160 else 0)
        tilde = k == "unplaced"
        ls, dl = wrap(m["label"], width - (12 if tilde else 0)), wrap(m["desc"], max(abs(b - a) - 16, 300), 5)
        ay = y + 14 * max(1, len(ls)) - 4
        s = (("" if tilde else gutter(m, ay))
             + f'<g class="{"msg unplaced" if tilde else "msg"}" data-from="{E(m["frm"])}" data-to="{E(m["to"])}">'
             + (f'<text x="{lx:g}" y="{y:g}" class="til">~</text>' if tilde else "")
             + f'{tx(lx + (12 if tilde else 0), y, ls, cls)}{line(a, b, ay, "ar", (m["frm"], m["to"]))}'
             + f'{tx(lx, ay + 18, dl, "tv dim")}</g>')
        y = ay + 18 + 14 * len(dl) + 8
        for sub in m["sub"]:
            ss, y = one(sub, y + 2, right)
            s += ss
        return s, y

    def draw(items, y, left, right, top_level=False, labels=None):
        out = []
        for n, it in enumerate(items, 1):
            mine = n if top_level else (labels.pop(0) if labels else None)
            if mine is not None:
                out.append(stepn(mine, y + 10))
            k = it["kind"]
            if k == "alt":
                top, inner, seps = y, [], []
                y += 26
                sub = [f"{mine}.{j}" for j in range(1, sum(len(b) for _, b in it["operands"]) + 1)] if mine else None
                for i, (guard, b) in enumerate(it["operands"]):
                    if i:
                        seps.append(y)
                        y += 12
                    gy = y
                    body, y = draw(b, y + 22, left + 8, right - 8, labels=sub)
                    inner.append((gy, guard, body))
                y += 4
                out.append(f'<g class="frag alt"><rect x="{left:g}" y="{top:g}" width="{right - left:g}" height="{y - top:g}" class="frame"/>'
                           f'<path d="M{left:g} {top:g} h34 v13 l-6 6 h-28 z" class="tag"/><text x="{left + 6:g}" y="{top + 14:g}" class="tagt">alt</text>'
                           + "".join(f'<text x="{left + 10:g}" y="{gy + 6:g}" class="guard">[{E(g)}]</text>' for gy, g, _ in inner)
                           + "".join(f'<line x1="{left:g}" y1="{sy:g}" x2="{right:g}" y2="{sy:g}" class="sep"/>' for sy in seps)
                           + "</g>" + "".join(b for _, _, b in inner))
                y += 14
            elif k == "core":
                top = y
                y += 22
                body = []
                for m in it["msgs"]:
                    s, y = one(m, y, right)
                    body.append(s)
                senders = list(dict.fromkeys(m["frm"] for m in it["msgs"]))
                br = "".join(f'<path d="M{xs[x] - 8:g} {top + 10:g} v-6 h16 v6 M{xs[x] - 8:g} {y - 10:g} v6 h16 v-6" class="core"/>'
                             for x in senders)
                lbl = f'<text x="{xs[senders[0]] + 14:g}" y="{top + 8:g}" class="tv dim h">coregion: order {GAP}</text>'
                flat = "".join(re.sub(r"<g [^>]*>|</g>", "", b) for b in body)
                out.append(f'<g class="coregion">{br}{lbl}{flat}</g>')
                y += 4
            elif it.get("loop"):
                a, b = xs[it["frm"]], xs[it["to"]]
                x1, x2 = min(a, b) - 26, max(a, b) + 26
                top = y
                gl = wrap("[" + "; ".join(it["loop"]) + "]", x2 - x1 - 56) + [f"how many times: {GAP}"]
                s, y = one(dict(it, loop=[], sub=[]), y + 24 + 14 * len(gl), right)
                y += 2
                out.append(f'<g class="frag loop" data-from="{E(it["frm"])}" data-to="{E(it["to"])}">'
                           f'<rect x="{x1:g}" y="{top:g}" width="{x2 - x1:g}" height="{y - top:g}" class="frame"/>'
                           f'<path d="M{x1:g} {top:g} h42 v13 l-6 6 h-36 z" class="tag"/><text x="{x1 + 6:g}" y="{top + 14:g}" class="tagt">loop</text>'
                           f'{tx(x1 + 50, top + 14, gl, "guard")}{re.sub(r"<g [^>]*>|</g>", "", s)}</g>')
                y += 12
                for sub in it.get("sub", []):
                    ss, y = one(sub, y, right)
                    out.append(ss)
            else:
                s, y = one(it, y, right)
                out.append(s)
        return "".join(out), y

    body, y = draw(sc["items"], y0, X0 - 48, W - 8, top_level=True)
    bottom = y + 8
    lifelines = "".join(f'<line x1="{xs[x]:g}" y1="{TOP + head_h[x]:g}" x2="{xs[x]:g}" y2="{bottom:g}" class="ll"/>'
                        for x in order)

    def mk(i, c):
        return (f'<marker id="{mid}-{i}" viewBox="0 0 8 8" refX="7.5" refY="4" markerWidth="7" markerHeight="7" '
                f'orient="auto"><path d="M0,0 L8,4 L0,8 z" style="fill:var({c})"/></marker>')
    name = M["step"][sc["sid"]].get("name", "")
    H = bottom + 14
    return (f'<svg class="seq" viewBox="0 0 {W:g} {H:g}" role="img" aria-label="{E("The step " + name + ", its interactions in order")}">'
            f'<defs>{mk("a", "--g600")}{mk("l", "--g400")}</defs>'
            f'<rect x="2" y="4" width="{W - 4:g}" height="{H - 8:g}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">sd {E(name)}</text>{lifelines}{"".join(heads)}{body}</svg>')


# ---------------------------------------------------------------- the card

def card(M, sc):
    E = cv.esc

    def nm(x):
        return E(M["subj"][x].get("name", ""))

    def item(m, label=None):
        sn = f'<span class="sn">{label}</span> ' if label else ""
        if m["kind"] == "note":
            return f'<li>{sn}<i>{E(m["label"][:1].upper() + m["label"][1:])}</i></li>'
        if m["kind"] == "gap":
            return f'<li>{sn}<i>How the turn passes from {nm(m["frm"])} to {nm(m["to"])}: {GAP}.</i></li>'
        lab = f'<code>{E(m["label"])}</code>' if m["op"] else E(m["label"])
        desc = f'; {E(m["desc"])}' if m["desc"] and m["desc"] != m["label"] else ""
        if m["kind"] == "found":
            s = (f'<b>{nm(m["to"])}</b> receives: {lab}{desc}. '
                 + (f'It is sent from {E(m["words"])}; that sender is {GAP}' if m["words"] else f"Its sender is {GAP}"))
        elif m["kind"] == "self" or m["frm"] == m["to"]:
            s = f'<b>{nm(m["frm"])}</b>: {lab}{desc}'
        else:
            s = f'<b>{nm(m["frm"])}</b> → <b>{nm(m["to"])}</b>' + (f": {lab}{desc}" if lab or desc else "")
            if m["kind"] == "unplaced":
                s += f" (its place in the step is {GAP})"
        if m.get("num"):
            s += f" (call {E(m['num'])} in the recorded order)"
        if m.get("loop"):
            s += f'. More than once, in the agent\'s own operations {E("; ".join(m["loop"]))}; how many times is {GAP}'
        subs = "".join(item(x) for x in m.get("sub", []))
        return f"<li>{sn}{s}" + (f"<ul>{subs}</ul>" if subs else "") + "</li>"

    def items(its, labels=None):
        """Top level: the list numbers itself 1, 2, 3. Inside a step's alternative ways: each step carries its number
        as the drawing circles it (3.1, 3.2 ...), counted on across the ways."""
        out = []
        for n, it in enumerate(its, 1):
            mine = n if labels is None else (labels.pop(0) if labels else None)
            lab = None if labels is None else mine
            sn = f'<span class="sn">{lab}</span> ' if lab else ""
            if it["kind"] == "alt":
                sub = [f"{mine}.{j}" for j in range(1, sum(len(b) for _, b in it["operands"]) + 1)] if mine else []
                out.append(f"<li>{sn}One of:<ul>" + "".join(f'<li>{E(g[:1].upper() + g[1:])}:<ul class="ways">{items(b, sub)}</ul></li>'
                                                         for g, b in it["operands"]) + "</ul></li>")
            elif it["kind"] == "core":
                out.append(f"<li>{sn}In an order {GAP}:<ul>" + "".join(item(m) for m in it["msgs"]) + "</ul></li>")
            else:
                out.append(item(it, lab))
        return "".join(out)

    def field(vals):
        vals = list(dict.fromkeys(v for v in vals if v))
        if not vals:
            return GAP
        return E(vals[0]) if len(vals) == 1 else "<ul>" + "".join(f"<li>{E(v)}</li>" for v in vals) + "</ul>"
    sid = sc["sid"]

    def answer(q, vals):  # the answer, or the gap measure-gaps.csv records for it, or the placeholder
        return field(vals) if vq.answered(M, q, sid) else vq.said(M, q, sid, field(vals))
    # moves one after another start with the first
    trig = [(body or f"what starts it is {GAP}") + (f". The case is in {st}" if st else "") for body, st in vq.trigger(M, sc)]
    outcome, prop = vq.right_outcome(M, sid)
    order, ins = order_lifelines(M, sc)
    where = "".join(f"<li>{nm(x)}: {E(where_it_sits(M, x, ins))}</li>" for x in order)
    return ('<div class="card"><dl>'
            f"<dt>Trigger</dt><dd>{answer('step: trigger', trig)}</dd>"
            f'<dt>Interactions, in order</dt><dd><ol>{items(sc["items"])}</ol></dd>'
            f'<dt>Right outcome</dt><dd>{(E(outcome) + (" (proposed)" if prop else "")) if outcome else GAP}</dd>'
            f"<dt>If it does not happen</dt><dd>{answer('step: if it does not happen', vq.if_not(M, sc))}</dd>"
            f"<dt>Timeouts</dt><dd>{answer('step: timeouts', vq.timeouts(M, sc))}</dd>"
            f"<dt>Where each part sits</dt><dd>{f'<ul>{where}</ul>' if where else GAP}</dd></dl></div>")


def sources(M, sc):
    """Where it comes from, with the register's codes and citations, folded away."""
    E, sid = cv.esc, sc["sid"]
    lis = [f'<li>{E(cv.step_title(M, sid))}: {E(M["step"][sid].get("source", ""))}</li>']
    lis += [f'<li>{E(mv.get("move_id"))}: {E(mv.get("source", ""))}</li>' for mv in sc["moves"]]
    lis += [f'<li>{E(p["subject_id"])} {E(M["subj"][p["subject_id"]].get("name", ""))}: {E(p.get("involvement", ""))}'
            + (f', {E(p["operation"])}' if p.get("operation") else "") + "</li>" for p in sc["rows"]]
    lis += [f'<li>{E(r.get("subject_id"))}: {E(r.get("from_id"))} to {E(r.get("to_id"))}, order '
            f'{E(cv.seq_for(r, sid) or "blank")}</li>' for r in calls_of(M, sid)]
    return f'<details class="cites"><summary>Where this comes from</summary><ul>{"".join(lis)}</ul></details>'


KEY = ('<details class="seqkey"><summary>Key to the drawing</summary><ul>'
       "<li>Each part has a box at the top and a dashed line down from it; time runs down the page.</li>"
       "<li>Round box: a person. An AI agent is drawn inside the box of the part it runs inside. "
       "Long-dashed box: an external dependency, run by someone else.</li>"
       "<li>Circled number: the interaction's number in the card's list below. Orange number: a call's place in a "
       "recorded order of calls.</li>"
       "<li>Mono label: the operation that performs the step. Italic label: the register's own description.</li>"
       f"<li>~: a call made within that hop whose place in it is {GAP}. Coregion bracket: calls whose order is {GAP}.</li>"
       f"<li>Dotted arrow with ?: how the turn passes between the two parts is {GAP}. Dot at the left edge: a call whose sender is {GAP}.</li>"
       "<li><i>loop</i>: a call made more than once. <i>alt</i>: one of several ways, each in its own band.</li>"
       "</ul></details>")


def block(M, sid):
    """One step's drawing, its key, its card and where it comes from."""
    sc = scenario(M, sid)
    return (f'<div class="seqfig">{drawing(M, sc, "sq" + re.sub(r"[^A-Za-z0-9]", "_", sid))}</div>'
            f"{KEY}{card(M, sc)}{sources(M, sc)}")
