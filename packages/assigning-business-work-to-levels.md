# Assigning a piece of business work to its level

**Who this is addressed to.** A language model handed source material about a business — anything
that describes how the work happens, whether that is source code, architecture documents, interview
notes, a strategy deck, a runbook, a ticket history, a database schema, a contract, a training
manual, a recorded conversation, or something with no name — that must draft how the work happens
as six levels: **capability**, **intended flow**, **stage**, **process step**,
**component**, **external dependency**.

**Why these six and not some other set.** The capability is running in production, delivered by
technology, and somebody has to know whether it is healthy — in business terms, in application
terms, in technology terms — and restore it when it is not. **Every distinction below earns its
place by passing one of four tests, and each test names the distinction it justifies:**

| The test | What it justifies |
|---|---|
| **Failure response** — does knowing this change what can be done when the thing fails? | The line between step and component, and the split between component and external dependency. Above the line a failure is something the business did not get; below it, something a technology team can act on |
| **Durability** — does this survive the work being re-implemented? | The capability. A new path, a new service, a re-platform: an expectation tied to the flow is orphaned by all of them, and tied to the capability it survives |
| **Structure** — does this record the shape of the path itself? | The intended flow, which holds the order the stages run in. Without it a draft is a set of stages and no sequence |
| **Decomposition** — does this separate time spent waiting from time spent working? | The line between stage and step. In most business work the waiting term dominates by an order of magnitude, and a model that collapses them cannot see it at all |

A distinction that passes none of the four is decoration. **Anything proposed as a seventh level has
to name which of the four it passes**, and may not invent a fifth test to fit — that is how a set
like this doubles in size.

**And one thing all four rest on, which is not a level.** Every test above assumes two drafts of the
same work mean the same thing, which is what the frame declarations buy and why Step 0 refuses to
be skipped. At one application that is tidiness. Across a portfolio it is the whole game: drafts
that were framed differently cannot be counted together, however carefully each one was made.

This says why the cuts fall where they do. It does not say what any particular draft is for — that
stays open, because one draft is read several ways.

*Level* is used as architecture frameworks use it — an ordering by what a thing answers, not a
containment hierarchy. Three sit on the case's path and three do not, which is the only grouping
there is; Test 1 and Test 2 are what separate them.

**The six are not one axis, and the relations between them are four different things.** A capability
and a flow are **cross-mapped**, many to many, and neither contains the other — one path serves
several capabilities and one capability is served by several paths, which Step 7 treats as the
normal case. A flow **contains** its stages and steps. A component **realises** a step. An external
dependency is **required by** a component. Four relations, not one ladder.

**What this forbids: rolling anything up past the flow.** Summing across a many-to-many cross-mapping
double counts, and summing a realisation into the thing it realises is a category error — a
component's error rate is not a fraction of a capability. Measures compose from signals to step to
stage to flow, and stop there. Above that they are derived or asserted, and must say which.

**The word the whole procedure turns on: *case*.** The individual thing that travels through the
work — one loan application, one payment, one order. Never a system, a team or a batch. Step 0 makes
declaring it the first act, and Test 1 below is asked about it — Test 2 is asked about the candidate.

**Why the six are kept apart.** They differ in what observing them can tell you, and collapsing any
two destroys a distinction somebody downstream needs. A capability has no executions at all, so it
emits nothing: any statement about how a capability is doing was **derived or asserted**, never
measured, and has to carry which — rolled up from what, over what coverage, and how much of it is
judgement. Capability heat maps, maturity ratings and readiness figures are all real and all made
this way. Forbidding the number does not prevent it; it only strips its provenance, and a rating
with no provenance is how a model of a business becomes a slide nobody can challenge. A flow finished or it did not. A
stage says how far the case got and how long that segment took. A step happened or did not, and
produced something or did not. A component and an external dependency yield diagnostics, which
explain a business measure rather than being one — except where an external dependency performs a
step itself, which Step 6 covers. The line that matters most runs between
step and component: above it a measure answers *did the business get what it expected*, below it
*how did the mechanism behave*. A draft that collapses those two can no longer tell a stakeholder
anything.

**What it produces.** One table. Every row is a single assignment and carries six fields: the
**level** it was assigned to, the **name** of the thing, the **evidence** actually read, the
**basis** on which it was assigned, the **alternative** reading rejected, and what it is **bound
to**. A seventh kind of row, `set aside`, holds the things a source names constantly that are not
levels at all. The full contract is at *What every assignment carries*; the shape is here so that
nothing below arrives without a column to go in.

**What it owes, and the standard it is held to.** A position on every assignment, the frame that
position was taken under, the evidence for it, whether it was read or inferred, and what else it
could have been.

It is **not** held to producing a determined answer. Two competent analysts given the same material
will not assign these levels identically, and no procedure will make them. Judging this kind of
guidance by whether two people converge is the wrong test and will condemn guidance that is working.
The right tests are: **is the position defensible, is the reasoning visible, and can someone who
disagrees see exactly what to argue with.** Everything below is built for those three, which is why
each assignment carries its frame, its basis and the alternative it rejected.

**Nothing here says what the draft is for, and that is deliberate.** One draft is read several ways
by people who want different things from it — a stakeholder reading only the business sentences, work
that builds on the step and component bindings, a reviewer arguing with the alternative, someone
taking a single assignment back to the material to check it. None of them is the intended one.

**Which is why the same assignment is kept in more than one form.** *`CreditService.evaluate()`* and
*the application is sent for a credit decision* are not a wrong answer and a right one. They are one
assignment in two forms, and which is the useful form depends entirely on who picked the draft up.
Collapse them and you have written for one reader and made the draft useless to the rest — and you
do not get to know which reader is coming.

So the rule throughout is: **do not discard the specific thing you read in favour of the general
thing you concluded.** Both are kept, in different columns. Where this procedure says a form is
wrong, it means wrong *for that column* — not wrong to have.

## Vocabulary — what not to import

Every term below is an ordinary industry term used in its ordinary sense, and the middle
column says whose. The column that earns its place is the third: each of these words carries a
*second* meaning a competent reader, or a model, will supply unprompted. **Test 1 and Test 2 remain
the definitions of record** — this table only says which neighbouring sense to put down.

