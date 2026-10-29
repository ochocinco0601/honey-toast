"""What the person reads, rendered from the run's files: the status line, the capability brief and the re-entry brief.

Usage: python brief.py status <register folder>       one line; every message to the person opens with it
       python brief.py capability <register folder>   the capability brief, also written to PLAN.md
       python brief.py reentry <register folder>      the re-entry brief, for a run picked up again
       python brief.py terms <file>                   ids and kit terms found in a text (exit 1 if any)

Reads `RUN.md` (its Status table), `orientation.json` (written by the run from its first, shallow look: the
capability, the services, every flow found with its stages, what was searched and what is open, and a
recommendation), `scope.json` (the person's picks, written by go.py) and `survey.csv`. The capability brief is
refused, and nothing written, while orientation.json is incomplete, names services other than the survey's, recommends
a flow it did not find, or carries an id, a file name or the kit's own vocabulary. Exit 0 written, 2 refused.
Python standard library only."""
import csv
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
NEW_RUN = (f"{STATUS_LEAD} Flow: not chosen yet · Stage: not chosen yet · not started · Drafted: nothing yet · "
           "Next: a first look over the system · Waiting on you: nothing")
# The run record's phase rows, by their opening words, and the activity each belongs to as the person reads it.
ACTIVITIES = ("Looking over the system", "Describing the flow from the code", "Naming the capability and what to "
              "measure", "Alerts and runbooks for the stages you picked", "Checking against the code and drawing the "
              "map", "Final check and report")
PICKS = "Your pick of the first flow"
REVIEW = 7  # the hold point between the alerts and the runbooks: the person reviews the proposed alerts
DEPTH_PICK = 8  # the hold point after mapping: the person picks how far each stage goes
# Activities 2, 3 and 4 each in two parts (activity number times ten, plus the part), each named for itself, so the
# status line never reports one part as both drafted and next, or as drafted while it is under way.
CASE, STRUCTURE = 21, 22
CAPABILITY, MEASURES = 31, 32
ALERTS, RUNBOOKS = 41, 42
PARTS = {CASE: "Describing the case and its lifecycle", STRUCTURE: "Describing the stages, steps and parts",
         CAPABILITY: "Naming the capability", MEASURES: "What to measure for the stages you pick",
         ALERTS: "The alerts for the stages you picked", RUNBOOKS: "The runbooks for those alerts"}
