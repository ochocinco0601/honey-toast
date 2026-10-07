# Filling a register for one capability

For a person working with an AI assistant. The result is a filled register (the tables in
`register-template/`, defined in `register-template/REGISTER.md`) from which `capability_views.py` draws the
design-for-operations views: the map, what each column reports, any AI agent as its own system, and where a
failure reaches.

These are design-time views. You are describing what the capability is and where it could be seen, not reading
a running system. Nothing you write is a live value.

Three sources feed a register: the **code**, the **documents** (runbooks, architecture pages, service catalogue
entries, the business's own process descriptions), and the **people** who own or run the parts. Code shows what
carries each step. Only documents and people can give owners, responders, promises, volumes and tolerances.

## Before you start

1. Copy the CSV files in `register-template/` (not `REGISTER.md`) to a folder named for the capability. As you do each step below, add a row to
   `how-made.csv`: what went in, which files came out, and who did it (a tool, a model drafting, a person
   confirming, or by hand). The page draws it as the workflow behind the map.
2. Decide what you will read and who you can ask. List each source in `sources.csv` with pass `1`, and keep the
   summary in `about.csv` → `sources_examined`, so a reader knows what "not assessed" covers.
3. If a code reader is available (the design-for-operations fact extractor, or your platform's equivalent), run
   it over the repository with a service map: one entry per deployable. Its facts give you deployables,
   emission sites (logs, metrics, spans) and calls between services, each with a file and line. It does not
   reach every language, logging style or deployment format, so what it did not find is not looked for: read
   the services and deployment files it found nothing in, and cite what you read.
4. Name the configuration you describe: which optional components are switched on. Describe the one that runs
   in production, or, where several do, the one that carries the capability's AI agent. Write it in
   `about.csv` → `what_it_is`.

## Step 1. Name the capability and the system

- `about.csv`: one row. `system` is the name the business uses; `what_it_is` is two or three sentences.
- `capabilities.csv`: the capability this work is about, the one above it, and any inside it. A capability is
  what the business is able to do, named apart from how it is built. Take names from the business's own words
  where the code or documents give them, and cite where. The narrowest capability a whole flow is for is usually
  the right one to name; a stretch of a flow that no other case uses is a stage, not a capability.
- **If an AI agent serves several flows**, the register covers the lowest capability that holds all of them:
  the agent is one part of that capability, not of one flow. Name the narrower capabilities inside it.

## Step 2. Find the flows

A flow is one case's path from start to end as designed. Ask: what is one case (one order, one application,
one appointment), what starts it, and what outcome ends it?

An AI agent's conversation is not a flow of its own when it ends in the same outcome as the flow's other way of
carrying those steps (it finds a product, as browsing does): it is another way of carrying them (Step 6,
`way`). It is a flow of its own only when it is one case's path the business would name, with its own start and
end.

- One row per flow in `flows.csv`. A capability usually has several flows; list each one the system carries.
- `delivers`: the capability ids the flow is for.
- `case_identifier`: the field that names one case end to end, and where it is lost. Read the code for it.
- `promise`: copy a stated expectation if a document or person gives one. Otherwise write
  `none stated; proposed: ...` with the expectation the business would plausibly hold.

## Step 3. Draft the stages

A stage is one ordered stretch of a flow with an entry and an exit. Draft the stages from the field's reference
models for this kind of work (APQC's process classification, SCOR, the domain's standard process) before you
read how the code divides the work, then reconcile. If you have no copy of a model to hand, draft from what you
know of it, name the model in `source`, and mark every draft `proposed:`.

A flow runs from what the business would call its start to the outcome that ends it, even where the code starts
later or stops sooner. The stages nothing in the system carries stay, and are drawn as not assessed. Code often names its own phases; the business's stages are
what a person running the work would recognise.

Mark drafted entries and exits `proposed:`.

## Step 4. Write the steps as business outcomes

A step is one act inside a stage with an outcome the business would recognise, that happened or did not:
"The appointment is booked", not "POST /visits returns 201".

- Write the steps the reference model expects, then check each against the code.
- **A step nothing carries out stays in the register.** It gets no participation rows and is drawn as *not
  assessed*. Do not delete it, and do not invent something to carry it.
- A step the code carries only in part gets `qualifier` `partial: <what is missing>`; one carried by a stand-in
  (a hard-coded value, a simulated call) gets `stub: <what stands in>`.
- Steps found in the code that the reference model did not expect are added, and cited to the code.

## Step 5. List the parts

In `subjects.csv`, one `element` row for each:

- **component**: a part inside the system that is released on its own or carries steps of its own (a service, a
  worker, a front end, a database it owns). A front end served from inside another deployable is still its own
  component; say where it is deployed in `source`. Monitoring and platform tooling is left out unless it carries
  a step.
- **external dependency**: something it relies on and does not run (a provider's API, another team's system, a
  model provider).
- **person**: a person who carries out a step, with no level.
- **case**: the business object one case is recorded as (`band` business, `part_kind` case, no level).

`part_kind` comes from `method/part-kinds.csv`; it decides which measurement set the part is asked. An **AI
agent** is a component whose software makes a judgment call, usually by calling a language model to decide what
to do: give it `part_kind` `LLM agent`.

`owner` and `responder` come only from a document or a person, with the date it was true. Leave them blank
otherwise. A blank is drawn as not assessed, which is the truth.

## Step 6. Record who carries out each step

For every step, in `participation.csv`: which parts **perform** it (execute it), **support** it (serve it,
so it blocks or degrades without them) or **record** it (only read or write its state). Write the activity in a
few words with the file and line in brackets.

**If a step can be carried more than one way** (the web form or the chat assistant; an automated route or a
person), name each way with a short label and, on every row of that step, list in `way` the ways the row belongs
to: `chat` for a part only the chat way uses, `form; chat` for a part both use. A part that hosts both ways (one
front end serving the form and the chat) lists both. Every way must be named on at least one row. Without this,
the failure view reads every way as required.

Then add an `interaction` row (`kind` relationship) in `subjects.csv` for each call between parts that matters to
a step: `from_id`, `to_id`, and the steps it happens within in `step_hint`, `;` separated. One row per call, not
per step. A call made only at start-up keeps `step_hint` blank. Where one step is a chain of calls (the front end
calls checkout, which calls the cart, then payment, then shipping), number them in `sequence` in the order they
happen.

**How far to go into an outside service** depends on what you can get for it, and varies from one service to the
next:
- **Nothing beyond its address:** it stays one external dependency, seen from the calling side.
- **Its code or its documents:** read them (a new pass, if the map already exists) and add the parts your calls
  reach as `external dependency` rows with `part_of` set to the service. Point each interaction at the part it
  reaches. Stop where the calls stop: the map is about your cases, not the other service.
- **Its owner has a map of their own:** put its address in `map_link` on the service's row.
These combine: one service can have its parts listed and a link to its owner's map.

## Step 7. Describe each AI agent as its own system

For each `LLM agent` component, add a block to `agent-system.csv`:

1. **The run:** one decision for one case, or one request answered. Name the business steps it serves.
2. **Its steps:** what one run does (take the request, decide the next move, call a tool, retrieve, write the
   answer, check the answer).
3. **Its parts:** the code that sequences the steps; the decider (the model, its prompt and its rules); its
   tools; what it retrieves from; the checks that stop an answer outside policy. Link each to the subject ids
   that carry it. **A part you looked for and did not find** (often the policy checks) gets a row with a blank
   `subject_id`, and `what_it_is` says where you looked. Something the agent claims to do (in its prompt or its
   description) that no part carries is a step with a blank `performed_by`: it is drawn as not assessed.
4. **Its dependencies:** the model provider and the systems its tools call. Fill `uses` on each part.

## Step 8. Propose the measures, question first

For each flow, each step that matters, and each part, ask the question first and then name the measure.

- **Business health and business impact count cases**: cases started, finished, still open, finished on time
  and right; cases wrong or late. Put these on the flow (its case subject, no step, and the flow id in `flow`) or
  on a step. Two flows that share a case subject each need their own measure.
- **Below the step, ask each part its kind's set** (`method/part-kinds.csv`): rate, errors and duration for a
  service; freshness, correctness and coverage for a pipeline; and so on. An external dependency is asked the
  same sets from the calling side.
- **An agent is asked the agentic questions** (`method/agent-questions.csv`); put the question in
  `agent_question`.
- `exists` is `yes` only where the system already emits it: cite the emitting line, or the dependency or setting
  that switches on a framework's built-in metric, in `source_ref`, and write `declared` in `source`. A log line
  counts. Everything else is `exists` `no`, `source` `proposed`.
- Which steps matter: every step with a step-impact row, every step an AI agent serves, and the first and last
  step of each flow.
- Do not write targets or thresholds unless a document or person states them.

## Step 9. Record what a failure costs

In `step-impact.csv`, for the steps where a failure hurts cases: the category from `method/impact.csv`, the unit
counted in cases, and `recovery` (`moves on`, `stranded` or `not created`) only if the code or a person shows
which. A row that describes what the step not happening costs keeps `cause` blank, and holds whatever stops the
step; a cost only one way's failure has (the chat way gets no list) names a cause. A row that describes what one
part's failure does (a wrong answer, a stale list, a lost write) names that part in `cause`; write one row per
such failure. In
`case-attributes.csv`, what is at stake in one case.

## Step 10. Check and draw

```
python "<skill>/capability_views.py" "<your-folder>" --check
python "<skill>/capability_views.py" "<your-folder>" --out "<your-folder>/views.html"
```

`<skill>` is the folder `capability_views.py` is in. Always pass `--out`: without it the page is written beside the program. `--check` lists every id that points nowhere, every value outside the closed lists, and every row with no
citation. Fix what it reports, then draw. Open the page and read the map first: is this the capability, are
these its flows and stages, and does each step have the parts you expected?

## When something new arrives

A map is updated, not rebuilt. When a source the register has not read turns up (a repository that was missing,
an architecture document, a person who explains the business), make a new pass:

1. Add the source to `sources.csv` with the next pass number. If the register has no `sources.csv`, create it
   first from `about.csv` → `sources_examined`, as pass `1`.
2. Read the new source against the map as it stands, step by step, and change only what it shows:
   - add the flows, stages, steps, parts, calls and measures it shows that the register lacks;
   - where it shows a part carrying a step marked not assessed, add the participation row: the step is found;
   - where it names an owner, a responder, a promise or a volume, fill the blank, citing it.
3. Never delete a row because the new source is silent about it, and never overwrite one source with another.
   Where they disagree, keep the existing row, add the new source's account beside it (a second row, or the
   other value in `note`), and write the disagreement in this pass's `how-made.csv` row: it is a finding for a
   person to settle.
4. Cite the new source in every row you add or change.
5. Add `how-made.csv` rows for this pass: which steps you re-ran, what went in, which files changed, who did it,
   and in `note` what the pass added, found and disagreed with.
6. Check and draw again. The page's "How this map was made" shows each pass in order; earlier states of the
   register are in its version history.

## What good enough looks like

- Every flow the system carries for the capability is in `flows.csv`, even if only one is filled to the step.
- Every step has a citation, and every step without participation was looked for.
- Every AI agent in the system is a component with its own block in `agent-system.csv`.
- Owners, responders and promises are blank or proposed unless someone stated them. That is a finding the
  views make visible, not a gap in your work.
