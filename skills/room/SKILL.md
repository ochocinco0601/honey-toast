---
name: room
description: Put advisors in the room while you work — an engineer, a mentor, a domain expert — each reasoning about YOUR problem in its own context and reporting back. Use when work is hard, stuck, or consequential enough to want more than one head on it; when a design decision is about to be made; when the user says "room", "/room", "get advisors", "who should be looking at this", "second head on this", "bring in the engineer", "what would a mentor say". Also fire proactively before committing to an architecture, or when this session has been corrected twice on the same point. A seat speaks to the WORK — "this design won't hold" — never to the worker's conduct — "that turn was long".
---

# /room

Advisors, each in its own context, thinking about the problem alongside the work.

Named practice: **Perspective-Based Reading** (Basili, Laitenberger et al., NASA
Software Engineering Laboratory, 1996). Several readers examine the same artifact,
each from one assigned perspective, each reporting separately. The documented gain
is the **union** of what they find, and it collapses when the perspectives overlap.
That single property decides almost every rule below.

## The distinction that governs everything

| Not this | This |
|---|---|
| "The session repeated itself" | "This design won't hold — writer and reader disagree about who owns state" |
| "That turn was long" | "You're solving the second-hardest version. The hard part is X" |
| "It asked you to decide" | "The field settled this — supervisor pattern, here's the shape" |

Left column is bookkeeping. Right column is why you want someone in the room.
**An advisor that reports on the session's conduct has failed.** Drop that report
and respawn the seat with the problem.

## The honesty problem, and what holds it

A room convened by the session that built the thing is a room grading its own work.
Left alone, that session picks the seats it expects to be kind to it, writes its own
verdict into their prompts, absorbs the reports, and then rules that they changed its
mind. That is what happens when it is left alone.

Three controls hold it, and **all three are mechanical, not intentions**:

1. **Freeze the pre-answer to a file before spawning anything.** Write down what you
   currently believe the answer is, and the decision you currently hold. Save it.
   Never write it into a file the seats are pointed at — that leak is invisible until
   a seat says so, and it reaches them through the prompt and through an artifact list
   handed over as context.

2. **Seat prompts go in verbatim.** The seat file, plus **paths** to the target and
   any feed — never your prose summary of the situation. Your reading of the situation
   is the thing the seats are checking; it must not reach them.

3. **Score each report against the frozen pre-answer** — MATCHED or DIFFERED. Without
   this a run cannot be scored at all: every report will feel valuable and nobody will
   be able to tell whether it said anything you did not already know.

**The falsifier, stated up front:** if the reports keep matching the pre-answers, the
value is in asking the questions, not in the separate contexts — and the honest product
is a short checklist, not a room. Keep the ledger honest enough that you would notice.

## Convening a room

`CONVENING.md` is the procedure. Read it before running one; it is the half that makes
this half honest.

## Choosing seats

**The session picks. Do not ask the user which seats to convene** — finding the
candidates is the session's job; the user can overrule.

**One seat per differently-shaped question the work poses. No fixed number.** A
headcount cannot express the property that makes this work — the gain is the union of
defects, and it collapses when perspectives overlap. Question shape can.

**Use the field's stopping rule instead of a cap.** Nielsen & Landauer's
diminishing-returns model, `problems = N(1 - (1 - L)^n)`, fitted L ≈ 0.31: one
evaluator surfaces roughly a third of discoverable problems, five reach about 85%, the
curve flattens after. Its own caveat travels with it — **use it to decide whether
another seat is worth spawning, never to claim coverage.**

**A seat earns its place by asking a differently-shaped question, not by being another
asker.** Two differently-shaped questions landing on the same figures is strong: *is
this count true* and *does this claim carry a citation* can turn out to be one defect.
Three similarly-shaped questions agreeing is worthless — and worse than worthless when
all three share an ancestor and therefore a blind spot.

**Agreement between two rooms is not corroboration either.** Two rooms convened on the
same problem that reach the same answer have measured a shared prior, not replicated a
result. They are language models reading one record with one set of instincts; a blind
spot is the thing they share and the thing neither can see. The shared-ancestor rule
above is the same rule, and it does not transfer on its own — it has to be said about
rooms as well as about questions.

**Never resolve a disagreement between measurements by majority.** A lone dissenting
count is often the only information in the set. Chase the outlier for its method
before you decide it is wrong, and record it as unreconciled rather than settling it
two-against-one.

