"""The inspection of proposing the measures (MEASURES-STEPS.md Step 9): whether a flow's measures are fit to hand on, by rules that hold
whatever the measures say.

    python check_measures.py REGISTER FLOW STAGE [STAGE ...] [--detail]

STAGE: the stages the person picked to measure, as separate arguments or separated by commas. Run when proposing the measures ends,
before the alerts are chosen. It reports and never blocks. It does not judge whether a measure is right about the
system: a reviewer reading the cited sources does that. The default text is the person's, in plain words, read at the
measures review; --detail adds, under each line, the columns, checks and decisions behind it.

Two halves, run and shown in this order: what to measure (rules 1 to 6), then what the system produces (rules 7 to
11), numbered in the order shown. A rule may pass with notes: things to look at that are not failures. Rule 3 holds the checks on the ties to
expectations.csv (flow_outputs.expectation_failures). Unlike check_map.py it loads the page builder, because its rule
functions live in flow_outputs.py."""
import contextlib
import io
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import capability_views as cv  # noqa: E402
import check_map  # noqa: E402
import flow_outputs as fo  # noqa: E402
import go  # noqa: E402
import view_questions as vq  # noqa: E402

HALVES = [("what", "What to measure"), ("produces", "What the system produces")]
# (rule, number, half, title in plain words), in the order shown
RULES = [
    ("receipt", 1, "what", "Every item on the coverage list, for the picked stages and the flow, has a measure or a "
                           "reason why none"),
    ("expectations", 2, "what", "The whole flow and every picked stage have at least one expectation, and every "
                                "expectation of them has a business measure showing whether it is met, or a reason "
                                "why none"),
    ("expectation-ties", 3, "what", "Every expectation a measure points to is one recorded, every objective is stated "
                                    "by someone, with where it is stated, and no expectation's own words carry a file "
                                    "citation (that goes in where it is stated)"),
    ("lists", 4, "what", "Every measure says its kind of health signal, its shape and the kind of record it is taken "
                         "from, and every reason says why none is proposed, each in the words the method allows"),
    ("unpicked", 5, "what", "No measure is on a stage left mapped only"),
    ("for-flow", 6, "what", "Every measure says which flow it was proposed for"),
    ("produced", 7, "produces", "A measure produced today cites the line of code that produces it, and a proposed "
                                "measure says nothing about what it gets wrong or whether anything collects it"),
    ("watched", 8, "produces", "Where a measure produced today says whether anything collects it, the answer is one "
                               "the method allows, rests on a source of its own, not the line that produces it, and "
                               "is not unknown where the setting that decides it was read; and every measure says "
                               "what shows its data and names what would send it on"),
    ("places", 9, "produces", "Every place a measure is taken at is named in plain words, and measures taken at one "
                              "place agree on whether it is produced today and say what tells them apart"),
    ("ids", 10, "produces", "No two measures, expectations or other rows share a name, across every flow's work"),
    ("cases", 11, "produces", "A measure of cases is taken where one case can be told from another: never at a part "
                              "that never holds the case's own identifier, and never from a metric for a question "
                              "about each case"),
]
NOTES = {  # (plain, detail)
    "receipt": ("Which of an AI agent's tools, replies and chained actions are its decisions is mapping's to say, "
                "and mapping's own checks report a row left unclassed; this rule reads that classing",
                "flow_outputs.receipt_failures(R, flow, measured=picked) errors. The agent classing rules "
                "(map_record.class_failures, chain_failures) run in mapping's done check (run_status.py) and in "
                "check_map.py, not here. gap_rows' two errors on a kind outside GAP_KINDS are reported under rule 4; "
                "every other gap_rows error stays here"),
    "expectations": ("", "view_questions.status(M, 'expectation: indicator', id): answered through indicators() (a "
                         "business health or business impact measure naming the id in `expectation`, with no "
                         "`defect`) or gapped through gap_of() (a measure-gaps.csv row that view_questions.counts "
                         "accepts). Owed for the flow's own expectations and those of picked stages. Before "
                         "that: expectations.csv holds a row of the flow with `stage` blank, and one of each picked "
                         "stage (MEASURES-STEPS.md Step 9: the customer has at least one of the whole flow, and every "
                         "measured stage at least one)"),
    "expectation-ties": ("", "flow_outputs.expectation_failures(R, flow); `expectation` and `satisfied_when` match "
                             "no FILE_CITE (a path, a file name or file:line), the citation belongs in `source`"),
    "lists": ("Whether anything collects a measure is checked under rule 8. A reason given in words the method does "
              "not allow is reported here, not again under rule 1",
              "layer: capability_views.layer_of on method/layers.csv; form: method/measure-forms.csv, required; "
              "taken_from: the eleven kinds of REGISTER.md, required; measure-gaps.csv kind: flow_outputs.GAP_KINDS"),
    "for-flow": ("A part two flows measure has a measure for each flow, so each flow's review of its measures stands "
                 "alone", "measures.csv `for_flow` set on every row (go.measures_owners, go.alert_owners)"),
    "unpicked": ("A measure of a part or of the whole flow is on no one stage, so it is not judged here",
                 "a measure's `stage`, or the stage of its `step` in steps.csv"),
    "produced": ("", "exists yes: source_ref matches capability_views.CITE; exists not yes: no `defect` (the rule "
                     "flow_outputs.check() states inline), no `watched`, no `watched_source`"),
    "watched": ("Whether the cited source really is the configuration that collects it is for the reviewer",
                "flow_outputs.watched_failures on rows with exists yes (its values flow_outputs.WATCHED; unknown "
                "fails on a watched_source that cites a line, unless it opens 'no inventory reachable' or says "
                "'not read'), plus watched_source != source_ref. `watched` and `watched_source` are this step's"),
    "places": ("Whether what tells two measures apart is true of the place is for the reviewer",
               "flow_outputs.counted_at_failures and flow_outputs.same_place_failures; and alike_items: two rows "
               "with the same counted_at and the same counted_how fail unless a `defect` on one names the other or "
               "says they cannot be told apart"),
    "ids": ("", "go.reused"),
    "cases": ("A metric can show cases, as one raised once for each order placed; it cannot say which cases",
              "rows with counted_on cases: fail where `subject_id`, or a part whose name stands whole in "
              "`counted_at`, has carries_case_id `no` (a person excluded; `partly` passes); fail where taken_from "
              "is metric and receipt_question names one of PER_CASE; a note where taken_from is metric and "
              "counted_how matches no ONCE (the once-per-case basis)"),
}
NOT_YET = ["whether a measure is right about the system, which a reviewer reading the cited sources decides"]
# REGISTER.md `taken_from`: the eleven kinds of record a measure is taken from (MEASURES-STEPS.md Step 9)
TAKEN_FROM = ("metric", "log or event record", "trace", "the edge", "external probe", "client-side instrumentation",
              "the case's own record", "a message log kept with the state", "configuration",
              "platform lifecycle events", "another organisation's record")
