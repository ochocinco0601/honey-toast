"""Phase 1 conformance — does this fact base satisfy the contract, whoever produced it.

Usage:  python contract.py <source-root> <fact-base.json> [--sample N | --all]
Output: a verdict, JSON on stdout. Exit 0 if it conforms, 1 if it does not.

**Why this exists.** Phase 1 of the method is a contract, and the tool that satisfies it is a
choice. That was true in prose and unenforceable in practice: nothing said what a conforming
fact base looks like, so "swap in a different extractor" meant "read the runner and guess".
This file is the contract in a form a machine can check, so a tool nobody here has ever run can
be fitted and the fit can be scored rather than asserted.

**What it can and cannot establish.** It checks the properties that are checkable from one
output plus the source it was taken from. Determinism needs two runs and is checked by
`--compare`. Whether a fact is *true* — whether this line really is a durable write — is a
precision question that only a reader answers; `precision.py` draws that sample. Conformance is
necessary and not sufficient, which is stated here so nobody reads a PASS as a warrant.

**The two sharpest checks are here because both defects were found in shipped output**, in this project's own extractor:

- **C6 rule-id hygiene.** Semgrep namespaces a rule id with the filesystem path of the rules
  file, so every emitted fact carried the operator's local directory tree. A fact base handed
  to someone else leaked the machine that made it, and two runs of one subject on different
  machines could never be compared. Any tool that derives an identifier from a path will do
  this.
- **C7 one location, one kind.** Two rules matched the same line and it became two facts. The
  same defect had already been found once between two other kinds, in another language, and
  recurred unseen. Any rule set with overlapping patterns will do this.

Neither is exotic. Both are what a second extractor will get wrong, which is why they are
checks rather than advice.
"""

import argparse
import json
import os
import re
import sys

# The closed vocabulary. A kind outside it is not a failure of the tool — it is a fact this
# method has no consumer for, and it is reported so the gap is visible rather than silently
# carried through the passes that follow.
KINDS = {
    "inbound_route", "outbound_http", "grpc_method", "grpc_call",
    "message_consumer", "message_producer", "message_publisher",
    "message_subscription", "event_binding",
    "durable_read", "durable_write", "repo_decl",
    "env_read", "config_ref",
    "background_trigger", "poll_interval",
    "client_binding",
}

REQUIRED_FACT_FIELDS = ("kind", "file", "line", "evidence", "service")
REQUIRED_TOP_FIELDS = ("root", "facts", "counts", "reach")

# A rule or tool identifier that carries a path segment is carrying the machine that produced it.
PATHLIKE = re.compile(r"[/\\]|^[A-Za-z]:|(?:^|\.)(?:c|users|home|opt|var|tmp|mnt)(?:\.|$)", re.I)
ABSOLUTE = re.compile(r"^(?:[A-Za-z]:|[/\\])")


def fail(check, detail, examples=None):
    return {"check": check, "passed": False, "detail": detail, "examples": (examples or [])[:5]}


def ok(check, detail):
    return {"check": check, "passed": True, "detail": detail}


def c1_top_level(base):
    missing = [f for f in REQUIRED_TOP_FIELDS if f not in base]
    if missing:
        return fail("C1 top-level shape", "required top-level fields absent", missing)
    if not isinstance(base["facts"], list):
        return fail("C1 top-level shape", "`facts` is not a list")
    return ok("C1 top-level shape", f"{len(base['facts'])} facts, all required blocks present")


def c2_fact_shape(facts):
    bad = []
    for i, f in enumerate(facts):
        if not isinstance(f, dict):
            bad.append({"index": i, "why": "not an object"})
            continue
        missing = [k for k in REQUIRED_FACT_FIELDS if k not in f]
        if missing:
            bad.append({"index": i, "why": "missing " + ", ".join(missing)})
        elif not isinstance(f["line"], int) or f["line"] < 1:
            bad.append({"index": i, "why": f"line is not a positive integer: {f['line']!r}"})
    if bad:
        return fail("C2 fact shape", f"{len(bad)} fact(s) malformed", bad)
    return ok("C2 fact shape", "every fact carries kind, file, line, evidence and service")


def c3_kind_vocabulary(facts):
    unknown = sorted({f.get("kind") for f in facts} - KINDS - {None})
    if unknown:
        return fail("C3 kind vocabulary",
                    "kinds outside the vocabulary — nothing downstream consumes these",
                    unknown)
    return ok("C3 kind vocabulary", "every kind is one the passes consume")


