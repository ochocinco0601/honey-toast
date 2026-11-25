"""The unit readers and fixers of a split run: their prompts, written for the lead to launch as subagents, or launched
as Claude Code processes.

Usage: python readers.py prompt <register folder> [<unit>...] [--in-scope] [--mode read|retry|fix|reread] [--ws DIR]
                        [--again] [--transcripts DIR]
       python readers.py prompt <register folder> <unit>... --mode stop --reason "<the reason, as printed>"
       python readers.py run <register folder> <workspace> <unit>... [--mode read|retry|fix] [--model ID]

`prompt` (the normal path) writes each agent's prompt to <reg>/prompts/<unit>/<mode>.md, and with
`fix` the unit `flow` gets one fixer per lead table with flagged rows, <reg>/prompts/flow/fix-<table>.md; a unit with
no flagged row gets no fixer. `--in-scope` adds every unit owed a reader for the flow worked now (in_scope: a unit of a
service the go took in whose files.csv is not newer than the go) and names the ones read already. `--mode reread`
writes the re-read of each call merge/unmatched-calls.csv lists, <reg>/prompts/<unit>/reread-<row_id>.md. `--mode
stop --reason` is the route back from the map stop for a reason of the map's inspection that only a reading unit's row
can clear: each unit named gets a fixer given that reason, <reg>/prompts/<unit>/stop-<hash>.md, one
per reason, which changes or adds the unit's rows of this flow from its code, or says the code does not show it. It
gathers
their pointer lines ("Read <file> and do exactly what it says. Reply with one line.") into launcher files under
<reg>/prompts/launch/ (readers-<mode>-<i>.md, at most judges.LAUNCHER_MAX agents each) and prints a count, then one
pointer line per launcher. The lead launches each launcher as a `general-purpose` subagent, which launches its agents
as `bfo-unit-reader` subagents (provenance.READER_TYPE: the kit's agents/bfo-unit-reader.md, whose tools hold no
shell, so a reader, fixer or re-read cannot run one), at most `parallel` at once; the lead keeps at most
judges.launcher_cap launchers running. Claude Code finds that agent only where agents are installed (the project's
`.claude/agents/` or the user's `~/.claude/agents/`), loaded when the session starts: `prompt` refuses, launching
nothing, until the copy Claude Code would use matches the kit's (reader_agent_problem). Readers and fixers share launchers rather than one per unit as judges have: a
launcher per reader would double the subagents running for no gain in context, and the session's limit holds them
all. Every prompt names the workspace (`--ws`, else the register's grandparent) and ends with the tool rule: no shell;
write only with Write and Edit, only under the unit's own folder (a `flow` fixer: only its own table; a re-read: only
the two files it may change).

Run again at any time, `prompt` launches no agent twice (emit, judges.Launches): an agent launched already, or queued
in a launcher still running, is named, not printed. A reader or fixer whose transcript shows a shell, even a read-only
one, fails its unit (provenance.py): its writes are not counted and its Reads credit nothing. `prompt ... --again`
relaunches it: each table it wrote is first put back as the unit's clean writers left it (on a unit an earlier flow
read, its finished rows with their recorded corrections; files.csv removed), then the prompt is written afresh. The
relaunched agent's writes then account for the unit. `--again` also says the session that launched the agents is gone
(a crash, a restart): every agent still named running is launched afresh, never one that finished.

`run` launches each reader as `claude -p` with the working folder the workspace (so its transcript lands where the reading check
finds it), given the reader's agent definition (agents/bfo-unit-reader.md), its unit from units/units.csv, its folder
<reg>/units/<unit>/, and the split run's file formats. `retry` adds the output of the unit's failed read check from
job/jobs.csv; `fix` adds the unit's flagged rows and the judges' reasons from judging/judgements.csv. The model is the
one passed with --model (the lead's own), else the definition's if it names one, else Claude Code's default. Each
reply is kept in <reg>/replies/<unit>-<mode>.json. `parallel` in run-settings.json sets how many run at once."""
import json
import pathlib
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
AGENT = HERE / "agents" / "bfo-unit-reader.md"
FORMATS = HERE / "split-run-formats.md"
ALLOWED = "Read,Grep,Glob,Write,Edit"
DISALLOWED = "Bash,PowerShell,Agent,WebFetch,WebSearch"
sys.path.insert(0, str(HERE))
import judges  # noqa: E402  (the agent definition's frontmatter and body)
import settings  # noqa: E402
import tables  # noqa: E402
import register_layout as layout  # noqa: E402
import reading_check  # noqa: E402  (owed_files: the files a unit owes, listed in its reader's prompt)
import provenance  # noqa: E402  (READER_TYPE)


