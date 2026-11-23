"""The run's first work after the launch: find the work already in the workspace, and decide by script whether this
run picks up a run of this kit or starts fresh.

Usage: python start.py <workspace root>                    find earlier work and decide
       python start.py <workspace root> --resume <folder>  carry on the run in that folder (the person's pick)
                                                           (a finished run too, named to take it further)
       python start.py <workspace root> --system "<name>"  as above, for the system the person named: only a run
                                                           of that system is picked up; another system's unfinished
                                                           run is listed beside (OTHER lines) and the run starts fresh
       python start.py <workspace root> --new              the person asked for new work: start fresh beside any
                                                           unfinished run (BESIDE lines), leaving it as it is
       python start.py <workspace root> --first-look-ended  a first look stopped short of its brief: end its mark
       ... --gave code|name|nothing                         on the run's first call: what the request gave to look
                                                           at, which fills the launch's last part (default: name
                                                           with --system, else code when the workspace holds any)
       ... --request "<the person's request, word for word>"   with any of the above: the request kept as data, so a
                                                           later stop it already answers is not asked (on a fresh
                                                           start, or a first look finished; a run picked up keeps
                                                           the request it was started with)
       python start.py <workspace root> --release <folder> --words "<the person's words>" [--test]
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

Then a line `FOLDER: <folder>` for each run named, a line `EARLIER: <folder>` for each earlier register found; on
resume at a stop where the page takes a pick (the go, the pick, the next flow), a line `WAIT:` with the wait the
session starts before it ends its turn; and, when there is something for the person, a line `MESSAGE:` followed by
that text, last, which is sent to the person exactly as printed. On the run's first call (no --resume, --release or
--new) MESSAGE is the run's whole first message: the launch (LAUNCH.md, its last part filled from --gave), then what
the decision says (on fresh or finish-first-look, that the page is open), then the page's one address. A run whose phases are all done is picked up too while the
first look found flows it has not started: the next flow goes into its register. Exit 0, or 2 when refused. Python standard library only."""
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
# The kit-version check comes first and uses the standard library only: a partial copy may lack the very modules
# imported below, so it is caught here, before any of them is imported.
MARKER = "KIT-VERSION.txt"  # in each built skill folder: the build it is, and every file it holds
MARKER_HEAD = ("The version of this skill folder, written when it was built: the release and date it was built "
               "as, then every file with the first 12 characters of a hash of its text (line endings aside). "
               "The start step checks the folder against it at every launch and resume.")


def _digest(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]


def _files(folder):
    folder = pathlib.Path(folder)
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")
                  if p.is_file() and p.name != MARKER and p.suffix != ".pyc"
                  and not any(x == "__pycache__" or x.startswith(".") for x in p.relative_to(folder).parts))


def write_marker(folder, release, date):
    """Write KIT-VERSION.txt for a folder: the release, its date, and each file's digest."""
    folder = pathlib.Path(folder)
    lines = [MARKER_HEAD, f"Build: {release} {date}"] + [f"{_digest(folder / r)}  {r}" for r in _files(folder)]
    (folder / MARKER).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def marker_files(folder):
    """{relative path: digest} as the folder's marker lists them, or None with no marker."""
    p = pathlib.Path(folder) / MARKER
    if not p.is_file():
        return None
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines()[2:]:
        digest, _, rel = line.partition("  ")
        if rel:
            out[rel] = digest
    return out


