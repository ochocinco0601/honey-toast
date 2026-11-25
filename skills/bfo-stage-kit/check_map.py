"""The map's own inspection: whether a flow's map is fit to hand on, by rules that hold whatever the map says.

    python check_map.py REGISTER FLOW [--all]

It prints how many rules pass and each rule that fails; --all lists every rule.

Run when mapping ends, before the person picks how far each stage goes. It reports and never blocks. It does not
judge whether the map is right about the system: a reviewer reading the sources does that. It also runs the done
check's conditions that are mapping's (run_status.mapping_owed: the view questions, the register check the drawing
runs, the drawings, the code cited),
says in its first line when any is still open, and lists each on stderr for the session to put right (stdout is
what the person reads)."""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map_record as mr  # noqa: E402
import register_layout as layout  # noqa: E402
import go  # noqa: E402
import view_questions as vq  # noqa: E402

RULES = [
    ("stages-connect", "Each stage leads into the next"),
    ("reachable", "Every state the case can be in has a path from where the case starts"),
    ("grounded", "Every step is tied to a move of the case"),
    ("cited", "Every step cites a source"),
    ("parts", "Every part named on a step is in the parts list"),
    ("impact", "Every step has a Business Impact, or a reason why not"),
    ("case", "Where one case starts is stated, with the identifier that follows it"),
    ("ids", "Every name in what mapping wrote is used once"),
    ("kept", "Every row of a finished flow is as it was when this flow began"),
    ("agent-decisions", "Every AI agent's tools, replies and chained actions are classed as its decisions or not"),
]
NOT_YET = ["who depends on the flow, recorded as connections", "open questions, each naming who could answer it",
           "how each row was established, from a source or inferred"]


THING = {"flows": "the flow", "stages": "the stage", "steps": "the process step", "subjects": "the part",
         "lifecycle": "the move", "expectations": "the expectation", "failure-modes": "the failure",
         "remedies": "the remedy", "measures": "the measure", "participation": "a part's work on the step",
         "step-impact": "the Business Impact of", "case-attributes": "the case attribute",
         "agent-system": "the agent's part", "measure-gaps": "the measure gap"}
SAID_BY = ("name", "move", "measure", "expectation", "failure", "action", "attribute", "activity", "element")


def said_row(table, row):
    """A row in its own words: its first naming column that holds any, never its id."""
    return next(((row.get(c) or "").strip() for c in SAID_BY if (row.get(c) or "").strip()), "with no name")


def cont(text):
    text = (text or "").strip()
    return text[:1].lower() + text[1:] if text[1:2].islower() else text


def not_a_flow(flow_id, flows):
    """The refusal check_measures.py gives for the same mistake, word for word."""
    return f"{flow_id} is not a flow of this register; its flows: {', '.join(f['flow_id'] for f in flows)}"