**Cap what gets RELAYED, not how many advisors think.** Interrupting a mid-build
session to say "your numbers are right" is the wall this exists to prevent. The
constraint is on routed output, never on the number of advisors thinking.

Pick by the question shapes the work poses — one seat per shape. The rows name the
shapes that usually apply. **They are not a quota.**

| The work is | Shapes it poses — one seat each |
|---|---|
| A design or build decision | what to build (`engineer`) · already solved (`field`) · how we'd know it worked (`acceptance`) · what job it's hired for (`jtbd`) |
| Something unsettled or vague | right problem (`mentor`) · whose job (`jtbd`) · already solved (`field`) · what capability (`ground`) |
| A deliverable someone must read | breaks where (`outsider`) · usable as handed over (`response`) · whose job (`jtbd`) |
| A claim, finding, or writeup | is it true (`checker`) · already solved (`field`) · contradicts a ruling (`cold`) |
| A finding whose items are all absences — never, no X exists, not yet | **is the absence the right frame (`worth`)**, plus the row above |
| Anything touching the business domain in scope | **is the business right (`domain`)**, plus the row above |
| Work that has run long or lost its shape | what is going on now (`situation`) · what is still open (`threads`) · contradicts a ruling (`cold`) |
| Work about to be committed or filed | legible as tracked items (`issues`) · how we'd know (`acceptance`) · is it true (`checker`) |
| A new effort, or one whose framing has never been stated | **what capability (`ground`)** · right problem (`mentor`) · already solved (`field`) |
| A program with children, not a single artifact | **spine versus tracker (`shape`)** · what is still open (`threads`) · right problem (`mentor`) |
| Several working parts that must become one thing | **does the whole hold together (`chief`)** · what capability (`ground`) · already solved (`field`) · how we'd know (`acceptance`) |
| A workflow built out of agents, prompts and skills | **is the decomposition right (`agentarch`)** · what to build (`engineer`) · already solved (`field`) |
| An approach you want judged without reference to what you built | **`outside`** — convened alone; it must never see the existing answer |

**Add a seat when the work poses a shape the rows do not carry. Stop when the next
seat would ask a shape already in the room** — that is the flattening point the
stopping rule names, and it is not a number.

**An all-absence finding pulls `worth`.** When every finding in a report is something
missing, seats pointed at the artifact and its record all measure the absence and none
asks whether it mattered — so they converge, and the observation that overturns them is
the one nobody was routed to: that the absence being measured does not, by itself, make
the work less valuable. Route a seat to whether the finding's frame is the right frame.

`cold` earns a seat whenever a premise has been running unchallenged for a while.
`ground` earns one at the start of any effort, and whenever the session cannot say what
capability is served without naming the thing it is building. `domain` is not optional
when the business is in scope — it is the only seat that holds knowledge rather than
craft.

**The `cold` seat is load-bearing.** Every other seat reads the session feed and so
inherits its frame. Without a seat that cannot see it, a wrong frame gets confirmed
unanimously and persuasively.

## Rules for briefing a seat

**Never hand a seat your own measurements.** Point it at the target and let it measure.
Numbers in the prompt are the finding handed over, and what comes back is then your own
work returned to you.

**Verify every citation before a report reaches the user.** Open the file, check the
quoted line, re-run the count. A room's reports are worth what their weakest unchecked
claim is worth.

**Then verify the INFERENCE, which is a different act.** A seat hands over a measurement
*and* a conclusion drawn from it, and checking the measurement says nothing about the
conclusion. Per finding, separate the two and check them separately:

    the seat MEASURED ..........  re-run it
    the seat CONCLUDED .........  what else would produce this measurement?

**The trap that produces it: absence of a STAGE is not absence of a FUNCTION.** In a
workflow built out of agents, a model performing a contract *is* the production — so a
grep over pipeline stages can return nothing, be perfectly true, and support a false
conclusion. Any finding of the form "nothing does X" gets that question asked of it
before it is acted on.

**And check the OBLIGATION, which is the third thing a report smuggles in.** A seat may
report a measurement. A seat may argue that a measurement ought to be a bar. **Only the
record makes it one.** The failure: a seat asserts that a score below some figure is a
failure, the figure gets written down as a gate, and the ratified scope turns out to
mention neither the figure nor the measure — the bar was the seat's, not the record's.
It is worse when the measure is incidental, a count derived from a string match on a
default value, and worse again when the thing it gates has already been ruled as not
blocking. A room that does not run this check will invent gates.

