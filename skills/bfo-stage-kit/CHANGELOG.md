# What changed in each release

Newest first. Each release replaces the one before it. If you ran an earlier release, see USE.md, "If you ran an
earlier version of this kit": a new run leaves your earlier register untouched and checks it against the code.

From Release 3, each entry ends with an effect line: what a register you already have needs for it. It is
`none`, `rename: reconcile.py --migrate` (a mechanical rename that touches no content; the check refuses the
register until it runs), `fill from each row's citation` (the answer is in the lines each row already cites), or
`re-walk` a named part of the walk, with the reason.

## Unreleased

### What you will notice

- **The page stays in one tab, and comes back if you close it.** The first stop no longer opens a second tab of
  the page; a reload or a link to another page of the run is not taken as a closed tab; if you close the tab, the
  next stop opens it again.
  Effect: none.
- **The page's background program stops when the run ends,** read from the run's record a couple of minutes after
  its end, even with the page still open in your browser.
  Effect: none.

## Release 6 — 2026-10-29

### What you will notice

- **A Sources page shows what the run is working from.** The home's top bar, and the page shown while the run
  starts, link to it as soon as a source is listed: each source gathered, what it is, and each one that could not be
  reached, with why. It only reads; nothing is added or retried from it.
  Effect: none.
- **The run's own words are checked before they reach you.** Every message the session writes itself, not only
  the ones a script prints, is checked for ids, file names and the kit's process words (phases, "the go", a stop,
  register and the like) and rewritten in your terms before it is sent.
  Effect: none.
- **The page's address comes with every message that points at the page,** not only when the browser could not
  be opened: the scripts add it themselves while the page is up, so it is never typed by hand.
  Effect: none.

- **The page comes up first, before the first look.** The start step now runs in the session itself, right after
  the opening message: it brings up the run's page, records when the run started, and only then looks for earlier
  work. The first look then writes its list of sources, its survey and the code reader's facts as each is complete,
  so the page shows how far it has got instead of nothing until the brief.
  Effect: none.

- **Two chats can no longer write one register at once.** A run could be picked up by a second chat while the first
  was still writing it, and each overwrote the other's work. The run that starts or picks up a register now holds
  it, and every script that writes the register refuses another chat while the holder has written within the last
  four hours, writing nothing. Picking up work another chat holds asks you whether that chat has stopped, and carries
  on only on your word, which the register records. A chat that has not written for four hours loses its hold to the
  next one that writes, which says so, so a chat that crashed never leaves the register stuck. Where the chat
  cannot be told apart from another (nothing names it), the run goes on without the hold, and the register says so.
  Two first looks started in one chat cannot be told apart by the hold, so a second start while a first look is
  under way is refused until that first look reaches its brief.
  Effect: none.

- **Work started before is picked up where it stands, decided by a script.** A run used to decide by its own
  reading whether the workspace held a run of this kit to carry on, and could miss one: it then looked over the
  system again and asked for the first flow again. The run's first work is now `start.py`, which searches the
  workspace and decides: one run not finished is picked up with the re-entry brief, several are put to you to pick
  from, and with none the first look starts fresh. The capability brief is refused for a run past its first look,
  and a new register is refused while a run is not finished, unless you have said to start new work, in words the
  new run records.
  Effect: none.

- **After a Done, the home screen no longer brings back your earlier ticks and words.** A browser could put the
  last answer's ticks and words back into the page after it reloaded, so the page held at the next choice as if you
  had changed something, and a Done would have sent the old answer again. Every tick and box on the home screen now
  opts out of that, and the page takes what it holds once loaded as nothing changed. Ticks and words you have not
  sent yet are kept by the page itself, in that browser tab: if you open one of the kit's pages and come back, or
  reload, they are put back as not yet sent. What a Done sent is not kept. If the run has moved to another choice
  meanwhile, the ticks and words for the old choice are not put back; your topics to talk about are.
  Effect: none.
- **The session says plainly when a stop is answered and how its two background tasks end.** Only a pick that
  `go.py` records answers a stop; a post of topics alone, words with no tick at the pick, or a refusal leave the run
  waiting there. The wait is stopped by its task id, and the page's listener by the stop command printed for it, once the run's report is sent.
  Effect: none.
- **After a refusal, the session no longer says the page was drawn again.** Nothing is recorded on a refusal, so
  nothing is redrawn. The answer can be sent again on the page or in the chat; when `go.py` says the page was drawn
  before the choice changed, the session draws it again first, and otherwise the page already shows the choice open
  now.
  Effect: none.
- **A home screen opened just as the run moved on now catches up.** If the run drew the page again in the moment
  between the tab opening it and the page's first check, the tab used to stay on the older page until the next
  change. Each drawing now carries a stamp of what it shows, and the tab compares against the one it opened.
  Effect: none.
- **The run searches for more code only where you agree.** Start with as much or as little as you have; for what
  is not there, the brief says what the run cannot find and where it proposes to look, and it searches only where
  you say yes; the brief's last part asks you which. With only a system's name, the run first looks at what is open
  in your workspace, and if the code is not there it proposes where to look and waits for your yes. Code found on a
  yes in the chat is surveyed and the brief is shown again, keeping any flow you picked as the recommendation, so you
  confirm it once; a yes sent from the home screen with a flow ticked goes on with that flow and the code found. What
  you do not agree to search is listed as still missing.
  Effect: none.
- **Done on the home screen counts only what it sent.** The page says "Sending…" until the answer is saved. Ticks
  or words you change while it is on its way stay unsent, so the page will not reload over them, and a second Done
  within the same second is saved like the first.
  Effect: none.
- **The home screen's hold message says "send or clear".** It used to say "save", where the kit's own
  instructions say "send"; both now use the one word.
  Effect: none.
- **Unticking a milestone on the home screen leaves the earlier ones as they are.** Unticking one takes the
  later milestones of that stage with it, as before; it no longer ticks the earlier ones.
  Effect: none.
- **Clear on the home screen.** A Clear beside each Done puts the ticks and words in its own drop-down back as the
  page loaded (or as your last Done sent them); the Clear on the line at the top does the same for the whole page.
  Clear sends nothing, and what stays unsent elsewhere is still kept. A drop-down's Clear also undoes the earlier
  milestones its own ticks ticked in other drop-downs. Once nothing is unsent, a held update goes ahead. Done still
  sends everything on the page.
  Effect: none.
- **The home screen says when it has put your unsent ticks and words back.** After a reload, or coming back from
  one of the kit's pages, a line at the top says they are back and not yet sent, with Send and Clear. A Send from
  that line leaves "Saved at" showing there until the page updates or you change something. After any Done, if
  anything changed after you pressed it, the line says that is not yet sent. Topic words are not put back under another flow: where
  the place you typed them now asks for your choice, or is no longer on the page, the line quotes them and says
  which, on every load of the page, until you press Clear on that line or send with Done.
  Effect: none.
- **The run opens its page by itself.** At each stop, the script that readies the home screen starts the page's
  listener when none is serving and opens your browser on it, instead of leaving both to the session; when the
  browser does not ask for the page, the session opens it itself. The session gives you the page's address too,
  every time it points you at it. Before your run has a home screen the page shows
  where the run stands, and it moves to the home screen by itself once there is one. A proxy set for command-line
  tools on your machine does not stop the run from finding its own page. The small web server that shows the page
  stops by itself after eight hours with no request; USE.md says what it is. If you close the page's tab,
  a later stop does not open it again; the address in the chat brings it back.
  Effect: none.
- **The home screen is replaced whole when the run draws it again,** so an open tab never loads a half-written page
  and stops following the run.
  Effect: none.

## Release 5 — 2026-10-28

### What you will notice

- **A home screen.** Every run draws `index.html` beside the map: one row per flow, each milestone shown as its
  status (not started, draft or reviewed), and a drop-down per milestone with what there is to review and links to
  the kit's own pages for it. The map and every page drawn once the home screen is beside it link back to Home. While the run waits on your pick
  of a flow or of how far each stage goes, the home carries the ticks and a box for your words.
  Effect: none.
- **The home screen's dots say only what the kit knows.** The dots for Instrumented, Dashboards built and Team
  prepared never fill, since that work is other teams'; Instrumented keeps its count of measures sent to monitoring,
  read from the code at design time. Runbooks written fills once drafted, as runbooks are never reviewed, and the
  legend says what fills each dot. The open page checks for changes by itself from the moment it loads, however long
  the run takes, and shows each redraw within about 15 seconds, sooner just after a Done. It never reloads over
  ticks or words you have not sent: it says at its top that the run has moved on, and updates once you save or
  clear them. Opening or closing a drop-down is not a change.
  Effect: none.
- **The home screen is served safely and says when it has stopped updating.** The page's listener serves only the
  run's own pages, by any spelling of the address, and never its tables, its answers or its run state. One listener
  serves the whole run, so the page you have open shows each new choice in the same tab; once the run ends and
  Claude Code stops watching it, the page says so and to carry on in the chat. Saying "read it" never takes answers
  already recorded: with nothing newer, Claude asks in the chat. A ticked topic names its milestone once in the run
  record.
  Effect: none.
