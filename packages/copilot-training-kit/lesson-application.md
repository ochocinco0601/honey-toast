# Lesson: an application you do not own

For everyone, after `lesson-your-files.md`. In the training session you watch the presenter's
screen and follow on this page; type along if your setup is ready and you have an application's
address. If anything on your machine does not work, note it and keep watching; the lesson still
makes sense. About twenty-five minutes together for steps 1 to 4 and the check in step 6; steps 5
and 7 are yours afterward, on your own.

By the end you will have brought an application's code onto your computer, asked it what it does
and who uses it, had a set of pages about it generated, explored those pages by the questions you
actually have, and checked one important claim against the file it came from.

You will not read code. You will read what the assistant and the generator write about the
code, and check that the file they point at says what they say it says.

## 1 of 7. Get the application's address

The code for an application is kept in a repository: one folder of its source files and
supporting files, held in a shared system where changes are tracked and reviewed. You need the
address of one you are allowed to open; your organization decides which, usually your own
team's. An address looks like a web link that ends in the application's name.
`[YOUR ORGANIZATION: which repositories a learner may open, and where to find the address]`

On your own, with no address yet, and only if your organization allows fetching from the public
internet: any public sample application works; a common one is the Bank of Anthos sample at
`https://github.com/GoogleCloudPlatform/bank-of-anthos`. Check that policy before you try.

## 2 of 7. Bring it onto your computer, and check three things

In the chat, type the following, replacing `<address>`, brackets and all, with the address:

> I need to inspect this application. Clone the repository at `<address>` into the `practice` folder so we can analyze it.

"Clone" means make a local copy. A button appears inside the reply asking whether to allow the
command; click Allow. A new folder appears under `practice` on the left and fills with the
application's files. You did not learn any command to do that; you asked, and the assistant
operated the tool. If it fails, see `faq.md`, "Setup: the clone fails".

Check three things before going on:

1. The application's folder shows on the left, with files inside it.
2. A simple question gets a reply:
   > What kinds of files are in this application?
3. Your organization's documentation generator is present, if it provides one.
   `[YOUR ORGANIZATION: how to confirm the generator is installed]`

## 3 of 7. Ask what it is, and make it cite files

> What does this application do, what business problem does it solve, and who uses it? You sometimes make mistakes, so cite the files that support each part of your answer.

Read the answer in its three parts: what it does, the business problem it solves, who uses it.
Then do the one thing that makes this safe:

> Open the first file you cited and show me the lines that support the "who uses it" claim.

Click that file when it opens. You are not reading the code; you are checking that the words the
assistant quoted are really there. If they are not, or if part of the answer had no file behind
it, say so:

> That part is not supported by the file you named. Re-answer using only what the files say, and cite a file for every claim.

If you do not know what to ask, ask this:

> What questions should I ask you to understand this application?

If the answer is disorganized or does not make sense to you, say exactly that: "Organize your
response," or "That does not make sense to me; explain it." It redoes the work.

The answer gives you orientation. The repository gives you the evidence.

## 4 of 7. Generate a set of pages about the application

In the session the presenter uses your organization's documentation generator. On your own, use
it if you have it; otherwise use the plain-words prompt below.
`[YOUR ORGANIZATION: the command to run the generator, and what it produces]`

It reads every file in the application and writes a set of linked pages: what the application
is, how its parts connect, what it depends on, and which files a new owner should read first.

It takes five to ten minutes, not seconds. While it runs, the assistant shows its list of steps
and works through them; the moving indicator means it is still working.

What you are about to see in the session was generated before the session, because ten minutes
of waiting is not a good use of the room. Yours will take that long when you run it afterward;
start it and come back.

Without a generator, ask for the same thing:

> Write a set of pages in the `practice` folder about this application, starting with an index: what it does, its main parts, what it depends on and what depends on it, the business rules in the code, its data, how it handles errors, and which files a new owner should read first. Cite files on every page.

When it finishes, it names the first page, usually called index. Click it.

**If it shows as text with symbols, press Ctrl+Shift+V.**

The index is a table of contents; each line opens a page. Open the overview page first.

## 5 of 7. Explore by the question you actually have

This is where the pages become useful to you: to bring someone new onto the application, to plan
a change, to support an incident, to settle who owns what. Do not read everything. With the
pages open, ask the questions you would have asked the application's engineer:

- How does this application work end to end?
- What does it depend on, and what depends on it?
- What logic is built into the code that I would not guess from the outside?
- What could break if it changes?
- How is it configured, and how is it monitored?

Each answer should point at a page or a file.

If the chat panel has grown to fill the screen, drag its top edge down to see the pages again.

## 6 of 7. Check one important claim

Pick one claim from the pages that would matter if it were wrong: a dependency, a business rule,
who is affected when something fails. Ask:

> You say that [the claim]. Show me the file and the lines that support it.

Open the file. There are three kinds of claim, and you can tell them apart:

- **Found directly in the code**: a setting, a name, a connection to another system. You can see it.
- **Worked out from how the code calls other things**: one part hands work to another, in an order. You can follow it.
- **The tool's own interpretation**: what it thinks the code is for. It should be labelled as interpretation.

A claim with no file behind it is unsupported. Treat it as a guess, and say so to the assistant.

**Before you use anything from these pages for a change to production, a risk decision, or a
question of ownership, apply your own judgment.** The pages are a reviewed starting point, not
the truth.

## 7 of 7. Come back tomorrow

Close VS Code. Open it again: menu File, then Open Recent, then this folder. Everything is still
there, including the application and its pages. Start a new chat with the plus button at the top
of the chat panel; a new chat remembers nothing of yesterday's conversation, which is the point:
the folder remembers, not the chat. Ask:

> Read the overview page under `practice` and tell me the three things a new support engineer should know first.

Read the pages when you want the whole picture; ask the chat when you want one answer. Both are
there whenever you need them, and nothing you did yesterday was lost.

## What you can now do

Start with the repository. Ask one direct question for orientation. Generate the pages for a
structured understanding. Explore them by the question or decision in front of you. Trace
important findings back to the file they came from. Treat generated knowledge as a reviewed
starting point, not automatic truth. When it is wrong, and sometimes it will be, say what is
wrong and it redoes the work; checking it is the skill, not trusting it.
