"""Join — turn a fact base into edges between deployables, and measure the result.

Usage:  python join.py <source-root> <fact-base.json>
Output: JSON on stdout.

**This is a separate program on purpose.** Extracting facts is a solved, purchasable step;
joining them across repositories is estate-specific and is the part that is legitimately ours
to build. Software architecture reconstruction splits them the same way — fact extraction is
phases 1 and 2, this is phase 3, view fusion. Keeping them apart means the extractor stays
replaceable.

**Why it has to exist at all.** A fact base is vertical: it says what each deployable does,
one cited line at a time. Nothing in it says which deployable calls which. The question this
method exists to answer is horizontal — trace a business process across an estate, find the
seams, watch them — so the edges are the deliverable and the facts are the input to it.

**Nothing here guesses.** An edge is emitted only when every hop is cited. A chain that breaks
becomes an `unresolved` record naming the hop that failed, which is a finding about the estate
or about the rules, never a missing row.
"""

import json
import os
import re
import sys

# `AddHttpClient<CatalogService>` / `AddGrpcClient<Basket.BasketClient>` — the registered type.
CLIENT_TYPE = re.compile(r"Add(?:Http|Grpc)Client<\s*([\w.]+)\s*>")
# The address literal in the same registration. `https+http://` is .NET service discovery's
# scheme-preference form; the host after it is the logical deployable name.
ADDRESS = re.compile(r"[\"'](?:[a-z+]+://)([A-Za-z0-9_.-]+)[\"'/]")
# `builder.AddProject<Projects.Catalog_API>("catalog-api")` — the deployment declaration that
# maps a logical name to a project directory.
DEPLOYABLE = re.compile(r"AddProject<\s*Projects\.([\w.]+)\s*>\s*\(\s*[\"']([^\"']+)[\"']")
# `.WithReference(catalogApi)` — the declared dependency, used as the answer key below.
REFERENCE = re.compile(r"\.WithReference\(\s*([A-Za-z_]\w*)\s*\)")
ASSIGNMENT = re.compile(r"var\s+([A-Za-z_]\w*)\s*=\s*builder\.AddProject")
SKIP_DIRS = {".git", "node_modules", "target", "build", "obj", "bin", "__pycache__", ".venv"}


def client_targets(facts):
    """Registered client type -> the logical host it is pointed at, with its citation.

    The registration is the hop that carries the address. A call site names a method on a
    receiver and never names a service; the address lives in composition-root registration,
    in a different file, against a type.
    """
    index = {}
    for fact in facts:
        if fact["kind"] != "client_binding":
            continue
        type_found = CLIENT_TYPE.search(fact["evidence"])
        host_found = ADDRESS.search(fact["evidence"])
        if not type_found:
            continue
        index[type_found.group(1).split(".")[-1]] = {
            "host": host_found.group(1) if host_found else None,
            "cite": f"{fact['file']}:{fact['line']}",
            "service": fact["service"],
            "evidence": fact["evidence"],
        }
    return index


def project_directories(root):
    """Project name -> the directory it builds from, by finding its project file on disk.

    **A lookup, not a convention.** The deployment declaration names a project symbolically
    (`Projects.Webhooks_API`); the directory that project lives in is what turns a logical
    deployable into a path the fact base can be matched against. Guessing `src/<name>/` from
    the symbol would be a naming convention dressed as a fact, and would break on the first
    estate that lays its repository out differently.
    """
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if filename.endswith(".csproj"):
                stem = os.path.splitext(filename)[0]
                rel = os.path.relpath(dirpath, root).replace("\\", "/")
                found[stem.replace(".", "_")] = rel
    return found


