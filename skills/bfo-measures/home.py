"""The home screen: index.html in the register folder, drawn from the run's depth.json.

Usage: python home.py <register folder>

One row per flow, one dot per milestone toward supported in production: Identified, Mapped, Measures defined,
Instrumented, Dashboards built, Alerts defined, Runbooks written, Team prepared. The five the kit works on show their
status in depth.json (`not started`, `draft`, `reviewed`); the other three are carried out by other teams, and
read "not started" (Instrumented carries a count read from the code at design time). A dot opens a
drop-down under its flow with what is there to review at that milestone and links to the kit's own pages for it,
each in the same tab. Reasons stay in depth.json and are never drawn; the one recommendation drawn is the
recommended flow at the go, marked. Nothing is ticked for the person, except a stage's depth already recorded.

While a choice waits on the person at the go or at the pick (depth.json's open choice), the page carries the form
for it, as a listener serving the page reads it: a hidden `choice_id`, one free-text `words`, and per item a
checkbox group named by the item's key whose values are the milestones ticked. At the go, which flow is mapped
first, those ticks, the words and Done sit at the top of the page, one row per flow found, seen without opening a
dot; while any choice is open, the line under the flows says the run is waiting on it. The review of the alerts is not
taken from a page, so it has no form. Every other tick is a topic to talk about with Claude, named
`talk:<milestone>:<item key>` with its label as the value, and each drop-down's words `talk-words:<milestone>`; any
Done sends them all, and the page reloads once the run has redrawn it. The page opens with "What do you want to
do?", always there whatever is open: the person's words to Claude (`talk-words:Home`), a topic like the others, kept for the tab by
its empty `data-flow`, as each drop-down's words box is kept by its flow.

Exit 0 written, 2 refused. Python standard library only."""
import hashlib
import html
import json
import os
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import capability_views as cv  # noqa: E402
import depth  # noqa: E402
import page_style as ps  # noqa: E402
import run_lock  # noqa: E402
import step_sequence as ss  # noqa: E402

FILE = "index.html"
TEMPLATE = HERE / "home.template.html"
MAP_FILE = "views.html"
MADE_FILE = "how-this-map-was-made.html"
E = html.escape

COLS = [
    ("Identified", "We know the flow exists", ""),
    ("Mapped", "Its stages, steps and parts are known", ""),
    ("Measures defined", "What “working” means, and what to count", ""),
    ("Instrumented", "The application produces them and sends them to monitoring", ""),
    ("Dashboards built", "The views exist", ""),
    ("Alerts defined", "What should raise an alert", ""),
    ("Runbooks written", "What to do when each alert fires", ""),
    ("Team prepared", "The people have practised on it", ""),
]
IDENT, MAPPED, MEAS, INSTR, DASH, ALERTS, RUNBOOKS, TEAM = range(8)
OUTSIDE = (INSTR, DASH, TEAM)
KEY = {MEAS: "measures", ALERTS: "alerts", RUNBOOKS: "runbooks"}
# What fills a dot. Runbooks are drafted and never reviewed, so they fill once drafted, like the first three. Alerts
# fill once the review of the proposed alerts is recorded. The three other teams carry out read "Nothing recorded
# yet." until a later stage reads their tools; the count of measures sent to monitoring is read from the code.
FILLED_WHEN = {IDENT: ("draft", "reviewed"), MAPPED: ("draft", "reviewed"),
               MEAS: ("draft", "reviewed", depth.REVIEWED_OPEN),
               ALERTS: ("reviewed", depth.REVIEWED_OPEN), RUNBOOKS: ("draft", "reviewed")}

TALK = "Tick what you want to talk about with Claude · say what in your words"
WORDS_ONLY = "Your words go to Claude"
AT_THE_GO = "Tick the flow to map in the next run · one flow per run"
FIRST_TASK = "Choose the flow to map first"  # depth.py's open choice at the go: picked at the top of the page
NEXT_TASK = "Choose the next flow to map"  # depth.py's (go.NEXT_TASK) once a flow is finished: offered, never awaited
AT_THE_FIRST = "Tick the flow to map first · one flow per run · anything else, in your words"
AT_THE_PICK = ("Tick what gets more work · say what in your words · ticking a milestone brings the ones "
               "before it")

KIND = {"does not apply": "does not apply here", "counted by": "counted by another measure",
        "no record": "the application keeps no record to count it", "not read": "not looked at yet"}
STAGE_Q = {"in the stage": "How many cases are in this stage now", "oldest's age": "How long the oldest case has waited",
           "time through": "How long cases take through the stage", "past the time limit": "How many are past the time limit"}
MAP_Q = {"stage: a case enters": "how a case enters", "stage: expected outcomes": "the outcome expected",
         "stage: other outcomes": "what else can happen", "stage: cannot be undone": "what cannot be undone",
         "stage: at stake": "what is at stake", "stage: expected by each party": "what each party expects",
         "stage: alerts": "its alerts",
         "step: moves": "its moves in the code", "step: trigger": "what starts it",
         "step: right outcome": "its right outcome", "step: if it does not happen": "what happens if it does not",
         "step: timeouts": "its time limits", "step: interactions": "the calls between its parts, in order",
         "step: where each part sits": "which parts carry it"}
LEVEL = {"flow": 0, "stage": 1, "step": 2, "part": 3}
PART = "A part is a piece of the system a step runs on: a service, a data store or an outside system."


def plain(text):
    """A register cell without its citations in brackets."""
    return re.sub(r"\s*\([^()]*(?:\([^()]*\)[^()]*)*\)", "", text or "").strip()


def marked(text):
    """A register cell without its citations, a leading `proposed:` read as the "(proposed)" mark after it, as the
    stage's own page marks a drafted value (stage_flow_views.headline)."""
    body, prop = ss.unproposed(plain(text or ""))
    body = body.strip()
    return body + (" (proposed)" if prop and body else "")


def short(text):
    """A stage's entry or exit as the states it names: each without its explanation after a colon, its `implicit:`
    (no system records the state) or its move ids, in any bracket that holds one; a `proposed:` one marked
    "(proposed)"; several ways out joined by "or"."""
    t, whole = ss.unproposed(re.sub(r"\s*\([^()]*\bL\d\d\b[^()]*\)", "", text or ""))
    # a cell drafted as a whole marks every way out in it; otherwise each way out carries its own mark
    split = r"[;,]\s*or\s+" if whole else r"[;,]\s*or\s+(?=(?:implicit|proposed)\s*:)"
    alts = []
    for a in re.split(split, t, flags=re.I):
        body, prop = ss.unproposed(re.sub(r"^\s*implicit\s*:\s*", "", a, flags=re.I))
        body = re.sub(r"^\s*implicit\s*:\s*", "", body, flags=re.I).split(":")[0].strip()
        body = "the start" if body.lower() == "the starting event" else body
        if body:
            alts.append(body + (" (proposed)" if prop or whole else ""))
    return ("; or " if any("," in a for a in alts) else ", or ").join(alts)


def nn(n, w):
    return f"{n} {w}{'' if n == 1 else 's'}"


def about(f):
    """(one case, starts, ends) in a few words each. Ends keeps the ending the party waits for and the one where they
    definitively do not, as a register writes them: "… Or definitively not: …", or "Main: … Does not: …".
    A drafted value (`proposed:`, whole or per ending) keeps its words before the cut and reads "(proposed)" after."""
    def lead(text):
        body, prop = ss.unproposed(plain(text))
        body = body.split(":")[0].strip()
        return body + (" (proposed)" if prop and body else "")

    ends, whole = ss.unproposed(plain(f.get("ends")))
    keep = []
    for i, x in enumerate(ends.split(". ")):
        x = x.strip().rstrip(".")
        if i == 0:
            x, prop = ss.unproposed(re.sub(r"^Main:\s*", "", x))
            x = x[:1].upper() + x[1:]
        elif x.startswith("Or "):
            head, sep, rest = x.partition(": ")
            rest, prop = ss.unproposed(rest)
            x = head + sep + rest
        elif x.startswith("Does not:"):
            rest, prop = ss.unproposed(x[len("Does not:"):])
            x = "Or it does not: " + rest.strip()
        else:
            continue
        if x.strip():
            keep.append(x + (" (proposed)" if prop or whole else ""))
    return lead(f.get("case")), lead(f.get("starts")), ". ".join(keep)


def sub_line(f):
    case, starts, ends = about(f)
    if not case:
        return f.get("what") or ""
    return " · ".join([case, "from: " + starts.lower(), "to: " + ends[:1].lower() + ends[1:]])


# ---------------------------------------------------------------- Instrumented: where each measure is counted

