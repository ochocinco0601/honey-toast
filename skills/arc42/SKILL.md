---
name: arc42
description: >
  Transform raw, unstructured source material about a system or service into
  arc42-structured architecture documentation (12 chapters). Produces markdown
  output suitable for direct use, or as structured input to any downstream
  process that needs a system described.
  Use when the user says "arc42 for [service]", "create arc42 docs",
  "structure this as arc42", "document this system's architecture",
  or when a system lacks architecture documentation.
---

# Arc42 Normalization

Transform raw source material into arc42-structured architecture documentation. This is a preprocessing capability — it normalizes messy input into a structured format that humans can read and that downstream processes can consume.

**Guiding principle:** "Minimal but honest" — produce the smallest amount of documentation that prevents expensive misunderstandings. Chapters with source material get populated. Chapters without get explicit gap statements. Never fabricate content to fill structural slots.

**Form: this is reference, not explanation.** Diátaxis separates the two, and the default failure is
writing explanation — an essay that argues its way forward — when the reader will enter at the
chapter they need. Load `/doc-check` if the distinction is unfamiliar. In practice: **tables
carry decisions, rules, risks, borrowed practice and vocabulary**; prose is for the problem
statement and little else. A three-column table — decision, why, what it costs — carries the same
reasoning as three paragraphs and can be scanned. If under roughly a third of the document's lines
are table rows on a structured subject, it has drifted into explanation.

**Domain knowledge:** The arc42 template is an established 12-chapter architecture documentation standard (arc42.org). Per-chapter guidance on what belongs, what doesn't, minimum viable versions, and quality checklists lives in `references/chapter-guidance.md`, distilled from Michaël Hompus's practical series. The full source is Hompus's public blog series at https://blog.hompus.nl (tag: arc42).

**Exemplar:** Complete, filled-in arc42 docs for the Pitstop garage management system ship with this skill at `references/exemplar/arc42/`, with the decision records they cite at `references/exemplar/ADRs/`. Read 2-3 chapter files during Phase 1 to calibrate output level. Provenance and licence: `references/exemplar/README.md`.

---

## Phase 0a: Frame — who reads this, and what must they decide

**Run this before cataloguing anything.** ISO/IEC/IEEE 42010, which arc42 conforms to, orders the
work: **stakeholders → concerns → viewpoint selection → views.** Concerns *select* which views get
produced. A view that frames no identified concern is non-conforming — which is exactly the failure
of filling every chapter completely while missing what the reader needed.

**Do not defer this to chapter production.** Chapter 1's guidance lists "Key stakeholders and
their concerns" (`references/chapter-guidance.md:18`). Producing concerns as an *output* of chapter
production inverts the ordering that is supposed to bound the work.

Write down, and carry into the output:

1. **Who reads this** — a person, not a role-shaped abstraction. "An engineer who has never seen it
   and must decide whether the design holds." "A model in a session with no access to this repo."
2. **What they must be able to decide.** Is it sound? Would I adopt it? What breaks if I change
   this? Can I run it?
3. **What they are NOT doing.** If they would verify a claim by reading the source, say so.

**Citations stay; argument goes.** Phase 0a and the Constraints block below can look like they
disagree — one says stop building an evidence trail, the other requires citations throughout. They
govern different things and both bind. **A citation is a location**, so a reader who does want to
check can; keep every one. **An evidence trail is rhetoric** — sentences whose job is to make the
reader believe the previous sentence. Cut those. The test: remove the sentence and ask whether the
reader lost a fact or only lost persuasion.

**Then let it bound the work.** The concern list decides which chapters are produced, at what depth,
and which are legitimately thin. A chapter no named concern reaches is not owed.

**Two failure modes this step exists to prevent**, both observed:

| Failure | What it looks like |
|---|---|
| **Serving the producer's concern** | The decisions chapter records *who ruled it and when* instead of the reason and the cost. A reader who must judge the design cannot use provenance of authority |
| **Serving the project manager's concern** | Risks and technical debt fills with what has not happened yet. You do not document a prototype by noting it has never run in production — maturity is a different axis in a different document |

