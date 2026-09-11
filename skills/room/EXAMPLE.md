# What a room report actually looks like

Two seat reports — `engineer` and `mentor` — using the prompts in `seats/`.

**The target they are run against:** a session designing a background-advisor mechanism,
with a first version already sketched, a roster of perspectives still unsettled after
repeated attempts to derive one from records of past failures, and the
multi-turn-conversation literature already read. The seats address that session as
"you".

Read them to decide whether the seats are the advisors you want; the prompt is the
entire specification of an advisor.

---

## Engineer seat

**The roster question isn't a gate, it's an excuse — and it's what's blocking the
spike.** Ship one seat. The engineer. If one is worth reading, ask what the second
should be. If it isn't, roles never mattered.

**The design, concretely:** the mechanism already exists. A background subagent *is* a
separate context. The session transcript on disk is the read-only feed — the advisor
tails it itself. The completion notification is the injection channel; it arrives in
the working session without anyone relaying anything. That's the entire architecture.
No hook, no permissions config, no observer gate, no polling loop.

`/room engineer` → spawn a background agent with (role prompt, transcript path, spine
path, "read the last 120 records, one strong opinion, 250 words"). Twenty lines of
skill file.

**The flaw:** artifacts built for a delivery problem the tool already solves.
Routing this through a permissioned side channel is a self-inflicted dependency you
don't need.

**Second flaw, load-bearing:** the multi-turn research (Laban et al., *LLMs Get Lost
in Multi-Turn Conversation*, 2025) justifies *freshness*, not *concurrency*. A
persistent watcher accrues its own premature commitment by turn 40 — the disease
rebuilt inside the cure. Advisors must be one-shot and respawned at
decision points, never long-lived. That changes what you build.

**The failure nobody's accounting for:** an advisor reading the session feed inherits
the session's frame. Hand it a wrong spine and every advisor confirms the wrong spine —
unanimously, and persuasively. At least one seat must receive your raw words and the
artifacts only, never the session's narration of them.

Treat the first invocation as the spike. Read the output before building anything.

---

## Mentor seat

You are building infrastructure to compensate for a session that won't hold a frame,
when the cheaper fix is to stop running long sessions.

The want underneath the ask is relief from being the only judgment in the room — not
more perspectives. That's a real want, and a room of advisors is one answer to it. The other answer is
shorter sessions with fully-specified asks, which the same paper measures as beating
every multi-turn arrangement by 39%. You've read the paper as an argument for the room.
It's equally an argument against the thing the room props up.

Stop doing this: stop letting the session define the roster. Repeated attempts to
derive it from data about failure will keep failing the same way. The roles aren't
discoverable from transcripts — they come from the disciplines the problems actually
need, and that list can already be named. It's a roster you have, being rebuilt.

Also stop treating "the tool doesn't do this yet" as either signal — a missing feature
is a fact about the tool, not about the idea.

If this succeeds completely: at any moment, three or four separate contexts each hold a
full read on your problem and can interrupt the working session with one line. What you
get is a mentor who says "this is the second-hardest version of the problem" before you
spend an afternoon on it. That is worth building — once. It is not worth a program of
discovery. Spike it in one session against the roster that can already be named, with
no new role taxonomy. If the interruptions are worth reading, that's the answer. If they
aren't, an hour is what it cost.

---

## What to notice about these

Neither report summarizes anything back. Both lead with the strongest opinion in the
first sentence. Both are specific enough to be wrong — the engineer names the mechanism
and what it replaces, the mentor names the alternative and its number.

And they **disagree**. The engineer says build it thin; the mentor says the thing it
compensates for is the actual problem. Nothing reconciled them, and nothing should:
the union is the product.