So: before any pass/fail language is routed or written down, the bar carries a citation
to a ruling, or it is written as an observation. **Three checks, and they are different
acts:**

    the citation   ...  open the file, re-run the count
    the inference  ...  what else would produce this measurement?
    the obligation ...  what makes this a bar, and who ruled it?

**Calibrate before aiming high.** An instrument that has never run is not validated on
the hardest problem in the building — if the reports come back weak you cannot tell a
weak room from a hard problem. Early runs go on small, ordinary work whose answer you
can check for yourself first.

**One-shot, always.** Seats are spawned fresh and never kept alive. A long-running
advisor accrues its own premature commitment — the disease rebuilt inside the cure.
Respawn at the next decision point.

## Objective

The user works a problem, and the perspectives they would otherwise have to supply
themselves arrive from seats that hold them — while the work is happening, in time to
change it.

**Done looks like:** a seat says something that changes what gets built, and the user
did not have to think of it, ask for it, or relay it.

**Not done:** reports they read and file. A room that produces things worth reading but
not worth acting on has failed, however good the reading is.

## Output contract, given to every seat

    Under 250 words. No preamble, no summarizing back what you read, no
    compliments. Lead with your strongest opinion. Be specific enough to be
    wrong. If you have nothing worth interrupting for, say so in one line.

    Never route a gap to a person. Not "only the business can supply this",
    not "pending a ruling", not "acquire from a stakeholder". The model
    drafts every value and states its basis; ratification is a point-in-time
    event in the real world and is never a precondition for building or
    testing. A person-shaped gap in a report is a failed pass.

## Seats

**A seat IS its prompt.** The files in `seats/` are the whole specification — read one
and you know exactly what that advisor will do. There is nothing behind them.

| Seat | Charged with |
|---|---|
| `engineer` | What to build, what is wrong with the direction, the simplest thing that works, the unaccounted failure case |
| `chief` | The integrity of the WHOLE product — what the customer gets end to end, whether the parts share one model, which seams are removable, which part is the trunk and what dies |
| `agentarch` | The medium — whether a workflow built out of agent sessions, prompts and scripts is decomposed right, typed at its seams, and evaluable |
| `outside` | An independent engineering approach derived from a functional brief alone, with no access to what was built |
| `mentor` | Is this the right problem, what is wanted underneath the ask, what to stop doing, whether success is worth it |
| `cold` | Reads the **rulings on disk** — contracts, decision records, standing guidance — and reports where today's premise contradicts one. Never reads the session feed |
| `checker` | Whether a claim is true and whether a cited source says what it is credited with. Opens the file, runs the grep, follows the citation |
| `field` | Whether this is already solved and by whom — outward to the discipline, inward to your own record of adopted practice. Names the practice, its limits, and the delta |
| `acceptance` | What question a proposed move answers, what would count as success or failure, and who can check it other than the person who built it |
| `outsider` | Reads the artifact cold as a stranger and quotes the exact line where comprehension breaks |
| `worth` | Whether the work is worth anything — does it improve on what the user already had, or is it their own words handed back |
| `domain` | The business domain as actual knowledge; contradicts the engineering when it is wrong about the business |
| `jtbd` | What job the work is hired to do, whose job it is, and whether the current activity serves it or an easier adjacent one |
| `situation` | What is actually going on right now, what changed that reframes earlier work, what is believed that is no longer true |
| `threads` | The current open set — threads never closed, forks, questions asked and never answered, commitments not kept |
| `response` | Whether what the session is handing the user is usable; quotes the worst sentence and rewrites it |
| `issues` | Whether the work is legible as tracked items — what warrants an issue, parent/child placement |
| `ground` | What capability is being served, stated with no reference to any solution; what already provides it; whether the session entered at the artifact and reasoned outward |
| `shape` | How the WORK is organized — the method a spine states versus the shape the tracker actually holds; which children are slices and which are components |

`EXAMPLE.md` shows what a report looks like.

**Adding a seat** means writing a prompt file in `seats/`. Draw the charge from the
discipline the work actually needs. Do not invent a taxonomy.

## What this deliberately is not

**Not a gate that fires on every turn.** A room is an LLM-as-judge arrangement, and it
exists because the model does not get it right the first time. A judge reading *some*
of the turns and saying which failed is worth more than a perfect version that inspects
every one. The perfect version delivers nothing: a validator that inspects every turn
bounces turns it cannot retract, and prints a second copy underneath the text it
objected to. Run this at good-enough — a sample of seats against some of the work.

**Not a code review.** Seats reason about the problem and the direction. A seat asked
to find bugs in a diff is a worse linter.
