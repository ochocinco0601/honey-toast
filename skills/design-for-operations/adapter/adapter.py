"""Adapter — turn a design-for-operations run into two structured blocks for onboarding a service.

Usage:  python adapter.py <fact-base.json> <join.json> <stages.json>
Output: JSON on stdout — {"dependencies_structured": {...}, "process_structured": [...], "adapter_report": {...}}

**What this is for.** Onboarding a service into a monitoring practice asks two structuring
questions — what depends on what, and what the business process is, in order — and both of them
normally expect a person to have read prose source material: an architecture document, a
runtime view, someone's description of the process. On an undocumented estate there is no such
material, or there is and nobody should trust it. This supplies both blocks from what a run
actually extracted, so onboarding can proceed on evidence instead.

**The done-test this exists to satisfy** — a service can be onboarded from a run with no prose
documents at all.

**Output format.** Two blocks and a report.

    dependencies_structured
        subject     the deployable the graph is anchored at (from stages.json)
        nodes[]     name · kind ("application") · failure_impact (string, never null — see
                    below) · signals[] (empty; filled by a later phase) · provenance ("extracted")
        edges[]     from · to · protocol · criticality (critical | degraded | informational) ·
                    failure_impact (may be null) · provenance ("inferred", because criticality is)
    process_structured
        [ { name, steps[] } ]   one process; each step: order · name · components[] (must name
                    nodes above) · blocking · condition · signals[] · description · owned ·
                    provenance
    adapter_report  counts, the silent and unreferenced nodes, and how criticality was inferred

Whatever onboarding format you feed, map these fields into it; nothing here assumes a schema
beyond what is stated above.

**What is extracted and what is inferred, kept apart.**

Nodes and edges are `extracted`: every one comes from a declared deployable or from a join
edge whose every hop is cited. Nothing is added because a model thought it should be there.

**Criticality is `inferred`, and it is the only judgement this file makes.** The field takes
critical / degraded / informational — what happens to the caller when the callee fails — and
no line of source says that. Refusing to answer would leave the field blank, which the
practitioner's-draft ruling forbids; guessing silently would be worse. So one stated rule is
applied and labelled:

    synchronous request/response  -> critical       the caller waits and has no stated fallback
    asynchronous message/event    -> degraded       the caller has already returned

A fallback the code does declare — a circuit breaker, a cached default, a try/except that
carries on — would move an edge off `critical`. **Nothing here detects one**, so `critical`
is the conservative reading and a reviewer's first job is to demote the ones that deserve it.

**What this file will not do.** It will not invent a node to make an edge resolve, it will
not carry a step whose components are not in the graph, and it will not emit a stage the run
did not rule on. Each of those fails the run loudly instead.
"""

import argparse
import json
import sys

# Which fact kinds make a call synchronous versus asynchronous. Used only to label
# criticality, never to create an edge — edges come from the join.
SYNCHRONOUS = {"outbound_http", "grpc_method", "client_binding", "inbound_route"}
ASYNCHRONOUS = {"message_consumer", "message_publisher", "background_trigger"}


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def name_map(join):
    """Declaration name -> service-map name, from the join's own correspondence block.

    The two halves of a run name deployables differently — the fact base by the operator's
    service map, the join by the deployment declaration — and until 2026-09-02 nothing
    reconciled them. `join.py` now emits the correspondence, resolved by shared directory.
    This reads it; it does not re-derive it, and it never matches on name similarity.
    """
    correspondence = join.get("deployable_name_map")
    if correspondence is None:
        sys.exit("This join predates `deployable_name_map`. Re-run join.py: without the "
                 "correspondence the two halves of the run cannot be joined, and guessing "
                 "from name similarity is how `payment-processor` gets matched to the wrong "
                 "thing.")
    return {logical: entry.get("service_map_name") for logical, entry in correspondence.items()}


