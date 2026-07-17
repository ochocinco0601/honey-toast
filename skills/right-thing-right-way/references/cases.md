# Pressure-Tested Cases — Right Thing Right Way

Five cases. Each tests a different dimension of the framework composition. Use for pattern matching when encountering similar situations.

## Case 1: Alert Enrichment — Knowledge Exists, Single Role

**Situation:** Platform team has 200 alerts. When one fires, 30-60 minutes to figure out business impact. The knowledge exists in people's heads — they reconstruct it every incident.

**Altitude 1:** Business outcome = faster incident response. Pipeline = alerts → investigation → impact assessment. Bottleneck = impact assessment (manual, slow).

**HPT Diagnosis:** Information + Resources gap. They KNOW the business context — they reconstruct it every time. They lack structure and tools to capture it once.

**Altitude 2:** Intervention = JPA (not training). A performance aid that guides alert enrichment: pick an alert → answer four questions → AI structures the answers → review. The IC provides knowledge; the AI provides structure.

**Key Finding:** HPT correctly identified this as NOT a training problem. The intervention is information + resources (JPA), not knowledge/skills (training).

---

## Case 2: Inherited Service — Knowledge Doesn't Exist Internally

**Situation:** Platform team inherited a service 3 months ago. They know the alerts technically but NOT the business context — who the stakeholders are, what "healthy" means from a business perspective.

**SIPOC revealed:** The supplier is MISSING. In Case 1, the IC is their own supplier (they carry the knowledge). Here, the knowledge has to come from external sources — Confluence, Jira, the dev team, the PO.

**HPT Diagnosis:** Information + Resources + Knowledge gap. This time it IS partly a knowledge gap — but not one solved by training. The knowledge exists elsewhere and needs to be FOUND, not taught.

**Altitude 2 adaptation:** JPA gains an additional first step: "Where can you find business context for this service?" Options: Confluence pages, Jira epics, runbooks, the dev team, the PO. Output is confidence-marked ("inferred from runbook" vs "confirmed by PO"). PO validation becomes mandatory, not optional.

**Key Finding:** The composition ADAPTS rather than breaks. Same frameworks, different output because SIPOC revealed a missing supplier and HPT diagnosed a different gap.

---

## Case 3: Production Handoff — Multiple Roles, Handoffs

**Situation:** Dev team built a capability, handing off to platform for production support. Three roles: PO (business context), Dev (signal implementation), Platform (operationalize).

**SIPOC at multiple levels:** The handoff is the FULL onboarding process compressed into one event. Three linked SIPOC chains — PO's output is Dev's input, Dev's output is Platform's input.

**HPT per role:** Different diagnoses for different roles:
- PO: Information + Resources gap (has business knowledge, lacks structure)
- Dev: Information + Resources + partial Knowledge (may not know ratio query translation)
- Platform: Information + Resources (sets thresholds today, just needs structured input)

**Altitude 2:** Three LINKED JPAs, not one. Each produces output consumable by the next role. Standards defined by the consumer at each boundary.

**Key Finding:** SIPOC handles multi-role by running per-function. HPT diagnoses DIFFERENTLY per role. JPA design produces linked aids. The handoff quality depends on output consumability at each boundary.

---

## Case 4: New Observability Practice — Process Doesn't Exist

**Situation:** Auto Lending has never done structured business observability. Basic infrastructure alerts exist. No business health signals. The PO has been told "we need business observability" and doesn't know what that means.

**SIPOC shift:** Descriptive → Prescriptive. No process to map, so SIPOC designs the process.

**HPT Diagnosis:** Information + Resources + Knowledge + Incentives. Almost everything is missing. This is fundamentally different from Cases 1-3.

**Altitude 2 adaptation:** JPA alone FAILS — the performer lacks the conceptual foundation. Intervention is PHASED:
1. Organizational mandate (incentives)
2. Four questions + domain-relevant example (information + knowledge)
3. One service onboarded manually with facilitation (practice before platform)
4. JPA for repeating independently (resources)
5. AI tools for acceleration (only after the practice works)

**Key Finding:** HPT correctly diagnosed a fundamentally different gap. The intervention type changes from "JPA" to "phased enablement." The composition produces a PHASED design, not single-shot. "Practice before platform" is load-bearing.

---

## Case 5: Manual Onboarding — No AI Involved

**Situation:** Same onboarding process using spreadsheets and Confluence. No Copilot, no AI.

**Result:** The composition works IDENTICALLY without the AI layer. Backward Design, SIPOC, HPT, Task Analysis, JPA Design, Gagné — all produce the same output. The JPA changes form (spreadsheet instead of prompt) but not substance (same questions, same sequence, same standards).

**Key Finding:** Human-AI Task Allocation is a module, not a dependency. The composition designs for the WORK, not the tool. AI accelerates the work but doesn't define it. Validates "practice before platform."

---

## Cross-Case Synthesis

**What held across all cases:**
- Backward Design (start from outcome, close with evidence) — all 5
- SIPOC (map the process, reveal boundaries) — all 5 (descriptive or prescriptive)
- HPT (diagnose the gap, route the intervention) — all 5, PIVOTAL
- Task Analysis (conditions/standards/performance) — all 5
- Gagné (session structure) — adapts naturally per gap type

**What HPT diagnosed differently (the router in action):**
- Case 1: Info + Resources → JPA
- Case 2: Info + Resources + Knowledge (external) → JPA with knowledge acquisition step
- Case 3: Different per role → linked JPAs
- Case 4: Info + Resources + Knowledge + Incentives → phased intervention
- Case 5: Info + Resources → JPA (spreadsheet form)

**The single most important finding:** HPT is the pivotal framework. It prevents treating every enablement problem the same way. Without it, you default to "build a JPA" or "run training" regardless of the actual gap. HPT forces the diagnostic, and the answer changes everything downstream.
