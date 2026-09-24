# How to: change many files at once

**You end with:** changed copies of your files in a new folder, with the originals untouched.

**Before you start:** VS Code open with this training's folder, the chat in Agent mode. New to it?
Do [Start here](../start-here.md) first. If you have done the
lessons, try writing the request yourself first, then compare it with the one below. About ten
minutes.

**When:** a job you would never do by hand: rename two hundred files by a pattern, replace a term
across a whole folder, pull every date or every address out of thirty notes into one table.

1. Add the folder to VS Code: menu File, then Add Folder to Workspace, then choose it. This
   training stays open beside it.
2. Ask for the outcome, and protect the originals. With two folders open, the assistant must be
   told which one, and this job changes files:
   > Copy every file in `<your folder>` into a new folder called `sanitized` inside it, and in the copies replace every occurrence of `<the old term>` with `<the new term>`. Tell me how many files you copied and how many replacements you made.
3. The assistant writes a small program, and a button appears in its reply asking permission to
   run it. You do not need to read the program: check the folder it names is `sanitized`, as in
   [Reading a permission request](../start-here.md#reading-a-permission-request). Then click Allow.
   It runs and reports. You asked for the outcome, not the program.
4. The same shape, different job:
   > Read every note in `<your folder>`. Make one table in `<your folder>/dates.md` of every date mentioned, the file it came from, and the sentence around it.

**Check:** in the list on the left, right-click the `sanitized` folder, choose Find in Folder, and
type the old term: there should be no results. Then open one original file and confirm it still
has the old term. If you want
to see the program, ask for it; you do not need to:

> Show me what you ran.

**Why this matters:** you did not need to know how to code to take advantage of code.

If it does not work: [If something goes wrong](../../troubleshooting.md).
