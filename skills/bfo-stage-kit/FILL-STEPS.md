# Filling a register for one capability

For a language model drafting from the source material it is given. The run never stops to ask a person: what
the sources do not state, the model infers plausibly and labels `proposed:` with its basis, and a person confirms
or corrects those rows afterwards. The result is a filled register (the tables in
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
is never inferred: it is written only where a source states it (Step 3a).

## Before you start

1. Start the register with `python "<skill>/start_register.py" "<your-folder>"`, in a new folder named for the
   capability. It copies the CSV files in `register-template/` (not `REGISTER.md`), and refuses a folder that
   already holds a CSV file, so earlier work is never copied over. Where the workspace holds a register with its own
   `RUN.md` from this kit (one with the section *Earlier registers*), read the effect lines in the kit's
   `CHANGELOG.md` and recommend to the person the least work that brings it up to this kit: nothing, fills from
   each row's citation, or the re-walks those lines name. The person decides. As you
   do each step below, add a row to `how-made.csv`: what went in, which files came out, and who did it (a tool,
   a model drafting, a person confirming, or by hand). `RUN.md` from the same folder is the run's record of its
   phases: when the kit is run as a skill, the skill's `SKILL.md` says how it is written and kept.
2. **Gather what you will read**, and list it. Take every source the person pointed at, and what is in the
   workspace, and get each with your own tools. List each in `sources.csv` with pass `1`; `kind` is `code`,
   `document` (a page, a diagram, a process description, a runbook, a catalogue entry), `person` (notes, tickets,
   recorded answers) or `tool output`. In `note`, write which step below will use it. Keep the summary in
   `about.csv` → `sources_examined`, so a reader knows what "not assessed" covers. If the code has no
   version history, list it as the folder as found, with the date you read it. For code, write the repository's
   folder and the commit read in `repository` and `commit`, one row per repository. With more than one, open each
   as a folder of one workspace and **write every citation from the workspace root**, starting with the
   repository's folder (`orders-api/src/Orders.cs:12`), so the same file name in two repositories is not
   ambiguous; the check warns on a citation whose first folder is no listed repository. Cite a shared library at
   the version the service's own lockfile or build manifest names, and cite that line. Every repository the run
   uses, fetched ones included, is a folder of the open workspace (a multi-root workspace when there are several),
   never a temporary folder, because the environment's code tools reach only the open workspace. If you cannot add
   folders to the workspace yourself, stop: record in `RUN.md` the repositories and that the person must open them
   as one multi-root workspace and start again.

   What the method takes from each kind of source:

   | Source | What the method takes from it | Used in |
   |---|---|---|
   | Code, with its build and deployment definitions | The line that creates the case; states, moves, how each travels, what carries it, what it needs, timing and what happens if it does not happen; each part's repository; the configuration that runs | Before you start 4; Steps 1, 2, 5, 6 |
   | A business process description (a process page, a process diagram, a procedure) | Whom the flow serves and what each party expects of it; where the case starts and ends; what the party would recognise as done, which places stage cuts; a stated bound (an objective); what a right outcome is | Steps 1, 3, 3a, 4 |
   | Code: the text it shows a party (status messages, notifications, notices) and the rules it enforces | A party's expectation in the words the party is shown; an objective, where the shown text states a bound, or where an enforced rule states one and the code names the rule's authority; a party the code shows only as a persona, a role or a rule, labelled `proposed:` | Step 3a |
   | An architecture page or diagram | The deployables the flow runs through, and where each one's code is; a cross-check of the parts the walk found, and of component against external dependency (whether its code can be had); an outside service's own parts, one level | Steps 5, 6 |
   | A service catalogue or configuration database entry | A part's registered id, owner and responder, with the date true | Step 5 |
   | A runbook, a support or incident page | Owner, responder, escalation; how a failure shows and what is done about it | Steps 5, 11 |
   | A document saying what the organisation is able to do | The capability, named from the documents alone | Step 8, second route |
   | People's notes, tickets, recorded answers | Owners, responders, parties with their expectations and objectives, and volumes no other source states | Steps 3, 3a, 5; "When something new arrives" |

   A source is read only far enough here to place it in this table; the steps read it in full.

   Read backwards, the same table says which kind of source would settle what the run had to propose. The report's
   *What would make this map fuller* counts the `proposed:` or blank cells this way:

   | `proposed:` or blank in | Settled by | From the table's row |
   |---|---|---|
   | `stages.csv` → `source` (a cut) | A business process description; a person | Step 3 |
   | `stages.csv` and `flows.csv` → `bound_in_code`, where filled | The code or its configuration: the line that sets the timer, deadline or overdue rule | Step 3 |
   | `expectations.csv` → `party`, `expectation`, `satisfied_when`; `objective` blank | A business process description; the text the business shows the party; a person | Step 3a |
   | `steps.csv` → `right_outcome` | A business process description; a person | Step 4 |
   | `subjects.csv` → `owner`, `responder`, `application_id` | A catalogue or configuration database entry; a runbook; a person | Step 5 |
   | `stages.csv` → `arrivals_per_period` and other volumes | The operators (never derived) | Step 3 |
   | `about.csv` → `what_it_is` (configuration) | Deployment definitions | Before you start 4 |
   | `capabilities.csv` route 2 missing | A document saying what the organisation does | Step 8 |
   | A part with `repository` blank, an external dependency with no source | Its repository or its owner's documents | Step 6; item 5 |

3. Use every code-intelligence tool the environment offers over the workspace's repositories: a call graph and its
   business logic for Step 2's walk; a cross-repository trace for Step 6's dependencies; failure-handling analysis
   (timeouts, retries, circuit breakers) for Step 11's failure modes; unreferenced code, written up as a finding.
   Each tool's output is a source in `sources.csv` like any other; what the stages are, what the case is and what to
   alert on stay the method's judgement. If a code reader is available (the design-for-operations fact extractor, or
   your platform's equivalent), run it over the repository with a service map you write: one entry per deployable. It gives calls between those
   deployables and, where its rules cover the language, emission sites (logs, metrics, spans), each with a file and
   line. Its reach differs by language and by kind of fact, so read in its own documentation what it covers: a
   language it cannot parse, or a kind it has no rule for, yields nothing, and nothing is not absence. What it did
   not find is not looked for: read the services and deployment files it found nothing in, and cite what you read.
4. Name the configuration you describe: which optional components are switched on. Describe the one that runs
   in production, or, where several do, the one that carries the capability's AI agent. Write it in
   `about.csv` → `what_it_is`. If no source says which runs in production, describe the fullest one the
   repository defines, and write `proposed:` and why.
5. **A call that leaves the workspace.** When the walk (Step 2) meets a call to a deployable whose code is not in
   the workspace, name it from what the call shows: an address, a client package, a queue or topic name, an image.
   If its repository or documents can be reached, get them: a source found during the first run is pass `1`, not a
   new pass, and it goes into a folder of the workspace (item 2). Fetch it only with access the person already has, and read-only: never request access, enter credentials, or change anything at the source. Record every fetched source in `RUN.md` *Sources* with what referenced it and why. If the person's request says to use only the sources they name, do not fetch: list it under *still missing* instead. With its code, it is a component (Step 5), whatever its application id or owning team, and you read the
   operations this flow calls and what those call. If its code cannot be had, it is still a part (Step 5), cited by
   the line that identified it, with `repository` blank: an external dependency, and its measures are gapped with
   the reason. List it under *still missing* in `RUN.md`.
   **Check the repository set is complete**, without being asked: (a) for every reference the code makes that no
   folder in the workspace answers (a host or service name, a client package, a queue or topic, an image, a
   configuration key, a URL), search the code host with the person's own access (repository search, code search
   across the organisation) for the repository behind it; (b) search the other way too, for repositories that call,
   consume from or deploy this flow's services; (c) repeat on what the new repositories reference, until a pass finds
   nothing new. Record each repository found in `sources.csv` with the search that found it, and add it to the
   workspace as a further folder, read-only; what is found and cannot be had goes under *still missing*. `RUN.md`'s
   Phase 0 line answers "Is this the complete set of repositories?" with that evidence, and Phase 0 is not done while
   a reference is unresolved and unsearched. If the person's request says to use only the sources they name, do not
   search: list each unresolved reference under *still missing* instead.

