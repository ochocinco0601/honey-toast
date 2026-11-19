---
name: bfo-mapping
description: Map the business flows of an application's capability from its code and the sources the person points at, one flow at a time into one map - each flow's stages and steps, the services and people that carry each step, and what is at stake if a step fails - and stop at the map, with the map's own inspection. Load it before writing anything to the person, because its first message introduces the work. Use when asked to map a business flow or a capability's flows, for operations or otherwise, when the person wants a map only or the whole capability's map first, with measures, alerts and runbooks left for later; for those, use bfo-stage-kit, which also runs this skill for its own mapping. Design time only - it reads code, documents and recorded answers, never a running system.
---

# Business flow mapping: one flow, from the sources to the map

This folder is the mapping skill. Everything below calls it **the skill folder**. Wherever `MAPPING-STEPS.md` writes
`<skill>`, it means this folder, and the folders it names (`register-template/`, `reference/`, `method/`) are
inside this folder too.

**Start here, before you write anything to the person.** Your first action is a tool call, the start step:
`python "<skill>/start.py" "<workspace root>" --request "<their request, word for word>" --gave <code, name or
nothing>` ("The start step", below, says which). **Nothing is read before the person's Start.** On a fresh start, or a
case picked up, it prints a `SAYBACK:` line instead of a message: draft what you understood (the lines it names, each
short, in their words, from their request and the folders' names alone) and run `say_back.py draft` as it says.
That script puts the lines on the run page as a review step, with one Start and one box for a correction, and prints the
chat's one line after `MESSAGE:` and the wait after `WAIT:`. Start that wait, and send the text after `MESSAGE:`,
exactly as printed, as your whole reply this turn, with no text before it, not even a line that you are starting
something; then end your turn. Start no helper and open no code until their Start. A script's output left inside its
tool call never reaches the person. On a case picked up, no page asks it: `MESSAGE:` holds the lines themselves and asks
them to say carry on or correct a line, in the chat, and no `WAIT:` is printed; send it and end your turn.

**Their answer to the say-back** comes from the page (an `ANSWERS` line whose file holds `say_back`) or typed in the
chat. Record it with `python "<skill>/say_back.py" answer "<the folder you drafted in>" --answers "<file>"` or
`--words "<their words, word for word>"`. On `STARTED`, do what it says: on a fresh start, start the first-look
helper ("The first look runs in one helper", below) with their request and the lines they started, and send one line,
through `say`, that the first look is under way; on a case picked up, carry on with what the last line proposed.
On `CORRECTED`, redraft the lines with their correction, run `say_back.py draft` again, send what it prints, and wait
again. When the code is not open in this window, give the lines a `search` too (where you propose to look, from the environment): the page then asks that one question, with Yes and No and no Start, and their answer is recorded the same way. On `SEARCH AGREED`, search there and draft the lines again with what was found, so Start appears; on `SEARCH DECLINED`, search nothing and ask them to point at the code. Start never stands for a yes to a search. `go.py --answers` refuses a say-back answer and names this command.

## The job this serves

Step 1 of the path from a new capability to supported in production: understand who depends on it. From the code
and the documents the person points at, this skill draws one business flow: what one case of it is and how to follow
it, the stages it goes through and the process steps in each, the services, stores, outside parties and people that
carry each step, and each step's Business Impact. **In:** what the person points at (repositories, documents,
diagrams, notes), as much or as little as they have. **Out:** the map, written into the register folder's tables
(`sources`, `about`, `capabilities`, `flows`, `lifecycle`, `stages`, `steps`, `subjects`, `participation`,
`set-aside`, `agent-system`, `step-impact`, `case-attributes`), every fact cited to its source or marked proposed,
drawn as the map's page, with the map's own inspection. The register is the capability's one map and grows flow by
flow: a further flow is added beside the finished ones, and changes none of their rows. It stops there: deciding what to count, alerts and
runbooks are later steps, done by other skills on what this one hands on. **Done:** the next step can work from the
map alone, the map is faithful to its sources (every finding that cites code checked against it by readers who
wrote none of it, and one still in doubt shown as not confirmed), and its inspection says what is missing.

## Run alone, or from the stage kit

**Run alone**, it starts with the launch below, and each flow ends at its map stop (phase 3), where the next flow
the first look found is offered and, on the person's pick, mapped into the same register. **Run by the stage kit**, the kit
has already sent its own launch and run its start step: begin at "The run", phase 0, in the register folder the kit
names, and at the map stop go back to the kit's `SKILL.md` for the pick of how far each stage goes.

## Your first message: the say-back

The first message is the say-back's one line, printed by `say_back.py draft` ("Start here", above); the lines
themselves are on the run page, never in the chat. `--gave` is `code` when the request pointed at the system's code
(its repositories, a link to its code, or "this application" with its code open here); `name` when it named only
the system, with `--system "<the system's name, as the person said it>"`; `nothing` otherwise. With `nothing`, the
start step's MESSAGE asks which system, in one line: send it as printed, end the turn, and when they answer, draft
the say-back from their answer (`say_back.py draft` on the work folder) without running the start step again.
Where and how to search is taken from the environment the run is in (its own instructions, tools and sources),
never from a fixed place, and the run searches only where the person agrees.