# gap_rows' two errors on a gap's kind outside GAP_KINDS, which rule 4 reports instead; nothing else of gap_rows
KIND_ERRORS = (re.compile(r"^measure-gaps\.csv [^:]*: `kind` is [^`]*, not one of the four, so it does not count"),
               re.compile(r"^measure-gaps\.csv [^:]*: measure-gaps\.csv has no `kind` column, so it does not count"))
INDICATOR = "expectation: indicator"
# a file citation in an expectation's own words: a path, a source file's name, or file:line. It belongs in `source`.
FILE_CITE = re.compile(r"(?:[\w.-]+/)+[\w.-]+\.\w{1,8}\b|\b[\w-]+\.(?:cs|razor|cshtml|py|java|go|kt|rb|php|csv|md|"
                       r"json|ya?ml|xml|html|properties|toml|sql)\b|\.\w{1,8}:\d")
# the receipt's questions about each case: a metric cannot say which cases are in a stage or how old each is
PER_CASE = ("in the stage", "oldest's age", "past the time limit")
# counted_how giving the once-per-case basis (MEASURES-STEPS.md Step 9: "written once per case")
ONCE = re.compile(r"\bonce (?:per|for each|for every|a)\b|\bone (?:\S+ ){0,4}?(?:per|for each|for every)\b", re.I)
QUESTION_WORDS = {"application": "is the work being done correctly", "technology": "is what it runs on up",
                  "the time limit": "do cases finish within the time limit", "in the stage": "how many cases are in it now",
                  "oldest's age": "how long the oldest case has waited", "time through": "how long cases take through it",
                  "past the time limit": "how many cases are past the time limit"}


