# Maintaining these trainings

For whoever changes or extends this kit, usually an AI assistant session asked to add to it. Read
this whole page before you change anything. Learners never need this folder.

This kit is a programme of trainings that share their help pages, practice files and web version.
Its levels divide by difficulty: **Getting started** is the beginner training, and intermediate and
advanced trainings sit beside it. Levels never divide by role. Learners skip around, so each
training and each unit opens by saying what it needs from earlier ones, and a learner can start
anywhere.

The kit ends at what learners can do when they finish: the objectives, in performance form, on
each training's home page. Measuring what happens afterwards is outside it.

## This kit's settings

Fixed when the kit was built. Every page is written to them; change one only on purpose, and then
review every page against it.

| Setting | This kit |
|---|---|
| Subject | `[TO BE WRITTEN: what the trainings teach]` |
| Audience | `[TO BE WRITTEN: who the learners are, by the work they do; what they know of this subject; how expert they are in their own work]` |
| Where practice happens | `[TO BE WRITTEN: the tool, screen or console; an assistant's chat; or, for a process, the cases, documents and decisions it works on]` |
| Help beside the learner | `[TO BE WRITTEN: who or what a stuck learner asks first (the learners' assistant comes first, if they have one), the person for what that cannot answer, and whether the help can read these pages]` |
| What learners can do | `[TO BE WRITTEN: what a learner can do when they finish, in performance form (a verb and what they do it to): the objectives on each training's home page]` |
| Writing standard and budget | `[TO BE WRITTEN: the standard the pages follow, and the budget: minutes per unit (the times in TRAININGS) and words per page]` |

The builder's own settings, at the top of `build_pages.py`, follow from this table: `PROGRAM_NAME`,
the programme's name; `PRACTICE_PLACE`, where practice happens; `ASSISTANT` and `ASSISTANT_CHAT`,
the help beside the learner and where a question for it is pasted; `KIT_OPEN_IN_ASSISTANT`,
whether that help can read these pages (the "Stuck?" question carries the step's own words either
way, so it never relies on kit files the help does not have); and `STUCK_BUTTON`, whether each step offers a question to
copy for that help (turn it off when the help is a person). Keep them in step with the table.
Each applies to every page at once, so changing one also changes pages you have not yet rewritten
for it. `SKILL_VERSION` is not a setting: it records which version of the skill built the kit.

The builder also writes some sentences itself. When the audience, the place practice happens or the
help beside the learner differs from the defaults, reread these in `build_pages.py` and reword them:
the prompt labels (`prompt_block`), the "Stuck on this step?" button and its question, the copy messages,
the outline's and the end-of-unit block's labels ("Start the training", "Continue", "Next unit:",
"End of the path", "Back to the training", "Not started" and the like), the line under a unit's
Continue button that says it marks the unit complete, "Mark as not complete", the end-of-path
message, and the page foot (`page_foot`). The builder's other
settings shape the menus and links: `TRAININGS` (each training's folder, name, level, time, path,
pages before unit 1, and `stuck_from`, the first step on a unit that offers "Stuck on this step?"),
`MENU_AFTER` (the help pages listed, in order, under "More" in the outline; its group names and
open flags are not shown), `GLOSSARY_TERMS` (words linked to the glossary) and
`UI_LABELS` (on-screen labels never linked, even when they contain a glossary word: add every bold
screen label that contains one, such as **Open Preview** when "Preview" is a glossary word).

## The rules that do not change

- **The learner's way in is the web pages.** A learner opens the kit at a web address and reads
  it in a browser, with the place practice happens open beside it. The markdown is the source the
  pages are built from. No learner page tells the learner how to find or open the pages they are
  already reading, and no page offers more than one way to get the kit. The home page and the side
  menu use one set of group names in one order.
- **Nothing to download.** The practice files every worked example uses are created by the
  assistant from a complete request on the page, starting in the first unit, which has it create
  the practice folder. The training then needs nothing on the learner's computer beforehand. No
  step depends on anything the learner may not have: their Downloads folder, their own documents,
  or a download that can fail (the build fails on a prompt that reads that folder: DOWNLOADS).
  Ready-made files come in only when a later training truly needs files that cannot be written to
  a spec: the build packs them in a zip beside the pages (`FILES_ZIP` in `build_pages.py`, `""` by
  default, which turns it off). Where practice is in an assistant, the request has it fetch them;
  otherwise that unit has the learner download and extract them. The learner never handles git by
  hand.
- **Setup is the workplace's way.** Where learners work on computers their company manages,
  software, its updates and the account they sign in with come through the company: its software
  portal and their work account. No page sends a learner to a vendor's download site, has them
  update the tool by its own menu, or speaks of "your plan". Name no particular portal: "your
  company's software portal" is the general default an adopter may replace. The build catches the
  common wordings: installing or downloading from a web address (PUBLICINSTALL), the tool's own
  update command (SELFUPDATE) and, for Copilot, a plan or a personal account (YOURPLAN). It does
  not catch every wording, so a review reads each setup step against this rule.