## Step 1. Declare the frame (*Assigning* Step 0; *Rules*, Rule 0)

Four declarations, written before anything else and never inferred silently:

| Declaration | Where it goes | The rule |
|---|---|---|
| The case | `flows.csv` → `case` | One individual business item: one order, one application, one appointment. Never a system, a team, a batch, a request or a basket. A flow has one kind of case. Write its name only; where it is stored and what identifies it go in `case_identifier` |
| Whom it serves | `flows.csv` → `customer` | The party counting on the outcome, the one whose outcome ends the flow: its role name only; a citation for it goes in the row's `source`. Every other party the flow serves or binds is named in Step 3a |
| The starting event | `flows.csv` → `starts_at` | **The act that first creates the case's record.** Cite the line that creates it. This is also where the party begins counting on an outcome: before it there is nothing for them to wait on |
| The ending outcome | `flows.csv` → `ends_at` | Where the party has what they were waiting for, or definitively does not. Name both endings. **The flow runs to that outcome even where the code stops sooner:** an order is delivered, not "Shipped"; the stretch after the last state the system records is added by the reference-model check in Step 3, drawn as not assessed |

`flows.csv` → `bound_in_code` is optional: fill it only where the application's code sets its own timer, deadline
or overdue rule for one case, end to end, cited as for a stage's (Step 3), and leave it empty otherwise. A limit a
source states is an objective (Step 3a). The four declarations and `delivers` (Step 8) are **required** for the view
*How a case moves end to end*; whom it serves is led by the parties' expectations (Step 3a).

**Everything before the case exists belongs to another flow.** Browsing, filling a basket, signing in, filling
in a form: real work, and set aside for this one. Write each in `set-aside.csv` with kind `other flow` and the
evidence, so a reader sees it was looked at. If the business would call something before the record its start,
say so in that row; it is a finding about where the record is created, not a stage of this flow. **Each piece of
work set aside as `other flow` is also a row in `flows.csv` now**, with its own case and no stages: the capability
carries it, and it is walked separately (Step 8).

If several kinds of case are plausible, name them, pick one, say why. If the source holds no case at all,
stop: draft the capability alone and say the rest would be fabricated.

`case_identifier`: the field that names one case, and every place it is lost. Read the code for it.

## Step 2. Build the case's lifecycle (*Assigning* Steps 1 and 4)

Walk one case from the line that creates it to each ending, through the code, and write `lifecycle.csv`: **one
row per move**, the act that takes the case from one state to the next. Walk the case, not the code's
structure: a call graph shows every hop and hides every wait.

For each move, record:

- `from_state` and `to_state`: the case's states, named as the system records them where it does (a status
  value, a table, a flag) and cited. Where the system records no state but the case plainly waits, name the
  state in words and write `implicit:`. The first row's `from_state` is `(none)`: it is the creation move.
- `from_kind`: whether the case **parks** in `from_state` (`park`) or is still inside an act (`in act`).
  **A case parks when nothing is progressing it and the next move needs a trigger that is not already in
  motion**: a timer or schedule, a person, an outside party, or the customer. A message already sent to a
  consumer that will act on it without any further trigger is the act still working, like a call out and back:
  `in act`. A poll that picks cases up on a schedule is a timer: the case is parked until it runs. Write which
  trigger in `park_because`.
- `move`: the act, in the case's terms ("stock is confirmed for the order"), never the performer.
- `path`: `main`, `alternative` (another ending the design allows: rejected, cancelled) or `exception`.
- `travels_by`: how the move reaches the case: `in-process`, `call` (HTTP, gRPC), `message` (name the event and
  the broker), `outbox` (written with the state, relayed later), `poll` (a worker on a schedule), `timer`,
  `person`. A move that takes several hops lists them in order, `;` separated. **Every hop has its body in
  brackets**, saying who does what (`person (the underwriter opens the file and approves it)`), never a bare
  `person;`: the first hop's body is what *How this process step is carried out* prints as the process step's trigger, so it is
  required.
- `carried_by`: the parts that carry the act out. `needs`: the stores, brokers and outside services the move
  cannot complete without. **Write each part as its subject id and name (`S04 Ordering API`)**, giving it the id now
  that becomes its `subjects.csv` row in Step 5. Every output is generated from these two columns, so a part named
  here and nowhere in `subjects.csv` fails the check.
- `started_by` (optional): on a move that can happen at any time while the case is in a stage (a cancel, a
  withdrawal), who starts it, cited: the flow's customer, a role, an outside party, `timer`, or `the software`.
  The stage's drawing names the starter; left blank, it reads as a condition whose starter is not recorded.
- `timing`: what the code assumes about time for this move (a grace period, a poll interval, a timeout, a retry
  schedule), cited. Required for *How this process step is carried out*: where the code sets none, write that with its
  citation ("no timeout is set on the call") or gap it `no record`; a person's act with no clock is gapped
  `does not apply`. **A retry or timeout counts only where the code applies it:**
  read the call site, not only the setting (a policy configured but wrapped around the wrong call never fires).
- `if_not`: what happens to the case if the move does not happen: retried by what, until when; left in
  `from_state` with nothing to move it; lost; failed back to the party. Cite it. This is the summary; Step 11 reads
  every hop's failure modes one by one, and where that reading finds the summary wrong, correct it here.
- `recovery`: `moves on`, `stranded`, `not created` or blank, as in step-impact.csv (Step 10). `if_not` is
  required for *How this process step is carried out*, and `recovery` beside it wherever the move can fail.
- `irreversible`: `yes` where the move cannot be undone (money taken, goods shipped, a filing made), and `no`
  otherwise, never blank: *How a case moves through this stage* reads a blank as not looked at.

Parallel moves get `parallel with <move>` in `order_note`; a move back to an earlier state gets `loops to
<state>`. Exceptions the code does not handle are written as `if_not`, not invented as moves. **A failure the code
does handle by telling the party** (an error page, a refusal returned to the caller) is a move: path
`exception`, into an ending named for it (`implicit: order failed back, shopper told`). Every way a case can leave
its stage then has a row, and a process step (Step 4).