def picked_stages(args):
    return [s.strip() for a in args for s in a.split(",") if s.strip()]


class Said:
    """Plain words for the register's rows: measures by name, parts and expectations by what they say."""

    def __init__(self, R):
        self.m = {m.get("handle"): m for m in R["measures"]}
        self.subj = {s["subject_id"]: s.get("name") or s["subject_id"] for s in R["subjects"]}
        self.exp = {e.get("expectation_id"): e for e in R.get("expectations", [])}
        self.stage = {s["stage"]: s.get("name") or s["stage"] for s in R["stages"]}
        self.step = {s["step"]: s.get("name") or s["step"] for s in R["steps"]}

    def element(self, el):
        """An element a reason is recorded for, in words: an expectation, a stage, a step or a part by its own text;
        anything else (an operation, an agent's tool) as the record names it."""
        if el in self.exp:
            return self.expectation(el)
        if el in self.stage:
            return f"the stage {self.stage[el]}"
        if el in self.step:
            return f"the process step {self.step[el]}"
        return self.subj.get(el, el)

    def measure(self, h):
        m = self.m.get(h)
        return f"the measure “{m.get('measure') or h}”" if m else f"a measure {h}"

    def measures(self, hs):
        return " and ".join(self.measure(h.strip()) for h in hs)

    def expectation(self, i):
        e = self.exp.get(i)
        if not e:
            return f"an expectation {i}"
        text = re.sub(r"^\s*proposed:\s*", "", e.get("expectation") or i)
        return f"the expectation of {e.get('party') or 'a party'}, “{text}”"

    def part(self, sid):
        return self.subj.get(sid, sid)


def question(q):
    return QUESTION_WORDS.get(q, q)


def said_what(what):
    for lead, words in (("flow: ", "the flow "), ("stage: ", "the stage "), ("step: ", "the process step ")):
        if what.startswith(lead):
            return words + what[len(lead):]
    return what


def receipt_item(S, rec_by, e):
    """Plain words for one of receipt_failures' errors."""
    for prefix, r in rec_by.items():
        if e.startswith(prefix):
            return f"{said_what(r['what'])}: “{question(r['question'])}” has no measure, and no reason why none"
    m = re.match(r"participation\.csv (\S+) step (\S+): class (its tool|the agent's reply)", e)
    if m:
        what = "its tool" if m.group(3) == "its tool" else "its reply"
        return (f"mapping has not said whether {what}, for the AI agent {S.part(m.group(1))} at process step "
                f"{m.group(2)}, is a decision the case relies on")
    m = re.match(r"participation\.csv (\S+) (.*?): classed yes", e)
    if m:
        return (f"the AI agent {S.part(m.group(1))} is said to decide with {m.group(2)} at one process step and not "
                "at another; mapping classes it one way")
    m = re.match(r"agent-system\.csv (\S+) (\S+):", e)
    if m:
        return (f"an action of the AI agent {S.part(m.group(1))} in its chain is classed as a decision or not in a "
                "way the record does not allow; mapping classes it")
    m = re.match(r"measure-gaps\.csv (.*?), (.*?): (.*)", e)
    if m:
        el, q, rest = m.groups()
        why = ("it does not say why, or where that was read" if rest.startswith("no ") else
               "it says another measure covers it, and names none" if "names no measure" in rest else
               "it is for a question the coverage list does not ask" if "is not one the receipt asks" in rest else
               "that question takes no reason" if "takes no gap" in rest else
               "it does not meet that question's terms")
        return f"the reason recorded for {S.element(el)}, “{question(q)}”, does not stand: {why}"
    return "a row the coverage list reads needs fixing (run with --detail)"


