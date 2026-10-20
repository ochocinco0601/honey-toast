---
name: runbook-basics
description: Start a team's runbooks for a system it has begun to support in production, organized the basic way (one folder per service, holding an overview, its procedures and a page per alert), then improve them with every use. Start writes a basic first version from what the team already holds (code and deployment config, past incidents, error logs, alert rules and queries, dashboards, developer notes, email and chat). Iterate takes something that just happened (an incident, a handled alert, a developer's answer, a postmortem, a step that failed) and updates the pages it teaches about. Use when a team needs its first runbooks, restart procedures or "the basics" for supporting a service, application or agentic function, or wants its runbooks updated from what was learned. Every procedural line is cited to its source; nothing is invented.
---

# Runbook basics: start, then iterate

A team that has just taken on a system in production cannot wait for complete runbooks. It needs a thin first version now, from what it already has, and a habit of improving the runbooks every time they are used. This skill does both:

- **Start** writes version 1 of the whole set.
- **Iterate** takes one new piece of evidence and updates the pages it teaches about.

Version 1 is meant to be basic. It gets better through use, not through a longer first pass. This is the Knowledge-Centered Service (KCS) practice: capture knowledge while doing the work, and improve it each time it is reused.

The system is usually distributed. Some services may be agentic functions (a model-driven step that decides or acts); they are one kind of service among applications, queues, data stores, jobs and external integrations.

## The organization

One folder for each service the team operates, the same three kinds of page in each, and one front page.

```
runbooks/<system>/
├── README.md                 front page: every service, its owner and on-call, its alerts
├── questions.md              open questions, each naming the page line it would fill
├── shared/
│   └── procedures.md         where to start with no alert (a user reported it), and checks that apply to many services
├── <service>/
│   ├── overview.md           what it does, who depends on it, what it needs, owner, dashboards
│   ├── procedures.md         checks and fixes written once: restart, roll back, what never to do
│   └── alerts/
│       └── <AlertName>.md    one per alert: what it means, is anyone affected, what to do, who to call
└── <service>/ ...
```

- An alert's link opens its alert page. The alert page links to its service's procedures and overview, and never copies them.
- A service another team or a vendor operates gets only an `overview.md`: who operates it, where its status is, what to hand them, and what this side does meanwhile.
- "Service" means anything the team would page about: an application, an agentic function, a queue, a data store, a job, a configuration store, an integration.

## The practice it follows

This skill follows the **runbook practice**: its `runbook-model.md` (what a runbook is) and `runbook-standard.md` (states 0 to 4). It ships in the same repository as this skill, in the folder `packages/runbook-practice/`. Find those files in the workspace and read them before writing. If they cannot be found, stop and tell the person: "This skill needs the runbook practice pages. Copy the folder `packages/runbook-practice/` from the repository this skill came from into this workspace, then ask again." In outputs, cite them by page name.

The model's parts are placed by what they do, whatever its section numbering. What one alert needs is on its alert page; what all of a service's alerts share is written once, on the service's pages.

| The model's part that says | Lives in |
|---|---|
| What fired · already known or expected · stop it getting worse · this alert's checks, on its own cases and window | `alerts/<AlertName>.md` |
| What the service does and who relies on it · what is at stake · escalate or declare, and to whom · dashboards and queries · who owns the runbook and when it was last used | `overview.md` |
| Access before you start · every check, written once · causes several alerts share · restore · how to close · what to do outside the runbook | `procedures.md` |

The standard's states are used as **a ladder each alert's runbook climbs**, scored on the alert page together with the service pages it links to. Pages show the plain name; the number is the standard's.

| Pages say "ready to" | Standard state | Moves up when it gains |
|---|---|---|
| **who to call** | 1 | What the standard lists for state 2 (it is the full list), chiefly: opening checks (already known? expected? a recent change?), a check of whether anyone is affected on the alert's own cases, a step that stops it getting worse, checks that tell its causes apart, a close for each ending, and what to do when a case is not covered; on the service's pages, what is at stake, access before you start, and the dashboards the checks use |
| **tell whether users are affected** | 2 | A fix a source supports and that is safe in this deployment |
| **fix it** | 3 | A rote fix set up to run on one approval |
| **fix it on one approval** | 4 | |

The standard is the authority; this table only says what the next rung needs. A page with no one to call says **"Call: not known yet"**, which the standard flags.

**Several answers lift every page at once.** Where open incidents and changes are recorded, and what each user step promises, are needed by every alert page to climb. Ask them once, at the top of `questions.md`, marked *fills every page*.

## Start

**0. Ask, then go on without waiting.** Ask the person:

- the system's name and what its users do with it, in plain steps
- **which deployment shape and environment it runs in**, because one codebase can deploy in shapes whose recovery is opposite (a data store that is disposable in one shape and holds real records in another)
- where the material lives

Search the workspace for the material yourself as well. A missing answer becomes a question in `questions.md`, not a stop.

**1. Services.** From code and deployment config, list the services and what each depends on. For each, record where it runs, who owns it, which user steps need it, and whether this team operates it; any of these may be *not known yet*.

**2. Alerts.** List every alert live in that deployment, from alert rules and saved queries, under the service it watches. Problems the team knows of that no alert catches (from incidents, error logs, notes and email) go in the README's *alerts we need*, with the symptom an alert would have to catch, in plain words.

**3. Write the pages,** service by service, starting with the services most likely to page:

- `overview.md`: everything the form asks, from the sources.
- `procedures.md`: each check once, with what each result means; each fix (restart, roll back, other responses); the *Never* list; the extras for its kind.
- One alert page per live alert, at the highest step its sources support. Step 1 is the floor for every alert. Each check on an alert page names the procedures check it runs, read on the alert's own cases and time window.