- **Each training teaches a learner working alone,** at their own pace. The kit is self-paced: it
  has no presenter material and assumes no live session.
- **Position and time are generated, never typed.** The breadcrumb, the unit's header and the
  outline show a unit's number and time. No page writes "Unit 2", "Unit 4 of the path" or a time
  such as "about 10 minutes" in its text, so reordering the path cannot leave a stale number.
  Text names a unit or step by its title or heading, or links it, never by number ("step 3") or by
  place ("the next unit"). The build fails on a position such as "Unit 4 of the path"
  (UNITPOSITION), a time such as "about 10 minutes" (TIMEINTEXT) and a reference by place such as
  "the second unit" (ORDINALREF); other forms are for the reviewer to catch.
- **Step headings are never numbered on screen;** only the actions inside a step, and the units in
  the outline, are. The markdown writes `## 1. Step name` so the builder knows it is a step; the
  page shows the name only, and the build fails if a number shows (STEPNUMBER).
- **The learner does every practice step,** in the place practice happens, because doing it is the
  skill being taught. Nothing is done or sent on their behalf; a prompt they paste has a Copy
  button. Help may explain, diagnose or check, but never does a practice step.
- **Where practice is in an assistant, the assistant operates and the learner directs and
  checks.** Operating it is the skill being taught, so any file work a step needs (fetching,
  copying, renaming, moving) is a request to the assistant followed by a check, never a manual
  chore. The learner does by hand only what the assistant cannot: the tool's own controls.
- **Every action has a check** saying what the learner should see, and every check compares against
  something they can see for themselves: the source, a second screen, the standard, a worked
  example. An assistant's or a tool's account of its own work is not a check, and neither is "you
  can say what it means". The build fails on a Check that says only that a reply appeared
  (REPLYCHECK).
- **Every step has a recovery route:** what to do when the check does not match, or a link to where
  that is covered. A recovery for a control in the wrong state finds it by what it does (in VS Code,
  Ctrl+. opens the list of agents), never by the label it no longer shows, and never by having the
  learner try other controls, which can change settings the page leaves alone. The late steps get the most care; that is where a stranded learner has invested
  the most.
- **A worked example comes before the learner's attempt,** and a hidden answer names the likeliest
  wrong answer and its cause: from people who do the work where you have it, otherwise your best
  inference, recorded as unverified in `facilitator/claims.md`.
- **Plain is not simplistic.** Write to two facts about the reader in the settings: how little they
  know of this subject, which sets how plainly you explain, and how capable they are in their own
  work, which sets the register. Never let the first lower the second. Test each sentence: would
  you say it this way, in person, to that reader? Name their work as they name it, in titles,
  headings and file names too: an auditor's evidence review is not "paperwork". Praising a simple
  act, or explaining what their own job taught them, talks down.
- **Say what a step will change, as reassurance.** Before the first step that changes something,
  say plainly what it will and will not change, as the tool's own documentation does. Add no
  caution, restriction or judgement test (no "only if you are sure", and no look-only units, which
  leave the learner nothing to do) unless the tool itself requires it or the requester asked for
  it. Teach a permission request as the tool's documentation teaches it, reassuringly: look at
  what it will do, allow it when it matches what you asked, skip it when it doesn't; skipping is
  safe (for VS Code: vscode-docs `docs/agents/run/approvals.md` and
  `docs/agents/concepts/trust-and-safety.md`, read 2026-09-30). Leave out options a beginner
  doesn't need. The build fails on the commonest cautions (CAUTION).
- **Less is more.** A page carries what the next action needs. The elements these rules require
  come first, each in the least intrusive form that serves its moment; answers, definitions and
  help open on request. Fix by changing or removing before adding, and judge a cut against the
  whole page: each element's job, the moment it serves, and what depends on it.
- **Nothing invented.** No policy, contact, system name or screen label you have not seen, and no
  page of organization defaults. What the tool does, and how it is set up, comes from its vendor's
  current documentation, read with the date, never from memory or an older kit: a tool's setup
  changes between versions. Where a setting the page leaves alone changes what the screen shows (in
  VS Code, the **Session Target**, Local or Copilot, lists different built-in agents, and an
  experiment can change its default), the page names only what every value shows, or has the
  learner select the value it assumes. A screen or step you have not seen is a marked blank (see below), with
  what to do meanwhile beside it. The way to get help is never a blank and never a person who gave
  the learner the training: it is the help beside the learner and the kit's help page,
  `troubleshooting.md`. The build fails on "ask whoever gave you the training" and its like
  (WHOTOASK).
