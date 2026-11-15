# Design review questions, by kind of artifact

The questions a reviewer answers about a rendered artifact before the person it is for sees it. Each kind has a short
set drawn from `catalog.md` (the design field's checks, with sources). The catalog is
the reference behind them; the reviewer works from the set for its kind, so a review takes minutes.

**How every question is answered.** From the reader's seat, on the rendered artifact. Open it
yourself in a browser, never from screenshots someone else chose. Look at it at desktop width and at
phone width, in light and dark theme when it has both, and walk every state a reader meets: each
step, tab, lens, open fold and clicked or selected state. The request names the states; walk each
one, and say which you walked. In every state, run `measure-text.md` and use its numbers as evidence. The answer is something you produce: a list, a measurement, a quotation, never "OK".
Then say where what you produced differs from what the artifact is meant to do. The artifact fails
until the evidence shows otherwise. If a question cannot apply (no figures, no tables), say so.

**Why this form.** On a lesson page whose steps do not group, "does spacing vary by level of
structure?" passes it; "list the chunks you see against the chunks the author meant" fails it
with the measured gaps.

## Every kind: the five first

1. **Where the eye goes.** The first three things your eye lands on, in order. The three things the
   reader came to do or learn. Where they differ.
2. **Groups seen against groups meant.** In each section, the groups your eye finds from spacing,
   lines, boxes and colour alone, and the groups the content is built from. At each boundary the
   content means, the measured gap (or the line or box that marks it) against the gaps inside.
3. **What competes.** Every treatment that draws attention on one screen (colour, bold, box, badge,
   link style). Which should win, and whether it does.
4. **Same thing, same look.** Each visual treatment and what it is applied to. Any treatment used
   for two different things, and any one thing drawn two ways.
5. **Can it be read.** Every text style `measure-text.md` lists, in every state, width and theme:
   its rendered size, contrast and line height, including small, grey and secondary text and text
   inside pictures. Anything under about 12 px, under 4.5:1 contrast (3:1 for large text and for
   marks that carry meaning), or set with line height under about 1.4 in running text.

## A page to read (briefs, explanations, runbooks, lesson pages, training sites)

6. **Units against the screen.** Each unit of work (a step, a section) and its height at the
   reader's width. Can they see an instruction and its check together?
7. **Section to section.** Moving from one section to the next: the gap or mark between them against
   the largest gap inside one. Does it give a break, or run on?
8. **Line length.** Characters per line in the main text at desktop width (field rule of thumb:
   45 to 80).
9. **Heading levels.** For each pair of adjacent levels, the cues that differ and their values. Can
   a subheading be told from bold body text?
10. **The thing to do.** The action the reader must take (copy, click, continue) in each section:
    is it the most visible thing there, at rest?

## A diagram or canvas

6. **The one claim.** What the diagram exists to show, in one sentence. Where a reader finds it, and
   how long that takes.
7. **Relationships.** Each relationship the diagram means, and whether it is drawn (a line, a
   nesting, an alignment) or only labelled. Lines that cross, run hidden, or end ambiguously.
8. **Encoding.** Each colour, shape and line style, and what it means. Is there a key where the
   reader needs one, and does every encoding mean one thing?
9. **Labels.** Every label's rendered size and contrast against what is behind it, at the size the
   diagram is actually shown, including at phone width.

## A dashboard or status board

6. **The verdict.** The one answer the board exists to give (ready, healthy, on track). Where it is,
   and whether it is the first thing the eye lands on.
7. **Status encoding.** Every status colour or symbol, and whether each can be told from the others
   by more than colour alone and by readers with colour vision deficiency.
8. **Panels.** Each panel, the question it answers, and whether its edges and spacing make it read
   as one unit separate from its neighbours.
9. **Numbers.** Each number shown: its unit, its time, and what it is compared against.

## A form or review page someone fills in

6. **What is asked of them.** Every place the page asks the reader to act (answer, choose, press),
   in order. Does the order follow the task, and does each say what it is for?
7. **State.** After each choice, what on screen shows it was taken. Pressed and unpressed controls
   compared: what differs, and can it be seen?
8. **The final action.** The control that finishes or submits: is it the most visible action, and
   does the page say what happens when it is pressed?
9. **Regions.** Each group of controls that belong together, and what marks it as a group.

## Not covered by this set

Slide decks, Word and PDF documents, draw.io and D2 sources viewed in their own tools, Confluence
pages and Grafana dashboards. Grafana dashboards have their own review, the
`dashboard-evaluation` skill.
