# Fact extractor

**What this is.** The tool that performs the structure-extraction step of design for operations:
read source, emit structural facts, each carrying a file and line so a person can check it without
trusting a model. In the field's own vocabulary this is a **fact extractor** producing a **fact
base** — phases 1 and 2 of software architecture reconstruction (SEI). The join beside it is phase
3, view fusion: turning facts into edges between deployables.

**It is a reference implementation, not the answer.** Phase 1 of the method is a contract, and any
tool that satisfies it can perform the phase. If your organisation already owns a code-analysis
tool, read `../INTEGRATION.md` — it states what the socket requires and how to score a substitute.

## What performs it

**Semgrep** does the parsing and matching. `rules.yaml` holds the fact definitions — one rule per
fact kind per language, each tagged `metadata.fact_kind`. `run.py` is thin glue: it invokes
Semgrep, attributes each fact to a deployable via the service map, and normalises the output.
**Nothing here reads source.** Adding a language or a framework means adding rules, not code.

Why Semgrep rather than the alternatives, in one line each: the target languages are all supported
by one rule language; **it needs no compiling build** (CodeQL does, for Java and C#, which on a
legacy estate is a project rather than a step); its output already carries path and line, so the
citation requirement is met by the tool instead of by our discipline; and the free engine needs no
procurement to start.

## Running it

```
pip install semgrep

python run.py      <repo-root> --service-map src/a=a src/b=b ... > fact-base.json
python coverage.py <repo-root> fact-base.json                    > coverage.json
python join.py     <repo-root> fact-base.json                    > join.json
python contract.py <repo-root> fact-base.json                    # conformance, exit 0/1
```

**Two rules decide whether any of it works.** The scan root is the repository root, never a
subdirectory — service-map keys are repo-root-relative, so a `src/` root makes every one of them
miss without an error. And a service map is required, one `<source-path>=<deployable-name>` pair
per deployable; without it the join returns nothing, and an empty result reads like a finding
rather than a mistake. A load generator or a test harness is not a deployable and does not belong
in the map.

**A fact with `service: null` is not a defect.** It is a file outside the service map, reported so
the map's coverage is visible rather than assumed. A fact with `in_test: true` came from test
code, which is evidence about the system and not part of it; downstream phases exclude it.

## What the output carries

Each fact: `kind`, `service`, `file`, `line`, `evidence` (the source text at that location),
`rule`, `in_type` (the enclosing type, which the join needs), `in_test`.

The kinds: `inbound_route`, `outbound_http`, `grpc_method`, `grpc_call`, `message_consumer`,
`message_producer`, `message_publisher`, `message_subscription`, `durable_read`,
`durable_write`, `repo_decl`, `env_read`, `config_ref`, `background_trigger`, `poll_interval`,
`client_binding`.

At the top level, the blocks a reader should open before trusting any count:

| Block | What it says |
|---|---|
| `tool` | The analyser's name and version, and `rules_sha256`, a fingerprint of the rule set. Two fact bases that differ here differ because the question changed, not because the answer is unstable |
| `reach` | Every declared deployable that produced no facts, with how much source it holds, and every file type present in the tree that no fact came from. `complete: false` means the run did not read the estate |
| `partial_parse_files` and `semgrep_errors` | Files the parser could only partly read. Facts inside the unparsed regions are silently absent; a run must state the count rather than treat the output as complete |
| `rule_standing` | Each rule's standing — `unchecked`, `provisional`, `established`, `quarantined` — computed from recorded precision evidence, with the number of facts resting on it. **Read this rather than any prose about which rules are trustworthy** |
| `provisional` | Rules authored during a run and not yet ratified, and the facts resting on them |
| `multi_kind_locations` | Lines that legitimately carry two kinds (a line can read the environment *and* bind a client). Disclosed so downstream tallies do not double-count silently |

## The reach check — what the run was pointed at versus what anything read

