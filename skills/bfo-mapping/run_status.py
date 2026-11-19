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


def reading_units(reg, units):
    """(owed the whole unit reading check, owed provenance only): each reading unit (never `flow`). One whose
    deployable the go of the flow worked now took in (`services_in`; every unit when the go names none), or that was
    surveyed after that go and not left out by it (go.services_read: code got for an external dependency), is owed the
    whole check whatever its folder and rows: the flow reads it for itself, so a unit an earlier flow read, or one never
    written, is not let off. Any other unit with a folder and rows of that flow, merged and judged as every unit folder
    is, is owed the provenance of its cells, since no reader of it was launched."""
    import provenance
    took = go_record.services_read(reg)  # a service surveyed after the go is read too
    deployable = {(r.get("unit") or "").strip(): ((r.get("deployable") or "").strip() or (r.get("unit") or "").strip())
                  for r in tables.dicts(reg / layout.UNITS_CSV)}
    readers = [u for u in units if u != "flow"]
    whole = [u for u in readers if took is None or deployable.get(u, u).lower() in took]
    return whole, [u for u in readers if u not in whole and layout.unit_dir(reg, u).is_dir()
                   and provenance.current_rows(reg, u)]


UNITS_MISSING = (f"the flow is not read in reading units ({layout.UNITS_CSV} is missing), so none of its findings is "
                 "judged: run units.py, the readers, the merge and the judges (the steps' order), then this check again")


def split_checks(reg):
    """A split run's checks in place of the sample re-read: every unit's rows judged by the number of judges
    run-settings.json sets and flagged rows judged again (judges.py, from the transcripts), and the map what a merge of
    the unit folders gives (merge.py), with every call between units it leaves unmatched re-read and resolved
    (merge.rereads). Above `merge_rereads` (run-settings.json) calls not resolved, re-reading them one by one is not the
    remedy: the reason says to read again the units they call. A unit outside every scope so far (merge.py) owes
    nothing and is not judged. Every reading unit of the go's scope, whatever its rows, is owed the unit
    reading check (reading_check.py --unit): read in full by its own reader, every cell of its tables accounted for by
    its typed writers (provenance.py). Any other unit with a folder and rows of that flow is owed the provenance of its
    cells alone: it is merged and judged as every unit folder is. With no units.csv the flow was never read in units,
    and nothing of it is judged: that is the reason, and no other check runs."""
    if not (pathlib.Path(reg) / layout.UNITS_CSV).is_file():
        return [f"Units: NOT DONE: no {layout.UNITS_CSV}"], [UNITS_MISSING]
    outside = merge.out_of_scope_units(reg)
    units = [r["unit"].strip() for r in tables.dicts(reg / layout.UNITS_CSV) if (r.get("unit") or "").strip()
             and r["unit"].strip() not in outside]
    lines, why = [], []
    import units as unit_list  # the reader rule keys on units.csv, so units.csv is checked first
    s = go_record.load(reg) or {}
    took = go_record.services_read(reg, s) if s else None
    differ = unit_list.differences(reg, took) if s else []
    lines.append("Units against units.py: " + ("ok" if not differ else f"NOT DONE: {len(differ)} difference(s)"))
    lines += [f"  {d}" for d in differ]
    if differ:
        why.append(f"{layout.UNITS_CSV} is not what units.py derives for the go's scope, so a service of it would go "
                   "unread (" + "; ".join(differ) + "): run units.py, then the readers it owes")
    n = judges_per_row(reg)
    for u in units:
        for r in (judges.check(reg, u), judges.fix_check(reg, u)):
            lines += r.lines()
            if not r.passed and not any(w.startswith("rows not judged by ") for w in why):
                why.append(f"rows not judged by {COUNT_WORDS.get(n, n)} judge{'s' if n != 1 else ''}")
    import readers  # which units of the go's scope still owe a reader for this flow: printed, never worked out alone
    owed, read = ([u for u in got if u != "flow"] for got in readers.in_scope(reg))
    lines.append("Readers owed for this flow: " + (
        f"{', '.join(owed)} (python readers.py prompt <register> --in-scope)" if owed else
        "none" + (f" (read for this flow: {', '.join(read)})" if read else "")))
    unread = []
    whole, cells_only = reading_units(reg, units)
    for u in whole:
        r = reading_check.check_unit(reg, u)
        lines += r.lines()
        if not r.passed:
            unread.append(u)
    for u in cells_only:
        import provenance
        got = provenance.unit(reg, u).problems
        lines.append(f"Unit {u}. Outside the go's scope, cells: " + ("ok" if not got else
                                                                     f"NOT ACCOUNTED: {len(got)} problem(s)"))
        lines += [f"  provenance: {p}" for p in got[:50]]
        if got:
            unread.append(u)
    if unread:
        why.append("units not read in full by their own reader, or with cells no writer of theirs accounts for: "
                   + ", ".join(unread))
    _, problems = merge.check(reg)
    lines.append("Merge: ok" if not problems else f"Merge: NOT DONE: {'; '.join(problems)}")
    if problems:
        why.append("the map is not the merge of the units: " + "; ".join(problems))
    calls = merge.rereads(reg)
    left = [c for c in calls if not c["resolved"]]
    if not calls:
        lines.append("Unmatched calls between units: none")
    elif not left:  # a call naming no unit could be re-read on its calling side only, and is said apart
        one_sided = sum(1 for c in calls if c["calling_side_only"])
        lines.append(f"Unmatched calls between units: ok: {len(calls)} re-read and labelled disputed"
                     + (f", {one_sided} of them on the calling side only (no unit named)" if one_sided else ""))
    else:
        lines.append(f"Unmatched calls between units: NOT DONE: {len(left)} of {len(calls)} not re-read and resolved")
        lines += [f"  {c['problem']}" for c in left[:40]]
        lines += [f"  ... and {len(left) - 40} more"] if len(left) > 40 else []
        why.append(f"calls between units not re-read and resolved: {len(left)}")
        cap = settings.number(settings.load(reg), "merge_rereads")
        if len(left) > cap:
            called = ", ".join(sorted({c["to_unit"] for c in left if c["to_unit"]})) or "none named"
            why.append(f"{len(left)} calls between units unmatched, more than the {cap} merge_rereads allows to "
                       f"re-read one by one: read again the units they call ({called})")
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


