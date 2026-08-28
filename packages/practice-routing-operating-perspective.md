# Routing a Naive Problem to Established Practice — an operating perspective

A frame for the situation where someone describes a problem in ordinary words, established
practice already solves it, and the two never meet. Written in generic terms — "the asker,"
"a practice," "the index" — so it maps onto whatever domain and body of knowledge an
environment already holds.

**How to use this.** It is a frame, not a tutorial. It names the distinctions that make the
situation tractable and the established practices they come from. Apply it to the situation
at hand; do not restate it back.

---

## The situation

Someone says: *we are having trouble figuring out what hygiene is supposed to mean for
monitoring.* Or: *nobody knows what to do with this tool.* Or: *we only find out when a
customer emails.*

They have stated a real problem in the only vocabulary they have. Somewhere in the world's
canon sits a practice that addresses it — named, sourced, with known limits. The asker cannot
reach it, because reaching it requires the name, and not holding the name is the whole
condition they are in.

The failure is not missing knowledge. The knowledge nearly always exists. Treating its
absence as the problem is the standard misdiagnosis, because adding content is visible and
cheap.

## The two questions inside every situated ask

Any question arriving attached to a real organization contains two, and they must be split
in writing before either is answered.

- **Type level** — what does the world already know about situations *of this kind*?
  Answerable from established knowledge alone. **No organization, person, or local fact is
  required, and gating it on one is the error.**
- **Instance level** — what is true in this particular place; the verdict from running the
  type-level answer against local conditions. Needs local facts.

The common failure is declaring a whole question blocked because its *verdict* is blocked,
forfeiting the reusable half — which is usually the more valuable half.

*Worked case.* "Are we ready?" is a **readiness instrument** (pure type level — production
readiness review, operational readiness review, TRL, CMMI are instance-free by construction)
**plus** a **readiness verdict** (needs local facts). Only the verdict is blocked.

## Placing the level — a test, not a taxonomy

Do not build a ladder of altitudes and ask anyone to pick a rung; it demands the vocabulary
the asker does not have. Ask instead, of any claim:

> **What would have to be supplied before this can be checked?**

- **nothing** — it holds wherever the practice applies
- **facts about a class** — sector, regulator, scale, jurisdiction
- **facts about this particular place**

The level falls out. Nobody picks a label. The established name for what this elicits is
**scope conditions**; the same idea appears as boundary conditions in management theory and
external validity in experimental design.

**Default to the widest scope that still answers.** Reuse lives at the top, and every step
narrower multiplies the local facts required.

Two properties matter. The test runs **continuously**, not once at intake — undeclared
switching mid-discussion is the defect, and it is what makes a discussion feel ungrounded.
And the unbound half is **never gated** on the bound half.

## The index and its negative half

Routing runs against a **closed universe** of practices — not a search, a fixed list.

**Write the index down before answering, from your own canon.** The practice names are
already held; what is not held is how *tight* a negative line has to be. Each entry carries
two, and the second one does the work:

```
PRACTICE NAME — source, with chapter or section
   ANSWERS: <the one question this practice answers, as a question>
   DOES NOT ANSWER: <the adjacent questions it is routinely mistaken for>
```

Calibrate against these three. They are working entries, not illustrations:

```
THE FOUR GOLDEN SIGNALS — Google SRE Book, ch. 6
   ANSWERS: what do I measure on a service to see whether it is healthy?
   DOES NOT ANSWER: what value is acceptable; when to wake someone; who
   responds; what anyone should DO about what they see.

ALERTING ON SLOs / SYMPTOM-BASED ALERTING — SRE Workbook ch. 5
   ANSWERS: which conditions should actually wake a human, and which should not?
   DOES NOT ANSWER: what the human does once woken; what to measure at all;
   how to reduce a backlog of existing bad alerts nobody owns.

SERVICE OWNERSHIP — Skelton & Pais, *Team Topologies*; "you build it, you run it"
   ANSWERS: who owns this system, and what does owning it actually oblige them to do?
   DOES NOT ANSWER: how to understand a system nobody understands; what to measure;
   how to handle an incident.
```

Note the tightness. "How to reduce a backlog of existing bad alerts nobody owns" is not a
category — it is a specific neighbouring situation someone would plausibly bring. A vague
negative line is no veto at all, and without the veto every entry looks like a plausible
match for anything in its subject area, because subject adjacency is what a capable reader
generates from a positive definition alone.

**Once written, the index is closed for that exchange.** Extending it mid-answer to reach a
match is the failure this whole discipline exists to prevent.

## The fit test

Run it before naming anything.

1. State the asker's actual question in one sentence, in plain words. If the situation
   carries more than one, state them all, numbered.
