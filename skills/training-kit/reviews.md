# Review briefs

Each pass is run by a reader that did not build the kit: a fresh session or a subagent. Give it the
brief below with the blanks filled, the path to the kit and to its `sources` folder, and nothing
else: not your notes, not your opinion of the kit, not earlier reviews. Its report comes back to
you; you decide what to fix.

Fill `<learner>` from the kit's settings table: who the learners are, by the work they do, what
they know of this subject, and how expert they are in their own work. Describe the learner. Do not
describe the kit.

## 1. First-time learner walk

> You are <learner>. You have never seen this training and have no one to ask. Open <path to the kit>/read-in-browser/README.html and follow the path from the first page, doing every step as written in <where practice happens>, or saying exactly what you would do where you cannot. At each step, write OK, HESITATE (you could go on but were unsure) or STOP (you could not go on), with the words on the page that caused it. Note every place the page assumed you knew something, and every place you left the training and could not see how to get back. Do not fix anything. Report the STOPs first.

## 2. Naive reader

> You are <learner>, reading this training for the first time with no background in this subject. Read every learner page in <path to the kit> in the order the path gives. List each place where a word is not defined before it is used, a step skips something you would need, a sentence could mean two things, a link sends you somewhere unexpected, or you do not know which window or screen to act in. For each, give the page, the exact words, and what you would need instead. Then read only the kit's name, the training names, the unit titles and the step headings, as the outline shows them: for each, say what you expect to do or learn there, and report every one that tells you nothing, or that leads you to expect something the page does not deliver. Do not rewrite the pages.

## 3. Instructional design

> Review the training in <path to the kit> as an instructional designer. Its learners are <learner>; the outcome it must produce a week later is <outcome a week later>. Judge: whether the path opens by grounding the learner (the situation they are in and why it matters, a short map of the ideas the path uses, what they will be able to do, how the path is laid out) before any doing; whether the objectives are stated where learners read them, in performance form; whether the learner practises rather than watches; whether support fades from a worked example to the learner's own task; whether the sequence contradicts itself; whether the checks let a learner catch an error; and whether the week-later measure can tell if the training worked. Report holes in the teaching, ranked by how much each weakens the outcome.

## 4. Claims check

> Here is a training kit at <path to the kit>, its claims register at <path to the kit>/facilitator/claims.md, and its sources at <path to the sources folder>. For each sentence in the kit that states what the subject does, what the organization requires, or what a screen or document shows, check it against the sources. Report each claim that is false, overstated, or stated as fact where the register marks it unverified, with the page and the exact words. Report claims missing from the register.

## 5. Regression

> A training kit at <path to the kit> was just changed. The change: <what changed, and why>. Read the changed pages and every page that links to them or repeats what they say. Report anything the change broke, anything it contradicts elsewhere, and any other place the same fix should also have been made. Then run `python maintaining/build_pages.py` from the kit's folder and report its last line.

## 6. Procedure style

> Review every instruction in the learner pages of <path to the kit> against <the writing standard the kit adopted: the environment's editorial standard for instructional documents if there is one, otherwise the Microsoft Writing Style Guide with the Google developer documentation style guide's procedure conventions>. Go sentence by sentence. Report every word that is not doing work, every long word where a short one serves, every sentence with more than one idea, each step that holds more than one action, names an action the learner cannot see or perform in <where practice happens>, names a control or artefact differently from how it appears, says what to do before saying where, leaves out what the learner should see afterwards, or runs longer than it needs to. Give the page, the exact words, and the rewrite the standard calls for. Do not cut safety reassurance or orientation a first-timer needs to act safely (what an action will and will not change, what they may ignore for now, where they are and how to get back): those words are doing work.

## 7. Learning-site experience

> Open <path to the kit>/read-in-browser/README.html in a browser and judge it as a self-paced learning site, for <learner> reading it beside <where practice happens>. Judge only what the kit's own pages control (their text, headings, order, links, what each page puts on screen), not the site's shared layout. For three pages (the home page, one unit, one help page), list every element that competes for attention with the job it does for the learner, the moment it serves (reading, doing a step, being stuck, returning later) and what else depends on it. Report jobs done twice, elements that could merge, and elements that could be shown only on request, and for each proposal show that no moment loses what it needs. Do not propose removing an element without naming what depended on it.

## 8. The whole programme

Run once per seat, one reader each. The seats: a learning-and-development designer, one learner for each audience the settings name, and, if the kit is also presented live, a presenter.

> Judge the whole training programme in <path to the kit> from one seat: <seat>. From that seat only, report what the programme gets wrong or leaves out as a whole: who it fails to serve, what it assumes, what order or level is wrong, what is missing. Do not proofread individual pages.

## 9. Register and naming

> Read every learner page in <path to the kit> as it would land on <learner>. Report each sentence you would not say that way, in person, to that reader: for each, quote it, name what it implies about the reader, and give the rewrite. Do not report a sentence for being plain, only for implying a less capable reader than the one described. Safety reassurance and orientation a first-timer needs to act safely (what an action will and will not change, what they may ignore for now) are not talking down: report only their wording, never their presence. Then list every name the kit uses for the learner's own work and tasks, including page titles, headings and file names, and for each say whether <learner> would call their work that, and what the name implies about the work if not.

## 10. Sequence

> Do a structural edit of the order in <path to the kit>, as a technical editor checks a procedure. Its learners are <learner>. For each unit and recipe, check: that the steps follow the order in which the task is actually done in <where practice happens>; that each step's result is what the next step needs; that anything a step relies on (access, a file, a concept, a term, a setting) is introduced before that step, with no forward references; that a condition ("if you see…") comes before the action it governs; that each numbered step is one step of the task and the numbering follows that logic, sub-steps included. Then check the units: they build on each other in order, and the order in the training's path list, the outline and the pages agree. Report each problem with the page, the exact words and the order it should be in.
