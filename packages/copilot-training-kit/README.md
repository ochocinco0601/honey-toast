# Start here

Your work arrives as files: tickets and changes exported from a system, notes, spreadsheets, a
folder someone sent you, or an application you support and have to answer questions about. This
folder is a short training on an assistant, GitHub Copilot, that works inside a program on your
computer, Visual Studio Code, and can read and change the files in a folder you choose. In about
fifteen minutes you will tell that assistant what you want, watch it do one real thing on your
computer, and check it. Do the steps in order. Nothing here changes a file you already have.

You need a Windows computer with Visual Studio Code installed and the assistant signed in. If
step 0 or step 3 does not look like what is described, stop there and use the setup answers at
the end of `faq.md`. `[YOUR ORGANIZATION: who to ask when setup fails]`

## 0. Open the program

Press the Windows key, type `code`, and press Enter. A program called Visual Studio Code
opens. If nothing by that name appears, it is not installed: see the setup answers in `faq.md`.

## 1. Open this folder in it

If this training arrived as a zip file, extract it first: right-click it in Windows File
Explorer, choose Extract All, and note where it went.

Menu File, then Open Folder. Choose the folder you saved this training in and click Select
Folder. If a box asks whether you trust the authors of the files, click the button that begins
"Yes, I trust".

Check: the list on the left shows these names, in this order: facilitator, how-to,
explanation.md, faq.md, glossary.md, lesson-application.md, lesson-your-files.md, README.md,
skills.md, plus a folder named practice if you have done step 5 before, and possibly a few
others your organization added. If there is no list on the left, menu View, then Explorer. If
none of these names appear, you opened a different folder; do this step again.

## 2. Read this page as a page

If this page shows as plain text with # and * in it, press Ctrl+Shift+V. The same page opens
as a readable page.

## 3. Open the chat

Menu View, then Chat. A chat box opens, usually on the right. At its bottom is a small mode
selector. It should say Agent; if not, click it and choose Agent. Agent means the assistant may
do things, not only answer. If the chat asks you to sign in, or no chat appears, stop and use
the setup answers in `faq.md`.

## 4. Say something

Type in the chat box and press Enter:

> What can you do in this folder?

A reply arrives within a few seconds. What it says does not matter yet; that it answered does.

## 5. Have it do one real thing

Type:

> Create a folder named practice inside this folder, and inside it a file named hello.txt that contains today's date.

A button appears inside the reply asking whether to allow the command. Click Allow. The
assistant asks before it changes anything on your computer; that question is the safeguard. On
the left, a folder named practice appears. Click it, then hello.txt: it opens in the middle
with today's date.

Check: open Windows File Explorer and go to the folder you saved this training in. The practice
folder is there, on your disk.

## 6. Have it look at your real files, changing nothing

Type:

> Look at my Downloads folder. Tell me how many files are in it, grouped by type, and name the five largest. Do not move, rename or change anything.

Click Allow if asked. An answer arrives with counts and names.

Check: open your Downloads folder in Windows File Explorer, sort by size, and compare the
largest file with what the assistant named. If they differ, type: "That is not the largest
file. Look again."

## You have done the thing

You told an assistant what you wanted in plain words, watched it act on your computer, and
checked its work against what you can see yourself. Everything else here is that same move on
things that matter to you.

## Next: your own files, then an application

Open `lesson-your-files.md`, about twenty minutes. The assistant reads a folder of your real
files, writes something from them, and you check it. Everyone does this one first.

Then `lesson-application.md`, about thirty minutes. An application's code is brought onto your
computer, asked what it does, documented, explored, and checked. The training session walks
this one together; you can also do it alone.

Click a file's name in the list on the left, then press Ctrl+Shift+V.

## When you want it

- `explanation.md`: why this assistant differs from the one in your office suite, in ten short
  ideas. Read it after a lesson.
- `how-to/`: eight recipes for chores: organize a messy folder, summarize a folder of notes,
  analyze an exported spreadsheet, review a change request for go or no-go, find what is
  missing from documentation you were handed, write your team's standards down once, change
  many files in one go, have the assistant write reusable instructions for a job you repeat.
- `skills.md`: skills, the instruction files that make the assistant do a job your
  organization's way: how to use one, where yours are, which to start with.
- `faq.md`: the questions people ask in this training, and the setup answers.
- `glossary.md`: the words.
- `facilitator/`: for whoever runs the training for others.

`[YOUR ORGANIZATION: ...]` marks an answer that depends on your organization; whoever gave you
this folder fills it in.
