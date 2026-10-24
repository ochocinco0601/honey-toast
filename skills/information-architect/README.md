# Information architect and librarian

For the assistant reading this in a clone of this catalog: these files are to be installed into the person's working repository, not used where they sit.

## What it is

Two agents and one command that ship together, to keep a repository organized for the person who works in it and for every session that has to find its way around it:

- **The information architect** (`agents/information-architect.md`). The person talks with it directly. It finds the structure the repository has, judges it against the field's standard, works out a written working model with the person, and from then on answers "where does this go?", works the cases the model does not cover, and reviews the structure as the work changes.
- **The librarian** (`agents/librarian.md`). Any session calls it after creating, moving or renaming documents, for an independent check that the work went where the agreed model says. It reports fixes to the session and logs what the model cannot settle as open cases for the architect.
- **`/information-architect`** (this folder's `SKILL.md`). Opens the architect in a chat, for surfaces where the `claude` command is not available in a terminal.

## Install

In the person's working repository:
1. Copy `agents/information-architect.md` and `agents/librarian.md` from this catalog into `.claude/agents/`.
2. Copy this folder's `SKILL.md` into `.claude/skills/information-architect/`.
3. If files with these names are already there, compare them and keep the person's changes; never overwrite their working copy blindly.

Nothing else is needed: no scripts, no settings. The agents write nothing until the person agrees.

## Start

Open a new Claude Code session in the repository and either type `/information-architect` in the chat, or run `claude --agent information-architect` in a terminal. The architect reads the repository, says what it found, and asks before saving its first draft of the working model. Once the person agrees the model, the architect adds one line to CLAUDE.md, and from then on every session knows to call the librarian after filing.