def inspect(reg, flow_id):
    """[{rule, title, passed, items, notes}] in RULES order: items name what fails, notes what is allowed because the
    record says why, both in the map's own words."""
    R = mr.load(reg)
    flow = next((f for f in R["flows"] if f["flow_id"] == flow_id), None)
    if flow is None:
        raise ValueError(not_a_flow(flow_id, R["flows"]))
    stages = sorted((s for s in R["stages"] if s["flow"] == flow_id), key=layout.stage_order)
    sids = {s["stage"] for s in stages}
    steps = [s for s in R["steps"] if s["stage"] in sids]
    moves = {m["move_id"]: m for m in R["lifecycle"] if m.get("flow", flow_id) in (flow_id, "")}
    step_moves = {s["step"]: [mv for mv in re.findall(r"\bL\d+\b", s.get("source") or "") if mv in moves]
                  for s in steps}
    found = {rule: [] for rule, _ in RULES}
    noted = {rule: [] for rule, _ in RULES}

    def stage_moves(stage):
        return [mv for s in steps if s["stage"] == stage["stage"] for mv in step_moves[s["step"]]]

    for a, b in zip(stages, stages[1:]):
        reached = {mr.state(moves[mv]["to_state"]) for mv in stage_moves(a)}
        starts = {mr.state(moves[mv]["from_state"]) for mv in stage_moves(b)}
        if not reached & starts:
            found["stages-connect"].append(f"{a['name']} does not lead into {b['name']}")

    seen, todo = {"(none)"}, ["(none)"]
    while todo:
        here = todo.pop()
        for m in moves.values():
            to = mr.state(m["to_state"])
            if mr.state(m["from_state"]) == here and to not in seen:
                seen.add(to)
                todo.append(to)
    cut = list(dict.fromkeys(mr.state(m["from_state"]) for m in moves.values() if mr.state(m["from_state"]) not in seen))
    entered = {mr.state(m["to_state"]) for m in moves.values() if mr.state(m["from_state"]) != mr.state(m["to_state"])}
    found["reachable"] = [s for s in cut if s not in entered] or cut  # the states the break starts at, not all after

    impact = {r["step"] for r in R["step-impact"]}
    for s in steps:
        # a step with no move is allowed where the record says why (the kit's own rule); then there is no move to
        # derive its Business Impact from either
        excused = not step_moves[s["step"]] and vq.moves_excuse(s, R["measure-gaps"], R["participation"])
        if not step_moves[s["step"]]:
            (noted if excused else found)["grounded"].append(cont(s["name"]))
        if not (s.get("source") or "").strip():
            found["cited"].append(cont(s["name"]))
        if s["step"] not in impact:
            (noted if excused else found)["impact"].append(cont(s["name"]))

    subj, unresolved = {r["subject_id"]: r for r in R["subjects"]}, []
    for mv in dict.fromkeys(mv for s in steps for mv in step_moves[s["step"]]):
        for col in ("carried_by", "needs"):
            mr.parts(moves[mv].get(col) or "", subj, unresolved)
    found["parts"] = list(dict.fromkeys(t.strip() for t in unresolved if t.strip()))

    for col, said in (("case", "what one case is"), ("starts_at", "where one case starts"),
                      ("case_identifier", "the identifier that follows one case")):
        if not (flow.get(col) or "").strip():
            found["case"].append(said)

    # said by name, for the person: the done check names the ids and rows, for the session to fix
    found["ids"] = [f"{THING.get(t, 'a row mapping wrote')} {' and '.join(sorted({said_row(t, r) for r in rs}))}, one "
                    f"name used twice" for t, _, _, rs in go.reused(reg)]
    flows = {f["flow_id"]: f.get("name") or "" for f in R["flows"]}
    found["kept"] = [f"{THING.get(t, 'a row mapping wrote')} {said_row(t, r)} of {flows.get(fid, 'a finished flow')}, "
                     "changed since that flow was finished" for t, r, fid in go.changed_rows(reg)]
    found["agent-decisions"] = agent_items(R, flow_id)
    return [{"rule": rule, "title": title, "passed": not found[rule], "items": found[rule], "notes": noted[rule]}
            for rule, title in RULES]


def agent_items(R, flow_id):
    """What FILL-STEPS Step 7 leaves unclassed, by the rules mapping's done check runs (map_record.class_findings,
    chain_findings), said by name: the agent, its tool, the step."""
    names = {s["subject_id"]: s.get("name") or s["subject_id"] for s in R["subjects"]}
    steps = {s["step"]: cont(s["name"]) for s in R["steps"]}
    out, fix = [], "mark it yes or no, with the reason and the line it rests on"
    for kind, p, *more in mr.class_findings(R, flow_id):
        agent, at = names.get(p["subject_id"], p["subject_id"]), steps.get(p["step"], f"step {p['step']}")
        tool = f"tool {p['operation']}" if (p.get("operation") or "").strip() else "work"
        if kind == "reply":
            out.append(f"{agent}'s reply at {at} is not marked as the agent's decision or not: {fix}")
        elif kind == "tool":
            out.append(f"{agent}'s {tool} at {at} is not marked as the agent's decision or not: {fix}")
        else:
            op, by = more
            out.append(f"{agent}'s {'tool ' + op if op else 'work at ' + at} is marked a decision at "
                       f"{' and '.join(steps.get(s, s) for s in by['yes'])} and not at "
                       f"{' and '.join(steps.get(s, s) for s in by['no'])}: mark it one way on every row")
    mine = {p["subject_id"] for p in mr.agent_rows(R, flow_id)}
    for kind, a, v in mr.chain_findings(R):
        if a.get("agent") not in mine:
            continue
        agent, what = names.get(a.get("agent"), a.get("agent")), said_row("agent-system", a)
        if kind == "not an action":
            out.append(f"{agent}'s {a.get('element') or 'row'} “{what}” is marked as a decision, and only an action "
                       "of the agent's chain is: leave it blank")
        else:
            out.append(f"{agent}'s action “{what}” is marked “{v}”, neither yes nor no: {fix}")
    return out


def open_items(reg, flow_id):
    """[(what, how many, reason)]: what the done check (run_status.py) would still fail on that is mapping's, by its
    own predicates (run_status.mapping_owed). Loaded here, never by inspect(), which reads only the record."""
    import run_status
    return run_status.mapping_owed(reg, flow_id)


def mapping_owed(reg, flow_id):
    """The done check's reasons, in its words for the session, that mapping still owes."""
    return [reason for _, _, reason in open_items(reg, flow_id)]


OPEN_SAID = {"questions": ("question about its parts, stages, process steps or flow left unanswered",
                           "questions about its parts, stages, process steps or flow left unanswered"),
             "register": ("row the drawing refuses", "rows the drawing refuses"),
             "drawings": ("drawing that came out empty", "drawings that came out empty"),
             "code": ("code it cites that was not opened", "code it cites that was not opened")}


