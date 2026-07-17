---
name: confluence-design
description: Design discipline for content published in Confluence — the bridge between good document design and the Confluence macro palette. Use when creating OR reviewing a Confluence page a reader will USE to accomplish a task (reference guides, triage/how-to pages, hubs, runbooks), where getting the reader to their answer matters. Covers reader-task-fit, top-task prioritization, macro-as-format selection, single-page composition, and light findability/maintainability. Triggers on "design a Confluence page", "make this Confluence page readable", "review this Confluence page", or proactively when authoring a Confluence page for a human audience. Does NOT own voice/tone (editorial), doc-type classification (Diataxis), or storage-format mechanics.
---

# Confluence Design — Reader-Task-Fit Within the Confluence Envelope

A Confluence page is not a document you write; it is a surface a reader **uses** to get something done. This discipline designs that surface — choosing, from the Confluence macro palette, the format that gets the reader to their answer fastest, and composing the whole page around the reader's task.

It is a **bridge**. Document-design disciplines (`editorial`, and the doc-type discipline) decide what good content *is*. The Confluence mechanics (storage-format XHTML, MCP tools) know how to *emit* a macro. This discipline sits between them: it decides **which macro realizes which reader-need, and how the page composes as a whole.** It owns nothing they own.

## Two modes

1. **During creation (primary):** apply while authoring a Confluence page.
2. **On review (as a lens):** evaluate an existing page — including when loaded by the `independent-discipline-reviewer`. Produce findings with reader-impact rationale.

**Rationale is mandatory in both modes.** The person reading your output (author or reviewer) is not trained in content-design frameworks. Never cite a framework as the justification — always state what happens to the reader.

- **Not this:** "Collapsed the applicability section because top-task theory says tiny tasks bury top tasks."
- **This:** "Put the applicability check in an expand — 90% of readers already know the gate applies to them; they shouldn't scroll past it to reach their fix. The 10% who need it click once."

## What good looks like

### The 5-second test — the severity anchor (Krug; Nielsen)
Before any element-level judgment, look at the first screen the way the reader will: a stressed, overworked person giving it about **five seconds**. Do they see something they can act on — or a wall they will bounce off? A stressed reader gives a page seconds, not minutes; if the first screen reads as dense, or as "not my task yet," they leave and ask a human instead.
- **This governs severity.** A bounce is the *worst* outcome, because it is total and silent — nobody files a complaint about a page they closed. So any finding that pushes the first screen toward "wall" is **high severity**, even if, element by element, a determined reader could eventually navigate through. "Eventually navigable" is not the bar; "engages a stressed reader in five seconds" is.
- **Reader impact:** the page can contain every answer and still fail every reader who took one look and left. Density is not cosmetic — it is the failure mode.

### 1. Answer, not essay (Richards)
Lead with the answer. The reader arrived with a task, not curiosity. The first screen gives the majority reader their path — not context, history, or scope-setting.
- **Reader impact:** a blocked person who must read three sections before finding their path often gives up or asks a human. The page failed even though it "contained" the answer.

### 2. Top tasks dominate; tiny tasks bury them (McGovern)
Name the top 1–3 tasks a reader comes to this page to do. Everything that is not a top task competes with them for attention. Cut it, collapse it, or link it out. Removing content raises success rates.
- **Reader impact:** a paragraph explaining a task-count discrepancy is a *tiny task* (rare curiosity) sitting in the main flow, where it slows every reader who came for the top task.

### 3. Prioritize by purpose within the one page (BLUF)
Confluence pushes toward one long page. That is fine **only if** the page is ordered by who-needs-what, not by how the system is built:
- **Fast path for the majority:** first and prominent (top of page, in a panel).
- **Deep reference for the few:** present but off the fast path (expand macros collapsed; or a linked child page).
- **Escalation:** unmissable, near where a stuck reader actually lands.

This is the handoff from the doc-type discipline: co-locating a how-to and a reference on one page is allowed — but only if the how-to comes first and the reference is collapsed or linked, **not interleaved**.

### 4. The macro palette IS the format toolkit
Content design is choosing the best format for the need. In Confluence, the formats are macros. Match need → macro:

| Reader need | Confluence format | When NOT to use it |
|---|---|---|
| Give the 90% their path immediately | Info panel or a short "Start here" block at the very top | Don't bury it below scope/applicability sections |
| Let scanners jump to their section | TOC macro at top | Not a fix for bad ordering — a TOC over a mis-ordered page still buries the top task |
| Keep deep reference available but off the fast path | Expand macro (collapsed) | Never collapse the fast-path content — only the deep/rare content |
| Signal state or severity at a glance | Status lozenge; note/warning panel | Don't panel everything — if every block is a colored panel, none stands out |
| Show a decision or comparison | Table; two-column layout | Don't table prose that reads fine as a sentence |
| Route a stuck reader to a human | A clearly placed contact/escalation block | Don't leave it only at the very bottom if readers get stuck mid-page |

**Palette is an environment fact.** This table assumes the standard Confluence Data Center set (panels, TOC, expand, status, tables, columns). If the target instance lacks one, drop to the nearest available (a bold "Start here" heading if no info panel). No HTML macro is assumed.

