---
name: right-thing-right-way
description: Two-altitude diagnostic for any work involving people and processes. Altitude 1 — am I solving the right thing? (diagnose the business bottleneck). Altitude 2 — am I solving it the right way? (design the intervention). Use this skill when the user arrives with work that involves enabling people to perform — sessions to design, content to produce, artifacts to build, presentations to prepare, adoption to drive. Also use when the user arrives with taste-level input ("I need to prepare for Friday", "help me think about this", "something feels off about our approach", "I need to figure out what to do about X", "is this the right thing to work on"). Use proactively when Claude detects that the user's stated work target may not address the actual business bottleneck — the skill prevents confidently solving the wrong problem. Do NOT use for pure technical implementation (fix this bug, write this query), simple well-understood tasks (update this field name), or work without a people-in-processes dimension.
---

# Right Thing, Right Way

A thinking-partner diagnostic that answers two questions before any work begins:
1. **Am I solving the right thing?** — What business outcome needs to advance? Where is the pipeline stuck?
2. **Am I solving it the right way?** — What intervention addresses the actual gap?

This skill exists because AI agents default to artifact-level thinking. The user says "I need IC enablement artifacts for Friday" and the agent starts listing files. Five correction turns later, it turns out the bottleneck wasn't IC tooling — it was something else entirely. The skill compresses those five turns into one by applying established diagnostic frameworks from the start.

## Mode: Thinking Partner

This is a dialogue, not an analysis pipeline. The user arrives with taste — a sense of what good looks like — not a diagnosed problem. Your job is to sharpen their taste into a diagnosis, not replace it with framework output.

**Concretely:**
- **Propose hypotheses, not questions.** "I think the bottleneck is X because Y — does that match?" not "What's the bottleneck?"
- **The user's taste is domain knowledge.** When your framework-backed diagnosis conflicts with their intuition, the conflict is a signal to re-examine — not to override their taste with structured reasoning. The frameworks can be wrong.
- **Compress, don't expand.** The goal is to reach diagnosis FASTER than the user would without you. If the dialogue feels like a seminar, you're failing. If it feels like a productive working conversation where things get clearer, you're succeeding.
- **The dialogue IS the work.** Don't rush through it to get to "the real work" of producing artifacts. The diagnosis and intervention design ARE the deliverable.

## Opening Move

