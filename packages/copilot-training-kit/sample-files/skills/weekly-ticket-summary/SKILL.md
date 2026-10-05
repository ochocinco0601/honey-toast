---
name: weekly-ticket-summary
description: Summarize a ticket export (a CSV or spreadsheet of tickets) into a one-page weekly summary with counts by category and status, the oldest open tickets, and problems that keep coming back. Use when asked to summarize, review or report on a ticket export or a list of tickets.
---

# Weekly ticket summary

**Folder:** work only in the folder that holds the ticket export the user names. If they name no
file, ask which one.

**Read:** the ticket export. Use only its columns; do not guess at values that are not there.

**Make, and where:** a file named `ticket-summary-<date of the newest ticket>.md` beside the
export, with exactly these headings, in this order:

1. `## In numbers`: total tickets, how many open and how many closed, and a table of categories
   with open and closed counts, largest first.
2. `## Oldest open`: the three oldest open tickets, each with its number, date opened, category
   and summary.
3. `## Keeps coming back`: problems that appear in two or more tickets with the same or nearly the
   same summary, each with the ticket numbers.
4. `## Worth a look`: at most three observations a team lead would act on, each one sentence.

Follow the shape of `example-result.md` in this skill's folder.

**Do not:** change, sort or rename the export. Do not copy names, email addresses, phone numbers
or account numbers into the summary, even if the export has them.

**Show your sources:** every count and every observation names the ticket numbers it comes from,
or says it is a count of the whole file.
