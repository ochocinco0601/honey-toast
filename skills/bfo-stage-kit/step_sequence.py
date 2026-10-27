"""One process step in order: a UML sequence drawing and one scenario card, both drawn from the register.

one_canvas.py puts each step's drawing and card in a panel beside the map, shown when the step is clicked. Read from
the register only:
- lifecycle.csv: the move that carries the step (named in the step's own source), its hops in order (`travels_by`),
  `timing`, `if_not` and `recovery`;
- participation.csv: the parts that take part (the lifelines), the `operation` each performs the step with;
- subjects.csv: each part's name, kind and owner, and the interactions recorded for the step (`step_hint`, `sequence`);
- agent-system.csv: a part of an AI agent shared with one component (the agent runs inside that component), and the
  agent's own actions that call the same dependency (a call made more than once).
The hops are the order: each hop's sender is the part the register names or
implies, a broker and an outbox store are drawn where the hop passes through them, and each recorded call an arrow draws
is consumed by it. A call no hop accounts for is listed on the card; on a step with no move, the calls are drawn in one
frame whose order is not recorded. What the register does not hold is a gap row on the card, never a note in the
drawing. Nothing is drawn that the register does not hold. Standard library only.
"""
import hashlib
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
            sep_before = "" if res and sep_before == sep == "," else sep_before  # an aside between commas goes with both
            continue
        res += (sep_before + " " if res else "") + seg.strip()
        sep_before = sep or ","
    res = re.sub(r"\s+unlike\s+L\d{2,3}\b,?", "", res)  # a move compared in passing goes with its comma
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
    """The agent's own actions serving this step that call `to` through one of its parts: two or more is a call made
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
    names = [r.get("name", "") for r in rows if r.get("element") == "action"
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
NOT_VERBS = {"is", "was", "as", "its", "this", "thus", "plus", "us", "has", "does", "always", "sometimes"}
# a clause that opens with one of these touches the store the part keeps its data in
STORE_VERB = re.compile(r"^(?:reads|selects|writes|sets|removes|deletes|stores|updates|inserts|saves|marks|loads|"
                        r"queries|fetches|commits|clears)\b")


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
    m = dict(kind="msg", frm=None, to=None, label="", op=False, desc="", hop=None, sub=[], loop=[], asy=False)
    m.update(kw)
    return m


def subject(M, pids, text):
    """(the part a clause opens with, the rest of the clause) for a clause of the form "<part> <verb>s ...", else
    (None, the clause). The longest opening that names one part of the process step wins."""
    w = (text or "").split()
    for n in range(min(5, len(w) - 1), 0, -1):
        if re.fullmatch(r"[a-z]+s", w[n]) and w[n] not in NOT_VERBS:
            x = resolve(M, pids, " ".join(w[:n]))
            if x:
                return x, " ".join(w[n:])
    return None, text


def call_label(r):
    """A recorded call is labelled with its own words, up to the first ";", else with its operation."""
    words = plain(re.split(r";", plain(r.get("source", "")) or "", maxsplit=1)[0]).strip(" ,")
    return words or plain(r.get("operation", ""))


def need_ids(move):
    return [x.split()[0] for x in cv.ids(move.get("needs")) if x.split()]


def clause_messages(M, sid, rows, pids, seq, calls, gaps):
    """The messages of the step's hops, in order. Who sends each hop, in this order: the clause's subject; an "X to
    Y" head whose X names a part; a "from X" whose X names a part; for an outbox or message hop, the broker and the
    outbox store; the person of the hop before. A found message only where none of these names a part. A clause that
    names no receiver is a gap row on the card, never a note in the drawing."""
    persons = [x for x in pids if M["family"](M["subj"][x]) == "person"]
    rec = {(r.get("from_id"), r.get("to_id")): r for r in calls}

    def fam(x):
        return M["family"](M["subj"][x])
    brokers = [x for x in pids if M["subj"][x].get("part_kind") == "message broker"]
    broker = brokers[0] if len(brokers) == 1 else None

    def store_of(actor, move, text, outbox=False):
        """The store of the move's `needs` the actor has a recorded call to: one, or the one the clause names."""
        need = need_ids(move)
        cand = [x for x in pids if fam(x) == "store" and (actor, x) in rec
                and (outbox and "outbox" in (M["subj"][x].get("purpose") or "").lower() or not outbox and x in need)]
        if len(cand) > 1:
            cand = [x for x in mentions(M, cand, text)]
        return cand[0] if len(cand) == 1 else None

    def into_broker(exclude):
        got = list(dict.fromkeys(f for f, t in rec if t == broker and f in pids and f not in exclude))
        return got[0] if len(got) == 1 else None

    out = []
    last_actor, last_event = None, None
    for n, kind, text, move in seq:
        actor, rest = subject(M, pids, text)
        if kind == "person":
            who = mentions(M, persons, text)
            frm = who[0] if len(who) == 1 else (persons[0] if len(persons) == 1 else None)
            if frm:
                out.append(message(kind="person", frm=frm, label=text, hop=n))
            else:
                gaps.append(text)
            continue
        ops = ops_in(rows, text)
        if kind in ("in-process", "timer", "poll"):
            first = []
            doer, body = actor, rest
            if not doer and ops:
                op, owners = ops[0]
                agents = [x for x in owners if fam(x) == "agent"]
                hosts = [x for x in owners if x not in agents]
                body = re.sub(r"\s+", " ", text.replace(op, " ")).strip(" ,")
                if agents and hosts:
                    first = [message(frm=agents[0], to=hosts[0], label=op, op=True, desc=text, hop=n)]
                    doer = hosts[0]
                else:
                    first = [message(kind="self", frm=owners[0], label=op, op=True, desc=text, hop=n)]
                    doer = owners[0]
            if not doer:
                # in-process work runs in a part that performs the step: the one the clause names, else the one the
                # case was last passed to, else the one that made the last call (a store or a dependency only answers)
                doers = [p["subject_id"] for p in rows if p.get("involvement") != "supports"]
                named = [x for x in mentions(M, pids, text) if x in doers]
                prev = next((m for m in reversed(out) if m["kind"] in ("msg", "self", "found")), None)
                last = [x for x in ((prev["to"], prev["frm"]) if prev else ()) if x in doers]
                doer = named[0] if len(named) == 1 else (last[0] if last else None)
            if not doer:
                gaps.append(text)
                continue
            store = store_of(doer, move, text)
            if first:  # the operation draws the hop; what it writes, where the clause says, follows it
                if store and STORE_VERB.match(body):
                    first[0]["desc"] = ""
                    first.append(message(frm=doer, to=store, label=body, hop=n))
                elif store:
                    first.append(message(frm=doer, to=store, label=call_label(rec[(doer, store)]), hop=n))
                out += first
            else:
                done, part = False, []
                for ph in [p.strip(" ,") for p in re.split(r",?\s+then\s+", body) if p.strip(" ,")]:
                    if store and not done and STORE_VERB.match(ph):
                        part.append(message(frm=doer, to=store, label=ph, hop=n))
                        done = True
                    else:
                        part.append(message(kind="self", frm=doer, label=ph, hop=n))
                if store and not done:  # what the part works on is read before it works on it
                    part.insert(0, message(frm=doer, to=store, label=call_label(rec[(doer, store)]), hop=n))
                out += part
            last_actor = doer
            continue
        if kind in ("outbox", "message") and broker:
            if ops:
                last_event = ops[0]
            ev, owners = last_event or (None, [])
            consumers = [x for x in owners if fam(x) != "agent"] or list(owners)
            label, is_op = (ev, True) if ev else (rest if actor else text, False)
            said = rest if actor else text
            if ev:  # the label names the event; the words under it say only the rest
                said = re.sub(r"\s{2,}", " ", said.replace(ev, " ")).strip(" ,")
            desc = "" if not said or norm_op(said).strip() == norm_op(label).strip() else said
            if kind == "outbox":
                pub = actor or into_broker(consumers) or last_actor
                if not pub or pub == broker:
                    out.append(message(kind="found", to=broker, label=label, op=is_op, desc=desc, hop=n, asy=True))
                    continue
                store = store_of(pub, move, text, outbox=True)
                if store:
                    phases = re.split(r",?\s+(?:and|then)\s+(?=publish)", said, maxsplit=1)
                    if len(phases) > 1 and STORE_VERB.match(phases[0]):
                        out.append(message(frm=pub, to=store, label=phases[0].strip(" ,"), hop=n))
                        desc = ""
                    else:
                        out.append(message(frm=pub, to=store, label=call_label(rec[(pub, store)]), hop=n))
                out.append(message(frm=pub, to=broker, label=label, op=is_op, desc=desc, hop=n, asy=True))
                last_actor = pub
                continue
            m = TO.match(text)
            to = consumers[0] if consumers else (resolve(M, pids, m.group("b")) if m else None)
            if not to:
                named = [x for x in mentions(M, pids, text) if x != broker]
                to = named[0] if len(named) == 1 else None
            prev = next((x for x in reversed(out) if x["kind"] in ("msg", "found")), None)
            if not (prev and prev["to"] == broker):  # the event reaches the broker first
                pub = actor or into_broker([to] if to else []) or last_actor
                if pub and pub != broker:
                    out.append(message(frm=pub, to=broker, label=label, op=is_op, hop=n, asy=True))
            if to:
                out.append(message(frm=broker, to=to, label=label, op=is_op, desc=desc, hop=n, asy=True))
                last_actor = to
            else:
                gaps.append(text)
            continue
        # a call, or a message with no broker among the parts: from a part to a part
        segs = [s.strip() for s, _ in _segments(rest if actor else text) if s.strip()]
        head, more = (segs[0], segs[1:]) if segs else ("", [])
        m = TO.match(head)
        frm, to, label = actor, None, rest if actor else text
        if m and len(m.group("a").split()) <= 4:
            a, b = resolve(M, pids, m.group("a")), resolve(M, pids, m.group("b"))
            if b:
                to = b
                frm = frm or a
                label = ", ".join([head[m.end():].strip(" ,:")] + more).strip(" ,")
        owners = [x for _, xs in ops for x in xs]
        if not to:
            hosts = [x for x in owners if fam(x) != "agent"]
            named = [x for x in mentions(M, pids, head) if x != frm]  # the receivers of this clause, not the next one's
            if not named:
                named = [x for x in mentions(M, pids, rest if actor else text) if x != frm]
            if owners:
                to = (hosts or owners)[0]
            elif len(named) == 1:
                to = named[0]
            elif frm and len(named) > 1:  # one sender, several parts named: one call to each, in its own words
                for x in named:
                    out.append(message(frm=frm, to=x, label=call_label(rec[(frm, x)]) if (frm, x) in rec else label, hop=n))
                last_actor = named[-1]
                continue
        if ops and to in owners:  # the operation labels the call; the rest of the clause, where it adds words, under it
            op = ops[0][0]
            label, desc, is_op = op, ("" if norm_op(label).strip() == norm_op(op) else label), True
        else:
            desc, is_op = "", False
        if not frm:
            fm = re.search(r"\bfrom\s+((?:any|a|an|the)\s+)?([^,;]+)", _no_paths(text))
            frm = resolve(M, pids, fm.group(2)) if fm else None
        if not frm and out and out[-1]["kind"] == "person":
            frm = out[-1]["frm"]
        if not to:
            gaps.append(text)
            continue
        if not frm:
            out.append(message(kind="found", to=to, label=label, op=is_op, desc=desc, hop=n))
        else:
            out.append(message(frm=frm, to=to, label=label, op=is_op, desc=desc, hop=n))
        last = out[-1]
        last_actor = to
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


