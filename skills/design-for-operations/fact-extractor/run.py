"""Fact extractor — runs the rule set and emits a fact base.

Usage:  python run.py <source-root> [--service-map src/frontend=frontend ...]
Output: JSON on stdout.

This is the thin glue around Semgrep, which does the parsing. It does three things
Semgrep does not: attributes each fact to a deployable via the service map, normalises
the output to one fact shape, and counts by kind so a run can be compared with another.

Everything structural comes from `rules.yaml`. Nothing here reads source.
"""

import hashlib
import json
import os
import re
import subprocess
import sys

RULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules.yaml")
SEMGREP = os.environ.get("DFO_SEMGREP", "semgrep")


def parse_args(argv):
    if not argv:
        sys.exit(__doc__)
    root = argv[0]
    service_map = {}
    if "--service-map" in argv:
        for pair in argv[argv.index("--service-map") + 1:]:
            if pair.startswith("--"):
                break
            path, _, name = pair.partition("=")
            service_map[path.replace("\\", "/")] = name
    return root, service_map


def attribute(rel_path, service_map):
    """Longest matching prefix wins, so nested services beat their parents.

    The prefix must end at a path separator: a bare `startswith` lets the map entry
    `src/frontend` also claim `src/frontend-tests/` and `src/frontendlegacy/`, silently
    attributing another deployable's facts to this one. Attribution errors do not look like
    errors downstream — they look like a service doing more than it does.
    """
    best = None
    for prefix, name in service_map.items():
        boundary = prefix if prefix.endswith("/") else prefix + "/"
        if (rel_path == prefix or rel_path.startswith(boundary)) and (
                best is None or len(prefix) > len(best[0])):
            best = (prefix, name)
    return best[1] if best else None


_line_cache = {}


def source_line(path, start, end=None):
    """The cited source, trimmed. Read once per file, at the location the tool reported.

    Spans start..end rather than one line, because a match often begins above the thing
    that names it: a C# method's match starts at its `[AllowAnonymous]` attribute, so a
    single-line read misses the method name entirely. Measured — reconciling gRPC methods
    against their proto declarations reported GetBasket missing when it had been found.
    Capped so a large match body cannot swamp the record.
    """
    if path not in _line_cache:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                _line_cache[path] = handle.read().splitlines()
        except OSError:
            _line_cache[path] = []
    lines = _line_cache[path]
    last = min(end or start, start + 2, len(lines))
    if not 0 < start <= len(lines):
        return ""
    return " ".join(line.strip() for line in lines[start - 1:last])[:300]


TYPE_DECL = re.compile(
    r"^\s*(?:public|internal|private|protected|sealed|static|abstract|partial|\s)*"
    r"(?:class|record|struct|interface)\s+([A-Za-z_]\w*)")


def enclosing_type(path, line):
    """The type a fact sits inside, by scanning back to the nearest declaration above it.

    **Needed because a call site does not name what it calls.** An outbound call names a
    method on a receiver; the address it resolves to is registered somewhere else, against a
    type. Joining the two needs to know which type the call is in.

    Lexical and deterministic — a text scan at a tool-supplied location, the same operation
    `source_line` performs, with no inference. **Its limits are real and it is used
    accordingly:** it names the nearest preceding declaration, so a nested type wins over the
    type containing it, and a file with several types can attribute a call to whichever was
    declared last above it. The join treats the result as one hop that can fail, never as a
    fact in its own right.
    """
    if path not in _line_cache:
        source_line(path, 1)
    lines = _line_cache.get(path, [])
    for index in range(min(line, len(lines)) - 1, -1, -1):
        found = TYPE_DECL.match(lines[index])
        if found:
            return found.group(1)
    return None


# A rule earns its standing from accumulated evidence, and loses it to any wrong verdict.
# Deliberately NOT a flag someone clears: a queue of unratified rules has an owner problem
# with no good answer — a person will not work it, and the authoring agent clearing its own
# flag is self-grading. Standing is computed instead, so the hygiene is a byproduct of use.
ESTABLISHED_SAMPLES = 10
ESTABLISHED_ESTATES = 2


