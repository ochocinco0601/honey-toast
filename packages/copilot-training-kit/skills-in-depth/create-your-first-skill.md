# Create your first skill

A skill saves your instructions for a task, so you don't type them again. In this unit, you ask
for a meeting summary with every instruction typed out, and have Copilot save those instructions
as a skill. Then you get the same summary by asking in one line.

## 1. Have Copilot create practice meeting notes

Copilot creates meeting notes to practice on, in a new folder for this training.

1. In the chat box, enter:

> Create a new folder named skills-practice in the folder Windows uses as my Documents folder, which may be under OneDrive.
> If that folder already exists, don't change it; tell me instead.
> In it, create a folder named notes with three short, made-up notes from a weekly team meeting.
> Each note lists what was decided, and the actions with an owner and a due date.
> Add or change no other file.

2. If a permission request appears, allow it if it matches what you asked.
3. On the **File** menu, select **Open Folder**. In the window that opens, go to Documents, the same Documents that File Explorer shows on the left. Select `skills-practice`, and then **Select Folder**.
4. If VS Code asks whether you trust the authors of the files, select **Yes, I trust the
   authors**. If a bar at the top says the folder is in Restricted Mode instead, select **Manage**,
   and then **Trust**.

Check: the list on the left shows `SKILLS-PRACTICE`, with `notes` in it, and a control at the bottom of the chat box says **Agent**.

<!-- more: If no control shows Agent -->
If no control there says **Agent**, or the controls show only icons, select the chat box, hold down Ctrl, and press the period key (.). The list of agents opens, with the selected agent marked. Select **Agent**.
<!-- /more -->

## 2. Ask for a meeting summary without a skill

To get a summary the way you want it, you type out every instruction.

1. Enter:

> Summarize the meeting notes in the notes folder.
> Lead with the decisions.
> Then list the actions, each with its owner and due date.
> After each item, name the note it came from.

Check: the summary leads with the decisions, gives each action an owner and a due date, and names
the note behind each item. Without a skill, you'd type all those instructions every time.

## 3. Have Copilot save the summary instructions as a skill

Saved as a skill, these instructions are used when you ask for a meeting summary, without typing
them again.

1. Enter:

> Save the instructions from my last request as a skill named meeting-summary.
> Put it in .github/skills/meeting-summary/SKILL.md in the skills-practice folder.
> Use it whenever I ask to summarize meeting notes.
> If a skill with that name already exists, don't change it; tell me instead.
> Add or change no other file.

2. In the list on the left, expand `.github` until `SKILL.md` shows, and select it.

Check: the file holds your instructions, and a description saying to use the skill when you ask to
summarize meeting notes.

**Important:** this skill is saved in the skills-practice folder, so it works only while that
folder is open in VS Code. To have a skill work in every folder, ask Copilot to save it in your
personal skills folder instead.

## 4. Ask for the summary again, with the skill

This time you ask in one line, and Copilot follows the skill.

1. Select **New Chat** (+).
2. Enter:

> Summarize the meeting notes in the notes folder.

Check: the summary leads with the decisions, gives each action an owner and a due date, and names
the note behind each item, like the one you typed out in full.

<!-- more: If the summary isn't laid out that way -->
Copilot doesn't use a skill for every request that could match its description. Run it by name
instead: type `/meet`, select **meeting-summary**, then type `the notes folder` and press Enter.
To have Copilot find out why and fix the skill, send:

> Review the meeting-summary skill.
> Tell me why it wasn't used when I asked to summarize the meeting notes, and fix it.
<!-- /more -->

## On your own work

When you catch yourself typing the same instructions again, ask Copilot to save them as a skill,
and say when to use it. To share a skill, give someone a copy of its folder.

## What you did

You asked for a summary with every instruction typed out, and had Copilot save those instructions
as a skill. Then you got the same summary from a one-line request.

Source: [Use Agent Skills in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills), Microsoft.
