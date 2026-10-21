# The review plan

Every review the skill runs, in the order it runs them, with what each reviewer sees, what it is
asked, and when it passes. SKILL.md's stage table says *when*; this file says *how*. The person
who asked for the piece is not on this list: they judge fit at the three stops, and a stop reaches
them only after every review before it has passed.

This is formative evaluation in the field's order (Dick & Carey): expert review first, then
one-to-one learner evaluation, then the finished piece.

## Rules for every review

- **The reviewer did not write what it reviews.** Expert reviews use the
  `independent-discipline-reviewer` agent with the lenses named below (each lens is a skill it
  loads); subject-matter checks and cold readers are `general-purpose` agents, told they did not
  write the work, and the cold readers are told to open no file. Hand every reviewer its questions
  word for word from the tables: the questions are the criteria. If the reviewer agent or a named
  lens skill is not installed, use a `general-purpose` agent given the same inputs, questions and
  report file, told that it did not write the work and that its job is to find what is wrong.
- **Its report is a file in the piece's folder**, named in the tables below. If the agent cannot
  write it, save its returned text to that file word for word. A stop page's report is
  `REVIEW-stop.md` beside the page; record your disposition of each finding at the end of the
  report, after the fixes. A stop page is learner content, so its reviews still pass before the
  person sees it. Nothing but you enforces that order.
- **Reviews in one set run at the same time**, dispatched in one message. A set waits only on what
  it reads.
- **Every dispatched agent and every render has a time limit and a check.** Reviews 20 minutes,
  renders 15. Dispatch in the background and look at each job when its limit passes. A job that has
  not returned is stopped and dispatched once more; if it stalls again, say so to the person in a
  line of its own. A frozen reviewer or a hung render with nothing watching it stalls the run
  until someone looks.
- **A review passes on what each line gives, never only on the absence of listed defects.** A
  checklist of things to avoid passes an empty line, because an empty line breaks none of them: a
  signpost that conveys nothing, or a mechanism described in place of a job, passes every rule it
  does not break, while any reader would call it empty.
- **The pass rule, the same everywhere:** a round passes when it returns no defect that would stop
  or mislead a viewer, and no claim that is wrong or unverifiable. Anything else is recorded in the
  report as standing, with the reason.
- **Fix, then re-run only the reviewers that found a defect,** except that a rewritten line goes
  back through every reviewer in its set that reads lines.
- **Three rounds at most per set.** A line that fails a third round is cut, or replaced with a
  different idea, not reworded again. Any other defect still open at the cap goes into the stop
  page's review record, named, with what was tried.
- **A change after a review does not ride on that review.** Anything edited after a set passed goes
  back through that set before the next stop.
- **A request for a review gets a review.** When the person asks for a review of anything, an agent
  that did not write it reviews it, and the review goes on the stop page beside the piece. A
  rewrite you propose follows from that review, never replaces it, and never lives only in chat.

## Set A: the plan, before Stop 1

Inputs to both: the brief, the scene list (one line per scene), `WALK.md`, any job aid, the
purpose file, the whole source, your opening message and the person's reply word for word.

| Reviewer | Agent and lens | Asked | Report |
|---|---|---|---|
| **Instructional design** | `independent-discipline-reviewer`, lens `editorial` | (1) **Is the brief right from the viewer's first moment?** Has every gap the walk found landed: in the brief, in Scope with a place that exists, in the Viewer line as an assumption, or with the subject's owner and the Fix line changed to match? Then against the source: what does the action need that the brief still leaves out? An exclusion is a gap too if the viewer cannot get what the piece is for without it and the brief names no other piece that covers it, or names one that does not exist at that location. One line in the piece saying where to get something covers it, if the source or the answers show that place exists. (2) Is an explainer the right fix beside what already exists, and is it the right size? (3) Is each scene in the viewer's order, and which scenes serve no line of the brief? (4) For each scene line, what does the viewer know after it? A topic heading fails. (5) The purpose file's outcome question, asked of the plan. | `REVIEW-plan-design.md` |
| **Subject matter** | `general-purpose` | Every claim the scenes make, checked against the subject's current documentation, marked confirmed, wrong, outdated or unverifiable, with the quote. | `REVIEW-plan-subject.md` |

A Stop 1 checked only for layout can reach the person while replaying something the viewers already
know; the two reviewers above are what catch that.

## Set B: the script, before Stop 2

The script goes out with **each line's stage labels beside it** (its `stage` field: what is on
screen while the line is spoken), because a line such as "type this" says nothing without its
picture. The word count has already run (SKILL.md, stage 7), so a cut does not undo these reviews.

