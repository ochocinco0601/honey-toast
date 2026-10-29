"""The competency questions each view answers, one predicate per question, shared by the cards that print the
answer and by run_status.py, which counts them. The page and the check therefore cannot disagree.

A question is answered (the register holds what the card prints), gapped (a row of measure-gaps.csv names the
element and the question, with one of the four kinds), or empty (the card prints a placeholder).

The contract of a question:
- required: it must be answered; no gap is accepted.
- answer or gap: answered, or a gap row with its kind.
- count only: counted, and never refused.

Element ids are those the coverage receipt uses: a step id, a stage id, a flow id, a part's subject id, for an
alert the handle of its measure, and for an expectation its id in expectations.csv. Usage: python view_questions.py <register folder> [stage id ...]"""
import contextlib
import io
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import capability_views as cv  # noqa: E402

REQUIRED, GAP_OK, COUNT = "required", "answer or gap", "count only"
CONTRACTS = (REQUIRED, GAP_OK, COUNT)
CONTRACT = {
    # How this step is carried out
    "step: moves": REQUIRED,  # the step's source cites the moves it is made of
    "step: trigger": GAP_OK,  # read from the body of the first hop of the move's travels_by
    "step: interactions": COUNT,  # the drawing marks what is not known; counted per step
    "step: right outcome": REQUIRED,
    "step: if it does not happen": REQUIRED,
    "step: timeouts": GAP_OK,
    "step: where each part sits": COUNT,
    # Inside this part
    "part: purpose": REQUIRED,
    "part: operations": GAP_OK,
    "part: depends on": GAP_OK,
    "part: agent parts": COUNT,
    "part: owner": COUNT,  # populated at the right time, never on the design surface
    "part: responder": COUNT,
    # How a case moves through this stage
    "stage: a case enters": REQUIRED,
    "stage: expected outcomes": REQUIRED,
    "stage: other outcomes": GAP_OK,
    "stage: cannot be undone": GAP_OK,
    "stage: at stake": REQUIRED,
    "stage: alerts": COUNT,
    "stage: expected by each party": REQUIRED,  # at least one expectations.csv row of the stage
    # How a case moves end to end
    "flow: one case": REQUIRED,
    "flow: starts": REQUIRED,
    "flow: ends": REQUIRED,
    "flow: serves": REQUIRED,  # the customer, and at least one expectation of the whole flow
    "flow: delivers": REQUIRED,
    "flow: stage runbooks": COUNT,
    # A runbook entry, for each alert drafted in a stage
    "alert: expectation it guards": REQUIRED,
    "alert: contain first": REQUIRED,
    "alert: its own tests": GAP_OK,
    # Each party's expectation, of a whole flow or of one stage
    "expectation: satisfied when": REQUIRED,
    "expectation: indicator": GAP_OK,  # a business health or impact measure naming it, or a gap with its kind
}
QUESTIONS = tuple(CONTRACT)
# Questions only measuring answers: what is at stake (the case attributes, written with the measures and costs) and an
# expectation's indicator (the measure that shows it is met). In a run whose person chose which stages to measure,
# they count only for those stages, and for the flow and its own expectations once any stage is measured.
MEASURE_ONLY = ("stage: at stake", "expectation: indicator")
# Questions only alerting answers (the alerts and the expectation each guards), and those only the runbooks answer
# (an alert's tests and what to contain first come from the failure modes, which are runbook work): each counts only
# for stages taken that far.
ALERTING_ONLY = ("stage: alerts", "alert: expectation it guards")
RUNBOOK_ONLY = ("flow: stage runbooks", "alert: contain first", "alert: its own tests")
# A required question one kind of gap may stand for, on one condition: a step no part carries may have no move in
# the code, which the gap says, citing where it was looked for. A step a part carries still needs its moves.
LIMITED = {"step: moves": ("no record",)}
GAPPABLE = tuple(q for q in QUESTIONS if CONTRACT[q] == GAP_OK or q in LIMITED)
KIND_WORDS = {  # measure-gaps.csv `kind`, as the cards open a gapped answer
    "does not apply": "Does not apply",
    "counted by": "Counted by",
    "no record": "No record to count",
    "not read": "Not assessed",
}


