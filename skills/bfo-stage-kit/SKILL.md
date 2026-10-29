---
name: bfo-stage-kit
description: Map the business flows of an application's capability from its code, one flow per run, and for the stages the person picks propose what to measure, what to alert on, and a runbook per alert, then draw the whole flow as one map. Load it before writing anything to the person, because its first message introduces the work. Use when asked to map a business flow or business capability for operations, to work out what to monitor or alert on for a flow, or to write runbooks for a flow's alerts, starting from the code and sources the person points at (repositories, documents, diagrams, process descriptions) and following the flow's calls into any code the run can get. Design time only - it reads code, documents and recorded answers, never a running system. Use this rather than the older capability-views skill, which draws an earlier form of the same map and writes no alerts or runbooks.
---

# Business flow observability: the whole capability, one flow per run

This folder is the kit. Everything below calls it **the skill folder**. Wherever `FILL-STEPS.md` writes
`<skill>`, it means this folder, and the folders it names (`register-template/`, `reference/`, `method/`) are
inside this folder too.

## The job this serves

A person who oversees operations needs each business capability their teams run to be supported in production:
someone can tell whether it is healthy, is told when it is not, and knows what to do. Two levels up, the customers and
the business who depend on it get what they need, and when something breaks the impact on them is found and limited
first. This skill's step in that job is the design-time map of the capability: from the code and the documents, it
finds the business flows the capability carries, and in batches, one flow per run, describes a flow and for the stages
the person picks drafts what to measure, what to alert on and a runbook per alert. The job is the whole capability,
every flow; one run is one batch, and each run says what remains. It receives what the person points at
(repositories, documents, diagrams, notes), directly or through the service reliability room; it hands the person,
the room's seats or the team that runs the capability a register and its generated outputs, each claim cited to its
source or marked proposed. The person oversees the work but is not an expert in this system or this kit. So, like any
team taking on work for an overseer, the run first introduces itself and how the two will work together; then, after
a first look, it briefs them in plain words on the capability, every flow found so far with its stages, and where it
recommends starting, and it waits for their picks before reading in depth; once the flow is mapped it stops again
for their pick of how far each stage goes, so a flow can be mapped and left there, or measured stage by stage, and a
map-only run hands on the map and each stage's page with no measure; before any runbook it shows the proposed
alerts, chosen from the health signals, and what each rests on, and waits for their go, because which signals
deserve an alert is a different question from the ways the work can fail; every message says where things stand, and
a run picked up again starts by saying, in full, where the work is. Done, for the whole job: the person can judge from
the first messages that the run understood its job and the system, can see what is covered and what remains, and can
trust what comes out, because every service the flow touches was read and every claim can be traced; and the outputs
are complete enough for the next step (measures built, alerts wired, runbooks used).

## Your first message: the launch

**Before any tool call, before you look at the workspace or open any file, your first message to the person is the
launch below.** It is the same whatever the workspace holds. Send it as it is, changing only the last part to what
their request already gave you. Say nothing before it.

