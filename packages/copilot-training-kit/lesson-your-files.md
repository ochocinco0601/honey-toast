# Lesson: your own files

For everyone who has finished the steps in README.md; this is the first lesson. Your work may be
tickets, exports, spreadsheets or notes, or an application's code; either way you start here.
About twenty minutes. By the end you will have had the assistant read a folder of your real
files, write you something from them, and you will have checked what it wrote against the files.

Nothing in this lesson changes your files. The assistant only reads them and writes new files
next to them.

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

Before you choose, one rule: until your organization has told you what may be used with the
assistant, pick files that contain nothing you would not paste into an email to a colleague.
`[YOUR ORGANIZATION: which classes of data may be used with the assistant]`

## 2. Put it next to this one

Menu File, then Add Folder to Workspace, then choose your folder. VS Code calls the set of
folders you have open a workspace; you now have two folders in it, this one and yours, and both
show on the left. This folder stays open so the assistant can keep reading these instructions.

When you close VS Code later it will offer to save this pair of folders under a name. Say yes.
Next time, menu File, then Open Recent, and pick that name to get both back.

## 3. Ask a question that changes nothing

In the chat, type the following, putting your folder's name in place of `<your folder>`, angle
brackets included:

> Look at the files in `<your folder>`. Tell me what is there, how many of each kind, and what they seem to be about. Do not change anything.

You should get a description. Check one thing in it against what you can see on the left.

## 4. Ask for something written

If your folder holds notes:

> Read every note in `<your folder>`. Write a file called `summary.md` in that folder with three sections: decisions made, open questions, and action items with owners. For every item, say which file it came from.

If your folder holds an exported spreadsheet, using its real file name:

> Read `<file name>` in `<your folder>`. Tell me the columns and how many rows. Then write `analysis.md` in that folder with the top ten categories by count, the ten oldest open items with their age in days, and a one-paragraph summary.

A button appears inside the reply asking whether to allow the command; click Allow. A new file
appears in your folder on the left. Click it. If it shows as text with symbols, press Ctrl+Shift+V to read it as a page.

## 5. Check it

Pick two items in what it wrote. For each, open the file it says the item came from and find
the sentence or row.

**What a good result looks like.** Every item names the file it came from, and the two you
checked are really there.

**What a bad result looks like.** An item with no file named, or one you cannot find in the
file it names. Treat that item as a guess. Say so:

> Item three does not appear in the file you named. Re-do the summary using only what the files say, and name the file for every item.

## 6. Ask the next question

Whatever you would have asked a colleague about these files, ask the assistant now, in your
own words. Then ask it to add the answer to the file it wrote.

## What you can now do

You can point the assistant at a folder of your real work, have it read the lot, get something
written from it, and check it. The pages in `how-to/` are this same move as short recipes for
specific chores. When a chore is one your organization already has a skill for, `skills.md`
says how to use it and where to find it.