When only a name was given, look, without reading any file, at whether the folders open here hold that system's
code (their names alone). If they do not, the code line says so and where you propose to look ("When the system's
code is not here", below), and give the lines that place as their `search`: the page asks them Yes or No to that
search before Start appears, and a correction of that line is where they would rather you looked. Once a helper is started, write nothing more until its reply, except as below when the
person writes.

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
pick: the go, the next flow), start that wait before you end your turn, as at every stop. Send it even when the person's request names other work: the message offers to start new work instead, and their answer decides. On finish-first-look or fresh, the helper below starts on their Start, and writes into the
folder the page is already serving; `start_register.py` refuses a new register until the start step has run for this
run.
From then until the first look's brief, a second start step on
the workspace is refused with "the first look is already running", so start one helper only, once. If the helper
returns blocked and the run starts over, end that mark first with `python "<skill>/start.py" "<workspace root>"
--first-look-ended`.

**The first look runs in one helper, so nothing of the setup reaches the person.** On their Start (`STARTED` from
`say_back.py answer`), start one subagent with the Agent tool (general-purpose). Claude Code
runs it in the background: in an interactive session (terminal, VS Code, desktop app) a session cannot wait for a
subagent while fork mode is on, as it is by default (Claude Code's documentation,
code.claude.com/docs/en/sub-agents: "Which subagents run in the background", "Let Claude wait for a subagent",
"Turn fork mode off"); the ways it names to wait are settings, none of them an argument of the call. So the turn
that starts it sends one line that the first look is under way: run `say` on it, start the helper, then send what
`say` printed, exactly as printed, and the turn ends on it. The helper's reply reaches you later as a
completion notification, in a turn of its own, and that turn sends the brief. Where Claude Code waits for the helper
instead, send that line before its brief, in the same turn. A later turn that starts the helper again (after a
search) does the same. If the person writes while the first-look helper is still running, answer in one line
through `say` that the first look is still under way and its brief follows when it is done, and start nothing: no
second helper, no start step. Give the helper: the person's request word for word, and the say-back's lines as they
started them;
the skill folder's path; the start step's DECISION, FOLDER and EARLIER lines as printed; on fresh, the register
folder you name for it, `bfo-work/<the system's name>/` at the workspace root, which is `<your-folder>` from then on;
and this task: *"Follow
`<skill>/SKILL.md`, section 'The run', from the start step's decision through the stop for the person's word in
phase 0, using `<skill>/MAPPING-STEPS.md` 'Before you start'. Write nothing for the person. The start step has run;
never run it again or decide by your own reading. On finish-first-look, finish the first look in the folder it
names; on fresh, start the register folder you were given with `start_register.py` and do the first look there. Write each of
the sources list, the survey and the code reader's facts as soon as it is complete, so the page shows the progress.
Then run `brief.py capability`, and your final reply is exactly the text that script printed, and nothing
else. If the run is blocked, your
final reply is what `brief.py say` printed for one plain sentence saying why and what
would unblock it, in the person's terms (with no code to read,
or only code that is not the named system's: that the system's code is needed, and that they can point at it or agree to a search for it)."* When it returns
blocked for want of code, see "When the system's code is not here" above. Otherwise, when it returns, your message is its reply, sent as it is, and nothing else: no sentence before it ("Here is the brief", "I'll pass this along"), none after it. Its first line
is already the status line. Then end your turn: the brief ends with what it waits on, the person's picks or one question
whether to carry on. Write nothing between the say-back and that message, except the one line that the first look is
under way.

**When the person answers the brief**, record their picks with `go.py` (phase 0, "Their answer is recorded as data"),
unless they agreed to a search: then search first and brief again, as phase 0 says there. `go.py` prints a status line;
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

**Talking to the person, for the whole run.**
- **Every later message opens with the status line**, copied exactly from `python "<skill>/brief.py" status
  "<your-folder>"` run just before you write it, or as `say` or a script prints it. Never type the line yourself,
  and never send two.
- **Write to the person only at the points this file names:** the say-back's one line (or the start step's
  MESSAGE, where it prints one), the line that the first look is under way, the capability brief or the re-entry brief,
  the map stop (phase 3) and the offer of the next flow there, a question that
  needs their judgement, a plain message that the run
  is blocked and why. Between
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


## The run

