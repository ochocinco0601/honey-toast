---
name: systems-analysis
description: Produces structured systems analysis with data flows, failure modes, leverage points, and workflow critique. Also produces architecture documentation for existing systems using C4 zoom levels (Brown) and arc42 design decisions (Starke). Triggers on "analyze this system", "map the components", "what are the dependencies", "show me how this connects", "review this workflow", "critique this process", "explain this system", "document this architecture", "how does this system work", or when Claude detects multi-component work, workflow/process design, or a need to explain an existing system's architecture to a reader.
---

# Systems Analysis — Structured Systems Thinking + Architecture Documentation

Produce a complete systems analysis for multi-component work. Two use cases, same analytical methodology:

- **Pre-build (Design phase):** Analyze a system to inform design decisions before building or changing it.
- **Post-build (Explanation):** Analyze an existing system to document how it works, why it's designed that way, and what its limitations are.

The analytical work is the same — map components, trace flows, identify failure modes, explain rationale. The input differs (requirements vs existing code). The output structure is the same.

When workflows or processes are involved, include expert-level design critique.

## Output Persistence

Save analysis to file for future reference. If a save location is specified by the calling context (e.g., an onboarding workflow), use that. Otherwise, save to the directory containing the files being analyzed.

---

## Output Structure — C4 Architecture + Systems Thinking

The output combines two established frameworks:

- **C4 Model** (Simon Brown) — zoom levels for communicating architecture. Each level tells a complete story at that depth.
- **Systems Thinking** (Meadows) — analytical methods for understanding behavior: failure modes, feedback loops, leverage points.
- **arc42** (Starke/Hruschka) — reasoning sections: design decisions, constraints, risks.

C4 provides the structure. Systems thinking provides the analytical content. arc42 provides the reasoning.

### Selecting Zoom Depth

Not every analysis needs all four C4 levels. Select based on what the reader needs:

| Reader need | Zoom levels | When |
|---|---|---|
| Understand what this system is | Context only | Quick orientation, stakeholder briefing |
| Understand the major building blocks | Context + Container | Most pre-build and post-build analyses |
| Understand internal structure | Context + Container + Component | Complex systems, file-level documentation |
| Understand implementation detail | All four levels | Rarely — only for complex single components |

## Output Format (Required)

Every systems analysis MUST produce this structured output:

