# IN-24 — First-Process Run Plan

<table style="border: 1px solid var(--md-typeset-table-color, #ddd); border-left: 4px solid var(--md-primary-fg-color, #673ab7); border-collapse: collapse; margin: 1em 0; font-size: 0.95em;">
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Type</th>
    <td style="padding: 0.4em 0.9em;">Adoption</td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">State</th>
    <td style="padding: 0.4em 0.9em;"><a href="index.html#content-state-key">Seeded</a></td>
  </tr>
  <tr>
    <th style="text-align: left; padding: 0.4em 0.9em; white-space: nowrap; font-weight: 600;">Lifecycle position</th>
    <td style="padding: 0.4em 0.9em;">Define</td>
  </tr>
</table>

---

## Purpose

A team adopting the practice needs more than the methodology (why) and the instruments (with what) — it needs the run plan: what to do first, who to put in the room, how the first working session runs, and what happens after. This instrument is that plan. It sequences the five-step walk, the discovery-dialogue conversation order ([IN-19](in-19-discovery-dialogue-protocol.md)), the capture templates ([IN-04](in-04-service-profile-template.md), [IN-05](in-05-signal-definition-template.md), [IN-06](in-06-stakeholder-expectation-template.md)), and the worked example into one executable path for a team's first business process.

The plan works with a spreadsheet and a wiki page. Tooling accelerates two steps and is noted where it applies; no step depends on it.

## The plan

### Before the first session

**Pick one business process.** Good first pick: one the business notices when it fails, and one the team knows well.

**Identify the people (three roles, however the org names them):**

- The person who knows what the process owes and to whom — product owner, business analyst, or the ops lead who fields the complaints.
- The engineer(s) who know the applications inside the process.
- The person who owns today's monitoring for those applications.

**Build the process inventory.** One table: the process → every application that participates, in order → where each runs. Pull from architecture docs and runbooks if they exist; write it from the engineers' heads if they don't. Most teams discover this table exists nowhere. Producing it is the first real output, not prep overhead.

**Generate the code-level picture (tool-accelerated).** Run DeepWiki against the repositories of the applications in the inventory — it produces flow diagrams and service descriptions from source. Then put it in front of the engineers and have them correct it. The documented flow must match the real one before anything is measured against it. If the tooling isn't available yet, a hand-drawn flow the engineers agree on serves for process one.

**Read the [worked example profile](worked-example-ledger-writer.md)** — it shows what done looks like; the room compares its own output against it after the session.

**Running it alone first (no room yet):** draft the stakeholder chains yourself from documents and your own knowledge, in the same order the session below uses — and mark every expectation and signal NEEDS VALIDATION. A solo pass produces a draft, not a finished profile. The working session then runs as confirm-and-correct with the people who can validate each chain — faster than starting blank, and nothing self-answered slips through as settled.

### The first working session (~90 minutes, facilitated)

One person facilitates and asks; the room answers. The order below is the [IN-19](in-19-discovery-dialogue-protocol.md) motivation-chain order — it follows how the business people actually reason, and it builds traceability as it goes instead of reconnecting things afterward.

**1. Context (10 min).** What is this process, what does it participate in, who depends on it. Confirm the inventory table in the room.

**2. Stakeholder chains — the core of the session (50 min).** One stakeholder at a time, complete before moving on:

- Who are they? (a named role: the operations team, the downstream reconciliation group, the customer)
- What do they expect of this process — as a measurable sentence? ("Files arrive by 6am." "A transaction completes end to end in 10 seconds." "The day's volume matches the source system.")
- For each expectation: what signal would tell us it's met or missed? That signal is a business health signal. Name it, even if nothing measures it today.
- **Close the chain before the next stakeholder:** does every expectation named have a signal named? Gaps stay on the page as gaps.

**3. Impact (10 min).** When those expectations are missed, what does it cost — money, customers, regulatory exposure, downstream teams blocked? Attach the cost to the expectation it belongs to.

**4. Technical signals (15 min).** Only now, engineers: for each business health signal, which application-level signals would explain a breach (the workflow errors, the queue depth, the latency between A and B)? Which system-level signals sit under those? Existing monitors slot in here — this is where years of bottom-up monitoring get connected upward instead of thrown away.

