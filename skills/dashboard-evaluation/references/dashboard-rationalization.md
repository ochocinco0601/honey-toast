# Reference: Dashboard Rationalization

> Read `../SKILL.md`, then `observability-panels.md` (the chain diagnostic), then
> `panel-form-fitness.md` (the form tests). This file is the **run** that uses
> both: take a dashboard that already exists and has grown, and produce a
> justified, per-panel disposition so the owner can keep, fix, move, or remove
> each one on stated grounds.
>
> Use it when a dashboard has accumulated panels faster than it has accumulated
> reasons — many panels, no organizing question, and no one willing to delete
> anything because no one can say what any of it is for.

---

## 1. What this is

**Alarm rationalization, applied to panels.** ISA-18.2 / IEC 62682 (*Management
of Alarm Systems for the Process Industries*) addresses the identical failure:
alarm systems accumulate alarms until the operator is flooded and the system stops
serving anyone. Its remedy is not tuning — it is a documented review in which
**every alarm must justify its own existence** against three tests: a defined
consequence, a defined operator action, and enough time to take it. Alarms that
cannot meet all three are removed, and the justification for each survivor is
recorded.

The transfer is direct. A panel justifies itself with:

1. **A named consumer** — someone with a responsibility, not "the team"
2. **A decision it unlocks** — an action, not "awareness"
3. **Enough context to make that decision** — the chain positions filled

**The burden of proof sits on the panel, not on the person removing it.** This is
the single move that makes a bloated dashboard tractable. Without it, every
deletion is an argument someone can lose by saying "but what if we need it," and
nothing is ever removed.

Two more bodies of practice sit under the run:

- **ISO/IEC/IEEE 42010** — *view / viewpoint / concern*. A **view** (the
  dashboard) exists to address the **concerns** (the questions) framed by a
  **viewpoint** (the occasion of asking) and held by named **stakeholders**.
  Rationalization is a conformance check in both directions: does every panel
  serve a concern, and is every concern served?
- **Basili GQM** — *goal → question → metric*, run backwards. Start at the metric
  on the panel and walk up. A metric that reaches no question is the defect the
  run is looking for.

---

## 2. Preconditions

### The consumer and the occasion

Who reads this, holding what responsibility, on what occasion — triage, start of
shift, a governance review, a capacity conversation? The occasion determines which
question set applies (`observability-panels.md` §2 gives the triage sequence). A
dashboard serving several occasions at once is a finding, not a starting
condition: name the occasions and expect the run to recommend splitting.

### The evidence — three sources, none of them optional by default

**Neither the definition nor the render substitutes for the other.** They answer
different questions, and a run using only one produces a predictable half of the
findings. Say which source each finding came from.

| Source | What it is | What it is the **only** source for |
|---|---|---|
| **Definition** | The dashboard's export — Grafana JSON, Splunk Simple XML, Dashboard Studio JSON | Whether a threshold exists *at all*; what each panel actually queries; whether two panels query the same thing; whether a table is sorted; whether a gauge has bounds |
| **Render** | A screenshot or the live view, at the size the reader actually sees | Whether the eye finds an entry point or hits a wall; visual hierarchy; density; whether threshold coloring reads at the size it is drawn; how much sits below the fold |
| **Use** | Platform view/access data, where the platform exposes it | Who opens this, how often, when last. Behavior rather than intent |

**Why the render is not a lesser source.** An absent threshold and an untripped
threshold look identical in a picture — that is the definition's job. But a
definition file cannot tell you a dashboard is unreadable, and tidy JSON produces
walls routinely. A dashboard whose panels are each individually justified can
still fail as a surface, because nothing tells the eye where to start. That
finding exists only in the render. Method and record for this source:
`reading-the-render.md` — including the monitoring-specific asks and the
adversarial stance it has to be run with.

**Why use data is worth asking for.** "Nobody has opened this in months" is the
cheapest RETIRE evidence there is, and the only evidence about what people do
rather than what they meant. Not every platform exposes it; ask before assuming.

