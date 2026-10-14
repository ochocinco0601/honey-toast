"""Say whether a run of the kit is done: list every output the register folder owes and whether it exists.

Usage: python run_status.py <register folder> [stage id ...]

A stage is owed its six files (STRUCTURE.md, MEASURES.md, ALERT.md, RUNBOOK.md, ALERT.html, RUNBOOK.html in
stage-<id>/) when it has a stage-<id> folder, when RUN.md in the register folder names stage-<id>, or when it is
given on the command line. The register is owed views.html and how-this-map-was-made.html. An empty file counts as
missing. The run is also NOT DONE while a view question that is required, or answer or gap, is empty for an element
the run owes (the flows with an owed stage, the owed stages and their steps, every part, each alert drafted in an owed
stage), or is gapped `not read` on a first run (view_questions.py holds the questions and their predicates, which the
cards print from). Count-only questions, owner and responder among them, never change DONE. Then a line DONE or NOT
DONE, naming the count missing and each view question not answered; the exit status is 0 only when done.

After that line, a Fullness block counts how full the register is: steps and measures per stage, the coverage
receipt and its gaps by kind (a `not read` gap is one the run did not look at; the others it looked at), operations recorded, parts with inside content, steps with calls, alerts and their tests, rows still
`proposed:`, and per view question: answered, gapped by kind, empty, with the ids of the empty elements."""
import csv
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
STAGE_FILES = ("STRUCTURE.md", "MEASURES.md", "ALERT.md", "RUNBOOK.md", "ALERT.html", "RUNBOOK.html")
MAP_FILES = ("views.html", "how-this-map-was-made.html")


def stages(reg, named):
    """Every stage the run owes outputs for, in order."""
    found = {p.name[len("stage-"):] for p in reg.glob("stage-*") if p.is_dir()}
    run = reg / "RUN.md"
    if run.exists():
        # An id starts with a capital and holds a digit (ST2), so prose such as "stage-by-stage" is not one.
        # Where stages.csv has rows, only its ids count.
        in_run = set(re.findall(r"\bstage-([A-Z][A-Za-z_]*[0-9][A-Za-z0-9_]*)\b", run.read_text(encoding="utf-8")))
        table = reg / "stages.csv"
        if table.exists():
            with table.open(encoding="utf-8-sig", newline="") as f:
                ids = {r.get("stage", "").strip() for r in csv.DictReader(f)} - {""}
            if ids:
                in_run &= ids
        found |= in_run
    found |= {s[len("stage-"):] if s.startswith("stage-") else s for s in named}
    return sorted(found)


def expected(reg, named):
    return [f"stage-{s}/{f}" for s in stages(reg, named) for f in STAGE_FILES] + list(MAP_FILES)


def present(reg, rel):
    p = reg / rel
    return p.is_file() and p.stat().st_size > 0


# ---------------------------------------------------------------- how full the register is

def table(reg, name):
    p = reg / f"{name}.csv"
    if not p.is_file():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ids(v):
    return [x.strip() for x in re.split(r"[;,]", v or "") if x.strip()]


def filled(r, col):
    return bool((r.get(col) or "").strip())


def share(n, total):
    return f"{round(100 * n / total)}%" if total else "0%"


def receipt_lines(reg):
    """The coverage receipt of each flow, flow-wide, counted as `flow_outputs.py --check` counts it: elements, those
    a candidate in measures.csv covers, and those not covered that a row of measure-gaps.csv accounts for."""
    flows = [f.get("flow_id", "").strip() for f in table(reg, "flows")]
    with_stages = {s.get("flow", "").strip() for s in table(reg, "stages")}
    flows = [f for f in flows if f and f in with_stages]
    if not flows:
        return ["receipt: none (no flow with a stage row)"]
    try:
        sys.path.insert(0, str(HERE))
        import flow_outputs as fo
        R = fo.load(reg)
    except Exception as e:  # a register the generator cannot read still gets its other counts
        return [f"receipt: not counted ({type(e).__name__}: {e})"]
    out = []
    for flow in flows:
        try:
            rec = fo.receipt(R, flow)
            _, _, gapped = fo.gap_rows(R, rec)
        except Exception as e:
            out.append(f"receipt for {flow}: not counted ({type(e).__name__}: {e})")
            continue
        n = len(rec)
        cov = sum(r["covered"] for r in rec)
        gap = sum((r["element"], r["question"]) in gapped and not r["covered"] for r in rec)
        out.append(f"receipt for {flow} (flow-wide): {n} elements, {cov} covered ({share(cov, n)}), "
                   f"{gap} gapped ({share(gap, n)}), {n - cov - gap} neither")
        kinds = [gapped[(r["element"], r["question"])] for r in rec
                 if (r["element"], r["question"]) in gapped and not r["covered"]]
        out.append(f"gapped for {flow}, by kind: " + ", ".join(f"{kinds.count(k)} {k}" for k in fo.GAP_KINDS) +
                   f"; not read in this run: {share(kinds.count('not read'), n)} of its elements")
    return out


def runbook_lines(reg):
    """Each generated stage-*/RUNBOOK.md: its alerts and the distinct tests each alert's entry lists."""
    out = []
    for rb in sorted(reg.glob("stage-*/RUNBOOK.md")):
        text = rb.read_text(encoding="utf-8", errors="replace")
        per = []
        for block in re.split(r"^## Alert ", text, flags=re.M)[1:]:
            handle = block.split(":", 1)[0].strip()
            entry = re.split(r"^## ", block, flags=re.M)[0]
            per.append(f"{handle} {len(set(re.findall(r'^[0-9]+[.] [*][*](T[0-9]+)[*][*]', entry, re.M)))}")
        rel = rb.relative_to(reg).as_posix()
        out.append(f"{rel}: {len(per)} alerts" + (f"; tests per alert: {', '.join(per)}" if per else ""))
    return out or ["runbooks: none"]