INSTR_STATES = [
    ("code", "Not produced: the application has to be changed"),
    ("kept", "Data stored, not yet counted"),
    ("uncollected", "Produced, but nothing collects it"),
    ("unknown", "Produced; whether anything collects it is not known"),
    ("wrong", "Produced, but it counts wrong"),
    ("outside", "Comes from outside the application"),
    ("seen", "Produced and sent to monitoring"),
]


STORED = ("the case's own record", "a message log kept with the state")


def counted_at_stand_in(reg):
    """{handle: {state, place, takes}}: where each measure is counted and what it needs, guessed from measures.csv's
    exists, watched, defect, taken_from and counted_how. depth.json does not carry this yet; swap this for its field
    when it does."""
    rows = cv.read_csv(pathlib.Path(reg) / "measures.csv") if (pathlib.Path(reg) / "measures.csv").is_file() else []
    subj = cv.read_csv(pathlib.Path(reg) / "subjects.csv") if (pathlib.Path(reg) / "subjects.csv").is_file() else []
    names = {s.get("subject_id"): s.get("name") for s in subj}
    out = {}
    for m in rows:
        if not m.get("handle"):
            continue
        src, w, how = m.get("taken_from", ""), m.get("watched", ""), m.get("counted_how", "")
        who = names.get(m.get("subject_id")) or "the application"
        if src in STORED and w == "no" and not m.get("defect"):
            st = "kept"  # stored, and nothing counts it: only a query and its collection are missing
        elif m.get("exists") == "yes":
            st = "wrong" if m.get("defect") else "seen" if w == "yes" else "unknown" if w in ("", "unknown") else "uncollected"
        elif src in STORED:
            st = "kept"
        elif src in ("metric", "log or event record", "trace", "client-side instrumentation"):
            st = "code"
        else:
            st = "outside"
        one = re.split(r";\s|; read with|; run in", how)[0].strip().rstrip(".")
        one, drafted = ss.unproposed(one)  # "proposed: a log line ..." reads "a log line ... (proposed)"
        one = one.strip() + (" (proposed)" if drafted and one.strip() else "")
        one = re.sub(r"^as M\d+ with", "the same count as the measure above, with", one)
        one = one if len(one) <= 110 else one[:107].rsplit(" ", 1)[0] + " …"
        place = {"the case's own record": "the application's database",  # the kind alone: never a code name
                 "a message log kept with the state": "the application's database",
                 "log or event record": f"{who} log", "trace": f"{who} traces", "metric": f"{who} metric",
                 "external probe": f"a health check run against {who}", "the edge": "the gateway in front of the application",
                 "client-side instrumentation": f"the client app ({who})",
                 "platform lifecycle events": "the hosting platform's container events",
                 "configuration": f"{who}'s settings",
                 "another organisation's record": "another organisation's records (no record in this application)",
                 }.get(src, src or "not recorded")
        place = (m.get("counted_at") or "").strip() or place  # the register's own name for it, where it has one
        has = "Exists: " + one + "."
        takes = {"seen": has + " Sent to monitoring.",
                 "wrong": "Needs: the developers to fix it. Counts wrong: " + plain(m.get("defect", "")) + " " + has,
                 "uncollected": "Needs: monitoring to collect it; no change to the application. " + has,
                 "unknown": "Needs: find out whether monitoring collects it. " + has,
                 "kept": "Needs: a query on that table, collected by monitoring; no change to the application. "
                         "Exists: the data, in " + place + ".",
                 "code": "Needs: the developers to add it to the application. Would count: " + one + ".",
                 "outside": "Needs: setting up outside the application, by whoever runs that. Would count: " + one + "."}[st]
        if src == "another organisation's record":
            takes = "Needs: that organisation's records, if they can be had. Would count: " + one + "."
        out[m["handle"]] = {"state": st, "place": place, "takes": takes}
    return out


# ---------------------------------------------------------------- Measures defined: whether each can be counted today

# The kind of source, in the reader's words, from the kind of record the measure is counted from (taken_from)
SOURCE_KIND = {"the case's own record": "Database", "a message log kept with the state": "Database",
               "log or event record": "Log", "metric": "Metric", "trace": "Trace", "external probe": "Probe",
               "platform lifecycle events": "Platform event", "configuration": "Configuration", "the edge": "Gateway",
               "client-side instrumentation": "Client app", "another organisation's record": "External party"}
# Exporter, from `watched` (MEASURES-STEPS.md, "A measure can be emitted and never collected"): (label, class)
EXPORTER = {"only if configured": ("Off by default", "st-off"), "development only": ("Development only", "st-off"),
            "in the app only": ("In the app only", "st-off"), "no": ("Not found", "st-nf"),
            "unknown": ("Not known", "st-nk")}
OFF_QUALIFIER = "sends once its endpoint is set"
NA = "n/a"
OUTSIDE_APP = "Outside the application"
MEASURE_DEFS = (
    '<div class="defs" hidden>'
    '<div><h4>Levels</h4><div class="ltree"><div class="ln"><b>Flow</b><span>measures of the flow as a whole; shown with every stage</span></div>'
    '<div class="lk1"><div class="ln"><b>Stage</b><span>one part of a flow</span></div><div class="lk2">'
    '<div class="ln"><b>Step</b><span>one thing that happens in a stage</span></div>'
    '<div class="ln"><b>Component</b><span>does the work of one or more steps; can serve several</span></div>'
    '</div></div></div></div>'
    '<div><h4>Layer</h4><div class="kv"><span class="badge l-bh">Business health</span><span>cases moving: how many, how '
    'long</span><span class="badge l-bi">Business impact</span><span>cases that went wrong for the customer or the '
    'business</span><span class="badge l-ap">Application</span><span>a service\'s requests, errors and time to '
    'answer</span><span class="badge l-te">Technology</span><span>what the services run on</span></div></div>'
    '<div><h4>From and Source</h4><div class="kv"><b>From</b><span>the component the data comes from; empty when it is '
    'the row\'s own component</span><b>Outside the application</b><span>the data is kept by another organisation</span>'
    '<b>Source</b><span>the kind of record counted: log, trace, metric, database, probe, platform event</span>'
    '<b>External party</b><span>another organisation\'s record</span></div></div>'
    '<div><h4>In code and Exporter</h4><div class="kv"><b>Found</b><span>the code writes the record</span>'
    '<b>Built in</b><span>the product provides it</span><b>Not found</b><span>In code: not in the code that was read. '
    'Exporter: no configuration sends it</span><b>Off by default</b><span>the exporter sends once its endpoint is set'
    '</span><b>Development only</b><span>collected only by a developer\'s tool</span><b>In the app only</b><span>shown '
    'in the application, sent nowhere</span><b>Not known</b><span>the configuration that would say was not within '
    'reach</span><b>n/a</b><span>does not apply: the data is outside the application</span><b>Nothing records it</b><span>the application keeps no record this question could be counted from</span><b>Not looked at yet</b><span>the code that would answer it was not read in this run</span></div></div></div>')
BCLS = {"business health": "b-bh", "business impact": "b-bi", "application": "b-ap", "technology": "b-te"}
LCLS = {"business health": "l-bh", "business impact": "l-bi", "application": "l-ap", "technology": "l-te"}
QTYPE = {"in the stage": "Cases in the stage now", "oldest's age": "Age of the oldest case",
         "time through": "Time through the stage", "past the time limit": "Cases past the time limit",
         "did it happen": "Whether it happens", "was its outcome right": "Whether it comes out right"}


def shown(name, comp):
    """A component's measure whose name starts with the component's own name shows without it."""
    if comp and re.match(re.escape(comp) + r"\s+", name or "", re.I):
        rest = re.sub("^" + re.escape(comp) + r"\s+", "", name, flags=re.I)
        return rest[:1].upper() + rest[1:]
    return name


def code_cell(v):
    if v == "Not found":
        return '<span class="chip nf">Not found</span>'
    return f'<span class="q">{E(v)}</span>' if v == NA else f'<span class="ok">{E(v)}</span>'


def exporter_cell(v):
    if v == "Off by default":
        return '<span class="chip off">Off by default</span>'
    if v == "Not found":
        return '<span class="chip nf">Not found</span>'
    return f'<span class="q">{E(v)}</span>' if v in ("Not known", NA, "Development only", "In the app only") else \
        f'<span class="ok">{E(v)}</span>'


def ref_html(s, code=True):
    """A long reference shows its first part, cut only where the register separates parts ("; "), with "more"."""
    s = re.sub(r"^\s*proposed\s*;\s*", "", s or "", flags=re.I)  # an older register's bare mark is no reference
    if not s:
        return ""
    head = re.split(r";\s+", s)[0]
    rest = s[len(head):].lstrip("; ")
    w = (lambda t: f"<code>{E(t)}</code>") if code else E
    if not rest:
        return w(s)
    return (f'<span data-short>{w(head)}</span><span data-full hidden>{w(s)}</span> '
            '<button type="button" class="more" data-more>more</button>')


