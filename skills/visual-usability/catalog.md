# Design review catalog for rendered reader-facing pages

**What this is for.** A checklist-shaped body of the design field's own review knowledge, for an AI reviewer looking at a rendered page in a browser: a web page, a lesson page on a self-paced training site, an HTML report, a briefing page, a document read in a browser. Each item gives the principle in the field's term and its source, a review question the reviewer answers from the reader's seat with evidence (never a yes/no), how to measure it on the rendered page where it can be measured, and a seeded defect that lets you test whether a review catches the failure.

**Where the items came from.** The design field, not this repo: Gestalt psychology (Wertheimer, Koffka; Palmer and Rock's common region and uniform connectedness), cognitive psychology of chunking and attention (Miller, Cowan, Treisman, Ware), Nielsen Norman Group eyetracking and usability research, Krug (*Don't Make Me Think*), Norman (*The Design of Everyday Things*), Williams (*The Non-Designer's Design Book*: contrast, repetition, alignment, proximity), Tufte, Few, Mayer's multimedia learning principles, Sweller's cognitive load theory, typography from Bringhurst (*The Elements of Typographic Style*), Butterick (*Practical Typography*), Lupton (*Thinking with Type*), Müller-Brockmann (grid systems), design-system guidance from Material, IBM Carbon, GOV.UK and USWDS, Baymard Institute, and WCAG 2.2 level AA.

**How to use it.**
- Answer every question with a list, a measurement or a quotation from the page. A verdict without evidence does not count as an answer.
- Measure at three widths: 1280 px (desktop), 768 px (tablet), 375 px and 320 px (phone). Measure in both colour schemes when the page has a dark mode.
- A threshold marked **(rule of thumb)** is a convention of the field, not a standard. A threshold marked **(WCAG)** is normative at level AA.
- Items marked **Human eye** have no reliable measurement. The reviewer can collect evidence for them but cannot settle them by number, and a person should look.

Measurement helpers used below (run them in the page console or through a DevTools evaluate call):
- `getComputedStyle(el)` gives font-size, line-height, font-weight, colour, margins and padding.
- `el.getBoundingClientRect()` gives position and size. The vertical gap between two blocks is `next.top - prev.bottom`.
- Contrast ratio: the WCAG relative-luminance formula on the computed foreground colour and the effective background colour (walk up ancestors until a non-transparent background is found, and check for background images).
- Characters per line: `el.clientWidth / (average glyph width)`. Measure the average glyph width by rendering a sample string of 100 lowercase characters in the same font and dividing its width by 100. Or count the characters on the first full line using a Range over the text node.

---

## A. Hierarchy and entry point

### A1. Visual hierarchy and entry point
1. **Principle.** Visual hierarchy: the order in which elements are perceived should match their order of importance. The page has one dominant entry point. Sources: Lupton, *Graphic Design: The New Basics*; NN/g "Visual Hierarchy in UX"; Williams (contrast).
2. **Question.** Squint at the page, or blur a screenshot by about 8 px. List the first three things your eye lands on, in order. Then list the three things the page most needs the reader to take away. For each mismatch, name the element that wins attention and the property that makes it win (size, weight, colour, isolation).
3. **Measure.** Rank elements by visual weight: font-size multiplied by weight, plus colour saturation and contrast against the background, plus area. Compare the order of the top three with the content's intended order. You can use a saliency model on a screenshot if one is available. **Human eye** for the final call.
4. **Seed.** Give a decorative pull-quote or a secondary "Note" box a larger size and a saturated background than the H1.

### A2. Distinguishable heading levels
1. **Principle.** Contrast between levels. Adjacent levels of hierarchy need a difference the reader can see, usually two or more cues (size, weight, space, case). A timid difference is worse than none. Sources: Butterick ("Headings"); Bringhurst §3; Williams ("don't be a wimp" about contrast).
2. **Question.** For each pair of adjacent heading levels on the page (H1 to H2, H2 to H3, H3 to body), list the cues that differ and their values. Pick one H3 and one bold body paragraph lead-in: can you tell them apart from the rendering alone? State which cue does it.
3. **Measure.** Computed font-size ratio between adjacent levels: **≥ 1.2 (rule of thumb)**, or a size step plus a weight step. Space above a heading should be greater than space below it (see C3). Two levels that differ only by about 1 to 2 px or by weight 600 against 700 count as indistinguishable.
4. **Seed.** Set H3 to the same size as body text with weight 600, while body lead-ins use `<strong>`.

### A3. Front-loaded, scannable headings and labels
1. **Principle.** Information scent and front-loading. Readers scan the first two or three words of headings, links and list items. Sources: NN/g "First 2 Words: A Signal for the Scanning Eye"; Pirolli and Card (information foraging); GOV.UK content design.
2. **Question.** Quote every H2 and H3. For each one, write down only its first three words and say what a reader would expect the section to contain from those words alone. Then compare that expectation with what the section actually contains.
3. **Measure.** Count the headings whose first three words are generic, such as "Overview", "About the", "More on", "Introduction to" or "Step 3". Count the headings that read the same as a sibling. **Human eye** for scent quality.
4. **Seed.** Rename section headings "Part 1", "Part 2" and "Part 3", or start every heading with "Understanding the…".

### A4. Inverted pyramid and the point first
1. **Principle.** Inverted pyramid, or BLUF (bottom line up front): the conclusion comes first and support follows. Sources: NN/g "Inverted Pyramid"; GOV.UK; Minto (*The Pyramid Principle*).
2. **Question.** Quote the first sentence of the page and the first sentence of each section. For each, say whether a reader who stopped there would know the main point or the action. If not, quote the sentence where the point first appears and give its position (paragraph number).
3. **Measure.** Find the position of the first sentence that carries the conclusion or the instruction. A first viewport made only of background or preamble fails this item. **Human eye** for the content judgment.
4. **Seed.** Move the key result or instruction to the last paragraph and open with history or context.

---

## B. Gestalt grouping

### B1. Proximity
1. **Principle.** Law of proximity: elements close together are seen as a group. Spacing must encode structure. Sources: Wertheimer (1923); Williams (proximity); NN/g "Proximity Principle in Visual Design".
2. **Question.** List the chunks your eye finds in this section from spacing, lines and size alone. List the chunks the content is built from. For each boundary the content means, give the measured gap against the gaps inside the chunks on either side. Name every label or caption that sits closer to the wrong item.
3. **Measure.** Collect vertical gaps between consecutive blocks with `getBoundingClientRect`. Between-group gap / within-group gap should be **≥ 1.5 to 2 (rule of thumb)**. A heading's gap above should be at least about 2 times its gap below. A caption should sit nearer its figure than the next paragraph.
4. **Seed.** Give every block an equal 24 px margin so section boundaries, list items and paragraphs all share one gap. Or put a heading equidistant between the previous section and its own.

### B2. Similarity
1. **Principle.** Law of similarity: things that look alike are read as the same kind and do the same job. Sources: Wertheimer; Ware, *Information Visualization* (preattentive features).
2. **Question.** List every distinct visual treatment on the page: each colour, box style, text style and icon style. For each one, list what it is applied to. Name any treatment applied to two different kinds of thing, and any kind of thing drawn in two treatments.
3. **Measure.** Group elements by computed style signature (colour, background, border, font-size, weight). Map each signature to content roles. A one-to-many or many-to-one mapping is a finding.
4. **Seed.** Style non-clickable key terms in the same blue as links. Or give "Warning" and "Tip" callouts identical boxes.

### B3. Common region
1. **Principle.** Common region: elements inside a shared boundary or background are grouped. This cue can override proximity. Sources: Palmer (1992); NN/g "Common Region".
2. **Question.** List every bounded region (card, box, shaded band). For each, list what it contains, and say whether everything inside belongs together and whether anything that belongs with it sits outside. Name any region that splits a unit or merges two.
3. **Measure.** Enumerate elements with a non-transparent background, a border or a box-shadow. Check DOM containment against the content's units. Nested boxes three or more deep count as a density finding (see M1).
4. **Seed.** Put a step's instruction inside a card and its screenshot just outside the card.

### B4. Alignment
1. **Principle.** Alignment: every element should have a visual connection to something else on the page. Shared edges create order. Sources: Williams (alignment); Müller-Brockmann, *Grid Systems*.
2. **Question.** List the distinct left edges (x positions) that text and figures start at in the main column. For each edge, list what uses it. Name the elements that sit off every shared edge by a small amount.
3. **Measure.** Collect `rect.left` for block elements and cluster them. Edges within 1 to 7 px of each other are near-misses, which read as errors. **Rule of thumb:** three or four intentional edges in a reading column. Check that centred and left-aligned text are not mixed in one column.
4. **Seed.** Indent one figure by 6 px. Or centre a single paragraph inside left-aligned prose.

### B5. Continuity
1. **Principle.** Good continuation: the eye follows lines and curves, and aligned sequences read as one path. Sources: Wertheimer; Koffka.
2. **Question.** Trace the path your eye takes through a multi-step sequence (steps, a flow diagram, a timeline). List the order you perceive. List the order the content intends. Name where the path breaks, jumps or reverses.
3. **Measure.** For sequenced items, check that their positions increase monotonically (top-to-bottom, or left-to-right then wrapping). Look for grid wraps at narrow widths that reorder steps visually.
4. **Seed.** Lay out steps 1 to 4 in a 2×2 grid that reads 1, 3 / 2, 4 at tablet width.

### B6. Closure
1. **Principle.** Closure: the mind completes incomplete shapes. Implied boundaries can group without drawn lines, and broken ones can mislead. Sources: Gestalt psychology; Koffka.
2. **Question.** List the groups the page implies without drawing a boundary (aligned columns, a set of cards with ragged ends). Say whether each implied shape is complete at every width, and name any group whose implied edge is broken by an orphan.
3. **Measure.** At each width, check grids for a single orphaned last item or uneven row ends that break the implied rectangle. **Human eye**.
4. **Seed.** Use a five-card grid in three columns so the last row holds two cards with no visual resolution.

### B7. Figure-ground
1. **Principle.** Figure-ground: the reader has to separate the subject from the background without effort. Sources: Rubin (1915); Gestalt psychology.
2. **Question.** For each layered element (text on images, overlays, sticky bars, callouts on tinted bands), state what is figure and what is ground, and whether any region is ambiguous. Quote any text that sits on a busy or patterned background.
3. **Measure.** Find text whose effective background is an image or gradient. Sample the worst-case pixel contrast from a screenshot (see P1). A sticky element with no shadow or border over scrolling content is a finding.
4. **Seed.** Place white heading text over a photo with a light region. Or give a sticky header a transparent background.

### B8. Uniform connectedness
1. **Principle.** Uniform connectedness: elements joined by a line or connector read as related more strongly than by proximity or similarity. Sources: Palmer and Rock (1994).
2. **Question.** List every connecting line or arrow in figures and in page layout. For each, name the two things it joins and say whether the content actually relates them. Name relationships the content states that the figure leaves unconnected.
3. **Measure.** Inspect the SVG paths and their endpoints. **Human eye** for intent.
4. **Seed.** Draw a divider rule that runs between a heading and its own first paragraph, which reads as "these are separate".

---

## C. Spacing systems and rhythm

### C1. Spacing scale
1. **Principle.** A spacing system: a small, fixed set of spacing values (often a 4 or 8 px base) applied consistently. Sources: Material Design (8 dp grid, 4 dp for type); IBM Carbon spacing scale; Nathan Curtis (EightShapes, "Space in Design Systems").
2. **Question.** List every distinct margin, padding and gap value used in the main content. For each, list where it appears. Name values that are one-offs, and pairs of values so close that the difference looks like an error.
3. **Measure.** Collect computed margin, padding and `gap` values and build a histogram. **Rule of thumb:** around 6 to 8 distinct values, mostly multiples of 4 or 8. Values 2 to 6 px apart (such as 14 and 16) are a finding.
4. **Seed.** Set one section's paragraph margin to 13 px and another's to 18 px.

### C2. Vertical rhythm
1. **Principle.** Vertical rhythm: spacing is derived from the body line-height, so the page has a steady cadence. Sources: Bringhurst §2.2 ("Vertical motion"); Butterick ("space between paragraphs").
2. **Question.** Give the body line-height in px. List the space between paragraphs, before and after headings, and around figures and lists, each as a multiple of the line-height. Name the places where the cadence breaks.
3. **Measure.** Divide each vertical gap by the computed body line-height. Values near 0.5, 1, 1.5 or 2 indicate rhythm. Odd fractions throughout indicate none. **Rule of thumb**, not a hard rule on the web.
4. **Seed.** Give lists a top margin of 0 while paragraphs keep 1 em, so lists collide with the preceding text.

### C3. Internal ≤ external
1. **Principle.** The space inside a group is smaller than the space around it (the internal ≤ external rule). Headings attach to what they head. Sources: Gestalt proximity applied (Williams); Butterick (space above a heading > below).
2. **Question.** For every heading, give the gap above it and the gap below it in px. For every card or callout, give its inner padding and its outer margin. Name every case where the inside is roomier than the outside.
3. **Measure.** Heading: `marginTop` / `marginBottom` (effective, after margin collapse, measured from rects) **≥ 1.5 to 2 (rule of thumb)**. Box: padding ≤ the gap between boxes.
4. **Seed.** Set h2 to `margin: 16px 0 32px`.

### C4. Grid and column structure
1. **Principle.** A layout grid: columns and gutters give consistent placement and widths. Sources: Müller-Brockmann; Material responsive layout grid; GOV.UK layout (two-thirds column for reading).
2. **Question.** Describe the column structure you can infer at each width (count, widths, gutters). List any elements whose widths or positions follow no column.
3. **Measure.** Collect `rect.left` and `rect.width` of the major blocks. Look for consistent gutters and widths that fit the grid. For reading pages, the text column should be narrower than the container (see E1).
4. **Seed.** Make one figure 100% wide and another 83% wide, with no grid reason, inside the same column.

---

## D. Chunking and content length

### D1. Chunking
1. **Principle.** Chunking: break content into small, meaningful units so working memory can hold them. Sources: Miller (1956); Cowan (2001, about 4 ± 1 items); NN/g "How Chunking Helps Content Processing".
2. **Question.** List the units this page asks the reader to take in (concepts, steps, options). Give the count per section. Name any section that holds more than about four or five unrelated units without sub-grouping, and any paragraph that carries more than one idea.
3. **Measure.** Count items in lists, steps per section and sentences per paragraph. **Rules of thumb:** paragraphs of about 3 to 5 sentences for web reading (NN/g, GOV.UK); a list longer than about 7 items should be grouped. **Human eye** for what counts as a unit.
4. **Seed.** Merge three steps into one 9-sentence paragraph. Or make a flat 14-item bullet list that mixes two categories.

### D2. Segmenting against the viewport
1. **Principle.** Segmenting: a self-paced lesson is presented in learner-paced segments. A segment should be readable without losing one's place. Sources: Mayer, *Multimedia Learning* (segmenting principle); Sweller (cognitive load).
2. **Question.** At 1280×800 and at 375×667, give the height of each section in viewports. Name any single concept or step whose content (including its figure) spans more than one screen. Say where a reader would have to scroll back to compare an instruction with its picture.
3. **Measure.** Section height / `window.innerHeight`. **Rule of thumb:** an instruction and its figure fit within one viewport on desktop. Lesson pages that run past about 8 to 10 viewports usually want splitting or an in-page index (see K4).
4. **Seed.** Put a 1400 px tall screenshot between an instruction and the step that refers back to it.

### D3. False floor (illusion of completeness)
1. **Principle.** False floor: a layout that looks finished at the fold, so readers do not scroll. Sources: NN/g "Illusion of Completeness"; NN/g "Scrolling and Attention".
2. **Question.** At each test width, describe exactly what is at the bottom edge of the first viewport. Say whether anything there signals that more content follows (cut-off text, a partly visible element) or whether a full-width band or a large gap ends the view cleanly.
3. **Measure.** Find elements whose bottom edge lies within about 40 px of `innerHeight` with a large gap after them. A full-bleed band that ends exactly at the fold is a finding.
4. **Seed.** Make the hero exactly `100vh` tall, with a solid background and no scroll cue.

### D4. Wall of text
1. **Principle.** Scannable text: headings, lists, short paragraphs and emphasis break up text. Sources: NN/g "How Users Read on the Web" (Morkes and Nielsen, 1997: concise, scannable and objective text improved measured usability by 124%); Krug ("omit needless words").
2. **Question.** Find the longest run of text with no heading, list, figure or callout. Give its height in px and its word count. Quote its first sentence, and say whether it could be a list or be split under a sub-heading.
3. **Measure.** Walk the main column for consecutive `<p>` runs. **Rule of thumb:** an unbroken run taller than about one viewport, or longer than about 300 words, is a finding.
4. **Seed.** Convert a numbered procedure into one long prose paragraph.

---

## E. Typography

### E1. Line length (measure)
1. **Principle.** Measure: characters per line. Sources: Bringhurst (45 to 75 characters, 66 ideal); Butterick (45 to 90); Baymard (50 to 75); WCAG 1.4.8 (AAA: ≤ 80).
2. **Question.** For body text at each test width, give the characters per line of three sample lines. Do the same for any text in cards, callouts and captions. Name any text block outside the range.
3. **Measure.** Count the characters on a rendered line with a Range: walk the text node and break where `getClientRects()` changes top. **Rule of thumb: 45 to 75 for body text, 40 to 50 minimum on phones. Over 90 is a finding.** Check `max-width` on the text column.
4. **Seed.** Remove `max-width` from the article so body text runs the full 1280 px (about 160 characters).

### E2. Body size
1. **Principle.** A comfortable body size for screen reading. Sources: Butterick (15 to 25 px on the web); GOV.UK (19 px body at desktop); USWDS (16 px minimum, body often 17 to 18 px).
2. **Question.** Give the computed body font-size at desktop and phone widths, and the smallest text size used anywhere that is meant to be read (captions, table cells, footnotes, figure labels).
3. **Measure.** Computed `font-size`. **Rule of thumb:** body ≥ 16 px. Any reading text < 12 px is a finding. Factor in x-height: fonts with a small x-height need to be larger.
4. **Seed.** Set table cells and figure captions to 11 px.

### E3. Line height (leading)
1. **Principle.** Leading proportional to measure and size. Sources: Butterick (120 to 145% of size); WCAG 1.4.12 (the content must survive 1.5); Bringhurst.
2. **Question.** Give the line-height ratio for body text, headings, list items and captions. Name any multi-line heading whose lines look too far apart, and any body text whose lines crowd.
3. **Measure.** `lineHeight / fontSize`. **Rule of thumb:** body 1.4 to 1.6; headings 1.1 to 1.3; long lines need more.
4. **Seed.** Set body to `line-height: 1.1`. Or set a 40 px H1 to `line-height: 1.6`.

### E4. Type scale
1. **Principle.** A modular type scale: a small set of sizes related by a ratio. Sources: Bringhurst ("the classic scale"); Tim Brown (Modular Scale); Material type scale.
2. **Question.** List every distinct font-size on the page with what uses it. Name sizes that are too close to read as different levels and sizes used only once.
3. **Measure.** Histogram of computed `font-size`. **Rule of thumb:** about 5 to 7 sizes. Adjacent steps should differ by a ratio of at least about 1.125 to 1.2. Pairs like 15 and 16 px are a finding.
4. **Seed.** Add a 17 px subtitle next to 16 px body and 18 px H4.

### E5. Typeface count and pairing
1. **Principle.** Restraint in typefaces: one or two families, each with a role. Sources: Lupton (*Thinking with Type*); Butterick ("font recommendations"); Williams (contrast between typefaces, not conflict).
2. **Question.** List every font family actually rendered (not just declared) and what it is used for. Name any two families that are similar but not the same (a conflict), and any fallback font showing because a web font failed to load.
3. **Measure.** `document.fonts` and the computed `font-family`. Check which face rendered via DevTools "Rendered Fonts". **Rule of thumb:** ≤ 2 families plus monospace for code.
4. **Seed.** Use Arial for body and Helvetica for headings. Or break the web font URL so the serif fallback renders.

### E6. Alignment, rag and hyphenation
1. **Principle.** Flush-left, ragged-right text on screens. Avoid justified text without hyphenation, and avoid centred multi-line text. Sources: Bringhurst §2.1; Butterick ("justified text"); WCAG 1.4.8 (AAA: not justified).
2. **Question.** Give the alignment of each text block. For any justified block, quote a line with visible rivers or wide word gaps. Quote any centred block longer than two lines.
3. **Measure.** Computed `text-align` and `hyphens`. Justified text without `hyphens:auto` in a narrow column is a finding.
4. **Seed.** Set `text-align: justify` on body text in a 320 px column.

### E7. Case and style in running text
1. **Principle.** Readable letterforms: avoid long runs of all caps, italic or light weights. Letter-space caps when you use them. Sources: Butterick ("all caps", "letterspacing"); Bringhurst.
2. **Question.** Quote every run of all caps longer than a few words, every italic passage longer than a sentence, and every text set in a weight below 400. Give the letter-spacing on caps.
3. **Measure.** Computed `text-transform`, `font-style`, `font-weight` and `letter-spacing`. **Rule of thumb:** caps get about 5 to 12% tracking. Body weight ≥ 400. A light weight combined with low contrast compounds the P1 contrast problem.
4. **Seed.** Set callout bodies in uppercase at weight 300 with no tracking.

### E8. Code, numbers and data text
1. **Principle.** Tabular (monospaced) figures in columns. Code is visually distinct and does not overflow. Sources: Butterick ("tables", "alternate figures"); Bringhurst §3.2; GOV.UK (tabular numbers).
2. **Question.** In each numeric table column, compare the digit widths across rows: do the figures line up? For each code block, give its font size against body text and say whether it scrolls, wraps or overflows its container at 375 px.
3. **Measure.** `font-variant-numeric: tabular-nums` on numeric cells. For code: `scrollWidth > clientWidth` with visible overflow is a finding. Code size should be about 85 to 95% of body.
4. **Seed.** Right-align a proportional-figure column. Or give `<pre>` `white-space: pre` with no `overflow-x`.

---

## F. Emphasis budget

### F1. Emphasis budget
1. **Principle.** Emphasis is a scarce resource: use one method (bold or italic, not both, and not underline, which signals a link), sparingly. When everything is emphasised, nothing is. Sources: Butterick ("bold or italic", "underlining"); Tufte (smallest effective difference); Williams.
2. **Question.** List every emphasised span (bold, italic, colour, highlight, caps) per section, with its words. Count them per 100 words. Say which ones the reader would lose something without, and which only repeat what a heading already says.
3. **Measure.** Count `<strong>`, `<b>`, `<em>`, `<mark>` and coloured spans, plus elements with weight ≥ 600 inside paragraphs. Divide by the word count. **Rule of thumb:** more than about 1 emphasis per paragraph, or more than ~5% of words, is a finding. Underlined text that is not a link is always a finding.
4. **Seed.** Bold one phrase in every sentence of a section, and underline a non-link term.

### F2. Callout and admonition budget
1. **Principle.** Callouts work by exception. Too many boxes cause banner blindness and flatten the hierarchy. Sources: GOV.UK design system (inset text and warning text: "use sparingly"); NN/g "Banner Blindness"; Material (emphasis levels).
2. **Question.** List every callout, alert or boxed note with its type and its first sentence. Give the count per viewport. For each, say whether its content is truly exceptional or simply body text in a box.
3. **Measure.** Count elements with role/class of alert, note or callout, or with a tinted background, in the main column. **Rule of thumb:** more than ~1 per viewport, or more than ~3 per page section, is a finding. Warnings should be rarer than notes.
4. **Seed.** Wrap every second paragraph of a lesson in a "Tip" or "Important" box.

---

## G. Colour

### G1. Colour carries consistent meaning
1. **Principle.** Colour coding: each colour that carries meaning keeps that meaning everywhere, and conventional meanings are respected (red for error or danger, green for success). Sources: Few, *Information Dashboard Design*; Ware; Material and Carbon (status colour tokens).
2. **Question.** List every non-neutral colour on the page with each place it is used and what it seems to mean there. Name any colour with two meanings, any meaning shown in two colours, and any use that conflicts with convention.
3. **Measure.** Collect computed `color`, `background-color`, `border-color` and SVG `fill`/`stroke`. Cluster them (ΔE < ~5 counts as the same colour) and map each cluster to its roles.
4. **Seed.** Use red for a figure's "primary path" and also for error messages. Or use green for both "success" and "link".

### G2. Colour is not the only cue
1. **Principle.** Use of colour (WCAG 1.4.1, level A): colour must not be the only visual means of conveying information. About 8% of men have a colour vision deficiency. Sources: WCAG 2.2; Few.
2. **Question.** List every distinction the page conveys by colour: chart series, status, links in text, required fields, highlighted rows. For each, name the second cue (text, shape, pattern, underline, icon), or state that none exists.
3. **Measure.** Render in greyscale and with DevTools "Emulate vision deficiencies" (protanopia, deuteranopia, achromatopsia), and re-run the question. Links in text that are not underlined need 3:1 contrast with the surrounding text plus a non-colour cue on hover and focus (WCAG technique G183).
4. **Seed.** Show a two-series line chart in red and green, with a legend but no direct labels and no line-style difference.

### G3. Palette restraint
1. **Principle.** A restrained palette: neutrals plus one accent plus semantic colours. Sources: Tufte (*Envisioning Information*, "above all, do no harm" with colour); Few; Material colour system (primary, secondary, surface, error).
2. **Question.** Count the distinct hues on the page. For each, say what job it does. Name hues that do no job.
3. **Measure.** Hue histogram from computed colours (or k-means on a screenshot). **Rule of thumb:** one or two accent hues plus semantic colours. Five or more unrelated hues in a reading page is a finding.
4. **Seed.** Give each section header its own colour.

### G4. Dark-mode parity
1. **Principle.** Theme parity: every colour meaning and contrast holds in both colour schemes. Sources: Material dark theme guidance (avoid pure black, elevated surfaces lighter); Apple HIG Dark Mode; WCAG (contrast applies to every theme offered).
2. **Question.** In dark mode, repeat P1 and G1 for the same elements. List every element that disappears, inverts its meaning, or keeps a hard-coded light background (images, SVG, code blocks).
3. **Measure.** Emulate `prefers-color-scheme: dark` and re-run the contrast checks. Find SVGs with hard-coded `fill="#000"`, and images with transparent backgrounds that hold dark line art.
4. **Seed.** Use an inline SVG diagram with black strokes on a transparent background.

---

## H. Scanning patterns

### H1. F-pattern and other scanning patterns
1. **Principle.** Readers scan rather than read. The F-pattern appears when the page gives poor cues. Good formatting produces layer-cake or spotted scanning instead. Sources: NN/g eyetracking ("F-Shaped Pattern", 2006 and 2017 update; "Text Scanning Patterns").
2. **Question.** Read only the left edge of the main column (the first two words of each line and block). Write down what you learn. Then list the key facts the page needs to convey, and mark which ones would be found that way and which are buried mid-line or at the right.
3. **Measure.** For each key term or instruction, record its x-offset within its line (via a Range rect). Key information starting past ~60% of the line width on desktop is a finding. **Human eye** to decide what is key.
4. **Seed.** Put the critical value or the action at the end of a long sentence in the middle of a paragraph.

### H2. Layer-cake scanning
1. **Principle.** Layer-cake pattern: readers jump from heading to heading. Headings must carry the story alone. Sources: NN/g "Layer-Cake Pattern of Scanning Content".
2. **Question.** Copy out only the headings, in order. Read them as an outline and say what the page tells you and in what sequence. Name gaps (sections with no heading taller than ~1 viewport) and headings that tell you nothing.
3. **Measure.** Extract `h1` to `h6` text. Compute the px distance between consecutive headings. **Rule of thumb:** a gap greater than about 1.5 viewports with no heading is a finding on reading pages.
4. **Seed.** Remove the H3s from a long section, leaving 2500 px of prose under one H2.

### H3. Lists, tables and parallel structure
1. **Principle.** Parallel content belongs in parallel form: lists for sets, numbered lists for sequences, tables for comparisons on more than one attribute. Sources: NN/g ("Bullet points", "Tables vs lists"); GOV.UK; Butterick ("bulleted and numbered lists").
2. **Question.** Find content written as prose that is really a set, a sequence or a comparison. Quote it. For each existing list, say whether its items are grammatically parallel, and whether a numbered list is used only where order matters.
3. **Measure.** Detect sentences in a paragraph that start with ordinal words ("First", "Then", "Next") or that repeat a "X: Y" pattern. **Human eye** for parallelism.
4. **Seed.** Write a 5-step procedure as prose, and make a bullet list where items mix fragments and full sentences.

### H4. Banner blindness
1. **Principle.** Readers ignore anything that looks like an ad or boilerplate: bright boxes, right rails, full-width banners. Sources: Benway and Lane (1998); NN/g "Banner Blindness Revisited".
2. **Question.** List every element styled as a banner, a right-rail box or a promo-like card. For each, say whether it holds content the reader needs. If it does, name it as at risk.
3. **Measure.** Find elements in a sidebar, or full-width saturated bands, that contain instructions or required information. **Human eye**.
4. **Seed.** Put the lesson's prerequisite in a bright, full-width, ad-like banner at the top.

---

## I. Actions and links

### I1. Link affordance
1. **Principle.** Signifiers: links have to look clickable. Underlined, coloured text is the convention in body copy. Sources: Norman (signifiers); NN/g "Guidelines for Visualizing Links"; Krug (conventions); WCAG 1.4.1.
2. **Question.** List every link in the body text with its styling. List every non-link element styled like a link (coloured or underlined). For each link, say how a reader without hover would know it is a link.
3. **Measure.** For `a[href]` inside paragraphs: `text-decoration-line` includes underline, or there is colour contrast ≥ 3:1 with the surrounding text plus a non-colour cue on focus or hover. Find non-anchors with link-like colour and underline. Visited state: `a:visited` is distinct where useful.
4. **Seed.** Remove the underline from body links and set their colour to #333 against #222 text.

### I2. Link text
1. **Principle.** Link purpose: link text describes its destination. Sources: WCAG 2.4.4 (A); NN/g "'Learn More' Links: You Can Do Better"; GOV.UK.
2. **Question.** List the text of every link out of context, as a screen-reader links list would show it. Name the links that are ambiguous ("here", "click here", "more", a bare URL), and duplicates with different destinations.
3. **Measure.** Collect `a.textContent` and `href`. Flag a generic-phrase list, identical text with different hrefs, and URLs as link text.
4. **Seed.** Change three links to "click here".

### I3. Primary action salience
1. **Principle.** A clear primary action: one dominant call to action per view, with secondary actions de-emphasised. Sources: Material (button emphasis levels); GOV.UK (one primary button per page); Hick's law.
2. **Question.** List every button and button-like link in each viewport with its visual weight (filled, outlined, text). Say which one a reader would take to be the main next step, and whether that is the one the page intends.
3. **Measure.** Count filled or high-contrast buttons per viewport. **Rule of thumb:** ≤ 1 primary per view. Check that the primary's background-to-page contrast ≥ 3:1 (WCAG 1.4.11).
4. **Seed.** Style "Skip this lesson" as a filled primary button next to an outlined "Continue".

### I4. Target size
1. **Principle.** Fitts's law: bigger, nearer targets are faster to hit. Target size minimum is WCAG 2.5.8 (AA). Sources: Fitts (1954); WCAG 2.2; Apple HIG (44 pt); Material (48 dp).
2. **Question.** List every interactive element smaller than 24×24 px at phone width, with its size and its distance to the nearest other target.
3. **Measure.** `getBoundingClientRect` on interactive elements. **WCAG 2.5.8: ≥ 24×24 CSS px**, or spacing so that a 24 px circle centred on the target does not intersect another target. Inline links in sentences are exempt. **Rule of thumb:** 44 to 48 px for touch.
4. **Seed.** Make icon-only "copy" buttons 16×16 px, placed 4 px apart.

### I5. Interaction states
1. **Principle.** Feedback and state visibility: hover, focus, active, visited and disabled are each visibly distinct. Sources: Nielsen heuristic 1 (visibility of system status); Material (state layers).
2. **Question.** For each kind of interactive element, describe its default, hover, focus and (where relevant) visited and disabled appearance. Name states that look the same as another state.
3. **Measure.** Force states in DevTools (`:hover`, `:focus-visible`, `:active`) and diff the computed styles. A state with no style difference is a finding (see P3 for focus).
4. **Seed.** Set `button:disabled` to look identical to enabled.

### I6. Hover-only and hidden affordances
1. **Principle.** Do not hide what the reader needs behind hover or mystery icons. Touch has no hover. Sources: NN/g "Hover-only" and "Icon usability" (label icons); WCAG 1.4.13.
2. **Question.** List every piece of content or control that appears only on hover, and every icon with no visible label. For each, say how a touch user or a keyboard user reaches it.
3. **Measure.** Find elements with `opacity:0` or `visibility:hidden` toggled by `:hover`. Find buttons whose accessible name is absent or whose only content is an icon.
4. **Seed.** Make the "copy prompt" button appear only on hover over the code block.

---

## J. Consistency

### J1. Internal consistency
1. **Principle.** Consistency and standards (Nielsen heuristic 4). Repetition (Williams). The same thing looks and behaves the same way everywhere. Sources: Nielsen (1994); Williams; design systems in general.
2. **Question.** Pick three repeated components (step blocks, figures with captions, callouts, buttons). For each, list every instance with its computed style differences. Name the instances that differ without reason.
3. **Measure.** Group elements by class or role and diff their computed styles (size, spacing, colour, radius). Any difference within a role is a finding unless it is intended.
4. **Seed.** Give one figure caption italic 14 px and the rest regular 15 px. Or give one step's number a different shape.

### J2. Cross-page consistency
1. **Principle.** Consistent navigation (WCAG 3.2.3, AA) and consistent identification (3.2.4, AA): repeated navigation keeps its order, and the same function has the same label. Sources: WCAG 2.2; Krug (conventions).
2. **Question.** Across two or three pages of the same site, list the navigation items and their order, the labels of repeated functions, and the page template regions. Name any differences.
3. **Measure.** Extract nav link texts and order on each page and diff them. Diff the button labels for the same action.
4. **Seed.** Label "Next lesson" on one page and "Continue" on another, and swap the order of two nav items.

---

## K. Navigation and wayfinding

### K1. You are here
1. **Principle.** Wayfinding and Krug's trunk test: on any page, a reader can tell what site this is, what page this is, the major sections, where they are in the structure, and how to search or go back. Sources: Krug, *Don't Make Me Think*, ch. 6; Lynch (*The Image of the City*), applied to the web.
2. **Question.** From a screenshot of a mid-site page at phone width (with no URL bar), answer the five trunk-test questions and quote the on-page evidence for each one.
3. **Measure.** Check for: a site identifier, an H1 that matches the `<title>`, a current-location indicator (`aria-current` on the nav item or breadcrumb), and a visible route home. Note any that is missing.
4. **Seed.** Remove `aria-current` styling and the breadcrumb, and make the H1 generic ("Lesson").

### K2. Progress and sequence in a course
1. **Principle.** Progress indicators and sequential navigation for linear content. Sources: NN/g ("Progress indicators", "Wizards"); Nielsen heuristic 1; Mayer (signalling).
2. **Question.** On a lesson page, say which lesson this is out of how many, what came before, and what comes next, using only what the page shows. Give the location of the next/previous controls at the end of the content and their labels.
3. **Measure.** Check for "n of N" text or a progress element, and prev/next links at both top and bottom, or at least at the bottom. Check that the links point to the adjacent pages.
4. **Seed.** Remove the "Lesson 3 of 7" label and keep only a bare "→" icon at the bottom.

### K3. Page title and heading identity
1. **Principle.** Page titled (WCAG 2.4.2, A). Headings and labels (2.4.6, AA): titles and headings describe topic or purpose. Sources: WCAG 2.2; NN/g (page titles).
2. **Question.** Quote the `<title>` and the H1. Say whether a reader seeing only the browser tab, or only the H1, would know which page among the site's pages this is.
3. **Measure.** `document.title` is unique across the site and front-loaded with the page-specific part. There is exactly one H1.
4. **Seed.** Give every page the same `<title>`, the site name.

### K4. In-page navigation for long pages
1. **Principle.** Tables of contents and anchor links for long documents. Sources: NN/g ("In-page links", "Table of contents"); GOV.UK (contents list on long guidance).
2. **Question.** Give the page length in viewports. If it is long, say how a reader would jump to section 4, return to the top, and know which section they are in mid-scroll.
3. **Measure.** Page height / `innerHeight`. **Rule of thumb:** above about 5 viewports with 4 or more sections, an in-page contents list is expected. Anchors should land with the heading visible, not hidden under a sticky header (check `scroll-margin-top`).
4. **Seed.** Add a sticky 80 px header with no `scroll-margin-top`, so anchor jumps hide the target heading.

---

## L. Figures and diagrams

### L1. Figure legibility at rendered size
1. **Principle.** Legibility after scaling: text inside a figure must meet body-text minimums at its displayed size, not its source size. Sources: Tufte; Few; WCAG 1.4.3 and 1.4.5 (images of text).
2. **Question.** For each figure, give its displayed width and the rendered height of its smallest text, at desktop and phone widths. Name every label you cannot read without zooming.
3. **Measure.** Rendered text size = source text size × (displayed width / natural width). For a raster image, use `naturalWidth` and `clientWidth`. For SVG, use the scaled `font-size` via `getBoundingClientRect` on `<text>`. **Rule of thumb:** ≥ 12 px rendered, and ideally near body size. Contrast within the figure per P1.
4. **Seed.** Insert a 2400 px wide screenshot scaled down to 700 px, so its 14 px UI text renders at about 4 px.

### L2. Spatial contiguity and direct labelling
1. **Principle.** Spatial contiguity: words go near the graphics they describe. Direct labels beat legends. Sources: Mayer (spatial contiguity principle); Tufte (*Visual Display*, integrating text and graphic); Few.
2. **Question.** For each figure, list where its caption, its legend and the text that refers to it sit, with distances in px. For each chart, count how many series a reader must decode through a legend rather than a direct label.
3. **Measure.** Distance from the figure rect to its caption and to the first paragraph that references it. **Rule of thumb:** the caption touches its figure (gap < the paragraph gap), and the reference text lies within a viewport. A legend with more than about 3 entries is a finding where direct labels would fit.
4. **Seed.** Put all figure captions in a list at the end of the page. Or use a 6-entry legend below a chart.

### L3. Data-ink and chartjunk
1. **Principle.** Maximise the data-ink ratio and erase non-data ink (heavy gridlines, 3D, decorative fills). Sources: Tufte, *The Visual Display of Quantitative Information*; Few, *Show Me the Numbers*.
2. **Question.** For each chart or diagram, list every non-data element (gridlines, borders, backgrounds, shadows, 3D, icons, gradients). For each, say what the reader would lose if it were removed.
3. **Measure.** Inspect SVG or canvas elements: count gridlines, borders, gradient and shadow filters. 3D and pie charts with more than ~5 slices are standard findings (Few). **Human eye** for the overall judgment.
4. **Seed.** Add a 3D effect and dark gridlines at every unit to a bar chart.

### L4. Figure earns its place
1. **Principle.** The coherence principle: exclude extraneous words, pictures and sounds. The signalling principle: cue what matters. Decorative images hurt learning. Sources: Mayer; Clark and Mayer, *e-Learning and the Science of Instruction*; NN/g ("Photos as web content").
2. **Question.** For each image, state what the reader can learn or do from it that the text does not already give. Name purely decorative images, and screenshots in which the reader cannot tell where to look (no highlight, crop or callout).
3. **Measure.** Count images per section, decorative images (`alt=""`) in the main column, and screenshots with no annotation overlay. **Human eye**.
4. **Seed.** Insert a stock photo at the top of every lesson. Or use an uncropped full-desktop screenshot where the target button is 2% of its area.

---

## M. Density and whitespace

### M1. Density appropriate to the task
1. **Principle.** Information density matched to reader and task. Reference displays can be dense; learning pages need room. Whitespace is active, not wasted. Sources: Tufte (high data density for analysis); Lupton (white space as an active element); Material ("density" guidance); Sweller (extraneous load).
2. **Question.** Describe the page's density: boxes per viewport, levels of nesting, the proportion of the viewport that is text against empty space. Say whether that suits who reads it and why. Name the most crowded region and the emptiest one.
3. **Measure.** Ink coverage from a screenshot (non-background pixel %), elements with borders per viewport, and the maximum nesting depth of bordered boxes. **Rule of thumb:** nested boxes three or more deep, or margins < 16 px at phone width, are findings. **Human eye** for fit to task.
4. **Seed.** Put a bordered card inside a bordered card inside a shaded panel, with 8 px padding throughout.

### M2. Micro-whitespace and crowding
1. **Principle.** Breathing room around text inside containers, and side gutters. Sources: Lupton; Material (padding); GOV.UK (gutters, 15 px on mobile).
2. **Question.** List every container whose text comes within 12 px of its border, and the side gutter at 320 and 375 px.
3. **Measure.** Computed padding of text containers. Distance from text rect to container rect. **Rule of thumb:** ≥ 12 to 16 px internal padding, and ≥ 16 px page gutter on phones.
4. **Seed.** Set `.callout { padding: 4px }` and `body { margin: 0 }` with no container padding.

---

## N. Tables

### N1. Table design
1. **Principle.** Tables are for reading across and down. Align numbers right and text left, use minimal rules, and keep headers clear. Sources: Butterick ("tables"); Few (*Show Me the Numbers*, ch. 8); Tufte; GOV.UK table component.
2. **Question.** For each table, list its column alignments, its rules and borders, and the header treatment. Name columns whose alignment fights their content, and say whether a reader can follow a row across without losing it. At 375 px, describe what happens to the table.
3. **Measure.** Computed `text-align` per column. Count borders (a full grid is a finding where light horizontal rules would do). `th` elements with `scope` are present. At narrow widths: the table scrolls in its own container (`overflow-x:auto`) rather than overflowing the page.
4. **Seed.** Centre-align a currency column, give every cell a 1 px black border, and let the table overflow the page at 375 px.

---

## O. Responsive behaviour

### O1. Reflow
1. **Principle.** Reflow (WCAG 1.4.10, AA): content works at 320 CSS px width without two-dimensional scrolling, apart from content that needs 2D layout (tables, maps, diagrams). Sources: WCAG 2.2; Marcotte (*Responsive Web Design*).
2. **Question.** At 320 px, list every element that causes horizontal page scroll, gets clipped, or overlaps another. For each, give its width.
3. **Measure.** `document.documentElement.scrollWidth > clientWidth` is a failure. Find culprits where `el.getBoundingClientRect().right > innerWidth`. Also test at 1280 px with 400% zoom.
4. **Seed.** Give a figure `width: 600px` with no `max-width: 100%`.

### O2. Intermediate widths and breakpoints
1. **Principle.** Content-out breakpoints: the layout holds at every width, not just at named devices. Sources: Marcotte; Material responsive layout; Brad Frost (*Atomic Design*); the content-first breakpoint advice of the field.
2. **Question.** Sweep the width from 320 to 1600 px. List each width where something breaks: awkward line length, orphaned grid items, collisions, a sidebar squeezing the text column below ~45 characters.
3. **Measure.** Resize in 40 px steps and re-run E1 (characters per line), O1 (overflow) and B6 (orphans) at each step. Look at the widths just above and below each media-query breakpoint.
4. **Seed.** Use a two-column layout that switches to one column only at 600 px, so at 700 px the text column is about 30 characters wide.

### O3. Touch and viewport behaviour
1. **Principle.** Mobile viewport and touch ergonomics: correct viewport meta, no zoom lock, sticky elements that do not eat the screen. Sources: WCAG 1.4.4 (resize text); Apple HIG; Material; NN/g ("Sticky headers").
2. **Question.** At 375×667, give the height of every fixed or sticky element and the share of the viewport they take together. Say whether pinch-zoom works.
3. **Measure.** The viewport meta has no `user-scalable=no` or `maximum-scale=1`. Sum the heights of `position: fixed|sticky` elements / `innerHeight`. **Rule of thumb:** ≤ about 15 to 20% of the viewport.
4. **Seed.** Add a 90 px sticky header, a 60 px sticky footer, and `maximum-scale=1`.

### O4. Layout stability
1. **Principle.** Visual stability: content should not jump while the reader reads. Sources: Google Core Web Vitals (Cumulative Layout Shift); NN/g (layout shift frustration).
2. **Question.** Load the page and start reading the first paragraph. List every shift that moves the text you were reading, with its cause (an image without dimensions, a late font, an injected banner).
3. **Measure.** CLS from a Lighthouse or Performance trace. **Rule of thumb (Google): CLS ≤ 0.1 is good.** Images without `width` and `height` or an `aspect-ratio` are likely causes.
4. **Seed.** Remove the width and height attributes from the images above the fold.

---

## P. Accessibility (WCAG 2.2 AA)

### P1. Text contrast
1. **Principle.** Contrast minimum (WCAG 1.4.3, AA). Sources: WCAG 2.2.
2. **Question.** List every text style on the page (body, muted, caption, link, placeholder, text on coloured backgrounds, figure labels, code) with its foreground, its effective background and its ratio. Name each one below threshold.
3. **Measure.** **WCAG: ≥ 4.5:1 for normal text; ≥ 3:1 for large text (≥ 24 px, or ≥ 18.66 px bold).** For text on images, sample the worst-case pixels. Check both colour schemes. Disabled controls and logos are exempt.
4. **Seed.** Set the muted caption colour to #999 on #fff (2.85:1).

### P2. Non-text contrast
1. **Principle.** Non-text contrast (WCAG 1.4.11, AA): UI component boundaries, states, and the graphical objects needed to understand content reach 3:1 against what is adjacent. Sources: WCAG 2.2.
2. **Question.** List input borders, button outlines (where the outline identifies the button), focus indicators, icons that carry meaning, and chart lines and segments. Give each one's contrast against its adjacent colour.
3. **Measure.** **WCAG: ≥ 3:1** against adjacent colours. For charts, check adjacent segments against each other or against a separator.
4. **Seed.** Give text inputs a 1 px #ddd border on white. Or draw a chart's two series in #8ab4f8 and #a1c2fa.

### P3. Focus visible and not obscured
1. **Principle.** Focus visible (2.4.7, AA). Focus not obscured, minimum (2.4.11, AA). Focus appearance (2.4.13) is AAA, but it is a useful bar. Sources: WCAG 2.2.
2. **Question.** Tab through the page. For each stop, describe the focus indicator and whether it is fully hidden by a sticky header, a footer or an overlay. List the stops in order and name any whose order does not match the visual order (2.4.3, A).
3. **Measure.** Check that `:focus-visible` styles exist (no `outline: none` without a replacement). After each Tab, compare the focused element's rect against the rects of fixed elements. A complete overlap fails 2.4.11. **Rule of thumb (from 2.4.13):** an indicator ≥ 2 px thick with 3:1 change contrast.
4. **Seed.** Add `*:focus { outline: none }` and a sticky footer that covers links near the bottom.

### P4. Text resize and text spacing
1. **Principle.** Resize text (1.4.4, AA: 200% without loss) and text spacing (1.4.12, AA: content survives user spacing overrides). Sources: WCAG 2.2.
2. **Question.** Apply 200% text zoom, then the 1.4.12 spacing overrides. List every element that clips, overlaps or truncates text.
3. **Measure.** Inject `* { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important } p { margin-bottom: 2em !important }`. Find elements with `scrollHeight > clientHeight` and `overflow: hidden`, and fixed-height containers holding text.
4. **Seed.** Give buttons and cards a fixed `height: 40px` with `overflow: hidden`.

### P5. Structure and semantics
1. **Principle.** Info and relationships (1.3.1, A). Headings and labels (2.4.6, AA). Meaningful sequence (1.3.2, A). The visual structure is present in the markup. Sources: WCAG 2.2; WAI-ARIA Authoring Practices.
2. **Question.** List the heading outline as a screen reader announces it, and compare it with the visual outline. Name skipped levels, things that look like headings but are not marked up as headings, visual lists that are not marked as lists, and landmark regions that are missing.
3. **Measure.** Extract the `h1` to `h6` sequence (look for skips) and elements with large or bold text that are not headings. Check for `main`, `nav` and `header`. Run axe-core or a Lighthouse accessibility audit for automated checks. These catch about 30 to 40% of issues, so they are not a pass on their own.
4. **Seed.** Make section titles `<div class="title">` styled like H2, and jump from H2 to H4.

### P6. Text alternatives
1. **Principle.** Non-text content (1.1.1, A): every meaningful image has an equivalent text alternative, and decorative images are hidden. Sources: WCAG 2.2; W3C WAI alt-text decision tree.
2. **Question.** For each image and SVG, quote its alt text or accessible name and say whether a reader who cannot see the image would get the same information. For diagrams, say where the full description is.
3. **Measure.** `img` without an `alt` attribute (a failure), alt equal to a filename, `alt` on decorative images that should be empty, and SVG without `role="img"` plus `aria-label` or `<title>`. **Human eye** for equivalence.
4. **Seed.** Give a process diagram `alt="diagram"`.

### P7. Motion, hover and timing
1. **Principle.** Pause, stop, hide (2.2.2, A). Content on hover or focus (1.4.13, AA: dismissible, hoverable, persistent). Respect `prefers-reduced-motion` (2.3.3 is AAA, but it is common practice). Sources: WCAG 2.2.
2. **Question.** List every animation, auto-advancing element and hover popup. For each, say how a reader stops it, dismisses it with Esc, or moves the pointer onto it without it vanishing.
3. **Measure.** Find animations longer than 5 seconds with no control, tooltips that close when the pointer moves onto them, and the absence of an `@media (prefers-reduced-motion)` rule.
4. **Seed.** Add an auto-rotating carousel of tips with no pause control.

---

## Q. Whole-page critique

### Q1. Coherence of the whole
1. **Principle.** Unity and the aesthetic-usability effect: a coherent visual system earns trust and patience. Readers judge credibility from visual design in about 50 ms. Sources: Kurosu and Kashimura (1995); Lindgaard et al. (2006); Fogg (Stanford web credibility); Williams (repetition).
2. **Question.** Describe the page's visual system in three sentences (type, colour, spacing, components). Then list every element that does not belong to that system.
3. **Measure.** Combine the outliers from C1, E4, G3 and J1. **Human eye** for the overall impression.
4. **Seed.** Paste in one section copied from another site, with its own font, colours and button style.

### Q2. Fit to the reader's task
1. **Principle.** User-centred fit: the form serves the reader's job (learn and do, decide, look up). Sources: Norman; Krug; Clark and Mayer (learning pages); Few (decision displays).
2. **Question.** State who reads this page and what they need to do next. Walk that task on the rendered page, step by step, and list each point where the design slows or misleads them, citing the item number above.
3. **Measure.** None in itself: this question is answered by walking the task. **Human eye**. The other items supply the evidence.
4. **Seed.** On a lesson page, put the "try it" exercise below an optional deep-dive section, so learners hit the depth before the practice.

### Q3. Print and export behaviour (where the page is a report or briefing)
1. **Principle.** Medium-appropriate output: reports and briefings get printed or saved as PDF. Sources: Butterick (print); W3C CSS Paged Media; GOV.UK (print styles).
2. **Question.** Print-preview the page. List the content lost or broken: navigation printed, backgrounds dropped that carried meaning, figures split across pages, links printed with no URLs.
3. **Measure.** Emulate the `print` media type. Check `@media print` rules and `break-inside: avoid` on figures and tables. Colour meaning should survive greyscale (see G2).
4. **Seed.** Encode status only through background colours that browsers drop in print.

---

## Items with no reliable measurement (need a human eye)

A1 (final hierarchy call), A3 (quality of the information scent), A4, B6, B8, D1 (what counts as a unit), H1 (what is key), H3 (parallelism), H4, L3 (overall chartjunk judgment), L4, M1 (fit of density to task), P6 (equivalence of the text alternative), Q1, Q2. For these the reviewer still gathers measured evidence: positions, counts, quotations. The verdict is a person's judgment.
