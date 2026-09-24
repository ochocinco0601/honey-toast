# How to: write your own request

**You end with:** a chore done that no recipe covers, from a request you wrote yourself and
checked.

**Before you start:** VS Code open with this training's folder, the chat in Agent mode. Best after
[Lesson: your own files](../lesson-your-files.md), which shows the five parts step by step. About
fifteen minutes.

**When:** a chore in front of you that none of the other recipes fits.

Every request you can check has five parts. Most of the other recipes use all five:

1. **Which folder or file.** Name it. With two folders open, always.
2. **What to read.** Every note; one export; the whole folder.
3. **What to make, and where.** A file, by name, in which folder, with which sections or columns.
4. **What not to do.** "Do not change anything." "Do not guess; if the files do not say, write
   not stated." "Plan first; do not move anything yet."
5. **Show your sources.** "For every item, say which file it came from."

Steps:

1. Add the folder to VS Code if it is not open: menu File, then Add Folder to Workspace.
2. Write your request in `my-requests.md` in your folder, with all five parts, and save it.
3. Copy the line below into the chat box, paste your request after it, and press Enter:
   <!-- tutor -->
   > Before you do anything, tell me which of these is missing or unclear in the request below, and do not carry it out: which folder, what to read, what to make and where, what not to do, show your sources. The request:

   Change your request in `my-requests.md` using what it said, and save it.
4. Copy it into the chat box on its own and press Enter. Allow only commands that match what you
   asked for; see [Reading a permission request](../start-here.md#reading-a-permission-request).
   `my-requests.md` keeps it for next time.

Three examples, one for each kind of work:

- **Tickets:** "Read `incidents.csv` in `ops-exports`. Write `repeat-offenders.md` in that folder
  listing every service with more than three incidents this month, with the count and the incident
  numbers. Do not change the export."
- **Planning:** "Read every document in `q3-planning`. Write `dates.md` in that folder: every
  deadline mentioned, who owns it, and the file and sentence it came from. Do not change the
  documents."
- **An application:** "Read the `config` folder of the application in `practice`. Write
  `settings.md` in `practice` listing every external system it connects to, with the file and
  line for each. Change nothing in the application."

**Check:** the new file exists where you asked. Pick two items and find them in the files they
name. If a result came back wrong, look for the missing part in your request; that is usually why.

If it does not work: [If something goes wrong](../../troubleshooting.md).
