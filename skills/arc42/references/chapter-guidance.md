# Arc42 Chapter Guidance

Distilled from Michaël Hompus's Arc42 Practical Series (blog.hompus.nl, Feb 2026).
Full source: Hompus's public blog series at https://blog.hompus.nl (tag: arc42)

---

## Group 1: Why and Where (Chapters 1-3)

These chapters anchor everything. Produce them first.

### Chapter 1: Introduction and Goals

**What belongs:**
- Brief problem statement and what's being built
- Most important requirements with explicit non-goals
- Top quality goals driving trade-offs (3-5, with measurable criteria)
- Key stakeholders and their concerns/expectations

**What doesn't belong:**
- Component diagrams, deployments, protocols, technical choices
- Complete requirements catalogs
- Extended background stories or project history

**Minimum viable version:**
1. One paragraph: system and rationale
2. 5-10 bullets: essential requirements
3. 3-5 quality goals (short, measurable)
4. Small stakeholder table

**Skeleton:**
```markdown
## 1. Introduction and goals

<1-3 short paragraphs: what's built, why, what problems it solves>

### 1.1 Requirements overview

Most important requirements:
- ...

Explicit non-goals:
- ...

### 1.2 Quality goals

| Priority | Quality | Scenario | Acceptance criteria |
| :------- | :------ | :------- | :------------------ |
| 1        |         |          |                     |

### 1.3 Stakeholders

| Stakeholder | Expectations |
| :---------- | :----------- |
|             |              |
```

**Done-when checklist:**
- [ ] Fits on a few screens
- [ ] New team member can explain the system after reading it
- [ ] Non-goals are explicit
- [ ] 3-5 quality goals with measurable criteria exist
- [ ] Stakeholders map to expectations (not just listed)

**Common mistakes:**
1. Only naming the application without context about problems and benefits
2. Listing features instead of goals (features are implementation; goals are outcomes)
3. No explicit non-goals (enables scope creep)

**Source mapping:** README files, product briefs, stakeholder interviews, call transcripts, project charters, wiki overview pages.

---

### Chapter 2: Architecture Constraints

**What belongs:**
- Organizational constraints (budget, team skills, governance)
- Technical constraints (platforms, operations models, security/compliance)
- Integration constraints (required connections, data formats)
- Conventions (coding standards, CI/CD rules, naming/versioning)

**What doesn't belong:**
- Architecture choices still to be determined (those are decisions, not constraints)
- Personal preferences
- Detailed design specifications

**Key distinction:** A constraint is a rule you must follow. A decision is a choice you make.

**Minimum viable version:** 8-15 constraints in a table.

**Skeleton:**
```markdown
## 2. Architecture constraints

Non-negotiables that shape the design space.

| Constraint | Type | Rationale | Impact | Reference |
| :--------- | :--- | :-------- | :----- | :-------- |
|            |      |           |        |           |
```

**Done-when checklist:**
- [ ] Contains genuine non-negotiables, not preferences
- [ ] Each constraint shows clear design/delivery impact
- [ ] Sources identified for all constraints
- [ ] List remains scannable yet comprehensive

**Common mistakes:**
1. Documenting constraints too late
2. Using vague terms ("secure," "fast") without measurable impact
3. Conflating constraints with architectural decisions

**Source mapping:** Governance documents, compliance requirements, security policies, platform standards, team skill inventories, vendor contracts.

---

### Chapter 3: Context and Scope

**What belongs:**
- Clear system boundary (inside vs outside)
- Business context: external actors and adjacent systems with roles and exchanges
- Technical context: interfaces with direction, protocol, and owner
- Sample payloads for top 1-3 interfaces

**What doesn't belong:**
- Internal building blocks (chapter 5)
- Runtime scenarios (chapter 6)
- Infrastructure layouts (chapter 7)

**Two perspectives, keep them separate:**
- Business context = who, what value/data is exchanged
- Technical context = protocols, formats, integration mechanisms

**Minimum viable version:**
1. One business context visualization or table
2. One technical context visualization or table
3. 1-3 interface examples (sample payloads)

