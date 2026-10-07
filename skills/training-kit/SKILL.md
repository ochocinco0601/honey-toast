---
name: training-kit
description: Build a self-paced training kit on any subject, for any audience - a small learning site of led lessons, practice recipes, shared help and a maintainer's guide, generated as web pages from markdown. Use when asked to build, create or start training, a training kit, a course, a tutorial, a workshop, a hands-on lab, enablement or a learning path that teaches people a tool, a process or a platform ("teach my team to..."), or to extend a kit this skill built. Not for a repository's contributor README.
---

# Building a training kit

Skill version: 1.13 (2026-10-07). Kits record it as `SKILL_VERSION` in `maintaining/build_pages.py`.

You build a kit that leaves its learners able to do something in their own work. What they can do
when they finish is the outcome, and every choice below serves it; the maintainer guide's opening
says where it is written and where the kit ends.

The kit is a **self-paced learning site**: a course home with a led path, units with numbered steps
and progress by unit, a workbook that keeps what the learner writes, practice recipes, shared help,
and web pages generated from markdown. The builder in `starter/` implements that kind of site's
conventions, and its page design is decided: the maintainer guide's "Page design" section states
it with its reasons. Build on it, and explain the navigation and the look in those terms when
asked.

**You are the training expert.** The requester judges whether the kit fits their people and their
work; the craft (instructional design, learning-site conventions, procedural writing, choosing the
reviewers) is yours. Make those calls and state them.

## What you start from

- `starter/` - copy it whole into a new folder named for the programme, outside this skill's
  folder, unless the requester names a place. Its `[TO BE WRITTEN: ...]` placeholders say what goes
  where. **`starter/maintaining/README.md`, the maintainer guide, is the single home of the page
  rules** - how a page is written, marked up, built and checked - and travels with every kit. Read
  it as its opening says before writing anything; this file does not repeat it.
- `reviews.md` - the briefs for the review passes in step 7.
- `references/reference-exercise.md` - a published hands-on exercise, unchanged: the form every
  unit is written in (the guide's "The form of a unit").

Beside the kit, keep a `sources` folder holding a copy of every source you used, including material
you were given only as pasted text, so the reviewers you start can read what you read. Keep your own
working notes elsewhere; reviewers never see them.

## 1. Fix the settings, and ask once

Five settings shape every page: the subject, the audience, where practice happens, the help beside
the learner, and what learners can do. Write them into the settings table at the top of the new
kit's `maintaining/README.md`, whose placeholders say what each holds, with the writing standard
from step 2 in its last row; the guide says below the table how the builder's settings follow.

Take them from the request and your own context. **The audience and the objectives are the
requester's to confirm**: play your reading back in two lines, and wait for the answer before
writing pages. State the audience as the requester states it, never split into kinds of learner
you have not been told of. Do not build on guesses about who the learners are or what their work
is: an audience you were told is wide stays wide.

In the same message, ask for everything the later steps need that you cannot reach yourself:
people who do the work, or a recording of it; samples of what the learners' main tasks use (the
screens of a tool, the documents or cases of a process); and two or three learners to try the kit
later. Start step 2 while you wait. Whatever does not arrive becomes a marked blank, and the kit
goes on.

**Settle the assumptions before writing pages, on one page.** List the starter's defaults this kit
would inherit, and everything you have inferred about the audience and their work, as one
assumptions page the requester answers card by card. Facts about how the tool works are not on it:
check those yourself, from the source the guide's "Nothing invented" names, and assume standard
features work. Never ask the requester to test normal behaviour. Build from the answers. Never
raise these one at a time as they surface in a unit.

## 2. Inventory before you design

- **The learners' real tasks,** from the sources you can reach. Lessons and recipes are training
  examples of these kinds of work, not tools for daily use. The requester's examples point to the
  kind of task; the instances come from the inventory.
- **The critical decisions and common errors,** from people who do the work, recordings, or incident
  and support records; documents describe the procedure, not where people go wrong. Notes in which
  practitioners describe their work count, recorded as told. What you infer yourself goes in the
  claims register as unverified.
- **Objectives,** in the form the guide's settings table gives them.
- **What the established trainings on this subject teach,** unit by unit and in what order,
  read from their published pages: the vendor's own courses and tutorials first. The sources'
  shared order is the default order of the path; a unit no source teaches needs its own reason,
  written down.
