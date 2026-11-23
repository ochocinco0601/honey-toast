"""The run's own timing record: <reg>/job/timings.csv, one row per agent attempt the run launched, read from the
agents' own transcripts.

Usage: python timings.py <register folder> [--transcripts DIR]

The file is kept current with no one asking: next.py rewrites it whole each time run control is called (each launch,
each launcher's reply, each wait and every stop), and picking a run back up after a crash or a restart writes it first
(start.py, and readers.py or judges.py with --again). Launchers run no shell, so no row is written between those calls;
nothing is lost by that, since the rows are read from the transcripts on disk. Every one of these goes through
refresh(), which never raises: a failure is logged to the register's events.log and run control carries on. Run on
its own, it prints the file's path and its row count. Python standard library only.

Which transcripts: the ones run control already reads (judges.given_sessions: every `*.jsonl` under the transcript
folders, `--transcripts` or the project folders of the register's path). An attempt is a transcript whose first user
message is the pointer line of a prompt file under this register's `prompts/` folder ("Read <file> and do exactly
what it says. Reply with one line."). The lead's own agents are attempts too: every other subagent transcript
(`<main>/subagents/*.jsonl`) of a main session that launched one of those attempts, the lead's helpers such as a
first look over the code, launched without a kit prompt. Any other session in the folder is left out.

The columns:
  unit         the folder of the prompt file, prompts/<unit>/; for a launcher (prompts/launch/), the unit of a
               judges launcher's name (judges-<unit>-r<N>-...), blank for a readers launcher and a lead's own agent
  step         from the prompt file's name: `read` reader, `retry` reader retry, `fix` and `fix-<table>` fixer,
               `reread-*` re-read, `stop-*` stop fixer, `r<N>-j<J>-*` judge round N, prompts/launch/readers-<mode>-*
               launcher of readers <mode>, prompts/launch/judges-*-r<N>-* launcher of judge round N; `lead's own
               agent` for one the lead launched without a kit prompt
  attempt      1, 2, ...: this transcript's place, by start, among all transcripts given the same prompt file's pointer
               line in this register (a flow mapped later that reuses a prompt file's name counts on); for a lead's
               own agent, among those with the same description
  agent        the transcript's `agentId` (a subagent), else its `sessionId`, else the file's name
  model        `message.model` of its first assistant message that is not Claude Code's own error reply
  start, end   the `timestamp` of the transcript's first and of its last line that has one, in file order, as UTC
               (YYYY-MM-DDTHH:MM:SSZ): when the agent wrote, never when run control looked
  seconds      end minus start, whole seconds
  turns        model responses: distinct `message.id` (else `requestId`) among `assistant` lines, Claude Code's own error
               replies (isApiErrorMessage, model <synthetic>) left out. One response is written as several lines (its
               text, and each tool call, on lines of their own, each carrying the same id and usage), so lines are
               never counted
  input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens
               the sum over those responses of `usage` input_tokens, output_tokens, cache_read_input_tokens and
               cache_creation_input_tokens, each response counted once (its last line's usage); blank where no
               response recorded that field. Other record kinds (api-request-blob, which replays a request) are never
               read for turns or tokens
  api_errors   failed model requests the transcript records: each `system` line of subtype `api_error` (a request that
               failed and was retried) plus each error reply of Claude Code's (isApiErrorMessage: the request it gave
               up on)
  longest_gap_seconds
               the longest time, in whole seconds, between two consecutive lines that have a `timestamp`, in file
               order. A response split over several lines splits its own writing time between them; it adds no gap
               of its own and none is counted twice
  gap_ends_on_error
               yes when the later line of that longest gap is an api_error line or an error reply, else no
  outcome      read as run control reads the transcript (judges.session_of), in this order:
                 discarded            it ran a shell (Bash or PowerShell): run control throws its work away
                 relaunched           an API error ended it, or it never ended, and a later attempt was given the
                                      same prompt file
                 lost to an API error an API error ended it (Claude Code's error reply, or retries with nothing after
                                      them once Claude Code says it finished or it has been quiet for
                                      judges.LAUNCHER_QUIET seconds), and no later attempt
                 finished             it replied (its last response called no tool), or Claude Code's metadata says so
                 still running        none of these: its transcript has not ended. In a run that stopped, read `end`
                                      against the time the run stopped
               A lead's own agent is never discarded (it may run a shell) nor relaunched (run control does not
               launch it).
  prompt       the prompt file, relative to the register; for a lead's own agent, `lead: <its description>` (from
               Claude Code's metadata file beside the transcript; blank description when there is none)
"""
import csv
import datetime
import io
import json
import os
import pathlib
import re
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import judges  # noqa: E402
import paths  # noqa: E402
import register_layout as layout  # noqa: E402

