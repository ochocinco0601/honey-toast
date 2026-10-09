# Filling a register for one capability

For a language model drafting from the source material it is given. The run never stops to ask a person: what
the sources do not state, the model infers plausibly and labels `proposed:` with its basis, and a person confirms
or corrects those rows afterwards. The result is a filled register (the tables in
`register-template/`, defined in `register-template/REGISTER.md`) from which `capability_views.py` draws the
design-for-operations views, and from which `flow_outputs.py` generates each stage's slice, measures, alert and
runbook.

These are design-time views. You are describing what the capability is and where it could be seen, not reading
a running system. Nothing you write is a live value.

**This procedure is the method's procedure, applied to a register.** The method is
`reference/assigning-business-work-to-levels.md` (cited below as *Assigning*, with its Step number)
and `reference/what-each-level-can-report.md` (cited as *Rules*). Where a step below says what to do,
the method says why. The terms are defined in `reference/vocabulary.md`, and the measure layers in `reference/four-layers.md`. One thing is built first, and everything else is read off it: **the case's lifecycle**,
the states one case passes through and the moves between them. Stages, steps, parts, measures, the alert and
the runbook are each derived from that lifecycle by a stated rule, so a later check has something to compare
them with.

Three sources feed a register: the **code**, the **documents** (runbooks, architecture pages, service catalogue
entries, the business's own process descriptions), and anything people have said that was written down (notes,
tickets, recorded answers). Code shows what carries each move. Owners, responders, promises and volumes that no
source states are inferred and labelled `proposed:`; volumes stay named for the operators to measure.

## Before you start

1. Copy the CSV files in `register-template/` (not `REGISTER.md`) to a folder named for the capability. As you
   do each step below, add a row to `how-made.csv`: what went in, which files came out, and who did it (a tool,
   a model drafting, a person confirming, or by hand).
2. Decide what you will read. List each source in `sources.csv` with pass `1`, and keep the
   summary in `about.csv` → `sources_examined`, so a reader knows what "not assessed" covers. If the code has no
   version history, list it as the folder as found, with the date you read it.
