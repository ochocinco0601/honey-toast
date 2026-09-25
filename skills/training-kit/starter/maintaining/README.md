# Maintaining these trainings

For whoever changes or extends this kit, usually an AI assistant session asked to add to it. Read
this whole page before you change anything. Learners never need this folder.

This kit is a programme of trainings that share their help pages, practice files and web version.
Where levels divide by experience, **Getting started** is the beginners' training everyone takes
first, and more advanced trainings sit beside it. Where they divide by role, each role has its own
starting training, side by side, and the kit's home page says which one to take.

## This kit's settings

Fixed when the kit was built. Every page is written to them; change one only on purpose, and then
review every page against it.

| Setting | This kit |
|---|---|
| Subject | `[TO BE WRITTEN: what the trainings teach]` |
| Audience | `[TO BE WRITTEN: who the learners are, by the work they do; what they know of this subject; how expert they are in their own work]` |
| Where practice happens | `[TO BE WRITTEN: the tool, screen or console; an assistant's chat; or, for a process, the cases, documents and decisions it works on]` |
| Help beside the learner | `[TO BE WRITTEN: who or what a stuck learner asks first, the person for what that cannot answer, and whether the help can read these pages]` |
| Outcome a week later | `[TO BE WRITTEN: what a learner does in their own work that shows the training worked]` |
| Writing standard and budget | `[TO BE WRITTEN: the standard the pages follow (the organization's editorial standard for instructional documents if it has one), and the budget: minutes per unit (the times in TRAININGS) and words per page]` |

The builder's own settings, at the top of `build_pages.py`, follow from this table: `PROGRAM_NAME`,
the programme's name; `PRACTICE_PLACE`, where practice happens; `ASSISTANT` and `ASSISTANT_CHAT`,
the help beside the learner and where a question for it is pasted; `KIT_OPEN_IN_ASSISTANT`,
whether that help can read these pages; and `STUCK_BUTTON`, whether each step offers a question to
copy for that help (turn it off when the help is a person). Keep them in step with the table.
Each applies to every page at once, so changing one also changes pages you have not yet rewritten
for it. `SKILL_VERSION` is not a setting: it records which version of the skill built the kit.

The builder also writes some sentences itself. When the audience, the place practice happens or the
help beside the learner differs from the defaults, reread these in `build_pages.py` and reword them:
the "Using a prompt" instructions (`how_to_use`), the prompt labels and the hint shown after
copying (`prompt_block`), the "Stuck on this step?" button and its question, the copy messages,
"Mark this step done", the outline's and the end-of-unit block's labels ("Start the training",
"Continue", "Next unit:", "End of the path", "Back to the training", "Not started" and the like),
the end-of-path message, and the page foot (`page_foot`). The builder's other
settings shape the menus and links: `TRAININGS` (each training's folder, name, level, time, path,
pages before unit 1, and `stuck_from`, the first step on a unit that offers "Stuck on this step?"),
`MENU_AFTER` (the help pages listed, in order, under "More" in the outline; its group names and
open flags are not shown), `GLOSSARY_TERMS` (words linked to the glossary) and
`UI_LABELS` (on-screen labels never linked, even when they contain a glossary word).

## The rules that do not change

- **Each training teaches a learner working alone,** whether or not they attended a live session.
  Every page must work with no presenter in the room.
- **The learner does every practice step,** in the place practice happens, because doing it is the
  skill being taught. Nothing is done or sent on their behalf; a prompt they paste has a Copy
  button. Help may explain, diagnose or check, but never does a practice step.
- **Every action has a check** saying what the learner should see, and every check compares against
  something they can see for themselves: the source, a second screen, the standard, a worked
  example. An assistant's or a tool's account of its own work is not a check, and neither is "you
  can say what it means".
- **Every step has a recovery route:** what to do when the check does not match, or a link to where
  that is covered. The late steps get the most care; that is where a stranded learner has invested
  the most.
- **A worked example comes before the learner's attempt,** and a hidden answer names the likeliest
  wrong answer and its cause: from people who do the work where you have it, otherwise your best
  inference, recorded as unverified in `facilitator/claims.md`.
- **Plain is not simplistic.** Write to two facts about the reader in the settings: how little they
  know of this subject, which sets how plainly you explain, and how capable they are in their own
  work, which sets the register. Never let the first lower the second. Test each sentence: would
  you say it this way, in person, to that reader? Name their work as they name it, in titles,
  headings and file names too.
- **Say what practising can change.** Before the first step in a live tool or process, say which
  actions only look and which change something, and keep the early units to actions that only
  look until a unit is about changing things. An action counts as look-only once someone has
  confirmed it on the screen or with the organization; until then it goes on the path as a marked
  blank, and the kit is released to a pilot only.