POINTED = re.compile(re.escape(judges.POINTER).replace(re.escape("{}"), "(.+?)"))


def _when(v):
    try:
        t = datetime.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)


def _utc(t):
    return t.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if t else ""


def pointed_prompt(f, prompts):
    """The prompt file a transcript was given, relative to `prompts` (a normalised path), when its first user message
    is the pointer line of a file under it; else None. Reads only up to the first user message."""
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"user"' not in line:
                continue
            text = judges.first_message(line)
            if text is None:
                continue
            m = POINTED.search(text.strip())
            if not m:
                return None
            target = m.group(1).replace("\\", "/")
            return target[len(prompts) + 1:] if paths.norm(target).startswith(prompts + "/") else None
    return None


FAST_PROMPT = "fast/mapper-prompt.md"  # the fast map's one mapping agent (fast_map.FOLDER / fast_map.PROMPT)
FAST_ROW = "fast mapper"  # its step, and the prompt column's value for it
LEAD_ROW = "lead"  # the run's own session: its row runs from its first line to its last


def step_of(rel):
    """(unit, step) from a prompt file's path relative to prompts/."""
    if rel == FAST_ROW:
        return "", FAST_ROW
    parts = rel.split("/")
    stem = parts[-1][:-3] if parts[-1].endswith(".md") else parts[-1]
    if rel == "first-look-lead.md":  # the first-look helper's own prompt (first_look.LEAD_PROMPT)
        return "", "first-look helper"
    if parts[0] == "first-look" and len(parts) > 1:  # a source reader of the first look, never a code unit's reader
        return stem[len("read-"):] if stem.startswith("read-") else stem, "source reader"
    if parts[0] == "launch":
        m = re.match(r"judges-(.+?)-r(\d+)(?:-|$)", stem)
        if m:
            return m.group(1), f"launcher of judge round {m.group(2)}"
        m = re.match(r"readers-([a-z]+)", stem)
        return "", f"launcher of readers {m.group(1)}" if m else "launcher"
    unit = parts[0] if len(parts) > 1 else ""
    m = re.match(r"r(\d+)-j\d+-", stem)
    if m:
        return unit, f"judge round {m.group(1)}"
    for start, step in (("reread-", "re-read"), ("stop-", "stop fixer"), ("fix", "fixer"), ("retry", "reader retry"),
                        ("read", "reader")):
        if stem.startswith(start):
            return unit, step
    return unit, stem


def run_started(reg):
    """When this run started (_run-state/run-started.json, else the register's or its work folder's), in UTC, or None."""
    reg = pathlib.Path(reg)
    for p in (reg / "_run-state" / "run-started.json", reg / "run-started.json", reg.parent / "run-started.json"):
        try:
            got = json.loads(p.read_text(encoding="utf-8")).get("started")
        except (OSError, ValueError, AttributeError):
            continue
        if got:
            try:
                return datetime.datetime.fromisoformat(got).astimezone(datetime.timezone.utc)
            except ValueError:
                continue
    return None


