"""What the person reads, rendered from the run's files: the status line, the capability brief and the re-entry brief.

Usage: python brief.py status <register folder>       one line; every message to the person opens with it
       python brief.py capability <register folder>   the capability brief for the chat; in full, written to PLAN.md
       python brief.py reentry <register folder>      the re-entry brief, for a run picked up again
       python brief.py terms <file>                   ids and kit terms found in a text (exit 1 if any)
       python brief.py say <register folder> <message file> [--after | --report] [--kit]
                                                      a message for the person: refused (exit 1) if it uses this
                                                      run's ids or work-folder file names, or a card lacks its
                                                      structure; any other word is advice; else printed after the
                                                      status line and ending with the page's address (--after: a
                                                      line added after a script's message, which has both: neither
                                                      is added; --report: the report, the kit's Done and Checked
                                                      fields put under the status line, before the message's own
                                                      tables; --kit: a message the kit built, never refused). A
                                                      paragraph outside the cards is advice.
                                                      Refused three times running, the next try is sent with a line
                                                      saying so. Before a register exists, give the workspace root
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
a flow it did not find, or carries an id of this run or a file of its work folder (other words are advice).
Exit 0 done; 1 refused by `say`, or terms found by `terms`; 2 refused otherwise, or wrong usage.
Python standard library only."""
import contextlib
import csv
from collections import Counter
import io
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import register_layout as layout  # noqa: E402
import run_lock  # noqa: E402
import run_md  # noqa: E402

STATUS_LEAD = "**Where things stand:**"
# Every stop that needs the person's call asks it in question cards (question_card.py), one decision per card, each
# standing alone (what it is, why, the choices, the recommendation), numbered "1 of N" when a message holds several.
STILL_TO_ANSWER = "STILL TO ANSWER (send this as your message, as it is, and wait):"


def search_text(x):
    """An open item of the first look as one line of text: a string as written, or a structured item's `what`."""
    return x if isinstance(x, str) else (x or {}).get("what", "")


# "<what is open>, so I propose to look in <where>" / "<what>, which I propose to look for on <where>"
PROPOSE = re.compile(r",?\s*(?:so |which |and )?I (?:propose|would like|suggest) to (look|search|read|check|ask you)"
                     r"(?: for(?: it| them)?)?(?: in| on| at| through)?(?:[\s,]+(.+))?$", re.I)
NOT_TIED = "not tied to a flow in what I found"
OWNERS = re.compile(r"(?i)\b(?:own(?:s|er|ers|ership)?|answers? for|responsib\w+|on-call)\b")


def split_search(x):
    """(what is open, where the run proposes to look, whether it proposes to ask the person instead) of one open
    item; where is "" when the text does not say."""
    if isinstance(x, dict):
        return cont(x.get("what", "")), cont(x.get("look_where", "")), bool(x.get("ask_person"))
    m = PROPOSE.search(x or "")
    if not m:
        return cont(x), "", False
    asks = m.group(1).lower() == "ask you"
    where = "" if asks else (m.group(2) or "")  # what follows "ask you" is the reason to ask, never a place
    return cont(x[:m.start()]), cont(where), asks


def affects_of(o, x):
    """Which flows an open item bears on, from the record: a structured item's own `affects`, else every flow whose
    services include one the item's text names (a service named in all flows, such as a front end, decides nothing);
    "" when the record ties it to no flow."""
    if isinstance(x, dict) and x.get("affects"):
        return x["affects"]
    flows = o.get("flows") or []
    squashed = re.sub(r"[^a-z]", "", search_text(x).lower())
    common = set.intersection(*(set(f.get("services") or []) for f in flows)) if flows else set()
    hit = []
    for f in flows:
        for s in set(f.get("services") or []) - common:
            core = re.sub(r"[^a-z]", "", s.lower().removesuffix("service"))
            if len(core) > 3 and core in squashed:
                hit.append(f["name"])
                break
    return ("only " if len(hit) == 1 else "") + and_list(hit) if hit else ""


def search_card(o, x, first_flow=None):
    """One open item of the first look as a question card's parts (question_card.card): what is open, where the run
    would look, which flow it bears on, why it is asked, and the choices; owners are asked of the person first.

    Its Why and its No say this item's own consequence from the record: the flows whose services the item names
    (affects_of), or, when the record ties it to none, that it is tied to no flow in what was found. A search is
    offered only with a place to look: an item that names none, or proposes to ask the person, is asked of them."""
    what, where, ask = split_search(x)
    ask = ask or not where  # a search with no Look where would search nowhere in particular
    affects = affects_of(o, x)
    flows = re.sub(r"^only ", "", affects)
    relies = "rely" if " and " in flows else "relies"
    fields = [("What", what), ("Look where", "" if ask else where + ", read-only"), ("Affects", affects or NOT_TIED)]
    short = re.split(r",\s", what, maxsplit=1)[0]  # the title is one line: the item up to its first clause
    owners = OWNERS.search(search_text(x))
    why = (x.get("why") if isinstance(x, dict) else "") or (
        "each alert's Wakes line names the owner of the part it watches; with none, it says not yet known" if owners
        else f"{flows} {relies} on it, and the code I was given does not show it" if flows
        else "the code I was given does not show it, and it is tied to no flow in what I found")
    without = f"the work on {flows} goes on without it" if flows else "the work goes on without it"
    if owners:
        choices = [("Tell me", "you name who owns each part, or where your team records it; I write it down")]
        if not ask:
            choices.append(("Search", f"I search {where}, read-only; it finds the code's authors, not your teams"))
        choices.append(("Skip", "nobody looks; every alert wakes someone not yet known"))
        return dict(title="Who owns each part of the system?", fields=fields, why=why, choices=choices,
                    recommended=(1, "you know your teams better than any public source"))
    if ask:  # only the person can say, or there is nowhere to look: asked of them, never searched
        return dict(title=f"Do you know {short}?", fields=fields, why=why,
                    choices=[("Tell me", "you say what it is, or where your team records it; I write it down"),
                             ("Not known", f"it stays listed as not known; {without}")],
                    recommended=(1, "only your teams can say"))
    elsewhere = bool(first_flow and flows and first_flow not in flows)
    choices = [("Yes", "I search there, read-only, and add what I find"),
               ("No", f"I search nothing; it stays listed as not looked up, and {without}")]
    rec = ((2, f"it is not needed for {first_flow}") if elsewhere else
           (1, f"{flows} {relies} on it; the search is read-only" if flows else "the search is read-only"))
    return dict(title=f"May I search for {short}?", fields=fields, why=why, choices=choices, recommended=rec)


def search_asks(o, asks_flow=True):
    """The first look's proposed searches, numbered after the flow pick when the brief asks it: [(number, the card's
    parts)]. A search runs only on a yes."""
    first = 2 if asks_flow else 1
    flow = (o.get("recommendation") or {}).get("flow") if asks_flow else None
    return [(first + i, search_card(o, x, flow)) for i, x in enumerate(o.get("unresolved") or [])]
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
BEFORE_THE_REVIEW = (None, 0, 1, CASE, STRUCTURE, CAPABILITY, DEPTH_PICK, MEASURES)  # no open item said yet
HELD_BY_OPEN = (RUNBOOKS, 5, 6)  # the runbooks wait on open alert items: the run puts them right next
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
    if not url and any((site / f).exists() for f in (listener.LOG_FILE, listener.URL_FILE, listener.PID_FILE)):
        try:  # a listener served this work and has died: start it again, once, opening no tab
            url = listener.start(site)[0]
        except OSError:
            return ("The page is not answering: the listener could not be started. Say so in the chat; the run "
                    "goes on without the page.")
    if not url:
        return ""
    if (folder / "index.html").is_file():  # the run's home, where its picks wait
        page = ("" if site == folder else folder.name + "/") + "index.html"
    elif (folder / "RUN.md").is_file():  # else this register's own run status page
        page = ("" if site == folder else folder.name + "/") + "operator.html"
    else:
        import start  # before a register: this run's own run status page, the address the start step opened
        page = start.run_page(site)
    got = listener.ask_check(url, "/" + page.lstrip("/"))  # never counted as the person's tab
    if got is not None and got.get("status") != 200:  # the listener says this address does not answer
        why = ("the run's start folder is gone" if "_start-" in page else
               "the listener does not serve this folder")
        return (f"The page is not answering: {why}. Restart the page (listener.py up, as at every stop) and say so "
                "in the chat.")
    return PAGE_LEAD + url + page


def with_kit(text):
    """The text with the kit release ("Kit 9.9.1", page_style.kit_version) at the end of its first line."""
    import page_style
    if not page_style.kit_known():  # no marker: the kit's source, never an installed kit
        return text
    first, nl, rest = text.partition("\n")
    return f"{first} · {page_style.kit_version()}{nl}{rest}"


def with_page(text, folder):
    """`text` with the page's address on a last line of its own while a listener serves the work, and, the first time
    a message goes out after the run put right open items a go was given on, the line naming that fix under its
    status line: such a fix is told, never reviewed again (go.record_open_fixed)."""
    import go
    told = go.take_untold(folder) if (pathlib.Path(folder) / layout.SCOPE).is_file() else []
    if told:
        first, sep, rest = text.partition("\n\n")
        text = f"{first}\n\n" + "\n\n".join(told) + (f"\n\n{rest}" if sep else "")
    notes = cap_notes()  # a message taken after CAP refusals says so, above the page's address
    if notes:
        text = text.rstrip() + "\n\n" + "\n".join(notes)
    line = page_line(folder)
    return f"{text.rstrip()}\n\n{line}" if line else text


def state_names(*states):
    """Each lifecycle state as written and as the pages name it (stage_flow_views.state_name: AwaitingValidation reads
    "Awaiting validation"), without a state marked implicit or none."""
    import stage_flow_views as sfv
    out = set()
    for s in states:
        s = (s or "").strip()
        if s and not s.startswith(("(", "implicit:")):
            out |= {s, sfv.state_name(s)}
    return out


WORDS_REFUSED = "REFUSED: the message uses words the person does not know"
FINISH_CLAIM = re.compile(r"(?i)\b(?:(?:the )?run (?:is|was|has) (?:now )?(?:finished|complete|completed|done)|"
                          r"(?:all|everything is|we are|we're) (?:finished|done|complete)|"
                          r"the work is (?:finished|done|complete))\b")


def finish_claimed(text):
    return bool(FINISH_CLAIM.search(text or ""))


def reconcile_phases(reg):
    """Every phase its files prove done written into RUN.md before a message goes out (run_md.reconcile)."""
    run_md.reconcile(reg)


def run_finished(reg):
    """The run is finished only when the done check said DONE on the map as it is now, after this flow's go: an
    earlier flow's DONE says nothing of the flow under way."""
    import run_status
    return run_status.verdict_holds(pathlib.Path(reg)) and run_md.verdict_this_flow(reg)


def end_said(reg):
    """The end-of-run message, built from the done check's own result: finished only when it said DONE on the map as
    it is; otherwise not finished, with how many things it still owes."""
    import run_status
    reg = pathlib.Path(reg)
    if run_finished(reg):
        return "The run is finished: the final check passed on the map as it is now."
    _, reasons = run_status.verdict(reg)
    n = len(reasons)
    return ("The run is not finished: the final check has not passed"
            + (f" and still owes {n} {'thing' if n == 1 else 'things'}" if n else "")
            + ". I am putting that right next, and will tell you when the check passes.")


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
                if f.name == "lifecycle.csv":  # the case's states (Paid, AwaitingValidation) are the business's names
                    names |= state_names(row.get("from_state"), row.get("to_state"))
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


