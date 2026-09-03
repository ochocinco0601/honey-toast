# Fitting a different extractor

**Read this if you are replacing or augmenting Phase 1 with a tool of your own.**

Phase 1 recovers what a system is built from. The method treats it as a **contract, not a
fixture**: any tool that satisfies the contract can perform it, and the one shipped here is a
reference implementation rather than the answer. If your organisation already owns a code-analysis
tool, it is very likely a better instrument than this one — it will read languages these rules do
not, and it is already deployed.

This document says what the socket requires, so you can fit your tool to it and **measure the fit
instead of asserting it**.

---

## What Phase 1 must produce

A **fact base**: a JSON object with a `facts` array. Each fact is one structural thing found in
the source, and it must carry:

| Field | What it is |
|---|---|
| `kind` | One of the closed vocabulary below |
| `file` | Repository-relative path, forward slashes |
| `line` | 1-indexed integer |
| `evidence` | The actual source text at that location |
| `service` | Which deployable it belongs to, or `null` if it matches none — reported, never guessed |

Recommended and consumed where present: `in_type` (the enclosing type — the join needs it),
`in_test` (test code is evidence about the system, not part of it), `rule` (which rule or tool
produced the fact, so its accuracy can be tracked).

**The kinds.** `inbound_route`, `outbound_http`, `grpc_method`, `grpc_call`, `message_consumer`,
`message_producer`, `message_publisher`, `message_subscription`, `durable_read`, `durable_write`,
`repo_decl`, `env_read`, `config_ref`, `background_trigger`, `poll_interval`, `client_binding`.

A kind outside that list is not rejected as wrong — it is reported, because nothing downstream
consumes it and the gap should be visible rather than silently carried.

**Top level** must also carry `root`, `counts` by kind, a `reach` block (below), and a `tool`
block naming the analyser, its version, and a fingerprint of its rule set.

---

## The three guarantees that are not negotiable

**1. Every fact carries a location, and the evidence is really there.** A person must be able to
open the file at the line and see the thing. This is the claim the whole method rests on: the
business account is drafted from an industry process model, and the code account is what stops it
being a story. A tool that emits plausible coordinates with invented evidence satisfies every
other check and destroys the method.

**2. Deterministic.** The same source gives the same answer. The model sorts and labels what the
tool found; **it never adds a connection it "saw" by reading source.** Model-asserted cross-service
structure has been measured at zero precision, zero recall, and 39.1% fabricated edges (De Luca et
al. 2026, arXiv:2606.26927). This is not a stylistic preference.

**3. The run says when it did not read the estate.** The `reach` block names every declared
deployable that produced no facts and every file type nothing read, and marks the run incomplete.
Without it, a run that read half a system is indistinguishable from a system half the size, and the
output for the unread half is empty rather than sparse — which reads as a finding.

---

## How to test your tool

Two commands. Run both. They answer different questions and neither substitutes for the other.

### 1. Does the output conform?

```
python fact-extractor/contract.py <source-root> <your-fact-base.json>
```

Ten checks, pass/fail, with the specific failures named. It verifies shape, the closed vocabulary,
path hygiene, the reach block, and — the one that matters — **it opens a sample of cited locations
and confirms the evidence is actually there.**

Two checks exist because both defects were found in this project's own shipped output, and they are
the ones a second tool is most likely to repeat:

- **Identifiers must not carry filesystem paths.** One analyser namespaces its rule ids with the
  path to its rule file, so every emitted fact carried the operator's directory tree. That leaks
  the producing machine and makes two machines' output incomparable.
- **A location may carry two kinds, but not silently.** A line can genuinely read the environment
  *and* write configuration. What it may not do is become two facts with nothing saying so, because
  every count downstream then doubles. Disclose it in a `multi_kind_locations` block.

To check determinism, run your tool twice and pass both:

```
python fact-extractor/contract.py <root> <run-a.json> --compare <run-b.json>
```

It reads the tool and rule-set fingerprints **before** calling a disagreement non-determinism — a
different rule set means a changed answer, not an unstable one. That distinction cost half a day
here when it was missing.

### 2. Does it find what is actually there?

```
python acceptance/accept.py <your-join-output.json>
```

Scored against **Bank of Anthos**, a public codebase whose answer was hand-derived twice,
independently, before any of this tooling existed. A tool scored against a key its own output
produced proves nothing.

---

