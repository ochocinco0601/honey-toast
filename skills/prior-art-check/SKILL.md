---
name: prior-art-check
description: Answer "is this established practice, or did we reinvent it?" — at the weight the answer actually warrants. ONE DOOR, TWO FORMS, and the skill picks the form, never the user. **Name it** is the default and most invocations end there: point at where the field already holds it, state the honest delta, move on — inline, no agents, no report files, no gate. A match you can point at is checkable by the reader without you, which is what makes it cheap. **Check it** — the blind pipeline (function-only description, cold prior-art-checker agent, encode gate against the activated prior-art inventory, and on STRONG/PARTIAL an automatic apparatus-auditor chain) — fires on narrow conditions only: you believe a match but can name no source for it; you are about to claim something is NOVEL; or an entry is about to enter the inventory. Novelty always checks, because "I couldn't think of one" and "there isn't one" are indistinguishable from the inside — the one verdict a session can never self-grade. Use when the user asks whether something is real/established, whether we're reinventing a wheel, or says a structure feels off in a way suggesting it may already exist in a real discipline. Triggers on "prior-art check", "prior art check this", "is this established", "did we reinvent this", "has this been solved", "does this already exist", "what discipline already does this", "check this against prior art", "is this novel". The user never invokes the apparatus audit separately and must never be asked to. Do NOT use this to review whether an artifact serves its reader — that is independent-discipline-reviewer.
---

# Prior-Art Check

The firing surface for prior art at **two weights**. The blind agent holds the
judgment on the heavy path; this skill holds the **apparatus** — the weight test at
the front, the blinding discipline going in, and the encode gate coming out. Without
this skill the agent is a blind reviewer nobody is guaranteed to hear.

**Definition of prior art** → the prior-art definition that ships with this capability.
Single source. Do not restate it here, and never paraphrase it into a prompt — you hand
it over whole (Step 3).

---

## Step 0 — Pick the weight (before anything else)

**Most invocations end here, in the turn, at no cost.** The pipeline is for narrow
cases. Running it on a question that a citation answers is the failure this step
exists to stop — ceremony spent where a sentence was owed.

The test is not how big the artifact is or how much the answer matters. It is
**whether a reader can check the answer without you.**

| What you have | Weight | Why |
|---|---|---|
| A match you can **point at** — you can name the practice, its discipline, and roughly where it lives | **Name it.** State the match, the honest delta, move on. No agent, no file, no gate. | The reader verifies it without you. That is what makes it cheap — not that it matters less. |
| A match you **believe but cannot source** — it feels established; no citation comes | **Check it.** | This is the failure the apparatus exists for: a confident name wearing borrowed authority, accreting where later sessions trust it. |
| A claim that something is **NOVEL** | **Check it. Always.** | *I couldn't think of one* and *there isn't one* are indistinguishable from the inside. A reader can verify a match; they cannot verify an absence. This is the one verdict a session can never self-grade. |
| An entry about to enter the **activated prior-art inventory** | **Check it. Always.** | Entries outlive the session that wrote them. |

**The delta is not optional at either weight.** A cheap naming still states what does
*not* fit. A match without its delta is an over-claim however little it cost.

**Naming is not adopting.** If the answer will sit in a sentence and pick a frame for
the work in front of you, you are done at *name it*. Step 6's apparatus question is
about practices we **built on**, not practices we mentioned.

**A named match that later gets built on re-enters at Step 1.** Cheap now does not
mean cheap forever — the weight is re-tested when the claim's consequence changes,
not grandfathered by having once been answered.

---

**Steps 1–7 below are the *Check it* path.** If Step 0 said *name it*, you are done.

## Step 1 — Name what's under check

One artifact or several (the agent takes 1..N). If there is nothing built to check
— a conversation, an idea not yet rendered — say so and stop. There is no target.

## Step 2 — Write the function-only description (the blinding discipline)

This is the step the whole check's validity rests on. For each item, describe
**what it does**: behaviour, rules, states, roles-as-functions.

**Strip, without exception:**
- the artifact's internal name — our names are often borrowed vocabulary and a name
  is not evidence;
- any practice, discipline, framework, or methodology **named anywhere**;
- our candidate answer, and any hint of what we think it matches;
- our reasoning for building it.

**Do not soften this by explaining more.** Every sentence of context you add is a
surface the answer can leak through. If you find yourself wanting the agent to
"understand the background," that impulse is the check failing.

The agent fails closed on a dirty description. A `BLINDNESS BREACH` back is the
system working — rewrite and re-dispatch; never argue with it.

## Step 3 — Dispatch the blind agent

Dispatch `prior-art-checker` with three things and **nothing else**: the descriptions,
a report path, and **the full text of the prior-art definition**.

