"""The home screen: index.html in the register folder, drawn from the run's depth.json.

Usage: python home.py <register folder>

One row per flow, one dot per milestone toward supported in production: Identified, Mapped, Measures defined,
Instrumented, Dashboards built, Alerts defined, Runbooks written, Team prepared. The five the kit works on show their
status in depth.json (`not started`, `draft`, `reviewed`); the other three are done by other teams, and their dots
never fill (Instrumented carries a count read from the code at design time). A dot opens a
drop-down under its flow with what is there to review at that milestone and links to the kit's own pages for it,
each in the same tab. Recommendations and their reasons stay in depth.json and are never drawn. Nothing is ticked
for the person, except a stage's depth already recorded.

While a choice waits on the person at the go or at the pick (depth.json's open choice), the page carries the form
for it, as a listener serving the page reads it: a hidden `choice_id`, one free-text `words`, and per item a
checkbox group named by the item's key whose values are the milestones ticked. The review of the alerts is not
taken from a page, so it has no form. Every other tick is a topic to talk about with Claude, named
`talk:<milestone>:<item key>` with its label as the value, and each drop-down's words `talk-words:<milestone>`; any
Done sends them all, and the page reloads once the run has redrawn it.

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
import run_lock  # noqa: E402

FILE = "index.html"
TEMPLATE = HERE / "home.template.html"
MAP_FILE = "views.html"
MADE_FILE = "how-this-map-was-made.html"
E = html.escape

COLS = [
    ("Identified", "We know the flow exists", ""),
    ("Mapped", "Its stages, steps and parts are known", ""),
    ("Measures defined", "What “working” means, and what to count", ""),
    ("Instrumented", "The application produces them and sends them to monitoring", "Outside the kit: the developers"),
    ("Dashboards built", "The views exist", "Outside the kit"),
    ("Alerts defined", "What should raise an alert", ""),
    ("Runbooks written", "What to do when each alert fires", ""),
    ("Team prepared", "The people have practised on it", "Outside the kit"),
]
IDENT, MAPPED, MEAS, INSTR, DASH, ALERTS, RUNBOOKS, TEAM = range(8)
OUTSIDE = (INSTR, DASH, TEAM)
KEY = {MEAS: "measures", ALERTS: "alerts", RUNBOOKS: "runbooks"}
# What fills a dot. Runbooks are drafted and never reviewed, so they fill once drafted, like the first three. Alerts
# fill once the review of the proposed alerts is recorded. The three outside the kit never fill: the kit cannot see
# another team's work, and its count of measures sent to monitoring is read from the code at design time.
FILLED_WHEN = {IDENT: ("draft", "reviewed"), MAPPED: ("draft", "reviewed"), MEAS: ("draft", "reviewed"),
               ALERTS: ("reviewed",), RUNBOOKS: ("draft", "reviewed")}

TALK = "Tick what you want to talk about with Claude · say what in your words"
WORDS_ONLY = "Your words go to Claude"
AT_THE_GO = "Tick the flow to map in the next run · one flow per run"
AT_THE_PICK = ("Tick what gets more work · say what in your words · ticking a milestone brings the ones "
               "before it")

KIND = {"does not apply": "does not apply here", "counted by": "counted by another measure",
        "no record": "the application keeps no record to count it", "not read": "not looked at yet"}
STAGE_Q = {"in the stage": "How many cases are in this stage now", "oldest's age": "How long the oldest case has waited",
           "time through": "How long cases take through the stage", "past the time limit": "How many are past the time limit"}
MAP_Q = {"stage: a case enters": "how a case enters", "stage: expected outcomes": "the outcome expected",
         "stage: other outcomes": "what else can happen", "stage: cannot be undone": "what cannot be undone",
         "stage: at stake": "what is at stake", "stage: expected by each party": "what each party expects",
         "step: moves": "its moves in the code", "step: trigger": "what starts it",
         "step: right outcome": "its right outcome", "step: if it does not happen": "what happens if it does not",
         "step: timeouts": "its time limits"}
LEVEL = {"flow": 0, "stage": 1, "step": 2, "part": 3}


def plain(text):
    """A register cell without its citations in brackets."""
    return re.sub(r"\s*\([^()]*(?:\([^()]*\)[^()]*)*\)", "", text or "").strip()


def unproposed(text):
    return re.sub(r"^\s*proposed:\s*", "", plain(text or ""))


def short(text):
    """A stage's entry or exit as the state it names: the text before any explanation after a colon, no move ids."""
    t = re.sub(r"\s*\((?:lifecycle )?L\d\d[^)]*\)", "", text or "")
    t = re.sub(r"^(implicit|proposed): ", "", t).split(":")[0].strip()
    return "the start" if t.lower() == "the starting event" else t