## The seam — read this before you decide anything

**Static analysers are good at per-file structure and typically stop at the boundary between
services.** That boundary is where a business process actually lives, so it is the axis on which
candidate tools differ, and it is scored separately for exactly that reason. A tool can be
excellent at everything else and recover no seams at all; one number would hide that.

The test case on this subject is the edge `frontend -> ledgerwriter`, and it is four hops:

1. The call site names no target — it reads a URI from configuration
2. The URI is built from an environment variable
3. The variable resolves to a service name **only inside a Kubernetes manifest**
4. The receiving route is in a different language

**Hop 3 leaves the programming language entirely.** A tool whose parsers cover source files but not
deployment manifests cannot complete this chain, however good it is at the other three hops. Check
what your tool parses before assuming it will.

**The harness reports three states, and the middle one is the whole judgement:**

- **cited** — every hop carries a location a person can open
- **partial** — some hops cited, the failing hop *named*, and the edge marked incomplete. This is
  the tool disclosing its limit, and it is the behaviour the method asks for
- **asserted** — no citations, or a claim of completeness with none. A hop somebody decided
  existed

**A tool that says where it stopped is usable. A tool that fills the gap silently is not.** If your
candidate produces cross-service edges by having a model decide there is a hop, those will land in
`asserted` and the harness will refuse it — not because model reasoning is forbidden, but because
an uncheckable edge reads exactly like a real one downstream and nothing later can tell.

**What "acceptable" means here** is deliberately not a recall threshold: the hard edge recovered
with citations, and nothing asserted. A tool that recovers eight easy edges and misses the seam has
not done the job. A tool that recovers the seam and little else has done the part nothing else does.

**The shipped extractor's own baseline**, so a substitute has something to be compared with:

| | |
|---|---|
| Verdict | acceptable |
| Cross-boundary, cited | 6 of 9 — `accept.py` → `cross_boundary` |
| HTTP | 6 of 6, including the hard edge with all four hops cited — `accept.py` → `cross_boundary.by_protocol` |
| SQL | 0 of 3 — `accept.py` → `cross_boundary.by_protocol` |
| Partial and disclosed | 2 — the alternative monolith deployment topology, whose target is not a declared deployable |
| Asserted without citations | 0 |

The shipped join recovers no database dependencies: it follows call sites and addresses, and the
hop from a service to the database it writes is not built, although the repository declarations it
would start from are in the fact base. A substitute that recovers those three edges with citations
has done something this one cannot.

---

## What to keep regardless of what you fit

**Keep the join, unless your replacement cites every hop.** Following a call site through a
configuration binding to a deployable is the step that produces the horizontal picture — the thing
that was asked for and the thing per-component tooling does not give. Replacing a cited chain with
an uncited one is a downgrade that looks like an upgrade.

**Keep the controls.** The reach check, the coverage reconciliation, the decoy control and the
false-negative control operate on the *fact base*, not on any particular extractor, so they survive
the swap — but only if you keep running them. Without them you cannot say a run read the estate.

**Keep the precision apparatus.** `fact-extractor/precision.py` draws a stratified sample for a reader
to judge, and `rule_standing` computes each rule's standing from accumulated evidence rather than
from a flag. Point it at whatever produces your facts. Conformance says the output has the right
shape; only a reader says the facts are true.

**One warning from experience, worth more than the rest of this section.** Enforcement written into
an instruction file that a model reads is not a gate. A documented rule fix in this project sat
unapplied in the file it described for a full day, and nobody noticed until something counted. If
you adopt a guarantee, put the check in code.

---

## Reporting the result

Whatever you fit, record in the run directory: the tool, its version, its exact invocation, the
conformance verdict, and the acceptance score with cross-boundary reported separately.

That record is what lets someone else judge the substitution without repeating it — which is the
same reason this package exists at all.

---

## What this does not settle

- **Conformance is necessary and not sufficient.** It says the fact base has the shape and the
  citation integrity the passes require. It does not say the facts are true.
- **The acceptance key covers one business process flow on one subject.** It is a gate, not a
  benchmark. There is no published accuracy baseline for static message-topology recovery anywhere,
  so there is nothing to calibrate against.
- **Ordering is out of reach for any static tool**, yours included. The order stages run in comes
  from knowing the business, which the method drafts from the industry's process model. Source
  reading says which stages are real and where. Confirmation is what is unavailable.
