# Estate review

**For:** the operations or SRE lead who owns an alert estate. **Job:** decide which alerts and runbooks to improve first and how, and show whether it is working, without rewriting runbooks one by one.

The loop combines established parts: Opsweekly classification, Pareto ranking, SRE alert review, ITIL problem management. *[This practice]*

## Before you start

**Inputs:**
- the [outcome record](outcome-record.md) on each acknowledged firing
- runbook states from the [runbook standard](runbook-standard.md)
- what the alerting and incident tools already hold: firing counts after deduplication, unanswered firings, time to acknowledge, firings per shift and out of hours

**Prerequisite:** each incident record states **what first detected it**: an alert on the affected service, an alert elsewhere, a person, or a customer. Coverage and the missed-incident review depend on it. If the incident tool has no such field, adding it comes first.

**Parameters the adopter sets:**
- criticality tiers, their weights, and which count as critical
- the busyness measure (firing count or total time firing) and its period
- the minimum number of records before an alert is routed
- the minimum runbook state for critical services ([runbook standard](runbook-standard.md))
- the validation window
- the review cadence
- the recall check's lookback and acceptable added delay

**Fit questions:**
- Where is the per-firing outcome recorded in the alert or incident tool?
- Who owns and approves a change to an alert definition?
- Where is the service criticality tier recorded?

## The loop

0. **Score the starting state.** Score the runbooks of paging alerts on critical services against the runbook standard. This needs people, and it is bounded by the number of critical-service alerts, not the whole estate. Outcome recording (step 2) starts at the same time.
1. **Build two lists.**
   - **Noisiest alerts**, from tool data: busyness × service criticality.
   - **Critical gaps**, from step 0: alerts on critical services below the minimum runbook state, however rarely they fire, ordered by criticality and then lowest state first. This finds the alert that fires once, during a real outage, with nobody familiar with it.
2. **Record outcomes** on every acknowledged firing ([outcome record](outcome-record.md)).
3. **Work from the top of both lists.**
   - **Noisy alerts** are routed in review (below) once they have the minimum number of records. Alerts that are mostly unanswered can be routed from tool data at once.
   - **Critical gaps** have little firing history, so they are raised to the minimum state with the building team's knowledge, using the [runbook model](runbook-model.md)'s writing steps, including the rehearsal.
   - **On both lists:** route by outcome where there is history. If the route is *retire*, retire it; otherwise the minimum state still applies.
4. **Change and record.** Make the change, and record the runbook state on the alert and the validation date on the runbook section. Retired alerts leave the scale. New alerts enter at the state they were created with.
   - **A change to the alert** restarts its outcome records from the change date.
   - **A change to the runbook only** keeps them, because how often the alert fires has not changed.
   - **Single incidents don't wait for a pattern.** When an incident review finds a fix the runbook lacked, the runbook is updated then, as one of the review's actions. *[This practice]*
5. **Review on a fixed cycle:**
   - the top of both lists
   - every missed incident: each ends in an alert change on the affected service, or a recorded reason why not
   - stale runbook sections ([runbook standard](runbook-standard.md)) and coverage gaps (runbook mark *gap*)

   Then back to step 1. The noisiest list is rebuilt over the latest period, excluding alerts changed within it and alerts marked *held*. The critical-gap list is rebuilt from the recorded states.

## Routing

*[This practice]* Routing is a review decision, not a formula. The reviewer looks at an alert's records since it last changed, and picks the row that fits most of them. If two rows fit and both can be done, do both; if not, do the less drastic one. The decision and its reason are recorded on the alert.

| What most of the records say | Change | Runbook target (never lowers a state, except retire) |
|---|---|---|
| **no impact** | Retire: remove or demote the page, or replace it with a symptom alert | Retired |
| **threshold or duration wrong**, or mostly unanswered | Tune: change the threshold, or add a hold duration longer than its typical time to clear. Still mostly noise after tuning → the next review retires it | Unchanged |
| **only meaningful alongside other alerts** | Make it conditional: fire only alongside another alert or a degraded business-health signal (inhibition or correlation; O-BOK IN-12: "suppress or downgrade a mechanism-layer alert when Business Health is green"). A conditional page still pages, so it keeps its state | Unchanged |
| **alert needs changing** | Change the alert definition per the notes, including making it fire earlier | Unchanged |
| **same fix as before** | Write the fix into the runbook. Open a problem record for the recurrence and attach the workaround; it becomes a known error once the cause is analysed (ITIL problem management) | At least 3; 4 if rote but needing a decision; retired with automation if rote and safe |
| **new or different fix**, or *can't tell* | Add an impact check, and open a problem investigation. If responders still can't tell after the impact check is rewritten once, the alert is not firing on a condition anyone can judge: route it to **alert needs changing** | At least 2 |

