# Proposed alert for "Place the order": M300 Checkouts that ended with no order

**Stage 1 of 4:** Place the order, in flow Fulfilling a customer's order. Its steps: Expected outcome: The order is placed; Step 1.1: The customer's basket is emptied. When it fires, follow its entry in [RUNBOOK.md](RUNBOOK.md) (the runbook link below).

| | |
|---|---|
| **The question it answers** | **M300** How many checkouts reaching Ordering API ended without their order being written? |
| **What it counts** | **M300** Checkouts that ended with no order: ordering-api log over the window, by request id: those with a 'Sending command:' line for the create command (Ordering.API/Apis/OrdersApi.cs:148-153) and no 'CreateOrderCommand succeeded - RequestId:' line (:159), that is the 'CreateOrderCommand failed - RequestId:' lines (:163) and the requests that threw before answering; against all such request ids. A retried call carries the same request id and counts once (counted on cases) |
| **Why it is proposed** | **M300** a checkout that reaches Ordering API and writes no order leaves the customer with no order and, on the web front end, an emptied basket and the orders page, so the customer is not told (lifecycle L01, recovery not created; WebApp/Services/BasketState.cs:107-108; WebApp/Components/Pages/Checkout/Checkout.razor:111-116). A checkout that never reaches Ordering API fails in front of the customer and is not counted here; nor is an order call refused at authentication, which writes no command line (Ordering API's answers by status show it) |
| **Runbook link** | **M300** [its entry in RUNBOOK.md](RUNBOOK.md#alert-m300-checkouts-that-ended-with-no-order) |
| **Grouping** | By the move the case left by: L01 from `the case is created`. Its runbook entry works that state's tests. |
| **Threshold** | *Operator value, not set here.* For each measure, the value at which the alert fires. Whether it pages a person, opens a ticket or shows on a dashboard is the operators' decision. |
| **No data** | Each alert also fires when its measure cannot be counted: the query or search itself fails for longer than the window. A count of events that finds none in a window is zero, not missing data. A count fails when what it is read from is down, and then cases go wrong unseen. What it counts says where each is read. |
| **Window** | *Operator value, not set here.* How long the condition must hold before the alert fires. What the design assumes about time: L01: WebApp's HTTP clients carry the standard resilience handler (eShop.ServiceDefaults/Extensions.cs:22-29); a repeated POST with the same x-requestid is answered without a second order (Ordering.API/Application/Commands/IdentifiedCommandHandler.cs:41-45; Ordering.API/Application/Commands/CreateOrderCommandHandler.cs:67-70); L02: No timeout of its own. The WebApp's basket delete is a gRPC call whose client is made by the HTTP client factory, so it carries the standard resilience handler: each attempt 10 seconds, up to 3 retries, 30 seconds in all (WebApp/Extensions/Extensions.cs:31-32; eShop.ServiceDefaults/Extensions.cs:22-29; defaults: https://raw.githubusercontent.com/dotnet/docs/main/docs/core/resilience/http-resilience.md). Basket API's delete on OrderStartedIntegrationEvent has no clock: the message waits in queue Basket until it is consumed, and the queue sets no expiry (EventBusRabbitMQ/RabbitMQEventBus.cs:258-263) |
| **Symptom, not cause** | It fires on what happens to cases, not on any component's errors. Telling causes apart is the runbook's job. |
| **Exists today** | M300: yes, Ordering.API/Apis/OrdersApi.cs:118-166; Ordering.API/Application/Commands/IdentifiedCommandHandler.cs:41-45, 99-102; the WebApp does not read the answer (WebApp/Services/OrderingService.cs:12-18) |

## Companion measures

Read by the runbook's tests, not proposed for alerting:

- M21 Order requests answered OK with no order created
- M40 Ordering API requests by route and status, and their duration
- M81 Ordering database accepting connections
- M82 Long-running statements on orderingdb
- M80 Connections to the postgres server against max_connections
