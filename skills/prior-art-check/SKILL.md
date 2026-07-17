---
name: prior-art-check
description: Run a blind, independent prior-art check on a structure this repo built — is it established practice, or did we reinvent (or genuinely invent) it? Use when the user asks whether something is real/established, whether we're reinventing a wheel, whether a structure has prior art, or says a structure feels off in a way that suggests it may already exist in a real discipline. Triggers on "prior-art check", "prior art check this", "is this established", "did we reinvent this", "has this been solved", "does this already exist", "what discipline already does this", "check this against prior art", "is this novel". Also fires when a session is about to claim something is novel, or is about to add an entry to the activated prior-art inventory. This skill owns the whole loop and is the ONE DOOR — the user invokes this and nothing else: it writes the blinded description, dispatches the cold prior-art-checker agent, then on any STRONG/PARTIAL match automatically chains to the apparatus-auditor ("we matched the form — did we adopt the apparatus that makes it work?"), reconciles findings against the environment's activated prior-art inventory behind an encode gate, and briefs the operator in outcome terms. The user never invokes the apparatus audit separately and must never be asked to. Do NOT use this to review whether an artifact serves its reader — that is independent-discipline-reviewer.
---

# Prior-Art Check

The firing surface for the blind prior-art check. The agent holds the judgment;
this skill holds the **apparatus** — the blinding discipline going in, and the
encode gate coming out. Without this skill the agent is a blind reviewer nobody is
guaranteed to hear.

**Definition of prior art** → the prior-art definition that ships with this capability.
Single source. Do not restate it here, and never paraphrase it into a prompt — you hand
it over whole (Step 3).

---

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

**On every STRONG or PARTIAL match, dispatch `apparatus-auditor`.** Do not ask
whether to. Do not wait to be told. The design is explicit: **one door.**
The operator invokes the check and must never have to remember that a second
question exists. The chain is the machinery's job, not the operator's memory.

Pass it: the artifact's function, the matched practice(s), and a report path. **Do
not pass it your view of whether the environment's apparatus is adequate** — that is the claim it
audits, not evidence for it.

It asks the question this skill cannot: **we matched the form — did we adopt the
operating apparatus that makes that practice work, or copy the form only?** Different
question, different yardstick (this environment's needs and scale, not the world's
practice), and deliberately not blind. It audits against the operating model — whichever
document states how work moves and what guarantees it — whose core claim holds anywhere:
*an artifact without its apparatus is a prop.*

**Skip only on an all-NONE result.** Nothing was borrowed, so there is no borrowed
apparatus to have missed.

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