**Skeleton:**
```markdown
## 3. Context and scope

### 3.1 Business context

<Who is outside the system, what value/data is exchanged?>

| External actor / system | Responsibility | Exchange with our system |
| :---------------------- | :------------- | :---------------------- |
|                         |                |                         |

### 3.2 Technical context

| Peer | Interface | Owner | Direction | Protocol / format | Notes |
| :--- | :-------- | :---- | :-------- | :---------------- | :---- |
|      |           |       |           |                   |       |

#### 3.2.1 Interface: <name>

**Purpose:** <why does this interface exist?>
**Direction:** <A -> B, source of truth?>
**Link to spec:** <OpenAPI/AsyncAPI link if exists>

**Example:**
```json
{ "example": "payload" }
```
```

**Done-when checklist:**
- [ ] System boundary explicitly defined (inside vs outside)
- [ ] Business actors and neighboring systems listed with roles
- [ ] Primary interfaces listed with direction, protocol, and owner
- [ ] Most significant integrations include 1-3 examples
- [ ] Critical interfaces have documented expectations or are marked undetermined

**Common mistakes:**
1. Naming neighbors without documenting what's exchanged
2. Conflating business and technical context into one view
3. Assuming REST is the only integration method (files, messaging, batch, manual processes count too)

**Source mapping:** API specs (OpenAPI/AsyncAPI), architecture diagrams, integration docs, system inventories, CMDB records, network diagrams.

---

## Group 2: How Built & How Runs (Chapters 4-7)

### Chapter 4: Solution Strategy

**What belongs:**
- Guiding design choices with rationale and consequences
- "Heavy" decisions unlikely to change each sprint
- Trade-offs linked to chapters 1-3
- Open strategy questions (unknowns made visible)

**What doesn't belong:**
- Detailed internal breakdowns (chapter 5)
- Step-by-step flows (chapter 6)
- Environment-specific details (chapter 7)
- Small sprint-level choices

**Key principle:** Strategy explains reasoning and implications, not just tools selected. "We use Kubernetes" is a technology list. "We deploy containers because operations standardizes on it" is strategy.

**Minimum viable version:** Concise strategy bullets, each with approach, rationale, consequence, and traceability to chapters 1-3.

**Skeleton:**
```markdown
## 4. Solution strategy

<1-3 short paragraphs: overall approach and rationale>

- **<Strategy/decision name>** <Why this direction, what it enables/constrains, which goal/constraint traces back to.>
- **<Strategy/decision name>** ...

### Open strategy questions (optional)

- **Question:** ... Why it matters: ... Next step/owner: ...
```

**Done-when checklist:**
- [ ] Contains strategy statements (not technology wishes)
- [ ] Each statement includes rationale and clear impact
- [ ] Statements link to goals/constraints/context from chapters 1-3
- [ ] Choices remain stable across sprints
- [ ] Open questions are visible, not hidden

**Common mistakes:**
1. Technology listing without rationale
2. Missing rationale makes statements look preferential
3. Hiding unknowns prevents team contribution

**Source mapping:** Architecture decision records, tech stack docs, design discussions, meeting notes about "why" decisions, strategy documents.

---

### Chapter 5: Building Block View

**What belongs:**
- Building block hierarchy (levels 1-3), broad to detailed
- Per block: one-sentence responsibility, key dependencies, main interfaces
- Ownership boundaries and team accountability

**What doesn't belong:**
- Step-by-step flows (chapter 6)
- Deployment details (chapter 7)
- Complete interface specifications
- Low-level implementation details

**Key principles:**
- Chapter 3 = black-box (external perspective). Chapter 5 = white-box (internal structure).
- Level 1 MUST include the same external neighbors from chapter 3.
- Use responsibility-based names, not technology names ("Order Processing" not "Kafka Consumer").

**Minimum viable version:**
1. One level 1 diagram showing system boundary and neighbors
2. Table with responsibilities and dependencies per level-1 block
3. Optionally one level 2 zoom for complex/risky areas

**Skeleton:**
```markdown
## 5. Building block view

### 5.1 Level 1: White-box overall system

| Building block | Responsibility | Dependencies | Notes |
| :------------- | :------------- | :----------- | :---- |
|                |                |              |       |

#### External interfaces (from chapter 3)

| Peer | Interface | Direction | Protocol | Ref |
| :--- | :-------- | :-------- | :------- | :-- |
|      |           |           |          |     |

#### Internal interfaces

| From | To | Purpose | Mechanism |
| :--- | :- | :------ | :-------- |
|      |    |         |           |

### 5.2 Level 2: <Block name> (optional)

| Sub-block | Responsibility | Dependencies | Notes |
| :-------- | :------------- | :----------- | :---- |
|           |                |              |       |
```