def measure_detail(c):
    """An opened row: the measure, and whether it can be counted today, one label per value."""
    absent = c["code"][0] in ("Not found", NA)
    record = re.sub(r"^not in the code,\s*", "", c["source_name"] or "", flags=re.I)
    e = c["exporter"][0]
    exp = (f'{e}: {c["exporter_name"]}' if c["exporter_name"] else e) if e in ("Off by default", "Not found") else \
        (c["exporter_name"] or e)
    left = [("What it answers", E(c["question"])), ("How it is counted", E(c["how"]))]
    right = [("Record", E(record)), ("Nearest code" if absent else "Code", ref_html(c["code_ref"])),
             ("Exporter", "" if e == NA else E(exp)), ("Set up in", ref_html(c["exporter_ref"], code=False))]
    dl = lambda xs: "<dl>" + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in xs if b) + "</dl>"
    return (f'<div class="evb"><section><h5>The measure</h5>{dl(left)}</section>'
            f'<section><h5>Can it be counted today</h5>{dl(right)}</section></div>')


def drafted(v):
    """A value as the person reads it: a leading `proposed:` mark said as "(proposed)" after it."""
    t, d = ss.unproposed((v or "").strip())
    t = t.strip()
    return t + (" (proposed)" if d and t else "")


def cited(v):
    """A citation as the person reads it: a `proposed:` mark inside it said as "proposed," (older registers)."""
    t = re.sub(r"\bproposed\s*:\s*", "proposed, ", drafted(v), flags=re.I)
    return "" if t.strip(" .,()").lower() == "proposed" else t  # a bare mark cites nothing


def measure_cells(reg):
    """{handle: the cells of the Measures defined screen}, read from measures.csv's own columns: nothing guessed.
    In code and Exporter follow exists, instrumented_kind and watched as MEASURES-STEPS.md defines them."""
    reg = pathlib.Path(reg)
    rows = cv.read_csv(reg / "measures.csv") if (reg / "measures.csv").is_file() else []
    names = {sid: v[0] for sid, v in part_info(reg).items()}
    out = {}
    for m in rows:
        if not m.get("handle"):
            continue
        tf, at = m.get("taken_from", ""), drafted(m.get("counted_at"))
        src_at = (m.get("taken_at") or "").strip()
        came = names.get(src_at) or (OUTSIDE_APP if tf == "another organisation's record" else NA)
        if at.lower().startswith("not in the code:"):
            at = "not in the code, " + at.split(":", 1)[1].split(";")[0].strip()
        if m.get("exists") == "yes":
            code = ("Built in", "st-yes") if m.get("instrumented_kind") == "built in" else ("Found", "st-yes")
        else:
            code = (NA, "muted") if tf == "another organisation's record" else ("Not found", "st-nf")
        w, name = (m.get("watched") or "").strip(), (m.get("exporter_name") or "").strip()
        exp = (name, "st-yes") if w == "yes" else EXPORTER.get(w, (NA, "muted"))
        said_exp = (f"{exp[0]}: {name}, {OFF_QUALIFIER}" if w == "only if configured" else
                    f"{exp[0]}: {name}" if w == "development only" and name else exp[0])
        sig = drafted(m.get("instrumented_signature"))
        out[m["handle"]] = {
            "source": SOURCE_KIND.get(tf, tf), "source_name": at, "code": code, "exporter": exp, "from": came,
            "found": sig if m.get("exists") == "yes" else "", "exporter_name": name if w in ("yes", "only if configured",
                                                                                         "development only") else "",
            "sends": OFF_QUALIFIER.replace("sends ", "") if w == "only if configured" else "",
            "said_code": f"{code[0]}: {sig}" if m.get("exists") == "yes" and sig else code[0],
            "said_exporter": said_exp, "code_ref": cited(m.get("source_ref")),
            "exporter_ref": cited(m.get("watched_source")), "how": drafted(m.get("counted_how")),
            "step": (m.get("step") or "").strip(), "subject": m.get("subject_id", ""),
            "question": drafted(m.get("question_it_answers")), "layer": m.get("layer", ""),
            "measure": drafted(m.get("measure"))}
    return out


def part_info(reg):
    """{subject_id: (name, part_kind, purpose without its trailing citation)} from subjects.csv."""
    reg = pathlib.Path(reg)
    rows = cv.read_csv(reg / "subjects.csv") if (reg / "subjects.csv").is_file() else []
    return {s.get("subject_id"): (drafted(s.get("name")), s.get("part_kind") or "",
                                  re.sub(r"\s*\([^()]*[:/][^()]*\)\s*$", "", drafted(s.get("purpose"))))
            for s in rows}


# ---------------------------------------------------------------- the pieces of a drop-down

def table(cols, trs):
    head = "".join(f"<th>{E(c)}</th>" for c in cols)
    body = "".join(f'<tr class="{E(cls)}">' + "".join(f"<td>{E(x)}</td>" for x in cells) + "</tr>" for cls, cells in trs)
    return f'<div class="tw"><table class="dt"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def secs(groups):
    out = []
    for title, items in groups:
        its = []
        for text, subs, more_title, more in items:
            s = "".join(f'<div class="sub"><span class="k">{E(k)}</span> {E(v)}</div>' for k, v in subs if v)
            m = (f"<details><summary>{E(more_title)}</summary><ul>" + "".join(f"<li>{E(z)}</li>" for z in more)
                 + "</ul></details>") if more else ""
            its.append(f'<div class="it"><div>{E(text)}</div>{s}{m}</div>')
        out.append(f'<div class="sec"><div class="st">{E(title)}</div>{"".join(its)}</div>')
    return "".join(out)


def note(text):
    return f'<div class="mute">{E(text)}</div>' if text else ""


def item(text, subs=(), more_title="", more=()):
    return (text, list(subs), more_title, list(more))


def level_rows(levels, cells_for, width, numbered=()):
    """Rows of a table read by level: the level's own row, then its items, or why there are none. Only the items of a
    level in `numbered`, which run in order, carry a number: a number on facts or on a set reads as a stage's."""
    trs = []
    for t, means, xs, empty in levels:
        trs.append(("blk lv", [t, "", means] + [""] * (width - 3)))
        if not xs:
            trs.append(("gap", ["", "", empty] + [""] * (width - 3)))
        n = 0
        for x in xs:
            if x.get("hole"):
                trs.append(("gap", ["", "", x["what"], x["hole"]] + [""] * (width - 4)))
            else:
                n += 1
                trs.append(("", ["", str(n) if t in numbered else ""] + cells_for(x)))
    return trs


def measure_what(r):
    """A receipt item, as the question it asks."""
    kind, _, name = (r.get("what") or "").partition(": ")
    q = r.get("question") or ""
    if kind == "stage":
        return STAGE_Q.get(q, q)
    if kind == "step":
        return {"did it happen": f"Whether “{name}” happens",
                "was its outcome right": f"Whether “{name}” comes out right"}.get(q, name)
    return "Health of " + re.sub(r"^(operation of |component: |system component: )", "", r.get("what") or "").replace(
        ", no operation named", "")


def gap_level(r):
    kind = (r.get("what") or "").partition(": ")[0]
    return 1 if kind == "stage" else 2 if kind == "step" else 3


def gap_why(r):
    return KIND.get(r.get("gap_kind"), r.get("gap_kind") or "not answered yet")


# ---------------------------------------------------------------- one flow