**When you only have one.** Run what you have and say plainly what you could not
produce. Render-only: no finding about absent thresholds or duplicate queries.
Definition-only: no verdict on readability, hierarchy, or density — do not guess
it, and do not let a clean definition pass as a working surface.

---

## 3. Step 1 — Inventory

### The facts the run needs

Platform-neutral. Every dashboard tool encodes these somewhere; the adapter below
says where.

| Fact | Why the run needs it |
|---|---|
| Identity | To refer to the panel and to record its disposition |
| Stated purpose | The claimed question. Usually blank — which is itself a finding |
| Form | Input to the form-fitness test |
| Query | The actual question, and the basis for detecting duplicates |
| Thresholds | Whether the value can be judged at all |
| Bounds / units | Whether a gauge is expressive; whether the number means anything |
| Grouping and position | The reading order the surface imposes |
| Handoff | Whether the reader can get to the next question |
| Repetition | Whether one definition is producing many panels |
| Reader inputs | What the reader is expected to choose before the surface works |

### The adapter

Structural anchors are stable; **option names are not.** Read them off the file in
hand rather than assuming — this holds within a platform across versions, and
sharply between Splunk's Simple XML and Dashboard Studio.

| Fact | Grafana JSON | Splunk Simple XML | Splunk Dashboard Studio |
|---|---|---|---|
| Panels | `panels[]`, recursing into any `type: "row"` | `<row>` → `<panel>` | `visualizations`, keyed by id |
| Form | `type` | the child element — `<chart>`, `<single>`, `<table>`, `<event>`, `<map>` | `type` on the visualization |
| Query | `targets[]` | `<search><query>` | `dataSources`, referenced by the visualization |
| Thresholds | `fieldConfig.defaults.thresholds.steps` | range options on a single value | `options` on the visualization |
| Bounds / units | `fieldConfig.defaults.min` / `.max` / `.unit` | charting axis options | `options` |
| Grouping | enclosing row panel title; `gridPos` | `<row>` order and `<panel>` grouping | `layout` |
| Handoff | `links[]`, and drill targets in `options` | `<drilldown>` | drilldown in `options` |
| Repetition | `repeat` | multi-value tokens on a panel | `inputs` driving dynamic options |
| Reader inputs | `templating.list` | `<input>` on `<form>` | `inputs` |

**A cross-cutting caution.** A dashboard's *definition format* and its *query
language* are independent axes. A Grafana dashboard can query Splunk; a Splunk
dashboard can query several backends. Read the format from the file's structure,
not from what the queries are written in — a file full of SPL is not necessarily
a Splunk dashboard, and mistaking one for the other sends you looking for fields
that are not there.

**No export at all** — an embedded view, a vendor portal, a screenshot someone
sent you. Run on the render and the reader alone, and mark the findings you could
not produce. That is a reduced run, not an invalid one.

### Detectable signals

Conditions, not field paths — check each against whatever the adapter gave you.
They are cheap, objective, and usually account for most findings on a grown
dashboard.

| Condition | Points at |
|---|---|
| A time-over-time chart with no threshold drawn | Right-edge test, threshold test |
| A single value or gauge with no threshold configured | Threshold test — the number cannot be judged |
| A gauge with no bound | Gauge test |
| A part-to-whole chart with many slices | Pie test |
| A table with no sort configured | Lookup-versus-scan test |
| A second value axis on one chart | Dual-axis test |
| Two panels whose queries are near-identical | MERGE candidate |
| No stated purpose recorded | The claimed question was never written down |
| Title names a metric or a system, not a question | The panel names its data, not its job |
| No drilldown or link out | No handoff — the reader is stranded after reading it |
| Panel needs a reader input that has no sensible default | The surface does not work on arrival |

---

## 3b. Step 1b — Group the panels by the story they tell

**Do this before judging any panel.** Walk the inventory and sort every panel into
the question it helps answer. Not its data source, not its section on the page —
the story a reader is following when they look at it.

A story is one question, one audience, one decision. "How big is the gap"
and "is the gap closing" are two stories, not one, because they serve different
decisions. "What is broken right now" is a third, and usually a different audience
entirely.

Produce a table before you produce any verdict:

