# Running the room on repeat

A convened room meets once, about a decision. A repeating room keeps meeting. **That is
the only difference.** Same seats, same prompts, same verification, same routing — the
room just does not stand down after one pass. You are a separate session watching a
working session; `ORCHESTRATOR.md` steps 5 to 9 govern what you do with each report, and
they apply here unchanged.

Start it the same way as an orchestrator — from the working session,
`python <skill-dir>/scripts/open_orchestrator.py --repeat`, or by typing
`/room repeat <session-id>` into a new Claude Code tab.

## Any seat, chosen per session

There is no special class of seat for this. Every seat carries a rate in
`scripts/repeat.py` and any of them can be put on repeat. **Choose them by what the
watched session is actually doing**, by the same table in `SKILL.md` that a convened
room uses.

    python <skill-dir>/scripts/repeat.py arm <session-id> checker engineer response

`arm` caps nothing. Pacing is the per-seat rate, which fires one seat per wake — arming
many does not mean many at once, and a fresh arming staggers them so they do not all
come due together. **The wall is the recipient, not the roster:** a working session
interrupted mid-build is the cost, and the user receives fit, taste and priority calls
too. Cap the relay, not the number armed.

**Two seats key on the work rather than the session.** `shape` judges how the work is
organised and `sound` judges the documents it stands on; neither moves when a session
types. They come due when the **spine** — the document that says what the work is — or
`HEAD` changes, so arming either names one:

    python <skill-dir>/scripts/repeat.py arm <session-id> shape sound --spine <path>

`shape`'s feed is the spine, and it reads the tracker the work lives in itself, against
it. `sound`'s feed is the spine and it finds the other load-bearing documents itself;
neither is handed the transcript. With a spine armed, `chief` and `mentor` get it ahead
of the transcript too, because their subject is the work and not the session.

## What sets the rate

**Not turns.** A session can take twelve turns of tool calls and put nothing at stake.
Each seat keys on the thing that carries its risk: **claims that reach the user** or
**writes that reach disk** — "a claim about to be built on", counted. `cold` keys on the
**user's own turns**, because their words are its whole input; keyed on the session's
output it would come due with its feed unchanged and duplicate itself.

**The rate moves with what is found**, simplified from ANSI/ASQ Z1.4: tightened on a
finding, back to normal after two clean passes, reduced after four. That is acceptance
sampling's answer to "you cannot inspect every unit," and it is the part a fixed interval
lacks.

**Every interval in `RATES` is a starting guess.** Change one only from what passes
actually find, and record why in the ledger first: a seat that keeps returning "nothing
worth interrupting for" is firing too often; one that finds something the user already
had to say themselves is firing too rarely.

**A rate change does not reach a watch that is already running.** `repeat.py watch` loads
the table once at start, so an edited number leaves the live watcher on the old intervals
— which reads exactly like the edit having failed. Stop the Monitor (TaskStop) and arm it
again.

**Bursts.** A session works in bursts, and the sharpest one is the burst the room causes
by routing findings: write-keyed seats then come due on writes the room provoked, already
tightened by the finding that provoked them. The counter cannot tell those writes from
independent ones. When you have checked a window yourself — opened the commits, run the
counts — record it as `covered`, which advances the counter without moving the rate.

## Permission prompts

Where a project's permission allow-list is not honoured — some managed installations
ignore it by policy — every `stage`, `record` and Monitor command prompts in the room's
tab, and so do the seats' own shell calls. Both sessions should stay in the same
permission mode (`SKILL.md` → **Starting the orchestrator**), so loosening only the
room's mode is not the answer. A standing room in that environment needs someone at its
tab to approve commands, and it degrades to "fires when approved" without one. Say so to
the user when you start, rather than letting a silent stall read as a quiet session.

## The procedure

