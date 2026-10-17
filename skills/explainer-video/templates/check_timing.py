"""Fail if any beat is still animating when the voice reaches the thing it draws.

The explainer's whole mechanism is that a picture is complete and still before the line that
explains it starts. That is arithmetic over `timing.json` (measured) and the page's beats, so
it is checked rather than watched:

  - a beat with no `plus` is anchored to its line's silence: fire + ramp must finish before
    that line's first word;
  - a beat with `plus` is placed by hand inside a line, because what it draws is a phrase:
    fire + ramp must finish before the NEXT line's silence begins (or, on a scene's last line,
    before the scene's tail).

A beat whose `line` or `plus` is an expression rather than a literal -- anything built in a
loop -- cannot be read from the source. Those are counted and named, and the run FAILS, because
a checker that silently skips what it cannot parse reports the same clean result whether the
page is right or unreadable. Write beats literally.

Needs only Python. Run: python check_timing.py        (exit 1 on any violation)
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
RAMP = 0.25      # must match the page; the reduced-motion value (0.12) is shorter, so safe
MAX_LEAD = 1.2   # must match the page

pages = sorted(HERE.glob("*-explainer.html"))
if len(pages) != 1:
    sys.exit(f"expected exactly one *-explainer.html, found {len(pages)}")
html = pages[0].read_text(encoding="utf-8")
timing = json.loads((HERE / "timing.json").read_text(encoding="utf-8-sig"))
spec = json.loads((HERE / "narration.json").read_text(encoding="utf-8-sig"))
TAIL = spec["tail"]

# \b so that a word such as "timeline:" in a comment is not read as a beat.
BEAT = re.compile(r"\bline:\s*([^,}\n]+?)\s*(?:,\s*plus:\s*([^,}\n]+?)\s*)?(?:,|\})")
LITERAL = re.compile(r"\d+(?:\.\d+)?$")


def lead(tm, n):
    return max(0.0, tm["starts"][n] - min(MAX_LEAD, max(0.0, tm["pre"][n] - 0.05)))


# Beats built in a loop are declared outside S.push, and those declarations sit BETWEEN two
# scenes in the source -- so they must be lifted out before slicing, or they are attributed to
# whichever scene happens to precede them. Collect them by the array they are pushed onto, and
# re-attach each to the scene whose `beats:` names it.
loose = {m.group(1): m.group(2) for m in
         re.finditer(r"var (\w+Beats) = \[(.*?)\n  S\.push", html, re.S)}
stripped = re.sub(r"var \w+Beats = \[.*?(?=\n  S\.push)", "", html, flags=re.S)

# One slice of source per scene, in order, so a beat is attributed to the right clip.
chunks = stripped.split("S.push({")[1:]

measured = hand = 0
bad, unreadable = [], []

for chunk in chunks:
    sid = re.search(r'id: "([^"]+)"', chunk).group(1)
    tm = timing[sid]
    nlines = len(tm["starts"])
    source = chunk
    for name, body in loose.items():
        if re.search(r"beats:\s*" + name + r"\b", chunk):
            source += body
    beats = BEAT.findall(source)
    if not beats:
        sys.exit(f"{sid}: no beats parsed - the regex no longer matches the page")

    for n_raw, plus_raw in beats:
        if not LITERAL.match(n_raw):
            unreadable.append(f"{sid}: line is `{n_raw}`, not a literal")
            continue
        n = int(float(n_raw))
        if n >= nlines:
            bad.append(f"{sid} beat on line {n}: the scene has {nlines} lines")
            continue
        if plus_raw and not LITERAL.match(plus_raw):
            unreadable.append(f"{sid} line {n}: plus is `{plus_raw}`, not a literal")
            continue
        if not plus_raw:
            measured += 1
            at, deadline = lead(tm, n), tm["starts"][n]
            what = f"{sid} line {n} (measured)"
        else:
            hand += 1
            at = tm["starts"][n] + float(plus_raw)
            deadline = (tm["starts"][n + 1] - tm["pre"][n + 1]) if n + 1 < nlines \
                else tm["dur"] - TAIL
            what = f"{sid} line {n} +{plus_raw} (hand-placed)"
        if at + RAMP > deadline + 1e-9:
            bad.append(f"{what}: ends {at + RAMP:.2f}s, deadline {deadline:.2f}s")

total = sum(v["dur"] for v in timing.values())
pause = (len(timing) * (spec["head"] + TAIL)
         + sum(line.get("pause", spec["gap"])
               for scene in spec["scenes"] for line in scene["lines"][:-1]))

print(f"beats: {measured} placed from measurement, {hand} by hand, "
      f"{measured + hand} readable in all")
print(f"runtime: {total:.1f}s ({int(total // 60)}:{int(total % 60):02d}); "
      f"silence {pause:.1f}s, {pause / total * 100:.0f}% of it")

if unreadable:
    print(f"\nFAIL - {len(unreadable)} beat(s) this script cannot read:")
    for u in unreadable:
        print("  " + u)
if bad:
    print("\nFAIL")
    for b in bad:
        print("  " + b)
if unreadable or bad:
    sys.exit(1)
print("\nPASS - every beat is finished before the voice reaches it")
