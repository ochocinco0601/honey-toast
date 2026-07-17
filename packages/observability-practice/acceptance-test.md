# Acceptance Test — Does a Reader Hold the Whole?

**What this is:** the comprehension check for the observability discipline — the criteria a reader (or an AI agent) meets to show they hold the whole of it, not just skimmed the pages. It is written so the material can be tested against it: a failed or shallow answer points at where the material didn't land, and the fix is to the material, not the answer.

**Method:**
1. A cold reader — someone (or an agent) with no prior context — answers every question below from the material alone.
2. Each failed or shallow answer locates a gap in the material.
3. Iterate the material until a cold reader passes.
4. The check also serves as a self-test for anyone entering the discipline fresh.

**Scoring:** no grades. Per question: PASS (answer contains the required elements) / GAP (element missing or unfindable) / DRIFT (answer present but wrong in a way the tells below predict). GAP and DRIFT both name the section to fix.

**Anti-gaming rule:** questions are answered in the reader's own words with citations to the material. Verbatim retrieval of a single paragraph is not comprehension.

---

## A. The whole

**A1. State the mission this discipline serves, without leaning on the word "observability."**
Pass requires: an organization able to see whether its business capabilities are working — all of them, at every level, agentic included; carried by a defined, repeatable way of working (a discipline), because it must happen for many capabilities and teams, not once; and the space between describing that outcome and making it true — the activities, who performs them, the methods, the coordination — is the real content of the work.
DRIFT tell: mission stated as "monitor the AI agents."

**A2. What forces this work, and how does the forcing function differ from the outcome?**
Pass requires: the forcing function is an anticipated leadership question ("are we ready?"); that urgency is not the outcome. The outcome is the discipline that makes the question answerable repeatably, by anyone, any time, from records. A readiness answer is the discipline's first output, not its definition.

**A3. What is the deliverable — and what is explicitly NOT delivered?**
Pass requires: the discipline *defined and made performable* — the standard, the instrument, the records machinery, the operating description. NOT delivered: the discipline *performed* — performers, owned rhythms, and gate authority are organizational decisions no artifact can make. NOT the deliverable: a tool, an agentic-only answer, or a one-time position paper.
DRIFT tell: artifact completion treated as mission-complete.

## B. Layers of abstraction

**B1. Walk the chain from a leadership question down to a signal.**
Pass requires the chain in order — stakeholder → expectation → impact → signal → playbook (who cares; what they expect; what a breach costs; the measurement that tells you, on a stated target; what happens when it fires) — with the rule that good = every position filled and traceable, deficiency = a position that cannot be filled when walked.

**B2. Name the layers between the business and the technology. Which tend to be recorded in enterprise systems, which are not?**
Pass requires the unit ladder — value stream → process → flow → service → application → component (labels disposable); the recorded ends are usually the top (critical products) and the bottom (application/component inventories); the middle — flows, journeys, capabilities — is typically unrecorded, and closing that gap is what the discipline's records exist to do.

**B3. Where does the agentic content sit in the structure — and what happens to the whole if you remove it?**
Pass requires: agentic is one *conditional* stratum inside the discipline — an added signal set for a step that can be confidently wrong (up, healthy, and deciding wrong); it activates per service. Remove it and the whole stands unchanged — the whole is not agentic.
DRIFT tell: the discipline read as "an agent-monitoring methodology."

## C. Discipline / practice / standard

**C1. Distinguish the discipline, the practice, and the standard.**
Pass requires: discipline = a practice + a standard + an operating leg (who performs, what coordinates); practice = the activities run per capability (identify & tier → define working → instrument → record readiness → rhythms read the records); standard = the written definition of good, in three forms.

**C2. Name the three forms of the standard and explain — with a concrete example — why one form alone fails.**
Pass requires: A model (teaches) / B record (captures) / C test (verifies); authored separately they drift. A record without a test decays into attestation — green statuses nobody computed (e.g. a service reads green on the surface teams use to decide, while an unmonitored dependency path is actively failing). A test with no model at the right grain decays into form-filling.

**C3. What is the relationship between tooling and the discipline?**
Pass requires: the discipline and the practice are true without any specific tool; tools exist to make the practice easier, and the discipline is never described as the tooling. ("Vendors will sell you observability, but you can't buy it.")
DRIFT tell: adopting a specific tool presented as the goal.

## D. State and epistemics

**D1. How does the discipline separate what is known from what is assumed?**
Pass requires: facts (stated by the domain owner) versus derivations (analysis that stands or falls with the facts under it); endorsement means plausible / fits reality, never verified; claims held at the grain of memory are flagged for primary-source verification against the actual systems in the operating environment.

**D2. Which claims require verification against the operating environment's primary sources, and how would that be done?**
Pass requires: environment-specific facts — the actual instrumentation standards, the default telemetry per platform, the real review cadences, the true denominators — are verified against the environment's own systems (configuration databases, consoles, documentation), cold, expecting heterogeneity (answer per platform, never one estate-wide answer).

**D3. What is the difference between what exists as an artifact and what is actually true in the operating world?**
Pass requires: an artifact's maturity is not adoption; a practice defined is not a practice performed; recorded intent is not recorded reality.
DRIFT tell: reading artifact maturity as organizational adoption.

## E. Can the reader act

**E1. Someone asks "are we ready?" tomorrow. Sketch the answer's shape.**
Pass requires: what "ready" means (a capability's record answers who cares / expectation / breach cost / signals per layer / who acts — plus decision-level evidence for agentic steps); where we stand (coverage as a fraction, computed from records, never hand-compiled); the specific gaps; and the organizational decisions the answer surfaces (who performs, who owns record currency, who owns the rhythm) — the ask hiding inside "are we ready."

**E2. A gate is asking a delivery team monitoring questions with no written standard behind them. Using the discipline: what is that moment, and what does the practice change about it?**
Pass requires: that is the enforcement gate operating without a standard behind it — a demand signal for shifting the work left, not the model to institutionalize; the practice runs left of the gate (define at design, instrument in build, record in the same cycle) so the gate becomes a lookup of a current record, not an interrogation.

**E3. Which decisions belong to whom?**
Pass requires: fit-judgment, sequencing, and domain facts belong to the domain owner; craft, derivation, and verification belong to the producer; who performs, rhythm ownership, gate authority, and adoption belong to the organization. Never ask the domain owner what a practice *should* be (that is the producer's derivation); ask only what *is*, and whether the output fits.

## F. The known failure modes

**F1. Name the ways work on this material predictably goes wrong, and the tell for each.**
Pass requires at least four, e.g.: agentic-as-whole (the mission restated as agent monitoring); artifact-completion-as-mission-complete ("done" with no performer); tooling-as-discipline (adopting a tool presented as the ask); attested green (claiming health without computing it from below); forms-without-substance (a record with no test); indictment register in public (naming a specific thing as a bad example — public language is positive exemplars and distance-from-target only); understanding-living-in-a-person (a step that requires someone to supply context from memory).

---

## Coverage map

| Group | What it verifies |
|---|---|
| A | The mission and its boundaries |
| B | The layers and the missing middle |
| C | The discipline's anatomy |
| D | Epistemic discipline and real-world state |
| E | Ability to act, not just describe |
| F | Resistance to the known failure modes |

A reader who produces PASS across A–F holds the whole. Anything less locates its own gap.