> **Where things stand:** Starting · Nothing read yet · Next: finding whether this work was started before, then a first look over the system · Waiting on you: nothing
>
> **What this is for.** This works out, from a system's code and documents, how to tell whether the business work it
> does is getting done, and what to do when it is not. A *business flow* is one piece of work the system carries for
> its customers from start to finish, such as placing an order. For each flow it describes the stages the work goes
> through and the services that carry each stage, proposes what to measure, and for the stages you choose drafts the
> alerts and a runbook (the steps a responder follows) for each alert. Everything it says is traced to the code, or
> marked as a proposal for someone to confirm. The job is the whole capability: every business flow the system
> carries. Each run maps one flow, a batch of the job, and says what remains.
>
> **How we work together.** There are six activities:
> 1. A first look over the system: what it does, and the business flows it carries. Then I stop for you to pick which
>    flow comes first.
> 2. Describing that flow from the code: its stages, its steps, and the services that carry them.
> 3. Naming the capability and drawing the map of the flow. Then I stop for you to pick, stage by stage, how far to
>    go: mapped only, measured, measured with alerts, or on to runbooks. Then I propose what to measure for the stages
>    you take that far.
> 4. For the stages you take to alerts: first the alerts, chosen from the health measures, which I stop for you to
>    review; then, for the stages you take to runbooks, what can go wrong, and a runbook for each alert.
> 5. Checking every finding against the code, and drawing the map again with what was added.
> 6. A final check and a report, with what remains.
>
> If this work was started before, I first tell you in full where it stands. Otherwise, at the end of the first look,
> you pick which flow comes first; I show you which services I will read and how my findings will be checked
> against the code, and you change those only if you want to. Once the flow is mapped you pick how far each stage goes. You
> review the proposed alerts before any runbook is written. Otherwise I come back to you only when something needs
> your judgement, each time with a recommendation. Every message from me opens with a line like the one above: the
> flow, the stage, the activity, what has been drafted, what is next, and what waits on you. Your tools may ask you to approve
> my reading the system's files or running my checks; that is expected, and approving them lets the work go on.
>
> **What I need to begin.** *[If the request named the system or its code: "You have pointed me at <the system, by
> its name> and its code; that is all I need to begin the first look." Otherwise: "Which system should I look at?
> Point me at its code and any documents about it."]*

In that last part, name what the person gave in their terms (the system's name, its code, its documents) and what is
still needed, and never repeat a path, a folder name or a file name from their request.

If the request named the system, go straight on in the same turn. Otherwise end the turn and wait; when they answer,
start the helper below with their answer as the request, and write nothing before its reply.

**The first look runs in one helper, so nothing of the setup reaches the person.** Right after the launch, in the
same turn, start one subagent with the Agent tool (general-purpose), **with `run_in_background: false`**, so you wait
for it and your turn ends on the brief and the stop (a helper left in the background ends your turn with nothing for
the person, and nothing may wake you when it finishes). Give it: the person's request word for word;
the skill folder's path; and this task: *"Follow `<skill>/SKILL.md`, section 'The run', from looking for earlier work
through the stop for the person's word in phase 0, using `<skill>/FILL-STEPS.md` 'Before you start'. Write nothing for
the person. If you find a stopped run whose first phase is done, run `brief.py reentry`; if its first phase is not
done, finish the first look in it and run `brief.py capability`; with no stopped run, do the first look and run
`brief.py capability`. Your final reply is exactly the text that script printed, and nothing else; if the run is blocked, your
final reply is one plain sentence saying why and what would unblock it."* When it returns, your message is its reply
and nothing else: no sentence before it ("Here is the brief", "I'll pass this along"), none after it. Its first line
is already the status line. Then end your turn: the brief ends with what it waits on, the person's picks or one question
whether to carry on. Write nothing between the launch and that message.

**When the person answers the brief**, record their picks with `go.py` (phase 0, "Their answer is recorded as data"),
which prints the status line; your reply opens with that line and says, in a sentence or two, what was recorded and
what happens next.

**Talking to the person, for the whole run.**
- **Every later message opens with the status line**, copied exactly from `python "<skill>/brief.py" status
  "<your-folder>"` run just before you write it. Never type the line yourself.
- **Write to the person only at the points this file names:** the launch, the capability brief or the re-entry brief,
  the pick of how far each stage goes (after phase 3), the review of the proposed alerts (phase 5a), a question that
  needs their judgement, a plain message that the run
  is blocked and why, and the report. Between
  tool calls, write nothing to them: no narration of what you are about to do.
- **Plain words.** They know the business but not this kit and not this system. Name flows, stages, steps and
  services by their names, never by an id; no file names, script names, folder names or the kit's own vocabulary
  (register, unit, phase numbers, judges, merge); define a term the first time you use it. Setup (Python, scripts,
  folders, the kit's files) is never their concern: if it fails, tell them in one plain sentence that the run is
  blocked, why, and what would unblock it.

## The run

A run is eight phases, done in order, the fifth in two parts with the person's review of the alerts between them.
Between the first and the second, the run shows the person its plan and
waits for their go, whatever the run's size. Each phase has an **In → Out**, and the files it names are what prove it done. The
work goes in the **register folder**, `bfo-work/<application>/` at the workspace root (in a multi-root workspace,
the first folder), never in the skill folder;
it is `<your-folder>` in `FILL-STEPS.md`. Run the kit's scripts from the skill folder, exactly as `FILL-STEPS.md`
writes them, with `<skill>` replaced by the skill folder's path.

**After the launch, the run's first work is to look for earlier work, silently.** Search the whole workspace, not only `bfo-work/`, for every
folder holding `steps.csv` or `lifecycle.csv`, leaving out the skill folder. A folder whose `RUN.md` has the section
*Earlier registers* was made by this version of the kit: if its phases are not all done, this run resumes it (below).
**Every other one is an earlier register: a tool's output, never a source and never a base.** The run never writes
into it, never copies the template over it, and never starts from it: it walks fresh from the code and the person's
sources into a new register folder (`bfo-work/<application>-<yyyy-mm-dd>/` when `bfo-work/<application>/` is taken),
lists each earlier register in `RUN.md` → *Earlier registers* → *Found*, and reconciles each with the new register in
Phase 7. If the stage to cover is not named, prefer one an earlier register has `stage-<id>/` work for, so the
re-derivation can be compared.

**Then `RUN.md`, and nothing else starts before it.** Before reading any code or writing any other file, create the
register folder, copy `register-template/RUN.md` into it, and write its section *What this run will produce* in your
own words, from this file: the application, the flow and the stages (named by the person, or left to the plan's
decisions), and, phase by phase,
what the phase does and the files it must leave. Then set Phase 0 to *doing*.

**`RUN.md` is kept as you go.** At the end of each phase, set it to *done* with the files that prove it, and the
next to *doing*. A phase that cannot be done is set to *blocked* with the reason (for example "python is not on
the path") and what would unblock it, and the run says so in the chat. No phase is skipped silently, and the run
never stops without saying where it stands. **If `RUN.md` already exists**, because the run is resuming or a new
chat has started, read it first. If it waits on their review of the alerts, the re-entry brief carries the alerts
as last put to them, so they have them in front of them. Your next message to the person, right after the launch, is the **re-entry brief**:
the text `python "<skill>/brief.py" reentry "<your-folder>"` prints, sent as it is. It says what the work is, what
the capability is, what has been drafted and found, what was decided and by whom, where it stands, and what is next. Never ask
"shall we pick up where we left off?". When it waits on nothing, it ends by asking whether to carry on with what
is next, recommending yes; on their yes, continue from the first phase that is not done.

**Waiting on the home screen**, at the two stops where the run waits on the person's pick: the flow to map first,
and how far each stage goes. After the message, run `python "<skill>/wait_on_page.py" "<your-folder>"`. It writes
`depth.json`, draws the home screen (`index.html`, by `home.py`) and writes `resume.md`. At the first stop it prints
three things to do: start the listener in the background, start the watch with the Monitor tool (timeout_ms
1800000), and open the page. Do all three. One listener serves the whole run, so the page stays in its one tab: at a
later stop it says the listener is already serving, and the open page, which checks for changes by itself, shows the
new choice within about 15 seconds (unless ticks or words on it are not yet sent: it then says so at its top and
waits for them to be sent or cleared); then start nothing and open no page. If at a later stop it prints all three
again, the listener has gone and the earlier tab has stopped updating: start the listener and the watch, open the
page once, and tell the person to use the new tab and close the old one. End the message with one line saying the run is waiting on the person there. If it refuses,
say why in the chat and take their answer there. **On an `ANSWERS <path>` event,** read that file, record it with
`python "<skill>/go.py" "<your-folder>" --answers "<path>"`, and say back in a line or two what was recorded, then
"you asked to talk about: ..." with the topics `go.py` printed after that phrase, and talk with the person about
them. A tick at any other milestone (talk:) and the words typed in any drop-down are those topics: recorded in
`RUN.md`, never a pick. A post of topics alone records no pick; at the pick, words with no tick record no pick either,
so ask in the chat how far each stage goes. On a refusal, say why in plain words, and how to answer again; still talk
about any topics in the file. Every record draws the home screen again, and the open page shows it within about 15 seconds; it never reloads over
ticks or words not yet sent, and says at its top to send or clear them first. Opening or closing a drop-down
changes nothing. If the
person says "read it", read the newest file in `<your-folder>/answers/` that `go.py` has not recorded already, and record it the same way; if there is none,
ask the question in the chat. An answer typed in the chat is recorded with `--flow` or `--depth`, as below. When the
watch ends with no answer, start it again with the same command. Keep the listener and the watch running between
stops; stop both, with the tool that stops a background task, once the run's report is sent at its end.

0. **Frame, gather, survey and plan** (FILL-STEPS "Before you start").
   In: whatever the person points at in their request (repositories, pages, diagrams, process descriptions,
   documents, notes), and what is already in the workspace. Out: the register's CSV files, copied from
   `register-template/` by `python "<skill>/start_register.py" "<your-folder>"`, never by hand: it copies only into
   a folder holding no CSV file, keeps the `RUN.md` already there, and refuses to write over an existing table;
   `sources.csv` with one row per source, pass `1`, and in `note` the step that will use it
   (the table in "Before you start"); `about.csv` → `sources_examined` and `what_it_is`; the first rows of
   `how-made.csv`; and `RUN.md` → *Sources*, listing what was gathered and what is still missing.
   **First, prove the scripts run:** `python "<skill>/run_status.py" "<your-folder>"`. It says NOT DONE at this
   point, and that is expected. If the command itself fails (no python, a version older than 3.9), set Phase 0
   *blocked* with the error and stop there: every later phase ends in a script, so nothing is drafted that cannot be
   generated.
   **Get every source with your own tools**, whatever its form: you already know how to clone a repository and how
   to read a page, a diagram or a PDF. Put each repository you fetch at the workspace root, as its own folder, because
   every citation starts with that folder. **Every repository the run uses is a folder of the open workspace** (a
   multi-root workspace when there are several), never a temporary folder: the environment's code tools reach only the
   open workspace. If you cannot add folders to the workspace yourself, set Phase 0 *blocked*, name the repositories,
   and tell the person to open them as one multi-root workspace and start again; write the same in `RUN.md`. A source you cannot reach (no access, a dead link) is listed under
   *still missing* in `RUN.md` with what you tried, and the run goes on: a missing source changes what the map is
   worth, never whether the run continues.
   **Check the repository set is complete**, without being asked: (a) for every reference the code makes that no
   folder in the workspace answers (a host or service name, a client package, a queue or topic, an image, a
   configuration key, a URL), search the code host with the person's own access (repository search, code search
   across the organisation) for the repository behind it; (b) search the other way too, for repositories that call,
   consume from or deploy this flow's services; (c) repeat on what the new repositories reference, until a pass finds
   nothing new. Record each repository found in `sources.csv` with the search that found it, and add it to the
   workspace as a further folder, read-only; what is found and cannot be had goes under *still missing*. `RUN.md`'s
   Phase 0 line answers "Is this the complete set of repositories?" with that evidence, and Phase 0 is not done while
   a reference is unresolved and unsearched. If the person's request says to use only the sources they name, do not
   search: list each unresolved reference under *still missing* instead. The same holds when the run cannot search (no
   access to a code host, or the person has said nothing is to be fetched): list each one, with why it was not searched.
   **This phase lists and places; it does not read everything.** Read each source only far enough to say what it
   is and which step uses it. Code is read in full from Phase 1 on, every service the flow touches, as the rules for
   the whole run below say.
   Keep the documents identifiable as a set: Step 8 hands them, without the walk, to a separate pass.
   **Then survey and plan** (FILL-STEPS "Before you start", items 6 and 7): `python "<skill>/survey.py"
   "<your-folder>"` writes `survey.csv`, each service's place, size, entry points and calls, counted by script;
   then the code reader, `python "<skill>/fact-extractor/run.py"`, writes `fact-base.json` in the register folder:
   routes, calls, messages and writes with file and line, found by rule. It is a module: any tool whose output
   `fact-extractor/contract.py` accepts can take its place. Its findings are leads to read, each later cited by a
   row or set aside with the reason; what it misses is found by reading and labelled `proposed:`, a call citing both
   ends.
   **Then the first look, and the capability brief.** Read, shallowly, only what names the business flows: each
   service's entry points and routes (the storefront's pages and its API), its interface definitions, the deployment
   files and the documents. Read no service in depth: that waits for the person's picks. From what you read and the
   survey, write `orientation.json` in the register folder, in the person's words, as FILL-STEPS item 7 sets out:
   what the work is for and what this run will produce, in your own words (it is how the person judges that the run
   understood its job); the capability (what it does, for whom, what one case is); every service the survey lists,
   what it does, and whether you recommend including it; every business flow found so far, each with its stages and
   one sentence per stage, and where in the code you saw it; what you looked at and what is still open; any earlier
   map found and what it changes for this run; and your recommendation (which flow to start with and why, and which
   flows remain after this run). Say nothing here about which stages get measures, alerts or runbooks: the person
   picks that once the flow is mapped. Then run `python "<skill>/brief.py" capability
   "<your-folder>"`. It refuses an incomplete or jargon-bearing `orientation.json` and says why: fix it and run it
   again. When it passes it writes `PLAN.md` and prints the **capability brief**.
   **Stop for the person's word.** `brief.py` marks the stop in `RUN.md`; send the printed brief as
   your message, exactly as printed, wait on the home screen (below), and end your turn. Read nothing further until
   they answer.
   **Their answer is recorded as data, by script, never by hand:** `python "<skill>/go.py" "<your-folder>" --flow
   "<flow, as named in the brief>" --words "<their answer, word for word>"`, with `--test` when the answer is a test
   standing in for the person. The go asks only which flow comes first; where they accepted the recommendation, the
   recommendation is their pick. The services read are those the brief marked include, and the checks per finding
   three, as the brief showed them; only when they say otherwise add `--in <service,...> --out <service,...>` (every
   service named once) or `--judges <n>`. `go.py` refuses `--stages`: the stages are picked after mapping, with
   `--depth`. It writes `scope.json` (with what remains after this run) and `run-settings.json`, and the go and scope
   lines of `RUN.md`; it refuses a flow or service the brief did not name. Map their words to the brief's names
   yourself where the match is plain (a spelling, a shortened name); ask only when their answer matches nothing in the
   brief. If they ask for changes to the brief instead, change `orientation.json`, run `brief.py capability` again and
   wait again. A run's done is not the capability's done: the done check owes what their pick of how far each stage
   goes asks for, and reports every other stage as not yet covered; until that pick it says NOT DONE. With no pick of
   how far each stage goes (an earlier run, whose go named stages), record the ids of exactly the stages they named
   with `python "<skill>/go.py" "<your-folder>" --stage-ids <id>,<id>` once Phase 2 cuts them, and the done check owes
   alerts and runbooks for those stages only. If their answer also says to stop there, stop after recording it.
   Under the service reliability room, the room's own agreement with the person is the go: its chief engineer
   records it with `go.py`. `run_status.py` names any work written before the go.
1. **The case and its lifecycle** (Steps 1 and 2).
   In: the sources. Out: `flows.csv` (the case, whose expectation, start and end), `lifecycle.csv`. The flow is the one the person chose at the go, from the plan's
   decision (their own, or the recommendation they accepted); write it into `RUN.md`.
2. **Stages, process steps, parts and agents** (Steps 3 to 7).
   In: the lifecycle. Out: `stages.csv`, `steps.csv`, `subjects.csv`, `participation.csv`, `set-aside.csv`,
   `agent-system.csv`. Which stages go on to measures, alerts and runbooks is the person's pick once the flow is
   mapped (phase 3), never decided here. An earlier run whose go named stages records their ids with `go.py
   --stage-ids`, adding none and dropping none. Only a run whose `RUN.md` has no *Plan and go* section chooses for
   itself: the stage the person named; else, if the register already has
   `stage-<id>` folders, the next stage with none; else the stage where a case most often waits or can be left
   stranded.
3. **The capability** (Step 8).
   In: the walk so far, and the documents read apart from it. Out: `capabilities.csv`.
   **Mapping ends here, and the run stops for the person's pick of how far each stage goes.** Mapping (phases 1 to
   3) is the whole flow, because the stages come out of it; measuring is chosen per stage. Draw the map
   (`capability_views.py --check`, then `one_canvas.py`, Step 12) so they can see the stages. The message is
   rendered: `python "<skill>/brief.py" depth "<your-folder>" <flow id> --recommend "<which stages to measure, and
   which of those to take on to alerts and runbooks, and why>"`; it names each stage with its process steps and marks
   the stop, and your recommendation is the only text you write. Record the same recommendation per stage with
   `python "<skill>/depth.py" "<your-folder>" --recommend "<id>=none|measure|alerting|runbooks: <one-line reason>;
   ..."`, which writes `depth.json` with the open choice, then `python "<skill>/home.py" "<your-folder>"`, which
   draws the home screen, `index.html`, from it. Send what `brief.py` printed, exactly as printed, wait on the
   home screen (below), and end your turn. Record their answer with `python "<skill>/go.py" "<your-folder>" --depth
   "<id>=measure|alerting|runbooks,..." --words "<their answer, word for word>"` (`--test` for a test standing in for
   them); a stage not named stays mapped only, and an empty answer makes the run a map only. They may later take a
   stage further with the same command; taking a stage less far than already picked is not supported yet, and
   `go.py` refuses it, so tell them so and keep their earlier pick. It sets the phases their
   pick leaves out to *not picked*, which counts as passed. Nothing is measured before their pick: `flow_outputs.py`
   refuses. A map-only run is done once the map is drawn: the done check owes each stage's page and the map, and no
   measure. This pick decides which stages get alerts and runbooks; in an earlier run whose go named stages, those
   stages stand until the person picks.
4. **Measures and costs** (Steps 9 and 10), for the stages the person chose to measure.
   In: the register so far. Out: `measures.csv`, `measure-gaps.csv`, `step-impact.csv`, `case-attributes.csv`, and
   for each measured stage `STRUCTURE.md` and `MEASURES.md` in `stage-<id>/`, written by `flow_outputs.py --out <dir>
   --measures`. Step 9's stage, step and part levels run only for the measured stages; the flow's own measures are
   owed as soon as any stage is measured, and a part shared by several stages is measured if any of its stages is.
   The measure receipt owes exactly that, and nothing for the stages left mapped only.
5. **Alerts for the stages taken to alerting, then runbooks for those taken to runbooks** (Step 11), in two parts
   with the person's review between them.
   Deciding what to alert on and working out the ways the work can fail are different concerns: the alerts are
   chosen from the health measures alone, and the failure modes are what a responder tests once an alert has fired.
   In: the register and the person's pick: 5a for each stage taken to alerting or runbooks, 5b for each taken to
   runbooks. Run 5a for every such stage, then one review for all of them, then 5b for every stage taken to runbooks.
   **5a. Alerting** (Step 11, "Alerting"). Out: the alert choices in `measures.csv` (each alert's basis, the
   expectation it guards and, for a count of cases, the moves it counts), and `stage-<id>/` holding `STRUCTURE.md`,
   `MEASURES.md`, `ALERT.md` and `ALERT.html`, written by `flow_outputs.py --out <dir> --alerts`. It writes the alert
   pages only when the alerting check passes; they show the runbook as still to come. Then **stop for the person's
   review of the alerts**. The message is rendered from the register: `python "<skill>/brief.py" alerts
   "<your-folder>" <flow id> <stage id>... --recommend "<your recommendation and its reason>"`, every stage taken to alerting or runbooks
   named. It gives the status line, then per stage each proposed alert (what it watches, the expectation it guards,
   its kind of health signal, whether it exists today, why it is proposed), the measures considered and not proposed,
   your recommendation, and their options: keep, drop, change or add an alert, or go on to the runbooks. Your
   recommendation is the only text you write, and the script refuses the message while it carries an id, a file name
   or a kit term. A warning that stands goes into the recommendation, with its reason, so it is checked too. Send
   what it prints, exactly as printed, and nothing else, and end your turn. Record their answer with `python "<skill>/go.py" "<your-folder>" --alerts-reviewed --decision
   go|changes --words "<their answer, word for word>"` (`--test` for a test standing in for them): `go` when they
   accept the alerts and say go on, `changes` when they ask for any change. Only `go` closes the review and keeps the
   alert set they reviewed, which is the set the message showed them: a `go` is refused when the alerts changed after
   the message was rendered, so render it again and show them what changed. A change they ask for goes back into `measures.csv`; 5a runs again, which opens the
   review again, and they review again.
   **5b. Runbooks** (Step 11, "Runbooks"), only after their go on the alerts. Out: `failure-modes.csv`,
   `remedies.csv`, and `RUNBOOK.md` and `RUNBOOK.html` in `stage-<id>/`, written by `flow_outputs.py --out <dir>
   --runbooks`, which also writes the alert pages again with their runbook links. It refuses while a stage that has
   alerts has no `ALERT.md`, while their review is not recorded, and when the alerts have changed since they reviewed
   them; and it writes the runbook only when the check passes, so a missing runbook means the check failed: fix the
   register. A measure added in 5b for a test is a companion measure, never a new alert: changing an alert's basis,
   expectation or counted moves takes the run back to 5a and their review.
   A stage no proposed alert reaches (on the stage, its process steps, the parts they use or the flow) gets no
   `ALERT.md` or `ALERT.html`, and its runbook says so; `flow_outputs.py --check` notes it, and does not fail, but a
   stage taken to alerting or runbooks still owes its alert at the done check. Regenerate every other stage their pick takes
   past mapping with plain `--out`, each with its own check, and leave the stages they left mapped only; plain
   `--out` writes what each stage's depth in their pick owes and no more, asks for the alerts' review only on a stage
   taken to runbooks, and refuses an alert changed since their review, which goes back through `--alerts`.
6. **Check and draw** (Step 12).
   In: the register. Out: the three checks of Step 12 run, every failure fixed in the step that produced it;
   `views.html` and `how-this-map-was-made.html` in the register folder, written by `one_canvas.py`. The done check
   opens every drawing page (the map, and each flow, stage, step and part page) and says NOT DONE for one whose
   drawing shows none of what it exists to show (a step's messages, a stage's work, a flow's stages, a part's
   operations or the steps it serves); a frame, lane or key alone is blank. On the map page each figure is judged
   on its own, and the map by its stage boxes and the lines between them. Every page the map's build writes is
   owed, so one it did not write is MISSING. Find why it came out empty and draw it again. A flow found but not mapped owes no drawing.
7. **Reconcile, done check and report.**
   **First, reconcile each earlier register** that `RUN.md` → *Earlier registers* names (skip this when it says
   none): `python "<skill>/reconcile.py" "<earlier register>" "<your-folder>"`. The script matches rows by what they
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
   DONE also needs every field a view requires answered or gapped (FILL-STEPS Step 12). If it says NOT DONE, go
   back to the phase that owes the missing file or writes the empty field, or mark that phase blocked with the reason.
   Then write how far each flow has gone: `python "<skill>/depth.py" "<your-folder>"` writes `depth.json` in the
   folder (each milestone a draft, not started, or reviewed where the person gave a go; the pages drawn for each).
   Then draw the home screen from it: `python "<skill>/home.py" "<your-folder>"` writes `index.html` beside the map,
   one row per flow with each milestone's status and links to the kit's pages for it. Every page drawn while
   `index.html` is in the folder links back to it.
   Out: `RUN.md` with every phase done, blocked, or *not picked* by the person, and the report to the person: the register folder, the flow and
   stage, the check results, the stages that still have no Step 11, each earlier register and what its reconciliation found (added,
   carried forward, not supported, not assessed, disagreements, each named), anything you could not do, and the output of
   `run_status.py` pasted as it is. End the report with **What would make this map fuller**: the deployables the map
   stops at (every part under *still missing*, and every external dependency with no source of its own), then the
   `proposed:` rows counted by the kind of source that would settle them, read off the table in FILL-STEPS "Before
   you start".

## Rules for the whole run

- Read `FILL-STEPS.md`, then `register-template/REGISTER.md` and the reference files `FILL-STEPS.md` cites in
  `reference/`, before Phase 1. Look at `example-eshop/` only to see what a finished register and its outputs look
  like. It is a different application and never a source of facts.
- Step 11 covers the stages the person picked; a flow is covered when every stage has had one, and the capability
  when every flow is.
- **Follow the code past the workspace.** When a move calls a deployable whose code is not here, identify it from
  what the call shows (an address, a client package, a queue or topic name, an image) and get it with your own
  tools if you can reach it: it is a pass-1 source like the others. Fetch it only with access the person already has, and read-only: never request access, enter credentials, or change anything at the source. Record every fetched source in `RUN.md` *Sources* with what referenced it and why. If the person's request says to use only the sources they name, do not fetch: list it under *still missing* instead. With its code it is a component, whoever owns
  it, and you read the operations this flow calls and what those call (FILL-STEPS Step 5); how far into an outside
  service to go is Step 6's. If you cannot reach it, it stays a part cited by how you identified it, an external
  dependency, and goes under *still missing* in `RUN.md`.
- **Read in full every service the flow touches.** Steps 1 to 8, the mapping, cover the whole flow and read every
  service it runs through, whatever stage it carries. Steps 9 and 10, the measures and costs, cover only the stages
  the person picked to measure, with the flow's own measures and the parts those stages use. Step 11 covers only the
  stages picked for alerts and runbooks. A run is cut shorter only when the person asks for it (`USE.md`). `KNOWN-GAPS.md` "At scale" says what is
  still open at size.
- **Open code with the Read tool, and write each row from what you read.** A row is written from code read, never
  from a script that searches the code and emits rows; a script may find where to look. The done check takes what
  was read from Claude Code's own record of the session, not from anything the run writes: every location a row
  cites must have been opened with Read, its lines inside the part read, or be a fact the code reader produced. A
  file shown by a shell command does not count. Before the done check, `python "<skill>/reread.py" "<your-folder>"`
  draws `re-read.csv`, a sample of rows; one agent that wrote none of the rows opens each row's cited lines and
  writes whether the code says what the row claims (FILL-STEPS "The run ends with `run_status.py`").
- **Talk to the person in names, not ids**, as "Talking to the person" above says: name parts, process steps and
  stages by their names ("the Ordering API", "Accept the order"), never by id, in every message and report.
- Never stop to ask the person a fact you can infer: where the sources do not say something, infer it and label it
  `proposed:` with the reason. What is the person's (intent, scope, judgement and taste: which flow, whether the
  sources are enough, whether to keep going) is brought to them with your proposal when it arises. The plan is the
  first such point.
- Never edit a generated file: fix the register and generate again.

## What the person gets

`USE.md` in the skill folder is written for the person running this. It explains what comes out, how to read it,
and what to check before taking it to anyone. `KNOWN-GAPS.md` lists what the kit is known to get wrong. Point the
person at both when you finish.
