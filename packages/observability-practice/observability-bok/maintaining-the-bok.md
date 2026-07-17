# Maintaining the BOK

This guide is for stewards — anyone modifying the BOK's structure: adding or changing Knowledge Areas, Topics, Practice Instruments, or Perspectives. It is not for practitioners contributing content from real work; that's covered by [Contributing](contribute.md).

The distinction matters. A practitioner says *"incidents keep revealing business context gaps — here's evidence for KA05.5."* A steward says *"we need a new perspective for edge IoT."* Both are valid. They require different discipline and touch different parts of the BOK.

---

## Part I — The three-element discipline

The BOK has three peer structural elements:

- **Knowledge Areas (KAs)** — major divisions of the domain that own *distinct knowledge*
- **Practice Instruments** — *concrete tools* practitioners pick up and use
- **Perspectives** — *context lenses* that bend how KAs and Instruments apply in specific platform-type or methodology contexts

Choosing the right element for a candidate is the first and most important structural decision. Getting this wrong means either duplicating content across elements, or fragmenting knowledge that belongs together.

### Disambiguation tests

Use these tests in order. The first "yes" determines the element.

**1. Does this own distinct knowledge that isn't already in another element?**

If yes → **Knowledge Area candidate.** A KA owns conceptual knowledge about a domain division. KA02 Signal Design owns the knowledge of what signals are, how they're classified, how semantic conventions work. That knowledge doesn't live anywhere else.

If no → continue.

**2. Is it a concrete tool, template, assessment, factory, or protocol that produces an artifact or decision?**

If yes → **Practice Instrument candidate.** An instrument has inputs, outputs, and a usage context. IN-04 Service Profile Template has a file format, required fields, validation rules. IN-01 Service Maturity Model has stages, criteria, and an assessment output. Instruments *do* something; KAs *explain* something.

If no → continue.

**3. Does it describe how existing KA knowledge varies in a specific context (platform, methodology, business domain)?**

If yes → **Perspective candidate.** Perspectives point to variations of existing KA knowledge without owning distinct knowledge themselves. The Mainframe perspective says "KA02 Signal Design uses SMF/RMF records here" — it doesn't redefine Signal Design.

If no → the candidate doesn't fit the current structure. Either it's a structural signal (see Part VI — When Structure Needs to Change), or the candidate isn't a BOK element at all.

### Common disambiguation failures

**"Mainframe observability" as a new KA.** Fails Test 1 — the knowledge isn't distinct from KA02 Signal Design, KA05 Incident Response, KA06 Platform & Tooling. Mainframe is a context that bends those KAs, not a parallel body of knowledge. → Perspective.

**"Observability economics" as an instrument.** Fails Test 2 — economics is a knowledge domain, not a tool. Cost-per-signal measurement is a technique within the domain; the domain itself is KA06.6 (a topic within KA06). A concrete cost-tracking template or dashboard pattern would be an instrument. → KA topic, with candidate instruments later.

**"Cloud-native tool landscape" as a KA topic.** Fails Test 3 — this is a variation of KA06.1 (Tool Landscape & Selection), not new knowledge. → Perspective variation under Cloud-Native.

---

## Part II — Content states and state transitions

Every KA topic, instrument, and perspective carries one of three states. The states apply to the element as a whole (for instruments and perspectives) or per topic (for KAs). The state-transition rules are intentional — they prevent drift toward false completeness.

### State definitions

| State | Meaning |
|---|---|
| **Current** | Practitioner-actionable from the page alone. A reader could read the content and act on it without clicking through to other files. |
| **Seeded** | The structure declares the element/topic exists. Cited prior art and/or candidate frame. Content is partial, queued, or under development. |
| **Missing** | The structure declares this should exist. No content drafted yet. Acknowledged absence; not a hidden gap. |

### The "Current" test — critical

Current is not *"a file mentions this topic"* or *"someone has written about this elsewhere."* Current means: **a practitioner can read the page and act**. Test questions:

1. Could a PO / Developer / Platform Engineer read this and do the thing it describes?
2. Does the content stand on its own, or does it require clicking through to decipher?
3. Does it include enough domain specificity to be useful, not just generic framing?

If any answer is no, the state is Seeded, not Current. Stewards who promote content to Current without applying this test create the exact failure mode the content-state discipline exists to prevent — pages that look complete but aren't usable.

### State transitions

| Transition | Trigger | Applied to |
|---|---|---|
| Missing → Seeded | Cited prior art added, or candidate frame drafted | Any topic or element |
| Seeded → Current | Content passes the practitioner test above | Any topic or element |
| Current → Seeded | Content ages and no longer reflects practice; rare but legitimate | Any topic or element |
| Seeded → Missing | The frame turns out not to belong; extremely rare | Any topic or element — usually signals structural change |
| Missing → Current | Direct from Missing to Current is possible but unusual | Requires substantial drafted content without an intermediate frame step |

### Who promotes state

State promotion is a deliberate steward action, not an automatic consequence of editing. Record state in the Content State audit (KA Section 7) or the element's header (instruments, perspectives). Don't promote state in the same commit as content edits — promotion is a separate review decision. This matches the Halvorson content-audit discipline the BOK is built on.

### Pending work lives off-page

A page carries at most its state marking — the header state for instruments and perspectives, Section 7 rows for KAs. It never carries pending-work tracking: gap inventories, "what would make it Current" lists, to-do sections. Tracking lives with whatever workstream owns the pending work. Two failure modes motivate this rule: inline tracking is builder-frame leakage the moment a practitioner reads the page (T4.4), and it goes stale silently because nothing that closes the work touches the page.

### Every page is page one

The BOK ships as pages that arrive alone — deep links, forwarded files, transferred copies. Abbreviations expand at first use on every page, not once per corpus. Product names (CICS, Kubernetes, Grafana) take a category gloss ("transaction monitors", "visualization platforms") rather than an expansion. Pages link the frames they lean on (the four-layer model, KA/IN codes, content states) instead of assuming the reader arrived through the front door.

### Domain Knowledge teaches the practice, not the implementation

