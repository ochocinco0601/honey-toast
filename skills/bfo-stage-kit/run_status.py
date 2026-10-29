"""Say whether a run of the kit is done: list every output the register folder owes and whether it exists.

Usage: python run_status.py <register folder> [stage id ...]

A run whose RUN.md has the section *Plan and go* first owes PLAN.md and a go recorded on it in the person's words.
Until the go is recorded the run is NOT DONE, and any work past gathering and the survey (a walk table with rows, a
stage folder, the map) is named as READ BEFORE THE GO. A RUN.md without that section is from an earlier kit.

A stage is owed its six files (STRUCTURE.md, MEASURES.md, ALERT.md, RUNBOOK.md, ALERT.html, RUNBOOK.html in
stage-<id>/) when it has a stage-<id> folder, when RUN.md in the register folder names stage-<id>, or when it is
given on the command line. A plan-first run is held to the scope its go set: RUN.md's line `- **Scope:** flow <id>;
stages <id>, <id>`, then the person's words. Only the stages in that scope (and any given on the command line) owe the
six; every other stage owes only STAGE.html, the page the map draws for every stage, and is listed as not yet covered,
never counted missing. A go with no scope recorded, or a scope naming a stage the register does not have, is NOT
DONE. The register is owed views.html and how-this-map-was-made.html. An empty file counts as
missing. A stage output is STALE, and the run NOT DONE, when it carries no stamp of the register it was generated from
(flow_outputs.py writes one into each) or when a table it was generated from has changed since: its line names the
tables and the command that regenerates it. The run is also NOT DONE while a view question that is required, or answer or gap, is empty for an element
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
sys.path.insert(0, str(HERE))
import reading_check  # noqa: E402
import reread  # noqa: E402
import go as go_record  # noqa: E402
import judges  # noqa: E402
import merge  # noqa: E402
import settings  # noqa: E402
import tables  # noqa: E402
import register_layout as layout  # noqa: E402


COUNT_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
MEASURED_JUDGES = 3  # the count the checks are built for


def judges_per_row(reg):
    return settings.number(settings.load(reg), "judges")


def judges_note(reg):
    """What the DONE or NOT DONE line of a split run says beside its verdict when fewer judges than the checks are built for."""
    n = judges_per_row(reg)
    if n >= MEASURED_JUDGES:
        return ""
    return (f"{COUNT_WORDS.get(n, n)} judge{'s' if n != 1 else ''} per row (run-settings.json): the checks that catch "
            f"wrong rows are built for three judges per row")


def split_checks(reg):
    """A split run's checks in place of the sample re-read: every unit's rows judged by the number of judges
    run-settings.json sets and flagged rows judged again (judges.py, from the transcripts), and the map what a merge of
    the unit folders gives (merge.py)."""
    units = [r["unit"].strip() for r in tables.dicts(reg / layout.UNITS_CSV) if (r.get("unit") or "").strip()]
    lines, why = [], []
    n = judges_per_row(reg)
    for u in units:
        for r in (judges.check(reg, u), judges.fix_check(reg, u)):
            lines += r.lines()
            if not r.passed and not any(w.startswith("rows not judged by ") for w in why):
                why.append(f"rows not judged by {COUNT_WORDS.get(n, n)} judge{'s' if n != 1 else ''}")
    _, problems = merge.check(reg)
    lines.append("Merge: ok" if not problems else f"Merge: NOT DONE: {'; '.join(problems)}")
    if problems:
        why.append("the map is not the merge of the units: " + "; ".join(problems))
    return lines, why

STAGE_FILES = ("STRUCTURE.md", "MEASURES.md", "ALERT.md", "RUNBOOK.md", "ALERT.html", "RUNBOOK.html")
MAP_FILES = ("views.html", "how-this-map-was-made.html")
STAGE_PAGE = "STAGE.html"  # one_canvas.py draws it for every stage in stages.csv; it carries no stamp


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


DEPTH_FILES = {"none": (), "measure": ("STRUCTURE.md", "MEASURES.md"),
               "alerting": ("STRUCTURE.md", "MEASURES.md", "ALERT.md", "ALERT.html"), "runbooks": STAGE_FILES}


def depth_of(reg):
    """{stage: none | measure | alerting | runbooks}, how far the person chose to take each stage (scope.json `depth`,
    written by go.py --depth), or None for a run whose person made no such choice."""
    got = (go_record.load(reg) or {}).get("depth")
    return dict(got) if isinstance(got, dict) else None


def expected(reg, named, scope=None, depth=None):
    """Every output owed. With `depth`, each stage owes what its depth does: mapped only (none), the page the map draws
    for it; measured, its structure and measures; alerting, those and the alert pages; runbooks, all six. Otherwise
    `scope` None: every stage owes its six files (a run record from an earlier kit, or one whose scope is not
    recorded); else the stages in `scope` and on the command line owe the six, and every other stage only the page the
    map draws for it."""
    if depth is not None:
        every = sorted(set(stages(reg, named)) | {r.get("stage", "").strip() for r in table(reg, "stages")} - {""})
        out = []
        for s in every:
            files = DEPTH_FILES.get(depth.get(s, "none"), ())
            out += [f"stage-{s}/{f}" for f in files] if files else [f"stage-{s}/{STAGE_PAGE}"]
        return with_drawings(reg, out)
    if scope is None:
        return with_drawings(reg, [f"stage-{s}/{f}" for s in stages(reg, named) for f in STAGE_FILES])
    inside = in_scope(scope, named)
    return with_drawings(reg, [f"stage-{s}/{f}" for s in inside for f in STAGE_FILES] +
                         [f"stage-{s}/{STAGE_PAGE}" for s in outside(reg, named, inside)])


def with_drawings(reg, out):
    """`out`, then the map files and every drawing page the map's build writes beside it (one_canvas.drawing_pages:
    each stage's, part's, process step's and flow's page) that `out` does not already name."""
    return out + [f for f in list(MAP_FILES) + drawing_pages(reg) if f not in out]


def drawing_pages(reg):
    """The drawing pages the map's build writes for this register. Nothing for a register the build refuses (its own
    check finds errors): no drawing page is then owed, and views.html is reported MISSING only if no earlier build
    left one. Pages an earlier build left stay on disk, unstamped, and are not checked against the register as it is
    now."""
    sys.path.insert(0, str(HERE))
    import capability_views as cv
    import one_canvas as oc
    R = cv.load(reg)
    if cv.check(R)[0]:
        return []
    return oc.drawing_pages(oc.number_steps(oc.prune(cv.model(R))))


def in_scope(scope, named):
    return sorted(set(scope) | {s[len("stage-"):] if s.startswith("stage-") else s for s in named})


def outside(reg, named, inside):
    """The stages outside the run's scope: every stage the register has, in stages.csv or as a folder, not in it."""
    every = (set(stages(reg, named)) | {r.get("stage", "").strip() for r in table(reg, "stages")}) - {""}
    return sorted(every - set(inside))


