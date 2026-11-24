"""Who is working now: one account of every agent of a run, read from the agents' own transcripts on disk each time the
run status page is drawn. The page's badge, its working line and its "Who is working now" panel are all read from
this one account, so they never disagree.

Which agents: the lead (the current session's own transcript), the lead's own agents (every subagent of every session
the run has had, found by session id, so a first-look helper shows before any kit prompt exists), and the kit's agents
(found by the pointer line of a prompt under prompts/, as timings.py finds them). Each transcript is taken once.

State of an agent, in this order: finished (Claude Code's metadata says so; never read from the transcript's last
line); lost to an API error; discarded (a kit agent that ran a shell); not heard from for N min (red, silence past
RED_MINUTES); waiting on the model for N min, or quiet for N min (amber, past AMBER_MINUTES); working.

gather() never raises: on any failure it returns the reason, and the page falls back to its own files and says so.
Python standard library only."""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

AMBER_MINUTES = 6  # above the 300 s request timeout, so a healthy wait on the model is not flagged
RED_MINUTES = 40  # a run of retries after a 503 can last over half an hour before its error line
LOST_QUIET = 120  # judges.LAUNCHER_QUIET: an API error with nothing after it for this long ended the agent
SESSIONS = "sessions.json"  # in _run-state/: every session id the run has had, oldest first
STATE_DIR = "_run-state"
RUN_DIR = "_start-"  # start.RUN_DIR: one run's own folder in the work folder before its register exists
SHELLS = ("Bash", "PowerShell")
READS = {"Read": "file_path", "Grep": "pattern", "Glob": "pattern", "WebFetch": "url", "Write": "file_path",
         "Edit": "file_path", "NotebookEdit": "notebook_path"}

WORKING, AMBER, RED, FINISHED, WAITING_AGENTS = "working", "amber", "red", "finished", "waiting on its agents"
QUEUED = "queued"
LEAD_PROMPT = "first-look-lead.md"  # first_look.LEAD_PROMPT: the lead's own; never shown queued

_cache, _lock = {}, threading.Lock()


def _when(v):
    try:
        t = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _json(p):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _short(s, n=60):
    s = " ".join(str(s).split())
    return s if len(s) <= n else "…" + s[-(n - 1):]


def facts(f):
    """The raw facts of one transcript, cached by (path, size, mtime): first and last line times, the kind of its last
    record, its last tool call and when, whether it ends on an API error, whether it ran a shell, its first user
    message. Derived states depend on the time and are never cached."""
    st = os.stat(f)
    key = (str(f), st.st_size, st.st_mtime_ns)
    with _lock:
        got = _cache.get(str(f))
        if got and got[0] == key:
            return got[1]
    first = last = None
    kind, tool, tool_at, n_tools, shell, error, prompt, ended = None, None, None, 0, False, False, None, False
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            t = _when(d["timestamp"]) if d.get("timestamp") else None
            typ = d.get("type")
            if typ == "system" and d.get("subtype") == "api_error":
                error, kind = True, "api_error"
                last = t or last
                continue
            if typ in ("api-request", "api_request"):
                kind, last = "model", t or last
                continue
            m = d.get("message")
            if typ not in ("user", "assistant") or not isinstance(m, dict):
                continue
            if t is not None:
                first = first or t
                last = t
            c = m.get("content")
            blocks = [b for b in (c if isinstance(c, list) else []) if isinstance(b, dict)]
            if typ == "user":
                if prompt is None:
                    prompt = c if isinstance(c, str) else " ".join(
                        b.get("text", "") for b in blocks if b.get("type") == "text")
                kind, error = "model", False  # a prompt or a tool's result: the model has the next move
                continue
            if d.get("isApiErrorMessage"):
                error, kind = True, "api_error"
                continue
            error = False
            uses = [b for b in blocks if b.get("type") == "tool_use"]
            if uses:
                kind, tool_at, n_tools = "tool", t, len(uses)
                u = uses[-1]
                arg = (u.get("input") or {}).get(READS.get(u.get("name"), ""), "") if isinstance(u.get("input"), dict) else ""
                tool = (u.get("name") or "a tool", _short(arg) if arg else "")
                shell = shell or any(b.get("name") in SHELLS for b in uses)
            else:
                kind = "writing"
            ended = not uses and m.get("stop_reason") == "end_turn"  # a reply that called no tool and ended its turn
    got = {"first": first, "last": last, "kind": kind, "tool": tool, "tool_at": tool_at, "n_tools": n_tools,
           "shell": shell, "error": error, "prompt": prompt or "", "end_turn": kind == "writing" and ended}
    with _lock:
        _cache[str(f)] = (key, got)
    return got


