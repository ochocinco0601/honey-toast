# Lesson: an application you do not own

Unit 3 of the path, after [Lesson: your own files](lesson-your-files.md). About twenty-five
minutes for steps 1 to 4 and 6; steps 5 and 7 are for later, when a real question comes up and the
next day.

**You need** the address of an application's code that you are allowed to open (step 1 says what
that is), and the `practice` folder from [Start here](start-here.md).
No address and nobody to ask yet? Leave this lesson for now and go to
[Your first real chore this week](first-real-chore.md).

**You end with** a plain account of what the application does and who uses it, a set of pages
about it, answers to the questions you actually have, and one important claim checked against the
file it came from. You will not read code. You will read what the assistant writes about the code,
and check that the file it points at says what it says.

Stuck? Ask the assistant, as before. (In a live session, the presenter walks steps 1 to 4 with
you; do 5 and 7 afterward.)

## 1 of 7. Get the application's address

The code for an application is kept in a repository: one folder of its source files and
supporting files, held in a shared system where changes are tracked and reviewed. You need the
address of one you are allowed to open; your organization decides which, usually your own
team's. An address looks like a web link that ends in the application's name.
`[YOUR ORGANIZATION: which repositories a learner may open, and where to find the address]`

With no address yet, and only if your organization allows fetching from the public internet: any
public sample application works; a common one is the Bank of Anthos sample at
`https://github.com/GoogleCloudPlatform/bank-of-anthos`. Check that policy before you try.

## 2 of 7. Bring it onto your computer, and check two things

Put the address where the prompt says `<address>`:

> I need to inspect this application. Clone the repository at `<address>` into the `practice` folder so we can analyze it.