- **Dated facts go stale.** A deadline, target or version stated in the kit is recorded with its
  date in `facilitator/claims.md` and rechecked before every release; once it has passed, reword
  or remove it.
- **The recipes are practice.** Each is a worked example of one kind of task.
- **The kit's practice data is made up.** No real people, customers, systems or addresses in any
  example or practice file the kit ships. Learners may use their own work files; the kit sets no
  rule on which. An example is labelled as an example, never dressed up as a particular person's
  or role's job.
- **No learner categories.** Content is never branched or labelled by kind of learner: every
  learner reads the same pages.
- **Progress stays with the learner.** It is kept in their own browser and shown to no one else:
  which units they have completed, the page and step they last read, and what they wrote in the
  note boxes and ratings. The workbook page gathers their notes and lets them download or print a
  copy, which is the only way they leave the browser.

## Where things are

| Path | What it is |
|---|---|
| `README.md` | The programme's home page: the trainings, help, more. It never says how to read or get the kit (see "The learner's way in is the web pages") |
| `getting-started/` | The beginner training: its `README.md` (home: what it needs from earlier trainings, if anything; what you will be able to do; the path; before you start), its units, `workbook.md` (the page that gathers the learner's notes; the build fills it), and `how-to/`, its practice recipes |
| `troubleshooting.md`, `glossary.md` | Help for every training: the help page (stuck requests, problems by when they happen, then common questions under "Questions") and the words. One help page, not a separate questions page: a learner looks in one place |
| `explanation.md` | Background: why the subject works as it does; read after a lesson |
| `CHANGELOG.md` | What's new: the kit's versions, newest first. The kit's version is its newest entry |
| `sample-files/` | The reference copy of the made-up practice files the requests on the path have the assistant create; for maintainers, not built into pages or downloaded |
| `facilitator/` | For maintainers; not built into pages. `claims.md` is the claims register (every factual sentence and its source), and `BLANKS.md` is generated |
| `read-in-browser/` | The web pages for the whole kit. **Generated: never edit them.** Change the markdown and build |
| `maintaining/` | This guide, the page builder and its checks. `build_pages.py` starts with the settings you change |

## Where new content goes

| You are adding | Put it in | Also change |
|---|---|---|
| An answer only an organization can give | Only a maintainer's file in `facilitator/`, as a `[YOUR ORGANIZATION: ...]` blank; never a learner page (the build fails, ORGBLANK) | `facilitator/BLANKS.md` lists those blanks; the build regenerates it |
| Setup steps: access, accounts, installs | A new page at the top of the kit, `get-set-up.md`, in the order the learner does them, each step with a check | Add `"get-set-up.md"` to the `before` list of Getting started in `TRAININGS`. The build then puts it first. Link it from "Before you start" in `getting-started/README.md` and from "Getting set up" in `troubleshooting.md` |
| A recipe | `<training>/how-to/<name>.md`, in the recipe shape below | A row in the table in that training's `how-to/README.md`; the outline and the recipe pages follow that table, and the build stops if a recipe is missing from it |
| A problem and its fix | `troubleshooting.md`, under the heading for when it happens | |
| A question | `troubleshooting.md`, under "## Questions" | |
| A word learners will not know | A row in `glossary.md` | Add it to `GLOSSARY_TERMS` to link its first use on each page. A glossary word means one thing in this kit: if the subject uses a word the kit also defines (such as "check" for a payment) in another sense, rename the kit's term or take it out of `GLOSSARY_TERMS` |
| A unit in a training | A new page in that training's folder, and a line in the list under "The path" in its `README.md` | Its `path` and `time` in `TRAININGS`; the builder shows its number and time (see "Position and time are generated") |
| A new training | See below | |
| A sentence stating what the subject does, what a screen shows or what the organization requires | The page | A row in `facilitator/claims.md` with its source |
| Any change that reaches learners | Wherever it belongs | Its entry in `CHANGELOG.md`; see "Versions" below |

Keep setup steps out of the path: the path teaches, setup is done once before it.

## Adding a more advanced training

Advanced topics are trainings of their own, beside Getting started. Do not add them as units on
Getting started's path.

1. **Its folder:** a `README.md` shaped like `getting-started/README.md`: what you will be able to
   do, "The path" as a numbered list of its units (the builder adds each one's number and time),
   before you start. Its
   "Before you start" names what it needs from earlier trainings, each with a link to the training
   that teaches it.
   Copy `getting-started/workbook.md` into the folder too.
2. **Its units and recipes** in the same folder, written to the conventions below.
3. **`TRAININGS` in `build_pages.py`:** its `folder`, `name`, `level` (Intermediate or Advanced),
   `time` and `path`. A training
   with an empty path shows as "coming later"; filling the path makes it available.
4. **The list under "The trainings" in the kit's `README.md`:** one line, in the same order as
   `TRAININGS`, saying what it teaches and what it needs from earlier trainings.

Reuse the shared help pages and Getting started's words for things already taught, rather than
teaching them again.

## Decisions

Choices made with the people this kit is for, so they are kept when the kit is extended. Add one
line for each: the date, what was chosen, what it was chosen over, and what the choice left
unsettled. Choosing one version over another does not approve its details (its wording, its
examples); say which details are still open and how they will be settled. No later change undoes
a recorded choice, a new version of the training-kit skill included: where one would, keep the
choice and tell the people the kit is for.

- `[TO BE WRITTEN: date - decision - chosen over what - left open]`

## Corrections

Every correction the requester gives, recorded the moment it arrives, so none is acknowledged and
then dropped. The build prints how many rows are still open, and nothing is shown to the
requester while any row is open.

| Date | Their words | The general rule | Pages it touches | Where the rule is held | Applied |
|---|---|---|---|---|---|

"Where the rule is held" names a check, a review-checklist item or a line in this guide. "Applied"
is `yes` with the commit, or `open`.

## Page design

Decided, and implemented by the builder; keep it rather than redesigning it. Every page has:

- **A course outline on the left:** first, under "Trainings", every training in the kit, one row
  each with its level and progress and the current one marked, on every page, so a learner always
  sees the whole programme and can move to any training (an outline showing only the current
  training makes the others look absent). Below it the current training's name and how many units
  are done, each unit as one numbered row whose ring fills green when the unit is complete, the
  current unit opened to its steps with a marker on the step being read, and the training's
  recipes. Help pages are in a short "More" list at the bottom. Below a narrow width it folds behind an "Outline" button.
- **A breadcrumb across the top:** the kit, the training, the page, and the unit number.
- **Under a unit's title:** its time and number of steps, once.
- **At the end of each unit:** a "Next unit" block with a Continue button.
- **Always in view:** the outline and the breadcrumb stay on screen as the page scrolls; progress
  never scrolls away. The breadcrumb carries a thin progress line.
- **Nothing that repeats them:** no "On this page" list and no right-hand rail on unit pages; the
  outline already lists the unit's steps.
- **Coming back:** the training's home page marks each unit Completed, In progress or Not started.
  It lists the units once, each with what it does and its time, and has no separate start box.
- **Light and dark:** pages follow the reader's system theme, with a switch in the header.
- **The learner's notes:** a box under each note's question, a line saying the answer is kept in
  this browser and is also in the workbook, and the workbook page itself, which prints without the
  outline, header and buttons.

It follows Microsoft Learn with a persistent outline, because learners return days later and need
to see where they are and what is done without searching. Position and progress are said once, in
the outline and the breadcrumb; do not repeat them on the page.

**Progress is by unit,** as on Microsoft Learn. Every unit on a path ends with a button: Continue,
or on the last unit Back to the training. Selecting it marks the unit complete and then opens the
next page; a unit with no numbered steps works the same way. A line under the button says so, and
on a completed unit offers "Mark as not complete". Steps have no checkboxes: a box on every step
turns reading into bookkeeping and pulls the eye from the instruction, while a unit is the size of
thing a learner returns to. The outline, the breadcrumb and the training's home count completed
units only. Kits built before progress was by unit kept a tick per step in the browser; those are
ignored, so a learner who ticked steps under an older build starts again with no units complete.

**The look is quiet,** so that nothing on the page is louder than the step the learner is doing.
One accent colour marks links and where the learner is; green appears only on a completed unit. A
check is its text led by a bold "Check:" with a thin rule beside it, not a coloured panel.
Outline rows are one line each and wrap when a name is long,
and steps are separated by space, not lines. The look meets measured standards, not a judgement by eye: text meets
WCAG 2.2 AA contrast (4.5:1) and every edge or mark that carries meaning 3:1, in light and dark;
seven type sizes and spacing on a 4-pixel grid; every click target at least 24 pixels; and each
step of a unit fits on one screen, beside another window too.

**The page is compact by choice.** The text column is as wide as the breadcrumb, 720 pixels or
about 100 characters a line, and steps, paragraphs and lines are set close. This is wider than the usual reading measure of 60
to 75 characters on purpose: a column that narrow leaves a wide screen mostly empty and makes a
unit feel sparse. Body text stays
at the browser's default size, so it follows each reader's zoom. If you change the look in
`build_pages.py`, measure these again.

## How a page is written

The builder reads these conventions. Anything else is ordinary markdown.

| Write | What the learner gets |
|---|---|
| `# Title` on the first line | The page title and its name in search |
| `## 3. Do something` on a unit page | A step, listed under its unit in the outline, where a marker follows the step being read. The page shows its name only (see "Step headings are never numbered on screen"). Steps are never ticked: progress is by unit (see "Page design") |
| `> request text`, consecutive `> ` lines forming one request | A prompt for the assistant, shown line by line, with a Copy button that keeps the line breaks. How to write one is under "Prompts" |
| `<!-- tool -->` on the line before a prompt | Text to paste into the place practice happens, labelled with `PRACTICE_PLACE` |
| `<!-- tutor -->` on the line before a prompt | A help question, labelled "Ask" and the `ASSISTANT` setting |
| `<!-- frame -->` on the line before a prompt | An example of a request the learner writes themselves (see "Prompts", rule 6), shown without a Copy button. The text around it says where they write it |
| A paragraph starting `**Important:**` | A boxed callout, for a fact that changes what the learner does later and would otherwise leave them believing something wrong (where a thing they made works, for example). Never a warning or caution. At most one per step; the build fails on two (CALLOUT) |
| A paragraph starting `Check:` | A check: what the learner should see, led by a bold "Check:" |
| A paragraph starting `Check your answer:` or `Answers:` | An answer hidden until the learner opens it. Everything after it, up to the next heading, `<!--` marker or prompt, is in the answer too. An answer to several cases is a list after the line, one case to an item, led by the case in bold (ANSWERBLOB) |
| A paragraph starting `Example:` or `Example, <what it shows>:` | A worked example, set apart, with the words before the colon as its label |
| `` `[YOUR ORGANIZATION: what goes here]` `` | A marked blank for the organization to fill, allowed only where "Where new content goes" puts it (ORGBLANK) |
| `` `[TO BE WRITTEN: what goes here]` `` | A marked placeholder for content not written yet |
| `[text](other-page.md)` | A link to that page in the web version. Links are relative to the page's own folder |
| `[text](https://...)` or `[text](mailto:...)` | A link out of the kit, such as to the tool's own screen, its help, or a support channel |
| `<!-- more: label -->` on its own line, then anything, then `<!-- /more -->` | Everything between, folded under the label until the learner opens it. What may fold is under "What a step shows" |
| A numbered list that starts at a number above 1, such as `4. ` after a prompt | The list carries on from that number, so a step's actions stay one numbered sequence around its prompts |
| A list item followed by lines indented under it that start `- ` or `1. ` | A list nested inside that item. Indent the nested lines to line up with the item's text (two spaces under `- `, three under `1. `) |
| `**bold**` around a link, or around text and a link together | Bold that includes the link |
| `<!-- note -->` on the line before a paragraph | The paragraph as a question, with a box under it for the learner's answer, kept as "Progress stays with the learner" says and gathered in the training's workbook. Use one wherever a step asks the learner to write something down, ending the question with a colon. An answer is tied to the step the note sits under and its place among that step's notes: rewording the question keeps learners' answers, but renaming the step or moving the note shows them an empty box |
| `<!-- rate -->` on the line before a list | Each item with a choice of "I can do this", "With the page open" or "Not yet", kept and gathered like a note. For the objectives at the end of a path, in the same words as the training's home page. The list ends at its first blank line |
| `<!-- workbook -->` on its own line | Where the build puts every note and rating from the training's pages, under the unit and step each came from, with Download and Print buttons. Only in a training's `workbook.md` |
| `[text](../sample-files/name.csv)` | A link to a practice file or any other file in the kit |
| `![what it shows](images/name.png)` on its own line | A picture, such as a screen with the control to use. Keep pictures in an `images` folder beside the page; describe what matters in the text as well, for readers who cannot see it |

**The first unit on a path is an Introduction** that grounds the learner before any doing, as every
Microsoft Learn module does (Gagné's first events, Ausubel's advance organizer): the real situation
they are in and why it matters to them now; a short map of the few ideas the path uses, each named
once in plain words; what they will be able to do; and how the path is laid out. A few minutes to
read, no practice, no lecture. Without it the first unit starts cold. It never repeats the
training home's objectives or path list; if it has nothing to say beyond them, it is not a unit,
and the home carries it.

**The last unit on a path** ends on its practice, then a section headed
`## You have finished the path`, saying what the learner can now do, then a rating list of the
training's objectives (`<!-- rate -->`). When every unit is done, the training's home page links to
it. No unit asks the learner to commit to a task or to report back afterwards, and no closing unit
plans their week (the build fails on "this week": THISWEEK).

**Every training has a `workbook.md`** once any of its pages has a note or a rating; the build stops
without one. It appears in the outline under More as the page's title. Copy it from
`getting-started/workbook.md` for a new training.

**A recipe** is optional practice for after a training is finished, and its index and the
training's home say so. It has, in order: **You end with**, **You need** (what must be open, never
a list of units to have done first), **When**, numbered steps, a **Check:** paragraph, and a line
pointing to `troubleshooting.md`.

## Writing

Follow the writing standard in the settings. For a self-paced procedural page for people new to the
subject, the calibration is set by the audience and the kind of document, not by anyone's taste:
**plain-language concision.** Cut every word that is not doing work; use the short word; one idea
per sentence (plain language as in Zinsser and the Microsoft Writing Style Guide). **One principled
exception:** keep the reassurance and orientation a first-timer needs: what an action will and will
not change, what they may ignore for now, where they are and how to get back. Those sentences are
doing work. They reassure; they do not warn. Beyond that:

- **Names lead.** Every label that takes the learner somewhere (the kit's and each training's name,
  unit titles, step headings, link text, outline and menu items) says what they will do or get
  there, in their words, and makes sense to someone who does not yet know the subject's terms:
  "Read your application's coverage status", not "The first lesson" or "Start here". A unit is
  named for what the learner does in it, never for where it sits in the order. A learner scanning
  the outline should know what each unit teaches (information scent). The starter's own titles and
  headings are stand-ins for this; the build counts any left. **Read the unit titles and step
  headings as a list, alone, as the outline shows them:** each step heading names what the learner
  does and to what, concretely, with the right doer and the product's term for the thing ("Have
  Copilot create a custom instructions file", not "Write instructions about the work"; "Turn the
  list into a table with a follow-up", not "Change the result with a follow-up"). A vague object
  ("the work", "a change", "one thing") or a doer the step doesn't have (the learner "writes" what
  Copilot creates) fails. A read of sentences does not catch these; run this as its own pass.
