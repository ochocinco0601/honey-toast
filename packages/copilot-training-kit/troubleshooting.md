# If something goes wrong

Find what happened below, grouped by when it happens. Most answers end with words to give the
assistant; it can read the files in the folders you have open, including this training, and it is
usually the fastest help.

## When you are stuck, ask the assistant first

Tell it what you expected and what you see. These words work for most problems.

**A step you do not understand:**

<!-- tutor -->
> I am on step `<number>` of `<page name>` in the training folder. In plain words, what does it ask me to do, and what should I see? Do not do it for me.

**A step that did not work:**

<!-- tutor -->
> I asked you to `<what you asked>`. Instead, `<what happened>`. What went wrong, and what should I try?

**A message or error:**

<!-- tutor -->
> I see this: `<paste the message>`. What does it mean, and what is the one thing I should do next? Do not change anything.

**Something you cannot find on the screen:**

<!-- tutor -->
> I cannot find `<the thing>` in VS Code. Tell me where it is, one step at a time.

**What it just did.** Then check its list against the files yourself:

<!-- tutor -->
> List every file you created, changed, moved or deleted in this chat.

**A permission request you cannot read:**

<!-- tutor -->
> In one sentence, which files will this create, change, move or delete? Name the folders.

**A word:**

<!-- tutor -->
> What does `<word>` mean here, in plain words?

**Which recipe fits your chore:**

<!-- tutor -->
> Read the getting-started/how-to folder in the training. My chore is `<describe it>`. Which recipe fits, and what would I change in it?

**Coming back after a break:**

<!-- tutor -->
> I am coming back to the Getting started training. Look at the getting-started folder in this training, the practice folder and my own folder. Which steps look done, and which should I do next? Do not change anything.

Do what it suggests only once you have found on screen what it describes. It can be wrong about
VS Code's menus and about what it did, so check against the screen and the files. It cannot tell
you what your organization allows: whether a kind of data may be used, which applications you may
open, your licence or sign-in. For those, and for more help, see
the sections below.

## Getting set up

### VS Code will not open, or is not installed

If pressing the Windows key and typing `code` finds nothing, VS Code is not installed. You cannot
go on without it. `[YOUR ORGANIZATION: how to get VS Code and the assistant installed, and who to ask]`

### The chat does not answer, or Copilot is not responding

In order. Is the assistant installed: menu View, then Extensions, and type Copilot in the search
box; it should show as installed. Is it signed in: the account icon at the bottom left of the
window shows your name. Do you have a licence: in many organizations the assistant needs one to be
granted to you before it will answer, and an unlicensed one fails silently or asks you to sign in
again. Is the chat panel open: menu View, then Chat. If any of these fails, stop here and ask.
`[YOUR ORGANIZATION: how a licence is requested, and who to ask]`

### It answers but never does anything

The mode selector at the bottom of the chat box is not on Agent. Click it and choose Agent. In the
other modes the assistant only writes text; in Agent mode it can create files and run commands,
after asking you.

### The list on the left does not show the training's files

If there is no list at all: menu View, then Explorer. If there is a list but not `README.md` and
the `getting-started` folder, you opened a different folder: menu File, then Open Folder, and choose the
training's folder again.

### The training came as a zip file

Right-click it in Windows File Explorer, choose Extract All, and note where it went. Then open that
folder in VS Code: menu File, then Open Folder.

### The page is full of # and * symbols

You are reading the raw text of a page in VS Code. Press Ctrl+Shift+V to read it as a page.

### Copying the training or an application fails

Three usual causes: the version-control program, called Git, is not installed; you are not signed
in to the place the repository lives, called the code host; or network and proxy settings are not
in place.

If this happens while copying the training itself, the chat cannot help yet. Get the training as a
zip file instead: on its web page, the green Code button, then Download ZIP; then see
[The training came as a zip file](#the-training-came-as-a-zip-file). Or ask the person who gave you
the training.

If it happens while copying an application, ask the assistant:

> Is git installed, am I signed in to the code host, and is a proxy configured?

It will check. `[YOUR ORGANIZATION: how to install git, how to sign in to the code host, and the network setup]`

## While it is working

### I pressed Enter and nothing seems to happen, or it has been working a long time

A moving indicator in the chat means it is still working. Some jobs take minutes: a set of pages
about an application takes five to ten. If you want it to stop, use the stop control in the chat
box, then say what you want instead.

### A panel full of text opened at the bottom of the window

That is where the commands it runs show their output. You do not need to type there. If the text
worries you, copy it and ask the assistant what it means.

### It asks me to allow something and I do not understand it

See [Reading a permission request](getting-started/start-here.md#reading-a-permission-request): which folder, danger
words, and what to ask when it is too long to read. If in doubt, decline and ask:

> In one sentence, which files will this create, change, move or delete? Name the folders.

While you are learning, do not choose any option that allows commands without asking.

### A file changed and I was not asked

The assistant may create or edit files in the folders you opened without asking; only commands it
runs need your permission. When it edits a file, the reply lists it with Keep and Undo. Undo
reverses that edit. It does not reverse commands it ran, such as moves and deletions.

### It asks me a question back, or offers choices

Answer in plain words. If you are unsure, ask it which choice changes nothing.

### It says it cannot read a file

Plain text, markdown and CSV files it reads directly. For Word or Excel files it may need to write
and run a small program to read them, and it will ask permission first. If that does not work in
your setup, save the file as text or CSV and try again. Pages in a notebook application have to be
exported to a file first.

### The reply is too long, too technical, or disorganized

Say so. It redoes the work:

> Organize your response.

> That does not make sense to me; explain it in plain words.

## When the result is wrong or surprising

### It says something I cannot find in the file it names

Treat that item as a guess, and say so:

> That does not appear in the file you named. Re-do it using only what the files say, and name the file for every item.

### It did something I did not ask for

Stop it if it is still working. Then ask:

> List every file you created, changed, moved or deleted in this chat.

Check that list against the list on the left or File Explorer, since its account of itself is not
proof. Then ask it to put things back, using that list. If the chat offers to undo its edits to a
file, that undoes edits only; it does not reverse commands it ran, such as moves and deletions.
This is why the recipes that change files ask for a plan first and a record of what was done.

### It worked on the wrong folder

With two folders open, it has to be told which one. Name the folder in every request.

### It has forgotten what we did

A new chat remembers nothing of the last one; the files do. Point it at the file: "Read
`summary.md` in `<your folder>` and continue from there."

### The conversation has gone in circles

Start a new chat with the plus button at the top of the chat panel, and state the request again:
which folder, what to read, what to make, what not to do, and to show its sources.

## When to ask a person

The assistant cannot settle these, even if it answers confidently: installing or signing in,
access to an application, and what data may be used.
`[YOUR ORGANIZATION: who to ask when setup fails]` If there is no one named here, ask whoever sent you this training.