| Term | The sense meant, and whose it is | Do not import |
|---|---|---|
| **case** | process mining's *case* — the `case id` every event log is keyed on; the *process instance* of the Workflow Management Coalition (WfMC) reference model | a support ticket, the *Case* object in CRM and service-management tools; a test case |
| **capability** | business architecture's *business capability* — the BIZBOK Guide, and TOGAF's business architecture | capability maturity; a security capability or token; POSIX capabilities |
| **intended flow** | the *de jure* process model (van der Aalst) — the process as designed, against the *de facto* process as it actually runs. *Flow / stage / step* as a naming triple is in monitoring use too | BPMN's *sequence flow*, which is an edge between two elements rather than the whole path |
| **stage** | the *place* of a place/transition net, where the token rests between transitions; the queue term of queueing theory, as against the service term; the accumulation point a value-stream map cuts at. A Kanban buffer column and a CRM pipeline stage are the same idea in working use | the *stage* of CMMN, the OMG's case management notation — a nestable container of tasks rather than a position reached; a CI/CD pipeline stage; a deployment environment |
| **process step** | the *task* / *activity* of BPMN, the OMG's business process notation; the *step* in flow / stage / step. The numbered sections of this procedure are also called Steps — the level is always written *process step*, the sections always *Step 4*, *Step 6* | a click, a field validation, an internal function call — Step 5 sets the floor |
| **component** | ArchiMate's *Application Component*, at the granularity of C4's **container** (Level 2) | C4's *component* (Level 3), which is code inside a container |
| **external dependency** | something the application consumes but is **not part of** — a platform, another application, a vendor; Step 6 defines it | a package or library dependency — one compiled into the application's deployable is part of the component, not a dependency of it |
| **park** | ordinary operations usage — a file parked pending documents, a case parked on a desk — given a precise test at Step 4. Formally it is a token resting in a *place* rather than moving through a transition, and the queue term of queueing theory as against the service term | a parked thread or process, which is suspended for different reasons and by something other than the work |
| **walk** (noun) | one run of this procedure under one declared frame — so *in this walk* means *under this frame*, and bounds scope | a **walkthrough** (IEEE 1028), which is a review meeting; a **Gemba walk**, which is going to look at the work in person |
| **trace** | — **not used here at all** | the runtime record of one request reconstructed from telemetry, measured after the fact. This procedure is design-time. It reasons about what each level *could* be measured on; it measures nothing |

Where *trace* is the word that comes to mind, say **walk**. "Trace the flow" sends a reader looking
for telemetry that does not exist.

---

## The two tests, in order

Everything below rests on these. Run them in this order; the second is meaningless before the first.

**Normalise the candidate before testing it.** Both tests are asked about a *name*, and a name can
be dressed to look like any level. Sources nominalise constantly — *document upload*, *credit
decisioning*, *income verification* — and a noun that came from a verb will read as an ability and
land at capability, taking half the step level with it. So before either test, restate the candidate
as a sentence about the case: *the applicant uploads documents*, *the lender decides*. If it will
not restate that way, it is probably not on the path at all, which is itself the answer Test 1
wants. The mirror case runs the other way — a capability named after the product that delivers it
(*instant card issuance*, shipping as `instant-issuance-svc`) reads as a deployable and lands at
component. Test the thing, not the label the source gave it.

### Test 1 — Is it a position the case reaches?

> Can you sensibly ask **"has the case reached it yet?"**

- **Yes** → it sits on the case's path. It is a **stage** or a **step**: a state the case sits in is a
  stage, an act between two such states is a step. **A container the case sits in is not a
  position.** *Has the application reached the underwriting queue?* is sensible, and the queue is
  still the mechanism holding the case, not the state it is in — the stage is *awaiting
  underwriting*, and the queue, if it runs anywhere, is a component. Ask what became true of the
  case, not where it is being held. Go to Step 4, which cuts them from the walk.
- **No — the question is malformed** → it is not a position on the path. Either it is a flow, or it
  is off the path entirely; the next paragraph separates those two before Test 2 runs.

**The flow is not reached by this test**, and asking it of one comes back malformed for the same
reason: the case is inside the flow the whole way, because the flow *is* the path rather than a
position on it. Step 3 shows the frame has already named it.

**A flow that is not the frame's own is `set aside`, not a capability.** *Servicing* under an
origination frame comes back malformed, is not restartable, and reads as an ability — so a literal
run of Test 2 lands it at capability, which Step 2 calls wrong. Check first whether the candidate is
a flow: if it is, and it is not the one the frame declared, it belongs to a different walk. Record
it `set aside`, naming the frame that would make it a flow.

*"Has the application reached document upload?"* — sensible. A step, however much *document upload*
sounds like an ability once it is written as a noun. *"Has the application reached loan origination?"* —
malformed; the application is inside loan origination the whole way. Off the path.

### Test 2 — For anything off the path: is it a thing that exists in an environment?

> **Is there a running instance of it somewhere** — something deployed, or a vendor running it on
> your behalf? Could you restart that instance?

Do not soften this into *does it have an owner*. A policy has an owner, a form has an owner, a team
has an owner, and none of them runs anywhere. Paging is an illustration of this, not the test:
you can page the underwriting team, and a team is still **Set aside**. What you cannot do is restart
one. Paging a team to pick up a stalled case is dispatch, and is not the same thing as alerting on
how long that team takes — Step 6 rules the second one out.

**Restartability is the usual sign, not the rule.** The rule is failure inheritance: **if a component
requires it and fails when it is absent, wrong or late, it is an external dependency** — whether or
not anything about it can be restarted. A nightly rate file that arrives from another system is not
a thing you restart, and a component that cannot price without it inherits its failure exactly as it
would from an API. Ask what breaks when it is not there.

And a role is **set aside** because a person is not a thing in an environment — not because of
anything to do with restarting. Do not run the restart question at a human and reason from the
answer.

- **No, and it is an ability** → **capability**. An ability is not a thing you can restart. A
  promise about *how well* an ability performs is not itself an ability — it is a service level
  target, and it goes to **Set aside** below. The time note after this test is where that is settled.
- **Yes** → a **component** or an **external dependency**. Step 6 separates those two, and returns
  a third outcome the test cannot see: a thing that runs but performs no step in *this* walk, which
  is `set aside` with its evidence.
- **Set aside** — neither of the above → it belongs to none of the six, unless it is the frame's own flow, which Step 3 has
  already named. A policy, a rule, a team, a role, a form, a document, a service level target, a
  regulation, a contract, a report, a metric, a meeting — the list does not close, and does not need
  to: real, named constantly by sources, and not a level here. Forcing it into the nearest level is how
  *the credit policy* ends up recorded as something the business is able to do, and how *decide
  within a day* ends up recorded as an ability rather than a promise about one.

  **Say which kind of thing it is.** `set aside` is the largest class on real material, and a
  policy, a target and a person doing the work are not the same kind of thing at all — recording
  them under one undifferentiated label repeats, at the biggest bucket in the draft, the collapse
  this whole procedure exists to prevent. Every `set aside` row carries a **Kind**: `role`,
  `rule or policy`, `target`, `form or document`, `team`, or `other`.

  **What that buys, which is the reason it is worth a field.** A step performed by a person has its
  performer recorded as a `set aside` row of kind `role`, bound to that step — which is how a human
  performer is recorded, and the only way it is recorded. That makes two standard questions
  answerable by counting rather than by reading: the proportion of steps no person touches, and
  which steps are performed by people and are therefore candidates for automation. Neither is
  computable from a draft where the underwriter and the credit policy carry the same label.

  **Set it aside in the open, not out of the draft.** On messy material this is usually the largest
  class — a real source names far more policies, teams, forms and targets than it does levels — so
  a draft that merely omits them cannot be checked, and no two drafts are comparable. Record each as
  a row with Level `set aside`, carrying its evidence and, where it is useful, what it attaches to:
  *the credit policy*, `set aside`, evidence *policy document §7*, attaches to *score against
  policy*. A reviewer can then see what you saw and disagree with where you put it.