QUOTE = re.compile(r'"[^"\n]*"|“[^”\n]*”')


def unquoted(text):
    """The text with every double-quoted span (straight or curly) set aside: words quoted from a source or from the
    person are theirs, never the session's, so no check judges them."""
    return QUOTE.sub(" ", text or "")


def say_terms(text, reg):
    """The terms check of a message the session wrote, outside what the person knows already: the register's own
    names, words quoted back in double quotes (theirs, as they said them) and a web address."""
    text = re.sub(r"https?://\S+", " ", text)
    # an address without its scheme: a host with a dot or localhost, a port maybe, then a path
    text = re.sub(r"\b(?:localhost|[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,})(?::\d+)?/[^\s,;)]*(?<![.,])", " ", text)
    for n in register_names(reg):  # as written, or with its first letter lower-cased mid-sentence
        text = re.sub("(?i:" + re.escape(n[:1]) + ")" + re.escape(n[1:]), " ", text)
    # quoted words are a source's or the person's own, as they said them, and are never judged
    text = unquoted(text)
    hits = kit_terms(text)
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


def reason_refused(text, reg):
    """What a recommendation's reason is refused for, each with what to change; [] when it is taken. Only what code
    decides exactly: an empty reason, or an id of this run's register or a file of its work folder (refused_terms).
    Everything else reason_faults names (sentences, a semicolon, its length, the code's terms) is advice."""
    t = (text or "").strip()
    if not t:
        return ["it is empty: say in one short sentence why"]
    hits = refused_terms(say_terms(t, reg), reg)
    return [f"it uses words the person does not know ({', '.join(hits)}): say each in the person's terms"] if hits else []


def reason_faults(text, reg):
    """What breaks the rule in a recommendation's reason, each with what to change; [] when it holds. The rule: one
    sentence, no semicolon, at most REASON_WORDS words, and no id or kit term that `say` would refuse. Only those
    reason_refused names refuse; the rest is advice for the writer."""
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
    hits = refused_terms(say_terms(t, reg), reg)
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


def reason_advice(text, reg):
    """The words of a reason that a person may not know and that are not refused: advice only."""
    return split_terms(say_terms((text or "").strip(), reg), reg)[1]


def refuse_reason(text, reg, kind="reason"):
    """Print the refusal of a `--recommend` reason that reason_refused refuses, and say so; nothing is written before
    it. What else breaks the rule, and words that are only advice, are printed as advice. A reason refused for its
    words CAP times running is taken on the next try (still_refused); an empty one is always refused."""
    refused = reason_refused(text, reg)
    advise([f"the reason: {f}" for f in reason_faults(text, reg) if f not in refused] + reason_advice(text, reg),
           lead="the reason shown to the person is best one short plain sentence in the business's terms;")
    if refused and (text or "").strip() and not still_refused(reg, kind, True, "the person's terms in its reason"):
        return False
    if not refused:
        still_refused(reg, kind, False)
    if refused:
        print(f"REFUSED: {REASON_RULE}; " + "; ".join(refused) + ". Rewrite --recommend and run this again. Nothing "
              "written.", file=sys.stderr)
    return bool(refused)


# What a message is refused for: only what code decides exactly over what the kit holds. An id that is an id of this
# run's register, and a file name or path that is a file in the run's own work folder. Every other hit of KIT_TERMS,
# of the prose checks and of the reason's technical words is advice for the session writing the message: whether a
# word is one the person knows is a judgment, and a bank's own words ("the receipt for the loan participation", "a P1
# incident", "the merge of two business units") must never stop a run.
ID_TERM = KIT_TERMS[0][0]
FILE_TERMS = (KIT_TERMS[1][0], KIT_TERMS[2][0])
ADVICE = "ADVICE, for you and not the person (nothing was refused, and this line is not part of the message):"


def register_ids(reg):
    """Every id this run's register gives: each value of an id column (stage, step, flow, handle, id, or a column
    ending in _id) of its tables and its reading units' tables, a cell listing several split."""
    reg = pathlib.Path(reg)
    out = set()
    for f in list(reg.glob("*.csv")) + list(reg.glob("units/*/*.csv")) + list(reg.glob("units/*.csv")):
        try:
            with f.open(encoding="utf-8-sig", newline="") as fh:
                for row in csv.DictReader(fh):
                    for c, v in row.items():
                        if c and v and (c in ("stage", "step", "flow", "handle", "id") or c.endswith("_id")):
                            out |= {x for x in re.split(r"[;,\s]+", v.strip()) if x}
        except (OSError, csv.Error, UnicodeDecodeError):
            continue
    return out


def work_files(reg):
    """(file names, posix paths relative to the work folder) of every file in the run's own work folder: the work
    folder the register sits in (bfo-work), else the register folder."""
    reg = pathlib.Path(reg).resolve()
    site = reg.parent if reg.parent.name == "bfo-work" else reg
    names, rels = set(), set()
    for d, _, files in os.walk(site):
        for n in files:
            names.add(n)
            rels.add((pathlib.Path(d) / n).relative_to(site).as_posix())
    return names, rels


def refused_terms(hits, reg):
    """The hits a message is refused for: an id of this register, or a file name or path of a file in the run's own
    work folder. A file name that is only the kit's (README.md, index.html, settings.py are names a business's own
    files have too) is advice, as is every other hit."""
    ids, files, out = None, None, []
    for h in hits:
        bare = h.split(" (")[0].strip()
        if re.fullmatch(ID_TERM, bare):
            ids = register_ids(reg) if ids is None else ids
            if bare in ids:
                out.append(h)
        elif any(re.fullmatch(p, bare) for p in FILE_TERMS):
            files = work_files(reg) if files is None else files
            norm = bare.replace("\\", "/").strip("/")
            if norm in files[0] or any(r == norm or r.endswith("/" + norm) for r in files[1]):
                out.append(h)
    return out


def split_terms(hits, reg):
    """(refused, advice) of a terms check's hits."""
    refused = refused_terms(list(dict.fromkeys(hits)), reg)
    return refused, [h for h in dict.fromkeys(hits) if h not in refused]


def advise(items, lead="consider plainer words, or a rewrite, for:"):
    """Print the advice on stderr, never on stdout, which is the message the person is sent."""
    items = list(dict.fromkeys(i for i in items if i))
    if items:
        print(f"{ADVICE} {lead} " + "; ".join(items), file=sys.stderr)


# A refusal of a message's own text (its words, its reason, its card form) asks the session to fix it and run the
# command again. After CAP refusals running of one kind of message, the next try is taken and sent with CAP_LINE
# naming the check it did not meet, so one bad message never stops the run. A pass of that kind starts the
# count again. The count is the run's own bookkeeping, kept beside the register's tables, never in them.
CAP = 3
CAP_FILE = "refusal-count.json"
CAP_LINE_LEAD = "Sent after three tries:"
_CAP_NOTES = []  # the lines a capped refusal owes the message being rendered now; with_page adds them


def _cap_file(folder):
    """Where the refusal count is kept: in the register (run_lock.is_register, or a folder inside the work folder),
    else in the work folder under the workspace root given before a register exists; None when there is neither, so
    nothing is ever written beside the person's own files (and nothing is counted)."""
    import run_lock
    import start
    folder = pathlib.Path(folder).resolve()
    # in this run's own folder of the work folder (start.run_dir), so a count left by an earlier run never carries over
    if folder.parent.name == "bfo-work":
        return start.run_dir(folder.parent) / CAP_FILE
    if run_lock.is_register(folder):  # a register outside a work folder is its own site (first_look.site_of)
        return start.run_dir(folder) / CAP_FILE
    if folder.name == "bfo-work":
        return start.run_dir(folder) / CAP_FILE
    return start.run_dir(folder / "bfo-work") / CAP_FILE if (folder / "bfo-work").is_dir() else None


def still_refused(reg, kind, refused, check=""):
    """Whether a refusal of `kind` stands: True while it has been refused CAP times running or fewer; False when it
    is not refused (the count of `kind` starts again) or when this is the try after CAP refusals, which is taken, its
    line naming `check` kept for the message (with_page). Once a cap is taken in a call, every later check of the same
    call takes its text too (the reason taken is in the message rendered from it), uncounted."""
    if _CAP_NOTES:
        return False
    f = _cap_file(reg)
    if f is None:
        return bool(refused)
    try:
        counts = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
        counts = counts if isinstance(counts, dict) else {}
    except (OSError, ValueError):
        counts = {}
    n = (int(counts.get(kind) or 0) + 1) if refused else 0
    stands = bool(refused) and n <= CAP
    if refused and not stands:
        n = 0
        _CAP_NOTES.append(f"{CAP_LINE_LEAD} this message did not meet the kit's check of {check or 'its form'}, "
                          "and is sent as it is.")
    if n:
        counts[kind] = n
    else:
        counts.pop(kind, None)
    try:
        if counts or f.is_file():
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(counts) + "\n", encoding="utf-8", newline="\n")
    except OSError:
        pass
    return stands


def cap_notes():
    """The lines capped refusals owe the message rendered now, taken once."""
    got = list(dict.fromkeys(_CAP_NOTES))
    _CAP_NOTES.clear()
    return got


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