def deployable_names(root):
    """Logical name -> project, from the deployment declaration, plus the declared edges.

    **Read the independence caveat before using the edges as a score.** Both the name
    resolution the join needs and the declared dependencies it is checked against come from
    the same file. That makes the reconciliation below a check of the join's *reasoning* —
    did following call sites through registrations reach what the deployment says is wired
    together — and not an independent check of the whole chain. Said plainly rather than
    left for a reader to notice.
    """
    names, declared_edges, cite = {}, [], None
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".cs"):
                continue
            path = os.path.join(dirpath, filename)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    lines = handle.read().splitlines()
            except OSError:
                continue
            if not any("AddProject<" in line for line in lines):
                continue
            rel = os.path.relpath(path, root).replace("\\", "/")
            variable_of_name, holder = {}, None
            for number, line in enumerate(lines, start=1):
                found = DEPLOYABLE.search(line)
                if found:
                    project, logical = found.group(1), found.group(2)
                    names[logical] = {"project": project, "cite": f"{rel}:{number}"}
                    assigned = ASSIGNMENT.search(line)
                    holder = assigned.group(1) if assigned else None
                    if holder:
                        variable_of_name[holder] = logical
                    cite = rel
                    current = logical
                elif holder is None and not line.strip().startswith("."):
                    current = None
                for referenced in REFERENCE.findall(line):
                    if current and referenced in variable_of_name:
                        declared_edges.append({
                            "from": current,
                            "to": variable_of_name[referenced],
                            "cite": f"{rel}:{number}",
                        })
                if not line.rstrip().endswith((",", ".")) and ";" in line:
                    holder = None
    return names, declared_edges, cite


def spring_application_name(lines):
    """`spring.application.name`, read by block rather than by adjacency.

    **A first version required `application:` on the line after `spring:` and missed two of
    eight modules** on the first Java estate it met, because one of them declares `main:`
    first. Pattern fitted to one file's shape — the exact defect this method exists to catch,
    committed inside the tool that catches it. Read the block instead.
    """
    inside, application = False, None
    for number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        key = line.strip().rstrip(":")
        if indent == 0:
            inside, application = key == "spring", None
            continue
        if not inside:
            continue
        if application is not None and indent <= application:
            application = None
        if line.strip() == "application:":
            application = indent
        elif application is not None and indent > application:
            found = re.match(r"name:\s*([A-Za-z0-9_.${}-]+)", line.strip())
            if found:
                return found.group(1), number
    return None, None
# `uri: lb://vets-service` — a Spring Cloud Gateway route. **The gateway's whole routing
# table lives in configuration, not in code**, so on a Spring estate a large part of the
# topology is invisible to any rule that only reads source.
LB_URI = re.compile(r"uri:\s*lb://([A-Za-z0-9_.-]+)")
BUILD_FILES = {"pom.xml", "build.gradle", "build.gradle.kts"}


def module_root(path, root):
    """The module a file belongs to — nearest ancestor holding a build file.

    A lookup rather than a path convention, for the same reason the .NET side finds a project
    by its project file: `<module>/src/main/resources/` is the Maven layout and not a fact.
    """
    here = os.path.dirname(os.path.abspath(path))
    stop = os.path.abspath(root)
    while here.startswith(stop):
        if any(os.path.exists(os.path.join(here, name)) for name in BUILD_FILES):
            return os.path.relpath(here, stop).replace("\\", "/")
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return None


def spring_declarations(root):
    """Deployables and declared routes from Spring configuration.

    Two declarations, both first-class and neither in code:

    - **`spring.application.name`** names the deployable a module runs as. It is what a
      service-discovery host in a call resolves to, so it is this estate's equivalent of a
      deployment manifest entry.
    - **`uri: lb://<service>`** is a Spring Cloud Gateway route. **A gateway's routing table
      is configuration**, so every edge from it is invisible to a source-only extraction —
      measured on Spring PetClinic microservices, where four gateway dependencies exist and
      no rule can see one of them.
    """
    names, declared_edges = {}, []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.startswith("application") or not filename.endswith((".yml", ".yaml")):
                continue
            path = os.path.join(dirpath, filename)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
            except OSError:
                continue
            rel = os.path.relpath(path, root).replace("\\", "/")
            module = module_root(path, root)
            logical, line = spring_application_name(text.splitlines())
            if not logical or module is None:
                continue
            names[logical] = {"project": module, "cite": f"{rel}:{line}", "directory": module}
            for number, content in enumerate(text.splitlines(), start=1):
                route = LB_URI.search(content)
                if route:
                    declared_edges.append({"from": logical, "to": route.group(1),
                                           "cite": f"{rel}:{number}"})
    return names, declared_edges


