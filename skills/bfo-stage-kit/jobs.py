"""The job runner of the split run (its file formats: split-run-formats.md).

Its one job: which step of which item runs next, and whether it is done. It knows items, steps, the order of steps,
states and check commands, nothing about maps. The kit supplies the items, steps and checks; any other method can use
it with its own. Python standard library only.

Files, all in the job folder `<reg>/job/` (written only by this script):
  jobs.csv     item,step,state,tries,reason,session,updated   state: to do | running | done | blocked
  lock.json    {"session": <id>, "last": <ISO time>}           the lead session and its last call
  events.log   one line per change, appended
  steps.json   each step's check command and what it waits for
  .busy        held for a moment around each read-modify-write, so parallel calls do not overwrite each other
Settings come from `<reg>/run-settings.json` through settings.py, which holds their defaults: `parallel`,
`lock_stale_minutes`, `on_change` (the command run after a change; the runner has no default of its own for it).

Commands (every one that changes state needs --session):
  jobs.py add <job> --step <step> <item>... --session <id>
      Add (item, step) lines in `to do`. A line that already exists is left as it is.
  jobs.py step <job> <step> --check "<command>" [--after <step>]... [--after-all <step>]... --session <id>
      Declare a step's check and what it waits for: --after, the same item's step done (an item with no line for
      that step does not wait for it); --after-all, that step done on every line that has it (a blocked line makes
      it wait until the line is dealt with). Placeholders in the check: {item} {step} {reg} (the job folder's
      parent) {job}. The check runs with cwd = {reg}.
  jobs.py next <job> --session <id> [--max N]
      Take or refresh the lock; start startable steps, marking them `running`, until N are running (default
      `parallel`); print each newly started one as `item<TAB>step`.
  jobs.py done <job> <item> <step> --session <id>
      Run the step's check. Passes: `done` (exit 0). Fails: back to `to do` with the output's first 300 characters
      in `reason` and tries+1; at the second failure, `blocked` (exit 1). A `done` line is never redone.
  jobs.py block <job> <item> <step> "<reason>" --session <id>
  jobs.py split <job> <item> <new item>... --session <id>
      Replace the item's not-done lines with the new items' lines for the same steps (the item's done lines stay).
  jobs.py status <job>
      Counts per state and step, and every blocked line with its reason. Exit 0 always; needs no lock.

The lock: a call is refused (exit 3) while another session holds a lock fresher than `lock_stale_minutes`. A stale
lock is taken over, printed and logged as `TOOK OVER STALE LOCK from <session>`, and every `running` line goes back
to `to do`: a step left running by a session that ended is started again. The caller notes the takeover in RUN.md.
After every command that changed state, `on_change` runs (placeholders {reg} {job}, cwd = this script's folder); its
failure is logged and never fails the runner. Exit codes: 0 ok, 1 check failed, 2 refused or bad use, 3 locked.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import settings as run_settings  # noqa: E402
import tables  # noqa: E402
import register_layout as layout  # noqa: E402

COLUMNS = layout.JOBS_COLS
STATES = ("to do", "running", "done", "blocked")
REASON_MAX = 300
BUSY_STALE_SECONDS = 120


class Locked(Exception):
    pass


class Refused(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def settings(job):
    """The run's settings, read from the job folder's parent. `on_change` comes from there too: the runner has no
    default of its own for it, and runs nothing when it is empty."""
    return run_settings.load(job.parent)


def atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    for _ in range(50):  # Windows refuses a replace while a reader has the file open
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.1)
    os.replace(tmp, path)


def read_jobs(job):
    return tables.dicts(job / layout.JOBS_FILE, encoding="utf-8")


def write_jobs(job, rows):
    atomic_write(job / layout.JOBS_FILE, tables.text(COLUMNS, rows))


def read_steps(job):
    p = job / layout.STEPS_FILE
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def log(job, session, *fields):
    line = "\t".join([now(), session or "-"] + [str(x).replace("\n", " ") for x in fields])
    with open(job / layout.EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


class Busy:
    """A short mutual exclusion around every read-modify-write of the job folder."""

    def __init__(self, job):
        self.path = job / ".busy"

    def __enter__(self):
        while True:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > BUSY_STALE_SECONDS:
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def take_lock(job, session, s, out):
    """Refuse on a fresh foreign lock; take over a stale one (running lines back to to do); refresh our own."""
    p = job / layout.LOCK_FILE
    took_over = None
    if p.exists():
        lock = json.loads(p.read_text(encoding="utf-8"))
        holder = lock.get("session")
        if holder and holder != session:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(lock["last"])).total_seconds() / 60
            if age < float(s["lock_stale_minutes"]):
                raise Locked(f"locked by session {holder} (last call {lock['last']}, "
                             f"stale after {s['lock_stale_minutes']} minutes)")
            took_over = holder
    if took_over:
        msg = f"TOOK OVER STALE LOCK from {took_over}"
        print(msg, file=out)
        log(job, session, msg)
        rows = read_jobs(job)
        reset = [r for r in rows if r["state"] == "running"]
        for r in reset:
            r.update(state="to do", session=session, updated=now())
            log(job, session, "to do", r["item"], r["step"], f"was running under {took_over}")
        if reset:
            write_jobs(job, rows)
    atomic_write(p, json.dumps({"session": session, "last": now()}))
    return bool(took_over)


def startable(rows, steps):
    by_key = {(r["item"], r["step"]): r for r in rows}
    out = []
    for r in rows:
        if r["state"] != "to do":
            continue
        decl = steps.get(r["step"], {})
        ok = all(by_key.get((r["item"], a), {"state": "done"})["state"] == "done" for a in decl.get("after", []))
        ok = ok and all(x["state"] == "done" for a in decl.get("after_all", []) for x in rows if x["step"] == a)
        if ok:
            out.append(r)
    return out


def fill(cmd, job, item="", step=""):
    """Put values in a command's placeholders. A path with a space is quoted unless the command already quotes it."""
    cmd = cmd.replace("{item}", item).replace("{step}", step)
    for name, path in (("{reg}", str(job.parent)), ("{job}", str(job))):
        quoted = f'"{path}"' if any(c.isspace() for c in path) else path
        cmd = cmd.replace(f'"{name}"', f'"{path}"').replace(name, quoted)
    return cmd