```markdown
## Systems Analysis: [Topic]

### 1. Context (C4 Level 1)

What this system is, where it fits, and why it exists.

- **What it does:** [one sentence — the system as a black box]
- **Who/what uses it:** [actors, consuming systems]
- **What it interacts with:** [external systems, platform mechanisms]
- **Why it exists:** [the problem it solves]
- **Boundary:** [what's in scope vs out of scope]

### 2. Containers (C4 Level 2)

The high-level building blocks inside the system boundary.

| Container | Responsibility | Interacts with |
|-----------|---------------|----------------|
| [name] | [what it does — one line] | [which other containers] |

### 3. Components (C4 Level 3) — include when zoom depth requires it

Internal parts of each container. Files, modules, scripts, configuration.

| Component | File/location | Role | State? |
|-----------|--------------|------|--------|
| [name] | [path] | [what it does] | [holds state / stateless] |

### 4. Data Flow
[Source] --writes--> [Stock/State] --reads--> [Consumer]

**Key flows:**
- [A] writes → [B] reads → [C] consumes
- ...

### 5. Failure Modes
| If This Fails | Consequence | Fallback |
|---------------|-------------|----------|
| [component/flow] | [what breaks] | [graceful degradation] |

### 6. Feedback Loops
- **Reinforcing:** [loops that amplify]
- **Balancing:** [loops that stabilize]
- **Delays:** [where effects are delayed]

### 7. Leverage Points
| Level | Intervention | Impact |
|-------|-------------|--------|
| Current | [what we're considering] | [parameter/flow/rule/paradigm] |
| Higher | [alternative if available] | [why higher leverage] |

### 8. Design Decisions (arc42)

Architecturally significant decisions with context and rationale.

| Decision | Alternatives considered | Rationale |
|----------|----------------------|-----------|
| [what was decided] | [what else was possible] | [why this choice] |

### 9. Constraints (arc42)

What the system cannot change — platform limits, organizational rules, technical boundaries.

- [constraint] — [consequence for the architecture]

### 10. Risks and Limitations (arc42)

Known gaps and their consequences. Not hidden — stated upfront.

- [risk/limitation] — [what could go wrong / what doesn't work]

### 11. Boundary Assumptions
- [Assumption about external factor] ← [risk if violated]

### 12. Recommendation (pre-build) / Summary (post-build)

**Pre-build:**
- **Proposed change:** [specific modification]
- **Affects:** [components, connections]
- **Expected behavior change:** [what should happen differently]
- **Watch for:** [emergence to observe]

**Post-build:**
- **Current state:** [working / partially working / known gaps]
- **Next actions:** [what needs attention]

### 9. Workflow/Process Critique
| Evaluation Criterion | Assessment |
|---------------------|------------|
| **Stakeholders & Expectations** | Who does this workflow serve? What does each stakeholder expect? Are expectations aligned or in tension? |
| **Goal-Process Alignment** | Does this process achieve its stated goal? [yes/no/partially - reasoning] |
| **Step Necessity** | Are all steps necessary? [list any redundant/unnecessary steps] |
| **Step Sufficiency** | Are any steps missing? [list gaps between current and goal state] |
| **Sequence Optimality** | Are steps in optimal order? [reordering recommendations if any] |
| **Actor Appropriateness** | Is this process appropriate for who executes it? [cognitive load, skill match, tool availability] |
| **Failure Recovery** | When steps fail, is recovery possible? [graceful degradation or catastrophic?] |
| **Expert Redesign** | What would an expert change? [alternative approach if current is sub-optimal] |

**Workflow Verdict:** [WELL-DESIGNED / NEEDS REFINEMENT / FUNDAMENTALLY FLAWED]
**Primary Issue (if any):** [single biggest problem to address first]

### 10. Diagrams (for human validation)

Generate Mermaid diagrams so the user can visually validate Claude's understanding. Without visual representation, the user cannot efficiently check if the analysis is correct.

**Select diagram types based on analysis focus:**

| Analysis Focus | Diagram Type | When to Include |
|---------------|--------------|-----------------|
| Components & relationships | `flowchart` | 4+ components |
| Data flows | `flowchart LR/TD` | Non-trivial data paths |
| Feedback loops | `flowchart` with cycle arrows | Any feedback loops identified |
| Workflow/process | `sequenceDiagram` | Section 9 applies |
| State transitions | `stateDiagram-v2` | Stateful components |

**Requirements:**
- At least one diagram per analysis (typically data flow or component map)
- Diagrams must be viewable in GitHub or VS Code preview
- Label nodes clearly - the user validates by checking if relationships match their understanding

For Mermaid diagram examples (data flow, feedback loop, workflow), see `references/examples.md`.

---

## Execution Steps

### Step 1: Identify the System

Determine scope from user input or conversation context.

**Analytical stance:** A system's behavior emerges from relationships between components, not from any single component. If you analyze each part in isolation and then combine the findings, you will miss the behavior that arises from their interaction. Map the whole system before diagnosing any part.

### Step 2: Map Components

Read relevant files. Classify each component: holds state (stock) or stateless (flow). Map dependencies.

**Why stocks matter:** Most system problems originate where state accumulates — stale data, missing writes, unbounded growth, race conditions. Stateless components transform; stateful components *remember*, and memory is where things go wrong. Pay disproportionate attention to stocks.

### Step 3: Trace Data Flows

For each component:
1. What writes to it?
2. What reads from it?
3. What happens if the write doesn't happen?
4. What happens if the read gets stale data?

### Step 4: Identify Failure Modes

For each critical flow:
- Silent failure (fails without signal)
- Loud failure (fails with error)
- Partial failure (half works)
- Cascade failure (spreads downstream)

### Step 5: Find Feedback Loops

System behavior comes from feedback loops, not one-way chains. If you haven't found the loops, you haven't understood the system.

Ask:
- Does any output eventually affect its own input?
- Is anything growing or shrinking over time? (reinforcing loop — amplifies change)
- Is anything stable despite pressure to change? (balancing loop — resists change)
- Where are the delays between cause and effect?

**Why delays matter:** Feedback loops don't respond instantly. A change you make today may not show effects for days or weeks. The trap: impatience causes over-intervention — you add a second change before the first has played out, and now you can't tell which caused what. After intervening, wait long enough to observe the effect before intervening again.

### Step 6: Assess Leverage Points

Rate the proposed intervention (Meadows' hierarchy, low → high):
- Parameters (numbers, settings) = Very Low
- Flows (rates, scanning) = Low
- Stocks (buffers, caches) = Medium
- Feedback loops = High
- Information flows = High
- Rules/constraints = Very High
- Goals = Very High
- Paradigm/mental model = Highest

**The counter-intuitive truth:** Most interventions target low-leverage points because they're obvious and comfortable — "change the timeout," "add more logging." High-leverage interventions challenge rules or mental models, which is uncomfortable: "change what we're optimizing for," "change who makes this decision," "change the fundamental assumption." The analysis should name the highest-leverage option available, even if it's harder to act on.

**Ask:** Is there a higher-leverage point we're avoiding because it's uncomfortable?

### Step 7: Check Boundary Assumptions

What does the system assume about things OUTSIDE its control?
- External services
- User behavior
- Model behavior
- Time/availability

**Which assumptions are fragile?**

### Step 8: Evaluate Workflow Design

Every system has actors who use it through some process. Identify who interacts with this system and evaluate the workflow they follow — whether that workflow is explicitly designed or emergent from the system's structure.

**Evaluation questions:**

1. **Who are the stakeholders?**
   - Who executes this workflow? (the actor)
   - Who consumes the output? (the beneficiary)
   - Who has oversight/approval authority? (governance)
   - Who is affected by the workflow's existence? (impacted parties)
   - What does each stakeholder expect from this workflow?
   - Are expectations aligned or in conflict?

2. **What is the stated goal of this workflow?**
   - If unstated, ask user to clarify before evaluating
   - A workflow without a clear goal cannot be evaluated
   - If stakeholders have conflicting goals, surface the tension

3. **Does the process actually achieve that goal?**
   - Trace from start to finish: does completing all steps produce the goal?
   - Identify gaps where the goal requires something the process doesn't provide

4. **Are all steps necessary?**
   - For each step: "If we removed this, would the goal still be achieved?"
   - Watch for: legacy steps, defensive steps that guard against solved problems, ceremonial steps

5. **Are steps in optimal sequence?**
   - Dependencies: Does step N actually require step N-1's output?
   - Parallelization: Could steps run concurrently?
   - Early exit: Are failure conditions checked early enough?

6. **Is the process appropriate for its actor?**
   - Cognitive load: Too many decisions? Too much to remember?
   - Skill match: Does the actor have required expertise?
   - Tool availability: Does actor have access to required tools/information?

7. **What would an expert redesign?**
   - If you were designing this from scratch, what would differ?
   - Are there established patterns for this type of workflow?
   - What's the simplest process that achieves the goal?
   - How would you resolve stakeholder tensions if present?

**If workflow is sub-optimal:** State the verdict clearly. Don't just document problems - recommend the better approach.

### Step 9: Generate Diagrams

Create Mermaid diagrams to enable user validation:

1. **Identify what needs visual representation:**
   - Which relationships are complex enough that text alone is hard to validate?
   - Are there feedback loops? (Always diagram these)
   - Is there a workflow? (Sequence diagram)

2. **Select appropriate diagram type(s)** from the table in Section 10

3. **Generate diagrams with clear labels:**
   - Node names should match component names from Section 2
   - Edge labels should indicate relationship type (writes, reads, triggers, etc.)
   - Keep diagrams focused - split into multiple if too complex

4. **Self-check:** Could the user look at this diagram and say "yes, that matches my understanding" or "no, you missed X"?

### Step 10: Produce Output

Generate the structured analysis in the required format.
- Include all sections (1-12) for systems analysis
- Include Section 9 (Workflow/Process Critique) — every system has actors and processes
- Include Section 10 (Diagrams) - at least one diagram per analysis

**Persistence:** Save to the location specified by the calling context. If none specified, save to the directory containing the files being analyzed.

---

## Reference Material

**Architecture documentation prior art:**
- C4 Model — Simon Brown, *Software Architecture for Developers* (c4model.com). Zoom-level structure for communicating architecture.
- arc42 — Starke/Hruschka (arc42.org). Design decisions, constraints, risks sections.
- Application: C4 provides zoom-level structure, systems thinking provides analytical content, arc42 provides reasoning.

**Systems thinking prior art:**
- Donella Meadows, *Thinking in Systems: A Primer*. 7 principles: see the whole, map stocks/flows, identify feedback loops, find leverage points, expect emergence, honor boundaries, design for failure.
- Peter Senge, *The Fifth Discipline*. Feedback loops and mental models in organizational systems.

---

## Red Flags (Stop and Reconsider)

**Systems Analysis:**
- ❌ Proposing changes before completing analysis
- ❌ Analyzing only one component in isolation
- ❌ Missing failure modes section
- ❌ No leverage point assessment
- ❌ Assuming outside-boundary factors are reliable
- ❌ Skipping feedback loop identification
- ❌ "I understand the system" without showing the map

**Workflow Critique:**
- ❌ Accepting a workflow at face value without questioning goal alignment
- ❌ Documenting a sub-optimal workflow without stating it's sub-optimal
- ❌ Identifying problems without recommending alternatives
- ❌ Evaluating a workflow without knowing its stated goal
- ❌ Assuming all existing steps are necessary
- ❌ Optimizing a workflow that shouldn't exist (wrong solution to problem)
- ❌ Ignoring the actor's capabilities when evaluating process design
- ❌ Assuming a single stakeholder when multiple exist with different expectations
- ❌ Ignoring stakeholder tensions instead of surfacing them

**Diagrams:**
- ❌ Producing text-only analysis without diagrams (user cannot validate efficiently)
- ❌ Diagrams that don't match the component names in the text
- ❌ Overly complex diagrams that obscure rather than clarify
- ❌ Missing diagram for feedback loops (these are hard to validate from text alone)

---

## Examples

For complete worked examples (minimal analysis + workflow critique), see `references/examples.md`.
