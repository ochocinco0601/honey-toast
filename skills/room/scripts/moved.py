"""Watch the artifact a finding was about: one line each time it, or HEAD, moves.

The orchestrator arms this in the same turn as it sends findings, so that a
change on disk wakes it whether or not anyone tells it:

  Monitor(timeout_ms: 1800000, description: "findings on <file> and HEAD",
          command: 'python <skill-dir>/scripts/moved.py <file> [<file> ...]')

It watches the working tree as well as HEAD, because a session that edits
without committing has still acted. Detect on the tree; score on the commit --
a tree under active edit has no defined state.

It observes a tree, and a tree has no author. A MOVED line says something in
this folder changed, never who changed it.

Run it from the working session's folder (git commands use the current folder).
Pure Python and git, so it behaves the same from Bash or PowerShell.

  python moved.py <file> [<file> ...] [--poll SECONDS]
  python moved.py <file> --once        print the current fingerprint and exit
"""
import hashlib
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def git(*args):
    try:
        r = subprocess.run(["git"] + list(args), capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except Exception:
        return ""


def digest(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()[:12]
    except OSError:
        return "absent"


def fingerprint(files):
    return (git("rev-parse", "HEAD"),) + tuple(digest(f) for f in files)


def describe(prev, cur, files):
    """What moved between two fingerprints, as one line. '' when nothing did."""
    if prev == cur:
        return ""
    parts = []
    if prev[0] != cur[0]:
        parts.append("HEAD %s -> %s: %s" % (prev[0][:8], cur[0][:8],
                                             git("log", "-1", "--oneline")))
    for f, a, b in zip(files, prev[1:], cur[1:]):
        if a != b:
            stat = git("diff", "--shortstat", "--", f)
            parts.append("%s changed%s" % (f, " (%s vs HEAD)" % stat if stat else ""))
    return "MOVED: " + " | ".join(parts)


def main(argv):
    if not argv or "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return 0 if argv else 2
    poll = 20
    if "--poll" in argv:
        i = argv.index("--poll")
        poll = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    once = "--once" in argv
    files = [a for a in argv if a != "--once"]
    prev = fingerprint(files)
    if once:
        print("HEAD %s  %s" % (prev[0][:8] or "(no git)", "  ".join(
            "%s=%s" % (f, d) for f, d in zip(files, prev[1:]))))
        return 0
    print("ARMED on %s and HEAD %s" % (", ".join(files), prev[0][:8] or "(no git)"), flush=True)
    while True:
        time.sleep(poll)
        cur = fingerprint(files)
        line = describe(prev, cur, files)
        if line:
            print(line, flush=True)
        prev = cur


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