- Speak to the learner.
- A file type or term a non-technical reader may not know (a `.md` file, a CSV) is explained in
  one plain line where it first appears: in that step's fold or the glossary, not on the main
  path.
- Name each action as the learner performs it in the place practice happens, in the form the
  standard gives. In a screen-based tool that is the visible control and what to do with it; a
  keyboard shortcut, if given, follows the visible action. Use the words the learner sees on the
  screen ("On the **View** menu, select **Chat**"), checked on the screen itself: a vendor's
  documentation sometimes names an unlabelled icon as a menu, and a beginner cannot find it.
- A unit's name is its title, stated once. The menu and the training's home take it from the
  page, and every link that opens a unit uses that title; the build fails on any other wording,
  so renaming a unit cannot leave its old name behind.
- One idea to a paragraph, the important words first. Short sentences.
- A training's home page links everything the training holds, its recipes included, in its own
  text, not only in the menu.
- Learners are adults: no step that only proves what is self-evident, such as removing a thing and
  asking again to show it is gone. Say it in a sentence where the learner needs it.
- Do not add "Next:" lines to units: each unit ends with the page's own Continue button, which
  marks the unit complete and opens the next one. A learner who leaves by such a line has not
  marked the unit complete, and coming back sends them to it again.
- If this copy is published outside your organization, keep organization details out of it; they
  belong in your organization's own copy.

