"""Coverage — measure an extraction against what the repository declares about itself.

Usage:  python coverage.py <source-root> <fact-base.json>
Output: JSON on stdout.

The extractor cannot report its own completeness: it knows what it found and nothing
about what it missed. This reads populations the repository already declares — protocol
definition files today — and reconciles them against the fact base by name.

**Every category with no declarative source is reported `unmeasured`, never assumed
complete.** That distinction is the point of the file. A category nobody can count is a
category nobody should claim.

Matching is by NAME at a cited location, not by count. Two totals agreeing proves
nothing: the `[$A]` incident produced six matches for six attributes that were six
unrelated expressions. Each declared item is looked for individually.
"""

import json
import os
import re
import sys

RPC = re.compile(r"^\s*rpc\s+(\w+)\s*\(")
SERVICE = re.compile(r"^\s*service\s+(\w+)\s*\{")
HTTP_METHODS = {"get", "post", "put", "delete", "patch"}
SEGMENT = re.compile(r"[A-Za-z0-9_-]+")
SKIP_DIRS = {".git", "node_modules", "target", "build", "obj", "bin", "__pycache__", ".venv"}


def declared_grpc(root):
    """Every rpc a .proto declares: the population gRPC entry points are drawn from."""
    declared = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".proto"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            service = None
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                for number, line in enumerate(handle, 1):
                    found_service = SERVICE.match(line)
                    if found_service:
                        service = found_service.group(1)
                    found_rpc = RPC.match(line)
                    if found_rpc:
                        declared.append({
                            "name": found_rpc.group(1),
                            "service": service,
                            "declared_in": f"{rel}:{number}",
                        })
    return declared


def declared_http(root):
    """Every operation an OpenAPI document declares: method plus path.

    **Read the standing caveat before trusting the number.** Where the document is
    *generated from* the same controllers the rules read, it is a second view of one
    source and agreement is not corroboration. Where it is hand-authored or generated at
    build time from a previous version, it can be stale in either direction. The recall
    figure is still worth having — it names specific unmatched operations — but it is a
    weaker instrument than a protocol definition, which is the source implementations are
    generated FROM rather than a description generated from them.
    """
    declared = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith((".json", ".yaml", ".yml")):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
                if '"openapi"' not in text and "openapi:" not in text:
                    continue
                document = json.loads(text) if name.endswith(".json") else None
            except (OSError, ValueError):
                continue
            if not isinstance(document, dict) or "paths" not in document:
                continue
            rel = os.path.relpath(path, root).replace("\\", "/")
            for route, operations in document["paths"].items():
                if not isinstance(operations, dict):
                    continue
                for method in operations:
                    if method.lower() in HTTP_METHODS:
                        declared.append({
                            "name": f"{method.upper()} {route}",
                            "route": route,
                            "service": None,
                            "declared_in": rel,
                        })
    return declared


VERB_TOKEN = re.compile(r"\b(?:Map|Http)(Get|Post|Put|Delete|Patch)\b", re.IGNORECASE)
QUOTED = re.compile(r"[\"']([^\"']*)[\"']")


def code_route(evidence):
    """The route string the implementation registers, or "" when it registers none.

    `api.MapGet("/items/facets", ...)` gives `/items/facets`; `[HttpGet("{id:int}")]` gives
    `{id:int}`; a bare `[HttpGet]` gives "" because its path is inherited entirely from the
    controller or group it sits in.
    """
    found = QUOTED.search(evidence)
    return found.group(1) if found else ""


def code_verb(evidence):
    found = VERB_TOKEN.search(evidence)
    return found.group(1).upper() if found else None


def path_tokens(path):
    """A path as a comparable sequence: parameters collapse to `*`, literals lowercase.

    `/items/{id:int}` and `/items/{id}` both become `["items", "*"]`. Parameter names and
    route constraints are spelled differently on the two sides and carry no identity.
    """
    tokens = []
    for segment in path.split("/"):
        if not segment:
            continue
        tokens.append("*" if "{" in segment or segment.startswith(":") else segment.lower())
    return tokens