"Clone" means make a local copy. A button appears inside the reply asking whether to allow the
command. Read it as in [Reading a permission request](start-here.md#reading-a-permission-request): it
should only copy the application into `practice`. Then click Allow. You did not learn any command to do that; you asked, and the assistant operated the tool.
If it fails, see [Copying the training or an application fails](../troubleshooting.md#copying-the-training-or-an-application-fails).

Check two things before going on:

1. A new folder appears under `practice` in the list on the left, with files inside it.
2. A simple question gets a reply, and the kinds of file it names (for example files ending
   `.java` or `.py`) can be seen in that folder:
   > What kinds of files are in this application?

## 3 of 7. Ask what it is, and make it cite files

> What does this application do, what business problem does it solve, and who uses it? You sometimes make mistakes, so cite the files that support each part of your answer.

Read the answer in its three parts: what it does, the business problem it solves, who uses it.
Then do the one thing that makes this safe:

> Open the first file you cited and show me the lines that support the "who uses it" claim.

Check: click the file name in its reply, or find the file in the list on the left, and find the
lines it quoted. You are not reading the code; you are checking that the words the assistant quoted
are really there. "Who uses it" is often the assistant's own interpretation: no file says it in
those words. If it cannot show lines, that is a finding, not a failure; step 6 shows how to tell
the difference. If they are not, or if part of the answer had no file
behind it, say so:

> That part is not supported by the file you named. Re-answer using only what the files say, and cite a file for every claim.

If you do not know what to ask, ask this:

<!-- tutor -->
> What questions should I ask you to understand this application?

If the answer is disorganized or does not make sense to you, say exactly that, and it redoes the
work:

<!-- tutor -->
> Organize your response.

<!-- tutor -->
> That does not make sense to me; explain it.

The answer gives you orientation. The repository gives you the evidence.

## 4 of 7. Generate a set of pages about the application

Ask for a set of linked pages about the whole application:

> Write a set of pages in the `practice` folder about this application, starting with an index: what it does, its main parts, what it depends on and what depends on it, the business rules in the code, its data, how it handles errors, and which files a new owner should read first. Cite files on every page.

If your organization provides a documentation generator, you can use it instead.
`[YOUR ORGANIZATION: the command to run the generator, and what it produces]`

It reads every file in the application, so it takes five to ten minutes, not seconds. While it
runs, the assistant shows its list of steps and works through them; the moving indicator means it
is still working. Start it and come back.

When it finishes, it names the first page, usually called index. Click it. If it shows as text
with symbols, press Ctrl+Shift+V.

Check: the index opens, and each line in it opens a page. Open the overview page, and find one file
it cites in the list on the left.

## 5 of 7. Explore by the question you actually have

This is where the pages become useful to you: to bring someone new onto the application, to plan
a change, to support an incident, to settle who owns what. Do not read everything. With the pages
open, ask what you would have asked the application's engineer. One example:

> How does this application work end to end?

Other things people ask: what it depends on, and what depends on it; logic built into the code that
you would not guess from the outside; what could break if it changes; how it is configured and
monitored. Pick the one closest to a decision in front of you this month and ask it in your own
words. Add the part that makes it checkable: ask it to name the page or file for each point.

Check: open the page or file the answer names. If it does not exist, or does not say that, tell
the assistant.

If the chat panel has grown to fill the screen, drag its top edge down to see the pages again.

## 6 of 7. Check one important claim

Pick one claim from the pages that would matter if it were wrong: a dependency, a business rule,
who is affected when something fails. Ask, putting in the claim:

<!-- frame -->
> You say that `<the claim>`. Show me the file and the lines that support it.

Open the file. There are three kinds of claim, and you can tell them apart:

- **Found directly in the code**: a setting, a name, a connection to another system. You can see it.
- **Worked out from how the code calls other things**: one part hands work to another, in an order. You can follow it.
- **The tool's own interpretation**: what it thinks the code is for. It should be labelled as interpretation.

For example: "the database address is set in the configuration file" is found directly; you can
see the setting. "A payment goes to the ledger after the balance is checked" is worked out; you
can follow one part calling the next. "This service exists to keep balances accurate" is
interpretation; no file says it in those words.

Practise first. Decide which kind each of these is, then compare with the answers below them:

- a. "The service retries a failed payment three times."
- b. "Orders are saved before the confirmation email is sent."
- c. "This is the most critical service in the application."
- d. "It connects to a database called ledger-db."

Answers: a is found directly, a setting you can see; b is worked out, from one part calling the
next; c is interpretation, no file says it; d is found directly, a name and a connection.

If you cannot tell which kind your own claim is, ask:

<!-- tutor -->
> Is this claim written in the file, worked out from how parts call each other, or your interpretation? Show me the lines either way.

Then decide yourself, using the examples above. A claim with no file behind it is unsupported:
treat it as a guess, and say so to the assistant.

Check: the lines say what the claim says, and you can name which of the three kinds it is.

**Before you use anything from these pages for a change to production, a risk decision, or a
question of ownership, apply your own judgment.** The pages are a starting point, not the truth:
you have checked one claim, and the rest stay unchecked until someone checks them.

## 7 of 7. Come back tomorrow

Close VS Code. Open it again: menu File, then Open Recent, then the name you saved your folders
under (or this training's folder). Everything is still there, including the application and its
pages. Start a new chat with the plus button at the top of the chat panel. A new chat remembers
nothing of yesterday's conversation, which is the point: the folder remembers, not the chat.

In the new chat, ask it in your own words to read the overview page under `practice` and tell you
the three things someone in your role should know first.

Check: the new chat has none of yesterday's messages; the application and its pages are still in
the list; and one of the three points can be found in the overview page.

Read the pages when you want the whole picture; ask the chat when you want one answer. Both are
there whenever you need them, and nothing you did yesterday was lost.

## What you can now do

Start with the repository. Ask one direct question for orientation. Generate the pages for a
structured understanding. Explore them by the question or decision in front of you. Trace
important findings back to the file they came from. Treat generated knowledge as a starting point
to check, not automatic truth. When it is wrong, and sometimes it will be, say what is wrong and it
redoes the work; checking it is the skill, not trusting it.

Next: [Your first real chore this week](first-real-chore.md).
