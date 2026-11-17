"""What the person reads, rendered from the run's files: the status line, the capability brief and the re-entry brief.

Usage: python brief.py status <register folder>       one line; every message to the person opens with it
       python brief.py capability <register folder>   the capability brief for the chat; in full, written to PLAN.md
       python brief.py reentry <register folder>      the re-entry brief, for a run picked up again
       python brief.py terms <file>                   ids and kit terms found in a text (exit 1 if any)
       python brief.py say <register folder> <message file> [--after]
                                                      a message for the person: refused (exit 1) if it uses ids,
                                                      file names or kit terms; else printed after the status line
                                                      and ending with the page's address (--after: a line added
                                                      after a script's message, which has both: neither is added).
                                                      Before a register exists, give the workspace root
       python brief.py checked <register folder>      what was checked of the map, for the report, as the checks
                                                      established it
       python brief.py page <register folder>         the page's address, as a line (the workspace root before a
                                                      register exists)
       python brief.py depth <register folder> <flow id> --recommend "<text>"
       python brief.py depth <register folder> <flow id> --from-request "<their request, verbatim>" [--depth
                    "<id>=measure|alerting|runbooks,..."] [--given "<when>"]
                                                      the pick their request already gave: recorded, said in
                                                      one line, no stop
       python brief.py measures <register folder> <flow id> <stage id>... --recommend "<text>"
                                                      the review of the proposed measures, before any alert
       python brief.py alerts <register folder> <flow id> <stage id>... --recommend "<text>"
       python brief.py next <register folder> --flow "<the flow recommended next>" --recommend "<why>" [--after]
                                                      the offer of the next flow, once this one is finished
                                                      (--after: no status line, after a message that had one)

Reads `RUN.md` (its Status table), `orientation.json` (written by the run from its first, shallow look: the
capability, the services, every flow found with its stages, what was searched and what is open, and a
recommendation), `scope.json` (the person's picks, written by go.py) and `survey.csv`. The capability brief is
refused, and nothing written, while orientation.json is incomplete, names services other than the survey's, recommends
a flow it did not find, or carries an id, a file name or the kit's own vocabulary.
Exit 0 done; 1 refused by `say`, or terms found by `terms`; 2 refused otherwise, or wrong usage.
Python standard library only."""
import contextlib
import csv
from collections import Counter
import io
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import register_layout as layout  # noqa: E402
import run_lock  # noqa: E402

STATUS_LEAD = "**Where things stand:**"
# The capability brief's ask about the searches its "Still open" line proposes: put where the person answers.
SEARCH_ASK = ("If you agree to any search proposed under *Still open*, say which: I search only where you agree, "
              "and show you what was found before reading in depth.")
NEW_RUN = (f"{STATUS_LEAD} not started · Drafted: nothing yet · Next: a first look over the system · "
           "Waiting on you: nothing")
# The run record's phase rows, by their opening words, and the activity each belongs to as the person reads it.
ACTIVITIES = ("Looking over the system", "Describing the flow from the code", "Naming the capability and what to "
              "measure", "Alerts and runbooks for the stages you picked", "Checking against the code and drawing the "
              "map", "Final check and report")
PICKS = "Your pick of the first flow"
REVIEW = 7  # the hold point between the alerts and the runbooks: the person reviews the proposed alerts
DEPTH_PICK = 8  # the hold point after mapping: the person picks how far each stage goes
MEASURES_REVIEW = 9  # the hold point after proposing the measures, before any alert: the person reviews the measures
# Activities 2, 3 and 4 each in two parts (activity number times ten, plus the part), each named for itself, so the
# status line never reports one part as both drafted and next, or as drafted while it is under way.
CASE, STRUCTURE = 21, 22
CAPABILITY, MEASURES = 31, 32
ALERTS, RUNBOOKS = 41, 42
PARTS = {CASE: "Following one piece of work from start to end", STRUCTURE: "Describing the stages, steps and services",
         CAPABILITY: "Naming the capability and what is at stake", MEASURES: "Proposing what to measure",
         ALERTS: "Choosing the alerts for the stages you picked", RUNBOOKS: "Writing the runbooks for those alerts"}
# What each activity leaves made, for the status line's "Drafted": a thing the person can look at, never the activity
# itself (never "Drafted: Looking over the system").
MADE = {1: "the flows found, and where to start", CASE: "where the flow starts, its path and its ends",
        STRUCTURE: "the flow's stages, steps and services", CAPABILITY: "the map of the flow, with what is at stake",
        MEASURES: "what to measure for the stages you picked", 4: "the alerts and runbooks for the stages you picked",
        ALERTS: "the alerts for the stages you picked", RUNBOOKS: "the runbooks for those alerts",
        5: "the map, checked against the code and drawn again", 6: "the report"}
HOLDS = (0, REVIEW, DEPTH_PICK, MEASURES_REVIEW)  # the person's picks and review: never reported as drafted
# What each hold waits on, as the status line's "Waiting on you" says it; the run status page says it in these words too.
WAITS = {0: "your pick of which flow comes first", REVIEW: "your review of the proposed alerts",
         MEASURES_REVIEW: "your review of the proposed measures", DEPTH_PICK: "your pick of how far each stage goes"}
ROWS = (("0 ", 1), ("The go", 0), ("1 ", CASE), ("2 ", STRUCTURE), ("3 ", CAPABILITY),
        ("Pick of how far", DEPTH_PICK), ("4 ", MEASURES), ("Review of the measures", MEASURES_REVIEW), ("5 ", 4),
        ("5a ", ALERTS),
        ("Review of the alerts", REVIEW), ("5b ", RUNBOOKS), ("6 ", 5), ("7 ", 6))
KIT_TERMS = [
    # P50 to P999 are latency percentiles, the alerts' own words, not ids
    (r"\b(?:F|ST|S|R|M|FM|AL|E|D)\d+\b|\bP(?!(?:50|75|90|95|99|999)\b)\d+\b|\bL\d{2,}\b", "an id"),
    (r"\b[\w.-]+\.(?:csv|md|py|json|html|log|ya?ml|java|go|js|ts|xml|properties|toml|txt|sh)\b", "a file name"),
    # a path has a letter in its first part, so a price per month or a date is not one
    (r"\b(?=[\w.-]*[A-Za-z][\w.-]*/)[\w.-]*[-_.][\w.-]*/[\w./-]+|\b(?=[\w.-]*[A-Za-z])[\w.-]+/[\w.-]+/[\w./-]+",
     "a path"),
    (r"\b(?:will|it|this run|the run)\s+(?:describes?|maps?|covers?|walks?)\s+(?:one|a single)\s+(?:business\s+)?"
     r"flow\b(?![^.]*\b(?:batch|remain))", "one flow presented as the whole job"),
    (r"\bregisters?\b", "kit vocabulary"), (r"\bunits?\b", "kit vocabulary"), (r"\bproposed:", "kit vocabulary"),
    (r"\b[Pp]hases?\s*(?:\d+(?:\s*(?:-|–|to|and)\s*\d+)?[a-z]?|zero|one|two|three|four|five|six|seven)\b",
     "kit vocabulary"), (r"\b5[ab]\b", "kit vocabulary"),
    # the run's process words used as nouns: "the go", "the flow go"; "this stop", "the next stop". As verbs ("go on",
    # "stop here", "orders that stop moving") they are ordinary English and pass.
    (r"\b(?:The|the|Your|your|Their|their|This|this) (?:[a-z]*flow )?go\b(?![-/]|\s(?:on|ahead|back|through|over|"
     r"into|to|with|for|out|up|down|away|first|in|off|by|wrong|well|live)\b)", "kit vocabulary"),
    (r"\b(?:The|the|This|this|That|that|[Ee]ach|[Nn]ext|[Ll]ater|[Ee]arlier|[Ww]hich) stop\b"
     r"(?! (?:the|it|them|here|now|working|reading|moving|there)\b| on (?:the|its|a|their|each) (?:\w+ )?(?:route|way|"
     r"line|round|run)\b)", "kit vocabulary"),
    (r"\breceipts?\b", "kit vocabulary"), (r"\b[Ss]tep \d+\b(?! of\b)", "kit vocabulary"),
    # the kit's checkers are "judges"; an AI agent that judges something is ordinary English, as mapping says it
    (r"(?<!\bmodel )(?<!\bagent )(?<!\bassistant )(?<!\bit )(?<!\bthat )(?<!\bwhich )(?<!\bwho )\bjudges?\b",
     "kit vocabulary"),
    (r"\bmerge\b", "kit vocabulary"), (r"\bfact base\b|\bfact-base\b", "kit vocabulary"),
    (r"\bstage-\w+", "kit vocabulary"), (r"\bsubjects?\.|\bparticipation\b", "kit vocabulary"),
]


PAGE_LEAD = "The page for this work: "


def page_line(folder):
    """The page's address, as a line for the person, while a listener serves the work; else "". `folder` is a register
    folder, or the workspace root before a register exists (its work folder's listener is asked)."""
    import listener
    folder = pathlib.Path(folder).resolve()
    work = folder / listener.WORK
    site = work.resolve() if work.is_dir() else listener.site_of(folder)
    url = listener.serving(site)
    if not url:
        return ""
    if (folder / "index.html").is_file():  # the run's home, where its picks wait
        return PAGE_LEAD + url + ("" if site == folder else folder.name + "/") + "index.html"
    return PAGE_LEAD + url + "operator.html"  # else the run status page, the address the start step opened


def with_page(text, folder):
    """`text` with the page's address on a last line of its own while a listener serves the work."""
    line = page_line(folder)
    return f"{text.rstrip()}\n\n{line}" if line else text


def register_names(reg):
    """The names the register gives (flows, stages, steps, parts, measures and the first look's), longest first: the
    business's own words, which the person knows the system by, so `say` lets them through."""
    reg, names = pathlib.Path(reg), set()
    for f in reg.glob("*.csv"):
        if f.name in ("how-made.csv", "sources.csv"):  # the kit's own tables, not the business's names
            continue
        try:
            for row in csv.DictReader(f.open(encoding="utf-8-sig")):
                names |= {(row.get(c) or "").strip() for c in ("name", "measure", "title", "service")}
        except (OSError, csv.Error, UnicodeDecodeError):
            continue
    try:
        o = json.loads((reg / layout.ORIENTATION).read_text(encoding="utf-8-sig"))
        names |= {s.get("name", "") for s in o.get("services") or []}
        for fl in o.get("flows") or []:
            names |= {fl.get("name", "")} | {s.get("name", "") for s in fl.get("stages") or []}
        names.add((o.get("capability") or {}).get("name", ""))
    except (OSError, ValueError, AttributeError):
        pass
    return sorted((n for n in names if n), key=len, reverse=True)


def say_terms(text, reg):
    """The terms check of a message the session wrote, outside what the person knows already: the register's own
    names, words quoted back in double quotes (theirs, as they said them) and a web address."""
    text = re.sub(r"https?://\S+", " ", text)
    # an address without its scheme: a host with a dot or localhost, a port maybe, then a path
    text = re.sub(r"\b(?:localhost|[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,})(?::\d+)?/[^\s,;)]*(?<![.,])", " ", text)
    for n in register_names(reg):  # as written, or with its first letter lower-cased mid-sentence
        text = re.sub("(?i:" + re.escape(n[:1]) + ")" + re.escape(n[1:]), " ", text)
    quoted = re.findall(r'"[^"\n]*"|\u201c[^\u201d\n]*\u201d', text)
    text = re.sub(r'"[^"\n]*"|\u201c[^\u201d\n]*\u201d', " ", text)
    # quoted words are the person's own and pass, except an id, a file name or a path, which are never theirs
    strict = [pat for pat, kind in KIT_TERMS if kind in ("an id", "a file name", "a path")]
    hits = kit_terms(text) + [m.group(0) for q in quoted for pat in strict for m in re.finditer(pat, q)]
    hits += [m.group(0) for m in re.finditer(BOOKKEEPING, text)]
    hits += [m.group(0) + " (say what was checked as brief.py checked prints it)" for m in re.finditer(OVERCLAIM, text)]
    return list(dict.fromkeys(hits))


# A claim about the checks that outruns them ("Placing an order is mapped, checked and done", when only a sample was
# re-read); what was checked is said as `brief.py checked` prints it.
OVERCLAIM = (r"(?i)\b(?:checked and done|fully checked|(?:every|each|all(?: the)?) (?:findings?|rows?|statements?|"
             r"claims?) (?:was |were |is |are |has been |have been )?(?:checked|verified|confirmed))\b")