def unit_row(reg, unit):
    p = pathlib.Path(reg) / layout.UNITS_CSV
    for r in tables.dicts(p):
        if r.get("unit") == unit:
            return r
    raise SystemExit(f"no unit {unit!r} in {p}")


def formats():
    p = FORMATS
    return ("## The file formats (split-run-formats.md)\n\n" + p.read_text(encoding="utf-8")) if p.is_file() else ""


def _flagged(reg, unit):
    """The unit's flagged rows from judging/judgements.csv, each with `as_judged`: the round and the content (row hash)
    its flagging verdicts judged. A fixer is the fix of its rows as the judges flagged them, so a row flagged again
    after its fixer finished, in the next round or at the map stop, is another fixer's."""
    got = [dict(r) for r in tables.dicts(pathlib.Path(reg) / layout.JUDGEMENTS_CSV)
           if r.get("unit") == unit and r.get("state") == "flagged"]
    try:
        current = {(r["table"], r["key"]): r for r in judges.rows(reg, unit)[0]} if got else {}
    except (OSError, ValueError, KeyError):
        current = {}
    for r in got:
        row, rnd = current.get((r.get("table"), r.get("row"))), int(r.get("round") or 0)
        hashes = (sorted({(v or {}).get("row_hash") or p.stem.rsplit("-", 1)[-1]
                         for _, p, v in judges._any_hash(reg, row, rnd) if v is None or v["verdict"] != "says"})
                  if row and rnd else [])
        r["as_judged"] = f"round {r.get('round', '')}" + (f", content {' '.join(hashes)}" if hashes else "")
    return got


def _tail(where):
    return ["## Tools", "", judges.NO_SHELL.format(where=where) + " Read the code and the register with Read, Grep "
            "and Glob.", "", "Reply with one line. " + judges.REPLY_TAIL]


def flow_fix_prompt(reg, table, rows, ws=None):
    """The prompt of the fixer of one lead table's flagged rows (the unit `flow`: the register's root tables, written
    by the lead), which edits only that table."""
    import go
    reg = pathlib.Path(reg).resolve()
    path = (reg / f"{table}.csv").as_posix()
    keys = go.ROW_KEYS.get(table)
    key = (f"its key columns ({', '.join(keys)})" if keys else "its first column")
    out = ["# Fix flagged rows of one table of a business flow map", "",
           "Independent judges read each row of the map against the code it cites, three of them per row. The rows "
           "below were flagged: at least one judge found the cited lines do not show what the row claims. Fixed, they "
           "are judged again; still flagged after that, they are labelled `disputed:` and never shown as fact.", "",
           judges.ws_line(judges.workspace(reg, ws)), "",
           f"Table: {path} (a row is named by {key})", "", "Rows and the judges' reasons:", ""]
    out += [f"- row {r['row']} (flagged in {r['as_judged']}): {r.get('reasons', '')}" for r in rows]
    out += ["", "For each row: open its cited lines with Read, then edit the row in place with Edit so it says only "
            "what the cited lines show: narrow the claim, or correct the citation. You may instead relabel the claim "
            "`proposed:`, drop a citation, or withdraw the row (delete it); say which in your reply. Never change "
            f"{key}: a row whose key changes counts as withdrawn and a new row, judged afresh. Change no other row.", ""]
    return "\n".join(out + _tail(f"to your own table {path}"))


def owed_section(owed):
    """The prompt's list of the files the unit owes (reading_check.owed_files), the list the reading check holds the
    reader to."""
    return ["## The files you owe", "",
            f"Open each of these with Read in full and list each in {layout.FILES_CSV}; it is what the reading check "
            "holds you to. Other files under your paths (generated or build output, vendored code, binary, lock and "
            "minified files" + ("" if reading_check.OWE_TESTS else ", test code") + ") are not owed: open one only "
            f"where it settles what the code does, and you may list it in {layout.FILES_CSV} as `not relevant` with "
            "the reason"
            + ("" if reading_check.OWE_TESTS else " (for a test file: `test code`). Do not read test code in full: "
               "consult a test only where a behaviour in the code above is unclear") + ".", ""] \
        + [f"- {r}" for r in sorted(owed)] + [""]


