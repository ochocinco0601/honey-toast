"""Tests for watch.py -- the thing that makes a watcher keep watching.

Plain Python:  python test_watch.py

A session told to watch another is alive only during its own turn: it looks
once, reports, and stops. A watch that fires only on activity is silent on
silence and cannot see a pause, which is the state a watcher most needs to see
(the supervisor-without-a-heartbeat problem: Erlang/OTP supervision, watchdog
timers and level-triggered reconcile loops all exist because of it).

pulse() is the whole judgment, isolated so it is testable without a live
session, a clock or a transcript on disk.
"""
import importlib.util
import pathlib
import sys

spec = importlib.util.spec_from_file_location(
    "watch", pathlib.Path(__file__).with_name("watch.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

fails = []


def check(label, got, want):
    if got != want:
        fails.append("%s\n   got:  %s\n   want: %s" % (label, got, want))


def check_in(label, needle, hay):
    if needle not in hay:
        fails.append("%s\n   looked for: %s\n   in:         %s" % (label, needle, hay))


def edit(path):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Edit", "input": {"file_path": path}}]}}


def shell(cmd):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}]}}


def typed(text, **extra):
    r = {"type": "user", "message": {"content": text}}
    r.update(extra)
    return r


def tool_result():
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


T0, MIN = 1000.0, 60.0
P = m.pulse
N = m.new_state

# ---------------------------------------------------------------- activity
lines, _ = P(N(), [edit("docs/register.csv")], T0, True)
check("an edit wakes the watcher", len(lines), 1)
check_in("and names the file", "register.csv", lines[0])
check("a commit wakes it", len(P(N(), [shell("git commit -m 'x'")], T0, True)[0]), 1)
check("a push wakes it", len(P(N(), [shell("git push origin main")], T0, True)[0]), 1)
check("a gh call wakes it", len(P(N(), [shell("gh issue create --title x")], T0, True)[0]), 1)
check("an ordinary read does not", P(N(), [shell("sed -n '1,40p' README.md")], T0, True)[0], [])
check("a tool result is not a turn", P(N(), [tool_result()], T0, True)[0], [])
check("the user's own turn wakes it", len(P(N(), [typed("stop doing that")], T0, True)[0]), 1)

# Harness-written records in the user's lane are not the user. A shape rule,
# not a roster: a roster fails open on the next kind of record invented.
for label, text in (("hook context", "<user-prompt-submit-hook>x</user-prompt-submit-hook>"),
                    ("a task notification", "<task-notification>done</task-notification>"),
                    ("an opened file", "<ide_opened_file>x.py</ide_opened_file>"),
                    ("a tag nobody has seen yet", "<some-new-tag>x</some-new-tag>")):
    check("%s is not a turn" % label, P(N(), [typed(text)], T0, True)[0], [])
check("a tag inside a sentence is still the user",
      len(P(N(), [typed("fix the <div> on that page")], T0, True)[0]), 1)

# A message from another session arrives as ordinary prose in the user's lane.
# Reporting it as the user is a wrong finding, not noise. The record says which.
peer = typed("Another Claude session sent a message:\nhi", isMeta=True,
             origin={"kind": "peer", "name": "worker"})
check("a peer's message is not the user", P(N(), [peer], T0, True)[0], [])
check("a record marked human is the user",
      len(P(N(), [typed("stop", origin={"kind": "human"})], T0, True)[0]), 1)
check("no origin field falls back to the text rule",
      len(P(N(), [typed("no origin at all")], T0, True)[0]), 1)

# A message typed while a turn runs is an attachment record, not a user one.
mid = {"type": "attachment", "attachment": {"origin": {"kind": "human"}, "prompt": "wait, not that"}}
lines, _ = P(N(), [mid], T0, True)
check("a mid-turn message wakes it", len(lines), 1)
check_in("and is labelled as mid-turn", "USER-MIDTURN", lines[0] if lines else "")

# ------------------------------------------------------------------- pause
st = N()
_, st = P(st, [edit("a.py")], T0, True)
lines, st = P(st, [], T0 + 2 * MIN, True)
check("two minutes of quiet is not a pause", lines, [])
lines, st = P(st, [], T0 + 6 * MIN, True)
check("the first step of quiet wakes it once", len(lines), 1)
check_in("and says how long", "6m", lines[0])
check_in("and does not call a live session dead", "live", lines[0].lower())
lines, st = P(st, [], T0 + 7 * MIN, True)
check("the same step does not wake it again", lines, [])
lines, st = P(st, [], T0 + 16 * MIN, True)
check("a longer quiet is a new step", len(lines), 1)

# ------------------------------------------------------------------ resume
lines, st = P(st, [edit("b.py")], T0 + 18 * MIN, True)
check("work after a pause wakes it with two lines", len(lines), 2)
check_in("and says the session came back", "resumed", " ".join(lines).lower())
lines, st = P(st, [], T0 + 19 * MIN, True)
check("the pause steps are re-armed, so no stale step fires", lines, [])
lines, st = P(st, [], T0 + 25 * MIN, True)
check("the first step fires again after the resume", len(lines), 1)

# ------------------------------------------------------------------- ended
st2 = N()
_, st2 = P(st2, [edit("a.py")], T0, True)
lines, st2 = P(st2, [], T0 + MIN, False)
check("a session whose pipe is gone wakes it", len(lines), 1)
check_in("and is reported as ended, not quiet", "ended", lines[0].lower())
check("and only once", P(st2, [], T0 + 2 * MIN, False)[0], [])

# ------------------------------------------------------- where to start, self
check("a stream starts at the end", m.start_offset(4096, once=False), 4096)
check("a single pass starts at the beginning", m.start_offset(4096, once=True), 0)
check("a session cannot watch itself", m.judging_itself("abc123", "abc123"), True)
check("watching another is allowed", m.judging_itself("abc123", "def456"), False)
check("an unknown own id does not lock the watch out", m.judging_itself("abc123", None), False)

if fails:
    print("FAIL (%d)\n\n%s" % (len(fails), "\n\n".join(fails)))
    sys.exit(1)
print("ok - watch pulse: activity, pause steps, resume, ended, self-watch")