**Why two tests and not one.** The six levels are three of one kind and three of another. Flow,
stage and step sit on the case's path — the flow is the whole of it, a stage or a step a position
along it. Capability, component and external dependency are not on the path at all: a capability is
what the path is **for**, and a component or external dependency is **what performs** it. A single
test cannot separate three groups. The split itself is business architecture's: what a business is
able to do is modelled separately from how work moves, precisely so that one can be re-implemented
without restating the other.

**What Test 2 deliberately permits**, which a cruder "does it survive the vendor changing" test
throws away:

- **Capabilities may carry time.** *Same-day settlement*, *next-day delivery*, *real-time
  authorization*. The time is the whole point where the business sells it — that is the ability.
  Where the time instead arrives as a commitment attached to an ability the business already holds
  — *we will decide within a day* — it is a **service level target** on that capability and not a
  capability itself. It falls to **Set aside** above: record the capability, record the target as `set aside`,
  and say you did.
- **Capabilities may be bound to a vendor, scheme or regulator.** *Accept a given payment method*,
  *issue cards on a given network*. Often exactly what the business sells. You cannot restart
  "accept a given payment method", so it is still a capability.

---

## Step 0 — Declare the frame. Do not skip it and do not infer it silently.

Five declarations, written on the artifact as **outputs**.

| Declaration | What it is |
|---|---|
| **The case** | The individual thing that travels. One loan application. One payment. One order. Not a system, not a team. |
| **The delivering application** | The application, or applications, that deliver the capability being walked — named. Step 6 separates component from external dependency entirely on membership of this, so leaving it unstated makes every verdict at that level turn on a choice nobody recorded. Where several deployables share the work, name the set. |
| **Whose expectation** | The party counting on this to happen, named. |
| **The starting event** | Where that party's expectation begins. |
| **The ending outcome** | Where that expectation is satisfied, or definitively is not. |

**Two of these can be the same word, and are not the same thing.** A loan *application* is a case;
the origination *application* is software. Where the case's own name collides like this, write *the
case* and *the delivering application* rather than either bare noun, and the rest of the draft stays
readable.

**The start and end are not free choices — the expectation sets them.** Everything below is relative
to this, and nothing in the source obliges you to state it. A walk that begins where the
source material happens to begin, and ends where it happens to end, produces a flow whose boundary
is an artifact of the document. A walk bounded by the expectation produces one whose boundary means
something: it starts when somebody began counting on an outcome and stops when they got it or
did not.

**The rule applied — where the walk starts and ends.**

| Reading from | Wrong | Right |
|---|---|---|
| Architecture documents | Start: *the document opens with the intake API*. End: *the last diagram in it* | Start: *the applicant submits and begins waiting on an answer*. End: *funds released, or declined* |
| A process document or SOP | Start: *underwriting receives the file*. End: *underwriting sends it to closing* | The same start and end as above — the applicant was waiting before underwriting saw it, and still waiting after |
| A strategy deck | Start and end read off *loan origination* itself, with no case named | Stop. No case is present. Draft the capability alone and say the rest would be fabricated |

Add a chapter and the first boundary moves. Reorganise the department and the second one moves.
Neither event changed what the applicant was waiting for.

Two consequences follow from this and nothing else in the procedure justifies them:

- **It is why stages are named as states reached** rather than as activities performed. The
  segments of the walk are positions between *"they are counting on it"* and *"they have it"*, and
  positions are states.
- **It is why the capability is the anchor.** A stakeholder does not expect a particular flow to
  execute; they expect the business can do a thing. The flow is the means, and means change — a new
  path, a new service, a re-platform. An expectation tied to the flow is orphaned by every
  re-implementation. Tied to the capability it survives.

Every assignment below is relative to these five. The same activity is a capability under one frame
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
| Source code | components, external dependencies, individual calls as "steps" | stages — they live in waits and handoffs, invisible in a call graph |
| Architecture documents | components and external dependencies | the case's path; everything on the timeline |
| A strategy deck | capabilities | everything beneath them |
| Interview notes | stages and steps | components, and often the capability |

**Those four are common cases, not the set.** A ticket history, a database schema, a contract, a
training deck, a recorded conversation, a regulator's filing — all are source material, and the
table cannot list them. What generalises is the rule behind it: **every source is a view taken for
some other purpose, so each one over-supplies the levels it was built to describe and is silent on
the rest.** Work out which way yours leans and say so. A schema will hand you state and no acts at
all; a contract will hand you obligations and targets and no mechanism; a recorded conversation will
hand you stages, exceptions and grievances in no order.

The case has a path regardless of which artifact you read it from. Anchor there.

**Write what happens to the case, in the case's terms.** Component names are Step 6.

**A step name must not carry its performer, and the reason is not tidiness.** The business set a
standard when a person did the work — whatever it qualified or quantified. Put a service or a model
in that place and the business expects the same thing, to the same standard. *The file is reviewed*
survives that swap; *the underwriter reviews the file* does not, because the performer is welded
into the claim. Let the expectation get rewritten every time the allocation changes and you have
destroyed the only before-and-after you had — there is then no way to ask whether the automation met
the bar the person was held to.

**Both halves hold at once, and dropping either one is a misreading.** The name is durable; the
allocation is material. *Which* performer does the work decides everything below the business line
— where the measurement point sits, what the remedy is, who gets woken — and Step 6 turns entirely
on it. What it never decides is what the business asked for.

**The rule applied — writing in the case's terms.**

| Reading from | What you read | The step's name | Where what you read goes |
|---|---|---|---|
| Source code | *`CreditService.evaluate()` is invoked* | *The application is sent for a credit decision* | Evidence — the call site is what proves the step exists |
| Architecture documents | *The record passes from the intake service to the decision service* | *The application is sent for a credit decision* | Evidence, and Binding once Step 6 names those two components |
| A process document | *The processor completes the verification worksheet* | *The application's income and assets are verified* | Evidence — cite the section |
| Interview notes | *Then I look it over and push it to the underwriter* | *The application is checked and handed to underwriting* | Evidence — cite who said it |

**This is the one pair that is not wrong-against-right.** The left column names the performer or the
machinery, which is never the step's *name* — and is exactly what a later reader needs when they go
looking for the thing itself. Both columns are kept. The sentence is how the step is named; what you
actually read is how it is found again.

## Step 2 — Name the capability

Ask what the whole path is **for** — what the business is thereby able to do — then apply Test 1 and
Test 2 to confirm what comes back is off the path and an ability. The two tests classify a candidate;
they do not produce one, and reading it off the path is where it comes from. What you have is a
capability: what the business is able to do, named independently of how it is built.

**The rule applied — naming the capability.**

| Reading from | Wrong | Right |
|---|---|---|
| A system inventory | *The loan origination system* — a deployable, not an ability | *Loan origination* — what the business is thereby able to do |
| An org chart | *Underwriting* — a department | *Loan origination*. The department is Test 2's *Set aside* |
| The walk itself | *Pull the credit file* — one step lifted a level | *Loan origination* — what the whole path is for, not one act inside it |
| A strategy deck | *Lending* — true of the firm, broader than this path delivers | The narrowest ability this walked path actually delivers |
| A stated commitment | *Same-day decisioning* | A service level target on the capability. Test 2's *Set aside* |

The first two fail Test 2: a system can be restarted, a department is not an ability. The third
fails Test 1 — you can ask whether the case has reached it. The fourth and fifth are abilities, just
not this path's.

