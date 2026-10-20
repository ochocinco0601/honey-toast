# Templates

Every page is read by a person, often under pressure. The layouts below are the house style. The rules under them are what a review checks.

## How every page reads

- **The top answers the reader's first question in one line.** On an alert page that is "what is broken for users". On an overview it is "what this does".
- **Steps are a checklist, never paragraphs:** a numbered heading per step, and under it a table with one row per check, written as action → what you should see → what to do. This is the aviation quick-reference checklist form the runbook model names.
- **One sentence per cell, no more than about 15 words.** When a cell needs more, it is two rows, or the detail belongs on another page.
- **Commands go in their own cell, in code format,** copyable as they are.
- **Unknowns are collected, not scattered.** Each page has a *Not known yet* box near the top listing its open questions in plain words. A cell that depends on one shows only `not known yet`.
- **Provenance stays out of the reading line.**
  - A source is a small marker at the end of the cell, `[n]`, and the list is at the bottom under *Sources*.
  - A line from reading code, or from generic platform documentation, carries one mark, `†`, explained once in the footer: "† not confirmed by the team yet". Its question goes in *Not known yet* and in `questions.md`.
- **Words a responder does not need are cut:** probe intervals, severities, internal reasoning, "derived from".

## README.md

```markdown
# <System> runbooks

<One line: what the system does for its users.>

## If something is broken
First: [is it already known or expected?](shared/procedures.md#already-known-or-expected)

| Users can't… | Look at | Call |
|---|---|---|
| <log in> | [<service>](<service>/overview.md) | <team · on-call link [n]>, or not known yet |

## Services
| Service | What it does | Alerts | Runbook ready to |
|---|---|---|---|
| [<service>](<service>/overview.md) | <plain words> | [<Alert>](<service>/alerts/<Alert>.md) | who to call |

"Runbook ready to" climbs: **who to call** → **tell whether users are affected** → **fix it** → **fix it on one approval**.

## Never do
- <the one or two things that would destroy data or state, each with its page link>

## Keeping these current
- After each alert you handle: note what you found and did, then update its page. <how [n] or not known yet>
- After each deploy: run the post-deploy checks, and update the service's procedures with what changed.
- An open question about the code: ask the code-assistant tool the team uses first, then confirm with the developers before a fix depends on the answer.
- Each page says how far it gets the responder; the open questions say what would take it further.

## Alerts we need
| Problem nobody would be told about | Service | Seen in |
|---|---|---|

## Alerts to change
| Alert | Problem with it | For |
|---|---|---|

[Open questions](questions.md)
```

## \<service\>/overview.md

```markdown
# <Service>

<One line: what it does for users.>

| | |
|---|---|
| **Users lose if it stops** | <plain words> |
| **Call** | <team · on-call link [n]>, or not known yet |
| **Runs on** | <platform, where, how many [n]> |
| **Needs** | <services it calls> |
| **Needed by** | <services that call it> |
| **Dashboards** | <links [n]> |

**Declare an incident** when a second team is needed, users can see it, or <time box> has passed.
**When you call, hand over:** what fired, what you checked, what you did, since when.

[Procedures](procedures.md) · Alerts: [<Alert>](alerts/<Alert>.md)

> **Not known yet:** <question> · <question>

Versions · Sources
```

A service another team or a vendor operates:

```markdown
# <Service> (run by <team or vendor>)
<One line: what it does for us.>

| | |
|---|---|
| **Users lose if it stops** | <...> |
| **Call** | <owner record [n]> |
| **Their status** | <where [n]> |
| **Meanwhile, on our side** | <pause calls, stop retries, fall back [n]> |
| **Never** | <...> |
```

## shared/procedures.md

The entry point when there is no alert (a user reported it, someone noticed), and the home of checks that apply to many services.