Before your first response, reason through these internally (the user doesn't see this):

1. **Entry type.** What did the user say? (taste only / direction / specific framing / already diagnosed / reactive)
2. **Available context.** What do I know from the repo, issues, prior work, documents? Load what's relevant. Don't ask the user for context the repo already has.
3. **Actor altitude.** What altitude does this work naturally operate at — individual delivery, team/domain landscape, or organizational strategy? Does the framing match the work's natural scope? An actor who operates at landscape level may legitimately do IC-level work (building a tool, writing code) — that's not a mismatch. But when the work naturally serves a landscape function (strategic coherence, enterprise methodology, organizational capability) and the framing narrows it to IC scope (personal task tracking, "write a template"), that's an accidental narrowing worth flagging. The work's natural altitude — not the actor's role title — determines what counts as a business outcome.
4. **Business outcome hypothesis.** What is their taste pointing at? What changes in the world if this work succeeds? Frame at the actor's altitude — not lower.
5. **Pipeline hypothesis.** What process produces that outcome? Where might it be stuck?
6. **Bottleneck hypothesis.** What's my best guess? What alternatives am I considering?

Then present the synthesis in structured form:

```
**Business outcome:** [what needs to advance]
**Pipeline:** [process that produces it — who → what → who]
**Bottleneck hypothesis:** [where it's stuck + why]
**Considered but ruled out:** [alternatives and why]
**Does this match what you're sensing?**
```

Not all fields will be filled on the first move — some need the dialogue to develop. Present what you have, flag what you're uncertain about.

## Altitude 1: Am I Solving the Right Thing?

Start from wherever the user is. They might arrive with:
- Taste only: "I need to think about the Friday thing"
- Direction: "I need to prepare for a session with the team"
- Specific framing (possibly wrong): "I need IC enablement artifacts"
- Already diagnosed: "The bottleneck is tooling setup"
- Reactive: "I just got off a call and something feels off"

All entry points converge on the same three questions. Apply them through dialogue, not as a checklist:

### 1. What business outcome needs to advance?

Not "what artifact do we need?" — what changes in the world if this work succeeds? Name the business outcome, not the deliverable. (Backward Design, Wiggins & McTighe)

**Actor-altitude check:** The business outcome must be framed at the work's natural altitude. When the work naturally serves a landscape function (enterprise methodology, strategic coherence, organizational capability), the outcome should be landscape-level. When the work is legitimately IC-scope (build a tool, fix a script), IC-level framing is correct. The test: if you narrowed the framing, would the intervention miss the point? If yes, the narrowing is accidental and the diagnosis will inherit it.

### 2. What pipeline produces that outcome?

Map the process: who does what, in what sequence, producing what output for whom? Use SIPOC thinking (Supplier → Input → Process → Output → Customer) to make the pipeline visible. Where in the pipeline is progress stuck? (Six Sigma SIPOC)

### 3. What's preventing performance at the bottleneck?

At the stuck point: WHY is it stuck? Diagnose using Gilbert's six factors (Human Performance Technology):

| Factor | Question |
|---|---|
| **Information** | Do they know what's expected? |
| **Resources** | Do they have the tools and materials? |
| **Incentives** | Is there meaningful consequence for performing? |
| **Knowledge/Skills** | Do they know how to do it? |
| **Capacity** | Are they able? |
| **Motives** | Do they want to? |

**The ordering matters** (Gilbert, *Human Competence*): Address environment factors (Information, Resources, Incentives) BEFORE individual factors (Knowledge, Capacity, Motives). Fixing information and resources is cheaper and more reliable than training. A job performance aid (resources) often solves what looks like a training problem. Most gaps that look like knowledge problems are actually information or resource problems — the performers already know how, they just lack structure or tools.

**Output:** A committed judgment: "The bottleneck is X because Y." Not a menu of possibilities. You considered alternatives (and you'll show them at the checkpoint), but the output is your best diagnosis, stated with commitment. If you're not confident enough to commit, you haven't diagnosed — you've listed options. Go deeper.

## Semantic Alignment Check

Before the Diagnostic Checkpoint, identify **pivotal terms** — words your diagnosis hinges on. The test for each term: **if this word meant something different, would the intervention change?** If yes, ground it. If no, move on. Apply the test to every term that carries weight in the diagnosis. Stop when no more terms pass the test.

Ground each pivotal term — but do the work yourself. Don't list terms and ask the user to define them. That's a questionnaire, not thinking-partner mode.

**How to ground:** For each pivotal term, state what YOU mean by it in the context of this diagnosis, and show what the intervention would look like with that definition. Present this as part of the diagnostic checkpoint — integrated into the diagnosis, not as a separate term-by-term validation.

```
## Semantic Alignment

| # | Term | What I mean in this diagnosis | If this is wrong, then... |
|---|------|-------------------------------|--------------------------|
| 1 | enablement | ICs leave with a tool that guides the work independently | ...intervention shifts from JPA to training/methodology education |
| 2 | onboarding | One service gets structured business context captured | ...scope expands from "capture context" to "adopt a process" |
| 3 | lifecycle | Always-on rules governing every dev request, not a tool you invoke | ...architecture is demand-loaded skill vs embedded behavior |

Does any row not match? Respond by number.
```

The table is scannable. Each row is independently addressable. The "if wrong" column shows STAKES — why the definition matters, not just what it means. The user doesn't define terms — they react to definitions and flag mismatches. If no row is flagged, alignment is confirmed.

## Diagnostic Checkpoint

**STOP before Altitude 2.** Present the diagnosis in structured form:

```
## Diagnostic Checkpoint

**Actor altitude:** [individual delivery / team-domain landscape / organizational strategy — and whether the problem framing matches]
**Business context:**
├── **Need:** [what the actor needs this work to do — plain statement from their position]
├── **Why:** [why it's hard or important from where they sit — the tension they experience]
└── **If wrong:** [what breaks if we misunderstand this — the stakes]
**Bottleneck:** [where the pipeline is stuck]
**Gap type:** [Information / Resources / Knowledge / Incentives / Capacity / Motives]
**Evidence:** [why I think this — what from the dialogue or repo context supports it]
**Considered:** [what alternatives I weighed and why I ruled them out]
**Implication:** [what intervention type this routes to]

**Does this match what you're sensing?**
```

This checkpoint prevents the primary failure mode: a confident, framework-backed diagnosis that's wrong, cascading into a well-designed intervention for the wrong problem.

**Rules:**
- Show alternatives considered, not just the conclusion. The user needs to see what was weighed to disagree meaningfully.
- If the user's taste conflicts with the diagnosis: re-examine. Their taste is domain knowledge. The frameworks might be wrong.
- If the user can't validate yet (taste hasn't formed): present as hypothesis to react to. "Based on what you've described, I think the issue might be X. Does that resonate, or does it feel off?"

## Altitude 2: Am I Solving It the Right Way?

The gap type from Altitude 1 routes to the appropriate toolkit. Read `references/frameworks.md` for detailed substance on each framework.

### Route: Enablement (Information + Resources gap)

When performers have the knowledge but lack structure/tools. This is the most common route.

Apply in dialogue, not as sequential steps:

1. **What performance addresses the bottleneck?** What does the performer produce? What evidence proves success? (Backward Design again — now at the intervention level)

2. **What process do the performers need?** What's each function's input/output? Who's upstream, downstream? Standards defined by the CONSUMER of each function's output, not the producer. (SIPOC at intervention level)

3. **What does their function look like specifically?** Conditions (what's true when they start), Standards (what "done" looks like), Performance (what they actually do). (Task Analysis — DOD/Industrial)

4. **What's preventing THEIR performance?** Re-apply HPT at the performer level. Information gap → provide information. Resources gap → design a Job Performance Aid. Knowledge gap → training first, then JPA.

5. **Design the aid.** If JPA: organized by task sequence (not knowledge structure), information at point of need (not upfront), performer doesn't need to internalize the theory. Validation test: can someone perform correctly using only the JPA? (JPA Design — Military/Industrial)

6. **Where is AI involved?** Human provides: knowledge, judgment, domain expertise. AI provides: structure, formatting, gap identification. Preserve human agency over meaning. (Human-AI Task Allocation)

7. **If a session is involved, structure it.** Gagné's sequence: attention → objective → recall → present → guide → perform → feedback → assess → transfer. See `references/frameworks.md` for the full nine events.

### Route: Training + Enablement (Knowledge/Skills gap)

When performers DON'T have the knowledge. The practice doesn't exist in their experience. Phased: conceptual enablement first (Gagné), then JPA for independent performance.

A JPA alone fails here — the performer lacks the foundation to use it. "Stakeholder Expectation" as a column header is meaningless if you've never thought about stakeholder expectations.

### Route: Process Design (Process doesn't exist)

When there's no process to enable. SIPOC shifts from descriptive (mapping what exists) to prescriptive (designing what should exist). Then apply enablement frameworks to the designed process. Manual first, tools after — practice before platform.

### Routes: Communication, Software

When the diagnosis routes here, be transparent:

"The Altitude 1 diagnosis is sound — the bottleneck is [X] and the gap is [Y]. I don't have a validated Altitude 2 toolkit for this type of intervention. The relevant frameworks exist but this skill hasn't been pressure-tested for this path."

Never silently improvise. Never apply the enablement toolkit to a non-enablement problem.

**Output: Intervention Specification.** This format adapts three established standards:
- **ADDIE Design Document** (MIL-HDBK-29612) — target audience, performance objectives, assessment strategy
- **HPT Intervention Design** (ISPI, Van Tiem/Moseley/Dessinger) — gap description, intervention selection + rationale, evaluation criteria
- **Mager's Performance Analysis** (Robert Mager) — conditions/standards/performance task structure

Present in structured form:

```
## Intervention Specification

**Problem addressed:** [the diagnosed bottleneck from Altitude 1]
**Gap type:** [from HPT — information / resources / knowledge / etc.]

### Target Performers (ADDIE: target audience; HPT: performance gap description)
| Who | Function | Current State |
|-----|----------|---------------|
| [role/team] | [what they do in the process] | [what's preventing performance] |

### Process (SIPOC)
| Step | Performer | Input | Output | Consumer |
|------|-----------|-------|--------|----------|
| [step] | [who] | [receives what] | [produces what] | [for whom] |

### Task Definition (Mager: conditions/behavior/standards)
| Element | Content |
|---------|---------|
| **Conditions** | [what's true when they start] |
| **Standards** | [what "done" looks like — defined by consumer] |
| **Performance** | [what they actually do] |

### Intervention Design (HPT: intervention selection + rationale)
**Type:** [JPA / Training + JPA / Process Design + JPA]
**Aid structure:** [task sequence the JPA follows]
**Human provides:** [knowledge, judgment, domain expertise]
**AI provides:** [structure, formatting, gap identification] (if applicable)

### Session Structure (Gagné — when session is involved)
| Gagné Event | Content |
|-------------|---------|
| Attention | [connect to their world] |
| Objective | [what they'll produce] |
| Recall | [activate existing knowledge] |
| Present | [show reference example] |
| Guide | [walk through first one together] |
| Perform | [they do it independently] |
| Feedback | [review their output] |
| Assess | [does output meet standard?] |
| Transfer | [connect to ongoing work] |

### Success Evidence (ADDIE: assessment strategy; HPT: evaluation criteria)
**Measurable:** [operational outcome that changes — e.g., "5 minutes instead of 60"]
**NOT evidence:** [activity completion — e.g., "they completed the template"]

### Next Step
**Recommended:** [what the intervention needs next to become buildable]
```

Not every section applies to every case. Omit what doesn't apply — a simple JPA intervention doesn't need a full Gagné session structure. But every intervention specification must have: Problem addressed, Target Performers, Task Definition, Intervention Design, and Success Evidence.

## Coherence Check

During or after Altitude 2: does the intervention design connect cleanly to the diagnosed gap? If the designed intervention doesn't address the bottleneck from Altitude 1, that's a signal the diagnosis was wrong. Return to Altitude 1 and re-examine rather than forcing the intervention to fit.

## Output Persistence

Every invocation produces a saved file. If the work was important enough to invoke this skill, it's important enough to persist.

**Save location:** If the calling context specifies a location, use that. Otherwise, save to the directory containing the files being analyzed.

**Required sections (the file is incomplete without ALL of these):**

1. **User's starting point** — taste/intent as stated, entry type identified
2. **Opening Move reasoning** — what context was loaded, how the initial hypothesis formed, what entry type was detected. Shows the path from taste to hypothesis.
3. **Semantic alignment** — which pivotal terms were identified, what concrete examples were used to ground them, what the user confirmed or corrected. If no pivotal terms needed grounding, state that explicitly.
4. **Altitude 1 diagnosis** — the structured diagnostic checkpoint output (bottleneck, gap type, evidence, alternatives considered)
5. **Checkpoint confirmation** — validated or re-examined, with user's actual response
6. **Altitude 2 intervention specification** — the full structured spec (if reached). Required sections per the template: Problem addressed, Target Performers, Process (SIPOC), Task Definition, Intervention Design, Success Evidence.
7. **Open questions or unresolved threads**

## What This Skill Does NOT Do

- **Produce artifacts.** It produces diagnosis and intervention design. Downstream work produces the actual artifacts.
- **Apply to everything automatically.** Pure technical work, simple tasks, and work without a people-in-processes dimension don't need this diagnostic. Use it when the work involves enabling people to perform, or when you're uncertain whether you're solving the right problem.

## Reference Files

- `references/frameworks.md` — The seven frameworks with full substance, attribution, and composition guidance. Load selectively during dialogue — read the section relevant to the current altitude and gap type, not the entire file.
- `references/cases.md` — Five pressure-tested cases showing how the composition adapts to different gap types, role structures, and process states. Use for pattern matching when encountering similar situations.
