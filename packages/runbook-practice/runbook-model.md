# Runbook model

**For:** whoever writes or reviews one runbook. **Job:** say what one runbook must let a first responder do, how it is laid out, and how to write it.

A runbook is **a decision procedure for one alert**: entered from the alert, opening with the expectation the alert guards, with an observable test at each branch and a determinable ending on every path. A runbook that says only "contact the dev team" is that procedure with one node and one leaf: the triage has been removed.

Where several alerts watch one slice of work, each alert still gets **its own short entry**, and its runbook link (Prometheus's `runbook_url`) points at that entry, not at the top of a shared page. What the alerts have in common is written **once, in one shared section** for the slice: the slice itself, what is at stake, every test, the causes the alerts share, and how to restore, close and escalate. An entry names the tests it runs and refers to them there; no test is copied from one alert's entry into another's. *[This practice]*

Splitting by alert alone does not make a walk reach its cause. Three rules carry that, and the entry holds them:
- **Bounded tests.** Each of the entry's tests is read on that alert's own cases and over that alert's own time window, so a test cannot match another alert's cases or a period outside the alert's. A count of cases waiting past a bound lags its cause by up to the bound, so its window opens when the oldest counted case entered, never only when the count began rising.
- **Contain first.** Before finding the cause, stop further harm to the cases the alert counts, or say why none is needed: a case that left with a wrong outcome is held where it is; more cases leaving by an unwanted move are stopped where a person makes that move.
- **A match explains the cases it lists.** The walk takes its ending for those cases and goes on for the rest, and a test the record ties to a cause tested for another alert says to run that test too.

## The endings

Every path ends in one of these. Each has a close, and each close records an outcome ([outcome record](outcome-record.md)).

| Ending | Close | Outcome and tag to record |
|---|---|---|
| **Nothing is wrong** | Close as no impact | *no action* · **no impact** (add **threshold or duration wrong** if the alert should not have fired) |
| **Expected condition**: a planned change, maintenance window or known batch behaviour | Link the change or window; close | *no action* · **no impact**; add **alert needs changing** if it should have been suppressed for the window |
| **Self-healed**: recovered before anyone acted | Confirm the expectation is met again; close | *no action* · **threshold or duration wrong** |
| **Degraded within tolerance** | Re-check after the runbook's time box: still within → close; worse → back to the tests. Not every alert has this ending: an SLO burn-rate page fires *because* the burn is not tolerable | *no action* · **threshold or duration wrong** |
| **Already known**: a duplicate of an open incident, or a known error with a fix in flight | Link it; close | *no action* · **only meaningful alongside other alerts** |
| **Broken — restore** | Restore, then confirm the expectation is met again | *action taken* · **same fix as before** or **new or different fix** |
| **Broken — cannot restore** | **Escalate** (below) | Completed by the tier that resolves it. The runbook mark is *worked*: escalation was the right ending |
| **Outside this runbook**: a condition the runbook does not cover, or a step that cannot be run as written | **Escalate**, with what you have | Completed by the tier that resolves it. Runbook mark: *gap* (not covered) or *failed* (a step could not be run) |

In coarse terms: the first five answer *does this need action? no*; the sixth answers *what restores service?*; the last two escalate. *[This practice; endings from the decision-tree form below]*

## Two different moves: escalate, and declare an incident

| | **Escalate** (functional escalation) | **Declare an incident** |
|---|---|---|
| What it is | Hand the problem to the owning tier because you cannot restore | Bring in incident coordination because the problem is bigger than one responder |
| What you do next | Stop, once the receiving tier **acknowledges** the handover. Until then you own it | **Keep working the runbook.** Restore continues in parallel |
| Triggers | Cannot restore with the steps here · outside this runbook · the fix needs approval (send to the change-approval path, not the owner's on-call) *[This practice]* | A second team is needed · customers can see the outage · unsolved after a time box of concentrated work (the Google SRE book's criteria for declaring an incident, *Managing Incidents*: "an hour's concentrated analysis") · impact crosses the threshold stated in S2 *[This practice]* |
| What crosses | The expectation, which tests ran and what they showed, what was done, the current state, when it started | The same, to whoever takes incident command |

Both are checked at every step, not only at the end, which is why every entry points to S8. The SRE book's advice is to declare early: "It is better to declare an incident early and then find a simple fix and close out the incident than to have to spin up the incident management framework hours into a burgeoning problem."

Past these two moves is **incident coordination** (severity, roles, communication, handoffs inside an incident). The runbook links to it and does not restate it.

## Anatomy, in reading order

Ordered for a responder under pressure: the alert's entry comes first, and its first screen says what fired, what to check first, how to stop further harm, and where the exits are. The shared section follows the entries.

**The alert's entry** (one per alert; E1 to E5 in this order):

| # | Part | What it holds | Required from state |
|---|---|---|---|
| E1 | **What fired** | What the alert detects, the expectation it guards, which cases it counts, the time window its tests are read over, and a pointer to S8's triggers | 1 |
| E2 | **Opening checks** | Already known, expected condition, then what changed in the alert's window (a change found leads to *roll back* in S6 or *escalate to the change owner*); then whether the count is falling | 2 |
| E3 | **Contain first** | The step that stops further harm to the cases the alert counts, or a statement that none is needed, and the actions not to take (S6) | 2 |
| E4 | **Its tests** | The alert's own tests, in order, each named by its number in S4: on the alert's own cases and over its window, each saying what a match means and which ending it leads to. Where the alert's cases are in several states, grouped by state, dependencies shared by the states first | 2 |
| E5 | **Restore, close, escalate** | Links into S6, S7 and S8 | 2 |

**The shared section** (one per slice):

| # | Section | What it holds | Required from state |
|---|---|---|---|
| S1 | **The slice on one page** | Its steps, who does each, what each relies on, and what is expected of the slice | 2 |
| S2 | **What is at stake** | Business and workflow impact, and the impact threshold for declaring an incident (or a link to the severity definition) | 2 |
| S3 | **Before you start** | Access and tools the steps need. A step the responder cannot run is a defect: record *failed* and add it to the access gaps | 2 |
| S4 | **Every test, once** | Each test written once: action, expected result if this is not the cause, the result that means it is, its ending, and which alerts' entries use it. Dependencies appear only where their state decides the ending | 2 |
| S5 | **Causes the alerts share** | The tests more than one alert uses, and the causes of one alert that the record ties to a cause tested for another | 2 |
| S6 | **Restore** | The remedy as action / expected result / what if different. Steps needing approval are marked. **What not to do** | 3 (state 4: the remedy runs on one click or approval) |
| S7 | **Close** | The close for each ending (table above) | 2 |
| S8 | **Escalate / declare** | Both moves' triggers; escalation **to whoever owns the failing part**, as the ownership record names it, or a stated gap where it names none; the change-approval path (**links** to the on-call, ownership and change records, never copied names); what to hand over; and a link to incident coordination | 1 |
| S9 | **Outside this runbook** | Escalate with what you have, record *gap* or *failed*, and go on with the cases still unexplained | 2 |
| S10 | **Links** | Dashboard views and queries the tests use | 2 |
| S11 | **About this runbook** | Owner, last validated (used or rehearsed), how to propose a change | 1 |

The states are defined in the [runbook standard](runbook-standard.md). A runbook needs every section required at its state and below. A runbook for one alert alone has one entry, and its shared section is the rest of the same page.

**Sources:**
- E1 follows the kube-prometheus runbooks, which open with "Meaning".
- S2 follows the O-BOK Playbook Factory's (IN-13) "context before procedure".
- S6's "what not to do" follows the kube-prometheus CPUThrottlingHigh runbook: "User shouldn't increase CPU limits unless the application is behaving erratically (another alert firing)."
- One entry per alert, pointed at by the alert's link, follows the Prometheus convention of a `runbook_url` annotation on each alerting rule.
- "What changed first" is common practice *[Unverified]*.

## How to write one

Established practice, composed *[This practice]*:

| # | Step | Discipline |
|---|---|---|
| 0 | **State the expectation** the alert guards. Every branch is a judgement against it | Google SRE (critical user journeys, SLOs) |
| 1 | **List the failure modes behind this alert's symptom**: what can go wrong, what each does to the outcome, how it would be detected. Scoped to this alert, or to the alerts that share the runbook, not the whole service | FMEA |
| 2 | **Map each failure mode to an observable test** that tells it apart | FMEA detection column |
| 3 | **Check the alert fires on a symptom**, not a cause. If two failure modes share a symptom, the discrimination goes inside the runbook, not into two alerts | Ewaschuk, *My Philosophy on Alerting* |
| 4 | **Break the response into steps**, with a plan saying which step comes next under which condition. The plans produce the branches; a stopping rule says how far to break a step down | Hierarchical task analysis (Annett & Duncan) |
| 5 | **Write it as a branched checklist**: one line per step, action / expected result / what if different. Every path ends | Aviation quick-reference checklist convention |
| 6 | **State the close for every ending**, including no impact and escalate | SRE verification; ITIL incident closure, which confirms the service is restored before closing (V3 wording) |
| 7 | **Rehearse it cold**: someone without system knowledge runs it unaided. An unrehearsed runbook is untested | SRE disaster role-play ("Wheel of Misfortune") and disaster-recovery testing (DiRT); aviation simulator validation |
| 8 | **Set the upkeep**: the resolver improves it at use, and each postmortem updates it | KCS (Consortium for Service Innovation); SRE postmortem practice |

Step 0 gates steps 6 and 7. Step 1 gates everything from step 2 on.

**Markers:** a claim with a source is cited inline. *[This practice]* marks this practice's own synthesis. *[Unverified]* marks a claim not checked against a source.