- **A writing standard,** before writing. If your environment has an editorial skill or house
  standard for instructional documents, it governs. Otherwise, the Microsoft Writing Style Guide is
  primary, with the Google developer documentation style guide's procedure conventions alongside
  it. The prompts follow the maintainer guide's "Prompts" section, which is fixed and not the
  environment's to override. Set a budget too: words per page, and minutes per unit computed by the guide's "Time estimates".

**A kit has two layers, from different sources.** The *judgment* layer (what a result means, what to
do about it) comes from documents, records and people. The *mechanics* layer (where to go, what each
control or artefact is called, the exact actions) comes only from the thing itself: a tool's
screens, a process's real documents, or someone doing the work. Sources rich in the first are often
empty of the second. Missing mechanics are marked blanks; **when the outcome needs the learner to
operate the thing, missing mechanics restrict release to a pilot**.

## 3. Design the path backward from the outcome

- Every action an objective names is practised on the path, with support that fades from the
  worked example to the learner doing it on their own work. Split an objective into its actions:
  reading a result and acting on it are two.
- **The path opens with an Introduction and ends on its last unit's practice,** with the
  learner's notes and ratings kept, as the guide's "The first unit on a path", "The last unit on a
  path" and its markup say.
- **One worked example runs through a training's path,** as a published course runs one
  scenario, on practice files every learner has, so every learner can follow it and check it.
  How those files are made, and where the learners' own come in, is the guide's "Nothing to
  download" and its "Prompts" rule 2; how examples and learners are labelled is its "The kit's
  practice data is made up" and "No learner categories".
- Practice is designed around the critical decisions from the inventory: varied cases, one of them
  a near miss. Give experienced learners a way to skip what they know.
- Size the path from the inventory: usually three or four units after the Introduction, the first
  of them short with a real result in minutes.
- Levels and further trainings follow the guide's opening and its "Adding a more advanced
  training".
- Recipes cover other tasks from the inventory (the guide's "The recipes are practice").
- The front page leads: the learner's problem in their terms, what they will be able to do, how
  long, and the single first action.

## 4. Work in increments

The first increment is the kit's home page, the first training's home, its Introduction and its
first unit. For each increment: write the pages (step 5), build and check them (step 6), review them
in rounds until one comes back clean (step 7), then show the requester the rendered pages.

**The requester agrees each piece before the next.** Start nothing new until they have reacted to
what is in front of them, in the order a learner reads, from the front page. Once they accept the
first unit of a training, build the rest of that training and show it whole. A handoff or an
instruction to another session never removes this. Waiting here is the process, not a stall.

**While they read, their edits go straight in.** Apply each within minutes, rebuild until the
build's checks pass, and republish; the full review runs once before they first see a piece and
once after they finish it, not on every edit of theirs. That holds for a change of wording. A
correction that cuts, adds or moves steps, or changes what a page is for, runs the learner walk and
the editorial check on the changed pages before it goes back to them; say which ran. A small edit of your own takes the short path in step 7.

**One stable link, opened at the front page.** Update it in place after each piece. Never a
before-and-after page, never a new link per piece, never a link that opens on the newest piece.

**Talking to the requester while they review.** Use the site's own words and no others: a
*training* (such as Getting started), a *unit* (one page on its path, given by number and title),
a *step* (a heading in a unit). Every message has one shape: a status line ("Ready to read: ..." or
"Rebuilding: ... Don't read it yet."), the answer to their question in one sentence, at most three
supporting points, and one line saying what they do now. One concern per message. "Ready to read"
lists exactly which units, which changed since they last read them, where to stop, and which pages
are still old. When pointing at text, quote its exact words and say where it is. "Rebuilding" means
you are working: never end a turn on it.

**You own the orchestration and the editing.** Decide, sequence and drive; never hand the next move
or the coordination back to the requester. They react to finished pieces for fit; they are not the
editor and not the tester. A basic fault they find means your checks failed, and is handled as a
correction, below, so they never raise it twice.

**When the requester corrects you.** Record it the moment it arrives as a row in the kit's
"Corrections" table; the guide's "Corrections" says what a row holds and what an open row stops.
Fix the whole class across every page. Generalize it to a rule for any training; put that rule
where it is enforced (a check if a pattern can find it, `references/review-checklist.md` if it
needs judgement); and if it is about training design in general rather than this kit, add it to
this skill in the same pass and raise the skill's version.

**An outside service is the requester's choice.** Which service, site or system the training has
learners connect to, sign in to or send their work to is a fit decision about their organization,
not craft: show the candidates with what each needs and what leaves the machine, and build on the
one they choose. Never pick one and present it as settled.

**Where their notes arrive.** Where the published page takes comments, the requester leaves each note
as a comment on the text it is about, so edits stay off the chat. Answer each on its thread with
what changed or what was found, then resolve it; the chat gets one status line. A note they mark
out of scope (for example "Parking lot: ...") is a real observation about something other than the
piece under review: log it in the kit's plan with their words and the page, reply that it is
logged and nothing changed, resolve it, and do not act on it until they bring it into scope.

**Handing the work to another session.** Keep `maintaining/HANDOFF.md` in the kit and update it
before handing over. It opens with the commander's intent (the purpose, the end state, what the
receiving session owns, how it will know it is going wrong), then the review cadence in force,
the requester's rulings in their words, where they are in their review, and the open rows of the
Corrections table. Cold-read it with an agent that has not seen the work before you trust it.

