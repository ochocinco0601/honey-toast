"""Acceptance — score a candidate extractor against a subject whose answer is known.

Usage:  python accept.py <join-output.json> [--key ANSWER-KEY-bank-of-anthos.json]
Output: a score, JSON on stdout. Exit 0 if the candidate is acceptable, 1 if not.

**What this is for.** `contract.py` asks whether a fact base has the right shape. This asks
whether the tool that produced it actually found what is there. It exists so a tool nobody here
has ever run can be fitted to Phase 1 and the fit reported as a number rather than an opinion.

**Why the subject is Bank of Anthos.** It is public, it is small enough to hand-trace, and the
answer was derived twice by hand before any of this tooling existed. A tool scored against a key
its own output produced proves nothing.

**The one thing this measures that nothing else does.** Static analysers are good at per-file
structure and are documented to stop at the seam between services. The hard edge on this subject
is `frontend -> ledgerwriter`: the call site names no target, the address comes from an
environment variable, the variable resolves only inside a Kubernetes manifest, and the receiving
route is in a different language. **Cross-boundary edges are therefore scored on their own and
never folded into a total**, because a single number lets a tool that recovers no seams at all
look competent.

**Cited, partial, asserted — and the middle one matters most.** An edge counts as recovered
only when every hop carries a citation someone can open. An edge that cites some hops, names the
one it could not follow, and says it is incomplete is PARTIAL — the tool disclosing its limit,
which is the behaviour this method asks for. An edge with no citations, or one claiming
completeness while hops carry none, is ASSERTED: a hop somebody decided existed, and
indistinguishable from a guess. Model-asserted cross-service structure has been measured at zero
precision, zero recall and 39.1% edge hallucination (De Luca et al. 2026, arXiv:2606.26927). The
three are reported separately and never
summed, because a tool that says where it stopped is usable and one that fills the gap silently
is not.

**Input shape.** A candidate needs to emit, or be adapted to emit, a JSON object with `edges`,
each `{from_deployable, to_deployable, hops: [{cite: "path:line"}]}`. `from`/`to` are accepted as
aliases. Nothing else about the producing tool is assumed.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KEY = os.path.join(HERE, "ANSWER-KEY-bank-of-anthos.json")


def endpoints(edge):
    """The two ends, under either naming. Nothing is inferred from name similarity."""
    src = edge.get("from_deployable") or edge.get("from")
    dst = edge.get("to_deployable") or edge.get("to")
    return src, dst


def classify(edge):
    """cited | partial | asserted — and the middle one is not a lesser version of the last.

    An edge whose hops all carry a location is CITED: a person can open every step.

    An edge that cites some hops, fails at a named one, and says so is PARTIAL. That is
    disclosed incompleteness — the tool reporting the limit of what it could follow. On
    Bank of Anthos it is what the join emits for the alternative monolith topology, whose
    target is not a declared deployable in the main one. Scoring that as an assertion would
    punish the exact behaviour this method asks for.

    An edge with no cited hops, or one claiming completeness while hops carry no location,
    is ASSERTED. That is a hop somebody decided existed, and it is indistinguishable from a
    guess. The distinction between this and PARTIAL is the whole judgement: a tool that
    says where it stopped is usable; a tool that fills the gap silently is not.
    """
    hops = edge.get("hops")
    if not isinstance(hops, list) or not hops:
        return "asserted"
    cited = [h for h in hops if isinstance(h, dict) and h.get("cite")]
    if len(cited) == len(hops):
        return "cited"
    if not cited:
        return "asserted"
    # Some hops cited. Honest only if the edge does not claim to be complete.
    return "partial" if edge.get("complete") is False else "asserted"


def score(candidate, key):
    expected = {(e["from"], e["to"]): e for e in key["cross_boundary_edges"]}

    cited, partial, asserted = {}, {}, {}
    buckets = {"cited": cited, "partial": partial, "asserted": asserted}
    for edge in candidate.get("edges", []):
        src, dst = endpoints(edge)
        if not src or not dst:
            continue
        buckets[classify(edge)][(src, dst)] = edge

    found_cited = set(cited) & set(expected)
    found_partial = (set(partial) & set(expected)) - found_cited
    found_asserted = (set(asserted) & set(expected)) - found_cited - found_partial
    missing = set(expected) - found_cited - found_partial - found_asserted
    # An edge the candidate claims that the key does not hold. The key is scoped to one business
    # process flow, so a claimed edge outside it is unscored rather than false — reported apart.
    claimed_outside = (set(cited) | set(partial) | set(asserted)) - set(expected)

    by_protocol = {}
    for pair, e in expected.items():
        proto = e.get("protocol", "?")
        row = by_protocol.setdefault(proto, {"expected": 0, "cited": 0})
        row["expected"] += 1
        row["cited"] += pair in found_cited

    hard = next((e for e in key["cross_boundary_edges"] if e.get("is_the_hard_one")), None)
    hard_pair = (hard["from"], hard["to"]) if hard else None

    return {
        "subject": key["subject"],
        "cross_boundary": {
            "expected": len(expected),
            "recovered_with_citations": len(found_cited),
            "recall_cited": round(len(found_cited) / len(expected), 3) if expected else None,
            "recovered_but_partial": sorted("%s -> %s" % p for p in found_partial),
            "recovered_but_asserted": sorted("%s -> %s" % p for p in found_asserted),
            "missing": sorted("%s -> %s" % p for p in missing),
            "by_protocol": by_protocol,
        },
        "the_hard_edge": {
            "edge": "%s -> %s" % hard_pair if hard_pair else None,
            "recovered_with_citations": hard_pair in found_cited if hard_pair else None,
            "why_it_is_the_test": hard.get("why") if hard else None,
        },
        "claimed_outside_the_key": {
            "count": len(claimed_outside),
            "edges": sorted("%s -> %s" % p for p in claimed_outside)[:20],
            "means": "the key covers one business process flow, so these are unscored rather "
                     "than wrong. Open a few: an edge with cited hops is likely a real "
                     "dependency outside the flow; an edge with none is the failure mode this "
                     "harness exists to catch",
        },
        "citation_discipline": {
            "edges_claimed": len(cited) + len(partial) + len(asserted),
            "fully_cited": len(cited),
            "partial_and_disclosed": len(partial),
            "asserted_without_citations": len(asserted),
            "means": "read asserted_without_citations FIRST when judging a tool nobody here "
                     "has run. partial_and_disclosed is not a lesser version of it — an edge "
                     "that names the hop it could not follow is the tool being honest about "
                     "its limit; an edge that fills that hop silently is the failure mode",
        },
    }


def verdict(result):
    """Acceptable means: the hard edge is recovered with citations, and nothing is asserted.

    Deliberately not a threshold on recall. A tool that recovers eight easy edges and misses the
    seam has not done the job this method needs; a tool that recovers the seam and little else
    has done the part nothing else does.
    """
    reasons = []
    # Partial edges are deliberately NOT a reason. Disclosed incompleteness is the contract
    # being honoured, not broken.
    hard = result["the_hard_edge"]
    if hard["edge"] and not hard["recovered_with_citations"]:
        reasons.append(f"the hard edge ({hard['edge']}) was not recovered with citations — this "
                       "is the seam the method exists to cross")
    if result["citation_discipline"]["asserted_without_citations"]:
        reasons.append(f"{result['citation_discipline']['asserted_without_citations']} edge(s) "
                       "claimed with no citation on every hop — unverifiable by a person")
    if result["cross_boundary"]["recall_cited"] is not None \
            and result["cross_boundary"]["recall_cited"] < 0.5:
        reasons.append(f"cited cross-boundary recall {result['cross_boundary']['recall_cited']} "
                       "— under half the known seams")
    return (not reasons), reasons


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", help="a join/edge output from the extractor under test")
    ap.add_argument("--key", default=DEFAULT_KEY)
    args = ap.parse_args()

    with open(args.candidate, "r", encoding="utf-8") as handle:
        candidate = json.load(handle)
    with open(args.key, "r", encoding="utf-8") as handle:
        key = json.load(handle)

    result = score(candidate, key)
    acceptable, reasons = verdict(result)
    result["acceptable"] = acceptable
    result["reasons_not_acceptable"] = reasons
    result["means"] = ("This scores whether a candidate finds the seams between services on a "
                       "subject whose answer was hand-derived twice. It says nothing about "
                       "whether individual facts are true — that is a precision sample judged "
                       "by a reader — and nothing about within-service coverage.")
    print(json.dumps(result, indent=2))
    return 0 if acceptable else 1


if __name__ == "__main__":
    sys.exit(main())