def ties_item(S, e):
    m = re.match(r"measures\.csv (\S+): `expectation` names (.*?), not", e)
    if m:
        return f"{S.measure(m.group(1))} points to expectation {m.group(2)}, which is not among those recorded"
    m = re.match(r"expectations\.csv (\S+): objective .* is proposed", e)
    if m:
        return (f"the objective of {S.expectation(m.group(1))} is a proposal; an objective is only what a document "
                "or a person states, so leave it blank where none is stated")
    m = re.match(r"expectations\.csv (\S+): objective is set with no", e)
    if m:
        return f"the objective of {S.expectation(m.group(1))} does not say where it is stated"
    return "a tie between a measure and an expectation needs fixing (run with --detail)"


def cited_expectation_items(R, S):
    """An expectation whose own words, or whose satisfaction condition, carry a file citation."""
    out = []
    for e in R.get("expectations", []):
        for col, words in (("expectation", "its words"), ("satisfied_when", "what shows it met")):
            hit = FILE_CITE.search(e.get(col) or "")
            if hit:
                out.append((f"{S.expectation(e.get('expectation_id'))}: {words} carry a file citation; it goes in where "
                            "the expectation is stated, not in the words",
                            f"expectations.csv {e.get('expectation_id')}: `{col}` cites {hit.group(0)!r}; move it to "
                            "`source`"))
    return out


def alike_items(R, S):
    """Two measures at one place taken the same way, neither saying they cannot be told apart."""
    by = {}
    for m in R["measures"]:
        at = fo.norm(m.get("counted_at")).lower()
        if at and not at.startswith("not in the code"):
            by.setdefault((at, fo.norm(m.get("counted_how")).lower()), []).append(m)
    out = []
    for (at, _), ms in by.items():
        if len(ms) < 2:
            continue
        hs = [m["handle"] for m in ms]
        told = any(re.search(r"\bapart\b", m.get("defect") or "", re.I)
                   or any(h != m["handle"] and re.search(rf"\b{re.escape(h)}\b", m.get("defect") or "") for h in hs)
                   for m in ms)
        if not told:
            out.append((f"{S.measures(hs)} are taken at the same place ({at}) in the same way: say in how each is "
                        "taken what tells them apart, or say in one, as what it gets wrong, that they cannot be told "
                        "apart", f"measures.csv {', '.join(hs)}: the same counted_at ({at}) and the same counted_how, "
                        "and no defect says they cannot be told apart"))
    return out


def cases_items(R, S):
    """([failures], [notes]) on the measures of cases: where the case cannot be told apart at the place, or from the
    kind of record."""
    never = {s["subject_id"]: s for s in R["subjects"]
             if (s.get("kind") or "element") == "element" and s.get("part_kind") != "person"
             and fo.norm(s.get("carries_case_id")).lower().startswith("no")}
    fails, notes = [], []
    unknown_at = {}  # part id: [(measure name, handle)] of cases taken where the case cannot be told apart
    for m in R["measures"]:
        if fo.norm(m.get("counted_on")) != "cases":
            continue
        h, name, at = m.get("handle"), S.measure(m.get("handle")), fo.norm(m.get("counted_at"))
        for sid, s in never.items():
            nm = fo.norm(s.get("name"))
            if m.get("subject_id") == sid or (nm and re.search(rf"(?<!\w){re.escape(nm)}(?!\w)", at, re.I)):
                unknown_at.setdefault(sid, []).append((name, h))
        if fo.norm(m.get("taken_from")) != "metric":
            continue
        asks = [q for q in (x.strip() for x in (m.get("receipt_question") or "").split(";")) if q in PER_CASE]
        if asks:
            fails.append((f"{name} is taken from a metric and answers “{'”, “'.join(question(q) for q in asks)}”, "
                          "which needs each case; a metric cannot say which cases",
                          f"measures.csv {h}: taken_from metric with receipt_question {'; '.join(asks)}"))
        elif not ONCE.search(m.get("counted_how") or ""):
            notes.append((f"{name} is of cases, taken from a metric: say why each increment is one case. A metric "
                          "cannot say which cases, so it cannot show the oldest or list them",
                          f"measures.csv {h}: counted_on cases, taken_from metric, and counted_how gives no "
                          "once-per-case basis"))
    for sid, ms in reversed(list(unknown_at.items())):  # once per part, however many measures
        one = len(ms) == 1
        what = ms[0][0] if one else f"{len(ms)} measures of cases ({', '.join(n for n, _ in ms)})"
        fails.insert(0, (f"{what} {'is of cases, and is' if one else 'are'} taken at {S.part(sid)}, which never "
                         f"holds the case's own identifier: take {'it' if one else 'them'} where the case is known, "
                         f"or say {'it is' if one else 'they are'} of something else",
                         f"measures.csv {', '.join(h for _, h in ms)}: counted_on cases at {sid} "
                         f"({never[sid].get('name')}), whose carries_case_id is no"))
    return fails, notes


