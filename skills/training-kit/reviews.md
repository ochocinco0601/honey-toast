# Review briefs

Each pass is run by a reader that did not build the kit: a fresh session or a subagent. Give it the
brief below with each part in angle brackets filled in, the path to the kit and to its `sources`
folder, and nothing else: not your notes, not your opinion of the kit, not earlier reviews. Its report comes back to
you; you decide what to fix. When the review ends is set by four pass-or-fail checks (SKILL.md, step 7),
not by how many findings a brief returns.

Fill `<learner>` from the kit's settings table: who the learners are, by the work they do, what
they know of this subject, and how expert they are in their own work. Describe the learner. Do not
describe the kit.

## 1. First-time learner walk

> You are <learner>. You have never seen this training and have no one to ask. Open <path to the kit>/read-in-browser/README.html and follow the path from the first page, doing every step as written in <where practice happens>, or saying exactly what you would do where you cannot. At each step, write OK, HESITATE (you could go on but were unsure) or STOP (you could not go on), with the words on the page that caused it. Note every place the page assumed you knew something, every place you left the training and could not see how to get back, every sentence you had to read twice, every step where you did not know why you were doing it, every control you had to search the screen for, and every Check where you could not tell whether your screen matched. Do not fix anything. Report the STOPs first.

## 2. Naive reader

> You are <learner>, reading this training for the first time with no background in this subject. Read every learner page in <path to the kit> in the order the path gives. List each place where a word is not defined before it is used, a step skips something you would need, a sentence could mean two things, a link sends you somewhere unexpected, or you do not know which window or screen to act in. For each, give the page, the exact words, and what you would need instead. Then read only the kit's name, the training names, the unit titles and the step headings, as the outline shows them: for each, say what you expect to do or learn there, and report every one that tells you nothing, or that leads you to expect something the page does not deliver. Do not rewrite the pages.

## 3. Instructional design

> Review the training in <path to the kit> as an instructional designer. Its learners are <learner>; what they must be able to do when they finish is <what learners can do>. Judge: whether the path opens, before any doing, with the Introduction that the kit's maintainer guide (<path to the kit>/maintaining/README.md, "The first unit on a path") describes; whether the objectives are stated where learners read them, in performance form; whether the learner practises rather than watches; whether support fades from a worked example to the learner's own task; whether the sequence contradicts itself; whether the checks let a learner catch an error; whether each idea that is a relationship between parts, or a contrast between two cases, is shown as well as told, and each picture carries content rather than decorating the page; whether each "What is ...?" unit teaches its subject's whole idea or narrows it to the case the training builds; whether learners meet a map of overlapping features before the training that first uses them; and whether the rating list at the end of the path names the same objectives as the home page. Report holes in the teaching, ranked by how much each weakens what learners can do when they finish. Measuring what happens after the training is outside the kit's scope: do not report its absence.

## 4. Claims check

> Here is a training kit at <path to the kit>, its claims register at <path to the kit>/facilitator/claims.md, and its sources at <path to the sources folder>. For each sentence in the kit that states what the subject does, what the organization requires, or what a screen or document shows, check it against the sources. Report each claim that is false, overstated, or stated as fact where the register marks it unverified, with the page and the exact words. Report claims missing from the register.

## 5. Regression

> A training kit at <path to the kit> was just changed. The change: <what changed, and why>. Read the changed pages and every page that links to them or repeats what they say. Report anything the change broke, anything it contradicts elsewhere, and any other place the same fix should also have been made. Then run `python maintaining/build_pages.py` from the kit's folder and report its last line.

## 6. Procedure style

> Review every instruction in the learner pages of <path to the kit> against <the writing standard in the kit's settings table>. Go sentence by sentence. Report every word that is not doing work, every long word where a short one serves, every sentence with more than one idea, each step that holds more than one action, names an action the learner cannot see or perform in <where practice happens>, names a control or artefact differently from how it appears, says what to do before saying where, leaves out what the learner should see afterwards, or runs longer than it needs to. Give the page, the exact words, and the rewrite the standard calls for. The kit's maintainer guide is <path to the kit>/maintaining/README.md: do not cut the reassurance or orientation its "Writing" section keeps, and do report any caution the tool does not require (its "Say what a step will change"). Then compare each unit with the guide's "The form of a unit" and the reference exercise it names (<path to the skill>/references/reference-exercise.md), and report each unit and step that departs from that form. Report every sentence you had to read twice to understand, with the split it needs. Then run `python maintaining/measure.py` from the kit folder and report the pages over budget, with what on each could go, as the guide's "Word budgets" says.