**One name or several.** Step 2 usually returns one. Step 7 routinely returns several, because a
source names abilities more freely than a path delivers them. Neither count is wrong, and they do
not have to match — what Step 7 compares is whether the same abilities appear on both sides, not how
many. Partial overlap is the common case and is recorded as partial overlap: the ones both routes
reached, then the ones only one did.

Hold it. You will derive it a second time in Step 7 and keep any disagreement.

## Step 3 — The flow is already decided

Once the frame is declared, **the flow is the frame**. The case, its starting event and its ending
outcome name exactly one intended flow. There is no separate judgement to make about *which* flow.

**What the flow row is for, given there is nothing to judge.** It is what every stage and step binds
to, and it is where the ordered path is stated once — the stage order, and which of them run in
parallel or loop back. Without that the draft holds a set of stages and no sequence, and the
sequence is the thing the walk was performed to find. A flow row that only restates the frame and
carries no order has not earned a level.

This dissolves the argument about whether something is a flow or a stage of something larger.
Underwriting is a stage if origination is the frame and a flow if underwriting is the frame. Both
are correct, and the frame — which is written down — says which.

**The rule applied — the flow is the frame.**

| Reading from | Wrong | Right |
|---|---|---|
| The source's own headings | Three flows — *intake*, *underwriting*, *closing* — because the document has three chapters | One flow, *originating a loan*, because the frame declared one case and one expectation |
| A workflow tool | The flow named after the tool's process definition | The flow the declared frame names, whether or not a tool models it that way |
| A process document | *Underwriting* named as the flow, because it is the part the document describes | *Underwriting* is a stage under this frame. It is a flow only when a frame makes it one |

There is nothing to judge here. If a candidate flow does not match the frame, the frame was wrong
or the candidate is a stage — go back to Step 0 rather than carrying two answers forward.

## Step 4 — Stage boundaries fall where the case parks, or passes a point of no return

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

**The rule applied — where a boundary falls.**

| Reading from | Wrong | Right |
|---|---|---|
| Source code | A boundary at every wait: *waiting on the bureau call* · *waiting on the retry* · *waiting on the write* | A boundary where the case sits with nothing moving it: *awaiting credit decision* · *awaiting conditions cleared* |
| A workflow tool or system of record | A boundary at each of the thirty statuses the tool exposes | Boundaries where the case actually parks, saying which statuses were merged into each |
| Interview notes | A boundary wherever the person paused in telling it | Boundaries at the parks they described, whether or not they paused there |

The first turns a five-stage flow into forty — a retry is the act still working, and nobody has put
the case down. The second inherits someone else's routing design: status fields are built to drive
a queue, not to record where work waits.

**Name each stage by the state the case has reached**, not the activity performed — *awaiting
appraisal*, *decision recorded*, *funds released*. A stage must answer *"where is this case right
now?"* for a case in flight. If your stage names cannot, you have written activities and collapsed
two levels.

**What the separation buys, and the reason to defend it.** Keeping the resting positions apart from
the acts decomposes elapsed time into waiting and working. That split is the whole of flow
efficiency, and in most business work the waiting term dominates by an order of magnitude — a model
that collapses stage into step cannot see it at all, and will report a process as slow without ever
being able to say that almost none of the time was spent working. Process notations and workflow
boards generally do collapse them; formal models of work — Petri nets, state machines, queueing
models — keep them apart by construction, for this reason. The reason is in Step 0: the walk runs between *they are counting on it* and *they have
it*, so every segment of it is a position, and positions are states.

**This inverts a standing convention, deliberately, and only for stages.** Verb-first naming is the
rule for process *activities* in BPMN and in process-classification frameworks, and a reader who
knows those will see a contradiction unless it is said plainly: steps here are activities and are
named as such; stages are not activities and are not. The same inversion is already conventional one
discipline over — a Kanban board names its buffer columns as states for exactly this reason, so that
*where is this card now* has an answer, and shipment status vocabularies do the same. Where a setting
expects verb phrases at this level, note the difference rather than treating a naming convention as a
modelling error.

**The rule applied — how a stage is named.**

| Reading from | Wrong | Right |
|---|---|---|
| Source code or architecture | *Perform appraisal* · *Review documents* · *Underwrite* — activities | *Awaiting appraisal* · *Documents reviewed* · *Decision recorded* |
| A process document or org chart | *Underwriting* · *Processing* · *Closing* — the department that handles it | *Awaiting underwriting decision* · *Conditions cleared* · *Funded* |
| A system of record | *In the loan origination system* · *In the pricing engine* — where the record currently sits | The state the case is in, which outlives the system holding it. The system goes in Evidence — it is where the state is recorded |

Ask *where is this case right now?* of *perform appraisal* and there is no answer for a case in
flight. The other two answer, but with something that is not about the case: a department can be
reorganised and a system replaced without any case changing state. Name stages after either and the
model dies when they do — which is the argument Step 0 already made about tying an expectation to
the means rather than the capability.

**Two results that look wrong and are not:**

- **Work that never parks yields one stage for the whole flow.** A card authorization of two hundred
  milliseconds, one service, nothing queued — one stage is correct, not degenerate.
- **Work that parks constantly yields many stages.** A mortgage file parks at dozens of points
  because it has dozens of waypoints. If a smaller number is wanted for reporting, make that
  aggregation explicit and say which stages were merged. Do not suppress boundaries to hit a count.

## Step 5 — Steps are the acts between parks

One act, one outcome, that either happened or did not.

**Floor: one outcome the business would recognise, that either happened or did not.** Do not go
below it. Clicks, field validations and internal function calls are not steps — and neither is a
call from one of the application's components to another. *Pull the credit file* is one step whether
one component performs it or four; the hops are mechanism, and mechanism is what the two levels
below record. Splitting a step because the work crossed a service boundary puts deployment structure
onto a line that is meant to carry business outcomes.

**The rule applied — the floor on a step.**

| Reading from | Wrong | Right |
|---|---|---|
| Source code | *Call the bureau adapter* → *adapter calls the bureau* → *adapter returns the file* | *Pull the credit file* |
| A user interface | *Click submit* · *Validate the postcode* · *Persist the draft* | *Submit the application* |
| A process document | *Send the conditions letter* · *Send the first reminder* · *Send the second reminder* | *Clear the outstanding conditions* |
| Interview notes | *I pull it up* · *I check the income against the paystubs* · *I tick the box* · *I tell the processor* — four steps, because four things were said | *Verify the applicant's income* — one step. The other three are how the person did it and how they said so |

The first splits one business outcome across a service boundary. The rest go below anything the
business would recognise as having happened at all — a chase is not an outcome, it is the same
outcome still not arrived.

A step **may** contain a wait if something is actively working through it — Step 4's test, applied
downward.

**An irreversibility boundary can fall inside a step, and does not split it.** Step 4's third cut
fires where the case passes a point of no return, which is often mid-act — the commit, the
disbursement, the filing. Splitting the step there would manufacture two halves that the business
does not recognise as having separately happened, which this floor forbids. Record the boundary on
the stage side and leave the step whole. The two cuts genuinely cross, and that is the clearest
reason stage and step are different levels rather than two names for one.

