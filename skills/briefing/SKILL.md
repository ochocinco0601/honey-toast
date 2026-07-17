---
name: briefing
description: >
  Produce and evaluate stakeholder briefing products using established intelligence,
  military, and business communication standards. Use this skill when producing ANY
  stakeholder deliverable: options lists, decision briefs, roadmap bullets, status
  updates, meeting prep materials, assessments, or presentations. Also use when
  evaluating a draft briefing for quality. Triggers on "create a briefing",
  "draft options for", "roadmap bullets", "status update", "decision brief",
  "evaluate this briefing", "brief [person]", or proactively when stakeholder
  deliverable production is detected at any organizational altitude. This skill
  enforces ICD 203 analytic tradecraft standards, FM 6-0 military briefing doctrine,
  Minto Pyramid Principle, CIA intelligence writing standards, and Amazon Working
  Backwards — adapted for enterprise engineer-to-leadership communication.
---

# Briefing Production & Evaluation

---

## Gotchas

These are failure modes AI agents hit repeatedly when executing this skill, despite the instructions.

1. **Presents multiple SCQA framings for user to choose** — Contractor mode. Pick the best framing, commit to it, defend it if challenged. The user validates; the user doesn't choose from menus.
2. **Names frameworks in the deliverable** — "Per ICD 203 standards..." or "Following Minto Pyramid..." appears in the output. Apply the standards invisibly. The consumer doesn't care about your methodology — they care about the product.
3. **Mode collapse under revision pressure** — When the user pushes back on a draft, switches from "expert analyst refining the brief" to "execution worker applying edits." Pushback means engage on substance, not capitulate and rewrite mechanically.
4. **Hedging qualifiers instead of uncertainty expression** — Writes "approximately" and "to date" instead of using Criterion #4 (confidence levels, tested vs. theoretical). Hedging adds words without adding signal.

---

## Workflow

### Phase 1: Type Selection

Determine briefing type BEFORE writing.

| Type | Consumer needs to... | Structure |
|------|---------------------|-----------|
| **Decision Brief** | Choose between alternatives | Problem → Options → Evaluation → Recommendation → Decision Requested |
| **Information Brief** | Gain awareness | BLUF → Facts → Implications |
| **Status Brief** | Know progress and blockers | BLUF → Done → So What → Next → Blocked → Ask |
| **Assessment** | Understand expert judgment | Key Judgments → Evidence → Alternatives → Outlook |

Source: FM 6-0 (U.S. Army doctrine) briefing type taxonomy.

### Phase 2: Consumer Analysis

Before writing:

1. **Who?** Name, role, altitude (CIO/MD/Manager/IC).
2. **What do they know?** Don't re-explain bought concepts. If the audience already has the concept, show operationalization — not justification.
3. **What decision or action?** Determines what belongs.
4. **Their language?** Write in consumer's terms, not analyst's. PDB standard: "the president's language, not officialese."

### Phase 2.5: Load Voice Governance

Before drafting, if the `/editorial` skill is available, invoke it to load editorial governance. If not available, apply these ambient principles:
- Validate their problem before introducing solutions
- Enabling language, not automatic language
- Collaborative framing, not product framing
- Respect their vocabulary
- Accurate capability claims
- Outside-in framing (reader's world first)
- Word economy is a production constraint

### Phase 3: Draft Using SCQA + What/So What/Now What

**Opening — SCQA (Minto Pyramid Principle):**
- **S**ituation — shared context consumer agrees with
- **C**omplication — problem or change creating urgency
- **Q**uestion — what needs addressing
- **A**nswer — key judgment or recommendation (= the BLUF)

**Body — What / So What / Now What (CIA Kent School):**
- **What** — the facts
- **So What** — why it matters to THIS consumer
- **Now What** — forward-looking action or implication

### Phase 4: Self-Evaluate Against 10 Core Criteria

Evaluate BEFORE delivery. Fail multiple → revise before presenting.

| # | Criterion | Quick Test |
|---|-----------|------------|
| 1 | **BLUF** | Key judgment in paragraph 1? |
| 2 | **Consumer-oriented** | Every section serves READER's need, not analyst's? |
| 3 | **Fact-judgment separation** | Reader can distinguish evidence from inference? |
| 4 | **Uncertainty expressed** | Confidence levels tagged? Tested vs. theoretical? |
| 5 | **Alternatives considered** | Analyst challenged own thinking? |
| 6 | **Assumptions stated** | What must be true for this to hold? |
| 7 | **Risks and failure modes** | "This fails if [X]" for each option? |
| 8 | **Actionable with clear ask** | Consumer can act same day? Decision explicitly requested? |
| 9 | **Logical structure** | Conclusions traceable to evidence? |
| 10 | **Prioritized** | Most important first? Options ordered by judgment of fit? |

### Phase 5: Type-Specific Criteria

**Decision Brief** — also requires:
- Problem as specific question, options are MECE, evaluation criteria weighted, resource implications per option, recommendation included

**Status Brief** — also requires:
- Change from prior noted, metrics quantified, accountability visible, blocked items include path to resolution

**Assessment** — also requires:
- Forward-looking outlook, source quality characterized, analytic line stated

Full criteria with provenance: `references/criteria-detail.md`

### Phase 6: Save and Deliver with Scorecard

Save to the location specified by the calling context. If none specified, save to the directory containing the files being analyzed.

Present evaluation scorecard alongside the deliverable. The user sees both the product and the quality assessment.

---

## Anti-Patterns

| Failure | What happens |
|---------|-------------|
| No BLUF | Consumer reads analysis without knowing the bottom line |
| Builder perspective | Methodology jargon, field names, system architecture consumer doesn't need |
| Equal grounding illusion | Tested and theoretical options presented as equally certain |
| Success path only | No failure modes, no assumptions, no "this fails if" |
| Vague ask | "Open questions" instead of specific decision request |
| Arbitrary ordering | Options in order of creation, not priority |

### AI Agent Anti-Patterns

When the briefing skill is used by an AI agent, additional failure modes apply:

| Failure | What happens |
|---------|-------------|
| Performative approval | "Great start!" followed by substantive failures — misleads about quality. Lead with what fails. |
| Corporate filler | Sentences that sound like content but carry no information. Test: remove the sentence; if nothing is lost, it was filler. |
| Invented specifics | Plausible numbers, dates, or names the analyst didn't provide. Use gap markers: `[INSERT: count]` |
| Hedging language | "Approximately," "to date," unnecessary qualifiers that add words without adding uncertainty signal. If confidence is genuinely uncertain, use Criterion #4 — not hedging adjectives. |

---

## Altitude-Aware Delivery

Same knowledge, different resolutions. When producing at multiple altitudes, verify consistency across levels.

| Altitude | Resolution |
|----------|-----------|
| Executive | Quarterly bullets — highest compression |
| CIO | Operational picture + what's achievable |
| Director/Manager | Execution options with trade-offs |
| Portfolio | Status + metrics + milestones |
