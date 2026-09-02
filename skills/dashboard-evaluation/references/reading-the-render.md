# Reference: Reading the Render

> Read `../SKILL.md` first. This file supplies one thing the engine assumes but
> does not teach: **how to judge a surface by looking at it.** Every other file in
> this package reasons from a description or a definition. This one requires you to
> see the thing as its reader sees it.
>
> Self-contained by design. It duplicates no method from the other files and
> depends on nothing outside this package.

---

## 1. Why this is its own evidence source

A surface's definition — an export, a spec, a source file — tells you what is
**configured**. Only the render tells you what is **perceived**. The two do not
substitute:

| Only the definition shows | Only the render shows |
|---|---|
| That a threshold is absent (absent and untripped look identical in a picture) | Whether the reader finds an entry point at all |
| What is actually being queried | Visual hierarchy — what the eye reaches first, second, never |
| That two elements carry the same content | Density: whether the first screen is a wall |
| Configured sort, bounds, units | Whether configured color reads at the size it is drawn |
| Structure, nesting, reading order as authored | Reading order as experienced, including what falls below the fold |

**A tidy definition file produces unreadable surfaces routinely.** A clean
structure, correct fields, and every element justified can still assemble into a
page nobody can use. That failure is invisible in the source and obvious in the
picture.

**If you have not seen it rendered, you do not have a verdict on it.** Say so.
Never infer the visual from the source — a text review will confidently call a
surface readable while the rendered page is a wall.

---

## 2. The stance

**Adversarial. Default is FAIL.**

You are biased toward passing what you are looking at, especially if you or your
session helped build it. Resist it. Assume the reader bounces and make the surface
prove otherwise.

- *"They'd probably find their way"* means they will not.
- *"It has structure"* is not *"it invites you in."*
- *"Everything on it is justified"* is not *"it works as a surface."*

Name the single worst thing the eye hits first, before anything else.

**Who you are reading as.** Not yourself, and not someone studying it. A person
under time pressure who came looking for one specific thing, on the device and at
the size they actually use — which is often a half-screen beside a ticket, a
shared wall display at a distance, or a phone. A surface that only works
full-screen on a large monitor has a stated constraint, not a pass.

---

## 3. The record

Inspect the first screen — what is visible before any scroll — and fill this in.
Every line is a finding, not a score.

```
RENDER EVALUATION — first screen
- Render actually inspected:     [yes / no — "no" is an automatic FAIL]
- Viewing condition:             [device, size, distance assumed]
- Worst thing the eye hits first:[name it, or "none found" and why]
- Focal point:                   [one dominant entry point / scattered across N equal-weight blocks
                                  — scatter = FAIL]
- Emphasis count:                [distinct competing emphasis treatments visible — color, boxes,
                                  banners, bold. More than a few competing = FAIL]
- Density:                       [share of the screen that is dense content vs. rest
                                  — mostly wall = FAIL]
- Scannable vs. buried:          [is the fast path in scannable form, or buried = FAIL]
- Top task above the fold:       [is the thing the reader came for visible here,
                                  or only navigation, scope, and framing = FAIL]
- Legibility at real size:       [can labels, values, and states be read at the rendered size
                                  — illegible = FAIL regardless of configuration]
- Gameability check:             [did any "pass" above ride on an illusion? see §4]
- Verdict:                       [ENGAGE / BOUNCE]
```

**Severity.** A BOUNCE is a high-severity finding on its own. It fails the
surface's job before any content matters, and it fails silently — nobody reports
that they gave up. Never soften it because the content underneath is sound.

---

## 4. Gameability — passes that are illusions

Each of these lets a bad surface score well. Check them explicitly.

- **Headers are not hierarchy.** Many section headings, each over an equal block of
  equal-weight content, is a labeled wall.
- **More elements are not more coverage.** Past a point, added elements are
  overload; the surface communicates only "busy."
- **A summary strip is not a focal point** if it is itself a row of identical
  tiles with nothing dominant.
- **Color everywhere is not signal.** When most of the surface is colored, color
  has stopped meaning anything, and the one thing that is actually wrong no longer
  stands out.
- **Whitespace inside a dense block is not breathing room.** Judge the screen, not
  the component.

---

## 5. For monitoring surfaces specifically

A dashboard is read at a glance, under pressure, by someone who came for one
thing. Everything above applies, plus:

| Ask | Healthy | Failure |
|---|---|---|
| What does the eye land on first? | The aggregate state — the thing the reader came for | A chart, a logo, a filter bar, or nothing in particular |
| Does status color still mean anything? | Reserved for state, and mostly absent | Series colors and decoration in the same palette as status; most of the surface colored |
| Does configured color actually read? | The state is unmistakable at the rendered size and distance | Thresholds set, but the tile is small, low-contrast, or drawn in a form where hue must carry magnitude |
| How many visual languages? | One — the same kind of thing looks the same everywhere | Several styles side by side, so each element must be decoded on its own terms |
| Does the layout follow the question order? | The reader's sequence — is it OK, what specifically, what does it mean, what now | Grouped by data source, by team, or by whatever was added when |
| Is the answer above the fold? | The state everyone comes for needs no scroll | The top of the surface is filters, titles, and context |

**A surface-level failure outranks every element-level finding.** A reader who
bounces in five seconds never reaches the element you were going to argue about.
Report the surface verdict first.

---

## 6. Where this plugs in

- **While designing** — render it and look, adversarially, before calling it done.
  Fix the wall before anything else.
- **While evaluating** — this is one of the evidence sources, alongside the
  surface's definition and, where the platform exposes it, data about who actually
  opens it. Say which source each finding came from.

---

## 7. Boundary

This judges the **rendered visual only** — what the eye takes in and at what cost.
It does not judge what the surface should contain or in what order (that is the
chain in `../SKILL.md`), whether an element is the right form for its question, or
voice and wording. And it cannot be run without seeing the artifact.

---

## Prior art

Krug, *Don't Make Me Think* and Nielsen (users scan and satisfice; first-seconds
abandonment — the five-second test) · Norman, *The Design of Everyday Things*
(cognitive load, discoverability, signifiers) · Few, *Information Dashboard
Design* (visual hierarchy; emphasis as a scarce currency; at-a-glance
constraints) · Tufte (density, data-ink, removing non-signal).
