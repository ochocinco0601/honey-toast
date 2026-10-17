---
name: explainer-video
description: Make a short explainer (90 seconds to 2 minutes, 3 at the outside) on any subject - clean shapes and text drawn by code, narrated, as a video file rendered with Manim, a scene-addressable page played in a browser, or both from one script. Triggers on "make an explainer video", "make a video explaining X", "explain this as a video", "overview video", "intro video for a training or course", "3b1b style video", "animated explainer", "narrated video", "explainer page", or a request to change, fix or rebuild an existing explainer. Not for screen-recorded demos or long training videos.
---

# Explainer

A short piece that explains one thing: shapes and text drawn by code, narrated, a couple of
minutes long. Built for one viewer; cheap enough to throw away.

**The files of this skill, and when to load each:**

| File | What it holds | Load |
|---|---|---|
| `SKILL.md` | the stages, what you ask, the analysis, the brief, the walk, the script rules, drawing, what it runs on | now, whole |
| `purpose-*.md` | what one kind of piece needs (see "What the piece is for") | when you pick the purpose |
| `reviews.md` | every review: who, with what lens, seeing what, in parallel or not, when it passes, round caps, time limits | before the first agent you dispatch (stage 0 for a new purpose file, else stage 4) |
| `stops.md` | the three stops, building and checking a stop page, delivery and when the piece is done | at stage 6 (stage 3 reads its "Building a stop page") |
| `build-page.md` | building and operating the page form, its screen contract and gotchas | at stage 8, for a page or both; step 1 at stage 3; step 7 (the screen contract) for any Stop 3 page |
| `build-video.md` | building the video file form, and both forms from one script | at stage 8, for a video file or both |
| `templates/` | the scripts and starting files every piece copies (stage 3) | at stage 3 |

**The templates** are a working three-scene example: `narration.json` (script and brief),
`example-explainer.html` (the page player), `scene.py` (the same scenes in Manim), the build and
check scripts, and `stop2.json` / `stop3.json` (the text of the stop pages). Every script runs
from the piece's own folder and reads the piece's files beside it; none needs editing for a new
piece. What a piece replaces is its scenes, its text and its brief.

## The stages

Do them in this order. The sections below say how for stages 0–5 and 7–8; `stops.md` for the stops and delivery; `reviews.md` for every review; the build files for stages 8 and 10.

| # | Stage | You produce (in the piece's folder) | Gate before the next stage |
|---|---|---|---|
| 0 | Find the source; pick the purpose; make the piece's folder (below) | `NOTES.md` with the start time and Stop 1's budget | — |
| 1 | The opening message | the message | **wait for their answers** |
| 2 | Whether an explainer is the fix | the Fix line | *no explainer* or *not yet*: tell them, and stop |
| 3 | Copy the templates; the brief, and the job aid if one is due | `narration.json` `brief`; `job-aid.md` | — |
| 4 | The first-moment walk | `WALK.md` | every gap sorted into the brief |
| 5 | The scene list | `narration.json` scenes, one line each | **Set A** passes |
| 6 | **Stop 1: the story** | the stop page | its review; **wait** |
| 7 | The script, with each line's stage labels | `narration.json` lines | your own line test and the word count (`build_audio.py --count`), then **Set B** passes |
| 8 | Voice, the drawing, stills | audio, `timing.json`; the page (page or both) or `scene.py` (video file only); `stills/` | — |
| 9 | **Stop 2: script and frames** | the stop page | its review; **wait** |
| 10 | Build the piece: for both, `scene.py` drawn to match the page, and the render; the package | the page and/or the video file; `package/` | **Set D** passes |
| 11 | **Stop 3: rough cut, then final cut** | the stop page with the piece in it | its review; **wait**; again after notes |
| 12 | Delivery: the package rebuilt from the final cut, and placed | `package/`, placed where the brief says | **Set E** passes; it plays there |

**The piece's folder.** All explainers live together, one folder each, named
`<subject>-explainer/`, so that a later session can compare one explainer against another. Use
the place the project already keeps such work; if there is none, `explainers/` at the root of
the workspace. The subject keeps its own folder and is only read from.