**An act that changes no state of the case** (emptying a basket, sending an email) is still a row, with `to_state`
the same as `from_state`. Its `from_state` is the earliest state it happens in: if it runs inside the same request
or transaction as another move, it takes that move's `from_state`, and so sits in that move's stage. Nothing waits
on it, so it never opens or closes a stage.

**A move that can leave from several states** (a cancellation allowed until payment) is one row per state it can
leave from, each cited to the guard that allows it.

## Step 3. Cut the stages from the lifecycle (*Assigning* Step 4)

**Draft the stages by judgment and say what each cut rests on.** A stage ends in a value item for the party in
`customer`: something they would recognise as done (*Assigning*, Step 4). Consider the parks, the
`irreversible` moves, a status the business uses, the domain's standard process and the documents. None of them
forces or forbids a boundary. Do not cut by service, sub-agent, deployable, a status the system exposes, or
message.

- Stage 1 runs from the starting event. A stage holds its entry state and the moves out of it.
- `entry`: the state the case is in when it enters. `exit`: the state it is in when it leaves (the next stage's
  entry, or an ending). Both are states read off the lifecycle. In `source`, cite the rows and what the cut rests
  on, or write `proposed:` with the reason.
- Name each stage for what it achieves for the case, verb first, two or three words. The state at the boundary
  is the exit criterion, not the name.
- `bound_in_code` (optional): the code's own time limit for the stage, filled only where the code sets one. Few
  applications do. Where the lifecycle's `timing` for the stage's moves shows a timer, a deadline or an overdue rule,
  write `proposed:` and the limit, cited. Otherwise leave the cell empty: never `none assumed`, and no gap is owed.
  **A bound a document or a person states, or one the business shows the party, never goes here**: it is
  an objective, written in Step 3a in `expectations.csv` → `objective`. Where the code's limit and a stated
  objective disagree (the code marks a case overdue after 5 days, and the customer is told "1-2 weeks"), keep both:
  neither is corrected to the other, and the stage card shows the two side by side as a finding. The parties'
  expectations (Step 3a) are the stage card's main content; *How a case moves through this stage* also needs the
  entry, the main exit and what is at stake (Step 10). A stage with no alternative or exception
  exit is gapped `does not apply` for its other outcomes.
- `arrivals_per_period`: `not stated: measured by the operators`, unless they give it.
- Do not merge or split to reach a count.

**Then check the cut against the domain's reference model** (APQC's process classification, SCOR, the domain's
standard process), from the starting event to the ending only. A stretch the reference model expects inside
that frame that no lifecycle row carries is added as a stage or process step with no participation, drawn as not
assessed. A stretch the reference model puts before the case exists is set aside (Step 1).

## Step 3a. Name the parties and their expectations

Numbered 3a so that the steps after it keep their numbers; in `how-made.csv` its `step` is `3a`.

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
stage has at least one expectation, the customer's included: the flow card's *Serves* and the stage card read them.

**Expectations come before alerts.** Usually write each expectation from what a party is told or a source states,
before any alert is drafted. An alert then names the expectation it guards (Step 9); the expectation is not written
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
(Step 3), and `objective` stays blank.

**Not found is not absent.** A party inferred from the rules the code enforces was read only as far as the code
goes. Write in that row's `source`: `only the obligations this code enforces were read`. Obligations the code does
not enforce were not looked for.

**The code's limit and the objective stay apart.** `bound_in_code` is what the application assumes; `objective` is
what a party has been told or a rule states. Where they disagree, both are kept, and the stage card shows the two
as a finding (Step 3).

## Step 4. Write the process steps from the moves (*Assigning* Step 5; *Rules*, Rule 0)

**Each process step is one move, or several moves with no park between them that make one outcome the business would
recognise.** No park between moves is needed to merge them, and is not enough: work that never waits is still
several process steps where it makes several outcomes the business would recognise. Hops between components inside one
outcome are one process step: they are mechanism, recorded in Step 6.

- **Write a stage's process steps in `steps.csv` in the order they run.** The drawings number and chain them in that
  order where the lifecycle does not chain them itself.
- Name the process step as its outcome, without its performer: "Stock is confirmed for the order", not "Catalog API
  confirms stock", never "POST /items returns 201".
- **Every stage's last process step is the move that takes the case out of it**, into the next stage's entry or an
  ending. One process step per way out: the main move, and each alternative or exception ending. A stage with no process step
  whose `to_state` is its exit is cut wrong: go back to Step 2.
- `right_outcome`: what a right outcome is for one case, stated or `proposed:` (the state the case should be in
  after it, with the values it should carry). Required for *How this process step is carried out*.
- A process step carried only in part gets `qualifier` `partial: <what is missing>`; one carried by a stand-in (a
  hard-coded value, a simulated call) gets `stub: <what stands in>`. A process step nothing carries stays, with no
  participation rows.
- Write the lifecycle row ids each process step comes from in `source`, with the code citation. They are required: a
  process step that cites no `L..` move has nothing in *How this process step is carried out*.

## Step 5. List the parts from the lifecycle (*Assigning* Step 6; *Rules*, Rules 0 and 2)

Every part named in `carried_by` or `needs` gets one `element` row in `subjects.csv`. Nothing else does.

- **Component or external dependency** is whether its code can be had: `level` `component` for any deployable the
  flow's process steps run through whose code the run can get, whatever its application id, repository or owning team;
  `external dependency` for one whose code it cannot get (a vendor, a third-party or software-as-a-service
  provider, a repository the run has no access to), drawn and measured from the calling side, and it can still
  perform a process step. Not the company boundary, not who owns it, and not whether it is open source. **Depth is bounded
  by the flow:** inside a component, read the operations this flow calls and what those operations call, not the
  whole service. A shared service many flows use adds only the operations this flow uses.
- **Application component or system component** is its layer, in `band`. Services, workers, front ends and AI
  agents are application components: `band` `application`. **Databases, caches, message brokers, search
  indexes, file stores, hosts and runtimes, and platform services are system components: `band` `technology`**, even when the application owns
  them. A system component is measured with its kind's set at the technology layer, never as an application
  component. `part_kind` from `method/part-kinds.csv` decides the set; an AI agent is a component with
  `part_kind` `LLM agent`.
- **A part with no process step it performs or supports is set aside**, in `set-aside.csv` with kind `out of scope part`
  and the evidence that named it: monitoring, platform tooling, a service no move uses. It is not deleted and not
  left out silently.
- A job that handles many cases per run (a polling worker, a nightly batch) is a component; its runs are its own
  measure, shown under the cases it failed to move.
- `carries_case_id` on every part the case passes through: `yes:`, `partly:` or `no:`, with where it is carried
  or lost (*Rules*, Rule 2).
- A front end served from inside another deployable is still its own component; say where it is deployed in
  `source`.
- A person who carries out a move: a `person` row, no level. It is the method's set-aside role, bound to its process step.
- `application_id`: the name the component is registered under in the organisation's configuration database, from that
  record; blank where no source states one. `repository`, filled for every component, never left blank: the code
  repository it is built from, from its build or deployment definition, with the path inside it where one repository builds several components; `not built here:`
  and the image for a component run from someone else's image. Shared infrastructure a parent component's deployment
  provisions (a database, a cache, a broker) is a `technology` component whose `repository` is the repository that
  defines it, with the path to the definition (`repo: path`). Something not separately built, such as an in-process
  sub-agent, is not a component, since a component is a deployable: it is an agent part inside its parent
  component's run, in `agent-system.csv` (Step 7), not a `subjects.csv` row. The one blank the check accepts is a
  `technology` component no repository defines (a platform service provisioned elsewhere), whose `source` says no
  repository defines it and where it was looked for.