**Show, do not ask.** When a choice is the requester's (which of two approaches fits their people,
which tasks the path covers first; not the page design, which is decided), build two or three working alternatives and show them
on one labelled page that says what each is and what to look at, then ask one question. That page
is for a choice between options, never a before-and-after (see the link, above). Never ask
them to describe what they want in the abstract, or to compare unlabelled pages. What their
choice settles, and what it leaves open, is the guide's "Decisions". Anything the
requester cannot judge by eye (contrast, density, brittleness, whether the teaching works) is
settled by an independent, measured review, and they see the outcome, not the question.
**Record every decision** made with the requester under the kit's "Decisions", as the guide says
there. When the path is complete, it goes to real learners (step 8) before it goes to everyone.

## 5. Write the pages

Follow the maintainer guide. Its "The rules that do not change", "Writing" and "Prompts" sections
are the page rules, and they decide what its other sections do not cover. The wording they set is
calibrated by the audience and the kind of document, not by taste: apply it, and never ask the
requester how terse or conservative they like it.

**Plan each unit's pictures as you write it,** by the guide's "Pictures": go through the unit
action by action and mark where its table gives a picture a job (find a control, confirm a
result, see the window's parts, explain an idea), then make or fetch each one. A page of text
with no picture is a decision you made against that table, never the default. Which pictures a
page needs and what each shows are craft calls, yours. **Where the pictures come from is the
requester's choice,** once per kit, before the first unit is shown: put the sources side by side
(the vendor's documentation under its licence, screenshots taken for the kit under the product
owner's screenshot terms, or both), with what each allows, what it shows that the learners will
not see, and what of the requester's screen it publishes.

The starter's pre-written sentences, and the ones the builder writes itself (listed in the guide),
assume one case: technical readers, practice in an assistant's chat, an assistant as help. Reread
every one against your settings and rewrite what does not fit. Where practice is not in a chat, its
devices become:

| Practice in an assistant's chat | In a tool | In a process |
|---|---|---|
| A prompt with a Copy button | The screen, the control and the action; `<!-- tool -->` for text pasted into the tool | The document, case or decision and what to do with it |
| `<!-- frame -->`: a request the learner writes | An entry the learner writes in the tool | A draft, note or decision the learner writes |
| "Ask the assistant" help | Help beside the learner, in-tool help or a support channel | Help beside the learner, or a colleague who does the work |
| Checking the assistant's work against the files | Checking the screen against its source, or a second screen | Checking the result against the standard or a worked example |

## 6. Build and check

Build and walk the pages as the guide's "Build and check" says, until the build ends "All checks
passed." A "DRAFT" line means placeholders are still unwritten, which makes the kit a draft (the
guide's "Before you hand it over"). If you cannot operate a browser, say so, and have the
requester walk it when you show the increment.

## 7. Review with readers who did not build it

Each pass in `reviews.md` is run as that file's opening says. Scale the set to the kit: every
increment gets review 1 (first-time learner), review 10 (sequence), review 11 (prompts as sent),
review 12 (pictures) and, after fixes, review 5 (regression); a complete path gets the rest. A
small kit still gets reviews 1, 3, 4, 5, 9, 10, 11 and 12. A reviewer that cannot operate a browser or the tool reads the
pages and says which steps it could not perform. If you cannot start a fresh session yourself,
give the requester the increment's briefs in one message to paste into new chats, and say the kit
is unreviewed until they do.

**Before every "Ready to read", run `references/review-checklist.md` on the built pages,** as its
opening says, after the build's `maintaining/check_rulings.py` has caught the mechanical half.
Its item 11, the titles and headings read alone, is a pass of its own: a sentence read does not
catch a vague heading.
**The review ends when these checks pass, each of which can fail without anyone judging how much
a finding matters:**
1. **Build:** the build and its rulings checks pass.
2. **Facts:** every claim about the tool on a changed page has a sourced line in the kit's facts
   file, and every claim about what is on screen is confirmed against the version the learners
   run (its source at that version's commit, or the screen itself), or is taken off the page.
3. **Learner walk:** a fresh first-time-learner walk (review 1) records no STOP, and that
   learner answers the unit's own self-check correctly from the page alone.
4. **Editorial:** one full editorial pass, every finding applied, none declined; then checks 1
   to 3 run again. There is no second editorial round.

Time matters: keep the checking in proportion to the change. A fact already confirmed for this
version is cited, never checked again; checks 2, 3 and 4 run at the same time; a unit or two
takes well under an hour, not an afternoon. A failed check is fixed and only that check runs again. The requester sees nothing until all
four pass. Record each check's result in a report file under `reviews/` and name it in the "Ready
to read" message. Rounds until one returns no findings never end: a fresh reviewer always finds
a wording to prefer.
**A small edit of your own takes the short path:** rebuild, run the checks, have a fresh reviewer
run review 5 on the changed page, then republish. Keep the full rounds for a new or rewritten unit.

**Before the requester sees a link, an editorial review reads every page in the order they will
read it, from the front page,** not only the piece that changed: for each sentence, what it says,
to whom, and whether that reader understands it on first read.

**Then walk the published link by clicking, from the front page,** as a learner arrives: each card,
each unit, each Continue, at 1,440 pixels with the folds closed. Reading the markdown and a
screenshot of a local file does not show what the hosted viewer does: a unit that opens scrolled
down, a picture of the wrong control. If you cannot click inside the hosted page, say so, and walk
a local build the same way.

## 8. Try it with real learners

Before the kit goes to everyone, two or three real learners from the audience take the path while
someone watches, or record where they stopped on the same form as review 1. Fix what stops them.
If no learners can be found, the kit is untried: say so in the hand-over, and release it as a pilot.

## 9. Hand it over

The learner's way in is the web pages (the guide's first rule), and the address they are served at
is what the hand-over gives out. How practice files reach the learner is the guide's "Nothing to
download". A kit with a placeholder left is a draft, with the release the guide's "Before you hand
it over" gives it. The kit's first release sets its version and dates its first entry in
`CHANGELOG.md`, as the guide's "Versions" says. Tell the requester where the kit is, the settings
used, what is still blank and what would fill it, the claims still unverified, what the reviews
and the learner tryout found and fixed, and what has not been checked.

## Gotchas

Each is a case of a principle above, stated where it bites.

- A site that is not recognisably a course (a checklist of files, no front door) has to be rebuilt,
  and the rebuild throws away every page written to the wrong shape.
- A requester's or reviewer's example written in as the rule overfits the kit to one case. Keep
  the general form.
- Reviewers asked to play roles in the requester's organization (a manager, a trainer, a
  presenter) invent that organization: a data rule, a measurement owner, an untested setup.
  Their findings about the organization are questions to check against what the requester has
  already said, never decisions to hand the requester.

## Extending a kit this skill built

**A kit built before this skill, or with another builder,** moves onto the starter's builder
before any page is rewritten: copy the starter's `maintaining/` scripts in, carry the kit's
settings into the block between the marker lines, add a `CHANGELOG.md`, and build. Otherwise every
round of fixes is made on pages the skill's design has already replaced.

**Before rewriting the pages of a kit, audit them.** Judge every page against the established
trainings' unit lists (step 2): keep, change, merge, move, cut, or add a missing one, each with
the source it rests on, and have an instructional designer who did not write the audit check it.
Rewrite only what survives. A page polished before it is judged may be one that should not exist.

Read the kit's own `maintaining/README.md` and follow it; its settings table says who the kit is
for, and `facilitator/claims.md` holds what the kit rests on. Run
review 5 after your change.

**Bringing a kit up to this version.** If the kit's `SKILL_VERSION` is older than this skill's:

1. Before replacing anything, list the sentences the kit reworded inside its `build_pages.py`
   (the maintainer guide names the sentences the builder writes itself). Only the settings
   between the two "What a maintainer changes" marker lines survive the next step.
2. Replace the kit's `maintaining/build_pages.py`, `check_text.py` and `check_structure.py` with
   the starter's, then put back everything between the marker lines from the kit's own copy and
   the rewordings from step 1. Set `SKILL_VERSION` to this version. From 1.1 or older, also copy
   the starter's `getting-started/workbook.md` into each training's folder, and give the last unit
   the objectives' rating list as the starter's last unit has it. From 1.6 or older, remove the
   kit's closing "this week" unit, its organization page and any "ask whoever sent the training"
   line, and move the rating list to the last remaining unit. From 1.7 or older, also copy the
   starter's `check_rulings.py` and set it for the pages not yet rebuilt, as the guide's "Build and
   check" says.
3. Bring every passage of the kit's maintainer guide that describes the pages, the builder or
   progress in line with the starter's, keeping the kit's own settings table and "Decisions".
   From 1.2 or older, this adds the guide's "Prompts" section.
4. Rebuild. From 1.2 or older, the build names each prompt with a slot (PROMPTSLOT): rewrite each
   by the guide's Prompts rules, then delete the kit glossary's "Blank" row and any page text
   telling learners to replace blanks, and build again. Then add a CHANGELOG entry that raises the
   minor number and says what learners will notice.

A choice recorded under the kit's "Decisions" that conflicts with what this version changes is
handled as the guide's "Decisions" says.

What 1.13 changed from 1.12:
- Checklist item 18: a "What is ...?" unit teaches its subject as the owner defines it, with
  more than one kind of use; the case the training builds is one kind, and a which-fits exercise
  grades on the owner's distinction. Item 19: overlapping features get one "which to use when"
  table on the programme's home page, before any training. Review 3 looks for both.
- Upgrading from 1.12: set `SKILL_VERSION`, then judge every concept unit and the home page
  against items 18 and 19.

What 1.12 changed from 1.11 (pictures):
- Guide, "Pictures": a picture has one of four jobs (locate a control, confirm a result, orient
  in the window, explain an idea), each with its form, the cases that get none, what the
  published trainings lead you to expect, and the rules every picture meets (placement, agreement
  with the text, text alternative, credit by licence). It replaces the one line that called for a
  picture only "where the learner must find something on the screen, cropped to that control".
- No review looked for a missing picture. Now: step 5 plans pictures as a unit is written;
  checklist item 15 judges both the pictures present and the places with none; review 12 is a
  pictures pass on every increment; reviews 1 and 3 report where a learner searched the screen
  and where an idea is told but not shown.
- `measure.py` prints each page's pictures; the build fails on a picture with no text
  alternative, or one over 150 characters (ALTTEXT). The builder puts an SVG drawing into the
  page itself, so it follows the page's light and dark colours.
- Where pictures come from: screenshots are taken for the kit, cropped and outlined as the job
  needs; a product owner's published screenshot terms are stated to the requester as a fact.
- Guide, "Density": a sentence has at most 25 words and a paragraph at most six sentences (the
  ASD-STE100 structure rules), and the build fails on either (SENTENCE, PARAGRAPH); parallel
  items are a list; a run of paragraphs breaks within about 130 words; a heading every 250 at
  most. Measured from the published trainings. The page's line height goes from 1.5 to 1.6 and
  the paragraph gap from 8 to 16 pixels, as those trainings set them.
- Upgrading from 1.11: replace `build_pages.py`, `check_text.py`, `check_rulings.py`,
  `measure.py` and `check_structure.py` (keep the kit's settings and EXEMPT lists), add the guide's "Pictures"
  section and its two changed table rows, then run review 12 on every unit.

What 1.11 changed from 1.10:
- Guide, markup: an answer runs from its `Check your answer:` line to the next heading, so an
  answer to several cases is a list, one case to an item, led by the case in bold. The build fails
  on an answer paragraph that runs the cases together (ANSWERBLOB).
- Upgrading from 1.10: replace `build_pages.py` and `check_rulings.py` as "Bringing a kit up to
  this version" says, update the guide's markup row, and rewrite any answer the build names.

What 1.10 changed from 1.9:
- Guide, "Setup is the workplace's way": where learners work on computers their company manages,
  software, its updates and the sign-in account come through the company (its software portal,
  their work account), never a vendor's download site, the tool's own update menu or "your plan".
  The build catches the common wordings: installing or downloading from a web address
  (PUBLICINSTALL), the tool's own update command (SELFUPDATE) and, for Copilot, a plan or a
  personal account (YOURPLAN). A review still reads each setup step against the rule.
- Builder: in the side menu, "Practice recipes" opens with its own toggle to list each recipe, as
  a unit opens to list its steps, on every page of the training; it is open on the recipe index
  and on each recipe. Before, the recipes were listed only on the index page.
- Upgrading from 1.9: replace `build_pages.py` and `check_rulings.py` as "Bringing a kit up to
  this version" says, and add the guide's new rule; then reword any setup step the build names.

What 1.9 changed from 1.8 (where rules live; four rules added):
- The review ends on four pass-or-fail checks (build, sourced facts, a learner walk with no STOP
  and a correct self-check, one editorial pass fully applied), not on a round with no findings,
  which never arrives (step 7).
- The requester's notes arrive as comments on the page; a note marked out of scope is logged
  in a parking lot and not acted on (step 4, "Where their notes arrive").
- Two rules, both in the guide under "Writing": a control is named in the
  words on the screen, checked there rather than taken from the vendor's documentation; and a
  unit's name is its title, stated once, which the build now enforces. On a training's home, the
  "Next" link at the foot follows the learner's progress and, once every unit is done, points to
  the next training.
- Each rule is stated in one place. The page rules are in the maintainer guide alone, and this
  file points at them; the review checklist names the guide rule each item judges; the review
  briefs point at the guide.
- Rules this file held for pages moved into the guide: the Introduction unit, the assistant doing
  the file work, tool facts from the vendor's current documentation, the permission request, and
  the scope of a customization the training creates. Each guide rule a check enforces names the
  check.
- Three copies that disagreed now say one thing: the learner's own files are offered after the
  worked prompt; the requester's edits go straight in while they read, and any other small edit
  takes the short review path; where practice is in an assistant, ready-made files are fetched by
  it, otherwise the learner downloads them.
- Gotchas that only repeated a rule are gone.
- Guide, "Nothing invented"; checklist item 8: where a setting
  the page leaves alone changes what the screen shows, such as VS Code's Session Target, a page
  names only what every value shows, or has the learner select the value it assumes.
- Checklist item 7: a decision exercise's cases each have one right
  answer under everything earlier units taught, with the hardest distinction beside a near miss.
- Checklist item 11: "no two start alike" holds within a training; across trainings, the same
  kind of unit titled the same way is the parallel the set needs.
- Guide, "Time estimates": each time is written as the writing standard writes numbers (for
  Microsoft's, words below 10 and numerals from 10), so the cards don't mix "25" with "fifteen".
- Guide, "Every step has a recovery route": a recovery finds a control in the wrong state by what it
  does, never by the label it no longer shows.
- Builder: the "Stuck on this step?" question now keeps each action's number and line; it ran a
  step's numbered actions together. A training's home with no progress no longer stops its script
  (the start button it looked for was removed with the start box), which had left the outline and
  search dead on a first visit.
- `measure.py` no longer counts the practice files in
  `sample-files/` as pages, and the build no longer reports "Getting started" as a stand-in name,
  since the guide names the beginner training that.
- Upgrading from 1.8: bring the kit's maintainer guide in line with the starter's (step 3 of
  "Bringing a kit up to this version"); its pages need no change.

What 1.8 changed from 1.7:
- Working with the requester (step 4): they agree each piece before the next, with direction set by
  each training's first unit; their edits go straight in while they read; one stable link opened
  at the front page; one message shape (status line, answer first, at most three points, what to
  do now); exact units, words and places, never a bare page or unit name; you own the orchestration and the
  editing, and every fault they find becomes a rule, a sweep and a check in the same pass;
  handoffs open with commander's intent.
- Step 1: the assumptions page carries defaults and inferences only; tool facts are checked
  against the vendor's documentation, never put to the requester.
- Step 7: reviews run in rounds until one comes back clean; `references/review-checklist.md` runs
  before every "Ready to read", and covers a unit or a line, lesson not mechanism, the example
  that misinforms, headings and unit titles read cold as a list, and where a created
  customization applies.
- Pages: worked examples run on practice files the assistant creates, so nothing is downloaded by
  default; requests name their target folder, write nothing else, and are laid out one
  instruction per line; step headings are never numbered; positions and times are generated, not
  typed; a callout (Note, Important) only for a fact that changes what the learner does, at most
  one per step; no presenter material.
- `maintaining/check_rulings.py` fails the build on faults otherwise found only by hand,
  for every learner page by default; its tool-specific rules switch on with `TOOL`.

What 1.7 changed from 1.6:
- The outcome is what learners can do when they finish; the week-later measure, the closing
  "this week" unit and the written commitment are gone, and measuring transfer is outside the kit.
- Levels divide by difficulty only, never by role. No kinds of learner, and no example dressed up
  as someone's job; learners may use their real work files.
- No organization page and no "ask whoever sent the training": help is the help beside the
  learner and the kit's help page.
- Each training and unit says what it needs from earlier ones, so learners can start anywhere.

What 1.6 changed from 1.5:
- Units are written in the form of a published hands-on exercise, kept in
  `references/reference-exercise.md`: the unit and each step open with why, actions are numbered
  one to a number, and what the learner sees follows each action. This replaces 1.4's sentence
  rule, which moved every "why" to the explanation page.
- Word budgets are a ceiling checked after writing, never a reason to shorten a sentence.
  Reviews 1 and 6 now report sentences that need a second read and steps with no reason given.
- A numbered list can carry on after a prompt (`4. ` resumes the numbering).
- A kit built before this skill moves onto its builder first.
- Step 2 reads the established trainings' unit lists before design; step 3 runs one worked
  example through a path, with a contrasting sample per unit, instead of branching by kind of
  learner; an existing kit is audited page by page before it is rewritten.
- Where practice is in an assistant, the assistant does the file work and the learner directs
  and checks; the first unit has it fetch the kit from a public repository. The build's
  training-files zip (`FILES_ZIP`) is for kits without one, and `""` turns it off.
- A step shows only what the learner acts on: a one-line reason, one to three short actions, a
  picture where something must be found on screen, and a one-line Check that never folds; the
  rest folds (`<!-- more: -->`). The numbers, measured from VS Code's quickstart and GitHub Skills,
  are in the guide's "What a step shows", with a ten-second test at 1,440 pixels before anyone
  sees a page. Pictures are copied in beside the pages, so they show wherever the pages are
  served.

What 1.5 changed from 1.4:
- No learner page shows a template. A `[YOUR ORGANIZATION: ...]` field may appear only in
  `facilitator/`; the build refuses one on any learner page (ORGBLANK). Links to the web open in
  a new tab. (1.5's organization page was removed in 1.7.)

What 1.4 changed from 1.3:
- The learner's way in is the web pages at an address; the files come to their computer in the
  first unit. The home page no longer explains how to read the kit (section 9; the guide's first
  rule).
- The guide's "Writing" section carries the sentence rule (a sentence in a step stays only if the
  learner needs it to act, to know where to look, to know what they should see, or to act
  safely) and word budgets per page kind, each from a measured published training, with
  `maintaining/measure.py` to count every page against them. Review 6 cites them.
- The home page and the side menu use one set of group names in one order.
- The build refuses a bracketed organization field on a learner page (ORGBLANK). (1.4's
  organization page was removed in 1.7.)

What 1.3 changed from 1.2:
- Prompts are sent as written. The highlighted blank, the folder box that filled one in, and the
  aside telling learners to change any blank are gone from the pages.
- The build fails (PROMPTSLOT) on any prompt line carrying an angle-bracket slot, naming the page
  and line.
- The maintainer guide has a "Prompts" section: the rules the established trainings follow, which
  every prompt in a kit is written to.
- A frame (`<!-- frame -->`) is a complete example to write from, never a skeleton with gaps.

What 1.2 changed from 1.1:
- Note boxes (`<!-- note -->`): a step that asks the learner to write something keeps their answer in
  the browser.
- Ratings (`<!-- rate -->`): the learner says how sure they are of each objective at the end of the
  path.
- A workbook page per training gathers both, under the unit and step they came from, and downloads
  or prints them.
- The starter's last unit closes with the rating. (1.2's written commitment was removed in 1.7.)

What 1.1 changed from 1.0:
- Progress is by unit: Continue completes a unit and steps have no checkboxes. Ticks a learner made
  on steps under 1.0 are ignored, so their progress starts again.
- The look is quieter and measured: contrast, type sizes and spacing meet the standards in the
  guide's "Page design".
- The page is compact: the text column is as wide as the breadcrumb, with tighter spacing.
- A list can nest inside a list item, and bold can wrap a link.
