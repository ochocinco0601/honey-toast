# Brief: one lesson video for a training kit

Give this to each helper that builds one lesson's video in a set. Fill in the bracketed parts; the
rest is what every lesson video in a set needs, so a helper does not relearn it.

You build ONE lesson's narrated companion video, script to package, the way the first video in the
set was built. Follow that video; add no new mechanisms or checks.

## Copy the first video
- Your folder sits beside the first video's and is named the way the set's folders are. Read that
  folder first: `narration.json` (with its `page` block) and `scenes.py`. Also write the two notes
  this brief asks of every video, `SCREENS.md` (what each screen shows) and `CLAIMS.md` (each
  factual claim and its source), even if the first video lacks them.
- The builder is this skill's `builder/` (`build_audio.py`, `check_timing.py`, `build_page.py`,
  `build_publish.py`, `kitparts.py`, `serve.py`); the docs are `SKILL.md` and `build-page.md`.
- If the set has a written agreement on the package (files, scene ids, the link back), build to it.

## The cut
- Narrate the lesson's main path: its numbered steps, not folded troubleshooting or answers. Each
  scene carries `step`, the step number it narrates (null for the opening and the close). At each
  check in the lesson, say to pause and do it, then show what to look for.
- Open with what the unit does; close with the kit's own instruction for finishing the unit, word
  for word.

## What every lesson video gets right
- Use the kit's own words for its parts (for example "unit" and "the written steps", if that is
  what the kit says), never a word of your own.
- Requests to paste are shown on screen, not read. To use one, say how the kit's page offers it,
  for example: "In the written steps, select Copy beside this request. Paste it into the chat box,
  and press Enter."
- A button name spoken inside a sentence is marked by ear: "select the button Yes, I trust the
  authors".
- Short lines, one action or fact each; no stacked qualifiers.
- Every word drawn on screen is spoken, or drawn as gray bars. Say once, early, exactly: "Gray bars
  stand for text you don't need to read." Words the narration names must be readable: show an
  enlarged copy of the same kit parts beside the source (`kitparts` inset), joined by a mark line,
  in a neutral frame, cut at whole parts, the rest faded.
- Every factual claim about the tool the kit teaches goes in `CLAIMS.md` with its source (the kit's
  own claims register if it has one, the tool's documentation, the tool's source at a named
  version); mark what you cannot verify. Say nothing the lesson does not support; if the lesson
  itself is wrong, report it rather than silently diverge.
- A step the kit words one way everywhere (a trust prompt, a permission request) is narrated in the
  kit's wording, every time.
- A video whose narration runs past about six minutes is split into chapters (`chapter` on its
  scenes; see `builder/examples/lesson-demo/`).

## Steps
1. Script (`narration.json` in the builder's form), `SCREENS.md` and `CLAIMS.md`. Have one cold,
   independent reviewer with an editorial lens read it against the lesson; act on its findings once.
2. `scenes.py` from the kit's drawing parts, with the same calls and arguments as the lesson's
   pictures.
3. `python <skill>/builder/build_audio.py <folder>` with the Python that has the speech engine,
   then `python <skill>/builder/check_timing.py <folder>`.
4. Operate it in a visible browser tab, served by `builder/serve.py`: each `#<scene id>`; Play after
   a jump starts the scene's first line; with the sound off, captions one line at a time; fit at
   1366x657 and at 683 wide.
5. Package: `python <skill>/builder/build_publish.py <folder> <kit>/videos/<training>/<stem>`. Rebuild
   the kit with its own build and confirm its checks pass with no stale-video warning. On the
   lesson's page, open the video in place from under the title and close it again; open it from
   the kit's outline, which opens the lesson with the video open; and check the previous unit's
   Continue opens the lesson with the video closed. A lesson has one video, opened where the
   learner is: no per-step links into it and no separate page for it.
6. Stop any server you started.

Do not touch other lessons' folders or videos, the kit's maintenance scripts, the builder (report a
fault in it instead), the set's agreement, or the kit's change notes.

## Commits
Commit to your own branch as you go, by path, adding new files first. Do not push. Commit the
kit's rebuilt pages separately from everything else, so whoever merges can rebuild them.

## Report (under 200 words)
Branch and commits (say which holds the rebuilt pages); length and scene list (id, step);
unverified claims; the reviewer's findings and what you did; any fault in the lesson or the
builder.