Built after a run passed every other check while reading less than half its estate: on a polyglot
subject, six of eleven declared deployables produced zero facts because most of the estate was
written in a language no rule covered, and nothing said so. **Being entirely unread looks exactly
like being simple.** Every run now reports the silent deployables and the unread file types, and
marks itself incomplete when there are any.

A thin launcher — a Spring Cloud config or discovery server is two annotations and a `main` — is
correctly silent. Thousands of lines and no facts means nothing read it. The skill says what to do
in each case.

## The coverage check — recall, where the estate declares a population

`coverage.py` reconciles the fact base against populations the repository already declares about
itself: service methods in `.proto` definitions, HTTP operations in OpenAPI documents. **Matching
is by name at a cited location, never by totals** — two counts agreeing proves nothing; each
declared item is looked for individually, and an unmatched one is named.

It runs two controls, and a failure in either invalidates the report:

- **The decoy control — things that must NOT match**, built from the subject's own declarations
  with the final segment of each replaced by a token not in the estate. A matcher that accepts
  everything fails it.
- **The matcher control — things that must MATCH**, fixed cases taken from real source shapes: a
  route-group prefix, a route constraint, an optional parameter, a bare attribute with no path. A
  matcher that rejects everything fails it. This is the control whose absence once let a
  too-strict matcher pass as healthy while reporting real operations as missing.

**The ceiling is structural, and the output says so in those words.** No estate declares
everything, and each declares something different — one ships protocol definitions and OpenAPI,
another ships SQL schema, another ships Kubernetes manifests. Message consumers, background
triggers and outbound calls have no declarative source in any subject seen so far; their recall is
**unmeasured**, which is not the same as passing, and the internal consistency check is the only
floor under them: a service that writes durable state or calls out but shows no entry point has
an unmodelled idiom, not an absent entry point. That check detects total absence per service, not
partial under-extraction — a service can be substantially under-read and pass.

## Rule standing — precision, by a reader who did not write the rules

**A rule is not trusted because someone marked it trusted.** Its standing is computed from
precision evidence recorded against it, and reported on every run:

| State | Meaning |
|---|---|
| `unchecked` | No precision pass has ever sampled it |
| `provisional` | Sampled, evidence still thin |
| `established` | Ten samples across two estates, none judged wrong |
| `quarantined` | A sampled fact was judged wrong. The pattern needs narrowing before its facts are used |

**Nobody clears a flag, and no queue needs working** — a person will not work a ratification queue
of rules, and an agent clearing its own flag is self-grading. The loop that feeds standing:

```
python precision.py <root> <fact-base.json> 3        > worksheet.json   # draw a stratified sample
#  a reader who did NOT author the rules adds "verdict": correct|wrong|unclear to each item
python precision.py --record worksheet.json <estate> > entries.txt      # emit the evidence lines
#  paste each line into that rule's metadata.checked: block in rules.yaml
```

`--record` refuses a worksheet with any item unjudged, and counts `unclear` as sampled-and-not-
correct: a fact a reader could not confirm has not been confirmed.

**Evidence expires when the pattern changes.** Each recorded sample carries a fingerprint of the
rule it was drawn from; edit the pattern and the entry is discarded and counted as
`voided_by_pattern_change`. Enforced in `run.py`, not by convention — widening a rule by one
pattern drops it from `established` to `unchecked` with nobody editing its evidence. Standing has
to be earned again after every edit, and that is the mechanism working.

**What the readers found, and it is one defect repeated:** every wrong fact came from a rule that
matched a **name or a signature and never checked what it was attached to** — an in-memory
append filed as a database write, a repository call filed as a network hop, a load generator's
task decorators filed as the estate's background work, a `SELECT` filed as a write because the
call site cannot say the statement's direction. The error is directional: cheap operations get
promoted into expensive claims, which **inflates the business process map rather than thinning
it**, so the monitoring it argues for would be placed on things that are not there.

## Rules authored during a run announce themselves