## What each level makes obtainable

The point of cutting the walk this way is that each side of the cut can be observed in a different
manner, and neither substitutes for the other. This is not a measurement design — no indicators, no
thresholds, no alerting — only what each level physically yields.

**At a park, nothing is running, so there is nothing to instrument.** What exists instead is the
bracket: the case arrived at one moment and left at another. That gives how long it sat, how many
cases are sitting there now, and how old the oldest one is — obtained from state changes, not from
inside any component. **At an act, something is running, so you instrument the performer**: rate,
failures, duration, saturation, from inside the thing doing the work.

**That assignment decides the three kinds of health without anyone having to choose.** Business
health is almost entirely parks — *are cases moving, and is any of them aging past what the party
was promised* is not answerable from application telemetry at all. Application and technology
health are almost entirely acts. And **business impact is counted at parks**, because a park is
where you can count *cases*: four hundred applicants still waiting, not four hundred failed
requests. Which is also the honest form of an impact claim — the count of parties whose experience
crossed a threshold is real and obtainable; the reputational damage it stands for is real and is
not.

**It also finishes the human step.** A person's work sits between two parks. You cannot instrument
inside it and should not try — but the parks either side bracket it completely, so the step is
measured without being penetrated. That is how a step performed by a person is fully measurable and
still not something to page on.

**And it is the reason a walk beats two dashboards.** A park growing abnormally is very often the
first visible sign that an act broke: the symptom surfaces where the cases pile up, the cause lives
in the thing that stopped working. A model that holds both on one path can get from one to the
other. Two separate views cannot, however good each one is.

## Step 6 — Components and external dependencies

Both passed Test 2: things that exist in an environment. Separate them by **whether they are part
of the application**.

| | Test | What to bind it to |
|---|---|---|
| **Component** | It performs a step, and **it is part of the delivering application.** | Bind each one to the step or steps it performs. A component that performs no step in this walk is out of scope for this frame — record it as `set aside`, with its evidence, rather than dropping it. |
| **External dependency** | A component **requires** it and **inherits its failure** — or it performs a step with no component in front of it — and it is **not part of that application**. It can only be called, waited on, or failed over. | Bind each one to the component that requires it, or to the step it performs directly. |

**What the split is worth, stated as what you do at three in the morning.** A component is
something a technology team can change — the remedy is a code or configuration change they own. An
external dependency is something they cannot change — the remedies are retry, fail over, degrade,
cache, or escalate through whatever contract exists. Two different answers to the same question, and
the reason this is two levels rather than one field: the field would be read past, and the answer
decides who is woken and what they can usefully do.

**A step performed by a person has no technology remedy, and must not be paged on.** Its duration is
measurable — the systems bracket it, handing off at the start and picking the case back up at the
end — and it is worth measuring, because a person taking twice as long as usual is often the
*symptom* of a technology fault somewhere else. But the duration itself is a staffing and capacity
fact. An alert on it wakes someone who cannot restore it, which is how alert fatigue starts. Measure
it, report it, route it to whoever owns the work — never to whoever owns the systems.

**The line is membership of the delivering application, not technology, and not the company boundary.** A database platform
supported by a platform team is an external dependency even though it sits inside the same firm —
the application consumes it, it is not part of it. A vendor's API is an external dependency for the
same reason — the same reason, not a different one, which is the point. **Do not reach for
*first-party* and *third-party* here.** Those words are defined by who owns the thing, so they split
the population on the company boundary, which is exactly the line this rule refuses. A library compiled into the application's own deployable is neither — it is part
of the component, which is where every build tool on earth will disagree with you.

**The rule applied — component or external dependency.**

| Reading from | Wrong | Right |
|---|---|---|
| Architecture documents | The database platform as a **component**, because it sits inside the company | The database platform as an **external dependency** — the application consumes it, it is not part of it |
| Source code | The JSON library as an **external dependency**, because the build tool calls it one | The JSON library as part of the **component** it compiles into |
| Interview notes or an org chart | *The pricing team* as a component | The deployable that team operates, where it performs a step. The team itself is Test 2's *Set aside* — and is Evidence for the component, being who named it |
| A vendor contract | *The credit bureau*, the company, as an external dependency | The bureau's API — the thing a component actually calls and inherits failure from |

**The same thing is a component in one walk and an external dependency in another, and neither is
wrong.** A platform team walking their own capability records that database platform as a component;
an application team consuming it records it as an external dependency. The verdict is relative to
the delivering application declared at Step 0, which is exactly why that declaration exists — and
why an outsourcing decision, or a team taking over a system, changes the level without anything
about the software changing. Two drafts under different declarations are not comparable here, and a
draft that did not declare cannot be checked at all.

**How many teams build a component does not enter the test.** One deployable may be built by one
team or by ten, and it is one component either way. The unit is the application, not the team —
which is why the question *whose is it* never has to be asked about people.

**A step performed by a person has no component, and that is a complete answer.** *The underwriter
reviews the file.* *The notary witnesses the signing.* A real step — it happened or it did not, it
produced something or it did not — with nothing in an environment performing it. Record it with no
component bound and say that is why. The performer is a role, and Test 2 has already ruled that
roles are set aside, not levels. Inventing a component to fill the column and dropping the step because
the column would be empty are the two failures, and a business walk that silently loses its manual
steps is describing the systems rather than the work.

**The rule applied — a step performed by a person.**

| Reading from | Wrong | Right |
|---|---|---|
| Source code | *Underwriter reviews the file* → component *Underwriting Service*, invented to fill the column | *Underwriter reviews the file* → Binding `n/a`, with a `set aside` row of kind `role` naming the underwriter and pointing at this step |
| Interview notes | Component: *the underwriter* — the role recorded as the thing that performs it | a `set aside` row of kind `role`, bound to the step. The role is not a level, however constantly the source names it |
| Any source | The step dropped, because the component column would have been empty | The step kept, with the empty column stated as the answer |

**An external dependency can perform a step with no component in front of it.** Where the applicant
signs through an e-signature vendor and the application holds nothing in that step, there is no
component to bind to. Bind the dependency to the step itself and say that no component mediates it.
Forcing a component into the gap invents one that nobody operates.

**This is where code-sourced drafts over-produce.** Code names every module, client and library it
touches, and a model reading it will return all of them. Most are not components in this model:
a component performs a step in *this* walk. If you cannot name the step it performs, it is out of
scope for this frame. **Out of scope is not deleted.** Record it `set aside` with the evidence that
named it, so a reviewer can tell the difference between thirty modules you read and excluded and
thirty you never opened — which is the difference between a scoped draft and an incomplete one.

**And where narrative sources under-produce.** Interview notes and strategy decks name almost no
components. Do not manufacture them — record the level as a single `undetermined` row saying what
source would settle it. A level with no rows at all reads as a level nobody looked at.

## Step 7 — Derive the capability twice, and keep the disagreement

You have a capability from Step 2, read off the path. Now do it again independently: **read
candidate capabilities directly from the source** — what does this organization say it is able to do.

