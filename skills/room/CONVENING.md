# Convening a room

`SKILL.md` says what a room is and which seats exist. This file is how you run one.

A room has two jobs and they are held by different things. The **seats** advise. The
**convener** decides when the room is needed, picks who sits, briefs them mechanically,
reads what comes back as a set, and keeps the score. You are the convener.

---

## The conflict you are running under, stated plainly

The convener here is the same session doing the work. That is a known weakness, not a
design: a party with a defect cannot select, brief, or score the check on that defect.
Where a separate session can hold the convener role, use one — it is strictly better.
Where it cannot, the three controls in `SKILL.md` are what stands in for it, and they
only work if they are done **mechanically and in order**. Doing them in spirit is doing
nothing.

The order matters more than any single control. Pre-answer first, then seats, then
scoring. A pre-answer written after reading a report is not a pre-answer.

---

## 1. Decide to convene

A session will not reliably notice its own decision points. Convene on any of these:

- a design about to be committed
- a premise that has been running unchallenged
- the same correction given twice
- an artifact about to be handed to someone
- a claim about to be built on

**Which target is the user's call. Finding the candidates is yours.** Retrieve them
from the record — the tracker, the effort's own spine, the commit log — never from the
user's memory, which is the burden this whole apparatus exists to lift. Then rank them
and recommend one with its reason. Do not hand over a menu to choose between.

## 2. Write and freeze the pre-answer

Before spawning anything, write down:

- your current answer to each seat's question
- the decision you currently hold

Save it somewhere the seats are **not** pointed at. This is control 1 and it is the one
easiest to skip, because it feels like a formality until the reports arrive and you
cannot tell which of them told you anything.

## 3. Pick the seats

By the table in `SKILL.md` — one seat per differently-shaped question, no headcount.
Stop when the next seat would ask a shape already in the room.

## 4. Assemble the prompts mechanically

Each seat gets:

- its seat file, **verbatim**
- the **path** to the problem — the effort's spine, or the artifact under discussion
- the **path** to any feed, if the seat reads one
- the output contract from `SKILL.md`

And nothing else. **No state summary, no "current state, honestly", no paraphrase of
the seat's own charge.** Your reading of the situation must not reach the seats — that
reading is what they are checking.

The problem statement is what advisors reason about. A feed, where one exists, only
tells them where the thinking has reached.

## 5. Spawn them concurrently, one subagent per seat

Send them in a single batch so they run at once. Each returns its own report; **no seat
can see any other's**. That independence is the whole source of the union property.

## 6. Read the findings as a set, before acting on any of them

The reports arrive one at a time, and each invites action on its own — which is what
makes this step the one most worth forcing.

Each seat reports what it saw. Ask the question **none of them can**:

> What single cause would produce all of these at once?

The answer is usually the finding worth having, and it is in no report. Two shapes to
look for: a count of a finding's own population carrying the same defect as the finding
— the recursion is the finding; and a set of wrong counts nobody asks why they were all
wrong about, which hides one cause — one candidate is that the thing being described
already exists on disk.

If the findings genuinely do not share a cause, say so and handle them separately. A
forced synthesis is worse than none.

## 7. Verify, then disposition each finding

**Verify every citation yourself before anything reaches the user.** Open the file,
check the quoted line, re-run the count.

**Then verify the inference separately.** Write the two as separate lines per finding —
what the seat MEASURED, and what it CONCLUDED — and ask what else would produce the same
measurement. A true measurement supporting a false conclusion is the failure this catches,
and it is invisible to citation-checking. Hold any finding shaped "nothing does X" until
that question is answered.

**Then check the obligation, which is the third act.** Where a finding carries pass/fail
language, ask what makes the bar a bar and who ruled it. A measurement a seat argues
*ought* to be a bar is not one until the record says so — so before that language is
acted on or written down, it either carries a citation to a ruling or it gets rewritten
as an observation.

**Verify the surface the finding is about.** A definition, a generated page and a
running application are three artifacts, and a guarantee proven on one is a guarantee
about one. Two green checks on two surfaces — the source artifact, and the generator
mutated to show its checks can fail — do not cover the third, and the third is usually
the running application someone is actually going to open. Where a surface cannot be
reached from a shell, say so; do not let two green checks stand in for three.

Then decide, per finding:

| Disposition | When |
|---|---|
| **Act now** | You can change what gets built, now, with what the finding says |
| **The user's call** | It is a fit, taste, or priority judgment, not a craft one |
| **Back to a seat** | The finding needs a check the room has not run |
| **To the record** | True, not actionable now, would be lost otherwise |

**A claim you write into a spine, a memory or a tracked item goes through `checker`
first — including a claim you formed after the last seat closed.** That window is where
the worst errors are made, in findings no seat ever sees: a flat assertion that nothing
in the codebase does a certain thing, drawn from a grep whose pattern could not match the
code it was ruling on. Nothing reads what the convener *writes*, and sorting your own
claim into a disposition does not cover it — a factual claim needs a checker, not a
disposition.

## 8. Do not silently drop a finding

A finding delivered and ignored is the failure this whole apparatus exists to prevent.
In a single-session room there is nobody else to chase it, so the discipline is
entirely on the record: **every finding gets a disposition in the ledger, including
"declined", with the reason.** A room whose ledger has blank dispositions has not been
scored, and nobody will notice the one that mattered.

## 9. Keep the score

Record the run in `RUNS.md`: the date, the target, the seats, the frozen pre-answer,
what came back, MATCHED or DIFFERED per seat, the disposition, and what actually
changed — a commit, a file, or `nothing`.

**Score on the committed change, never on the working tree.** A tree under active edit
has no defined state. A finding closed from a green test run on such a tree will read
red on the next invocation, with nothing regressed: a file is being typed into and one
code path momentarily emits nothing. Notice the act on the tree if you like; judge it on
the commit.

**Re-spawn, never persist.** The convener role is re-entered fresh each time; a
long-lived one accrues the same lock-in the seats exist to catch. Its state lives in
`RUNS.md` on disk, not in a context window. On each new run, read it to see what has
been convened, what is outstanding, and what nobody acted on.