A run that meets a language nobody wrote rules for, and works it out, should both update the
library and say so. Writing a rule back silently is self-modification with the run as its only
witness. So an authored rule enters the library marked `provisional: true`, carrying the estate
and date that produced it and what it was checked against, and `run.py` counts every fact resting
on an unratified rule and reports it in `provisional` on **every** run — the announcement is
generated, not remembered.

**Why it matters more than it looks.** A rule verified on one estate becomes a **silent default on
the next**, and what transfers is coverage, not correctness: opening its matches here proves it
matched the right things *here*. An authored rule is a ratification item, not a commit. It stops
being provisional when someone rules on it.

## What this covers, and what it cannot reach — stated in three tiers

**Tier 1 — covered, and narrower than the language list implies.** C#, Java, Python, Go and
JavaScript/TypeScript, **and only the framework idioms someone wrote a rule for**: Spring, Flask,
ASP.NET controllers and minimal APIs, gRPC, Entity Framework, integration-event handlers, hosted
background workers, Express, Go's standard HTTP and gRPC. A team's own conventions inside those
languages are unmodelled until measured. Coverage is per rule, not per language, and `rule_standing`
says which rules have been judged against source.

**Tier 2 — reachable but unwritten.** The parser handles roughly thirty languages. These initiate
work and no rule reads them:

| Not read | Why it initiates business process work |
|---|---|
| Shell scripts | A script on a schedule starts work as surely as an endpoint does |
| Dockerfiles and container entrypoints | Declares what actually starts when a deployable runs |
| Enterprise scheduler definitions (Autosys, Control-M, Tivoli) | Batch is where a great deal of financial-services work runs |
| Other service languages — Kotlin, Scala, Ruby, PHP | Parseable; no rules written |
| Infrastructure declarations (Terraform, HCL) | Dependencies that sit in no business process sequence and can stop one dead |

Each is a bounded piece of work with the usual caveat: writing the rule is cheap, knowing it is
complete is not.

**Tier 3 — not read here.**

| | |
|---|---|
| **Mainframe** — COBOL, CICS | Out of scope. Declined, not worked around |
| **Stored procedures** — SQL, PL/SQL | Not read by this tool. In scope, unbuilt |
| **Vendor and packaged applications** | Genuinely unreachable — no source exists to read |

**Where the extractor cannot reach, sources compose** — runtime evidence, a stated architecture,
the industry reference model, or people. This extractor is one source. A run whose only source is
this tool inherits exactly the boundary above, and should say so in its framing rather than
discovering it at the end.

## The join — turning facts into edges

**A separate program on purpose.** Extracting facts is a solved, purchasable step; joining them
across repositories is estate-specific and is the part that is legitimately ours. A fact base is
vertical — what each deployable does, one cited line at a time. Nothing in it says which deployable
calls which. Every question this method answers is horizontal, so the edges are the deliverable and
the facts are the input to it.

**A call site names a method on a receiver. It never names the service it reaches.** The address
lives somewhere else entirely, so an edge is four hops:

| Hop | From | Read at |
|---|---|---|
| 1 | The outbound call | the call site, cited |
| 2 | The type it sits in | to the client registration that carries the address |
| 3 | The address literal | to a logical deployable name |
| 4 | The logical name | to the project it runs, and the directory that project builds from |

**An edge is emitted only when every hop carries a citation.** Anything short of that becomes an
`unresolved` record naming the hop that failed. A guessed edge is worse than an absent one: it
puts monitoring on a dependency that is not there.

**A call site does not have to live in a deployable.** A shared library's call is attributed to
every deployable whose project references it, following the project reference graph rather than
the directory tree. A library referenced by several deployables yields an edge for each, which is
correct rather than duplicated — each of them ships that call.

**Where the address lives is a property of the framework**, so the join tries four resolvers in
order and names the one that worked in the edge's hops:

| Where the address is | Looks like | Seen on |
|---|---|---|
| The call's own URI literal | `…uri("http://customers-service/owners/{id}")` | Spring |
| A field the same file initialises | `…uri(hostname + "pets")` with `hostname = "http://visits-service/"` above | Spring |
| A typed-client registration | `AddHttpClient<CatalogService>(o => o.BaseAddress = new("https+http://catalog-api"))` | .NET |
| A manifest binding an environment variable | `@Value("http://${BALANCES_API_ADDR}/balances")` with `BALANCES_API_ADDR: "balancereader:8080"` in a ConfigMap | Kubernetes |

The Kubernetes one is the enterprise case: the address leaves the programming language entirely.
Where an estate binds the same variable to two mutually exclusive topologies, the edges are marked
`ambiguous_config` and neither topology is silently preferred. A dependency whose far end nothing
declares is admitted only when the same variable also resolves to a declared deployable — that
co-occurrence is what distinguishes a service address from a database host or an external URL.

**Event seams.** On an event-driven estate the business process does not cross services over
HTTP; it crosses at the broker. The join pairs a publish site in one service with a subscription
declaration in another on the event type name, both cited. That recovers *which* service publishes
and consumes which message. **It never recovers the order** — every consumer of an event is a
possible successor, and a branch is indistinguishable from an alternative.

**What the join does not do.**

- **Database dependencies are not recovered.** Repository declarations are in the fact base, but
  the hop from a service to the database deployable it writes is not built; the acceptance
  harness reports it as such.
- **Durable-state seams** — a write in one service joined to a read of the same state in another —
  are not built.
- **`in_type` is lexical.** It names the nearest type declaration above a line, so a nested type
  wins over the type containing it. It is one hop that can fail, never a fact.
- **Templated manifests are read as written.** Helm and Kustomize overlays are not rendered, so an
  unrendered placeholder stays a placeholder and its hop fails visibly rather than silently.

The join's own `reconciliation` block scores it against the dependencies the deployment
declaration states, where one exists. Read the independence caveat in the output before treating
that as a score: the name resolution the join needs and the dependencies it is checked against can
come from the same file.

## Conformance — is a fact base the shape the method needs

`contract.py` runs ten checks against a fact base and the source it claims to describe: shape, the
closed vocabulary of kinds, path hygiene, the reach block, identifiers free of filesystem paths,
multi-kind locations disclosed — and the one that matters, **it opens a sample of cited locations
and confirms the evidence is actually there.** Exit 0 or 1, with the specific failures named.

```
python contract.py <root> <run-a.json> --compare <run-b.json>
```

reads the tool and rule-set fingerprints **before** calling a disagreement non-determinism. A
different rule set means a changed answer, not an unstable one.

## Limits stated so nobody has to find them

- **Semgrep's C# parser fails on primary constructors** (a C# 12 feature). A partial parse loses
  the construct that failed, not the file: a rule keyed on the failing construct misses, a rule
  keyed on anything else in the same file succeeds. The count is in `partial_parse_files`.
- **Recall is measurable only where the estate declares a population.** Everything else is
  unmeasured and reported as such.
- **Precision comes from reader sampling, and standing is per rule.** No language is "covered";
  rules are.
- **Every subject so far is a reference application** — small, coherent, built to be readable.
  Nothing here says how this behaves on a system carrying several teams' conventions.
- **Rules have no fixture tests.** Each rule should carry a fixture file with expected match lines;
  a fixture set is what would catch the next defect before a run does.
- **The fact base has no interchange format.** Output is this tool's own JSON. The field ships
  formats for exactly this — RSF, TA, GXL — and adopting one would be better than inventing a
  schema.

## Three rule-writing traps, so they are not rediscovered

1. **A bare Java annotation is not a standalone pattern.** `@Async` alone fails to parse; it must
   be attached to the declaration it decorates.
2. **A C# attribute is matched without its brackets.** `HttpGet(...)` matches both `[HttpGet]` and
   `[HttpGet("{id}")]`. `[HttpGet]` as a pattern matches nothing.
3. **A count that looks right can be wrong.** `[$A]` returned six matches on a controller with six
   attributes — and they were array-indexing expressions on entirely different lines. Confirm by
   opening the cited lines, never by the count.