**Done-when checklist:**
- [ ] Level 1 includes system boundary and chapter 3 neighbors
- [ ] Each block has clear single-sentence responsibility
- [ ] External interfaces referenced (not duplicated)
- [ ] Level 2/3 used only where complexity justifies
- [ ] New team members can explain "what lives where"

**Common mistakes:**
1. Excessive detail too early (class-level diagrams nobody maintains)
2. Blocks without clear responsibilities (generic names like "Service")
3. Technology as architecture ("Kafka" is implementation, not a building block name)

**Source mapping:** Source code structure, module/package layout, microservice inventories, repository maps, team ownership docs, dependency graphs.

---

### Chapter 6: Runtime View

**What belongs:**
- Scenarios showing building block collaboration during important operations
- User interactions that change state or trigger workflows
- Integrations with external neighbors
- Operationally important processes (batch, scheduled, import/export)
- Alternatives and exceptions: timeouts, retries, partial failures, degraded behavior
- Observability notes: correlation IDs, key logs/metrics

**What doesn't belong:**
- Static responsibility descriptions (chapter 5)
- Full contract catalogs (chapter 3)
- Deployment details (chapter 7)
- Cross-cutting flows identical everywhere like auth (chapter 8)

**Key insight:** "Runtime view is where architecture stops being a set of boxes and becomes a set of promises."

**Minimum viable version:**
1. 1-3 boundary-crossing scenarios
2. Each with: intention, participants (matching chapter 5 names), happy path, first important exception

**Skeleton:**
```markdown
## 6. Runtime view

### 6.1 <Scenario name>

<What happens, why it matters, what "done" looks like>

- **Intention:** what are we trying to achieve?
- **Trigger:** what starts this?
- **Participants:** which building blocks and neighbors?

<Sequence description or diagram>

**Exceptions and alternatives:**
- <timeout> -> <behavior/fallback>
- <partial failure> -> <behavior/fallback>
```

**Done-when checklist:**
- [ ] Relevant user and neighbor interactions covered
- [ ] Scenario descriptions use building block names from chapter 5
- [ ] Key alternatives/exceptions documented
- [ ] Chapter is navigable (scenarios grouped and titled)
- [ ] Readers can explain "what happens when..." without guessing

**Common mistakes:**
1. Only documenting the happy path (architecture shows up in failure handling)
2. Diagram names not matching chapter 5 building blocks
3. Diagram noise instead of insight (skip repetitive returns)

**Source mapping:** Sequence diagrams, runtime traces, log analysis, runbooks, incident reports, user journey maps, API call flows.

---

### Chapter 7: Deployment View

**What belongs:**
- Deployment overview: nodes, environments, network connections
- Building block to infrastructure mapping
- Runtime configuration (5-15 key settings with locations and defaults)
- Trust boundaries and data classification
- Links to IaC assets

**What doesn't belong:**
- Building block explanations (chapter 5)
- Runtime scenarios (chapter 6)
- Interface payload specs (chapter 3)
- Unstructured configuration dumps

**Minimum viable version:**
1. One deployment diagram for the critical environment
2. Mapping table: building blocks to infrastructure
3. 5-15 key configuration settings

**Skeleton:**
```markdown
## 7. Deployment view

### 7.1 Infrastructure overview

<Deployment diagram or description>

#### What runs where

| Building block | Node / environment | Notes |
| :------------- | :----------------- | :---- |
|                |                    |       |

### 7.2 Configuration

| Setting | Default | Production | Impact |
| :------ | :------ | :--------- | :----- |
|         |         |            |        |
```

**Done-when checklist:**
- [ ] All relevant environments or variants described
- [ ] Building blocks mapped to nodes/locations
- [ ] Key runtime configuration documented with defaults
- [ ] Operational concerns acknowledged
- [ ] Newcomers can answer "where does it run?"

