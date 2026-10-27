"""Find the semgrep executable without depending on PATH.

WHY THIS EXISTS
    A bare `semgrep` works only if the scripts directory is on PATH.
    `pip install semgrep` puts `semgrep.exe` in the interpreter's scripts
    directory, and on Windows that directory usually isn't on PATH -- Python's own
    install adds the interpreter directory and not `Scripts/`.

    The failure is silent in the way that matters: with semgrep installed and
    working, every entry point dies with `FileNotFoundError: [WinError 2]` before
    it asserts anything, and nothing names the real cause.

    `DFO_SEMGREP` still wins, so an explicit choice is never second-guessed.
"""

import os
import shutil
import sysconfig


def resolve():
    """The semgrep command to invoke. Falls back to the bare name so that when it
    genuinely is not installed, the caller's own error message is the one raised."""
    override = os.environ.get("DFO_SEMGREP")
    if override:
        return override

    on_path = shutil.which("semgrep")
    if on_path:
        return on_path

    for key in ("scripts", "purelib"):
        try:
            directory = sysconfig.get_path(key)
        except (KeyError, TypeError):
            continue
        if not directory:
            continue
        for name in ("semgrep.exe", "semgrep"):
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate):
                return candidate

    return "semgrep"