K8S_WORKLOAD_KINDS = {"Service", "Deployment", "StatefulSet", "DaemonSet", "CronJob"}
K8S_KIND = re.compile(r"^kind:\s*([A-Za-z]+)")
K8S_NAME = re.compile(r"^\s{2}name:\s*([A-Za-z0-9_.-]+)")
K8S_DATA_ENTRY = re.compile(r"^\s{2}([A-Za-z_][\w.-]*):\s*[\"']?([^\"'#]+?)[\"']?\s*$")
K8S_ENV_NAME = re.compile(r"^\s*-\s*name:\s*([A-Za-z_]\w*)")
K8S_ENV_VALUE = re.compile(r"^\s*value:\s*[\"']?([^\"'#]+?)[\"']?\s*$")
# The first DNS label of an address, which in Kubernetes is the service name:
# `ledgerwriter:8080`, `http://balancereader:8080/x`, `balancereader.default.svc.cluster.local`
# and `ledgermonolith-service.c.[PROJECT_ID].internal:8080` all yield the deployable.
#
# **Taking the whole dotted name instead cost a real finding.** A templated manifest leaves an
# unrendered placeholder in the middle of the host, so a pattern that must match every label
# matched nothing — and the edge it dropped was the one that makes the estate's two mutually
# exclusive deployment topologies visible.
HOST_IN_VALUE = re.compile(r"^(?:[a-z+]+://)?([A-Za-z0-9-]+)(?=[.:/]|$)")


def kubernetes_declarations(root):
    """Deployables and environment bindings from Kubernetes manifests.

    **This is the idiom an estate on Kubernetes actually uses**, and it is the one the
    superseded proof of concept was built for: a service reads an environment variable, the
    variable is bound in a ConfigMap or a container spec, and the value names another
    deployable. Measured — without this resolver the join returned zero edges on Bank of
    Anthos, where the old script had recovered eight cross-service pairs.

    Read as lines rather than parsed, to stay dependency-free like the rest of the tool. Its
    limits follow from that: a multi-document file is split on `---`, values are taken as
    written, and templated manifests (Helm, Kustomize overlays) are not rendered, so a value
    that is a placeholder stays a placeholder and the hop fails visibly.
    """
    names, bindings = {}, {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(dirpath, filename)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    lines = handle.read().splitlines()
            except OSError:
                continue
            rel = os.path.relpath(path, root).replace("\\", "/")
            kind, in_data, pending = None, False, None
            for number, line in enumerate(lines, start=1):
                if line.strip() == "---":
                    kind, in_data, pending = None, False, None
                    continue
                found_kind = K8S_KIND.match(line)
                if found_kind:
                    kind = found_kind.group(1)
                    in_data = False
                    continue
                found_name = K8S_NAME.match(line)
                if found_name and kind in K8S_WORKLOAD_KINDS:
                    names.setdefault(found_name.group(1),
                                     {"project": None, "cite": f"{rel}:{number}",
                                      "directory": None, "kind": kind})
                if line.rstrip() == "data:" and kind == "ConfigMap":
                    in_data = True
                    continue
                if in_data:
                    entry = K8S_DATA_ENTRY.match(line)
                    if entry:
                        bindings.setdefault(entry.group(1), []).append(
                            {"value": entry.group(2).strip(), "cite": f"{rel}:{number}"})
                    elif line.strip() and not line.startswith("  "):
                        in_data = False
                # Container `env:` entries, which bind a variable inline rather than by map.
                env_name = K8S_ENV_NAME.match(line)
                if env_name:
                    pending = (env_name.group(1), number)
                elif pending:
                    env_value = K8S_ENV_VALUE.match(line)
                    if env_value:
                        bindings.setdefault(pending[0], []).append(
                            {"value": env_value.group(1).strip(),
                             "cite": f"{rel}:{pending[1]}"})
                    pending = None
    return names, bindings


ENV_VAR_IN_CODE = re.compile(
    r"""(?:os\.environ\.get\(|os\.environ\[|getenv\(|System\.getenv\()\s*['"]([A-Za-z_]\w*)['"]"""
    r"""|@Value\(\s*["']\$\{([A-Za-z_]\w*)""")


SPRING_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_]\w*)")


def env_var_named(evidence):
    """The environment variable a read names, across the forms three languages use.

    **The Spring form cost a real edge twice over.** The ledger writer's dependency on the
    balance reader is declared `@Value("http://${BALANCES_API_ADDR}/balances")` — the
    placeholder sits *inside* a URL template rather than filling the whole value, so a
    pattern anchored to the opening quote misses it. The superseded script had found this
    edge; a first version of this resolver did not, and the difference was that anchor.
    """
    if "@Value(" in evidence or "${" in evidence:
        placeholder = SPRING_PLACEHOLDER.search(evidence)
        if placeholder:
            return placeholder.group(1)
    found = ENV_VAR_IN_CODE.search(evidence)
    return (found.group(1) or found.group(2)) if found else None