def measure(f, since=None):
    """The counted columns of one transcript (module docstring); with `since`, only its lines at or after that time
    (the lead's session may have run an earlier run before this one)."""
    agent = model = None
    first = last = prev = None
    gap, gap_err, errors = 0.0, False, 0
    usage = {}
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            is_err = (d.get("type") == "system" and d.get("subtype") == "api_error") or bool(
                d.get("type") == "assistant" and d.get("isApiErrorMessage"))
            t = _when(d["timestamp"]) if d.get("timestamp") else None
            if since is not None and (t is None or t < since):
                continue
            errors += is_err
            agent = agent or d.get("agentId") or None
            if t is not None:
                first = first or t
                if prev is not None and (t - prev).total_seconds() > gap:
                    gap, gap_err = (t - prev).total_seconds(), is_err
                prev = last = t
            m = d.get("message")
            if d.get("type") != "assistant" or d.get("isApiErrorMessage") or not isinstance(m, dict) \
                    or m.get("model") == "<synthetic>":
                continue
            model = model or m.get("model")
            key = m.get("id") or d.get("requestId") or d.get("uuid")
            u = m.get("usage")
            usage[key] = u if isinstance(u, dict) else usage.get(key, {})
    if agent is None:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    agent = json.loads(line).get("sessionId")
                except (ValueError, AttributeError):
                    continue
                if agent:
                    break

    def total(field):
        got = [u[field] for u in usage.values() if isinstance(u.get(field), (int, float))]
        return sum(got) if got else ""

    return {"agent": agent or pathlib.Path(f).stem, "model": model or "", "start": first, "end": last,
            "seconds": int(round((last - first).total_seconds())) if first and last else "",
            "turns": len(usage), "input_tokens": total("input_tokens"), "output_tokens": total("output_tokens"),
            "cache_read_tokens": total("cache_read_input_tokens"),
            "cache_creation_tokens": total("cache_creation_input_tokens"), "api_errors": errors,
            "longest_gap_seconds": int(round(gap)), "gap_ends_on_error": "yes" if gap_err else "no"}


def rows(reg, transcripts=None):
    """One dict per agent attempt (module docstring), ordered by start."""
    reg = pathlib.Path(reg).resolve()
    prompts = paths.norm((reg / layout.PROMPTS).as_posix())
    fast = paths.norm(reg.as_posix())  # the fast map's prompt is fast/mapper-prompt.md, beside prompts/ (fast_map.py)
    try:
        import agents_now
        ids = set(agents_now.session_ids(reg)[0])
    except Exception:  # noqa: BLE001  (the record is for evaluation; an unreadable id list loses no attempt)
        ids = set()
    found, others, leads, mains = [], [], set(), []
    for folder in judges._folders(reg, transcripts):
        for f in sorted(pathlib.Path(folder).rglob("*.jsonl")):
            try:
                target = pointed_prompt(f, prompts)
                rel = pointed_prompt(f, fast) if target is None else None
                if rel and rel.startswith("fast/") and rel.endswith("/mapper-prompt.md") or rel == FAST_PROMPT:
                    target = FAST_ROW  # one mapping agent per service: fast/mappers/<group>/mapper-prompt.md
                if target is None:
                    if f.parent.name == "subagents":
                        others.append(f)
                    elif f.stem in ids:  # the lead: a main session the run has had (its lock, its start marks)
                        mains.append(f)
                    continue
                _, _, done, shell, last, _ = judges.session_of(f)
                found.append((target, measure(f), done, shell, last or "", False))
                if f.parent.name == "subagents":
                    leads.add(f.parent)
            except OSError:
                continue
    if transcripts is None:  # a session started in another folder keeps its main transcript there (judges._folders)
        seen_main = {m.resolve() for m in mains}
        mains += [f for f in judges.run_session_files(reg) if f.resolve() not in seen_main]
    # the lead's own agents: the other subagents of a main session that launched one of this register's attempts, or
    # of any session the run has had (a first-look helper runs before any kit prompt exists)
    began = run_started(reg)
    for f in mains:
        try:
            found.append((LEAD_ROW, measure(f, since=began), False, False, "", True))
        except OSError:
            continue
    for f in others:
        if f.parent not in leads and f.parent.parent.name not in ids:
            continue
        try:
            first, _, done, _, last, _ = judges.session_of(f)
            if first is None or POINTED.search(first.strip()):  # no message yet, or another register's kit agent
                continue
            found.append((f"lead: {_description(f)}", measure(f), done, False, last or "", True))
        except OSError:
            continue
    far = datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)
    found.sort(key=lambda x: (x[1]["start"] or far, x[1]["agent"]))
    tries = {}
    for target, *_ in found:
        tries[target] = tries.get(target, 0) + 1
    seen, out = {}, []
    for target, m, done, shell, last, own in found:
        seen[target] = seen.get(target, 0) + 1
        later = seen[target] < tries[target] and not own
        lost = done and last.startswith(judges.API_STOPPED)
        if shell:
            outcome = "discarded"
        elif later and (lost or not done):
            outcome = "relaunched"
        elif lost:
            outcome = "lost to an API error"
        elif done:
            outcome = "finished"
        else:
            outcome = "still running"
        if target == LEAD_ROW:
            unit, step, outcome = "", LEAD_ROW, "the run's own session"
        else:
            unit, step = ("", "lead's own agent") if own else step_of(target)
        out.append({**m, "unit": unit, "step": step, "attempt": seen[target], "start": _utc(m["start"]),
                    "end": _utc(m["end"]), "outcome": outcome,
                    "prompt": target if own else FAST_PROMPT if target == FAST_ROW else f"{layout.PROMPTS}/{target}"})
    return out


