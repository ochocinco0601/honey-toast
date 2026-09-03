# Ratification queue — `eshop-order-2026-09-01`

Every `proposed` cell from this run, grouped by the role whose yes it needs. A ruling is recorded
here — who, when, accept or reject — and the specification's labels flip to `ratified` from this
record. **This file is what makes `ratified` producible at all.**

**Every role below is unfilled.** `dotnet/eShop` is a public reference application; it has no
business behind it and nobody owns any of this. The rule is never to attach a plausible name, so
the names column is empty by design rather than by omission. **On a subject with real owners this
file is the product** — the specification is what they read, this is what they act on.

---

## For whoever owns payments — 1 item

| | Item | The drafted position | Ruling |
|---|---|---|---|
| **R1** | The stage *business takes the money* is present in structure and performs no payment. The handler reads a configuration setting and publishes success or failure | **Real hole in the application, not a wrong draft.** Anything reading the topology sees a working payment step and would monitor it; that watch would be green forever and mean nothing | *unfilled* |

---

## For whoever owns fulfilment — 1 item

| | Item | The drafted position | Ruling |
|---|---|---|---|
| **R2** | The stage *business picks and ships* exists as a web address (`PUT /ship`) that nothing in this estate calls | **Real hole.** The longest part of a customer's wait — paid to delivered — happens entirely outside this system's knowledge, with no signal and no owner | *unfilled* |

---

## For whoever owns the ordering business process — 14 items

| | Item | The drafted position | Ruling |
|---|---|---|---|
| **S1–S12** | The twelve stages, their order, and their boundaries | Drafted from the published order-to-cash process, then bound to code. **Expected failure profile: structurally right, locally wrong** — the boundaries between stages are what a reviewer corrects first | *unfilled* |
| **Q1** | Stock is checked *after* the customer has ordered and *before* any money moves, so an order can fail on stock after the customer believes it succeeded | Correct as a design, and **the most likely source of a complaint the business cannot see coming** — nothing counts stock rejections | *unfilled* |
| **Q2** | *Too broken* — how much of this business process failing is too much | `gapped`. Needs a stated failure rate the business would act on, and who owns that number | *unfilled* |

---

## For whoever owns the monitoring platform — 12 items

| | Item | The drafted position | Ruling |
|---|---|---|---|
| **W1–W12** | For each stage: is the producible signal actually watched today | `gapped` — this run had no access to a running system or a dashboard inventory. **Settling it by reading code is forbidden**, so it stays open until someone supplies the inventory | *unfilled* |

**Twelve `gapped` cells with one cause.** One telemetry inventory closes all of them, which makes
this the cheapest item on the queue and the one that most changes what the specification says.

---

## For whoever holds the extractor — 3 items

These are instrument changes, not facts about the subject. They outlive this run, which makes them
more consequential than the drafts above rather than less.

| | Item | The drafted position | Ruling |
|---|---|---|---|
| **I1** | The join follows call sites and addresses; this estate's business process travels as published events, so the join found four peripheral edges and none of the eighteen that matter | Build an event resolver — pair a published event type to the services declaring a handler for it. Both ends are already extracted facts | *unfilled* |
| **I2** | The order's own database write was not extracted — the rule matches one persistence idiom and this application uses another | Widen the rule, **and then re-sample its precision**, because widening voids the evidence | *unfilled* |
| **I3** | Judging condition 2 asks for a business account drafted without reference to the code; the skill's composition ruling means a single session has always read the extraction first. The condition is unreachable as written | Restate the condition, or make Phase 2 run before Phase 1 is read. **A ruling, not a run's call** | *unfilled* |

---

## What ratifying this would actually take

**Four roles, about half an hour each**, on a subject that had owners. The twelve monitoring items
are one question to one team. The twelve stage items are one review meeting with whoever owns the
business process. R1 and R2 are one question each to the teams that own those steps.

**That estimate is a drafted position too, and it is the one with the least evidence behind it** —
this run has never been put in front of anybody.
