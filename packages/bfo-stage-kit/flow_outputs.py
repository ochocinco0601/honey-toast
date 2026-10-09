"""Every output for one stage of one flow, read off the register's lifecycle.

STRUCTURE.md (the slice as a tree with branches), MEASURES.md (where each measure is counted, by level and layer),
ALERT.md (what pages, from the measures marked `pages`) and RUNBOOK.md (a branched checklist: one branch per state a
case can be left in, one test per failure mode in failure-modes.csv). All four share the register's step numbers.

Usage: flow_outputs.py <register dir> <flow id> <stage id> --out <dir>      check, then write all four
       flow_outputs.py <register dir> <flow id> <stage id> --check          check only

The check fails the run when a move of the stage has a hop, a carrier or a need with no failure mode, when a failure
mode names a part its move does not use, and on the other rules listed in `check`. STRUCTURE.md and MEASURES.md are
written even when it fails; ALERT.md and RUNBOOK.md are not."""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from capability_views import read_csv, ids  # noqa: E402

TABLES = ["about", "flows", "capabilities", "stages", "steps", "subjects", "participation", "measures", "lifecycle",
          "failure-modes", "remedies", "step-impact", "case-attributes"]
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
REMEDY_KINDS = ("restore", "re-drive", "roll back", "none exists", "do not")
RESTORING = ("restore", "re-drive", "roll back")
RECOVERY = ("moves on", "stranded", "not created", "")
LAYERS = ["business health", "business impact", "application", "technology"]
HEAD = ["Business health<br>is the expectation met? (counted on cases)", "Business impact<br>for how many cases is it not?",
        "Application<br>how did the software behave?", "System<br>how did the infrastructure behave?"]


# ---------------------------------------------------------------- reading

def load(reg):
    reg = pathlib.Path(reg)
    R = {t: [{k: cell(v) for k, v in r.items()} for r in read_csv(reg / f"{t}.csv")] for t in TABLES}
    R["hop-failures"] = read_csv(HERE / "method" / "hop-failures.csv")
    R["_name"] = reg.name
    return R


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
             unresolved=unresolved)
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
    M["pages"] = [m for m in R["measures"] if m.get("pages", "").lower() == "yes"]
    M["parts"] = list(dict.fromkeys(x for s in steps for x in M["performers"][s["step"]] + M["supporters"][s["step"]]))
    return M


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


def kind(sc):
    if sc.get("part_kind") == "person":
        return "Person"
    if sc.get("level") == "external dependency":
        return "External dependency"
    return "Application component" if sc.get("band") == "application" else "System component"


# ---------------------------------------------------------------- the check