def route_matches(route, evidence, verb=None):
    """A declared operation matches a fact when the code's route is a tail of the declared one.

    **A tail, not the whole path, because the prefix is genuinely not there to compare.**
    OpenAPI writes `/api/catalog/items`; the code writes `MapGet("/items", ...)` under a
    group whose `/api/catalog` prefix is established on a different line. The cited evidence
    is one line, so the prefix is absent by construction and any matcher demanding it reports
    a found endpoint as missing.

    **The prior version demanded it** — the declaration's last two literal segments had to
    appear in the cited line — and reported seven implemented operations missing on the one
    subject that has ever been measured. It also matched on substrings, so `catalog` matched
    inside `GetCatalogFacets` and let one declaration claim another's fact.

    A code route of "" inherits its whole path and is unmatchable here; it is reported
    unmatched rather than allowed to satisfy everything.
    """
    code = code_route(evidence)
    declared_tokens = path_tokens(route)
    code_tokens = path_tokens(code)
    if not code_tokens or len(code_tokens) > len(declared_tokens):
        return False
    if verb:
        found_verb = code_verb(evidence)
        if found_verb and found_verb != verb.upper():
            return False
    return declared_tokens[len(declared_tokens) - len(code_tokens):] == code_tokens


# Cases the matcher must get right, checked on every run. **This is the control that was
# missing**, and its absence is why a matcher that reported implemented endpoints as missing
# passed as healthy for a day: the only control tested that fabricated routes are *rejected*,
# which a too-strict matcher passes trivially. Each `True` case below is a real shape taken
# from a subject on disk and verified by opening the source.
MATCHER_CASES = [
    ("/api/catalog/items", "GET", 'v1.MapGet("/items", GetAllItemsV1)', True),
    ("/api/catalog/items/{id}", "DELETE", 'api.MapDelete("/items/{id:int}", DeleteItemById)', True),
    ("/api/catalog/items/facets", "GET", 'api.MapGet("/items/facets", GetCatalogFacets)', True),
    ("/api/catalog/items/type/{typeId}/brand/{brandId}", "GET",
     'v1.MapGet("/items/type/{typeId}/brand/{brandId?}", GetItemsByBrandAndTypeId)', True),
    ("/api/orders/{id}", "GET", '[HttpGet("{id:int}")]', True),
    ("/api/catalog/items", "GET", 'api.MapGet("/items/facets", GetCatalogFacets)', False),
    ("/api/catalog/items", "POST", 'v1.MapGet("/items", GetAllItemsV1)', False),
    ("/api/catalog/brands", "GET", 'v1.MapGet("/items", GetAllItemsV1)', False),
    ("/api/catalog/items", "GET", "[HttpGet]", False),
]


def matcher_control():
    """Run the matcher against known answers. A failure invalidates the report.

    Independent of any subject: it tests the comparison itself, so editing `route_matches`
    cannot quietly change what recall means. The estate-derived decoy control below tests
    the other direction, against this subject's own declarations.
    """
    failures = [
        {"route": route, "verb": verb, "evidence": evidence, "expected": expected}
        for route, verb, evidence, expected in MATCHER_CASES
        if route_matches(route, evidence, verb) != expected
    ]
    return {
        "cases": len(MATCHER_CASES),
        "must_match": sum(1 for c in MATCHER_CASES if c[3]),
        "must_not_match": sum(1 for c in MATCHER_CASES if not c[3]),
        "failures": failures,
        "passed": not failures,
        "note": "false-negative control — known implementations that must be recognised. "
                "The decoy control cannot detect a matcher that is too strict; this can",
    }


def reconcile(declared, facts, kinds):
    """Look for each declared name in the evidence of a fact of a relevant kind.

    Reports per item, not per total. An unmatched item names what is missing; the
    caller can open the declaration and see for itself.
    """
    candidates = [f for f in facts if f["kind"] in kinds]
    matched, missing, claimed = [], [], set()
    for item in declared:
        # A fact satisfies at most one declared item. Without this, one broadly-matching fact
        # could be counted as evidence for every declaration in the file and carry recall to
        # 1.0 on its own — the arithmetic would look perfect and mean nothing.
        hit = next((f for i, f in enumerate(candidates)
                    if i not in claimed and item["name"] in f.get("evidence", "")), None)
        if hit:
            claimed.add(candidates.index(hit))
            matched.append({**item, "found_at": f"{hit['file']}:{hit['line']}"})
        else:
            missing.append(item)
    return matched, missing