class Flow:
    def __init__(self, reg, d, i, f, counted):
        self.reg, self.d, self.i, self.f = reg, d, i, f
        self.stages = f.get("stages") or []
        self.mapped = bool(f.get("mapped") and self.stages)
        self.ms = {m["handle"]: m for m in (f.get("measures") or {}).get("items") or []}
        self.counted = counted
        self.mile = {m["milestone"]: m for m in f.get("milestones") or []}

    def status(self, p):
        return (self.mile.get(COLS[p][0]) or {}).get("status", depth.NOT_STARTED)

    def stage_measures(self, s):
        """The measures of a stage below the flow's own, by handle, once each."""
        return [self.ms[h] for h in (s.get("measures") or {}).get("handles") or []
                if h in self.ms and self.ms[h].get("level") != "flow"]

    def flow_measures(self):
        return [m for m in self.ms.values() if m.get("level") == "flow"]

    def sent(self, ms):
        return sum(1 for m in ms if (self.counted.get(m["handle"]) or {}).get("state") == "seen")

    # ---- the dots
    def dot(self, p):
        if p in OUTSIDE:
            if p == INSTR and self.mapped and self.ms:  # the count, read from the code; the dot never fills
                total, on = len(self.ms), self.sent(self.ms.values())
                return "", f"{on} of {nn(total, 'measure')}", ["sent to monitoring"]
            return "", depth.NOT_STARTED, []
        st = self.status(p)
        cls = "done" if st in FILLED_WHEN[p] else ""
        lst = []
        if p == MAPPED and self.mapped:
            steps = sum(len(s.get("steps") or []) for s in self.stages)
            parts = len({x.get("part") for s in self.stages for x in s.get("parts") or []})
            lst = [nn(len(self.stages), "stage"), nn(steps, "step"), nn(parts, "part")]
        elif p == MEAS and st != depth.NOT_STARTED:
            by = {k: sum(1 for m in self.ms.values() if m.get("level") == k) for k in LEVEL}
            lst = [nn(len(self.ms), "measure")] + [f"{by[k]} on the {k}{'' if k == 'flow' else 's'}" for k in LEVEL]
        elif p in (ALERTS, RUNBOOKS) and st != depth.NOT_STARTED:
            key = KEY[p]
            lst = [f"{(s.get(key) or {}).get('count', 0)} · {s.get('name')}" for s in self.stages]
        if p in (MEAS, ALERTS) and st != depth.NOT_STARTED:  # a draft its own check fails says so, wherever it shows
            n = (self.mile.get(COLS[p][0]) or {}).get("open_items", 0)  # each item once, however many stages find it
            at = [s.get("name") for s in self.stages if (s.get(KEY[p]) or {}).get("open_items")]
            lst += [f"{nn(n, 'open item')} · {', '.join(at)}"] if n else []
        return cls, st, lst

    # ---- the pages each drop-down links
    def pages(self, p):
        if not self.mapped:
            return []
        name = {s["stage"]: f"Stage {s.get('order')}: {s.get('name')}" for s in self.stages}

        def stage_of(rel):
            m = re.match(r"stage-([^/]+)/", rel)
            return name.get(m.group(1)) if m else None
        if p == MAPPED:
            got = [(rel, "The map of the flow") for rel in (self.mile.get("Mapped") or {}).get("pages") or []]
            got += [(f"flow-{self.f.get('flow')}/FLOW.html", "The flow’s page"), (MADE_FILE, "How this map was made")]
            got += [(f"stage-{s['stage']}/STAGE.html", name[s["stage"]] + ", its page") for s in self.stages]
        elif p in (MEAS, INSTR, ALERTS, RUNBOOKS):
            mile = COLS[MEAS if p == INSTR else p][0]
            word = {MEAS: "its measures", INSTR: "its measures", ALERTS: "its alerts", RUNBOOKS: "its runbook"}[p]
            got = [(rel, (stage_of(rel) or "The map of the flow") + ", " + word)
                   for rel in (self.mile.get(mile) or {}).get("pages") or []]
            if not got:
                got = [(MAP_FILE, "The map of the flow")]
        else:
            return []
        seen, out = set(), []
        for rel, label in got:
            if rel not in seen and (self.reg / rel).is_file():
                seen.add(rel)
                out.append((rel, label))
        return out

    # ---- the panes of a drop-down: {selection: html}, selection "-1" the flow, "k" a stage
    def panes(self, p):
        f = self.f
        if p == IDENT:
            case, starts, ends = about(f)
            it = item(f["what"]) if f.get("what") else item(case, [("Starts", starts), ("Ends", ends)])
            text = "" if self.mapped else (f.get("why_not_mapped") or "") + " Nothing more is known until a run maps it."
            return {"-1": secs([("What this flow is", [it])]) + note(text.strip())}
        if not self.mapped:
            return {"-1": note("Nothing here yet: the flow has not been mapped.")}
        if p in (DASH, TEAM):
            return {"-1": note(depth.NOT_STARTED.capitalize() + ".")}
        if p == MAPPED:
            return {k: self.map_pane(s) for k, s in self.choices()}
        if p == MEAS:
            return {"all": self.measure_pane(None, every=True), "flow": self.measure_pane(None),
                    **{k: self.measure_pane(s) for k, s in self.choices() if s}}
        if p == INSTR:
            return {k: self.instr_pane(s) for k, s in self.choices()}
        if p == ALERTS:
            return {k: self.alert_pane(s) for k, s in self.choices()}
        return {str(k): self.runbook_pane(s) for k, s in enumerate(self.stages)}

    def selected(self, s):
        """A pane's section headers, naming the flow and the stage selected: (flow, stage, step, part)."""
        flow = f"Flow {self.i + 1}, {self.f.get('name')}, as a whole"
        if not s:
            return (flow, "each stage: select one in the tree", "each step of a stage",
                    "each part doing a stage’s steps")
        st = f"Stage {s.get('order')}, {s.get('name')}"
        return flow, st + ", as a whole", "each step of " + st, "each part doing the steps of " + st

    def choices(self):
        return [("-1", None)] + [(str(k), s) for k, s in enumerate(self.stages)]

    def hole(self, h, who):
        """A question not answered: "Not known yet" only where nothing is said; a gap reads as its kind."""
        why = "not known yet" if h.get("state") == "empty" else (
            "the code keeps no record of it" if h.get("gap_kind") == "no record" else KIND.get(h.get("gap_kind"), h.get("gap_kind") or ""))
        return {"what": "↳ " + MAP_Q.get(h.get("question"), h.get("question") or ""), "hole": why[:1].upper() + why[1:],
                "who": who}

    def map_pane(self, s):
        case, starts, ends = about(self.f)
        flow = [{"item": a, "known": b} for a, b in (("One case", case), ("Starts", starts), ("Ends", ends),
                                                    ("Serves", marked(self.f.get("serves"))))]
        stage, steps, parts = [], [], []
        if s:
            # a question only measuring, alerting or the runbooks answer is the map's to ask only of a stage whose
            # recorded pick takes it that far: before any pick, and past a stage's pick, it is not asked here
            import view_questions as vq
            reach = depth.REACHES.get(s.get("recorded_depth") or "none", ())
            owed = {"measure": vq.MEASURE_ONLY, "alerting": vq.ALERTING_ONLY, "runbooks": vq.RUNBOOK_ONLY}
            later = {q for lv, qs in owed.items() if lv not in reach for q in qs}
            holes = [h for h in s.get("holes") or [] if h.get("question") not in later]
            stage = [{"item": "Enters", "known": short(s.get("entry"))}, {"item": "Leaves", "known": short(s.get("exit"))}]
            stage += [{"item": "Expected by " + marked(e.get("party")).lower(), "known": marked(e.get("expectation"))}
                      for e in s.get("expects") or []]
            stage += [self.hole(h, "") for h in holes if h.get("of") == "stage"]
            for x in s.get("steps") or []:
                right = marked(x.get("right_outcome"))
                steps.append({"item": x.get("name"), "known": "Right outcome: " + right if right else ""})
                steps += [self.hole(h, x.get("name")) for h in holes if h.get("of") == "step" and h.get("item") == x.get("name")]
            parts = [{"item": x.get("name"), "known": x.get("role")} for x in s.get("parts") or []]
        none = "Nothing known at this level"
        pick = "Shown when a stage is selected"
        hf, hs, hp, hpt = self.selected(s)
        levels = [("Flow", hf, flow, none), ("Stage", hs, stage, none if s else pick),
                  ("Step", hp, steps, none if s else pick), ("Part", hpt, parts, none if s else pick)]
        trs = level_rows(levels, lambda x: [x["item"], x["known"]], 4, numbered=("Step",))
        return (table(["Level", "", "Item", "What is known"], trs)
                + note("Mapped from one case traced through the code to each of its endings. A step or part the "
                       "trace missed would not show here."))

    def measure_groups(self, s):
        """[(level, pill, name, kind, place, [measure handles], [unmeasured items])] in the flow's order: the flow,
        then for a stage the stage, each step and each component it uses."""
        cells, parts = getattr(self, "cells", {}), getattr(self, "parts", {})
        fname = self.f.get("name") or ""
        gaps = lambda items, keep: [r for r in items or [] if r.get("state") != "measured" and keep(r)]
        out = [("Flow", "Flow", fname, "", [m["handle"] for m in self.flow_measures()],
                gaps((self.f.get("measures") or {}).get("flow_items"), lambda r: True))]
        if not s:
            return out
        items = (s.get("measures") or {}).get("items")
        ms = self.stage_measures(s)
        at = lambda lv: [m["handle"] for m in ms if LEVEL.get(m.get("level")) == lv]
        out.append(("Stage", f"Stage {s.get('order')}", s.get("name") or "", "", at(1),
                    gaps(items, lambda r: gap_level(r) == 1)))
        for x in s.get("steps") or []:
            k = str(x.get("step"))
            out.append(("Step", f"Step {k}", x.get("name") or "", "",
                        [h for h in at(2) if (cells.get(h) or {}).get("step") == k],
                        gaps(items, lambda r, k=k: gap_level(r) == 2 and str(r.get("element")) == k)))
        for x in s.get("parts") or []:
            pid = x.get("part")
            name, kind, _purpose = parts.get(pid, (x.get("name") or "", "", ""))
            out.append(("Part", "Component", name or x.get("name") or "", kind[:1].upper() + kind[1:],
                        [h for h in at(3) if (cells.get(h) or {}).get("subject") == pid],
                        gaps(items, lambda r, pid=pid: gap_level(r) == 3 and str(r.get("element")) == pid)))
        return out

    def all_groups(self):
        """Every measure of the flow once: end to end, then each stage with its steps, then each component once
        (a component serves several stages), its measures and its unanswered questions gathered from them all."""
        out = [g for g in self.measure_groups(None)]
        comps = {}
        for s in self.stages:
            for g in self.measure_groups(s):
                if g[0] == "Flow":
                    continue
                if g[0] != "Part":
                    out.append(g)
                    continue
                level, pill, name, kind, handles, holes = g
                have = comps.setdefault(name, [level, pill, name, kind, [], [], set()])
                have[4] += [h for h in handles if h not in have[4]]
                for r in holes:
                    key = (r.get("question"), r.get("element"))
                    if key not in have[6]:
                        have[6].add(key)
                        have[5].append(r)
        return out + [tuple(v[:6]) for v in comps.values()]

    def measure_pane(self, s, every=False):
        """One part of the flow, with the level chips over the table: All levels, Flow, Stage, Steps, Components, each
        counted in this part, exactly one pressed. All measures (every) shows each measure once, each component once;
        the flow (no stage) shows the flow's own measures; a stage shows only its own, never the flow's."""
        cells = getattr(self, "cells", {})
        groups = self.all_groups() if every else self.measure_groups(s) if not s else self.measure_groups(s)[1:]
        lv_of = {"Flow": "flow", "Stage": "stage", "Step": "step", "Part": "part"}
        seen = {}
        for g in groups:
            for h in g[4]:
                if h in cells:
                    seen.setdefault(lv_of[g[0]], set()).add(h)
        total = len(set().union(*seen.values())) if seen else 0
        scope = "the whole flow" if every else "this stage" if s else "the flow as a whole"
        part = ("All measures" if every else f'Flow · {self.f.get("name") or ""}' if not s
                else f'Stage {s.get("order")} of {len(self.stages)} · {s.get("name") or ""}')
        chips = [("all", "All levels", total)] + [(k, lab, len(seen.get(k, ()))) for k, lab in
                                                   (("flow", "Flow"), ("stage", "Stage"), ("step", "Steps"),
                                                    ("part", "Components"))]
        bar = ('<div class="lvbar" role="group" aria-label="Level">' + "".join(
            f'<button type="button" class="lvchip{" zero" if n == 0 else ""}" data-lv="{k}" data-n="{n}" '
            f'data-name="{E(lab)}" aria-pressed="{"true" if k == "all" else "false"}">{E(lab)}<span class="c">{n}</span>'
            "</button>" for k, lab, n in chips) + "</div>")
        count = f'<p class="count" data-scope="{scope}">{E(nn(total, "measure"))} in {scope}</p>'
        strip = (f'<span class="sl">Part</span><span class="sn">{E(part)}</span>'
                 '<span class="sl">Level</span><span class="sn" data-lvname>All levels</span>')
        rows, prev = [], None
        for level, pill, name, kind, handles, holes in groups:
            lv = lv_of[level]
            depth = {"Flow": 0, "Stage": 1}.get(level, 2)
            comp = name if level == "Part" else None
            ms = [h for h in handles if h in cells]
            holes = [r for r in holes if r.get("gap_kind") not in ("does not apply", "counted by")]  # nothing missing
            if not ms and not holes:
                continue  # nothing to show at this level
            if level == "Part" and prev != "Part":
                rows.append(f'<tr class="lvh gs" data-lv="part"><td colspan="7" style="padding-left:{4 + depth * 6}px">'
                            '<span class="pill">Components</span></td></tr>')
            span = len(ms) + len(holes)
            where = (f'<span class="cline"><span class="atname b">{E(name)}</span><span class="ktag">{E(kind)}</span></span>'
                     if level == "Part" else f'<span class="pill">{E(pill)}</span><span class="atname">{E(name)}</span>')
            at = (f'<td class="at{" stg" if level == "Stage" else ""}" rowspan="{max(span, 1)}" '
                  f'style="padding-left:{4 + depth * 6}px">{where}</td>')
            start = (" gp" if prev == "Part" else "") if level == "Part" else (" gs" if level != prev else " gp")
            prev, first = level, [True]

            def lead():
                if first[0]:
                    first[0] = False
                    return at
                return ""
            for i, h in enumerate(ms):
                c, key = cells[h], f"{self.i}|{h}"
                lay = c["layer"].lower()
                came = "" if c["from"] == comp else (f'<span class="q">{E(NA)}</span>' if c["from"] == NA else
                                                     E(c["from"]) if " " in c["from"] else f'<span class="nm">{E(c["from"])}</span>')
                rows.append(
                    f'<tr class="m{start if i == 0 else ""}" data-lv="{lv}" tabindex="0" data-k="{E(key)}" '
                    f'aria-expanded="false" title="Click to open or close">{lead()}<td class="mcol"><span class="mname">'
                    f'{E(shown(c["measure"], comp))}</span></td>'
                    f'<td class="lay"><span class="badge {LCLS.get(lay, "")}">{E(lay[:1].upper() + lay[1:])}</span></td>'
                    f'<td class="can">{came}</td><td class="can">{E(c["source"])}</td>'
                    f'<td class="can">{code_cell(c["code"][0])}</td><td class="can">{exporter_cell(c["exporter"][0])}</td></tr>')
                rows.append(f'<tr class="ev" data-lv="{lv}" data-ev="{E(key)}" hidden><td colspan="6">{measure_detail(c)}</td></tr>')
            for i, r in enumerate(holes):
                said = "Nothing records it" if r.get("gap_kind") == "no record" else "Not looked at yet"
                label = QTYPE.get(r.get("question") or "") or measure_what(r)
                rows.append(f'<tr class="np{start if not ms and i == 0 else ""}" data-lv="{lv}">{lead()}<td class="mcol">'
                            f'{E(label)}</td><td class="lay"></td><td class="can" colspan="4"><span class="chip nf">{said}</span>'
                            "</td></tr>")
            if not span:
                rows.append(f'<tr class="np{start}" data-lv="{lv}">{lead()}<td colspan="6"></td></tr>')
        table = ('<div class="m2s"><table class="mt"><colgroup><col><col><col><col><col><col><col>'
                 '</colgroup>'
                 '<thead><tr><th></th><th></th><th></th><th class="can" colspan="4">Can it be counted today</th></tr>'
                 '<tr><th>Where</th><th>Measure</th><th>Layer</th><th class="can">From</th><th class="can">Source</th>'
                 '<th class="can">In code</th><th class="can">Exporter</th></tr></thead><tbody>' + "".join(rows)
                 + "</tbody></table></div>")
        return f'{bar}{count}<div class="shead">{strip}</div>{table}'

    def instr_pane(self, s):
        xs = self.stage_measures(s) if s else self.flow_measures()
        trs = []
        for k, title in INSTR_STATES:
            g = [m for m in xs if (self.counted.get(m["handle"]) or {}).get("state") == k]
            if not g:
                continue
            trs.append(("blk grp", ["", "", f"{title} ({len(g)})", "", ""]))
            for n, m in enumerate(g, 1):
                c = self.counted[m["handle"]]
                trs.append(("ins" if k == "seen" else "ins no", ["", str(n), m.get("measure") or "", c["place"], c["takes"]]))
        unknown = [m for m in xs if m["handle"] not in self.counted]
        for n, m in enumerate(unknown, 1):
            trs.append(("ins no", ["", str(n), m.get("measure") or "", "not recorded", ""]))
        if not xs:
            trs = [("gap", ["", "", "No measures defined here yet", "", ""])]
        said = ("This stage: " if s else "The whole flow: ") + f"{self.sent(xs)} of {nn(len(xs), 'measure')} sent to monitoring."
        return (table(["", "", "Measure", "Counted from", "What exists, and what it needs"], trs)
                + note("Instrumented: the application produces the measure and sends it to monitoring. " + said
                       + " Read from the code and its monitoring set-up, not from a running system."))

    def alert_pane(self, s):
        if s:
            pool = [dict(a, where="") for a in (s.get("alerts") or {}).get("items") or []]
        else:
            pool = [dict(a, where=f"Stage {st.get('order')}: ") for st in self.stages
                    for a in (st.get("alerts") or {}).get("items") or []]
        lay = [lambda x: x.startswith("business"), lambda x: x == "application", lambda x: x == "technology"]

        def cell(lv, fit):
            xs = [(n, a) for n, a in enumerate(pool, 1) if LEVEL.get(a.get("level"), 3) == lv and fit(a.get("layer") or "")]
            return "\n".join(f"{n}. {a['where']}{a.get('measure')}"
                             + (f" ({a['layer'][9:]})" if (a.get("layer") or "").startswith("business ") else "")
                             + ("" if a.get("exists_today") else ", not in the app yet") for n, a in xs) or "none"
        trs = [("ab", [t, ""] + [cell(lv, fit) for fit in lay]) for t, lv in (("Flow", 0), ("Stage", 1), ("Step", 2), ("Part", 3))]
        return (table(["Level", "", "Business", "Application", "Technology"], trs)
                + note(("This stage’s " if s else "The flow’s ") + nn(len(pool), "alert") + ", each placed once: at "
                       "the level it watches, and in the health layer of the measure it is built on (business, "
                       "application or technology; a business alert is marked impact when it counts cases that failed "
                       "what was expected of them, and health when it counts whether the work is happening). The kit "
                       "proposes alerts only on what happens to the flow’s cases, and leaves service and store "
                       "signals to the runbooks, so empty Application and Technology columns are how the kit works, not "
                       "a gap in this run. The threshold, the window and whether it pages someone are set by the "
                       "people who run it, not by the kit."))

    def runbook_pane(self, s):
        rb = s.get("runbooks") or {}
        entries = rb.get("entries") or []
        if not entries:
            return note("No runbook written for this stage.")
        rows = rb.get("failure_rows") or []
        more = [r.get("what") + ("" if r.get("written") else ": not written yet") for r in rows]
        title = f"Failure modes the stage needs ({sum(1 for r in rows if r.get('written'))} of {len(rows)} written)"
        its = [item("For “" + (e.get("heading") or e.get("handle") or "") + "”",
                    [("Kit check", "passes" if e.get("passes") else "does not pass yet: " + "; ".join(e.get("reasons") or [])),
                     ("Status", rb.get("status", "") + ", never rehearsed")], title, more) for e in entries]
        return secs([(f"Runbook entries, one per alert ({len(entries)})", its)])

    # ---- the tree's counts
    def count(self, p, s):
        def opened(key):  # a draft its own check fails says so wherever the stage's measures or alerts show
            n = (s.get(key) or {}).get("open_items", 0)
            return f", {nn(n, 'open item')}" if n else ""
        if p == MAPPED:
            return f"{nn(len(s.get('steps') or []), 'step')}, {nn(len(s.get('parts') or []), 'part')}"
        if p == MEAS:
            gaps = sum(1 for r in (s.get("measures") or {}).get("items") or [] if r.get("state") != "measured")
            return f"{nn(len(self.stage_measures(s)), 'measure')}, {nn(gaps, 'question')} without one{opened('measures')}"
        if p == INSTR:
            xs = self.stage_measures(s)
            return f"{self.sent(xs)} of {len(xs)} sent to monitoring"
        if p == ALERTS:
            return nn((s.get("alerts") or {}).get("count", 0), "alert") + opened("alerts")
        if p == RUNBOOKS:
            return nn((s.get("runbooks") or {}).get("count", 0), "runbook")
        return ""

    def flow_count(self, p):
        if p == MEAS:
            return nn(len(self.flow_measures()), "measure") + " of the whole flow"
        if p == INSTR:
            xs = self.flow_measures()
            return f"{self.sent(xs)} of {nn(len(xs), 'measure')} of the whole flow sent to monitoring"
        if p == ALERTS:
            return nn(sum((s.get("alerts") or {}).get("count", 0) for s in self.stages), "alert") + " across its stages"
        return ""


