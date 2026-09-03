# Phases 3–6 — reconcile, rule, select, specify observation

**Run:** `eshop-order-2026-09-01` · **Subject:** placing an order on `dotnet/eShop`

---

## Phase 3 — reconcile the accounts

Every stage drafted in Phase 2, classified against the extracted structure.

| # | Stage | Classification | What it binds to | Label |
|---|---|---|---|---|
| 1 | Customer chooses what to buy | **Convergence** | `catalog` · `CatalogApi.cs:21,26,31,36,41,52,73` — the catalogue read surface | `extracted` |
| 2 | Customer holds items until ready | **Convergence** | `basket` · `BasketService.cs:13,36,59` — get, update, delete basket. **`GetBasket` is at `:13`; the extractor cites `:12`**, where the match begins at the `[AllowAnonymous]` attribute above it | `extracted` |
| 3 | Customer submits the order | **Convergence** | `ordering` · `OrdersApi.cs:17` — `MapPost("/", CreateOrderAsync)` | `extracted` |
| 4 | Business acknowledges the order | **Convergence** | `webapp` · `OrderStatusChangedToSubmittedIntegrationEventHandler.cs:5` | `extracted` |
| 5 | Short window to change their mind | **Convergence** | `orderprocessor` · `GracePeriodManagerService.cs:15` → `ordering` · `GracePeriodConfirmedIntegrationEventHandler.cs:3` | `extracted` |
| 6 | Check the goods are available | **Convergence** | `catalog` · `OrderStatusChangedToAwaitingValidationIntegrationEventHandler.cs:3` → `ordering` · `OrderStockConfirmed…:3` / `OrderStockRejected…:2` | `extracted` |
| 7 | **Business takes the money** | **Divergence** | `payment` · `OrderStatusChangedToStockConfirmedIntegrationEventHandler.cs:3` exists — **and it charges nobody.** See ruling R1 | `extracted` structure, `proposed` reading |
| 8 | Confirm the order is going ahead | **Convergence** | `catalog` · `OrderStatusChangedToPaidIntegrationEventHandler.cs:3,20` (stock decremented) · `webhooks` · `OrderStatusChangedToPaidIntegrationEventHandler.cs:3` · `webapp` · `OrderStatusChangedToPaidIntegrationEventHandler.cs:5` | `extracted` |
| 9 | **Pick and ship the goods** | **Divergence** | `ordering` · `OrdersApi.cs:12` — `MapPut("/ship", ShipOrderAsync)`. **An endpoint nothing calls, not a process.** It is not unobservable: invoking it runs `Order.cs:130` → `:139` → `OrderShippedDomainEventHandler.cs:30`, publishing the announcement stage 10 consumes. **What cannot be measured is the physical fulfilment**, not the transition. See ruling R2 | `extracted` structure, `proposed` reading |
| 10 | Customer is told it shipped | **Convergence** | `webapp` · `OrderStatusChangedToShippedIntegrationEventHandler.cs:5` · `webhooks` same event | `extracted` |
| 11 | Tell partners what happened | **Convergence** | **Dispatch:** `webhooks` · `OrderStatusChangedToShippedIntegrationEventHandler.cs:16` — `sender.SendAll(subscriptions, whook)`; same shape for the paid event. **Subscription management** is a separate surface, `WebHooksApi.cs:13,35,66` | `extracted` |
| 12 | Handle cancellation or failure | **Convergence** | `ordering` · `OrdersApi.cs:11` · `webapp` · `OrderStatusChangedToCancelledIntegrationEventHandler.cs:5` · `ordering` · `OrderPaymentFailedIntegrationEventHandler.cs:3` · `OrderStockRejectedIntegrationEventHandler.cs:2` | `extracted` |

### Convergence reported explicitly, and then discounted

**Ten of twelve stages converge and two diverge. Read that number down, not up.** The Phase 2
draft was written after the extraction had been read, so the two accounts are not independent and
convergence is weak corroboration. What survives the discount is the **two divergences and the
recall defect below** — those are findings the contamination cannot manufacture, because a
contaminated draft biases toward agreement.

### The two open questions from Phase 2, answered from extracted evidence

- **Is there a grace period?** Yes. A hosted worker drives it (`GracePeriodManagerService.cs:15`)
  and the ordering service consumes its confirmation. The industry draft guessed this correctly.
- **Is stock checked before or after payment?** **Before**, and the two halves of that answer have
  different sources. **That stock is checked, and that payment happens, are extracted** — both
  stages bind to handlers at cited lines. **That one precedes the other is drafted**, from how the
  retail order-to-cash process works. An earlier version of this line said the chain was "readable
  from the handler names on both sides", which was a model reading English in class names and
  presenting it as corroboration from code. **Struck** — the ordering needed no such support, and
  the claim it borrowed is the one the tool-only rule forbids. What a code rule *could* legitimately
  add is that the stock handler publishes what the payment stage consumes, which says the two *can*
  hand over; that rule is not written. The customer-facing consequence is unchanged: the order can
  fail on stock *after* they believe they have ordered, and before any money is involved.

### A recall defect this reconciliation found, which no self-check caught

**The order being saved is the single most important durable write in this business process, and
it was not extracted.** `CreateOrderCommandHandler.cs:51` persists through
`_orderRepository.UnitOfWork.SaveEntitiesAsync(...)`; the rule matches `SaveChangesAsync`. The
extracted durable writes for the `ordering` service are its seed-data loader and nothing else.

**Every automated check passed on this run** — reach complete, both controls passed, recall 1.0 on
both declared populations. The declared populations are HTTP operations and gRPC methods; **no
declarative source enumerates durable writes**, which the coverage output states as `unmeasured`.
This is that `unmeasured` becoming concrete: the tool reported perfect scores while missing the
write that the whole business process exists to perform.

