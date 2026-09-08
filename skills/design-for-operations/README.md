# Design for Operations

**Work out what a business process flow actually does, which code implements each part of it, and
what could be watched — from source you can read, with a file and line under every mechanical
claim.**

The problem this addresses is the precondition that business activity monitoring assumes and rarely
has: a known, instrumentable business process. Where architecture documentation has drifted and the
people who built the system have moved on, that precondition does not hold, and this recovers it.

## What you get

One specification document per business process flow. It says, stage by stage: what the business
calls it, what runs it, and whether anyone could tell if it broke.

A complete worked example is in [`example/PLACING-AN-ORDER.md`](example/PLACING-AN-ORDER.md) — the
customer ordering journey through Microsoft's `dotnet/eShop` reference application, twelve stages,
every code reference resolving to a file and line.

**What that example found is the point.** Two of the twelve stages are present in structure and
hollow in function: the payment step decides its outcome by reading a configuration setting, so
nobody is ever charged, and the shipping endpoint works but nothing in the system calls it. Every
automated check on that run passed while both sat there. A topology diagram shows them as ordinary
working services, and a success rate placed on the payment step would measure a config flag.

## What is in the package

| | |
|---|---|
| `SKILL.md` | The instrument — nine phases, for a coding agent to run |
| `INTEGRATION.md` | **Read this to fit your own extractor.** What Phase 1 must emit, the guarantees it must carry, and how to score the fit |
| `fact-extractor/` | The structure extraction: Semgrep rules, a runner, a coverage reconciliation, a join, a precision sampler and a conformance check |
| `adapter/` | Turns a run into a dependency graph and an ordered business process, in the format stated at the top of `adapter/adapter.py`, so a service can be onboarded with no prose source material |
| `acceptance/` | Scores a candidate extractor against a subject whose answer was hand-derived twice |
| `reference/` | The method, and the target it aims at |
| `JUDGING-INSTRUMENT.md` | The seven conditions a run is scored against |
| `example/` | One complete run: the specification, its score, its ratification queue, its verification report, the working paper that carries its citations, and the stages file the adapter reads |
| `verify/` | The recorded fact base an install is checked against |

## It does two jobs

**Run it.** *"Run design for operations on this repository."* The agent works the nine phases and
produces the specification — the business process flow stage by stage, each stage bound to code
with a file and line, what signal could be produced for each, and what cannot be seen. Plus a
ratification queue: every drafted position, grouped by the role whose yes it needs.
[`example/PLACING-AN-ORDER.md`](example/PLACING-AN-ORDER.md) is what that output looks like.

**Extend it.** *"Make our own analysis tool perform Phase 1."* The extractor here is a reference
implementation, not the answer — if your organisation already owns a code-analysis tool it will
read languages these rules do not. [`INTEGRATION.md`](INTEGRATION.md) states what the socket
requires, and two commands score the fit:

```
python fact-extractor/contract.py <source-root> <fact-base.json>   # does it conform        -> exit 0/1
python acceptance/accept.py <join-output.json>                     # does it find the seams -> exit 0/1
```

**Both return a verdict, not a view.** That is deliberate. Instructions alone would make a
substitution a matter of opinion — *"I integrated it, it looks good"* — which nobody at a distance
can judge. The checks are what let someone report *"conforms: false, C4 citation integrity, 12
evidence mismatches"* instead.

## Requirements

- **Python 3.9+** (verified on 3.12)
- **Semgrep** — `pip install semgrep` (verified on 1.176, native Windows, no WSL needed)
- **Git**, to clone the subject
- **A coding agent that loads skills.** This directory is a skill in the open `SKILL.md` format.
  For GitHub Copilot in VS Code, place it at `.github/skills/design-for-operations/`; any other
  agent that reads that format loads it from its own skills directory. The agent invokes it; the
  Python beside it is what the skill tells the agent to run
- **On Windows, clone the subject to a short path** such as `C:\src\`. Deep paths hit the
  260-character limit and the checkout fails part-way, leaving a repository that looks cloned and
  is missing files

## Verify the install before trusting a run

This reproduces a recorded result exactly. If your numbers differ, stop and find out why.

```
git clone https://github.com/dotnet/eShop.git eshop-dotnet
cd eshop-dotnet && git checkout b4a40872005d4bb29e5b1fa1ff7e244143d39215 && cd ..

python fact-extractor/run.py eshop-dotnet --service-map \
  src/Basket.API=basket src/Catalog.API=catalog src/Ordering.API=ordering \
  src/Identity.API=identity src/Webhooks.API=webhooks src/PaymentProcessor=payment \
  src/OrderProcessor=orderprocessor src/WebApp=webapp > fact-base.json