**The independence has to be built, not intended.** *You* are the second derivation here, not some
later human reviewer — this constrains how you run, not how anyone checks you. A pass that already
holds Step 2's answer will agree with it, and the agreement will mean nothing — the comparison returns concurrence by
construction, and disagreement, the outcome this step exists to make reachable, can no longer arise.
So derive the source side in a pass that has not seen the path side: a separate context, a separate
session, or the source side first with the walk withheld. This is the software reflexion model's own
constraint — a model read from the source is compared against a model derived some other way, and
deriving the second from the first makes the comparison tautological.

**The rule applied — deriving it twice.**

| Reading from | Wrong | Right |
|---|---|---|
| The context that produced Step 2 | The second derivation agrees, having been shown the first | The source side derived in a pass that never saw the path side |
| A source naming a different ability | The two smoothed into one line that reads cleanly | Both recorded, and the disagreement stated as a finding about the source |

An agreement produced by a reader who already held the answer is not evidence, and it costs the
step the only outcome it exists to reach.

- **They agree** → record once, note both routes produced it. The strongest assignment in the draft.
- **They disagree** → **record both and say so.** Do not resolve it silently. The disagreement is
  information about the source, not an error in the draft.

**There is no adjudication step here, and its absence is deliberate.** Most paired-derivation
practices arbitrate — a third reader breaks the tie, a voter picks the majority, a senior reviewer
rules. Those exist to produce one trustworthy output from two attempts at the same known answer.
This does not: there is no known answer, and the two routes are reading different things. Residual
disagreement is a property of the source material, which is the stance independent double coding
takes when it reports how far two coders diverged instead of averaging them away. Arbitrating here
would destroy the only finding the step exists to produce. If a downstream use needs one answer, it
picks one — with both still on the record.
- **One path serves several capabilities** → common and correct. Order-to-cash delivers selling,
  collecting cash, and giving the customer visibility. List all of them.
- **One capability served by several paths** → also correct. Straight-through settlement and
  settlement via an adjuster are two flows delivering one capability. Do not merge them.

---

## What every assignment carries

Six fields. An assignment without them is an arbitrary choice that reads as an authoritative one.

**Level**, **Basis** and **Binding** take values from closed sets, listed below and nowhere else.
Name, Evidence and Alternative are free text. Keeping three of the six closed is
what lets a reader — or anything else that picks the draft up — count the `undetermined` rows
without reading them, and it costs nothing at drafting time.

These three are the only closed sets in this procedure. **Every other list in it is illustrative**
— the source kinds, the things that go to `set aside`, the *Reading from* column of every
demonstration table. Those name common cases so a reader recognises the shape; they are not
enumerations to match against, and a thing missing from one of them is not thereby excluded.

| Field | Closed set |
|---|---|
| **Level** | `capability` · `intended flow` · `stage` · `process step` · `component` · `external dependency` · `set aside` |
| **Kind** | on a `set aside` row only: `role` · `rule or policy` · `target` · `form or document` · `team` · `other`. `n/a` at every level |
| **Basis** | `attested` · `inferred` · `undetermined` |
| **Binding** | a named step, component, capability or flow · `none` · `undetermined` · `n/a` |
| **Order** | **one integer sequence across stages and steps together**, not a sequence per level · `parallel with <n>` · `loops to <n>` · `n/a` at the other levels, the flow row included: the order lives on the rows that are ordered, not restated on the flow |

| Label | Values | Why |
|---|---|---|
| **Frame** | the case, the delivering application, whose expectation, starting event, ending outcome | every assignment is relative to it — and without the delivering application, Step 6 cannot separate component from external dependency at all, so the draft cannot say whether a failing thing is yours to fix |
| **Evidence** | the specific thing you read — a call site, a section, a status enum, a named speaker. Where there is none: `none in source` if the material simply does not cover it, and `none exists` only where nothing could establish it at any effort. The first is somebody's backlog; the second is a limit, and reporting them with one word loses the difference | the assignment in the form the source gave it. A reviewer checks against it, and work that has to act on the draft needs the location rather than the sentence. Without it `attested` is an assertion about an assertion |
| **Basis** | `attested` — stated in the source or given by the declared frame, cite which · `inferred` — derived, say from what · `undetermined` — the source does not settle it | on messy input this is the line between a draft and a fabrication |
| **Alternative** | the reading you did not take, or `none`. **It may be that the thing is not one of the six at all** — that is a reading, and a common one | this is what a reviewer disagrees with; omitting it makes the draft uncorrectable |
| **Binding** | for a component, the step or steps it performs; for an external dependency, the component that requires it, or the step it performs where no component mediates; for the capability the walk delivers, that flow — an ability the source names but the walk does not deliver binds `undetermined`, which is what distinguishes the two kinds of capability row; for a step, `n/a` where a performer row points at it and `undetermined` where none does and none could be found — never `none`, because a step row does not name its own performer, the performer row points at the step | Step 6 demands it, and a component bound to no step is not a component in this walk |
| **Order** | the position of a stage or step along the flow, as a single integer sequence spanning both — the case meets parks and acts interleaved, so a sequence per level gives two ladders with no rung between them and the path cannot be rebuilt from the fields alone. `parallel with <n>` where two run at once and `loops to <n>` where the case can go back — those are the branching cases the limits section names, and they belong here rather than in prose | **without this the ordered path is not recorded anywhere.** Rows in a table have adjacency, which nothing declares meaningful, and a draft reordered by any consumer loses the one structure the whole model is about |

**`undetermined` is expected, not a failure.** A model with thin material that produces confident
assignments is worse than one that declines.

**The rule applied — choosing a basis.**

| Reading from | Wrong | Right |
|---|---|---|
| A thin source | Every row `attested`, on material that named three things | `attested` for those three · `inferred` for what follows from them · `undetermined` for the rest |
| Interview notes | `attested`, because a senior person said it with confidence | `inferred`, with that person named in Evidence. Confidence is not a citation; the speaker is |
| What everyone knows | `attested`, because nobody in the room would dispute it | `undetermined` — nothing in the material settles it, and the room is not the material |

A draft where everything is attested on thin material is not confident. It is unlabelled.

**And a complete draft must be distinguishable, on its face, from an unattempted one.** If every
level came back attested and nothing is undetermined, that is a valid and good outcome — say so
explicitly rather than letting silence stand for it. An instrument that cannot report the negative
finding cannot be trusted when it reports the positive one, and a blank reads as fine to everyone who
sees it.

---

## What this procedure goes blind to

Known limits, stated rather than discovered later. **Parallel work and loops are recorded in
Order** — `parallel with <n>`, `loops to <n>` — because they are structure inside the model, not
things outside it, and routing them to `set aside` would put in-model structure in the field
reserved for what is not a level at all. A changing unit of case is declared on the frame, where the
case is. What remains genuinely uncovered is named below and stays named: a limit that is stated
here and silently dropped in the draft is worse than one nobody knew about, because the draft looks
complete.

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

A plausible example, to show the shape.

Evidence citations below name arc42 sections, a convention for architecture documentation whose
numbered chapters (§3 context, §5 building blocks, §6 runtime) give a stable place to point at. Any
citation scheme works; what matters is that it lands on something a reader can open.

**Frame.** Case: one home loan application. Delivering application: the origination platform — the
API, the bureau interface and the decision service, which are built and deployed together. Whose
expectation: the applicant. Starting event: they
submit the application and begin waiting on an answer. Ending outcome: funds released, or the
application declined — the point at which they have their answer or definitively do not.