HOLDS = (0, REVIEW, DEPTH_PICK)  # the person's picks and review: never reported as drafted
ROWS = (("0 ", 1), ("The go", 0), ("1 ", CASE), ("2 ", STRUCTURE), ("3 ", CAPABILITY),
        ("Pick of how far", DEPTH_PICK), ("4 ", MEASURES), ("5 ", 4), ("5a ", ALERTS),
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
    (r"\breceipts?\b", "kit vocabulary"), (r"\b[Ss]tep \d+\b(?! of\b)", "kit vocabulary"), (r"\bjudges?\b", "kit vocabulary"),
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
    rel = "" if site == folder else folder.name + "/"
    return PAGE_LEAD + url + (rel + "index.html" if (folder / "index.html").is_file() else "")


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
    return list(dict.fromkeys(hits))


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
                    out.append((act, cells[1].lower()))
                    break
    return out


def name(act):
    if act == REVIEW:
        return "Your review of the alerts"
    if act == DEPTH_PICK:
        return "Your pick of how far each stage goes"
    if act in PARTS:
        return f"Activity {act // 10} of {len(ACTIVITIES)}: {PARTS[act]}"
    return PICKS if act == 0 else f"Activity {act} of {len(ACTIVITIES)}: {ACTIVITIES[act - 1]}"


def short(act):
    if act == REVIEW:
        return "your review of the alerts"
    if act == DEPTH_PICK:
        return "your pick of how far each stage goes"
    if act in PARTS:
        return PARTS[act]
    return PICKS.lower() if act == 0 else ACTIVITIES[act - 1]


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


def status(reg):
    st = state(reg)
    if st is None:
        return NEW_RUN.replace("not started", "Activity 1 of 6: not started")
    current, last, after, blocked = st
    scope = load(reg, layout.SCOPE) or {}
    flow = scope.get("flow") or "not chosen yet"
    stages = scope.get("stages") or []
    stage = ", ".join(stages) if isinstance(stages, list) and stages else (stages or "not chosen yet")
    if scope.get("flow") and not stages:  # the go picks only the flow; the stages are picked after mapping
        stage = "picked once the flow is mapped"
        mapped = mapped_stages(reg, scope["flow"])
        if mapped and (STRUCTURE, "done") in phases(reg):
            stage = f"mapped as {and_list(mapped)}; how far each goes is yours to pick"
    if scope.get("depth"):  # once the person has picked how far each stage goes, that is what the run does
        stage = depth_said(reg, scope["depth"])
    if current is None:
        return (f"{STATUS_LEAD} Flow: {flow} · Stage: {stage} · Draft complete, for your review · Drafted: "
                f"{short(last) if last is not None else 'nothing yet'} · Next: nothing · Waiting on you: nothing")
    waiting = "nothing"
    if blocked:
        waiting = "the run is blocked; the message below says why"
    elif current == 0:
        waiting = "your pick of which flow comes first"
    elif current == REVIEW:
        waiting = "your review of the proposed alerts"
    elif current == DEPTH_PICK:
        waiting = "your pick of which stages to measure"
    return (f"{STATUS_LEAD} Flow: {flow} · Stage: {stage} · {name(current)} · Drafted: "
            f"{short(last) if last is not None else 'nothing yet'} · Next: {short(after) if after is not None else 'the report'}"
            f" · Waiting on you: {waiting}")


REQUIRED = {"activity": ("for", "this_run"), "capability": ("name", "what", "for_whom", "one_case"),
            "recommendation": ("flow", "why", "remains")}


def problems(reg, o):
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
        if not f.get("stages") or not all(s.get("name") and s.get("what") for s in f["stages"]):
            out.append(f"flow {f.get('name', '?')}: every flow needs its stages, each with a sentence")
    names = [f.get("name") for f in flows]
    rec = o.get("recommendation") or {}
    if rec.get("flow") and rec["flow"] not in names:
        out.append(f"the recommended flow {rec['flow']!r} is not a flow found")
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
    """What this run does to check its findings against the code, as the person reads it: independent checks of
    every finding only in a run split into reading units; otherwise one re-read of a sample."""
    if (reg / layout.UNITS_CSV).is_file():
        n = (load(reg, layout.SETTINGS) or {}).get("judges", 3)
        return (f"I will have {n} independent checks read each finding against the code; three is the kit's default.")
    return ("When the reading is done, a reader who wrote none of the findings will re-read a sample of ten of them "
            "against the code, and the run is not done until every one holds; the other findings are not checked one by "
            "one.")


def capability(reg, o):
    c, a, r = o["capability"], o["activity"], o["recommendation"]
    flows = []
    for i, f in enumerate(o["flows"], 1):
        stages = "\n".join(f"   - *{s['name']}*: {cont(s['what'])}." for s in f["stages"])
        flows.append(f"{i}. **{f['name']}.** {sentence(f['what'])} Its stages:\n{stages}")
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
**{c['name']}, in brief.** {sentence(c['what'])} It serves {cont(c['for_whom'])}. One case, the thing followed from start to end, is {cont(c['one_case'])}.

**The business flows found so far: {n}.** These come from a first look at the system's entry points and documents. A flow not found here may still exist.

{chr(10).join(flows)}

**What was looked at, and what is still open.**
- Looked at: {'; '.join(cont(x) for x in o['searched'])}.
- Still open: {'; '.join(cont(x) for x in o.get('unresolved') or ['nothing known'])}.

**The services, and which to include.** A service left out is not read; a call into it is noted as outside this run.

{services}

**Where to start.** Start with *{r['flow']}*: {cont(r['why'])}. What remains of the job after this run: {cont(r['remains'])}.

**What I will do unless you say otherwise.** I will read the services marked include above and leave out the others. {checks_said(reg)} Once the flow is mapped, I will show you its stages, and you pick how far each one goes: mapped only, measured, measured with alerts, or measured with alerts and then runbooks.

**What I need from you.** Nothing is read in depth until you answer.
1. Which flow to start with. Recommended: *{r['flow']}*.
{SEARCH_ASK + chr(10) if o.get('unresolved') else ''}"""


def reentry(reg, o):
    c, a = o["capability"], o["activity"]
    scope = load(reg, layout.SCOPE)
    st = state(reg)
    # what the run drafted; the person's picks and review are reported under what was decided, never as the run's work
    done = [cont(short(x)) for x, s in phases(reg) if s == "done" and x not in HOLDS]
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
            decided += (f" After the flow was mapped, {'a test standing in for you' if p.get('test') else 'you'} "
                        f"picked how far each stage goes, on {p.get('given', 'an earlier day')}, and that pick "
                        f"decides: {depth_said(reg, scope['depth'], '*')}."
                        + (f" In those words: \"{p['words']}\"" if p.get("words") else ""))
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
    where = (f"The run stopped at {name(current).lower() if current else 'the end'}"
             + (f", after {cont(short(last))}." if last is not None else "."))
    nxt = cont(status(reg).split("Next: ", 1)[1].split(" · ")[0])
    waits = status(reg).split("Waiting on you: ", 1)[1]
    if state(reg) and state(reg)[0] == DEPTH_PICK and (reg / PICK_FILE).is_file():
        # Waiting on the person's pick of how far each stage goes: the stages again, as last put to them
        tail = "\n**The stages you were asked to pick from, again.**\n\n" + \
               (reg / PICK_FILE).read_text(encoding="utf-8").split("\n", 2)[2]
    elif not scope:
        # Waiting on the person's picks: give them what they pick from again, not a pointer to an old message.
        tail = "\n**What you were asked to pick from, again.**\n\n" + capability(reg, o).split("\n", 2)[2]
    elif state(reg) and state(reg)[0] == REVIEW and (reg / REVIEW_FILE).is_file():
        # Waiting on the person's review of the alerts: the alerts again, as last put to them, without their old status line
        tail = "\n**The alerts you were asked to review, again.**\n\n" + \
               (reg / REVIEW_FILE).read_text(encoding="utf-8").split("\n", 2)[2]
    elif waits == "nothing":
        tail = f"\nShall I carry on with {nxt}? I recommend yes.\n"
    else:
        tail = ""
    return f"""{status(reg)}

**What this work is.** {sentence(a['for'])} The job is the whole capability: every business flow it carries, each with its stages. {sentence(a['this_run'])} One run maps one flow, so each run is one batch of the job.

**{c['name']}, in brief.** {sentence(c['what'])} It serves {cont(c['for_whom'])}. One case, the thing followed from start to end, is {cont(c['one_case'])}.

**Drafted and found so far.** {('Drafted so far: ' + '; '.join(done) + '. ') if done else 'Nothing past the first look is drafted yet. '}Flows found on the first look: {found}.

**Decided, and by whom.** {decided}

**Where it stands.** {where}

**What is next, and what waits on you.** Next comes {nxt}. Waiting on you: {waits}.{(' What remains after this run: ' + remains + '.') if remains else ''}
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


REVIEW_FILE = "alert-review.md"  # the last review message rendered, shown again on re-entry at the review
PICK_FILE = "depth-pick.md"  # the last pick message rendered, shown again on re-entry at the pick
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

    out = [status(reg), "", "**The alerts proposed, for your review.** Nothing about how each could fail, and no "
           "runbook, has been written yet: those come after your go on these alerts."]
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
                               for e in re.split(r"\s*;\s*", m.get("expectation") or "") if e in expect)
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
        out += ["", "Considered for the stage and its steps, and not proposed as alerts: " +
                ("; ".join(cont(plain(M, x)) for x in dict.fromkeys(own)) or "none") + ".",
                "", "Considered for the services and stores it uses, and not proposed as alerts: " +
                ("; ".join(cont(plain(M, x)) for x in dict.fromkeys(of_parts)) or "none") + "."]
        flow_measures = [x for x in M["measures"].values() if (x.get("flow") or "").strip() == flow_id and
                         not (x.get("stage") or "").strip() and not (x.get("step") or "").strip()]
        flow_name, flow_M = M["flow"]["name"], M
    if stage_ids:  # the flow's own measures belong to the flow: listed once, not under every stage
        flow_other = [x["measure"] for x in flow_measures if x["handle"] not in proposed]
        out += ["", f"### The flow as a whole: {cont(flow_name)}", "",
                "Considered for the flow, and not proposed as alerts: " +
                ("; ".join(cont(plain(flow_M, x)) for x in dict.fromkeys(flow_other)) or "none") + "."]
    out += ["", f"**My recommendation.** {sentence(recommend)}", "",
            "**What you can decide.** Keep these alerts as they are, drop one, change one or add one; or say go on "
            "to the runbooks."]
    return "\n".join(out) + "\n", names, measure_names


