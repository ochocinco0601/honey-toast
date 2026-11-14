---
name: bfo-measures
description: Propose what to measure for the stages of one mapped business flow that the person picks - what each party the flow serves counts on, and for each stage, process step and service the candidate measures, each saying the question it answers, whether the system already produces it and where, and whether anything collects it - with the coverage list and the measures' inspection, ending in the person's review of the measures. Steps 2 and 3 of the path to supported in production (what to measure, and whether the system can show it). Use when a flow has been mapped (by the bfo-mapping skill) and the person asks what to measure or monitor for it, or which of its stages can be seen today. Design time only - it reads what mapping recorded, the code and collection configuration, never a running system. It chooses no alerts and sets no targets; the business flow observability stage kit (bfo-stage-kit) takes the measures on to alerts and runbooks, and the stage kit also runs this skill, for its phase 4.
---

# Proposing the measures: for the stages picked, from a register whose mapping is finished

This folder is the measures skill. Everything below calls it **the skill folder**. Wherever `MEASURES-STEPS.md`
writes `<skill>`, it means this folder, and the folders it names (`register-template/`, `method/`, `reference/`) are inside this
folder too.

## The job this serves

The bigger job is to get a business capability to supported in production: someone can tell whether the work it
does for its customers is getting done, is told when it is not, and knows what to do; and, one level further up,
the customers and the business who depend on it get what they need, and when something breaks the harm to them is
found and limited first. On the path to that, mapping (step 1) says who depends on the flow and what carries it.
**This skill is the next two steps of that path, taken together:** what to measure (step 2), and whether the
system can show each measure today, where, and whether anything collects it (this skill's part of step 3). They are one
skill because a measure's definition and how it is taken are one thing to whoever builds it; they stay two halves in
its inspection and its review.

**It receives** a register whose mapping is finished for the flow (the folder of files one mapping run wrote:
mapping's last stop reached, its inspection run), from the bfo-mapping skill, or from a stage kit run that has
finished its flow, for a further stage (a register an earlier version of these skills wrote is brought up to this
version's form first, without asking); the
code mapping read, open in the workspace, and any collection configuration within reach (scrape, collector or
dashboard configuration); and the person's pick of which stages to measure, from their request or asked for. Run
by the stage kit, it receives the same from the kit's phase 4, in the middle of the kit's run: the register, the
kit's hold on it, and the pick of how far each stage goes, already recorded by the kit.

**It hands on**, after the person's go at the review of the measures (run by the stage kit: as soon as its step 3
is done, to the kit, which holds that review, records the go and runs the done check): the measures of the flow and its picked
stages, what each party counts on, and the reason any part has no measure. They go to choosing the alerts (the
stage kit's next step, which picks the alerts from these measures alone and writes nothing of this skill's) and to
the runbooks, which read the measures a responder's checks use. What cannot be seen yet is handed, as rows, to
the developers and to whoever runs the monitoring: a measure the code would have to start producing, a record that
does not exist, and a measure produced but collected by nothing. Turning those rows into written requests to them
is not built yet. What it finds wrong in what mapping recorded goes back to mapping as a correction, named to the person, for
mapping to take up when it runs again.

**Done, for the whole job,** is not a full table: choosing the alerts can work from this output alone, without
going back to the code; every measure said to be produced today cites the line that produces it, and every
"collected" rests on the collection configuration that was read; every part of the picked stages has a measure or
the reason it has none; and the person has seen the measures and said go. The inspection checks that each citation
is there; whether each says what its row claims is checked by a reader who wrote none of the rows, which a run of
this skill alone does not do yet, so its closing message says the measures are reviewed, not verified. Run by the
stage kit, the person's go and that re-read are the kit's: done for this skill's part is its step 3 with its
checks passing, handed back to the kit for the review.

Inferred, and so to be checked first: that the person who asks is the same one who oversees operations and reviews the measures.

## Run alone, or by the stage kit

`MEASURES-STEPS.md` is the only text of the step "Propose the measures": the stage kit carries no copy of it.

**Run alone**, everything below applies: the first message, then "The run" from step 1 to step 5. A stage kit run
still under way on the flow is carried on by the stage kit, not by a run of this skill alone.

**Run by the stage kit**, for its phase 4, the kit has already sent its own launch, run its start step, taken the
register's hold and recorded the person's pick of how far each stage goes. Do only step 3 of "The run", "Propose the
measures", in the register folder the kit names, for every stage of the flow picked past mapped only (to measure, to
alerts or to runbooks), and run each command from the stage kit's own folder, which carries the same scripts: where
this file or `MEASURES-STEPS.md` writes `<skill>`, put the kit's folder, so the person keeps the kit's status line
and stops. Read the folders this file and `MEASURES-STEPS.md` name (`register-template/`, `method/`,
`reference/`) in the kit's folder too: they are copies built from one source. "Rules for the whole run" below still hold. Skip the
rest: no first message; no step 1 (the kit has found the register and holds it, and its run being
under way is why you are here); no step 2 (the pick is recorded); no step 4 (the kit renders the review of the
measures itself, naming every measured stage, and records the person's answer); no step 5 (no closing message, and
never stop the page's listener: the kit's page and its wait stay up). When step 3 is done, its checks passing,
go back to the stage kit's `SKILL.md`, phase 4, for the review. A `changes` at that review, or a correction a later
step files, brings the kit back here, to step 3 again.

## Your first message

**Before any tool call, your first message to the person is the one below.** Send it as it is, changing only the
last part to what their request gave you. Say nothing before it.

> **Where things stand:** Starting · Nothing read yet · Next: finding the flow's mapping and checking that it is finished · Waiting on you: nothing
>
> **What this is for.** Once a business flow has been mapped (the stages its work goes through, the steps in each
> and the services that carry them), this proposes what to measure, so that someone can tell whether the flow's
> work is getting done. For each stage you pick, it proposes measures such as how many cases are in the stage and
> how long the oldest has waited, whether each step that matters happened and came out right, and whether each
> service that carries the work is doing it. It first writes down what each party the flow serves counts on, so
> that every measure answers to someone. For each measure it says what question it answers, whether the system
> already produces it today and where, and whether anything collects it. Everything it says is traced to the code
> or marked as a proposal. It sets no targets and chooses no alerts: those come after your review.
>
> **How we work together.**
> 1. I find what mapping recorded for the flow and check that it is finished. Unless you have already said which stages to measure
>    and the check of mapping's work finds nothing, I stop for you to pick them, with my recommendation and that
>    check.
> 2. I write down what each party counts on, then propose the measures for the stages you picked, reading the code
>    at each place a measure would be taken from.
> 3. I stop for your review of the measures: a short list per stage, what each measure shows, whether the system
>    produces it today and whether anything collects it, what any of them gets wrong today, and why any part of
>    those stages has no measure; and a check of the measures in two halves, what to measure and what the system
>    produces. The detail behind each is there when you ask for it. You keep, drop, change or add measures, or say go. Your go ends this
>    work, and choosing the alerts can start from it.
>
> Otherwise I come back to you only when something needs your judgement, each time with a recommendation. Every
> message from me opens with a line like the one above. Your tools may ask you to approve my reading the system's
> files or running my checks; that is expected, and approving them lets the work go on.
>
> **What I need to begin.** *[If the request named the flow, or the system whose flow is mapped here: "You have
> pointed me at <the flow, by its name>; that is all I need to begin." Otherwise: "Which flow should I start
> from? Name the system and the flow, as much as you know; I will look for its mapping in what is open here."]*

In that last part, name what the person gave in their terms, and never repeat a path, a folder name or a file name
from their request. If the request named the flow or the system, go straight on in the same turn; otherwise end the
turn and wait.

## Talking to the person

- **Every later message opens with the status line**, as `say` or a script prints it. Never type it yourself.
- **Write to the person only at:** the first message, the pick of stages (when it is needed), the review of the
  measures, a question that needs their judgement, a plain message that the work is blocked and why, the one-line
  notices step 1 names (the work brought up to this version's form, an earlier chat's hold that lapsed, a copy of
  this skill out of date), the detail of the review when they ask for it, and the closing message after their go.
  Between tool calls, write nothing to them.
- **Plain words.** They know the business, not this skill or this system's code. Name flows, stages, steps and
  services by their names, never by an id; no file, script, folder, table or column names; never call a measure a
  count, or this work counting. Every message you write yourself goes through `say`: write it to a file outside the
  system's code and run `python "<skill>/brief.py" say "<your-folder>" "<message file>"`; send what it printed,
  exactly. It refuses ids, file names and kit terms it knows: say each in the person's terms and run it again.
- **The status line** names where this work stands among its own steps (the pick of the stages, proposing the
  measures, the person's review, and then the alerts as next, with the stage kit). Send it as printed.
- **Before the register is found**, `say` takes the workspace root in place of `<your-folder>`.

## The run

The work is in the **register folder**, `<your-folder>` below: the folder mapping wrote for the flow, usually
`bfo-work/<application>/` at the workspace root. Run the skill folder's scripts exactly as written here and in
`MEASURES-STEPS.md`, with `<skill>` replaced by the skill folder's path.

1. **Find the register and check that mapping is finished.**
   In: the request, and the workspace. Find the register folder: a folder holding `flows.csv`, `lifecycle.csv`
   and `RUN.md`. If there are several, or the flow is not in its `flows.csv`, ask the person which, through `say`,
   naming each by its system and flows. If there is none, tell them, through `say`, that the flow has to be mapped
   first (the mapping skill does that), and stop.
   The flow's mapping is finished when `RUN.md` shows mapping's phases 1 to 3 done. If they are not, tell the person
   so, through `say`, and stop: proposing measures on a flow still being mapped would measure the wrong stages. If
   `RUN.md` shows a stage kit run under way on the flow (its pick of how far each stage goes waiting, or the alerts,
   their review or the runbooks neither done nor *not picked*), tell the person the stage kit carries that run on,
   and stop. Its last two phases (check and draw; done check and report) left *to do* by an earlier run of this
   skill are not a stage kit run under way: carry on.
   **Then take the work up, by script, silently:** `python "<skill>/start.py" "<workspace root>" --resume
   "<your-folder>"`. It takes this run's hold on the register (below), and prints a `KIT:` line naming the build this
   copy of the skill is; a `WARNING` on that line means the copy is partial, mixed with another version or out of
   date, and the step stops there: tell the person in one line, through `say`, that this copy of the skill is
   incomplete or out of date and needs installing again from its source, and stop. It also brings up the work
   page, which shows the person the work so far beside the chat: give them the address it prints (its `PAGE:`
   line) in your next message, saying it is the page for this work, and if it prints `OPEN FAILED`, first open the
   address in their browser as that line says. On `PAGE: not brought up`, say nothing of a page: the work goes on
   in the chat. Send nothing else it prints
   (its wait and its message are the stage kit's), and start no wait: this skill takes the person's answers in the
   chat. What else it can print:
   - `REFUSED`, the folder not being a run this kit can pick up. Where `RUN.md` shows mapping finished (above), it
     is a run an older version wrote: follow `UPGRADE: not done` below. Otherwise the register is another tool's
     output: tell the person, through `say`, that the flow has to be mapped first (the mapping skill does that),
     and stop.
   - DECISION `held`: another chat holds the work (below).
   - DECISION `finish-first-look`: mapping's first look of the system is not finished, so mapping is not either:
     tell them so, as above, and stop.
   - A line starting `note: took over the lock`: an earlier chat's hold had lapsed (below).
   **A register an earlier version wrote is upgraded without asking.** When the start step picks the register up,
   it does this itself, once it holds the lock: it backs the register folder up outside the workspace, migrates it
   in place (with `reconcile.py`, which this skill carries), and prints `UPGRADED:` with what changed, where the
   backup is, the lines it leaves owed, and, last, the sentence that tells the person. Do what that line says before
   anything else: run the check, `python "<skill>/capability_views.py" "<your-folder>" --check`, and restart the
   page's listener, which otherwise keeps running the older version (`python "<skill>/listener.py" stop
   "<workspace root>/bfo-work"`, then `python "<skill>/wait_on_page.py" "<your-folder>"`, sending nothing it prints
   and starting no wait). Send the sentence for the person through `say`, in place of the message it speaks of. A
   column the upgrade fills from the register's own rows is filled without asking. Where `UPGRADED:` says code must
   be read again, say so in that same message, saying what will be read and why, and go on in the same turn: if
   they object when they read it, stop and take their answer. Only a check failure the upgrade does not explain is a
   reason to stop and tell them, through `say`. If it prints `UPGRADE: not done` instead, run the check: where it
   names `reconcile.py --migrate`, back the register folder up to a folder outside the workspace (inside it, the
   copy would be taken for an earlier register), run `python "<skill>/reconcile.py" --migrate "<your-folder>"`, run
   the check again, and tell them as above; then run the start step again, so this run takes its hold on the
   register. Any other failure, stop and tell them.
   Run mapping's inspection, `python "<skill>/check_map.py" "<your-folder>" <flow id>`. It reports and never
   blocks. A rule it fails is mapping's to put right, never this skill's: file each as a row in `corrections.csv`
   for mapping (`MEASURES-STEPS.md`, "What this step reads"), and stop at the pick (below) even when their request
   already named the stages, so they decide with the inspection in front of them whether to measure on mapping's
   work as it stands now or have mapping take the corrections up first. Recommend the second when a failed rule changes what the
   coverage list asks (stages that do not lead into each other, a step tied to no move, an AI agent's decisions
   left unclassed, steps with no Business Impact, where some of those steps matter); otherwise recommend going on.
   **The code must be open here.** Every repository `sources.csv` lists as code must be a folder of the open
   workspace, because the citations start there and this step opens the cited lines itself. If one is not, tell
   the person, through `say`, which (by its name) and that it needs opening here, and stop until it is.
   **If a script refuses because another chat holds the register** (at the start, `start.py` prints DECISION
   held), ask the person, through `say`, to confirm no
   other chat is working on it. On their yes, run `python "<skill>/start.py" "<workspace root>" --release
   "<your-folder>" --words "<their answer, word for word>"`: it frees the register for this run and picks it up as
   the start step does, so act on what it prints as above (an upgrade, a lapsed hold), sending none of the rest.
   Never wait the lock out. A lock no run has written for four hours is not a refusal: the next script that writes
   takes it over, says so (a line starting `note: took over the lock`), and records it in `RUN.md`, so a stopped
   chat never leaves the register unusable. When that happens, tell the person in one line, through `say`, that an
   earlier chat's hold on this work had lapsed and this run has taken it over.

2. **The pick of stages to measure.**
   If the request named the stages and the inspection passed every rule, record them and go on. Otherwise stop:
   write through `say` mapping's inspection as `check_map.py` printed it, each stage of the flow by name with one
   sentence on what happens in it, your recommendation of which stages to measure first and why (where cases wait
   or can be lost, and where the most is at stake), and the question: which stages to measure (and, when a rule
   failed, whether to go ahead on mapping's work as it stands). End the turn. If they say mapping should put its work right first, tell
   them the mapping skill takes the corrections up when it runs again, and stop.
   Record their answer with `python "<skill>/go.py" "<your-folder>" --depth "<id>=<depth>,..." --words "<their
   answer, word for word>"` (`--test` when a test stands in for them). Name every stage already picked for this
   flow at the depth it was picked (`depth` in `scope.json`), because a stage left out is recorded as mapped only
   and taking a stage less far is refused; then each stage they pick now, at `measure`. Alerts and runbooks are the
   stage kit's: if they ask for them, say so through `say` and record `measure`. A stage no one names stays mapped
   only.

3. **Propose the measures** (`MEASURES-STEPS.md`, all of it).
   Read `MEASURES-STEPS.md` first, then `register-template/REGISTER.md` for the columns of the tables it writes.
   In: the register, the code, any open row of `corrections.csv` naming this step's tables. Out: `expectations.csv`,
   `measures.csv`, this step's rows of `measure-gaps.csv`, any `product-names.csv` rows, and the `how-made.csv`
   rows of step `9`. **Open code with the Read tool, and write each row from what you read**: a script may find
   where to look, never write a row. Then, for every stage of this flow picked to measure (run by the stage kit:
   every stage picked past mapped only, to measure, to alerts or to runbooks), `python "<skill>/flow_outputs.py" "<your-folder>"
   <flow id> <stage id> --out "<your-folder>/stage-<stage id>" --measures`, and fix what its check names, in the
   rows, until it passes. Then `python "<skill>/check_measures.py" "<your-folder>" <flow id> <stage id>...`, naming
   every stage you measured: it reports and never blocks; put right every failure that is this step's, and keep for the
   review only what you cannot (with the reason in your recommendation).

4. **Stop for the person's review of the measures.**
   `python "<skill>/brief.py" measures "<your-folder>" <flow id> <stage id>... --recommend "<your recommendation
   and its reason>"`, naming every stage of this flow picked to measure and no stage taken further (to alerts or
   runbooks), whose review is the stage kit's. It gives, per stage, what each party counts on, a short list of the
   stage's measures (what each shows, whether the system produces it today, whether anything collects it), what a
   measure produced today gets wrong, and each part with no measure and why; then the measures several stages
   share and the flow's own, the coverage list and the inspection as counts with anything that fails, your
   recommendation, and their options. Your recommendation is the only text you write, and the script refuses the
   message while it, or register text it shows, carries an id, a file name or a kit term: fix the recommendation,
   or the row the text comes from, and run it again. Send what it printed, exactly, and end your turn.
   The detail one level down (where each measure is produced and of what kind, and every item of the coverage list
   with the measure that answers it) is written beside the message, as `measures-review-detail.md` in the register
   folder, checked by the same script. When the person asks for it, whole or for one stage, send them that text,
   or its section for the stage, as it is: the whole text opens with its own status line; a stage's section goes
   through `say`, which puts the status line before it.
   Record their answer with `python "<skill>/go.py" "<your-folder>" --measures-reviewed --decision go|changes
   --words "<their answer, word for word>"` (`--test` when a test stands in for them). `go` keeps what they
   reviewed; it is refused when the measures changed after the message was rendered, so render it again and show
   them. `changes`: make each change in step 3, and review again.

5. **After their go.** Write to the person, through `say`: the measures of those stages are reviewed and kept
   (reviewed by them, not yet re-read against the code by someone who wrote none of them); how many the system
   produces today, how many it does not yet, how many are produced but collected by nothing, how many it is not
   known whether anything collects, and how many records the code does not keep; that the ones not produced, not
   collected or with no record are what the developers and whoever runs the monitoring would be asked for; any
   corrections filed to mapping, for it to take up when it runs again; and the next step in their terms: to
   choose the alerts for these stages, they ask the stage kit for alerts on them, and it starts from these
   measures. The work ends there: stop the page's listener (`python "<skill>/listener.py" stop "<workspace
   root>/bfo-work"`); the stage kit brings the page up again when it runs. A further stage, or the same flow again, starts at step 2.
   **The state it leaves.** A first pick on a register the mapping skill finished leaves the flow finished. A pick that
   changes an earlier one (a further stage) sets the run's check-and-draw and done-check phases back to *to do*,
   and this skill does neither: the flow then counts as not finished until the stage kit runs on it, and the
   mapping skill will not start the next flow before then. Say so in the closing message when it applies: the map's
   pages are drawn again and checked when the stage kit next runs on this flow, and the mapping skill starts no further flow until then.

## Rules for the whole run

- **Never write mapping's tables** (the flow, its lifecycle, stages, steps, parts, who carries out each step,
  agents, Business Impact). Where one is wrong or missing, file a row in `corrections.csv` and go on.
- **Never write alerts or runbooks**, and never set a target or threshold that no document or person states.
- **Never edit a generated file** (a stage's pages): fix the register and generate again.
- **Not found is not absent.** A measure or a record you did not find is written as a gap with its reason, never
  left out.
- Never stop to ask the person a fact you can read or infer: infer it, and label it `proposed:` with the reason.
  What is theirs (which stages, whether the measures will do) is brought to them with your recommendation.
