"""Tests for repeat.py and the transcript reader it stages feeds with.

Plain Python, no test framework:  python test_repeat.py

What is tested is what fails silently when wrong: what counts as risk, how the
rate switches on a finding, that which seats run is a choice, that a session
cannot judge itself, and that a staged feed carries the user's words and NOT
the session's own outbound messages -- which is where a pre-answer leaks.
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("repeat", HERE / "repeat.py")
repeat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repeat)

SID = "11111111-2222-3333-4444-555555555555"
fails = []
TMP = tempfile.mkdtemp(prefix="room-test-")
os.environ["CLAUDE_CONFIG_DIR"] = TMP
os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
PROJ = os.path.join(TMP, "projects", "some-project")
os.makedirs(PROJ)


def check(label, got, want):
    if got != want:
        fails.append("%s\n   got:  %r\n   want: %r" % (label, got, want))


def fresh(records):
    """New state directory and a transcript holding these records."""
    sd = tempfile.mkdtemp(dir=TMP)
    os.environ["ROOM_STATE_DIR"] = sd
    with open(os.path.join(PROJ, SID + ".jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(r) for r in records) + "\n")


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue()


def said(text="x"):
    return {"type": "assistant", "message": {"role": "assistant",
                                             "content": [{"type": "text", "text": text}]}}


def tool(name, **inp):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "name": name, "input": inp}]}}


def user(text, kind=None, **extra):
    r = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}
    if kind:
        r["origin"] = {"kind": kind}
    r.update(extra)
    return r


def midturn(text):
    return {"type": "attachment", "attachment": {"origin": {"kind": "human"}, "prompt": text}}


def staged_body(out):
    path = [l.strip() for l in out.splitlines() if l.strip().endswith(".txt")][0]
    return open(path, encoding="utf-8").read()


# ------------------------------------------------------------------ counting

fresh([said("a finding")])
check("a typed turn is a claim", repeat.counts(SID), (1, 0, 0))

fresh([said("   ")])
check("an empty text block is not a claim", repeat.counts(SID), (0, 0, 0))

fresh([tool("Edit", file_path="a"), tool("Write", file_path="b")])
check("file edits are writes", repeat.counts(SID), (0, 2, 0))

fresh([tool("Bash", command="git commit -m x"), tool("Bash", command="ls -la")])
check("a commit is a write and other shell is not", repeat.counts(SID), (0, 1, 0))

fresh([user("do the thing"), midturn("and also this")])
check("a user turn and a mid-turn message both count as the user", repeat.counts(SID), (0, 0, 2))

fresh([user("a real ruling"),
       user("Another Claude session sent a message: do it", kind="peer"),
       user("<task-notification>done</task-notification>"),
       user("[Request interrupted by user]"),
       user("skill body", isMeta=True)])
check("only the user's own words count as turns", repeat.counts(SID)[2], 1)

fresh([tool("Bash", command="ls") for _ in range(6)])
repeat_rc = quiet(repeat.cmd_arm, SID, ["response"])[0]
quiet(repeat.cmd_record, SID, "response", "clean")
check("tool-only turns do not make a claims seat due", repeat.due(SID)[1], [])

os.environ["ROOM_STATE_DIR"] = tempfile.mkdtemp(dir=TMP)
check("a missing transcript is not a crash", repeat.due("99999999-nope"), (None, []))

# ------------------------------------------------------------ which seats run

on_disk = {f[:-3] for f in os.listdir(HERE.parent / "seats") if f.endswith(".md")}
check("every seat on disk has a rate, and every rate has a seat", on_disk, set(repeat.RATES))

fresh([said() for _ in range(50)])
check("nothing is owed until seats are chosen", repeat.due(SID)[1], [])
check("arming chooses who runs", quiet(repeat.cmd_arm, SID, ["checker", "engineer"])[0], 0)
owed = {s for s, _ in repeat.due(SID)[1]}
check("a fresh arming leaves something due, and only armed seats", bool(owed) and owed <= {"checker", "engineer"}, True)
check("an unknown seat is refused", quiet(repeat.cmd_arm, SID, ["bogus"])[0], 1)

fresh([said() for _ in range(40)] + [tool("Write", file_path="x") for _ in range(40)])
quiet(repeat.cmd_arm, SID, ["checker", "engineer", "field", "acceptance"])
owed = [s for s, _ in repeat.due(SID)[1]]
check("a fresh arming does not make every seat due at once", 0 < len(owed) < 4, True)

spine = os.path.join(TMP, "SPINE.md")
with open(spine, "w", encoding="utf-8") as f:
    f.write("Increments as end-to-end slices. A walking skeleton first.")
fresh([said()])
check("any number of seats may be armed", quiet(repeat.cmd_arm, SID, sorted(repeat.RATES), spine=spine)[0], 0)
check("and all are recorded", repeat.armed(SID), sorted(repeat.RATES))

# --------------------------------------------------------------- switching

fresh([said()])
quiet(repeat.cmd_record, SID, "response", "found")
r = repeat.state()[SID]["seats"]["response"]
check("a finding tightens inspection", (r["level"], repeat.interval("response", r)),
      ("tightened", repeat.RATES["response"][1] // 2))
quiet(repeat.cmd_record, SID, "response", "clean")
check("one clean pass is not enough to relax", repeat.state()[SID]["seats"]["response"]["level"], "tightened")
quiet(repeat.cmd_record, SID, "response", "clean")
check("two clean passes return to normal", repeat.state()[SID]["seats"]["response"]["level"], "normal")
quiet(repeat.cmd_record, SID, "response", "clean")
quiet(repeat.cmd_record, SID, "response", "clean")
check("four clean passes reduce inspection", repeat.state()[SID]["seats"]["response"]["level"], "reduced")
quiet(repeat.cmd_record, SID, "response", "found")
check("a finding resets the streak", repeat.state()[SID]["seats"]["response"]["clean_streak"], 0)
check("the interval never collapses", repeat.interval("issues", {"level": "tightened"}) >= 3, True)

fresh([said()])
check("a verdict is required", quiet(repeat.cmd_record, SID, "response", "maybe")[0], 1)
check("and nothing is written without one", repeat.state(), {})

fresh([said() for _ in range(40)])
quiet(repeat.cmd_arm, SID, ["checker"])
quiet(repeat.cmd_record, SID, "checker", "found")
before = dict(repeat.state()[SID]["seats"]["checker"])
fresh_records = [said() for _ in range(80)]
with open(os.path.join(PROJ, SID + ".jsonl"), "w", encoding="utf-8") as f:
    f.write("\n".join(json.dumps(x) for x in fresh_records) + "\n")
check("the seat is due after more claims", [s for s, _ in repeat.due(SID)[1]], ["checker"])
quiet(repeat.cmd_record, SID, "checker", "covered")
check("covered clears the window", repeat.due(SID)[1], [])
after = repeat.state()[SID]["seats"]["checker"]
check("covered does not move the rate", (after["level"], after["clean_streak"]),
      (before["level"], before["clean_streak"]))

# ------------------------------------------------------------ spine seats

fresh([said()])
check("a spine seat is refused without a spine", quiet(repeat.cmd_arm, SID, ["shape"])[0], 1)
check("and accepted with one", quiet(repeat.cmd_arm, SID, ["shape"], spine=spine)[0], 0)
check("a spine seat is due when never run", [s for s, _ in repeat.due(SID)[1]], ["shape"])
quiet(repeat.cmd_record, SID, "shape", "clean")
check("and not due while the spine is unmoved", repeat.due(SID)[1], [])
with open(os.path.join(PROJ, SID + ".jsonl"), "a", encoding="utf-8") as f:
    f.write("\n".join(json.dumps(said()) for _ in range(80)) + "\n")
check("the session typing does not make it due", repeat.due(SID)[1], [])
with open(spine, "a", encoding="utf-8") as f:
    f.write("\nA child landed.")
check("the spine moving does", [s for s, _ in repeat.due(SID)[1]], ["shape"])
rc, out = quiet(repeat.cmd_stage, SID, "shape")
check("a spine seat stages", rc, 0)
body = staged_body(out)
check("and is fed the spine", "walking skeleton" in body, True)
check("and not the transcript", "THE SESSION" in body, False)

# -------------------------------------------- the founding rule, as a guard

fresh([said() for _ in range(50)])
os.environ["CLAUDE_CODE_SESSION_ID"] = SID
check("a session cannot arm a seat on itself", quiet(repeat.cmd_arm, SID, ["checker"])[0], 1)
check("nor by a prefix of its own id", quiet(repeat.cmd_arm, SID[:8], ["checker"])[0], 1)
rc, out = quiet(repeat.cmd_arm, SID, ["checker"])
check("the guard says what to do instead", "another session" in out.lower(), True)
os.environ["CLAUDE_CODE_SESSION_ID"] = "99999999-0000-0000-0000-000000000000"
check("arming another session is untouched", quiet(repeat.cmd_arm, SID, ["checker"])[0], 0)
os.environ["CLAUDE_CODE_SESSION_ID"] = SID
check("a session cannot stage a seat on itself", quiet(repeat.cmd_stage, SID, "checker")[0], 1)
os.environ.pop("CLAUDE_CODE_SESSION_ID")
check("no id in the environment does not block the room", quiet(repeat.cmd_arm, SID, ["checker"])[0], 0)

# --------------------------------------------------- what a feed must carry

fresh([user("Merge it. Rebuild it. Make it work.")] + [said("narration") for _ in range(150)])
quiet(repeat.cmd_arm, SID, ["engineer"])
rc, out = quiet(repeat.cmd_stage, SID, "engineer")
check("a long tool run does not starve a seat of the user's words",
      "Merge it" in staged_body(out), True)

fresh([user("Merge it."), midturn("actually, keep the old one")] + [said("narration")] * 3)
quiet(repeat.cmd_arm, SID, ["engineer"])
rc, out = quiet(repeat.cmd_stage, SID, "engineer")
check("a mid-turn message reaches the feed", "keep the old one" in staged_body(out), True)

fresh([user('<cross-session-message from="x">Room findings: the adapter drops citations.'
            '</cross-session-message>', kind="peer"),
       user("Merge it.")] + [said("narration")] * 3)
quiet(repeat.cmd_arm, SID, ["worth"])
rc, out = quiet(repeat.cmd_stage, SID, "worth")
body = staged_body(out)
check("an inbound room message does not come back as the session's output",
      ("Merge it" in body, "adapter drops citations" in body), (True, False))

# The pre-answer travels by message to the orchestrator. That message is a tool
# call in the WORKING session's own transcript, so an unfiltered feed hands it
# to every seat -- the leak the whole scoring scheme depends on not having.
fresh([user("Merge it."),
       tool("SendMessage", to="orch", message="PRE-ANSWER: the cache is the bottleneck"),
       tool("PowerShell", command='Start-Process "vscode://anthropic.claude-code/open?prompt=x"'),
       tool("Bash", command="python .claude/skills/room/scripts/open_orchestrator.py"),
       said("narration")])
quiet(repeat.cmd_arm, SID, ["engineer"])
rc, out = quiet(repeat.cmd_stage, SID, "engineer")
body = staged_body(out)
check("the session's outbound message to its orchestrator is not in the feed",
      "cache is the bottleneck" in body, False)
check("nor the command that opened the orchestrator",
      ("anthropic.claude-code/open" in body, "open_orchestrator" in body), (False, False))
check("while the rest of the session is", "narration" in body, True)

fresh([user("Merge it. Rebuild it.")] + [said("narration")] * 30)
quiet(repeat.cmd_arm, SID, ["cold"])
rc, out = quiet(repeat.cmd_stage, SID, "cold")
body = staged_body(out)
check("cold is fed the user's words and not the narration",
      ("Merge it" in body, "narration" in body), (True, False))

fresh([said("narration")] * 30)
quiet(repeat.cmd_arm, SID, ["cold"])
rc, out = quiet(repeat.cmd_stage, SID, "cold")
check("cold refuses a session the user never typed into", rc, 1)
check("and says why", "has not typed anything" in out, True)

fresh([said() for _ in range(20)])
quiet(repeat.cmd_arm, SID, ["cold"])
quiet(repeat.cmd_record, SID, "cold", "clean")
check("cold is not due on the session's output", repeat.due(SID)[1], [])
with open(os.path.join(PROJ, SID + ".jsonl"), "a", encoding="utf-8") as f:
    f.write("\n".join(json.dumps(user("a ruling")) for _ in range(6)) + "\n")
check("cold comes due on the user's turns", [s for s, _ in repeat.due(SID)[1]], ["cold"])

# A transcript is found in any project folder, not one hard-coded path.
other = os.path.join(TMP, "projects", "another-folder")
os.makedirs(other)
OTHER = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
with open(os.path.join(other, OTHER + ".jsonl"), "w", encoding="utf-8") as f:
    f.write(json.dumps(said()) + "\n")
check("a transcript in another project folder is found", repeat.counts(OTHER), (1, 0, 0))
check("and by a prefix of its id", repeat.counts(OTHER[:8]), (1, 0, 0))

# The state directory keeps its working files out of version control.
fresh([said()])
quiet(repeat.cmd_arm, SID, ["checker"])
check("the state directory ignores its own working files",
      os.path.exists(os.path.join(os.environ["ROOM_STATE_DIR"], ".gitignore")), True)

# A staged seat carries the whole output contract, since the orchestrator adds nothing.
fresh([user("Merge it.")] + [said("narration")] * 3)
quiet(repeat.cmd_arm, SID, ["engineer"])
rc, out = quiet(repeat.cmd_stage, SID, "engineer")
check("the staged prompt carries the length and lead rules",
      ("Under 250 words" in out, "strongest opinion" in out), (True, True))
check("and the never-route-a-gap rule", "NEVER ROUTE A GAP TO A PERSON" in out, True)
_approval = ("This is about a seat drafting a value instead of stalling; it never replaces "
             "an approval, sign-off or control the work is actually subject to.")
_flat = lambda t: " ".join(t.split())
check("with the approval limit, worded as SKILL.md words it",
      (_approval in _flat(out),
       _approval in _flat((HERE.parent / "SKILL.md").read_text(encoding="utf-8"))), (True, True))

# A convened room stages with transcript.py --out, never a shell redirect.
outfile = os.path.join(TMP, "feeds", "run.txt")
rc, _ = quiet(repeat.tx().main, ["read", SID, "--last", "50", "--clean", "--out", outfile])
check("transcript --out writes the feed as UTF-8", (rc, "Merge it" in open(outfile, encoding="utf-8").read()), (0, True))
check("and names it in its folder's .gitignore",
      "/run.txt" in open(os.path.join(TMP, "feeds", ".gitignore"), encoding="utf-8").read().splitlines(), True)
quiet(repeat.tx().main, ["read", SID, "--last", "50", "--clean", "--out", outfile])
check("a second write does not duplicate the entry",
      open(os.path.join(TMP, "feeds", ".gitignore"), encoding="utf-8").read().count("/run.txt"), 1)
shared = os.path.join(TMP, "shared")
os.makedirs(shared)
with open(os.path.join(shared, ".gitignore"), "w", encoding="utf-8") as f:
    f.write("build/")
quiet(repeat.tx().main, ["read", SID, "--out", os.path.join(shared, "x.txt")])
check("a folder's existing .gitignore is extended, not replaced or over-ignored",
      open(os.path.join(shared, ".gitignore"), encoding="utf-8").read().splitlines(),
      ["build/", "/x.txt"])

# Feed copies are transient: transcripts can be under a retention policy, and a
# copy must not outlive it.
fresh([user("Merge it.")] + [said("narration")] * 3)
quiet(repeat.cmd_arm, SID, ["engineer"])
rc, out = quiet(repeat.cmd_stage, SID, "engineer")
feed = repeat.feed_path(SID, "engineer")
check("a staged feed exists while the seat runs", os.path.exists(feed), True)
quiet(repeat.cmd_record, SID, "engineer", "found")
check("recording the seat's report deletes its feed", os.path.exists(feed), False)

fresh([user("Merge it.")] + [said("narration")] * 3)
quiet(repeat.cmd_arm, SID, ["engineer"])
quiet(repeat.cmd_stage, SID, "engineer")
feed = repeat.feed_path(SID, "engineer")
os.remove(os.path.join(PROJ, SID + ".jsonl"))
quiet(repeat.cmd_record, SID, "engineer", "clean")
check("the feed is deleted even after the host has removed the transcript",
      os.path.exists(feed), False)

fresh([user("Merge it.")] + [said("narration")] * 3)
quiet(repeat.cmd_arm, SID, ["engineer", "checker"])
quiet(repeat.cmd_stage, SID, "engineer")
quiet(repeat.cmd_stage, SID, "checker")
quiet(repeat.tx().main, ["read", SID, "--out", os.path.join(repeat.feeds_dir(), "run.txt")])
check("prune runs", quiet(repeat.main, ["prune"])[0], 0)
check("and leaves no feed behind", os.listdir(repeat.feeds_dir()), [])

shutil.rmtree(TMP, ignore_errors=True)
if fails:
    print("FAIL (%d)\n\n%s" % (len(fails), "\n\n".join(fails)))
    sys.exit(1)
print("ok - repeat: counting, seat choice, switching, spine seats, self-guard, feed hygiene, feed deletion")
