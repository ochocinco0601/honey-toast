---
name: requirements
description: Elicit and structure requirements before any new work begins — skills, protocols, methodology, deliverables, software features. Covers functional requirements, quality attributes, failure definition, stakeholder analysis, outcome specification, data context, and prior art research, grounded in the Volere Requirements Specification Template. Use when the user says "let's gather requirements", "what should this do", "I want to build something", "requirements for", or when the user invokes /requirements. Also use proactively when new capability work is starting without externalized requirements. The skill ensures comprehensive, consistent requirements coverage — not just user stories, but the full context needed to build correctly. Includes outside-in story orientation checking, concept verification, and expertise-adapted elicitation.
---

# Requirements — Structured Elicitation for Any Work

Elicit requirements through thinking-partner dialogue. Produce a consistent artifact regardless of work domain.

## Why This Skill Exists

AI agents already know how to have a requirements conversation. Two problems emerge without structure: inconsistent format (each session produces different output shapes), and incomplete coverage (entire requirement categories get missed). The skill solves both — consistent artifact structure AND comprehensive elicitation grounded in the Volere Requirements Specification Template (Robertson & Robertson), the established standard for requirements coverage.

## Mode: Thinking Partner

You are a thinking partner, not an execution worker. This is the hardest instruction in this skill because the mode sustainment failure is well-documented — AI agents read "be a thinking partner," acknowledge it, then encounter something actionable and drop into production mode.

Concretely, what thinking-partner mode means here:

- **Propose hypotheses, not questions.** Instead of "who is the actor?" say "I think the actor is [X] because [Y] — does that match?" Hypotheses are challengeable. Questions put the burden on the user.
- **Use scenario walkthroughs.** "Here's how I think someone uses this..." forces concrete assumptions that the user can correct. Abstract discussion hides misunderstanding.
- **Challenge back.** When something doesn't add up, say so. "You said X, but that seems to conflict with Y" is partnership. Accepting everything uncritically is order-taking.
- **Don't rush to produce the artifact.** The conversation IS the work. The artifact captures what the conversation produced. If you haven't had your assumptions corrected at least once, you probably haven't probed deep enough. The skill has 20 elicitation areas, a quality gate, and a prior art research obligation — all of which happen through dialogue before the artifact is written. This isn't a checklist to race through.
- **Own the methodology.** The user owns domain truth ("is this one use case or two?"). The agent owns requirements methodology ("should this be one story or two?"). When the user says "I'm not a requirements expert" — that's your cue to explain the reasoning (e.g., INVEST criteria) and make the recommendation, not defer the decision to them. Teach the vocabulary as you use it.
- **Calibrate to expertise.** Assess the user's relationship to requirements methodology from their language and questions. Signal unfamiliarity → teach vocabulary and explain reasoning. Demonstrated expertise → engage at peer level without over-explaining.
- **Observe format preferences.** When the user requests a specific format (diagrams, monospace, tables), adapt for the remainder of the session including the final artifact.

## Opening Move: Directional Validation

Before eliciting stories, run a directional validation diagnostic. This is unconditional — it runs every time, like a pre-flight checklist runs before every flight regardless of crew experience or route familiarity. For clear, well-understood work, the diagnostic completes quickly as a fast pass. For ambiguous work, it takes longer. Neither case skips.

If the `/right-thing-right-way` skill is available, invoke it. If not, apply this inline diagnostic:

### Inline Directional Diagnostic

**Step 1: Hypothesize before responding.** Reason through:
- What business outcome does this work serve? (not "what artifact" — what changes in the world)
- What pipeline produces that outcome? Who does what, for whom?
- Where is the pipeline stuck? Why?

Diagnose using Gilbert's six factors (Human Performance Technology, *Human Competence*):

| Factor | Question |
|---|---|
| **Information** | Do they know what's expected? |
| **Resources** | Do they have the tools and materials? |
| **Incentives** | Is there meaningful consequence for performing? |
| **Knowledge/Skills** | Do they know how to do it? |
| **Capacity** | Are they able? |
| **Motives** | Do they want to? |

Address environment factors (1-3) before individual factors (4-6). Most gaps that look like knowledge problems are actually information or resource problems.