def nn(n, w):
    return f"{n} {w}{'' if n == 1 else 's'}"


def about(f):
    """(one case, starts, ends) in a few words each."""
    ends = "; ".join(x.rstrip(".") for i, x in enumerate(plain(f.get("ends")).split(". ")) if i == 0 or x.startswith("Or "))
    return plain(f.get("case")).split(":")[0], plain(f.get("starts")).split(":")[0], ends


def sub_line(f):
    case, starts, ends = about(f)
    if not case:
        return f.get("what") or ""
    return " · ".join([case, "from: " + starts.lower(), "to: " + ends.lower()])


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


def level_rows(levels, cells_for, width):
    """Rows of a table read by level: the level's own row, then its items numbered, or why there are none."""
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
                trs.append(("", ["", str(n)] + cells_for(x)))
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
            return "", "Nothing recorded", []
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
            return {"-1": note("Nothing recorded yet. This is done outside the kit.")}
        if p == MAPPED:
            return {k: self.map_pane(s) for k, s in self.choices()}
        if p == MEAS:
            return {k: self.measure_pane(s) for k, s in self.choices()}
        if p == INSTR:
            return {k: self.instr_pane(s) for k, s in self.choices()}
        if p == ALERTS:
            return {k: self.alert_pane(s) for k, s in self.choices()}
        return {str(k): self.runbook_pane(s) for k, s in enumerate(self.stages)}

    def choices(self):
        return [("-1", None)] + [(str(k), s) for k, s in enumerate(self.stages)]

    def hole(self, h, who):
        why = "not answered yet" if h.get("state") == "empty" else (
            "the code keeps no record of it" if h.get("gap_kind") == "no record" else KIND.get(h.get("gap_kind"), h.get("gap_kind") or ""))
        return {"what": "↳ " + MAP_Q.get(h.get("question"), h.get("question") or ""), "hole": "Not known: " + why,
                "who": who}

    def map_pane(self, s):
        case, starts, ends = about(self.f)
        flow = [{"item": a, "known": b} for a, b in (("One case", case), ("Starts", starts), ("Ends", ends),
                                                    ("Serves", self.f.get("serves") or ""))]
        stage, steps, parts = [], [], []
        if s:
            holes = s.get("holes") or []
            stage = [{"item": "Enters", "known": short(s.get("entry"))}, {"item": "Leaves", "known": short(s.get("exit"))}]
            stage += [{"item": "Expected by " + (e.get("party") or "").lower(), "known": unproposed(e.get("expectation"))}
                      for e in s.get("expects") or []]
            stage += [self.hole(h, "") for h in holes if h.get("of") == "stage"]
            for x in s.get("steps") or []:
                right = unproposed(x.get("right_outcome"))
                steps.append({"item": x.get("name"), "known": "Right outcome: " + right if right else ""})
                steps += [self.hole(h, x.get("name")) for h in holes if h.get("of") == "step" and h.get("item") == x.get("name")]
            parts = [{"item": x.get("name"), "known": x.get("role")} for x in s.get("parts") or []]
        none = "Nothing known at this level"
        pick = "Shown when a stage is selected"
        levels = [("Flow", "the whole flow", flow, none),
                  ("Stage", "this stage as a whole" if s else "each stage: select one in the tree", stage, none if s else pick),
                  ("Step", "each step of this stage" if s else "each step of a stage", steps, none if s else pick),
                  ("Part", "each part doing this stage’s steps" if s else "each part doing a stage’s steps", parts,
                   none if s else pick)]
        trs = level_rows(levels, lambda x: [x["item"], x["known"]], 4)
        return (table(["Level", "", "Item", "What is known"], trs)
                + note("Mapped from one case traced through the code to each of its endings. A step or part the "
                       "trace missed would not show here."))

    def measure_pane(self, s):
        flows = [{"what": m.get("counts") or "", "measure": m.get("measure") or ""} for m in self.flow_measures()]
        flows += [{"what": measure_what(r), "hole": "No measure: " + gap_why(r)}
                  for r in (self.f.get("measures") or {}).get("flow_items") or [] if r.get("state") != "measured"]

        def at(k):
            if not s:
                return []
            got = [{"what": m.get("counts") or "", "measure": m.get("measure") or ""}
                   for m in self.stage_measures(s) if LEVEL.get(m.get("level")) == k]
            return got + [{"what": measure_what(r), "hole": "No measure: " + gap_why(r)}
                          for r in (s.get("measures") or {}).get("items") or []
                          if r.get("state") != "measured" and gap_level(r) == k]
        none, pick = "Nothing is asked at this level here", "Shown when a stage is selected"
        levels = [("Flow", "the whole flow", flows, none),
                  ("Stage", "this stage as a whole" if s else "each stage: select one in the tree", at(1), none if s else pick),
                  ("Step", "each step of this stage" if s else "each step of a stage", at(2), none if s else pick),
                  ("Part", "each part doing this stage’s steps" if s else "each part doing a stage’s steps", at(3),
                   none if s else pick)]
        trs = level_rows(levels, lambda x: [x["what"], x["measure"]], 4)
        return (table(["Level", "", "What it answers", "Measure"], trs)
                + note("What working means: each question at each level, and the measure that answers it, or why "
                       "none does. A part used by several stages is listed under each of them."))

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
        if p == MAPPED:
            return f"{nn(len(s.get('steps') or []), 'step')}, {nn(len(s.get('parts') or []), 'part')}"
        if p == MEAS:
            gaps = sum(1 for r in (s.get("measures") or {}).get("items") or [] if r.get("state") != "measured")
            return f"{nn(len(self.stage_measures(s)), 'measure')}, {nn(gaps, 'question')} without one"
        if p == INSTR:
            xs = self.stage_measures(s)
            return f"{self.sent(xs)} of {len(xs)} sent to monitoring"
        if p == ALERTS:
            return nn((s.get("alerts") or {}).get("count", 0), "alert")
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