| The story | Panels telling it | Who for | What it decides |
|---|---|---|---|

### Why this comes first

**It is what a person actually needs.** A reader asked to make sense of a grown
dashboard is not asking which panels are defective. They are asking *what is being
communicated here, and which parts of it are for me.* The per-panel record answers
a question they did not ask until they have this one.

**It makes the dispositions obvious.** Redundancy is a property of the group, not
of any panel. Seven panels telling one story is visible instantly here and nearly
invisible one panel at a time — each of the seven looks fine on its own.

**It finds the defects a per-panel pass cannot see:**

| Pattern | What it means |
|---|---|
| **One story, many panels** | Restatement. Feeds MERGE and RETIRE, and usually accounts for most of the cuts |
| **One panel, one story, and it is the important one** | The finding is real and under-weighted. Check where it sits on the page |
| **Two audiences on one surface** | Reporting and operational stories share a page. Neither reader is served well; feeds a split recommendation |
| **Stories interleaved rather than grouped** | The layout is organized by data type or by team. A reader following one question has to hop across the page |
| **Two stories that look like one** | Adjacent panels measuring different things in identical treatment — a reader infers a causal link that is not there |
| **A story with no panel** | Falls out of the coverage step, but is easier to name once the existing stories are on the table |

### Naming a story

Write it as the question a person would say out loud, not as a metric name. *"Is it
moving?"* — not *"burn-down trend."* If a story cannot be phrased as a question
someone asks, it is a data category, and the panels under it need re-sorting.

---

## 4. Step 2 — The per-panel record

For each panel, one record. This is the ISA-18.2 rationalization record in this
domain: the written justification a survivor carries.

| Field | What goes in it |
|---|---|
| **Panel** | id and title |
| **Claimed question** | What the title and description say it answers |
| **Actual question** | What the query and form *can* answer. Where these differ, say so — the gap is the finding |
| **Consumer** | The named role with the responsibility. "Unnamed" is a valid and damning answer |
| **Decision** | The action it unlocks. "Awareness" is not a decision |
| **Chain positions** | Which of the five are filled, which are absent (`observability-panels.md` §1) |
| **Form verdict** | FIT / INCOMPLETE / RESHAPE / SPLIT, with the failing test named (`panel-form-fitness.md` §3, §5) |
| **Disposition** | From §5 |
| **Grounds** | One sentence. The reason a reader could disagree with |

Both diagnostics run, and they are independent. A panel can be perfectly shaped
and serve nobody; a panel can serve a real decision in the wrong form. Record
both.

---

## 4b. Every finding carries its basis

**This is separate from evidence source and both are required.** Source says which
artifact a finding came from — definition, render, usage. **Basis says what kind of
claim it is.** A finding can be render-sourced and pure opinion; marking only the
source lets the opinion travel as fact.

Three bases. Every finding, in every section, carries exactly one.

| Basis | What it means | What it must carry |
|---|---|---|
| **OBSERVED** | Readable off the surface. Another reader can verify it without leaving the page or trusting you | **Where it is readable.** A panel, a legend, a cell. If you cannot point, it is not observed |
| **STANDARD** | A named rule is being broken | **The name of the rule**, and what it says. "Bad design" is not a standard; "hue is selective, not ordered — Bertin" is |
| **INFERRED** | Your judgment about what it costs, what it means, or what matters most | Phrasing that reads as judgment. It is legitimate work; it is not a fact |

### The rules that make this a control rather than a note

1. **A blocking finding must be OBSERVED or STANDARD.** Never INFERRED. The most
   prominent claim on the record cannot rest on the reviewer's opinion.
2. **INFERRED never uses the grammar of fact.** No "the most important X," no
   "nobody will," no "not X — none." Write "in my reading," or name whose judgment
   it is, or cut it.
3. **OBSERVED must reconcile with the rest of the surface.** Before asserting a
   value or a trend, **look for the same quantity stated elsewhere on the page** —
   a legend, a min/max column, a summary tile, a table row — and reconcile them. A
   dashboard usually states its key quantities more than once, and the second
   statement is often more precise than the one you read first.