**Step 2: Semantic alignment.** Identify pivotal terms — words the diagnosis hinges on. For each: state what YOU mean, show what changes if the definition is wrong. Present as a table the user can react to by row.

**Step 3: Present the diagnostic checkpoint:**
```
**Business outcome:** [what needs to advance]
**Bottleneck:** [where the pipeline is stuck]
**Gap type:** [Information / Resources / Knowledge / etc.]
**Evidence:** [why I think this]
**Considered:** [alternatives weighed and why ruled out]

**Does this match what you're sensing?**
```

When the user confirms direction, proceed to Elicitation Areas below.

### Output Integration

The diagnostic's output seeds the requirements work:
- **Problem framing seed:** The validated diagnosis becomes the starting problem framing. Elicitation builds on it.
- **Semantic alignment:** Pivotal terms grounded during the diagnostic carry forward. Do not re-ground them.
- **Actor/stakeholder context:** The diagnostic identifies who's involved. This informs elicitation areas 1-2.

### Skip Override

The user can say "skip the diagnostic." If so, the Problem Framing Evaluation gate (later) still catches framing issues.

## Elicitation Areas

There is no rigid sequence — these emerge through dialogue, not a checklist. Propose scenarios, let the user correct, iterate. Before writing the artifact, verify coverage: each area should be either addressed or consciously determined to be not applicable. The areas below are informed by the Volere Requirements Specification Template (Robertson & Robertson).

### Core Identity

1. **Who is the actor?** Not who you'd assume. State as a hypothesis and get confirmation.

2. **Who else has a stake?** The actor is the primary user, but stakeholders include everyone affected by, who approves, or who constrains the work. Different stakeholders have different requirements. (Volere §2: The Stakeholders.)

3. **What is the base case?** Not the interesting edge case. Getting this wrong means building for the secondary scenario.

4a. **What does the audience encounter when this exists?** Not what the builder does. Not how the system works internally. What does the person who arrives at the finished product see, experience, or gain the ability to do? Describe from their perspective, not the builder's.

    **Requester ≠ audience.** The person who requests the work is not always the person who encounters the result. Identify both.

    This is the Commander's Intent formulation (US Army doctrine; Marquet, *Turn the Ship Around*): state the desired end state from the perspective of the people it serves, not the people who build it.

    **Perspective test:** Read your outcome statement and ask — is this describing what the builder does, or what the audience experiences?

    **Sharpness test:** The outcome statement must be specific enough that misaligned implementation would be *visibly wrong* against it. "For a PE to use as a reference" doesn't constrain. Sharpen until wrong implementation would be visible.

    Propose the outcome as a hypothesis: "I think this is for [person] to [experience/do what]."

4b. **How do we test that?** Testable acceptance criteria that verify the outcome in 4a.

**Story orientation.** Stories describe what the USER needs, not what the SYSTEM does. Apply journey-first framing (Patton, User Story Mapping): start from the user's experience, not the component architecture. If a story's actor is the system rather than the user, reorient before including it.

### Domain & Data

5. **What data does this work operate on?** Identify the key entities, relationships, and data flows in the problem domain. You can't write requirements in a vacuum — stories that sound right but don't account for the actual data structure they'll touch will fail during build. (Volere §7: Business Data Model.)

### Boundaries

6. **What is out of scope?** Explicit exclusions prevent scope creep during build. Unstated boundaries get violated.

7. **What constraints exist?** Things the solution must work within — existing patterns, token budgets, mode limitations, integration points.

8. **What assumptions are we making?** Different from constraints. Constraints are known limits. Assumptions are things taken as true that could be wrong. State them explicitly so they can be validated or challenged. (IEEE 830, BABOK)

### Context

9. **Why does this work exist?** What problem triggered it? What happens if we don't build it? (IEEE 830 Section 1: Purpose.)

10. **How is this handled today?** What's the current workaround, manual process, or gap? Probe for the SYSTEM of compensating mechanisms — related workarounds, tools, processes, and informal practices. Understanding the full system prevents building something that duplicates or disrupts existing workarounds. (Volere §9: Current Environment.)

11. **What does this replace or displace?** If something exists today that the new work supersedes, what happens to it? When the new thing arrives, the old thing doesn't vanish — it creates a transition problem. If nothing is being replaced, say so and move on. (Volere §22: Migration.)

