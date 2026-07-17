---
name: editorial
description: >
  Load editorial governance before producing human-facing content — tone/style principles,
  documentation production standard, and writing craft principles. Implements the editorial
  function from content strategy (Halvorson), publishing (house style), and technical
  communication. Use when the user says "/editorial", "apply editorial", "load editorial",
  "load tone and style", or when producing stakeholder-facing work. Covers documentation,
  emails, presentations, stakeholder deliverables, guides, and any output where the
  audience is someone other than the author or future AI sessions.
---

# /editorial — Editorial Governance

Activate editorial governance before producing human-facing content. This skill loads quality principles that shape how you write for the rest of the session.

The reason this exists as a dedicated skill: editorial governance is too much to hold as ambient instructions, and behavioral instructions to "write well" are unreliable across sessions. This skill makes governance activation structural — same principles, same confirmation, every time.

## Activation

When invoked, confirm the governance is active:

```
## Editorial Governance Active

**Voice** — tone and stakeholder communication principles
**Structure** — documentation production standard
**Craft** — writing discipline principles

Governance active for this session. Re-invoke /editorial to refresh.
```

Then apply all principles below during content production — not as a post-hoc review, but as active constraints while writing.

---

## Voice Principles

How you sound when writing for stakeholders. Sourced from content strategy governance (Halvorson, *Content Strategy for the Web*) and stakeholder communication best practices.

### 1. Validate Their Problem First

Lead by acknowledging the recipient's problem statement before introducing any solution. Starting with your solution implies they haven't thought about the problem. Starting with their problem shows you listened.

### 2. Enabling Language, Not Automatic Language

Use language that describes potential and enablement, not automatic operation.

| Avoid | Prefer |
|-------|--------|
| feeds | informs |
| produces | enables, can generate |
| extracts | facilitates extraction |
| automatically | can be used to |
| integrates with | can inform, can enrich |

Automatic language implies turnkey systems that may not exist. Enabling language is accurate about current state while conveying real value.

### 3. Current State vs Future Vision Accuracy

Explicitly distinguish what exists now from what's envisioned. Use status indicators:
- "Exists (manual workflow)" — system exists, content helps the manual process
- "Future (envisioned)" — aspiration, not current reality

Conflating current and future misleads about what's available today.

### 4. Accurate Capability Claims

Be precise about what exists vs what could be adapted or extended:
- "We have X for Y" — exists and works today
- "X could be adapted for Y" — exists, would require modification
- "X would need to be created for Y" — neither exists

Overstating capabilities damages credibility.

### 5. Collaborative Framing, Not Product Framing

Frame as collaborative problem-solving — not as selling a solution to their problem.

**Avoid:** "Our solution provides..." / Feature lists without connection to their context
**Prefer:** "Here's how it maps to what you need" / Their vocabulary mapped to your vocabulary

Product framing positions you as vendor, them as customer. Collaborative framing positions both as problem-solvers.

### 6. Respect Their Vocabulary

Map their terms to your terms; don't force vocabulary replacement. Forcing vocabulary replacement feels like absorption. Mapping vocabulary shows conceptual equivalence while respecting their domain language.

### 7. Acknowledge Their Contributions

Reference their work explicitly. Use their phrases. Show you've read and understood their contribution. People invest effort in their work — acknowledging it builds trust.

### 8. Show Expansion Opportunities, Not Gaps

When their use case requires something you don't have, frame as enrichment that validates extensibility — not as a gap or deficiency. Gap language implies incompleteness. Expansion language positions their contribution as valuable input.

### 9. Don't Reference Structure the Audience Hasn't Met

Phrases like "just your part" or "on your side" imply a larger system the audience hasn't been introduced to. Present content as complete for this audience — introduce broader structure only when the audience needs it.

### 10. Don't Frame Proven Methodology as an Experiment

When the methodology is established, don't hedge on whether it works. Starting small is practical sequencing, not a value experiment. Hedging undermines everything you just presented.

### 11. Instructions, Not Encouragement

If a sentence's purpose is encouragement rather than information, cut it. Motivational filler takes up space, adds no information, and can feel patronizing. Say what to do. Don't add a pep talk.

---

## Documentation Production Standard

How you decide what to include, exclude, and organize. Sourced from Baker (*Every Page Is Page One*), Carroll (*Minimalism*), McGovern (*Top Tasks*), and field-tested documentation production.

### 0. Concept vs Operationalization Balance

Before writing, determine: does this audience already have the concept? If yes, lead with operationalization (what teams do). If not, provide just enough concept to make the operational content legible — then operationalize immediately.

### 1. Outside-In Framing

Start from the reader's world, not the system's internal logic. The opening sentence should describe something the reader recognizes from their own experience.

### 2. Audience-First Organization

Organize by who needs it and what they need to understand — not by document type, content group, or creation history. Use need statements ("I need to evaluate this for my team") not job titles.