_meta_cache = {}


def meta(f):
    """Claude Code's metadata beside a transcript, cached by the file's size and time; {} when there is none."""
    p = pathlib.Path(f).with_name(pathlib.Path(f).stem + ".meta.json")
    try:
        st = os.stat(p)
    except OSError:
        return {}
    key = (st.st_size, st.st_mtime_ns)
    with _lock:
        got = _meta_cache.get(str(p))
        if got and got[0] == key:
            return got[1]
    d = _json(p) or {}
    with _lock:
        _meta_cache[str(p)] = (key, d)
    return d


def window_record_is(reg, record):
    """Whether the work folder's window-wide run-started.json (an earlier release's: one record for the window) is
    this register's: it names this register, or names none while this is the only register in the work folder. With
    several registers an unnamed record could be any of them, so it is none of theirs."""
    reg = pathlib.Path(reg)
    named = str((record or {}).get("register") or "")
    if named:
        return named in (str(reg), str(reg.resolve()))
    try:
        others = [d for d in reg.parent.iterdir() if d.is_dir() and d != reg and (d / "RUN.md").is_file()]
    except OSError:
        return False
    return (reg / "RUN.md").is_file() and not others


def session_ids(reg):
    """(every session id the run has had, oldest first; the current one, or None). Read from the run's lock, its
    run-started.json, the first-look marks naming this folder, and _run-state/sessions.json. Another run's start
    folder or an earlier release's window-wide record is never this run's. A folder that is neither a register nor
    a run's start folder (the work folder) has no sessions of its own: it never borrows a run's."""
    reg = pathlib.Path(reg)
    start_dir = reg.name.startswith(RUN_DIR)
    if not start_dir and not (reg / "RUN.md").is_file() and not (reg / "RUN.lock").is_file():
        return [], None
    ids = list((_json(reg / STATE_DIR / SESSIONS) or {}).get("ids") or [])
    current = None
    lock = _json(reg / "RUN.lock") or {}
    found = []
    for p in (reg / STATE_DIR / "run-started.json", reg / "run-started.json"):
        r = (_json(p) or {}).get("run")
        if r:
            found.append(r)
    parent = reg.parent
    if not start_dir:
        started = _json(parent / "run-started.json") or {}
        if started.get("run") and window_record_is(reg, started):
            found.append(started["run"])
        for p in sorted(parent.glob(RUN_DIR + "*/run-started.json")):  # the run's start folder that led here
            d = _json(p) or {}
            named = d.get("register")
            if d.get("run") and named and pathlib.Path(named).resolve() == reg.resolve():
                found.append(d["run"])
    marks = [reg / "first-look.json"] + ([] if start_dir else list(parent.glob(RUN_DIR + "*/first-look.json")))
    for mark in marks:
        m = _json(mark) or {}
        folder = m.get("folder")
        own = mark.parent == reg or (folder and pathlib.Path(folder).resolve() == reg.resolve())
        if m.get("run") and own:
            found.append(m["run"])
    if lock.get("run"):
        found.append(lock["run"])
        current = lock["run"]
    for r in found:
        if r not in ids:
            ids.append(r)
    if not start_dir:  # a session another register holds as its own (its lock, a start folder naming it) is not this
        # run's, unless this run's own records name it too: a list kept before runs were told apart may carry one
        theirs = claimed_elsewhere(reg) - set(found)
        ids = [r for r in ids if r not in theirs]
    return ids, current or (ids[-1] if ids else None)