def deployables(fact_base, join):
    """Every deployable, named the way the fact base names them.

    The service map is the run's own declaration of what a deployable is called, so it wins;
    a declared deployable outside the map is reported rather than renamed into the graph.
    """
    mapped = {f["service"] for f in fact_base.get("facts", []) if f.get("service")}
    resolved = {v for v in name_map(join).values() if v}
    outside = sorted(k for k, v in name_map(join).items() if not v)
    return mapped, resolved, outside


def build_nodes(fact_base, names):
    """One node per deployable, with what the facts say about it and nothing more."""
    kinds = {}
    for fact in fact_base.get("facts", []):
        service = fact.get("service")
        if service:
            kinds.setdefault(service, set()).add(fact["kind"])

    nodes = []
    for name in sorted(names):
        seen = kinds.get(name, set())
        # `kind` is what a component IS, from C4's container types. A deployable in a
        # service map runs code, so it is an application. A database is a real node of
        # this graph too, but nothing names one: a durable_write cites the line that
        # performs it, never the store it reaches. That gap is reported, not guessed at.
        nodes.append({
            "name": name,
            "kind": "application",
            "failure_impact": None,
            "signals": [],
            "provenance": "extracted",
            # not schema fields — carried for the reviewer, stripped before emit
            "_fact_kinds": sorted(seen),
            "_silent": not seen,
        })
    return nodes


def edge_criticality(edge):
    """critical / degraded, by the one stated rule. Never blank, always labelled."""
    kinds = set()
    for hop in edge.get("hops", []) or []:
        if isinstance(hop, dict) and hop.get("kind"):
            kinds.add(hop["kind"])
    for key in ("via", "kind", "fact_kind"):
        if edge.get(key):
            kinds.add(edge[key])

    if kinds & ASYNCHRONOUS:
        return "degraded", "an asynchronous hop — the caller has already returned"
    if kinds & SYNCHRONOUS:
        return "critical", "a synchronous hop with no fallback detected in source"
    # The join resolved it but named no hop kind. Conservative, and said out loud.
    return "critical", "hop kind not recorded by the join — read conservatively"


def build_edges(join, node_names, translate):
    """Join edges, with both ends translated into service-map names.

    An edge whose source the join could not attribute is NOT emitted and IS reported. On eShop
    several of the join's edges are in that state — call sites in projects the run's service map
    never listed — and a topology that quietly dropped them would read as complete.
    """
    edges, unanchored, unmapped, seen = [], [], [], set()
    for raw in join.get("edges", []):
        src = translate.get(raw.get("from_deployable"), raw.get("from_deployable"))
        dst = translate.get(raw.get("to_deployable"), raw.get("to_deployable"))
        if not raw.get("from_deployable"):
            unanchored.append({
                "to": dst,
                "at": (raw.get("hops") or [{}])[0].get("cite"),
                "why": "the join could not attribute the call site to a declared deployable",
            })
            continue
        if src not in node_names or dst not in node_names:
            unmapped.append({"from": src, "to": dst,
                             "why": "an end is not in the run's service map"})
            continue
        if (src, dst) in seen:
            continue
        seen.add((src, dst))
        criticality, reason = edge_criticality(raw)
        edges.append({
            "from": src,
            "to": dst,
            "protocol": raw.get("protocol") or "HTTP",
            "criticality": criticality,
            "failure_impact": None,
            # Nodes are extracted; this classification is not, and says so.
            "provenance": "inferred",
            "_criticality_reason": reason,
        })
    return edges, unanchored, unmapped


