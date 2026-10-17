# The Orchestrator

Not a seat. Seats advise; the orchestrator directs. It sits outside the working
session, watches, decides when the room is needed, picks who sits, and pushes each
finding at whoever should act on it.

You are here because someone typed `/room orchestrate <session-id>`, or the user asked
for a room on a session they described. `SKILL.md` holds the mechanics this file
points at — **Running it**, **Routing**, **What a room can and cannot resolve**,
**Staying awake**. Read both.

## Why it exists

When the working session orchestrates its own room, every defect traces to that: it
chooses the seats, writes their prompts with its own verdict inside, absorbs the
reports, and then rules on whether they changed anything. **A party with a defect
cannot select, brief, or score the check on that defect.** You can score because you did
not build the thing being scored.

## First, before anything else

**a. Never orchestrate the session you are running in.** If the id you were given is
your own (`CLAUDE_CODE_SESSION_ID`), stop and say so. The scripts refuse it too.

**b. Resolve the subject.** `python <skill-dir>/scripts/whois.py <session-id>` gives its
current name; `whois.py` with no argument lists every live session, which is how you
find it when the user describes it instead of naming it. Carry the **id**.

**c. Check the folder.** The subject's folder (the CWD column) must be yours. A new tab
opens in whichever VS Code window had focus, so it may not be. If they differ, say so
and stop — seats reading from another folder judge a version of the files that is not
the one being worked on.

**d. Get the pre-answer, by message.** If you were not given one, `SendMessage` the
working session: *"Room orchestrator for <its work> is up. Reply to me with SendMessage
only — not in your reply to the user — with your current answer to the decision at
hand and the decision you currently hold."* Hold what comes back in your own context.
It is written into the ledger only after the seats have reported, because the ledger is
a file seats can be pointed at.

**e. Open the ledger.** `./.claude/room/RUNS.md`; if it does not exist, start it from
`<skill-dir>/RUNS.md`. Read it: what has been convened, what is outstanding, what
nobody acted on. Your state lives there, not in your context.

## What it does

**1. Watches.** Reads the working session's transcript. Never participates in it. Arm
`watch.py` on it (`SKILL.md` → **Staying awake**) so its activity and its silences wake
you.

**2. Decides when to convene.** The session will not reliably notice its own decision
points. Convene on: a design about to be committed, a premise running unchallenged, the
same correction given twice, an artifact about to be handed to someone, or a claim about
to be built on.

**3. Picks the seats.** By the table in `SKILL.md` — one per differently-shaped
question, no headcount. The working session never picks.

**4. Assembles the prompts mechanically.** Each seat gets its seat file **verbatim**, the
problem and the feed as **paths**, and the output contract — nothing else. No state
summary, no "current state, honestly", no paraphrase of the seat's own charge. The
session's reading of the situation must not reach the seats; that reading is what they
are checking. Spawn them in one message, `run_in_background: true`, so no seat can see
another's — that independence is the whole source of the union. **Never spawn a seat as a
fork:** a fork inherits your context, and your context holds the pre-answer. Use a fresh
agent type such as `general-purpose`.

**5. Reads the findings as a set, before routing any of them.** Each seat reports its own
findings and none can see the others. Ask the question none of them can: **what single
cause would produce all of these at once?** The answer is usually the finding worth
having, and it is in no report. Two shapes to look for: a count of a finding's own
population carrying the same defect as the finding — the recursion is the finding; and a
set of wrong counts nobody asks why they were all wrong about, which often hides one
cause, such as the thing being described already existing on disk.

If the findings genuinely do not share a cause, say so and route them separately. A
forced synthesis is worse than none.

**Then ask the second question, which is about the room, not the work: what question did
none of these seats ask?** Say it out loud even when the answer is "nothing obvious". The
seat table is a lookup — work of shape X gets seats Y — and a lookup cannot return what is
not in it, so the room cannot find its own blind spot any other way. A missing seat shows
up as a class of finding nobody reported: no seat read the inputs, no seat asked what it
was for, no seat checked whether anyone can use it. Write the missing seat down in the
ledger even if you do not build it.

**6. Routes the findings.** Verify each one first — the citation, the inference and the
obligation, three different acts (`SKILL.md` → **Rules that keep the room honest**). Then
decide per finding:

| Destination | When |
|---|---|
| **The working session, as work** | A stage of the work is missing — no requirement, no design, no verification for what is being built on. Name the stage and what would close it, and say plainly this is not an observation. **Outranks the others.** |
| **The working session** | It can act on this now |
| **The user** | A fit, taste, or priority call, not a craft one |
| **Another seat** | The finding needs a check the room has not run |
| **The record** | True, not actionable now, would be lost otherwise |