python fact-extractor/coverage.py eshop-dotnet fact-base.json > coverage.json
python fact-extractor/join.py     eshop-dotnet fact-base.json > join.json
python adapter/adapter.py         fact-base.json join.json example/stages.json > onboarding-blocks.json
```

Takes about 90 seconds. Expect exactly:

| | |
|---|---|
| Facts | **211** — `inbound_route` 48, `outbound_http` 28, `durable_write` 27, `durable_read` 25, `message_consumer` 18, `message_subscription` 18, `config_ref` 13, `event_binding` 13, `env_read` 9, `message_publisher` 6, `client_binding` 5, `background_trigger` 1 |
| Reach | **`complete: false`**, with the two reasons stated: 946 lines of JavaScript in 14 files that no rule reads, and 46 files the parser could not fully read. All 8 declared deployables produced facts. This is the correct answer for this subject — see below |
| Recall | **1.0** on gRPC methods (3 of 3) and **1.0** on HTTP operations (16 of 16), against the counts the repository declares about itself (your `coverage.json`, from the run above) |
| Controls | Both pass — the decoy control (fabricated routes must not match) and the false-negative control (known implementations must be recognised) |
| Join | **20 edges**, 11 unresolved, 3 of the 4 dependencies the deployment file declares. **3 event types published against 13 subscribed** — ten subscriptions have no publisher the tool could locate, and it says so rather than pairing them |
| Adapter | **8 nodes, 5 edges, 12 stages** |
| Conformance | Ten checks pass. The eleventh, determinism, needs `--compare` — the command below |

**Two of those numbers look like failures and are not.**

`reach.complete` is `false` because the run names two things it did not read. A run that read part
of an estate and reported nothing missing would be worse, not better: the unread part would be
indistinguishable from a part that holds nothing. On this subject some of it genuinely went
unread, and the block says which.

The event graph is sparse for a related reason. An earlier version of the C# publisher rule
matched where an integration event is **constructed** rather than where it is sent. It produced
thirteen publishes on this estate and paired every one of the thirteen subscriptions — and a
precision sample judged it wrong about what the line does in every case it opened. The rule now
matches the broker send. It finds six, a sample judged four of those six correct, and that verdict
holds it in quarantine, so its facts are reported and labelled rather than treated as settled. Ten
subscriptions with no located publisher is what reading this estate statically actually supports.
The denser graph was not the better answer.

Then let the conformance check compare your fact base with the recorded one. It reads the tool
and rule-set fingerprints first, so a different rule set is reported as a changed answer rather
than as instability:

```
python fact-extractor/contract.py eshop-dotnet fact-base.json --compare verify/fact-base.json
```

`verify/fact-base.json` is regenerated whenever the rule set changes and should match your run
except for recorded file paths. The example run in `example/` was made with an earlier rule set
and reports its own, lower counts.

## What the adapter is for

A run produces a specification. **The adapter turns it into two structured blocks** — the
dependency graph and the ordered business process, in the format stated at the top of
`adapter/adapter.py` — so a service can be onboarded from recovered evidence rather than from
prose somebody has to trust. Map those fields into whatever onboarding format you use. The adapter
checks its own output: every step's components name nodes in the graph, and it refuses to emit a
step or a node it cannot back.

**Two things it deliberately refuses to do.** It will not invent a dependency to make a graph
connect, and it will not state what happens when a service fails. Every node it emits says so in
that field, because no line of source states a failure consequence and a plausible sentence there
would be a fabrication.

**On an event-driven estate the dependency graph comes mostly from event seams**, not call sites: a
publisher and the subscription that declares the same event type, both cited. That recovers *which*
service publishes and consumes which message. **It does not recover the order they run in**, which
static reading cannot establish — the order comes from knowing the business, and the method drafts
it from the industry's process model.

## Two rules that decide whether the extraction works at all

- **Scan the repository root, never a subdirectory.** Service-map keys are repo-root-relative, so a
  `src/` root makes every one of them miss without an error.
- **A service map is required** — one `<source-path>=<deployable-name>` pair per deployable. Without
  it the join returns nothing, and an empty result reads like a finding rather than a mistake.

## How a run is judged

Seven conditions, in [`JUDGING-INSTRUMENT.md`](JUDGING-INSTRUMENT.md). **Each is lifted from an
established field's own done-condition** — SEI architecture reconstruction, the software reflexion
model (Murphy, Notkin & Sullivan 1995), important business services and impact tolerance
(FCA/PRA), service level indicators and objectives (Google SRE). Nobody on this side wrote the
bar, which is the point: a standard written by the thing being measured is not a standard.

The example run scored **three met, two not met, one partial, one not exercised**
([`example/JUDGING-SCORE.md`](example/JUDGING-SCORE.md)), and its own account of why is more useful
than the tally.

## What it does not do

- **It cannot confirm the order stages run in.** Static source reading admits transitions that never
  occur; recovering real ordering needs the record of a system that actually ran. The order comes
  from knowing the business — stock is checked before goods ship — which the method drafts from the
  industry's process model. The code supplies which stages are real and where. Confirmation is what
  is unavailable.
- **Healthy, tolerance and ownership need a person.** The run drafts a position on every one and
  labels it; nothing in a codebase supplies a business objective, a maximum tolerable disruption, or
  an owner. Those land in a ratification queue grouped by the role whose yes each needs.
- **Mainframe subjects are out of scope** — declined, not worked around.
- **Language coverage is per rule, not per language.** Java 32 rules, C# 28, Python 19,
  JavaScript/TypeScript 17, Go 4. **Coverage is not the same as standing** — see below for which rules
  have been judged against source. A language the parser reads but no rule covers returns nothing,
  which looks identical to a system with no structure. The `reach` block reports every deployable
  that produced nothing and every file type nothing read, and marks the run incomplete when either
  happens.

## What is written down but not established

Stated so nobody has to find out the hard way.

- **Seven of the hundred rules hold established standing** — `dfo-js-env-read`,
  `dfo-js-outbound-http`, `dfo-js-durable-read`, `dfo-js-durable-write`, `dfo-python-env-read`,
  `dfo-java-durable-write` and `dfo-java-repo-decl`, each judged correct against source on ten or
  more samples across two or more estates. **Forty are provisional, fifty-one unchecked and
  two quarantined**, and `fact-base.json` → `rule_standing` reports which, on every run, with
  the facts resting on each.
- **A quarantined rule keeps running, and its facts stay labelled rather than dropped.** Two are
  quarantined. `dfo-csharp-message-publisher` had four of six sampled facts judged correct.
  `dfo-java-durable-read` reads a hand-rolled class carrying the framework's repository annotation
  over an in-memory list — type name, annotation and method name all say durable, only the
  field's initialisation says otherwise, and a line-scoped rule cannot see it.
- **Standing is computed from evidence, and evidence expires when a pattern changes.** Each
  recorded sample carries a fingerprint of the rule it was drawn from; edit the pattern and the
  evidence is discarded rather than carried forward. This is enforced, not a convention — two
  rules in the current set carry samples voided this way.
- **Sixteen of the C# rules have been sampled and none has reached established standing.** One is
  quarantined; the rest sit provisional.
- **`background_trigger` for Python matches nothing on either test estate.** A pattern that matched
  a load generator's decorators was removed as wrong, and the remaining patterns have never fired,
  so the rule is unverified rather than clean.
- **The Go rules were authored during a run, are marked provisional, and have never been
  sampled.** The JavaScript and TypeScript rules have since been sampled on real estates, and four
  of them hold established standing.
- **A load generator does not belong in the service map.** It is not part of the business system,
  and mapping it declares a deployable whose silence the reach check then reports.
- **Every subject so far is a reference application** — small, coherent, built to be readable.
  Nothing here says how this behaves on a system carrying several teams' conventions.
- **No independent scorer has used the judging instrument.** It has been applied by people who have
  also worked on the method.
- **Rules authored during a run enter marked `provisional`** and appear in the run's announcement
  block. They belong in the ratification queue, not in accepted output.

## After you have fitted your own tool

This directory is a kit for standing the method up somewhere it has never run, and a kit carries
things that are used once. If you have replaced Phase 1's extractor with a tool of your own,
scored the fit, and reproduced the install check, these have done their job and can go:

| Done its job | Why |
|---|---|
| `fact-extractor/rules.yaml`, `fact-extractor/run.py`, `fact-extractor/README.md` | The reference extractor and its description; your tool performs the phase now |
| `acceptance/` | Scored your tool once against the hand-derived key; keep it only if you expect to swap again |
| `verify/` | The install check for the reference extractor |
| `INTEGRATION.md` | Read once, while fitting |

What stays is the skill itself: `SKILL.md`, `reference/`, `JUDGING-INSTRUMENT.md`, `adapter/`,
and the checks that operate on any extractor's output rather than on ours —
`fact-extractor/contract.py`, `fact-extractor/coverage.py`, `fact-extractor/join.py` (unless your
tool cites every hop across services itself) and `fact-extractor/precision.py`. Keep the example
for shape. If you kept the reference extractor beside your own, keep everything: sources compose.

## The one thing to keep

The example run's most valuable finding was made by the step that reads a difference and rules on
it — not by any automated check. Every mechanical check passed on a run where two of twelve stages
were hollow. **The checks tell you the extraction reached the estate. They do not tell you the
business works.**