def c4_citation_integrity(root, facts, sample):
    """Open the cited location and confirm the evidence is what is actually there.

    This is the check the whole method rests on. Every other guarantee is about shape; this one
    is about whether the citations are real. A tool that emits plausible coordinates with
    invented evidence passes everything else and fails here.
    """
    checked, mismatched, unreadable = 0, [], []
    for f in sample:
        path = os.path.join(root, f["file"].replace("/", os.sep))
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                lines = handle.read().splitlines()
        except OSError:
            unreadable.append({"at": f"{f['file']}:{f['line']}", "why": "file cannot be opened"})
            continue
        if not 0 < f["line"] <= len(lines):
            unreadable.append({"at": f"{f['file']}:{f['line']}",
                               "why": f"line beyond end of file ({len(lines)} lines)"})
            continue
        checked += 1
        actual = lines[f["line"] - 1].strip()
        claimed = (f.get("evidence") or "").strip()
        # The evidence may be a normalised or truncated form of the line, so containment either
        # way counts. What must not happen is evidence that appears nowhere near the location.
        if claimed and claimed not in actual and actual not in claimed:
            mismatched.append({"at": f"{f['file']}:{f['line']}",
                               "claimed": claimed[:100], "actual": actual[:100]})
    if unreadable or mismatched:
        return fail("C4 citation integrity",
                    f"{len(mismatched)} evidence mismatch(es), {len(unreadable)} unreadable "
                    f"location(s) out of {len(sample)} sampled",
                    mismatched + unreadable)
    return ok("C4 citation integrity",
              f"{checked} cited location(s) opened; evidence matches the source at every one")


def c5_path_hygiene(facts):
    bad = []
    for f in facts:
        p = f.get("file", "")
        if ABSOLUTE.match(p):
            bad.append({"at": p, "why": "absolute path — not portable, and names the machine"})
        elif "\\" in p:
            bad.append({"at": p, "why": "backslash separator — the same fact reads differently "
                                        "on another platform"})
    if bad:
        return fail("C5 path hygiene", f"{len(bad)} fact path(s) are not repo-relative POSIX",
                    bad)
    return ok("C5 path hygiene", "every fact path is repo-relative with forward slashes")


def c6_identifier_hygiene(base, facts):
    """No identifier may carry the filesystem of the machine that produced the run."""
    bad = []
    for f in facts:
        rule = f.get("rule")
        if isinstance(rule, str) and PATHLIKE.search(rule):
            bad.append({"rule": rule[:120],
                        "why": "identifier contains a path — leaks the producing machine and "
                               "makes two machines' output incomparable"})
            if len(bad) >= 5:
                break
    tool = base.get("tool")
    if isinstance(tool, str) and ABSOLUTE.match(tool):
        bad.append({"rule": tool[:120], "why": "`tool` is a filesystem path, not a tool name"})
    if bad:
        return fail("C6 identifier hygiene", "identifiers carry filesystem paths", bad)
    return ok("C6 identifier hygiene", "no identifier carries a path")


def c7_multi_kind_disclosed(base, facts):
    """A location may carry two kinds. It may not do so silently.

    A line can genuinely do two things, so forbidding duality would lose real facts. But
    every count and coverage figure downstream treats a fact as a countable unit, so an
    undisclosed double inflates all of them. Twice in this project a pair of rules has
    overlapped and nothing noticed — in C# and again in Java, the second time after the
    first had been documented as fixed. The contract is therefore disclosure, not absence:
    an extractor that emits doubles must say so, in a `multi_kind_locations` block.
    """
    seen = {}
    for f in facts:
        seen.setdefault((f.get("file"), f.get("line")), set()).add(f.get("kind"))
    doubled = {k: sorted(v) for k, v in seen.items() if len(v) > 1}
    disclosed = base.get("multi_kind_locations")
    if not doubled:
        return ok("C7 multi-kind disclosure", "no source line carries two kinds")
    if not isinstance(disclosed, dict) or 'count' not in disclosed:
        return fail("C7 multi-kind disclosure",
                    f"{len(doubled)} location(s) carry two kinds and the fact base does not "
                    "declare it — every downstream tally counts them twice with nothing "
                    "saying so. Emit a `multi_kind_locations` block.",
                    [{"at": f"{k[0]}:{k[1]}", "kinds": v} for k, v in doubled.items()])
    if disclosed["count"] != len(doubled):
        return fail("C7 multi-kind disclosure",
                    f"declared {disclosed['count']} multi-kind location(s), found "
                    f"{len(doubled)}")
    return ok("C7 multi-kind disclosure",
              f"{len(doubled)} location(s) carry two kinds, all declared: "
              + ", ".join(f"{k} x{v}" for k, v in disclosed.get("by_kinds", {}).items()))