DRAWINGS = ("views.html", "flow-*/FLOW.html", "stage-*/STAGE.html", "stage-*/step-*/STEP.html", "part-*/PART.html")
# What each drawing exists to show, by the class its generator gives it: a step's messages (step_sequence), a stage's
# tasks, any-time ones included (stage_flow_views), a flow's stage boxes (flow_page), a part's operations and the steps
# it serves (part_page), a part's operation rows on the map page (part_inside). Frames, pools, lanes, lifelines, heads,
# keys and measure marks are drawn whatever the register holds, so they never count; nor, on a stage, its outer box
# (bp-stagebox), its strip's sequence flows (bp-seq), the neighbouring stages folded (bp-collapsedbox), the
# sub-process boxes that hold the tasks (bp-sub, bp-adhoc) and the event sub-process boxes (bp-esp, the timer's drawn
# from the stage's time limit), which a stage draws whatever its tasks hold.
# Keyed by kind, because a class one drawing gives its content another gives its wiring: `ar` is a step's message, but
# also a part row's connector (drawn on "opbox none" rows too) and a flow drawing's entry arrow. Keys are the page's
# file name, or a figure's prefix on the map page (a flow's value stream there is sfv.flow_drawing, its stages g.stage).
CONTENT = {"STEP.html": {"ar"}, "STAGE.html": {"bp-taskbox"}, "FLOW.html": {"sb"},
           "PART.html": {"opbox", "sv"}, "s:": {"ar"}, "f:": {"stage"}, "p:": {"oprow"}, "g:": set()}