def tool_identity(rules_path):
    """Exactly what performed this run — name, version, rule-set fingerprint, invocation.

    Recorded because its absence cost half a day, and the way it cost it is the lesson.
    A fact base for one subject stopped reproducing between a morning run and an afternoon
    run, each stable on repeat. The rules looked byte-identical because they were compared
    against a stale checkout, so the difference was attributed to the analyser. It was not
    the analyser: a rule fix had landed between the two runs, removing a pattern that had
    been reporting a load generator's task decorators as the estate's background work. The
    delta was correct engineering.

    The fact base said only `tool: semgrep` — no version, no rule-set fingerprint — so
    there was nothing to attribute a change to and no way to tell a rule edit from an
    analyser change. **`rules_sha256` is the field that would have answered it in one
    step**, which is why it is here and why `contract.py --compare` reads it before it
    calls a disagreement non-determinism.
    """
    version = None
    try:
        version = subprocess.run([SEMGREP, '--version'], capture_output=True, text=True,
                                 timeout=60).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass
    fingerprint = None
    try:
        with open(rules_path, 'rb') as handle:
            fingerprint = hashlib.sha256(handle.read()).hexdigest()[:12]
    except OSError:
        pass
    return {
        "name": "semgrep",
        "version": version,
        "rules_file": os.path.basename(rules_path),
        "rules_sha256": fingerprint,
        "python": sys.version.split()[0],
        "means": "the analyser, its version and the exact rule set. A fact base that does "
                 "not carry these cannot be reproduced by anyone else, and a change in any "
                 "of them changes the answer",
    }


def multi_kind_report(facts):
    """Locations that produced more than one kind, disclosed rather than left to be found.

    A source line can legitimately do two things — `app.config[X] = os.environ.get(Y)` reads
    the environment and writes configuration; a call whose URL comes from config is both an
    outbound call and a configuration read. Forcing one kind would lose half of each.

    What is not legitimate is silence. Every count, coverage figure and tally downstream
    treats a fact as a countable unit, so an undisclosed double inflates all of them. Twice
    now a pair of rules has overlapped and nothing noticed: env_read against config_ref in
    C#, and env_read against poll_interval in Java. This block is what makes the third time
    visible on the run that produces it.
    """
    locations = {}
    for fact in facts:
        locations.setdefault((fact["file"], fact["line"]), set()).add(fact["kind"])
    doubled = {loc: sorted(kinds) for loc, kinds in locations.items() if len(kinds) > 1}
    pairs = {}
    for kinds in doubled.values():
        key = " + ".join(kinds)
        pairs[key] = pairs.get(key, 0) + 1
    return {
        "count": len(doubled),
        "by_kinds": dict(sorted(pairs.items(), key=lambda kv: -kv[1])),
        "examples": [f"{f}:{n}" for (f, n) in list(doubled)[:5]],
        "means": "a source line that produced two facts. Legitimate when the line genuinely "
                 "does two things; a rule-overlap defect when it does not. Disclosed either "
                 "way so a reader can tell, and so downstream counts can be corrected",
    }


