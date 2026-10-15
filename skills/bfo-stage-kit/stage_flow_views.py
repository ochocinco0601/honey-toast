"""How a case moves: through one stage, and through a flow end to end. Drawn from the register.

    python -I stage_flow_views.py REGISTER OUT.html [STAGE_OR_FLOW_ID ...]

`block(M, stage_id, docs)` is a stage's panel content and `flow_block(M, flow_id, docs)` a flow's, for a page that
has already numbered its steps. Read from the register only:
- lifecycle.csv: each move's from and to state, its path (main or not) and whether it can be undone;
- steps.csv: the moves each process step makes (its `source`), so a stage's moves are its own steps' moves;
- stages.csv and flows.csv: entry, case, start, end, whom it serves, what it delivers, and the time limit in the code
  where the code sets one (an optional column, shown only where it is filled);
- case-attributes.csv: what is at stake for a case; measures.csv: the measures proposed for alerting.
A stage is drawn as a BPMN 2.0.2 sub-process of its flow, from stages, steps, lifecycle and participation: the flow is the pool and its customer a closed pool; the stages before and after are folded; the steps
that leave the case in the stage are an ad-hoc sub-process; the ways out are a decision sub-process ending in events
named by the state each leaves the case in, with an error boundary back to the work where a move can strand the case;
moves any role can make at any time are event sub-processes, and the stage's time limit in the code, where it sets
one, a non-interrupting timer. A gateway after the stage routes on how it ended. Business roles head their tasks; the
parts and any AI agent are left to each step's sequence diagram. A
flow is drawn as its stages left to right in order, each with the time limit its code sets where it sets one, joined by the moves the register records
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
import view_questions as vq  # noqa: E402

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

def tail_words(texts):
    """What tells each of several moves apart: the words after the prefix they all share."""
    if len(texts) < 2:
        return texts
    split = [t.split() for t in texts]
    n = 0
    while all(len(s) > n for s in split) and len({s[n] for s in split}) == 1:
        n += 1
    return [" ".join(s[n:]) or t for s, t in zip(split, texts)]


def on_label(M, sid):
    """A process step's short label for a measures table's On column: its own label ("Process step 2.1",
    "Expected outcome"), except that an other outcome is named by the state it ends the case in and the words that
    tell its way out from the stage's others to that state ("Cancelled: because payment failed"), the flow drawing's
    rule for its ways out, so several other outcomes of one stage read apart."""
    label = M.get("_step_label", {}).get(sid) or cv.step_title(M, sid).split(":")[0]
    if label != "Other outcome":
        return label
    stage = M["step"].get(sid, {}).get("stage", "")
    mine = [(s, m) for s, m in exits(M, stage) if m.get("path") != "main"]
    to = next((fo.state(m.get("to_state")) for s, m in mine if s == sid), "")
    if not to:
        return label
    moves = list(dict.fromkeys(m["move"] for s, m in mine if fo.state(m.get("to_state")) == to))
    tail = dict(zip(moves, tail_words(moves)))
    own = next(m["move"] for s, m in mine if s == sid)
    return f"{state_name(to)}: {tail[own]}" if len(moves) > 1 else state_name(to)


def state_name(s):
    """A state as words in sentence case, however the code writes it: IN_REVIEW and in_review read "In review",
    StockConfirmed reads "Stock confirmed", PaymentAPIFailed "Payment API failed". A name already written in words
    is kept as written."""
    s = (s or "").strip()
    if s.replace("_", "").isupper():
        s = s.replace("_", " ").strip()
        return s[:1].upper() + s[1:].lower()
    if " " in s or not re.search(r"_|[a-z0-9][A-Z]", s):
        return s
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", s.replace("_", " ")).split()
    words = [w if len(w) > 1 and w.isupper() else w.lower() for w in words]
    return " ".join([words[0][:1].upper() + words[0][1:]] + words[1:])


def state_in_prose(s):
    """A state's name inside a sentence: its name as `state_name` writes it ("Stock confirmed"), never lower-cased,
    so a reader tells a state from the words around it."""
    return state_name(s)


def states_listed(states):
    """States as a label: each by its name."""
    return or_list([state_name(t) for t in states])


def states_in_prose(M, text):
    """Register prose with each lifecycle state read as its name, whether the prose writes its code form
    (StockConfirmed) or its words in any case (Clear to Close): `state_name`, at the start of the text and inside it.
    A state of one word is matched in its code form or with its capital ("Paid"), never as an ordinary lower-case
    word ("the paid order"); a state of more than one word is matched in any case. A state inside quotes or joined to
    a code name ('Paid', Status.Paid, ORDER_PAID) is a literal in the code and is left as written."""
    known = sorted({fo.state(m.get(k)) for m in moves(M).values() for k in ("from_state", "to_state")} - {"(none)"},
                   key=len, reverse=True)
    if not known or not text:
        return text

    def pattern(s):
        words = state_name(s).split()
        if len(words) == 1:
            return re.escape(s) + "|" + re.escape(words[0][:1].upper() + words[0][1:])
        return re.escape(s) + "|(?i:" + r"\s+".join(map(re.escape, words)) + ")"
    alts = [rf"(?P<s{i}>(?<!['\"._])\b(?:{pattern(s)})\b(?!['\"_]|\.\w))" for i, s in enumerate(known)]
    return re.sub("|".join(alts), lambda m: state_name(known[int(m.lastgroup[1:])]), text)


def tidy(text):
    """Text with a citation taken out: no doubled spaces, no space left before a comma, no trailing comma."""
    return re.sub(r"\s+([,;.])", r"\1", re.sub(r"\s+", " ", text or "")).strip(" ,;.")


def headline(M, text):
    """A register value's lead clause, as the runbook writer reads one: citations out, the part before the first
    colon, steps by their labels, states by their names. A leading `proposed:` comes off before the cut and returns
    as the "(proposed)" mark, so "proposed: a visit is wanted: by phone" reads "a visit is wanted (proposed)"."""
    body, prop = ss.unproposed(text or "")
    t = tidy(fo.strip_parens(body).split(":")[0])
    t = states_in_prose(M, fo.relabel_prose(M["_step_label"], M["R"]["steps"], t))
    return t + (" (proposed)" if prop and t else "")


def bound(M, text):
    """(the time limit's lead, whether it is proposed), or ("", False) where the code sets none (fo.time_limit).
    "proposed: 2 minutes ..." reads as proposed."""
    v = re.sub(r"^\s*none stated\s*;\s*", "", fo.strip_parens(fo.time_limit(text)), flags=re.I).strip()
    if not v:
        return "", False
    body, prop = ss.unproposed(v)
    body = re.split(r"(?<=\w)\.\s+(?=[A-Z])|;\s", tidy(body))[0]
    body = states_in_prose(M, fo.relabel_prose(M["_step_label"], M["R"]["steps"], body))
    return tidy(body), prop


def bound_text(M, text):
    """The time limit in the code as a card prints it, or "" where the code sets none: the column is optional."""
    body, prop = bound(M, text)
    return body + (" (proposed)" if prop else "") if body else ""


def duration(M, text):
    """The time limit's length alone ("2 minutes"), for a box with no room for the rest; "" where the code sets none."""
    body, prop = bound(M, text)
    m = re.search(r"\d+(?:\s*[-–]\s*\d+)?\s+(?:business\s+)?(?:seconds?|secs?|s|minutes?|mins?|hours?|days?|weeks?|"
                  r"months?)\b", body)
    if not body:
        return ""
    return (m.group(0) if m else body) + (" (proposed)" if prop else "")


# ---------------------------------------------------------------- what each party expects

CODE_WORDS = re.compile(r"\S*[/\\]\S*|\b\w+\.(?:py|cs|cshtml|razor|ts|tsx|js|jsx|java|kt|go|rb|php|html|yaml|yml|json|"
                        r"md|sql|xml|toml|ini|cfg)\b(?::\S*)?|\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b")


def expectations(M):
    """The rows of the register's expectations.csv, or [] where it has none. The table is optional here: a register
    made before it existed still draws, and the check says what is missing."""
    R = M["R"]
    if "expectations" not in R:
        p = R.get("_path")
        R["expectations"] = cv.read_csv(pathlib.Path(p) / "expectations.csv") if p else []
    return R["expectations"]


def plain_said(M, text):
    """(a register value as a reader sees it, whether it is proposed): `proposed:` taken off, citations, file names and
    code names out, steps by their labels, flows and states by their names."""
    body, prop = ss.unproposed(text)
    body = re.sub(r"^\s*asked\s*:\s*", "", body, flags=re.I)
    body = tidy(CODE_WORDS.sub("", ss.plain(body) or ""))
    body = cv.named_flows(M, fo.relabel_prose(M["_step_label"], M["R"]["steps"], body))
    return tidy(states_in_prose(M, body)), prop


def labelled(M, text):
    body, prop = plain_said(M, text)
    return body + (" (proposed)" if prop and body else "")


def party_key(v):
    return tidy(fo.strip_parens(ss.unproposed(v)[0])).lower()


def by_party(M, flow_id, stage_id=""):
    """The expectations of a flow (stage_id blank: of the whole flow) or of one of its stages, the customer's first."""
    f = next((x for x in M["flows"] if x["flow_id"] == flow_id), {})
    c = party_key(f.get("customer", ""))
    rows = [r for r in expectations(M) if (r.get("flow") or "").strip() == flow_id
            and (r.get("stage") or "").strip() == stage_id]
    return sorted(rows, key=lambda r: party_key(r.get("party")) != c)


def possessive(who):
    who = who if who.lower().startswith("the ") else "the " + who
    return who + ("'" if who.endswith("s") else "'s")


def party_line(M, r, limit_text, customer=False):
    """One party's line on a stage card: the expectation, what one case shows when it is met, and the objective with
    its source or "not stated". Where the customer's stated objective and the code's time limit differ, both, as a
    finding; another party's objective (a regulator's notice deadline) bounds something else, so is never set
    against it."""
    P = lambda t: cv.marked(M, t)  # noqa: E731
    who, _ = plain_said(M, r.get("party", ""))
    line = f"<b>{P(labelled(M, r.get('party', '')))}</b>: {P(labelled(M, r.get('expectation', '')) or GAP)}. "
    line += f'<div class="mw">{cv.prose(M, "Met when: " + (labelled(M, r.get("satisfied_when", "")) or GAP) + ".")}</div> '
    obj = plain_said(M, r.get("objective", ""))[0] or (r.get("objective") or "").strip()
    if not obj:
        return line + '<div class="mw">Objective: not stated.</div>'
    src = labelled(M, r.get("objective_source", ""))
    line += f'<div class="mw">Objective: {P(obj)}' + (f", stated by {P(src)}" if src else "") + "."
    code = vq.bound_said(M, limit_text)
    code_body = bound(M, limit_text)[0]
    if customer and code and not code_body.lower().startswith("none") and code_body.lower() != obj.lower():
        line += (f' <b class="warn-state">Finding to check:</b> the code\'s limit is {P(code)}; '
                 f"{P(possessive(who))} stated objective is {P(obj)}.")
    return line + "</div>"


def expectation_cites(rows):
    """The fold's lines for expectation rows: each cell as the register writes it, the row's id left out."""
    E = cv.esc
    return [f'<li>{E(r.get("party", ""))}: {E(r.get("expectation", ""))}; '
            + "; ".join(f"{k}: {E(r.get(k, ''))}" for k in ("satisfied_when", "objective", "objective_source", "source")
                        if (r.get(k) or "").strip()) + "</li>" for r in rows]


def move_said(M, sid, m):
    """A move as the reader sees it: by the step that makes it, and where it takes the case when that step makes more
    than one move."""
    many = len({fo.state(x.get("to_state")) for x in ss.moves_of(M, sid)}) > 1
    return cv.step_title(M, sid) + (f", to {state_in_prose(fo.state(m.get('to_state')))}" if many else "")


# ---------------------------------------------------------------- a stage, as a BPMN sub-process of its flow

def _arrow_defs(mid):
    return (f'<defs><marker id="{mid}" viewBox="0 0 8 8" refX="7.5" refY="4" markerWidth="7" markerHeight="7" '
            'orient="auto"><path d="M0,0 L8,4 L0,8 z" style="fill:var(--g600)"/></marker></defs>')


def performers(M, sid):
    """The business roles that perform a step, by name, in the register's order. The parts that carry it (application
    and technology) are the step's sequence diagram's to show, so they are not named here."""
    out = []
    for p in M["R"].get("participation", []):
        s = M["subj"].get(p.get("subject_id"), {})
        if p.get("step") == sid and p.get("involvement") == "performs" and s.get("band") == "business":
            n = (s.get("name") or "").strip()
            if n and n not in out:
                out.append(n)
    return out


def performed_at_all(M, sid):
    return any(p.get("step") == sid and p.get("involvement") == "performs" for p in M["R"].get("participation", []))


def or_list(xs):
    return ", ".join(xs[:-1]) + " or " + xs[-1] if len(xs) > 1 else "".join(xs)


def leaving(M, stage_id, sid):
    """The step's moves that take a case out of the stage's states."""
    inside = set(inside_states(M, stage_id))
    return [m for m in ss.moves_of(M, sid) if not fo.side_move(m) and fo.state(m.get("to_state")) not in inside]


def stage_parts(M, stage_id):
    """How the stage's steps sit in its BPMN drawing, read from the register alone:
    - work: steps that leave the case in the stage (a move that stays put, a move between two of its states, or no
      move at all), in an ad-hoc sub-process; `chain` holds (a, b) where a's move ends in the state b's move starts from;
    - decision: the ways out a person or the software decides, in the decision sub-process: any step with an
      expected outcome, and any other outcome made by one role from where the work leaves the case;
    - any time: other outcomes any of several roles can make, or that leave from every state of the stage, or that
      wait on the flow's customer, each an event sub-process: started by the customer's message where the move waits
      on the customer, by a condition otherwise;
    - error: whether a decided move can leave the case stranded (`recovery`), drawn as an error boundary back to the
      work; timer: the stage's time limit in the code, or "" where it sets none."""
    inside = inside_states(M, stage_id)
    cust = bool(customer_name(M, stage_id))
    out = {"work": [], "decision": [], "any time": [], "chain": [], "error": False, "timer": ""}
    for sid in steps_of(M, stage_id):
        leave = leaving(M, stage_id, sid)
        if not leave:
            out["work"].append(sid)
            continue
        if any(m.get("path") == "main" for m in leave):
            out["decision"].append(sid)
            continue
        waits = cust and (any((m.get("park_because") or "").strip().lower() == "customer" for m in leave)
                          or customer_performs(M, stage_id, sid))
        froms = {fo.state(m.get("from_state")) for m in leave}
        if waits or len(performers(M, sid)) > 1 or (len(inside) > 1 and set(inside) <= froms):
            out["any time"].append((sid, start_of(M, stage_id, sid)[0]))
        else:
            out["decision"].append(sid)

    out["ladder"] = ladder(M, stage_id, out["decision"], out["work"])
    between = {b for _, _, b in out["ladder"] if b}
    out["work"] = [w for w in out["work"] if w not in between]

    def first_state(sid):
        ms = ss.moves_of(M, sid)
        k = [inside.index(fo.state(m.get("from_state"))) for m in ms if fo.state(m.get("from_state")) in inside]
        return min(k) if k else -1
    out["work"].sort(key=first_state)
    for a in out["work"]:
        for b in out["work"]:
            ends_in = {fo.state(m.get("to_state")) for m in ss.moves_of(M, a) if not fo.side_move(m)}
            starts_at = {fo.state(m.get("from_state")) for m in ss.moves_of(M, b) if not fo.side_move(m)}
            if a != b and ends_in & starts_at & set(inside):
                out["chain"].append((a, b))
    out["error"] = any((m.get("recovery") or "").strip().lower() == "stranded"
                       for sid in out["decision"] for m in leaving(M, stage_id, sid))
    out["timer"] = duration(M, M["stage"][stage_id].get("bound_in_code", ""))
    return out


def work_order(M, stage_id, work):
    """The work steps in the order the register records: where one step's move ends in the state another's starts
    from (the chain), the one before the other; otherwise in steps.csv order, which FILL-STEPS has as the order the
    steps run in."""
    at = {s: k for k, s in enumerate(steps_of(M, stage_id))}
    chain = stage_parts_chain(M, stage_id, work)
    left, out = sorted(work, key=lambda s: at.get(s, 0)), []
    while left:
        free = [s for s in left if not any(b == s and a in left for a, b in chain)] or left[:1]
        out.append(free[0])
        left.remove(free[0])
    return out


def stage_parts_chain(M, stage_id, work):
    inside = set(inside_states(M, stage_id))
    out = []
    for a in work:
        ends_in = {fo.state(m.get("to_state")) for m in ss.moves_of(M, a) if not fo.side_move(m)}
        for b in work:
            starts_at = {fo.state(m.get("from_state")) for m in ss.moves_of(M, b) if not fo.side_move(m)}
            if a != b and ends_in & starts_at & inside:
                out.append((a, b))
    return out


def work_kind(M, work):
    """How the stage's work is drawn: "ad hoc" (~) where a business role performs one of its steps, since only a
    performer can choose the order (BPMN 2.0.2, 10.3.5); "task" for a single step the software does; "sequence"
    for several, one after another."""
    if any(performers(M, s) for s in work):
        return "ad hoc"
    return "task" if len(work) == 1 else "sequence"


def work_title(M, work):
    who = list(dict.fromkeys(n for s in work for n in performers(M, s)))
    return f"{or_list(who)}: work the case, in any order" if who else "Work the case, in this order"


def ladder(M, stage_id, dec, work):
    """[(state, its ways out, the step that moves the case on to the next state, or None for the last)] where the
    stage's decided ways out leave from more than one of its states and lifecycle.csv chains those states through
    steps of the stage: the decision is then taken state by state, in that order. [] where every way out leaves from
    the same state, or the register does not chain them."""
    inside = inside_states(M, stage_id)
    froms = {}
    for sid in dec:
        f = {fo.state(m.get("from_state")) for m in leaving(M, stage_id, sid)}
        if len(f) != 1 or not f <= set(inside):
            return []
        froms[sid] = f.pop()
    states = sorted(set(froms.values()), key=inside.index)
    if len(states) < 2:
        return []
    rungs = []
    for i, st in enumerate(states):
        nxt = None
        if i + 1 < len(states):
            nxt = next((w for w in work if any(fo.state(m.get("from_state")) == st and
                                               fo.state(m.get("to_state")) == states[i + 1] for m in ss.moves_of(M, w))),
                       None)
            if nxt is None:
                return []
        rungs.append((st, [x for x in dec if froms[x] == st], nxt))
    return rungs


def branch_labels(M, stage_id, sids):
    """{step: its branch's label}: the state the way out leaves the case in, in words; where two ways out would read
    the same, each adds what its step's name in the register says that the others' do not ("cancelled: payment
    failed")."""
    base = {x: states_listed(targets(M, stage_id, x)) for x in sids}
    out = dict(base)
    for b in set(base.values()):
        same = [x for x in sids if base[x] == b]
        if len(same) < 2:
            continue
        words = {x: M["step"][x].get("name", "").split() for x in same}
        k = 0
        while all(len(w) > k for w in words.values()) and len({w[k].lower() for w in words.values()}) == 1:
            k += 1
        for x in same:
            rest = " ".join(words[x][k:]) or M["step"][x].get("name", "")
            out[x] = f"{b}: {rest}"
    return out


def started_by(m):
    """A move's optional `started_by` in words, citation and `proposed:` taken off: who starts a move that can happen
    at any time. "" where the register leaves it blank."""
    return tidy(fo.strip_parens(ss.unproposed(m.get("started_by") or "")[0]))


def start_of(M, stage_id, sid):
    """(how an any-time way out starts, the parties it comes from), read from its moves in lifecycle.csv. Where
    `started_by` is filled it decides: a timer or schedule, the software (a condition), or else a message from the
    party it names. Otherwise: "message" where `travels_by` has a person or `carried_by` names a person or role part,
    from those people (or the step's business roles where the move names none); "timer" where `travels_by` has a
    timer; "message" where the move is first carried by a front end or app (`front_end`), from whoever uses it;
    "conditional" otherwise. A register that names no party for a move gets a condition, which is what it
    records."""
    moves_ = leaving(M, stage_id, sid)
    said = list(dict.fromkeys(x for x in (started_by(m) for m in moves_) if x))
    if said:
        if all(re.match(r"(?:an? |the )?(?:timer|schedule)\b", x, re.I) for x in said):
            return "timer", []
        if all(re.match(r"(?:the )?(?:software|system|code)\b", x, re.I) for x in said):
            return "conditional", ["the software"]
        return "message", [x for x in said if not re.match(r"(?:an? |the )?(?:timer|schedule|software|system|code)\b",
                                                           x, re.I)]
    parties = []
    for m in moves_:
        for part in (m.get("carried_by") or "").split(";"):
            ids = part.split()
            s_ = M["subj"].get(ids[0], {}) if ids else {}
            if s_.get("part_kind", "").strip().lower() in ("person", "role") or (
                    s_.get("band") == "business" and s_.get("part_kind", "").strip().lower() not in ("case", "")):
                n = (s_.get("name") or "").strip()
                if n and n not in parties:
                    parties.append(n)
    kinds = [k for m in moves_ for k in re.findall(r"(?:^|;)\s*(\w+)", m.get("travels_by") or "")]
    if parties or "person" in kinds:
        return "message", parties or performers(M, sid)
    if "timer" in kinds:
        return "timer", []
    if front_end(M, stage_id, sid):
        return "message", []
    return "conditional", []


FRONT_END = re.compile(r"\bfront[- ]?ends?\b|\bapps?\b", re.I)


def front_end(M, stage_id, sid):
    """The kind of front end or app an any-time way out is first carried by ("web front end"), or "": a move whose
    first `carried_by` part has such a part_kind starts with a request from whoever uses it. The register does not
    say who that is, so no party is named, and the stage drawing names no application part."""
    for m in leaving(M, stage_id, sid):
        ids = (m.get("carried_by") or "").split(";")[0].split()
        s_ = M["subj"].get(ids[0], {}) if ids else {}
        if FRONT_END.search(s_.get("part_kind") or ""):
            return s_["part_kind"].strip().lower()
    return ""


def from_customer(M, stage_id, sid):
    """Whether an any-time way out is a message from the flow's customer, so its message flow comes from the closed
    pool above the flow."""
    kind, parties = start_of(M, stage_id, sid)
    words = set(re.findall(r"[a-z]+", customer_name(M, stage_id).lower()))
    return kind == "message" and bool(words) and any(name_words(n) <= words for n in parties)


def name_words(n):
    """A party's name as a set of words, its article left out: "the shopper" and "Shopper" are one party."""
    return set(re.findall(r"[a-z]+", n.lower())) - {"the", "a", "an"}


def esp_title(M, stage_id, sid):
    """An event sub-process's title, which sits over its start and says what the start's mark means: a message from
    whom, after how long, or a condition and who checks it."""
    kind, parties = start_of(M, stage_id, sid)
    if kind == "message":
        if from_customer(M, stage_id, sid):
            c = customer_name(M, stage_id)
            return "At any time: a message from " + (c if c.lower().startswith("the ") else "the " + c).lower()
        fe = "" if parties else front_end(M, stage_id, sid)
        if fe:
            return f"At any time: a request from someone using the {fe}"
        return "At any time: a message" + (f" from {or_list([n if n[:1].islower() else n.lower() for n in parties])}"
                                           if parties else ", from whom is not recorded")
    if kind == "timer":
        d = next((x for x in (duration(M, m.get("timing", "")) for m in leaving(M, stage_id, sid)) if x), "")
        return f"At any time: after {d}" if d else "At any time: after a time passes"
    return ("At any time: on a condition the software checks" if parties else
            "At any time: on a condition; who starts it is not recorded")


def customer_performs(M, stage_id, sid):
    """Whether a business role the step's participation names as performing it is the flow's customer."""
    words = set(re.findall(r"[a-z]+", customer_name(M, stage_id).lower()))
    return any(name_words(n) <= words for n in performers(M, sid))


def decider(M, stage_id, dec):
    """(who decides the way out, whether an AI agent proposes it): the business roles that perform the decided ways
    out, and whether an agent's participation in one of them is a decision point."""
    who = list(dict.fromkeys(n for s in dec for n in performers(M, s)))
    agent = any(p.get("step") in dec and (p.get("decision_point") or "").strip().lower().startswith("yes")
                and M["family"](M["subj"].get(p.get("subject_id"), {})) == "agent"
                for p in M["R"].get("participation", []) if p.get("subject_id") in M["subj"])
    return who, agent


def customer_name(M, stage_id):
    f = next((x for x in M["flows"] if x["flow_id"] == M["stage"][stage_id].get("flow", "")), {})
    c = labelled(M, f.get("customer", ""))
    return c[:1].upper() + c[1:]


def case_name(M, stage_id):
    """The case's name, from the business subject the stage's steps act on."""
    ids = [M["step"][s].get("business_subject", "") for s in steps_of(M, stage_id)]
    sid = max(set(ids), key=ids.count) if ids else ""
    return (M["subj"].get(sid) or {}).get("name", "")


# ---------------------------------------------------------------- the measures marked on a drawing
# A stage's drawing and a flow's page mark the same thing the same way: the business measures counted on cases, one
# square per measure in its state under its layer's word, wrapping inside its box; and list them in one table.
MEASURED = ("business health", "business impact")  # the layers counted on cases: is the expectation met, for how many not
SQ, PITCH = 14, 19  # a square, and the distance from one square to the next


def case_measures(M, at):
    """The business measures counted on cases for which `at(m)` holds, each with its layer as the method names it."""
    R = M["R"]
    out = []
    for m in R.get("measures", []):
        layer = cv.layer_of(R, m.get("layer"))
        if m.get("counted_on") == "cases" and layer in MEASURED:
            m = {**m, "layer": layer}
            if at(m):
                out.append(m)
    return out


def stage_measures(M, stage_id):
    """A stage's measures: those at one of its steps, and those on the whole stage."""
    steps = set(steps_of(M, stage_id))
    return case_measures(M, lambda m: m["step"] in steps if m.get("step") else m.get("stage") == stage_id)


def measure_state(m):
    """(class, words): a measure's state as its square and its row say it: exists, proposed or cannot be counted, and
    nothing more: no watched or collected state."""
    if m.get("exists") == "yes":
        return "exists", "exists"
    if m.get("counted_how", "").lower().startswith("not countable"):
        return "nc", "cannot be counted"
    return "proposed", "proposed"


STATE_RANK = {"exists": "0", "proposed": "1", "nc": "2"}  # the State column sorts in the key's order


def square(m, x, y, tip=True):
    """One measure's square at (x, y): filled where it exists, hatched where it is proposed (never an empty box),
    a dashed outline where it cannot be counted."""
    cls, said = measure_state(m)
    t = f"<title>{cv.esc(m.get('measure', ''))}: {said}</title>" if tip else ""
    out = f'<rect x="{x:g}" y="{y:g}" width="{SQ}" height="{SQ}" rx="3" class="dot {cls}">{t}</rect>'
    if cls == "proposed":
        out += (f'<path class="hatch" d="M{x + 1:g},{y + 7:g} L{x + 7:g},{y + 1:g} M{x + 1.5:g},{y + 12.5:g} '
                f'L{x + 12.5:g},{y + 1.5:g} M{x + 7:g},{y + 13:g} L{x + 13:g},{y + 7:g}"/>')
    return out


def key_html():
    """The three states, each its square and its word, for the end of a drawing's heading line."""
    return ('<span class="key">' + "".join(f'<span class="dot {c}"></span> {w}' for c, w in
                                          (("exists", "exists"), ("proposed", "proposed"), ("nc", "cannot be counted")))
            + "</span>")


def state_key(x, y, cls="lb"):
    """The three states, each its square and its word, in a row from (x, y): (svg, width)."""
    out, dx = [], x
    for state, said in (("yes", "exists"), ("", "proposed"), ("nc", "cannot be counted")):
        m = {"exists": state} if state == "yes" else {"counted_how": "not countable"} if state == "nc" else {}
        out.append(square(m, dx, y, tip=False) + f'<text x="{dx + 20:g}" y="{y + 12:g}" class="{cls}" text-anchor="start">{said}</text>')
        dx += 20 + cv.text_w(said, 13) + 22
    return "".join(out), dx - x


BOLD = 1.12  # a bold 13 px word's width against cv.text_w's estimate


def squares_at(ms, empty=True, layers=MEASURED):
    """Where a box's squares start, from its left edge: after the widest layer word it shows, and never before 76."""
    shown = [L for L in layers if empty or any(m["layer"] == L for m in ms)]
    return max([76] + [round(12 + cv.text_w(L.split()[-1].capitalize(), 13) * BOLD + 8) for L in shown])


def layer_rows(ms, x, y, w, empty=True, top=26, row=26, pad=14, word="ml", none="gp", layers=MEASURED):
    """Under each layer's word, one square per measure in its state, wrapping to a new row inside `w`: (svg, height).
    `empty` names a layer with no measure ("none"); without it such a layer is left out. `layers` in their order. The
    squares start after the widest layer word shown (squares_at)."""
    at = squares_at(ms, empty, layers)
    per_row = max(1, int((w - at - 10) // PITCH))
    body, ly, last = [], y + top, y + top
    for layer in layers:
        mine = [m for m in ms if m["layer"] == layer]
        if not mine and not empty:
            continue
        body.append(f'<text x="{x + 12:g}" y="{ly:g}" class="{word}" text-anchor="start">{cv.esc(layer.split()[-1].capitalize())}</text>')
        if not mine:
            body.append(f'<text x="{x + at:g}" y="{ly:g}" class="{none}" text-anchor="start">none</text>')
        for k, m in enumerate(mine):  # a square per measure, at any count
            body.append(square(m, x + at + PITCH * (k % per_row), ly - 12 + PITCH * (k // per_row)))
        last = ly + PITCH * max(0, (len(mine) - 1) // per_row)
        ly = last + row
    return "".join(body), last - y + pad


def rows_width(ms, w, layers=MEASURED, empty=False):
    """The width a box of `layer_rows` needs, at most `w`."""
    at = squares_at(ms, empty, layers)
    per_row = max(1, int((w - at - 10) // PITCH))
    most = max([sum(1 for m in ms if m["layer"] == L) for L in layers] + [1])
    return min(w, at + 10 + PITCH * min(most, per_row))


PILL_W = 164  # a pill's widest, inside a task's box
NONE = "none on record"  # a place with no measure, in plain words


def pill(M, sid):
    """(height, width, draw(x, y) -> svg) of a step's measures pill."""
    return mark_pill(case_measures(M, lambda m: m.get("step") == sid), sid)


def mark_pill(ms, sid, wmax=PILL_W, layers=MEASURED):
    """(height, width, draw(x, y) -> svg) of a pill marking the measures `ms` at the place `sid`: its layers' words
    with a square per measure, or the plain words "none on record" where there is none, with no box (a dashed outline
    is the code of a measure that cannot be counted)."""
    E = cv.esc
    if not ms:
        w, h = 104, 26
        return h, w, lambda x, y: f'<text x="{x + w / 2:g}" y="{y + 18:g}" class="bp-gp" text-anchor="middle">{NONE}</text>'
    w = rows_width(ms, wmax, layers)
    body, h = layer_rows(ms, 0, 0, w, empty=False, top=18, row=21, pad=8, word="bp-ml", none="bp-gp", layers=layers)

    def draw(x, y):
        b, _ = layer_rows(ms, x, y, w, empty=False, top=18, row=21, pad=8, word="bp-ml", none="bp-gp", layers=layers)
        return (f'<g class="mark" data-at="{E(sid)}" tabindex="0"><rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
                f'rx="11" class="mbox"/>{b}</g>')
    return h, w, draw


def guards(M, m):
    """The expectation a measure guards, in the register's words made plain, or ""."""
    r = next((r for r in expectations(M) if m.get("expectation") and r.get("expectation_id") == m.get("expectation")), None)
    return labelled(M, r.get("expectation", "")) if r else ""


def measure_form(M, m):
    """A measure's form, as its row opens to it. Where it counts one call, the call is named here, never in the On
    column, which would widen it many times over."""
    rows = [("Answers", m.get("question_it_answers", "")), ("Kind", m.get("form", "")), ("Counted on", m.get("counted_on", "")),
            ("On its call", m.get("operation", "")), ("Counted how", m.get("counted_how", "")),
            ("Exists today", "yes" if m.get("exists") == "yes" else "no"), ("Expectation it guards", guards(M, m)),
            ("Taken from", m.get("taken_from", ""))]
    return "<dl>" + "".join(f"<dt>{a}</dt><dd>{cv.prose(M, states_in_prose(M, no_measure_ids(M, b)))}</dd>"
                            for a, b in rows if b) + "</dl>"


MEASURE_IDS = re.compile(r"\s*\(\s*M\d+(?:\s*(?:,|;|and|or)\s*M\d+)*\s*\)")


def no_measure_ids(M, text):
    """A form value with the register's measure ids taken out: an id in brackets goes, with its brackets; an id in the
    words reads as that measure's name, in quotes; a word of that shape that is no measure's id stays."""
    names = {m.get("handle"): m.get("measure", "") for m in M["R"].get("measures", []) if m.get("handle")}
    text = MEASURE_IDS.sub("", text or "")
    return re.sub(r"\bM\d+\b", lambda mo: f"\u201c{names[mo.group(0)]}\u201d" if names.get(mo.group(0)) else mo.group(0),
                  text)


COLS = ("Layer", "Measure", "State", "On", "Alert")
COL_CLASS = ("ly", "mname", "state", "on", "alert")  # set widths, so opening a measure moves no column


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


SEAMS = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[/_.])")  # where a long identifier may break: a hump, after / _ .


def on_cell(text, breaks):
    """The On cell's words, escaped; with `breaks`, a line may break at an identifier's own seams."""
    if not breaks:
        return cv.esc(text)
    return "<wbr>".join(cv.esc(x) for x in SEAMS.split(text))


def measures_table(M, ms, where, order, link=lambda m: "", layers=MEASURED, stay=False, on_max=None, on_break=False):
    """The measures as one spreadsheet-style table: Layer, Measure, State, On, Alert, every column sorting on a click
    of its name and filtering from a checklist of its values (TABLE_JS); in layer order a band heads each layer with
    its question, and inside it the rows run in the drawing's order, the page's own place first. `where(m)` is (the
    place a mark filters by, its short label for the On column, its full name, the cell's title and the filter's
    value); `order(m)` sorts the places; `link(m)` is a page the On cell opens, or "". While a filter is set, a line
    above the table says how many show, with Clear filters. `layers` are the bands, in order; `stay` keeps the page
    where it is when a mark is picked, for a page whose panel opens beside the drawing. `on_max` caps the On column's
    width, and `on_break` lets its words wrap, breaking a long identifier at its seams."""
    E = cv.esc
    question = {r["layer"]: r["question_it_asks"] for r in M["R"]["method"]["layers"]}
    ms = sorted(ms, key=order)
    rank = {}
    for m in ms:
        rank.setdefault(where(m)[0], len(rank))
    trs = []
    on_w = max([160] + [round(len(where(m)[1]) * 6.2) + 24 for m in ms])  # the On column holds its longest label on one line at 14px
    on_w = min(on_w, on_max) if on_max else on_w
    for li, layer in enumerate(layers):
        word = layer.capitalize()
        mine = [m for m in ms if m["layer"] == layer]
        said = "" if mine else '<span class="bnil">No measure on record</span>'
        trs.append(f'<tr class="band" data-layer="{E(word)}" data-ly="{slug(layer)}"><th colspan="5"><span class="lname">'
                   f'{E(word)}</span><span class="lq">{E(question.get(layer, ""))}</span>'
                   + (f'<div class="bnote">{said}</div>' if said else "") + "</th></tr>")
        for m in mine:
            at, on, full = where(m)
            cls, state = measure_state(m)
            alert = "proposed" if m.get("alert", "").startswith("yes") else "none"
            name = " ".join(m.get("measure", "").split())
            vals = (word, name, state, full, alert)
            keys = (f"{li:02d}", name.lower(), STATE_RANK[cls], f"{rank[at]:04d}", alert)
            href = link(m)
            trs.append(f'<tr class="mrow" data-at="{E(at)}" data-ly="{slug(layer)}" '
                       + " ".join(f'data-v{i}="{E(v)}" data-k{i}="{E(k)}"' for i, (v, k) in enumerate(zip(vals, keys)))
                       + f'><td class="ly">{E(word)}</td><td class="mname"><button type="button" class="mopen" '
                       f'aria-expanded="false">{E(name)}</button>'
                       + f'</td><td class="state nw"><span class="dot {cls}"></span> {E(state)}</td>'
                       + (f'<td class="on{" wraps" if on_break else ""}"><a href="{E(href)}" title="{E(full)}">{on_cell(on, on_break)}</a></td>'
                          if href else f'<td class="on{" wraps" if on_break else ""}"><span title="{E(full)}">{on_cell(on, on_break)}</span></td>')
                       + f'<td class="alert">{alert}</td></tr>'
                       f'<tr class="mform" hidden><td colspan="5">{measure_form(M, m)}</td></tr>')
    head = "".join(f'<th data-c="{i}"><button type="button" class="sort">{c}<span class="ar"></span></button>'
                   f'<button type="button" class="fbtn" aria-label="Filter {c}">▾</button></th>' for i, c in enumerate(COLS))
    return ('<p class="shown" hidden><span class="which"></span> <button type="button" class="all">Clear filters</button></p>'
            '<table class="mtable xl"' + (' data-stay="1"' if stay else "") + '><colgroup>' + "".join(f'<col class="{c}" style="width:{on_w}px">' if c == "on" else f'<col class="{c}">'
                                                     for c in COL_CLASS) + '</colgroup>'
            f'<thead><tr>{head}</tr></thead><tbody>' + "".join(trs) + "</tbody></table>")


MEASURE_CSS = """
svg .mark{cursor:pointer;outline:none}
svg .mark .mbox{fill:var(--m-col);stroke:var(--m-line);stroke-width:1.2}
svg .mark .mnone{fill:var(--m-col);stroke:var(--m-bus-s);stroke-width:1.2;stroke-dasharray:3 4}
svg .mark:hover .mbox,svg .mark:focus-visible .mbox,svg .mark.on .mbox,
svg .mark:hover .mnone,svg .mark:focus-visible .mnone,svg .mark.on .mnone{stroke:var(--m-acc);stroke-width:2.5}
svg rect.dot.exists{fill:var(--m-ok);stroke:none}
svg rect.dot.proposed{fill:var(--m-col);stroke:var(--m-ink2);stroke-width:1.4}
svg path.hatch{stroke:var(--m-ink2);stroke-width:1.4;fill:none;pointer-events:none}
svg rect.dot.nc{fill:none;stroke:var(--m-bus-s);stroke-width:1.6;stroke-dasharray:3 2}
span.dot{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;box-sizing:border-box}
span.dot.exists{background:var(--m-ok)}span.dot.nc{border:2px dashed var(--m-bus-s)}
span.dot.proposed{border:1.5px solid var(--m-ink2);background:repeating-linear-gradient(-45deg,var(--m-ink2) 0 1.4px,transparent 1.4px 4px)}
table.mtable{width:100%;border-collapse:collapse;background:var(--m-col);border:1px solid var(--m-line);font-size:14px}
.mtable th,.mtable td{text-align:left;padding:2px 10px;line-height:1.35;border-bottom:1px solid rgba(127,127,127,.28);vertical-align:top}
.mtable thead th{font-size:13px;color:var(--m-ink2);white-space:nowrap;position:relative}
.mtable.xl thead th button{font:inherit;font-weight:700;background:none;border:0;color:inherit;cursor:pointer;padding:0 2px}
.mtable.xl thead th.filtered .fbtn{color:var(--m-acc)}
.mtable [data-ly^="business"]{--ly:var(--m-bus-s)}.mtable [data-ly="application"]{--ly:var(--m-app-s)}
.mtable [data-ly="agentic"]{--ly:var(--m-agt-s)}.mtable [data-ly="technology"]{--ly:var(--m-tec-s)}
.mtable [data-ly="people"]{--ly:var(--m-per-s)}
.mtable tr.band th{background:color-mix(in srgb,var(--ly,var(--m-line)) 16%,var(--m-col));border-left:6px solid var(--ly,var(--m-line));
border-top:2px solid var(--ly,var(--m-line));padding:6px 10px 4px;font-size:15px}
.mtable tr.band .lname{font-weight:800}.mtable tr.band .lq{font-weight:400;color:var(--m-ink2);margin-left:12px;font-size:14px}
.mtable .bnote{font-weight:400;font-size:13.5px;font-style:italic;color:var(--m-ink2);margin-top:2px}
.mtable tr.mrow td.ly{font-size:13px;color:var(--m-ink2);border-left:6px solid var(--ly,var(--m-line))}
.mtable tr.mrow[data-ly$="impact"] td.ly,.mtable tr.band[data-ly$="impact"] th{border-left-style:double}
table.mtable.xl{table-layout:fixed}
.mtable td.nw,.mtable td.on{white-space:nowrap}.mtable col.ly{width:130px}.mtable col.state{width:140px}.mtable col.on{width:240px}.mtable col.alert{width:90px}
.mtable td{overflow-wrap:anywhere}.mtable td.on.wraps{white-space:normal}
.mtable .mopen{font:inherit;font-weight:600;color:inherit;background:none;border:0;padding:0;margin:0;text-align:left;cursor:pointer}
.mtable .mopen::before{content:"\\25B8\\00a0"}.mtable .mopen[aria-expanded="true"]::before{content:"\\25BE\\00a0"}
.mtable tr.mform td{background:var(--m-page);padding:4px 10px 8px 140px}
.mtable dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 12px;margin:8px 0 2px;font-size:13.5px;color:var(--m-ink2)}
.mtable dt{font-weight:700}.mtable dd{margin:0;overflow-wrap:anywhere}
.xlpop{position:absolute;top:100%;left:0;z-index:5;min-width:240px;max-width:420px;max-height:320px;overflow:auto;background:var(--m-col);
color:var(--m-ink);border:1px solid var(--m-line);border-radius:8px;padding:8px 10px;font-size:14px;font-weight:400;
letter-spacing:0;text-transform:none;box-shadow:0 6px 18px rgba(0,0,0,.35)}
.xlpop label{display:block;margin:3px 0;white-space:normal}.xlbtns{display:flex;gap:8px;margin-top:8px}
.xlpop .xlbtns button{font:inherit;border:1px solid var(--m-line);border-radius:6px;padding:2px 10px;background:var(--m-page);color:var(--m-ink);cursor:pointer}
p.shown{margin:0 0 8px;font-size:15px;font-weight:600;scroll-margin-top:12px}
p.shown button{font:inherit;font-size:14px;margin-left:10px;padding:3px 12px;border-radius:999px;border:1px solid var(--m-line);background:var(--m-col);color:var(--m-ink);cursor:pointer}
p.shown[hidden]{display:none}
h2.sec .key{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:13px;font-weight:400;color:var(--m-ink2)}
h2.sec .key .dot{margin-left:8px}
"""

TABLE_JS = """<script>
(function () {  // the measures, spreadsheet style: a column's name sorts it, its arrow filters it from a checklist of its
  // values; in layer order a band heads each layer; a mark picked on the drawing filters to its place, as one filter
  var t = document.querySelector('table.mtable.xl'), shown = document.querySelector('p.shown'); if (!t || !shown) return;
  var body = t.tBodies[0], heads = t.tHead.rows[0].cells, ncol = heads.length;
  var rows = [].slice.call(body.querySelectorAll('tr.mrow')), bands = [].slice.call(body.querySelectorAll('tr.band'));
  var named = document.getElementById('lane-names'), NAMES = named ? JSON.parse(named.textContent) : {};
  var marks = document.querySelectorAll('svg .mark'), keep = [], place = null, sortCol = -1, dir = 1, pop = null;
  for (var i = 0; i < ncol; i++) keep.push(null);  // null: every value shown
  rows.forEach(function (r) {  // a measure's form sits in the row below it, full width, so opening it moves no column
    var f = r.nextElementSibling, b = r.querySelector('.mopen'); r.form = f;
    if (b) b.addEventListener('click', function () {
      var open = b.getAttribute('aria-expanded') !== 'true'; b.setAttribute('aria-expanded', open); f.hidden = !open;
    });
  });
  function put(r) {
    body.appendChild(r); body.appendChild(r.form);
    if (r.hidden) r.form.hidden = true;
    else r.form.hidden = r.querySelector('.mopen').getAttribute('aria-expanded') !== 'true';
  }
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); }
  function filtered() { return !!place || keep.some(function (k) { return k; }); }
  function render() {
    var any = filtered();
    if (sortCol <= 0) {
      bands.forEach(function (b) {
        body.appendChild(b);
        var mine = rows.filter(function (r) { return r.dataset.v0 === b.dataset.layer; });
        mine.forEach(put);
        b.hidden = any && !mine.some(function (r) { return !r.hidden; });
      });
    } else {
      bands.forEach(function (b) { b.hidden = true; });
      rows.forEach(put);
    }
  }
  function apply() {
    var n = 0;
    rows.forEach(function (r) {
      var ok = !place || r.dataset.at === place;
      for (var c = 0; c < ncol; c++) if (keep[c] && keep[c].indexOf(r.dataset['v' + c]) < 0) ok = false;
      r.hidden = !ok; if (ok) n++;
    });
    shown.querySelector('.which').textContent = (place && NAMES[place] ? NAMES[place] + ': ' : '') + n + ' of ' + rows.length + ' measures shown';
    shown.hidden = !filtered();
    marks.forEach(function (g) { g.classList.toggle('on', g.dataset.at === place); });
    [].forEach.call(heads, function (th, c) { th.classList.toggle('filtered', !!keep[c]); });
    render();
  }
  function sortBy(c) {
    dir = sortCol === c ? -dir : 1; sortCol = c;
    rows.sort(function (a, b) { var x = a.dataset['k' + c], y = b.dataset['k' + c]; return (x < y ? -1 : x > y ? 1 : 0) * dir; });
    [].forEach.call(heads, function (th, i) { th.querySelector('.ar').textContent = i === c ? (dir > 0 ? ' \\u25B2' : ' \\u25BC') : ''; });
    render();
  }
  function values(c) {
    var seen = {}, out = [];
    rows.forEach(function (r) { var v = r.dataset['v' + c]; if (!(v in seen)) { seen[v] = r.dataset['k' + c]; out.push(v); } });
    return out.sort(function (a, b) { return seen[a] < seen[b] ? -1 : seen[a] > seen[b] ? 1 : 0; });
  }
  function close() { if (pop) { pop.remove(); pop = null; } }
  function openFilter(th, c) {
    close();
    var vals = values(c), sel = keep[c] || vals.slice();
    pop = document.createElement('div'); pop.className = 'xlpop';
    pop.innerHTML = '<label class="every"><input type="checkbox"' + (sel.length === vals.length ? ' checked' : '') + '> (Select all)</label>'
      + vals.map(function (v) { return '<label><input type="checkbox" value="' + esc(v) + '"' + (sel.indexOf(v) >= 0 ? ' checked' : '') + '> ' + esc(v) + '</label>'; }).join('')
      + '<div class="xlbtns"><button type="button" class="ok">OK</button><button type="button" class="cancel">Cancel</button></div>';
    th.appendChild(pop);
    var every = pop.querySelector('.every input'), boxes = pop.querySelectorAll('label:not(.every) input');
    every.addEventListener('change', function () { boxes.forEach(function (b) { b.checked = every.checked; }); });
    pop.querySelector('.ok').addEventListener('click', function (e) {
      e.stopPropagation();
      var on = []; boxes.forEach(function (b) { if (b.checked) on.push(b.value); });
      keep[c] = on.length === vals.length ? null : on; close(); apply();
    });
    pop.querySelector('.cancel').addEventListener('click', function (e) { e.stopPropagation(); close(); });
    pop.addEventListener('click', function (e) { e.stopPropagation(); });
  }
  [].forEach.call(heads, function (th, c) {
    th.querySelector('.sort').addEventListener('click', function () { sortBy(c); });
    th.querySelector('.fbtn').addEventListener('click', function (e) { e.stopPropagation(); openFilter(th, c); });
  });
  document.addEventListener('click', close);
  shown.querySelector('button.all').addEventListener('click', function () { for (var c = 0; c < ncol; c++) keep[c] = null; place = null; apply(); });
  function pick(at) {
    place = place === at ? null : at; apply();
    if (place && !t.dataset.stay) shown.scrollIntoView({behavior: 'smooth', block: 'start'});
  }
  marks.forEach(function (g) {
    g.addEventListener('click', function () { pick(g.dataset.at); });
    g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(g.dataset.at); } });
  });
  apply();
})();
</script>"""


def names_json(names):
    """The places marks filter by, named, for TABLE_JS."""
    import json
    return f'<script type="application/json" id="lane-names">{json.dumps(names).replace("</", "<" + chr(92) + "/")}</script>'


def end_label(M, stage_id, sid, t):
    """An end event's name: the state the case is left in, in words, and whether the move cannot be undone."""
    irr = any((m.get("irreversible") or "").strip().lower().startswith("yes")
              for m in leaving(M, stage_id, sid) if fo.state(m.get("to_state")) == t)
    return state_name(t) + ("; cannot be undone" if irr else "")


def targets(M, stage_id, sid):
    return list(dict.fromkeys(fo.state(m.get("to_state")) for m in leaving(M, stage_id, sid)))


FS, HF, LH, LP, TW = 14.5, 13, 18, 16, 180   # a task's name, a label or header, and their line heights
TF, STF = 15.5, 20  # a sub-process's title, the stage's title
CAP = 1200   # the column a stage's drawing fits, drawn at its natural size and never scaled to fit
ENDW = 140   # an end event's label
LABW = 124   # a branch's label


def _r(v):
    return round(v * 2) / 2


def lines(text, width, fs=HF):
    """Text wrapped to a width, whole: a drawing never cuts a word off with an ellipsis; its box grows instead."""
    return cv.wrap(text, width, fs, 10 ** 6)


class _Svg:
    """The marks of one BPMN drawing, written to a list. Coordinates are kept to half units, so a boundary event's centre
    and its box's edge compare equal."""

    def __init__(self, mid):
        self.p, self.mid, self.late = [], mid, []
        self.link = None  # sid -> a process step's own page, or "": its task opens it
        self.marks = set()  # the marks drawn with no words beside them to say what they are: the key's entries

    def add(self, s):
        self.p.append(s)

    def text(self, x, y, lines, cls, anchor="start", lh=LH):
        E = cv.esc
        for i, ln in enumerate(lines):
            self.p.append(f'<text x="{x:g}" y="{y + i * lh:g}" class="{cls}" text-anchor="{anchor}">{E(ln)}</text>')

    def flow(self, pts, main=False, extra=""):
        d = "M" + " L".join(f"{x:g},{y:g}" for x, y in pts)
        self.p.append(f'<path class="bp-seq{" main" if main else ""}"{extra} d="{d}" marker-end="url(#{self.mid}a)"/>')

    def assoc(self, pts):
        d = "M" + " L".join(f"{x:g},{y:g}" for x, y in pts)
        self.p.append(f'<path class="bp-assoc" d="{d}" marker-end="url(#{self.mid}o)"/>')

    def message(self, pts):
        d = "M" + " L".join(f"{x:g},{y:g}" for x, y in pts)
        x0, y0 = pts[0]
        self.p.append(f'<circle cx="{x0:g}" cy="{y0 + 4:g}" r="3.5" class="bp-msgstart"/>'
                      f'<path class="bp-msg" d="{d}" marker-end="url(#{self.mid}o)"/>')

    def gateway(self, cx, cy, r=20, after=False, state=None):
        k = r * 0.38
        tail = ' data-after="yes"' if after else (f' data-state="{cv.esc(state)}"' if state is not None else "")
        self.p.append(f'<g class="bp-gateway"{tail}>'
                      f'<path class="bp-gw" d="M{cx:g},{cy - r:g} L{cx + r:g},{cy:g} L{cx:g},{cy + r:g} L{cx - r:g},{cy:g} Z"/>'
                      f'<path class="bp-gwx" d="M{cx - k:g},{cy - k:g} L{cx + k:g},{cy + k:g} M{cx + k:g},{cy - k:g} '
                      f'L{cx - k:g},{cy + k:g}"/></g>')

    def glyph(self, cx, cy, kind):
        if kind == "message":
            return (f'<rect class="bp-glyph" x="{cx - 6.5:g}" y="{cy - 4.5:g}" width="13" height="9"/>'
                    f'<path class="bp-glyph" d="M{cx - 6.5:g},{cy - 4.5:g} L{cx:g},{cy + 0.5:g} L{cx + 6.5:g},{cy - 4.5:g}"/>')
        if kind == "timer":
            return (f'<circle class="bp-glyph" cx="{cx:g}" cy="{cy:g}" r="7"/>'
                    f'<path class="bp-glyph" d="M{cx:g},{cy - 5:g} L{cx:g},{cy:g} L{cx + 3.5:g},{cy + 1.5:g}"/>')
        if kind == "conditional":
            return (f'<rect class="bp-glyph" x="{cx - 5:g}" y="{cy - 6.5:g}" width="10" height="13"/>'
                    + "".join(f'<path class="bp-glyph" d="M{cx - 3:g},{cy - 3 + i * 3:g} L{cx + 3:g},{cy - 3 + i * 3:g}"/>'
                              for i in range(3)))
        if kind == "error":
            return (f'<path class="bp-glyph" d="M{cx - 5:g},{cy + 5:g} L{cx - 2:g},{cy - 5:g} L{cx + 1.5:g},{cy + 1:g} '
                    f'L{cx + 5:g},{cy - 5:g} L{cx + 2:g},{cy + 5:g} L{cx - 1.5:g},{cy - 1:g} Z"/>')
        return ""

    def start(self, cx, cy, trigger=None, interrupting=True):
        if trigger:
            self.p.append(f'<g class="bp-start" data-trigger="{trigger}" data-interrupting="{"yes" if interrupting else "no"}">'
                          f'<circle class="bp-ev{"" if interrupting else " ni"}" cx="{cx:g}" cy="{cy:g}" r="14"/>'
                          f'{self.glyph(cx, cy, trigger)}</g>')
        else:
            self.marks.add("start")
            self.p.append(f'<circle class="bp-ev" cx="{cx:g}" cy="{cy:g}" r="14"/>')

    def end(self, cx, cy, state=None, label=None, lw=ENDW):
        E = cv.esc
        ls = lines(label, lw) if label else []
        if not ls:
            self.marks.add("end")
        y0 = cy + 5 - (len(ls) - 1) * LP / 2
        body = (f'<circle class="bp-evend" cx="{cx:g}" cy="{cy:g}" r="14"/>'
                + "".join(f'<text x="{cx + 20:g}" y="{y0 + i * LP:g}" class="bp-l">{E(ln)}</text>'
                          for i, ln in enumerate(ls)))
        self.p.append(f'<g class="bp-end" data-state="{E(state)}">{body}</g>' if state else body)
        return cx + 20 + (max(cv.text_w(ln, HF) for ln in ls) if ls else 0)

    def boundary(self, cx, cy, on):
        self.p.append(f'<g class="bp-boundary" data-kind="error" data-on="{on}"><circle cx="{cx:g}" cy="{cy:g}" r="14" '
                      f'class="bp-ev"/><circle cx="{cx:g}" cy="{cy:g}" r="10.5" class="bp-ev"/>{self.glyph(cx, cy, "error")}'
                      '</g>')


def task_lines(M, sid):
    """(header lines, name lines, height) of a step's task: the header is its label and who performs it."""
    who = performers(M, sid)
    label = M.get("_step_label", {}).get(sid, sid)
    head = f"{label} · {or_list(who)}" if who else (f"{label} · by the software" if performed_at_all(M, sid) else label)
    hl = lines(head, TW - 16)
    nl = lines(M["step"][sid].get("name", ""), TW - 16, FS)
    return hl, nl, _r(max(66, 14 + LP * len(hl) + 4 + LH * len(nl) + 6) + pill(M, sid)[0] + 8)


def draw_task(S, M, sid, x, y, where):
    E = cv.esc
    hl, nl, h = task_lines(M, sid)
    tip = cv.step_title(M, sid)
    to = S.link(sid) if S.link else ""
    S.add((f'<a href="{E(to)}">' if to else "") + f'<g class="bp-task" data-act="{E(sid)}" data-in="{where}"><rect class="bp-taskbox" x="{x:g}" y="{y:g}" '
          f'width="{TW}" height="{h:g}" rx="9"/><title>{E(tip)}</title>')
    cx = x + TW / 2
    ph, pw, draw = pill(M, sid)
    words = h - ph - 8  # the box above its pill
    y0 = y + words / 2 - (LP * len(hl) + 4 + LH * len(nl)) / 2 + 12
    S.text(cx, y0, hl, "bp-hd", "middle", LP)
    S.text(cx, y0 + LP * len(hl) + 4, nl, "bp-t", "middle")
    S.add("</g></a>" if to else "</g>")
    S.late.append(draw(_r(cx - pw / 2), y + h - ph - 8))  # drawn last, so no line of the drawing crosses it
    return h


CW, CH = 140, 72  # another stage of the flow, folded


def collapsed_lines(st, w=CW):
    return lines(f'Stage {st.get("order", "")}: {st.get("name", "")}', w - 14, FS)


def collapsed_h(st):
    """A folded stage's height: its name, whole, above its + marker."""
    return max(CH, _r(LH * len(collapsed_lines(st)) + 34))


def draw_collapsed(S, M, st, x, y, w=CW, h=CH):
    E = cv.esc
    S.marks.add("folded")
    ls = collapsed_lines(st, w)
    cx = x + w / 2
    y0 = y + (h - 16) / 2 - (len(ls) - 1) * LH / 2 + 5
    S.add(f'<g class="bp-collapsed" data-stage="{E(st["stage"])}"><rect class="bp-collapsedbox" x="{x:g}" y="{y:g}" '
          f'width="{w}" height="{h:g}" rx="9"/>')
    S.text(cx, y0, ls, "bp-cn", "middle", LH)
    by = y + h - 4
    S.add(f'<rect class="bp-mk" x="{cx - 7:g}" y="{by - 14:g}" width="14" height="14"/>'
          f'<path class="bp-plus" d="M{cx - 4:g},{by - 7:g} L{cx + 4:g},{by - 7:g} M{cx:g},{by - 11:g} L{cx:g},{by - 3:g}"/></g>')


def outcome_block(S, M, stage_id, sid, x, cy, where, main):
    """A way out's task at (x, middle cy), and an end event for each state it leaves the case in, through an exclusive
    gateway where there is more than one. Returns the right-most x used."""
    _, _, h = task_lines(M, sid)
    draw_task(S, M, sid, x, _r(cy - h / 2), where)
    ts = targets(M, stage_id, sid)
    right = x + TW
    if len(ts) == 1:
        S.flow([(right, cy), (right + 30, cy)], main)
        return S.end(right + 44, cy, ts[0], end_label(M, stage_id, sid, ts[0]))
    gx = right + 44
    S.flow([(right, cy), (gx - 20, cy)], main)
    S.gateway(gx, cy)
    far = 0
    for k, t in enumerate(ts):
        ty = cy + (k - (len(ts) - 1) / 2) * 44
        if ty == cy:
            S.flow([(gx + 20, ty), (gx + 66, ty)])
        else:
            S.flow([(gx, cy + (20 if ty > cy else -20)), (gx, ty), (gx + 66, ty)])
        far = max(far, S.end(gx + 80, ty, t, end_label(M, stage_id, sid, t)))
    return far


def outcome_height(M, stage_id, sid):
    return max(task_lines(M, sid)[2], 44 * (len(targets(M, stage_id, sid)) - 1) + 34)


def esp_lines(M, stage_id, sid, w):
    return lines(esp_title(M, stage_id, sid), w - 70, TF)


def esp_size(M, stage_id, sid):
    """(width, height) of an event sub-process: its title, its start, and the way out it makes, sized to its content."""
    w = 78 + TW + (44 if len(targets(M, stage_id, sid)) == 1 else 124) + 20 + ENDW + 14
    return w, outcome_height(M, stage_id, sid) + 62 + 19 * (len(esp_lines(M, stage_id, sid, w)) - 1)


def draw_esp(S, M, stage_id, sid, trigger, x, y, w, h):
    ls = esp_lines(M, stage_id, sid, w)
    S.add(f'<rect class="bp-esp" data-esp="{trigger}" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="12"/>')
    S.text(x + (54 if from_customer(M, stage_id, sid) else 12), y + 20, ls, "bp-title", "start", 19)
    top = 28 + 19 * (len(ls) - 1)
    cy = _r(y + top + (h - top) / 2)
    S.start(x + 30, cy, trigger)
    S.flow([(x + 44, cy), (x + 44 + 34, cy)])
    outcome_block(S, M, stage_id, sid, x + 78, cy, "any time", False)
    return x + 30, cy


def party_in_prose(n):
    """A party's name inside a sentence, its article left off: "Underwriter" reads "underwriter", "QA lead" keeps its
    acronym."""
    w = re.sub(r"^(?:the|an?)\s+", "", (n or "").strip(), flags=re.I).split()
    if not w:
        return ""
    return " ".join([w[0] if len(w[0]) > 1 and w[0].isupper() else w[0].lower()] + w[1:])


def decided_by(M, stage_id, dec):
    """Who decides the way out, as the first gateway's question says it: "Decided by the underwriter, on an AI agent's
    proposal", or "Decided by the software" where no business role performs a decided way out."""
    who, agent = decider(M, stage_id, dec)
    said = "the " + or_list([party_in_prose(n) for n in who]) if who else "the software"
    return f"Decided by {said}" + (", on an AI agent's proposal" if agent else "")


def stack_half(M, stage_id, sids):
    hs = [outcome_height(M, stage_id, x) for x in sids]
    return (sum(hs) + 30 * (len(hs) - 1)) / 2


def label_lines(text):
    return lines(text, LABW)


def rung_drop(M, stage_id, P, i, upto=None):
    """How far below the centre line the first way out of the i-th rung of a ladder sits: clear of the step beside it
    and of the later rungs on the same line (all later rungs, where `upto` does not say where the line ends)."""
    rungs = P["ladder"]
    st, exits, nxt = rungs[i]
    clear = max([task_lines(M, nxt)[2] / 2] + [stack_half(M, stage_id, r[1]) for r in rungs[i + 1:upto]])
    lab = label_lines(branch_labels(M, stage_id, P["decision"])[exits[0]])
    return clear + 14 + LP * len(lab) + 8 + outcome_height(M, stage_id, exits[0]) / 2


def draw_branch_label(S, x, y_bottom, text):
    ls = label_lines(text)
    S.add('<g class="bp-branch">')
    S.text(x, y_bottom - LP * (len(ls) - 1), ls, "bp-fl", "start", LP)
    S.add("</g>")


def draw_stack(S, M, stage_id, sids, gx, MAIN, labels, state=None):
    """An exclusive gateway at (gx, MAIN) and the ways out to its right, one above the other, each branch labelled.
    Returns the right-most x used."""
    mains = [any(m.get("path") == "main" for m in leaving(M, stage_id, x)) for x in sids]
    hs = [outcome_height(M, stage_id, x) for x in sids]
    S.gateway(gx, MAIN, state=state)
    tx = gx + 48 + LABW
    y = MAIN - stack_half(M, stage_id, sids)
    far = tx
    for sid, h, mn in zip(sids, hs, mains):
        yy = _r(y + h / 2)
        if abs(yy - MAIN) < 1:
            S.flow([(gx + 20, yy), (tx, yy)], mn)
            lx = gx + 28
        elif abs(yy - MAIN) < 40:
            S.flow([(gx + 20, MAIN), (gx + 34, MAIN), (gx + 34, yy), (tx, yy)], mn)
            lx = gx + 42
        else:
            S.flow([(gx, MAIN + (20 if yy > MAIN else -20)), (gx, yy), (tx, yy)], mn)
            lx = gx + 8
        draw_branch_label(S, lx, yy - 6, labels[sid])
        far = max(far, outcome_block(S, M, stage_id, sid, tx, yy, "decision", mn))
        y += h + 30
    return far


QGAP = 150    # from one rung's step to the next gateway: room for its question
QGAP0 = 280   # from the decision's start to its first gateway: room for the question that also says who decides


def ask_lines(question, gap=QGAP):
    return lines(question, gap - 30)


ASK_UP = 13  # a question's last line sits this far above the line into its gateway: clear of the arrowhead (7 of the main stroke's 2.4)


def ask(S, gx, MAIN, question, gap=QGAP):
    """A gateway's question, above the line that comes into it, ending short of the diamond."""
    ls = ask_lines(question, gap)
    S.text(gx - 24, MAIN - ASK_UP - LP * (len(ls) - 1), ls, "bp-l", "end", LP)


def rung_question(st):
    return f"In {state_in_prose(st)}: which way out?"


def rung_ask(M, stage_id, P, i):
    """(the i-th rung's question, the gap it is drawn in): the first rung's also says who decides."""
    q = rung_question(P["ladder"][i][0])
    return (f"{q} {decided_by(M, stage_id, P['decision'])}", QGAP0) if i == 0 else (q, QGAP)


def draw_rung(S, M, stage_id, P, labels, i, gx, MAIN, upto=None):
    """The i-th rung of a ladder with its gateway at (gx, MAIN): the question, the gateway, the ways out that leave from
    its state below it, and the step that moves the case on to the next state beside it. Returns (the x where the flow
    on to the next rung leaves, or None for the last rung; the right-most x used; how far below MAIN it reaches)."""
    st, exits, nxt = P["ladder"][i]
    ask(S, gx, MAIN, *rung_ask(M, stage_id, P, i))
    if nxt is None:
        if len(exits) == 1:
            mn = any(m.get("path") == "main" for m in leaving(M, stage_id, exits[0]))
            S.gateway(gx, MAIN, state=st)
            S.flow([(gx + 20, MAIN), (gx + 48 + LABW, MAIN)], mn)
            draw_branch_label(S, gx + 28, MAIN - 6, labels[exits[0]])
            far = outcome_block(S, M, stage_id, exits[0], gx + 48 + LABW, MAIN, "decision", mn)
            return None, far, outcome_height(M, stage_id, exits[0]) / 2
        return None, draw_stack(S, M, stage_id, exits, gx, MAIN, labels, state=st), stack_half(M, stage_id, exits)
    S.gateway(gx, MAIN, state=st)
    bx = gx + 48 + LABW
    S.flow([(gx + 20, MAIN), (bx, MAIN)], True)
    draw_branch_label(S, gx + 28, MAIN - 6, state_name(P["ladder"][i + 1][0]))
    _, _, bh = task_lines(M, nxt)
    draw_task(S, M, nxt, bx, _r(MAIN - bh / 2), "decision")
    far, below = bx + TW, bh / 2
    y = MAIN + rung_drop(M, stage_id, P, i, upto) - outcome_height(M, stage_id, exits[0]) / 2
    for x in exits:
        h = outcome_height(M, stage_id, x)
        yy = _r(y + h / 2)
        mn = any(m.get("path") == "main" for m in leaving(M, stage_id, x))
        S.flow([(gx, MAIN + 20), (gx, yy), (gx + 40, yy)], mn)
        draw_branch_label(S, gx + 8, yy - h / 2 - 8, labels[x])
        far = max(far, outcome_block(S, M, stage_id, x, gx + 40, yy, "decision", mn))
        below = max(below, yy - MAIN + h / 2)
        y += h + 30
    return bx + TW, far, below


def rung_up(M, stage_id, P, i):
    """How far above its centre line the i-th rung of a ladder reaches: its question, the step beside it, or the ways
    out stacked at the last rung."""
    st, exits, nxt = P["ladder"][i]
    q = ASK_UP + LP * (len(ask_lines(*rung_ask(M, stage_id, P, i))) - 1) + HF
    if nxt is not None:
        return max(q, task_lines(M, nxt)[2] / 2)
    return max(q, stack_half(M, stage_id, exits) if len(exits) > 1 else outcome_height(M, stage_id, exits[0]) / 2)


TITLE_UP = 40  # a sub-process's title, above what it holds


def draw_decision(S, M, stage_id, P, DX0, top, xmax):
    """The decision sub-process's content, below its title at `top`: a None start, then, where there is more than one
    way out, an exclusive gateway per state (the first one's question says who decides) the ways out leave from, in the order
    lifecycle.csv chains those states, with the step that moves the case on between them. The chain runs left to
    right; a rung that would pass `xmax` starts a new line below, reached by one connector running back to the left.
    Returns (the right-most x used, the lowest y used)."""
    dec = P["decision"]
    labels = branch_labels(M, stage_id, dec)
    if len(dec) == 1:
        h = outcome_height(M, stage_id, dec[0])
        MAIN = _r(top + TITLE_UP + max(h / 2, 20))
        S.start(DX0 + 26, MAIN)
        mn = any(m.get("path") == "main" for m in leaving(M, stage_id, dec[0]))
        S.flow([(DX0 + 40, MAIN), (DX0 + 64, MAIN)], mn)
        return outcome_block(S, M, stage_id, dec[0], DX0 + 64, MAIN, "decision", mn), MAIN + h / 2
    head = DX0 + 40   # the start's right edge: its flow runs straight to the first gateway

    def draw_head(MAIN):
        S.start(DX0 + 26, MAIN)

    if not P["ladder"]:
        question = f"Which way out? {decided_by(M, stage_id, dec)}"
        q = ASK_UP + LP * (len(ask_lines(question, QGAP0)) - 1) + HF
        MAIN = _r(top + TITLE_UP + max(stack_half(M, stage_id, dec), q))
        draw_head(MAIN)
        gx = head + QGAP0
        S.flow([(head, MAIN), (gx - 20, MAIN)], True)
        froms = {fo.state(m.get("from_state")) for x in dec for m in leaving(M, stage_id, x)}
        ask(S, gx, MAIN, question, QGAP0)
        far = draw_stack(S, M, stage_id, dec, gx, MAIN, labels, state=froms.pop() if len(froms) == 1 else "")
        return far, MAIN + stack_half(M, stage_id, dec)
    # a ladder: measure each rung where it would sit, then break the chain into lines that fit
    rungs = P["ladder"]
    size = []
    for i in range(len(rungs)):
        out, far, below = draw_rung(_Svg("x"), M, stage_id, P, labels, i, 0, 0)
        size.append((out, far, below, rung_up(M, stage_id, P, i)))
    LEAD = DX0 + 20  # where a broken line comes in from the left
    lines, x = [[]], head
    for i, (out, far, below, up) in enumerate(size):
        gx = x + (QGAP0 if i == 0 else QGAP)
        if lines[-1] and gx + far + (24 if out is not None else 0) > xmax:
            lines.append([])
            gx = LEAD + QGAP
        lines[-1].append((i, gx))
        x = gx + out if out is not None else x
    far_all, y, prev = 0, top + TITLE_UP, None
    for k, line in enumerate(lines):
        up = max(size[i][3] for i, _ in line)
        down = 0
        upto = line[-1][0] + 1
        MAIN = _r(y + up)
        if k == 0:
            draw_head(MAIN)
            S.flow([(head, MAIN), (line[0][1] - 20, MAIN)], True)
        else:
            (out0, MAIN0, lane, rx) = prev
            S.flow([(out0, MAIN0), (rx, MAIN0), (rx, lane), (LEAD, lane), (LEAD, MAIN), (line[0][1] - 20, MAIN)], True)
        out_x = None
        line_far = 0
        for j, (i, gx) in enumerate(line):
            if j:
                S.flow([(out_x, MAIN), (gx - 20, MAIN)], True)
            out_x, far, below = draw_rung(S, M, stage_id, P, labels, i, gx, MAIN, upto)
            down = max(down, below)
            line_far = max(line_far, far)
        far_all = max(far_all, line_far)
        bottom = MAIN + down
        if k + 1 < len(lines):
            lane = _r(bottom + 18)
            rx = _r(max(line_far, out_x) + 16)
            prev = (out_x, MAIN, lane, rx)
            far_all = max(far_all, rx)
            y = lane + 30  # clear of a tag above the next line's step
    return far_all, bottom


def after_groups(M, stage_id, P, stages, at):
    """[(key, {"states", "main"})] for where the stage's ways out lead, in the flow's order: the next stages, then the
    end of the flow, then states the register places in no stage."""
    groups = {}
    for sid in P["decision"] + [s for s, _ in P["any time"]]:
        for m in leaving(M, stage_id, sid):
            kind, nxt = leads_to(M, stage_id, m)
            key = ("stage", nxt["stage"]) if kind == "stage" else (kind or "none", None)
            g = groups.setdefault(key, {"states": [], "main": False})
            t = fo.state(m.get("to_state"))
            if t not in g["states"]:
                g["states"].append(t)
            g["main"] |= m.get("path") == "main"
    order = sorted(groups, key=lambda k: (0, at.get(k[1], 0)) if k[0] == "stage" else (1 if k[0] == "end" else 2, 0))
    if not order and stages and stages[-1]["stage"] == stage_id:
        groups[("end", None)] = {"states": [], "main": True}
        order = [("end", None)]
    return [(k, groups[k]) for k in order]


AFTER_W = 110  # a branch's label after the stage


def after_label(k):
    return "The flow ends" if k[0] == "end" else "The register places this state in no stage"


def after_width(k):
    return CW if k[0] == "stage" else 28 + 20 + max(cv.text_w(x, HF) for x in lines(after_label(k), AFTER_W))


def stage_drawing(M, stage_id, cap=CAP, whole=False, link=None):
    """The stage as a BPMN 2.0.2 sub-process of its flow, drawn from the register to fit a column `cap` wide at its
    natural size. The flow is a pool and its customer a closed pool above. A strip across the top holds the stage
    before, folded, flowing into the stage, and at its right the gateway on how the stage ended, with the stages after,
    folded. Inside the stage, row by row: the start and the work, an ad-hoc sub-process with its steps in up to three
    columns; the decided ways out, a sub-process across the stage whose chain breaks onto a new line where it would
    not fit, ending in events named by the state each leaves the case in, with an error boundary back to the work up
    the left margin; and what can happen at any time, event sub-processes side by side, each sized to its content."""
    E = cv.esc
    st = M["stage"][stage_id]
    steps = steps_of(M, stage_id)
    name = f'Stage {st.get("order", "")}: {st.get("name", "")}'
    if not steps:
        return no_moves_drawing(M, stage_id, name)
    mid = "bp" + re.sub(r"[^A-Za-z0-9]", "_", stage_id)
    S = _Svg(mid)
    S.link = link
    P = stage_parts(M, stage_id)
    f = next((x for x in M["flows"] if x["flow_id"] == st.get("flow", "")), {})
    cust = customer_name(M, stage_id)
    inside = inside_states(M, stage_id)
    stages = flow_stages(M, st.get("flow", ""))
    at = {s["stage"]: k for k, s in enumerate(stages)}
    k = at.get(stage_id, 0)
    prev = [stages[k - 1]["stage"]] if k > 0 else []   # the stage before, in the order of stages.csv
    recorded = bool(stage_moves(M, stage_id))         # whether the lifecycle says how a case leaves the stage
    if recorded:
        after = after_groups(M, stage_id, P, stages, at)
    else:  # the stage after, in order; nothing about how this one ends
        after = [(("stage", stages[k + 1]["stage"]), {"states": [], "main": False})] if k + 1 < len(stages) else []

    X0, BAND = 6, 26
    pool = cust and any(from_customer(M, stage_id, s) for s, _ in P["any time"])  # only where a message reaches it
    PT = 56 if pool else 8
    SX0 = X0 + BAND + 14
    SXMAX = cap - 24          # the stage's right edge at most, leaving the pool's margin for a message to come down
    # ---- the strip above the stage: what comes before and after it
    said = [states_listed(g["states"]) for _, g in after]
    lab = [lines(x, AFTER_W) if x else [] for x in said]
    top_room = (30 + 8 + LP * max(len(lab[1]), 1)) if len(after) > 1 else 0
    for j in range(3, len(after)):
        top_room += 22
    bot_room = (24 + 8 + LP * max(len(lab[2]), 1) + 6) if len(after) > 2 else 0
    FH = max([collapsed_h(M["stage"][s]) for s in prev] + [collapsed_h(M["stage"][k[1]]) for k, _ in after
                                                            if k[0] == "stage"] + [CH])  # the folded stages' height
    BOX_T = PT + 16 + top_room
    CY = BOX_T + FH / 2
    BOX_B = BOX_T + FH
    SY0 = BOX_B + max(bot_room, 0) + 26
    gap0 = max(60, (max(cv.text_w(x, HF) for x in lab[0]) if lab and lab[0] else 0) + 40) if len(after) > 1 else 40
    group_w = (50 + 20 + gap0 if len(after) > 1 else 40) + sum(after_width(k) for k, _ in after) + 30 * (len(after) - 1)
    q_lines = lines("How did the stage end?", 90) if len(after) > 1 else []
    prev_w = (len(prev) * (CW + 16)) if prev else 40
    strip_need = 16 + prev_w + 30 + (max(cv.text_w(x, HF) for x in q_lines) + 20 if q_lines else 0) + group_w + 16

    # ---- the stage's title, whole, within the column
    tl = lines(name, SXMAX - SX0 - 32, STF)
    TY = SY0 + 30
    # ---- row 1: the start and the work
    work = work_order(M, stage_id, P["work"])
    wk = work_kind(M, work) if work else ""
    R1 = TY + 26 * (len(tl) - 1) + 16
    CG = 16 if wk == "ad hoc" else 40   # the gap between two steps of the work: room for an arrow where they follow
    ncol = min(3, len(work)) or 1
    grid = [work[i:i + ncol] for i in range(0, len(work), ncol)]
    rowh = [max(task_lines(M, s)[2] for s in r) for r in grid]
    WX0 = SX0 + 150
    if wk == "task":
        WW, WH, wtl, WTOP = TW, rowh[0], [], 0
    else:
        WW = 28 + ncol * TW + (ncol - 1) * CG if work else 0
        wtl = lines(work_title(M, work), WW - 24, TF) if work else []
        WTOP = 40 + 19 * (len(wtl) - 1)   # the box's title, over its steps
        WH = _r(WTOP + sum(rowh) + 26 * (len(grid) - 1) + 30) if work else 0
    MAIN1 = _r(R1 + max(WH / 2, 34))
    dlab = []
    if inside:
        cn = case_name(M, stage_id)
        dlab = lines(f'{cn} [{", ".join(state_name(s) for s in inside)}]' if cn else
                     f'[{", ".join(state_name(s) for s in inside)}]', 120)
    B1 = max(R1 + WH, (MAIN1 + 30 + 50 + LP * (len(dlab) - 1) + 8) if dlab else MAIN1 + 20)
    SEX = (WX0 + WW if work else WX0) + 70  # the stage's end
    unrec = [] if recorded else lines("Its ways out are not recorded.", 150)
    if unrec:
        SEX = (WX0 + WW if work else WX0) + 24 + max(cv.text_w(x, HF) for x in unrec)
    S.start(SX0 + 30, MAIN1)
    if dlab:
        dx, dy = SX0 + 62, MAIN1 + 30
        S.add(f'<path class="bp-dobj" d="M{dx:g},{dy:g} L{dx + 18:g},{dy:g} L{dx + 26:g},{dy + 8:g} L{dx + 26:g},{dy + 34:g} '
              f'L{dx:g},{dy + 34:g} Z M{dx + 18:g},{dy:g} L{dx + 18:g},{dy + 8:g} L{dx + 26:g},{dy + 8:g}"/>')
        S.text(dx + 13, dy + 50, dlab, "bp-l", "middle", LP)
        if work:
            S.assoc([(dx + 26, dy + 17), (WX0, dy + 17)])
    task_at = {}
    if wk == "task":
        draw_task(S, M, work[0], WX0, R1, "work")
        S.flow([(SX0 + 44, MAIN1), (WX0, MAIN1)], True)
    elif work:
        WY0 = R1
        cls = "bp-adhoc" if wk == "ad hoc" else "bp-sub"
        S.add(f'<g class="bp-subg" data-sub="work"><rect class="{cls}" data-sub="work" x="{WX0:g}" y="{WY0:g}" '
              f'width="{WW:g}" height="{WH:g}" rx="12"/>')
        S.text(WX0 + 12, WY0 + 22, wtl, "bp-title", "start", 19)
        ty = WY0 + WTOP
        row_of = {}
        for k, (r, h) in enumerate(zip(grid, rowh)):
            for c, sid in enumerate(r):
                tx = WX0 + 14 + c * (TW + CG)
                th = draw_task(S, M, sid, tx, ty, "work")
                task_at[sid] = (tx, ty, th)
                row_of[sid] = (k, c, ty, ty + h)
            ty += h + 26
        cx = WX0 + WW / 2
        if wk == "ad hoc":
            S.add(f'<path class="bp-tilde" d="M{cx - 9:g},{WY0 + WH - 11:g} q4.5,-7 9,0 t9,0"/>')
        joins = stage_parts_chain(M, stage_id, work) if wk == "ad hoc" else list(zip(work, work[1:]))
        for a, b in joins:
            ax, ay, ah = task_at[a]
            bx, by, bh = task_at[b]
            ra, ca, ta, ba = row_of[a]
            rb, cb, tb, bb = row_of[b]
            if ra == rb and abs(ca - cb) == 1:
                ym = min(ay + ah, by + bh) / 2 + max(ay, by) / 2
                pts = [(ax + TW, ym), (bx, ym)] if bx > ax else [(ax, ym), (bx + TW, ym)]
            elif rb > ra:   # down through the gap under a's row
                g = ba + 13
                pts = [(ax + TW / 2, ay + ah), (ax + TW / 2, g), (bx + TW / 2 + 12, g), (bx + TW / 2 + 12, by)]
            else:           # up through the gap over a's row
                g = ta - 13
                pts = [(ax + TW / 2, ay), (ax + TW / 2, g), (bx + TW / 2 + 12, g), (bx + TW / 2 + 12, by + bh)]
            S.flow([(_r(px), _r(py)) for px, py in pts], True, f' data-from="{E(a)}" data-to="{E(b)}"')
        S.add("</g><!--sub-->")
        S.flow([(SX0 + 44, MAIN1), (WX0, MAIN1)], True)
    dec = P["decision"]
    DY0 = _r(B1 + 44)
    far = SEX + 40
    if dec:
        DX0 = SX0 + 28
        S.add(f'<g class="bp-subg" data-sub="decision"><rect class="bp-sub" data-sub="decision" x="{DX0:g}" y="{DY0:g}" '
              f'width="@DW" height="@DH" rx="12"/>')
        S.text(DX0 + 12, DY0 + 22, ["Decide the way out"], "bp-title")
        dfar, dbot = draw_decision(S, M, stage_id, P, DX0, DY0, SXMAX - 30)
        DH = _r(dbot + 24 - DY0)
        S.p = [x.replace('height="@DH"', f'height="{DH:g}"') for x in S.p]
        S.add("</g><!--sub-->")
        far = max(far, dfar + 30)
        down_x = WX0 + WW - 30 if work else WX0
        if work:
            S.flow([(down_x, R1 + WH), (down_x, DY0)], True)
        else:
            S.flow([(SX0 + 44, MAIN1), (down_x, MAIN1), (down_x, DY0)], True)
        S.flow([(SEX, DY0), (SEX, MAIN1 + 14)], True)
        R3 = DY0 + DH + 30
        if P["error"] and work:
            bx, by = DX0 + 40, DY0 + DH
            low = by + 34
            S.boundary(bx, by, "decision")
            S.flow([(bx, by + 14), (bx, low), (SX0 + 14, low), (SX0 + 14, B1 + 18), (WX0 + 30, B1 + 18),
                    (WX0 + 30, R1 + WH)])
            state = f", still {state_in_prose(inside[0])}" if len(inside) == 1 else ""
            el = lines(f"could not be completed: back to the work{state}", 420)
            S.text(bx + 22, by + 28, el, "bp-fl", "start", LP)
            R3 = low + LP * (len(el) - 1) + 30
    else:
        R3 = B1 + 30
        if unrec:
            S.text((WX0 + WW if work else WX0) + 20, MAIN1 + 5 - LP * (len(unrec) - 1) / 2, unrec, "bp-l", "start", LP)
        elif work:
            S.flow([(WX0 + WW, MAIN1), (SEX - 14, MAIN1)], True)
        else:
            S.flow([(SX0 + 44, MAIN1), (SEX - 14, MAIN1)], True)
    if not unrec:
        S.end(SEX, MAIN1)
    # ---- row 3: what can happen at any time, side by side, wrapping
    items = []
    tm = lines(P["timer"], 300) if P["timer"] else []
    if P["timer"]:
        items.append(("timer", None, "timer", 330, 100 + LP * (len(tm) - 1)))
    conds = [(s, t) for s, t in P["any time"] if not from_customer(M, stage_id, s)]
    msgs = [(s, t) for s, t in P["any time"] if from_customer(M, stage_id, s)]
    for sid, t in conds + msgs:
        w, h = esp_size(M, stage_id, sid)
        items.append(("step", sid, t, w, h))
    placed, x, y, lh_, row_right = [], SX0 + 16, R3, 0, 0
    msg_rows = 0
    for kind, sid, t, w, h in items:
        if x > SX0 + 16 and x + w > SXMAX - 16:
            x, y, lh_ = SX0 + 16, y + lh_ + 34, 0
        placed.append((kind, sid, t, x, y, w, h))
        row_right = max(row_right, x + w)
        x, lh_ = x + w + 16, max(lh_, h)
    bottom = (y + lh_) if items else R3 - 30
    SX1 = _r(max([SX0 + strip_need, far, row_right + 16, SEX + 60]
                 + [SX0 + 32 + cv.text_w(x, STF) for x in tl]))
    SY1 = _r(bottom + 18)
    if dec:
        S.p = [x.replace('width="@DW"', f'width="{SX1 - 16 - (SX0 + 28):g}"') for x in S.p]
    for kind, sid, t, x, yy, w, h in placed:
        if kind == "step":
            sx, sy = draw_esp(S, M, stage_id, sid, t, x, yy, w, h)
            if from_customer(M, stage_id, sid):
                lane = yy - 12 - 8 * msg_rows
                msg_rows += 1
                S.message([(SX1 + 10, PT - 12), (SX1 + 10, lane), (sx, lane), (sx, sy - 15)])
        else:
            S.add(f'<rect class="bp-esp" data-esp="timer" x="{x:g}" y="{yy:g}" width="{w}" height="{h}" rx="12"/>')
            S.text(x + 12, yy + 20, ["Time limit in the code"], "bp-title")
            cy = yy + 58
            S.start(x + 30, cy, "timer", interrupting=False)
            S.text(x + 12, cy + 34, tm, "bp-l", "start", LP)
            S.flow([(x + 44, cy), (x + 96, cy)])
            S.end(x + 110, cy, None, "the case is past its time limit; the stage carries on", 190)
    S.add(f'<rect class="bp-stagebox" x="{SX0:g}" y="{SY0:g}" width="{SX1 - SX0:g}" height="{SY1 - SY0:g}" rx="16"/>')
    S.p.insert(0, S.p.pop())  # the stage's box goes under everything in it
    S.text(SX0 + 16, TY, tl, "bp-stitle", "start", 26)
    if whole:  # the whole stage's measures, as a pill on its title row
        ph, pw, draw = mark_pill([m for m in stage_measures(M, stage_id) if not m.get("step")], "stage", 420)
        S.add(draw(SX1 - 16 - pw, TY - 18))  # at the title row's far end, clear of the first step under the title
    # ---- the strip: before the stage
    if prev:
        for k, s in enumerate(prev):
            px = SX0 + 16 + k * (CW + 16)
            draw_collapsed(S, M, M["stage"][s], px, BOX_T, h=FH)
            S.flow([(px + CW / 2, BOX_B), (px + CW / 2, SY0)], True)
    else:
        fx = SX0 + 40
        S.marks.add("start")
        S.add(f'<g class="bp-flowstart"><circle class="bp-ev" cx="{fx:g}" cy="{CY:g}" r="14"/></g>')
        S.flow([(fx, CY + 14), (fx, SY0)], True)
    # ---- the strip: after the stage, at the top right, a gateway on how it ended
    if after:
        xin = SX1 - 16 - group_w
        if len(after) == 1:
            k, g = after[0]
            tx = xin + 40
            S.flow([(xin, SY0), (xin, CY), (tx, CY)], g["main"])
            targets_x = [tx]
        else:
            GX = xin + 50
            S.flow([(xin, SY0), (xin, CY), (GX - 20, CY)], True)
            S.gateway(GX, CY, after=True)
            S.text(xin - 10, CY - 6 - LP * (len(q_lines) - 1), q_lines, "bp-l", "end", LP)
            targets_x, tx = [], GX + 20 + gap0
            for k, _ in after:
                targets_x.append(tx)
                tx += after_width(k) + 30
        lane_t = BOX_T - 30
        for j, ((k, g), tx) in enumerate(zip(after, targets_x)):
            if k[0] == "stage":
                draw_collapsed(S, M, M["stage"][k[1]], tx, BOX_T, h=FH)
                cx, ent_t, ent_b = tx + CW / 2, BOX_T, BOX_B
            else:
                S.end(tx + 14, CY, None, after_label(k), AFTER_W)
                cx, ent_t, ent_b = tx + 14, CY - 14, CY + 14
            if len(after) == 1:
                continue
            if j == 0:
                S.flow([(GX + 20, CY), (tx, CY)], g["main"])
                if lab[0]:
                    S.text(GX + 28, CY - 6 - LP * (len(lab[0]) - 1), lab[0], "bp-fl", "start", LP)
            elif j == 2:
                lane = BOX_B + 24
                S.flow([(GX, CY + 20), (GX, lane), (cx, lane), (cx, ent_b)], g["main"])
                S.text(GX + 8, lane + 20, lab[j], "bp-fl", "start", LP)
            else:
                lane = lane_t - (22 * (j - 2) if j > 2 else 0)
                S.flow([(GX, CY - 20), (GX, lane), (cx, lane), (cx, ent_t)], g["main"])
                if j == 1:
                    S.text(GX + 8, lane - 8 - LP * (len(lab[j]) - 1), lab[j], "bp-fl", "start", LP)
    W = SX1 + 24
    H = SY1 + 14
    fl = f.get("name", "")
    H = max(H, _r(PT + cv.text_w(fl, HF) * 1.1 + 24))  # the flow's name, whole, up the pool's band
    pools = []
    if pool:
        pools.append(f'<g class="bp-pool closed" data-pool="customer"><rect class="bp-pool" x="{X0}" y="6" '
                     f'width="{W - X0 - 4:g}" height="{PT - 18}"/><text x="{(X0 + W) / 2:g}" y="{6 + (PT - 18) / 2 + 5:g}" '
                     f'class="bp-pn" text-anchor="middle">{E(cust)}</text></g>')
    fy = (PT + H) / 2
    pools.append(f'<g class="bp-pool" data-pool="flow"><rect class="bp-pool" x="{X0}" y="{PT:g}" width="{W - X0 - 4:g}" '
                 f'height="{H - PT:g}"/><line class="bp-pool" x1="{X0 + BAND}" y1="{PT:g}" x2="{X0 + BAND}" y2="{H:g}"/>'
                 f'<text x="{X0 + BAND / 2 + 5:g}" y="{fy:g}" class="bp-pn" text-anchor="middle" '
                 f'transform="rotate(-90 {X0 + BAND / 2 + 5:g} {fy:g})">{E(fl)}</text></g>')
    defs = (f'<defs><marker id="{mid}a" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="bp-head"/></marker>'
            f'<marker id="{mid}o" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="8" markerHeight="8" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" class="bp-heado"/></marker></defs>')
    H += 6
    key, kh = draw_key(S.marks, W, H)
    H += kh
    return (f'<svg class="seq casemoves bpmn" viewBox="0 0 {W:g} {H:g}" style="width:{W:g}px;max-width:none" role="img" '
            f'aria-label="{E(name + ": a business process (BPMN): its work, the ways out, what can happen at any time, and where each leads")}">'
            f'{defs}{"".join(pools)}{"".join(S.p)}{"".join(S.late)}{key}</svg>')


# The key: a few words for each mark the drawing cannot label where it stands. Everything else is said in words on
# the drawing itself: a message's sender, a timer's duration, the ~ box's performer, a gateway's question, the error
# boundary's effect, each end's state.
KEY = {"start": "a case starts here",
       "end": "the stage's work ends here",
       "folded": "another stage of the flow, folded"}


def key_glyph(k, x, cy):
    """(the mark as drawn in the key, its width)."""
    if k == "start":
        return f'<circle class="bp-ev" cx="{x + 10:g}" cy="{cy:g}" r="9"/>', 20
    if k == "end":
        return f'<circle class="bp-evend" cx="{x + 10:g}" cy="{cy:g}" r="9"/>', 20
    if k == "folded":
        return (f'<rect class="bp-collapsedbox" x="{x:g}" y="{cy - 10:g}" width="26" height="20" rx="4"/>'
                f'<rect class="bp-mk" x="{x + 7:g}" y="{cy - 6:g}" width="12" height="12"/>'
                f'<path class="bp-plus" d="M{x + 9.5:g},{cy:g} L{x + 16.5:g},{cy:g} M{x + 13:g},{cy - 3.5:g} L{x + 13:g},{cy + 3.5:g}"/>'), 26
    return "", 0


def draw_key(marks, width, top):
    """(the key under the figure, its height): one entry per mark drawn without words, in KEY's order, set in rows
    that fit `width`. ("", 0) where the drawing labels all it draws."""
    items = [k for k in KEY if k in marks]
    if not items:
        return "", 0
    E = cv.esc
    out, x, row = ['<g class="bp-key">'], 16, 0
    head = "Key:"
    out.append(f'<text x="{x:g}" y="{top + 17:g}" class="bp-hd" text-anchor="start">{head}</text>')
    x += cv.text_w(head, HF) + 20
    for k in items:
        said = KEY[k]
        gw = key_glyph(k, 0, 0)[1]
        w = gw + 8 + cv.text_w(said, HF)
        if x + w > width - 16 and x > 80:
            x, row = 16 + cv.text_w(head, HF) + 20, row + 1
        cy = top + 12 + row * 28
        g, _ = key_glyph(k, x, cy)
        out.append(f'<g class="bp-keyitem" data-key="{k}">{g}<text x="{x + gw + 8:g}" y="{cy + 5:g}" class="bp-l" '
                   f'text-anchor="start">{E(said)}</text></g>')
        x += w + 28
    out.append("</g>")
    return "".join(out), 28 * (row + 1) + 8


def no_moves_drawing(M, stage_id, name):
    """A stage the register gives no steps: nothing to draw but its name."""
    E = cv.esc
    return (f'<svg class="seq casemoves bpmn" viewBox="0 0 {W} 76" style="width:{W}px;max-width:none" role="img" '
            f'aria-label="{E(name)}"><rect x="2" y="4" width="{W - 4}" height="68" class="frame"/>'
            f'<text x="12" y="30" class="bp-stitle" text-anchor="start">{E(name)}</text>'
            '<text x="24" y="58" class="bp-l" text-anchor="start">The register records no process steps for this stage.</text></svg>')


MOVE_IDS = re.compile(r"\s*(?:\b(?:of|in|by|from|at|see)\s+)?\(?\bL\d+\b(?:\s*(?:,|and|or|to|-|–)\s*L\d+\b)*\)?")


def no_move_ids(text):
    """Card text with the register's move ids taken out, with the word that introduced them: "read from the timing of
    L03, L04 and L06: a grace period" reads "read from the timing: a grace period"."""
    return re.sub(r"\s+([,;:.)])", r"\1", MOVE_IDS.sub("", text or "")).strip()


def stage_card(M, stage_id, docs=None):
    E = cv.esc
    st = M["stage"][stage_id]
    ins = vq.stage_enters(M, stage_id)
    main_ = vq.stage_outcomes(M, stage_id, "Expected outcome")
    other = vq.stage_outcomes(M, stage_id, "Other outcome")
    undo = vq.stage_undo(M, stage_id)
    stake = vq.stage_stake(M, stage_id)
    page_ = (docs or {}).get(stage_id, {}).get("Runbook")
    al = [(f'<a href="{E(page_)}#alert-{E(m.get("handle", ""))}">{E(m.get("measure", ""))}</a>' if page_
           else E(m.get("measure", ""))) for m in alerts(M, stage_id)]

    def ul(xs, raw=False):  # each item once, as the reader sees it, broken up by the prose renderer
        xs = list(dict.fromkeys(no_move_ids(x) if raw else cv.prose(M, no_move_ids(x)) for x in xs))
        return "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>" if xs else ""

    def ending(sid):  # an outcome by its step's name, and where it leads
        to = step_leads(M, stage_id, sid)
        return M["step"][sid].get("name", "") + (f" ({to})" if to else "")
    cust = party_key(next((f for f in M["flows"] if f["flow_id"] == st.get("flow", "")), {}).get("customer", ""))
    parties = [party_line(M, r, st.get("bound_in_code", ""), customer=party_key(r.get("party", "")) == cust)
               for r in by_party(M, st.get("flow", ""), stage_id)]
    limit = vq.bound_said(M, st.get("bound_in_code", ""))  # optional: a row only where the code sets one
    rows = [("Time limit in the code", cv.prose(M, no_move_ids(limit)))] if limit else []
    rows += [("Expected by each party", ul(parties, raw=True)
             or vq.said(M, "stage: expected by each party", stage_id, "No expectations recorded")),
            ("A case enters", ul(ins) or GAP),
            ("Expected outcomes", ul([ending(x) for x in main_]) or vq.said(M, "stage: expected outcomes", stage_id, GAP)),
            ("Other outcomes", ul([ending(x) for x in other]) or vq.said(M, "stage: other outcomes", stage_id, "none on record")),
            ("Cannot be undone", ul(undo) or vq.said(M, "stage: cannot be undone", stage_id, "nothing on record")),
            ("At stake", ul(stake) or GAP),
            ("Its alerts", ul(al, raw=True) or "none proposed")]
    return '<div class="card"><dl>' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl></div>"


def stage_sources(M, stage_id):
    E = cv.esc
    st = M["stage"][stage_id]
    lis = [f'<li>{E(k)}: {E(st.get(k, ""))}</li>' for k in ("entry", "exit", "bound_in_code", "source")
           if st.get(k) and (k != "bound_in_code" or fo.time_limit(st[k]))]
    lis += expectation_cites(by_party(M, st.get("flow", ""), stage_id))
    lis += [f'<li>{E(m.get("move_id"))}: {E(m.get("from_state"))} to {E(m.get("to_state"))}, {E(m.get("path"))}'
            + (", irreversible" if (m.get("irreversible") or "").lower().startswith("yes") else "")
            + f'; process step {E(sid)}; {E(m.get("source", ""))}</li>' for sid, m in stage_moves(M, stage_id)]
    return f'<details class="cites"><summary>Where this comes from</summary><ul>{"".join(lis)}</ul></details>'


def block(M, stage_id, docs=None):
    """One stage's panel content: its BPMN drawing and key, its card, and where it comes from."""
    d = stage_drawing(M, stage_id)
    return f'<div class="seqfig">{d}</div>{stage_card(M, stage_id, docs)}{stage_sources(M, stage_id)}'


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
    """The stages left to right in their order, each with the time limit its code sets where it sets one, joined by the moves the register records between
    them: an arrow to the next stage, an arc over the stages a case can go straight past, an arc under for a move back.
    The expected path ends in a state of its own; under each stage, the states its other outcomes end a case in."""
    E = cv.esc
    f = next(x for x in M["flows"] if x["flow_id"] == flow_id)
    stages = flow_stages(M, flow_id)
    if not stages:
        return ""
    limited = [f'Stage {st.get("order", "")}' for st in stages if fo.time_limit(st.get("bound_in_code"))]
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
        pr = cv.wrap(duration(M, st.get("bound_in_code", "")), BW - 12, 10.5, 2)
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
            f'aria-label="{E(f.get("name", "") + ": its stages in order" + (", with the time limit the code sets on " + ", ".join(limited) if limited else "") + ", and the moves between them")}">'
            f'{_arrow_defs(mid)}<rect x="2" y="4" width="{W - 4}" height="{H - 8:g}" class="frame"/>'
            f'<text x="12" y="24" class="tagt">{E(f.get("name", ""))}: how a case moves end to end</text>'
            f'{"".join(parts)}</svg>')


def flow_key(M, flow_id):
    """The key to a flow's drawing: a box's time limit is keyed only where a stage of the flow has one."""
    limited = any(fo.time_limit(st.get("bound_in_code")) for st in flow_stages(M, flow_id))
    return FLOW_KEY.replace("Box: a stage, in order.", "Box: a stage, in order, with the time limit its code sets, "
                            "where it sets one." if limited else "Box: a stage, in order.")


FLOW_KEY = ('<details class="seqkey"><summary>Key to the drawing</summary><ul>'
            "<li>Box: a stage, in order. Filled dot: where a case starts.</li>"
            "<li>Arrow between stages: a case moves from one to the other. Solid: an expected outcome makes the move. "
            "Dashed: only an other outcome does.</li>"
            "<li>Arc over a stage: a case can go straight past it, to the stage the arc ends at.</li>"
            "<li>Dashed arrow down: an other outcome that ends the case in that stage.</li>"
            "<li>Rounded box with a ringed dot: where the expected path ends.</li>"
            "</ul></details>")


def serves(M, f):
    """Whom the flow serves: the customer first, then each other party, each with its whole-flow expectation."""
    E = cv.esc
    cust = labelled(M, f.get("customer", ""))
    whole = by_party(M, f["flow_id"])
    if not whole:
        return (cv.marked(M, cust) + ". " if cust else "") + "No expectations recorded"
    items = [f"{cv.marked(M, labelled(M, r.get('party', '')))}: "
             f"{cv.prose(M, labelled(M, r.get('expectation', '')) or GAP)}" for r in whole]
    if cust and party_key(whole[0].get("party")) != party_key(f.get("customer", "")):
        items.insert(0, cv.marked(M, cust))
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def flow_card(M, flow_id, docs=None):
    E = cv.esc
    f = next(x for x in M["flows"] if x["flow_id"] == flow_id)
    dl = vq.flow_delivers(M, f)
    books = []
    for st in flow_stages(M, flow_id):
        said = E(f'Stage {st.get("order", "")}: {st.get("name", "")}')
        page_ = (docs or {}).get(st["stage"], {}).get("Runbook")
        books.append(f'<a href="{E(page_)}">{said}</a>' if page_ else f"{said}: no runbook yet")
    rows = [("One case", cv.prose(M, vq.flow_row(M, f, "case")) or GAP),
            ("Starts", cv.prose(M, vq.flow_row(M, f, "starts_at")) or GAP),
            ("Ends", cv.prose(M, vq.flow_row(M, f, "ends_at")) or GAP),
            ("Serves", serves(M, f))]
    limit = vq.bound_said(M, f.get("bound_in_code", ""))  # optional: a row only where the code sets one
    rows += [("Time limit in the code", cv.prose(M, limit))] if limit else []
    rows += [("Delivers", "<ul>" + "".join(f"<li>{cv.prose(M, x)}</li>" for x in dl if x) + "</ul>" if any(dl) else GAP)]
    if books:
        rows.append(("Stage runbooks", "<ul>" + "".join(f"<li>{b}</li>" for b in books) + "</ul>"))
    return '<div class="card"><dl>' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl></div>"


def flow_sources(M, flow_id):
    E = cv.esc
    f = next(x for x in M["flows"] if x["flow_id"] == flow_id)
    lis = [f'<li>{E(k)}: {E(f.get(k, ""))}</li>'
           for k in ("case", "starts_at", "ends_at", "customer", "bound_in_code", "delivers", "source")
           if f.get(k) and (k != "bound_in_code" or fo.time_limit(f[k]))]
    lis += expectation_cites(by_party(M, flow_id))
    lis += [f'<li>{E(st["stage"])} time limit in the code: {E(st["bound_in_code"])}</li>' for st in flow_stages(M, flow_id)
            if fo.time_limit(st.get("bound_in_code"))]
    return f'<details class="cites"><summary>Where this comes from</summary><ul>{"".join(lis)}</ul></details>'


def flow_block(M, flow_id, docs=None):
    """One flow's panel content: its stages in order and key, its card, and where it comes from."""
    d = flow_drawing(M, flow_id)
    fig = (f'<div class="seqfig">{d}</div>{flow_key(M, flow_id)}' if d else
           '<p class="note">The register orders no stages for this flow.</p>')
    return fig + flow_card(M, flow_id, docs) + flow_sources(M, flow_id)


CSS = """
.casemoves .seqfig{background:var(--paper);border:1px solid var(--g200);border-radius:4px;margin:0 0 6px;overflow-x:auto}
.casemoves svg.seq{display:block;width:100%;height:auto}
.casemoves .card dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 10px;margin:6px 0;font-size:13px}
.casemoves .card dt{color:var(--g500);font-weight:600}.casemoves .card dd{margin:0;overflow-wrap:anywhere}
.casemoves .card ul{margin:0;padding-left:18px}.casemoves .card li{margin:0 0 3px}
.casemoves details{font-size:13px;color:var(--g600)}.casemoves details ul{padding-left:18px;margin:4px 0}
svg.seq.casemoves .bx{fill:var(--paper);stroke:var(--g600);stroke-width:1.2}
svg.seq.casemoves .ar.alt{stroke-dasharray:6 4}
svg.seq.casemoves .act{font-family:var(--sans);font-size:11.5px;fill:var(--slate)}
svg.seq.casemoves .lbl{font-family:var(--sans);font-size:10.5px;fill:var(--g600)}
svg.seq.casemoves .sn{font-family:var(--serif);font-size:11.5px;fill:var(--slate)}
svg.seq.casemoves .end{fill:var(--paper);stroke:var(--slate);stroke-width:1.4}
svg.bpmn .bp-pool{fill:none;stroke:var(--g600);stroke-width:1.2}
svg.bpmn .bp-pn{font:600 13px var(--sans);fill:var(--slate)}
svg.bpmn .bp-stagebox{fill:var(--ivory);stroke:var(--slate);stroke-width:2.2}
svg.bpmn .bp-sub,svg.bpmn .bp-adhoc{fill:var(--g200);fill-opacity:.55;stroke:var(--g600);stroke-width:1.3}
svg.bpmn .bp-esp{fill:var(--g200);fill-opacity:.3;stroke:var(--g600);stroke-width:1.4;stroke-dasharray:2 3}
svg.bpmn .bp-taskbox,svg.bpmn .bp-collapsedbox{fill:var(--paper);stroke:var(--g600);stroke-width:1.2}
svg.bpmn .bp-t{font:14.5px var(--sans);fill:var(--slate)}
svg.bpmn .bp-hd{font:600 13px var(--sans);fill:var(--g600)}
svg.bpmn .bp-cn{font:14.5px var(--sans);fill:var(--slate)}
svg.bpmn .bp-l{font:13px var(--sans);fill:var(--g600)}
svg.bpmn .bp-fl{font:italic 13px var(--sans);fill:var(--g600)}
svg.bpmn .bp-title{font:600 15.5px var(--sans);fill:var(--slate)}
svg.bpmn .bp-stitle{font:600 20px var(--sans);fill:var(--slate)}
svg.bpmn .bp-seq{fill:none;stroke:var(--g600);stroke-width:1.3}
svg.bpmn .bp-seq.main{stroke:var(--slate);stroke-width:2.4}
svg.bpmn .bp-head{fill:var(--slate)}svg.bpmn .bp-heado{fill:none;stroke:var(--slate);stroke-width:1.4}
svg.bpmn .bp-msg{fill:none;stroke:var(--g600);stroke-width:1.2;stroke-dasharray:6 4}
svg.bpmn .bp-msgstart{fill:var(--paper);stroke:var(--g600);stroke-width:1.2}
svg.bpmn .bp-assoc{fill:none;stroke:var(--g600);stroke-width:1.1;stroke-dasharray:2 3}
svg.bpmn .bp-ev{fill:var(--paper);stroke:var(--slate);stroke-width:1.3}svg.bpmn .bp-ev.ni{stroke-dasharray:4 2.5}
svg.bpmn .bp-evend{fill:var(--paper);stroke:var(--slate);stroke-width:3.4}
svg.bpmn .bp-gw{fill:var(--paper);stroke:var(--slate);stroke-width:1.3}svg.bpmn .bp-gwx{stroke:var(--slate);stroke-width:2.4}
svg.bpmn .bp-glyph{fill:none;stroke:var(--slate);stroke-width:1.1}
svg.bpmn .bp-mk{fill:none;stroke:var(--slate);stroke-width:1.1}svg.bpmn .bp-plus{stroke:var(--slate);stroke-width:1.3}
svg.bpmn .bp-tilde{fill:none;stroke:var(--slate);stroke-width:1.6}
svg.bpmn .bp-dobj{fill:var(--paper);stroke:var(--g600);stroke-width:1.1}
svg.bpmn .bp-ml{font:700 13px var(--sans);fill:var(--m-ink2)}
svg.bpmn .bp-gp{font:italic 13px var(--sans);fill:var(--m-bus-s)}
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
                   "main{max-width:78rem}</style></head><body><main>"
                   f'<h1>{E(M["system"])}: how a case moves</h1>{"".join(secs)}</main></body></html>\n', encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
