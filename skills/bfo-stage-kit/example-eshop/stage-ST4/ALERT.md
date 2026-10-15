# Proposed alert for "Deliver the order": M301 Shipped orders not confirmed delivered within the expected time

**Stage 4 of 4:** Deliver the order, in flow Fulfilling a customer's order. Its process steps: Process step 4.1: Webhook subscribers are told the order is shipped; Process step 4.2: The order is delivered to the customer. When it fires, follow its entry in [RUNBOOK.md](RUNBOOK.md) (the runbook link below).

| | |
|---|---|
| **The question it answers** | **M301** How many shipped orders have not reached the customer within the time they expect? |
| **What it counts** | **M301** Shipped orders not confirmed delivered within the expected time: per order, the time since its OrderStatusChangedToShipped outbox row "CreationTime" with no delivery confirmation for it; needs a per-order delivery record (a carrier's confirmation) the code does not keep: the last state is Shipped (counted on cases) |
| **Why it is proposed** | **M301** a shipped order not delivered within the expected time leaves the customer without the goods they expect (flows.csv F1, delivers). The record this alert needs does not exist yet: the code records nothing after Shipped, so a per-order delivery confirmation must be added before it can fire. The bound is the customer's expected delivery time, which no source states and the code sets no time limit for (expectations.csv e5; stages.csv ST4). Its runbook entry has no tests, and that is the finding, not an omission: tests come from the failures of the move a stage's cases wait on, and these wait on delivery, which no part of the application carries out (process step 4.2 has no lifecycle row; the code's last state is Shipped, Ordering.Domain/AggregatesModel/OrderAggregate/OrderStatus.cs:12). The stage's one recorded move, L14, tells webhook subscribers and does not move an order. Its cases go to the carrier, outside this runbook, until a delivery move and its record are added. This measure is not emitted yet; deployed as written, the alert fires on No data until it is. |
| **Runbook link** | **M301** [its entry in RUNBOOK.md](RUNBOOK.md#alert-m301-shipped-orders-not-confirmed-delivered-within-the-expected-time) |
| **Grouping** | By the state the case is in: Shipped. Its runbook entry groups the cases by state and works each state's tests. |
| **Threshold** | *Operator value, not set here.* For each measure, the value at which the alert fires. Whether it pages a person, opens a ticket or shows on a dashboard is the operators' decision. |
| **No data** | Each alert also fires when its measure cannot be counted: the query or search itself fails for longer than the window. A count of events that finds none in a window is zero, not missing data. A count fails when what it is read from is down, and then cases go wrong unseen. What it counts says where each is read. |
| **Time limit** | *Operator value.* For M301, how old a waiting case may be is the operators' value. |
| **Window** | *Operator value, not set here.* How long the condition must hold before the alert fires. What the design assumes about time: L14: Each post is bounded only by the standard resilience handler every HTTP client carries: each attempt 10 seconds, up to 3 retries, 30 seconds in all (Webhooks.API/Program.cs:3; eShop.ServiceDefaults/Extensions.cs:22-29; defaults: https://raw.githubusercontent.com/dotnet/docs/main/docs/core/resilience/http-resilience.md); the posts to all subscriptions go out together and are awaited together (Webhooks.API/Services/WebhooksSender.cs:5-10). No clock watches the message waiting in queue Webhooks (EventBusRabbitMQ/RabbitMQEventBus.cs:258-263) |
| **Symptom, not cause** | It fires on what happens to cases, not on any component's errors. Telling causes apart is the runbook's job. |
| **Exists today** | M301: no, proposed |

## Companion measures

Read by the runbook's tests, not proposed for alerting:


<!-- bfo-generated-from {"flow": "F1", "stage": "ST4", "tables": {"about": "c9f8351ce577", "agent-system": "80df4fb74aa2", "capabilities": "f4fc19936bf8", "case-attributes": "3f95e73172bd", "expectations": "cd4f9fe286e7", "failure-modes": "132f9700adac", "flows": "a27265fffff5", "lifecycle": "440f83f4a1fa", "measure-gaps": "f3ef7b5dbcfd", "measures": "3c7ec5c71e65", "participation": "f08de4c4ac9a", "remedies": "2e9c1e60a265", "sources": "328a3c147492", "stages": "4595b2c6e50a", "step-impact": "4e066d413fd0", "steps": "e09fc039d65e", "subjects": "644d8b1712b7"}} -->
