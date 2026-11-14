"""A split run's settings: run-settings.json in the register folder, and the one set of defaults every module reads
it with (split-run-formats.md). Any key may be missing from the file; the default below then holds.

`on_change` is the kit's choice of what to run after the job runner changes state (redraw the sponsor's page). It is
a default here, not in jobs.py: the runner receives it as a setting and knows nothing of the page.
Python standard library only."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import register_layout as layout  # noqa: E402

DEFAULTS = {"judges": 3, "judge_rounds": 2, "unit_lines": 4000, "parallel": 6, "merge_rereads": 50,
            "lock_stale_minutes": 20, "on_change": "python run_page.py {reg}"}


def load(reg):
    """The defaults updated with the file's values (unknown keys kept), a fresh dict each call. A missing file gives
    the defaults; a file that is not a JSON object raises ValueError, and the caller decides whether to go on."""
    s = dict(DEFAULTS)
    p = pathlib.Path(reg) / layout.SETTINGS
    if p.is_file():
        got = json.loads(p.read_text(encoding="utf-8-sig"))
        if not isinstance(got, dict):
            raise ValueError(f"{p}: not a JSON object")
        s.update(got)
    return s


def number(s, key):
    """A count setting as an int, its default when the value is blank or zero."""
    return int(s.get(key) or DEFAULTS[key])
