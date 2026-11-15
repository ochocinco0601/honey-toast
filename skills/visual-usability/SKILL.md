---
name: visual-usability
description: Design discipline for the RENDERED visual of a page or document — visual hierarchy, information density, cognitive load, scannability, and the 5-second first impression. Use when creating OR reviewing anything a reader takes in with their eyes (a Confluence page, a slide, a one-pager, a dashboard), and especially to judge whether a stressed reader engages or bounces in the first seconds. REQUIRES seeing the rendered artifact (screenshot or live render) — it cannot be judged from source text or a text extraction. Grounded in Norman, Tufte, Few, Krug. Does NOT own content/structure (confluence-design), voice/tone (editorial), or doc-type (Diataxis).
---

# Visual Usability — Can the Eye Take This In, Fast?

Before a reader reads a word, they **see** the page — and in a few seconds decide whether to engage or bounce. This discipline judges that: the rendered visual. It is the counterpart to the content/structure disciplines (which judge *what* the page says and *how* it's organized). This one judges how it **looks** and how much effort the eye must spend.

**Requires the rendered artifact.** You cannot judge visual density, hierarchy, or cognitive load from source text or a text extraction — a tidy outline hides the wall. Review a screenshot or a live render. If you only have source text, say so and decline the visual verdict; do not fake it. A text-based review can declare a page "engages" while the rendered page is a wall a reader bounces off — the source hides the very thing you are judging.

## The job this serves

*Inferred from this skill's own text.*

- **The job, one and two levels up:** a page someone made reaches a time-poor reader who takes it in and acts on it, so the person's work lands with the people it is for instead of being skimmed past.
- **Its step:** the visual check, while a page is designed and before it is shown, alongside the content, structure and voice checks, which it does not own.
- **What it receives:** a rendered page, from the session building it or from a reviewer agent given this skill as its lens.
- **What it hands on:** what the reader's eye experiences, each with a recommendation, to whoever builds the page.
- **Done for the whole job:** the reader engages with the page in its first seconds and finds what they came for, shown by evidence from the rendered page, not by the builder's account of it.

## Two modes

1. **During creation:** apply while designing the rendered page.
2. **On review (as a lens):** evaluate a rendered artifact; findings as **what the eye experiences + recommendation**.

Rationale is mandatory — state what the reader's *eye* experiences, never the principle name.

## What good looks like

### The 5-second visual gestalt — the severity anchor (Krug; Nielsen)
Look at the first screen *as rendered*, for five seconds, as a stressed reader. Does the eye find an obvious entry point and a sense of "I can act here" — or hit a **wall**: dense text, no whitespace, everything the same weight? A wall = bounce = total, silent failure. This governs severity: **visual density that loses the reader in five seconds is HIGH**, no matter how sound the underlying content is. (This is the *visual* half of the 5-second test; the *structural* half — order, top-task, burial — lives in `confluence-design`. Neither alone is the whole verdict.)

### Visual hierarchy (Norman; Tufte)
The eye should be led — biggest/boldest = most important; a clear path from primary to secondary.
- **Eye experience:** with no hierarchy, everything competes, and the reader must read everything to find anything.

### Density & signal ratio (Tufte; Few)
Every visual element should carry signal. Cut visual noise — redundant borders, heavy rules, decorative panels, cramped blocks. Whitespace is not wasted space; it is what lets the eye rest and parse.
- **Eye experience:** a dense wall raises the effort-per-glance, and a stressed reader won't pay it.

### Scannability (Krug)
Users scan, they don't read. Support the scan: headings that state the point, short chunks, lists over paragraphs for steps, the fast path visually prominent.
- **Eye experience:** an unscannable page forces linear reading no one under pressure will do.

### Cognitive load (Norman)
Minimize what the reader must hold in their head. Consistency reduces load — the same kind of element should look the same everywhere.
- **Eye experience:** overload feels like work, and the reader offloads it by leaving.

### Emphasis is a scarce currency (Few)
Spend emphasis — color, panels, bold — only on what matters. If everything is emphasized, nothing is.
- **Eye experience:** over-emphasis (every block a colored panel) flattens back into visual noise.

## During creation — apply it

1. Design the first screen to pass the 5-second gestalt: obvious entry point, breathing room, one clear "act here."
2. Establish hierarchy — size/weight the most important thing biggest.
3. Cut visual noise; add whitespace; prefer scannable chunks and lists.
4. Spend emphasis sparingly.
5. **Render it and look — adversarially.** Five seconds, stressed reader, default FAIL: hunt for the worst thing the eye hits first. Engage or bounce? Fix the wall before anything else.

## On review — evaluate it (the lens)

**Rendered artifact required — source alone is not a valid pass.** Evaluation from source (or a text extraction) is *not a valid pass*. Given only text, or no browser to open it in, stop this lens and report that the visual verdict can't be rendered — never guess it.

**The stance is ADVERSARIAL. Default is FAIL.** You are biased toward passing what you're looking at — resist it. Assume the stressed reader bounces, and make the page prove otherwise. "They'd probably find their way" means they won't; "it has structure" is not "it invites you in." Name the single worst thing the eye hits first before anything else.

**Review the whole artifact, in a browser you drive yourself, with the questions for its kind.**
Why: judging only the first screen, from screenshots the builder chose, with pass-or-fail items,
passes a lesson page whose steps do not group. A reviewer asked to list the groups it sees against
the groups the author meant fails that page, with measured gaps.

1. **Open it yourself** with the browser tools. Screenshots someone else picked are not a review.
2. **Walk every state** the request names (steps, tabs, lenses, open folds, a clicked selection), at
   desktop and phone width, light and dark where the page has both. Say which you walked.
3. **Run `measure-text.md`** in each state, width and theme.
4. **Answer `questions.md`** for the artifact's kind: the five every kind gets, then its kind's own.
   Each answer is a list, a measurement or a quotation, compared with what the artifact is meant
   to do. `catalog.md` holds the design field's full checks behind them, with sources; use it when a
   question needs more depth or the artifact is a kind the questions do not list.
5. **Report** each finding with its evidence, ranked by harm to the reader, then the 5-second
   verdict below. Name what you could not check and why.

```
VISUAL EVALUATION
- Opened and walked: [states, widths, themes]
- Worst thing the eye hits first: [name it]
- Findings, worst first: [question or catalog id · evidence · harm to the reader]
- Needs a human eye: [anything measurement and these questions could not settle]
- 5-second verdict: [ENGAGE / BOUNCE]
```

**Severity:** a BOUNCE is **high severity** on its own — it fails the page's job before any content matters, and it fails silently. Never soften it to "medium" because the content underneath is fine.

**Verdict line:** in five seconds on the rendered first screen, does a stressed reader engage or bounce? BOUNCE is the high-severity headline verdict.

## What this discipline does NOT do

- **Content prioritization, top-task, macro/format choice, page composition** → `confluence-design` (the structural half of the 5-second test).
- **Voice, tone, word economy** → `editorial`.
- **Document type** (Diataxis) → the doc-type discipline.
- It judges the **rendered visual only**, and it must **see** the artifact.

## Source / prior art

- **Don Norman**, *The Design of Everyday Things* — cognitive load, discoverability, signifiers.
- **Edward Tufte**, *The Visual Display of Quantitative Information* — data-ink ratio, remove non-signal, density done right.
- **Stephen Few**, *Information Dashboard Design* — visual hierarchy, emphasis as scarce currency, scannability.
- **Steve Krug**, *Don't Make Me Think* / **Jakob Nielsen** — users scan and satisfice; first-seconds abandonment (the 5-second test).