**Common mistakes:**
1. Production-only focus (dev and onboarding are valid deployment variants)
2. Unstructured configuration lists without grouping
3. Lost traceability between deployment boxes and building blocks

**Source mapping:** Docker/Kubernetes configs, Terraform/IaC files, deployment diagrams, CI/CD pipelines, environment configs, runbooks.

---

## Group 3: Reusables, Decisions, & Qualities (Chapters 8-10)

### Chapter 8: Cross-cutting Concepts

**What belongs:**
- Patterns applying across multiple building blocks
- Reusable conventions for consistent implementation
- Categories: security, resilience, observability, data/consistency, integration conventions, domain model, test strategy

**What doesn't belong:**
- Feature-specific domain rules
- Raw configuration lists (chapter 7)
- Hard architectural constraints (chapter 2)

**The test:** "If you want developers implementing something identically in multiple places over time, document it here."

**Chapter 8 vs 9:** Chapter 8 = "how we do X consistently." Chapter 9 = "why we chose X over Y."

**Minimum viable version:** 3-6 concepts affecting multiple parts, each with description, key rules, and where it shows up.

**Skeleton:**
```markdown
## 8. Cross-cutting concepts

### 8.1 <Concept name>

<1-3 paragraphs: what and why>

#### Rules
- <rule 1>
- <rule 2>

#### Implementation
- <how it's done>
- <where it lives>

#### Where it shows up
- Scenario: chapter 6.x
- Building block: chapter 5.x
- ADR: chapter 9.x
```

**Done-when checklist:**
- [ ] Contains concepts reused or intended for reuse
- [ ] Each concept includes at least one actionable rule
- [ ] Concepts link to where they appear (chapters 5, 6, 7, 9)
- [ ] Keeps runtime scenarios lean (no repeated explanations)

**Common mistakes:**
1. Waiting until patterns appear everywhere before documenting
2. Chapter becomes a technology dump instead of rules + rationale
3. Repeating concept details in every chapter 6 scenario (move here, link there)

**Source mapping:** Coding standards, shared libraries, middleware configs, logging conventions, error handling patterns, security policies, domain models, test frameworks.

---

### Chapter 9: Architectural Decisions

**What belongs:**
- Decision timeline in scannable table format
- For important decisions: ADR with context, decision, consequences, considered options
- Links to implementing chapters (4-8)

**What doesn't belong:**
- Easy-to-reverse changes
- Meeting notes or transcripts
- Concept guides (chapter 8)

**Key principles:**
- Treat accepted ADRs as immutable. When decisions change, mark original "Superseded" and create new ADR.
- Put the decision in the ADR title for scanning.

**Minimum viable version:** Timeline table with 1-3 lines of motivation per entry.

**Skeleton:**
```markdown
## 9. Architecture decisions

| Date | Decision | Motivation | ADR |
| :--- | :------- | :--------- | :-- |
|      |          |            |     |

### ADR-NNN: <Decision in the title>

| Field | Value |
| :---- | :---- |
| Date | YYYY-MM-DD |
| Status | Pending / Accepted / Superseded by ADR-XXX |
| Decision makers | Names or roles |

#### Context
<What triggered this decision?>

#### Decision
<What we decided and why>

#### Consequences
<What changes, what we accept>

#### Considered options
1. <Option A> -- why not: ...
2. **<Option B (selected)>** -- why: ...
```

**Done-when checklist:**
- [ ] Contains scannable decision timeline
- [ ] Each entry includes decision and motivation
- [ ] Important decisions record considered options
- [ ] Decisions link to relevant chapters

**Common mistakes:**
1. Not recognizing decisions as they happen
2. Skipping considered options (causes later debates)
3. Breaking successor trails when decisions change

**Source mapping:** ADR files, design docs, RFC documents, meeting decisions, commit messages explaining "why", architecture review notes.

---

### Chapter 10: Quality Requirements

**What belongs:**
- Quality requirements grouped by structure (ISO/IEC 25010 recommended)
- Quality scenarios with stimulus, expected response, and measurable metrics
- Links back to chapter 1 quality goals

**What doesn't belong:**
- Technology choices ("Kafka" is a solution, not a requirement)
- Purely functional requirements
- Unmeasurable adjectives