3. If a code reader is available (the design-for-operations fact extractor, or your platform's equivalent), run
   it over the repository with a service map: one entry per deployable. It gives deployables, emission sites
   (logs, metrics, spans) and calls between services, each with a file and line. What it did not find is not
   looked for: read the services and deployment files it found nothing in, and cite what you read.
4. Name the configuration you describe: which optional components are switched on. Describe the one that runs
   in production, or, where several do, the one that carries the capability's AI agent. Write it in
   `about.csv` → `what_it_is`. If no source says which runs in production, describe the fullest one the
   repository defines, and write `proposed:` and why.

## Step 1. Declare the frame (*Assigning* Step 0; *Rules*, Rule 0)

Five declarations, written before anything else and never inferred silently:

| Declaration | Where it goes | The rule |
|---|---|---|
| The case | `flows.csv` → `case` | One individual business item: one order, one application, one appointment. Never a system, a team, a batch, a request or a basket. A flow has one kind of case |
| The delivering application | `about.csv` → `delivering_application` | The deployables that make up the application, named. Step 5 separates component from external dependency on membership of this set, so write it now |
| Whose expectation | `flows.csv` → `expectation_of` | The party counting on the outcome |
| The starting event | `flows.csv` → `starts_at` | **The act that first creates the case's record.** Cite the line that creates it. This is also where the party begins counting on an outcome: before it there is nothing for them to wait on |
| The ending outcome | `flows.csv` → `ends_at` | Where the party has what they were waiting for, or definitively does not. Name both endings. **The flow runs to that outcome even where the code stops sooner:** an order is delivered, not "Shipped"; the stretch after the last state the system records is added by the reference-model check in Step 3, drawn as not assessed |

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
  `person`. A move that takes several hops lists them in order, `;` separated.
- `carried_by`: the parts that carry the act out. `needs`: the stores, brokers and outside services the move
  cannot complete without. **Write each part as its subject id and name (`S04 Ordering API`)**, giving it the id now
  that becomes its `subjects.csv` row in Step 5. Every output is generated from these two columns, so a part named
  here and nowhere in `subjects.csv` fails the check.
- `timing`: what the code assumes about time for this move (a grace period, a poll interval, a timeout, a retry
  schedule), cited. Leave blank if nothing is assumed. **A retry or timeout counts only where the code applies it:**
  read the call site, not only the setting (a policy configured but wrapped around the wrong call never fires).
- `if_not`: what happens to the case if the move does not happen: retried by what, until when; left in
  `from_state` with nothing to move it; lost; failed back to the party. Cite it. This is the summary; Step 11 reads
  every hop's failure modes one by one, and where that reading finds the summary wrong, correct it here.
- `recovery`: `moves on`, `stranded`, `not created` or blank, as in step-impact.csv (Step 10).
- `irreversible`: `yes` where the move cannot be undone (money taken, goods shipped, a filing made).

Parallel moves get `parallel with <move>` in `order_note`; a move back to an earlier state gets `loops to
<state>`. Exceptions the code does not handle are written as `if_not`, not invented as moves. **A failure the code
does handle by telling the party** (an error page, a refusal returned to the caller) is a move: path
`exception`, into an ending named for it (`implicit: order failed back, shopper told`). Every way a case can leave
its stage then has a row, and a step (Step 4).

**An act that changes no state of the case** (emptying a basket, sending an email) is still a row, with `to_state`
the same as `from_state`. Its `from_state` is the earliest state it happens in: if it runs inside the same request
or transaction as another move, it takes that move's `from_state`, and so sits in that move's stage. Nothing waits
on it, so it never opens or closes a stage.

**A move that can leave from several states** (a cancellation allowed until payment) is one row per state it can
leave from, each cited to the guard that allows it.

## Step 3. Cut the stages from the lifecycle (*Assigning* Step 4)

**A stage boundary falls at each `park` state, and after each `irreversible` move.** Nowhere else: not at a
service boundary, not at each status the system exposes, not at each message.

- Stage 1 runs from the starting event to the first park. Each later stage opens where the case enters a park
  and runs to where it enters the next park or an ending. A stage holds its park and the moves out of it.
- `entry`: the state the case is in when it enters (the park, by its recorded value). `exit`: the state it is in
  when it leaves (the next park, or an ending). Both are read off the lifecycle, so they are not `proposed:`;
  cite the rows.
- Name each stage for what it achieves for the case, verb first, two or three words. The state at the boundary
  is the exit criterion, not the name.
- `promise`: a stated bound if a source gives one. Otherwise `proposed:` and a bound read from the
  lifecycle's `timing` for the stage's moves, cited: what the application's own design assumes. If the design
  assumes nothing, write `proposed: none assumed by the code` and say what would set one. A stage with no bound
  is a finding about the flow, not a reason to stop.
- `arrivals_per_period`: `not stated: measured by the operators`, unless they give it.
- Work that never parks is one stage. Work that parks often is many. Do not merge or split to reach a count.

**Then check the cut against the domain's reference model** (APQC's process classification, SCOR, the domain's
standard process), from the starting event to the ending only. A stretch the reference model expects inside
that frame that no lifecycle row carries is added as a stage or step with no participation, drawn as not
assessed. A stretch the reference model puts before the case exists is set aside (Step 1).

## Step 4. Write the steps from the moves (*Assigning* Step 5; *Rules*, Rule 0)

**Each step is one move, or several moves with no park between them that make one outcome the business would
recognise.** Hops between components inside one outcome are one step: they are mechanism, recorded in Step 6.

- Name the step as its outcome, without its performer: "Stock is confirmed for the order", not "Catalog API
  confirms stock", never "POST /items returns 201".
- **Every stage's last step is the move that takes the case out of it**, into the next stage's entry or an
  ending. One step per way out: the main move, and each alternative or exception ending. A stage with no step
  whose `to_state` is its exit is cut wrong: go back to Step 2.
- `right_outcome`: what a right outcome is for one case, stated or `proposed:` (the state the case should be in
  after it, with the values it should carry).
- A step carried only in part gets `qualifier` `partial: <what is missing>`; one carried by a stand-in (a
  hard-coded value, a simulated call) gets `stub: <what stands in>`. A step nothing carries stays, with no
  participation rows.
- Write the lifecycle row ids each step comes from in `source`, with the code citation.

## Step 5. List the parts from the lifecycle (*Assigning* Step 6; *Rules*, Rules 0 and 2)

Every part named in `carried_by` or `needs` gets one `element` row in `subjects.csv`. Nothing else does.

- **Component or external dependency** is membership of the delivering application (Step 1): `level`
  `component` if it is part of it, `external dependency` if the application only calls, waits on or fails over to
  it. Not the company boundary, and not whether it is open source.
