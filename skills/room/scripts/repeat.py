"""Run seats on repeat against a working session, at a rate set by what they find.

The only difference between this and a convened room is repetition. Any seat
can run here; which ones do is a choice made per session with `arm`, never a
property of the seat.

WHAT COUNTS. Not turns. A session can take twelve turns of tool calls and put
nothing at stake. Risk is in CLAIMS that reach the user (assistant text) and
WRITES that reach disk (file edits, commits), and each seat keys on the one that
carries its risk. `cold` keys on the user's own TURNS, because the user's words
are its whole input. `shape` and `sound` key on the SPINE -- the document that
says what the work is -- because the shape of the work and the documents it
stands on move when the work moves, not when someone types.

SWITCHING. Acceptance sampling's answer to "you cannot inspect every unit" is a
rate that moves with the defect rate. Simplified from ANSI/ASQ Z1.4:

  a pass that finds something  -> TIGHTENED, interval halved
  two clean passes in a row    -> back to NORMAL
  four clean passes in a row   -> REDUCED, interval doubled

Z1.4's real switching numbers are larger; these are smaller because a session
is short, and that substitution is a judgement, not the standard. Every interval
below is a starting guess. Change one only from what passes actually find.

Known defect: a session works in bursts, and the sharpest burst is the one the
room causes by routing findings. Write-keyed seats then come due on writes the
room provoked, already tightened by the finding that provoked them. The counter
cannot tell those writes from independent ones. Use `record ... covered` for a
window you checked yourself.

  repeat.py arm <session-id> <seat> [<seat> ...] [--spine PATH]
  repeat.py due <session-id>                         who is owed a pass
  repeat.py stage <session-id> <seat>                write the feed, print the prompt
  repeat.py record <session-id> <seat> found|clean|covered
  repeat.py watch <session-id>                       one line per newly-due seat
  repeat.py prune                                    delete every feed copy

State and feeds live in ./.claude/room/ (the folder you run from), or in
$ROOM_STATE_DIR when set. Run from the working session's folder.

Feeds are transient. A feed is transcript text, tool results included, and the
host may hold transcripts under a retention policy; a copy must not outlive it.
`record` deletes the seat's feed, and `prune` empties feeds/ at the end of a run.
"""
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# seat -> (the counter that carries its risk, interval at NORMAL inspection)
RATES = {
    "response":   ("claims", 10),
    "checker":    ("claims", 12),
    "outsider":   ("claims", 25),
    "issues":     ("writes", 30),
    "engineer":   ("writes", 40),
    "chief":      ("writes", 40),    # integrity is lost per part that lands
    "critic":     ("writes", 45),    # a rendered page changes when it is regenerated
    "field":      ("writes", 60),
    "agentarch":  ("writes", 70),    # moves when the skill files and scripts do
    "outside":    ("writes", 120),   # its answer changes only when the problem does
    "cold":       ("turns",   3),    # the user's words are its whole input
    "threads":    ("both",   60),
    "situation":  ("both",   60),
    "acceptance": ("both",   70),
    "domain":     ("both",   80),
    "ground":     ("both",   90),
    "jtbd":       ("both",   90),
    "worth":      ("both",  100),
    "mentor":     ("both",  120),
    "shape":      ("spine",   1),    # comes due when the spine or HEAD moves
    "sound":      ("spine",   1),
}

# Seats whose SUBJECT is the work rather than the session. They come due on
# session activity like the rest; only their feed differs -- the spine first,
# the transcript after it as context. Without this a seat told to read the
# problem is handed a transcript and a footer naming the transcript as its
# subject, and it reports on how the session has been talking.
WORK_SUBJECT = {"chief", "mentor"}

LEVELS = {"tightened": 0.5, "normal": 1.0, "reduced": 2.0}
ARRIVAL_STEP = 8

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
_mods = {}


