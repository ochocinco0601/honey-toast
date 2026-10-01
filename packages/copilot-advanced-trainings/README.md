# Copilot training, after Getting started — syllabus

**What this is:** the topics, order and sources for the trainings that follow Getting started,
borrowed from published courses rather than written from nothing. It is the design input for
building each training with the training-kit skill. It is not the training itself.

**Who it is for:** people who have finished Getting started's path (Start here, Your own files,
An application, First real chore). They can open a folder, write a request with the five parts
(which folder, what to read, what to make and where, what not to do, show your sources), check the
result, and they have committed to one real chore. The path does **not** make them write a skill
or set house rules; those are optional recipes, so Training 1 starts by making sure they have both.

The kit's front page already reserves two slots, "Skills, in more depth" and "Agents"; this fills
them and adds a third.

**Status:** proposed, 2026-10-01. Sources read the same day.

## Why borrowing works here almost unchanged

VS Code Copilot reads the same skill format that Anthropic's courses teach. A skill is a folder
with a `SKILL.md` file (a `name` and a `description` at the top, instructions below), and Copilot
looks for skills in `.github/skills/`, `.claude/skills/` and `.agents/skills/`. Custom agents
are `.agent.md` files in `.github/agents/` or `.claude/agents/`. So a lesson written for Claude
Code about skills or subagents needs its folder paths and button names changed, not its ideas.
Two official Copilot sources put the same topics next after the basics: GitHub's Copilot
Learning Hub (its "Advanced" articles) and Microsoft Learn's intermediate module on instructions
and custom agents.

**What to borrow:** each course's topics, order, learning objectives and worked examples.
**What not to borrow:** their pages. They are read-along courses written for engineers, and the
Microsoft module's exercise is in C#. Our trainings are hands-on: the learner does each step,
checks it against something they can see, and has a "Stuck?" route. Link to the source course
and do not paste its text.

## Rules every training follows

- **Each training has its own learner kinds.** One outcome line and one worked example for each
  of: operations staff, engineers, managers and analysts. Where a kind gets little from a
  training, say so and mark it optional for them.
- **About four hands-on units fit an hour.** Each training has a core path of four units; the
  rest become recipes, as in Getting started.
- **The outcome is behaviour a week later, not something made in the room.** Each training ends
  with a unit modelled on First real chore: the learner names the real job, the day they will
  run it, and how they will check it. Each adds one question to `facilitator/evaluation.md`.
- **The assistant operates the tool; the learner directs and checks.** As in Getting started
  (explanation idea 4). Learners read and edit what the assistant makes; they are not asked to
  create dot-folders or file headers by hand.
- **Judgment units are checked against worked cases, not a bare rule.** Where the learner decides
  something (skill or agent?), the training ships a one-page decision aid, which is also the job
  aid they keep, and six or seven worked cases from the three learner kinds with the expert's
  choice and reasoning. The check compares the learner's choice and reason with the case.

## What the trainings need

The practice skills, agents and decision aids listed as build items below are in `practice/`.

The trainings need VS Code with Copilot where skills, custom agents and connections (MCP servers)
are turned on. `[YOUR ORGANIZATION: which connections are available, for example to the ticketing system, the wiki or log search]`

## The sequence

| # | Training | For | Length | Main sources |
|---|---|---|---|---|
| 1 | Skills, in more depth | everyone who finished Getting started; optional for managers whose work rarely repeats | about 1 hour core | Anthropic Academy, *Introduction to agent skills* |
| 2 | Connecting your tools | using a connection: everyone; adding one: engineers | about 1 hour | VS Code *MCP servers*; GitHub Learning Hub, *Understanding MCP servers*; Academy MCP course, first two lessons only |
| 3 | Agents | anyone who has used a skill on real work | about 1 hour core | Anthropic Academy, *Introduction to subagents*; Microsoft Learn, *Configure GitHub Copilot instructions and create custom agents*; GitHub Learning Hub, *Building custom agents* |
| later | Letting it run with less supervision | engineers | to be decided | Anthropic Academy, *Claude Code in action* (lessons 2, 5, 8, 9); GitHub Learning Hub, *Automating with hooks* |

**Why Skills is first:** the learners repeat the same jobs, so a saved way of doing one pays off
soonest.

**Why Connecting your tools is second:** where a ticketing connection exists, using it instead of
an export is worth more to operations staff than Agents. It also settles early whether the
ticketing and log systems can be reached from the assistant. Agents comes third and can then use
those connections.

## 1. Skills, in more depth

**Outcome, a week later:** a skill the learner wrote runs on their real work, and they have
corrected it at least once.

| Kind | Worked example |
|---|---|
| Operations staff | a weekly summary of a ticket export |
| Engineers | documenting an application from its code (scripts allowed) |
| Managers and analysts | a go or no-go review of a change, built on the existing recipe |

**Entry check (first five minutes):** the learner has a skill file and a house-rules file. If not,
they do the recipes Ask for a skill and Set house rules first (about 25 minutes), or open the
starter skill in `practice/skills/weekly-ticket-summary/`.

**Core path**

| Unit | The learner does | They check | Borrowed from | Copilot translation |
|---|---|---|---|---|
| A skill is a saved request | Open their skill and find the five parts of a request in it, plus the description that says when to use it | They can point to each part; any missing part is added | Academy L1 "What are skills?" | VS Code *Agent skills*: the description is read first, the instructions when the skill is used, extra files when needed |
| Make it fire when it should | Ask for the job without naming the skill; if it is not used, edit the description and ask again | The chat shows the skill was used | Academy L2 "Creating your first skill" | `/` lists skills; location `.github/skills/<name>/SKILL.md` or personal `~/.copilot/skills/` |
| Show it a good result | Have the assistant save an example of a good result as a second file the skill points to | Two runs on the same input match the example's shape | Academy L3 "Configuration and multi-file skills" | Same; scripts in a skill are for engineers only |
| Fix one that misbehaves | Repair one of three broken practice skills: one that does not fire, one that fires on the wrong job, one that gives different answers each run | The fault is gone on a rerun | Academy L6 "Troubleshooting skills" | The description causes the first two faults; loose instructions the third |
| This week | Name the real job the skill will run on, the day, and the check | Written in `my-requests.md` | Getting started, First real chore | — |

