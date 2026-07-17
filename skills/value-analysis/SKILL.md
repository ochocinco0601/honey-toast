---
name: value-analysis
description: Structured value analysis using established strategy and operations management frameworks. Walks an 8-step analytical flow in 3 phases (Understand/Intervene/Validate) with output contracts enforcing step gating. Use when the user needs to reason about value at any organizational altitude — business strategy, technology positioning, team delivery, individual contribution, AI investment, competitive response, or prioritization. Triggers on "analyze the value of", "where should we focus", "is this worth doing", "what's the value", "how do I position this", "value analysis", "where's the constraint", or when the user needs structured reasoning about where to invest effort for maximum impact.
---

# Value Analysis

Structured value analysis in 3 phases, 8 steps. Do NOT use for simple cost/benefit calculations or questions without organizational altitude or constraint identification.

## Core Synthesis

Two modes of creating value:

**Optimization** (Run/Grow): Improvement at the constraint, weighted by the base it operates on, at the altitude that matters to the strategy. Goldratt's Theory of Constraints governs.

**Transformation** (Transform): Creating a new system where the old constraint is irrelevant. Christensen's Innovator's Dilemma governs.

**Decision test (step 5):** Has the human's ROLE changed, not just the tool? Same role + faster tool = optimization. Different role = transformation.

## Execution: Three Phases, Eight Steps

**In conversation, hold three phases. In execution, follow eight steps.**

| Phase | Steps | Core Question |
|-------|-------|---------------|
| **Understand** | 1-4 | What is the system and where's the bottleneck? |
| **Intervene** | 5-7 | What to change, what type, what time horizon? |
| **Validate** | 8 | Does it compose into a strategy? |

### Entry Point

**Altitude is per-analysis, not per-person.** Determine which altitude the user is analyzing:

- **Top-down** (altitude 1-2): Start at step 1. "What does the customer need?"
- **Bottom-up** (altitude 3-4): Start THINKING from the user's work, then fill steps 1-3 to satisfy contracts before proceeding past the step 4 gate. All contracts must be satisfied regardless of entry direction.

### Output Contract Convention

Each step has a required output contract. The next step requires the prior step's contract as input. If a required field is empty, the step is incomplete and downstream steps cannot proceed without explicitly acknowledging the gap.

---

## Phase 1: Understand

### Step 1: Identify the Customer Job

**Question:** What job is the customer hiring this entity to do?
**Prior art:** Jobs to Be Done (Christensen, 2003)
**Trap:** Defining the job in terms of your current product instead of the customer's actual need.

"Customer" is whoever consumes the output at the analysis altitude. At altitude 1, end customer. At altitude 3, business stakeholder. At altitude 4, whoever depends on the work.

**Output contract:**
```
Altitude:          [1-4]
Customer:          [who consumes the output — name the entity, not your role]
Job (functional):  [what they need done]
Job (emotional):   [how they want to feel]
Job (social):      [what it means for their identity/status]
```

### Step 2: Map Value Chain Activities

**Question:** What activities are performed to do this job?
**Input requires:** Step 1 contract
**Prior art:** Porter's Value Chain (1985)
**Trap:** Mapping org chart instead of value flow. Activities are not departments.

**Output contract:**
```
Primary activities:    [numbered list — directly create value]
Support activities:    [numbered list — enable primary activities]
Flow:                  [which activities feed which — the chain]
```

### Step 3: Assess Evolution

**Question:** Which activities are commodity, which are custom, which are novel?
**Input requires:** Step 2 contract
**Prior art:** Wardley Mapping (Wardley, 2005)
**Trap:** Treating custom-built as inherently valuable. Some are custom because nobody invested in commoditizing them — waste, not differentiation.

**Output contract:**
```
Per activity from step 2:
  Activity:     [number + name from step 2]
  Evolution:    [genesis | custom | product | commodity]
  Rationale:    [why this classification]
```

### Step 4: Identify the Constraint

**Question:** Which activity constrains the throughput of the entire system?
**Input requires:** Step 2 + Step 3 contracts
**Prior art:** Theory of Constraints (Goldratt, 1984); Amdahl's Law (1967)
**Trap:** Assuming every improvement matters equally. Any improvement NOT at the constraint is illusion of improvement. 1% of $100M > 100% of $100K.