UNDRAWN = {"defs", "marker", "symbol", "clippath", "mask", "pattern"}  # a browser draws nothing inside these by itself
FIGURE = {"data-seq": "s:", "data-case": "", "data-inside": "p:"}  # the map page's figure sections, keyed as its data-k


def figures(text, kind):
    """{figure: marks of content} for a page. "page" counts every drawing on it, by CONTENT[kind] (the page's file
    name). On the map page, each figure section
    (a step's sequence "s:<step>", a stage's card "g:<stage>", a flow's value stream "f:<flow>", a part's operations
    "p:<part>") counts on its own; "map" holds the stages whose boxes the map draws (HTML, from their data-k), "wires"
    the [from, to] id pairs its script draws lines between (#map-wires), and "ids" every id on the page: the map's svg
    is empty until the browser runs it."""
    from html.parser import HTMLParser
    import json

    class Count(HTMLParser):
        svg = undrawn = 0
        open_ = None  # [figure key, depth of its section]
        depth = 0
        map_at = None
        wires = False

        def __init__(self):
            super().__init__()
            self.n = {"page": 0, "map": set(), "wires": [], "ids": set()}

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag in ("section", "div"):
                self.depth += 1
                key = next((pre + a[k] for k, pre in FIGURE.items() if a.get(k)), None)
                if tag == "section" and key and not self.open_:
                    self.open_ = [key, self.depth]
                    self.n.setdefault(key, 0)
                if a.get("id") == "map" and self.map_at is None:
                    self.map_at = self.depth
            if tag == "script" and a.get("id") == "map-wires":
                self.wires = True
            if a.get("id"):
                self.n["ids"].add(a["id"])
            cls = set((a.get("class") or "").split())
            if (self.map_at or 0) > 0 and {"bx", "stage"} <= cls and (a.get("data-k") or "").startswith("g:"):
                self.n["map"].add(a["data-k"][2:])
            if tag == "svg":
                self.svg += 1
            elif tag in UNDRAWN:
                self.undrawn += 1
            elif self.svg and not self.undrawn and "none" not in cls:
                self.n["page"] += bool(cls & CONTENT.get(kind, set()))
                if self.open_:
                    self.n[self.open_[0]] += bool(cls & CONTENT[self.open_[0][:2]])

        def handle_startendtag(self, tag, attrs):
            if tag not in UNDRAWN and tag not in ("svg", "section", "div"):
                self.handle_starttag(tag, attrs)

        def handle_data(self, data):
            if self.wires:
                try:
                    self.n["wires"] += json.loads(data)
                except ValueError:
                    pass

        def handle_endtag(self, tag):
            if tag == "script":
                self.wires = False
            if tag in ("section", "div"):
                if self.open_ and self.open_[1] == self.depth:
                    self.open_ = None
                if self.map_at == self.depth:
                    self.map_at = -1  # closed; one map per page
                self.depth -= 1
            if tag == "svg" and self.svg:
                self.svg -= 1
            elif tag in UNDRAWN and self.undrawn:
                self.undrawn -= 1
    c = Count()
    c.feed(text)
    return c.n


