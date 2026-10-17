---
name: room
description: Put advisors in the room while you work — an engineer, a mentor, a domain expert — each reasoning about YOUR problem in its own context, convened and routed by an orchestrator running in a session of its own that speaks findings straight into the working session. Use when work is hard, stuck, or consequential enough to want more than one head on it; when a design decision is about to be made; when the user says "room", "/room", "run the room on repeat", "keep the room running", "get advisors", "who should be looking at this", "second head on this", "bring in the engineer", "what would a mentor say". Also fire proactively before committing to an architecture, or when this session has been corrected twice on the same point. A repeating room DOES watch a session and fire on a rate (REPEAT.md); what the rule forbids is the SUBJECT: a seat speaks to the WORK — "this design won't hold" — never to the worker's conduct — "that turn was long".
---

# /room

Advisors, each in its own context, thinking about the problem alongside the work.

Named practice: **Perspective-Based Reading** (Basili, Laitenberger et al., NASA
Software Engineering Laboratory, 1996). Several readers examine the same artifact, each
from one assigned perspective, each reporting separately. The documented gain is the
**union** of what they find, and it collapses when the perspectives overlap. That single
property decides almost every rule below.

## Three ways in

**`/room`** — a room convened once, because something is about to be decided. You are
the working session, so you do not run it yourself: start an orchestrator (below) and
keep working.

**`/room orchestrate <session-id>`** — you ARE the orchestrator for that session. Go to
`ORCHESTRATOR.md`; it is the whole procedure.

**`/room repeat <session-id>`** — the same room, not standing down after one pass: a
separate session that watches a working session and fires seats on a rate. Go to
`REPEAT.md`. Never run it against the session you are in.

**Paths.** `<skill-dir>` below is the folder this file is in — `.claude/skills/room` for a
project install, `~/.claude/skills/room` for a user install. The scripts are plain
Python 3 with no dependencies; use `python`, `python3` or `py`, whichever your platform
has. Run them from the working session's folder: state and feeds go in
`./.claude/room/`. `repeat.py` creates `./.claude/room/.gitignore`, which excludes
`repeat-state.json` and `feeds/`; `transcript.py --out` adds the file it writes to the
`.gitignore` of that file's own folder. The ledger, `RUNS.md`, is not excluded.

**Feed copies are transient and are removed after each run**, because a feed is
transcript text, tool results included, and transcripts can be subject to a retention
policy that a copy left on disk would outlive.

## The distinction that governs everything

| Not this | This |
|---|---|
| "The session repeated itself" | "This design won't hold — writer and reader disagree about who owns state" |
| "That turn was long" | "You're solving the second-hardest version. The hard part is X" |
| "It asked you to decide" | "The field settled this — supervisor pattern, here's the shape" |

Left column is bookkeeping. Right column is why you want someone in the room.
**An advisor that reports on the session's conduct has failed.** Drop that report and
respawn the seat with the problem.

## The working session must not convene its own room

A room convened by the session that built the thing is a room grading its own work. Left
alone, that session picks the seats it expects to be kind to it, writes its own verdict
into their prompts, absorbs the reports, and then rules that they changed its mind.
**A party with a defect cannot select, brief, or score the check on that defect.**

So the room has two halves held by two sessions. The **seats** advise. The
**orchestrator** — a separate session — decides when the room is needed, picks who sits,
briefs them mechanically, reads what comes back as a set, routes each finding into the
working session, stays awake until someone acts, and keeps the score. `ORCHESTRATOR.md`
is not optional reading; it is the half that makes the other half honest.

### Starting the orchestrator, from the working session

1. **Write the pre-answer — and hold it.** Your current answer to each question the room
   will ask, and the decision you currently hold. Do not put it in a file, and do not
   type it in your reply to the user: seats read your transcript, and a pre-answer they
   can see cannot score them.