def kit_check(folder=None):
    """(the build the folder says it is, [warnings]): a file the marker lists that is missing or changed, or one it
    does not list, is a partial copy or one mixed with another version, named plainly."""
    folder = pathlib.Path(folder or HERE)
    listed = marker_files(folder)
    if listed is None:
        return "of no known build", [f"no version marker ({MARKER}) in {folder}: this copy was made before the kit "
                                     "had one, or copied in part; install the kit again from its source before "
                                     "going on"]
    head = (folder / MARKER).read_text(encoding="utf-8").splitlines()[1].split()
    built = f"built from {head[1] if len(head) > 1 else 'an unknown release'} on {head[2] if len(head) > 2 else 'an unknown date'}"
    have = set(_files(folder))
    missing = sorted(set(listed) - have)
    changed = sorted(r for r in set(listed) & have if _digest(folder / r) != listed[r])
    extra = sorted(have - set(listed))

    def some(names):
        return ", ".join(names[:8]) + (f" and {len(names) - 8} more" if len(names) > 8 else "")
    parts = ([f"{len(missing)} missing ({some(missing)})"] if missing else []) + \
            ([f"{len(changed)} changed ({some(changed)})"] if changed else []) + \
            ([f"{len(extra)} not in that build ({some(extra)})"] if extra else [])
    if not parts:
        return built, []
    restore = (f"To put it right, delete {folder} whole and copy the skill folder in fresh from the release it came "
               "from (copying over it leaves the changed and extra files in place), then run the start step again")
    if changed or extra:
        return built, [f"files of the kit at {folder} were changed after it was installed: " + "; ".join(parts)
                       + ". The kit is never changed where it runs: a change made here is lost at the next release, "
                       "and a problem found in the kit is written down in the run's kit-findings.md (kit_findings.py) "
                       "for the person to report to whoever maintains the kit. " + restore]
    return built, [f"this copy of the kit at {folder} does not match the build it says it is: " + "; ".join(parts)
                   + ". It is a partial copy, or mixed with another version. " + restore]


def is_source(folder=None):
    """A development copy of the kit (BFO_KIT_SOURCE=1), which carries no marker, rather than an installed one."""
    folder = pathlib.Path(folder or HERE)
    return os.environ.get("BFO_KIT_SOURCE") == "1" and not (folder / MARKER).is_file()


def kit_line(folder=None):
    """The KIT line the start step prints first at every launch and resume."""
    folder = pathlib.Path(folder or HERE)
    if is_source(folder):
        return "KIT: a development copy, not an installed one"
    built, warnings = kit_check(folder)
    return f"KIT: {built}" + "".join(f"; WARNING: {w}" for w in warnings)


def restore_said(name):
    """What the person is told to do with a changed or partial copy: the folder by its skill's name, never a path,
    which the word check refuses; deleted first, since a copy over it keeps the changed and extra files."""
    return (f"Your copy of the \"{name}\" skill was changed or is incomplete, so the run cannot start. Delete its "
            f"folder, \"{name}\", in this project's skills folder, copy it in fresh from the release it came from, "
            "then start again.")


BLOCKED = ("DECISION: blocked\nThis copy of the kit does not match its build (the KIT line above names what is "
           "missing or changed). Nothing was written. Never edit the kit's files to get past this. Send the person "
           "this, through brief.py say, as it is: " + restore_said(HERE.name) + "\nOnce they have, run the start "
           "step again.")
if __name__ == "__main__" and not is_source() and kit_check()[1]:
    print(kit_line())
    print(BLOCKED)
    sys.exit(2)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import brief  # noqa: E402
import register_layout as layout  # noqa: E402
import run_lock  # noqa: E402

TABLES = ("steps.csv", "lifecycle.csv")
KIT_SECTION = "## Earlier registers"
STARTED = "run-started.json"  # in the work folder: {"run": <the run's name>, "started": <ISO time>}
# in the work folder while a first look runs, from the start step to its brief: {"run", "since", "since_epoch",
# "folder"}. Two first looks inside one session carry one session id, so the lock cannot part them; this mark does.
FIRST_LOOK = "first-look.json"
FIRST_LOOK_MINUTES = 45


UPGRADE_SAID = ("Before carrying on, I brought this work's saved records up to the form this version reads: what they "
                "say is unchanged, and a copy of them as they were is kept outside your workspace.")
FILL_SAID = "each measure now also records the flow it was proposed for, filled in from where it already sat"
FILL_NOTE = "measures.csv: the flow"  # the start of the upgrade's own note for that fill (reconcile.migrate)