def claimed_elsewhere(reg):
    """The session ids the other registers in the work folder hold as their own: each one's lock, and each run's start
    folder naming one of them."""
    reg = pathlib.Path(reg).resolve()
    out = set()
    try:
        others = [d.resolve() for d in reg.parent.iterdir() if d.is_dir() and d.resolve() != reg
                  and (d / "RUN.md").is_file()]
    except OSError:
        return out
    for d in others:
        r = (_json(d / "RUN.lock") or {}).get("run")
        if r:
            out.add(r)
    names = {str(d) for d in others}
    for p in reg.parent.glob(RUN_DIR + "*/run-started.json"):
        d = _json(p) or {}
        named = d.get("register")
        if d.get("run") and named and str(pathlib.Path(named).resolve()) in names:
            out.add(d["run"])
    return out


def remember_session(reg, run):
    """Add `run` to the run's list of sessions, so a later session that rewrites RUN.lock never loses an earlier
    session's agents. Never raises."""
    if not run:
        return
    try:
        p = pathlib.Path(reg) / STATE_DIR / SESSIONS
        ids = list((_json(p) or {}).get("ids") or [])
        if run in ids:
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"ids": ids + [run]}), encoding="utf-8")
    except OSError:
        pass


def _folders(reg, transcripts):
    if transcripts:
        return [pathlib.Path(t) for t in (transcripts if isinstance(transcripts, (list, tuple)) else [transcripts])]
    import reading_check
    return reading_check.project_folders(reg)


def _kit_prompt(text, prompts, reg=None):
    """The prompt a kit agent was given, relative to prompts/; a fast mapper's (fast/mappers/<group>/) as
    timings names it ("fast mapper: <group>"); None for an agent the kit did not launch."""
    import timings
    m = timings.POINTED.search((text or "").strip())
    if not m:
        return None
    import paths
    target = m.group(1).replace("\\", "/")
    if paths.norm(target).startswith(prompts + "/"):
        return target[len(prompts) + 1:]
    if reg is not None:
        fast = paths.norm((pathlib.Path(reg).resolve() / "fast" / "mappers").as_posix())
        if paths.norm(target).startswith(fast + "/") and target.endswith("/mapper-prompt.md"):
            return f"{timings.FAST_ROW}: {target.split('/')[-2]}"
    return None


AGENT_OF = {"reader": "bfo-unit-reader", "reader retry": "bfo-unit-reader", "fixer": "bfo-unit-reader",
            "re-read": "bfo-unit-reader", "stop fixer": "bfo-unit-reader", "fast mapper": "bfo-flow-mapper",
            "source reader": "bfo-source-reader", "judge round": "bfo-row-judge"}


def no_shell_agents():
    """The kit's agent types whose tools hold no shell, read from their own definitions (agents/*.md `tools:`)."""
    out = set()
    for f in sorted((HERE / "agents").glob("*.md")):
        tools = next((x.split(":", 1)[1] for x in f.read_text(encoding="utf-8").splitlines()
                      if x.startswith("tools:")), "")
        if not {t.strip() for t in tools.split(",")} & set(SHELLS):
            out.add(f.stem)
    return out


def shell_breaks(step):
    """An agent of this step may not run a shell, so one that did is discarded: the kit's agent types with no shell,
    and the launchers, which run none. The first-look helper runs the kit's own scripts and is never discarded."""
    if step.startswith("launcher"):
        return True
    agent = next((a for s, a in AGENT_OF.items() if step == s or step.startswith(s + " ")), None)
    return agent in no_shell_agents()


def turn_ended(fx, now):
    """The lead's turn has ended: its last line is a reply that called no tool and ended its turn, and nothing newer
    came for run_state.TURN_ENDED_SECONDS (a reply's lines, its thinking, its text and its tool call, come apart by
    up to a few minutes, so one alone never ends a turn)."""
    import run_state
    last = fx.get("last")
    return bool(fx.get("end_turn") and last and (now - last).total_seconds() >= run_state.TURN_ENDED_SECONDS)


