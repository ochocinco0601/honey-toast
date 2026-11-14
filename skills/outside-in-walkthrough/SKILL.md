---
name: outside-in-walkthrough
description: Walk the stakeholder through how something will behave, step by step from their chair, on concrete screens and words beside today's behaviour, before it is designed in detail or built, and make the design from their reactions. Use when the person says "outside-in walkthrough", "walk me through how it will behave", "how will this behave", "do I just get to discover it once it's changed?", and before designing or building a change to how something behaves for the stakeholder (a skill's run or stops, a tool's first reply, a page or screen, the order of what they are asked), from the first idea onward. Not for copy edits, for fixes that restore behaviour already designed, for reviewing finished output (artifact-review), or for evaluating a dashboard on its own (dashboard-evaluation, which this skill uses for screens).
---

# Outside-in walkthrough

## The job this serves

**Two levels up:** the stakeholder (the person directing the work) steers and judges it while sessions do the engineering, and never has to open a black box hours or days later to find something they did not want. **One level up:** whatever is being designed fits the stakeholder's work the first time they use it. **This step:** before the design is detailed or built, the stakeholder experiences its behaviour scene by scene and reacts, and the design is made from those reactions. Its place in the lifecycle: envisioning, in Disciplined Agile's Inception or before any iteration that changes what the stakeholder sees.

**It receives** an initiative or a proposed change, from the person or from the session doing the work, and the existing record: the built thing and its screens, the stakeholder's recorded rulings and requirements, or, before anything is built, how the work is done today.

**It hands on** a walkthrough file with a confirmed reading of the stakeholder's call on every happy-path scene, to the design and build work, which builds from those readings; and it stays with the build until the built thing has been checked against them.

**Done for the whole job:** what gets built behaves the way the stakeholder pictured, so their first look at it confirms rather than surprises. The walkthrough part is done when every happy-path scene has a confirmed call, no scene they flagged is open, and they say so; the session never declares it done. The whole is done when the stakeholder has seen the built thing beside the walked scenes (step 17).

