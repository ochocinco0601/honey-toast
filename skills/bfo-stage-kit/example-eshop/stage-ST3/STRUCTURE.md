# Fulfilling a customer's order: stage 3 of 4, Ship the order

**How to read it.** Solid arrows between process steps follow the case: each is labelled with the state the case is in when the next process step starts. Where several arrows leave one process step, they are alternatives: one case takes one of them. **Done by** is every part that carries the process step out; **needs** is a part it cannot complete without that does not itself carry the process step out. Process steps are numbered within their stage, the same in every stage file. Process step 3.1: Stock is reduced by the order's units; Process step 3.2: Webhook subscribers are told the order is paid: each changes no state of the case: it happens alongside, and nothing waits on it.

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
  P9["Process step 3.1: <b>Stock is reduced by the order's units</b>"]
  P10["Process step 3.2: <b>Webhook subscribers are told the order is paid</b>"]
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

<!-- bfo-generated-from {"flow": "F1", "stage": "ST3", "tables": {"about": "c9f8351ce577", "agent-system": "80df4fb74aa2", "capabilities": "f4fc19936bf8", "case-attributes": "3f95e73172bd", "expectations": "cd4f9fe286e7", "failure-modes": "132f9700adac", "flows": "a27265fffff5", "lifecycle": "440f83f4a1fa", "measure-gaps": "f3ef7b5dbcfd", "measures": "3c7ec5c71e65", "participation": "f08de4c4ac9a", "remedies": "2e9c1e60a265", "sources": "328a3c147492", "stages": "4595b2c6e50a", "step-impact": "4e066d413fd0", "steps": "e09fc039d65e", "subjects": "644d8b1712b7"}} -->
