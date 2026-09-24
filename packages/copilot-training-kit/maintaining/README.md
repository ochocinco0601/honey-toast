# Maintaining these trainings

For whoever changes or extends this kit, usually an AI assistant session asked to add to it. Read
this whole page before you change anything. Learners never need this folder.

This kit is a programme of trainings. **Getting started** is the beginners' training everyone takes
first. More advanced trainings, such as skills in depth or agents, sit beside it in the same kit and
share its help pages, practice files and web version.

## The rules that do not change

- **Each training teaches a learner working alone,** whether or not they attended a live session.
  Every page must work with no presenter in the room.
- **The learner does every practice step.** They type or paste each request into the chat and send
  it, because operating the assistant is the skill being taught. The pages never send anything
  anywhere: every prompt is a Copy button. The assistant may explain, diagnose or check, but no page
  or prompt does a practice step for the learner.
- **It is for people who do not write code.** Plain words, second person ("you"), and a check after
  every action saying what the learner should see.
- **The recipes are practice.** Each is a worked example of one kind of file work, not a toolbox
  for daily use.
- **It states no organization policy.** Where an organization must supply an answer, leave a marked
  blank (see below). Never invent a rule, a contact or a system name.
- **Practice data is made up.** No real people, customers, systems or addresses in any example or
  practice file.
- **Compare assistants by what each is for,** never by what the other one lacks.
- **Progress stays with the learner.** It is kept in their own browser and shown to no one else.

## Where things are

| Path | What it is |
|---|---|
| `README.md` | The programme's home page: the trainings, help for every training, how to read them |
| `getting-started/` | The beginners' training: its `README.md` (home: what you will be able to do, the path, before you start), its four units, and `how-to/`, its practice recipes |
| `skills-in-depth/`, `agents/` | Placeholder trainings: a `README.md` each, to be written |
| `troubleshooting.md`, `faq.md`, `glossary.md` | Help for every training: problems by when they happen, questions, words |
| `explanation.md` | Why this assistant is different; background, read after a lesson |
| `skills.md` | The organization's skills: mostly blanks for the organization to fill |
| `sample-files/` | Made-up practice files; not built into pages |
| `facilitator/` | For presenters of a live session; not built into pages. `BLANKS.md` there is generated |
| `read-in-browser/` | The web pages for the whole kit. **Generated: never edit them.** Change the markdown and build |
| `maintaining/` | This guide, the page builder and its checks. `build_pages.py` starts with the settings you change |

## Where new content goes

| You are adding | Put it in | Also change |
|---|---|---|
| An organization's answer to a blank | The blank itself, in place. `facilitator/BLANKS.md` lists every blank; the build regenerates it | The same question is often asked in more than one file, including `facilitator/`: find each in `BLANKS.md` and answer them all. Read the sentence around each so it still makes sense |
| Setup steps: installing VS Code, requesting access, network or proxy setup, extensions | A new page at the top of the kit, `get-set-up.md`, in the order the learner does them, each step with a check. A step that uses the chat says briefly how to open it, since Start here comes later | Add `"get-set-up.md"` to the `before` list of Getting started in `TRAININGS`. The build then puts it first: the training's Start button and Next links go through it to Start here. Do not add a Next link of your own. Link it from "Before you start" in `getting-started/README.md` and from "Getting set up" in `troubleshooting.md` |
| The organization's skills | The blanks in `skills.md`: for each skill, its name, the one job it does, and a prompt that uses it | Link to the organization's own catalogue rather than copying it. Once filled in, drop "(it fills this in)" from its menu name in `MENU_AFTER`, and "once your organization has filled it in" where `getting-started/README.md` and `getting-started/first-real-chore.md` point to it |
| A recipe | `<training>/how-to/<name>.md`, in the recipe shape below | A row in the table in that training's `how-to/README.md`; the menu follows that table |
| A problem and its fix | `troubleshooting.md`, under the heading for when it happens | |
| A question | `faq.md` | |
| A word learners will not know | A row in `glossary.md` | Add it to `GLOSSARY_TERMS` to link its first use on each page |
| A unit in a training | A new page in that training's folder, and a line in the list under "The path" in its `README.md` | Its `path` and `time` in `TRAININGS`; the "Unit N of the path" line at the top of later units |
| A new training, or writing up a placeholder one | See below | |
| Material for presenters | `facilitator/` | |

