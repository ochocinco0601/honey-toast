# Review a change request for go or no-go

**You end with:** `review.md`, one row per change request: a suggested go, no-go or ask for more
information, and why.

**You need:** the copilot-practice folder open in VS Code. If another folder is open, on the **File** menu, select **Open Recent**, and then select
`copilot-practice`.

**When:** a change request needs your go or no-go, and the answer depends on checking what was
submitted against what you require.

## 1. Have Copilot create practice change requests

Copilot leaves items out of two of the change requests on purpose, so you know what it should find.

1. If the control at the bottom of the chat box doesn't show **Agent**, select the control, and
   then select **Agent**.
2. In the chat box, enter:

> In the copilot-practice folder, create a folder named change-practice.
> In it, create checklist.md: the four things a change must have before it is approved.
> The four are an owner, a time window, a rollback plan and a test result.
> Then create change-requests.md in the same folder, with three made-up change requests named CHG-201, CHG-202 and CHG-203.
> Give CHG-201 all four things.
> Leave the rollback plan out of CHG-202.
> Leave the owner and the test result out of CHG-203.
> Add or change no other file.

Check: `change-practice` holds `checklist.md` and `change-requests.md`.

## 2. Check each change request against the checklist

A quote shows where a change request meets an item. "Not stated" gives Copilot a way to report a
missing item instead of guessing.

1. Enter:

> Read change-requests.md and checklist.md in the change-practice folder of the copilot-practice folder.
> For each change request and each checklist item, quote the words in the request that meet it.
> Where the request doesn't say, write "not stated".
> Don't guess.
> Don't change any file.

Check: CHG-201 meets all four. CHG-202's rollback plan is "not stated", and so are CHG-203's owner
and test result. For CHG-201, find each quote in `change-requests.md`.

If an item that was left out has a quote instead, or CHG-201 has an item "not stated", find the
item in `change-requests.md`. A quote such as "Rollback: none provided" doesn't meet the item. Tell
Copilot what you found, and ask it to correct the item.

## 3. Save a suggested decision

Copilot only suggests. The decision stays yours.

1. In the same chat, enter:

> In the change-practice folder, create review.md: a table with one row per change request.
> In each row, give a suggested go, no-go, or ask for more information, and why.
> Add or change no other file.

2. In the list on the left, right-click `review.md` and select **Open Preview**.

Check: CHG-201 is a go, and the other two are no-go or ask for more information, each with its
missing items as the reason.

To use your own change requests: save them in one folder with your checklist, and open that
folder. Send the same requests, except the one that creates practice files. Use your files' names,
and leave out the practice folder names.

If it does not work: [Help](../../troubleshooting.md).