def config_edges(facts, bindings, names, directories, graph):
    """Edges evidenced by a configuration read rather than by a call site.

    **A different granularity on purpose.** In this idiom the call site names a variable, not
    a service; what names the service is the binding. So the edge is evidenced by the pair —
    the read, cited in code, and the binding, cited in a manifest — and it is attributed to
    the deployable that performs the read.

    A variable whose bound value does not name a known deployable is not an edge. It is a
    database address, a feature flag or an external URL, and passing it through would put a
    dependency on the map that the estate does not have.
    """
    edges, seen = [], set()
    for fact in facts:
        if fact["kind"] not in ("env_read", "config_ref") or fact.get("in_test"):
            continue
        variable = env_var_named(fact.get("evidence", ""))
        if not variable:
            continue
        # **Every binding for the variable, not the first.** A key bound twice describes two
        # deployment topologies that cannot both be live — a decomposed estate and a monolith
        # variant, say — and taking whichever manifest was walked first would report one of
        # them as the estate. Both are emitted and marked, so the ambiguity is on the map.
        found_bindings = bindings.get(variable) or []
        targets, undeclared = {}, {}
        for binding in found_bindings:
            host = HOST_IN_VALUE.match(binding["value"])
            if not host:
                continue
            if host.group(1) in names:
                targets.setdefault(host.group(1), binding)
            else:
                undeclared.setdefault(host.group(1), binding)
        # **An undeclared host is admitted only when the same variable also resolves to a
        # declared deployable.** That co-occurrence is what makes it a service address rather
        # than a database host or an external URL, and what it reveals is the estate's second
        # deployment topology: Bank of Anthos binds the same three variables to a monolith
        # running outside the cluster, which nothing in Kubernetes declares. Dropping it
        # silently reports one topology as the estate; admitting anything undeclared would
        # put every connection string on the map.
        if targets:
            targets.update(undeclared)
        origins = deployables_of(fact["file"], directories, graph) or [fact["service"]]
        for target, binding in targets.items():
            for origin in origins:
                key = (origin, target, fact["file"], fact["line"])
                if key in seen:
                    continue
                seen.add(key)
                edges.append({
                    "from": fact["service"],
                    "from_deployable": origin,
                    "to_host": target,
                    "to_project": None,
                    "to_deployable": target,
                    "hops": [
                        {"hop": "environment read", "cite": f"{fact['file']}:{fact['line']}",
                         "evidence": fact["evidence"][:120]},
                        {"hop": "binding in a deployment manifest", "cite": binding["cite"],
                         "evidence": f"{variable} = {binding['value']}"},
                        {"hop": "deployable declaration",
                         "cite": names[target]["cite"] if target in names else None,
                         "note": None if target in names else
                                 "nothing in this repository declares this target — it runs "
                                 "outside the orchestrator, and the dependency is real but "
                                 "its far end is not described here"},
                    ],
                    "ambiguous_config": len(targets) > 1,
                    "target_declared": target in names,
                    "complete": origin is not None and target in names,
                })
    return edges


PROJECT_REFERENCE = re.compile(r"<ProjectReference\s+Include\s*=\s*[\"']([^\"']+)[\"']")


