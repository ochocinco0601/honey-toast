# How to: turn a folder of notes into one summary

Assumes you have finished `README.md`: VS Code open, this training folder open, the chat in Agent
mode. About ten minutes.

**When:** meeting notes, scratch files, exported chat threads, a week of scattered text.

1. Add the folder to the workbench: menu File, then Add Folder to Workspace, then choose it. This
   kit stays open beside it.
2. Ask, typing your folder's name where it says `<your folder>`; with two folders open the
   assistant needs to be told which one:
   > Read every text and markdown file in `<your folder>`. Write `summary.md` in `<your folder>` with four sections: decisions made, open questions, action items with owners, and, for each item, the file it came from.
3. Open `summary.md` in preview. Spot-check two items against their source files.
4. Iterate in words:
   > Split the action items by week.
   > Drop anything older than March.

**Check:** every item names a source file. An item with no source is a guess.