### 3. Word Economy as Testable Constraint

Set word budgets before writing. Measure after. A section that exceeds its budget must be cut, not explained. Guidelines: navigation page 150-300 words, practitioner page 400-600 words. If it's longer, content is doing the job of linked artifacts.

Expert discipline tests during writing:
- **McEnerney:** Does every sentence establish problem, present evidence, draw conclusion, or signal structure? If not, cut it.
- **Carroll (Minimalism):** Get users doing tasks immediately. Don't front-load concepts.
- **McGovern (Top Tasks):** Removing content improves findability.
- **Zinsser/Orwell:** If you can cut a word, cut it.
- **Horn (Chunking):** One point per block. Max ~7 sentences per block.

### 4. Exclude List Before Include List

For every section, define what NOT to include before defining what to include. The exclude list is where word economy actually gets enforced. The writer always knows more than the reader needs.

### 5. Thinking Scaffolding Separation

Methodology internals are reasoning tools. Audiences see the minimum needed to understand and act. If removing a concept from the page would not change what the reader does, the concept is scaffolding and belongs in the repo, not the page.

### 6. Self-Contained with Inline Examples

Pages must carry their proof. Links are supplementary. The page works if every link is broken. Inline tables, concrete examples embedded on the page — link to full artifacts for those who want more detail.

### 7. Positioning Before Detail

The reader must understand what this IS (and isn't) before encountering methodology, tools, or procedures. If the reader only reads the first two sentences, do they know what domain they're in?

### 8. Every Page Is Page One (Baker EPPO)

A reader arriving at any page — via search, shared link, or meeting follow-up — understands context without having read other pages. No "as discussed above" or context that only exists on a parent page.

### 9. Audience-World Projection

Content projects the system onto the reader's world. It does not present the system's internal logic and expect the reader to map it. Use the reader's vocabulary.

### 10. Progressive Disclosure

The same structure serves a 60-second scan and a 30-minute deep dive. Headings and first sentences give the full picture on scan. Don't bury key points in paragraph 3.

---

## Writing Craft Principles

How you construct prose. Sourced from iterative feedback during practitioner content production — general principles that apply to any documentation.

### 1. Start from the reader's experience, not the system's taxonomy

Frame content from THEIR world and map TO the system's concepts. Don't ask the reader to locate themselves in your model.

### 2. Examples earn their place only by resonating

If the reader doesn't recognize the example from their own experience, it's noise. Use examples from the reader's likely domain or describe the recognition moment.

### 3. Lead with the absence, not the offering

Describing what's MISSING connects to the reader's lived pain faster than describing what you're PROVIDING. Name their pain and they'll connect the dots themselves.

### 4. Don't narrow the hook to one dimension

When describing impact, problems, or value — cover the full spectrum so every reader finds their situation.

### 5. Word economy is a production constraint, not polish

Apply during writing, not after. Every sentence that isn't actionable is a sentence the reader skips.

### 6. Pressure test with real examples

Abstract models work in theory. Real organizational structure breaks them. Always test frameworks and examples against concrete cases before considering content stable.

### 7. Preempt "it already exists"

When claiming a structured record doesn't exist, readers will think "but it's in Jira / Confluence / my head." Preempt with one sentence: name why scattered fragments don't count.

### 8. Write to learn, not to perfect

The first real reader exposes what the writer can't see. Close enough to learn from, not perfect before testing.

---

## Pre-Delivery Checklists

### Voice Checklist
- [ ] Validates their problem before introducing solutions?
- [ ] Enabling language, not automatic language?
- [ ] Current state clearly distinguished from future vision?
- [ ] Capability claims accurate?
- [ ] Collaborative framing, not product positioning?
- [ ] Respects their vocabulary?
- [ ] Acknowledges their contributions?
- [ ] Missing capabilities framed as expansion?
- [ ] Every sentence instructional or informational — no motivational filler?

### Structure Checklist
- [ ] Concept vs operationalization balance determined for audience?
- [ ] Opens from the reader's world, not the system's?
- [ ] Organized by audience need, not content type?
- [ ] Word budgets set, measured, and met?
- [ ] Exclude list defined — you know what you left out and why?
- [ ] No methodology internals in audience-facing content?
- [ ] Inline examples — works with broken links?
- [ ] Positioning in first two sentences?
- [ ] Every page stands alone — no sequential dependency?
- [ ] Reader's vocabulary, not system vocabulary?
- [ ] Headings and first sentences give the full picture on scan?

---

## What This Skill Does NOT Do

- **Produce content** — sets quality context, then exits. Production is other skills' or sessions' concern.
- **Evaluate output** — post-production review is a separate concern.
- **Load professional disciplines** — craft expertise (Tufte, Baker, Norman) is separate from editorial governance.
- **Classify document type** — Diataxis classification (tutorial, how-to, reference, explanation) is a separate concern.