- **Less is more.** A page carries what the next action needs. The elements these rules require
  come first, each in the least intrusive form that serves its moment; answers, definitions and
  help open on request. Fix by changing or removing before adding, and judge a cut against the
  whole page: each element's job, the moment it serves, and what depends on it.
- **Nothing invented.** No organization policy, contact, system name or screen label you have not
  seen: a marked blank instead (see below), with what to do meanwhile beside it. The way to get help
  is never a blank: the help beside the learner, or whoever sent them the training.
- **The recipes are practice.** Each is a worked example of one kind of task.
- **Practice data is made up.** No real people, customers, systems or addresses in any example or
  practice file.
- **Progress stays with the learner.** It is kept in their own browser and shown to no one else.

## Where things are

| Path | What it is |
|---|---|
| `README.md` | The programme's home page: the trainings, help for every training, how to read them |
| `getting-started/` | The beginners' training: its `README.md` (home: what you will be able to do, the path, before you start), its units, and `how-to/`, its practice recipes |
| `troubleshooting.md`, `faq.md`, `glossary.md` | Help for every training: problems by when they happen, questions, words |
| `explanation.md` | Background: why the subject works as it does; read after a lesson |
| `CHANGELOG.md` | What's new: the kit's versions, newest first. The kit's version is its newest entry |
| `sample-files/` | Made-up practice files; not built into pages |
| `facilitator/` | For presenters and maintainers; not built into pages. `evaluation.md` is how the training is judged, `claims.md` is the claims register (every factual sentence and its source), and `BLANKS.md` is generated |
| `read-in-browser/` | The web pages for the whole kit. **Generated: never edit them.** Change the markdown and build |
| `maintaining/` | This guide, the page builder and its checks. `build_pages.py` starts with the settings you change |

## Where new content goes

| You are adding | Put it in | Also change |
|---|---|---|
| An organization's answer to a blank | The blank itself, in place. `facilitator/BLANKS.md` lists every blank; the build regenerates it | The same question is often asked in more than one file: find each in `BLANKS.md` and answer them all. Read the sentence around each so it still makes sense |
| Setup steps: access, accounts, installs | A new page at the top of the kit, `get-set-up.md`, in the order the learner does them, each step with a check | Add `"get-set-up.md"` to the `before` list of Getting started in `TRAININGS`. The build then puts it first. Link it from "Before you start" in `getting-started/README.md` and from "Getting set up" in `troubleshooting.md` |
| A recipe | `<training>/how-to/<name>.md`, in the recipe shape below | A row in the table in that training's `how-to/README.md`; the outline and the recipe pages follow that table, and the build stops if a recipe is missing from it |
| A problem and its fix | `troubleshooting.md`, under the heading for when it happens | |
| A question | `faq.md` | |
| A word learners will not know | A row in `glossary.md` | Add it to `GLOSSARY_TERMS` to link its first use on each page |
| A unit in a training | A new page in that training's folder, and a line in the list under "The path" in its `README.md` | Its `path` and `time` in `TRAININGS`. The breadcrumb shows each unit's number, so do not write it on the page |
| A new training | See below | |
| Material for presenters | `facilitator/` | |
| A sentence stating what the subject does, what a screen shows or what the organization requires | The page | A row in `facilitator/claims.md` with its source |
| A change prompted by evaluation results | Wherever the problem is | A line under "Revising from results" in `facilitator/evaluation.md` saying what was learned and what changed |
| Any change that reaches learners | Wherever it belongs | A new entry in `CHANGELOG.md`; see "Versions" below |

When a new page answers a question an existing blank asks, replace that blank with a link to the
page, so each answer is filled in one place.

Keep setup steps out of the path: the path teaches, setup is done once before it.

## Adding a more advanced training

Advanced topics are trainings of their own, beside Getting started. Do not add them as units on
Getting started's path.

1. **Its folder:** a `README.md` shaped like `getting-started/README.md`: what you will be able to
   do, "The path" as a numbered list of its units with their times, before you start. Its
   "Before you start" names Getting started as the training to finish first, and links to it.
2. **Its units and recipes** in the same folder, written to the conventions below.
3. **`TRAININGS` in `build_pages.py`:** its `folder`, `name`, `level`, `time` and `path`. A training
   with an empty path shows as "coming later"; filling the path makes it available.
4. **The list under "The trainings" in the kit's `README.md`:** one line, in the same order as
   `TRAININGS`, saying what it is for and who should take it.

Reuse the shared help pages and Getting started's words for things already taught, rather than
teaching them again.

## How a page is written

The builder reads these conventions. Anything else is ordinary markdown.

