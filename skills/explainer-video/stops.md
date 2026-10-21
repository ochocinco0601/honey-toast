# The three stops, and delivery

Load at stage 6 of SKILL.md, before the first stop page is built.

The person who asked is the client. They see the plan at three points, while a note is still cheap
to act on, and you wait for them at each. This is the client review of video production: the
treatment, the script with its storyboard, and the rough cut, which ends in the final cut. Nothing
else goes to them for a decision; the craft calls in between are yours. **The client judges fit**
(their audience, where it plays, what it must say). **They are not the reviewer of the content**, so
a stop reaches them only after the reviews before it have passed (`reviews.md`).

| Stop | What they get | What their notes change |
|---|---|---|
| **1. The story** | In plain words: who it is for, what they will do after watching, what is left out, and each scene as one line, in order | What the piece says, and in what order |
| **2. Script and frames** | Each scene's spoken words and caption beside a still of its settled frame | The wording and the pictures |
| **3. Rough cut, then final cut** | The playable piece, both forms if both were asked for, the video file with its captions track | Timing, a scene that does not land, anything to cut |

**Stop 3 ends with an approved final cut.** If their rough-cut notes change anything, apply them;
a changed line goes back through Set B (and fresh readers, Set C, for the lines it changed); then
run Set D again and bring the same page back as the final cut, saying what changed. The final cut is
the exact version they approve with no further changes. Approval on trust of a version they have not
seen is not approval.

## Building a stop page

**The stop page is its own page, `stop.html`, in the piece's folder.** The delivered piece never
carries the stop's material.

- **Stop 1** has no builder: write `stop.html` by hand to the Stop 1 row, using the page template
  inside `build_stop.py` (its doctype, its styles and its one wide column, review record first)
  without the scene-and-still rows.
- **Stop 2**: `python build_stop.py` lays out each scene's still beside its captions. Every
  sentence on the page comes from `stop2.json` (the title, heading, lede, the "changed since" line,
  the ask, the guesses still unconfirmed, the reply options) and, per scene, its title, its stills
  with their alt text, and an optional note. Rewrite all of them for the piece; the builder refuses,
  naming what is missing, when a scene, a still or the review record is absent.
- **Stop 3**: `python build_stop3.py` wraps the piece's page itself, player first, with the review
  record directly beneath it and the captioned video file from `package/` below that; for a page
  only, leave `video_text` out of `stop3.json`. Its sentences (the stop's ask, the "what changed"
  line, the video file's description, the delivery ask and guess, the reply options) come from
  `stop3.json`: rewrite them. The `<video>` plays `package/<name>.mp4` (built at stage 10) with a
  `poster` of the first still. **For a video file only** there is no builder: write `stop.html` by
  hand, the `<video>` first and sized to the window as the screen contract says for a player, then
  the review record and the rest of the Stop 3 page as above.
- **The review record on the page** comes from a JSON list of `{"verdict", "who", "what"}` per
  stop (`stop2-reviews.json`, `stop3-reviews.json`). **A verdict is written there only from a review
  report that exists in the folder**, never ahead of it.

## How every stop works

- **One page.** `stop.html` is rebuilt in place at each stop: never a second page, never a
  before-and-after page. Its stills, audio and video sit beside it in the piece's folder, so its
  relative links resolve when it is opened from disk. Each stop's review is added to
  `REVIEW-stop.md` under its own heading, so the earlier stops' records stay.
- **The page carries the review; the message is the pointer.** The page opens with who reviewed
  it, the lens each reviewer used, and the verdict, then which stop this is, what changed since the
  person last looked, and whether their last notes landed. At Stop 3 the player comes first, sized
  to the window under the screen contract, so the person sees what a viewer will, with that record
  directly beneath it. Each part opens, under its heading, with the one question to read it with; a
  question after the content sends the reader back. The page cites nothing the person cannot open,
  and ends with what a reply can say. Text sits in a wide reading column (about `max-width:
  68rem`), never a narrow default; a player or a still keeps its own cap. A still enlarges in place
  when clicked.
- **Put it in front of them.** Open `stop.html` in the person's default browser for them where you
  can (on Windows, `Start-Process "<full path to stop.html>"`), and give its full path in the
  message as well.
- **The message that hands it over**, at every stop and the final cut alike, is the page's path and
  one line on what changed and what is wanted, standing alone because it may be read cold. Never
  walk the page in chat: a handover that only names the stop leaves them guessing, and one that
  restates the page buries it. A review record placed at the bottom of a long page, or text in a
  narrow column, is a defect of the page, not of the message.
- **Check every stop page as the person will see it, before handing it over:** opened from disk in
  a browser, at a laptop-sized window (1366×768 screen, a viewport of about 1366×657) as well as a
  phone and a desktop width. Any claim about what they will see names the surface it was measured
  on; "it fits on a laptop" measured on some other surface is a claim they will have to correct. If
  it fails, fix, have the stop page reviewer look at the change, and rebuild before the handover.
- **Their notes** come back in the conversation. They go into `NOTES.md` under the stop they came
  at, as the point in the field's terms, with their own words beneath it as provenance. A note that
  touches the brief changes the brief first, and everything after it is rebuilt from it. A brief
  changed after Stop 1 by a review, not by them, is shown at the top of Stop 2 as a change.
- **Any change after a stop's notes goes back through the reviews that ran before that stop**,
  operating the page included, before the page is rebuilt for them.

## Stage 12: delivery, and when the piece is done

The brief's "Where it plays" line names a place. **Generate the package; never hand-edit it.** It
is first built at stage 10 for Stop 3 and rebuilt here from the final cut. **A page only:** the
builder's `python <skill>/builder/build_publish.py <folder>` writes `package/` as `index.html`,
`audio/` and the manifest `video.json`, and refuses a page that is not clean; the rest of this
paragraph is the video file's package. **A video file, or both:** the template's `python
build_publish.py` writes it to the piece's `package/` folder, which it empties first and which git
ignores; it refuses to write over the piece's own folder. It holds the page as `index.html` with no
review material or code comments and no outside calls, with
`<!doctype html>`, `lang` and `charset`, and the audio beside it (when there is a page); the video
file with its captions track and the `.vtt` (when there is a video file); `job-aid.md` when there
is one; and a README saying what each version is and how to open it, written from `title` and
`about` in `narration.json` (read it, and correct those two if it does not read right for the
piece). Media carry no metadata. Set E checks it (`reviews.md`).

Then put it where the brief says, and check that it plays there (sound, captions, size):

- **A place the person has named that you can write to** (a folder, a file share, a documentation
  site): place it there only once they say to, never anywhere else you happen to have write
  access, then check it yourself, opened the way viewers will open it. A page goes as the
  `index.html`-and-`audio` folder together.
- **A place you cannot reach** (a chat channel, an intranet page): hand the person the package and
  exactly where each file goes (a page goes as the `index.html`-and-`audio` folder; a video file
  goes alone, with its `.vtt` if the place takes one), with the three checks (it plays with sound,
  the captions show, it fits the screen). Their confirmation completes "plays there".
- **A place with its own publishing procedure or review:** follow it; this skill does not replace
  it, and the place is never inferred from a name: the person says where the piece goes.

**The piece is done when the final cut is approved and it plays where the brief says it does.**
Until then, say which of the two is outstanding, never "done".