def first_run(reg):
    """Whether this is the register's first run: every row of how-made.csv is in its first `pass` (a blank counts as
    the first), or it has none. A later run may leave a question `not read` outside the stage it reads."""
    return all((r.get("pass") or "1").strip() in ("", "1") for r in table(reg, "how-made"))


def view_questions(reg, owed):
    """(Fullness lines, the reasons DONE fails) for the view questions. A register with no steps or subjects has
    none to ask."""
    if not (table(reg, "steps") and table(reg, "subjects")):
        return ["view questions: none (no steps or subjects)"], []
    sys.path.insert(0, str(HERE))
    import view_questions as vq
    try:
        C = vq.count(reg, owed)
    except Exception as e:  # a register the generators cannot read cannot show its answers either
        return ([f"view questions: not counted ({type(e).__name__}: {e})"],
                [f"view questions not counted ({type(e).__name__})"])
    first = first_run(reg)
    why = []
    for q in vq.QUESTIONS:
        if vq.CONTRACT[q] == vq.COUNT:
            continue
        if C[q]["empty"]:
            why.append(f"{q} {len(C[q]['empty'])} empty")
        unread = C[q]["gapped"].get("not read", [])
        if first and unread:
            why.append(f"{q} {len(unread)} gapped not read on a first run")
    head = (f"view questions (answered / gapped / empty), first run: {'yes' if first else 'no'} (how-made.csv); "
            "required and answer-or-gap ones decide DONE, count-only ones never do")
    return [head] + vq.lines(C), why


def fullness(reg, extra=()):
    st_rows = table(reg, "stages")
    steps = table(reg, "steps")
    ms = table(reg, "measures")
    part = table(reg, "participation")
    subj = table(reg, "subjects")
    agent = table(reg, "agent-system")
    lines = ["Fullness (counts; only the view questions' empty and first-run unread ones change DONE)"]

    stage_of = {s.get("step", "").strip(): s.get("stage", "").strip() for s in steps}
    for st in [s.get("stage", "").strip() for s in st_rows if s.get("stage", "").strip()]:
        n_steps = sum(1 for s in steps if s.get("stage", "").strip() == st)
        n_ms = sum(1 for m in ms if m.get("stage", "").strip() == st
                   or any(stage_of.get(x) == st for x in ids(m.get("step"))))
        lines.append(f"stage {st}: {n_steps} steps, {n_ms} measures")
    if not st_rows:
        lines.append("stages: none")
    lines.append(f"measures, all: {len(ms)}")

    lines += receipt_lines(reg)

    lines.append(f"participation rows with an operation: {sum(filled(p, 'operation') for p in part)} of {len(part)}")
    inter = [s for s in subj if s.get("kind", "").strip() == "relationship"]
    lines.append(f"interactions with an operation: {sum(filled(s, 'operation') for s in inter)} of {len(inter)}")
    inside = ({p.get("subject_id", "").strip() for p in part if filled(p, "operation")}
              | {a.get("agent", "").strip() for a in agent if a.get("element", "").strip() == "operation"}) - {""}
    lines.append(f"parts with inside content (an operation on a participation row, or an agent's operation "
                 f"elements): {len(inside)}")
    # A step's card has calls when an interaction names the step in `step_hint` (step_sequence.calls_of).
    hinted = {x for s in inter for x in ids(s.get("step_hint"))}
    step_ids = {s.get("step", "").strip() for s in steps} - {""}
    lines.append(f"steps with calls (named in an interaction's step_hint): {len(hinted & step_ids)} of {len(step_ids)}")

    lines += runbook_lines(reg)

    proposed = total = 0
    for p in sorted(reg.glob("*.csv")):
        with p.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))[1:]
        total += len(rows)
        proposed += sum(any("proposed:" in c for c in r) for r in rows)
    lines.append(f"rows holding proposed: {proposed} of {total} ({share(proposed, total)})")
    return lines + list(extra)


def main(argv):
    if not argv:
        sys.exit(__doc__)
    reg = pathlib.Path(argv[0])
    if not reg.is_dir():
        sys.exit(f"not a folder: {reg}")
    owed = expected(reg, argv[1:])
    width = max(len(r) for r in owed)
    print(f"Register: {reg}")
    missing = 0
    if not stages(reg, argv[1:]):
        print(f"{'stage-<id>/':<{width}}  MISSING (no stage has had Step 11)")
        missing += 1
    for rel in owed:
        ok = present(reg, rel)
        missing += not ok
        print(f"{rel:<{width}}  {'ok' if ok else 'MISSING'}")
    total = len(owed) + (0 if stages(reg, argv[1:]) else 1)
    vq_lines, why = view_questions(reg, stages(reg, argv[1:]))
    said = f"{missing} of {total} expected outputs missing" if missing else f"all {total} expected outputs exist"
    if missing or why:
        print(f"NOT DONE: {said}" + (f"; view questions not answered: {'; '.join(why)}" if why else ""))
    else:
        print(f"DONE: {said}")
    try:
        block = fullness(reg, vq_lines)
    except Exception as e:  # the other counts never change whether the run is done
        block = [f"Fullness: not counted ({type(e).__name__}: {e})"] + vq_lines
    print("\n".join(block))
    return 1 if missing or why else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
