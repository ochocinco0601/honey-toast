# How to: find what is missing from documentation you were handed

Assumes you have finished `README.md`: VS Code open, this training folder open, the chat in Agent
mode. About fifteen minutes.

**When:** an application team has sent you their documentation, an engineering spec, an export
from the wiki, a game plan for a release or an event, and you have to support or approve
something on the strength of it. You need to know what it does not say before you need it at
two in the morning.

1. Save the documents into one folder. If they live in a wiki, export or copy them to files
   first; the assistant reads files. Write a second short file, `what-support-needs.md`, listing
   what you need to find in any application's documentation: who to call, what it depends on,
   how to tell it is healthy, how to restart it, known failure modes, whatever your team's list
   is. Add the folder to the workbench: menu File, then Add Folder to Workspace.
2. Ask:
   > Read every document in `<your folder>`. For each item in `what-support-needs.md`, say where in the documents it is answered, quoting the passage, or write "not found". Do not fill gaps from general knowledge.
3. Ask for the list you will send back:
   > Write `gaps.md` in `<your folder>`: the items marked not found, each written as a question I can send to the application team.
4. If the documents disagree with each other, ask it to list the contradictions with both
   passages quoted.

**Check:** open one item marked "answered" and read the quoted passage in the source. Open one
marked "not found" and search the documents yourself for the obvious word; if you find it, tell
the assistant it missed one and ask it to look again.

**Why this works:** the assistant is good at reading a lot of text against a short list. It is
not good at knowing what your team needs; that is what the list is for, and it is worth writing
once and keeping.