**Recorded as an INSTRUMENT finding. Not fixed — this run is in V&V mode.**

### A second thing the join got wrong, which its own output states

The join's `reconciliation` block reports **three of four declared connections recovered**,
and names the one it lost: **the web application to the basket service — stage 2 of this
journey.** A fourth row appears in `dependencies` with a null origin, so the array length is
four and the result is three. Recorded because a count taken from an array length rather than
from the tool's own verdict is the same defect class this directory keeps finding.

---

## Phase 4 — rulings on each difference (practitioner's draft)

Drafted in the accountable role's voice. `proposed`; every one needs a named person.

### R1 — "Business takes the money" is a divergence, and the draft is right

**Ruling: real hole in the application, not a wrong draft.** The payment service consumes the
stock-confirmed event and decides the outcome by reading a configuration flag —
`if (options.CurrentValue.PaymentSucceeded)` — then publishes success or failure. No gateway, no
authorisation, no capture, no money.

**Why this is worth a ruling rather than a shrug about a reference application.** The stage is
*structurally present*: the event arrives, a decision is made, downstream services react
correctly. Anything reading the topology sees a payment step and would place monitoring on it.
**A watch on this step would be green forever and would mean nothing.** That is the specific
failure this method exists to catch, and it is visible here only because the ruling step asks what
the code does rather than whether a component exists.

**Would ratify:** whoever owns payments.

### R2 — "Pick and ship" is an endpoint, not a process

**Ruling: real hole.** `MapPut("/ship", ShipOrderAsync)` is an API call someone or something must
make. Nothing in this estate makes it: no warehouse integration, no fulfilment consumer, no
scheduled job. The order sits paid until an external actor calls that endpoint.

**Consequence for the business process:** the longest and least visible part of a customer's wait
has no owner inside this system and no signal. **Would ratify:** whoever owns fulfilment.

### R3 — the missing durable write is a defect in the instrument, not in the estate

**Ruling: wrong draft on the tool's side.** The order is persisted; the rule did not match the
idiom. Nothing about the estate is wrong. Routed to the V&V report.
**Would ratify:** whoever holds the extractor.

---

## Phase 5 — select what matters

**Not exercised.** Phase 0 framed a single business process flow and its candidate list records
four others that were not taken. With one candidate in scope there is nothing to cut between, and
manufacturing a selection would be a fabricated result.

**One candidate surfaced during the run and does not join this subject:** *keeping the catalogue
priced correctly* — `webhooks` consumes `ProductPriceChangedIntegrationEventHandler.cs:3`, and a
price-change process crosses catalogue, webhooks and partners. Recorded as a seed for a later run.

---

## Phase 6 — specify observation

Per stage, at its boundaries. Signal dispositions are **exists and watched · exists and unwatched
· cannot be produced**.

**The watched / unwatched split cannot be settled by this run, and is not guessed.** It needs a
telemetry or dashboard inventory from the monitoring platform; Phase 0 recorded that no runtime
source was reachable. Every producible signal below is therefore **`gapped` on whether anything
watches it**, with that reason. Settling it by reading code is the failure the tool-only rule
exists to prevent.

| # | Stage | Signal, and its disposition | Healthy | Owner |
|---|---|---|---|---|
| 1 | Chooses what to buy | Catalogue request rate and errors — **exists** (HTTP surface, `CatalogApi.cs`) | `gapped` — no stated objective, no incident history | `unowned` |
| 2 | Holds items | Basket update rate and failures — **exists** (`BasketService.cs:36`) | `gapped` | `unowned` |
| 3 | Submits the order | Orders created — **exists** (`OrdersApi.cs:17`) | `gapped` — expected volume is a business fact no code produces | `unowned` |
| 4 | Order acknowledged | Submitted-notification published and consumed — **exists** (handler, `webapp`) | `gapped` | `unowned` |
| 5 | Grace window | Grace period elapsed and confirmed — **exists** (`GracePeriodManagerService.cs:15`) | `gapped` — the window's length is a policy | `unowned` |
| 6 | **Stock checked** | Stock confirmed vs rejected — **exists**, both branches are separate events | `gapped` — a rejection rate a business would act on is a business number | `unowned` |
| 7 | **Money taken** | **Cannot be produced.** No payment occurs; the outcome is a configuration flag (R1). A success rate here measures a setting, not revenue | n/a | `unowned` |
| 8 | Order confirmed | Paid-event fan-out to catalogue, webhooks and the web application — **exists** | `gapped` | `unowned` |
| 9 | **Picked and shipped** | **Cannot be produced.** Nothing inside this estate performs or observes fulfilment; the endpoint records that someone said it shipped (R2) | n/a | `unowned` |
| 10 | Told it shipped | Shipped-notification published and consumed — **exists** | `gapped` | `unowned` |
| 11 | Partners told | Webhook dispatch success and failure — **exists** (`webhooks` outbound) | `gapped` | `unowned` |
| 12 | Cancellation and failure | Cancelled, payment-failed and stock-rejected events — **exists**, three distinct branches | `gapped` | `unowned` |

**Too broken — how much broken is too much, per this business process flow.** `gapped`. It needs
an expectation source: a stated objective, an industry norm this business accepts, or an incident
history. This subject has none of the three, and there is no one to ask. **What would close it:**
a named owner stating an order-failure rate the business would act on, and who owns that number.

**`unowned` throughout is the rule working, not a shortfall.** A public reference application has
no owners; attaching a plausible name would be worse than a visibly empty column.