def c8_reach(base):
    """A run must be able to say it did NOT read the estate.

    Without this a run that read half a system is indistinguishable from a system that is half
    as large, and the output for the unread half is empty rather than sparse.
    """
    reach = base.get("reach")
    if not isinstance(reach, dict):
        return fail("C8 reach", "no reach block — the run cannot say whether it read the estate")
    missing = [k for k in ("deployables_with_no_facts", "file_types_present_that_no_rule_read",
                           "complete") if k not in reach]
    if missing:
        return fail("C8 reach", "reach block incomplete", missing)
    silent = reach["deployables_with_no_facts"]
    unread = reach["file_types_present_that_no_rule_read"]
    claims_complete = bool(reach["complete"])
    # `complete` is about DEPLOYABLES, not file types. Every repository holds configuration,
    # documentation and build files that no code rule reads, and treating those as
    # incompleteness would mark every real run incomplete and make the signal useless. The
    # unread list is information for the person choosing rules; the silent list is the failure.
    if claims_complete and silent:
        return fail("C8 reach",
                    "reach.complete is true while declared deployables produced no facts — the "
                    "block contradicts itself",
                    [{"silent": list(silent)}])
    # A silent deployable is one way to miss something; source in a language no rule reads, and
    # regions the parser could not read, are others, and only `incomplete_because` carries those.
    reasons = reach.get("incomplete_because") or []
    if not claims_complete and not silent and not reasons:
        return fail("C8 reach",
                    "reach.complete is false and neither a silent deployable nor a stated "
                    "reason is named — a run must say WHAT it did not reach, not only that "
                    "it did not")
    return ok("C8 reach",
              f"reach block present and self-consistent (complete={claims_complete}, "
              f"{len(silent)} silent deployable(s), {len(reasons)} stated reason(s); "
              f"{len(unread)} file type(s) no rule reads, "
              f"which is information rather than a defect)")


def c9_attribution(base, facts):
    """A fact matching no deployable is reported, never dropped and never guessed at."""
    actual = sum(1 for f in facts if f.get("service") is None)
    declared = base.get("unattributed")
    if declared is None:
        return ok("C9 attribution",
                  f"{actual} fact(s) match no deployable; no `unattributed` count declared")
    if declared != actual:
        return fail("C9 attribution",
                    f"`unattributed` says {declared}, the facts say {actual}")
    return ok("C9 attribution", f"{actual} unattributed fact(s), and the count agrees")


def c11_tool_identity(base):
    """A fact base must say what produced it, precisely enough to reproduce.

    This check exists because its absence cost a day. A committed fact base stopped
    reproducing from byte-identical rules on the same machine — 266 facts, then 255 — and
    the fact base recorded only the analyser's name. There was nothing to attribute the
    change to and no way to tell a rule edit from an analyser change. Name, version and a
    fingerprint of the rule set are the minimum that makes a run reproducible by someone
    else, which is the whole point of handing one over.
    """
    tool = base.get("tool")
    if isinstance(tool, str):
        return fail("C11 tool identity",
                    f"`tool` is a bare name ({tool!r}) with no version. A run that cannot "
                    "say which build produced it cannot be reproduced, and an analyser "
                    "change is indistinguishable from a rule change.")
    if not isinstance(tool, dict):
        return fail("C11 tool identity", "no `tool` block — nothing says what produced this")
    missing = [k for k in ("name", "version") if not tool.get(k)]
    if missing:
        return fail("C11 tool identity", "tool block incomplete", missing)
    detail = f"{tool['name']} {tool['version']}"
    if tool.get("rules_sha256"):
        detail += f", rule set {tool['rules_sha256']}"
    else:
        detail += (", but no fingerprint of the rule set — a rule edit will not be "
                   "distinguishable from an analyser change")
    return ok("C11 tool identity", detail)