A run is four phases, 0 to 3, done in order.
Between the first and the second, the run shows the person its plan and
waits for their go, whatever the run's size. Each phase has an **In → Out**, and the files it names are what prove it done. The
work goes in the **register folder**, `bfo-work/<application>/` at the workspace root (in a multi-root workspace,
the first folder), never in the skill folder;
it is `<your-folder>` in `MAPPING-STEPS.md`. Take `<your-folder>` from the `FOLDER:` line `start.py` printed for the
run picked up (on choose, the one the person picked), or on fresh the folder you named for the first-look helper,
which `start_register.py` prints back on its own `FOLDER:` line; never from a listing of the work folder. `bfo-work/`
also holds `answers/`, where the page saves what the person sends, and a listing can put it first: the home screen is
then drawn in the wrong folder and the person's page shows an error instead of it. A script handed a folder that is
not a register refuses it and names the register folders it found; run the command again with the one it names. Run the kit's scripts from the skill folder, exactly as `MAPPING-STEPS.md`
writes them, with `<skill>` replaced by the skill folder's path.

**The run's first work is the start step, by script, before any text:** `python "<skill>/start.py"
"<workspace root>" --request "<their request, word for word>" --gave <code, name or nothing>` (in a multi-root
workspace, the first folder), run by the session itself before any helper; the say-back it hands to (or its own
MESSAGE, where it prints one), sent exactly as printed, is the run's first message. On a fresh start it keeps the request, and the new register's run record
records it, so a later stop the request already answers reads it from there.
First it brings up the run status page, served from the workspace's `bfo-work/` folder (made if need be), so
the person has the page while the rest runs: before the register exists it shows step 1, Discovery, under way, then
the run's own; it links to the work page and, once drawn, the home. Then it prints a `KIT:` line: the build this copy of the skill is, as its
`KIT-VERSION.txt` names it (the release and date it was built as). A `WARNING` on that line means the copy is
partial, mixed with another version, or made before the kit had a version marker (a file missing, changed, or from another build, or
no marker at all), and the start step stops there with DECISION blocked, before it takes any lock or writes
anything: tell the person in one line, through `say`, that this copy of the skill is incomplete or out of date and
needs installing again from its source, and once it is, run the start step again. When it picks up a register an
older version wrote, it upgrades it in place once it holds the lock (backed up outside the workspace first) and
prints `UPGRADED:`; the re-entry brief carries the line that tells the person (with no brief, send that line through
`say`). Before you send the brief, run the check (`python "<skill>/capability_views.py" "<your-folder>" --check`)
and restart the page's listener, which otherwise keeps running the older version (`python "<skill>/listener.py" stop
"<work folder>"`, then `python "<skill>/wait_on_page.py" "<your-folder>"`); the columns and stage folders `UPGRADED:`
lists as owed are the run's own work, and only a check failure they do not explain is a reason to stop and tell the
person. Once its decision clears, it records when the run started
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
lists each earlier register in `RUN.md` → *Earlier registers* → *Found*, and reconciles each with the new register (the stage kit's
phase 7). If the stage to cover is not named, prefer one an earlier register has `stage-<id>/` work for, so the
re-derivation can be compared.

**Then `RUN.md`, and nothing else starts before it.** Before reading any code or writing any other file, on
DECISION fresh, create the register folder with `python "<skill>/start_register.py" "<your-folder>"`, which copies
`RUN.md` and the empty tables from `register-template/` into it, and write its section *What this run will produce* in your
own words, from this file: the application, the flow and the stages (named by the person, or left to the plan's
decisions), and, phase by phase,
what the phase does and the files it must leave. Then set Phase 0 to *doing*.

**`RUN.md` is kept as you go.** At the end of each phase, set it to *done* with the files that prove it, and the
next to *doing*. A phase that cannot be done is set to *blocked* with the reason (for example "python is not on
the path") and what would unblock it, and the run says so in the chat. No phase is skipped silently, and the run
never stops without saying where it stands. **If `RUN.md` already exists**, because the run is resuming or a new
chat has started, read it first. If it waits on their review of the alerts, the re-entry brief carries the alerts
as last put to them, so they have them in front of them. Your next message to the person is the **re-entry brief** (on a pickup, the start step's MESSAGE carries it after the launch):
the text `python "<skill>/brief.py" reentry "<your-folder>"` prints, sent as it is. It says what the work is, what
the capability is, what has been drafted and found, what was decided and by whom, where it stands, and what is next. Never ask
"shall we pick up where we left off?". When it waits on nothing, it ends by asking whether to carry on with what
is next, recommending yes; on their answer, your reply goes through `say`, and on their yes, continue from the
first phase that is not done.

**Waiting on the home screen**, at each stop where the run waits on the person's pick: the flow to map first, and
the next flow once one is finished. Before you send that stop's message, run `python "<skill>/wait_on_page.py"
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
through the offer of the next flow; once the map stop's message is sent at its end and no flow is left to offer, or
the person says stop at that offer, stop the wait by its task id, with the tool that stops a background task, and
the listener with the stop command it printed.