4. **Superlatives and absolutes are INFERRED by default.** "Most important,"
   "only," "never," "no progress at all" — each is a claim about everything on the
   surface, not about one panel. Either demote it to INFERRED or prove it across
   the whole surface.

### Why rule 3 exists

A rounded percentage line reading the same at both ends does not establish that
nothing changed. The underlying counts may have moved inside the rounding, the
denominator may have grown, and the panel beside it may report the exact
minimum and maximum. **Reading one panel and asserting a trend, while a more
precise statement of the same quantity sits unread on the same screen, is the
most common way a review states something false with confidence.**

The check is cheap: for every number you are about to assert, scan the surface for
that number stated again.

---

## 5. Step 3 — Disposition

Eight, in three families.

**Justified**

| | |
|---|---|
| **KEEP** | Consumer named, decision named, chain positions filled, form fit. It stays, and now it carries its reason |

**Fix in place** — the question is right, the panel is not

| | |
|---|---|
| **COMPLETE** | Right question, right form, a required element missing. Name it — most often the threshold |
| **RESHAPE** | Right question, wrong form. Name the target form from `panel-form-fitness.md` §2 |
| **SPLIT** | Carrying two questions. Name both; one keeps the panel, the other gets its own |
| **RENAME** | The panel works; its title misdescribes it. Most often two panels sharing a title while showing different content, or a title naming the metric instead of the question |

**Move or remove** — the panel is not wrong, it is misplaced or surplus

| | |
|---|---|
| **MERGE** | Answers a question another panel already answers. Name the survivor |
| **DEMOTE** | Real question, real consumer, wrong altitude or wrong occasion for this surface. Move it to the drill-down or the dashboard where its reader actually is |
| **RETIRE** | No consumer, or no decision, or answers a question nobody asks. This is the default for anything that survives only because removing it feels risky |

**On RETIRE.** The objection is always the same: *someone might want it one day.*
That is the exact reasoning ISA-18.2 exists to overrule. A panel that serves no
named decision is not free — it costs attention on every read, and it dilutes the
panels that do serve one. If the question genuinely gets asked occasionally, it
belongs in a query or an on-demand view, not on a monitoring surface. Record the
query so nothing is lost; take it off the wall.

---

## 6. Step 4 — Coverage, the other direction

Per-panel disposition only finds excess. Run the reverse to find absence: take
the question set the consumer's occasion demands, and ask which panel answers
each one.

**Take the set from the occasion, not from habit.** `observability-panels.md` §1b
lists the nine occasions and what each one asks. For triage, the set is the
seven-step chain in §2 — detect, localize, assess, diagnose, scope, assign,
remediate — at the altitude the consumer works at. For the other eight, §1b gives
the governing question and its prior art; enumerate that occasion's questions
first, then map panels onto them.

**This is the step most often done wrong.** Running the triage chain against a
readiness, review or capacity surface reports gaps that were never that surface's
job. A coverage table reading "four of seven uncovered" against the wrong
occasion's ruler is a defect in the *review*, not in the dashboard — and it is
hard to spot afterwards, because the gaps it names are all individually true.

| Finding | What it looks like |
|---|---|
| **Uncovered question** | A step in the chain no panel answers. Usually impact, ownership, and runbook — the steps that are not metrics |
| **Over-covered question** | Several panels answering one step. Feeds MERGE |
| **Orphan panel** | A panel mapping to no question in the set. Feeds RETIRE or DEMOTE |
| **Broken sequence** | Steps answered, but the reader cannot get from one to the next. A handoff defect, not a content one |

The impact step is the one most often missing, and it is the expensive one — the
surface shows the system healthy while the business outcome fails.

### The surface as a whole

Panel-by-panel work and coverage work both assume the reader can find things.
Judge that separately, from the render, at the size the reader actually sees.
These findings belong to the dashboard, not to any panel — every panel can be
justified and the surface still fail.

Run `reading-the-render.md`: the record in its §3, then the monitoring-specific
asks in its §5 (what the eye lands on first, whether status color still means
anything, whether configured color reads at drawn size, how many visual languages,
whether the layout follows the question order, whether the answer is above the
fold). Produce its ENGAGE / BOUNCE verdict.

