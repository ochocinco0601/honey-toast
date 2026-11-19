# Filling a register for one capability

For a language model drafting from the source material it is given. The run never stops to ask a fact it can infer:
what the sources do not state, the model infers plausibly and labels `proposed:` with its basis, and a person confirms
or corrects those rows afterwards. What is the person's (intent, scope, judgement and taste: which flow, whether the
sources are enough, whether to keep going) is brought to them with a proposal when it arises; the plan (Before you
start, item 7) is the first such point. The result is a filled register (the tables in
`register-template/`, defined in `register-template/REGISTER.md`) from which `one_canvas.py` draws the
design-for-operations map, and from which `flow_outputs.py` generates each stage's slice, measures, alert and
runbook.

**A claim that something is absent or never happens** ("stored nowhere", "never joined", "no other service can be
asked") cites the search that established it: what was searched for, and where (the files or folders read), named
in the row; otherwise it is labelled `proposed:` with its reason. A cited line shows what is there, never what is not.

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
is never inferred: it is written only where a source states it (the measures skill's step "Propose the measures", the parties and their expectations).

## Before you start

`<your-folder>` is the register folder: the one on the `FOLDER:` line `start.py` printed for the run picked up, or on a
fresh start the one you were given or named, `bfo-work/<the system's name>/` (never `answers`), which
`start_register.py` prints back on its own `FOLDER:` line. Never take it from a listing of the work folder: `bfo-work/`
also holds `answers/`, where the page saves what the person sends, and a home screen drawn there leaves the person's
page on an error. A script handed a folder that is not a register refuses it and names the register folders it found.

1. Start the register with `python "<skill>/start_register.py" "<your-folder>"`, in a new folder named for the
   capability. It copies the CSV files in `register-template/` (not `REGISTER.md`), and refuses a folder that
   already holds a CSV file, so earlier work is never copied over. While the workspace holds a run of this kit that
   is not finished, it refuses a new folder unless given the person's words to start new (`--new --words`): such a
   run is picked up, and `start.py` decides which. When the run picked up was written by an earlier release of
   this kit (a new chat, a resume, or the kit updated mid-run; the check says so and names `--migrate`), upgrade
   it without asking, since the migration changes no content and this kit cannot run the old form: back the
   register folder up to a folder outside the workspace (inside it, the start step would take the backup for an
   earlier register); run `python "<skill>/reconcile.py" --migrate "<your-folder>"`, which rewrites the register
   itself in place; run the check again; and restart the page's listener so the page runs this kit:
   `python "<skill>/listener.py" stop "<work folder>"`, then `python "<skill>/wait_on_page.py" "<your-folder>"`,
   and start the wait again. Tell the person in one line, through `say`, what was done and where the backup is.
   Where the upgrade names AI agent rows not classed (an older kit classed them while proposing the measures), that line says how
   many, and that mapping re-reads the code behind each tool, reply and chained action and classes it (Step 7)
   before the run is done: a re-walk, announced before it starts and going ahead unless they object, as a
   correction to mapping (`corrections.csv` for a finished flow's rows).
   For what the effect lines in the kit's `CHANGELOG.md` still name: a fill from the register's own citations
   runs on its own and is announced; a re-walk, which reads the code again, is announced before it starts, saying
   what will be re-read and why, and goes ahead unless they object; only a failed check makes it a question, so if
   the check still fails after migrating, stop and tell them, through `say`, with what you recommend.
   This is the run's own register; an earlier register, made by another run, is never written into. As you
   do each step below, add a row to `how-made.csv`: what went in, which files came out, and who did it (a tool,
   a model drafting, a person confirming, or by hand). `RUN.md` from the same folder is the run's record of its
   phases: when the kit is run as a skill, the skill's `SKILL.md` says how it is written and kept.
2. **Gather what you will read**, and list it. Take every source the person pointed at, and what is in the
   workspace, and get each with your own tools. List each in `sources.csv` with pass `1`; `kind` is `code`,
   `document` (a page, a diagram, a process description, a runbook, a catalogue entry), `person` (notes, tickets,
   recorded answers) or `tool output`. `found_by` is `person` for a source the person named or gave (and anything
   read inside it), `run` for one the run's own search found. In `note`, write which step below will use it. Write `sources.csv` as soon
   as the list is complete, and run the survey and the code reader (item 6) as soon as what each reads is in
   place, never all at the end: the run's page reads these files to show how far the first look has got. Keep the summary in
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
   | A business process description (a process page, a process diagram, a procedure) | Whom the flow serves and what each party expects of it; where the case starts and ends; what the party would recognise as done, which places stage cuts; a stated bound (an objective); what a right outcome is | Steps 1, 3, 4, 9 |
   | Code: the text it shows a party (status messages, notifications, notices) and the rules it enforces | A party's expectation in the words the party is shown; an objective, where the shown text states a bound, or where an enforced rule states one and the code names the rule's authority; a party the code shows only as a persona, a role or a rule, labelled `proposed:` | The measures skill |
   | An architecture page or diagram | The deployables the flow runs through, and where each one's code is; a cross-check of the parts the walk found, and of component against external dependency (whether its code can be had); an outside service's own parts, one level | Steps 5, 6 |
   | A service catalogue or configuration database entry | A part's registered id, owner and responder, with the date true | Step 5 |
   | A runbook, a support or incident page | Owner, responder, escalation; how a failure shows and what is done about it | Steps 5, 11 |
   | A document saying what the organisation is able to do | The capability, named from the documents alone | Step 8, second route |
   | People's notes, tickets, recorded answers | Owners, responders, parties with their expectations and objectives, and volumes no other source states | Steps 3, 5, 9; "When something new arrives" |

   A source is read only far enough here to place it in this table; the steps read it in full.

   Read backwards, the same table says which kind of source would settle what the run had to propose. The report's
   *What would make this map fuller* counts the `proposed:` or blank cells this way:

   | `proposed:` or blank in | Settled by | From the table's row |
   |---|---|---|
   | `stages.csv` → `source` (a cut) | A business process description; a person | Step 3 |
   | `stages.csv` and `flows.csv` → `bound_in_code`, where filled | The code or its configuration: the line that sets the timer, deadline or overdue rule | Step 3 |
   | `expectations.csv` → `party`, `expectation`, `satisfied_when`; `objective` blank | A business process description; the text the business shows the party; a person | The measures skill |
   | `steps.csv` → `right_outcome` | A business process description; a person | Step 4 |
   | `subjects.csv` → `owner`, `responder`, `application_id` | A catalogue or configuration database entry; a runbook; a person | Step 5 |
   | `stages.csv` → `arrivals_per_period` and other volumes | The operators (never derived) | Step 3 |
   | `about.csv` → `what_it_is` (configuration) | Deployment definitions | Before you start 4 |
   | `capabilities.csv` route 2 missing | A document saying what the organisation does | Step 8 |
   | A part with `repository` blank, an external dependency with no source | Its repository or its owner's documents | Step 6; item 5 |

3. Use every code-intelligence tool the environment offers over the workspace's repositories: a call graph and its
   business logic for Step 2's walk; a cross-repository trace for Step 6's dependencies; failure-handling analysis
   (timeouts, retries, circuit breakers) for the stage kit's step "The failure modes, the alerts and the runbook for a stage"'s failure modes; unreferenced code, written up as a finding.
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
   If the person has already agreed to a search that covers it, the place and the kind of code they agreed to
   (`RUN.md` *Sources* records what they agreed to search), and its repository or documents can be reached, get
   them; otherwise ask the person, as a question that needs their judgement, with where you propose to look, and get
   them only on their yes. A source found during the first run is pass `1`, not a
   new pass, and it goes into a folder of the workspace (item 2). Fetch it only with access the person already has, and read-only: never request access, enter credentials, or change anything at the source. Record every fetched source in `RUN.md` *Sources* with what referenced it and why. If the person's request says to use only the sources they name, do not fetch: list it under *still missing* instead. With its code, it is a component (Step 5), whatever its application id or owning team, and you read the
   operations this flow calls and what those call. If its code cannot be had, it is still a part (Step 5), cited by
   the line that identified it, with `repository` blank: an external dependency, and its measures are gapped with
   the reason. List it under *still missing* in `RUN.md`.
   **Check the repository set is complete.** The first look resolves references only against the workspace and what
   the person gave; it does not search a code host. (a) For every reference the code makes that no folder in the
   workspace answers (a host or service name, a client package, a queue or topic, an image, a configuration key, a
   URL), and (b) the other way, for the repositories that may call, consume from or deploy this flow's services, write
   an item in `orientation.json`'s `unresolved`: what is open and where the run proposes to look, in plain words like
   the rest of the brief, taking where and how to search from the environment the run is in (its own instructions,
   tools and sources). Write each so the brief's plain-words check passes: name the service and the kind of
   reference ("the address the basket service calls for payments"), never the address, path, file name or id
   itself. The brief lists them under what is still open. At the brief the person can say yes to any of these
   searches. Search only on that yes, with the person's own access and read-only: a yes is a change to the brief
   (below, "If they ask for changes to the brief"), and (c) what the repositories found reference is brought to the
   person the same way. Record each repository found in `sources.csv` with the search that found it and `found_by` `run`, add it to the
   workspace as a further folder, read-only, and write in `RUN.md` *Sources* what the person agreed to search; what
   is found and cannot be had goes under *still missing*, and what the person does not agree to search goes under
   *still missing* too. `RUN.md`'s Phase 0 line answers "Is this the complete set of
   repositories?" with that evidence, and Phase 0 is not done while a reference is neither resolved nor put to the
   person with a proposal. If the person's request says to use only the sources they name, do not
   search: list each unresolved reference under *still missing* instead. The same holds when the run cannot search (no
   access to a code host, or the person has said nothing is to be fetched): list each one, with why it was not searched.

6. **Survey before reading.** Once the repository set holds what the workspace and the person gave (and again, with
   the code reader, whenever a search the person agreed to adds repositories), run
   `python "<skill>/survey.py" "<your-folder>"`. It reads the code rows of `sources.csv` (or the repository folders
   given after the register folder) and writes `survey.csv`: each service with its place, its size in files and
   lines, its entry points, and the other services it names as an address, counted by the script and never
   estimated. Read the deployment and configuration definitions now (item 4), and enough of each service's entry
   points and routes to say what it does in one line. Nothing else is read in depth yet. Add the survey to
   `sources.csv` as `tool output` and to `how-made.csv`.
   Then run the code reader over the same repositories, from the workspace root:
   `python "<skill>/fact-extractor/run.py" . --service-map <folder>=<service> ... > "<your-folder>/fact-base.json"`,
   one `--service-map` pair per service folder (`fact-extractor/README.md` says how to run it and what it cannot
   reach). It finds each service's routes, calls, messages and database writes, each with file and line, by rule and
   never by a model. Check what it produced with `python "<skill>/fact-extractor/contract.py" . "<your-folder>/fact-base.json"`
   and record its `reach` block in `how-made.csv`; a kind its contract does not know is reported, not a reason to
   stop. The reader is a module: any tool whose output `fact-extractor/contract.py` accepts can take its place. A row
   resting on one of its facts is labelled `extracted` and cites the fact's file and line. What it finds are leads,
   not rows: each one in a service the flow touches is read, then cited by a row or set aside with the reason, and
   the done check names any left over. What it misses (most calls between services, in practice) is found by
   reading, labelled `proposed:`, and cites both ends, the call and the operation that receives it.
   A file the survey or the code reader could not read is listed with the reason (`survey.csv` → `unread_files`,
   and the fact base's `unread_files`); the capability brief and the map's inspection then tell the person how many,
   and that mapping may have missed code in those files.
7. **The first look, the capability brief, and the stop for the person's word.** The person knows the business but
   not this system and not this kit. Before anything is read in depth, they get a brief that shows the run understood
   its job and the system, and they pick which flow this run maps first.
   - **Read shallowly, only what names the business flows:** each service's entry points and routes (for a
     storefront, its pages and its API), its interface definitions, the deployment files, and the documents. No
     service is read in depth before the person's word.
   - **Write `orientation.json`** in the register folder. Every text in it is for the person: plain words, no ids, no
     file or folder names, none of the kit's vocabulary (register, unit, phase numbers, judges, merge), and each term
     defined in the sentence that first uses it. Its fields:
     ```json
     {"activity": {"for": "what business flow observability is for, in your own words",
                   "this_run": "what this run will produce for this system"},
      "capability": {"name": "", "what": "what the system does, in one or two sentences",
                     "for_whom": "who it serves"},
      "services": [{"name": "exactly as in the survey", "does": "a phrase starting with a verb: holds, takes, decides",
                    "recommend": "in or out", "why": ""}],
      "flows": [{"name": "", "what": "one sentence",
                 "one_case": "what one case of this flow is, the thing followed start to end", "found_in": "where in the code you saw it (path:line; kept
                 for checking, never shown)", "stages": [{"name": "", "what": "one sentence"}],
                 "services": ["each service this flow touches, exactly as in the survey; the go reads these for
                 this flow, and without them reads every service for any flow but the one recommended"]}],
      "searched": ["what you looked at"], "unresolved": ["what is still open, and where I propose to look"],
      "earlier": "an earlier map found, and what it changes for this run (leave out when none)",
      "recommendation": {"flow": "a flow named above", "why": "",
                         "remains": "what remains of the capability after this run"}}
     ```
     List every flow found so far, not only the one you recommend: one run maps one flow, and the job is the whole
     capability. Each flow says what one case of it is: a case belongs to a flow (one order, one sign-up), so the
     capability names none. A flow you did not find may still exist; say what you searched. Each flow is labelled a proposal
     until the walk confirms it. `this_run` says what this run produces as one batch of the job, never as the whole
     job ("this run maps the flow you pick, one batch"). The brief places each text inside a sentence: write `for_whom`,
     `one_case`, each `searched` and `unresolved` item, `why` and `remains` as phrases that continue a
     sentence, starting in lower case unless with a name; name tools in words joined by "and", never with slashes.
     `why` is one short sentence, with no semicolons: the one reason that makes this flow the place to start, in
     under 30 words ("it is where the shop takes the shopper's money, so a failure there costs the most"), never a
     chain of reasons. The same holds for every recommendation you write for the person: the `--recommend` of
     `brief.py depth`, `next`, `measures` and `alerts` is one short sentence, with no semicolons.
   - **Render the brief:** `python "<skill>/brief.py" capability "<your-folder>"`. It refuses, and says why, while a
     field is empty, the services are not the survey's, the recommended flow was not found, or the text
     carries an id, a file name or kit vocabulary. When it passes it writes the full brief to `PLAN.md` and prints the short one for the chat: the question
     and your recommendation first, what a yes does, the flows found as a list, and what else they can change.
     When they ask for the detail (each flow's stages, each service and why, what is still open), show `PLAN.md`.
   - **Send the printed brief as your message, exactly as printed, and stop.** `brief.py` marks the stop in `RUN.md` itself.
     Read nothing further until the person answers. If they ask for changes, change `orientation.json`, render again
     and wait again. A yes to a search the brief proposed is such a change and records no go: search, add each
     repository found (item 5), run the survey and the code reader again (item 6), update `orientation.json`, render
     again and wait again, with any flow they picked in the same answer as the recommendation (SKILL.md phase 0
     says how a yes sent from the home screen is taken).
   - **Record their answer by script:** `python "<skill>/go.py" "<your-folder>" --flow "<flow>" --words "<their
     answer, word for word>"` (add `--test` when a test stands in for the person). The go asks only which flow comes
     first; where they accepted the recommendation, it is their pick. The services read are those the brief marked
     include, and the checks per finding three, as the brief said; add `--in <service,...> --out <service,...>` or
     `--judges <n>` only when they say otherwise. Every finding that cites code is checked by that many readers who
     wrote none of it ("Reading in units, and every finding checked", below).
     `--stages` is refused: the stages are picked after mapping (`go.py --depth`). `go.py`
     writes `scope.json`, with what remains after this run, and `run-settings.json`, and fills the go and scope lines
     of `RUN.md`. A run's done is not the capability's done: `run_status.py` owes what their pick of how far each
     stage goes asks for, reports every other stage as not yet covered, and says NOT DONE while no go or no pick is
     recorded. With no pick of how far each stage goes (an earlier run, whose go named stages), `go.py
     "<your-folder>" --stage-ids <id>,<id>` records the ids of the stages it named once Phase 2 cuts them, and
     `run_status.py` owes alerts and runbooks for those stages only.

### Reading in units, and every finding checked

From the go on, every flow is read in **reading units**, one per service (a large service cut by folder), each read
by its own reader, and every row that cites code is **checked by `judges` independent checks** (`run-settings.json`;
three unless the person gave another number at the go), each a fresh agent that wrote none of the map. There is no
other path and no sample. Steps 1 to 4 and 7, 8 and 10 below are the lead's; Steps 5 and 6 are what each reader does
for its own service, in the unit formats (`split-run-formats.md`), and the lead does them only for its own parts (the
case, the people who act).

**Who does what.** The lead is the run's own session, the one that talks to the person: it writes the flow-level
rows, launches every other agent and decides each next step. The first-look helper launches none, and nothing but
the first-look helper is launched before the go. The lead never writes into `units/`, a verdict file or a unit's row itself: a unit holding the
lead's writing fails its check. Every agent is launched with the Agent tool, never a fork: a launcher or a judge as
`general-purpose`, a reader, fixer or re-read as `bfo-unit-reader` (its launcher says which), and
every prompt is a file a script wrote: each Agent call carries only its pointer line. The check reads this from the
transcripts: a reader, fixer or re-read whose first message is not the pointer line of a prompt `readers.py` or
`judges.py` wrote, unchanged since, has its writes left out and fails its unit, named, until relaunched.

**How agents are launched.** `readers.py prompt` and `judges.py emit` write the prompts under
`<your-folder>/prompts/` and print a count, then one pointer line per launcher. Launch one launcher per printed
pointer line: a `general-purpose` agent with that line as its whole prompt. For judges that is one launcher per unit,
and for the `flow` unit one per lead table; readers and fixers share launchers. No launcher holds more than 150 agents
(the scripts split a larger set across launchers). Each launcher launches its own agents, at most `parallel` at once
(`run-settings.json`, default 6), and replies in one line. A launcher is an agent too, so keep running at once no
more launchers, in all, than the count line names ("keep at most N launcher(s) running at once"); on "Concurrent
subagent limit reached", launch nothing until a completion notification arrives. After launching, the lead ends its
turn. Each launcher's reply comes back as a completion notification, in a turn of its own: decide the next step from
the files on disk, never from the replies. Run the same command again (`judges.py emit`, `readers.py prompt`) at any
time: it never launches an agent twice. It prints only the agents never launched, and the ones still running when
their launcher replied (they stopped without replying) or when it stopped without its reply line (its transcript ended
on other text, an error or out of turns, and has been quiet two minutes since: the command names it); an agent launched already, or waiting in a launcher still
running, is named, `queued in a launcher still running`, `launched already, still running` or `launched already,
finished`, and not printed, and a launcher still running is left as it is. So launch every pointer line it prints.
Judges: it prints only judges whose verdict is still missing on disk. Readers: a unit is read for this flow once its
`files.csv` was written after this flow's go (an earlier flow's reader left one too); `readers.py prompt
"<your-folder>" --in-scope` writes a reader for every unit owed one and names the units read already, so you never
work out yourself which units are owed. Fixers: a fixer that keeps a row as it is
writes nothing, so the tables cannot say it is done; its transcript can. A fixer is the fix of its rows as the judges
flagged them: a row flagged again after its fixer finished (in the next round, or when judged again at the map stop)
gets a fixer of its own. Start round 2 once no fixer is named still
running. A reader or fixer that ran a shell fails its unit's check, which names it and the relaunch command
(`readers.py prompt "<your-folder>" <unit> --mode read` or `--mode fix`, with `--again`, which first puts back what
that agent wrote); launch what it prints. A lead that lost count, or whose context was compacted, resumes the same
way, from disk. **After a crash or a restart of your own session**, every agent and launcher you had launched died
with it, though the files still name them running: run each command once with `--again`, which launches afresh only
those, and never an agent that finished. Use `--again` only then: while your own launchers run, it would launch
their agents a second time. If the person writes while agents are running, answer in one line, through `say`, that
the mapping is under way and what is being done (reading, checking or fixing), and launch nothing.

**The order.**
1. Steps 1 to 4, by the lead: the case, its lifecycle, the stages and the process steps (`flows.csv`,
   `lifecycle.csv`, `stages.csv`, `steps.csv`), and its own parts in `subjects.csv` and `participation.csv`. The
   readers place their parts in these process steps, so these come first.
2. `python "<skill>/units.py" "<your-folder>"` lists the reading units (`units/units.csv`). Then
   `python "<skill>/readers.py" prompt "<your-folder>" --in-scope`, which writes a reader for every unit of a service
   in the go's scope (`scope.json` `services_in`) not yet read for this flow, and launch as above. Each reader reads
   its unit in full and writes only `units/<unit>/`; a unit it finds nothing of this flow in is recorded as read, with
   no rows.
3. When every reader is back (`readers.py prompt "<your-folder>" --in-scope` writes no reader and names none still
   running): `python "<skill>/merge.py" "<your-folder>"` writes the map's parts and the calls between them. Each call
   it leaves unmatched (`merge/unmatched-calls.csv`) is re-read by its own agent: `python "<skill>/readers.py" prompt
   "<your-folder>" --mode reread` writes one re-read per call, and you launch as above; then merge again. A reader
   cannot ask the person anything, so a call to a deployable whose code is not in the workspace reaches the lead
   through the merge: the reader records it with `to_part` `external:<name>`, named from what the call shows, and the
   merge draws each such name as an external dependency. For each external dependency that is a service (not a store
   or a broker), the lead applies "Before you start", item 5: get its code if a search the person agreed to covers
   it, otherwise ask them. Code that is got goes into the workspace (item 2), is surveyed and cut into units as the
   rest was (the survey again, then `units.py`, which keeps the units already listed), and is read by its own reader
   before judging starts: a service the survey lists that the go neither took in nor left out came after the go, and
   `readers.py prompt "<your-folder>" --in-scope` writes its reader as for any service of the go's scope; code that cannot be had stays an external dependency, listed under *still missing*.
4. The lead's rows after the merge: the parts set aside, the AI agents (Step 7), the capability (Step 8) and Business
   Impact (Step 10). A row the lead adds to `subjects.csv` or `participation.csv` after the first merge goes in
   `merge/lead-rows/`, then merge again. Judging starts only once these are written, so the flow-level rows written
   after the merge are judged once written, in the same rounds as every other row. A row written or changed later has
   no current verdict, and the next `emit` prints its judges.
5. Round 1: `python "<skill>/judges.py" emit "<your-folder>" <unit> --round 1` for `flow` and for every unit with rows
   of this flow, and launch. When `emit` prints nothing still missing for any unit:
   `python "<skill>/judges.py" collect "<your-folder>"`.
6. Fix: `python "<skill>/readers.py" prompt "<your-folder>" <unit> ... --mode fix` writes a fixer for each unit with
   flagged rows, and for `flow` one fixer per lead table with flagged rows; launch. A unit's fixer writes only its
   unit's folder, a lead table's fixer only its table. Merge again when a unit's rows changed.
7. Round 2: `python "<skill>/judges.py" emit "<your-folder>" <unit> --round 2 --rows flagged` for each unit with
   flagged rows, launch, then `collect`, which labels every row still flagged `disputed:`.

So the order is round 1, `collect`, fix, round 2, `collect`, and only then the done check (`run_status.py`, or
`go.py --mapping-ends` for mapping alone): never before the last `collect`, so the last label is on the map before
its verdict is kept.

**Fixing a flagged row.** One owner: the fix step above, by fixers. The lead never fixes a row itself, which keeps
its own writing out of the units. A fixer may narrow the claim to what the cited lines show, or correct the citation
to the lines that show it. It may also relabel the claim `proposed:` with the reason, drop a citation, or withdraw
the row; each of these is counted apart in the report and never counted as fixed. It never changes a row's key (its
first column): that counts as a withdrawn row plus a new, unjudged one. A row still flagged after round 2 stays on the
map labelled `disputed:`, shown as not confirmed by the code, never as fact.

### The next flow, in a map that holds a finished one

The job is the whole capability, so each flow after the first is added to the same register. When the person picks
the next flow (`go.py --flow`), `go.py` keeps a copy of every row the map holds, under `earlier-flows/<flow id>/`,
and the walk is Steps 1 to 8 and Step 10 for that flow alone, read from the code again. Phase 0 is not done again:
the sources, the survey and the first look stand, and a source this flow needs is added to `sources.csv` with the
next id.

- **Add rows; change none.** Every row already in the map stays as it is, word for word: an earlier flow's rows,
  and the parts it listed. A part this flow uses that is listed already keeps its `subject_id`; add its
  participation rows for this flow's steps (Step 6), and list only the parts not yet listed. What you find wrong in
  an earlier flow's row goes in `corrections.csv`, never into the row. This flow's own row in `flows.csv` is
  filled in as Step 1 says.
- **Ids continue after the highest the map holds.** Stages from the next `ST<n>`, process steps from the next
  number, moves from the next `L<nn>`, parts from the next `S<nn>` and relationships from the next `R<nn>`;
  expectations, failure modes, remedies and measure handles the same way. An id is never used twice in the map.
- **A further flow is a new pass.** Its `how-made.csv` rows take the next pass number: one above the highest pass
  the map holds when the flow starts. The sources it reads again keep their rows and their pass: no row is added to
  `sources.csv` for them, and the check accepts a pass for each flow the register holds. Only a source the flow adds
  gets a row, with that pass; never `1`, which stays the first flow's.
- **The same holds for Steps 9 and 11** when the person takes the new flow's stages on to measures, alerts and
  runbooks: this flow's measures, failure modes and remedies are added; a finished flow's are never changed, and a
  part a finished flow already measures keeps those measures.
- The done check (`run_status.py`) says NOT DONE on an id used twice and on any row of a finished flow that is
  changed or gone; the map inspection (`check_map.py`) reports both.

## Step 1. Declare the frame (*Assigning* Step 0; *Rules*, Rule 0)

Four declarations, written before anything else and never inferred silently:

| Declaration | Where it goes | The rule |
|---|---|---|
| The case | `flows.csv` → `case` | One individual business item: one order, one application, one appointment. Never a system, a team, a batch, a request or a basket. A flow has one kind of case. Write its name only; where it is stored and what identifies it go in `case_identifier` |
| Whom it serves | `flows.csv` → `customer` | The party counting on the outcome, the one whose outcome ends the flow: its role name only; a citation for it goes in the row's `source`. Every other party the flow serves or binds is named in the first part of the measures skill's step "Propose the measures" |
| The starting event | `flows.csv` → `starts_at` | **The act that first creates the case's record.** Cite the line that creates it. This is also where the party begins counting on an outcome: before it there is nothing for them to wait on |
| The ending outcome | `flows.csv` → `ends_at` | Where the party has what they were waiting for, or definitively does not. Name both endings. **The flow runs to that outcome even where the code stops sooner:** an order is delivered, not "Shipped"; the stretch after the last state the system records is added by the reference-model check in Step 3, drawn as not assessed |

`flows.csv` → `bound_in_code` is optional: fill it only where the application's code sets its own timer, deadline
or overdue rule for one case, end to end, cited as for a stage's (Step 3), and leave it empty otherwise. A limit a
source states is an objective (the measures skill's step "Propose the measures", the parties and their expectations). The four declarations and `delivers` (Step 8) are **required** for the view
*How a case moves end to end*; whom it serves is led by the parties' expectations (the measures skill's step "Propose the measures", the parties and their expectations).

**Everything before the case exists belongs to another flow.** Browsing, filling a basket, signing in, filling
in a form: real work, and set aside for this one. Write each in `set-aside.csv` with kind `other flow` and the
evidence, so a reader sees it was looked at. If the business would call something before the record its start,
say so in that row; it is a finding about where the record is created, not a stage of this flow. **Each piece of
work set aside as `other flow` is also a row in `flows.csv` now**, with its own case and no stages: the capability
carries it, and it is walked separately (Step 8).

If several kinds of case are plausible, name them: the choice is the person's, made at the plan's go (Before you
start, item 7), where each is listed with a recommendation and its reason; the run does not pick. Here, take the one
the person chose. If the source holds no case at all,
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
  `from_state` with nothing to move it; lost; failed back to the party. Cite it. This is the summary; the stage kit's step "The failure modes, the alerts and the runbook for a stage" reads
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
  an objective, written in the first part of the measures skill's step "Propose the measures" in `expectations.csv` → `objective`. Where the code's limit and a stated
  objective disagree (the code marks a case overdue after 5 days, and the customer is told "1-2 weeks"), keep both:
  neither is corrected to the other, and the stage card shows the two side by side as a finding. The parties'
  expectations (the measures skill's step "Propose the measures", the parties and their expectations) are the stage card's main content; *How a case moves through this stage* also needs the
  entry, the main exit and what is at stake (Step 10). A stage with no alternative or exception
  exit is gapped `does not apply` for its other outcomes.
- `arrivals_per_period`: `not stated: measured by the operators`, unless they give it.
- Do not merge or split to reach a count.

**Then check the cut against the domain's reference model** (APQC's process classification, SCOR, the domain's
standard process), from the starting event to the ending only. A stretch the reference model expects inside
that frame that no lifecycle row carries is added as a stage or process step with no participation, drawn as not
assessed. A stretch the reference model puts before the case exists is set aside (Step 1).

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

**Which of the agent's actions are its decisions.** Class them here: it is a fact about who decides at a process
step, read from the tool's arguments and the agent's code. Proposing the measures, later in the run, asks its questions
of each one classed `yes:`; a run that stops at the map needs only the classes.

**Class each tool first.** On every participation row of an agent, write `decision_point`. A tool call is a
decision point, `yes:`, when the agent chooses a value that becomes the case's outcome or a person's basis for
deciding it: a recommendation, a decision type, a condition's text, the inputs to a risk computation. A call that
only records what a person stated or asked for is an action, `no:`: entering the borrower's details, acknowledging
a disclosure. Class it by reading what the tool's arguments carry, and cite the signature. A tool that computes by
fixed rules is a decision point only through the arguments the agent chose to pass it; say which. One agent's tool
is classed one way on every row. Mapping's done check and its inspection fail on an agent row not classed, and on a
tool classed both ways.

**A tool whose class depends on the conversation is a decision point.** The same call can record an item the
person named, or choose one the person only described (an add-to-basket call given a product's name against one
given "something warm for winter"; an add-pet call with the owner the person named against the owner the model
picked from a list). One class per row stays: write `yes:`, and the reason says **when** the call carries the
agent's choice.

**Then class each reply.** The agent's reply to a person is a decision point when the person relies on it: it
reports or explains a result, such as a recommendation, a risk assessment or a check's outcome.
Its operation is the agent's turn, not a tool, so a tool computed by fixed rules (classed `no:`) can still be
reported by a reply that is a decision point. On the agent's row for that process step, write `reply_decision_point`:
`yes:` where the person relies on the reply, `no:` where it only confirms what the person asked, asks for more, or
replies to no person at that process step, and why, citing the prompt or the code that hands the tool's result to the
model. The done check and the inspection fail on an agent row whose reply is not classed.

**A model output a later call relies on is its own decision point.** Where the agent's chain writes something
with one model call and a later call decides from it (a description of a room written from a photo, then fed to
the call that chooses products), that first output is a judgment no tool or reply holds. Class it on the action row
of `agent-system.csv` that makes the call, in `decision_point`: `yes:` and why, citing the line that feeds it on.
Do not class an action whose output a tool's or a reply's decision point already holds: the model's choice of a tool's arguments is that
tool's decision point.

## Step 8. Name the capability, twice (*Assigning* Steps 2 and 7)

1. **From the walk:** what the whole path is for, what the business is thereby able to do, named apart from how
   it is built. The narrowest ability this flow delivers.
2. **From the sources, in a pass that has not seen the walk:** what the documents say the organisation is able
   to do (a separate session or subagent given only the documents).

Write `capabilities.csv`: one row per capability, with both routes in `basis`. If they agree, say both
produced it. If they disagree, keep both rows and say so; do not smooth them into one. A capability the sources
name that the walk does not deliver is kept, delivered by no flow. When you tell the person about one, say in plain words
what it means and what they can do: only the documents name it, and no flow found in the code delivers it; if a flow
of the system does carry it, they can name that flow, and it is added as a flow still to map; if not, it can be left,
and it changes nothing in the map. Fill `flows.csv` → `delivers`.

If an AI agent serves several flows, the register covers the lowest capability that holds all of them. List the
other flows the capability carries in `flows.csv`; each is its own frame and walk, and a flow not yet walked has
no stages.

The step that comes between Step 8 and Step 10, "Propose the measures", is the measures skill's (`bfo-measures`, its
`MEASURES-STEPS.md`): this file does not carry it.

## Step 10. Record Business Impact (*Rules*, Rule 3)

Part of mapping: done right after Step 8, for every stage of the flow, before the person picks how far each stage
goes, so the pick shows what each stage's failure costs, and before the measures skill's step "Propose the measures", which measures every process step with a
Business Impact row. For each lifecycle move whose `if_not`
hurts the case, a `step-impact.csv` row on the process step it belongs to: the
category from `method/impact.csv`, the unit counted in cases, and `recovery` copied from the lifecycle. A case
acknowledged to the party and then lost fits no recovery value: leave `recovery` blank and begin `note` with
`lost after acknowledgement:` and the evidence. In `case-attributes.csv`, what is at stake in one case:
`what_is_at_stake` is required for *How a case moves through this stage*.
