# V&V report — `eshop-order-2026-09-01`

**Mode:** V&V. The instrument changed materially the same day — the extractor gained two languages
and four target-resolution idioms, the join was built, and the skill gained its reach-check
section. **Under V&V a finding is recorded and the run moves on; nothing here was fixed mid-run.**

| Class | Meaning | Destination |
|---|---|---|
| INSTRUMENT | A phase contract produced the wrong kind of output, named an input with no producer, or was ambiguous enough to need inventing | Issue, then a Gotchas line — after the run |
| CONTENT | Right shape, wrong facts about the subject | The ratification queue |
| EDGE | The subject has a pattern no phase handles | Design backlog |

---

## I1 · INSTRUMENT — the join follows the wrong seams on an event-driven estate

**What happened.** `join.py` recovered four HTTP dependencies. The ordering business process is
carried by **eighteen integration-event handlers**, and the join found none of them, because a
published event has no call site and no address to follow.

**Why it is not just a missing feature.** The extractor's documentation already lists the
asynchronous join as not ported from the superseded script, and reads as an edge case. **On this
subject it is not an edge case — it carries most of the business process.**

**And the four it did find are not peripheral, which an earlier draft of this report got wrong.**
One of them is `webapp → ordering-api` at `src/WebApp/Services/OrderingService.cs:17`, inside
`CreateOrder` — the call that submits the order, stage 3, the commitment point. The join reads
web calls well. **It also lost one of them:** its own `reconciliation` block reports three of four
declared connections recovered and names the miss as `webapp → basket-api`, stage 2. So the
honest statement is three failures of different kinds, not one.

**What made the run survive it.** The event handlers are `extracted` facts in their own right and
**their class names are the business process** — `OrderStatusChangedToAwaitingValidation`,
`OrderStockConfirmed`, `OrderStatusChangedToPaid`. The structure was recovered from what each
service listens for rather than from what it calls. That is a workaround, not a design.

**What would close it.** A resolver that pairs a published event type with the services that
declare a handler for it. Both ends are already extracted facts; the pairing is on the type name,
which is the same shape as every other hop the join performs.

---

## I2 · INSTRUMENT — the most important durable write in the process was not extracted

**What happened.** `CreateOrderCommandHandler.cs:51` persists the order through
`_orderRepository.UnitOfWork.SaveEntitiesAsync(...)`. The rule matches `SaveChangesAsync`. The
extracted durable writes for the `ordering` service are its seed-data loader and nothing else.

**Why no check caught it.** Coverage reconciliation needs a declarative source that enumerates the
population. Durable writes have none, and the coverage output says so — it reports the category
`unmeasured`. **This is that word becoming concrete:** the run reported recall 1.0 on both measured
categories while missing the write the whole business process exists to perform.

**What it says about the shape of the risk.** The categories that can be measured are the ones an
estate declares — HTTP operations, protocol methods. The categories that carry the business
process — durable writes, message seams, background work — are exactly the ones nothing declares.
**Measurable and important are close to disjoint here**, and no amount of measuring the first set
bounds the second.

---

## I3 · INSTRUMENT — condition 2 is unreachable as the skill is written

**What happened.** The judging instrument's condition 2 requires the business account be *stated
without reference to the code*. The skill's own standing ruling supersedes the blind fork —
sources compose, independence is recorded per claim. **A single session running all phases in
order has necessarily read the extraction before drafting**, so condition 2 cannot be met by any
run performed the way the skill describes.

**This is a contradiction between two parts of the instrument, not a mistake by this run.** Either
the condition should be restated to match the composition ruling, or the skill should say that
Phase 2 is drafted before Phase 1 is read — which is a real option, since Phase 2 needs only the
sector and the subject's name.

**Recorded, not resolved.** Resolving it is a ruling, and a run does not make rulings about the
method.

---

## I4 · INSTRUMENT — the run claimed a sequence that no source-reading can establish

**Added after the run, from two independent prior-art checks** — a blind check and a sourced
literature search, which reached it by different methods.

**What happened, stated precisely, because a first version of this finding overreached.** The
run's stage order came from Phase 2 — drafted from how the retail order-to-cash process works,
before any code was read, and labelled `proposed` throughout. **That is the correct source for
an order and it is one of the sources this method is built to compose.** Domain knowledge
supplies sequence; a credit request precedes closing documents in lending whether or not anyone
reads the lender's source.

**The defect is one sentence in Phase 3**, which said the chain was *"readable from the handler
names on both sides"*. That is a model reading English in class names and presenting it as
corroboration from code — the exact move the tool-only rule forbids, and measured at zero
precision for cross-service claims. **The order needed no such support.** It had a legitimate
source already, and the sentence borrowed a second one it had not earned.

**What the code genuinely cannot do.** Confirm that this business runs the stages in that order.
Reading source establishes that a step *can* hand to another, never that it *always* does —
static sequence reconstruction admits transitions that never occur and is undecidable in general,
and the discipline that confirms a real sequence consumes the record of a system that ran.
**Confirmation is what is unavailable here. The order is not.**

**What is defensible from code, and is cheap.** A rule for *this handler publishes that event*.
A one-hop fact with a file and line at both ends; the research pass confirms no tool currently
emits it. It says which stages *can* hand to which — real corroboration for a drafted order,
which is what the Phase 3 sentence was reaching for without the evidence. **Composing those hops
into a claimed sequence is the thing that must not be done:** every consumer of an event is a
possible successor, and a branch is indistinguishable from an alternative.

**The consequence for the method.** Its premise is that sources compose, and this is that
premise working rather than failing: the industry model supplies the order, the code supplies
which stages are real and where, and runtime — which no run in this cut produces — would supply
confirmation. **A code-only run yields a drafted order bound to real implementations. It does
not yield a confirmed one, and it never claimed to until that sentence.**

---

## C1 · CONTENT — the payment step charges nobody

**Not an instrument finding.** The extraction, the reconciliation and the ruling step all worked;
what they found is a fact about the subject. Recorded here because it is the run's headline result
and because it is the case that no mechanical check detected. It goes to the ratification queue as
R1.

---

## E1 · EDGE — a hollow stage looks identical to a working one in every structural view

**The pattern.** A service consumes the right event, decides an outcome, and publishes the right
downstream event — while performing none of the work the stage names. Topologically it is
indistinguishable from a working stage. Every automated check passes on it.

**No phase handles this.** Phase 3 classifies it convergence, correctly, because the structure
does converge. Only Phase 4's ruling step — a model or person asking *what does this actually do* —
separates the two, and nothing in the instrument requires that question be asked of a
**convergent** stage. Today it was asked because the reader was curious.

**Why it belongs in the backlog rather than being fixed here.** The cheap version — flagging a
handler whose body reads configuration and publishes — is a heuristic that would fire on plenty of
legitimate code. The honest version is that convergence is not evidence of function, and the
instrument currently treats it as though it were.

---

## What passed, and is worth recording as having passed

- **The reach check.** Every declared deployable produced facts; the run had no silent services.
- **Both coverage controls.** Fabricated routes rejected; known implementations recognised.
- **Reproducibility.** The extraction and the join reproduce from the committed commands.
- **Test exclusion.** Eight facts from end-to-end test configuration were marked and excluded from
  every downstream phase.
- **The practitioner's-draft discipline.** No cell was left as a secretary's blank. Everything
  unknowable on this subject is `gapped` or `unowned` with the reason and what would close it.