- **Each measure says where it is counted.** Beside the kind of record it is taken from, every measure now names
  the place in plain words a reader knows without the code: the table and the database it lives in, the log and the
  service that writes it, or the system whose own status it is, such as the message broker or the database server.
  Where the code does not show one, it says what it would take. The home screen shows it with each stage's measures.
  A server's own status names the product, and a measure counted from two places names both. A measure that cites
  its source and leaves the place blank, or names it as the code spells it, keeps the run from being done, and so do
  two measures naming one place that disagree on whether it exists; the check says which.
  Effect: fill from each row's citation: open the line each measure's `source_ref` cites and write the place it names
  in the new `counted_at` column; nothing is walked again.
- **Whether a measure exists today follows from its signal, not its kind.** A count of a request metric the
  framework already records, a join of log lines and spans the code already writes, a count over rows the code
  already stores, or a server's own answer to a probe, now says it exists today,
  citing the emitting lines; only a measure that needs the code to write something new says it does not. The
  worked example's six measures of that kind are corrected.
  Effect: fill from each row's citation: where a measure says it does not exist and its citation shows the signal
  already written, set it to exist and cite the emitting line.
- **Regenerating a stage writes what you picked for it and no more.** A stage you chose to map or measure only gets
  its slice and measures, a stage taken to alerts its alert pages, and only a stage taken to runbooks waits for your
  review of the alerts. An alert changed since you reviewed it is never written again unseen: it comes back to you.
  A stage you left mapped only is not regenerated. Once you have picked how far each stage goes, the status line and the brief that picks a run
  up again say that pick, a run stopped at the pick shows you the stages again, and the run record keeps your words
  on it under Plan and go, with *not picked* for the phases it leaves out.
  Effect: none.
- **A blank drawing no longer passes.** The final check opens the map and every flow, stage, step and part page,
  and a page that draws nothing keeps the run from being done. A frame, lane, key or row of empty lifelines is
  nothing: a step must show its messages, a stage its work, a flow its stages and a part its operations or steps.
  A step or stage the register gives nothing to draw (a step carried out outside the application) is not held to it.
  On the map page each drawing is judged on its own, so one drawn figure no longer carries a blank one, and the map
  itself must show its stages and the lines between them. Every flow, stage, step and part page the map's build
  writes is now an expected output, so the count of expected outputs goes up and a page left unwritten is MISSING.
  Effect: none.
- **A run picked up again calls its work drafted.** The brief that picks a run up again lists what the run has
  drafted so far, never as done, and leaves your picks and review to what was decided. The launch says the status
  line shows what has been drafted. A split run's sponsor page ends on *Draft complete, for your review*, saying the
  done check found every output, as a draft for review, not accepted.
  Effect: none.
- **The pick of how far each stage goes says when mapping changed the stages.** When the stages found by mapping
  the code differ from those the first look proposed, the message says so and names both.
  Effect: none.
- **The status line says what the run has drafted and what comes next, and calls it a draft.** It never names one
  piece of work as both drafted and next: describing the flow, naming the capability and measuring are each
  reported in two parts, and your picks and review are never reported as the run's work. Once the flow is mapped
  it names the stages mapped. `Done:` is now `Drafted:`, the end of a run reads *Draft complete, for your review*,
  and the final check's DONE line says every expected output exists as a draft for review, not accepted.
  Effect: none.
- **When the done check cannot find the session's record, it says what to set.** A session started outside the
  register's folder keeps its record where the check does not look; the check now says so and names the folder to
  put in `BFO_TRANSCRIPTS`, and the re-read check says the same instead of blaming the tool that wrote the verdicts.
  USE.md says when it is needed.
  Effect: none.
- **The first look's survey is not charged to the read check.** The services and entry points the survey lists are
  not the map's findings, so a file only the survey names no longer keeps the run from being done.
  Effect: none.
- **Your go on the alerts covers the alerts you were shown.** If they change after the review message reaches you,
  your go is not recorded until you have seen them again.
  Effect: none.
- **Once you have picked how far each stage goes, you can take a stage further but not back.** Taking a stage less
  far than already picked is refused for now, with a message saying so, and your earlier pick stands.
  Effect: none.
- **The first brief asks you one thing: which flow to start with.** It shows, rather than asks, which services it
  will read and how many independent checks read each finding; say so if you want either changed. Which stages get
  measures, alerts and runbooks you pick once the flow is mapped. The pick of how far each stage goes now also prints
  the status line for the reply.
  Effect: none.
- **The text you read when reviewing an alert is checked when it is written.** An alert's reason, the question it
  answers and the expectation it guards may not carry the kit's own words, a table or file name, or an id, as you
  would read them in the review; the check refuses the alert pages until they are reworded. The worked example's two
  reasons that did are reworded.
  Effect: fill from each row's citation: an alert whose reason names a table, a file or the register is reworded in
  plain words, from what the reason already says.

- **The code reader no longer counts the kit's own files as your application's.** Installed in the folder it reads,
  the reader would find its own test samples and count them among the application's routes and calls, overstating
  them. It now leaves its own folder out, and its counts cover only what it could place
  in one of your services, with the rest counted apart.
  Effect: none: a first look made with the kit installed in the workspace overstated its counts, and running the
  code reader again corrects them.

- **You can map a flow and stop there, or choose which stages are measured.** Mapping the flow (the case, its
  lifecycle, stages, steps, parts and the capability) is one piece of work; measuring is chosen per stage after it.
  The run stops once the flow is mapped and asks how far each stage goes: mapped only, measured, on to alerts, or on
  to runbooks (`go.py --depth`). A map-only run is done once the map is drawn, with no measure owed. A measured stage
  owes its own measures, the flow's, and those of the parts it uses; `flow_outputs.py --out <dir> --measures` writes
  its structure and measures pages alone. The questions only measuring answers (what is at stake, an expectation's
  indicator) are asked only of measured stages.
  Effect: none: a run whose person made no such choice is checked as before.

- **You can see a stage's alerts before its runbook is written.** `flow_outputs.py --out <dir> --alerts` checks only
  what the alerts rest on (the register's structure, and each alert's basis, the expectation it guards and the moves
  it counts) and writes the alert pages alone, with the runbook shown as still to come. `--out <dir> --runbooks` then
  checks the failure modes, their tests and remedies, and writes the runbook and the alert pages with their runbook
  links; it refuses while the stage has alerts and no alert page. Plain `--out` still does both at once, unchanged.
  Effect: none: plain `--out` writes the same files from the same register.
- **A run stops for your review of the alerts before it writes any runbook.** Phase 5 is now alerting (5a), your
  review, then runbooks (5b): the alerts are chosen from the health measures alone, and the ways the work can fail,
  their tests and remedies are worked out only after your go. The run record has a row for each, and the status
  line says when the run waits on your review.
  Effect: none: a register you already have keeps its run record; a new run uses the three rows.

- **The run introduces itself first.** Before it looks at anything, its first message says what it is for, how you
  will work together (six activities, where you decide, how you are kept informed) and what it needs from you to
  begin. Nothing about setup reaches you; if setup fails you get one plain sentence on why the run is blocked.
  Effect: none.
- **A first look, then a brief for someone who does not know the system, then a stop for your picks.** It reads the
  entry points, routes and documents only, and sends a brief rendered by `brief.py` from `orientation.json`: what the
  work is, what the system does and what one case is, every business flow found so far with its stages, what it
  looked at and what is open, the services and which to include, and where to start and what remains. Nothing is
  read in depth before you answer. It replaces the plan's work breakdown; `PLAN.md` now holds the brief.
  Effect: none: a register you already have keeps its `PLAN.md`.
- **Every message opens with one line saying where things stand**, made by `brief.py status` from the run's files:
  the flow, the stage, the activity, what is done, what is next, and what waits on you. **Coming back to a stopped
  run, you first get a re-entry brief** that stands on its own: what the work is, the capability, what is done and
  found, what was decided and by whom, where it stands, and what is next.
  Effect: none.
- **Your picks at the go are kept as data the run follows.** `go.py` records the flow, the services in and out,
  the stages that get alerts and runbooks, and your words, in `scope.json`, and the number of judges per row in
  `run-settings.json`. It refuses a service the survey does not have, one left unnamed, or one named both in and out.
  The done check takes the scope's stages from `scope.json` when it is there.
  Effect: none: a register with no `scope.json` is judged from its `RUN.md` Scope line, as before.
- **A call to a service you left out reads "out of scope", not "unmatched".** It is listed in
  `merge/out-of-scope-calls.csv` and drawn to the left-out service, marked out of scope; it sends nothing back to be
  re-read.
  Effect: none.
- **The done check uses the number of judges you set.** Below three, it says so beside DONE: the checks
  that catch wrong rows are built for three judges per row.
  Effect: none.

## Release 4 — 2026-10-27

### What you will notice