def build_process(stages_doc, node_names):
    """Stages become steps. A step naming a component outside the graph is fatal.

    An owned step's components must name nodes in the dependency graph, or the two blocks
    contradict each other. Emitting a step that fails that would hand a broken record
    downstream and make the check somebody else's problem.
    """
    steps, orphans = [], []
    for stage in stages_doc["stages"]:
        unknown = [c for c in stage["components"] if c not in node_names]
        if unknown:
            orphans.append({"stage": stage["name"], "unknown_components": unknown})
            continue
        steps.append({
            "order": stage["order"],
            "name": stage["name"],
            "components": stage["components"],
            "blocking": stage["blocking"],
            "condition": stage.get("condition"),
            "signals": [],
            "description": stage["description"],
            "owned": stage["owned"],
            "provenance": stage["provenance"],
        })
    return [{"name": stages_doc["business_process_flow"], "steps": steps}], orphans


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fact_base")
    parser.add_argument("join")
    parser.add_argument("stages")
    args = parser.parse_args()

    fact_base, join, stages_doc = load(args.fact_base), load(args.join), load(args.stages)

    mapped, resolved, outside_map = deployables(fact_base, join)
    names = mapped | resolved
    translate = name_map(join)

    nodes = build_nodes(fact_base, names)
    node_names = {n["name"] for n in nodes}
    edges, unanchored, unmapped = build_edges(join, node_names, translate)
    process, orphans = build_process(stages_doc, node_names)

    if orphans:
        print("A stage names a component that is not in the dependency graph. The run is "
              "not adaptable until that is resolved — either the service map is missing a "
              "deployable, or the stage binds to something that is not one:", file=sys.stderr)
        for orphan in orphans:
            print(f"  {orphan['stage']}: {', '.join(orphan['unknown_components'])}",
                  file=sys.stderr)
        sys.exit(1)

    subject = stages_doc.get("subject")
    if subject and subject not in node_names:
        print(f"The declared subject '{subject}' is not a node in the graph.", file=sys.stderr)
        sys.exit(1)

    silent = sorted(n["name"] for n in nodes if n["_silent"])
    unreferenced = sorted(node_names - {c for s in process[0]["steps"] for c in s["components"]})

    # `failure_impact` on a node is a string, never null — unlike the same field on an edge.
    # **Nothing in source states what happens when a deployable
    # fails.** Leaving it blank is not available and inventing a consequence is the
    # fabrication this method exists to prevent, so each node carries a statement of what the
    # run actually recovered plus an explicit declaration that the consequence is undrafted.
    # This is the fourth field found to need a person, alongside healthy, tolerance and owner.
    callers = {}
    for edge in edges:
        callers.setdefault(edge["to"], []).append(edge["from"])
    for node in nodes:
        who = sorted(set(callers.get(node["name"], [])))
        node["failure_impact"] = (
            ("Recovered callers: " + ", ".join(who) + ". " if who
             else "No caller was recovered for this deployable. ")
            + "The consequence of its failure is NOT drafted — no source this run read states "
              "one, and the run does not invent it. A reviewer owes this field."
        )
        node.pop("_fact_kinds", None)
        node.pop("_silent", None)
    reasons = {}
    for edge in edges:
        reason = edge.pop("_criticality_reason")
        reasons[reason] = reasons.get(reason, 0) + 1

    json.dump({
        "dependencies_structured": {
            "subject": subject,
            "nodes": nodes,
            "edges": edges,
        },
        "process_structured": process,
        "adapter_report": {
            "deployables_from_service_map": sorted(mapped),
            "deployables_declared_and_resolved": sorted(resolved),
            "declared_but_outside_the_service_map": outside_map,
            "in_map_but_not_declared": sorted(mapped - resolved),
            "nodes": len(nodes),
            "edges": len(edges),
            "edges_whose_source_could_not_be_attributed": unanchored,
            "edges_with_an_end_outside_the_service_map": unmapped,
            "nodes_with_no_facts": silent,
            "nodes_no_stage_binds_to": unreferenced,
            "stages": len(process[0]["steps"]),
            "criticality_by_reason": reasons,
            "criticality": "inferred by one stated rule — see this file's docstring. "
                           "Every edge carries provenance 'inferred' for that reason; the "
                           "nodes and the edge endpoints are 'extracted'.",
            "what_a_reviewer_owes": [
                "failure_impact is null on every edge, and on every node it states only what "
                "was recovered plus that the consequence is undrafted — no source line states "
                "a consequence, and inventing one would be the fabrication this method exists "
                "to prevent",
                "criticality is a conservative default and wants demoting where a fallback "
                "actually exists",
                "signals are empty here; they are populated after the later phases",
            ],
        },
    }, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
