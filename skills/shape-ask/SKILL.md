---
name: shape-ask
description: Hand back a reading of the user's ask before doing any work on it. Use whenever a substantive work ask arrives in imprecise form — hedged recall ("I think we had", "it's my recollection", "I suspect", "if I remember"), an unnamed target ("that thing", "some other source", "the one we did before"), a stated goal with no named deliverable, a request to make something "simple" or "better" or "readable" without saying what good looks like, or an ask that says what to find but not what it is for. Also use when the user asks explicitly — "help shape my ask", "my words are imprecise", "shape this ask", "/shape-ask", "what is this an instance of", "I'm talking about the gist", "I don't know the specifics", "I'm not the expert". Do NOT skip this because the ask looks answerable: an ask that is easy to act on literally is the exact case this exists to catch. The output is a plain-language playback of what was heard, handed back for confirmation — never work built on the raw phrasing.
---

# /shape-ask — Diagnose the ask before working it

## The move

The user's words are symptoms, not spec. The work is diagnosis: name what the ask is an instance of in established practice, then reason from the named thing — because the name is the handle that pulls in everything the world already knows. Most problems are not bespoke. A session that builds a private frame around the literal words is asking the user to be the craft expert; correctness has to rest on things the user does not have to supply — prior art and industry grounding.

## Contract — the playback is the whole turn

The deliverable is a **playback**: the understanding handed back for the user's confirm before any work exists. Named practice: requirements validation (playback of elicited understanding before specification); reflective listening.

**Nothing above it and nothing below it.** No search, no file inventory, no findings, no plan, no "my call," no build offer. Reading the ask does not require reading the codebase — if you searched before playing back, you already built the frame this exists to prevent, and moving it above the playback does not undo that.

**This holds even when the ask names the search.** "Find this in the repo," "look in commit history," "I think it's in the database" — the search is part of what is being asked for, so it waits for the confirm like everything else. An ask that tells you where to look is still an ask you might be reading wrong, and running the search first is how a session ends up handing back the right files for the wrong job. It is the easiest case to get wrong: the ask hands you the first step, so taking it feels like compliance.

1. **What I heard** — the job the user is trying to get done, in their terms. Two or three sentences. No craft vocabulary.

2. **Which mode** — *do a known thing* or *work out what the thing is*. One line, plain language, no jargon. **These take opposite handling and conflating them is a live failure:** in the first, a confident name is the whole win; in the second, a confident name is actively harmful because it snaps a forming shape to the nearest existing one. **When working out what the thing is, no name ships until the shape holds** — say "this doesn't have a name yet" rather than reaching for the nearest respectable-sounding one.

3. **How I'm reading it** — what the ask actually is underneath the words, in plain language. Where the real job differs from the stated one, say so and say why.

4. **Where my reading could be wrong** — the intent forks, one line each. Different readings of what the user means; not craft options, and never a menu they have to price.

5. **Stop on one question about intent, never about the analysis.** The turn ends on a question naming the single thing being confirmed, answerable from knowing what was meant: *"Did I get what you're asking for: <one line>? Yes or no."* Never *"Is that reading right?"*: after a playback it reads as "is all of this right?", which asks the person to parse the whole turn and rule on engineering they cannot check. An engineering claim in the playback is checked by a blind reviewer, never by their yes.

The playback carries **no diagnosis table and no prior-art names** — deliberately. Naming the practice at the user before they have confirmed what they meant is the craft wall.

## After the confirm — and only then

Name it, then work it.

| What you asked | What it is | Basis |
|---|---|---|

One row per distinct thing the ask contains; **split only where the split changes what gets built.** Every "what it is" must pass the prior-art test: a practitioner of the named discipline would recognize it **by name**, judged by **function**, never by name-similarity. `NOVEL — <argument>` is permitted and carries a burden (what was searched, why nothing fits). Base rate: problems like these are almost always industry-common, so a NOVEL verdict is presumptively under-search, not discovery.

**The name is not the scope. Every name ships with its cut.** A discipline name switches on a whole body — "requirements engineering" covers elicitation, specification, validation, traceability and stakeholder analysis, and ten minutes or two weeks both qualify. The name alone therefore instructs nothing. State, in the user's terms and not the discipline's:

> **which part** of it · **at what depth** · **producing what**

The user cannot supply the name and cannot supply the cut. Both are the session's, and a name delivered without a cut has handed the specification back to them.

**Every name ships with who can check it.** Naming is *activation* — it binds the session to a structure, which is the point — so a wrong name does not merely mislabel, it runs the wrong process confidently and everything downstream inherits it. The user's ability to catch that varies, and the difference must be stated rather than assumed:

| The user's standing | What their "yes, that's it" is worth | What does the checking |
|---|---|---|
| **They have lived it** | Real evidence — they are the domain authority | The user |
| **They saw one instance, just now** | Covers that specimen; silent on the general claim | The user for the instance; a blind check for the generalisation |
| **They have never encountered it** | **Nothing.** It means the account was coherent | Not the user — a retrieved citation, or a blind check (`prior-art-check`, if installed) |

The third row is the dangerous one because it is indistinguishable from the first from where the user sits. When it applies, say so in the same sentence as the name, and carry **unverified** until a citation or blind verdict lands. *Existence* claims ("a standard for this exists") are cheap — retrieve and cite, never assert from memory. *Characterisation* claims ("what you have is an instance of X") need the blind check, because a session that proposes a name is anchored and its own PASS is worth what anchoring makes it worth.

**And state what the name switches on, behaviourally.** Not "this is a reference interview" but "I will now separate what you asked for from what you need, expect them to differ, and build nothing until the second is settled." The user cannot rule on whether the term is right; they can rule on whether that behaviour fits their situation. **That is the ruling to ask for** — consequences, which are theirs, never vocabulary, which is not.

