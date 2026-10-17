# Building the page form

Load at stage 8 of SKILL.md, when the script has passed Set B. The template is
`templates/example-explainer.html`: a working three-scene page that builds from the template
`narration.json` and meets the screen contract below. Its player, transport, transcript and sizing
are the part you keep; its scenes and its text are the part you replace.

## The steps

1. **The folder and its scripts** were made at stages 0 and 3 of SKILL.md (`<subject>-explainer/`).
   Now copy `templates/example-explainer.html` in as `<subject>-explainer.html` and write its scenes
   and captions before step 2, which checks the captions against the script. The scripts find the
   page as the one `*-explainer.html` in the folder, so keep exactly one.

   **What a piece replaces:** the scene definitions (`S.push({...})`, one per scene, with the
   drawing helpers above them that only the example uses) in `<subject>-explainer.html`, and in
   `scene.py` for both forms; every text in the page that carries the subject (below); `title`,
   `name` and `about` in `narration.json`; and the sentences in `stop2.json` and `stop3.json`
   (`stops.md`, "Building a stop page"). The Python scripts need no edits. `build_audio.py` and
   `build_publish.py` also run without a page, and `build_publish.py` without a video file.

   **Keep the shapes the scripts read**, or a check fails or, worse, passes on nothing:
   the `  var TIMING = {` … `  };` block with its two-space indentation; each caption written as
   `caption: "..."` on one line, matching `narration.json` exactly; one `S.push({` per scene,
   each with `id: "..."` first; at least one beat per scene; beats written with literal numbers
   (`{ line: 2, plus: 1.6, ... }`); and no comment containing the word "line" followed by a colon,
   which `check_timing.py` would read as a beat.
2. **`python build_audio.py`.** Counts the words first (SKILL.md, "The budget in words": over 255
   it warns, over 385 it refuses), then speaks one clip per line, pads it, joins one clip per scene
   normalised to -16 LUFS, writes `timing.json` (each scene's length and the **measured** start of
   every line), writes those numbers into the page's `TIMING` block, and fails if a caption in the
   page has drifted from `narration.json`. Pacing is configuration (`head`, `gap`, `tail` and a
   line's `pause`), so changing it is one edit and one command; a hand-copy between two files is a
   two-place edit that breaks silently. Needs the speech engine and ffmpeg (SKILL.md, "What it runs
   on").
3. **Place beats by line, never by stopwatch.** A beat names the line it belongs to and lands at
   `starts[n] - LEAD`, inside the silence. Add `plus` (seconds into the line) only when the thing
   illustrated is a *phrase* and not the whole line; drift there is bounded by one spoken line.
4. **`python check_timing.py`.** Computes every beat's deadline against the measured clip and exits
   non-zero if any beat is still animating when the voice reaches what it draws. It prints the beat
   split and the runtime, which is how you check the budget. **Write beats as literals:** a beat
   built in a loop cannot be read out of the source, and the check fails rather than skipping it,
   because a checker that silently ignores what it cannot parse reports the same clean result
   whether the page is right or unreadable. Share the *drawing* behind a helper if it repeats; keep
   the line and plus numbers literal.
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

## Stills for Stop 2

Serve the folder or open the page from disk, drive each scene to its settled point ("Operate it",
below: jump to the scene from the transcript), and screenshot the stage with your browser tool into
`stills/`, named `<n>-<scene id>.png` (a scene with two pictures adds a letter: `2a-...`). Each still
is named, with its alt text, in `stop2.json`. For both forms these are the stills; `scene.py` is
drawn to match them at stage 10.

## Everything in the page that carries the subject

The scene definitions are the obvious part and nowhere near all of it. One contract is
machine-enforced (the build refuses if a caption drifts from `narration.json`); every other item
rides on you noticing:

`<title>` · the eyebrow · `<h1>` · the standfirst · the stage's SVG
`aria-label` · the panel `<h2>` · the Summary prose (the job aid's text, when there is one) · the
closing note (`<p class="note">`, which `build_stop3.py` places the review record after; keep it).

**A note with hard counts is the trap.** A sentence such as "of the 44 marks, 13 …" goes wrong the
instant a beat changes, and nothing checks it. `check_timing.py` prints the real split; copy it from
there or state no number.

**Where the person's answers land:**

| Answer | What it touches |
|---|---|
| sound off at the start | `sound = true` in the player, the sound button's `aria-label`, the poster's hint, and the standfirst if it promises sound |
| captions start off (everyone has sound) | the `#cc` button's `aria-pressed` and `aria-label`, and `hidden` on `#caption` |
| captions carry the piece | the `caption` column throughout, written as reading text rather than a transcript |
| the pacing | `head`, `gap`, `tail` and any line's `pause` |

## Operate it. Do not compute about it.

**Drive the page** in a visible browser tab: open the file from disk, or run `python -m http.server
8777 --bind 127.0.0.1` in the folder (this computer only, not the network) and open
`http://127.0.0.1:8777/<name>-explainer.html`, and click things with
your browser tool. Reading the page's state with a script in the tab tells you what it is really
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
- **Keep the file ASCII.** Build any non-ASCII mark from `String.fromCharCode` or draw it; a stray
  byte mojibakes when the file is opened from disk.
- **Keep the doctype.** A page without `<!doctype html>` renders in quirks mode when opened from
  disk, and its layout shifts. The template and the stop-page builders write one.
- **A 960-unit stage is unreadable at phone width.** That bounds how much belongs in one scene.
