"""Judge every row of a reading unit three times, collect the verdicts, and say whether the judging really happened.

Usage: python judges.py rows <reg> <unit>
       python judges.py run <reg> <ws> <unit> --round N [--rows all|flagged] [--model ID]
       python judges.py collect <reg> [--transcripts DIR]
       python judges.py --check <reg> <unit> [--round N] [--transcripts DIR]
       python judges.py --fix-check <reg> <unit> [--round N] [--transcripts DIR]

Every row of a unit that cites code gets `judges` judges (run-settings.json, default 3): each a fresh Claude Code
process (`claude -p`, cwd the workspace <ws>) given the judge's agent definition (agents/bfo-row-judge.md) and one row,
which opens the cited code with Read and writes its verdict, and nothing else, to
`judging/<unit>/r<round>-j<n>-<table>-<row key>.csv`. A row any judge flags is fixed by its reader and judged again in
the next round, only the flagged rows; still flagged in round `judge_rounds` (default 2), it is disputed, and
`collect` puts `disputed: ` at the start of its claim cell. Formats: split-run-formats.md.

`--check` reads the verdict files and Claude Code's own transcripts (found as reading_check.py finds them): for the
unit's latest round, every row judged in it has `judges` verdict files, each written with Write by a different session
that wrote nothing else, ran no shell, and opened every cited line with Read. It reports the model(s) the judges ran
on. `--fix-check`: every row flagged in a round before the last has the next round's verdicts, passing the same check,
and every disputed row carries its label. Exit status 0 only when the check passes. `run` passes `--model` only when
given one (the model the lead session runs on) or when the agent definition names one other than `inherit`."""
import csv
import io
import json
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
NOT_ROWS = {"sources", "how-made", "survey", "set-aside", "re-read", "re-read-history", "about"}
MERGED = {"subjects", "participation"}  # rewritten by merge.py from the units, which are judged in their own folders
ALLOWED = "Read,Grep,Glob,Write"
DISALLOWED = "Bash,PowerShell,Edit,Agent,WebFetch,WebSearch"
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
DISPUTED = "disputed: "


def settings(reg):
    s = run_settings.load(reg)
    return {k: run_settings.number(s, k) for k in COUNTS}


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
        if c not in seen:
            seen.add(c)
            cites.append(c)
    claim = next((h for h in CLAIMS if h in header), header[1] if len(header) > 1 else header[0])
    return {"unit": unit, "table": table, "key": key, "header": list(header), "cells": list(cells), "cited": cites,
            "citations": "; ".join(_cite(p, a, b) for p, a, b in cites),
            "claim": claim, "path": path, "index": index}


def _cite(p, a, b):
    return p + (f":{a}" + (f"-{b}" if b != a else "") if a else "")


def _tables(reg, unit):
    reg = pathlib.Path(reg)
    if unit == "flow":
        return [p for p in sorted(reg.glob("*.csv")) if p.stem not in NOT_ROWS | MERGED]
    return [p for p in sorted(layout.unit_dir(reg, unit).glob("*.csv")) if p.name != layout.FILES_CSV]


def rows(reg, unit):
    """(judgeable rows of the unit, how many rows cite no code)."""
    out, uncited = [], 0
    for p in _tables(reg, unit):
        header, body = tables.grid(p)
        if not header:
            continue
        col = header.index("row_id") if unit != "flow" and "row_id" in header else 0
        count = Counter()
        for i, cells in enumerate(body):
            cells = cells + [""] * (len(header) - len(cells))
            base = _strip(cells[col])
            count[base] += 1
            key = base if count[base] == 1 else f"{base}#{count[base]}"
            r = make_row(unit, p.stem, key, header, cells, p, i)
            if r["cited"]:
                out.append(r)
            else:
                uncited += 1
    return out, uncited


def verdict_name(rnd, j, table, key):
    return f"r{rnd}-j{j}-{table}-{re.sub(r'[^A-Za-z0-9_-]', '_', key)}.csv"


def verdict_path(reg, row, rnd, j):
    return layout.judging_dir(pathlib.Path(reg).resolve(), row["unit"]) / verdict_name(rnd, j, row["table"], row["key"])


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


def latest_round(reg, unit):
    folder = layout.judging_dir(reg, unit)
    got = [int(m.group(1)) for p in folder.glob("r*-j*-*.csv") if (m := re.match(r"r(\d+)-j\d+-", p.name))]
    return max(got, default=0)


def _round(reg, row, rnd, n):
    """[(judge, path, verdict dict or None)] for the verdict files present for this row and round."""
    out = []
    for j in range(1, n + 1):
        p = verdict_path(reg, row, rnd, j)
        if p.is_file():
            out.append((j, p, read_verdict(p)))
    return out


def _flags(got):
    return [(j, v) for j, _, v in got if v is None or v["verdict"] != "says"]


def flagged_in(reg, rws, rnd, n):
    return [r for r in rws if _flags(_round(reg, r, rnd, n))]