# ---------------------------------------------------------------- the open choice

def form_of(d):
    """(milestone, {item key}) of the open choice the page takes, or None: the go and the pick only."""
    c = d.get("open_choice")
    if not c or c.get("milestone") not in ("Mapped", "Measures defined"):
        return None
    return c["milestone"], [i["key"] for i in c.get("items") or []]


def recorded(d, keys):
    """{stage id: the milestones its recorded depth already holds}: shown ticked, never locked."""
    got = {}
    for f in d.get("flows") or []:
        for s in f.get("stages") or []:
            if s.get("stage") in keys:
                reach = depth.REACHES.get(s.get("recorded_depth") or "none", ())
                got[s["stage"]] = [o for o, v in depth.DEPTH_OPTS.items() if v in reach]
    return got


CLEAR = ('<button type="button" class="ab2" data-clear="" title="Undo what you changed in this drop-down">'
         'Clear</button>')  # puts its own drop-down back as it loaded and sends nothing
CLEAR_PAGE = ('<button type="button" class="ab2" data-clear="page" title="Undo everything you changed on this page">'
              'Clear</button>')  # the top line's: the whole page


def at_the_first(d):
    """Whether the open choice is the go's, which flow is mapped first: then it is picked at the top of the page."""
    return bool(form_of(d)) and d["open_choice"].get("task") == FIRST_TASK