---

## Phase 0: Source Catalog

**First, exclude any prior answer to this same task.** An existing description of this subject is
not a source — it is the answer key, and cataloguing it makes the run a paraphrase of work already
done. Search the subject's own directory and the output location for one before you start.

If a prior description exists, choose and **record the choice**: exclude it and produce an
independent account, or read it and state plainly that this run corroborates nothing. There is no
third option — a run cannot be both calibrated by a document and independent of it.

Read and catalog all remaining source material. For each source:

1. Assign an ID: S1, S2, S3...
2. Record: path, source type, 1-sentence description
3. Classify using `references/source-classification.md` — which arc42 chapters can this source inform?

**Code repo minimum read depth:** When a code repository is a source, "cataloging" means identifying and READING the following (not just noting they exist):
- Every `Program.cs` / startup file — DI registration, health checks, resilience policies, middleware
- Every controller / API surface — endpoints, error handling, response codes
- Shared infrastructure libraries — abstractions, implementations, retry behavior
- Configuration files (`appsettings.json`, `Dockerfile`) — runtime settings, health checks, environment config
- At least one representative file per service type (API vs worker vs library)

A source catalog entry that says "231 .cs files" without identifying which specific files inform which chapters is NOT a valid catalog. Name the files.

Produce a **source coverage matrix**:

```
SOURCE COVERAGE
| Source | Type        | Ch1 | Ch2 | Ch3 | Ch4 | Ch5 | Ch6 | Ch7 | Ch8 | Ch9 | Ch10 | Ch11 | Ch12 |
| S1     | product doc |  P  |     |  S  |     |     |     |     |     |     |      |      |  S   |
| S2     | code repo   |     |     |     |     |  P  |  S  |  S  |  P  |     |      |      |      |
| Coverage:            |  1  |  0  |  1  |  0  |  1  |  1  |  1  |  1  |  0  |  0   |  0   |  1   |
```

This matrix drives the rest of the process. Chapters with zero coverage will be gap-only.

Present the matrix to the user before proceeding. If critical chapters (1, 3, 5) have no sources, flag this — the user may have additional material to provide.

---

## Phase 1: Read Exemplar

Read 2-3 chapter files from `references/exemplar/arc42/` to internalize the output structure and detail level. Good choices:
- `01-introduction-and-goals.md` (the compass chapter)
- `05-building-block-view.md` (the structural core)
- One chapter matching the user's richest source coverage

Also read the index page `references/exemplar/arc42/arc42.md` for the TOC structure.

---

## Phase 2: Chapter Production

**Bound by Phase 0a.** Before producing any chapter, name which concern from the framing it serves.
A chapter no named concern reaches gets a one-line gap statement, not a filled-in section — the
priority order below is a default sequence, not an obligation to produce all twelve. **The reader
named in Phase 0a decides depth**, and a chapter serving no reader is where padding accumulates.

