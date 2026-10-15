---
name: implementing-a-measure
description: Work out how a specified measure could actually be taken - which kind of source (metric, log or event, trace, the edge, an external probe, client-side instrumentation, the business item's own record), in which of the tools this environment really has, and what each choice misses. Use when someone has a measure or an SLI in mind ("what share of payments complete", "how many orders are stuck past the time limit") and asks how to implement it, what to instrument, where to define it, which tool to use, or whether a tool's feature (a grouped-trace transaction, a synthetic test, a dashboard query) can serve it. It discovers the environment's monitoring and telemetry estate from whatever it can read, asks only what that leaves open, and never names a tool it did not find.
---

# Implementing a measure

A measure has been specified, and the question is how it could actually be taken. This skill gives the field's way
of thinking about that choice. It names no tool: which tools exist is for the environment to show (§3).

**Its input is any measure specification**: what is counted, over which population, for which question and which
use (a report, an alert, or both). That can come from a register of measures, a document, or a person's words.

---

## 1. Specification and implementation

| | Says |
|---|---|
| **Specification** | *"The assessment of service outcome that you think matters to users, independent of how it is measured"* |
| **Implementation** | *"The SLI specification and a way to measure it"* |

Both definitions are quoted from the Google SRE Workbook, ch. 2, "Implementing SLOs". The Workbook's point is that
one specification has several implementations, and each sees a different population. It recommends writing the
measure as a ratio: *"the number of good events divided by the total number of events"*. That applies to a measure
that is a share. A volume, a backlog or a duration has no good event. It is recorded in its own form: a count, a
current level or a distribution.

In ISO/IEC/IEEE 15939 terms, the specification is the *information need* and *measurable concept*. The
implementation is the *measurement method* (the logic) together with the *measurement procedure* (the operational
steps). Deming's *operational definition* covers both halves: the criterion and the test applied.

**Specification first.** Starting from a tool and looking for questions it can answer finds only the questions that
tool can answer.

## 2. How to think about the choice

### Where a count can be taken

| Source | What one record is | Good for | Cannot do |
|---|---|---|---|
| **Metric** | A pre-aggregated number over time: a counter, a gauge, a histogram | Rates, durations and saturation of requests and resources. **Counters of a case's transitions** (entered a stage, left it, by outcome) give entered-versus-left cheaply | Name one case: every label value is a separate series, so a case id is never a label. A latency threshold is only as exact as the histogram's bucket boundaries near it |
| **Log or event record** | One record per thing that happened | Counting events per case where the record carries the case id; the reason for a failure | Count what did not happen, unless compared with an expected population |
| **Trace** (spans) | One request's path across services, with timings | Where a request went, slowed or failed. Rate, errors and duration per entry operation, including spans grouped into a named set by a matching rule | Follow a case past an asynchronous hop unless the context is carried across (span links, propagated context or baggage). **A case that runs for hours or days is never one trace.** Count anything correctly under sampling (below) |
| **The edge** (load balancer, gateway) | One record per request as it enters | Requests the service never handled. In-service instrumentation cannot see a request that never arrived, so a service that is fully down can look healthy from inside | See inside the service |
| **External probe** | A scripted request run on a schedule from outside | Whether a path works from the user's side, with no traffic needed; catches requests that cannot reach the network | Say anything about real cases; it may miss problems that affect only some users. **Its traffic is excluded from real-traffic denominators** |
| **Client-side instrumentation** | Records from the user's device or browser | What the user experienced, including failures the server never saw | See work after the user's request ends. It needs a code change in the client |
| **The case's own record** | The case's state in the application's store, its state history, or its business event stream | Business health and impact: cases in a state, the oldest, cases past the time limit, cases that ended wrong | Explain why. **A store that keeps only the current state cannot answer timing questions.** Look for a history table, change data capture or an event stream |
| **A message log kept with the state** (an outbox, an integration-event table) | One row per message the application wrote alongside a state change, with its time and status | A partial history of the case where the store keeps only current state: when it entered a state, whether a message went out | Show states that send no message. Its rows may be pruned, so its retention is checked |
| **Configuration** | A setting as deployed or as read at start | Whether a part is set up as the design assumes (a timeout, a schedule, a limit) | See a later change unless it is read again. Deployed overrides can differ from the file |
| **Platform lifecycle events** | One record per start, stop, restart or schedule run of a deployable or job | Whether a job or a container ran, against its schedule | See a part that is running but doing nothing |
| **Another organisation's record** | What a partner, network or counterparty reports back: a settlement or reconciliation file, a status reply, a statement | The outcome of a case's stretch that runs outside this organisation | Arrive on time: it comes on the other party's schedule. Its definitions are theirs, and it may cover only some cases |

A *case* is one business item the flow carries: one order, one payment, one application. The sources follow the
Workbook (application logs, load balancer monitoring, black-box probers, client-side instrumentation) and
OpenTelemetry's signals (traces, metrics, logs, baggage). Counting from the case's own record is established
practice in **process mining** (an event log keyed by case id, activity and timestamp; IEEE 1849, XES) and
**business activity monitoring**.

### Rules of thumb

1. **Match the source to what the specification counts:**
   - **Cases:** the case's own record, events keyed by the case id, or counters of its transitions.
   - **Events:** event records, or counters of them.
   - **Requests:** the edge, metrics or traces on the operation.
   - **Resources:** metrics.
   - **Runs** of an AI agent, a scheduled job, a poller or a container: a span or log record per run, or the
     platform's lifecycle events, compared with the schedule. For an agent, use the OpenTelemetry GenAI conventions,
     which are still at development status.

   A judgment by an agent is recorded as an event: the decision, with the person's agreement or override. An
   implementation that counts something other than what the specification counts is a proxy, and is recorded as one
   (§4).

   **Decide the source kind from the specification first, before looking at the environment's tools. Never change
   it to fit them.** If the environment has nothing for that kind, the finding is the gap, not a different kind.
2. **Ask what population it sees.** Request-based sources count attempts, so retries inflate them. A probe counts its
   script. The edge counts what arrived, and the service counts what it handled. When two implementations of one
   specification disagree, compare their populations before calling either one wrong.
3. **Ask whether it can see what did not happen.** A trace or an error log cannot report silence. Only a comparison
   with an expected population can: cases that entered a stage against cases that left it, or a job's run against its
   schedule. **Both sides of that comparison need a source that is complete for every case: not sampled, and kept for
   the whole window.** A missing span or record counts as a failure only where the record would certainly exist for a
   success.
4. **Ask whether it survives sampling.** Head sampling keeps a known random share of requests, so counts from kept
   traces can be scaled back up by that rate. Tail sampling keeps chosen requests (errors, slow ones), so counts and
   ratios from what was kept are biased: error ratios rise. The safe route under either is to compute rate, errors
   and duration from every span, before the sampler. Exemplars tie a metric to sample traces without changing the
   count. **Where the sampler is not stated, treat the traces as sampled**: never count cases, or their absence, from
   kept spans, and say the sampler is unknown.
5. **Count a window by one clock.** A ratio or a duration for a period counts the cases that entered in the period,
   or the ones that left in it, never entries from one and exits from the other. Cases still open at the window's end
   are counted as open, not dropped.
   - **Where an outcome can arrive late** (retries, another party's file), count by the entry clock and state the
     longest delay. A period's figure is final only once that delay has passed, and an alert reads the cases old
     enough to have an outcome.
   - **The delay is a value a source states**, never one assembled from several (an interval from one source times a
     count from another). Where sources state different values, the longest stated is the bound, the others are
     carried, and the question is asked (§3.2).
   - Waiting for the delay makes an alert late, so pair it with a count of open cases already past the time limit,
     which needs no wait.
   - **An age runs from the case's entry into the state the measure names** (for "shipped", from when it shipped).
     That is the creation time only where the case is created in that state, and the answer says so. Count only the
     cases in that state, not every case that is unfinished.
6. **Ask whether it serves the measure's use: a report, an alert, or both.** An alert needs its count within its
   evaluation window, something that evaluates it, and somewhere it is sent. Multiwindow burn-rate alerting (SRE
   Workbook, ch. 5) pairs a short window with a long one. A query run once a day can feed a report but never an alert.
   Retention bounds how far back the measure can be compared. Record report use and alert use separately: an
   implementation can serve one and not the other.
7. **Take them in this order:** a faithful source that already exists; then a faithful new one; then a proxy, only
   as an interim and labelled as one, with the faithful source named beside it. Where the measure's existing
   definition describes a proxy, propose the faithful source and keep the existing one as the interim. The
   specification is never changed to fit the source.
8. **Ask where the definition lives, and what would notice it breaking.**
   - In code: an attribute set where the case is handled.
   - In auto-instrumentation: what an agent or library emits unchanged.
   - In configuration: a rule in a monitoring tool that matches an endpoint.
   - In a query.

   Any of them breaks silently when the code changes, unless a test or an alert on missing data guards it. A rule
   that matches an endpoint breaks on a rename without a code review seeing it. An attribute in code costs a
   developer's change and goes through review.

   A component's own built-in check (a database's readiness command, a broker's diagnostics, a cache's ping) belongs
   to the component. It is not a tool, and it may be named whether or not tools were found. Something must still run
   it on a schedule and keep its result, and that something comes from §3.
9. **When no source fits, keep the specification.** Record that no implementation is available, with what was
   considered and why each fell short. Where a source answers part of the specification, record which part it
   answers and keep the rest as the gap. Never mark the whole measure implemented. A gap is a finding about the
   environment, not a reason to change the question.

## 3. What the environment has

The thinking above is the same everywhere. **Which implementations are available is not, and it changes.** Work
that out for the environment you are in, in three moves, and write the result as a dated list.

### 3.1 Find it in what you can reach

Before proposing anything, search everything you can read for the environment's monitoring and telemetry estate.
That covers the code and its deployment files, the workspace's documents, and wherever you have access: mail,
chats, meeting notes and transcripts, shared files, a service catalogue. Look for:

- **What the code emits, and to where:** instrumentation libraries, exporters and their endpoints, logging
  configuration, metric registries, agents baked into images, sampler settings.
- **What collects and stores it:** collector and agent configuration, dashboards and alert definitions kept as code,
  queries saved in documents, links to monitoring tools in runbooks.
- **What people say they use:** tool names in runbooks, incident write-ups, onboarding guides, standards and mandates,
  meeting discussions. That includes what is being introduced or retired, and who owns each tool.
- **What teams built themselves:** scheduled scripts, check jobs and homegrown dashboards. Each is an option like
  any product, listed with its owner.
- **The environment's own names.** One product often goes by several names: a vendor name, an internal shorthand,
  a former name. Record them as one option with its aliases, never as several.

Every fact found is cited to where it was found, with that source's date. A tool mentioned once in an old chat is
weaker evidence than one in a current deployment file; say which kind each row rests on. **Found is not the same as
available to this flow.** A tool the organisation uses can still not reach these parts. Reach is filled from
evidence about these parts, or marked unknown.

### 3.2 Ask what it could not settle

After the search, list what it left open.

- **The specification itself comes first, when it came in a person's words.** A word the measure turns on that no
  source defines ("started", "completed", "the time limit") is asked first, with the definition proposed from what
  was found.
- **Then the environment:** an option whose reach to these parts is unknown, two sources that disagree, a status or
  retention nobody states, a name that may be one tool or two.

**Ask the person these as specific questions, each carrying the evidence found and a proposed answer.** For example:
"Two documents name a tracing tool and its former name. Are these one product, and does it receive traces from the
payment service?"

- Ask them all at once, not one at a time, and only what the search could not answer. A question the code or the
  documents already answer is never asked.
- **Every proposed answer comes from evidence about the same mechanism, cited.** A different job's clock is not this
  alarm's clock. Where there is no evidence, the proposed answer is `unknown`, never a guess. A proposed answer is
  never stated as fact later.
- The same holds for the implementation. A field, a status value or a table that a query or a definition relies on
  is cited to where it was seen, or raised as a question. It is never assumed.

If you cannot ask, or nobody answers, carry on. Use the proposed answer, labelled `proposed:` with its evidence. The
question stays on the list for whoever owns it.

### 3.3 Write the list

The result is the environment's list, dated, one row per option:

| Column | Holds |
|---|---|
| `option` | The environment's name for it, with its aliases |
| `sources` | Which sources from §2 it takes |
| `defined_by` | How a measure is defined in it: code, auto-instrumentation, configuration rule, query |
| `reaches` | What it can see, and what must be onboarded to it first |
| `freshness`, `retention` | How soon a count is available, and for how long. Where another option stores the data, name it, and that option's row decides |
| `evaluates` | Whether it evaluates a count against a condition and sends a notification, or relies on another option to do so |
| `status` | The option's lifecycle **for these parts**, not across the organisation: in use for them, being explored for them, being introduced, being retired, or in use and moving to another option (name it). A tool in use elsewhere but only being explored here is not in use |
| `owner` | Who runs the option, and whom to ask about it |
| `as_of` | The date the row was true, and who said so |
| `evidence` | Where each column's value was found (file and line, message, meeting, document), or `asked:` with the person and date, or `proposed:` with its basis |
| `open` | The questions still unanswered for this row |

**A list already exists?** Read it first. Search only for what is newer than its date, or for what it leaves open,
and update it rather than starting again.

Propose implementations only from this list, and cite the row. **Where the search found nothing and nobody could be
asked, name the source kind only, never a tool.** A row past its stated date is used with its date shown.

**An option implements a measure only if all four hold:**
- its `reaches` covers what is counted, read literally. Where the row is narrower than its own name suggests, follow
  the row and record the question for the list's owner;
- its `status` covers the use (an option for development only is never a production implementation);
- its `retention` covers the measure's window;
- its `freshness`, and something that evaluates it, cover alert use if the measure is to alert.

Otherwise it is not an implementation, and the answer says which condition failed. A measure may need two options:
the count from one and its population from another. Record both. The list belongs to the environment. The nearest
established forms are a technology radar and a platform team's supported-tooling catalogue. A radar's rings advise
people what to adopt, whereas this list records what is in use and bounds what may be proposed.

## 4. What is recorded, for each measure

Recorded wherever the measure lives, all `proposed:` until a source states it or the people who build it agree:

- the source kind (§2), decided before the list is read;
- the operation it is taken on, if any;
- where the definition would go: a code line, a rule, a query, or the case's own record;
- the option or options chosen, each with its list row;
- the query: good over total for a share, the count for any other form;
- its use (report, alert, or both), and what stops the other;
- whether it is a proxy, and the faithful source it stands in for;
- what it misses against the specification, including any part not answered;
- the alternatives considered and why each fell short.
