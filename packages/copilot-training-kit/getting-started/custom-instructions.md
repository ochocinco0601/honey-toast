# Give Copilot custom instructions for a folder

Custom instructions are notes Copilot reads before every request in a folder: what the work is,
who reads it, and how you want it done. You stop repeating them. In this unit, you ask for a
summary, have Copilot write down how you want summaries, and ask again. Start with the practice
folder open. It holds the `notes` folder from [Change Copilot's work, then undo it](lesson-your-files.md).

## 1. Ask Copilot to summarize the meeting notes

You'll compare this answer with the next one.

1. In the chat box, enter:

> Summarize the meeting notes in the notes folder of the copilot-practice folder.

Check: the chat shows a summary of the notes. Look at what comes first, and whether each item
names the note it came from.

## 2. Have Copilot save custom instructions for summaries

1. Enter:

> In the copilot-practice folder, create .github/copilot-instructions.md describing this work:
> - The notes folder holds a team's weekly meeting notes.
> - The people who read summaries of them are busy and not technical.
> - They only need what they must act on: lead with the actions, grouped by owner, then one line of decisions.
> - After each item, name the note it came from.
> If that file already exists, don't change it; tell me instead.
> Add or change no other file.

2. In the list on the left, open `.github` and select `copilot-instructions.md`.

Check: the file holds the four points you asked for.

<!-- more: Why the file name matters -->
Copilot reads this file before every request in this folder. It must have exactly this name, in a
folder named `.github`. Nothing is sent to GitHub.
<!-- /more -->

## 3. Ask for the summary again, and compare

A new chat starts without the first answer, so any difference comes from the instructions.

1. At the top of the chat, select **New Chat** (+).
2. Enter the same request as before:

> Summarize the meeting notes in the notes folder of the copilot-practice folder.

Check: the new summary leads with the actions, grouped by owner, then one line of decisions, and
names the note behind each item.

<!-- more: If the summary ignores the instructions -->
Send:

> Follow the instructions in .github/copilot-instructions.md and summarize again.
<!-- /more -->

## 4. Have Copilot delete the custom instructions

Left in place, these instructions shape every later answer in this folder, so remove them.

1. Enter:

> Delete the .github folder in the copilot-practice folder, and nothing else.

2. If a permission request appears, allow it if it deletes only that folder.

Check: the list on the left no longer shows `.github`.

## On your own work

Real custom instructions hold your context and standards: what the work is, who it's for, and how
you want it written. In a folder of your own, ask Copilot to create
`.github/copilot-instructions.md` holding yours. If the folder already has one, ask Copilot to add
to it rather than replace it.

**Important:** instructions saved in a folder apply only while that folder is open. For
instructions that apply in every folder, ask Copilot to help you set up personal custom
instructions.

## What you did

You saved instructions once, saw Copilot follow them without being asked, then removed them.