12. **What does failure look like?** Not just "what could go wrong with the solution" but "what does the world look like when this thing doesn't exist or doesn't work?" This clarifies the value proposition.

13. **When does this problem NOT occur?** Probe for boundary conditions. If the user can describe contexts where the problem is absent, the framing sharpens. If they can't, the problem may be too vaguely defined. (Falsifiability — adapted from Popper.)

14. **Can you point to a specific instance?** Ask for a concrete, recent example where this problem manifested. Not a hypothetical — a real event with real consequences. (Evidence-based practice.)

### Prior Art Check

15. **Has this problem already been solved?** This is the agent's research obligation, not a question for the user. The user may not know that an established standard, framework, library, or pattern exists.

    Before investing effort in stories and artifact production, STOP and research:
    - Name the problem domain explicitly
    - Search for established standards, frameworks, or tools that address it
    - Present what exists, how well it fits, and what it doesn't cover

    Present findings to the user. The user decides whether to adopt, adapt, or build custom. If nothing established exists, say so explicitly — that's valuable information too.

### Quality Attributes

16. **What quality attributes matter for this work?** Probe for the relevant ones during dialogue. (Volere §10-17, adapted for all work types.)

    | Attribute | Example |
    |-----------|---------|
    | **Look & Feel** | Visual design, presentation quality |
    | **Usability** | Can the audience act on this without explanation? |
    | **Performance** | Response time, throughput, context window consumption |
    | **Operational/Environmental** | Deployment environment, platform constraints |
    | **Maintainability** | Can someone modify this later? Who owns it? |
    | **Security** | Data sensitivity, access control |
    | **Cultural** | Enterprise vocabulary, stakeholder tone expectations |
    | **Compliance** | Regulatory context |

    Surface the relevant attributes during dialogue. Irrelevant attributes are simply omitted.

### Failure Inversion

17. **Tell the story of this failing.** This is the pre-mortem (Gary Klein, Prospective Hindsight): assume the work is complete, every requirement met, every acceptance criterion green — and it still failed. Narrate how.

    This is NOT "what could go wrong with the implementation" — that's component-level risk analysis. This is holistic failure: the initiative doesn't achieve its purpose despite meeting all specs. Research shows prospective hindsight produces 30% more failure explanations than "what could go wrong?" because assuming failure has already occurred removes optimism bias.

    Propose a failure narrative as a hypothesis: "I think this fails when..." Let the user correct or expand.

    This question scales with the work:
    - For a small tool: "It's built to spec. Three months later it's abandoned. Why?"
    - For a workstream: "Every component delivers. The initiative still failed. Tell me the story."
    - For methodology: "Every requirement green. Nobody's behavior changed. How?"

18. **How does the solution itself break?** Distinct from the holistic failure narrative. This asks about component-level failure modes — what does bad output, broken behavior, or degraded performance look like?

19. **What new problems does success create?** Assumes the work SUCCEEDS and asks: what didn't exist before that now exists because you built this? These are problems CAUSED by the solution working, not by it failing. (Volere §20: New Problems.)

### Dependencies

20. **What must exist for this to work?** Other artifacts, infrastructure, data, patterns, decisions. Dependencies that aren't stated become invisible blockers during build.

## Problem Framing Evaluation

When the user signals readiness to produce the artifact, run this evaluation BEFORE writing any stories. This is a quality gate — it ensures that the foundation under every user story is sound.

**Announce the gate** by name before running it. The user must know what process ran and be able to verify it.

### Step 1: State the Problem Framing

Synthesize a 2-4 sentence problem statement from the dialogue. The statement must:
- **Name the situation** — what's happening, or what's not happening that should be
- **Name the affected actors** — who experiences the problem, who bears the consequence
- **Name the consequence** — what this costs, breaks, or prevents in concrete terms

### Step 2: IS/IS NOT Specificity Check

Apply Kepner-Tregoe IS/IS NOT analysis to sharpen the framing. A vague problem statement can't be meaningfully evaluated.

