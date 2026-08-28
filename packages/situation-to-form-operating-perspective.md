# From a Messy Ask to a Real Form — an operating perspective

A frame for the path a rough request travels between arriving and becoming something the
organization holds. Written in generic terms — "the asker," "the producer," "the form" — so it
maps onto whatever domain and organization an environment already has.

**How to use this.** It is a frame, not a tutorial. It names six decisions, the established
practice behind each, and what breaks when one is skipped. Apply it to the work in hand; do not
restate it back.

---

## The situation

Someone brings a request. The work gets done well. It is handed on — and the receiver cannot
tell why this approach rather than another, how much rigor was judged appropriate, whose hand
owns which piece, or whether the thing in front of them is finished.

Nothing was done wrong. **The choices are simply unrecoverable from the output**, so the work
cannot be reviewed, delegated, or reused, and the next person pays for the same reasoning again.

**Fires when:** work is being produced for someone else to receive, judge, or continue. Not on
a self-contained task whose output is its own evidence.

---

## The six links

### 01 — Capture the situation · *situation characterization*

**Decides:** what, exactly, is the situation — stated once, durably, before anything is worked.

**Rests on:** situation characterization, the front half of situational method engineering
(Brinkkemper; Harmsen; Rolland). Its supporting results are Taylor's question negotiation —
the presented question and the actual need routinely differ — and the vocabulary problem
(Furnas, Landauer, Gomez & Dumais 1987: two people spontaneously choose the same term for the
same concept under 20% of the time).

**The discrimination:** a situation is an **object**, not a preamble. It persists, it can be
pointed at later, and everything downstream references it. A situation re-described each time it
surfaces has not been captured — it has been re-narrated, and nothing can be held against it.

**When skipped:** every later party re-derives the problem, and no two derivations agree.

### 02 — Name it against canon · *practice routing*

**Decides:** which established practice this is an instance of — or none.

**Rests on:** the field's bodies of knowledge (SWEBOK, PMBOK, BABOK and their siblings), held
with an explicit statement of what each practice *does not* answer.

**The discrimination:** subject adjacency is not fit. **NONE is a correct answer**, and a refusal
must name the discipline that owns the problem.

*This link has a part of its own, at working depth — the index form with its negative half, the
fit test, the closed-universe rule, the chain-versus-stretch distinction, and the measured
failure modes. Load it when the routing decision is the live one.*

### 03 — Record the route · *basis of design*

**Decides:** which approach was taken, what else was available, and why.

**Rests on:** basis of design and trade study — established process-engineering practice for
recording what was chosen against what was rejected. Lightweight relatives: the Architecture
Decision Record, and Decision Analysis and Resolution in CMMI.

**The discrimination:** canon holds several valid routes to any end. The route is picked in the
moment, and the pick, the alternatives, and the reason are almost never written. **What makes
work recoverable is not the choice — it is the rejected alternatives.** A record naming only
what was done is a description; one naming what was not done, and why, is a basis.

**The form it produces:**

```
ROUTE:        <the approach taken>
REJECTED:     <each alternative considered, with the reason it lost>
WOULD FALSIFY: <what you would later observe if this pick was wrong>
```

*The falsifier line is this frame's own addition, not part of the cited canon.* Basis of design,
trade study, ADR and DAR all record alternatives and rationale; none obliges a stated falsifier.
It is added here because a rationale nobody can test is only a rationale.

**When skipped:** no reviewer, successor, or asker has anything to hold the work against.
Independent review has nothing to check, because no claim was stated to check.

### 04 — Set the weight · *tailoring*

**Decides:** how much of the practice applies here — what rigor, what depth, what ceremony.

**Rests on:** the tailoring clauses of ISO/IEC/IEEE 12207 and 15288; CMMI tailoring criteria;
PRINCE2's tailoring principle; the assurance levels of DO-178C and IEC 61508; NASA's software
classes; and Cockburn's criticality-by-team-size grid.

**The discrimination — and it is a distinction *within* that list, not a rule across it:**

- **Assurance-level standards scale on consequence.** DO-178C derives its design assurance
  levels from failure-condition severity; NASA's software classes work the same way. What
  happens if this is wrong sets the level, and nothing else does.
- **Risk-based standards scale on consequence *and* likelihood.** IEC 61508 derives safety
  integrity levels from risk, not severity alone.
- **General lifecycle tailoring is multi-factor.** 12207 and 15288 tailor on project
  characteristics that explicitly include available budget and organizational resources;
  PRINCE2 tailors on size, complexity, importance, capability and environment; Cockburn's grid
  is two-axis — criticality *and* team size.

**So the move is to know which kind you are doing.** Reaching for a resource argument inside an
assurance decision is a category error; reaching for pure consequence inside a lifecycle
decision ignores factors the standard names. Getting this backwards is the common failure and it
looks principled either way.

