# Public skills to get from their publishers

Some skills in this repository rely on skills that others publish and that are not in this repository. Get each one from its publisher, at the publisher's current version, and keep the licence file that comes with it.

| Skill | Get it from | Folder in that repository | Needed by |
|---|---|---|---|
| `ux-copy` | https://github.com/anthropics/knowledge-work-plugins | `design/skills/ux-copy` | `outside-in-walkthrough` |
| `design-critique` | https://github.com/anthropics/knowledge-work-plugins | `design/skills/design-critique` | `outside-in-walkthrough` |

Install each one the same way as the skills here: copy the whole folder to `.claude/skills/<skill>/`.

## For a tool that syncs from this repository

- Each row is a package whose source is its publisher, not this repository.
- On each sync, get the publisher's current folder for every row, and show what changed since the copy already installed before installing it.
- A skill folder removed from this repository that has a row in this table has changed source. It has not been retired: do not delete it.
- A row removed from this table, with no folder for it in this repository, is a retirement.
