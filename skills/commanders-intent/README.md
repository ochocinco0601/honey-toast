# commanders-intent

For the assistant reading this in a clone of this catalog: install it into the person's working repository, not where it sits.

## Install

1. Copy this folder to `.claude/skills/commanders-intent/` in the person's repository (or to `~/.claude/skills/commanders-intent/` for every repository).
2. Add this line to that repository's `CLAUDE.md`, with the person's yes, since that file loads into every session:

   > When you create or revise a SKILL.md or an agent definition, by any means including skill-creator or a direct edit, load the `commanders-intent` skill first and follow it.

The line is what makes it fire reliably: a skill's description alone may not be loaded alongside another authoring skill, and in a repository with many skills the descriptions can be cut from the list the assistant sees.

It works alongside `skill-creator` (the authoring skill) and calls the `independent-discipline-reviewer` agent for its review where that is installed. Neither needs changing.
