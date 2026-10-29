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

REPLIES = "replies"  # the unit readers' replies, <unit>-<mode>.json

UNITS_COLS = ("unit", "deployable", "repository", "paths", "files", "lines", "reader_facts", "calls", "called_by",
              "note")
# a unit's calls.csv; a file without `within` and `sequence` still merges, with them blank
CALLS_COLS = ("row_id", "from_part", "protocol", "to_unit", "to_part", "via", "operation", "within", "sequence",
              "step_hint", "carries_case_id", "source")
VERDICT_COLS =["unit", "table", "row", "round", "judge", "verdict", "reason"]
JUDGEMENT_COLS = ["unit", "table", "row", "round", "judges", "says", "flagged", "state", "reasons"]
UNMATCHED_COLS = ["call", "from_unit", "to_unit", "protocol", "operation", "source", "why"]
JOBS_COLS = ["item", "step", "state", "tries", "reason", "session", "updated"]


def unit_dir(reg, unit):
    """A unit's folder, written only by its reader."""
    return pathlib.Path(reg) / UNITS / unit


def judging_dir(reg, unit=None):
    """The judging folder, or one unit's verdict files in it."""
    p = pathlib.Path(reg) / JUDGING
    return p / unit if unit else p
