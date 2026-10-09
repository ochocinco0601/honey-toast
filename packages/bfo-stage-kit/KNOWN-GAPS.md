# Known gaps

## How far to trust a run

A run usually gets the stage, its steps and the layers right. Expect an occasional error in the parts, such as a
step's dependency on a database left out, or a mobile app drawn as a web front end (the eShop example below still
has this one). Most errors fall in what the code does under failure: what a test would show, where a restore
leads, and what a log really records. Treat the runbook as a draft for the code owners to correct before anyone
relies on it.

## Open in the eShop example

- **M28** is named for orders cancelled because payment failed, but it counts the Payment Processor's publish
  attempts. That line is written even when the publish fails, so it also counts stranded orders.
- **ClientApp** is drawn as a web front end. It is the mobile app.
- **FM44 and FM46** (the ordering database or the broker down, in the shared tests) lead to the re-drive R1, which
  cannot run while either is down. FM11 and FM14, the same checks in the `Submitted` branch, lead to the real
  restores, R5 and R4. When a database reaches its connection limit, FM45 and FM49 say restore while FM13 says
  escalate.
- **R1** sends orders back to `Submitted`, so the ones already in `StockConfirmed` pass through payment again, with
  no guard. It is safe only because payment is simulated, and the runbook does not say so.
- **Log tests use `az containerapp logs show --tail 300`.** By the time someone is paged, the failure lines may
  have rolled out of those 300. The procedure requires a search over the time since the count rose (FILL-STEPS
  Step 11.3); the example's log tests tail 300 lines instead.
- **FM23 and FM28** read the only evidence that outlives a lost log (a missing catalog outbox row, a payment
  result for an order still in `StockConfirmed`), then route past it.

Failure-mode ids (`FM..`) are the register's; each runbook test names the mode it comes from.

## Open in the kit

- The generated "What changed" test sends any change, an unplanned restart included, to a rollback through the
  change-approval path or the change owner. An unplanned restart has neither; for one, escalate as section 7 says.
- The rules for a stage that never parks (one synchronous call that succeeds or fails within seconds) have no worked
  example in this kit (the eShop example's stage parks).
- `flow_outputs.py --check` tests the register's structure and coverage. It cannot tell whether a citation says what
  the row claims: that is the verification pass in Step 11, which the assistant runs on its own work.
