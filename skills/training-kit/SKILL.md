---
name: training-kit
description: Build a self-paced training kit on any subject, for any audience - a small learning site of led lessons, practice recipes, shared help, presenter notes and a maintainer's guide, generated as web pages from markdown. Use when asked to build, create or start training, a training kit, a course, a tutorial, a workshop, a hands-on lab, enablement or a learning path that teaches people a tool, a process or a platform ("teach my team to..."), or to extend a kit this skill built. Not for a repository's contributor README.
---

# Building a training kit

Skill version: 1.0 (2026-09-24). Kits record it as `SKILL_VERSION` in `maintaining/build_pages.py`.

You build a kit that leaves its learners able to do something in their own work a week later.
Approval at the end of a session does not count; that later behaviour is the outcome, and every
choice below serves it.

The kit is a **self-paced learning site**: a course home with a led path, units with numbered steps
and progress, practice recipes, shared help, and web pages generated from markdown. The builder in
`starter/` implements that kind of site's conventions; build on them rather than redesigning them.

**You are the training expert.** The requester judges whether the kit fits their people and their
work; the craft (instructional design, learning-site conventions, procedural writing, choosing the
reviewers) is yours. Make those calls and state them. Obvious defects are for your reviews to find,
not for the requester.

## What you start from

- `starter/` - copy it whole into a new folder named for the programme, outside this skill's
  folder, unless the requester names a place. Its `[TO BE WRITTEN: ...]` placeholders say what goes
  where. **`starter/maintaining/README.md` is the single home of the page rules** - how a page is
  written, marked up, built and checked - and travels with every kit. Read it in full before
  writing; this file does not repeat it.
- `reviews.md` - the briefs for the review passes in step 7.

Beside the kit, keep a `sources` folder holding a copy of every source you used, including material
you were given only as pasted text, so the reviewers you start can read what you read. Keep your own
working notes elsewhere; reviewers never see them.

## 1. Fix the settings, and ask once

Five settings shape every page. Write them into the table at the top of the new kit's
`maintaining/README.md`, with the writing standard from step 2 in its last row, and the matching
values at the top of `maintaining/build_pages.py`.

| Setting | What to decide |
|---|---|
| Subject | What the trainings teach, in one line |
| Audience | Who the learners are, by the work they do; what they already know of this subject; and how expert they are in their own work |
| Where practice happens | The tool, screen or console the learner operates; an assistant's chat; or, for a process, the cases, documents and decisions it works on |
| Help beside the learner | Who or what a stuck learner asks, and whether it can read the kit. If the learners have an assistant, it comes first, with a person for what it cannot answer; if not, the person comes first |
| Outcome a week later | The observable thing a learner does in their own work that shows the training worked |

Take them from the request and your own context. **The audience and the outcome are the requester's
to confirm**: play your reading back in two lines, and wait for the answer before writing pages.

In the same message, ask for everything the later steps need that you cannot reach yourself:
people who do the work, or a recording of it; samples of what the learners' main tasks use (the
screens of a tool, the documents or cases of a process); a person for what the help beside the
learner cannot answer; and two or three learners to try the kit later. Start step 2 while you wait.
Whatever does not arrive becomes a marked blank, and the kit goes on.

## 2. Inventory before you design

- **The learners' real tasks,** from the sources you can reach. Lessons and recipes are training
  examples of these kinds of work, not tools for daily use. The requester's examples point to the
  kind of task; the instances come from the inventory.
- **The critical decisions and common errors,** from people who do the work, recordings, or incident
  and support records; documents describe the procedure, not where people go wrong. Notes in which
  practitioners describe their work count, recorded as told. What you infer yourself is recorded as
  unverified.
- **Objectives in performance form,** on the training's home page where learners read them.
- **The week-later measure,** in `facilitator/evaluation.md`, before any unit is written: a record or
  artefact that shows the behaviour, a baseline, and who can reach learners who took the training
  alone.
- **A writing standard,** before writing. If your environment has an editorial skill or house
  standard for instructional documents, it governs. Otherwise, the Microsoft Writing Style Guide is
  primary, with the Google developer documentation style guide's procedure conventions alongside
  it. Set a budget too: minutes per unit and words per page.

**A kit has two layers, from different sources.** The *judgment* layer (what a result means, what to
do about it) comes from documents, records and people. The *mechanics* layer (where to go, what each
control or artefact is called, the exact actions) comes only from the thing itself: a tool's
screens, a process's real documents, or someone doing the work. Sources rich in the first are often
empty of the second. Missing mechanics are marked blanks; **when the outcome needs the learner to
operate the thing, missing mechanics restrict release to a pilot**.

## 3. Design the path backward from the outcome

- Every action the week-later outcome names is practised on the path before the last unit, with a
  worked example first and support that fades to the learner doing it on their own work. Split the
  outcome into its actions: reading a result and acting on it are two. The last unit is their own
  work, this week.
- Practice is designed around the critical decisions from the inventory: varied cases, one of them
  a near miss, and a short attempt a few days after the path. Add a cue when the outcome is a
  habit, and a way for experienced learners to skip what they know.
- **The path opens with an Introduction unit** that grounds the learner before any doing (as every
  Microsoft Learn module does; Gagné's first events, Ausubel's advance organizer): the real
  situation they are in and why it matters to them now; a short map of the few ideas the path uses,
  each named once in plain words; what they will be able to do; and how the path is laid out. A few
  minutes to read, no practice, no lecture. Without it the first unit starts cold.
- Size the path from the inventory: usually three or four units after the Introduction, the first
  of them short with a real result in minutes.
