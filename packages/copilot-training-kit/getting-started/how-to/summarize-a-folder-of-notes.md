# How to: turn a folder of notes into one summary

**You end with:** `summary.md`, decisions, questions and actions from all your notes, every item
naming the note it came from.

**Before you start:** VS Code open with this training's folder, the chat in Agent mode. New to it?
Do [Start here](../start-here.md) first. If you have done the
lessons, try writing the request yourself first, then compare it with the one below. About ten
minutes.

**When:** meeting notes, scratch files, exported chat threads, a week of scattered text.

1. Add the folder to VS Code: menu File, then Add Folder to Workspace, then choose it. This
   training stays open beside it.
2. Ask. With two folders open, the assistant needs to be told which one:
   > Read every note in `<your folder>`, including Word files. Write `summary.md` in `<your folder>` with three sections: decisions made, open questions, and action items with owners. For every item, say which file it came from. Do not change the notes.
3. Open `summary.md`. If it shows as text with symbols, press Ctrl+Shift+V.
4. Iterate in words:
   > Split the action items by week.
   > Drop anything older than `<a month>`.

**Check:** every item names a source file. Open the files for two items and find them there. An
item with no source is a guess.

If it does not work: [If something goes wrong](../../troubleshooting.md).