def reader_agent_problem(reg, ws=None):
    """None when the reader agent Claude Code would launch by the name READER_TYPE is the kit's own definition; else
    what to do. Claude Code takes a project's `.claude/agents/` (the folder the session started in: the register's
    grandparent by the kit's layout, or a folder above it) before the user's (CLAUDE_CONFIG_DIR, else `~/.claude`)."""
    return judges.agent_problem(reg, provenance.READER_TYPE, AGENT, "reader")


def workspace_problem(reg, units, ws=None):
    """Why readers of `units` cannot be launched: a path of theirs (units.csv `paths`) not under the folder their
    prompts name, so every read of it would fail and the reader be thrown away; None when all are there."""
    w = judges.workspace(reg, ws)
    f = pathlib.Path(reg) / layout.UNITS_CSV
    rows = {r.get("unit"): r for r in tables.dicts(f)} if f.is_file() else {}
    paths = [p for u in units for p in ((rows.get(u) or {}).get("paths") or "").split(";") if p.strip()]
    missing = judges.missing_under(w, paths)
    return judges.where_to_say(w, missing) if missing else None


MERGE_FIX = "merge-fix.md"  # a reader relaunched once with the merge's reason for refusing its unit's rows


def prompt(reg, unit, mode="read", ws=None, reason=None):
    reg = pathlib.Path(reg).resolve()
    u = unit_row(reg, unit)
    body = judges.agent_body(AGENT)
    plist = [p.strip() for p in u.get("paths", "").split(";") if p.strip()]
    paths = "; ".join(plist)
    owed, _ = reading_check.owed_files(judges.workspace(reg, ws), plist)
    out = [body, "", "## Your unit", "",
           judges.ws_line(judges.workspace(reg, ws)),
           f"Unit: {unit}",
           f"Deployable: {u.get('deployable', '')}",
           f"Paths it covers, from the workspace root: {paths}",
           f"Size: {len(owed)} files you owe; {u.get('reader_facts', '')} code-reader findings",
           f"Register folder: {reg}",
           f"Your folder (write only here): {layout.unit_dir(reg, unit)}",
           f"The flow and its steps: {reg / 'flows.csv'}, {reg / 'lifecycle.csv'}, {reg / 'stages.csv'}, "
           f"{reg / 'steps.csv'}; the plan: {reg / 'PLAN.md'}; the code reader's findings: {reg / 'fact-base.json'}",
           ""] + owed_section(owed)
    if mode in ("read", "retry", "fix"):
        import path_reading  # a flow read by stage reads the path of its stages taken further (run-settings `reading`)
        out += path_reading.path_block(reg, unit, judges.workspace(reg, ws))
    if mode == "retry" and reason:
        out += ["## What the merge refused in your unit's rows", "",
                "The merge of the unit folders refused these rows of your unit. Put each right in your unit's tables "
                "with Edit, from the code (a row id used once only, a part named as an element of the unit), keeping "
                "every other row as it is:", "", reason, ""]
    elif mode == "retry":
        why = [r.get("reason", "") for r in tables.dicts(reg / layout.JOBS_CSV)
               if r.get("item") == unit and r.get("step") == "read"]
        out += ["## The check that failed", "", "\n".join(w for w in why if w) or "(no output recorded)", ""]
    if mode == "fix":
        rows = _flagged(reg, unit)
        out += ["## Rows to fix", ""] + [f"- {r['table']} {r['row']} (flagged in {r['as_judged']}): "
                                         f"{r.get('reasons', '')}" for r in rows] + [""]
    out += [formats(), ""] + _tail(f"under your own unit folder {layout.unit_dir(reg, unit).as_posix()}/")
    return "\n".join(out)


