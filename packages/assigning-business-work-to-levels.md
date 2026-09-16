# Assigning a piece of business work to its level

**Who this is addressed to.** A language model handed source material about a business — source
code, architecture documents, interview notes, a strategy deck, a runbook — that must draft how the
work happens as six levels: **capability**, **intended flow**, **stage**, **process step**,
**component**, **dependency**.

**Why the six are kept apart.** They differ in what observing them can tell you, and collapsing any
two destroys a distinction somebody downstream needs. A capability has no executions at all — it can
report how much of itself is modelled and never how it is doing. A flow finished or it did not. A
stage says how far the case got and how long that segment took. A step happened or did not, and
produced something or did not. A component and a dependency yield diagnostics, which explain a
business measure and are never one themselves. The line that matters most runs between step and
component: above it a measure answers *did the business get what it expected*, below it *how did the
mechanism behave*. A draft that collapses those two can no longer tell a stakeholder anything.

**What it owes, and the standard it is held to.** A position on every assignment, the frame that
position was taken under, whether it was read or inferred, and what else it could have been.

It is **not** held to producing a determined answer. Two competent analysts given the same material
will not assign these levels identically, and no procedure will make them. Judging this kind of
guidance by whether two people converge is the wrong test and will condemn guidance that is working.
The right tests are: **is the position defensible, is the reasoning visible, and can someone who
disagrees see exactly what to argue with.** Everything below is built for those three, which is why
each assignment carries its frame, its standing and the alternative it rejected.

**A word to avoid: *trace*.** In observability and monitoring, *a trace* means the runtime record of
one request reconstructed from telemetry — what actually happened, measured after the fact. This
procedure is entirely design-time; nothing is running and nothing is being measured. Saying "trace
the flow" will send a reader to look for telemetry that does not exist. Say **walk**.

---

## The two tests, in order

Everything below rests on these. Run them in this order; the second is meaningless before the first.

### Test 1 — Is it a position the case reaches?

> Can you sensibly ask **"has the case reached it yet?"**

- **Yes** → it sits on the case's path. It is a **stage** or a **step**: a state the case sits in is a
  stage, an act between two such states is a step. Go to Step 4, which cuts them from the walk.
- **No — the question is malformed** → it is off the path. Run Test 2.

**The flow is not reached by this test**, and asking it of one comes back malformed for the same
reason: the case is inside the flow the whole way, because the flow *is* the path rather than a
position on it. Step 3 shows the frame has already named it.

*"Has the application reached document upload?"* — sensible. A step, however much *document upload*
sounds like an ability once nominalized. *"Has the application reached loan origination?"* —
malformed; the application is inside loan origination the whole way. Off the path.

### Test 2 — For anything off the path: is it a thing that exists in an environment?

> Could you **deploy it, restart it, or page someone about it**? Does it have a version, an owner,
> or a vendor?

- **No, and it is an ability** → **capability**. An ability is not a thing you can restart.
- **Yes** → a **component** or a **dependency**. Separate those two in Step 6.
- **Neither** → it belongs to none of the six, unless it is the frame's own flow, which Step 3 has
  already named. A policy, a rule, a team, a role, a form, a document:
  real, named constantly by sources, and not a level here. Say so and set it aside. Forcing it into
  the nearest level is how *the credit policy* ends up recorded as something the business is able to
  do.

**Why two tests and not one.** The six levels are three of one kind and three of another. Flow,
stage and step sit on the case's path — the flow is the whole of it, a stage or a step a position
along it. Capability, component and dependency are not on the path at all: a capability is what the
path is **for**, and a component or dependency is **what performs** it. A single test cannot
separate three groups. The split itself is business architecture's: what a business is able to do is
modelled separately from how work moves, precisely so that one can be re-implemented without
restating the other.

**What Test 2 deliberately permits**, which a cruder "does it survive the vendor changing" test
throws away:

- **Capabilities may carry time.** *Same-day settlement*, *next-day delivery*, *real-time
  authorization*. The time is usually the whole point.
- **Capabilities may be bound to a vendor, scheme or regulator.** *Accept a given payment method*,
  *issue cards on a given network*. Often exactly what the business sells. You cannot restart
  "accept a given payment method", so it is still a capability.

---