UNTRIED = ("Before hand-over: {n} runbook tests not yet tried on a known case: try each once, on a case whose answer "
           "is known (a seeded row or a reproduced failure), and record it in how-made.csv")


def untried_tests(reg):
    """How many tests the runbooks hold, none of which the run has tried on a known case: each failure mode with a
    test, of every stage taken to runbooks (every stage with a runbook, in a run with no pick of how far each goes).
    The run reads code and runs nothing, so none is tried; the count is a readiness item owed before hand-over, said
    in the done check's report and never in the runbook, and never a reason the run is not done."""
    import flow_outputs as fo
    reg = pathlib.Path(reg)
    depth = depth_of(reg)
    wanted = ({s for s, d in depth.items() if d == "runbooks"} if depth else
              {p.name[len("stage-"):] for p in reg.glob("stage-*") if (p / "RUNBOOK.md").is_file()})
    if not wanted:
        return 0
    R = fo.load(reg)
    flow_of = {r["stage"]: r.get("flow") for r in R["stages"]}
    modes = set()
    for s in sorted(wanted & set(flow_of)):
        modes |= {r["mode_id"] for r in fo.live(fo.build(R, flow_of[s], s)) if (r.get("test") or "").strip()}
    return len(modes)


def depth_of(reg):
    """{stage: none | measure | alerting | runbooks}, how far the person chose to take each stage (scope.json `depth`,
    written by go.py --depth), or None for a run whose person made no such choice."""
    got = go_record.depth_all(reg)  # every flow picked in this register, each stage at its own flow's pick
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


