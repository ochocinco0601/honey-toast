"""Where a split run keeps its files in the register folder, and the columns of the files it hands between modules.

The one place the layout of split-run-formats.md is written down in code: every split-run module builds its paths
and column lists from here, so a change to the layout is a change to this file. Paths are relative to the register
folder <reg>, written with `/`; join them as `reg / UNITS_CSV`. Python standard library only."""
import pathlib

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