## Step 0 — Declare the frame. Do not skip it and do not infer it silently.

Four declarations, written on the artifact as **outputs**.

| | |
|---|---|
| **The case** | The individual thing that travels. One loan application. One payment. One order. Not a system, not a team. |
| **Whose expectation** | The party counting on this to happen, named. |
| **The starting event** | Where that party's expectation begins. |
| **The ending outcome** | Where that expectation is satisfied, or definitively is not. |

**The start and end are not free choices — the expectation sets them.** Everything below is relative
to this, and nothing in the source obliges you to state it. A walk that begins where the
source material happens to begin, and ends where it happens to end, produces a flow whose boundary
is an artifact of the document. A walk bounded by the expectation produces one whose boundary means
something: it starts when somebody began counting on an outcome and stops when they got it or
did not.

Two consequences follow from this and nothing else in the procedure justifies them:

- **It is why stages are named as states reached** rather than as activities performed. The
  segments of the walk are positions between *"they are counting on it"* and *"they have it"*, and
  positions are states.
- **It is why the capability is the anchor.** A stakeholder does not expect a particular flow to
  execute; they expect the business can do a thing. The flow is the means, and means change — a new
  path, a new service, a re-platform. An expectation tied to the flow is orphaned by every
  re-implementation. Tied to the capability it survives.

Every assignment below is relative to these four. The same activity is a capability under one frame
and a single act under another, and neither is wrong. Two drafts made under different unstated
frames look comparable and are not.

**If no expectation is identifiable in the source**, say so and name the boundary you used instead.
A frame drawn from document convenience is still a frame — it just has to admit what it is.

**If the source contains no case** — a target operating model, a capability deck, an org chart —
**stop and say so**: *"This source describes abilities only. No case is present. A walk cannot be
performed; the capability level can be drafted alone, and everything below it would be fabricated."*
Do not invent a path in order to have something to walk.

**If several cases are plausible**, name them, pick one, say why. Do not blend them.

## Step 1 — Walk the case

Follow that one case from the starting event to the ending outcome and write down, in order, what
happens to it.

**Walk the case, not the document.** You will be tempted to return the structure of whatever you
were given. This is the characteristic failure in this task and it produces a description of
the document rather than the business:

| Given | What you will reach for | What you will miss entirely |
|---|---|---|
| Source code | components, dependencies, individual calls as "steps" | stages — they live in waits and handoffs, invisible in a call graph |
| Architecture documents | components and dependencies | the case's path; everything on the timeline |
| A strategy deck | capabilities | everything beneath them |
| Interview notes | stages and steps | components, and often the capability |

The case has a path regardless of which artifact you read it from. Anchor there.

**Write what happens to the case, in the case's terms.** *"The application is sent for a credit
decision"*, not *"`CreditService.evaluate()` is invoked"*. Component names are Step 6.

## Step 2 — Name the capability

Ask what the whole path is **for** — what the business is thereby able to do — then apply Test 1 and
Test 2 to confirm what comes back is off the path and an ability. The two tests classify a candidate;
they do not produce one, and reading it off the path is where it comes from. What you have is a
capability: what the business is able to do, named independently of how it is built.

Hold it. You will derive it a second time in Step 7 and keep any disagreement.

## Step 3 — The flow is already decided

Once the frame is declared, **the flow is the frame**. The case, its starting event and its ending
outcome name exactly one intended flow. There is no separate judgement.

This dissolves the argument about whether something is a flow or a stage of something larger.
Underwriting is a stage if origination is the frame and a flow if underwriting is the frame. Both
are correct, and the frame — which is written down — says which.

## Step 4 — Stage boundaries fall where the case PARKS

**Do not cut on waits.** Waits are everywhere and cutting on them shatters the model. Ask:

> **Is anything actively progressing the case right now?**

- **Yes** — a retry, a call out and back, a write, a scoring run. The wait is *inside* an act; the
  act has not finished. **Not a boundary** — unless the case becomes irreversible here; see below.
- **No** — the case is sitting, nothing is moving it, it waits to be picked up or waits on
  something external. **Boundary.**

**Three things park a case, and they are not all the same rule.** Two are the test above seen twice:
the case **changes hands**, or it **queues** — in both, nothing is progressing it. The third is a
different rule and worth knowing as one: the case **becomes irreversible** and cannot go back. That
can fall where the case never actually stopped, and it is still a boundary, because what is true of
the case on either side of it is not the same.

