# How to: analyze an exported spreadsheet

**You end with:** tables that answer your question, checked by you, in `analysis.md` next to the
export.

**Before you start:** VS Code open with this training's folder, the chat in Agent mode. New to it?
Do [Start here](../start-here.md) first. If you have done the
lessons, try writing the request yourself first, then compare it with the one below. About fifteen
minutes.

**When:** a ticket export, an incident list, a change calendar, anything a system will give you
as a CSV or spreadsheet file. Today you probably do this by hand in a spreadsheet.

**Before you export:** until your organization tells you otherwise, use only data with no
customer names, account numbers, personal details, passwords or system addresses. Delete those
columns first, or use a copy with made-up values. Not sure? Practise on this training's
`sample-files` folder first. `[YOUR ORGANIZATION: which classes of data may be used with the assistant]`

1. Export the data from the system to a file. Put the file in a folder. Add that folder to VS
   Code: menu File, then Add Folder to Workspace, then choose it. This training stays open beside
   it.
2. Orient. CSV is the format it reads most reliably; a spreadsheet file may work, depending on
   what is installed, and if it does not, export as CSV instead:
   > Read `<your export file>` in `<your folder>`. Tell me the columns and how many rows. Then give me the top ten categories by count and the trend by week. For each figure, say which column and filter you used. Do not change the export.
3. Ask the question you actually have, in your own words. For a ticket export, for example,
   "Which assignment group has the oldest open items? Show the ten oldest with their age in days."
   For a change calendar, "Which changes next week have no named owner?"
   <!-- frame -->
   > `<your question about the data>`
4. Ask for something you can keep and send:
   > Write `analysis.md` next to the export, with the tables above and a one-paragraph summary.
**Check:** open the export in your spreadsheet program. Filter one category and compare the count
with the assistant's. Take one figure it computed, such as an item's age, and work it out yourself
from the data. If either differs, ask:

> How did you compute that?

**Next week:** save the new export under a different name, for example `export-week2.csv`, put it
in the same folder, and ask:

> Compare `<this week's file>` with `<last week's file>`. What changed in the top categories, and which of last week's ten oldest items are still open?

**Direct access instead of an export:** whether the assistant can read the system itself depends
on connectors your organization has set up. `[YOUR ORGANIZATION: available connectors and their status]`

If it does not work: [If something goes wrong](../../troubleshooting.md).