def rule_fingerprints(rules_path):
    """A hash per rule of everything in it EXCEPT its evidence and its comments.

    Standing must not survive a change to what a rule matches. That was previously a
    discipline — "clear `checked:` when you edit the patterns" — and the docstring below
    called it the sharpest hole here, because nothing enforced it. This closes it: each
    `checked` entry carries the fingerprint of the rule it was drawn from, and an entry
    whose fingerprint no longer matches is discarded rather than counted.

    Comments are excluded so that explaining a rule does not void its evidence; the
    `checked:` lines are excluded so that recording evidence does not void it either.
    """
    blocks, current, lines = {}, None, []
    try:
        with open(rules_path, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("- id:"):
                    if current:
                        blocks[current] = lines
                    current, lines = stripped.split("- id:", 1)[1].strip(), []
                    continue
                if current is None or not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("checked:") or stripped.startswith("- {"):
                    continue
                lines.append(stripped)
        if current:
            blocks[current] = lines
    except OSError:
        return {}
    return {rule: hashlib.sha256(chr(10).join(body).encode()).hexdigest()[:12]
            for rule, body in blocks.items()}


def rule_standing(rules_path):
    """Per rule: its accumulated `checked:` evidence, and the standing that follows.

    A `checked` entry is appended by a precision pass — estate, date, how many facts were
    sampled at cited locations, how many a reader who did not author the rule judged correct.

    **Standing does not survive a change to what the rule matches.** Evidence is about the
    patterns that were sampled; narrow or widen them and it describes a rule that no longer
    exists. Carrying it forward would report a changed rule as vouched-for on a sample drawn
    from a different one — which is the substitution this whole mechanism exists to prevent,
    committed by the mechanism itself. **Editing a rule's patterns means clearing its
    `checked:` list in the same edit.** Nothing enforces that; it is the sharpest hole here.
    """
    fingerprints = rule_fingerprints(rules_path)
    evidence, voided, current = {}, {}, None
    try:
        with open(rules_path, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("- id:"):
                    current = stripped.split("- id:", 1)[1].strip()
                    evidence.setdefault(current, [])
                elif stripped.startswith("- {") and current:
                    # A list item under `checked:`, written as a JSON flow mapping so a line
                    # scanner can read it and YAML still parses it.
                    try:
                        entry = json.loads(stripped[2:])
                    except ValueError:
                        continue
                    # Evidence drawn from a rule that has since changed describes a rule
                    # that no longer exists. Discarded, and counted so the discard is
                    # visible rather than silent.
                    if entry.get("pattern_sha") != fingerprints.get(current):
                        voided[current] = voided.get(current, 0) + 1
                        continue
                    evidence[current].append(entry)
    except OSError:
        return {}

    standing = {}
    for rule, checks in evidence.items():
        sampled = sum(c.get("sampled", 0) for c in checks)
        correct = sum(c.get("correct", 0) for c in checks)
        estates = len({c.get("estate") for c in checks if c.get("estate")})
        if not checks:
            # Never sampled. Distinct from provisional, which means looked at and not yet
            # enough — conflating them would let "nobody has ever checked this" read as
            # "checked, in progress".
            state = "unchecked"
        elif correct < sampled:
            state = "quarantined"
        elif sampled >= ESTABLISHED_SAMPLES and estates >= ESTABLISHED_ESTATES:
            state = "established"
        else:
            state = "provisional"
        standing[rule] = {"state": state, "sampled": sampled, "correct": correct,
                          "estates": estates}
        if voided.get(rule):
            standing[rule]["voided_by_pattern_change"] = voided[rule]
    return standing


def standing_report(facts, standing):
    """How much of this run rests on rules that have not earned their standing.

    Reported on every run so the number is generated rather than remembered, and so nobody
    has to work a queue to find out.
    """
    tally, quarantined, provisional = {}, 0, 0
    for fact in facts:
        rule = fact["rule"].split(".")[-1]
        state = standing.get(rule, {}).get("state", "unchecked")
        tally.setdefault(state, {"facts": 0, "rules": set()})
        tally[state]["facts"] += 1
        tally[state]["rules"].add(rule)
        quarantined += state == "quarantined"
        provisional += state in ("provisional", "unchecked")
    return {
        "thresholds": {"samples": ESTABLISHED_SAMPLES, "estates": ESTABLISHED_ESTATES},
        "by_state": {k: {"facts": v["facts"], "rules": sorted(v["rules"])}
                     for k, v in sorted(tally.items())},
        "facts_on_quarantined_rules": quarantined,
        "facts_not_yet_established": provisional,
        "per_rule": standing,
        "means": "a rule is established by accumulated precision evidence, never by anyone "
                 "clearing a flag. `unchecked` means no precision pass has sampled it yet; "
                 "`quarantined` means a sampled fact was judged wrong and the pattern needs "
                 "narrowing before its facts are used.",
    }


def provisional_report(facts, rules_path):
    """Rules authored during a run and not yet ratified, and how much rests on them.

    **This block was documented before it existed.** `README.md` printed its shape and said
    the announcement is generated rather than remembered; nothing generated it, so an
    authored rule entered the library in silence — the precise failure the announcement was
    written to prevent. Found and closed 2026-09-01 while authoring one.

    A rule declares itself with `provisional: true` in its metadata, alongside the estate and
    date that produced it. It stops being provisional when someone rules on it, not when a
    run stops noticing.
    """
    marked, current = set(), None
    try:
        with open(rules_path, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("- id:"):
                    current = stripped.split("- id:", 1)[1].strip()
                elif stripped.startswith("provisional:") and current:
                    if stripped.split(":", 1)[1].strip().lower() == "true":
                        marked.add(current)
    except OSError:
        return {}
    resting = sum(1 for f in facts if f["rule"].split(".")[-1] in marked)
    return {
        "provisional_rules_in_library": sorted(marked),
        "facts_resting_on_them": resting,
        "means": "these facts come from rules authored during a run and not yet ratified. "
                 "They belong in the ratification queue, not in the accepted output",
    }


ENTRY_KINDS = {"inbound_route", "message_consumer", "background_trigger"}
WORK_KINDS = {"durable_write", "durable_read", "outbound_http"}


TEST_PATH = re.compile(
    r"(^|/)(tests?|testing|spec|specs|e2e|integration-tests?|__tests__|cypress|"
    r"functionaltests?|unittests?)(/|$)", re.IGNORECASE)
TEST_FILE = re.compile(
    r"(_test\.go|\.test\.[jt]sx?|\.spec\.[jt]sx?|Test\.java|Tests\.cs|Test\.cs|"
    r"test_[^/]*\.py|[^/]*_test\.py|playwright\.config\.[jt]s|conftest\.py)$")


def in_test(rel_path):
    """Whether a fact comes from test or CI code rather than from the running system.

    **A capability the superseded script had and the rebuild lost.** Its join skipped facts
    marked this way; nothing here did, and a rule authored on one estate immediately picked up
    eight environment reads from another's end-to-end test configuration — true statements
    about files that never run in production.

    Marked rather than dropped. A test names real endpoints and real environment variables, so
    it is evidence about the system; it is just not part of it. Which of those a consumer wants
    is the consumer's call, and it cannot make that call if the distinction was thrown away
    before the fact reached it.
    """
    return bool(TEST_PATH.search(rel_path) or TEST_FILE.search(rel_path))


SOURCE_SUFFIXES = {
    ".java", ".cs", ".py", ".go", ".ts", ".js", ".rb", ".php", ".kt", ".scala", ".rs",
    ".cpp", ".c", ".sh", ".sql", ".yaml", ".yml", ".tf", ".xml", ".json",
}


def reach(facts, service_map, root):
    """What the run was pointed at versus what any rule actually read.

    **This is the control that catches a confidently empty result**, and it was built after
    one: on a polyglot estate, six of eleven declared deployables produced zero facts because
    they are written in a language no rule covers, and every other self-check passed. The
    consistency check below cannot see it — a deployable with no work and no entry point
    satisfies *work implies entry point* perfectly, so being entirely unread looks identical
    to being simple.

    Two questions, both answered from the run rather than from anyone's memory:
    **which declared deployables produced nothing**, and **which source file types are present
    in the tree that no fact came from.** A run that is silent on either is a run whose
    emptiness cannot be told apart from an estate's simplicity.
    """
    with_facts = {f["service"] for f in facts if f["service"] and not f["in_test"]}
    silent = sorted(set(service_map.values()) - with_facts)

    # **How much source each silent deployable has, because that is what separates the two
    # cases.** A deployable with a dozen lines and no facts is a thin launcher whose behaviour
    # is all framework — Spring Cloud's config, discovery and admin servers are two annotations
    # and a `main`, and zero facts is the right answer. A deployable with thousands of lines
    # and no facts was not read. The check cannot tell them apart; this number can, and without
    # it every silent deployable costs someone a manual look.
    sizes = {}
    for prefix, name in service_map.items():
        if name not in silent:
            continue
        total = 0
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, prefix)):
            dirnames[:] = [d for d in dirnames if d not in {".git", "target", "build", "obj",
                                                            "bin", "__pycache__", ".venv"}]
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() in SOURCE_SUFFIXES:
                    try:
                        with open(os.path.join(dirpath, filename), "r",
                                  encoding="utf-8", errors="replace") as handle:
                            total += sum(1 for line in handle if line.strip())
                    except OSError:
                        pass
        sizes[name] = total

    present, read = {}, {f["file"].rsplit(".", 1)[-1] for f in facts if "." in f["file"]}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in {".git", "node_modules", "target", "build", "obj", "bin",
                                    "__pycache__", ".venv", "vendor"}]
        for name in filenames:
            suffix = os.path.splitext(name)[1].lower()
            if suffix in SOURCE_SUFFIXES:
                present[suffix] = present.get(suffix, 0) + 1
    unread = {suffix: count for suffix, count in present.items()
              if suffix.lstrip(".") not in read}

    return {
        "deployables_declared": len(set(service_map.values())),
        "deployables_with_facts": len(with_facts & set(service_map.values())),
        "deployables_with_no_facts": silent,
        "source_lines_in_silent_deployables": dict(
            sorted(sizes.items(), key=lambda kv: -kv[1])),
        "file_types_present_that_no_rule_read": dict(sorted(
            unread.items(), key=lambda kv: -kv[1])[:12]),
        "complete": not silent,
        "means": "a declared deployable with no facts is not a simple deployable. It is one "
                 "nothing read — an unsupported language, a missed scan root, or an idiom no "
                 "rule covers — and the output for it is empty rather than sparse. A run must "
                 "say which, and never present the remainder as the estate",
        "how_to_read_the_silent_list": "the source-line count separates the two cases. A few "
                 "dozen lines is a thin launcher whose behaviour is all framework, and zero "
                 "facts is the right answer for it. Hundreds or thousands of lines with zero "
                 "facts means nothing read it, and the run is missing that deployable "
                 "entirely — open it before reporting anything about this estate",
    }


