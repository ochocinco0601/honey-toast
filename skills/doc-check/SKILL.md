---
name: doc-check
description: Evaluate documentation against the Diataxis 4-type framework (tutorial, how-to, reference, explanation). Use when creating, reviewing, or structuring documentation for any audience. Triggers on "doc check", "is this the right doc type", "review this guide structure", "am I mixing doc types", or when building guides, references, practitioner content, presentations, or toolkits. Also use proactively when documentation may be mixing types.
---

# Doc Check - Diataxis Documentation Type Framework

## How This Skill Works

**Two modes:**

1. **During creation (primary):** Apply this framework when producing documentation. Classify the doc type first, then follow that type's rules. When making structural choices (e.g., separating explanation from a how-to guide), proactively explain the reasoning to the user with reader-impact rationale.

2. **On review (`/doc-check`):** Evaluate existing content against the framework. Produce findings with reader-impact rationale so the user can evaluate whether each finding is legitimate for their audience.

**Rationale is mandatory in both modes.** Never cite framework rules as justification — always explain in terms of what happens to the reader:

- **Not this:** "Separated the theory into a background section because how-to guides exclude explanation."
- **This:** "Moved the context into a linked background section. A practitioner following these steps will either skip it (wasted space) or get pulled out of task flow. Those who want the context can follow the link; practitioners stay in flow."

---

## The Framework

Golden rule: **never mix documentation types in the same document.** Type mixing is the #1 documentation failure.

|  | **Learning (Acquisition)** | **Working (Application)** |
|---|---|---|
| **Practical (Action)** | Tutorial | How-to Guide |
| **Theoretical (Cognition)** | Explanation | Reference |

Classify with two questions:
1. **Doing or understanding?** (practical vs theoretical)
2. **Learning or working?** (acquisition vs application)

---

## The Four Types

### Tutorial
Learning-oriented lesson — guided, hands-on experience.

- Teach by doing, not telling. Every step produces a visible result.
- Start simple, build complexity. Use beginner-friendly approaches.
- Minimal explanation — only what's needed to complete the step.
- **Exclude:** Theory, alternatives, options, digressions, reference material.
- **Test:** Can a beginner follow this cold and succeed?
- **Examples:** Onboarding walkthrough, "register your first service" guided exercise, getting-started guide.

### How-to Guide
Goal-oriented directions — solve a specific problem.

- Assume competence. Reader knows what they want to achieve.
- Address real-world problems, not tool functionality.
- Action and only action. Title: "How to [X]."
- Use conditional imperatives: "If you want X, do Y."
- **Exclude:** Teaching, theory, extended explanation. Link instead.
- **Test:** Can a competent practitioner solve their specific problem?
- **Examples:** Runbooks, playbooks, persona-specific guides, operational procedures.

### Reference
Information-oriented — technical description of the machinery.

- Austere, authoritative, no ambiguity.
- Describe what things ARE, not how to use them.
- Structure mirrors the thing described, not the user's journey.
- Consistent format — same pattern for every entry. Consulted, not read linearly.
- **Exclude:** Instructions, how-to steps, explanations of WHY, opinions.
- **Test:** Can an expert find the specific fact they need in under 30 seconds?
- **Examples:** Data model reference, schema docs, API reference, field definitions, configuration reference.

### Explanation
Understanding-oriented — context, rationale, and perspective.

- Provide the WHY — design decisions, history, constraints, alternatives.
- Take a wider perspective than any single task. Make connections across topics.
- Admit opinion and perspective — judgment is appropriate here.
- **Exclude:** Instructions, procedures, technical reference details.
- **Test:** Does someone understand the reasoning after reading, without touching the product?
- **Examples:** Architecture decision records, design rationale, strategic framing, principles documents.

---

## During Creation: Apply the Framework

When producing documentation:

1. **Classify first.** Before writing, determine: what type is this? Use the audience and purpose to decide.
2. **Follow the type's rules.** Consult the rules above for the identified type.
3. **When tempted to mix types** — stop. Extract the other-type content into a separate artifact and link to it. Explain to the user why you're separating it, in reader-impact terms.
4. **Surface the classification.** When presenting documentation to the user, briefly state the type and why: "I've structured this as a how-to guide — the practitioner knows what they want to accomplish, so I've kept it to actions and linked the background context separately."

---

## On Review: Evaluation Workflow

When invoked with `/doc-check`:

### Step 1: Classify
- **What type IS this trying to be?** (author's apparent intent)
- **What type SHOULD this be?** (based on audience and purpose)
- **Are types mixed?**

### Step 2: Check Type-Specific Rules
For each finding, state:
1. **What** — the specific content and location
2. **Reader impact** — what the reader experiences because of this
3. **Recommendation** — concrete action

### Step 3: Identify and Separate Mixed Content

| Found Type | Mixed Into | Separation |
|-----------|-----------|------------|
| Explanation in how-to | Extract to linked doc or clearly separated "background" section |
| How-to steps in explanation | Extract to companion how-to guide, link from explanation |
| Reference in how-to | Extract to reference doc, link: "See [X] for complete list" |
| Tutorial tone in how-to | Tighten — assume competence, drop teaching scaffolding |

### Step 4: Deliver

```
## Doc Check: [Document Name]

**Classified as:** [type]
**Audience:** [who this serves]
**Verdict:** [Clean / Minor mixing / Significant mixing / Wrong type]

### What Works
[What this doc does well for its reader]

### Findings
For each finding:
- **[Location]:** [What the content is]
- **Reader impact:** [What happens to the reader — why it matters]
- **Recommendation:** [What to do]

### Summary
[Pattern-level observation — systemic issue or isolated instances?]
```

---

## Common Type-Mixing Traps

Recurring patterns across documentation projects:

| Content | Type | Trap |
|---------|------|------|
| **Practitioner guides** | How-to | Embedding "what is X" explanation in content meant to tell someone what to DO |
| **Presentations** | Explanation | Putting how-to procedures in slides. Slides show WHY; handout guides show HOW |
| **Data model docs** | Reference | Mixing "how to use it" (how-to) or "why we designed it" (explanation) into reference |
| **Principles docs** | Explanation | Including step-by-step application procedures (those are how-to guides) |
| **Getting started** | Tutorial | Mixing reference tables into a guided walkthrough |

---

## Source

Diataxis by Daniele Procida (diataxis.fr). Widely adopted: Django, NumPy, Gatsby, Canonical.