**1. Never judge the session you are running in.** A session grading itself is the
room's founding defect. `arm` and `stage` refuse it: the harness puts the session id in
`CLAUDE_CODE_SESSION_ID` and the scripts compare. Where the variable is absent the room
still runs — a guard that cannot read its input must not become a lock.

**2. Find the session to watch**, and check its folder is yours — `SKILL.md` → **Running
it**. Most recently active is not "the one doing the work"; `whois.py --here` lists
everyone sharing your tree.

**3. Arm the seats the work calls for, then sleep:**

    Monitor(timeout_ms: 1800000, description: "seats due on <name>",
            command: 'python <skill-dir>/scripts/repeat.py watch <session-id>')

Each line it prints names one due seat and the exact command to stage it. Between lines
this costs nothing. **Do not poll it and do not loop in your own context** — that
accumulation is what the one-shot rule exists to prevent.

**This watch is silent on silence, and that is not a watch on the session.** It fires
when a seat's counter crosses a rate, so a session that has stopped producing claims and
writes produces nothing here — stuck, blocked and thinking all look identical. Arm the
session watch beside it:

    Monitor(timeout_ms: 1800000, description: "watching <name>",
            command: 'python <skill-dir>/scripts/watch.py <session-id>')

The two answer different questions and neither substitutes for the other.

**Re-arm both at every expiry.** A Monitor is killed after thirty minutes at the outside;
the expiry notice is itself a wake, so re-arming costs one call. A watcher that armed once
and believes it is still watching has been blind since, with nothing arriving either way
to tell it.

**4. One seat per wake.** `repeat.py stage <session-id> <seat>` writes the feed to
`./.claude/room/feeds/` and prints the seat file verbatim with the feed's path and the
output contract appended. Pass that to `Agent` as-is, `run_in_background: true`, as a
fresh agent type — never a fork, which would inherit your context and the pre-answer in
it. **Add nothing** — no summary of where the work has got to, no note on what you expect it to
find, no result from the last pass. Several due at once is several wakes, not one batch.

The staged feed holds the user's turns from the whole session and a cleaned window of
recent activity: injected records, peer messages and the session's own outbound
messages are removed. `cold` gets the user's words alone, and declines on a session the
user never typed into, because a seat handed nothing does not return nothing — it goes
looking, and judges whatever it finds.

**5. Verify before routing.** The citation, the inference, the obligation.

**6. Route to the watched session**, re-resolving its name in the same turn, opening with
the STOP line. The user relays nothing. `ORCHESTRATOR.md` steps 6 to 8 govern routing,
staying awake, and the one re-raise per dropped finding.

**7. Record the pass:** `repeat.py record <session-id> <seat> found|clean|covered`. The
verdict sets the next rate. A pass that ran and was not recorded comes due again at once
and looks like a bug. `record` also deletes that seat's feed: feed copies are transient,
because transcripts can be subject to a retention policy.

**8. When the room stands down**, and at the end of every run, with no seat still
running: `repeat.py prune` deletes every feed copy left in `./.claude/room/feeds/`.

## The room stays a loop

It is long-lived; **every judge it spawns is one-shot and fresh.** It holds the loop, the
rates and the routing, and never an opinion. It does not carry a judge's verdict into the
next spawn or accumulate a view of the work between passes. **If it finds itself arguing
rather than dispatching, it has become an advisor and must be re-spawned.**

## Its own falsifier

**If the repeated judges keep reporting what the watched session already knew, repetition
adds nothing**, and these seats should go back to being convened on demand. Score every
pass against a pre-answer held outside the files the seats read — in your context, asked
for by message — and say so plainly if it fires.

## Not this

- **Not session monitoring.** It judges what the session produced, never how it behaved.
  A pass reporting on conduct is a failed pass — drop it and re-spawn.
- **Not a gate.** It blocks nothing. Enforcement firing after the text is written prints
  a second copy underneath the first.
- **Not perfect, and not trying to be.** It reads a sample and misses things. A judge
  that catches some of what the model misses is worth having.
