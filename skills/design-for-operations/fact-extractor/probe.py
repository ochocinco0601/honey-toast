"""Coverage probe — which enumerated framework idioms can this rule set actually see.

    python probe.py            # the gap table
    python probe.py --covered  # also list what is covered

**Why this exists, and why it is not `selftest.py`.** The self-test asks whether every rule can
fire. That is a floor, and it cannot answer the question that actually matters when the tool
meets an unfamiliar estate: *which idioms exist in the world that no rule covers.* A rule set
that passes every control it wrote for itself will still read a Dapper repository, a MassTransit
consumer or a Mongoose model as nothing at all, and report that estate as simple.

**The method.** `fixtures/probe/` holds one file per language enumerating the idioms a large
polyglot enterprise estate commonly runs — the frameworks in common use, and for each, the
constructs that produce an entry point, an outbound call, a durable operation, a message, a
schedule or a configuration read. Each is preceded by a marker:

    // PROBE:<fact_kind>:<framework>:<name>

A marker owns the next non-blank, non-marker line. The rule set is run over the probe files and
each marker is scored: **covered** if a fact of the declared kind landed on its line, **wrong
kind** if a fact landed but disagrees about what the construct is, **not seen** if nothing did.

**This is enumeration, not discovery.** The list is only as good as the frameworks written into
it, and it is a standing invitation to add more. What it removes is the need to wait for a real
estate to tell you what the rules cannot read. A gap found here costs a fixture; the same gap
found on a live subject costs a run.

**A `not seen` result is a finding, not a defect to suppress.** Some idioms should stay
uncovered — the rule that would catch them may not be worth its false positives, and saying so
explicitly is better than a silent absence. The point is that the choice is visible.
"""

import argparse
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "rules.yaml")
PROBES = os.path.join(HERE, "fixtures", "probe")
SEMGREP = os.environ.get("DFO_SEMGREP", "semgrep")

MARKER = re.compile(r"(?://|#)\s*PROBE:([a-z_]+):([A-Za-z0-9._-]+):([A-Za-z0-9._-]+)\s*$")


def markers():
    """Every probe marker, with the span of lines it owns.

    **A marker owns everything up to the next marker, not just the following line.** The first
    version owned one line and scored a third of the Python probes as unseen because the
    construct sat inside a function and the marker owned the `def`. Idioms do not all fit on
    one line — a consumer is a class, a batch job is a builder chain, an ORM call sits in a
    method body — so the span is the unit. Spans are disjoint, and each contains exactly one
    probed construct by construction.
    """
    found = []
    for name in sorted(os.listdir(PROBES)):
        path = os.path.join(PROBES, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        here = []
        for number, text in enumerate(lines, start=1):
            hit = MARKER.search(text)
            if hit:
                here.append({"file": name, "line": number, "kind": hit.group(1),
                             "framework": hit.group(2), "label": hit.group(3)})
        for index, probe in enumerate(here):
            probe["end"] = (here[index + 1]["line"] - 1) if index + 1 < len(here) else len(lines)
        found.extend(here)
    return found


def facts_by_location():
    proc = subprocess.run(
        [SEMGREP, "--config", RULES, "--json", "--quiet", "--metrics=off", PROBES],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if not proc.stdout:
        sys.exit(f"semgrep produced no output:\n{proc.stderr[-1500:]}")
    report = json.loads(proc.stdout)
    located = collections.defaultdict(set)
    for hit in report.get("results", []):
        name = os.path.basename(hit["path"])
        kind = hit["extra"]["metadata"]["fact_kind"]
        # A match spans lines; credit every line it covers, because a construct written across
        # several lines is one idiom and the marker sits above its first.
        start, end = hit["start"]["line"], hit.get("end", {}).get("line", hit["start"]["line"])
        for line in range(start, min(end, start + 12) + 1):
            located[(name, line)].add(kind)
    return located, report.get("errors", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--covered", action="store_true",
                        help="also list the idioms that are covered")
    args = parser.parse_args()

    probes = markers()
    located, errors = facts_by_location()

    covered, wrong, unseen = [], [], []
    for probe in probes:
        kinds = set()
        for line in range(probe["line"], probe["end"] + 1):
            kinds |= located.get((probe["file"], line), set())
        if probe["kind"] in kinds:
            covered.append(probe)
        elif kinds:
            probe["saw"] = ", ".join(sorted(kinds))
            wrong.append(probe)
        else:
            unseen.append(probe)

    total = len(probes)
    print(f"probed idioms: {total}   covered: {len(covered)}   "
          f"wrong kind: {len(wrong)}   NOT SEEN: {len(unseen)}")

    by_language = collections.Counter()
    for probe in unseen:
        by_language[probe["file"]] += 1
    if by_language:
        print("\nnot seen, by probe file:")
        for name, count in by_language.most_common():
            seen_here = sum(1 for p in probes if p["file"] == name)
            print(f"  {name:26} {count:>3} of {seen_here}")

    if unseen:
        print("\nNOT SEEN — an idiom in the catalogue that no rule reads:")
        for probe in sorted(unseen, key=lambda p: (p["kind"], p["framework"])):
            print(f"  {probe['kind']:20} {probe['framework']:24} {probe['label']:32} "
                  f"{probe['file']}:{probe['line']}")

    if wrong:
        print("\nWRONG KIND — a fact landed, and it disagrees with what the construct is:")
        for probe in wrong:
            print(f"  {probe['framework']:24} {probe['label']:32} "
                  f"declared {probe['kind']}, saw {probe['saw']}  "
                  f"{probe['file']}:{probe['line']}")

    if args.covered:
        print("\ncovered:")
        for probe in sorted(covered, key=lambda p: (p["kind"], p["framework"])):
            print(f"  {probe['kind']:20} {probe['framework']:24} {probe['label']}")

    unparsed = {
        loc.get("path")
        for err in errors
        for loc in (err.get("type") or [None, []])[1] or []
        if isinstance(loc, dict)
    }
    if unparsed:
        print(f"\nNOTE  {len(unparsed)} probe file(s) only partially parsed; some 'not seen' "
              f"results below may be parse failures rather than missing rules:")
        for path in sorted(unparsed):
            print(f"  {os.path.basename(path)}")

    # The probe reports; it does not gate. A gap is a decision to take, not a build to break.
    return 0


if __name__ == "__main__":
    sys.exit(main())