**A surface-level failure outranks every panel finding**, and is reported first. A
reader who bounces in five seconds never reaches the panel you were arguing about.

---

## 7. Step 5 — The output contract

**This section is binding.** The output of this run has a fixed shape. Without it,
every run produces something differently shaped, and the record stops being
comparable between dashboards or between runs of the same one.

**The output is a worksheet, not an essay.** Its reader is deciding what to cut.
They must be able to see every verdict at once, without scrolling through prose.
That rules out one section per panel: **the record is a table, one row per panel.**

### 7.1 Required order

Six parts, in this order, and nothing above them.

**1 — Header.** Dashboard name, source, panel count, which evidence sources were
used, date. Four lines at most.

**2 — Blocking findings.** Only defects that stop the whole dashboard from working
(a gating variable that cannot resolve; data that is not real). **Three sentences
each, maximum: what is broken, why, what fixes it.** Most runs have none — omit
the section rather than padding it. If a blocking finding runs longer than three
sentences it belongs in an appendix, not above the table.

**3 — The stories.** The table from §3b: one row per story, the panels telling it,
who it is for, what it decides. **This comes before the per-panel record**, because
it is the part a reader can act on without knowing anything about panels — it says
what the surface communicates and which parts are theirs. A run that ships only the
per-panel record has answered a question nobody asked first.

**4 — The record.** One table. One row per panel. Exactly these columns:

| # | Panel | Form | Answers | Verdict | Basis | Grounds |
|---|-------|------|---------|---------|-------|---------|

- **Answers** — the question the panel actually answers, as a question, in the
  reader's words. Where the claimed question and the actual one differ, give the
  actual one and say so in Grounds.
- **Verdict** — exactly one word from §5. No hedging, no "KEEP but".
- **Grounds** — **one sentence.** The reason a reader could disagree with. If it
  needs two sentences, the finding is not sharp enough yet. This is the column
  that does the work; it is also the one that most often bloats.

Group rows under the dashboard's own section headings so the reader can match the
record to the screen.

**5 — Coverage.** One table: the question, covered yes/partial/no, one clause of
note. Runs the other direction from the record and finds absence rather than excess.

**6 — The read.** What this dashboard actually is, in one sentence, then at most a
short paragraph. This is where a finding that explains many rows goes — it earns
its place by collapsing the list, not by summarizing it.

### 7.2 Rules that hold regardless of format

- **Every row carries grounds.** A verdict with no reason is an opinion, and the
  whole point of the record is that it is not one.
- **Counts are never the headline.** "17 panels, 6 cut" is arithmetic. The grounds
  are the product. **And if you state a count anywhere, count the rows** — a record
  whose own summary disagrees with its own table has destroyed the only thing it
  was for. Recount at the end of the run, from the finished table, every time.
- **MERGE names the surviving panel, and the survivor cannot be one you removed.**
  Read the disposition set as a whole before shipping: a row that folds into a
  panel another row retires is an instruction that cannot be carried out.
- **Say which evidence source produced each finding** when it is not obvious —
  especially anything that came from the render alone or the definition alone.
- **Retired panels keep their query**, recorded, so the removal is reversible.
- **No recommendation section.** The verdicts *are* the recommendation. A separate
  "recommendations" list restates the table and lets the reader skip the grounds.

### 7.3 Format

**Markdown is the default and must be sufficient.** The tables above are the
deliverable; a run that can only produce something good by building a custom page
has not met this contract. Render richer output only when the destination supports
it, and only after the markdown version stands on its own.

If you do render it as a page, it is still a worksheet: every verdict visible
without scrolling past prose, verdict encoded in form as well as word, and detail
reachable rather than forced.

---

## 8. Step 6 — The closing check

**Run this before the record leaves your hands. Every time.** It is mechanical on
purpose: each line is something you can check by looking, not a judgment call, so
it fires the same way for every operator on every run.

