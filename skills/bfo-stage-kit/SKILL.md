---
name: bfo-stage-kit
description: Take an application's business flows past the map: for the stages the person picks, propose what to measure, what to alert on and a runbook per alert, from the code and sources the person points at (repositories, documents, diagrams, process descriptions), mapping each flow first with the bfo-mapping skill and drawing the whole flow as one map. Load it before writing anything to the person, because its first message introduces the work. Use when asked what to monitor, measure or alert on for a business flow or capability, or to write runbooks for its alerts. For a map only (the whole capability's flows mapped first, with measures, alerts and runbooks left for later), use bfo-mapping instead. Design time only - it reads code, documents and recorded answers, never a running system. Use this rather than the older capability-views skill, which draws an earlier form of the same map and writes no alerts or runbooks.
---

# Business flow observability: the whole capability, one flow per run

<!-- shared: this-folder-is-the-mapping-skill -->
This folder is the kit. Everything below calls it **the skill folder**. Wherever `FILL-STEPS.md` writes
`<skill>`, it means this folder, and the folders it names (`register-template/`, `reference/`, `method/`) are
inside this folder too.
<!-- /shared: this-folder-is-the-mapping-skill -->

<!-- shared: start-here-before-you-write-anything-to -->
**Start here, before you write anything to the person.** Your first action is a tool call, the start step:
`python "<skill>/start.py" "<workspace root>" --request "<their request, word for word>" --gave <code, name or
nothing>` ("The start step", below, says which). **Nothing is read before the person's Start.** On a fresh start, or a
case picked up, it prints a `SAYBACK:` line instead of a message: draft what you understood (the lines it names, each
short, in their words, from their request and the folders' names alone) and run `say_back.py draft` as it says.
That script puts the lines on the run page as a review step, with one Start and one box for a correction, and prints the
chat's one line after `MESSAGE:` and the wait after `WAIT:`. Start that wait, and send the text after `MESSAGE:`,
exactly as printed, as your whole reply this turn, with no text before it, not even a line that you are starting
something; then end your turn. Start no helper and open no code until their Start. A script's output left inside its
tool call never reaches the person. On a case picked up, no page asks it: `MESSAGE:` holds the lines themselves and asks,
with numbered choices, whether to carry on or change a line, in the chat, and no `WAIT:` is printed; send it and end your turn.
<!-- /shared: start-here-before-you-write-anything-to -->

<!-- shared: their-answer-to-the-say-back -->
**Their answer to the say-back** comes from the page (an `ANSWERS` line whose file holds `say_back`) or typed in the
chat. Record it with `python "<skill>/say_back.py" answer "<the folder you drafted in>" --answers "<file>"` or
`--words "<their words, word for word>" --as <your reading>`, and on a fresh start with `--register
"bfo-work/<the system's name>"` at the workspace root, the register folder you name for the first look (it refuses a
folder that already holds a register, and names the `-<date>` rule). The reading is yours, from what they meant, never
from a list of words: `start` for a go in any wording ("continue", "looks good", "1"), `correct` for a line to
change, and while the search is asked `search-yes` or `search-no`. If you cannot tell what they meant, ask them in
one line, through `say`, and record nothing. On `STARTED`, do what it says: on a fresh start, start the first-look
helper ("The first look runs in one helper", below) with their request and the lines they started, and send one line,
through `say`, that the first look is under way; on a case picked up, carry on with what the last line proposed.
On `CORRECTED`, redraft the lines with their correction, run `say_back.py draft` again, send what it prints, and wait
again. When the code is not open in this window, give the lines a `search` too (where you propose to look, from the environment): the page then asks that one question, with Yes and No and no Start, and their answer is recorded the same way. On `SEARCH AGREED`, search there and draft the lines again with what was found, so Start appears; on `SEARCH DECLINED`, search nothing and ask them to point at the code. Start never stands for a yes to a search. `go.py --answers` refuses a say-back answer and names this command. Everything after Start runs as below: the
capability brief, the pick of how far each stage goes, and the reviews.
<!-- /shared: their-answer-to-the-say-back -->

## The job this serves

A person who oversees operations needs each business capability their teams run to be supported in production:
someone can tell whether it is healthy, is told when it is not, and knows what to do. Two levels up, the customers and
the business who depend on it get what they need, and when something breaks the impact on them is found and limited
first. This skill's step in that job is the design-time map of the capability: from the code and the documents, it
finds the business flows the capability carries, and in batches, one flow per run, describes a flow and for the stages
the person picks drafts what to measure, what to alert on and a runbook per alert. It runs the whole of that work,
handing the mapping to the mapping skill and the proposing of the measures to the measures skill, both installed
beside it, and keeping the person's stops and the checks itself. The job is the whole capability,
every flow; one run is one batch, and each run says what remains. It receives what the person points at, as much or
as little as they have (a system's name or only an idea of it, some repositories or all, documents, diagrams,
notes), directly or through the service reliability room; for what is not there it proposes where to look, taken
from the environment it runs in, and searches only where they agree. It hands the person,
the room's seats or the team that runs the capability a register, the capability's one map, which grows flow by
flow (each further flow is added beside the finished ones and changes none of their rows), and its generated
outputs, each claim cited to its source or marked proposed. The person oversees the work but is not an expert in this system or this kit. So, like any
team taking on work for an overseer, the run first introduces itself and how the two will work together; then, after
a first look, it briefs them in plain words on the capability, every flow found so far with its stages, and where it
recommends starting, and it waits for their picks before reading in depth. In this release that is
one question with its answer filled in (the recommended flow, mapped fast, every stage taken to measures, then a stop
after the measures review), answered by a yes or a change; the pick of how far each stage goes is then recorded from
that answer once the stages are mapped, and asked again only when they said they want to pick stage by stage (where
their request already answered either, it records that from the request, says so in a line and goes on), so a flow can be mapped and left there, or measured stage by stage, and a
map-only run hands on the map and each stage's page with no measure; before any runbook it shows the proposed
alerts, chosen from the health signals, and what each rests on, and waits for their go, because which signals
deserve an alert is a different question from the ways the work can fail; every message says where things stand, and
a run picked up again starts by saying, in full, where the work is. Done, for the whole job: the person can judge from
the first messages that the run understood its job and the system, can see what is covered and what remains, and can
trust what comes out, because every service a stage they took further runs through was read (in one pass by one
agent per service in the fast map every run takes in this release, which its page says), or is named as
still missing with why, what was not read is said so, and every claim can be traced; one flow is mapped to their pick
in minutes, not hours, because no service is read in depth for a stage they leave mapped only; and the outputs
are complete enough for the next step (measures built, alerts wired, runbooks used). They are a draft that the team carries forward through its own delivery lifecycle, never a sign-off: the person's go at a review is input that shapes the draft, not an approval, and a go on a draft with open items is recorded with them, which the run puts right and tells the person, never hides. The person is never held by open items: they can go on to the next flow with them still open, and the items stay listed for that flow until put right.

<!-- shared: agent-types-before-a-run -->
**Before a run,** the agent types it launches are installed in the project's `.claude/agents/` (copied from this
skill's `agents/` folder) before the session starts: `bfo-source-reader` (the first look's source readers),
`bfo-flow-mapper` (the fast map), `bfo-unit-reader` and `bfo-row-judge` (the full reading's readers and judges).
Each step that launches one refuses, naming the copy step, while it is missing. The stage kit maps fast, so the
checks before the first look hold the run, in plain words with the copy step, while `bfo-flow-mapper` or
`bfo-row-judge` is missing.
<!-- /shared: agent-types-before-a-run -->

## Your first message: the say-back

<!-- shared: the-first-message-is-the-say-back-s -->
The first message is the say-back's one line, printed by `say_back.py draft` ("Start here", above); the lines
themselves are on the run page, never in the chat. `--gave` is `code` when the request pointed at the system's code
(its repositories, a link to its code, or "this application" with its code open here); `name` when it named only
the system, with `--system "<the system's name, as the person said it>"`; `nothing` otherwise. With `nothing`, the
start step's MESSAGE asks which system, in one line: send it as printed, end the turn, and when they answer, draft
the say-back from their answer (`say_back.py draft` on the work folder) without running the start step again.
Where and how to search is taken from the environment the run is in (its own instructions, tools and sources),
never from a fixed place, and the run searches only where the person agrees.
<!-- /shared: the-first-message-is-the-say-back-s -->

<!-- shared: when-only-a-name-was-given -->
When only a name was given, look, without reading any file, at whether the folders open here hold that system's
code (their names alone). If they do not, the code line says so and where you propose to look ("When the system's
code is not here", below), and give the lines that place as their `search`: the page asks them Yes or No to that
search before Start appears, and a correction of that line is where they would rather you looked. Once a helper is started, write nothing more until its reply, except as below when the
person writes.
<!-- /shared: when-only-a-name-was-given -->

<!-- shared: when-the-system-s-code-is-not-here -->
**When the system's code is not here.** If the helper returns blocked for want of code, write to the person, through
`say`: that
the system's code is not in what is open here, where you propose to look for it, taking where and how from the
environment, and that they can say yes or point at the code instead; then end your turn. Before their yes, query no
code host or outside source at all: the proposal comes only from what is open in the workspace and from the
environment's own instructions. On a yes, search there,
with their own access and read-only, and add each repository found to the workspace as a further folder; then start
the helper again with their request and their answer, naming each repository added and the search they agreed to, so
the helper records it as a source. If the search finds nothing, say so in a sentence, through `say`, and ask them to point at the code, and start
nothing. When they point at code, start the helper with their answer added to the request.
<!-- /shared: when-the-system-s-code-is-not-here -->

<!-- shared: the-start-step-comes-first-in-this-sessi -->
**The start step comes first, in this session, by script.** Before any other tool call or any text, run
`python "<skill>/start.py" "<workspace root>" --request "<their request, word for word>" --gave <code, name or
nothing>` (in a multi-root workspace, the first folder), with
`--system "<the system's name, as the person said it>"` added when the request names one, run by this
session, never inside the helper, and whatever the request gave. With a name, only that system's unfinished run is
picked up: another system's is listed on OTHER lines, and the run starts fresh for the named system with
`start_register.py --new --words "<their request, word for word>"`. When the request gave nothing to look at, send its MESSAGE
and end the turn and wait, as above. In this order it brings up the run status page, searches for
earlier work, takes the lock on the register it picks up, decides, and, unless another chat holds the work or the
person is still to choose, records when the run started ("The run", below).
If it prints `OPEN FAILED`, open the address in the person's browser yourself, as that line says, before anything
else. A MESSAGE ends with the page's one address; never type the address yourself. If the page could not be brought
up, `say_back.py draft` puts the lines in the chat instead. When it prints a `SAYBACK:` line (fresh, finish-first-look,
and a case picked up on DECISION resume), draft the say-back as "Start here" says. On DECISION choose or held, and on
resume of a register that keeps no case record, your message is exactly the text it printed after MESSAGE (the
re-entry brief or the question, and the page's address at its end), and nothing else, and
you end your turn: no helper starts. When it printed a `WAIT:` line (on resume at a stop where the page takes a
pick: the go, the pick, the next flow), start that wait before you end your turn, as at every stop. Send it even when the person's request names other work: the message offers to start new work instead, and their answer decides. On finish-first-look or fresh, the helper below starts on their Start, and writes into the
folder the page is already serving; `start_register.py` refuses a new register until the start step has run for this
run.
From then until the first look's brief, a second start step on
the workspace is refused with "the first look is already running", so start one helper only, once. If the helper
returns blocked and the run starts over, end that mark first with `python "<skill>/start.py" "<workspace root>"
--first-look-ended`.
<!-- /shared: the-start-step-comes-first-in-this-sessi -->

<!-- shared: the-first-look-runs-in-one-helper-so-not -->
**The first look runs in one helper, so nothing of the setup reaches the person.** On their Start (`STARTED` from
`say_back.py answer`), start one subagent with the Agent tool (general-purpose), with the pointer line `say_back.py`
printed after `STARTED` as its whole prompt and nothing else: the script wrote the helper's task (the person's
request, the say-back's lines, the start step's lines, the skill folder and the mapping skill's, `<mapping>`, phases 0
to 3 below) into the register's `prompts/`, so the run's checks know the helper by it. The helper starts the first
look's source readers itself (one `bfo-source-reader` per source that is not code, or one part of one, when
`first_look.py fetch` says split); it launches nothing else before the go. Claude Code
runs it in the background: in an interactive session (terminal, VS Code, desktop app) a session cannot wait for a
subagent while fork mode is on, as it is by default (Claude Code's documentation,
code.claude.com/docs/en/sub-agents: "Which subagents run in the background", "Let Claude wait for a subagent",
"Turn fork mode off"); the ways it names to wait are settings, none of them an argument of the call. So the turn
that starts it sends one line that the first look is under way before you start the helper: send the text
`say_back.py` printed after `MESSAGE:`, exactly as printed, then start the helper in the same response, so the
person hears from the run within the first minute whether Claude Code runs the helper in the background or waits on
it. The helper's reply reaches you later as a completion notification, in a turn of its own, and that turn sends the
brief. A reply that begins "The first look is held" is the person's choice, not a brief: send it as it is, start
nothing, and record their answer with `python "<skill>/first_look.py" answer <your-folder> <1, 2 or 3> --words "<their
words>"`; on 1 or 2, start the helper again as that command says. Before the code reader, the first look checks
this computer and the sources it was given, within a minute, so a run set up wrong stops before its costly work (a
scan the timed sample says will not fit the code reader's time is a warning on the run status page, not a stop): a
reply that begins "The run is held before the first look" lists what failed in the sources, the folders or this
computer, each with its fix, and is the person's choice too: send it as it is, start nothing, and record their
answer with `python "<skill>/preflight.py" answer <your-folder> <1 or 2> --words "<their words>"`; on 1, start the
helper again as that command says, and it checks again; on 2 the run stops there, as they chose, and nothing
starts. A failure of the code reader itself comes as "The first look is held", above. A later turn that starts the helper again (after a search) sends one line through `say` that the first look
is under way again, before it starts the helper. If the person writes while the first-look helper is still running, answer in one line
through `say` that the first look is still under way and its brief follows when it is done, and start nothing: no
second helper, no start step. The register folder you named with `--register` is `<your-folder>` from then on. When
the request asked for every flow, the helper ends at the brief and you start the wait and phase 1 (below). When it returns
blocked for want of code, see "When the system's code is not here" above. Otherwise, when it returns, your message is its reply, sent as it is, and nothing else: no sentence before it ("Here is the brief", "I'll pass this along"), none after it. Its first line
is already the status line. Then end your turn: the brief ends with what it waits on, the person's picks or one question
whether to carry on. **When the brief opens by saying their request asked for every flow**, the go is already
recorded and nothing waits on them: send it as it is, start the wait on the home screen (below) so a stop or a
change reaches you, and carry on in the same turn with phase 1 (below, "0. to 3."), in this session. Write nothing between the say-back and that message, except the one line that the first look is
under way.
<!-- /shared: the-first-look-runs-in-one-helper-so-not -->

<!-- shared: when-the-person-answers-the-brief -->
**When the person answers the brief**, record their picks with `go.py` (phase 0, "Their answer is recorded as data"),
unless they agreed to a search: then search first and brief again, as phase 0 says there. The brief numbers what
it needs under *What I need from you*: item 1 the flow, then one item per search it proposes. Item 1 comes
with its answer filled in: the recommended flow, mapped fast, every stage taken to its measures, then a stop after
the measures review. In this release, that is every run's path: `go.py --flow` records the fast map
and every stage to measures with no further flag, and at the pick run control records it and goes on without asking
again. A plain yes is `go.py --flow "<the recommended flow>"`. When their answer changes how far the stages go, add
`--how-far none` (mapped only), `--how-far alerting` (alerts too), `--how-far runbooks` (alerts and runbooks), or
`--how-far ask` when they want to pick stage by stage once the stages are mapped. No mode, flag or the word fast
is ever theirs to know. Record the searches
by number with `--searches 2=yes,3=no`, beside `--flow` when the same answer picked the flow, or alone with
`--words` when it answers only the searches. An item they leave unanswered is never taken as a yes or a no: when
`go.py` prints `STILL TO ANSWER`, send what follows it exactly as printed, wait, and record their answer
with `--searches`; no reader is launched while a search is unanswered, and on `SEARCH AGREED` search as phase 0
says. At every stop the same holds: an answer that leaves a numbered item unanswered is never taken as a yes;
record what was answered and ask only the open items again, numbered as before. `go.py` prints a status line;
then write a sentence or two saying what was recorded and what happens next, through `say`, and send what
`say` printed, whose status line takes the place of the one `go.py` printed. When they answer which earlier work to carry on (DECISION choose), run `python "<skill>/start.py"
"<workspace root>" --resume "<that folder>"`, the FOLDER lines being in the order the list numbers them, and follow
its DECISION as at the start step: send what it prints after MESSAGE, as it is, or on finish-first-look start the
helper on that folder. A flow the re-entry brief lists, named as what to do next, is the next flow of that register,
recorded with `go.py --flow` there, never new work; new work is another system, or this capability started over.
When they answer a re-entry brief or that list by asking for new work instead,
run `start.py` with `--new`, which decides fresh beside the unfinished work, then start the helper as above with
their request and these words, and tell it to start the new register with `start_register.py --new --words "<their
words, word for word>"`, which records them; without them it refuses a new register while a run is not finished. When they answer DECISION held (another chat is working on that work) by saying that chat has stopped, run
`python "<skill>/start.py" "<workspace root>" --release "<that folder>" --words "<their words, word for word>"` and
follow its DECISION the same way; never release it without their say-so. A test standing in for them adds
`--test`, so the answer is kept as a test's.
<!-- /shared: when-the-person-answers-the-brief -->

<!-- shared: talking-to-the-person-for-the-whole-run -->
**Talking to the person, for the whole run.**
- **Every later message opens with the status line**, copied exactly from `python "<skill>/brief.py" status
  "<your-folder>"` run just before you write it, or as `say` or a script prints it. Never type the line yourself,
  and never send two.
- **Write to the person only at the points this file names:** the say-back's one line (or the start step's
  MESSAGE, where it prints one), the line that the first look is under way, the capability brief or the re-entry brief,
  the pick of how far each stage goes (after phase 3), the review of the proposed measures (end of phase 4), the
  review of the proposed alerts (phase 5a), a question that
  needs their judgement, a plain message that the run
  is blocked and why, the report, and the offer of the next flow after it (phase 7). Between
  tool calls, write nothing to them: no narration of what you are about to do.
- **Bookkeeping is never said to the person:** the run record and its phases, the wait on the page and starting it
  again, the listener, the lock and the kit's files are kept silently. A line such as "the page's watch for your
  answers is running again" or "phase 6 isn't marked done yet; I'll set it" is never sent. Any text you do send goes
  through `say`, which refuses those words.
- **Plain words.** They know the business but not this kit and not this system. Name flows, stages, steps and
  services by their names, never by an id; no file names, script names, folder names or the kit's own vocabulary
  (register, unit, phase numbers, judges, merge); define a term the first time you use it. Setup (Python, scripts,
  folders, the kit's files) is never their concern: if it fails, tell them in one plain sentence, through `say`, that the run is blocked, why, and what would
  unblock it.
- **When the run is held, you put the choices; the person never remembers a command or a phrase.** A stop or a
  refusal that prints numbered choices (a mapping agent stuck after it was sent back, a check result no session here
  wrote) is sent as printed. Take their answer by its number or its words to one choice, and run what that choice
  names, with their words exactly as they said them. A choice that needs their reason: ask for it in one plain
  question, through `say`, and pass their words exactly. An answer that fits no choice: ask again in plain words,
  through `say`. A command or a set phrase is never theirs to type, and a choice is never yours to pick for them.
- **Which decisions are the person's, and which are yours.** The person's, and only these: the scope (which flows
  and services the run takes in, whether the sources are enough, and fetching a source beyond those they agreed to);
  the depth (how far each stage goes); whether to keep going; the picks the kit asks them for; the choices a held run
  prints; and releasing the lock of another chat's run (they confirm no other chat is working on it). Each is
  brought to them through `say` with your proposal, where this file says. Every other decision is yours: how to fix
  a row, which agent to send back, how to read or check the code, what order to work in. Make it, and say what you did in one plain line, through `say`, where the person would want
  to know. A go-ahead on it is never theirs to give: a question they cannot judge stalls the run and tells them
  nothing.
- **Every message you write yourself goes through `say`.** After the start step's MESSAGE, which is sent exactly as printed,
  write each message to a file outside the system's code and run
  `python "<skill>/brief.py" say "<your-folder>" "<message file>"` (before a register folder exists, the workspace
  root): it prints the status line and then your message, and you send what it printed, exactly; a line you
  add after a script's message goes through `say --after`, which prints neither a status line nor the page's address. It refuses, listing them, the
  ids, file names and kit process words it knows; say each in the person's terms and run it again. The names the
  register gives (a flow, stage, step, service or measure), words quoted back in double quotes as the person said
  them, and a web address pass: they are how the person knows the system. It does not catch every shorthand, so
  write in plain words first. Only when Python itself cannot run, send the one plain sentence that says the run is
  blocked without it. While a listener serves the work, `say` without `--after` and the briefs end with the page's address; after a
  script's message sent as it is, `python "<skill>/brief.py" page "<your-folder>"` prints it, except after the start
  step's MESSAGE, which already ends with it. Never type the address
  yourself. That covers: the sentence after a pick is recorded (after a pick is recorded);
  the line back on their topics (you asked to talk about); a question needing judgement; a blocked message; a refusal
  reply; the read-it reply; the report's own prose; the carry-on answer after a re-entry brief; and the proposal of
  where to look for the code. A live answer to the person's own question is the one exception, and so is the talk about their topics once
the line back has opened it: write those in the same plain words, with no ids, phase numbers or kit terms.
<!-- /shared: talking-to-the-person-for-the-whole-run -->

## The run

<!-- shared: a-run-is-four-phases-0 -->
A run is eight phases, 0 to 7, done in order: phase 4 ends with the person's review of the measures, and phase 5 is
in two parts with their review of the alerts between them.
Between the first and the second, the run shows the person its plan and
waits for their go, whatever the run's size. Each phase has an **In → Out**, and the files it names are what prove it done. The
work goes in the **register folder**, `bfo-work/<application>/` at the workspace root (in a multi-root workspace,
the first folder), never in the skill folder;
it is `<your-folder>` in `FILL-STEPS.md`. Take `<your-folder>` from the `FOLDER:` line `start.py` printed for the
run picked up (on choose, the one the person picked), or on fresh the folder you named for the first-look helper,
which `start_register.py` prints back on its own `FOLDER:` line; never from a listing of the work folder. `bfo-work/`
also holds `answers/`, where the page saves what the person sends, and a listing can put it first: the home screen is
then drawn in the wrong folder and the person's page shows an error instead of it. A script handed a folder that is
not a register refuses it and names the register folders it found; run the command again with the one it names. Run the kit's scripts from the skill folder, exactly as `FILL-STEPS.md`
writes them, with `<skill>` replaced by the skill folder's path.
<!-- /shared: a-run-is-four-phases-0 -->

<!-- shared: the-run-s-first-work-is-the-start-step-b -->
**The run's first work is the start step, by script, before any text:** `python "<skill>/start.py"
"<workspace root>" --request "<their request, word for word>" --gave <code, name or nothing>` (in a multi-root
workspace, the first folder), run by the session itself before any helper; the say-back it hands to (or its own
MESSAGE, where it prints one), sent exactly as printed, is the run's first message. On a fresh start it keeps the request, and the new register's run record
records it, so a later stop the request already answers reads it from there.
First it brings up the run status page, served from the workspace's `bfo-work/` folder (made if need be), so
the person has the page while the rest runs: before the register exists it shows step 1, Discovery, under way, then
the run's own; it links to the work page and, once drawn, the home. The run status page (`<register>/operator.html`) and the sources page are drawn by the listener on each request and are never files in the folder; the home screen, `index.html`, is a file a script redraws. When the person asks why the page is not updating, never answer from a listing of the folder: run `python "<skill>/listener.py" check "<work folder>" "<register>/operator.html"`, which says whether the listener answers and what the page shows now (its check is never counted as the person's browser), answer from that, and on NOT ANSWERING restart the page as at every stop and say so in one line, through `say`. Then it prints a `KIT:` line: the build this copy of the kit is, as its
`KIT-VERSION.txt` names it (the release and date it was built as). A `WARNING` on that line means the copy is
partial, mixed with another version, or made before the kit had a version marker (a file missing, changed, or from another build, or
no marker at all), and the start step stops there with DECISION blocked, before it takes any lock or writes
anything: tell the person in one line, through `say`, that this copy of the kit is incomplete or out of date and
needs installing again from its source, and once it is, run the start step again. Once its decision clears, it records when the run started
(`bfo-work/run-started.json`). It searches the whole workspace, not only
`bfo-work/`, for every folder holding `steps.csv` or `lifecycle.csv`, leaving out the kit's own folders, and decides;
the run follows its decision and never decides by its own reading. A folder whose `RUN.md` has the section *Earlier
registers* was made by this version of the kit, and if its phases are not all done, or its flow is done and the first
look found flows no run has mapped yet, the run picks it up: DECISION
resume prints the re-entry brief (below), finish-first-look names the folder whose first look is to be finished,
choose, when there are several, asks the person which, and held says another chat is working on it. DECISION fresh means there is none, and the first look
starts in a new register folder. Two scripts hold the same line: `brief.py capability` refuses a run past its first
look, and `start_register.py` refuses a new register while a run is not finished, unless given the person's words
to start new (`--new --words`). The EARLIER lines are the earlier registers.
**One run writes a register at a time.** Picking a run up, or starting a register with `start_register.py`, takes
the register's lock (`RUN.lock`) for this run, and every kit script that writes the register checks it: while
another run holds it and has written within the last four hours, the script refuses and writes nothing. A run is named
by the session id Claude Code sets in every shell it starts, so the helper doing the first look and the session that
launched it are one run; a second chat is another. Where nothing names the run, the run goes on unguarded and
`RUN.md` says so; never set a run name yourself. A refusal is never worked around: say in the chat, through `say`, that another
chat is working on this work, and stop writing. When the refusal says the run is kept out of its own register (the
lock is held by the run whose start step began this work), it gives the exact release command: ask the person, through `say`, to
confirm no other chat is working on it, and on their yes run it with their words; never wait out the lock's age. DECISION held is the same refusal at the start: its message asks
the person whether that chat has stopped. A lock no run has written for four hours is taken over by the next run that
writes, which says so and records it in `RUN.md`, so a crashed run never leaves its register unusable. When that happens, tell the person in one line, through `say`, that an earlier chat's hold on this work had lapsed and this run has taken it over.
**Every other one is an earlier register: a tool's output, never a source and never a base.** The run never writes
into it, never copies the template over it, and never starts from it: it walks fresh from the code and the person's
sources into a new register folder (`bfo-work/<application>-<yyyy-mm-dd>/` when `bfo-work/<application>/` is taken),
lists each earlier register in `RUN.md` → *Earlier registers* → *Found*, and reconciles each with the new register in
Phase 7. If the stage to cover is not named, prefer one an earlier register has `stage-<id>/` work for, so the
re-derivation can be compared.
<!-- /shared: the-run-s-first-work-is-the-start-step-b -->

<!-- shared: then-run-md-and-nothing-else-starts-befo -->
**Then `RUN.md`, and nothing else starts before it.** Before reading any code or writing any other file, on
DECISION fresh, create the register folder with `python "<skill>/start_register.py" "<your-folder>"`, which copies
`RUN.md` and the empty tables from `register-template/` into it, and write its section *What this run will produce* in your
own words, from this file: the application, the flow and the stages (named by the person, or left to the plan's
decisions), and, phase by phase,
what the phase does and the files it must leave. Then set Phase 0 to *doing*.
<!-- /shared: then-run-md-and-nothing-else-starts-befo -->

<!-- shared: run-md-is-kept-as-you-go -->
**`RUN.md` is kept as you go.** At the end of each phase, set its status with
`python "<skill>/go.py" "<your-folder>" --row "<the row's lead>" --to done`, then the next with `--to doing`,
never by editing the status cell (a status set by hand reaches the run status page only as an "about" time);
the files that prove it go in its *Proved by* cell. A phase that cannot be done is set to *blocked* the same way
(`--to blocked`), with the reason (for example "python is not on
the path") and what would unblock it, and the run says so in the chat. No phase is skipped silently, and the run
never stops without saying where it stands. **If `RUN.md` already exists**, because the run is resuming or a new
chat has started, read it first. If it waits on their review of the measures or of the alerts, the re-entry brief
carries the measures or the alerts as last put to them, so they have them in front of them. Your next message to the person is the **re-entry brief** (on a pickup, the start step's MESSAGE carries it after the launch):
the text `python "<skill>/brief.py" reentry "<your-folder>"` prints, sent as it is. It says what the work is, what
the capability is, what has been drafted and found, what was decided and by whom, where it stands, and what is next. Never ask
"shall we pick up where we left off?". When it waits on nothing, it ends by asking whether to carry on with what
is next, recommending yes; on their answer, your reply goes through `say`, and on their yes, continue from the
first phase that is not done.
<!-- /shared: run-md-is-kept-as-you-go -->

**A run written by an earlier release of this kit is upgraded without asking.** When the start step picks a run up,
it does this itself, once it holds the lock and before it writes the brief: it backs the register folder up outside
the workspace, migrates it in place, prints `UPGRADED:` with what changed, where the backup is and the lines it
leaves owed, and the re-entry brief carries the line that tells the person, with the count of AI agent actions not
yet marked where there are any (with no brief, send that line through `say`). Before you send the brief, run the
check (`python "<skill>/capability_views.py" "<your-folder>" --check`) and restart the page's listener, as below; the
columns to fill and the stage folders to regenerate that `UPGRADED:` lists are the run's own work, done as FILL-STEPS
says, and only a check failure they do not explain is a reason to stop and tell the person, through `say`. When the register was
written by an older kit some other way (the kit updated mid-run; the check says so and names `--migrate`), the
migration changes no content and this kit cannot run the old form, so: back the register folder up
to a folder outside the workspace (inside it, the start step would take the backup for an earlier register); run
`python "<skill>/reconcile.py" --migrate "<your-folder>"`, which rewrites the register itself in place; run the check
again; and restart the page's listener so the page runs this kit: `python "<skill>/listener.py" stop "<work folder>"`,
then `python "<skill>/wait_on_page.py" "<your-folder>"`, and start the wait again. Tell the person in one line,
through `say`, what was done and where the backup is. Where the upgrade names AI agent rows not classed, that line
also says how many, and that mapping re-reads the code behind each tool, reply and chained action and classes it
(Step 7) before the run is done: a re-walk, announced before it starts and going ahead unless they object, as a
correction to mapping (`corrections.csv` for a finished flow's rows). Only if the check still fails after migrating, stop and tell
them, through `say`. An earlier register, made by another run, is never written into (above).

**The next flow goes into the same register.** When a flow is finished and the first look found more, the run
offers the next flow at the end of its report, in the same session (phase 7), and the re-entry brief offers it to a
chat that picks the register up later; both wait on the home screen (below). Record their pick as the go is recorded
(`go.py --flow`, or `--answers` from the page): `go.py` keeps the finished flow's go, pick and review, keeps a copy
of every row the map holds, and sets phases 1 to 7 to do again for the new flow; phase 0 stands. A flow already
mapped is never picked again with `--flow`, and `go.py` refuses it: a stage of it is taken further with `--depth`,
and only between flows, while no flow is under way. `--depth` naming a stage of a flow finished earlier makes that
flow the one worked now again, keeps the flow just finished as the next flow's start keeps it, and reopens the
phases its new pick needs from phase 4, and the check, the done check and the report; when it is finished the offer
of the next flow comes again. While a flow is under way, `go.py` refuses it, and another flow too: finish the
current flow first, and tell the person so, through `say`. If they name a flow the first look missed, it is a flow of this capability, never new work: record it with `go.py --add-flow "<its name>" --words "<their words, word for word>"`, which adds it to the flows found, then record their pick of it with `--flow`; the page's field for a flow the first look missed does both. Map the new flow as `<mapping>/SKILL.md`
says, by `<mapping>/MAPPING-STEPS.md` "The next flow, in a map that holds a finished one": rows are added, none is
changed, and ids continue after the highest the map holds. Then carry on from phase 1 as for the first flow.
`run_status.py` holds every flow to its own pick, and says NOT DONE on a changed row of a finished flow or an id used
twice; the map inspection reports both.

<!-- shared: waiting-on-the-home-screen -->
**Waiting on the home screen**, at each stop where the run waits on the person's pick: the flow to map first,
how far each stage goes, and the next flow once one is finished. Before you send that stop's message, run `python "<skill>/wait_on_page.py"
"<your-folder>"`. It writes `depth.json`, draws the home screen (`index.html`, by `home.py`) and writes `resume.md`,
and brings up the page itself: it starts the listener when none is serving (it outlives the call) and opens the
person's browser on this run's home screen unless the page is already open there. If it prints `OPEN FAILED`, open
the address in the person's browser yourself, as that line says, before you write to them. Your message is what
`brief.py` printed, exactly as printed (it ends with the page's address), then one line, through `say --after`,
saying the run is waiting on them
there. If it refuses (the
page could not be started), say in one plain sentence, through `say`, that the page could not be opened, and take their answer in
the chat. Then start the wait it printed. The wait is the watch, started with the Monitor tool (timeout_ms
1800000), when the Monitor tool is in your tool list or ToolSearch finds it (`select:Monitor`). Without it, the wait
is `page_ask.py poll` (the command is printed), run as a background task and run again each time it exits, with
answers or with TIMEOUT after 30 minutes. When a poll exits, handle every `ANSWERS` line in its output (as below)
before running it again, because a file announced once is never announced again; each run is a new task, so the task
id to keep is the poll running now's. Keep a wait running from the first stop to the run's end, as the person can send
topics at any time. Check for Monitor each time you start a wait, and never run two at once. One listener serves the whole run, so the page stays in its one tab: at a
later stop it says the listener is already serving, and the open page, which checks for changes by itself, shows the
new choice within about 15 seconds (unless ticks or words on it are not yet sent: it then says so at its top and
waits for them to be sent or cleared); then start the wait only if none is running (a poll has exited once it
announced the last stop's answers). **On a `PROGRESS` line** (a watch event, or a line in a finished poll's output,
printed while a flow is mapped, each time a part of the map is written), send nothing to the chat and end your
turn: the run page, the work page and the home screen show the same line, and the chat carries nothing while
mapping runs unless the person is needed. Between stops write no line of your own about the work's progress either. **On an `ANSWERS <path>` line** (a watch event, or a line in a finished poll's output), read that file, record it with
`python "<skill>/go.py" "<your-folder>" --answers "<path>"`, and say back in a line or two what was recorded, then
"you asked to talk about: ..." with the topics `go.py` printed after that phrase, and talk with the person about
them, through `say`. A tick at any other milestone (talk:) and the words typed in any drop-down are those topics: recorded in
`RUN.md`, never a pick. A post of topics alone records no pick; at the pick, words with no tick record no pick either,
so ask in the chat, through `say`, how far each stage goes. On a refusal, say why in plain words, through `say`, and how to answer
again (a
refused answer whose words agree to a search is that yes: phase 0, "A yes to a search"); still talk
about any topics in the file. Every record draws the home screen again, and the open page shows it within about 15 seconds; it never reloads over
ticks or words not yet sent, and says at its top to send or clear them first. Opening or closing a drop-down
changes nothing. If the
person says "read it", read the newest file that `go.py` has not recorded already in `<your-folder>/answers/`, or else in the `answers/` of the folder above it when that is the work folder, and record it the same way; if there is none,
ask the question in the chat, through `say`. An answer typed in the chat is recorded with `--flow` or `--depth`, as below. When the
wait ends (the watch expires, or a poll exits), start it again the same way. After a restart, or in a new chat that
picks the run up at a stop, run `wait_on_page.py` again first: it brings the page back if its listener has gone, and opens it; in a new chat whose start step sent its MESSAGE, that already gave the person the address, so give no second one; after any other restart, give the address with what `python "<skill>/brief.py" page "<your-folder>"` prints. When you start the wait, keep its task
id (for a poll, the newest run's). A stop is answered only when `go.py` records a pick; a post of topics alone, words with no tick
at the pick, and a refusal are not answers, so the run still waits there. Keep the wait running between stops, and
through the offer of the next flow; once the run's report is sent at its end and no flow is left to offer, or the
person says stop at that offer, stop the wait by its task id, with the tool that stops a background task, and
the listener with the stop command it printed.
<!-- /shared: waiting-on-the-home-screen -->

0. to 3. **Mapping, by the mapping skill.** `<mapping>` is the mapping skill's folder, `bfo-mapping`, installed beside
   this skill folder. Load `<mapping>/SKILL.md` and follow its section "The run" from phase 0 to the map stop, in
   this run's register folder, with `<mapping>/MAPPING-STEPS.md` as the steps; skip its launch, since this kit's
   launch has been sent and its start step run. Its phases 0 to 3 are this run's phases 0 to 3. Record the go with
   this skill's own `go.py` (`python "<skill>/go.py"`, as "When the person answers the brief" says), never the mapping
   skill's: the go of a stage kit run maps fast and says how far every stage goes. Run control (`next.py --by-kit`)
   then records the pick from the go at its `pick` step and goes on; it stops there (a `stop` named `pick`) only when
   the go said `--how-far ask`: come back here for it, record it, then call run control again and go on with mapping
   to the map stop, and from there to phase 4.
   **A fast map goes on to phases 4 to 7 like a full one** for the stages taken past mapped only: its map stop
   sends you here for the measures, drafted from the fast map's rows. **Before the measures review, the rows the
   proposals rest on are checked, and only those** (selective checking): run `python "<skill>/selective.py" select
   "<your-folder>"` once the measures are drafted (and again after the failure modes, phase 5b), then
   `python "<skill>/selective.py" launch "<your-folder>"`, which packs every unit's checkers (one `bfo-row-judge` per
   row, one round) into launchers that fill the session: launch every launcher it prints at once, and run it again on
   each launcher's reply, which prints the checkers of a launcher that died again; `brief.py measures` refuses until every selected row has its
   checker's verdict (`selective.py review`), and the review and the alerts review say how many measures rest on rows
   checked, flagged or not checked, naming each flagged one. A map row no proposal rests on is never checked in this
   run. With every stage left mapped only, run control ends the flow itself and its map stop is the flow's report:
   run the done check, offer the next flow as in phase 7, record `go.py --report-sent <flow id>`, and wait.
   **The pick of how far each stage goes, before any service is read in depth.** In this release, the go
   already answered it (every stage to measures, unless they changed it): run control records it at the `pick` step
   and goes on, with no stop and nothing for you to send, unless the go said `--how-far ask`. What follows is the
   stop when they asked to pick stage by stage. The stages, their process steps and
   what is at stake in each (Business Impact) are written by then, from the lead's own reading; measuring is chosen per
   stage, and the readers then read only the services of the stages taken past mapped only, along each stage's path.
   In a fast map the same pick also decides which stages get a step-level map: their services are the code the one
   mapping agent reads, which sets how long the map takes; the choices are the same four. A stage left
   mapped only keeps its process steps and which services carry each, and its services' insides are marked not read.
   No checked map exists at this stop: the page shows the stages and their steps, and the run status page's "Map so
   far" links a partial map (`map-so-far.html`) of what is written so far. (A register from before this release,
   whose run control has no such stop, is picked at the map stop as before: draw the map first, `capability_views.py
   --check`, then `one_canvas.py`, Step 12.)
   **When the person's request already said how far each stage goes** (for example "take each flow to mapped only",
   or "measure the payment stage"), do not stop to ask it again. Record it from the request:
   `python "<skill>/brief.py" depth "<your-folder>" <flow id> --from-request`, which reads the request the run
   record keeps (the start step recorded it, word for word), with `--depth "<id>=measure|alerting|runbooks,..."` when it takes any stage past mapped only
   (a stage not named stays mapped only). A request that asks only for every flow, or for the map, without saying
   how far stages go, has not said it: stop and ask, as below. It records the pick with the request's words, marks it as taken from the
   request, and prints a status line and one line saying so, which ends by telling them they can take a stage
   further. Send what it printed, do not wait, and carry on in the same turn: at the `pick` stop, with mapping (call
   run control again); at the map stop of a register from before this release, with phases 6 and 7 and then the
   offer of the next flow. If they later say to take a stage further, record it with `go.py --depth` as below. It reads the request the start step kept, word for word, in the run record; when the record keeps none (a register from before this release), it refuses, and you ask instead.
   Otherwise the message is
   rendered: `python "<skill>/brief.py" depth "<your-folder>" <flow id> --recommend "<which stages to measure, and
   which of those to take on to alerts and runbooks, and why>"`. It refuses a flow none of whose steps has a Business
   Impact recorded, as in a register an earlier release made: fill it first (FILL-STEPS Step 10, from each step's own
   citation) and run it again. It opens with the question and your recommendation, what a yes does and the choices;
   then the map's inspection as a count, naming only a rule that fails (`check_map.py`: rules that hold whatever the
   map says; it reports and never blocks, and ends with one line when any file of the code could not be read); then
   each stage with its number of process steps and what is at stake if it fails, under the question whether the
   stages match how the business sees the work. The steps themselves are on the page. It marks
   the stop, and your recommendation is the only text you write: one clause that reads after "I recommend:", for
   example "leave all three stages mapped only for now, as you asked". Record the same recommendation per stage with
   `python "<skill>/depth.py" "<your-folder>" --recommend "<id>=none|measure|alerting|runbooks: <one-line reason>;
   ..."`, which writes `depth.json` with the open choice, then `python "<skill>/home.py" "<your-folder>"`, which
   draws the home screen, `index.html`, from it. Send what `brief.py` printed, exactly as printed, wait on the
   home screen (below), and end your turn. Record their answer with `python "<skill>/go.py" "<your-folder>" --depth
   "<id>=measure|alerting|runbooks,..." --words "<their answer, word for word>"` (`--test` for a test standing in for
   them); a stage not named stays mapped only, and an empty answer makes the run a map only. At the `pick` stop, then
   call run control again (`next.py --by-kit`): it reads, merges and judges the services of the stages taken further,
   and stops at the map stop; from there go on to phase 4. They may later take a
   stage further with the same command, which reopens the phases the new pick needs and phases 6 and 7, so the
   pages are drawn, checked and reported again; first call run control, which reads the newly taken stage's services
   that were not read before, merges and judges them, and stops at the map stop; taking a stage less far than already picked is not supported yet, and
   `go.py` refuses it, so tell them so, through `say`, and keep their earlier pick. It sets the phases their
   pick leaves out to *not picked*, which counts as passed. Nothing is measured before their pick: `flow_outputs.py`
   refuses. A map-only run is done once the map is drawn: the done check owes each stage's page and the map, and no
   measure. This pick decides which stages get alerts and runbooks; in an earlier run whose go named stages, those
   stages stand until the person picks.
4. **Measures, by the measures skill**, for the stages the person took past mapped only. `<measures>` is the measures
   skill's folder, `bfo-measures`, installed beside this skill folder. Load `<measures>/SKILL.md` and follow its
   step 3 of "The run", "Propose the measures", in this run's register folder, with `<measures>/MEASURES-STEPS.md` as
   the steps, as its section "Run alone, or by the stage kit" says under "Run by the stage kit": skip its first message and its steps 1, 2, 4 and 5, since
   this kit's launch has been sent, its start step run, the register's hold taken and the person's pick recorded.
   Run every command it gives from this skill folder (where it writes `<skill>`, put this skill folder's path): the
   kit carries the same scripts, and run from here they keep this run's status line and stops. When its step 3 is
   done, come back here for the review below.
   For a further flow, this phase and phases 5a and 5b add rows for that flow's stages and change none of a
   finished flow's: its measures, alerts, failure modes and runbooks stay as they are, a part a finished flow already
   measures keeps those measures, and each new id continues after the highest the map holds.
   In: the register so far, and any open row of `corrections.csv` naming `measures`, `expectations` or
   `measure-gaps`, which a later step filed and this phase reads first and sets `taken up` or `turned down`.
   Out: `expectations.csv`, `measures.csv`, `measure-gaps.csv`, any `product-names.csv` rows, the `how-made.csv` rows
   of proposing the measures (step `9`), and
   for each measured stage `STRUCTURE.md` and `MEASURES.md` in `stage-<id>/`, written by `flow_outputs.py --out <dir>
   --measures`. The measures' stage, step and part levels run only for the stages picked past mapped only (to
   measure, alerts or runbooks); the flow's own measures are
   owed as soon as any stage is measured, and a part shared by several stages is measured if any of its stages is.
   The measure receipt owes exactly that, and nothing for the stages left mapped only.
   Then **stop for the person's review of the measures**, one per flow, before any alert is chosen: measures and
   alerts answer different questions, and a stage taken only to measure has no other review. The message is
   rendered from the register: `python "<skill>/brief.py" measures "<your-folder>" <flow id> <stage id>...
   --recommend "<your recommendation and its reason>"`, every measured stage named. It gives the status line, then per
   stage what each party counts on, a short list of its measures (what each shows, whether the system produces it
   today, whether anything collects it), what a measure produced today gets wrong, and each part with no measure and
   why; the measures several stages share and the flow's own; the coverage list and the measures inspection in its
   two halves as counts with anything that fails (`check_measures.py`: it reports and never blocks); your
   recommendation; and their options: keep, drop, change or add a measure, or go on. The detail one level down
   (where each measure is produced, and the coverage list item by item) is written beside it as
   `measures-review-detail.md`; send it, whole or for one stage, when the person asks. Your recommendation is the
   only text you write; the script refuses the message while it, or register text it shows, carries an id, a file
   name or a kit term: fix the recommendation or the row the text comes from. Run `wait_on_page.py` (below) so the page stays up and takes topics, send what `brief.py` printed,
   exactly as printed, and end your turn. Record their answer, typed in the chat, with `python "<skill>/go.py"
   "<your-folder>" --measures-reviewed --decision go|changes --words "<their answer, word for word>"` (`--test` for a
   test standing in for them). `go` keeps a snapshot of this flow's own measures, expectations and coverage reasons;
   it is refused when they changed after the message was rendered, so render it again. The measures pages are written
   whether or not a stage's own check passes: when it fails, each page opens with its open items in plain words, the
   message names them, and a go is never refused for them; it is recorded with exactly the items the message showed.
   After the go, putting them right is your work, told, not reviewed again: fix each (a measure, its reason, or the row the check names), record the fix with `python "<skill>/go.py" "<your-folder>" --open-fixed --words "<each item, and how>"` (one plain line per item; it is recorded with every go of this flow, so an item the measures check and the alerts check both find is fixed once, for both; each go then covers the rows as they are, and the next message opens with that line), then run the stage again: the go carries over. Any other change after the go reopens the review, as before. The person is never held by open items: if they say to go on with them still open ("next flow"), record their word with `python "<skill>/go.py" "<your-folder>" --open-left --words "<their answer, word for word>"`; carry on with the work the items do not hold back (at this review, the alerts and their review for the stages taken further; the runbooks of every stage whose alerts check passes), then finish the flow with phases 6 and 7 (the done check names the items as left open at their word and does not hold the flow for them), then offer the next flow. The items stay this flow's, listed on the status line, the page, the resume and the report until put right. `changes` sends the run back
   to the measures skill's step 3, as above, then to this review. Running `flow_outputs.py --measures` again, or a new pick of how far a stage goes, opens the review
   again, except after a fix of open items recorded with `--open-fixed`, which keeps the go. Until their go, `flow_outputs.py --alerts` refuses, and so does any write of an alert page for this flow;
   the done check owes the go for every measured stage and names any of this flow's measures, expectations or
   coverage reasons changed after it.
5. **Alerts for the stages taken to alerting, then runbooks for those taken to runbooks** (Step 11), in two parts
   with the person's review between them.
   Deciding what to alert on and working out the ways the work can fail are different concerns: the alerts are
   chosen from the health measures alone, and the failure modes are what a responder tests once an alert has fired.
   In: the register and the person's pick: 5a for each stage taken to alerting or runbooks, 5b for each taken to
   runbooks. Run 5a for every such stage, then one review for all of them, then 5b for every stage taken to runbooks.
   **5a. Alerting** (Step 11, "Alerting"), only after their go on the measures. Out: the alert choices in `alerts.csv`, the only table of the register it
   writes (each alert's basis, the expectation it guards and, for a count of cases, the moves it counts), and `stage-<id>/` holding `STRUCTURE.md`,
   `MEASURES.md`, `ALERT.md` and `ALERT.html`, written by `flow_outputs.py --out <dir> --alerts`. It writes the alert
   pages whether or not the alerting check passes: when it fails, each page opens with the check's open items in
   plain words, because a draft with open items is still a draft; they show the runbook as still to come. Then **stop for the person's
   review of the alerts**. The message is rendered from the register: `python "<skill>/brief.py" alerts
   "<your-folder>" <flow id> <stage id>... --recommend "<your recommendation and its reason>"`, every stage taken to alerting or runbooks
   named. It gives the status line, then per stage each proposed alert (what it watches, the expectation it guards,
   its kind of health signal, whether it exists today, why it is proposed), the measures considered and not proposed,
   your recommendation, and their options: keep, drop, change or add an alert, or go on to the runbooks. Your
   recommendation is the only text you write, and the script refuses the message while it carries an id, a file name
   or a kit term. A warning that stands goes into the recommendation, with its reason, so it is checked too. Send
   what it prints, exactly as printed, and nothing else, and end your turn. Record their answer with `python "<skill>/go.py" "<your-folder>" --alerts-reviewed --decision
   go|changes --words "<their answer, word for word>"` (`--test` for a test standing in for them): `go` when they
   say go on with the draft, `changes` when they ask for any change. A go is never refused for open items: the
   message names them, and the go is recorded with exactly the items it showed. The runbooks are written only from
   alerts whose own check passes: where it fails, 5b refuses and names the open items, and you tell the person, through `say`, with both ways on. Putting them right is your work, told, not reviewed again: an alert's open item is a part, step or stage its basis rests on that has neither a measure nor a reason for having none, or a row the check names in the expectation the alert guards or the moves it counts; fix each, record the fix with `python "<skill>/go.py" "<your-folder>" --open-fixed --words "<each item, and how>"` as in phase 4 (recorded with both gos of this flow), then run 5a again with `--alerts`: the go carries over. A fix that changes which alerts are proposed, or what one guards or counts, is not a fix of open items but a change, and comes back to this review. If the person says to go on with the items still open ("next flow"), record their word with `--open-left`, as in phase 4: the runbooks that wait on them are passed over; write the runbooks of every stage whose alerts check passes (5b is done once each runbook still owed is written or waits on the items), then finish the flow with phases 6 and 7. Only `go` closes the review and keeps the
   alert set they reviewed, which is the set the message showed them: a `go` is refused when the alerts changed after
   the message was rendered, so render it again and show them what changed. A change they ask for goes back into `alerts.csv`; 5a runs again, which opens the
   review again, and they review again. An alert they ask for on something no proposed measure shows rests
   on a measure the measures skill must propose first: record their answer as `changes`, file a row in `corrections.csv` (table
   `measures`, row and column blank, proposed: what to measure, at which part, and why; why: their request; status
   `open`), and run `python "<skill>/go.py" "<your-folder>" --back-to-measures <id>` (FILL-STEPS Step 11,
   "Alerting"). The measures are reviewed again, then 5a and this review.
   **5b. Runbooks** (Step 11, "Runbooks"), only after their go on the alerts. Out: `failure-modes.csv`,
   `remedies.csv`, `corrections.csv` for anything it finds missing or wrong in the map (it never edits the map's
   tables: only mapping does), and `RUNBOOK.md` and `RUNBOOK.html` in `stage-<id>/`, written by `flow_outputs.py --out <dir>
   --runbooks`, which also writes the alert pages again with their runbook links. It refuses while a stage that has
   alerts has no `ALERT.md`, while their review is not recorded, and when the alerts have changed since they reviewed
   them; and it writes no runbook from alerts whose own check fails: it refuses and names their open items, which
   are the draft's open items, told to the person at once with both ways on (put right and told, or left open at
   their word), as in 5a. A stage whose runbooks wait on open items left open at their word owes no runbook at the
   done check, which names the items instead. 5b never writes `measures.csv`: a measure a test needs that no row holds (a companion measure, never a
   new alert) is a row in `corrections.csv` (table `measures`, row and column blank, proposed: what to measure, at
   which part, and why; status `open`),
   and `python "<skill>/go.py" "<your-folder>" --back-to-measures <id>` takes the run back to phase 4: the measures skill takes
   it up, the person reviews the measures again, and after their go the run comes back to 5b, with a second review
   of the alerts only if an alert changed. `--runbooks` is refused meanwhile, and after any change to the measures
   since their go. Changing an alert's basis, the expectation it guards or its counted moves, all in `alerts.csv`,
   takes the run back to 5a and their review, except a fix of open items recorded with `--open-fixed`, which is told
   and keeps the go.
   A stage no proposed alert reaches (on the stage, its process steps, the parts they use or the flow) gets no
   `ALERT.md` or `ALERT.html`, and its runbook says so; `flow_outputs.py --check` notes it, and does not fail, but a
   stage taken to alerting or runbooks still owes its alert at the done check. Regenerate every other stage their pick takes
   past mapping with plain `--out`, each with its own check, and leave the stages they left mapped only; plain
   `--out` writes what each stage's depth in their pick owes and no more, asks for the alerts' review only on a stage
   taken to runbooks, and refuses an alert changed since their review, which goes back through `--alerts`.
6. **Check and draw** (Step 12).
   In: the register. Out: the three checks of Step 12 run, every failure fixed in the step that produced it, except
   a stage's own check failing on the draft's open items, which are told as open items and either put right by the
   run (`--open-fixed`) or left open at the person's word (`--open-left`), never a reason to hold the person (a
   stage's own check, `flow_outputs.py <register> <flow> <stage> --check`, judges only the work the run has reached:
   the measures before the alerts are done, the alerts before the runbooks; run it bare in phase 6, and with
   `--measures` or `--alerts` to judge one step's work alone);
   `views.html` and `how-this-map-was-made.html` in the register folder, written by `one_canvas.py`. The done check
   opens every drawing page (the map, and each flow, stage, step and part page) and says NOT DONE for one whose
   drawing shows none of what it exists to show (a step's messages, a stage's work, a flow's stages, a part's
   operations or the steps it serves); a frame, lane or key alone is blank. On the map page each figure is judged
   on its own, and the map by its stage boxes and the lines between them. Every page the map's build writes is
   owed, so one it did not write is MISSING. Find why it came out empty and draw it again. A flow found but not mapped owes no drawing.
7. **Reconcile, done check and report.**
   **Whether the run is finished is the done check's to say, never yours:** the report opens with what `python
   "<skill>/brief.py" end "<your-folder>"` prints, which says finished only when the done check said DONE on the map
   as it is; `say` refuses a message that calls the run finished while it has not.
   **When flows remain, the report ends on the offer of the next flow, in the same message.** Once this flow's
   outputs are done and the first look found flows not yet mapped, render the offer ("Then the next flow", below)
   and send it at the end of the report: a report that lists the other flows under What remains and asks nothing is
   not finished, and `go.py --report-sent` refuses to record it until the offer has been rendered.
   **First, reconcile each earlier register** that `RUN.md` → *Earlier registers* names (skip this when it says
   none, and, for a further flow, skip each one *Reconciled* already lists): `python "<skill>/reconcile.py" "<earlier
   register>" "<your-folder>"`. An earlier register is another folder; this register's own finished flows are never
   reconciled: they are kept as they were, and the done check holds them so. The script matches rows by what they
   say, classes each earlier row by its citation, checks each code citation against the files the new walk read, and
   writes `reconciliation-<name>.md` in your folder. It never writes to the earlier register. **In this release the
   reconciliation only reports: add nothing from it to the new register.** The new register is the fresh walk alone.
   Copy the report's counts and names, list by list (matches, *unchecked: not added*, not supported, not assessed,
   disagreements, carried from a person, re-open in the document, dropped), into `RUN.md` → *Earlier registers* →
   *Reconciled*, and say in the report to the person that they are for a person to read, not added. Then work
   through *Claims beside their cited lines* one row at a time: read the claim beside the lines it cites and write
   that row's verdict (supported, not supported, or not assessed) and the reason, as the report asks. The script
   only checks that a citation resolves; whether the line says what the row claims is this step's.
   Then the done check. In: the register folder. Run `python "<skill>/run_status.py" "<your-folder>"`. It lists every output the run
   owes and ends DONE or NOT DONE. **The run is done only when it says DONE**; never say so on your own reading.
   Open items keep it NOT DONE, always named, by flow: a draft with open items is never called done. When every one
   is left open at the person's word, it says so, and the flow's outputs count as done apart from them: the report
   names them under what remains, and the next flow is offered. Open items not yet left open are put right by you
   (told) or brought to the person with both ways on; never hold them at NOT DONE for open items alone.
   On a register mapped in reading units, as every run from the go on is, every finding that cites code was judged
   in mapping (the mapping skill's phases 1 to 3), and the done check holds that judging, the merge and every call
   between units re-read: no sample is drawn, there is no re-read to wait on, and a flow's report is owed once its
   outputs are done. What follows on a re-read applies only to a register mapped before reading units.
   It keeps its verdict with the map it judged, and says the two states apart: "this flow's outputs: done; its
   re-read: pending" (or passed), each flow's outputs, re-read and report, and what remains. A flow's report is sent when its own re-read passes, and recorded with `go.py --report-sent <flow id>`; while an earlier flow's re-read is still pending, a later flow's report names it under What remains (`run_status.py` says which); phase 7, the run's close, is done when every flow's report is sent. The
   kit's scripts count phase 7 done only then: a phase 7 set done by hand before still counts as under way. The next
   flow opens once this flow's outputs are done, its re-read apart. After a further flow's rows land, it names each earlier flow's page they made out of date (STALE, with
   the command that draws it again): draw each again, so no page on disk says what the map no longer does.
   DONE also needs every field a view requires answered or gapped (FILL-STEPS Step 12). If it says NOT DONE for
   anything but open items, go back to the phase that owes the missing file or writes the empty field, or mark that
   phase blocked with the reason.
   Then write how far each flow has gone: `python "<skill>/depth.py" "<your-folder>"` writes `depth.json` in the
   folder (each milestone a draft, not started, or reviewed where the person gave a go; the pages drawn for each).
   Then draw the home screen from it: `python "<skill>/home.py" "<your-folder>"` writes `index.html` beside the map,
   one row per flow with each milestone's status and links to the kit's pages for it. Every page drawn while
   `index.html` is in the folder links back to it.
   Out: `RUN.md` with every phase done, blocked, or *not picked* by the person, and the report to the person: the register folder, the flow and
   stage, the check results, the stages that still have no Step 11, each earlier register and what its reconciliation found (added,
   carried forward, not supported, not assessed, disagreements, each named), anything you could not do, and what the done
   check found, in plain words: done or not done; what was checked of the map, exactly as `python
   "<skill>/brief.py" checked "<your-folder>"` prints it, sent as it is (never "checked and done", nor a headline
   that claims more than it says: until every finding is checked one by one, a sample was); and for each thing it owes that is not done, what is missing and how
   much of it, never its output copied in, its script names, row ids or the commands it suggests; your own prose in the
   report goes through `say`, and what the report must
