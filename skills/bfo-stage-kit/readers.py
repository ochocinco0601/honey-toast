"""Launch the unit readers of a split run, one Claude Code process per unit, several at once.

Usage: python readers.py run <register folder> <workspace> <unit>... [--mode read|retry|fix] [--model ID]
       python readers.py prompt <register folder> <unit> [--mode read|retry|fix]      prints the prompt

Each reader is `claude -p` with the working folder the workspace (so its transcript lands where the reading check
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


def unit_row(reg, unit):
    p = pathlib.Path(reg) / layout.UNITS_CSV
    for r in tables.dicts(p):
        if r.get("unit") == unit:
            return r
    raise SystemExit(f"no unit {unit!r} in {p}")


def formats():
    p = FORMATS
    return ("## The file formats (split-run-formats.md)\n\n" + p.read_text(encoding="utf-8")) if p.is_file() else ""


def prompt(reg, unit, mode="read"):
    reg = pathlib.Path(reg).resolve()
    u = unit_row(reg, unit)
    body = judges.agent_body(AGENT)
    paths = "; ".join(p for p in u.get("paths", "").split(";") if p)
    out = [body, "", "## Your unit", "",
           f"Unit: {unit}",
           f"Deployable: {u.get('deployable', '')}",
           f"Paths it covers, from the workspace root (the current folder): {paths}",
           f"Size: {u.get('lines', '')} lines of source in {u.get('files', '')} files; "
           f"{u.get('reader_facts', '')} code-reader findings",
           f"Register folder: {reg}",
           f"Your folder (write only here): {layout.unit_dir(reg, unit)}",
           f"The flow and its steps: {reg / 'flows.csv'}, {reg / 'lifecycle.csv'}, {reg / 'stages.csv'}, "
           f"{reg / 'steps.csv'}; the plan: {reg / 'PLAN.md'}; the code reader's findings: {reg / 'fact-base.json'}",
           ""]
    if mode == "retry":
        why = [r.get("reason", "") for r in tables.dicts(reg / layout.JOBS_CSV)
               if r.get("item") == unit and r.get("step") == "read"]
        out += ["## The check that failed", "", "\n".join(w for w in why if w) or "(no output recorded)", ""]
    if mode == "fix":
        rows = [r for r in tables.dicts(reg / layout.JUDGEMENTS_CSV)
                if r.get("unit") == unit and r.get("state") == "flagged"]
        out += ["## Rows to fix", ""] + [f"- {r['table']} {r['row']}: {r.get('reasons', '')}" for r in rows] + [""]
    out.append(formats())
    return "\n".join(out)


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
    jobs = [(u, command(prompt(reg, u, mode), model)) for u in units]
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
    argv = list(argv)
    mode = _opt(argv, "--mode", "read")
    model = _opt(argv, "--model")
    if len(argv) >= 3 and argv[0] == "prompt":
        print(prompt(argv[1], argv[2], mode))
        return 0
    if len(argv) >= 4 and argv[0] == "run":
        import run_lock  # the register is written by one run at a time
        run_lock.guard(argv[1])
        n = run(argv[1], argv[2], argv[3:], mode, model)
        print(f"{n} reader(s) finished; replies in {pathlib.Path(argv[1]) / layout.REPLIES}")
        return 0
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