### 5. Findability — the page has to be reached (light) (Baker; McGovern)
A page only works if the right reader lands on it.
- Title it the way people **search for the problem**, not the way the system names it.
- Make it THE canonical first-stop, and link to it from where readers actually are (the pages or tickets that send them here).
- Every page stands alone — a reader arriving cold from search must orient without the parent context.
- **Reader impact:** a perfect page nobody finds is a page nobody reads.

### 6. Maintainability — the page has to stay true (light) (Kissane "supported"; Halvorson)
A reference synthesized from other sources rots as they change.
- Declare the sources it synthesizes, a last-verified date, and a named owner / feedback channel so drift gets reported.
- **Reader impact:** a stale page that still looks authoritative sends readers down wrong paths — worse than no page at all.

## During creation — apply it

1. **Name the top 1–3 reader tasks first.** Write them down; everything else is measured against them.
2. **Draft the fast path** for the majority task — put it first, in a panel or short block.
3. **Everything that isn't a top task:** cut, collapse (expand), or link out.
4. **Choose macros by need** (table above), not decoration.
5. **Place the escalation path** where a stuck reader will be.
6. **Add the maintainability footer** (sources, last-verified, owner).
7. **Gut-check the first screen:** five seconds, stressed reader — would they engage, or bounce? If bounce, the fast path isn't prominent enough. Fix that before polishing anything else.
8. **Surface your choices** to the user in reader-impact terms.

## On review — evaluate it (the lens)

**First, the holistic pass — it sets severity.** Read only the first screen, as a stressed reader with five seconds. Would they engage, or bounce? A first screen that reads as a wall — dense text, or scope/applicability/glossary before the fix path, with no obvious "act on this now" — is a **high-severity** finding on its own, and it raises the severity of every element-level finding that feeds the wall. Do not settle on "medium / no blocker" because a determined reader *could* get through; the stressed reader the page is for will not try.

Then walk these element-level checks — each finding stated as **location + reader impact + recommendation**:

1. **Top task named?** Can you state the top 1–3 tasks from the page alone? Does the first screen serve them? (First screen is scope/applicability/history → finding.)
2. **Burial:** what non-top-task content sits in the main flow (machinery explanations, traceability codes, exhaustive enumerations)? Cut / collapse / link?
3. **Fast-path prominence:** is the majority path first and visually prominent, or behind context?
4. **Macro fit:** is each macro doing a job for the reader, or decoration / over-paneling? Is deep reference collapsed and fast-path content *not* collapsed?
5. **Ordering:** sequenced by reader need, or by system structure?
6. **Escalation:** can a stuck reader reach a human from where they get stuck?
7. **Findability:** does the title match how readers search? Does the page stand alone?
8. **Maintainability:** sources declared, last-verified date, owner named?

**Verdict line:** in five seconds on the first screen, would a stressed, overworked reader engage — or bounce? If they would bounce, the page fails its job no matter what it contains — that is the headline verdict, and it is high severity. Then: does the majority reader reach their answer fast, and can everyone else get theirs without wading through content that isn't theirs?

## What this discipline does NOT do

- **Voice, tone, word-level economy, provenance** → `editorial`.
- **Document *type* classification and type-separation** (Diataxis) → the doc-type discipline. This discipline assumes the type is settled; it governs how settled content is prioritized and formatted for Confluence.
- **Storage-format XHTML, macro syntax, MCP tool selection, 400-error avoidance** → the Confluence mechanics layer (a mechanics skill, or the model's native Confluence ability). This discipline names *which* macro and *why*; it does not emit it.
- **On-demand multi-lens usability critique** → `artifact-review` (this discipline can serve as one lens within it).
- **The rendered visual** — visual hierarchy, density, cognitive load, scannability → `visual-usability`, which must *see* the page. The 5-second test is **co-determined**: this discipline judges its *structural* half (order, top-task, burial, prominence — all judgeable from structure/source); `visual-usability` judges its *visual* half (density, whitespace, hierarchy — judgeable only from a render). Neither alone is the whole verdict, and a text-only review can only reach the structural half.

## Source / prior art

- **Steve Krug**, *Don't Make Me Think* (2000) — users don't read, they scan and satisfice; a page must be self-evident in seconds or they leave.
- **Jakob Nielsen (NN/g)** — users judge and frequently abandon a page within the first seconds; the "5-second test" as a usability method.
- **Sarah Richards**, *Content Design* (2017) / GOV.UK — content design is choosing the best format for the user need; answer, not essay.
- **Gerry McGovern**, *Top Tasks* (2018) — top tasks dominate; tiny tasks bury them; removing content improves findability.
- **Erin Kissane**, *The Elements of Content Strategy* (2011) — "supported" content (owner, lifecycle, maintenance).
- **Kristina Halvorson**, *Content Strategy for the Web* — governance and workflow.
- **Mark Baker**, *Every Page Is Page One* (2013) — pages reached cold from search must stand alone.
- **BLUF / inverted pyramid** — answer-first ordering.
- Handoff to the doc-type discipline (Diataxis, Procida) for type; `editorial` for voice.