def coverage_warnings(facts):
    """Internal consistency check on the extraction itself.

    A service that writes durable state or calls another service is doing work, and
    work is initiated by something. If no entry point of any kind was extracted for
    it, the extraction is incomplete for that service — the code did not stop having
    an entry point, the rules stopped modelling its idiom.

    Detects total absence per service. It does NOT detect partial under-extraction,
    and that is its known limit: on the .NET reference estate the basket service has
    three unmodelled gRPC entry points and still satisfies this predicate through one
    message consumer. Verified against a real defect: on the pre-fix run of that
    estate it flagged 7 of 8 services, every one of them genuinely under-read.
    """
    per_service = {}
    for fact in facts:
        counts = per_service.setdefault(fact["service"], {})
        counts[fact["kind"]] = counts.get(fact["kind"], 0) + 1

    warnings = []
    for service, counts in sorted(per_service.items(), key=lambda kv: (kv[0] is None, kv[0])):
        work = sum(counts.get(k, 0) for k in WORK_KINDS)
        entries = sum(counts.get(k, 0) for k in ENTRY_KINDS)
        if work > 0 and entries == 0:
            warnings.append({
                "service": service,
                "finding": "no entry point extracted for a service that performs work",
                "work_facts": work,
                "means": "an unmodelled entry-point idiom, not a service without entry points",
            })
    return warnings


