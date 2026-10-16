---
name: html
description: Produce interactive, self-contained HTML from any content, shaped for a specific job to be done (understand, assess risk, brief, present, orient, reference). Use whenever the user wants content rendered as HTML instead of markdown, wants a long document made consumable, wants an interactive view of an analysis or report, says "render this as HTML", "make this an HTML page", "interactive version of this", or wants to share a document that opens in any browser with no dependencies. This skill is the output format layer: it shapes content for a job, not just wraps it in tags.
---

# /html: produce interactive HTML from content

Produce self-contained, interactive HTML shaped for a specific job. The input is content in any form: an existing file, the output of a skill that just ran, or thinking in the current session. The output is a single `.html` file with inline CSS and JS, no external dependencies, opening in any browser.

This is not a markdown-to-HTML converter. The same source rendered for "understand" looks different from "assess risk" or "brief a stakeholder."

## Workflow

1. **Determine the job.** What does the reader need to do with this content?
2. **Classify.** Diataxis type, LATCH scheme, visual argument.
3. **Select a layout shell.**
4. **Shape.** Apply the moves that serve the job.
5. **Produce.** Load the two design skills first (Step 5), then build.
6. **Evaluate.** Climb the quality ladder; fix until rung 3 or higher.

## Step 1: Discover the job

The job is what the reader needs to do with the content. It organizes every later decision: layout, emphasis, grouping, what is foregrounded, what is omitted.

Jobs are discovered, not only specified. Check in order:

1. **Explicit.** The user says "render this for risk assessment" or "I need to brief someone with this." Use it.
2. **Context.** What just happened in the session? A system analysis implies "understand." A status roll-up implies "orient." "I need to share this" implies "brief" or "present."
3. **Content.** A document heavy on failure modes and assumptions implies "assess risk." One with recommendations and options implies "brief." One with step-by-step procedures implies "follow."

State the discovered job before proceeding. If it is genuinely ambiguous, name the two candidates, pick one and shape for it. The user redirects if wrong.

| Job | Shaping approach | What gets foregrounded |
|---|---|---|
| **Understand** | Shneiderman's overview-first mantra | Overview with insight, conceptual grouping (how / what / why), synthesis leads |
| **Assess risk** | Pre-mortem structure (Klein) | Failure modes, risks and assumptions at the top; risk stats in the overview |
| **Brief** | Minto Pyramid: situation, complication, resolution | Executive summary first, recommendations prominent, detail subordinated |
| **Present** | Duarte and Reynolds minimal-text principles | Key messages, visual weight, sparse content, large type |
| **Orient** | Situation-report structure | Status, obligations, constraints, next actions; temporal grouping |
| **Reference** | Diataxis reference type | Sidebar for non-linear consultation, consistent section format, search |

The table is a starting vocabulary. If the content surfaces another job, name it, name a shaping approach by analogy, and proceed. Name the approach; do not encode its steps.

## Step 2: Classify the content

State the classification before producing HTML.

**Layer 1, Diataxis type (reader relationship):**
- Reference: reader consults non-linearly. Needs sidebar, search, consistent format.
- Explanation: reader builds understanding. Needs narrative flow and connections.
- How-to: reader follows steps. Needs sequential flow, checkboxes, progress.
- Tutorial: reader learns by doing. Needs a guided sequence and a focused view.

**Layer 2, LATCH organizing scheme (Wurman):**
- Hierarchy: tree navigation.
- Time: timeline navigation.
- Category: tab or card navigation.
- Location: spatial layout.
- Alphabet: indexed list.

**Layer 3, visual argument (what the layout encodes):**
- Components relate structurally: spatial architecture or composite cheatsheet.
- Peer options: side-by-side or card grid.
- Sequence: linear flow or timeline.
- Multiple facets: composite with a central hub.
- Two aspects answering different questions: two-zone composite.

## Step 3: Select a layout shell

