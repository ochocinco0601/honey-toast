# Fulfilling a customer's order: stage 4 of 4, Deliver the order

**How to read it.** Solid arrows between steps follow the case: each is labelled with the state the case is in when the next step starts. Where several arrows leave one step, they are alternatives: one case takes one of them. **Done by** is every part that carries the step out; **needs** is a part it cannot complete without that does not itself carry the step out. Steps are numbered within their stage, the same in every stage file. Step 4.1: Webhook subscribers are told the order is shipped changes no state of the case: it happens alongside, and nothing waits on it.

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
  P12["Step 4.1: <b>Webhook subscribers are told the order is shipped</b>"]
  P13["Step 4.2: <b>The order is delivered to the customer</b><br/>not assessed: no lifecycle row carries it"]
  ST4 -->|enters at: Shipped| P12
  S05["Application component<br/><b>Ordering API</b><br/>API service"]
  S11["Application component<br/><b>Webhooks API</b><br/>API service"]
  S14["System component<br/><b>Webhooks database</b><br/>database"]
  S15["System component<br/><b>Event bus</b><br/>message broker"]
  S18["External dependency<br/><b>Webhook subscriber endpoint</b><br/>third-party API"]
  P12 ==>|done by| S05
  P12 ==>|done by| S11
  P12 -.->|needs| S14
  P12 -.->|needs| S15
  P12 -.->|needs| S18
  classDef on stroke-width:3px
  class ST4 on
  classDef off opacity:0.45
  class ST1,ST2,ST3 off
```
