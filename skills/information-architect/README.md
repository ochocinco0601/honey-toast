# Information architect and librarian

For the assistant reading this in a clone of this catalog: these files are to be installed into the person's working repository, not used where they sit.

## What it is

A skill and an agent that ship together, to keep a repository organized for the person who works in it and for every session that has to find its way around it:

- **The information architect** (this folder's `SKILL.md`), a skill. It runs in the person's own session, so they talk with it directly: it surveys the whole repository, shows them its understanding of how the place is organized and used, asks only what the files cannot tell it, and works out with them what to improve and a written working model. From then on it answers "where does this go?", works the cases the model does not cover, and reviews the structure as the work changes.
- **The librarian** (`agents/librarian.md`), an agent. Any session calls it after creating, moving or renaming documents, for an independent check, in its own context, that the work went where the agreed model says. It reports fixes to the session and logs what the model cannot settle as open cases for the architect.

## Install

In the person's working repository:
1. Copy this folder's `SKILL.md` into `.claude/skills/information-architect/`. It replaces any earlier `SKILL.md` there: the earlier version's was only a short pointer to an agent file and holds nothing to keep.
2. Copy `agents/librarian.md` from this catalog into `.claude/agents/`. If a `librarian.md` is already there, compare them and keep the person's changes; never overwrite their working copy blindly.
3. Remove `information-architect.md` from `.claude/agents/` and from `~/.claude/agents/` if an earlier version left it in either: the architect is now the skill, and the old agent file would compete with it.
4. Start a new Claude Code session so the skill is picked up.

Nothing else is needed: no scripts, no settings. Neither changes the person's files until they agree, except the architect's own draft working model, which it creates and tells them about.

## Start

In a Claude Code session in the repository, type `/information-architect`, or ask it to help organize the repository. The architect surveys the whole repository, tells the person what it understands about how it is organized and used, and asks only what it could not read for itself. Once the person agrees a working model, the architect adds one line to CLAUDE.md, and from then on every session knows to call the librarian after filing.
