# Runbook standard

**For:** team leads and readiness reviewers. **Job:** say how good a service's runbooks must be, and score a runbook against that.

It replaces a yes/no "runbook link exists" readiness check (O-BOK IN-08, KA03), under which an escalate-only runbook passes.

## Runbook state

*[This practice]* Scored against the [runbook model](runbook-model.md). Its anatomy table lists the sections each state requires.

| State | Name | What the runbook lets the responder do |
|---|---|---|
| 0 | None | Nothing: no runbook link |
| 1 | Escalate-only | Escalate. The knowledge lives in a person |
| 2 | Impact check | Tell whether action is needed (which test, which result means which ending), close the no-action endings, and escalate |
| 3 | Mitigating | All of state 2, plus restore |
| 4 | Assisted | All of state 3, where the restore is rote but needs a human decision (risk, timing, blast radius), so it runs on one click or approval |

**Off the scale: retired.** The page is removed, demoted to a ticket or dashboard, or replaced by a different alert (which gets its own state). A restore that is rote *and* safe without a decision should not page at all: "if a page merely merits a robotic response, it shouldn't be a page" (Google SRE book). It runs automatically and the automation is monitored. The top rung of the SRE book's automation hierarchy is the same idea: "systems that don't need any automation."

States 0–2 have no published counterpart found. States 3–4 and retired follow the direction of the SRE book's automation hierarchy.

## Scoring rules

- **A runbook takes the highest state whose required sections it has in full.**
- **A linked runbook with no escalation path** scores 1 and is flagged; adding the path is the cheap fix.
- **Cause-hunting is not an impact check.** Steps that only diagnose the cause, with no test of whether users or the business are affected, leave a runbook at state 1.
- **A symptom alert carries its own impact check.** When the alert fires on the impact itself (for example an SLO burn-rate alert against the expectation), the firing establishes impact. The runbook still needs the *already known* and *expected condition* tests to reach state 2.
- **Shared runbooks.** A platform alert often fires for many services and links one generic runbook. The impact check can be generic, but the restore usually depends on the service, so the state is scored per alert on each service. A generic runbook rarely rises above state 2 without a service-specific section.
- **Who scores:** tool data shows only state 0. States 1–4 need someone to read the runbook against the model.

## Minimum state

For critical services, the adopter sets a minimum state, typically 2 or 3 *[Assumption]*. It applies:
- to new alerts at readiness, where the runbook must also have been **rehearsed once** (runbook model, step 7), because an unrehearsed runbook is untested *[This practice]*;
- to existing alerts through the estate review's critical-gap list.

## Currency

- **Validated** applies per runbook section. For a shared runbook, a section is the generic part or one service's section, so one service's success does not validate another's restore steps.
- **A section is validated** when it is used successfully (runbook mark *worked* in the [outcome record](outcome-record.md)) or rehearsed.
- **A section is stale** when it is past the adopter's validation window, has never been validated, or has a *failed* mark. Staleness is reported as a flag ("state 3, stale"), not a lower state.
- **A stale section is cleared** by a successful use, a successful rehearsal, a correction followed by either, or re-scoring to the state it actually supports.

## Worked instance: KubePodCrashLooping

A real, widely used public runbook from the Kubernetes monitoring rule set (kube-prometheus):
- **Impact:** "Service degradation or unavailability."
- **Diagnosis:** pod status, events and logs, and a list of likely causes (resources, dependencies, configuration, secrets, permissions).
- **Mitigation:** "Talk with developers or read documentation about the app."

**Score: state 1.** Every diagnosis step finds the cause; none tests whether users are affected (for example, whether other replicas are still serving). The restore is "talk with developers." It is the escalate-only case with a diagnostic appendix. It is also a shared runbook, used by every service on the platform, so reaching state 3 needs a service-specific restore section.

A second instance: the kube-prometheus **CPUThrottlingHigh** runbook says whether action is needed ("purely informative… unless there is some other issue") and gives a conditional fix, but names no escalation path, so it scores 1 and is flagged.

Sources: https://runbooks.prometheus-operator.dev/runbooks/kubernetes/kubepodcrashlooping/ · https://runbooks.prometheus-operator.dev/runbooks/kubernetes/cputhrottlinghigh/
