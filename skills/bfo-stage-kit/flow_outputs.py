"""Every output for one stage of one flow, read off the register's lifecycle.

STRUCTURE.md (the slice as a tree with branches), MEASURES.md (where each measure is counted, by level and layer),
ALERT.md (the alerts proposed, from the measures marked in `alert`) and RUNBOOK.md (a short entry per proposed alert, which
its runbook link points at, and one shared section for the stage that writes every test once: one test per failure mode
in failure-modes.csv), with ALERT.html and RUNBOOK.html, the same two as pages. All six share the register's step
numbers; a stage with no proposed alert gets no ALERT.md or ALERT.html.

Usage: flow_outputs.py <register dir> <flow id> <stage id> --out <dir>      check, then write all six
       flow_outputs.py <register dir> <flow id> <stage id> --check          check only

The check fails the run when a move of the stage has a hop, a carrier or a need with no failure mode, when a failure
mode names a part its move does not use, when an element the measure step accounts for is neither covered by a
candidate in measures.csv nor gapped in measure-gaps.csv (`receipt`: an error for the run's stage and the flow, a
warning for an element only other stages hold), and on the other rules listed
in `check`. STRUCTURE.md and MEASURES.md are written even when it fails; the four alert and runbook files are not."""
import argparse
import csv
import hashlib
import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from capability_views import read_csv, ids  # noqa: E402
import capability_views as cv  # noqa: E402
import go  # noqa: E402
import page_style as ps  # noqa: E402
import view_questions as vq  # noqa: E402

TABLES = ["about", "flows", "capabilities", "stages", "steps", "subjects", "participation", "measures", "lifecycle",
          "failure-modes", "remedies", "step-impact", "case-attributes", "agent-system", "measure-gaps", "sources",
          "expectations"]
ENDINGS = {
    "nothing wrong": "Nothing is wrong",
    "expected condition": "Expected condition",
    "self-healed": "Self-healed",
    "degraded within tolerance": "Degraded within tolerance",
    "already known": "Already known",
    "restore": "Broken — restore",
    "cannot restore": "Broken — cannot restore",
    "outside": "Outside this runbook",
    "not possible": "Not possible here",
}
GAP_KINDS = vq.KIND_WORDS  # measure-gaps.csv `kind`, a closed list: the kind is data, never read from the reason's wording
REMEDY_KINDS = ("restore", "re-drive", "roll back", "none exists", "do not")
RESTORING = ("restore", "re-drive", "roll back")
REMEDY_TEXT = ("action", "expected", "if_different", "also_escalate_to")
REMEDY_ID = r"\bRM\d+\b"  # a remedy id; an interaction is R01, a remedy of an earlier release R1 (old_remedy_id_failures)


def old_remedy_id_failures(R):
    """One error per table holding a remedy id written the earlier way (`R1`, now `RM1`), naming the migration."""
    out = []
    for table in ("remedies", "failure-modes"):
        old = list(dict.fromkeys(r["remedy"] for r in R.get(table, []) if re.fullmatch(r"R\d+", r.get("remedy") or "")))
        if old:
            out.append(f"{table}.csv: remedy {', '.join(f'{x} is now RM{x[1:]}' for x in old[:3])}"
                       f"{f' (and {len(old) - 3} more)' if len(old) > 3 else ''} (a register made with an earlier "
                       "version of this kit): run reconcile.py --migrate on a copy of the register, which renames "
                       "every remedy id and every reference to one")
    return out
RECOVERY = cv.RECOVERY
RUNBOOK_LATER = ("The runbook comes at the runbooks stage, after these alerts are reviewed: it writes the ways each "
                 "can fail, the tests that tell them apart, and what to do.")
THRESHOLD = ("*Operator value, not set here.* For each measure, the value at which the alert fires. Whether it "
             "pages a person, opens a ticket or shows on a dashboard is the operators' decision.")
LAYERS = ["business health", "business impact", "application", "technology"]
HEAD = ["Business health<br>is the expectation met? (counted on cases)", "Business impact<br>for how many cases is it not?",
        "Application<br>how did the software behave?", "System<br>how did the infrastructure behave?"]


# ---------------------------------------------------------------- reading

def load(reg):
    reg = pathlib.Path(reg)
    R = {t: [{k: cell(v) for k, v in r.items()} for r in read_csv(reg / f"{t}.csv")] for t in TABLES}
    R["hop-failures"] = read_csv(HERE / "method" / "hop-failures.csv")
    R["measure-forms"] = read_csv(HERE / "method" / "measure-forms.csv")
    R["agent-questions"] = read_csv(HERE / "method" / "agent-questions.csv")
    R["impact"] = read_csv(HERE / "method" / "impact.csv") if (HERE / "method" / "impact.csv").exists() else []
    R["products"] = vouched_products(read_csv(reg / PRODUCT_NAMES))
    R["_name"] = reg.name
    return R


# ---------------------------------------------------------------- freshness

STAMP = re.compile(r"<!-- bfo-generated-from (\{.*?\}) -->")


def fingerprint(reg):
    """{table: digest} of the register tables the outputs are generated from, each read as rows (so a byte-order mark
    or line endings change nothing), `absent` for a table the register does not have."""
    out = {}
    for t in TABLES:
        p = pathlib.Path(reg) / f"{t}.csv"
        if not p.is_file():
            out[t] = "absent"
            continue
        with p.open(encoding="utf-8-sig", newline="") as f:
            rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
        out[t] = hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
    return out


def stamp(reg, flow_id, stage_id):
    """The line each generated output ends with: the flow, the stage and the fingerprint of the register it was
    generated from. An HTML comment, so neither the markdown nor the page shows it. run_status.py reads it back."""
    data = {"flow": flow_id, "stage": stage_id, "tables": fingerprint(reg)}
    return f"\n<!-- bfo-generated-from {json.dumps(data, sort_keys=True)} -->\n"