def check(M):
    """(errors, warnings). An error fails the run."""
    err, warn = [], []
    R, moves, sm = M["R"], M["moves"], M["stage_moves"]
    for tok in dict.fromkeys(M["unresolved"]):
        err.append(f"lifecycle.csv names {tok!r} in carried_by or needs, and no subjects.csv row is it: write its subject id")
    for s in M["steps"]:
        if not M["step_moves"][s["step"]]:
            msg = f"steps.csv step {s['step']}: its source names no lifecycle row (L..)"
            if s.get("source", "").lower().startswith("reference model"):
                warn.append(msg + ", so it is drawn not assessed")
            else:
                err.append(msg + "; only a reference-model step nothing carries may have none")
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
    cat = {(h["hop_kind"], h["mode"]) for h in R["hop-failures"]}
    for r in M["fm"]:
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
            if r["part"] not in allowed:
                err.append(f"failure-modes.csv {i}: part {r['part']} is not in lifecycle {mv}'s "
                           f"{'needs' if r['hop'] == 'needs' else 'carried_by or needs'}")
            if r["hop"] != "needs" and r["hop"] not in M["hops"][mv]:
                err.append(f"failure-modes.csv {i}: lifecycle {mv} does not travel by {r['hop']}")
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
    for rid, rem in M["remedies"].items():
        if rem.get("kind") not in REMEDY_KINDS:
            err.append(f"remedies.csv {rid}: kind {rem.get('kind')!r} is not one of {', '.join(REMEDY_KINDS)}")
    covered = {}
    for r in M["fm"]:
        for mv in ids(r["moves"]):
            covered.setdefault(mv, []).append(r)
    for mv in sm:
        rows = covered.get(mv, [])
        if not rows:
            err.append(f"lifecycle {mv} ({moves[mv]['move']}): no failure mode at all")
            continue
        for h in M["hops"][mv]:
            for c in R["hop-failures"]:
                if c["hop_kind"] == h and not any(r["hop"] == h and r["mode"] == c["mode"] for r in rows):
                    err.append(f"lifecycle {mv}: hop {h}, mode {c['mode']!r} has no failure mode row (write one, or "
                               f"ending 'not possible' with the citation)")
        for need in M["needs"][mv]:
            for c in R["hop-failures"]:
                if c["hop_kind"] == "needs" and not any(r["hop"] == "needs" and r["part"] == need and r["mode"] == c["mode"]
                                                        for r in rows):
                    err.append(f"lifecycle {mv}: need {need} ({name(M, need)}), mode {c['mode']!r} has no failure mode row")
        for part in M["carried"][mv]:
            if not any(r["part"] == part for r in rows):
                err.append(f"lifecycle {mv}: carrier {part} ({name(M, part)}) has no failure mode row")
    for b in M["branch_states"]:
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
    for m in M["pages"]:
        if m.get("stage") != sid or m.get("counted_on") != "cases":
            if m.get("stage") and m.get("stage") != sid and m.get("counted_on") == "cases":
                continue
            err.append(f"measures.csv {m['handle']}: pages, but only a measure of a stage counted on cases pages")
    if not [m for m in M["pages"] if m.get("stage") == sid]:
        err.append(f"measures.csv: no measure of stage {sid} is marked pages, so there is no alert to write")
    parks = any(moves[mv].get("from_kind") == "park" for mv in sm)
    for m in M["pages"]:
        if m.get("stage") == sid and not parks and m.get("form") in ("backlog", "cycle time"):
            err.append(f"measures.csv {m['handle']}: pages on a {m['form']}, but stage {sid} never parks, so cases cannot "
                       "pile up in it: page on the cases leaving by its exception endings or left stranded (a failure "
                       "rate counted on cases)")
    return err, warn


# ---------------------------------------------------------------- STRUCTURE.md

def q(s):
    return (s or "").replace('"', "'").replace("\\|", "/")


def shown(st):
    if st == "(none)":
        return "the case is created"
    return st.removeprefix("implicit:").strip() + " (not recorded)" if st.startswith("implicit:") else st


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
        t.append(f'  P{s["step"]}["Step {s["step"]}: <b>{q(s["name"])}</b>{na}"]')
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
    key = ("**How to read it.** Solid arrows between steps follow the case: each is labelled with the state the case is "
           "in when the next step starts. Where several arrows leave one step, they are alternatives: one case takes one "
           "of them. **Done by** is every part that carries the step out; **needs** is a part it cannot complete without "
           "that does not itself carry the step out. Step numbers are the register's, and every other output uses the same ones.")
    side = [s["step"] for s in M["steps"] if M["step_moves"][s["step"]]
            and all(side_move(M["moves"][mv]) for mv in M["step_moves"][s["step"]])]
    if side:
        key += " Step " + ", ".join(side) + " changes no state of the case: it happens alongside, and nothing waits on it."
    return (f"# {flow['name']}: stage {stage['order']} of {len(stages)}, {stage['name']}\n\n{key}\n\n"
            "```mermaid\n" + "\n".join(t) + "\n```\n")


# ---------------------------------------------------------------- MEASURES.md

