"""The say-back: before anything is read in depth, the run says back what it understood, as a review step on the run
page (each line correctable, one Start), and waits for the person. On a case picked up (a register), Run status shows
nothing waiting on the person, so the lines and the ask (numbered: carry on, or change a line) go in the chat instead.
What the person meant is the session's reading, never a match against a list of words: a typed answer is recorded
with that reading (--as) beside their words, word for word.

Usage: python say_back.py draft <folder> --lines <json file> [--register <register>]
           write the lines and print the chat's one line (MESSAGE) and the wait (WAIT). <folder> is the work folder
           (bfo-work) on a fresh start, or the register picked up on a resume. The json holds the session's lines:
           application, code, wants, answered (fresh); application, proposal, and wants if their words say it
           (resume). The earlier work is drawn here, from what the workspace and the case record hold.
       python say_back.py answer <folder> (--answers <answers file> |
                                           --words "<their words, word for word>" --as start|correct|search-yes|search-no)
                                          [--test]
           record the person's Start or correction, with the lines they were shown. --as is the session's reading of
           what they meant: a go in any wording, or the number of the go, is start; a line to change is correct; to
           the search, yes or no. When the session cannot tell, it asks them and records nothing.
       python say_back.py earlier <workspace root> [--folder <register>]
           print the earlier-work line

One writer of say-back.json: this script. Before a register exists, the work folder named stands for this run's own
folder in it (start.run_dir), so runs on other systems in the same window keep their own say-back and answers.
Answers go to say-back-decisions.jsonl in that folder (the register's
decisions.jsonl on a resume), through case.py; start_register.py copies them into the register it starts.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import case  # noqa: E402

FILE = "say-back.json"
DECISIONS = "say-back-decisions.jsonl"
STOP = "say-back"
LABELS = (("application", "Application"), ("code", "Code found in this window"), ("wants", "What you want"),
          ("earlier", "Earlier work"), ("answered", "What your request already settles"),
          ("proposal", "What this session will do"))
NEEDS = {"fresh": ("application", "code", "wants", "answered"), "resume": ("application", "proposal")}
MAX_WORDS = 30
MESSAGE = "What I understood is on the page, {url}: correct any line there, or press Start."  # one line: the address cannot be dropped
NO_PAGE = "The page could not be opened. Here is what I understood:"
# A case picked up: Run status shows nothing waiting on the person, so the lines and the ask are in the chat.
RESUME = "Here is what I understood:"
# The ask under the lines in the chat: the choices numbered, and any wording taken for what it means.
ASK = ("**Waiting on you: is this right?**\n"
       "1. That's right: {go}\n"
       "2. Change a line: tell me which, and what it should be\n\n"
       "Reply with a number, or in your own words.")
READINGS = ("start", "correct", "search-yes", "search-no")
# Each flow's case state as the earlier-work line counts it, in this order; a flow with no state is not started.
STATE_WORDS = (("mapped", "mapped and checked"), (case.ENDED, "not checked: you stopped the checks"),
               ("mapping", "under way"), (None, "not started"))
MAX_LISTED = 2  # more earlier maps than this: a count, and where they are listed


def is_register(folder):
    return (pathlib.Path(folder) / "RUN.md").is_file()


def is_run_dir(folder):
    import start
    return start.is_run_dir(folder)


def own_folder(folder, writing=False):
    """The folder this run's say-back lives in: a register as given; for the work folder, this run's own folder in
    it; a work folder an earlier release wrote, whose window-wide say-back still waits, while this run has none."""
    import start
    folder = pathlib.Path(folder).resolve()
    if is_register(folder) or is_run_dir(folder) or folder.name != start.run_lock.WORK:
        return folder
    own = start.run_dir(folder)
    if not writing and not (own / FILE).is_file() and (folder / FILE).is_file():
        return folder
    return own


def root_of(folder):
    """The workspace root: the work folder's parent, or the register's (or this run's folder's) work folder's
    parent."""
    folder = pathlib.Path(folder).resolve()
    return folder.parent.parent if is_register(folder) or is_run_dir(folder) else folder.parent


def placed(named, folder):
    """(the register folder `named` means, None) or (None, why it is refused). A relative path is the workspace's,
    never the folder the script was started in (the skill says to run the kit from its own folder); a folder inside
    a skill folder (one holding SKILL.md) is refused: the kit's folder is never a register."""
    p = pathlib.Path(named)
    if not p.is_absolute():
        p = root_of(folder) / p
    p = p.resolve()
    for d in [p, *p.parents]:
        if (d / "SKILL.md").is_file():
            return None, (f"{p} is inside the skill folder {d}: a register is never written into a skill. Name it "
                          "under the workspace's bfo-work/ folder (bfo-work/<the system's name>). Nothing written.")
    return p, None


