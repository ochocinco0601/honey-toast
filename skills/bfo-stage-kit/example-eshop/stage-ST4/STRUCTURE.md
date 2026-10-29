# Fulfilling a customer's order: stage 4 of 4, Deliver the order

**How to read it.** Solid arrows between process steps follow the case: each is labelled with the state the case is in when the next process step starts. Where several arrows leave one process step, they are alternatives: one case takes one of them. **Done by** is every part that carries the process step out; **needs** is a part it cannot complete without that does not itself carry the process step out. Process steps are numbered within their stage, the same in every stage file. Process step 4.1: Webhook subscribers are told the order is shipped changes no state of the case: it happens alongside, and nothing waits on it.

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
  P12["Process step 4.1: <b>Webhook subscribers are told the order is shipped</b>"]
  P13["Process step 4.2: <b>The order is delivered to the customer</b><br/>not assessed: no lifecycle row carries it"]
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

<!-- bfo-generated-from {"flow": "F1", "stage": "ST4", "tables": {"about": "c9f8351ce577", "agent-system": "80df4fb74aa2", "capabilities": "f4fc19936bf8", "case-attributes": "3f95e73172bd", "expectations": "cd4f9fe286e7", "failure-modes": "132f9700adac", "flows": "a27265fffff5", "lifecycle": "440f83f4a1fa", "measure-gaps": "f3ef7b5dbcfd", "measures": "b0ad6bcbbe1a", "participation": "f08de4c4ac9a", "remedies": "2e9c1e60a265", "sources": "328a3c147492", "stages": "4595b2c6e50a", "step-impact": "4e066d413fd0", "steps": "e09fc039d65e", "subjects": "644d8b1712b7"}} -->