- `owner` and `responder`: from a source that states them, with the date it was true; otherwise inferred from what
  the sources show (who builds and deploys the part) and written `proposed:` with that basis. They are counted,
  never required: fill them when known, and the run is not refused without them.
- `purpose`, on every component and external dependency: what this part does in this flow, in one sentence, cited.
  Required for *Inside this part*.

## Step 6. Record who carries out each process step

For every process step, in `participation.csv`, from the lifecycle rows it came from: each part in `carried_by`
**performs** it; each part in `needs` **supports** it (the process step blocks or goes wrong without it, including a
database constraint that enforces the process step's rule). The part that carries the move out of a stage performs that
stage's last process step. Every part in `carried_by` performs; none leads. The generated outputs name all of them, so the
part that changes the case's state and the part that decides (a stock checker, a payment service) are both shown.
Where a person makes the move through a route or screen, its performers are whoever the code lets make it, each a
`person` part in `carried_by` (Step 5): a named role, where a guard names roles (a role check, a permission
check, an admin path); `anyone signed in`, where the guard asks only for a sign-in; `anyone, the code checks no
identity`, where there is no guard. Cite the guard, or for its absence the route's declaration and the security
configuration you looked for and did not find. A move whose guard names roles but whose performers are not on
record (no source says who holds the roles, or which of them made the move) gets a `measure-gaps.csv` row on its
process step, question `step: trigger`, kind `no record`, citing the guard; it is never left blank. `records` (only reads or writes the process step's trace) may be added for a part that also performs
or supports some process step; a part whose only involvement is `records` is set aside (Step 5). Write the activity in
a few words with the file and line in brackets. Name the `operation` that does the process step: the agent tool, HTTP route or message handler
the part offers, read from its declaration (the tool's name, the route's method and path). Where the cited line
is not itself a declaration (a status value, a shared service function), follow the move's `travels_by` to what the
caller invokes. The operation is what a caller calls, not the code structure behind it, so it survives a refactor. A part that shows the process step's result to the party performs the
process step whose outcome is that the party sees it. Each component's operations are required for *Inside this part*; a
data store or external dependency, which offers none, is gapped `does not apply`.

Then add an `interaction` row (`kind` relationship) in `subjects.csv` for each hop in `travels_by`: `from_id`,
`to_id`, and the process steps it happens within in `step_hint`. A call that both reads and writes is two rows,
one per direction of data, so the drawing labels each message from its own row. `step_hint` lists only the process steps the call
is made in for each case; a call made at startup is not hinted to any process step. Where the code shows which of the calling part's operations
make the call (the route or tool whose handler calls it), name them in `operation`, as `participation.csv` names
them, and cite the line; leave it blank where the call is made once for a session or a connection. `band` `application` between components, `technology`
for a part's call to the store or broker it runs on. A message published through a broker is two hops: the
publisher to the broker, the broker to the consumer. Number the hops of one process step in `sequence` in the order they
happen, only for calls made once, one after another, on one way. Leave `sequence` blank, and say why in the
citation, for a call repeated per item, made in parallel, not waited for, or made only on one branch. These rows
are each part's dependencies, required for *Inside this part*; a part that calls nothing is gapped `does not
apply`, so the view can tell it from one not looked at.

**How far to go into an outside service** depends on what you can get for it: nothing beyond its address, it
stays one external dependency seen from the calling side; its code, it is a component (Step 5), read for the
operations this flow calls and what those call; only its documents, add the parts your calls reach as
`external dependency` rows with `part_of` set to the service (one level only); its owner has a map, put the
address in `map_link`.

## Step 7. Describe each AI agent as its own system

For each `LLM agent` component, add a block to `agent-system.csv`. If the capability has none, leave it with its
header only and write a `how-made.csv` row naming where you looked.

1. **The run:** one decision for one case, or one request answered. Name the process steps it serves.
2. **Its steps:** what one run does (take the request, decide the next move, call a tool, retrieve, write the
   answer, check the answer).
3. **Its parts:** the sequencing code; the decider (the model, its prompt and its rules); its tools; what it
   retrieves from; the checks that stop an answer outside policy. Link each to the subject ids that carry it. A
   part looked for and not found gets a row with a blank `subject_id`, and `what_it_is` says where you looked.
4. **Its dependencies:** the model provider and the systems its tools call. Fill `uses` on each part.

An agent's conversation is a flow of its own only when it is one case's path the business would name, with its
own start and end; otherwise the parts it uses carry process steps of an existing flow, recorded as participation rows
(Step 6) like any other part's.

## Step 8. Name the capability, twice (*Assigning* Steps 2 and 7)

1. **From the walk:** what the whole path is for, what the business is thereby able to do, named apart from how
   it is built. The narrowest ability this flow delivers.
2. **From the sources, in a pass that has not seen the walk:** what the documents say the organisation is able
   to do (a separate session or subagent given only the documents).

Write `capabilities.csv`: one row per capability, with both routes in `basis`. If they agree, say both
produced it. If they disagree, keep both rows and say so; do not smooth them into one. A capability the sources
name that the walk does not deliver is kept, delivered by no flow. Fill `flows.csv` → `delivers`.

If an AI agent serves several flows, the register covers the lowest capability that holds all of them. List the
other flows the capability carries in `flows.csv`; each is its own frame and walk, and a flow not yet walked has
no stages.

## Step 9. Propose the measures, question first (*Rules*, the form and Rule 1)

This step proposes **candidate** measures: what could show whether the capability works. It does not choose which
are wanted, and it sets no targets or thresholds. Choosing measures and making them service level indicators with
objectives is done later, by people. The candidates are accounted for with three mechanisms adapted from a service onboarding practice, whose question set is published in the same collection as this
kit (`packages/observability-practice/the-instrument-sud-v2.yaml`), so that a thin
stage or an unmeasured agent step is caught rather than left unnoticed.

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
   agent serves (its participation rows, and its `agent-system.csv` run and operations). Mark each process step measure in
   `receipt_question` with the question it answers.
4. **Each part, its kind's set** (`method/part-kinds.csv`), at its layer: `application` for an application
   component, `technology` for a system component. An external dependency is asked the same sets from the
   calling side. An application component is asked **per operation** (mechanism 3). Every component that takes part
   in a process step is asked, whatever its involvement: a store whose only rows are `records` (a basket store a restart
   empties) is asked its set like one that performs. An AI agent is read at two grains (below): its judgment at
   each **decision point**, and its operation at its **runs**. **An agent whose own component also serves a route**
   (the agent is the deployable, and a caller reaches it by an HTTP route) is asked both: the agent questions, and
   the application set for each route on its rows, keyed like any operation (`S06 POST /chatclient`). Hosting an
   agent does not take the component's route out of the application layer. The receipt tells a route from a tool
   by how `operation` is written, a method and a path (`POST /chatclient`) or `route` and a pattern; a handler of
   another kind on an agent's row (a message consumer, a gRPC method) is not recognised yet, so write its
   application candidate or gap by hand and say so in `why`.

### The agentic layer: the decision point and the run

**Class each tool first.** On every participation row of an agent, write `decision_point`. A tool call is a
decision point, `yes:`, when the agent chooses a value that becomes the case's outcome or a person's basis for
deciding it: a recommendation, a decision type, a condition's text, the inputs to a risk computation. A call that
only records what a person stated or asked for is an action, `no:`: entering the borrower's details, acknowledging
a disclosure. Class it by reading what the tool's arguments carry, and cite the signature. A tool that computes by
fixed rules is a decision point only through the arguments the agent chose to pass it; say which. One agent's tool
is classed one way on every row. The check fails on an agent row not classed, and on a tool classed both ways.

**A tool whose class depends on the conversation is a decision point.** The same call can record an item the
person named, or choose one the person only described (an add-to-basket call given a product's name against one
given "something warm for winter"; an add-pet call with the owner the person named against the owner the model
picked from a list). One class per row stays: write `yes:`, and the reason says **when** the call carries the
agent's choice. Where telemetry can tell the two kinds of call apart, the candidates count only the judged calls,
and say how in `counted_how`. Where it cannot, the reason says so, and every call is counted. The receipt cannot
split the two; the reason is where the difference is kept.

**Then class each reply.** The agent's reply to a person is a decision point when the person relies on it: it
reports or explains a result, such as a recommendation, a risk assessment or a check's outcome.
Its operation is the agent's turn, not a tool, so a tool computed by fixed rules (classed `no:`) can still be
reported by a reply that is a decision point. On the agent's row for that process step, write `reply_decision_point`:
`yes:` where the person relies on the reply, `no:` where it only confirms what the person asked, asks for more, or
replies to no person at that process step, and why, citing the prompt or the code that hands the tool's result to the
model. The check fails on an agent row whose reply is not classed. Each reply classed `yes:` is a decision point keyed, like a tool's, by the agent
and the operation whose result it reports, element `S04 reply to uw_render_decision`, listing every process step it spans: a
judge sampling the agent's replies after that operation is one measure whichever of those process steps the case is in. Its
candidates name `reply` and the operation in `operation` (`reply; uw_render_decision`). A row naming no tool keys its
reply by its process step (`S04 reply at step 17`), with `reply` in `operation` and the process step in `step`. **An agent with no
tools** still has its reply as a decision point, keyed by the agent and the route that runs it: element
`S03 reply on POST /`, candidates naming `reply; POST /`. The receipt writes `reply on` where the row's operation
is a route and `reply to` where it is a tool.

**A model output a later call relies on is its own decision point.** Where the agent's chain writes something
with one model call and a later call decides from it (a description of a room written from a photo, then fed to
the call that chooses products), that first output is a judgment no tool or reply holds. Class it on the operation row
of `agent-system.csv` that makes the call, in `decision_point`: `yes:` and why, citing the line that feeds it on.
It is keyed by the agent and its place in the chain, element `S03 AS2`, and asked the same questions; its
candidates name the process step's id in `operation` (`AS2`). Only a process step row classed `yes:` is asked. Do not class a process step
whose output a tool's or a reply's decision point already holds: the model's choice of a tool's arguments is that
tool's decision point. Grounding comes first:
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

**At the run**, every agent, whatever its tools are classed: the agent question of grain `run`, `operations`. One
run is one invocation of the agent: a request in, the model and tool calls it makes, an answer out. Each of five
metrics is its own element, covered by an `agentic` measure of the agent with `agent_question` `operations` marked
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

On every measure, write in `taken_from` the kind of record it is counted from, one of the eleven `REGISTER.md` lists: where
`exists` is `yes`, the kind of the cited line; on a proposed measure, where it would be taken from, decided from what
the measure counts and never from the tools at hand. For how a measure could be taken from each kind, and what each
cannot do, see the implementing-a-measure skill, §2. Name the kind of the cited line itself, never of what it
reports on: a part's own health check is the kind of record that runs it (a probe or a metric), never the case's own
record or configuration.

**A measure can be emitted and never collected.** On every measure whose `exists` is `yes`, write `watched`:
`yes` where operations monitoring collects it, `in the app only` where an application screen shows it and nothing
collects it, `no` where nothing does (a metrics endpoint no scrape configuration lists), or `unknown`; and
`watched_source`, the collection configuration or screen read, with its citation. Watched is never settled by reading the
emitting code. Where no collection configuration is within reach, write `unknown` and `no inventory reachable`; only
`unknown` may rest on that. The page shows `watched` in an opened measure. Business measures count cases. No thresholds or targets unless a document or person states them, and
then only as that source states them.

### The three mechanisms

**1. The coverage receipt**. Every element
of every start-set below is either **covered** by at least one candidate in `measures.csv` or **gapped**: a row in
`measure-gaps.csv` saying why no candidate is proposed, with its source. There is no third state. A gap is not a
measure, so it is never a `measures.csv` row with the measure left blank. `flow_outputs.py --check` recomputes the
receipt from the register for the whole flow, whichever stage it is run for, and fails on every element that is
neither covered nor gapped. A gap row with no `why` or no `source` does not count.

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
| Every decision point: an agent with a tool its participation rows class `yes:` in `decision_point` (the rows of one tool, at several process steps, are one decision point) | the agent's id and the tool (`S04 uw_render_decision`); for a row naming no tool, `S04 at step 15` | each agent question in `method/agent-questions.csv` whose `status` is `provisional` and `grain` is `decision point` | of the agent, `agentic`, with that `agent_question` and the tool in `operation` (for a row naming no tool, that `step`) |
| Every reply relied on: an agent row classed `yes:` in `reply_decision_point`, one per agent and operation | the agent's id, `reply to` and the tool (`S04 reply to uw_render_decision`), or `reply on` and the route for an agent with no tool (`S03 reply on POST /`); a row naming no operation, `reply at step` and the step | the same agent questions | of the agent, `agentic`, with that `agent_question`, `reply` and the operation in `operation` (a row naming no operation: `reply` and that `step`) |
| Every model output a later call relies on: an agent's operation in `agent-system.csv` classed `yes:` in `decision_point` | the agent's id and the operation's id (`S03 AS2`) | the same agent questions | of the agent, `agentic`, with that `agent_question` and the operation's id in `operation` |
| Every agent that performs or supports a process step, or whose `agent-system.csv` run serves one | its id (`S04`) | each run metric: `run duration`, `failed tool calls`, `tokens`, `refusals`, `fallbacks to a person` | of the agent, `agentic`, answering the agent question of grain `run` (`operations`), with the metric in `receipt_question` |

An agent question marked `candidate` is not asked until the agentic layer settles it. A tool classed `no:` is not a
decision point, and its agent is still asked at the run.

**2. The expectation chain** (that question set, q15b). Every
expectation has a business candidate that would show whether it is met. The question set gives the reason: without
it, candidates default to *whatever the service's API behavior suggests rather than what stakeholders need to know*.
Here the expectations are the rows of `expectations.csv` (Step 3a) and each process step's `right_outcome`:

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

**Draft alerts as proposals, and say what each rests on.** Each names the expectation it guards. Whether to alert,
and on what, at any level (the flow, a stage, a process step or a part), is the team's decision; the register only drafts.
Mark each measure you propose for alerting in `alert`, as `yes:` and its basis, required for the alert's runbook
entry, and **name the expectation it guards by id in `expectation`** (Step 3a). `--check` fails on an alerting
measure whose `expectation` is blank or names an id `expectations.csv` does not hold, at whatever level it is. The
alert is drafted on every stage its measure reaches: a process step's stage, every stage of a flow, each stage a part
serves. The runbook generator works a stage's tests for each of them, which fits best a stage's measures counted
on cases (Step 11). A stage no alert reaches gets no alert page, and its runbook says so; `--check` notes it and
does not fail. The measures, the alerts and the runbook are generated from that column, so they cannot disagree.
Whether an alert pages a person, opens a ticket or shows on a dashboard is the operators' decision, not the
register's.

A stage usually loses cases in three ways. Consider each; where one would break the expectation, a measure of it
is a candidate to propose:

- **Cases wait too long**: the cases in the stage older than they should be (past its time limit, where the code
  sets one; otherwise past an age the operators set). Where a move out of a park stops, they pile
  up here.
- **Cases leave wrongly**: cases leaving by an alternative or exception ending the expectation does not want (failed
  back, cancelled because a part failed), or left stranded, counted against the cases that entered. A stage whose
  work never waits loses cases mostly this way. Say which record counts one event per case at those exits; if none
  does, the measure is `proposed` and names the record it needs. **`counted_moves` lists the moves (`L..`) the
  cases leave by**, by id: the alert's runbook entry works the tests of the state those moves leave from. An ending the party wants
  (their own cancellation, a rule's refusal) is not a loss.
- **Cases leave with a wrong outcome**: the main ending, reached with the wrong values (a stale read, a wrong
  decision from a rules engine or a model). The process step measures of item 3, "was its outcome right", count it. Where a record
  shows the wrong outcome per case, one may be proposed for alerting.

A measure not proposed for alerting is still read by the runbook's tests. Where the stage proposes alerts of its own,
the check warns where its moves show a kind of loss no proposed measure counts. Consider proposing one, or say in the
basis why not: a warning whose reason the basis gives stands, and does not stop the outputs being written. Only
errors do.

## Step 10. Record what a failure costs (*Rules*, Rule 3)

For each lifecycle move whose `if_not` hurts the case, a `step-impact.csv` row on the process step it belongs to: the
category from `method/impact.csv`, the unit counted in cases, and `recovery` copied from the lifecycle. A case
acknowledged to the party and then lost fits no recovery value: leave `recovery` blank and begin `note` with
`lost after acknowledgement:` and the evidence. In `case-attributes.csv`, what is at stake in one case:
`what_is_at_stake` is required for *How a case moves through this stage*.

## Step 11. The failure modes, the alerts and the runbook for a stage (`reference/runbook-model.md`, "How to write one")

For each stage. The runbook is written for every stage, and the alert page for every stage an alert reaches, at
whatever level the alert is drafted (Step 9). The alerts and the runbook are **generated**, never written: what you
write is the worksheet they are generated from.

1. **The expectations** are the stage's rows in `expectations.csv` (Step 3a), each alert naming the one it guards
   in `expectation`, with the stage's time limit in the code where the code sets one (Step 3) and the right outcome of each process step that takes a case out of
   the stage. **The alerts** fire on the measures marked in `alert` (Step 9). **The runbook has one short entry per
   alert**, which that alert's runbook link points at, **and one shared section for the stage**: the stage on one
   page, what is at stake, every test written once with the alerts that use it, the causes the alerts share, and
   restore, close and escalate. What the generator puts in each entry, from what you write:
   - **What fired**: the measure and its basis.
   - **Its cases and window**: for a measure of cases waiting, the cases past the bound, read from when the oldest of
     them entered the stage (the count lags its cause by up to the bound); for a measure of cases leaving, the cases
     that left by the moves its `counted_moves` names, read from when the earliest of them entered the stage.
     **`counted_moves` lists, by id and separated by `;`, the moves whose cases the alert counts**, and only
     those. The basis is free text: a move it names, to say the alert does not count it or why, is explanation and
     is never read as counted. `--check` fails on an alert of cases leaving whose `counted_moves` is empty, and on
     one that names an id not in `lifecycle.csv` or not a move of the stage; an alert of cases waiting leaves it blank. Cases that left by the
     move that creates the case, from `(none)`, were created: its `not created` recovery says what happens when the
     move fails, so an alert naming it counts cases created wrongly, held where they are.
   - **Opening checks**: open incident, maintenance window, what changed in that window; then whether the count is
     falling.
   - **Contain first**: from where the counted cases are now. Waiting cases need no hold. A case that left by the
     main ending with a wrong outcome is held where it is. More cases leaving by an alternative or exception move
     are stopped by everyone who can make that move: each person in its `carried_by`, and whoever can sign in to a
     web front end in its `carried_by` that no main move of the stage uses (a back-office screen with its own login).
     So put every role that can make the move in `carried_by`, each a person row in `subjects.csv`. A move marked
     `irreversible` is said to be so. Every `do not` remedy is named here.
   - **Its tests**: the failure modes of the states its cases are in or left from, except one whose `measures` reads
     another proposed alert's count and not this one's: that test lists the other alert's cases, so it is the other
     alert's own. Its own count's tests come first. **Shared dependencies come first of all**: a `needs` part that
     two or more of the stage's performing parts reach (their interactions in `subjects.csv`), or one that holds
     cases in several states, is tested before the rest, whether or not the states are recorded; among them, the
     cheapest check still leads, then the part more of the stage needs. Nothing is ordered by how likely it is: that
     is the operators' judgment, not the register's. **A called service's own dependency is reached through it**: a
     part only one service needs, where the stage reaches that service by a call and has a test of it answering
     with an error or slowly, is not a test of its own in the entry. It is linked from those tests, because a
     dependency that fails leaves its service up and answering badly. It stays in the shared section, and where the
     service has no such test it stays a test of its own. Each line says what a match means (the mode's `failure`, its
     citations dropped) and its ending; a match explains only the cases it lists, and the walk goes on for the rest.
     A test whose evidence lists no cases (a match in a log or a metric) explains no case by itself: the walk notes
     it, if the match falls inside the look-back, and goes on; a case no later test explains takes the ending of every
     test noted for it, each named in the hand-over, and where those endings differ the responder escalates rather
     than restores. For an alert that counts cases that already left wrongly, a falling count means only that no new
     cases are arriving: the recovering check never closes it.
   - **Linked tests**: where a mode's `failure` names another mode (`FM..`), it is linked to that mode; where it
     names a move (`L..`), it is linked to the modes that stop that move (those with `recovery` set). A link runs
     one way, from the mode whose text names the other, so name the cause a matching test should lead on to.
     **Write an `FM..` or `L..` id in `failure` only to make that link**; anywhere else, say the move or mode in
     words ("the booking record stays"), or the runbook sends the responder to a test that has nothing to do with it. An entry's
     linked tests are the ones its own tests link that it does not already work; a matching test's line says to
     run them too, on the same cases, and the shared section lists the same links, alert by alert. Each test's
     **Used by** names the alerts whose entries work it and those that link it. Name the other mode or move in
     `failure` where one cause leads to another, and write each test so it can be read on the cases of every alert
     that runs or links it: a linked test meets cases that may have left the stage.
   - **Escalation** goes to the owner of the failing part, the mode's `part`, as `subjects.csv` → `owner` records
     it; where that is blank, the runbook says *not in the map yet*. A party a remedy also escalates to
     (`remedies.csv` → `also_escalate_to`) gets its own row in the escalation table, *not in the map yet* where the
     register records no owner for it.
2. **List the failure modes, hop by hop (FMEA)**, in `failure-modes.csv`. For each move of the stage, take each hop
   kind in its `travels_by` and each mode `method/hop-failures.csv` lists for that kind; then each part in its
   `needs`, with the catalogue's `needs` modes; then make sure each part in its `carried_by` has a row. For each
   one, read the code: what happens to the case here, and how it recovers. Where the design rules a mode out, write
   the row with ending `not possible` and the citation. A mode the catalogue lacks is `other`. One row may serve
   several moves where the part, the test and the ending are the same. **One row may serve several parts, as a
   sweep**, where they are of one `part_kind` and share the hop, the mode and the ending: list them in `part`, and
   write one command over all of them whose result names which matched, so the test still tells them apart (every
   service with no ready instance, every database refusing connections). Take the command from what the
   deployment uses, as for any test; where no one command reaches them all, keep a row per part. Each part that
   matches is escalated to its own owner. A sweep keeps a stage that many services carry to a runbook a responder
   can work. **A mode is a live test only where what it
   does to the case is something a measure the stage proposes for alerting counts.** Otherwise its ending is `not possible`,
   its `failure` begins `not possible here: as a cause of` what the stage's alerts count, and names the measure that
   does count it (a wrong outcome is counted by its process step's measure, Step 9).
3. **Give each mode a test that tells it apart** from the others a responder meets in the same state: the exact
   query (table and columns as the code defines them), the log text as the code writes it, or the command. On a
   state column, `seen` lists every value the code can leave other than the healthy one. Name the measures it reads,
   adding them in Step 9 if they are missing. **A signal is only evidence where it is written:** a cancellation
   or deadline started by a caller shows at the caller, not in the callee's logs; a call made outside the request's
   trace context is not in its trace. Where a harmless cause gives the same signal as a fault (a party giving up
   looks like a slow part), the test says how to tell them apart, or the harmless ending is not used. **A test
   reads evidence that is still there when the responder arrives:** a search over the alert's window (the entry
   states it, and the runbook tells the responder to put it wherever a command asks for a time span in angle
   brackets, such as `--since=<window>`), by case id where the evidence carries one, never a tail of the last
   lines; and where a log may have
   rolled over, the test names the durable record (a row, a queue) that outlives it. Write the test so it can be
   read on the alert's own cases: a query that lists every case in a state is read only for the cases the alert
   counts. Where a test must see cases wherever they are now (a linked test meets cases that have left the stage),
   filter on `<case ids>`: the runbook tells the responder to put there the ids of the cases being worked.
   **A test is written once**: it serves every alert whose entry runs it. An alert's runbook entry needs its
   tests; where the code keeps nothing a test could read, gap them `no record`.
   **A test that lists cases takes them from every test after it**, because a match ends the walk for the cases
   it lists. So where a broad test lists cases that a more specific test explains (a condition still open, where a
   check that never ran is the cause), give the broad test a higher `order` than the specific one. After the
   checks that each part is up, which always come first, the entry runs tests by `order`, a blank counting as 0. A
   test whose evidence lists no cases needs none.
   **A command cites the deployed value, never a code default**: the port the deployed process listens on, the log
   line as the deployed logging configuration emits it (a traceback's last line, not a window of lines after the
   message), the name the deployment gives a resource. Where a configuration switch changes the value, write the
   value for the configuration `about.csv` names and state the switch beside it.
   **Before a test goes into a runbook, check it against one known case**: a seeded or demo row, or a reproduced
   failure, whose answer is known. The query lists that case, the grep prints that line, the command shows that
   state; and the healthy case gives the expected result. A test that matches every instance of a wider event (every
   failed turn, every restart) is not its mode's test: make it specific, or say in `seen` what tells it apart.
   Record each check in `how-made.csv`.
4. **Give each mode its ending**, and each `restore` or `stranded` mode its remedy in `remedies.csv`. **A mode that
   leaves its case stranded ends in `restore` or `cannot restore`**, even when the refusal that stranded it is the
   application working as designed (a balance that may not go below zero): the responder's job is the stranded case,
   not the refusal, and the check holds you to it. For a stranded
   case, look for a re-drive **outside the code as well as in it**: an action that puts the case back into a state
   the application moves on from by itself (a status reset the poller re-sends), cited to the code that makes it
   safe. If there is none, write a `none exists` remedy saying so and what to record. Write the actions that look
   like fixes and are not as `do not`. **A remedy is written once for every alert whose tests end at it**, so its
   text names no alert and no alert's query: say what to record in words that hold for any of them. It names no
   runbook section either (write `Escalate`; the runbook points it at its escalation section); it may name another
   remedy (`RM..`), and the runbook then writes that one too. A `do not` reaches only the alerts whose tests end at a remedy that uses or names it, so a remedy whose action makes a move that cannot be undone names the `do not` that cautions against that move. Escalation goes to the failing part's owner; a party
   the responder must also tell (the owner of a regulation, say) goes in `also_escalate_to`, never in the action's
   prose.
5. **Describe one configuration.** A test and a remedy are written for the configuration `about.csv` names. Where the
   repository ships another that changes the answer (a different store), say so in the test. Values are written as
   the store holds them: a status kept as a number is tested as that number, with its name beside it.
6. **Verify the claims against the code before anything is generated.** Re-open every distinct `file:line` a live
   failure mode cites (its `failure`, `test` and `source`: what a responder acts on), and a random sample of the
   rest of what the register cites for the stage's rows and the frame (flows, stages, steps, participation,
   lifecycle, remedies, measures, step impact). Rows added or carried forward from an earlier register (the
   `how-made.csv` pass `reconcile`) are read first, every one of them. State the sample's size in the `how-made.csv` row before you draw
   it. A failure in the sample re-opens every row of the batch it came from: the rows written the same way, in
   the same pass. Read the line itself, not a listing of several files. For each: does the
   line say what the row claims, and does the behaviour hold when you follow the call (a retry wrapped around the
   call that fails, a state the code really writes, a log text exactly as written, a remedy the code really
   lacks, a restore that really reaches the fault: adding an instance helps only if callers spread their calls
   over instances)? Correct each row that fails, and write a `how-made.csv` row for the pass: how many claims were read
   (those cited by live failure modes, and the sample, each counted), and how many were corrected. This pass is the drafter's own; someone who did not draft the register still checks a sample of the citations afterwards (USE.md, "Before you take it to anyone").
7. **Generate** the slice, the measures, the alerts and the runbook:

```
python "<skill>/flow_outputs.py" "<your-folder>" <flow> <stage> --out "<your-folder>/stage-<stage>"
```

It checks first, and writes `ALERT.md` and `RUNBOOK.md` only when the check passes: every hop, need and carrier of
every move covered; every mode's part in its move's lifecycle row; every test's measures in `measures.csv`; no two
modes in one state a responder cannot tell apart; a remedy for every restore and every stranded case; exactly the
measures marked in `alert` proposed for alerting, each naming the expectation it guards, at whatever level it is.
A stage no alert reaches is noted, not failed: it gets its runbook, which says no alert is proposed for it, and no
`ALERT.md`. A failure is fixed in the step that produced it. **Never edit a generated file.**
`ALERT.md` gives each alert its runbook link, to its own entry in `RUNBOOK.md`.

**Where other stages already have a `stage-<id>` folder**, this run can change what they rest on: a shared row, a
flow-wide row, a remedy. So regenerate every one of them the same way, each with its own `--check`. The run is not
done until every stage's check passes, because this stage's check only warns on what other stages hold.

## Step 12. Check and draw

Before drawing, run these against the register. Each one is a rule from above that a register can break:

- `flows.csv` → `starts_at` cites the line that creates the case's record, and the first lifecycle row's
  `from_state` is `(none)`.
- Every stage's `entry` is the previous stage's `exit` or the starting event (stage 1), its `exit` is the next
  stage's `entry` or an ending, and its `source` cites what each cut rests on or is `proposed:`.
- Every exit of every stage, main and alternative, has a process step whose lifecycle `to_state` is that exit.
- Every element of the measure step's receipt (Step 9) is covered by a candidate in `measures.csv` or gapped in
  `measure-gaps.csv` with its reason and source. `flow_outputs.py --check` prints the receipt's count and an error
  for each element of the run's stage, or of the flow, that is neither. One that belongs only to other stages is a
  warning in this run, and an error in its own stage's run.
- Every test in an alert's entry explains something that alert counts. The check warns where a test's mode leaves
  the case in a way the moves in the alert's `counted_moves` do not count (it `moves on`, and the alert counts cases
  `stranded`): name the measure that does see it in the mode's `measures`, or say in the basis why it stays.
- Every measure with `alert` set names in `expectation` the expectation it guards, by an id in `expectations.csv`.
  Every `objective` has its `objective_source`, and none starts `proposed:`.
- Every `subjects.csv` row of `part_kind` database, cache, message broker, search index, file store, host or
  runtime, or platform service has `band` `technology`.
- Every component and external dependency has at least one `performs` or `supports` row; every other part named
  in the sources is in `set-aside.csv`.
- Every part in `lifecycle.csv` `carried_by` and `needs` is a subject id in `subjects.csv`.

```
python "<skill>/capability_views.py" "<your-folder>" --check
python "<skill>/one_canvas.py" "<your-folder>" "<your-folder>/views.html"
python "<skill>/flow_outputs.py" "<your-folder>" <flow> <stage> --check
```

`<skill>` is the folder `capability_views.py` is in. `one_canvas.py` writes the page, `how-this-map-was-made.html` beside it, and copies each stage's `RUNBOOK.html` and `ALERT.html` into `stage-<id>/` beside it. `--check` lists every id that points
nowhere, every value outside the closed lists, and every row with no citation. A failure in any check is fixed in
the step that produced it, and if the step's rule allowed it, in this procedure. A warning is not a failure: read
it, and either act on it or leave the reason in the row it names.

**The run ends with `run_status.py`**, and it is done only when that says DONE. DONE needs every output the run
owes, and every field a view requires (each one marked required in the steps above) answered or gapped, for each
element of the stages the run owes and for the flow. A gap is a row in `measure-gaps.csv`: the element's id (a
process step id, a part's subject id, a stage id, an alert measure's handle, or an expectation's id), the question exactly
as `run_status.py` names it, which is one of `step: trigger`, `step: timeouts`, `part: operations`,
`part: depends on`, `stage: other outcomes`, `stage: cannot be undone`, `alert: its own tests` or
`expectation: indicator`, the `kind` (`does not apply`,
`counted by`, `no record` or `not read`), `why` and `source`. `step: moves` takes a gap too, only of kind
`no record`, only for a process step no part carries, and with a `why` that cites the code read; that gap also stands for the
process step's trigger, what happens if it does not happen and its timeouts, and for the expected outcomes of a stage the process step
ends. Every other view question is answered, or only counted. A gap of kind `not read` does not pass on a first run. `run_status.py` lists each empty field by
element: fill it or gap it in the step that writes it, and run it again.

## When something new arrives

This is for a source that arrives after the run has finished. A source the first run fetches while walking is
pass `1` (Before you start, item 5).

A map is updated, not rebuilt. When a source the register has not read turns up, make a new pass:

1. Add the source to `sources.csv` with the next pass number.
2. Read it against the lifecycle first: a state or move it shows that the lifecycle lacks is added there, and the
   stages, process steps, parts and measures are re-derived from the changed rows by Steps 3 to 10. Where it names an
   owner, a responder, a party, an expectation, an objective or a volume, fill the blank, citing it.
3. Never delete a row because the new source is silent about it, and never overwrite one source with another.
   Where they disagree, keep the existing row and put both accounts in its citation cell, each with its citation,
   and write the disagreement in this pass's `how-made.csv` `note`: it is a finding for a person to settle.
4. Cite the new source in every row you add or change, add `how-made.csv` rows for the pass, and check and draw
   again.

**An existing dashboard or alert export.** When the person points at an existing dashboard or alert export, read it
like any other source. Add a `sources.csv` row saying where it came from (the file or link) and when it was read.
For each panel or alert: cite it on the measure it shows, propose it as a candidate if the walk missed it, or set it
aside with a reason.

**An earlier register is not a new source.** A register made by an earlier run or an earlier version of this kit is
a tool's output: it is never read as a source, never written to, and its rows reach a new register only through the
reconciliation (`reconcile.py`, `SKILL.md` Phase 7), after a fresh walk. **In this release the reconciliation only
reports, and nothing from it is added to the new register.** The report lists each earlier row by its citation: a row
cited to code whose line still exists is *unchecked: not added*, since a line existing does not say it supports the
row; where the new register disagrees, the new row stands and the disagreement is listed. Under *Claims beside their
cited lines* the report prints each matched or unchecked row's claim with the lines it cites, and under *Re-open in
the document* each document-cited claim with the section it names, each with blank *Verdict* and *Reason* lines.
Fill them yourself, one row at a time (supported, not supported or not assessed, and why), since the script only
checks that a citation resolves, never what the line says. A row cited to a document is listed to re-open in the
document. A row cited to a person (`asked:`), or in a table the earlier `how-made.csv`
says a person confirmed, is listed as carried from a person, and a disagreement with the new walk is listed for a
person to settle. A `proposed:` row is dropped. A row citing a repository the new walk never read is *not assessed*,
never unsupported. Rule 3 above, keep the existing row on a disagreement, holds between sources, never for an earlier
register.

## What good enough looks like

- The frame is declared, and the flow starts where the case is created.
- Every stage boundary cites what it rests on, and every stage ends with the process step that moves the case out.
- Every part is tied to a process step, and sits at its layer. Every part not tied to one is set aside, in the open.
- Owners, responders and volumes are blank or proposed unless someone stated them, and an objective is blank unless someone stated it. That is a
  finding the views make visible, not a gap in your work.