def form_html(d):
    """The form beside its ticks: the choice it answers, the person's words, Done, and what happened. The ticks are
    the named checkboxes in the drop-downs; a tick the choice does not take has no name. At the go the pick at the
    top of the page carries it instead."""
    c = d.get("open_choice")
    if not form_of(d) or at_the_first(d):
        return ""
    add = ""
    if c.get("task") == NEXT_TASK:  # a flow the first look missed: added, and mapped next
        add = (f'<span class="mute">{E(c.get("add") or "")}</span><input type="text" class="wi" name="add" '
               f'aria-label="{E(c.get("add") or "")}" placeholder="Its name" autocomplete="off">')
    return (f'<div id="answers" hidden><input type="hidden" name="choice_id" value="{E(c["choice_id"])}" '
            'autocomplete="off"><div class="tdone" id="ask"><span class="mute"></span>'
            '<input type="text" class="wi" name="words" aria-label="Your words" placeholder="Your words" '
            'autocomplete="off">' + add +
            '<button type="button" class="ab2 dn" data-done>Done</button>' + CLEAR +
            '<span class="mute" data-status></span></div></div>')


# ---------------------------------------------------------------- the page

def tick(attrs, label):
    # autocomplete off on every input: after a reload a browser would otherwise put the last load's ticks back
    return f'<input type="checkbox" class="tk" aria-label="{E(label)}"{attrs} autocomplete="off">'


TALK_KEY, TALK_WORDS = "talk:", "talk-words:"  # topics to talk about with Claude, never recorded as a pick


def pick_html(d):
    """At the go: every flow found, one row each with its tick to map it first (the go's own tick, named by the flow,
    so go.py --answers records it as the flow), the recommended one marked, then the words and Done. Drawn at the top
    of the page, so the pick is seen without opening anything; the drop-downs carry no second tick for it. Its own
    `data-dd` scopes its Clear to it."""
    if not at_the_first(d):
        return ""
    c = d["open_choice"]
    rows = []
    for i in c.get("items") or []:
        box = tick(f' name="{E(i["key"])}" value="{E(depth.FLOW_OPT)}" data-flowtick', f"Map {i.get('name')} first")
        mark = '<span class="recm">Recommended</span>' if i.get("recommended") else ""
        rows.append(f'<div class="it"><label class="trow">{box}<span class="pnm">{E(i.get("name") or "")}</span>'
                    f'{mark}</label></div>')
    return (f'<div class="card pick" id="pick" data-dd="pick"><div class="dh"><b>{E(c["task"])}</b>'
            '<span class="mute">The run waits on this pick. One flow per run; the others follow into the same map.'
            f'</span></div>{"".join(rows)}<div id="answers"><input type="hidden" name="choice_id" '
            f'value="{E(c["choice_id"])}" autocomplete="off"><div class="tdone" id="ask"><span class="mute">'
            f'{E(AT_THE_FIRST)}</span><input type="text" class="wi" name="words" aria-label="Your words" '
            'placeholder="Your words" autocomplete="off"><button type="button" class="ab2 dn" data-done>Done</button>'
            + CLEAR + '<span class="mute" data-status></span></div></div></div>')


TODO_TITLE = "What do you want to do?"
TODO_KEY = TALK_WORDS + "Home"  # a topic like any drop-down's words: go.py --answers records it in RUN.md


