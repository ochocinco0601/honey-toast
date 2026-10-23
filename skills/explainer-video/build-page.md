# Building the page form

Load at stage 8 of SKILL.md, when the script has passed Set B. **The page is generated, never
written by hand:** this skill's builder, `builder/`, writes it from the piece's data, and its
template `builder/page-template.html` is the design (step 8). Its two examples are the references:
`builder/examples/overview/` is a short piece drawn with plain shapes, and
`builder/examples/lesson-demo/` is a lesson video built from a training kit's own drawing parts,
with chapters and step numbers.

Every command below takes the piece's folder. `<skill>` stands for this skill's folder; run the
commands from the folder that holds your pieces, and give a kit's path relative to it.

## The steps

1. **The folder holds data, not code** (stages 0 and 3 of SKILL.md): `<subject>-explainer/` with
   `narration.json` (what is spoken, and the `page` block: title, standfirst, the Summary's HTML,
   and for a lesson video the lesson, its link back and the kit) and `scenes.py` (what is drawn:
   `BEATS = {scene id: [beat, ...]}`). `builder/explainer.py` says what every field holds. A lesson
   video sets `"kind": "lesson"`, gives each scene its `title`, its lesson `step` (or null) and,
   past about six minutes, its `chapter`.
2. **`python <skill>/builder/build_audio.py <folder>`**, with the Python that has the speech engine.
   Counts the words first (SKILL.md, "The budget in words"), then speaks one clip per line, pads
   it, joins one clip per scene normalised to -16 LUFS, writes `timing.json` (each scene's length
   and the **measured** start of every line), writes the page from the data (its `TIMING` block
   included), and fails if a caption in the page differs from `narration.json`. A scene whose words
   and pauses are unchanged is not spoken again (`audio/.made.json`; `--all` speaks everything).
   Pacing is configuration (`head`, `gap`, `tail` and a line's `pause`), so changing it is one edit
   and one command. It finds the Kokoro model files through the `KOKORO_MODELS` environment
   variable, and ffmpeg on PATH or bundled with `imageio-ffmpeg` (SKILL.md, "What it runs on").
   After a change to `scenes.py` or the `page` block alone, `python <skill>/builder/build_page.py
   <folder>` rewrites the page without speaking.
3. **Place beats by line, never by stopwatch.** A beat says `"line": n` and lands at
   `starts[n] - LEAD`, inside the silence. Use `"plus": s` only when the thing illustrated is a
   *phrase* and not the whole line; drift there is bounded by one spoken line. Draw with
   `builder/stage.py` (shapes and labels on the 960 by 540 stage) or, for a lesson's screens,
   `builder/kitparts.py`: the kit's own parts, one part's fragment per beat, the picture put on the
   stage by one transform (`kitparts.Picture`). A screen with the same content as a picture in its
   lesson is drawn by the same calls with the same arguments, so its checked claims carry over.
4. **`python <skill>/builder/check_timing.py <folder>`.** Reads the beats from `scenes.py`, the same
   data the page is made from, and exits non-zero if any beat is still animating when the voice
   reaches what it draws. It prints the beat split and the runtime, which is how you check the
   budget.
5. **Audio plays through detached `Audio` objects**, one per scene, never inserted into the DOM,
   and the scene advances when its clip ends. A scene therefore cannot run past its own line, and
   nothing accumulates across scenes.
6. **The bar reports the scene; the clock reports the second.** The thumb holds at the current
   scene's position while it plays and steps at the boundary, and **the filled portion of the
   track steps with it** rather than flowing. The bar answers "where am I in the sequence". Keep
   the tick marks proportional to scene length, and snap a drag to the scene it lands in, guarding
   the handler so a drag inside the current scene does not re-seek its audio on every pointer
   event. **The clock keeps running:** with both held, a viewer with the sound off sees nothing
   change for seconds at a time, and the end state shows the bar short of its edge beside a clock
   short of its total. **A stepped bar needs a track you can see:** a filled portion and an
   unplayed groove at 3:1 or better against the ground (WCAG 1.4.11, non-text contrast); below
   that, the bar can read as missing.
7. **The screen contract: what the viewer sees on load.** The reference class is the
   video-learning player (a video site's desktop page with its transcript open; course platforms).
   At a laptop-sized window (a 1366×768 screen, viewport about 1366×657), on load and with no
   scrolling, the stage, the caption and the transport with its beat line are visible together,
   sized to the window's height, with at most one line of title above them; the standfirst and
   Summary go below the player. The transcript docks to the right of the player, highlights the
   line being spoken, and seeks when a line is clicked; on a narrow screen it stacks below. The
   player has its own cap, never the page's text column: the wide reading column (about 68rem) is
   for text. The template sizes the player from the space actually left in the window and gives the
   transcript the rest; keep that rather than a CSS guess.
   - **With the sound off**, captions are on and carry the piece: the caption box at its longest
     line must still leave the whole stage and a one-row transport inside the window.
   - **A page inside another page's frame sees the frame's width, not the window's**, so a
     breakpoint fires at a different window size than when the file is opened on its own. Measure
     it opened the way its viewers will open it.
   - Widening the page for its text must not grow the 16:9 player past a laptop screen, and a
     transcript stacked under the player cannot be read while watching: both are failures of this
     contract, not matters of taste.
8. **The page's design is the builder's template; keep it.** Every page is generated from
   `builder/page-template.html`, changing only what carries the subject (below). A change to the
   design is a change to the template, reviewed as one, and every video takes it at its next build.
   Its parts, top to bottom:
   - **The lesson link** (when the `page` block has `back_href`): one strip above the title,
     "Written steps: <title> &rsaquo;", or "Back to the trainings &rsaquo;" for an overview. It
     serves a package opened on its own. Inside a kit (`?in=kit`) the page hides the strip and the
     title line, and the kit opens the player in place on the lesson page.
   - **One title line:** the `<h1>` and, beside it, a quiet meta line (Video, the scene count
     and the running time, both filled by the script).
   - **The player**, the one element with a card's weight (radius and shadow): the stage, then a
     dark console holding the caption and a one-row transport, grouped as play, previous and next;
     the scene bar, which scene boundaries cut into segments; the readout; then sound, CC, speed
     and replay. `fitPlayer()` caps it at `MAX_PLAYER` (860px) and the window's height.
   - **The transcript**, docked right and transcript only: a header, then lines grouped under
     sticky scene headings ("Scene 2: <title>"), under chapter headings when the video has
     chapters, the current line marked with the same amber rule as the caption. A chapter boundary
     cuts the scene bar deeper.
   - **The reading column**, `<section class="about">`, 68rem wide and starting on the player's
     left edge (the script sets the page's width, `--tw`, to the player and transcript together):
     a heading, the standfirst as a lead, the Summary (or the job aid's text; where the subject has
     parts, a lead paragraph, the parts as a `ul.parts` list, then where to start), then "Using the
     player" with its keys and the note on how the bar and sound behave. Nothing that is reading
     text goes in a tab beside the player.
   - **The player's keys** (Space, the arrows, C for captions) work wherever focus is on the page,
     as a video player's do; the scene bar keeps its own arrows.
   - **Tokens are in two groups.** The stage tokens (`--bg --paper --ink --muted --line --accent
     --accent-soft --caution --caution-ui --good --bad`) are what the drawing reads and what the
     video file and stills match ("Drawing" in SKILL.md): change them only with the video. The page
     chrome tokens are the design's own. Both have light and dark values, generated from one table
     in `builder/explainer.py`. A piece with a `kit` in its `page` block wears the kit's palette:
     the kit's tokens, read from its `maintaining/build_pages.py`, with the explainer's aliased onto
     them, and the kit's `.dg-*` drawing stylesheet goes in once when a beat uses a kit part.
   - **No web fonts and no CDN**: type is system stacks, so the page works offline and on a
     network that blocks font hosts. The stage's text uses the same sans.

## Stills for Stop 2

Serve the folder or open the page from disk, drive each scene to its settled point ("Operate it",
below: jump to the scene from the transcript), and screenshot the stage with your browser tool into
`stills/`, named `<n>-<scene id>.png` (a scene with two pictures adds a letter: `2a-...`). Each still
is named, with its alt text, in `stop2.json`. For both forms these are the stills; `scene.py` is
drawn to match them at stage 10.

## Everything in the page that carries the subject

The scenes are the obvious part and nowhere near all of it. Each of the others is a field of the
`page` block in `narration.json`, and only the captions are checked against anything; the rest
rides on you noticing:

`title` (the `<h1>` and the lesson link's words) · `doc_title` (the browser tab) · `standfirst` ·
`stage_label` (the stage's `aria-label`) · `summary_html` (the reading column's Summary, the job
aid's text when there is one) · `back_href` · each scene's `title`, `step` and `chapter`. The note
under "Using the player" is the template's and is the same for every piece. Keep
`<section class="about">` in the template: `build_stop3.py` places the review record after it.

**A note with hard counts is the trap.** A sentence such as "of the 44 marks, 13 …" goes wrong the
instant a beat changes, and nothing checks it. `check_timing.py` prints the real split; copy it from
there or state no number.

**Where the person's answers land:**

| Answer | What it touches |
|---|---|
| sound off at the start | the template: `sound = true` in the player, the sound button's `aria-label`, the poster's hint; and the standfirst if it promises sound |
| captions start off (everyone has sound) | the template: the `#cc` button's `aria-pressed` and `aria-label`, and `hidden` on `#caption` |
| captions carry the piece | the `caption` column throughout, written as reading text rather than a transcript |
| the pacing | `head`, `gap`, `tail` and any line's `pause` |

## Operate it. Do not compute about it.

**Drive the page** in a visible browser tab: run `python <skill>/builder/serve.py <folder> 8777`
and open `http://127.0.0.1:8777/<name>-explainer.html` (or `package/index.html`, the delivered
form), and click things with your browser tool. **Not `python -m http.server`:** it serves no byte
ranges, so the browser cannot seek a clip, and a transcript line in the middle of a scene plays
from the scene's start, a fault the published page does not have. If another session shares the
browser, emulate the viewport on your own tab rather than resizing the window. Reading the page's state with a script in the tab tells you what it is really
doing. A hidden or background tab loads and plays nothing, so a check of playback, the transcript's
follow or click-to-seek made there proves nothing: check `document.visibilityState` first. Then
check fit as the viewer will open it (`stops.md`, "How every stop works").

Review passes, arithmetic and screenshots do not reach **interaction** defects, such as a muted
piece paced by a speech recording, or a jump landing on a scene that has not finished drawing.
Only using the page shows them, so operate it.

The checks to run every time, each a line of script in the tab:

- jump to every scene from the transcript: the right scene is visible and every beat is drawn,
  except one that fades out, which must be gone;
- next and previous step both ways, each landing finished; previous does not underflow at the
  first scene;
- the poster computes to `display: none` after Play;
- the sound toggle rebuilds the timeline, the ticks and the transcript, and leaves the viewer on the
  scene they were on;
- muted playback stops when a scene has finished drawing rather than running on, and Play there
  goes on to the next scene;
- the transcript highlights the line being spoken, and clicking a line plays from it;
- the scene address: `#<scene id>` on load and as a `hashchange` opens that scene finished and
  paused, previous and next work from there, and an unknown id opens at the start;
- the console shows no errors, and the page is in standards mode (`document.compatMode` is
  `CSS1Compat`).

## Gotchas

- **The poster and `[hidden]`.** `.poster` sets `display`, which outranks the browser's own rule
  for `[hidden]`, so without `.poster[hidden] { display: none; }` the pill never leaves and its
  full-bleed button swallows every click on the stage. The template has the rule; keep it.
- **No `<audio>` element.** Probing for `document.querySelector("audio")` reports *no audio* for a
  fully narrated piece, because the clips are detached objects. Instrument
  `HTMLMediaElement.prototype.play` rather than reading the DOM.
- **`var` hoisting.** `buildTimeline()` reads `sound` and `audioOK`; declared below it, they are
  `undefined` when it first runs and the first timeline is always the muted one.
- **Landing a jump at the settled point breaks `prev`** if its rule assumes jumps land at a scene's
  start; the template's `prev` already accounts for it.
- **The file is ASCII.** The builder writes any non-ASCII character in the page's HTML as an HTML
  entity and in its script data as a `\u` escape, and refuses a page that is not ASCII; a stray
  byte mojibakes when the file is opened from disk. In the template, build a mark from
  `String.fromCharCode` or draw it.
- **The page is generated; never edit it.** Line 1 says so; change `narration.json`, `scenes.py`
  or the template and rebuild.
- **The package is `build_publish.py`'s** (`python <skill>/builder/build_publish.py <folder>`):
  `package/index.html` with comments, host-only meta tags and fonts stripped, `audio/`, and
  `video.json` (the scenes, the files and their hashes; for a kit's video also the lesson, the hash
  of the lesson's text and the link back). It refuses a page with a build machine's path or a date
  in it, so neither goes in `summary_html` or a caption.
- **Keep the doctype.** A page without `<!doctype html>` renders in quirks mode when opened from
  disk, and its layout shifts. The template and the stop-page builders write one.
- **A 960-unit stage is unreadable at phone width.** That bounds how much belongs in one scene.
- **`fitPlayer()` holds the layout's numbers:** the 960px breakpoint (also in the CSS), the
  player cap, the transcript's 320 to 460px, and the 16px clear below the player. Change a
  border, gap or padding in the player and re-measure the fit at 1366x657, sound on and off.