def scope(reg, unit, rnd, n, mode=None):
    """The rows judged in this round: all of them in round 1, else those flagged in the round before."""
    rws = rows(reg, unit)[0]
    if (mode or ("all" if rnd <= 1 else "flagged")) == "all":
        return rws
    return flagged_in(reg, rws, rnd - 1, n)


# ---- run ----

def prompt(body, row, rnd, j, path):
    fields = "\n".join(f"- {h}: {v}" for h, v in zip(row["header"], row["cells"]) if v.strip())
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow([row["unit"], row["table"], row["key"], rnd, j, ""])
    return (f"{body}\n\n## The row\n\n"
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


def run(reg, ws, unit, rnd, mode=None, model=None, launcher=None, agent=None):
    """Launch a judge for every verdict file of this round not yet written; returns how many were launched."""
    s = settings(reg)
    meta, body = _split_agent(agent)
    if not model and meta.get("model", "inherit") not in ("", "inherit"):
        model = meta["model"]
    jobs = []
    for row in scope(reg, unit, rnd, s["judges"], mode):
        for j in range(1, s["judges"] + 1):
            p = verdict_path(reg, row, rnd, j)
            if not p.is_file():
                jobs.append(command(prompt(body, row, rnd, j, p), model))
    if jobs:
        layout.judging_dir(reg, unit).mkdir(parents=True, exist_ok=True)
        cwd = str(pathlib.Path(ws).resolve())
        with ThreadPoolExecutor(max(1, s["parallel"])) as ex:
            list(ex.map(lambda c: (launcher or _launch)(c, cwd), jobs))
    return len(jobs)


# ---- transcripts ----

class Session:
    """One transcript: what it wrote, whether it ran a shell, which models answered, what it read."""

    def __init__(self, path):
        self.path = path
        self.writes = []  # (tool, normalised path)
        self.shell = False
        self.models = set()
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                m = d.get("message") if isinstance(d, dict) else None
                if not isinstance(m, dict):
                    continue
                if d.get("type") == "assistant" and m.get("model") and m.get("model") != "<synthetic>":
                    self.models.add(m["model"])
                content = m.get("content")
                for b in content if isinstance(content, list) else []:
                    if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                        continue
                    name, inp = b.get("name"), b.get("input") or {}
                    if name in WRITE_TOOLS:
                        self.writes.append((name, paths.norm(inp.get("file_path") or inp.get("notebook_path") or "")))
                    elif name in ("Bash", "PowerShell"):
                        self.shell = True
        self._reads = None

    def reads(self):
        if self._reads is None:
            self._reads = rc.reads([self.path])
        return self._reads


def _folders(reg, transcripts):
    if transcripts:
        return [pathlib.Path(t) for t in (transcripts if isinstance(transcripts, (list, tuple)) else [transcripts])]
    return rc.project_folders(reg)


def writers(reg, transcripts=None):
    """{normalised verdict file path: [sessions that wrote it with Write]}, main sessions and subagents alike."""
    root = paths.norm(layout.judging_dir(pathlib.Path(reg).resolve())) + "/"
    got = {}
    for folder in _folders(reg, transcripts):
        for f in sorted(folder.rglob("*.jsonl")):
            s = Session(f)
            for tool, p in s.writes:
                if tool == "Write" and p.startswith(root):
                    got.setdefault(p, []).append(s)
    return got


def _model_lines(models):
    if not models:
        return ["Judges ran on: no model recorded in the transcripts"]
    return ["Judges ran on: " + ", ".join(f"{m} ({n} judge session{'s' if n != 1 else ''})"
                                          for m, n in sorted(models.items()))]


# ---- check ----

class Result:
    def __init__(self, unit, rnd, n, problems, models, what="Judging"):
        self.unit, self.round, self.rows, self.problems = unit, rnd, n, problems
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
        return out + _model_lines(self.model_counts)


def _check_rows(reg, todo, rnd, n, by_path):
    problems, models = [], Counter()
    for row in todo:
        name = f"{row['table']} {row['key']}"
        used = []
        for j in range(1, n + 1):
            p = verdict_path(reg, row, rnd, j)
            tag = f"{name}: round {rnd} judge {j}"
            if not p.is_file():
                problems.append(f"{tag}: no verdict file ({p.name})")
                continue
            v = read_verdict(p)
            if v is None:
                problems.append(f"{tag}: {p.name} is not a well-formed verdict file")
            elif [v["unit"], v["table"], v["row"], v["round"], v["judge"]] != \
                    [row["unit"], row["table"], row["key"], str(rnd), str(j)]:
                problems.append(f"{tag}: {p.name} names another row, round or judge")
            ws = by_path.get(paths.norm(p), [])
            if not ws:
                problems.append(f"{tag}: no judge session wrote {p.name} with Write")
                continue
            if len(ws) > 1:
                problems.append(f"{tag}: {p.name} was written by {len(ws)} sessions")
            sess = ws[0]
            used.append(sess.path)
            models.update(sess.models or {"(none recorded)"})
            other = sorted({q for t, q in sess.writes if not (t == "Write" and q == paths.norm(p))})
            if other:
                problems.append(f"{tag}: the judge session wrote other files: {', '.join(other[:3])}")
            if sess.shell:
                problems.append(f"{tag}: the judge session ran a shell")
            opened = sess.reads()
            for path, a, b in row["cited"]:
                spans = [x for q, xs in opened.items() if q.endswith("/" + path.lower()) for x in xs]
                if not paths.covered(a, b, spans):
                    problems.append(f"{tag}: the judge did not open {_cite(path, a, b)}")
        if len(set(used)) < len(used):
            problems.append(f"{name}: round {rnd}: one session wrote more than one of its verdicts")
    return problems, models


def check(reg, unit, round=None, transcripts=None, _writers=None):
    """The judging of the unit's latest round (or `round`) happened as the kit says, read from the transcripts."""
    reg = pathlib.Path(reg).resolve()
    n = settings(reg)["judges"]
    rnd = round or latest_round(reg, unit)
    if rnd == 0:
        rws = rows(reg, unit)[0]
        return Result(unit, 0, len(rws), [f"no verdict files in judging/{unit}/"] if rws else [], Counter())
    todo = scope(reg, unit, rnd, n)
    by_path = writers(reg, transcripts) if _writers is None else _writers
    problems, models = _check_rows(reg, todo, rnd, n, by_path)
    return Result(unit, rnd, len(todo), problems, models)


def fix_check(reg, unit, round=None, transcripts=None):
    """Every row flagged in a round before judge_rounds was judged again in the next round, and that judging passes
    the check; a row flagged in the last round carries its disputed label. `round` stops at that round."""
    reg = pathlib.Path(reg).resolve()
    s = settings(reg)
    n = s["judges"]
    by_path = writers(reg, transcripts)
    problems, models, rnd, count = [], Counter(), 1, 0
    rws = rows(reg, unit)[0]
    while True:
        flagged = flagged_in(reg, rws, rnd, n)
        if not flagged or (round and rnd >= round):
            break
        count += len(flagged)
        if rnd >= s["judge_rounds"]:
            for r in flagged:
                cell = r["cells"][r["header"].index(r["claim"])]
                if len(_round(reg, r, rnd, n)) >= n and not cell.startswith(DISPUTED.strip()):
                    problems.append(f"{r['table']} {r['key']}: disputed in round {rnd} but not labelled "
                                    "(run judges.py collect)")
            break
        missing = [r for r in flagged if not _round(reg, r, rnd + 1, n)]
        problems += [f"{r['table']} {r['key']}: flagged in round {rnd}, not judged in round {rnd + 1}"
                     for r in missing]
        p2, m2 = _check_rows(reg, [r for r in flagged if r not in missing], rnd + 1, n, by_path)
        problems += p2
        models.update(m2)
        rnd += 1
    return Result(unit, rnd, count, problems, models, what="Fixing")


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


def collect(reg, transcripts=None):
    """Write judging/judgements.csv, label disputed rows, and count the models the judges ran on."""
    reg = pathlib.Path(reg).resolve()
    s = settings(reg)
    n = s["judges"]
    out, disputed = [], []
    for unit in _units(reg):
        top = latest_round(reg, unit)
        for row in rows(reg, unit)[0]:
            rnd = next((r for r in range(top, 0, -1) if _round(reg, row, r, n)), 0)
            got = _round(reg, row, rnd, n) if rnd else []
            flags = _flags(got)
            if rnd == 0 or len(got) < n:
                state = "pending"
            elif flags:
                state = "disputed" if rnd >= s["judge_rounds"] else "flagged"
            else:
                state = "passed"
            if state == "disputed":
                disputed.append(row)
            reasons = [v["reason"] if v else "unreadable verdict file" for _, v in flags]
            out.append({"unit": unit, "table": row["table"], "row": row["key"], "round": rnd, "judges": len(got),
                        "says": len(got) - len(flags), "flagged": len(flags), "state": state,
                        "reasons": " | ".join(reasons)})
    layout.judging_dir(reg).mkdir(exist_ok=True)
    tables.write(reg / layout.JUDGEMENTS_CSV, JUDGEMENT_FIELDS, out, lineterminator="\r\n")
    _label(disputed)
    models = Counter()
    for ss in writers(reg, transcripts).values():
        for m in ss[0].models or {"(none recorded)"}:
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


def main(argv):
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
        reg, ws, unit = argv[:3]
        import run_lock  # the register is written by one run at a time
        run_lock.guard(reg)
        rnd = rnd or 1
        launched = run(reg, ws, unit, rnd, mode, model)
        n = settings(reg)["judges"]
        missing = [verdict_path(reg, r, rnd, j).name for r in scope(reg, unit, rnd, n, mode)
                   for j in range(1, n + 1) if not verdict_path(reg, r, rnd, j).is_file()]
        print(f"Judges launched: {launched} for unit {unit}, round {rnd}; verdict files missing: {len(missing)}")
        print("\n".join(f"  missing: {m}" for m in missing[:25]))
        return 0 if not missing else 1
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
