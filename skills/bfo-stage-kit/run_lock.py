"""One run writes a register at a time: a lock the start step takes, and every script that writes the register checks.

Two runs writing one register at once overwrite each other's work, so a second run is refused, never warned. A run is
named by the session id Claude Code sets in every shell it starts (CLAUDE_CODE_SESSION_ID). The shells of the
subagents a session launches carry the same id, so the helper that does the first look and the session that launched
it are one run and share the lock; a session started from inside another session's shell is given its own id, so it
is another run. Two subagents of one session running at once carry the same id too, and are not told apart. Where no
session id is set (the kit run outside Claude Code), BFO_RUN names the run. With neither, the run is never stopped:
no lock is taken or checked, and RUN.md records once that the lock did not guard the register, and why. A script is
refused only when a lock no older than STALE_MINUTES names a run and this process is named as a different one.

The lock is `RUN.lock` in the register folder. It names the run and when it last wrote. A lock no run has written for
STALE_MINUTES is stale: the next run to write takes it over, says so, and records the take-over in RUN.md, so a run
that crashed never leaves its register unusable. The person can also release a lock at once, in their own words, with
`python start.py <workspace root> --release <register folder> --words "<their words>"`.

A folder with no lock is taken by the first script that writes it, if this kit made it (its RUN.md has the section
Earlier registers); a folder this kit did not make, such as the worked example or an earlier register, is never
locked. Python standard library only."""
import datetime
import json
import os
import pathlib
import sys
import time

LOCK = "RUN.lock"
SESSION = "CLAUDE_CODE_SESSION_ID"
TOKEN = "BFO_RUN"
STALE_MINUTES = 240  # hand-written tables refresh no lock, so a hold outlasts hours of reading
KIT_SECTION = "## Earlier registers"
HOLDERS = "## Runs that held this register"


def identity():
    """The run this process belongs to, or None when nothing names it."""
    return (os.environ.get(SESSION) or os.environ.get(TOKEN) or "").strip() or None


def made_by_this_kit(reg):
    p = pathlib.Path(reg) / "RUN.md"
    try:
        return p.is_file() and KIT_SECTION in p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def read(reg):
    """The lock's content, or None when there is none (or it cannot be read as a lock)."""
    p = pathlib.Path(reg) / LOCK
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) and d.get("run") else None
    except (OSError, ValueError):
        return None