def compare(a_path, b_path):
    """Two runs of one subject: do they agree, and if not, why not.

    Disagreement has two very different causes and calling one by the other's name wastes
    a day. If the rule sets differ, the answer changed because someone changed what it
    asks — that is the expected consequence of a fix, not a fault. Only when the tool,
    its version and the rule fingerprint all match is a disagreement non-determinism.

    Written after exactly that mistake: a fact-count delta between two runs was attributed
    to the analyser when a rule fix had landed between them. The fingerprints would have
    said so immediately, had either fact base carried one.
    """
    def load(p):
        with open(p, "r", encoding="utf-8") as handle:
            base = json.load(handle)
        facts = sorted(
            (f.get("kind"), f.get("file"), f.get("line"), f.get("rule"), f.get("service"))
            for f in base["facts"])
        return base.get("tool"), facts

    tool_a, a = load(a_path)
    tool_b, b = load(b_path)
    if a == b:
        return ok("C10 determinism", f"two runs agree on all {len(a)} facts")

    # Name the cause before naming the symptom.
    def ident(t):
        if isinstance(t, dict):
            return (t.get("name"), t.get("version"), t.get("rules_sha256"))
        return (t, None, None)

    ia, ib = ident(tool_a), ident(tool_b)
    if ia != ib:
        changed = []
        for label, x, y in zip(("tool", "version", "rule set"), ia, ib):
            if x != y:
                changed.append(f"{label}: {x} -> {y}")
        return fail("C10 determinism",
                    "the two runs used different instruments, so this is a CHANGED ANSWER "
                    "rather than an unstable one — " + "; ".join(changed) + ". Compare "
                    "against a run made with the same rule set before reading a fact-count "
                    f"delta as a defect ({len(a)} vs {len(b)} facts).",
                    [{"first": ia, "second": ib}])

    if ia == (None, None, None):
        return fail("C10 determinism",
                    f"two runs disagree ({len(a)} vs {len(b)} facts) and NEITHER records "
                    "its instrument, so the cause cannot be established. A fact base that "
                    "does not carry its tool version and rule fingerprint makes a rule "
                    "change indistinguishable from non-determinism.")

    only_a = [x for x in a if x not in b][:5]
    only_b = [x for x in b if x not in a][:5]
    return fail("C10 determinism",
                f"same tool, same version, same rule set, different answer — "
                f"{len(a)} vs {len(b)} facts. This is non-determinism.",
                [{"only_in_first": only_a}, {"only_in_second": only_b}])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", help="the source root the fact base was taken from")
    ap.add_argument("fact_base")
    ap.add_argument("--sample", type=int, default=60,
                    help="how many citations to open and verify (default 60)")
    ap.add_argument("--all", action="store_true", help="verify every citation")
    ap.add_argument("--compare", metavar="OTHER_FACT_BASE",
                    help="a second run of the same subject, for the determinism check")
    args = ap.parse_args()

    with open(args.fact_base, "r", encoding="utf-8") as handle:
        base = json.load(handle)

    results = [c1_top_level(base)]
    if not results[0]["passed"]:
        print(json.dumps({"conforms": False, "checks": results}, indent=2))
        return 1

    facts = base["facts"]
    # Evenly spaced rather than the first N, which would sample one file repeatedly.
    if args.all or len(facts) <= args.sample:
        sample = facts
    else:
        step = max(1, len(facts) // args.sample)
        sample = facts[::step][:args.sample]

    results += [
        c2_fact_shape(facts),
        c3_kind_vocabulary(facts),
        c4_citation_integrity(args.root, facts, sample if results[0]["passed"] else []),
        c5_path_hygiene(facts),
        c6_identifier_hygiene(base, facts),
        c7_multi_kind_disclosed(base, facts),
        c8_reach(base),
        c9_attribution(base, facts),
        c11_tool_identity(base),
    ]
    if args.compare:
        results.append(compare(args.fact_base, args.compare))

    conforms = all(r["passed"] for r in results)
    print(json.dumps({
        "conforms": conforms,
        "fact_base": args.fact_base,
        "facts": len(facts),
        "citations_verified": len(sample),
        "checks": results,
        "means": "Conformance is necessary and not sufficient. It says the fact base has the "
                 "shape and the citation integrity the passes require. It does not say the "
                 "facts are true — that is a precision sample, judged by a reader.",
    }, indent=2))
    return 0 if conforms else 1


if __name__ == "__main__":
    sys.exit(main())