# ---------------------------------------------------------------- the gaps

def refusal(q, kind, why, element, participation):
    """Why a gap row on view question q does not count, or None. participation: the register's participation rows."""
    if q not in LIMITED:
        return None
    if kind not in LIMITED[q]:
        return f"{q!r} takes only a gap of kind {' or '.join(map(repr, LIMITED[q]))}, never {kind!r}"
    if any(p.get("step") == element for p in participation):
        return f"{q!r} is gapped only for a step no part carries; a part carries step {element}, so name its moves"
    if not cv.CITE.search(why or ""):
        return f"{q!r}: the reason cites no code read; say where the move was looked for, with the line"
    return None


def gaps(M):
    """{(element, question): (kind, why)} for the view questions in measure-gaps.csv that say why, where from, and a
    kind of the four. A required or count-only question takes no gap, so none is read for it."""
    if "_view_gaps" not in M:
        out = {}
        p = M["R"].get("_path")
        rows = (M["R"]["measure-gaps"] if "measure-gaps" in M["R"] else  # flow_outputs' model reads the table
                cv.read_csv(pathlib.Path(p) / "measure-gaps.csv") if p else [])
        for g in rows:
            if counts(g, M["R"].get("participation", [])):
                out[(" ".join(g["element"].split()), " ".join(g["question"].split()))] = (
                    " ".join(g["kind"].split()).lower(), g["why"].strip())
        M["_view_gaps"] = out
    return M["_view_gaps"]


def counts(g, participation):
    """Whether a measure-gaps.csv row counts as a gap on a view question: a question that takes a gap, a kind of the
    four, a why and a source, and none of refusal()'s reasons."""
    q = " ".join((g.get("question") or "").split())
    kind = " ".join((g.get("kind") or "").split()).lower()
    el = " ".join((g.get("element") or "").split())
    return bool(q in GAPPABLE and kind in KIND_WORDS and (g.get("why") or "").strip() and (g.get("source") or "").strip()
                and not refusal(q, kind, g.get("why"), el, participation))


def moves_excuse(step, gap_rows, participation):
    """Whether flow_outputs.py --check excuses a step with no move in lifecycle.csv. A step no part carries is excused
    by its `step: moves` gap of kind `no record` whose why cites the code read: returns that row. The gap is judged by
    counts(), the predicate the count of `step: moves` reads too, so the check and the count agree on every gap. A step
    whose source begins `reference model` and that no part carries is excused too: returns "reference model", and
    status() counts its `step: moves` as does not apply. Otherwise None."""
    g = next((g for g in gap_rows if " ".join((g.get("question") or "").split()) == "step: moves"
              and " ".join((g.get("element") or "").split()) == step["step"] and counts(g, participation)), None)
    if g:
        return g
    if (step.get("source") or "").lower().startswith("reference model") and not any(
            p.get("step") == step["step"] for p in participation):
        return "reference model"
    return None


FROM_MOVES = ("step: trigger", "step: if it does not happen", "step: timeouts")


def moveless_outcomes(M, stage_id):
    """[(step, its `step: moves` gap)] for the stage's steps that no move and no part carries, whose moves are gapped:
    such a step is how a case leaves the stage, and the register can say no more of it."""
    import step_sequence as ss
    out = []
    for x in M["stage"][stage_id]["_steps"]:
        g = gaps(M).get((x["step"], "step: moves"))
        if g and not ss.moves_of(M, x["step"]):
            out.append((x["step"], g))
    return out


def gap_of(M, q, el):
    """(kind, why) of the gap that stands for question q of element el, or None. A step whose moves are gapped passes
    the questions read from its moves by the same gap, and a stage whose expected outcome is such a step passes that
    question by it, so neither needs rows of its own."""
    g = gaps(M).get((el, q))
    if g:
        return g
    if q in FROM_MOVES:
        return gaps(M).get((el, "step: moves"))
    if q == "stage: expected outcomes" and el in M["stage"]:
        inherited = moveless_outcomes(M, el)
        return inherited[0][1] if inherited else None
    return None


