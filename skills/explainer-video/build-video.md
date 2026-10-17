# Building the video file form

Load at stage 8 of SKILL.md, when the script has passed Set B. The templates build the video file
and the page from one `narration.json`; SKILL.md stage 3 says what to copy, and `build-page.md`
step 1 what a piece replaces. `templates/scene.py` draws the same three example scenes as the
page template, with the timing machinery (`beat`, `hold`, `finish`) you keep.

**Both forms from one script.** When the person wants both, build one folder: `build_audio.py` makes
the voice and `timing.json` once, the page reads them through its `TIMING` block, and `scene.py`
reads the same `timing.json`. At stage 8 build the page and take Stop 2's stills from it
(`build-page.md`). At stage 10 draw `scene.py` to match them, render its stills with step 3, and
look at each pair side by side: the two drawings are separate code, and nothing else checks that
they agree. A script change is one edit to `narration.json`; any rerun of `build_audio.py` is
followed by a re-render, because the video is timed to the audio it was rendered against.

**A video file only:** do not copy the page. `build_audio.py` and `build_publish.py` skip their page
steps, `check_timing.py` is not used, and Stop 3's page is the video player with the review around
it (`stops.md`). The drawing and its stills (steps 2 and 3) are stage 8.

## The steps

1. **Voice and timing:** `python build_audio.py`, as in `build-page.md` step 2. The video uses
   Kokoro `af_heart` like the page, so the word budget (set for that voice) applies to both. Speech
   is normalised to -16 LUFS, the usual level for spoken video.
2. **Drawing:** `scene.py`, written with [Manim](https://www.manim.community/). One function per
   scene builds its settled frame; one `Scene` class per scene shows that frame alone (the stills);
   the `Explainer` class plays all of them in order. Its `beat(n, ...)` places an animation in the
   silence before line `n`, from `timing.json`, as the page does (`build-page.md` step 3), and
   `plus=` places one inside a line. Its deadline for a `plus` beat on a scene's last line is the
   scene's end less 0.6s, looser than the page's check. Text is drawn in the font named by `FONT`;
   Manim substitutes another without saying so when it is missing, so look at the stills.
3. **Stills for Stop 2:** `python -m manim -s -qh scene.py S1Open` (and so on, one `Scene` class per
   scene) renders each scene's last frame to `media/images/scene/`; copy each into `stills/` under
   the name the stop page uses (`<n>-<scene id>.png`). A still enlarges in place when clicked on the
   stop page.
4. **Render and join:** `python build.py` (`-ql` for a quick draft, `--mux` to skip the render and
   only rejoin the audio). The render **fails** if any beat is still animating when the voice
   reaches what it draws, and writes the result to `timing-check.txt`: this is the video's timing
   check. It then joins the scene clips and muxes the voice into `<name>.mp4` (`name` from
   `narration.json`) with `+faststart`.
5. **The first frame is a picture.** A player shows the first frame before Play, so scene 1 opens
   on a drawn frame, never a blank ground; on the stop page give the `<video>` a `poster` of the
   first still.
6. **Captions:** the video file carries them as a separate track a player can turn off, never drawn
   into the frame. `build_publish.py` builds a WebVTT file from `narration.json` captions and
   `timing.json`, and muxes it into the MP4 as a `mov_text` track in `package/`; the `.vtt` also
   ships beside the file for players that take one. The package is built at stage 10, before Stop
   3, and the Stop 3 page plays `package/<name>.mp4`, so the person judges the file viewers get.

Setup for Manim and the speech engine: SKILL.md, "What it runs on".

## What the video file cannot do

It cannot jump to a scene, step, show a transcript beside the picture, or follow light and dark. A
viewer with no sound gets the captions track only if their player shows it. If those matter for
this audience, the page is the form, or both.