**A time budget per stop, tracked.** When you start work toward a stop, write in `NOTES.md` the time
you started and the budget; when the stop page is handed over, write the actual, from timestamps.
The budgets, of your own work and not counting waiting on the person, with the reviews dispatched in
parallel as `reviews.md` says: Stop 1, 45 minutes from their answers; Stop 2, 30 minutes; Stop 3, 45
minutes for one form; each revision after notes, 20 minutes. Over budget, write what took the time
beside it, and reset the numbers from your own measured runs. The time record stays in `NOTES.md`,
off the stop page. A fault the checks before a stop exist to catch costs a rough-cut revision when
it is found after the stop instead: run them, and the rough cut stays short.

## What it runs on

State these to the person when a piece needs something not yet installed; never assume them.

| To | Needs |
|---|---|
| Count the words (`build_audio.py --count`), check timing, build the stop pages | Python 3 only |
| Make the voice and timing (every piece, any form) | Python with `kokoro-onnx` and `soundfile`; the Kokoro model files `kokoro-v1.0.onnx` and `voices-v1.0.bin`; ffmpeg |
| The page form | the above and a browser. **No Manim.** |
| The video file form | the above and Manim Community Edition (`manim`) |
| Build the package (`build_publish.py`) | Python and ffmpeg |
| Operate the page, take stills and screenshots, run Lighthouse | a browser the session can drive, such as a Chrome DevTools MCP server |
| Watch the delivered piece | a browser (page) or any video player (video file); nothing else |

Even a page that will be watched with the sound off is timed from spoken clips, so it needs the
speech engine to build. ffmpeg is found on PATH first, then through `imageio-ffmpeg` installed in
the same Python (Manim installs that package itself). The scripts look for the model files in the
folder named by the `KOKORO_MODELS` environment variable, or in `kokoro-models` in your home folder
when it is unset, and say so plainly when they are missing.

One-time setup on Windows, in PowerShell (the environment's location is only an example):

```powershell
python -m venv $HOME\.venvs\explainer
& $HOME\.venvs\explainer\Scripts\python -m pip install kokoro-onnx soundfile imageio-ffmpeg
New-Item -ItemType Directory -Force $HOME\kokoro-models | Out-Null
$base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
Invoke-WebRequest "$base/kokoro-v1.0.onnx" -OutFile $HOME\kokoro-models\kokoro-v1.0.onnx
Invoke-WebRequest "$base/voices-v1.0.bin" -OutFile $HOME\kokoro-models\voices-v1.0.bin
# For a video file, add Manim (a separate environment if pip reports a conflict):
& $HOME\.venvs\explainer\Scripts\python -m pip install manim
```

Where the organisation has an approved package source or mirror, get the packages and the two model
files through it instead of from PyPI and GitHub directly. Check the licences of the speech engine
and its dependencies before use: the text-to-phoneme dependency `phonemizer` is published as GPL-3.0
or later (its own PyPI metadata), and `kokoro-onnx` and `espeakng-loader` state no licence in their
package metadata. The upstream release publishes no checksums for the model files, so record the
SHA-256 of what was downloaded (`Get-FileHash $HOME\kokoro-models\*`) and the package versions used
(`pip freeze`).

In the commands in these files, `python` means the Python holding what that step needs (the table
above). Without a browser the session can drive, the checks that need one (operating the page, the
stills taken from it, screenshots, Lighthouse) cannot be done by you: say so on the stop page and
in the handover, and never report them as done.

## What the piece is for

A **purpose file** beside this one says what one kind of piece needs, in seven parts: **Fits
when** (how you pick it from the subject), what to work out about the viewer before the brief, the
lines it adds to the brief, whether an explainer is the fix and what its job aid holds, what the
viewer's first moment looks like, its rules for the script, and the reviewer's outcome question.
Everything else in this skill is the same for every purpose.

If none fits (explaining an idea, announcing a change, making the case for a decision, an overview
of a system), write one in the same seven parts from the established practice for that kind of
communication, beside the others, and have a reviewer that did not write it check it against that
practice (`reviews.md`, "Rules for every review") before the brief is written, its report in the
explainers folder as `REVIEW-purpose-<name>.md`. Name the purpose in the opening message anyway;
the writing and its review run while you wait for the answers. A new purpose changes only its own
file. Where a common section assumes a viewer action or a tool's parts (the walk's questions 2–4,
"Describe the subject by the job it does"), a purpose whose viewer has no action to start says in
its own file what replaces them.

