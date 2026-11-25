"""Selective checking for a fast map: only the map rows a proposed measure, alert or failure mode rests on are checked,
each by one judge that wrote none of the map, before the measures review; every other row stays labelled unchecked.
How strongly a row is checked follows what a wrong row would cost where it is used: a row nothing downstream uses costs nothing if wrong at this point, and is never checked in this run.

Usage: python selective.py select <register>   writes fast/check-rows.csv: the unit rows to check, and why
       python selective.py states <register>   prints each measure's state: checked, flagged or not checked
       python selective.py review <register>   exit 0 when the measures review may be shown, 2 and why when not
       python selective.py launch <register> [--again]   writes the checker of every selected row, every unit packed
                                                into launchers that fill the session, and prints them; run it again on
                                                each launcher's reply: a launcher that died leaves its unlaunched
                                                checkers to be printed again

A row is selected when a proposed measure (measures.csv), an alert on a measure (alerts.csv, by handle) or a failure
mode (failure-modes.csv: its part and its measures) names it: a part by its subject_id, resolved to the reading unit's
element of the same name; an operation by the operation a measure names; a process step's participation by its step
and part; a call by the operation it calls. The judges are judges.py's, one per row and one round in a fast map
(judges.settings), every unit's packed together (selective.py launch, judges.emit_selected); judges.scope takes only
these rows.
Python standard library only.
"""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

FILE = "fast/check-rows.csv"
COLS = ["unit", "table", "row_id", "why"]
CHECKED, FLAGGED, NOT_CHECKED, WAITING = "checked", "flagged", "not checked", "waiting for its checker"


def _rows(p):
    p = pathlib.Path(p)
    if not p.is_file():
        return []
    with p.open(newline="", encoding="utf-8-sig") as f:
        return [{k: (v or "").strip() for k, v in r.items() if k is not None} for r in csv.DictReader(f)]


def _split(v):
    return [x.strip() for x in (v or "").replace(";", ",").split(",") if x.strip()]


KEYS = ("subjects", "steps", "case_steps", "operations", "spans")


def _spans(text):
    import fast_map
    return [(f.replace(chr(92), "/"), a, b) for f, a, b in fast_map.spans(text or "")]


def references(reg):
    """What the proposed measures, alerts and failure modes name: root subject ids, steps, operations, the code
    spans their citations rest on, and the steps whose every part a measure of the case rests on; and the same per
    measure (by_measure)."""
    reg = pathlib.Path(reg)
    root = _root(reg)
    cases = {sid for sid, r in root.items() if (r.get("part_kind") or "") == "case"}
    of_stage = {}
    for r in _rows(reg / "steps.csv"):
        of_stage.setdefault(r.get("stage", ""), set()).add(r.get("step", ""))
    measures = {r.get("handle", ""): r for r in _rows(reg / "measures.csv") if r.get("handle")}
    by_measure = {}
    for h, r in measures.items():
        subj, steps = set(_split(r.get("subject_id"))), set(_split(r.get("step")))
        case_steps = (steps or of_stage.get(r.get("stage", ""), set())) if subj & cases else set()
        by_measure[h] = {"subjects": subj, "steps": steps, "case_steps": case_steps,
                         "operations": {r["operation"]} if r.get("operation") else set(),
                         "spans": _spans(r.get("source_ref"))}
    refs = {k: [] if k == "spans" else set() for k in KEYS}
    for mine in by_measure.values():
        for k in KEYS:
            if k == "spans":
                refs[k] += mine[k]
            else:
                refs[k] |= mine[k]
    for fm in _rows(reg / "failure-modes.csv"):
        refs["subjects"] |= set(_split(fm.get("part")))
        refs["spans"] += _spans(fm.get("source"))
    refs["by_measure"] = by_measure
    return refs


def _root(reg):
    """{root subject_id: its row} of the merged map."""
    return {r["subject_id"]: r for r in _rows(pathlib.Path(reg) / "subjects.csv") if r.get("subject_id")}


def _units(reg):
    return sorted(p for p in (pathlib.Path(reg) / "units").glob("*") if p.is_dir())


