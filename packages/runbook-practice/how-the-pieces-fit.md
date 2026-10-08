# How alerts, dashboards, runbooks and the rest fit together

**For:** anyone learning the practice, and anyone deciding where a piece of operational content belongs. **Job:** explain what these artifacts are jointly for, and what each one contributes.

## What they are for

A service makes a promise to the people who rely on it (the O-BOK calls it an *expectation*): a payment goes through, a loan funds by the deadline, a page loads. Operational artifacts exist to **keep that promise true, and when it breaks, to shorten how long the impact lasts and stop it happening again.** ITIL 4 states the middle part as incident management's purpose, "to minimize the negative impact of incidents by restoring normal service operation as quickly as possible", and puts stopping recurrence in problem management.

The O-BOK's semantic chain (its methodology page) starts at the promise: *a stakeholder has an expectation, measured by a business health signal; if the expectation is breached → business impact signal → alert → owner + next action* (abridged). This page explains the part after the alert.

## Each artifact serves one moment

| Moment | Artifact | Its job | Where it is covered |
|---|---|---|---|
| Define healthy | **Expectation and signals** (SLOs where they exist) | Say what "working" means for users and the business, and measure it | O-BOK KA01, KA02 |
| Notice | **Alert** | Interrupt a person when the expectation is broken or about to be. Page on symptoms of impact; keep causes for looking | Google SRE book, *Monitoring Distributed Systems*; Ewaschuk; O-BOK IN-12 for gating mechanism-layer alerts |
| Look | **Dashboard** | Show the state: how bad, where, since when. Cause-level detail lives here, not in pages | Google SRE book, *Monitoring Distributed Systems*; O-BOK KA04 |
| Decide and restore | **Runbook** | Take the responder from this alert to an ending: no action needed, restored, or escalated with the triage attached | [runbook model](runbook-model.md) |
| Get the right people | **Escalation path and on-call** | Who owns it when the first responder cannot finish | The on-call and ownership records; the runbook links to them |
| Coordinate when it is big | **Incident coordination** and **playbooks** | Severity, roles, communication, handoffs across teams | Google SRE book, *Managing Incidents*; O-BOK KA05 |
| Learn | **Postmortem and problem record** | Find and fix the cause, then update the signals, alerts, dashboards and runbooks that let it happen | Google SRE book, *Postmortem Culture*; ITIL problem management; O-BOK KA05 |
| Keep it working | **Estate review** | Find which alerts are noise and which runbooks are weak, and fix the worst first | [estate review](estate-review.md) |

*[This practice]* The table is a synthesis: each row's practice is established, and no single source draws all of them together.

## How they connect

- **An alert links to one runbook.** The responder never searches.
- **A runbook links to the dashboard views its tests use.** The dashboard is where the responder looks; the runbook says what to look for and what each result means.
- **A runbook links onward** to the escalation path and to incident coordination. It says *when* to escalate or declare, and *what to hand over*, and stops there.
- **Every acknowledged firing leaves an outcome record**, and every incident records what first detected it. Those two records are how the estate review tells noise from need, and missed incidents from caught ones.
- **Learning flows back up the chain.** A postmortem or a run of outcome records changes an alert (tune, re-point, retire), a runbook (add a test, a restore, a caution), a dashboard view, or the expectation itself.

## The two failure shapes this explains

- **A runbook that says "contact the dev team".** The *decide and restore* moment is missing, so every alert collapses into act-or-pass-it-on ([runbook model](runbook-model.md)).
- **An alert nobody acts on.** The *notice* moment is firing on a cause, not a symptom, or the alert is right but nothing records that it needed no action, so nobody fixes it. The first is alert design; the second is the outcome record and the estate review.

Sources: Google SRE book chapters at https://sre.google/sre-book/ (*Monitoring Distributed Systems*, *Managing Incidents*, *Postmortem Culture*) · ITIL 4 incident management (see [README](README.md) sources) · Ewaschuk, *My Philosophy on Alerting*.