def review_terms(text, measure_names):
    """The kit-term check of the review, except inside a measure's own name: the register's name for what is counted
    (a route, a queue) is how the person finds it, as a part's name is."""
    for n in sorted((n for n in measure_names if n), key=len, reverse=True):
        text = text.replace(n, " ")
    return kit_terms(text)


def mark_the_pick_stop(reg):
    """The pick message is the stop after mapping: the capability row done and the pick row doing."""
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"^(\| 3 [^|]*\| )[^|]*\|", r"\1done |", text, count=1, flags=re.M)
    text = re.sub(r"^(\| Pick of how far each stage goes \| )(?:to do|doing) \|", r"\1doing |", text, count=1,
                  flags=re.M)
    p.write_text(text, encoding="utf-8", newline="\n")


def count_word(n):
    return ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")[n] if n <= 10 else str(n)


def replaced_stages(reg, walked):
    """(the first look's stage names, the walk's) for the flow the person picked when the walk's differ from the first
    look's, else None. The first look's flow is the one named at the go, else the one it recommended."""
    o = load(reg, "orientation.json") or {}
    picked = (load(reg, layout.SCOPE) or {}).get("flow") or (o.get("recommendation") or {}).get("flow")
    flow = next((f for f in o.get("flows") or [] if (f.get("name") or "").strip() == (picked or "").strip()), None)
    first = [(s.get("name") or "").strip() for s in (flow or {}).get("stages") or [] if (s.get("name") or "").strip()]
    walked = [n for n in walked if n]
    if not first or not walked or [n.lower() for n in first] == [n.lower() for n in walked]:
        return None
    return first, walked


