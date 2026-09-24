# Lesson: your own files

Unit 2 of the path, after [Start here](start-here.md). Your work
may be tickets, exports, spreadsheets or notes, or an application's code; either way you start
here. About thirty minutes. By the end the assistant will have read a folder of your real files
and written you something from them, you will have checked it against the files, and you will
have written a request of your own.

Nothing in this lesson changes your files, except one small file you add and then delete yourself.
The assistant only reads them and writes new files next to them.

Stuck? Tell the assistant what you expected and what you see; the words are in
[When you are stuck](../troubleshooting.md#when-you-are-stuck-ask-the-assistant-first). A word you do not know: [Glossary](../glossary.md),
or ask the assistant.

## 1. Pick a real folder

Choose one folder on your computer that holds work you actually do. Any of these:

- a folder of meeting notes or scratch notes, as text or Word files;
- one spreadsheet a system exported for you, such as a list of tickets, incidents or changes,
  saved in its own folder;
- a folder someone sent you that you have not had time to read.

If you have nothing like that to hand, make one: copy three or four documents you have written
recently into a new folder.

Plain text, markdown and CSV files are read directly. Word and Excel files usually work too; the
assistant may ask permission to run a small program to read them. If a file cannot be read, save
it as text or CSV and try again.

Until your organization tells you otherwise, use only files with no customer names, account
numbers, personal details, passwords or system addresses. For an export, delete those columns
first, or use a copy with made-up values.

**Not sure your files are allowed?** Use the practice files instead: made-up meeting notes, a ticket
export and some change requests, in this training's `sample-files` folder. Copy that folder to
your Documents folder in Windows File Explorer, and use the copy as your folder from here on.
`[YOUR ORGANIZATION: which classes of data may be used with the assistant]`

Check: open two of the files and look. None of those things is in them.

## 2. Put it next to this one

Menu File, then Add Folder to Workspace, then choose your folder. You now have two folders open,
this training and yours, and both show in the list on the left. The training stays open so the
assistant can keep reading these pages and help you with them. VS Code may reload its window when
you add a folder, and the chat may clear; that is expected, and nothing in your files changed.

When you close VS Code later, it asks whether to save your workspace configuration. Click Save,
type a name you will recognise, such as `copilot-training`, and save it in your Documents folder.
Next time: menu File, then Open Recent, and pick that name to get both folders back.

Check: the list on the left shows two folders, this training and yours, by name. If yours does not
appear, ask the assistant, using the words in [When you are stuck](../troubleshooting.md#when-you-are-stuck-ask-the-assistant-first).

## 3. Ask a question that changes nothing

From here on, prompts have blanks: parts in angle brackets, such as `<your folder>`. Replace each
one, brackets included, with your own before you press Enter. Use the folder's name as it appears in
the list on the left. With two folders open, always name the one you mean.

> Look at the files in `<your folder>`. Tell me what is there, how many of each kind, and what they seem to be about. Do not change anything.

Check: pick one number in the reply, such as how many Word files there are, and count them
yourself in the list on the left. They should match.

## 4. Ask for something written

If your folder holds notes, first add one file of your own to it, so you have an answer you
already know. In the list
on the left, right-click your folder, choose New File, type `known.txt` and press Enter. In the
file that opens, type one sentence you made up, such as "Decision: the team review moves to
Thursday." Then press Ctrl+S to save it. A dot on the file's tab means it is not saved yet. If
your folder holds a spreadsheet instead, do not make `known.txt`: note one row's category and date
now. A CSV export works best; if the assistant asks to install something to read a spreadsheet
file, decline and save the export as CSV instead.

If your folder holds notes:

> Read every note in `<your folder>`. Write a file called `summary.md` in that folder with three sections: decisions made, open questions, and action items with owners. For every item, say which file it came from. Do not change the notes.

If your folder holds an exported spreadsheet:

> Read `<file name>` in `<your folder>`. Tell me the columns and how many rows. Then write `analysis.md` in that folder with the top ten categories by count, the ten oldest open items with their age in days, and a one-paragraph summary. For each figure, say which column and filter you used. Do not change the export.

If a permission request appears, read it as in
[Reading a permission request](start-here.md#reading-a-permission-request): it should name your folder
and the new file only. If none appears, the file may have been written directly; go on to the
check. If it cannot read a file, or writes the file somewhere else, tell it what happened in the
words from [When you are stuck](../troubleshooting.md#when-you-are-stuck-ask-the-assistant-first).

Check: the new file appears inside your folder in the list on the left, not in the training
folder. Click it. If it shows as text with symbols, press Ctrl+Shift+V to read it as a page.

## 5. Check it

**A check where you already know the answer.** Look for your made-up sentence from `known.txt`.
A good result lists it and names `known.txt`. (For a spreadsheet: find the row you noted, and
check its category is counted and its age is right.) If it is missing, or names another file, you
have just seen why checking matters. When you are done, delete `known.txt`: right-click it in the
list, then Delete.

Then pick two more items, ones you would act on. For each, open the file it says the item came
from and find the sentence or row. Open a Word or Excel file from File Explorer, in Word or Excel;
in VS Code it does not show as a page. To mark what you found, click the text tab of the file it
wrote, `summary.md` or `analysis.md` (not the preview), type `(checked)` after the item, and press
Ctrl+S. The assistant can tell you
where to look; only the file can tell you whether it is right.

**What a good result looks like.** Every item names the file it came from, and the ones you
checked are really there.

**What a bad result looks like.** An item with no file named, or one you cannot find in the file
it names. Treat that item as a guess, and say so, putting in the item and the file:

<!-- frame -->
> The item `<the item>` does not appear in `<the file it named>`. Re-do the summary using only what the files say, and name the file for every item.

If you cannot find the file it names, ask:

<!-- tutor -->
> Which file and which line did `<the item>` come from?

Then open it yourself.

## 6. See how your request was built

The notes request in step 4 has five parts. Every request you can check has them:

1. **Which folder or file:** `<your folder>`.
2. **What to read:** every note.
3. **What to make, and where:** a file called `summary.md` in that folder, with three sections.
4. **What not to do:** do not change the notes.
5. **Show your sources:** for every item, say which file it came from. For figures from a
   spreadsheet, say which column and filter each one used.

Now find the five parts in the other request in step 4, the spreadsheet one, before you read on.

Check your answer: 1 is `<file name>` in `<your folder>`; 2 is that one file, its columns and rows;
3 is `analysis.md` in that folder, with the top ten categories, the ten oldest items and a
summary; 4 is do not change the export; 5 is say which column and filter each figure used.

A request with all five is one you can check. When a result comes back wrong, the missing part is
usually why. The first request in a chat needs all five. Follow-ups in the same chat, such as
"Split the action items by week", can be short: they build on the first.

## 7. Write a request of your own

Ask for a second file from the same folder, one you would actually use: a list of deadlines, a
note to your team, three things to raise at your next meeting, or whatever you would have asked a
colleague to pull from these files. Write it yourself. This frame is only a start; a file name
ending in `.md`, such as `deadlines.md`, works well:

<!-- frame -->
> Read `<what to read>` in `<your folder>`. Write `<file name>` in that folder with `<what it should contain>`. Do not change `<what must stay as it is>`. For every item, say which file it came from.

Write your request in a new file first, so you cannot lose it: in the list on the left, right-click
your folder, choose New File, name it `my-requests.md`, type your request in it and press Ctrl+S.

Then ask the assistant to review it. Copy the line below into the chat box, and after it paste
your request (select it in `my-requests.md`, press Ctrl+C, click at the end of the line in the chat
box, press Ctrl+V). Then press Enter:

<!-- tutor -->
> Before you do anything, tell me which of these is missing or unclear in the request below, and do not carry it out: which folder, what to read, what to make and where, what not to do, show your sources. The request:

Change your request in `my-requests.md` using what it said, and save it. Then copy it into the chat
box on its own and press Enter.

Check: the new file exists in your folder, and one item in it is really in the file it names.
`my-requests.md` now holds a request you wrote that works: the start of your own collection.

## What you can now do

You can point the assistant at a folder of your real work, have it read the lot, get something
written from it, and check it. You can also write the request yourself: the five parts are in
step 6.

Two checks go with you to every chore:

- **Know one answer in advance.** Before you ask, note one item you know should be there, such as a
  decision, a row or a change, and see that it comes back.
- **Check what you would act on.** Choose the items you would act on, not random ones, and find
  each in the file it names.

Why this works: [the workbench](../explanation.md#2-the-workbench),
[the assistant has hands](../explanation.md#3-the-assistant-has-hands) and
[check the receipts](../explanation.md#9-check-the-receipts).

Next: [Lesson: an application you do not own](lesson-application.md). You need an application's
address for it. Without one, go straight to
[Your first real chore this week](first-real-chore.md).