def form_html(d):
    """The form beside its ticks: the choice it answers, the person's words, Done, and what happened. The ticks are
    the named checkboxes in the drop-downs; a tick the choice does not take has no name."""
    c = d.get("open_choice")
    if not form_of(d):
        return ""
    return (f'<div id="answers" hidden><input type="hidden" name="choice_id" value="{E(c["choice_id"])}" '
            'autocomplete="off"><div class="tdone" id="ask"><span class="mute"></span>'
            '<input type="text" class="wi" name="words" aria-label="Your words" placeholder="Your words" '
            'autocomplete="off">'
            '<button type="button" class="ab2 dn" data-done>Done</button>' + CLEAR +
            '<span class="mute" data-status></span></div></div>')


# ---------------------------------------------------------------- the page

def tick(attrs, label):
    # autocomplete off on every input: after a reload a browser would otherwise put the last load's ticks back
    return f'<input type="checkbox" class="tk" aria-label="{E(label)}"{attrs} autocomplete="off">'


TALK_KEY, TALK_WORDS = "talk:", "talk-words:"  # topics to talk about with Claude, never recorded as a pick


def talk_tick(milestone, key, label):
    """A tick outside the open choice: a topic to talk about, sent with every Done. The value is the item's own label;
    go.py names the milestone before it."""
    return tick(f' name="{E(TALK_KEY + milestone + ":" + key)}" value="{E(label)}"', f"{milestone}: {label}")