### The form of a unit

Write a unit the way the published hands-on exercises do. The training-kit skill keeps one as
`references/reference-exercise.md`; read it before writing a unit.

- **The unit opens** with why the work matters to the learner, in a short paragraph in their
  terms, then one sentence saying what they do in this unit, and anything it needs beyond the
  units before it (never its time or position: see "Position and time are generated"). A
  training's home lists what the learner needs before its units.
- **One name for the tool,** its own ("Copilot"), on every page; never a generic stand-in ("the
  assistant") that a page has to announce. For Copilot the build checks it (NAME, on when `TOOL`
  in `check_rulings.py` is set).
- **Each step opens** with one sentence saying why the learner does it.
- **Then numbered actions,** one action to a number, in the order the learner does them: where,
  then what. A label on the screen is in bold.
- **What the learner should see** follows the action as its own sentence, indented under it.
  The step's `Check:` comes after the actions.
- **Every sentence reads right the first time,** said aloud to the audience as the settings state
  it. A sentence that carries a condition, a result and an exception at once is split into
  sentences, never shortened.

A second way to do a thing, what a later unit adds, and a restatement go.

### What a step shows

A page is read at a glance before it is read in full. Each step shows only what the learner acts
on; the rest folds away (`<!-- more: label -->` to `<!-- /more -->`, opened on request). Measured
2026-10-03 from VS Code's agents quickstart (about 1,200 words in 9 sections, about 130 a section,
action lines of 15 to 25 words, 5 screenshots) and GitHub Skills' *Getting Started with GitHub
Copilot*, step 1 (1,197 words, 12 screenshots, the "missing?" help folded in two `<details>`):