2. Reproduce, **word for word**, the `ANSWERS` line of the entry under consideration.
3. Put them side by side and **do not judge whether they match.** Write both lists:
   - **LINE ASKS, THEY DID NOT** — what does the quoted line ask about that this person
     never raised?
   - **THEY ASKED, LINE DOES NOT COVER** — what did they raise that the line is silent on?
4. **If either list has anything in it, the answer is NONE.** Do not empty a list by
   rewording. "Nothing material" is a full list in disguise.

If the question is covered by any entry's `DOES NOT ANSWER` line, that entry does not fit,
however related it seems.

**Being in the same subject area is not fit. Partially helping is not fit.**

## The chain rule, and what the answer must still say

One practice rarely closes a compound situation. A practice that is a gate or a precondition
leaves work behind it, so name what the chosen one **requires** next, in order, one clause
each.

> **A chain names practices the chosen one REQUIRES to be useful.
> A stretch names practices that merely RESEMBLE the situation.**

If you cannot say in a few words *why* the primary requires a link, it does not belong. "Nothing
follows — this closes the situation" is a normal answer.

Three fields are not optional, and the last one is the only instrument that makes a partial
answer visible:

- **RULED OUT** — the practices a reader might expect to fit, one reason each.
- **WHAT THE SOURCE ACTUALLY COVERS** — see below.
- **WHAT IS STILL UNANSWERED** — of the questions enumerated at step 1, which the practice and
  its chain do not address. If everything is covered, say so explicitly.

## NONE is a correct answer

A router that always finds a match is broken.

A refusal must name **the discipline that owns the problem** — names only, no hedging. A
refusal that names no owner detects a gap nobody can act on, which is half an answer. A
stretched match leaves the asker worse off than a clean refusal; the refusal at least tells
them where to go.

Refusals are also the **only legitimate input to growing the index**. A practice is added
because a real situation found nothing — never because the practice exists.

## What the answer carries

Beyond the practice name: **what the cited source actually covers.** A real source cited
outside its true scope is the failure a non-expert cannot detect, and it is the residual risk
of this entire approach. Naming discipline defends against invention; it does not defend
against misreading. Every citation therefore owes a statement of its own coverage.

## The two failure modes

They pull in opposite directions, and the discipline that suppresses one loosens the other.

- **Over-matching** — answering when nothing fits. The commonest failure, and it worsens as
  the index grows: each practice added loosens the refusal boundary, so every addition must be
  re-checked against situations that were previously refused correctly. Its signature is
  **reinterpretation dressed as matching** — reading the situation as an *instance* of the
  `ANSWERS` line rather than as the same question. "A budget cut is a kind of too-much-work
  problem" is a reinterpretation, not a match.
- **Under-serving** — answering correctly but partially, because a one-practice rule cannot
  express a situation that legitimately carries three questions. **More dangerous than
  over-matching in one specific way: the answer is right, so nothing signals that most of the
  question went unanswered.** The chain rule and the `WHAT IS STILL UNANSWERED` field exist
  against this, and correctness scoring cannot see it — an under-served answer scores correct.

Two further failures worth naming:

- **Gating the type level on missing local facts.** The reusable half is forfeited and nobody
  notices, because an answer never attempted leaves no trace.
- **Asking the asker to classify.** No front door can require a category the asker does not
  know exists. Classification is performed by the receiver.

*On the evidence:* in one measured run across 40 unseen situations the refusal boundary held
with no drift across two blind repeats, and the single disputed case was a **wrongly refused**
one — two judges split on whether it was an error at all, so the honest statement of that
result is *39/40 or 40/40, unresolved*. An earlier, smaller run on a different index version
showed over-matching as the only failure; that one-directional claim did not survive the
larger test. Treat both failure modes as live.

## Established practice this rests on

Named so the relevant knowledge can be loaded directly rather than reconstructed:

- **Scope conditions** — Walker & Cohen (1985), and boundary conditions in management theory.
  The mechanism behind the level test above.
- **Taylor's question negotiation** (1968) and the **reference interview** — specifically the
  founding distinction between the presented question and the actual information need.
- **The vocabulary problem** — Furnas, Landauer, Gomez & Dumais (1987). The under-20% figure.
- **Faceted classification** — Ranganathan; the several-independent-axes structure, against
  single-tree placement.
- **Situational method engineering** — situation characterization and method assembly.
- **Clinical decision rules** — the reproducibility result: fixed inputs, same category,
  different practitioners.
- **Inert knowledge** — Whitehead (1929). The condition this frame exists to break.
- **Controlled vocabularies with entry terms** — ISO 25964; the entry-term mechanism.
- **Triage** — classification by the receiver, never demanded of the arriver.

---

*This frame governs the routing exchange only. It does not decide what the asker should do
once the practice is named, and it carries no claim that the named practice is well-executed
where they are.*