**Field terms:** outside-in development (behaviour-driven development's term; not Given/When/Then test code), the structured walkthrough (Yourdon), user-centred design (ISO 9241-210), design critique, decision log.

## The run

### Prepare (the session's work, before the stakeholder sees anything)

0. **If a confirmed walkthrough already exists for this change** (its file beside the work's other records), go to step 17: the work is at build, not at the walk.
1. **Start from what already exists.** Read the built thing, its current screens, and the stakeholder's recorded rulings and requirements first; before anything is built, how the work is done today. Confirmed rulings bind; reactions recorded but not confirmed are evidence, shown as such. Never re-derive a requirement they already stated.
2. **Use the most real case available.** A real record or system when one exists, because it cannot hide the hard parts (a worked example built from real code counts); otherwise an invented case that is still concrete, named and with numbers, and labelled invented. Check earlier walkthrough files (their headers name the case) and use a different one.
3. **Find the real entry points.** How the thing is started, what a person actually types (imprecise, half-formed), how that is read, and the first response for each kind of input. For a part of a larger tool, each way a person actually arrives at it. If two tools claim the same request, find out which answers today (a cold run of the request, or failing that the descriptions) and show that. Never open on a tidied request.
4. **Show today as it is today.** Render today's screens and replies from today's code; if rendering writes files, do it in a copy of the record, never the original.
5. **Lay out the happy path** in the product's own sequence (its progress steps, if it has them), critical path first; other situations hang off the step where they happen. Treat that sequence as input the stakeholder reconciles when they reach it, not as settled.
6. **Make the walkthrough file** in the folder where the work's records live (create one if none exists): scenes, a decisions section, and a header naming the case used and carrying step 17's rule, so a build session that opens the file sees it.

### Walk (one scene at a time, led by the session, in the chat)

7. **Where the walk happens.** In the chat, each scene shown inline. When a scene is a screen, open the rendered page on their screen at that spot. The walkthrough file is the record, never the place they are sent to read.
8. **The first message** names the scenes in one line, then gives scene 1. Within each scene the question comes first.
9. **Each scene, in this layout:**
   - **The question, first and alone.** It asks for fit: could they use this, in their situation, against any standard they have set for the user (for example, a reader who knows neither the tool nor the system). Never a line-by-line audit, never a yes/no on the session's reasoning.
   - **Whose chair.** The stakeholder's, judged against their standard. Where the product's actual user is someone else (a responder opening a runbook when an alert fires), that person's moment of use gets its own scene.
   - **What they would see:** the actual words and screens, quoted or rendered, never a description in their place. For a long artifact, the part met at the moment of use, with a link to the whole.
   - **Today, beside it,** quoted or rendered the same way.
   - **The new behaviour:** a concrete proposal labelled "proposed", wherever an established pattern or their recorded rulings give an answer. "Not settled" only where the choice is genuinely theirs and nothing answers it; then show each option concretely.
10. **A scene they flag comes back fixed before the next scene.** Recording a reaction is not acting on it.
11. **Keep their pace and proportion.** Do not restructure ahead of them. An example they call trivial is evidence for their point, not the work item: answer the point, fix the example in one move, go on.
12. **Reviewers run alongside, never as a gate.** Launch them as scene 1 goes out: the `independent-discipline-reviewer` agent with the lens `visual-usability`, plus `design:ux-copy` and `design:design-critique` where those plugin skills are installed (tell the reviewer to load them through the Skill tool), one pass over the scenes plus a re-check of any scene that changes, with the stakeholder's own rulings as their first standard (a fix that breaks a ruling is reported, not applied). Findings go beside the walkthrough file and fold into later scenes; a passed scene is re-shown only if a fix changes what they see.
13. **For a screen, start from needs shown as moments of use** ("the run started three hours ago and you come back: this box shows ..."), never a bare list, worked when that screen's scene is reached. Evaluate it element by element by established practice: the question, decision or need each element serves, why it exists, whether it does that (the `dashboard-evaluation` skill). Cut what repeats or says nothing.

### Decide and record

14. **Record a reading of what they decided, never the session's wording around it.** Write the decision in the field's terms, keep their words beside it, read it back to them, and mark it confirmed or unconfirmed; silence is not a yes. The form stays open unless they ruled on it.
15. **Who decides what.** Engineering choices are the engineers'. Choices that change what the stakeholder experiences are theirs, except where an established pattern answers them (a review step for a confirmation, structured fields instead of prose): then the engineers apply the pattern and show the result for reaction. Asking them to pick the pattern makes them the expert. "Make it lean" cuts what is built; it never hands their experience choices to the session or ends the walkthrough early.
16. **Never write a call they did not make.** Whatever the session writes down becomes the ruling, so it records only readings of calls they made, read back. Log each in the decisions section with their words and the time, and build every later version from the log, never re-reasoned from scratch. Situations off the happy path may carry the session's proposal, marked unconfirmed; they do not hold up done.

### After the walkthrough (it stays with the build)

17. **The build follows the log.** Any build change that alters a walked scene, or a scene that cannot be built as walked, goes back to the stakeholder as a re-walked scene before it ships. When it is built, they see each built scene beside the walked one, and any difference is either fixed or walked again.

## Gotchas

- **Too much or too little.** Sessions swing between every possible situation at once and four bare step names with nothing in them. The cure is the happy path, one scene at a time, each with its real screen.
- **A list is not a walkthrough.** Needs, rules or options handed over as a list sit at the top of the ladder of abstraction; come down to the concrete moment.
- **"Doing next" with nothing running.** Never end a turn saying what comes next unless it is already running; otherwise say "Stopped." and what it waits on.
- **Burying the question.** If the stakeholder has to ask "my answer to what?", the scene layout was not followed.