**Key principle:** "If you cannot imagine a test, a metric, or an operational check for a statement, it belongs in chapter 1 as a goal, not chapter 10 as a requirement."

**Minimum viable version:**
1. Quality overview grouped by ISO 25010
2. 3-6 top-priority scenarios
3. Measurable targets per scenario

**Skeleton:**
```markdown
## 10. Quality requirements

### 10.1 Quality overview

<Requirements grouped by quality characteristic>

### 10.2 Quality scenarios

| Scenario | Stimulus | Response | Metric / Target |
| :------- | :------- | :------- | :-------------- |
|          |          |          |                 |
```

**Done-when checklist:**
- [ ] Requirements grouped in recognizable structure
- [ ] Top goals converted to measurable scenarios
- [ ] Scenarios include stimulus, response, and metric
- [ ] Quality areas traced to implementing concepts/decisions

**Common mistakes:**
1. Only adjectives without measurable targets ("fast," "secure")
2. Mixing requirements and solutions
3. No connection back to chapter 1 quality goals

**Source mapping:** SLA/SLO documents, performance requirements, security standards, compliance checklists, load test results, production baselines, quality attribute workshops.

---

## Group 4: Reality & Shared Language (Chapters 11-12)

### Chapter 11: Risks and Technical Debt

**What belongs:**
- Architecturally relevant risks (product, integration, operational, security, performance)
- Technical debt items deliberately postponed
- Open questions / postponed decisions (unmade decisions are risks)
- Per item: statement, why it matters, mitigation, owner

**What doesn't belong:**
- Full project management backlogs
- Sensitive vulnerability details in shared docs (link to private register)
- Duplicate content from chapter 9

**Key distinctions:**
- Risk = something that might happen. Managed through mitigation.
- Technical debt = something already done. A chosen shortcut with continuing costs.
- "If something feels uncomfortable to say out loud, it probably belongs here."

**Minimum viable version:**
- 3-5 realistic risks
- 3-5 technical debt items

**Skeleton:**
```markdown
## 11. Risks and technical debt

| Risk / debt item | Why it matters | Mitigation / decision |
| :--------------- | :------------- | :-------------------- |
|                  |                |                       |

### Known technical debt (optional)

- <shortcut> -> <why acceptable now> ; <when to revisit>
```

**Done-when checklist:**
- [ ] Lists realistic risks affecting delivery or operations
- [ ] Technical debt items visible (not hidden)
- [ ] Each item has owner and next steps
- [ ] Items link to relevant chapters

**Common mistakes:**
1. Treating as a shame list (it supports visibility, not blame)
2. No owners ("A risk without an owner is a wish")
3. Only technical risks (adoption, workflow fit, vendor behavior matter too)

**Source mapping:** Incident reports, post-mortems, tech debt trackers, risk registers, retrospective notes, known-issues lists, audit findings.

---

### Chapter 12: Glossary

**What belongs:**
- Domain terms appearing throughout the documentation
- Abbreviations and acronyms
- Homonyms requiring clarification
- Synonyms with documented canonical terms
- Language mappings for multilingual domains

**What doesn't belong:**
- Extended tutorials or explanations
- Complete domain model duplications
- Unused terminology
- API field definitions

**Include a term if it:** appears across multiple chapters, could be interpreted differently by stakeholders, functions as a contract with neighbors, or would confuse new team members.

**Minimum viable version:** 5-10 terms, 1-2 lines per definition.

**Skeleton:**
```markdown
## 12. Glossary

### Terms and abbreviations

- **Term** -- Meaning/description. Alias: <alternative name if any>.
- **ABBREVIATION** -- _Full Form._ Meaning/description.

### Translations (optional)

| English | <Other language> | Notes |
| :------ | :--------------- | :---- |
|         |                  |       |
```

**Done-when checklist:**
- [ ] Key domain terms across documentation defined
- [ ] Acronyms and abbreviations explained
- [ ] Ambiguous terms have explicit system-specific meanings
- [ ] New team members understand content without repeated clarification

**Common mistakes:**
1. Listing only acronyms without addressing shared meaning
2. Defining terms not used in the document
3. Neglecting ongoing maintenance as terms evolve

**Source mapping:** Existing glossaries, domain models, data dictionaries, onboarding FAQs, terms that caused confusion in meetings or reviews.
