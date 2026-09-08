# Placing an order — what it does, what runs it, what you can see

**eShop · 2026-09-01** · subject pinned at `b4a40872` (`dotnet/eShop`, 2026-08-28) — **every line
number below is valid only against that revision**

**Produced under the rule set of that date, which is not the one shipped beside it.** The fact count
in *How this was produced* is that run's own; the current rules read more of the same tree and
report different totals. The document is kept as the run recorded it — what it shows is the
shape of the output and the two findings, not a number to reproduce.

A customer buys something and waits for it to arrive. This document says what that
business process flow is, in business terms; which code implements each part of it; and — for
each part — whether anyone could tell if it broke.

**Nobody has reviewed this.** Every business-level statement is a draft awaiting someone who owns
the business process. Almost every code reference was produced by a tool and resolves to a file
and line; the exceptions are marked where they occur.

**One thing to know before reading the agreement between the two halves.** The business stages
below were drafted *after* the code had been read, which is not how the method is supposed to
run. That makes the ten-of-twelve agreement between them **weak evidence, close to worthless** —
a draft written with the code in view is biased toward agreeing with it. What survives that bias
is the **disagreement**: the two stages below that are not what they appear to be. The run scored
itself as failing on exactly this point — [`JUDGING-SCORE.md`](JUDGING-SCORE.md), condition 2.

---

## The short version

**Twelve stages. All twelve exist in the code. Two are not what they look like — and they are not
broken in the same way.**

| | |
|---|---|
| Stages a business person would name | 12 |
| Present in this application | 12 |
| **Present, and does nothing** | **1 — taking the money** |
| **Present, works, and nothing calls it** | **1 — shipping the goods** |
| Stages where a signal could be produced | 11 |
| **Stages where no signal can be produced** | **1 — taking the money** |
| Stages currently watched | **Unknown — and this run cannot find out** |

**Both involve money or physical goods, and their defects are different.** The payment step *runs
and does nothing*: it decides success by reading a configuration setting, so no gateway is
contacted and nobody is charged. The shipping step *works and is never called*: `PUT /ship` does
exactly what it says, and nothing in this system ever invokes it.

**A topology view shows both as ordinary working stages**, because structurally they are. A
success rate placed on the payment step would measure the configuration setting rather than the
business.

---

## The journey

Read left to right: what the business calls it, what runs it, and whether you would know if it
broke.

| # | Stage of the journey | What runs it | Can you tell if it broke? |
|---|---|---|---|
| 1 | Customer chooses what to buy | `catalog` — the catalogue web addresses | Yes — requests and errors are countable |
| 2 | Customer holds items in a basket | `basket` — get, update, delete | Yes |
| 3 | **Customer submits the order** | `ordering` — `POST /` creates the order | Yes |
| 4 | Business acknowledges it | An *order submitted* announcement the web application picks up | Yes |
| 5 | Short window to change their mind | `orderprocessor` — a background worker runs the grace period | Yes |
| 6 | **Business checks the goods exist** | `catalog` answers *awaiting validation*, replies stock confirmed **or rejected** | Yes — and both branches are separate announcements |
| 7 | ~~**Business takes the money**~~ | `payment` — **reads a setting and announces the result** | **No — there is nothing to watch.** See below |
| 8 | Business confirms it is going ahead | `catalog` reduces stock · `webhooks` and the web application are told | Yes |
| 9 | ~~**Business picks and ships**~~ | `ordering` — `PUT /ship`, **which nothing in this system calls** | **No — nothing here performs or observes it** |
| 10 | Customer is told it shipped | An *order shipped* announcement to the web application and partners | Yes |
| 11 | Partners are told what happened | `webhooks` — dispatches to subscribed third parties | Yes |
| 12 | Cancellation and failure | `ordering` — `PUT /cancel`, plus payment-failed and stock-rejected announcements | Yes — three distinct branches |

**Every code reference above traces to a file and line**, listed in
`PHASE-3-6-RECONCILE-RULE-SELECT-OBSERVE.md`.

---

## The one thing a customer should know about this ordering business process flow

**Stock is checked after the customer has ordered, and before any money is involved.**

The chain is: order submitted → grace period → *is this actually in stock?* → **stock confirmed or
rejected** → payment. So a customer can complete a checkout, receive an acknowledgement, and then
have the order fail because the goods were not there — with no money having moved.

**Where that order comes from, since it matters.** It comes from **knowing how this kind of
business works** — stock is checked before goods ship, payment is taken before an order is
confirmed, the same way a credit request comes before closing documents in lending. It was
drafted that way before any code was read, and it is a **draft awaiting someone who owns this
business process** — labelled as one throughout.

**What the code contributes is different and equally necessary:** which of those stages actually
exist here, what implements each one, and which are hollow. That is the pairing this method
exists to perform.

**One thing the code cannot do, and an earlier version of this page implied it could.** It
cannot *confirm* that this business runs the stages in that order — reading source tells you a
step **can** hand to another, never that it **always** does. A working paper claimed the order
was "readable from the handler names", which was a model reading English in file names and
calling it evidence. The order stands on the business draft, where it always stood. Recorded in
[`VV-REPORT.md`](VV-REPORT.md) as I4.

That is a workable design and this document takes no position on whether it is the right one.
What it does say: **the stock rejection is a distinct, countable announcement, and whether
anything counts it today is precisely what this run could not find out** — it had no access to a
running system. If nothing does, a customer-visible failure is happening with no number attached
to it.

---

## What cannot be watched, and why that is the useful half

### Taking the money

