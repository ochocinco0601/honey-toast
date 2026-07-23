# Worked Example — Ledger-Writer Service Profile

**Type:** Worked example (companion artifact to [IN-24](in-24-first-process-run-plan.md))

**State:** Seeded

---

## What this is

The completed output of a first-process run — the filled service profile [IN-24](in-24-first-process-run-plan.md)'s working session produces — for a real service: the ledger-writer service of Bank of Anthos, a public reference banking application. Use it two ways: read it before your own session to see what done looks like, and compare your session's output against it afterward.

This page keeps the shape your session produces: stakeholders → expectations → business signals → supporting application and system signals, plus impact notes and the gap list.

## The service in one paragraph

Ledger-writer validates and records every customer payment — the single gate through which all payments flow. It is critical-path: there is no alternative channel, no degraded mode, no retry queue. When it fails, customers experience immediate, total inability to send money. Tier 1; regulatory exposure: every transaction must produce an auditable record.

## The process it serves

**Send Payment:** payment initiation (frontend) → **transaction acceptance (ledger-writer — the step this profile covers, blocking)** → balance update (balance-reader) → payment confirmation (frontend). Critical dependencies at the acceptance step: the balance-reader service (synchronous call, no fallback) and the ledger database (synchronous write, no queue).

## Stakeholder chains — the session's core output

Four chains. Each one: who → what they expect (as a measurable sentence) → the business health signal that tells us it's met or missed → what it costs when it isn't.

### Chain 1 — Bank Customers (CRITICAL)

**Expectation:** "Payments complete successfully, quickly, and without double-charging."

| Business health signal | Question it answers | Target |
|---|---|---|
| Transaction Success Rate | Are customer payments completing successfully? | ≥ 99.5% (30-day) |
| Transaction Processing Duration p95 | Is payment processing fast enough? | < 2,000 ms |
| Payment Volume Capacity Headroom | Can we absorb volume spikes (payroll day, month-end)? | ≥ 20% buffer |

**Impact when missed:** the only path for sending money is down — no fallback; roughly $2,400/hour of uncaptured revenue at baseline volume; beyond 2 seconds customers resubmit, which stresses duplicate prevention; trust erosion and account-closure risk.

### Chain 2 — Compliance & Risk Management (CRITICAL)

**Expectation:** "Every processed transaction produces a complete, auditable record; no unauthorized transactions are accepted."

| Business health signal | Question it answers | Target |
|---|---|---|
| Transaction Audit Completeness | Does every transaction — including rejected ones — produce a complete audit record? | ≥ 99.99% |

**Impact when missed:** audit gaps are examination findings — BSA/AML reporting gaps, consent-order risk, mandatory disclosure. The record must show *why* a transaction was rejected, not just that it was.

### Chain 3 — Finance & Treasury (HIGH)

**Expectation:** "Ledger balances are accurate — no duplicate entries, no missing transactions, reconciliation closes daily."

| Business health signal | Question it answers | Target |
|---|---|---|
| Duplicate Prevention Rate | Are duplicate payment attempts caught before ledger write? | ≥ 99.9% |

**Impact when missed:** at just 0.1% leakage, ~5 duplicate transactions a day each need manual reversal; balance errors, daily reconciliation breaks, restatement risk.

### Chain 4 — Payments Operations (HIGH)

**Expectation:** "Transaction failures are visible and diagnosable within 15 minutes; the system handles volume changes without manual intervention."

This chain is served by the whole signal set plus the diagnostic descent below — and it carries this profile's most instructive finding: **no single composite health signal exists**; operators must correlate individual signals. That finding is recorded in the gap list rather than hidden.

**Impact when missed:** blind spots in payment health, manual-correlation delay, incident-response SLA breaches, dependency failures cascading undetected.

## The supporting layers — connecting existing monitoring upward

Every business health signal above is explained by signals at the layers below. This is where a team's existing monitors slot in instead of being thrown away.

**Application-layer signals** (which step is failing?):

| Signal | Question it answers | Explains |
|---|---|---|
| Payment Validation Rate | Are payments passing the validation chain (auth, format, business rules)? | Success Rate |
| Balance Check Latency p95 | Is the balance-verification dependency fast enough? (target < 500 ms) | Duration, Success Rate |
| Ledger Write Latency p95 | Is the database write keeping up? (target < 200 ms) | Duration, Success Rate |
| Transaction Request Rate | What volume is arriving right now? | Capacity Headroom |

**System-layer signals** (why is it failing?):

| Signal | Question it answers |
|---|---|
| Ledger-Writer Availability | Is the service accepting requests at all? (readiness probe) |
| CPU Utilization | Is it working past its resource budget? (target < 70%) |
| DB Connection Pool Saturation | Is the write path about to bottleneck? (target < 80%) |

## How diagnosis walks the layers

Business health says *customers can't pay* or *payments are slow*. Application signals say *which step* — validation, balance check, or write. System signals say *why* — service down, CPU contention, pool exhausted. For this service the single largest risk is the balance-reader dependency: its failure blocks every local payment and surfaces as ledger-writer errors, not as a clear dependency signal.

## The gap list — kept on the page as gaps

What the analysis could not settle, recorded instead of smoothed over:

- **Duplicate prevention has a structural hole:** the deduplication cache is per-pod, not shared — a pod restart or a multi-replica deployment opens a window for duplicate writes. (Recorded as a violated precondition.)
- **Rated capacity has never been established by load test** — the capacity-headroom signal depends on it. (Unknown.)
- **Whether balance-reader scales with ledger-writer throughput is unverified** — if it's the bottleneck, headroom overstates safety. (Unknown.)
- **No composite health signal** — Operations correlates individual signals by hand today.

## What to imitate

- Every expectation is a **measurable sentence**, not a sentiment.
- Every expectation has a **named signal** — even where nothing measures it yet; the gap stays visible.
- Every signal carries **the question it answers**, in business language.
- Existing monitors are **connected upward** under business signals, not discarded.
- **Gaps stay on the page as gaps** — the profile records what the room couldn't answer.