| Shown | Standard |
|---|---|
| What the step does | In its heading and reason line, in plain words ("Create the practice folder", not "scaffold"); never only in a prompt or a fold |
| The step's reason | One line, 12 words or fewer |
| Actions | One to three, numbered, 25 words or fewer each |
| A picture | Wherever the learner must find something on the screen, cropped to that control: no menu open on options the text leaves out, nothing the audience could not read |
| The Check | Always visible, one line: checking is what the training teaches |
| Visible words in the step | About 130 at most |
| Folded | Explanations, what to do when something differs, practice and its answers. Never something every learner needs to finish an action, such as which program opens a file: that goes in the action |

Before a page goes to anyone, look at it in a browser at 1,440 pixels wide with the folds closed:
someone who has never seen it can tell in ten seconds what each step asks them to do.

### Time estimates

A unit's time is computed, not guessed: its visible words at 238 a minute (Brysbaert 2019, silent
reading of non-fiction), plus a minute for
each request the learner sends (typing or pasting it and waiting for the reply), plus half a
minute for each other action. Round to five minutes. A training's total is the sum of its units.
Write each time as the writing standard writes numbers; for the Microsoft Writing Style Guide,
words below 10 and numerals from 10 ("about five minutes", "about 15 minutes").

### Word budgets

