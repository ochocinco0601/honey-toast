# Proposing the measures for one flow

This is the step "Propose the measures" of business flow observability, and this file is its only text. The
measures skill runs it alone; the stage kit runs it too, for its phase 4, by handing the step to this skill. The
opening below is the same as the stage kit's and the mapping skill's steps files open with, and holds for this
step too; what it says of the work after the measures (the alerts, the runbooks, drawing the map) is the stage
kit's.

For a language model drafting from the source material it is given. The run never stops to ask a fact it can infer:
what the sources do not state, the model infers plausibly and labels `proposed:` with its basis, and a person confirms
or corrects those rows afterwards. What is the person's (intent, scope, judgement and taste: which flow, whether the
sources are enough, whether to keep going) is brought to them with a proposal when it arises; the plan (the mapping
skill's, before it reads the code in depth) is the first such point. The result is a filled register (the tables in
`register-template/`, defined in `register-template/REGISTER.md`) from which `one_canvas.py` draws the
design-for-operations map, and from which `flow_outputs.py` generates each stage's slice, measures, alert and
runbook.

These are design-time views. You are describing what the capability is and where it could be seen, not reading
a running system. Nothing you write is a live value.

**This procedure is the method's procedure, applied to a register.** The method is
`reference/assigning-business-work-to-levels.md` (cited below as *Assigning*, with its Step number)
and `reference/what-each-level-can-report.md` (cited as *Rules*). Where a step below says what to do,
the method says why. The terms are defined in `reference/vocabulary.md`, and the measure layers in `reference/four-layers.md`. One thing is built first, and everything else is read off it: **the case's lifecycle**,
the states one case passes through and the moves between them. Stages and alerts are drafted from it with the
basis of each cited; process steps, parts, measures and the runbook are each derived from it by a stated rule. Either
way a later check has something to compare them with.

Three sources feed a register: the **code**, the **documents** (runbooks, architecture pages, service catalogue
entries, the business's own process descriptions), and anything people have said that was written down (notes,
tickets, recorded answers). Code shows what carries each move. Owners, responders and volumes that no source
states are inferred and labelled `proposed:`; volumes stay named for the operators to measure. A party's objective
is never inferred: it is written only where a source states it (Step 9, the parties and their expectations).

## Step 9. Propose the measures, question first (*Rules*, the form and Rule 1)

**Only this step writes `expectations.csv`, `measures.csv` and its own rows of `measure-gaps.csv`** (those of the
coverage list's questions and of `expectation: indicator`; mapping's questions and `alert: its own tests` are the
other steps'). A later step that needs one of them changed asks for it in
`corrections.csv`, and this step answers.

**What this step reads.** The register's flow tables, which mapping wrote and this step never writes (where one is
missing or wrong, file a row in `corrections.csv` for mapping); the code, the repositories mapping read, which this
step opens itself, with the Read tool, at each line a measure would be counted from; for `watched`, the collection
configuration within reach (scrape, collector or dashboard configuration, and wherever the export address is
actually set, below); and the method's lists, which give the
values of `layer` (`method/layers.csv`), `form` (`method/measure-forms.csv`), each part kind's set
(`method/part-kinds.csv`) and the agent questions (`method/agent-questions.csv`).

**The tables it writes, with their columns in this order** (the first line of each file):

```
expectations.csv   expectation_id,flow,stage,party,expectation,satisfied_when,objective,objective_source,source
measures.csv       handle,subject_id,step,stage,flow,measure,question_it_answers,layer,counted_on,counted_how,form,exists,agent_question,source,source_ref,expectation,operation,receipt_question,defect,watched,watched_source,taken_from,counted_at,for_flow,instrumented_kind,instrumented_signature,exporter_name,taken_at
measure-gaps.csv   element,question,kind,why,source
product-names.csv  name,source
```

**Each time this step runs, read `corrections.csv` first.** Each `open` row whose `table` is `measures`,
`expectations` or `measure-gaps` is a request to this step: from the runbook step, a measure one of its tests
reads that no row holds (a companion measure); from choosing the alerts, a measure an alert the person asked for
would rest on. Its `row` is blank for a row to add, or names the row to change; `proposed` says what to measure, at
which part, and why. Take each up or turn it down, as you would any candidate: write the row from the code read,
with its citation and, in `for_flow`, the flow whose later step asked for it (the flow worked now), and set the
correction's `status` to `taken up`; or set it to `turned down` and write why in
this pass's `how-made.csv` `note`. Then the person reviews the measures again. The review of the measures will
not take their go while such a request is still `open`. Once they have said go, the review is closed: it opens
again only when this step runs again (`go.py --back-to-measures`, `flow_outputs.py --measures`, or a new pick of
how far each stage goes), so a change a later step makes to these tables itself is refused at the runbooks and
named by the done check until it comes through here.

