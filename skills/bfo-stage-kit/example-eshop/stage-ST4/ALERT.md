# Proposed alert for "Deliver the order": M301 Shipped orders not confirmed delivered within the stage's promise

**Stage 4 of 4:** Deliver the order, in flow Fulfilling a customer's order. Its steps: Step 4.1: Webhook subscribers are told the order is shipped; Step 4.2: The order is delivered to the customer. When it fires, follow its entry in [RUNBOOK.md](RUNBOOK.md) (the runbook link below).

| | |
|---|---|
| **The question it answers** | **M301** How many shipped orders have not reached the customer within the delivery promise? |
| **What it counts** | **M301** Shipped orders not confirmed delivered within the stage's promise: per order, the time since its OrderStatusChangedToShipped outbox row "CreationTime" with no delivery confirmation for it; needs a per-order delivery record (a carrier's confirmation) the code does not keep: the last state is Shipped (counted on cases) |
| **Why it is proposed** | **M301** a shipped order not delivered within the stage's promise leaves the customer without the goods they expect (flows.csv F1, delivers). The record this alert needs does not exist yet: the code records nothing after Shipped, so a per-order delivery confirmation must be added before it can fire. The bound is the stage's promise, which no source states (stages.csv ST4, proposed:). Its runbook entry has no tests, and that is the finding, not an omission: tests come from the failures of the move a stage's cases wait on, and these wait on delivery, which no part of the application carries out (step 4.2 has no lifecycle row; the code's last state is Shipped, Ordering.Domain/AggregatesModel/OrderAggregate/OrderStatus.cs:12). The stage's one recorded move, L14, tells webhook subscribers and does not move an order. Its cases go to the carrier, outside this runbook, until a delivery move and its record are added. This measure is not emitted yet; deployed as written, the alert fires on No data until it is. |
| **Runbook link** | **M301** [its entry in RUNBOOK.md](RUNBOOK.md#alert-m301-shipped-orders-not-confirmed-delivered-within-the-stages-promise) |
| **Grouping** | By the state the case is in: `Shipped`. Its runbook entry groups the cases by state and works each state's tests. |
| **Threshold** | *Operator value, not set here.* For each measure, the value at which the alert fires. Whether it pages a person, opens a ticket or shows on a dashboard is the operators' decision. |
| **No data** | Each alert also fires when its measure cannot be counted: the query or search itself fails for longer than the window. A count of events that finds none in a window is zero, not missing data. A count fails when what it is read from is down, and then cases go wrong unseen. What it counts says where each is read. |
| **Age bound** | *Operator value.* For M301, the stage's promise: proposed: none assumed by the code; the carrier's delivery commitment would set one |
| **Window** | *Operator value, not set here.* How long the condition must hold before the alert fires. What the design assumes about time: L14: Each post is bounded only by the standard resilience handler every HTTP client carries: each attempt 10 seconds, up to 3 retries, 30 seconds in all (Webhooks.API/Program.cs:3; eShop.ServiceDefaults/Extensions.cs:22-29; defaults: https://raw.githubusercontent.com/dotnet/docs/main/docs/core/resilience/http-resilience.md); the posts to all subscriptions go out together and are awaited together (Webhooks.API/Services/WebhooksSender.cs:5-10). No clock watches the message waiting in queue Webhooks (EventBusRabbitMQ/RabbitMQEventBus.cs:258-263) |
| **Symptom, not cause** | It fires on what happens to cases, not on any component's errors. Telling causes apart is the runbook's job. |
| **Exists today** | M301: no, proposed |

## Companion measures

Read by the runbook's tests, not proposed for alerting:

