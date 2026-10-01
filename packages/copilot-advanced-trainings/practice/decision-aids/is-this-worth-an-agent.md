# Is this worth an agent?

Keep this page. An agent is worth making when most of the left column is true.

| Worth an agent | Not worth one |
|---|---|
| The work is the same kind each time: reviewing, analysing, checking | Every time is different, or it happens once |
| You want the report, not every step that produced it | You want to watch and steer each step |
| It should be able to read but not change files | It has to change files, and you would not check each change |
| The report can have a fixed layout you check quickly | You cannot say what a good report looks like |
| It can say what it could not do, and you will read that part | You would only read the conclusion |

Before handing work to an agent, decide how you will check its report: which one finding you will
trace back to the file it names.

## Worked cases

Decide each one yourself before reading the answer.

**1. Operations.** "Each week, find the problems that keep coming back in the ticket export."
Worth an agent, or a skill. Same kind of work each time, the report has a fixed layout, and it
never needs to change the export. Check: open the export and find the tickets it names for one
repeated problem.

**2. Operations.** "Reorganize my team's shared folder into a new structure."
Not worth an agent. It changes many files, and you want to approve the plan before anything moves.
Use Agent mode with a request that says to show the plan first, as in the recipe Organize a folder.

**3. Managers and analysts.** "Before each review meeting, tell me what the runbook leaves out."
Worth an agent. A read-only reviewer with a fixed report of gaps, each quoting the line it is about.
Check: open one quoted line and judge whether the gap is real.

**4. Managers and analysts.** "Help me think through which of two options to recommend."
Not worth an agent. It is a conversation, not a handoff; you want to steer every step. Use the chat.

**5. Engineers.** "Check every change request against the checklist before the approval board."
Worth an agent. Repeated, read-only, and the report is a go or no-go table you can check line by
line. Check: pick one No-go and confirm the missing item is really missing.

**6. Engineers.** "Fix the failing tests in this application."
Not an agent for everyone. It changes files and runs commands. Engineers who use agents that change
files do so with checks set up in advance; that is the later training, not this one.