- **Application component or system component** is its layer, in `band`. Services, workers, front ends and AI
  agents are application components: `band` `application`. **Databases, caches, message brokers, search
  indexes, file stores, hosts and runtimes, and platform services are system components: `band` `technology`**, even when the application owns
  them. A system component is measured with its kind's set at the technology layer, never as an application
  component. `part_kind` from `method/part-kinds.csv` decides the set; an AI agent is a component with
  `part_kind` `LLM agent`.
- **A part with no step it performs or supports is set aside**, in `set-aside.csv` with kind `out of scope part`
  and the evidence that named it: monitoring, platform tooling, a service no move uses. It is not deleted and not
  left out silently.
- A job that handles many cases per run (a polling worker, a nightly batch) is a component; its runs are its own
  measure, shown under the cases it failed to move.
- `carries_case_id` on every part the case passes through: `yes:`, `partly:` or `no:`, with where it is carried
  or lost (*Rules*, Rule 2).
- A front end served from inside another deployable is still its own component; say where it is deployed in
  `source`.
- A person who carries out a move: a `person` row, no level. It is the method's set-aside role, bound to its step.
- `owner` and `responder`: from a source that states them, with the date it was true; otherwise inferred from what
  the sources show (who builds and deploys the part) and written `proposed:` with that basis.

## Step 6. Record who carries out each step

For every step, in `participation.csv`, from the lifecycle rows it came from: each part in `carried_by`
**performs** it; each part in `needs` **supports** it (the step blocks or goes wrong without it, including a
database constraint that enforces the step's rule). The part that carries the move out of a stage performs that
stage's last step. Every part in `carried_by` performs; none leads. The generated outputs name all of them, so the
part that changes the case's state and the part that decides (a stock checker, a payment service) are both shown. `records` (only reads or writes the step's trace) may be added for a part that also performs
or supports some step; a part whose only involvement is `records` is set aside (Step 5). Write the activity in
a few words with the file and line in brackets. A part that shows the step's result to the party performs the
step whose outcome is that the party sees it.

**If a step can be carried more than one way** (the web form or the chat assistant; an automated route or a
person), name each way with a short label and, on every row of that step, list in `way` the ways the row belongs
to. Every way must be named on at least one row.

Then add an `interaction` row (`kind` relationship) in `subjects.csv` for each hop in `travels_by`: `from_id`,
`to_id`, and the steps it happens within in `step_hint`. `band` `application` between components, `technology`
for a part's call to the store or broker it runs on. A message published through a broker is two hops: the
publisher to the broker, the broker to the consumer. Number the hops of one step in `sequence` in the order they
happen, only for calls made once, one after another, on one way. Leave `sequence` blank, and say why in the
citation, for a call repeated per item, made in parallel, not waited for, or made only on one branch.

**How far to go into an outside service** depends on what you can get for it: nothing beyond its address, it
stays one external dependency seen from the calling side; its code or documents, add the parts your calls reach
as `external dependency` rows with `part_of` set to the service (one level only); its owner has a map, put the
address in `map_link`.

## Step 7. Describe each AI agent as its own system

For each `LLM agent` component, add a block to `agent-system.csv`. If the capability has none, leave it with its
header only and write a `how-made.csv` row naming where you looked.

1. **The run:** one decision for one case, or one request answered. Name the business steps it serves.
2. **Its steps:** what one run does (take the request, decide the next move, call a tool, retrieve, write the
   answer, check the answer).
3. **Its parts:** the sequencing code; the decider (the model, its prompt and its rules); its tools; what it
   retrieves from; the checks that stop an answer outside policy. Link each to the subject ids that carry it. A
   part looked for and not found gets a row with a blank `subject_id`, and `what_it_is` says where you looked.
4. **Its dependencies:** the model provider and the systems its tools call. Fill `uses` on each part.

An agent's conversation is a flow of its own only when it is one case's path the business would name, with its
own start and end; otherwise it is another way of carrying steps (Step 6, `way`).

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

Work down the levels, asking the question first and then naming the measure:

1. **The flow** (its case subject, `flow` set, `step` and `stage` blank): cases started, finished, still open;
   finished on time and right; still open past the promise.
2. **Each stage** (its case subject, `stage` set): cases in the stage now, the age of the oldest, the time to get
   through, and cases past the stage's promise. These sit at the park, counted from state changes. A stage
   measure counts cases, never requests.