def todo_html():
    """The page's first section, always there: the person's words to Claude, sent with Done by the page's one route
    (page-kit.js posts every named input to the listener, which saves it in answers/ for the session waiting on the
    page; go.py --answers records the words as a topic to talk about). Its own `data-dd` scopes its Clear to it."""
    return (f'<div class="card" id="todo" data-dd="todo"><div class="dh"><b>{E(TODO_TITLE)}</b></div>'
            f'<div class="tdone todo"><span class="mute">{E(WORDS_ONLY)}</span><input type="text" class="wi" '
            f'name="{E(TODO_KEY)}" data-flow="" aria-label="Your words" placeholder="Your words" autocomplete="off">'
            '<button type="button" class="ab2 dn" data-done>Done</button>' + CLEAR +
            '<span class="mute" data-status></span></div></div>')


def where_it_stands(d):
    """The line under the flows: what the run waits on while a choice is open, else the run's stop. The next flow is
    an open case's next step, never a wait on the person: its line is the run's stop, which offers it."""
    task = (d.get("open_choice") or {}).get("task")
    return f"waiting on you to {task[:1].lower() + task[1:]}" if task and task != NEXT_TASK else d.get("stop")


def talk_tick(milestone, key, label):
    """A tick outside the open choice: a topic to talk about, sent with every Done. The value is the item's own label;
    go.py names the milestone before it."""
    return tick(f' name="{E(TALK_KEY + milestone + ":" + key)}" value="{E(label)}"', f"{milestone}: {label}")


def measures_split(fl, d, name, panes, first, stage_choice, stage_keys, held):
    """Measures defined: the flow on the left, its whole and its stages, the selected one a tab joined to the strip
    over the table; while the person's pick of how far each stage goes is open, each stage carries its ticks beside
    its tab (picking is not selecting). On the right the title, the meanings, one words box, and the selection's pane."""
    f = fl.f
    first = first if first in panes else "all"
    cur = lambda k: f' aria-current="{"true" if k == first else "false"}"'
    own = {m["handle"] for m in fl.flow_measures()}
    side = [f'<nav class="mside" aria-label="Flow and stages"><div class="ents">'
            f'<button type="button" class="ent whole" data-sel="all"{cur("all")}><span>All measures</span>'
            f'<span class="c">{len(fl.ms)}</span></button></div><div class="fhead"><span class="flab">Flow</span></div>'
            f'<div class="ents"><button type="button" class="ent whole fent" data-sel="flow"{cur("flow")}>'
            f'<span class="fname">{E(f.get("name") or "")}</span><span class="c">{len(own)}</span></button></div>'
            '<div class="fhead"><span class="flab">Stages</span></div><div class="ents">']
    for k, s in enumerate(fl.stages):
        picks = ""
        if stage_choice and s["stage"] in stage_keys:
            on = " checked" if name in held.get(s["stage"], ()) else ""
            picks = ('<span class="epick">' + tick(f' name="{E(s["stage"])}" value="{E(name)}" data-stagetick{on}',
                                                   f"{name}: {s.get('name')}") + "</span>")
        side.append(f'<div class="erow">{picks}<button type="button" class="ent" data-sel="{k}"{cur(str(k))}>'
                    f'<span class="n">{E(str(s.get("order")))}</span><span>{E(s.get("name") or "")}</span>'
                    f'<span class="c">{len({m["handle"] for m in fl.stage_measures(s)} - own)}</span></button></div>')
    side.append("</div></nav>")
    if stage_choice:
        talk = (f'<div class="tslot" data-ask data-flow="{E(f.get("name") or "")}" data-milestone="{E(name)}" '
                f'data-note="{E(AT_THE_PICK)}"></div>')
    else:
        talk = (f'<div class="tslot talk"><input type="text" class="wi" name="{E(TALK_WORDS + name)}" '
                f'data-flow="{E(f.get("name") or "")}" aria-label="Ask about this stage" placeholder="Ask about this '
                'stage" autocomplete="off"><button type="button" class="ab2 dn" data-done>Done</button>' + CLEAR +
                '<span class="mute" data-status></span></div>')
    head = ('<div class="mhead"><h3 class="mtitle">Measures</h3><button class="tbtn" type="button" data-defs '
            'aria-expanded="false">Meanings</button></div>')
    pane = "".join(f'<div class="pane" data-pane="{k}"{"" if k == first else " hidden"}>{v}</div>' for k, v in panes.items())
    return f'<div class="msplit">{"".join(side)}<div class="m2 mmain">{head}{talk}{MEASURE_DEFS}{pane}</div></div>'


def dropdown(fl, p, d):
    f, i = fl.f, fl.i
    name, q, _ = COLS[p]
    choice = form_of(d)
    flow_choice = bool(choice and choice[0] == "Mapped" and p == MAPPED and f.get("name") in choice[1]
                       and not at_the_first(d))  # at the go the pick sits at the top of the page
    stage_keys = set(choice[1]) if choice and choice[0] == "Measures defined" else set()
    stage_choice = p in KEY and fl.mapped and any(s["stage"] in stage_keys for s in fl.stages)
    held = recorded(d, stage_keys) if stage_choice else {}
    pages = fl.pages(p)
    out = [f'<div class="inl" hidden data-dd="{i}-{p}"><div class="dh"><b>{E(name)}</b><span class="mute">{E(q)}</span></div>']
    if pages:
        out.append('<div class="pgs"><span class="mute">The stage kit\'s own pages, opened in this tab:</span>' + "".join(f'<a class="pgl" href="{E(rel)}">{E(label)} ›</a>'
                                                       for rel, label in pages) + "</div>")
    panes = fl.panes(p)
    first = "0" if "0" in panes else "-1"
    if p == MEAS and fl.mapped and len(panes) > 1:
        out.append(measures_split(fl, d, name, panes, first, stage_choice, stage_keys, held))
        out.append("</div>")
        return "".join(out)
    picker = False
    tree = [f'<div class="tree" role="tree" aria-label="Where this is"{" data-picker" if picker else ""}>'
            + ('<div class="tlab"><span>Flow</span><span>Measures</span></div>' if picker else
               f'<div class="tn d0"><span class="tl">{E(d["_title"])}</span></div>')]
    ticked = False
    flow_tick = ""
    if p == MAPPED:
        ticked = True
        flow_tick = (tick(f' name="{E(f.get("name") or "")}" value="{E(depth.FLOW_OPT)}" data-flowtick',
                          "Map this flow in the next run") if flow_choice
                     else talk_tick(name, f.get("name") or "", f.get("name") or ""))
    flow_label = (f'<span class="tl">{E(f.get("name") or "")}</span><span class="tc">{len(fl.flow_measures())}</span>'
                  if picker else
                  f'<span class="tg">└─</span><span class="tl"><span class="lvl">Flow {i + 1}</span> '
                  f'{E(f.get("name") or "")}</span><span class="tc">{E(fl.flow_count(p))}</span>')
    if "-1" in panes and len(panes) > 1:
        tree.append(f'<div class="trow">{flow_tick}<button type="button" class="tn d1 tb" data-sel="-1" '
                    f'aria-current="false">{flow_label}</button></div>')
    else:
        tree.append(f'<div class="trow">{flow_tick}<div class="tn d1">{flow_label}</div></div>')
    if fl.mapped and p != IDENT:
        n = len(fl.stages)
        if picker:
            tree.append('<div class="tlab"><span>Stages</span><span></span></div>')
        for k, s in enumerate(fl.stages):
            glyph = "└─" if k == n - 1 else "├─"
            t = ""
            if p != MAPPED:
                ticked = True
                on = " checked" if name in held.get(s["stage"], ()) else ""
                t = (tick(f' name="{E(s["stage"])}" value="{E(name)}" data-stagetick{on}', f"{name}: {s.get('name')}")
                     if stage_choice and s["stage"] in stage_keys
                     else talk_tick(name, s["stage"], s.get("name") or ""))
            body = (f'<span class="sno">{E(str(s.get("order")))}</span><span class="tl">{E(s.get("name") or "")}</span>'
                    f'<span class="tc">{len(fl.stage_measures(s))}</span>' if picker else
                    f'<span class="tg">{glyph}</span><span class="tl"><span class="lvl">Stage {E(str(s.get("order")))}</span> '
                    f'{E(s.get("name") or "")}</span><span class="tc">{E(fl.count(p, s))}</span>')
            if str(k) in panes:
                on = " on" if str(k) == first else ""
                tree.append(f'<div class="trow">{t}<button type="button" class="tn d2 tb{on}" data-sel="{k}" '
                            f'aria-current="{"true" if on else "false"}">{body}</button></div>')
            else:
                tree.append(f'<div class="trow">{t}<div class="tn d2">{body}</div></div>')
    elif fl.mapped and p == IDENT:
        n = len(fl.stages)
        for k, s in enumerate(fl.stages):
            glyph = "└─" if k == n - 1 else "├─"
            tree.append(f'<div class="trow"><div class="tn d2"><span class="tg">{glyph}</span><span class="tl">'
                        f'<span class="lvl">Stage {E(str(s.get("order")))}</span> {E(s.get("name") or "")}</span></div></div>')
    tree_note = {MAPPED: PART + " A part shared by several stages counts in each.",
                 INSTR: "A part shared by several stages counts in each."}.get(p) if fl.mapped else None
    if tree_note:
        tree.append(f'<div class="mute" style="padding: 6px 4px 0">{E(tree_note)}</div>')
    if flow_choice or stage_choice:
        said = AT_THE_GO if flow_choice else AT_THE_PICK
        tree.append(f'<div class="tslot" data-ask data-flow="{E(f.get("name") or "")}" data-milestone="{E(name)}" '
                    f'data-note="{E(said)}"></div>')
    else:
        said = TALK if ticked else WORDS_ONLY
        tree.append(f'<div class="tslot"><div class="tdone"><span class="mute">{E(said)}</span><input type="text" '
                    f'class="wi" name="{E(TALK_WORDS + name)}" data-flow="{E(f.get("name") or "")}" aria-label="Your words" '
                    'placeholder="Your words" '
                    'autocomplete="off">'
                    '<button type="button" class="ab2 dn" data-done>Done</button>' + CLEAR +
                    '<span class="mute" data-status></span></div></div>')
    tree.append("</div>")
    pane = "".join(f'<div class="pane" data-pane="{k}"{"" if k == first else " hidden"}>{v}</div>' for k, v in panes.items())
    out.append(f'<div class="split">{"".join(tree)}{pane}</div></div>')
    return "".join(out)


