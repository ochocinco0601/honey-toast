---
name: artifact-review
description: Evaluate artifacts (documentation, dashboards, guides, playbooks, presentations) from expert perspectives using selectable lenses. Use when reviewing artifacts for usability, clarity, stakeholder fit, or quality issues. Triggers on "review this artifact", "evaluate this", "check this for usability", "does this work for [audience]", "is this too complex", "expert review", "critique this", or when assessing any deliverable before sharing with stakeholders.
---

# Artifact Review - Multi-Lens Expert Evaluation

Evaluate artifacts from multiple expert perspectives, producing structured feedback.

## Key Principle: Evaluation as Living Document

The evaluation report is a **living document**, not a one-time report:
- Findings have **suggested priorities** (agent's judgment as starting point)
- User adds **their priority** (may differ from suggestion)
- User marks **status** as work happens (OPEN → FIXED / WON'T FIX)

---

## Invocation Patterns

### All Lenses (Comprehensive)
```
/artifact-review /path/to/artifact
```

### Selective Lenses
```
/artifact-review ux /path/to/file.html
/artifact-review stakeholder sre /path/to/dashboard.json
/artifact-review workflow comprehension /path/to/guide.md
```

### Available Lenses

| Lens | Shorthand | Focus |
|------|-----------|-------|
| UX/Visual Design | `ux` | Layout, hierarchy, cognitive load, visual clarity |
| Documentation Design | `docs` | Information architecture, progressive disclosure, navigation |
| Stakeholder Fit | `stakeholder [type]` | Does it serve the target audience's needs? |
| Workflow Logic | `workflow` | Steps make sense, failure points, recovery paths |
| Comprehension | `comprehension` | Jargon, assumptions, learnability, fresh eyes |
| Semantic Accuracy | `accuracy` | Are terms true? Do claims hold? Naming matches reality? |
| Inclusivity | `inclusivity` | Who does this assume the reader is? Who can't use it? |
| Word Economy | `economy` | Can text be cut? Is every sentence serving a function? |

---

## Workflow

### 1. Determine Input Requirements

| Lens | Input Required | Why |
|------|----------------|-----|
| `ux` | **Rendered screenshots** | Visual hierarchy, layout, density require seeing the artifact |
| `docs` | Source code/content | IA and navigation visible in structure |
| `stakeholder` | Both source + rendered | Content from source, presentation from visual |
| `workflow` | Source + rendered | Step logic in code, user flow in visual |
| `comprehension` | Source primarily | Jargon and language are in the text |

### 2. Load Artifact

**For source analysis**: Read the file(s).

**For visual analysis** (when `ux`, `stakeholder`, or `workflow` lenses selected):
- Render and capture screenshots if possible
- Capture key screens: initial view, each major section, interactive states

### 3. Load Lens Criteria
Read `references/lenses.md` for detailed evaluation criteria per lens.

### 4. Evaluate
Apply each lens systematically:
- Note specific elements/sections (line numbers, element IDs, section names)
- Assign **suggested priority** (agent's judgment)
- Identify what works well

### 5. Write Report

Save to the location specified by the calling context. If none specified, save to the directory containing the artifact being reviewed.

---

## Output Format

```markdown
# Artifact Evaluation Report

**Artifact**: [name/path]
**Date**: [YYYY-MM-DD]
**Lenses Applied**: [list]
**Status**: Pending review | In progress | Complete

## How to Use This Report

This is a living document. For each finding:
1. Review the **Suggested** priority (agent's judgment)
2. Add **Your Priority** based on your context (may differ)
3. Update **Status** as you work: OPEN → FIXED | WON'T FIX

## Executive Summary
[2-3 sentences: overall assessment, finding counts, recommendation]

## Tracking Summary

| Suggested | Count | Fixed | Open | Won't Fix |
|-----------|-------|-------|------|-----------|
| Critical | N | 0 | N | 0 |
| Medium | N | 0 | N | 0 |
| Minor | N | 0 | N | 0 |

## [Lens Name]

**What Works:**
- [Specific positive with element reference]

**Findings:**
| ID | Issue | Suggested | Your Priority | Status |
|----|-------|-----------|---------------|--------|
| 1 | [specific issue with location] | Critical | ___ | OPEN |
| 2 | [specific issue with location] | Medium | ___ | OPEN |

**Recommendations:**
1. [Specific actionable improvement]

[Repeat for each lens]

## All Findings (Flat List)

For easy scanning and status tracking:

| ID | Lens | Issue | Suggested | Your Priority | Status |
|----|------|-------|-----------|---------------|--------|
| UX-1 | UX | [issue] | Medium | ___ | OPEN |
| DOC-1 | Docs | [issue] | Minor | ___ | OPEN |
| WF-1 | Workflow | [issue] | Critical | ___ | OPEN |
...
```

---

## Priority Definitions (Suggested)

These are the agent's suggested priorities. You may re-prioritize based on your context.

| Priority | Definition | Typical Action |
|----------|-----------|----------------|
| **Critical** | Blocks user success, causes confusion/failure | Fix before sharing |
| **Medium** | Degrades experience, causes friction | Fix soon |
| **Minor** | Polish items, inconsistencies | Fix when convenient |

---

## Evaluation Stance

Apply expert judgment, not checklist compliance:
- **Be specific**: "The submit button at line 247 lacks loading state" not "buttons should have states"
- **Explain impact**: Why does this matter for the user?
- **Suggest priorities**: But acknowledge user may reprioritize
- **Acknowledge strengths**: What's working well and why

Fresh eyes perspective: Evaluate as if encountering this artifact for the first time, without insider knowledge of the domain methodology.

---

## References

- **Lens criteria**: `references/lenses.md`
