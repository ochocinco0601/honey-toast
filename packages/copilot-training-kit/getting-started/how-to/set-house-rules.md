# How to: set house rules once

**You end with:** an instructions file in your folder that the assistant follows every time,
without you restating it.

**Before you start:** VS Code open with this training's folder, the chat in Agent mode. New to it?
Do [Start here](../start-here.md) first. If you have done the
lessons, try writing the request yourself first, then compare it with the one below. About ten
minutes.

**When:** you keep re-explaining the same standards: your status categories, your fiscal year,
terms you never use, the shape you want every summary to take.

1. Add the folder where you do the work to VS Code: menu File, then Add Folder to Workspace, then
   choose it. This training stays open beside it.
2. Ask, putting your own rules where the prompt says `<your rules>`. For example: our status
   categories are Red, Amber and Green; our fiscal year starts in October; never recommend a
   vendor by name; every summary ends with three next steps.
   > Create the instructions file this assistant reads automatically, inside `<your folder>`, not the training folder. Put in it: `<your rules>`.

   In VS Code with GitHub Copilot that file is `.github/copilot-instructions.md`. The assistant
   knows where it goes; you do not need to.
3. Start a new chat, with the plus button at the top of the chat panel, so it cannot remember the
   rules from this conversation. Copy any recent document of yours into the folder, a status note
   or a summary. Ask for something from it without mentioning the rules:
   > Write a three-line status note from `<your document>` in `<your folder>`.
4. Change a rule by editing the file, or by asking the assistant to change it.

**Check:** open the instructions file and read your rules there. Then read the status note from
step 3: it should follow them without being told, for example using your status categories and
ending with next steps. If it does not, the rules are not being read; ask the assistant why.

`[YOUR ORGANIZATION: any standard instructions file your teams share, and where it lives]`

If it does not work: [If something goes wrong](../../troubleshooting.md).