## 7. Learning-site experience

> Open <path to the kit>/read-in-browser/README.html in a browser and judge it as a self-paced learning site, for <learner> reading it beside <where practice happens>. Judge the site as a whole, both the web pages as a surface and the learner's experience of them. Report separately what the kit's own pages control (their text, headings, order, links, what each page puts on screen) and what the shared layout controls (navigation, progress, typography, colour): the first is fixed in the pages, the second in the page builder. For three pages (the home page, one unit, one help page), list every element that competes for attention with the job it does for the learner, the moment it serves (reading, doing a step, being stuck, returning later) and what else depends on it. Report jobs done twice, elements that could merge, and elements that could be shown only on request, and for each proposal show that no moment loses what it needs. Do not propose removing an element without naming what depended on it.

## 8. The whole programme

Run once per seat, one reader each. The seats: a learning-and-development designer, and a learner as the settings describe them.

> Judge the whole training programme in <path to the kit> from one seat: <seat>. From that seat only, report what the programme gets wrong or leaves out as a whole: who it fails to serve, what it assumes, what order or level is wrong, what is missing. Do not proofread individual pages.

## 9. Register and naming

> Read every learner page in <path to the kit> as it would land on <learner>. Report each sentence you would not say that way, in person, to that reader: for each, quote it, name what it implies about the reader, and give the rewrite. Do not report a sentence for being plain, only for implying a less capable reader than the one described. The reassurance and orientation that the "Writing" section of the kit's maintainer guide (<path to the kit>/maintaining/README.md) keeps are not talking down: report only their wording, never their presence. Then list every name the kit uses for the learner's own work and tasks, including page titles, headings and file names, and for each say whether <learner> would call their work that, and what the name implies about the work if not.

## 10. Sequence

> Do a structural edit of the order in <path to the kit>, as a technical editor checks a procedure. Its learners are <learner>. For each unit and recipe, check: that the steps follow the order in which the task is actually done in <where practice happens>; that each step's result is what the next step needs; that anything a step relies on (access, a file, a concept, a term, a setting) is introduced before that step, with no forward references; that a condition ("if you see…") comes before the action it governs; that each numbered step is one step of the task and the numbering follows that logic, sub-steps included. Then check the units: they build on each other in order, and the order in the training's path list, the outline and the pages agree. Report each problem with the page, the exact words and the order it should be in.

## 11. Prompts as sent

> Read every prompt in the learner pages of <path to the kit> as the learner who will send it, in <where practice happens>. For each prompt with a Copy button: send it exactly as written against the practice files the kit's earlier requests created, or, if you cannot operate the tool, say exactly what it would do as written. Report every prompt, and every request the learner is told to write themselves, that breaks a rule in the "Prompts" section of the kit's maintainer guide (<path to the kit>/maintaining/README.md), and every prompt that names something no earlier request opened or created. Give the page, the exact words, the rule, and the sentence the rule calls for. Do not rewrite the pages.

## 12. Pictures

The figures part of an editor's substantive edit, run by a reader who can see the built pages.

> Review the pictures in the learner pages of <path to the kit>, and the places that have none, against the "Pictures" section of the kit's maintainer guide (<path to the kit>/maintaining/README.md). Its learners are <learner>. Open the built pages under <path to the kit>/read-in-browser in a browser. First, without looking at the pictures, go through every unit action by action and list each place the section's table calls for a picture (which job, and why this learner needs it there), then each idea a page explains that the table says needs a drawing. Then look at the pictures. Report: each place on your list that has no picture; each picture that does none of the four jobs; each picture that breaks a rule under "Every picture" (where it sits, what it shows that the text does not say or contradicts, its text alternative, its credit line); and each page whose count is far from what the section says to expect, with the reason if the table explains it. Give the page, the step, and the picture or the missing one. Do not propose pictures for decoration, and do not rewrite the pages.