# The run's own bookkeeping, never said to the person (for example, "The page's watch for your answers is running
# again"; "Phase 6 isn't marked done in the run log yet"). Checked in `say` only: a measure "watches" the business,
# and the reviews the scripts render say so.
BOOKKEEPING = (r"(?i)\b(?:run log|run record|listener|marked (?:as )?(?:done|doing|to do)|"
               r"(?:the|its|a|my|page's) (?:watch|wait|poll)\b(?! (?:on|for) (?:the|a|an|each) (?:order|payment|case|customer))|"
               r"(?:watch|wait|poll) (?:is|was) (?:running|started|restarted|up)\b)")


# A recommendation's reason, shown to the person at a stop (the first look's `why` and every `--recommend`), is one
# short plain sentence: FILL-STEPS says so.
REASON_WORDS = 30
REASON_RULE = "the reason shown to the person must be one short plain sentence"
# a stop that ends an abbreviation, not a sentence
ABBREVIATION = re.compile(r"(?i)\b(?:e\.g|i\.e|etc|vs|cf|incl|approx|a\.m|p\.m)\.$")


def reason_faults(text, reg):
    """What breaks the rule in a recommendation's reason, each with what to change; [] when it holds. The rule: one
    sentence, no semicolon, at most REASON_WORDS words, and no id or kit term that `say` would refuse."""
    t = (text or "").strip()
    out = []
    pieces = []
    for piece in re.split(r"(?<=[.!?])\s+|\n+", t):
        if pieces and ABBREVIATION.search(pieces[-1]):
            pieces[-1] += " " + piece
        elif piece.strip():
            pieces.append(piece)
    if len(pieces) > 1:
        out.append(f"it is {len(pieces)} sentences: keep the one that says why, and drop the rest")
    if ";" in t:
        out.append("it has a semicolon: keep one clause, or join the two with a plain word such as and or because")
    words = len(t.split())
    if words > REASON_WORDS:
        out.append(f"it is {words} words: cut it to {REASON_WORDS} or fewer")
    hits = say_terms(t, reg)
    if hits:
        out.append(f"it uses words the person does not know ({', '.join(hits)}): say each in the person's terms")
    plain = t
    for n in register_names(reg):  # a name the register gives ("Ordering API") is the business's word and passes
        plain = re.sub("(?i:" + re.escape(n[:1]) + ")" + re.escape(n[1:]), " ", plain)
    tech = list(dict.fromkeys(m.group(0) for m in TECHNICAL.finditer(plain)))
    if tech:
        out.append(f"it explains in the code's terms ({', '.join(tech)}): put the reason in the business's terms, "
                   "the flow, the stage, and what the customer or the business would lose")
    return out


# How the code works, said to a business reader (for example, "nothing waits between the calls inside one request")
TECHNICAL = re.compile(r"(?i)\b(?:calls?|requests?|endpoints?|rpcs?|handlers?|(?:a)?synchronous(?:ly)?|async|threads?|"
                       r"payloads?|schemas?|functions?|methods?|modules?)\b")


def refuse_reason(text, reg):
    """Print the refusal of a `--recommend` reason that breaks the rule, and say so; nothing is written before it."""
    faults = reason_faults(text, reg)
    if faults:
        print(f"REFUSED: {REASON_RULE}; " + "; ".join(faults) + ". Rewrite --recommend and run this again. Nothing "
              "written.", file=sys.stderr)
    return bool(faults)


def kit_terms(text):
    """Every id, file name or kit term in `text`, as found."""
    hits = []
    for pattern, _ in KIT_TERMS:
        hits += [m.group(0) for m in re.finditer(pattern, text)]
    return [h for h in hits if not re.fullmatch(r"[A-Z][A-Za-z]*\.js", h)]  # Node.js, Next.js: products, not files


SLOT_CAPITAL = re.compile(r"(?:\b(?:serves|is|are|was|at|for|of|with|by|to)|[:,]) ([A-Z][a-z]+)(?= [a-z])")


def prose_faults(text, names=()):
    """Where filled slots break the prose a newcomer reads: a doubled full stop, or a capitalised common word in
    mid-sentence (after a verb or preposition, a colon or a comma, and followed by a lower-case word, so a proper name
    such as "Sock Shop" passes, as does any of `names`, the names the register itself gives). The status line is not
    prose and is skipped."""
    out = []
    named = tuple(n for n in names if n)
    for line in text.splitlines():
        if line.lstrip("> ").startswith(STATUS_LEAD):
            continue
        out += [f"doubled stop: ...{line[max(0, m.start() - 20):m.end() + 5]}..."
                for m in re.finditer(r"(?<!\.)\.\.(?!\.)", line)]
        out += [f"capital in mid-sentence: ...{line[max(0, m.start() - 10):m.end() + 8]}..."
                for m in SLOT_CAPITAL.finditer(line) if not (named and line[m.start(1):].startswith(named))]
    return out


def cont(s):
    """A slot written as its own sentence, made to continue one: trailing stop dropped, first letter lower-cased unless
    the first word is a name (a capital inside it, or a capitalised word after it)."""
    s = (s or "").strip().rstrip(".")
    words = s.split(" ", 2)
    first = words[0] if words else ""
    name = len(first) > 1 and (any(ch.isupper() for ch in first[1:]) or
                               (len(words) > 1 and words[1][:1].isupper()))
    return s if not s or name else s[0].lower() + s[1:]


def sentence(s):
    """A slot as a whole sentence: first letter upper-cased, one closing stop."""
    s = (s or "").strip().rstrip(".")
    return (s[0].upper() + s[1:] + ".") if s else ""


def rows(p):
    if not p.is_file():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load(reg, name):
    p = reg / name
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.is_file() else None


def scope_now(reg):
    """The record of the flow worked now (go.py's), or None before the go."""
    import go
    return go.load(reg)


def next_ready(reg):
    """The flow worked now is finished, its re-read apart, and the first look found flows still to map."""
    import go
    return bool(flows_left(reg)) and go.run_finished(reg)


def flows_left(reg):
    """The flows the first look found that this register has not started, once a go is recorded."""
    import go
    return go.flows_left(reg) if go.load(reg) is not None else []


def earlier_flows_said(reg):
    """The flows this register finished before the one worked now, each with the person's pick, in their words."""
    import go
    out = []
    for s in go.load_all(reg)[:-1]:
        said = f"*{s.get('flow', '')}*"
        if s.get("depth"):
            said += f", where the pick decided: {depth_said(reg, s['depth'], '*')}"
            words = (s.get("depth_picked") or {}).get("words")
            said += f" (in those words: \"{words}\")" if words else ""
        out.append(said)
    return ("Flows finished before this one, kept in this map: " + "; ".join(out) + ". ") if out else ""


def phases(reg):
    """[(activity number, 0 for the person's picks), status] from RUN.md's Status table, in order."""
    p = reg / "RUN.md"
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(cells) >= 2:
            for lead, act in ROWS:
                if cells[0].startswith(lead):
                    status = cells[1].lower()
                    if lead.startswith("7 ") and status == "done" and not done_check_holds(reg):
                        status = "doing"  # the done check has not said DONE on the map as it is
                    out.append((act, status))
                    break
    return _mapping_from_case(reg, out)


import case  # noqa: E402

CASE_ENDED = case.ENDED
STRUCTURE_SUBS = ("units", "readers", "merge", "re-reads")


def case_flow(reg):
    """The case record's entry for the flow worked now, or None: run control keeps mapping's phases there."""
    import case
    flows = case.load(reg)["flows"]
    if not flows:
        return None
    name = ((scope_now(reg) or {}).get("flow") or "").strip().lower()
    for r in rows(reg / "flows.csv"):
        fid = (r.get("flow_id") or "").strip()
        if name and (r.get("name") or "").strip().lower() == name and fid in flows:
            return flows[fid]
    mapping = [f for f in flows.values() if f.get("state") == "mapping"]
    return mapping[0] if len(mapping) == 1 else None


def checks_stopped(reg):
    return (case_flow(reg) or {}).get("state") == CASE_ENDED


def _mapping_from_case(reg, ph):
    """Phases 1 to 3 as the case record says, in place of the run record's rows for them."""
    f = case_flow(reg)
    if not f:
        return ph
    st, sub = f.get("state"), f.get("sub")
    if st in ("mapped", CASE_ENDED):
        now = {CASE: "done", STRUCTURE: "done", CAPABILITY: "done"}
    elif st == "mapping" and sub in STRUCTURE_SUBS:
        now = {CASE: "done", STRUCTURE: "doing", CAPABILITY: "to do"}
    elif st == "mapping" and sub and sub != "lead steps":
        now = {CASE: "done", STRUCTURE: "done", CAPABILITY: "doing"}
    elif st == "mapping":
        now = {CASE: "doing", STRUCTURE: "to do", CAPABILITY: "to do"}
    else:
        return ph
    return [(a, now.get(a, s)) for a, s in ph]


def done_check_holds(reg):
    """Phase 7, the run's close, is done when the done check says DONE on the map as it is and every flow's report
    is sent (each once its own re-read has passed) with no correction to that flow applied since."""
    import go
    import run_status
    reg = pathlib.Path(reg)
    if not run_status.verdict_holds(reg):
        return False
    return all(run_status.report_current(reg, s) for s in go.load_all(reg))


MAPPING_ACTIVITIES = 3  # the mapping skill run alone: the first look, describing the flow, the capability and its impact