def row(fl):
    f, i = fl.f, fl.i
    dots = [fl.dot(p) for p in range(len(COLS))]
    out = [f'<div class="trk rw" data-row="{i}"><span class="nm"><span class="lvl">Flow {i + 1}</span>'
           f'<b>{E(f.get("name") or "")}</b><small>{E(sub_line(f))}</small></span>']
    for p, (cls, label, lst) in enumerate(dots):
        go_on = " go" if cls and p < len(dots) - 1 and dots[p + 1][0] else ""
        out.append(f'<button type="button" class="sp {cls}{go_on}" data-dot="{i}-{p}" aria-pressed="false" '
                   f'aria-label="Flow {i + 1}, {E(COLS[p][0])}: show what is there to review"><span class="ln"></span>'
                   f'<span class="pt"></span><span class="lb">{E(label)}</span>'
                   + "".join(f'<span class="lb sm">{E(y)}</span>' for y in lst) + "</button>")
    out.append("</div>")
    return "".join(out)


PROGRESS = [(MAPPED, "Mapped"), (MEAS, "Measures"), (ALERTS, "Alerts"), (RUNBOOKS, "Runbooks")]
NOT_RECORDED = "not recorded"


def identity_html(reg, flows):
    """The block at the top: which application this is, what it does, and how far its flows have come. Labels by
    colour only, one font size; a field the register does not hold reads "not recorded"."""
    about = cv.read_csv(reg / "about.csv") if (reg / "about.csv").is_file() else []
    system, prop = ss.unproposed((about[0].get("system") if about else "") or "")
    system = system.strip() + (" (proposed)" if prop and system.strip() else "")
    app_id = ((about[0].get("application_id") if about else "") or "").strip()
    try:
        what = (json.loads((reg / "orientation.json").read_text(encoding="utf-8")).get("capability") or {}).get("what")
    except (OSError, ValueError, AttributeError):
        what = ""
    n = len(flows)
    progress = " · ".join(f"{label} {sum(1 for fl in flows if fl.status(p) in FILLED_WHEN[p])}/{n}"
                          for p, label in PROGRESS)
    rows = [("Application", system, True), ("Application ID", app_id, False), ("Line of business", "", False),
            ("What it does", (what or "").strip(), False), ("Flows", str(n), False), ("Progress", progress, False)]
    cells = "".join(f'<span class="il">{E(k)}</span>'
                    + (f'<span>{"<b>" + E(v) + "</b>" if bold else E(v)}</span>' if v
                       else f'<span class="il">{NOT_RECORDED}</span>')
                    for k, v, bold in rows)
    return f'<div class="card ident"><div class="idg">{cells}</div></div>'


def render(reg, d):
    reg = pathlib.Path(reg)
    d = dict(d, _title=title(reg, d))
    counted = counted_at_stand_in(reg)
    flows = [Flow(reg, d, i, f, counted) for i, f in enumerate(d.get("flows") or [])]
    cells, parts = measure_cells(reg), part_info(reg)
    for fl in flows:
        fl.cells, fl.parts = cells, parts
    head = ('<div class="trk hd"><span>Flow</span>' + "".join(
        f'<span class="sh"><b>{E(n)}</b><small>{E(q)}</small><small class="out">{E(o)}</small></span>'
        for n, q, o in COLS) + "</div>")
    rows = "".join(row(fl) + "".join(dropdown(fl, p, d) for p in range(len(COLS))) for fl in flows)
    the_map = (f'<a class="go" href="{MAP_FILE}">The map</a>' if (reg / MAP_FILE).is_file()
               else '<span class="off">The map</span>')
    sources = '<a class="go" href="sources.html">Sources</a>' if (reg / "sources.csv").is_file() else ""
    status = '<a class="go" href="operator.html">Run status</a>' if (reg / "RUN.md").is_file() else ""
    up = (f'<a class="go" href="{ps.all_systems_href(FILE)}">{ps.ALL_SYSTEMS}</a>'
          if ps.all_systems_above(reg) else "")
    nav = (f'<div class="nav">{up}<span class="sys">{E(d["_title"])}</span><a class="go on" href="{FILE}" '
           f'aria-current="page">Home</a>{the_map}{sources}{status}<span class="sp2"></span></div>')
    blind = ("Found is only what has been found so far; a traced flow shows only what its trace found."
             if any(fl.mapped for fl in flows) else "Found is only what has been found so far.")
    source = f"Drawn from depth.json in the register {d.get('register') or reg.name}. Where the run stands: {where_it_stands(d)}."
    import progress  # while a flow is mapped, the last part of the map written, as the chat said it
    source += (" " + progress.latest(reg)) if progress.latest(reg) else ""
    generated = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n     Source: depth.json in this folder, and "
                 "home.template.html\n     Builder: home.py\n     Build: python home.py <register folder>\n-->")
    page = TEMPLATE.read_text(encoding="utf-8")
    for k, v in (("<!--GENERATED-->", generated), ("<!--TITLE-->", E("Home · " + d["_title"])), ("<!--NAV-->", nav),
                 ("<!--TODO-->", todo_html()), ("<!--IDENTITY-->", identity_html(reg, flows)), ("<!--HEAD-->", head),("<!--ROWS-->", rows), ("<!--BLIND-->", E(blind)),
                 ("<!--SOURCE-->", E(source)), ("<!--FORM-->", form_html(d)), ("<!--PICK-->", pick_html(d)), ("<!--CLEAR-->", CLEAR_PAGE)):
        page = page.replace(k, v, 1)
    # the watch compares this stamp, not the first page it fetches, so a redraw before its first check is still seen
    stamp = hashlib.sha256(page.encode("utf-8")).hexdigest()[:16]
    return page.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta name="drawn" content="{stamp}">', 1)


def title(reg, d):
    """The system's name as the run's pages show it: the capability's, "(proposed)" while drafted, else the register's."""
    name, prop = ss.unproposed(d.get("capability") or "")  # a drafted capability name reads "(proposed)" too
    return (name.strip() + (" (proposed)" if prop else "")) if name.strip() else d.get("register") or pathlib.Path(reg).name


def write(reg):
    reg = pathlib.Path(reg)
    d = json.loads((reg / depth.FILE).read_text(encoding="utf-8"))
    import all_systems  # the work folder's list of every system: there before the link to it, listing this one after
    all_systems.update(reg)
    # written beside it and moved into place in one step, so the open page never fetches half of it
    part = reg / (FILE + ".part")
    part.write_text(render(reg, d), encoding="utf-8", newline="\n")
    try:
        for attempt in range(10):
            try:
                os.replace(part, reg / FILE)
                break
            except PermissionError:  # on Windows, while the listener is reading the page; it lets go within moments
                if attempt == 9:
                    raise
                time.sleep(0.05)
    except OSError:
        part.unlink(missing_ok=True)
        raise
    all_systems.update(reg)
    return reg / FILE


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) != 1 or not pathlib.Path(argv[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    reg = pathlib.Path(argv[0])
    run_lock.guard(reg, touch=False)  # a redraw of the register's view: never itself work in motion
    if not (reg / depth.FILE).is_file():
        print(f"REFUSED: {reg / depth.FILE} is missing: write it first with depth.py. Nothing written.", file=sys.stderr)
        return 2
    print(f"Written: {write(reg)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