def mlabel(m, sid):
    pages = " **pages**" if m.get("pages", "").lower() == "yes" and m.get("stage") == sid else ""
    return f'{m["handle"]} {m["measure"]} ({"exists" if m.get("exists") == "yes" else "proposed"}){pages}'


def measures(M):
    R, subj, stage = M["R"], M["subj"], M["stage"]
    sid = stage["stage"]
    step_ids = [s["step"] for s in M["steps"]]
    rows = [(f"**Stage {stage['order']}: {stage['name']}**", [m for m in R["measures"] if m.get("stage") == sid])]
    for s in M["steps"]:
        doers = ", ".join(name(M, c) for c in M["performers"][s["step"]]) or "nothing"
        rows.append((f"Step {s['step']}: {s['name']} (done by {doers})",
                     [m for m in R["measures"] if m.get("step") == s["step"]
                      and subj.get(m["subject_id"], {}).get("part_kind") == "case"]))
    for c in M["parts"]:
        if subj[c].get("part_kind") == "person":
            continue
        rows.append((f"{kind(subj[c])}: {subj[c]['name']}",
                     [m for m in R["measures"] if m["subject_id"] == c and m.get("step", "") in step_ids + [""]
                      and not m.get("stage")]))
    md = ["| | " + " | ".join(HEAD) + " |", "|---|" + "---|" * len(HEAD)]
    for label, ms in rows:
        md.append("| " + label + " | " + " | ".join("<br>".join(mlabel(m, sid) for m in ms if m["layer"] == lay) or "none"
                                                     for lay in LAYERS) + " |")
    how = ["| Measure | Counted on | Counted how | Exists today |", "|---|---|---|---|"]
    for _, ms in rows:
        for m in ms:
            how.append(f'| {m["handle"]} {m["measure"]} | {m.get("counted_on", "")} | '
                       f'{m.get("counted_how", "")} | '
                       f'{"yes: " + m.get("source_ref", "") if m.get("exists") == "yes" else "no, proposed"} |')
    paging = [m["handle"] for m in M["pages"] if m.get("stage") == sid]
    head = [f"# {M['flow']['name']}: stage {stage['order']} of {len(M['stages'])}, {stage['name']}: where each measure is counted", "",
            f"**Expected of the stage:** {stage.get('promise', '').removeprefix('proposed: ')}. The time limit is the operators' to set.", "",
            f"**What pages:** {', '.join(paging) or 'nothing'}, the measures marked **pages** below, and nothing else. "
            "The alert is in [ALERT.md](ALERT.md); when it fires, follow [RUNBOOK.md](RUNBOOK.md). Every other measure is "
            "not paged on; the runbook's tests read the ones ALERT.md lists as companion measures.", "",
            "Step numbers are the register's. A step's row holds the measures counted on the case at that step; each "
            "component's row holds its own.", ""]
    return "\n".join(head) + "\n" + "\n".join(md) + "\n\n## How each measure is counted\n\n" + "\n".join(how) + "\n"


# ---------------------------------------------------------------- ALERT.md