0. **Frame, gather, survey and plan** (MAPPING-STEPS "Before you start").
   In: whatever the person points at in their request (repositories, pages, diagrams, process descriptions,
   documents, notes), and what is already in the workspace. Out: the register's CSV files, copied from
   `register-template/` by `python "<skill>/start_register.py" "<your-folder>"`, never by hand: it copies only into
   a folder holding no CSV file, keeps the `RUN.md` already there, and refuses to write over an existing table;
   `sources.csv` with one row per source, pass `1`, and in `note` the step that will use it
   (the table in "Before you start"); `about.csv` → `sources_examined` and `what_it_is`; the first rows of
   `how-made.csv`; and `RUN.md` → *Sources*, listing what was gathered and what is still missing.
   **Write each file as soon as it is complete, never all at the end:** `sources.csv` once the sources are listed,
   then the survey, then the code reader's facts, each run as soon as what it reads is in place. The work page reads
   these files, so the person sees the first look move.
   **First, prove the scripts run:** `python "<skill>/run_status.py" "<your-folder>"`. It says NOT DONE at this
   point, and that is expected. If the command itself fails (no python, a version older than 3.9), set Phase 0
   *blocked* with the error and stop there: every later phase ends in a script, so nothing is drafted that cannot be
   generated.
   **Get every source with your own tools**, whatever its form: you already know how to clone a repository and how
   to read a page, a diagram or a PDF. Put each repository you fetch at the workspace root, as its own folder, because
   every citation starts with that folder. **Every repository the run uses is a folder of the open workspace** (a
   multi-root workspace when there are several), never a temporary folder: the environment's code tools reach only the
   open workspace. If you cannot add folders to the workspace yourself, set Phase 0 *blocked*, name the repositories,
   and tell the person, through `say`, to open them as one multi-root workspace and start again; write the same in `RUN.md`. A source you cannot reach (no access, a dead link) is listed under
   *still missing* in `RUN.md` with what you tried, and the run goes on: a missing source changes what the map is
   worth, never whether the run continues.
   **Check the repository set is complete.** The first look resolves references only against the workspace and what
   the person gave; it does not search a code host. (a) For every reference the code makes that no folder in the
   workspace answers (a host or service name, a client package, a queue or topic, an image, a configuration key, a
   URL), and (b) the other way, for the repositories that may call, consume from or deploy this flow's services, write
   an item in `orientation.json`'s `unresolved`: what is open and where the run proposes to look, in plain words like
   the rest of the brief, taking where and how to search from the environment the run is in (its own instructions,
   tools and sources). Write each so the brief's plain-words check passes: name the service and the kind of
   reference ("the address the basket service calls for payments"), never the address, path, file name or id
   itself. The brief lists them under what is still open. At the brief the person can say yes to any of these
   searches. Search only on that yes, with the person's own access and read-only: a yes is a change to the brief
   (below, "If they ask for changes to the brief"), and (c) what the repositories found reference is brought to the
   person the same way. Record each repository found in `sources.csv` with the search that found it, add it to the
   workspace as a further folder, read-only, and write in `RUN.md` *Sources* what the person agreed to search; what
   is found and cannot be had goes under *still missing*, and what the person does not agree to search goes under
   *still missing* too. `RUN.md`'s Phase 0 line answers "Is this the complete set of
   repositories?" with that evidence, and Phase 0 is not done while a reference is neither resolved nor put to the
   person with a proposal. If the person's request says to use only the sources they name, do not
   search: list each unresolved reference under *still missing* instead. The same holds when the run cannot search (no
   access to a code host, or the person has said nothing is to be fetched): list each one, with why it was not searched.
   **This phase lists and places; it does not read everything.** Read each source only far enough to say what it
   is and which step uses it. Code is read in full from Phase 1 on, every service the flow touches, as the rules for
   the whole run below say.
   Keep the documents identifiable as a set: Step 8 hands them, without the walk, to a separate pass.
   **Then survey and plan** (MAPPING-STEPS "Before you start", items 6 and 7): `python "<skill>/survey.py"
   "<your-folder>"` writes `survey.csv`, each service's place, size, entry points and calls, counted by script;
   then the code reader, `python "<skill>/fact-extractor/run.py"`, writes `fact-base.json` in the register folder:
   routes, calls, messages and writes with file and line, found by rule. It is a module: any tool whose output
   `fact-extractor/contract.py` accepts can take its place. Its findings are leads to read, each later cited by a
   row or set aside with the reason; what it misses is found by reading and labelled `proposed:`, a call citing both
   ends.
   **Then the first look, and the capability brief.** Read, shallowly, only what names the business flows: each
   service's entry points and routes (the storefront's pages and its API), its interface definitions, the deployment
   files and the documents. Read no service in depth: that waits for the person's picks. From what you read and the
   survey, write `orientation.json` in the register folder, in the person's words, as MAPPING-STEPS item 7 sets out:
   what the work is for and what this run will produce, in your own words (it is how the person judges that the run
   understood its job); the capability (what it does, for whom); every service the survey lists,
   what it does, and whether you recommend including it; every business flow found so far, each with what one case of it is, its stages and
   one sentence per stage, and where in the code you saw it; what you looked at and what is still open; any earlier
   map found and what it changes for this run; and your recommendation (which flow to start with and why, and which
   flows remain after this run). Say nothing here about which stages get measures, alerts or runbooks: the person
   picks that once the flow is mapped. Then run `python "<skill>/brief.py" capability
   "<your-folder>"`. It refuses an incomplete or jargon-bearing `orientation.json` and says why: fix it and run it
   again. When it passes it writes the full brief to `PLAN.md` and prints the **capability brief** for the chat:
   the question and your recommendation first, then what a yes does and what was found, as lists. When they ask
   for the detail (each flow's stages, each service and why, what is still open), show them `PLAN.md`.
   **When the person's request already asked for every flow** (for example "map every business flow", or "the
   whole capability's map first"), and nothing else waits on their word (no code still to point at, no earlier
   work to choose between), do not stop for the first flow: run it as
   `python "<skill>/brief.py" capability "<your-folder>" --from-request`, which reads the request the run record
   keeps (the start step recorded it, word for word). It records the recommended flow as their go, with the request's words, and prints the brief
   led by the line that says so, ending with what they can stop or change. Send it as printed, start the wait on
   the home screen (below) so a stop or a change reaches you, and go on in the same turn to phase 1. A search
   proposed under what is still open is never run without their yes, and a change they ask for (another flow
   first, other services read) is recorded as phase 0 says for their answer.
   **Otherwise, stop for the person's word.** `brief.py` marks the stop in `RUN.md`; send the printed brief as
   your message, exactly as printed, wait on the home screen (below), and end your turn. Read nothing further until
   they answer.
   **Their answer is recorded as data, by script, never by hand:** `python "<skill>/go.py" "<your-folder>" --flow
   "<flow, as named in the brief>" --words "<their answer, word for word>"`, with `--test` when the answer is a test
   standing in for the person. The go asks only which flow comes first; where they accepted the recommendation, the
   recommendation is their pick. The services read are those the brief marked include, and the checks per finding
   three, as the brief showed them; only when they say otherwise add `--in <service,...> --out <service,...>` (every
   service named once) or `--judges <n>`. Every finding that cites code is checked by that many readers who wrote
   none of it, as the brief said (phases 1 to 3). `go.py` refuses `--stages`: the stages are picked after mapping, with
   `--depth`. It writes `scope.json` (with what remains after this run) and `run-settings.json`, and the go and scope
   lines of `RUN.md`; it refuses a flow or service the brief did not name. Map their words to the brief's names
   yourself where the match is plain (a spelling, a shortened name); ask only when their answer matches nothing in the
   brief. If they ask for changes to the brief instead, change `orientation.json`, run `brief.py capability` again and
   wait again. A yes to a search the brief proposed is such a change, and records no go: search there, add each
   repository found as above, run `survey.py` and the code reader again, update `orientation.json` (its services,
   flows and what is still open), run `brief.py capability` again and wait again. If the same answer also picked a
   flow, make that flow the recommendation, so the next stop asks them only to confirm it. From the home screen the
   yes comes in the words: with a flow ticked, `go.py --answers` records the go at once, so search and survey as
   above, update `orientation.json` with each service found and whether you recommend including it, then record the
   go again with `python "<skill>/go.py" "<your-folder>" --flow "<the flow they ticked>" --words "<their words>"`,
   which replaces it and takes its services from the new survey and those recommendations, and tell them in a short message, through `say`, which services were added, your recommendation for each, and any flow or open question the search
   turned up, so they can change it; with no flow ticked, `go.py` refuses the answer, and its words, where they agree to a
   search, are that yes all the same: search, survey and brief again. A topic sent from the home screen that agrees
   to a search is that yes too. A run's done is not the capability's done: the done check owes what their pick of how far each stage
   goes asks for, and reports every other stage as not yet covered; until that pick it says NOT DONE. With no pick of
   how far each stage goes (an earlier run, whose go named stages), record the ids of exactly the stages they named
   with `python "<skill>/go.py" "<your-folder>" --stage-ids <id>,<id>` once Phase 2 cuts them, and the done check owes
   alerts and runbooks for those stages only. If their answer also says to stop there, stop after recording it.
   Under the service reliability room, the room's own agreement with the person is the go: its chief engineer
   records it with `go.py`. `run_status.py` names any work written before the go.
   **The next flow, once one is finished,** goes into the same register. It is offered at the end of the run that
   finished a flow (run alone: the map stop, below; run by the stage kit: its report), and by the re-entry brief to a
   chat that picks the register up later; their pick is recorded with `go.py --flow` (or `--answers`). `go.py`
   refuses another flow while the flow worked now is under way, and a flow already mapped. If they name a flow the first look missed, it is a flow of this capability, never new work: record it with `go.py --add-flow "<its name>" --words "<their words, word for word>"`, which adds it to the flows found, then record their pick of it with `--flow`; the page's field for a flow the first look missed does both. Phase 0 is not done again. Phases 1 to 3 map the new flow as MAPPING-STEPS "The next flow, in a map that holds a finished one" says:
   rows are added and none is changed, and ids continue after the highest the map holds. The map inspection reports
   an id used twice or a changed row of a finished flow, and the done check says NOT DONE on either.