def _description(f):
    """The description Claude Code recorded for a subagent, in the metadata file beside its transcript; else ''."""
    try:
        meta = json.loads(f.with_name(f.stem + ".meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    d = meta.get("description") if isinstance(meta, dict) else None
    return " ".join(str(d).split()) if d else ""


def write(reg, transcripts=None):
    """Rewrite <reg>/job/timings.csv whole (a reader never sees half a file); returns (path, row count). Several
    writers at once (two calls of run control, or this command run on its own) each write a temporary file of their own beside it and rename it into place,
    so the last one wins whole; a rename refused while another holds the file is tried again briefly, then given up
    (that writer's rows are no newer than the next one's)."""
    reg = pathlib.Path(reg).resolve()
    got = rows(reg, transcripts)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=layout.TIMINGS_COLS, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(got)
    path = reg / layout.TIMINGS_CSV
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(buf.getvalue())
        _replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return path, len(got)


REPLACE_TRIES, REPLACE_WAIT = 20, 0.05  # Windows refuses a rename onto a file another process has open


def _replace(tmp, path):
    """Rename `tmp` onto `path`; on PermissionError try again, REPLACE_TRIES times REPLACE_WAIT seconds apart, then
    give up without raising (write removes the temporary file)."""
    for i in range(REPLACE_TRIES):
        try:
            os.replace(tmp, path)
            return True
        except PermissionError:
            if i + 1 < REPLACE_TRIES:
                time.sleep(REPLACE_WAIT)
    return False


def refresh(reg, transcripts=None, why=""):
    """write(), never raising: run control calls it, and the timing record must never stop or change a
    run. A failure is logged to the register's events.log (case.log) and None is returned; nothing is printed. A
    register with no prompts/ folder has launched no agent, so there is nothing to time: nothing is written."""
    try:
        if not (pathlib.Path(reg) / layout.PROMPTS).is_dir():
            return None
        return write(reg, transcripts)
    except Exception as e:  # noqa: BLE001  (the record is for evaluation; the run goes on without it)
        try:
            import case
            case.log(reg, "timings.csv not written", why=why, said=f"{type(e).__name__}: {e}"[:400])
        except Exception:  # noqa: BLE001
            pass
        return None


def main(argv):
    transcripts = None
    if "--transcripts" in argv:
        i = argv.index("--transcripts")
        transcripts = argv[i + 1] if len(argv) > i + 1 else None
        argv = argv[:i] + argv[i + 2:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    got = refresh(argv[0], transcripts, "timings.py run on its own")
    if got is None:
        print(f"{argv[0]}: timings.csv not written (events.log says why)")
        return 0  # the record is for evaluation: a failure to write it is no failure of the command's caller
    path, n = got
    print(f"{path}: {n} agent attempt(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
