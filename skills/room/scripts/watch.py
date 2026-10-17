"""Keep watching another session -- activity, silence, and the end.

A session is only alive during its own turn. Told to watch another session, it
reads the transcript once, says something true, ends the turn, and is dormant
until something wakes it. This is the thing that wakes it:

  Monitor(timeout_ms: 1800000, description: "watching <name>",
          command: 'python <skill-dir>/scripts/watch.py <session-id>')

Every line this prints is one Monitor event, and every event wakes the watcher.
Between lines it costs nothing. Do not poll it and do not loop in your own
context.

RE-ARM AT EVERY EXPIRY. A Monitor is killed after thirty minutes at the outside
and sends one notice, which is itself a wake, so re-arming costs one call. A
watcher that armed once and believes it is still watching has been blind since,
and cannot tell: an unarmed watch and a quiet subject look the same. There is no
"persistent" option; a parameter that sounds like one is ignored, not refused.

A running watch holds the code it started with. After changing this file, stop
the Monitor (TaskStop) and arm it again.

What it reports, and what a seat rate cannot: that work happened (edits,
history-changing git commands, gh calls, messages to other sessions, the user's
own turns including mid-turn ones, context compaction); that none has happened
for a while (5, 15, 30, 60, 120, 240 minutes); and that the session has ended.
A pause is never called a death: the messaging pipe answers liveness, so a
QUIET line says the session is still live.

  python watch.py <session-id|prefix|name>          stream until the session ends
  python watch.py <session-id> --once               one pass from the start of
                                                    the transcript, to check the filter
"""
import importlib.util
import os
import pathlib
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

POLL = 30
PAUSE_STEPS = (5, 15, 30, 60, 120, 240)

_mods = {}


def mod(name):
    if name not in _mods:
        spec = importlib.util.spec_from_file_location(
            name, pathlib.Path(__file__).with_name(name + ".py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _mods[name] = m
    return _mods[name]


def judging_itself(target_id, own_id):
    """A session pointed at itself. Unknown own id never locks the watch out."""
    if not own_id or not target_id:
        return False
    return target_id.startswith(own_id) or own_id.startswith(target_id)


def new_state():
    return {"last": None, "fired": (), "paused": False, "ended": False}


def _quiet(st, now):
    return 0.0 if st["last"] is None else (now - st["last"]) / 60.0


def pulse(state, records, now, alive):
    """Lines worth waking a watcher for, and the state to carry forward.

    Pure, so the whole judgment is testable without a clock, a live session or a
    transcript on disk. The loop in main() is a thin shell around it.
    """
    st = dict(state)
    st["fired"] = tuple(state["fired"])
    lines = []
    for rec in records:
        got = mod("transcript").classify(rec)
        if not got:
            continue
        if st["paused"]:
            lines.append("RESUMED after %dm quiet" % round(_quiet(st, now)))
            st["paused"], st["fired"] = False, ()
        lines.append("%s %s" % got)
        st["last"] = now
    if st["last"] is None:
        st["last"] = now
    if not alive:
        if not st["ended"]:
            st["ended"] = True
            lines.append("ENDED - its messaging pipe is gone, %dm after its last move"
                         % round(_quiet(st, now)))
        return lines, st
    quiet = _quiet(st, now)
    due = [s for s in PAUSE_STEPS if quiet >= s and s not in st["fired"]]
    if due:
        st["fired"] = st["fired"] + tuple(due)
        st["paused"] = True
        lines.append("QUIET %dm - no edit, commit or user turn since; it is still live, "
                     "so it is thinking, blocked, or waiting on its user" % round(quiet))
    return lines, st


def start_offset(size, once):
    """A stream starts at the end; a single pass starts at the beginning, because
    from the end it could only ever show nothing, which reads as a clean feed."""
    return 0 if once else size


def resolve(who):
    for r in mod("whois").load():
        if r.get("name") == who or r["sessionId"].startswith(who):
            return r
    return None


def read_new(path, offset):
    """Records appended since the last look, stopping at the last full line."""
    import json
    recs = []
    try:
        size = path.stat().st_size
    except OSError:
        return recs, offset
    if size < offset:
        offset = 0
    if size == offset:
        return recs, offset
    with open(path, "rb") as f:
        f.seek(offset)
        blob = f.read()
    tail = blob.rfind(b"\n")
    if tail == -1:
        return recs, offset
    for raw in blob[:tail].splitlines():
        try:
            recs.append(json.loads(raw.decode("utf-8", "replace")))
        except Exception:
            continue
    return recs, offset + tail + 1


def main(argv):
    if not argv or "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return 0 if argv else 2
    who, once = argv[0], "--once" in argv
    row = resolve(who)
    registry = bool(row)
    if not row:
        # No registry entry (an older or newer harness may not write one). Watch the
        # transcript alone: activity and silence still report, liveness does not.
        try:
            p = mod("transcript").find(who)
        except ValueError as e:
            print(e)
            return 1
        if not p:
            print("no session in the registry or on disk matches %r - run whois.py" % who)
            return 1
        sid = os.path.basename(p)[:-len(".jsonl")]
        row = {"sessionId": sid, "name": sid[:8], "alive": True}
        print("NOTE: %s is not in the session registry, so this watch cannot tell when it "
              "ends; QUIET lines may mean ended." % sid[:8], flush=True)
    sid, name = row["sessionId"], row["name"]
    if judging_itself(sid, os.environ.get("CLAUDE_CODE_SESSION_ID")):
        print("refusing: that is this session. A session cannot watch itself.")
        return 1
    found = mod("transcript").find(sid)
    if not found:
        print("no transcript on disk for %s" % sid[:8])
        return 1
    path = pathlib.Path(found)
    st, offset = new_state(), start_offset(path.stat().st_size, once)
    print("ARMED on %s (%s) - every further line is something it did, or a silence "
          "worth knowing about" % (name, sid[:8]), flush=True)
    while True:
        recs, offset = read_new(path, offset)
        fresh = resolve(sid) if registry else row
        if fresh:
            name = fresh["name"]      # the name can change mid-session; the id cannot
        lines, st = pulse(st, recs, time.time(), bool(fresh) and fresh["alive"])
        for ln in lines:
            print("%s %s" % (name, ln), flush=True)
        if st["ended"] or once:
            return 0
        time.sleep(POLL)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