def agent_classing(reg):
    """The map's classing of each AI agent's tools, replies and chained actions as its decisions or not (FILL-STEPS
    Step 7): the rules' messages for every flow, so a mapping-only run owes it as much as one taken further."""
    import map_record as mr
    try:
        R = mr.load(reg)
    except (OSError, KeyError, ValueError):  # a register too incomplete to read is reported by the other checks
        return []
    flows = [f["flow_id"] for f in R["flows"] if any(s["flow"] == f["flow_id"] for s in R["stages"])]
    return list(dict.fromkeys(mr.chain_failures(R) + [e for f in flows for e in mr.class_failures(R, f)]))


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


def mapping_owed(reg, flow_id):
    """[(what, how many, reason)]: the reasons report() gives for NOT DONE that are mapping's to put right, run when
    mapping ends (check_map.py at the map stop) by the same predicates report() runs, so mapping cannot call its
    phases done while the done check would still fail on its rows. `what` is "questions", "register", "drawings" or
    "code". Mapping's: the view questions a flow mapped only is asked (its stages', steps' and flow's, and every
    part's; none of measuring's, alerting's or runbooks'), the register check the drawing runs (undrawable), the
    drawings (blank_drawings), and, in a
    run with a plan that is not split, the code its rows cite (reading_check). Also mapping's, and already rules of
    check_map.py: agent classing, an id used twice, a finished flow's row changed. Not mapping's: the stage files the
    depth pick owes, their freshness, counted_at, the measures review, and the re-read, which the kit draws after."""
    reg = pathlib.Path(reg)
    out = []
    own = [s.get("stage", "").strip() for s in table(reg, "stages") if s.get("flow", "").strip() == flow_id]
    _, why = view_questions(reg, own, set(), set(), set())
    if why:
        n = sum(int(m) for w in why for m in re.findall(r" (\d+) (?:empty|gapped not read)", w)) or len(why)
        out.append(("questions", n, f"view questions not answered: {'; '.join(why)}"))
    refused = undrawable(reg)
    if refused:
        out.append(("register", len(refused), cannot_draw_reason(refused)))
    blank = blank_drawings(reg)
    if blank:
        out.append(("drawings", len(blank), f"drawings with no content ({', '.join(blank)}): find why the drawing "
                    "came out empty and draw it again"))
    if plan_and_go(reg)[0] and not (reg / layout.UNITS_CSV).is_file() and not reading_check.check(reg).passed:
        out.append(("code", 1, "cited code not read by the run (python reading_check.py <register folder> names "
                    "what to read, cite or set aside)"))
    return out


def undrawable(reg):
    """The register check's errors, the ones the map's drawing (one_canvas.py, capability_views.py --check) refuses
    on: [] when the map can be drawn. Run at the map stop, so mapping never reports done on a map that cannot be drawn
    (the inspection and the register check can pass while the drawing still refuses rows, such as parts with no kind)."""
    sys.path.insert(0, str(HERE))
    import capability_views as cv
    return cv.check(cv.load(reg))[0]