def dropdown(fl, p, d):
    f, i = fl.f, fl.i
    name, q, _ = COLS[p]
    choice = form_of(d)
    flow_choice = bool(choice and choice[0] == "Mapped" and p == MAPPED and f.get("name") in choice[1])
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
    tree = [f'<div class="tree" role="tree" aria-label="Where this is"><div class="tn d0"><span class="tl">{E(d["_title"])}</span></div>']
    ticked = False
    flow_tick = ""
    if p == MAPPED:
        ticked = True
        flow_tick = (tick(f' name="{E(f.get("name") or "")}" value="{E(depth.FLOW_OPT)}" data-flowtick',
                          "Map this flow in the next run") if flow_choice
                     else talk_tick(name, f.get("name") or "", f.get("name") or ""))
    flow_label = (f'<span class="tg">└─</span><span class="tl"><span class="lvl">Flow {i + 1}</span> '
                  f'{E(f.get("name") or "")}</span><span class="tc">{E(fl.flow_count(p))}</span>')
    if "-1" in panes and len(panes) > 1:
        tree.append(f'<div class="trow">{flow_tick}<button type="button" class="tn d1 tb" data-sel="-1" '
                    f'aria-current="false">{flow_label}</button></div>')
    else:
        tree.append(f'<div class="trow">{flow_tick}<div class="tn d1">{flow_label}</div></div>')
    if fl.mapped and p != IDENT:
        n = len(fl.stages)
        for k, s in enumerate(fl.stages):
            glyph = "└─" if k == n - 1 else "├─"
            t = ""
            if p != MAPPED:
                ticked = True
                on = " checked" if name in held.get(s["stage"], ()) else ""
                t = (tick(f' name="{E(s["stage"])}" value="{E(name)}" data-stagetick{on}', f"{name}: {s.get('name')}")
                     if stage_choice and s["stage"] in stage_keys
                     else talk_tick(name, s["stage"], s.get("name") or ""))
            body = (f'<span class="tg">{glyph}</span><span class="tl"><span class="lvl">Stage {E(str(s.get("order")))}</span> '
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
    tree_note = {MAPPED: "A part shared by several stages counts in each.",
                 MEAS: "A question is one of the standard questions a measure should answer. A part shared by several "
                       "stages counts in each, so the stages add up to more than the flow’s measures.",
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


def render(reg, d):
    reg = pathlib.Path(reg)
    d = dict(d, _title=d.get("capability") or d.get("register") or reg.name)
    counted = counted_at_stand_in(reg)
    flows = [Flow(reg, d, i, f, counted) for i, f in enumerate(d.get("flows") or [])]
    head = ('<div class="trk hd"><span>Flow</span>' + "".join(
        f'<span class="sh"><b>{E(n)}</b><small>{E(q)}</small><small class="out">{E(o)}</small></span>'
        for n, q, o in COLS) + "</div>")
    rows = "".join(row(fl) + "".join(dropdown(fl, p, d) for p in range(len(COLS))) for fl in flows)
    the_map = (f'<a class="go" href="{MAP_FILE}">The map</a>' if (reg / MAP_FILE).is_file()
               else '<span class="off">The map</span>')
    sources = '<a class="go" href="sources.html">Sources</a>' if (reg / "sources.csv").is_file() else ""
    nav = (f'<div class="nav"><span class="sys">{E(d["_title"])}</span><a class="go on" href="{FILE}" '
           f'aria-current="page">Home</a>{the_map}{sources}<span class="sp2"></span></div>')
    blind = ("Found is only what has been found so far; a traced flow shows only what its trace found."
             if any(fl.mapped for fl in flows) else "Found is only what has been found so far.")
    source = f"Drawn from depth.json in the register {d.get('register') or reg.name}. Where the run stands: {d.get('stop')}."
    generated = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n     Source: depth.json in this folder, and "
                 "home.template.html\n     Builder: home.py\n     Build: python home.py <register folder>\n-->")
    page = TEMPLATE.read_text(encoding="utf-8")
    for k, v in (("<!--GENERATED-->", generated), ("<!--TITLE-->", E("Home · " + d["_title"])), ("<!--NAV-->", nav),
                 ("<!--HEAD-->", head), ("<!--ROWS-->", rows), ("<!--BLIND-->", E(blind)),
                 ("<!--SOURCE-->", E(source)), ("<!--FORM-->", form_html(d)), ("<!--CLEAR-->", CLEAR_PAGE)):
        page = page.replace(k, v, 1)
    # the watch compares this stamp, not the first page it fetches, so a redraw before its first check is still seen
    stamp = hashlib.sha256(page.encode("utf-8")).hexdigest()[:16]
    return page.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta name="drawn" content="{stamp}">', 1)


def write(reg):
    reg = pathlib.Path(reg)
    d = json.loads((reg / depth.FILE).read_text(encoding="utf-8"))
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
    return reg / FILE


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) != 1 or not pathlib.Path(argv[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    reg = pathlib.Path(argv[0])
    run_lock.guard(reg)
    if not (reg / depth.FILE).is_file():
        print(f"REFUSED: {reg / depth.FILE} is missing: write it first with depth.py. Nothing written.", file=sys.stderr)
        return 2
    print(f"Written: {write(reg)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
