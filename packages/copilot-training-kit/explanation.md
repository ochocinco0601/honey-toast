# Why this assistant is different from the one you already have

You already have an assistant in your office suite; in many organizations it is Microsoft 365
Copilot. It reaches across the content your organization shares: mail, chats and channels,
meetings, files people have sent each other, your own cloud drive. It works inside those apps,
and it is the right tool for that. This training does not replace it.

The assistant in this training, GitHub Copilot inside Visual Studio Code, works on a folder of
files on your machine, and it can act on them: create, move, rename, transform, run a small
program, write a document, and leave all of that in the folder for next time. The two are not
better and worse; they are for different things. **Reach across shared content is the office
assistant's strength. Acting on a folder of files you are working on is this one's.**

What this training is about, in three lines, the same three the session closes on:

1. Bring the assistant to your own work: your files, your exports, an application you support.
2. It acts, and it asks first.
3. Check what it says against the file it names.

Two words to fix. This training calls VS Code a **workbench**: think of a table you lay your
work out on and leave it there between sittings. A folder of files sits open on it, and the
assistant can read them and act on them. And a **chore** is one piece of file work from start to
finish: organize a folder, summarize a set of notes, analyze one export.

Below are the ten ideas the training rests on. Each names the idea, says what changes for you,
gives one sentence to remember, and points at where in this kit you do it. They build in order.

## 1. It meets your work where it already is

Your work already lives in two places: the shared content your office assistant reaches, and the
files you actually work on, such as downloads, an export a system produced for you, your notes,
a folder someone sent you. This training is about the second place. Nothing here asks you to move
your work into a new system. Put a folder of files on the workbench, from wherever they came, and
the assistant comes to it. If a system you use every day has no direct connection yet, the export
you already make is enough to start with.

To remember: bring the assistant to your existing work, not your work to a new tool.
In the kit: every how-to starts from a folder you already have.

## 2. The workbench

VS Code is a workbench. Open a folder and everything in it is on the bench. The assistant can
read those files, write new ones, rename, move and organize them. Come back tomorrow and the
folder is still there, with what you and the assistant made. Work accumulates in one place, in
files you own, instead of being scattered across conversations and pasted answers.

To remember: a conversation produces answers; a workbench accumulates work.
In the kit: `README.md` step 5; `lesson-application.md` step 7.

## 3. The assistant has hands

A conversation gives you advice and drafts. This assistant does the chore on the files in front
of it. Ask for a folder and the folder appears. Ask it to sort thirty downloads into three
folders by type and it does. Before it acts on your machine it asks first, unless you choose the
option it offers to allow commands for the rest of the session. That question is the safety
feature, not an obstacle.

To remember: it does not draft advice; it does the chore.
In the kit: `README.md` steps 5 and 6; how-to `organize-a-folder.md`.

## 4. You direct; it operates the tool

You do not learn the developer tool. You say what you need, in your words, and the assistant runs
the tool: it fetches an application's files, it finds the setting, it opens the file. When you do
not know how to do something in VS Code, ask the assistant. It either does it or tells you the one
step to take. The tool is a means; the assistant is the operator.

To remember: when you do not know how, ask it how.
In the kit: `lesson-application.md` step 2, fetching by asking; `faq.md`, "How did you get the chat panel there?"

## 5. House rules

In conversation you tend to restate your team's standards each time you start one: the fiscal
year, the status categories, the words you never use, the shape a summary should take. On the
workbench you write them once, in an instructions file in the folder. The assistant reads it with
every request you make there. Ask for a review of a document and the rules apply without you
restating them.

To remember: explain team standards once.
In the kit: how-to `set-house-rules.md`.

## 6. Skills: a written way of doing one job

The assistant knows a great deal in general. It does not know how your team wants a job done. A
**skill** is a short instruction file that says how: how to write a status briefing, how to
document an application, how to analyze a set of tickets. Your organization may provide some;
see `skills.md`. You can ask the assistant to write one, then correct it until it fits.

Why skills exist: the assistant already knows how a status briefing is generally written. The
skill says how your team writes one.

To remember: general knowledge, plus your way of doing it.
In the kit: how-to `ask-for-a-skill.md`; `lesson-application.md` step 4.

## 7. Disposable tools

A job you would never do by hand, across hundreds of files, usually waits for someone who can
write a program. On the workbench the assistant is that someone: it can write a small program for
a one-time job, run it, and throw it away: rename two hundred files by a pattern, replace a term
across a whole folder, pull every date out of thirty notes into one table. You never see the
program. You asked for the outcome, and it asked your permission before running anything.

To remember: you do not need to know how to code to take advantage of code.
In the kit: how-to `change-many-files-at-once.md`.

## 8. The loop

A conversational answer is usually one pass. The assistant on the workbench can work a loop: do
the step, check the result, fix what failed, continue. You give it the finish line and what
"done" looks like; it iterates. You review what it flags, not every item.

To remember: state the finish line, not the steps.
In the kit: how-to `analyze-an-export.md`; how-to `summarize-a-folder-of-notes.md`.

## 9. Check the receipts

The assistant is sometimes confidently wrong. The habit that makes it safe to use is one move.
Ask it to cite the files it used, and it names them. Open one. See whether the file says what the
assistant said. An answer with no source is a guess. This is what you do with the output before
you use it for a decision.

To remember: an answer with no source is a guess.
In the kit: `README.md` step 6; `lesson-application.md` step 3; `lesson-your-files.md` step 5; every how-to ends with a check.

## 10. Where a repository fits

A repository is a folder holding an application's source code and supporting files, kept in a
shared system. For an engineer it is where work happens. For everyone else it is a system you can
ask questions of: what it does, what it depends on, who uses it, in plain language, with the files
as evidence, and without waiting for an engineer to be free. Here the assistant only reads;
nothing you ask changes the application. And a repository describes what the application is meant
to do, not what is running right now, so treat its answers as a first draft of the truth. Nothing
new is needed for this: the same workbench, the same assistant, the same check. The folder is
just bigger.

To remember: an on-demand briefing on a system you do not own.
In the kit: `lesson-application.md`.
