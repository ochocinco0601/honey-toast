---
name: session-archive
description: A personal backup of the user's Claude Code session history, kept for the number of days they choose, which Claude searches to answer questions about past work. Use when the user says "set up the session archive", "is the session archive working", or asks about earlier sessions or work, e.g. "did we work on X a few weeks ago", "which session did Y", "where did that page or file end up", "I remember we talked about Z", "find the session where...". The archive is for Claude to search; the user never reads it directly.
---

# Session archive

## The job this serves

The user works across many Claude Code sessions at once and forgets what was done where. This skill exists so they do not have to carry that in their head. Weeks later they want to recall a past piece of work, either to find where its outputs are or to pick it back up, and they ask Claude in plain words. The record is kept for the number of days the user chooses (about ten weeks by default); Claude searches it and gives back the answer.

This skill's step is to keep that record and answer from it. It receives the session logs Claude Code writes on the user's machine, and the user's question when they ask. It hands the user answers: which session it was, what they were after, and where its outputs are now. Done means that when the user asks about work from weeks ago, Claude finds the session and its outputs, or says plainly that the archive does not reach back that far. A backup that no one checks is running, or that no one searches when asked, does not count.

It is a reference only. It points to where work lives and never records what is open or done; the user's own trackers and folders do that.

## What is in this folder

- `archive.py`: copies new or changed files from `~/.claude/projects` into the archive and deletes archive copies older than `KEEP_DAYS`. It only adds files and never changes the original logs. Each run writes `_last-archived.txt`, and any file it could not copy is recorded in `_archive-errors.log`.
- `search.py`: searches the archive for words in the user's messages and Claude's replies.

The folder and the number of days are the two settings at the top of `archive.py` (`ARCHIVE_DIR`, default `~/claude-session-archive`; `KEEP_DAYS`, default 70). Changing either one is the user's call: tell them the line, the value now and the value wanted, and wait for their yes.

## Setup ("set up the session archive")

Suggest a scheduled task that runs `archive.py` once a day. On Windows that is Task Scheduler. Tell the user what you would create, and set it up only after their yes. Then run it once, and confirm that `_last-archived.txt` was written and `_archive-errors.log` is absent. Tell the user when it next runs and how to remove it.

## Answering a question about past work

1. Read `_last-archived.txt` in the archive. If it is more than a day old, or missing, say so first: the archive has stopped running, and answers may be missing recent work.
2. Search with `python <this skill's folder>/search.py "<archive>" "<regex>"`, adding `--exclude <first 8 characters>` for this session's ID if you know it. It looks only at the user's own messages and Claude's replies, leaving out injected reminders and tool output. Its first line says how far back the archive reaches. Use several spellings of the user's words, and the words a reply would have used. Earlier askings of the same question show up as hits: skip them, and follow the session they were asking about. Add `--since` and `--until` when the question gives a rough time.
3. Read only the parts of a log around a hit, never a whole log; they are large.
4. Before naming an output, check that it still exists: the file at that path, the commit in git, the page or issue.
5. Answer with: which session (date and folder), what the user was after in it, and where its outputs are now. Say how sure you are. If two sessions fit, name both. If the user wants to pick the work back up, read the last few exchanges of that session and say where it stopped and what was left unsettled there, as of that session; where the work stands now is in its real home (the file, issue or folder), so point there.
6. If the time asked about is older than the archive reaches, say so plainly. Then look for later sessions that refer back to it (they often name its files), and say that the original session itself is not available.
