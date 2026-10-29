# The kit's checks

Every check the kit runs, one row each. `capability_views.py --check` and `flow_outputs.py --check` report the errors
and warnings; `run_status.py` says NOT DONE for the rest. The rule that keeps this list bounded is in
`register-template/REGISTER.md`, "What a finding in a register changes": a finding in a register adds no check.

Every check in the code has a row here, and every row here names a check in the code.
A row is tied to its check by the module, the function and the lead words of its message: the message holds
the lead words (`=` before them: the message is exactly that). The line is where the check sat at the commit that
last changed this file (`git log -1 -- CHECKS.md` names it); the lead words find it after the code moves.

Class: **a** structure (a table, a column, a cell's own value or format; `a*` needs a value from another row),
**b** integrity (an id resolves in another table, or two tables agree about one relationship), **c** coverage
(every element of a set is answered or gapped), **d** residue (a text heuristic, a domain advisory, freshness or
the run's process).

## The checks in code

| id | module | function | line | severity | class | lead | guards |
|---|---|---|---|---|---|---|---|
| cv-01 | capability_views.py | read_csv | 51 | error | a | {len(reader.fieldnames) + len(extra)} fields | Row arity equals header |
| cv-69 | capability_views.py | declared_value_failures | 139 | warning | a | is not one of the values REGISTER.md declares | each value of a column REGISTER.md declares a `One of:` list for is in that list (today subjects.band, lifecycle.from_kind and path, measures.form and receipt_question); a warning, so no register in use turns red |
| cv-02 | capability_views.py | column_failures | 179 | error | a (migration) | {'; '.join((f'{o} is now | Renamed column |
| cv-03 | capability_views.py | column_failures | 186 | error | a | {t}.csv has no {', | every column REGISTER.md defines, Optional ones aside, is present (read from REGISTER.md) |
| cv-04 | capability_views.py | column_failures | 193 | warning | a (migration) | {RETIRED[t, c]} | Retired column present |
| cv-05 | capability_views.py | column_failures | 197 | warning | a | {', '.join(extra)} {'are' if | no column REGISTER.md does not define (read from REGISTER.md) |
| cv-06 | capability_views.py | unique | 245 | error | a | a row has no | the id column is filled, in capabilities, flows, stages, steps, subjects, measures |
| cv-07 | capability_views.py | unique | 247 | error | a | {col} {v} appears twice | the id is unique, in the same six tables |
| cv-08 | capability_views.py | check | 252 | error | a | needs exactly one row, | Cardinality 1 |
| cv-09 | capability_views.py | check | 261 | error | b | parent {r['parent']} is not | capabilities.parent -> capability_id |
| cv-10 | capability_views.py | check | 264 | warning | a | delivers no capability | flows.delivers is filled; the same rule gates view question `flow: delivers` (vq-q19), where it is not a warning but a gate |
| cv-11 | capability_views.py | check | 267 | error | b | delivers {c}, which is | delivers -> capabilities |
| cv-12 | capability_views.py | check | 270 | error | b | =stages.csv {r['stage']}: flow {r.get('flow')} is not a flow | stages.flow -> flows |
| cv-13 | capability_views.py | check | 272 | error | a | order {r.get('order')} is not | stages.order integer |
| cv-14 | capability_views.py | check | 275 | error | b | stage {r.get('stage')} is not | steps.stage -> stages |
| cv-15 | capability_views.py | check | 277 | error | b | business_subject {r['business_subject']} is not | steps.business_subject -> subjects (does not check it is a `case`) |
| cv-16 | capability_views.py | check | 280 | error | a | qualifier must start with | steps.qualifier starts `partial:` or `stub:` |
| cv-17 | capability_views.py | check | 284 | error | a | kind must be element | subjects.kind is element or relationship |
| cv-18 | capability_views.py | check | 286 | error | a | level {r['level']} is not | subjects.level is component, external dependency or blank |
| cv-19 | capability_views.py | check | 289 | error | a | part_kind {pk} is not | Enum from method list |
| cv-20 | capability_views.py | check | 293 | error | b | {c} {r.get(c)} is not | Interaction ends -> subjects |
| cv-21 | capability_views.py | check | 296 | error | b | step_hint {h} is not | -> steps |
| cv-22 | capability_views.py | check | 298 | error | a | a {pk} has no | subjects.level is blank where the part_kind's family is case, interaction or person |
| cv-23 | capability_views.py | check | 301 | error | a (migration) | subjects.csv has no purpose | subjects.csv has the purpose column; said in place of cv-03, with what to do |
| cv-24 | capability_views.py | check | 306 | error | a | no purpose; write what | subjects.purpose filled on a part row; the same rule as view question `part: purpose` (vq-q06) |
| cv-25 | capability_views.py | check | 310 | error | a (migration) | subjects.csv has no repository | subjects.csv has the repository column; said in place of cv-03, with what to do |
| cv-26 | capability_views.py | check | 323 | error | d (text) | a component with no repository that | a component with no repository whose name, purpose or source says it is not separately built |
| cv-27 | capability_views.py | check | 328 | error | a | a system component with | subjects.repository filled on a system component, or its source says no repository defines it |
| cv-28 | capability_views.py | check | 334 | error | a | a component with no repository; | subjects.repository filled on an application component |
| cv-29 | capability_views.py | check | 345 | error | a | part_of is only for | Conditional: part_of only when level is external dependency |
| cv-30 | capability_views.py | check | 347 | error | b | part_of {po} is not | subjects.part_of -> a subject of level external dependency |
| cv-31 | capability_views.py | check | 349 | error | b | part_of {po} is itself | One level deep |
| cv-32 | capability_views.py | check | 362 | error | a | sequence {o} is not | subjects.sequence is a whole number |
| cv-33 | capability_views.py | check | 364 | error | b | sequence names step {st | Two columns of one row agree |
| cv-34 | capability_views.py | check | 366 | error | a | sequence {o} in step | Compound unique (step, order) |
| cv-35 | capability_views.py | check | 371 | warning | a | list each source with | Table present |
| cv-36 | capability_views.py | check | 374 | error | b | =participation.csv: subject {r.get('subject_id')} is not a subject | participation.subject_id -> subjects |
| cv-37 | capability_views.py | check | 376 | error | b | =participation.csv: step {r.get('step')} is not a step | participation.step -> steps |
| cv-38 | capability_views.py | check | 378 | error | a | involvement {r.get('involvement')} is not | Enum (method/involvement.csv) |
| cv-39 | capability_views.py | check | 382 | error | b | =measures.csv {h}: subject {r.get('subject_id')} is not a subject | measures.subject_id -> subjects |
| cv-40 | capability_views.py | check | 384 | error | b | step {r['step']} is not | measures.step -> steps |
| cv-41 | capability_views.py | check | 386 | error | a | layer {r.get('layer')} is not | Enum with aliases |
| cv-42 | capability_views.py | check | 388 | error | a | counted_on {r.get('counted_on')} is not | measures.counted_on is cases, events, requests, resources or runs |
| cv-43 | capability_views.py | check | 390 | error | a | exists must be yes | measures.exists is yes, no or blank |
| cv-44 | capability_views.py | check | 392 | error | b | flow {r['flow']} is not | measures.flow -> flows |
| cv-71 | capability_views.py | check | 407 | error | a (migration) | agent_question {r['agent_question']} is now | Renamed measures.agent_question value (operations is now operating health) |
| cv-45 | capability_views.py | check | 394 | error | a | agent_question {r['agent_question']} is not | Enum from method list |
| cv-46 | capability_views.py | check | 396 | warning | a | a business measure counts | Same-row conditional value |
| cv-47 | capability_views.py | check | 399 | error | b | =step-impact.csv: step {r.get('step')} is not a step | step-impact.step -> steps |
| cv-48 | capability_views.py | check | 401 | error | a | impact_category {r.get('impact_category')} is not | step-impact.impact_category is in method/impact.csv |
| cv-49 | capability_views.py | check | 403 | error | a | recovery must be 'moves | step-impact.recovery is moves on, stranded, not created or blank (RECOVERY) |
| cv-50 | capability_views.py | check | 406 | error | b | =case-attributes.csv {r.get('attribute')}: flow {r.get('flow')} is not a flow | case-attributes.flow -> flows |
| cv-51 | capability_views.py | check | 416 | warning | b | its case {sid} is | Conditional-required through a join |
| cv-52 | capability_views.py | check | 423 | error | b | agent {a} is not | agent-system.agent -> a subject whose part_kind is an agent kind |
| cv-70 | capability_views.py | check | 442 | error | a (migration) | element {r['element']} is now | Renamed agent-system.element value (operation is now action) |
| cv-53 | capability_views.py | check | 425 | error | a | element must be one | agent-system.element is run, action, agent part or dependency |
| cv-54 | capability_views.py | check | 430 | error | a | agent {a} repeats an | Compound unique (agent, id) |
| cv-55 | capability_views.py | check | 432 | error | a | agent {a} needs exactly | Per-group cardinality |
| cv-56 | capability_views.py | check | 436 | error | b | performed_by {p} is not | agent-system.performed_by -> an agent part of the same agent |
| cv-57 | capability_views.py | check | 439 | error | b | uses {p} is not | agent-system.uses -> a dependency of the same agent |
| cv-58 | capability_views.py | check | 442 | error | a | next is for the | Conditional column |
| cv-59 | capability_views.py | check | 444 | error | b | next {p} is not | agent-system.next -> an action of the same agent, or end |
| cv-60 | capability_views.py | check | 448 | error | b | serves_business_step {s} is not | agent-system.serves_business_step -> steps |
| cv-61 | capability_views.py | check | 451 | error | b | subject_id {s} is not | agent-system.subject_id -> subjects |
| cv-62 | capability_views.py | check | 453 | warning | c | an agent with no | Every agent subject has a block |
| cv-63 | capability_views.py | check | 457 | error | a | kind {r.get('kind')} is not | sources.kind is code, document, person or tool output |
| cv-64 | capability_views.py | check | 459 | error | a | pass {r.get('pass')} is not a number | sources.pass is a whole number |
| cv-65 | capability_views.py | check | 463 | error | b | pass {r.get('pass')} is not a pass | how-made.pass -> a pass in sources.csv |
| cv-66 | capability_views.py | check | 466 | error | a | done_by {x} is not | Enum list |
| cv-67 | capability_views.py | check | 472 | warning | d (text) | no citation | CITE regex over cells |
| cv-68 | capability_views.py | bound_failures | 501 | error | d (text) | bound_in_code {v} cites no | flows/stages.bound_in_code that names a time limit cites code; also run by flow_outputs.py --check for its flow and stage |
| fo-01 | flow_outputs.py | old_remedy_id_failures | 59 | error | a (migration) | remedy {', '.join((f'{x} is | Old id form |
| fo-02 | flow_outputs.py | expectation_failures | 347 | error | b | `expectation` names {', '.join(unknown)}, | measures.expectation -> expectations |
| fo-03 | flow_outputs.py | expectation_failures | 354 | error | a | objective {obj} is proposed; | expectations.objective is not `proposed` |
| fo-04 | flow_outputs.py | expectation_failures | 357 | error | a | objective is set with | dependentRequired |
| fo-05 | flow_outputs.py | chain_failures | 530 | error | a | decision_point is set on | Conditional column |
| fo-06 | flow_outputs.py | chain_failures | 533 | error | a | class it in decision_point, | agent-system.decision_point starts `yes:` or `no:` |
| fo-07 | flow_outputs.py | class_failures | 558 | error | a* | class the agent's reply | Required on rows whose subject is an LLM agent |
| fo-08 | flow_outputs.py | class_failures | 564 | error | a* | class its tool as | participation.decision_point classes the tool of an LLM agent's operation |
| fo-09 | flow_outputs.py | class_failures | 573 | error | b | classed yes at step | One (agent, tool) has one class across rows |
| fo-10 | flow_outputs.py | gap_rows | 735 | warning | c | the code sets no | Gap names a non-element |
| fo-11 | flow_outputs.py | gap_rows | 739 | error | c | {key[1]} is a view | From the vq CONTRACT |
| fo-12 | flow_outputs.py | gap_rows | 743 | error | a | question {key[1]} is not | Enum (vocabulary built from the receipt and vq) |
| fo-13 | flow_outputs.py | gap_rows | 747 | error | a | no {' and no | Required |
| fo-14 | flow_outputs.py | gap_rows | 753 | error | a | {said}, so it does | measure-gaps.kind is one of the four gap kinds |
| fo-15 | flow_outputs.py | gap_rows | 757 | error | b | `kind` is `counted by`, | a `counted by` gap's reason names a measures.csv handle |
| fo-16 | flow_outputs.py | gap_rows | 763 | error | a | {why_not}, so it does | a view-question gap passes the rule of that question (vq-01 to vq-03) |
| fo-17 | flow_outputs.py | gap_rows | 766 | warning | c | names nothing the receipt | Gap names a non-element |
| fo-18 | flow_outputs.py | gap_rows | 768 | warning | c | a candidate in measures.csv | False gap |
| fo-19 | flow_outputs.py | citation_failures | 789 | warning | b (FK in text) | a citation starts with | Citation prefix -> sources.repository |
| fo-20 | flow_outputs.py | receipt_failures | 884 | warning | c | whose own run errors on it | the receipt, for an element of another stage: a warning, since its own run errors on it |
| fo-20m | flow_outputs.py | receipt_failures | 882 | warning | c | not measured in this run | the receipt, where the person chose which stages to measure: an element only of stages not measured is a warning, never owed |
| fo-21 | flow_outputs.py | receipt_failures | 808 | error | c | ={msg} | the receipt: each element of the run's stage or flow is covered by a measure or gapped |
| fo-21p | flow_outputs.py | person_text_failures | 426 | error | c | a person reads when reviewing this alert | an alert's basis, question and guarded expectations, as the person reviewing it reads them, carry no id, file name or kit term (the review's own term list) |
| fo-22 | flow_outputs.py | watched_failures | 827 | error | a | watched is set and | Same-row conditional |
| fo-23 | flow_outputs.py | watched_failures | 830 | error | a | watched {w or 'blank'} | measures.watched is yes, in the app only, no or unknown |
| fo-24 | flow_outputs.py | watched_failures | 832 | error | a | watched is {w} with | dependentRequired |
| fo-25 | flow_outputs.py | watched_failures | 835 | error | a | watched is {w} on | Same-row conditional |
| fo-73 | flow_outputs.py | counted_at_failures | 953 | error | a | and says no counted_at | dependentRequired: a measure with a source_ref names the place it is counted at; run_status.py says NOT DONE on the same rows |
| fo-75 | flow_outputs.py | counted_at_failures | 1010 | error | a | counted_at names {hit}, a name only | measures.counted_at is a plain name, never a code identifier (flow_outputs.code_name: backticked, a quoted word not a log line, snake_case, an inner capital starting a word, a dotted lower-case name not a file, host or number) |
| fo-76 | flow_outputs.py | same_place_failures | 985 | error | b | the same counted_at | two measures naming the same place agree on exists |
| fo-74 | flow_outputs.py | check | 1116 | warning | a | measures.csv has no counted_at column | a register made before counted_at existed is told to add it, filled from each row's citation |
| fo-26 | flow_outputs.py | check | 844 | error | b | lifecycle.csv names {tok} in | lifecycle.carried_by and needs -> subjects, by id or name |
| fo-27 | flow_outputs.py | check | 849 | warning | c | {msg}, so it is | a step has moves: a step view_questions.moves_excuse excuses is drawn not assessed |
| fo-28 | flow_outputs.py | check | 851 | error | c | {msg}; only a step no part carries | a step has moves, or view_questions.moves_excuse excuses it: a step no part carries, by a gap the view question `step: moves` also counts, or as a step the reference model adds, which the view question counts as does not apply |
| fo-29 | flow_outputs.py | check | 855 | error | c | lifecycle {mv} leaves {state(moves[mv]['from_state'])}, | Every move from a stage state is placed |
| fo-30 | flow_outputs.py | check | 859 | error | a | travels_by hop {h[1:]} is | Enum (method/hop-failures.csv) |
| fo-31 | flow_outputs.py | check | 863 | warning | b | performs {sorted(perf)}; the lifecycle's | participation equals lifecycle.carried_by |
| fo-32 | flow_outputs.py | check | 874 | warning | b | step_hint {h} names a | Interaction within lifecycle.needs |
| fo-33 | flow_outputs.py | check | 881 | warning | b | its lifecycle needs {d} | lifecycle.needs within interactions |
| fo-34 | flow_outputs.py | check | 887 | warning | b | a do not remedy | Orphan |
| fo-35 | flow_outputs.py | check | 893 | error | a | hop {r['hop']} is not | failure-modes.hop is a hop kind in method/hop-failures.csv |
| fo-36 | flow_outputs.py | check | 895 | error | a | mode {r['mode']} is not | Enum conditional on hop (composite method key) |
| fo-37 | flow_outputs.py | check | 898 | error | b | move {mv} is not | failure-modes.moves -> lifecycle |
| fo-38 | flow_outputs.py | check | 902 | error | b | part {r['part']} is not | failure-modes.part is in the move's carried_by (or needs, for a needs hop) |
| fo-39 | flow_outputs.py | check | 905 | error | b | lifecycle {mv} does not | failure-modes.hop is one the move travels by |
| fo-40 | flow_outputs.py | check | 911 | error | b | part {x} of the | each part of a sweep test is in a listed move's carried_by or needs |
| fo-41 | flow_outputs.py | check | 915 | error | b | a sweep test covers | Joined values equal |
| fo-42 | flow_outputs.py | check | 918 | error | a | order {r['order']} is not | failure-modes.order is a whole number |
| fo-43 | flow_outputs.py | check | 921 | error | a | ending {ending} is not | failure-modes.ending is one of the endings (ENDINGS) |
| fo-44 | flow_outputs.py | check | 924 | error | a | recovery {r['recovery']} is not | failure-modes.recovery is moves on, stranded or not created (RECOVERY, shared with cv-49) |
| fo-45 | flow_outputs.py | check | 927 | error | a | a mode ruled out | Same-row conditional pattern |
| fo-46 | flow_outputs.py | check | 931 | error | a | no {col} | Conditionally required |
| fo-47 | flow_outputs.py | check | 934 | error | b | measure {h} is not | failure-modes.measures -> measures |
| fo-48 | flow_outputs.py | check | 937 | error | b | remedy {r['remedy']} is not | failure-modes.remedy -> remedies |
| fo-49 | flow_outputs.py | check | 939 | error | d (declarable) | ending restore needs a | Join plus value |
| fo-50 | flow_outputs.py | check | 941 | error | d (declarable) | the case is stranded, so its remedy | Join plus value |
| fo-51 | flow_outputs.py | check | 944 | error | a | the case is stranded, so its ending | Same-row conditional |
| fo-52 | flow_outputs.py | check | 947 | error | a | defect is set and | Same-row conditional |
| fo-53 | flow_outputs.py | check | 955 | error | a | kind {rem.get('kind')} is not | remedies.kind is restore, re-drive, roll back, none exists or do not |
| fo-54 | flow_outputs.py | check | 959 | error | d (text) | {col} names a runbook section ({x}); the register does not know the runbook's sections: | Regex over remedy text |
| fo-55 | flow_outputs.py | check | 963 | error | d (text) | {col} names {', '.join(named)}, | Regex over remedy text |
| fo-56 | flow_outputs.py | check | 969 | error | d (text) | =failure-modes.csv {r.get('mode_id', '?')}: {col} names a runbook section ({x}); the register does not know the runbook's sections | Regex over failure-mode text |
| fo-57 | flow_outputs.py | required_failure_rows | 965 | error | c | no failure mode at | FMEA coverage |
| fo-58 | flow_outputs.py | required_failure_rows | 971 | error | c | hop {h}, mode {c['mode']} | move x hop x catalogue mode |
| fo-59 | flow_outputs.py | required_failure_rows | 979 | error | c | need {need} ({name(M, need)}), | move x need x needs-mode |
| fo-60 | flow_outputs.py | required_failure_rows | 984 | error | c | carrier {part} ({name(M, part)}) | move x carrier |
| fo-61 | flow_outputs.py | check | 1000 | error | d (declarable) | same measures and same | Unique (derived branch, measures, seen) |
| fo-62 | flow_outputs.py | check | 1067 | note (printed as `note:`, never stops the outputs) | d | proposed for alerting on its | Reports where an alert not on a stage's count of cases is drafted: every stage it reaches (its step's stage, every stage of its flow, or each stage its part serves), or that it reaches none. Was an error in earlier releases: the register says which measures alert, at any level |
| fo-63 | flow_outputs.py | check | 1073 | note (printed as `note:`, never stops the outputs) | d | no alert is proposed on stage | Reports a stage with no alert reaching it: no ALERT page is written and its runbook says so. Was an error ("each run stage has at least 1 alert") in earlier releases: whether to alert is the team's decision |
| fo-64 | flow_outputs.py | check | 1078 | warning | a | proposed for alerting with | measures.alert proposed for alerting starts `yes:` with its basis, on every drafted alert at any level |
| fo-65 | flow_outputs.py | check | 1091 | error | a | counts cases leaving the | Conditionally required (form not backlog or cycle time), on an alert of the stage counted on cases |
| fo-66 | flow_outputs.py | check | 1081 | error | a | proposed for alerting, and | measures.expectation filled on every drafted alert at any level; fo-02 checks the ids it names, and view question `alert: expectation it guards` (vq-q20) that one is known |
| fo-67 | flow_outputs.py | check | 1096 | error | b | `counted_moves` names {', '.join(unknown)}, | measures.counted_moves -> lifecycle |
| fo-68 | flow_outputs.py | check | 1100 | error | b | `counted_moves` names {', '.join(other)}, | measures.counted_moves -> a move of the measure's stage |
| fo-69 | flow_outputs.py | check | 1043 | warning | d | its runbook entry works | Domain advisory |
| fo-70 | flow_outputs.py | check | 1051 | warning | d | cases wait in it | Domain advisory |
| fo-71 | flow_outputs.py | check | 1056 | warning | d | no move leaves a | Domain advisory |
| fo-72 | flow_outputs.py | check | 1063 | warning | d | cases leave it by | Domain advisory |
| vq-01 | view_questions.py | refusal | 84 | error | a | {q} takes only a | Conditional enum |
| vq-02 | view_questions.py | refusal | 86 | error | b | {q} is gapped only | No participation rows for the element |
| vq-03 | view_questions.py | refusal | 88 | error | d (text) | the reason cites no | CITE regex |
| rs-01 | run_status.py | view_questions | 174 | not done | c | {q} {len(C[q]['empty'])} empty | each view question that gates is answered or gapped, for each element owed (vq-q01 to vq-q24) |
| rs-02 | run_status.py | view_questions | 177 | not done | d (process) | {q} {len(unread)} gapped not | a gap of kind `not read` does not pass on a first run |
| rs-03 | run_status.py | split_checks | 72 | not done | d (process) | rows not judged by | in a split run, every unit's rows are judged by the number of judges run-settings.json sets (default three) and flagged rows judged again, read from the transcripts (judges.py) |
| rs-04 | run_status.py | split_checks | 54 | not done | d (process) | the map is not the | in a split run, the map's tables are what a merge of the unit folders gives, every call matched or listed (merge.py) |

## The view questions that gate

`view_questions.CONTRACT`. `run_status.py` says NOT DONE while one is empty for an element owed (rs-01). A question
that is `count only` is counted and never gates, so it has no row.

| id | question | contract |
|---|---|---|
| vq-q01 | step: moves | required |
| vq-q02 | step: trigger | answer or gap |
| vq-q03 | step: right outcome | required |
| vq-q04 | step: if it does not happen | required |
| vq-q05 | step: timeouts | answer or gap |
| vq-q06 | part: purpose | required |
| vq-q07 | part: operations | answer or gap |
| vq-q08 | part: depends on | answer or gap |
| vq-q09 | stage: a case enters | required |
| vq-q10 | stage: expected outcomes | required |
| vq-q11 | stage: other outcomes | answer or gap |
| vq-q12 | stage: cannot be undone | answer or gap |
| vq-q13 | stage: at stake | required |
| vq-q14 | stage: expected by each party | required |
| vq-q15 | flow: one case | required |
| vq-q16 | flow: starts | required |
| vq-q17 | flow: ends | required |
| vq-q18 | flow: serves | required |
| vq-q19 | flow: delivers | required |
| vq-q20 | alert: expectation it guards | required |
| vq-q21 | alert: contain first | required |
| vq-q22 | alert: its own tests | answer or gap |
| vq-q23 | expectation: satisfied when | required |
| vq-q24 | expectation: indicator | answer or gap |

## What run_status.py reports besides

| id | module | function | severity | class | lead | guards |
|---|---|---|---|---|---|---|
| rs-s1 | run_status.py | main | not done | c | no stage has had Step 11 | at least one stage is owed |
| rs-s2 | run_status.py | main | not done | c | else 'MISSING' | every output owed exists and is not empty |
| rs-s3 | run_status.py | stale | not done | d (freshness) | no record of the register it was generated from | a stage output carries the stamp of the register it was generated from |
| rs-s4 | run_status.py | stale | not done | d (freshness) | changed since it was generated | the register's tables are as they were when the output was generated |
| rs-s5 | run_status.py | view_questions | not done | d (process) | view questions not counted | the view questions can be counted (the generators read the register) |
