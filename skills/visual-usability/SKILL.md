---
name: visual-usability
description: Design discipline for the RENDERED visual of a page or document — visual hierarchy, information density, cognitive load, scannability, and the 5-second first impression. Use when creating OR reviewing anything a reader takes in with their eyes (a Confluence page, a slide, a one-pager, a dashboard), and especially to judge whether a stressed reader engages or bounces in the first seconds. REQUIRES seeing the rendered artifact (screenshot or live render) — it cannot be judged from source text or a text extraction. Grounded in Norman, Tufte, Few, Krug. Does NOT own content/structure (confluence-design), voice/tone (editorial), or doc-type (Diataxis).
---

# Visual Usability — Can the Eye Take This In, Fast?

Before a reader reads a word, they **see** the page — and in a few seconds decide whether to engage or bounce. This discipline judges that: the rendered visual. It is the counterpart to the content/structure disciplines (which judge *what* the page says and *how* it's organized). This one judges how it **looks** and how much effort the eye must spend.

**Requires the rendered artifact.** You cannot judge visual density, hierarchy, or cognitive load from source text or a text extraction — a tidy outline hides the wall. Review a screenshot or a live render. If you only have source text, say so and decline the visual verdict; do not fake it. A text-based review can declare a page "engages" while the rendered page is a wall a reader bounces off — the source hides the very thing you are judging.

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

**Rendered artifact required — source alone is not a valid pass.** Evaluation from source (or a text extraction) is *not a valid pass*. Given only text, stop this lens and report that the visual verdict can't be rendered — never guess it.

**The stance is ADVERSARIAL. Default is FAIL.** You are biased toward passing what you're looking at — resist it. Assume the stressed reader bounces, and make the page prove otherwise. "They'd probably find their way" means they won't; "it has structure" is not "it invites you in." Name the single worst thing the eye hits first before anything else.

Inspect the rendered first screen (what's visible before scrolling) and record:

```
VISUAL EVALUATION — first screen:
- Screenshot actually inspected: [yes / no — "no" = automatic FAIL]
- Worst thing the eye hits first: [name it, or "none found" + why]
- Focal point: [one dominant entry point / scattered across N equal-weight blocks — scatter = FAIL]
- Emphasis-treatment count: [colored panels + banners + bold callouts + status colors visible — >3 competing = FAIL ("if everything's emphasized, nothing is")]
- Density: [share of the screen that is dense text vs. whitespace — mostly wall = FAIL]
- Scannable vs. buried: [is the reader's fast path in scannable form — headings, short list items — or buried in prose? buried = FAIL]
- Above-the-fold answer: [is the reader's top task visible here, or only scope/nav/deadline? only-meta = FAIL]
- Gameability check: [many headers but each section a dense block != scannable; many panels = overload not hierarchy — did any "pass" ride on one of these illusions?]
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