**Name each stage by the state the case has reached**, not the activity performed — *awaiting
appraisal*, *decision recorded*, *funds released*. A stage must answer *"where is this case right
now?"* for a case in flight. If your stage names cannot, you have written activities and collapsed
two levels. The reason is in Step 0: the walk runs between *they are counting on it* and *they have
it*, so every segment of it is a position, and positions are states. Where a setting expects verb
phrases — value-stream and process-classification practice conventionally uses them at this level
— note the difference rather than treating a naming convention as a modelling error.

**Two results that look wrong and are not:**

- **Work that never parks yields one stage for the whole flow.** A card authorization of two hundred
  milliseconds, one service, nothing queued — one stage is correct, not degenerate.
- **Work that parks constantly yields many stages.** A mortgage file parks at dozens of points
  because it has dozens of waypoints. If a smaller number is wanted for reporting, make that
  aggregation explicit and say which stages were merged. Do not suppress boundaries to hit a count.

## Step 5 — Steps are the acts between parks

One act, one outcome, that either happened or did not.

**Floor:** one performer, one place, one sitting. Do not go below it. Clicks, field validations and
internal function calls are not steps.

A step **may** contain a wait if something is actively working through it — Step 4's test, applied
downward.

## Step 6 — Components and dependencies

Both passed Test 2: things that exist in an environment. Separate them by **whose they are**.

| | Test | |
|---|---|---|
| **Component** | It performs a step, and **your side can change or fix it.** | Bind each one to the step or steps it performs. A component that performs no step in this walk is out of scope for this frame — say so rather than listing it. |
| **Dependency** | A component **requires** it and **inherits its failure**, and your side **cannot fix it** — it can only be called, waited on, or failed over. | Bind each one to the component that requires it. |

**The line is control, not technology.** A shared database owned by another team inside the same
company is a dependency if your side cannot change it. A third-party API is a dependency. A library
compiled into your own service is neither — it is part of the component.

**This is where code-sourced drafts over-produce.** Code names every module, client and library it
touches, and a model reading it will return all of them. Most are not components in this model:
a component performs a step in *this* walk. If you cannot name the step it performs, it is out of
scope for this frame — say so, as above, rather than listing it for completeness.

**And where narrative sources under-produce.** Interview notes and strategy decks name almost no
components. Do not manufacture them — record the level as a single `undetermined` row saying what
source would settle it. A level with no rows at all reads as a level nobody looked at.

## Step 7 — Derive the capability twice, and keep the disagreement

You have a capability from Step 2, read off the path. Now do it again independently: **read
candidate capabilities directly from the source** — what does this organization say it is able to do.

**The independence has to be built, not intended.** A reader who already holds Step 2's answer will
agree with it, and the agreement will mean nothing — the comparison returns concurrence by
construction, and disagreement, the outcome this step exists to make reachable, can no longer arise.
So derive the source side in a pass that has not seen the path side: a separate context, a separate
session, or the source side first with the walk withheld. This is the software reflexion model's own
constraint — a model read from the source is compared against a model derived some other way, and
deriving the second from the first makes the comparison tautological.

- **They agree** → record once, note both routes produced it. The strongest assignment in the draft.
- **They disagree** → **record both and say so.** Do not resolve it silently. The disagreement is
  information about the source, not an error in the draft.
- **One path serves several capabilities** → common and correct. Order-to-cash delivers selling,
  collecting cash, and giving the customer visibility. List all of them.
- **One capability served by several paths** → also correct. Straight-through settlement and
  settlement via an adjuster are two flows delivering one capability. Do not merge them.

---

## What every assignment carries

Four labels. An assignment without them is an arbitrary choice that reads as an authoritative one.

| Label | Values | Why |
|---|---|---|
| **Frame** | the case, whose expectation, starting event, ending outcome | every assignment is relative to it |
| **Standing** | `attested` — stated in the source or given by the declared frame, cite which · `inferred` — derived, say from what · `undetermined` — the source does not settle it | on messy input this is the line between a draft and a fabrication |
| **Alternative** | the reading you did not take, or `none` | this is what a reviewer disagrees with; omitting it makes the draft uncorrectable |
| **Binding** | for a component, the step or steps it performs; for a dependency, the component that requires it; `undetermined` where nothing in the source binds it; `n/a` at the other four levels | Step 6 demands it, and a component bound to no step is not a component in this walk |