def stop_prompt(reg, unit, reason, ws=None):
    """The prompt of a unit's fixer for a reason of the map's inspection (the map stop) that only the unit's rows can
    clear: it reads the unit's code and changes or adds the unit's rows of this flow, under its own
    folder only, or changes nothing and says the code does not show it."""
    base = prompt(reg, unit, "read", ws)
    head, tail = base.split("## The file formats", 1) if "## The file formats" in base else (base, "")
    ask = ["## What the map's inspection asks of this unit", "",
           "You are a fixer of one reason the map's inspection gave, not the unit's reader: do only what \"Putting "
           "right a reason of the map's inspection\" above says, for this reason. You need not read the whole unit.",
           "", f"> {reason}", "",
           "Where the code shows what the reason asks for, put it right in your unit's tables with Edit (or Write for "
           "a table not yet there): change a row, or add a row of this flow under a new row_id, each citing the lines "
           "that show it. Where it does not, change nothing and say so.", ""]
    return head + "\n".join(ask) + ("\n## The file formats" + tail if tail else "")


def _fixed_rows(text):
    """The rows a fixer's prompt names, as the judges flagged them (its `- <row> (flagged in <round, content>):
    <reasons>` lines, reasons set aside): two fix prompts naming the same rows flagged by the same verdicts are one
    fixer's, whatever a rerun of `collect` did to the reasons; the same rows flagged again, in a later round or at the map
    stop, are another's."""
    return sorted(l.split(": ", 1)[0] for l in text.splitlines() if l.startswith("- ") and ": " in l)


def reread_prompt(reg, call, ws=None):
    """The prompt of the re-read of one call the merge left unmatched (a row of merge/unmatched-calls.csv), which
    writes only the calling unit's calls.csv and the called unit's operations.csv. Its opening line names
    the session's kind, so neither the agent nor a reader of its transcript takes it for a unit's reader."""
    reg = pathlib.Path(reg).resolve()
    unit, rid = call["call"].split("/", 1)
    a = unit_row(reg, unit)
    to = (call.get("to_unit") or "").strip()
    listed = {(r.get("unit") or "").strip() for r in tables.dicts(reg / layout.UNITS_CSV)}
    b = unit_row(reg, to) if to in listed else None
    calls = (layout.unit_dir(reg, unit) / "calls.csv").as_posix()
    ops = (layout.unit_dir(reg, to) / "operations.csv").as_posix() if b else None

    def where(u):
        return "; ".join(p for p in u.get("paths", "").split(";") if p)

    out = [judges.agent_body(AGENT), "", "## Your call", "",
           "You are a re-read of one unmatched call, not the reader of a unit: do only what \"Re-reading an unmatched "
           "call\" above says, for this one call.", "",
           judges.ws_line(judges.workspace(reg, ws)),
           f"Call: {call['call']} (row `{rid}` of {calls})",
           f"Calling unit: {unit}; paths from the workspace root: {where(a)}",
           (f"Called unit: {to}; paths from the workspace root: {where(b)}; its operations: {ops}" if b else
            f"Called unit: {to or '(none named)'}, not a unit in units.csv: correct the row, never dispute it"),
           f"Protocol: {call.get('protocol', '')}; operation: {call.get('operation', '')}; "
           f"source: {call.get('source', '')}",
           f"Why the merge left it unmatched: {call.get('why', '')}",
           f"Register folder: {reg}", "",
           formats(), ""]
    return "\n".join(out + _tail(f"to {calls} and {ops}" if ops else f"to {calls}"))


def in_scope(reg):
    """(the reading units owed a reader for the flow worked now, the ones read for it already): the units of a service
    the go took in (scope.json `services_in`; every unit when the go names none), or one surveyed after the go that it
    did not leave out (code got for an external dependency, go.services_read), each read for
    this flow once its files.csv was written after this flow's go (scope.json `given`)."""
    import datetime
    reg = pathlib.Path(reg).resolve()
    import go
    took = go.services_read(reg)
    since = judges.go_given(reg)
    owed, done = [], []
    for r in tables.dicts(reg / layout.UNITS_CSV):
        u = (r.get("unit") or "").strip()
        if not u or (took is not None and ((r.get("deployable") or "").strip() or u).lower() not in took):
            continue
        f = layout.unit_dir(reg, u) / layout.FILES_CSV
        read = f.is_file() and (since is None or datetime.datetime.fromtimestamp(
            f.stat().st_mtime, datetime.timezone.utc) >= since)
        (done if read else owed).append(u)
    return owed, done


KINDS = {"read": "reader", "retry": "reader", "fix": "fixer", "reread": "re-read", "stop": "fixer"}
HELD = {"queued": "queued in a launcher still running", "still running": "launched already, still running",
        "finished": "launched already, finished", "ran a shell": "launched already, ran a shell (relaunch with --again)",
        "gave up": "stopped on an API error each time it was launched, and launched afresh as many times as "
                   f"{layout.SETTINGS} `relaunches` allows: not launched again"}


