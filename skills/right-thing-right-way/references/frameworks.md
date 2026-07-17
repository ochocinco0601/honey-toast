# Framework Reference — Right Thing Right Way

Detailed substance for each framework. Load selectively during dialogue — read the section relevant to the current altitude and gap type, not the entire file.

## Table of Contents

1. [Backward Design](#backward-design) — used at both altitudes
2. [SIPOC](#sipoc) — used at both altitudes
3. [HPT Gap Analysis](#hpt-gap-analysis) — used at both altitudes (the router)
4. [Task Analysis](#task-analysis) — Altitude 2, enablement route
5. [Job Performance Aid Design](#job-performance-aid-design) — Altitude 2, enablement route
6. [Human-AI Task Allocation](#human-ai-task-allocation) — Altitude 2, when AI is involved
7. [Gagné's Nine Events](#gagnés-nine-events) — Altitude 2, when session is involved
8. [How They Compose](#how-they-compose) — the flow between frameworks

---

## Backward Design

**Source:** Grant Wiggins & Jay McTighe, "Understanding by Design" (1998, revised 2005)

**Core idea:** Design by starting from the end. Three stages:

1. **Desired results** — what should the person be able to DO after? Not understand — DO.
2. **Acceptable evidence** — how do we know they achieved it? Not "did they attend" — did the operational outcome change?
3. **Learning experience** — what activities produce that capability?

**Why it matters here:** Traditional design starts with "what content do we have?" and works forward. Backward Design starts with "what performance do we need?" and works backward. The content is determined by the performance requirement, not the other way around.

**At Altitude 1:** "What business outcome needs to advance?" — not "what artifact do we need?"
**At Altitude 2:** "What performance addresses the bottleneck? What evidence proves success?"

**Key discipline:** Success is measured by the operational outcome, not by activity completion. "They completed the template" is not evidence. "During the next incident, they knew the business impact in 5 minutes instead of 60" is evidence.

---

## SIPOC

**Source:** Six Sigma process improvement methodology

**Core idea:** Define any process by five elements:

| Element | Question |
|---|---|
| **Supplier** | Who/what provides input to this function? |
| **Input** | What do they provide? |
| **Process** | What transformation happens? |
| **Output** | What does this function produce? |
| **Customer** | Who consumes the output? |

**Applied at two levels:**
- The overall process (end-to-end pipeline that produces the business outcome)
- Each function within the process (what does this specific performer's function look like?)

**The power is in the boundaries:** Every function's output must be consumable by the next function's customer. Standards are defined by the CONSUMER, not the producer. "Good enough" means the next function can use it.

**Descriptive vs Prescriptive:** When a process exists, SIPOC maps it. When a process doesn't exist (Case 4: new practice), SIPOC designs it. Same framework, different mode.

**At Altitude 1:** Map the business pipeline. Where is it stuck?
**At Altitude 2:** Map the performers' process. What are the I/O boundaries?

---

## HPT Gap Analysis

**Source:** International Society for Performance Improvement (ISPI). Thomas Gilbert, "Human Competence" (1978).

**Core idea:** Systematic diagnosis of what prevents performance. Training is only ONE of six interventions. Most performance gaps are misdiagnosed as knowledge problems when they're actually information or resource problems.

**Gilbert's six factors (Behavior Engineering Model):**

| Factor | Question | If Missing → Intervention |
|---|---|---|
| **Information** | Do they know what's expected and how they're doing? | Process documentation, feedback systems, clear expectations |
| **Resources** | Do they have the tools, time, and materials? | Tool provision, JPA design, resource allocation |
| **Incentives** | Is there meaningful consequence for performing? | Alignment with existing incentives, organizational mandate |
| **Knowledge/Skills** | Do they know how to do it? | Training, practice, conceptual enablement |
| **Capacity** | Are they physically/cognitively able? | Selection, job redesign, workload management |
| **Motives** | Do they want to? | Culture, leadership, purpose connection |

**The ordering matters:** Gilbert argues you should address factors 1-3 (environment) BEFORE factors 4-6 (individual). Fixing information and resources is cheaper and more reliable than training. A JPA (resources) often solves what looks like a training problem.

**Why this is the pivotal framework:** The HPT diagnosis is the router. It determines which Altitude 2 toolkit loads. Getting the gap type right routes to the right intervention. Getting it wrong cascades — everything downstream is well-designed for the wrong problem.

**At Altitude 1:** What's preventing the pipeline from flowing at the bottleneck?
**At Altitude 2:** What's preventing the specific performers from performing their function?

---

## Task Analysis

**Source:** DOD MIL-HDBK-29612 (Instructional Systems Development). Widely used in industrial/organizational psychology.

**Core idea:** Decompose a function into three elements:

| Element | Question |
|---|---|
| **Conditions** | What's true when the person starts? What do they have? What's the environment? |
| **Standards** | What does "done" look like? Measurable, observable. Defined by the CONSUMER of the output. |
| **Performance** | What does the person actually DO? Observable actions, not internal understanding. |

**The critical distinction:** Standards are about OUTPUT quality, not ACTIVITY completion. "Produced a structured capture a PO could validate" is a standard. "Went through the prompt" is not.

**Role flexibility:** The pressure tests showed function boundaries are flexible. A platform IC can perform both the Capture function and the Operationalize function (the "pencil in" path). Task Analysis defines the FUNCTION, not who performs it. The same conditions/standards/performance apply regardless of which role performs the function.

---

## Job Performance Aid Design

**Source:** Military/industrial performance engineering. ISPI.

**Core idea:** A JPA enables correct performance at the point of work WITHOUT requiring the performer to internalize the underlying theory.

**Classic examples:** Pilot's checklist. Surgeon's protocol. The performer doesn't re-learn the theory each time — the aid guides the performance.

**Design principles:**
- **Organized by task sequence**, not by knowledge structure. The aid follows the work, not the methodology.
- **Information at point of need**, not upfront. You learn what a health signal is WHEN you're defining one, not as a prerequisite reading.
- **Assumes basic competency**, not expert knowledge. The IC knows their service. The JPA guides the structuring.
- **Validation test:** Can someone perform correctly using ONLY the JPA? If they need to read a guide first, the JPA isn't self-sufficient.

**Distinction from training:** Training builds internal capability that persists. JPAs provide external support that's present during performance. For most enablement work of this kind, a JPA is more appropriate than training — the performers already have domain knowledge. They lack structure.

**When JPA alone fails:** When the knowledge gap is genuine (Case 4: new practice). A spreadsheet template with "Stakeholder Expectation" as a column header is meaningless if you've never thought about stakeholder expectations. In these cases: conceptual enablement FIRST (using Gagné), THEN JPA for independent performance.

---

## Human-AI Task Allocation

**Source:** Human factors engineering. Draws from Sheridan & Verplank automation levels (1978) and emerging human-AI teaming research.

**Core question:** For each function in a process, what should the human provide vs what should the AI provide?

| Human Provides | AI Provides |
|---|---|
| Knowledge — domain expertise, judgment, contextual understanding | Structure — organizing, formatting, pattern matching, gap identification |
| Decision authority — "is this right?" | Labor — "here's the structured version of what you said" |
| Validation — "this captures my service accurately" | Completeness checking — "these fields are empty" |

**Key principle:** Preserve human agency over MEANING while offloading cognitive LABOR of structuring. The IC decides WHAT their service does and WHO cares. The AI decides HOW to structure that into the required format.

**Practice before platform:** The process must work WITHOUT the AI. If it can't, the questions themselves need work. The AI is an accelerator, not a prerequisite. This was validated in Case 5 (no AI involved) — the same frameworks produced the same process design with a spreadsheet instead of a prompt.

---

## Gagné's Nine Events

**Source:** Robert Gagné, "The Conditions of Learning" (1965, revised through 1992).

**Core idea:** Nine instructional events that align with cognitive processing. When the intervention includes a live session, this sequence structures it:

| # | Event | What It Does | Example |
|---|---|---|---|
| 1 | **Gain attention** | Connect to something they care about | "Last Thursday when that alert fired — how long to figure out who was affected?" |
| 2 | **Inform of objective** | State what they'll be able to DO after | "By the end, your top 5 alerts will have business context." |
| 3 | **Stimulate recall** | Activate existing knowledge as foundation | "You already know this — you reconstruct it every incident." |
| 4 | **Present content** | Show the new material | Side by side: unenriched alert vs enriched alert. |
| 5 | **Provide guidance** | Walk through the first one together | Enrich one alert collaboratively using the JPA. |
| 6 | **Elicit performance** | They do it on their own | Each person enriches one alert from their service. |
| 7 | **Provide feedback** | Review their output | Pair review: "Would this help you at 2 AM?" |
| 8 | **Assess performance** | Does their output meet the standard? | Can the on-call engineer act on it without asking anyone? |
| 9 | **Enhance transfer** | Connect to their ongoing work | "Pick 5 more this week. Same process." |

**Event 3 adapts to the gap type:**
- Knowledge exists (Cases 1, 3): "You already know this. We're capturing it once."
- Knowledge is elsewhere (Case 2): "Your service has business context scattered across Confluence and Jira. Let's find it."
- Knowledge doesn't exist (Case 4): "Let me show you what this looks like with a real example from your domain."

---

## How They Compose

The frameworks aren't seven separate tools. They compose into a flow where each feeds the next:

```
ALTITUDE 1:
Backward Design    →  What business outcome?
      ↓
SIPOC              →  What pipeline? Where stuck?
      ↓
HPT Gap Analysis   →  Why stuck? What gap type?
      ↓
      ╔══════════════════════════════════╗
      ║  DIAGNOSTIC CHECKPOINT          ║
      ║  Present diagnosis + alternatives║
      ║  User's taste validates          ║
      ╚══════════════════════════════════╝
      ↓
Gap type routes to Altitude 2 toolkit
      ↓
ALTITUDE 2 (enablement route):
Backward Design    →  What performance addresses the gap?
      ↓
SIPOC              →  What process do performers need?
      ↓
Task Analysis      →  Conditions / Standards / Performance
      ↓
HPT (again)        →  Information gap? Resources? Knowledge?
      ↓
JPA Design         →  Design the performance aid
+ Human-AI Alloc       (if AI involved: what does each provide?)
      ↓
Gagné              →  Structure the session (if session involved)
      ↓
      ╔══════════════════════════════════╗
      ║  COHERENCE CHECK                ║
      ║  Does intervention connect to   ║
      ║  the diagnosed gap?             ║
      ╚══════════════════════════════════╝
      ↓
Output: Intervention design → handoff to production
```

**Backward Design bookends the whole thing.** SIPOC and Task Analysis define what you're designing for. HPT determines what kind of intervention. JPA and Human-AI Allocation shape the artifact. Gagné structures the delivery. The checkpoints catch errors before they cascade.

**What the composition produces that no single framework would:**

| Insight | Which Framework |
|---|---|
| Success is the operational outcome, not activity completion | Backward Design |
| The performer's customer is the on-call engineer, not "the system" | SIPOC |
| The standard is consumability by the next function | Task Analysis |
| This is NOT a training problem — it's information + resources | HPT |
| The artifact is a JPA, not training material | HPT → JPA |
| The AI structures; the human provides knowledge | Human-AI Allocation |
| Start from their last incident, not from concepts | Gagné Event 1 + 3 |
