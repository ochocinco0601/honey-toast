# Analyze an exported spreadsheet

**You end with:** `analysis.md`, with counts and the oldest open tickets from a CSV export,
and one figure you checked yourself.

**You need:** the copilot-practice folder open in VS Code. If another folder is open, on the **File** menu, select **Open Recent**, and then select
`copilot-practice`.

**When:** a system gives you a CSV export, such as a ticket list or an incident list, and you need
counts or the oldest items.

## 1. Have Copilot create a practice export

A made-up export gives you tickets to count without using real data.

1. If the control at the bottom of the chat box doesn't show **Agent**, select the control, and
   then select **Agent**.
2. In the chat box, enter:

> In the copilot-practice folder, create a folder named export-practice.
> In it, create tickets.csv: 40 rows of made-up service desk tickets.
> Give it the columns Ticket, Opened, Category, Group and Status.
> Use five categories.
> Make 15 tickets Open and the rest Closed.
> Add or change no other file.

3. In the list on the left, expand `export-practice`, and select `tickets.csv`.

Check: the first line holds the five column names, and each line after it is one ticket, with
commas between the values. The last ticket is on line 41, so there are 40 tickets. If the last ticket is on another line, subtract one from that line number. That's how many tickets
to expect below.

## 2. Ask your questions, and ask how Copilot got each figure

Asking how it got each figure tells you what to check.

1. Enter:

> Read tickets.csv in the export-practice folder of the copilot-practice folder.
> Tell me how many tickets it has, and how many are in each category.
> List the ten oldest open tickets, with their age in days as of today.
> For each figure, say which column and which filter you used.
> Don't change any file.

2. If a permission request appears, allow it if it reads only `tickets.csv`.

Check: the reply counts all the tickets, gives a count for each category, and names the column and
filter behind each figure.

## 3. Check one figure yourself

Counting one figure yourself shows whether Copilot counted the way it said it did.

1. Take the category with the fewest tickets in Copilot's answer. If two tie, take either. In
   `tickets.csv`, count that category's tickets yourself.

Check: your count matches Copilot's. If it doesn't, enter:

> How did you count the category with the fewest tickets?
> List the rows you counted.
> Don't change any file.

Compare its list with the file. If Copilot's count was wrong, tell it which rows it got wrong, and ask
it to correct its figures before you save them.

## 4. Save the answers

1. In the same chat, enter:

> In the export-practice folder, create analysis.md with the category counts and the ten oldest open tickets from your answer, and a one-paragraph summary.
> Add or change no other file.

2. In the list on the left, right-click `analysis.md` and select **Open Preview**.

Check: the preview shows the counts and the ten oldest open tickets, and the category you counted
has your count.

To use your own export: save it as a CSV file in a folder, and open that folder. Send the same
requests, except the one that creates practice files. Use your file's name, and leave out the
practice folder names.

If it does not work: [Help](../../troubleshooting.md).