KA Section 2 carries general practice knowledge (the BOK's declared scope: a reference pattern, not bespoke to any organization). The authoring organization's own implementation may appear only as a **declared reference implementation** — "in a reference implementation…", "e.g." — and never as unresolvable internal referents: spec numbers, repo paths, program clocks ("Year 1", quarter labels), internal counts presented as fact, or internal system names. Experience-based claims are either grounded in citable practice or owned as the reference implementation's experience — not voiced as "typical" industry knowledge.

---

## Part III — CRUD: Knowledge Areas

### Adding a new KA

A new KA is a significant structural change. Before adding, confirm the candidate passes the distinct-knowledge test AND has at least 3-5 distinct topics to justify its own KA boundary.

**Required artifacts:**

1. **Markdown file** at `observability-bok/kaNN-<slug>.md` following the 7-section page pattern:
   - Section 1: Purpose & Scope
   - Section 2: Domain Knowledge (the substantive content)
   - Section 3: Practices & Processes
   - Section 4: Roles & Responsibilities
   - Section 5: Tools, Artifacts & Techniques (including instruments that operationalize this KA)
   - Section 6: Connected KAs & External References
   - Section 7: Content State & Gaps

2. **YAML entry** in `observability-bok.yaml` under `knowledge_areas:`. Required fields: `id`, `name`, `category` (core-practice / enabling-practice / management-practice), `description`, `question` (the question this KA answers), `topics` (list with id, name, description), `cross_ka` (list of relationships to other KAs with type and description), `boundary_rules` (where ambiguous topics land).

3. **Hub README entry** in the appropriate category section.

4. **mkdocs.yml nav entry** in the appropriate category group. *(`mkdocs.yml` is the site nav config — this and every nav step below apply where your deployment publishes the BOK as a rendered site.)*

5. **Cross-reference updates** in every KA named in the new KA's Section 6. Bidirectional links are mandatory — if KANN says it feeds KA02, KA02's Section 6 must say KANN feeds it.

6. **Perspective KA Variations updates** — for each existing perspective, evaluate whether the new KA has variations under that lens. Add rows to the perspective's KA Variations table where applicable.

### Modifying an existing KA

Routine content changes within a KA (adding a topic, updating domain knowledge, promoting a topic state) don't require steward approval beyond the content-state discipline. Changes to KA boundaries — renaming, splitting, merging — are structural changes (see Part VI).

**When editing an existing KA:**
- If adding a topic: update the YAML topics list, add the Section 2 content, add to Section 7 audit
- If changing cross-references: update the target KA's Section 6 to maintain bidirectionality
- If changing primary owner or category: update the YAML and all references

### Retiring a KA

Extremely rare. A KA retires only when its content is fully subsumed into other KAs or when the domain it represents is no longer relevant. Retirement requires:

- Explicit content migration — every topic in the retired KA moves to a new home
- Redirect notes on the retired KA page (leave the page as a tombstone with pointers)
- YAML marked as superseded (don't delete; set a `superseded_by` field)
- All cross-references updated to the new homes
- Perspective KA Variations updated

---

## Part IV — CRUD: KA Topics

### Adding a topic

Topics are subdivisions within a KA. Adding a topic is a common routine operation and requires:

1. **YAML update** — add to the KA's `topics:` list with `id` (e.g., `KA02.8`), `name`, `description`
2. **Section 2 content** — draft the topic content in the KA's Domain Knowledge section
3. **Section 7 audit entry** — add a row with the topic's state (Seeded, Missing, Current)
4. **Cross-reference check** — if the new topic creates relationships to other KAs, update Section 6

Topic IDs follow `KAnn.m` format where `nn` is the KA number and `m` is the sequential topic number within that KA. Don't renumber existing topics when adding a new one; append.

### Modifying a topic

Routine content improvements don't need special procedure. Ensure:
- Section 2 content and Section 7 audit stay in sync
- If the topic's scope expands beyond its original definition, consider whether it should split into two topics

### Retiring a topic

If a topic no longer represents the domain, retire it:
- Remove from YAML topics list
- Delete content from Section 2
- Section 7 audit row gets a final row noting retirement (or delete the row)
- Check instruments and perspectives that referenced this topic — update their cross-references

---

## Part V — CRUD: Practice Instruments

### Adding an instrument

An instrument is a concrete tool. Before adding, confirm it passes the concrete-tool test: does it produce an artifact or decision? Does it have identifiable inputs and outputs?

**Instrument types (pick one):**
- **Assessment** — measures where something is (IN-01 Service Maturity Model)
- **Definition** — captures specification (IN-04 Service Profile Template)
- **Production** — generates artifacts (IN-10 Story Factory)
- **Adoption** — onboards teams (IN-16 Onboarding Simulation)
- **Communication** — stakeholder visibility (IN-20 Portfolio Maturity View)

If the candidate doesn't fit one of these types, either the candidate isn't an instrument, or the type taxonomy needs a new type (which is a structural change — see Part VI).

**Required artifacts:**

1. **Markdown file** at `observability-bok/instruments/in-NN-<slug>.md` following the pattern:
   - Header: Type (one of the five), Lifecycle position
   - Purpose
   - Inputs
   - Outputs
   - KA Cross-References (which KAs the instrument draws from)
   - Usage Context (when to reach for this instrument)
   - Related Instruments

2. **YAML entry** in `observability-bok.yaml` under `practice_instruments:`. Required fields: `id`, `name`, `type`, `description`, `ka_refs` (list of KAs this instrument draws from).

3. **Instruments catalog README entry** in the appropriate type section.

4. **KA Section 5 updates** — for every KA listed in `ka_refs`, add a row to that KA's Section 5 Practice Instruments table. Bidirectional linking is mandatory.

5. **mkdocs.yml nav entry.**

6. **Related Instruments updates** — if the new instrument is related to existing instruments, update their Related Instruments sections.

**Definition-type instruments: the page IS the reference surface.** The catalog promises "what do I fill out?" and the Current test requires that a practitioner can read the page and act — so a Definition instrument page carries the canonical field set on-page, rendered from the authoritative source, not a pointer to a template the reader can't reach. When the source fields change, the page is stale until re-rendered; the content-state discipline applies.

### Modifying an instrument

Common modifications: refining inputs/outputs, updating usage context, changing KA references.

**When KA references change:**
- Update the YAML `ka_refs`
- Add the instrument row to newly-related KAs' Section 5
- Remove the instrument row from KAs no longer related

### Retiring an instrument

An instrument retires when it's absorbed into another instrument or superseded:
- Mark the YAML entry with `superseded_by` or `retired: true`
- Remove from catalog README
- Remove from all KA Section 5 tables
- Leave a tombstone page with redirect note
- Update Related Instruments in adjacent instruments

---

## Part VI — CRUD: Perspectives

### Adding a perspective

A new perspective is justified when a real-world question reveals that KA knowledge varies meaningfully in a specific context, and that variation isn't captured by any existing perspective.

**Test checklist before adding:**

1. Does this describe variation of existing KAs, not new knowledge? (If new knowledge → probably a KA.)
2. Will the KA Variations table meaningfully differ from any existing perspective's? (If not → fold into existing perspective.)
3. Is the context stable enough to be a perspective, or is it transient? (Transient contexts may belong as sub-variations within a parent perspective — e.g., "Mainframe-to-cloud migration" is a transient variation of Hybrid, not its own perspective.)

**Required artifacts:**

1. **Markdown file** at `observability-bok/perspectives/<slug>.md` following the pattern:
   - Header: State (Seeded at creation; promoted to Current later)
   - What distinguishes this perspective
   - KA Variations (table: KA | Variation)
   - Known gaps in this perspective
   - External references
   - "Why it matters" — a short closing coda naming what breaks if this perspective is ignored (part of the template; every page is some reader's first page)

2. **Perspectives catalog README entry** — add to the catalog table with state.

3. **Hub README entry** in the Perspectives section.

4. **Start Here routing** — if the perspective is reader-navigable at top level (most are), add no new row but ensure the "Find platform-type-specific guidance" row routes to the perspectives catalog.

5. **mkdocs.yml nav entry** under the Perspectives group.

6. **KA Variations population** — identify which KAs vary under this perspective and draft the variation descriptions. This is the substantive content of the perspective page; it cannot be empty at creation.

### Modifying a perspective

Perspectives evolve as real practice accumulates. Common modifications:
- Adding a KA variation when a new pattern emerges
- Promoting from Seeded to Current when the KA Variations table is substantively populated across all relevant KAs
- Updating external references as the field matures

### Retiring a perspective

A perspective retires when:
- Its context is no longer relevant (e.g., a technology category disappears)
- Its content has been absorbed into another perspective (e.g., "container-on-mainframe" might merge into Mainframe)

Retirement procedure matches KA retirement: tombstone page, YAML flag, catalog update, remove from hub and nav.

### Perspective proliferation — a warning

If the BOK has more than ~7 perspectives, the structure may need review. Candidate issues:
- Some perspectives are composable lenses rather than peer contexts (e.g., "Regulated Industry" could be a secondary lens layered onto any platform perspective, not a peer)
- Some perspectives represent the same variation pattern at different granularity
- The KA Variations tables are becoming repetitive across perspectives — suggesting the variation belongs in the KA itself, not scattered across perspectives

Perspective proliferation is a structural signal. See Part VII.

---

## Part VII — Cross-reference discipline

The BOK's structural integrity depends on bidirectional linking. Every change that creates or breaks a relationship between elements must update both sides.

### The integration points checklist

When any element changes, the steward must verify updates to every surface the element touches:

**Add/modify a KA:**
- [ ] YAML `knowledge_areas` entry
- [ ] Markdown file (7-section pattern)
- [ ] Hub README category section
- [ ] mkdocs.yml nav
- [ ] Every adjacent KA's Section 6 (cross-references)
- [ ] Every perspective's KA Variations (check if new KA has variations)
- [ ] Every instrument whose KA refs include this KA (check Section 5 back-reference)
- [ ] **Meta-page review** (Part XI) — at minimum how-the-bok-is-organized, questions-the-bok-answers, about

**Add/modify a KA topic:**
- [ ] YAML topics list
- [ ] KA Section 2 (Domain Knowledge)
- [ ] KA Section 7 (Content State audit)
- [ ] Adjacent KAs' Section 6 (if topic creates new relationships)
- [ ] **Meta-page review** (Part XI) — check questions-the-bok-answers if the topic adds a new question the BOK now answers

**Add/modify an instrument:**
- [ ] YAML `practice_instruments` entry
- [ ] Markdown file
- [ ] Instruments catalog README
- [ ] Every KA in `ka_refs` — Section 5 entry
- [ ] mkdocs.yml nav
- [ ] Related Instruments in adjacent instruments
- [ ] **Meta-page review** (Part XI) — check instrument-type counts in any meta that cites them

**Add/modify a perspective:**
- [ ] Markdown file
- [ ] YAML `perspectives` entry
- [ ] Perspectives catalog README
- [ ] Hub README Perspectives section
- [ ] mkdocs.yml nav
- [ ] KA Variations table populated (per KA referenced)
- [ ] About.md prior-art table (if introducing a new structural pattern)
- [ ] **Meta-page review** (Part XI) — at minimum how-the-bok-is-organized, questions-the-bok-answers, about

### Bidirectional linking test

For any cross-reference, verify both directions exist:

- KA01 Section 6 says "KA01 feeds KA02" → KA02 Section 6 must say "KA02 depends on KA01"
- KA02 Section 5 lists IN-05 → IN-05 KA Cross-References must list KA02
- Mainframe perspective KA Variations table has a KA05 row → optional reciprocal (KA05 doesn't need to list every perspective; perspectives point into KAs, KAs don't need to point out)

The one asymmetry: KAs don't list perspectives back. Perspectives are lenses *onto* KAs; the KA doesn't need to know which perspectives exist. This keeps KAs perspective-invariant, which is the whole point.

---

## Part VIII — When structure itself needs to change

The taxonomy is an opinion. It can be revised. The question is when.

### Structural signals to watch

**A KA with persistent boundary confusion.** If contributions repeatedly get filed in KA X when they should be in KA Y, the boundary description isn't doing its job. Either rewrite the boundary rules, or the KAs need to merge/split.

**A topic that never moves from Seeded to Current.** If multiple sessions touch a Seeded topic but nothing promotes, the topic may not be real — or the Current criteria are too strict — or the topic belongs somewhere else entirely.

**A KA with <3 Current topics.** Might indicate the KA is premature — not yet substantiated by practice. Or the KA is a placeholder for future work (legitimate, as long as content states are honest).

**An instrument that touches 8+ KAs.** The instrument may be too broad — really multiple instruments masquerading as one. Or the KA boundaries are too fine-grained.

**Perspective proliferation beyond ~7.** Some of the perspectives may be composable lenses rather than peer contexts.

**Real practitioner vocabulary doesn't match KA names.** If people in the field consistently use different terms for the concepts the KAs describe, the naming may need revision. Vocabulary drift is a signal; fight it with renaming, not with insistence that practitioners should use the BOK's terms.

**KA Variations tables in perspectives duplicate across multiple perspectives.** If three perspectives all say the same thing about KA X, the content belongs in KA X, not scattered across perspectives.

### Process for structural change

1. **Document the pattern evidence.** What specific contributions, questions, or failed navigations expose the structural problem? Concrete examples, not vague concerns.

2. **Propose the change explicitly.** New element? Renamed element? Merged elements? Moved content? State the change as a specific set of before/after edits.

3. **Validate against the disambiguation tests.** A proposed new KA must pass the distinct-knowledge test. A proposed new perspective must pass the lens-not-knowledge test. If the proposal fails the test, the answer is usually to refine the proposal, not override the test.

4. **Execute the change atomically.** Update all affected pages and the YAML in one change, not spread across multiple sessions. Structural change spread out becomes structural drift.

5. **Update this guide.** If the change reveals a rule the guide didn't cover, add the rule. The guide evolves with the BOK.

### What structural change looks like in practice

Examples of legitimate structural moves that have happened or might happen:

- **Adding the Perspectives structural element.** Originally the BOK had KAs and Instruments. A real-world question (platform-type variation) couldn't be answered by either. Perspectives was added with BABOK v3 Perspectives Chapter as prior art.
- **Splitting a KA.** If KA10 Stakeholder Engagement grows so large it fragments naturally into two bodies of knowledge (say, Stakeholder Engagement + Communication), the split is legitimate once the boundary is clean.
- **Merging topics.** If KA02.3 (Instrumentation Strategy) and KA02.4 (Signal Hierarchy) turn out to always be discussed together with no distinct content, merge them.
- **Introducing a new instrument type.** The current five types (Assessment, Definition, Production, Adoption, Communication) cover 23 instruments. A future instrument that doesn't fit would be a signal — either the instrument isn't really an instrument, or the type taxonomy needs expansion.

### What structural change is NOT

- **Renaming a KA to match a trend.** "Observability" vs. "Observability 2.0" naming debates are vocabulary churn. Rename only when the practitioner vocabulary has genuinely shifted.
- **Adding a KA because a stakeholder asked for one.** Stakeholder requests are input, not authority. The disambiguation tests decide whether the request creates a new KA, a new topic within an existing KA, a new perspective, or nothing structural.
- **Splitting a KA to make it look smaller.** KAs aren't a page-size problem. A big KA with many Current topics is more useful than two small KAs with the same content split arbitrarily.

---

## Part IX — What this guide is and isn't

**This guide IS:**
- The rulebook for stewards making structural changes
- The disambiguation authority when element-type questions arise
- The integration-points checklist for every element change
- The structural-change process, including what signals to watch

**This guide is NOT:**
- A content style guide (that lives in how each KA writes its Domain Knowledge)
- A contributor's handbook (that's [contribute.md](contribute.md), practitioner-facing)
- The methodology itself (that's [the-methodology.md](the-methodology.md))
- A description of how the BOK is organized (that's [how-the-bok-is-organized.md](how-the-bok-is-organized.md))

**When to update this guide:**
- A structural change reveals a rule this guide didn't cover → add the rule
- A disambiguation test produces a counterintuitive outcome → document the edge case
- A cross-reference discipline gap causes drift → add the missing integration point to Part VII
- A new element type is introduced (rare) → add a CRUD section for it

**When to consult this guide:**
- Before adding a KA, Topic, Instrument, or Perspective — confirm it passes the disambiguation tests and you've identified every integration point
- Before promoting a content state — confirm the practitioner test holds
- When something doesn't fit — see if it's a structural signal (Part VIII) or just in the wrong element
- When proposing a structural change — follow the process in Part VIII

---

## Part X — Tests

This Part defines the test suite an AI agent (or human steward) can run against the BOK to verify it is maintaining its legitimate reasoning and usefulness. Tests are organized by what they verify. Each test has a description, an execution procedure, pass criteria, and remediation when the test fails.

Tests are categorized by execution type:
- **Scriptable** — can be run mechanically (grep, YAML parsing, file existence checks)
- **Judgment** — require reading content and applying criteria; an AI agent can perform these but the outcome is not a simple string match
- **Sampled** — verify the BOK can answer representative real-world questions; require working through specific cases

Tests should be run whenever the BOK is modified structurally, periodically even without changes (drift detection), and before any external sharing of the BOK as a draft.

### Test category 1 — Structural integrity

These verify the BOK's internal consistency. All are scriptable.

**T1.1 — File / YAML correspondence for KAs**
- **Check:** Every KA defined in `observability-bok.yaml` under `knowledge_areas:` has a corresponding markdown file at `observability-bok/kaNN-<slug>.md`. Every `ka*.md` file has a YAML entry.
- **Procedure:** List KA IDs from YAML. List KA files by glob. Compare sets for symmetric difference.
- **Pass:** Sets are equal.
- **Fail remediation:** Add the missing file or YAML entry, or document the intentional asymmetry (extremely rare — tombstone pages for retired KAs).

**T1.2 — File / YAML correspondence for Instruments**
- **Check:** Every instrument in YAML has a markdown file at `instruments/in-NN-<slug>.md`; every `in-*.md` has a YAML entry.
- **Procedure:** Same as T1.1 for instruments.
- **Pass/Fail:** Same as T1.1.

**T1.3 — Bidirectional KA cross-references**
- **Check:** Every `cross_ka` relationship in the YAML has a matching reverse declaration. If KA01 declares `feeds` KA02, KA02 must declare `depends_on` or equivalent reverse from KA01.
- **Procedure:** For each `cross_ka` edge in YAML, find the target KA's `cross_ka` list and verify a reverse relationship exists. Cross-check against the markdown Section 6 content.
- **Pass:** Every forward relationship has a semantic reverse.
- **Fail remediation:** Add the missing reverse. The relationship-type vocabulary in the YAML defines valid pairs (feeds / depends_on, governs / governed_by, etc.).

**T1.4 — Bidirectional KA ↔ Instrument references**
- **Check:** For every instrument, its `ka_refs` list is mirrored by that instrument appearing in each referenced KA's Section 5 table. Conversely, every Section 5 instrument reference corresponds to the KA appearing in that instrument's KA Cross-References.
- **Procedure:** For each instrument, parse `ka_refs` from YAML. Read each referenced KA's markdown Section 5 and verify the instrument is listed. Reverse-check by reading each KA's Section 5 and verifying each listed instrument has the KA in its Cross-References.
- **Pass:** Complete bidirectional coverage.
- **Fail remediation:** Add the missing row to Section 5 or the missing KA to the instrument's Cross-References.

**T1.5 — Topic audit completeness**
- **Check:** Every topic in a KA's YAML `topics:` list appears in that KA's Section 2 (Domain Knowledge) as a subsection AND in Section 7 (Content State audit) as a row.
- **Procedure:** For each KA, parse YAML topics. Grep KA markdown for each topic name appearing as a heading and a Section 7 row.
- **Pass:** Every topic present in all three locations (YAML, Section 2, Section 7).
- **Fail remediation:** Add the missing entry. If a YAML topic isn't ready for Section 2 content, it should still have a Section 7 row marked Missing or Seeded.

**T1.6 — Content state value discipline**
- **Check:** Every state marking uses one of the canonical values: Current, Seeded, Missing. No other values permitted.
- **Procedure:** Grep all KA pages, instrument pages, and perspective pages for state markings (pattern: `**Current**`, `**Seeded**`, `**Missing**`, and the field `state:` in YAML). Flag any other values (e.g., "Needs Fix", "Partial", "Draft").
- **Pass:** All state values are canonical.
- **Fail remediation:** Reconcile the non-canonical state to one of the three. "Needs Fix" is not a state — it describes the current Current content that needs revision; should stay Current but with a remediation note.

**T1.7 — mkdocs nav correspondence** *(applies only where the deployment publishes the BOK as a rendered site with `mkdocs.yml`)*
- **Check:** Every nav entry in `mkdocs.yml` points to an existing file. Every markdown file in the BOK tree is reachable from the nav (no orphan pages).
- **Procedure:** Parse `mkdocs.yml` nav. For each entry, confirm the file exists. For each `.md` file in the BOK tree, confirm it's referenced in the nav.
- **Pass:** Bidirectional coverage.
- **Fail remediation:** Add the missing nav entry or remove the orphan file. Documentation tombstones (retired elements) should stay in the nav until their successor absorbs all inbound references.

**T1.8 — Perspective KA reference validity**
- **Check:** Every KA ID referenced in a perspective's KA Variations table corresponds to a real KA.
- **Procedure:** For each perspective, parse the KA Variations table and verify each referenced KA ID exists in the YAML `knowledge_areas`.
- **Pass:** Every reference is valid.
- **Fail remediation:** Fix the typo or update the perspective to reference the current KA ID.

### Test category 2 — Discipline adherence

These verify the disambiguation rules and state criteria from Parts I-II are being upheld. They require reading and applying criteria.

**T2.1 — Practitioner test for Current topics**
- **Check:** Every topic marked Current in Section 7 passes the practitioner test: a reader can read Section 2 content for that topic and act on it without clicking through to external files.
- **Procedure:** For each Current topic, read the Section 2 content. Apply three questions: (1) Could a practitioner (PO, Dev, Platform) act on this? (2) Is the content substantive, or mostly pointers? (3) Does it include domain specificity — concrete fields, decision criteria, process steps — or just generic framing?
- **Pass:** All three questions answerable Yes.
- **Fail remediation:** Either promote the content to substantive (filling in the specifics) or demote the state to Seeded with an honest Section 7 note.

**T2.2 — Instrument concreteness**
- **Check:** Every instrument page has substantive Inputs, Outputs, and Usage Context sections. An instrument without concrete inputs and outputs isn't an instrument — it's a KA topic or a perspective.
- **Procedure:** For each instrument, verify the presence and substance of three sections: Inputs (specific data required), Outputs (specific artifacts produced or decisions made), Usage Context (when to reach for this).
- **Pass:** All three sections are substantive, not placeholder.
- **Fail remediation:** Either fill in the missing specifics, or reconsider whether this is really an instrument (Part I disambiguation test).

**T2.3 — Perspective as lens, not knowledge**
- **Check:** Every perspective page contains variation-of-existing-KA content, not distinct knowledge. A perspective must point into KAs; it must not redefine concepts.
- **Procedure:** For each perspective, read the page. Verify: (1) the "What distinguishes this perspective" section describes contextual distinctiveness without introducing new concepts; (2) the KA Variations table points to existing KAs and describes how techniques vary under this lens; (3) no section of the perspective defines concepts that belong in a KA (e.g., explaining what an SLO is).
- **Pass:** Perspective content is variation, not invention.
- **Fail remediation:** Either move the invented content to the appropriate KA, or elevate the candidate from perspective to KA (rare — requires passing the distinct-knowledge test from Part I).

**T2.4 — KA size balance**
- **Check:** No KA has fewer than 3 topics marked Current. Premature KAs signal either over-eager structural creation or a KA that should merge with another.
- **Procedure:** For each KA, count topics with state Current. Flag any KA with fewer than 3.
- **Pass:** Every KA has ≥3 Current topics, OR the KA has been explicitly flagged as developmental with Section 7 notes explaining the maturity trajectory.
- **Fail remediation:** Either promote Seeded topics to Current (if the content warrants), merge the KA with an adjacent one, or accept the KA as developmental with honest notes.

**T2.5 — Instrument type coverage**
- **Check:** Every instrument belongs to exactly one of the five canonical types: Assessment, Definition, Production, Adoption, Communication.
- **Procedure:** Parse instrument YAML for `type` field. Verify value is one of the five.
- **Pass:** All instruments typed canonically.
- **Fail remediation:** Reconcile the type. If a new type seems legitimately required, this is a structural change — see Part VIII.

### Test category 3 — Paradigm integrity

These verify the BOK is anchored to its methodology and hasn't drifted into generic observability content.

**T3.1 — Methodology anchor present**
- **Check:** `the-methodology.md` exists and explicitly names the business-context-first paradigm.
- **Procedure:** Read `the-methodology.md`. Verify it contains the phrase "business-context-first" or equivalent (e.g., "business health first," "stakeholder expectations first as primary frame"). Verify it explicitly distinguishes itself from telemetry-first observability.
- **Pass:** Paradigm is named, claimed, and contrasted with the alternative.
- **Fail remediation:** Restore the paradigm claim. This is the single most load-bearing file in the BOK; if it drifts, the BOK drifts.

**T3.2 — Four-layer model consistency**
- **Check:** Every reference to signal layers uses the canonical names (System, Application, Business Health, Business Impact). "Application" replaced "Process" as the layer name; "Process" as a layer name is retired. The L1/L2/L3/L4 numbering shorthand is retired — it implies an inside-out order and collides with product-hierarchy notations. No alternate taxonomies. **One conditional stratum is legitimate:** **Agent Workflow** (provisional name) — valid ONLY when presented as conditional (activates per service, for agentic steps) and provisional-marked. Agent Workflow rendered as an unconditional fifth layer, any other fifth-layer name, or the Agent Decision dimensions presented as industry-canonical — all fail.
- **Procedure:** Grep KA pages and perspectives for signal classification language. Flag any classification that uses non-canonical names (e.g., "Infra / App / Business" would fail — it doesn't match the four-layer names). Grep for "Agent Workflow" and verify each occurrence carries the conditional framing and a provisional marker (in prose or via link to KA02's taxonomy status note).
- **Pass:** Consistent terminology across all KAs; every Agent Workflow mention conditional and provisional-marked.
- **Fail remediation:** Reconcile to the canonical full names. The L1-L4 numbering shorthand is retired — use names only. Unmarked Agent Workflow mentions get the conditional/provisional framing restored from the four-layer model canon.

**T3.3 — Semantic chain visibility**
- **Check:** The semantic chain — stakeholder → expectation → **Business Health signal** (supported by Process/System signals) → *on breach* → **Business Impact signal** → alert → owner + next action — appears in: (a) `the-methodology.md` (its Semantic Chain section is the canonical rendering this check quotes), (b) KA01 Section 2 as foundation, (c) referenced by at least KA02, KA04, KA05 (the KAs that consume its outputs).
- **Procedure:** Grep target pages for the chain in recognizable form.
- **Pass:** Chain visible at all required locations, in the canonical form (impact *after* the health signal, conditional on breach — a rendering that puts qualitative impact before the signal is the older design-time flow, not this chain).
- **Fail remediation:** Restore the chain in the canonical form. Like T3.1, this is load-bearing.

**T3.4 — Paradigm distinction stated**
- **Check:** The BOK explicitly positions itself against the alternative paradigm — **telemetry-first** observability — somewhere accessible: either in `the-methodology.md`, `about.md`, or both. Silent smuggling fails. (SRE/SLO practice is NOT the opposing paradigm — canon states it is compatible and upstream-consumed; a steward must never add anti-SRE positioning to satisfy this check. T5.3 carries the correct SRE stance.)
- **Procedure:** Grep `the-methodology.md` and `about.md` for explicit paradigm contrast with telemetry-first practice.
- **Pass:** Contrast is stated.
- **Fail remediation:** Add the explicit telemetry-first comparison.

**T3.5 — Prior-art citation completeness**
- **Check:** Every structural element (KA taxonomy pattern, 7-section page pattern, Practice Instruments Catalog, Perspectives, three-category KA split, lifecycle spine, content-state discipline) has a named source in `about.md`'s prior-art table.
- **Procedure:** Read `about.md` prior-art table. Verify each of the structural elements above is named with a source.
- **Pass:** Every element cited.
- **Fail remediation:** Add the missing citation. If a structural element doesn't have prior art, it was invented — and the BOK's core discipline forbids invented structure. Either find the prior art or reconsider the structural element.

### Test category 4 — Drift detection

These detect regression toward known failure modes. All are scriptable grep patterns.

**T4.1 — Repo path leakage**
- **Check:** No markdown file in the BOK references source-repo-internal paths of any shape. The test needs no list: any relative path pointing outside the BOK tree fails.
- **Procedure:** Run a mechanical validation script (see Automation scope below), or grep the BOK tree for path *shapes*, not a fixed list. An enumerated list goes stale: grepping for path shapes catches a real leak that an enumerated list would miss.
- **Pass:** Zero matches.
- **Fail remediation:** Replace the path reference with either inlined content or a generic capability description. See Part VIII patterns.

**T4.2 — Internal stakeholder leakage**
- **Check:** No content references specific internal individuals by name.
- **Procedure:** Scan the BOK tree for personal names. Instance-vs-category: any term naming a particular person fails; a role or category ("a senior leader," "a champion") passes. No name list exists or should — a forbidden-name list that enumerates the names defeats itself.
- **Pass:** Zero matches.
- **Fail remediation:** Genericize the reference (e.g., "a senior leader" or "a champion") or remove it.

**T4.3 — Meeting and date leakage**
- **Check:** No content references specific internal meetings, forums, or dates. Instance-vs-category: a named forum or a month-plus-day date fails; "a recurring architecture forum" passes.
- **Procedure:** Grep for date shapes ("the [date] meeting" and month-plus-day patterns); read for named forums.
- **Pass:** Zero matches.
- **Fail remediation:** Remove the temporal reference. The BOK is ahistorical; meeting-date references belong in session notes, not the BOK itself.

**T4.4 — Builder-frame leakage**
- **Check:** No content contains inline builder-frame language: "**Content gap:**", "What Would Make It Current", "What Exists Today", "Needs authoring", "No repo content exists", "exists implicitly", "the concept is defined within..."
- **Procedure:** Grep for these patterns.
- **Pass:** Zero matches (outside the Maintaining the BOK guide itself, which legitimately references some of these).
- **Fail remediation:** Rewrite the content as substantive knowledge or delete it. Content-state markings belong in Section 7 audits, not inline in Domain Knowledge.

**T4.5 — Enterprise-specific leakage**
- **Check:** No content references any specific enterprise by name, abbreviation, or internal program/framework/forum acronym. Instance-vs-category: a term naming a particular organization or its internal program fails; the category it belongs to passes ("enterprise service hierarchy frameworks" is acceptable; a named internal framework is not).
- **Procedure:** Read for proper nouns and unexpanded acronyms. The acid test: would the term mean anything in a different enterprise? If not, it is an instance and fails.
- **Pass:** Zero specific-instance references.
- **Fail remediation:** Genericize. See Part VIII failure patterns.

**T4.6 — Session / AI-agent self-reference**
- **Check:** No content refers to "this session", the maintaining agent by name, "AI session", "future sessions", or first-person authorial voice. The BOK is not written by the agent for the agent; it's a practitioner resource.
- **Procedure:** Grep for these patterns, plus whatever the maintaining agent is called in this environment.
- **Pass:** Zero matches in practitioner-facing content. Maintenance guides and AI-first YAML commentary are legitimate exceptions. Design notes about the structure's machine-readability are also legitimate when phrased as a property of the artifact ("the dependency structure can be traversed programmatically"), not as AI actors ("AI sessions walk the dependencies").
- **Fail remediation:** Rewrite in third person as domain content. The BOK speaks about the observability domain; it doesn't speak about itself as an AI artifact.

### Test category 5 — Usefulness validation

These verify the BOK can answer real-world questions. Each test names a representative question, the expected route, and the expected substance of the answer. These are sampled — they don't exhaustively cover the question space but probe representative corners.

**T5.1 — "How do we measure business impact?"**
- **Expected route:** KA01.4 (Impact Category Classification) and `the-methodology.md` (Four-Layer Model, Business Impact).
- **Expected substance:** Names the four impact categories (customer_experience, financial, legal_risk, operational). References Business Impact as the quantification layer. Includes concrete fields or metrics.
- **Pass:** Both pages reachable from relevant entry points; answer substantive.
- **Fail remediation:** Restore or expand the content. A BOK that can't answer its most foundational question has lost its purpose.

**T5.2 — "How do we observe a mainframe batch job?"**
- **Expected route:** Mainframe perspective → KA02 Signal Design (via variation), KA04 Monitoring (batch-window dashboard patterns), KA05 Incident Response (checkpoint/restart playbooks).
- **Expected substance:** Names SMF/RMF records as signal sources, batch-window monitoring as the rhythm, checkpoint/restart as the recovery pattern. KA02 variation under Mainframe is substantive.
- **Pass:** Mainframe perspective page exists; KA Variations table has rows for at least KA02, KA04, KA05 with specific content.
- **Fail remediation:** Populate the Mainframe perspective. If the perspective is Seeded at the content level, that's honest state — don't fake Current.

**T5.3 — "Where do SLOs fit?"**
- **Expected route:** KA01.6 (SLO Definition & Error Budget) and `the-methodology.md` (SLOs as quantified stakeholder expectations).
- **Expected substance:** SLOs positioned as Business Health signals — quantified stakeholder expectations. Error budgets as reliability-velocity tradeoff within business context. Relationship to SRE explicitly named.
- **Pass:** KA01.6 is Current. Methodology page explicitly positions SLOs.
- **Fail remediation:** Restore the SLO framing. SLOs are a paradigm-test topic — how the BOK treats SLOs reveals whether the business-context-first paradigm is intact.

**T5.4 — "How do we handle observability cost?"**
- **Expected route:** KA06.6 (Observability Economics & Cost Optimization).
- **Expected substance:** Names FinOps Foundation patterns. Cost-per-signal concept. Retention tiering by impact category. Sampling policies tied to signal type.
- **Pass:** KA06.6 content substantive.
- **Fail remediation:** Restore or expand the content.

**T5.5 — "What's the difference between monitoring and observability?"**
- **Expected route:** `the-methodology.md` or KA01 Section 1.
- **Expected substance:** Monitoring tells you what broke; observability lets you ask why. Business observability adds: what matters, to whom, with what consequence.
- **Pass:** Answerable from the methodology or entry-point pages.
- **Fail remediation:** Add the distinction at the methodology page if missing.

**T5.6 — "How does the BOK treat [platform type]?"**
- **Expected route:** Perspectives catalog → specific perspective.
- **Expected substance:** A perspective page exists for the platform type (cloud-native, mainframe, hybrid, SaaS). If the platform type isn't covered, the BOK honestly reports that — no perspective exists for "edge IoT" or "HPC" yet, and the structure explains how such a perspective would be added.
- **Pass:** Existing perspectives reachable; missing perspectives acknowledged honestly.
- **Fail remediation:** Either add the perspective (if work has accumulated) or ensure the Perspectives catalog README describes the honest scope — which platform types are covered and which are not.

### Test category 6 — Traversal validation

These verify the BOK's primary value claim: not classification, but traversal — walking dependencies with content-state awareness at each stop.

**T6.1 — Dependency walk from a leaf topic**
- **Check:** Starting from any leaf topic (a specific KA topic or instrument), traverse upstream through cross-references. At each stop, content state is visible.
- **Procedure:** Pick a topic (e.g., KA04.3 Cross-Signal Correlation). Read the KA04 Section 6 cross-references. Follow the "depends on" relationship to KA02. Read KA02 Section 6 → follow to KA01. Read KA01. At each stop, check Section 7 for content state.
- **Pass:** The walk is possible (cross-references lead somewhere valid) and state is visible at each stop.
- **Fail remediation:** Fix broken cross-references (T1.3). Add state markings if missing (T1.5).

**T6.2 — Investigative traversal: "We need better correlation capabilities"**
- **Check:** Given a practitioner question like this, can an AI session walk it through the BOK?
- **Expected walk:** KA04.3 (Cross-Signal Correlation) is the primary home. Section 7 shows the topic as Seeded. Cross-references trace to KA02 (Signal Design must enable correlation) and KA06 (platform tooling must support it). Content state on the walk reveals where the chain is solid vs. thin. Conclusion: investing in correlation tools without addressing signal design (KA02) may underperform.
- **Pass:** The walk can be performed and the conclusion is supported by visible evidence in the BOK.
- **Fail remediation:** If the walk breaks (missing cross-reference, orphan topic, no state visible), fix the specific gap. This is the BOK's flagship use case — if it can't perform traversal, it's reduced to classification.

**T6.3 — Perspective-aware traversal**
- **Check:** Given a question with platform context ("how do we correlate signals in a hybrid environment?"), the traversal combines KA content with perspective variations.
- **Expected walk:** Enter through Hybrid perspective → see KA04.3 named as a variation → read KA04.3 general content → read Hybrid variation for KA04 (metadata parity, the seam problem) → traverse to KA07 Integration (the "seam" is an integration problem).
- **Pass:** Traversal combines KAs and perspectives coherently.
- **Fail remediation:** Populate perspective KA Variations tables if sparse. Verify Perspectives catalog is reachable from relevant entry points.

### Running the test suite

**Frequency:**
- After any structural change (new KA, topic, instrument, or perspective): run Categories 1, 2, 3, 4.
- Before any external sharing (draft distribution, stakeholder review): run all six categories.
- Periodically (monthly or quarterly) without structural changes: run Category 4 (drift detection) and Category 5 (usefulness).
- On demand when a practitioner reports the BOK "doesn't cover" something: run Category 5 and 6 for the relevant topic.

**Interpreting results:**
- **Category 1 failures** are defects — fix immediately. Structural incoherence compounds fast.
- **Category 2 failures** indicate discipline drift — may require state demotion or restructuring.
- **Category 3 failures** are paradigm drift — the most serious kind. Escalate before making content edits.
- **Category 4 failures** are leakage — clean up immediately. Leakage is visible to external readers.
- **Category 5 failures** indicate content sparsity — may be honest (Seeded state) or may reveal a missing KA topic or perspective.
- **Category 6 failures** reveal traversal breakage — either cross-reference gaps or missing content on the walk. The BOK's flagship use case.

**Reporting format:**
For each test executed, report: test ID, status (Pass / Fail / N/A), evidence (specific files/locations), remediation action if Fail. Aggregate into a summary: X tests passed, Y tests failed, Z tests skipped with reason.

**Automation scope:**
Categories 1, 4 can be fully scripted (shell + YAML parsing + grep). Categories 2, 3 require an AI agent reading content. Categories 5, 6 are best performed by an AI agent executing the walk and reporting findings.

A mechanical validation pass is worth scripting in any deployment: Categories 1 and 4, the Part XI count checks, an identifier-resolvability check (every backticked file reference must resolve inside the BOK tree), and instrument state correspondence (page header vs. YAML registry) are all mechanically checkable. Such a script should exit nonzero on any finding and can also emit report-only warnings (e.g., Section 6 rows without matching YAML edges); run it after any structural change and before any external sharing. T4.2 stays manual — the instance-vs-category judgment cannot be scripted without enumerating names, which would defeat itself.

A second pass worth scripting enforces the *Every page is page one* linking convention (Part II): pages must link the frames they lean on, not leave bare codes that force manual navigation. Such a link pass wraps bare `KAnn` / `KAnn.m` / `IN-nn` codes and meta-page names as markdown links — to the topic's exact heading anchor (generated with the site's own slugify and verified to exist on the target page) or the page top as fallback — skipping tokens already inside a link or code span, so runs are idempotent. Run it after content edits to relink new references, and run a check mode in the same cadence as the mechanical pass, exiting nonzero if any bare linkable reference has crept back in. It should skip this guide, which names codes as instructional examples. Without this guard the corpus drifts back to bare codes on every edit — the reason the convention needed mechanical enforcement, not just a stated rule.

---

## Part XI — Meta-page discipline

The BOK includes pages that describe *what the BOK is*, distinct from pages that describe *observability as a domain*. These are **meta pages** — the BOK's self-description. Their accuracy depends on the BOK's structure staying synchronized with how the BOK describes itself. Without explicit discipline, meta pages drift: "13 KAs" in prose becomes false when the fourteenth is added; "three peer structural elements" becomes false when a fourth appears; a perspective count cited in one meta page contradicts reality in another. Over time, the BOK lies about itself.

This Part establishes the meta set, the review triggers, and the holistic review protocol.

### The meta set

Meta pages, in navigation order:

| Page | Role |
|---|---|
| `start-here.md` | Routing — first orientation for any reader |
| `the-methodology.md` | The methodology itself (business observability paradigm) |
| `questions-the-bok-answers.md` | Usefulness claim at full scope, plus explicit scope boundaries |
| `how-the-bok-is-organized.md` | Structural mental model — three peer elements, lifecycle spine, reader modes |
| `how-to-walk-a-question.md` | Worked example of traversal — the BOK's flagship use mode |
| `about.md` | Opinionated choices, prior-art citations |
| `contribute.md` | Practitioner contribution discipline |
| `maintaining-the-bok.md` | Steward discipline (this page) |

These pages are not Knowledge Areas (they don't own observability domain knowledge), not Practice Instruments (they don't produce artifacts), not Perspectives (they don't vary by platform). They are the BOK's self-description, and they have their own discipline.

### Why meta pages need explicit governance

Meta drift is silent. A steward adding a new KA updates the hub README (visible change), YAML (visible change), nav (visible change), and cross-references (visible change). The meta pages are not adjacent to the change — they're upstream descriptions that happen to reference the structure. Nothing mechanical forces the steward to re-read them. By default, they get stale.

The failure mode is specific: the meta pages describe the BOK as *it was*, while the structure reflects the BOK as *it is*. Readers encountering the meta first believe they're learning the current BOK; they're learning a superseded version. When the discrepancy shows up in practice — a reader looking for the "fifth instrument type" that was introduced but never reached the meta — the BOK's credibility erodes.

This Part prevents that drift by making meta review a named step, not an assumption.

### Review triggers

Meta pages need review whenever the structure or claims those pages describe change. Specific triggers:

| Change | Meta pages to review |
|---|---|
| Adding or removing a KA | how-the-bok-is-organized, questions-the-bok-answers, about |
| Adding or removing a KA topic | questions-the-bok-answers (if the topic introduces a new question the BOK now answers or scopes out) |
| Adding or removing an Instrument | questions-the-bok-answers (the Role/Workflow section references instruments), how-the-bok-is-organized (if instrument type counts are cited) |
| Introducing a new Instrument type | how-the-bok-is-organized (instrument type list), instruments catalog README, about |
| Adding or removing a Perspective | how-the-bok-is-organized (perspective count/list), questions-the-bok-answers (perspective-variation section), about |
| Modifying the methodology | the-methodology (primary), about, every KA Section 1 that references the methodology |
| Modifying the three-element structure | how-the-bok-is-organized (primary), about, maintaining-the-bok Parts I and VI |
| Changing content-state definitions | contribute, maintaining-the-bok Part II, every KA Section 7 audit header (if template references the definitions) |
| Adding/removing a meta page | start-here routing, hub README, mkdocs nav, any meta page that cross-references the changed page |

### The holistic review protocol

When a review trigger fires, the steward walks the meta set. This is a deliberate step, not an assumption.

**For each meta page identified as affected:**

1. **Read it cold.** Assume nothing about what it currently says. Read as a new reader would.
2. **Check counts and claims.** Does every count in the page match current reality? (Count of KAs, topics, instruments, perspectives, instrument types.) Does every structural claim still hold? ("Three peer structural elements," "five perspectives," "23 instruments in five types.")
3. **Check examples.** If the page uses a worked example (how-to-walk-a-question) or references specific IDs (how-the-bok-is-organized cites KA examples), do the examples still hold? Did any referenced KA/topic/instrument get renamed, moved, or retired?
4. **Check cross-references.** Do internal links resolve? Did a linked page get renamed or moved?
5. **Check consistency with other meta.** Does this page contradict any other meta page? (Two meta pages citing different structure element counts is a smoking-gun inconsistency.)
6. **Update or declare no-change.** Either update the page to reflect current reality, or explicitly note "reviewed, no change needed." The declaration is part of the discipline — silence is not acceptable.

**For the meta set as a whole:**

7. **Cross-meta consistency check.** After individual updates, do all meta pages agree? Run this as a last-pass review.
8. **Navigation coherence check.** After updates, does the start-here routing still make sense? Does the hub README still match what's reachable? Does mkdocs nav expose everything?

### Documenting the review

Meta reviews should leave a trace. Options:

- **Commit message discipline** — the commit that executes a structural change includes a line naming which meta pages were reviewed (e.g., `Meta reviewed: how-the-bok-is-organized (updated), questions-the-bok-answers (no change), about (updated)`)
- **Review notes in maintaining-the-bok itself** — for significant structural changes, append a dated note to this page's changelog section (add one if absent)
- **Test assertion** — some meta drift can be caught by extending Part X tests. For example, a T3.x test could assert that "how-the-bok-is-organized claims N KAs" matches the YAML count. When mechanical assertions exist, silent drift fails the suite.

### What meta review is NOT

- **It is not a full rewrite.** Most meta pages survive a structural change with no edits needed. The review checks; it doesn't assume edits.
- **It is not prose polishing.** Meta review is for accuracy, not style. Resist the urge to "improve" unaffected content during the review — that's a different task and invites scope creep.
- **It is not optional.** Skipping meta review because "the change is small" is how drift accumulates. Small unreviewed changes compound.

### When meta itself needs to change

The meta set can evolve. A new meta page (like `questions-the-bok-answers.md` added after the BOK was built) is a legitimate structural move. The triggers:

- A new dimension of BOK usage emerges that existing meta doesn't address → new meta page
- An existing meta page grows beyond its scope → split
- Two meta pages cover overlapping ground → merge
- A meta page no longer describes anything current → retire with tombstone

Adding/removing a meta page is itself a structural change and follows the Part VIII process for structural change. Include the full integration review: start-here routing, hub README, mkdocs nav, and any meta page that cross-references the changed page.

### The asymmetry: meta is outside the three-element discipline

Meta pages are not Knowledge Areas, Instruments, or Perspectives — so the disambiguation tests in Part I don't apply. A meta page doesn't own domain knowledge, doesn't produce artifacts, doesn't describe variation. It describes the BOK itself. That makes meta a separate class with its own governance — this Part — rather than a fourth peer structural element.

This is deliberate. The three-element discipline is about the *domain content* of the BOK. The meta discipline is about the *self-description* of the BOK. Conflating them would imply meta pages need cross-references into KAs (they don't — they describe them), state markings (they don't — they're either current and accurate or they're broken), and variation by perspective (they don't — meta is invariant across platform contexts).

Meta is not a peer element. It's a governance layer.
