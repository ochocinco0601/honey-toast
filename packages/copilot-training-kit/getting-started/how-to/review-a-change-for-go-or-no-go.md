# How to: review a change request for go or no-go

**You end with:** `review.md`, one row per change: go, no-go, or ask, and why, with your decision
still yours.

**Before you start:** VS Code open with this training's folder, the chat in Agent mode. New to it?
Do [Start here](../start-here.md) first. If you have done the
lessons, try writing the request yourself first, then compare it with the one below. About fifteen
minutes.

**When:** a change request has landed on you for approval, or you are the one who says go or
no-go, and the answer depends on reading what was submitted against what you require.

**Before you export:** until your organization tells you otherwise, use only records with no
customer names, account numbers, personal details, passwords or system addresses. Delete those
columns first, or use a copy with made-up values. Not sure? Practise on this training's
`sample-files` folder first.
`[YOUR ORGANIZATION: which classes of data may be used with the assistant]`

1. Export the change record, or the list of changes awaiting you, to a file. Put it in a folder
   with your checklist: the things a change must have before you approve it, such as a rollback
   plan, a test result, a change window, a named owner, whatever your team requires. If the
   checklist is in your head, write it down first as a short file called `checklist.md`. Add the
   folder to VS Code: menu File, then Add Folder to Workspace.
2. Ask:
   > Read `<your export file>` in `<your folder>` and `checklist.md`. For each change, say which checklist items are met, which are missing, and which you cannot tell from the record. Do not guess; if the record does not say, write "not stated".
3. Ask the question you would put to the submitter:
   > For the changes missing a rollback plan, what would I need to ask the submitter?
4. Keep it:
   > Write `review.md` next to the export, one row per change: a suggested go, no-go, or ask, and why.

**Check:** open one change the assistant marked as fully met and confirm each item is really in
the record. "Not stated" is the answer to trust; a confident "met" with nothing to point at is a
guess.

**What this is not:** the assistant does not approve anything. It reads the record against your
list and shows you where to look. The decision is yours, as it was before.

If it does not work: [If something goes wrong](../../troubleshooting.md).
