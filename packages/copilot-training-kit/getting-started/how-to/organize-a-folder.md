# Organize a folder

**You end with:** a folder sorted into subfolders, and `moves.md`, a record of where each file was
and where it went.

**You need:** the copilot-practice folder open in VS Code. If another folder is open, on the **File** menu, select **Open Recent**, and then select
`copilot-practice`.

**When:** a folder grew without a plan, such as your desktop or a shared project folder.

## 1. Have Copilot create a cluttered folder

The folder gives you files to sort without touching your own.

1. If the control at the bottom of the chat box doesn't show **Agent**, select the control, and
   then select **Agent**.
2. In the chat box, enter:

> In the copilot-practice folder, create a folder named inbox.
> In it, create 12 short, made-up files: meeting notes, drafts of team emails, and ticket exports as .csv files.
> Put a date from August or September in each file's name.
> Add or change no other file.

Check: `inbox` holds 12 files. If it holds a different number, expect that number below.

## 2. Ask for a plan, and change nothing yet

Reading the plan first lets you correct it before any file moves.

1. Enter:

> List the files in the inbox folder of the copilot-practice folder, grouped by kind and by month.
> Propose subfolders inside inbox to sort them into.
> Don't change any file yet.

Check: the reply lists all 12 files and proposes subfolders, and `inbox` hasn't changed.

## 3. Change the plan by asking again

You don't have to accept the first plan. Asking again changes it.

1. Enter:

> Change the plan so the email drafts go in a subfolder named emails.
> In the new plan, leave the .csv files where they are.
> Don't change any file yet.

Check: the new plan has an `emails` subfolder and leaves the .csv files in `inbox`.

## 4. Save the plan, then move the files

Saving the plan first gives you a record of where everything was.

1. Enter:

> In the inbox folder, create moves.md: one row per file, with where it is now and where it will go.
> Then move the files as moves.md says.
> Tell me any file the plan moves that didn't move.
> Add or change no other file.

2. If a permission request appears, allow it if everything it creates or moves is inside
   `inbox`.

Check: `inbox` holds the new subfolders, the .csv files and `moves.md`, and `moves.md` has a row
for each of the 12 files. 

<!-- more: If you want the files back where they were -->
`moves.md` records where each file was, so Copilot can put them back. Enter:

> Move every file in the inbox folder back to where moves.md says it was.
> Add or change no other file.
<!-- /more -->

To use your own folder: make a copy of it, and open the copy. Send the same requests, except the
one that creates practice files. Use the copy's name in place of inbox, and leave out the practice
folder names.

If it does not work: [Help](../../troubleshooting.md).