def cannot_draw_reason(errors):
    shown = "; ".join(errors[:5]) + (f"; and {len(errors) - 5} more" if len(errors) > 5 else "")
    return (f"the map cannot be drawn: its register check refuses {len(errors)} row(s): {shown} (python "
            "capability_views.py <register folder> --check lists each)")


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
    a candidate in measures.csv covers, and those not covered that a row of measure-gaps.csv accounts for. With no
    stage measured by the person's pick, no receipt is owed (flow_outputs.receipt_failures runs none), and the line
    says so rather than count one."""
    flows = [f.get("flow_id", "").strip() for f in table(reg, "flows")]
    with_stages = {s.get("flow", "").strip() for s in table(reg, "stages")}
    flows = [f for f in flows if f and f in with_stages]
    if not flows:
        return ["receipt: none (no flow with a stage row)"]
    depth, none_owed = depth_of(reg), []
    if depth is not None:  # a flow every stage of which is mapped only owes no measures, so no receipt
        of_flow = {}
        for s in table(reg, "stages"):
            of_flow.setdefault(s.get("flow", "").strip(), []).append(s.get("stage", "").strip())
        mapped_only = [f for f in flows if all(depth.get(s, "none") == "none" for s in of_flow.get(f, []))]
        flows = [f for f in flows if f not in mapped_only]
        none_owed = [f"receipt for {f}: not owed (no stage is measured: each is mapped only)"
                     for f in mapped_only]
        if not flows:
            return none_owed
    try:
        sys.path.insert(0, str(HERE))
        import flow_outputs as fo
        R = fo.load(reg)
    except Exception as e:  # a register the generator cannot read still gets its other counts
        return [f"receipt: not counted ({type(e).__name__}: {e})"]
    out = list(none_owed)
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


NOT_READ_BY_STAGE = ("part: operations", "part: depends on")  # what only a part's reading answers


def parts_of_unpicked_stages(reg, measured):
    """{subject id}: in a flow read by stage (go.BY_STAGE), each part that takes part in a process step of this flow
    and in none of a stage taken past mapped only (`measured`), and whose service no such stage reaches by the closure
    of its calls (go.stage_reading): it is not read, so its operations and what it depends on may be gapped `not read`
    on a first run. Empty for a flow an earlier release took the go of, and when every service is read."""
    stage_of = {(r.get("step") or "").strip(): (r.get("stage") or "").strip() for r in table(reg, "steps")}
    part_stages = {}
    for p in table(reg, "participation"):
        sid = (p.get("subject_id") or "").strip()
        if sid:
            part_stages.setdefault(sid, set()).add(stage_of.get((p.get("step") or "").strip(), ""))
    subj = {(r.get("subject_id") or "").strip(): r for r in table(reg, "subjects")}
    current = go_record.load(reg) or {}
    excused, read_somewhere = set(), set()
    for s in go_record.load_all(reg):  # each flow by its own pick and reading: a finished flow keeps its excuse
        if not s.get(go_record.BY_STAGE):
            continue
        picked = set(go_record.picked_stages(s))
        if s.get("flow") == current.get("flow"):
            picked |= set(measured or ())  # the pick on record holds whoever asks
        mine = set(go_record.stages_of(reg, s))
        read_somewhere |= {sid for sid, sts in part_stages.items() if sts & picked}
        read = go_record.staged_services(reg, s)
        if read is None:  # every service its go took in is read: none of its parts is let off
            continue
        for sid, sts in part_stages.items():
            mine_sts = sts & mine
            if mine_sts and not mine_sts & picked and go_record.service_of(reg, subj.get(sid)) not in read:
                excused.add(sid)
    # map only in some flow, and read in none: a part a stage taken further runs through is never let off
    return excused - read_somewhere


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
    unpicked = parts_of_unpicked_stages(reg, measured)
    why = []
    for q in vq.QUESTIONS:
        if vq.CONTRACT[q] == vq.COUNT:
            continue
        if C[q]["empty"]:
            why.append(f"{q} {len(C[q]['empty'])} empty")
        unread = C[q]["gapped"].get("not read", [])
        if q in NOT_READ_BY_STAGE:  # a part whose stages were all left mapped only is not read, by the person's pick
            unread = [e for e in unread if str(e).strip() not in unpicked]
        if first and unread:
            why.append(f"{q} {len(unread)} gapped not read on a first run")
    head = (f"view questions (answered / gapped / empty), first run: {'yes' if first else 'no'} (how-made.csv); "
            "required and answer-or-gap ones decide DONE, count-only ones never do")
    return [head] + vq.lines(C), why


def questions_owed_mapped_only(reg):
    """What the done check will owe of the map for the flow worked now if it is left mapped only, and every earlier
    flow at its own pick: the view questions' reasons, exactly as the done check states them. Mapping's own end check
    (run_status.py --mapping, and go.py --mapping-ends), so mapping never hands back a map the done check then refuses."""
    depth = dict(depth_of(reg) or {})
    for s in table(reg, "stages"):
        depth.setdefault(s.get("stage", "").strip(), "none")
    depth.pop("", None)
    return view_questions(reg, sorted(depth), {s for s, d in depth.items() if d != "none"},
                          {s for s, d in depth.items() if d in ("alerting", "runbooks")},
                          {s for s, d in depth.items() if d == "runbooks"})[1]


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
            pick = ("the person has not yet picked how far each stage goes (after mapping: python go.py <register> "
                    "--depth ...)")
            if not recorded.get("stages"):  # a go by this kit names no stages: --stage-ids does not apply to it
                return None, pick
            return None, (pick + "; this run's go is from before that pick and named stages, so it may instead record "
                          "the ids of exactly those stages as scope.json stage_ids (python go.py <register> "
                          "--stage-ids <id>)")
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
    unread = reread_pending = False
    if planned:
        reading = reading_check.check(reg)
        out.append("\n".join(reading.lines()))
        unread = not reading.passed
        if unread:
            said += "; cited code not read by the run"
            reasons.append("cited code not read by the run")
        if in_units(reg):
            lines, why_split = split_checks(reg)
            out.append("\n".join(lines))
            if why_split:
                unread = True
                said += "; " + "; ".join(why_split)
                reasons += why_split
        else:
            sample = reread.check(reg)
            out.append("\n".join(sample.lines()))
            if not sample.passed:  # gates the run's DONE and its report, never the next flow
                reread_pending = True
                said += "; sampled rows not re-read and borne out"
                reasons.append(REREAD_REASON)
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
    changed, twice = go_record.earlier_rows_changed(reg), go_record.reused_ids(reg)
    out += [f"CHANGED (a finished flow's row): {c}" for c in changed] + [f"ID USED TWICE: {t}" for t in twice]
    if changed:
        said += f"; {len(changed)} row{'s' if len(changed) > 1 else ''} of a finished flow changed"
        reasons.append("rows of a finished flow changed (" + "; ".join(changed) + "): put each back as it was; a "
                       "correction to a finished flow goes in corrections.csv")
    if twice:
        said += f"; {len(twice)} id{'s' if len(twice) > 1 else ''} used twice"
        reasons.append("ids used twice (" + "; ".join(twice) + "): a further flow's ids continue after the highest "
                       "the map holds")
    unclassed = agent_classing(reg)
    out += [f"AI AGENT NOT CLASSED: {e}" for e in unclassed]
    if unclassed:
        said += f"; {len(unclassed)} AI agent row{'s' if len(unclassed) > 1 else ''} not classed"
        reasons.append("an AI agent's tools, replies or chained actions not classed as its decisions or not (Step 7): "
                       + "; ".join(unclassed))
    unreviewed = measures_review_reasons(reg)
    out += [f"MEASURES REVIEW: {r}" for r in unreviewed]
    if unreviewed:
        said += "; the review of the measures " + ("not recorded" if any("not recorded" in r for r in unreviewed)
                                                   else "outdated by a later change"
                                                   if any("changed after" in r for r in unreviewed)
                                                   else "owes a request still open")
        reasons += unreviewed
    if why:
        reasons.append(f"view questions not answered: {'; '.join(why)}")
    outputs_done = not (missing or why or old or unread or no_scope or blank or unplaced or changed or twice
                        or unclassed or unreviewed)
    done = outputs_done and not reread_pending
    if planned:  # a split run's rows are judged by the judges, and it draws no sample to re-read
        out.append(state_said(outputs_done, None if in_units(reg) else own_reread_passed(reg)))
        pending = earlier_pending(reg)
        if pending:  # a later flow's report says, under What remains, which earlier flow's re-read is still owed
            out.append("What remains, for this flow's report: the re-read of " + ", ".join(pending) + ".")
        out.append("Close (phase 7): done when every flow's report is sent" + (
            "." if in_units(reg) else ", each once its own re-read has passed."))
        out += flow_states(reg, outputs_done)
    try:
        untried = untried_tests(reg)
    except Exception:  # a readiness count, owed before hand-over: it never changes whether the run is done
        untried = 0
    if untried:
        out.append(UNTRIED.format(n=untried))
    note = judges_note(reg) if planned and in_units(reg) else ""
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


VERDICT = "done-check.json"  # the done check's last verdict, with the map it was given on
REREAD_REASON = "sampled rows not re-read and borne out"


def state_said(outputs_done, reread_passed):
    """The two states the done check holds apart: this flow's outputs (they open the next flow), and its re-read
    (with the rest, it makes the run DONE and lets its report go onward)."""
    if not outputs_done:
        return "State: this flow's outputs: not done."
    if reread_passed is None:
        return "State: this flow's outputs: done."
    return f"State: this flow's outputs: done; its re-read: {'passed' if reread_passed else 'pending'}."


def measures_review_reasons(reg):
    """Why the measures review holds the run back: the flow worked now, with a stage its pick measures, has no go on
    its measures (where RUN.md has the review's row: an earlier register is not held to it); and, for every flow with
    a go, each of its rows of proposing the measures changed, added or gone since. [] when none."""
    reg = pathlib.Path(reg)
    out = []
    cur = go_record.load(reg)
    measured = any(d != "none" for d in ((cur or {}).get("depth") or {}).values())
    if cur is not None and measured and go_record.measures_review_state(reg)[0] and not cur.get("measures_reviewed"):
        out.append(f"the person's review of the measures is not recorded for the flow {cur.get('flow', '')}: show "
                   "them the measures (brief.py measures) and record their answer (go.py --measures-reviewed)")
    for s in go_record.load_all(reg):
        if not s.get("measures_reviewed"):
            continue
        fid = go_record.flow_id_of(reg, s)
        changed = go_record.measures_changed(reg, fid)
        if changed:
            out.append(f"the flow {s.get('flow', fid)}'s measures changed after the review of the measures ("
                       + "; ".join(changed) + "): show the person the measures again and record their answer")
    for r in go_record.measures_requests(reg):  # a later step asked proposing the measures, which has not answered
        cid = (r.get("correction_id") or "").strip()
        out.append(f"corrections.csv {cid} asks proposing the measures for a change to {r.get('table')}.csv and is "
                   f"still open: take the run back to it (go.py --back-to-measures {cid}), take the request up or "
                   "turn it down there, and show the person the measures again")
    return out


def in_units(reg):
    """The flow worked now is mapped in reading units: every finding that cites code is judged (split_checks), no
    sample is drawn, and nothing waits on one. So is every flow whose go this kit recorded (go.IN_UNITS), whether or not
    units.csv is there yet: without it the flow is not done. Only a flow an earlier release took the go of, in a
    register with no units.csv, keeps its sample."""
    reg = pathlib.Path(reg)
    return (reg / layout.UNITS_CSV).is_file() or bool((go_record.load(reg) or {}).get(go_record.IN_UNITS))


def owes_sample(reg, s):
    """The flow `s` records drew a sample of ten to re-read: its go was taken by an earlier release (no go.IN_UNITS),
    and the register is not mapped in units."""
    return not (s.get(go_record.IN_UNITS) or (pathlib.Path(reg) / layout.UNITS_CSV).is_file())


def own_reread_passed(reg):
    """The flow worked now's own sample re-read and borne out (another flow's pending re-read is that flow's). A
    register mapped in units draws none: its findings are judged as part of its outputs."""
    import reread
    reg = pathlib.Path(reg)
    if in_units(reg):
        return True
    s = go_record.load(reg)
    sheet = reread.sheet_for(reg, s)
    return sheet.is_file() and reread.check_sheet(reg.resolve(), sheet).passed


def earlier_pending(reg):
    """The flows before the one worked now whose own re-read has not passed, by name (none in a register mapped in
    units, which draws no sample)."""
    import reread
    reg = pathlib.Path(reg)
    cur = go_record.load(reg)
    out = []
    for s in go_record.load_all(reg):
        if (cur is not None and s.get("flow") == cur.get("flow")) or not owes_sample(reg, s):
            continue
        sheet = reread.sheet_for(reg, s)
        if not (sheet.is_file() and reread.check_sheet(reg.resolve(), sheet).passed):
            out.append(s.get("flow", ""))
    return out


def report_current(reg, s):
    """The flow `s`'s report is sent, and no correction to its rows was applied since: a later correction owes it
    again, once its re-read has passed."""
    return bool(s.get("report_sent")) and not reread.corrected_since_report(reg, s)


def flow_states(reg, outputs_now=None):
    """One line per flow the register has started: its outputs (done for a flow already finished; for the flow
    worked now, as this check finds them), its re-read (its own sample) and its report (sent once its re-read has
    passed: an earlier flow's report is owed then, while a later flow is under way)."""
    import reread
    reg = pathlib.Path(reg)
    cur = go_record.load(reg)
    out = []
    for s in go_record.load_all(reg):
        units = not owes_sample(reg, s)  # its findings are judged with its outputs, and no sample is drawn
        now = cur is not None and s.get("flow") == cur.get("flow")
        done = (outputs_hold(reg) if outputs_now is None else outputs_now) if now else True
        sheet = reread.sheet_for(reg, s)
        passed = units or (sheet.is_file() and reread.check_sheet(reg.resolve(), sheet).passed)
        again = bool(s.get("report_sent")) and not report_current(reg, s)
        report = ("sent" if s.get("report_sent") and not again else "owed now" if done and passed
                  else "waits on its re-read" if done else "waits on its outputs")
        out.append(f"Flow {s.get('flow', '')}: outputs: {'done' if done else 'not done'}; "
                   + ("" if units else f"re-read: {'passed' if passed else 'pending'}; ") + f"report: {report}"
                   + (" again (corrected after it was sent)" if again else "")
                   + (" (record it with go.py --report-sent once sent)" if report == "owed now" else ""))
    return out


def outputs_done_of(done, reasons):
    """Everything but the sampled re-read passed: the next flow can open."""
    return bool(done) or (bool(reasons) and all(r == REREAD_REASON for r in reasons))


ROUND_RECORD = re.compile(r"r\d+-rows\.csv")  # judging/<unit>/r<n>-rows.csv: derived, never fingerprinted


def _rows_digest(files, root):
    """One digest of the files' rows, each read as rows (a byte-order mark, line endings or quoting change nothing)
    and named by its path under root."""
    import hashlib
    import json
    got = []
    for p in sorted(files, key=lambda q: q.relative_to(root).as_posix()):
        with p.open(encoding="utf-8-sig", newline="") as f:
            got.append([p.relative_to(root).as_posix(), [r for r in csv.reader(f) if any(c.strip() for c in r)]])
    return hashlib.sha256(json.dumps(got, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def verdict_fingerprint(reg):
    """The fingerprint a stored verdict is kept with: the map's tables (flow_outputs.fingerprint) and, in a split run,
    its units (units.csv and each unit's tables, files.csv aside) and its verdict files (judgements.csv and the round
    records aside, being derived). A register with no units/ or judging/ has the map's tables alone."""
    import flow_outputs as fo
    reg = pathlib.Path(reg)
    out = fo.fingerprint(reg)
    units = reg / layout.UNITS
    if units.is_dir():
        files = [p for p in units.glob("*.csv")] + [p for t in layout.UNIT_TABLES for p in units.glob(f"*/{t}.csv")]
        out[layout.UNITS] = _rows_digest(files, reg)
    verdicts = [p for p in layout.judging_dir(reg).glob("*/*.csv") if not ROUND_RECORD.fullmatch(p.name)]
    if verdicts:
        out[layout.JUDGING] = _rows_digest(verdicts, reg)
    return out


MAPPING_CHECK = "mapping-check.json"  # the split checks' verdict at the end of mapping alone, with its fingerprint


def split_reasons(reg):
    """split_checks' reasons, the units not judged named: [] when the split checks pass."""
    lines, why = split_checks(reg)
    bad = sorted({m.group(1) for ln in lines for m in [re.match(r"(?:Judging|Fixing) of unit (\S+), round \d+: .*NOT "
                                                                r"DONE", ln)] if m})
    return [w + (f" (units: {', '.join(bad)})" if w.startswith("rows not judged") and bad else "") for w in why]


def store_mapping_check(reg, flow_id):
    """At the end of mapping alone, the split checks: their reasons when they do not pass, else [] and their verdict
    stored with the fingerprint, so the flow stays finished after its transcripts are gone, and only while nothing
    the fingerprint covers changes."""
    import json
    reasons = split_reasons(reg)
    if not reasons:
        got = {"passed": True, "flow": flow_id, "tables": verdict_fingerprint(reg)}
        (pathlib.Path(reg) / MAPPING_CHECK).write_text(json.dumps(got) + "\n", encoding="utf-8")
    return reasons


def mapping_check_holds(reg):
    """A flow not mapped in units (an earlier release's go, no units.csv), or the split checks' stored verdict at the
    end of mapping alone passed and nothing it covers has changed since."""
    import json
    reg = pathlib.Path(reg)
    if not in_units(reg):
        return True
    try:
        got = json.loads((reg / MAPPING_CHECK).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(got.get("passed")) and got.get("tables") == verdict_fingerprint(reg)


def record_verdict(reg, done, outputs_done=None):
    """The done check's verdict, kept with the fingerprint of the map it judged: phase 7 counts done only while it
    says DONE on the map as it is now, and the next flow opens while its outputs are done, the re-read apart."""
    import json
    got = {"done": bool(done), "outputs_done": bool(done if outputs_done is None else outputs_done),
           "tables": verdict_fingerprint(reg)}
    (pathlib.Path(reg) / VERDICT).write_text(json.dumps(got) + "\n", encoding="utf-8")


def outputs_hold(reg):
    """The done check said this flow's outputs are done (the re-read apart), and the map has not changed since."""
    import json
    try:
        got = json.loads((pathlib.Path(reg) / VERDICT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(got.get("outputs_done", got.get("done"))) and got.get("tables") == verdict_fingerprint(reg)


def verdict_holds(reg):
    """The done check said DONE, and the map has not changed since."""
    import json
    p = pathlib.Path(reg) / VERDICT
    try:
        got = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(got.get("done")) and got.get("tables") == verdict_fingerprint(reg)


def verdict(reg, named=()):
    """(done, the reasons it is not): the DONE or NOT DONE line's decision, without the Fullness counts."""
    _, done, reasons = report(pathlib.Path(reg), named, full=False)
    return done, reasons


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if not argv:
        sys.exit(__doc__)
    reg = pathlib.Path(argv[0])
    if not reg.is_dir():
        sys.exit(f"not a folder: {reg}")
    if argv[1:] == ["--mapping"]:  # mapping's end check: what the done check owes of a map left mapped only
        owed, refused = questions_owed_mapped_only(reg), undrawable(reg)
        if not owed and not refused:
            print("MAPPED: the map answers every question the done check asks of a flow left mapped only, and can be "
                  "drawn")
            return 0
        said = (["view questions not answered: " + "; ".join(owed) + ". Answer each in the register, or write its gap "
                 "with the reason"] if owed else []) + ([cannot_draw_reason(refused)] if refused else [])
        print("NOT MAPPED: " + ". ".join(said) + ". Put each right and run this again.")
        return 1
    out, done, reasons = report(reg, argv[1:])
    import run_lock
    d = run_lock.read(reg)  # the verdict is the run's: a check run by another session while it works writes nothing
    if not (d and d["run"] != run_lock.identity() and not run_lock.stale(d)):
        record_verdict(reg, done, outputs_done_of(done, reasons))
    for line in out:
        print(line)
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
