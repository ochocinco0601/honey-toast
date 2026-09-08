# Phases 0–2 — framing, extraction, business draft

**Run:** `eshop-order-2026-09-01` · **Subject:** placing an order on `dotnet/eShop`

---

## Phase 0 — the framed run

| | |
|---|---|
| **Business process flow** | **Placing an order** — a customer buys something and it reaches them |
| **Coverage cell** | **Proof** — one business process flow × one concern. The concern is **Impact**: where in the business process did this break, and who is affected |
| **Mode** | **V&V.** The instrument changed materially the same day — the extractor gained two languages and four target-resolution idioms, the join was built, and this skill gained its reach-check section. Under V&V an instrument finding is recorded and the run moves on; **it is not fixed mid-run** |
| **Contamination** | **None.** This subject has no prior run of this method. The earlier run's specification (a payments reference application) was read for shape only, on a different subject |

### Source inventory — what was reachable

| Source | Reachable | Used |
|---|---|---|
| **Code** | Yes — `dotnet/eShop`, cloned locally | Yes, via `fact-extractor/` |
| **Deployment declaration** | Yes — the .NET Aspire host declares deployables and their wiring | Yes, via `join.py` |
| **Protocol and API declarations** | Yes — `.proto` and OpenAPI documents | Yes, via `coverage.py` |
| **Industry reference model** | Yes — the published order-to-cash / retail order-management process | Yes, Phase 2 |
| **Runtime evidence** | **No** — nothing is running, and no telemetry or dashboard inventory exists | **`gapped`.** Consequence recorded at Phase 6: the watched / unwatched split cannot be settled |
| **Stated architecture** | Partial — the repository's README and diagrams describe the application | Not used as a reconciliation arm; recorded as available and unexercised |
| **People** | **No** — a public reference application has no owners to ask | **`gapped`.** Consequence: the ratification queue comes back with roles and no names |

### Candidate business process flows on this subject

Kept because Phase 5 consumes it. Drafted from the application's own surface.

| Candidate | Taken |
|---|---|
| **Placing an order** | **Yes — the subject** |
| Browsing and searching the catalogue | No |
| Signing in and managing an account | No |
| Managing the basket | No — folded into placing an order, where it is a stage |
| Publishing a webhook to a partner | No |

---

## Phase 1 — extract structure

**Tool:** `fact-extractor/` — Semgrep over `rules.yaml`, plus `join.py` for edges and
`coverage.py` for reconciliation. The commands below produce the fact base, the join and the
coverage report this phase reads.

```
python fact-extractor/run.py      eshop-dotnet --service-map src/Basket.API=basket \
  src/Catalog.API=catalog src/Ordering.API=ordering src/Identity.API=identity \
  src/Webhooks.API=webhooks src/PaymentProcessor=payment \
  src/OrderProcessor=orderprocessor src/WebApp=webapp   > phase1-fact-base.json
python fact-extractor/join.py     eshop-dotnet phase1-fact-base.json > phase1-join.json
python fact-extractor/coverage.py eshop-dotnet phase1-fact-base.json > phase1-coverage.json
```

### What the run's own checks say about itself

| Check | Result |
|---|---|
| **Reach** — did anything read every declared deployable | **Complete.** No deployable silent |
| **Matcher control** — are known implementations recognised | **Passed** |
| **Negative control** — are fabricated routes rejected | **Passed** |
| **Recall against declared populations** | gRPC methods 1.0 · HTTP operations 1.0 (the coverage report's `categories`) |
| **Facts from test or CI code** | 8, excluded from everything downstream |
| **Rule standing** | **No rule is established.** Every fact rests on a rule with incomplete or absent precision evidence (the fact base's `rule_standing` block) |

**That last row bounds this whole run** and is stated here rather than at the end. The structure
below is reproducible and cited; how *accurate* the underlying patterns are has not been measured
on this rule set by anyone.

### The finding that decided the shape of this run

**This estate's business process does not cross services over HTTP.** The join recovered four
HTTP dependencies (its `dependencies` block); the ordering process is carried by
**eighteen integration-event handlers** — one service publishing an event another picks up.

Those handlers are `extracted` facts with file and line, and **their class names are the business
process**: `OrderStarted`, `OrderStatusChangedToAwaitingValidation`, `OrderStockConfirmed`,
`OrderStatusChangedToPaid`, `OrderStatusChangedToShipped`. A state machine, named by the
application about itself, recovered without a model reading anything.

**This is an INSTRUMENT finding and it is the sharpest one available.** The join follows call
sites to addresses; a published event has neither. So on an event-driven estate the join reports
four edges that are real but peripheral and misses the eighteen that carry the business process.
The extractor's own documentation already names the asynchronous join as not built. **Measured here: on this subject that omission is not a gap at the edge — it is
the business process itself.** Recorded, not fixed: this run is in V&V mode.

---

## Phase 2 — the business account, drafted

**Drafted from** the published order-to-cash / retail order-management process — the stages a
retailer's operation names regardless of implementation. **`proposed`** throughout.

**Independence is compromised and recorded rather than claimed.** This draft was written after the
extraction had been read. The method's ruling is that sources compose and independence is recorded
per claim rather than staged as a blind fork — so convergence below is **weaker evidence than a
blind draft would give**, and that is stated where it matters in Phase 3.

**The stage test applied:** would a business person name it, and would they care if it stopped?

| # | Stage, in business words | Why a business names it |
|---|---|---|
| 1 | Customer chooses what to buy | No selection, no order |
| 2 | Customer holds items until they are ready to buy | An abandoned basket is a measured business loss |
| 3 | Customer submits the order | The commitment point; the first moment a business owes something |
| 4 | Business acknowledges the order to the customer | The customer's evidence that it worked |
| 5 | Business allows a short window to change their mind | A cancellation window is a policy, not a technicality |
| 6 | Business checks the goods are actually available | Selling what you do not have is a customer-facing failure |
| 7 | Business takes the money | The revenue event |
| 8 | Business confirms the order is going ahead | Where a customer stops worrying |
| 9 | Business picks and ships the goods | The physical fulfilment |
| 10 | Customer is told it has shipped | The second thing a customer waits for |
| 11 | Business tells its partners what happened | Downstream systems and third parties depend on order state |
| 12 | Business handles cancellation or failure | Every real order process has an unhappy path |

**Expected failure profile, stated up front:** structurally right and locally wrong. A reviewer who
knows this business corrects the stage *boundaries* fastest — where one stage ends and the next
begins — rather than the set of stages.

**Open questions carried into Phase 3.**

- Does this business run a grace period, or is submission immediate?
- Is stock checked before or after payment? The order differs by retailer and changes what a
  customer sees when it fails.
- Is shipping performed by this business or by a partner?