def drawn(items):
    """Every message the drawing draws, nested ones too."""
    for m in items:
        if m["kind"] == "alt":
            for _, b in m["operands"]:
                yield from drawn(b)
        else:
            yield m
            yield from drawn(m.get("sub", []))


def place_calls(M, sid, pids, msgs, calls):
    """Take out of `calls` each recorded call an arrow draws (the same two ends). A clause of a message that names
    another part, with a recorded call to it from one of the message's ends, becomes that call, drawn under it."""
    def take(a, b):
        got = [r for r in calls if r.get("from_id") == a and r.get("to_id") == b]
        for r in got:
            calls.remove(r)
        return got[0] if got else None
    for m in msgs:
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
                        hit = message(kind="msg", frm=e, to=x, label=seg, sub=[])
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
    for m in list(drawn(msgs)):
        if m["kind"] == "msg":
            take(m["frm"], m["to"])


def hand_offs(M, sid, msgs, calls, gaps):
    """Between two messages, where the next sender is not the part the case was last passed to: the hand-off, as a
    recorded call when there is one, else a gap row on the card."""
    out, prev = [], None
    for m in msgs:
        if prev and m["frm"] and m["kind"] in ("msg", "self"):
            last_to = prev["to"] or prev["frm"]
            if last_to and m["frm"] not in (last_to, prev["frm"]) and M["family"](M["subj"][m["frm"]]) != "person":
                r = next((r for r in calls if r.get("from_id") == last_to and r.get("to_id") == m["frm"]), None)
                if r:
                    out.append(message(frm=last_to, to=m["frm"], label=call_label(r)))
                else:
                    a, b = M["subj"][last_to]["name"], M["subj"][m["frm"]]["name"]
                    gaps.append(f"how the turn passes from {a} to {b}: {GAP}")
        out.append(m)
        if m["kind"] in ("msg", "self", "found"):
            prev = m
    return out