def _match(reg, refs):
    """[(unit, table, row_id, why, frozenset of measure handles it serves)]: each unit row the references name."""
    root = _root(reg)
    names = {}  # element name -> root ids naming it
    rel_ops = {}  # an interaction's operation -> root ids
    for sid, r in root.items():
        if (r.get("kind") or "element") == "element" and r.get("name"):
            names.setdefault(r["name"].lower(), set()).add(sid)
        if r.get("operation"):
            rel_ops.setdefault(r["operation"], set()).add(sid)
    out = []
    for u in _units(reg):
        local = {}  # unit-local subject id -> root ids of the same name
        for r in _rows(u / "subjects.csv"):
            local[r.get("subject_id", "")] = names.get((r.get("name") or "").lower(), set())
            hit = local[r.get("subject_id", "")] & refs["subjects"]
            if hit:
                out.append((u.name, "subjects", r.get("row_id", ""), "the part " + ", ".join(sorted(hit))))
        for r in _rows(u / "operations.csv"):
            if r.get("operation") in refs["operations"]:
                out.append((u.name, "operations", r.get("row_id", ""), "the operation " + r["operation"]))
        for r in _rows(u / "participation.csv"):
            parts = local.get(r.get("subject_id", ""), set())
            if r.get("step") in refs["steps"] and parts & refs["subjects"]:
                out.append((u.name, "participation", r.get("row_id", ""), f"step {r['step']} by "
                            + ", ".join(sorted(parts & refs["subjects"]))))
        for r in _rows(u / "calls.csv"):
            op = r.get("operation", "")
            if op in refs["operations"] or rel_ops.get(op, set()) & refs["subjects"]:
                out.append((u.name, "calls", r.get("row_id", ""), "the call " + op))
        for r in _rows(u / "participation.csv"):
            if r.get("step") in refs.get("case_steps", set()):
                out.append((u.name, "participation", r.get("row_id", ""),
                            f"step {r['step']}, which a measure of the case rests on"))
        want = refs.get("spans") or []
        for table in ("subjects", "operations", "calls", "participation") if want else ():
            for r in _rows(u / f"{table}.csv"):
                if any(f == g and a <= d and c <= b for f, a, b in _spans(" ".join(r.values()))
                       for g, c, d in want):
                    out.append((u.name, table, r.get("row_id", ""), "cited at the lines a proposal rests on"))
    return out


def select(reg):
    """[{unit, table, row_id, why}]: the unit rows to check, each once."""
    seen, out = set(), []
    for unit, table, rid, why in _match(reg, references(reg)):
        if rid and (unit, table, rid) not in seen:
            seen.add((unit, table, rid))
            out.append({"unit": unit, "table": table, "row_id": rid, "why": why})
    return out


def write_selection(reg):
    p = pathlib.Path(reg) / FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    got = select(reg)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(got)
    return got


def selected(reg):
    """{unit: {(table, row_id)}} from fast/check-rows.csv, or None when no selection is written."""
    p = pathlib.Path(reg) / FILE
    if not p.is_file():
        return None
    out = {}
    for r in _rows(p):
        out.setdefault(r["unit"], set()).add((r["table"], r["row_id"]))
    return out


def verdicts(reg):
    """{(unit, table, row_id): verdict} of the selected rows judged at their current content (round 1, judge 1)."""
    import judges
    sel = selected(reg) or {}
    out = {}
    for unit, keys in sel.items():
        for row in judges.rows(reg, unit)[0]:
            if (row["table"], row["key"]) not in keys:
                continue
            got = judges.read_verdict(judges.verdict_path(reg, row, 1, 1))
            if got:
                out[(unit, row["table"], row["key"])] = got["verdict"]
    return out


def measure_states(reg):
    """{measure handle: checked | flagged | not checked | waiting for its checker}: flagged when any row it rests on
    was judged other than "says", checked when every such row says, waiting while one is unjudged, not checked when
    none of the map's rows is matched for it."""
    refs = references(reg)
    got = verdicts(reg)
    out = {}
    for h, mine in refs["by_measure"].items():
        rows = {(u, t, r) for u, t, r, _ in _match(reg, mine) if r}
        if not rows:
            out[h] = NOT_CHECKED
        elif any(got.get(k) and got[k] != "says" for k in rows):
            out[h] = FLAGGED
        elif all(got.get(k) == "says" for k in rows):
            out[h] = CHECKED
        else:
            out[h] = WAITING
    return out