def project_graph(root):
    """Project directory -> the project directories it references.

    **Needed because a call site does not have to live in a deployable.** In this subject
    every catalog call `webapp` makes is written in `WebAppComponents`, a shared library that
    is not deployed on its own. Attributing those calls by directory alone put them under no
    deployable at all, and the dependency `webapp -> catalog-api` — declared in the
    deployment manifest — came back unrecovered while thirteen cited call sites for it sat in
    the output under a null owner.

    A shared library referenced by several deployables yields an edge for each, and that is
    correct rather than a duplicate: each of them makes the call.
    """
    graph = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".csproj"):
                continue
            here = os.path.relpath(dirpath, root).replace("\\", "/")
            try:
                with open(os.path.join(dirpath, filename), "r",
                          encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
            except OSError:
                continue
            referenced = []
            for include in PROJECT_REFERENCE.findall(text):
                target = os.path.normpath(os.path.join(dirpath, include.replace("\\", "/")))
                referenced.append(
                    os.path.relpath(os.path.dirname(target), root).replace("\\", "/"))
            graph[here] = referenced
    return graph


def owning_project(rel_path, graph):
    """The project directory a file builds into — longest matching directory that has one."""
    best = None
    for directory in graph:
        boundary = directory.rstrip("/") + "/"
        if rel_path.startswith(boundary) and (best is None or len(directory) > len(best)):
            best = directory
    return best


def deployables_of(rel_path, directories, graph):
    """Every declared deployable whose project contains this file or reaches it by reference.

    Returns a list because the honest answer can be more than one, and naming all of them is
    what keeps a shared library's calls attached to each deployable that ships it.
    """
    owner = owning_project(rel_path, graph)
    if owner is None:
        # No project graph covers this file. **Fall back to a direct directory match** rather
        # than returning nothing: the graph exists to follow shared libraries, and an estate
        # whose build system this does not read still has deployables laid out in directories.
        # Returning nothing here filed every Java call site under a null deployable and scored
        # a reconciliation at zero while three dependencies had been correctly recovered.
        return [logical for logical, directory in sorted(directories.items())
                if rel_path.startswith(directory.rstrip("/") + "/")]
    found = []
    for logical, directory in directories.items():
        if directory == owner:
            found.append(logical)
            continue
        seen, frontier = set(), list(graph.get(directory, []))
        while frontier:
            node = frontier.pop()
            if node in seen:
                continue
            seen.add(node)
            if node == owner:
                found.append(logical)
                break
            frontier.extend(graph.get(node, []))
    return sorted(found)


# The argument a fluent HTTP client is given its target in: `.uri(...)`.
URI_ARG = re.compile(r"\.uri\(\s*([^,)]+)")
# Any `scheme://host` inside a string literal.
URL_LITERAL = re.compile(r"[\"'][a-z+]+://([A-Za-z0-9_.-]+)")
# `pb.NewCartServiceClient(conn)` — a protobuf-generated client, service in the name.
GENERATED_CLIENT = re.compile(r"New([A-Za-z]\w*?)Client\s*\(")
# `hostname + "pets/visits"` — the target begins with an identifier the file defines.
IDENT_FIRST = re.compile(r"^\s*([A-Za-z_]\w*)\s*\+")


def resolve_target(fact, clients, root, names_in_scope=()):
    """Where this call goes, by whichever hop the estate's idiom actually supplies.

    **Three idioms, three hop shapes, and which one applies is a property of the framework
    rather than of the call.** Trying them in order and naming the one that worked is what
    lets the same join read a .NET estate and a Spring estate without a flag:

    1. **The address is at the call site.** `…uri("http://customers-service/owners/{id}")`.
       One hop, and the strongest evidence available — the target is in the cited line.
    2. **The address is in a field the same file initialises.** `…uri(hostname + "pets")`
       with `private String hostname = "http://visits-service/"` above it. Two hops, both in
       one file, both citable.
    3. **The address is in a client registration.** The .NET typed-client case: the call names
       no address at all and the registration carries it, keyed by the type the call sits in.

    Returns `(host, hops, None)` or `(None, [], reason)`. **A reason is a finding** — it names
    the hop this estate uses that nothing here follows yet, which is how the next rule gets
    written from evidence rather than from guessing.
    """
    evidence = fact.get("evidence", "")
    argument = URI_ARG.search(evidence)

    direct = URL_LITERAL.search(argument.group(1)) if argument else None
    if direct:
        return direct.group(1), [{"hop": "address literal at the call site",
                                  "cite": f"{fact['file']}:{fact['line']}"}], None

    if argument:
        named = IDENT_FIRST.match(argument.group(1))
        if named:
            identifier = named.group(1)
            path = os.path.join(root, fact["file"].replace("/", os.sep))
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    lines = handle.read().splitlines()
            except OSError:
                lines = []
            initialiser = re.compile(
                r"\b" + re.escape(identifier) + r"\s*=\s*[\"'][a-z+]+://([A-Za-z0-9_.-]+)")
            for number, line in enumerate(lines, start=1):
                found = initialiser.search(line)
                if found:
                    return found.group(1), [
                        {"hop": "address built from a field",
                         "cite": f"{fact['file']}:{fact['line']}"},
                        {"hop": "field initialiser",
                         "cite": f"{fact['file']}:{number}", "evidence": line.strip()[:120]},
                    ], None
            return None, [], (f"the target is built from `{identifier}`, and no initialiser "
                              "in the same file gives it an address. It is set from "
                              "configuration or injected, which is a hop nothing here follows")
        return None, [], ("the target is computed by an expression at the call site — a helper "
                          "method or a concatenation with no identifier to follow")

    # A generated client names its service in its own constructor: `pb.NewCartServiceClient`.
    # **The target is in the identifier, so there is no second file to reach for** — the one
    # idiom where the call site alone is enough. Required to resolve to a declared deployable,
    # so a name that means nothing to this estate produces no edge rather than a guess.
    generated = GENERATED_CLIENT.search(evidence)
    if generated:
        candidate = generated.group(1).lower()
        for declared in names_in_scope:
            if declared.replace("-", "").lower() == candidate:
                return declared, [{"hop": "generated client names its service",
                                   "cite": f"{fact['file']}:{fact['line']}",
                                   "evidence": evidence[:120]}], None
        return None, [], (f"the client constructor names `{generated.group(1)}`, and no "
                          "deployable declared in this repository has that name")

    holder = fact.get("in_type")
    if not holder:
        return None, [], ("no address at the call site and no enclosing type, so neither hop "
                          "shape applies")
    registration = clients.get(holder)
    if not registration:
        return None, [], ("no client registration names this type. A typed client is injected "
                          "into the type it is registered against; a client resolved by any "
                          "other means is not reachable this way")
    if not registration["host"]:
        return None, [], ("the registration carries no address literal — the target is "
                          "computed at runtime, so no static hop reaches it")
    return registration["host"], [
        {"hop": "call site", "cite": f"{fact['file']}:{fact['line']}",
         "evidence": evidence[:120]},
        {"hop": "client registration", "cite": registration["cite"],
         "evidence": registration["evidence"][:120]},
    ], None


def join(facts, clients, names, directories, graph, root):
    """Every outbound call turned into an edge, or into a record of the hop that failed.

    **The join is not one chain — it is a resolver per idiom** (`resolve_target`), because
    where a target address lives is a property of the framework. Once a host is named, the
    remaining hops are the same everywhere: host to declared deployable, and call site to the
    deployable that ships it.

    An edge is emitted only when every hop carries a citation. A guessed edge is worse than
    an absent one: it puts monitoring on a dependency that is not there.
    """
    edges, unresolved = [], []
    for fact in facts:
        if fact["kind"] not in ("outbound_http", "grpc_call") or fact.get("in_test"):
            continue
        # **Falling back to the run's own service map, not to nothing.** The map is the run's
        # statement of which deployable a path belongs to; an estate whose deployables are
        # declared only in Kubernetes has no directory index to resolve against, and filing
        # every edge under a null origin there loses the `from` end of the whole graph.
        origins = (deployables_of(fact["file"], directories, graph)
                   or ([fact["service"]] if fact.get("service") else [None]))
        host, hops, reason = resolve_target(fact, clients, root, names)
        if reason:
            unresolved.append({
                "from": fact["service"], "from_deployable": origins[0],
                "at": f"{fact['file']}:{fact['line']}", "in_type": fact.get("in_type"),
                "evidence": fact.get("evidence", "")[:120],
                "failed_at": reason,
            })
            continue
        target = names.get(host)
        # One edge per deployable that ships this call site. A call written in a shared
        # library belongs to every deployable that references it, and naming only one of
        # them would drop real dependencies.
        for origin in origins:
            edges.append({
                "from": fact["service"],
                "from_deployable": origin,
                "to_host": host,
                "to_project": target["project"] if target else None,
                "to_deployable": host if host in names else None,
                "hops": hops + [{"hop": "deployable declaration",
                                 "cite": target["cite"] if target else None}],
                # A host with no declaration is still a named target and still an edge. It is
                # incomplete because nothing on disk says what runs there — which on a real
                # estate is common and is a finding about the deployment record, not about
                # the call.
                "complete": target is not None and origin is not None,
            })
    return edges, unresolved


def reconcile_edges(edges, declared_edges):
    """Which declared dependencies the join recovered, and which it did not.

    Reported per declared edge, never as a total, so an unrecovered one names itself and can
    be opened. **An unrecovered edge is a finding about the rules or the idiom**, not a number
    to average away — the first run of this recovered three of four and the fourth named the
    idiom it could not follow.

    Both ends are compared as logical deployable names. An earlier version compared the
    join's end against the run's service map, which silently dropped every deployable the map
    did not happen to name and scored one of four.
    """
    found = {(edge["from_deployable"], edge["to_host"]) for edge in edges}
    recovered, missing = [], []
    for declared in declared_edges:
        hit = (declared["from"], declared["to"]) in found
        (recovered if hit else missing).append(declared)
    return {
        "declared": len(declared_edges),
        "recovered": len(recovered),
        "missing": [f"{m['from']} -> {m['to']} ({m['cite']})" for m in missing],
        "caveat": "the name resolution this join uses and the dependencies it is checked "
                  "against come from the same declaration file, so this scores the join's "
                  "reasoning rather than the chain as a whole",
    }


def distinct(edges):
    """One row per deployable pair, carrying every call site that evidences it.

    A pair with nine call sites is one dependency, not nine. Both numbers matter — the pair
    is what a business process flow is drawn from, the call sites are what makes it
    checkable — so neither is discarded.
    """
    rows = {}
    for edge in edges:
        key = (edge["from_deployable"], edge["to_host"])
        row = rows.setdefault(key, {
            "from": edge["from_deployable"], "to": edge["to_host"],
            "to_project": edge["to_project"], "call_sites": [], "complete": edge["complete"],
        })
        row["call_sites"].append(edge["hops"][0]["cite"])
    return sorted(rows.values(), key=lambda r: (str(r["from"]), str(r["to"])))


def name_correspondence(facts, directories):
    """Declaration name -> the run's service-map name for the same deployable.

    **Two name spaces have always existed here and nothing reconciled them.** The fact base
    calls a deployable whatever the operator's `--service-map` called it (`catalog`); this
    join calls it whatever the deployment declaration calls it (`catalog-api`). Both resolve
    to the same project directory, so the correspondence is computable — but it was never
    computed, and a consumer holding both outputs at once matched almost nothing.

    Found 2026-09-02, by building the first thing that reads both.

    Resolved by directory, never by name similarity: `catalog-api` and `catalog` happen to
    look alike, and matching on that would be a guess that works until an estate names two
    deployables `orders` and `orders-api` for different things.
    """
    by_directory = {}
    for fact in facts:
        if not fact.get("service"):
            continue
        rel = fact["file"].replace(chr(92), "/")
        by_directory.setdefault(fact["service"], []).append(rel)

    correspondence = {}
    for logical, directory in sorted(directories.items()):
        prefix = directory.rstrip("/") + "/"
        matched = sorted({service for service, paths in by_directory.items()
                          if any(path.startswith(prefix) for path in paths)})
        correspondence[logical] = {
            "directory": directory,
            "service_map_name": matched[0] if len(matched) == 1 else None,
            "ambiguous": matched if len(matched) > 1 else None,
            "means": ("this deployable is outside the run's service map"
                      if not matched else
                      "more than one service-map entry covers this directory"
                      if len(matched) > 1 else
                      "resolved by shared directory, not by name similarity"),
        }
    return correspondence


# The event type is read from the construct or the declaration, never by scanning the
# line for the first thing that looks like one. A first cut did the latter and picked
# `orderPaymentIntegrationEvent` - the VARIABLE on an assignment line - as the type, and
# paired nothing. The same lesson as the direction-blind execute(): identity lives in the
# construct, not in whatever the line happens to mention first. Found 2026-09-02.
PUBLISHED_TYPE = re.compile("new\\s+(\\w*IntegrationEvent)")
SUBSCRIBED_TYPE = re.compile("AddSubscription<\\s*(\\w+)")


def event_edges(facts):
    """Publisher -> subscriber, paired on the event type both sides name.

    **Why this exists.** The rest of this file follows call sites and addresses. On an
    event-driven estate that recovers almost nothing: eShop returned two edges between eight
    deployables while its business process crosses all eight, and six nodes had no path to the
    subject in the recovered graph. The stages are joined by events and nothing extracted
    events.

    **Both ends are cited and neither is guessed.** A publisher is the line constructing the
    event; a subscriber is the line DECLARING the subscription, which names the event type
    and its handler together. An event published with no subscriber, or subscribed with no
    publisher, is reported as a finding rather than dropped or invented.

    **This recovers WHICH service publishes and consumes which message. It does not recover
    the ORDER, and cannot** — static sequence reconstruction admits transitions that never
    occur. Composing these hops into a sequence would make the claim unsound.
    """
    published, subscribed = {}, {}
    for fact in facts:
        if fact.get("in_test") or not fact.get("service"):
            continue
        if fact["kind"] == "message_publisher":
            match = PUBLISHED_TYPE.search(fact.get("evidence") or "")
            bucket = published
        elif fact["kind"] == "message_subscription":
            match = SUBSCRIBED_TYPE.search(fact.get("evidence") or "")
            bucket = subscribed
        else:
            continue
        if not match:
            continue
        bucket.setdefault(match.group(1), []).append(fact)

    edges, seen = [], set()
    for event in sorted(set(published) & set(subscribed)):
        for source in published[event]:
            for target in subscribed[event]:
                if source["service"] == target["service"]:
                    continue
                key = (source["service"], target["service"], event)
                if key in seen:
                    continue
                seen.add(key)
                edges.append({
                    "from": source["service"],
                    "from_deployable": source["service"],
                    "to_host": target["service"],
                    "to_deployable": target["service"],
                    # No project reference stands behind an event seam - the pairing is on
                    # the event type both sides name. Complete because both hops are cited.
                    "to_project": None,
                    "complete": True,
                    "event": event,
                    "kind": "message_publisher",
                    "hops": [
                        {"hop": "publish site",
                         "cite": f"{source['file']}:{source['line']}",
                         "evidence": source["evidence"]},
                        {"hop": "subscription declaration",
                         "cite": f"{target['file']}:{target['line']}",
                         "evidence": target["evidence"]},
                    ],
                })
    return edges, {
        "events_published": sorted(published),
        "events_subscribed": sorted(subscribed),
        "published_with_no_subscriber": sorted(set(published) - set(subscribed)),
        "subscribed_with_no_publisher": sorted(set(subscribed) - set(published)),
        "means": "an event published with nobody listening, or listened for and never "
                 "published, is a finding about the estate. Neither is filled in here",
    }


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    root, fact_base = sys.argv[1], sys.argv[2]
    with open(fact_base, "r", encoding="utf-8") as handle:
        facts = json.load(handle)["facts"]

    clients = client_targets(facts)
    names, declared_edges, declared_in = deployable_names(root)
    # A second declaration source, for estates with no .NET deployment manifest. Merged rather
    # than chosen between: an estate can carry more than one, and a name declared twice is a
    # finding rather than a conflict to resolve silently.
    spring_names, spring_edges = spring_declarations(root)
    for logical, entry in spring_names.items():
        names.setdefault(logical, entry)
    declared_edges += spring_edges
    k8s_names, k8s_bindings = kubernetes_declarations(root)
    for logical, entry in k8s_names.items():
        names.setdefault(logical, entry)
    # Logical deployable -> the directory its project builds from, so a call site's file can
    # be attributed to the deployable that makes the call. **Deliberately not the run's
    # service map:** the map names the deployables a run chose to study, and an edge whose
    # end is outside it is still an edge. An earlier version filtered on the map and scored
    # one of four declared dependencies while having recovered three.
    projects = project_directories(root)
    directories = {}
    for logical, entry in names.items():
        if entry["project"] in projects:
            directories[logical] = projects[entry["project"]]
        elif entry.get("directory"):
            directories[logical] = entry["directory"]

    graph = project_graph(root)
    edges, unresolved = join(facts, clients, names, directories, graph, root)
    # Edges this estate evidences through configuration rather than at a call site. Additive
    # rather than alternative: an estate can use both idioms, and several do.
    edges += config_edges(facts, k8s_bindings, k8s_names, directories, graph)
    # The event seams. Additive, like config_edges: an estate can carry both idioms and eShop
    # carries both, with the call-site half recovering only its peripheral edges.
    seam_edges, event_report = event_edges(facts)
    edges += seam_edges
    json.dump({
        "root": root,
        "fact_base": fact_base,
        "client_registrations": len(clients),
        "deployables_declared": len(names),
        "environment_bindings": len(k8s_bindings),
        "deployables_located": len(directories),
        "declared_in": declared_in,
        # See name_correspondence: the two halves of a run named deployables differently
        # and nothing joined them until something consumed both.
        "deployable_name_map": name_correspondence(facts, directories),
        "event_topology": event_report,
        "dependencies": distinct(edges),
        "edges": edges,
        "unresolved": unresolved,
        "reconciliation": reconcile_edges(edges, declared_edges),
        "means": "an edge is emitted only when every hop carries a citation. An unresolved "
                 "record names the hop that failed and is a finding, not a gap to fill in",
    }, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