| Write | What the learner gets |
|---|---|
| `# Title` on the first line | The page title and its name in search |
| `## 3. Do something` on a unit page | A numbered step with "Mark this step done" and progress. Only units on a path track progress |
| `> request text` on one line | A prompt for the assistant, with a Copy button |
| `<!-- tool -->` on the line before a prompt | Text to paste into the place practice happens, labelled with `PRACTICE_PLACE` |
| `<!-- tutor -->` on the line before a prompt | A help question, labelled "Ask" and the `ASSISTANT` setting |
| `<!-- frame -->` on the line before a prompt | A request or entry the learner writes themselves, with no Copy button. The text around it says where they write it |
| `<your folder>` or any `<blank>` inside a prompt | A highlighted blank the learner replaces. `<your folder>` fills in from a folder box on the page. Blanks cannot nest: write `<name>`, not `<not sure, ask <name>>` |
| A paragraph starting `Check:` | A check box: what the learner should see |
| A paragraph starting `Check your answer:` or `Answers:` | An answer hidden until the learner opens it |
| A paragraph starting `Example:` or `Example, <what it shows>:` | A worked example, set apart, with the words before the colon as its label |
| `` `[YOUR ORGANIZATION: what goes here]` `` | A marked blank for the organization to fill |
| `` `[TO BE WRITTEN: what goes here]` `` | A marked placeholder for content not written yet |
| `[text](other-page.md)` | A link to that page in the web version. Links are relative to the page's own folder |
| `[text](https://...)` or `[text](mailto:...)` | A link out of the kit, such as to the tool's own screen, its help, or a support channel |
| `[text](../sample-files/name.csv)` | A link to a practice file or any other file in the kit |
| `![what it shows](images/name.png)` on its own line | A picture, such as a screen with the control to use. Keep pictures in an `images` folder beside the page; describe what matters in the text as well, for readers who cannot see it |

**The last unit on a path** ends with a section headed `## You have finished the path`, saying what
the learner can now do. When every unit is done, the training's home page links to it.

**A recipe** has, in order: **You end with**, **Before you start**, **When**, numbered steps, a
**Check:** paragraph, and a line pointing to `troubleshooting.md`.

## Writing

Follow the writing standard in the settings. For a self-paced procedural page for people new to the
subject, the calibration is set by the audience and the kind of document, not by anyone's taste:
**plain-language concision.** Cut every word that is not doing work; use the short word; one idea
per sentence (plain language as in Zinsser and the Microsoft Writing Style Guide). **One principled
exception:** keep the safety reassurance and the orientation a first-timer needs to act safely:
what an action will and will not change, what they may ignore for now, where they are and how to
get back. Those sentences are doing work. Beyond that:

- **Names lead.** Every label that takes the learner somewhere (the kit's and each training's name,
  unit titles, step headings, link text, outline and menu items) says what they will do or get
  there, in their words: "Read your application's coverage status", not "The first lesson" or
  "Start here". A learner scanning the outline should know what each unit teaches (information
  scent). The starter's own titles and headings are stand-ins for this; the build counts any left.
- Speak to the learner. Say where, then what to do, then what they should see.
- Name each action as the learner performs it in the place practice happens, in the form the
  standard gives. In a screen-based tool that is the visible control and what to do with it; a
  keyboard shortcut, if given, follows the visible action.
- One idea to a paragraph, the important words first. Short sentences.
- Every prompt is complete and works when pasted, apart from its marked blanks.
- Do not add "Next:" lines to units: the page's own Next link comes after the last step's "Mark
  this step done", and a line above it lets learners leave with that step unmarked.
- If this copy is published outside your organization, keep organization details out of it; they
  belong in your organization's own copy.

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
- a learner page is not in any menu, so learners could not reach it;
- the list under "The trainings" in `README.md` does not match `TRAININGS`, or a training's list
  under "The path" does not match its `path`;
- a picture or a linked file does not exist;
- a page's numbered steps do not run 1, 2, 3 in order (renumbering is not enough: check the order
  still follows the task);
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
- **What the pages show:** the version and its date at the foot of every page, linked to What's
  new, and each page's "Last updated" date. That date is the last commit that changed the page's
  markdown when the kit is kept in git (today, if it has changes not yet committed); otherwise it
  is the newest `CHANGELOG.md` date. It never comes from the file's own date, which copying resets.

## Before you hand it over

- The build ends with "All checks passed." A kit with any `[TO BE WRITTEN: ...]` placeholder left
  is a draft; the build counts them. A draft goes only to named pilot learners, never to everyone.
- A change that reaches learners has a new, dated entry in `CHANGELOG.md`, and the build printed
  no NOTE about pages changed after it.
- You walked the changed pages in a browser. If you changed a unit on a path, you marked a step
  done and saw the progress in the outline and the breadcrumb move.
- Every organization answer you did not have is a marked blank, not a guess.
- No real names, customers, systems or addresses in anything you added.
- Every practice step is still one the learner performs.
