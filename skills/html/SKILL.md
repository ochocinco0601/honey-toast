---
name: html
description: >
  Produce interactive, self-contained HTML from any content — shaped for a specific
  job to be done (understand, assess risk, brief, present, orient, reference). Use
  this skill whenever the user wants content rendered as HTML instead of markdown,
  wants to make a long document consumable, needs an interactive view of a system
  analysis or report, says "render this as HTML", "make this consumable", "produce
  HTML", "html output", "I can't read 500 lines of markdown", or when any skill
  output would be better served as a navigable interactive document rather than flat
  text. Also use when the user says "make this an HTML page", "interactive version
  of this", or wants to share a document that opens in any browser with no
  dependencies. This skill is the output format layer — it shapes content for a job,
  not just wraps it in tags.
---

# /html — Produce Interactive HTML from Content

Produce self-contained, interactive HTML shaped for a specific job. The input is content in any form — an existing file, the output of a skill that just ran, or thinking happening in the current session. The output is a single `.html` file: inline CSS/JS, no external dependencies, opens in any browser.

This is NOT a markdown-to-HTML converter. It is an output format skill that shapes content for a job to be done. The same source content rendered for "understand" looks different from "assess risk" or "brief a stakeholder."

**Reference examples:** `references/examples/index.html` — a gallery of 20 worked examples, one per job type. Open it to see what the output should feel like. The design tokens in Step 5 come from the same set.

## Workflow

1. **Determine the job** — what does the reader need to DO with this content?
2. **Classify** — Diataxis type, LATCH scheme, visual argument
3. **Select layout** — which shell fits the classification?
4. **Shape** — apply the moves that serve the job
5. **Produce** — build HTML with the design token system
6. **Evaluate** — climb the quality ladder, fix until Rung 3+

## Step 1: Discover the Job

The job is what the reader needs to DO with this content. It's the organizing cut for every decision that follows — layout, emphasis, grouping, overview, what's foregrounded, what's omitted.

**Jobs are discovered, not just specified.** Three sources, checked in order:

1. **Explicit:** The user says "render this for risk assessment" or "I need to brief someone with this." Use it.
2. **Context:** What just happened in the session? If a system analysis just ran, the job is probably "understand." If a status briefing just ran, probably "orient." If the user said "I need to share this," probably "brief" or "present." The invoking context carries intent.
3. **Content:** What does the content itself imply? A document heavy on failure modes and assumptions implies "assess risk." A document with recommendations and options implies "brief." A document with step-by-step procedures implies "follow." Read the content structure — the job is often visible in what's there.

State the discovered job before proceeding. If genuinely ambiguous, name the two candidates and why — then pick one and shape for it. The user redirects if wrong.

### Job vocabulary

| Job | Named shaping approach | What gets foregrounded |
|-----|----------------------|----------------------|
| **Understand** | Shneiderman's overview-first mantra | Overview with insight, conceptual grouping (how/what/why), synthesis leads |
| **Assess risk** | Pre-mortem structure (Gary Klein) | Failure modes, risks, assumptions promoted to top; risk stats in overview |
| **Brief** | Minto Pyramid — situation, complication, resolution | Executive summary first, recommendations prominent, detail subordinated |
| **Present** | Duarte/Reynolds minimal-text principles | Key messages, visual weight, sparse content, large type |
| **Orient** | Chief-of-staff terrain model | Status, obligations, constraints, next actions; temporal grouping |
| **Reference** | Diataxis reference type | Sidebar for non-linear consultation, consistent section format, search-optimized |

This table is a starting vocabulary, not a closed set. Content may surface a job not listed here — name it, name the shaping approach by analogy, proceed.

The LLM knows these approaches from training. Naming them activates the full methodology — don't encode the steps, name the approach.

## Step 2: Classify the Content (three layers)

Each layer constrains the layout differently. State the classification before producing HTML.

**Layer 1 — Diataxis type** (reader relationship):
- Reference → reader consults non-linearly → needs sidebar, search, consistent format
- Explanation → reader builds understanding → needs narrative flow, connections
- How-to → reader follows steps → needs sequential flow, checkboxes, progress
- Tutorial → reader learns by doing → needs guided sequence, focused view

**Layer 2 — LATCH organizing scheme** (Wurman):
- Hierarchy → tree navigation (C4 levels, org charts, component nesting)
- Time → timeline navigation (status reports, incident reports, changelogs)
- Category → tab or card navigation (options lists, feature comparisons)
- Location → spatial layout (architecture diagrams, service maps)
- Alphabet → indexed list (glossaries, API references)

**Layer 3 — Visual argument** (what the layout encodes):
- "Components relate structurally" → spatial architecture or composite cheatsheet
- "These are peer options" → side-by-side or card grid
- "This happened in sequence" → linear flow or timeline
- "This has multiple facets" → composite with central hub
- "Two aspects answer different questions" → two-zone composite

## Step 3: Select Layout Shell

| Shell | When to use |
|-------|------------|
| **Sidebar + content** | Reference, system analyses, multi-section documents |
| **Single-column narrative** | Explanations, briefings, explainers |
| **Step-flow** | Implementation plans, runbooks, how-to guides |
| **Composite with hub** | Multi-faceted reference, cheatsheets, dashboards |
| **Card grid** | Peer comparison, options lists, alternatives |

## Step 4: Apply Shaping Moves

Six named moves discovered through spike testing. Apply the ones the job requires — not all moves apply to all jobs.

### Move 1: Insight-driven overview
The overview synthesizes, it doesn't summarize. State what matters and why — not counts or labels.
- BAD: "7 stages, 26 components, 10+ services"
- GOOD: "One judgment step everything depends on. If the capture is wrong, every downstream artifact is wrong."