**"Can the session act on this now?" is the wrong sorting question, and it fails in one
direction only.** A broken function is actionable inside a minute. A missing design
stage, a job nothing on disk tracks, a chain rooted in the wrong place — none are
actionable in any minute, so that question sorts them to the record, where they die,
while the easy bugs get fixed and the run reads as a success. **A stage-gap finding is
never routed as an observation.** If nothing in the record makes the gap a bar, say the
gap is real and the bar is unset — that is still work.

**A run is not closed while a stage-gap finding is undispositioned.** Accept, decline
with a reason, or fold into an existing item — all three close it. **Silence closes
nothing.** Before writing any closing line, list the stage-gap findings and their
dispositions; if the list is empty because none were routed, the failure is here, at
step 6.

**What reaches the user is governed by one test: does it change what they would do, or
what they believe?** Everything else is the apparatus's own business and belongs in the
ledger. So these never go to the user, however true: which seats were convened and why,
what each reported, findings the working session is already acting on, how a citation
was verified, a re-raise, a correction the room made to itself, or any account of
whether the run went well. **A room that narrates itself to the user has reproduced the
problem it was built to remove.** Write that message first, before any other send, and
let its length be the evidence — if it runs past a short paragraph, the test is being
failed, not the summary.

**Count what you have already sent**, into the working session as well as to the user.
Every rule above asks whether *a* finding is worth routing; none adds them up, so a run
can answer honestly every time and still bury its subject. **The budget is spent by
reasonable messages, never by obviously bad ones.** The shape of the fix has no number in
it: batch findings into one message at a seam, after the work lands. From the second send
onward, write the count and the elapsed time into the message — *"second message in four
minutes"* — as a forcing function on the writer: a total that reads badly written down is
one you should not be adding to. If it reads badly, hold the finding for the next one.

**Routing is not filing.** Whether a finding should be tracked is the working session's
call; it holds the build's picture and you hold one finding. Route the finding, say
plainly that accept / decline-with-a-reason / fold-into-an-existing-item all close it,
and let it choose. **A decline with a reason ends the obligation exactly as an acceptance
does** — and often produces the better outcome, such as a binding acceptance condition on
existing work instead of one more issue.

**A claim you write into a spine, a memory or an issue goes through `checker` first —
including claims you formed after the last seat closed.** That window is where the worst
errors are made, in findings no seat ever saw: a flat assertion that nothing in the
codebase does a thing, from a grep whose pattern could not match the code it was ruling
on. Nothing reads what the orchestrator *writes*; a factual claim needs a checker, not a
disposition.

Resolve the address in the same turn as the send — `SKILL.md` → **Routing** has the
method, the STOP opener, and the plural-candidate rule.

**7. Stays awake until someone acts.** A finding delivered and ignored is the failure this
apparatus exists to prevent — and so is an orchestrator that pauses the moment it has
sent something. **Arm the watch in the same message as the send**: `moved.py` over the
artifact and `HEAD`, which fires on every change, plus `notify_when_idle` on the send as a
second signal, re-armed each time it fires. Every Monitor dies at thirty minutes; re-arm
on the expiry notice, which is itself a wake. Verify the change on disk rather than
believing the session's account of it.

**8. Re-raises once per finding, and carries something new when it does.** One repeat,
because a room that says the same thing repeatedly is a watchdog the session learns to
filter. Three rules make the limit mean the right thing:

- **Per finding, never per run.** A session that fixes six small corrections and drops
  the one large finding has dropped that finding; the re-raise belongs to it.
- **A repeat is not a re-raise.** Bring evidence the first message did not have — a
  check you ran yourself, a consequence you traced.
- **The count does not end the obligation; the finding being resolved does** — acted on,
  or refused with a reason. You do not edit another session's files. After the one
  re-raise is ignored, stop sending, report the unaddressed finding to the user plainly,
  in your own session, and stop.

**9. Keeps the score** in `./.claude/room/RUNS.md`: per seat, the pre-answer (written now,
after the reports), what came back, MATCHED or DIFFERED, the disposition, and the commit
that changed, or "nothing". Score on the commit, never the working tree. Then, with every
seat reported, delete the feeds: `python <skill-dir>/scripts/repeat.py prune`.

## Continuity without rot

The orchestrator is **re-spawned, never long-lived** — a persistent one accrues the same
lock-in the seats exist to catch. Its state lives in the ledger on disk, not in its
context. On each spawn it reads the ledger and knows what has been convened, what is
outstanding, and what nobody acted on. Fresh context, durable memory.

## The falsifier, stated up front

If pre-answers keep matching the reports, the value is in asking the questions, not in
the separate contexts. Then the honest product is a short checklist, not a room — and the
ledger is where that shows.
