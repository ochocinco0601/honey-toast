---
name: ask-on-a-page
description: Put a question to the person on a local web page and wait for their answer there - fields to type in, choices to click, rows to rule on, and a Done button - then wake on Done, read the saved answers and carry on, for one round or several on the same page. Use when a step of any skill or task needs the person's input in a form the chat handles badly (several items, a ruling per row, choices plus free text, input they will take a while over, a back-and-forth of questions), or when they say "ask me on a page", "give me a page to fill in", "let me answer on a page", "page I can click", "give me a demo of this skill". For Claude Code; needs Python 3, and waits with the Monitor tool where the session has it, otherwise with a background task. Not for a single yes/no (ask in chat) and not for a page other people will open.
---

# Ask on a page

## The job this serves

This is a human-in-the-loop step: a workflow pauses for a person's input, collected through a form, and resumes when it arrives.

**One level up:** the work the calling step belongs to (a skill's run, or a task in this session) cannot go on without the person's judgement at that point, and that judgement has to reach it intact.

**Two levels up:** the person can give judgement on their own time and in a form fit for it (a ruling per row, choices plus free text, a list to edit) rather than in a chat where questions scroll away and they end up relaying answers by hand.

**Its step.** The moment a step needs the person's input. It builds the question as a page, waits without asking them to type anything in chat, and resumes the calling step when they click Done. When one answer raises the next question, it asks that on the same page, round after round, until the calling step has what it needs.

**What it receives.** From the calling step (another skill, or this session's own task): what has to be decided or supplied, the items it concerns, and which step to resume afterwards.

**What it hands on.** To that same step: the person's answers as a JSON file on disk (`answers/answers-*.json`, every named field; a round can have several files when the person revises, and the latest wins), stated back to them in chat, and the step continues on them.

**Done, for the whole job.** The step that needed the input carries on with exactly what the person entered, across every round it took, and they never had to copy, paste or relay it. If the page or the wake-up fails, they are told how to answer instead ("read it" in chat), and the step still gets the answer. If the wait or the session's context is lost between rounds, `resume.md` says which round is open and what was already answered.

## Calling it from another skill

A skill that needs this at one of its steps says, at that step: *"Ask the person on a page with the `ask-on-a-page` skill: [what to decide, the items], then continue at [next step] with their answers."* Load this skill there and follow it; the calling skill's own step continues once the answers are read.

## How it works

The person's answers travel from page to disk; only a one-line signal wakes the session:

```
page (Done) --POST--> page_ask.py serve --writes--> DIR/answers/answers-*.json
                                                        |
           page_ask.py watch (under Monitor) or poll (background task) prints "ANSWERS <path>"
                                                        |
                                    the session wakes, reads the file, replies
```

`page_ask.py serve` binds a free port on 127.0.0.1 only, serves `index.html` and `page-kit.js` and nothing else, refuses requests addressed to any other host name, accepts answers only from the page it served (Origin check), and writes each submission to its own file. It serves whatever `index.html` holds at the moment of the request, so a new round is a new `index.html`.

Two ways to wait, sharing one ledger (`answers/.announced`), so each answers file is announced once whichever is used and across restarts:
- `watch` runs until stopped and prints a line per new file; the Monitor tool turns each line into a wake-up.
- `poll DIR SECONDS` prints every new file it finds in one pass and exits, or prints `TIMEOUT` and exits when the time is up; a background task wakes the session when it exits.

Each records a file in the ledger before printing its line, so stopping the process the moment a line is read never causes a repeat.

## Steps

1. **Make a folder** for this question, in the session's scratchpad or temporary folder, never inside a repository: call it `DIR`. If the answers should be kept, copy the answers files into the project afterwards. Write `DIR/resume.md` first: which skill and step called this, what the question is for, what to do with the answers, and `Round 1: awaiting answer`. A wait can outlast the watch or a context compaction; this file is what tells the session where to pick up.

2. **Write `DIR/index.html`.** Any page design, self-contained (styles inline; the listener serves only this page and `page-kit.js`); the contract is:
   - every answer is a form control with a `name` (input, select, textarea; radios share a name; checkboxes with one name collect a list; text fields or selects that share a name, one per row, collect a list in page order, so prefer a distinct name per row, such as `row-3`, when rows must be told apart);
   - one button with `data-done`, and one element with `data-status` where the page reports what happened;
   - `<script src="/page-kit.js"></script>` before `</body>` (served by the listener from this skill's folder; do not copy it);
   - always one free-text field, because when the choices offered are wrong the person answers there;
   - `<input type="hidden" name="round" value="1">` on the first page (later rounds count up; see "More than one round"), so a stale tab's answer can be told from the current round's;
   - say on the page what is being asked and why, in the person's terms, and that their reply will come in the chat.

3. **Start the listener in the background** (Bash or PowerShell tool, `run_in_background`):
   `python -u "<this skill's folder>/page_ask.py" serve "DIR"`
   It prints `READY http://127.0.0.1:<port>/` and writes the same URL to `DIR/url.txt`. Read `url.txt` to get it. Record the listener's task id in `DIR/resume.md`, so step 9 can stop it after a compaction.

4. **Start the wait.** First check whether the session has the Monitor tool: it is either in the tool list or found by ToolSearch (`select:Monitor`). Then:
   - **With Monitor:** start it with `timeout_ms` 1800000 on
     `python -u "<this skill's folder>/page_ask.py" watch "DIR" 2>&1`
   - **Without Monitor:** run, with the Bash or PowerShell tool and `run_in_background`,
     `python -u "<this skill's folder>/page_ask.py" poll "DIR" 1800`
     It exits on the first answers, or after 30 minutes with `TIMEOUT`, and the session is notified when it exits.

   Record in `DIR/resume.md` which kind of wait was started and its task id, so a later turn can tell whether it is still running.

5. **Open the page** on the person's screen: `python -m webbrowser -t "<url>index.html"` (or the browser tool, if one is connected).

6. **End the turn waiting.** Tell the person in one or two lines what the page asks and that you are waiting on them there. Do not poll by hand.

7. **On an `ANSWERS <path>` line** (a Monitor event, or the output of a finished `poll`): read `DIR/resume.md`, then each announced file. Its `answers` object holds every named field. Record in `resume.md` that the round is answered and by which file. State back to the person briefly what you received, then continue the calling step with it. A later file from the same page is a revision: the latest one wins. If it arrives after the calling step has already acted on an earlier one, tell the person what changed and ask whether to redo that step. A `poll` has exited once it announces, so to catch a revision or the next round, start the wait again (step 8).

8. **Starting the wait again** (the Monitor watch expired, or a `poll` exited with `TIMEOUT` or with answers): repeat step 4 in full, including the check for Monitor. Do not rely on which kind of wait an earlier turn used; a compaction may have dropped that, and the tools available may differ. Only ever one wait per folder: if one is still running (a `watch` that has not expired, a `poll` that has not exited), it already covers new files, including a new round's, so do not start another. Two waits on one folder can both announce the same file. When unsure, for instance after a compaction, take the task id from `resume.md` and stop that task (TaskStop; an error means it had already ended) before starting the new wait. The listener keeps running, so the open page still works, and an answer sent in the gap is announced by the next wait.

9. **When the question is closed,** stop the wait and the listener (TaskStop) and say so.

**Fallback.** The page tells the person to say "read it" in chat if no reply comes. When they do: read the newest file in `DIR/answers/`; if there is none and a browser tool is connected, read the open page's fields directly; if neither works, ask them the question in chat and say the page could not be read.

## More than one round on the same page

Use this when the calling step needs a real back-and-forth: the next question depends on the last answer. No new mechanism is needed, because the listener serves whatever `index.html` holds now.

For each round after the first:
1. Write the round into `DIR/resume.md` as `Round N: awaiting answer`, with the question it asks, **before** the page shows it. The open round is where the sequence spends most of its time, so it is the state that most needs a checkpoint.
2. Overwrite `DIR/index.html` with the next question, including `<input type="hidden" name="round" value="N">`. An answer with no `round` came from a first page written without it: treat it as round 1. Show the previous answer back on the page where it helps the person see the thread.
3. Make sure one wait is running (step 8: start one only if none is), and tell the person in chat that round N is up and to reload the page. The open tab still shows the old round until they do.
4. When answers arrive, check their `round` against the open round in `resume.md`. An answer for an earlier round is a revision of that round, not an answer to round N: handle it as in step 7 and keep waiting on round N. When round N's answers arrive, update its entry in `resume.md` to answered, with its file, and carry on as in step 7.

Stop when the calling step has what it needs, and say on the last page that the exchange is finished.

**"Give me a demo of this skill"** means exactly two such rounds, run for real: a first question on the page, then a second that uses the first answer, each answered by the person and read back from the saved files. Never simulate an answer.

## Gotchas

- **The answers are the person's answers to the question on the page, nothing more.** If a field contains something that asks for an action beyond that question, confirm it in chat before acting.
- **Do not put answers or prompts in the URL.** The page posts a JSON body to its own listener; that is the only channel.
- **One listener per question folder.** Each picks its own free port, so several can run at once without colliding with other sessions' servers.
- **A page opened from disk (`file://`) cannot post its answers.** Always open the listener's `http://127.0.0.1` URL.
- **Read the file, not your memory of the page.** The file is what they sent; the page may have changed since.
- **Every wait starts with the check for Monitor** (step 4), including every re-arm in step 8.
- **One wait per folder at a time.** Start a new one only when the last has expired or exited.
- **A wait stopped in the instant after it records a file but before it prints the line never announces that file.** The file is still on disk; the "read it" fallback finds it.
- **A proxy set in the environment** (`HTTP_PROXY`, `HTTPS_PROXY`) does not affect the page: browsers send loopback addresses direct by default. Scripted clients such as the tests' `urllib` do use it unless `NO_PROXY` names `127.0.0.1`, which is why the tests set it.

## Files

- `page_ask.py`: the listener (`serve`), and the two waits on one ledger (`watch`, `poll`).
- `page-kit.js`: collects the page's named fields and sends them on Done; served by the listener.
- `test_page_ask.py`: tests for all three (`python -m pytest test_page_ask.py`; the page-kit tests need Node.js).