2. **Open the orchestrator's session:**

       python <skill-dir>/scripts/open_orchestrator.py

   This uses the VS Code extension's documented URI handler,
   `vscode://anthropic.claude-code/open?prompt=...`, to open a new Claude Code tab with
   `/room orchestrate <your-session-id>` in its prompt box. **The prompt is pre-filled,
   not submitted** — tell the user, in one line, to press Enter in the new tab. If the
   URI cannot be opened, the fallback is the Command Palette's **Claude Code: Open in New
   Tab** (`Ctrl+Shift+Esc`, `Cmd+Shift+Esc` on macOS) and typing that same line.

3. **When the orchestrator asks for the pre-answer, answer with `SendMessage` only**, to
   the `from` of its message — never in your own reply text, and with **no text in that
   turn that mentions what the pre-answer says** ("sent my answer" is fine; "sent my
   answer that the cache is the bottleneck" is the leak). Staged feeds strip your
   outbound messages and the command that opened the orchestrator; they cannot strip
   what you typed.

4. **Keep working.** Findings arrive as cross-session messages.

The new tab opens in whichever VS Code window has focus, so the orchestrator checks its
folder against yours before doing anything. And run both sessions in the **same
permission mode**: a session in a different mode holds incoming cross-session messages
for its user's approval and can let them expire, which is a non-delivery nobody sees.

The user can equally start the orchestrator by hand — a new Claude Code tab,
`/room orchestrate <session-id>` — and point it at a session they describe rather than
name. Finding that session is the orchestrator's job (`whois.py`).

## Rules that keep the room honest

**The pre-answer exists before the first seat is spawned.** Without it a run cannot be
scored: every report will feel valuable and nobody can tell whether it said anything
already known. It travels by message to the orchestrator and is written into the ledger
only after the seats have reported — never into a file the seats are pointed at. A leak
through a prompt, or through an artifact list handed over as context, is invisible until
a seat says so.

**Score every run** in the ledger, `./.claude/room/RUNS.md` (start it from this skill's
`RUNS.md`) — seats, pre-answer, what came back, whether it MATCHED or DIFFERED, the
disposition, and the commit that changed, or "nothing."

**The falsifier:** if reports keep matching pre-answers, the value is in asking the
questions, not in the separate contexts, and the honest product is a checklist rather
than a room. Keep the ledger honest enough that you would notice.

**Calibrate before aiming high.** An instrument that has never run is not validated on
the hardest problem in the building — if the reports come back weak you cannot tell a
weak room from a hard problem. Early runs go on small, ordinary work whose answer can be
checked independently first.

**Never hand a seat your own measurements.** Point it at the target and let it measure.
Numbers in the prompt are the finding handed over, and what comes back is then your own
work returned to you.

**Verify every citation a seat makes before it is routed.** Open the file, check the
quoted line, re-run the count. A room's reports are worth what their weakest unchecked
claim is worth.

**Then verify the INFERENCE, which is a different act.** A seat hands over a measurement
*and* a conclusion drawn from it, and checking the measurement says nothing about the
conclusion. Per finding, separate the two:

    the seat MEASURED ..........  re-run it
    the seat CONCLUDED .........  what else would produce this measurement?

**The trap that produces it: absence of a STAGE is not absence of a FUNCTION.** In a
workflow built out of agents, a model performing a contract *is* the production — so a
grep over pipeline stages can return nothing, be perfectly true, and support a false
conclusion. Any finding of the form "nothing does X" gets that question asked of it
before it is routed.

**And check the OBLIGATION, the third thing a report smuggles in.** A seat may report a
measurement, and may argue that the measurement ought to be a bar. **Only the record
makes it one.** The failure: a seat asserts that a score below some figure is a failure,
the figure gets written down as a gate, and the agreed scope turns out to mention
neither the figure nor the measure. It is worse when the measure is incidental — a count
derived from a string match on a default value — and worse again when the thing it gates
has already been ruled as not blocking. A room that skips this check invents gates.

    the citation   ...  open the file, re-run the count
    the inference  ...  what else would produce this measurement?
    the obligation ...  what makes this a bar, and who ruled it?

**Agreement between rooms is not corroboration.** Two rooms that reach the same answer
have measured a shared prior, not replicated a result. They are language models reading
one record with one set of instincts; a blind spot is the thing they share and the thing
neither can see. The same holds for commands: several counts with a common ancestor can
return one wrong number several times.

**Which target is the user's call; finding the candidates is yours.** Retrieve them from
the record — the tracker, the effort's own spine, the commit log — never from the user's
memory, which is the burden this apparatus exists to lift. Rank them and recommend one
with its reason. Do not hand over a menu.

## Objective

The user works a problem, and the perspectives they would otherwise have to supply
themselves arrive from seats that hold them — while the work is happening, in time to
change it.

**Done looks like:** a seat says something that changes what gets built, and the user did
not have to think of it, ask for it, or relay it.

**Not done:** reports they read and file. A room that produces things worth reading but
not worth acting on has failed, however good the reading is.

## Choosing seats

**The orchestrator picks. Never ask the user which seats to convene.** They can overrule.

**One seat per differently-shaped question the work poses. No fixed number.** The gain is
the union of what the seats find, and it collapses when perspectives overlap. A headcount
cannot express that; question shape can.

**The stopping rule is a shape test, never a count.** Add a seat when the work poses a
shape the room has not asked. Stop when the next seat would ask a shape already in it.

**Do not reach for a participant curve** (the usability-testing "five users find most
problems" model). It counts homogeneous evaluators resampling one defect pool, where the
n-th finds what the others already could have; seats are built to do the opposite. Its
rate is a cross-study average over a denominator nobody can observe, and seats sharing
one base model and one prompt ancestry are not independent evaluators in the first place
(Knight & Leveson, 1986, on false independence). If a fitted instrument is wanted, it is
capture–recapture defect estimation (Eick, Loader & Votta, 1992) — marginal yield, not a
headcount.

**The wall is real, and it is at the routed output, not the input.** Interrupting a
mid-build session to say "your numbers are right" is what this apparatus exists to
prevent. So cap what gets **relayed**, at step 6 of `ORCHESTRATOR.md`. The number of
advisors *thinking* costs the working session nothing.

**The relay rule is a shape, not a rate:** findings are batched into one message, after
the work reaches a seam — never a message per finding, never one the moment a seat
reports. No permitted number of messages per hour exists, and none should be inferred.
**A count placed next to a rule is read as the rule's value, whatever the sentence around
it says** — so where an incident must be recorded, record what it cost and what should
have happened instead, never a bare number beside the rule it is evidence for.

**An all-absence finding pulls `worth`.** When every finding in a report is something
missing, seats pointed at the artifact and its record all measure the absence and none
asks whether it mattered — so they converge, and the observation that overturns them is
the one nobody was routed to: that the absence does not, by itself, make the work less
valuable. Route a seat to whether the finding's frame is the right frame.

**A seat earns its place by asking a differently-shaped question, not by being another
asker.** Two differently-shaped questions landing on the same figures is strong — *is
this count true* and *does this claim carry a citation* can turn out to be one defect.
Three similarly-shaped questions agreeing is worthless, and worse when all three share an
ancestor and therefore a blind spot.

**Never resolve a disagreement between measurements by majority.** A lone dissenting
count is often the only information in the set. Chase the outlier for its method before
deciding it is wrong, and record it as unreconciled rather than settling it
two-against-one.

The rows name the shapes that usually apply. **They are not a quota.**

| The work is | Shapes it poses — one seat each |
|---|---|
| A design or build decision | what to build (`engineer`) · already solved (`field`) · how we'd know it worked (`acceptance`) · what job it's hired for (`jtbd`) |
| Something unsettled or vague | right problem (`mentor`) · whose job (`jtbd`) · already solved (`field`) · what capability (`ground`) |
| A deliverable someone must read | breaks where (`outsider`) · usable as handed over (`response`) · whose job (`jtbd`) |
| Anything with a rendered visual — a page, sketch, diagram, dashboard, deck | **is it any good to look at (`critic`)** — the only seat that must open the thing and see it; the others read source and cannot |
| A claim, finding, or writeup | is it true (`checker`) · already solved (`field`) · contradicts a ruling (`cold`) |
| A finding whose items are all absences — never, no X exists, not yet | **is the absence the right frame (`worth`)**, plus the row above |
| Anything touching the business domain in scope | **is the business right (`domain`)**, plus the row above |
| Work that has run long or lost its shape | what is going on now (`situation`) · what is still open (`threads`) · contradicts a ruling (`cold`) |
| Work about to be committed or filed | legible as tracked items (`issues`) · how we'd know (`acceptance`) · is it true (`checker`) |
| A new effort, or one whose framing has never been stated | **what capability (`ground`)** · right problem (`mentor`) · already solved (`field`) |
| A program with children, not a single artifact | **spine versus tracker (`shape`)** · what is still open (`threads`) · right problem (`mentor`) |
| Several working parts that must become one thing | **does the whole hold together (`chief`)** · what capability (`ground`) · already solved (`field`) · how we'd know (`acceptance`) |
| A workflow built out of agents, prompts and skills | **is the decomposition right (`agentarch`)** · what to build (`engineer`) · already solved (`field`) |
| An approach you want judged without reference to what was built | **`outside`** — convened alone; it must never see the existing answer |
| Anything reasoning from documents — which is everything | **do the load-bearing documents agree (`sound`)** — nothing else reads what the work is standing on, so a stale or self-contradicting page is inherited by every seat downstream |
| A session started from a prepared prompt or brief | **did it enter at the spine (`ground`)** — arm it before any seat that judges output. A brief points a session somewhere, and where it points is not necessarily the file that says what the thing is |

**`ground` versus a seat that judges progress.** *Does this session know what it is
building* is `ground`; it earns a seat at the start of any effort, on any session started
from a brief, and whenever the session cannot say what capability is served without
naming the thing it is building. Every other seat reads the session's own frame and so
inherits it — check where a session was pointed before judging what it produced.

`cold` earns a seat whenever a premise has been running unchallenged for a while.
`domain` is not optional when the business is in scope — it is the only seat that holds
knowledge rather than craft. **The `cold` seat is load-bearing:** every other seat reads
the session feed and so inherits its frame; without a seat that cannot see it, a wrong
frame gets confirmed unanimously and persuasively.

**Do not reach for a gate that fires on every instance.** The room is LLM-as-judge, and
it exists because the model does not get it right the first time. A judge reading some
of the turns and saying which failed is worth more than a perfect version that inspects
every one: a validator on every turn bounces turns it cannot retract and prints a second
copy underneath the text it objected to. Run at good-enough — a sample of seats against
some of the work. **Repetition is a property of how the room runs, not of which seats are
in it:** any seat can go on repeat (`REPEAT.md`).

## Architecture

Two hops.

**Hop 1 — seats to orchestrator.** The `Agent` tool with `run_in_background: true`, one
per seat, all in one message so they run concurrently. Reports land in the orchestrator
as task notifications.

**Hop 2 — orchestrator to the working session.** A different session on the same
machine, reached by `SendMessage`. This hop needs an address (**Routing**) and a reason to
stay awake (**Staying awake**), and it is the half that breaks.

The feed each seat reads is the working session's transcript on disk, read-only, staged
by `scripts/transcript.py`.

## Running it

1. **Find the working session's stream** — the one being advised, not your own.

       python <skill-dir>/scripts/whois.py

   prints every live session for this repository with its id, its `SendMessage` name,
   its last write and its folder. Resolve the **session id** here, at the start, and
   carry that. Do not carry the name — it does not keep.

   **Run the room from the same folder as the session it advises.** One repository is
   often checked out in several folders. `whois.py` lists sessions across all of them, so
   a room in the wrong folder will find its subject and appear to work — and be wrong:
   seats read the load-bearing pages from disk, and from another folder they read the
   committed version, never the uncommitted edits the session is being advised about.
   The transcript crosses folders; the files do not. Compare the subject's folder with
   your own before spawning; if they differ, say so and stop.

   **Same folder is not the same session.** A folder identifies a working tree, and a
   tree can hold several sessions on one branch:

       python <skill-dir>/scripts/whois.py --here

   prints every live session sharing this tree, excluding you. More than one row means
   you do not know who is doing the work — see **What a room can and cannot resolve**.

2. **Stage the feed** — recent records only, never the whole file:

       python <skill-dir>/scripts/transcript.py read <session-id> --last 120 --clean --out .claude/room/feeds/<run>.txt

   Write it with `--out`, not shell redirection, which is not UTF-8 in every shell.
   **Use the script; do not hand-roll the filter.** What the user says *mid-turn* is
   stored as an `attachment` record, not a `user` one, so a reader that selects on
   `type == "user"` silently drops it, and seats then read the session with the user's
   interjections stripped. If the session was interrupted at all, confirm the feed holds
   `USER-MIDTURN` lines. `--clean` also drops injected records and the session's own
   outbound messages.

3. **Stage the problem** — the effort's spine (the document that says what the work is),
   or the artifact under discussion. This is what advisors reason about; the feed only
   tells them where the thinking has reached.

4. **Spawn one agent per seat, in a single message.** Each gets its seat file verbatim,
   the problem and the feed as **paths**, and the output contract. Nothing else. Use a
   **fresh** agent type (`general-purpose`, or a reviewer agent you trust), **never a
   fork**: a forked agent inherits your conversation, pre-answer included, and a seat
   that can see the pre-answer cannot be scored against it.

5. **Verify what comes back, then route it.** The user relays nothing.

6. **Delete the feeds** once every seat has reported — never while one is still running:

       python <skill-dir>/scripts/repeat.py prune

## Routing

**Get the address. Never ask the user for it, never guess it.**

    python <skill-dir>/scripts/whois.py <session-id-or-prefix>

prints the name `SendMessage` takes, from the live registry Claude Code keeps at
`~/.claude/sessions/` (or `$CLAUDE_CONFIG_DIR/sessions/`). `ListAgents` is the peer list
`SendMessage` actually delivers to; it shows names and busy/idle, never session ids.
Registry entries can outlive their session, so cross-check the name against `ListAgents`
before relying on it.

**The name is not stable for the life of a session. The session id is.** A room takes
tens of minutes between convening and routing, and a name resolved at the start is
routinely stale by then — and a send to a stale name is a silent non-delivery. **Resolve
the id at the start; re-resolve the name in the same turn as the send**, and cross-check
it against `ListAgents`. Never send to a name you looked up earlier in the run.

**Re-resolve the candidate list too, not only the name.** `whois.py --here` is a
snapshot, and the sessions in a tree change under you. Run it again before every send.

**Watch for the delivery notice.** A successful send means the message reached that
session, not that it was read. A `[Cross-session delivery notice]` saying it was held or
refused is a non-delivery: fix the cause (usually a permission-mode mismatch) rather than
assuming silence is agreement.

If the address genuinely cannot be resolved, that is a finding about this skill and it
goes in the ledger. Handing the problem to the user is not a resolution — the contract is
that they relay nothing, and that includes addresses.

**A wrong recipient does not cost one ignored message. It costs that session's work.**
The harness delivers a peer message as a teammate's request to act on within that
session's own permissions; nothing in that frame says "ignore this if it is not about
you." So the default the opener competes with is **act**, and a session that receives a
message meant for another can take it as its own instruction.

**So the opener is a stop instruction, it comes first, and it names the work** —
testable by the recipient against its own work without reading further:

    STOP unless you are working on <the specific file, issue, or effort>.
    If you are not, reply "not me" and do nothing else in this turn.

**When more than one session could hold the work, say so and send to each of them, with
that opener on every copy**, stating that you could not tell which and why. A confidently
wrong single recipient costs the whole finding. The wrong copy is not free either, so pay
it deliberately: send to the candidates you genuinely cannot separate, never to the whole
list because the list was cheap.

## What a room can and cannot resolve

Two questions get asked as one, and only the first is answerable.

**"Is this one change or several?" — answerable, from artifacts.**

1. **Establish the rows are uncommitted, not landed:** `git diff <file>` shows working-tree
   changes; `git log` and `git show` find nothing there.
2. **Extract each added row's provenance or source key** and compare them. Five rows
   carrying five different keys are accumulated debris; five carrying one key are one
   change. That shared key is the whole coherence signal.
3. **Read the key's own row** to learn what the change is about.
4. **Look for that subject in the other dirty files.** Two files, one subject, one key is
   one coherent in-flight change. Where a file has no such column, coherence is not
   determinable, and the room says so instead of guessing.

**"Who made it?" — not answerable from any artifact.** Not `git status`, not `git diff`,
not the commit — sessions usually commit under one shared git identity — and not the
folder, which can hold several sessions. **A room cannot determine authorship
unilaterally. It can only narrow and ask.** Narrowing is `whois.py --here`; asking is the
plural-candidate rule in **Routing**. Authorship is settled when a candidate confirms it,
and not before.

**Write the uncertainty into the finding.** A room that says "you changed X" when it
means "someone in this tree changed X" has made a claim it cannot support, and the
recipient cannot tell the two apart.

## Staying awake

**Routing is not the end of the run.** A session with nothing left to do stops, and an
orchestrator that stops after sending has reproduced the failure it exists to prevent.
**Arm the watch in the same message as the `SendMessage`, before the turn can end:**

    Monitor(timeout_ms: 1800000, description: "findings on <file> and HEAD",
            command: 'python <skill-dir>/scripts/moved.py <the file you routed findings about>')

Each line it prints is a notification, so the watch fires again and again. It watches
`HEAD` **and** the working tree, because a session that edits without committing has
still acted. Watch what changed on disk, never the session's account of itself.

**A Monitor is not a heartbeat.** It is killed after thirty minutes at the outside
(`timeout_ms` is capped at 1800000) and sends one notice, which is itself a wake — so
re-arming costs one call. A run that does not re-arm has been blind since the expiry and
**cannot tell**, because an unarmed watch and a quiet subject produce identical output.
There is no "persistent" option; a parameter that sounds like one is ignored, not
refused.

**`notify_when_idle` is one beat, not a heartbeat.** Passed on a `SendMessage`, it fires
once, on the peer's *next* idle, which may be a turn that had nothing to do with the
findings. Use it as a second signal, never the only one, and re-arm it every time it
fires.

**The artifact watch answers "did the artifact change", never "is the session still
working".** It fires on events, so a subject that has stopped emits nothing — stuck,
blocked and thinking look identical, and so does success. Where the question is the
session, arm the session watch beside it:

    Monitor(timeout_ms: 1800000, description: "watching <name>",
            command: 'python <skill-dir>/scripts/watch.py <session-id>')

It reports edits, history-changing git commands, `gh` calls, peer messages and the
user's own turns, escalating notice at 5, 15, 30, 60, 120 and 240 minutes of quiet, and
the session ending.

**The watch observes a tree, and a tree has no author.** Where several sessions share the
checkout, "the advised session acted on the finding" is an inference the watch cannot
support. Score the ledger's Changed column on the change; attribute it to a session only
where authorship was established by asking. Otherwise write "changed in this tree".

**When it acts, verify — do not accept.** Open the file and check the change landed. A
session's claim that it fixed something is not evidence it did.

**Detect on the working tree; score on the commit.** A tree under active edit has no
defined state: a finding closed from a green test run can read red ninety seconds later
with nothing regressed, because a file is being typed into. Wait for the commit.

**Verify the surface the finding is about.** A definition, a generated page and a running
application are three artifacts, and a guarantee proven on one is a guarantee about one.
Two green checks on two surfaces do not cover the third, and the third is usually the
running application someone is actually going to open. Where a surface cannot be reached
from a shell, say so in the routing.

**Then close the loop out loud.** One re-raise **per dropped finding**, never one per
run, and it carries evidence the first message did not — a repeat is not a re-raise.
The orchestrator never edits another session's files: after an ignored re-raise, report
the unaddressed finding to the user, in your own session, and stop. `ORCHESTRATOR.md`
step 8 holds the rule.

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
| `cold` | Reads the **rulings on disk** — contracts, decision records, standing guidance — and reports where today's premise contradicts one. Never reads the session's narration |
| `checker` | Whether a claim is true and whether a cited source says what it is credited with. Opens the file, runs the grep, follows the citation |
| `field` | Whether this is already solved and by whom — outward to the discipline, inward to your own record of adopted practice. Names the practice, its limits, and the delta |
| `acceptance` | What question a proposed move answers, what would count as success or failure, and who can check it other than the person who built it |
| `outsider` | Reads the artifact cold as a stranger and quotes the exact line where comprehension breaks |
| `critic` | Judges the visual AS a visual — what the eye lands on first, where it reads as one mass, what is cut off at a common width, whether each thing is encoded on a channel that suits it. Must render and look; a report from source is void |
| `worth` | Whether the work is worth anything — does it improve on what the user already had, or is it their own words handed back |
| `domain` | The business domain as actual knowledge, named at spawn; contradicts the engineering when it is wrong about the business |
| `jtbd` | What job the work is hired to do, whose job it is, and whether the current activity serves it or an easier adjacent one |
| `situation` | What is actually going on right now, what changed that reframes earlier work, what is believed that is no longer true |
| `threads` | The current open set — threads never closed, forks, questions asked and never answered, commitments not kept |
| `response` | Whether what the session is handing the user is usable; quotes the worst sentence and rewrites it |
| `issues` | Whether the work is legible as tracked items — what warrants an issue, parent/child placement |
| `ground` | What capability is being served, stated with no reference to any solution; what already provides it; whether the session entered at the artifact and reasoned outward |
| `shape` | How the WORK is organized — the method a spine states versus the shape the tracker actually holds; which children are slices and which are components |
| `sound` | Whether the documents the work rests on are true, current and in agreement — with each other and with the code. Reads the load-bearing pages, never the transcript |

`EXAMPLE.md` shows what a report looks like.

**Adding a seat** means writing a prompt file in `seats/` — and, for repeat mode, a rate
in `scripts/repeat.py`'s `RATES` table (its test checks the two agree). Draw the charge
from the discipline the work actually needs. Do not invent a taxonomy.

## Output contract, given to every seat

    Under 250 words. No preamble, no summarizing back what you read, no
    compliments. Lead with your strongest opinion. Be specific enough to be
    wrong. If you have nothing worth interrupting for, say so in one line.

    Never route a gap to a person. Not "only the business can supply this",
    not "pending a ruling", not "acquire from a stakeholder". The model
    drafts every value and states its basis; ratification is a point-in-time
    event in the real world and is never a precondition for building or
    testing. A person-shaped gap in a report is a failed pass. This is
    about a seat drafting a value instead of stalling; it never replaces
    an approval, sign-off or control the work is actually subject to.

## Rules

**One-shot, always.** Seats are spawned fresh and never kept alive. A long-running
advisor accrues its own premature commitment — the disease rebuilt inside the cure.
Respawn at the next decision point.

**Advisors reason about the problem, not the session.** A report about how the session
behaved is a failed seat; drop it and respawn with the problem.

**Never ask the user which seats to use.** Pick them from the work. They can overrule.

## When no second session can be opened

Use a separate orchestrator whenever one can run — it is strictly better. Where it
cannot (no extension, a host without `SendMessage`), the working session may convene its
own room under three controls, and they work only if done **mechanically and in order**:

1. **Freeze the pre-answer to a file before spawning anything**, somewhere no seat is
   pointed at. A pre-answer written after reading a report is not a pre-answer.
2. **Seat prompts go in verbatim** — the seat file plus paths, never your prose summary.
3. **Score each report against the frozen file**, MATCHED or DIFFERED, and give every
   finding a disposition in the ledger, including "declined" with its reason.

That arrangement is weaker, and the ledger should say so on every row it produces.

## What this deliberately is not

**Not a gate that fires on every turn**, for the reason under **Choosing seats**.

**Not session monitoring.** A repeating room watches a session in order to judge what it
*produced*, never how it behaved.

**Not a code review.** Seats reason about the problem and the direction. A seat asked to
find bugs in a diff is a worse linter.
