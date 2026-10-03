# What each level can report

The model's relation table says how the ordered levels connect. It does
not say what each one is *able to say* — which is the question that arrives the moment the
model has to appear on a screen, and the question a stakeholder asks first.

**Reporting is about executions, never about the record.** An intended flow is authored, not
measured; what carries a number is the observing of its runs. So every row below means *what
observing executions of this level tells you* — the observed side of the design/observe pair
the vocabulary already names.

These rows are read from what a level **is**. An ability has no executions. A traversal has a
beginning, an end, and a population of attempts. That is why business architecture assesses a
capability on a planning cadence and never monitors it, and why a service level indicator is
set on a journey. Nothing here is read off any register, schema or tool — those are
implementations of this.

## The form

**The level decides what a measure is counted on. The question it asks decides its layer.**
Business health asks whether the expectation is met. Business impact asks for how many cases it
is not, and what is at stake. Both are asked at the flow, the stage and the step, each over that
level's own scope. Component and external dependency measures answer a third question: why. A
layer is not a level, so an application or agentic measure can also be taken at a step, about
how its software did the work.

| Level | Runs | Counted on | Business health: is the expectation met? | Business impact: for how many cases is it not? | Why |
|---|---|---|---|---|---|
| Capability | no | Its flows, the ones that deliver it | Derived or asserted from its flows, and says which. Its own measure is coverage: how much of what it contains is modelled | Its flows' counts, kept per flow. A total only in a unit they share, labelled derived | |
| Intended flow | yes | Each case, start to end, or over any stretch between two points of the flow | Cases started, finished and still open; cases finished on time and right; cases still open past the promise | Cases wrong or late anywhere in the flow, qualified by what is at stake and by whether they move on or stay stranded | |
| Stage | yes | Each case, from entry to exit of the stage | Cases in it now, the age of the oldest, the time to get through, and how many are past the stage's promise | Cases wrong or late here, located here, qualified as for the flow. Projected separately: the cases still upstream that will reach it | |
| Process step | yes | One event per case | Did it happen for this case, and was what it produced right | Cases where it did not happen, or produced the wrong outcome | Application and agentic measures taken at the step, about how its software did the work |
| Component | yes | Requests, runs or resources | | | How the mechanism behaved, by its kind's set (below). It explains a business measure and is never one itself |
| External dependency | yes | Calls, from the calling side | | | Whether what the step required was available, on time, and what it answered. The step inherits what goes wrong with it |

**Health and impact both need the expectation stated.** That means what a right outcome is, for
the flow and for each step, and the time promise for the flow and each stage. Where none is
stated, count against one proposed from what the application does, as Rule 3 says. Asking
whether a flow met its expectation over a period also needs an objective: a target share of
cases over a window. The method names the objective; its value is for the operators to set.

**Volume is counted at the flow and the stage, and it is not health.** Volume means cases
arriving per hour, or per day. Projecting the cases still upstream needs it.

### Below the step: the sets a part can report

"Why" names a role, not a list. What a part can report depends on what kind of part it is,
and the field already has a named set for each kind. A part is complete when every set that fits
its kind has been asked about, not when one example of each has been listed. A set nobody asked
about is a gap; a set asked about with nothing to measure is an answer.

| Kind of part | The set to ask about | Source |
|---|---|---|
| Any part | Telemetry by type: metrics, events (deploys, configuration changes), logs, traces | MELT, the common observability shorthand |
| What any part runs on: its host, its pools, its database engine | Utilization, saturation, errors | USE (Gregg) |
| A service that answers requests | Rate, errors, duration; and saturation, the fourth golden signal | RED (Wilkie); golden signals, *Site Reliability Engineering* ch. 6 |
| A pipeline: a batch job, a polling reader, a message consumer | Freshness, correctness, coverage; and throughput, with lag, redeliveries and duplicates where it consumes messages | The first three: the SLI menu for data processing, *The Site Reliability Workbook* ch. 2 |
| A store, or a part that answers a step's question | Durability; and whether what it answered was right: timeliness, accuracy, completeness, validity | Storage SLI, same chapter; DAMA's data quality dimensions |
| An agent: software that makes a judgment call | Not a set of its own here: an agent is its own system of interest. See *The agentic stratum* below | |

**An external dependency is asked the same sets, from the outside.** The caller sees only what
it calls, so each set is measured at the calling side: was it available, how long did it take,
did it error or time out, was the call throttled, and was what it answered right. The SRE book
recommends measuring where the client sees it (ch. 4); calls to a system someone else runs are where
*Release It!* (Nygard) places most stability failures. Where the provider states a commitment,
the measure is read against it.

