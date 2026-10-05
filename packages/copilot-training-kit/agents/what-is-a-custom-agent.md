# What is a custom agent?

A custom agent is Copilot set up for one kind of work, such as reviewing documents or planning a
change. It has its own instructions, the tools it may use and, if you choose, the AI model it uses.
In this unit, you learn what a custom agent is and when to use one. There's nothing to do in VS Code yet.

## Why use a custom agent

When you do the same kind of work often, you select a custom agent instead of repeating its
instructions in every request. For example, a reviewer can hold your review checklist, and a
planner can say how you want a plan laid out.

Copilot does its work with tools. A tool is one action it can take, such as reading a file,
changing a file or running a command. A custom agent can also take tools away. A request, custom instructions or a skill can only ask Copilot not to change a file. With any of them, Copilot still has every tool, including the one that changes files.

For example, say you want Copilot to check your procedures for unclear steps, and to leave each procedure exactly as written. A custom agent that has only the tools for reading files can list the problems. It can't change a procedure, even if a request asks it to. Afterward, you don't have to check that each procedure is unchanged.

## What a custom agent looks like

A custom agent is a Markdown file whose name ends in `.agent.md`. You don't type one yourself: when you ask, Copilot writes the whole file.
This one, `procedure-reviewer.agent.md`, checks procedures:

```
---
name: Procedure reviewer
description: Check a procedure for unclear or missing steps, without changing it.
tools: ['read', 'search']
---

Read the procedure I name.
List each step that is unclear or missing, and say why.
```

The lines between the two `---` marks are the header: the agent's name, a description of what it
does, and the tools it may use. `read` and `search` let it read and search the files in the
folder you have open. `edit`, the tool that changes files, isn't in the list. After the header come the agent's instructions.

## Where a custom agent works

A custom agent saved in a folder works only while that folder is open in VS Code. Anyone who opens that folder can use it. A custom agent saved in your personal agents folder works in every folder you open, but only for you. When you have Copilot create a custom agent, you tell it which of these two places to save it in.

## How you select a custom agent

At the bottom of the chat box, the control that shows **Agent** opens a list of agents. In a narrow chat, that
control may show only an icon. **Agent**, the one you've
used so far, can change files and run commands. The list may show other agents too. You can leave them alone. A custom agent
you create is added to the list. When you select a custom agent, the control shows its name. As
long as it does, Copilot follows that agent's instructions and uses only its tools. To go back to **Agent**, select that control, and then select **Agent**.

## Custom instructions, a skill or a custom agent?

| To have Copilot | Use | Copilot uses it |
|---|---|---|
| Follow the same rules in every request in a folder | Custom instructions | With every request while the folder is open |
| Do a task you repeat the same way each time | A skill | When a request matches the skill's description |
| Work in one role, such as reviewer, with its own instructions and only the tools it needs | A custom agent | When you select it in the chat box |

For something you need only once, use none of them: say it in the request.

Which would you use for each of these? Decide, and then select **Show the answer**.

a. Everything Copilot writes in a folder should spell out abbreviations.

b. Each week, you ask Copilot to check the new procedures against a style guide and fix their wording to match.

c. Each new procedure needs checking for missing steps. It must stay unchanged while it's checked, even if a request asks Copilot to fix it.

d. One procedure needs checking for missing steps, just this once.

Check your answer: For a, custom instructions: a rule for every request in the folder. For b, a
skill: a task you ask for again and again. The task is meant to change the files, so there's nothing Copilot must be kept from doing. Custom instructions would apply the style guide to every request, not only to this task. For c, a custom agent: a reviewer whose tools only read. While it's selected,
Copilot can't use the tool that changes files, so each procedure stays as written. For d, none of them:
say it in the request. The likeliest mistake is choosing a skill for c. The Skills training gave "the same
checks on every new document" as an example of a task for a skill. A skill is right when there's nothing Copilot must be kept from doing. Here each procedure must stay unchanged, and a skill's instructions can only ask Copilot not to change it.

## What you learned

A custom agent is Copilot set up for one role: a `.agent.md` file with a header that gives its
name, a description and the tools it may use, then its instructions. You select it in the chat
box. Use one for a role you work in often, such as reviewer, especially when Copilot must be kept from doing something, such as changing a file.

Source: [Custom agents in VS Code](https://code.visualstudio.com/docs/agent-customization/custom-agents) and [Understand agent customization](https://code.visualstudio.com/docs/agents/concepts/customization), Microsoft.
