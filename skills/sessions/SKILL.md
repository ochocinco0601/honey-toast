---
name: sessions
description: List the Claude Code sessions open on this machine, each with its title (in VS Code, the title on its tab), its messaging name and its session ID, or find any session (open or closed) from its tab title. Use on "/sessions", "what sessions are open", "list my sessions", "what's the ID of the X session", "which session is X", and whenever the user names another session by its tab title, e.g. "be my second set of eyes on <title>", "read <title>", "what did <title> do". Resolve the title with this before any other search.
---

# /sessions

The user names sessions by the session's title (in VS Code, the title on its tab). Nothing else they see names a session, so a session they mention must be found from that title, never guessed from what it was working on.

**Which mode.** If the message carries a session's title in any form (quoted, pasted on a line of its own, inline, or a few words of it), run **find**, whatever else is asked. Run the plain list only when no session is named. A session the user pastes a title into is often given that same title on its own tab, so in the plain list the session running it can look like the one meant; find never returns it, and the list marks it "(this session, not the one meant)".

**List the open sessions** (no session named; the user wants to see them, or "/sessions"):

```
python "<this skill's base directory>/sessions.py"
```

Reply with the table exactly as printed, nothing cut. Rows are numbered, most recently active first. If the user named a session by number ("ID of 3") or description ("the Grafana one"), put that row's identifier on its own line above the table so it can be copied in one go. Otherwise, add nothing else.

**Acting on a listed row** ("read #3", "send this to #3", "watch the retention one"): the table is already in context, so never ask for an identifier. To read it, its transcript is `~/.claude/projects/*/<session ID>.jsonl` (or run find with its title, which prints the path). To message it, use SendMessage to its messaging name, only after the user has said what to send.

**Find a session from its tab title** (the user gave a title, whatever they want done with it):

```
python "<this skill's base directory>/sessions.py" find <the title, or the words of it they gave>
```

It searches every saved conversation on this machine, open or closed, never returns the session running it, and gives each match's session ID, its messaging name if it is open, and the path to its transcript. An exact title match is preferred over partial ones; open sessions come first.

- **One match:** that is the session. Say its title and whether it is open, and go on with what was asked.
- **Several:** show the numbered table and ask which number. Do not pick.
- **None:** say so, and show the open list so they can pick from it.

Where it reads from: `~/.claude/sessions/<pid>.json` (one file per running session: ID, messaging name, status), and the tab title from the session's transcript under `~/.claude/projects/*/<session-id>.jsonl` (the last `custom-title` if the tab was renamed or forked, else the last `ai-title`). These are Claude Code's internal files, not a documented interface; if a table comes back empty or a column is blank after a Claude Code update, check those two places first.
