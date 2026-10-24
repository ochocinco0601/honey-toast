---
name: commanders-intent
description: Makes every skill or agent you write or revise state the bigger job it serves, and has a reviewer that did not write it check that before it is called done. Load it whenever creating, revising or reviewing a SKILL.md or an agent definition, by any means (skill-creator or a direct edit), and whenever the person asks whether a skill or agent understands what it is for.
---

# Commander's intent for skills and agents

## The job this serves

The person builds skills and agents so that their assistant does real parts of their work inside bigger jobs: a process, a deliverable, a team's practice. A skill or agent that knows only its own task acts like a contractor: it delivers its output and stops, without understanding the need behind it. One level up, this skill keeps every definition aimed at the job it is part of; two levels up, it means the person no longer has to carry that intent themselves and remind each session of it. It is the step in authoring and review that does this. It receives a skill or agent being written or revised, from whatever authoring tool is in use (often skill-creator), and hands the person a definition that carries its purpose, with the verdict of a reviewer who did not write it. Done is not a section with the right heading: it is a skill or agent that, used in the person's real work, does its part of the bigger job, and a reviewer has confirmed it after the last change.

The field's name for this is commander's intent: the purpose one and two levels up, stated so that whoever carries out the task can act well when the plan does not fit the case.

## When writing or revising

Work out five things:
1. **The job it serves:** the purpose one and two levels up.
2. **Its step in that job.**
3. **What it receives,** and from where.
4. **What it hands on,** and to whom.
5. **What done means for the whole job,** not just for its own output.

Take them from the person's own words where they exist: the conversation, notes they pointed to, the request. Where they do not, write your best reading, mark it inferred, and say which sources you drew it from; the review checks the inferred parts first.

Write them into the definition as a short section titled **The job this serves**, near the top. A thin entry point that only loads another skill or agent says so, and names where its job is stated. When revising, read the existing section first; if there is none, add it before changing anything else, and judge every change against it.

## Review: part of done, not after it

A reviewer that did not write the skill or agent checks it, in its own context: the `independent-discipline-reviewer` agent where it is installed, otherwise a fresh agent or session. Give it:
- the paths of the definition's files, and which version it is reviewing;
- this skill's path, as its lens;
- the job in the person's own words where they exist, and otherwise your inferred reading with its sources;
- where to write its report.

Ask it:
- Does "The job this serves" name all five things, and is each true to how the skill or agent will actually be used?
- Does the rest of the definition serve that job, or does it stop at its own output?
- For an agent: does what it hands back give its caller what the bigger job needs next?

Settle each finding: fix it, or record why it stands. A finding about what the person intends goes to the person. Then the same reviewer, or a new one given its earlier report, re-checks what changed. Repeat until a re-check finds nothing that needs fixing. The skill or agent is not done until that re-check has passed; tell the person its verdict when you hand it over.

## Gotchas

- The re-check after fixing the review's findings is easy to skip, because the work already feels finished. It is part of done.
- A heading with thin content under it passes a glance and fails the job. The review judges the content.
- The author's own reading of the job is the one most likely to be wrong; take the job from the person's words.