### First, the parties and their expectations

This is what "working" means to each party, so it is the first part of this step, not of mapping: mapping names
whom the flow serves (`flows.csv` → `customer`), and this part writes what each party counts on. It is written for
the flow and for each stage picked to measure. In `how-made.csv` its `step` is `9`.

Write `expectations.csv`: whom the flow serves, and what each of them counts on, of the whole flow and of each
stage. It is the flow's stakeholder register, one row per party per expectation. It comes after the stages because
a stage's expectations are written per stage, and before the measures, because Step 9 ties each measure to the
expectations it is evidence of.

**Who counts as a party.** A party is someone the flow's outcome serves or binds: the customer (`flows.csv` →
`customer`, the one party whose outcome ends the flow), a regulator whose rules the flow must keep, a sponsor. A
person who carries out a process step (a row in `participation.csv`: a clerk, an underwriter) is a performer, and is a party
only where a document or a person states what they expect of the flow. Name each party by the role the business
uses, and write the customer exactly as `flows.csv` writes it. A party no document or person names, read from the
code alone (a persona, an authorisation role, a rule the code enforces), is written `proposed: ` with that basis.

**What each party expects.** For each party, the expectation of the whole flow (`stage` blank), and of each stage
where they expect something of it, in their own words where a source has them, quoted and cited. Code is a source
here for two things only: **the text the system shows the party** (status messages, notifications, notices) and
**the rules the code enforces** (a notice that must be sent within a deadline). Where no source has the words,
write `proposed: ` and the expectation. The customer has at least one expectation of the whole flow, and every
measured stage has at least one expectation, the customer's included: the flow card's *Serves* and the stage card read them.
`check_measures.py` fails a run that records none of the whole flow, or none of a measured stage. The quote is
cited in `source`: `expectation` and `satisfied_when` carry no file citation (no path, file name or line), since
the reviews show them to people as the party's own words. `check_measures.py` fails one that does.