3. **Each step that matters** (one event per case): did it happen for this case, and was its outcome right. The
   steps that matter are every stage's last step, the flow's first step, every step with a step-impact row, and
   every step an AI agent serves.
4. **Each part, its kind's set** (`method/part-kinds.csv`), at its layer: `application` for an application
   component, `technology` for a system component. An external dependency is asked the same sets from the
   calling side. An agent is asked the agentic questions (`method/agent-questions.csv`).

`exists` is `yes` only where the system already emits it: cite the emitting line, or the setting that switches on
a framework's built-in metric, in `source_ref`, and write `declared` in `source`. A log line counts, if it is
written once per case: read where it is written and what triggers it. Everything else is `exists` `no`, `source`
`proposed`. Business measures count cases. No thresholds or targets unless a document or person states them.

**Name a measure for what it counts.** A count of wrong outcomes is "Orders confirmed with an unknown item", never
"Stock confirmed rightly": a reader takes a rising count of a thing named "rightly" as good news.

**Mark `pages` `yes` on the stage measure an alert fires on**, and on no other row. The measures, the alert and
the runbook are generated from that column, so they cannot disagree. Which measure depends on the stage:

- **A stage that parks** piles cases up when a move out of it stops: page on the cases in the stage past its
  promise.
- **A stage that never parks** (one synchronous act that ends in seconds, success or failure) cannot pile cases
  up, because each case fails back or finishes at once. Page on the cases leaving by its exception endings or
  left stranded, against the cases that entered: a failure rate counted on cases. Say which record counts one
  event per case at those exits; if none does, the measure is `proposed` and names the record it needs.

## Step 10. Record what a failure costs (*Rules*, Rule 3)

For each lifecycle move whose `if_not` hurts the case, a `step-impact.csv` row on the step it belongs to: the
category from `method/impact.csv`, the unit counted in cases, and `recovery` copied from the lifecycle. A case
acknowledged to the party and then lost fits no recovery value: leave `recovery` blank and begin `note` with
`lost after acknowledgement:` and the evidence. A row about the move not happening at all keeps `cause` blank; a
row about one part's failure (a wrong answer, a lost write) names that part in `cause`, one row per failure. In
`case-attributes.csv`, what is at stake in one case.

## Step 11. The failure modes, the alert and the runbook for a stage (`reference/runbook-model.md`, "How to write one")

For each stage an alert is wanted on. The alert and the runbook are **generated**, never written: what you write
is the worksheet they are generated from.

1. **The expectation** is the stage's promise (Step 3), and the right outcome of each step that takes a case out of
   the stage. **The alert** fires on the measure marked `pages` (Step 9): cases past the promise in a stage that
   parks, cases failing back or stranded in one that never parks.
2. **List the failure modes, hop by hop (FMEA)**, in `failure-modes.csv`. For each move of the stage, take each hop
   kind in its `travels_by` and each mode `method/hop-failures.csv` lists for that kind; then each part in its
   `needs`, with the catalogue's `needs` modes; then make sure each part in its `carried_by` has a row. For each
   one, read the code: what happens to the case here, and how it recovers. Where the design rules a mode out, write
   the row with ending `not possible` and the citation. A mode the catalogue lacks is `other`. One row may serve
   several moves where the part, the test and the ending are the same.
3. **Give each mode a test that tells it apart** from the others a responder meets in the same state: the exact
   query (table and columns as the code defines them), the log text as the code writes it, or the command. On a
   state column, `seen` lists every value the code can leave other than the healthy one. Name the measures it reads,
   adding them in Step 9 if they are missing. **A signal is only evidence where it is written:** a cancellation
   or deadline started by a caller shows at the caller, not in the callee's logs; a call made outside the request's
   trace context is not in its trace. Where a harmless cause gives the same signal as a fault (a party giving up
   looks like a slow part), the test says how to tell them apart, or the harmless ending is not used. **A test
   reads evidence that is still there when the responder arrives:** a search over the time since the count began
   rising, by case id where the evidence carries one, never a tail of the last lines; and where a log may have
   rolled over, the test names the durable record (a row, a queue) that outlives it.
