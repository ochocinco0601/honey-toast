"""The say-back: before anything is read in depth, the run says back what it understood, as a review step on the run
page (each line correctable, one Start), and waits for the person. On a case picked up (a register), Run status shows
nothing waiting on the person, so the lines and the ask (carry on, or correct a line) go in the chat instead.

Usage: python say_back.py draft <folder> --lines <json file> [--register <register>]
           write the lines and print the chat's one line (MESSAGE) and the wait (WAIT). <folder> is the work folder
           (bfo-work) on a fresh start, or the register picked up on a resume. The json holds the session's lines:
           application, code, wants, answered (fresh); application, proposal, and wants if their words say it
           (resume). The earlier work is drawn here, from what the workspace and the case record hold.
       python say_back.py answer <folder> (--answers <answers file> | --words "<their words, word for word>") [--test]
           record the person's Start or correction, with the lines they were shown
       python say_back.py earlier <workspace root> [--folder <register>]
           print the earlier-work line

One writer of say-back.json: this script. Answers go to say-back-decisions.jsonl in the work folder (the register's
decisions.jsonl on a resume), through case.py; start_register.py copies them into the register it starts.
"""
import json
import pathlib
import re
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
NO_PAGE = "The page could not be opened. Here is what I understood: correct any line, or say start."
# A case picked up: Run status shows nothing waiting on the person, so the lines and the ask are in the chat.
RESUME = "Here is what I understood. Say carry on, or tell me which line is wrong and what it should be."
START_WORDS = {"start", "yes", "y", "go", "ok", "okay", "go ahead", "yes start", "start it", "yes go ahead", "sure",
               "carry on", "yes carry on", "carry on please", "please carry on"}
# Each flow's case state as the earlier-work line counts it, in this order; a flow with no state is not started.
STATE_WORDS = (("mapped", "mapped and checked"), (case.ENDED, "not checked: you stopped the checks"),
               ("mapping", "under way"), (None, "not started"))
MAX_LISTED = 2  # more earlier maps than this: a count, and where they are listed


def is_register(folder):
    return (pathlib.Path(folder) / "RUN.md").is_file()


def root_of(folder):
    """The workspace root: the work folder's parent, or the register's work folder's parent."""
    folder = pathlib.Path(folder).resolve()
    return folder.parent.parent if is_register(folder) else folder.parent


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
    if is_register(folder):
        url = listener.serving(listener.site_of(folder))
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
        return json.loads((pathlib.Path(folder) / FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


NO_WORDS = {"no", "n", "nope", "no thanks", "dont", "do not", "not there"}


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
    p = folder / FILE
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(sb, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
    return sb, ""


def answer(folder, answers=None, words=None, test=False):
    """(what to print, exit code)."""
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
        said = words or ""
        norm = re.sub(r"[^\w ]", "", said.lower()).strip()
        if not norm:
            return "REFUSED: no words given. Nothing written.", 2
        if sb.get("search"):  # the question on the page is the search: a yes or no answers it, never Start
            action = "search-yes" if norm in START_WORDS else "search-no" if norm in NO_WORDS else "correct"
        else:
            action = "start" if norm in START_WORDS else "correct"
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
    into = case.DECISIONS if sb["kind"] == "resume" else DECISIONS
    entry = case.decide(folder, STOP, sb["shown"], said, source, test, into=into, kind=action,
                        corrections=corrections)
    if sb.get("register") and sb["kind"] == "fresh" and is_register(sb["register"]):
        case.import_decisions(sb["register"], [entry])
    sb["state"] = "started" if action == "start" else "corrected"
    sb["answered"] = entry["at"]
    (folder / FILE).write_text(json.dumps(sb, indent=2, ensure_ascii=False), encoding="utf-8")
    if action == "start":
        then = ("carry on with what the last line proposed" if sb["kind"] == "resume"
                else "start the first-look helper now, as the skill says")
        return f"STARTED: recorded, with the lines shown. Now {then}.", 0
    if sb["kind"] == "resume":
        return ("CORRECTED: recorded. Redraft the lines with this and run say_back.py draft again, and send what it "
                f"prints; read nothing before they say carry on. Their correction: {said}"), 0
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
                  "Their answer comes in the chat. Start no helper and read no code until they say carry on.")
            print("MESSAGE:\n" + RESUME + "\n\n" + listed)
            return 0
        url = address(folder)
        print(f"WAIT: Start the wait on the page before you end your turn. {wait(folder)}")
        print("SEND: the text after MESSAGE is your whole reply this turn, copied exactly. Start no helper and read "
              "no code until the person presses Start or says start.")
        body = MESSAGE.format(url=url) if url else NO_PAGE + "\n\n" + listed
        print("MESSAGE:\n" + body)
        return 0
    answers, args = option(args, "--answers")
    words, args = option(args, "--words")
    test = "--test" in args
    if (answers is None) == (words is None):
        print("REFUSED: give --answers <file> or --words \"<their words>\". Nothing written.", file=sys.stderr)
        return 2
    said, code = answer(folder, answers, words, test)
    print(said, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