def calls_into(calls):
    """{receiver: [(sender, receiver), one per recorded call]}."""
    out = {}
    for r in calls:
        out.setdefault(r.get("to_id"), []).append((r.get("from_id"), r.get("to_id")))
    return out


def only_call_into(into, frm, parent):
    """Whether the call `parent` (sender, receiver) is the only recorded call into `frm` in this process step: the one
    condition on which a call from `frm` is drawn under it. Any other way into the sender, and it stands at the top."""
    got = into.get(frm, [])
    return len(got) <= 1 and all(x == parent for x in got)


def frame_calls(M, sid, pids, calls):
    """A step with no move: the calls with a recorded place in the order, in it; the rest, each
    under the call whose receiver makes it where there is one, in one frame whose order is not recorded."""
    mine = [r for r in calls if r.get("from_id") in pids and r.get("to_id") in pids]
    ordered = sorted([r for r in mine if cv.seq_for(r, sid).isdigit()], key=lambda r: int(cv.seq_for(r, sid)))
    rest = [r for r in mine if r not in ordered]
    msgs = {id(r): message(frm=r["from_id"], to=r["to_id"], label=call_label(r), sub=[]) for r in mine}
    parent, into = {}, calls_into(calls)  # every call recorded for the step, its parts or not
    for r in rest:
        for p in ordered + rest:
            if (p is not r and p["to_id"] == r["from_id"] and p["from_id"] != r["to_id"]
                    and only_call_into(into, r["from_id"], (p["from_id"], p["to_id"]))):
                up, seen = p, {id(r)}  # never under a call that is itself under this one
                while up is not None and id(up) not in seen:
                    seen.add(id(up))
                    up = parent.get(id(up))
                if up is None:
                    parent[id(r)] = p
                    break
    for r in mine:
        if id(r) in parent:
            msgs[id(parent[id(r)])]["sub"].append(msgs[id(r)])
    top = [msgs[id(r)] for r in ordered]
    norec = [msgs[id(r)] for r in rest if id(r) not in parent]
    return top, norec


def outside(M, calls, pids):
    return [f"a call from {M['subj'].get(r.get('from_id'), {}).get('name', '')} to "
            f"{M['subj'].get(r.get('to_id'), {}).get('name', '')} is recorded for this process step, and one of them "
            f"taking part in it is {GAP}" for r in calls if not (r.get("from_id") in pids and r.get("to_id") in pids)]