def changes_said(changed, notes):
    """Everything the upgrade changed, in the person's words: the flow fill, the stated time limits moved to where
    they are kept as expected outcomes, the alert choices moved to a list of their own, and names brought up to date."""
    what = [FILL_SAID] if any(n.startswith(FILL_NOTE) for n in notes) else []
    limits = [n for n in notes if not n.startswith(FILL_NOTE)]
    if limits:
        what.append(f"{len(limits)} stated time limit{'s' if len(limits) != 1 else ''}, which no code sets, "
                    f"{'are' if len(limits) != 1 else 'is'} now kept as {'expected outcomes' if len(limits) != 1 else 'an expected outcome'}, "
                    "still to be confirmed")
    if any(c.endswith("alerts.csv") for c in changed):
        what.append("the choices of what to alert on are now kept in a list of their own")
    accounted = {"measures.csv", "alerts.csv", "expectations.csv"}
    if any(pathlib.Path(c).name not in accounted for c in changed) or (
            any(pathlib.Path(c).name == "measures.csv" for c in changed) and not what):
        what.append("some names were brought up to the ones this version uses")
    return "What changed: " + "; ".join(what) + "." if what else ""


def upgrade_if_old(reg):
    """A register an older kit wrote, upgraded in place at the start, announced and never asked: the upgrade is tried on a copy of its tables first, and only where it changes something
    is the register backed up outside the workspace (BFO_BACKUPS, else the system's temporary folder) and upgraded.
    Returns (the backup, the files changed, the upgrade's notes, what it leaves owed, the line the person is told),
    or None when nothing needs it. The line is UPGRADE_SAID, with the upgrade's own line for AI agent actions not yet
    marked (a re-walk, announced before it starts) where there are any."""
    import importlib
    import go
    try:  # by name: the measures skill carries no reconcile.py (an upgrade is mapping's), and there none is tried
        reconcile = importlib.import_module("reconcile")
    except ImportError:
        return None
    reg = pathlib.Path(reg)
    for_flow = go.inferred_for_flow(reg)
    with tempfile.TemporaryDirectory() as t:
        trial = pathlib.Path(t) / reg.name
        trial.mkdir()
        for p in reg.glob("*.csv"):
            shutil.copy2(p, trial / p.name)
        for p in reg.glob("earlier-flows/*/*.csv"):
            (trial / p.parent.relative_to(reg)).mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, trial / p.relative_to(reg))
        if not reconcile.migrate(trial, [], for_flow):
            return None
    base = pathlib.Path(os.environ.get("BFO_BACKUPS") or pathlib.Path(tempfile.gettempdir()) / "bfo-backups")
    backup = base / f"{reg.name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    shutil.copytree(reg, backup, ignore=shutil.ignore_patterns("__pycache__"))
    notes = []
    changed = reconcile.migrate(reg, notes, for_flow)
    said = " ".join(x for x in (UPGRADE_SAID, changes_said(changed, notes),
                                reconcile.unclassed_line(reconcile.unclassed_agents(reg))) if x)
    return backup, changed, notes, reconcile.still_owed(reg), said


RUN_DIR = "_start-"  # in the work folder, one per run (chat): its start record, say-back and answers before a register


def run_dir(site, run=None):
    """The folder in the work folder that holds this run's start-time state, so runs started in one window on
    different systems never share it. Keyed by the run's name; a run nothing names shares one folder."""
    run = run_lock.identity() if run is None else run
    key = hashlib.sha256(run.encode("utf-8")).hexdigest()[:10] if run else "unnamed"
    return pathlib.Path(site) / (RUN_DIR + key)


def is_run_dir(folder):
    folder = pathlib.Path(folder)
    return folder.name.startswith(RUN_DIR) and folder.parent.name == run_lock.WORK


def start_file(site, name):
    """This run's copy of a start-time file; a work folder written by an earlier release, where one copy served the
    whole window, is read while this run has none of its own."""
    own = run_dir(site) / name
    old = pathlib.Path(site) / name
    return own if own.exists() or not old.exists() else old


