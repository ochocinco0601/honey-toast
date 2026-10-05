# Help

## When you're stuck, ask Copilot

Copilot can see your chat, so it can tell you what happened and what to try.

**On a step:** most steps have **Stuck? Copy a question for Copilot** under them. Select it and
paste into the chat box. The question asks Copilot to explain the step without doing it for you.

**A request that didn't do what you expected:**

<!-- tutor -->
> My last request didn't do what I expected.
> Tell me what you did, what went wrong, and what I should try next.
> Don't change anything.

**An error in the chat:**

<!-- tutor -->
> Explain the last error in this chat in plain words.
> Tell me the one thing to do next.
> Don't change anything.

**What Copilot has done so far:**

<!-- tutor -->
> List every file you created, changed or deleted in this chat.

## Getting set up

### VS Code doesn't open

If pressing the Windows key and typing `code` finds nothing, VS Code isn't installed. Install it
from your company's software portal, then try again.

### The chat asks you to sign in, or doesn't answer

Copilot is built into VS Code; there's nothing to install. In order:

1. At the bottom of the VS Code window, hover over the Copilot icon. If it offers **Use AI
   Features** or **Sign in to use Copilot**, select it and sign in with your work GitHub account.
2. Update VS Code: install the newest version your company's software portal offers.
3. If a reply says you've sent too many requests, wait a few minutes and send it again. If it says
   you've used your monthly allowance, select the Copilot icon at the bottom of the window to see
   your usage; the allowance resets each month.

<!-- more: Signed in with the wrong account -->
Select the **Accounts** icon at the bottom of the bar on the far left of the window, then
**Sign out**. Then sign in again from the Copilot icon with your work GitHub account.
<!-- /more -->

### The chat isn't there

On the **View** menu, select **Chat**. Or press Ctrl+Alt+I.

### Copilot answers but doesn't create or change files

Copilot may be set to another agent. Select the chat box, hold down Ctrl, and press the period key (.). The list of agents opens, with the selected agent marked. Select **Agent**. If **Agent** is already selected, Copilot may be set only to plan the work. A control below the chat box, not inside it, then shows **Plan**. In a narrow chat, it shows only an icon. Select **Plan**, and then select **Interactive** in the list that opens. With **Interactive**, Copilot does the work instead of only planning it.

## While Copilot is working

### Nothing seems to happen, or it's taking a long time

A moving indicator in the chat means Copilot is still working. Some requests take a few minutes.
To change course, type what you want instead and press Enter. Copilot finishes its current action, and then takes your new message.

### A panel full of text opened at the bottom of the window

That's the terminal, where the commands Copilot runs show their output. You don't need to type
there.

### A permission request you don't understand

If you can't tell whether the command matches what you asked for, select **Skip**. Nothing runs. Then send:

<!-- tutor -->
> What command did you want to run, and which files and folders would it have changed?
> Don't run it.

More on reading one: [Reading a permission request](getting-started/start-here.md#reading-a-permission-request).

### Copilot asks you a question, or offers choices

Answer in the chat box, as you would answer a person.

### Copilot says it can't read a file

Word, Excel and PDF files aren't plain text, so Copilot may ask to run a small command to read them. If it
reads the file you named, allow it. If it still can't, save the file as plain text (for an Excel file, choose CSV in Save As) and ask again.

### The reply is too long or too technical

Say so in a follow-up:

> Explain that in plain words, in five lines or fewer.

## When the result is wrong

### Copilot says something you can't find in the file

Ask Copilot:

> Name the file and line numbers where that is, and quote those lines.

If the quote isn't in the file, send:

> That isn't in the file. Look again, and quote only what's in the file.

### Copilot changed something you didn't want changed

Hover over the request that made the change and select **Restore Checkpoint**, as in
[Undo the table](getting-started/lesson-your-files.md#3-undo-the-table).
Restore Checkpoint puts the files back as they were before that request, and removes that request
and every later one from the chat. It doesn't reverse a
command already run, such as a move or a delete.
For those, ask:

> List every file you moved or deleted in this chat, and put each one back where it was.
> If you can't restore one exactly, say so instead of recreating it.
> Change nothing else.

### Copilot worked in the wrong folder

If the files it changed are in the folder you have open, select **Restore Checkpoint** on that
request. For files anywhere else, use the request in
[Copilot changed something you didn't want changed](#copilot-changed-something-you-didn-t-want-changed).
Then ask again, and name the folder in the request.

### Copilot has forgotten what you did

A new chat starts empty, but the files stay. Name the file in your request, for example:

> Read actions.md in the copilot-practice folder and continue from there.

### The chat is going in circles

Select **New Chat** (+) at the top of the chat, and ask again in one request: which folder, what to
read, what to make, and where to put it.

## Skills and custom agents

### A skill isn't used, or does the wrong thing

Tell Copilot what you asked and what happened, and ask it to review the skill and fix it. A skill
saved in a folder works only while that folder is open; one in your personal skills folder works
everywhere.

### A custom agent isn't in the list of agents

Ask Copilot:

<!-- tutor -->
> List the custom agent files in the .github/agents folder of the folder open in VS Code.
> Also list those in my personal agents folder: the agents folder inside .copilot in my user folder.
> For each, check where it is saved, that its header is complete, and that nothing in it hides it from the list.
> Tell me which of them VS Code can't list, and why.
> Don't change any file.

Then ask Copilot to fix what it found.

## Questions

### Do I need to write code?

No. You ask in plain words, and Copilot reads and writes the files.

### Is this the same as Copilot in my office suite?

No. That one reaches across the shared content at your work: mail, chats, meetings and shared
files. This one works on a folder of files on your computer and can act on them.

### Can Copilot reach other systems, such as a ticketing system, directly?

Only through a connection to that system; VS Code calls these MCP servers. Without one, export the
data to a file and ask Copilot about the file.

### How do I put the chat on the other side of the window?

Ask Copilot:

> How do I put the chat on the other side of the VS Code window?
> Tell me the steps; don't change anything.