def scenario(M, sid):
    """Everything one step's drawing and card show, from the register's rows: `items` drawn in order, `norec` the
    calls of a step with no move whose order is not recorded, `other` the recorded calls no hop accounts for on a step
    with hops (the card lists them), `gaps` what the register does not hold (the card's gap rows)."""
    rows = rows_of(M, sid)
    pids = list(dict.fromkeys(p["subject_id"] for p in rows))
    moves = moves_of(M, sid)
    distinct = list({re.sub(r"\{[^{}]*\}|\"[^\"]*\"", "", mv.get("travels_by", "")): mv for mv in moves}.values())
    calls = calls_of(M, sid)
    gaps = []
    base = dict(sid=sid, rows=rows, pids=pids, moves=moves, inside=inside(M))
    if not distinct:
        said = vq.gap_said(M, "step: moves", sid)
        gaps.append(f"how this process step travels between its parts: {said}" if said
                    else f"how this process step travels between its parts is {GAP}")
        top, norec = frame_calls(M, sid, pids, calls)
        return dict(base, items=top, norec=norec, other=[], gaps=gaps + outside(M, calls, pids))
    chained = all(fo.state(b.get("from_state")) == fo.state(a.get("to_state")) for a, b in zip(distinct, distinct[1:]))
    groups = [distinct] if chained else [[mv] for mv in distinct]
    operands, left = [], list(calls)
    for g in groups:
        hl, n0 = [], 0
        for mv in g:
            hs = hops(mv)
            hl += [(n + n0, k, whole, mv) for n, k, alts, whole in hs]
            n0 += len(hs)
        body = hand_offs(M, sid, clause_messages(M, sid, rows, pids, hl, calls, gaps), calls, gaps)
        place_calls(M, sid, pids, body, left)
        operands.append((g[0], body))
    # On a step with hops, a call no hop accounts for is the residue, listed on the card and never
    # drawn, not even under a call whose receiver makes it (where it runs in the order is not recorded)
    items = operands[0][1] if len(operands) == 1 else [
        {"kind": "alt", "operands": [(f"the case is in {fo.state(mv.get('from_state'))}", b) for mv, b in operands]}]
    other = [message(frm=r["from_id"], to=r["to_id"], label=call_label(r))
             for r in left if r.get("from_id") in pids and r.get("to_id") in pids]
    return dict(base, chained=chained, items=items, norec=[], other=other, gaps=gaps + outside(M, left, pids))


# ---------------------------------------------------------------- the drawing

COLW, HEADW, HEADH, NESTH, X0, TOP = 150, 132, 58, 104, 64, 40
FS = 13  # every text of the drawing, measured as it renders
STYLE = "<style>" + "".join(f"svg.seq[data-sd] .{c}{{font-size:{FS}px}}" for c in
                            ("tagt", "nm", "kd", "op", "tv", "hopt", "guard", "stepn", "ow")) + \
        f"svg.seq[data-sd] .tv.dim{{font-size:{FS}px}}svg.seq[data-sd] .ar.asy{{stroke-dasharray:none}}</style>"


def walk(items):
    for it in items:
        if it["kind"] == "alt":
            for _, b in it["operands"]:
                yield from walk(b)
        else:
            yield it
            yield from walk(it.get("sub", []))


def order_lifelines(M, sc):
    seen = []
    for m in list(walk(sc["items"])) + list(walk(sc.get("norec", []))):
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


def under_head(M, s):
    """The words under a head: its kind, and for a part run outside the system, that it is."""
    out = [cv.kind_label(M, s)]
    if s.get("level") == "external dependency":
        out.append("run by someone else")
    return [x for x in out if x]


FIT = 1200  # the column every drawing fits at its natural size: the lifelines draw closer, the drawing never scales


def pitch_of(n):
    """(the distance between lifelines, a head's width) for `n` lifelines, so the drawing fits FIT."""
    pitch = min(COLW, (FIT - X0 - 10 - 110) / max(1, n))
    return pitch, min(HEADW, pitch - 18)


def text_w(s, mono=False):
    """A text's width at the drawing's size: an operation is set in a monospace face, the rest in a sans."""
    return len(s) * FS * (0.62 if mono else 0.54)


def pieces(word, camel):
    """A word cut at its seams: after "-", "_", "/" or "."; with `camel`, at a CamelCase hump too."""
    seams = r"(?<=[-_/.])(?=.)" + (r"|(?<=[a-z0-9])(?=[A-Z])" if camel else "")
    return [p for p in re.split(seams, word) if p]


def pack(ps, width, mono):
    """A word's pieces, joined into as few lines of `width` as they fill in turn."""
    out, cur = [], ""
    for p in ps:
        if cur and text_w(cur + p, mono) > width:
            out.append(cur)
            cur = p
        else:
            cur += p
    return out + [cur]


def seam_wrap(text, width, mono=False, camel=True):
    """Words to lines of `width`, every word whole: a word wider than the line starts a line of its own and breaks
    only at its seams, so no line ends inside a word, nor holds a word's first piece after other words ("writes Order").
    Nothing is cut short."""
    lines, cur = [], ""
    for w in (text or "").split():
        t = (cur + " " + w).strip()
        if text_w(t, mono) <= width:
            cur = t
        elif text_w(w, mono) <= width:
            lines.append(cur)
            cur = w
        else:
            if cur:
                lines.append(cur)
            ps = pieces(w, camel)
            got = pack(ps, width, mono)
            narrow = width  # the narrowest line that keeps as few lines, so no short last piece hangs alone
            while narrow - 4 >= max(text_w(p, mono) for p in ps) and len(pack(ps, narrow - 4, mono)) == len(got):
                narrow -= 4
            got = pack(ps, narrow, mono)
            lines += got[:-1]
            cur = got[-1]
    if cur:
        lines.append(cur)
    return lines


def widest_piece(text, camel=False, mono=False):
    return max((text_w(p, mono) for w in (text or "").split() for p in pieces(w, camel)), default=0)


def layout(M, order, ins):
    """({lifeline: x}, {lifeline: its head's width}, the drawing's width). A head is as wide as the rest, or as its
    widest piece of name or of the words under it, whichever is wider. The lifelines draw closer until the drawing fits
    FIT; where even the narrowest heads do not, the heads stand closer and the room right of the last lifeline
    narrows."""
    need = {}
    for x in order:
        s = M["subj"][x]
        under = [cv.kind_label(M, s) or ""] if x in ins else under_head(M, s)
        need[x] = max(widest_piece(s.get("name", "")), max((widest_piece(k) for k in under), default=0)) + (
            24 if x in ins else 12)
    for space in (18, 8):
        pitch, headw = pitch_of(len(order))
        while True:
            hw = {x: max(headw, need[x]) for x in order}
            xs, at, prev = {}, 0, None
            for x in order:
                at = X0 + hw[x] / 2 if prev is None else at + max(pitch, (hw[prev] + hw[x]) / 2 + space)
                xs[x], prev = at, x
            edge = (xs[prev] + hw[prev] / 2 + space) if prev else X0 + 10
            if edge + 120 <= FIT:
                return xs, hw, max(560, edge + 120)
            if pitch <= 40:
                break
            pitch -= 2
            headw = min(HEADW, pitch - 18)
    return xs, hw, max(FIT, edge + 10)


