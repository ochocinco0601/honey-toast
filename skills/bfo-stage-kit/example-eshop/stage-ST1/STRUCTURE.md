# Fulfilling a customer's order: stage 1 of 4, Place the order

**How to read it.** Solid arrows between steps follow the case: each is labelled with the state the case is in when the next step starts. Where several arrows leave one step, they are alternatives: one case takes one of them. **Done by** is every part that carries the step out; **needs** is a part it cannot complete without that does not itself carry the step out. Steps are numbered within their stage, the same in every stage file. Step 1.1: The customer's basket is emptied changes no state of the case: it happens alongside, and nothing waits on it.

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
  P1["Expected outcome: <b>The order is placed</b>"]
  P2["Step 1.1: <b>The customer's basket is emptied</b>"]
  ST1 -->|enters at: the case is created| P1
  ST1 -->|enters at: the case is created| P2
  X0(["leaves the stage: Submitted<br/>into Accept the order"])
  P1 -->|then: Submitted| X0
  S02["Application component<br/><b>WebApp</b><br/>web front end"]
  S03["Application component<br/><b>ClientApp</b><br/>web front end"]
  S04["Application component<br/><b>Mobile BFF</b><br/>gateway"]
  S09["Application component<br/><b>Basket API</b><br/>API service"]
  S07["Application component<br/><b>Catalog API</b><br/>API service"]
  S05["Application component<br/><b>Ordering API</b><br/>API service"]
  S12["System component<br/><b>Ordering database</b><br/>database"]
  S16["System component<br/><b>Basket store</b><br/>cache"]
  S13["System component<br/><b>Catalog database</b><br/>database"]
  S10["Application component<br/><b>Identity API</b><br/>identity provider"]
  S15["System component<br/><b>Event bus</b><br/>message broker"]
  P1 ==>|done by| S02
  P1 ==>|done by| S03
  P1 ==>|done by| S04
  P1 ==>|done by| S09
  P1 ==>|done by| S07
  P1 ==>|done by| S05
  P1 -.->|needs| S12
  P1 -.->|needs| S16
  P1 -.->|needs| S13
  P1 -.->|needs| S10
  P2 ==>|done by| S02
  P2 ==>|done by| S03
  P2 ==>|done by| S09
  P2 ==>|done by| S05
  P2 -.->|needs| S16
  P2 -.->|needs| S15
  classDef on stroke-width:3px
  class ST1 on
  classDef off opacity:0.45
  class ST2,ST3,ST4 off
```