When a new page answers a question an existing blank asks, replace that blank with a link to the
page, so each answer is filled in one place. If it answers only part of the blank, link that part
and keep the rest as a smaller blank.

Keep setup steps out of the path: the path teaches, setup is done once before it. A setup prompt the
learner pastes, such as one that configures a proxy, is written as a prompt like any other.

## Adding a more advanced training

Advanced topics are trainings of their own, beside Getting started in this kit. Do not add them as
units on Getting started's path, and do not grow `skills.md` into a course; it stays the shared
reference.

To write one up, starting from its placeholder folder or a new one:

1. **Its folder:** a `README.md` shaped like `getting-started/README.md`: what you will be able to
   do, "The path" as a numbered list of its units with their times, before you start. Its
   "Before you start" names Getting started as the training to finish first, and links to it.
2. **Its units and recipes** in the same folder, written to the conventions below.
3. **`TRAININGS` in `build_pages.py`:** its `level`, `time` and `path`. A training with an empty
   path shows as "coming later"; filling the path makes it available.
4. **The list under "The trainings" in the kit's `README.md`:** one line, in the same order as
   `TRAININGS`, saying what it is for and who should take it.

Reuse the shared help pages and Getting started's words for things already taught, rather than
teaching them again. The side menu, the top bar and progress follow from `TRAININGS`; each training
has its own path and progress, and the top bar shows which training the learner is in.

## How a page is written

The builder reads these conventions. Anything else is ordinary markdown.

| Write | What the learner gets |
|---|---|
| `# Title` on the first line | The page title and its name in search |
| `## 3. Do something` on a unit page | A numbered step with "Mark this step done" and progress. Only units on a path track progress; numbered steps elsewhere, such as a setup page, are plain headings |
| `> request text` on one line | A prompt with a Copy button |
| `<your folder>` or any `<blank>` inside a prompt | A highlighted blank the learner replaces. `<your folder>` fills in from the folder box on the page |
| `<!-- frame -->` on the line before a prompt | A prompt the learner writes themselves, with no Copy button |
| `<!-- tutor -->` on the line before a prompt | A help question for the assistant, labelled "Ask the assistant" |
| A paragraph starting `Check:` | A check box: what the learner should see |
| A paragraph starting `Check your answer:` or `Answers:` | An answer hidden until the learner opens it |
| `` `[YOUR ORGANIZATION: what goes here]` `` | A marked blank for the organization to fill. A whole prompt the organization supplies is written `` > `[YOUR ORGANIZATION: the prompt that ...]` ``; it shows as a blank with no Copy button |
| `` `[TO BE WRITTEN: what goes here]` `` | A marked placeholder for content the training's authors have not written yet |
| `[text](other-page.md)` | A link to that page in the web version. Links are relative to the page's own folder |

A prompt that names a file in the kit gives its folder, such as `getting-started/start-here.md`,
because learners open the whole kit in VS Code.

**A recipe** has, in order: **You end with**, **Before you start**, **When**, numbered steps with
their prompts, a **Check:** paragraph, and a line pointing to `troubleshooting.md`. Copy an existing
recipe, such as `getting-started/how-to/analyze-an-export.md`, as the pattern.

## Writing

- Speak to the learner. Say what to do, then what they should see.
- One idea to a paragraph, the important words first. Short sentences.
- Every prompt is complete and works when pasted, apart from its marked blanks.
- Add as little as the change needs. Before adding a paragraph, look for one it replaces.
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
  under "The path" does not match its `path`.

Fix the markdown, never the pages, and build again. Then open `read-in-browser/README.html` in a
browser and walk what you changed as a learner would, in a window as narrow as one beside VS Code.
Keep the markdown and the rebuilt pages together in the same change.

Without Python, you can still change the markdown, but the web pages will not show it. Say so when
you hand the work over.

## Before you hand it over

- The build ends with "All checks passed."
- You walked the changed pages in a browser. If you changed a unit on a path, you marked a step
  done and saw the progress in the top bar move.
- Every organization answer you did not have is a marked blank, not a guess.
- No real names, customers, systems or addresses in anything you added.
- Every practice step is still one the learner performs.
