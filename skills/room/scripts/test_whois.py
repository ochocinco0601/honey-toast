"""Tests for whois.py -- scoping, liveness, and who shares a working tree.

Plain Python:  python test_whois.py

One repository is often checked out in several folders at once (a main folder
and worktrees). scope() keeps sessions in ANY folder of the repository;
cohabitants() keeps only those in THIS folder, because only a session here can
have made the uncommitted edit sitting here. Neither can name an author.
"""
import importlib.util
import os
import pathlib
import sys

spec = importlib.util.spec_from_file_location(
    "whois", pathlib.Path(__file__).with_name("whois.py"))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

ROOT = os.path.abspath(os.sep)
MAIN = os.path.join(ROOT, "work", "project")
TREE = os.path.join(ROOT, "work", "project-feature")
OTHER = os.path.join(ROOT, "work", "unrelated")

fails = []


def check(label, got, want):
    if got != want:
        fails.append("%s\n   got:  %s\n   want: %s" % (label, got, want))


def ids(rows):
    return sorted(r["sessionId"] for r in rows)


ROWS = [{"sessionId": "aaa", "name": "project-01", "cwd": MAIN},
        {"sessionId": "bbb", "name": "project-02", "cwd": TREE},
        {"sessionId": "ccc", "name": "unrelated-01", "cwd": OTHER}]

# --- scope --------------------------------------------------------------
check("sees every folder of this repository", ids(w.scope(ROWS, MAIN, [MAIN, TREE])), ["aaa", "bbb"])
check("the answer does not depend on which folder asks", ids(w.scope(ROWS, TREE, [MAIN, TREE])), ["aaa", "bbb"])
check("an unrelated project is excluded", "ccc" in ids(w.scope(ROWS, MAIN, [MAIN, TREE])), False)
check("no git: fall back to the caller's own folder", ids(w.scope(ROWS, TREE, [])), ["bbb"])
if os.name == "nt":
    # git reports forward slashes; os.getcwd() reports backslashes and any case.
    check("separator style does not decide membership",
          ids(w.scope(ROWS, MAIN, [MAIN.replace("\\", "/"), TREE.replace("\\", "/")])), ["aaa", "bbb"])

# --- liveness -----------------------------------------------------------
# The messaging pipe, never the pid: an ended session's pid is routinely reused
# by an unrelated live process, so a pid check reports the dead as working.
HERE = pathlib.Path(__file__).parent
check("a pipe that exists means live", w.alive({"messagingSocketPath": str(HERE / "whois.py")}), True)
check("a pipe that is gone means ended", w.alive({"messagingSocketPath": str(HERE / "no-such-pipe")}), False)
check("no pipe recorded is not alive", w.alive({"pid": 4242}), False)
check("an empty pipe path is not alive", w.alive({"messagingSocketPath": ""}), False)

# --- cohabitants ----------------------------------------------------------
LIVE_A = {"sessionId": "aaa", "name": "project-01", "cwd": MAIN, "alive": True}
LIVE_B = {"sessionId": "bbb", "name": "project-02", "cwd": MAIN, "alive": True}
LIVE_TREE = {"sessionId": "ccc", "name": "project-03", "cwd": TREE, "alive": True}
DEAD_A = {"sessionId": "ddd", "name": "project-04", "cwd": MAIN, "alive": False}
CO = [LIVE_A, LIVE_B, LIVE_TREE, DEAD_A]

check("every live session in the folder is a candidate", ids(w.cohabitants(CO, MAIN)), ["aaa", "bbb"])
check("a sibling worktree is not a cohabitant", "ccc" in ids(w.cohabitants(CO, MAIN)), False)
check("the caller is excluded by id", ids(w.cohabitants(CO, MAIN, me="aaa")), ["bbb"])
check("or by id prefix", ids(w.cohabitants(CO, MAIN, me="aa")), ["bbb"])
check("or by its exact name", ids(w.cohabitants(CO, MAIN, me="project-01")), ["bbb"])
check("an ended session is not a routing candidate", "ddd" in ids(w.cohabitants(CO, MAIN)), False)
check("but is an authorship candidate", ids(w.cohabitants(CO, MAIN, live_only=False)), ["aaa", "bbb", "ddd"])
check("one other session returns exactly it", ids(w.cohabitants([LIVE_A, LIVE_TREE], MAIN)), ["aaa"])
check("an empty folder returns nothing rather than failing", ids(w.cohabitants([LIVE_TREE], MAIN)), [])
if os.name == "nt":
    check("separator and case do not decide cohabitation",
          ids(w.cohabitants(CO, MAIN.replace("\\", "/").upper())), ["aaa", "bbb"])

if fails:
    print("FAIL (%d)\n\n%s" % (len(fails), "\n\n".join(fails)))
    sys.exit(1)
print("ok - whois scope + liveness + cohabitants")
