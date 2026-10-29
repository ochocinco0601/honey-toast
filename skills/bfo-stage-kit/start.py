"""The run's first work after the launch: find the work already in the workspace, and decide by script whether this
run picks up a run of this kit or starts fresh.

Usage: python start.py <workspace root>                    find earlier work and decide
       python start.py <workspace root> --resume <folder>  carry on the run in that folder (the person's pick)
       python start.py <workspace root> --system "<name>"  as above, for the system the person named: only a run
                                                           of that system is picked up; another system's unfinished
                                                           run is listed beside (OTHER lines) and the run starts fresh
       python start.py <workspace root> --new              the person asked for new work: start fresh beside any
                                                           unfinished run (BESIDE lines), leaving it as it is
       python start.py <workspace root> --first-look-ended  a first look stopped short of its brief: end its mark
       python start.py <workspace root> --release <folder> --words "<the person's words>"
                                                           the person says the other chat on that run has stopped:
                                                           its lock passes to this run, and the run is picked up

It searches the whole workspace for register folders: every folder holding `steps.csv` or `lifecycle.csv`, or a
`RUN.md` with the section *Earlier registers*, leaving out the kit itself (any folder at or under one holding
`SKILL.md`, and a template, which holds `REGISTER.md`). A folder whose `RUN.md` has *Earlier registers* was made by
this kit, and is a run; with its phases not all done or passed over, it can be picked up. Every other folder is an
earlier register: a tool's output, never a base. Then it decides, and prints the decision for the run:

    DECISION: resume             one run to pick up, its first look done: MESSAGE is the re-entry brief
    DECISION: finish-first-look  one run to pick up, its first look not done: finish it in FOLDER
    DECISION: choose             several runs to pick up: MESSAGE asks the person which; record it with --resume
    DECISION: fresh              no run to pick up: the first look starts fresh in a new register folder
    DECISION: held               one run to pick up, which another run is writing now: MESSAGE asks the person
                                 whether that chat has stopped; on their yes, --release with their words

Picking a run up takes its lock for this run (run_lock.py), so the helper doing the first look and the session that
launched it hold it together, and a second session is refused. With nothing naming the run, it refuses.

Then a line `FOLDER: <folder>` for each run named, a line `EARLIER: <folder>` for each earlier register found, and,
when there is something for the person, a line `MESSAGE:` followed by that text, which is sent to the person exactly
as printed. Exit 0, or 2 when refused. Python standard library only."""
import datetime
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import brief  # noqa: E402
import register_layout as layout  # noqa: E402
import run_lock  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TABLES = ("steps.csv", "lifecycle.csv")
KIT_SECTION = "## Earlier registers"
STARTED = "run-started.json"  # in the work folder: {"run": <the run's name>, "started": <ISO time>}
# in the work folder while a first look runs, from the start step to its brief: {"run", "since", "since_epoch",
# "folder"}. Two first looks inside one session carry one session id, so the lock cannot part them; this mark does.
FIRST_LOOK = "first-look.json"
FIRST_LOOK_MINUTES = 45


def first_look_open(site):
    """The mark of a first look begun and not yet at its brief, if it is younger than FIRST_LOOK_MINUTES."""
    try:
        m = json.loads((pathlib.Path(site) / FIRST_LOOK).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    age = (time.time() - float(m.get("since_epoch", 0))) / 60
    return m if 0 <= age < FIRST_LOOK_MINUTES else None


def mark_first_look(site, folder=None):
    p = pathlib.Path(site) / FIRST_LOOK
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"run": run_lock.identity(), "since": datetime.datetime.now().isoformat(timespec="seconds"),
                             "since_epoch": time.time(), "folder": str(folder) if folder else None}), encoding="utf-8")


def end_first_look(site):
    """The first look reached its brief (brief.py capability), or the session says it stopped short."""
    (pathlib.Path(site) / FIRST_LOOK).unlink(missing_ok=True)


