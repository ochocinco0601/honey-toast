# Copilot Skills, Agents & Reference Packages

Reusable GitHub Copilot skills and agents for structured thinking, writing, and analysis, plus a set of reference packages on observability practice.

## Skills (`skills/`)

| Skill | What it does |
|-------|-------------|
| **artifact-review** | Evaluate artifacts from expert perspectives using selectable review lenses (usability, clarity, stakeholder fit). |
| **briefing** | Produce stakeholder briefing products using intelligence, military, and business communication standards (BLUF, SOF, options lists). |
| **confluence-design** | Design or review a Confluence page for reader-task-fit — top-task prioritization, macro-as-format selection, page composition, answer-first ordering. |
| **doc-check** | Evaluate documentation against the Diataxis 4-type framework (tutorial, how-to, reference, explanation). |
| **editorial** | Editorial governance for human-facing content — tone/style, production standards, writing craft. |
| **html** | Produce interactive, self-contained HTML shaped for a specific job (understand, brief, present, orient, reference). Includes 20 worked examples. |
| **information-surface-design** | Design or evaluate any information surface so it collapses need → uncertainty → decision. Includes a worked observability-panel instance. |
| **prune-instructions** | Restructure an overgrown instructions file via the residency-test method (GATE / FACT / CONDUCT). |
| **requirements** | Elicit and structure requirements before work begins — functional requirements, quality attributes, stakeholder analysis, failure definition. |
| **right-thing-right-way** | Two-altitude diagnostic: am I solving the right problem? am I solving it the right way? |
| **skill-creator** | Create, modify, and evaluate Copilot skills. |
| **systems-analysis** | Structured systems analysis — data flows, failure modes, leverage points, architecture (C4 + arc42). |
| **value-analysis** | Structured value reasoning — value for whom, at what altitude, under what constraints. |
| **visual-usability** | Judge the rendered visual of a page or document — hierarchy, density, cognitive load, scannability, the 5-second first impression. Requires seeing the render. |

## Agents (`agents/`)

| Agent | What it does |
|-------|-------------|
| **independent-discipline-reviewer** | Cold, fresh-eyes review of an artifact against one or more named discipline skills, run in its own context. It holds only independence — it loads the disciplines you name as review lenses, and writes a findings report rather than editing the artifact. |

## Reference packages (`packages/`)

| Package | What it is |
|---------|-----------|
| **observability-practice** | An observability Body of Knowledge (13 knowledge areas, 23 instruments, domain perspectives), plus a practice system and the SUD v2 instrument. |
| **observability-capability-gap.md** | A worked articulation of a platform capability gap against an observability standard — why dependency, producer, and internal errors fall outside a common APM metric model, and what that costs. |
| **meeting-delegate** | A package for the meeting-delegate practice (start-here, the practice, acceptance test). |
| **portfolio-coverage-operating-perspective.md** | An operating perspective for reasoning about observability coverage across a service portfolio. |

## Install

Copy a skill folder into your environment's skills directory:

```
your-repo/.github/skills/<skill-name>/SKILL.md
```

Some skills include a `references/` subfolder — copy that too.

Agents go in the agents directory:

```
your-repo/.github/agents/<agent-name>.md
```