def own_id(M, sc, order):
    """A short id of what one drawing draws (its process step, its parts, its messages), the same on every build."""
    said = [M["step"][sc["sid"]].get("name", "")] + [M["subj"][x].get("name", "") for x in order] + [
        f'{m.get("frm")}>{m.get("to")}:{m.get("label")}' for m in list(walk(sc["items"])) + list(walk(sc.get("norec", [])))]
    return hashlib.sha1("\n".join(said).encode("utf-8")).hexdigest()[:8]


def drawing(M, sc, mid, marks=None):
    """The step's UML sequence drawing. `marks`, for a page that marks where each measure sits, holds optional hooks:
    "head"(lifeline, width) -> (height, draw(cx, y)) for what a head holds under its name; "arrow"(message) ->
    (height, draw(x, y)) for what sits under an arrow; "tag" -> (height, width, draw(x, y)) beside the frame's name;
    "at"(lifeline) -> the place a head stands for, each head then a mark of it; "link"(lifeline) -> a page its name
    opens, or "", the name then a link drawn over the head's mark; "numbers" False to leave out the circled numbers
    that index the card's list."""
    E = cv.esc
    marks = marks or {}
    order, ins = order_lifelines(M, sc)
    mid = f"{mid}-{own_id(M, sc, order)}"  # two drawings on one page never share an arrowhead
    xs, hw, W = layout(M, order, ins)  # a label beside the last lifeline has room to run right
    tag = marks.get("tag")
    top = max(TOP, 8 + tag[0] + 10) if tag else TOP  # the heads start under the frame's name and what sits beside it
    hosts = set(ins.values())
    # a head's name wraps whole, only at its seams, never cut short
    names = {x: seam_wrap(M["subj"][x].get("name", ""), hw[x] - 12, camel=False) for x in order}
    inner = {a: seam_wrap(M["subj"][a].get("name", ""), hw[a] - 24, camel=False) for a in ins}
    kinds = {x: [ln for k in (under_head(M, M["subj"][x])[:1 if x in hosts else 2] if x not in ins
                              else [cv.kind_label(M, M["subj"][x])])
                 for ln in seam_wrap(k, hw[x] - (24 if x in ins else 12), camel=False)] for x in order}
    inner_y = {a: top + 18 + 15 * (len(names[ins[a]]) + len(kinds[ins[a]])) - 2 for a in ins}  # under the host's words
    inner_h = {a: 17 + 14 * (len(inner[a]) + len(kinds[a]) - 1) + 7 for a in ins}
    base = {}
    for x in order:
        if x in hosts or x in ins:
            c = ins.get(x, x)
            kids = [a for a in ins if ins[a] == c]
            base[x] = max(inner_y[a] + inner_h[a] for a in kids) + 6 - top
        else:  # what a head holds under its words starts right under them
            base[x] = 18 + 15 * (len(names[x]) + len(kinds[x])) + (-6 if marks.get("head") else 4)
    extra = {x: (marks["head"](x, hw[x] - 12) if marks.get("head") else None) for x in order}
    head_h = {}
    for x in order:
        c = ins.get(x, x)
        group = [c] + [a for a in ins if ins[a] == c]
        head_h[x] = max(HEADH, max(base[x] + (extra[y][0] if extra[y] else 0) for y in group))
    heads, hits, over = [], [], []
    link = marks.get("link") or (lambda x: "")

    def named(x, texts):
        """A head's name: in its head, or, where it opens a page, a link over the head's mark."""
        h = link(x)
        if not h:
            return texts
        over.append(f'<a href="{E(h)}" class="partlink">{"".join(texts)}</a>')
        return []
    for x in order:
        if x in ins:
            continue
        s, kids = M["subj"][x], [a for a, c in ins.items() if c == x]
        fam = M["family"](s)
        style = ' style="stroke-dasharray:8 4"' if s.get("level") == "external dependency" else ""
        left = xs[x] - hw[x] / 2
        w = (xs[kids[-1]] + hw[kids[-1]] / 2 if kids else xs[x] + hw[x] / 2) - left
        g = [f'<g class="head" data-lifeline="{E(x)}"><rect x="{left:g}" y="{top}" width="{w:g}" '
             f'height="{head_h[x]}" rx="{8 if fam == "person" else 3}" class="bx"{style}/>']
        lines = names[x]
        g += named(x, [f'<text x="{xs[x]:g}" y="{top + 18 + 15 * i}" class="nm">{E(ln)}</text>' for i, ln in enumerate(lines)])
        g += [f'<text x="{xs[x]:g}" y="{top + 18 + 15 * (len(lines) + i)}" class="kd">{E(k)}</text>'
              for i, k in enumerate(kinds[x])]
        for a in kids:
            ay, al = inner_y[a], inner[a]
            g.append(f'<g class="head inner" data-lifeline="{E(a)}" data-inside="{E(x)}">'
                     f'<rect x="{xs[a] - hw[a] / 2 + 6:g}" y="{ay:g}" width="{hw[a] - 12:g}" height="{inner_h[a]:g}" rx="3" '
                     'class="bx"/>'
                     + "".join(named(a, [f'<text x="{xs[a]:g}" y="{ay + 17 + 14 * i:g}" class="nm">{E(ln)}</text>'
                                         for i, ln in enumerate(al)]))
                     + "".join(f'<text x="{xs[a]:g}" y="{ay + 17 + 14 * (len(al) + i):g}" class="kd">{E(k)}</text>'
                               for i, k in enumerate(kinds[a])) + "</g>")
        for y in [x] + kids:
            if extra[y]:
                g.append(extra[y][1](xs[y], top + base[y]))
        g.append("</g>")
        heads.append("".join(g))
        at = marks.get("at")
        if at:  # each head a mark of its place, drawn over it so a click anywhere on the head reaches it
            hits.append(f'<g class="mark" data-at="{E(at(x))}" tabindex="0"><rect x="{left:g}" y="{top}" '
                        f'width="{w:g}" height="{head_h[x]}" rx="3" class="hit"/></g>')
            hits += [f'<g class="mark" data-at="{E(at(a))}" tabindex="0"><rect x="{xs[a] - hw[a] / 2 + 6:g}" '
                     f'y="{inner_y[a]:g}" width="{hw[a] - 12:g}" height="{inner_h[a] + (extra[a][0] if extra[a] else 0):g}" '
                     f'rx="3" class="hit"/></g>' for a in kids]
    y0 = top + max(head_h.values(), default=HEADH) + 34

    def wrap(text, width, n=4):
        return cv.wrap(text, max(150, width), FS, n) if text else []

    ll = sorted(xs.values())

    def gap(lo, hi):
        """(left, right) a message's words sit in, clear of every lifeline it does not end on: along its own arrow,
        inside its span; a self-message's (lo == hi), between its lifeline and the next."""
        if lo == hi:
            nxt = [v for v in ll if v > lo + 1]
            return lo + 30, (nxt[0] - 8 if nxt else W - 8)
        return lo + 8, hi - 8

    def tx(x, y, lines, cls):
        return "".join(f'<text x="{x:g}" y="{y + 15 * i:g}" class="{cls} h">{E(ln)}</text>' for i, ln in enumerate(lines))

    def line(a, b, y, data, asy):
        end = b - 3 if b > a else b + 3
        dd = f' data-from="{E(data[0])}" data-to="{E(data[1])}"' if data else ""
        return (f'<line x1="{a:g}" y1="{y:g}" x2="{end:g}" y2="{y:g}" class="ar{" asy" if asy else ""}"{dd} '
                f'marker-end="url(#{mid}-{"o" if asy else "a"})"/>')

    def stepn(n, y):  # the item's number in the card's list of steps, so the two read as one
        n = str(n)
        r = 10 if "." not in n else 15 if n.count(".") == 1 else 20
        return (f'<circle cx="{X0 - 30}" cy="{y:g}" r="{r}" class="hopc"/>'
                f'<text x="{X0 - 30}" y="{y + 4.5:g}" class="hopt stepn">{n}</text>')

    def labels(m, width):
        """(label lines, description lines), every word whole and nothing cut short."""
        return seam_wrap(m["label"], width, mono=m["op"]), seam_wrap(m["desc"], width)

    def one(m, y, right, num=None):
        """One message drawn from y down, with its number where it has one: (svg, the next y). A call drawn under it
        is numbered on from it ("2.1")."""
        k = m["kind"]
        lead = stepn(num, y + 10) if num is not None and marks.get("numbers", True) else ""
        cls = "op" if m["op"] else "tv"
        ex = marks["arrow"](m) if marks.get("arrow") else None  # what sits under the arrow: (height, draw(x, y))
        eh = ex[0] + 6 if ex else 0
        if k == "self" or (k == "msg" and m["frm"] == m["to"]):
            a = xs[m["frm"]]
            gl, gr = gap(a, a)
            ls, dl = labels(m, gr - gl)
            ey = y + 15 * len(ls) - 8
            s = (f'<g class="msg self" data-from="{E(m["frm"])}" data-to="{E(m["frm"])}">'
                 f'<path d="M{a:g} {y - 6:g} h22 v12 h-19" class="ar" marker-end="url(#{mid}-a)"/>'
                 f'{tx(a + 30, y, ls, cls)}{tx(a + 30, y + 15 * len(ls) + 2 + eh, dl, "tv dim")}</g>'
                 + (ex[1](a + 30, ey) if ex else ""))
            y += 15 * (len(ls) + len(dl)) + 22 + eh
        elif k == "found":
            a, b = X0 - 8, xs[m["to"]]
            ls, dl = labels(m, b - a - 20)
            dl = seam_wrap("sender not recorded", b - a - 20) + dl
            ay = y + 15 * max(1, len(ls)) - 4
            s = (f'<g class="found" data-to="{E(m["to"])}">{tx(a + 12, y, ls, cls)}'
                 f'<circle cx="{a:g}" cy="{ay:g}" r="4.5" class="dot"/>{line(a, b, ay, None, m["asy"])}'
                 f'{tx(a + 12, ay + 18 + eh, dl, "tv dim")}</g>'
                 + (ex[1](a + 12, ay + 6) if ex else ""))
            y = ay + 18 + 15 * len(dl) + 10 + eh
        else:
            a, b = xs[m["frm"]], xs[m["to"]]
            lx, rx = gap(min(a, b), max(a, b))
            ls, dl = labels(m, rx - lx)
            ay = y + 15 * max(1, len(ls)) - 4
            klass = "msg sub" if m.get("_sub") else "msg"
            s = (f'<g class="{klass}" data-from="{E(m["frm"])}" data-to="{E(m["to"])}">'
                 f'{line(a, b, ay, (m["frm"], m["to"]), m["asy"])}{tx(lx, y, ls, cls)}'
                 f'{tx(lx, ay + 18 + eh, dl, "tv dim")}</g>'
                 + (ex[1](lx, ay + 6) if ex else ""))
            y = ay + 18 + 15 * len(dl) + 8 + eh
        for i, sub in enumerate(m.get("sub", []), 1):
            ss_, y = one(dict(sub, _sub=True), y + 2, right, f"{num}.{i}" if num is not None else None)
            s += ss_
        return lead + s, y

    def draw(items, y, left, right, top_level=False, labels_=None):
        out = []
        for n, it in enumerate(items, 1):
            mine = n if top_level else (labels_.pop(0) if labels_ else None)
            if mine is not None and marks.get("numbers", True) and (it["kind"] == "alt" or it.get("loop")):
                out.append(stepn(mine, y + 10))
            if it["kind"] == "alt":
                top, inner, seps = y, [], []
                y += 26
                sub = [f"{mine}.{j}" for j in range(1, sum(len(b) for _, b in it["operands"]) + 1)] if mine else None
                for i, (guard, b) in enumerate(it["operands"]):
                    if i:
                        seps.append(y)
                        y += 12
                    gy = y
                    body, y = draw(b, y + 22, left + 8, right - 8, labels_=sub)
                    inner.append((gy, guard, body))
                y += 4
                out.append(f'<g class="frag alt"><rect x="{left:g}" y="{top:g}" width="{right - left:g}" height="{y - top:g}" class="frame"/>'
                           f'<path d="M{left:g} {top:g} h38 v14 l-6 6 h-32 z" class="tag"/><text x="{left + 6:g}" y="{top + 15:g}" class="tagt">alt</text>'
                           + "".join(f'<text x="{left + 10:g}" y="{gy + 6:g}" class="guard">[{E(g)}]</text>' for gy, g, _ in inner)
                           + "".join(f'<line x1="{left:g}" y1="{sy:g}" x2="{right:g}" y2="{sy:g}" class="sep"/>' for sy in seps)
                           + "</g>" + "".join(b for _, _, b in inner))
                y += 14
            elif it.get("loop"):
                a, b = xs[it["frm"]], xs[it["to"]]
                x1, x2 = min(a, b) - 26, max(a, b) + 26
                top = y
                gl = wrap("[" + "; ".join(it["loop"]) + "]", x2 - x1 - 56)
                s, y = one(dict(it, loop=[], sub=[]), y + 24 + 15 * len(gl), right)
                y += 2
                out.append(f'<g class="frag loop" data-from="{E(it["frm"])}" data-to="{E(it["to"])}">'
                           f'<rect x="{x1:g}" y="{top:g}" width="{x2 - x1:g}" height="{y - top:g}" class="frame"/>'
                           f'<path d="M{x1:g} {top:g} h46 v14 l-6 6 h-40 z" class="tag"/><text x="{x1 + 6:g}" y="{top + 15:g}" class="tagt">loop</text>'
                           f'{tx(x1 + 54, top + 15, gl, "guard")}{re.sub(r"<g [^>]*>|</g>", "", s)}</g>')
                y += 12
                for i, sub in enumerate(it.get("sub", []), 1):
                    ss_, y = one(dict(sub, _sub=True), y, right, f"{mine}.{i}" if mine is not None else None)
                    out.append(ss_)
            else:
                s, y = one(it, y, right, mine)
                out.append(s)
        return "".join(out), y

    body, y = draw(sc["items"], y0, X0 - 48, W - 8, top_level=True)
    if sc.get("norec"):  # one plain frame, named in words: no operator, no brackets, no numbers
        ftop, left, right = y, X0 - 48, W - 8
        within, y = draw_plain(sc["norec"], y + 34, right, one)
        y += 4
        body += (f'<g class="norec"><rect x="{left:g}" y="{ftop:g}" width="{right - left:g}" height="{y - ftop:g}" class="frame"/>'
                 f'<text x="{left + 8:g}" y="{ftop + 18:g}" class="tagt">order not recorded</text>{within}</g><!-- /norec -->')
        y += 14
    bottom = y + 8
    lifelines = "".join(f'<line x1="{xs[x]:g}" y1="{top + head_h[x]:g}" x2="{xs[x]:g}" y2="{bottom:g}" class="ll"/>'
                        for x in order)

    def mk(i, c, opened=False):
        path = ('<path d="M0,0 L8,4 L0,8" style="fill:none;stroke:var({c});stroke-width:1.3"/>' if opened
                else '<path d="M0,0 L8,4 L0,8 z" style="fill:var({c})"/>').replace("{c}", c)
        return (f'<marker id="{mid}-{i}" viewBox="0 0 9 9" refX="7.5" refY="4" markerWidth="8" markerHeight="8" '
                f'orient="auto">{path}</marker>')
    name = M["step"][sc["sid"]].get("name", "")
    H = bottom + 14
    return (f'<svg class="seq" data-sd="" viewBox="0 0 {W:g} {H:g}" role="img" aria-label="{E("The process step " + name + ", its interactions in order")}">'
            f'{STYLE}<defs>{mk("a", "--m-ink2")}{mk("o", "--m-ink2", True)}</defs>'
            f'<rect x="2" y="4" width="{W - 4:g}" height="{H - 8:g}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">{E(name)}</text>{lifelines}{"".join(heads)}{"".join(hits)}{"".join(over)}{body}'
            + (tag[2](12 + cv.text_w(name, FS) + 16, 8) if tag else "") + "</svg>")


