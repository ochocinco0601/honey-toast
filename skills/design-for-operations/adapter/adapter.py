"""Adapter — turn a design-for-operations run into two structured blocks for onboarding a service.

Usage:  python adapter.py <fact-base.json> <join.json> <stages.json> [--observation observation.json]
Output: JSON on stdout — {"dependencies_structured": {...}, "process_structured": [...],
                          "seeds": {...} (when --observation is given), "adapter_report": {...}}

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
                    failure_impact (may be null) · provenance ("inferred", because criticality is) ·
                    source (the file and line of the fact the join derived the edge from)
    process_structured
        [ { name, steps[] } ]   one process; each step: order · name · components[] (must name
                    nodes above) · blocking · condition · signals[] · description · owned ·
                    provenance
    seeds           (with --observation) Phase 6's cells mapped onto service-definition fields:
                    per signal the disposition (producible + source, watched + source), healthy,
                    owner; per flow the too-broken cell and Phase 2's business account as a
                    stakeholder chain. Every seed carries the run's label, the schema label it
                    becomes, and the cell it came from. See "Seeds" below.
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

**Seeds, and the label table.** A run's Phase 7 writes `observation.json`: the cells Phase 6
drafted, each with the run's own label — `extracted`, `proposed`, `gapped`. A service definition
records provenance in its own vocabulary, and the table below is **one mapping onto one such
format**, the one this adapter emits. Read it as a worked example and rewrite the right-hand side
for whatever you onboard into.

The target vocabulary, defined here so the output is readable without the format in front of you:

  * `constructed` — a value nobody extracted, written deliberately, with the draft it came from
    cited. `validated` — a value a person has since said yes to.
  * **Motivation-chain fields** — the fields carrying why the service matters and to whom: the
    stakeholders, what each expects of it, and what the impact is when that is not met.
  * **A coverage receipt** — a per-layer record of what the definition covers and where it is
    short, kept in five layers: `business_health`, `business_impact`, `process`, `system`,
    `operational`. A gap is filed on the layer its cell belongs to; one with no matching receipt
    element goes to `gaps[]`.
  * **The review queue** — where a drafted position waits for the role whose yes it needs.

    extracted  ->  extracted                        any field
    proposed   ->  constructed, the draft cited     motivation-chain fields; a structured block
                                                    that needs a proposed value gets inferred
    gapped     ->  a coverage-receipt gap           same reason, on the layer the cell belongs to
    ratified   ->  validated on structured blocks   the review queue records the yes

Mapped cells: healthy -> an expectation with its target; owner -> the owner fields; too-broken
-> `service.impact_tolerance`; the disposition -> `producible`/`producible_source` and
`watched`/`watched_source`; Phase 2's business account -> the stakeholder chain. **A seed is
never source material**, and never carries `extracted` unless the run extracted it. A step
whose reading the run labelled `proposed` (its ruling) is emitted with provenance `inferred`,
not `extracted`, because its description carries that reading.

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
    service map, the join by the deployment declaration — and nothing reconciled them.
    `join.py` now emits the correspondence, resolved by shared directory.
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
        edge = {
            "from": src,
            "to": dst,
            "protocol": raw.get("protocol") or "HTTP",
            "criticality": criticality,
            "failure_impact": None,
            # Nodes are extracted; this classification is not, and says so.
            "provenance": "inferred",
            "_criticality_reason": reason,
        }
        # The fact the join derived the edge from: its first hop, the call site or the
        # publish site, as file and line. Carried so a downstream signal can cite it.
        cites = [h.get("cite") for h in (raw.get("hops") or []) if isinstance(h, dict) and h.get("cite")]
        if cites:
            edge["source"] = cites[0]
        edges.append(edge)
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
            # A step is `inferred` when the run proposed any part of it: its reading (a ruling
            # the description carries) or the stage itself (an absence: a stage the business
            # names and nothing in the code performs, `components: []`). The label table has no
            # `proposed` on a structured block, so a proposed value goes to `inferred` with the
            # seed cited. Emitting `proposed` verbatim produces a value the target format has no
            # meaning for, and a validator that checks its labels will reject the record.
            "provenance": ("inferred" if "proposed" in (stage.get("reading_provenance"), stage["provenance"])
                           else stage["provenance"]),
        })
    return [{"name": stages_doc["business_process_flow"], "steps": steps}], orphans


# --------------------------------------------------------------------------- seeds
LABEL_TABLE = {
    "extracted": {"becomes": "extracted", "where": "any field"},
    "proposed": {"becomes": "constructed", "where": "motivation-chain fields, the draft cited as the seed; a structured block needing a proposed value gets inferred"},
    "gapped": {"becomes": "a coverage-receipt gap with the same reason", "where": "the receipt, on the cell's layer; a gap with no receipt element goes to gaps[]"},
    "ratified": {"becomes": "validated on structured blocks; on chain fields the label stays and the review queue records the yes", "where": "the review queue"},
}
STANDING = ("Seeds are drafted positions from a design for operations run, mapped onto service-definition "
            "fields under the label table. They are never source material: no field seeded here carries "
            "'extracted' unless the run extracted it, and every seed cites the cell it came from.")


def _slug(text):
    return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")[:40]


def build_seeds(obs, process):
    """Map observation.json's cells onto service-definition fields, label by label."""
    records, receipt = [], {"business_health": [], "business_impact": [], "process": [], "system": [],
                            "operational": []}
    document_gaps = []
    steps = {s["order"]: s for s in process[0]["steps"]}
    src_note = obs.get("note", "")

    def rec(**kw):
        base = {"cell": None, "stage": None, "signal_name": None, "schema_field": None, "value": None,
                "label": None, "from": None, "receipt_gap": None, "document_gap": None}
        base.update(kw)
        records.append(base)
        return base

    # -- the business account -> the stakeholder chain (proposed -> constructed)
    account = obs["business_account"]
    stakeholders, expectation_of_stage = [], {}
    for party in account["who_depends"]:
        pslug = _slug(party["party"])
        exps = []
        for order in party["stages"]:
            stage = next(s for s in obs["stages"] if s["order"] == order)
            eid = f"{pslug}_{order:02d}_{_slug(stage['name'])}"[:60]
            exps.append({"expectation_id": eid, "stage": order,
                         "text": f"{stage['name']}: {account['why_a_business_names_each_stage'][str(order)]}",
                         "label": "constructed"})
            expectation_of_stage.setdefault(order, []).append((party["party"], eid))
        stakeholders.append({"schema_field": "stakeholders[]", "name": party["party"],
                             "expects": party["expects"], "expectations": exps, "label": "constructed",
                             "from": {"dfo_label": party["label"], "source": account["source"]}})
    rec(cell="business_account", schema_field="stakeholders[].expectations[]", value=f"{len(stakeholders)} parties",
        label="constructed", **{"from": {"dfo_label": account["label"], "source": account["source"]}})

    # -- per stage: disposition, healthy, owner
    for st in obs["stages"]:
        order, sg, src = st["order"], st["signal"], st["source"]
        step = steps.get(order)
        if sg["producible"] == "yes":
            name = sg["name"]
            rec(cell="disposition", stage=order, signal_name=name, schema_field="signals[].producible",
                value="yes", label="extracted", **{"from": {"dfo_label": sg["label"], "source": src, "cite": sg["producible_source"]}})
            rec(cell="disposition", stage=order, signal_name=name, schema_field="signals[].producible_source",
                value=sg["producible_source"], label="extracted", **{"from": {"dfo_label": sg["label"], "source": src}})
            rec(cell="disposition", stage=order, signal_name=name, schema_field="signals[].watched",
                value=sg["watched"], label=None,
                **{"from": {"dfo_label": sg["watched_label"], "source": src, "reason": sg["watched_reason"]}},
                document_gap=None)
            rec(cell="disposition", stage=order, signal_name=name, schema_field="signals[].watched_source",
                value=sg["watched_source"], label=None, **{"from": {"dfo_label": sg["watched_label"], "source": src}})
            if step is not None:
                step["signals"] = [name]
            # healthy -> the expectation's target
            h = st["healthy"]
            if h["label"] == "gapped":
                gap = f"stage {order} ({st['name']}): healthy is gapped, {h['reason']}; the signal exists and its target is not drafted"
                rec(cell="healthy", stage=order, signal_name=name, schema_field="signals[].slo_target",
                    value=None, label=None, **{"from": {"dfo_label": "gapped", "source": src, "reason": h["reason"]}},
                    document_gap=gap)
                document_gaps.append(gap)
            else:
                rec(cell="healthy", stage=order, signal_name=name, schema_field="signals[].slo_target",
                    value=h["value"], label="constructed", **{"from": {"dfo_label": h["label"], "source": src}})
            # owner -> the signal's owner field
            o = st["owner"]
            if o["label"] == "gapped":
                rec(cell="owner", stage=order, signal_name=name, schema_field="signals[].technical_owner",
                    value="", label=None, **{"from": {"dfo_label": "gapped", "value": o["value"], "source": src}},
                    receipt_gap={"layer": "operational", "element": name, "reason": o["reason"]})
                receipt["operational"].append({"element": name, "reason": o["reason"], "provenance": "extracted"})
            else:
                rec(cell="owner", stage=order, signal_name=name, schema_field="signals[].technical_owner",
                    value=o["value"], label="constructed", **{"from": {"dfo_label": o["label"], "source": src}})
        else:
            reason = f"cannot be produced ({sg.get('ruling')}): {sg['reason']}"
            r = rec(cell="disposition", stage=order, signal_name=None, schema_field="signals[]", value=None,
                    label=None, **{"from": {"dfo_label": sg["label"], "source": src, "cite": sg["producible_source"], "ruling": sg.get("ruling")}},
                    document_gap=f"stage {order} ({st['name']}): {reason}")
            document_gaps.append(r["document_gap"])
            if st["owned"]:
                el = f"{order}: {st['name']}"
                r["receipt_gap"] = {"layer": "process", "element": el, "reason": reason}
                receipt["process"].append({"element": el, "reason": reason, "provenance": "extracted"})
            for party, eid in expectation_of_stage.get(order, []):
                receipt["business_health"].append({"element": eid, "reason": reason, "provenance": "extracted"})

    # -- too broken -> impact_tolerance
    tb = obs["too_broken"]
    if tb["label"] == "gapped":
        rec(cell="too_broken", schema_field="service.impact_tolerance", value=None, label=None,
            **{"from": {"dfo_label": "gapped", "source": tb["source"], "would_close": tb["would_close"]}},
            receipt_gap={"layer": "business_impact", "element": "impact_tolerance", "reason": tb["reason"]})
        receipt["business_impact"].append({"element": "impact_tolerance", "reason": tb["reason"], "provenance": "extracted"})
    else:
        rec(cell="too_broken", schema_field="service.impact_tolerance", value=tb["value"], label="constructed",
            **{"from": {"dfo_label": tb["label"], "source": tb["source"]}})

    # -- owners at service level
    unowned = obs.get("unowned_note", "")
    rec(cell="owner", schema_field="service.product_owner; service.technical_owner", value="", label=None,
        **{"from": {"dfo_label": "gapped", "value": "unowned", "source": "the run's Phase 0 source inventory: no owner reachable from the sources the run could reach"}},
        document_gap="service owners: unowned; " + unowned)
    document_gaps.append("service owners: unowned; " + unowned)

    return {
        "standing": STANDING,
        "observation_note": src_note,
        "label_table": LABEL_TABLE,
        "stakeholders": stakeholders,
        "records": records,
        "receipt_gaps": receipt,
        "document_gaps": document_gaps,
        "rulings": obs.get("rulings", {}),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fact_base")
    parser.add_argument("join")
    parser.add_argument("stages")
    parser.add_argument("--observation", help="the run's observation.json (Phase 7); adds the seeds block")
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

    seeds = None
    if args.observation:
        seeds = build_seeds(load(args.observation), process)

    out = {
        "dependencies_structured": {
            "subject": subject,
            "nodes": nodes,
            "edges": edges,
        },
        "process_structured": process,
    }
    if seeds is not None:
        out["seeds"] = seeds
    out["adapter_report"] = {
            "seeds": (None if seeds is None else {
                "records": len(seeds["records"]),
                "stakeholders": len(seeds["stakeholders"]),
                "receipt_gaps": {k: len(v) for k, v in seeds["receipt_gaps"].items()},
                "document_gaps": len(seeds["document_gaps"]),
                "steps_with_a_proposed_reading_emitted_as_inferred": [
                    s["order"] for s in process[0]["steps"] if s["provenance"] == "inferred"],
            }),
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
                "signals are empty here unless --observation supplied them; a seeded signal "
                "name is the run's, and its target, owner and watched state are gapped as the "
                "seeds say",
            ],
    }
    json.dump(out, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