def state_of(fx, md, now, lead=False):
    """(state, the words for it) of one agent from its raw facts, its metadata and the time now."""
    if not lead and md.get("finished") is True:
        return FINISHED, "finished"
    last = fx["last"]
    quiet = (now - last).total_seconds() if last else None
    if fx["error"] and quiet is not None and quiet >= LOST_QUIET:
        return RED, f"lost to an API error at {_clock(last, now)}"
    if quiet is None:
        return WORKING, "started"
    mins = int(quiet // 60)
    if quiet > RED_MINUTES * 60:
        return RED, f"not heard from for {mins} min"
    if quiet > AMBER_MINUTES * 60:
        return AMBER, (f"waiting on the model for {mins} min" if fx["kind"] == "model" else f"quiet for {mins} min")
    return WORKING, "working"


def _clock(t, now):
    return t.astimezone(now.tzinfo).strftime("%H:%M") if t else ""


def now_line(fx, now):
    """What the agent is doing right now, from the kind of its last record."""
    k = fx["kind"]
    if k == "model":
        return f"waiting on the model since {_clock(fx['last'], now)}"
    if k == "writing":
        return "writing"
    if k == "tool":
        if fx["n_tools"] > 1:
            return f"running {fx['n_tools']} tool calls"
        name, arg = fx["tool"] or ("a tool", "")
        verb = {"Read": "reading", "Grep": "searching", "Glob": "listing", "Write": "writing", "Edit": "editing",
                "WebFetch": "fetching"}.get(name, f"running {name}")
        return f"{verb} {arg}".strip()
    if k == "api_error":
        return "retrying after an API error"
    return "starting"


def last_action(fx, now):
    if not fx["tool"]:
        return ""
    name, arg = fx["tool"]
    return f"{name} {arg}".strip() + (f", {_clock(fx['tool_at'], now)}" if fx["tool_at"] else "")


def first_look(reg):
    """(mode, the window's start, the parts as {key: record path}) of the first look under way, or None: none started,
    or its brief already rendered (PLAN.md newer than its mode.json). Parts are first-look/parts.csv's rows; a part is
    done when its record (first-look/<key>.json) was written since the window started, so a record left by an earlier
    look never counts."""
    import csv
    reg = pathlib.Path(reg)
    fl = reg / "first-look"
    m = _json(fl / "mode.json")
    if not m:
        return None
    plan = reg / "PLAN.md"
    try:
        if plan.is_file() and plan.stat().st_mtime > (fl / "mode.json").stat().st_mtime:
            return None
        with open(fl / "parts.csv", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except (OSError, csv.Error):
        rows = []
    parts = {}
    for r in rows:
        sid, part = (r.get("source_id") or "").strip(), (r.get("part") or "").strip()
        if sid:
            key = sid if part in ("", "whole") else f"{sid}-{part}"
            parts[key] = fl / f"{key}.json"
    return m.get("mode") or "single", _when(m.get("window_start")), parts


def part_done(path, since):
    try:
        t = dt.datetime.fromtimestamp(pathlib.Path(path).stat().st_mtime, dt.timezone.utc)
    except OSError:
        return False
    return since is None or t >= since


def emissions(reg, floor):
    """{prompt path under prompts/: the time of its latest emission at or after `floor`} from emitted-at.jsonl."""
    got = {}
    p = pathlib.Path(reg) / "prompts" / "emitted-at.jsonl"
    try:
        lines = p.read_text(encoding="utf-8").splitlines() if p.is_file() else []
    except OSError:
        return got
    for x in lines:
        try:
            d = json.loads(x)
        except ValueError:
            continue
        at = _when(d.get("at")) if isinstance(d, dict) else None
        if at is None or (floor is not None and at < floor) or not d.get("path"):
            continue
        if d["path"] not in got or at > got[d["path"]]:
            got[d["path"]] = at
    return got


def gather(reg, now=None, transcripts=None):
    """{"readable", "reason", "lead", "agents", "finished", "at_work", "red", "amber"}; never raises."""
    try:
        return _gather(pathlib.Path(reg), now or dt.datetime.now(dt.timezone.utc).astimezone(), transcripts)
    except Exception as e:  # noqa: BLE001  (the page draws its other panels whatever this meets)
        return {"readable": False, "reason": f"Cannot read the agents' records: {type(e).__name__}: {e}"[:300],
                "lead": None, "agents": [], "finished": 0, "at_work": 0, "red": 0, "amber": 0, "queued": 0,
                "count": None}


def _count(look):
    if not look:
        return None
    _, since, parts = look
    return f"{sum(part_done(p, since) for p in parts.values())} of {len(parts)} parts"


def _floor(reg, look):
    """The earliest emission that can still be queued: the flow worked now's go, else the first look's window."""
    s = _json(pathlib.Path(reg) / "scope.json") or {}
    given = _when(s.get("given")) if s.get("given") else None
    return given or (look[1] if look else None)


def _gather(reg, now, transcripts):
    look = first_look(reg)
    got = _gather_agents(reg, now, transcripts, look)
    got["count"] = _count(look)
    return got


def _gather_agents(reg, now, transcripts, look):
    ids, current = session_ids(reg)
    folders = [f for f in _folders(reg, transcripts) if f.is_dir()]
    empty = {"lead": None, "agents": [], "finished": 0, "at_work": 0, "red": 0, "amber": 0, "queued": 0}
    if not ids:
        return dict(empty, readable=False, reason="No session is recorded for this run yet, so who is working "
                                                  "cannot be read; the badge is read from the run's files.")
    if not folders:
        return dict(empty, readable=False, reason="Cannot read the agents' records: no transcript folder was found "
                                                  "for this workspace. The badge falls back to the run's own files, "
                                                  "which can show a stopped agent as running for up to 90 minutes.")
    import paths
    prompts = paths.norm((reg.resolve() / "prompts").as_posix())
    seen, agents, lead = set(), [], None
    for folder in folders:
        for sid in ids:
            main = folder / f"{sid}.jsonl"
            if sid == current and main.is_file() and lead is None:
                fx = facts(main)
                st, words = state_of(fx, {}, now, lead=True)
                lead = {"who": "the lead", "on": "the run itself", "now": now_line(fx, now),
                        "last_action": last_action(fx, now), "last": fx["last"], "tool_at": fx["tool_at"],
                        "started": fx["first"],
                        "state": st, "words": words, "kind": "lead", "replied": fx["kind"] == "writing",
                        "idle_turn": turn_ended(fx, now)}
            sub = folder / sid / "subagents"
            for f in sorted(sub.glob("*.jsonl")) if sub.is_dir() else []:
                if str(f) in seen:
                    continue
                seen.add(str(f))
                fx = facts(f)
                md = meta(f)
                rel = _kit_prompt(fx["prompt"], prompts, reg)
                if rel is not None:
                    import timings
                    unit, step = timings.step_of(rel)
                    who, on, kind = step, unit or rel, "kit"
                else:
                    if (fx["prompt"] or "").strip().startswith("Read ") and "do exactly what it says" in fx["prompt"]:
                        continue  # another register's kit agent
                    who, on, kind = "helper", " ".join(str(md.get("description") or "").split()) or "the lead's own agent", "lead's agent"
                st, words = state_of(fx, md, now)
                if look and rel is not None and rel.startswith("first-look/") and on in look[2] and \
                        part_done(look[2][on], look[1]):
                    st, words = FINISHED, "finished"  # its record is written: done, whatever Claude Code recorded
                if kind == "kit" and fx["shell"] and st != FINISHED and shell_breaks(who):
                    st, words = RED, "discarded: it ran a shell"
                agents.append({"who": who, "on": on, "now": "" if st == FINISHED else now_line(fx, now),
                               "last_action": last_action(fx, now), "last": fx["last"], "tool_at": fx["tool_at"],
                               "started": fx["first"],
                               "state": st, "words": words, "kind": kind, "prompt": rel})
    single = bool(look) and look[0] != "split"
    import timings
    for rel, at in sorted(emissions(reg, _floor(reg, look)).items()):
        if rel == LEAD_PROMPT or (single and rel.startswith("first-look/")):
            continue  # the lead's own prompt, and a single-mode look's parts, which the lead reads itself
        if any(a.get("prompt") == rel and a["started"] and a["started"] >= at - dt.timedelta(seconds=1)
               for a in agents):
            continue  # taken by a transcript that started after its latest emission
        if not (reg / "prompts" / rel).is_file():
            continue  # its prompt is gone (replaced, or its row not selected): it will never run
        unit, step = timings.step_of(rel)
        agents.append({"who": step, "on": unit or rel, "now": "", "last_action": "", "last": None, "started": None,
                       "emitted": at,
                       "state": QUEUED, "words": "queued", "kind": "kit", "prompt": rel})
    if lead is None and not agents:
        return dict(empty, readable=False, reason="No agent started yet.") if folders else empty
    # running agents, and launches emitted moments ago that Claude Code has yet to start: a launch left queued past
    # the quiet limit is not one the lead is waiting on, so a quiet lead shows quiet, not "waiting on its agents"
    live = [a for a in agents if a["state"] in (WORKING, AMBER) or a["state"] == QUEUED and a.get("emitted")
            and (now - a["emitted"]).total_seconds() <= AMBER_MINUTES * 60]
    if lead is not None and live and lead["replied"]:
        lead.update(state=WAITING_AGENTS, words=f"waiting on its agents ({len(live)} running)",
                    now=f"waiting on its agents ({len(live)} running)")
    elif lead is not None and lead["idle_turn"] and lead["state"] == WORKING:  # its turn has ended (turn_ended) and
        # nothing it started is running: it no longer reads as working (run_state reads this as stopped)
        lead.update(state=AMBER, words="its turn has ended", now="its turn has ended")
    rows = ([lead] if lead else []) + agents
    return {"readable": True, "reason": None, "lead": lead, "agents": agents,
            "finished": sum(a["state"] == FINISHED for a in agents),
            "queued": sum(a["state"] == QUEUED for a in agents),
            "at_work": sum(r["state"] in (WORKING, WAITING_AGENTS) for r in rows),
            "red": sum(r["state"] == RED for r in rows), "amber": sum(r["state"] == AMBER for r in rows)}


def as_ended(g):
    """The account of a run that has ended (every step done, no flow left): an agent or lead not heard from lately is
    finished, never waiting or not heard from, and a launch never taken is no longer queued. An agent still working
    is shown as it is. Only for a run that has ended: a live run's account is never passed through this."""
    if not g.get("readable"):
        return g
    done = dict(state=FINISHED, words="finished", now="")
    agents = [a if a["state"] in (WORKING, FINISHED) else dict(a, **done) for a in g["agents"]
              if a["state"] != QUEUED]
    live = g["lead"] and (g["lead"]["state"] == WORKING or g["lead"]["state"] == WAITING_AGENTS and any(
        a["state"] == WORKING for a in agents))
    lead = g["lead"] if live or not g["lead"] else dict(g["lead"], **done)
    rows = ([lead] if lead else []) + agents
    return dict(g, lead=lead, agents=agents, finished=sum(a["state"] == FINISHED for a in agents), queued=0,
                at_work=sum(r["state"] in (WORKING, WAITING_AGENTS) for r in rows), red=0, amber=0)


def badge(g):
    """The page's badge from the account alone: running, stopped, quiet, starting; None when it cannot be read (the
    page then uses its own files, and says so)."""
    if not g["readable"]:
        return "starting" if g.get("reason") == "No agent started yet." else None
    if g["at_work"]:
        return "running"
    rows = ([g["lead"]] if g["lead"] else []) + g["agents"]
    open_ = [r for r in rows if r["state"] != FINISHED]
    if open_ and all(r["state"] == RED for r in open_) and any(r["kind"] != "lead" for r in open_):
        return "stopped"
    return "quiet"


def words(g):
    """The line under the badge, counted from the rows the panel shows and said in their own words ("not
    heard from", "waiting on the model", "lost to an API error"), never a word no row says."""
    if not g["readable"]:
        return g.get("reason") or ""
    rows = ([g["lead"]] if g.get("lead") else []) + list(g.get("agents") or [])
    bits = [g["count"]] if g.get("count") else []
    working = sum(r["state"] in (WORKING, WAITING_AGENTS) for r in rows)
    if working:
        bits.append(f"{working} working")
    queued = sum(r["state"] == QUEUED for r in rows)
    if queued:
        bits.append(f"{queued} queued")
    kinds = {}
    for r in rows:
        if r["state"] in (AMBER, RED):
            k = re.sub(r"( for \d+ min| at \d\d:\d\d|: .*)$", "", r["words"])
            kinds[k] = kinds.get(k, 0) + 1
    bits += [f"{n} {k}" for k, n in kinds.items()]
    finished = sum(r["state"] == FINISHED for r in rows)
    if finished:
        bits.append(f"{finished} finished")
    return " · ".join(bits)