```markdown
# Shared procedures

## Already known or expected?
| Check | If yes |
|---|---|
| An open incident for this? <where [n]>, or not known yet | Link it and stop |
| A deploy or change in the last <time>? <where [n]>, or not known yet | Check that service first; roll back if it does not settle |

## Is anyone affected?
| Do | If you see | Then |
|---|---|---|
| <reproduce what the user reported, or a check across the system [n]> | <it works> | Close: record what was reported |

## Checks that apply to many services
| # | Do | You should see | If not |
|---|---|---|---|
| P1 | `<command>` [n] | <healthy result> | <result> → <next> |

Versions · Sources
```

## \<service\>/procedures.md

```markdown
# <Service>: procedures

**Before you start:** <access and tool, one line [n]>. Change approval: <yes, how / no / not known yet>.

> **Not known yet:** <question> · <question>

## Checks
| # | Do | You should see | If not |
|---|---|---|---|
| C1 | `<command>` [n] | <healthy result> | <result> → C2 · <result> → C3 |

## Fixes
| Fix | When | How | Watch out |
|---|---|---|---|
| Restart | <condition> | `<command>` [n] | <what a restart loses, one line> |
| Roll back | <a release in the window> | `<command>` [n] | |
| Pause / fall back | | <or none> | |

## Is it back?
| Check | Good looks like |
|---|---|
| It is up | <health check [n]> |
| It is doing its work | <a case moves through, a backlog drains [n]> |

## Never
- <a step that is unsafe here, in one line, and why [n]>

Versions · Sources
```

### What each kind of service adds to its procedures

| Kind | Add |
|---|---|
| Application or API service | Rolling or full restart; what users see while it is down; session or cache loss |
| Agentic function | Which model, prompt and configuration version is running, and how to roll each back; the switch that pauses it without stopping the app around it; what happens to in-flight work; the manual fallback and who does it |
| Queue or messaging | Consumer or broker restart; what happens to a message that fails (a dead-letter queue and how to replay it, retried, or lost); whether messages survive a broker restart; duplicate risk |
| Data store | Usually not restarted by this team: failover, its owner; whether data survives a restart in this deployment |
| Batch or scheduled job | Whether it can run twice safely; restart from a checkpoint; its schedule window |
| Configuration or secret store | Where the value is set; how a change rolls out and back; expiry dates |
| Anything another team or an outside party runs (a vendor, a public service, a shared platform) | Overview only, short form |

## \<service\>/alerts/\<AlertName\>.md

```markdown
# <What is broken for users, in plain words>

**Alert:** `<AlertName>` · fires when <condition, one line [n]>
**Call:** <team · on-call link>, or not known yet · **Ready to:** who to call / tell whether users are affected / fix it

> **Not known yet:** <question> · <question>

### 1. Is it already known or expected?
| Check | If yes |
|---|---|
| An open incident for <service>? <where [n]> | Link it and stop |
| A deploy or change in the last <time>? <where [n]> | <wait for X, then re-check / roll back: procedures> |

### 2. Is anyone affected?
| Do | If you see | Then |
|---|---|---|
| <check on this alert's own cases and time window [n]> | <no failures> | Close: no impact |

### 3. Stop it getting worse
<one line, or "Nothing needed: <why>">

### 4. Find the cause
| Do | If you see | It is | Fix |
|---|---|---|---|
| Procedures C1 | <result> | <cause> | <fix, procedures> |

### 5. Close when
<the work is done again, one line [n]>. Not fixed: call, and hand over as in the [overview](../overview.md).

Versions · Sources
```

## questions.md

```markdown
# <System>: open questions

| # | Question | Who can answer | Fills |
|---|---|---|---|
| Q1 | <plain question> | <developers / platform owner / operations> | <page, step> |

## Found while writing, for the developers
- <a defect that would give a wrong outcome or lose data, one sentence [n]>

## Material not found
- <kind>: where does it live?
```

## Footer of every page

```markdown
---
Versions
- v1 <date>: <what, from what>.
- v2 <date>: <what changed, from what evidence>. <Ready to: before → after, if it moved>

Sources · † not confirmed by the team yet
1. <file:line, record id, dashboard or query name>
```