## Stage 0–1: what the person gives, and what you ask

**They give one thing: the subject.** "Make an explainer about X" is a complete request. Nobody
asking is expected to know how this skill works or what it needs.

**Find the subject's source yourself:** the skill file, the documentation, the code, whatever the
subject is made of, all of it and not only the part the piece will cover. Find also what has
already been decided about the subject (its records, rulings, open issues) and read it before you
raise anything about the subject. If you cannot find the source, say what you searched and ask for
it inside the opening message, never in a separate one. **Pick the purpose yourself** and name it
in that message as a statement.

**When they name a body of material rather than one subject** (a whole training, a documentation
set, a codebase), the opening message first plays the situation back: what the material is, and two
or three pieces it could become (for example, an overview of the whole, or one part of it), each
with what the viewer would get. The person chooses, in their reply to the same message. Do not pick
a part for them, and do not default to any one choice: a review only refines the piece it is
handed, so a wrong choice of subject survives every review after it, however many rounds polish
it. This is the discovery step of video production.

**Lay the opening message out for decisions, in this order:** for a body of material, the playback
and the choice of piece; then the purpose, as a statement (for a body of material, the purpose for
each choice); then the three questions, each in a line or two with your guess; then a request for
the source if you could not find it; then, in one line, what happens after they answer (you bring
the story back for them to see before anything is scripted). Nothing else.

**Ask once, in one message, before writing anything:** the three questions below. Each carries your
best guess from the source, so someone who does not know can answer "yes". Each asks only what the
person can know. Why the viewers are not doing it yet, and where they go wrong, are not questions
for them: someone asking for a piece already has a reason, and to them those questions read as
theory. You work both out yourself, from the source and the walk.

1. **Who is it for?** One line of guess, from the source: the people who would use the subject,
   never the person asking unless the source says it is only for them. Say where the guess comes
   from and that it is only the source's assumption ("the documentation's introduction assumes it
   is for..."): a source describes the audience it assumes, which may not be who actually comes,
   and the person can only correct a guess they can see the basis of. What those viewers already
   know or have, and what the piece leaves out, are yours: they go into the brief's Viewer and Scope
   lines, which the person sees at Stop 1. **"Anyone new", or "no role assumed", means a capable
   adult who is new to this subject**, not one who can do little. A claim about what the viewer
   cannot do or does not know needs a source other than the material's own audience line; read
   without one, "assume no role" turns into "assume the least", and the script starts telling
   viewers what they cannot do.
2. **A video file, a page, or both; will they have sound; and where will viewers find it?** The
   last part names a place (a channel, a page, an email, the top of the documentation), which is
   where the piece is delivered and checked at the end. Say what each form gives, in the viewer's
   terms:
   - **A video file** plays anywhere a file can be sent (a chat channel, email, a wiki page), is
     always narrated, and carries captions as a track the player can turn on. It cannot jump to a
     scene, step, or show a transcript.
   - **A page** opens in a browser: the viewer can step scene by scene, jump from the transcript
     beside the player, read captions, and watch with the sound off. It is a small folder (the page
     and its audio files), not one attachment: it goes wherever a folder of files can be opened or
     served, such as a file share, a web server or a documentation site.
   - **Both** come from one script and one voice, but every picture is drawn twice, once for each
     form, so both takes longer than either (`build-video.md`).

   Your guess may come from where they will watch, but it is a suggestion they confirm, never a
   decision you make. **If the answer is short or could mean either form** ("a video"), play back
   what each form gives and lacks, as above, and have them choose before Stop 1: never read the word
   as the form. A form chosen by assumption is found out at the rough cut, when what it lacks shows,
   and then part of the piece is built twice.
3. **Anything it must say, or must not show?** Required wording, things that cannot appear on
   screen, a standard it has to meet. Guess "nothing" unless the source suggests otherwise.

Ask nothing beyond these three. The brief, the scenes, the length and the narrator voice (Kokoro
`af_heart`; `am_michael` is the backup) are yours. Whether there is narration at all is the
person's, from question 2: sound for everyone means narrated; no sound means a captioned page with
no narration; some with and some without means a page, narrated, with the sound optional.