**`undetermined` is expected, not a failure.** A model with thin material that produces confident
assignments is worse than one that declines.

**And a complete draft must be distinguishable, on its face, from an unattempted one.** If every
level came back attested and nothing is undetermined, that is a valid and good outcome — say so
explicitly rather than letting silence stand for it. An instrument that cannot report the negative
case cannot be trusted when it reports the positive one, and a blank reads as fine to everyone who
sees it.

---

## What this procedure goes blind to

Known limits, stated rather than discovered later.

- **Parallel work.** Background check, references and offer approval running at once — *"where is the
  case right now?"* has three simultaneous answers and the stage level assumes one. Record the
  branches; do not force a sequence.
- **Rework and loops.** A case returning to an earlier state repeatedly is normal and an ordered
  segment does not express it. Note the loop.
- **Exceptions, cancellations and reversals** — the reject, the appeal, the return, the refund.
  Plausibly most real operational work and not covered here.
- **A changing unit of case.** Many requisitions become one purchase order; one invoice spans
  several; one payment batches several invoices. Step 0's single case has no answer. Say which unit
  you walked and where it changes.
- **Components shared across flows.** A component performing steps in several flows is bound here to
  one walk only. Nothing in this procedure reconciles across walks.

---

## Worked example — plausible, not real

A plausible case, to show the shape.

**Frame.** Case: one home loan application. Whose expectation: the applicant. Starting event: they
submit the application and begin waiting on an answer. Ending outcome: funds released, or the
application declined — the point at which they have their answer or definitively do not.

Note what the expectation boundary excluded. Everything the lender does after funding — servicing,
collections, the secondary market — is real work and is outside this walk, because the applicant
stopped waiting when the funds landed. A different party's expectation gives a different flow over
the same systems.

| Level | Assignment | Standing | Alternative | Binding |
|---|---|---|---|---|
| Capability | Loan origination | `attested` — named in the source, and reached independently by walking the path; Steps 2 and 7 agree | `none` | `n/a` |
| Capability | Same-day credit decisioning | `inferred` — from a stated commitment, not named as a capability | could be a target rather than an ability | `n/a` |
| Intended flow | Originating a loan | `attested` — given by the declared frame | `none` — the frame decides it | `n/a` |
| Stage | Submitted | `attested` — the source names it as the entry state | `none` | `n/a` |
| Stage | Awaiting credit decision | `inferred` — the case parks on the bureau | could sit inside *submitted* if the bureau answers inline | `n/a` |
| Stage | Decision recorded | `attested` — named in the source | `none` | `n/a` |
| Stage | Awaiting conditions cleared | `undetermined` — conditions are mentioned, parking is not | may not be a distinct stage at all | `n/a` |
| Stage | Funded | `attested` — named in the source | `none` | `n/a` |
| Process step | Pull the credit file | `attested` — named in the source | `none` | `n/a` |
| Process step | Score against policy | `inferred` — from a policy the source references but no step performs | may be part of pulling the file if the bureau scores | `n/a` |
| Process step | Record the decision | `attested` — named in the source | `none` | `n/a` |
| Component | Bureau interface | `attested` — named in the source | `none` | performs *pull the credit file* |
| Component | Decision service | `inferred` — not named as a deployable, implied by a step that records a decision | could be the same deployable as the bureau interface | performs *record the decision* |
| Dependency | The credit bureau's API | `attested` — named in the source, and not fixable from this side | `none` | required by *bureau interface* |
| Dependency | The application store | `undetermined` — implied by every step, named by nothing | may be internal to the decision service, in which case it is not a dependency | `undetermined` — no component names it |

**Note what the frame did.** *Credit underwriting* is absent from the capability level, because under
this frame it is a position the application reaches — the one recorded above as *decision recorded*. Take a different case — one credit file moving
through the lender's risk operation, whose expectation belongs to the risk officer — and underwriting
becomes the flow, with the ability to underwrite the capability it delivers. Both are right; the
frame is why.