def alert(M):
    stage, sid, moves = M["stage"], M["stage"]["stage"], M["moves"]
    paging = [m for m in M["pages"] if m.get("stage") == sid]
    stranded = [mv for mv in M["stage_moves"] if moves[mv].get("recovery") == "stranded"]
    timings = [f"{mv}: {moves[mv]['timing']}" for mv in M["stage_moves"] if moves[mv].get("timing")]
    rows = [("The question it answers", " ".join(m.get("question_it_answers", "") for m in paging)),
            ("What it counts", "<br>".join(f"**{m['handle']}** {m['measure']}: {m.get('counted_how', '')} "
                                           f"(counted on {m.get('counted_on')})" for m in paging)),
            ("Grouping", ("By the state the case is in: " + ", ".join(f"`{shown(b)}`" for b in M["branch_states"]) +
                          ". The state tells the responder which branch of the runbook to work.") if recorded(M) else
             ("None. The states of this stage (" + ", ".join(f"`{shown(b)}`" for b in M["branch_states"]) +
              ") are not recorded, so cases cannot be grouped by state; the runbook works every branch in order.")),
            ("Threshold", "*Operator value, not set here.* The count above which a person is paged."),
            ("No data", "The alert also fires when its measure cannot be counted (the query fails or returns no data "
                        "for longer than the window). That happens when a part the count itself runs on is down, and then cases "
                        "pile up unseen. Of the parts the stage's moves need, check which the count runs on: "
                        + ", ".join(name(M, c) for c in M["parts"] if M["subj"][c].get("band") == "technology"
                                    or M["subj"][c].get("level") == "external dependency") + "."),
            ("Age bound", f"*Operator value.* The stage's promise: {stage.get('promise', '')}"),
            ("Window", "*Operator value, not set here.* How long the condition must hold before the alert fires." +
             (" What the design assumes about time: " + "; ".join(timings) if timings else "")),
            ("Why it pages a person", ("Cases left by these moves are stranded, with nothing in the application to move "
                                       "them: " + "; ".join(f"{mv} {moves[mv]['move']} ({moves[mv]['if_not']})" for mv in stranded))
             if stranded else "No move of this stage strands a case; the alert pages because the stage's promise is missed."),
            ("Symptom, not cause", "It fires where cases pile up, not on any component's errors. Telling causes apart is "
                                   "the runbook's job."),
            ("Exists today", "; ".join(f"{m['handle']}: {'yes, ' + m.get('source_ref', '') if m.get('exists') == 'yes' else 'no, proposed'}"
                                       for m in paging))]
    used = list(dict.fromkeys(h for r in M["fm"] if r.get("ending") != "not possible" for h in ids(r["measures"])))
    out = [f"# Alert: cases past the promise in \"{stage['name']}\"", "",
           f"**Stage {stage['order']} of {len(M['stages'])}:** {stage['name']}, in flow {M['flow']['name']}. Steps "
           f"{', '.join(s['step'] for s in M['steps'])}. When it fires, follow [RUNBOOK.md](RUNBOOK.md).", "",
           "| | |", "|---|---|"] + [f"| **{k}** | {v} |" for k, v in rows]
    out += ["", "## Companion measures", "", "Read by the runbook's tests, never paged on:", ""]
    out += [f"- {h} {M['measures'][h]['measure']}" for h in used if h in M["measures"] and h not in [m["handle"] for m in paging]]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- RUNBOOK.md

def ending_text(M, r):
    e = ENDINGS[r["ending"]]
    if r["ending"] == "restore":
        return f"**{e}**: §5 {r['remedy']}"
    if r["ending"] == "cannot restore":
        return f"**{e}**: escalate (§7)" + (f"; §5 {r['remedy']} says what to record" if r.get("remedy") else "")
    return f"**{e}**"


def mtext(M, h):
    m = M["measures"].get(h, {})
    return f"{h} ({m.get('measure', '?')}: {m.get('counted_how', '')})"


def outcome(s):
    o = s['right_outcome']
    return "(proposed) " + o.removeprefix('proposed: ') if o.startswith('proposed: ') else o


