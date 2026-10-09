# Fulfilling a customer's order: stage 2 of 4, Accept the order

**How to read it.** Solid arrows between steps follow the case: each is labelled with the state the case is in when the next step starts. Where several arrows leave one step, they are alternatives: one case takes one of them. **Done by** is every part that carries the step out; **needs** is a part it cannot complete without that does not itself carry the step out. Step numbers are the register's, and every other output uses the same ones.

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
  P3["Step 3: <b>The order is released for stock checking when the grace period ends</b>"]
  P4["Step 4: <b>Stock is confirmed for every item of the order</b>"]
  P5["Step 5: <b>The order is cancelled because an item is out of stock</b>"]
  P6["Step 6: <b>Payment is taken for the order</b>"]
  P7["Step 7: <b>The order is cancelled because payment failed</b>"]
  P8["Step 8: <b>The order is cancelled at the customer's request</b>"]
  ST2 -->|enters at: Submitted| P3
  ST2 -->|or, alternative: Submitted| P8
  P3 -->|then: AwaitingValidation| P4
  P3 -->|or, alternative: AwaitingValidation| P5
  P3 -->|or, alternative: AwaitingValidation| P8
  P4 -->|then: StockConfirmed| P6
  P4 -->|or, alternative: StockConfirmed| P7
  P4 -->|or, alternative: StockConfirmed| P8
  X0(["leaves the stage: Cancelled<br/>the case ends here"])
  P5 -->|then: Cancelled| X0
  P7 -->|then: Cancelled| X0
  P8 -->|then: Cancelled| X0
  X1(["leaves the stage: Paid<br/>into Ship the order"])
  P6 -->|then: Paid| X1
  S06["Application component<br/><b>Order Processor</b><br/>worker"]
  S05["Application component<br/><b>Ordering API</b><br/>API service"]
  S12["System component<br/><b>Ordering database</b><br/>database"]
  S15["System component<br/><b>Event bus</b><br/>message broker"]
  S07["Application component<br/><b>Catalog API</b><br/>API service"]
  S13["System component<br/><b>Catalog database</b><br/>database"]
  S08["Application component<br/><b>Payment Processor</b><br/>message consumer"]
  S03["Application component<br/><b>ClientApp</b><br/>web front end"]
  S04["Application component<br/><b>Mobile BFF</b><br/>gateway"]
  S10["Application component<br/><b>Identity API</b><br/>identity provider"]
  P3 ==>|done by| S06
  P3 ==>|done by| S05
  P3 -.->|needs| S12
  P3 -.->|needs| S15
  P4 ==>|done by| S05
  P4 ==>|done by| S07
  P4 -.->|needs| S12
  P4 -.->|needs| S13
  P4 -.->|needs| S15
  P5 ==>|done by| S05
  P5 ==>|done by| S07
  P5 -.->|needs| S12
  P5 -.->|needs| S13
  P5 -.->|needs| S15
  P6 ==>|done by| S05
  P6 ==>|done by| S08
  P6 -.->|needs| S12
  P6 -.->|needs| S15
  P7 ==>|done by| S05
  P7 ==>|done by| S08
  P7 -.->|needs| S12
  P7 -.->|needs| S15
  P8 ==>|done by| S03
  P8 ==>|done by| S04
  P8 ==>|done by| S05
  P8 -.->|needs| S12
  P8 -.->|needs| S10
  classDef on stroke-width:3px
  class ST2 on
  classDef off opacity:0.45
  class ST1,ST3,ST4 off
```