def on_change(job, session, s):
    cmd = s.get("on_change") or ""
    if not cmd:
        return
    try:
        r = subprocess.run(fill(cmd, job), shell=True, cwd=HERE, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            log(job, session, "on_change failed", r.returncode, (r.stdout + r.stderr)[:REASON_MAX])
    except Exception as e:  # never fails the runner
        log(job, session, "on_change failed", repr(e)[:REASON_MAX])


def find(rows, item, step):
    for r in rows:
        if r["item"] == item and r["step"] == step:
            return r
    raise Refused(f"no line for item {item!r} step {step!r}")


# --- commands: each returns (exit code, changed) and runs under Busy with the lock already taken ---------------

def cmd_add(a, job, rows, out):
    have = {(r["item"], r["step"]) for r in rows}
    added = 0
    for item in a.items:
        if (item, a.step) not in have:
            rows.append(dict(item=item, step=a.step, state="to do", tries="0", reason="", session=a.session,
                             updated=now()))
            have.add((item, a.step))
            log(job, a.session, "to do", item, a.step, "added")
            added += 1
    if added:
        write_jobs(job, rows)
    return 0, bool(added)


def cmd_step(a, job, rows, out):
    steps = read_steps(job)
    steps[a.step] = {"check": a.check, "after": a.after or [], "after_all": a.after_all or []}
    atomic_write(job / layout.STEPS_FILE, json.dumps(steps, indent=2))
    log(job, a.session, "step declared", "", a.step, a.check)
    return 0, True


def cmd_next(a, job, rows, out):
    s = settings(job)
    limit = a.max if a.max is not None else int(s["parallel"])
    room = limit - sum(r["state"] == "running" for r in rows)
    started = startable(rows, read_steps(job))[:max(room, 0)]
    for r in started:
        r.update(state="running", session=a.session, updated=now())
        log(job, a.session, "running", r["item"], r["step"])
        print(f"{r['item']}\t{r['step']}", file=out)
    if started:
        write_jobs(job, rows)
    return 0, bool(started)


def cmd_block(a, job, rows, out):
    r = find(rows, a.item, a.step)
    if r["state"] == "done":
        raise Refused(f"{a.item} {a.step} is done; a done line is never changed")
    r.update(state="blocked", reason=a.reason[:REASON_MAX], session=a.session, updated=now())
    log(job, a.session, "blocked", a.item, a.step, a.reason)
    write_jobs(job, rows)
    return 0, True


def cmd_split(a, job, rows, out):
    mine = [r for r in rows if r["item"] == a.item]
    if not mine:
        raise Refused(f"no lines for item {a.item!r}")
    existing = {r["item"] for r in rows}
    clash = [n for n in a.new_items if n in existing]
    if clash:
        raise Refused(f"items already exist: {', '.join(clash)}")
    pending = [r["step"] for r in mine if r["state"] != "done"]
    keep = [r for r in rows if not (r["item"] == a.item and r["state"] != "done")]
    for n in a.new_items:
        for step in pending:
            keep.append(dict(item=n, step=step, state="to do", tries="0", reason="", session=a.session,
                             updated=now()))
    log(job, a.session, "split", a.item, ";".join(pending), "into " + ";".join(a.new_items))
    write_jobs(job, keep)
    return 0, True


def cmd_done(a, job, out):
    """Run the check outside Busy, then apply its result to a fresh read of jobs.csv."""
    s = settings(job)
    with Busy(job):
        take_lock(job, a.session, s, out)
        r = find(read_jobs(job), a.item, a.step)
        if r["state"] == "done":
            print(f"{a.item}\t{a.step}\talready done", file=out)
            return 0
        if r["state"] == "blocked":
            raise Refused(f"{a.item} {a.step} is blocked: {r['reason']}")
        decl = read_steps(job).get(a.step)
        if not decl or not decl.get("check"):
            raise Refused(f"step {a.step!r} has no declared check; declare it with `jobs.py step`")
    res = subprocess.run(fill(decl["check"], job, a.item, a.step), shell=True, cwd=job.parent,
                         capture_output=True, text=True)
    passed = res.returncode == 0
    with Busy(job):
        take_lock(job, a.session, s, out)
        rows = read_jobs(job)
        r = find(rows, a.item, a.step)
        if r["state"] == "done":
            return 0
        if passed:
            r.update(state="done", reason="", session=a.session, updated=now())
            log(job, a.session, "done", a.item, a.step)
            print(f"{a.item}\t{a.step}\tdone", file=out)
        else:
            tries = int(r["tries"] or 0) + 1
            reason = (res.stdout + res.stderr).strip()[:REASON_MAX] or f"check exited {res.returncode}"
            state = "blocked" if tries >= 2 else "to do"
            r.update(state=state, tries=str(tries), reason=reason, session=a.session, updated=now())
            log(job, a.session, state, a.item, a.step, reason)
            print(f"{a.item}\t{a.step}\t{state}\t{reason}", file=out)
        write_jobs(job, rows)
    on_change(job, a.session, s)
    return 0 if passed else 1


def cmd_status(job, out):
    rows = read_jobs(job)
    if not rows:
        print(f"no jobs yet in {job}", file=out)
        return 0
    total = {st: sum(r["state"] == st for r in rows) for st in STATES}
    print("  ".join(f"{st}: {n}" for st, n in total.items()), file=out)
    for step in dict.fromkeys(r["step"] for r in rows):
        counts = {st: sum(r["state"] == st and r["step"] == step for r in rows) for st in STATES}
        print(f"{step}: " + "  ".join(f"{st} {n}" for st, n in counts.items() if n), file=out)
    for r in rows:
        if r["state"] == "blocked":
            print(f"BLOCKED\t{r['item']}\t{r['step']}\t{r['reason']}", file=out)
    lock = job / layout.LOCK_FILE
    if lock.exists():
        print("lock: " + lock.read_text(encoding="utf-8"), file=out)
    return 0


def parser():
    p = argparse.ArgumentParser(prog="jobs.py", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def with_session(sp):
        sp.add_argument("job")
        sp.add_argument("--session", required=True)
        return sp

    sp = with_session(sub.add_parser("add"))
    sp.add_argument("--step", required=True)
    sp.add_argument("items", nargs="+")
    sp = with_session(sub.add_parser("step"))
    sp.add_argument("step")
    sp.add_argument("--check", required=True)
    sp.add_argument("--after", action="append")
    sp.add_argument("--after-all", action="append", dest="after_all")
    sp = with_session(sub.add_parser("next"))
    sp.add_argument("--max", type=int)
    sp = with_session(sub.add_parser("done"))
    sp.add_argument("item")
    sp.add_argument("step")
    sp = with_session(sub.add_parser("block"))
    sp.add_argument("item")
    sp.add_argument("step")
    sp.add_argument("reason")
    sp = with_session(sub.add_parser("split"))
    sp.add_argument("item")
    sp.add_argument("new_items", nargs="+")
    sp = sub.add_parser("status")
    sp.add_argument("job")
    return p


COMMANDS = {"add": cmd_add, "step": cmd_step, "next": cmd_next, "block": cmd_block, "split": cmd_split}


def main(argv=None):
    a = parser().parse_args(argv)
    out = sys.stdout
    job = pathlib.Path(a.job).resolve()
    if a.cmd == "status":
        return cmd_status(job, out)
    job.mkdir(parents=True, exist_ok=True)
    import run_lock  # the register is written by one run at a time
    run_lock.guard(job.parent)
    try:
        if a.cmd == "done":
            return cmd_done(a, job, out)
        s = settings(job)
        with Busy(job):
            took_over = take_lock(job, a.session, s, out)
            code, changed = COMMANDS[a.cmd](a, job, read_jobs(job), out)
        if changed or took_over:
            on_change(job, a.session, s)
        return code
    except Locked as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
