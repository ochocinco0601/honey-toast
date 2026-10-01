# Practice materials for the advanced Copilot trainings

The practice materials that `../README.md` lists as build items for the Skills and
Agents trainings. Whoever builds those trainings writes the unit pages; the files here
are what the units hand to learners. Everything is made up and names no organization. The skills
and agents work on the beginner kit's `sample-files` (the ticket export, the change requests and
checklist, the meeting notes).

These need VS Code with Copilot where skills and custom agents are turned on.

| Folder | What it is | Used in |
|---|---|---|
| `skills/weekly-ticket-summary/` | The starter skill, a saved five-part request with a description, and `example-result.md`, the result it should produce on `tickets.csv` | Skills: entry check, "A skill is a saved request", "Show it a good result" |
| `skills-broken/helper/` | Fault: never used. The description, "Helps with files", matches no request. Fix: say the job and when to use it | Skills: "Fix one that misbehaves" |
| `skills-broken/ticket-everything/` | Fault: used for the wrong job. The description claims every kind of request. Fix: narrow it to ticket exports | same |
| `skills-broken/ticket-summary-loose/` | Fault: different every run. The description is fine; the instructions give no layout and no example. Fix: fixed headings and an example result | same |
| `agents/ticket-analyst.agent.md` | Read-only agent for operations staff: patterns in a ticket export | Agents: worked example, operations |
| `agents/change-reviewer.agent.md` | Read-only agent for engineers: go or no-go against a checklist | Agents: worked example, engineers |
| `agents/document-reviewer.agent.md` | Read-only agent for managers and analysts: what a plan or set of notes leaves out | Agents: worked example, managers and analysts |
| `decision-aids/request-rules-skill-or-agent.md` | One-page decision aid and seven worked cases across the three learner kinds | Skills recipe; the learner keeps it |
| `decision-aids/is-this-worth-an-agent.md` | One-page decision aid and six worked cases | Agents recipe; the learner keeps it |

**Where the files go in a learner's folder:** skills in `.github/skills/<name>/SKILL.md`, agents in
`.github/agents/<name>.agent.md`. Install broken skills one at a time; together they compete for
the same requests.

**The decision aids are content for the unit pages,** not finished pages.