| Shell | Use for |
|---|---|
| Sidebar + content | Reference, analyses, multi-section documents |
| Single-column narrative | Explanations, briefings, explainers |
| Step-flow | Plans, runbooks, how-to guides |
| Composite with hub | Multi-faceted reference, cheatsheets, dashboards |
| Card grid | Peer comparison, options, alternatives |

## Step 4: Apply shaping moves

Six moves. Apply the ones the job requires.

### The governing constraint: shaping never adds claims

When the input has a source of record, every sentence on the page traces to a sentence in that source. The moves below arrange; they do not assert.

| Shaping may | Shaping may not |
|---|---|
| Reorder, group, collapse, promote, cross-link | Add a fact, a date, a name, a number |
| Choose what is foregrounded for the job | Draw a conclusion the source does not draw |
| Set visual weight and hierarchy | Soften a hedge or harden a claim ("looks like" to "is") |
| Cut what the job does not need, and say what was cut | Silently drop a caveat, a source tag or an unknown |

Moves 1 and 4 are where invention enters, because an insight-driven overview and a synthesis lead are new prose by construction. Write them into the source, not into the render, so they are reviewable and carry provenance.

Two cases:

- **A source of record exists.** The render is faithful: zero new sentences. If the page needs a lead the source lacks, add it to the source and re-render.
- **No source of record** (live session thinking, one-off content). The HTML is the record, so it carries its own provenance, and its authored prose is labelled as the session's reading, not as fact.

Before delivering, list every sentence on the page that is not in the source. An empty list passes case one. A non-empty list is a work item: those sentences go into the source first.

### Move 1: insight-driven overview
Composed in the source. The overview synthesizes; it does not summarize. State what matters and why, not counts or labels.
- Weak: "5 sections, 12 endpoints, 3 services."
- Strong: "One middleware everything trusts. If verifyToken is wrong, every route behind it is wrong."

Include a "things to know" callout of two to four sentences that gives the reader a mental model in 15 seconds.

### Move 2: hierarchy signaling
- Tier 1 sections (primary for the job): accent left border.
- Tier 2 sections (supporting): a quieter left border.
- Reference detail: no border.
- Stat cards in the overview show meaning, not counts.

### Move 3: conceptual grouping
Reorganize by meaning, not by source structure. Name groups as questions: "How it works," "What can go wrong," "Why it is designed this way." Sidebar navigation and body order must match. Group dividers without a body reorder are worse than none.

### Move 4: synthesis leads
Composed in the source. One italic sentence at the top of each section body that tells the section's story before the detail.

### Move 5: cross-linking
Connect related content across sections: clicking a component name in a failure-modes table opens and scrolls to the components section. Use a small `openSection('id')` function.

Every reference on the page is a link, not a label. An identifier the reader must copy and look up by hand is a chore the render was meant to remove.
- A reference with no target stays inert and visibly so. Do not invent a destination.
- Verify a link scheme works before wiring it. A dead link looks actionable and is not.
- Build absolute paths from the run's working directory, never a remembered root.
- Say on the page, in one legend line, what opens where.

Clickable must be visible at rest, not only on hover:

| State | Treatment |
|---|---|
| Link, at rest | Underline (2px offset) plus a small arrow, `cursor: pointer` |
| Link, hover | Brightness shift and a ring, as a change and not the first signal |
| Link, keyboard focus | Visible `:focus-visible` outline |
| Not a link | About 55% opacity, no arrow, `cursor: default` |

Show one live chip and one dead chip side by side in the legend.

Check glyphs by rendering. A CSS escape such as `content: "\2197"` can print as literal text depending on how it terminates; prefer the character itself and look at the result. Test identifier legibility in the actual face: a monospace `O1` reads as zero-one, so avoid single-letter schemes that collide with `O/0`, `I/1`, `S/5`, `B/8`, `Z/2`.

Every in-page jump owes the reader four things, because silent scrolling on a page where every section looks alike is disorientation:

