"""Fail if any beat is still animating when the voice reaches the thing it draws.

The explainer's mechanism is that a picture is complete and still before the line that explains it
starts. That is arithmetic over timing.json (measured) and the beats in scenes.py, the same data the
page is generated from, so it is checked rather than watched:

  - a beat with no `plus` is anchored to its line's silence: fire + ramp must finish before that
    line's first word;
  - a beat with `plus` is placed by hand inside a line, because what it draws is a phrase: fire +
    ramp must finish before the NEXT line's silence begins (or, on a scene's last line, before the
    scene's tail).

A beat whose `line` is not a whole number, or whose `plus` is not a number, fails the run.
A `held` beat (what the previous scene left on screen) is shown at once and has nothing to land; it
may still fade out (`outLine`, `outPlus`), and a jump lands after that fade, as for any beat.

Run: python check_timing.py <video folder>      (exit 1 on any violation)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explainer  # noqa: E402

video = explainer.Video(sys.argv[1] if len(sys.argv) > 1 else ".")
report, bad = explainer.check_timing(video)
print("\n".join(report))
if bad:
    print("\nFAIL")
    for b in bad:
        print("  " + b)
    sys.exit(1)
print("\nPASS - every beat is finished before the voice reaches it")
