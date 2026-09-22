# How to: set house rules once

Assumes you have finished `README.md`: VS Code open, this training folder open, the chat in Agent
mode. About ten minutes.

**When:** you keep re-explaining the same standards: your status categories, your fiscal year,
terms you never use, the shape you want every summary to take.

1. Add the folder where you do the work to the workbench: menu File, then Add Folder to
   Workspace, then choose it. This kit stays open beside it.
2. Ask:
   > Create the instructions file this assistant reads automatically, inside `<your folder>`, not the training folder. Put in it: our status categories are Red, Amber and Green; our fiscal year starts in October; never recommend a vendor by name; every summary ends with three next steps.

   In VS Code with GitHub Copilot that file is `.github/copilot-instructions.md`. The assistant
   knows where it goes; you do not need to.
3. Copy any recent document of yours into the folder, a status note or a summary, and ask, using
   its real name in place of `draft.md`:
   > Review `draft.md` against our house rules and list every place it breaks one.
4. Change a rule by editing the file, or by asking the assistant to change it.

**Check:** ask "What house rules are you following in this folder?" and see whether it recites
yours.

`[YOUR ORGANIZATION: any standard instructions file your teams share, and where it lives]`
