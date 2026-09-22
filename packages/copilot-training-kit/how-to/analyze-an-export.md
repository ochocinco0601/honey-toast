# How to: analyze an exported spreadsheet

Assumes you have finished `README.md`: VS Code open, this training folder open, the chat in Agent
mode. About fifteen minutes.

**When:** a ticket export, an incident list, a change calendar, anything a system will give you
as a CSV or spreadsheet file. Today you probably do this by hand in a spreadsheet.

**Before you export:** an export can hold customer data. Until your organization has told you
what may be used with the assistant, use one that contains nothing you would not paste into an
email to a colleague. `[YOUR ORGANIZATION: which classes of data may be used with the assistant]`

1. Export the data from the system to a file. Put the file in a folder. Add that folder to the
   workbench: menu File, then Add Folder to Workspace, then choose it. This kit stays open beside it.
2. Orient. Replace `export.csv` with your file's actual name. CSV is the safe format; a spreadsheet
   file may work, depending on what is installed, and if it does not, export as CSV instead:
   > Read `export.csv` in `<your folder>`. Tell me the columns and how many rows. Then give me the top ten categories by count and the trend by week.
3. Ask the question you actually have:
   > Which assignment group has the oldest open items? Show the ten oldest with their age in days.
4. Ask for something you can keep and send:
   > Write `analysis.md` next to the export, with the tables above and a one-paragraph summary.
5. Next week, save the new export under a different name, for example `export-week2.csv`, put it
   in the same folder, and ask:
   > Compare `export-week2.csv` with `export.csv`. What changed in the top categories, and which of last week's ten oldest items are still open?

**Check:** ask "How did you compute the age?" and see whether the method matches what you meant.

**Direct access instead of an export:** whether the assistant can read the system itself depends
on connectors your organization has set up. `[YOUR ORGANIZATION: available connectors and their status]`