def first_look_open(site):
    """This run's mark of a first look begun and not yet at its brief, if younger than FIRST_LOOK_MINUTES. Two first
    looks inside one run (one chat) are refused by it; another run's first look on another system is not."""
    for p in (run_dir(site) / FIRST_LOOK, pathlib.Path(site) / FIRST_LOOK):
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if p.parent != run_dir(site) and m.get("run") != run_lock.identity():
            continue  # an earlier release's window-wide mark, made by another run
        age = (time.time() - max(float(m.get("since_epoch", 0)), float(m.get("refreshed_epoch", 0)))) / 60
        if 0 <= age < FIRST_LOOK_MINUTES:
            return m
        try:  # past the minutes, the mark holds while the first-look helper or a source reader is alive
            import first_look
            if first_look.agents_alive(site):
                return m
        except (ImportError, OSError, ValueError):
            pass
    return None


def mark_first_look(site, folder=None):
    p = run_dir(site) / FIRST_LOOK
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"run": run_lock.identity(), "since": datetime.datetime.now().isoformat(timespec="seconds"),
                             "since_epoch": time.time(), "folder": str(folder) if folder else None}), encoding="utf-8")


def end_first_look(site):
    """The first look reached its brief (brief.py capability), or the session says it stopped short."""
    (run_dir(site) / FIRST_LOOK).unlink(missing_ok=True)
    old = pathlib.Path(site) / FIRST_LOOK
    try:
        if json.loads(old.read_text(encoding="utf-8")).get("run") == run_lock.identity():
            old.unlink(missing_ok=True)
    except (OSError, ValueError):
        pass