**Output contract:**
```
Status:              [IDENTIFIED | UNIDENTIFIED]
Constraint:          [specific activity number from step 2, or "unknown"]
Constraint type:     [resource | policy | knowledge | capability | unknown]
Evidence:            [how you know this is the constraint]
If UNIDENTIFIED:     [what instrumentation or data is needed to identify it]
```

**GATE:** Step 5 requires `Status: IDENTIFIED`. If `UNIDENTIFIED`:
1. Ask the user — they may have the domain knowledge to identify it
2. If still unidentified: mark all downstream output as `UNDIRECTED` (acknowledged noise)
3. There is no third option — proceeding without a constraint while believing interventions are targeted is self-deception

**Goldratt's Five Focusing Steps operate here:**
1. Identify the constraint
2. Exploit it — understand WHY (the `Constraint type` field), get everything possible without new investment
3. Subordinate everything else
4. Elevate — invest to expand the bottleneck
5. Repeat — the constraint moves

---

## Phase 2: Intervene

### Step 5: Identify Intervention Points

**Question:** Where could a change alter the economics or capability of the system?
**Input requires:** Step 3 contract (evolution per activity) + Step 4 contract (IDENTIFIED + constraint + type)
**Prior art:** Meadows' Leverage Points (1999)
**Trap:** Generating interventions without steps 1-4 = brainstorming noise.

**Output contract:**
```
Mode:                [optimization | transformation]
Decision test:       [has the human's ROLE changed? — evidence]
Directed:            [DIRECTED | UNDIRECTED — from step 4 status]
Interventions:
  Per intervention:
    #:               [number]
    Activity:        [step 2 activity number it targets]
    Evolution:       [step 3 evolution of that activity]
    Description:     [what the intervention does]
    Leverage level:  [parameter | feedback | structure | paradigm]
```

**Optimization/transformation fork:**
- **Optimize:** Improve the constraint within the existing system. Goldratt governs. Continue to steps 6-8.
- **Transform:** Replace the system so the constraint is irrelevant. Christensen governs. The old steps 1-4 describe what you're replacing — run a NEW pass through steps 1-4 for the replacement system.

**Transformation recursion contract:** When mode is `transformation`, append:
```
New system S1 contract:  [customer job for the replacement system]
New system S2 contract:  [activities in the replacement system]
New system S3 contract:  [evolution of new activities]
New system S4 contract:  [constraint in the new system]
```
Steps 6-8 evaluate using the new system's contracts.

### Step 6: Classify the Change Type

**Question:** What type of value does each intervention create?
**Input requires:** Step 5 contract
**Prior art:** TBM Run/Grow/Transform (TBM Council, ~2012)
**Trap:** Defaulting to "Run" because it's measurable. Cost savings are quantifiable; transformation is not — but transformation is where the highest value lives.

**S5 Mode vs S6 Change Type:** S5's `Mode` (optimization/transformation) describes whether the SYSTEM changes. S6's `Change Type` (Run/Grow/Transform) describes what TYPE OF VALUE each INDIVIDUAL intervention creates. Different dimensions.

**Output contract:**
```
Per intervention from step 5:
  Intervention #:  [from step 5]
  Change type:     [Run | Grow | Transform]
  Rationale:       [why this classification]
```

### Step 7: Assess Time Horizon

**Question:** When would this intervention produce value, and for whom?
**Input requires:** Step 5 + Step 6 contracts
**Prior art:** Three Horizons (McKinsey, 1999)
**Trap:** Filling the portfolio with H1. A portfolio of only H1 optimizes the present at the expense of the future.

**Specify the actor.** Horizon is relative to a specific organization or person. Same intervention can be H1 for an early adopter and H3 for an industry.

**Output contract:**
```
Actor:             [relative to whom]
Per intervention from step 5:
  Intervention #:  [from step 5]
  Horizon:         [H1 | H2 | H3]
  Rationale:       [why this horizon, for this actor]
```

---

## Phase 3: Validate

### Step 8: Test Strategic Coherence

**Question:** Do the proposed interventions reinforce each other? Do they compose into a strategy or is this just a list?
**Input requires:** Steps 5-7 contracts
**Prior art:** Good Strategy Bad Strategy (Rumelt, 2011)
**Trap:** Treating a list of good ideas as a strategy. Strategy requires choosing — deciding what NOT to do.