Include a "things to know" callout — 2-4 sentences that give the reader a mental model in 15 seconds.

### Move 2: Hierarchy signaling
Not all sections are equal. Signal importance visually:
- Tier 1 sections: clay left-border (primary for the job)
- Tier 2 sections: oat left-border (supporting)
- Untied sections: no border (reference detail)
- Stat cards in overview show meaning, not counts

### Move 3: Conceptual grouping
Reorganize content by meaning, not by source structure. Name the groups as questions: "How it works," "What can go wrong," "Why it's designed this way."

**All-or-nothing rule:** Sidebar navigation AND body section order must match. Group dividers without body reorder creates visible inconsistency — worse than no dividers.

### Move 4: Synthesis leads
One italic sentence at the top of each section body that tells the section's story before the detail. The reader gets the point without reading the table.
- "Most failures are caught by validators. The dangerous one — wrong but schema-valid understanding — can only be caught by human review."

### Move 5: Cross-linking
Connect related content across sections. Clicking a component name in the failure modes table opens and scrolls to the components section. Trivial in HTML, impossible in markdown. Use `<a class="xref" onclick="openSection('sN')">` pattern.

### Move 6: Job-specific foregrounding
For the stated job, foreground the relevant sections (expanded by default, promoted to overview stats) and subordinate the rest (collapsed, no tier border). The job table in Step 1 names what gets foregrounded.

## Step 5: Design Token System

Use these tokens. Do not invent alternatives. Source: 20 reference examples at `references/examples/`.

### Palette
```css
--ivory:  #FAF9F5;   /* page background */
--paper:  #FFFFFF;   /* card/panel background */
--slate:  #141413;   /* primary text */
--clay:   #D97757;   /* attention, warning, primary accent */
--clay-d: #B85C3E;   /* darker clay for text on light backgrounds */
--oat:    #E3DACC;   /* secondary accent, supporting borders */
--olive:  #788C5D;   /* success, positive states */
```
Gray ramp: `--g50` through `--g700` for structure (borders, labels, metadata).

### Semantic color roles
- **Clay** = look here, warning, attention, primary tier
- **Olive** = good, done, success, durable
- **Gray** = neutral, metadata, mechanical, stateless

One color system per document. If clay means "attention" in the overview, it means "attention" everywhere.

### Typography
- **Headings:** `--serif` (ui-serif, Georgia), weight 500, letter-spacing -0.01em
- **Body:** `--sans` (system-ui), 14px, line-height 1.6
- **Metadata/labels:** `--mono` (ui-monospace, SF Mono), 10-11px, uppercase, letter-spacing 0.08em
- **Code:** `--mono`, 12px, `--g100` background, 4px radius

### Borders and panels
- Borders: 1.5px solid (not 1px, not 2px)
- Panel radius: 12px
- Chip/small element radius: 8px
- Transitions: 150ms ease

### Interaction patterns
- Collapsible sections via button toggle (not `<details>`)
- Sticky sidebar with scroll spy
- Cross-link navigation via `openSection()` JS function
- Section summary chips on toggle bar (right-aligned, mono, gray)

## Step 6: Evaluation — Quality Ladder

Evaluate on a ladder. Each rung depends on the one below. Declare which rung the output reaches.

**Rung 1 — Navigable** (mechanical)
- [ ] Overview fits one viewport without scrolling
- [ ] Sub-regions independently understandable
- [ ] Semantic color consistent — one system, no dual meaning
- [ ] No layout defects (overflow, truncation, broken interaction)

**Rung 2 — Oriented** (the reader knows what they're looking at)
- [ ] Overview provides insight, not data
- [ ] Hierarchy of importance visible — not all sections equal
- [ ] Reader can answer "what is this and why should I care?" in 30 seconds

**Rung 3 — Shaped for the job** (content serves the stated purpose)
- [ ] Content restructured for the job, not mirrored 1:1 from source
- [ ] Job-relevant sections foregrounded, job-irrelevant subordinated
- [ ] Cross-links connect related content across sections
- [ ] Sidebar and body order match (all-or-nothing grouping)

**Rung 4 — Understandable** (reader builds a mental model)
- [ ] Document tells the story, not just lists parts
- [ ] Cause-effect relationships visible
- [ ] Reader could explain the subject to someone else after reading

### Self-evaluation protocol
1. Review the output visually.
2. Check Rung 1. Fix defects. Re-check.
3. Check Rung 2. Rewrite overview if data-not-insight. Add hierarchy if flat.
4. Check Rung 3. Name the job. Compare what's foregrounded vs what the job needs.
5. Check Rung 4. Read overview + one expanded section. Could you explain this?
6. Declare the rung reached. Rung 3 is the minimum acceptable output.

Fix and iterate until Rung 3+. Do not present to the user below Rung 3.

## Output

- Single `.html` file, self-contained (inline CSS/JS, no CDN, no build step)
- Place alongside source file or in location the user specifies
- Opens in any browser with no dependencies

## What This Skill Does NOT Do

- **Convert markdown mechanically.** It shapes content for a job. Same source, different job = different output.
- **Replace visual/diagram skills.** Those produce communication visuals (diagrams, infographics, slides). This skill produces interactive documents. If the job is "make a diagram," use a diagram skill. If the job is "make this 500-line analysis consumable," use this skill.
- **Replace briefing or editorial skills.** Those shape CONTENT (what to say, how to say it). This skill shapes the FORMAT (how to present it interactively). They compose — briefing shapes the message, this skill renders it as interactive HTML.
- **Require source skills to change.** The skill works with whatever content exists. Source skills don't need HTML-awareness.
