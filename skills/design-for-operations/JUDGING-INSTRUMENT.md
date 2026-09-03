# How to judge a run

**The problem this solves.** A second run of this method would produce a second document and no
way to tell whether it did the right thing. The method's own statement of what good looks like
cannot be the test: **a standard written by the thing being measured is not a standard.**

**Where the standard comes from instead.** Each subproblem this method performs is an established
practice, and **each of those practices carries a done-condition written by its own field.** Those
conditions are external by construction — nobody here wrote them. Collecting them gives an
instrument that scores any run.

**The altitude.** This asks *did each part produce the kind of thing its discipline says it should.*
It is not a fine-grained inspection of the content.

**One yardstick that would be circular, and is excluded.** Published industry reference models
cannot be the test. The method **drafts from** them — they are an input, and scoring an output
against its own input proves nothing.

---

## The instrument

| # | Subproblem | Field | The field's done-condition |
|---|---|---|---|
| 1 | Recover the code account | software architecture reconstruction (SEI) | Every element of the recovered model traces to a source location |
| 2 | Recover the business account | reflexion model's precondition: the high-level model is supplied independently | Stated end to end at one level, without reference to the code |
| 3 | Reconcile | software reflexion model — Murphy, Notkin & Sullivan 1995 | **Every** relation classified as convergence, divergence, or absence |
| 4 | Rule on each difference | same paper — the engineer investigates each discrepancy and confirms it or revises the model | Each discrepancy carries a drafted ruling — stale belief, wrong draft, or real hole — with its reasoning |
| 5 | Prune to what matters | important business service (FCA / PRA); critical user journeys (Google SRE) | The set is selected against a stated impact criterion |
| 6 | Define signals | service level indicators and objectives (Google SRE) | Each signal carries a definition of healthy. **An indicator without an objective is incomplete** |
| 7 | Set the tolerance | impact tolerance (FCA / PRA) | A maximum tolerable disruption is stated, with its owner named or recorded unowned |

**It scores the draft, not its acceptance.** Conditions 4, 6 and 7 could be read as requiring *a
ruling by someone with authority*, which nothing the method performs can supply. That reading
grades every run against the presence of an organization, so the score reads mostly-failing by
construction and says nothing about the work. **A prototype is not graded on whether it has run
in production.** Under the practitioner's-draft rule the method takes a position on every cell;
whether a named role then accepts it is the receiver's business and appears in the ratification
queue, not here.

**Feeding back is not on this instrument.** Re-running when the code moves needs a live estate and
an incident history — it describes a practice an organization holds, not something a run does.

---

## How to record a score

One row per condition: the verdict — MET, PARTIAL, NOT MET, or NOT EXERCISED — and the evidence
quoted from the run's own output. NOT EXERCISED is for a condition the subject gave the run no
occasion to perform (one candidate business process flow, nothing to prune between); it is not a
softer NOT MET. Below the table, say what the score says: which failures are things the run did
not write, and which are properties of the subject. `example/JUDGING-SCORE.md` is one.

---

## What this instrument does not do

- **It does not judge content.** A run can meet all seven conditions and be wrong about the
  business. That requires someone who owns the business process flow, which is condition 4.
- **It does not score reproducibility.** Two runs by different producers agreeing is a different
  test.
- **It has only been applied by people who also worked on the method.** No independent scorer has
  used it.