def gap_said(M, q, el):
    """The gap's kind and reason as plain words, or None."""
    g = gap_of(M, q, el)
    return f"{KIND_WORDS[g[0]]}: {why_said(M, g[1])}" if g else None


def why_said(M, why):
    """A gap's reason as a reader sees it: plain words, a flow it cites by the flow's name."""
    import step_sequence as ss
    return cv.named_flows(M, ss.plain(why) or why)


def said(M, q, el, placeholder):
    """What a card prints for a question with no answer: the gap's kind and reason where measure-gaps.csv gives one,
    else the placeholder. Escaped HTML."""
    if q == "stage: expected outcomes" and el in M["stage"] and moveless_outcomes(M, el):
        return "<ul>" + "".join(f"<li>{cv.esc(cv.step_title(M, x))}: <i>{cv.esc(KIND_WORDS[g[0]])}</i>: "
                                f"{cv.esc(why_said(M, g[1]))}</li>" for x, g in moveless_outcomes(M, el)) + "</ul>"
    g = gap_of(M, q, el)
    if not g:
        return placeholder
    return f"<i>{cv.esc(KIND_WORDS[g[0]])}</i>: {cv.esc(why_said(M, g[1]))}"


# ---------------------------------------------------------------- one step

def scenario(M, sid):
    import step_sequence as ss
    cache = M.setdefault("_vq_scenarios", {})
    if sid not in cache:
        cache[sid] = ss.scenario(M, sid)
    return cache[sid]


def trigger(M, sc):
    """[(what starts it, or "" where the hop has no body; the state the case is in, or "")]: the first hop of the
    first move where the moves run one after another, else of each move."""
    import flow_outputs as fo
    import step_sequence as ss
    out = []
    for mv in (sc["moves"][:1] if sc.get("chained") else sc["moves"]):
        hs = ss.hops(mv)
        if hs:
            st = fo.state(mv.get("from_state"))
            out.append((hs[0][3], "" if st in ("", "(none)") else st))
    return out


def trigger_answered(M, sc):
    t = trigger(M, sc)
    return bool(t) and all(body for body, _ in t)


def if_not(M, sc):
    import step_sequence as ss
    vals = [ss.plain(mv.get("if_not", "")) + (f'. Recovery: {mv["recovery"]}' if mv.get("recovery") else "")
            for mv in sc["moves"]]
    return list(dict.fromkeys(v for v in vals if v))


def timeouts(M, sc):
    import step_sequence as ss
    return list(dict.fromkeys(v for v in (ss.plain(mv.get("timing", "")) for mv in sc["moves"]) if v))


def right_outcome(M, sid):
    import step_sequence as ss
    outcome, prop = ss.unproposed(M["step"][sid].get("right_outcome", ""))
    return ss.plain(outcome), prop


def interactions_known(M, sc):
    """True where the step's interactions carry no mark of something not known."""
    import step_sequence as ss
    card = ss.card(M, sc)
    m = re.search(r"<dt>Interactions, in order</dt><dd>(.*?)</dd><dt>", card, re.S)
    return bool(m) and ss.GAP not in m.group(1)


# ---------------------------------------------------------------- one part

def purpose(M, pid):
    import step_sequence as ss
    v = M["subj"][pid].get("purpose", "")
    return ss.plain(v) or v.strip()


def depends_on(M, pid):
    """(the parts it calls, the dependencies named through its agent parts)."""
    import part_inside as pi
    calls = list(dict.fromkeys(r["to_id"] for r in pi.interactions(M, pid)))
    through = []
    if M["family"](M["subj"][pid]) == "agent":
        through = list(dict.fromkeys(r.get("name", "") for r in pi.agent_rows(M, pid) if r.get("element") == "dependency"))
    return calls, through


def agent_parts(M, pid):
    import part_inside as pi
    return [r for r in pi.agent_rows(M, pid) if r.get("element") == "agent part"]


# ---------------------------------------------------------------- one stage