def _strings(x, path=""):
    if isinstance(x, str):
        yield path, x
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from _strings(v, f"{path}.{k}" if path else k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _strings(v, f"{path}[{i}]")


def fault_fields(o, faults):
    """Each prose fault with the orientation.json field its text came from, where one holds it, so one pass of edits
    fixes every fault: the snippet's longest stretch between the dots is looked up in every text field."""
    fields = list(_strings(o or {}))
    out = []
    for f in faults:
        snip = f.split(": ", 1)[-1].strip(".")
        pieces = sorted((s.strip() for s in re.split(r"\.\.\.", snip) if s.strip()), key=len, reverse=True)
        core = pieces[0] if pieces else ""
        hit = next((p for p, s in fields if core and core in s), None)
        if hit is None and core:
            words = core.split()
            for n in range(len(words), 1, -1):
                cand = " ".join(words[-n:])
                hit = next((p for p, s in fields if cand in s), None)
                if hit:
                    break
        out.append(f"{f} (in orientation.json: {hit})" if hit else f)
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
    text = p.read_text(encoding="utf-8")
    try:  # a phase its files prove done reads done, whether or not the lead set the row
        text = run_md.derived(text, run_md.proved(reg))
    except Exception:  # noqa: BLE001
        pass
    for line in text.splitlines():
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
    elif st == "mapping" and sub == "pick":  # Business Impact is written; the pick's own row says the run waits on it
        now = {CASE: "done", STRUCTURE: "done", CAPABILITY: "done"}
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


def started_skill(reg):
    """"kit" or "mapping": which skill's start step began this run, as start.py records it in the work folder; None
    when no record is found. `reg` is a register folder, or the workspace root before a register exists."""
    reg = pathlib.Path(reg)
    import start
    work = reg / "bfo-work"
    tries = ([start.start_file(work, start.STARTED)] if work.is_dir() else []) + [
        reg / "_run-state" / start.STARTED, reg.parent / start.STARTED]
    record = next((p for p in tries if p.is_file()), None)
    try:
        return json.loads(record.read_text(encoding="utf-8")).get("skill") if record else None
    except (OSError, ValueError, AttributeError):
        return None


def activity_count(reg):
    """How many activities the person was told there are: three when the mapping skill started the run on its own,
    six when the stage kit did (start.py records which, in the work folder). `reg` is a register folder, or the
    workspace root before a register exists, whose work folder holds the record."""
    reg = pathlib.Path(reg)
    import start
    work = reg / "bfo-work"
    tries = ([start.start_file(work, start.STARTED)] if work.is_dir() else []) + [
        reg / "_run-state" / start.STARTED, reg.parent / start.STARTED]
    record = next((p for p in tries if p.is_file()), tries[-1])
    try:
        d = json.loads(record.read_text(encoding="utf-8"))
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


FAST_MADE = {5: "the map, its cited lines checked by script and drawn again"}  # a fast map: no reader re-read it


def made(act, reg=None):
    """What an activity left made, as the status line's Drafted field says it."""
    if reg is not None and act in FAST_MADE:
        import run_status
        if run_status.is_fast(reg):
            return FAST_MADE[act]
    return MADE.get(act) or short(act)


WHAT_WORDS = 30  # the brief's "What it does" field: well inside a field's limit (question_card.FIELD_WORDS)


def what_it_does(text, cap=WHAT_WORDS):
    """The capability's what, for its own field of the first brief: its first sentence, cut at a semicolon, colon or
    dash if it has one, never at a comma, since a comma in a what most often parts the items of a list ("browse a
    catalogue, fill a cart, pay for it") and a cut there drops the meaning. Longer than `cap` words, its first `cap` words and "…", so a cut shows."""
    what = re.split(r"(?<=[.!?])\s+(?=[A-Z])", (text or "").strip(), maxsplit=1)[0]
    what = re.split(r"; |: | — ", what, maxsplit=1)[0].strip().rstrip(".")
    words = what.split()
    if len(words) > cap:
        what = " ".join(words[:cap]).rstrip(",;:") + "…"
    return what[:1].upper() + what[1:]


def fast_checked_said(reg):
    """What was checked of a fast map, for the report: the rows the proposals rest on, one check each, and how many
    were confirmed or flagged; every other row unchecked. Never "every finding" or a count of checks per row. One
    clause: the long account of who checks and how is said where the check runs, not in the report."""
    import selective
    sel = selective.selected(reg) or {}
    n = sum(len(v) for v in sel.values())
    if not n:
        return ["no row read against the code by a second reader"]
    got = selective.verdicts(reg)
    flagged = sum(1 for v in got.values() if v and v != "says")  # judges.VERDICTS: says, does not say, unclear
    out = [f"{n} rows against the code, one check each · {len(got) - flagged} confirmed · {flagged} flagged"
           + (f" · {n - len(got)} not yet read" if len(got) < n else "")]
    return out


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
    taken = [f"{mark}{names.get(s) or s}{mark} " + DEPTH_WORDS.get(d, d)
             for s, d in depth.items() if d != "none"]
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
    st.sort(key=lambda r: int(r.get("order") or 0) if str(r.get("order") or "").strip().isdecimal() else 0)
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
    elif open_record(reg)["items"]:  # reviewed, and the checks still find open items: said, and put right next
        rec = open_record(reg)
        n = len(rec["items"])
        now, drafted, nxt, waiting = (f"The measures reviewed, with {count_word(n)} open item{'' if n == 1 else 's'}"
                                      + (" left open at your word" if rec["left_open"] else ""),
                                      "the measures for the stages you picked",
                                      MEASURES_NEXT if rec["left_open"] else "putting the open items right", "nothing")
    else:
        now, drafted, nxt, waiting = ("The measures reviewed", "the measures for the stages you picked",
                                      MEASURES_NEXT, "nothing")
    return f"{STATUS_LEAD} Flow: {flow} · Stage: {stage} · {now} · Drafted: {drafted} · Next: {nxt} · Waiting on you: {waiting}"


def status(reg):
    """The status line, with the run's stop record (run_state.read_stop): a stopped run says so and what to do,
    never "Waiting on you: nothing". The line goes out with the lead's own messages, so the lead is in its turn: the
    rest of the run's state (its turn ended, no sign of work) cannot hold, and reading the agents' transcripts for it
    on every message would cost the run its time. A page that shows the line while nobody writes (the work page)
    passes the whole state through stopped_line."""
    line = _status(reg)
    try:
        import run_state
        stop = run_state.read_stop(reg)
    except Exception:  # noqa: BLE001 - a record mid-write: the line as the run record has it
        return line
    return stopped_line(line, {"state": "stopped", **stop}) if stop else line


def stopped_line(line, run):
    """`line` as run_state's state `run` says it: stopped, with the reason and what to do; any other state as it is."""
    if run.get("state") != "stopped":
        return line
    head = line.split(" · Stopped: ", 1)[0] if " · Stopped: " in line else (
        line.rpartition(" · Waiting on you: ")[0] or line)
    return f"{head} · Stopped: {run['reason']} · Waiting on you: {run.get('next') or ''}"


def _status(reg):
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
        rec = open_record(reg)
        n = len(rec["items"])
        if n and rec["left_open"]:  # the person said go on with them open: listed, never held
            return (f"{lead} Draft complete, with {count_word(n)} open item{'' if n == 1 else 's'} left open at your "
                    f"word{pending} · Drafted: {drafted_said(reg, last)} · Next: "
                    + ("the next flow" if left else "nothing") + " · Waiting on you: nothing")
        if n:  # a draft whose own checks still fail: said here, and putting it right comes before anything else
            return (f"{lead} Draft complete, with {count_word(n)} open item{'' if n == 1 else 's'}{pending} · "
                    f"Drafted: {drafted_said(reg, last)} · Next: putting the open items right · Waiting on you: "
                    "nothing")
        return (f"{lead} Draft complete{pending}, for your review · Drafted: {drafted_said(reg, last)} · Next: "
                + ("the next flow · Waiting on you: nothing" if left else "nothing · Waiting on you: nothing"))
    waiting = "the run is blocked; the message below says why" if blocked else WAITS.get(current, "nothing")
    unanswered = [x for x in scope.get("searches") or [] if x.get("answer") == "open"]
    if unanswered and not blocked:  # a search the first look proposed, not yet answered: the run waits on it
        waiting = (f"your answer on {count_word(len(unanswered)).lower()} search"
                   f"{'es' if len(unanswered) != 1 else ''} the first look proposed")
    if after is not None:
        nxt = short(after)
    elif current == len(ACTIVITIES):  # the last activity is the report itself: next is what follows it
        nxt = "the next flow" if flows_left(reg) else "nothing more: this is the last step"
    else:
        nxt = "the report"
    # while it waits on the person, the activity would only repeat what it waits on
    now = "" if waiting != "nothing" and not blocked and current in HOLDS else f" {name(current, count)} ·"
    opened = ""
    if current not in BEFORE_THE_REVIEW:  # from the measures review on, the draft's open items, one count
        rec = open_record(reg)
        n = len(rec["items"])
        if rec.get("unreadable"):
            opened = " Open items: could not be checked ·"
        elif n:
            opened = f" Open items: {count_word(n).lower()} open item{'' if n == 1 else 's'}" + (
                ", left open at your word ·" if rec["left_open"] else " ·")
            if not rec["left_open"] and waiting == "nothing" and current in HELD_BY_OPEN:
                nxt = "putting the open items right"  # the runbooks wait on them: the report does not come next
    return f"{lead}{now}{opened} Drafted: {drafted_said(reg, last)} · Next: {nxt} · Waiting on you: {waiting}"


def drafted_said(reg, last):
    """The status line's Drafted field: what the last activity left made, and that the map is not checked when the
    person stopped its checks, wherever the run then waits."""
    drafted = made(last, reg) if last is not None else "nothing yet"
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
        # only an id or a work file in it refuses; the rest of the rule is advice (why_advice)
        out += [f"recommendation.why: {REASON_RULE}; {f}" for f in reason_refused(rec["why"], reg)]
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
    hits = refused_terms(orientation_terms(reg, o, surveyed), reg)
    if hits:
        out.append(f"ids or file names of this run in the person's text: {', '.join(sorted(set(hits)))}")
    if brief_now and (reg / "about.csv").is_file() and not any(
            (r.get("system") or "").strip() for r in rows(reg / "about.csv")):  # started by start_register, never filled
        out.append("about.csv has no row with the system: the first look writes it (the system, the configuration "
                   "that runs, the sources examined) before the brief; the pick page is drawn from it")
    if brief_now:  # every source that is not code read, proven from the transcripts (first_look.py)
        import first_look
        out += first_look.brief_problems(reg, o)
        out += first_look_citation_problems(reg, o)
    return out


def orientation_terms(reg, o, surveyed=None):
    """Every hit of the terms check in the text of orientation.json the person reads (its flows' citations and
    sources aside), the surveyed services' names let through."""
    if surveyed is None:
        surveyed = {r["service"].strip() for r in rows(pathlib.Path(reg) / "survey.csv")
                    if (r.get("kind") or "").strip() == "service" and (r.get("service") or "").strip()}
    flows = (o or {}).get("flows") or []
    text = json.dumps({k: v for k, v in (o or {}).items() if k != "flows"}, ensure_ascii=False) + " ".join(
        json.dumps({k: v for k, v in f.items() if k not in ("found_in", "seen_in")}, ensure_ascii=False)
        + " " + seen_of(reg, f) for f in flows)
    text = text.replace('"name"', "")
    return [h for h in kit_terms(text) if h not in surveyed]


def first_look_citation_problems(reg, o=None):
    """A citation the first look wrote (about.csv, each flow's found_in) that names a file only by its path inside a
    repository, when the file is found under the repository's folder: every later step opens a citation as written,
    from the folder that holds the repositories, so it names the repository's folder first."""
    import fast_map
    reg = pathlib.Path(reg)
    ws = fast_map.workspace(reg)
    texts = [" ".join(v or "" for v in r.values()) for r in rows(reg / "about.csv")]
    if o is None:
        try:
            o = json.loads((reg / layout.ORIENTATION).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            o = {}
    texts += [str(f.get("found_in") or "") for f in (o or {}).get("flows") or []]
    spans = [s for text in texts for s in fast_map.spans(text)]
    if not spans or not ws.is_dir():
        return []
    repos = [d for d in ws.iterdir() if d.is_dir()]  # one level only: the repositories sit side by side in ws
    out = []
    for f, lo, hi in spans:
        if (ws / f).is_file():
            continue
        hits = [d for d in repos if (d / f).is_file()]
        if len(hits) == 1:
            out.append(f"the first look cites {f}:{lo}-{hi} without its repository folder: write "
                       f"{hits[0].name}/{f}:{lo}-{hi}")
    return sorted(set(out))


def seen_of(reg, f):
    """Where a flow was seen, in plain words, when the first look's reading recorded it; else ""."""
    if not f.get("seen_in"):
        return ""
    try:
        import first_look
        return first_look.seen_said(reg, f)
    except (ImportError, OSError, ValueError):
        return ""


def sources_read(reg):
    """The full plan's list of the sources the first look's readers read: what each turned out to be, its date, and
    how many spots in it were not read; "" when the first look's reading recorded none."""
    try:
        import first_look
        got = first_look.reader_files(reg)
    except (ImportError, OSError, ValueError):
        return ""
    seen, lines = set(), []
    for p, d in got:
        what = (d.get("what_it_is") or "").strip()
        if not what or (p["source_id"], what) in seen:
            continue
        seen.add((p["source_id"], what))
        gap = len(d.get("not_read") or [])
        dated = (d.get("dated") or "").strip()
        lines.append(f"- {what}" + (f", dated {dated}" if dated and dated != "none shown" else ", no date shown")
                     + (f"; {gap} spot{'s' if gap != 1 else ''} in it not read" if gap else ""))
    return "\n\n**The sources read at the first look.**\n" + "\n".join(lines) if lines else ""


def flow_line(reg, f):
    seen = seen_of(reg, f)
    return f"*{f['name']}*" + (f" (seen {seen})" if seen else "")


def bullets(items):
    return "\n".join(f"- {i}" for i in items)


def checks_said(reg):
    """What this run does to check its findings against the code, as the person reads it: every run reads in units
    and has every finding that cites code checked by independent readers, at the count the go records."""
    got = load(reg, layout.SETTINGS) or {}
    import go  # before the go, the stage kit's own: it always maps fast
    if got.get("mapping") == "fast" or ("judges" not in got and go.stage_kit_run(reg)):
        return ("I will have one check read each finding a proposed measure, alert or failure mode rests on against "
                "the code, by a reader who wrote none of it; every other finding is shown as not checked.")
    n = got.get("judges", 3)
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
    """What was checked of the map, as lines of text: checked_fields without their labels."""
    return "\n".join(text for _, text in checked_fields(reg))


def report_fields(reg):
    """The kit's own part of the report, as labelled one-line fields: Done (the done check's word) and what was
    checked, one field a line, never a paragraph. `say --report` puts them under the status line."""
    reg = pathlib.Path(reg)
    return "\n".join(f"- **{label}:** {text}" for label, text in [("Done", end_said(reg))] + checked_fields(reg))


def checked_fields(reg):
    """What was checked of the map, in the past tense, for the report, as (label, one line) pairs: exactly what the
    checks established, never more (never "mapped, checked and done" when only a sample was re-read).
    Each line is what a check of the kit verified: the sampled re-read (or, in a split run, every row judged) and the
    reading check against Claude Code's own record of the sessions."""
    import reading_check
    import reread
    import run_status
    out = []
    if checks_stopped(reg):
        out.append(("Checked", "You stopped the checks before they finished, so the map is not checked against the "
                               "code: any finding not read through every round is not checked."))
    elif (reg / layout.UNITS_CSV).is_file() and run_status.is_fast(reg):
        out += [("Checked", x) for x in fast_checked_said(reg)]
    elif (reg / layout.UNITS_CSV).is_file():
        n = (load(reg, layout.SETTINGS) or {}).get("judges", 3)
        out.append(("Checked", f"Each finding was read against the code by {n} independent checks."))
    else:
        held = reread.check(reg).passed
        out.append(("Checked", "A reader who wrote none of the findings re-read a sample of ten of them against the "
                               "code, " + ("and every one of the ten held" if held else
                                           "and not every one of the ten holds yet")
                    + "; the other findings were not checked one by one."))
    reading = reading_check.check(reg)
    if reading.passed and reading.cited:
        by_run = reading.covered - reading.by_reader
        out.append(("Code read", f"every place the map cites · {by_run} opened by the run"
                    + (f" · {reading.by_reader} found by the code reader" if reading.by_reader else "")))
    import kit_findings
    found = kit_findings.line(reg)
    if found:
        out.append(("Kit problems", found))
    return out


def unread(reg):
    """The capability brief's line on files of the code that could not be read, as one more item, or nothing."""
    import first_look
    import map_record
    lines = [x for x in (map_record.unread_line(reg), first_look.not_read_line(reg)) if x]
    reader = first_look.code_reader_line(reg)  # whole sentences of its own: never after "Not read:"
    return "".join(f"\n- Not read: {x}" for x in lines) + (f"\n- {reader}" if reader else "")


def unfounded(reg):
    """The capability brief's lines on every word a source reader copied that the first look's quote check could not
    confirm independently (first_look.unfounded_said): quotes judged not in their source, each left out of what was
    found; rows no one could check, kept unchecked; and rows the session that copied them settled itself because no
    judge answered, each with its verdict. Each is said with the passage nearest to it, so the person can judge the
    source and the reading; nothing when there are none."""
    try:
        import first_look
        got = first_look.unfounded_said(reg)
    except (ImportError, OSError, ValueError):
        return ""
    if not got:
        return ""
    what = {(r.get("source_id") or "").strip(): (r.get("what") or "").strip()
            for r in rows(pathlib.Path(reg) / "sources.csv")}
    settled = {"found": "kept as found", "paraphrase": "kept as a paraphrase",
               "not in source": "left out as not in its source", "unchecked": "kept unchecked"}

    def item(x, verdict=False):
        return ((f"the name “{x['quote']}”" if x["what"] != "quote" else f"“{x['quote']}”")
                + f" in {what.get(x['source']) or x['source']}"
                + (f", {settled.get(x['verdict'], x['verdict'])}" if verdict else "")
                + (f" (nearest there: “{x['nearest']}”)" if x["nearest"] else ""))
    lead = {"not in source": "Quoted by a reader but not in its source, so left out of what was found",
            "unchecked": "Copied by a reader and kept, but not checked in its source, since no one could open it or tell",
            "self-settled": "Settled by the session that copied it, since no independent judge answered, so not "
                            "independently checked"}
    out = ""
    for kind in first_look.NOT_CONFIRMED:
        xs = [x for x in got if x["kind"] == kind]
        if xs:
            out += f"\n- {lead[kind]}: " + "; ".join(item(x, kind == "self-settled") for x in xs) + "."
    return out


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
    """The first-look brief as the person reads it in the chat: the status line, then one question card per decision
    (the first flow, then each search the first look proposes), each standing alone for someone who knows nothing of
    the system or the kit. The rest (every service and why it is read or left out, what was looked at) is the full
    plan, `capability_full`, written to PLAN.md and shown when the person asks."""
    import go
    import question_card as qc
    c, r = o["capability"], o["recommendation"]
    services = o.get("services") or []
    n_in = sum(s.get("recommend") == "in" for s in services)
    kit = go.stage_kit_run(reg)
    parts = []
    lead = ""
    if request:
        lead = (f"Your request asked for every flow, so I'm starting with *{r['flow']}*, and I'll add the others one "
                f"at a time after it. {sentence(r['why'])} You can stop me, or change this, at any time: start with "
                "another flow instead, or change which services are read.")
    else:
        table = (("#", "Flow", "What happens", "Its stages"),
                 [(i, f["name"], cont(qc.fragment(f.get("what", ""))),
                   " · ".join(s["name"] for s in f.get("stages") or []))
                  for i, f in enumerate(o["flows"], 1)])
        reads = (f"the code of {count_word(n_in)} of the system's {count_word(len(services))} services; the full plan "
                 "says which and why")
        fields = [("Terms", None), ("Application", c["name"])]
        if what_it_does(c.get("what")):
            fields.append(("What it does", what_it_does(c.get("what"))))
        if kit:
            plan = "I map it in one quick pass, propose measures for each stage, then stop for your review"
            choices = [("Go ahead", f"I map {r['flow']} first and propose measures for every stage"),
                       ("Another flow", "you name one from the table, or describe one I missed; I map that first"),
                       ("Change how far", "you say which stages stop at the map, or go on to alerts and runbooks")]
            rec, title = 1, f"Shall I start with {r['flow']}?"
        else:
            plan = "I map it, show you its stages, and you say how far each goes"
            choices = [(f"Map {f['name']}", "I map this flow first") for f in o["flows"]]
            choices.append(("Another flow", "you describe one I missed; I add it and map it first"))
            rec = next((i for i, f in enumerate(o["flows"], 1) if f["name"] == r["flow"]), 1)
            title = "Which flow should I map first?"
        parts.append(dict(title=title, fields=fields, table=table,
                          after=[("Plan", plan), ("Reads", reads), ("Not found", "a flow missing here may still exist")],
                          why="I map one flow at a time, and the first sets where the work starts",
                          choices=choices, recommended=(rec, cont(r["why"]))))
    parts += [p for _, p in search_asks(o, asks_flow=not request)]
    # every kit word the first card uses is defined in it: its choices name alerts and runbooks on the stage kit
    # and the words of the work to come (finding, checked finding) are defined in its Terms, never as loose lines after
    # it; how the check runs is said where it runs
    words = (["flow", "stage", "map", "service"] + (["measure", "alert", "runbook"] if kit else [])
             + ["finding", "checked finding"])
    told = qc.terms(reg, words) if parts else ""
    if parts:
        p0 = parts[0]
        p0["fields"] = [("Terms", told)] + [f for f in p0.get("fields") or [] if f[0] != "Terms"]
    cards = qc.cards(parts)
    tail =("The full plan, with each service and why it is read or left out, is ready: ask me for it."
            + unread(reg).replace("\n- ", "\n") + unfounded(reg))
    return "\n\n".join(x for x in (status(reg), lead, cards, tail) if x) + "\n"


def capability_full(reg, o):
    """The first-look brief in full, for PLAN.md: the plan the person oversees, shown when they ask for it."""
    import go
    c, a, r = o["capability"], o["activity"], o["recommendation"]
    if go.stage_kit_run(reg):  # the stage kit: the go's answer is filled in, the first flow with every stage measured
        then = ("Once the flow is mapped, I propose what to measure for each of its stages, then stop for you to "
                "review the measures. Alerts and runbooks come only if you ask for them.")
        ask = (f"**Shall I go ahead?** I recommend *{r['flow']}* first, mapped in one quick pass, with each of its "
               "stages taken on to proposed measures. Say yes, or tell me what to change.")
    else:
        then = ("Once the flow is mapped, I will show you its stages, and you pick how far each one goes: mapped only, "
                "measured, measured with alerts, or measured with alerts and then runbooks.")
        ask = f"**Which flow should I map first?** I recommend *{r['flow']}*."
    flows = []
    for i, f in enumerate(o["flows"], 1):
        stages = "\n".join(f"   - *{s['name']}*: {cont(s['what'])}." for s in f["stages"])
        seen = seen_of(reg, f)
        flows.append(f"{i}. **{f['name']}.** {sentence(f['what'])}{case_said(f)}"
                     + (f" Seen {seen}." if seen else "") + f" Its stages:\n{stages}")
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
- Still open: {'; '.join(cont(search_text(x)) for x in o.get('unresolved') or ['nothing known'])}.{unread(reg)}{unfounded(reg)}{sources_read(reg)}

**The services, and which to include.** A service left out is not read; a call into it is noted as outside this run.

{services}

**Where to start.** Start with *{r['flow']}*: {cont(r['why'])}. What remains of the job after this run: {cont(r['remains'])}.

**What I will do unless you say otherwise.** I will read the services marked include above and leave out the others. {checks_said(reg)} {then}

Nothing is read in depth until you answer.

The questions are put to you in the chat, one card each; nothing is read in depth until you answer them.
"""


def open_record(reg):
    """The flow worked now's record of open items and the person's decisions on them (open_items.of_flow), read by
    every surface; an empty record when the checks cannot read the register."""
    import open_items
    try:
        return open_items.of_flow(pathlib.Path(reg))
    except Exception:  # noqa: BLE001 - a register the checks cannot read: said as such, never as no open items
        return open_items.empty(unreadable=True)


def open_now(reg):
    """(the stages whose own check fails, [each open item once]) from the flow's record of open items."""
    rec = open_record(reg)
    return rec["stages"], rec["items"]


def still_open(reg):
    """The draft's open items in a sentence for the person ("" when every check passes), each counted once."""
    failing, items = open_now(reg)
    if not items:
        return ""
    st = {(r.get("stage") or "").strip(): (r.get("name") or "").strip() for r in rows(pathlib.Path(reg) / "stages.csv")}
    named = and_list([f"*{st.get(s) or s}*" for s in failing])
    n = len(items)
    return (f"The check of {named} still finds {count_word(n)} open item{'' if n == 1 else 's'}: "
            + "; ".join(items) + ".")


def reentry_open_tail(reg, current=None, nxt=""):
    """The resume's close when the draft's own checks still fail: the items, that the run puts them right and tells
    the person, and the person's way past them: they are never held. "" when every check passes."""
    said = still_open(reg)
    if not said:
        return ""
    rec = open_record(reg)
    if rec["left_open"]:  # the person said to go on with them open: listed, never offered again
        return (f"\n**Open items left open at your word.** {said} You said to go on with them still open "
                f"(\"{(rec['left'] or {}).get('words', '')}\"); they stay listed for this flow until each is put "
                "right.\n")
    if current is None:
        st = state(reg)
        current = st[0] if st else None
    # what comes after the fix is the work the run is at (the runbooks, say), not the status line's next
    then = cont(short(current)) if current is not None and current not in HOLDS else nxt
    if not then or then.startswith("putting the open items right"):
        then = "the next flow" if flows_left(reg) else ""
    import question_card as qc
    failing, items = open_now(reg)
    st = {(r.get("stage") or "").strip(): (r.get("name") or "").strip() for r in rows(pathlib.Path(reg) / "stages.csv")}
    leave = (("Next flow", "I go on to the next flow; these stay listed until each is put right") if flows_left(reg)
             else ("Stop", "the map stays as it is, with these still open and listed"))
    n = len(items)
    return "\n" + qc.card(
        title=f"{count_word(n).capitalize()} open item{'' if n == 1 else 's'} still in this draft: shall I put them right?",
        fields=[("Where", and_list([st.get(s) or s for s in failing]) if failing else "")],
        table=(("#", "Open item"), [(i, x) for i, x in enumerate(items, 1)]),
        after=[("Who can fix", "I can; what you said stands, and nothing is reviewed again"),
               ("Cost", "left open, the final check of the map lists them, and the pages say so")],
        why="the final check of the map names them until each is put right",
        choices=[("Fix now", "I put each right and tell you what I changed"
                  + (f", then carry on with {then}" if then else "")), leave],
        recommended=(1, "it is my work, and nothing you decided changes")) + "\n"


def carry_on_card(nxt):
    """The re-entry brief's question when nothing waits on the person: carry on with what is next, or new work."""
    import question_card as qc
    return qc.card(title=f"Shall I carry on with {nxt}?", why="this work was started before and is not finished",
                   choices=[("Carry on", f"I go on with {nxt}, from where the work stands"),
                            ("New work", "I start new work beside this one, which stays as it is")],
                   recommended=(1, "the work stands where it was left"))


def reentry(reg, o):
    c, a = o["capability"], o["activity"]
    scope = scope_now(reg)
    st = state(reg)
    # what the run drafted; the person's picks and review are reported under what was decided, never as the run's work
    done = [cont(made(x, reg)) for x, s in phases(reg) if s == "done" and x not in HOLDS]
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
            elif p.get("from_go"):
                decided += (" Your answer at the start also said how far each stage goes; it was recorded once the "
                            f"stages were mapped, on {p.get('given', 'an earlier day')}, and it decides: "
                            f"{depth_said(reg, scope['depth'], '*')}.")
            else:
                decided += (f" After the flow was mapped, {'a test standing in for you' if p.get('test') else 'you'} "
                            f"picked how far each stage goes, on {p.get('given', 'an earlier day')}, and that pick "
                            f"decides: {depth_said(reg, scope['depth'], '*')}.")
            decided += f" In those words: \"{p['words']}\"" if p.get("words") else ""
        for key, what in (("measures_reviewed", "the measures"), ("alerts_reviewed", "the alerts")):
            r = scope.get(key) or {}
            if r:  # each go, and whether it was given on a draft with open items, is the person's decision
                n = len(r.get("open") or [])
                by = "a test standing in for you" if r.get("test") else "you"
                decided += (f" On {r.get('given', 'an earlier day')}, {by} said go on {what}"
                            + (f", a draft with {count_word(n)} open item{'' if n == 1 else 's'}" if n else "") + ".")
        for f in scope.get("open_fixed") or []:  # a fix after a go: told, and the go carried over
            decided += (f" On {f.get('given', 'an earlier day')}, I put open items right after your go, and told you: "
                        f"{cont(f.get('words', ''))}; your go stood.")
        left = scope.get("open_left") or {}
        if left:
            n = len(left.get("items") or [])
            by = "a test standing in for you" if left.get("test") else "you"
            decided += (f" On {left.get('given', 'an earlier day')}, {by} said to go on with {count_word(n).lower()} "
                        f"open item{'' if n == 1 else 's'} left open, in these words: \"{left.get('words', '')}\".")
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
    if open_case:
        # the next flow is what is next, offered with the recommendation the record holds, never a wait on the person
        rec = next_flow_recommended(reg) or (o.get("recommendation") or {})
        tail = "\n" + next_flow_card(reg, rec.get("flow"), (rec.get("why") or "").strip(), flows_left(reg)) + "\n"
        if open_record(reg)["left_open"]:  # open items left open at the person's word stay listed
            tail += reentry_open_tail(reg)
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
    elif waits == "nothing" and still_open(reg):
        tail = reentry_open_tail(reg, current, nxt)
        if open_record(reg)["left_open"]:  # their word stands: the run carries on to the end of this flow
            tail += "\n" + carry_on_card(nxt) + "\n"
    elif waits == "nothing":
        tail = "\n" + carry_on_card(nxt) + "\n"
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
    run_md.write(p, text)


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
    return f"{status(reg)}\n\n{next_flow_card(reg, flow, why, left, done)}\n"


def next_flow_card(reg, flow, why, left, done=""):
    """The question card for the next flow: one choice per flow still to add, the recommended one first, a flow the
    first look missed, and stop."""
    import question_card as qc
    order = [flow] + [n for n in left if n != flow] if flow in left else list(left)
    choices = [(f"Map {n}", "I map it next and add it to the same map") for n in order]
    choices += [("Another flow", "you describe one I missed; I add it and map it next"),
                ("Stop", "the map stays as it is, with those flows still to add; nothing drafted is lost")]
    return qc.card(
        title=(f"{done} is drafted to the end. Which flow next?" if done else "Which flow should I map next?"),
        fields=[("Done", f"{done}: its map, your picks and its pages stay as they are" if done else "")],
        why="I map one flow at a time; each is added to the same map",
        choices=choices, recommended=(1, cont(why)) if flow in left else (None, "no flow is recommended yet"))
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
    run_md.write(p, text)


def open_items_said(reg, R, flow_id, stage_ids, part):
    """The draft's open items, as the stages' own checks find them for `part` (flow_outputs.stage_open): lines for the
    review, or [] when every check passes. A failing check never blocks the review or hides: it is said here, and the
    go is recorded with these items open."""
    import go
    import open_items
    picked = (go.record_of(reg, flow_id) or {}).get("depth") or go.depth_all(reg) or {}
    chosen = {s for s, d in picked.items() if d != "none"} or None
    failing, items = [], []
    for sid in stage_ids:  # the one computation the record of open items uses (open_items.stage_items)
        got = open_items.stage_items(R, flow_id, sid, chosen, part)
        if got:
            failing.append(sid)
            items += [x for x in got if x not in items]
    go.record_open_shown(reg, part, items)  # the go records exactly these: one computation, one count
    if not failing:
        return []
    st = {s["stage"]: s.get("name") for s in R["stages"]}
    named = and_list([f"*{st.get(s) or s}*" for s in failing])
    n = len(items)
    out = [f"**Open items in this draft.** The check of {named} found {count_word(n)} still open. This is a draft "
           "with open items: if you say go, I record it with them open, and each stage's page lists them:"]
    return out + [f"- {x}" for x in items]


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
    opened = open_items_said(reg, R, flow_id, stage_ids, "alerts")
    table, stage_names = [], []
    out = [status(reg), "", "", "", "**Draft of the alerts:** " + (
        "no runbook, and nothing on how each could fail, is written yet: those come after these alerts"
        if runbooks else "as far as the stages you picked go, kept as a draft"),
        *(["", *opened] if opened else [])]
    for sid in stage_ids:
        M = fo.build(R, flow_id, sid)
        names |= set(fo.given_names(M)) | {fo.states_said(M, fo.state(v.get(k))) for v in M["moves"].values()
                                           for k in ("from_state", "to_state")}
        measure_names |= {cont(plain(M, x["measure"])) for x in M["measures"].values()}
        expect = {e.get("expectation_id"): e for e in R.get("expectations", [])}
        out += ["", f"### {M['stage']['name']}", "", f"**Flow:** {M['flow']['name']}"]
        alerts = fo.stage_alerts(M)
        stage_names.append(M["stage"]["name"])
        import question_card as qc
        table += [(len(table) + 1, m["measure"], cont(qc.fragment(plain(M, lost_of(fo.basis(m))))),
                   fires_when(m), wakes(R, m)) for m in alerts if m["measure"] not in {r[1] for r in table}]
        if not alerts:
            out += ["", "**Alerts proposed:** none for this stage"]
        for m in alerts:
            guards = "; ".join("“" + quoted(re.sub(r"^proposed:\s*", "", expect[e]["expectation"])) + "”"
                               for e in fo.guards(m) if e in expect)
            kind = signal_kind(m.get("layer"))
            out += ["", f"**Alert:** {m['measure']}",
                    "", f"**Watches:** “{cont(plain(M, m.get('question_it_answers')))}”",
                    "", f"**Protects what someone counts on:** {guards or 'no one named'}",
                    "", f"**Kind:** {KIND_WORDS.get(kind, kind)}",
                    "", f"**Produced today:** {'yes' if m.get('exists') == 'yes' else 'no, proposed'}",
                    "", f"**Why I propose it:** {cont(plain(M, fo.basis(m)))}"]
        steps = {s["step"] for s in M["steps"]}
        alerting = {m["handle"] for m in alerts}
        proposed |= {m["handle"] for m in M["alerts"]}
        parts = {p for mv in M["stage_moves"] for p in M["carried"][mv] + M["needs"][mv]}
        own = [x["measure"] for x in M["measures"].values() if x["handle"] not in alerting and
               ((x.get("stage") or "").strip() == sid or (x.get("step") or "").strip() in steps)]
        # the parts' own measures are the application and technology health signals of this stage
        of_parts = [x["measure"] for x in M["measures"].values() if x["handle"] not in alerting and
                    x.get("subject_id") in parts and not any((x.get(c) or "").strip() for c in ("step", "stage", "flow"))]
        out += [""] + not_alerts([(cont(plain(M, x)), "the stage and its steps") for x in dict.fromkeys(own)]
                                 + [(cont(plain(M, x)), "the services and stores it uses")
                                    for x in dict.fromkeys(of_parts)])
        flow_measures = [x for x in M["measures"].values() if (x.get("flow") or "").strip() == flow_id and
                         not (x.get("stage") or "").strip() and not (x.get("step") or "").strip()]
        flow_name, flow_M = M["flow"]["name"], M
    if stage_ids:  # the flow's own measures belong to the flow: listed once, not under every stage
        flow_other = [x["measure"] for x in flow_measures if x["handle"] not in proposed]
        out += ["", f"### The flow as a whole: {cont(flow_name)}", ""]
        out += not_alerts([(cont(plain(flow_M, x)), "the flow") for x in dict.fromkeys(flow_other)])
    if runbooks:  # verification is the build's to report, never the runbook's: said here, owed before hand-over
        out += ["", "**Before hand-over:** each test a runbook holds is tried once on a known example (a test record "
                "or a reproduced failure) by someone who can run it; this work reads the code and runs nothing",
                "", "**Tests still owed that try:** counted by the final check"]
    if (scope_now(reg) or {}).get("mapping") == "fast":  # each alert rests on a measure: its checking is said again
        import selective
        out += ["", selective.said(reg)]
    import question_card as qc
    n = len(table)
    out[2] = qc.card(
        title=f"Which of these {count_word(n).lower()} alert{'' if n == 1 else 's'} should wake someone?" if n else
        "No alert is proposed: is that right?",
        fields=[("Terms", qc.terms(reg, ["alert"] + (["runbook"] if runbooks else [])))],
        table=(("#", "Alert", "What is lost when it fires", "Fires when", "Wakes"), table),
        why=("each alert you keep gets a runbook next" if runbooks else
             "the alerts you keep are as far as these stages go"),
        choices=[("Keep", "I keep them" + (" and write a runbook for each" if runbooks else " as the draft")),
                 ("Change", "you say which to drop, change or add (any measure can become one); I redraft them")],
        recommended=(review_pick(recommend), cont(recommend)))
    if opened:
        out[2] = out[2].replace("\n> **Why:**", f"\n> **Open items:** {count_word(len(opened) - 1)} still open, "
                                               "listed below\n>\n> **Why:**", 1)
    return "\n".join(out) + "\n", names, measure_names


def not_alerts(rows_):
    """The measures considered and not proposed as alerts, as a table: each with what it is for."""
    if not rows_:
        return ["**Considered, not proposed as alerts:** none"]
    return ["| Considered, not proposed as an alert | Of |", "|---|---|"] + [f"| {a} | {b} |" for a, b in rows_]


def lost_of(basis):
    """What is lost when an alert fires, from its reason as the register words it: the clause after "means", else a
    clause that names a loss, else its first clause; of its first sentence only, as fits a table cell."""
    basis = re.split(r"(?<=[.!?])\s+(?=[A-Z])", (basis or "").strip(), maxsplit=1)[0].rstrip(".")
    if " means " in basis:
        return re.split(r";", basis.split(" means ", 1)[1])[0].strip()
    parts = [x.strip() for x in re.split(r";", basis) if x.strip()]
    return next((x for x in parts if re.search(r"(?i)\blos[est]\b|\blost\b|\bloses\b", x)), parts[0] if parts else "")


def review_pick(recommend):
    """The choice a review's recommendation points at: 2 (change) when it opens with a change, else 1 (keep)."""
    return 2 if re.match(r"(?i)\s*(?:change|drop|add|remove|replace|rewrite)\b", recommend or "") else 1


def fires_when(m):
    """When an alert fires, as the register holds it: the form of its measure rising, with no level set yet (the
    register keeps no threshold)."""
    form = cont((m.get("form") or "").strip())
    return f"its {form} rises above a level not set yet" if form else "a level not set yet"


def wakes(R, m):
    """Whom an alert wakes: the responder, else the owner, of the part its measure is taken from, as the register
    proposes it; "not yet known" when it names none."""
    subj = next((s for s in R.get("subjects") or [] if s.get("subject_id") == m.get("subject_id")), {})
    for col in ("responder", "owner"):
        v = (subj.get(col) or "").strip()
        if v and not re.match(r"(?i)(?:proposed:\s*)?that\b", v):
            proposed = v.lower().startswith("proposed:")
            v = re.split(r"[;,]", re.sub(r"(?i)^proposed:\s*", "", v))[0].strip()
            return f"{v} (proposed)" if proposed else v
    return "not yet known"


WATCHED_WORDS = {"yes": "yes", "in the app only": "only inside the application", "no": "no",
                 "only if configured": "only where a setting turns it on", "development only": "only in development",
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
    run_md.write(p, text)


# The heading each kind of health signal has in the review, in plain words, keyed by the names method/layers.csv
# writes it by; the method's own names stay in the method and on the pages that teach it
LAYER_HEADS = {"business health": "Does the work get done", "business impact": "How much work is lost",
               "application": "Is the software working", "technology": "Are the machines up",
               "agentic": "Does the AI agent decide right"}
# a kind of health signal as an alert's Kind field says it
KIND_WORDS = {"business": "the business's own work", "application": "the software", "technology": "the machines"}


def quoted(s):
    """Words someone counts on, as a quote: first letter upper-cased, "i" as "I", no closing stop."""
    s = re.sub(r"\bi\b", "I", (s or "").strip().rstrip("."))
    return s[:1].upper() + s[1:]


def case_noun(R, flow_id):
    """What one case of the flow is, in the register's own word ("One order: ..." gives order); "item of work" when
    the register does not say."""
    f = next((x for x in R.get("flows") or [] if x.get("flow_id") == flow_id), {})
    m = re.match(r"(?i)\s*one (\w+)", f.get("case") or "")
    return m.group(1).lower() if m else "item of work"


def cased(text, noun):
    """The kit's word "case" in a question, said as the flow's own case noun."""
    plural = noun if noun.endswith("work") else noun + "s"
    return re.sub(r"\bcase\b", noun, re.sub(r"\bcases\b", plural, text))


def where_said(what):
    """Where a thing with no measure sits, from check_measures.said_what, in plain words."""
    for lead, words in (("the process step ", "step "), ("the stage ", "stage "), ("the flow ", "the flow ")):
        if what.startswith(lead):
            return words + what[len(lead):]
    return what
MEASURES_DETAIL_FILE = "measures-review-detail.md"  # the review's detail, one level down: the session shows it on request


CODE_NAME = re.compile(r"\b(?:[A-Z][a-z]+[A-Z][A-Za-z]*|[a-z]+[A-Z][A-Za-z]*|[A-Za-z]+_[A-Za-z_]+)\b")


def code_names(text):
    """Advice only, never a refusal: the code's own names (a joined-up word such as PlaceOrder, or an underscored
    one) in what the person reads, outside the status line and web addresses: each is said as what the shopper or
    the business sees, in the register's rows (MEASURES-STEPS, "What the person reads is in plain words"). Where a
    measure is produced ("Produced today: yes, at ...") is the code's own place and keeps its names."""
    said = "\n".join(x for x in (text or "").splitlines()
                     if "**Where things stand:**" not in x and "Produced today: yes, at" not in x)
    said = re.sub(r"https?://\S+", " ", said)
    found = list(dict.fromkeys(CODE_NAME.findall(said)))
    return [f"code names in the review ({', '.join(found[:8])}): say what the shopper or the business sees, in the "
            "register's rows, and render it again"] if found else []


def one_clause(text):
    """A table cell's reason as one clause: its first sentence, up to its first semicolon or colon, so a cell never
    chains "a: b: c"."""
    first = re.split(r"(?<=[.!?])\s+(?=[A-Z])", (text or "").strip(), maxsplit=1)[0]
    return re.split(r"; |: ", first, maxsplit=1)[0].strip().rstrip(".")


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

    def asks(M, x):  # the register's question, as a quote: a bare word list ("errors; duration") keeps no stop
        q = cont(plain(M, x.get("question_it_answers")))
        return f"“{q}”" if q else "not said"

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

    noun = case_noun(R, flow_id)

    def no_measure(key):
        """A table row per thing with no measure: where it is, the question, and why none, the reason's first sentence
        only."""
        lines = []
        for r in (r for r in owed if not r["covered"] and where_owed(r) == key):
            k = (r["element"], r["question"])
            if k in gapped and gapped[k] == "counted by":  # the measure it is folded into is the reason
                into = [by_name[h] for h in dict.fromkeys(re.findall(r"\bM\d+\b", why.get(k, ""))) if by_name.get(h)]
                said = GAP_WORDS["counted by"] + (f": {and_list(into)}" if into else "")
            elif k in gapped:
                reason = one_clause(prose(flow_M, why.get(k, "")))
                said = GAP_WORDS.get(gapped[k], "a reason is recorded") + (f": {cont(reason)}" if reason else "")
            else:
                said = "no measure, and no reason why none"
            lines.append(f"| {where_said(what_of(r))} | “{cased(check_measures.question(r['question']), noun)}” | "
                         f"{said} |")
        return ["| Not measured | Question | Why none |", "|---|---|---|"] + lines if lines else []

    def counted_on(M, scope):
        """A table: who counts on what, and whether anyone has said it yet."""
        out = []
        for e in R["expectations"]:
            if (e.get("flow") or "").strip() != flow_id or (e.get("stage") or "").strip() != scope:
                continue
            proposed = (e.get("expectation") or "").strip().lower().startswith("proposed:")
            bound = (e.get("objective") or "").strip()
            out.append(f"| {cont(plain(M, e.get('party'))) or 'someone not named'} | "
                       f"“{quoted(prose(M, e.get('expectation')))}”" + (f"; limit: {plain(M, bound)}" if bound else "")
                       + " | " + ("no one yet: proposed" if proposed else "yes") + " |")
        return ["| Who | Counts on | Said by anyone |", "|---|---|---|"] + out if out else []

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

    def section(M, title, measures, key, flow=""):
        out = ["", f"### {title}", ""] + ([f"**Flow:** {flow}", ""] if flow else [])
        exp = counted_on(M, "" if key == "flow" else key) if key else []
        if exp:
            out += exp + [""]
        if measures:
            for head, _, group in by_layer(measures):
                out += [f"**{head}:** {len(group)} measure{'' if len(group) == 1 else 's'}", "",
                        "| Measure | What it shows | Produced today | Collected |", "|---|---|---|---|"]
                out += [row(M, x) for x in group] + [""]
            out.pop()
        else:
            out.append("**Measures:** none of its own here")
        wrong = [x for x in measures if (x.get("exists") or "").strip() == "yes" and (x.get("defect") or "").strip()]
        if wrong:
            out += ["", "| Measure | What it gets wrong today |", "|---|---|"]
            out += [f"| {x['measure']} | {one_clause(prose(M, x['defect']))} |" for x in wrong]
        gaps = no_measure(key)
        if gaps:
            out += [""] + gaps
        return out

    produced = [x for xs in placed.values() for x in xs if (x.get("exists") or "").strip() == "yes"]
    total = sum(len(xs) for xs in placed.values())
    opened = open_items_said(reg, R, flow_id, stage_ids, "measures")
    import question_card as qc
    staged = and_list([M_of[s]["stage"]["name"] for s in stage_ids]) if stage_ids else "this flow"
    card = qc.card(
        title=f"Do the measures for {staged} stand?",
        fields=[("Terms", qc.terms(reg, ["measure"] + (["alert"] if alerts else []))),
                ("What", f"{total} measures: {len(produced)} the system records today, {total - len(produced)} "
                         "proposed, below"),
                ("Open items", f"{count_word(len(opened) - 1)} still open, listed below" if opened else ""),
                ("Cost", "a proposed measure needs a developer to add it; keeping it here commits no one yet")],
        why=("the alerts are chosen from these measures next" if alerts else
             "these measures are as far as the stages you picked go"),
        choices=[("Keep", "I keep them" + (" and go on to the alerts" if alerts else " as the draft")),
                 ("Change", "you say what to drop, change or add; I redraft them and show you again")],
        recommended=(review_pick(recommend), cont(recommend)))
    out = [status(reg), "", card, "", f"**Draft of the measures:** {total}: {len(produced)} the system produces "
           f"today, {total - len(produced)} proposed; " + ("alerts are chosen from them next" if alerts else
                                                          "as far as the stages you picked go, kept as a draft"),
           *(["", *opened] if opened else [])]
    # By default the review is one summary table, a row per stage; each measure in full is one level down, shown when
    # the person asks, since every measure in full is too long to read in the chat.
    by_stage = []
    full = []
    for sid in stage_ids:
        M = M_of[sid]
        by_stage.append((M["stage"]["name"], placed[sid]))
        full += section(M, M["stage"]["name"], placed[sid], sid, flow=M["flow"]["name"])
    if placed[""] or no_measure(""):
        by_stage.append(("Shared by several stages", placed[""]))
        full += section(flow_M, "Shared by several of these stages", placed[""], "")
    if flow_M is not None:
        if placed["flow"]:
            by_stage.append(("The flow as a whole", placed["flow"]))
        full += section(flow_M, f"The flow as a whole: {cont(flow_M['flow']['name'])}", placed["flow"], "flow")

    def made(x):
        return (x.get("exists") or "").strip() == "yes"
    summary = [(name, len(xs), sum(made(x) for x in xs), sum(not made(x) for x in xs),
                sum(made(x) and (x.get("watched") or "").strip() in ("no", "unknown") for x in xs),
                sum(made(x) and bool((x.get("defect") or "").strip()) for x in xs)) for name, xs in by_stage]
    out += ["", "### By stage", ""] + qc.table_lines(
        ("Stage", "Measures", "Produced today", "Proposed", "Not collected or not known", "Gets something wrong"),
        summary)
    results = check_measures.inspect(reg, flow_id, stage_ids)
    failed = [r for r in results if not r["passed"]]
    out += ["", f"**Checked for a measure:** {len(owed)} things these stages and the flow hold (stages, steps that "
            f"matter, services, stores): {covered} with a measure, {reasoned} with a reason why none, "
            f"{len(owed) - covered - reasoned} with neither",
            "", f"**Check of how the measures are written:** {len(results)} rules, {len(results) - len(failed)} pass, "
            f"{len(failed)} fail; not whether they are right about the system"]
    for half, heading in check_measures.HALVES:
        mine = [r for r in results if r["half"] == half]
        bad = [r for r in mine if not r["passed"]]
        fails = "; ".join(f"{cont(r['title'])}: fails on {'; '.join(cont(s) for s in r['said'])}" for r in bad)
        out += ["", f"**{heading}:** " + (fails if bad else f"all {len(mine)} rules pass")]
    if (scope_now(reg) or {}).get("mapping") == "fast":  # the map's rows are checked only where a measure rests
        import selective
        out += ["", selective.said(reg)]
    out += ["", "**More, if you want it:** each stage's measures, what each shows and what it gets wrong, where it is "
            "produced, and each thing checked: ask me for it, whole or for one stage"]
    detail = [status(reg), "", "**The measures proposed, stage by stage.**",
              "", "**Each table says:** what it shows, whether the system produces it today, whether anything collects it"]
    detail += full
    detail += ["", "**Each measure in full.**"]
    titles = [(sid, f"{M_of[sid]['stage']['name']}, in the flow {cont(M_of[sid]['flow']['name'])}")
              for sid in stage_ids]
    if flow_M is not None:
        titles += [("", "Shared by several of these stages"), ("flow", f"The flow as a whole: "
                                                                       f"{cont(flow_M['flow']['name'])}")]
    for key, title in titles:
        if placed.get(key):
            M = M_of.get(key, flow_M)
            detail += (["", f"### {title}: each measure in full", ""]
                       + [line for x in placed[key] for line in item(M, x)])
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
    if (scope_now(reg) or {}).get("mapping") == "fast":  # the rows the measures rest on are checked first
        import selective
        held = selective.review_problem(reg)
        if held:
            print(f"REFUSED: {held}. Nothing written.", file=sys.stderr)
            return 2
    run_md = reg / "RUN.md"
    before = run_md.read_bytes() if run_md.is_file() else None
    import question_card
    told_before = question_card.snapshot(run_md.parent)
    mark_the_measures_review(reg)
    text, detail, names, measure_names = measures_review(reg, args[1], args[2:], recommend)
    bad, advice = split_terms(review_terms(text + detail, measure_names | names), reg)
    advice += prose_faults(text + detail, names | measure_names) + code_names(text + detail)
    if still_refused(reg, "measures", bool(bad), "the person's terms"):
        if before is not None:
            run_md.write_bytes(before)
            question_card.restore(run_md.parent, told_before)
        print("REFUSED: ids or file names of this run in the message: " + "; ".join(bad) +
              ". Fix the recommendation or the register text it comes from, and run this again.", file=sys.stderr)
        return 2
    advise(advice)
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
    return kit_terms(unquoted(text))  # words quoted from a source are never judged


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
    run_md.write(p, text)


def count_word(n):
    return ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")[n] if n <= 10 else str(n)


def stage_key(name):
    """A stage name with its wording taken out: lower case, no article, each word cut to its stem ("Taking the
    order" and "Take the order" both read "tak order"), so a renaming alone is not a change of stages."""
    out = []
    for w in re.findall(r"[a-z]+", (name or "").lower()):
        if w in ("the", "a", "an"):
            continue
        w = w[:-3] if w.endswith("ing") and len(w) > 5 else w
        w = w[:-1] if w.endswith("e") and len(w) > 3 else w
        w = w[:-1] if len(w) > 3 and w[-1] == w[-2] else w
        out.append(w)
    return " ".join(out)


def replaced_stages(reg, walked):
    """(the first look's stage names, the walk's) for the flow the person picked when the walk's differ from the first
    look's, else None. The first look's flow is the one named at the go, else the one it recommended."""
    o = load(reg, "orientation.json") or {}
    picked = (scope_now(reg) or {}).get("flow") or (o.get("recommendation") or {}).get("flow")
    flow = next((f for f in o.get("flows") or [] if (f.get("name") or "").strip() == (picked or "").strip()), None)
    first = [(s.get("name") or "").strip() for s in (flow or {}).get("stages") or [] if (s.get("name") or "").strip()]
    walked = [n for n in walked if n]
    if not first or not walked or [stage_key(n) for n in first] == [stage_key(n) for n in walked]:
        return None  # the same stages, at most reworded ("Taking the order", "Take the order"): nothing changed
    return first, walked


STAKE_WORDS = {"customer": "Customers lose out", "financial": "Money is lost", "operational-efficiency": "Rework",
               "legal-risk-compliance": "A compliance breach"}
STAKE_RECOVERY = {"moves on": "these move on once the cause is fixed", "stranded": "these are left stranded",
                  "not created": "these never come into being"}


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


def before_reading(reg, flow_id):
    """Whether the pick of how far each stage goes is asked before any service is read in depth: run control stands
    at its stop for the pick (case.json, sub `pick`) for this flow."""
    try:
        import case
        return case.flow(pathlib.Path(reg), flow_id).get("sub") == "pick"
    except Exception:  # noqa: BLE001  (a register with no case record: the pick comes after mapping, as before)
        return False


PICK_WORDS = {"none": "map only", "measure": "measures", "alerting": "measures and alerts",
               "runbooks": "measures, alerts and runbooks"}


def depth_review(reg, flow_id, recommend):
    """The message for the person's pick of how far each stage goes, after mapping: a question card with each stage,
    what is lost if it fails and how far the run recommends taking it, with the reason per stage; a second card on
    whether the stages match how the business sees the work only when mapping changed them beyond their wording;
    then, below the cards, the mapping inspection and each stage's losses in full."""
    import check_map
    import flow_outputs as fo
    import question_card as qc
    R = fo.load(reg)
    names = set()
    walked = sorted((x for x in R["stages"] if x.get("flow") == flow_id), key=layout.stage_order)
    flow = next((f.get("name") for f in R["flows"] if f.get("flow_id") == flow_id), "") or "The flow"
    early = before_reading(reg, flow_id)
    rec = load(reg, "depth-recommendation.json") or {}
    rows_, detail = [], []
    for i, s in enumerate(walked, 1):
        M = fo.build(R, flow_id, s["stage"])
        names |= set(fo.given_names(M)) | {cont(n) for n in fo.given_names(M)}
        n = sum(1 for x in M["steps"] if (x.get("name") or "").strip())
        items = at_stake_items(R, M)
        losses = list(dict.fromkeys(u for _, units in items for u in units))
        lost = ("; ".join(losses[:2]) + (f"; and {len(losses) - 2} more, below" if len(losses) > 2 else "")
                or "no loss recorded")  # a cell, not a list: the whole list is below the card
        r = rec.get(s["stage"]) or {}
        rows_.append((s["name"], lost, PICK_WORDS.get(r.get("depth"), ""), cont(r.get("why", ""))))
        detail += ["", f"**{i}. {s['name']}** ({count_word(n)} step{'' if n == 1 else 's'}). "
                   + ("At stake if it fails:" if items else "No Business Impact is recorded for its steps.")]
        detail += [stake_lines(items)] if items else []
    told = qc.terms(reg, ["stage", "measure", "alert", "runbook"])
    # a recommendation is offered only when the record holds one, with its reason, for every stage: a table with an
    # empty Recommended cell, or a choice "as the table says" pointing at nothing, is never shown
    advised = bool(rows_) and all(r[2] and r[3] for r in rows_)
    change = ("Change", 'you say a stage and how far, e.g. "Ship the order: measures"; I take each as you say')
    parts = [dict(
        title=f"How far should each stage of {flow} go?",
        fields=[("Terms", told)],
        table=(("Stage", "If it fails", "Recommended", "Why"), rows_) if advised else
        (("Stage", "If it fails"), [r[:2] for r in rows_]),
        after=[("Levels", "map only, then measures, then alerts on top, then runbooks on top"),
               ("Cost", "each level up is more of my work for you to review; a stage can go further later")],
        why="I propose measures, alerts and runbooks only for the stages you take further",
        choices=[("As recommended", "I take each stage as far as the table says"), change,
                 ("All map only", "I stop at the map; nothing is measured yet")] if advised else
        [("Say how far", change[1]), ("All map only", "I stop at the map; nothing is measured yet")],
        recommended=(1, cont(recommend)) if advised else
        (None, "no recommendation per stage is recorded; you say how far each goes"))]
    replaced = replaced_stages(reg, [(s.get("name") or "").strip() for s in walked])
    if replaced:
        import itertools
        first, now = replaced
        names |= set(first) | {cont(n) for n in first}
        parts.append(dict(
            title="Do these stages match how your business sees the work?",
            table=(("Proposed before reading the code", "Found in the code"),
                   list(itertools.zip_longest(first, now, fillvalue="-"))),
            why="the code divides the work differently from the first proposal; the rest of the work uses the stages",
            choices=[("Keep", "I use the stages found in the code"),
                     ("Redraw", "you say how you would divide the work; I redraw the stages before anything else")],
            recommended=(1, "they follow what the code does")))
    cards = qc.cards(parts)
    out =[status(reg), "", cards, "", "**Below, for reference.**", "", check_map.counted(reg, flow_id,
                                                                                         before_reading=early)]
    checked = checks_found(reg)
    out += ["", checked] if checked else []
    out += ["", f"**What is lost if each stage of {flow} fails.**"] + detail
    return "\n".join(out) + "\n", names


def depth_from_go(reg, flow_id):
    """The pick of how far each stage goes, when the person's answer at the go already said it (go.HOW_FAR): every
    stage of the flow taken that far, recorded with the go's words, and the run goes on without stopping. Returns the
    flow's record or a refusal."""
    import argparse
    import go
    s = go.load(reg) or {}
    how_far = s.get(go.HOW_FAR)
    if not how_far:
        return "the go said nothing of how far the stages go: the pick is put to the person"
    mark_the_pick_stop(reg, flow_id)
    refused = go.record_flow_id(reg, flow_id)
    if refused:
        return refused
    s = go.load(reg) or s
    spec = "" if how_far == "none" else ",".join(f"{sid}={how_far}" for sid in go.stages_of(reg, s))
    words = (s.get("words") or "").strip() or "yes"
    a = argparse.Namespace(words=words, given=None, test=bool(s.get("test")), page=False, from_go=True)
    got = go.record_depth(reg, spec, a)
    if isinstance(got, str):
        return got
    go.record_decision(reg, "depth", words, "go", test=bool(s.get("test")),
                       shown=f"(answered at the go: every stage {DEPTH_WORDS.get(how_far, how_far)}) {words}")
    import depth
    depth.write_quietly(reg)
    return got


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
    """_main, then the timing record rewritten for a register mapped fast (timings.refresh_if_fast)."""
    try:
        return _main(argv)
    finally:
        import timings
        timings.refresh_if_fast(argv, "brief.py")


def _main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    _CAP_NOTES.clear()  # a line owed by a capped refusal belongs to this call's message only
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
        import question_card
        told_before = question_card.snapshot(run_md.parent)
        if request is not None:  # the request already said how far each stage goes: recorded, said in a line, no stop
            import go
            scope_file = pathlib.Path(args[0]) / layout.SCOPE
            kept = scope_file.read_bytes() if scope_file.is_file() else None
            got = depth_from_request(pathlib.Path(args[0]), args[1], request.strip(), opts.get("--depth", ""),
                                     opts.get("--given"))
            said = ([], []) if isinstance(got, str) else split_terms(say_terms(got[0].split("\n", 2)[2], args[0]),
                                                                    args[0])
            bad = got if isinstance(got, str) else "; ".join(said[0])
            if not isinstance(got, str) and not still_refused(args[0], "depth", bool(bad), "the person's terms"):
                bad = ""  # its words pass, or are taken after CAP refusals with the line saying so
            if bad:
                if before is not None:
                    run_md.write_bytes(before)
                    question_card.restore(run_md.parent, told_before)
                if kept is not None:
                    scope_file.write_bytes(kept)
                print(f"REFUSED: {bad}. Nothing recorded.", file=sys.stderr)
                return 2
            advise(said[1])
            import depth
            depth.write_quietly(args[0])
            print(with_page(got[0], args[0]))
            return 0
        mark_the_pick_stop(args[0], args[1])
        text, names = depth_review(pathlib.Path(args[0]), args[1], recommend)
        bad, advice = split_terms(review_terms(text, names), args[0])
        if still_refused(args[0], "depth", bool(bad), "the person's terms"):
            if before is not None:
                run_md.write_bytes(before)
                question_card.restore(run_md.parent, told_before)
            print("REFUSED: ids or file names of this run in the message: " + "; ".join(bad) +
                  ". Fix the recommendation or the register text it comes from, and run this again.", file=sys.stderr)
            return 2
        advise(advice + prose_faults(text, names))
        # kept, so a run picked up again at the pick can show it again
        (pathlib.Path(args[0]) / PICK_FILE).write_text(text, encoding="utf-8", newline="\n")
        import guard  # go.py --depth records a pick only for a flow whose pick was put to the person
        guard.mark_pick_shown(args[0], args[1])
        # the change of stages, asked in its own card, is never told again by the next message
        mark_stages_told(args[0], stages_change(args[0]) if "Do these stages match" in text else "")
        import depth  # the page draws this stop's open choice from depth.json
        import go
        refused = go.record_flow_id(pathlib.Path(args[0]), args[1])  # found by id, never a name the walk may change
        if refused:
            print(f"REFUSED: {refused}. Name the flow worked now by its own id and run this again.", file=sys.stderr)
            return 1
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
                  "to map; " + ("none is left" if not left else "this flow is not finished" + (
                      ": its stages' own checks still find open items. Either the run puts them right and tells the "
                      "person (go.py --open-fixed --words), or the person says to go on with them open (go.py "
                      "--open-left --words, their answer); then the done check, then the next flow"
                      if open_now(reg)[1] and not open_record(reg)["left_open"] else
                      ": run the done check (run_status.py), then offer the next flow" if open_now(reg)[1] else ""))
                  + ".", file=sys.stderr)
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
        bad, advice = split_terms(review_terms(text, known), reg)
        if still_refused(reg, "next", bool(bad), "the person's terms"):
            print("REFUSED: ids or file names of this run in the message: " + "; ".join(bad) +
                  ". Fix the recommendation, and run this again.", file=sys.stderr)
            return 2
        advise(advice + prose_faults(text, known))
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
        import question_card
        told_before = question_card.snapshot(run_md.parent)
        mark_the_review(args[0])
        text, names, measure_names = alerts_review(pathlib.Path(args[0]), args[1], args[2:], recommend)
        bad, advice = split_terms(review_terms(text, measure_names), args[0])
        if still_refused(args[0], "alerts", bool(bad), "the person's terms"):
            if before is not None:
                run_md.write_bytes(before)
                question_card.restore(run_md.parent, told_before)
            print("REFUSED: ids or file names of this run in the message: " + "; ".join(bad) +
                  ". Fix the recommendation or the register text it comes from, and run this again.", file=sys.stderr)
            return 2
        advise(advice + prose_faults(text, names | measure_names))
        # kept, so a run picked up again at the review can show it again
        (pathlib.Path(args[0]) / REVIEW_FILE).write_text(text, encoding="utf-8", newline="\n")
        import go  # what the person is shown is what their go covers: go.py --alerts-reviewed checks against this
        go.record_alerts_shown(pathlib.Path(args[0]))
        print(with_page(text, args[0]))
        return 0
    if argv[:1] == ["say"]:
        after = "--after" in argv
        # --kit: a message the kit itself built (next.py's stops), sent once say has refused it and the refusal is
        # written down as a kit finding: every refusal of its text is advice, never a stop of the run
        report = "--report" in argv
        kit = "--kit" in argv
        args = [a for a in argv[1:] if a not in ("--after", "--report", "--kit")]
        if len(args) != 2 or not pathlib.Path(args[0]).is_dir():
            print(__doc__, file=sys.stderr)
            return 2
        text = pathlib.Path(args[1]).read_text(encoding="utf-8-sig").strip()
        hits, advice = split_terms(say_terms(text, args[0]), args[0])
        if hits and not kit and still_refused(args[0], "say-words", True, "the person's terms"):
            print(WORDS_REFUSED + " (ids or file names of this run): " + "; ".join(hits)
                  + ". Say each in the person's terms (the flow, stage, step or service by its name; what was done or "
                  "is next in plain words), and run this again. Nothing sent.", file=sys.stderr)
            return 1
        if not hits and not kit:
            still_refused(args[0], "say-words", False)
        import question_card  # every question is a card: its why, its numbered choices, its recommendation
        broken = question_card.faults(text)
        if broken and not kit and still_refused(args[0], "say-form", True, "the question card's form"):
            print("REFUSED: a question in the message is not in the question form: " + "; ".join(broken) + ". "
                  "Render it as question_card.py does (SKILL.md, \"Every question is a card\"), and run this again. "
                  "Nothing sent.", file=sys.stderr)
            return 1
        if not broken and not kit:
            still_refused(args[0], "say-form", False)
        advise(advice + hits + broken)  # what was refused before, now taken (--kit, or after CAP refusals)
        # the words inside the form (long fields or cells, a question mark outside a card) read the business's own
        # words, so they are advice only
        advise(question_card.form_advice(text) + question_card.loose_questions(text)
               + ([] if kit else question_card.paragraphs(text)),
               lead="the question form would read better with:")
        if finish_claimed(text) and not run_finished(args[0]):
            print("REFUSED: the message says the run is finished, and the done check has not said DONE on the map as "
                  f"it is. Send what `brief.py end {args[0]}` prints instead. Nothing sent.", file=sys.stderr)
            return 1
        reconcile_phases(args[0])
        if after:  # a line added to a message a script printed, which has its status line and the page's address
            print("\n\n".join([text] + cap_notes()))
            return 0
        print(status(pathlib.Path(args[0])))
        print()
        if report:  # the report: the kit's Done and Checked fields first, then the session's own fields and tables
            print(report_fields(pathlib.Path(args[0])))
            print()
        changed = stages_change_untold(args[0])  # the next message after mapping changed the agreed stages
        if changed:
            print(changed)
            print()
            mark_stages_told(args[0], changed)
        print(with_page(text, args[0]))
        return 0
    if argv[:1] == ["end"]:
        if len(argv) != 2 or not pathlib.Path(argv[1]).is_dir():
            print(__doc__, file=sys.stderr)
            return 2
        print(with_page(end_said(pathlib.Path(argv[1])), argv[1]))
        return 0
    if argv[:1] == ["checked"]:
        if len(argv) != 2 or not pathlib.Path(argv[1]).is_dir():
            print(__doc__, file=sys.stderr)
            return 2
        print(with_kit(checked_said(pathlib.Path(argv[1]))))
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
        print("REFUSED: " + "; ".join(bad) + (". Put right what each names (the first look's own files, as its "
                                              "line says) and run this again."
                                              if all(b.startswith("first look:") for b in bad) else
                                              ". Fix orientation.json and run this again."), file=sys.stderr)
        return 2
    run_md = reg / "RUN.md"
    before = run_md.read_bytes() if run_md.is_file() else None
    import question_card
    told_before = question_card.snapshot(run_md.parent)
    if what == "capability":
        mark_the_stop(reg)
    text = capability(reg, o) if what == "capability" else reentry(reg, o)
    full = capability_full(reg, o) if what == "capability" else ""
    # a message the kit wrote at a stop and the re-entry brief shows again was checked when written, against the
    # register's names: it is read against the same names here, and a fault in it names that message's file
    quoted = next(((f, q) for f in (PICK_FILE, MEASURES_REVIEW_FILE, REVIEW_FILE) if what == "reentry"
                   for q in [shown_again(reg, f)] if q and q in text), None)
    if quoted:
        advise([f"in the message shown again from {quoted[0]}, {x}" for x in
                prose_faults(quoted[1], set(register_names(reg)))])
        text_checked = text.replace(quoted[1], "")
    else:
        text_checked = text
    why = ((o.get("recommendation") or {}).get("why") or "") if what == "capability" else ""
    advise(fault_fields(o, prose_faults(text_checked + full, [f.get("name", "") for f in o.get("flows") or []]))
           + split_terms(orientation_terms(reg, o), reg)[1]
           + [f"recommendation.why: {f}" for f in (reason_faults(why, reg) if why.strip() else [])
              if f not in reason_refused(why, reg)])
    if what == "capability" and request:  # the recommended flow, taken as their go from the request
        got = go_from_request(reg, o["recommendation"]["flow"], request)
        if got:
            if before is not None:
                run_md.write_bytes(before)
                question_card.restore(run_md.parent, told_before)
            print(f"REFUSED: {got}. Nothing written.", file=sys.stderr)
            return 2
        question_card.restore(run_md.parent, told_before)  # the brief rendered again defines its terms again
        text = capability(reg, o, request)
        # the session's own words in it (orientation.json) were checked above; the rest is the kit's text and the
        # sources' verbatim quotes, so a hit here is advice, never a refusal after the go is recorded
        advise([h for pair in split_terms(say_terms(text.split("\n", 2)[2], reg), reg) for h in pair])
    if what == "capability":
        (reg / "PLAN.md").write_text(full, encoding="utf-8", newline="\n")
        (reg / FLOWS_FILE).write_text(with_page(with_kit(text), reg), encoding="utf-8", newline="\n")
        record_first_look(reg)
        import start  # the first look has reached its brief: its mark in the work folder ends here
        if reg.resolve().parent.name == "bfo-work":
            start.end_first_look(reg.resolve().parent)
        import depth  # the page draws this stop's open choice from depth.json
        depth.write_quietly(reg)
    print(with_page(with_kit(text), reg))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