def content_in(text, kind):
    """How many marks of content a page of `kind` (its file name: STEP.html, STAGE.html, FLOW.html, PART.html) holds:
    elements inside an <svg>, outside its definitions, whose class names what that drawing exists to show
    (CONTENT[kind]), "opbox none" (no operation on record) not among them."""
    return figures(text, kind)["page"]


def counted_at_missing(reg):
    """The check's line for each measure that cites its source and says no counted_at, the named place it is counted
    at (flow_outputs.counted_at_failures). A register with no counted_at column is warned by the check, not here."""
    sys.path.insert(0, str(HERE))
    import flow_outputs as fo
    products = fo.vouched_products(fo.read_csv(pathlib.Path(reg) / fo.PRODUCT_NAMES))
    return [e for m in table(reg, "measures") for e in fo.counted_at_failures(m, products)]


def blank_drawings(reg):
    """Every drawing page in the register folder that came out with no content: the map, each flow, stage, step and
    part page, and on the map page each figure on its own: the map ("views.html (the map)") and each step, stage, flow
    and part drawing ("views.html (step 3)"); a stage's section there is its card, not a drawing. A page that is missing is the owed-files check's; this one opens the
    pages that exist. A drawing is held to content only where the register gives it something to show: a flow its
    stages (stages.csv), a stage its steps (steps.csv), a step or part its participation rows, a part's operations on
    the map page its participation rows with an operation, the map its stages: a box for each stage of each flow it
    has, and lines whose two ends are boxes on the page. A step the register records no part
    taking part in (one carried out outside the application) draws an honest empty frame, and is not blank."""
    def ids(name, col, where=lambda r: True):
        return {(r.get(col) or "").strip() for r in table(reg, name) if where(r)} - {""}
    flows, stages_, steps = ids("stages", "flow"), ids("steps", "stage"), ids("participation", "step")
    mapped = ids("flows", "flow_id")  # the map draws the stages of the flows it has; with no flows.csv, every stage
    given = {"FLOW.html": flows, "STAGE.html": stages_, "STEP.html": steps,
             "PART.html": ids("participation", "subject_id")}
    on_map = {"f:": flows, "s:": steps,  # a stage's section on the map page is its card; its drawing is STAGE.html
              "p:": ids("participation", "subject_id", lambda r: (r.get("operation") or "").strip())}
    words = {"f:": "flow", "s:": "step", "p:": "part"}
    blank = []
    for pat in DRAWINGS:
        for p in reg.glob(pat):
            if not p.is_file():
                continue
            rel = p.relative_to(reg).as_posix()
            n = figures(p.read_text(encoding="utf-8", errors="replace"), p.name)
            if p.name != "views.html":
                if p.parent.name.split("-", 1)[1] in given[p.name] and not n["page"]:
                    blank.append(rel)
                continue
            drawn = ids("stages", "stage", lambda r: not mapped or (r.get("flow") or "").strip() in mapped)
            loose = [w for w in n["wires"] if not set(w) <= n["ids"]]
            if drawn and (drawn - n["map"] or not n["wires"] or loose):
                blank.append(f"{rel} (the map)")
            blank += [f"{rel} ({words[k[:2]]} {k[2:]})" for k, v in n.items()
                      if k[:2] in on_map and k[2:] in on_map[k[:2]] and not v]
    return sorted(blank)


def present(reg, rel):
    p = reg / rel
    return p.is_file() and p.stat().st_size > 0


def stale(reg, rel):
    """Why a stage output no longer matches the register, or "" where it does. flow_outputs.py stamps each output with
    the fingerprint of the register tables it read; an output with no stamp, or one whose tables have changed since,
    is stale. The map files carry no stamp and are not compared."""
    if not rel.startswith("stage-") or rel.endswith(("/" + STAGE_PAGE, "/STEP.html")):
        return ""
    sys.path.insert(0, str(HERE))
    import flow_outputs as fo
    stage = rel.split("/", 1)[0][len("stage-"):]
    got = fo.stamp_of((reg / rel).read_text(encoding="utf-8", errors="replace"))
    flow = (got or {}).get("flow") or next((r.get("flow", "").strip() for r in table(reg, "stages")
                                           if r.get("stage", "").strip() == stage), "") or "<flow>"
    if got is None:
        why = "no record of the register it was generated from"
    else:
        changed = fo.changed_since(got.get("tables"), reg)
        if not changed:
            return ""
        why = f"{', '.join(changed)} changed since it was generated"
    return f"{why}: regenerate with {fo.regenerate_command(reg, flow, stage)}"


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


