# Alert: cases past the promise in "Accept the order"

**Stage 2 of 4:** Accept the order, in flow Fulfilling a customer's order. Steps 3, 4, 5, 6, 7, 8. When it fires, follow [RUNBOOK.md](RUNBOOK.md).

| | |
|---|---|
| **The question it answers** | How many orders have waited longer than the promise to be accepted, and in which state are they held? |
| **What it counts** | **M13** Orders past the acceptance promise, by state: SELECT "OrderStatus", count(*) FROM ordering.orders WHERE "OrderStatus" IN ('Submitted','AwaitingValidation','StockConfirmed') AND now() - "OrderDate" > interval '2 minutes' GROUP BY 1 (the interval is the stage's proposed promise); in the postgres container (az containerapp exec --name postgres --resource-group <rg>) run psql -U postgres -d orderingdb (counted on cases) |
| **Grouping** | By the state the case is in: `Submitted`, `AwaitingValidation`, `StockConfirmed`. The state tells the responder which branch of the runbook to work. |
| **Threshold** | *Operator value, not set here.* The count above which a person is paged. |
| **No data** | The alert also fires when its measure cannot be counted (the query fails or returns no data for longer than the window). That happens when a part the count itself runs on is down, and then cases pile up unseen. Of the parts the stage's moves need, check which the count runs on: Ordering database, Event bus, Catalog database. |
| **Age bound** | *Operator value.* The stage's promise: proposed: 2 minutes from entering Submitted, read from the timing of L03, L04 and L06: a 1-minute grace period and up to 30 seconds to the next poll (OrderProcessor/appsettings.json:15-16; OrderProcessor/Services/GracePeriodManagerService.cs:17, 51), then 10 seconds before StockConfirmed and 10 before Paid (Ordering.API/Application/Commands/SetStockConfirmedOrderStatusCommandHandler.cs:22; Ordering.API/Application/Commands/SetPaidOrderStatusCommandHandler.cs:22). The stage is entered when the record is created, so a case's age in it is now minus "OrderDate" (Ordering.Domain/AggregatesModel/OrderAggregate/Order.cs:58) |
| **Window** | *Operator value, not set here.* How long the condition must hold before the alert fires. What the design assumes about time: L03: Grace period GracePeriodTime 1 minute, polled every CheckUpdateTime 30 seconds (OrderProcessor/appsettings.json:15-16; OrderProcessor/Services/GracePeriodManagerService.cs:17, 34, 50-52). Every run re-publishes for each order still Submitted (OrderProcessor/Services/GracePeriodManagerService.cs:54-61). The bus's retry policy (RetryCount 10, EventBusRabbitMQ/EventBusOptions.cs:6) never retries a failed publish: Execute is given an async lambda, so the failure lands in the returned task, not the call (EventBusRabbitMQ/RabbitMQEventBus.cs:57, 302-314; Polly's Execute overloads, https://www.pollydocs.org/api/Polly.ResiliencePipeline.html); L04: 10 seconds of simulated work before the status is set (Ordering.API/Application/Commands/SetStockConfirmedOrderStatusCommandHandler.cs:21-22). Ordering API consumes its queue with one consumer on one channel (EventBusRabbitMQ/RabbitMQEventBus.cs:246, 270-277), so these waits queue behind one another; L05: 10 seconds of simulated work before the status is set (Ordering.API/Application/Commands/SetStockRejectedOrderStatusCommandHandler.cs:21-22), queued behind the other waits as in L04; L06: 10 seconds of simulated work before the status is set (Ordering.API/Application/Commands/SetPaidOrderStatusCommandHandler.cs:21-22), on the same single consumer as L04 |
| **Why it pages a person** | Cases left by these moves are stranded, with nothing in the application to move them: L04 Stock is confirmed for every item of the order (The order stays in AwaitingValidation with nothing to move it: a failed publish is marked PublishedFailed and never sent again (Ordering.API/Application/IntegrationEvents/OrderingIntegrationEventService.cs:27-31; Catalog.API/IntegrationEvents/CatalogIntegrationEventService.cs:21-25; IntegrationEventLogEF/Services/IntegrationEventLogService.cs:19-23, 56-59); a consumer that throws still acknowledges the message, so it is gone (EventBusRabbitMQ/RabbitMQEventBus.cs:170-180); the poll re-sends only for Submitted (OrderProcessor/Services/GracePeriodOrdersRepository.cs:27). A message waiting in its queue for a stopped consumer moves on when the consumer returns); L05 The order is cancelled because an item is out of stock (The order stays in AwaitingValidation with nothing to move it: a failed publish is marked PublishedFailed and never sent again (Ordering.API/Application/IntegrationEvents/OrderingIntegrationEventService.cs:27-31; Catalog.API/IntegrationEvents/CatalogIntegrationEventService.cs:21-25; IntegrationEventLogEF/Services/IntegrationEventLogService.cs:19-23, 56-59); a consumer that throws still acknowledges the message, so it is gone (EventBusRabbitMQ/RabbitMQEventBus.cs:170-180); the poll re-sends only for Submitted (OrderProcessor/Services/GracePeriodOrdersRepository.cs:27). A message waiting in its queue for a stopped consumer moves on when the consumer returns); L06 Payment is taken for the order (The order stays in StockConfirmed with nothing to move it: Ordering API's publish failure is marked PublishedFailed and never retried (Ordering.API/Application/IntegrationEvents/OrderingIntegrationEventService.cs:27-31; IntegrationEventLogEF/Services/IntegrationEventLogService.cs:19-23, 56-59); Payment Processor's publish has no outbox and its failure throws out of the handler (PaymentProcessor/IntegrationEvents/EventHandling/OrderStatusChangedToStockConfirmedIntegrationEventHandler.cs:32), and every consumer acknowledges a message it failed on (EventBusRabbitMQ/RabbitMQEventBus.cs:170-180). A message waiting in its queue for a stopped consumer moves on when the consumer returns); L07 The order is cancelled because payment failed (The order stays in StockConfirmed with nothing to move it: Ordering API's publish failure is marked PublishedFailed and never retried (Ordering.API/Application/IntegrationEvents/OrderingIntegrationEventService.cs:27-31; IntegrationEventLogEF/Services/IntegrationEventLogService.cs:19-23, 56-59); Payment Processor's publish has no outbox and its failure throws out of the handler (PaymentProcessor/IntegrationEvents/EventHandling/OrderStatusChangedToStockConfirmedIntegrationEventHandler.cs:32), and every consumer acknowledges a message it failed on (EventBusRabbitMQ/RabbitMQEventBus.cs:170-180). A message waiting in its queue for a stopped consumer moves on when the consumer returns) |
| **Symptom, not cause** | It fires where cases pile up, not on any component's errors. Telling causes apart is the runbook's job. |
| **Exists today** | M13: no, proposed |

## Companion measures

Read by the runbook's tests, never paged on:

- M50 Grace-period releases published
- M52 Order Processor exits and restarts
- M51 Grace-period poll query failures
- M54 Grace period and poll interval in effect
- M53 Event bus start failures
- M92 Bindings on exchange eshop_event_bus
- M45 Queue Ordering: messages waiting and consumers
- M41 Ordering API messages it failed to handle
- M46 Ordering API messages of an event type it does not know
- M42 Ordering API transaction failures, by command
- M81 Ordering database accepting connections
- M82 Long-running statements on orderingdb
- M80 Connections to the postgres server against max_connections
- M90 Broker running
- M91 Broker resource alarms and headroom
- M43 Ordering outbox rows not published, by State
- M44 Ordering API publish failures
- M62 Catalog outbox rows by State
- M61 Catalog API publish failures
- M70 Payment Processor messages it failed to handle
- M72 Payment results published, by kind
- M63 Queue Catalog: messages waiting and consumers
- M71 Queue PaymentProcessor: messages waiting and consumers
- M60 Catalog API messages it failed to handle
- M83 Catalog database accepting connections
- M84 Long-running statements on catalogdb
- M85 Connections to the postgres server from catalogdb