def first_look_refusal(m, root="<workspace root>"):
    ago = max(0, int((time.time() - float(m.get("since_epoch", 0))) // 60))
    return (f"REFUSED: the first look is already running: it began {ago} minute(s) ago and has not reached its brief. "
            "Two first looks on one workspace overwrite each other's work, so nothing was started. Wait for the "
            "helper doing it to return. If no first look is running any more (its helper returned blocked, or "
            f'stopped), end the mark with: python start.py "{pathlib.Path(root).resolve()}" --first-look-ended, and run the start '
            f"step again. The mark lapses by itself {FIRST_LOOK_MINUTES} minutes after it was made.")
SKIP = {".git", "node_modules", "venv", ".venv", "__pycache__", ".tox", ".mypy_cache", ".pytest_cache", "worktrees"}


def made_by_this_kit(folder):
    p = pathlib.Path(folder) / "RUN.md"
    try:
        return p.is_file() and KIT_SECTION in p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def resumable(folder):
    """A run of this kit whose phases are not all done or passed over."""
    reg = pathlib.Path(folder)
    if not made_by_this_kit(reg):
        return False
    if not brief.phases(reg):
        return True  # a record with no status table yet: the run stopped before it began its first phase
    st = brief.state(reg)
    return st is not None and st[0] is not None


def registers(root):
    """(runs of this kit, earlier registers) under `root`, each a sorted list of resolved folders. The kit's own
    folders (a skill folder, its template, its worked example) are never either."""
    root = pathlib.Path(root).resolve()
    runs, earlier = [], []
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            kids = list(d.iterdir())
        except OSError:
            continue
        names = {p.name for p in kids}
        if "SKILL.md" in names or d == HERE:
            continue  # a skill folder, this kit's among them: its template and example are never a run
        if "REGISTER.md" not in names and (any(t in names for t in TABLES) or made_by_this_kit(d)):
            (runs if made_by_this_kit(d) else earlier).append(d)
        stack += [p for p in kids if p.name not in SKIP and not p.is_symlink() and p.is_dir()]
    return sorted(runs), sorted(earlier)


def to_pick_up(root):
    """(runs of this kit that can be picked up, earlier registers) under `root`."""
    runs, earlier = registers(root)
    return [r for r in runs if resumable(r)], earlier


def what_it_is(reg):
    """The work in a folder as the person knows it: the capability's name from the first look, else the application
    as the run record gives it, else the folder's own name."""
    o = brief.load(reg, layout.ORIENTATION) or {}
    name = ((o.get("capability") or {}).get("name") or "").strip()
    if name:
        return name
    p = reg / "RUN.md"
    for line in (p.read_text(encoding="utf-8").splitlines() if p.is_file() else []):
        if line.startswith("- **Application:**"):
            v = line.split(":**", 1)[1].strip()
            if v and not v.startswith("_"):
                return v.rstrip(".")
    try:  # no name given yet: the person knows it by when it was last worked on, never by its folder
        when = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%d %B %Y").lstrip("0")
    except OSError:
        return "work with no name yet"
    return f"the work last worked on {when}"


def plain(text):
    """A name reduced to its letters and digits, lower-cased, so "the Sock Shop" and "sockshop" can be compared."""
    return "".join(c for c in (text or "").lower() if c.isalnum())


def of_system(reg, system):
    """Whether the run in `reg` is for the system the person named: its capability, application or folder name and
    the name they gave each hold the other."""
    asked = plain(system)
    names = {plain(what_it_is(reg)), plain(reg.name)} - {""}
    return any(n in asked or asked in n for n in names)


def first_look_done(reg):
    ph = brief.phases(reg)
    return bool(ph) and ph[0][1] == "done"


def resume(reg):
    """The decision and the message for picking up the run in `reg`."""
    if not first_look_done(reg):
        return "finish-first-look", ""
    o = brief.load(reg, layout.ORIENTATION)
    if brief.problems(reg, o):
        return "finish-first-look", ""  # marked done without what the brief is drawn from: the first look is owed
    return "resume", brief.reentry(reg, o).rstrip("\n") + (
        "\n\nIf you want new work started instead, say so, and I will start it beside this and leave this as it is.\n")


def choose_message(found):
    lines = [f"{brief.STATUS_LEAD} Starting · Found work started before · Next: your pick of which work to carry on "
             "· Waiting on you: your pick", "",
             "**This work was started before, more than once.** Each of these was begun and is not finished:", ""]
    for i, reg in enumerate(found, 1):
        nxt = brief.status(reg).split("Next: ", 1)[-1].split(" · ")[0]
        lines.append(f"{i}. *{what_it_is(reg)}*: next comes {brief.cont(nxt)}."
                     + (" Another chat is working on it now." if held_by_another(reg) else ""))
    lines += ["", "Which should I carry on with? Say its number or its name. If you want new work started instead, "
              "say so, and I will start it beside these and leave them as they are."]
    return "\n".join(lines)


def held_by_another(reg):
    """The lock on `reg` when another run holds it and it is not stale, else None."""
    d = run_lock.read(reg)
    return d if d and d["run"] != run_lock.identity() and not run_lock.stale(d) else None


def held_message(reg):
    d = run_lock.read(reg) or {}
    ago = run_lock.minutes_since(d) if d else 0
    return "\n".join([
        f"{brief.STATUS_LEAD} Starting · Found work started before, open in another chat · Next: carrying on with it "
        "once that chat has stopped · Waiting on you: whether that chat has stopped", "",
        f"**This work was started before, and another chat is working on it.** *{what_it_is(reg)}* was last worked on "
        f"{ago} minute{'s' if ago != 1 else ''} ago, from another chat. Two chats working on it at once would overwrite "
        "each other's work, so I have not touched it.", "",
        "If that chat is closed or has stopped, say so, and I will carry on here from where the work stands. Otherwise, "
        "carry on in that chat."])


def open_the_page(root):
    """The start step's first act: the work page up, served from the workspace's work folder (made if need be), so
    the person has it while the rest runs. Prints the PAGE line; a listener that cannot start never stops the run."""
    import listener
    site = pathlib.Path(root).resolve() / listener.WORK
    try:
        print(listener.say(*listener.up(site)))
    except OSError as e:
        print(f"PAGE: not brought up ({e}); the run goes on without it")
    return site


def record_start(site):
    """When this run started, in the work folder, for the page's "running N minutes": kept while the same run calls
    the start step again, written new for another run."""
    run = run_lock.identity()
    p = pathlib.Path(site) / STARTED
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("run") == run and d.get("started"):
            return d
    except (OSError, ValueError):
        pass
    d = {"run": run, "started": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d), encoding="utf-8")
    return d


def emit(decision, folders=(), earlier=(), message=""):
    out = [f"DECISION: {decision}"] + [f"FOLDER: {f}" for f in folders] + [f"EARLIER: {e}" for e in earlier]
    if message:
        out += ["MESSAGE:", message.rstrip("\n")]
    print("\n".join(out))


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = list(argv)
    new = "--new" in args
    ended = "--first-look-ended" in args
    args = [a for a in args if a != "--first-look-ended"]
    args = [a for a in args if a != "--new"]
    picked = release_words = None
    releasing = "--release" in args
    for flag in ("--resume", "--release"):
        if flag in args:
            i = args.index(flag)
            picked = args[i + 1] if i + 1 < len(args) else ""
            args = args[:i] + args[i + 2:]
    system = None
    if "--system" in args:
        i = args.index("--system")
        system = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    words = ""
    if "--words" in args:
        i = args.index("--words")
        words = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    if releasing:
        release_words = words
    if len(args) != 1 or not pathlib.Path(args[0]).is_dir() or picked == "":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    if release_words is not None and not release_words.strip():
        print("REFUSED: --release needs the person's words, word for word: --words \"<their words>\". Release a run "
              "only when the person says the other chat has stopped. Nothing written.", file=sys.stderr)
        return 2
    site = open_the_page(args[0])  # first, so the person has the page while the rest runs
    if ended:
        end_first_look(site)
        print("ENDED: the mark of a first look under way is removed; run the start step again.")
        return 0
    found, earlier = to_pick_up(args[0])
    other = []
    if system and system.strip() and picked is None and not new:
        other = [r for r in found if not of_system(r, system)]
        found = [r for r in found if of_system(r, system)]
    if other and not found:  # another system's unfinished work: the named system starts fresh, beside it
        if first_look_open(site):
            print(first_look_refusal(first_look_open(site), args[0]), file=sys.stderr)
            return 2
        mark_first_look(site)
        record_start(site)
        emit("fresh", earlier=earlier)
        print("\n".join(f"OTHER: {f}" for f in other))
        print('NEW: the unfinished work here is for another system. Start the register with start_register.py --new '
              '--words "<the person\'s request, word for word>", which records them.')
        return 0
    if new:  # the person asked for new work: the unfinished runs are left as they are, beside it
        if first_look_open(site):
            print(first_look_refusal(first_look_open(site), args[0]), file=sys.stderr)
            return 2
        mark_first_look(site)
        record_start(site)
        emit("fresh", earlier=earlier)
        if found:
            print("\n".join(f"BESIDE: {f}" for f in found))
            print('NEW: start the register with start_register.py --new --words "<the person\'s words, word for '
                  'word>", which records them; without them it refuses a new register beside unfinished work.')
        return 0
    if picked is not None:
        reg = pathlib.Path(picked).resolve()
        if reg not in found:
            print(f"REFUSED: {picked} is not a run of this kit that can be picked up. Those that can: "
                  + (", ".join(map(str, found)) or "none") + ". Nothing written.", file=sys.stderr)
            return 2
        found = [reg]
    if not found:
        if first_look_open(site):
            print(first_look_refusal(first_look_open(site), args[0]), file=sys.stderr)
            return 2
        mark_first_look(site)
        record_start(site)
        emit("fresh", earlier=earlier)
        return 0
    if len(found) > 1:
        emit("choose", folders=found, earlier=earlier, message=choose_message(found))
        return 0
    reg = found[0]
    if release_words is not None:
        run_lock.release(reg, release_words)
    refused, note = run_lock.hold(reg, take_missing=True)
    if refused:
        emit("held", folders=[reg], earlier=earlier, message=held_message(reg))
        return 0
    if note:
        print(note, file=sys.stderr)
    record_start(site)  # the decision has cleared: this run is the one under way
    decision, message = resume(reg)
    if decision == "finish-first-look":
        # a release, on the person's word, is the run carrying on its own first look, never a second one
        if first_look_open(site) and release_words is None:
            print(first_look_refusal(first_look_open(site), args[0]), file=sys.stderr)
            return 2
        mark_first_look(site, reg)
    emit(decision, folders=[reg], earlier=earlier, message=message)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