def not_finished(items):
    """The sentence the person reads when mapping's part of the done check is still open, or ""."""
    if not items:
        return ""
    parts = [f"{n} {OPEN_SAID[w][n != 1]}" if w != "code" else OPEN_SAID[w][0] for w, n, _ in items]
    listed = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return f" Mapping is not finished: {listed}; these are put right before the flow is handed on."


def said(results, items=()):
    """The inspection as the person reads it at the map stop. `items`, mapping's part of the done check still open
    (open_items), goes in the first line: ten rules passing is not mapping done."""
    failed = sum(not r["passed"] for r in results)
    lines = [f"**Mapping inspection.** {len(results)} rules checked: {len(results) - failed} pass, {failed} "
             f"fail{'s' if failed == 1 else ''}. It checks the shape of what mapping recorded, not whether it is right "
             "about the system." + not_finished(items)]
    for r in results:
        text = "passes" if r["passed"] else f"fails on {'; '.join(r['items'])}"
        if r["notes"]:
            text += ((", with a note on " if r["passed"] else "; allowed, with a note, on ") + "; ".join(r["notes"])
                     + " (no move in the code, and the record says why)")
        if r["rule"] == "impact" and r["items"]:  # Step 10 writes rows only where a failure hurts the case
            text += ". The record has no place yet for a reason, so a step where nothing is at stake is listed too: " \
                    "check each"
        lines.append(f"- {r['title']}: {text}.")
    lines.append("- Not checked yet, because the record has no place for it: " + "; ".join(NOT_YET) + ".")
    return "\n".join(lines)


BEFORE_READING = ("parts", "agent-decisions")  # rules the readers and the lead's rows after them answer


def counted(reg, flow_id, items=(), before_reading=False):
    """The inspection as the stop says it: the count of rules that pass, each failing rule with what fails, and the
    line on files that could not be read. The rules that pass are only counted; `report` lists them all. At the pick
    made before any service is read in depth (`before_reading`), the rules the reading answers are left out."""
    results = [r for r in inspect(reg, flow_id) if not (before_reading and r["rule"] in BEFORE_READING)]
    bad = [r for r in results if not r["passed"]]
    lines = [f"**Mapping inspection.** {len(results) - len(bad)} of {len(results)} rules pass. It checks that what "
             "mapping recorded is complete and hangs together, not whether it is right about the system."
             + not_finished(items)]
    for r in bad:
        lines += [f"- {r['title']}: fails on these:"] + [f"  - {x}" for x in r["items"]]
    return "\n".join(x for x in lines + [not_read_line(reg), mr.unread_line(reg)] if x)


def not_read_line(reg):
    """One line counting the parts whose inside the run did not read (measure-gaps.csv, kind `not read`): no stage
    taken past mapped only reaches them. "" when there are none."""
    import csv
    p = pathlib.Path(reg) / "measure-gaps.csv"
    if not p.is_file():
        return ""
    with p.open(encoding="utf-8-sig", newline="") as f:
        parts = {(r.get("element") or "").strip() for r in csv.DictReader(f)
                 if (r.get("kind") or "").strip() == "not read" and (r.get("question") or "").startswith("part:")}
    parts.discard("")
    if not parts:
        return ""
    n = len(parts)
    return (f"{n} part{'' if n == 1 else 's'} not read in depth in this run: no call the code reader found reaches "
            f"{'it' if n == 1 else 'them'} from a stage taken further, so what "
            f"{'it does inside' if n == 1 else 'they do inside'} is not on the map.")


def report(reg, flow_id, items=None):
    """The inspection as the person reads it at the map stop, with mapping's part of the done check still open in its
    first line, and, when any file of the code could not be read, the line that says so."""
    items = open_items(reg, flow_id) if items is None else items
    return "\n".join(x for x in (said(inspect(reg, flow_id), items), not_read_line(reg), mr.unread_line(reg),
                                 mr.unread_named(reg)) if x)


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    every = "--all" in argv
    argv = [a for a in argv if a != "--all"]
    if len(argv) != 2:
        print(__doc__.splitlines()[2].strip())
        return 2
    flows = mr.load(argv[0])["flows"]
    if argv[1] not in {f["flow_id"] for f in flows}:
        print(not_a_flow(argv[1], flows))
        return 2
    items = open_items(argv[0], argv[1])
    # stdout is what the person reads; stderr, for the session: what the done check would say NOT DONE on, with the
    # ids, to put right before phase 3 is set done
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    if items:
        print("Done check, mapping's part: NOT DONE. Put each right and run this again before setting phase 3 done:\n"
              + "\n".join(f"- {reason}" for _, _, reason in items), file=sys.stderr)
    else:
        print("Done check, mapping's part: passes (view questions, the register check the drawing runs, drawings, "
              "cited code read).", file=sys.stderr)
    print(report(argv[0], argv[1], items) if every else counted(argv[0], argv[1], items))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
