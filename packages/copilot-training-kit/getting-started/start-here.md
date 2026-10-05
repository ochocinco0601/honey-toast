# Make your first request to Copilot

In this unit, you open the chat in VS Code, have GitHub Copilot create a folder to practice in, and
open that folder.

## 1. Open VS Code and the chat

You type your requests to Copilot in the chat.

1. Press the Windows key, type `code`, and press Enter.
2. On the **View** menu, select **Chat**.

Check: the chat is open, and a control at the bottom of the chat box says **Agent**.

<!-- more: If the control doesn't say Agent, or the chat won't open -->
With **Agent** selected, Copilot can run commands and create files, not only answer questions. In a narrow chat, the controls may show only icons. If no control says **Agent**, select the chat box, hold down Ctrl, and press the period key (.). The list of agents opens, with the selected agent marked. Select **Agent**. Leave the other controls as they are. If VS Code doesn't open, no chat
appears, or the chat asks you to sign in, see
[Getting set up](../troubleshooting.md#getting-set-up).
<!-- /more -->

### Reading a permission request

Copilot doesn't ask before it creates or edits files in the folder you have open. Before it runs a command that could change something on your computer, it
asks in the chat and waits.

![The Allow and Skip buttons at the bottom of a permission request](images/permission-request.png)

- Look at what it's about to do. If it matches what you asked, select **Allow**.
- If it doesn't, select **Skip**. Skipping is always safe: nothing runs.

## 2. Have Copilot create a practice folder

Your first request: Copilot makes the folder you practice in.

1. In the chat box, enter:

> Create a new, empty folder named copilot-practice.
> Put it in the folder Windows uses as my Documents folder, which may be under OneDrive.
> Change nothing else on my computer.

2. If a permission request appears, allow it if it looks for your Documents folder or creates
   `copilot-practice` there.
3. In Windows File Explorer, select **Documents** on the left.

Check: Documents has a `copilot-practice` folder, and it's empty.

<!-- more: If you can't find the folder -->
If Documents has no copilot-practice folder, tell Copilot:

> I don't see copilot-practice in Documents in File Explorer.
> Tell me where you created it.
> Create it in the Documents folder File Explorer shows, and remove the other one.
> Change nothing else.
<!-- /more -->

## 3. Open the practice folder in VS Code

Copilot works on the files in the folder you open.

1. On the **File** menu, select **Open Folder**.
2. In Documents, select `copilot-practice`, and then **Select Folder**.
3. If VS Code asks whether you trust the authors of the files, select **Yes, I trust the
   authors**. If a bar at the top says the folder is in Restricted Mode instead, select **Manage**,
   and then **Trust**.

Check: the list on the left shows `COPILOT-PRACTICE`, with nothing in it yet.

<!-- more: If the chat or file list looks different -->
VS Code reopens with the folder, and the chat starts empty. If no control at the bottom of the chat box says **Agent** now, select the chat box, hold down Ctrl, and press the period key (.). The list of agents opens, with the selected agent marked. Select **Agent**. If the list on the left is missing, open the **View** menu and select **Explorer**.
<!-- /more -->

## What you did

You opened the chat, had Copilot create a practice folder, checked it in File Explorer, and opened
it in VS Code.

Screenshots: Visual Studio Code documentation, Microsoft, CC BY 3.0.