def _flow_names(reg):
    import brief
    return {(r.get("flow_id") or "").strip(): (r.get("name") or "").strip() for r in brief.rows(reg / "flows.csv")}


def _found(reg):
    """The names of the flows the first look found, from its orientation."""
    try:
        o = json.loads((reg / "orientation.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [(f.get("name") or "").strip() for f in o.get("flows") or [] if (f.get("name") or "").strip()]


def _count(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def register_said(reg):
    """One register as the earlier-work line tells it, short by construction: the application once, its number of
    flows, and how many are in each state, zero counts left out."""
    import start
    reg = pathlib.Path(reg)
    flows = case.load(reg)["flows"] if (reg / case.CASE).is_file() else {}
    if not flows:
        return f"a map of {start.what_it_is(reg)}, started earlier"
    names = _flow_names(reg)
    ids = set(names) | set(flows)
    # a flow the first look found that the map holds no row for yet is a flow all the same: not started
    have = {n.lower() for n in names.values()}
    for f in _found(reg):
        if f.lower() not in have:
            have.add(f.lower())
            ids.add(f"found: {f.lower()}")
    known = {s for s, _ in STATE_WORDS if s}
    by = {s: sum(1 for i in ids if ((flows.get(i) or {}).get("state") if (flows.get(i) or {}).get("state") in known
                                    else None) == s) for s, _ in STATE_WORDS}
    counts = ", ".join(f"{by[s]} {w}" for s, w in STATE_WORDS if by[s])
    return f"a map of {start.what_it_is(reg)} with {_count(len(ids), 'flow')}: {counts}"


def earlier_line(root, reg=None):
    """The earlier work, drawn by code: the register picked up, or every run of this kit and every earlier map in the
    workspace, as a count once there are more than can be told in a line."""
    import start
    if reg is not None:
        return register_said(reg)
    runs, others = start.registers(root)
    if len(runs) + len(others) > MAX_LISTED:
        return f"{len(runs) + len(others)} earlier maps, listed on the work page"
    parts = [register_said(r) for r in runs] + ["a map made another way"] * len(others)
    return "; ".join(parts) if parts else "None found in this window"


def faults(key, value, folder):
    import brief
    v = (value or "").strip()
    if not v:
        return [f"{key}: empty"]
    out = []
    hits = brief.say_terms(v, folder)
    if hits:
        out.append(f"{key}: words the person does not know ({', '.join(hits)})")
    if len(v.split()) > MAX_WORDS:
        out.append(f"{key}: {len(v.split())} words, keep it to {MAX_WORDS}")
    if key == "answered" and "?" in v:
        out.append(f"{key}: a question; say as a statement what their request settles, or 'Nothing yet: after the "
                   "first look I ask which flow to start with'")
    return out


def address(folder):
    """The run page's address: the work folder's status page, or the register's own."""
    import listener
    folder = pathlib.Path(folder).resolve()
    if is_register(folder) or is_run_dir(folder):
        url = listener.serving(listener.site_of(folder) if is_register(folder) else folder.parent)
        return url + folder.name + "/operator.html" if url else ""
    url = listener.serving(folder)
    return url + "operator.html" if url else ""


def wait(folder):
    import wait_on_page
    folder = pathlib.Path(folder).resolve()
    kit = wait_on_page.PAGE_ASK
    return wait_on_page.how_to_wait({"watch": f'python -u "{kit}" watch "{folder}" 2>&1',
                                     "poll": f'python -u "{kit}" poll "{folder}" {wait_on_page.WATCH_MS // 1000}'})


def load(folder):
    try:
        return json.loads((own_folder(folder) / FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def search_question(application, place):
    """The one question asked in place of Start when the code is not open: the application by its name alone."""
    name = application.split(",", 1)[0].strip() or "the system"
    return f"May I look for {name}'s code in {place}?"


def draft(folder, given, register=None):
    folder = pathlib.Path(folder).resolve()
    kind = "resume" if is_register(folder) else "fresh"
    missing = [k for k in NEEDS[kind] if not (given.get(k) or "").strip()]
    lines = []
    for key, label in LABELS:
        value = earlier_line(root_of(folder), folder if kind == "resume" else None) if key == "earlier" \
            else (given.get(key) or "").strip()
        if value:
            lines.append({"key": key, "label": label, "value": value})
    bad = [f for x in lines for f in faults(x["key"], x["value"], folder)]
    place = (given.get("search") or "").strip()
    if place:
        bad += faults("search", place, folder)
    if missing or bad:
        return None, "; ".join([f"missing: {', '.join(missing)}"] * bool(missing) + bad)
    shown = "\n".join(f"{x['label']}: {x['value']}" for x in lines)
    search = None
    if place:  # the code is not open here: one question, apart from Start, whether to look for it there
        search = {"place": place, "question": search_question(given.get("application") or "", place)}
        shown += f"\nAsked: {search['question']}"
    sb = {"kind": kind, "lines": lines, "shown": shown, "fingerprint": case.fingerprint(shown), "state": "waiting",
          "drafted": case.now(), "register": str(register) if register else None, "search": search}
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / FILE
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(sb, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
    return sb, ""


LEAD_TASK = """# The first look of a business flow observability run

You are the first-look helper. The person has pressed Start on the say-back below. Write nothing for the person.

- **The person's request, word for word:** {request}
- **The say-back's lines, as they started them:**
{lines}
- **The start step's lines (it has run; never run it again or decide by your own reading):**
{start}
- **The register folder (`<your-folder>`):** {register}
- **The skill folder (`<skill>`):** {skill}
- **The mapping skill's folder (`<mapping>`):** {mapping}

Follow `<mapping>/SKILL.md`, section "The run", from the start step's decision through the stop for the person's word
in phase 0, using `<mapping>/MAPPING-STEPS.md` "Before you start". On finish-first-look, finish the first look in the
folder it names; on fresh, start the register folder above with `start_register.py` and do the first look there.
Your own turns are the first look's cost, so keep them few: scripts do the bookkeeping. Write `sources.csv` once (every
source the person gave, each with its `location`; code rows with their repository folder), then run
`python <skill>/first_look.py prepare <your-folder>`: it runs the survey, the code reader, the fetch and the reader
prompts in one command. When it prints LAUNCH, start every `bfo-source-reader` line it prints in one message, each
line as its whole prompt, in the foreground; when it says single, read each owed part yourself with the Read tool only
and write its file in the form. Then run `first_look.py check`, `names` and `first_look.py merge` together; `merge` writes
`first-look/leads-merged.json` (every lead grouped by name, with the sources it was seen in) and places each name no
code holds as unresolved. Write `orientation.json` from the merged leads and the survey in one write (each flow's
`seen_in` from the merge; read code only where the merged leads leave a flow's stages unclear), then run
`brief.py capability`, with `--from-request` when the request asked for every flow, and your final reply is exactly
the text that script printed, and nothing else; with `--from-request`, end there too: start no wait and do not begin
phase 1, which the session that started you does. If the run is blocked, your final reply is what `brief.py say` printed
for one plain sentence saying why and what would unblock it, in the person's terms (with no code to read, or only
code that is not the named system's: that the system's code is needed, and that they can point at it or agree to a
search for it).
"""


def start_lines(folder):
    """The start step's DECISION, FOLDER and EARLIER lines, as start.py kept them in this run's folder, or None."""
    import start
    try:
        return json.loads((pathlib.Path(folder) / start.START_LINES).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def taken(folder):
    """A folder that already holds a register (a CSV file, or RUN.md)."""
    folder = pathlib.Path(folder)
    return folder.is_dir() and ((folder / "RUN.md").is_file() or any(folder.glob("*.csv")))


def lead_prompt(run_folder, sb, register):
    """Write the first-look helper's prompt in the register's prompts/ through write_prompt; return its pointer line."""
    import first_look
    import judges
    import start
    lines = start_lines(run_folder) or {}
    try:
        request = json.loads((pathlib.Path(run_folder) / start.STARTED).read_text(encoding="utf-8")).get("request")
    except (OSError, ValueError):
        request = None
    request = request or start.request_of(register)
    said = "\n".join(f"  - {x}" for x in (sb.get("shown") or "").splitlines()) or "  - (none)"
    start_said = "\n".join([f"  - DECISION: {lines.get('decision', '')}"]
                           + [f"  - FOLDER: {f}" for f in lines.get("folders") or []]
                           + [f"  - EARLIER: {e}" for e in lines.get("earlier") or []])
    mapping = HERE if (HERE / "MAPPING-STEPS.md").is_file() else HERE.parent / "bfo-mapping"
    text = LEAD_TASK.format(request=request or "(not kept)", lines=said, start=start_said,
                            register=pathlib.Path(register).resolve().as_posix(), skill=HERE.as_posix(),
                            mapping=mapping.as_posix())
    return judges.write_prompt(pathlib.Path(register).resolve() / "prompts" / first_look.LEAD_PROMPT, text)


def answer(folder, answers=None, words=None, test=False, reading=None, register=None):
    """(what to print, exit code). `register`: on a fresh Start, the folder the first look's register goes in."""
    folder = pathlib.Path(folder).resolve()
    sb = load(folder)
    if not sb or sb.get("state") != "waiting":
        return "REFUSED: nothing is waiting on the say-back here. Nothing written.", 2
    corrections = {}
    if answers is not None:
        try:
            d = json.loads(pathlib.Path(answers).read_text(encoding="utf-8")).get("say_back")
        except (OSError, ValueError, AttributeError):
            d = None
        if not isinstance(d, dict):
            return "REFUSED: that file is not an answer to the say-back. Nothing written.", 2
        if d.get("shown") and d["shown"] != sb["fingerprint"]:
            return ("REFUSED: the person answered lines that have since been redrafted; the page shows the new ones. "
                    "Nothing written: wait for their answer to what the page shows now."), 2
        text = d.get("correction")
        text = text.strip() if isinstance(text, str) else ""
        asked = d.get("action")
        if asked in ("start", "search-yes", "search-no") and text:
            return ("REFUSED: a button came with a correction; neither Start nor an answer to the search sends one. "
                    "Nothing written: the page shows the lines again."), 2
        if asked == "start" and sb.get("search"):
            return ("REFUSED: Start came while the search is still asked; Start is not shown until it is answered. "
                    "Nothing written."), 2
        if asked in ("search-yes", "search-no") and not sb.get("search"):
            return "REFUSED: an answer to a search that was not asked. Nothing written.", 2
        action = {"start": "start", "search-yes": "search-yes", "search-no": "search-no"}.get(asked) or (
            "correct" if text else None)
        if action is None:
            return "REFUSED: a correction with no words in it. Nothing written.", 2
        said = {"start": "pressed Start on the page", "search-yes": "pressed Yes on the page",
                "search-no": "pressed No on the page"}.get(action, text)
        source = "page"
    else:
        said = (words or "").strip()
        if not said:
            return "REFUSED: no words given. Nothing written.", 2
        if reading not in READINGS:
            return ("REFUSED: say how you read their words, with --as: start (a go, in any wording, or the number of "
                    "the go), correct (a line to change)"
                    + (", or search-yes / search-no (their answer to the search)" if sb.get("search") else "")
                    + ". If you cannot tell what they meant, ask them in one line, through say, and record nothing. "
                      "Nothing written."), 2
        searching = bool(sb.get("search"))
        if searching and reading == "start":
            return ("REFUSED: the search is still asked, so a go answers it: record it as search-yes, or as "
                    "search-no if they declined. Nothing written."), 2
        if not searching and reading in ("search-yes", "search-no"):
            return "REFUSED: an answer to a search that was not asked. Nothing written.", 2
        action = reading
        source = "chat"
    if action in ("search-yes", "search-no"):
        entry = case.decide(folder, STOP, sb["shown"], said, source, test, into=DECISIONS if sb["kind"] == "fresh"
                            else case.DECISIONS, kind="search-consent", agreed=action == "search-yes",
                            place=sb["search"]["place"])
        if sb.get("register") and sb["kind"] == "fresh" and is_register(sb["register"]):
            case.import_decisions(sb["register"], [entry])
        sb["state"] = "search agreed" if action == "search-yes" else "search declined"
        sb["answered"] = entry["at"]
        (folder / FILE).write_text(json.dumps(sb, indent=2, ensure_ascii=False), encoding="utf-8")
        if action == "search-yes":
            return (f"SEARCH AGREED: recorded. Search {sb['search']['place']} for the code, with their own access and "
                    "read-only; add each repository found to the workspace as a further folder; then redraft the "
                    "lines with the code line saying what was found, with no search, and run say_back.py draft "
                    "again, so the page shows them with Start. Read nothing in depth before Start."), 0
        return ("SEARCH DECLINED: recorded; search nothing. Ask them, through say, to point at the code; when they "
                "do, redraft the lines with it and run say_back.py draft again."), 0
    lead_at = None
    if action == "start":  # where the first-look helper's prompt goes, checked before anything is recorded
        lines = start_lines(folder) or {}
        if lines.get("decision") == "finish-first-look":
            lead_at, why = placed((lines.get("folders") or [None])[0] or register or "", folder)
            if why:
                return f"REFUSED: {why}", 2
        elif sb["kind"] == "fresh":
            named = register or sb.get("register")
            if not named:
                return ("REFUSED: name the register folder for this first look with --register "
                        "bfo-work/<the system's name>. Nothing written."), 2
            lead_at, why = placed(named, folder)
            if why:
                return f"REFUSED: {why}", 2
            if taken(lead_at):
                return (f"REFUSED: {lead_at} already holds a register; an earlier register is never written into. "
                        "Name a new folder by the -<date> rule (bfo-work/<the system's name>-<date>/) and run this "
                        "again with --register. Nothing written."), 2
    into = case.DECISIONS if sb["kind"] == "resume" else DECISIONS
    entry = case.decide(folder, STOP, sb["shown"], said, source, test, into=into, kind=action,
                        corrections=corrections)
    if sb.get("register") and sb["kind"] == "fresh" and is_register(sb["register"]):
        case.import_decisions(sb["register"], [entry])
    sb["state"] = "started" if action == "start" else "corrected"
    sb["answered"] = entry["at"]
    (folder / FILE).write_text(json.dumps(sb, indent=2, ensure_ascii=False), encoding="utf-8")
    if action == "start":
        if lead_at is not None:
            pointer = lead_prompt(folder, sb, lead_at)
            return ("STARTED: recorded, with the lines shown. Now start the first-look helper (a general-purpose "
                    "subagent) with the line below as its whole prompt, and nothing else.\n" + pointer), 0
        then = ("carry on with what the last line proposed" if sb["kind"] == "resume"
                else "start the first-look helper now, as the skill says")
        return f"STARTED: recorded, with the lines shown. Now {then}.", 0
    if sb["kind"] == "resume":
        return ("CORRECTED: recorded. Redraft the lines with this and run say_back.py draft again, and send what it "
                f"prints; read nothing before they answer. Their correction: {said}"), 0
    return ("CORRECTED: recorded. Redraft the lines with this and run say_back.py draft again (the page shows them "
            f"and the run waits again); read nothing before Start. Their correction: {said}"), 0


def option(args, name):
    if name in args:
        i = args.index(name)
        return (args[i + 1] if i + 1 < len(args) else ""), args[:i] + args[i + 2:]
    return None, args


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = list(argv)
    if len(args) < 2 or args[0] not in ("draft", "answer", "earlier"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, folder, args = args[0], pathlib.Path(args[1]), args[2:]
    if cmd != "earlier":
        folder = own_folder(folder, writing=cmd == "draft")
    if cmd != "earlier" and is_register(folder):  # a case picked up: only the run holding it writes its register
        import run_lock
        run_lock.guard(folder)
    if cmd == "earlier":
        reg, _ = option(args, "--folder")
        print(earlier_line(folder, pathlib.Path(reg) if reg else None))
        return 0
    if cmd == "draft":
        lines, args = option(args, "--lines")
        register, args = option(args, "--register")
        try:
            given = json.loads(pathlib.Path(lines).read_text(encoding="utf-8")) if lines else None
        except (OSError, ValueError) as e:
            given = None
            print(f"REFUSED: the lines file cannot be read ({e}). Nothing written.", file=sys.stderr)
            return 2
        if not isinstance(given, dict):
            print("REFUSED: --lines <json file> with the lines as keys. Nothing written.", file=sys.stderr)
            return 2
        sb, why = draft(folder, given, register)
        if sb is None:
            print(f"REFUSED: {why}. Say each line in the person's words, short, and run this again. Nothing written.",
                  file=sys.stderr)
            return 2
        listed = "\n".join(f"- {x['label']}: {x['value']}" for x in sb["lines"])
        print(f"DRAFTED: {folder / FILE}")
        if sb["kind"] == "resume":  # no page asks it: the answer comes in the chat
            print("SEND: the text after MESSAGE is your whole reply this turn, copied exactly; then end your turn. "
                  "Their answer comes in the chat. Start no helper and read no code until they answer.")
            print("MESSAGE:\n" + RESUME + "\n\n" + listed + "\n\n" + ASK.format(go="carry on"))
            return 0
        url = address(folder)
        print(f"WAIT: Start the wait on the page before you end your turn. {wait(folder)}")
        print("SEND: the text after MESSAGE is your whole reply this turn, copied exactly. Start no helper and read "
              "no code until the person presses Start or says start.")
        body = MESSAGE.format(url=url) if url else NO_PAGE + "\n\n" + listed + "\n\n" + ASK.format(go="start")
        print("MESSAGE:\n" + body)
        return 0
    answers, args = option(args, "--answers")
    register, args = option(args, "--register")
    words, args = option(args, "--words")
    reading, args = option(args, "--as")
    test = "--test" in args
    if (answers is None) == (words is None):
        print("REFUSED: give --answers <file> or --words \"<their words>\" --as <your reading>. Nothing written.",
              file=sys.stderr)
        return 2
    said, code = answer(folder, answers, words, test, reading, register)
    print(said, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