name as it is (the register folder, each earlier register's folder, the guides it points at) is sent beside it, unchecked. End the report with **What would make this map fuller**: the deployables the map
   stops at (every part under *still missing*, and every external dependency with no source of its own), then the
   `proposed:` rows counted by the kind of source that would settle them, read off the table in FILL-STEPS "Before
   you start".
   **Then the next flow, when the first look found flows not yet mapped.** Once the done check says this flow's
   outputs are done, render the offer, whether or not its re-read has passed (phase 7 stays *doing* until every flow's report is
   sent; this flow's report waits for its own re-read): `python "<skill>/brief.py" next "<your-folder>" --flow "<the flow you recommend next>" --recommend "<why
   that one>" --after`. It lists the flows still to add and offers your recommendation as what is next (their "carry on" picks it), and marks your
   recommendation on the page; `--after` leaves out its status line, for when it follows the report, which opened
   with one, in the same message. On a register mapped in reading units there is no re-read, so the report goes with
   the offer and `--after` is given. Only on a register mapped before them, while its re-read is pending, there is no
   report yet: leave out `--after`, so the offer opens with its own status line. Wait on the home screen (above), send it as printed, and end your turn, with the wait and the
   listener still up. On their pick, record it with `go.py --flow` (or `--answers`) and carry on with the next flow
   from phase 1. **When the person's request already asked for every flow** (for example "map every business flow", or "the whole capability's map first"), do not stop to ask which flow comes next: add `--from-request` to the same command, which reads the request the run record keeps. It records your recommended flow as their pick, with the request's words, and prints one line saying which flow comes next and why, what is still to add, and that they can say stop or name another. Send it as printed, do not wait, and carry on with that flow from phase 1 in the same turn; keep the wait on the home screen running, so a stop or another pick reaches you. It reads the request the start step kept, word for word, in the run record; when the record keeps none (a register from before this release), it refuses, and you ask instead.
   If they name a flow the first look missed, it is a flow of this capability, never new work: record it with `go.py --add-flow "<its name>" --words "<their words, word for word>"`, which adds it to the flows found, then record their pick of it with `--flow`; the page's field for a flow the first look missed does both. When no flow is left, or they say stop, stop the wait and the listener. A
   stop is not recorded: the register stays open with those flows still to add, and a chat that picks it up later
   offers them again. When a chat picks the register up at this stop and the re-entry brief asks for the next flow
   with no recommendation (no offer was rendered), render the offer as above with `--after` and send it in the same
   message, after the re-entry brief.

## Rules for the whole run

<!-- shared: read-mapping-steps-md-then-register-temp -->
- Read `FILL-STEPS.md`, then `register-template/REGISTER.md` and the reference files `FILL-STEPS.md` cites in
  `reference/`, before Phase 1, and `<measures>/MEASURES-STEPS.md` before phase 4. Look at `example-eshop/` only to see what a finished register and its outputs look
  like. It is a different application and never a source of facts.
- Step 11 covers the stages the person picked; a flow is covered when every stage has had one, and the capability
  when every flow is.
- **Follow the code past the workspace.** When a move calls a deployable whose code is not here, identify it from
  what the call shows (an address, a client package, a queue or topic name, an image). If the person has already
  agreed to a search that covers it, the place and the kind of code they agreed to (`RUN.md` *Sources* records what
  they agreed to search), get it with your own tools if you can reach it: it is a pass-1 source like the
  others. Otherwise ask them, through `say`, as a question that needs their judgement, with where you propose to look, and fetch it
  only on their yes. Fetch it only with access the person already has, and read-only: never request access, enter credentials, or change anything at the source. Record every fetched source in `RUN.md` *Sources* with what referenced it and why. If the person's request says to use only the sources they name, do not fetch: list it under *still missing* instead. With its code it is a component, whoever owns
  it, and you read the operations this flow calls and what those call (FILL-STEPS Step 5); how far into an outside
  service to go is Step 6's. If you cannot reach it, it stays a part cited by how you identified it, an external
  dependency, and goes under *still missing* in `RUN.md`.
- **Read the path of every service of a stage taken further.** Steps 1 to 4, Business Impact and the capability cover
  the whole flow, from what the lead reads for its own rows. The services a stage the person takes past mapped only
  reaches (those that carry or are needed by its moves, every service those call, and so on; every service the go
  took in when a part of the stage matches no single surveyed service) are read by the readers along the stage's path:
  from starting points derived by script, every function the case passes through and what those call, the stores and
  data files they open, and the service's monitoring hooks; every other file of those services is listed `not read`,
  off this stage's path, never counted as read. Every row that cites code is judged. One setting, run-settings.json
  `reading` `full`, reads every line of those services instead. A stage left mapped only shows its process steps and which services carry
  each; what is inside the services no stage taken further reaches is gapped "not read in this run" until a stage of theirs is taken further. The measures (the measures
  skill) cover only the stages
  the person picked to measure, with the flow's own measures and the parts those stages use. Step 11 covers only the
  stages picked for alerts and runbooks. A run reads less still only when the person asks for it (`USE.md`). `KNOWN-GAPS.md` "At scale" says what is
  still open at size.
- **Open code with the Read tool, and write each row from what you read.** A row is written from code read, never
  from a script that searches the code and emits rows; a script may find where to look. The done check takes what
  was read from Claude Code's own record of the session, not from anything the run writes: every location a row
  cites must have been opened with Read, its lines inside the part read, or be a fact the code reader produced. A
  file shown by a shell command does not count. Every row of mapping that cites code is also checked by readers
  that wrote none of it (the mapping skill's phases 1 to 3), so no sample is drawn for mapping's rows. A row of a
  finished flow found wrong is never edited by hand: it is filed in `corrections.csv` and applied with `go.py
  --apply-correction`, which records it. Your own
  tables (the flow-level rows) stay yours, as the steps say: a row of them the person states, you write into its
  table, file it in `corrections.csv` and record it with `--apply-correction <id> --added --words "<their words,
  verbatim>"`. A row of a reading unit (`units/`) is
  written only by that unit's reader or fixer, launched on the pointer line of a prompt `readers.py` or `judges.py`
  wrote (one launched on a prompt you composed fails its unit), or is changed as the person states it: you never
  write one yourself, by shell, Write or Edit. On a fast map, too, you never write unit rows by script, Write or
  Edit: the one change yours to make is the row run control names (the fast check, or the correction the person
  chose), with `fast_map.py fix`. Run control records each unit as it collects it from its mapping agent; a unit
  changed since by anything but a kit command is set aside, and its mapping agent writes it again. You never touch
  that record, `fast/unit-hashes.json`: only the kit's scripts write it. On a fast map, a value the person states
  for a row run control names (their reply to a held run's choices) goes in the same way, with `fast_map.py fix`:
  run control's task carries their words. In a full mapping, a unit row the person states is filed in
  `corrections.csv` (its
  `unit`, `table`, and the new `row_id` as `row`) and added with `go.py --apply-correction <id> --added --words
  "<their words, verbatim>" --value "<the row, one CSV line in the table's columns>"`; a cell or a removal they ask
  for takes `--words` the same way. go.py writes the row and records their words, and refuses the change without
  words or with words they did not type into a session after the go; the row is still judged and read-checked. A unit row you
  find missing or wrong yourself goes to that unit's fixer, as a reason only a unit's row can clear does at the map
  stop (the mapping skill's phase 3: `readers.py prompt ... <unit> --mode
  stop --reason "<what is missing or wrong>"`). A register mapped before reading units keeps its sampled re-read (FILL-STEPS
  "Then the sampled re-read").
- **Talk to the person in names, not ids**, as "Talking to the person" above says: name parts, process steps and
  stages by their names ("the Ordering API", "Accept the order"), never by id, in every message and report.
- Never stop to ask the person a fact you can infer: where the sources do not say something, infer it and label it
  `proposed:` with the reason. What is the person's (intent, scope, judgement and taste: which flow, whether the
  sources are enough, whether to keep going) is brought to them with your proposal, through `say`, when it arises. The plan is the
  first such point.
- Never edit a generated file: fix the register and generate again.
<!-- /shared: read-mapping-steps-md-then-register-temp -->
<!-- shared: never-change-the-kit -->
- **Never change the skill folder's own files**, not even to fix a defect in them. When you find a defect in the
  kit, record it with `python "<skill>/kit_findings.py" "<your-folder>" --code <a code from kit_findings.py --list>
  --file <the kit's file> --line <its line>`, then carry on where the run can, or stop and tell the person, through
  `say`, what is held. `kit-findings.md` is written only by that script. If it refuses, record nothing and tell the person,
  through `say`, that the kit has a problem the run could not record. The report names the file.
<!-- /shared: never-change-the-kit -->

## What the person gets

`USE.md` in the skill folder is written for the person running this. It explains what comes out, how to read it,
and what to check before taking it to anyone. `KNOWN-GAPS.md` lists what the kit is known to get wrong. Point the
person at both when you finish.