def owed_expectations(R, flow_id, picked):
    """The expectations rule 2 asks of: the flow's whole-flow ones, and those of a picked stage."""
    return [e for e in vq.expectations({"R": R}, flow=flow_id) if not e.get("stage") or e["stage"] in picked]


def expectation_items(R, flow_id, picked, S):
    """Rule 2, the expectation chain (MEASURES-STEPS.md Step 9, mechanism 2), through view_questions: each expectation of the
    flow (whole-flow, or of a picked stage) is answered by a business measure naming it, or gapped with a reason."""
    out = []
    mine = vq.expectations({"R": R}, flow=flow_id)
    if not any(not e.get("stage") for e in mine):
        out.append(("no expectation is recorded of the whole flow: write what its customer counts on from it",
                    f"expectations.csv: no row of flow {flow_id} with `stage` blank"))
    for st in sorted(picked):
        if not any(e.get("stage") == st for e in mine):
            out.append((f"no expectation is recorded of the stage {S.stage.get(st, st)}: write what a party counts "
                        "on from it", f"expectations.csv: no row of stage {st}"))
    for e in owed_expectations(R, flow_id, picked):
        i = e.get("expectation_id", "")
        state, _ = vq.status({"R": R}, INDICATOR, i)
        if state == "empty":
            out.append((f"{S.expectation(i)} has no business measure showing whether it is met, and no reason why "
                        "none",
                        f"expectations.csv {i}: no business health or business impact measure names it in "
                        f"`expectation` (without a `defect`), and no measure-gaps.csv row {i}, {INDICATOR} stands"))
    return out


def kind_items(R, S):
    """A measure-gaps.csv row that says why and where from, whose kind is not one of fo.GAP_KINDS."""
    out = []
    for g in R["measure-gaps"]:
        if not (fo.norm(g.get("why")) and fo.norm(g.get("source"))):
            continue
        kind = fo.norm(g.get("kind")).lower()
        if kind not in fo.GAP_KINDS:
            el, q = fo.norm(g.get("element")), fo.norm(g.get("question"))
            out.append((f"the reason recorded for {S.element(el)}, “{question(q)}”, is of kind "
                        f"“{g.get('kind') or 'none'}”, not one of {', '.join(fo.GAP_KINDS)}",
                        f"measure-gaps.csv {el}, {q}: kind {g.get('kind') or 'blank'!r} is not one of "
                        f"{', '.join(fo.GAP_KINDS)}"))
    return out


def list_items(R, S):
    layers = {"method": {"layers": cv.read_csv(cv.METHOD / "layers.csv")}}
    forms = {f.get("form") for f in R.get("measure-forms", [])}
    out = []
    for m in R["measures"]:
        h, name = m.get("handle"), S.measure(m.get("handle"))
        if not cv.layer_of(layers, m.get("layer")):
            out.append((f"{name}: its layer “{m.get('layer') or 'none'}” is not one of the layers",
                        f"measures.csv {h}: layer {m.get('layer')!r} is not in method/layers.csv"))
        form = fo.norm(m.get("form"))
        if not form:
            out.append((f"{name} does not say its form, the kind of signal it is (a setting the part runs with is "
                        "one too: configuration)", f"measures.csv {h}: no form"))
        elif form not in forms:
            out.append((f"{name}: its form “{form}” is not one of the forms (each question a part is asked "
                        "has a form of its own)", f"measures.csv {h}: form {form!r} is not in method/measure-forms.csv"))
        kind = fo.norm(m.get("taken_from"))
        if not kind:
            out.append((f"{name} does not say the kind of record it is taken from, one of {', '.join(TAKEN_FROM)}",
                        f"measures.csv {h}: no taken_from"))
        elif kind not in TAKEN_FROM:
            out.append((f"{name}: the kind of record it is taken from, “{kind}”, is not one of "
                        f"{', '.join(TAKEN_FROM)}", f"measures.csv {h}: taken_from {kind!r} is not in the list"))
    return out + kind_items(R, S)