NONSENSE = ["/api/nonexistent/xyzzy", "/quux/wibble"]


def decoys(declared):
    """Near-miss routes built from the subject's own declarations, by replacing the final
    literal segment of each real route with a token that is not in the estate.

    **The point is that these CAN match, and must not.** An earlier control used only
    invented words — `xyzzy`, `frobnicate` — which nothing in any codebase would contain, so
    it passed by construction and established nothing while being reported as validating every
    recall figure. An independent review named it: a control that cannot fail is not a control.
    A decoy shares the real route's whole prefix and differs only where it matters, so a
    matcher that is satisfied by a prefix, or by a distinctive-looking middle segment, fails
    here loudly.
    """
    built = []
    for item in declared:
        segments = [s for s in item["route"].split("/") if s and "{" not in s]
        if segments:
            built.append("/" + "/".join(segments[:-1] + ["zzqx" + segments[-1][:3]]))
    return built


def negative_control(facts, declared_http, declared_rpc):
    """Things that must not match, run on every invocation.

    Covers **both** matchers — routes through `route_matches` and gRPC methods through the
    same name-in-evidence test the reconciliation uses. The earlier control ran over routes
    only, so half the reported recall rested on a matcher nothing had ever probed.
    """
    routes = [f for f in facts if f["kind"] == "inbound_route"]
    evidence = [f.get("evidence", "") for f in routes]

    route_decoys = decoys(declared_http)
    falsely_matched = [r for r in NONSENSE + route_decoys
                       if any(route_matches(r, e) for e in evidence)]

    # The same shape for gRPC: a method name that is not in the estate must not be found.
    rpc_decoys = ["zzqx" + item["name"] for item in declared_rpc]
    falsely_matched += [n for n in rpc_decoys if any(n in e for e in evidence)]

    return {
        "nonsense_routes": len(NONSENSE),
        "near_miss_route_decoys": len(route_decoys),
        "grpc_name_decoys": len(rpc_decoys),
        "falsely_matched": falsely_matched,
        "passed": not falsely_matched,
        "note": "decoys are built from the subject's own declarations and share the real "
                "prefix, so a matcher satisfied by a prefix fails here rather than passing",
    }


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    root, fact_base = sys.argv[1], sys.argv[2]

    with open(fact_base, "r", encoding="utf-8") as handle:
        facts = json.load(handle)["facts"]

    categories = {}

    proto_all = declared_grpc(root)
    # One rpc can be declared in more than one .proto — a service copy and a client copy of the
    # same contract. Counting both inflates the denominator and reports the same method missing
    # twice. Deduplicate on (service, name); keep every declaring location so the double
    # declaration stays visible rather than being silently collapsed.
    by_identity = {}
    for item in proto_all:
        key = (item["service"], item["name"])
        if key in by_identity:
            by_identity[key]["declared_in"] += f" · {item['declared_in']}"
        else:
            by_identity[key] = dict(item)
    proto = list(by_identity.values())
    if proto:
        # A .proto is generated-from nothing — it is the source the C# stubs are generated
        # FROM, so it is a genuine independent declaration. It can still over-count: a
        # declared rpc with no implementation is a real finding, not a measurement error.
        # **Both kinds, because a gRPC entry point is spelled differently per language.** The
        # C# rule files them as inbound routes and the Go rule as grpc methods; reconciling
        # only the first reported a recall of 0.25 on an estate whose handlers had all been
        # extracted, under the other name.
        matched, missing = reconcile(proto, facts, {"inbound_route", "grpc_method"})
        categories["grpc_methods"] = {
            "source": ".proto service definitions",
            "declared": len(proto),
            "declaration_sites": len(proto_all),
            "matched": len(matched),
            "missing": missing,
            "recall": round(len(matched) / len(proto), 3) if proto else None,
            "caveat": "a declared rpc with no implementation is a finding about the estate, "
                      "not an extraction defect — open the declaration to tell them apart",
        }
    else:
        categories["grpc_methods"] = {"source": None, "state": "unmeasured — no .proto in subject"}

    http_all = declared_http(root)
    # Two documents can describe the same operation — a v1 and a v2 file for one service, or a
    # generated copy beside a checked-in one. Counting both inflates the denominator, the same
    # defect already found and fixed for protocol definitions. Deduplicate on method-and-route,
    # keeping every declaring document so the duplication stays visible.
    seen = {}
    for item in http_all:
        seen.setdefault(item["name"], dict(item))
    http = list(seen.values())
    if http:
        candidates = [f for f in facts if f["kind"] == "inbound_route"]
        # One fact, one declaration — see the note in `reconcile`. **Assigned most-specific
        # first rather than in file order.** Taking the first unclaimed match made recall
        # order-dependent: a general declaration could claim a specific declaration's fact and
        # leave the specific one reported missing. Ranking candidate pairs by how many path
        # segments the implementation actually spells means `/items/facets` claims its own
        # registration before `/items` can.
        pairs = []
        for declaration_index, item in enumerate(http):
            verb = item["name"].split(" ", 1)[0]
            for fact_index, fact in enumerate(candidates):
                evidence = fact.get("evidence", "")
                if route_matches(item["route"], evidence, verb):
                    pairs.append((len(path_tokens(code_route(evidence))),
                                  declaration_index, fact_index))
        pairs.sort(key=lambda pair: -pair[0])
        assigned, used_declarations, used_facts = {}, set(), set()
        for _, declaration_index, fact_index in pairs:
            if declaration_index in used_declarations or fact_index in used_facts:
                continue
            used_declarations.add(declaration_index)
            used_facts.add(fact_index)
            assigned[declaration_index] = candidates[fact_index]

        matched, missing = [], []
        for declaration_index, item in enumerate(http):
            hit = assigned.get(declaration_index)
            (matched if hit else missing).append(
                {**item, "found_at": f"{hit['file']}:{hit['line']}"} if hit else item)
        categories["http_operations"] = {
            "source": "OpenAPI documents",
            "declared": len(http),
            "declaration_sites": len(http_all),
            "matched": len(matched),
            "missing": [m["name"] for m in missing],
            "recall": round(len(matched) / len(http), 3),
            "caveat": "weaker than a protocol definition — where the document is generated from "
                      "the same code the rules read, agreement is not corroboration",
        }
    else:
        categories["http_operations"] = {
            "source": None,
            "state": "unmeasured — no OpenAPI document in subject",
            "extracted": sum(1 for f in facts if f["kind"] == "inbound_route"),
        }

    for kind in ("durable_write", "outbound_http", "message_consumer",
                 "background_trigger", "env_read", "config_ref"):
        categories[kind] = {
            "source": None,
            "state": "unmeasured — no declarative source enumerates this population",
            "extracted": sum(1 for f in facts if f["kind"] == kind),
        }

    measured = [c for c in categories.values() if c.get("recall") is not None]
    control = negative_control(facts, http, proto)
    self_test = matcher_control()
    invalid = None
    if not control["passed"]:
        invalid = ("negative control failed — the matcher accepts routes that do not exist, "
                   "so no recall figure below can be trusted")
    elif not self_test["passed"]:
        invalid = ("matcher control failed — the matcher rejects implementations it is known "
                   "to have been given, so every recall figure below is understated")
    json.dump({
        "root": root,
        "fact_base": fact_base,
        "matcher_control": self_test,
        "negative_control": control,
        "categories": categories if invalid is None else {"INVALID": invalid, **categories},
        "summary": {
            "categories_measured": len(measured),
            "categories_unmeasured": len(categories) - len(measured),
            "note": "an unmeasured category is not a passing category. Recall for it is unknown",
        },
    }, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
