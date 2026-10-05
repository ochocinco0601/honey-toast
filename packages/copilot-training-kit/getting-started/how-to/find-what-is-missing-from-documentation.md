# Find what is missing from documentation

**You end with:** `gaps.md`, the things a set of documents doesn't say, written as questions for the team
that sent them.

**You need:** the copilot-practice folder open in VS Code. If another folder is open, on the **File** menu, select **Open Recent**, and then select
`copilot-practice`.

**When:** a team hands you documentation for an application or a process, and you have to support
or approve something based on it.

## 1. Have Copilot create practice documents

Copilot leaves two things out of the documents on purpose, so you know what it should find.

1. If the control at the bottom of the chat box doesn't show **Agent**, select the control, and
   then select **Agent**.
2. In the chat box, enter:

> In the copilot-practice folder, create a folder named docs-practice.
> In it, write three short, made-up documents for an application named Order Tracker: an overview, a setup guide and a support guide.
> Leave out who to call when it fails, and how to restart it.
> Then create what-support-needs.md in the same folder: six things a support team must find in any application's documentation.
> Make who to call and how to restart the application two of the six.
> Add or change no other file.

Check: `docs-practice` holds the three documents and `what-support-needs.md`.

## 2. Ask where each thing is answered

A quote is an answer you can find in the document. "Not found" gives Copilot a way to report a gap
instead of guessing.

1. Enter:

> Read the three documents in the docs-practice folder of the copilot-practice folder.
> For each item in what-support-needs.md, quote the passage that answers it and name its document, or write "not found".
> Don't fill gaps from general knowledge.
> Don't change any file.

Check: who to call and how to restart Order Tracker are among the items "not found". Pick one item
that has a quote. Open the document it names, and find the quote there.

If who to call or how to restart Order Tracker has a quote, open the document it names and read
it. A quote such as "Contact: to be confirmed" doesn't answer the item. If that's what you find,
tell Copilot so, and ask it to mark the item "not found".

## 3. Turn the gaps into questions

1. In the same chat, enter:

> In the docs-practice folder, create gaps.md: each item marked "not found", written as a question I can send to the team that owns Order Tracker.
> Add or change no other file.

2. In the list on the left, right-click `gaps.md` and select **Open Preview**.

Check: `gaps.md` has a question for each item marked "not found".

To use documents you were handed: save them in one folder with your own list of what you need,
and open that folder. Send the same requests, except the one that creates practice files. Use your
files' names and your application's name, and leave out the practice folder names.

If it does not work: [Help](../../troubleshooting.md).