def depth_review(reg, flow_id, recommend):
    """The message for the person's pick of how far each stage goes, after mapping: each stage of the flow with its process
    steps, the session's recommendation in its one slot, and their options."""
    import flow_outputs as fo
    R = fo.load(reg)
    out = [status(reg), "", "**The flow is mapped.** Pick how far each of its stages goes. Nothing is measured until "
           "you answer; a stage you do not name stays mapped only."]
    names = set()
    walked = sorted((x for x in R["stages"] if x.get("flow") == flow_id), key=lambda x: int(x.get("order") or 0))
    replaced = replaced_stages(reg, [(s.get("name") or "").strip() for s in walked])
    if replaced:
        first, now = replaced
        names |= set(first) | {cont(n) for n in first}
        out += ["", "**Mapping replaced the first look's stages.** "
                f"The first look proposed {count_word(len(first))}: {'; '.join(cont(n) for n in first)}. "
                f"Mapping the code found {count_word(len(now))}: {'; '.join(cont(n) for n in now)}. "
                "The stages below are the ones you pick from."]
    for s in walked:
        M = fo.build(R, flow_id, s["stage"])
        names |= set(fo.given_names(M)) | {cont(n) for n in fo.given_names(M)}
        steps = "; ".join(cont(x.get("name") or "") for x in M["steps"] if (x.get("name") or "").strip())
        out += ["", f"**{s['name']}**", "", f"Its steps: {steps or 'none recorded'}."]
    out += ["", f"**My recommendation.** {sentence(recommend)}", "",
            "**What you can decide.** For each stage: mapped only; measured; measured, with alerts you then review; "
            "or measured, with alerts and then runbooks."]
    return "\n".join(out) + "\n", names


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if argv[:1] == ["depth"]:
        args = argv[1:]
        recommend = ""
        if "--recommend" in args:
            i = args.index("--recommend")
            recommend = args[i + 1] if i + 1 < len(args) else ""
            args = args[:i] + args[i + 2:]
        if len(args) != 2 or not recommend.strip():
            print("Usage: python brief.py depth <register folder> <flow id> --recommend \"<your recommendation and "
                  "its reason>\"", file=sys.stderr)
            return 2
        run_lock.guard(args[0])
        run_md = pathlib.Path(args[0]) / "RUN.md"
        before = run_md.read_bytes() if run_md.is_file() else None
        mark_the_pick_stop(args[0])
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
        import depth  # the page draws this stop's open choice from depth.json
        import go
        go.record_flow_id(pathlib.Path(args[0]), args[1])  # found by id, not by a name the walk may change
        depth.write_quietly(args[0])
        print(with_page(text, args[0]))
        return 0
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
        if not after:  # --after: a line added to a message a script printed, which has its status line already
            print(status(pathlib.Path(args[0])))
            print()
        print(with_page(text, args[0]))
        return 0
    if argv[:1] == ["page"]:
        if len(argv) != 2 or not pathlib.Path(argv[1]).is_dir():
            print(__doc__, file=sys.stderr)
            return 2
        line = page_line(argv[1])
        if line:
            print(line)
        return 0
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
    bad = problems(reg, o)
    if bad:
        print("REFUSED: " + "; ".join(bad) + ". Fix orientation.json and run this again.", file=sys.stderr)
        return 2
    run_md = reg / "RUN.md"
    before = run_md.read_bytes() if run_md.is_file() else None
    if what == "capability":
        mark_the_stop(reg)
    text = capability(reg, o) if what == "capability" else reentry(reg, o)
    faults = prose_faults(text)
    if faults:
        if before is not None:
            run_md.write_bytes(before)
        print("REFUSED: the brief does not read as prose where orientation.json's text was filled in: "
              + "; ".join(faults) + ". Rewrite those fields so each reads in its sentence, and run this again.",
              file=sys.stderr)
        return 2
    if what == "capability":
        (reg / "PLAN.md").write_text(text, encoding="utf-8", newline="\n")
        import start  # the first look has reached its brief: its mark in the work folder ends here
        if reg.resolve().parent.name == "bfo-work":
            start.end_first_look(reg.resolve().parent)
        import depth  # the page draws this stop's open choice from depth.json
        depth.write_quietly(reg)
    print(with_page(text, reg))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
