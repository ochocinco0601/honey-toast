# Outcome record

**For:** the on-call responder. **Job:** what to record when closing an alert, so the judgement made on this firing is not lost.

## Why

An unrecorded judgement is redone on every firing. Firings that need no action, repeated, teach people to stop responding: **alert fatigue** (Google SRE book, *Monitoring Distributed Systems*). Its worst consequence is a real firing dismissed as "it always does that." The outcome record is what lets the [estate review](estate-review.md) tell noise from need. *[This practice]*

## What to record, per acknowledged firing

*[Adapted from Etsy Opsweekly, which asks the on-call engineer "a few simple questions about each alert received", with Action Taken / No Action Taken types, reason tags, a notes field and bulk classification.]*

| Field | Values |
|---|---|
| Outcome | *action taken* · *no action taken* · *can't tell* |
| Reason tag (one or two) | **no impact** · **threshold or duration wrong** · **only meaningful alongside other alerts** · **alert needs changing** (including *fired too late*) · **same fix as before** · **new or different fix** |
| Runbook | *worked* · *failed* (a step was wrong or could not be run) · *gap* (the condition is not covered) · *not followed* |
| Note | what restored service, or what should change |

**Which outcome and tag for which runbook ending:** the endings table in the [runbook model](runbook-model.md) gives the outcome and tag for each ending.

## Rules

- **The outcome records what restored service, or that nothing was needed.** Escalating is not itself an action.
- **Who completes it:**
  - The responder fills the **runbook** field: how the runbook served them. If escalation was the runbook's correct ending, that is *worked*.
  - The **outcome, tag and note** are completed by whoever resolved it. On an escalated firing that is the receiving tier, recording what they found and did.
  
  Without this split, every escalate-only alert looks like it always needs action, and its noise stays hidden. *[This practice]*
- **What a firing is:** one notification to a person, after the tool's deduplication. Where the tool groups several alert rules into one incident, record one outcome per alert rule.
- **Inside a declared incident**, the many alerts that fire alongside the main one are recorded in bulk once the incident ends, as *no action* · **only meaningful alongside other alerts**, unless someone acted on one specifically. *[This practice]*
- **Firings nobody acknowledged** are not recorded by the responder. The alerting tool counts them as *unanswered*; the [estate review](estate-review.md) treats them separately.

## What a runbook mark does

| Mark | What it changes |
|---|---|
| *worked* | Updates the last-validated date of the runbook section used |
| *failed* | Flags that section stale at once |
| *gap* | Flags a coverage gap for the next review. The runbook is not marked stale |

The stale and validated rules themselves are in the [runbook standard](runbook-standard.md).