def emit(reg, units, mode="read", ws=None, again=False, transcripts=None, reason=None):
    """Write each agent's prompt file and a launcher of their pointer lines; return the lines to print (the agents held
    and why, a count, then one pointer line per launcher). A reading unit's prompt is <reg>/prompts/<unit>/<mode>.md;
    with `fix`, a unit with no flagged row gets none, and the unit `flow` gets one fixer per lead table with flagged
    rows, <reg>/prompts/flow/fix-<table>.md; with `reread`, every call merge/unmatched-calls.csv lists (of the units
    named, or all when none is) gets <reg>/prompts/<unit>/reread-<row_id>.md; with `stop`, each unit named gets a fixer
    given `reason`, <reg>/prompts/<unit>/stop-<hash of the reason>.md; with `retry` and `reason` (a text, or one per
    unit), the reader relaunched with what the merge refused in its rows, <reg>/prompts/<unit>/merge-fix.md.

    Run again at any time, it launches no agent twice (judges.Launches): an agent queued in a launcher still
    running, or launched and still running, or finished, is named and not launched; one still running whose launcher
    has replied stopped without replying, and is launched afresh; so is one an API error ended, at most `relaunches`
    times (run-settings.json), after which it is named as given up. A fixer given other rows is another fixer; one given
    the same rows with other reasons is the same. `again` says the session that launched them is gone (a
    crash, a restart): every agent still named running, or that ran a shell, is launched afresh, never one that
    finished. With `again`, a reading unit whose reader or fixer ran a shell first has its tables put back as its clean
    writers left them (provenance.undo_breaches), so the relaunched agent can pass. With `again`, the run's timing
    record is rewritten first, before anything is undone or relaunched (timings.refresh)."""
    reg = pathlib.Path(reg).resolve()
    if again:
        import timings
        timings.refresh(reg, transcripts, "readers.py prompt --again")
    lines, said = [], []
    seen = judges.Launches(reg, transcripts, again)
    kind = KINDS[mode]

    def agent(path, text, name):
        launch, state = seen.decide(path, text, (lambda a, b: _fixed_rows(a) == _fixed_rows(b))
                                    if mode == "fix" else None)
        if not launch:
            said.append(f"{name}: {kind} {HELD[state]}" + (
                " (a row it fixed that is flagged again once judged again gets a fixer of its own)"
                if mode == "fix" and state == "finished" else
                " for this reason: if the map's inspection still gives it, the code does not show it; name it to the "
                "person as still open" if mode == "stop" and state == "finished" else ""))
            return
        if state == "stopped":
            said.append(f"{name}: {kind} stopped without replying (its launcher has replied or stopped): launched afresh")
        if state == "errored":
            said.append(f"{name}: {kind} stopped on an API error before it finished: launched afresh")
        lines.append(judges.write_prompt(path, text))

    for u in units:
        if again and u != "flow":
            undone = provenance.undo_breaches(reg, u, transcripts)
            if undone:
                said.append(f"{u}: relaunched over {', '.join(undone)} (ran a shell; what it wrote is undone)")
    if mode == "reread":
        for c in tables.dicts(reg / layout.UNMATCHED_CSV):
            unit, rid = c["call"].split("/", 1)
            if not units or unit in units or (c.get("to_unit") or "").strip() in units:
                agent(layout.prompts_dir(reg, unit) / f"reread-{judges.name_key(rid)}.md", reread_prompt(reg, c, ws),
                      c["call"])
        units = []
    for u in units:
        if mode == "fix" and u == "flow":
            by = {}
            for r in _flagged(reg, "flow"):
                by.setdefault(r["table"], []).append(r)
            for t, rs in sorted(by.items()):
                agent(layout.prompts_dir(reg, "flow") / f"fix-{t}.md", flow_fix_prompt(reg, t, rs, ws), f"flow {t}")
            continue
        unit_row(reg, u)
        if mode == "stop":
            import hashlib
            key = hashlib.sha256(" ".join((reason or "").split()).encode("utf-8")).hexdigest()[:12]
            agent(layout.prompts_dir(reg, u) / f"stop-{key}.md", stop_prompt(reg, u, reason, ws), u)
            continue
        if mode == "fix" and not _flagged(reg, u):
            continue
        if mode == "retry" and reason:
            why = reason.get(u) if isinstance(reason, dict) else reason
            agent(layout.prompts_dir(reg, u) / MERGE_FIX, prompt(reg, u, mode, ws, why), u)
            continue
        agent(layout.prompts_dir(reg, u) / f"{mode}.md", prompt(reg, u, mode, ws), u)
    pointers = judges.launchers(reg, f"readers-{mode}", [("", lines)] if lines else [], keep=seen.running,
                                agent_type=provenance.READER_TYPE)
    return said + seen.ended_lines(f"readers-{mode}") + [f"{len(lines)} {kind}(s) to launch in {len(pointers)} launcher(s); keep at most "
                   f"{judges.launcher_cap(reg)} launcher(s) running at once"] + pointers