Note what the expectation boundary excluded. Everything the lender does after funding — servicing,
collections, the secondary market — is real work and is outside this walk, because the applicant
stopped waiting when the funds landed. A different party's expectation gives a different flow over
the same systems.

| Level | Kind | Name | Evidence | Basis | Alternative | Binding | Order |
|---|---|---|---|---|---|---|---|
| Capability | `n/a` | Loan origination | strategy deck p.3, and the walk itself | `attested` — named in the source, and reached independently by walking the path; Steps 2 and 7 agree | `none` | `n/a` | `n/a` |
| Capability | `n/a` | Price credit risk | strategy deck p.3 | `attested` — the source names it as an ability | **Steps 2 and 7 disagree and both are recorded.** Reading the source, this is named as a capability; walking the path, nothing delivers it inside this frame. The disagreement is a finding about the source, not an error to resolve | `n/a` | `n/a` |
| `set aside` | `target` | Same-day credit decisioning | service commitment, ops handbook §2 | `attested` — the commitment is stated | a **service level target** on *loan origination*, not an ability. Capability is the reading this rejects — Test 2's *Set aside* | attaches to *loan origination* | `n/a` |
| `set aside` | `rule or policy` | The credit policy | policy document §7 | `attested` — named throughout the source | a rule, not a level. Test 2's *Set aside* | attaches to *score against policy* | `n/a` |
| `set aside` | `role` | Underwriter | org chart; interview 2026-03-04 | `attested` — the handbook assigns the work to this role | could be `team` rather than `role` if the work is pooled and no individual owns a case | attaches to *clear the outstanding conditions* | `n/a` |
| Intended flow | `n/a` | Originating a loan | the declared frame | `attested` — given by the declared frame | `none` — the frame decides it | `n/a` | `n/a` |
| Stage | `n/a` | Submitted | status enum, `LoanApplication.java:41` | `attested` — the source names it as the entry state | `none` | `n/a` | 2 |
| Stage | `n/a` | Awaiting credit decision | bureau call site, `CreditClient.java:88` | `inferred` — the case parks on the bureau | could sit inside *submitted* if the bureau answers inline | `n/a` | 4 |
| Stage | `n/a` | Decision recorded | status enum, `LoanApplication.java:41` | `attested` — named in the source | `none` | `n/a` | 7 |
| Stage | `n/a` | Awaiting conditions cleared | ops handbook §4 names conditions; nothing shows parking | `undetermined` — conditions are mentioned, parking is not | may not be a distinct stage at all | `n/a` | 8 |
| Stage | `n/a` | Awaiting signature | callback handler, `SigningController.java:29` | `inferred` — the case parks on the applicant | could sit inside *awaiting conditions cleared* | `n/a` | parallel with 8 |
| Stage | `n/a` | Funded | status enum, `LoanApplication.java:41` | `attested` — named in the source | `none` | `n/a` | 11 |
| Process step | `n/a` | Submit the application | web form handler, `OriginationController.java:17` | `attested` — named in the source | `none` | `n/a` | 1 |
| Process step | `n/a` | Pull the credit file | `CreditService.evaluate()`, `CreditClient.java:88` | `attested` — named in the source | `none` | `n/a` | 3 |
| Process step | `n/a` | Score against policy | policy document §7; no call site found | `inferred` — from a policy the source references but no step performs | may be part of pulling the file if the bureau scores | `undetermined` — nothing in the source says what performs it | 5 |
| Process step | `n/a` | Record the decision | `DecisionService.record()`, `DecisionService.java:52` | `attested` — named in the source | `none` | `n/a` | 6 |
| Process step | `n/a` | Clear the outstanding conditions | ops handbook §4, which assigns it to the underwriter | `inferred` — the section assigns it to a person, and names no system | may be automated policy checks rather than a person | `n/a` — the *Underwriter* row points at it | 9 |
| Process step | `n/a` | Sign the disclosures | `SigningController.java:29`; ops handbook §5 | `attested` — named in the source | `none` | `n/a` | parallel with 9 |
| Process step | `n/a` | Release the funds | ops handbook §6; no call site found | `inferred` — the declared ending outcome, with no system evidence | may be performed outside the delivering application entirely | `undetermined` — nothing in the source says what performs it | 10 |
| Component | `n/a` | Origination API | inbound handler, `OriginationController.java:17`; no deployment manifest seen | `inferred` — implied by the entry handler, not named as a deployable | could be the same deployable as the bureau interface | performs *submit the application* and *pull the credit file* | `n/a` |
| Component | `n/a` | Bureau interface | arc42 §5 building block view; deployment manifest, `bureau-interface` | `attested` — named in the source | `none` | performs *pull the credit file* | `n/a` |
| Component | `n/a` | Decision service | `DecisionService.java:52` | `inferred` — not named as a deployable, implied by a step that records a decision | could be a module inside the origination API rather than a deployable of its own | performs *record the decision* | `n/a` |
| External dependency | `n/a` | The credit bureau's API | arc42 §3 external systems; vendor contract | `attested` — named in the source, and consumed rather than built here | `none` | required by *bureau interface* | `n/a` |
| External dependency | `n/a` | The e-signature vendor | arc42 §3 external systems | `attested` — named in the source | `none` | performs *sign the disclosures* — no component mediates it | `n/a` |
| External dependency | `n/a` | The application store | `none in source` — implied by every step, named by nothing; a schema would settle it | `undetermined` — the source does not say whether this is a separate store | may be internal to the decision service, and would then not be an external dependency at all | `undetermined` — no component names it | `n/a` |

Note the Evidence column against *pull the credit file*. The method name is not an error the draft
had to avoid — it is what makes the sentence next to it checkable.

**Note what the example declines to do.** Two rows disagree with each other and stay that way.
Five rows are `set aside` or `undetermined` rather than assigned. One capability is recorded as
unreachable by the walk that was performed. A draft with none of these on thin material is not a
better draft — it is one that did not report what it could not establish.

**Note what the frame did.** *Credit underwriting* is absent from the capability level, because under
this frame it is a position the application reaches — the one recorded above as *decision recorded*.
Take a different case — one credit file moving through the lender's risk operation, whose expectation
belongs to the risk officer — and underwriting
becomes the flow, with the ability to underwrite the capability it delivers. Both are right; the
frame is why.

---

## Prior art referenced

Named so the relevant knowledge can be loaded directly rather than reconstructed.

**What is borrowed and what is arranged.** Nearly everything below is established practice a working
practitioner will recognise by name, usually from more than one discipline. What is assembled here
is the arrangement: two rules from unrelated fields fused into one cut (Step 4), and a labelling
convention applied at far finer granularity than the disciplines it comes from apply it. One thing
has no name anywhere — screening a candidate by whether the reached-question *breaks* rather than by
how it answers. The distinction that test draws is old and well named; using malformedness as the
screen is this procedure's own, and is flagged rather than dressed up.

**Test 1 — the reached question**

- **Event versus activity** — PERT/CPM (1958) and milestone semantics: an event is reached or it is
  not, and has no duration. The distinction Test 1 turns on, by its oldest name
