"""Build the Stop 3 review page (stop.html): the piece's page itself, player first, with the review
record beneath it and, when there is one, the captioned video file from package/ below that.

Reads the piece's *-explainer.html (after build_audio.py has written its TIMING block),
stop3.json (every sentence this page adds), stop3-reviews.json (the review record, written only
from review reports that exist) and narration.json (`name`, for the video file).
For a video file only there is no page to wrap: write stop.html by hand (see stops.md).

Needs only Python. Run: python build_stop3.py
"""
import html as H
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def load(name, hint):
    path = HERE / name
    if not path.exists():
        sys.exit(f"{name} is missing: {hint}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


pages = sorted(HERE.glob("*-explainer.html"))
if len(pages) != 1:
    sys.exit(f"expected exactly one *-explainer.html, found {len(pages)}")
page = pages[0].read_text(encoding="utf-8")
spec = load("narration.json", "the script")
text = load("stop3.json", "copy it from the skill's templates and rewrite every sentence for this piece")
reviews = load("stop3-reviews.json", "write it from the review reports in this folder, one {verdict, who, what} per review")
e = H.escape

video = Path("package") / f"{spec['name']}.mp4"
if text.get("video_text") and not (HERE / video).exists():
    sys.exit(f"{video.as_posix()} does not exist: run build_publish.py first, or drop video_text for a page only")

STYLE = """
<style>
.stopband { display: grid; gap: 12px; margin: 0 0 30px; padding: 0 0 26px; border-bottom: 1px solid var(--line); }
.stopk { font-size: 11px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--accent); margin: 0; }
.stopband h2, .after h2 { font-size: 18px; margin: 6px 0 0; }
.stopband p, .after p, .stopband li, .after li, .after dd { font-size: 15px; line-height: 1.6; margin: 0; }
.stopband ul, .after ul { margin: 0; padding-left: 20px; display: grid; gap: 6px; }
.stopband ul.reviews { list-style: none; padding: 0; }
.verdict { font-weight: 700; color: var(--accent); }
.ask { border-left: 3px solid var(--accent); background: var(--surface); padding: 9px 13px; font-weight: 600; }
.ask.open { border-color: var(--caution-ui); }
.after { display: grid; gap: 12px; margin: 34px 0 0; padding: 26px 0 0; border-top: 1px solid var(--line); }
.after video { width: 100%; max-width: 44rem; height: auto; border: 1px solid var(--line); border-radius: 8px; background: #000; }
.after dl { margin: 0; display: grid; gap: 8px; }
.after dt { font-weight: 700; font-size: 15px; }
.guess { color: var(--caution); font-weight: 700; }
</style>
"""

review_items = "".join(
    f'<li><span class="verdict">{e(r["verdict"])}</span> <b>{e(r["who"])}.</b> {e(r["what"])}</li>' for r in reviews)
record = f"""  <section class="stopband after" id="review">
    <p class="stopk">Stop 3 of 3 &middot; {e(text["cut"])}</p>
    <p class="ask">Who checked this before you, and what did they find?</p>
    <h2 style="margin-top:0">Who reviewed it</h2>
    <ul class="reviews">{review_items}</ul>
    <h2>What changed</h2>
    <p>{e(text["changed"])}</p>
    <p class="ask">{e(text["ask"])}</p>
  </section>
"""

video_section = f"""
  <section class="after">
    <h2>The video file</h2>
    <p>{e(text["video_text"])}</p>
    <video controls preload="metadata" poster="{e(text.get("poster", "stills/1-open.png"))}" src="{video.as_posix()}"></video>
  </section>
""" if text.get("video_text") else ""

guesses = "".join(
    f'<dt>{e(g["term"])}</dt><dd><span class="guess">Guess:</span> {e(g["guess"])}</dd>' for g in text.get("guesses", []))
delivery = f"""
  <section class="after">
    <p class="ask open">{e(text["delivery_ask"])}</p>
    <h2>Delivery</h2>
    <p>{e(text["delivery_text"])}</p>
    {f"<dl>{guesses}</dl>" if guesses else ""}
  </section>
"""

replies = f"""
  <section class="after">
    <h2>What a reply can say</h2>
    <ul>{"".join(f"<li>{e(r)}</li>" for r in text["replies"])}</ul>
  </section>
"""

out = page.replace("</style>", "</style>" + STYLE, 1)
# The player and its transcript open the page; the review sits directly beneath them, so nothing
# is added above the player.
out = out.replace('<p class="eyebrow">Explainer</p>', "", 1)
anchor = '<p class="note">'
if anchor not in out:
    sys.exit('the page has no <p class="note">: the review record is placed after it')
i = out.index(anchor)
j = out.index("</p>", i) + len("</p>")
out = out[:j] + "\n" + record + video_section + delivery + replies + out[j:]
note = "<!-- Made by build_stop3.py from the piece's page, stop3.json and stop3-reviews.json: rebuild it rather than editing this file. -->\n"
doctype = "<!doctype html>\n"
if out.lstrip().lower().startswith("<!doctype html>"):
    out = out.lstrip()[len(doctype) - 1:].lstrip("\n")
(HERE / "stop.html").write_text(doctype + note + out, encoding="utf-8", newline="")
print("wrote stop.html")
