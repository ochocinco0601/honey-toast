"""Build the Stop 2 review page (stop.html): each scene's still beside its spoken words.

Reads narration.json (the captions), stop2.json (every sentence on the page, and per scene its
title, its stills with their alt text, and an optional note), stop2-reviews.json (the review
record, written only from review reports that exist) and stills/<name>.png. It refuses, naming
what is missing, rather than building a page with a gap in it.

Needs only Python. Run: python build_stop.py
"""
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def load(name, hint):
    path = HERE / name
    if not path.exists():
        sys.exit(f"{name} is missing: {hint}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


spec = load("narration.json", "the script")
page_text = load("stop2.json", "copy it from the skill's templates and rewrite every sentence for this piece")
reviews = load("stop2-reviews.json", "write it from the review reports in this folder, one {verdict, who, what} per review")

problems = []
for s in spec["scenes"]:
    entry = page_text["scenes"].get(s["id"])
    if not entry:
        problems.append(f"stop2.json has no entry for scene {s['id']}")
        continue
    if not entry.get("alt"):
        problems.append(f"scene {s['id']} names no stills")
    for still in entry.get("alt", {}):
        if not (HERE / "stills" / f"{still}.png").exists():
            problems.append(f"stills/{still}.png does not exist")
if problems:
    sys.exit("\n".join(problems))

words = sum(len(l["say"].split()) for s in spec["scenes"] for l in s["lines"])
e = html.escape

rows = []
for n, s in enumerate(spec["scenes"], 1):
    entry = page_text["scenes"][s["id"]]
    imgs = "".join(
        f'<button class="still" type="button" aria-label="Enlarge picture for scene {n}" aria-pressed="false">'
        f'<img src="stills/{p}.png" alt="{e(alt)}"></button>'
        for p, alt in entry["alt"].items())
    lines = "".join(f"<li>{e(l['caption'])}</li>" for l in s["lines"])
    note = f'<p class="note">{e(entry["note"])}</p>' if entry.get("note") else ""
    rows.append(f'<li class="scene"><div class="pics">{imgs}</div><div class="words">'
                f'<h3><span class="n">{n}</span> {e(entry["title"])}</h3><ul class="said">{lines}</ul>{note}</div></li>')

review_items = "".join(
    f'<li><span class="verdict">{e(r["verdict"])}</span> <b>{e(r["who"])}.</b> {e(r["what"])}</li>' for r in reviews)
guesses = "".join(
    f'<dt>{e(g["term"])}</dt><dd><span class="guess">Guess:</span> {e(g["guess"])}</dd>' for g in page_text.get("guesses", []))
guess_section = f"""
<section>
  <p class="ask open">{e(page_text["guesses_ask"])}</p>
  <h2>Still to confirm</h2>
  <dl>{guesses}</dl>
</section>
""" if guesses else ""
replies = "".join(f"<li>{e(r)}</li>" for r in page_text["replies"])

page = f"""<!doctype html>
<!-- Made by build_stop.py from narration.json, stop2.json and stop2-reviews.json: rebuild it rather than editing this file. -->
<html lang="en">
<meta charset="utf-8">
<title>{e(page_text["title"])}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* Layout: one wide reading column, review record first; each scene is its picture beside its spoken words */
:root {{
  --bg: #f6f7f4; --surface: #ffffff; --ink: #1d2321; --muted: #5b6662; --line: #d9ded9;
  --accent: #1f6f78; --accent-soft: #e2f0f0; --open: #9a5b00; --open-soft: #fbf0dc;
  --display: "Segoe UI", system-ui, sans-serif;
  --body: "Segoe UI", system-ui, sans-serif;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #151a19; --surface: #1d2422; --ink: #e6ebe8; --muted: #9eaaa5; --line: #2f3936;
    --accent: #6fc3cb; --accent-soft: #1d3436; --open: #f0b860; --open-soft: #33291a; color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #151a19; --surface: #1d2422; --ink: #e6ebe8; --muted: #9eaaa5; --line: #2f3936;
  --accent: #6fc3cb; --accent-soft: #1d3436; --open: #f0b860; --open-soft: #33291a; color-scheme: dark;
}}
body {{ background: var(--bg); color: var(--ink); font-family: var(--body); font-size: 17px; line-height: 1.55; margin: 0; }}
.wrap {{ max-width: 68rem; margin: 0 auto; padding-inline: 16px; padding-block: 2rem 4rem; display: grid; gap: 2.25rem; }}
header {{ display: grid; gap: .6rem; }}
.stop {{ font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); font-weight: 700; }}
h1 {{ font-family: var(--display); font-size: clamp(1.8rem, 5vw, 2.4rem); line-height: 1.1; margin: 0; text-wrap: balance; }}
h2 {{ font-family: var(--display); font-size: 1.35rem; margin: 0; text-wrap: balance; }}
h3 {{ font-size: 1.1rem; margin: 0 0 .4rem; }}
p {{ margin: 0; }}
.lede {{ color: var(--muted); }}
section {{ display: grid; gap: .9rem; min-width: 0; }}
.ask {{ border-left: 3px solid var(--accent); background: var(--accent-soft); padding: .55rem .85rem; font-weight: 700; }}
.ask.open {{ border-color: var(--open); background: var(--open-soft); }}
ul {{ margin: 0; padding-left: 1.2rem; display: grid; gap: .35rem; }}
.reviews {{ list-style: none; padding: 0; }}
.verdict {{ font-weight: 700; color: var(--accent); }}
ol.scenes {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 0; }}
.scene {{ display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: 1.25rem; padding: 1.25rem 0; border-top: 1px solid var(--line); align-items: start; }}
.pics {{ display: grid; gap: .6rem; min-width: 0; }}
.still {{ all: unset; cursor: zoom-in; display: block; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: var(--surface); }}
.still:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 2px; }}
.still img {{ display: block; width: 100%; height: auto; }}
.scene.big {{ grid-template-columns: 1fr; }}
.scene.big .still {{ cursor: zoom-out; }}
.n {{ font-family: var(--display); color: var(--accent); margin-right: .35rem; }}
.said {{ padding-left: 1.1rem; }}
.said li {{ font-size: 1.05rem; }}
.note {{ color: var(--muted); font-size: .92rem; margin-top: .6rem; }}
dl {{ margin: 0; display: grid; gap: .7rem; }}
dt {{ font-weight: 700; }}
dd {{ margin: 0; }}
.guess {{ color: var(--open); font-weight: 700; }}
footer {{ border-top: 1px solid var(--line); padding-top: 1.25rem; display: grid; gap: .6rem; }}
@media (max-width: 760px) {{ .scene {{ grid-template-columns: 1fr; }} .scene.big .still {{ overflow-x: auto; }} .scene.big .still img {{ width: 220%; max-width: none; }} }}
</style>

<div class="wrap">
<section>
  <p class="ask">Who checked this before you, and what did they find?</p>
  <h2>Who reviewed it</h2>
  <p>Independent reviewers, none of which wrote the script or the pictures:</p>
  <ul class="reviews">{review_items}</ul>
</section>

<header>
  <div class="stop">Stop 2 of 3 &middot; Script and pictures</div>
  <h1>{e(page_text["heading"])}</h1>
  <p class="lede">{e(page_text["lede"])}</p>
  <p><b>Changed since you last looked:</b> {e(page_text["changed"])}</p>
</header>

<section>
  <p class="ask">{e(page_text["ask"])}</p>
  <h2>The script, scene by scene</h2>
  <p>{e(page_text["intro"])}</p>
  <ol class="scenes">{"".join(rows)}</ol>
</section>
{guess_section}
<footer>
  <h2>What a reply can say</h2>
  <ul>{replies}</ul>
</footer>
</div>
<script>
document.querySelectorAll(".still").forEach(function (b) {{
  b.addEventListener("click", function () {{
    var row = b.closest(".scene");
    var big = row.classList.toggle("big");
    row.querySelectorAll(".still").forEach(function (s) {{ s.setAttribute("aria-pressed", big ? "true" : "false"); }});
  }});
}});
</script>
</html>
"""
(HERE / "stop.html").write_text(page, encoding="utf-8", newline="")
print(f"wrote stop.html: {len(spec['scenes'])} scenes, {words} words")
