# Runbook for "Deliver the order"

One entry per proposed alert, then the stage's shared section. Each alert's runbook link ([ALERT.md](ALERT.md)) points at its own entry. The shared section holds what the alerts have in common and writes every test once; an entry names the tests it runs, bounded to its own cases and window. Generated from the register by `flow_outputs.py`: each test after the opening checks is a row of `failure-modes.csv`. State: draft, never rehearsed. Process steps are numbered within their stage, the same in every stage file.

- [Alert M301: Shipped orders not confirmed delivered within the expected time](#alert-m301-shipped-orders-not-confirmed-delivered-within-the-expected-time)
- [Shared section: Deliver the order](#shared-section-deliver-the-order)

## Alert M301: Shipped orders not confirmed delivered within the expected time

### What fired

**M301 Shipped orders not confirmed delivered within the expected time** is above the operators' threshold for longer than their window ([ALERT.md](ALERT.md)).

**The expectation it guards:** a shipped order not delivered within the expected time leaves the customer without the goods they expect (flows.csv F1, delivers). The record this alert needs does not exist yet: the code records nothing after Shipped, so a per-order delivery confirmation must be added before it can fire. The bound is the customer's expected delivery time, which no source states and the code sets no time limit for (expectations.csv e5; stages.csv ST4). Its runbook entry has no tests, and that is the finding, not an omission: tests come from the failures of the move a stage's cases wait on, and these wait on delivery, which no part of the application carries out (process step 4.2 has no lifecycle row; the code's last state is Shipped, Ordering.Domain/AggregatesModel/OrderAggregate/OrderStatus.cs:12). The stage's one recorded move, L14, tells webhook subscribers and does not move an order. Its cases go to the carrier, outside this runbook, until a delivery move and its record are added.

This measure is not emitted yet; deployed as written, the alert fires on No data until it is.

**Its cases:** those held in the stage past the time limit (the time limit in [ALERT.md](ALERT.md)). A case not past the time limit is not one of M301's.

**Window:** from when the oldest of its cases entered the stage, to now. The alert fires only once a case has waited past the time limit, so its cause can be as old as that: never read a test over only the time since the count began rising.

Check the triggers to escalate or declare an incident ([S8](#s8-escalate-or-declare)) at every step, not only at the end.

### Opening checks

Run T1, T2 and T3 ([S4](#s4-every-test-once)) over the window above: an open incident or known error, a planned window or change, and what changed since the window opened. Then T4: is the count falling?

### Contain first

No hold is needed: the cases M301 counts are still in the stage, and nothing more is done to them while they wait.

### Its tests

No record to count: Tests come from the failures of the move a stage's cases wait on, and these wait on delivery, which no part of the application carries out: the code's last state is Shipped.

### Restore, close, escalate

[Restore (S6)](#s6-restore) · [Close (S7)](#s7-close) · [Escalate or declare (S8)](#s8-escalate-or-declare). Each test above says where its ending goes; escalation goes to the owner of the failing part.

## Shared section: Deliver the order

### S1. The stage on one page

**Configuration described:** An online store selling outdoor clothing and equipment to signed-in customers through a web front end (and a mobile app), with orders accepted, stock-checked, paid and shipped by back-end services joined by a message broker. Configuration described: the Aspire AppHost (eShop.AppHost/Program.cs:1-104) as deployed to Azure Container Apps (eShop.AppHost/Program.cs:6), with UseFoundry=true so the chat and embedding models are present (eShop.AppHost/Program.cs:80-85; Ollama is hard-coded off at :87-91); Postgres, RabbitMQ and Redis run as the application's own containers (eShop.AppHost/Program.cs:8-19). proposed: no source says which configuration runs in production; this is the fullest the repository defines. In this configuration the services run outside Development, so /health is not mapped (eShop.ServiceDefaults/Extensions.cs:115-125) and logs default to Information (Ordering.API/appsettings.json:4).

Flow **Fulfilling a customer's order**, one case: One order. Stage 4 of 4, **Deliver the order**. [STRUCTURE.md](STRUCTURE.md) draws the same steps and [MEASURES.md](MEASURES.md) measures them.

| Process step | Right outcome | From → to | Path | Done by | Needs |
|---|---|---|---|---|---|
| Process step 4.1: Webhook subscribers are told the order is shipped | (proposed) one post to each OrderShipped subscription | Shipped → Shipped | main | Ordering API, Webhooks API | Webhooks database, Event bus, Webhook subscriber endpoint |
| Process step 4.2: The order is delivered to the customer | (proposed) the customer has the goods |  |  |  | — |

**Expected of the stage.** A case that enters it leaves in one of these ways:


### S2. What is at stake

- **Order id ("Id")**: The only key that joins the order across services and to the customer
- **Order total (sum of Units x UnitPrice)**: Money the customer pays; value blocked while the order is stuck
- **Items and units (ordering."orderItems")**: What must be in stock and shipped
- **Buyer (ordering.buyers "IdentityGuid")**: Who is waiting and who is told
- **Delivery address**: Where the goods must arrive
- **Payment method (card number masked to the last four digits)**: What is charged
- **Declare an incident** when the impact threshold in the severity definition is crossed: an operator value, linked here.

### S3. Before you start

You need to be able to read each of these. A step you cannot run is a defect: record the runbook as *failed* and add the access to the access gaps.

- **Deployment, configuration and restart history** for Ordering API, Webhooks API.

### S4. Every test, once

Each test is written here once. An alert's entry says which it runs, in what order, over which window and on which cases; **Used by** names the alerts whose entries run it. Where a command asks for a time span in angle brackets, it is the window of the entry being worked.

| # | Test | Measures | Expected if this is not the cause | If it is | Ending | Used by |
|---|---|---|---|---|---|---|
| T1 | Is there an open incident, or a known error with a fix in flight, for Ordering API, Webhooks API, Webhooks database, Event bus, Webhook subscriber endpoint? | — | None | One is open | **Already known** | M301 |
| T2 | Is there a maintenance window on any of those parts, or a planned change to a timing the stage depends on (Process step 4.1: Webhook subscribers are told the order is shipped — Each post is bounded only by the standard resilience handler every HTTP client carries: each attempt 10 seconds, up to 3 retries, 30 seconds in all (Webhooks.API/Program.cs:3; eShop.ServiceDefaults/Extensions.cs:22-29; defaults: https://raw.githubusercontent.com/dotnet/docs/main/docs/core/resilience/http-resilience.md); the posts to all subscriptions go out together and are awaited together (Webhooks.API/Services/WebhooksSender.cs:5-10). No clock watches the message waiting in queue Webhooks (EventBusRabbitMQ/RabbitMQEventBus.cs:258-263))? | — | None | A window, or a setting changed on purpose | **Expected condition** (add *alert needs changing* if it should have been suppressed) | M301 |
| T3 | **What changed:** any deploy, configuration change or unplanned restart of Ordering API, Webhooks API, Webhooks database, Event bus, Webhook subscriber endpoint since the window of the alert that fired opened (its entry says when)? | — | None | A change lines up with the start | Roll it back through the change-approval path, or escalate to the owner of the part that changed (S8); then re-run T4 | M301 |
| T4 | Is the count of the alert that fired falling within one window (for a count of cases waiting, with the oldest only just past the time limit)? | M301 | Not falling | Falling within one window | **Self-healed** (mark *threshold or duration wrong*), for an alert that counts cases waiting. For one that counts cases that already left wrongly, falling means only that no new cases are arriving: go on and work the cases it counted | M301 |

**Ruled out by the design** (no test needed):

- FM131 Ordering API, outbox: row left unpublished (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the order's status is already written with the event row. Here, the paid or shipped event row stays at State 0 or 1 and nothing sends it later (IntegrationEventLogEF/Services/IntegrationEventLogService.cs:19-23). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM132 Ordering API, outbox: publish marked failed (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the order's status is already written with the event row. Here, the row is set to 3 and never retried (Ordering.API/Application/IntegrationEvents/OrderingIntegrationEventService.cs:27-31). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM133 Ordering API, outbox: relay not running (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the order's status is already written with the event row. Here, there is no relay to stop: the request that committed the status change publishes right after its commit (Ordering.API/Application/Behaviors/TransactionBehavior.cs:47-52). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM134 Ordering API, message: publish fails (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the stock reduction and the notifications do not touch the order (Catalog.API/IntegrationEvents/EventHandling/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-21; Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, Ordering API cannot hand the paid or shipped event to the broker; logged and the row marked failed (Ordering.API/Application/IntegrationEvents/OrderingIntegrationEventService.cs:27-31). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM135 Event bus, message: message not routed (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the stock reduction and the notifications do not touch the order (Catalog.API/IntegrationEvents/EventHandling/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-21; Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, no queue Catalog or Webhooks is bound for the event, so the broker drops it (EventBusRabbitMQ/RabbitMQEventBus.cs:97-102, 279-285; Catalog.API/Extensions/Extensions.cs:33; Webhooks.API/Extensions/Extensions.cs:22-23). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM136 Catalog API and Webhooks API, message: consumer not running (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the stock reduction and the notifications do not touch the order (Catalog.API/IntegrationEvents/EventHandling/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-21; Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, the event waits in queue Catalog or Webhooks until its consumer returns (EventBusRabbitMQ/RabbitMQEventBus.cs:258-263). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM137 Catalog API and Webhooks API, message: consumer fails on the message (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the stock reduction and the notifications do not touch the order (Catalog.API/IntegrationEvents/EventHandling/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-21; Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, the event is acknowledged and gone (EventBusRabbitMQ/RabbitMQEventBus.cs:170-180). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM138 Catalog API and Webhooks API, message: consumer slow (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the stock reduction and the notifications do not touch the order (Catalog.API/IntegrationEvents/EventHandling/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-21; Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, the event is handled late. Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM141 Webhook subscriber endpoint, call: callee down (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order (Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, the subscriber's endpoint cannot be reached; the post is retried up to 3 times on a transient failure by the standard resilience handler, then throws out of the handler and the event is acknowledged and gone (eShop.ServiceDefaults/Extensions.cs:22-29; EventBusRabbitMQ/RabbitMQEventBus.cs:170-180). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM142 Webhook subscriber endpoint, call: callee returns an error (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order (Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, the subscriber's error answer is not read (Webhooks.API/Services/WebhooksSender.cs:32), so nothing records it. Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM143 Webhook subscriber endpoint, call: callee slow or hangs (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order (Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, the post waits on the subscriber, up to the resilience handler's timeout (eShop.ServiceDefaults/Extensions.cs:22-29). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM144 Webhooks API, call: caller gives up mid-call (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order (Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, a post that outlasts the resilience handler throws out of the handler, and the event is acknowledged and gone (EventBusRabbitMQ/RabbitMQEventBus.cs:170-180). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM145 Webhook subscriber endpoint, call: callee answers wrongly (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order (Webhooks.API/IntegrationEvents/OrderStatusChangedToPaidIntegrationEventHandler.cs:8-17; Webhooks.API/IntegrationEvents/OrderStatusChangedToShippedIntegrationEventHandler.cs:8-17). Here, the subscriber's answer is not read (Webhooks.API/Services/WebhooksSender.cs:32). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM154 Event bus, needs: unavailable (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the broker does not answer and the publish of the paid or shipped event is marked failed, never re-sent (EventBusRabbitMQ/RabbitMQEventBus.cs:31-111; IntegrationEventLogEF/Services/IntegrationEventLogService.cs:19-23). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM155 Event bus, needs: slow (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the event arrives late. Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM156 Event bus, needs: full or out of capacity (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: a memory or disk alarm blocks the publish until it clears (https://www.rabbitmq.com/docs/alarms). Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM157 Event bus, needs: answers stale or wrong (L11, L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the broker holds messages, not data the moves read. Stock left unreduced is counted per order by M32; Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM158 Webhooks database, needs: unavailable (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order. Here, the webhooks database does not answer, the subscription read throws and the event is acknowledged and gone (Webhooks.API/Services/WebhooksRetriever.cs:5-8; EventBusRabbitMQ/RabbitMQEventBus.cs:170-180). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM159 Webhooks database, needs: slow (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order. Here, the subscriptions are read late and subscribers told late. Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM160 Webhooks database, needs: full or out of capacity (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order. Here, the shared postgres server refuses Webhooks API's connections, and the read fails as when it does not answer. Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM161 Webhooks database, needs: answers stale or wrong (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order. Here, the subscriptions are read from one server with no replica (eShop.AppHost/Program.cs:19). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM162 Webhook subscriber endpoint, needs: unavailable (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order. Here, the subscriber's endpoint does not answer; the post is retried and then throws, and the event is acknowledged and gone for every subscriber (Webhooks.API/Services/WebhooksSender.cs:5-10; EventBusRabbitMQ/RabbitMQEventBus.cs:170-180). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM163 Webhook subscriber endpoint, needs: slow (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order. Here, the subscriber answers late, holding the post up to the resilience handler's timeout. Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM164 Webhook subscriber endpoint, needs: full or out of capacity (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order. Here, the subscriber refuses the post, which is not read (Webhooks.API/Services/WebhooksSender.cs:32). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)
- FM165 Webhook subscriber endpoint, needs: answers stale or wrong (L12, L14): as a cause of paid orders waiting to ship (M14), of shipped orders not confirmed delivered within the expected time (M301), or of any change to the order: the notifications do not touch the order. Here, the subscriber's answer is not read (Webhooks.API/Services/WebhooksSender.cs:32). Subscribers not told are counted per order by M119 (paid) and M120 (shipped)

### S5. Causes the alerts share

One alert is proposed for this stage, so no cause is shared between alerts.

### S6. Restore

| # | Kind | Action | Expected result | If different | Approval |
|---|---|---|---|---|---|

### S7. Close

| Ending | Close |
|---|---|
| Nothing is wrong | Close as no impact. If the alert should not have fired, add *threshold or duration wrong*. |
| Expected condition | Link the window or change, then close. Add *alert needs changing* if it should have been suppressed. |
| Self-healed | Confirm the alert that fired is back under its threshold, then close. Mark *threshold or duration wrong*. |
| Already known | Link the incident, then close. |
| Broken — restore | After the S6 action, confirm the alert that fired is under its threshold, no case it counted is still affected, and new cases get through. Any that remain: back to its entry, T4. |
| Broken — cannot restore | Escalate (S8). Runbook mark: *worked*. |
| Outside this runbook | Escalate with what you have. Mark *gap*, or *failed* if a step could not be run. |

### S8. Escalate or declare

**Escalate** (hand over to the owning tier) when you cannot restore with S6; when a test ends in *Broken — cannot restore* (none); or when a remedy needs approval (use the change-approval path).

**Escalate to the owner of the part that failed**: the part the test that matched names. The owners as the register records them, with the date each was recorded; *not in the map yet* means the register names none, a gap to fill and not a reason to stop. Links to the on-call and change records are the operators' to add.

| Part | Owner (register) | As of | Responder (register) | Tests that end in escalation to it |
|---|---|---|---|---|
| Ordering API | proposed: the team that deploys the eShop AppHost, which ships every service and store together (eShop.AppHost/Program.cs:1-104); no source names a team | 2026-08-28 | proposed: that team's on-call; no source names one | — |
| Webhooks API | proposed: the team that deploys the eShop AppHost, which ships every service and store together (eShop.AppHost/Program.cs:1-104); no source names a team | 2026-08-28 | proposed: that team's on-call; no source names one | — |
| Webhooks database | proposed: the team that deploys the eShop AppHost, which ships every service and store together (eShop.AppHost/Program.cs:1-104); no source names a team | 2026-08-28 | proposed: that team's on-call; no source names one | — |
| Event bus | proposed: the team that deploys the eShop AppHost, which ships every service and store together (eShop.AppHost/Program.cs:1-104); no source names a team | 2026-08-28 | proposed: that team's on-call; no source names one | — |
| Webhook subscriber endpoint | proposed: each subscriber; no source names one | 2026-08-28 | proposed: each subscriber | — |

**Declare an incident** when a second team is needed, customers can see the problem, it is unsolved after a time box of concentrated work, or the impact threshold in S2 is crossed. Keep working the entry in parallel.

**Hand over:** the alert and the expectation it guards (its entry); the affected case ids by state; whether new cases are still affected now; which tests ran and what they showed; what was contained and what was done; when the window opened.

### S9. Outside this runbook

For the cases no test explained: escalate them with what you have (S8), and record *gap* (not covered) or *failed* (a step could not be run). Then go on with the next group of cases that still has some: an unexplained group does not end the walk for the others.

### S10. Links

Operator links to fill in, one per measure the tests read:


### S11. About this runbook

- **Owner:** not stated.
- **Last validated:** never. It has not been rehearsed cold.
- **To change it:** change the register (`lifecycle.csv`, `failure-modes.csv`, `remedies.csv`, `measures.csv`) and generate it again. Never edit this file.

| Test | Failure mode | Lifecycle rows | Part | Source |
|---|---|---|---|---|

<!-- bfo-generated-from {"flow": "F1", "stage": "ST4", "tables": {"about": "c9f8351ce577", "agent-system": "80df4fb74aa2", "capabilities": "f4fc19936bf8", "case-attributes": "3f95e73172bd", "expectations": "cd4f9fe286e7", "failure-modes": "132f9700adac", "flows": "a27265fffff5", "lifecycle": "440f83f4a1fa", "measure-gaps": "f3ef7b5dbcfd", "measures": "3c7ec5c71e65", "participation": "f08de4c4ac9a", "remedies": "2e9c1e60a265", "sources": "328a3c147492", "stages": "4595b2c6e50a", "step-impact": "4e066d413fd0", "steps": "e09fc039d65e", "subjects": "644d8b1712b7"}} -->