**Hand over the definition verbatim.** The agent has no read capability at all — that
absence is what makes its verdicts worth having, and it means the definition cannot be
fetched, only given. Paste it whole; do not summarise it, do not trim it to "the
relevant parts," and do not let a stale paraphrase drift from the single source. If you
find yourself editing it on the way through, stop — you are rewriting the criteria the
check is judged against.

Do not tell it what you think.

## Step 4 — Read the report; reconcile against the inventory

Read the report **first**, then open the **activated prior-art inventory** — the
standing table of frameworks already adopted. Never the other way round: reconciling
before you have read the blind verdict is how the inventory's contents become the
answer.

Per finding: **do we already hold this?**
- **Already in the inventory** → the check corroborated it. Note that; nothing to
  encode.
- **Not in it, passes the gate below** → encode it (Step 5).
- **NONE verdict** → the honest novelty answer. Encode nothing. NONE is a result,
  not a failure.

**If the environment has no inventory**, the check still runs and the gate below
still applies — but the finding has nowhere to accrete, and a check whose findings
nowhere accrete teaches a session and not the organization. Name that plainly rather
than letting it be discovered later: standing an inventory up is the cheapest thing
that converts this capability from an answer service into a compounding asset.

## Step 5 — The encode gate (nothing enters the table without passing)

**This gate exists for one failure mode, and it is the worst one:** forced matches
accreting in the inventory as stretched attributions that future sessions trust. A bad
entry outlives the session that made it and poisons every check after it. The gate is
not paperwork.

Before any entry reaches the inventory, all four must hold:

1. **Honest delta stated.** A match without what-does-NOT-fit is an over-claim.
   No delta → do not encode.
2. **Not a stretch.** If the connection needed imagination, it fails — the agent's
   Pass 2 should have killed it; if it survived and still reads thin, kill it here.
3. **Judged by function, not name.** If the match rests on shared vocabulary, it
   isn't a match.
4. **Real discipline, recognizable by name.** A practitioner would name it. If it
   is ours, it is not prior art.

Then encode per the inventory's own conventions, and per whatever maintenance rule
governs it — **this step is that rule's only guaranteed firing moment.** Nothing else reliably
brings a discovered framework to the inventory: the rule fires on a *discovery
event*, which no path-scope can catch. If the environment has no such rule, this
step is still the only moment that reliably closes the loop.

Record what you rejected at the gate and why. A gate with no rejections on record
is a gate nobody is operating.

## Step 6 — Chain to the apparatus audit (automatic — do not ask)

**On every STRONG or PARTIAL match against a practice this repo BUILT ON, dispatch
`apparatus-auditor`.** Do not ask whether to. Do not wait to be told. The design is
explicit: **one door.** The operator invokes the check and must never have to remember
that a second question exists. The chain is the machinery's job, not the operator's memory.

**Built on means there is apparatus to audit** — a skill, a pipeline, a gate, a process
someone runs. A practice merely *named in a document* has none, so the audit returns a
finding about a sentence. That is this step firing on prose, and it spends a second agent
on nothing.

Pass it: the artifact's function, the matched practice(s), and a report path. **Do
not pass it your view of whether the environment's apparatus is adequate** — that is the claim it
audits, not evidence for it.

It asks the question this skill cannot: **we matched the form — did we adopt the
operating apparatus that makes that practice work, or copy the form only?** Different
question, different yardstick (this environment's needs and scale, not the world's
practice), and deliberately not blind. It audits against the operating model — whichever
document states how work moves and what guarantees it — whose core claim holds anywhere:
*an artifact without its apparatus is a prop.*

**Skip on an all-NONE result** — nothing was borrowed, so there is no borrowed apparatus
to have missed — **and skip on matches that are claims rather than builds.**

## Step 7 — Brief the operator in outcome terms

**The operator gets the answer, not the findings file.** Handing them a report to
adjudicate is a role inversion — the operator holds intent, judgment and taste, not
craft adjudication.

Brief them with:
- **the answer to what they asked** — is it real, or was it reinvented;
- what it turned out to be, in one line, and the honest delta;
- **what's genuinely novel**, if anything — usually the part they want;
- what you encoded, and what you rejected at the gate.

**Route to the operator only what is theirs:** if a finding implies work — a form
copied without its apparatus, an over-claim somewhere — the **priority call** is the
operator's.
Ask it as one question. Resolve everything else yourself.

---

## Boundaries

- **The judgment is the agent's, not yours.** If you disagree with a verdict, that
  is not license to overrule it — you are the party whose self-grading it exists to
  replace. Re-dispatch with a better description, or record your disagreement in the
  brief. Do not substitute your own answer.
- **The apparatus *judgment* is not yours — but the apparatus *dispatch* is.**
  "Did we adopt the practice's operating apparatus or copy its form?" is
  `apparatus-auditor`'s question, and Step 6 fires it automatically. You do not
  answer it yourself, and you do not make the operator ask for it.
- **Never let the table reach the agent.** Not in the prompt, not as context, not as
  a "for reference." The whole value is that it does not know what we already think.