**Recipes:** Skill, house rules, or agent? (decision aid and worked cases; Academy L4 and VS Code
*Customization overview*). Share a skill, held until `[YOUR ORGANIZATION: the approved catalogue, review and how a skill is published]`
exists; the assistant does the repository steps, and the check is a teammate's run later, not in
the session (Academy L5).

**Build items:** three broken practice skills and a starter skill, in `practice/`; the decision
aid and worked cases.

**Evaluation question:** "Has a skill you wrote run on your real work since the session? Has
anyone else used it?"

Example libraries, subject to `[YOUR ORGANIZATION: whether outside skills may be used]`:
`github/awesome-copilot` and `anthropics/skills`.

## 2. Connecting your tools

**Outcome, a week later:** the learner has used an approved connection on real work instead of an
export, and can say what it can read and which data rule still applies.

Split by task, not by role:

- **Using an approved, installed connection: everyone.** Ask a question that needs it, see which
  tool it used, check the answer against the system. The data rule from Getting started (delete
  sensitive columns first) is no longer something the learner does to a file, so the check
  includes saying what the connection can read and what must not be asked for.
- **Adding or configuring one: engineers.** From VS Code *MCP servers*: add a server, see its tools
  in the chat, turn tools off.

Borrow only the ideas from the Academy MCP course's first two lessons (what a connection is, and
what the assistant's side does). The rest teaches building a connection in Python, which is out of
scope.

`[YOUR ORGANIZATION: which connections each group may use, how one is added, what each may read or change, and which data rules apply to it]`

**Evaluation question:** "Since the session, have you used a connection instead of an export?"

## 3. Agents

**Outcome, a week later:** the learner has handed a real piece of review or analysis to an agent
that can read but not change their files, and checked what it reported.

| Kind | Worked example |
|---|---|
| Operations staff | a ticket analyst that reads exports and reports patterns |
| Engineers | a reviewer that reads a change and reports risks |
| Managers and analysts | a document reviewer that reports what a plan or runbook leaves out |

**Core path**

| Unit | The learner does | They check | Borrowed from | Copilot translation |
|---|---|---|---|---|
| From Agent mode to an agent of your own | Start from the Agent mode they have used since Start here; compare it with a custom agent (a role with its own instructions and its own tools) and a subagent (an agent the assistant sends work to, which reports back) | They can say, for one of their jobs, which of the three it needs, and the reason matches a worked case | Academy subagents L1; Microsoft Learn units 2 and 4 | VS Code *Custom agents*: "What are custom agents?" |
| Make a read-only reviewer | Have the assistant create an agent that can read files but not change them | Ask it to edit a file; it refuses or asks first. Say no; the file is unchanged | Academy subagents L2; GitHub Learning Hub *Building custom agents* | `.github/agents/<name>.agent.md` with a `tools` list |
| Make it dependable | Give it a fixed layout for its report and a required section for what it could not do | Two runs have the same headings; the "could not do" section is filled in when it should be | Academy subagents L3 | Same |
| This week | Name the real review it will do, the day, and the check | Written in `my-requests.md` | Getting started, First real chore | — |

**Recipes:** When to use an agent, and when not (decision aid and worked cases; Academy subagents
L4). For engineers only: chain agents with handoffs (Microsoft Learn unit 5 and its exercise;
VS Code handoffs and the `agents` property), and check runs you did not watch (Academy *Claude
Code in action* L8). Agents that change files stay in the engineers' recipes, in line with
Getting started's rule not to allow commands without asking.

**Evaluation question:** "Since the session, have you had an agent of your own review or analyse
something real? Did you check its report?"

## Later: letting it run with less supervision

For engineers, once Skills and Agents have run. Candidate topics from *Claude Code in action*: house rules
the assistant actually follows (L2), hooks that enforce a rule every time (L5, and GitHub's
*Automating with hooks*), checking runs nobody watched (L8), and packaging a team's setup as a
plugin (L9). VS Code has each: custom instructions, hooks, agent plugins.

## Sources

- Anthropic Academy catalogue: https://academy.claude.com/courses
- *Introduction to agent skills*: https://academy.claude.com/courses/introduction-to-agent-skills
- *Introduction to subagents*: https://academy.claude.com/courses/introduction-to-subagents
- *Claude Code in action*: https://academy.claude.com/courses/claude-code-in-action
- *Introduction to Model Context Protocol*: https://academy.claude.com/courses/introduction-to-model-context-protocol
- Microsoft Learn, *Configure GitHub Copilot instructions and create custom agents*: https://learn.microsoft.com/en-us/training/modules/configure-customize-github-copilot-visual-studio-code/
- GitHub Copilot Learning Hub: https://awesome-copilot.github.com/learning-hub
- VS Code customization overview: https://code.visualstudio.com/docs/agent-customization/overview
- VS Code agent skills: https://code.visualstudio.com/docs/agent-customization/agent-skills
- VS Code custom agents: https://code.visualstudio.com/docs/agent-customization/custom-agents
- VS Code MCP servers: https://code.visualstudio.com/docs/agent-customization/mcp-servers
- Example library: https://github.com/github/awesome-copilot