A rationalization record's entire value is that a reader can trust any single line
enough to argue with it. One wrong number destroys that for the whole document —
a reader who catches an error in the summary stops believing the table, and they
are right to.

### The checks

| # | Check | How to fail it |
|---|---|---|
| 1 | **Recount every stated number from the finished table** | Any count in the prose or summary disagrees with the rows |
| 2 | **Every row has a verdict from §5** | A verdict you invented mid-run and never added to the set |
| 3 | **Every row has grounds, and grounds are one sentence** | A blank, or a paragraph |
| 4 | **Every MERGE names a survivor, and no survivor is RETIRE'd or MERGE'd away** | An instruction that cannot be carried out |
| 5 | **Every number in the prose has a referent on the page** | "…eight times over" when nothing on the page is eight |
| 6 | **No hedged verdicts** | "KEEP, but…" — that is COMPLETE or RENAME |
| 7 | **Blocking findings are within the three-sentence cap** | An essay above the table |
| 8 | **Findings from a single evidence source say so** | A render-only claim presented as fact about the definition |
| 8a | **Every finding carries a basis — OBSERVED, STANDARD or INFERRED** (§4b) | A blank, or a judgment travelling as a fact |
| 8b | **No blocking finding is INFERRED** | The most prominent claim rests on your opinion |
| 8c | **Every OBSERVED number was reconciled against the same quantity stated elsewhere on the surface** | A trend asserted from one panel while a legend, min/max or summary tile on the same screen says otherwise |
| 8d | **Every superlative and absolute is either proved across the whole surface or marked INFERRED** | "the most important," "only," "no progress at all" stated as fact |
| 9 | **Retired panels' queries are recorded** | The removal is irreversible |

### If you rendered it as a page

10. **Look at it.** Not the source — the rendered page, at the size the reader
    uses, including a small laptop. `reading-the-render.md` is the method; the
    minimum is that a reader sees what the dashboard *is* and at least the first
    verdicts before scrolling.
11. **Confirm the page and the markdown say the same thing.** Two artifacts of one
    run that disagree is the same defect as check 1, one level up.

### The part a checklist cannot do

These checks catch arithmetic and incoherence. They do not catch a wrong *reading*
— accepting a panel's own framing, crediting the appearance of something for the
thing, or missing what the surface actually is. **Those need a second pair of eyes
that did not do the run.** Where an independent review is available, use it on the
record before it ships; where it is not, say plainly that the record has had one
reader, so the recipient knows what it has been through.

---

## 9. Cautions

**Do not start at the form.** A session that opens with chart-type opinions
produces a prettier dashboard answering the same unexamined questions. Consumer
and decision first, always.

**A metric being available is not a reason.** The most common origin of a surplus
panel is that the data existed. Availability explains how a panel got there; it
never justifies keeping it.

**Aggregate counts are not judgments.** "23 panels, 9 retire" is arithmetic. The
grounds per panel are the product; the count is a byproduct.

**Recommendations are not decisions.** The run produces a justified proposal. The
dashboard's owner rules on it — and the record exists precisely so they can
disagree with a specific line rather than with the whole.

**One source will not do.** The two most common half-runs: judging readability
from an export (a tidy definition file says nothing about whether the page is a
wall), and judging configuration from a picture (an absent threshold and an
untripped one look the same). When only one source is available, say which
findings you could not produce rather than quietly producing fewer.

**Do not port the platform's vocabulary into the reasoning.** A tool's menu of
visualization names is not a taxonomy of questions. Work in question shapes and
fit forms (`panel-form-fitness.md` §2); translate to the product's names only at
the point of writing the recommendation.

---

## Prior art

ISA-18.2 / IEC 62682 (alarm rationalization; justification burden; documented
per-alarm record) · ISO/IEC/IEEE 42010 (view / viewpoint / concern conformance) ·
Basili GQM (goal → question → metric, walked in reverse) · ITIL 4 Incident
Management (the triage question sequence) · Few, *Information Dashboard Design*
(monitoring surfaces are read at a glance; surplus is not free) · Krug
(the five-second test) · Norman (visual hierarchy; the display should not make the
reader compute) · Tufte (density, data-ink).