**Walked against the two examples on this page** (Bank of Anthos and the invented
home-lending example). Every component measure they draw falls into one of these sets: the ledger writer's
requests, errors and duration (service: rate, errors, duration); decision service outbox write
failures (pipeline: coverage); document service duplicate deliveries (pipeline: duplicates) and
latency (service: duration); agent run duration and fallback rate (the agentic stratum,
operational); disbursement release success rate (service: errors). The walk
also shows what neither example asks about: traces, deploy and configuration events, and the
right-answer set for the balance reader. The balance reader is the part whose wrong answer this
page uses as its example. **Neither example declares an external dependency**, so that row rests on
the field's sets alone and has no instance to walk.

### The agentic stratum: its own system of interest

An agent is software that makes a judgment call inside a step: it reviews a closing package and
decides whether funds can be released. An agent is in effect its own system of interest: the
thing being described is the agent itself, not the business flow around it (the term is
ISO/IEC/IEEE 42010's). So it gets a view of its own, with its own run, steps, parts and
dependencies, and joins the business map at one place: the step it performs or supports.

**Why it is separate.** Every set above rests on one contract: software either does the specified
thing or fails in a way the machinery can see. An agent breaks the *specification*, not the
machinery. Its specification is "exercise discretion well", so it can answer quickly, without an
error, and still decide wrong. No set above has a question for that.

**Still forming, and labelled so.** The sets above have been settled for years. This one has not:
the sources (the OpenTelemetry conventions for generative AI, OpenInference, the NIST AI Risk
Management Framework, vendors' evaluation taxonomies) are converging, not converged, so every
dimension below is provisional.

**The agent as a system.**

| Inside the agent | What it is | Examples |
|---|---|---|
| Its run | One decision, made for one business case | one closing package reviewed |
| Its steps | What one run does | plan the work; retrieve the case's documents; call a tool; write the answer; check it against policy |
| Its parts | What performs those steps | the code that sequences the steps; the decider (the model, its prompt and its rules, versioned together as a deploy is); the search index it retrieves from; its tools; the checks that block an answer outside policy |
| Its dependencies | What it calls and does not run | the model provider; tools and APIs run by others |

Which part does which step: the decider performs *plan the work* and *write the answer*, and calls
the model provider to do it; the search index performs *retrieve*; the tools perform *call a tool*;
the policy checks perform *check it against policy*. The sequencing code performs none of them: it
supports all five, in the model's sense of *supports*, by deciding which runs next.

**What it can report.**

| Question | Measures | Status | Where it joins the business flow |
|---|---|---|---|
| Correctness: was the call right? | Agreement with an answer key: a golden set, cases with known answers re-run per release; or a judge, a second opinion sampling live decisions | in the set, provisional | Why, beneath the step |
| Grounding: did it decide from the case's actual inputs? | Its answer checked against the inputs it claims to rest on | in the set, provisional | Why, beneath the step |
| Traceability: can the decision be reconstructed? | Which decider, which inputs, which steps | in the set, provisional | Why, beneath the step |
| Drift: is it still the decider that was vetted? | Today's inputs and decisions against the validated baseline | in the set, provisional | Why, beneath the step |
| Operations | Run duration, failed tool calls, cost per run, refusals, fallbacks to a person or a simpler rule (a fallback changes who decided), rate limits, how full its working context is | open: whether agents need an operational set of their own is still a question | Why, beneath the step |
| Candidates | Escalation: does it know when not to decide? Policy scope: did it stay within its authority? | candidates, not in the set | Open |

**Business health stays with the business.** The step the agent serves reports health the same
way as any step: one event per case, here the share of closing packages produced right. A wrong
package is a wrong case under Rule 3, counted in cases. The agent's correctness and grounding
explain that count, and sit beneath it.

**Walked against the invented home-lending example below.** Its agentic doc component carries two
measures, both operational: agent run duration and fallback rate. **Nothing measures whether what
it produced was right, either at the step it serves or beneath it.** A closing package missing a
required disclosure is a reportable event, and exactly the wrong-with-nothing-failing case; no
measure in the example would see it. The example also draws no parts or steps inside the agent,
so the system-of-interest view has no instance to walk.

## The three boundaries

Three lines cross the levels, and they are not the same kind of thing. Two are properties of the
world. The third is a habit of implementations, and it is worth seeing as a choice rather than
mistaking for a limit.

| Boundary | Between | Reads |
|---|---|---|
| Real | Capability and Intended flow | A capability is an ability — no executions, so nothing above here can be observed running. This is why a portfolio reports coverage, never health of its own. |
| Not real | Stage and Process step | Where measurement is usually made to begin. A stage runs and can be measured; keying measures to steps alone is a choice some implementation made, not a limit anyone found. |
| Real | Process step and Component | Above here a measure answers whether the business got what it expected. At and below it, what is produced is a diagnostic measurement, which explains an indicator and is never the business answer itself. |

## The levels, drawn on an open-source application

Bank of Anthos, sending a payment: an open-source sample banking application. Every component
below is a service in its public source; the stages and steps are named for what each achieves
for the payment.

**The business side, top down.** Line one: nothing above it runs.

```
Retail banking › Move money                      capability   the flow points up to it; coverage only
═══════════════════ nothing above this line runs ═══════════════════
Sending a payment                                flow         runs once per case; one case = one payment
   ├ Make the payment                            stage        counted in payments
   │  ├ Customer sends the payment               step         the payment is posted: the case exists from here
   │  ├ Bank checks the money is there           step         events, one per payment
   │  └ Bank moves the money                     step
   └ Show the payment                            stage
      ├ Customer's balance updates               step
      └ It appears in their history              step

   preconditions, not steps: signing in and loading the home page, which serve many payments
   not drawn here: the two form steps before the post (who gets paid, the amount), which a
   step-level model might draw as steps, but which happen before the payment exists
```

**Below one step.** Line two: business above, machinery below.

```
Bank checks the money is there                   step         was this payment's funds check right?
═══════════════════ business above · machinery below ═══════════════════
 ├ performs  Ledger writer                       component    requests, errors, duration
 └ supports  Balance reader                      component    answers "what is the balance?"; an
                └ reads  Ledger database         component    out-of-date answer makes the step wrong
 external dependency: none in this example. The ledger database is Bank of Anthos's own, so it is
 a component, not a dependency.
```

**Bottom up, where one part's failure reaches.** The Balance reader stalls:

```
Balance reader                                   component
 ├ performs  Customer's balance updates          step  › Show the payment › Sending a payment › Move money
 └ supports  Bank checks the money is there      step  › Make the payment › Sending a payment › Move money
```

The second branch is why *supports* is a link: nothing fails at the funds check, and payments are
still checked against a balance that is out of date.

## One instance, walked

Home lending — an invented lender that takes an application, underwrites it, produces the closing
documents, and releases the funds. One flow among several the lender runs; the others are not
described here.

| Level | Name | Assessed | What it can say |
|---|---|---|---|
| Capability | C0 Home Lending | yes | 1 flow modelled, of the several this lender runs |
| Capability | C1 Loan origination | yes | 1 of 4 sub-capabilities reached by a modelled stage |
| Intended flow | Originating a loan | yes | health and impact of the whole flow, in loans |
| Stage | ST1 Take the application | no | |
| Stage | ST2 Underwrite the loan | no | |
| Stage | ST3 Prepare the closing documents | yes | modelled, and no stage measure exists to report |
| Stage | ST4 Fund the loan | no | |
| Process step | 0 Decision recorded | yes | volume in per hour |
| Process step | 1 Handoff accepted | yes | pickup within 5 min |
| Process step | 2 Content gathered | no | UNDEFINED — recorded, with no business measure chosen |
| Process step | 3 Package assembled | yes | packages produced |
| Process step | 4 Package persisted | yes | completion rate |
| Process step | 5 Funding notified | yes | decision to funded — how long a borrower waits |
| Component | Decision service | yes | outbox write failures — why step 0 behaved as it did, never whether the business got its decision |
| Component | Document service | yes | duplicate deliveries, latency p95 — it performs four of the six steps |
| Component | Agentic doc component | yes | agent run duration, fallback rate |
| Component | Disbursement service | yes | release success rate |
| External dependency | none declared | no | The model says a component depends on an external dependency. This example attaches what a step requires to the step instead, as supporting components — so the rung exists in the model and has no rows here. |

A level that is **not assessed** is drawn as not assessed. An unassessed segment and a healthy
one must never render alike, because blank reads as fine.

## What this view exposes, and it is open

Every level above is measured in the field, by a named discipline — a capability is assessed on
a heat map, a journey carries an indicator against an objective, a stage and a step carry
durations and rates. **The relation table joins none of them to anything that holds a number.**
Its only crossing between the obligation half and the structural half is a diagnostic
measurement produced by a component that performs or supports a step, and a diagnostic is by its own
definition about the mechanism, not the outcome.

Goal-Question-Metric states the missing relation: a metric is defined *for an object*, and the
object is named in the goal. This model permits one object — Component. The vocabulary also
names an **observed flow**, the runtime counterpart of the intended flow, and the relation table
never joins it to anything, so the model has a
design-time half and no runtime half.

## From the levels to measures and impact

The form above says what each level can report. The working rules below say how a given measure
is placed, what it is evidence of, and how business impact is counted during an incident.

**They are what is known so far, not a standard.** They rest on the two examples on this page and are
expected to change. When a walk on a real flow disagrees with them,
that is a finding about the rules, to be weighed, not a flow to be bent to fit. Nothing here is a
gate: no draft, register or view is held back for failing to satisfy them.

**Protected assumption: business measures are about cases.** The rules below are revised when a
walk disagrees with them; this assumption is not. When an example seems to break it, the example is
reread. Business measures, health and impact alike, are about cases (see *Case* in the model's
vocabulary): each counts cases, times how long each case took, or adds up something
each case carries, such as the amount at stake. A measure that counts requests, messages or runs is
never a business measure. The same incident, two measures: "funding runs that failed last night"
counts runs, so it is not a business measure; "loans not funded because last night's run failed"
counts loans, so it is one.

**Rule 0: declare the frame first.** Whose expectation the flow serves, what the case is, where
the flow starts and ends, and which application delivers it. The case is one individual business
item: one payment, one application. It is never a system, a team, a batch or a request, and a flow
has one kind of case. The flow starts where the case first exists; a stage or step before that
point belongs to some other flow and is set aside for this one. Moving a case out of a stage is an
act, so it is that stage's last step, and the part that does it performs a step. A part of the delivering
application is a component whether it performs a step or only supports one; a part outside it is
an external dependency. A job that handles many cases per run or per poll, a nightly batch or a
polling reader, is a component; its runs are its own measure, shown as the cause under the cases
it failed to process.

**Rule 1: a measure's level is what it is counted on.**

| Counted on | Level | Example |
|---|---|---|
| Cases, between the flow's start and end, or between any two points of the flow | Flow, for that stretch | payments started, finished, still open; start-to-end time; confirmation to visible balance |
| Cases, between a stage's entry and exit | Stage | payments in the stage now; age of the oldest; time to get through |
| Events, one per case, at a step | Process step | one line per payment written to the ledger |
| Requests or resources | Component, or dependency | errors per request to a service; cache hit rate |

The step a measure is emitted at does not decide its level. A failure log written once per request
to a service is a component measure even though the request happens during a step. A handoff
between two components is a relationship, not a level: a measure on it is placed by what it counts,
like any other. Counting requests makes it a measure of the component whose code counts them;
counting one event per case makes it a step measure. A lag is a component duration, unless it is
counted per case, which makes it a flow measure for that stretch, and a stage's time in stage when
the stretch is a stage.

**Rule 2: first-hand or inferred.** Evidence stays **first-hand** across containment. A stage's
case count is first-hand about its flow for that stretch, and a step's events, one per case, are
first-hand about the stage and the flow at that point. Evidence becomes **inferred** only across
one of three links: a component **performs** a step; a part **supports** a step; a component
**depends on** a dependency. *Supports* is a link because a part that answers a step's question can
make that step wrong, not only make it fail: a stale balance served to a step gives a wrong answer
with nothing failing. A part with no such link to any step of the flow is set aside for that flow.
Counting cases at all needs the case's identifier where the count is taken; counting them from
start to end needs it in every system the case passes through.

*First-hand* and *inferred* are used rather than *direct* and *indirect*, which in measurement
practice mean a base measure against one computed from others; and not *traced*, which readers take
to mean telemetry.

**Rule 3: business impact is counted in cases.** Count the cases whose expectation is unmet, per
flow, in that flow's own unit. The expectation is that of the party Rule 0 names; a message the
application shows is evidence of it, never its definition. It is unmet in one of two ways. **Wrong:** the case gets an
outcome it should not have, such as a valid payment refused, or one accepted that the true balance
does not cover; a case can be wrong with nothing late and nothing failing. **Late:** a time bound has passed.
Count against the stated bound. Where none is stated, report that as a finding about the flow and
count anyway, against a bound drafted from what the application does, the timing its design
assumes, labelled proposed. A proposed bound is context for whoever owns the flow, never a gate on
counting. Qualify them by what is at stake for each (amounts, deadlines), and by whether they move on by
themselves once the cause is fixed or stay stranded until someone acts. Locate them by
stage. Project forward: the cases in earlier stages that will reach the failure point. Never add
counts across flows with different kinds of case, except in a unit they share (customers affected,
money at risk), and label such a total derived. Show the step, component and dependency measures
underneath, as the cause.

### What a register must hold for these rules to run

The rules decide which inputs must exist. A register is checked against this list, and what it
lacks is a finding about that flow: nobody has stated it.

| Input | Needed by |
|---|---|
| Whose expectation, the case, the start and the end, the delivering application | Rule 0 |
| Each stage's entry and exit criteria | Rule 1, stage counts |
| For each measure, what it is counted on and which thing it counts | Rule 1 |
| For each system the case passes through, whether it carries the case identifier | Rule 2 |
| The promise for the flow and for each stage: stated, or else a bound proposed from what the application does | Rule 3, counting late cases |
| What a right outcome is, for the flow and for each step | Rule 3, counting wrong cases |
| The objective, a target share of cases over a window: named here, set by the operators | business health over a period |
| Cases arriving per period, at the flow and each stage | Rule 3, projecting |
| The attributes that say what is at stake for a case | Rule 3, qualifying |
| The capability each flow sits under | the capability's coverage |