def for_flow_items(R, S):
    """Each measure that does not say which flow it was proposed for."""
    return [(f"{S.measure(m['handle'])} does not say which flow it was proposed for",
             f"measures.csv {m['handle']}: for_flow is empty") for m in R["measures"]
            if (m.get("handle") or "").strip() and not (m.get("for_flow") or "").strip()]


def unpicked_items(R, flow_id, picked, S):
    stages = {s["stage"]: s.get("name") or s["stage"] for s in R["stages"] if s["flow"] == flow_id}
    stage_of = {s["step"]: s["stage"] for s in R["steps"]}
    out = []
    for m in R["measures"]:
        at = fo.norm(m.get("stage")) or stage_of.get(fo.norm(m.get("step")), "")
        if at in stages and at not in picked:
            out.append((f"{S.measure(m.get('handle'))} is on the stage {stages[at]}, which is mapped only",
                        f"measures.csv {m.get('handle')}: on {at}, a stage left mapped only"))
    return out


def produced_items(R, S):
    out = []
    for m in R["measures"]:
        h, name = m.get("handle"), S.measure(m.get("handle"))
        if m.get("exists") == "yes":
            if not cv.CITE.search(m.get("source_ref") or ""):
                out.append((f"{name} is produced today, and cites no line of code that produces it",
                            f"measures.csv {h}: exists yes and source_ref cites no line "
                            f"({fo.norm(m.get('source_ref'))[:80] or 'blank'!r})"))
            continue
        if fo.norm(m.get("defect")):
            out.append((f"{name} is only proposed, and says what it gets wrong; only a measure produced today can "
                        "get something wrong", f"measures.csv {h}: defect is set and exists is "
                        f"{m.get('exists') or 'blank'}"))
        if fo.norm(m.get("watched")) or fo.norm(m.get("watched_source")):
            out.append((f"{name} is only proposed, and says whether anything collects it; nothing can collect it yet",
                        f"measures.csv {h}: watched or watched_source is set and exists is "
                        f"{m.get('exists') or 'blank'}"))
    return out


def watched_items(R, S):
    out = []
    for m in R["measures"]:
        if m.get("exists") != "yes":
            continue  # rule 7's
        name, w = S.measure(m["handle"]), fo.norm(m.get("watched"))
        got = fo.watched_failures(m)
        for e in got:
            plain = (f"{name}: whether anything collects it is given as “{w or 'nothing'}”, not one of "
                     f"{', '.join(fo.WATCHED)}" if "is not one of" in e else
                     f"{name} says whether anything collects it ({w}) without citing what was read to know" if
                     "with no watched_source" in e else
                     f"{name} is collected only if configured, and does not cite the setting that decides it" if
                     "cites no setting" in e else
                     f"{name}: whether anything collects it is given as unknown, while the setting that decides it "
                     "was read: say yes, no, only if configured or development only" if "setting read" in e else
                     f"{name} says it is collected ({w}) while no inventory could be reached; only unknown may rest "
                     "on that" if fo.NO_INVENTORY in e else
                     f"{name}: whether anything collects it needs fixing (run with --detail)")
            out.append((plain, e))
        src = fo.norm(m.get("watched_source"))
        if not got and src and src == fo.norm(m.get("source_ref")):
            out.append((f"{name}: what collects it is cited as the line that produces it; cite what collects it "
                        "(the scrape, collector or dashboard configuration read)",
                        f"measures.csv {m['handle']}: watched_source is the row's own source_ref"))
    return out


INSTRUMENTED = ("instrumented_kind", "instrumented_signature", "exporter_name", "taken_at")
OUTSIDE = "another organisation's record"
INSTRUMENTED_KINDS = ("code", "built in")
EXPORTED = ("yes", "only if configured", "development only")
SIGNATURE_MAX = 60