Alert changes follow alert-design practice (Google SRE book, *Monitoring Distributed Systems*; Ewaschuk, *My Philosophy on Alerting*). This review decides *that* an alert changes, not *how* to design one.

**Recall check.** Before any change to an alert, replay the changed rule against the incidents in the adopter's lookback. For a retirement, confirm that an alert on the affected service would catch each incident this one caught. The change passes if it would still have caught each one within the adopter's acceptable added delay. If it fails, create the covering alert first, or keep the alert unchanged.

**Held alerts.** An alert is marked *held*, with the reason, when nothing more can be changed for now. That covers three cases:
- it failed the recall check;
- it is at its target while a problem record is open;
- it is a critical gap that cannot reach the minimum until something else changes, recorded as an exception.

It leaves both lists until a new incident, the problem's resolution, or a change in the recorded reason.

## Measures

The SRE Workbook names four attributes for evaluating an alerting strategy: precision, recall, detection time and reset time. This practice uses the first two, where a significant event "consumes a large fraction of the error budget":
- **precision:** "the proportion of events detected that were significant"
- **recall:** "the proportion of significant events detected"

*[This practice]* For alerts not tied to an SLO, *action taken* stands in for "significant".

- **Precision** comes from outcome records. Unanswered firings are excluded, because nobody judged them.
- **Recall** comes from the incident record, because a missed incident never fires.

**Missed incident:** an incident whose first detection was not an alert on the affected service. An incident during which an alert on that service fired but went unanswered also counts as missed.

| Measure | What it is |
|---|---|
| **Load** | Pages per on-call shift, and the share out of hours. For comparison, the SRE book's *Being On-Call* sets an upper bound of "2 per 12-hour on-call shift", counted in incidents, not pages |
| **Coverage** | The share of incidents that were not missed |
| **Response** | Time to mitigate: until the impact stops, which can come before full restoration |
| **Runbook readiness** | Over scored alerts: the distribution of runbook states, the share of critical-service alerts at or above the minimum, and the share of state 3–4 sections that are stale |

Load must not improve at coverage's expense.

## Worked instances (public)

**CPUThrottlingHigh** (kube-prometheus). The runbook says the alert "is purely informative and unless there is some other issue with the application, it can be skipped", and "User shouldn't increase CPU limits unless the application is behaving erratically (another alert firing)." The rule set ships it at *info* severity, held back by an "InfoInhibitor" rule unless a warning or critical alert fires in the same namespace.
- It is a cause alert, already conditional by design.
- Firings at pod start-up (Mirantis troubleshooting documentation, of its equivalent alert: "The alert usually fires when a Pod starts") and on low-usage, bursty pods (Robusta) that clear unanswered route to *tune*.
- Firings recorded as **only meaningful alongside other alerts** route to the conditional row, which is what the maintainers chose.

**GitLab.com's alert noise.** GitLab's infrastructure team found thirteen alerts in their alerting configuration that fire when a condition has lasted less than a minute, then summed two weeks of firing time for critical production alerts and found these produced "about 74% of our alert noise over the past two weeks."
- This is the noisiest-alerts list: found from configuration and confirmed with tool data, with no outcome records.
- Three of their four proposals match three rows by kind of change (the fourth, which they favoured, was anomaly detection):
  - **extend the pending period:** *tune*
  - **use error rates instead of static thresholds:** *alert needs changing*
  - **review expressions that don't aggregate:** *alert needs changing*
- The practice would add three things:
  - criticality weighting by service tier (they filtered on alert severity, a different thing)
  - the recall check before lengthening hold durations
  - outcome records, so "nobody takes action for these alerts" becomes measured precision

**Limits.** Public sources give runbook text and estate-level noise measurements. None gives per-firing outcome records over time, so routing from outcome patterns is walked against reported patterns, not measured ones.

Sources: https://runbooks.prometheus-operator.dev/runbooks/kubernetes/cputhrottlinghigh/ · https://docs.mirantis.com/mosk/latest/troubleshooting/tshoot-stacklight/ts-alerts/ts-cadvisor-alerts.html · https://runbooks.prometheus-operator.dev/runbooks/general/infoinhibitor/ · https://github.com/robusta-dev/alert-explanations/wiki/CPUThrottlingHigh-(Prometheus-Alert) · https://gitlab.com/gitlab-com/gl-infra/production-engineering/-/work_items/6374
