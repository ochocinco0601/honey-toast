# How to: organize a messy folder

**You end with:** a sorted folder, and `moves.md`, a record of every move.

**Before you start:** VS Code open with this training's folder, the chat in Agent mode. New to it?
Do [Start here](../start-here.md) first. If you have done the
lessons, try writing the request yourself first, then compare it with the one below. About ten
minutes. The first time, try it on a small folder, or on a copy of one.

**When:** your downloads folder, your desktop, a project folder that grew without a plan. A
downloads folder can hold exports with customer data. The plan in step 2 reads only file names,
but until your organization tells you otherwise, use a folder with no customer names, account
numbers, personal details, passwords or system addresses in its files.

1. Add the folder to VS Code: menu File, then Add Folder to Workspace, then choose it. This
   training stays open beside it. Adding a folder moves nothing.
2. Ask for a plan before any action. With two folders open, the assistant needs to be told which
   one:
   > Tell me how many files are in `<your folder>`. List them grouped by type and by month. Propose a folder structure. Do not move anything yet.
3. Read the plan. Change it in words, for example "Put all the vendor PDFs under vendors/
   instead":
   > `<your change to the plan>`
4. Save the plan first, then move. The record exists before anything moves:
   > Save the plan as `moves.md` in `<your folder>`: one row per file, where it is now and where it will go. Then move the files as `moves.md` says, and tell me any that did not move.
5. Before you allow each command, check it as in
   [Reading a permission request](../start-here.md#reading-a-permission-request): it should only move
   files inside your folder, as the plan said. Then allow it and watch the list on the left of VS
   Code change.

**Check:** in File Explorer, right-click the folder and choose Properties. "Contains" shows the
number of files, including those in the new sub-folders. It should equal the number from step 2,
plus one for `moves.md`. Then open two files where they landed.

**If it went wrong:** ask it to move the files back, and point it at `moves.md`, which records
where everything was. That record is why step 4 saves it first.

If it does not work: [If something goes wrong](../../troubleshooting.md).
