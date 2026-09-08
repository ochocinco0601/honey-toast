# Copilot Skills, Agents & Reference Packages

Reusable GitHub Copilot skills and agents for structured thinking, writing, and analysis, plus a set of reference packages on observability and engineering practice.

## Skills (`skills/`)

| Skill | What it does |
|-------|-------------|
| **arc42** | Turn raw, unstructured source material about a system into arc42-structured architecture documentation — twelve chapters, ISO/IEC/IEEE 42010 ordering (stakeholders, concerns, then views). Populates what the sources support and states the gaps plainly rather than filling them. Ships with a complete worked example. |
| **artifact-review** | Evaluate artifacts from expert perspectives using selectable review lenses (usability, clarity, stakeholder fit). |
| **briefing** | Produce stakeholder briefing products using intelligence, military, and business communication standards (BLUF, SOF, options lists). |
| **confluence-design** | Design or review a Confluence page for reader-task-fit — top-task prioritization, macro-as-format selection, page composition, answer-first ordering. |
| **dashboard-evaluation** | Evaluate a dashboard that already exists — panel by panel, with a stated reason per panel — or design a new one before any layout. Asks whether the surface answers the questions its reader actually has, whether each panel is drawn in the right form for its question, and whether the page can be read at all. Produces a keep / fix / remove record the owner can dispute line by line. |
| **design-for-operations** | Work out what a business process flow actually does, which code implements each part of it, and what could be watched — from source, with a file and line under every mechanical claim. Runs as a nine-phase skill over a bundled Semgrep-based extractor, or fits your own code-analysis tool and scores the fit with exit codes. Includes a worked example on a public reference application. |
| **doc-check** | Evaluate documentation against the Diataxis 4-type framework (tutorial, how-to, reference, explanation). |
| **editorial** | Editorial governance for human-facing content — tone/style, production standards, writing craft. |
| **html** | Produce interactive, self-contained HTML shaped for a specific job (understand, brief, present, orient, reference). Includes 20 worked examples. |
| **model-lookup** | Surface the conceptual models already built for a domain — the typed-slot structures (chains, stacks, sets, graphs) catalogued in a companion compendium — that fit the work in front of you, on the cue "what are the models for this?". Names the fit (one model, a composition, or none) instead of reinventing. Ships with the compendium it reads. |
| **prior-art-check** | Check whether something you built already exists as established practice — a named practice, a standard artifact, or a framework — or is genuinely novel. Judges by function rather than by name, and reconciles what it finds against your own record of adopted practice. Ships with the definition it judges against. |
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
| **apparatus-auditor** | Audit whether something has the operating apparatus it needs to actually work — what guarantees it gets written, what guarantees it gets read — or whether it is a prop that will die in a drawer. Reads your operating model as the yardstick, and grades against your real scale rather than a borrowed one. |
| **independent-discipline-reviewer** | Cold, fresh-eyes review of an artifact against one or more named discipline skills, run in its own context. It holds only independence — it loads the disciplines you name as review lenses, and writes a findings report rather than editing the artifact. |
| **prior-art-checker** | A deliberately blind evaluator. It receives only a functional description — never the artifact, its name, or what you think it matches — and names the established practice with the same function, with an honest account of what does not fit. "No match" is a valid, valuable answer. The blindness is the point: an evaluator told what you believe can only agree with you. |

## Reference packages (`packages/`)

| Package | What it is |
|---------|-----------|
| **observability-practice** | An observability Body of Knowledge (13 knowledge areas, 24 instruments, domain perspectives), plus a practice system, the SUD v2 instrument, a walk-before-run kit — a focused nine-page rendering for a team's first business process — and a one-page rendering of the model itself: its terms, how they connect, and where the methodology stops and implementation begins. |
| **observability-capability-gap.md** | A worked articulation of a platform capability gap against an observability standard — why dependency, producer, and internal errors fall outside a common APM metric model, and what that costs. |
| **meeting-delegate** | A package for the meeting-delegate practice (start-here, the practice, acceptance test). |
| **portfolio-coverage-operating-perspective.md** | An operating perspective for reasoning about observability coverage across a service portfolio. |
| **ai-credit-cap-justification.md** | Argument architecture for justifying an AI-assistant credit-cap increase — the answer-with-context method, per-question structure, candidate framings, and cautions. |
| **design-for-operations.md** | A repeatable method for taking a business capability from architecture to observability — eight passes from surface discovery to signal placement and ownership, each producing an artefact and ending at a checkpoint. |
| **design-for-operations-operating-perspective.md** | The same method in activation form, written for an assistant that already holds the field rather than for a reader learning it — seven passes with the practice each activates, what each of the three views may not claim, the four concerns as competency questions, what code cannot yield, and where established practice runs out. A working draft under active development. |
| **platform-capability-assessment-operating-perspective.md** | An operating perspective for the situation where a platform reports that a capability exists and the consuming team's need is still unmet — decomposing a capability claim into presence, coverage, and depth, naming the scope state it holds, and shaping a request that asks for published scope rather than a one-off exception. |
| **situation-to-form-operating-perspective.md** | An operating perspective for the whole path a rough request travels before it becomes something an organization holds — six decisions (capture the situation, name it against canon, record the route, set the weight, split the roles, become a real form), each with the established practice behind it. The frame of a two-part set; `practice-routing-operating-perspective.md` is its second link at working depth. |
| **practice-routing-operating-perspective.md** | An operating perspective for routing a problem stated in ordinary words to the established practice that addresses it — or refusing and naming the discipline that owns it. Covers the split between what is known about situations of a kind and what is true in one place, the index form with its does-not-answer veto, the fit test, and the two failure modes. |

## Install

Copy a skill folder into your environment's skills directory:

```
your-repo/.github/skills/<skill-name>/SKILL.md
```

Some skills include extra files — a `references/` subfolder, or a companion document. Copy the whole folder.

Agents go in the agents directory:

```
your-repo/.github/agents/<agent-name>.md
```