**Phases 1 to 3: run control decides each next step.** Once the go is recorded, call
`python "<skill>/next.py" "<your-folder>" <flow id>`, with `--by-kit` added on every call when the stage kit runs this
skill (it then never ends the flow: its map stop says to go back to the kit's `SKILL.md` for the pick, and you do), and
do what the one action it prints says, then call it again; a `stop` carries its message already rendered, status line
and all, which you send as it is:
`judgment` is a task for you, with the tables you may write and the checks it must pass (the findings say what the
last check found); `fanout` is one `general-purpose` launcher per pointer line, at most `cap` at once, after which you
end your turn; `wait` means agents are still running and you end your turn; `code` with `ok` false is a step that
failed, said in `said`, to put right or tell the person about through `say`; `stop` is where the run waits on the
person; a `stop` of helpers that stopped without their work (an error from the service that runs the model, each time they were tried) never moves on by itself: when the person says to try again, call it with `--event retry "<their words, word for word>"`. On each launcher's reply, call it with `--event launcher-done "<its file>"`. When the person writes while it
works, call it with `--event chat "<their words, word for word>"`, and when their words stop the work, with
`--event stop "<their words, word for word>"`: it stops what was launched, puts back what half-finished agents wrote,
and marks the map not checked (`--test` before `--event` when a test stands in for them, so the answer is kept
as a test's). Never decide the next step yourself, and never keep `RUN.md`'s phases for these three
phases by hand: the case record keeps them (`case.json`, `decisions.jsonl`, `case-log.jsonl`). What follows says what
each step is; `next.py` says when.

1. **The case and its lifecycle** (Steps 1 and 2).
   In: the sources. Out: `flows.csv` (the case, whose expectation, start and end), `lifecycle.csv`. The flow is the one the person chose at the go, from the plan's
   decision (their own, or the recommendation they accepted); write it into `RUN.md`.
   **Phases 1 to 3 run one path, every time** (MAPPING-STEPS "Reading in units, and every finding checked" gives the
   commands). The lead is the run's own session, the one that talks to the person: it writes the flow-level rows,
   launches every other agent and decides each next step. The first-look helper launches none. The parts are read in
   reading units, one reader per unit of a service the go took in, and every row that cites code is then checked by
   as many readers as the go recorded, each a fresh agent that wrote none of it. Launch one launcher per pointer line
   the script prints, each a `general-purpose` agent and never a fork, given that line alone: for judging, one
   launcher per unit (the `flow` unit, one per lead table). Each launcher holds at most 150 agents and launches them
   itself; keep running at once no more launchers, in all, than the script's count line names. After launching, the
   lead ends its turn; each launcher's reply comes back as a completion notification, and the lead decides the next
   step from the files on disk, never from the replies: the same command, run again at any time, never launches an
   agent twice, so launch every pointer line it prints (MAPPING-STEPS says how, for readers, judges and fixers). After
   a crash or a restart of the lead's own session, and only then, run it with `--again`, which launches afresh the
   agents that died with that session and never one that finished. A new chat picking up a run whose agents the
   files still name running, though no completion notification will ever reach it, is such a restart. If the person writes while agents run, answer in
   one line, through `say`, that the mapping is under way, and launch nothing. The order: the lead's Steps 1 to 4; the readers; the merge; the lead's rows after the merge (the capability, Business
   Impact and the rest), which are judged once written, in the same rounds; then round 1, `collect`, fix, round 2,
   `collect`, with each flagged row fixed by a fixer and never by the lead, and a row still flagged after round 2
   labelled `disputed:`. Only then the done check.
2. **Stages, process steps, parts and agents** (Steps 3 to 7).
   In: the lifecycle. Out: `stages.csv` and `steps.csv`, by the lead; the parts and who takes part in each process
   step from the reading units, merged into `subjects.csv` and `participation.csv`; `set-aside.csv` and
   `agent-system.csv`, by the lead after the merge. Which stages go on to measures, alerts and runbooks is the person's pick once the flow is
   mapped (phase 3), never decided here. An earlier run whose go named stages records their ids with `go.py
   --stage-ids`, adding none and dropping none. Only a run whose `RUN.md` has no *Plan and go* section chooses for
   itself: the stage the person named; else, if the register already has
   `stage-<id>` folders, the next stage with none; else the stage where a case most often waits or can be left
   stranded.
3. **The capability and Business Impact** (Steps 8 and 10).
   In: the walk so far, and the documents read apart from it. Out: `capabilities.csv`, and for every stage
   `step-impact.csv` and `case-attributes.csv`. Then the judging rounds and their fixes, as above, over every row of
   this flow that cites code.
   **Mapping ends here, at the map stop.** Draw the map: `python "<skill>/capability_views.py" "<your-folder>"
   --check`, then `python "<skill>/one_canvas.py" "<your-folder>" "<your-folder>/views.html"`, and run the map's
   inspection, `python "<skill>/check_map.py" "<your-folder>" <flow id>` (rules that hold whatever the map says; it
   reports and never blocks; when any file of the code could not be read, it ends with one line saying how many, and
   that mapping may have missed code in those files, which the person sees as printed). When its first line says
   **Mapping is not finished**, the done check would still fail on what this skill wrote or drew: put right each
   reason it lists on its error output (`python "<skill>/run_status.py" "<your-folder>"` names, under its view
   questions, each element left empty), draw the map again and rerun it, until that sentence is gone. Then run
   mapping's end check, `python "<skill>/run_status.py" "<your-folder>" --mapping`: it asks of the map exactly what
   the done check will ask of a flow left mapped only, and prints MAPPED or NOT MAPPED with each question still
   unanswered (a service's operations, what it depends on, and the like). Answer each in the register, or write its
   gap with the reason, and run it again until it prints MAPPED. A row changed
   or added to put a reason right is judged like every other row before the map is drawn again: a reason in the
   lead's own tables (the case, lifecycle, stages, process steps, Business Impact, case attributes, agents, parts set
   aside, and the lead's rows in `merge/lead-rows/`) is put right by the lead, as in the step that wrote it (this is
   the lead writing its own step, not fixing a flagged row, which stays a fixer's); merge again if a lead row
   changed; then judge it as in MAPPING-STEPS "The order", items 5 to 7: `judges.py emit` for `flow` with `--round`
   set to the latest round `judges.py --check "<your-folder>" flow` names (round 1 for a row never judged), launch,
   `collect`, and a row a judge flags goes to its fixer and the next round like any other. A reason only a reading
   unit's row can clear goes to a fixer of that unit, since the lead never writes into `units/`: `python
   "<skill>/readers.py" prompt "<your-folder>" <unit> --mode stop --reason "<the reason, as printed>"`, naming the
   unit whose code the reason concerns (for a part, the unit of its deployable in `units/units.csv`; for a process
   step no part carries, each unit in the go's scope whose code may carry it), writes one fixer per unit and reason;
   launch it as in MAPPING-STEPS "How agents are launched". It changes or adds that unit's rows from the code, or
   changes nothing when the code does not show it. Then merge again, judge that unit as `flow` is judged above
   (`judges.py emit "<your-folder>" <unit>` with `--round` the latest round `judges.py --check "<your-folder>" <unit>`
   names), launch, `collect`, and draw and inspect the map again. When the inspection still gives the same reason,
   the same `readers.py ... --mode stop` command names that fixer `launched already, finished` and launches none: the
   code does not show it. Until both pass, send no map stop and never report phases 1 to 3 done. The one exception is a
   reason no change clears (a check that cannot run, a drawing fault, a reason the unit's fixer has finished on and
   the code does not show): send the map stop with it named as still open, in its own words, and phase 3 not done, and tell the
   person what it holds up: this flow cannot be ended, so no next flow starts, until it clears. A chat that picks the
   run up at that stop with the same reason still open says so in one line and sends no second map stop. Otherwise set phase 3 to *done* in
   `RUN.md` with those files. That much is done both ways; the
   rest of this phase is the ending of a run alone, and a run by the stage kit takes the last paragraph instead.

   **Run alone only.** When the map stop goes out with a reason of the map's inspection still open, phase 3 stays
   not done and the ending is skipped: no re-read is drawn and no `go.py --mapping-ends` is run, so the flow is not
   ended and no next flow is offered; once the reason clears, draw and inspect the map again and end here. Otherwise
   end the flow with
   `python "<skill>/go.py" "<your-folder>" --mapping-ends <flow id>` (the id the inspection was run on), once the
   last `collect` has run. It binds the
   flow's id, sets the phases after mapping *not picked*, so the flow counts finished, and is the done check of a run
   that ends at the map: it refuses while any row of this flow is not judged by every check the go recorded, the map
   is not the merge of the units, a call between units is not re-read and resolved, an id is used twice or a finished
   flow's row is changed, and names each, so put it right and run it again. Then write to the person through `say`: the flow is mapped, the inspection as
   `check_map.py` printed it (a count, naming only a rule that fails), and where the map's page is. When the first look found flows not yet mapped, offer the
   next one in the same message: `python "<skill>/brief.py" next "<your-folder>" --flow "<the flow you recommend
   next>" --recommend "<why that one>" --after` (`--after`: no second status line), wait on the home screen, send it
   as printed after your `say` text, and end your turn; on their pick (their "carry on" picks the flow you
   recommended), record it with `go.py --flow` (or `--answers`) and map that flow from phase 1. **When the person's request already asked for every flow** (for example "map every business flow", or "the whole capability's map first"), do not stop to ask which flow comes next: add `--from-request` to the same command, which reads the request the run record keeps. It records your recommended flow as their pick, with the request's words, and prints one line saying which flow comes next and why, what is still to add, and that they can say stop or name another. Send it as printed, do not wait, and carry on with that flow from phase 1 in the same turn; keep the wait on the home screen running, so a stop or another pick reaches you. It reads the request the start step kept, word for word, in the run record; when the record keeps none (a register from before this release), it refuses, and you ask instead.
   When no flow is left, or they say stop, end the run. A stop is not
   recorded: the register stays open with those flows still to add, and a chat that picks it up later offers them
   again. When a chat picks the register up at this stop and the re-entry brief asks for the next flow with no
   recommendation, render the offer as above and send it after the re-entry brief, in the same message.

   **Run by the stage kit, go back** to the kit's `SKILL.md` for the pick of how far each stage goes, and do none of
   the run-alone ending: no `go.py --mapping-ends` (it would mark the phases after mapping
   *not picked* and count the flow finished before the kit measures it), no offer of the next flow. The kit's own done
   check holds the judging, and the kit offers the next flow itself. With a reason of the map's inspection still
   open, go back all the same, with phase 3 not done, and name that reason to the person in the kit's next message.

## Rules for the whole run

- Read `MAPPING-STEPS.md`, then `register-template/REGISTER.md` and the reference files `MAPPING-STEPS.md` cites in
  `reference/`, before Phase 1.
- **Follow the code past the workspace.** When a move calls a deployable whose code is not here, identify it from
  what the call shows (an address, a client package, a queue or topic name, an image). If the person has already
  agreed to a search that covers it, the place and the kind of code they agreed to (`RUN.md` *Sources* records what
  they agreed to search), get it with your own tools if you can reach it: it is a pass-1 source like the
  others. Otherwise ask them, through `say`, as a question that needs their judgement, with where you propose to look, and fetch it
  only on their yes. Fetch it only with access the person already has, and read-only: never request access, enter credentials, or change anything at the source. Record every fetched source in `RUN.md` *Sources* with what referenced it and why. If the person's request says to use only the sources they name, do not fetch: list it under *still missing* instead. With its code it is a component, whoever owns
  it, and you read the operations this flow calls and what those call (MAPPING-STEPS Step 5); how far into an outside
  service to go is Step 6's. If you cannot reach it, it stays a part cited by how you identified it, an external
  dependency, and goes under *still missing* in `RUN.md`.
- **Read in full every service the flow touches.** Steps 1 to 8 and Step 10, the mapping and its Business Impact,
  cover the whole flow and read every service it runs through, whatever stage it carries: the readers read each
  unit in full, and the lead reads only what its own rows need. A run is cut shorter only
  when the person asks for it.
- **Open code with the Read tool, and write each row from what you read.** A row is written from code read, never
  from a script that searches the code and emits rows; a script may find where to look. The done check takes what
  was read from Claude Code's own record of the session, not from anything the run writes: every location a row
  cites must have been opened with Read, its lines inside the part read, or be a fact the code reader produced. A
  file shown by a shell command does not count. Every row of this flow that cites code is also checked by readers
  that wrote none of it (phases 1 to 3), so no sample is drawn. A row of a finished flow found wrong is never edited
  by hand: it is filed in `corrections.csv` and applied with `go.py --apply-correction`, which records it. Your own
  tables (the flow-level rows) stay yours, as the steps say: a row of them the person states, you write into its
  table, file it in `corrections.csv` and record it with `--apply-correction <id> --added --words "<their words,
  verbatim>"`. A row of a reading unit (`units/`) is
  written only by that unit's reader or fixer, launched on the pointer line of a prompt `readers.py` or `judges.py`
  wrote (one launched on a prompt you composed fails its unit), or is changed as the person states it: you never
  write one yourself, by shell, Write or Edit. A unit row the person states is filed in `corrections.csv` (its
  `unit`, `table`, and the new `row_id` as `row`) and added with `go.py --apply-correction <id> --added --words
  "<their words, verbatim>" --value "<the row, one CSV line in the table's columns>"`; a cell or a removal they ask
  for takes `--words` the same way. go.py writes the row and records their words, and refuses the change without
  words or with words they did not type into a session after the go; the row is still judged and read-checked. A unit row you
  find missing or wrong yourself goes to that unit's fixer, as a reason only a unit's row can clear does at the map
  stop (phase 3 above: `readers.py prompt ... <unit> --mode stop --reason "<what is missing or wrong>"`).
- **Talk to the person in names, not ids**, as "Talking to the person" above says: name parts, process steps and
  stages by their names ("the Ordering API", "Accept the order"), never by id, in every message and report.
- Never stop to ask the person a fact you can infer: where the sources do not say something, infer it and label it
  `proposed:` with the reason. What is the person's (intent, scope, judgement and taste: which flow, whether the
  sources are enough, whether to keep going) is brought to them with your proposal, through `say`, when it arises. The plan is the
  first such point.
- Never edit a generated file: fix the register and generate again.

