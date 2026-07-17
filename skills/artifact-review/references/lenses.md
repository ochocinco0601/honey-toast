# Evaluation Lenses - Detailed Criteria

## Table of Contents
- [UX/Visual Design](#uxvisual-design)
- [Documentation Design](#documentation-design)
- [Stakeholder Fit](#stakeholder-fit)
- [Workflow Logic](#workflow-logic)
- [Comprehension](#comprehension)
- [Semantic Accuracy](#semantic-accuracy)
- [Inclusivity](#inclusivity)
- [Word Economy](#word-economy)

---

## UX/Visual Design

Evaluate visual presentation and interaction design.

### Evaluation Criteria

| Aspect | Questions | Look For |
|--------|-----------|----------|
| **Visual Hierarchy** | Does the eye know where to go? What's primary vs secondary? | Clear focal points, size/weight differentiation, logical reading order |
| **Layout & Spacing** | Is whitespace used effectively? Cluttered or breathing room? | Consistent margins, grouped related items, separation between sections |
| **Cognitive Load** | How much mental effort per screen? | Information density, number of choices, competing elements |
| **Feedback & Affordance** | Do interactive elements look interactive? Is state clear? | Button styling, hover states, progress indicators, error visibility |
| **Consistency** | Do similar elements behave similarly? | Pattern repetition, predictable locations, uniform styling |

### Output Format

```markdown
### UX/Visual Design

**What Works:**
- [Specific positive observation with element reference]

**Issues Found:**
| Priority | Element/Section | Issue | Impact |
|----------|-----------------|-------|--------|
| Critical/Medium/Minor | [location] | [problem] | [user impact] |

**Recommendations:**
- [Specific actionable improvement]
```

---

## Documentation Design

Evaluate information architecture and progressive disclosure.

### Evaluation Criteria

| Aspect | Questions | Look For |
|--------|-----------|----------|
| **Information Architecture** | Is content chunked logically? Can different entry points find their path? | Clear sections, logical groupings, multiple navigation paths |
| **Progressive Disclosure** | Is complexity revealed appropriately? Too much upfront? | Layered detail, expand/collapse patterns, beginner vs advanced paths |
| **Navigation** | Can users find what they need? Is location clear? | Breadcrumbs, clear headings, table of contents, back/next flow |
| **Content Hierarchy** | Are headings descriptive? Is structure scannable? | Heading levels, summary-then-detail pattern, visual scanning support |
| **Completeness** | Are there gaps? Dead ends? Missing context? | Orphan pages, unexplained terms, assumed knowledge |

### Output Format

```markdown
### Documentation Design

**What Works:**
- [Specific positive observation]

**Issues Found:**
| Priority | Section | Issue | Impact |
|----------|---------|-------|--------|
| Critical/Medium/Minor | [location] | [problem] | [user impact] |

**Recommendations:**
- [Specific actionable improvement]
```

---

## Stakeholder Fit

Evaluate whether artifact serves its intended audience given their timeframe and needs. Define stakeholder profiles for the specific artifact being reviewed.

### Evaluation Criteria

| Aspect | Questions | Look For |
|--------|-----------|----------|
| **Timeframe Alignment** | Does content match stakeholder's operational cadence? | Real-time for SRE, sprint-level for PO, quarterly for Platform, annual for Exec |
| **Decision Support** | Does it help them make their decisions? | Actionable info for their scope, relevant metrics, appropriate detail level |
| **Mental Model Match** | Does structure align with how they think about work? | Familiar terms, expected organization, workflow-aligned sections |
| **Value Proposition** | Is "why should I care" clear for this stakeholder? | Benefits framed in their terms, outcomes they care about |

### Output Format

```markdown
### Stakeholder Fit: [Stakeholder Type]

**What Works:**
- [How artifact serves this stakeholder]

**Issues Found:**
| Priority | Element | Issue | Impact on [Stakeholder] |
|----------|---------|-------|-------------------------|
| Critical/Medium/Minor | [location] | [problem] | [specific stakeholder impact] |

**Recommendations:**
- [Specific improvement for this stakeholder]
```

---

## Workflow Logic

Evaluate the logical flow of steps, failure points, and recovery paths.

### Evaluation Criteria

| Aspect | Questions | Look For |
|--------|-----------|----------|
| **Step Sequence** | Do steps make logical sense? Is order correct? | Dependencies honored, prerequisites stated, logical progression |
| **Failure Points** | Where could users get stuck? What happens on error? | Error states, validation feedback, unclear instructions |
| **Recovery Paths** | Can users recover from mistakes? Is backtracking possible? | Undo options, edit previous steps, clear error recovery |
| **Edge Cases** | What about unusual inputs? Missing data? | Handling of optional fields, empty states, boundary conditions |
| **Completion** | Is it clear when done? What happens next? | Success confirmation, next steps, handoff to other processes |

### Output Format

```markdown
### Workflow Logic

**What Works:**
- [Specific positive observation about flow]

**Issues Found:**
| Priority | Step/Point | Issue | Failure Mode |
|----------|------------|-------|--------------|
| Critical/Medium/Minor | [location] | [problem] | [what goes wrong] |

**Recommendations:**
- [Specific flow improvement]
```

---

## Comprehension

Evaluate ease of understanding, jargon, assumptions, and learnability.

### Evaluation Criteria

| Aspect | Questions | Look For |
|--------|-----------|----------|
| **Jargon & Terminology** | Are terms explained? Is vocabulary appropriate for audience? | Undefined acronyms, domain terms without context, inconsistent naming |
| **Assumptions** | What prior knowledge is assumed? Are assumptions valid? | Skipped explanations, "you know" patterns, expert blind spots |
| **Learnability** | Can someone new follow this? Is there a learning curve? | Onboarding path, examples, scaffolding for new concepts |
| **Clarity** | Is language clear and unambiguous? | Passive voice, vague pronouns, unclear antecedents |
| **Examples** | Are concepts illustrated? Do examples help? | Concrete examples, before/after, real scenarios |

### Fresh Eyes Test
Imagine encountering this artifact with zero prior domain knowledge:
- What would confuse you?
- What would you need to look up?
- Where would you get stuck?

### Output Format

```markdown
### Comprehension

**What Works:**
- [Specific clarity observation]

**Issues Found:**
| Priority | Element | Issue | Comprehension Barrier |
|----------|---------|-------|----------------------|
| Critical/Medium/Minor | [location] | [problem] | [what reader won't understand] |

**Recommendations:**
- [Specific clarity improvement]
```

---

## Semantic Accuracy

Evaluate whether terms, claims, and descriptions match reality across the artifact's full lifecycle — not just at the moment of writing.

### Evaluation Criteria

| Aspect | Questions | Look For |
|--------|-----------|----------|
| **Naming** | Are things called what they actually are? | Terms that describe one thing but the artifact is another (e.g., "dashboard" for a structured record) |
| **Temporal accuracy** | Are claims true today AND long-term? | Statements that are true now but false as the work evolves (e.g., "stays as they are" for something that will change) |
| **Consistency** | Does the same thing get called the same name throughout? | Term drift within the document, or terms that conflict with controlled vocabulary |
| **Relationship accuracy** | Do described relationships match actual relationships? | "Replaces" vs "informs," "produces" vs "enables," causal claims that aren't causal |

### Output Format

```markdown
### Semantic Accuracy

**What Works:**
- [Specific accuracy observation]

**Issues Found:**
| Priority | Term/Claim | Issue | Reality |
|----------|-----------|-------|---------|
| Critical/Medium/Minor | [the term or claim] | [what's wrong] | [what's actually true] |

**Recommendations:**
- [Specific correction]
```

---

## Inclusivity

Evaluate who this artifact assumes the reader is — and who it excludes.

### Evaluation Criteria

| Aspect | Questions | Look For |
|--------|-----------|----------|
| **Assumed experience** | What experience level does this assume? | "You know this," "you've done this before," assumed operational history |
| **Assumed role** | What role does this assume? | Senior IC language applied to a document juniors will also read |
| **Alternate paths** | Can someone who doesn't match the assumed profile still use this? | Single happy path with no accommodation for different starting points |
| **Exclusionary language** | Does any phrasing make a group feel this isn't for them? | Gendered language, seniority assumptions, cultural assumptions |
| **False constraints** | Does this impose rules the workflow doesn't require? | Arbitrary thresholds ("at least 2-3"), ownership claims ("your team owns"), completeness demands ("no blanks"), time references ("at 2 AM"), specificity added to sound authoritative that narrows the audience or creates gates that shouldn't exist |

### Key Question
Who is the INTENDED audience, and who ELSE will encounter this artifact? The fix is not to water down for everyone — it's to ensure the primary audience is served while others aren't blocked.

### Output Format

```markdown
### Inclusivity

**Intended audience:** [who this is designed for]
**Also likely to encounter it:** [who else will read it]

**Issues Found:**
| Priority | Location | Assumption | Who it excludes |
|----------|----------|-----------|-----------------|
| Critical/Medium/Minor | [line/section] | [what's assumed] | [who can't use it] |

**Recommendations:**
- [Specific wording change — REPLACE, don't add]
```

---

## Word Economy

Evaluate whether text can be cut. Every sentence must serve a task function. Replace, don't add.

### Evaluation Criteria

| Aspect | Questions | Look For |
|--------|-----------|----------|
| **Function test** | Does this sentence establish a problem, present evidence, draw a conclusion, or signal structure? (McEnerney) | Sentences that explain what the reader will see for themselves, restate what was just said, or describe obvious things |
| **Motivational filler** | Does this sentence reassure, encourage, or motivate rather than inform? | "It gets faster each time," "you'll find this useful," "this is what makes that possible," "visible to your team and managers." The reader doesn't need encouragement - they need the workflow. |
| **Audience knowledge** | Does this explain something the reader already knows? | Describing Confluence to a Confluence user, explaining JSON to an engineer |
| **Redundancy** | Is the same point made twice in different words? | Parallel sections with overlapping content, definitions restated |
| **Qualifier bloat** | Can hedging words, filler phrases, or unnecessary modifiers be cut? | "In order to," "it should be noted that," "basically," "essentially" |

### Key Constraint
When a finding suggests a fix, the fix must be SHORTER than the original. If you can't make it shorter, flag it but don't propose adding text.

### Output Format

```markdown
### Word Economy

**Current word count:** [N]
**Estimated reducible:** [N words / N%]

**Issues Found:**
| Priority | Location | Current | Shorter alternative |
|----------|----------|---------|-------------------|
| Medium/Minor | [line] | [verbose text] | [tighter version] |

**Recommendations:**
- [Specific cuts]
```