| | |
|---|---|
| **Land on the item** | Anchor each item individually, not just its section. Scroll with `block: 'center'` so it lands in the eye's resting zone, not under a header. |
| **Flash it** | A 2 to 3 second highlight plus a persistent edge marker on the row or card. |
| **Move focus** | `tabindex="-1"` and `.focus({preventScroll: true})` on the target, with a real focus ring. |
| **Offer the way back** | A "Back to <section>" control that restores the exact prior scroll position. Name the origin from the clicked link's own section, not from scroll-spy state. |

Also: sticky section headers while a section is open, and a heavy, clearly marked active state in the navigation. Anchors double as deep links: `page.html#p4` opens that section and lands on item P4.

### Move 6: job-specific foregrounding
For the stated job, foreground the relevant sections (expanded by default, promoted to overview stats) and subordinate the rest (collapsed, no tier border).

## Step 5: Design

**Before writing any HTML, load both companion skills:** `frontend-design` (visual direction: palette, type, layout) and `html-design-contract` (page mechanics: skeleton, tokens, light and dark, responsive rules, delivery checklist). Do not start the page until both are loaded. Do not ask the user to name them. This skill sets no palette or fonts of its own, and an existing project design system overrides both. When the page is built, run the contract's delivery checklist before handing it over.

Interaction patterns:
- Collapsible sections via button toggle (not `<details>`).
- Sticky sidebar with scroll spy.
- Cross-link navigation via `openSection()`.
- Section summary chips on the toggle bar, right-aligned and quiet.

## Step 6: Evaluation, the quality ladder

Declare which rung the output reaches.

**Rung 1, navigable (mechanical)**
- [ ] The overview fits one viewport without scrolling.
- [ ] Sub-regions are independently understandable.
- [ ] Semantic colour is consistent: one system, no dual meaning.
- [ ] No layout defects (overflow, truncation, broken interaction).

**Rung 2, oriented**
- [ ] The overview gives insight, not data.
- [ ] A hierarchy of importance is visible.
- [ ] The reader can answer "what is this and why should I care?" in 30 seconds.

**Rung 3, shaped for the job**
- [ ] Content is restructured for the job, not mirrored one to one.
- [ ] Job-relevant sections are foregrounded, the rest subordinated.
- [ ] Cross-links connect related content.
- [ ] Sidebar and body order match.

**Rung 4, understandable**
- [ ] The document tells the story, not just a list of parts.
- [ ] Cause and effect are visible.
- [ ] The reader could explain the subject to someone else.

Protocol:
1. Take a screenshot and read it.
2. Check rung 1; fix defects; re-check.
3. Check rung 2; rewrite the overview if it is data, not insight; add hierarchy if flat.
4. Check rung 3; name the job; compare what is foregrounded with what the job needs.
5. Check rung 4; read the overview and one expanded section; could you explain this?
6. Declare the rung reached. Rung 3 is the minimum. Do not present below it.

## Output

- A single `.html` file, self-contained: inline CSS and JS, no CDN, no build step.

**Where the file goes.** A page worth rendering is worth keeping, so never leave it only in a session's temporary folder, where it disappears with the session.

| Case | Path |
|---|---|
| The user named a location | Use it |
| Rendering an existing file | Alongside the source |
| Anything else | Ask for one, or use a durable path in the project |

Keep one maintained rendering, not dated copies: put the date in the page header, not the filename, so copies do not fork and go stale.

**Hand over by opening the file.** The deliverable is the page open in the user's browser. The last step of every run is to open it with the platform's opener (`Start-Process` on Windows, `open` on macOS, `xdg-open` on Linux), then say in one line that it is open and what it is. A path printed in chat is inert text the user has to carry into a browser by hand. Build the absolute path from the run's working directory.

## What this skill does not do

- Convert markdown mechanically. It shapes content for a job.
- Decide what to say. Other skills and the user shape the content; this one shapes the format, and the two compose.
- Require source skills to change. It works with whatever content exists.