**No reply is not a yes.** Wait. Continue when they say to. **A reply that answers some questions
and not others** settles those it answers; the rest stay your guesses, written into the brief as
unconfirmed and put to them once more at Stop 1. **A "go on" accepts every guess that was put to
them**; ask again only when the next step cannot proceed without the answer. Asking the same
guesses again at the next stops, after a "go on", is the failure this rule exists for.

## Stage 2: whether an explainer is the fix

An explainer fixes one thing: viewers who do not know something. Decide whether that is what stops
them, from the source and the person's answer to question 1; the walk, later, can change it. This is
your analysis, not a question to the person: when the outcome is an explainer, it appears only as
the brief's Fix line. When it is *no explainer* or *not yet*, tell them in plain words what is
missing and what you made instead (for example: "Nothing says how a colleague gets this tool, so a
video would teach something they cannot start. I've made the one-page sheet with that step marked
unknown."), never the sorting below; that message is the whole exchange, with no stops. This is the
performance analysis instructional design runs before any training: Mager & Pipe ask whether the
person could do it if their life depended on it, and if they could, training is not the fix; in
Gilbert's model, missing knowledge is one cause among six.

Sort each thing that stops the viewers:

| What stops them | What fixes it |
|---|---|
| They do not know how, that, or why | an explainer |
| They do not have the tool, access, a credential, or the setup | the subject's owner; no piece fixes it |
| They have a reason not to: not their job, nobody asks, the old way is easier | the subject's owner, or whoever asks for the work |

Then take the first outcome that applies, in this order, and write it with its reason as the Fix
line:

1. **No explainer.** Imagine every *have* and every *reason not to* cleared: would anything they do
   not know still stop them? If not, no piece is made. Say so, name what goes to the subject's
   owner, and stop. If the action is a procedure they already want to do, a job aid alone may be the
   whole fix.
2. **Not yet.** Knowledge is missing, but something before the first step (a way to install it, a
   credential) is one only the owner can supply, and the source does not say where it comes from. A
   piece released now teaches an action nobody can start. Report the blocker, make the job aid if
   one is due with the blocked step marked unknown, and make the piece when the blocker has an
   answer.
3. **Explainer and a job aid.** The action has more than about two steps, or hands back decisions:
   two minutes of watching will not hold it, so a one-page sheet goes alongside (Rossett & Schafer's
   criteria for a job aid).
4. **Explainer.**

**Reporting a blocker:** say it to the person who asked, in a message of its own and never inside a
stop's handover, naming the owner if the source names one. If the subject's owner tracks work
somewhere you can write to, and the person agrees, record it there too. Never solve it inside the
piece by supplying how it works at the viewer's workplace. Where a step depends on that, the piece
and the job aid mark it unknown. A stop carries the piece and nothing else. When the person who
asked owns the subject, the blocker goes to them all the same, and an answer that clears it lets the
work go on from stage 2.

**The job aid.** One page, readable without having watched, in the order the viewer works. The
purpose file says what goes on it. It is `job-aid.md` in the piece's folder. A page carries the same
text in its Summary panel, below the player; a video file is sent with the sheet beside it
(`build_publish.py` copies `job-aid.md` into the package). With no piece made, it goes in a
`<subject>-job-aid/` folder beside the explainers, with the Fix line in a `FIX.md` beside it, never
on the sheet, whose reader is the viewer. When the piece is made later, move the sheet into the
piece's folder and delete the old folder.

## Stage 3: the brief, which decides whether the piece is the right thing

Every production check asks whether a part is made well. None can say whether the piece is the
right piece. The brief does. It comes before the script, and everything after it is judged against
it. This is the creative brief from video production.

Written by you from the source and the person's answers: the five common lines below, plus the
lines the purpose file adds.

- **Fix.** The outcome of stage 2, its reason, and anything routed to the subject's owner and where.
- **Viewer.** Who watches, what they already have or know, and what they are in the middle of when
  they need this.
- **Scope.** Where the viewer starts and where the piece stops, and what is deliberately left out
  and where that is covered instead, by its location. Named, so a reviewer can tell "left out on
  purpose" from "forgotten".
- **Where it plays, sound, and anything it must say or not show.** From questions 2 and 3. Where it
  plays is a place viewers will find it, not only a form.
- **Source.** What the piece was made from, and its version (a commit or a version line), so a later
  reader can tell when the piece has gone stale.

**Copy the templates into the piece's folder first.** From this skill's `templates/` folder copy
`narration.json`, `build_audio.py`, `check_timing.py`, `build_stop.py`, `build_stop3.py`,
`build_publish.py`, `stop2.json`, `stop3.json` and `.gitignore`; for a video file or both, also
`scene.py` and `build.py`; for a page or both, `example-explainer.html` is copied at stage 8
(`build-page.md`), because the build checks a page's captions against the script. Then replace
`narration.json`'s contents, keeping its shape (`title`, `name`, `about`, `brief`, `voice`, `speed`,
`scenes`, `head`, `gap`, `tail`): `title` is the piece's title, `name` the file name of the video
and captions files, `about` one sentence for the package's README. Put the brief at its top as
`brief`, one key per line above and per purpose line (`fix`, `viewer`, `scope`, `where_it_plays`,
`must`, `source`, then the purpose's), so it travels with the script.

Without a brief, every component check can pass a piece that teaches how the subject is designed
rather than the viewer's turns in it, and a piece can pass its own review while its brief leaves out
how to start. That is why the reviewers judge the brief and its exclusions, not only the parts.

## Stage 4: walk the brief from the viewer's first moment

A brief checked only against the source leaves out whatever the source leaves out, and whoever wrote
the brief has read the source, so they fill those gaps without noticing (the curse of knowledge).
Dick & Carey call what the viewer must already have and be able to do the *entry behaviours*, and
specify them from the viewer, not from the content. So dispatch an agent that has never seen the
source (a `general-purpose` agent), hand it **only the brief**, and tell it not to open any file.
Give it this, with the purpose file's notes on the first moment:

> Take the viewer as this brief describes them, at the moment it says they need this. (1) What is
> open on their screen, and what do they have, before the first scene? (2) After the piece, what is
> the first thing they physically do to begin the action: where do they click or type, and in what?
> (3) What must already be true for that to work, and does the brief say where each comes from? (4)
> Walk on, act by act, to the end of the action. Report each place the viewer cannot take the next
> act from what the brief gives them: the act, what is missing, and whether it is something to KNOW
> or something to HAVE or be GIVEN. Say whether you opened any file.

Then you, with the source, sort each gap:

- **Something to know** that the action needs: into the brief, or into Scope as an exclusion with
  the place that covers it.
- **Something the viewer, as the brief describes them, already has** (signed in to a tool they use
  every day, rights they need for their job): into the Viewer line as a stated assumption, so a
  reviewer can see it and object.
- **Something to have or be given** that they may not have: back to stage 2. It is a blocker for
  the subject's owner, and it may change the Fix line to *not yet*. The piece may carry one line
  saying where to get it only if the source or the person's answers show that place exists.
- **A gap the source has too** (it does not say how to start, where the credential comes from): a
  finding about the subject, reported to its owner, not filled in by you.

Write the walk's report, word for word, and your sorting to `WALK.md` (in the `-job-aid/` folder
when no piece is made); every review of the brief gets it. A tryout of the finished piece does not
replace this walk: it runs after everything is drawn and voiced, when a missing first step costs a
rebuild, and on a set-up where the tool is already installed, which is the access a real viewer may
lack. A walk given only the brief can find entry blockers and gaps that a review of the brief
against the source cannot, because that reviewer has read the source too.

