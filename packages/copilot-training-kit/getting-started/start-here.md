# Start here: your first fifteen minutes

The first unit of the training. You end with a folder the assistant made on your computer, and a
check you did yourself. Before you begin, see [Before you start](README.md#before-you-start).

Do these in order. Nothing here changes a file you already have.

## 1. Open VS Code

Press the Windows key, type `code`, and press Enter. A program called Visual Studio Code opens.

Check: a window titled Visual Studio Code, usually showing a Welcome page. If nothing by that name
appears, see [Getting set up](../troubleshooting.md#getting-set-up).

## 2. Open this training in VS Code

If this training is already on your computer: menu File, then Open Folder. Choose the training's
own folder, the one that contains the `getting-started` and `read-in-browser` folders (not either
of those), and
click Select Folder. Reading these pages in a browser? The browser's address bar shows where they
are: the training's folder is the one that holds `read-in-browser`.

If you were given its web address instead: on VS Code's Welcome page, click Clone Git Repository,
paste the address, press Enter, and choose where to save it; your Documents folder is a good
place. When VS Code asks whether to open it, click Open. `[YOUR ORGANIZATION: the training's address]` If VS Code says Git is not installed,
asks you to sign in, or the copy fails, see
[Copying the training or an application fails](../troubleshooting.md#copying-the-training-or-an-application-fails).
If it came as a zip file, see [The training came as a zip file](../troubleshooting.md#the-training-came-as-a-zip-file).

A box may ask whether you trust the authors of the files. This training is plain text pages, so
click the button that begins "Yes, I trust".

Check: the list on the left of VS Code includes `README.md` and the `getting-started` folder. If there is
no list on the left: menu View, then Explorer.

To read these pages inside VS Code as pages rather than raw text: click `README.md` in the list,
then press Ctrl+Shift+V.

## 3. Open the chat and choose Agent

Menu View, then Chat. A chat box opens, usually on the right. At its bottom is a small mode
selector. It should say Agent; if not, click it and choose Agent. Agent means the assistant may
do things, not only answer.

Check: the selector reads Agent. If the chat asks you to sign in, or no chat appears, see
[Getting set up](../troubleshooting.md#getting-set-up).

## 4. Say something

Type this into the chat box, or paste it, and press Enter:

> What can you do in this folder?

Check: a reply arrives within a few seconds. What it says does not matter yet; that it answered
does.

## 5. Ask it to explain the next step

This training's pages are in the folder you opened, so the assistant can read them. From now on
it is also your helper. Try it before you need it:

<!-- tutor -->
> Read getting-started/start-here.md in this folder. In plain words, what does step 6 ask me to do, and what will I see? Do not do it yet.

Check: compare its answer with step 6 below. If they differ, the page is right; tell it so. Its
directions about VS Code are sometimes for a different version: your screen is the truth.

## 6. Have it do one real thing

Type or paste:

> Create a folder named practice inside this folder, and inside it a file named hello.txt that contains today's date.

Before the assistant runs a command on your computer, it asks you: a button appears in its reply.
That question is the safeguard, so read it before you answer; see
[Reading a permission request](#reading-a-permission-request) just below. It may also create or
edit files in the folders you opened without asking; when it does, the reply lists the changed
file with Keep and Undo. Click Keep when the file is what you asked for; Undo removes the change. Here, whichever happens, it should only create one folder and one file.

Check: on the left, a folder named practice appears; click it, then hello.txt, and it opens with
today's date. Open Windows File Explorer and go to the training's folder: the practice folder is
there, on your disk.

### Reading a permission request

The request has two buttons: Allow, and one beside it that declines (it may say Skip or Cancel).
Declining is always safe: nothing runs, and the assistant waits for you. You do not need to
understand the whole command. Look for three things:

1. **Which folder.** Does it name only the folder you asked about? A folder you did not mention
   means decline.
2. **Danger words.** Remove, Delete, del, rm, Move, mv, Rename. If you did not ask for something to
   be deleted, moved or renamed, decline.
3. **Too long to read?** Decline it, then ask the question below. If its answer names only what
   you asked for, reply "Go ahead". It asks again; this time, allow it. Afterwards check the list
   on the left: its answer is a claim, not proof.

<!-- tutor -->
> In one sentence, which files will this create, change, move or delete? Name the folders.

An example to decline: you asked for a new file, and the request reads
`Remove-Item -Recurse practice\old`. That deletes a folder you did not mention. Decline it.

Practise: you asked the assistant to write `summary.md` in your folder `team-notes`. Allow or
decline each of these?

- a. `New-Item team-notes\summary.md`
- b. `Move-Item team-notes\*.docx archive\`
- c. A long program that ends by writing `C:\Users\you\Documents\team-notes\summary.md`

Answers: a, allow: it creates the file you asked for, in your folder. b, decline: it moves files,
and you did not ask for a move. c, too long to read: decline, ask which files it will create,
change, move or delete, and allow it when the answer is only `summary.md` in `team-notes`.

While you are learning, do not choose any option that allows commands without asking.

## 7. Have it look at your real files, changing nothing

If your Downloads folder holds exports from work systems, use your Documents folder instead, and
change the prompt to match. This request reads only the names and sizes of files, not what is in
them. Type or paste:

> Look at my Downloads folder. Tell me how many files are in it, grouped by type, and name the five largest. Do not move, rename or change anything.

If a permission request appears, read it as above, then click Allow.

Check: open the same folder in Windows File Explorer, sort by size, and compare the largest file
with what the assistant named. If they differ, say so:

> That is not the largest file. Look again.

## You have done the thing

You told an assistant what you wanted in plain words, watched it act on your computer, and checked
its work against what you can see yourself. Everything else here is that same move on things that
matter to you.

Look back at step 7's request: it said which folder, what to find, and what not to do. In the
next lesson you learn to write requests like that yourself.

Next: [Lesson: your own files](lesson-your-files.md).
