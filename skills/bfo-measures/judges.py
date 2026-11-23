"""Judge every row of a reading unit three times, collect the verdicts, and say whether the judging really happened.

Usage: python judges.py rows <reg> <unit>
       python judges.py run <reg> <ws> <unit> --round N [--rows all|flagged] [--model ID] [--again]
                        [--set-aside "<the person's reason>"] [--transcripts DIR]
       python judges.py emit <reg> <unit> --round N [--rows all|flagged] [--ws DIR] [--again] [--transcripts DIR]
       python judges.py collect <reg> [--transcripts DIR]
       python judges.py --check <reg> <unit> [--round N] [--transcripts DIR]
       python judges.py --fix-check <reg> <unit> [--round N] [--transcripts DIR]

`emit` (the normal path) writes the prompt of every judge of the round whose verdict file is not yet on
disk to <reg>/prompts/<unit>/<verdict file stem>.md, gathers their pointer lines ("Read <file> and do exactly what it
says. Reply with one line.") into launcher files under <reg>/prompts/launch/ (judges-<unit>-r<n>[-<table>]-<i>.md, at
most LAUNCHER_MAX agents each; the unit `flow` one or more per lead table), and prints a count, then one pointer line
per launcher. The lead launches each launcher as a `general-purpose` subagent, which launches its judges as
`bfo-row-judge` subagents (the kit's judge agent, with no shell), at most `parallel` at once; the lead keeps at most the count line's number of launchers
running (launcher_cap). Run again at any time, it launches no judge twice (Launches): it prints only judges
whose verdict is not on disk and that were never launched, or that stopped (still running when their launcher
replied); a launcher still running is left as it is and its judges held. `--again` is for after a crash or restart:
the agents still named running died with the session that launched them, and are launched afresh; a finished one
never is. (`run --again` is the `claude -p` path's: it removes the round's failing verdict files first.)

Every row of a unit that cites code gets `judges` judges (run-settings.json, default 3): each a fresh agent (a
subagent from `emit`, or under `run` a Claude Code process, `claude -p`, cwd the workspace <ws>) given the judge's agent definition (agents/bfo-row-judge.md) and one row,
which opens the cited code with Read and writes its verdict, and nothing else, to
`judging/<unit>/r<round>-j<n>-<table>-<name key>-<row hash>.csv`. A row any judge flags is fixed by its reader and
judged again in the next round, only the flagged rows; still flagged in round `judge_rounds` (default 2), it is
disputed, and `collect` puts `disputed: ` at the start of its claim cell. Rounds are counted by the row's identity
(unit, table, key); the row hash in the name only says whether a verdict is current, so an edited row has no current
verdict and a fixed row keeps its place in the rounds. `run --again` first removes the round's verdict files that fail
the check (a judge that ran a shell, say), so their judges are launched afresh onto the same paths: the new judge
never reads the old verdict, and the Write tool would refuse to overwrite a file it has not read. Formats:
split-run-formats.md.

`--check` reads the verdict files and Claude Code's own transcripts (found as reading_check.py finds them): for the
unit's latest round, every row judged in it has `judges` verdict files at its current hash, each with an effective
writer (the latest session whose successful Write equals the file on disk; other writers are named superseded), a
different session per verdict, that wrote nothing else, ran no shell, and opened every cited line with Read. Verdicts
at an older hash are listed as stale, never failed. A superseded writer that was itself a clean judge of a well-formed
verdict fails the check (a clean verdict was replaced). Every row outside the round's scope is checked at its own
latest round, at its current content, so an edited, added or re-keyed row is not done until judged. A Write or Edit
whose tool result is an error is not a write. It reports the model(s) the judges ran on. `--fix-check`: every row flagged in a round before the last has the next round's verdicts, passing the same check,
and every disputed row carries its label. Exit status 0 only when the check passes. `run` passes `--model` only when
given one (the model the lead session runs on) or when the agent definition names one other than `inherit`."""
import csv
import datetime
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reading_check as rc  # noqa: E402
import paths  # noqa: E402
import tables  # noqa: E402
import settings as run_settings  # noqa: E402
import register_layout as layout  # noqa: E402

AGENT = pathlib.Path(__file__).resolve().parent / "agents" / "bfo-row-judge.md"
COUNTS = ("judges", "judge_rounds", "parallel")  # the settings this module reads
VERDICT_FIELDS = layout.VERDICT_COLS
HEADER = ",".join(VERDICT_FIELDS)
JUDGEMENT_FIELDS = layout.JUDGEMENT_COLS
VERDICTS = {"says", "does not say", "unclear"}
CLAIMS = ("purpose", "activity", "operation", "name", "move", "failure", "measure")
NOT_ROWS = {"sources", "how-made", "survey", "re-read", "re-read-history", "about"}
# the unit `flow`: mapping's lead tables (bfo-mapping/SKILL.md's outputs), never the measures step's
FLOW_TABLES = ("flows", "lifecycle", "stages", "steps", "set-aside", "agent-system", "capabilities", "step-impact",
               "case-attributes")
MERGED = {"subjects", "participation"}  # rewritten by merge.py from the units, which are judged in their own folders
ALLOWED = "Read,Grep,Glob,Write"
DISALLOWED = "Bash,PowerShell,Edit,Agent,WebFetch,WebSearch"
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
DISPUTED = "disputed: "
NAME_KEY_MAX = 40  # a longer key is named by its own hash, so the verdict path stays under Windows' 260 characters
LAUNCHER_MAX = 150  # agents one launcher holds: its context grows with each agent it holds
POINTER = "Read {} and do exactly what it says. Reply with one line."
NO_SHELL = "Use no shell (no Bash, no PowerShell). Write only with the Write and Edit tools, and only {where}."


def settings(reg):
    """The run's counts. A fast map is checked selectively (selective.py): one judge per row, one round."""
    s = run_settings.load(reg)
    got = {k: run_settings.number(s, k) for k in COUNTS}
    if s.get("mapping") == "fast":
        got["judges"], got["judge_rounds"] = 1, 1
    return got


# ---- the agent definition ----

def _split_agent(path=None):
    text = pathlib.Path(path or AGENT).read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---\s*\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"{path or AGENT}: no frontmatter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def agent_meta(path=None):
    return _split_agent(path)[0]


def agent_body(path=None):
    return _split_agent(path)[1]


# ---- rows ----

def _strip(v):
    return v[len(DISPUTED):] if v.startswith(DISPUTED) else v


def make_row(unit, table, key, header, cells, path=None, index=None):
    seen, cites = set(), []
    for c in rc.cited_in(" ".join(cells)):
        if c[1] is None:  # a file named in prose: the register cites code as path:line or path:first-last
            continue
        if c not in seen:
            seen.add(c)
            cites.append(c)
    claim = next((h for h in CLAIMS if h in header), header[1] if len(header) > 1 else header[0])
    return {"unit": unit, "table": table, "key": key, "header": list(header), "cells": list(cells), "cited": cites,
            "citations": "; ".join(_cite(p, a, b) for p, a, b in cites),
            "claim": claim, "path": path, "index": index, "hash": row_hash(cells)}