SIGNAL_FOUND = "signal found in code"  # the code scanner found a log, metric or span emitted at the cited line
SIGNAL_CITED = "signal cited, not confirmed by the code scanner"  # the cited lines exist; no emission fact there
SIGNAL_NOT_FOUND = "signal not found in code"  # said to exist, with no citation that resolves to code
SIGNAL_PROPOSED = "not emitted yet (proposed)"  # exists: no
CLAIM_SUPPORTED = "cites code"
CLAIM_UNSUPPORTED = "unsupported (no code cited)"


def _ws(reg, ws=None):
    import fast_map
    return fast_map.workspace(reg, ws)


def _resolves(ws, text):
    """[(file, first, last)] of the citations in `text` whose file is found once in the workspace and whose lines it
    has."""
    import fast_map
    out = []
    for f, lo, hi in fast_map.spans(text or ""):
        p = fast_map._resolve(ws, f)
        if p is not None and 1 <= lo <= hi <= len(fast_map._text(p)):
            out.append((f, lo, hi))
    return out


def signal_states(reg, ws=None):
    """{measure handle: one of SIGNAL_*}: whether what an alert on the measure would read exists today, by script. A
    measure said to exist (`exists` yes) is found when the code scanner recorded an emission site (a log, metric or
    span) inside a line its `source_ref` cites; cited when the cited lines exist but the scanner has no emission there
    (its rules may not cover the call); not found when no citation resolves to code."""
    import fast_map
    reg = pathlib.Path(reg)
    ws = _ws(reg, ws)
    emitted = [(f["file"], int(f.get("line") or 0)) for f in fast_map.facts(reg) if f.get("kind") == "emission_site"]
    out = {}
    for m in _rows(reg / "measures.csv"):
        h = m.get("handle")
        if not h:
            continue
        if (m.get("exists") or "").strip().lower() != "yes":
            out[h] = SIGNAL_PROPOSED
            continue
        cites = _resolves(ws, m.get("source_ref"))
        if not cites:
            out[h] = SIGNAL_NOT_FOUND
        elif any((f.endswith(c) or c.endswith(f)) and lo <= n <= hi for c, lo, hi in cites for f, n in emitted):
            out[h] = SIGNAL_FOUND
        else:
            out[h] = SIGNAL_CITED
    return out


def failure_claims(reg, ws=None):
    """{failure mode id: CLAIM_*}: a failure mode's recovery and expected behaviour is what a runbook tells a responder,
    so it must cite the code that does it (`source`), resolving to real lines; else it is unsupported."""
    reg = pathlib.Path(reg)
    ws = _ws(reg, ws)
    return {fm["mode_id"]: (CLAIM_SUPPORTED if _resolves(ws, fm.get("source")) else CLAIM_UNSUPPORTED)
            for fm in _rows(reg / "failure-modes.csv") if fm.get("mode_id")}


# each signal state as the person reads it in a review
SIGNAL_SAID = {SIGNAL_FOUND: "found in the code", SIGNAL_CITED: "cited in the code but not confirmed there",
               SIGNAL_NOT_FOUND: "not found in the code", SIGNAL_PROPOSED: "proposed, not produced yet"}


