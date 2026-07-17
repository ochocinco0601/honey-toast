# What "Prior Art" Means Here

The single source for how this repo defines and judges prior art. Handed whole to the
`prior-art-checker` agent at dispatch; read by any session or human who needs it.

Kept in its own file deliberately: the prior-art check must run **blind** to the
**activated prior-art inventory** — the standing table of frameworks already adopted.
Knowing what has already been activated would anchor a verdict, so the definition must
stand alone, readable without the inventory anywhere near it.

---

## The definition

**Prior art = named practices, standard artifacts, or frameworks — from real professional disciplines.**

Three forms, one qualification test. The form varies; the provenance is the constant.

| Form | It is |
|---|---|
| **Named practice** | a way of *doing* — a method or technique the discipline performs |
| **Standard artifact** | a standardized *output form* — a document or record type the discipline produces |
| **Framework** | a structured *model* — an organizing scheme the discipline reasons with |

**No examples are listed here, deliberately.** Named instances would hand a blind
reader a menu of this repo's own answer set — precisely the anchoring that keeping
this file separate from the table exists to prevent. (Measured, not theoretical:
the first calibration run was contaminated exactly this way.) A human wanting
illustration has the entire inventory to read; a blind checker must supply instances
from its own knowledge, which is the whole point.

**Qualification test:** something a practitioner of that discipline would recognize
**by name**. Established and citable — not a plausible analogy, not a pattern you
could argue for.

The term is literal: *the art already exists*. Someone in a real discipline worked
it out and named it, so we don't reinvent it.

## Rules for judging a match

- **Judge by function, not by name.** Our internal names are frequently borrowed
  vocabulary. A name is *never* evidence of prior art — a file called "manifest"
  is not thereby a manifest.
- **No stretched or forced analogies.** Forced connections are the failure mode.
  Missing ones are not.
- **"No match" is a valid, valuable verdict.** Novelty honestly cleared is worth
  as much as a match correctly named. If unsure whether something is real
  established practice, downgrade it or drop it.
- **Every match states its delta** — what matches *and* what does not. A match
  without its honest delta is an over-claim.
- **Verdict scale:** STRONG (an established practice/artifact with the same
  function exists) · PARTIAL (established pattern, different domain, partial
  overlap — or an established-ingredients / unpublished-arrangement composition) ·
  NONE.
- **The practitioner-naming test decides STRONG vs PARTIAL on composition cases.**
  Ask: *would practitioners name this correctly, and would they agree?* If one
  discipline names it and what's left over is a stated addition to a thing they'd
  recognize → **STRONG**, with the delta named. If three disciplines each name it
  differently and each misses most of it, that divergence is the signature of
  composition → **PARTIAL**. (Earned in calibration: without this rule, one run
  graded two structurally identical composition cases inconsistently — and was
  right both times by different reasoning.)
- **Check at rule level, not only artifact level.** One artifact often carries
  several separately established controls. Naming only the artifact under-credits
  how much borrowed practice is inside it — and it is at rule level that genuine
  novelty usually shows up.

## The boundary — what is NOT prior art

Knowledge the organization **originated** is not prior art — it is theirs, not the
world's. The honest verdict on it is NONE, and NONE is the correct answer, not a
failure.

Settle borrowed-vs-invented with one question: **does a real discipline already
hold this?** Never by whether a file is attached to an entry, and never by any
marker or annotation in the inventory — those record how knowledge is *loaded*,
not where it came from.

**No instances are named in this section, deliberately** — naming which of the
organization's assets are "ours" pre-announces a verdict to a blind reader, and a
pre-announced verdict is not a verdict. (Measured: a calibration run had its answer
class pre-announced by this exact section.)

## Composition is ours

Individual frameworks are prior art. **Combining** them into behaviours none of
them individually teaches is this repo's original contribution. A check that finds
every ingredient established and the arrangement unpublished should say exactly
that: ingredients named, recipe ours. That is a PARTIAL with an honest delta, not
a failure.

---

**Consumers:** the `prior-art-checker` agent (this is its only criteria — it is handed
the text and can reach nothing else) · the `prior-art-check` skill (the firing surface,
which hands it over verbatim, and the encode gate) ·
the environment's activated prior-art inventory (the table this definition governs) ·
any session running a prior-art check by hand.
