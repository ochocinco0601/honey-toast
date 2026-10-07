# Review checklist: what a reader must not have to catch

Run this on every unit before anyone is shown it, after `maintaining/check_rulings.py` passes. The
script catches the faults a pattern can find; this list covers the ones that need judgement. The
examples come from a training on an AI coding assistant; each item applies to any subject. A
reviewer who did not write the unit runs it, reading the built page in a browser after arriving
the way a learner does (the walk in the skill's step 7).

Where an item judges a rule in the kit's maintainer guide (`maintaining/README.md`), it names that
rule; the rule's wording is there, not here.

Report each finding as: the item, the line, and what a learner would do wrong because of it.

## Does the unit earn its place

1. **Purpose.** In one sentence: what can the learner do after this unit that they couldn't do
   before? If the answer is trivial ("see a reply arrive"), or no different from what the learner could already do, the unit is wrong, not the wording.
   **A unit, or a line?** If the lesson fits in one sentence ("if a skill isn't used, ask the
   assistant to review and fix it"; "share a skill by giving someone its folder"), it is a line in another
   unit, not a unit of its own.
   **Lesson, not mechanism.** For each step, ask what the learner knows afterwards. If the answer is
   where a file goes, which menu to right-click, or how the tool wires things together, the step
   teaches plumbing: under the guide's "Where practice is in an assistant", the tool does the
   plumbing in one request, and the step shows the effect. The mechanism goes in a fold, if
   anywhere.
2. **Gist, not toy.** The example shows why the feature matters, ideally by contrast, for example
   the same request before and after. Rules invented only so there is something to check (date
   formats, list lengths) don't teach the concept.
3. **Minimum.** Judged by the guide's "Less is more": every step, sentence and action earns its
   place. Two steps that teach one idea become one. No checker's bookkeeping for the learner:
   hunting lines, ticking items, learning a taxonomy.

## Could a learner actually do it

4. **One sitting, in order.** Nothing waits for a real question, the next day, or another unit.
5. **Nothing the learner may not have.** The guide's "Nothing to download": does any step rely on
   something not every learner has?
6. **Nothing left behind.** The guide's "Prompts" rules 9 and 10: after the unit, has anything
   from the training landed in the learner's real files or setup?
7. **The example doesn't misinform.** A worked example teaches a rule whether or not the page
   states one. For each thing the page has the learner create that changes how the tool behaves,
   is its scope stated as "Prompts" rule 10 requires, and does nothing in the example suggest
   another? A decision exercise's cases each have one right answer under everything the earlier
   units taught, and its hardest case sits beside a near miss: a case an earlier lesson answers
   differently teaches the learner that the lesson was wrong.
8. **Current documentation.** Every instruction about the tool being taught is checked against the
   source the guide's "Nothing invented" names, and the review cites it, under every value of a
   setting the page leaves alone. (Instances: an AI assistant described as an installed extension,
   when it now ships built in; a built-in agent named that one session target does not list.)
9. **Every control works.** Click every link, fold, copy button and "Stuck?" button. Each one says
   what it does, and lands where its words say. Each page opens at its title, also inside the
   viewer it is published in.

## Does it read right

10. **Each sentence says something, to someone.** Read it as an editor, against the guide's "Every
   sentence reads right the first time": no inverted or knotted sentences, no restatement, nothing
   announcing what the page calls things.
11. **Headings as a list.** Run the test in the guide's "Names lead" on the unit titles, as the
    menu and the training's cards show them, and then on each unit's step headings, as the menu
    shows them. Beyond that rule: the titles are parallel, no two in one training start alike, and
    they hold up beside how published courses on the subject title the same topics. Across
    trainings, the same kind of unit titled the same way ("What is a skill?", "What is a custom
    agent?") is the parallel the set needs, not a clash.
12. **One name for one thing.** The guide's "One name for the tool", for every name: the product's
    own names, the same on every page, and the units, steps and trainings named the same way in
    the menu, on the cards and in the text.
13. **Non-technical reader.** The guide's "Writing" rule for a term a non-technical reader may not
    know: is every such term (Markdown, terminal, checkpoint) explained where it first appears?
14. **Reassurance and verification, not generic warnings.** The guide's "Say what a step will change" and "Prompts" rule 8:
    is any caution, judgement test or blanket warning left that the tool doesn't require?
15. **Pictures, in both directions.** Against the table in the guide's "Pictures". Missing: an
    action whose control is small, inside a menu or among several like it, the first time its
    training uses it; a Check whose look the product fixes (a control that appears, a status
    that changes, a dialog) where words leave doubt; an idea a paragraph carries as a
    relationship or a contrast. Each of these with no picture is a finding. A Check on content
    that differs from learner to learner (a reply, a file the tool writes) needs no picture, and
    one there is a finding. Present: each picture does one of the four jobs, sits under what it
    belongs to, and meets "Every picture" there. It is a drawing from the product's layout, never
    a capture of one step's state; each label is the page's word for the thing; varying text is
    a gray bar; it shows the panel around the control with its header, icons and neighbouring
    controls, at the level of the kit's other drawings of that window; nothing in it contradicts the text (for example, an "Install Extension" heading,
    or a label the learners' version has renamed). Where two pages name the same parts, they
    share a drawing or its parts, not two near-copies. A picture with no job is a finding too.
16. **The page as a whole.** The page passes the guide's ten-second test ("What a step shows"), and
    its "Density": no run of paragraphs over about 130 words without a list, table, picture or
    code block, no heading more than 250 words from the last, and parallel items as a list. The
    same thing isn't listed twice on one screen. No time or position is typed in the text ("Position
    and time are generated").
17. **Across pages.** Read the front page, the training home and the units in order. No page
    repeats another's content; every reference to another page names it by title and still points
    at the right one; every "next" goes forward. Names don't collide with words the audience
    already uses for something else (a training called "Track changes" reads as the word
    processor's feature; "save a version" collides with File, Save).
18. **The whole idea, not the worked example.** A "What is ...?" unit states its subject as the
    subject's owner defines it, with more than one kind of use from the owner's docs. The case
    the training goes on to build is named as one kind, never taught as the definition. An
    exercise that asks which feature fits grades on the distinction the owner's docs draw, never
    on one the kit made up, and says when more than one would work.
19. **A map before the features.** When the subject has several features that do overlapping
    jobs, the programme's home page has one "which to use when" table before any training. It
    is built from the owner's own comparison: what each is for, when it applies, which training
    teaches it, and that more than one can fit. A later unit that compares them points back to
    it rather than being where the comparison first appears.