def runbook(M):
    R, stage, sid, moves = M["R"], M["stage"], M["stage"]["stage"], M["moves"]
    about = R["about"][0] if R["about"] else {}
    paging = [m for m in M["pages"] if m.get("stage") == sid]
    ph = ", ".join(m["handle"] for m in paging)
    out = [f"# Runbook: cases past the promise in \"{stage['name']}\"", "",
           "Entered from [ALERT.md](ALERT.md). Laid out in the anatomy of the runbook model. Generated from the register by "
           "`flow_outputs.py`: every branch is a state from `lifecycle.csv`; after the standing tests at the start of "
           "§4, every test is a row of `failure-modes.csv`. "
           "State: draft, never rehearsed. Step numbers are the register's.", ""]
    out += ["## 0. The slice", "", f"**Configuration described:** {about.get('what_it_is', 'not stated')}", "",
            f"Flow **{M['flow']['name']}**, one case: {strip_parens(M['flow']['case']).split(':')[0].strip()}. Stage "
            f"{stage['order']} of {len(M['stages'])}, **{stage['name']}**. [STRUCTURE.md](STRUCTURE.md) draws the same "
            "steps and [MEASURES.md](MEASURES.md) measures them.", "",
            "| Step | Right outcome | From → to | Path | Done by | Needs |", "|---|---|---|---|---|---|"]
    for s in M["steps"]:
        mvs = M["step_moves"][s["step"]]
        ft = "; ".join(f"{state(moves[m]['from_state'])} → {state(moves[m]['to_state'])}" for m in mvs)
        out.append(f"| Step {s['step']}: {s['name']} | {outcome(s)} | {ft} | "
                   f"{', '.join(dict.fromkeys(moves[m]['path'] for m in mvs))} | "
                   f"{', '.join(name(M, c) for c in M['performers'][s['step']])} | "
                   f"{', '.join(name(M, c) for c in M['supporters'][s['step']]) or '—'} |")
    out.append("")
    last = [s for s in M["steps"] if to_states(M, s["step"]) & set(M["exits"])]
    out += ["## 1. Alert and expectation", "",
            "**What fired.** " + "; ".join(f"{m['handle']} {m['measure']}" for m in paging) +
            ": above the operators' threshold for longer than their window.", "",
            f"**The expectation it guards.** A case that enters this stage leaves it within the promise "
            f"({stage.get('promise', '')}), in one of these ways:", ""]
    out += [f"- Step {s['step']}: {s['name']}: {outcome(s)}" for s in last]
    stranded = [mv for mv in M["stage_moves"] if moves[mv].get("recovery") == "stranded"]
    if stranded:
        out += ["", "**Why a person is paged.** A case left by " + ", ".join(stranded) +
                " is stranded: nothing in the application moves it again."]
    out += ["", "Check §7's triggers at every step, not only at the end.", ""]
    out += ["## 2. What is at stake", ""]
    for a in R["case-attributes"]:
        if a.get("flow") == M["flow"]["flow_id"]:
            out.append(f"- **{a['attribute']}**: {a['what_is_at_stake']}")
    for mv in M["stage_moves"]:
        if moves[mv].get("irreversible") == "yes":
            out.append(f"- **Irreversible:** {moves[mv]['move']} ({mv}) cannot be undone.")
    step_ids = [s["step"] for s in M["steps"]]
    for i in R["step-impact"]:
        if i["step"] in step_ids:
            out.append(f"- Step {i['step']}: {i['impact_category']}, counted in {i.get('unit', '')}. {i.get('note', '')}".rstrip(". ") + ".")
    out += ["- **Declare an incident** when the impact threshold in the severity definition is crossed: an operator value, "
            "linked here.", ""]
    used = list(dict.fromkeys(h for r in M["fm"] if r.get("ending") != "not possible" for h in ids(r["measures"])))
    by_part = {}
    for h in used:
        if h in M["measures"]:
            by_part.setdefault(M["measures"][h]["subject_id"], []).append(h)
    out += ["## 3. Before you start", "", "You need to be able to read each of these. A step you cannot run is a defect: "
            "record the runbook as *failed* and add the access to the access gaps.", ""]
    for sidp, hs in by_part.items():
        out.append(f"- **{name(M, sidp)}**: " + "; ".join(mtext(M, h) for h in hs))
    apps = [c for c in M["parts"] if M["subj"][c].get("band") == "application" and M["subj"][c].get("level") == "component"]
    out += [f"- **Deployment, configuration and restart history** for {', '.join(name(M, c) for c in apps)}.", ""]
    out += ["## 4. Tests that find the ending", "",
            "Run them in order. Every result has a route: the expected result goes on to the test named; the result "
            "this test looks for ends the walk at its ending; anything else (an unclear answer, a step you cannot run) "
            "is noted for the hand-over and goes on as shown.", "",
            "| # | Test | Measures | Expected if this is not the cause | If it is | Ending | Anything else |",
            "|---|---|---|---|---|---|---|"]
    every = ", ".join(name(M, c) for c in M["parts"] if M["subj"][c].get("part_kind") != "person")
    timing = "; ".join(moves[mv]["timing"] for mv in M["stage_moves"] if moves[mv].get("timing"))
    groups = ", ".join(f"`{shown(b)}`" for b in M["branch_states"])
    apps_s = ", ".join(name(M, c) for c in apps)
    items = [("test", dict(t=f"Is there an open incident, or a known error with a fix in flight, for {every}?", m="—",
                           e="None", s="One is open", end="**Already known**")),
             ("test", dict(t=f"Is there a maintenance window on any of those parts, or a planned change to a timing the "
                             f"stage depends on ({timing or 'none stated'})?", m="—", e="None",
                           s="A window, or a setting changed on purpose",
                           end="**Expected condition** (add *alert needs changing* if it should have been suppressed)")),
             ("test", dict(t=f"**What changed:** any deploy, configuration change or unplanned restart of {every} since "
                             "the count started rising?", m="—", e="None", s="A change lines up with the start",
                           end="Roll it back through the change-approval path, or escalate to the change owner (§7); "
                               "then re-run T4")),
             ("test", dict(t=(f"Group the cases past the promise by the state they are in ({groups}). Is the count "
                              "falling, with the oldest only just past the bound?") if recorded(M) else
                           (f"Is the count falling, with the oldest only just past the bound? The states of this stage "
                            f"({groups}) are not recorded, so the cases cannot be grouped by state: work every branch "
                            "below, in order"), m=ph,
                           e="Not falling. If the cases sit in several states, work every branch below that has cases, "
                             "the largest group first", s="Falling within one window",
                           end="**Self-healed** (mark *threshold or duration wrong*)"))]
    tid = {}
    order = list(M["stage_moves"])

    def sort_key(r):
        mvs = [x for x in ids(r["moves"]) if x in order]
        first = mvs[0] if mvs else ""
        hops = M["hops"].get(first, [])
        # a test that closes with no impact runs after every test that finds a fault: the same signal may be either
        return (r.get("ending") in BENIGN, min((order.index(x) for x in mvs), default=99),
                hops.index(r["hop"]) if r["hop"] in hops else len(hops), r["mode_id"])

    def fm_item(r):
        return ("test", dict(fm=r["mode_id"], t=f"{r['test']} *({r['mode_id']}: {name(M, r['part'])}, {r['hop']}: "
                                                f"{r['mode']}; {', '.join(ids(r['moves']))})*",
                             m="; ".join(mtext(M, h) for h in ids(r["measures"])), e=r["expected"], s=r["seen"],
                             end=ending_text(M, r)))

    active = [r for r in M["fm"] if r.get("ending") != "not possible"]
    sh = [r for r in active if shared(M, r)]
    if sh:
        items.append(("head", "Shared dependencies: they leave cases in several states at once, so test them first"))
        items += [fm_item(r) for r in sorted(sh, key=sort_key)]
        items.append(("end", "the branch of the largest group of cases (below)"))
    placed = {r["mode_id"] for r in sh}
    for b in M["branch_states"]:
        rows = [r for r in active if b in branch_of(M, r) and not shared(M, r)]
        mvs = [mv for mv in M["stage_moves"] if state(moves[mv]["from_state"]) == b]
        items.append(("head", f"Cases left in **{shown(b)}**: the move out did not happen "
                              "(" + "; ".join(mv + " " + moves[mv]["move"] for mv in mvs) + ")"))
        for r in sorted(rows, key=sort_key):
            item = fm_item(r)
            item[1]["again"] = r["mode_id"] in placed
            placed.add(r["mode_id"])
            items.append(item)
        items.append(("outside", b))
        items.append(("end", "the next branch that still has cases; when none is left, **Outside this runbook** (§8)"))
    n = 0
    for k, (what, x) in enumerate(items):
        if what == "test":
            n += 1
            x["id"] = f"T{n}"
            if x.get("fm") and x["fm"] not in tid:
                tid[x["fm"]] = x["id"]
            elif x.get("fm"):
                x["t"] += f" Same check as {tid[x['fm']]}: if you ran it there, use that result here."
    for k, (what, x) in enumerate(items):
        if what != "test":
            continue
        nxt = next((y for w, y in items[k + 1:] if w in ("test", "end", "outside")), None)
        nw = next((w for w, y in items[k + 1:] if w in ("test", "end", "outside")), None)
        route = (f"→ {nxt['id']}" if nw == "test" else f"→ nothing in this branch explains the cases in {shown(nxt)}: escalate them "
                 "as **Outside this runbook** (§8), then work the next branch that still has cases" if nw == "outside" else f"→ {nxt}" if nxt else "→ T5")
        if x["id"] == "T4" and nw:
            route = f"→ {nxt['id'] if nw == 'test' else nxt}"
        x["route"] = route
    for what, x in items:
        if what == "test":
            out.append(f"| {x['id']} | {x['t']} | {x['m']} | {x['e']} {x['route']} | {x['s']} | {x['end']} | "
                       f"Note it for the hand-over; {x['route']} |".replace("\n", " "))
        elif what == "head":
            out.append(f"| | **{x}** | | | | | |")
        elif what == "note":
            out.append(f"| | {x} also applies here: see {tid.get(x, x)} | | | | | |")
        elif what == "outside":
            out.append(f"| | None of the above explains the cases in {shown(x)} | | | | **Outside this runbook** (§8) | |")
    ruled = [r for r in M["fm"] if r.get("ending") == "not possible"]
    if ruled:
        out += ["", "**Ruled out by the design** (no test needed):", ""]
        out += [f"- {r['mode_id']} {name(M, r['part'])}, {r['hop']}: {r['mode']} ({', '.join(ids(r['moves']))}): "
                f"{r['failure'].removeprefix('not possible here:').strip()}" for r in ruled]
    out.append("")
    used_rem = list(dict.fromkeys(r["remedy"] for r in M["fm"] if r.get("remedy")))
    out += ["## 5. Restore", "", "| # | Kind | Action | Expected result | If different | Approval |", "|---|---|---|---|---|---|"]
    for rid in used_rem:
        rem = M["remedies"].get(rid)
        if not rem:
            continue
        exp = rem.get("expected", "")
        if rem["kind"] in RESTORING:
            exp += " Then re-run T4 and work every branch that still has cases: a restore can leave cases in other states."
        if rem["kind"] == "none exists":
            exp = (("Record the case ids, their state, " if recorded(M) else
                    "Record what the tests showed (no record of this stage holds the case ids or states), ") +
                   "and whether new cases are still failing now. Ending: "
                   "**Broken — cannot restore**; escalate (§7).")
        out.append(f"| {rid} | {rem['kind']} | {rem['action']} | {exp} | {rem.get('if_different', '') or 'Escalate (§7)'} | "
                   f"{'needs approval: change-approval path' if rem.get('needs_approval') == 'yes' else '—'} |".replace("\n", " "))
    donts = [rem for rem in M["remedies"].values() if rem.get("kind") == "do not"]
    if donts:
        out += ["", "**What not to do.**", ""] + [f"- {rem['action']}" for rem in donts]
    out.append("")
    out += ["## 6. Close", "", "| Ending | Close |", "|---|---|",
            "| Nothing is wrong | Close as no impact. If the alert should not have fired, add *threshold or duration wrong*. |",
            "| Expected condition | Link the window or change, then close. Add *alert needs changing* if it should have been suppressed. |",
            f"| Self-healed | Confirm {ph} is back under the threshold, then close. Mark *threshold or duration wrong*. |",
            "| Already known | Link the incident, then close. |",
            f"| Broken — restore | After the §5 action, confirm {ph} is under the threshold and no case of the original set is still in the stage. Any that remain: back to T4. |",
            "| Broken — cannot restore | Escalate (§7). Runbook mark: *worked*. |",
            "| Outside this runbook | Escalate with what you have. Mark *gap*, or *failed* if a step could not be run. |", ""]
    esc = [r for r in active if r["ending"] == "cannot restore"]
    owners = [f"{name(M, c)}: {M['subj'][c].get('owner') or 'owner not stated'}" for c in M["parts"]
              if M["subj"][c].get("part_kind") != "person"]
    out += ["## 7. Escalate / declare", "",
            "**Escalate** (hand over to the owning tier) when you cannot restore with §5; when a test ends in *Broken — "
            "cannot restore* (" + ", ".join(tid.get(r["mode_id"], r["mode_id"]) for r in esc) + "); or when a remedy needs "
            "approval (use the change-approval path).", "",
            "**Escalation targets** are links to the on-call, ownership and change records, to fill in. The owners as the "
            "register records them: " + "; ".join(owners) +
            ". A blank is a gap to fill, not a reason to stop.", "",
            "**Declare an incident** when a second team is needed, customers can see the problem, it is unsolved after a "
            "time box of concentrated work, or the impact threshold in §2 is crossed. Keep working this runbook in parallel.", "",
            "**Hand over:** the expectation (§1); " + ("the stuck case ids by state" if recorded(M) else
                                                      "the counts the measures showed (no record of this stage holds case ids)") +
            "; whether new cases are still affected now; "
            "which tests ran and what they showed; what was done; when the count started rising.", ""]
    out += ["## 8. Outside this runbook", "",
            "For the cases no test explained: escalate them with what you have (§7), and record *gap* (not covered) or "
            "*failed* (a step could not be run). Then go on to the next branch that still has cases: an unexplained "
            "branch does not end the walk for the others.", ""]
    out += ["## 9. Links", "", "Operator links to fill in, one per measure the tests read:", ""]
    out += [f"- {mtext(M, h)}: {'exists' if M['measures'].get(h, {}).get('exists') == 'yes' else 'proposed'}" for h in used]
    out += ["", "## 10. About this runbook", "", "- **Owner:** not stated.",
            "- **Last validated:** never. It has not been rehearsed cold.",
            "- **To change it:** change the register (`lifecycle.csv`, `failure-modes.csv`, `remedies.csv`) and generate "
            "it again. Never edit this file.", "",
            "| Test | Failure mode | Lifecycle rows | Part | Source |", "|---|---|---|---|---|"]
    for r in M["fm"]:
        if r["mode_id"] in tid:
            out.append(f"| {tid[r['mode_id']]} | {r['mode_id']} {r['hop']}: {r['mode']} | {', '.join(ids(r['moves']))} | "
                       f"{name(M, r['part'])} | {r.get('source', '')} |")
    return "\n".join(out) + "\n"


WRITERS = {"STRUCTURE.md": structure, "MEASURES.md": measures, "ALERT.md": alert, "RUNBOOK.md": runbook}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("register")
    ap.add_argument("flow")
    ap.add_argument("stage")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    M = build(load(a.register), a.flow, a.stage)
    err, warn = check(M)
    for w in warn:
        print("warning:", w)
    for e in err:
        print("ERROR:", e)
    print(f"{len(err)} errors, {len(warn)} warnings")
    if a.out:
        out = pathlib.Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for fname in ("STRUCTURE.md", "MEASURES.md") + (() if err else ("ALERT.md", "RUNBOOK.md")):
            (out / fname).write_text(WRITERS[fname](M), encoding="utf-8")
            print("wrote", out / fname)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