## Stage 5 and 7: writing the scenes and the script

These rules shape the scene list at stage 5 and the script at stage 7. Before dispatching any
review, put every line through the first rule yourself. The purpose file adds its own rules.

**One idea per scene. Six to ten scenes. Ninety seconds to two minutes, three at the outside.**
Over that, cut a scene. Not the pauses, not the voice speed: a scene. If nothing can be cut, the
subject is two explainers.

**Every line tells the viewer something specific.** The test, for each line: what does the viewer
know after hearing it that they did not know before? A line whose answer is "nothing specific" is
cut or replaced: an agenda or signpost that announces content without giving it ("what they let you
do, how they fit, and where to begin"), an abstraction with no referent, a restatement of the line
before. A scene line in the plan at stage 5 passes the same test. Plain language is not the same as
empty language: an objective stated as a list of topic headings conveys no meaning.

**Pitch it to a capable adult.** Plain words, never simple ideas: do not explain what any working
adult knows, do not reassure, do not tell the viewer what they cannot do. A script that does any of
these reads as talking to a child.

**Describe the subject by the job it does in the viewer's work, not by how it works.** The system of
interest is the viewer's work. The tool's parts are named by their real names, and each is described
by what it lets the viewer get done ("for work you repeat"), never by its mechanism ("rules scoped
to a folder", "a server that exposes tools"). Ice skates are described as what you skate on, not as
sharpened blades that overcome friction. The mechanism belongs to the material the viewer opens
next.

**Contrast a thing by what each is for, never by what the other lacks.** "Unlike X, this can …"
asserts an absence nobody checked, and is often wrong about X.

**Every piece opens before it explains.** By the end of its opening, the viewer has been told what
this is and what they will get from the next minute or two. "What they will get" is named outright
as what they will be able to do in their own work, from the viewer's side, never a list of the
topics the piece covers and never the artifacts a course has them make ("you will have built a
template, a checklist …" is the course's view, not the viewer's). A short hook showing the problem
may come first, but no piece goes into its content before the viewer knows what they are watching;
a piece that opens on its first demonstration starts cold. This is the title and hook of explainer
practice, and the first two of Gagné's events of instruction (gain attention, state the objective).
The purpose file says what the opening holds for its kind of piece.

**An example illustrates a point; it never stands in for it.** A line that narrates an example's
details in place of the point it stands for fails; an example that demonstrates the point passes.
With a broad Viewer line ("anyone new"), draw examples from more than one kind of work, so no viewer
reads the piece as aimed at someone else.

**State nothing the subject will change unless the action needs it.** A narrated piece is the most
expensive thing to rebuild, and its subject is usually the cheapest to edit, so a detail that moves
with the subject makes the piece stale on the day it moves. What moves is durations, counts,
numbering and version numbers, locations and addresses, and what a page currently lists: leave those
out unless the viewer acts on them. Keep what the action needs, such as the exact text they type or
the menu they click: that is the picture, and the brief's Source line records the version it
matches. **A concept's established name and a part's title are not in that list.** They are the
words the viewer meets next, so name them; calling a part "the next one" instead of its title talks
down. Technical writing calls this evergreen content.

**A title heard is not a title seen.** A part whose title is also an ordinary word ("Skills") does
not register as a title by ear: say "the Skills training", and show the title on the stage.

**Never preview a list you are about to walk.** If the piece takes five things one at a time, do not
open with a scene naming all five: the viewer meets each twice and the second meeting is the one
that teaches, and the walk then opens each scene with a dead ordinal ("the third failure is…")
instead of re-entering by its own subject. A card listing the five can stay, because a viewer who
leaves early takes the card with them; what goes is the *narration* of the list. A spoken preview
and its ordinals cost runtime and carry no idea the walk does not, so cutting both loses nothing.

**Write the script as spoken lines, one sentence each.** A line is the unit: it gets its own moment
on screen and its own picture. Each line holds two strings, and they differ:

- `say` is for the speech engine: `"A S D, S T E one hundred"`, `"A I"`. Only punctuation a voice
  can perform: no semicolons, parentheses, slashes or quotation marks.
- `caption` is for a reader: `"ASD-STE100"`, `"AI"`, and it can carry what the voice cannot: `It
  does not mean "near".`

Beside each line, write its **stage labels** in the line's `stage` field: what is on screen while
it is spoken. The reviewers read them with the line.

**The budget in words, so it can be checked before anything is drawn.** At Kokoro `af_heart`, speed
1.0, and these pauses, speech runs about 3.35 words a second and silence takes about a third of the
runtime. So **two minutes buys roughly 255 spoken words** and three buys about 385.
`build_audio.py` counts before it speaks: over 255 it says so, over 385 it refuses, and either way
it lists each scene's words and points at the brief to choose the cut. Run it with `--count` at
stage 7, before Set B (`python build_audio.py --count`, which needs no speech engine), so a cut is
reviewed once rather than after the reviews passed. Change the voice or its speed and these move:
remeasure on one built piece and change `TARGET, CEILING` there. A first cut over the budget is the
moment to cut, which is far cheaper than cutting after the pictures exist; with
nothing counting, nothing stops a two-minute piece from shipping at three.

**The voice explains; the stage shows; never the same words in both.** Mayer's modality and
redundancy principles: people learn more from narration with pictures than from printed text with
pictures, and printed text that repeats the narration makes them learn less, because eyes reading
words cannot also read the picture.

- **Stage text is labels:** a name, a number, a few key words that point at part of the picture,
  never the sentence the voice is speaking. If a spoken line says what the stage already prints, cut
  one of them, whatever the runtime.
- **Words that are the thing shown stay on the stage:** what the viewer will type, a message the
  tool returns, a menu path to click. They are the picture. The voice says what to do with them
  ("type this", "undo is here") and does not read them out; three or four words is the limit for
  showing and saying at once. Show each once: a menu path drawn as the menu is not also a line of
  text in the same frame.
- **Captions are always available and never a second copy forced on a listener.** Access practice
  requires captions (WCAG 1.2.2), so the page always has them, as captions a viewer can turn on and
  off, and the video file carries them as a track. Whether they start on follows question 2: an
  audience that all has sound starts with them off and the button showing; any audience without
  sound starts with them on, and then the captions are the narration, so the stage still carries
  only labels. A mixed audience starts with them on on purpose: the viewer without sound would
  otherwise get nothing, and a listener turns them off with one press. The transcript, docked beside
  the player, is off the stage and the viewer's to read or not; it is not a copy in this sense
  (`build-page.md`, the screen contract).

**The silence is the mechanism, not padding.** Put real silence before each line and put the picture
up *during* it, so the picture is complete and still before the voice starts explaining it. That
pause is the moment the viewer uses. It comes in two lengths, and a flat gap reads as a metronome:

- **0.3–0.5s** between sentences that share a picture;
- **2.2–3.8s** where the picture turns.

To match a narration you admire, measure its pauses from word timings and ffmpeg's
`silencedetect`. The templates use 0.4 and 2.4, with `head` and `tail` of 1.3 making a 2.6s pause
between scenes, and any line can override the short default with its own `pause`. The reveal
animation must be shorter than the gap it runs inside, or the fade eats the pause. The lead is
derived from the measured silence, `min(1.2, pre - 0.05)`, never fixed. Pauses cost runtime
directly, about a third of it: say so when you report the length. **Measure a reference, do not
eyeball it:** watching and describing is too coarse to recover either the pause tiers or how a
player's transport behaves.

## Drawing

Warm off-white or paper ground, near-black ink, one accent, green for right and red for wrong,
amber for caution. Simple shapes over detailed drawings. Fades and short slides; plain cross-fades
read better than morphing text.

- **Draw right and wrong as paths, never as glyphs.** No font carries a tick reliably, bold is
  silently ignored, and the mark changes size between machines.
- **A before/after comparison shares one frame** (same box, same position), or the viewer compares
  across a hard cut from memory.
- **A crossfading pair ramps linearly**, so the two opacities sum to one and the outgoing copy is
  never legible under the incoming one.
- **Check frames, not the build.** A build passes with defects only a look catches: a shape that
  reads wrong, text past its box, marks sitting on a border.

## Rules for the session using this skill

- **Do not change this skill's rules while making a piece with it.** When a rule is wrong, write the
  defect in the piece's folder (`SKILL-DEFECTS.md`) for whoever maintains the skill, and work around
  it in the piece. A session that changes the rule it is working under can make any claim it has
  made come true, for example by renaming the last stop so that "the piece is done" becomes true.
  Writing a purpose file the skill does not yet have is the one addition the skill asks for.
- **Whoever maintains the skill applies defects as they are found**, not at the end of a run, and
  each change is reviewed against the whole skill, not only the line it touches: a one-line fix can
  delete an earlier fix's carve-out unnoticed.

## Known limits

- **The brief and the budget are held by reviewers and a word count, not by watching.** No agent
  can watch a timed piece; reviewers read the transcript and the stage text.
- **The page's scenes are hand-written** in `<subject>-explainer.html`, beside the same lines in
  `narration.json`; `build_audio.py` writes the timing into the page and refuses if a caption has
  drifted, but the drawing is kept in step by you, and for both forms so is `scene.py`.
- **Trying the piece on real viewers is outside this skill.** Its cold readers (`reviews.md`, Set C)
  are stand-ins, not viewers.