def instrumented_items(R, S):
    """What shows each measure's data and what would send it on: a register without the three columns fails once,
    naming them; otherwise each row is held to its own exists and watched (MEASURES-STEPS.md, "What shows the data")."""
    have = set(R["measures"][0]) if R["measures"] else set()
    if R["measures"] and not all(c in have for c in INSTRUMENTED):
        miss = [c for c in INSTRUMENTED if c not in have]
        return [("The measures do not say what shows their data or what would send it on: add "
                 f"{', '.join(miss)} and fill each row from its own citation",
                 f"measures.csv has no {', '.join(miss)} column: add them and fill each row from its own citation "
                 "(source_ref, counted_at, watched_source); nothing is walked again")]
    out = []
    components = {s["subject_id"] for s in R["subjects"] if fo.norm(s.get("level")) == "component"}
    for m in R["measures"]:
        name, h = S.measure(m["handle"]), m["handle"]
        kind, sig, exp, at = (fo.norm(m.get(c)) for c in INSTRUMENTED)
        if at and at not in components:
            out.append((f"{name} says its data comes from something that is not one of the application's components",
                        f"measures.csv {h}: taken_at is {at}, not a component in subjects.csv"))
        elif not at and m.get("exists") == "yes" and fo.norm(m.get("taken_from")) != OUTSIDE:
            out.append((f"{name} is produced today but does not say which component its data comes from",
                        f"measures.csv {h}: exists is yes with no taken_at"))
        if m.get("exists") == "yes":
            if not kind or not sig:
                out.append((f"{name} is produced today but does not say what shows its data",
                            f"measures.csv {h}: exists is yes with no instrumented_kind or instrumented_signature"))
            elif kind not in INSTRUMENTED_KINDS:
                out.append((f"{name}: what produces its data is given as “{kind}”, not code or built in",
                            f"measures.csv {h}: instrumented_kind is {kind}, not one of {', '.join(INSTRUMENTED_KINDS)}"))
            elif len(sig) > SIGNATURE_MAX:
                out.append((f"{name}: what shows its data is written as a sentence; say it in a few words",
                            f"measures.csv {h}: instrumented_signature is longer than {SIGNATURE_MAX} characters"))
        elif kind or sig:
            out.append((f"{name} is not produced today but says what shows its data",
                        f"measures.csv {h}: instrumented_kind or instrumented_signature is set and exists is not yes"))
        w = fo.norm(m.get("watched"))
        if m.get("exists") != "yes" or fo.watched_failures(m):
            continue  # whether anything collects it is wrong already, and said so above (rules 7 and 8)
        if w in EXPORTED and not exp:
            out.append((f"{name} says something would send its data on ({w}) without naming it",
                        f"measures.csv {h}: watched is {w} with no exporter_name"))
        elif w not in EXPORTED and exp:
            out.append((f"{name} names what would send its data on, while nothing does ({w or 'not said'})",
                        f"measures.csv {h}: exporter_name is set and watched is {w or 'blank'}"))
    return out


def place_items(R, S):
    out = []
    for m in R["measures"]:
        name = S.measure(m["handle"])
        for e in fo.counted_at_failures(m, R.get("products", ())):
            hit = re.search(r"counted_at names (.*?), a name only the code knows", e)
            out.append(((f"{name} names its place as {hit.group(1)}, a name only the code knows: use the plain name "
                         "a reader knows (the table and its database, the log and the service that writes it, or the "
                         "system whose own status it is)") if hit else
                        f"{name} cites the code but does not name, in plain words, the place it is taken at", e))
    for e in fo.same_place_failures(R["measures"]):
        m = re.match(r"measures\.csv (.*?): the same counted_at \((.*?)\) and", e)
        hs = m.group(1).split(", ") if m else []
        out.append((f"{S.measures(hs)} are taken at the same place ({m.group(2) if m else 'one place'}), and disagree "
                    "on whether it is produced today", e))
    return out


def id_items(reg):
    return [(f"{check_map.THING.get(t, 'a recorded row')} "
             f"{' and '.join(sorted({check_map.said_row(t, r) for r in rs}))}, two that share one name",
             f"{t}.csv: {c} {v} used twice") for t, c, v, rs in go.reused(reg)]