**The form it produces:** the setting, the factor it was derived from, and **its own failure
condition** — what you would observe if the weight had been set wrong. A weight with no stated
failure condition is a preference wearing a standard's clothes.

**When skipped:** the setting is made silently and cannot be argued with or revisited. Two
symmetric failures follow and both are invisible: full ceremony on a case that never warranted
it, and a consequential case handled at the weight of a routine one.

### 05 — Split the roles · *ownership separation*

**Decides:** whose hand owns this, whose runs it, whose consumes it.

**Rests on:** service ownership and "you build it, you run it" (Skelton & Pais, *Team
Topologies*, whose Team API publishes what a team offers and to whom); RACI for responsibility
assignment; and the assessment standards' architectural requirement that the reference model be
external to the assessor (ISO/IEC 33004) — the same separation, made structural.

**The discrimination:** a single producer performs all three roles in one voice, so the output
arrives **with no seams** — nothing marks where one hand's responsibility ends and another's
begins. Roles can be assigned to finished work afterward; RACI is applied retrospectively all the
time. What cannot be recovered afterward is *why the division falls where it does*, which is the
expertise the requester lacks and the producer never wrote down.

**The form it produces:** for each surface, three named hands — **owns · operates · consumes** —
and, where any is unfilled, the word `unassigned` rather than a blank.

**When skipped:** the output reads as finished but cannot be handed on, because no part of it
says who is meant to hold which piece.

### 06 — Become a real form · *genre selection*

**Decides:** what this becomes in the world — an email, a form, a standing process, a published
model — and who receives it.

**Rests on:** **no single practice owns this whole decision, but several own parts of it, and
naming them is obligatory under link 02's own rule.** Genres of organizational communication
(Yates & Orlikowski 1992; Orlikowski & Yates 1994) is the literature whose subject is which
recognized form a communication takes in an organization and what the community will accept.
PRINCE2's product-based planning and its Product Description name what the work becomes, its
composition, its acceptance criteria and its approver. ISO/IEC/IEEE 15289 specifies the
information items a lifecycle produces and the content of each. Media richness (Daft & Lengel
1986) fits form to equivocality. Boundary objects (Star & Griesemer 1989) covers the form work
takes when it must cross into another community. ITIL service transition names the event where a
working thing becomes an organizational one.

**The discrimination:** producing an internal artifact is not the terminal step. The terminal
step is when the work leaves the producer's own workspace and enters the organization's. These
are different events, and the first is routinely mistaken for the second.

**When skipped:** work stops one step short, reliably. A complete, well-made artifact sits where
it was made, and nothing enters the organization.

---

## What this frame is actually for

Links 02 and 06 attract effort, because both are visible — naming things is satisfying, producing
things is legible. Links 03, 04 and 05 attract almost none, and they share the property that
makes them the payload: **each is a point where a choice is made that does not appear in the
output.** Which route. How much. Whose hand.

**Order is not free, despite the numbering.** Link 04 cannot set the weight of a practice link 02
has not named, and link 05 cannot split roles over a form link 06 has not chosen. Links 01–02 and
04–06 are ordered; link 03 records whatever was just decided and can run after any of them.

A situation may close at link 02 and owe nothing further. Saying so is a legitimate outcome and
better than manufacturing the remaining four.

---

## Established practice this rests on

Named so the relevant knowledge can be loaded directly rather than reconstructed:

- **Situational method engineering** — situation characterization and method assembly (link 01).
- **Taylor's question negotiation** (1968) and **the vocabulary problem** — Furnas, Landauer,
  Gomez & Dumais (1987), the under-20% result (link 01).
- **Bodies of knowledge** — the SWEBOK / PMBOK / BABOK pattern (link 02).
- **Basis of design and trade study**; **Architecture Decision Record**; **Decision Analysis and
  Resolution** (link 03).
- **Tailoring** — ISO/IEC/IEEE 12207 and 15288 tailoring clauses, CMMI tailoring criteria,
  PRINCE2's tailoring principle, DO-178C design assurance levels, IEC 61508 safety integrity
  levels, NASA software classes, Cockburn's criticality-by-team-size grid (link 04).
- **Service ownership** and the Team API — Skelton & Pais, *Team Topologies*; **RACI**;
  **ISO/IEC 33004** on assessor-model separation (link 05).
- **Genres of organizational communication** — Yates & Orlikowski; **PRINCE2 Product
  Description**; **ISO/IEC/IEEE 15289**; **media richness** — Daft & Lengel; **boundary
  objects** — Star & Griesemer; **ITIL service transition** (link 06).

---

*The falsifier requirements in links 03 and 04 are this frame's own additions and carry no
external authority. Everything else here is established practice, named so it can be checked.*