def stamp_of(text):
    """The stamp an output carries, or None for one written without it (by an earlier kit, or by hand)."""
    m = STAMP.search(text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def changed_since(tables, reg):
    """The register tables (`steps.csv`) that differ from a stamp's fingerprint, sorted."""
    now, then = fingerprint(reg), tables or {}
    return sorted(f"{t}.csv" for t in set(now) | set(then) if then.get(t) != now.get(t))


def regenerate_command(reg, flow_id, stage_id):
    """The command that writes a stage's outputs again, into the register's stage-<id> folder."""
    return f"python flow_outputs.py {reg} {flow_id} {stage_id} --out {pathlib.Path(reg) / f'stage-{stage_id}'}"


def cell(v):
    """A register value made safe for a markdown table cell: a pipe would end the cell."""
    return (v or "").replace("|", "\\|").replace("\n", " ")


def split_top(text, seps=";"):
    """Split on separators that are not inside parentheses."""
    out, depth, cur = [], 0, ""
    for ch in text or "":
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        if ch in seps and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return [x for x in out if x]


def strip_parens(text):
    out, depth = "", 0
    for ch in text or "":
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        elif not depth:
            out += ch
    return out


def state(s):
    s = (s or "").strip()
    if s.startswith("(none)"):
        return "(none)"
    return re.split(r"\s+\(", s)[0].strip()


def resolve(token, subj):
    t = token.strip()
    m = re.match(r"([A-Z]\d+)\b", t)
    if m and m.group(1) in subj:
        return m.group(1)
    low = t.lower()
    for sid, s in subj.items():
        if s.get("kind") == "element" and (s["name"].lower() == low or state(s["name"]).lower() == low):
            return sid
    first = low.split()[0] if low.split() else ""
    hits = [sid for sid, s in subj.items() if s.get("kind") == "element" and s["name"].lower().split()[:1] == [first]]
    return hits[0] if len(hits) == 1 else None


def parts(text, subj, unresolved):
    out = []
    for tok in split_top(strip_parens(text), ";,"):
        sid = resolve(tok, subj)
        if sid and sid not in out:
            out.append(sid)
        elif not sid:
            unresolved.append(tok)
    return out


def hop_kinds(travels_by, catalogue_kinds):
    kinds = []
    for hop in split_top(travels_by):
        head = hop.split("(")[0].lower()
        found = [k for k in catalogue_kinds if re.search(rf"(^|\W){re.escape(k)}($|\W)", head)]
        kinds.append(found[-1] if found else "?" + head.strip())
    return list(dict.fromkeys(kinds))


# ---------------------------------------------------------------- the model of one stage

def step_labels(stages, steps, lifecycle):
    """How every output names a process step, in reading order. A step whose moves stay in its stage is an act,
    numbered within the stage in register order ("Process step 3.1"); a step whose move takes the case out of the stage is
    one of its endings, unnumbered, the main path's first ("Expected outcome", then "Other outcome")."""
    moves = {m.get("move_id"): m for m in lifecycle}
    out = {}
    for st in sorted(stages, key=lambda s: (s.get("flow", ""), int(s["order"]) if s.get("order", "").isdigit() else 0)):
        mine = [s for s in steps if s.get("stage") == st["stage"]]
        mv = {s["step"]: [moves[x] for x in dict.fromkeys(re.findall(r"\bL\d+\b", s.get("source", ""))) if x in moves]
              for s in mine}
        inside = {state(m.get("from_state")) for ms in mv.values() for m in ms}
        ends = {sid: [m for m in ms if not side_move(m) and state(m.get("to_state")) not in inside] for sid, ms in mv.items()}
        acts = [s["step"] for s in mine if not ends[s["step"]]]
        main = [s["step"] for s in mine if any(m.get("path") == "main" for m in ends[s["step"]])]
        other = [s["step"] for s in mine if ends[s["step"]] and s["step"] not in main]
        out.update({sid: f'Process step {st.get("order")}.{i}' for i, sid in enumerate(acts, 1)})
        out.update({sid: "Expected outcome" for sid in main})
        out.update({sid: "Other outcome" for sid in other})
    return out


def step_title(labels, s):
    """"Process step 3.1: The parcel is delivered", or the register's id where the step has no stage."""
    return f'{labels.get(s["step"]) or "Process step " + s["step"]}: {s.get("name", "")}'


def at_stake(M, i):
    """One step-impact row as a sentence about what is at stake: the impact category in the method's words and the
    step by its name ("Customer experience and trust, if “The parcel is delivered” fails"); the caller adds the unit."""
    words = next((c["what_is_at_stake"] for c in M["R"].get("impact", []) if c["impact_category"] == i["impact_category"]),
                 i["impact_category"].replace("-", " "))
    s = next((x for x in M["steps"] if x["step"] == i["step"]), {})
    return f"{cap(words)}, if “{s.get('name') or 'its step'}” fails"


def relabel_prose(labels, steps, text):
    """Register prose cites a step by its register id ("as step 9"); a reader sees it by its label instead:
    "as process step 2.4", or 'as the expected outcome "The parcel is delivered"'. The register itself is not rewritten."""
    names = {s["step"]: s.get("name", "") for s in steps}

    def one(m):
        sid, label = m.group(3), labels.get(m.group(3))
        upper = (m.group(1) or m.group(2)) in "PS"
        if not label:
            return m.group(0)
        if label.startswith("Process step "):
            return ("P" if upper else "p") + "rocess step " + label[len("Process step "):]
        said = f'the {label.lower()} \u201c{names.get(sid, "")}\u201d'
        return said[0].upper() + said[1:] if upper else said
    return re.sub(r"\b(?:([Pp])rocess s|([Ss]))tep (\d+)\b(?!\.\d)", one, text)


def build(R, flow_id, stage_id):
    subj = {s["subject_id"]: s for s in R["subjects"]}
    flow = next(f for f in R["flows"] if f["flow_id"] == flow_id)
    stages = sorted([s for s in R["stages"] if s["flow"] == flow_id], key=lambda s: int(s["order"]))
    stage = next(s for s in stages if s["stage"] == stage_id)
    moves = {m["move_id"]: m for m in R["lifecycle"] if m.get("flow", flow_id) in (flow_id, "")}
    order = list(moves)
    steps = sorted([s for s in R["steps"] if s["stage"] == stage_id], key=lambda s: int(s["step"]))
    kinds = list(dict.fromkeys(h["hop_kind"] for h in R["hop-failures"]))
    unresolved = []
    M = dict(R=R, subj=subj, flow=flow, stages=stages, stage=stage, steps=steps, moves=moves, kinds=kinds,
             unresolved=unresolved, labels=step_labels(R["stages"], R["steps"], R["lifecycle"]))
    M["step_moves"] = {s["step"]: list(dict.fromkeys(x for x in re.findall(r"\bL\d+\b", s.get("source", "")) if x in moves))
                       for s in steps}
    M["stage_moves"] = sorted({x for v in M["step_moves"].values() for x in v}, key=order.index)
    M["carried"] = {mv: parts(moves[mv]["carried_by"], subj, unresolved) for mv in moves}
    M["needs"] = {mv: parts(moves[mv]["needs"], subj, unresolved) for mv in moves}
    M["hops"] = {mv: hop_kinds(moves[mv]["travels_by"], kinds) for mv in moves}
    M["performers"] = {s["step"]: list(dict.fromkeys(x for mv in M["step_moves"][s["step"]] for x in M["carried"][mv]))
                       for s in steps}
    M["supporters"] = {s["step"]: [x for x in dict.fromkeys(x for mv in M["step_moves"][s["step"]] for x in M["needs"][mv])
                                   if x not in M["performers"][s["step"]]] for s in steps}
    M["branch_states"] = list(dict.fromkeys(state(moves[mv]["from_state"]) for mv in M["stage_moves"]))
    produced = {state(moves[mv]["to_state"]) for mv in M["stage_moves"] if not side_move(moves[mv])}
    M["exits"] = list(dict.fromkeys(state(moves[mv]["to_state"]) for mv in M["stage_moves"]
                                    if state(moves[mv]["to_state"]) not in M["branch_states"] and not side_move(moves[mv])))
    starts = list(dict.fromkeys(state(moves[mv]["from_state"]) for mv in M["stage_moves"]))
    M["entries"] = [s for s in starts if s not in produced] or starts[:1]
    M["fm"] = [r for r in R["failure-modes"] if set(ids(r.get("moves"))) & set(M["stage_moves"])]
    M["remedies"] = {r["remedy"]: r for r in R["remedies"]}
    M["measures"] = {m["handle"]: m for m in R["measures"]}
    M["alerts"] = [m for m in R["measures"] if proposed(m)]
    M["reach"] = {m["handle"]: reach(R, m) for m in M["alerts"]}
    M["parts"] = list(dict.fromkeys(x for s in steps for x in M["performers"][s["step"]] + M["supporters"][s["step"]]))
    return M


WAITING = ("backlog", "cycle time")


def proposed(m):
    return re.match(r"yes\b", m.get("alert", "").strip(), re.I) is not None


def basis(m):
    return re.sub(r"^yes\b\s*:?\s*", "", m.get("alert", "").strip(), flags=re.I)


def level(m):
    """Where a measure sits, read off the register's own columns: its step, its stage, its flow, else the part it is a
    measure of. An alert is drafted at whatever level its measure is on; the kit presumes none."""
    for col in ("step", "stage", "flow"):
        if norm(m.get(col)):
            return col
    return "part"


def reach(R, m):
    """[(stage id, [step ids])] a measure reaches, in the flow's order: a step's own stage and step; a stage itself;
    every stage of a flow; and for a part, each step its participation.csv rows put it on, narrowed to the operations
    its `operation` names where any row writes one of them (a part's measure is held once and reaches every stage
    it serves)."""
    stages = sorted(R["stages"], key=lambda s: (s.get("flow", ""), int(s["order"]) if s.get("order", "").isdigit() else 0))
    of = {s["step"]: s.get("stage", "") for s in R["steps"]}
    lv = level(m)
    if lv == "step":
        st = of.get(norm(m["step"])) or norm(m.get("stage"))
        return [(st, [norm(m["step"])])] if st else []
    if lv == "stage":
        return [(norm(m["stage"]), [])]
    if lv == "flow":
        return [(s["stage"], []) for s in stages if s.get("flow") == norm(m["flow"])]
    rows = [p for p in R["participation"] if p.get("subject_id") == m.get("subject_id")]
    ops = set(listed(m.get("operation")))
    rows = [p for p in rows if ops & set(listed(p.get("operation")))] or rows
    steps = list(dict.fromkeys(p["step"] for p in rows if of.get(p["step"])))
    order = [s["step"] for s in R["steps"]]
    return [(s["stage"], sorted((x for x in steps if of[x] == s["stage"]), key=order.index))
            for s in stages if any(of[x] == s["stage"] for x in steps)]


def placed(M, m):
    """Where an alert is drafted, in words: its level and every stage and step it reaches."""
    st = {s["stage"]: s for s in M["R"]["stages"]}
    steps = {s["step"]: s for s in M["R"]["steps"]}

    def stage_said(sid, xs):
        s = st.get(sid, {})
        return (f"stage {s.get('order', '?')} {s.get('name', sid)}" +
                (f" ({'; '.join(step_title(M['labels'], steps[x]) for x in xs if x in steps)})" if xs else ""))
    reached = "; ".join(stage_said(sid, xs) for sid, xs in M["reach"].get(m["handle"], [])) or "no stage of the register"
    lv = level(m)
    if lv == "stage":
        return "On the stage: " + reached
    if lv == "step":
        return "On a process step: " + reached
    if lv == "flow":
        f = next((x for x in M["R"]["flows"] if x["flow_id"] == norm(m["flow"])), {})
        return f"On the flow {f.get('name', m['flow'])}, so it reaches every stage: {reached}"
    return f"On the part {name(M, m.get('subject_id', ''))}, so it reaches every stage and process step it serves: {reached}"


def grouped(items, key):
    """(key, items) pairs in first-seen order, so text shared by several moves is written once."""
    out = {}
    for x in items:
        out.setdefault(key(x), []).append(x)
    return list(out.items())


def step_timings(M):
    """Each timing the stage's moves record, led by the process steps whose moves it times: "Process step 2.1: The stock
    is checked — 10 seconds of simulated work…". A timing on no step of the stage stands alone."""
    timed = [mv for mv in M["stage_moves"] if M["moves"][mv].get("timing")]
    out = []
    for t, g in grouped(timed, lambda mv: M["moves"][mv]["timing"]):
        on = [step_title(M["labels"], s) for s in M["steps"] if set(g) & set(re.findall(r"\bL\d+\b", s.get("source", "")))]
        out.append("; ".join(on) + " — " + t if on else t)
    return out


def failed_back(move):
    """Whether an alert naming this main move counts the cases its failure sent back to the party: `not created` says
    what happens when the move does not happen. Not for the move that creates the case (from `(none)`): a case that
    left by it was created, so an alert naming it counts cases created wrongly, which are in the application."""
    return (move.get("path") == "main" and move.get("recovery") == "not created"
            and state(move.get("from_state")) != "(none)")


def counted_moves(m):
    """The moves an alert says it counts, by id, in its `counted_moves` column (FILL-STEPS Step 11). The basis is
    free text: a move id in it is explanation, never read as a move the alert counts."""
    return list(dict.fromkeys(ids(m.get("counted_moves"))))


def guards(m):
    """The expectations a measure is evidence of, by id, from its `expectation` column: on an alert, those it guards.
    The basis is free text, and an id written there is never read as one."""
    return list(dict.fromkeys(ids(m.get("expectation"))))


def person_text_failures(M, drafted):
    """Errors for an alert whose text, as the person reviewing it reads it, carries an id, a file name or the kit's
    own vocabulary: its basis, the question it answers and the expectations it guards, each turned into words as the
    review renders them (brief.py alerts) and judged by the review's own term list, so the review can always be
    rendered. A measure's own name is the register's, and is let stand."""
    import brief
    R = M["R"]
    expect = {e.get("expectation_id"): e for e in R.get("expectations", [])}
    names = {brief.cont(as_reviewed(M, x["measure"])) for x in M["measures"].values()} | \
            {as_reviewed(M, x["measure"]) for x in M["measures"].values()}
    out = []
    for m in drafted:
        texts = [("basis", basis(m)), ("question_it_answers", m.get("question_it_answers"))] + \
                [(f"expectation {e}", expect[e].get("expectation")) for e in guards(m) if e in expect]
        for col, text in texts:
            hits = brief.review_terms(as_reviewed(M, text), names)
            if hits:
                out.append(f"measures.csv {m['handle']}: the {col} a person reads when reviewing this alert carries "
                           f"{', '.join(dict.fromkeys(hits))}: write it in their words, naming no table, file, id or "
                           "word of the kit's")
    return out


def as_reviewed(M, text):
    """Register text as the person reads it in a review: ids named, remedies and states in words, no proposal label."""
    return re.sub(r"\bproposed:\s*", "", states_said(M, remedy_words(unid(M, unpipe(text or ""))))).strip()


def expectation_failures(R, flow_id):
    """Errors on the register's ties to expectations.csv: an id in `measures.expectation` that is not a row of it, and
    an `objective` of the flow's expectations that is `proposed:` (an objective is only ever stated, never drafted)
    or has no `objective_source`."""
    err = []
    known = {e.get("expectation_id") for e in R.get("expectations", [])} - {"", None}
    for m in R["measures"]:
        unknown = [x for x in guards(m) if x not in known]
        if unknown:
            err.append(f"measures.csv {m['handle']}: `expectation` names {', '.join(unknown)}, not an expectation in "
                       "expectations.csv")
    for e in R.get("expectations", []):
        if e.get("flow") != flow_id:
            continue
        obj, i = norm(e.get("objective")), e.get("expectation_id", "?")
        if obj.lower().startswith("proposed:"):
            err.append(f"expectations.csv {i}: objective {obj!r} is proposed; an objective is only what a document "
                       "or a person states, so leave it blank where none is stated")
        elif obj and not norm(e.get("objective_source")):
            err.append(f"expectations.csv {i}: objective is set with no objective_source: cite where it is stated")
    return err


def exits_of(M, m):
    """The stage's moves a measure of cases leaving counts: those its `counted_moves` names."""
    return [mv for mv in counted_moves(m) if mv in M["stage_moves"]]


def counted_recoveries(M, m):
    """The recoveries of the cases a measure of cases leaving counts, from its `counted_moves`. The creating
    move's `not created` is left out: the cases that left by it were created."""
    moves = M["moves"]
    return {moves[mv].get("recovery", "") for mv in exits_of(M, m)
            if not (moves[mv].get("recovery") == "not created" and state(moves[mv].get("from_state")) == "(none)"
                    and moves[mv].get("path") == "main")} - {""}


def kind_of(R, m):
    """What kind of number a measure is: its form's meaning, else its agent question, else "not stated"."""
    forms = {f["form"]: f["what_it_captures"] for f in R["measure-forms"]}
    agent_qs = {a["agent_question"]: a["question"] for a in R["agent-questions"]}
    return forms.get(m.get("form", "")) or agent_qs.get(m.get("agent_question", "")) or "not stated"


def exists_today(m, lead):
    """Whether the system emits a measure: the emitting line, and what it counts wrong where `defect` says so."""
    if m.get("exists") != "yes":
        return "no, proposed"
    return lead + m.get("source_ref", "") + (f"; exists, but misleading: {m['defect']}" if m.get("defect") else "")


def side_move(m):
    """A move that leaves the case in the state it was in: it happens alongside, and nothing waits on it."""
    return state(m["to_state"]) == state(m["from_state"])


def from_states(M, step):
    return {state(M["moves"][mv]["from_state"]) for mv in M["step_moves"][str(step)]}


def to_states(M, step):
    return {state(M["moves"][mv]["to_state"]) for mv in M["step_moves"][str(step)] if not side_move(M["moves"][mv])}


def stage_states(M, stage_id):
    """The states a case can be in inside another stage: where its steps' moves start."""
    mvs = [x for s in M["R"]["steps"] if s["stage"] == stage_id for x in re.findall(r"\bL\d+\b", s.get("source", ""))]
    return {state(M["moves"][mv]["from_state"]) for mv in mvs if mv in M["moves"]}


def recorded(M):
    """The stage's states the application records, so cases can be found and grouped by them."""
    return [b for b in M["branch_states"] if b != "(none)" and not b.startswith("implicit:")]


BENIGN = ("nothing wrong", "expected condition", "self-healed", "degraded within tolerance", "already known")


def branch_of(M, r):
    return list(dict.fromkeys(state(M["moves"][mv]["from_state"]) for mv in ids(r["moves"]) if mv in M["stage_moves"]))


def shared(M, r):
    return r["hop"] == "needs" and len(branch_of(M, r)) > 1


def name(M, sid):
    return M["subj"][sid]["name"] if sid in M["subj"] else sid


def parts_of(r):
    """A failure mode's parts: one, or several for a sweep test (same hop, mode, part kind and ending)."""
    return ids(r.get("part"))


def part_names(M, r):
    names = [name(M, x) for x in parts_of(r)]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def escalated_part(M, r):
    """Whose owner a matching test escalates to: its part, or for a sweep each part that matched."""
    return part_names(M, r) if len(parts_of(r)) == 1 else "each part that matched"


def kind(sc):
    if sc.get("part_kind") == "person":
        return "Person"
    if sc.get("level") == "external dependency":
        return "External dependency"
    return "Application component" if sc.get("band") == "application" else "System component"


# ---------------------------------------------------------------- the coverage receipt

BUSINESS = ("business health", "business impact")
TIME_LIMIT_FORMS = ("cycle time", "completion rate")
# a stage's candidates (FILL-STEPS Step 9, item 2): the question, the layers and the forms that may answer it. The
# last, and the flow's own `the time limit`, are asked only of an element whose code sets a time limit (time_limit).
STAGE_ASKS = {
    "in the stage": (("business health",), ("backlog",)),
    "oldest's age": (("business health",), ("backlog",)),
    "time through": (("business health",), TIME_LIMIT_FORMS),
    "past the time limit": (BUSINESS, ("backlog",)),
}
STAGE_QUESTIONS = tuple(STAGE_ASKS)
TIME_LIMIT_QUESTIONS = ("the time limit", "past the time limit")


def time_limit(text):
    """A `bound_in_code` cell as written where it names a time limit the code sets, else "". The column is optional:
    few applications set their own timer, deadline or overdue rule. A cell that is empty, or that reads as none (it
    opens `none`, after an optional `none stated;` and an optional `proposed:`), names none. An earlier register's
    `none stated;` lead says only that no source states a limit; what follows it is read for the code's own."""
    t = (text or "").strip()
    body = re.sub(r"^(?:none stated\s*;\s*)?(?:proposed\s*:\s*)?", "", t, flags=re.I)
    return "" if not body or re.match(r"none\b", body, re.I) else t


STEP_QUESTIONS = ("did it happen", "was its outcome right")
# the run grain of an agent: the OpenTelemetry GenAI run and tool metrics, and a fallback to a person
RUN_QUESTIONS = ("run duration", "failed tool calls", "tokens", "refusals", "fallbacks to a person")


def norm(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def listed(text):
    """The `;`-separated values of a cell, each with its spacing made even."""
    return [norm(x) for x in (text or "").split(";") if norm(x)]


def decision_class(p, col="decision_point"):
    """`yes` or `no` from a participation row's `decision_point` cell (or its `reply_decision_point`), or None when it
    is not classed."""
    m = re.match(r"\s*(yes|no)\s*:", p.get(col) or "")
    return m.group(1) if m else None


REPLY = "reply"  # the operation of an agent's reply to a person: its turn, not a tool (FILL-STEPS Step 9)
ROUTE = re.compile(r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+\S|route\s+\S")


def route(op):
    """Whether an operation is written as an HTTP route (`POST /chatclient`, `route /api/genai/**`): what a caller
    invokes on a component, not a tool its agent's model calls. A handler of another kind is not recognised."""
    return bool(ROUTE.match(op or ""))


def chain_points(R, flow_id, runs, step_ids):
    """An agent's intermediate model outputs a later call relies on: its agent-system.csv action rows classed `yes:` in
    `decision_point`, keyed by the agent and the action's id, its place in the chain (`S03 AS2`)."""
    out = []
    for a in R["agent-system"]:
        if a.get("element") != "action" or a.get("agent") not in runs or decision_class(a) != "yes":
            continue
        serves = [x for x in ids(a.get("serves_business_step"))]
        if serves and not set(serves) & set(step_ids):
            continue
        out.append(a)
    return out


def chain_failures(R):
    """An agent-system.csv action row's `decision_point` is blank, `yes:` or `no:`; any other row leaves it blank."""
    err = []
    for a in R["agent-system"]:
        v = norm(a.get("decision_point"))
        if not v:
            continue
        if a.get("element") != "action":
            err.append(f"agent-system.csv {a.get('agent')} {a.get('id')}: decision_point is set on a {a.get('element')} "
                       "row; only an action of the agent's chain is classed")
        elif not decision_class(a):
            err.append(f"agent-system.csv {a.get('agent')} {a.get('id')}: class it in decision_point, `yes:` where a later "
                       "call of the chain relies on what this model call writes, `no:` or blank where not, and why "
                       f"(got {v!r})")
    return err


def agent_rows(R, flow_id):
    subj = {s["subject_id"]: s for s in R["subjects"]}
    stages = {st["stage"] for st in R["stages"] if st["flow"] == flow_id}
    step_ids = [s["step"] for s in R["steps"] if s["stage"] in stages]
    return [p for p in R["participation"] if p["step"] in step_ids and p.get("involvement") in ("performs", "supports")
            and subj.get(p["subject_id"], {}).get("part_kind") == "LLM agent"]


def point_key(p, op):
    return f"{p['subject_id']} {op}" if op else f"{p['subject_id']} at step {p['step']}"


def class_failures(R, flow_id):
    """An agent's participation row says whether its tool is a decision point: `yes:` or `no:` and why.
    A row not classed fails, and so does one agent's tool classed both ways, since the point is the agent and tool.
    Its reply is classed the same way, in `reply_decision_point`, on every agent row."""
    err, seen = [], {}
    for p in agent_rows(R, flow_id):
        if not decision_class(p, "reply_decision_point"):
            err.append(f"participation.csv {p['subject_id']} step {p['step']}: class the agent's reply in "
                       f"reply_decision_point, `yes:` where the person relies on it, as when it reports or explains a "
                       f"result, `no:` where it only confirms or asks, or replies to no person here, and why "
                       f"(got {p.get('reply_decision_point') or 'nothing'!r})")
        c = decision_class(p)
        if not c:
            err.append(f"participation.csv {p['subject_id']} step {p['step']}: class its tool as a decision point "
                       f"in decision_point, `yes:` where the agent chooses a value that becomes the case's outcome or "
                       f"a person's basis for it, `no:` where it records what a person stated or asked, and why "
                       f"(got {p.get('decision_point') or 'nothing'!r})")
            continue
        for op in listed(p.get("operation")) or [None]:
            seen.setdefault(point_key(p, op), {}).setdefault(c, []).append(p["step"])
    for key, by in seen.items():
        if len(by) > 1:
            err.append(f"participation.csv {key}: classed yes at step {', '.join(by['yes'])} and no at step "
                       f"{', '.join(by['no'])}; a decision point is the agent and its tool, so class it one way")
    return err


def receipt(R, flow_id):
    """The coverage receipt of one flow (FILL-STEPS Step 9), recomputed from the register: every element of every
    start-set with the question it is asked, and whether a candidate in measures.csv answers it.

    flow: its time limit, where its code sets one (time_limit), by a business health measure of the flow, counted on
    cases, of form cycle time or completion rate. stage: its candidates (STAGE_ASKS; past the time limit only where its
    code sets one), each by a measure of the stage, counted on cases, at the layer and
    form the question allows, marked for it in `receipt_question`. step that matters (a stage's exit, the flow's first
    step, a step with a step-impact row, a step an agent serves): did it happen, and was its outcome right, each by a
    business measure of the step marked for it in `receipt_question`. operation: an application measure of its
    component naming it in `operation`; a component whose row names no operation is its own element. system
    component: a technology measure of it. decision point (an agent with a tool its participation rows class `yes:`):
    each provisional agent question of grain `decision point`, by an agentic measure of the agent naming the tool in
    `operation`, or of the step where the agent's row names no tool. reply (an agent row whose `reply_decision_point`
    is `yes:`): the same questions, one decision point per agent and operation whose result it reports, by an agentic
    measure of the agent naming `reply` and that operation in `operation` (a row naming no tool: `reply` at its step). agent: each run metric (RUN_QUESTIONS), by an
    agentic measure of the agent answering a provisional question of grain `run`, marked for it in
    `receipt_question`."""
    subj = {s["subject_id"]: s for s in R["subjects"]}
    flow = next(f for f in R["flows"] if f["flow_id"] == flow_id)
    stages = sorted([s for s in R["stages"] if s["flow"] == flow_id], key=lambda s: int(s["order"]))
    ms = R["measures"]
    case = {sid for sid, s in subj.items() if s.get("part_kind") == "case"}
    out = []

    def add(element, question, what, by, at=()):
        # `by`: the measures that answer the element; covered when there is one, and `by` names them by handle
        out.append(dict(element=element, question=question, what=what, covered=bool(by),
                        by=[m.get("handle") or m.get("measure") for m in by], stages=sorted(set(at))))

    stage_of = {s["step"]: s["stage"] for s in R["steps"]}

    def on_cases(m):
        return m.get("subject_id") in case and m.get("counted_on") == "cases"

    steps = [s for s in R["steps"] if s["stage"] in {st["stage"] for st in stages}]
    own_cases = {s.get("business_subject") for s in steps}  # a case measure naming no flow counts only the flows of its case
    if time_limit(flow.get("bound_in_code")):
        add(flow_id, "the time limit", f"flow: {flow['name']}",
            [m for m in ms if on_cases(m) and not m.get("step") and not m.get("stage")
             and (m.get("flow") == flow_id or (not m.get("flow") and m.get("subject_id") in own_cases))
             and m.get("layer") == "business health" and m.get("form") in TIME_LIMIT_FORMS], [])
    step_ids = [s["step"] for s in steps]
    rows = [p for p in R["participation"] if p["step"] in step_ids]  # every component, whatever its involvement
    agents = agent_rows(R, flow_id)
    served = {p["step"] for p in agents}
    runs = list(dict.fromkeys(p["subject_id"] for p in agents))
    for a in R["agent-system"]:
        if a.get("element") in ("run", "action") and subj.get(a.get("agent"), {}).get("part_kind") == "LLM agent":
            hit = {x for x in ids(a.get("serves_business_step")) if x in step_ids}
            served |= hit
            if hit and a["agent"] not in runs:
                runs.append(a["agent"])
    impact = {r["step"] for r in R["step-impact"]}
    for st in stages:
        sid = st["stage"]
        mine = [m for m in ms if m.get("stage") == sid and not m.get("step") and on_cases(m)]
        for q, (layers, forms) in STAGE_ASKS.items():
            if q in TIME_LIMIT_QUESTIONS and not time_limit(st.get("bound_in_code")):
                continue
            add(sid, q, f"stage: {st['name']}", [m for m in mine if m.get("layer") in layers and m.get("form") in forms
                                                  and q in listed(m.get("receipt_question"))], [sid])
        M = build(R, flow_id, sid)
        for s in M["steps"]:
            n = s["step"]
            leaves = to_states(M, n) & set(M["exits"])
            first = any(state(M["moves"][mv]["from_state"]) == "(none)" for mv in M["step_moves"][n])
            if not (leaves or first or n in impact or n in served):
                continue
            for q in STEP_QUESTIONS:
                add(n, q, f"step: {s['name']}", [m for m in ms if m.get("step") == n and on_cases(m)
                                                  and m.get("layer") in BUSINESS
                                                  and q in listed(m.get("receipt_question"))], [sid])
    for c in dict.fromkeys(p["subject_id"] for p in rows):
        s = subj.get(c, {})
        if s.get("band") == "technology":
            add(c, "technology", f"system component: {s['name']}",
                [m for m in ms if m["subject_id"] == c and m.get("layer") == "technology"],
                [stage_of[p["step"]] for p in rows if p["subject_id"] == c])
        elif (s.get("band") == "application" and s.get("level") == "component"
              and s.get("part_kind") not in ("LLM agent", "person", "case")):
            mine = [p for p in rows if p["subject_id"] == c]
            app = [m for m in ms if m["subject_id"] == c and m.get("layer") == "application"]
            for op in dict.fromkeys(o for p in mine for o in listed(p.get("operation"))):
                add(f"{c} {op}", "application", f"operation of {s['name']}",
                    [m for m in app if listed(m.get("operation")) == [op]],  # one candidate per operation
                    [stage_of[p["step"]] for p in mine if op in listed(p.get("operation"))])
            if any(not listed(p.get("operation")) for p in mine):
                add(c, "application", f"component: {s['name']}, no operation named", app,
                    [stage_of[p["step"]] for p in mine if not listed(p.get("operation"))])
        elif s.get("band") == "application" and s.get("level") == "component" and s.get("part_kind") == "LLM agent":
            # an agent hosted by a component that also serves a route: the route keeps its application set
            app = [m for m in ms if m["subject_id"] == c and m.get("layer") == "application"]
            for op in dict.fromkeys(o for p in rows if p["subject_id"] == c for o in listed(p.get("operation"))):
                if route(op):
                    add(f"{c} {op}", "application", f"route of {s['name']}, the agent's own component",
                        [m for m in app if listed(m.get("operation")) == [op]],
                        [stage_of[p["step"]] for p in rows if p["subject_id"] == c and op in listed(p.get("operation"))])
    provisional = [q for q in R["agent-questions"] if q.get("status") == "provisional"]
    at_point = [q["agent_question"] for q in provisional if q.get("grain") == "decision point"]
    at_run = [q["agent_question"] for q in provisional if q.get("grain") == "run"]
    points = {}
    for p in agents:
        if decision_class(p) != "yes":
            continue
        for op in listed(p.get("operation")) or [None]:
            points.setdefault(point_key(p, op), dict(agent=p["subject_id"], op=op, steps=[]))["steps"].append(p["step"])
    for p in agents:  # a reply relied on is keyed by the operation whose result it reports, whatever its tool is classed
        if decision_class(p, "reply_decision_point") == "yes":
            for op in listed(p.get("operation")) or [None]:
                # reporting a tool's result: `reply to` the tool; a run a route starts: `reply on` the route
                key = (f"{p['subject_id']} {REPLY} {'on' if route(op) else 'to'} {op}" if op
                       else f"{p['subject_id']} {REPLY} at step {p['step']}")
                points.setdefault(key, dict(agent=p["subject_id"], op=op, steps=[], reply=True))["steps"].append(p["step"])
    for a in chain_points(R, flow_id, runs, step_ids):
        points.setdefault(f"{a['agent']} {a['id']}", dict(agent=a["agent"], op=a["id"], steps=[], chain=a["name"]))

    def answers(m, pt):
        if pt.get("reply"):
            named = listed(m.get("operation"))
            return (sorted(named) == sorted([REPLY, pt["op"]]) if pt["op"]
                    else named == [REPLY] and m.get("step") in pt["steps"])
        if pt["op"]:
            return listed(m.get("operation")) == [pt["op"]]
        return m.get("step") in pt["steps"] and REPLY not in listed(m.get("operation"))
    for key, pt in points.items():
        mine = [m for m in ms if m["subject_id"] == pt["agent"] and m.get("layer") == "agentic"]
        what = (f"model output of {subj[pt['agent']]['name']} a later call relies on: {pt['chain']}" if pt.get("chain")
                else f"{'reply' if pt.get('reply') else 'decision point'} of {subj[pt['agent']]['name']}, "
                f"at step{'s' if len(pt['steps']) > 1 else ''} " + ", ".join(pt["steps"]))
        for q in at_point:
            add(key, q, what, [m for m in mine if m.get("agent_question") == q and answers(m, pt)],
                [stage_of[n] for n in pt["steps"] if n in stage_of] or
                [stage_of[p["step"]] for p in agents if p["subject_id"] == pt["agent"]])
    if at_run:
        for agent in runs:
            mine = [m for m in ms if m["subject_id"] == agent and m.get("layer") == "agentic"
                    and m.get("agent_question") in at_run]
            for q in RUN_QUESTIONS:
                add(agent, q, f"runs of {subj[agent]['name']}", [m for m in mine if q in listed(m.get("receipt_question"))],
                    [stage_of[p["step"]] for p in agents if p["subject_id"] == agent])
    return out


def gap_rows(R, rec):
    """(errors, warnings, the elements the gaps account for, each with its `kind`). A gap counts only when it says
    why, where from, and which of GAP_KINDS it is; a `counted by` gap names, by id, the measure that counts it."""
    err, warn, gapped = [], [], {}
    asked = {(r["element"], r["question"]): r for r in rec}
    known = set(("the time limit",) + STAGE_QUESTIONS + STEP_QUESTIONS + RUN_QUESTIONS + ("application", "technology")) | {
        q["agent_question"] for q in R["agent-questions"]}
    handles = {m.get("handle") for m in R["measures"]} - {"", None}
    kinds = ", ".join(f"`{k}`" for k in GAP_KINDS)
    no_limit = {r.get("flow_id") or r.get("stage") for r in R["flows"] + R["stages"]
                if not time_limit(r.get("bound_in_code"))}
    for g in R["measure-gaps"]:
        key = (norm(g.get("element")), norm(g.get("question")))
        label = f"measure-gaps.csv {key[0]}, {key[1]}"
        if key[1] in TIME_LIMIT_QUESTIONS and key[0] in no_limit:
            warn.append(f"{label}: the code sets no time limit for {key[0]}, so the receipt does not ask this; the row "
                        "can be removed")
            continue
        if key[1] in vq.QUESTIONS and key[1] not in vq.GAPPABLE:
            err.append(f"{label}: {key[1]!r} is a view question that is {vq.CONTRACT[key[1]]}, so it takes no gap; "
                       f"the view questions that do: {', '.join(vq.GAPPABLE)}")
            continue
        if key[1] not in known and key[1] not in vq.GAPPABLE:
            err.append(f"{label}: question {key[1]!r} is not one the receipt asks ({', '.join(sorted(known))}; or a view question, {', '.join(vq.GAPPABLE)})")
            continue
        missing = [c for c in ("why", "source") if not norm(g.get(c))]
        if missing:
            err.append(f"{label}: no {' and no '.join(missing)}, so it does not count")
            continue
        kind = norm(g.get("kind")).lower()
        if kind not in GAP_KINDS:
            said = ("measure-gaps.csv has no `kind` column" if "kind" not in g else
                    f"`kind` is {g.get('kind') or 'empty'}, not one of the four")
            err.append(f"{label}: {said}, so it does not count; reading this row's reason, write one of {kinds}"
                       + (" in a `kind` column after `question`" if "kind" not in g else ""))
            continue
        elif kind == "counted by" and not handles.intersection(re.findall(r"[\w-]+", g.get("why") or "")):
            err.append(f"{label}: `kind` is `counted by`, and its reason names no measure of measures.csv by id, so it "
                       "does not count: name the measure that counts it")
            continue
        if key[1] in vq.GAPPABLE:  # a view question: its card and run_status.py read it, never the receipt
            why_not = vq.refusal(key[1], kind, g.get("why"), key[0], R["participation"])
            if why_not:
                err.append(f"{label}: {why_not}, so it does not count")
            continue
        if key not in asked:
            warn.append(f"{label}: names nothing the receipt of this flow asks")
        elif asked[key]["covered"]:
            warn.append(f"{label}: a candidate in measures.csv covers it, so the gap no longer holds")
        gapped[key] = kind
    return err, warn, gapped


CITATION = re.compile(r"(?<![\w./-])([\w.-]+)/[\w./-]*\.\w+:\d+")


def citation_failures(R):
    """Warnings for a register read from several repositories: a citation starts at the workspace root, with the
    folder of a repository `sources.csv` lists. A register that lists no repository is not checked."""
    repos = {norm(s.get("repository")) for s in R["sources"]} - {""}
    if not repos:
        return []
    stray = {}
    for t in TABLES:
        for r in R[t]:
            for v in r.values():
                for first in CITATION.findall(v or ""):
                    if first not in repos:
                        stray.setdefault(first, f"{t}.csv")
    return [f"{where}: a citation starts with {first}/, which is not a repository in sources.csv "
            f"({', '.join(sorted(repos))}); cite from the workspace root" for first, where in sorted(stray.items())]


def receipt_failures(R, flow_id, stage=None, measured=None):
    """A run that names a stage errors on an element of that stage or of the flow, and warns on one that belongs only
    to other stages: their own runs read their code, and error on it. `measured`, the set of stages the person chose
    to measure, takes the named stage's place: an element is owed when it belongs to the flow or to any measured stage
    (so a part shared by several stages is owed when one of them is measured). With no stage measured, the measure
    receipt is not run at all."""
    if measured is not None and not measured:
        return [], set(), [], []
    rec = receipt(R, flow_id)
    err, warn, gapped = gap_rows(R, rec)
    elsewhere = {(r["element"], r["question"]) for f in R["flows"] if f["flow_id"] != flow_id for r in receipt(R, f["flow_id"])}
    warn = [w for w in warn if not any(w.startswith(f"measure-gaps.csv {e}, {q}: names nothing") for e, q in elsewhere)]
    err = class_failures(R, flow_id) + chain_failures(R) + err
    for r in rec:
        if not r["covered"] and (r["element"], r["question"]) not in gapped:
            msg = (f"receipt: {r['element']} ({r['what']}), {r['question']}: no candidate in measures.csv and no "
                   "reason in measure-gaps.csv")
            if measured is not None and r["stages"] and not set(r["stages"]) & set(measured):
                warn.append(msg + f"; it belongs only to {', '.join(r['stages'])}, not measured in this run")
            elif measured is None and stage and r["stages"] and stage not in r["stages"]:
                warn.append(msg + f"; it belongs only to {', '.join(r['stages'])}, whose own run errors on it")
            else:
                err.append(msg)
    return rec, gapped, err, warn


# ---------------------------------------------------------------- the check

WATCHED = ("yes", "in the app only", "no", "unknown")
NO_INVENTORY = "no inventory reachable"


def watched_failures(m):
    """`watched`: whether operations monitoring collects an emitted measure,
    `yes`, `in the app only` (an application screen shows it, nothing collects it), `no` or `unknown`, with
    `watched_source`, the collection configuration or screen read. Only `unknown` may rest on
    `no inventory reachable`. Written only where `exists` is `yes`: a proposed measure is emitted by nothing."""
    w, src, h = norm(m.get("watched")), norm(m.get("watched_source")), m["handle"]
    if not w and not src:
        return []
    if m.get("exists") != "yes":
        return [f"measures.csv {h}: watched is set and exists is {m.get('exists') or 'blank'}; watched says whether "
                "anything collects an emitted measure, so a proposed measure has none"]
    if w not in WATCHED:
        return [f"measures.csv {h}: watched {w or 'blank'!r} is not one of {', '.join(WATCHED)}"]
    if not src:
        return [f"measures.csv {h}: watched is {w} with no watched_source: cite the scrape, collector or dashboard "
                f"configuration read, or write {NO_INVENTORY!r} with unknown"]
    if src.lower().startswith(NO_INVENTORY) and w != "unknown":
        return [f"measures.csv {h}: watched is {w} on {NO_INVENTORY!r}; only unknown may rest on it"]
    return []


# What counted_at may hold and what only the code knows. A quoted span after `line` or before `log line` is a log
# line's own words and is let through, whatever it holds; any other quoted span is refused, a space in it or not.
# Abbreviations (`e.g.`) and version numbers (`v7.2`) pass. Refused: anything backticked; a quoted word that is not a log line
# (`'Cancelled'`); a word joined by an underscore (`pg_stat_activity`); a word with a capital inside it that starts a
# new lower-case word (`orderItems`, `IntegrationEventLog`), a product spelled that way aside; a dotted word that is
# all lower case (`ordering.orders`), unless it is a file of a known kind, a host name or a number. A capital at the
# end of a name (`RabbitMQ`, `PostgreSQL`, `MongoDB`) and a dotted product name (`ASP.NET`, `Node.js`) pass.
QUOTED = re.compile(r"(?<!\w)(['\"])(.+?)\1(?!\w)")
WORD = re.compile(r"[\w.\-]+")
PRODUCTS = {"GitHub", "GitLab", "OpenTelemetry", "OpenSearch", "OpenShift", "JavaScript", "TypeScript", "WebSocket",
            "PayPal", "YouTube", "ServiceNow", "PagerDuty", "Datadog", "NewRelic", "AppDynamics", "CloudWatch",
            "SolarWinds", "BigPanda", "LogicMonitor", "DynamoDB", "eShop", "BigQuery", "NServiceBus", "MassTransit",
            "IdentityServer", "PowerShell", "WebLogic", "WebSphere", "BizTalk", "AutoSys", "SharePoint", "MuleSoft",
            "CyberArk", "webMethods", "TeamCity", "NetScaler", "LoadRunner", "SiteScope", "BladeLogic", "ZooKeeper",
            "WildFly", "NetBackup", "OpenStack", "BigFix", "ArcSight", "LogRhythm", "vSphere", "vCenter", "NetApp"}
PROSE = {"e.g", "i.e", "etc", "vs", "cf"}  # abbreviations, as WORD finds them with the last dot stripped
VERSION = re.compile(r"v?\d+(\.\d+)+")
FILE_KINDS = ("log", "txt", "json", "csv", "yaml", "yml", "xml", "conf", "ini", "out", "err")
HOST_ENDS = ("com", "net", "org", "io", "dev", "cloud", "local", "internal", "svc", "lan")


PRODUCT_NAMES = "product-names.csv"  # in the register: name, source (where the name is written so)


def vouched_products(rows):
    """The product names the register declares that the check may accept: each with a source, one word, and holding
    no dot, underscore, backtick or slash, so no declaration can let a code identifier through."""
    return {n for r in rows for n in [norm(r.get("name"))]
            if n and norm(r.get("source")) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9\-]*", n)}


def code_name(text, products=()):
    """The first part of `text` only the code knows, or None. `products`: names the register vouches for."""
    rest = []

    def lift(m):
        if (re.search(r"\blines?:?\s*$", text[:m.start()])
                or re.match(r"\s*(log\s+)?lines?\b", text[m.end():])):  # a log line: whatever its quotes hold
            return " "
        rest.append(m.group(0))
        return " "
    s = QUOTED.sub(lift, text)
    tick = re.search(r"`[^`]*`", s)
    if rest or tick:
        return rest[0] if rest else tick.group(0)
    for tok in WORD.findall(s):
        tok = tok.strip(".-")
        if tok.lower() in PROSE or VERSION.fullmatch(tok):
            continue
        if re.search(r"[A-Za-z0-9]_[A-Za-z0-9]", tok):
            return tok
        if re.search(r"[a-z][A-Z][a-z]", tok) and tok not in PRODUCTS and tok not in products:
            return tok
        parts = tok.split(".")
        if len(parts) > 1 and any(re.match(r"[A-Z][a-z]", p) for p in parts[1:]):  # schema.Table (`dbo.Orders`)
            return tok
        if len(parts) > 1 and not (any(re.search(r"[A-Z]", p) for p in parts) or parts[-1].lower() in FILE_KINDS
                                   or parts[-1].lower() in HOST_ENDS or all(p.isdigit() for p in parts)):
            return tok
    return None


def same_place_failures(measures):
    """An error per place two measures name in the same `counted_at` while their `exists` differ: the place either
    produces the signal today or does not."""
    by = {}
    for m in measures:
        at = norm(m.get("counted_at")).lower()
        if at and not at.startswith("not in the code"):
            by.setdefault(at, []).append(m)
    out = []
    for at, ms in by.items():
        if len({m.get("exists") for m in ms}) > 1:
            said = ", ".join(f"{m['handle']} {m.get('exists') or 'blank'}" for m in ms)
            out.append(f"measures.csv {', '.join(m['handle'] for m in ms)}: the same counted_at ({at}) and a different "
                       f"exists ({said}): a place either produces the signal today or does not, so set each from "
                       "its citation")
    return out


def counted_at_failures(m, products=()):
    """`counted_at`: the plain name of the place a measure is counted at, read from its own counted_how and
    citation. A row with a `source_ref` and no `counted_at` fails, and so does one naming a code identifier; a
    register whose measures.csv has no such column (made with an earlier release) is warned once by the check
    instead."""
    if "counted_at" not in m or not norm(m.get("source_ref")):
        return []
    at = norm(m.get("counted_at"))
    if not at:
        return [f"measures.csv {m['handle']}: it cites {norm(m['source_ref'])[:80]!r} and says no counted_at, so the "
                "screen cannot say where it is counted: write the plain name of the place that citation shows (the "
                "table and the database it lives in, the log and the service that writes it, or the system whose own "
                "status it is), or 'not in the code: ' and what it would take"]
    hit = code_name(at, products)
    if hit:
        return [f"measures.csv {m['handle']}: counted_at names {hit}, a name only the code knows, so a "
                "reader cannot find the place from it: write the plain name a reader knows without the code (the "
                "table and the database it lives in, the log and the service that writes it, or the system whose "
                f"own status it is). If {hit} is a product's own name, declare it in {PRODUCT_NAMES} with where "
                "its vendor or the sources write it so"]
    return []


def alert_check(M):
    """The alerting stage's check: the register's structure, and the measure and alert rules (basis, expectation,
    counted moves). It reads no failure-mode work: alerts are chosen from the measures alone."""
    return check(M, "alerts")


def runbook_check(M):
    """The runbooks stage's check: the register's structure, and the failure-mode coverage of every move and hop, the
    tests, what a responder should see, and the remedies."""
    return check(M, "runbooks")


def required_failure_rows(M, mv):
    """The failure-mode rows a stage's move owes, each with whether it is written: first, any row at all; then each
    hop kind's modes, each need's modes and each carrier. The check's errors and depth.json both read this list."""
    R, move = M["R"], M["moves"][mv]["move"]
    rows = [r for r in M["fm"] if mv in ids(r["moves"])]
    out = [dict(move=mv, what=f"{move}: any failure mode", met=bool(rows),
                error=f"lifecycle {mv} ({move}): no failure mode at all")]
    for h in M["hops"][mv]:
        for c in R["hop-failures"]:
            if c["hop_kind"] == h:
                out.append(dict(move=mv, what=f"{move}: {h}, {c['mode']}",
                                met=any(r["hop"] == h and r["mode"] == c["mode"] for r in rows),
                                error=f"lifecycle {mv}: hop {h}, mode {c['mode']!r} has no failure mode row (write "
                                      f"one, or ending 'not possible' with the citation)"))
    for need in M["needs"][mv]:
        for c in R["hop-failures"]:
            if c["hop_kind"] == "needs":
                out.append(dict(move=mv, what=f"{move}: needs {name(M, need)}, {c['mode']}",
                                met=any(r["hop"] == "needs" and need in parts_of(r) and r["mode"] == c["mode"]
                                        for r in rows),
                                error=f"lifecycle {mv}: need {need} ({name(M, need)}), mode {c['mode']!r} has no "
                                      f"failure mode row"))
    for part in M["carried"][mv]:
        out.append(dict(move=mv, what=f"{move}: carried by {name(M, part)}",
                        met=any(part in parts_of(r) for r in rows),
                        error=f"lifecycle {mv}: carrier {part} ({name(M, part)}) has no failure mode row"))
    return out


def check(M, part="all"):
    """(errors, warnings). An error fails the run. `part` "alerts" or "runbooks" keeps the register's structure and only
    that stage's own rules; "all" is both, in one pass."""
    alerts, runbooks = part in ("all", "alerts"), part in ("all", "runbooks")
    err, warn = [], []
    R, moves, sm = M["R"], M["moves"], M["stage_moves"]
    for tok in dict.fromkeys(M["unresolved"]):
        err.append(f"lifecycle.csv names {tok!r} in carried_by or needs, and no subjects.csv row is it: write its subject id")
    for s in M["steps"]:
        if not M["step_moves"][s["step"]]:
            msg = f"steps.csv step {s['step']}: its source names no lifecycle row (L..)"
            if vq.moves_excuse(s, R["measure-gaps"], R["participation"]):  # the one rule, as `step: moves` counts
                warn.append(msg + ", so it is drawn not assessed")
            else:
                err.append(msg + "; only a step no part carries may have none: one the reference model adds, or one "
                           "whose `step: moves` gap of kind `no record` cites the code read")
    for mv in moves:
        if mv not in sm and state(moves[mv]["from_state"]) in M["branch_states"]:
            err.append(f"lifecycle {mv} leaves {state(moves[mv]['from_state'])}, a state of {M['stage']['stage']}, and no step names it")
    for mv in sm:
        for h in M["hops"][mv]:
            if h.startswith("?"):
                err.append(f"lifecycle {mv}: travels_by hop {h[1:]!r} is not a hop kind in method/hop-failures.csv")
    for s in M["steps"]:
        perf = {p["subject_id"] for p in R["participation"] if p["step"] == s["step"] and p["involvement"] == "performs"}
        if R["participation"] and perf != set(M["performers"][s["step"]]):
            warn.append(f"participation.csv step {s['step']}: performs {sorted(perf)}; the lifecycle's carried_by gives "
                        f"{sorted(M['performers'][s['step']])}. The outputs follow the lifecycle")
    for r in R["subjects"]:
        to = r.get("to_id", "")
        if r.get("kind") != "relationship" or not to:
            continue
        for h in ids(r.get("step_hint")):
            mvs = M["step_moves"].get(h)
            # a call into a part that carries the step out is the step's own work; any other callee is one it needs
            if mvs and not any(x in M["needs"][mv] + M["carried"][mv]
                               for mv in mvs for x in (to, M["subj"].get(to, {}).get("part_of"))):
                warn.append(f"subjects.csv {r['subject_id']}: step_hint {h} names a step none of whose lifecycle moves "
                            f"needs {to} ({name(M, to)}): add it to that move's needs, or correct the step_hint")
    rel = [r for r in R["subjects"] if r.get("kind") == "relationship" and r.get("to_id")]
    for s in M["steps"]:
        for d in dict.fromkeys(d for mv in M["step_moves"][s["step"]] for d in M["needs"][mv]):
            if not any(s["step"] in ids(r.get("step_hint")) and d in (r["to_id"], M["subj"].get(r["to_id"], {}).get("part_of"))
                       for r in rel):
                warn.append(f"step {s['step']}: its lifecycle needs {d} ({name(M, d)}), and no interaction on that step "
                            f"reaches it, so the map draws no caller: list the step on the subjects.csv interaction "
                            f"that calls it, or correct the needs")
    reached = donts_of(M, R["failure-modes"]) if runbooks else set()
    for rid, rem in (M["remedies"].items() if runbooks else ()):
        if rem.get("kind") == "do not" and rid not in reached:
            warn.append(f"remedies.csv {rid}: a do not remedy that no failure mode uses, and no remedy they use names, "
                        "so no runbook shows it: name it in the remedy of the modes it cautions against")
    cat = {(h["hop_kind"], h["mode"]) for h in R["hop-failures"]}
    for r in (M["fm"] if runbooks else ()):
        i = r.get("mode_id", "?")
        if r["hop"] not in M["kinds"]:
            err.append(f"failure-modes.csv {i}: hop {r['hop']!r} is not a hop kind in method/hop-failures.csv")
        elif (r["hop"], r["mode"]) not in cat and r["mode"] != "other":
            err.append(f"failure-modes.csv {i}: mode {r['mode']!r} is not a {r['hop']} mode in method/hop-failures.csv")
        for mv in ids(r["moves"]):
            if mv not in moves:
                err.append(f"failure-modes.csv {i}: move {mv} is not in lifecycle.csv")
                continue
            allowed = M["needs"][mv] if r["hop"] == "needs" else M["carried"][mv] + M["needs"][mv]
            if len(parts_of(r)) == 1 and r["part"] not in allowed:
                err.append(f"failure-modes.csv {i}: part {r['part']} is not in lifecycle {mv}'s "
                           f"{'needs' if r['hop'] == 'needs' else 'carried_by or needs'}")
            if r["hop"] != "needs" and r["hop"] not in M["hops"][mv]:
                err.append(f"failure-modes.csv {i}: lifecycle {mv} does not travel by {r['hop']}")
        if len(parts_of(r)) > 1:  # a sweep: each of its parts serves at least one of its moves
            col = "needs" if r["hop"] == "needs" else "carried"
            for x in parts_of(r):
                if not any(x in M[col].get(mv, []) + (M["needs"].get(mv, []) if col == "carried" else [])
                           for mv in ids(r["moves"])):
                    err.append(f"failure-modes.csv {i}: part {x} of the sweep is in no listed move's "
                               f"{'needs' if r['hop'] == 'needs' else 'carried_by or needs'}")
        kinds = {M["subj"].get(x, {}).get("part_kind", "") for x in parts_of(r)}
        if len(kinds) > 1:
            err.append(f"failure-modes.csv {i}: a sweep test covers parts of one kind; its parts are "
                       f"{', '.join(sorted(k or 'blank' for k in kinds))}")
        if norm(r.get("order")) and not re.fullmatch(r"\d+", norm(r.get("order"))):
            err.append(f"failure-modes.csv {i}: order {r['order']!r} is not a whole number")
        ending = r.get("ending", "")
        if ending not in ENDINGS:
            err.append(f"failure-modes.csv {i}: ending {ending!r} is not one of {', '.join(ENDINGS)}")
            continue
        if r.get("recovery", "") not in RECOVERY:
            err.append(f"failure-modes.csv {i}: recovery {r['recovery']!r} is not one of {', '.join(x for x in RECOVERY if x)}")
        if ending == "not possible":
            if not r.get("failure", "").startswith("not possible here:"):
                err.append(f"failure-modes.csv {i}: a mode ruled out writes 'not possible here:' and the citation in failure")
            continue
        for col in ("test", "measures", "expected", "seen"):
            if not r.get(col):
                err.append(f"failure-modes.csv {i}: no {col}")
        for h in ids(r.get("measures")):
            if h not in M["measures"]:
                err.append(f"failure-modes.csv {i}: measure {h} is not in measures.csv")
        rem = M["remedies"].get(r.get("remedy", ""))
        if r.get("remedy") and not rem:
            err.append(f"failure-modes.csv {i}: remedy {r['remedy']} is not in remedies.csv")
        if ending == "restore" and (not rem or rem["kind"] not in RESTORING):
            err.append(f"failure-modes.csv {i}: ending restore needs a remedy of kind {', '.join(RESTORING)}")
        if r.get("recovery") == "stranded" and (not rem or rem["kind"] not in ("re-drive", "none exists")):
            err.append(f"failure-modes.csv {i}: the case is stranded, so its remedy is a re-drive or a stated "
                       f"'none exists', not {rem['kind'] if rem else 'nothing'}")
        if r.get("recovery") == "stranded" and ending not in ("restore", "cannot restore"):
            err.append(f"failure-modes.csv {i}: the case is stranded, so its ending is restore or cannot restore")
    for m in R["measures"]:
        if norm(m.get("defect")) and m.get("exists") != "yes":
            err.append(f"measures.csv {m['handle']}: defect is set and exists is {m.get('exists') or 'blank'}; a defect "
                       "says what an emitted measure counts wrong, so a proposed measure has none: say what it must "
                       "count in counted_how")
        err += watched_failures(m)
        err += counted_at_failures(m, R.get("products", ()))
    err += same_place_failures(R["measures"])
    if R["measures"] and not any("counted_at" in m for m in R["measures"]):
        warn.append("measures.csv has no counted_at column (a register made with an earlier version of this kit), so "
                    "the screen cannot say where any measure is counted: add it, with its header from "
                    "register-template/measures.csv, and " + cv.EFFECT[("measures", "counted_at")])
    handles ={m["handle"] for m in M["alerts"]}
    if runbooks:
        err += old_remedy_id_failures(R)
    for rid, rem in (M["remedies"].items() if runbooks else ()):
        if rem.get("kind") not in REMEDY_KINDS:
            err.append(f"remedies.csv {rid}: kind {rem.get('kind')!r} is not one of {', '.join(REMEDY_KINDS)}")
        for col in REMEDY_TEXT:
            text = rem.get(col) or ""
            for x in dict.fromkeys(re.findall(r"§\s*\d+", text)):
                err.append(f"remedies.csv {rid}: {col} names a runbook section ({x}); the register does not know the "
                           "runbook's sections: write the action ('Escalate') and the runbook points it at its section")
            named = [h for h in dict.fromkeys(re.findall(r"\bM\d+\b", text)) if h in handles]
            if named:
                err.append(f"remedies.csv {rid}: {col} names {', '.join(named)}, a measure proposed for alerting; a "
                           "remedy is written once for every alert whose tests end at it, so its text names no alert: "
                           "say what to record in words that hold for any of them")
    for r in (M["fm"] if runbooks else ()):
        for col in ("failure", "test", "expected", "seen"):
            for x in dict.fromkeys(re.findall(r"§\s*\d+", r.get(col) or "")):
                err.append(f"failure-modes.csv {r.get('mode_id', '?')}: {col} names a runbook section ({x}); the "
                           "register does not know the runbook's sections")
    for mv in (sm if runbooks else ()):
        owed = required_failure_rows(M, mv)
        if not owed[0]["met"]:  # no failure mode at all on the move: that one error stands for the rest
            err.append(owed[0]["error"])
            continue
        err += [o["error"] for o in owed[1:] if not o["met"]]
    for b in (M["branch_states"] if runbooks else ()):
        seen = {}
        for r in M["fm"]:
            if r.get("ending") == "not possible" or b not in branch_of(M, r):
                continue
            key = (tuple(sorted(ids(r["measures"]))), r["seen"].strip().lower())
            if key in seen:
                err.append(f"failure-modes.csv {seen[key]} and {r['mode_id']}: same measures and same 'seen' in the "
                           f"{b} branch, so a responder cannot tell them apart")
            seen.setdefault(key, r["mode_id"])
    sid = M["stage"]["stage"]
    # Which measures alert, and at which level, is the register's to say: an alert is drafted on every stage its
    # measure reaches (`reach`). Every drafted alert, at any level, meets the basis and expectation checks: those this
    # stage's outputs hold, and those that reach no stage at all, which no stage's outputs would hold.
    here = stage_alerts(M)
    drafted = (here + [m for m in M["alerts"] if not M["reach"].get(m["handle"])]) if alerts else []
    for m in drafted:
        if level(m) != "stage" or m.get("counted_on") != "cases":
            where = M["reach"].get(m["handle"])
            warn.append(f"note: measures.csv {m['handle']}: proposed for alerting on its {level(m)}, counted on "
                        f"{m.get('counted_on') or 'nothing stated'}: " +
                        ("drafted on every stage it reaches (" + ", ".join(s for s, _ in where) + "), and each stage's "
                         "runbook works its own tests for it" if where else
                         "it reaches no stage of the register, so no alert page or runbook entry holds it"))
    if alerts and not here:
        warn.append(f"note: no alert is proposed on stage {sid}, its steps, the parts they use or its flow, so no ALERT "
                    "page is written for it and its runbook says so. Whether to alert, and on what, is the team's "
                    "decision")
    for m in drafted:
        if not basis(m):
            warn.append(f"measures.csv {m['handle']}: proposed for alerting with no basis: write `yes:` and the "
                        "expectation the alert guards and why it is proposed")
        if not guards(m):
            err.append(f"measures.csv {m['handle']}: proposed for alerting, and its `expectation` is empty: name, by id "
                       "and separated by `;`, the expectations.csv rows (e..) the alert guards. A register made with an "
                       "earlier version of this kit has no such column or table: add expectations.csv and the column, "
                       "and fill them from the expectation the basis names")
    err += person_text_failures(M, drafted)
    # the stage's own counts of cases: the moves they count, and what they cannot see
    mine = [m for m in M["alerts"] if m.get("stage") == sid and m.get("counted_on") == "cases"]
    stands = ("A warning whose reason the basis gives stands, and does not stop the outputs being written")
    for m in (mine if alerts else ()):
        named = counted_moves(m)
        if m.get("form") not in WAITING and not named:
            err.append(f"measures.csv {m['handle']}: counts cases leaving the stage, and its `counted_moves` is empty: "
                       "list, by id and separated by `;`, the lifecycle moves (L..) whose cases it counts, so the "
                       "runbook can send its responder to a branch")
        unknown = [mv for mv in named if mv not in moves]
        if unknown:
            err.append(f"measures.csv {m['handle']}: `counted_moves` names {', '.join(unknown)}, not a move in "
                       "lifecycle.csv")
        other = [mv for mv in named if mv in moves and mv not in sm]
        if other:
            err.append(f"measures.csv {m['handle']}: `counted_moves` names {', '.join(other)}, not a move of stage "
                       f"{sid}: an alert of the stage counts cases leaving by the stage's own moves")
    for m in (mine if runbooks else ()):
        counts = counted_recoveries(M, m)
        if m.get("form") in WAITING or not counts:
            continue
        blind = [r["mode_id"] for r in entry_modes(M, m) if r.get("recovery") and r["recovery"] not in counts]
        if blind:
            warn.append(f"measures.csv {m['handle']}: its runbook entry works {', '.join(blind)}, whose recovery is "
                        f"{' or '.join(sorted({r['recovery'] for r in M['fm'] if r['mode_id'] in blind}))}, and the "
                        f"moves its `counted_moves` names count only cases whose recovery is {' or '.join(sorted(counts))}: it "
                        "cannot see what those tests explain. Name the measure that does in their `measures`, or say "
                        "why in the basis")
    parked = [mv for mv in sm if moves[mv].get("from_kind") == "park"] if alerts else []
    waits_only = alerts and mine and all(m.get("form") in WAITING for m in mine)
    if parked and mine and not any(m.get("form") in WAITING for m in mine):
        warn.append(f"stage {sid}: cases wait in it ({', '.join(parked)} leave a park), and no measure proposed for "
                    "alerting counts cases waiting too long. If cases waiting too long breaks the "
                    "expectation, propose one. "
                    + stands)
    if not parked and waits_only:
        warn.append(f"stage {sid}: no move leaves a park, so a case waits in it only while an act hangs, and every "
                    "measure proposed for alerting counts cases waiting. Propose one on the cases failing back or left "
                    "stranded, or say in "
                    "the basis why waiting is the loss that matters. " + stands)
    leaving = [mv for mv in sm if moves[mv].get("path") in ("alternative", "exception")
               or moves[mv].get("recovery") == "not created"] if alerts else []
    if leaving and waits_only:
        warn.append(f"stage {sid}: cases leave it by alternative or exception endings, or are failed back "
                    f"({', '.join(leaving)}), and every measure proposed for alerting counts cases "
                    "waiting. If cases leaving that way breaks the expectation, propose a measure of them. An "
                    "ending the party wants (their own cancellation, a rule's refusal) needs no alert. " + stands)
    _, _, r_err, r_warn = receipt_failures(R, M["flow"]["flow_id"], M["stage"]["stage"], M.get("measured"))
    bounds = cv.bound_failures({"flows": [M["flow"]], "stages": [M["stage"]]})
    return (err + bounds + expectation_failures(R, M["flow"]["flow_id"]) + r_err,
            warn + r_warn + citation_failures(R))


# ---------------------------------------------------------------- STRUCTURE.md

def q(s):
    return (s or "").replace('"', "'").replace("\\|", "/")


def shown(st):
    if st == "(none)":
        return "the case is created"
    return st.removeprefix("implicit:").strip() + " (not recorded)" if st.startswith("implicit:") else st


def said(st):
    """A state as the runbook and the alerts name it: in the words the stage cards use (`state_name`), "the case is
    created" for a case not yet in one, and "(not recorded)" after a state the code does not record."""
    import stage_flow_views as sfv  # state_name lives with the cards; imported here, as it imports this module
    if st == "(none)":
        return "the case is created"
    if st.startswith("implicit:"):
        return sfv.state_name(st.removeprefix("implicit:").strip()) + " (not recorded)"
    return sfv.state_name(st)


def to_said(st):
    """A state a move leads into, as said: a move into no state leaves the case in none."""
    return "no state" if st == "(none)" else said(st)


def once(items):
    """A list as the reader sees it: a line several register rows write alike (moves that share an outcome) once."""
    return list(dict.fromkeys(items))


def edge_label(M, step, st, first=False, out=False):
    key = "to_state" if out else "from_state"
    paths = {M["moves"][mv]["path"] for mv in M["step_moves"][str(step)] if state(M["moves"][mv][key]) == st}
    if out or "main" in paths or not paths:
        word = "enters at" if first else "then"
    else:
        word = "or, " + "/".join(sorted(paths))
    return q(f"{word}: {shown(st)}")


def structure(M):
    flow, stage, stages, subj = M["flow"], M["stage"], M["stages"], M["subj"]
    caps = [c["name"] for d in ids(flow.get("delivers")) for c in M["R"]["capabilities"] if c["capability_id"] == d]
    t = ["flowchart TD"]
    t.append(f'  FL["Intended flow<br/><b>{q(flow["name"])}</b><br/>one case: '
             f'{q(strip_parens(flow["case"]).split(":")[0].strip())}"]')
    for k, c in enumerate(caps):
        t += [f'  CAP{k}["Capability<br/><b>{q(c)}</b>"]', f"  CAP{k} -->|delivered by| FL"]
    prev = "FL"
    for s in stages:
        t += [f'  {s["stage"]}["Stage {s["order"]} of {len(stages)}<br/><b>{q(s["name"])}</b>"]',
              f'  {prev} -->|{"first stage" if prev == "FL" else "then"}| {s["stage"]}']
        prev = s["stage"]
    sid = stage["stage"]
    for s in M["steps"]:
        na = "" if M["step_moves"][s["step"]] else "<br/>not assessed: no lifecycle row carries it"
        t.append(f'  P{s["step"]}["{M["labels"].get(s["step"]) or "Process step " + s["step"]}: <b>{q(s["name"])}</b>{na}"]')
    for e in M["entries"]:
        for s in M["steps"]:
            if e in from_states(M, s["step"]):
                t.append(f'  {sid} -->|{edge_label(M, s["step"], e, first=True)}| P{s["step"]}')
    for a in M["steps"]:
        for b in M["steps"]:
            if a["step"] == b["step"]:
                continue
            for st in sorted(to_states(M, a["step"]) & from_states(M, b["step"])):
                t.append(f'  P{a["step"]} -->|{edge_label(M, b["step"], st)}| P{b["step"]}')
    for k, x in enumerate(M["exits"]):
        nxt = next((s for s in stages if s["stage"] != sid and x in stage_states(M, s["stage"])), None)
        label = f"leaves the stage: {shown(x)}" + (f"<br/>into {nxt['name']}" if nxt else "<br/>the case ends here")
        t.append(f'  X{k}(["{q(label)}"])')
        for s in M["steps"]:
            if x in to_states(M, s["step"]):
                t.append(f'  P{s["step"]} -->|{edge_label(M, s["step"], x, out=True)}| X{k}')
    for c in M["parts"]:
        sc = subj[c]
        t.append(f'  {c}["{kind(sc)}<br/><b>{q(sc["name"])}</b><br/>{q(sc.get("part_kind", ""))}"]')
    for s in M["steps"]:
        for c in M["performers"][s["step"]]:
            t.append(f'  P{s["step"]} ==>|done by| {c}')
        for c in M["supporters"][s["step"]]:
            t.append(f'  P{s["step"]} -.->|needs| {c}')
    t += ["  classDef on stroke-width:3px", f"  class {sid} on", "  classDef off opacity:0.45"]
    others = [s["stage"] for s in stages if s["stage"] != sid]
    if others:
        t.append("  class " + ",".join(others) + " off")
    key = ("**How to read it.** Solid arrows between process steps follow the case: each is labelled with the state the case is "
           "in when the next process step starts. Where several arrows leave one process step, they are alternatives: one case takes one "
           "of them. **Done by** is every part that carries the process step out; **needs** is a part it cannot complete without "
           "that does not itself carry the process step out. Process steps are numbered within their stage, the same in every stage file.")
    side = [s["step"] for s in M["steps"] if M["step_moves"][s["step"]]
            and all(side_move(M["moves"][mv]) for mv in M["step_moves"][s["step"]])]
    if side:
        key += (" " + "; ".join(step_title(M["labels"], s) for s in M["steps"] if s["step"] in side) +
                (" changes" if len(side) == 1 else ": each changes") +
                " no state of the case: it happens alongside, and nothing waits on it.")
    return (f"# {flow['name']}: stage {stage['order']} of {len(stages)}, {stage['name']}\n\n{key}\n\n"
            "```mermaid\n" + "\n".join(t) + "\n```\n")


# ---------------------------------------------------------------- MEASURES.md

def mlabel(m, paging):
    mark = " **proposed alert**" if m["handle"] in paging else ""
    return f'{m["handle"]} {m["measure"]} ({"exists" if m.get("exists") == "yes" else "proposed"}){mark}'


def measures(M):
    R, subj, stage = M["R"], M["subj"], M["stage"]
    sid = stage["stage"]
    step_ids = [s["step"] for s in M["steps"]]
    rows = [(f"**Stage {stage['order']}: {stage['name']}**", [m for m in R["measures"] if m.get("stage") == sid])]
    for s in M["steps"]:
        doers = ", ".join(name(M, c) for c in M["performers"][s["step"]]) or "nothing"
        rows.append((f"{step_title(M['labels'], s)} (done by {doers})",
                     [m for m in R["measures"] if m.get("step") == s["step"]
                      and subj.get(m["subject_id"], {}).get("part_kind") == "case"]))
    for c in M["parts"]:
        if subj[c].get("part_kind") == "person":
            continue
        rows.append((f"{kind(subj[c])}: {subj[c]['name']}",
                     [m for m in R["measures"] if m["subject_id"] == c and m.get("step", "") in step_ids + [""]
                      and not m.get("stage")]))
    agentic = any(m["layer"] == "agentic" for _, ms in rows for m in ms)
    layers = LAYERS + (["agentic"] if agentic else [])
    head_cells = HEAD + (["Agentic<br>did the agent judge right?"] if agentic else [])
    md = ["| | " + " | ".join(head_cells) + " |", "|---|" + "---|" * len(head_cells)]
    marked = {m["handle"] for m in stage_alerts(M)}
    for label, ms in rows:
        md.append("| " + label + " | " + " | ".join("<br>".join(mlabel(m, marked) for m in ms if m["layer"] == lay) or "none"
                                                     for lay in layers) + " |")
    how = ["| Measure | Answers | Kind | Counted on | Counted how | Exists today |", "|---|---|---|---|---|---|"]
    for _, ms in rows:
        for m in ms:
            how.append(f'| {m["handle"]} {m["measure"]} | {m.get("question_it_answers", "")} | '
                       f'{cell(kind_of(R, m))} | {m.get("counted_on", "")} | '
                       f'{m.get("counted_how", "")} | '
                       f'{exists_today(m, "yes: ")} |')
    paging = [m["handle"] for m in stage_alerts(M)]
    shown_ = {m["handle"] for _, ms in rows for m in ms}
    limit = time_limit(stage.get("bound_in_code"))
    head = [f"# {M['flow']['name']}: stage {stage['order']} of {len(M['stages'])}, {stage['name']}: where each measure is counted", "",
            *([f"**Expected of the stage:** {limit.removeprefix('proposed: ')}. The time limit is the operators' to set.", ""]
              if limit else []),
            (f"**Proposed for alerting:** " + ", ".join(
                h + ("" if h in shown_ else f" (on the {level(M['measures'][h])})") for h in paging) +
             (", the measures marked **proposed alert** below. " if set(paging) <= shown_ else
              ", marked **proposed alert** below where the table holds it. ") +
             f"The alert{'s are' if len(paging) > 1 else ' is'} in [ALERT.md](ALERT.md); when "
             f"{'one' if len(paging) > 1 else 'it'} fires, follow its own entry in RUNBOOK.md (" +
             ", ".join(f"[{h}]({entry_link(M['measures'][h])})" for h in paging) + "). Every other measure is "
             "read by the runbook's tests where ALERT.md lists it as a companion measure." if paging else
             "**Proposed for alerting:** nothing. No alert is proposed on this stage, its process steps, the parts they use or "
             "the flow, so there is no alert page for it. Whether to alert, and on what, is the team's decision."), "",
            "Process steps are numbered within their stage, the same in every stage file. A process step's row holds the measures counted on the case at that process step; each "
            "component's row holds its own.", ""]
    return "\n".join(head) + "\n" + "\n".join(md) + "\n\n## How each measure is counted\n\n" + "\n".join(how) + "\n"


# ---------------------------------------------------------------- ALERT.md

def alert_grouping(M, m, lead=True):
    """Which cases an alert's runbook entry works, and by what it groups them."""
    moves = M["moves"]
    lead = f"**{m['handle']}** " if lead else ""
    if m.get("counted_on") != "cases":
        return lead + (f"None: it is counted on {m.get('counted_on') or 'what it counts'}, not cases, so its runbook "
                       "entry works every state's tests of this stage.")
    if m.get("form") not in WAITING:
        ex = exits_of(M, m)
        kinds = {failed_back(moves[mv]) for mv in ex}
        how = ("where the case failed back" if kinds == {True} else "the case left by" if kinds == {False}
               else "where the case failed back or left")
        return lead + ((f"By the move {how}: " + "; ".join(
            f"{', '.join(g)} from {said(b)}" for b, g in grouped(ex, lambda mv: state(moves[mv]["from_state"]))) +
            ". Its runbook entry works that state's tests.") if ex else
            "None: its `counted_moves` names no move the cases leave by, so its runbook entry works every state's tests.")
    return lead + (("By the state the case is in: " + ", ".join(said(b) for b in M["branch_states"]) +
                    ". Its runbook entry groups the cases by state and works each state's tests.") if recorded(M) else
                   ("None. The states of this stage (" + ", ".join(said(b) for b in M["branch_states"]) +
                    ") are not recorded, so cases cannot be grouped by state; its runbook entry works every "
                    "state's tests in order."))


def not_emitted(m):
    """Said beside an alert's basis when its measure does not exist today: its query finds nothing to count."""
    return "" if m.get("exists") == "yes" else (
        "This measure is not emitted yet; deployed as written, the alert fires on No data until it is.")


NO_DATA_WHAT = ("If it shows No data rather than a count, that is why: it counts no case, so there is nothing to work "
                "here; note it for the hand-over and close.")


def and_not_emitted(text, m):
    """An alert's basis, then the not-emitted line as its own sentence where it applies."""
    line = not_emitted(m)
    return text + (("" if re.search(r"(?:[.!?]|</\w+>)\s*$", text) else ".") + " " + line if line else "")  # HTML ends a block


def elsewhere(paging):
    """Whether any of a stage's alerts is on another level than the stage: then each says where it is placed."""
    return any(level(m) != "stage" for m in paging)


def symptom(paging):
    """What each alert fires on: cases, or the count of a part, a step or the flow it is a measure of."""
    if all(m.get("counted_on") == "cases" for m in paging):
        return ("It fires on what happens to cases, not on any component's errors. Telling causes apart is the "
                "runbook's job.")
    return "<br>".join(f"**{m['handle']}** fires on " + (
        "what happens to cases" if m.get("counted_on") == "cases" else
        f"its {level(m)}'s count of {m.get('counted_on') or 'what it counts'}, which is not a count of cases") +
        "." for m in paging) + "<br>Telling causes apart is the runbook's job."


def alert(M):
    stage, sid, moves = M["stage"], M["stage"]["stage"], M["moves"]
    paging = stage_alerts(M)
    stranded = [mv for mv in M["stage_moves"] if moves[mv].get("recovery") == "stranded"]
    timings = [f"{', '.join(g)}: {t}" for t, g in grouped([mv for mv in M["stage_moves"] if moves[mv].get("timing")],
                                                          lambda mv: moves[mv]["timing"])]
    waiting = [m for m in paging if m.get("form") in WAITING and m.get("counted_on") == "cases"]
    rows = [("The question it answers", "<br>".join(f"**{m['handle']}** {m.get('question_it_answers', '')}" for m in paging)),
            ("What it counts", "<br>".join(f"**{m['handle']}** {m['measure']}: {m.get('counted_how', '')} "
                                           f"(counted on {m.get('counted_on')})" for m in paging)),
            ("Why it is proposed", "<br>".join(
                f"**{m['handle']}** " + and_not_emitted(basis(m) or "not stated in the register (`measures.csv` → `alert`)", m)
                for m in paging))]
    if elsewhere(paging):
        rows.insert(0, ("Where it is placed", "<br>".join(f"**{m['handle']}** {placed(M, m)}" for m in paging)))
    if stranded:
        rows.append(("Cases stranded", "A case is stranded, with nothing in the application to move it on, when one of "
                                       "these moves does not happen: " + "; ".join(
                                           ", ".join(f"{mv} {move_name(M, mv)}" for mv in g) + f" ({why})"
                                           for why, g in grouped(stranded, lambda mv: moves[mv]["if_not"]))))

    rows += [("Runbook link", RUNBOOK_LATER if M.get("runbook_pending") else
              "<br>".join(f"**{m['handle']}** [its entry in RUNBOOK.md]({entry_link(m)})" for m in paging)),
             ("Grouping", "<br>".join(alert_grouping(M, m, len(paging) > 1) for m in paging)),
             ("Threshold", THRESHOLD),
             ("No data", "Each alert also fires when its measure cannot be counted: the query or search itself fails for "
                         "longer than the window. A count of events that finds none in a window is zero, not missing data. "
                         "A count fails when what it is read from is down, and then cases go wrong unseen. What it "
                         "counts says where each is read.")]
    if waiting:
        limit = time_limit(stage.get("bound_in_code"))
        rows.append(("Time limit", f"*Operator value.* For {', '.join(m['handle'] for m in waiting)}, how old a waiting "
                                  "case may be is the operators' value"
                                  + (f"; the stage's time limit in the code: {limit}" if limit else ".")))
    rows += [("Window", "*Operator value, not set here.* How long the condition must hold before the alert fires." +
              (" What the design assumes about time: " + "; ".join(timings) if timings else "")),
             ("Symptom, not cause", symptom(paging)),
             ("Exists today", "; ".join(f"{m['handle']}: {exists_today(m, 'yes, ')}" for m in paging))]
    used = list(dict.fromkeys(h for r in M["fm"] if r.get("ending") != "not possible" for h in ids(r["measures"])))
    pending = M.get("runbook_pending")
    out = [f"# Proposed alert{'s' if len(paging) > 1 else ''} for \"{stage['name']}\": "
           + "; ".join(f"{m['handle']} {m['measure']}" for m in paging), "",
           f"**Stage {stage['order']} of {len(M['stages'])}:** {stage['name']}, in flow {M['flow']['name']}. Its process steps: "
           f"{'; '.join(step_title(M['labels'], s) for s in M['steps'])}. " +
           (("Each measure below is its own alert. " if len(paging) > 1 else "") + RUNBOOK_LATER if pending else
            ("Each measure below is its own alert; whichever fires, follow its own entry in [RUNBOOK.md](RUNBOOK.md)"
             if len(paging) > 1 else "When it fires, follow its entry in [RUNBOOK.md](RUNBOOK.md)") +
            " (the runbook link below)."), "",
           "| | |", "|---|---|"] + [f"| **{k}** | {v} |" for k, v in rows]
    if not pending:
        out += ["", "## Companion measures", "", "Read by the runbook's tests, not proposed for alerting:", ""]
        out += once(f"- {h} {M['measures'][h]['measure']}" for h in used
                    if h in M["measures"] and h not in [m["handle"] for m in paging])
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- RUNBOOK.md
#
# One short entry per proposed alert, which the alert's runbook link points at, then one shared section for the
# stage. Every test is written once, in the shared section; an entry names the tests it runs, bounded to its own
# cases and window, and says what a match on each means.

def slug(heading):
    """The anchor a markdown renderer gives a heading: lower case, punctuation dropped, spaces as hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


# The shared section's subsections, in the order they are written. Every reference to one is generated from this list,
# so a reference cannot point at a section that is not written.
SECTIONS = (("stage", "The stage on one page"), ("stake", "What is at stake"), ("start", "Before you start"),
            ("tests", "Every test, once"), ("shared", "Causes the alerts share"), ("restore", "Restore"),
            ("close", "Close"), ("escalate", "Escalate or declare"), ("outside", "Outside this runbook"),
            ("links", "Links"), ("about", "About this runbook"))


def sec(key):
    return f"S{[k for k, _ in SECTIONS].index(key) + 1}"


def head(key):
    return f"### {sec(key)}. {dict(SECTIONS)[key]}"


def ref(key, text=None):
    return f"[{text or sec(key)}](#{slug(head(key).lstrip('# '))})"


def stage_alerts(M):
    """The alerts this stage's outputs hold: every proposed alert whose measure reaches the stage, at whatever level
    the register puts it (the stage, one of its steps, a part its steps use, or its flow)."""
    sid = M["stage"]["stage"]
    return [m for m in M["alerts"] if any(st == sid for st, _ in M["reach"].get(m["handle"], []))]


def entry_heading(m):
    return f"Alert {m['handle']}: {m['measure']}"


def entry_link(m):
    return "RUNBOOK.md#" + slug(entry_heading(m))


def live(M):
    return [r for r in M["fm"] if r.get("ending") != "not possible"]


def entry_states(M, m):
    """The states an alert's cases are in, or left from: every state the stage holds cases in, for a count of cases
    waiting or one whose `counted_moves` names no move; else the states the moves it counts leave from."""
    ex = exits_of(M, m)
    if m.get("form") in WAITING or not ex:
        return list(M["branch_states"])
    return list(dict.fromkeys(state(M["moves"][mv]["from_state"]) for mv in ex))


def owned_elsewhere(M, m, r):
    """A test that reads another proposed alert's count, and not this one's, is that alert's own test: run for this
    alert it lists the other alert's cases."""
    reads = set(ids(r["measures"]))
    return m["handle"] not in reads and bool(reads & ({a["handle"] for a in stage_alerts(M)} - {m["handle"]}))


def needers(M):
    """{part: the parts whose interactions in subjects.csv reach it}."""
    out = {}
    for s in M["subj"].values():
        if s.get("kind") != "element" and s.get("from_id") and s.get("to_id"):
            out.setdefault(s["to_id"], set()).add(s["from_id"])
    return out


def fan_in(M):
    """{part: how many of the stage's performing parts need it}."""
    perf = {x for v in M["performers"].values() for x in v}
    return {x: len(n & perf) for x, n in needers(M).items()}


def shared_need(M, r, fan=None):
    """A dependency two or more of the stage's performing parts need: grouped first, whatever the states record."""
    fan = fan_in(M) if fan is None else fan
    return r["hop"] == "needs" and max((fan.get(x, 0) for x in parts_of(r)), default=0) > 1


# a dependency's failure reaches its caller as the service answering with an error or slowly, never as it being down
SURFACES = {("call", "callee returns an error"), ("call", "callee slow or hangs")}


def behind_callee(M):
    """{part: the one service that needs it}, where the stage reaches that service by a call and has a test of it
    answering with an error or slowly: the part is worked as a linked test from those, not as a test of its own."""
    callees = {x for r in live(M) if (r["hop"], r["mode"]) in SURFACES for x in parts_of(r)}
    return {x: next(iter(n)) for x, n in needers(M).items() if len(n) == 1 and n <= callees}


def entry_modes(M, m):
    """An alert's own tests. A called service's dependency leaves them only where this entry works that service's
    error or slow test, which links it: nothing the entry would have worked goes unreached."""
    states, behind = set(entry_states(M, m)), behind_callee(M)
    rows = [r for r in live(M) if set(branch_of(M, r)) & states and not owned_elsewhere(M, m, r)]
    surfaced = {x for r in rows if (r["hop"], r["mode"]) in SURFACES for x in parts_of(r)}
    return [r for r in rows if not (r["hop"] == "needs" and parts_of(r)
                                    and all(behind.get(x) in surfaced for x in parts_of(r)))]


def test_order(r):
    """`order`, a whole number the drafter sets; blank, or not a number (the check reports it), is 0."""
    v = norm(r.get("order"))
    return int(v) if v.isdigit() else 0


def mode_key(M, handle=None):
    order = list(M["stage_moves"])

    def key(r):
        mvs = [x for x in ids(r["moves"]) if x in order]
        first = mvs[0] if mvs else ""
        hops = M["hops"].get(first, [])
        # a test that closes with no impact runs after every test that finds a fault: the same signal may be either.
        # Whether each part is up comes first: the cheapest check, and it needs no case ids. Then a test reading the
        # alert's own count: it lists the cases the other tests are read on.
        # then the drafter's `order`: a test whose evidence lists cases runs after the tests that explain them. An
        # up-check lists no cases, so it stays ahead of any order.
        return (r.get("ending") in BENIGN, not is_up(r), test_order(r), handle not in ids(r["measures"]),
                min((order.index(x) for x in mvs), default=99),
                hops.index(r["hop"]) if r["hop"] in hops else len(hops), r["mode_id"])
    return key


def entry_groups(M, m):
    """(group heading or None, modes, the state or None) in the order an entry works them: the dependencies that hold
    cases in several of its states first, then each state's tests."""
    states, rows, key = entry_states(M, m), entry_modes(M, m), mode_key(M, m["handle"])
    fan = fan_in(M)
    sh = [r for r in rows if shared_need(M, r, fan)
          or (r["hop"] == "needs" and len(set(branch_of(M, r)) & set(states)) > 1)]
    first = [("Shared dependencies: several parts of the stage need them, or they hold cases in several states at "
              "once, so test them first",
              # the cheapest check first still leads; then the part more of the stage needs
              sorted(sh, key=lambda r: key(r)[:4] + (-max((fan.get(x, 0) for x in parts_of(r)), default=0),)
                     + key(r)[4:]), None)]
    if len(states) < 2:
        rest = sorted([r for r in rows if r not in sh], key=key)
        return (first + [("The other tests", rest, None)]) if sh else [(None, rest, None)]
    groups = first if sh else []
    gone = m.get("form") not in WAITING
    for b in states:
        mvs = [mv for mv in M["stage_moves"] if state(M["moves"][mv]["from_state"]) == b]
        groups.append((f"Cases in {said(b)}{', or that left the stage from it' if gone else ''}: the move out did "
                       f"not happen{' as it should' if gone else ''} ("
                       + "; ".join(mv + " " + move_name(M, mv) for mv in mvs) + ")",
                       sorted([r for r in rows if b in branch_of(M, r) and r not in sh], key=key), b))
    return groups


def numbering(M):
    """{test id: failure-mode row}: T1 to T4 are the opening checks (None); then every live mode once, in the order
    the entries first reach it, and last the modes no proposed alert reaches."""
    seen = []
    for m in stage_alerts(M):
        for _, rows, _ in entry_groups(M, m):
            seen += [r["mode_id"] for r in rows if r["mode_id"] not in seen]
    seen += [r["mode_id"] for r in sorted(live(M), key=mode_key(M)) if r["mode_id"] not in seen]
    by_id = {r["mode_id"]: r for r in live(M)}
    out = {f"T{n}": None for n in range(1, 5)}
    out.update({f"T{k}": by_id[mid] for k, mid in enumerate(seen, 5)})
    return out


def users(M, linked=True):
    """{mode id: the handles of the proposed alerts whose entries run it}, and, with `linked`, of those whose entries
    send the responder to it as a linked test, marked `(linked)`."""
    out = {r["mode_id"]: [] for r in live(M)}
    for m in stage_alerts(M):
        for r in entry_modes(M, m):
            out[r["mode_id"]].append(m["handle"])
    if linked:
        for m in stage_alerts(M):
            for y in dict.fromkeys(y for ys in entry_links(M, m).values() for y in ys):
                out[y].append(f"{m['handle']} (linked)")
    return out


def named_in(M, r):
    """[(the id the register's text names, [mode ids])] for one mode's `failure`. A mode named by its id is that mode;
    a move named by its id stands for the modes that stop it: a mode whose recovery is set says what becomes of a case
    when the move does not happen."""
    out = []
    for x in dict.fromkeys(re.findall(r"\b(FM\d+|L\d+)\b", r.get("failure", ""))):
        hits = [y["mode_id"] for y in live(M) if y["mode_id"] != r["mode_id"] and (
            y["mode_id"] == x if x.startswith("FM") else x in ids(y["moves"]) and y.get("recovery"))]
        if hits:
            out.append((x, hits))
    return out


def entry_links(M, m):
    """{mode id: {linked mode id: [what the register's text names]}} for one alert's entry. An alert's own tests are
    the ones its entry works over its window; a linked test is one its own tests' failure texts name and that the
    entry does not already work. A link runs one way, from the cause whose text names the other: a cause the text
    calls latent behind another is not sent back to it. The entry's lines and the shared section's list are both
    written from this, so the two cannot disagree."""
    own = {r["mode_id"] for r in entry_modes(M, m)}
    behind = behind_callee(M)
    out = {}
    for r in live(M):
        if r["mode_id"] not in own:
            continue
        if (r["hop"], r["mode"]) in SURFACES:
            for d in live(M):
                if d["mode_id"] not in own and d["hop"] == "needs" and parts_of(d) and all(
                        behind.get(x) in parts_of(r) for x in parts_of(d)):
                    why = f"{part_names(M, r)} needs {part_names(M, d)}"
                    if why not in out.setdefault(r["mode_id"], {}).setdefault(d["mode_id"], []):
                        out[r["mode_id"]][d["mode_id"]].append(why)
        for x, hits in named_in(M, r):
            for y in hits:
                if y not in own:
                    out.setdefault(r["mode_id"], {}).setdefault(y, [])
                    if f"{r['mode_id']} names {x}" not in out[r["mode_id"]][y]:
                        out[r["mode_id"]][y].append(f"{r['mode_id']} names {x}")
    return out


def owner_of(M, sid):
    return (M["subj"].get(sid, {}).get("owner") or "").strip()


def plain(text):
    """Register text with its citations (the parentheses) taken out, for a line a responder reads in passing."""
    return re.sub(r"\s+([;,:]|\.(?!\w))", r"\1", norm(strip_parens(text)))  # ".NET" keeps the space before it


def escalate_to(M, sid):
    """Escalation goes to whoever owns the failing part, as the register records it."""
    owner = plain(owner_of(M, sid)) or "not in the map yet"
    return f"escalate to the owner of {name(M, sid)}: {owner} ({sec('escalate')})"


def written_remedies(M):
    """The remedies the runbook writes in its restore table, in order: every one a test's ending names, then every one
    a written remedy sends the responder on to (an `if_different` naming another), so no reference is left dangling.
    `do not` remedies are listed apart."""
    out = [x for x in dict.fromkeys(r["remedy"] for r in M["fm"] if r.get("remedy")) if x in M["remedies"]]
    for rid in out:  # grows while it is walked: a remedy named by one just added is added after it
        for x in re.findall(REMEDY_ID, " ".join(M["remedies"][rid].get(c) or "" for c in REMEDY_TEXT)):
            if x in M["remedies"] and x not in out and M["remedies"][x].get("kind") != "do not":
                out.append(x)
    return out


def donts_of(M, modes):
    """The `do not` remedies the given failure modes use: one a mode names as its remedy, or one named by a remedy
    they use (followed on through every remedy so named). A caution reaches only the stages and alerts whose tests
    lead to it."""
    out = [x for x in dict.fromkeys(r.get("remedy") for r in modes) if x in M["remedies"]]
    for rid in out:  # grows while it is walked
        for x in re.findall(REMEDY_ID, " ".join(M["remedies"][rid].get(c) or "" for c in REMEDY_TEXT)):
            if x in M["remedies"] and x not in out:
                out.append(x)
    return [x for x in out if M["remedies"][x].get("kind") == "do not"]


def entry_donts(M, m):
    """The `do not` remedies one alert's entry reaches: those its own tests, and the tests it links, use."""
    mids = {r["mode_id"] for r in entry_modes(M, m)} | {y for ys in entry_links(M, m).values() for y in ys}
    return donts_of(M, [r for r in M["fm"] if r["mode_id"] in mids])


def point_escalation(text):
    """Register text that says to escalate, pointed at the section the runbook writes escalation in."""
    return re.sub(r"\b([Ee]scalate)\b(?!\s*\(S\d+\))", lambda x: f"{x.group(1)} ({sec('escalate')})", text)


def also_escalated(M, rids):
    """{party: [remedy ids]} for the parties a remedy escalates to besides the failing part's owner
    (`remedies.csv` → `also_escalate_to`, `;` separated): a subject id stands for that part's owner, any other text for
    a party the register names but does not map."""
    out = {}
    for rid in rids:
        for p in split_top(M["remedies"][rid].get("also_escalate_to") or ""):
            if p.strip():
                out.setdefault(p.strip(), []).append(rid)
    return out


def party_text(M, p):
    """How a remedy line names a party it also escalates to."""
    return f"the owner of {name(M, p)}" if p in M["subj"] else p


def party_label(M, p):
    """The party's name as the escalation table's first column gives it."""
    return name(M, p) if p in M["subj"] else re.sub(r"^the\s+", "", p, flags=re.I)[:1].upper() + \
        re.sub(r"^the\s+", "", p, flags=re.I)[1:]


def ending_text(M, r):
    e = ENDINGS[r["ending"]]
    if r["ending"] == "restore":
        return f"**{e}**: {sec('restore')} {r['remedy']}"
    if r["ending"] in ("cannot restore", "outside"):
        return f"**{e}**: {escalate_to(M, parts_of(r)[0]) if len(parts_of(r)) == 1 else 'escalate to the owner of each part that matched (' + sec('escalate') + ')'}" + (f"; {sec('restore')} {r['remedy']} says what to record" if r.get("remedy") else "")
    return f"**{e}**"


def mtext(M, h):
    m = M["measures"].get(h, {})
    return f"{h} ({m.get('measure', '?')}: {m.get('counted_how', '')})"


def outcome(s):
    o = s['right_outcome']
    return "(proposed) " + o.removeprefix('proposed: ') if o.startswith('proposed: ') else o


def move_name(M, mv):
    """A lifecycle move in the words the map uses: the name of the process step that cites it, else the move's own."""
    for s in M["steps"]:
        if mv in re.findall(r"\bL\d+\b", s.get("source", "")):
            return s.get("name") or M["moves"][mv]["move"]
    return M["moves"][mv]["move"]


def leaving_lines(M, m):
    moves = M["moves"]
    return [(f"- A case failed back at {', '.join(g)} ({move}) did not get what it expected" if back else
             f"- Leaving by {', '.join(g)} ({move})") + f": {m['handle']} counts those cases"
            for (back, move), g in grouped(exits_of(M, m), lambda mv: (failed_back(moves[mv]), move_name(M, mv)))]


def window(M, m):
    """(its cases, its window) for one alert's entry."""
    moves, h = M["moves"], m["handle"]
    if m.get("form") in WAITING:
        return (f"those held in the stage past the time limit (the time limit in [ALERT.md](ALERT.md)). A case not past the "
                f"time limit is not one of {h}'s.",
                "from when the oldest of its cases entered the stage, to now. The alert fires only once a case has "
                "waited past the time limit, so its cause can be as old as that: never read a test over only the time "
                "since the count began rising.")
    ex = exits_of(M, m)
    if not ex:
        return ("those it counts leaving the stage. Its `counted_moves` names no move they leave by, so its tests are every "
                "state's.", "from when the earliest of its cases entered the stage, to now.")
    return ("those that left by " + "; ".join(f"{', '.join(g)} from {said(b)}" for b, g in
                                              grouped(ex, lambda mv: state(moves[mv]["from_state"])))
            + f" in the alert's window. A case still in the stage is not one of {h}'s.",
            "from when the earliest of its cases entered the stage, to now: what sent a case out wrongly can come "
            "before it left.")


def contain(M, m, donts=True):
    """Contain first: the step that stops further harm to the cases the alert counts, or why none is needed, from
    where those cases are now and the moves that brought them there."""
    moves, h = M["moves"], m["handle"]
    dont = entry_donts(M, m) if donts else []
    tail = (f" Take none of the actions under **What not to do** ({ref('restore')}: {', '.join(dont)})."
            if dont else "")
    if m.get("form") in WAITING:
        return (f"No hold is needed: the cases {h} counts are still in the stage, and nothing more is done to them "
                "while they wait." + tail)
    ex = exits_of(M, m)
    if not ex:
        return ("Its `counted_moves` names no move its cases leave by, so nothing here says where they are now. Find them with "
                "its tests, and move none of them on until the failing part's owner has ruled." + tail)
    out = []
    main = [mv for mv in ex if moves[mv].get("path") == "main" and not failed_back(moves[mv])]
    back = [mv for mv in ex if failed_back(moves[mv])]
    alt = [mv for mv in ex if mv not in main and mv not in back]
    if main:
        to = ", ".join(said(s) for s in dict.fromkeys(state(moves[mv]["to_state"]) for mv in main))
        out.append(f"Hold each case {h} lists where it is now ({to}): move none of them on until the failing part's "
                   "owner has ruled. It left by the stage's main ending with a wrong outcome, and every later move "
                   "carries that outcome on.")
    if alt:
        # everyone who can make the move: each person who carries it, and whoever can sign in to a front end that
        # carries it and no main move of the stage (a back-office screen with its own login is a way to make the move
        # that no person row names; a front end the main path uses is the party's own, not a way round it)
        carriers = list(dict.fromkeys(c for mv in alt for c in M["carried"][mv]))
        on_main = {c for mv in M["stage_moves"] if moves[mv].get("path") == "main" for c in M["carried"][mv]}
        who = ([f"every {name(M, c)}" for c in carriers if M["subj"][c].get("part_kind") == "person"] +
               [f"everyone who can sign in to {name(M, c)}" for c in carriers
                if M["subj"][c].get("part_kind") == "web front end" and c not in on_main])
        told = (", ".join(who[:-1]) + " and " + who[-1]) if len(who) > 1 else "".join(who)
        out.append(f"Stop more cases leaving by {', '.join(alt)}: " + (
            f"tell {told} to make no more of these moves until the failing part's owner has ruled." if who else
            "no person makes these moves, so nothing here holds more cases back; they keep leaving until the cause "
            "is restored."))
    if back:
        out.append(f"The cases failed back at {', '.join(back)} are no longer in the application: there is nothing "
                   "to hold.")
    irr = [mv for mv in ex if moves[mv].get("irreversible") == "yes"]
    if irr:
        out.append(f"{', '.join(irr)} cannot be undone: a case already left by {'it' if len(irr) == 1 else 'them'} "
                   "stays as it is.")
    return " ".join(out) + tail


def no_tests(M, m, groups):
    """The one line an entry writes in place of an empty list of tests, or None when it has tests: a case waiting in
    a state that no lifecycle move leaves has nothing in the register to test."""
    if any(rows for _, rows, _ in groups):
        return None
    gapped = vq.gap_said(M, "alert: its own tests", m.get("handle", ""))
    if gapped:
        return gapped + "."
    left = {state(v["from_state"]) for v in M["moves"].values() if state(v["from_state"]) != state(v["to_state"])}
    if any(s not in left for s in entry_states(M, m)):
        return "No tests yet: no recorded move takes these cases out of the stage."
    return "No tests yet."


def entry(M, m, num):
    h, stage = m["handle"], M["stage"]
    tid = {r["mode_id"]: t for t, r in num.items() if r}
    lk = entry_links(M, m)
    cases, win = window(M, m)
    out = [f"## {entry_heading(m)}", "", "### What fired", "",
           f"**{h} {m['measure']}** is above the operators' threshold for longer than their window "
           "([ALERT.md](ALERT.md)).", "",
           "**The expectation it guards:** " + re.sub(r"(?<![.!?])\s*$", ".", basis(m) or "not stated in the register (`measures.csv` → `alert`)", count=1),
           ""] + ([not_emitted(m), ""] if not_emitted(m) else [])
    lines = leaving_lines(M, m) if m.get("form") not in WAITING else []
    out += (lines + [""] if lines else [])
    out += [f"**Its cases:** {cases}", "", f"**Window:** {win}", "",
            f"Check the triggers to escalate or declare an incident ({ref('escalate')}) at every step, "
            "not only at the end.", "",
            "### Opening checks", "",
            f"Run T1, T2 and T3 ({ref('tests')}) over the window above: an open incident or known error, a "
            "planned window or change, and what changed since the window opened. Then T4: is the count falling?", "",
            "### Contain first", "", contain(M, m), "",
            "### Its tests", ""]
    groups = entry_groups(M, m)
    none = no_tests(M, m, groups)
    if none:
        return out + [none, "", *restore_close(M)]
    out += [f"Work them over the window, on its cases only, in order; each is written in {ref('tests')}. "
            "Where a test's command asks for a time span in angle brackets (a `--since` or a time range), give it this "
            "entry's window, whatever the placeholder says. Where it asks for case ids in angle brackets (`<case "
            "ids>`, `<id>`), give it the ids of the cases you are working: this entry's own, or those the test that "
            "sent you to it listed. Every result has a route:", "",
            "- the expected result: go on to the next test;",
            "- a match: it explains the cases it lists. Take the line's ending for those cases; if the alert counts "
            "cases it did not list, go on to the next test for the rest. Where the line says to run linked tests as "
            f"well, run them on the same cases: the register ties those causes together ({ref('shared')});",
            "- a check whose evidence lists no cases (a match in a log or a metric) explains no case by itself: note "
            "it, if the match falls inside the look-back, and go on; a case no later check explains takes the ending of "
            "every check noted for it, each named in the hand-over; where those endings differ, escalate rather than "
            "restore;",
            "- anything else (an unclear answer, a step you cannot run): note it for the hand-over and go on.", ""]
    states = entry_states(M, m)
    if len(states) > 1:
        names = ", ".join(said(b) for b in states)
        out += [(f"Group its cases by the state they are in ({names}) and work each group below that has cases, the "
                 "largest group first." if recorded(M) else
                 f"The states of this stage ({names}) are not recorded, so its cases cannot be grouped by state: work "
                 "every group below, in order."), ""]
    k, done = 0, []
    for g, (gh, rows, b) in enumerate(groups):
        if gh:
            out += [f"**{gh}**", ""]
        for r in rows:
            k += 1
            t = tid[r["mode_id"]]
            if r["mode_id"] in done:
                out.append(f"{k}. **{t}** again ({r['mode_id']}): ran above, so use the result you have for these cases.")
                continue
            done.append(r["mode_id"])
            more = sorted((tid[y] for y in lk.get(r["mode_id"], {})), key=lambda x: int(x[1:]))
            out.append(f"{k}. **{t}** {r['mode_id']} {part_names(M, r)}, {r['hop']}: {r['mode']} "
                       f"({', '.join(ids(r['moves']))}). A match means: {plain(r['failure']).rstrip('.')}. "
                       f"Ending: {ending_text(M, r)}." +
                       (f" If it matches, also run {', '.join(more)}, on the same cases." if more else ""))
        if gh and b is None and g < len(groups) - 1:
            out.append("")
            continue
        k += 1
        last = g == len(groups) - 1
        out.append(f"{k}. None of these explains the cases left" + (f" in {said(b)}" if b else "") +
                   f": **Outside this runbook** ({ref('outside')})" +
                   ("." if last else "; go on with the next group that still has cases."))
        out.append("")
    return out + restore_close(M)


def restore_close(M):
    return ["### Restore, close, escalate", "",
            f"{ref('restore', 'Restore (' + sec('restore') + ')')} · {ref('close', 'Close (' + sec('close') + ')')} · "
            f"{ref('escalate', 'Escalate or declare (' + sec('escalate') + ')')}. "
            "Each test above says where its ending goes; escalation goes to the owner of the failing part.", ""]


def approval_text(M, rid):
    """Whose approval a remedy needs, in words that need no owner on record: the team that owns each part whose
    failure modes use it."""
    parts = list(dict.fromkeys(p for r in M["fm"] if r.get("remedy") == rid for p in parts_of(r) if p))
    said = [name(M, p) for p in parts]
    names = " or ".join(said) if 0 < len(said) <= 2 else "the part it changes"  # a long list of teams is noise to a responder
    return f"Needs approval from the team that owns {names} (not recorded yet)."


def runbook(M):
    R, stage, sid, moves = M["R"], M["stage"], M["stage"]["stage"], M["moves"]
    about = R["about"][0] if R["about"] else {}
    alerts = stage_alerts(M)
    num, use = numbering(M), users(M)
    tid = {r["mode_id"]: t for t, r in num.items() if r}
    shared_head = f"Shared section: {stage['name']}"
    out = [f"# Runbook for \"{stage['name']}\"", "",
           ("One entry per proposed alert, then the stage's shared section. Each alert's runbook link "
            "([ALERT.md](ALERT.md)) points at its own entry. The shared section holds what the alerts have in common "
            "and writes every test once; an entry names the tests it runs, bounded to its own cases and window. "
            if alerts else
            "No alert is proposed for this stage in the register: not on the stage, its process steps, the parts they use or "
            "the flow. So this runbook has no alert entries and there is no alert page. Whether to alert, and on what, "
            "is the team's decision. The stage's shared section below still writes every test once. ") +
           "Generated from the register by `flow_outputs.py`: each test after the opening checks is a row of "
           "`failure-modes.csv`. State: draft, never rehearsed. Process steps are numbered within their stage, the same in every stage file.", ""]
    out += [f"- [{entry_heading(m)}](#{slug(entry_heading(m))})" for m in alerts]
    out += [f"- [{shared_head}](#{slug(shared_head)})", ""]
    for m in alerts:
        out += entry(M, m, num)
    out += [f"## {shared_head}", ""]

    # S1 the stage on one page
    out += [head('stage'), "", f"**Configuration described:** {about.get('what_it_is', 'not stated')}", "",
            f"Flow **{M['flow']['name']}**, one case: {strip_parens(M['flow']['case']).split(':')[0].strip()}. Stage "
            f"{stage['order']} of {len(M['stages'])}, **{stage['name']}**. [STRUCTURE.md](STRUCTURE.md) draws the same "
            "steps and [MEASURES.md](MEASURES.md) measures them.", "",
            "| Process step | Right outcome | From → to | Path | Done by | Needs |", "|---|---|---|---|---|---|"]
    for s in M["steps"]:
        mvs = M["step_moves"][s["step"]]
        ft = "; ".join(once(f"{said(state(moves[x]['from_state']))} → {to_said(state(moves[x]['to_state']))}" for x in mvs))
        out.append(f"| {step_title(M['labels'], s)} | {outcome(s)} | {ft} | "
                   f"{', '.join(dict.fromkeys(moves[x]['path'] for x in mvs))} | "
                   f"{', '.join(name(M, c) for c in M['performers'][s['step']])} | "
                   f"{', '.join(name(M, c) for c in M['supporters'][s['step']]) or '—'} |")
    last = [s for s in M["steps"] if to_states(M, s["step"]) & set(M["exits"])]
    limit = time_limit(stage.get("bound_in_code"))
    out += ["", "**Expected of the stage.** A case that enters it leaves"
            + (f" within the time limit ({limit})," if limit else "") + " in one of these ways:", ""]
    out += once(f"- {step_title(M['labels'], s)}: {outcome(s)}" for s in last)
    stranded = [mv for mv in M["stage_moves"] if moves[mv].get("recovery") == "stranded"]
    if stranded:
        out += ["", "**Cases stranded.** When " + ", ".join(stranded) +
                " does not happen, the case is stranded: nothing in the application moves it on."]
    out.append("")

    # S2 what is at stake
    out += [head('stake'), ""]
    stake = [f"- **{a['attribute']}**: {a['what_is_at_stake']}" for a in R["case-attributes"]
             if a.get("flow") == M["flow"]["flow_id"]]
    stake += [f"- **Irreversible:** {mn} ({', '.join(g)}) cannot be undone." for mn, g in
              grouped([mv for mv in M["stage_moves"] if moves[mv].get("irreversible") == "yes"],
                      lambda mv: move_name(M, mv))]
    step_ids = [s["step"] for s in M["steps"]]
    stake += [f"- {at_stake(M, i)}: counted in {i.get('unit', '')}. {i.get('note', '')}".rstrip(". ") + "."
              for i in R["step-impact"] if i["step"] in step_ids]
    out += once(stake)
    out += ["- **Declare an incident** when the impact threshold in the severity definition is crossed: an operator value, "
            "linked here.", ""]

    # S3 before you start
    used = list(dict.fromkeys(h for r in live(M) for h in ids(r["measures"])))
    by_part = {}
    for h in used:
        if h in M["measures"]:
            by_part.setdefault(M["measures"][h]["subject_id"], []).append(h)
    out += [head('start'), "", "You need to be able to read each of these. A step you cannot run is a defect: "
            "record the runbook as *failed* and add the access to the access gaps.", ""]
    for sidp, hs in by_part.items():
        out.append(f"- **{name(M, sidp)}**: " + "; ".join(mtext(M, h) for h in hs))
    apps = [c for c in M["parts"] if M["subj"][c].get("band") == "application" and M["subj"][c].get("level") == "component"]
    out += [f"- **Deployment, configuration and restart history** for {', '.join(name(M, c) for c in apps)}.", ""]

    # S4 every test, once
    every = ", ".join(name(M, c) for c in M["parts"] if M["subj"][c].get("part_kind") != "person")
    timing = "; ".join(step_timings(M))
    waits = any(m.get("form") in WAITING for m in alerts)
    out += [head('tests'), "",
            "Each test is written here once. An alert's entry says which it runs, in what order, over which window "
            "and on which cases; **Used by** names the alerts whose entries run it. Where a command asks for a time "
            "span in angle brackets, it is the window of the entry being worked.", "",
            "| # | Test | Measures | Expected if this is not the cause | If it is | Ending | Used by |",
            "|---|---|---|---|---|---|---|"]
    opening = [
        (f"Is there an open incident, or a known error with a fix in flight, for {every}?", "—", "None", "One is open",
         "**Already known**"),
        (f"Is there a maintenance window on any of those parts, or a planned change to a timing the stage depends on "
         f"({timing or 'none stated'})?", "—", "None", "A window, or a setting changed on purpose",
         "**Expected condition** (add *alert needs changing* if it should have been suppressed)"),
        (f"**What changed:** any deploy, configuration change or unplanned restart of {every} since the window of the "
         "alert that fired opened (its entry says when)?", "—", "None", "A change lines up with the start",
         f"Roll it back through the change-approval path, or escalate to the owner of the part that changed "
         f"({sec('escalate')}); then re-run T4"),
        ("Is the count of the alert that fired falling within one window" +
         (" (for a count of cases waiting, with the oldest only just past the time limit)" if waits else "") + "?",
         ", ".join(m["handle"] for m in alerts), "Not falling", "Falling within one window",
         "**Self-healed** (mark *threshold or duration wrong*), for an alert that counts cases waiting. For one that "
         "counts cases that already left wrongly, falling means only that no new cases are arriving: go on and work "
         "the cases it counted")]
    every_alert = ", ".join(m["handle"] for m in alerts)
    for n, (t, ms, e, s, end) in enumerate(opening, 1):
        out.append(f"| T{n} | {t} | {ms} | {e} | {s} | {end} | {every_alert} |".replace("\n", " "))
    for t, r in num.items():
        if not r:
            continue
        out.append((f"| {t} | {r['test']} *({r['mode_id']}: {part_names(M, r)}, {r['hop']}: {r['mode']}; "
                    f"{', '.join(ids(r['moves']))})* | {'; '.join(mtext(M, h) for h in ids(r['measures']))} | "
                    f"{r['expected']} | {r['seen']} | {ending_text(M, r)} | "
                    f"{', '.join(use[r['mode_id']]) or 'no proposed alert'} |").replace("\n", " "))
    ruled = [r for r in M["fm"] if r.get("ending") == "not possible"]
    if ruled:
        out += ["", "**Ruled out by the design** (no test needed):", ""]
        out += [f"- {r['mode_id']} {part_names(M, r)}, {r['hop']}: {r['mode']} ({', '.join(ids(r['moves']))}): "
                f"{r['failure'].removeprefix('not possible here:').strip()}" for r in ruled]
    out.append("")

    # S5 causes the alerts share
    out += [head('shared'), ""]
    if not alerts:
        out += ["No alert is proposed for this stage, so no cause is shared between alerts.", ""]
    elif len(alerts) < 2:
        out += ["One alert is proposed for this stage, so no cause is shared between alerts.", ""]
    else:
        own = users(M, linked=False)
        multi = [(t, r) for t, r in num.items() if r and len(own[r["mode_id"]]) > 1]
        out += ["**Tested for more than one alert.** One fault here can fire several of the alerts at once: when "
                "two fire together, start with these.", ""]
        out += [f"- {t} {r['mode_id']} {part_names(M, r)}, {r['hop']}: {r['mode']}: {', '.join(own[r['mode_id']])}"
                for t, r in multi] or ["- None: no test serves more than one alert."]
        crossing = []
        for m in alerts:
            for mid, ys in sorted(entry_links(M, m).items(), key=lambda kv: int(tid[kv[0]][1:])):
                r = next(x for x in live(M) if x["mode_id"] == mid)
                order = sorted(ys, key=lambda y: int(tid[y][1:]))
                crossing.append(f"- {m['handle']}, {tid[mid]} {mid} ({part_names(M, r)}, {r['hop']}: {r['mode']}): "
                                "run " + "; ".join(f"{tid[y]} {y} ({', '.join(own[y]) or 'no proposed alert'})"
                                                   for y in order) +
                                " as well: " + "; ".join(dict.fromkeys(w for y in order for w in ys[y])))
        out += ["", "**Linked in the register.** The register's own text of one cause names another: a mode named is "
                "that mode, and a move named stands for the modes that stop it. For each alert's own test, the tests "
                "it links that the alert's entry does not already work; its entry says to run them, on the same "
                "cases, when it matches.", ""]
        out += crossing or ["- None."]
        out.append("")

    # S6 restore
    used_rem = written_remedies(M)
    also = also_escalated(M, used_rem + donts_of(M, M["fm"]))
    out += [head('restore'), "", "| # | Kind | Action | Expected result | If different | Approval |", "|---|---|---|---|---|---|"]
    for rid in used_rem:
        rem = M["remedies"][rid]
        exp = rem.get("expected", "")
        if rem["kind"] in RESTORING:
            exp += (" Then go back to the entry of the alert that fired: re-run T4 and its tests for every case still "
                    "affected, since a restore can leave cases in other states.")
        if rem["kind"] == "none exists":
            exp = (("Record the case ids, their state, " if recorded(M) else
                    "Record what the tests showed (no record of this stage holds the case ids or states), ") +
                   "and whether new cases are still failing now. Ending: "
                   f"**Broken — cannot restore**; escalate ({sec('escalate')}).")
        exp += "".join(f" Also escalate to {party_text(M, p)} ({sec('escalate')})." for p, rs in also.items() if rid in rs)
        out.append(f"| {rid} | {rem['kind']} | {point_escalation(rem['action'])} | {exp} | "
                   f"{point_escalation(rem.get('if_different', '') or 'Escalate')} | "
                   f"{approval_text(M, rid) if rem.get('needs_approval') == 'yes' else '—'} |".replace("\n", " "))
    donts = [M["remedies"][x] for x in donts_of(M, M["fm"])]
    if donts:
        out += ["", "**What not to do.**", ""] + once(f"- {rem['remedy']}: {point_escalation(rem['action'])}" for rem in donts)
    out.append("")

    # S7 close
    out += [head('close'), "", "| Ending | Close |", "|---|---|",
            "| Nothing is wrong | Close as no impact. If the alert should not have fired, add *threshold or duration wrong*. |",
            "| Expected condition | Link the window or change, then close. Add *alert needs changing* if it should have been suppressed. |",
            "| Self-healed | Confirm the alert that fired is back under its threshold, then close. Mark *threshold or duration wrong*. |",
            "| Already known | Link the incident, then close. |",
            f"| Broken — restore | After the {sec('restore')} action, confirm the alert that fired is under its threshold, no case it counted is still affected, and new cases get through. Any that remain: back to its entry, T4. |",
            f"| Broken — cannot restore | Escalate ({sec('escalate')}). Runbook mark: *worked*. |",
            "| Outside this runbook | Escalate with what you have. Mark *gap*, or *failed* if a step could not be run. |", ""]

    # S8 escalate or declare
    esc = [r for r in live(M) if r["ending"] in ("cannot restore", "outside")]
    failing = list(dict.fromkeys([c for c in M["parts"]] + [x for r in live(M) for x in parts_of(r)] +
                                 [p for p in also if p in M["subj"]]))
    out += [head('escalate'), "",
            f"**Escalate** (hand over to the owning tier) when you cannot restore with {sec('restore')}; when a test ends in *Broken — "
            "cannot restore* (" + (", ".join(tid[r["mode_id"]] for r in esc) or "none") + "); or when a remedy needs "
            "approval (use the change-approval path).", "",
            "**Escalate to the owner of the part that failed**: the part the test that matched names. The owners as "
            "the register records them, with the date each was recorded; *not in the map yet* means the register "
            "names none, a gap to fill and not a reason to stop. Links to the on-call and change records are the "
            "operators' to add.", "",
            "| Part | Owner (register) | As of | Responder (register) | Tests that end in escalation to it |",
            "|---|---|---|---|---|"]
    for c in failing:
        sc = M["subj"].get(c, {})
        ends = ", ".join(tid[r["mode_id"]] for r in esc if c in parts_of(r)) or "—"
        out.append(f"| {name(M, c)} | {owner_of(M, c) or 'not in the map yet'} | {sc.get('owner_as_of') or '—'} | "
                   f"{(sc.get('responder') or '').strip() or 'not in the map yet'} | {ends} |")
    for p, rs in also.items():  # a party a remedy names that is no part of the map: the register records no owner
        if p not in M["subj"]:
            out.append(f"| {party_label(M, p)} | not in the map yet | — | not in the map yet | "
                       f"— ({', '.join(rs)} {'escalates' if len(rs) == 1 else 'escalate'} to it) |")
    out += ["", "**Declare an incident** when a second team is needed, customers can see the problem, it is unsolved after a "
            f"time box of concentrated work, or the impact threshold in {sec('stake')} is crossed. Keep working the entry in parallel.", "",
            "**Hand over:** the alert and the expectation it guards (its entry); " +
            ("the affected case ids by state" if recorded(M) else
             "the counts the measures showed (no record of this stage holds case ids)") +
            "; whether new cases are still affected now; which tests ran and what they showed; what was contained and "
            "what was done; when the window opened.", ""]
    out += [head('outside'), "",
            f"For the cases no test explained: escalate them with what you have ({sec('escalate')}), and record *gap* (not covered) or "
            "*failed* (a step could not be run). Then go on with the next group of cases that still has some: an "
            "unexplained group does not end the walk for the others.", ""]
    out += [head('links'), "", "Operator links to fill in, one per measure the tests read:", ""]
    out += [f"- {mtext(M, h)}: {'exists' if M['measures'].get(h, {}).get('exists') == 'yes' else 'proposed'}" for h in used]
    out += ["", head('about'), "", "- **Owner:** not stated.",
            "- **Last validated:** never. It has not been rehearsed cold.",
            "- **To change it:** change the register (`lifecycle.csv`, `failure-modes.csv`, `remedies.csv`, "
            "`measures.csv`) and generate it again. Never edit this file.", "",
            "| Test | Failure mode | Lifecycle rows | Part | Source |", "|---|---|---|---|---|"]
    for t, r in num.items():
        if r:
            out.append(f"| {t} | {r['mode_id']} {r['hop']}: {r['mode']} | {', '.join(ids(r['moves']))} | "
                       f"{part_names(M, r)} | {r.get('source', '')} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- RUNBOOK.html and ALERT.html
#
# The same alerts and runbook, laid out for a responder who arrives from an alert: the alerts first, then each entry's
# Do now, one line per check with how to check folded under it, and the shared reference folded below. Every routing
# decision is the markdown writers' own (entry_groups, entry_links, contain, window, written_remedies); only the form
# differs. Every section is filled from the register, or says the register holds nothing for it. Register ids appear
# only in anchors and in the folds for maintainers.

# a part that is not running: the cheapest check, run first in every entry
UP = {("call", "callee down"), ("needs", "unavailable"), ("message", "consumer not running"),
      ("poll", "poller not running"), ("outbox", "relay not running")}
# one plain question per failure mode of method/hop-failures.csv, filled with the part's name
QUESTIONS = {
    ("call", "callee down"): "Is {p} down or unreachable?",
    ("call", "callee returns an error"): "Is {p} answering with errors?",
    ("call", "callee slow or hangs"): "Is {p} slow to answer, or not answering at all?",
    ("call", "caller gives up mid-call"): "Did {p} give up on calls before they finished?",
    ("call", "callee answers wrongly"): "Is {p} answering in time, but wrongly?",
    ("message", "publish fails"): "Is {p} failing to publish its messages?",
    ("message", "message not routed"): "Are the messages for {p} accepted but routed to no queue?",
    ("message", "consumer not running"): "Is {p} not running, leaving its messages queued?",
    ("message", "consumer fails on the message"): "Is {p} failing on the messages it reads?",
    ("message", "consumer slow"): "Is {p} falling behind on its queue?",
    ("outbox", "row left unpublished"): "Are changes in {p} left unpublished in its outbox?",
    ("outbox", "publish marked failed"): "Are {p}'s outbox rows marked failed?",
    ("outbox", "relay not running"): "Is {p}'s outbox relay not running?",
    ("poll", "poller not running"): "Is {p} not polling?",
    ("poll", "poll query fails"): "Is {p}'s poll query failing?",
    ("poll", "poll selects the wrong cases"): "Is {p} polling but missing cases?",
    ("timer", "timer does not fire"): "Did {p}'s timer not fire?",
    ("timer", "timer setting changed"): "Did {p}'s timer setting change?",
    ("in-process", "the act fails"): "Is the act failing inside {p}?",
    ("in-process", "the act completes wrongly"): "Is {p} completing the act, but wrongly?",
    ("person", "nobody acts"): "Has no {p} acted on the cases?",
    ("person", "the person acts wrongly"): "Did a {p} act wrongly on the cases?",
    ("needs", "unavailable"): "Is {p} down or unreachable?",
    ("needs", "slow"): "Is {p} slow?",
    ("needs", "full or out of capacity"): "Is {p} full or out of capacity?",
    ("needs", "answers stale or wrong"): "Is {p} answering with stale or wrong data?",
}
ID = r"\b(?:FM|ST|RM|L|R|M|S|F)\d+\b"
IDS = re.compile(rf"{ID}(?:(?:,\s*|;\s*|\s+and\s+|\s+or\s+|\s*,\s*and\s+){ID})*")
CITE = re.compile(r"\s*\((?=[^()]*(?:\w/\w|\.(?:py|ya?ml|tsx?|json|md|cs|java|go|sql)\b|:\d))[^()]*\)")


def is_up(r):
    return (r.get("hop"), r.get("mode")) in UP


def question(M, r):
    p = part_names(M, r)
    q = QUESTIONS.get((r["hop"], r["mode"]), "{p}: " + r["mode"] + "?")
    if len(parts_of(r)) > 1:  # a check on several parts asks of them all: "Are A and B down", "on their queues"
        q = re.sub(r"\bits queue\b", "their queues", re.sub(r"^Is \{p\}(?!')", "Are {p}", q))
        q = q.replace(" it reads", " they read").replace(" its ", " their ")
    q = q.format(p=p)
    return re.sub(r"\ba ([AEIOUaeiou])", r"an \1", q)


def remedy_number(M):
    """{remedy id: its number} for the remedies the runbook writes, in number order. A remedy keeps its register
    number on every page: RM6 is remedy 6 wherever it appears."""
    num = {rid: int(rid[2:]) if re.fullmatch(r"RM\d+", rid) else rid for rid in written_remedies(M)}
    return dict(sorted(num.items(), key=lambda kv: (0, kv[1]) if isinstance(kv[1], int) else (1, 0)))


REMEDY_CITED = re.compile(r"(?<![\w>])(?:([Rr])estore action|([Rr])emedy) (\d+)\b(?![^<]*</code>)")


def remedy_words(text):
    """Register prose naming a remedy by number ("restore action 4", from earlier releases, or "remedy 4") reads
    "remedy 4": the number is the remedy's register number."""
    return REMEDY_CITED.sub(lambda mo: ("R" if (mo.group(1) or mo.group(2)) == "R" else "r") + f"emedy {mo.group(3)}",
                            text)


def link_remedies(M, text):
    """Each "remedy n" in a restore card's text, a link to remedy n's card where the runbook writes it."""
    byn = {n: rid for rid, n in remedy_number(M).items()}
    return REMEDY_CITED.sub(lambda mo: (f'<a href="#restore-{esc(byn[int(mo.group(3))])}">{remedy_words(mo.group(0))}</a>'
                                        if int(mo.group(3)) in byn else remedy_words(mo.group(0))), text)


def id_name(M, x):
    """What a register id names, in the words a responder reads."""
    fm = {r["mode_id"]: r for r in M["fm"]} | {r["mode_id"]: r for r in M["R"]["failure-modes"]}
    if x in fm:
        r = fm[x]
        return (f"the check “{question(M, r)}”" if r.get("ending") != "not possible" else
                f"“{part_names(M, r)}, {r['mode']}”")
    if x in M["moves"]:
        return f"“{move_name(M, x)}”"
    if x in M["remedies"]:
        n = remedy_number(M).get(x)
        return f"remedy {n}" if n else ("what not to do" if M["remedies"][x].get("kind") == "do not"
                                        else "a remedy")
    if x in M["measures"]:
        return f"“{M['measures'][x]['measure']}”"
    if x in M["subj"]:
        return name(M, x)
    st = {s["stage"]: s for s in M["R"]["stages"]}
    if x in st:
        return f"the stage “{st[x]['name']}”"
    fl = {f["flow_id"]: f for f in M["R"]["flows"]}
    return f"the flow “{fl[x]['name']}”" if x in fl else ""


def unid(M, text):
    """Register prose with each run of ids replaced by what they name, and its file citations taken out."""
    t = text or ""
    while CITE.search(t):
        t = CITE.sub("", t)
    order = list(M["moves"])

    def span(mo):
        a, b = f"L{mo.group(1)}", f"L{mo.group(2)}"
        if a in order and b in order and order.index(a) < order.index(b):
            return ", ".join(order[order.index(a):order.index(b) + 1])
        return mo.group(0)
    t = re.sub(r"\bL(\d+)\s*[-–]\s*L?(\d+)\b", span, t)
    t = re.sub(rf"({ID})'s\s+(\w+)", r"the \2 of \1", t)  # "FM07's test": the test of what FM07 names

    def run(mo):
        names = list(dict.fromkeys(n for n in (id_name(M, x) for x in re.findall(ID, mo.group(0))) if n))
        return (", ".join(names[:-1]) + " and " + names[-1]) if len(names) > 1 else "".join(names)
    t = IDS.sub(run, t)
    return re.sub(r"(?<![\w)])\(\s*\)", "", re.sub(r"\s+([;,:)]|\.(?!\w))", r"\1", re.sub(r"  +", " ", t))).strip()  # now() stays


def states_said(M, text):
    """Register prose with each lifecycle state named as the cards name it (`state_name`: AwaitingValidation reads
    "Awaiting validation"). A value in quotes or in a code span is a literal, as the database or a command holds it,
    and stays as written."""
    import stage_flow_views as sfv  # state_name lives with the cards; imported here, as it imports this module
    names = {s: sfv.state_name(s) for s in {state(v.get(k)) for v in M["moves"].values()
                                            for k in ("from_state", "to_state")} - {"(none)"}}
    names = {s: n for s, n in names.items() if n != s and not s.startswith("implicit:")}
    if not names:
        return text
    word = re.compile(r"(?<![\w'\"`])(" + "|".join(re.escape(s) for s in sorted(names, key=len, reverse=True)) +
                      r")(?![\w'\"`])")
    return "".join(piece if piece.startswith("`") else word.sub(lambda mo: names[mo.group(1)], piece)
                   for piece in re.split(r"(`[^`]*`)", text))


def say(M, text):
    """Register or generated prose as HTML: ids named, citations out, states named, escaped, its markdown made HTML."""
    t = html.escape(states_said(M, remedy_words(unid(M, unpipe(text)))), quote=False)
    t = re.sub(r"\[ALERT\.md\]\(ALERT\.md\)", '<a href="ALERT.html">the alerts page</a>', t)
    t = re.sub(r"\[RUNBOOK\.md\]\(RUNBOOK\.md\)", '<a href="RUNBOOK.html">the runbook</a>', t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", t)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", t)


def given_names(M):
    """The names the register gives (each part, step, stage, flow and the system), which read as names, never code."""
    if "_given" not in M:
        R = M["R"]
        rows = [M["subj"].values(), R.get("steps", []), R.get("stages", []), R.get("flows", []), R.get("about", [])]
        M["_given"] = {(r.get(k) or "").strip() for rs in rows for r in rs for k in ("name", "system")} - {""}
    return M["_given"]


_KEEP = re.compile(r"(<(code|pre|a)\b[^>]*>.*?</\2>|<[^>]+>)", re.S)


def code_face(M, html_text):
    """Page HTML with each code term in its text (outside tags, code, commands and links) set in the shared code face,
    as on the cards (page_style.marked): page_html runs it over a whole page."""
    out = []
    for i, piece in enumerate(_KEEP.split(html_text)):
        if i % 3 == 0:  # text between tags: already escaped, so marked on its unescaped words
            out.append(ps.marked(html.unescape(piece), given_names(M)).replace("&#x27;", "'").replace("&quot;", '"')
                       if piece else "")
        elif i % 3 == 1:
            out.append(piece)
    return "".join(out)


def say_prose(M, text):
    """A long register field broken up as a card's is (page_style.prose), each piece read by `say`."""
    return ps.prose(unpipe(text), given_names(M), inline=lambda t: say(M, t))


def cap(text):
    return text[:1].upper() + text[1:]


def unpipe(text):
    """Register text as written: load() escapes a pipe for the markdown tables, which a page or a command must not keep."""
    return (text or "").replace("\\|", "|")


def esc(text):
    return html.escape(unpipe(text), quote=True)


def how_block_whole(M, text):
    """The whole-field reading, for a field the writer cannot take apart: a command in its own block, with an instruction
    before it as prose where one leads it."""
    t = (text or "").strip()
    m = re.match(r"([A-Z][^:`|\"'<>]{0,300}?):\s+(\S.*)$", t, re.S)
    if m and not re.search(r"--|\||=", m.group(1)):
        return f'<p>{say(M, m.group(1))}:</p><pre><code>{esc(m.group(2))}</code></pre>'
    return f'<pre><code>{esc(t)}</code></pre>'


def programs(M):
    """The programs the register's own commands start with: the first word of every field (a test, a count, a
    restore action) that opens on a lower-case word whose first clause carries a flag or a pipe."""
    if "_programs" not in M:
        fields = ([r.get("test") for r in M["fm"]] + [x.get("counted_how") for x in M["measures"].values()] +
                  [x.get("action") for x in M["remedies"].values()])
        out = set()
        for f in (unpipe(x).strip() for x in fields if x):
            top = top_level(f)
            if top is None or not re.match(r"[a-z][\w.-]*\s", f):
                continue
            first = cut_top(f, top, r";\s*|\s+and\s+|[,:]\s")[0][1]
            if re.search(r"\s--?[A-Za-z]|\|", first):
                out.add(f.split()[0])
        M["_programs"] = out
    return M["_programs"]


def quote_mask(t):
    """[True where the character is inside a quote, its quote marks included], or None where a quote does not close.
    An apostrophe inside a word (exception's) is not a quote."""
    out, q = [], None
    for i, c in enumerate(t):
        if q:
            out.append(True)
            if c == q and not (q == '"' and t[i - 1] == "\\"):
                q = None
            continue
        if c == '"' or (c == "'" and not (0 < i < len(t) - 1 and t[i - 1].isalnum() and t[i + 1].isalnum())):
            q = c
        out.append(bool(q))
    return None if q else out


def top_level(t):
    """[True where the character is outside every quote and parenthesis], or None where a quote or a parenthesis
    does not close."""
    mask = quote_mask(t)
    if mask is None:
        return None
    out, depth = [], 0
    for c, inq in zip(t, mask):
        if not inq and c == "(":
            depth += 1
        out.append(not inq and depth == 0 and c != ")")
        if not inq and c == ")":
            depth -= 1
            if depth < 0:
                return None
    return None if depth else out


def cut_top(t, top, pattern):
    """t cut at every match of pattern that starts at the top level: [(the separator before, the piece)]."""
    out, last, sep = [], 0, ""
    for mo in re.finditer(pattern, t):
        if top[mo.start()]:
            out.append((sep, t[last:mo.start()]))
            sep, last = mo.group(0), mo.end()
    return out + [(sep, t[last:])]


SHELL_LOOP = re.compile(r"\b(?:for|while|until)\s+.*?;\s*do\b.*?;\s*done\b")
SQL_OPENING = re.compile(r"(?:SELECT|WITH|SHOW|UPDATE|INSERT|DELETE|EXPLAIN)\b")


def code_start(M, piece, after_code, first=False):
    """Where a command starts in one piece of a field: a program the register's commands start with, at the start
    of the piece or after a top-level comma or colon; or a statement in capitals (SELECT) after a top-level colon,
    or at the start of a piece that follows a command; or, after a top-level "run", a program, a shell loop, or a
    word with a flag straight after it (run psql -U ...). A field's first piece may open on a SQL statement. None for
    a piece that is prose."""
    top = top_level(piece)
    if top is None:
        return None
    for mo in re.finditer(r"(?:^|(?<=[,:]\s)|(?<=\brun\s))([A-Za-z][\w.-]*)\b", piece):
        p, w = mo.start(1), mo.group(1)
        if not top[p]:
            continue
        colon = piece[:p].rstrip().endswith(":")
        run = piece[:p].endswith("run ")
        if w in programs(M) or (re.fullmatch(r"[A-Z]{2,}", w) and (colon or (p == 0 and after_code))):
            return p
        if p == 0 and first and SQL_OPENING.match(piece):
            return p
        if run and (SHELL_LOOP.match(piece, p) or re.match(r"[a-z][\w.-]*\s+--?[A-Za-z]", piece[p:])):
            return p
    return None


def trailing_notes(code):
    """A command's trailing notes in parentheses, peeled off its end: (the command, [each note, its outer
    parentheses taken off])."""
    notes = []
    while code.endswith(")"):
        mask = quote_mask(code)
        if mask is None or mask[-1]:
            break
        depth, i = 0, len(code) - 1
        while i >= 0:
            if not mask[i]:
                depth += {")": 1, "(": -1}.get(code[i], 0)
                if depth == 0:
                    break
            i -= 1
        note = code[i + 1:-1].strip()
        # a note is words (the front end's own delete ..., the API ...), never a list of values or a statement in capitals (IN (...))
        if i <= 0 or not code[i - 1].isspace() or not re.match(r"(?:[a-z]|[A-Z][a-z])[\w'-]*[\s:,]", note):
            break
        notes.insert(0, note)
        code = code[:i].rstrip()
    return code, notes


def how_parts(M, text):
    """A command field taken apart into [("prose" | "code" | "note", text)], keyed on the register's own text: what
    can be pasted and run is a code piece; the instruction before it, a note after it (in parentheses) and the words
    that join two commands are prose. None where the field cannot be taken apart mechanically: no piece starts with
    a command, or a quote or a parenthesis does not close."""
    t = unpipe(text).strip()
    top = top_level(t)
    if top is None:
        return None
    out, after_code = [], False
    # a shell loop (for ...; do ...; done) is one command: its semicolons cut nothing
    for mo in SHELL_LOOP.finditer(t):
        top[mo.start():mo.end()] = [False if c == ";" else x for c, x in zip(mo.group(0), top[mo.start():mo.end()])]
    # a command ends at a top-level ";", a bare "and", ", then", or a sentence that starts after a closing quote or
    # a full stop
    pieces = cut_top(t, top, r";\s*|\s+and\s+|,\s+then:?\s+|(?<=[\"'])\s+(?=[A-Z][a-z]+\s+[a-z])|"
                             r"\.\s+(?=[A-Z][a-z]+\s+[a-z])")
    for n, (sep, piece) in enumerate(pieces):
        whole = piece.strip()
        body = re.sub(r"^(?:and|then)\s+", "", whole)
        p = code_start(M, body, after_code, first=n == 0)
        if p is None:
            # a new sentence after a command drops the separator and a bare "and" before it
            out.append(("prose", re.sub(r"^and\s+", "", whole) if after_code else sep + piece))
            after_code = False
            continue
        lead = whole[:len(whole) - len(body) + p]
        if after_code and re.search(r"\bthen\b", sep + whole[:len(whole) - len(body)]):
            out.append(("prose", "then:"))  # the order between two commands is said, not dropped
        lead = re.sub(r"^(?:and|then)\s+", "", lead) if after_code else sep + lead
        if lead.strip():
            out.append(("prose", lead))
        code, notes = trailing_notes(body[p:].strip())
        if top_level(code) is None and not SHELL_LOOP.match(code) or not code:
            return None
        if code.split()[0] in programs(M) or SHELL_LOOP.match(code) or not re.match(r"[A-Z]{2,}\b", code):
            code = code.rstrip(";,").rstrip()
        elif not code.endswith(";"):
            code += ";"  # a statement (SQL) ends with its semicolon, so it runs as pasted at its prompt
        out.append(("code", code))
        out += [("note", n) for n in notes]
        after_code = True
    if not any(k == "code" for k, _ in out):
        return None
    # a statement that opens the field, then the shell it runs in: the shell is said first, as it is done first
    if out[0][0] == "code" and re.match(r"[A-Z]{2,}\b", out[0][1]) and len(out) >= 3 and out[-1][0] == "code" \
            and out[-2][0] == "prose" and not re.match(r"[A-Z]{2,}\b", out[-1][1]):
        out = out[-2:] + out[:-2]
    merged = []
    for k, x in out:
        if k == "prose" and merged and merged[-1][0] == "prose":
            merged[-1] = ("prose", merged[-1][1] + x)
        else:
            merged.append((k, x))
    return merged


def prose_html(M, text):
    """One prose piece of a command field as a sentence: a command written in parentheses inside it is set as code."""
    t = re.sub(r"^[\s;,]+", "", text).rstrip()
    lead = t.endswith((":", ",")) or re.search(r"\brun$", t)  # it leads into the command after it
    t = re.sub(r"[\s;,:]+$", "", t)
    if not t:
        return ""
    t += ":" if lead else ("" if t.endswith((".", "!", "?")) else ".")

    def inline(mo):
        inner = mo.group(1)
        cut = re.search(r"\s\(", inner)
        cmd, rest = (inner[:cut.start()], inner[cut.start():]) if cut else (inner, "")
        return f"(`{cmd}`{rest})" if cmd.split() and cmd.split()[0] in programs(M) and "`" not in inner else mo.group(0)
    t = re.sub(r"\(((?:[^()]|\([^()]*\))*)\)", inline, keep_claims(t))
    return f"<p>{cap(say(M, t))}</p>"


FILE_CITE = re.compile(r"(?<![\w/])(?:(?:[\w.@-]+/)+[\w.@-]+|[\w.@-]+\.(?:py|ya?ml|tsx?|json|md|cs|java|go|sql|csv))"
                       r"(?::\d[\d-]*(?:,\s*\d[\d-]*)*)?|(?<![\w/])[\w.@-]+:\d[\d-]*(?:,\s*\d[\d-]*)*")


def keep_claims(text):
    """Text that came out of a command field, with each parenthesis that cites a file kept for what it claims: the
    file citations go, the claim stays. A claim that still reads like a citation (a route) is set off with commas,
    so the page's citation filter does not take it."""
    def one(mo):
        if not CITE.fullmatch(mo.group(0).lstrip()):
            return mo.group(0)
        inner = re.sub(r"\s*[,;:]\s*$|^\s*[,;:]\s*", "", re.sub(r"(?:[,;]\s*)?(?:" + FILE_CITE.pattern + ")", "", mo.group(1)))
        inner = re.sub(r"\s*[,;:]\s*$", "", inner.strip())
        if not inner:
            return ""
        return f" ({inner})" if not CITE.search(f" ({inner})") else f", {inner},"
    return re.sub(r"\s*\(([^()]*)\)", one, text or "")


def count_block(M, text):
    """What a measure counts: a command the way the runbook writes one (how_block), prose as prose."""
    t = unpipe(text).strip()
    if not t:
        return ""
    if how_parts(M, t) is None and t.split()[0] not in programs(M):
        return f"<p>{cap(say(M, t))}</p>"
    return how_block(M, t)


def how_block(M, text, prose_ok=False):
    """How to check: each command in its own block, holding only what can be pasted and run; the instruction before
    it, the notes after it and the words joining two commands are prose outside the block. A field the writer cannot
    take apart keeps the whole-field reading, unless `prose_ok` and it holds nothing a shell would read (no pipe, flag,
    `=` or placeholder): then it is an instruction to a person, written as prose."""
    parts = how_parts(M, text)
    if parts is None:
        t = unpipe(text).strip()
        if prose_ok and t and not re.search(r"\||\s--?[A-Za-z]|=|<\w", t):
            return f"<p>{cap(say(M, keep_claims(t)))}</p>"
        # an instruction that holds its command in parentheses: the sentence as prose, the command in it set as code,
        # never the sentence inside a block that a reader would paste
        if any(x.split()[:1] and x.split()[0] in programs(M) for x in re.findall(r"\(([^()]+)", t)) \
                and t.split()[0] not in programs(M):
            return prose_html(M, t)
        return how_block_whole(M, text)
    out = []
    for k, x in parts:
        if k == "code":
            out.append(f"<pre><code>{esc(x)}</code></pre>")
        elif k == "note":
            if how_parts(M, x):  # a note that holds a command of its own
                out.append(f'<div class="small">{how_block(M, x)}</div>')
                continue
            n = cap(say(M, keep_claims(x)))
            out.append(f'<p class="small">{n}{"" if n.endswith((".", "!", "?")) else "."}</p>' if n else "")
        else:
            out.append(prose_html(M, x))
    return "".join(out)


CSS = ps.CSS + """
*{box-sizing:border-box}
body{line-height:1.55}
main{max-width:76rem;margin:0 auto;padding:24px 16px 64px;display:grid;gap:24px}
a{color:var(--m-acc)}
h1{margin:0;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
p{margin:0 0 6px;max-width:68rem}
.doc{background:var(--m-col);border:1px solid var(--m-line);border-radius:6px;padding:18px 20px;display:grid;gap:12px;
min-width:0}
.trail{color:var(--m-acc);font-size:13px}
.lbl{font:500 13px/1.4 var(--m-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--m-ink2)}
.landing{display:grid;grid-template-columns:1fr 1fr;gap:24px}
@media (max-width:760px){.landing{grid-template-columns:1fr}}
.col{display:grid;gap:8px;align-content:start;min-width:0}
.card{border:1px solid var(--m-line);border-radius:6px;padding:10px 12px;display:grid;gap:2px;text-decoration:none;
color:var(--m-ink)}
a.card b{color:var(--m-acc)}
.card.gap{border-color:var(--m-bad)}.card.gap b{color:var(--m-bad)}
.sub{color:var(--m-ink2);font-size:13px}
.chip{display:inline-block;font-size:13px;padding:1px 8px;border-radius:10px;border:1px solid var(--m-line);
text-decoration:none;color:var(--m-ink)}
.chip.ok{border-color:var(--m-ok);color:var(--m-ok)}.chip.bad{border-color:var(--m-bad);color:var(--m-bad)}
.chip.warn{color:var(--m-ink2)}
.meta{display:flex;flex-wrap:wrap;gap:6px 22px;font-size:13px;color:var(--m-ink2)}
.meta b{color:var(--m-ink)}
.now{border:2px solid var(--m-ink);border-radius:6px;padding:10px 14px}
.now ol{margin:6px 0 0;padding-left:1.3em;display:grid;gap:6px}
.sec{font-weight:600;margin-top:6px}
.hint{font-weight:400;color:var(--m-ink2);font-size:13px}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%}
td,th{border-bottom:1px solid var(--m-line);padding:6px 8px;vertical-align:top;text-align:left}
th{font:500 13px/1.4 var(--m-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--m-ink2)}
table.chk td:first-child{width:2em;color:var(--m-ink2);font-variant-numeric:tabular-nums}
table.chk td:nth-child(3){width:30%}
@media (max-width:600px){table.chk tr{display:grid;grid-template-columns:2em 1fr}
table.chk td{border:0}table.chk tr{border-bottom:1px solid var(--m-line)}
table.chk td:nth-child(3){grid-column:2;width:auto;padding-top:0}}
tr.grp td{font:500 13px/1.4 var(--m-mono);letter-spacing:.06em;text-transform:uppercase;
color:var(--m-ink2);padding-top:12px}
details{border-bottom:1px solid var(--m-line);padding:6px 0}
details>summary{cursor:pointer}
details.how{border:0;padding:2px 0}
details.how>summary{color:var(--m-acc);font-size:13px}
.box{margin-top:6px;display:grid;gap:6px;padding:8px 10px;border-left:3px solid var(--m-line)}
pre{margin:0;padding:8px 10px;background:var(--m-page);border-radius:4px;white-space:pre-wrap;word-break:break-word;
font:13px/1.45 var(--m-mono)}
.row2{display:flex;flex-wrap:wrap;gap:4px 22px;font-size:14px}
.small{font-size:13px;color:var(--m-ink2)}
.done{font-size:13px;color:var(--m-ink2);display:flex;gap:14px;flex-wrap:wrap}
ul{margin:0;padding-left:1.2em;display:grid;gap:4px}
.ref{display:grid;gap:12px}
:target{scroll-margin-top:12px}
main.frame.rbpage section.doc:first-of-type{padding-top:8px}
main.frame.rbpage p.untested{margin:2px 0 10px;font:600 15px var(--m-sans);color:var(--m-bad)}
main.frame.rbpage .landing .lbl{font:600 15px var(--m-sans);letter-spacing:0;text-transform:none;color:var(--m-ink)}
"""
OPEN_TARGET = ("<script>(function(){function go(){try{var h=decodeURIComponent(location.hash.slice(1));"
               "var e=h&&document.getElementById(h);for(var p=e;p;p=p.parentElement){if(p.tagName==='DETAILS')"
               "p.open=true;}var d=e&&e.tagName==='TR'&&e.querySelector('details');if(d)d.open=true;"
               "if(e)e.scrollIntoView();}catch(x){}}window.addEventListener('hashchange',go);"
               "window.addEventListener('load',go);})();</script>")


def page_html(M, title, body, main_class=""):
    reg, out = M.get("register", "<register>"), M.get("out", "<dir>")
    main = f'<main class="{main_class}">' if main_class else "<main>"
    return ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n"
            f"     Source: {reg}\n     Builder: flow_outputs.py\n"
            f"     Build: python -I flow_outputs.py {reg} {M['flow']['flow_id']} {M['stage']['stage']} --out {out}\n-->\n"
            f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>'
            f"<style>{CSS}</style></head><body>{main}\n{code_face(M, body)}\n</main>{OPEN_TARGET}</body></html>\n")


# The runbook page sits in the frame the flow, stage and step pages wear (page_style.frame_head): its trail opens the
# map, the flow's page and the stage's page, which one_canvas.py writes at these paths beside it.
MAP_FILE = "views.html"  # the map, in the register folder (run_status.MAP_FILES)
STAGE_FILE = "STAGE.html"  # the stage's own page, beside RUNBOOK.html (one_canvas.STAGE_FILE)
UNTESTED = "No test of this runbook is on record."


def flow_words(M):
    """The flow's page by its title, "Flow: ...", as flow_page.title names it."""
    return f'Flow: {M["flow"]["name"]}'


def stage_words(M):
    return f'Stage {M["stage"]["order"]}: {M["stage"]["name"]}'


def runbook_title(M):
    return f'Stage {M["stage"]["order"]} runbook: {M["stage"]["name"]}'


def tested(M):
    """Whether the register records a test of this runbook. It has no place to record one yet, so never."""
    return False


def untested_line(M):
    """The runbook's untested state, said where a responder lands: under the title and atop each alert's entry."""
    return "" if tested(M) else f'<p class="untested">{UNTESTED}</p>'


def chip(M, r, ret=""):
    """A check's ending as a chip: green to restore, orange to escalate, plain for an ending with no harm. An ending
    that cannot restore here but has a restore action in the register leads to that action's card first: it says
    what to record and whom else to tell before escalating."""
    e, rn = r["ending"], remedy_number(M)
    if e == "restore" and r.get("remedy") in rn:
        return (f'<a class="chip ok" href="#restore-{esc(r["remedy"])}">Yes → Restore: remedy '
                f'{rn[r["remedy"]]}</a>')
    if e in ("cannot restore", "outside") and r.get("remedy") in rn:
        return (f'<a class="chip bad" href="#restore-{esc(r["remedy"])}">Yes → Can’t restore here: remedy '
                f'{rn[r["remedy"]]}, then escalate to the owner of {esc(escalated_part(M, r))}</a>')
    if e in ("restore", "cannot restore", "outside"):
        return (f'<a class="chip bad" href="#escalate">Yes → Can’t restore here: escalate to the owner '
                f'of {esc(escalated_part(M, r))}</a>')
    return f'<span class="chip">Yes → {esc(ENDINGS[e])}</span>'


def entry_anchors(M, m, mode_id):
    """The rows of one alert's entry a responder reaches a check from: the check's own row, else every row whose "also
    check" sends them to it. Empty where the entry neither works nor links it."""
    own = [r["mode_id"] for _, rows, _ in entry_groups(M, m) for r in rows]
    if mode_id in own:
        return [f'{m["handle"]}-{mode_id}']
    lk = entry_links(M, m)
    return [f'{m["handle"]}-{x}' for x in dict.fromkeys(own) if mode_id in lk.get(x, {})]


def back_links(M, mode_ids):
    """"Back to" links, one per row of an alert's entry that reaches any of these checks, each to that row; where one
    alert is reached from more than one row, each link names its check."""
    rows = {r["mode_id"]: r for r in live(M)}
    out = []
    for m in stage_alerts(M):
        anchors = list(dict.fromkeys(a for y in mode_ids for a in entry_anchors(M, m, y)))
        for a in anchors:
            mode = a[len(m["handle"]) + 1:]
            what = f": {question(M, rows[mode])}" if len(anchors) > 1 and mode in rows else ""
            out.append(f'<a href="#{esc(a)}">‹ Back to {esc(m["measure"])}{esc(what)}</a>')
    return " ".join(out)


def check_box(M, r, uses, back):
    """How to check one cause: the same content under its line in an entry and as its card in the reference."""
    linked = ""
    if uses:
        linked = ('<div class="row2"><span><b>If yes, also check, on the same cases:</b> ' + "; ".join(
            f'<a href="#check-{esc(y)}">{esc(question(M, next(x for x in live(M) if x["mode_id"] == y)))}</a>'
            for y in uses) + "</span></div>")
    return ('<div class="box"><div class="lbl">How to check</div>' + how_block(M, r.get("test")) +
            f'<div class="row2"><span><b>Not the cause if</b> {say(M, r.get("expected"))}</span></div>'
            f'<div class="row2"><span><b>The cause if</b> {say(M, r.get("seen"))}</span></div>' + linked +
            f'<div class="row2">{back}</div></div>')


OPENING = (
    ("Is this already known?", "Already known",
     "Look for an open incident, or a known error with a fix in flight, for any of these parts: {parts}. "
     "Not the cause if there is none; the cause if one is open: link it and close."),
    ("Was it planned?", "Planned change",
     "Look for a maintenance window on any of those parts, or a planned change to a timing the stage depends on "
     "({timing}). Not the cause if there is none; the cause if a window is open or a setting was changed on purpose: "
     "link it and close."),
    ("Did something change when it started?", "Roll the change back, or escalate to the owner of the part that changed",
     "Look for any deploy, configuration change or unplanned restart of those parts since the look-back time above. "
     "Not the cause if there is none; the cause if a change lines up with the start."),
    ("Is it already recovering?", "Self-healed",
     "Read the alert's own count over one window{waits}. Not the cause if it is not falling; {recover}"),
)


SPAN = re.compile(r"(?:--since[= ]|\b(?:since|for|over|last)\s+)?<([^<>]*)>([a-zA-Z]*)")
UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "sec": "seconds", "min": "minutes"}


def span_form(M, m):
    """How the look-back goes into a command's time span, from what the entry's commands show: in the unit a
    command's placeholder shows, where every one shows one; else counted in hours as well as days, since a command
    that does not show its unit may take only one of them. Empty where no command of the entry asks for a span."""
    lk = entry_links(M, m)
    rows = [r for _, rs, _ in entry_groups(M, m) for r in rs]
    texts = [unpipe(r.get("test")) for r in rows] + [unpipe(r.get("test")) for r in live(M)
                                                     if any(r["mode_id"] in v for v in lk.values())]
    units = []
    for t in texts:
        for mo in SPAN.finditer(t):
            inner, after = mo.group(1).lower(), mo.group(2).lower()
            if not (mo.group(0).startswith("--since") or re.search(r"\b(window|look-?back|span|duration)\b", inner)):
                continue
            named = next((u for u in ("seconds", "minutes", "hours", "days") if u in inner), None)
            flag = mo.group(0).startswith("--") and "duration flag"
            units.append(UNITS.get(after) or named or flag)
    if not units:
        return ""
    if all(units) and len(set(units)) == 1 and units[0] != "duration flag":
        return f", in {units[0]}, the unit its command shows"
    if set(units) <= {"duration flag", "hours"}:
        flags = sorted({mo.group(0).split("=")[0].split()[0] for t in texts for mo in SPAN.finditer(t)
                        if mo.group(0).startswith("--")})
        return (", written in hours with the unit after the number, as a " + " or ".join(f"<code>{esc(f)}</code>"
                                                                                          for f in flags) +
                " time span takes it: <code>48h</code> for 2 days" +
                ("; where the placeholder is already followed by <code>h</code>, the number alone (<code>48</code>)"
                 if "hours" in units else ""))
    return (", counted in hours as well as days (2 days is 48 hours): a command that does not show its unit may "
            "take only one of them")


def tail_form(M, m):
    """Where a check of the entry reads only the last lines of a log (`--tail`), what a "not found" in them is worth:
    nothing, unless they reach back to the look-back time. Empty where no check does."""
    lk = entry_links(M, m)
    rows = [r for _, rs, _ in entry_groups(M, m) for r in rs] + [r for r in live(M)
                                                               if any(r["mode_id"] in v for v in lk.values())]
    if not any(re.search(r"--tail\b", unpipe(r.get("test"))) for r in rows):
        return ""
    return (" Where a command reads only the last lines of a log (<code>--tail</code>), a line not found there rules "
            "its cause out only if the oldest line returned is older than the look-back time; if it is not, note the "
            "check for the hand-over as not fully run, and go on.")


def entry_html(M, m):
    h = m["handle"]
    lk = entry_links(M, m)

    def own(text):
        """Text about this alert, naming it as "the alert" rather than by its handle."""
        return re.sub(rf"\b{h}\b", "the alert", re.sub(rf"\b{h}'s\b", "this alert's", text))
    cases, win = (own(x) for x in window(M, m))
    win = re.sub(r"^from\s+", "", win)
    groups = entry_groups(M, m)
    parts = ", ".join(name(M, c) for c in M["parts"] if M["subj"][c].get("part_kind") != "person")
    timing = say(M, "; ".join(step_timings(M))) or "the register states none"
    donts = [M["remedies"][x] for x in entry_donts(M, m)]
    out = [f'<section class="doc" id="alert-{esc(h)}">',
           f'<div class="trail"><a href="#top">{esc(runbook_title(M))}</a> › Alert</div>',
           f"<h2>{esc(m['measure'])}</h2>" + untested_line(M),
           (lambda b: b if b.startswith("<div") else f"<p>{b}</p>")(say_prose(M, cap(basis(m))) if basis(m) else
                                                                    "The register states no basis for this alert."),
           *([f"<p>{esc(not_emitted(m))} {NO_DATA_WHAT}</p>"] if not_emitted(m) else []),
           '<p class="small">It has been above the operators’ threshold for longer than their window '
           f'(<a href="ALERT.html#alert-{esc(h)}">the alert</a>).</p>',
           f'<div class="meta"><span><b>Its cases</b> {say(M, cases)}</span></div>',
           f'<div class="meta"><span><b>Look back from</b> {say(M, win)}</span></div>',
           '<div class="now"><div class="lbl">Do now</div><ol>',
           "<li><b>List its cases and set the look-back.</b> Every check below runs on these cases, over that time. "
           + ('List them with the alert’s own count:<details class="how" open><summary>How</summary>'
              f'{count_block(M, m["counted_how"])}</details>' if m.get("counted_how") else
              "The register says nothing about how the alert counts them.") + "</li>",
           f"<li><b>Contain.</b> {say(M, own(contain(M, m, donts=False)))}</li>",
           ("".join('<li class="dont">' + re.sub(r"^(Do not|Never)\b", r"<b>\1</b>", say(M, rem["action"]))
                    + "</li>" for rem in donts) if donts else
            "<li><b>Do not:</b> the register names no action to avoid here.</li>"),
           '<li><b>Escalate or declare</b> as soon as a trigger is met, at any point below. '
           '<a href="#escalate">Triggers ›</a></li></ol></div>',
           '<div class="sec">Check first</div><table class="chk">']
    for n, (q, end, how) in enumerate(OPENING, 1):
        how = how.format(parts=esc(parts), timing=timing,
                         waits=" (for a count of cases waiting, with the oldest only just past the time limit)"
                         if m.get("form") in WAITING else "",
                         recover="it is recovering if the count falls within one window: confirm it is back under its "
                                 "threshold, then close." if m.get("form") in WAITING else
                         "a falling count means only that no new cases are arriving, and the cases it counted stay "
                         "wrong: this check never closes the alert, so go on and work them.")
        if end == "Self-healed" and m.get("form") not in WAITING:
            end = "No new cases: go on and work the ones it counted"
        out.append(f'<tr><td>{n}</td><td>{q}<details class="how"><summary>How</summary><div class="box">{how}'
                   f'</div></details></td><td><span class="chip">Yes → {esc(end)}</span></td></tr>')
    none = no_tests(M, m, groups)
    if none:
        out += ["</table>", f'<div class="sec">Find the cause</div><p>{esc(none)}</p>']
        done = {}
    else:
        out += ["</table>", '<div class="sec">Find the cause <span class="hint">in order, on its cases only. No → '
                "next check. Yes → take its ending for the cases it lists, and go on for the rest. A check whose "
                "evidence lists no cases (a match in a log or a metric) explains no case by itself: note it, if the match falls "
                "inside the look-back, and go on; a "
                "case no later check explains takes the ending of every check noted for it, each named in the "
                "hand-over; where those endings differ, escalate rather than restore. A result you "
                "cannot read, or a check you cannot run: note it for the hand-over and go on. Where a command asks for "
                f"a time span in angle brackets, give it the look-back above{span_form(M, m)}; where it asks for case "
                "ids in angle brackets, give it the ids of the cases you are working." + tail_form(M, m) +
                "</span></div>",
                '<table class="chk">']
        if len(entry_states(M, m)) > 1:
            names = ", ".join(esc(said(b)) for b in entry_states(M, m))
            out.append(f'<tr><td></td><td colspan="2">' + (
                f"Group its cases by the state they are in ({names}) and work each group below that has cases, the "
                "largest first." if recorded(M) else
                f"The states of this stage ({names}) are not recorded, so its cases cannot be grouped by state: work "
                "every group below, in order.") + "</td></tr>")
        k, done = 0, {}
        gone = m.get("form") not in WAITING
        for g, (gh, rows, b) in enumerate(groups):
            if gh and b is None:
                out.append('<tr class="grp"><td></td><td colspan="2">' + (
                    "Shared dependencies: several parts of the stage need them, or they hold cases in several states at "
                    "once" if gh.startswith("Shared dependencies") else esc(gh)) + "</td></tr>")
            elif gh:
                out.append(f'<tr class="grp"><td></td><td colspan="2">Cases in {esc(said(b))}'
                           f'{", or that left the stage from it" if gone else ""}</td></tr>')
            sub = None
            for r in rows:
                k += 1
                if not gh:
                    now = "Is it up?" if is_up(r) else "This alert's own causes"
                    if now != sub and (any(is_up(x) for x in rows) or now != "This alert's own causes"):
                        out.append(f'<tr class="grp"><td></td><td colspan="2">{now}</td></tr>')
                    sub = now
                if r["mode_id"] in done:
                    out.append(f'<tr><td>{k}</td><td>Same as check {done[r["mode_id"]]}: use the result you have for '
                               f"these cases.</td><td></td></tr>")
                    continue
                done[r["mode_id"]] = k
                back = f'<a href="#check-{esc(r["mode_id"])}">The same check in the reference ›</a>'
                out.append(f'<tr id="{esc(h)}-{esc(r["mode_id"])}"><td>{k}</td><td>{esc(question(M, r))}'
                           f'<details class="how"><summary>How</summary>'
                           f'{check_box(M, r, sorted(lk.get(r["mode_id"], {})), back)}</details></td>'
                           f"<td>{chip(M, r)}</td></tr>")
            if gh and b is None and g < len(groups) - 1:
                continue
            last = g == len(groups) - 1
            out.append(f'<tr><td></td><td><b>None of these explains the cases left'
                       f'{" in " + esc(said(b)) if b else ""}.</b></td><td><a class="chip" href="#none">Escalate with '
                       f"what you have</a>{'' if last else ' and go on with the next group'}</td></tr>")
        out.append("</table>")
    out += ['<div class="done">When it is restored or handed over: <a href="#close">Close ›</a> '
            '<a href="#handover">What to hand over ›</a></div>',
            '<details class="small"><summary>For maintainers: this entry’s register ids</summary><ul>'
            f"<li>Alert: {esc(h)}</li>"]
    out += [f"<li>Check {n}: {esc(mid)}</li>" for mid, n in done.items()]
    out += ["</ul></details></section>"]
    return out


def runbook_html(M):
    R, stage, moves = M["R"], M["stage"], M["moves"]
    alerts = stage_alerts(M)
    num, use = numbering(M), users(M)
    rnum = remedy_number(M)
    about = R["about"][0] if R["about"] else {}
    esc_rows = [r for r in live(M) if r["ending"] in ("cannot restore", "outside")]
    also = also_escalated(M, list(rnum) + donts_of(M, M["fm"]))
    failing = list(dict.fromkeys(list(M["parts"]) + [x for r in live(M) for x in parts_of(r)] + [p for p in also if p in M["subj"]]))
    gaps = [c for c in failing if not owner_of(M, c)]
    words = stage_words(M)
    out = ['<section class="doc" id="top">' +
           ps.frame_head([(ps.MAP, f"../{MAP_FILE}"), (flow_words(M), f'../flow-{M["flow"]["flow_id"]}/FLOW.html'),
                          (words, STAGE_FILE)], runbook_title(M)) + untested_line(M),
           '<div class="landing"><div class="col"><div class="lbl">Its alerts</div>']
    out += [f'<a class="card" href="#alert-{esc(m["handle"])}"><b>{esc(m["measure"])}</b>'
            f'<span class="sub">{say(M, m.get("question_it_answers"))}</span></a>' for m in alerts]
    if not alerts:
        out.append('<div class="card">No alert is proposed for this stage in the register.</div>')
    if gaps:
        out.append('<a class="card gap" href="#escalate"><b>Escalation has gaps.</b><span class="sub">No owner is '
                   "named yet for: " + esc(", ".join(name(M, c) for c in gaps)) + "</span></a>")
    # the stage is its own page: one link to it, never a copy of it here
    out += ['</div><div class="col"><div class="lbl">The stage</div>',
            f'<a class="card" href="{STAGE_FILE}"><b>{esc(words)}</b><span class="sub">its process steps, outcomes and '
            "measures</span></a>"]
    # what is at stake, for the call to declare an incident: written in the escalation fold, where that call is made
    stake = [f"<li><b>{esc(a['attribute'])}</b>: {say(M, a['what_is_at_stake'])}</li>"
             for a in R["case-attributes"] if a.get("flow") == M["flow"]["flow_id"]]
    stake += [f"<li><b>Cannot be undone:</b> {say(M, move_name(M, mv))}</li>"
              for mv in M["stage_moves"] if moves[mv].get("irreversible") == "yes"]
    sids = [s["step"] for s in M["steps"]]
    stake += [f"<li>{esc(at_stake(M, i))}: counted "
              f"in {say(M, i.get('unit', ''))}. {say(M, i.get('note', ''))}</li>" for i in R["step-impact"] if i["step"] in sids]
    stake = once(stake)
    stake_html = ("<p><b>What is at stake.</b></p>" + ("<ul>" + "".join(stake) + "</ul>" if stake else
                  "<p>The register states nothing at stake for this stage.</p>"))
    out += ['<div class="lbl" style="margin-top:14px">Shared by every alert</div>']
    # before you start: first, as its name says
    used = list(dict.fromkeys(x for r in live(M) for x in ids(r["measures"])))
    by_part = {}
    for x in used:
        if x in M["measures"]:
            by_part.setdefault(M["measures"][x]["subject_id"], [])
            by_part[M["measures"][x]["subject_id"]] = once(by_part[M["measures"][x]["subject_id"]] +
                                                           [M["measures"][x]["measure"]])
    apps = [c for c in M["parts"] if M["subj"][c].get("band") == "application" and M["subj"][c].get("level") == "component"]
    out += ['<details id="access"><summary>Before you start: the access you need</summary>',
            "<p>You need to be able to read each of these. A check you cannot run is a gap in this runbook: note it.</p>"
            "<ul>"]
    out += once(f"<li><b>{esc(name(M, p))}</b>: {esc('; '.join(ms))}</li>" for p, ms in by_part.items())
    if apps:
        out.append(f"<li><b>Deployment, configuration and restart history</b> for "
                   f"{esc(', '.join(name(M, c) for c in apps))}.</li>")
    out += ["</ul></details>"]
    # every check, written once
    out.append('<details id="checks"><summary>Every check</summary><div class="ref">')
    ent = {m["handle"]: m for m in alerts}
    for t, r in num.items():
        if not r:
            continue
        users_ = [u.split(" ")[0] for u in use[r["mode_id"]]]
        back = back_links(M, [r["mode_id"]])
        used_by = ", ".join(dict.fromkeys(ent[u]["measure"] for u in users_ if u in ent)) or "no proposed alert"
        out.append(f'<div class="card" id="check-{esc(r["mode_id"])}"><h3>{esc(question(M, r))}</h3>'
                   f'<div class="meta"><span><b>Used by</b> {esc(used_by)}</span><span><b>Part</b> '
                   f'{esc(part_names(M, r))}</span><span><b>Reads</b> '
                   + esc("; ".join(M["measures"][x]["measure"] for x in ids(r["measures"]) if x in M["measures"])
                         or "no measure") + "</span></div>" +
                   check_box(M, r, [], back or "") +
                   f'<div class="row2"><span><b>Ending</b> {chip(M, r)}</span></div>'
                   f'<details class="how"><summary>Why this check reads it this way</summary><div class="box">'
                   f'{say(M, r.get("failure"))}</div></details></div>')
    ruled = [r for r in M["fm"] if r.get("ending") == "not possible"]
    if ruled:
        out.append('<details class="how"><summary>Causes the design rules out, so no check is needed</summary><ul>')
        out += once(f"<li>{esc(part_names(M, r))}, {esc(r['mode'])}: "
                    f"{say(M, r['failure'].removeprefix('not possible here:').strip())}</li>" for r in ruled)
        out.append("</ul></details>")
    out.append("</div></details>")
    # restore
    out.append('<details id="restore"><summary>Restore</summary><div class="ref">')
    out.append("<p>After any action that restores: go back to the entry of the alert that fired and run its checks "
               "again for every case still affected, since a restore can leave cases in other states.</p>")
    for rid, n in rnum.items():
        rem = M["remedies"][rid]
        exp = say(M, rem.get("expected", ""))
        if rem["kind"] == "none exists":
            exp = (("Record the case ids and their state, " if recorded(M) else
                    "Record what the checks showed (no record of this stage holds the case ids or states), ") +
                   'and whether new cases are still failing now; then <a href="#escalate">escalate</a>.')
        more = "".join(f"<p>Also escalate to {esc(party_text(M, p))}.</p>" for p, rs in also.items() if rid in rs)
        back = back_links(M, [r["mode_id"] for r in live(M) if r.get("remedy") == rid])
        back = " ".join(x for x in [back] + [
            f'<a href="#restore-{esc(o)}">‹ Back to remedy {k}</a>' for o, k in rnum.items()
            if o != rid and re.search(rf"\b{re.escape(rid)}\b", unpipe(M["remedies"][o].get("if_different", "")))] if x)
        more += f'<div class="row2">{back}</div>' if back else ""
        # a remedy this one sends the responder on to is a link to its card
        body = link_remedies(M, (f"<p><b>{esc(approval_text(M, rid))}</b></p>" if rem.get("needs_approval") == "yes"
                                 else "") + how_block(M, rem.get("action"), prose_ok=True) +
                             f'<div class="row2"><span><b>Expected</b> {exp}</span></div>'
                             f'<div class="row2"><span><b>If different</b> '
                             f'{say(M, rem.get("if_different")) or "escalate to the owner of the failing part."}'
                             "</span></div>")
        out.append(f'<div class="card" id="restore-{esc(rid)}"><h3>Remedy {n}: {esc(rem["kind"])}</h3>{body}{more}</div>')
    if not rnum:
        out.append("<p>The register holds no remedy for this stage's checks.</p>")
    donts = [M["remedies"][x] for x in donts_of(M, M["fm"])]
    if donts:
        out += ["<p><b>What not to do.</b></p><ul>"] + once(f"<li>{say(M, rem['action'])}</li>" for rem in donts) + ["</ul>"]
    out.append("</div></details>")
    # escalate or declare
    out += ['<details id="escalate"><summary>Escalate or declare an incident</summary><div class="ref">',
            "<p><b>Escalate</b> to the owner of the failing part when a check’s ending says to, when a remedy "
            "does not give its expected result, or when one needs approval.</p>",
            '<div class="tw"><table><tr><th>Part</th><th>Owner</th><th>As of</th><th>Responder</th>'
            "<th>Checks that end in escalation to it</th></tr>"]
    for c in failing:
        sc = M["subj"].get(c, {})
        ends = "; ".join(question(M, r) for r in esc_rows if c in parts_of(r)) or "—"
        out.append(f"<tr><td>{esc(name(M, c))}</td><td>{say(M, owner_of(M, c)) or 'none named yet'}</td>"
                   f"<td>{esc(sc.get('owner_as_of') or '—')}</td>"
                   f"<td>{say(M, (sc.get('responder') or '').strip()) or 'none named yet'}</td><td>{esc(ends)}</td></tr>")
    for p, rs in also.items():
        if p not in M["subj"]:
            out.append(f"<tr><td>{esc(party_label(M, p))}</td><td>none named yet</td><td>—</td><td>none named yet</td>"
                       f"<td>— (a remedy escalates to it)</td></tr>")
    out += ["</table></div>",
            "<p><b>Declare an incident</b> when the operators’ severity definition says to: the register holds "
            "no trigger for it. Keep working the entry while it is declared. For that call, what is at stake here is "
            f'below; the stage itself is <a href="{STAGE_FILE}">{esc(words)}</a>.</p>', stake_html,
            '<p id="handover"><b>What to hand over:</b> the alert and what it guards (its entry); ' +
            ("the affected case ids by state" if recorded(M) else
             "the counts the measures showed (no record of this stage holds case ids)") +
            "; whether new cases are still affected now; which checks ran and what they showed; what was contained "
            "and what was done; the look-back time.</p></div></details>"]
    # close
    out += ['<details id="close"><summary>Close</summary><div class="tw"><table><tr><th>Ending</th><th>Close</th></tr>',
            "<tr><td>Already known</td><td>Link the incident, then close.</td></tr>",
            "<tr><td>Planned change</td><td>Link the window or change, then close. Note that the alert should have "
            "been suppressed, if it should.</td></tr>",
            "<tr><td>Self-healed</td><td>Only for an alert that counts cases waiting: confirm it is back under its "
            "threshold, then close. Note that its threshold or window may be wrong.</td></tr>",
            "<tr><td>Restore</td><td>After the action, confirm the alert is under its threshold, no case it counted "
            "is still affected, and new cases get through. Any that remain: back to its entry.</td></tr>",
            "<tr><td>Can’t restore here</td><td>Escalate, and hand over.</td></tr>",
            "<tr><td>None of the checks explains it</td><td>Escalate with what you have, and note the gap in this "
            "runbook.</td></tr></table></div></details>"]
    out += ['<details id="none"><summary>None of the checks explains it</summary><p>For the cases no check '
            'explained: <a href="#escalate">escalate</a> them with what you have, and note the gap in this runbook '
            "(a cause it does not cover, or a check that could not be run). Then go on with the next group of cases "
            "that still has some: an unexplained group does not end the walk for the others.</p></details>"]
    # about
    out += ['<details id="about"><summary>About this runbook <span class="sub">where it comes from, its register ids'
            "</span></summary>",
            f"<p>Generated from the register{' as of ' + esc(about['as_of']) if about.get('as_of') else ''}. "
            + ("The register records no test of it. " if not tested(M) else "") +
            "To change it, change the register and generate it again; never edit this file.</p>",
            '<div class="tw"><table><tr><th>Check</th><th>Failure mode</th><th>Lifecycle rows</th><th>Part</th>'
            "<th>Source</th></tr>"]
    for t, r in num.items():
        if r:
            out.append(f"<tr><td>{esc(question(M, r))}</td><td>{esc(r['mode_id'])} {esc(r['hop'])}: {esc(r['mode'])}"
                       f"</td><td>{esc(', '.join(ids(r['moves'])))}</td><td>{esc(r['part'])}</td>"
                       f"<td>{esc(r.get('source', ''))}</td></tr>")
    out += ["</table></div>"] + (["<p>Remedy <i>n</i> is the register's RM<i>n</i> (<code>remedies.csv</code>).</p>"]
                                 if rnum else [])
    out += ["</details></div></div></section>"]
    for m in alerts:
        out += entry_html(M, m)
    return page_html(M, runbook_title(M), "\n".join(x for x in out if x), "frame rbpage")


def alert_html(M):
    stage, sid = M["stage"], M["stage"]["stage"]
    paging = stage_alerts(M)
    timings = "; ".join(step_timings(M))
    out = ['<section class="doc">' + ps.frame_head(  # the runbook page's frame, with the runbook as the last step
               [(ps.MAP, f"../{MAP_FILE}"), (flow_words(M), f'../flow-{M["flow"]["flow_id"]}/FLOW.html'),
                (stage_words(M), STAGE_FILE),
                ("Runbook (not yet written)", None) if M.get("runbook_pending") else ("Runbook", "RUNBOOK.html")],
               f"Alerts proposed: {stage['name']}"),
           ("<p>Each is its own alert. " + esc(RUNBOOK_LATER) if M.get("runbook_pending") else
            "<p>Each is its own alert. When one fires, follow its own entry in "
            '<a href="RUNBOOK.html">the runbook</a>.') + " Thresholds, windows and whether an alert pages a person "
           "are the operators’ values, not set here.</p></section>"]
    if not paging:
        out.append('<section class="doc"><p>No alert is proposed for this stage in the register.</p></section>')
    for m in paging:
        h = m["handle"]
        rows = ([("Where it is placed", say(M, placed(M, m)))] if elsewhere(paging) else []) + [
                ("The question it answers", say(M, m.get("question_it_answers"))),
                ("What it counts", count_block(M, m.get("counted_how")) +
                 f'<p class="small">Counted on {esc(m.get("counted_on"))}.</p>'),
                ("Why it is proposed", and_not_emitted(say_prose(M, basis(m)) or "the register states no basis for it", m)),
                ("Which cases its entry works", say_prose(M, alert_grouping(M, m, False))),
                ("Threshold", say(M, THRESHOLD)),
                ("Window", "<i>Operator value, not set here.</i> How long the condition must hold before it fires."
                 + (f" What the design assumes about time: {say(M, timings)}." if timings else ""))]
        if m.get("form") in WAITING and m.get("counted_on") == "cases":
            limit = time_limit(stage.get("bound_in_code"))
            rows.append(("Time limit", "<i>Operator value.</i> How old a waiting case may be is the operators’ value"
                                      + (f"; the stage’s time limit in the code: {say(M, limit)}" if limit else ".")))
        rows += [("No data", "It also fires when its measure cannot be counted for longer than the window. A count "
                             "that finds no events in a window is zero, not missing data. A count fails when what it is "
                             "read from is down; What it counts says where that is."),
                 ("Symptom, not cause", "It fires on what happens to cases, not on any component’s errors. "
                                        "Telling causes apart is the runbook’s job." if m.get("counted_on") == "cases"
                  else f"It fires on its {esc(level(m))}’s count of {esc(m.get('counted_on') or 'what it counts')}, "
                       "which is not a count of cases. Telling causes apart is the runbook’s job."),
                 ("Exists today", "yes" + (f", but misleading: {say(M, m['defect'])}" if m.get("defect") else "")
                  if m.get("exists") == "yes" else "no, proposed")]
        out += [f'<section class="doc" id="alert-{esc(h)}"><h2>{esc(m["measure"])}</h2>',
                ("" if M.get("runbook_pending") else
                 f'<p><a href="RUNBOOK.html#alert-{esc(h)}">Its entry in the runbook ›</a></p>'),
                '<div class="tw"><table>'] + [f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows]
        out += ["</table></div>", '<details class="small"><summary>For maintainers: register ids and sources'
                f"</summary><ul><li>Measure: {esc(h)}</li><li>Emitted at: {esc(m.get('source_ref') or '—')}</li>"
                f"<li>Basis as written: {esc(m.get('alert'))}</li></ul></details></section>"]
    if not M.get("runbook_pending"):
        used = list(dict.fromkeys(x for r in live(M) for x in ids(r["measures"])))
        comp = [M["measures"][x]["measure"] for x in used if x in M["measures"] and x not in [m["handle"] for m in paging]]
        out += ['<section class="doc"><h2>Companion measures</h2><p>Read by the runbook’s checks, not proposed for '
                "alerting:</p><ul>"] + once(f"<li>{esc(x)}</li>" for x in comp) + ["</ul></section>"]
    return page_html(M, f"Alerts: {stage['name']}", "\n".join(out), "frame rbpage")


WRITERS = {name: (lambda fn: lambda M: relabel_prose(M["labels"], M["R"]["steps"], fn(M)))(fn) for name, fn in
           {"STRUCTURE.md": structure, "MEASURES.md": measures, "ALERT.md": alert, "RUNBOOK.md": runbook,
            "ALERT.html": alert_html, "RUNBOOK.html": runbook_html}.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("register")
    ap.add_argument("flow")
    ap.add_argument("stage")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true")
    stage_of_work = ap.add_mutually_exclusive_group()
    stage_of_work.add_argument("--alerts", action="store_true")
    stage_of_work.add_argument("--runbooks", action="store_true")
    stage_of_work.add_argument("--measures", action="store_true")
    a = ap.parse_args(argv)
    part = "alerts" if a.alerts else "runbooks" if a.runbooks else "measures" if a.measures else "all"
    R = load(a.register)
    flows = [f["flow_id"] for f in R["flows"]]
    if a.flow not in flows:
        print(f"{a.flow} is not a flow of this register; its flows: {', '.join(flows)}")
        return 2
    mine = [s["stage"] for s in R["stages"] if s["flow"] == a.flow]
    if a.stage not in mine:
        print(f"{a.stage} is not a stage of flow {a.flow}; its stages: {', '.join(mine) or 'none'}")
        return 2
    M = build(R, a.flow, a.stage)
    M.update(register=a.register, out=a.out or "<dir>")
    depth = (go.load(a.register) or {}).get("depth")
    measures_only = a.measures  # what this call writes: a measured stage's pages, its alert pages, or all of them
    alerts_only = a.alerts
    if depth is not None:  # the person chose which stages are measured: the receipt owes theirs and the flow's
        M["measured"] = {s for s, d in depth.items() if d != "none"}
        if not (a.alerts or a.runbooks or a.measures):
            # with no stage of work named (as when a stale stage is regenerated), a stage is checked and written for
            # what its depth does, never for more
            d = depth.get(a.stage, "none")
            part = {"none": "measures", "measure": "measures", "alerting": "alerts"}.get(d, "all")
            measures_only, alerts_only = d in ("none", "measure"), d == "alerting"
    has_pick, picked = go.pick_state(a.register)
    if a.out and has_pick and not picked:
        print("REFUSED: the person has not picked how far each stage goes, so nothing is measured yet. Show them the "
              f"mapped stages, and record their answer with: python go.py {a.register} --depth \"<id>=measure,...\" "
              "--words \"<their words>\"")
        return 2
    if a.runbooks and a.out and stage_alerts(M) and not (pathlib.Path(a.out) / "ALERT.md").is_file():
        print(f"REFUSED: the runbooks stage comes after the alerting stage, and {pathlib.Path(a.out) / 'ALERT.md'} "
              f"is not there. Run the alerting stage first: python flow_outputs.py {a.register} {a.flow} {a.stage} "
              f"--out {a.out} --alerts, and "
              "have the person review the alerts.")
        return 2
    if a.out and not (alerts_only or measures_only):  # a runbook, by --runbooks or plain --out, follows the review
        has_row, reviewed = go.review_state(a.register)
        if has_row and not reviewed:
            print("REFUSED: the person has not said go on the proposed alerts, so no runbook is written. Show them the "
                  f"alerts, and record their answer with: python go.py {a.register} --alerts-reviewed --decision "
                  "go|changes --words \"<their words>\"")
            return 2
    if a.out and not measures_only and not a.alerts:
        # alert pages written again, at alerting or runbooks depth, must still be the alerts the person reviewed; only the
        # alerting stage run by name (--alerts) writes changed alerts, and it reopens their review
        done = (go.load(a.register) or {}).get("alerts_reviewed")
        if done and done.get("alerts") != go.alert_fingerprint(a.register):
            print("REFUSED: the alerts have changed since the person reviewed them (an alert's basis, expectation or "
                  "counted moves in measures.csv). Run the alerting stage again: python flow_outputs.py "
                  f"{a.register} {a.flow} {a.stage} --out {a.out} --alerts, and bring the change to them.")
            return 2
    if a.runbooks:
        # the alert rules run again: a change made after the review must not reach the alert pages unchecked
        part = "all"
    err, warn = check(M, part)
    for w in warn:
        print(w if w.startswith("note: ") else "warning: " + w)
    for e in err:
        print("ERROR:", e)
    rec, gapped, r_err, r_warn = receipt_failures(M["R"], a.flow, a.stage, M.get("measured"))
    print(f"receipt for {a.flow}: {len(rec)} elements, {sum(r['covered'] for r in rec)} covered by a candidate, "
          f"{sum((r['element'], r['question']) in gapped and not r['covered'] for r in rec)} gapped, "
          f"{sum(e.startswith('receipt:') for e in r_err + r_warn)} neither; "
          f"{sum(1 for r in rec if r['stages'] and a.stage not in r['stages'])} belong only to other stages")
    if not [m for m in R["lifecycle"] if m.get("flow", a.flow) in (a.flow, "")]:
        print(f"receipt for {a.flow}: its step set is partial: with no lifecycle rows, no stage's exit and not the "
              f"flow's first step are in it")
    notes = sum(w.startswith("note: ") for w in warn)
    print(f"{len(err)} errors, {len(warn) - notes} warnings" + (f", {notes} note{'s' * (notes > 1)}" if notes else ""))
    if a.out:
        out = pathlib.Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        alerting = bool(stage_alerts(M))
        if alerts_only:
            # the alerts are under review: a runbook left by an earlier run no longer follows from them; only the
            # alerting stage itself, run by name, opens the review again
            M["runbook_pending"] = True
            if a.alerts:
                go.reset_review(a.register)
            for fname in ("RUNBOOK.md", "RUNBOOK.html"):
                (out / fname).unlink(missing_ok=True)
        owed = (() if measures_only else ("ALERT.md", "ALERT.html") if alerts_only else
                ("ALERT.md", "RUNBOOK.md", "ALERT.html", "RUNBOOK.html"))
        # a stage measured on its own is done only when its measure check passes: its measures page waits for that
        always = ("STRUCTURE.md",) if measures_only else ("STRUCTURE.md", "MEASURES.md")
        if measures_only:
            owed = ("MEASURES.md",)
        with ps.home_beside(out.parent):  # the map sits one folder up from a stage's pages
            for fname in always + (() if err else owed):
                if fname.startswith("ALERT.") and not alerting:  # no alert, no alert page: one left by an earlier run goes
                    (out / fname).unlink(missing_ok=True)
                    continue
                (out / fname).write_text(WRITERS[fname](M) + stamp(a.register, a.flow, a.stage), encoding="utf-8")
                print("wrote", out / fname)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
