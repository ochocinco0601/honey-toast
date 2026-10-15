# Proposed alert for "Ship the order": M14 Paid orders waiting to ship, and the oldest's age

**Stage 3 of 4:** Ship the order, in flow Fulfilling a customer's order. Its process steps: Process step 3.1: Stock is reduced by the order's units; Process step 3.2: Webhook subscribers are told the order is paid; Expected outcome: The order is shipped. When it fires, follow its entry in [RUNBOOK.md](RUNBOOK.md) (the runbook link below).

| | |
|---|---|
| **The question it answers** | **M14** How many paid orders are waiting to ship, and for how long? |
| **What it counts** | **M14** Paid orders waiting to ship, and the oldest's age: rows in 'Paid'; age from the order's OrderStatusChangedToPaid outbox row "CreationTime" (counted on cases) |
| **Why it is proposed** | **M14** a paid order still waiting has not been shipped when the customer expects the goods, and nothing moves it but a person recording the shipment: no timer watches Paid orders and nothing in the application calls the ship endpoint (lifecycle L13, recovery stranded). How long a wait is too long is the operators' dispatch target, not the register's. This measure is not emitted yet; deployed as written, the alert fires on No data until it is. |
| **Cases stranded** | A case is stranded, with nothing in the application to move it on, when one of these moves does not happen: L13 The order is shipped (The order stays in Paid. Nothing in the application calls the ship endpoint and no timer watches Paid orders: it is mapped (Ordering.API/Apis/OrdersApi.cs:12, 51-78) and has no caller in WebApp, ClientApp or any worker) |
| **Runbook link** | **M14** [its entry in RUNBOOK.md](RUNBOOK.md#alert-m14-paid-orders-waiting-to-ship-and-the-oldests-age) |
| **Grouping** | By the state the case is in: Paid. Its runbook entry groups the cases by state and works each state's tests. |
| **Threshold** | *Operator value, not set here.* For each measure, the value at which the alert fires. Whether it pages a person, opens a ticket or shows on a dashboard is the operators' decision. |
| **No data** | Each alert also fires when its measure cannot be counted: the query or search itself fails for longer than the window. A count of events that finds none in a window is zero, not missing data. A count fails when what it is read from is down, and then cases go wrong unseen. What it counts says where each is read. |
| **Time limit** | *Operator value.* For M14, how old a waiting case may be is the operators' value. |
| **Window** | *Operator value, not set here.* How long the condition must hold before the alert fires. What the design assumes about time: L11: No timeout: the stock is reduced when Catalog API consumes the Paid event from queue Catalog; no clock watches the message waiting there, and the queue sets no expiry (Catalog.API/IntegrationEvents/EventHandling/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-21; EventBusRabbitMQ/RabbitMQEventBus.cs:258-263); L12: Each post is bounded only by the standard resilience handler every HTTP client carries: each attempt 10 seconds, up to 3 retries, 30 seconds in all (Webhooks.API/Program.cs:3; eShop.ServiceDefaults/Extensions.cs:22-29; defaults: https://raw.githubusercontent.com/dotnet/docs/main/docs/core/resilience/http-resilience.md); the posts to all subscriptions go out together and are awaited together (Webhooks.API/Services/WebhooksSender.cs:5-10). No clock watches the message waiting in queue Webhooks (EventBusRabbitMQ/RabbitMQEventBus.cs:258-263); L13: No timeout: a person ships the goods and records it, and nothing in the application schedules or times that act (Ordering.API/Apis/OrdersApi.cs:12, 51-78) |
| **Symptom, not cause** | It fires on what happens to cases, not on any component's errors. Telling causes apart is the runbook's job. |
| **Exists today** | M14: no, proposed |

## Companion measures

Read by the runbook's tests, not proposed for alerting:

- M40 Ordering API requests by route and status, and their duration
- M42 Ordering API transaction failures, by command
- M81 Ordering database accepting connections
- M82 Long-running statements on orderingdb
- M80 Connections to the postgres server against max_connections
- M75 Identity API rate, errors, duration

<!-- bfo-generated-from {"flow": "F1", "stage": "ST3", "tables": {"about": "c9f8351ce577", "agent-system": "80df4fb74aa2", "capabilities": "f4fc19936bf8", "case-attributes": "3f95e73172bd", "expectations": "cd4f9fe286e7", "failure-modes": "132f9700adac", "flows": "a27265fffff5", "lifecycle": "440f83f4a1fa", "measure-gaps": "f3ef7b5dbcfd", "measures": "3c7ec5c71e65", "participation": "f08de4c4ac9a", "remedies": "2e9c1e60a265", "sources": "328a3c147492", "stages": "4595b2c6e50a", "step-impact": "4e066d413fd0", "steps": "e09fc039d65e", "subjects": "644d8b1712b7"}} -->