**Expectations come before alerts.** Usually write each expectation from what a party is told or a source states,
before any alert is drafted. An alert then names the expectation it guards (the stage kit's step "The failure modes, the alerts and the runbook for a stage", "Alerting", in `alerts.csv` → `guards`); the expectation is not written
from the alert.

**What satisfies it.** `satisfied_when` is the satisfaction condition: what one case would show if the expectation
is met (its state, the record written, the values it carries), read from the lifecycle and the process steps. It is
testable on one case. Write it `proposed:` unless a source states it, as for `right_outcome`. It holds the
condition only: what the code cannot show (the last state it records falls short of the condition) is never
appended after a `;`. Step 9 writes it as a `measure-gaps.csv` row of kind `no record`, whose `why` says which
record is missing.

**The objective is never drafted.** `objective` holds a bound only where a document or a person states one, and
`objective_source` cites the statement. **Text the business shows the party is a stated objective**: "1-2 weeks"
on the customer's status screen is the business stating a bound, cited to the line that shows it. Write it as
stated: two bounds shown for one stage stay two, never summed or averaged. Where nothing states one, leave
`objective` blank, never `proposed:`. A blank objective is a finding for the people who will later choose
objectives, not a gap in the run.

**A rule the code enforces is a stated objective only where the code names its authority** (a check that cites the
regulation it implements). Then `objective_source` carries both the code line and the authority it names, for a
person to confirm. Where the code names no authority, the bound is the code's own: it belongs in `bound_in_code`
(the mapping skill's step "Cut the stages from the lifecycle"), and `objective` stays blank.

**Not found is not absent.** A party inferred from the rules the code enforces was read only as far as the code
goes. Write in that row's `source`: `only the obligations this code enforces were read`. Obligations the code does
not enforce were not looked for.

**The code's limit and the objective stay apart.** `bound_in_code` is what the application assumes; `objective` is
what a party has been told or a rule states. Where they disagree, both are kept, and the stage card shows the two
as a finding (the mapping skill's step "Cut the stages from the lifecycle").

### Then the measures

This step proposes **candidate** measures: what could show whether the capability works. It does not choose which
are wanted, and it sets no targets or thresholds. Choosing measures and making them service level indicators with
objectives is done later, by people. The candidates are accounted for with three mechanisms adapted from a service onboarding practice and its question set, so that a thin
stage or an unmeasured agent step is caught rather than left unnoticed.

**Measuring is chosen per stage; mapping is not.** Mapping (Steps 1 to 8) covers the whole flow. Then the person picks how far
each stage goes (`go.py --depth`, once the flow is mapped). This step's stage, step and part levels run only for the
stages they chose to measure. The flow level runs as soon as any stage is measured, because the flow's own measures
belong to the flow. A part shared by several stages is measured if any of its stages is. The expectations are this
step's too (its first part, above), with the measures that show each is met: written for the flow and for each
measured stage. With no stage measured this step is not done at all.

Work down the levels, asking the question first and then naming the measure:

1. **The flow** (its case subject, `flow` set, `step` and `stage` blank): cases started, finished, still open;
   finished on time and right; where the code sets the flow a time limit, still open past it.
2. **Each stage** (its case subject, `stage` set): cases in the stage now, the age of the oldest, the time to get
   through, and, where the code sets the stage a time limit, cases past it. Counted from the case's state changes
   at the stage's entry and exit. A stage measure counts cases, never requests. Mark each in `receipt_question` with
   the candidates it answers (`in the stage`, `oldest's age`, `time through`, `past the time limit`); one measure
   may answer two.
3. **Each process step that matters** (one event per case): did it happen for this case, and was its outcome right. The
   process steps that matter are each stage's **exits**, read from its moves in `lifecycle.csv` (a process step whose move takes
   the case out of the stage, by the main move and by every alternative or exception ending, never the process step that
   happens to be listed last), the flow's first process step, every process step with a step-impact row, and every process step an AI
   agent serves (its participation rows, and its `agent-system.csv` run and actions). Each of these is owed only when
   its stage is measured: the flow's first process step, in a stage left mapped only, is not asked. Mark each process
   step measure in `receipt_question` with the question it answers.
4. **Each part, its kind's set** (`method/part-kinds.csv`), at its layer: `application` for an application
   component, `technology` for a system component. An external dependency is asked the same sets from the
   calling side, at its own layer: the coverage list holds it as one item (an external dependency of the
   application layer, below), covered by a measure of the dependency taken from the caller's outgoing requests to
   it. An application component is asked **per operation** (mechanism 3). Every component that takes part
   in a process step is asked, whatever its involvement: a store whose only rows are `records` (a basket store a restart
   empties) is asked its set like one that performs. An AI agent is read at two grains (below): its judgment at
   each **decision point**, and its operation at its **runs**. **An agent whose own component also serves a route**
   (the agent is the deployable, and a caller reaches it by an HTTP route) is asked both: the agent questions, and
   the application set for each route on its rows, keyed like any operation (`S06 POST /chatclient`). Hosting an
   agent does not take the component's route out of the application layer. The receipt tells a route from a tool
   by how `operation` is written, a method and a path (`POST /chatclient`) or `route` and a pattern; a handler of
   another kind on an agent's row (a message consumer, a gRPC method) is not recognised yet, so write its
   application candidate or gap by hand and say so in `why`.

**Layer and form come from the method's lists.** `layer` is one of `method/layers.csv`. `form` is one of the forms in
`method/measure-forms.csv` (its `applies_to` says which layers each suits). A part kind's set
(`method/part-kinds.csv`) names questions; each item of it is measured in the form below, the field's own: RED's
rate, errors and duration, USE's utilization, saturation and errors, and the service level indicator types of the
SRE Workbook ("Implementing SLOs": availability; freshness, correctness and coverage for pipelines; durability for
storage). Write the item itself in `question_it_answers`, and its form in `form`; the person's review shows each
part's measures by form, so a measure with no form loses the kind of signal it is. Every measure has a form, never
blank: a measure of a setting the part runs with (a poll interval, a queue's bindings) is of form `configuration`,
the setting's value watched for drift. `check_measures.py` fails a blank form and a form not in the list.

| Set item | Form |
|---|---|
| `rate` | `rate` |
| `throughput` | `rate` |
| `errors` | `errors` |
| `timeouts` | `errors` |
| `throttled` | `errors` |
| `redeliveries` | `errors` |
| `duration` | `duration` |
| `saturation` | `saturation` |
| `utilization` | `utilization` |
| `available` | `availability` |
| `right answer` | `correctness` |
| `correctness` | `correctness` |
| `accuracy` | `correctness` |
| `validity` | `correctness` |
| `duplicates` | `correctness` |
| `freshness` | `freshness` |
| `timeliness` | `freshness` |
| `lag` | `freshness` |
| `coverage` | `coverage` |
| `completeness` | `coverage` |
| `durability` | `durability` |

A call that timed out or was throttled, and a message delivered again, are failed requests (RED's errors); a
duplicate, an inaccurate or invalid value is a wrong output (correctness); a consumer's lag and a value's timeliness
are how old the data is (freshness); completeness is coverage. No item of any set is without a form today.

### The agentic layer: the decision point and the run

the mapping skill's step "Describe each AI agent as its own system" classed each agent's tools, replies and chained actions as its decisions or not; here each one classed `yes:`
is keyed as an element of the receipt and asked. A tool's class can depend on the conversation (the mapping skill's step "Describe each AI agent as its own system"): the same
call either records what the person named, or chooses for them from what they only described, and is classed
`yes:` for the second. Where telemetry can tell the two kinds of call apart, the candidates count only the judged calls,
and say how in `counted_how`. Where it cannot, the reason says so, and every call is counted. The receipt cannot
split the two; the reason is where the difference is kept.

Each reply classed `yes:` is a decision point keyed, like a tool's, by the agent
and the operation whose result it reports, element `S04 reply to uw_render_decision`, listing every process step it spans: a
judge sampling the agent's replies after that operation is one measure whichever of those process steps the case is in. Its
candidates name `reply` and the operation in `operation` (`reply; uw_render_decision`). A row naming no tool keys its
reply by its process step (`S04 reply at step 17`), with `reply` in `operation` and the process step in `step`. **An agent with no
tools** still has its reply as a decision point, keyed by the agent and the route that runs it: element
`S03 reply on POST /`, candidates naming `reply; POST /`. The receipt writes `reply on` where the row's operation
is a route and `reply to` where it is a tool.

A model output a later call relies on, classed `yes:` on its action row (the mapping skill's step "Describe each AI agent as its own system"), is keyed by the agent and its
place in the chain, element `S03 AS2`, and asked the same questions; its
candidates name the action's id in `operation` (`AS2`). Only an action row classed `yes:` is asked. Grounding comes first:
does the reply say what the tool returned (a judge sampling replies against the tool's output, NIST AI 600-1
MS-2.5-003). Correctness, traceability and drift take the forms below. Correctness comes from the person's
agreement with the reply itself, never from a record of something else, such as agreement with a rule's result.
Where nothing records that agreement, propose a labelled set or a judge, or write a gap. Traceability comes from
the run and tool-call record: a record of the turn that carries the case, holding the tool's result beside the
reply.

**At each decision point** (`yes:`), the agent questions of grain `decision point` in
`method/agent-questions.csv`. Write each candidate for that tool, naming it in `operation`, from what that tool
writes, in these forms:

- **correctness**, from the person's agreement with or override of that decision, where a record keeps it: NIST AI
  600-1, *Generative Artificial Intelligence Profile*, MS-4.2-004, *"Monitor and document instances where human
  operators … override the GAI's decisions"* (nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf). Where no record
  keeps it, a judge or a labelled set re-run per release, or a gap.
- **grounding**, from checking the decision against the inputs it claims to rest on: the values the tool wrote,
  recomputed from the case's own records (NIST AI 600-1 MS-2.5-003, sources checked in ongoing monitoring).
- **traceability**, from a run and tool-call record that carries the case: which decider, which inputs, which
  case (the OpenTelemetry GenAI `invoke_agent` and `execute_tool` spans carry the agent's id and version, the
  conversation and the tool; OpenTelemetry semantic conventions for generative AI, `docs/gen-ai/gen-ai-agent-spans.md`
  and `gen-ai-spans.md`, status Development). A record keyed only by session does not carry the case: say so.
- **drift**, from that decision point's inputs and outputs compared with a validated baseline, and the agent's
  configuration (model, prompt, rules) compared with the one vetted (NIST AI 100-1, MEASURE 2.4, functionality and
  behaviour monitored in production).

A measure that names no tool answers for none of its decision points: the grain is the judgment. A measure listing
every tool the agent has is not a decision-point candidate; write one per tool, against what that tool records.

**At the run**, every agent, whatever its tools are classed: the agent question of grain `run`, `operating health`. One
run is one invocation of the agent: a request in, the model and tool calls it makes, an answer out. Each of five
metrics is its own element, covered by an `agentic` measure of the agent with `agent_question` `operating health` marked
for it in `receipt_question`, or gapped:

| Run metric | The field's form (OpenTelemetry GenAI semantic conventions, repository `open-telemetry/semantic-conventions-genai`, status Development: `docs/gen-ai/gen-ai-metrics.md`, `gen-ai-token-metrics.md`, `gen-ai-agent-spans.md`) |
|---|---|
| `run duration` | `gen_ai.invoke_agent.duration` per run; a model call's duration (`gen_ai.client.inference.duration`) is not a run's |
| `failed tool calls` | `execute_tool` spans and calls per run, with `error.type` set |
| `tokens` | input and output token usage per run (`gen-ai-token-metrics.md`) |
| `refusals` | a run ended by a guardrail or the model declining: the finish reason, a shield's block |
| `fallbacks to a person` | a run handed to a person, or ended telling the person to try later (NIST AI 600-1 MG-3.2-006: monitoring that triggers human intervention) |

These are recorded at the agentic layer of the agent (`layer` `agentic`) as operational evidence, not judgments of whether it decided well. **Escalation and
policy scope** stay `candidate` and are not asked; where an application emits a refusal per tool call by its role
or authorisation check, propose one `policy scope` candidate from it.

**A measure emitted but counting the wrong thing gets `defect`**: one line saying what it counts wrong, with the
citation (a per-tool duration that is the batch's time split evenly; a label that never varies; a counter nothing
increments; a summary serving generated data while its source is off). `source_ref` keeps only the emitting line.
`defect` is written only where `exists` is `yes`: a proposed measure is not yet counting anything.

`exists` is `yes` only where the system already emits it: cite the emitting line, or the setting that switches on
a framework's built-in metric, in `source_ref`, and write `declared` in `source`. A log line counts, if it is
written once per case: read where it is written and what triggers it. Everything else is `exists` `no`, `source`
`proposed`.

`exists` follows from whether the signal the measure is counted from is produced today, never from its kind in
`taken_from`. A count of a request metric the framework already records is `yes`, like every other measure of that
metric, even when no one has built the count yet. A join of log lines or spans the code already writes (orders
cancelled while their payment went ahead, from the payment log line and the order's state) is `yes`, citing each
emitting line: it needs a query, not a code change. Only a measure that needs the code to write something it does
not write today is `no`. A record the code already stores is produced today: a count over rows of a table the code
writes is `yes`, and so is a server's own answer to a probe, like its other statistics. Whether anything collects
the signal is `watched`, not `exists`. Two measures counted from
the same signal have the same `exists`.

On every measure, write in `taken_from` the kind of record it is counted from, one of these eleven: `metric`,
`log or event record`, `trace`, `the edge`, `external probe`, `client-side instrumentation`, `the case's own
record`, `a message log kept with the state`, `configuration`, `platform lifecycle events`, `another organisation's
record`. Where `exists` is `yes`, the kind of the cited line; on a proposed measure, where it would be taken from,
decided from what the measure counts and never from the tools at hand. Name the kind of the cited line itself, never of what it
reports on: a part's own health check is the kind of record that runs it (a probe or a metric), never the case's own
record or configuration.

On every measure with a `source_ref`, write in `counted_at` the named place it is counted at: `taken_from` says the
kind, `counted_at` says which one, so a reader can go and find it. It is a plain name a reader knows without the
code: the table and the database it lives in (`order lines table, ordering database`, never `ordering.orderItems`),
the log and the service that writes it (`Ordering API log, line 'CreateOrderCommand succeeded'`), a service's
request metric or traces, or the system whose own status it is (a queue's depth is the message broker's own status,
connections are the database server's own status, never a metric of the application that uses them). Never a code
identifier: nothing dotted or backticked, nothing quoted unless it is a log line's own words (after `line`, or
before `log line`), and no table, class or event name as the code spells it; say a state or an event in words.
Product names, abbreviations such as e.g., and version numbers are plain names. A product whose own name has a
capital inside a word (`SiteMinder`) and that the check refuses is declared in `product-names.csv` in the
register: its name as one word, and in `source` where its vendor or the sources write it so. A declared name
passes only as a whole word, and one holding a dot, underscore, backtick or slash is ignored; never declare a
table, class or event name. A server's own status names the product where the code shows it:
`database server's own status (PostgreSQL)`, `message broker's queue status (RabbitMQ)`. A measure counted from
two places names both, as `X, against Y`: `orders table, ordering database, against the Payment Processor log`.
`flow_outputs.py --check` refuses a name only the code knows, and two measures with the same `counted_at` and a
different `exists`. Fill it per row from that row's own `counted_how` and citation:
this step has the code, so open the cited file at the cited line yourself, with the Read tool, and name the system
that holds what it shows. It is never filled by walking the code again: only the cited line and what it names are
opened. Where the cited code does not show the place (a proposed measure whose
record does not exist yet), write `not in the code: ` and what it would take. Never leave it blank:
`flow_outputs.py --check` fails on a row with a citation and no `counted_at`, and the run is not done.

**Two measures at one place say what tells them apart.** Where two measures name the same `counted_at`, each one's
`counted_how` says what in the signal tells its events from the other's (a label, a log line's words, a field the
record carries). Where the signal holds nothing that does (a request metric whose labels carry the address but not
which kind of notice was posted), one of them says in `defect` that the two cannot be told apart at this place,
naming the other: an alert on either would fire on both. `check_measures.py` fails two measures at one place with
the same `counted_how` where no `defect` says so; whether what tells them apart is really in the signal is for the
reviewer.

**A measure of cases is taken where one case can be told from another.** `counted_on` says what one event is: a
case, a request, a notice, a run. A measure `counted_on` cases is never taken at a part that never holds the case's
own identifier (`subjects.csv` → `carries_case_id` `no`): there, say what it is of instead. A metric can show cases
(a counter raised once for each order placed), but it cannot say which cases, so it never answers a question about
each case (`in the stage`, `oldest's age`, `past the time limit`): take those from the case's own record. Where a
measure of cases is taken from a metric, `counted_how` says why each increment is one case (`once per order
placed`): one post per partner, or one request per retry, is not one case. `check_measures.py` fails the first
two and notes the third until `counted_how` says why each increment is one case.

**A measure can be emitted and never collected.** On every measure whose `exists` is `yes`, write `watched`:
`yes` where operations monitoring collects it, `in the app only` where an application screen shows it and nothing
collects it, `only if configured` where it is sent only when a setting gives where to (an export address, an
exporter switched on by a setting), `development only` where only a tool used in development collects it (a
development dashboard the local host starts), not operations monitoring, `no` where nothing does (a metrics
endpoint no scrape configuration lists), or `unknown`; and `watched_source`, the collection configuration or screen
read, with its citation; for `only if
configured`, the setting by name, where it is set or found unset. Watched is never settled by reading the emitting
code. **Find where the export address is actually set**, beyond the files you were pointed at: the launch and host
configuration (launch profiles, the host or orchestrator that starts the services and passes them settings), the
environment the services run with (deployment manifests, container and environment files), and the application's
own settings files. Where no collection configuration is within reach, write `unknown` and
`no inventory reachable`; only `unknown` may rest on that. Read the other way: where `watched_source` cites a collection setting
that was read, the answer is `yes`, `no`, `only if configured` or `development only`, never `unknown`; `unknown`
on a cited setting says what was `not read` (a configuration repository out of reach). `flow_outputs.py --check`
fails the others. The page shows `watched` in an opened measure. Business measures count cases. No thresholds or targets unless a document or person states them, and
then only as that source states them.

**What shows the data, and what would send it on.** On every measure whose `exists` is `yes`, write
`instrumented_kind`: `code` where the application's own code writes what the measure is counted from (a log line, a
span, a metric, a table's schema), `built in` where it is a product's own status (a database server's, a message
broker's, the hosting platform's); and `instrumented_signature`, a few words a reader can find it by: the log line's
own words (`log line 'order placed'`), the span (`trace span on the charge call`), the metric's name, `table schema`,
or for `built in` the product's name. It is a cell, not a sentence: at most 60 characters. On every measure whose
`watched` is `yes`, `only if configured` or `development only`, write `exporter_name`, the configuration that sends
the data on by its usual name, with the product where the configuration names one (`OTLP exporter`, `Prometheus scrape`, `Log shipper (Fluentd)`), from `watched_source`. On every measure, write
`taken_at`: the subject id of the component the data comes from, the one whose code writes the line, span, metric or
table, or whose own status it is (`S02`). It can differ from `subject_id`, which says what the measure is about: a
measure of the flow, a stage or a step is about the case, but its data still comes from a component. Leave it blank
only where the data comes from outside the application (`taken_from` `another organisation's record`). Fill all four
per row from that row's own `source_ref`, `counted_at` and `watched_source`, never by walking the code again; leave
them blank where they do not apply. In `counted_at`, name a component by its `subjects.csv` name, its own name as
its code or deployment states it (`ordering-api log`), never another label for it. They say where a measure's data
would come from; none of them says the measure itself is built or counted anywhere: every measure here is a proposal.
`check_measures.py` (rule 8) fails a register with no such columns, a value missing where it applies or set where it
does not, a kind outside the two, a signature longer than 60 characters, and a `taken_at` that names no component.

**Every measure row says which flow it was proposed for**, in `for_flow`, by its `flows.csv` id: the flow whose
stage or step led this step to propose it, a part's measure included. It is who made the row, not where the
measure sits, so `flow` keeps its own meaning and stays blank on a part's measure. A part that a further flow also
measures gets a row of its own for that flow, with its own handle, and the finished flow's row stays as it is: each
flow's review of its measures, and its alerts, stand alone. `check_measures.py` fails a measure without it.

### The three mechanisms

**1. The coverage receipt**. Every element
of every start-set below is either **covered** by at least one candidate in `measures.csv` or **gapped**: a row in
`measure-gaps.csv` saying why no candidate is proposed, with its source. There is no third state. A gap is not a
measure, so it is never a `measures.csv` row with the measure left blank. `flow_outputs.py --check` recomputes the
receipt from the register, whichever stage it is run for, and fails on every element that is neither covered nor
gapped: of the whole flow in a run with no pick of how far each stage goes; otherwise of the flow and of the stages
picked to measure (a part shared with a measured stage included), and not at all when no stage is measured. A gap row with no `why` or no `source` does not count.

Each gap row also says its `kind`, one of four, chosen by what stops a candidate for this question:
`does not apply` (ruled out by design: the question cannot arise here, as when the stage lasts one request and no
case waits in it), `counted by` (folded into another measure, named by its id in `why`: `folded into M38:`),
`no record` (the code keeps nothing that could count it today; say what record it would need), or `not read` (not
assessed in this run, as for a flow set aside). A gap that points at a decision point asked elsewhere is not
`counted by`: that kind needs a measure. The map labels each gap from `kind`, never from the reason's wording, and
`run_status.py` counts the gaps by it, so `not read` is kept for what the run did not look at. `--check` fails on
a row with no `kind` or one not in the list, and on a `counted by` row whose `why` names no measure.

| Start-set | Element (`element` in measure-gaps.csv) | Question (`question`) | Covered by a candidate that is |
|---|---|---|---|
| The flow, where its `bound_in_code` is filled | its id (`F1`) | `the time limit` | of the flow (stage and process step blank), counted on cases, `business health`, form `cycle time` or `completion rate` |
| Every stage | its id (`ST2`) | `in the stage` | of the stage, counted on cases, `business health`, form `backlog`, marked `in the stage` in `receipt_question`: the cases in it now |
| | | `oldest's age` | the same, marked `oldest's age`: the age of the oldest case in it |
| | | `time through` | of the stage, counted on cases, `business health`, form `cycle time` or `completion rate`, marked `time through`: the time through |
| | | `past the time limit`, only where the stage's `bound_in_code` is filled | of the stage, counted on cases, `business health` or `business impact`, form `backlog`, marked `past the time limit`: the cases in it older than its time limit |
| Every process step that matters (item 3) | its process step id (`7`) | `did it happen` | of the process step, on its case subject, counted on cases, `business health` or `business impact`, with `did it happen` in `receipt_question` |
| | | `was its outcome right` | the same, with `was its outcome right` in `receipt_question` |
| Every operation (each `operation` in `participation.csv` of an application component that takes part in a process step, whatever its involvement) | the component's id and the operation (`S03 PATCH /api/applications/{id}`) | `application` | of the component, `application`, with the operation, written as participation writes it, in `operation` |
| A component whose row names no operation | its id (`S12`) | `application` | of the component, `application` |
| Every route an agent's own component serves (an `operation` on an agent's row written as a route) | the agent's id and the route (`S06 POST /chatclient`) | `application` | of the agent's component, `application`, with the route in `operation` |
| Every system component (`band` `technology`) that takes part in a process step, whatever its involvement | its id (`S08`) | `technology` | of the component, `technology` |
| Every external dependency of the application layer (`level` `external dependency`, `band` `application`: a partner's endpoint the flow posts to, a provider's API it calls) that takes part in a process step | its id (`S16`) | `application` | of the dependency, `application`, seen from the calling side (the caller's outgoing requests to it) |
| Every decision point: an agent with a tool its participation rows class `yes:` in `decision_point` (the rows of one tool, at several process steps, are one decision point) | the agent's id and the tool (`S04 uw_render_decision`); for a row naming no tool, `S04 at step 15` | each agent question in `method/agent-questions.csv` whose `status` is `provisional` and `grain` is `decision point` | of the agent, `agentic`, with that `agent_question` and the tool in `operation` (for a row naming no tool, that `step`) |
| Every reply relied on: an agent row classed `yes:` in `reply_decision_point`, one per agent and operation | the agent's id, `reply to` and the tool (`S04 reply to uw_render_decision`), or `reply on` and the route for an agent with no tool (`S03 reply on POST /`); a row naming no operation, `reply at step` and the step | the same agent questions | of the agent, `agentic`, with that `agent_question`, `reply` and the operation in `operation` (a row naming no operation: `reply` and that `step`) |
| Every model output a later call relies on: an agent's action in `agent-system.csv` classed `yes:` in `decision_point` | the agent's id and the action's id (`S03 AS2`) | the same agent questions | of the agent, `agentic`, with that `agent_question` and the action's id in `operation` |
| Every agent that performs or supports a process step, or whose `agent-system.csv` run serves one | its id (`S04`) | each run metric: `run duration`, `failed tool calls`, `tokens`, `refusals`, `fallbacks to a person` | of the agent, `agentic`, answering the agent question of grain `run` (`operating health`), with the metric in `receipt_question` |

An agent question marked `candidate` is not asked until the agentic layer settles it. A tool classed `no:` is not a
decision point, and its agent is still asked at the run.

**2. The expectation chain** (that question set, q15b). Every
expectation has a business candidate that would show whether it is met. The question set gives the reason: without
it, candidates default to *whatever the service's API behavior suggests rather than what stakeholders need to know*.
Here the expectations are the rows of `expectations.csv` (Step 9, the parties and their expectations) and each process step's `right_outcome`:

- **Each row of `expectations.csv`** is covered by a candidate at `business health` or `business impact`, of the
  flow, a stage or a process step, that names its id in `expectation`. Either business layer counts, which is broader than
  the question set's business health alone: whether a case's outcome was right is often counted at business impact.
  Read the row's `satisfied_when`, and name what one case would show if it did not hold. A tied measure whose
  `defect` says it counts nothing does not answer it: propose another, or gap it. An expectation no candidate names
  gets a `measure-gaps.csv` row: element its id (`e3`), question `expectation: indicator`, and its kind. Where
  nothing records what `satisfied_when` names, the kind is `no record`, and `why` says which record is missing.
- **Usually give each expectation at least one business health measure** (the cases that meet `satisfied_when`)
  **and at least one business impact measure** (the cases that fail it), or a gap for each with its kind. Several
  are fine. Consider tagging every business measure that counts against `satisfied_when`. A stage's exit-step
  "did it happen" count is a place to start the health side, but it matches only where the stage has one wanted
  exit: where the expectation also accepts other endings, it does not count what the expectation counts.
- **A business impact measure that guards an expectation counts the cases that fail its `satisfied_when`.** A case
  the condition counts as met never appears in it. Where cases ending some other way (cancelled, refunded) matter,
  count them in a measure of their own.
- **"Was its outcome right" is derived from the process step's `right_outcome`**: read that column, and name what one case
  would show if it did not hold (the state, the values it should carry). Where nothing records the values the right
  outcome names, the gap says which record is missing.

Name the measure for what it counts (below). The flow's `the time limit` and each stage's questions are asked
in mechanism 1, as the flow's and the stages' coverage; this mechanism adds no second gate on them.

**3. Signals per operation** (that question set, q40 to q43). Where
telemetry can tell a component's operations apart (a metric labelled by route or tool name, a log line naming the
handler), each operation gets its own application candidate, naming it in `operation`. Where it cannot, or one
candidate already answers for several, write the gap for each operation it folds in: `folded into M51:` and why.

**Kept from the kit, not from that practice:** the stage level, and the stage's exits read from its moves in place of a
"last step". **Not adopted:** that practice's targets, thresholds and authority, and its per-signal standing. Those
belong to choosing measures, which people do later. Nothing here is fixed: where the procedure misses an element
or asks a useless question, change it.

**Name a measure for what it counts.** A count of wrong outcomes is "Orders confirmed with an unknown item", never
"Stock confirmed rightly": a reader takes a rising count of a thing named "rightly" as good news.

A stage usually loses cases in three ways. Each is a question a measure answers; consider each, and where one would
break the expectation, a measure of it is a candidate to propose. Which of them to alert on is the stage kit's step "The failure modes, the alerts and the runbook for a stage"'s, "Alerting":

- **Cases wait too long**: the cases in the stage older than they should be (past its time limit, where the code
  sets one; otherwise past an age the operators set). Where a move out of a park stops, they pile
  up here.
- **Cases leave wrongly**: cases leaving by an alternative or exception ending the expectation does not want (failed
  back, cancelled because a part failed), or left stranded, counted against the cases that entered. A stage whose
  work never waits loses cases mostly this way. Say which record counts one event per case at those exits; if none
  does, the measure is `proposed` and names the record it needs. An ending the party wants
  (their own cancellation, a rule's refusal) is not a loss.
- **Cases leave with a wrong outcome**: the main ending, reached with the wrong values (a stale read, a wrong
  decision from a rules engine or a model). The process step measures of item 3, "was its outcome right", count it.