def stage_enters(M, stage_id):
    import flow_outputs as fo
    import stage_flow_views as sfv
    out = []
    for m, sid in sfv.entering(M, stage_id):
        if sid and M["step"].get(sid, {}).get("stage") != stage_id:
            other = M["stage"].get(M["step"][sid].get("stage"), {})
            out.append(f'from Stage {other.get("order", "")}: {cv.step_title(M, sid)}')
        elif sid:
            out.append(cv.step_title(M, sid))
    flow = M["stage"][stage_id].get("flow", "")
    first = (sfv.flow_stages(M, flow) or [{}])[0].get("stage") == stage_id
    if not out and first:  # the first stage, whose moves all start from (none): a case enters by the flow's start
        f = next((x for x in M["flows"] if x["flow_id"] == flow), {})
        starts = sfv.headline(M, f.get("starts_at", ""))
        made = list(dict.fromkeys(sid for sid, m in sfv.stage_moves(M, stage_id) if fo.state(m.get("from_state")) == "(none)"))
        if starts or made:
            out.append("the case starts" + (f": {starts}" if starts else "")
                       + (f", by {'; '.join(cv.step_title(M, x) for x in made)}" if made else ""))
    if not out:  # no move says how a case enters: the stage's own entry, where the register states one
        entry = sfv.headline(M, M["stage"][stage_id].get("entry", ""))
        out += [entry] if entry else []
    return out


def stage_outcomes(M, stage_id, label):
    """The steps by which a case leaves the stage, of one label: "Expected outcome" or "Other outcome"."""
    import stage_flow_views as sfv
    return list(dict.fromkeys(sid for sid, m in sfv.exits(M, stage_id) if M["_step_label"].get(sid) == label))


def stage_undo(M, stage_id):
    import stage_flow_views as sfv
    return [sfv.move_said(M, sid, m) for sid, m in sfv.stage_moves(M, stage_id)
            if (m.get("irreversible") or "").strip().lower().startswith("yes")]


def stage_stake(M, stage_id):
    """What is at stake for a case in the stage: one line naming the flow's case attributes, and saying the register
    does not tie them to a stage. case-attributes.csv has no stage or step column (REGISTER.md), so which attributes
    a stage touches is not in the register, and listing every attribute's stake under every stage would claim it is.
    [] where the flow has none."""
    flow = M["stage"][stage_id].get("flow", "")
    names = list(dict.fromkeys(a.get("attribute", "").strip() for a in M["R"].get("case-attributes", [])
                               if a.get("flow") in (flow, "") and a.get("attribute", "").strip()))
    if not names:
        return []
    return ["For the whole flow: " + "; ".join(names) + "."]


def bound_said(M, text):
    """The time limit in the code as the cards print it, or "" where the code sets none (flow_outputs.time_limit).
    The column is optional, so it is no question of any view: a card prints it only where it is filled."""
    import flow_outputs as fo
    import stage_flow_views as sfv
    return sfv.bound_text(M, text) if fo.time_limit(text) else ""


# ---------------------------------------------------------------- one flow

def flow_row(M, f, col):
    import stage_flow_views as sfv
    return sfv.headline(M, f.get(col, ""))


def flow_delivers(M, f):
    caps = {c.get("capability_id"): c.get("name", "") for c in M["R"].get("capabilities", [])}
    return [x for x in (caps.get(c.strip(), "") for c in (f.get("delivers") or "").split(";") if c.strip()) if x]


# ---------------------------------------------------------------- one expectation

def expectations(M, flow=None, stage=None):
    """The expectations.csv rows of a flow (whole-flow ones where stage is ""), or of a stage."""
    return [e for e in M["R"].get("expectations", [])
            if (flow is None or e.get("flow") == flow) and (stage is None or (e.get("stage") or "") == stage)]


def indicators(M, eid):
    """The measures that answer whether an expectation is met: at `business health` or `business impact`, of a flow,
    a stage or a step, whose `expectation` names it. A measure whose `defect` is set counts wrongly, so it does not."""
    import flow_outputs as fo
    return [m for m in M["R"].get("measures", []) if m.get("layer") in fo.BUSINESS
            and eid in cv.ids(m.get("expectation")) and not (m.get("defect") or "").strip()]


# ---------------------------------------------------------------- the predicates

def _flow(M, fid):
    return next(x for x in M["flows"] if x["flow_id"] == fid)