- **The kit runs in Claude Code.** Copy it to `~/.claude/skills/bfo-stage-kit/` for every workspace, or to
  `.claude/skills/bfo-stage-kit/` in the folder Claude Code starts in, and ask in your own words (USE.md, "What you
  need"). The done check reads Claude Code's own record of the session, so a run in another assistant never reaches
  DONE.
  Effect: none: a register you already have is judged as before.
- **The done check reads only the session records it needs, and says so.** It reads Claude Code's records for the
  folders from the register up to, not including, your home folder, never a session started in the home folder or
  above; USE.md, "What you need", says what it reads and keeps. The code reader runs Semgrep with its version check
  off, so a scan contacts nothing.
  Effect: none.
- **Every run shows you its plan and waits for your go before it reads the code in depth.** After gathering, the run
  surveys the repositories (each service's size, entry points and calls, counted by `survey.py` into `survey.csv`),
  writes `PLAN.md` in plain words (what the system is and how big, what it will read and in what order, what comes
  out, what it will take, where it stops, what it leaves out) and stops. Say go, and it goes on; your words are kept
  in `RUN.md`. `run_status.py` names any work written before the go. This holds at every size.
  Effect: none: a register you already have has no *Plan and go* section in its `RUN.md`, and is judged as before.
- **A run is done only when the code its map cites was read.** After the go, `run_status.py` takes what the run
  opened from Claude Code's own record of the session and names every cited line the run never opened with the Read
  tool. A code reader (`fact-extractor/`, rules that find routes, calls, messages and writes with file and line)
  runs with the survey; every finding in a service the map touches is cited by a row or set aside with the reason.
  Any tool whose output `fact-extractor/contract.py` accepts can replace it. Before the done check, ten rows are
  re-read against their code by an agent that wrote none of them (`reread.py`, `re-read.csv`).
  Effect: none: a register you already have has no *Plan and go* section, and is judged as before.
- **A question's "does not apply" reason names a flow it cites by the flow's name**, on a part's page and the map
  alike: "flow F3, set aside" is "flow Signing a customer in, set aside" on the example.
  Effect: none: pages only.

## Release 3 — 2026-10-15

### What you will notice

- **A stage's unfolded process steps and outcomes are boxes on the map**, as its parts are, each reached by the keyboard;
  a click on one opens its own side panel and lights its chain.
  Effect: none: pages only.
- **The side panel's trail says where the box is**, as a level page's does: "Map › Flow: name › Stage N: name", then
  the box itself as plain text. "Map" closes the panel, as Show all does.
  Effect: none: pages only.

- **The side panel closes from its heading row.** A close control (×) beside the name, and Escape, close the panel
  and clear what the map lights, as Show all does.
  Effect: none: pages only.
- **Every level page's trail says where the page is**: "Map", then each level above it by its own page's title, each
  opening that page ("Map › Flow: name › Stage N: name"), then the page itself as plain text. On a part's page the trail
  runs through the process step it was opened from.
  Effect: none: pages only.
- **The links under the side panel's title name what each opens, never the title again**: a stage's read "Process
  diagram · Alerts · Runbook"; a flow's "Value stream"; a process step's "Sequence diagram", then its stage's page and
  documents; a part's "Operations", then its stage's where it is used in one only.
  Effect: none: pages only.
- **A process step's card says "Expected outcome"**, the word every other page uses, in place of "Right outcome".
  Effect: none: pages only.
- **No line on a page talks about the screen or sends the reader elsewhere.** Gone: "Wider than the panel." under a
  side-panel drawing; "1 measured on a call below" in a sequence drawing's heads; the note on a person picked on the
  map (a person now opens no inside panel); "The card below names them." and "The run below shows..." in a part's
  key; "Each measure is listed in Measures..." under an agent's questions.
  Effect: none: pages only.
- **A link to an outcome opens its stage's page with that outcome picked**, its measures filtered as a click on its
  mark filters them (`STAGE.html#s:<id>`); on a part's page, its rows and trail link this way.
  Effect: none: pages only.
- **A sequence drawing reads with no key and every word whole.** Its frame is titled with the process step's name in words, with no "sd". On a step with moves, a recorded call no hop accounts for is listed on the card only, never drawn, and every message drawn carries the number the card lists it by, a call drawn under another as "2.1". A part's name breaks only at a space, "-", "_", "/" or "."; a name with none of these that is wider than its head widens the head, and the lifelines draw closer to keep the drawing within 1200 px. A message's words break at those or at a CamelCase hump, an identifier broken across lines starts its own line, and nothing is cut short with "…". A message's words sit along its own arrow, inside its span, and a self-message's between its lifeline and the next, so no label runs past its arrow's end across another lifeline. Each drawing's arrowheads have ids of their own, so two drawings can share a page.
  Effect: none: pages only.
- **The map's panel says a measure's state as the other pages do.** A measure that cannot be counted reads "cannot be
  counted" in its line, its row and the count of a folded group, never "proposed".
  Effect: none: pages only.
- **On a stage's page, each of its alerts links to its entry in the stage's runbook**, where that runbook is written.
  Effect: none: pages only.
- **A register's words that cite a flow by its id read the flow's name**, as a process step's id reads its label:
  "(F1 starts)" is "(Fulfilling a customer's order starts)" on the example.
  Effect: none: pages only.
- **A stage's runbook page wears the flow, stage and step pages' frame.** A trail opens the map, the flow's page and
  the stage's page; the title (and the tab) is "Stage N runbook: name", with no draft chip. "No test of this runbook is
  on record." stands under the title and at the top of every alert's entry. The landing's columns are "Its alerts",
  "The stage" and "Shared by every alert", with no question as a label. The stage is one link to its own page, in
  place of the copy of it; what is at stake for declaring an incident is in the escalation fold. "Before you start"
  is the first of the shared folds.
  Effect: none: pages only.
- **The runbook says "time limit", never "bound"**, and the alert page's "Age bound" row is "Time limit". An entry for
  a measure not emitted yet says what to do when the alert shows No data. Where a log command reads only its last
  lines (`--tail`), the entry says a line not found there rules a cause out only if those lines reach back to the
  look-back time.
  Effect: none: pages only.
- **A command pastes as it stands.** What follows "run" with a flag after it, or a shell loop kept whole, is its own
  block, with the place it runs in said before it; a SQL statement that opens a field comes after the shell it runs
  in, ends with its semicolon, and leaves its aside as a note below; a command written in parentheses inside a
  sentence is set as code in the sentence, never the sentence in a block; a count that is a description is prose.
  Effect: none: pages only.
- **A remedy that needs approval says whose:** "Needs approval from the team that owns <part> (not recorded yet)."
  No owner is drafted; owners are filled at the right time.
  Effect: none: runbook wording only.
- **FILL-STEPS: a call that both reads and writes is two interaction rows**, one per direction of data, so each
  message in the sequence drawing is labelled from its own row.
  Effect: fill from each row's citation: split any such row by what its cited lines read and write.
- **Each process step has its own page, `stage-<id>/step-<id>/STEP.html`, in the frame of the flow and stage pages.** Its trail runs system › flow › stage and its title names it ("Process step 2.2: ..."). The sequence drawing carries the measures: each part's head holds its name, its kind, the stages of the flow it serves where it serves several ("serves Stages 1–4"), and a square per measure under its layer's word; a part's measure of one operation sits under the arrow that carries that operation, and the head says how many sit on a call below; the process step's own measures are a pill beside the drawing's name. A box picked opens its measures beside the drawing, by layer and name with their state, and filters the table; nothing is open on load. The card folds, closed: trigger, what happens in each part's own words, outcomes, if it does not happen, recovery and timeouts. The measures table is the shared one, every layer the step's measures fall in, one row per square. The stage page's tasks, the map's process step rows and the side panel's head link to it.
  Effect: none: pages only; read from the rows the register already holds.
- **Each part has its own page, `part-<id>/PART.html`, in the frame of the flow, stage and process step pages,** for every part or dependency a process step relies on. Its title names it ("Part: ..." or "Agent: ..."); its trail runs system › flow › stage › the process step it was opened from, or, opened from the map, the first process step it serves. Above the drawing, every process step and outcome it takes part in, once each, by stage (and by flow where it serves several), the one it was opened from in bold. The drawing is the part form: one row per operation, the process steps that rely on it, the calls in those steps and its measures, a square per measure under its layer's word; a process step it takes part in with no operation named is a dashed row, "No operation on record"; a store or a broker, with no operation, has its process steps as its rows; the whole part's measures sit at the drawing's top right. An AI agent adds one run of the agent. The card and the measures table follow, the table in the part's own layers only (application and technology, and agentic for an agent). Each part's head on a process step's page and the side panel's head for a part on the map link to it.
  Effect: none: pages only; read from the rows the register already holds.
- **A process step's panel never squeezes its drawing.** It opens beside the drawing only where the drawing at its natural width and the panel fit the column; otherwise it opens as a sheet at the window's right edge, over the page. Picked again, or Clear filters, it closes.
  Effect: none: pages only.
- **A measures pill's squares start after its widest layer word,** so "Application" no longer runs into its first square; and a place with no measure reads "none on record" in plain words, with no dashed box (a dashed outline is the code of a measure that cannot be counted).
  Effect: none: pages only.
- **A part's card and a measure's form read truer.** A bullet that starts with an identifier ("ordering-api", "rabbitmqctl list_queues") keeps its case; "Where it sits" is left out where it would only say "a component of this system"; an agent's card lists only the agent parts found, and under Depends on only the dependencies those parts use that the list does not already name; a measure's form never prints a register id: an id in brackets is left out, an id in the words reads as that measure's name. An agent's run with no recorded order reads "One run: <name> · order not on record", an operation with no agent part reads "by no agent part found", and an operation whose agent part names the agent's own operations says which it calls.
  Effect: none: pages only.
- **Every sequence drawing fits a 1200 px column at its natural size,** its lifelines closer where it has many, and a part's name wraps whole in its head, never cut short. A call is drawn under another only where that other is the only recorded call into its sender in the step; otherwise it stands on its own.
  Effect: none: drawings only.
- **A process step's sequence drawing shows who calls whom, in the order the register gives.** The hops of the step's moves are the order. Each hop's sender is the part the register names: the clause's subject, an "X to Y" whose X is a part, a "from X" whose X is a part, the broker and the outbox store for an outbox or message hop, or the person of the hop before. A message passed through a broker is drawn into the broker and out of it, with an open arrowhead. A part's read or write to its store is drawn inside the hop. A dot with "sender not recorded" beside it is drawn only where none of these names a sender. A recorded call is labelled with its own words, never with what its receiver does in the step. Long identifiers wrap at their CamelCase humps, "/", "_" and "."; an operation name is never cut short; every text is 13 px or more. There are no coregion brackets, no orange numbers, no notes in the drawing and no key: a head says "person" or "run by someone else" where that applies.
  Effect: none: drawings only; read from the rows the register already holds.
- **Calls whose order is not recorded are said in words.** On a step with moves, a recorded call no hop accounts for is listed on the card under "Other recorded calls (order not recorded)". On a step with no move, the calls are drawn in one plain frame named "order not recorded", each call from a receiver under the call it serves. What the register does not hold is listed on the card under "Not in the map yet".
  Effect: none: drawings and cards only.
- **FILL-STEPS says `step_hint` lists only the process steps a call is made in for each case;** a call made at startup is not hinted to any process step.
  Effect: fill from each row's citation: clear step_hint on a call its citation shows is made at startup.
- **The measures table on the flow and stage pages works like a spreadsheet.** Its columns are Layer, Measure, State, On and Alert. A click on a column's name sorts by it; its ▾ opens a checklist of the column's values, with (Select all), OK and Cancel. While a filter is set, a line above the table says how many measures show, with Clear filters. In layer order a tinted band heads each layer with its question, and inside it the page's own measures come first, then each stage or process step in the drawing's order. A box or pill picked on the drawing filters the table to that place.
  Effect: none: pages only.
- **FILL-STEPS says how to read `taken_from` when a line could be read two ways:** the kind of the cited line itself; a part's own health check is the kind that runs it.
  Effect: none: wording for the next walk; a filled cell is read from the same citation.
- **A measure's state is exists, proposed or cannot be counted, and nothing more.** "exists, not watched" and the Watched line of a measure's form are gone; the register's `watched` column stays.
  Effect: none: pages only; the `watched` column stays.
- **Every page says "process step", never bare "step"**, for the business's step: labels ("Process step 2.2"), counts ("2 process steps · 4 outcomes"), the drawings' task headers and the panels. A gateway's question sits clear of the arrowhead into it.
  Effect: none: pages and labels only; no row changes.
- **The On column names the place by its short label** ("Process step 2.1", "Stage 2", "Flow"), with its full name on hover; an other outcome reads by the state it ends in and what tells it apart ("Cancelled: because payment failed"), and on the flow page each label leads with its stage ("Stage 2 · Process step 2.1"). Where a measure counts one call, the call is named in its form ("On its call").
  Effect: none: pages only.
- **A measure's opened form names the expectation it guards, and where it was taken from** (`taken_from`), where the register says.
  Effect: none: the form shows what the register already holds.
- **An alert in the measures table is "proposed".**
  Effect: none: pages only.
- **The flow and stage pages wear one frame.** A centred column with a compact head: a trail of links (system › flow › stage), then the title, which names the kind ("Flow: ...", "Stage 2: ..."); then three sections in the same order, each named by what it holds at 18 px: the drawing ("Stages, and where each is measured" on a flow, "The process of the stage, and where each step is measured" on a stage), with the square key at the end of its heading and, on a stage, the whole stage's measures as a pill beside its title, the card, which folds and opens by default ("The case, whom it serves, what it delivers"; "Expectations, entry, outcomes and alerts"), and "Measures". Their tabs are named for the page and the system.
  Effect: none: pages only.
- **A stage's runbook and alert page set code apart as the cards do.** Identifiers, routes, file names and quoted names in their text wear the code face; an alert's reason and the cases its entry works, and an entry's opening, are broken up into lines and bullets like a card's fields.
  Effect: none: pages only.
- **The measures table keeps its columns still.** Layer, State, On and Alert have set widths and Measure takes the rest; a measure's form opens in a full-width row below it, so opening one moves no column and no other row. Rows are tighter.
  Effect: none: pages only.
- **An existing dashboard or alert export can be a source.** Read it like any other source, record where it came from and when, and cite, propose or set aside each panel or alert (FILL-STEPS "When something new arrives"); `sources.csv` `repository` may name the folder an export was saved into. The `watched` column keeps its plain definition.
  Effect: none: a new kind of source you may add; no row changes.
- **Card and form text is broken up so it can be scanned.** On the step, stage and flow cards, the flow and stage pages, the part cards and the measure forms, a value's lead clause ends in a colon and each ";" item under it is its own bullet; each further sentence is its own line; a trailing "Recovery: ..." gets its own row. The ways a step fails to happen are bullets, not numbers. The words are the register's; only the layout changes.
  Effect: none: layout only; the words are the register's.
- **Code in the text is set apart.** Identifiers (in CamelCase or snake_case), routes such as `POST /api/orders`, file paths and file:line citations, and quoted names are set in a monospace face on a light tint, in light and dark. Ordinary words, product names and the names the register gives (parts, steps, the system) are never marked.
  Effect: none: pages only.
- **Cards run the full width of the page,** like the drawing and the measures table. No card text is under 13 px.
  Effect: none: pages only.
- **A lifecycle state is written as its name everywhere,** mid-sentence too: "the order in Stock confirmed", never "stock confirmed". A one-word state is read in its code form or with its capital, so "the paid order" stays an ordinary phrase, and a state quoted as a code literal ('Paid') is left as written.
  Effect: none: pages only.
- **A step's qualifier (partial, or simulated) is on no page.** The map's step boxes carry no tag and no tooltip line, the side panel and the measure rows no note; `steps.csv` `qualifier` stays in the register and `--check` still reads it.
  Effect: none: `qualifier` stays in the register and is read as before.
- **A stage's page marks its measures on its steps.** `STAGE.html` shows the whole stage's measures with the state key, then the process diagram with a pill on each step: one square per business measure counted on cases at that step, under its layer's word, or a dashed "No measure"; then the stage card and the measures. A pill picked filters the measures to that step and names it in the count line above them, with Show all.
  Effect: none: pages only.
- **Partial and stub are no longer tags on a stage's drawing.**
  Effect: none: pages only.
- **A proposed measure's square is hatched,** on the stage's page and the flow's page alike, so it no longer reads as an empty box.
  Effect: none: pages only.
- **A stage box on a flow's page opens that stage's page.**
  Effect: none: pages only.
- **An alert is drafted at whatever level the register puts it: the flow, a stage, a step or a part.** The kit no longer presumes which measures can alert. Each alert's page and runbook entry are written on every stage its measure reaches: a step's stage, every stage of its flow, each stage a part serves (from `participation.csv`, narrowed by `operation` where it is set). Where a stage holds an alert off its own level, the alert page says where each is placed and every stage and step it reaches. The checks that an alert has a basis and names the expectation it guards apply to every drafted alert, at any level.
  Effect: none: the outputs are written again from the rows as they are; what an alert owes for the expectation it guards is in the expectations entries under "Changed in the register".
- **A stage with no alert gets no alert page, and its runbook says no alert is proposed for it.** `flow_outputs.py --check` used to fail a stage with no alert, and an alert that was not a stage's count of cases; both are now notes (`note:` in its output, rows fo-62 and fo-63 of `CHECKS.md`), and neither stops the outputs being written. An alert page left by an earlier run is removed, so the map links none that is not there.
  Effect: none: a check failure became a note.
- **FILL-STEPS puts expectations before alerts, and its alert wording is guidance, not a rule.** Step 3a: usually write each expectation from what a party is told or a source states, before any alert is drafted. Step 9: usually give each expectation a business health and a business impact measure, or a gap; draft alerts as proposals that name the expectation they guard, and leave whether to alert, and on what, to the team.
  Effect: none: wording for the next walk; what an earlier register lacks here is in the expectations entries under "Changed in the register".
- **A step's sequence diagram draws its arrowheads in the page's ink again**, not black.
  Effect: none: pages only.
- **A flow opens its own page.** Each flow has `flow-<id>/FLOW.html` beside the map: its value stream (the stages left to right, each stage's other ways out leaving at that stage), a "Measured here" lane under each stage and under the end with one square per business measure counted on cases, by layer and state (exists, proposed, cannot be counted), then the flow's card, then its measures. A lane box picked shows only that place's measures. The flow's line in the side panel links it as "Value stream and measures", and the page's trail goes back to the map with the flow selected.
  Effect: none: pages only.
- **A step the reference model adds and nothing carries is counted the same way by the check and the view questions.** Its moves read as does not apply, instead of empty.
  Effect: none: the check and the view questions now agree; no row changes.
- **A finding in a register adds no check.** REGISTER.md says so, in "What a finding in a register changes": a finding adds a declaration the definition was missing, or it becomes FILL-STEPS wording and review. The list of checks grows only when the definition grows.
  Effect: none: no check is added.
- **Every check the kit runs is listed in `CHECKS.md`,** one row each: where it sits, its severity, its class (structure, integrity, coverage or residue), the lead words of its message, and what it guards.
  Effect: none: a list of the checks; nothing new is checked.
- **The check accepts the `step: moves` gap that `run_status.py` accepts.** A step with no move passes the check only where no part carries it: a step the reference model adds, or one whose `step: moves` gap of kind `no record` cites the code read, judged as `run_status.py` judges it. The check used to refuse that gap, and to pass a reference-model step a part carries.
  Effect: none: the check accepts more, never less.
- **The check warns on a value outside a column's declared list.** REGISTER.md declares the allowed values of `band`, `from_kind`, `path`, `form` and `receipt_question` with a `One of:` list ending each description, and `capability_views.py --check` warns on any other value; a blank cell passes, and each value of a `;` list is checked. They are warnings for now, so a register already in use does not fail on them.
  Effect: none: warnings only, so a register in use does not fail on them.
- **A stage's process diagram is its own page.** Each stage folder holds `STAGE.html` beside its runbook and alert page, with the diagram at its own size; the stage line in the side panel links it as "Process diagram". The side panel keeps its reading width, so the map stays in view with the stage lit, and the page's trail (flow › stage) goes back to the map with that stage selected.
  Effect: none: pages only.
- **FILL-STEPS Step 4 says a stage's steps are written in the order they run.** The stage drawing chains software-only work in that order where the lifecycle does not.
  Effect: none: wording for the next walk; steps in an earlier order still draw.
- **Two instructions tightened in FILL-STEPS.** An impact measure that guards an expectation counts only the cases that fail its `satisfied_when` (Step 9); `satisfied_when` holds the condition only, and what the code cannot show goes in a `no record` gap row (Step 3a).
  Effect: none: wording for the next walk; `satisfied_when` is in `expectations.csv`, which is new in this release.
- **The check warns when a step needs a dependency nothing calls on that step.** The step's lifecycle names it in `needs`, but no interaction listing that step reaches it, so the map would draw no caller.
  Effect: none: a warning only.
- **Every page reads as one product.** The map, a stage's runbook and alert page, how the map was made and inside each part share the map screen's colours, in light and dark, and its sans type; no word is under 13 px.
  Effect: none: pages only.
- **A stage's drawing fits a 1200 px column at its own size, with no text under 13 px.** The stages before and after sit in a strip above the stage; inside it, the work (up to three steps a row), then the decision across the stage, its chain breaking onto a second line where it would not fit, then the event sub-processes side by side.
  Effect: none: pages only.
- **The map starts at the flow.** Five columns, from intended flow to external dependency; capabilities are no longer drawn on the map, and each flow's card still names the capabilities it delivers.
  Effect: none: pages only.
- **A stage's key is drawn under the figure, open, and only for marks the drawing cannot label.** A message says whom it is from, a timer its duration, the ~ box who does the work, the error boundary what happens; the key under the figure keeps only what is left (a plain start or end, a folded stage, a partial or stub tag), each a mark and a few words. The folded "Key to the drawing" list under a stage, with its line weights and white boxes, is gone.
  Effect: none: pages only.
- **A stage's drawing says who starts what can happen at any time, and draws the customer only where a message comes from them.** The box's title says what starts it: a message from whom, after how long, or a condition and whether the software checks it. The customer's band across the top is drawn only where a message comes down from it, which needs the move's new `started_by` to name the customer. Where it is blank and the move is first carried by a front end or an app, the box reads "a request from someone using the web front end" (the kind of part, never its name), with no customer drawn; where nothing says, it reads "on a condition; who starts it is not recorded".
  Effect: none: pages only.
- **A stage's drawing says only what is there.** The line under its title about what is drawn elsewhere is gone. The decision no longer opens with a "Decide which way out" step that repeats its box's name: its start runs to the first gateway, whose question says who decides ("Which way out? Decided by the underwriter, on an AI agent's proposal", or "Decided by the software"). A state is spelled one way: in sentence case where it starts a label ("Cancelled: payment failed"), in lower case inside one ("In stock confirmed: which way out?"), however the register's prose writes it.
  Effect: none: pages only.
- **A stage's neighbours are the stages before and after it in stages.csv.** The folded stage above-left is the one before it in order, never every stage a move comes from. Where the register records no lifecycle moves for a stage, the stage after it in order is drawn, the drawing says its ways out are not recorded, and no end is drawn, so the stage no longer reads as the whole flow.
  Effect: none: pages only.
- **The ~ (ad-hoc) mark only where a person does the work.** A stage's work is drawn with ~ only where a business role performs one of its steps, and its box is titled with that role. Work the software does alone is a plain box whose steps follow one another, in the order the lifecycle chains them or else the order of steps.csv; a single step is drawn as a bare step.
  Effect: none: pages only.
- **A stage's drawing reads at one type scale and never cuts its words short.** Labels and tags are 13 px, a step's name 14.5, a box's title 15.5 and the stage's title 20, all in one sans face. A box grows to hold its words; nothing ends in "…", so a step's header keeps who does it whole.
  Effect: none: pages only.
- **A stage's folded steps count its outcomes apart.** The map reads "2 steps · 4 outcomes", not "6 steps", and the line under the title counts process steps without the endings.
  Effect: none: pages only.
- **The runbook and alert pages say each thing once, name states as the cards do, and number a remedy by its
  register id.** Moves that share an outcome no longer print "Cannot be undone: ..." once per move; every list on the
  two pages prints a line once. A state reads as words wherever the pages print it ("Awaiting validation", not
  "AwaitingValidation"), with the same function the cards use; a status quoted as the database holds it stays as
  written. A remedy keeps one number on every page: RM6 is "Remedy 6" on its card and "Restore: remedy 6" on a
  check, never "Action 6" in one stage and "Action 2" in another. Register text can now write "remedy 4" and it links
  to that remedy's card; text from earlier releases that says "restore action 4" now means remedy 4 (RM4), is
  linked the same way, and reads "remedy 4".
  Effect: none: pages only.
- **The map is the new map screen.** Six columns, from capability to external dependency, with a capability's
  flows beside it. Each stage's steps fold to a count that opens in place, and with them the parts that carry those
  steps and the external dependencies those parts call, on the stage's row and joined along the chain. Pointing at a
  box lights its chain and fades the rest; clicking it opens its page in the panel beside the map, which stays closed
  until then. Nothing on the screen is smaller than 13 px at Fit, nothing is faded on load, and the instruction lines
  are gone. Parts no step's chain reaches are named in one line under the map.
  Effect: none: pages only.
- **The flow and stage cards read right on any register.** A value written "proposed: ..." keeps its words and shows
  "(proposed)" after them, where the cards used to print only "proposed". State names read as words whatever the
  code's style: "StockConfirmed" reads "stock confirmed", "in_review" reads "in review". Where no lifecycle move says
  how a case enters a stage, "A case enters" gives the stage's own entry instead of "not in the map yet". "At stake"
  no longer repeats every case attribute's stake under every stage: the register does not say which stage each
  attribute matters in, so the card says so in one line and names the flow's attributes.
  Effect: none: pages only.
- **An application with no AI agent says the agentic layer does not apply.** Every Measures panel used to show
  "Agentic: No measure on record" even where the register names no AI agent, which reads as something missing. It
  now reads once: "Does not apply: no AI agent in this flow." A gap the register records there still shows instead.
  Effect: none: pages only.
- **No stage the register gives a flow is dropped.** A stage whose every step is drafted from a reference model and
  carried by nothing used to vanish, with its measures, and the header counted fewer stages than the register holds.
  It is now drawn with those steps marked not assessed. A lone step of that kind in a stage with other steps is still
  left out, and listed under "Not drawn".
  Effect: none: pages only.
- **The Glossary's State and Status examples come from the register.** State shows a state the case's lifecycle
  names, an unrecorded one where there is one, and Status a state a system records. A register with no lifecycle
  table says "none in the register".
  Effect: none: pages only.
- **The Operation example finds tools in any naming style.** A tool is an AI agent's operation that is one name,
  in camelCase or snake_case alike; with no agent, the example gives a handler instead. A page or a path is never
  given as a tool.
  Effect: none: pages only.
- **An operation serving several flows names each flow.** Inside this part read "Stages 1 to 1" where an
  operation served the first stage of two flows. It now reads each flow by name with its stages, as "Fulfilling a
  customer's order: Stage 1; Filling a basket: Stage 1".
  Effect: none: pages only.
- **Who makes a move is whoever the code lets make it.** The fill steps record a person's move as made by a named
  role where a guard names roles, by "anyone signed in" where the guard asks only for a sign-in, and by "anyone, the
  code checks no identity" where there is no guard, each cited to the guard or to its absence. Where a guard names
  roles but nothing records who holds them or which of them made the move, the step's trigger reads "No record to
  count" instead of a blank.
  Effect: none: wording for the next walk; an earlier row still draws.
- **"ok" never means out of date.** Each runbook, alert and structure file a stage run writes now records which
  version of the register it was made from. If the register changes afterwards, `run_status.py` marks the file STALE,
  names the tables that changed and gives the command that writes it again, and the run is not done. A file made by
  an earlier release has no such record, so it reads as stale until you generate it again.
  Effect: none: generate each stage folder again, as `run_status.py` names them; no row changes.
- **`reconcile.py --migrate` says what it leaves for you.** At the end it lists the stage folders to generate again
  (it never does that itself) and, for each table, the columns this release defines that the register still lacks.
  Fill each as its column's entry under "Changed in the register" says in its effect line (`taken_from`: from each
  row's citation, with nothing walked again); never add them blank. The list and the check's message carry that
  effect beside the column.
  Effect: none: it reports; it changes no row.
- **An old "promise" no longer shows as the time limit in the code unless the code is cited.** `--migrate` keeps an
  earlier `promise` in `bound_in_code` only where the cell or the row's source cites a file and line. Any other is a
  stated bound: it goes to `expectations.csv` as the objective of its stage or flow, party "not stated", and the
  migration names each one moved. The check now fails a filled `bound_in_code` that cites no code.
  Effect: rename: reconcile.py --migrate; it moves each `promise`, then fill from each row's citation for any uncited
  value it sends to `expectations.csv`.
- **One test for component, and the example says "time limit".** The vocabulary and the register template now give
  the same test as the fill steps: a component is any deployable the flow runs through whose code can be had, whoever
  owns it. The application layer counts operation completions, not step completions. The eShop example no longer
  says "promise": it reads "time limit" where the code sets one, and the customer's expected time where it does not.
  Effect: none: the test is the one FILL-STEPS already gave; only the vocabulary and the template now say it too.
- **The Glossary reads as a thesaurus.** Its first column is "Term", and a new "Related terms" column gives each
  entry's synonyms (UF), broader and narrower terms (BT, NT) and related terms (RT), the same from both ends. New
  entries: State and Status (where a case stands, and the value a system records for it; neither is a stage).
  Component is narrower than Part, and is now any deployable whose code can be had; an external dependency is one
  whose code cannot. Operation is a tool, route or handler a component offers, and Action an act inside an AI
  agent's run. A column name's hover shows the related terms too.
  Effect: none: pages only.
- **The cards say who the flow serves and what each party expects.** The flow card's "Serves" lists the customer
  first, then each other party with what it expects of the whole flow. The stage card gives one line per party: what
  it expects of the stage, what one case shows when that is met, and the objective someone stated, with where it was
  stated, or "not stated". Where a stated objective differs from the code's time limit, the card shows both as a
  finding, and does not pick one. A register with no expectations says "No expectations recorded".
  Effect: none: drawn from `expectations.csv` where it exists; what that needs is in the entries under "Changed in the register".
- **The time limit in the code is optional.** Few applications set their own timer, deadline or overdue rule, so
  `bound_in_code` is filled only where the code sets one, and the pages show it only there; an empty cell shows
  nothing and owes no gap or question. The parties' expectations are each stage's main content.
  Effect: none: the column is optional, and an empty cell owes nothing.
- **An AI agent's run is drawn as a UML activity diagram.** Inside this part shows the run with a start node, its
  actions, an end node, and the moves between them: a diamond where the run chooses its next move, a
  diamond where moves join, and a line back up where it repeats. A move is drawn only where the register records
  it; where it does not, the drawing says so in plain words. The agent's measures are no longer listed inside the
  part: they are in its Measures, with the measures of the calls it makes, and the part keeps the questions asked of
  an agent and how each is settled.
  Effect: none: drawn from what the register records; `next` is optional.
- **The agent's run and its questions read more plainly.** Each condition in the run's diagram sits on its own move
  where the move leaves the decision; moves that skip ahead run on the left and moves back up on the right, each on
  its own line. A run whose order the register does not record is listed, not drawn, with that line first. The
  table of questions asked of an agent says, per question, how many of its measures answer it, or "No measure on
  record", or the gap the register records. The Glossary says what UF, BT, NT and RT mean, a column name's hover
  spells them out, and "Operation" has an example from the register.
  Effect: none: pages only.
- **A stage is drawn as a business process (BPMN).** Clicking a stage now opens a BPMN sub-process of its flow in
  place of the state machine. The flow is the pool, and the customer is a closed pool above it. The stages before and
  after the stage are drawn folded. Inside the stage:
  - the steps that leave the case in the stage form "Work the case", with no required order. Where the register
    orders two of them, an arrow joins them;
  - the ways out are decided in "Decide the way out". Each ends in an event named by the state the case is left in,
    with "cannot be undone" where the move cannot be undone. Where a decided move can leave the case stranded, a
    boundary event leads back to the work;
  - moves any of several roles can make, or that leave from every state of the stage, are event sub-processes
    ("At any time"), each started as its lifecycle row says (below);
  - the time limit in the code is a timer that stops nothing, and is drawn only where the code sets one.

  A gateway after the stage routes on how it ended. Each step's box says who does it. The parts and any AI agent are
  left to the step's sequence diagram. The key lists only the marks drawn.
  Effect: none: pages only.
- **How an "at any time" move starts is read from its lifecycle row.**
  - A move that travels by a person, or whose `carried_by` names a person or a role, starts as a message from
    those people. The box title names them. Where the person is the flow's customer, a dashed line comes down from
    the customer's band.
  - A move that travels by a timer starts with a timer.
  - Any other move starts on a condition. That is what the register records when it names no party.
  Effect: none: drawn from each lifecycle row as it is; `started_by` is optional.
- **A stage's decision follows the order the register gives it.** When a stage's ways out leave from more than one of
  its states, and the lifecycle chains those states, the decision has a gateway at each state, in that order. The
  step that moves the case on sits between them. In the eShop example, the order's stock is confirmed or it is
  cancelled; then payment is taken or it is cancelled. A single gateway is drawn only when every way out leaves from
  the same state. Where two branches would read the same, each adds what its step's name says that the other's does
  not, for example "cancelled: an item is out of stock" and "cancelled: payment failed".
  Effect: none: pages only.
- **The stage card says each thing once.** An outcome reached by several moves is listed once, and no line on the
  card prints a move id.
  Effect: none: pages only.
- **A sentence a move id is taken out of still reads.** An id set off between commas goes with both commas, and a
  comparison with a move ("unlike" and the id) goes with its comma, so no stray comma is left behind.
  Effect: none: pages only.
- **A word that starts with a dot keeps the space before it.** Taking a citation out of the runbook and alert text no
  longer joins ".NET" to the word before it.
  Effect: none: pages only.
- **An alert's reason ends cleanly.** On the alerts page, no period is printed after the reason's last paragraph; in
  the runbook, the "expectation it guards" line ends with a period.
  Effect: none: pages only.
- **A check reached from more than one test links back to each.** Where several tests in an alert's entry send the
  responder to the same check, the check's card has a "Back to" link to every one of them, not only the first.
  Effect: none: pages only.
- **Each timing the design assumes names its process step.** The alert page's Window row, and the runbook's "Was it
  planned?" check, lead each timing with the process step it belongs to, so a reader can tell which wait is whose.
  Effect: none: pages only.
- **A check on several parts asks of them all.** "Are Ordering database and Catalog database down or unreachable?",
  "… falling behind on their queues?": a check that names more than one part reads in the plural, in its card, its
  line in an entry and the escalation table.
  Effect: none: pages only.
- **The alert page has the runbook page's trail.** Its trail opens the map, the flow, the stage and the runbook.
  Effect: none: pages only.

### Changed in the register

- **measures.csv has a required `taken_from` column**, filled on every measure: the kind of record a measure is counted from, one of eleven (`metric`, `log or event record`, `trace`, `the edge`, `external probe`, `client-side instrumentation`, `the case's own record`, `a message log kept with the state`, `configuration`, `platform lifecycle events`, `another organisation's record`). Where `exists` is `yes`, the kind of the cited line; on a proposed measure, where it would be taken from. `--check` fails a register without the column and warns on any other value.
  Effect: fill from each row's citation: the kind of the line `source_ref` cites, or on a proposed measure the kind it would be taken from; nothing is walked again.
- **lifecycle.csv has an optional `started_by` column**, beside `carried_by`: on a move that can happen at any time while the case is in a stage (a cancel, a withdrawal), who starts it, cited: the flow's customer, a role, an outside party, `timer` or `the software`. Fill it where you know; `reconcile.py --migrate` adds it empty to an earlier register.
  Effect: none: optional; `reconcile.py --migrate` adds it empty, and you fill it where you know.
- **An agent's run is made of actions, and its run question is "operating health", so "operation" means only a tool
  or route a part offers.** `agent-system.csv` → `element` value `operation` is now `action`: one act inside an AI
  agent's run (a model call, a call to a tool, a check), as in a UML activity; Inside this part and the Glossary say
  "action", and the Glossary's "Operation" is what a part offers. `measures.csv` → `agent_question` value
  `operations` is now `operating health` ("Operating health: how did its runs go?"). Run `python reconcile.py
  --migrate <register>` on a copy of an earlier register to rename both; without it, the check names each old value
  and its new one. Prose in the register (a measure's question, a note) is never rewritten.
  Effect: rename: reconcile.py --migrate; on a copy, and no row's content changes.
- Two columns are renamed: `flows.csv` → `expectation_of` is now `customer` (the role name only; its citation goes in
  the row's `source`), and `flows.csv` and `stages.csv` → `promise` is now `bound_in_code`, shown as "Time limit in
  the code". The receipt questions `the promise` and `past the promise` are now `the time limit` and `past the time
  limit`. An earlier register needs nothing: `reconcile.py` reads it under the new names when it compares it with
  the new one. To draw an earlier register with this kit, run `python reconcile.py --migrate <register>` on a copy
  of it: that renames the columns and those question cells in place and moves a code citation out of `customer` into
  `source`. Without it, the check fails that register with a missing-column error.
  Effect: rename: reconcile.py --migrate; on a copy, and no row's content changes.
- Remedy ids are renamed from `R1`, `R2`, ... to `RM1`, `RM2`, ..., so a remedy no longer reads like an interaction
  (`R01` in `subjects.csv`, unchanged). What an earlier register needs: run `python reconcile.py --migrate
  <register>` on a copy of it. That renames each id in `remedies.csv`, the `remedy` column of `failure-modes.csv`,
  and each remedy one remedy's `action`, `expected` or `if_different` names. Without it, `flow_outputs.py --check`
  fails the register with an error naming the old ids.
  Effect: rename: reconcile.py --migrate; on a copy, and no row's content changes.
- A new table, `expectations.csv`, names whom the flow serves and what each party counts on, of the whole flow and
  of each stage: the party, the expectation in their words, what one case shows when it is met, and an objective
  only where a document, a person or the text the business shows the party states one. The new Step 3a in
  FILL-STEPS says how to fill it. A time limit a source states now goes there as an objective; `bound_in_code`
  holds only the code's own time limit, and where the two disagree the stage card shows both.
  Effect: re-walk Step 3a, the parties and their expectations, because what a party is told or a source states is cited by no row of an earlier register.
- `measures.csv` has a new column, `expectation`: the ids of the expectations a measure is evidence of. Every
  measure you propose for alerting names the expectation it guards there. A business health or business impact
  measure that names an expectation shows whether it is met; an expectation no measure names gets a gap row.
  Effect: re-walk Step 3a, the parties and their expectations first, because the ids this column names come from `expectations.csv`; each alerting measure then names the one it guards.
- What an earlier register needs: add `expectations.csv` from the template and write the parties and their
  expectations into it (Step 3a), add the `expectation` column to `measures.csv`, and put the id of the expectation
  each alert guards on every measure proposed for alerting. Until then the check fails every alerting measure.
  Effect: re-walk Step 3a, the parties and their expectations, because no row of an earlier register holds them.
- A run now fills who each flow serves and what each party expects: a new `expectations.csv` with at least one row
  for the whole flow and one for every stage, each with what one case shows when it is met, and a measure that shows
  it (or a gap row saying why there is none). A run is not DONE while any of these is empty. An earlier register's
  alerting measures fail the check until their new `expectation` column names the expectation each one guards.
  Effect: re-walk Step 3a, the parties and their expectations, because a run is not done without them and no row of an earlier register holds them.
- `agent-system.csv` gains an optional `next` column: the run's control flow, read from the code that sequences it. On
  the run row, the operation a run starts with; on an operation row, the operations that may follow, or `end`, each
  with an optional condition in square brackets. An earlier register needs nothing: the column may be absent or
  blank, and the run is drawn without moves until it is filled.
  Effect: none: optional; the run is drawn without moves until it is filled.

## Release 2 — 2026-10-14 (afternoon)

### What you will notice

- **An earlier register is checked, never trusted.** Point the kit at a workspace where an earlier run left a
  register, and it leaves that register exactly as it is and walks the code afresh into a new folder. Then a script
  compares the two row by row: what the earlier one has is kept only if the code, the document or the person it
  cites supports it, and the report lists what was added, carried forward, not supported, not assessed, and where
  the two disagree. **In this release the comparison only reports: nothing from the earlier register is added to the
  new one.** Rows whose cited code line still exists are headed *Unchecked: not added*, because a line existing does
  not show it supports the row; a person reads them. Adding checked rows comes in the next release. A new register is only ever started in an empty folder; the starting script refuses to copy
  over existing files. This replaces the in-place upgrade prompt that USE.md used to give.

- **The run checks it has every repository.** In Phase 0 it searches your code host, with your own access, for
  the repository behind every reference the code makes that the workspace doesn't answer, and for repositories
  that call or deploy this flow's services, and repeats until nothing new turns up. Each one found is recorded
  with the search that found it and added to the workspace; `RUN.md` answers "Is this the complete set of
  repositories?".
- **The run follows a workflow and keeps a record.** Before it does anything, the assistant writes `RUN.md` in the
  register folder. It restates what the run will produce, phase by phase, and then marks each phase to do, doing,
  done or blocked. A new chat reads `RUN.md` first and carries on from where the run stopped. If something stops a
  phase, such as Python not being available, the phase is marked blocked and the reason is given. Nothing is skipped
  without saying so.
- **Done is checked, not claimed.** `run_status.py` lists every file the run should have produced, the HTML pages
  included, and prints DONE or NOT DONE. The final report pastes its output, so a run that stopped before drawing the
  map can't report success.
- **Fullness counts.** Under DONE / NOT DONE, `run_status.py` prints how full the register is: steps and measures
  per stage, the share of elements left as gaps (split by kind), steps with an operation named, parts with an inside
  view, and tests per alert.
- **Gathering sources (Phase 0).** Name in your request what the run should read: repositories, pages, diagrams,
  process descriptions, notes. The assistant gets them with its own tools and lists each in `sources.csv` with the
  step that uses it. When the code calls a service whose code isn't in the workspace, the assistant fetches it, but
  only with access you already have, and read-only. It never requests access, never enters credentials, and never
  changes anything at the source. Every fetched source is recorded with what referenced it. To keep the run to
  exactly what you named, say "use only the sources I name".
- **What would make this map fuller.** The final report ends with the services the map stops at, and the guesses
  (`proposed:`) grouped by the kind of source that would settle them.
- **A component is any service the flow runs through whose code can be had**, whatever application or team it
  belongs to. An external dependency is one whose code can't be had, such as a vendor or a service you have no access
  to. Inside a component, the run reads only the operations this flow calls and what they call.
- **The worked example is full.** The eShop example now covers all four stages, with operations, inside views,
  measures on every stage, and runbook entries kept short. It is the shape to follow.
- **The page.**
  - The map fills the window, and you can collapse it again.
  - Drawings in the side panel are at reading size.
  - Measures are grouped by layer.
  - Where nothing is measured, the panel says why: "Does not apply", "Counted by …", "No record to count" or "Not
    assessed".
- **Runbooks at scale.** Tests that check the same thing are grouped, shared parts are checked first, and the
  runbook author can set the order of tests. The "is it up" checks always come first.
- **Every stage.** Running the kit for a later stage updates and rechecks every stage already done.
- **A run can't report DONE on a thin map.** Each view has a fixed set of questions it must answer: for a step, which
  moves make it up, what starts it, what happens if it doesn't, and how long it is allowed; for a part, what it is for,
  its operations and what it depends on; for a stage, its promise, how a case enters, its outcomes and what can't be
  undone; for the flow, what one case is, when it starts and ends, and who expects what. `run_status.py` counts each
  question as answered, gapped or empty, and prints NOT DONE, naming each question, while a required one is empty.
  On a first run, a question left as "not read" doesn't count either.
- **An empty answer has to say why.** Where the code doesn't hold an answer, the run writes a gap row with its kind
  (does not apply, counted by, no record), and the views show the reason instead of "not in the map yet".
- **Owner and responder are counted, never required.** They are filled when known.
- **"Inside this part" says what each part is for**, from the code.
- **Repositories are opened as folders of your workspace, and the run uses your environment's code tools.** Every
  repository, including ones the run fetches, must be a folder of the open workspace; if the run can't add them, it
  stops, names them and asks you to open them as one multi-root workspace. It then uses whatever code-intelligence
  tools are on offer (call graph, cross-repository trace, failure-handling and unreferenced-code analysis) as sources.

### Changed in the register

- `participation.csv` → `way` is no longer read: the step drawing ignores it, and the check warns while the column is
  there. Remove it.
- `capability_views.py --check` compares every table's columns with `register-template/REGISTER.md`. A table that
  lacks a column defined there is an error, one per table naming each missing column, unless the column's
  description begins *Optional*; a column defined nowhere there is a warning, since nothing reads it. A retired
  column (`way`, `delivering_application`, `step-impact.csv` → `cause`) keeps its own warning. A missing table file
  is not checked. The template's headers are tested against the same definition, so the two can't drift.

The check names each change. A run that finds an earlier register leaves it untouched and starts a new one (see
"Retired" below).

- The check now refuses a `subjects.csv` with no `repository` column, and a component with `repository` blank;
  only a `technology` component whose `source` says no repository defines it may stay blank.
- `sources.csv` gains `repository` (the workspace folder a code source is) and `commit`. Every citation starts
  with a repository listed there. `subjects.csv` → `repository` (since release 1) is filled for every component,
  from its build or deployment definition.
- `measures.csv` gains `counted_moves`. On an alert of cases leaving a stage, it lists the moves the alert counts.
- `measure-gaps.csv` gains `kind`: `does not apply`, `counted by`, `no record` or `not read`.
- `failure-modes.csv` gains an optional `order`.
- `about.csv` loses `delivering_application`.
- `subjects.csv` has a new column, `purpose`: what the part does in this flow, in one sentence, cited. The check fails
  without it.
- `measure-gaps.csv` accepts gaps on view questions, with the `question` values FILL-STEPS lists (for example
  `step: trigger`, `part: operations`). A step no part carries may gap its moves as `no record`, saying where it was
  looked for.
- `lifecycle.csv`: every hop in `travels_by` has a description (what starts the step is read from the first one), and
  `irreversible` is `yes` or `no`, never blank.
- A register from an earlier release fails DONE until these are filled. KNOWN-GAPS says how.

### Fixed

- **The comparison with an earlier register reads it the way it was written.** A part named `Name (repository)`
  matches `Name`. A citation into a copy of a repository outside the workspace is checked in that repository. An
  `asked:` answer covers only its own field and is printed with its value. A document named in a field is re-opened
  at the section it names. Each row's claim is printed beside its cited lines, with a verdict and reason left blank
  for the assistant to fill in.
- The copy-and-paste prompt in USE.md now runs the whole workflow, so it draws the map. Before, it stopped after the
  stage files.
- An alert proposed on a measure the code doesn't emit yet now says it fires on "No data" until the measure exists.
- An alert's counted moves come from their own column, never from its written explanation.

### Retired: upgrading an earlier register in place

Until this release, USE.md gave a prompt that upgraded an earlier register in place, and KNOWN-GAPS.md carried these
notes for it. An upgraded row looks verified and is not, so the route is retired; an earlier register is now
reconciled against the code instead. The notes, as they stood:

- A register filled with an earlier version of this kit names the alerting column of `measures.csv` `pages`.
  Rename it to `alert`; until then no measure is proposed for alerting and no alert or runbook is written.
- A register filled with an earlier version of this kit fails `--check` until it has rows for the two newest
  failure modes, `call: callee answers wrongly` and `needs: answers stale or wrong`, and no alert or runbook is
  written until then. Add the rows; a `call` row names the part that is called, the callee whose answer the move
  waits on, one row per callee where a move makes several calls (a `not possible here:` row with its reason is enough where the mode cannot
  cause what the stage's alerts count), and state the basis of each measure proposed for alerting as `yes:` and the reason.
- A register filled with an earlier version of this kit fails `--check` until its measure step's receipt is
  complete: every element FILL-STEPS Step 9 accounts for (the flow and each stage at business health, each step
  that matters asked both questions, each operation, each system component, each agent's decision points) is
  covered by a candidate in `measures.csv` or has a row in `measure-gaps.csv` saying why not (an earlier register
  has no `measure-gaps.csv`: copy it from `register-template/` first). That is intended:
  the failure lists the elements nobody had looked at. Mark the existing step measures in `receipt_question` and the
  operations they count in `operation` first; many elements are already covered.
- A register filled with an earlier version of this kit has no `receipt_question` column: add it, empty `defect` and `operation` columns to `measures.csv` and a `decision_point` column to
  `participation.csv`. It then fails `--check` until each stage's four candidates are marked or gapped (`in the
  stage`, `oldest's age`, `time through`, `past the promise`),
  each agent row is classed `yes:` or `no:` in `decision_point`, and each agent's five run metrics are covered or
  gapped. Defect prose in `source_ref` moves to `defect`. Add a `reply_decision_point` column to
  `participation.csv` too: the check then fails until each agent row's reply is classed `yes:` or `no:`.
- A register filled with an earlier version of this kit names the acts inside an agent's run `step` and its pieces `part` in
  `agent-system.csv`'s `element` column: rename `step` to `operation` and `part` to `agent part`. The check fails on
  the old values.
- A register filled with an earlier version of this kit may name a runbook section (`§2`) in a remedy's `action`,
  `expected` or `if_different` in `remedies.csv`. The check fails on it: write
  the action itself (`Escalate`, `Roll back`) in its place, and the runbook points it at its section. A remedy that
  names a measure proposed for alerting (`M13`) fails the same way: write the action, not the measure.
- A register filled with an earlier version of this kit has no `operation` column in `participation.csv`. The column
  is optional: without it the receipt asks no question of any operation, and the check passes. To have each operation
  asked, add the column and fill each row from the code with the route, tool or handler that performs the step; then
  name in `measures.csv` `operation` the operations each measure counts.
- A register filled with an earlier version of this kit has no `counted_moves` column in `measures.csv`; the
  moves an alert counted were read from its basis. Add the column after `alert` and, for each alert of cases
  leaving the stage, fill it from the moves its basis says it counts, by id and `;` separated, as a person reads the
  basis (a move it names only to say it is not counted stays out). `--check` fails, and lists every alert that needs
  it, until each is filled. An alert of cases waiting leaves it blank.
- A register filled with an earlier version of this kit has a `delivering_application` column in `about.csv`, and
  may list as an external dependency a service the flow runs through only because another application owns it. The
  check warns on the column: remove it, since a component is now any deployable the flow runs through whose code
  the run can get (FILL-STEPS Step 5). For each external dependency whose code can be reached, get its repository,
  list it in `sources.csv`, and map it as a component, reading the operations this flow calls and what those call.
- A register filled with an earlier version of this kit has a `way` column in `participation.csv`. Nothing
  reads it any more, and the step drawing is the same with it or without it. The check warns on the column: remove it.
- A register filled with an earlier version of this kit may lack newer optional columns: `watched`,
  `watched_source` and `order` in `measures.csv`, `also_escalate_to` in `remedies.csv`, `decision_point` in
  `agent-system.csv`. Add each from `register-template/`; they may stay empty, and fill them from the code where
  it says.
- A register filled with an earlier version of this kit has no `kind` column in `measure-gaps.csv`, and
  `--check` fails until each row has one. Add the column after `question` and fill it on every gap row by reading
  its reason, as a person would: `does not apply` (ruled out by design), `counted by` (folded into another measure,
  whose id the reason names), `no record` (the code keeps nothing that could count it), or `not read` (not assessed
  in this run). `--check` lists every row that needs it; a row left blank or with any other value fails the same way.
- A register filled with an earlier version of this kit is NOT DONE until each field a view requires is answered
  or gapped (FILL-STEPS marks each one required at the step that writes it): a trigger in every hop's body, timing,
  `if_not`, `irreversible` as `yes` or `no`, each part's operations and dependencies, and the stage and flow
  fields. `run_status.py` names each empty one by element. Add a `purpose` column to `subjects.csv` after `name` and
  fill it for each component and external dependency from the code: what the part does in this flow, in one
  sentence, cited. `--check` fails until the column exists and every such row has one.
- A register filled with an earlier version of this kit may have no `repository` column in `subjects.csv`, with each
  component's repository written inside `name`, in parentheses. `--check` fails until the column exists and every
  component has one. Add the column after `application_id`, as in the template; move each repository out of `name`
  into it, so `name` is the plain name; and fill it for every component from its build or deployment definition, or
  `not built here:` and the image for one run from someone else's image. Shared infrastructure a parent component's
  deployment provisions (a database, a cache, a broker) takes the repository that defines it, with the path to the
  definition (`repo: path`). A row not separately built, such as an in-process sub-agent, is not a component: remove
  it and describe it in `agent-system.csv` inside its parent component's run. A `technology` component no repository
  defines stays blank, and its `source` says so and where it was looked for.
- A register filled with an earlier version of this kit may lack columns the tables now define, in any table, and
  `--check` fails with one error per table naming them. Add each missing column from the matching file in
  `register-template/`, in its place, and fill it as FILL-STEPS says at the step that writes it; a blank cell reads as
  not assessed. A column whose description in `register-template/REGISTER.md` begins *Optional* may stay out. Remove
  a column `--check` warns is defined nowhere, or move what it holds into the column it belongs in.

## Release 1 — 2026-10-14 (midday)

- The kit is a skill. Copy `skills/bfo-stage-kit/` to `.github/skills/` in your workspace (or `~/.copilot/skills/`)
  and ask the assistant in your own words.
- The map is one page: click a step, part, stage or the flow to light its chain and open its measures. It has
  views for how a step is carried out, what is inside a part, and how a case moves through a stage and end to end.
- Runbook and alert pages for each stage, as HTML beside the Markdown.
- USE.md explains how to bring a register made with the first version up to date.

## First version — 2026-10-09

- The first version: the procedure, the register template, the generator for one stage's structure, measures,
  alert and runbook, and a worked example.