- **State versus attribute** — Harel statecharts (1987), UML state machines: what a thing *is in*
  against what is *true of* it
- **Category mistake** (Ryle, 1949) and **presupposition failure** (Strawson, 1950) — why a
  malformed question carries information rather than being an error. The screening move itself has
  no applied-discipline name; this is its underpinning, not its precedent

**Step 0 — the frame**

- **Case, and the case notion** — process mining (van der Aalst): the `case id` is the mandatory
  attribute of every event log, and choosing *what the case is* is the acknowledged hard part
- **Case handling** — van der Aalst, Weske & Grünbauer (2005): organising work around the case rather
  than around activities. Step 1's *walk the case, not the document* is that move
- **Workflow nets and soundness** — van der Aalst: a case as a token traversing the net, correctness
  stated per case. Test 1 asks that question
- **Workflow Management Coalition (WfMC) reference model** — case as process instance: what an engine instantiates and routes
- **CMMN (Case Management Model and Notation)** — OMG: *case* and *stage* as first-class modelled elements. Its stage is a nestable
  container of tasks, not a position reached — the nearest term and a real difference
- **Object-centric process mining** — van der Aalst: convergence and divergence where one case notion
  does not hold. The named limit *a changing unit of case* is this problem
- **Operational definition** — Bridgman (1927), Deming (1986): a measurement is meaningless until
  the procedure producing it is declared. Step 0's claim that two undeclared frames are not
  comparable is this, stated for classification
- **SIPOC and the DMAIC define charter** — the beneficiary and the boundary declared before analysis
  starts, not discovered during it
- **Value-stream scoping** — Rother & Shook (1999), Womack & Jones (1996): the customer defines
  value, so the customer sets where the stream begins and ends
- **GQM** — Basili & Weiss (1984): the viewpoint is declared before anything is measured
- **Function allocation** — human factors and systems engineering: system functions are specified
  independently of whether a human or a machine will perform them, precisely so the allocation can
  be revisited without rewriting the function. **Levels of automation** (Sheridan & Verplank;
  Parasuraman, Sheridan & Wickens) is the scale for that per-function decision
- **Business capability** — the BIZBOK Guide and TOGAF: what a business is able to do, modelled independently of
  how it is delivered. The split Test 2 turns on
- **ArchiMate** — the business / application / technology carving the step-to-component line follows;
  *Application Component* as the term meant here; the *realisation* relationship as the form Binding
  takes
- **C4 model** — container (Level 2) as the granularity meant by component here; Level 3 explicitly
  not; and its container-versus-external-system split
- **Twelve-Factor, Factor IV: backing services** — Wiggins (2011): the application "makes no
  distinction between local and third party services." The rule of Step 6, stated as doctrine, with
  the company-boundary exclusion explicit
- **System of interest versus operational environment** — ISO/IEC/IEEE 15288 and INCOSE: the same
  membership split in systems-engineering terms, also drawn without reference to who owns what
- **Bounded context** — Evans, domain-driven design: a term's meaning is bounded by the context that
  declares it. Step 0's frame is a bounded-context declaration, and *the same activity is a
  capability under one frame and a single act under another* is that claim
- **Value streams and process classification** — the APQC Process Classification Framework and value-stream practice: the verb-phrase
  naming convention at the stage level, noted in Step 4 as a difference rather than an error

**Step 4 — where the cut falls, and what the segment is called**

- **Queueing theory** — Kendall (1953); waiting time decomposes into queue time plus service time.
  A busy server is not a wait, which is the whole of *do not cut on waits*
- **Value-stream map grammar** — the cut falls at inventory and accumulation. Its delta: it cuts at
  every queue and has no irreversibility rule
- **Pivot transaction** — the saga pattern (Garcia-Molina & Salem, 1987; Richardson, 2018): the
  point after which the work cannot be compensated. The precise name for the third park
- **Commit point** — Gray & Reuter (1993): the same boundary in transaction terms
- **Buffer columns named as states** — Kanban (Anderson, 2010), where *where is this card now* is
  the stated purpose of the naming; and shipment status vocabularies (ANSI X12 214, GS1 EPCIS
  disposition), which name dispositions rather than activities for the same reason

**Step 7 — deriving it twice**
- **Place / transition** — Petri (1962) and the place/transition net: a token rests in a **place**
  and moves through a **transition**. Stage and step are those two, and the net is bipartite by
  construction — which is the strongest statement available that they are not a modelling
  preference but the two halves of one structure
- **Queue time against service time** — queueing theory (Kendall, 1953): waiting decomposes into
  time queued and time served. Stage is the first, step the second, and that is what makes the
  separation pay rather than merely be tidy
- **Accumulation as the cut** — value-stream mapping (Rother & Shook, 1999): the map breaks where
  inventory piles up, and the whole flow-efficiency calculation rests on it
- **Buffer columns named as states** — Kanban (Anderson, 2010), where *where is this card now* is
  the stated reason for the naming; and pipeline stages in sales and case management, which do the
  same thing in ordinary business use
- **Flow / stage / step** — the triple also appears as a monitoring vocabulary, with health
  composing upward; a naming precedent rather than a source of the distinction
- **Software reflexion model** — Murphy, Notkin & Sullivan: a model read from the source compared
  against a model derived some other way. Step 7's independence requirement is its constraint
- **Independent double coding and inter-coder reliability** — Cohen (1960), Krippendorff (1980):
  residual disagreement reported as a property of the material rather than averaged away. The
  closest match to recording the disagreement instead of resolving it
- **N-version programming** (Avizienis & Chen, 1977) and **IEEE 1012 / IV&V**: independence of the
  producing context, not merely of the person
- **Ambiguity detection by divergent independent reading** — Basili et al. (1996), IEEE 830: two
  readers diverging indicts the source document, which is Step 7's stance

**The labels, and reporting the negative**

- **Architecture Decision Record** — Nygard (2011): *Considered Options* is mandatory for the reason
  given here, that a reader who cannot see the rejected option cannot revise the decision
- **Design rationale** — IBIS (Rittel & Kunz, 1970) and QOC (MacLean et al., 1991): rejected
  positions retained as structure rather than discarded
- **ICD 203 analytic standards** and **Analysis of Competing Hypotheses** (Heuer, 1999):
  distinguishing sourced fact from analyst judgement, and retaining the hypotheses that failed
- **ISA 230 audit documentation** — the record must let an experienced practitioner with no prior
  connection reconstruct the work. The standard Evidence is held to
- **Negative control** — Fisher (1935) and assay validation practice: an instrument that cannot
  report the negative case cannot be trusted on the positive one
- **Nil return** — negative reporting in military, police and collection tasking: an explicit
  *nothing to report* exists so that silence is never ambiguous between *nothing there* and *nobody
  looked*
- **Explicit absent-data semantics** — FHIR `dataAbsentReason`, CDISC SDTM *not done* with a reason,
  and Codd (1986) on the two kinds of null: `undetermined` is a value, not a blank
- **Critical user journey** — Google SRE: a flow carrying business value, bounded by what a party is
  counting on. Step 0's frame is that bounding
- **Underpinning contracts and operational level agreements** — ITIL: the industry seam if external
  dependencies ever need splitting into third-party and other-team