def answered(M, q, el, ctx=None):
    """Whether the register answers question q for element el, as the card prints it. ctx: for an alert, the stage
    model flow_outputs builds and the measure row."""
    view = q.split(":")[0]
    if view == "step":
        sc = scenario(M, el)
        return {
            "step: moves": lambda: bool(sc["moves"]),
            "step: trigger": lambda: trigger_answered(M, sc),
            "step: interactions": lambda: interactions_known(M, sc),
            "step: right outcome": lambda: bool(right_outcome(M, el)[0]),
            "step: if it does not happen": lambda: bool(if_not(M, sc)),
            "step: timeouts": lambda: bool(timeouts(M, sc)),
            "step: where each part sits": lambda: bool(sc["pids"]),
        }[q]()
    if view == "part":
        import part_inside as pi
        s = M["subj"][el]
        return {
            "part: purpose": lambda: bool(purpose(M, el)),
            "part: operations": lambda: bool(pi.operations(M, el)),
            "part: depends on": lambda: any(depends_on(M, el)),
            "part: agent parts": lambda: bool(agent_parts(M, el)),
            "part: owner": lambda: bool((s.get("owner") or "").strip()),
            "part: responder": lambda: bool((s.get("responder") or "").strip()),
        }[q]()
    if view == "stage":
        import stage_flow_views as sfv
        return bool({
            "stage: a case enters": lambda: stage_enters(M, el),
            "stage: expected outcomes": lambda: stage_outcomes(M, el, "Expected outcome"),
            "stage: other outcomes": lambda: stage_outcomes(M, el, "Other outcome"),
            "stage: cannot be undone": lambda: stage_undo(M, el),
            "stage: at stake": lambda: stage_stake(M, el),
            "stage: alerts": lambda: sfv.alerts(M, el),
            "stage: expected by each party": lambda: expectations(M, stage=el),
        }[q]())
    if view == "flow":
        f = _flow(M, el)
        cols = {"flow: one case": "case", "flow: starts": "starts_at", "flow: ends": "ends_at"}
        if q == "flow: serves":
            return bool(flow_row(M, f, "customer")) and bool(expectations(M, flow=el, stage=""))
        if q in cols:
            return bool(flow_row(M, f, cols[q]))
        if q == "flow: delivers":
            return bool(flow_delivers(M, f))
        if q == "flow: stage runbooks":
            return bool(f["_stages"]) and all((M.get("_docs") or {}).get(st["stage"], {}).get("Runbook")
                                              for st in f["_stages"])
    if view == "alert":
        import flow_outputs as fo
        SM, m = ctx
        if q == "alert: expectation it guards":  # read from `expectation`, never from the basis's prose
            known = {e.get("expectation_id") for e in M["R"].get("expectations", [])}
            return any(x in known for x in fo.guards(m))
        if q == "alert: contain first":
            return not fo.contain(SM, m).startswith("Its `counted_moves` names no move")
        if q == "alert: its own tests":
            return not fo.no_tests(SM, m, fo.entry_groups(SM, m))
    if view == "expectation":
        e = next((x for x in M["R"].get("expectations", []) if x.get("expectation_id") == el), {})
        if q == "expectation: satisfied when":
            return bool((e.get("satisfied_when") or "").strip())
        if q == "expectation: indicator":
            return bool(indicators(M, el))
    raise KeyError(q)


def status(M, q, el, ctx=None):
    """("answered", None), ("gapped", kind) or ("empty", None)."""
    if answered(M, q, el, ctx):
        return ("answered", None)
    if q == "step: moves" and el in M["step"] and moves_excuse(M["step"][el], [], M["R"]["participation"]):
        return ("gapped", "does not apply")  # a reference-model step nothing carries, excused as the check excuses it
    g = gap_of(M, q, el) if q in GAPPABLE or q in FROM_MOVES or q == "stage: expected outcomes" else None
    return ("gapped", g[0]) if g else ("empty", None)


# ---------------------------------------------------------------- counting a register

def load(reg):
    import one_canvas as oc
    M = oc.number_steps(oc.prune(cv.model(cv.load(pathlib.Path(reg)))))
    M["_docs"] = oc.stage_docs(pathlib.Path(reg))
    return M


