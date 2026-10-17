"""Resolve a session to the name SendMessage accepts.

SendMessage and ListAgents address sessions by NAME and show no session id.
Transcripts, the extension's session list and CLAUDE_CODE_SESSION_ID all use
the id. This bridges the two, from the live registry Claude Code writes at
<config>/sessions/*.json (<config> is $CLAUDE_CONFIG_DIR or ~/.claude).

  python whois.py                  every live session for this repository
  python whois.py <id-or-prefix>   print the current name for one session
  python whois.py --here <own-id>  sessions sharing THIS working folder, minus you
  python whois.py --all            every session on the machine

The name is not stable for the life of a session; the id is. Resolve the id
once, and re-resolve the name in the same turn as every send.
"""
import glob
import json
import os
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def config_root():
    c = os.environ.get("CLAUDE_CONFIG_DIR")
    return os.path.expanduser(c) if c else os.path.join(os.path.expanduser("~"), ".claude")


def last_write(session_id):
    for d in glob.glob(os.path.join(config_root(), "projects", "*")):
        p = os.path.join(d, session_id + ".jsonl")
        if os.path.exists(p):
            return time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(p)))
    return "-"


def alive(d):
    """Whether the session behind a registry entry still exists.

    Its messaging pipe or socket, which the operating system removes when the
    session ends. Not the pid: registry entries outlive their sessions, and a
    dead entry's pid is routinely reused by an unrelated live process, so a pid
    check reports a dead session as working.
    """
    p = d.get("messagingSocketPath")
    return bool(p) and os.path.exists(p)


def load():
    out = []
    for p in glob.glob(os.path.join(config_root(), "sessions", "*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        if not d.get("sessionId") or not d.get("name"):
            continue
        d["alive"] = alive(d)
        d["lastWrite"] = last_write(d["sessionId"])
        out.append(d)
    return sorted(out, key=lambda r: r["lastWrite"], reverse=True)


def norm(p):
    return os.path.normcase(os.path.normpath(p or ""))


def repo_paths():
    """Every working folder of this repository: main checkout and worktrees."""
    try:
        out = subprocess.run(["git", "worktree", "list", "--porcelain"],
                             capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return []
    return [ln[len("worktree "):].strip() for ln in out.splitlines()
            if ln.startswith("worktree ")]


def scope(rows, here, paths):
    """Sessions in any folder of this repository. Other projects are dropped."""
    inside = {norm(p) for p in paths} or {norm(here)}
    return [r for r in rows if norm(r.get("cwd")) in inside]


def cohabitants(rows, here, me=None, live_only=True):
    """Sessions sharing one working tree -- the candidate set for a change on disk.

    Not the same question as scope(), which spans every checkout of the repo.
    Files do not cross folders, so only a session in THIS folder can have made
    the edit sitting in THIS tree.

    This narrows candidates. It cannot name an author: sessions usually commit
    under one shared git identity, and `git status` / `git diff` carry no
    identity at all. Narrow, then ask.

    live_only=False includes ended sessions, which cannot be messaged but may
    have authored a landed commit before they ended.
    """
    out = [r for r in rows if norm(r.get("cwd")) == norm(here)]
    if live_only:
        out = [r for r in out if r.get("alive")]
    if me:
        key = me.lower()
        out = [r for r in out if not (r["sessionId"].lower().startswith(key)
                                      or key == r.get("name", "").lower())]
    return out


def main(argv):
    if "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return 0
    flags = {"--all", "--here"}
    args = [a for a in argv if a not in flags]
    everything = load()
    rows = everything
    if "--all" not in argv:
        scoped = scope(rows, os.getcwd(), repo_paths())
        if scoped:
            rows = scoped

    if "--here" in argv:
        me = args[0] if args else os.environ.get("CLAUDE_CODE_SESSION_ID")
        here = os.getcwd()
        others = cohabitants(everything, here, me=me)
        print("%d live session(s) share %s%s" % (
            len(others), here, " besides %s" % me[:8] if me else ""))
        for r in others:
            print("  %-38s %-24s last wrote %s" % (r["sessionId"], r["name"], r["lastWrite"]))
        print("\nThis is a CANDIDATE SET, not an author. No artifact names the session\n"
              "behind a change. If more than one row is listed, say so when you route\n"
              "and send to each of them with the STOP opener. Narrow, then ask.")
        return 0

    if args:
        needle = args[0].lower()

        def match(rs):
            return [r for r in rs if r["sessionId"].lower().startswith(needle)
                    or needle == r["name"].lower()]
        hit = match(rows) or match(everything)
        if not hit:
            print("NO MATCH for %r. Not a session on this machine, or the registry is "
                  "stale. Check ListAgents." % args[0])
            return 1
        for r in hit:
            print("%s%s" % (r["name"], "" if r["alive"] else "   (GONE - cannot be messaged)"))
        return 0

    print("%-38s %-24s %-12s %-5s %-9s %s" % (
        "SESSION ID", "SENDMESSAGE NAME", "KIND", "LIVE", "LASTWRITE", "CWD"))
    for r in rows:
        print("%-38s %-24s %-12s %-5s %-9s %s" % (
            r["sessionId"], r["name"], r.get("kind", "?"),
            "yes" if r["alive"] else "GONE", r["lastWrite"], r.get("cwd", "")))
    print("\nLIVE is the liveness signal: the session's messaging pipe, which disappears\n"
          "when it ends. LASTWRITE is not -- a transcript untouched for ten minutes is a\n"
          "session thinking or a session that ended, and no threshold tells them apart.\n"
          "Cross-check any name against ListAgents before sending to it.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