def inspect(reg, flow_id, picked):
    """[{rule, n, half, title, passed, items, said, note_items, notes}] in RULES order: `items` the technical messages,
    `said` the same in plain words, one for one; `note_items` and `notes` the same for what is to look at, not a
    failure."""
    picked = set(picked)
    with contextlib.redirect_stdout(io.StringIO()):  # the page builder prints while it builds a stage
        R = fo.load(reg)
        rec, _, receipt_err, _ = fo.receipt_failures(R, flow_id, measured=picked)
    S = Said(R)
    rec_by = {f"receipt: {r['element']} ({r['what']}), {r['question']}:": r for r in rec}
    found = {
        "receipt": [(receipt_item(S, rec_by, e), e) for e in receipt_err
                    if not any(k.match(e) for k in KIND_ERRORS)],
        "expectations": expectation_items(R, flow_id, picked, S),
        "expectation-ties": [(ties_item(S, e), e) for e in fo.expectation_failures(R, flow_id)]
                            + cited_expectation_items(R, S),
        "lists": list_items(R, S),
        "unpicked": unpicked_items(R, flow_id, picked, S),
        "for-flow": for_flow_items(R, S),
        "produced": produced_items(R, S),
        "watched": watched_items(R, S) + instrumented_items(R, S),
        "places": place_items(R, S) + alike_items(R, S),
        "ids": id_items(reg),
    }
    found["cases"], noted = cases_items(R, S)
    notes = {"cases": noted}
    return [{"rule": r, "n": n, "half": h, "title": t, "passed": not found[r],
             "items": [d for _, d in found[r]], "said": [p for p, _ in found[r]],
             "note_items": [d for _, d in notes.get(r, [])], "notes": [p for p, _ in notes.get(r, [])]}
            for r, n, h, t in RULES]


def said(results, detail=False, for_person=False):
    """The inspection as the person reads it at the measures review; with `detail`, the technical lines under each;
    `for_person`, inside the review message, without the line telling a session how to see them."""
    failed = sum(not r["passed"] for r in results)
    lines = [f"**Measures inspection.** {len(results)} rules checked: {len(results) - failed} pass, {failed} "
             f"fail{'s' if failed == 1 else ''}. It checks the measures' shape, not whether they are right about the "
             "system."]
    for half, heading in HALVES:
        lines.append(f"\n*{heading}*")
        for r in (r for r in results if r["half"] == half):
            text = "passes" if r["passed"] else f"fails on {'; '.join(r['said'])}"
            if r.get("notes"):
                text += f"{',' if r['passed'] else ';'} with {len(r['notes'])} to look at: {'; '.join(r['notes'])}"
            note, tech = NOTES.get(r["rule"], ("", ""))
            lines.append(f"- {r['n']}. {r['title']}: {text}." + (f" ({note}.)" if note else ""))
            if detail:
                lines.append(f"  - How: {tech}.")
                lines += [f"  - {i}" for i in r["items"]]
                lines += [f"  - note: {i}" for i in r.get("note_items", [])]
    lines.append("\n- Not checked yet: " + "; ".join(NOT_YET) + ".")
    if not detail and not for_person:
        lines.append("- For the columns and checks behind each line, run it with --detail.")
    return "\n".join(lines)


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    detail = "--detail" in argv
    argv = [a for a in argv if a != "--detail"]
    usage = __doc__.splitlines()[3].strip()
    if len(argv) < 3:
        print(usage)
        return 2
    reg, flow_id, picked = argv[0], argv[1], picked_stages(argv[2:])
    with contextlib.redirect_stdout(io.StringIO()):
        R = fo.load(reg)
    flows = [f["flow_id"] for f in R["flows"]]
    if flow_id not in flows:
        print(f"{flow_id} is not a flow of this register; its flows: {', '.join(flows)}")
        return 2
    mine = [s["stage"] for s in R["stages"] if s["flow"] == flow_id]
    wrong = [s for s in picked if s not in mine]
    if not picked or wrong:
        print(f"{', '.join(wrong) or 'no stage'}: name the picked stages of flow {flow_id}, of {', '.join(mine)}")
        return 2
    print(said(inspect(reg, flow_id, picked), detail))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