Budgets are a ceiling a reviewer checks after the page is written, never a target to write
toward. Never shorten a sentence to meet one: a page over budget loses a step, an example or a
branch, not the words that make its sentences readable. Budgets are words of prose, prompts not
counted; `python maintaining/measure.py` from the kit folder prints every learner page against
them. They are what the published hands-on trainings
use (GitHub Skills' Copilot course, the Microsoft Learning lab, VS Code's agents quickstart,
GitHub's Copilot cookbook, and the help pages of GitHub Docs and VS Code Docs), measured
2026-10-02. A kit on another subject keeps them unless its settings table sets its own.

| Page | Budget | Where it comes from |
|---|---|---|
| The whole path of a training | 3,750 | The whole GitHub Skills course: 3,742 |
| A unit on the path | 950 | The longest Skills lesson page: 952; the lab's two Chat exercises: 950 |
| A step in a unit | about 90: why, the actions, what you see | VS Code's agents quickstart: 1,110 words over 12 steps |
| A training's home page | 500 | No reference page does this job; half a unit |
| A recipe | 300, or 400 with five prompts | GitHub's cookbook page: 390 words for four recipes; 100 words of prose a prompt |
| A troubleshooting entry | 110 | GitHub's Copilot troubleshooting page: 1,432 words, 13 entries |
| A question on the FAQ | 90 | VS Code's Copilot FAQ: 2,369 words, 27 questions |
| A glossary term | 28 | GitHub's glossary: 5,848 words, 206 terms |
| An idea on the explanation page | 100 | VS Code's agents concept page: sections of 86 to 162 words |

## Prompts

The prompts are the training: a learner judges a page by whether its prompt did what the page
said. These rules follow how the published Copilot and Claude Code trainings present prompts
(the Microsoft Learn labs, GitHub Skills, the VS Code docs, the Claude Code docs).

0. **One instruction to a line.** A prompt's sentences go on separate `> ` lines, in the order the
   assistant needs them: what to work on, what to make and where, what to leave alone. Lists inside
   it (a skill's instructions, a file's contents) are `- ` items on their own lines. The learner
   reads the request at a glance, and its parts show what a good request contains. Copy keeps the
   line breaks. A request run together as one block is a wall of text the learner has to parse
   before they can see what it asks. The build fails on a request over 8 lines or a line over 25
   words (PROMPTLINES). GitHub's prompt guidance for Copilot Chat says the same: break a complex
   request into simpler parts.
1. **A prompt the learner copies is sent as written.** It is a complete request in plain
   sentences. No part of it is for the learner to replace: no angle brackets, no square brackets,
   no "your" standing in for a value. The build fails on a prompt with an angle-bracket slot.
2. **A prompt on the path runs on the practice files the assistant created, named by their real
   names.** The learner's own files come after the worked prompt, in one sentence: the same request
   works on a folder of their own, named in the request instead.
3. **A prompt names its files and folders,** such as "the notes folder in sample-files", so it is
   complete on its own. Where the tool finds files itself, attaching them to the chat is
   optional, mentioned once in a fold, never a step. VS Code: "You don't need to identify every
   relevant file before you start... Explicit references are useful when you already know which
   information the agent should consider" (vscode-docs, `docs/agents/concepts/context.md`,
   read 2026-10-03).
4. **"This" only when it is visible.** "This folder", "this file", "this function" is allowed only
   when the thing is open or selected. With two folders open, say which.
5. **Text the learner supplies is pasted after the prompt.** When a prompt needs the learner's own
   text (an error message, a request to review), the prompt ends with a colon and the step says
   what to paste after it and then to press Enter.
6. **The learner's own request is written, not filled in.** Where the learner must write in their
   own words (their house rules, their question about the data), show one complete example first,
   then say: "Write yours in the same shape." The example carries `<!-- frame -->`, so it has no
   Copy button. A frame is a complete example, never a skeleton with gaps.