def command(text, model=None):
    cmd = ["claude", "-p", text, "--output-format", "json",
           "--allowedTools", ALLOWED, "--disallowedTools", DISALLOWED]
    return cmd + (["--model", model] if model else [])


def _launch(cmd, cwd):
    cmd = [shutil.which(cmd[0]) or cmd[0]] + cmd[1:]
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=5400).stdout
    except subprocess.TimeoutExpired:
        return json.dumps({"result": "timed out"})


def run(reg, ws, units, mode="read", model=None, launcher=None):
    reg = pathlib.Path(reg).resolve()
    meta = judges.agent_meta(AGENT)
    if not model and meta.get("model", "inherit") not in ("", "inherit"):
        model = meta["model"]
    jobs = [(u, command(prompt(reg, u, mode, ws), model)) for u in units]
    for u in units:
        layout.unit_dir(reg, u).mkdir(parents=True, exist_ok=True)
    (reg / layout.REPLIES).mkdir(exist_ok=True)
    cwd = str(pathlib.Path(ws).resolve())
    par = max(1, settings.number(settings.load(reg), "parallel"))

    def one(job):
        u, cmd = job
        out = (launcher or _launch)(cmd, cwd)
        (reg / layout.REPLIES / f"{u}-{mode}.json").write_text(out or "", encoding="utf-8")

    with ThreadPoolExecutor(par) as ex:
        list(ex.map(one, jobs))
    return len(jobs)


def _opt(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    argv = list(argv)
    mode = _opt(argv, "--mode", "read")
    model = _opt(argv, "--model")
    ws = _opt(argv, "--ws")
    transcripts = _opt(argv, "--transcripts")
    reason = _opt(argv, "--reason")
    if mode == "stop" and not (reason or "").strip():
        sys.exit("--mode stop needs --reason \"<the reason of the map's inspection, as printed>\"")
    again, scoped = "--again" in argv, "--in-scope" in argv
    argv = [a for a in argv if a not in ("--again", "--in-scope")]
    if len(argv) >= 2 and argv[0] == "prompt" and (len(argv) >= 3 or scoped or mode == "reread"):
        import guard  # the order of mapping, held here whichever command was typed (guard.py)
        problem = guard.require(argv[1], mode, units=argv[2:]) or reader_agent_problem(argv[1], ws)
        if problem:
            print(f"REFUSED: {problem}. Nothing was launched.", file=sys.stderr)
            return 2
        units, said = argv[2:], []
        if scoped:
            owed, done = in_scope(argv[1])
            units = list(dict.fromkeys(units + owed))
            said = [f"{u}: read for this flow already (its files.csv is newer than the go)" for u in done]
        problem = workspace_problem(argv[1], units, ws)
        if problem:
            print(f"REFUSED: {problem}. Nothing was launched.", file=sys.stderr)
            return 2
        print("\n".join(said + emit(argv[1], units, mode, ws, again, transcripts, reason)))
        return 0
    if len(argv) >= 4 and argv[0] == "run":
        import run_lock  # the register is written by one run at a time
        run_lock.guard(argv[1])
        import guard
        problem = guard.require(argv[1], mode, units=argv[3:]) or workspace_problem(argv[1], argv[3:], argv[2])
        if problem:
            print(f"REFUSED: {problem}. Nothing was launched.", file=sys.stderr)
            return 2
        n = run(argv[1], argv[2], argv[3:], mode, model)
        print(f"{n} reader(s) finished; replies in {pathlib.Path(argv[1]) / layout.REPLIES}")
        return 0
    sys.exit(__doc__)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