def _hash12(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def row_hash(cells):
    """12 hex characters of the row's cells with `disputed: ` stripped, so the label collect adds never makes a verdict
    stale."""
    return _hash12(json.dumps([_strip(c) for c in cells], ensure_ascii=False))


def _cite(p, a, b):
    return p + (f":{a}" + (f"-{b}" if b != a else "") if a else "")


def _tables(reg, unit):
    """The unit's tables to judge. The unit `flow` is the lead's: an allowlist of mapping's lead tables at the root
    (FLOW_TABLES), and the lead's own subjects and participation rows (merge/lead-rows/), never the measures step's
    tables nor the merged root subjects and participation."""
    reg = pathlib.Path(reg)
    if unit == "flow":
        got = [reg / f"{t}.csv" for t in FLOW_TABLES] + [reg / layout.LEAD_ROWS / f"{t}.csv" for t in sorted(MERGED)]
        return [p for p in got if p.is_file()]
    return [p for p in sorted(layout.unit_dir(reg, unit).glob("*.csv")) if p.name != layout.FILES_CSV]


def _key(unit, table, header, cells, col):
    if unit == "flow":
        import go
        if table in go.ROW_KEYS:
            return go.row_key(table, {h: _strip(c) for h, c in zip(header, cells)})
    return _strip(cells[col])


def rows(reg, unit):
    """(judgeable rows of the unit of the flow worked now, how many of those rows cite no code). A finished flow's row
    is never judged again (finished)."""
    reg = pathlib.Path(reg).resolve()
    done = finished(reg, unit)
    every = [r for r in all_rows(reg, unit) if r["index"] not in done.get(r["path"], ())]
    return [r for r in every if r["cited"]], sum(1 for r in every if not r["cited"])


def finished(reg, unit):
    """{table path: {row index}} of the unit's rows that are a finished flow's: rows the latest finished flow's judged
    snapshot (earlier-flows/<id>/judged/) holds as they are now, `disputed: ` labels set aside. The snapshot holds the
    rows as that flow finished; a row a correction changed since is judged again. A unit row is matched by row_id (provenance.current_rows); a row of the unit `flow` by its whole
    content, as many times as the snapshot holds it."""
    import provenance  # it imports this module
    reg = pathlib.Path(reg).resolve()
    snap = provenance.snapshot_dir(reg)
    if snap is None:
        return {}
    out = {}
    if unit != "flow":
        current = set(provenance.current_rows(reg, unit))
        for r in all_rows(reg, unit):
            ident = (r["table"], _strip(r["cells"][r["header"].index("row_id")]) if "row_id" in r["header"] else "")
            if ident not in current:
                out.setdefault(r["path"], set()).add(r["index"])
        return out
    import go
    for p in _tables(reg, "flow"):
        lead = p.parent.name == pathlib.Path(layout.LEAD_ROWS).name
        kept = snap / (layout.LEAD_ROWS if lead else "") / p.name
        if not kept.is_file():
            continue
        _, old = go.table_rows(kept.parent, p.stem)  # as the flow finished: a correction since is judged again
        pool = Counter(tuple(sorted((c, _strip(v or "")) for c, v in r.items() if c is not None))
                       for r in old)
        header, body = tables.grid(p)
        for i, cells in enumerate(body):
            cells = cells + [""] * (len(header) - len(cells))
            k = tuple(sorted((c, _strip(v or "")) for c, v in zip(header, cells)))
            if pool[k] > 0:
                pool[k] -= 1
                out.setdefault(p, set()).add(i)
    return out


def all_rows(reg, unit):
    """Every row of the unit's tables, cited or not, as make_row makes them."""
    out = []
    for p in _tables(reg, unit):
        header, body = tables.grid(p)
        if not header:
            continue
        col = header.index("row_id") if unit != "flow" and "row_id" in header else 0
        count = Counter()
        for i, cells in enumerate(body):
            cells = cells + [""] * (len(header) - len(cells))
            base = _key(unit, p.stem, header, cells, col)
            count[base] += 1
            key = base if count[base] == 1 else f"{base}#{count[base]}"
            out.append(make_row(unit, p.stem, key, header, cells, p, i))
    return out


# ---- the round record: the rows as each round judged them ----

RECORD_COLS = ["unit", "table", "row", "hash", "header", "cells"]
FIX_CLASSES = ("claim narrowed", "citation changed", "relabelled proposed", "citation dropped", "withdrawn",
               "unchanged")


def record_path(reg, unit, rnd):
    return layout.judging_dir(pathlib.Path(reg).resolve(), unit) / f"r{rnd}-rows.csv"


def read_record(reg, unit, rnd):
    """{(table, row): record row} of judging/<unit>/r<rnd>-rows.csv, or None when there is none."""
    p = record_path(reg, unit, rnd)
    if not p.is_file():
        return None
    return {(r["table"], r["row"]): r for r in tables.dicts(p)}


def write_record(reg, unit, rnd, todo):
    """Record every row in the round's scope, with its cells and hash. A row already recorded keeps its record once any
    verdict of the round names it (the before-state its fix is classified from); before that, it is recorded as it is
    now."""
    old = read_record(reg, unit, rnd) or {}
    for row in todo:
        if (row["table"], row["key"]) in old and _any_hash(reg, row, rnd):
            continue
        old[(row["table"], row["key"])] = {"unit": unit, "table": row["table"], "row": row["key"],
                                           "hash": row["hash"], "header": json.dumps(row["header"]),
                                           "cells": json.dumps(row["cells"], ensure_ascii=False)}
    p = record_path(reg, unit, rnd)
    p.parent.mkdir(parents=True, exist_ok=True)
    tables.write(p, RECORD_COLS, list(old.values()), lineterminator="\n")


def record_problems(reg, unit, rnd):
    """The round record checked against the judges' own files: each recorded row's cells hash to its recorded hash,
    and that hash is one its round's verdict files carry in their `row_hash` column (they are written by the judges,
    the record and the file names by the lead's script)."""
    got = read_record(reg, unit, rnd)
    out = []
    for (table, key), r in sorted((got or {}).items()):
        try:
            cells = json.loads(r.get("cells") or "[]")
        except ValueError:
            cells = None
        tag = f"round record r{rnd}-rows.csv: {table} {key}"
        if not isinstance(cells, list) or row_hash(cells) != r.get("hash"):
            out.append(f"{tag}: its cells do not hash to its recorded hash (the record was edited)")
            continue
        hashes = {v["row_hash"] if v else p.name[-len("0123456789ab.csv"):-len(".csv")]
                  for _, p, v in _any_hash(reg, {"unit": unit, "table": table, "key": key}, rnd)}
        if hashes and r["hash"] not in hashes:
            out.append(f"{tag}: recorded at a content its round-{rnd} verdicts never judged (the record was edited)")
    return out


def flagged_ids(reg, unit, rnd):
    """[(table, row)] the round's verdict files flag, read from the files' own columns."""
    out = []
    for p in round_files(reg, unit, rnd):
        v = read_verdict(p)
        if v is not None and v["round"] == str(rnd) and v["verdict"] != "says" and (v["table"], v["row"]) not in out:
            out.append((v["table"], v["row"]))
    return out


def classify_fixes(reg, unit, rnd):
    """{(table, row): class} of every row the round flagged, from its recorded cells and the row as it is now: claim
    narrowed, citation changed, relabelled proposed, citation dropped, withdrawn (no row of that identity now, a key
    changed included), unchanged; or "not classified: no round record". Relabels, dropped citations and withdrawals
    are never counted as fixed."""
    rec = read_record(reg, unit, rnd)
    now = {(r["table"], r["key"]): r for r in all_rows(reg, unit)}
    out = {}
    for ident in flagged_ids(reg, unit, rnd):
        if rec is None or ident not in rec:
            out[ident] = "not classified: no round record"
            continue
        before = [_strip(c) for c in json.loads(rec[ident]["cells"])]
        b = make_row(unit, ident[0], ident[1], json.loads(rec[ident]["header"]), before)
        a = now.get(ident)
        if a is None:
            out[ident] = "withdrawn"
        elif b["cited"] and not a["cited"]:
            out[ident] = "citation dropped"
        elif (_strip(a["cells"][a["header"].index(a["claim"])]).startswith("proposed:")
              and not before[b["header"].index(b["claim"])].startswith("proposed:")):
            out[ident] = "relabelled proposed"
        elif a["cited"] != b["cited"]:
            out[ident] = "citation changed"
        elif [_strip(c) for c in a["cells"]] != before:
            out[ident] = "claim narrowed"
        else:
            out[ident] = "unchanged"
    return out


def fix_lines(reg, unit, rnd):
    got = Counter(classify_fixes(reg, unit, rnd).values())
    if not got:
        return []
    return [f"Fixes of round {rnd}'s flagged rows: " + ", ".join(f"{got[c]} {c}" for c in
                                                                list(FIX_CLASSES) + sorted(set(got) - set(FIX_CLASSES))
                                                                if got[c])]


def name_key(key):
    """The key as a verdict file's name carries it: every char outside [A-Za-z0-9_-] replaced by _, or, over
    NAME_KEY_MAX characters, the key's own hash. Lossy, so a file's own columns say whose verdict it is."""
    return _hash12(key) if len(key) > NAME_KEY_MAX else re.sub(r"[^A-Za-z0-9_-]", "_", key)


def verdict_name(rnd, j, table, key, h):
    return f"r{rnd}-j{j}-{table}-{name_key(key)}-{h}.csv"


def verdict_path(reg, row, rnd, j):
    """This row's verdict file for the round and judge, at the row's current content."""
    return layout.judging_dir(pathlib.Path(reg).resolve(), row["unit"]) / verdict_name(
        rnd, j, row["table"], row["key"], row["hash"])


def read_verdict(path):
    """The verdict file's one data row as a dict, or None when it is not a well-formed verdict file."""
    try:
        header, body = tables.grid(path)
    except OSError:
        return None
    if header != VERDICT_FIELDS or len(body) != 1 or len(body[0]) != len(VERDICT_FIELDS):
        return None
    d = dict(zip(VERDICT_FIELDS, body[0]))
    d["verdict"] = d["verdict"].strip().lower()
    return d if d["verdict"] in VERDICTS else None


def flow_now(reg):
    """The flow worked now, as a verdict file's `flow` names it (go.flow_key, the id earlier-flows/ keeps it under):
    "" before any go."""
    import go
    return go.flow_key(reg, go.load(reg) or {})


def go_given(reg):
    """The go of the flow worked now (scope.json `given`) as an aware datetime, or None when none is recorded."""
    import datetime
    import go
    try:
        got = datetime.datetime.fromisoformat(str((go.load(reg) or {}).get("given") or "").strip()
                                              .replace("Z", "+00:00"))
    except ValueError:
        return None
    return got if got.tzinfo else got.astimezone()


def _of_flow(v, flow, path=None, since=None):
    """A verdict file is the flow worked now's when its own `flow` says so. One that cannot be read counts (it flags),
    unless it was last written before this flow's go (`since`): then it is a finished flow's."""
    if v is not None:
        return v["flow"] == flow
    if since is None or path is None:
        return True
    import datetime
    return datetime.datetime.fromtimestamp(pathlib.Path(path).stat().st_mtime, datetime.timezone.utc) >= since


def round_files(reg, unit, rnd=None):
    """The unit's verdict files of the flow worked now (of round `rnd`, when given): a finished flow's verdicts never
    count toward this flow's rounds."""
    folder = layout.judging_dir(pathlib.Path(reg).resolve(), unit)
    if not folder.is_dir():
        return []
    flow, since = flow_now(reg), go_given(reg)
    return [p for p in sorted(folder.glob(f"r{rnd if rnd else '*'}-j*-*.csv"))
            if _of_flow(read_verdict(p), flow, p, since)]


def latest_round(reg, unit):
    got = [int(m.group(1)) for p in round_files(reg, unit) if (m := re.match(r"r(\d+)-j\d+-", p.name))]
    return max(got, default=0)


def _round(reg, row, rnd, n):
    """[(judge, path, verdict dict or None)] for this row's verdict files of the round at its current hash."""
    out = []
    for j in range(1, n + 1):
        p = verdict_path(reg, row, rnd, j)
        if p.is_file():
            out.append((j, p, read_verdict(p)))
    return out


def _any_hash(reg, row, rnd):
    """[(judge, path, verdict dict or None)] for this row's verdict files of the round at any hash. Found by the anchored
    name (never a prefix glob: keys hold `-`), and kept only when the file's own columns name this row and round, or,
    when it cannot be read, when its name carries the row's current hash (name keys are lossy: `a/b`, `a_b`). A
    verdict of another flow (its `flow` column) is never this row's: a finished flow's rounds are not this flow's."""
    folder = layout.judging_dir(pathlib.Path(reg).resolve(), row["unit"])
    if not folder.is_dir():
        return []
    pat = re.compile(rf"r{rnd}-j(\d+)-{re.escape(row['table'])}-{re.escape(name_key(row['key']))}-([0-9a-f]{{12}})\.csv")
    flow, since = flow_now(reg), go_given(reg)
    out = []
    for p in sorted(folder.iterdir()):
        m = pat.fullmatch(p.name)
        if not m:
            continue
        v = read_verdict(p)
        if v is None:
            # unreadable: its own name (table, name key) is all that says whose it is; it counts as a flag, in the
            # flow whose go came before it was written
            mine = _of_flow(None, flow, p, since)
        else:
            mine = [v["unit"], v["table"], v["row"], v["round"], v["flow"]] == [row["unit"], row["table"], row["key"],
                                                                             str(rnd), flow]
        if mine:
            out.append((int(m.group(1)), p, v))
    return out


def _stale(reg, row, rnd):
    """This row's verdict files of the round at an older hash: listed, never failed."""
    return [p for _, p, _ in _any_hash(reg, row, rnd) if not p.name.endswith(f"-{row['hash']}.csv")]


def _flags(got):
    return [(j, v) for j, _, v in got if v is None or v["verdict"] != "says"]


def flagged_in(reg, rws, rnd, n):
    """The rows any of whose verdicts of this round, at any hash, flagged them: a fix changes the row's hash, never its
    place in the rounds."""
    return [r for r in rws if _flags(_any_hash(reg, r, rnd))]


def _moved_on(reg, row, rnd, last):
    """Flagged in this round at an older content and not judged at its current one: fixed, and due in the next round,
    not this one. Never in the last round (`last`, judge_rounds): with no round left, the row is judged again in it."""
    if rnd >= last:
        return False
    got = _any_hash(reg, row, rnd)
    return bool(_flags(got)) and not any(p.name.endswith(f"-{row['hash']}.csv") for _, p, _ in got)


def scope(reg, unit, rnd, n, mode=None):
    """The rows judged in this round: all of them in round 1, else those flagged in the round before at any hash; less
    the rows flagged in this round and fixed since, which are due in the next."""
    last = settings(reg)["judge_rounds"]
    rws = rows(reg, unit)[0]
    if run_settings.load(reg).get("mapping") == "fast":  # only the rows a proposal rests on (selective.py)
        import selective
        keep = (selective.selected(reg) or {}).get(unit, set())
        rws = [r for r in rws if (r["table"], r["key"]) in keep]
    if (mode or ("all" if rnd <= 1 else "flagged")) != "all":
        rws = flagged_in(reg, rws, rnd - 1, n)
    return [r for r in rws if not _moved_on(reg, r, rnd, last)]


# ---- run ----

def workspace(reg, ws=None):
    """The folder citations are relative to, which every reader's and judge's prompt names: `ws`, else where the code
    is (layout.code_root: the folder the survey read it from, or that holds the repositories sources.csv names), else
    the register's grandparent (<ws>/bfo-work/<reg>)."""
    if ws:
        return pathlib.Path(ws).resolve()
    return layout.code_root(reg) or pathlib.Path(reg).resolve().parent.parent


def session_root(reg):
    """The folder the run's Claude Code session starts in, where a project's `.claude/agents/` is looked for: the
    register's grandparent (<workspace>/bfo-work/<reg>), whatever folder the code is read from."""
    return pathlib.Path(reg).resolve().parent.parent


JUDGE_AGENT = "bfo-row-judge"  # provenance.JUDGE_TYPE: the kit's agents/bfo-row-judge.md, launched by that name
JUDGE_AGENT_FILE = pathlib.Path(__file__).resolve().parent / "agents" / f"{JUDGE_AGENT}.md"


def agent_problem(reg, name, want, kind):
    """None when the agent Claude Code would launch by `name` is the kit's own definition `want` (a file); else what
    to do. Claude Code takes a project's `.claude/agents/` (the folder the session started in, or one above it) before
    the user's (CLAUDE_CONFIG_DIR, else `~/.claude`)."""
    import os
    file = f"{name}.md"
    start = session_root(reg)
    home = pathlib.Path.home().resolve()
    project = [d / ".claude" / "agents" / file for d in (start, *start.parents) if d != home and d != d.parent]
    config = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude")
    found = next((p for p in project + [config / "agents" / file] if p.is_file()), None)
    fix = (f"copy the kit's agents/{file} to .claude/agents/ in the folder Claude Code starts in ({start.as_posix()}) "
           f"(or to {(config / 'agents').as_posix()}/ for every project), then start a new session: it loads agents "
           "when a session starts")
    if found is None:
        return f"the {kind} agent {name} is not installed: {fix}"
    if found.read_bytes().replace(b"\r\n", b"\n") != pathlib.Path(want).read_bytes().replace(b"\r\n", b"\n"):
        return f"the {kind} agent at {found.as_posix()} is not this kit's copy: {fix}"
    return None


def judge_agent_problem(reg):
    """None when the judge agent (JUDGE_AGENT, no shell) is installed as the kit's copy; else what to do."""
    return agent_problem(reg, JUDGE_AGENT, JUDGE_AGENT_FILE, "judge")


def missing_under(ws, paths):
    """The paths (relative, `/`) that are not a file or folder under `ws`, each once, in order."""
    ws = pathlib.Path(ws)
    return [p for p in dict.fromkeys(p.strip().strip("/") for p in paths if p and p.strip())
            if not (ws / p).exists()]


def where_to_say(ws, missing):
    return (f"the code these agents would be told to open is not under {pathlib.Path(ws).as_posix()} (the folder "
            f"their prompts name): {', '.join(missing[:6])}{' ...' if len(missing) > 6 else ''}. Every one would fail "
            "its first read and be thrown away; run the survey on the repositories where they are (it records that "
            "folder), or pass --ws <the folder holding the repositories>")


def launch_problem(reg, unit, rnd, mode=None, ws=None):
    """Why this round's judges of `unit` cannot be launched now, or None: the judge agent not installed as the kit's
    copy, or a cited file not under the folder their prompts name. Checked by a direct `emit` and by run control."""
    return judge_agent_problem(reg) or workspace_problem(
        reg, scope(reg, unit, rnd, settings(reg)["judges"], mode), ws)


def workspace_problem(reg, rows, ws=None):
    """Why judges of `rows` (rows() dicts, each with `cited` [(path, first, last)]) cannot be launched: a cited file
    not under the folder their prompts name; None when every one is there."""
    w = workspace(reg, ws)
    missing = missing_under(w, [c[0] for r in rows for c in r.get("cited") or []])
    return where_to_say(w, missing) if missing else None


def ws_line(ws):
    w = pathlib.Path(ws).as_posix()
    return f"Workspace: {w} (the code is there; citations are paths relative to it, opened as {w}/<path>)"


EMITTED = "emitted.txt"  # prompts/emitted.txt: '<sha256 of the file as written> <its path under prompts/>', one a line
EMITTED_AT = "emitted-at.jsonl"  # prompts/emitted-at.jsonl: {"path", "sha256", "at"} per emission, "at" in UTC


def _prompts_root(path):
    """The register's prompts/ folder holding `path`, or None."""
    return next((p for p in pathlib.Path(path).parents if p.name == layout.PROMPTS), None)


def _digest(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def write_prompt(path, text):
    """Write one agent's prompt file and return its pointer line. A file under a register's prompts/ is recorded in
    prompts/emitted.txt by the hash of its bytes as written, every version kept (a prompt is written again in place
    from round to round): the agent launched on it is told from one launched on a prompt the lead wrote."""
    path = pathlib.Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    root = _prompts_root(path)
    if root is not None:
        digest, rel = _digest(path), path.relative_to(root).as_posix()
        with (root / EMITTED).open("a", encoding="utf-8") as f:
            f.write(f"{digest} {rel}\n")
        # when, beside it and never in it: the prompt check parses emitted.txt as '<hash> <path>' and nothing more
        at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        with (root / EMITTED_AT).open("a", encoding="utf-8") as f:
            f.write(json.dumps({"path": rel, "sha256": digest, "at": at}) + "\n")
    return POINTER.format(path.as_posix())


def kit_prompt_problem(sess, reg):
    """None when session `sess` was launched on a prompt a kit script wrote for register `reg`: its first message is
    exactly the pointer line of a file under <reg>/prompts/ whose bytes, as they are now, are one version
    write_prompt recorded for that file. Else why not, naming the session (a reader, fixer or re-read the lead
    dictated, inline or in a prompt file it wrote by hand)."""
    name = pathlib.Path(sess.path).stem
    first = " ".join(str(sess.prompt or "").split())
    m = re.fullmatch(re.escape(POINTER).replace(re.escape("{}"), "(.+?)"), first)
    if not m:
        return (f"{name} was launched on a prompt no kit script wrote (its first message is not the pointer line of "
                "a prompt readers.py or judges.py wrote under prompts/)")
    target = pathlib.Path(m.group(1))
    root = pathlib.Path(reg).resolve() / layout.PROMPTS
    if not paths.norm(target).startswith(paths.norm(root) + "/"):
        return f"{name} was launched on a prompt no kit script wrote ({m.group(1)} is not under {root.as_posix()}/)"
    rel = paths.norm(target)[len(paths.norm(root)) + 1:]
    got = set()
    ledger = root / EMITTED
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            h, _, p = line.partition(" ")
            if p.strip().lower() == rel:
                got.add(h)
    try:
        now = _digest(target)
    except OSError:
        return f"{name} was launched on a prompt no kit script wrote ({m.group(1)} is gone)"
    if now not in got:
        return (f"{name} was launched on a prompt no kit script wrote ({rel} "
                + ("was changed after a kit script wrote it)" if got else
                   "was never written by readers.py or judges.py)"))
    return None


LAUNCHER = """# Launch {n} helper agent(s) of a business flow observability run

You launch helper agents for the run's lead. Each line under "Agents" is the whole prompt of one agent: launch it with
the Agent tool, `subagent_type` `{agent_type}` (never a fork: a fork has seen the lead's reasoning, and the run's
check fails it; never any other type, which the check fails too), in the foreground, never in the background. If
Claude Code refuses that type (no such agent), launch nothing and reply with its error, word for word. Keep at most {parallel} running at once: launch
{parallel}, then launch the next each time one finishes. If a launch is refused with "Concurrent subagent limit
reached", launch nothing more until one finishes. Launch each line once. Do no other work: read no other file, write
no file, run no shell. When every agent has finished, and only then, reply with one line:
`launched <n>, finished <n>`.

## Agents

{lines}
"""
SESSION_LIMIT = 20  # subagents one Claude Code session runs at once (its documentation); nested ones are counted
REPLIED = re.compile(r"launched \d+, finished \d+")  # a launcher's reply line: only it says every agent has finished
# Seconds a launcher's transcript must be quiet, ended on text that is not its reply line, before it counts as stopped:
# a turn's text and its tool call are written as separate lines, so one read between them looks ended.
LAUNCHER_QUIET = 120


def launcher_cap(reg):
    """How many launchers the lead keeps running at once: each is a subagent holding up to `parallel` agents, and the
    session holds at most SESSION_LIMIT (whether nested agents count toward it is not established, so they are
    counted)."""
    return max(1, SESSION_LIMIT // (max(1, settings(reg)["parallel"]) + 1))


def launchers(reg, name, groups, keep=(), agent_type="general-purpose", parallel=None):
    """Write launcher files for `groups` [(label, [pointer line])], each split into files of at most LAUNCHER_MAX
    agents, under <reg>/prompts/launch/ as <name>[-<label>]-<i>.md; returns one pointer line per launcher file. This
    name's earlier launcher files are removed first, except those in `keep` (launchers still running, Launches): those
    are left as they are, byte for byte, and no new file takes their name. Each launcher launches its agents as
    `agent_type` subagents: JUDGE_AGENT for judges; provenance.READER_TYPE for readers, fixers and re-reads."""
    folder = pathlib.Path(reg).resolve() / layout.LAUNCH
    folder.mkdir(parents=True, exist_ok=True)
    keep = {pathlib.Path(k).resolve() for k in keep}
    for old in folder.glob(f"{name}-*.md"):
        if old.resolve() not in keep:
            old.unlink()
    par = max(1, parallel or settings(reg)["parallel"])
    out = []
    for label, lines in groups:
        i = 0
        for start in range(0, len(lines), LAUNCHER_MAX):
            chunk = lines[start:start + LAUNCHER_MAX]
            while True:
                i += 1
                path = folder / ("-".join(x for x in (name, label, str(i)) if x) + ".md")
                if path.resolve() not in keep:
                    break
            out.append(write_prompt(path, LAUNCHER.format(n=len(chunk), parallel=par, agent_type=agent_type,
                                                             lines="\n".join(chunk))))
    return out


def given_sessions(reg, transcripts=None):
    """[(the first user message's text, its first timestamp as a UTC datetime or None, finished, shell, the last
    assistant text, when the transcript was last written as a UTC datetime)] of every transcript here: finished when
    its last assistant message called no tool (it has replied); shell when it called Bash or PowerShell."""
    out = []
    for folder in _folders(reg, transcripts):
        for f in sorted(pathlib.Path(folder).rglob("*.jsonl")):
            s = session_of(f)
            if s[0]:
                out.append(s)
    return out


def first_message(line):
    """The text of a transcript line when it is a user message, else None."""
    try:
        d = json.loads(line)
    except ValueError:
        return None
    if not isinstance(d, dict) or d.get("type") != "user" or not isinstance(d.get("message"), dict):
        return None
    m = d["message"]
    c = m.get("content")
    return c if isinstance(c, str) else " ".join(
        b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")


def session_of(f):
    """One transcript as given_sessions reads it: (first user message's text or None, its first timestamp, finished,
    shell, the last assistant text, when the transcript was last written)."""
    import datetime
    f = pathlib.Path(f)
    first, when, last_tools, shell, last, error = None, None, None, False, "", None
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict) and d.get("type") == "system" and d.get("subtype") == "api_error":
                e = d.get("error") if isinstance(d.get("error"), dict) else {}
                error = ("retry", str(e.get("formatted") or e.get("message") or e.get("status") or "")[:200])
                continue
            m = d.get("message") if isinstance(d, dict) else None
            if not isinstance(m, dict):
                continue
            c = m.get("content")
            if first is None and d.get("type") == "user":
                first = first_message(line)
                try:
                    when = datetime.datetime.fromisoformat(str(d.get("timestamp")).replace("Z", "+00:00"))
                except ValueError:
                    when = None
            if d.get("type") == "assistant":
                blocks = [b for b in (c if isinstance(c, list) else []) if isinstance(b, dict)]
                uses = [b for b in blocks if b.get("type") == "tool_use"]
                last_tools = bool(uses)
                last = " ".join(b.get("text", "") for b in blocks if b.get("type") == "text") or (
                    c if isinstance(c, str) else "")
                shell = shell or any(b.get("name") in ("Bash", "PowerShell") for b in uses)
                error = ("ended", last[:200]) if d.get("isApiErrorMessage") else None
    done = last_tools is False
    meta = _meta_finished(f)
    if not done and meta:
        done, last = True, last if REPLIED.search(last or "") else META_FINISHED
    # An API error ends it: Claude Code's own error reply (isApiErrorMessage), or retries of a failed request
    # (system api_error lines) with nothing after them, once Claude Code says it finished or it has been quiet.
    # A retry still going on is neither: the agent may yet answer.
    quiet = f.stat().st_mtime <= datetime.datetime.now().timestamp() - LAUNCHER_QUIET
    if error and (error[0] == "ended" or meta or quiet):
        done, last = True, API_STOPPED + error[1]
    return (first, when, done, shell, last, datetime.datetime.fromtimestamp(f.stat().st_mtime,
                                                                             datetime.timezone.utc))


META_FINISHED = "finished, per Claude Code's metadata; its reply was not recorded"
API_STOPPED = "stopped on an API error: "  # the last text of a session an API error ended, before the error's own text


def relaunch_cap(reg):
    """How many times an agent an API error stopped, before its owed output was written, is launched afresh for the
    same prompt (run-settings.json `relaunches`; 0 is none)."""
    v = run_settings.load(reg).get("relaunches")
    return run_settings.DEFAULTS["relaunches"] if v in (None, "") else max(0, int(v))


RETRY_FROM = "relaunch-from.txt"  # prompts/relaunch-from.txt: the time the person said to try again; tries count after it


def _meta_finished(transcript):
    """Claude Code's own record that a subagent finished, in the metadata file beside its transcript. A headless
    session (claude -p) writes no final reply into the transcript, so the transcript alone cannot say it."""
    try:
        meta = json.loads(transcript.with_name(transcript.stem + ".meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return meta.get("finished") is True


class Launches:
    """Which prompt files a session was given, read from the transcripts and the launcher files, so that `emit` and
    `readers.py prompt`, run again at any time, launch no agent twice.

    A session counts for a prompt file when its first message is the file's pointer line and it started after the file
    was last written and after the go of the flow worked now (scope.json `given`): a finished flow's agents never
    count. A launcher still running (given its pointer, and no reply line `launched <n>, finished <n>` yet) is left as
    it is, and every agent it lists is held, whether it has started or not. A launcher whose transcript ended on other
    text (an API error, out of turns) and has been quiet for LAUNCHER_QUIET seconds has stopped: its
    agents are treated as a replied launcher's, so those never started or still named running (they died with it) are
    launched afresh, and `ended` names it. `again` says the session that launched them is gone (a crash, a restart):
    every agent and launcher still named running died with it.

    An agent whose transcript ended on an API error (a 503, an overloaded model) stopped without its work, though Claude
    Code's metadata says it finished: its state is 'errored', and it is launched afresh for the same prompt, at most
    `relaunches` times (run-settings.json, default 2) counted since the go, or since the person last said to try again
    (prompts/relaunch-from.txt); then its state is 'gave up', and run control stops on it."""

    def __init__(self, reg, transcripts=None, again=False, stuck_after=None):
        self.reg, self.again, self._tx, self._sessions = pathlib.Path(reg).resolve(), again, transcripts, None
        # judges only: an agent live but silent this many seconds is 'stuck'; the prompts already relaunched for it
        self.stuck_after = stuck_after
        self.stuck_before = {r.get("prompt") for r in tables.dicts(layout.judging_dir(self.reg) / STUCK)} \
            if stuck_after else set()
        self.since = go_given(self.reg)
        self.cap = relaunch_cap(self.reg)
        self.tries_from = self.since
        try:
            import datetime
            t = datetime.datetime.fromisoformat((self.reg / layout.PROMPTS / RETRY_FROM).read_text(
                encoding="utf-8").strip().replace("Z", "+00:00"))
            t = t if t.tzinfo else t.astimezone()
            self.tries_from = t if self.tries_from is None else max(self.tries_from, t)
        except (OSError, ValueError):
            pass
        self.running, self.held, self.replied, self.ended = set(), set(), set(), []
        folder = self.reg / layout.LAUNCH
        for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            agents = {l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("Read ")}
            state = self.state(f, launcher=True)
            if state == "still running" and not again and self.silent(f, agents):
                state = "ended"  # died mid-turn: quiet, none of its agents running, and it never replied
            if state == "still running" and not again:
                self.running.add(f.resolve())
                self.held |= agents
            elif state in ("finished", "ended"):
                self.replied |= agents
                if state == "ended":
                    self.ended.append(f.name)

    def silent(self, launcher, agents):
        """Whether a launcher not finished has died mid-turn: every session given it has been quiet for LAUNCHER_QUIET
        seconds and none of the agents it lists is still running. A live launcher is waiting on a running agent, or
        launches the next within seconds of one finishing."""
        import datetime
        quiet = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=LAUNCHER_QUIET)
        pointer = POINTER.format(pathlib.Path(launcher).resolve().as_posix())
        mine = [mtime for first, when, _, _, _, mtime in self.sessions() if pointer in first and when is not None]
        if not mine or any(m > quiet for m in mine):
            return False
        for line in agents:
            f = line.split("Read ", 1)[1].split(" and do exactly", 1)[0]
            if self.state(f) in ("still running", "stuck"):  # live, however long silent: the launcher waits on it
                return False
        return True

    def ended_lines(self, name):
        """One line per launcher of this name that stopped without its reply line."""
        return [f"{f}: launcher stopped without its reply line (an error or out of turns): its agents never started, "
                f"and those it left running, are launched afresh" for f in self.ended if f.startswith(name + "-")]

    def sessions(self):
        if self._sessions is None:
            self._sessions = given_sessions(self.reg, self._tx)
        return self._sessions

    def state(self, path, launcher=False):
        """None (no session was given this file as it stands), 'still running', 'finished', 'ran a shell', for an
        agent 'errored' (an API error ended it) or 'gave up' (and it has been launched afresh `relaunches` times
        already), or for a launcher 'ended' (its transcript ended without its reply line, and has been quiet since: it
        died)."""
        import datetime
        path = pathlib.Path(path).resolve()
        if not path.is_file():
            return None
        written = datetime.datetime.fromtimestamp(path.stat().st_mtime, datetime.timezone.utc) - \
            datetime.timedelta(seconds=2)
        if self.since is not None:
            written = max(written, self.since)
        pointer = POINTER.format(path.as_posix())
        got = [(done, shell, last, mtime) for first, when, done, shell, last, mtime in self.sessions()
               if pointer in first and when is not None and when >= written]
        if not got:
            return None
        if any(shell for _, shell, _, _ in got):
            return "ran a shell"
        if not launcher and all(done for done, _, _, _ in got) and any(
                (last or "").startswith(API_STOPPED) for _, _, last, _ in got):
            return "gave up" if self.errored(path) > self.cap else "errored"
        if all(done and (not launcher or REPLIED.search(last or "") or last == META_FINISHED)
               for done, _, last, _ in got):
            return "finished"
        now = datetime.datetime.now(datetime.timezone.utc)
        quiet = now - datetime.timedelta(seconds=LAUNCHER_QUIET)
        if launcher and all(done and mtime <= quiet for done, _, _, mtime in got):
            return "ended"
        if not launcher and self.stuck_after:
            limit = now - datetime.timedelta(seconds=self.stuck_after)
            live = [mtime for done, _, _, mtime in got if not done]
            if live and all(m <= limit for m in live):
                return "stuck"
        return "still running"

    def errored(self, path):
        """How many sessions given this file's pointer, since the go or the person's last word to try again, an API
        error ended: whatever the file's version, since a relaunch rewrites it."""
        pointer = POINTER.format(pathlib.Path(path).resolve().as_posix())
        return sum(1 for first, when, done, _, last, _ in self.sessions()
                   if pointer in first and done and (last or "").startswith(API_STOPPED)
                   and (self.tries_from is None or (when is not None and when >= self.tries_from)))

    def decide(self, path, text, same=None):
        """(launch it now, its state): ('queued', 'still running', 'finished', 'ran a shell', 'stopped', 'errored',
        'gave up' or None). A prompt held is never rewritten. Launched: one never launched; one still named running
        whose launcher has replied (it stopped without replying); one an API error ended, until it has been launched
        afresh `relaunches` times ('gave up' after); with `again`, one still named running or that ran a shell; and one
        finished whose prompt changed in substance (`same`, default equal text: a fixer given other rows is another
        fixer). A finished agent is never launched again for the same prompt, `again` or not."""
        path = pathlib.Path(path).resolve()
        pointer = POINTER.format(path.as_posix())
        state = self.state(path)
        if state == "stuck":  # live but silent past its limit: launched afresh once, whatever holds it
            return (False, "stuck twice") if path.name in self.stuck_before else (True, state)
        if pointer in self.held:
            return False, "queued"
        if state is None:
            return True, None
        if state == "still running":
            if self.again:
                return True, state
            return (True, "stopped") if pointer in self.replied else (False, state)
        if state == "ran a shell":
            return self.again, state
        if state in ("errored", "gave up"):
            return state == "errored", state
        old = path.read_text(encoding="utf-8")
        return (not (same or (lambda a, b: a == b))(old, text)), state


def emit(reg, unit, rnd, mode=None, ws=None, transcripts=None, again=False):
    """Write the prompt file of every judge of this round whose verdict file is not on disk and that is not launched
    already (Launches), under <reg>/prompts/<unit>/<verdict file stem>.md, gather their pointer lines into launcher
    files (the `flow` unit's by lead table), and return the lines to print: a count, the judges held and why, then one
    pointer line per launcher. `again`: after a crash or restart, every judge and launcher still named running died;
    the run's timing record is rewritten first, before anything is relaunched (timings.refresh)."""
    reg = pathlib.Path(reg).resolve()
    if again:
        import timings
        timings.refresh(reg, transcripts, "judges.py emit --again")
    seen = Launches(reg, transcripts, again, stuck_after=judge_seconds(reg))
    groups, held, relaunched, todo = _owed_judges(reg, unit, rnd, mode, ws, seen)
    pointers = launchers(reg, f"judges-{unit}-r{rnd}", sorted(groups.items()), keep=seen.running,
                         agent_type=JUDGE_AGENT)
    n = sum(len(v) for v in groups.values())
    return ([f"Unit {unit}, round {rnd}: {n} judge(s) to launch in {len(pointers)} launcher(s), "
             f"{todo - n - sum(held.values())} verdict file(s) already on disk; keep at most "
             f"{launcher_cap(reg)} launcher(s) running at once"]
            + _held_lines(unit, held, relaunched, seen.cap, judge_seconds(reg))
            + seen.ended_lines(f"judges-{unit}-r{rnd}") + pointers)


def _owed_judges(reg, unit, rnd, mode, ws, seen):
    """({group: [pointer line]}, Counter of judges held by state, judges relaunched after an API error, judges owed):
    each judge of the round whose verdict file is not on disk and that Launches says to launch now, its prompt
    written."""
    s = settings(reg)
    body, ws, flow = agent_body(), workspace(reg, ws), flow_now(reg)
    groups, held, relaunched = {}, Counter(), Counter()
    todo = scope(reg, unit, rnd, s["judges"], mode)
    write_record(reg, unit, rnd, todo)
    folder = layout.prompts_dir(reg, unit)
    owed = set()
    for row in todo:
        for j in range(1, s["judges"] + 1):
            p = verdict_path(reg, row, rnd, j)
            owed.add(f"{p.stem}.md")
            if p.is_file():
                continue
            f, text = folder / f"{p.stem}.md", prompt(body, row, rnd, j, p, ws, flow)
            launch, state = seen.decide(f, text)
            if not launch:
                held[state] += 1
                continue
            if state in ("errored", "stuck"):
                relaunched[state] += 1
            if state == "stuck":
                _record_stuck(reg, f)
            groups.setdefault(row["table"] if unit == "flow" else "", []).append(write_prompt(f, text))
    _drop_unowed(folder, rnd, owed, seen)
    return groups, held, relaunched, len(todo) * s["judges"]


STUCK = "stuck.csv"  # judging/: prompt,at: each judge launched afresh because it sat silent past judge_seconds


def judge_seconds(reg):
    """Seconds a judge may sit live and silent before it counts as stuck (run-settings.json `judge_seconds`)."""
    return run_settings.number(run_settings.load(reg), "judge_seconds")


def _record_stuck(reg, f):
    p = layout.judging_dir(reg) / STUCK
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.is_file()
    with p.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["prompt", "at"])
        w.writerow([pathlib.Path(f).name, datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")])


def _drop_unowed(folder, rnd, owed, seen):
    """Remove this round's judge prompts no judge is owed (a row the selection dropped, a row's earlier text) and no
    agent was given: the status page counts every prompt on disk no agent took as queued."""
    for f in folder.glob(f"r{rnd}-j*.md") if folder.is_dir() else []:
        if f.name not in owed and seen.state(f) is None and POINTER.format(f.resolve().as_posix()) not in seen.held:
            f.unlink()


SELECTED = "judges-selected-r1"  # the launcher files of a fast map's selective checking, every unit packed together


def emit_selected(reg, units, ws=None, transcripts=None, again=False):
    """A fast map's selective checking (one round): the judges owed for every unit named, packed into as few launchers
    as fill the session at once. With n judges, one launcher holding up to SESSION_LIMIT - 1 at once when n fits, else
    two holding SESSION_LIMIT // 2 - 1 each, the judges dealt between them by turns, so no slot waits on a small unit.
    Returns the lines to print, as `emit` does."""
    reg = pathlib.Path(reg).resolve()
    if again:
        import timings
        timings.refresh(reg, transcripts, "judges.py emit-selected --again")
    seen = Launches(reg, transcripts, again, stuck_after=judge_seconds(reg))
    lines, held, relaunched, todo = [], Counter(), Counter(), 0
    for unit in units:
        g, h, r, t = _owed_judges(reg, unit, 1, None, ws, seen)
        lines += [x for v in g.values() for x in v]
        held, relaunched, todo = held + h, relaunched + r, todo + t
    count = 1 if len(lines) <= SESSION_LIMIT - 1 else 2
    par = SESSION_LIMIT // count - 1
    chunks = [lines[i::count] for i in range(count)] if lines else []
    pointers = launchers(reg, SELECTED, [(str(i + 1), c) for i, c in enumerate(chunks) if c], keep=seen.running,
                         agent_type=JUDGE_AGENT, parallel=par)
    return ([f"Selective checking: {len(lines)} judge(s) of {len(units)} unit(s) to launch in {len(pointers)} "
             f"launcher(s), {todo - len(lines) - sum(held.values())} verdict file(s) already on disk; launch every "
             "launcher printed at once"]
            + _held_lines("<unit>", held, relaunched, seen.cap, judge_seconds(reg))
            + seen.ended_lines(SELECTED) + pointers)


def _held_lines(unit, held, relaunched, cap, limit):
    why = {"queued": "queued in a launcher still running",
           "stuck twice": f"stuck twice, silent past {limit} s each time ({layout.SETTINGS} `judge_seconds`): not launched again; "
                          f"judging/{STUCK} lists them",
           "still running": "launched already and still running",
           "finished": f"finished without their verdict file: delete a judge's prompt file (prompts/{unit}/) to "
                       "launch it afresh",
           "ran a shell": "ran a shell and wrote no verdict file: run this again with --again to launch them afresh",
           "gave up": f"stopped on an API error without their verdict file, launched afresh {cap} time(s) "
                      f"already ({layout.SETTINGS} `relaunches`): not launched again"}
    return ([f"  {c} judge(s) {why[k]}" for k, c in held.items()]
            + ([f"  {relaunched['errored']} judge(s) stopped on an API error without their verdict file: launched "
                "afresh"] if relaunched["errored"] else [])
            + ([f"  {relaunched['stuck']} judge(s) silent past {limit} s ({layout.SETTINGS} `judge_seconds`): "
                f"launched afresh once, recorded in judging/{STUCK}"] if relaunched["stuck"] else []))


def prompt(body, row, rnd, j, path, ws=None, flow=""):
    """One judge's prompt. Its data line names the row, round and judge, the flow worked now and the row's hash, which
    the judge copies into its verdict file: a verdict is current only while both match the row."""
    fields = "\n".join(f"- {h}: {v}" for h, v in zip(row["header"], row["cells"]) if v.strip())
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow([row["unit"], row["table"], row["key"], rnd, j, flow, row["hash"], ""])
    where = f"{ws_line(ws)}\n\n" if ws else ""
    return (f"{body}\n\n## The row\n\n{where}"
            f"The row is from the map's {row['table']} table (unit {row['unit']}, row {row['key']}; judging round "
            f"{rnd}, you are judge {j}). Its columns and values:\n{fields}\n\n"
            f"Cited locations: {row['citations']}\n\n"
            f"Verdict file: {path}\n"
            f"Header line: {HEADER}\n"
            f"Data line: {buf.getvalue()}<verdict>,\"<reason>\"\n")


def command(text, model=None):
    cmd = ["claude", "-p", text, "--output-format", "json",
           "--allowedTools", ALLOWED, "--disallowedTools", DISALLOWED]
    return cmd + (["--model", model] if model else [])


def _launch(cmd, cwd):
    cmd = [shutil.which(cmd[0]) or cmd[0]] + cmd[1:]
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=1800).returncode
    except subprocess.TimeoutExpired:
        return -1


SET_ASIDE_DIR = "set-aside"  # judging/<unit>/set-aside/<when>/: verdict files moved aside on the person's word


def unknown_choices(reg, ws, unit, rnd, mode, files):
    """The refusal of `run --again` over failing verdict files no transcript here wrote: what happened, and
    the person's choices in plain words for the session to put to them, each naming what the session then runs."""
    rows = f" --rows {mode}" if mode else ""
    again = f'python judges.py run "{reg}" "{ws}" {unit} --round {rnd}{rows} --again'
    return "\n".join([
        f"judges.py run --again: no transcript wrote {len(files)} failing verdict file(s) of unit {unit}, round {rnd} "
        "(transcripts not found here: another PC, another project folder, or cleaned up?); nothing removed: "
        + ", ".join(p.name for p in files[:10]),
        "Put these choices to the person as written; take their answer by its number or its words:",
        "---",
        f"Some checks of the map against the code failed, and no session on this computer ran them, so the kit "
        "cannot tell what went wrong in them. What would you like to do?",
        "1. Set those results aside, kept but not counted, and check those findings again. I'll ask for your reason "
        "and keep it, word for word, with the record.",
        "2. Leave them as they are: mapping waits here until the record of the computer that ran them is brought here.",
        "---",
        f'On 1: ask for their reason in one plain question, then run {again} --set-aside "<their reason, word for '
        'word>". On 2: tell them mapping waits here, and run nothing.'])


def set_aside_unknown(reg, unit, files, words):
    """Move `files` (failing verdict files no transcript here wrote) to judging/<unit>/set-aside/<when>/, kept and no
    longer counted, and record the person's words with them: their judges are then launched afresh."""
    import case
    when = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = layout.judging_dir(reg, unit) / SET_ASIDE_DIR / when
    dest.mkdir(parents=True, exist_ok=True)
    moved = []
    for f in files:
        shutil.move(str(f), str(dest / f.name))
        moved.append(f.name)
    (dest / "why.json").write_text(json.dumps({"words": words, "files": moved}, indent=1), encoding="utf-8")
    case.log(reg, "verdict files set aside on the person's word", unit=unit, files=moved, words=words)
    case.decide(reg, "check results set aside", f"failing check results of {unit} no session here wrote: "
                + ", ".join(moved), words, "chat", choice="set aside and check again", unit=unit, files=moved)
    return moved


def relaunchable(reg, unit, rnd, mode=None, transcripts=None, set_aside_words=None, ws=None):
    """The round's verdict files that fail the check on their own (a judge that ran a shell, wrote another file or
    skipped a cited line, a malformed file, a file no Write matches): the ones a relaunch removes first. A failing file
    no transcript here wrote is never removed: its verdict, a flag perhaps, could not be told from nothing. The relaunch
    is refused, naming those files. Returns (files to remove, [(file, [sessions])] whose clean verdict was replaced):
    those are kept, since re-rolling them would only replace the clean verdict again; the clean judge's content, in its
    transcript, is what is restored."""
    s = settings(reg)
    todo = scope(reg, unit, rnd, s["judges"], mode)
    by_path = writers(reg, transcripts)
    _, _, _, bad, kept = _check_rows(pathlib.Path(reg).resolve(), todo, rnd, s["judges"], by_path)
    unknown = [p for p in bad if paths.norm(p) not in by_path]
    if unknown and set_aside_words:
        set_aside_unknown(reg, unit, unknown, set_aside_words)
        bad = [p for p in bad if p not in unknown]
    elif unknown:
        raise SystemExit(unknown_choices(reg, ws or "<ws>", unit, rnd, mode, unknown))
    return bad, kept


def run(reg, ws, unit, rnd, mode=None, model=None, launcher=None, agent=None, again=False, transcripts=None,
        say=print, set_aside_words=None):
    """Launch a judge for every verdict file of this round not yet written; returns how many were launched. With
    `again`, the round's verdict files that fail the check are removed first and their judges launched afresh onto the
    same paths: removed rather than read, so the new judge never sees the old verdict, and the Write tool, which
    refuses to overwrite a file the session has not read, does not fail. A file whose clean verdict was replaced is
    kept, and `say` names it and the session whose content restores it."""
    s = settings(reg)
    meta, body = _split_agent(agent)
    if not model and meta.get("model", "inherit") not in ("", "inherit"):
        model = meta["model"]
    if again:
        bad, kept = relaunchable(reg, unit, rnd, mode, transcripts, set_aside_words, ws)
        for p in bad:
            p.unlink(missing_ok=True)
        for p, ss in kept:
            say(f"kept {p.name}: a clean verdict by {', '.join(pathlib.Path(x.path).stem for x in ss)} was replaced; "
                "restore that judge's Write content from its transcript, then check again (not relaunched)")
    jobs, flow = [], flow_now(reg)
    for row in scope(reg, unit, rnd, s["judges"], mode):
        for j in range(1, s["judges"] + 1):
            p = verdict_path(reg, row, rnd, j)
            if not p.is_file():
                jobs.append(command(prompt(body, row, rnd, j, p, workspace(reg, ws), flow), model))
    if jobs:
        layout.judging_dir(reg, unit).mkdir(parents=True, exist_ok=True)
        cwd = str(pathlib.Path(ws).resolve())
        with ThreadPoolExecutor(max(1, s["parallel"])) as ex:
            list(ex.map(lambda c: (launcher or _launch)(c, cwd), jobs))
    return len(jobs)


# ---- transcripts ----

class Session:
    """One transcript, the kit's one reader of them: what it wrote, whether it ran a shell, which models answered, what
    it read, when it started. A Write or Edit whose tool_result is an error wrote nothing and is not counted. A shell
    call counts whatever its result: it was tried."""

    def __init__(self, path):
        self.path = path
        self.writes = []  # (tool, normalised path), successful calls only
        self.wrote = []  # (normalised path, content, (timestamp, order)): successful Writes, and its own Edits of them
        self.ops = []  # (tool, normalised path, input, (timestamp, order)): every successful write tool call, in order
        self.shell = False
        self.models = set()
        self.first = ""  # the first timestamp the transcript records
        self.prompt = None  # the text of its first user message: the pointer line it was launched with
        calls, errors, read_calls = [], set(), []
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("timestamp") and not self.first:
                    self.first = str(d["timestamp"])
                m = d.get("message") if isinstance(d, dict) else None
                if not isinstance(m, dict):
                    continue
                if d.get("type") == "assistant" and m.get("model") and m.get("model") != "<synthetic>":
                    self.models.add(m["model"])
                content = m.get("content")
                if self.prompt is None and d.get("type") == "user":
                    self.prompt = content if isinstance(content, str) else " ".join(
                        b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")
                # A tool_use counts only from an assistant record and a tool_result only from a user record: other
                # records (an api-request-blob, untimed) replay the request body and would count each call again.
                kind = d.get("type")
                for b in content if isinstance(content, list) and kind in ("assistant", "user") else []:
                    if not isinstance(b, dict):
                        continue
                    if kind == "user" and b.get("type") == "tool_result" and b.get("is_error"):
                        errors.add(b.get("tool_use_id"))
                    if kind != "assistant" or b.get("type") != "tool_use":
                        continue
                    name, inp = b.get("name"), b.get("input") or {}
                    if name in WRITE_TOOLS:
                        calls.append((b.get("id"), name, inp, (str(d.get("timestamp") or ""), len(calls))))
                    elif name == "Read":
                        read_calls.append((b.get("id"), inp))
                    elif name in ("Bash", "PowerShell"):
                        self.shell = True
        for tid, name, inp, when in calls:
            if tid is not None and tid in errors:
                continue
            p = paths.norm(inp.get("file_path") or inp.get("notebook_path") or "")
            self.writes.append((name, p))
            self.ops.append((name, p, inp, when))
            if name == "Write":
                self.wrote.append((p, str(inp.get("content") or ""), when))
            elif name == "Edit":  # an Edit of a file this session itself wrote: the file as the session left it
                mine = [c for q, c, _ in self.wrote if q == p]
                old, new = str(inp.get("old_string") or ""), str(inp.get("new_string") or "")
                if mine and old and old in mine[-1]:
                    edited = mine[-1].replace(old, new) if inp.get("replace_all") else mine[-1].replace(old, new, 1)
                    self.wrote.append((p, edited, when))
        self._ok_reads = [inp for tid, inp in read_calls if tid is None or tid not in errors]
        self._reads = None

    def reads(self):
        """{normalised path: [(first, last)]} of every Read, as reading_check.py counts them."""
        if self._reads is None:
            self._reads = rc.reads([self.path])
        return self._reads

    def ok_reads(self):
        """As reads(), counting only the Reads whose result is not an error."""
        got = {}
        for inp in self._ok_reads:
            if inp.get("file_path"):
                first = int(inp.get("offset") or 1)
                got.setdefault(paths.norm(inp["file_path"]), []).append(
                    (first, first + int(inp.get("limit") or rc.DEFAULT_LIMIT) - 1))
        return got


def _folders(reg, transcripts):
    if transcripts:
        return [pathlib.Path(t) for t in (transcripts if isinstance(transcripts, (list, tuple)) else [transcripts])]
    found = rc.project_folders(reg)
    return found + [d for d in run_session_dirs(reg) if not any(d == f or f in d.parents for f in found)]


def run_session_files(reg):
    """The main transcript of every session the run has had (agents_now.session_ids), wherever Claude Code keeps it:
    a session started in a folder other than the register's (a VS Code window on another repository, the code beside
    the work folder) keeps its transcripts under that folder's project folder, which project_folders never reaches."""
    try:
        import agents_now
        ids = agents_now.session_ids(reg)[0]
    except Exception:  # noqa: BLE001  (no id list: only the register's own project folders are read)
        return []
    if not ids or os.environ.get("BFO_TRANSCRIPTS"):
        return []
    home = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR") or pathlib.Path.home() / ".claude") / "projects"
    out = []
    for sid in ids:
        out += [p for p in home.glob(f"*/{sid}.jsonl") if p.is_file()]
    return out


def run_session_dirs(reg):
    """The folder of each run session's own subagents (<project>/<session id>/), so the agents a session launched are
    found wherever the session was started."""
    return [p.with_suffix("") for p in run_session_files(reg) if p.with_suffix("").is_dir()]


def writers(reg, transcripts=None):
    """{normalised verdict file path: [(session, content, (timestamp, order))] for every successful Write of it}, main
    sessions and subagents alike."""
    root = paths.norm(layout.judging_dir(pathlib.Path(reg).resolve())) + "/"
    got = {}
    for folder in _folders(reg, transcripts):
        for f in sorted(folder.rglob("*.jsonl")):
            s = Session(f)
            for p, content, when in s.wrote:
                if p.startswith(root):
                    got.setdefault(p, []).append((s, content, when))
    return got


def _cells(text):
    """CSV text as parsed rows: BOM stripped, line endings normalized, `disputed: ` stripped, trailing blank lines
    dropped. (provenance.py normalizes the same way.)"""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    got = [[_strip(c) for c in r] for r in csv.reader(io.StringIO(text))]
    while got and not any(c.strip() for c in got[-1]):
        got.pop()
    return got


def effective_writer(path, wrote):
    """(the session whose successful Write equals the file on disk, the latest of them; [the other sessions that wrote
    it]). The first is None when no Write matches the file (overwritten by a shell or an Edit)."""
    try:
        disk = _cells(pathlib.Path(path).read_text(encoding="utf-8-sig", errors="replace"))
    except OSError:
        disk = None
    match = [w for w in wrote if disk is not None and _cells(w[1]) == disk]
    eff = max(match, key=lambda w: w[2])[0] if match else None
    others = []
    for s, _, _ in wrote:
        if s is not eff and s not in others:
            others.append(s)
    return eff, others


def _model_lines(models):
    if not models:
        return ["Judges ran on: no model recorded in the transcripts"]
    return ["Judges ran on: " + ", ".join(f"{m} ({n} judge session{'s' if n != 1 else ''})"
                                          for m, n in sorted(models.items()))]


# ---- check ----

class Result:
    def __init__(self, unit, rnd, n, problems, models, what="Judging", notes=()):
        self.unit, self.round, self.rows, self.problems = unit, rnd, n, problems
        self.notes = list(notes)  # stale verdicts and superseded writers: listed, never failed
        self.model_counts = Counter(models)
        self.models = set(self.model_counts)
        self.what = what
        self.passed = not problems

    def lines(self):
        head = f"{self.what} of unit {self.unit}, round {self.round}: {self.rows} row(s)"
        out = [head + (": ok" if self.passed else f": NOT DONE: {len(self.problems)} problem(s)")]
        out += [f"  {p}" for p in self.problems[:40]]
        if len(self.problems) > 40:
            out.append(f"  ... and {len(self.problems) - 40} more")
        out += [f"  note: {p}" for p in self.notes[:20]]
        if len(self.notes) > 20:
            out.append(f"  note: ... and {len(self.notes) - 20} more")
        return out + _model_lines(self.model_counts)


def _faults(sess, p, row):
    """What makes this session not a clean judge of the row's verdict file p: other files written, a shell run, a cited
    line not opened, a session that is not the kit's judge agent (or, judged before it, a `general-purpose` subagent:
    provenance.JUDGE_TYPES; provenance.agent_type fails closed)."""
    import provenance  # it imports this module
    out = []
    _, why = provenance.agent_type(sess.path, provenance.JUDGE_TYPES)
    if why:
        out.append(f"the judge session is {why}")
    other = sorted({q for t, q in sess.writes if not (t in ("Write", "Edit") and q == paths.norm(p))})
    if other:
        out.append(f"the judge session wrote other files: {', '.join(other[:3])}")
    if sess.shell:
        out.append("the judge session ran a shell")
    opened = sess.reads()
    for path, a, b in row["cited"]:
        spans = [x for q, xs in opened.items() if q.endswith("/" + path.lower()) for x in xs]
        if not paths.covered(a, b, spans):
            out.append(f"the judge did not open {_cite(path, a, b)}")
    return out


def _currency(v, row, flow):
    """Why the verdict `v` is not of the row as it is now, in the flow worked now: [] when it is."""
    out = []
    if v["row_hash"] != row["hash"]:
        out.append(f"judged the row at hash {v['row_hash'] or '(none)'}, not as it is now ({row['hash']})")
    if v["flow"] != flow:
        out.append(f"judged in flow {v['flow'] or '(none)'}, not in the flow worked now ({flow or 'none recorded'})")
    return out


def _clean_verdict(sess, p, wrote, row, rnd, j, flow):
    """The session's last Write of p was a well-formed verdict naming this row, round and judge, and the session is a
    clean judge (only that file, no shell, every cited line opened)."""
    content = next((c for s, c, _ in reversed(wrote) if s is sess), None)
    got = _cells(content or "")
    if len(got) != 2 or got[0] != VERDICT_FIELDS or len(got[1]) != len(VERDICT_FIELDS):
        return False
    d = dict(zip(VERDICT_FIELDS, got[1]))
    if [d["unit"], d["table"], d["row"], d["round"], d["judge"]] != \
            [row["unit"], row["table"], row["key"], str(rnd), str(j)]:
        return False
    return d["verdict"].strip().lower() in VERDICTS and not _currency(d, row, flow) and not _faults(sess, p, row)


def _check_rows(reg, todo, rnd, n, by_path):
    """(problems, models, notes, [verdict files that fail on their own and a relaunch may remove],
    [(verdict file, [sessions]) whose clean verdict was replaced: to restore, never to remove])."""
    problems, models, notes, bad, kept = [], Counter(), [], [], []
    flow = flow_now(reg)
    for row in todo:
        name = f"{row['table']} {row['key']}"
        stale = _stale(reg, row, rnd)
        if stale:
            notes.append(f"{name}: round {rnd}: {len(stale)} stale verdict(s) at an older content of the row: "
                         + ", ".join(p.name for p in stale[:3]))
        used = []
        for j in range(1, n + 1):
            p = verdict_path(reg, row, rnd, j)
            tag = f"{name}: round {rnd} judge {j}"
            if not p.is_file():
                problems.append(f"{tag}: no verdict file ({p.name})")
                continue
            before = len(problems)
            v = read_verdict(p)
            if v is None:
                problems.append(f"{tag}: {p.name} is not a well-formed verdict file")
            elif [v["unit"], v["table"], v["row"], v["round"], v["judge"]] != \
                    [row["unit"], row["table"], row["key"], str(rnd), str(j)]:
                problems.append(f"{tag}: {p.name} names another row, round or judge")
            else:
                problems += [f"{tag}: {x}" for x in _currency(v, row, flow)]
            wrote = by_path.get(paths.norm(p), [])
            if not wrote:
                problems.append(f"{tag}: no judge session wrote {p.name} with Write")
                bad.append(p)
                continue
            sess, superseded = effective_writer(p, wrote)
            # a superseded writer whose own Write was a clean verdict of this row, round and judge: its verdict is
            # gone from disk, replaced (a lead re-rolling a judge, say). Not counted toward `bad`: removing the
            # replacement would not bring the clean verdict back.
            replaced = [s for s in superseded if _clean_verdict(s, p, wrote, row, rnd, j, flow)]
            if replaced:
                problems.append(f"{tag}: a clean verdict by {', '.join(pathlib.Path(s.path).stem for s in replaced)} "
                                f"was replaced ({p.name})")
                before += 1
                kept.append((p, replaced))
            rest = [s for s in superseded if s not in replaced]
            if rest:
                notes.append(f"{tag}: superseded writer(s) of {p.name}: "
                             + ", ".join(pathlib.Path(s.path).stem for s in rest))
            if sess is None:
                problems.append(f"{tag}: no judge session's Write matches the file on disk ({p.name})")
                bad.append(p)
                continue
            used.append(sess.path)
            models.update(sess.models or {"(none recorded)"})
            problems += [f"{tag}: {f}" for f in _faults(sess, p, row)]
            if len(problems) > before:
                bad.append(p)
        if len(set(used)) < len(used):
            problems.append(f"{name}: round {rnd}: one session wrote more than one of its verdicts")
    gone = {q for q, _ in kept}
    return problems, models, notes, [q for q in bad if q not in gone], kept


def _moved_notes(reg, unit, rnd, n, mode=None):
    """Notes for the rows this round no longer holds: flagged in it, fixed since, due in the next round."""
    last = settings(reg)["judge_rounds"]
    rws = rows(reg, unit)[0]
    if run_settings.load(reg).get("mapping") == "fast":  # only the rows a proposal rests on (selective.py)
        import selective
        keep = (selective.selected(reg) or {}).get(unit, set())
        rws = [r for r in rws if (r["table"], r["key"]) in keep]
    if (mode or ("all" if rnd <= 1 else "flagged")) != "all":
        rws = flagged_in(reg, rws, rnd - 1, n)
    return [f"{r['table']} {r['key']}: round {rnd}: flagged, fixed since (its verdicts here are stale); due in round "
            f"{rnd + 1}" for r in rws if _moved_on(reg, r, rnd, last)]


def check(reg, unit, round=None, transcripts=None, _writers=None):
    """The judging of the unit's latest round (or `round`) happened as the kit says, read from the transcripts."""
    reg = pathlib.Path(reg).resolve()
    n = settings(reg)["judges"]
    rnd = round or latest_round(reg, unit)
    fixers = flow_fixer_problems(reg, transcripts) if unit == "flow" else []
    if rnd == 0:
        rws = rows(reg, unit)[0]
        return Result(unit, 0, len(rws), ([f"no verdict files in judging/{unit}/"] if rws else []) + fixers,
                      Counter())
    todo = scope(reg, unit, rnd, n)
    by_path = writers(reg, transcripts) if _writers is None else _writers
    problems, models, notes, _, _ = _check_rows(reg, todo, rnd, n, by_path)
    problems += fixers
    for r in range(1, rnd + 1):
        problems += record_problems(reg, unit, r)
    moved = _moved_notes(reg, unit, rnd, n)
    if not todo and not moved and round_files(reg, unit, rnd):
        problems.append(f"round {rnd} has verdict files but no row in scope claims them (old names, or rows re-keyed "
                        "or withdrawn)")
    problems += _sweep(reg, unit, rnd, n, todo, by_path, notes)
    return Result(unit, rnd, len(todo), problems, models, notes=moved + notes)


def flow_fixer_problems(reg, transcripts=None):
    """The fixers of the unit `flow`, each a subagent of the flow worked now that wrote one of its tables (the lead
    tables at the root, the lead's rows in merge/lead-rows/): each must be a `bfo-unit-reader` subagent launched on a
    prompt a kit script wrote (kit_prompt_problem) that wrote that one table and nothing else and ran no shell. A main
    session's writes are the lead's own (Steps 1-3) and are not checked here."""
    import provenance  # it imports this module
    reg = pathlib.Path(reg).resolve()
    mine = {paths.norm(p) for p in [reg / f"{t}.csv" for t in FLOW_TABLES]
            + [reg / layout.LEAD_ROWS / f"{t}.csv" for t in MERGED]}
    out, fixers = [], []
    for s in provenance.flow_sessions(reg, transcripts)[0]:
        written = {p for _, p in s.writes}
        if written & mine and pathlib.Path(s.path).parent.name == "subagents":
            fixers.append(s)
    for s in fixers:
        written = {p for _, p in s.writes}
        name = pathlib.Path(s.path).stem
        _, why = provenance.agent_type(s.path, provenance.READER_TYPE)
        if why:
            out.append(f"fixer {name} of the flow's tables is {why}")
        if len(written) > 1:
            out.append(f"fixer {name} wrote more than its own table: " + ", ".join(sorted(written)[:4]))
        # a shell run, or a fixer launched on a prompt no kit script wrote, is superseded by a clean fixer of the
        # same table launched after it on a kit prompt (the relaunch): what it changed is judged again, as any
        # change to a row is
        later = [x for x in fixers if x is not s and not x.shell and not kit_prompt_problem(x, reg)
                 and {p for _, p in x.writes} == written
                 and provenance.judges_when((x.first, 0)) > provenance.judges_when((s.first, 0))]
        if later:
            continue
        unprompted = kit_prompt_problem(s, reg)
        if unprompted:
            out.append(f"fixer of the flow's tables: {unprompted}; relaunch it: readers.py prompt <reg> flow "
                       "--mode fix")
        if s.shell:
            out.append(f"fixer {name} of the flow's tables ran a shell; relaunch it: readers.py prompt <reg> flow "
                       "--mode fix")
    return out


def _sweep(reg, unit, rnd, n, todo, by_path, notes):
    """Every row outside this round's scope is checked at its own latest round, at its current content: a row edited,
    added or re-keyed after a later round began, or a verdict overwritten since, is not done until judged."""
    last = settings(reg)["judge_rounds"]
    held = {(r["table"], r["key"]) for r in todo}
    problems = []
    for row in rows(reg, unit)[0]:
        if (row["table"], row["key"]) in held or _moved_on(reg, row, rnd, last):
            continue
        name = f"{row['table']} {row['key']}"
        at = next((r for r in range(rnd, 0, -1) if _any_hash(reg, row, r)), 0)
        if at == 0:
            problems.append(f"{name}: not judged in any round")
        elif _moved_on(reg, row, at, last) or (at < last and _flags(_round(reg, row, at, n))):
            problems.append(f"{name}: flagged in round {at}, not judged in round {at + 1}")
        else:
            p2, _, n2, _, _ = _check_rows(reg, [row], at, n, by_path)
            problems += p2
            notes += n2
    return problems


def fix_check(reg, unit, round=None, transcripts=None):
    """Every row flagged in a round before judge_rounds was judged again in the next round, and that judging passes
    the check; a row flagged in the last round carries its disputed label. `round` stops at that round."""
    reg = pathlib.Path(reg).resolve()
    s = settings(reg)
    n = s["judges"]
    by_path = writers(reg, transcripts)
    problems, models, notes, rnd, count = [], Counter(), [], 1, 0
    rws = rows(reg, unit)[0]
    while True:
        flagged = flagged_in(reg, rws, rnd, n)
        if not flagged or (round and rnd >= round):
            break
        count += len(flagged)
        if rnd >= s["judge_rounds"]:
            for r in flagged:
                cell = r["cells"][r["header"].index(r["claim"])]
                # disputed on the last round's verdicts at any content: an edit after it does not undo the dispute
                if len(_any_hash(reg, r, rnd)) >= n and not cell.startswith(DISPUTED.strip()):
                    problems.append(f"{r['table']} {r['key']}: disputed in round {rnd} but not labelled "
                                    "(run judges.py collect)")
            break
        missing = [r for r in flagged if not _any_hash(reg, r, rnd + 1)]
        problems += [f"{r['table']} {r['key']}: flagged in round {rnd}, not judged in round {rnd + 1}"
                     for r in missing]
        # a row flagged again in the next round and fixed since is due in the round after; the loop reaches it there
        due = [r for r in flagged if r not in missing and not _moved_on(reg, r, rnd + 1, s["judge_rounds"])]
        p2, m2, n2, _, _ = _check_rows(reg, due, rnd + 1, n, by_path)
        problems += p2
        models.update(m2)
        notes += n2
        rnd += 1
    classes = [line for r in range(1, s["judge_rounds"]) for line in fix_lines(reg, unit, r)]
    return Result(unit, rnd, count, problems, models, what="Fixing", notes=classes + notes)


# ---- collect ----

def _units(reg):
    reg = pathlib.Path(reg)
    got = [r["unit"] for r in tables.dicts(reg / layout.UNITS_CSV) if r.get("unit")]
    got.append("flow")
    j = layout.judging_dir(reg)
    if j.is_dir():
        got += sorted(d.name for d in j.iterdir() if d.is_dir())
    return list(dict.fromkeys(got))


def _label(disputed):
    by_file = {}
    for r in disputed:
        by_file.setdefault(r["path"], []).append(r)
    for path, rs in by_file.items():
        header, body = tables.grid(path)
        for r in rs:
            cells = body[r["index"]]
            cells += [""] * (len(header) - len(cells))
            c = header.index(r["claim"])
            if not cells[c].startswith(DISPUTED.strip()):
                cells[c] = DISPUTED + cells[c]
        tables.write_grid(path, header, body)


def row_state(reg, row, top, s):
    """(state, round, the verdicts it is read from) of a row whose unit's latest round is `top`, `s` the settings: its
    round is its latest by identity; its state is read from the verdicts at its current content, and while those are
    short a flag at an older content keeps it flagged (it is being fixed)."""
    n = s["judges"]
    rnd = next((r for r in range(top, 0, -1) if _any_hash(reg, row, r)), 0)
    got = _round(reg, row, rnd, n) if rnd else []
    every = _any_hash(reg, row, rnd) if rnd else []
    if rnd and len(got) < n and _flags(every) and (rnd < s["judge_rounds"] or len(every) >= n):
        return ("flagged" if rnd < s["judge_rounds"] else "disputed"), rnd, every
    if rnd == 0 or len(got) < n:
        return "pending", rnd, got
    if _flags(got) or (rnd >= s["judge_rounds"] and _flags(every)):
        return ("disputed" if rnd >= s["judge_rounds"] else "flagged"), rnd, got
    return "passed", rnd, got


def disputed_rows(reg, unit):
    """{(table, key)} of the unit's rows its verdicts make disputed: the rows `collect` labels."""
    reg = pathlib.Path(reg).resolve()
    s, top = settings(reg), latest_round(reg, unit)
    if not top:
        return set()
    return {(r["table"], r["key"]) for r in rows(reg, unit)[0] if row_state(reg, r, top, s)[0] == "disputed"}


def _unmatched_calls(reg):
    """{"<unit>/<row_id>"} of the calls a merge of the unit folders leaves unmatched now, or none outside a split run."""
    if not (pathlib.Path(reg) / layout.UNITS_CSV).is_file():
        return set()
    import merge  # only here: merge reads this module
    try:
        files, _, _ = merge.build(reg)
    except (OSError, ValueError, KeyError):  # no merge to be had: the call is labelled as any disputed row is
        return set()
    return {r["call"] for r in csv.DictReader(io.StringIO(files.get(layout.UNMATCHED_CSV) or ""))}


def collect(reg, transcripts=None):
    """Write judging/judgements.csv, label disputed rows, and count the models the judges ran on. A disputed call the
    merge leaves unmatched is left unlabelled: its re-read labels it (merge.py), and a label `collect` put there
    first would have no session behind it, so no re-read could resolve the call."""
    reg = pathlib.Path(reg).resolve()
    s = settings(reg)
    out, disputed = [], []
    for unit in _units(reg):
        top = latest_round(reg, unit)
        for row in rows(reg, unit)[0]:
            state, rnd, got = row_state(reg, row, top, s)
            flags = _flags(got)
            if state == "disputed":
                disputed.append((unit, row))
            reasons = [v["reason"] if v else "unreadable verdict file" for _, v in flags]
            out.append({"unit": unit, "table": row["table"], "row": row["key"], "round": rnd, "judges": len(got),
                        "says": len(got) - len(flags), "flagged": len(flags), "state": state,
                        "reasons": " | ".join(reasons)})
    layout.judging_dir(reg).mkdir(exist_ok=True)
    tables.write(reg / layout.JUDGEMENTS_CSV, JUDGEMENT_FIELDS, out, lineterminator="\r\n")
    calls = [f"{u}/{r['key']}" for u, r in disputed if r["table"] == "calls"]
    left = _unmatched_calls(reg) if calls else set()
    _label([r for u, r in disputed if not (r["table"] == "calls" and f"{u}/{r['key']}" in left)])
    models = Counter()
    for p, wrote in writers(reg, transcripts).items():
        eff = effective_writer(p, wrote)[0] or wrote[-1][0]
        for m in eff.models or {"(none recorded)"}:
            models[m] += 1
    return {"rows": len(out), "states": Counter(r["state"] for r in out), "models": dict(models)}


def read_judgements(reg):
    return tables.dicts(pathlib.Path(reg) / layout.JUDGEMENTS_CSV)


# ---- command line ----

def _opt(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return default


def _guarded(reg, unit, rnd):
    """2, having said why, when judging `unit` in round `rnd` is out of mapping's order (guard.py); else None."""
    import guard
    problem = guard.require(reg, f"judge {2 if rnd >= 2 else 1}", unit=unit)
    if problem:
        print(f"REFUSED: {problem}. Nothing was launched.", file=sys.stderr)
        return 2
    return None


def main(argv):
    """_main, then the timing record rewritten for a register mapped fast (timings.refresh_if_fast)."""
    try:
        return _main(argv)
    finally:
        import timings
        timings.refresh_if_fast(argv, "judges.py")


def _main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    argv = list(argv)
    if not argv:
        sys.exit(__doc__)
    cmd = argv.pop(0)
    transcripts = _opt(argv, "--transcripts")
    rnd = _opt(argv, "--round")
    rnd = int(rnd) if rnd else None
    if cmd == "rows":
        rws, uncited = rows(argv[0], argv[1])
        for r in rws:
            print(f"{r['table']}\t{r['key']}\t{r['claim']}: {r['cells'][r['header'].index(r['claim'])]}\t"
                  f"{r['citations']}")
        print(f"{len(rws)} row(s) to judge; {uncited} row(s) cite no code and are not judged")
        return 0
    if cmd == "run":
        mode, model = _opt(argv, "--rows"), _opt(argv, "--model")
        if "--set-aside" in argv and (argv.index("--set-aside") + 1 >= len(argv)
                                      or argv[argv.index("--set-aside") + 1].startswith("--")):
            print("REFUSED: --set-aside needs the person's reason after it, in quotes, word for word. Nothing was "
                  "set aside or launched.", file=sys.stderr)
            return 2
        words = _opt(argv, "--set-aside")
        again = "--again" in argv
        argv = [a for a in argv if a != "--again"]
        reg, ws, unit = argv[:3]
        import run_lock  # the register is written by one run at a time
        run_lock.guard(reg)
        rnd = rnd or 1
        refused = _guarded(reg, unit, rnd)
        if refused:
            return refused
        held = workspace_problem(reg, scope(reg, unit, rnd, settings(reg)["judges"], mode), ws)
        if held:
            print(f"REFUSED: {held}. Nothing was launched.", file=sys.stderr)
            return 2
        launched = run(reg, ws, unit, rnd, mode, model, again=again, transcripts=transcripts,
                       set_aside_words=words)
        n = settings(reg)["judges"]
        missing = [verdict_path(reg, r, rnd, j).name for r in scope(reg, unit, rnd, n, mode)
                   for j in range(1, n + 1) if not verdict_path(reg, r, rnd, j).is_file()]
        print(f"Judges launched: {launched} for unit {unit}, round {rnd}; verdict files missing: {len(missing)}")
        print("\n".join(f"  missing: {m}" for m in missing[:25]))
        return 0 if not missing else 1
    if cmd == "emit":
        mode, ws = _opt(argv, "--rows"), _opt(argv, "--ws")
        again = "--again" in argv
        argv = [a for a in argv if a != "--again"]
        refused = _guarded(argv[0], argv[1], rnd or 1)
        if refused:
            return refused
        held = launch_problem(argv[0], argv[1], rnd or 1, mode, ws)
        if held:
            print(f"REFUSED: {held}. Nothing was launched.", file=sys.stderr)
            return 2
        print("\n".join(emit(argv[0], argv[1], rnd or 1, mode, ws, transcripts, again)))
        return 0
    if cmd == "collect":
        got = collect(argv[0], transcripts)
        print(f"judgements.csv: {got['rows']} row(s): "
              + ", ".join(f"{c} {k}" for k, c in sorted(got["states"].items())))
        print("\n".join(_model_lines(got["models"])))
        return 0
    if cmd in ("--check", "--fix-check"):
        fn = check if cmd == "--check" else fix_check
        r = fn(argv[0], argv[1], round=rnd, transcripts=transcripts)
        print("\n".join(r.lines()))
        return 0 if r.passed else 1
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