def first_look_refusal(m, root="<workspace root>"):
    ago = max(0, int((time.time() - float(m.get("since_epoch", 0))) // 60))
    return (f"REFUSED: the first look is already running: it began {ago} minute(s) ago and has not reached its brief. "
            "Two first looks in one chat overwrite each other's work, so nothing was started. Wait for the "
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
    """A run of this kit whose phases are not all done or passed over, or whose flow is done while the first look
    found flows it has not started: the next flow is added to the same register."""
    reg = pathlib.Path(folder)
    if not made_by_this_kit(reg):
        return False
    if not brief.phases(reg):
        return True  # a record with no status table yet: the run stopped before it began its first phase
    st = brief.state(reg)
    if st is not None and st[0] is not None:
        return True
    import go
    return st is not None and go.load(reg) is not None and bool(go.flows_left(reg))


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


def refresh_timings(reg):
    """Rewrite the run's timing record (job/timings.csv) before anything else when a run is picked up, so the times of
    agents a crash or a restart cut off are on record. Never raises, prints nothing (timings.refresh logs a failure to
    the register's events.log)."""
    try:
        import timings
        timings.refresh(reg, why="start.py: run picked up")
    except Exception:  # noqa: BLE001  (timings.py could not be loaded: the pickup goes on)
        pass


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


def record_release(reg, words, test=False):
    """The person's answer that the other chat has stopped, kept with the question it answered, before the hold moves."""
    import go
    go.record_decision(reg, "release", words, "chat", test=test, shown=held_message(reg))


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
    """The start step's first act: the run status view up, served from the workspace's work folder (made if need
    be), so the person has it while the rest runs: before any run folder exists it shows the first look under way,
    and its address then leads to the run's own; it links to the work page and the run's home. Prints the PAGE line;
    a listener that cannot start never stops the run."""
    import listener
    import operator_page
    site = pathlib.Path(root).resolve() / listener.WORK
    run_dir(site).mkdir(parents=True, exist_ok=True)
    try:
        line = listener.say(*listener.up(site, run_page(site)))
        # the address reaches the person once, at the end of MESSAGE, never also typed from this line
        print(line.split(" Give the person the address", 1)[0] + " Its address goes to the person in MESSAGE below.")
    except OSError as e:
        print(f"PAGE: not brought up ({e}); the run goes on without it. Do not tell the person the page is open: "
              "MESSAGE below says that the page for this work could not be opened and the work goes on without it")
    return site


def started_by(folder=None):
    """Which skill this start step belongs to: "mapping" for the mapping skill (its folder holds MAPPING-STEPS.md and
    no FILL-STEPS.md), else "kit"."""
    folder = pathlib.Path(folder or HERE)
    return "mapping" if (folder / "MAPPING-STEPS.md").is_file() and not (folder / "FILL-STEPS.md").is_file() else "kit"


def says_back(folder=None):
    """Whether this start step says back what it understood before anything is read: the mapping skill's and the
    stage kit's do; the measures skill's (its folder holds MEASURES-STEPS.md and no FILL-STEPS.md) only picks up a
    finished map and is left as it is."""
    folder = pathlib.Path(folder or HERE)
    return not ((folder / "MEASURES-STEPS.md").is_file() and not (folder / "FILL-STEPS.md").is_file())


ASK_SYSTEM = "Which system should I look at? Name it, or point me at its code."


def say_back_task(folder, kind, register=None):
    """The SAYBACK line: the session drafts what it understood, and nothing is read before the person's Start."""
    keys = ("application (the system, as they named it or as the folders show it); code (what code is open here, "
            "from the folders' names only: read no file; when only a name was given and its code is not here, say so); "
            "search (only when the code is not here: where you propose to look, taken from the environment, in "
            "plain words; the page then asks whether to look there, with Yes and No and no Start, and nothing is "
            "searched before their yes); wants (what they want, from their request); "
            "answered (a statement, never a question, of what their request already settles: which flow first, or "
            "map only or further, as in 'map every flow, from your words'; when it settles neither, 'Nothing yet: "
            "after the first look I ask which flow to start with')") if kind == "fresh" else (
            "application; proposal (what this session proposes to work on now, from where each flow stands); wants "
            "only if their words say something new")
    reg = f' --register "{register}"' if register else ""
    return (f"SAYBACK: before anything is read, draft what you understood, each line short, in their words: write a "
            f"JSON file outside the system's code with the keys {keys}; then run python \"{HERE / 'say_back.py'}\" "
            f"draft \"{folder}\" --lines \"<that file>\"{reg}. What it prints after MESSAGE is your whole reply this "
            "turn. Start no helper and read no code until the person "
            + ("says carry on." if kind == "resume" else "presses Start or says start."))


REQUEST = "- **Request:**"  # RUN.md's line under Plan and go: the person's request, word for word, as data


def record_request(reg, words, when=None):
    """The person's request, word for word, in the register's RUN.md, once: a run picked up keeps the request it was
    started with. Nothing is written without words or a RUN.md."""
    p = pathlib.Path(reg) / "RUN.md"
    if not (words or "").strip() or not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    if REQUEST in text:
        return
    when = when or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    line = f'{REQUEST} "{words.strip()}" (the person, {when})'
    lines = text.splitlines()
    at = next((i for i, x in enumerate(lines) if x.startswith("- **Plan:**")), None)
    if at is None:
        lines += ["", line]
    else:
        lines.insert(at, line)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def request_of(reg):
    """The request RUN.md keeps, word for word, or ""."""
    import re
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    m = re.search(r'^- \*\*Request:\*\* "(.*)" \(the person, [^)]*\)\s*$', text, re.M)
    return m.group(1) if m else ""


def record_start(site, request=None, reg=None, fresh=False):
    """When this run started, and which skill started it, in this run's own folder in the work folder: for the page's
    "running N minutes" and the status line's count of activities. Kept while the same run calls the start step
    again, written new for another run. The person's request, given, is kept with it, for the register started next
    (start_register.py); `reg`, the register this run carries on, is where its page leads. `fresh`: the start step
    begins new work; a record that already led to a register belongs to an earlier run in the same chat, so it is
    written new, or this run's page would lead to that run's register."""
    run = run_lock.identity()
    p = run_dir(site) / STARTED
    at = str(pathlib.Path(reg).resolve()) if reg is not None else None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("run") == run and d.get("started") and not (fresh and d.get("register")):
            changed = False
            if (request or "").strip() and not d.get("request"):
                d["request"] = request.strip()
                changed = True
            if at and d.get("register") != at:
                d["register"] = at
                changed = True
            if changed:
                p.write_text(json.dumps(d), encoding="utf-8")
            return d
    except (OSError, ValueError):
        pass
    d = {"run": run, "started": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
         "skill": started_by()}
    if (request or "").strip():
        d["request"] = request.strip()
    if at:
        d["register"] = at
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d), encoding="utf-8")
    return d


def run_page(site):
    """This run's own run status address under the work folder's listener, never the window-wide one."""
    return run_dir(site).name + "/operator.html"


def wait_line(reg):
    """At a stop where the page takes a pick (the go, the pick, the next flow), the page made ready for it and the
    wait the session starts before it ends its turn, as at every stop; else ''."""
    import depth
    import wait_on_page
    c = depth.build(reg)["open_choice"]
    if not c or c["task"] not in wait_on_page.ON_PAGE:
        return ""
    depth.write_quietly(reg)
    return ("Start the wait on the page before you end your turn, as at every stop. "
            + wait_on_page.how_to_wait(wait_on_page.commands(reg)))


LAUNCH = "LAUNCH.md"  # in each skill folder that starts a run: the launch, the first message of every run
PAGE_OPEN_LOOK = "The page for this work is open in your browser, and the first look over the system is under way."
PAGE_OPEN = "The page for this work is open in your browser."
PAGE_NOT_OPEN = "The page for this work could not be opened; the work goes on without it."
SEND = ("SEND: the text after MESSAGE is your whole reply to the person this turn, copied exactly, with nothing before "
        "or after it (but for the skill's proposal of where to look, when only a name was given and its code is not "
        "here), and the last thing you write this turn. Write no text before it, not even a line that you are "
        "starting the helper. On fresh or finish-first-look, start the first-look helper first, as the skill says, "
        "and then send it.")


def launch_file(folder=None):
    """The skill's LAUNCH.md, in its own folder; a development copy takes the stage kit's."""
    folder = pathlib.Path(folder or HERE)
    for p in (folder / LAUNCH, folder / "bfo-stage-kit" / LAUNCH):
        if p.is_file():
            return p
    return None


def gave_of(root, system=None, gave=None):
    """What the request gave to look at: the kind the session named (`--gave`), else a name when it named one, else
    code when the workspace holds any folder or file besides the kit's own, else nothing."""
    if gave in ("code", "name", "nothing"):
        return gave
    if (system or "").strip():
        return "name"
    import listener
    own = {".claude", ".git", ".vscode", listener.WORK}
    return "code" if any(p.name not in own for p in pathlib.Path(root).iterdir()) else "nothing"


def launch(gave, system=None, folder=None):
    """The launch, its last part filled from what the request gave; "" for a skill with no launch of its own."""
    import re
    p = launch_file(folder)
    if p is None:
        return ""
    t = p.read_text(encoding="utf-8")
    body = t.split("<!-- launch -->", 1)[1].split("<!-- /launch -->", 1)[0].strip("\n")
    m = re.search(r"<!-- begin %s -->\n(.*?)\n<!-- /begin -->" % gave, t, re.S)
    begin = m.group(1).strip().replace("{system}", (system or "").strip() or "this system")
    return body.replace("{begin}", begin)


def first_message(launch_text, body, address):
    """The run's first message, whole: the launch, then what the decision says (the page line, a brief), then the one
    address. One status line: the launch's, unless what follows opens with its own, which then leads."""
    import brief
    parts = [launch_text.strip()] if launch_text.strip() else []
    body = body.strip()
    if parts and body.startswith(brief.STATUS_LEAD):
        status, _, body = body.partition("\n\n")
        parts = [status, parts[0].partition("\n\n")[2]]
    if body:
        parts.append(body)
    if address:
        parts.append(address)
    return "\n\n".join(parts)


def address_line(site, reg=None):
    """The one address the first message gives: the run's home, on a run picked up that has one (the person's pick
    waits there); else the run status page."""
    import brief
    import listener
    import operator_page
    if reg is not None and (pathlib.Path(reg) / "index.html").is_file():
        return brief.page_line(reg)
    url = listener.serving(site)
    if not url:
        return ""
    if reg is not None and (pathlib.Path(reg) / "RUN.md").is_file():
        return brief.PAGE_LEAD + url + pathlib.Path(reg).name + "/" + operator_page.FILE
    return brief.PAGE_LEAD + url + run_page(site)


START_LINES = "start-lines.json"  # in this run's own folder: the start step's DECISION, FOLDER and EARLIER lines
_SITE = None  # the work folder of this start step, set by main once the page is up


def emit(decision, folders=(), earlier=(), message="", wait="", extra=()):
    out = [f"DECISION: {decision}"] + [f"FOLDER: {f}" for f in folders] + [f"EARLIER: {e}" for e in earlier]
    if _SITE is not None:  # kept on disk, so the say-back's Start writes the helper's prompt from them, not the chat
        p = run_dir(_SITE) / START_LINES
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"decision": decision, "folders": [str(f) for f in folders],
                                 "earlier": [str(e) for e in earlier],
                                 "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}),
                     encoding="utf-8")
    out += list(extra)
    if wait:
        out.append(f"WAIT: {wait}")
    if message:
        out += [SEND, "MESSAGE:", message.rstrip("\n")]
    print("\n".join(out))


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = list(argv)
    new = "--new" in args
    ended = "--first-look-ended" in args
    args = [a for a in args if a != "--first-look-ended"]
    args = [a for a in args if a != "--new"]
    test = "--test" in args  # a test standing in for the person: its answers are kept as a test's
    args = [a for a in args if a != "--test"]
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
    request = None
    if "--request" in args:
        i = args.index("--request")
        request = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    gave = None
    if "--gave" in args:
        i = args.index("--gave")
        gave = args[i + 1] if i + 1 < len(args) else ""
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
    global _SITE
    site = open_the_page(args[0])  # first, so the person has the page while the rest runs
    _SITE = site
    print(kit_line())  # which build this is, and a partial or mixed copy named, before any work
    if not is_source() and kit_check()[1]:  # a broken copy takes no lock, writes no mark, upgrades nothing
        print(BLOCKED)
        return 2
    if ended:
        end_first_look(site)
        print("ENDED: the mark of a first look under way is removed; run the start step again.")
        return 0
    found, earlier = to_pick_up(args[0])
    gave = gave_of(args[0], system, gave)
    saying_back = says_back() and picked is None and not new
    # coming back to a case is said back however the register was reached: found, picked from a list, or released
    coming_back = says_back() and not new
    # the run's first call only; the mapping skill sends no launch: it says back what it understood instead
    launch_text = launch(gave, system) if picked is None and not new and not saying_back else ""

    def said(decision, body="", reg=None):
        """MESSAGE: on the first call the launch leads it; on fresh or finish-first-look the page line follows;
        the one address ends it."""
        if decision in ("fresh", "finish-first-look"):
            if saying_back:  # the say-back's own message, printed by say_back.py; with nothing given, which system
                if gave == "nothing" and decision == "fresh":
                    return first_message("", ASK_SYSTEM, address_line(site, reg))
                return ""
            if not launch_text:
                return ""
            import listener
            if not listener.serving(site):
                body = PAGE_NOT_OPEN
            else:
                body = PAGE_OPEN_LOOK if gave == "code" or decision == "finish-first-look" else PAGE_OPEN
        return first_message(launch_text, body, address_line(site, reg))

    def sayback(decision, reg=None):
        if decision == "resume" and coming_back:  # the work picked up is what there is to say back
            return [say_back_task(reg, "resume")]
        if not saying_back:
            return []
        if gave == "nothing" and decision == "fresh":  # nothing to say back yet: which system comes first
            return []
        return [say_back_task(site.resolve(), "fresh", reg if decision == "finish-first-look" else None)]

    other = []
    if system and system.strip() and picked is None and not new:
        other = [r for r in found if not of_system(r, system)]
        found = [r for r in found if of_system(r, system)]
    if other and not found:  # another system's unfinished work: the named system starts fresh, beside it
        if first_look_open(site):
            print(first_look_refusal(first_look_open(site), args[0]), file=sys.stderr)
            return 2
        mark_first_look(site)
        record_start(site, request, fresh=True)
        emit("fresh", earlier=earlier, message=said("fresh"), extra=sayback("fresh") + [f"OTHER: {f}" for f in other] + [
            'NEW: the unfinished work here is for another system. Start the register with start_register.py --new '
            '--words "<the person\'s request, word for word>", which records them.'])
        return 0
    if new:  # the person asked for new work: the unfinished runs are left as they are, beside it
        if first_look_open(site):
            print(first_look_refusal(first_look_open(site), args[0]), file=sys.stderr)
            return 2
        mark_first_look(site)
        record_start(site, request, fresh=True)
        emit("fresh", earlier=earlier)
        if found:
            print("\n".join(f"BESIDE: {f}" for f in found))
            print('NEW: start the register with start_register.py --new --words "<the person\'s words, word for '
                  'word>", which records them; without them it refuses a new register beside unfinished work.')
        return 0
    if picked is not None:
        reg = pathlib.Path(picked).resolve()
        # a finished run of this kit, named, is picked up to take it further (the measures skill on a flow whose
        # mapping is finished): it takes the run's hold and upgrades an earlier version's register as any pickup does
        if reg not in found and not made_by_this_kit(reg):
            print(f"REFUSED: {picked} is not a run of this kit that can be picked up. Those that can: "
                  + (", ".join(map(str, found)) or "none") + ". Nothing written.", file=sys.stderr)
            return 2
        found = [reg]
    if not found:
        if first_look_open(site):
            print(first_look_refusal(first_look_open(site), args[0]), file=sys.stderr)
            return 2
        mark_first_look(site)
        record_start(site, request, fresh=True)
        emit("fresh", earlier=earlier, message=said("fresh"), extra=sayback("fresh"))
        return 0
    if len(found) > 1:
        emit("choose", folders=found, earlier=earlier, message=said("choose", choose_message(found)))
        return 0
    reg = found[0]
    refresh_timings(reg)  # first on any pickup: a crash or a stop mid-step leaves its agents' times on record
    if release_words is not None:
        record_release(reg, release_words, test=test)
        run_lock.release(reg, release_words)
    refused, note = run_lock.hold(reg, take_missing=True)
    if refused:
        emit("held", folders=[reg], earlier=earlier, message=said("held", held_message(reg)))
        return 0
    if note:
        print(note, file=sys.stderr)
    record_start(site, reg=reg)  # the decision has cleared: this run is the one under way
    try:
        upgraded = upgrade_if_old(reg)
    except Exception as e:  # noqa: BLE001 - the run goes on; the upgrade rule is followed by hand
        upgraded = None
        print(f"UPGRADE: not done ({type(e).__name__}: {e}). Run the register check (capability_views.py --check); "
              "if it names reconcile.py --migrate, follow the upgrade rule it states", file=sys.stderr)
    if upgraded:
        backup, changed, notes, owed, told = upgraded
        print(f"UPGRADED: this register was written by an older kit and is upgraded in place ({', '.join(changed)}); "
              f"its backup as it was is at {backup}. Before you send anything: run capability_views.py --check and "
              "restart the page's listener (listener.py stop <work folder>, then wait_on_page.py <register>). The "
              "message below tells the person; with no message, tell them in one line through brief.py say: " + told)
        print("\n".join(f"  {x}" for x in notes + owed if x))
    decision, message = resume(reg)
    if decision in ("resume", "finish-first-look"):  # picked up again: its stop is over, a stopped first look asked anew
        import run_state
        run_state.resumed(reg)
    if decision == "resume" and coming_back and (reg / "case.json").is_file():
        # coming back to a case: what exists and what this session proposes, said back on the page, never a brief
        emit("resume", folders=[reg], earlier=earlier, extra=sayback("resume", reg))
        return 0
    if upgraded and message:
        lead, _, rest = message.partition("\n\n")
        message = f"{lead}\n\n{upgraded[4]}\n\n{rest}"
    if decision == "finish-first-look":
        # a release, on the person's word, is the run carrying on its own first look, never a second one
        if first_look_open(site) and release_words is None:
            print(first_look_refusal(first_look_open(site), args[0]), file=sys.stderr)
            return 2
        mark_first_look(site, reg)
        record_start(site, reg=reg)
        record_request(reg, request)  # its first look is this run's own: the request is the one it starts with
    message = said(decision, message, reg) if message or decision == "finish-first-look" else message
    emit(decision, folders=[reg], earlier=earlier, message=message,
         wait=wait_line(reg) if decision == "resume" else "",
         extra=sayback(decision, reg) if decision == "finish-first-look" else ())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
