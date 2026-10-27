# Operating model

`operating-model.md` sets out how an assistant starts a job for a person: work that produces something, changes something lasting, or runs past one exchange. It reads the situation through a few lenses: what kind of problem this is, whether it is a retrofit or a new build, and where in the service lifecycle it sits. It then proposes the job's five terms (standards, plan, finish level, inspection, coordination), each with a recommendation, and agrees them with the person before doing the work. A quick question gets a direct answer, and a subagent works inside the terms its brief carries. The model treats the person as the stakeholder, who gives intent and judgement, not as the expert: the assistant does the reading, drafting and checking itself. The file is written for the assistant to read.

## Install for Claude Code

1. Copy `operating-model.md` to `~/.claude/operating-model.md` (on Windows, `%USERPROFILE%\.claude\operating-model.md`).
2. Add this line to your user-level instructions file, `~/.claude/CLAUDE.md`. Create the file if it does not exist.

   > **How the person's work is approached** (reading the situation; the five terms of a job; their role): `~/.claude/operating-model.md`.

3. Check it: open a new session and ask for a small job that changes a file. The first reply should propose the five terms, each with a recommendation, and wait for your agreement before starting.