4. **Give each mode its ending**, and each `restore` or `stranded` mode its remedy in `remedies.csv`. For a stranded
   case, look for a re-drive **outside the code as well as in it**: an action that puts the case back into a state
   the application moves on from by itself (a status reset the poller re-sends), cited to the code that makes it
   safe. If there is none, write a `none exists` remedy saying so and what to record. Write the actions that look
   like fixes and are not as `do not`.
5. **Describe one configuration.** A test and a remedy are written for the configuration `about.csv` names. Where the
   repository ships another that changes the answer (a different store), say so in the test. Values are written as
   the store holds them: a status kept as a number is tested as that number, with its name beside it.
6. **Verify every claim against the code before anything is generated.** Re-open each `file:line` the register
   cites, for the stage's rows and the frame (flows, stages, steps, participation, lifecycle, failure modes,
   remedies, measures, step impact), and read the line itself, not a listing of several files. For each: does the
   line say what the row claims, and does the behaviour hold when you follow the call (a retry wrapped around the
   call that fails, a state the code really writes, a log text exactly as written, a remedy the code really
   lacks, a restore that really reaches the fault: adding an instance helps only if callers spread their calls
   over instances)? Correct each row that fails, and write a `how-made.csv` row for the pass: how many claims were read and
   how many were corrected. This pass is the drafter's own; someone who did not draft the register still checks a sample of the citations afterwards (USE.md, "Before you take it to anyone").
7. **Generate** the slice, the measures, the alert and the runbook:

```
python "<skill>/flow_outputs.py" "<your-folder>" <flow> <stage> --out "<your-folder>/stage-<stage>"
```

It checks first, and writes `ALERT.md` and `RUNBOOK.md` only when the check passes: every hop, need and carrier of
every move covered; every mode's part in its move's lifecycle row; every test's measures in `measures.csv`; no two
modes in one state a responder cannot tell apart; a remedy for every restore and every stranded case; exactly the
`pages` measures paging. A failure is fixed in the step that produced it. **Never edit a generated file.**

## Step 12. Check and draw

Before drawing, run these against the register. Each one is a rule from above that a register can break:

- `flows.csv` → `starts_at` cites the line that creates the case's record, and the first lifecycle row's
  `from_state` is `(none)`.
- Every stage's `entry` is a park, the state after an irreversible move, or the starting event (stage 1), and its
  `exit` is the next stage's `entry` or an ending.
- Every stage has a last step whose lifecycle `to_state` is its exit.
- Every `subjects.csv` row of `part_kind` database, cache, message broker, search index, file store, host or
  runtime, or platform service has `band` `technology`.
- Every component and external dependency has at least one `performs` or `supports` row; every other part named
  in the sources is in `set-aside.csv`.
- Every part in `lifecycle.csv` `carried_by` and `needs` is a subject id in `subjects.csv`.

```
python "<skill>/capability_views.py" "<your-folder>" --check
python "<skill>/capability_views.py" "<your-folder>" --out "<your-folder>/views.html"
python "<skill>/flow_outputs.py" "<your-folder>" <flow> <stage> --check
```

`<skill>` is the folder `capability_views.py` is in. Always pass `--out`. `--check` lists every id that points
nowhere, every value outside the closed lists, and every row with no citation. A failure in any check is fixed in
the step that produced it, and if the step's rule allowed it, in this procedure.

## When something new arrives

A map is updated, not rebuilt. When a source the register has not read turns up, make a new pass:

1. Add the source to `sources.csv` with the next pass number.
2. Read it against the lifecycle first: a state or move it shows that the lifecycle lacks is added there, and the
   stages, steps, parts and measures are re-derived from the changed rows by Steps 3 to 10. Where it names an
   owner, a responder, a promise or a volume, fill the blank, citing it.
3. Never delete a row because the new source is silent about it, and never overwrite one source with another.
   Where they disagree, keep the existing row and put both accounts in its citation cell, each with its citation,
   and write the disagreement in this pass's `how-made.csv` `note`: it is a finding for a person to settle.
4. Cite the new source in every row you add or change, add `how-made.csv` rows for the pass, and check and draw
   again.

## What good enough looks like

- The frame is declared, and the flow starts where the case is created.
- Every stage boundary is a park or a point of no return in the lifecycle, and every stage ends with the step
  that moves the case out.
- Every part is tied to a step, and sits at its layer. Every part not tied to one is set aside, in the open.
- Owners, responders, volumes and stated promises are blank or proposed unless someone stated them. That is a
  finding the views make visible, not a gap in your work.