def draw_plain(msgs, y, right, one):
    out = []
    for m in msgs:
        s, y = one(m, y, right)
        out.append(s)
    return "".join(out), y


# ---------------------------------------------------------------- the card

def what_happens(M, sc):
    """The readable card's "What happens": each part's activity in this process step, one sentence each, in the
    drawing's order, the part's name in bold, the register's citations taken out."""
    order, _ = order_lifelines(M, sc)
    rank = {x: i for i, x in enumerate(order)}
    out = []
    for p in sorted(sc["rows"], key=lambda p: rank.get(p["subject_id"], len(rank))):
        act = plain(p.get("activity", "")).strip().rstrip(".")
        if act:
            out.append(f'<li><b>{cv.esc(M["subj"][p["subject_id"]].get("name", ""))}</b> {cv.marked(M, act)}.</li>')
    return f'<ol>{"".join(out)}</ol>' if out else ""


def card(M, sc, readable=False):
    """The scenario card. `readable`, for the process step's own page, where the drawing shows every interaction and
    each part's head: "What happens" in the parts' own words in place of the interactions, and no list of where each
    part sits."""
    E = cv.esc

    def nm(x):
        return E(M["subj"][x].get("name", ""))

    def item(m, label=None, num=None):
        """One message; `label` the number shown beside it, `num` its number, which a call under it numbers on from
        as the drawing circles it ("2.1")."""
        sn = f'<span class="sn">{label}</span> ' if label else ""
        lab = f'<code>{E(m["label"])}</code>' if m["op"] else cv.marked(M, m["label"])
        desc = f'; {cv.marked(M, sfv.states_in_prose(M, m["desc"]))}' if m["desc"] and m["desc"] != m["label"] else ""
        if m["kind"] == "found":
            s = f'<b>{nm(m["to"])}</b> receives: {lab}{desc} (sender not recorded)'
        elif m["kind"] == "self" or m["frm"] == m["to"]:
            s = f'<b>{nm(m["frm"])}</b>: {lab}{desc}'
        else:
            s = f'<b>{nm(m["frm"])}</b> → <b>{nm(m["to"])}</b>' + (f": {lab}{desc}" if lab or desc else "")
        if m.get("loop"):
            s += f'. More than once, in the agent\'s own actions {E("; ".join(m["loop"]))}; how many times is {GAP}'
        subs = "".join(item(x, f"{num}.{i}", f"{num}.{i}") if num is not None else item(x)
                       for i, x in enumerate(m.get("sub", []), 1))
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
            else:
                out.append(item(it, lab, mine))
        return "".join(out)

    sid = sc["sid"]

    import stage_flow_views as sfv  # it imports this module; importing it back only here avoids a cycle

    def rows(label, q, vals):  # the answer by the prose renderer, or the gap measure-gaps.csv records, or the placeholder
        vals = list(dict.fromkeys(sfv.states_in_prose(M, v) for v in vals if v))
        if q and not vq.answered(M, q, sid) and vq.said(M, q, sid, None) is not None:
            return [(label, vq.said(M, q, sid, None))]
        if not vals:
            return [(label, GAP)]
        if len(vals) == 1:
            return cv.prose_rows(M, label, vals[0])
        lis = []
        for v in vals:  # ways that differ by move: each its own item, its recovery under it
            body, rec = cv.ps.recovery(v)
            lis.append(f"<li>{cv.prose(M, body)}" + (f"<p>Recovery: {cv.marked(M, rec)}</p>" if rec else "") + "</li>")
        return [(label, "<ul>" + "".join(lis) + "</ul>")]
    # moves one after another start with the first
    trig = [(body or f"what starts it is {GAP}") + (f". The case is in {sfv.state_name(st)}" if st else "")
            for body, st in vq.trigger(M, sc)]
    outcome, prop = vq.right_outcome(M, sid)
    order, ins = order_lifelines(M, sc)
    where = "".join(f"<li>{nm(x)}: {cv.marked(M, where_it_sits(M, x, ins))}</li>" for x in order)
    calls = []
    if readable:
        said = what_happens(M, sc)
        calls.append(("What happens", said or GAP))
    elif sc["items"]:
        calls.append(("Interactions, in order", f'<ol>{items(sc["items"])}</ol>'))
    if sc.get("norec") and not readable:
        calls.append(("Interactions, order not recorded", "<ul>" + "".join(item(m) for m in sc["norec"]) + "</ul>"))
    if sc.get("other"):
        calls.append(("Other recorded calls (order not recorded)", "<ul>" + "".join(item(m) for m in sc["other"]) + "</ul>"))
    gaps = [g[:1].upper() + g[1:] for g in dict.fromkeys(sc.get("gaps", []))]
    dl = (rows("Trigger", "step: trigger", trig)
          + calls
          + rows("Expected outcome", None, [outcome + (" (proposed)" if prop else "")] if outcome else [])
          + rows("If it does not happen", "step: if it does not happen", vq.if_not(M, sc))
          + rows("Timeouts", "step: timeouts", vq.timeouts(M, sc))
          + ([] if readable else [("Where each part sits", f"<ul>{where}</ul>" if where else GAP)])
          + ([("Not in the map yet", "<ul>" + "".join(f"<li><i>{cv.marked(M, g)}</i></li>" for g in gaps) + "</ul>")]
             if gaps else []))
    return '<div class="card"><dl>' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in dl) + "</dl></div>"


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


def block(M, sid):
    """One step's drawing, its card and where it comes from. The drawing needs no key: what is not plain UML is said
    in words on it ("person", "run by someone else", "order not recorded", "sender not recorded")."""
    sc = scenario(M, sid)
    return (f'<div class="seqfig">{drawing(M, sc, "sq" + re.sub(r"[^A-Za-z0-9]", "_", sid))}</div>'
            f"{card(M, sc)}{sources(M, sc)}")
