# Run of show: managers and non-engineers, 60 minutes

## Objective, said aloud in the first minute

By the end, each of you can do one of these, depending on your work:

- open a folder of your own files, have the assistant do one chore across them, and check the result;
- ask an application a plain question and open a cited file to check the answer.

Say both. The room holds both kinds of people, and each will hear the one that is theirs.

## Roles

| Role | Does | Does not |
|---|---|---|
| Presenter | the screen and the narration | watch chat |
| Chat watcher | answers setup problems in chat; pastes each prompt at the moment it is used; pastes the full list at close | present |
| Host | opens, times, closes, collects suggestions | |

Confirm the chat watcher at the dry run. Without one, a session runs for minutes without anyone
knowing who is stuck.

## Before the session: what must exist

Check each of these the day before, not at minute thirty.

- A presenting machine signed in, with the chat open, the mode set to Agent, and a fresh chat
  started so no earlier conversation shows.
- A folder holding one or two real exports of the kind the room's people receive, such as a
  ticket list or a change list, with anything sensitive removed. The prompts below run against
  it the day before, so you know what comes back.
- An application already fetched onto the machine, with the orientation prompt below already
  run once, so you know it answers and cites files.
- The generated documentation for that application already produced, and open in a second
  window. A live run takes too long. `[YOUR ORGANIZATION: the generator command]`
- The prompt list below in the chat watcher's hands.
- Two skill names you can say aloud. `[YOUR ORGANIZATION: two skills your teams can use today]`
- Every blank in the kit filled. The list is at the end of this page. The blank to fill first
  is data handling: what leaves the machine, and which data may be used. Have that answer
  before the session, in writing.
- The message that will accompany the folder afterward, written; see "After the session".

## Prompts the chat watcher pastes, in order

| When | Prompt |
|---|---|
| Setup check | What can you do in this folder? |
| The workbench, live | Create a folder named practice inside this folder, and inside it a file named hello.txt that contains today's date. |
| The workbench, live | Read `export.csv` in `<your folder>`. Tell me the columns and how many rows. Then give me the top ten categories by count and the trend by week. |
| The workbench, live | Which assignment group has the oldest open items? Show the ten oldest with their age in days. |
| Bring an application to the bench | I need to inspect this application. Clone the repository at `<address>` into the `practice` folder so we can analyze it. |
| Bring an application to the bench | What does this application do, what business problem does it solve, and who uses it? You sometimes make mistakes, so cite the files that support each part of your answer. |
| Bring an application to the bench | Open the first file you cited and show me the lines that support the "who uses it" claim. |
| The generated pages | The generator command: `[YOUR ORGANIZATION: the command to run the generator]`. Without one, paste: Write a set of pages in the `practice` folder about this application, starting with an index: what it does, its main parts, what it depends on and what depends on it, the business rules in the code, its data, how it handles errors, and which files a new owner should read first. Cite files on every page. |
| Check one claim | You say that [the claim]. Show me the file and the lines that support it. |
| Close | All of the above, as one message. These prompts are word for word the ones in README.md, the application lesson and the export recipe, so the room can match what is pasted to what they are reading |

## Method, every segment

Name the idea. Show the difference in kind, hands on a working set of files versus reach across
shared content, and never as a shortfall of the office assistant the room already uses. Do the
two-minute exercise. The ideas are numbered in `explanation.md`; the column below says which one
each segment carries, so the room hears the idea, not only the clicks.

## Timeline