def activity_count(reg):
    """How many activities the person was told there are: three when the mapping skill started the run on its own,
    six when the stage kit did (start.py records which, in the work folder). `reg` is a register folder, or the
    workspace root before a register exists, whose work folder holds the record."""
    reg = pathlib.Path(reg)
    record = reg / "bfo-work" / "run-started.json"
    try:
        d = json.loads((record if record.is_file() else reg.parent / "run-started.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return len(ACTIVITIES)
    return MAPPING_ACTIVITIES if d.get("skill") == "mapping" else len(ACTIVITIES)


def name(act, count=len(ACTIVITIES)):
    if act == REVIEW:
        return "Your review of the alerts"
    if act == MEASURES_REVIEW:
        return "Your review of the measures"
    if act == DEPTH_PICK:
        return "Your pick of how far each stage goes"
    if act in PARTS:
        return f"Activity {act // 10} of {count}: {PARTS[act]}"
    return PICKS if act == 0 else f"Activity {act} of {count}: {ACTIVITIES[act - 1]}"


def short(act):
    if act == REVIEW:
        return "your review of the alerts"
    if act == MEASURES_REVIEW:
        return "your review of the proposed measures"
    if act == DEPTH_PICK:
        return "your pick of how far each stage goes"
    if act in PARTS:
        return PARTS[act]
    return PICKS.lower() if act == 0 else ACTIVITIES[act - 1]


def made(act):
    """What an activity left made, as the status line's Drafted field says it."""
    return MADE.get(act) or short(act)


def state(reg):
    """(current activity, last activity the run drafted, the one after current, blocked) from the run record. The
    person's picks and review are never the last drafted: they are the person's, not the run's."""
    ph = phases(reg)
    if not ph:
        return None
    passed = ("done", "not picked")  # a phase the person's pick left out is passed over, never waited on
    current = next(((a, s) for a, s in ph if s not in passed), None)
    done = [a for a, s in ph if s == "done" and a not in HOLDS]
    last = done[-1] if done else None
    if current is None:
        return None, last, None, False
    at = next(i for i, (a, s) in enumerate(ph) if s not in passed)
    after = next((a for a, s in ph[at + 1:] if a != current[0] and s != "not picked"), None)
    return current[0], last, after, current[1] == "blocked"


NEXT_STOP = "draft complete; next comes the next flow"  # an open case with its next step, never a wait on the person


def at_next_flow(reg, current):
    """The run is at the next flow: this flow is done (or finished but for its re-read and report) and the first look
    found flows still to map. That is an open case whose next step is the next flow, offered with the recommendation;
    it never waits on the person: an unfinished case is not activity in motion."""
    import go
    return current is None or bool(flows_left(reg) and go.run_finished(reg))


def where_it_stands(reg):
    """(the activity now, or None; where the run stands as the person reads it), from the one decision the status line
    makes too: the next flow as what comes next, a draft complete, a phase blocked, or the phase now."""
    st = state(reg)
    if st is None:
        return None, "not started"
    current, _, _, blocked = st
    if at_next_flow(reg, current):
        return current, (NEXT_STOP if flows_left(reg) else "draft complete")  # never "finished"
    return current, short(current) + (": blocked" if blocked else "")


DEPTH_WORDS = {"none": "mapped only", "measure": "measured", "alerting": "measured, with alerts",
               "runbooks": "measured, with alerts and runbooks"}


def depth_said(reg, depth, mark=""):
    """The person's pick of how far each stage goes, by stage name: the stages taken past mapping, then the rest."""
    names = {(r.get("stage") or "").strip(): (r.get("name") or "").strip() for r in rows(reg / "stages.csv")}
    taken = [f"{mark}{names.get(s) or s}{mark} {DEPTH_WORDS.get(d, d)}" for s, d in depth.items() if d != "none"]
    rest = "every stage mapped only" if not taken else "the rest mapped only"
    return "; ".join(taken + [rest]) if len(taken) < len(depth) else "; ".join(taken)


def and_list(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def mapped_stages(reg, flow_name):
    """The stage names the walk recorded for the flow the person picked, in order: the flow named so in flows.csv, else every
    stage when the register has one flow's stages only."""
    ids = {(r.get("flow_id") or "").strip() for r in rows(reg / "flows.csv")
           if (r.get("name") or "").strip().lower() == (flow_name or "").strip().lower()}
    st = [r for r in rows(reg / "stages.csv") if (r.get("name") or "").strip()]
    if ids:
        st = [r for r in st if (r.get("flow") or "").strip() in ids]
    elif len({(r.get("flow") or "").strip() for r in st}) > 1:
        return []
    st.sort(key=lambda r: int(r.get("order") or 0) if str(r.get("order") or "").strip().isdigit() else 0)
    return [r["name"].strip() for r in st]


def measures_skill():
    """True when this copy of the script is the measures skill's (its folder holds MEASURES-STEPS.md and not the stage
    kit's FILL-STEPS.md): its status line then speaks of that skill's own work, never of the kit's six activities."""
    here = pathlib.Path(__file__).resolve().parent
    return (here / "MEASURES-STEPS.md").is_file() and not (here / "FILL-STEPS.md").is_file()


MEASURES_NEXT = "the alerts for those stages, chosen with the stage kit"


def measures_status(reg, flow, stage):
    """The status line of the measures skill run alone: where it stands among its own steps (the pick of the stages to
    measure, proposing the measures, the person's review of them), read from the same run record."""
    ph = dict(phases(reg))
    # read from what is done, never from what is passed over: on a register the mapping skill finished, the pick and
    # every later phase are "not picked" (and a release before the review had no review row), which is the pick
    if ph.get(CAPABILITY) not in ("done",):
        now, drafted, nxt, waiting = ("Waiting for the flow to be mapped", "nothing yet", "the pick of the stages to "
                                      "measure", "nothing")
    elif ph.get(DEPTH_PICK) != "done" or ph.get(MEASURES) == "not picked":
        now, drafted, nxt, waiting = ("Your pick of the stages to measure", "nothing yet", "the measures for the stages "
                                      "you pick", "your pick of which stages to measure")
    elif ph.get(MEASURES) != "done":
        now, drafted, nxt, waiting = ("Proposing the measures for the stages you picked", "nothing yet",
                                      "your review of the proposed measures", "nothing")
    elif ph.get(MEASURES_REVIEW) != "done":
        now, drafted, nxt, waiting = ("Your review of the measures", "the measures for the stages you picked",
                                      MEASURES_NEXT, "your review of the proposed measures")
    else:
        now, drafted, nxt, waiting = ("The measures reviewed", "the measures for the stages you picked",
                                      MEASURES_NEXT, "nothing")
    return f"{STATUS_LEAD} Flow: {flow} · Stage: {stage} · {now} · Drafted: {drafted} · Next: {nxt} · Waiting on you: {waiting}"


def status(reg):
    st = state(reg)
    count = activity_count(reg)
    if st is None and measures_skill():
        st = (None, None, None, False)  # no run record: the measures skill's own line still says where it stands
    if st is None:
        return NEW_RUN.replace("not started", f"Activity 1 of {count}: not started")
    current, last, after, blocked = st
    scope = scope_now(reg) or {}
    flow = scope.get("flow") or "not chosen yet"
    stages = scope.get("stages") or []
    stage = ", ".join(stages) if isinstance(stages, list) and stages else (stages or "not chosen yet")
    if scope.get("flow") and not stages:  # the go picks only the flow; the stages are picked after mapping
        stage = "picked once the flow is mapped"
        mapped = mapped_stages(reg, scope["flow"])
        if mapped and (STRUCTURE, "done") in phases(reg):
            stage = f"mapped as {and_list(mapped)}" + (
                "" if (DEPTH_PICK, "not picked") in phases(reg) else "; how far each goes is yours to pick")
    if scope.get("depth"):  # once the person has picked how far each stage goes, that is what the run does
        stage = depth_said(reg, scope["depth"])
    if measures_skill():
        return measures_status(reg, flow, stage)
    # The line is short and every field it shows says something: a flow or stage not chosen yet, and the stages
    # before the person's pick (the message shows them), are left out (a field that says nothing reads as
    # noise).
    if not scope.get("depth") and not (isinstance(stages, list) and stages):
        stage = ""
    flow = "" if flow == "not chosen yet" else flow
    lead = STATUS_LEAD + "".join(f" {k}: {v} ·" for k, v in (("Flow", flow), ("Stage", stage)) if v)
    if at_next_flow(reg, current):
        left = flows_left(reg)  # the flow is done; the first look found more, added to this map one at a time
        import run_status
        pending = "" if current is None or run_status.own_reread_passed(reg) else "; its re-read pending"
        return (f"{lead} Draft complete{pending}, for your review · Drafted: {drafted_said(reg, last)} · Next: "
                + ("the next flow · Waiting on you: nothing" if left else "nothing · Waiting on you: nothing"))
    waiting = "the run is blocked; the message below says why" if blocked else WAITS.get(current, "nothing")
    if after is not None:
        nxt = short(after)
    elif current == len(ACTIVITIES):  # the last activity is the report itself: next is what follows it
        nxt = "the next flow" if flows_left(reg) else "nothing more: this is the last step"
    else:
        nxt = "the report"
    # while it waits on the person, the activity would only repeat what it waits on
    now = "" if waiting != "nothing" and not blocked and current in HOLDS else f" {name(current, count)} ·"
    return f"{lead}{now} Drafted: {drafted_said(reg, last)} · Next: {nxt} · Waiting on you: {waiting}"


def drafted_said(reg, last):
    """The status line's Drafted field: what the last activity left made, and that the map is not checked when the
    person stopped its checks, wherever the run then waits."""
    drafted = made(last) if last is not None else "nothing yet"
    if checks_stopped(reg):
        drafted += (", not checked: you stopped the checks" if last == CAPABILITY
                    else "; the map not checked: you stopped the checks")
    return drafted


REQUIRED = {"activity": ("for", "this_run"), "capability": ("name", "what", "for_whom"),
            "recommendation": ("flow", "why", "remains")}


def problems(reg, o, brief_now=False):
    """What stops the brief rendering. `brief_now`: the capability brief, which also needs each flow's own case (a
    re-entry brief of a register written before that renders without it)."""
    if o is None:
        return ["orientation.json is missing"]
    out = []
    for part, keys in REQUIRED.items():
        for k in keys:
            if not (o.get(part) or {}).get(k):
                out.append(f"{part}.{k} is empty")
    flows = o.get("flows") or []
    if not flows:
        out.append("no flow found")
    for f in flows:
        if not (f.get("name") and f.get("what")):
            out.append(f"a flow without a name or a sentence: {f.get('name', '?')}")
        if brief_now and not f.get("one_case"):
            out.append(f"flow {f.get('name', '?')}: one_case is empty (what one case of this flow is)")
        if not f.get("stages") or not all(s.get("name") and s.get("what") for s in f["stages"]):
            out.append(f"flow {f.get('name', '?')}: every flow needs its stages, each with a sentence")
    names = [f.get("name") for f in flows]
    rec = o.get("recommendation") or {}
    if rec.get("flow") and rec["flow"] not in names:
        out.append(f"the recommended flow {rec['flow']!r} is not a flow found")
    if brief_now and rec.get("why"):
        out += [f"recommendation.why: {REASON_RULE}; {f}" for f in reason_faults(rec["why"], reg)]
    for k in ("stages_for_alerts", "stages_why"):
        if rec.get(k):
            out.append(f"recommendation.{k}: the first look recommends a flow, not stages for alerts; the person picks "
                       "how far each stage goes once the flow is mapped, so remove it")
    surveyed = {r["service"].strip() for r in rows(reg / "survey.csv")
                if (r.get("kind") or "").strip() == "service" and (r.get("service") or "").strip()}
    given = {s.get("name") for s in o.get("services") or []}
    if given != surveyed:
        missing, extra = sorted(surveyed - given), sorted(given - surveyed)
        out.append("services must be the survey's, each once" + (f"; missing: {', '.join(missing)}" if missing else "")
                   + (f"; not in the survey: {', '.join(extra)}" if extra else ""))
    for s in o.get("services") or []:
        if s.get("recommend") not in ("in", "out") or not s.get("does") or not s.get("why"):
            out.append(f"service {s.get('name')}: needs what it does, recommend in or out, and why")
    if not o.get("searched"):
        out.append("searched is empty")
    text = json.dumps({k: v for k, v in o.items() if k != "flows"}, ensure_ascii=False) + " ".join(
        json.dumps({k: v for k, v in f.items() if k != "found_in"}, ensure_ascii=False) for f in flows)
    text = text.replace('"name"', "")
    hits = [h for h in kit_terms(text) if h not in surveyed]
    if hits:
        out.append(f"ids, file names or kit terms in the person's text: {', '.join(sorted(set(hits)))}")
    return out


def bullets(items):
    return "\n".join(f"- {i}" for i in items)


def checks_said(reg):
    """What this run does to check its findings against the code, as the person reads it: every run reads in units
    and has every finding that cites code checked by independent readers, at the count the go records."""
    n = (load(reg, layout.SETTINGS) or {}).get("judges", 3)
    return (f"I will have {n} independent checks read each finding against the code, each by a reader who wrote none "
            "of it; a finding they doubt is corrected and checked again, and one still in doubt is shown as not "
            "confirmed by the code. Three is the kit's default.")


# how each kind of fix of a doubted finding is said to the person (judges.FIX_CLASSES), in that order
FIX_WORDS = (("claim narrowed", "narrowed to what the code shows"), ("citation changed", "given the right lines"),
             ("relabelled proposed", "marked as not shown by the code"), ("citation dropped", "left with no lines cited"),
             ("withdrawn", "withdrawn"), ("unchanged", "kept as written"))


def fix_kinds(reg):
    """{(unit, table, row): kind} of every finding a round before the last doubted, from the round record
    (judges.classify_fixes); a finding with no round record is left out."""
    import judges
    reg = pathlib.Path(reg)
    rounds = int((load(reg, layout.SETTINGS) or {}).get("judge_rounds", 2))
    out = {}
    for unit in judges._units(reg):
        for rnd in range(1, rounds):
            for (table, row), kind in judges.classify_fixes(reg, unit, rnd).items():
                if not kind.startswith("not classified"):
                    out.setdefault((unit, table, row), kind)
    return out


def checks_found(reg):
    """What the checks of the findings found, as the person reads it after mapping, from judging/judgements.csv
    (judges.py collect) and the round record: how many findings were checked and by how many readers, how many were
    doubted and how each was fixed, by kind, and how many are still in doubt; '' before any were collected."""
    p = reg / layout.JUDGEMENTS_CSV
    if not p.is_file():
        return ""
    got = rows(p)
    if not got:
        return ""
    if checks_stopped(reg):
        return (f"**How the findings were checked.** You stopped the checks before they finished, so this map is not "
                f"checked against the code: of the {len(got)} findings that cite code, any not read through every "
                "round is not checked.")
    n = (load(reg, layout.SETTINGS) or {}).get("judges", 3)
    kinds = fix_kinds(reg)
    doubted = {(r.get("unit"), r.get("table"), r.get("row")) for r in got
               if (r.get("state") or "") in ("flagged", "disputed") or int(r.get("round") or 1) > 1} | set(kinds)
    disputed = sum(1 for r in got if (r.get("state") or "") == "disputed")
    d = len(doubted)
    count = Counter(kinds.values())
    how = ", ".join(f"{count[k]} {w}" for k, w in FIX_WORDS if count[k])
    return (f"**How the findings were checked.** Each of the {len(got)} findings that cite code was read against its "
            f"code by {n} readers who wrote none of it. {d} {'was' if d == 1 else 'were'} doubted"
            + (f" ({how})" if how else "") + f", and every one still on the map was checked again; {disputed} "
            f"{'is' if disputed == 1 else 'are'} still in doubt and {'is' if disputed == 1 else 'are'} shown as not "
            "confirmed by the code.")


def checked_said(reg):
    """What was checked of the map, in the past tense, for the report: exactly what the checks established, never
    more (never "mapped, checked and done" when only a sample was re-read).
    Each line is what a check of the kit verified: the sampled re-read (or, in a split run, every row judged) and the
    reading check against Claude Code's own record of the sessions."""
    import reading_check
    import reread
    out = []
    if checks_stopped(reg):
        out.append("You stopped the checks before they finished, so the map is not checked against the code: any "
                   "finding not read through every round is not checked.")
    elif (reg / layout.UNITS_CSV).is_file():
        n = (load(reg, layout.SETTINGS) or {}).get("judges", 3)
        out.append(f"Each finding was read against the code by {n} independent checks.")
    else:
        held = reread.check(reg).passed
        out.append("A reader who wrote none of the findings re-read a sample of ten of them against the code, "
                   + ("and every one of the ten held" if held else "and not every one of the ten holds yet")
                   + "; the other findings were not checked one by one.")
    reading = reading_check.check(reg)
    if reading.passed and reading.cited:
        by_run = reading.covered - reading.by_reader
        out.append(f"Claude Code's own record of the work shows every place in the code the map cites was read: "
                   f"{by_run} opened by the run" + (f", and {reading.by_reader} found by the code reader, which reads "
                                                     "the code by rule" if reading.by_reader else "") + ".")
    return "\n".join(out)


def unread(reg):
    """The capability brief's line on files of the code that could not be read, as one more item, or nothing."""
    import map_record
    line = map_record.unread_line(reg)
    return f"\n- Not read: {line}" if line else ""


def case_said(x):
    """What one case is, for a flow (or, in a register written before each flow said its own, the capability), as a
    sentence after a space; nothing when it is not given (the case is the flow's, never fixed for the whole
    capability before a flow is picked)."""
    return f" One case, the thing followed from start to end, is {cont(x['one_case'])}." if x.get("one_case") else ""


def request_given(reg, given):
    """The request to record from: the words given, else the request the run record keeps (start.py --request)."""
    import start
    return (given or "").strip() or start.request_of(reg)


def take_request(args):
    """(args without `--from-request` and its words, the words or "" when none follow, or None when absent)."""
    if "--from-request" not in args:
        return args, None
    i = args.index("--from-request")
    has = i + 1 < len(args) and not args[i + 1].startswith("--")
    return args[:i] + args[i + (2 if has else 1):], (args[i + 1] if has else "")


def go_from_request(reg, flow, request):
    """The go on `flow`, recorded with the person's request as its words, when the request already asked for every
    flow: "" when recorded, else go.py's refusal."""
    import go
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        rc = go.main([str(reg), "--flow", flow, "--words", request, "--source", "request"])
    return "" if rc == 0 else err.getvalue().strip().removeprefix("REFUSED: ").removesuffix(" Nothing written.")


def capability(reg, o, request=None):
    """The first-look brief as the person reads it in the chat: the one thing asked with the recommendation first,
    then what a yes does, then what the first look found, as lists. The rest (every flow's stages, each service and
    why it is read or left out, what was looked at and what is still open) is the full plan, `capability_full`,
    written to PLAN.md and shown when the person asks."""
    c, r = o["capability"], o["recommendation"]
    services = o.get("services") or []
    n_in = sum(s.get("recommend") == "in" for s in services)
    open_ = o.get("unresolved") or []
    flows = bullets(f"*{f['name']}*" for f in o["flows"])
    also = ["Start with another of these flows instead." if request else "Pick another of these flows to start with.",
            "Change which services are read."]
    if open_:
        also.append(f"{count_word(len(open_)).capitalize()} question{'s are' if len(open_) != 1 else ' is'} still "
                    "open about the system. Where one proposes a search, I search only if you agree.")
    if request:
        lead = (f"**Your request asked for every flow, so I'm starting with *{r['flow']}*, and I'll add the others "
                f"one at a time after it.** {sentence(r['why'])}")
        doing, also_head = "What I'm doing now:", "**You can stop me, or change this, at any time:**"
        after_map = ("Once the flow is mapped, I show you its stages, each taken as far as your request said, or "
                     "I ask you how far.")
    else:
        lead = f"**Which flow should I map first? I recommend *{r['flow']}*.** {sentence(r['why'])}"
        doing, also_head = "If you say yes:", "**You can also:**"
        after_map = ("Once the flow is mapped, I show you its stages. How far each goes is yours to say: mapped only, "
                     "or on to measures, alerts and runbooks.")
    return f"""{status(reg)}

{lead}

{doing}
- I read the code of {count_word(n_in)} of the system's {count_word(len(services))} services and leave the others out.
- {checks_said(reg)}
- {after_map}

**What the first look found.** {sentence(c['what'])} The business flows found so far:
{flows}

A flow not found here may still exist.{unread(reg)}

{also_head}
{bullets(also)}

Each flow's stages, each service and why it is read or left out, and the open questions are in the full plan: ask me for it.
"""


def capability_full(reg, o):
    """The first-look brief in full, for PLAN.md: the plan the person oversees, shown when they ask for it."""
    c, a, r = o["capability"], o["activity"], o["recommendation"]
    flows = []
    for i, f in enumerate(o["flows"], 1):
        stages = "\n".join(f"   - *{s['name']}*: {cont(s['what'])}." for s in f["stages"])
        flows.append(f"{i}. **{f['name']}.** {sentence(f['what'])}{case_said(f)} Its stages:\n{stages}")
    services = "\n".join(f"- **{s['name']}** {cont(s['does'])}. Recommended: "
                         f"{'include' if s['recommend'] == 'in' else 'leave out'}. {sentence(s['why'])}"
                         for s in o["services"])
    earlier = f"\n**Earlier maps.** {sentence(o['earlier'])}\n" if o.get("earlier") else ""
    n = len(o["flows"])
    batch = ("" if "batch" in a["this_run"].lower() else
             " One run maps one flow, so this run is one batch of the job, and the rest remains for later runs.")
    return f"""{status(reg)}

**What this work is.** {sentence(a['for'])} The job is the whole capability: every business flow it carries, each with its stages. {sentence(a['this_run'])}{batch}
{earlier}
**{c['name']}, in brief.** {sentence(c['what'])} It serves {cont(c['for_whom'])}.{case_said(c)}

**The business flows found so far: {n}.** These come from a first look at the system's entry points and documents. A flow not found here may still exist.

{chr(10).join(flows)}

**What was looked at, and what is still open.**
- Looked at: {'; '.join(cont(x) for x in o['searched'])}.
- Still open: {'; '.join(cont(x) for x in o.get('unresolved') or ['nothing known'])}.{unread(reg)}

**The services, and which to include.** A service left out is not read; a call into it is noted as outside this run.

{services}

**Where to start.** Start with *{r['flow']}*: {cont(r['why'])}. What remains of the job after this run: {cont(r['remains'])}.

**What I will do unless you say otherwise.** I will read the services marked include above and leave out the others. {checks_said(reg)} Once the flow is mapped, I will show you its stages, and you pick how far each one goes: mapped only, measured, measured with alerts, or measured with alerts and then runbooks.

**What I need from you.** Nothing is read in depth until you answer.
1. Which flow to start with. Recommended: *{r['flow']}*.
{SEARCH_ASK + chr(10) if o.get('unresolved') else ''}"""


def reentry(reg, o):
    c, a = o["capability"], o["activity"]
    scope = scope_now(reg)
    st = state(reg)
    # what the run drafted; the person's picks and review are reported under what was decided, never as the run's work
    done = [cont(made(x)) for x, s in phases(reg) if s == "done" and x not in HOLDS]
    done = list(dict.fromkeys(done))
    found = "; ".join(f"*{f['name']}* ({len(f['stages'])} stage{'s' if len(f['stages']) != 1 else ''})"
                      for f in o["flows"])
    if scope:
        who = "a test standing in for you" if scope.get("test") else "you"
        stages = scope.get("stages") or []
        stages = ", ".join(f"*{x}*" for x in stages) if isinstance(stages, list) else f"*{stages}*"
        earlier = f"; alerts and runbooks for: {stages}" if stages else ""  # a run whose go still picked stages
        decided = (f"On {scope.get('given', 'an earlier day')}, {who} chose" if who != "you" else
                   f"On {scope.get('given', 'an earlier day')}, you chose") + (
            f" the flow *{scope.get('flow')}*{earlier}. In those words: \"{scope.get('words', '')}\" The services "
            f"read: {', '.join(scope.get('services_in') or [])}; left out: "
            f"{', '.join(scope.get('services_out') or []) or 'none'}.")
        if scope.get("depth"):
            p = scope.get("depth_picked") or {}
            if p.get("from_request"):
                decided += (" Then, because your request said how far each stage goes, that was recorded from it, "
                            f"on {p.get('given', 'an earlier day')}, and it decides: "
                            f"{depth_said(reg, scope['depth'], '*')}.")
            else:
                decided += (f" After the flow was mapped, {'a test standing in for you' if p.get('test') else 'you'} "
                            f"picked how far each stage goes, on {p.get('given', 'an earlier day')}, and that pick "
                            f"decides: {depth_said(reg, scope['depth'], '*')}.")
            decided += f" In those words: \"{p['words']}\"" if p.get("words") else ""
        rem = dict(scope.get("remains") or {})
        if scope.get("depth"):  # after the person's pick, the stages left without alerts are those it leaves below alerting
            names = {(r.get("stage") or "").strip(): (r.get("name") or "").strip() for r in rows(reg / "stages.csv")}
            rem["stages_without_alerts"] = [names.get(s) or s for s, d in scope["depth"].items()
                                            if d not in ("alerting", "runbooks")]
        remains = "; ".join(x for x in (
            ("other flows: " + ", ".join(f"*{x}*" for x in rem["flows"])) if rem.get("flows") else "",
            ("stages with no alerts yet: " + ", ".join(f"*{x}*" for x in rem["stages_without_alerts"]))
            if rem.get("stages_without_alerts") else "",
            ("services left out: " + ", ".join(rem["services_left_out"])) if rem.get("services_left_out") else "") if x)
    else:
        decided = "Nothing has been decided yet: the run is waiting for your pick of the first flow on the capability brief."
        remains = ""
    current, last, after, _ = st if st else (1, None, None, False)
    where = (f"The run stopped at {name(current, activity_count(reg)).lower() if current else 'the end'}"
             + (f", after {cont(short(last))}." if last is not None else "."))
    line = status(reg)
    nxt = cont(line.split("Next: ", 1)[1].split(" · ")[0])
    waits = line.split("Waiting on you: ", 1)[1]
    open_case = next_ready(reg)  # coming back to a finished flow with flows still to map: an open case, not a wait
    import go
    on_page = open_case and ((load(reg, "depth.json") or {}).get("open_choice") or {}).get("task") == go.NEXT_TASK
    if open_case:
        # the next flow is what is next, offered with the recommendation the record holds, never a wait on the person; the
        # page is named as one place to choose it only where Home draws the pick
        tail = "\n**The flows still to add to this map.** " + "; ".join(f"*{n}*" for n in flows_left(reg)) + ".\n"
        rec = next_flow_recommended(reg) or (o.get("recommendation") or {})
        where = "on the page or here in the chat" if on_page else "here in the chat"
        if rec.get("flow") in flows_left(reg):
            why = (rec.get("why") or "").strip()
            tail += f"\n**My recommendation.** Next: *{rec['flow']}*." + (f" {sentence(why)}" if why else "") + "\n"
            tail += f"\nSay carry on and I will map *{rec['flow']}*, or name another flow {where}."
        else:
            tail += f"\nName the flow to map next {where}."
        tail += " Or say stop, and this map stays as it is, with those flows still to add.\n"
    elif state(reg) and state(reg)[0] == DEPTH_PICK and (reg / PICK_FILE).is_file():
        # Waiting on the person's pick of how far each stage goes: the stages again, as last put to them
        tail = "\n**The stages you were asked to pick from, again.**\n\n" + shown_again(reg, PICK_FILE)
    elif not scope:
        # Waiting on the person's picks: give them what they pick from again, not a pointer to an old message.
        tail = "\n**What you were asked to pick from, again.**\n\n" + capability(reg, o).split("\n", 2)[2]
    elif state(reg) and state(reg)[0] == MEASURES_REVIEW and (reg / MEASURES_REVIEW_FILE).is_file():
        # Waiting on the person's review of the measures: the measures again, as last put to them
        tail = "\n**The measures you were asked to review, again.**\n\n" + shown_again(reg, MEASURES_REVIEW_FILE)
    elif state(reg) and state(reg)[0] == REVIEW and (reg / REVIEW_FILE).is_file():
        # Waiting on the person's review of the alerts: the alerts again, as last put to them, without their old status line
        tail = "\n**The alerts you were asked to review, again.**\n\n" + shown_again(reg, REVIEW_FILE)
    elif waits == "nothing":
        tail = f"\nShall I carry on with {nxt}? I recommend yes.\n"
    else:
        tail = ""
    after_run = (' What remains after this run: ' + remains + '.') if remains else ''
    upcoming = (f"**What is next.** Next comes {nxt}: one of the flows below.{after_run}" if open_case else
                f"**What is next, and what waits on you.** Next comes {nxt}. Waiting on you: {waits}.{after_run}")
    return f"""{line}

**What this work is.** {sentence(a['for'])} The job is the whole capability: every business flow it carries, each with its stages. {sentence(a['this_run'])} One run maps one flow, so each run is one batch of the job.

**{c['name']}, in brief.** {sentence(c['what'])} It serves {cont(c['for_whom'])}.{case_said(c)}

**Drafted and found so far.** {('Drafted so far: ' + '; '.join(done) + '. ') if done else 'Nothing past the first look is drafted yet. '}Flows found on the first look: {found}.

**Decided, and by whom.** {earlier_flows_said(reg)}{decided}

**Where it stands.** {where}

{upcoming}
{tail}"""


def mark_the_stop(reg):
    """The brief is the stop: RUN.md's first phase done and the go row doing, so the status line waits on the person's picks."""
    p = reg / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"^(\| 0 [^|]*\| )[^|]*\|", r"\1done |", text, count=1, flags=re.M)
    text = re.sub(r"^(\| The go on the plan \| )(?:to do|doing) \|", r"\1doing |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


# What phase 0 leaves, in the order RUN.md's *What this run will produce* names them: those present prove it done.
FIRST_LOOK_FILES = ("sources.csv", "about.csv", "how-made.csv", "survey.csv", "fact-base.json", "orientation.json",
                    "PLAN.md")


def record_first_look(reg):
    """Phase 0 ends at the brief: RUN.md's phase 0 row names the files that prove it (when its cell is still blank: a
    run's own words there are kept), and *Sources*, written by now, keeps none of the template's text under a bullet
    the run has written."""
    import go
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    proof = "; ".join(n for n in FIRST_LOOK_FILES if (pathlib.Path(reg) / n).is_file())
    text = go.proved_by(text, "0 ", proof) if proof else text
    p.write_text(sources_without_template(text), encoding="utf-8", newline="\n")


def section_span(text, title):
    """(start, end) of a RUN.md section's body, after its heading line, or None."""
    m = re.search(rf"^## {re.escape(title)}[ \t]*$", text, re.M)
    if not m:
        return None
    end = re.search(r"^## ", text[m.end():], re.M)
    return m.end(), m.end() + end.start() if end else len(text)


def template_bullets(body):
    """{a bullet's label: (its first line, [its continuation lines])} for each bullet of a section's body."""
    out, label = {}, None
    for line in body.splitlines():
        if line.startswith("- ") and ":**" in line:
            label = line.split(":**")[0]
            out[label] = (line, [])
        elif line.startswith("  ") and label:
            out[label][1].append(line)
        else:
            label = None
    return out


def sources_without_template(text):
    """RUN.md's text with each template continuation line dropped from under a *Sources* bullet whose first line the
    run has rewritten: replacing only a bullet's first line leaves the template's next line standing. The template is
    the one beside this script, as the kit built it; a bullet still as the template wrote it stays whole."""
    tpl = pathlib.Path(__file__).resolve().parent / "register-template" / "RUN.md"
    span = section_span(text, "Sources")
    t = tpl.read_text(encoding="utf-8") if tpl.is_file() else ""
    tspan = section_span(t, "Sources")
    if not span or not tspan:
        return text
    bullets = template_bullets(t[tspan[0]:tspan[1]])
    kept, drop = [], ()
    for line in text[span[0]:span[1]].split("\n"):
        if line.startswith("- "):
            first, cont = bullets.get(line.split(":**")[0], (line, []))
            drop = cont if line != first else ()
        elif not line.startswith("  "):
            drop = ()
        elif line in drop:
            continue
        kept.append(line)
    return text[:span[0]] + "\n".join(kept) + text[span[1]:]


REVIEW_FILE = "alert-review.md"  # the last review message rendered, shown again on re-entry at the review
MEASURES_REVIEW_FILE = "measures-review.md"  # the same, for the review of the measures
FLOWS_FILE = "flows-brief.md"  # the last capability brief sent to the chat: what the flow pick answers
PICK_FILE = "depth-pick.md"  # the last pick message rendered, shown again on re-entry at the pick


def shown_again(reg, name):
    """A message the kit wrote at a stop, as the re-entry brief shows it again: without its old status line; "" if
    there is none."""
    p = pathlib.Path(reg) / name
    return p.read_text(encoding="utf-8").split("\n", 2)[2] if p.is_file() else ""
NEXT_FILE = "next-flow.md"  # the last next-flow message rendered, shown again on re-entry at that stop
NEXT_JSON = "next-flow.json"  # its recommendation, which the page marks: {"flow": <name>, "why": <reason>}


def next_flow_recommended(reg):
    """The recommendation at the next-flow stop, while its flow is still to map: {"flow", "why"}, or None."""
    got = load(pathlib.Path(reg), NEXT_JSON)
    return got if got and got.get("flow") in flows_left(reg) else None


def next_flow_message(reg, flow, why, left):
    """The message at the end of a flow, when the first look found more: the flows still to add, the recommendation,
    and the recommended flow offered as what is next, never as a wait on the person."""
    done = (scope_now(reg) or {}).get("flow", "")
    return f"""{status(reg)}

**{done} is drafted to the end.** It stays in this map as it is: your picks, your words and its pages.

**The flows still to add to this map.** {'; '.join(f'*{n}*' for n in left)}.

**My recommendation.** Next: *{flow}*. {sentence(why)}

**What is next.** *{flow}*, as I recommend. Say carry on and I will map it, or name another flow on the page or here in the chat. Or say stop, and this map stays as it is, with those flows still to add.
"""
SIGNAL = {"business health": "business", "business impact": "business", "application": "application",
          "system": "technology", "technology": "technology"}


def signal_kind(layer):
    """A measure's layer as the person reads its kind of health signal; a layer the kit does not name is shown as
    written."""
    layer = (layer or "").strip()
    return SIGNAL.get(layer.lower(), layer or "not stated")


def mark_the_review(reg):
    """The review message is the stop: RUN.md's alerting row done and the review row doing, so its line waits on the person."""
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"^(\| 5a [^|]*\| )[^|]*\|", r"\1done |", text, count=1, flags=re.M)
    text = re.sub(r"^(\| Review of the alerts \| )(?:to do|doing) \|", r"\1doing |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


def alerts_review(reg, flow_id, stage_ids, recommend):
    """The message for the person's review of the proposed alerts, before any runbook: per stage, each proposed alert
    with what it watches, what it guards, its kind of health signal, whether it exists today and why it is proposed,
    then the stage's measures considered and not proposed; the session's recommendation in its one slot; the options."""
    import flow_outputs as fo
    R = fo.load(reg)

    def plain(M, text):
        said = fo.states_said(M, fo.remedy_words(fo.unid(M, fo.unpipe(text or ""))))
        return re.sub(r"\bproposed:\s*", "", said).strip()

    names, proposed, measure_names = set(), set(), set()

    import go
    picked = go.depth_all(reg) or {}
    runbooks = any(picked.get(sid) == "runbooks" for sid in stage_ids)  # else the alerts are as far as these stages go
    out = [status(reg), "", "**The alerts proposed, for your review.** " + (
        "Nothing about how each could fail, and no runbook, has been written yet: those come after your go on these "
        "alerts." if runbooks else "They are written into the alert pages once you say go."), "",
        f"**My recommendation.** {sentence(recommend)}", "",
        "**What you can decide.** Keep these alerts as they are, drop one, change one or add one; or say go" +
        (" on to the runbooks." if runbooks else ".")]
    for sid in stage_ids:
        M = fo.build(R, flow_id, sid)
        names |= set(fo.given_names(M)) | {fo.states_said(M, fo.state(v.get(k))) for v in M["moves"].values()
                                           for k in ("from_state", "to_state")}
        measure_names |= {cont(plain(M, x["measure"])) for x in M["measures"].values()}
        expect = {e.get("expectation_id"): e for e in R.get("expectations", [])}
        out += ["", f"### {M['stage']['name']}, in the flow {cont(M['flow']['name'])}"]
        alerts = fo.stage_alerts(M)
        if not alerts:
            out += ["", "No alert is proposed for this stage."]
        for m in alerts:
            guards = "; ".join(cont(re.sub(r"^proposed:\s*", "", expect[e]["expectation"]))
                               for e in fo.guards(m) if e in expect)
            out += ["", f"**{m['measure']}**", "",
                    f"- What it watches: {cont(plain(M, m.get('question_it_answers')))}",
                    f"- It guards: {guards or 'no expectation named'}.",
                    f"- Health signal: {signal_kind(m.get('layer'))}.",
                    f"- Exists today: {'yes' if m.get('exists') == 'yes' else 'no, proposed'}.",
                    f"- Why I propose it: {cont(plain(M, fo.basis(m)))}."]
        steps = {s["step"] for s in M["steps"]}
        alerting = {m["handle"] for m in alerts}
        proposed |= {m["handle"] for m in M["alerts"]}
        parts = {p for mv in M["stage_moves"] for p in M["carried"][mv] + M["needs"][mv]}
        own = [x["measure"] for x in M["measures"].values() if x["handle"] not in alerting and
               ((x.get("stage") or "").strip() == sid or (x.get("step") or "").strip() in steps)]
        # the parts' own measures are the application and technology health signals of this stage
        of_parts = [x["measure"] for x in M["measures"].values() if x["handle"] not in alerting and
                    x.get("subject_id") in parts and not any((x.get(c) or "").strip() for c in ("step", "stage", "flow"))]
        out += ["", "Considered for the stage and its steps, and not proposed as alerts:",
                bullets(cont(plain(M, x)) for x in dict.fromkeys(own)) or "- none",
                "", "Considered for the services and stores it uses, and not proposed as alerts:",
                bullets(cont(plain(M, x)) for x in dict.fromkeys(of_parts)) or "- none"]
        flow_measures = [x for x in M["measures"].values() if (x.get("flow") or "").strip() == flow_id and
                         not (x.get("stage") or "").strip() and not (x.get("step") or "").strip()]
        flow_name, flow_M = M["flow"]["name"], M
    if stage_ids:  # the flow's own measures belong to the flow: listed once, not under every stage
        flow_other = [x["measure"] for x in flow_measures if x["handle"] not in proposed]
        out += ["", f"### The flow as a whole: {cont(flow_name)}", "",
                "Considered for the flow, and not proposed as alerts:",
                bullets(cont(plain(flow_M, x)) for x in dict.fromkeys(flow_other)) or "- none"]
    if runbooks:  # verification is the build's to report, never the runbook's: said here, owed before hand-over
        out += ["", "**Before hand-over, each test its runbook holds is tried once on a known case** (a seeded row "
                "or a reproduced failure), by someone who can run it: this work reads the code and runs nothing. The "
                "done check counts the tests still owed that try."]
    return "\n".join(out) + "\n", names, measure_names


WATCHED_WORDS = {"yes": "yes", "in the app only": "only inside the application", "no": "no",
                 "unknown": "not known"}
GAP_WORDS = {"does not apply": "it does not apply here", "counted by": "a measure proposed for something else already answers it",
             "no record": "nothing the system keeps records it", "not read": "the code that would say was not read"}


def mark_the_measures_review(reg):
    """The measures review message is the stop: RUN.md's measures row done and the review row doing."""
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"^(\| 4 [^|]*\| )[^|]*\|", r"\1done |", text, count=1, flags=re.M)
    text = re.sub(r"^(\| Review of the measures \| )(?:to do|doing) \|", r"\1doing |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


# The heading each kind of health signal has in the review, from the names method/layers.csv also writes it by
LAYER_HEADS = {"business health": "Business Health", "business impact": "Business Impact", "application": "Application",
               "technology": "System", "agentic": "Agentic"}
MEASURES_DETAIL_FILE = "measures-review-detail.md"  # the review's detail, one level down: the session shows it on request


def measures_placed(M_of, flow_id, stage_ids, rec):
    """{stage id: [measure rows]}, with "" for the measures several picked stages share and "flow" for the flow's own.
    A measure on a stage or a step is that stage's. A measure on a part or an operation is placed by the coverage
    items it answers: under the one picked stage they belong to, or with those shared when they belong to several;
    one that answers no item is placed by the stages that use its part. Never by the first stage that uses the part,
    which would put every operation of a shared service under the first stage."""
    picked = list(stage_ids)
    steps_of = {sid: {s["step"] for s in M_of[sid]["steps"]} for sid in picked}
    parts_of = {sid: {p for mv in M_of[sid]["stage_moves"] for p in M_of[sid]["carried"][mv] + M_of[sid]["needs"][mv]}
                for sid in picked}
    serves = {}
    for r in rec:
        for h in r["by"]:
            serves.setdefault(h, set()).update(set(r["stages"]) & set(picked))
    placed = {sid: [] for sid in picked}
    placed.update({"": [], "flow": []})
    seen = set()
    for sid in picked:
        for x in M_of[sid]["measures"].values():
            st, sp = (x.get("stage") or "").strip(), (x.get("step") or "").strip()
            if x["handle"] not in seen and (st == sid or sp in steps_of[sid]):
                placed[sid].append(x)
                seen.add(x["handle"])
    for sid in picked:
        for x in M_of[sid]["measures"].values():
            h = x["handle"]
            if h in seen or any((x.get(c) or "").strip() for c in ("step", "stage")):
                continue
            if (x.get("flow") or "").strip():
                if (x.get("flow") or "").strip() == flow_id:
                    placed["flow"].append(x)
                    seen.add(h)
                continue
            where = serves.get(h) or {s for s in picked if x.get("subject_id") in parts_of[s]}
            if where:
                placed[next(iter(where)) if len(where) == 1 else ""].append(x)
                seen.add(h)
    return placed


def measures_review(reg, flow_id, stage_ids, recommend):
    """The message for the person's review of the proposed measures, before any alert is chosen, short enough to
    read in the chat: per stage, what each party counts on, a short list of its measures (what each shows, whether
    the system produces it today, whether anything collects it), what a measure produced today gets wrong, and each
    part with no measure and why; the measures several stages share, and the flow's own, once; the coverage list
    and the inspection as counts with what fails; the session's recommendation; the options. Returns (message,
    detail, names, measure names): the detail is the full review one level down, each measure with where it is
    produced and the coverage list item by item, which the session shows when the person asks."""
    import check_measures
    import flow_outputs as fo
    import go
    R = fo.load(reg)

    def plain(M, text):
        said = fo.states_said(M, fo.remedy_words(fo.unid(M, fo.unpipe(text or ""))))
        return re.sub(r"^\s*proposed:\s*", "", said).strip()

    def prose(M, text):  # register prose with its file citations taken out and the claim kept
        said = fo.keep_claims(text or "")
        # a parenthesis left ending on the word that led into its citation ("swallowed at") says nothing
        said = re.sub(r"\s*\([^()]*\b(?:at|in|see|by|from|of|on)\s*\)", "", said)
        return cont(plain(M, said)).rstrip(". ")

    def asks(M, x):
        q = cont(plain(M, x.get("question_it_answers")))
        return q + ("" if q.endswith("?") else ".")

    def collected(x):
        if (x.get("exists") or "").strip() != "yes":
            return "not yet produced"
        return WATCHED_WORDS.get((x.get("watched") or "").strip(), "not said")

    def row(M, x):
        produced = "yes" if (x.get("exists") or "").strip() == "yes" else "no, proposed"
        return f"| {x['measure']} | {asks(M, x)} | {produced} | {collected(x)} |"

    def item(M, x):  # the detail, one level down: one measure in full
        produced = (x.get("exists") or "").strip() == "yes"
        where = cont(plain(M, x.get("counted_at"))) if (x.get("counted_at") or "").strip() else "a place not named"
        lines = [f"- **{x['measure']}**: {asks(M, x)}",
                 f"  Health signal: {signal_kind(x.get('layer'))}. Produced today: "
                 + (f"yes, at {where}." if produced else "no, proposed.")]
        if produced:
            lines.append(f"  Whether anything collects it: {collected(x)}.")
        if produced and (x.get("defect") or "").strip():
            lines.append(f"  What it gets wrong today: {prose(M, x['defect'])}.")
        return lines

    picked = go.depth_all(reg) or {}
    alerts = any(picked.get(sid) in ("alerting", "runbooks") for sid in stage_ids)
    names, measure_names = set(), set()
    M_of = {}
    for sid in stage_ids:
        M = fo.build(R, flow_id, sid)
        M_of[sid] = M
        names |= set(fo.given_names(M)) | {fo.states_said(M, fo.state(v.get(k))) for v in M["moves"].values()
                                           for k in ("from_state", "to_state")}
        measure_names |= {x["measure"] for x in M["measures"].values()}
        # the register's own name for where a measure is taken (a queue, a trace, a table) is how the person finds it
        for x in M["measures"].values():
            at = cont(plain(M, x.get("counted_at"))) if (x.get("counted_at") or "").strip() else ""
            names |= {at} | {p.strip() for p in at.split(",")} if at else set()
    flow_M = M_of[stage_ids[-1]] if stage_ids else None
    rec, _, _, _ = fo.receipt_failures(R, flow_id, measured=set(stage_ids))
    gapped = fo.gap_rows(R, rec)[2]
    why = {(fo.norm(g.get("element")), fo.norm(g.get("question"))): g.get("why") or "" for g in R["measure-gaps"]}
    by_name = {m.get("handle"): m.get("measure") for m in R["measures"]}
    owed = [r for r in rec if not r["stages"] or set(r["stages"]) & set(stage_ids)]
    covered = sum(r["covered"] for r in owed)
    reasoned = sum(not r["covered"] and (r["element"], r["question"]) in gapped for r in owed)
    placed = measures_placed(M_of, flow_id, stage_ids, rec) if stage_ids else {"": [], "flow": []}

    def where_owed(r):
        st = [s for s in stage_ids if s in r["stages"]]
        return st[0] if len(st) == 1 else ("flow" if not r["stages"] else "")

    def what_of(r):
        return cont(plain(flow_M, check_measures.said_what(r["what"]))) if flow_M else r["what"]

    def no_measure(key):
        lines = []
        for r in (r for r in owed if not r["covered"] and where_owed(r) == key):
            q = f"{what_of(r)}, “{check_measures.question(r['question'])}”"
            k = (r["element"], r["question"])
            if k in gapped and gapped[k] == "counted by":  # the measure it is folded into is the reason
                into = [by_name[h] for h in dict.fromkeys(re.findall(r"\bM\d+\b", why.get(k, ""))) if by_name.get(h)]
                lines.append(f"- {q}: {GAP_WORDS['counted by']}"
                             + (f": {and_list([f'*{n}*' for n in into])}." if into else "."))
            elif k in gapped:
                reason = prose(flow_M, why.get(k, ""))
                lines.append(f"- {q}: {GAP_WORDS.get(gapped[k], 'a reason is recorded')}"
                             + (f". {sentence(reason)}" if reason else "."))
            else:
                lines.append(f"- {q}: no measure, and no reason why none.")
        return lines

    def counted_on(M, scope):
        out = []
        for e in R["expectations"]:
            if (e.get("flow") or "").strip() != flow_id or (e.get("stage") or "").strip() != scope:
                continue
            proposed = (e.get("expectation") or "").strip().lower().startswith("proposed:")
            bound = (e.get("objective") or "").strip()
            out.append(f"- {cont(plain(M, e.get('party'))) or 'someone not named'}: “{prose(M, e.get('expectation'))}”"
                       + (" (proposed, not yet stated by anyone)" if proposed else "")
                       + (f"; the bound stated: {plain(M, bound)}" if bound else "") + ".")
        return out

    import capability_views as cv
    layers = cv.read_csv(cv.METHOD / "layers.csv")  # in outside-in order: health, impact, application, system, agentic
    layer_R = {"method": {"layers": layers}}

    def by_layer(measures):
        """[(heading, the question it asks, measures)], in the method's order, only the layers these measures have;
        a measure whose layer the method does not name comes last, under its own word."""
        groups = {}
        for x in measures:
            groups.setdefault(cv.layer_of(layer_R, x.get("layer")) or (x.get("layer") or "not stated").strip(),
                              []).append(x)
        out = []
        for r in layers:
            if r["layer"] in groups:
                out.append((LAYER_HEADS.get(r["layer"], r["layer"].title()), r["question_it_asks"],
                            groups.pop(r["layer"])))
        return out + [(k[:1].upper() + k[1:], "not one the method names.", v) for k, v in groups.items()]

    def section(M, title, measures, key):
        out = ["", f"### {title}", ""]
        exp = counted_on(M, "" if key == "flow" else key) if key else []
        if exp:
            out += ["What each party counts on:"] + exp + [""]
        if measures:
            for head, asks_, group in by_layer(measures):
                out += [f"**{head}**, {asks_[:1].lower() + asks_[1:]} {len(group)} "
                        f"measure{'' if len(group) == 1 else 's'}.", "",
                        "| Measure | What it shows | Produced today | Collected |", "|---|---|---|---|"]
                out += [row(M, x) for x in group] + [""]
            out.pop()
        else:
            out.append("No measure of its own here.")
        wrong = [x for x in measures if (x.get("exists") or "").strip() == "yes" and (x.get("defect") or "").strip()]
        if wrong:
            out += ["", "What a measure produced today gets wrong:"]
            out += [f"- *{x['measure']}*: {prose(M, x['defect'])}." for x in wrong]
        gaps = no_measure(key)
        if gaps:
            out += ["", "No measure, and why:"] + gaps
        return out

    produced = [x for xs in placed.values() for x in xs if (x.get("exists") or "").strip() == "yes"]
    total = sum(len(xs) for xs in placed.values())
    out = [status(reg), "", "**The measures proposed, for your review.** " + (
        "No alert has been chosen yet: alerts are chosen from these measures after your go on them." if alerts else
        "These are as far as the stages you picked go; they stand once you say go.")
        + f" There are {total}: {len(produced)} the system produces today and {total - len(produced)} proposed. "
        "For each, what it shows, whether the system produces it today, and whether anything collects it.", "",
        f"**My recommendation.** {sentence(recommend)}", "",
        "**What you can decide.** Keep these measures as they are, drop one, change one or add one; or say go"
        + (" on to the alerts." if alerts else ".")]
    for sid in stage_ids:
        M = M_of[sid]
        out += section(M, f"{M['stage']['name']}, in the flow {cont(M['flow']['name'])}", placed[sid], sid)
    if placed[""] or no_measure(""):
        out += section(flow_M, "Shared by several of these stages", placed[""], "")
    if flow_M is not None:
        out += section(flow_M, f"The flow as a whole: {cont(flow_M['flow']['name'])}", placed["flow"], "flow")
    results = check_measures.inspect(reg, flow_id, stage_ids)
    failed = [r for r in results if not r["passed"]]
    out += ["", f"**The coverage list.** Every stage, step that matters, service and store these stages and the flow "
            f"hold, with what is asked of each: {len(owed)} items, {covered} with a measure, {reasoned} with a reason "
            f"why none (each under its stage above), {len(owed) - covered - reasoned} with neither.",
            "", f"**Measures inspection.** {len(results)} rules checked: {len(results) - len(failed)} pass, "
            f"{len(failed)} fail{'s' if len(failed) == 1 else ''}. It checks the measures' shape, not whether they "
            "are right about the system."]
    for half, heading in check_measures.HALVES:
        mine = [r for r in results if r["half"] == half]
        bad = [r for r in mine if not r["passed"]]
        fails = "; ".join(f"{cont(r['title'])}: fails on {'; '.join(cont(s) for s in r['said'])}" for r in bad)
        out.append(f"- *{heading}*: " + (f"{fails}." if bad else f"all {len(mine)} rules pass."))
    out += ["", "**The detail.** Where each measure is produced, and every item of the coverage list with the measure "
            "that answers it, is one level down: ask me for it, whole or for one stage."]
    detail = [status(reg), "", "**The measures proposed, in detail.**"]
    titles = [(sid, f"{M_of[sid]['stage']['name']}, in the flow {cont(M_of[sid]['flow']['name'])}")
              for sid in stage_ids]
    if flow_M is not None:
        titles += [("", "Shared by several of these stages"), ("flow", f"The flow as a whole: "
                                                                       f"{cont(flow_M['flow']['name'])}")]
    for key, title in titles:
        if placed.get(key):
            M = M_of.get(key, flow_M)
            detail += ["", f"### {title}", ""] + [line for x in placed[key] for line in item(M, x)]
    detail += ["", f"**The coverage list, item by item.** {len(owed)} items.", ""]
    for r in owed:
        if r["covered"]:
            answer = "; ".join(f"*{by_name.get(h) or h}*" for h in dict.fromkeys(r["by"]))
        elif (r["element"], r["question"]) in gapped:
            answer = "no measure: " + GAP_WORDS.get(gapped[(r["element"], r["question"])], "a reason is recorded")
        else:
            answer = "no measure, and no reason why none"
        detail.append(f"- {what_of(r)}, “{check_measures.question(r['question'])}”: {answer}.")
    detail += ["", check_measures.said(results, for_person=True)]
    return "\n".join(out) + "\n", "\n".join(detail) + "\n", names, measure_names


def measures_main(args):
    """brief.py measures: render the review of the measures, mark the stop, keep the message and what it showed."""
    recommend = ""
    if "--recommend" in args:
        i = args.index("--recommend")
        recommend = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    if len(args) < 3 or not recommend.strip():
        print("Usage: python brief.py measures <register folder> <flow id> <stage id>... --recommend \"<your "
              "recommendation and its reason>\"", file=sys.stderr)
        return 2
    run_lock.guard(args[0])
    if refuse_reason(recommend, args[0]):
        return 2
    reg = pathlib.Path(args[0])
    run_md = reg / "RUN.md"
    before = run_md.read_bytes() if run_md.is_file() else None
    mark_the_measures_review(reg)
    text, detail, names, measure_names = measures_review(reg, args[1], args[2:], recommend)
    bad = list(dict.fromkeys(review_terms(text + detail, measure_names | names)
                             + prose_faults(text + detail, names | measure_names)))
    if bad:
        if before is not None:
            run_md.write_bytes(before)
        print("REFUSED: ids, file names, kit terms or broken prose in the message: " + "; ".join(bad) +
              ". Fix the recommendation or the register text it comes from, and run this again.", file=sys.stderr)
        return 2
    (reg / MEASURES_REVIEW_FILE).write_text(text, encoding="utf-8", newline="\n")
    (reg / MEASURES_DETAIL_FILE).write_text(detail, encoding="utf-8", newline="\n")
    import go  # what the person is shown is what their go covers: go.py --measures-reviewed checks against this
    go.record_measures_shown(reg)
    import depth
    depth.write_quietly(reg)
    print(with_page(text, reg))
    return 0


def review_terms(text, measure_names):
    """The kit-term check of the review, except inside a measure's own name: the register's name for what is counted
    (a route, a queue) is how the person finds it, as a part's name is."""
    for n in sorted((n for n in measure_names if n), key=len, reverse=True):
        text = text.replace(n, " ")
    return kit_terms(text)


def no_business_impact(reg, flow_id):
    """The flow's process steps, when step-impact.csv holds a row for none of them; else []."""
    stages = {(r.get("stage") or "").strip() for r in rows(reg / "stages.csv") if (r.get("flow") or "").strip() == flow_id}
    steps = [(r.get("step") or "").strip() for r in rows(reg / "steps.csv") if (r.get("stage") or "").strip() in stages]
    rated = {(r.get("step") or "").strip() for r in rows(reg / "step-impact.csv")}
    return [] if not steps or rated & set(steps) else steps


def mark_the_pick_stop(reg, flow_id=None):
    """The pick message is the stop after mapping: the capability row done and the pick row doing. Sent for the flow
    worked now once it is finished (ended at the map, or done), it takes that flow further: the flow is current again,
    at its pick, so the page and the status line ask for the pick, not the next flow."""
    import go
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    s = go.load(reg)
    again = bool(flow_id and s and go.flow_id_of(reg, s) == flow_id and go.run_finished(reg))
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"^(\| 3 [^|]*\| )[^|]*\|", r"\1done |", text, count=1, flags=re.M)
    text = re.sub(r"^(\| Pick of how far each stage goes \| )(?:to do|doing" + ("|not picked|done" if again else "")
                  + r") \|", r"\1doing |", text, count=1, flags=re.M)
    if again:  # what follows the pick is owed again, as for a flow at its first pick; the pick then says how far
        text = re.sub(r"^(\| 4 [^|]*\| )[^|]*\|", r"\1to do |", text, count=1, flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


def count_word(n):
    return ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")[n] if n <= 10 else str(n)


def replaced_stages(reg, walked):
    """(the first look's stage names, the walk's) for the flow the person picked when the walk's differ from the first
    look's, else None. The first look's flow is the one named at the go, else the one it recommended."""
    o = load(reg, "orientation.json") or {}
    picked = (scope_now(reg) or {}).get("flow") or (o.get("recommendation") or {}).get("flow")
    flow = next((f for f in o.get("flows") or [] if (f.get("name") or "").strip() == (picked or "").strip()), None)
    first = [(s.get("name") or "").strip() for s in (flow or {}).get("stages") or [] if (s.get("name") or "").strip()]
    walked = [n for n in walked if n]
    if not first or not walked or [n.lower() for n in first] == [n.lower() for n in walked]:
        return None
    return first, walked


STAKE_WORDS = {"customer": "Customers lose out", "financial": "Money is lost", "operational-efficiency": "Rework",
               "legal-risk-compliance": "A compliance breach"}
STAKE_RECOVERY = {"moves on": "these move on once the cause is fixed", "stranded": "these are left stranded",
                  "not created": "these never come into being"}
GROUNDING = ("Here's how we've divided the work into stages. Does that match how the business sees it, or would you "
             "divide it differently?")


STAGES_TOLD = "stages-change-told.json"  # the stage changes already put to the person, so each is said once


def stages_change(reg, walked=None):
    """When mapping changed the stages the person agreed to at the go, the change said plainly, the first look's
    stages and the code's side by side; else "". With `walked` None, the walk's stages of the flow picked, once the
    stages are mapped (six stages agreed and three mapped is said plainly, never only mentioned at the pick)."""
    import itertools
    reg = pathlib.Path(reg)
    if walked is None:
        if (STRUCTURE, "done") not in phases(reg):
            return ""
        walked = mapped_stages(reg, (scope_now(reg) or {}).get("flow"))
    replaced = replaced_stages(reg, walked)
    if not replaced:
        return ""
    first, now = replaced
    rows = [f"| {a} | {b} |" for a, b in itertools.zip_longest(first, now, fillvalue="")]
    return ("**The stages changed when the flow was mapped.** When you picked the flow, the first look had proposed "
            f"{count_word(len(first))} stages; reading the code found {count_word(len(now))}. Side by side:\n\n"
            "| Agreed when you picked the flow | Found in the code |\n|---|---|\n" + "\n".join(rows) +
            "\n\nThe stages found in the code are the ones the rest of the work uses.")


def stages_change_untold(reg):
    """The change of stages, while it has not yet been put to the person; else ""."""
    said = stages_change(reg)
    told = load(pathlib.Path(reg), STAGES_TOLD) or []
    return "" if not said or said in told else said


def mark_stages_told(reg, said):
    if said:
        reg = pathlib.Path(reg)
        told = load(reg, STAGES_TOLD) or []
        (reg / STAGES_TOLD).write_text(json.dumps(told + [said]) + "\n", encoding="utf-8")


def at_stake_items(R, M):
    """What a stage's failure costs, from the Business Impact rows of its process steps, in plain words:
    [(what it costs and what becomes of the cases, [what is lost])], grouped in the order first met."""
    sids = {x["step"] for x in M["steps"]}
    groups = {}
    for r in R["step-impact"]:
        if r["step"] in sids and (r.get("unit") or "").strip():
            cost = STAKE_WORDS.get(r.get("impact_category"), (r.get("impact_category") or "").capitalize())
            fate = STAKE_RECOVERY.get(r.get("recovery"), "")
            head = f"{cost}, and {fate}" if cost and fate else (cost or fate.capitalize() or "Lost")
            groups.setdefault(head, []).append(r["unit"].strip())
    return list(groups.items())


def stake_lines(groups):
    """The groups as a list: each cost, with what is lost under it, the same loss at several steps said once."""
    def said(units):
        n = {}
        for u in units:
            n[u] = n.get(u, 0) + 1
        return "\n".join(f"  - {u}" + (f" (at {c} steps)" if c > 1 else "") for u, c in n.items())
    return "\n".join(f"- {head}:\n" + said(units) for head, units in groups)


def depth_review(reg, flow_id, recommend):
    """The message for the person's pick of how far each stage goes, after mapping: the ask with the session's
    recommendation first, what a yes does and the choices; then the mapping inspection as a count; then each stage
    with its count of process steps and what is at stake if it fails, under the question whether the stages match
    how the business sees the work. The steps themselves are on the page."""
    import check_map
    import flow_outputs as fo
    R = fo.load(reg)
    names = set()
    walked = sorted((x for x in R["stages"] if x.get("flow") == flow_id), key=lambda x: int(x.get("order") or 0))
    flow = next((f.get("name") for f in R["flows"] if f.get("flow_id") == flow_id), "") or "The flow"
    n_st = len(walked)
    out = [status(reg), "", f"**{flow} is mapped. How far should each of its {count_word(n_st)} stage"
           f"{'' if n_st == 1 else 's'} go? I recommend: {cont(recommend)}.**", "",
           "If you say yes, I record it and go on to the stages you take further, then the map's check and report. "
           "A stage left mapped only can go further later. Each stage's steps are on the page.", "",
           "For each stage you can choose:",
           bullets(["mapped only: the map below, nothing more",
                    "measured: I propose what to measure to tell whether it is working",
                    "measured, with alerts: I propose which of those measures should wake someone, for you to review",
                    "measured, with alerts and then runbooks: and, for each alert, what to do when it fires"]),
           "", check_map.counted(reg, flow_id)]
    checked = checks_found(reg)
    out += ["", checked] if checked else []
    out += ["", f"**The stages.** {GROUNDING}"]
    changed = stages_change(reg, [(s.get("name") or "").strip() for s in walked])
    if changed:
        first = replaced_stages(reg, [(s.get("name") or "").strip() for s in walked])[0]
        names |= set(first) | {cont(n) for n in first}
        out += ["", changed]
    for i, s in enumerate(walked, 1):
        M = fo.build(R, flow_id, s["stage"])
        names |= set(fo.given_names(M)) | {cont(n) for n in fo.given_names(M)}
        n = sum(1 for x in M["steps"] if (x.get("name") or "").strip())
        items = at_stake_items(R, M)
        out += ["", f"**{i}. {s['name']}** ({count_word(n)} step{'' if n == 1 else 's'}). "
                + ("At stake if it fails:" if items else "No Business Impact is recorded for its steps.")]
        out += [stake_lines(items)] if items else []
    return "\n".join(out) + "\n", names


def depth_from_request(reg, flow_id, words, spec, given=None):
    """The pick of how far each stage goes, when the person's request already said it: recorded from the request,
    word for word, and said back in one line; the run goes on without stopping. Returns (message, names) or a
    refusal."""
    import argparse
    import go
    mark_the_pick_stop(reg, flow_id)
    go.record_flow_id(reg, flow_id)
    a = argparse.Namespace(words=words, given=given, test=False, page=False, from_request=True)
    got = go.record_depth(reg, spec or "", a)
    if isinstance(got, str):
        return got
    go.record_decision(reg, "depth", words, "request", shown=f"(the request, word for word) {words}")
    flow = got.get("flow") or "this flow"
    st = {(r.get("stage") or "").strip(): (r.get("name") or "").strip() for r in rows(pathlib.Path(reg) / "stages.csv")}
    named = and_list([f"*{st.get(s) or s}*" for s in got["depth"]])
    line = (f"*{flow}* is mapped into {count_word(len(got['depth']))} stage{'' if len(got['depth']) == 1 else 's'}: "
            f"{named}. Your request already said how far each goes, so I've recorded it: "
            f"{depth_said(reg, got['depth'])}. In your words: \"{words}\" To take a stage further, say which.")
    return f"{status(reg)}\n\n{line}\n", set(register_names(reg)) | {flow}


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if argv[:1] == ["depth"]:
        args, request = take_request(argv[1:])
        opts = {}
        for flag in ("--recommend", "--depth", "--given"):
            if flag in args:
                i = args.index(flag)
                opts[flag] = args[i + 1] if i + 1 < len(args) else ""
                args = args[:i] + args[i + 2:]
        recommend = opts.get("--recommend", "")
        if request is not None and len(args) == 2:
            request = request_given(args[0], request)
        if len(args) != 2 or (request is None and not recommend.strip()) or (request is not None
                                                                              and not request.strip()):
            print("Usage: python brief.py depth <register folder> <flow id> --recommend \"<your recommendation and "
                  "its reason>\"\n       python brief.py depth <register folder> <flow id> --from-request \"<their "
                  "request's words, word for word>\" [--depth \"<id>=measure|alerting|runbooks,...\"] [--given "
                  "\"<when they asked>\"]  (with no words after --from-request, the request the run record keeps)",
                  file=sys.stderr)
            return 2
        run_lock.guard(args[0])
        if recommend.strip() and refuse_reason(recommend, args[0]):
            return 2
        missing = no_business_impact(pathlib.Path(args[0]), args[1])
        if missing:
            print(f"REFUSED: Business Impact is recorded for none of this flow's {len(missing)} process steps, as in a "
                  "register made by an earlier release. Fill it first, FILL-STEPS Step 10, from each step's own "
                  "citation (step-impact.csv, one row per step a failure hurts), then run this again.", file=sys.stderr)
            return 2
        run_md = pathlib.Path(args[0]) / "RUN.md"
        before = run_md.read_bytes() if run_md.is_file() else None
        if request is not None:  # the request already said how far each stage goes: recorded, said in a line, no stop
            import go
            scope_file = pathlib.Path(args[0]) / layout.SCOPE
            kept = scope_file.read_bytes() if scope_file.is_file() else None
            got = depth_from_request(pathlib.Path(args[0]), args[1], request.strip(), opts.get("--depth", ""),
                                     opts.get("--given"))
            bad = got if isinstance(got, str) else "; ".join(say_terms(got[0].split("\n", 2)[2], args[0]))
            if bad:
                if before is not None:
                    run_md.write_bytes(before)
                if kept is not None:
                    scope_file.write_bytes(kept)
                print(f"REFUSED: {bad}. Nothing recorded.", file=sys.stderr)
                return 2
            import depth
            depth.write_quietly(args[0])
            print(with_page(got[0], args[0]))
            return 0
        mark_the_pick_stop(args[0], args[1])
        text, names = depth_review(pathlib.Path(args[0]), args[1], recommend)
        bad = review_terms(text, names) + prose_faults(text, names)
        if bad:
            if before is not None:
                run_md.write_bytes(before)
            print("REFUSED: ids, file names, kit terms or broken prose in the message: " + "; ".join(bad) +
                  ". Fix the recommendation or the register text it comes from, and run this again.", file=sys.stderr)
            return 2
        # kept, so a run picked up again at the pick can show it again
        (pathlib.Path(args[0]) / PICK_FILE).write_text(text, encoding="utf-8", newline="\n")
        told = re.search(r"[*][*]The stages changed.*?the rest of the work uses[.]", text, re.S)
        mark_stages_told(args[0], told.group(0) if told else "")
        import depth  # the page draws this stop's open choice from depth.json
        import go
        go.record_flow_id(pathlib.Path(args[0]), args[1])  # found by id, not by a name the walk may change
        depth.write_quietly(args[0])
        print(with_page(text, args[0]))
        return 0
    if argv[:1] == ["next"]:
        after = "--after" in argv
        args, request = take_request([x for x in argv[1:] if x != "--after"])
        opts = {}
        for flag in ("--flow", "--recommend"):
            if flag in args:
                i = args.index(flag)
                opts[flag] = args[i + 1] if i + 1 < len(args) else ""
                args = args[:i] + args[i + 2:]
        if len(args) != 1 or not (opts.get("--flow") or "").strip() or not (opts.get("--recommend") or "").strip():
            print("Usage: python brief.py next <register folder> --flow \"<the flow you recommend next>\" "
                  "--recommend \"<why>\"", file=sys.stderr)
            return 2
        reg = pathlib.Path(args[0])
        run_lock.guard(reg)
        left = flows_left(reg)
        if not left or not next_ready(reg):
            print("REFUSED: the next flow is offered once this flow is finished and the first look found flows still "
                  "to map; " + ("none is left" if not left else "this flow is not finished") + ".", file=sys.stderr)
            return 2
        flow, why = opts["--flow"].strip(), opts["--recommend"].strip()
        if refuse_reason(why, reg):
            return 2
        if flow not in left:
            print(f"REFUSED: {flow} is not a flow still to map (still to map: {', '.join(left)}).", file=sys.stderr)
            return 2
        request = request_given(reg, request) if request is not None else None
        if request is not None and not request:
            print("REFUSED: --from-request has no words, and the run record keeps no request. Nothing written.",
                  file=sys.stderr)
            return 2
        if request:  # the request asked for every flow: recorded, said, no stop
            finished = (scope_now(reg) or {}).get("flow", "")
            got = go_from_request(reg, flow, request)
            if got:
                print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
                return 2
            rest = [n for n in left if n != flow]
            done = finished
            line = ((f"*{done}* is drafted to the end. " if done else "")
                    + f"Your request asked for every flow, so I'm going on with *{flow}* next: {cont(why)}. "
                    + (f"Still to add after it: {and_list([f'*{n}*' for n in rest])}. " if rest else "")
                    + "To stop here or pick another flow, say stop or name it.")
            import depth
            depth.write_quietly(reg)
            print(with_page(line if after else f"{status(reg)}\n\n{line}", reg))
            return 0
        text = next_flow_message(reg, flow, why, left)
        known = set(register_names(reg)) | set(left)  # the reason may name a stage, a step or a service
        bad = review_terms(text, known) + prose_faults(text, known)
        if bad:
            print("REFUSED: ids, file names, kit terms or broken prose in the message: " + "; ".join(bad) +
                  ". Fix the recommendation, and run this again.", file=sys.stderr)
            return 2
        (reg / NEXT_FILE).write_text(text, encoding="utf-8", newline="\n")
        (reg / NEXT_JSON).write_text(json.dumps({"flow": flow, "why": why}) + "\n", encoding="utf-8")
        import depth  # the page draws the next-flow choice, with this recommendation, from depth.json
        depth.write_quietly(reg)
        print(with_page(text.split("\n", 2)[2] if after else text, reg))
        return 0
    if argv[:1] == ["measures"]:
        return measures_main(argv[1:])
    if argv[:1] == ["alerts"]:
        args = argv[1:]
        recommend = ""
        if "--recommend" in args:
            i = args.index("--recommend")
            recommend = args[i + 1] if i + 1 < len(args) else ""
            args = args[:i] + args[i + 2:]
        if len(args) < 3 or not recommend.strip():
            print("Usage: python brief.py alerts <register folder> <flow id> <stage id>... --recommend \"<your "
                  "recommendation and its reason>\"", file=sys.stderr)
            return 2
        run_lock.guard(args[0])
        if refuse_reason(recommend, args[0]):
            return 2
        run_md = pathlib.Path(args[0]) / "RUN.md"
        before = run_md.read_bytes() if run_md.is_file() else None
        mark_the_review(args[0])
        text, names, measure_names = alerts_review(pathlib.Path(args[0]), args[1], args[2:], recommend)
        bad = review_terms(text, measure_names) + prose_faults(text, names | measure_names)
        if bad:
            if before is not None:
                run_md.write_bytes(before)
            print("REFUSED: ids, file names, kit terms or broken prose in the message: " + "; ".join(bad) +
                  ". Fix the recommendation or the register text it comes from, and run this again.", file=sys.stderr)
            return 2
        # kept, so a run picked up again at the review can show it again
        (pathlib.Path(args[0]) / REVIEW_FILE).write_text(text, encoding="utf-8", newline="\n")
        import go  # what the person is shown is what their go covers: go.py --alerts-reviewed checks against this
        go.record_alerts_shown(pathlib.Path(args[0]))
        print(with_page(text, args[0]))
        return 0
    if argv[:1] == ["say"]:
        after = "--after" in argv
        args = [a for a in argv[1:] if a != "--after"]
        if len(args) != 2 or not pathlib.Path(args[0]).is_dir():
            print(__doc__, file=sys.stderr)
            return 2
        text = pathlib.Path(args[1]).read_text(encoding="utf-8-sig").strip()
        hits = say_terms(text, args[0])
        if hits:
            print("REFUSED: the message uses words the person does not know (ids, file names or the kit's own "
                  "process words): " + "; ".join(hits) + ". Say each in the person's terms (the flow, stage, step "
                  "or service by its name; what was done or is next in plain words), and run this again. Nothing "
                  "sent.", file=sys.stderr)
            return 1
        if after:  # a line added to a message a script printed, which has its status line and the page's address
            print(text)
            return 0
        print(status(pathlib.Path(args[0])))
        print()
        changed = stages_change_untold(args[0])  # the next message after mapping changed the agreed stages
        if changed:
            print(changed)
            print()
            mark_stages_told(args[0], changed)
        print(with_page(text, args[0]))
        return 0
    if argv[:1] == ["checked"]:
        if len(argv) != 2 or not pathlib.Path(argv[1]).is_dir():
            print(__doc__, file=sys.stderr)
            return 2
        print(checked_said(pathlib.Path(argv[1])))
        return 0
    if argv[:1] == ["page"]:
        if len(argv) != 2 or not pathlib.Path(argv[1]).is_dir():
            print(__doc__, file=sys.stderr)
            return 2
        line = page_line(argv[1])
        if line:
            print(line)
        return 0
    request = None
    if argv[:1] == ["capability"] and "--from-request" in argv:  # the request asked for every flow: no stop
        argv, request = take_request(argv)
        request = request_given(argv[1], request) if len(argv) == 2 else request
        if not request:
            print("REFUSED: --from-request has no words, and the run record keeps no request. Nothing written.",
                  file=sys.stderr)
            return 2
    if len(argv) != 2 or argv[0] not in ("status", "capability", "reentry", "terms"):
        print(__doc__, file=sys.stderr)
        return 2
    what, path = argv[0], pathlib.Path(argv[1])
    if what == "terms":
        hits = kit_terms(path.read_text(encoding="utf-8"))
        print("\n".join(hits) if hits else "none")
        return 1 if hits else 0
    reg = path
    if what == "status":
        print(status(reg))
        return 0
    if what == "capability" and any(s == "done" for _, s in phases(reg)[1:]):
        # past the first look, the run is picked up where it stands: asking for the first flow again would undo the go
        print("REFUSED: this run is past its first look (a phase after it is done), so the person is not asked for "
              "the first flow again. Pick the run up with: python brief.py reentry " + f'"{reg}"' + ", and send what "
              "it prints. Nothing written.", file=sys.stderr)
        return 2
    if what == "capability":
        run_lock.guard(reg)
    o = load(reg, layout.ORIENTATION)
    bad = problems(reg, o, brief_now=what == "capability")
    if bad:
        print("REFUSED: " + "; ".join(bad) + ". Fix orientation.json and run this again.", file=sys.stderr)
        return 2
    run_md = reg / "RUN.md"
    before = run_md.read_bytes() if run_md.is_file() else None
    if what == "capability":
        mark_the_stop(reg)
    text = capability(reg, o) if what == "capability" else reentry(reg, o)
    full = capability_full(reg, o) if what == "capability" else ""
    # a message the kit wrote at a stop and the re-entry brief shows again was checked when written, against the
    # register's names: it is read against the same names here, and a fault in it names that message's file
    quoted = next(((f, q) for f in (PICK_FILE, MEASURES_REVIEW_FILE, REVIEW_FILE) if what == "reentry"
                   for q in [shown_again(reg, f)] if q and q in text), None)
    if quoted:
        bad = prose_faults(quoted[1], set(register_names(reg)))
        if bad:
            print(f"REFUSED: the message shown again from {quoted[0]} does not read as prose: " + "; ".join(bad)
                  + ". Render that message again with its own command, and run this again.", file=sys.stderr)
            return 2
        text_checked = text.replace(quoted[1], "")
    else:
        text_checked = text
    faults = prose_faults(text_checked + full)
    if faults:
        if before is not None:
            run_md.write_bytes(before)
        print("REFUSED: the brief does not read as prose where orientation.json's text was filled in: "
              + "; ".join(faults) + ". Rewrite those fields so each reads in its sentence, and run this again.",
              file=sys.stderr)
        return 2
    if what == "capability" and request:  # the recommended flow, taken as their go from the request
        got = go_from_request(reg, o["recommendation"]["flow"], request)
        if got:
            if before is not None:
                run_md.write_bytes(before)
            print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
            return 2
        text = capability(reg, o, request)
        hits = say_terms(text.split("\n", 2)[2], reg)
        if hits:
            print("REFUSED: kit terms in the message: " + "; ".join(hits), file=sys.stderr)
            return 2
    if what == "capability":
        (reg / "PLAN.md").write_text(full, encoding="utf-8", newline="\n")
        (reg / FLOWS_FILE).write_text(with_page(text, reg), encoding="utf-8", newline="\n")
        record_first_look(reg)
        import start  # the first look has reached its brief: its mark in the work folder ends here
        if reg.resolve().parent.name == "bfo-work":
            start.end_first_look(reg.resolve().parent)
        import depth  # the page draws this stop's open choice from depth.json
        depth.write_quietly(reg)
    print(with_page(text, reg))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
