# Reference: Panel Form Fitness

> Read `../SKILL.md` first, then `observability-panels.md`. This file answers one
> question those two leave open: **given the question a panel is supposed to
> answer, is the form it is drawn in the right form — and if not, which is?**
>
> **Order matters.** Form fitness is the *second* test, never the first. A panel
> with no named consumer and no named decision is not a form problem — it is a
> panel that should not exist, and the diagnostic in `observability-panels.md` §1
> catches it. Run that first. Only panels that survive it are worth arguing about
> the shape of.

---

## 1. The one idea

**A form is a claim about the shape of the question.** Choosing a time series
claims the answer lives in a trajectory. Choosing a single number claims the
answer lives in one current value judged against a threshold. When the claim is
wrong, the reader has to do work the panel was supposed to do — and on a
monitoring surface, that work is not done. They glance and move on.

Two named criteria decide it (Mackinlay 1986, *Automating the Design of Graphical
Presentations*):

- **Expressiveness** — the form encodes *exactly* the facts in the data. No more
  (a trend line drawn through a value with no meaningful history asserts a trend
  that is not a fact), no less (a colored tile that hides the number withholds a
  fact the reader needs).
- **Effectiveness** — of the forms that are expressive, choose the one the human
  perceptual system decodes most accurately.

Effectiveness has a measured ranking for quantitative values (Cleveland & McGill
1984, *Graphical Perception*), most accurate first:

> position on a common scale → position on non-aligned scales → length → angle /
> slope → area → volume → color saturation / hue

Bertin (*Semiology of Graphics*) supplies the complementary rule for
non-quantitative data: a visual variable must match the data's type. Hue is
**selective** (finds a category fast) but not **ordered** — so hue can say *which
one*, and cannot say *how much*. This is why a red/amber/green tile is a correct
form for a state and a wrong form for a magnitude.

**The dashboard-specific discount** (Few, *Information Dashboard Design*): a
dashboard is read at a glance, under time pressure, usually by someone who came
looking for something else. Forms that need decoding — legends, dual axes,
stacked areas, anything requiring the eye to integrate before it can judge — cost
far more here than in an analytical report where the reader arrived to study. A
form that is merely *acceptable* in a report can be *unfit* on a dashboard.

---

## 2. Question shape → form

Match on the shape of the question, not on the shape of the data. The same metric
supports several of these; which one is being asked decides the form.

The **fit form** column is the answer. The platform columns are only how that form
is spelled in two common tools — the reasoning is the form, not the product's menu
of visualization names.

| Question shape | The reader wants | Fit form | Grafana | Splunk |
|---|---|---|---|---|
| **Is it OK right now?** | One state, judged | Status indicator with explicit thresholds | Stat (threshold coloring) · Status history | Single Value with ranges · single-value icon (Studio) |
| **How much, and is that enough?** | Value against a target | Value + target + delta | Stat with target · Gauge · Bar gauge | Single Value with trend · marker / filler gauge |
| **Which of these is worst?** | A ranking | Sorted bars on a common scale | Bar chart (sorted) · Table with a bar column | Bar chart on a sorted search · Table |
| **Is it moving, and which way?** | A trajectory | Line over time, with the threshold drawn | Time series (with threshold line) | Line / area chart on a timechart |
| **When did it change?** | An event in time | State over time, or an annotated line | State timeline · Time series with annotations | Line chart with an overlay · Event listing |
| **How is it spread?** | A distribution | Histogram, or density over time | Histogram · Heatmap | Column chart on binned values · Punchcard |
| **Are these peers behaving alike?** | Side-by-side, same scale | Small multiples (Tufte) | Repeated panel by variable | Repeating panel via a multi-value token |
| **What is it made of?** | Part-to-whole | Bars, stacked or grouped | Bar chart · Pie only for a few coarse slices | Stacked column · Pie under the same limit |
| **Where is the problem?** | A position in a structure | Topology with state on the nodes | Node graph · Canvas | Custom viz — Splunk has no native topology form |
| **What exactly happened?** | Specific records to read | Rows | Logs · Table · Traces | Event listing · Statistics table |
| **Who owns this?** | An identity and how to reach it | Contact detail | Text panel | HTML / Markdown panel |
| **What do I do about it?** | A procedure | A named next action with a link | Text panel with runbook link | HTML panel with a drilldown |