| Minute | Segment | Idea | Notes |
|---|---|---|---|
| 0–3 | Open | | The objective. One question to the room before anything else: "What do you think this tool is?" Read two answers aloud; the difference-in-kind segment answers them. The rule: setup problems go to chat. Setup check on a 60-second clock: any prompt that gets a reply, with the chat in Agent mode. Move on at 60 regardless |
| 3–6 | Three landmarks | 4 | The list of files on the left, the chat, the reading pane in the middle. Give permission to ignore everything else. When you do not know where something is, ask the assistant |
| 6–8 | The difference in kind | 1, 2 | The office-suite assistant reaches across mail, chats, meetings and shared files, and this does not replace it. This one works on a folder on your machine: point it at your downloads folder and tell it to organize it, and it leaves its work there for next time. Say it as a difference in kind, never as a shortfall of the tool they already use |
| 8–18 | **The workbench, live** | 1, 3, 8 | Create a folder by prompt; show the permission prompt as the guard. Then the real one, on real files: open a folder holding one or two exports the room's people actually receive, such as a ticket list or a change list, and ask what it is about, then one question a manager would ask of it. Say you gave it the finish line, not the steps. If no export is to hand, organize a messy folder by prompt instead, plan first, then move. This is the segment for everyone whose work is files. Show it, do not describe it |
| 18–22 | Check the receipts | 9 | Ask a question about the folder's files with "cite the files". Open one. Say it aloud: an answer with no source is a guess |
| 22–30 | Bring an application to the bench: lesson steps 1 to 3 | 4, 10 | Say once: watch my screen, follow on the page, type along if you are set up; if something does not work, note it and keep watching. Clone by prompt; you did not learn a command, the assistant operated the tool. The orientation question with citations. Open one cited file |
| 30–38 | The generated pages, and one claim checked: lesson steps 4 and 6 | 6, 9 | Announce the cut: what you are about to see was generated before the session; theirs takes five to ten minutes and they run it afterward. Open the index, press Ctrl+Shift+V on screen, open the overview. Then two minutes on step 6: one claim, the file it came from, the three kinds of claim in a sentence each, and the judgment line said aloud. Steps 5 and 7 are theirs afterward; say so. `[YOUR ORGANIZATION: generator command]` |
| 38–42 | Skills, house rules and tools, in one breath | 5, 6, 7 | A skill is a text file; name the two from the preparation list; say you can ask for one. Say that standards can be written once in the folder. Say it can write and run a small program for a batch job you would never do by hand. Do not tour any menu |
| 42–45 | Recap | | The three lines below. Chat watcher pastes all prompts |
| 45–60 | Questions | | Keep the last fifteen minutes. A first run fills them |

## Pre-empt the wrong answer

Say early that the assistant will sometimes be confidently wrong, and that if it happens you will
show it, because checking the answer against the file is the skill being taught. A wrong answer
then lands as the lesson, not as the demo failing. If nothing goes wrong, say what you would have
checked.

## Cost

If your organization meters usage, show where the meter is once, and answer the question a manager
actually has: what a team's normal week costs, not what one prompt costs. Do not put figures in
this kit.

## Recap, said aloud

1. The assistant sits at your desk with your files. Bring it to your work.
2. It has hands. It does the chore. It asks first.
3. Check the receipts. An answer with no source is a guess.

## After the session: how to send the folder

A folder does nothing on its own. When a learner opens it they see a list of nine names and
nothing else happens, so the message that delivers it has to carry the first three clicks.
Send the kit folder itself, so the first thing a learner opens is README.md. Send it however
your organization shares files, and put this in the message, in these words or yours:

> Open VS Code. Menu File, then Open Folder, and pick the folder you saved. In the list on the
> left, click README.md. If it shows as plain text with symbols, press Ctrl+Shift+V. Follow the
> steps on that page; they take about fifteen minutes and lead into two short lessons, in
> order.

If the folder is shared as a repository, README.md shows itself on the repository's web page
before anyone clones it; say so in the message and give the address.

One week later, ask one question. See `evaluation.md`.

## Blanks to fill before sending

Every place the training says `[YOUR ORGANIZATION: ...]` is listed, by file, line and section, in
`BLANKS.md` beside this file. The list is rebuilt each time the pages are built, so it is always
current. Fill them once in your copy. The one on the critical path is the repository address in
`lesson-application.md`; without it the application lesson stops at step 1.

Without the build, find them in VS Code: press Ctrl+Shift+F and search for `[YOUR ORGANIZATION`.
