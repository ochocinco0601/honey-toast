# How to: review a change request for go or no-go

Assumes you have finished `README.md`: VS Code open, this training folder open, the chat in Agent
mode. About fifteen minutes.

**When:** a change request has landed on you for approval, or you are the one who says go or
no-go, and the answer depends on reading what was submitted against what you require.

**Before you start:** a change record can hold customer or system details. Until your
organization has told you what may be used with the assistant, use one that contains nothing you
would not paste into an email to a colleague.
`[YOUR ORGANIZATION: which classes of data may be used with the assistant]`

1. Export the change record, or the list of changes awaiting you, to a file. Put it in a folder
   with your checklist: the things a change must have before you approve it, such as a rollback
   plan, a test result, a change window, a named owner, whatever your team requires. If the
   checklist is in your head, write it down first as a short file called `checklist.md`. Add the
   folder to the workbench: menu File, then Add Folder to Workspace.
2. Ask, using your folder's and files' real names:
   > Read `changes.csv` in `<your folder>` and `checklist.md`. For each change, say which checklist items are met, which are missing, and which you cannot tell from the record. Do not guess; if the record does not say, write "not stated".
3. Ask the question you would put to the submitter:
   > For the changes missing a rollback plan, what would I need to ask the submitter?
4. Keep it:
   > Write `review.md` next to the export, one row per change: go, no-go, or ask, and why.

**Check:** open one change the assistant marked as fully met and confirm each item is really in
the record. "Not stated" is the answer to trust; a confident "met" with nothing to point at is a
guess.

**What this is not:** the assistant does not approve anything. It reads the record against your
list and shows you where to look. The decision is yours, as it was before.