| Dimension | IS | IS NOT |
|-----------|-----|---------|
| **What** is the problem? | [specific behavior or gap] | [adjacent problems explicitly excluded] |
| **Where** does it occur? | [specific context, scope, system] | [where it doesn't occur] |
| **When** does it manifest? | [trigger conditions, timing] | [conditions where it's absent] |
| **Extent** | [how much, how many affected] | [what's unaffected] |

For simple problems, IS/IS NOT may be stated inline rather than as a table.

### Step 3: Analytical Tests

Apply five tests. Each produces a pass/fail with one-sentence evidence. All must pass before proceeding to user stories.

| # | Test | Question | Pass Condition |
|---|------|----------|----------------|
| 1 | **Symptom vs Root Cause** | Can you ask "why does this happen?" and get a deeper answer that changes what you'd build? | No deeper "why" changes the scope. (Ohno / 5 Whys) |
| 2 | **Solution Independence** | Remove any proposed solution from the framing. Does the problem still describe a real situation? | Problem is stated as a condition, not the absence of a solution. (IEEE 830) |
| 3 | **Consequence Test** | What specifically happens if this is never solved? | Consequence is concrete and non-trivial. (Goldratt / Theory of Constraints) |
| 4 | **Key Assumptions Check** | What is the framing taking for granted? Would the problem change if any assumption were wrong? | All critical assumptions stated. (Heuer & Pherson, Structured Analytic Techniques) |
| 5 | **Outcome Perspective** | Is the desired outcome described from the audience's perspective? Sharp enough that misaligned work would be visibly wrong? | The outcome describes an observable state in the audience's world. (Commander's Intent, Marquet) |

### Gate Behavior

- **All pass:** State results concisely, proceed to output artifact.
- **Any fail:** Name the failing test(s), explain what's specifically wrong, and re-enter dialogue targeting the gap. Don't ask generic "can you clarify?" — ask the specific question the failing test implies.
- **Scaling:** For simple problems, the tests pass trivially and the gate is one paragraph.

### Presentation

Show the evaluation to the user. The gate is visible work, not invisible checking.

```
**Problem Framing Evaluation**

**Framing:** [2-4 sentence problem statement]

**IS/IS NOT:** [table or inline summary]

| Test | Result | Evidence |
|------|--------|----------|
| Symptom vs Root Cause | PASS | [one sentence] |
| Solution Independence | PASS | [one sentence] |
| Consequence | PASS | [one sentence] |
| Key Assumptions | PASS | [one sentence] |
| Outcome Perspective | PASS | [one sentence] |

**Gate: PASS** — proceeding to artifact.
```

## Output Artifact

When the gate passes, produce a DRAFT artifact in this structure. The draft is part of the elicitation — present it as "here's what I think we have" for the user to review, not as the finished product.

```markdown
# Requirements: [Title]

**Date:** YYYY-MM-DD
**Status:** Draft | Accepted
**Work type:** [skill | protocol | methodology | deliverable | software | other]

## Background

**Problem:** [The evaluated problem framing. 2-5 sentences.]

**Goal:** [What the audience encounters when this work is done. One sentence if possible.]

**Stakeholders:** [Actor] (primary), [other stakeholders].

**Audience:** [Who encounters the finished product — may differ from the actor.]

**Success evidence:** [Measurable, observable outcomes.]

**Data context:** [Key entities and relationships this work operates on.]

**Replaces/displaces:** [What exists today that this supersedes. "None" if greenfield.]

## Failure Definition

**Holistic failure (pre-mortem):** [What it looks like when every requirement is met and the work still fails. 2-4 sentences.]

**Solution failure modes:**
- [failure mode] — [implied requirement or acceptance criterion]

**New problems created by success:**
- [problem that success introduces] — [what it implies]

## Quality Attributes
[Only the attributes relevant to this work.]
- [attribute category]: [requirement] — [why it matters]

## User Stories

### Story 1: [Descriptive title]

**As a** [actor], **I want** [capability], **so that** [value].

**Acceptance Criteria:**
- Given [context], when [action], then [outcome]

### Story 2: [Descriptive title]
...

## Scope Boundaries

**In scope:**
- ...

**Out of scope:**
- [exclusion] — [why it's excluded]

## Assumptions
- [assumption] — [what changes if this is wrong]

## Dependencies
- [dependency] — [what it enables]

## Constraints
- [constraint] — [source/rationale]

## Open Questions
- [question] — [why it matters, who can answer it]

## Next Step
[What happens after requirements are accepted.]
```

### Format Rules

- **User stories use the standard format:** `As a [actor], I want [capability], so that [value]` (Mike Cohn, "User Stories Applied").
- **Acceptance criteria use Given/When/Then** (BDD, Dan North). Makes criteria testable.
- **Acceptance criteria describe audience-observable states.** Given/When/Then criteria test what the audience encounters, not system internals.
- **Scope boundaries require rationale for exclusions.**
- **Assumptions state the consequence of being wrong.**
- **Failure Definition has three levels.** Holistic pre-mortem, solution failure modes, and new problems created by success.
- **Quality Attributes are selective.** Include only the relevant ones.
- **Dependencies name what they enable.**
- **The number of stories is flexible.** Could be 1 or 10.

### Story Splitting

When a proposed story feels too broad, apply **story splitting** (Mike Cohn) using the **INVEST criteria** (Bill Wake — Independent, Negotiable, Valuable, Estimable, Small, Testable). The test: does the second story surface acceptance criteria that the first wouldn't identify on its own? If yes, split.

The agent owns this decision — it's requirements methodology, not domain knowledge.

### Coverage Validation

Before finalizing the story set, organize stories by **path or dimension** — read path vs write path, actor A vs actor B, happy path vs failure path — and check that each path has stories. Also check whether stories collectively serve the outcome from 4a.

### Outside-In Story Orientation Check

After organizing by dimension, check story orientation: does each story use the user as the actor and describe a user-facing outcome? Also check outcome alignment: does each story's "so that [value]" serve the audience identified in 4a?

### Draft as Elicitation

Writing up the first draft of stories often surfaces new stories. The artifact draft is part of the elicitation process, not just the output. Present the draft as "here's what I think we have — does this surface anything missing?"

If drafting reveals that the problem framing itself was wrong — re-run the Problem Framing Evaluation rather than forcing stories to fit a bad frame.

### Artifact Location

Save to the location specified by the calling context. If none specified, save to the directory containing the files being analyzed.

## What This Skill Does NOT Do

- **Design the solution.** Requirements say WHAT, design says HOW.
- **Create a plan.** Requirements don't sequence work.
- **Replace domain-specific discovery.** This skill is domain-neutral.

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| **Questionnaire mode** | Agent walks through all 20 items sequentially, asking one question at a time | The 20 areas are a coverage map, not a script. Propose hypotheses that naturally span multiple areas. If the conversation feels like an interview, you're doing it wrong. |
| **Premature artifact** | Agent writes the requirements doc before understanding converges | The conversation is the work. Don't produce the artifact until the user signals readiness. |
| **Gate skipping** | Agent produces stories without running the Problem Framing Evaluation | The gate is visible work. Show the framing, show the test results, show the pass/fail. |
| **Perfunctory gate** | Agent runs the gate but treats it as ceremony — every test "passes" with generic evidence | Each test answer must be specific to this problem. "The framing is clear" is not evidence. |
| **Prior art amnesia** | Agent skips the prior art check or does a superficial search, then builds custom | This is the agent's research obligation. Name the domain. Search for standards. Present findings. |
| **NFR blindness** | Agent elicits functional requirements but never probes for quality attributes | Every piece of work has at least some quality attribute that matters. Surface the relevant ones. |
| **Pre-mortem skip** | Agent proceeds to stories without narrating holistic failure | The failure inversion surfaces requirements that no individual story would. |
| **Assumed actor** | Agent assumes who uses the thing without checking | State the actor as a hypothesis and get confirmation. Then ask who else has a stake. |
| **Edge-case-first** | Requirements built around interesting scenarios, not the base case | Ask "what's the most common use?" first. Edge cases come after. |
| **Scope silence** | No explicit out-of-scope section | Unstated boundaries get violated. Always ask what's NOT included. |
| **Data vacuum** | Requirements written without understanding what data the work operates on | Ground the stories in the actual entities, relationships, and data flows. |
| **Builder-perspective stories** | Stories describe system mechanics rather than what the audience encounters | Check every story's "so that [value]" against the audience identified in 4a. |
| **Performative externalization** | Outcome statement is technically audience-perspective but too vague to constrain | Apply the sharpness test: would misaligned implementation be visibly wrong? |
| **Requester-as-audience** | Outcome described from the requester's perspective when the actual audience is someone different | Explicitly identify both requester and audience. |