Produce chapters in priority order (from the blog's "First Week Starter Pack"):

**First priority** (anchor everything):
1. Chapter 1: Introduction and Goals
2. Chapter 2: Architecture Constraints
3. Chapter 3: Context and Scope

**Second priority** (core structure and quality):
4. Chapter 5: Building Block View
5. Chapter 6: Runtime View
6. Chapter 10: Quality Requirements

**Third priority** (often emerge from earlier chapters):
7. Chapter 4: Solution Strategy — **must include what the design borrows from established
   practice, and what it deliberately did NOT take.** Name the practice, its field, the part
   adopted, and the part refused. A practice adopted in name but not in apparatus behaves nothing
   like one followed properly, and that difference is exactly what an evaluator needs. This is also
   the only section that lets a reader with no connection to the authors judge whether the design is
   grounded or invented. Where something genuinely has no established name, say so — that is a
   finding, not a gap.
8. Chapter 9: Architecture Decisions

**Fourth priority** (supporting chapters):
9. Chapter 7: Deployment View
10. Chapter 8: Cross-cutting Concepts
11. Chapter 11: Risks and Technical Debt
12. Chapter 12: Glossary

For each chapter:
1. Read the chapter's section in `references/chapter-guidance.md` — specifically the done-when checklist and common mistakes. These are your quality gate, not optional reading.
2. Extract relevant content from sources, citing by ID: `[S1: section name]` or `[S2: filename.cs line N]`. Citations must be specific enough to verify — `[S2: code analysis]` is not a citation.
3. Produce the chapter using the markdown skeleton from the guidance as structural template.
4. Apply the "minimum viable version" standard — don't aim for exhaustive, aim for honest.
5. Before saving, run the done-when checklist against your output. If any item FAILS, fix it before proceeding. If it fails because source material doesn't exist, convert to an explicit gap statement.
6. For sections with no source material, write a gap statement:
   > **Gap:** No source material available for this section. To fill: [what specific information or source type is needed].
7. Write the file immediately (incremental save — every chapter is a recovery point)

**Quality enforcement:** The done-when checklist is not advisory. A chapter that fails its checklist has a defect. Fix it or explain why the checklist item is unachievable given available sources (that's a gap statement, not a pass).

### Output structure

Write to the user-specified directory (or derive from context):

```
[output-dir]/arc42/
  arc42.md                              # Index/TOC
  01-introduction-and-goals.md
  02-architecture-constraints.md
  03-system-scope-and-context.md
  04-solution-strategy.md
  05-building-block-view.md
  06-runtime-view.md
  07-deployment-view.md
  08-cross-cutting-concepts.md
  09-architecture-decisions.md
  10-quality-requirements.md
  11-risks-and-technical-debt.md
  12-glossary.md
```

The index file follows the Pitstop exemplar format:
```markdown
# [System Name] - Architecture Documentation (Arc42)

**About this document:** Architecture documentation for [System Name],
following the [Arc42](https://arc42.org/) template.

---

## Table of Contents

1. [Introduction and Goals](01-introduction-and-goals.md)
2. [Architecture Constraints](02-architecture-constraints.md)
3. [System Scope and Context](03-system-scope-and-context.md)
4. [Solution Strategy](04-solution-strategy.md)
5. [Building Block View](05-building-block-view.md)
6. [Runtime View](06-runtime-view.md)
7. [Deployment View](07-deployment-view.md)
8. [Cross-cutting Concepts](08-cross-cutting-concepts.md)
9. [Architecture Decisions](09-architecture-decisions.md)
10. [Quality Requirements](10-quality-requirements.md)
11. [Risks and Technical Debt](11-risks-and-technical-debt.md)
12. [Glossary](12-glossary.md)
```

---

## Phase 3: Cross-Reference Pass

After all chapters are written, run each check explicitly and record PASS/FAIL:

| # | Check | Rule | Result |
| :- | :---- | :--- | :----- |
| 1 | Ch3 → Ch5 | Every external actor/system named in chapter 3 must appear in chapter 5 level 1 (as a neighbor or interface target) | |
| 2 | Ch1 → Ch4 | Every strategy statement in chapter 4 must trace to a specific chapter 1 quality goal or chapter 2 constraint | |
| 3 | Ch5 → Ch6 | Every runtime scenario must use building block names exactly as they appear in chapter 5 (no unnamed participants) | |
| 4 | Ch1 → Ch10 | Every chapter 1 quality goal must have at least one concretizing scenario in chapter 10 with a measurable metric | |
| 5 | Ch9 → Ch4-8 | Each ADR/decision must link to the chapter(s) where it's implemented | |
| 6 | Ch12 | Glossary must cover terms that appear in 3+ chapters. Scan chapter files for repeated domain/architecture terms not yet defined. | |
| 7 | Ch5 → Ch8 | Cross-cutting concepts in chapter 8 must name where they show up (which building blocks, which scenarios) | |

**Execution:** Fill in the Result column with PASS or FAIL + what's broken. Fix FAILs before proceeding to Phase 4. If a fix requires reading additional source material you skipped in Phase 0, go read it — don't paper over with inference.

Write the completed cross-reference table to the output directory as `_cross-reference-check.md`.

---

## Phase 4: Validation

Run the done-when checklist for each produced chapter (from `references/chapter-guidance.md`).

Produce a validation report:

```
VALIDATION REPORT
| Chapter | Title                        | Status |
| :------ | :--------------------------- | :----- |
| Ch 1    | Introduction and Goals       | PASS   |
| Ch 2    | Architecture Constraints     | GAP    |
| Ch 3    | Context and Scope            | PASS   |
| Ch 4    | Solution Strategy            | PASS   |
| Ch 5    | Building Block View          | PASS   |
| Ch 6    | Runtime View                 | FAIL   |
| Ch 7    | Deployment View              | GAP    |
| Ch 8    | Cross-cutting Concepts       | PASS   |
| Ch 9    | Architecture Decisions       | PASS   |
| Ch 10   | Quality Requirements         | PASS   |
| Ch 11   | Risks and Technical Debt     | GAP    |
| Ch 12   | Glossary                     | PASS   |

Coverage: 8/12 chapters with substantive content
Gaps: Ch 2 (no governance docs), Ch 7 (no deployment configs), Ch 11 (no incident data)
```

Status meanings:
- **PASS** — meets done-when checklist
- **FAIL** — has content but doesn't meet checklist (fix it, max 2 retry iterations)
- **GAP** — insufficient source material; gap statements are the correct output
- **NOT OWED** — no concern named in Phase 0a reaches this chapter. A one-line statement of that is
  the correct output, and the twelve-file structure is a default rather than an obligation

---

## Phase 5: Handoff

Present to the user:
1. Output directory path
2. Validation report (coverage summary)
3. Gap inventory with what source material would fill each gap
4. Cross-reference issues found and resolved

## Constraints

- **Extract, don't fabricate.** Every statement traces to a source. If no source supports a claim, it's a gap, not an inference.
- **Inferences are labeled.** When combining evidence from multiple sources, state the reasoning chain and mark as inferred.
- **Gap statements are valuable.** They tell the user exactly what's missing and what would fix it. An arc42 document with honest gaps is more useful than one with plausible hallucinations.
- **Show a specimen.** If the subject produces artifacts, reproduce a real one — in full or in
  excerpt — inside the description. Naming an example file is not showing it. A reader deciding
  whether to adopt something cannot see the thing they would be buying, and no amount of
  description substitutes.
- **A claim sourced only to the subject is not verified.** When the subject asserts a measurement
  about itself, cite where the measurement was made, not where it is repeated. A number carried
  only by the file under description is self-report, and it must be labelled as such — especially
  when it is load-bearing for a central design decision.
- **Source citations inline.** Use `[S1: filename.cs line N]` or `[S3: ADR-0004 section]` format throughout. Citations must be specific enough to verify. `[S2: code analysis]` is NOT acceptable — name the file.
- **Incremental save.** Write each chapter file as it's completed. Every file is a recovery point.
- **Match the exemplar tone.** The Pitstop arc42 docs are practical, concise, and stakeholder-readable. Match that level — not academic, not marketing.
- **Verify claims against code.** When source material (documentation, ADRs, READMEs) claims a behavior exists (e.g., "circuit breaker," "exponential backoff"), verify it by reading the implementing code before restating the claim. Documentation can be aspirational or stale. Code is truth. If documentation claims something the code doesn't implement, flag the discrepancy — don't propagate the claim.

---

## Skill Ecosystem

| Skill | Relationship |
| :---- | :----------- |
| `/systems-analysis` | **Complementary analysis.** Its structural output feeds arc42 chapters 3, 5, 6, 7. |
| `/artifact-review` | **Quality assurance.** Can evaluate arc42 output using documentation and comprehension lenses. |