def main():
    root, service_map = parse_args(sys.argv[1:])
    proc = subprocess.run(
        [SEMGREP, "--config", RULES, "--json", "--quiet", "--metrics=off", root],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 and not proc.stdout:
        sys.exit(f"semgrep failed ({proc.returncode}):\n{proc.stderr[-2000:]}")

    report = json.loads(proc.stdout)
    # **A rule file the engine could not load is fatal, not a result.** Measured 2026-09-01:
    # one invalid escape inside a regex made the whole file unparseable, and the run reported
    # zero facts for an entire estate with no error — an empty output that reads exactly like
    # a system with no structure. The engine says so in `errors`; nothing was reading it.
    fatal = [error for error in report.get("errors", [])
             if error.get("level") == "error"
             and "PartialParsing" not in str(error.get("type"))]
    if fatal:
        sys.exit("the rule file did not load, so this run read nothing. Fix it and re-run "
                 "rather than treating the empty output as a finding:\n"
                 + "\n".join(str(error.get("message", error))[:400] for error in fatal[:3]))
    facts, counts, by_language = [], {}, {}
    root_abs = os.path.abspath(root)

    for hit in report.get("results", []):
        abs_path = os.path.abspath(hit["path"])
        rel = os.path.relpath(abs_path, root_abs).replace("\\", "/")
        kind = hit["extra"]["metadata"]["fact_kind"]
        ext = os.path.splitext(rel)[1]
        facts.append({
            "kind": kind,
            "service": attribute(rel, service_map),
            "file": rel,
            "line": hit["start"]["line"],
            # Semgrep namespaces a rule id with the filesystem path of the rules file,
            # so the raw check_id embeds the operator's local directory tree. That leaks
            # a path into every fact of an output that gets handed over, and it makes two
            # runs of the same subject on different machines incomparable. The internal
            # accounting already reads only the last segment; the emitted fact must match.
            "rule": hit["check_id"].split(".")[-1],
            # The cited source line, read from disk at the location the tool reported. This is
            # what gives a fact identity: without it a fact is a coordinate, and a coordinate
            # can only be counted, never matched against an independently declared population.
            # Reading a line at a tool-supplied location is deterministic; nothing is inferred.
            "evidence": source_line(abs_path, hit["start"]["line"], hit.get("end", {}).get("line")),
            # The type this fact sits inside. Not a claim about behaviour — a coordinate the
            # join needs, because a call site never names the service it reaches.
            "in_type": enclosing_type(abs_path, hit["start"]["line"]),
            # Test and CI code is evidence about the system, not part of it.
            "in_test": in_test(rel),
        })
        counts[kind] = counts.get(kind, 0) + 1
        by_language[ext] = by_language.get(ext, 0) + 1

    facts.sort(key=lambda f: (f["file"], f["line"], f["kind"]))
    json.dump({
        "root": root,
        "tool": tool_identity(RULES),
        "rules": os.path.basename(RULES),
        "counts": counts,
        "by_language": by_language,
        "unattributed": sum(1 for f in facts if f["service"] is None),
        "in_test": sum(1 for f in facts if f["in_test"]),
        "reach": reach(facts, service_map, root),
        "multi_kind_locations": multi_kind_report(facts),
        "coverage_warnings": coverage_warnings(facts),
        "rule_standing": standing_report(facts, rule_standing(RULES)),
        "provisional": provisional_report(facts, RULES),
        # Files the parser could not fully read. Facts inside those regions are absent
        # and unrecoverable, so this count bounds every claim the run makes.
        "partial_parse_files": len({
            loc.get("path")
            for err in report.get("errors", [])
            for loc in (err.get("type") or [None, []])[1] or []
            if isinstance(loc, dict)
        }),
        "semgrep_errors": report.get("errors", []),
        "facts": facts,
    }, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
