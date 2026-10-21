"""Write a video's package, the folder that is delivered (to a training kit, or on its own):

  index.html        the page, cleaned: no comments, no web fonts or CDN, no host-only meta tags,
                    no paths from the machine it was built on, no dates, ASCII with every
                    non-ASCII character as an HTML entity
  audio/<id>.mp3    each scene's clip, metadata stripped
  video.json        the manifest: title, seconds, scenes (id, title, step) and files (each one's
                    sha256); for a kit's video also lesson, lesson_sha256 (the lesson's text as the
                    video was made from it, line endings as LF, so the kit can tell when the lesson
                    has changed since) and back_href

It encodes first, then asserts each of those properties, and refuses to write a package that fails
one. Nothing in the package is edited by hand.

Run (after build_audio.py): python build_publish.py <video folder> [out dir, default <folder>/package]
"""
import hashlib
import html.entities
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explainer  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
video = explainer.Video(args[0] if args else ".")
HERE = video.dir
OUT = Path(args[1]).resolve() if len(args) > 1 else HERE / "package"
if OUT in (HERE, *HERE.parents):
    sys.exit(f"refusing to write the package over {OUT}: it is emptied first, and that would delete the piece")
page = video.page
if not page.get("title"):
    sys.exit("narration.json's page block has no `title`; the manifest needs it")
lesson_file = None
if page.get("lesson"):
    for field in ("back_href", "kit"):
        if not page.get(field):
            sys.exit(f"the page block names a `lesson` but no `{field}`: a kit's video needs both")
    lesson_file = video.kit / page["lesson"]
    if not lesson_file.is_file():
        sys.exit(f"the lesson {page['lesson']} is not in the kit at {video.kit}")
for sc in video.scenes:
    step = sc.get("step")
    if step is not None and not (isinstance(step, int) and step > 0):
        sys.exit(f"scene {sc['id']}: step is {step!r}; a lesson step's number, or null")
    if not sc.get("title"):
        sys.exit(f"scene {sc['id']} has no title; the manifest lists each scene's title")

FFMPEG = shutil.which("ffmpeg")
if not FFMPEG:
    try:
        import imageio_ffmpeg
        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg not found: put it on PATH, or pip install imageio-ffmpeg in this Python")

# --- the page, cleaned ----------------------------------------------------------------------------
source = video.page_path()
if not source.exists():
    sys.exit(f"no {source.name}: run build_audio.py (or build_page.py) first")
explainer.check_captions(video, source)
text = source.read_text(encoding="utf-8")
text = re.sub(r"<!--.*?-->\s*", "", text, flags=re.S)
text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
text = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", text)
text = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\s*', "", text)
text = re.sub(r'<meta name="claude:[^>]*>\s*', "", text)
text = re.sub(r"[ \t]+\n", "\n", text)
text = re.sub(r"\n{3,}", "\n\n", text)
# Encode first: any non-ASCII character left is written as an entity (named where HTML has a name).
text = "".join(c if ord(c) < 128 else
               (f"&{html.entities.codepoint2name[ord(c)]};" if ord(c) in html.entities.codepoint2name
                else f"&#{ord(c)};") for c in text)
if not text.endswith("\n"):
    text += "\n"
if "</html>" not in text:
    text += "</html>\n"

checks = [
    ("is not ASCII", lambda t: any(ord(c) > 127 for c in t)),
    ("still has a comment", lambda t: "<!--" in t or "/*" in t),
    ("loads a web font or a CDN", lambda t: re.search(r"googleapis|gstatic|@font-face|@import|<link\b|"
                                                      r"<script[^>]+src=|cdnjs|jsdelivr|unpkg", t)),
    ("has a host-only meta tag", lambda t: "claude:" in t),
    ("names a path from the build machine", lambda t: (re.search(r"(?<![A-Za-z])[A-Z]:[\\/]|/Users/|\\Users\\|/home/|"
                                                                  r"\.claude/|maintaining/", t)
                                                        or ("/" in video.rel(HERE) and video.rel(HERE) in t))),
    ("carries a date", lambda t: re.search(r"\b20\d\d-\d\d-\d\d\b|\b20\d\d/\d\d/\d\d\b", t)),
    ("does not start with the doctype", lambda t: not t.startswith("<!doctype html>")),
]
failed = [what for what, bad in checks if bad(text)]
if failed:
    sys.exit("refusing to write the package: index.html " + "; ".join(failed))

# --- write --------------------------------------------------------------------------------------
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "audio").mkdir(parents=True)
(OUT / "index.html").write_bytes(text.encode("ascii"))
explainer.check_captions(video, OUT / "index.html")   # the entities decode to the narration's words
for sid in video.ids:
    src = HERE / "audio" / f"{sid}.mp3"
    if not src.exists():
        sys.exit(f"no audio/{sid}.mp3: run build_audio.py")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(src), "-map_metadata", "-1",
                    "-fflags", "+bitexact", "-c", "copy", str(OUT / "audio" / f"{sid}.mp3")], check=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


timing = video.timing()
manifest = {"format": 1}
if lesson_file:
    manifest["lesson"] = page["lesson"]
    manifest["lesson_sha256"] = hashlib.sha256(lesson_file.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
manifest["title"] = page["title"]
manifest["seconds"] = round(sum(timing[i]["dur"] for i in video.ids))
if lesson_file:
    manifest["back_href"] = page["back_href"]
manifest["scenes"] = [{"id": sc["id"], "title": sc["title"], "step": sc.get("step")} for sc in video.scenes]
manifest["files"] = {f.relative_to(OUT).as_posix(): sha(f) for f in sorted(OUT.rglob("*")) if f.is_file()}
(OUT / "video.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=True) + "\n", encoding="ascii", newline="\n")
size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
print(f"wrote {OUT}: index.html, {len(video.ids)} clips, video.json; {manifest['seconds']}s, {size / 1e6:.2f} MB")