**5. Close (5 min).** Read back the open questions — everything the room couldn't answer — each with an owner and a date.

**The session's output is a filled service profile:** stakeholders → expectations → business signals → supporting application and system signals, plus the impact notes and the gap list. The [worked example profile](worked-example-ledger-writer.md) shows what done looks like — review it with the room before and after their own session. The structured question set (tool-accelerated) can walk a facilitator through this whole session; it works best live in the room, not sent around as a form.

### After the session

**Set measurements and targets.** For each signal: which source answers it — logs, APM (application performance monitoring), synthetics — and what the target is. Where no agreement was ever documented, derive the starting range from existing telemetry: what has normal looked like for this signal over the last months? Set that as the range, alert on deviation, and replace it with a documented agreement when one exists.

**Wire the response.** Every signal that can breach gets an owner and a next action. From here it's the reliability practice the team already runs — alerting, triage, review — now anchored to the process map instead of tribal memory.

**Let the profile drive the artifacts.** The filled profile is the source the generation factories ([IN-11](in-11-dashboard-factory.md), [IN-12](in-12-alert-factory.md), [IN-13](in-13-playbook-factory.md)) consume to produce dashboard panels, alert definitions, and playbook skeletons. The team maintains the profile; the artifacts regenerate from it. Until that machinery is in place locally: the profile lives on a wiki page, the dashboard is built once by hand from it, and the page maps question → signal → tool.

### Process two and three

Repeat the plan on the next process with less facilitation — the people who sat in session one can now run their own. Log friction as it happens ([IN-18](in-18-friction-logging-protocol.md): what confused the room, what blocked progress, 30 seconds per entry) and fix the next run from the log. A signal that traces to no expectation is a cleanup candidate, not a keeper — the same test prunes the legacy monitor pile as processes get walked.

## Inputs

- One selected business process (selection criteria above)
- The three roles in the room (business knowledge, application knowledge, monitoring ownership)
- Existing documentation if any (architecture docs, runbooks) — absence is workable
- The capture templates [IN-04](in-04-service-profile-template.md) / [IN-05](in-05-signal-definition-template.md) / [IN-06](in-06-stakeholder-expectation-template.md) — the field structure the session's output fills
- The [worked example profile](worked-example-ledger-writer.md) — the completed output of a first run, for calibration

## Outputs

- Process inventory table (process → applications → hosting)
- Corrected code-level flow picture
- Filled service profile (stakeholder chains, signals across layers, impact, gaps)
- Measurement targets and response wiring per signal
- Open-questions list with owners
- Friction log feeding the next run

## KA Cross-References

| KA | Relationship |
|----|-------------|
| [KA12 — Adoption & Enablement](../ka12-adoption-enablement.md) | This instrument is the executable form of [KA12.1](../ka12-adoption-enablement.md#onboarding-first-experience) first experience — the path a receiving team actually walks |
| [KA01 — Business Context](../ka01-business-context.md) | The session captures [KA01](../ka01-business-context.md) knowledge — stakeholder expectations, business processes, impact |

## Usage Context

**When to reach for this instrument:**

- A receiving team (new division, new line of business, peer champion's team) asks "how do we actually start?" — this plan is the answer, ahead of methodology reading
- Assembling a transfer package ([IN-17](in-17-transfer-packages.md)) — this plan is the on-ramp component that binds reference material, instruments, and the worked example into an executable sequence
- A pilot ([KA12.3](../ka12-adoption-enablement.md#pilot-design-execution)) needs a defined walkthrough to measure friction against

**Related instruments:**

- [IN-19 Discovery Dialogue Protocol](in-19-discovery-dialogue-protocol.md) — the conversation order inside the first working session
- [IN-16 Onboarding Simulation](in-16-onboarding-simulation.md) — the guided-walkthrough form of the same first experience, with AI-assisted observation
- [IN-17 Transfer Packages](in-17-transfer-packages.md) — the package this plan fronts
- [IN-04](in-04-service-profile-template.md) / [IN-05](in-05-signal-definition-template.md) / [IN-06](in-06-stakeholder-expectation-template.md) — the templates the session fills
- [IN-11](in-11-dashboard-factory.md) / [IN-12](in-12-alert-factory.md) / [IN-13](in-13-playbook-factory.md) — the factories the filled profile feeds