Then **resolved-vs-local** — what the name answers by retrieval, what stays genuinely local; expect the name to *dissolve* problems, not just label them. Then the work itself, every downstream sentence reasoning from the name. The user's original words survive as provenance only.

**Do not stop here.** The post-confirm turn produces the work, not another checkpoint. A turn that lands the name, the cut and the activation and then ends has returned the burden to the user one step further along — which is the same defect as never firing, wearing better clothes.

## Sources, in order

- **Latent knowledge** — the reservoir; most correct names come from training. What it owes is verification (the test above). An unverified name is confident invention wearing borrowed authority.
- **Any curated prior-art or vocabulary list the project keeps** — a starting point, never a boundary.

## What a correct diagnosis looks like

| What was asked | What it is | Basis |
|---|---|---|
| "When we fix the parser, can we re-run it over every file it already processed, so the old results reflect the fix?" | Rebuilding derived data from an immutable source when the deriving logic improves | Event-sourcing projection rebuild; pipeline backfill; Kleppmann, *Designing Data-Intensive Applications*, Part III |

The name does real work. Worries about old results "contaminating" new ones dissolve — a rebuild reads the source, never the existing derived data; that is a defining property of the pattern, not an open problem. Not knowing which files have been reprocessed turns out to be a standard reprocessing watermark. Hard-looking problems answered by retrieval, none by invention. That delta — problems dissolving, not just gaining labels — is the sign the diagnosis is right.

## Boundaries

- **Not discovery.** Working out what an unsettled thing is, and ending on a plan, is a larger elicitation job (`requirements`, if installed). This is the playback of one imprecise ask; it may conclude that the ask needs discovery first.
- **Not a prior-art check.** `prior-art-check` blindly verifies things already built. This diagnoses an ask before work starts.
- **Not repair.** Fixing output that has already missed its reader is a different job; this prevents the bespoke frame that produces such output.

## Failure modes this exists to kill

- **Never firing** — the ask is imprecise but doesn't say so, and the session just answers it competently. A skill fires on a request phrase more reliably than on imprecision, so an imprecise ask with no request phrase is the one most easily missed. The literal-answerability of an ask is not evidence it was understood. (This is why the hook exists.)
- **Work outside the playback** — research, inventory, or plans above it, or continuing past it below. Both directions happen; an instruction that says "then work it" with no stop is obeyed exactly.
- **The craft wall** — prior-art names and a dense table handed over before the user has confirmed what they meant. Diagnosis performed at the user instead of understanding established with them.
- Working from the literal words — echoing the user's phrasing back as if it were spec.
- Sticker-naming — reasoning bespoke, labeling after. The lens loads before the read.
- Asking the user to arbitrate between session-invented frames. The user rules on cases; they never legislate frames they had to build themselves.

## The hook — what it adds

The skill works without the hook; the hook only makes it fire reliably. `hooks/unnamed-ask-detector.py` runs on every prompt and stays silent unless it matches. It places one or both signals into the turn:

- **ASK-SHAPE SIGNAL** — the prompt says, in effect, "I can describe this but can't name it" ("I don't know what to call this", "my words are imprecise", "there must be a standard for this"). The session runs the playback above.
- **DIRECTION SIGNAL** — the prompt carries a hedge ("or something like that", "off the cuff", "don't hold me to it"). A hedged statement is direction, not a decision: it is not recorded as a requirement or ruling until the session has played back what was said verbatim, the need under it in the field's terms, and how satisfaction would be measured — and the user has confirmed that.

It never blocks a prompt (it always exits 0), and it ignores turns injected by another session or a subagent, so a hedge quoted in a relayed message is not treated as the user's own words.

## Install the hook

1. Copy this folder to `.claude/skills/shape-ask/` in the project, so the script sits at `.claude/skills/shape-ask/hooks/unnamed-ask-detector.py`.
2. Add a `UserPromptSubmit` hook to the project's `.claude/settings.local.json`, which is personal and not committed, so the hook changes only your own sessions. Put it in `.claude/settings.json` instead only if everyone who clones the project should get it. If the file already has a `"hooks"` key, add the `"UserPromptSubmit"` entry inside it rather than replacing it:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/skills/shape-ask/hooks/unnamed-ask-detector.py"
          }
        ]
      }
    ]
  }
}
```

Notes:

- `UserPromptSubmit` takes no `matcher`. The format follows the Claude Code hooks reference: https://code.claude.com/docs/en/hooks
- The command needs Python 3 on `PATH` as `python`. On Windows, if only the launcher is installed, use `py` in place of `python`.
- The path is relative: Claude Code runs a hook in the session's current directory, normally the project root. **Claude Code only:** if sessions work from another directory, use exec form instead — `"command": "python", "args": ["${CLAUDE_PROJECT_DIR}/.claude/skills/shape-ask/hooks/unnamed-ask-detector.py"]`. Do not use that form for VS Code Copilot, whose hooks reference documents neither `args` nor path placeholders.
- **VS Code Copilot** (local agent) reads hooks from `.claude/settings.json` and `.claude/settings.local.json` only when the `chat.useClaudeHooks` setting is on (it is off by default), and Workspace Trust applies. It supports `UserPromptSubmit` and passes the prompt in the same `prompt` field, so the same entry runs there. Its reference does not document `additionalContext` for `UserPromptSubmit`, so check once that the signal reaches the model (type "I don't know what to call this" and see whether the reply is a playback). See https://code.visualstudio.com/docs/copilot/customization/hooks
- To check the script by hand: `echo '{"prompt":"I do not know what to call this"}' | python .claude/skills/shape-ask/hooks/unnamed-ask-detector.py` prints a JSON object containing `ASK-SHAPE SIGNAL`; a prompt with no tell prints nothing.