7. **Introduce a prompt with where it goes.** One short line, such as "In the chat box, enter:"
   or "Ask:", then the prompt in its own block with its Copy button.
8. **Every step has an observable result the learner sees on screen;** a prompt whose only result
   is a reply arriving, such as "What can you do with the files in the folder I have open?", goes.
   After a prompt, its Check follows "Every action has a check" above. Never a blanket caution
   that the assistant can be wrong (the build fails on one: AIWARNING); teach the technique that
   makes its work quick to verify, such as naming the file behind every item, once, with its
   purpose. Start here says once that the assistant's wording differs from run to run.
9. **A prompt that has the assistant write a file says "add or change no other file",** not only
   "change no other file". To read a file it can't open directly, an assistant may write a helper
   file beside the learner's own, and the step then has no clean Keep. The build fails on a
   writing request without it (SCOPE).
10. **A practice request that writes names its practice folder, never "the folder I have open",**
   and never replaces a file that already exists, so nothing from the training lands in a
   learner's real files (OPENFOLDER). Anything the training creates that shapes the tool's later
   answers (instructions, a skill, an agent) lives in the practice folder or is removed at the end,
   and the page says in one line where it applies (this folder only, or everywhere) and how to get
   the other.

## Build and check

From the kit's folder:

```
python maintaining/build_pages.py
```

It needs Python 3 and nothing else. It rebuilds every page in `read-in-browser/`, then checks them,
and ends with "All checks passed." It stops and says why when:

- a page's words differ from its markdown;
- a link or a jump within a page leads nowhere;
- a prompt is missing its Copy button, or has one it should not;
- a prompt line carries an angle-bracket slot (reported as PROMPTSLOT, with the page and line);
- a learner page is not in any menu, so learners could not reach it;
- the list under "The trainings" in `README.md` does not match `TRAININGS`, or a training's list
  under "The path" does not match its `path`;
- a picture or a linked file does not exist;
- a page's numbered steps do not run 1, 2, 3 in order (renumbering is not enough: check the order
  still follows the task), or a step heading shows its number on screen (STEPNUMBER);
- a page writes a unit's position, such as "Unit 4 of the path" (UNITPOSITION);
- a learner page breaks a rule in `check_rulings.py`, such as a time typed in the text
  (TIMEINTEXT). An empty `RULED` there checks every learner page; list a page not yet rebuilt
  in `EXEMPT` until it is. `TOOL` turns on the rules that hold for one tool only;
- `CHANGELOG.md` is missing, its newest entry's heading is not in the form below, a date is not a
  real date or is in the future, or the entries are not newest first.

It also prints a NOTE, without stopping, when pages changed after the newest `CHANGELOG.md` date.

Fix the markdown, never the pages, and build again. Then open `read-in-browser/README.html` in a
browser and walk what you changed as a learner would, in a window as narrow as one beside the tool
they practise in. Keep the markdown and the rebuilt pages together in the same change.

Without Python, you can still change the markdown, but the web pages will not show it. Say so when
you hand the work over.

## Versions

The kit's version lives in one place: the newest entry in `CHANGELOG.md`, which learners read as
"What's new". Each entry is a heading, `## 1.2 - 2026-09-24` (the version, a space, a hyphen, a
space, the date it reaches learners), then short plain bullets of what changed for them, saying
when someone who already took a training should look again. Newest first.

- **Every change that reaches learners gets a new entry.** Raise the minor number (1.2 to 1.3) for
  content changes; raise the major number and reset the minor (1.3 to 2.0) for a restructure, such
  as a new training or a reordered path.
- **The first release** fills in the `0.1` entry's placeholders. Versions stay below 1.0 while the
  kit goes to pilot learners only; the first release to everyone is `1.0`.
- **What the pages show:** the version at the foot of every page, linked to What's
  new, and each page's "Last updated" date. That date is the last commit that changed the page's
  markdown when the kit is kept in git (today, if it has changes not yet committed); otherwise it
  is the newest `CHANGELOG.md` date. It never comes from the file's own date, which copying resets.

## Before you hand it over

- The build ends with "All checks passed." A kit with any `[TO BE WRITTEN: ...]` placeholder left
  is a draft; the build counts them. A draft goes only to named pilot learners, never to everyone.
- A change that reaches learners has its `CHANGELOG.md` entry (see "Versions"), and the build
  printed no NOTE about pages changed after it.
- You walked the changed pages in a browser. If you changed a unit on a path, you marked the unit
  complete by selecting Continue at its end, and saw it show complete in the outline, the
  breadcrumb and the training's home, with the home offering to continue at the next unit.
- What you changed still keeps "The rules that do not change", "Nothing invented", "The kit's
  practice data is made up" and "The learner does every practice step" in particular.
- Every choice made with the people the kit is for is under "Decisions", and its rule held.