def view_questions(reg, owed, measured=None, alerting=None, runbooks=None):
    """(Fullness lines, the reasons DONE fails) for the view questions. A register with no steps or subjects has
    none to ask. `measured` and `alerting` (view_questions.count) limit the questions only measuring or alerting
    answer to the stages taken that far."""
    if not (table(reg, "steps") and table(reg, "subjects")):
        return ["view questions: none (no steps or subjects)"], []
    sys.path.insert(0, str(HERE))
    import view_questions as vq
    try:
        C = vq.count(reg, owed, measured, alerting, runbooks)
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
              | {a.get("agent", "").strip() for a in agent if a.get("element", "").strip() == "action"}) - {""}
    lines.append(f"parts with inside content (an operation on a participation row, or an agent's action "
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


# ---------------------------------------------------------------- the plan, and the go on it

BEFORE_GO = {"sources", "about", "how-made", "survey"}


def plan_and_go(reg):
    """(plan-first run, go recorded) from RUN.md's section *Plan and go*. A RUN.md without the section is from an
    earlier kit, and none of this applies to it."""
    run = reg / "RUN.md"
    text = run.read_text(encoding="utf-8") if run.is_file() else ""
    if not re.search(r"^## Plan and go\s*$", text, re.M):
        return False, False
    m = re.search(r"^- \*\*Go:\*\*[ \t]*(.*)$", text, re.M)
    words = (m.group(1).strip() if m else "")
    return True, bool(words) and not words.startswith("_")


def scope_of(reg):
    """(stage ids, why not). From scope.json's `stage_ids` when go.py wrote the go there; otherwise from RUN.md's line
    `- **Scope:** flow <id>; stages <id>, <id>`, set at the go. Ids are read only from the text before the person's
    words (the first quotation mark or bracket), so their words add no stage. An id that is not a stage in stages.csv
    (of the scoped flow, where one is named) is named in `why not`."""
    recorded = go_record.load(reg)
    if recorded is not None:
        ids = [str(x).strip() for x in recorded.get("stage_ids") or [] if str(x).strip()]
        if not ids:
            return None, ("the person has not yet picked how far each stage goes (after mapping: python go.py "
                          "<register> --depth ...); an earlier run, whose go named stages, records them as scope.json "
                          "stage_ids (python go.py <register> --stage-ids <id>)")
        known = {(r.get("stage") or "").strip() for r in table(reg, "stages")} - {""}
        bad = [x for x in ids if known and x not in known]
        if bad:
            return None, f"scope.json names {', '.join(bad)}, not a stage in stages.csv"
        return ids, ""
    run = reg / "RUN.md"
    text = run.read_text(encoding="utf-8") if run.is_file() else ""
    m = re.search(r"^- \*\*Scope:\*\*[ \t]*(.*)$", text, re.M)
    words = (m.group(1).strip() if m else "")
    if not words or words.startswith("_"):
        return None, "scope not recorded at the go (RUN.md, Plan and go, the line - **Scope:**)"
    head = re.split(r"[\"“(]", words, maxsplit=1)[0]
    flow = re.search(r"\bflow\s+([A-Za-z0-9_]+)", head)
    got = re.search(r"\bstages?\s+([A-Za-z0-9_]+(?:\s*,\s*[A-Za-z0-9_]+)*)", head)
    if not got:
        return None, "scope names no stage (RUN.md, - **Scope:** flow <id>; stages <id>, <id>)"
    ids = [x.strip() for x in got.group(1).split(",") if x.strip()]
    rows = [r for r in table(reg, "stages") if (r.get("stage") or "").strip()]
    if rows:
        known = {r["stage"].strip() for r in rows if not flow or (r.get("flow") or "").strip() in ("", flow.group(1))}
        bad = [x for x in ids if x not in known]
        if bad:
            return None, (f"scope names {', '.join(bad)}, not a stage of "
                          f"{'flow ' + flow.group(1) if flow else 'the register'} in stages.csv")
    return ids, ""


def read_before_go(reg):
    """What the run wrote that the plan's go has to come before: walk tables with rows, stage folders, the map."""
    early = []
    for p in sorted(reg.glob("*.csv")):
        if p.stem in BEFORE_GO:
            continue
        with p.open(encoding="utf-8-sig", newline="") as f:
            if len(list(csv.reader(f))) > 1:
                early.append(p.name)
    early += sorted(p.name + "/" for p in reg.glob("stage-*") if p.is_dir())
    early += [f for f in MAP_FILES if (reg / f).exists()]
    return early


def report(reg, named=(), full=True):
    """(what main prints, one string per printed line, done, the reasons it is NOT DONE). `full` False leaves out the
    Fullness block, which never changes whether the run is done."""
    out, reasons = [], []
    planned, go = plan_and_go(reg)
    if planned:
        has_plan = present(reg, "PLAN.md")
        out.append(f"Plan: PLAN.md {'ok' if has_plan else 'MISSING'}; go: "
                   f"{'recorded' if go else 'not recorded, so the run is waiting for the go'}")
        early = [] if go else read_before_go(reg)
        if early:
            out.append(f"READ BEFORE THE GO: {', '.join(early)} hold work, but RUN.md records no go on the plan. "
                       "The plan's go comes before any reading in depth.")
        if not has_plan or early or not go:
            why = ("PLAN.md MISSING" if not has_plan else
                   "read before the go" if early else "waiting for the go on the plan")
            out.append(f"NOT DONE: {why}")
            return out, False, [why + (f": {', '.join(early)}" if early else "")]
    depth = depth_of(reg)
    # a run whose person chose how far each stage goes is held to that choice; mapping only is a whole run
    scope, no_scope = scope_of(reg) if planned and depth is None else (None, "")
    owed = expected(reg, named, scope, depth)
    width = max(len(r) for r in owed)
    out.append(f"Register: {reg}")
    if depth is not None:
        out.append("How far each stage goes (scope.json, set by the person): " +
                   ", ".join(f"{s} {d}" for s, d in sorted(depth.items())))
    elif planned:
        out.append(f"Scope: {'stages ' + ', '.join(scope) + (' (scope.json, set at the go)' if go_record.load(reg) is not None else ' (RUN.md, set at the go)') if scope else no_scope}")
    missing = old = 0
    gone, aged = [], []
    if not stages(reg, named) and not scope and depth is None:
        out.append(f"{'stage-<id>/':<{width}}  MISSING (no stage has had Step 11)")
        missing += 1
        gone.append("stage-<id>/ (no stage has had Step 11)")
    for rel in owed:
        ok = present(reg, rel)
        missing += not ok
        why_stale = stale(reg, rel) if ok else ""
        old += bool(why_stale)
        if not ok:
            gone.append(rel)
        if why_stale:
            aged.append(rel)
        out.append(f"{rel:<{width}}  {('STALE (' + why_stale + ')') if why_stale else 'ok' if ok else 'MISSING'}")
    later = outside(reg, named, in_scope(scope, named)) if scope else []
    for s in later:
        out.append(f"stage-{s}: not yet covered: no alerts or runbooks (outside this run's scope)")
    for s, d in sorted((depth or {}).items()):
        said_of = {"none": "mapped, not measured", "measure": "measured; no alerts or runbooks",
                   "alerting": "measured and alerts; no runbooks"}.get(d)
        if said_of:
            out.append(f"stage-{s}: {said_of}")
    total = len(owed) + (0 if stages(reg, named) or scope or depth is not None else 1)
    if depth is not None:
        every = sorted(depth)
        vq_lines, why = view_questions(reg, every, {s for s, d in depth.items() if d != "none"},
                                       {s for s, d in depth.items() if d in ("alerting", "runbooks")},
                                       {s for s, d in depth.items() if d == "runbooks"})
    else:
        vq_lines, why = view_questions(reg, in_scope(scope, named) if scope else stages(reg, named))
    said = f"{missing} of {total} expected outputs missing" if missing else f"all {total} expected outputs exist"
    if missing:
        reasons.append(f"{missing} of {total} expected outputs missing ({', '.join(gone)})")
    if old:
        said += f"; {old} stale (generated from the register as it was, not as it is now)"
        reasons.append(f"{old} stale, generated from the register as it was ({', '.join(aged)})")
    unread = False
    if planned:
        reading = reading_check.check(reg)
        out.append("\n".join(reading.lines()))
        unread = not reading.passed
        if unread:
            said += "; cited code not read by the run"
            reasons.append("cited code not read by the run")
        if (reg / layout.UNITS_CSV).is_file():
            lines, why_split = split_checks(reg)
            out.append("\n".join(lines))
            if why_split:
                unread = True
                said += "; " + "; ".join(why_split)
                reasons += why_split
        else:
            sample = reread.check(reg)
            out.append("\n".join(sample.lines()))
            if not sample.passed:
                unread = True
                said += "; sampled rows not re-read and borne out"
                reasons.append("sampled rows not re-read and borne out")
    if no_scope:
        said += f"; {no_scope}"
        reasons.append(no_scope)
    blank = blank_drawings(reg)
    for rel in blank:
        out.append(f"{rel}  BLANK (its drawing shows no messages, work, stages or operations)")
    if blank:
        said += f"; {len(blank)} drawing{'s' if len(blank) > 1 else ''} blank"
        reasons.append(f"drawings with no content ({', '.join(blank)}): find why the drawing came out empty and draw "
                       "it again")
    unplaced = counted_at_missing(reg)
    out += unplaced
    if unplaced:
        said += f"; {len(unplaced)} measure{'s' if len(unplaced) > 1 else ''} with no counted_at"
        reasons.append("measures with a citation and no counted_at (" +
                       ", ".join(u.split(":")[0][len("measures.csv "):] for u in unplaced) +
                       "): write where each is counted, from its own citation")
    if why:
        reasons.append(f"view questions not answered: {'; '.join(why)}")
    done = not (missing or why or old or unread or no_scope or blank or unplaced)
    note = judges_note(reg) if planned and (reg / layout.UNITS_CSV).is_file() else ""
    if not done:
        out.append(f"NOT DONE: {said}" + (f"; view questions not answered: {'; '.join(why)}" if why else "")
                   + (f"; {note}" if note else ""))
    else:
        # the DONE token stays, the skill reads it; what exists is a draft for review, not accepted
        out.append(f"DONE: every expected output exists, all {total}: a draft for review, not accepted"
                   + (f"; {note}" if note else ""))
    if full:
        try:
            block = fullness(reg, vq_lines)
        except Exception as e:  # the other counts never change whether the run is done
            block = [f"Fullness: not counted ({type(e).__name__}: {e})"] + vq_lines
        out.append("\n".join(block))
    return out, done, reasons


def verdict(reg, named=()):
    """(done, the reasons it is not): the DONE or NOT DONE line's decision, without the Fullness counts."""
    _, done, reasons = report(pathlib.Path(reg), named, full=False)
    return done, reasons


def main(argv):
    if not argv:
        sys.exit(__doc__)
    reg = pathlib.Path(argv[0])
    if not reg.is_dir():
        sys.exit(f"not a folder: {reg}")
    out, done, _ = report(reg, argv[1:])
    for line in out:
        print(line)
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
