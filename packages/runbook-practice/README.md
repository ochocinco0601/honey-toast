# Runbook practice

How to write runbooks, and how to manage them across a large estate of production alerts where the runbook behind each alert ranges from escalate-only ("contact the dev team") to a full restore path.

Split by who uses each piece:

| Piece | Who uses it | Kind of document | What it answers |
|---|---|---|---|
| [How the pieces fit](how-the-pieces-fit.md) | Anyone learning the practice; read it first | Explanation | What do alerts, dashboards, runbooks, escalation and postmortems jointly do, and which moment does each serve? |
| [Runbook model](runbook-model.md) | Whoever writes or reviews one runbook | Procedure | What must one runbook let a responder do, how is it laid out, how is it written? |
| [Outcome record](outcome-record.md) | On-call responder | Procedure | What do I record when I close an alert? |
| [Runbook standard](runbook-standard.md) | Team leads, readiness reviewers | Standard | How good must a service's runbooks be, and how is that scored? |
| [Estate review](estate-review.md) | Operations or SRE lead | Procedure, reported to leadership | Which alerts and runbooks do we improve first, how, and how do we know it is working? |

## Scope

**In scope:** one alert and the first responder's response to it (what the alert is for, whether it needs action, what restores service, when that responder's part ends), the runbooks that make that repeatable, and the estate of them. In ITIL terms, the first-line part of incident management: diagnosis, workaround, and escalation to a specialist group ("functional escalation" in ITIL V3 wording).

**Out of scope, pointed to:**
- **Incident coordination**, which starts once an incident is declared: severity scales, incident roles, stakeholder communication, the live incident document, handoffs inside an incident. See the Google SRE book, *Managing Incidents*, and O-BOK KA05. A runbook links to it at its *declare an incident* move.
- **Alert design** (alert on symptoms of impact, not causes): Google SRE book, *Monitoring Distributed Systems*; Ewaschuk, *My Philosophy on Alerting*; and, for gating mechanism-layer alerts, O-BOK IN-12 Alert Factory. The estate review decides *that* an alert changes; it does not restate how to design one.

## Vocabulary

The field does not agree on the words.
- **Google SRE book:** calls the per-alert instructions a "playbook".
- **Common operations usage:** calls them a "runbook", and keeps "playbook" for a coordinated response across teams *[Unverified]*.
- **ITIL:** defines workarounds and known errors; first-line support works from a knowledge base.
- **O-BOK:** mixed. "Playbook" in KA05 and IN-13, "runbook URL" in IN-08 and KA03.

**Here:** a *runbook* is what to do when one alert fires on one service. A *playbook* is a coordinated response across teams. *Impact* is used for effect on users or the business. *Expectation* is the O-BOK's term for what a stakeholder (a user, a business unit, a regulator) expects of a service.

**O-BOK references:** knowledge areas (KA) and instruments (IN) cited by number are in the Observability Body of Knowledge, published as the observability-practice package.

**Markers:** a claim with a source is cited inline. *[This practice]* marks this practice's own synthesis. *[Assumption]* marks an unverified belief. *[Unverified]* marks a claim not checked against a source.

## Status

Draft, expected to change. Claims are cited to their sources or marked (see Markers above). Not yet tested against an operating estate's own alert data.

## Sources

- Google SRE Book, *Introduction*: https://sre.google/sre-book/introduction/
- Google SRE Book, *Monitoring Distributed Systems*: https://sre.google/sre-book/monitoring-distributed-systems/
- Google SRE Book, *Eliminating Toil*: https://sre.google/sre-book/eliminating-toil/
- Google SRE Book, *Being On-Call*: https://sre.google/sre-book/being-on-call/
- Google SRE Book, *Managing Incidents*: https://sre.google/sre-book/managing-incidents/
- Google SRE Book, *Postmortem Culture*: https://sre.google/sre-book/postmortem-culture/
- Google SRE Book, *The Evolution of Automation at Google*: https://sre.google/sre-book/automation-at-google/
- Google SRE Workbook, *Alerting on SLOs*: https://sre.google/workbook/alerting-on-slos/
- Rob Ewaschuk, *My Philosophy on Alerting*: https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/
- Etsy, Opsweekly: https://github.com/etsy/opsweekly
- ITIL 4, *Create, Deliver and Support*, incident management: https://www.oreilly.com/library/view/itil-4-create/9781787783393/xhtml/Chap14.html
- ITIL problem management (secondary, V3-era): https://wiki.en.it-processmaps.com/index.php/Problem_Management