def tx():
    if "transcript" not in _mods:
        spec = importlib.util.spec_from_file_location("transcript", HERE / "transcript.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _mods["transcript"] = m
    return _mods["transcript"]


def state_dir():
    d = os.environ.get("ROOM_STATE_DIR") or os.path.join(os.getcwd(), ".claude", "room")
    return d


def state_file():
    return os.path.join(state_dir(), "repeat-state.json")


def ensure_state_dir():
    d = state_dir()
    os.makedirs(os.path.join(d, "feeds"), exist_ok=True)
    gi = os.path.join(d, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w", encoding="utf-8") as f:
            f.write("# room working state - not for version control\n"
                    "repeat-state.json\nfeeds/\n")
    return d


def feeds_dir():
    return os.path.join(state_dir(), "feeds")


def feed_path(sid, seat):
    return os.path.join(feeds_dir(), "feed-%s-%s.txt" % (sid[:8], seat))


def drop(path):
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def jsonl(sid):
    try:
        return tx().find(sid)
    except ValueError:
        return None


# ------------------------------------------------------------------ counting

WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def counts(sid):
    """(claims, writes, turns): what reached the user, what reached disk, and
    what the user typed. None when there is no transcript."""
    p = jsonl(sid)
    if not p:
        return None
    claims = writes = turns = 0
    for d in tx().load_records(p):
        if d.get("isSidechain"):
            continue
        if tx().person_text(d):
            turns += 1
            continue
        m = d.get("message") or {}
        if m.get("role") != "assistant":
            continue
        said = False
        for c in m.get("content") or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text" and c.get("text", "").strip():
                said = True
            elif c.get("type") == "tool_use":
                name = c.get("name")
                if name in WRITE_TOOLS:
                    writes += 1
                elif name in ("Bash", "PowerShell"):
                    if "git commit" in str((c.get("input") or {}).get("command", "")):
                        writes += 1
        if said:
            claims += 1
    return claims, writes, turns


def spine_state(spine):
    """A fingerprint of the spine and of HEAD in its folder. None if unreadable,
    which must never take a watch down."""
    if not spine:
        return None
    try:
        with open(spine, "rb") as f:
            h = hashlib.sha1(f.read()).hexdigest()[:12]
    except OSError:
        return None
    try:
        head = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(spine)),
                               "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except Exception:
        head = ""
    return "%s@%s" % (h, head[:12])


def metric(seat, claims, writes, turns=0):
    which = RATES[seat][0]
    if which == "spine":
        return None
    if which == "turns":
        return turns
    return claims if which == "claims" else writes if which == "writes" else claims + writes


# --------------------------------------------------------------------- state

def state():
    try:
        with open(state_file(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(s):
    ensure_state_dir()
    with open(state_file(), "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, sort_keys=True)


def armed(sid):
    return state().get(sid, {}).get("armed", [])


def interval(seat, rec):
    base = RATES[seat][1]
    return max(3, int(round(base * LEVELS.get(rec.get("level", "normal"), 1.0))))


def due(sid):
    c = counts(sid)
    if c is None:
        return None, []
    claims, writes, turns = c
    sess = state().get(sid, {})
    seen = sess.get("seats", {})
    owed = []
    for seat in sorted(sess.get("armed", [])):
        if seat not in RATES:
            continue
        if RATES[seat][0] == "spine":
            now = spine_state(sess.get("spine"))
            if now is None:
                continue
            was = (seen.get(seat) or {}).get("spine")
            if was is None:
                owed.append((seat, "never run against this spine"))
            elif now != was:
                owed.append((seat, "the spine or HEAD moved since it ran"))
            continue
        now = metric(seat, claims, writes, turns)
        rec = seen.get(seat) or {}
        last = rec.get("at")
        every = interval(seat, rec)
        lvl = rec.get("level", "normal")
        if last is None:
            owed.append((seat, "never run here (%s, every %d at %s)" % (RATES[seat][0], every, lvl)))
        elif now - last >= every:
            owed.append((seat, "%d %s since it ran, due every %d at %s"
                         % (now - last, RATES[seat][0], every, lvl)))
    return (claims, writes), owed


def judging_itself(sid):
    """True when the caller is the session it is about to convene a seat on.
    Absent the variable the room still runs: a guard that cannot read its input
    must not become a lock."""
    mine = os.environ.get("CLAUDE_CODE_SESSION_ID")
    return bool(mine) and bool(sid) and (mine.startswith(sid) or sid.startswith(mine))


def refuse_self(verb):
    print("This is the session you are running in, and %s a seat on yourself is" % verb)
    print("the room's founding defect: a party with a defect cannot select, brief or")
    print("score the check on it. Do this from another session; whois.py lists them.")
    return 1


def stagger(st, sid):
    """Spread the seats a fresh arming would otherwise queue for the same instant.

    Only seats with no history are touched. The fastest stays due now; the rest
    arrive ARRIVAL_STEP apart, frequent ones first. Arithmetic spacing, not a
    multiple of each interval, which would push slow seats past a short session.
    """
    sess = st.get(sid) or {}
    seen = sess.setdefault("seats", {})
    c = counts(sid)
    if c is None:
        return
    fresh = [x for x in sess.get("armed", []) if x in RATES and x not in seen
             and RATES[x][0] != "spine"]
    fresh.sort(key=lambda x: RATES[x][1])
    for k, seat in enumerate(fresh):
        now = metric(seat, *c)
        seen[seat] = {"at": now + (k * ARRIVAL_STEP) - interval(seat, {}),
                      "level": "normal", "clean_streak": 0,
                      "last_verdict": "staggered at arm"}


# ------------------------------------------------------------------ commands

def cmd_arm(sid, seats, spine=None):
    if judging_itself(sid):
        return refuse_self("arming")
    bad = [s for s in seats if s not in RATES]
    if bad:
        print("No such seat: %s" % ", ".join(bad))
        print("Available: %s" % ", ".join(sorted(RATES)))
        return 1
    # No cap on how many are armed. The wall is what gets RELAYED to a working
    # session, not how many advisors think; pacing is the per-seat rate.
    wants = [x for x in seats if RATES[x][0] == "spine"]
    s = state()
    spine = os.path.abspath(spine) if spine else s.get(sid, {}).get("spine")
    if wants and not spine:
        print("%s read(s) the spine, so arming needs one: --spine <path to the document "
              "that says what this work is>" % ", ".join(wants))
        return 1
    had = set(s.get(sid, {}).get("armed", []))
    dropped = had - set(seats)
    if dropped:
        print("REPLACING seats another room may be holding: %s no longer armed on %s"
              % (", ".join(sorted(dropped)), sid[:8]))
    s.setdefault(sid, {})["armed"] = sorted(set(seats))
    if spine:
        s[sid]["spine"] = spine
    stagger(s, sid)
    save(s)
    print("on repeat for %s: %s" % (sid[:8], ", ".join(sorted(set(seats)))))
    return 0


def cmd_due(sid):
    c, owed = due(sid)
    if c is None:
        print("No transcript for %s" % sid)
        return 1
    print("session %s - %d claims to the user, %d writes to disk" % (sid[:8], c[0], c[1]))
    if not armed(sid):
        print("no seats armed. Choose them by what this session is doing:")
        print("  repeat.py arm %s <seat> <seat> ..." % sid)
        print("  available: %s" % ", ".join(sorted(RATES)))
        return 0
    if not owed:
        print("nothing owed")
        return 0
    for seat, why in owed:
        print("  DUE %-10s %s" % (seat, why))
    return 0


def cmd_watch(sid, once=False):
    """One stdout line per newly-owed seat. Each line becomes a Monitor event."""
    me = str(HERE / "repeat.py")
    announced = set()
    while True:
        c, owed = due(sid)
        if c is not None:
            names = set(s for s, _ in owed)
            for seat, why in owed:
                if seat not in announced:
                    print('DUE %s on %s (%s) - stage it: python "%s" stage %s %s'
                          % (seat, sid[:8], why, me, sid, seat), flush=True)
                    announced.add(seat)
            announced &= names
        if once:
            return 0
        time.sleep(30)


FOOTER_GAP = """OUTPUT CONTRACT. Under 250 words. No preamble, no summarizing back what you
read, no compliments. Lead with your strongest opinion. Be specific enough to be
wrong. If you have nothing worth interrupting for, say so in one line.

NEVER ROUTE A GAP TO A PERSON. Not "only the business can supply this",
not "pending a ruling", not "blocked until someone decides". The model drafts
every value and states its basis; ratification is a point-in-time event in the
real world and is never a precondition for building or testing. A person-shaped
gap in a report is a failed pass. This is about a seat drafting a value instead
of stalling; it never replaces an approval, sign-off or control the work is
actually subject to."""


def cmd_stage(sid, seat):
    if judging_itself(sid):
        return refuse_self("staging")
    seatfile = SKILL / "seats" / (seat + ".md")
    if seat not in RATES or not seatfile.exists():
        print("No such seat: %s" % seat)
        return 1
    path = jsonl(sid)
    if not path:
        print("No transcript for %s" % sid)
        return 1
    ensure_state_dir()
    feed = feed_path(sid, seat)
    sess = state().get(sid, {})
    spine = sess.get("spine")
    kind = RATES[seat][0]

    # The user's turns come from the WHOLE session, never from a window: a long
    # run of tool calls pushes every one of them out of the last 120 records.
    turns = tx().person_turns(path)
    # The recent window, cleaned: no injected records, none of the session's own
    # outbound messages, and each line capped so one pasted file cannot eat it.
    win = "\n".join((l[:1200] + " ...[line truncated]") if len(l) > 1200 else l
                    for l in tx().window(path, 120, clean=True).splitlines()
                    if "cross-session-message" not in l)

    def spine_text():
        try:
            with open(spine, encoding="utf-8", errors="replace") as f:
                return f.read()[:30000]
        except (OSError, TypeError):
            return None

    spine_given = False
    if kind == "spine":
        body = spine_text()
        if body is None:
            print("%s needs the spine and it could not be read: %s" % (seat, spine))
            return 1
        text = ("=== THE SPINE (%s): what this work is and how it is meant to be "
                "built ===\n\n%s" % (spine, body))
    elif seat == "cold":
        if not turns:
            print("cold declined on %s: the user has not typed anything in this session." % sid[:8])
            print()
            print("cold's whole input is the user's words. A session started from a")
            print("prompt nobody typed leaves none, and a cold pass on an empty feed does")
            print("not fail loudly -- it goes looking for a premise and judges whatever it")
            print("finds, often the room's own briefing. Seats keyed to the work still")
            print("run here: shape and sound read the spine.")
            return 1
        text = "\n".join(turns[-25:])[-22000:]
    else:
        text = ("=== WHAT THE USER SAID, in order, across the whole session ===\n"
                + "\n".join(turns[-12:])
                + "\n\n=== THE SESSION, most recent ===\n" + win[-20000:])
        if seat in WORK_SUBJECT and spine:
            body = spine_text()
            if body is not None:
                text = ("=== THE PROBLEM (%s): what this work is and how it is meant to "
                        "be built. THIS is your subject. ===\n\n%s\n\n=== THE SESSION, as "
                        "context only -- where the thinking has got to, never the thing "
                        "you are judging ===\n\n%s" % (spine, body, text))
                spine_given = True
    with open(feed, "w", encoding="utf-8") as f:
        f.write(text)

    fp = feed.replace(os.sep, "/")
    print(seatfile.read_text(encoding="utf-8"))
    print("\n---\n")
    if seat == "shape":
        print("THE FEED. Read this file -- it holds the spine:\n  %s\n" % fp)
        print("No board is staged here. Read the tracker the work actually lives in")
        print("yourself (the spine usually names it; for GitHub, `gh issue list` and the")
        print("parent issue) and read it AGAINST the spine. The subject is HOW THE WORK")
        print("IS ORGANISED, not this session's turns.\n")
    elif seat == "sound":
        print("THE FEED. Read this file -- it holds the spine, one load-bearing document:")
        print("  %s\n" % fp)
        print("Find the others it rests on yourself, and the code they describe. The")
        print("session transcript is deliberately not included.\n")
    elif seat == "cold":
        print("THE USER'S OWN WORDS, verbatim, and nothing else from the session:")
        print("  %s\n" % fp)
        print("You are denied the session's narration -- that frame is what you are")
        print("checking. Take the premise from these words and check it against the")
        print("rulings ON DISK.\n")
    elif spine_given:
        print("THE FEED. Read this file -- it opens with the spine, what this work is,")
        print("and the session follows it as context:\n  %s\n" % fp)
        print("The subject is THE WORK -- its design, its direction, what it is for. A")
        print("report about how the session has been talking is a failed pass.\n")
    else:
        print("THE FEED. Read this file -- the user's turns, then the working session's")
        print("recent activity:\n  %s\n" % fp)
        print("Judge what the session produced -- the claims it made, the work it")
        print("landed -- never how it behaved.\n")
    print(FOOTER_GAP)
    print()
    print("(after the seat reports: repeat.py record %s %s found|clean)" % (sid, seat))
    return 0


def cmd_record(sid, seat, verdict):
    if verdict not in ("found", "clean", "covered"):
        print("verdict must be 'found', 'clean' or 'covered' - it sets the inspection rate")
        return 1
    if seat not in RATES:
        print("No such seat: %s" % seat)
        return 1
    # The seat has reported, so its feed has been read. Delete it before
    # anything can return early: once the host has removed the transcript,
    # the copy is the only one left.
    drop(feed_path(sid, seat))
    c = counts(sid)
    if c is None:
        print("No transcript for %s" % sid)
        return 1
    s = state()
    sess = s.setdefault(sid, {})
    rec = sess.setdefault("seats", {}).setdefault(seat, {})
    spine_kind = RATES[seat][0] == "spine"

    if verdict == "covered":
        # The orchestrator checked this window itself. Not a verdict about the
        # work: it neither tightens nor counts toward relaxing.
        if spine_kind:
            rec["spine"] = spine_state(sess.get("spine"))
        else:
            rec["at"] = metric(seat, *c)
        rec.setdefault("level", "normal")
        rec.setdefault("clean_streak", 0)
        rec["last_verdict"] = "covered"
        save(s)
        print("recorded %s on %s - covered by the orchestrator, rate unchanged" % (seat, sid[:8]))
        return 0

    streak = 0 if verdict == "found" else rec.get("clean_streak", 0) + 1
    if verdict == "found":
        level = "tightened"
    elif streak >= 4:
        level = "reduced"
    elif streak >= 2:
        level = "normal"
    else:
        level = rec.get("level", "normal")
    if spine_kind:
        rec["spine"] = spine_state(sess.get("spine"))
    rec["at"] = metric(seat, *c)
    rec["level"] = level
    rec["clean_streak"] = streak
    rec["last_verdict"] = verdict
    save(s)
    print("recorded %s on %s - %s, inspection now %s (clean streak %d)"
          % (seat, sid[:8], verdict, level, streak))
    return 0


def cmd_prune():
    """Delete every feed copy. Run at the end of a run, once every seat has
    reported: a seat still running in the background is reading its feed."""
    d = feeds_dir()
    gone = 0
    if os.path.isdir(d):
        for name in os.listdir(d):
            p = os.path.join(d, name)
            if os.path.isfile(p) and drop(p):
                gone += 1
    print("pruned %d feed file(s) from %s" % (gone, d))
    return 0


def main(argv):
    a = list(argv)
    if not a or "-h" in a or "--help" in a:
        print(__doc__.strip())
        return 0 if a else 2
    if a[0] == "arm" and len(a) >= 3:
        spine = None
        if "--spine" in a:
            i = a.index("--spine")
            spine = a[i + 1] if len(a) > i + 1 else None
            a = a[:i] + a[i + 2:]
        return cmd_arm(a[1], a[2:], spine=spine)
    if a[0] == "due" and len(a) == 2:
        return cmd_due(a[1])
    if a[0] == "watch" and len(a) in (2, 3):
        return cmd_watch(a[1], once="--once" in a)
    if a[0] == "stage" and len(a) == 3:
        return cmd_stage(a[1], a[2])
    if a[0] == "record" and len(a) == 4:
        return cmd_record(a[1], a[2], a[3])
    if a[0] == "prune" and len(a) == 1:
        return cmd_prune()
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