**Output contract:**
```
Diagnosis:          [one sentence — what is the challenge]
Guiding policy:     [one sentence — the approach to the challenge]
Coherent actions:   [numbered list — pruned to those that reinforce each other]
Explicitly NOT:     [what was considered and rejected]
Coherence test:     [does each action reinforce at least one other? evidence]
Verdict:            [COHERENT | INCOHERENT]
```

**Feedback loop:** If `Verdict: INCOHERENT`:
1. The `Explicitly NOT` list identifies which interventions broke coherence
2. Prune or replace those interventions in step 5
3. Re-run steps 6-7 on revised set
4. Re-evaluate step 8
5. **Termination:** If two iterations produce INCOHERENT, the issue is likely in Phase 1 (wrong constraint, wrong customer, or wrong activity map). Return to step 1.

---

## Output Persistence

Save the analysis to file after completion or at any halt point (including step 4 UNIDENTIFIED). Save to the location specified by the calling context. If none specified, save to the directory containing the files being analyzed.

### File Structure (Two Layers)

The persisted file has two layers — the product (what the user reads) and the system (what future sessions parse):

**Layer 1 — Summary (top of file).** The user-facing analysis. Must be readable and actionable without reading Layer 2. Required fields:

```markdown
# Value Analysis: [Topic]

**Date:** YYYY-MM-DD
**Altitude:** [1-4]
**Mode:** [Optimization | Transformation]
**Directed:** [Yes | No (UNDIRECTED — constraint not identified)]

---

## Summary

**Diagnosis:** [one sentence — the challenge]

**Guiding policy:** [one sentence — the approach]

**Do this:**
1. [retained intervention] — [why, one phrase]
2. ...

**Not this (subordinated):**
- [rejected intervention] — [why rejected, one phrase]

**Patterns detected:**
- ⚠️ [pattern name] — [what was observed]

**Verdict:** [COHERENT | INCOHERENT] — [one sentence evidence]
```

**Layer 2 — Analysis Detail (below summary).** The full output contracts for every completed step. A future session reads this to understand the reasoning, resume partial analysis, or challenge specific steps.

## Prior Art Quick Reference

| # | Framework | Author | Year | Step |
|---|-----------|--------|------|------|
| 1 | Value Chain | Porter | 1985 | 2 |
| 2 | Jobs to Be Done | Christensen | 2003 | 1 |
| 3 | Theory of Constraints | Goldratt | 1984 | 4 |
| 4 | Amdahl's Law | Amdahl | 1967 | 4 |
| 5 | Leverage Points | Meadows | 1999 | 5 |
| 6 | Wardley Mapping | Wardley | 2005 | 3 |
| 7 | Run/Grow/Transform | TBM Council | ~2012 | 6 |
| 8 | Three Horizons | McKinsey | 1999 | 7 |
| 9 | Good Strategy Bad Strategy | Rumelt | 2011 | 8 |
| 10 | Innovator's Dilemma | Christensen | 1997 | 5 (fork) |
| 11 | Balanced Scorecard | Kaplan & Norton | 1992 | Multi-dimensional measurement |
| 12 | Lean Value Streams | Womack & Jones | 1996 | 2 (alternative) |
| 13 | ITIL 4 Value Co-creation | Axelos | 2019 | 1 (altitude 4) |
| 14 | Value Proposition Canvas | Osterwalder | 2014 | 1 (depth tool) |
| 15 | Real Options Theory | Financial economics | — | 7 (depth tool) |
| 16 | Competitive Strategy | Porter | 1980 | Context |
| 17 | Absorptive Capacity | Cohen & Levinthal | 1990 | Contextual |
| 18 | Diffusion of Innovations | Rogers | 1962 | Contextual |

## Altitude Reference

| # | Altitude | Question | Trap |
|---|----------|----------|------|
| 1 | Business | How does this create value for customers? | Assuming current value chain is permanent |
| 2 | Technology / Support Org | How does this amplify business value? | Defaulting to "Run" |
| 3 | Delivery Team | How does output connect to value chain? | Measuring velocity instead of impact |
| 4 | Individual | How does this work preserve or create value? | Invisible value — prevention has no metric |
