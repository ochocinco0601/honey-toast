"""Precision — draw a sample of facts and lay them out to be judged.

Usage:  python precision.py <source-root> <fact-base.json> [per-rule]
Output: a judgment worksheet, JSON on stdout.

**This file makes no judgment. It draws the sample and gathers the evidence.**
Whether a fact is what it claims to be is decided by a reader who did not author the
rules — the same reason the specification gets an independent read. A sampler that also
scored itself would be the self-grading this work has already been caught by once.

**What it is for.** Every other check here asks whether the extraction found everything:
the negative control, the coverage check, reconciliation against declared populations,
the provisional-rule counter. **None asks whether what was found is real.** A receiver
pattern like `$SET.Add(...)` claiming a durable write matches any collection's Add just
as happily, and nothing in the pipeline would notice.

**Stratified by rule, not drawn at random across the whole base.** A random sample is
dominated by whichever rule fires most and can miss a rule that fired twice — and a rule
that fires rarely is exactly where an over-broad pattern hides.
"""

import json
import os
import sys

CONTEXT = 2


def read_context(path, line):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return None, []
    lo, hi = max(1, line - CONTEXT), min(len(lines), line + CONTEXT)
    return lines[line - 1] if 0 < line <= len(lines) else None, [
        {"line": n, "text": lines[n - 1], "is_cited": n == line} for n in range(lo, hi + 1)
    ]


def record(judged_path, estate, date):
    """Turn a judged worksheet into the evidence lines `run.py` reads.

    Without this the only way to give a rule standing is hand-editing YAML in a format
    documented nowhere but the parser — which an independent review named as the reason the
    whole mechanism had no input and reported `unchecked` about everything, forever.

    The judged worksheet is this file's own output with a `verdict` added to each item by a
    reader who did not author the rules: `correct`, `wrong`, or `unclear`. **Only `correct`
    counts as correct**; `unclear` counts as sampled and not correct, because a fact a reader
    could not confirm has not been confirmed.
    """
    with open(judged_path, "r", encoding="utf-8") as handle:
        worksheet = json.load(handle)

    unjudged = [i["id"] for i in worksheet["items"] if "verdict" not in i]
    if unjudged:
        sys.exit(f"{len(unjudged)} item(s) carry no verdict — {', '.join(unjudged[:5])}"
                 f"{' …' if len(unjudged) > 5 else ''}\n"
                 "Add \"verdict\": \"correct\" | \"wrong\" | \"unclear\" to every item first.")

    tally = {}
    for item in worksheet["items"]:
        counts = tally.setdefault(item["rule"], {"sampled": 0, "correct": 0})
        counts["sampled"] += 1
        counts["correct"] += item["verdict"] == "correct"

    # The fingerprint of the rule the sample was drawn from. `run.py` discards evidence
    # whose fingerprint no longer matches, so a pattern edit voids its evidence without
    # anyone having to remember to clear it.
    rules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules.yaml")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from run import rule_fingerprints
    fingerprints = rule_fingerprints(rules_path)

    print("# Paste each line into that rule's `metadata.checked:` block in rules.yaml.")
    for rule, counts in sorted(tally.items()):
        entry = {"estate": estate, "date": date,
                 "sampled": counts["sampled"], "correct": counts["correct"],
                 "pattern_sha": fingerprints.get(rule)}
        flag = "   # QUARANTINES THIS RULE" if counts["correct"] < counts["sampled"] else ""
        print(f'{rule}:\n      - checked: {json.dumps(entry)}{flag}')


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--record":
        if len(sys.argv) < 4:
            sys.exit("usage: precision.py --record <judged-worksheet.json> <estate> [date]")
        date = sys.argv[4] if len(sys.argv) > 4 else __import__("datetime").date.today().isoformat()
        return record(sys.argv[2], sys.argv[3], date)

    if len(sys.argv) < 3:
        sys.exit(__doc__)
    root, fact_base = sys.argv[1], sys.argv[2]
    per_rule = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    with open(fact_base, "r", encoding="utf-8") as handle:
        facts = json.load(handle)["facts"]

    by_rule = {}
    for fact in facts:
        by_rule.setdefault(fact["rule"].split(".")[-1], []).append(fact)

    items, unreadable = [], 0
    for rule, rule_facts in sorted(by_rule.items()):
        # Evenly spaced through the rule's own findings rather than the first N, which
        # would sample one file repeatedly and miss how the rule behaves elsewhere.
        step = max(1, len(rule_facts) // per_rule)
        for fact in rule_facts[::step][:per_rule]:
            cited, context = read_context(os.path.join(root, fact["file"]), fact["line"])
            if cited is None:
                unreadable += 1
                continue
            items.append({
                "id": f"{rule}#{len(items) + 1}",
                "rule": rule,
                "claims": fact["kind"],
                "at": f"{fact['file']}:{fact['line']}",
                "context": context,
                "question": f"Does the cited line constitute a {fact['kind']}? "
                            f"Answer correct / wrong / unclear, and say why in one line.",
            })

    json.dump({
        "root": root,
        "fact_base": fact_base,
        "population": len(facts),
        "rules_in_population": len(by_rule),
        "sampled": len(items),
        "unreadable_locations": unreadable,
        "instructions": "Judge each item independently. A fact is `correct` only if the cited "
                        "line really is an instance of what it claims. `$SET.Add(...)` claiming "
                        "a durable write on a plain list is `wrong`, not `unclear`. Report "
                        "per-rule counts; a rule with any `wrong` needs its pattern narrowed.",
        "note_on_reading": "A cited location that cannot be read is counted separately and is "
                           "never scored as correct — it is a defect in the fact, not a pass.",
        "items": items,
    }, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