def minutes_since(d):
    return max(0, int((time.time() - float(d.get("touched", 0))) // 60))


def stale(d):
    return minutes_since(d) >= STALE_MINUTES


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def write(reg, run, taken=None):
    """Write the lock for `run` by replacing the file whole, so a reader never sees half of it."""
    p = pathlib.Path(reg) / LOCK
    tmp = p.with_name(f"{LOCK}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"run": run, "taken": taken or now(), "touched": time.time()}), encoding="utf-8")
    os.replace(tmp, p)


def create(reg, run):
    """Take a missing lock, or return False when another process made one first."""
    p = pathlib.Path(reg) / LOCK
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps({"run": run, "taken": now(), "touched": time.time()}))
    return True


def record(reg, line):
    """A line in RUN.md's record of the runs that held the register: take-overs and releases."""
    p = pathlib.Path(reg) / "RUN.md"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    if HOLDERS not in text:
        text = text.rstrip("\n") + f"\n\n{HOLDERS}\n\nWritten by the scripts when a run takes over or releases the lock.\n"
    p.write_text(text.rstrip("\n") + f"\n- {line}\n", encoding="utf-8", newline="\n")


def held_message(reg, d):
    reg = pathlib.Path(reg).resolve()
    root = reg.parent.parent if reg.parent.name == "bfo-work" else None
    release_cmd = (f'python start.py "{root or "<workspace root>"}" --release "{reg}" --words '
                   '"<the person\'s words, word for word>"')
    try:  # the run whose start step began the work in this workspace, as the start step recorded it
        began = json.loads((reg.parent / "run-started.json").read_text(encoding="utf-8")) if root else {}
    except (OSError, ValueError):
        began = {}
    if began.get("run") and began.get("run") == d.get("run"):
        # the lock is held by the run whose start step began this work: most likely this very run, its helper's shell
        # named differently from its session's, kept out of its own register
        return (f"REFUSED: this register ({reg}) is locked by the run whose start step began this work, at "
                f"{began.get('started', 'an unknown time')}, and this script runs under another name. If this script "
                "is part of that same run (its first-look helper, say), the run is kept out of its own register: it "
                "is not another chat. Tell the person so in one plain sentence and ask them to confirm no other chat "
                f"is working on this work; on their yes, run: {release_cmd}, then run this script again. Nothing was "
                "written. Never wait out the lock's age.")
    return (f"REFUSED: another run is writing this register ({reg}): it last wrote here {minutes_since(d)} minute(s) "
            "ago. Two runs writing one register at once overwrite each other's work, so nothing was written. If that "
            "run has stopped (its chat is closed, or it crashed), the person can release it, in their own words: "
            f"{release_cmd}. A lock no run has written for {STALE_MINUTES} minutes is taken over by the next run "
            "that writes.")


NOT_TAKEN = (f"the lock was not taken: nothing names this run ({SESSION} and {TOKEN} are both unset), so a second run "
             "writing this register at the same time is not refused.")
NOT_CHECKED = (f"the lock was not checked: nothing names this run ({SESSION} and {TOKEN} are both unset), so it was "
               "written whichever run holds the lock.")


def record_once(reg, why):
    """`why` in RUN.md's record of the runs that held the register, once: a run with no name writes many times."""
    p = pathlib.Path(reg) / "RUN.md"
    try:
        if why in p.read_text(encoding="utf-8"):
            return
    except OSError:
        return
    record(reg, f"{now()}: {why}")


def hold(reg, take_missing=None):
    """(refusal, note) for the current run writing `reg`. refusal is None when it may write; note says what was done
    (a take-over), or is empty. A missing lock is taken when this kit made the folder, or when `take_missing` is
    True (the start step, on a folder it is starting)."""
    reg = pathlib.Path(reg)
    d = read(reg)
    run = identity()
    if run is None:
        # nothing names this run: it goes on, never refused, and the record says the lock did not guard it
        if d is None and not (reg / LOCK).exists():
            if take_missing or (take_missing is None and made_by_this_kit(reg)):
                record_once(reg, NOT_TAKEN)
        else:
            record_once(reg, NOT_CHECKED)
        return None, ""
    if d is None and not (reg / LOCK).exists():
        if not (take_missing or (take_missing is None and made_by_this_kit(reg))):
            return None, ""
        if create(reg, run):
            return None, ""
        d = read(reg)  # another process took it a moment ago
    if d is None:  # a lock that cannot be read: taken over as stale
        write(reg, run)
        record(reg, f"{now()}: took over a lock that could not be read.")
        return None, "note: took over a lock that could not be read"
    if d["run"] == run:
        if time.time() - float(d.get("touched", 0)) > 60:  # refreshed at most once a minute: a refusal changes nothing
            write(reg, run, d.get("taken"))
        return None, ""
    if not stale(d):
        return held_message(reg, d), ""
    was = minutes_since(d)
    write(reg, run)
    if (read(reg) or {}).get("run") != run:
        return held_message(reg, read(reg) or d), ""
    record(reg, f"{now()}: took over the lock from another run, which had not written here for {was} minutes.")
    return None, f"note: took over the lock from another run, which had not written here for {was} minutes"


def release(reg, words):
    """The person's release of the lock, in their words: the lock is given to the current run, and the words recorded."""
    run = identity()
    if run is None:  # nothing names the run that asked: the lock is removed, and none is taken
        (pathlib.Path(reg) / LOCK).unlink(missing_ok=True)
        record(reg, f'{now()}: released by the person, who said "{words}"; no lock was taken, as nothing names the '
                    "run that asked.")
        return None
    write(pathlib.Path(reg), run)
    record(reg, f'{now()}: released by the person, who said "{words}"; the lock passed to the run that asked.')
    return None


def guard(reg, take_missing=None):
    """For a script about to write `reg`: exit 2 with the refusal when another run holds it; say any take-over."""
    refusal, note = hold(reg, take_missing)
    if refusal:
        print(refusal, file=sys.stderr)
        sys.exit(2)
    if note:
        print(note, file=sys.stderr)