| Step | Reviewer | Agent and lens | Sees | Never sees | Passes when | Report |
|---|---|---|---|---|---|---|
| B1, at once with B2 | **Subject matter** | `general-purpose` | the script and the whole source | — | every claim in every line is traced to the source (file and section) | `REVIEW-script-subject.md` |
| B2, at once with B1 | **Instructional design and script craft, against the brief** | `independent-discipline-reviewer`, lens `editorial` | the script, the brief, the purpose file, "Stage 5 and 7: writing the scenes and the script" in SKILL.md, `WALK.md`, any job aid, the opening message and reply | — | for every line it has written what the viewer knows after it; no line is empty, about the tool's insides rather than the viewer's work, condescending, presumptuous about the viewer, or hard to follow by ear; no example is narrated in place of the point it stands for (an example that demonstrates the point passes); every scene serves a line of the brief; the purpose's outcome question holds; the script says everything the person said it must and shows nothing they said it must not; no line states what the subject will change unless the viewer acts on it; no part or concept is left unnamed where its title or established name belongs; with a job aid, every statement on it is in the source and every workplace-dependent step is marked unknown | `REVIEW-script-craft.md` |
| C, after B passes | **Cold readers**, three, at once, backgrounds varied inside the Viewer line | `general-purpose`, told to open no file | the script with stage labels, and the Viewer line | the source, the brief, this skill, the earlier reviews | each reader, for every line, says what it tells them, why they would care, and whether it is about their work or the tool; at the end each names the brief's action as what they would do next | `REVIEW-script-readers.md` |

A line any reader cannot answer for is rewritten, goes back through B1 and B2, then to three fresh
readers. The readers are the common-sense check: they cannot pass a line for complying with a rule
they never saw. They are stand-ins, not viewers.

## Set D: the finished piece, before Stop 3 and again before the final cut

Run at once, after the build:

| Check | Who | What | Report |
|---|---|---|---|
| **Timing** | the scripts | page: `python <skill>/builder/check_timing.py <folder>` exits zero (it prints to the terminal; copy its result into `NOTES.md`); video file: the render in `build.py` succeeds, since it fails on any late beat and writes `timing-check.txt` | `NOTES.md`; `timing-check.txt` |
| **Operate it** | you | the page driven in a visible browser tab (`build-page.md`, "Operate it") | in `NOTES.md` |
| **Frames** | you | every scene's settled frame looked at, both forms: a shape that reads wrong, text past its box, marks on a border | in `NOTES.md` |
| **The finished piece** | `independent-discipline-reviewer` | lenses `visual-usability` and `editorial`, given the brief, the purpose file, `WALK.md`, and renders of every scene's settled frame you made; asks Set B2's brief questions of the transcript and stage text (page) or the narration and the text drawn in `scene.py` (video) | `REVIEW-<page stem>.md`, or `REVIEW-<video file stem>.md` for a video-file-only piece |

A piece judged only against its own brief passes whatever the brief forgot, so the finished-piece
review gets `WALK.md` too.

**Say what you measured and what you did not.** The `visual-usability` lens cannot judge a page
without a render, and two passes of arithmetic are not a render. The screen contract and what the
person will see are measured with the page opened the way they and the viewers will open it, at a
laptop-sized window, and the report names that surface.

## The stop page review, at every stop

Each stop page is reviewed before the person sees it: `independent-discipline-reviewer`, lenses
`visual-usability` and `editorial`, report `REVIEW-stop.md`. The reviewer has no browser, so you
open the page, screenshot it at 1366×657, a phone width and a desktop width with your browser
tool, and hand it the screenshots with the page. It asks:

- Does the page open with who reviewed the piece, the lens each used, and the verdict (at Stop 3,
  directly beneath the player, which comes first), before anything is put to the person? Does each
  part open with the one question to read it with?
- Is every statement on it true: the "what changed" line, any claim that something was checked or
  measured, any claim about the layout?
- Does it cite anything the person cannot open from the page (a path on a machine they cannot
  reach, a file that is not beside the page)?
- Does it ask whether their last notes landed, and end with what a reply can say?
- In the screenshots: does it fit as the screen contract says?

The check in the person's own browser is yours, after building and before the handover (`stops.md`,
"How every stop works"). A fix it forces goes back to this reviewer before the handover.

## Set E: the package, before delivery

The delivered files are checked as files, not as the stop page, after the last build of the
package. **You run the measurable checks** and record each result: the page loads nothing from
outside (opened with your browser tool, its network list); it declares `<!doctype html>`, `lang`
and `charset`; it meets WCAG AA text contrast in light and dark (a Lighthouse accessibility run,
from your browser tool or the browser's own Lighthouse panel); each media file's metadata holds
nothing beyond the container's brand and encoder lines, no title, author, comment, date or location
(`ffmpeg -i <file> -f ffmetadata -`, which works with any ffmpeg, including the one `imageio-ffmpeg`
installs, which has no `ffprobe`); the video file lists a subtitle stream (`ffmpeg -i`).
**Then `independent-discipline-reviewer`**, lenses `visual-usability` and `editorial`, reads the
package's text files and your results: no review sections or code comments, a README that says
what each version is and how to open it, nothing a viewer cannot open. If the place it goes has its
own release checks, they run too. Report: `REVIEW-package.md` in the piece's folder, never inside
`package/`; a rebuild of the package means running Set E again.

## What a clean run dispatches

The walk: 1 agent. Set A: 2. Stop 1 page: 1. Set B: 2, then 3 readers. Stop 2 page: 1. Set D: 1.
Stop 3 page: 1. The final cut, if notes changed anything: Set D and the stop page again, 2. Package:
1. Thirteen agents for a run with no failed rounds and no rough-cut notes, most of them in
parallel. The time budgets in SKILL.md assume that parallelism.