Leave each unknown as a visible *not known yet*, with its question in the page's *Not known yet* box, never filled with a plausible guess.

**4. Questions and README.** Gather every open question into `questions.md`: first the ones that fill every page, then the ones that would move the most alert pages up. Fill the README last.

**5. Review as the reader.** The pages are for people, so a draft is not done until it has been read as one. Take the two alert pages most likely to page, and the README.

- **If you can start a separate reviewer** (a subagent, a second session), give it only those pages and this instruction: *you are on call, this alert just fired; walk the page and say where you stopped, re-read or could not tell what to do.*
- **Otherwise** walk them yourself as that responder, line by line.

Then check every page against *How every page reads* in [templates.md](templates.md): checklists, not paragraphs; a cell is one short sentence; unknowns collected at the top; provenance out of the reading line. Fix what the reading found, across all pages, not only the ones read.

**6. Check, then hand back.** Before saying it is done:

- every procedural line has a marker whose source *contains* it, or is *not known yet* with its question in `questions.md`, or carries `†` with its question there
- no sourced step that is unsafe in this deployment appears as a fix
- every live alert has a page at step 1 or higher
- no service or alert page is longer than a screen (about 50 lines of markdown, not counting its sources); the README and `questions.md` may run longer, but the README's *If something is broken* table sits on its first screen
- no check or fix is written in two places
- every alert page's step matches what it and its service pages hold

Then tell the person:

- how many alert pages are at each step
- the few questions that would move the most pages up

## Iterate

**Input:** one piece of evidence. It can be:

- an incident or problem record
- an outcome record from a handled alert (runbook practice, *outcome record*)
- a developer's or owner's answer
- a postmortem
- a responder's note that a step failed or was missing
- a change to the system, or a deploy's pre-deploy and post-deploy check results
- an answer from a code-assistant tool about the code. It is a lead, not a confirmation: it can add a check or explain a cause, but a fix or a "safe to restart" drawn from it carries `†` until a developer or a test confirms it

**1. Read what the evidence teaches.** Name each lesson as one of these:

- a new check
- a new cause behind an alert
- a fix that worked
- a step that failed or could not be run
- an access or tool the responder lacked
- an owner or escalation path
- a sign that an alert itself is wrong (fires with no impact, or misses impact)

**2. Put each lesson on the page it belongs to.**

| Lesson | Page |
|---|---|
| A check, cause or fix that belongs to the service | `procedures.md` |
| Owners, dependencies or links | `overview.md` |
| How one alert's responder walks the checks | That alert's page |

Make each change with the evidence as its source, and leave every other line as it was. When the lesson settles an open question, fill the line, drop its `†` if it had one, and remove the question from `questions.md`. A lesson about an alert itself goes to the README's *alerts to change*, for the alert's owner, not into a runbook.

**3. Re-score and record.** Re-score every alert page the change reaches. Add a version line to each changed page: the date, what changed, the source, and any step change. Update the README.

**4. Keep pages to a screen, and readable.** If a page would pass a screen, move what belongs to the service out of the alert page and into procedures, and what belongs to many services into `shared/procedures.md`. Re-read each changed page against *How every page reads* in [templates.md](templates.md). An added line follows the page's checklist form, never a sentence appended to a cell.

## Rules

- **Never invent a procedural line.** A command, job name, flag, role, threshold, queue name or escalation target comes from a source that contains it and carries its marker, or it is *not known yet* with its question. A marker pointing at a source that only *implies* the line is invention. An action worked out from reading code (a switch the code reads, an endpoint it exposes) carries `†` and its question until the team confirms it.
- **Never pass on a sourced step that is unsafe here.** A documented command that destroys data or state in this deployment (a redeploy that wipes a data store, a restart that drops in-flight work) goes in the *Never* list with why, and never as a fix.
- **Platform documentation supplies generic commands only.** Cite the documentation page that contains the command, mark the line `†`, and ask in `questions.md` whether the team may run it on this service.
- **"The process is up" is never enough to close.** Close when the work is done again: a case moves through, a backlog drains, an outcome is correct.
- **Restart is one response among several.** The others: roll back, fail over, scale out, pause or switch off with a manual fallback, replay, escalate. Write the one the sources support. For an agentic function a restart rarely changes a wrong outcome; pausing it, falling back to the manual step, and rolling back its model, prompt or configuration version usually do.
- **Never resolve a disagreement between sources silently.** Prefer the record of what happened (an incident, the live config) over the record of what was intended (a design document, a README). Put the disagreement in `questions.md`.
- **Flag currency.** Material older than its service's last change in behavior is marked *possibly stale*. With no change history, *currency unknown*.
- **Link people, never copy them.** Owners and on-call link to their records. A name from email or chat never appears in an output.
- **Carry no sensitive content.** Cite incidents, logs and email by record id or file and line; never copy customer data or credentials.
- **Write for a person under pressure.** Follow *How every page reads* in [templates.md](templates.md): plain words, checklists, one short sentence per cell, unknowns collected at the top, provenance out of the reading line. The practice's terms appear only where a reader acts on them.
- **A defect found while writing is not a runbook problem.** If the code will produce a wrong outcome or lose data, put it in `questions.md` for the developers, in one sentence with its source.

## Gotchas

- **The only documented recovery may be destructive.** Check every sourced fix against the deployment the team runs.
- **Few or no live alerts** means few alert pages on day one. Problems then arrive as user reports, so the README's *If something is broken* table and `shared/procedures.md` (already known? anyone affected?) are the way in, and *alerts we need* says what to build first.
- **One codebase, several deployment shapes:** write procedures for the shape the team runs.
- **Agentic parts often have little written down about running them.** Their procedures will rest mostly on the team's own notes and questions until the first iterations.