def count(reg, owed=None, measured=None, alerting=None, runbooks=None):
    """{question: {"answered": [ids], "gapped": {kind: [ids]}, "empty": [ids]}} over the flows with a stage the run owes, the stages it owes and their steps, every part, and each alert drafted in an owed stage. owed None: every
    stage. `measured`, `alerting` and `runbooks`, the stages the person chose to measure, to take to alerting and to
    take to runbooks: given, a question of MEASURE_ONLY counts only for a measured stage (and for the flow's own
    expectations once any stage is measured), one of ALERTING_ONLY only for a stage taken to alerting, and one of
    RUNBOOK_ONLY only for one taken to runbooks. None: every owed stage, as before."""
    import flow_outputs as fo
    import part_inside as pi
    M = load(reg)
    C = {q: {"answered": [], "gapped": {}, "empty": []} for q in QUESTIONS}

    def counted(q, stage):
        """Whether question q is asked of an element of `stage` (None: of the flow as a whole)."""
        for only, chosen in ((MEASURE_ONLY, measured), (ALERTING_ONLY, alerting), (RUNBOOK_ONLY, runbooks)):
            if q in only and chosen is not None:
                return bool(chosen) if stage is None else stage in chosen
        return True

    def put(q, el, ctx=None, stage=None):
        if not counted(q, stage):
            return
        st, kind = status(M, q, el, ctx)
        if st == "gapped":
            C[q]["gapped"].setdefault(kind, []).append(el)
        else:
            C[q][st].append(el)

    def of(view):
        return [q for q in QUESTIONS if q.startswith(view + ":")]
    for f in M["flows"]:
        stages = [st for st in f["_stages"] if owed is None or st["stage"] in owed]
        if not stages:  # a flow the run owes no stage of is not this run's
            continue
        for q in of("flow"):
            put(q, f["flow_id"])
        for st in stages:
            for q in of("stage"):
                put(q, st["stage"], stage=st["stage"])
            for x in st["_steps"]:
                for q in of("step"):
                    put(q, x["step"])
    for p in pi.parts(M):
        for q in of("part"):
            if q == "part: agent parts" and M["family"](M["subj"][p]) != "agent":
                continue
            put(q, p)
    R = fo.load(pathlib.Path(reg))
    for f in R["flows"]:
        for s in R["stages"]:
            if s.get("flow") != f["flow_id"] or (owed is not None and s["stage"] not in owed):
                continue
            with contextlib.redirect_stdout(io.StringIO()):
                SM = fo.build(R, f["flow_id"], s["stage"])
            for m in [m for m in SM["alerts"] if m.get("stage") == s["stage"]]:
                for q in of("alert"):
                    put(q, m.get("handle", ""), (SM, m), stage=s["stage"])
    for f in M["flows"]:  # each expectation of an owed flow: of the whole flow, or of a stage the run owes
        owed_here = [st["stage"] for st in f["_stages"] if owed is None or st["stage"] in owed]
        if not owed_here:
            continue
        for e in expectations(M, flow=f["flow_id"]):
            if not e.get("stage") or e["stage"] in owed_here:
                for q in of("expectation"):
                    put(q, e.get("expectation_id", ""), stage=e.get("stage") or None)
    return C


def lines(C):
    """One line per question: its contract, and answered / gapped by kind / empty, with the empty ids."""
    out = []
    for q in QUESTIONS:
        c = C[q]
        n_gap = sum(len(v) for v in c["gapped"].values())
        if not (c["answered"] or n_gap or c["empty"]):
            continue
        kinds = ", ".join(f"{len(c['gapped'][k])} {k}" for k in KIND_WORDS if c["gapped"].get(k))
        out.append(f"{q} [{CONTRACT[q]}]: {len(c['answered'])} answered, {n_gap} gapped{f' ({kinds})' if kinds else ''}, "
                   f"{len(c['empty'])} empty"
                   + (f" ({', '.join(c['empty'])})" if c["empty"] and CONTRACT[q] != COUNT else ""))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print("\n".join(lines(count(sys.argv[1], sys.argv[2:] or None))))