def said(reg):
    """The review's lines on checking, as labelled one-line fields in plain words: how many measures rest on map lines
    a checker confirmed, flagged or that nothing on the map matched, each flagged measure by name, where each measure's
    number was found in the code, and the measures an alert on which would never fire as drafted."""
    names = {r.get("handle", ""): (r.get("measure") or r.get("handle", "")) for r in _rows(pathlib.Path(reg) /
                                                                                          "measures.csv")}
    states = measure_states(reg)
    n = {k: sum(1 for v in states.values() if v == k) for k in (CHECKED, FLAGGED, WAITING, NOT_CHECKED)}
    sel = selected(reg) or {}
    rows = sum(len(v) for v in sel.values())
    lines = [f"**Check of the map against the code:** the {rows} lines of the map these measures rest on, each read "
             "by a checker that wrote none of the map; the map's other lines are not checked in this run",
             f"**What it found:** of {len(states)} measures, {n[CHECKED]} checked, {n[FLAGGED]} flagged, {n[WAITING]} "
             f"waiting for a checker, {n[NOT_CHECKED]} not checked (no line of the map matched)"]
    flagged = [names.get(h, h) for h, v in sorted(states.items()) if v == FLAGGED]
    if flagged:
        lines.append("**Flagged, a line each rests on judged wrong or unclear:** " + "; ".join(flagged))
    signals = signal_states(reg)
    if signals:
        s = {k: [names.get(h, h) for h, v in sorted(signals.items()) if v == k]
             for k in (SIGNAL_FOUND, SIGNAL_CITED, SIGNAL_NOT_FOUND, SIGNAL_PROPOSED)}
        lines.append("**Where each number is produced, looked up by script:** "
                     + ", ".join(f"{len(s[k])} {SIGNAL_SAID[k]}" for k in (SIGNAL_FOUND, SIGNAL_CITED, SIGNAL_NOT_FOUND,
                                                                          SIGNAL_PROPOSED)))
        if s[SIGNAL_NOT_FOUND]:
            lines.append("**An alert on these would never fire as drafted (not found in the code):** "
                         + "; ".join(s[SIGNAL_NOT_FOUND]))
    claims = failure_claims(reg)
    bad = sorted(k for k, v in claims.items() if v == CLAIM_UNSUPPORTED)
    if claims:
        lines.append(f"**What the runbooks will say the code does on failure:** {len(claims) - len(bad)} of "
                     f"{len(claims)} ways it can fail cite code" + (f"; none cited for {', '.join(bad)}" if bad else ""))
    return "\n\n".join(lines)


def review_problem(reg):
    """"" when every selected row has its checker's verdict, so the measures review may be shown; else why not."""
    sel = selected(reg)
    if sel is None:
        return "the rows the measures rest on are not selected yet: run selective.py select, then their judges"
    want = sum(len(v) for v in sel.values())
    have = len(verdicts(reg))
    if have < want:
        return (f"{want - have} of the {want} map rows the proposed measures rest on have no checker's verdict yet: "
                "launch their checkers (selective.py launch, every launcher it prints at once) and wait")
    return ""


def main(argv):
    """_main, then the timing record rewritten for a register mapped fast (timings.refresh_if_fast)."""
    try:
        return _main(argv)
    finally:
        import timings
        timings.refresh_if_fast(argv, "selective.py")


def _main(argv):
    again = "--again" in argv
    argv = [a for a in argv if a != "--again"]
    if len(argv) != 2 or argv[0] not in ("select", "states", "review", "launch"):
        print(__doc__)
        return 2
    reg = pathlib.Path(argv[1])
    if argv[0] == "launch":
        import judges
        import run_lock
        run_lock.guard(reg)
        units = sorted(selected(reg) or {})
        for u in units or [""]:  # the same order check a judge emit makes (guard.py)
            if judges._guarded(reg, u, 1):
                return 2
        import guard
        print(guard.SILENT)  # first, before the lines to launch: between stops nothing goes to the person
        print("\n".join(judges.emit_selected(reg, units, again=again)))
        return 0
    if argv[0] == "select":
        import run_lock  # the register is written by one run at a time
        run_lock.guard(reg)
        got = write_selection(reg)
        units = sorted({r["unit"] for r in got})
        print(f"{len(got)} map row(s) selected for checking, in {len(units)} unit(s): {', '.join(units) or 'none'}")
        return 0
    if argv[0] == "states":
        for h, st in sorted(measure_states(reg).items()):
            print(f"{h}: {st}")
        return 0
    why = review_problem(reg)
    if why:
        print(f"HELD: {why}")
        import guard
        print(guard.SILENT)
        return 2
    print("READY: every selected row has its checker's verdict")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
