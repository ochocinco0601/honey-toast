# How to: ask for a skill

Assumes you have finished `README.md`: VS Code open, this training folder open, the chat in Agent
mode. About fifteen minutes.

**When:** you do the same analysis or the same kind of write-up more than twice.

1. Describe the job, not the steps:
   > I handle tickets for one application. Every week I need to find what the tickets have in common. Write me a skill that does that analysis on an export in `<your folder>`, and save it where skills belong in this setup. Tell me its name and where you saved it.
   Look for the file it names in the list on the left; a skill is a file you can open and read.
2. Run it on a real export. Ask for it by name in plain words, for example:
   > Use the ticket-commonality skill on `export.csv` in `<your folder>`.
   Or type a forward slash in the chat box and start typing the skill's name; a list appears.
3. Correct it in words:
   > Too verbose.
   > Group by root cause, not by requester.
   > Always end with three recommendations.
4. It updates the file. Run it again.

**Check:** the result names the export file and the groups it found. Run it a second time on
the same file; if the two runs disagree about the groups, the skill's instructions are too
loose. Say which grouping you meant and it tightens them.

**Why this works:** a skill is a text file of instructions. The assistant already knows how the
job is generally done. The file tells it how you want it done.

`[YOUR ORGANIZATION: where skills are stored, and where approved shared skills are published]`
