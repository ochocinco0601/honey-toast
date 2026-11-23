"""Where a split run keeps its files in the register folder, and the columns of the files it hands between modules.

The one place the layout of split-run-formats.md is written down in code: every split-run module builds its paths
and column lists from here, so a change to the layout is a change to this file. Paths are relative to the register
folder <reg>, written with `/`; join them as `reg / UNITS_CSV`. Python standard library only."""
import pathlib

CODE_ROOT = "code-root.txt"  # the folder the survey read the code from, relative to the workspace (survey.py)
SETTINGS = "run-settings.json"
SCOPE = "scope.json"  # the person's picks at the go, written by go.py
ORIENTATION = "orientation.json"  # the run's first look, for the capability brief (brief.py)
RUN_HTML = "run.html"

UNITS = "units"
UNITS_CSV = f"{UNITS}/units.csv"
FILES_CSV = "files.csv"  # in a unit's folder: every file of the unit's paths, never judged
UNIT_TABLES = ("subjects", "operations", "calls", "participation")

JUDGING = "judging"
JUDGEMENTS_CSV = f"{JUDGING}/judgements.csv"

MERGE = "merge"
LEAD_ROWS = f"{MERGE}/lead-rows"
UNMATCHED_CSV = f"{MERGE}/unmatched-calls.csv"
OUT_OF_SCOPE_CSV = f"{MERGE}/out-of-scope-calls.csv"  # calls to a service left out at the go; same columns
SUMMARY_JSON = f"{MERGE}/summary.json"

JOB = "job"
JOBS_FILE, LOCK_FILE, EVENTS_FILE, STEPS_FILE = "jobs.csv", "lock.json", "events.log", "steps.json"
JOBS_CSV = f"{JOB}/{JOBS_FILE}"
LOCK_JSON = f"{JOB}/{LOCK_FILE}"
TIMINGS_CSV = f"{JOB}/timings.csv"  # one row per agent attempt, from its transcript; written whole by timings.py

REPLIES = "replies"  # the unit readers' replies, <unit>-<mode>.json
PROMPTS = "prompts"  # prompts/<unit>/<name>.md: one agent's prompt (judges.py emit, readers.py prompt); never in units/
LAUNCH = f"{PROMPTS}/launch"  # launcher files: the pointer lines one launcher subagent launches

UNITS_COLS = ("unit", "deployable", "repository", "paths", "files", "lines", "reader_facts", "calls", "called_by",
              "note")
# a unit's calls.csv; a file without `within` and `sequence` still merges, with them blank
CALLS_COLS = ("row_id", "from_part", "protocol", "to_unit", "to_part", "via", "operation", "within", "sequence",
              "step_hint", "carries_case_id", "source")
# a verdict file names the flow it was judged in and the hash of the row as it judged it
VERDICT_COLS = ["unit", "table", "row", "round", "judge", "flow", "row_hash", "verdict", "reason"]
JUDGEMENT_COLS = ["unit", "table", "row", "round", "judges", "says", "flagged", "state", "reasons"]
UNMATCHED_COLS = ["call", "from_unit", "to_unit", "protocol", "operation", "source", "why"]
JOBS_COLS = ["item", "step", "state", "tries", "reason", "session", "updated"]
TIMINGS_COLS = ["unit", "step", "attempt", "agent", "model", "start", "end", "seconds", "turns", "input_tokens",
                "output_tokens", "cache_read_tokens", "cache_creation_tokens", "api_errors", "longest_gap_seconds",
                "gap_ends_on_error", "outcome", "prompt"]


def unit_dir(reg, unit):
    """A unit's folder, written only by its reader."""
    return pathlib.Path(reg) / UNITS / unit


def prompts_dir(reg, unit):
    """One unit's prompt files."""
    return pathlib.Path(reg) / PROMPTS / unit


def judging_dir(reg, unit=None):
    """The judging folder, or one unit's verdict files in it."""
    p = pathlib.Path(reg) / JUDGING
    return p / unit if unit else p


def holding_folder(base, repos):
    """The folder citations into `repos` start from, so that a citation starts with its repository's folder name:
    `base` (the workspace) when every repository is inside it; else the one folder they all sit directly in, wherever
    it is (a `repos/` folder beside the workspace, say); None when they sit in different folders, where no citation
    form would start with each repository's own name."""
    base = pathlib.Path(base).resolve()
    repos = [pathlib.Path(r).resolve() for r in repos]
    if not repos or all(r == base or base in r.parents for r in repos):
        return base
    parents = {r.parent for r in repos}
    return parents.pop() if len(parents) == 1 else None


def code_folders(reg):
    """{repository name: its folder (absolute, existing)} for the code rows of sources.csv: the folder recorded in
    `location` (absolute, or relative to the workspace), else the repository's name under the workspace. A row whose
    folder does not exist is left out."""
    reg = pathlib.Path(reg).resolve()
    base = reg.parent.parent
    src = reg / "sources.csv"
    if not src.is_file():
        return {}
    import csv
    out = {}
    with src.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            if (r.get("kind") or "").strip() != "code":
                continue
            name = (r.get("repository") or "").strip()
            where = (r.get("location") or "").strip() or name
            if not name or not where:
                continue
            p = (base / where).resolve()
            if p.is_dir():
                out[pathlib.PurePath(name.replace("\\", "/")).name] = p
    return out


def code_root(reg):
    """The folder the run's code is read from, which every reader's and judge's prompt names: the one the survey
    recorded (CODE_ROOT), else the folder holding the repositories sources.csv records (code_folders), else the
    workspace (the register's grandparent). None when the recorded repositories sit in different folders."""
    reg = pathlib.Path(reg).resolve()
    base = reg.parent.parent
    mark = reg / CODE_ROOT
    if mark.is_file():
        got = (base / mark.read_text(encoding="utf-8").strip()).resolve()
        if got.is_dir():
            return got
    return holding_folder(base, list(code_folders(reg).values()))