- Levels divide by experience (a beginners' training first, advanced ones beside it) or by role (one
  starting training per role, side by side). Default to experience unless the roles do different
  tasks. Advanced topics are sibling trainings, never extra units on the beginner path.
- Recipes cover other tasks from the inventory, one each.
- The front page leads: the learner's problem in their terms, what they will be able to do, how
  long, and the single first action.

## 4. Work in increments

The first increment is the kit's home page, the first training's home, its Introduction and its
first unit. For each increment: write the pages (step 5), build and check them (step 6), review them (step 7), then show
the requester the rendered pages and carry on with the next increment unless their reaction changes
the direction. Learners waiting on the training need something to use now. When the path is
complete, it goes to real learners (step 8) before it goes to everyone.

## 5. Write the pages

Follow the maintainer guide. These principles govern it, and decide what the guide does not cover:

- **The learner does it.** Every practice step is performed by the learner in the place practice
  happens; help explains and checks, never does. Every check compares against something the learner
  can see for themselves.
- **Plain is not simplistic.** Write to two separate facts about the reader: how little they know of
  this subject, which sets how plainly you explain, and how capable they are in their own work, as
  the audience setting states, which sets the register. Never let the first lower the second. Test:
  would you say it this way, in person, to the audience as stated? Name their work the way they
  name it.
- **The wording is calibrated, not a matter of taste.** For self-paced procedural pages for people
  new to the subject, the standard is plain-language concision with one exception, safety
  reassurance and orientation; the guide's Writing section states it. Apply it; do not ask the
  requester how terse or conservative they like the wording.
- **Names lead.** Every title, heading, link and menu label tells the learner what they will do or
  get there, in their words (information scent). The starter's titles and headings name stages of
  this method and are stand-ins; the build counts any left.
- **Less is more.** A page carries what the next action needs. The elements the guide requires come
  first, each in the least intrusive form that serves its moment; everything else opens on request.
  Fix by changing or removing before adding.
- **Nothing invented.** No organization policy, contact, screen label or system name that you have
  not seen; a marked blank instead, with what to do meanwhile. Record every claim in
  `facilitator/claims.md` with its source.

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

From the kit's folder, `python maintaining/build_pages.py`, until it ends "All checks passed." A
"DRAFT" line means placeholders are still unwritten; a draft goes to named pilot learners only. Then
walk `read-in-browser/README.html` as a learner, at the width of a window beside the place practice
happens. If you cannot operate a browser, say so, and have the requester walk it when you show the
increment.

## 7. Review with readers who did not build it

Each pass in `reviews.md` is run by a fresh session or subagent given only its brief, the kit and
the `sources` folder. Scale the set to the kit: every increment gets review 1 (first-time learner),
review 10 (sequence) and, after fixes, review 5 (regression); a complete path gets the rest. A small
kit still gets reviews 1, 3, 4, 5, 9 and 10. A reviewer that cannot operate a browser or the tool reads the pages and
says which steps it could not perform. If you cannot start a fresh session yourself, give the requester the
increment's briefs in one message to paste into new chats, and say the kit is unreviewed until they
do.

## 8. Try it with real learners

Before the kit goes to everyone, two or three real learners from the audience take the path while
someone watches, or record where they stopped on the same form as review 1. Fix what stops them.
If no learners can be found, the kit is untried: say so in the hand-over, and release it as a pilot.

## 9. Hand it over

The generated `read-in-browser/` pages travel with the markdown wherever the kit is published;
without them learners get raw markdown. A kit with any `[TO BE WRITTEN: ...]` placeholder left is a
draft, and goes to named pilot learners only, never to everyone. The kit's first release sets its
version and dates its first entry in `CHANGELOG.md`, as the guide's "Versions" says. Tell the requester where the kit is, the
settings used, what is still blank and what would fill it, the claims still unverified, what the
reviews and the learner tryout found and fixed, and what has not been checked.

## Gotchas

Each is a case of a principle above, stated where it bites.

- A site that is not recognisably a course (a checklist of files, no front door) has to be rebuilt,
  and the rebuild throws away every page written to the wrong shape.
- Keyboard shortcuts given without the visible action strand newcomers in a screen-based tool. Name
  the action as the learner performs it in the place practice happens, in the standard's form.
- A kit that names a professional's work in words they would never use for it (calling an
  auditor's evidence review "paperwork"), praises simple acts, or explains what their job taught
  them talks down to them. The register test catches the sentence; the naming rule catches the
  title and the file name.
- A "Next:" line above a unit's end lets a learner leave before the unit is recorded, and resume
  then sends them back to a finished unit. Leave the way on to the builder's end-of-unit block.
- A kit whose every help route is a blank strands the learner at the first stop. The way to get
  help is never a blank: the help beside the learner, or whoever sent the training.
- A rule to use only look-only actions, with no screen confirmed, leaves the first units with
  nothing to do. An action not yet confirmed goes on the path as a marked blank, and the kit goes
  to a pilot.
- Sources that explain what results mean but hold no screens produce a kit that teaches judgment
  and not the clicks. Ask for the mechanics in the step 1 message.
- Cutting one element at a time removes what something else depends on. Cut from the whole page:
  each element's job, the moment it serves, what depends on it.
- A requester's or reviewer's example written in as the rule overfits the kit to one case. Keep
  the general form.

## Extending a kit this skill built

Read the kit's own `maintaining/README.md` and follow it; its settings table says who the kit is
for, and `facilitator/claims.md` and `facilitator/evaluation.md` hold what the kit rests on. Run
review 5 after your change.
