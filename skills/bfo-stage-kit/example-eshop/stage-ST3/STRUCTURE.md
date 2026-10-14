# Fulfilling a customer's order: stage 3 of 4, Ship the order

**How to read it.** Solid arrows between steps follow the case: each is labelled with the state the case is in when the next step starts. Where several arrows leave one step, they are alternatives: one case takes one of them. **Done by** is every part that carries the step out; **needs** is a part it cannot complete without that does not itself carry the step out. Steps are numbered within their stage, the same in every stage file. Step 3.1: Stock is reduced by the order's units; Step 3.2: Webhook subscribers are told the order is paid: each changes no state of the case: it happens alongside, and nothing waits on it.

```mermaid
flowchart TD
  FL["Intended flow<br/><b>Fulfilling a customer's order</b><br/>one case: One order"]
  CAP0["Capability<br/><b>Fulfil customer orders</b>"]
  CAP0 -->|delivered by| FL
  CAP1["Capability<br/><b>Take and process customer orders</b>"]
  CAP1 -->|delivered by| FL
  CAP2["Capability<br/><b>Notify outside parties of business events</b>"]
  CAP2 -->|delivered by| FL
  ST1["Stage 1 of 4<br/><b>Place the order</b>"]
  FL -->|first stage| ST1
  ST2["Stage 2 of 4<br/><b>Accept the order</b>"]
  ST1 -->|then| ST2
  ST3["Stage 3 of 4<br/><b>Ship the order</b>"]
  ST2 -->|then| ST3
  ST4["Stage 4 of 4<br/><b>Deliver the order</b>"]
  ST3 -->|then| ST4
  P9["Step 3.1: <b>Stock is reduced by the order's units</b>"]
  P10["Step 3.2: <b>Webhook subscribers are told the order is paid</b>"]
  P11["Expected outcome: <b>The order is shipped</b>"]
  ST3 -->|enters at: Paid| P9
  ST3 -->|enters at: Paid| P10
  ST3 -->|enters at: Paid| P11
  X0(["leaves the stage: Shipped<br/>into Deliver the order"])
  P11 -->|then: Shipped| X0
  S05["Application component<br/><b>Ordering API</b><br/>API service"]
  S07["Application component<br/><b>Catalog API</b><br/>API service"]
  S12["System component<br/><b>Ordering database</b><br/>database"]
  S13["System component<br/><b>Catalog database</b><br/>database"]
  S15["System component<br/><b>Event bus</b><br/>message broker"]
  S11["Application component<br/><b>Webhooks API</b><br/>API service"]
  S14["System component<br/><b>Webhooks database</b><br/>database"]
  S18["External dependency<br/><b>Webhook subscriber endpoint</b><br/>third-party API"]
  S17["Person<br/><b>Fulfilment staff</b><br/>person"]
  S10["Application component<br/><b>Identity API</b><br/>identity provider"]
  P9 ==>|done by| S05
  P9 ==>|done by| S07
  P9 -.->|needs| S12
  P9 -.->|needs| S13
  P9 -.->|needs| S15
  P10 ==>|done by| S05
  P10 ==>|done by| S11
  P10 -.->|needs| S14
  P10 -.->|needs| S15
  P10 -.->|needs| S18
  P11 ==>|done by| S17
  P11 ==>|done by| S05
  P11 -.->|needs| S12
  P11 -.->|needs| S10
  classDef on stroke-width:3px
  class ST3 on
  classDef off opacity:0.45
  class ST1,ST2,ST4 off
```
