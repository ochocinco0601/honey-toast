# How to: change many files at once

Assumes you have finished `README.md`: VS Code open, this training folder open, the chat in Agent
mode. About ten minutes.

**When:** a job you would never do by hand: rename two hundred files by a pattern, replace a term
across a whole folder, pull every date or every address out of thirty notes into one table.

1. Add the folder to the workbench: menu File, then Add Folder to Workspace, then choose it. This
   kit stays open beside it.
2. Ask for the outcome, and protect the originals. Type your folder's name where it says
   `<your folder>`; with two folders open the assistant must be told which one, and this job
   changes files:
   > Copy every file in `<your folder>` into a new folder called `sanitized` inside it, and in the copies replace every occurrence of "Project Falcon" with "Project Redacted". Tell me how many files you copied and how many replacements you made.
3. The assistant writes a small program and a button appears in its reply asking permission to
   run it. Nothing runs until you click Allow. Then it runs and reports. You never see the
   program. You asked for the outcome.
4. The same shape, different job:
   > Read every note in `<your folder>`. Make one table in `<your folder>/dates.md` of every date mentioned, the file it came from, and the sentence around it.

**Check:** open two of the changed files. If you want to see the program, ask "Show me what you
ran." You do not need to.

**Why this matters:** you did not need to know how to code to take advantage of code.
