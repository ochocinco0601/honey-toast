# Judging score — `eshop-order-2026-09-01`

Scored against `JUDGING-INSTRUMENT.md`'s seven conditions. **The instrument scores the draft, not
its acceptance**, so "nobody ratified it" is never a reason to mark a
condition unmet.

| # | Subproblem | Verdict | Evidence, from this run's own output |
|---|---|---|---|
| 1 | Recover the code account | **MET** | Every stage binds to a file and line (the run's Phase 3 reconciliation table). The extraction reproduces and its artifacts are committed |
| 2 | Recover the business account | **NOT MET** | The done-condition is *stated end to end at one level, without reference to the code*. The draft was stated end to end at one level; it was **not** written without reference to the code. Recorded in Phase 2 rather than discovered later |
| 3 | Reconcile | **MET** | All twelve stages classified — ten convergence, two divergence, no absence |
| 4 | Rule on each difference | **MET** | Both divergences carry a drafted ruling with reasoning (R1 payment, R2 shipping), plus R3 on the instrument. **This is the condition the prior run failed outright, and here it produced the run's most valuable finding** |
| 5 | Prune to what matters | **NOT EXERCISED** | One business process flow in scope. A candidate that surfaced mid-run was recorded as a seed rather than admitted |
| 6 | Define signals | **NOT MET** | Twelve signals carry a disposition; **no signal carries a definition of healthy.** All twelve are `gapped` with the reason — no stated objective, no industry norm this business accepts, no incident history |
| 7 | Set the tolerance | **PARTIAL** | The owner half is done as the condition requires: every boundary carries a recorded `unowned` rather than a blank or a plausible name. The tolerance itself is `gapped` — no expectation source and nobody to ask |

---

## What the score says

**Three met, two not met, one partial, one not exercised.**

**Condition 2 is the one I got wrong, and it was a choice rather than an accident.** The business
draft was written after the extraction had been read. The method's own ruling permits it — sources
compose, and independence is recorded per claim rather than staged as a blind fork — but the
*judging* condition still asks for a business account stated without reference to the code, and
this run cannot claim one. The cost is concrete and named in Phase 3: **ten of twelve stages
converge, and that number is nearly worthless as corroboration**, because a draft written with the
code in view is biased toward agreeing with it.

**What survives the contamination is the part that matters.** A biased draft biases *toward*
convergence, so it cannot manufacture the two divergences, and it cannot manufacture the recall
defect. Those three findings stand independent of the run-design flaw.

**Conditions 6 and 7 are unmet for the same reason and it is a property of the subject.** Healthy,
tolerance and ownership are business facts. A public reference application has no business behind
it, no objectives, no incident history and no owners. **This is the boundary the method has always
said it has** — the machine half cannot supply these, by design — but it is worth being exact:
this run did not *fail* to draft them, it recorded that there is no source from which to draft
them. On a subject with real owners those cells become the ratification queue's main content.

**Condition 4 earned its place.** The prior run scored NOT MET here — no ruling was written on any
difference. On this run the ruling step is what separated *a payment service exists* from *the
payment service charges nobody*, which no automated check on this run detected and which every
automated check passed alongside.

---

## The gap between the checks and the truth, stated plainly

Every mechanical check on this run passed. Reach complete, both matcher controls passed, recall
1.0 on both declared populations, no deployable silent, extraction reproducible.

**And the run's three real findings were all made by a person or a model asking a question no
check asks:**

- the payment step reads a configuration flag rather than charging anyone,
- nothing calls the shipping endpoint,
- the order's own database write was never extracted.

**That is not an argument against the checks.** They are what makes the structure trustworthy
enough to reason over. It is an argument against reading a run's green checks as a verdict on its
output, and it is the sharpest thing this run established about the method itself.
