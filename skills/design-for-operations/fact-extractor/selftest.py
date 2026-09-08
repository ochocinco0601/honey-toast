"""Positive and negative controls for the rule set. Run before trusting any extraction.

    python selftest.py            # exits non-zero if any control fails

**Why this exists.** Semgrep does not error on a pattern its grammar cannot use for a
language — it returns no matches. A rule written in an unsupported form and an estate that
genuinely contains none of that construct produce byte-identical output: nothing. Measured
on a NestJS estate, the AST pattern `@Get(...)` matched 0 of 21 decorators
actually present in the source, and every other check in the pipeline passed. The run
reported an estate with no HTTP entry points, which was false, and nothing in the run could
have said so.

That is the failure this file makes impossible to ship. Two controls, both mechanical:

**Positive.** `fixtures/positive/` holds one small, realistic file per language containing at
least one instance of every construct every rule claims to match. A rule that matches nothing
there cannot match anything anywhere, and is reported as SILENT. This is a floor, not a
recall measurement — passing means the rule is capable of firing, never that it finds
everything a real estate contains. Only running it on real estates shows that.

**Negative.** `fixtures/negative/` holds constructs that must NOT be matched, each one a
precision defect this rule set actually committed and had corrected: Cypress selectors filed
as inbound routes, a `WebClient.builder()` bean factory filed as an outbound call, ordinary
Map and array access filed as database reads. Any match there is a regression, named at its
line. A defect that has been paid for once is cheaper to keep out than to find again.

**A new rule owes both.** Add the construct to the positive fixture in the same edit that adds
the rule, or the rule ships unable to prove it works.
"""

import collections
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "rules.yaml")
FIXTURES = os.path.join(HERE, "fixtures")
SEMGREP = os.environ.get("DFO_SEMGREP", "semgrep")


def scan(path):
    proc = subprocess.run(
        [SEMGREP, "--config", RULES, "--json", "--quiet", "--metrics=off", path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if not proc.stdout:
        sys.exit(f"semgrep produced no output for {path}:\n{proc.stderr[-1500:]}")
    return json.loads(proc.stdout)


def rule_ids():
    """Read the ids by line rather than by YAML, so the check does not need a YAML parser."""
    ids = []
    with open(RULES, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("- id:"):
                ids.append(stripped.split("- id:", 1)[1].strip())
    return ids


def source_line(path, number):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return ""
    return lines[number - 1].strip()[:90] if 0 < number <= len(lines) else ""


def evidence_mismatches():
    """Every `checked:` entry must name an estate written in the rule's own language.

    **A third control, added after this file's author committed the defect it catches.** An
    edit located a rule's `checked:` block by searching forward from its id, which finds the
    next such block in the FILE rather than the one inside that rule, and three rules that had
    never been sampled were handed another rule's samples. Fabricated evidence is the worst
    failure this mechanism can have — the whole point of `checked:` is that a reader vouched
    for those matches — and it was caught by reading, which is exactly the thing that does not
    scale. The estate-to-language map travels beside the fixtures, as estate-languages.json.
    """
    # Beside the fixtures so the check travels with the thing it checks; a control that
    # silently becomes a no-op where the estate list is absent is worse than no control.
    map_path = os.path.join(FIXTURES, "estate-languages.json")
    try:
        with open(map_path, "r", encoding="utf-8") as handle:
            languages = json.load(handle)["languages"]
    except (OSError, KeyError, ValueError):
        print("  NOTE  estate-languages.json is missing; the evidence check did not run")
        return []

    try:
        import yaml
    except ImportError:
        return []
    with open(RULES, "r", encoding="utf-8") as handle:
        rules = yaml.safe_load(handle)["rules"]

    found = []
    for rule in rules:
        declared = set(rule.get("languages") or [])
        for entry in (rule.get("metadata", {}).get("checked") or []):
            estate = entry.get("estate")
            known = set(languages.get(estate, []))
            # An unknown estate is not a mismatch — it is an estate nobody has mapped yet.
            if known and not (known & declared):
                found.append((rule["id"], ", ".join(sorted(declared)), estate))
    return found


def main():
    ids = rule_ids()

    # **Both fixture sets count as positive material, and that is deliberate.** `positive/`
    # holds hand-written constructs per language; `probe/` holds the enumerated framework
    # idioms `probe.py` scores. Both are real constructs, so either can prove a rule capable
    # of firing. Keeping them separate for this purpose would mean writing every construct
    # twice, and the copy nobody edits is the one that rots. What separates the two
    # instruments is the question they answer, not the material they read: this file asks
    # whether a rule can fire at all, `probe.py` asks which idioms in the world nothing reads.
    positive = scan(os.path.join(FIXTURES, "positive"))
    probe = scan(os.path.join(FIXTURES, "probe"))
    hits = collections.Counter(
        r["check_id"].split(".")[-1]
        for report in (positive, probe) for r in report["results"])
    silent = [rule for rule in ids if not hits.get(rule)]

    negative = scan(os.path.join(FIXTURES, "negative"))
    fired = [
        (r["check_id"].split(".")[-1], os.path.basename(r["path"]), r["start"]["line"],
         source_line(r["path"], r["start"]["line"]))
        for r in negative["results"]
    ]

    print(f"positive controls: {len(ids) - len(silent)}/{len(ids)} rules fired")
    for rule in silent:
        print(f"  SILENT   {rule} — matched nothing it claims to match. The pattern form is "
              f"probably unsupported for this language; it will read every estate as empty")
    print(f"negative controls: {len(fired)} unwanted match(es)")
    for rule, name, number, text in fired:
        print(f"  REGRESSION  {rule}  {name}:{number}  {text}")

    # Partial parses in the fixtures mean the controls themselves were not fully read, so a
    # pass would be reporting on source the analyser never saw.
    unparsed = {
        loc.get("path")
        for report in (positive, probe, negative)
        for err in report.get("errors", [])
        for loc in (err.get("type") or [None, []])[1] or []
        if isinstance(loc, dict)
    }
    if unparsed:
        print(f"fixture parse: {len(unparsed)} fixture file(s) only partially parsed — the "
              f"controls did not fully run")
        for path in sorted(unparsed):
            print(f"  UNPARSED  {os.path.basename(path)}")

    mismatched = evidence_mismatches()
    print(f"evidence integrity: {len(mismatched)} misplaced entr(ies)")
    for rule, languages, estate in mismatched:
        print(f"  MISPLACED  {rule} ({languages}) claims a sample from {estate}, which is not "
              f"written in that language — the evidence belongs to another rule")

    if silent or fired or unparsed or mismatched:
        sys.exit(1)
    print("all controls passed")


if __name__ == "__main__":
    main()