*Platform note:* visualization names and options drift between versions and
between Splunk's Simple XML and Dashboard Studio. Confirm the spelling against the
dashboard in hand; the fit form does not change.

---

## 3. The fitness tests

These are the sharp edges. Each names a defect that is common, cheap to detect,
and has a specific remedy. Run them per panel.

**The right-edge test.** *If the reader only ever looks at the right-hand edge of
the line, the history is decoration.* The most common defect on a mature
dashboard: a time series drawn for a question ("is it OK?") whose answer is a
single current state. **Remedy:** demote to a stat with thresholds; keep the time
series only if someone actually asks which way it is going.

**The threshold test.** *If the number cannot be judged without a threshold the
panel does not show, the panel answers nothing.* A value with no target is raw
data delegated to the reader's memory. **Remedy:** add the target and the delta,
or say plainly whose expectation it is failing. This is diagnostic position 3
(`observability-panels.md` §1) surfacing as a form defect.

**The naming test.** *If the reader cannot name the series, the chart is a
texture.* A line chart carrying more series than working memory holds
communicates only "busy" or "not busy". **Remedy:** rank and show the top few
against the rest, split into small multiples, or aggregate and drill.

**The gauge test.** *A gauge without a target is a stat with extra ink.* A gauge
buys exactly one thing — the position of a value inside a bounded range — and
pays for it in area and non-data ink (Tufte). **Remedy:** with no meaningful
bound, use a stat.

**The pie test.** *If the reader must compare slices to each other, use bars.*
Angle and area sit near the bottom of the Cleveland-McGill ranking. Pie survives
only for a handful of slices where the answer is coarse ("most of it is X").
**Remedy:** sorted bar chart.

**The lookup-versus-scan test.** *Tables answer lookup; they do not answer "which
is worst".* If the reader knows the row they want, a table is correct. If they
must scan to find the outlier, the table has handed them the work. **Remedy:**
sort by the thing that matters, add a bar column, or replace with a ranked chart.

**The altitude test.** *A form can be fit and still be wrong if it is drawn at an
altitude the reader does not work at.* Infrastructure detail under a business
label is the classic case (diagnostic position 5). **Remedy:** move the panel to
the drill-down where its consumer lives; put the rolled-up state where the
business reader is.

**The dual-axis test.** *Two y-axes assert a relationship the reader cannot
verify.* The apparent correlation is an artifact of the chosen scales.
**Remedy:** two aligned panels, or a ratio if the relationship is the real
question.

---

## 4. What each form cannot answer

This is the pick-and-choose lever. When a panel is asked to carry more than its
form can, the surplus question needs its own panel — or the panel needs a
different form.

| Form | Answers | Cannot answer |
|---|---|---|
| Status indicator | Is it OK | How far off, how long, why |
| Stat with target | Is it OK, and by how much | Which way it is heading, when it changed |
| Gauge | Position in a bounded range | Trajectory, history, comparison across subjects |
| Time series | Trajectory, when it changed | Whether the current value is acceptable — unless the threshold is drawn |
| Sorted bars | Which is worst, relative size | Change over time; whether any of them is acceptable |
| Histogram / heatmap | Spread, concentration, outlier density | The state of any one subject |
| Topology | Where it sits, what it depends on | Magnitude — node color is selective, not ordered |
| Table / logs | Specific records | Aggregate state; anything at a glance |

---

## 5. Verdicts

One of four per panel, each with a defined next step.

| Verdict | Meaning | Next step |
|---|---|---|
| **FIT** | Form matches the question shape and passes the tests | Leave it |
| **INCOMPLETE** | Right form, missing an element the form needs — usually the threshold | Add the named element |
| **RESHAPE** | Right question, wrong form | Name the target form from §2 |
| **SPLIT** | The panel is carrying two questions | Name both; one keeps the panel, one gets its own |

A form verdict is never the whole verdict. It composes with the chain diagnostic —
a panel can be perfectly shaped and still have no consumer. Both run in
`dashboard-rationalization.md`.

---

## Prior art

Mackinlay 1986 (expressiveness / effectiveness) · Cleveland & McGill 1984
(perceptual accuracy ranking) · Bertin 1967 (visual variables; selective vs
ordered) · Tufte 1983 (data-ink, chartjunk, small multiples) · Few,
*Information Dashboard Design* (at-a-glance monitoring constraints) · Norman
(the reader should not have to compute what the display can present).