The payment service receives the stock-confirmed announcement and decides the outcome like this:

> `if (options.CurrentValue.PaymentSucceeded)` — publish succeeded, else publish failed.

That is line 21 of
`PaymentProcessor/IntegrationEvents/EventHandling/OrderStatusChangedToStockConfirmedIntegrationEventHandler.cs`.
It reads a setting. The class takes an event bus, an options monitor and a logger — **no HTTP
client, nothing that could contact a gateway.** No authorisation, no capture. **A success rate
measured here measures the setting**, and under the configuration this application ships it would
read 100% regardless of whether the business could take money at all.

**Why this matters beyond a demo application.** The stage is structurally complete — the
announcement arrives, a decision is made, downstream services react correctly. **Every automated
check on this run passed, and none of them evaluates a stage**, so none could have caught this.
What found it was the method's ruling step asking *what does this code actually do* — asked here
by a model, not a person, and still awaiting anyone's ratification.

### Shipping the goods

`PUT /ship` exists and works — calling it marks the order shipped and publishes the announcement
stage 10 depends on. **Nothing in this estate calls it.**

**How that negative was established**, since every other claim here carries a citation and a
negative cannot. The clone was searched for the route, the command behind it, and the domain
method that performs it. Outside the ordering service the only callers are its own functional
tests, and the command handler carries a comment naming an administrator application that does
not exist in this repository. **That search is weaker evidence than the positive claims above** —
this run also holds eight outbound calls whose targets it could not resolve, and three projects
that sat outside its service map, so a caller could in principle hide there.

**What genuinely cannot be measured here is the physical part.** The system records *paid* and
records *someone said it shipped*; the stretch from marked-shipped to actually-delivered is
outside its knowledge entirely.

---

## How this was produced, and what each step contributed

| | The step | What it produced above |
|---|---|---|
| **1** | **Read the code with a tool** | The *What runs it* column. 135 facts, each with a file and line |
| **2** | **Draft the business layer from the industry's own order-to-cash reference model** | The *Stage of the journey* column |
| **3** | **Reconcile the two** | That ten stages line up, and which two do not |
| **4** | **Rule on each difference** | That the two mismatches are real holes in the application rather than a wrong draft — the finding about payment came from here |
| **5** | **Prune to what matters** | Nothing. One business process flow in scope, nothing to cut between |
| **6** | **Place signals, define healthy, assign owners** | The *Can you tell if it broke* column — and the two that cannot be produced |
| **7** | **Feed back from incidents** | Did not run — needs a production system with an incident history |

**The step that did the work here was step 4.** Steps 1 to 3 produced a topology in which payment
and shipping look like ordinary working stages. Only asking what each difference *means* separated
"a service exists" from "a service does something."

### One thing that makes this application unusual to read

**Most of this business process flow does not travel over web requests between services.** It
travels as announcements — one service publishes *the order's status changed*, others react.
Eighteen such handlers were found; **seventeen name a stage of this journey** — order started,
awaiting validation, stock confirmed, stock rejected, paid, shipped, cancelled. The eighteenth
belongs to a different business process flow, keeping the catalogue priced correctly.

**The tool that follows connections between services found the web calls and none of the
announcements.** It is checked against what the deployment file declares, and by its own
`reconciliation` block it recovered **three of the four declared connections** — including the call
that submits the order, which is stage 3. **The one it lost is the web application's connection
to the basket, which is stage 2 of this very journey.** So it is not confined to the periphery:
it reads one kind of connection well, misses one of those, and cannot see the kind that carries
most of this business process flow at all. Recorded as a defect in the tool, not the application.

---

## What this document does not establish

- **Whether anything currently watches any of these signals.** That needs an inventory from the
  monitoring platform. This run had no access to a running system, so every "yes" in the last
  column means *a signal could be produced*, never *someone is looking*.
- **What healthy means for any stage.** Expected order volume, an acceptable stock-rejection rate,
  how long a grace period should be — all business facts. No code produces them and this run does
  not invent them.
- **Who owns any of it.** A public reference application has no owners. The column is deliberately
  empty rather than plausibly filled.
- **How accurate the underlying patterns are.** The tool's own bookkeeping reports that no rule it
  used has completed precision evidence. The structure here is reproducible and citable; how often
  patterns like these are wrong has not been measured on this rule set.
- **One known miss, found by doing this.** The order being saved to the database — the most
  important write in the whole business process flow — was not extracted, because the rule matches one
  persistence idiom and this application uses another. Recorded and not fixed, because this run was
  a test of the instrument.

---

## Coverage accounting

Every element the run set out to account for ends either **covered** — established, with a
citation — or **gapped**, meaning it could not be determined, with the reason and what would
close it. Nothing is left silently unaccounted for.

| Element | Count | Covered | Gapped |
|---|---|---|---|
| Stages drafted | 12 | 12 — each bound to code with a citation | 0 |
| Stage-to-code bindings | 12 | 12 tool-produced — **2 of them also carrying a judgement** about
what the code means (stages 7 and 9) | 0 |
| Signals wanted, one per stage | 12 | 11 producible | **1 cannot be produced** — taking the money |
| Watched / unwatched dispositions | 12 | 0 | **12 gapped** — no access to a running system or its monitoring |
| Healthy definitions | 12 | 0 | **12 gapped** — nobody has stated what good looks like for any stage |
| Owners | 12 | 0 | **12 recorded unowned** — this application has none, and a plausible name would be worse than an empty column |
| Too-broken thresholds | 1 | 0 | **1 gapped** — needs an owner to say how much failure is too much |
