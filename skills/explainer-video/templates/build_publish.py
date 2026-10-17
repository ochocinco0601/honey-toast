"""Generate the shareable package of this explainer: the page version, the video file with a
captions track, a separate captions file, the job aid if there is one, and a README. Nothing in it
is edited by hand: rebuild it.

Needs: ffmpeg on PATH, or imageio-ffmpeg installed in this Python. No Manim, no speech engine.
Run (after build_audio.py, and build.py for a video file): python build_publish.py [out-dir, default ./package]
Reads `title`, `name` and `about` from narration.json for the file names and the README.
The out-dir is emptied only if this script made it (it holds the marker file it writes); any other
existing path is refused and left as it is.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "package"
if OUT.resolve() in (HERE.resolve(), *HERE.resolve().parents):
    sys.exit(f"refusing to write the package over {OUT}: it is emptied first, and that would delete the piece")
MARKER = ".made-by-build_publish"
if OUT.exists() and not (OUT / MARKER).is_file():
    sys.exit(f"refusing to write the package to {OUT}: it already exists and was not made by this script, "
             "so it is left untouched. Name a folder that does not exist yet, or delete this one yourself.")


def find_ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit("ffmpeg not found: put it on PATH, or pip install imageio-ffmpeg in this Python")


FFMPEG = find_ffmpeg()

if OUT.exists():  # only reached when it holds the marker: this script made it
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
(OUT / MARKER).write_text("This folder is made by build_publish.py, which empties it on each run.\n", encoding="utf-8")

narration = json.loads((HERE / "narration.json").read_text(encoding="utf-8-sig"))
timing = json.loads((HERE / "timing.json").read_text(encoding="utf-8"))
TITLE, NAME, ABOUT = narration["title"], narration["name"], narration["about"]

pages = sorted(HERE.glob("*-explainer.html"))
if pages:  # a video-file-only piece has no page version
    (OUT / "audio").mkdir()
    page = pages[0].read_text(encoding="utf-8")
    page = re.sub(r"/\*.*?\*/", "", page, flags=re.S)
    page = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    page = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", page)
    page = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\s*', "", page)
    page = re.sub(r"[ \t]+\n", "\n", page)
    page = re.sub(r"\n{3,}", "\n\n", page)
    assert "googleapis" not in page and "gstatic" not in page, "a font link survived"
    if not page.lstrip().lower().startswith("<!doctype html>"):
        page = '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n' + page.lstrip() + "\n</html>\n"
    assert 'lang="' in page and "charset" in page, "the page declares no lang or no charset"
    (OUT / "index.html").write_text(page, encoding="utf-8", newline="\n")
    for sc in narration["scenes"]:
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(HERE / "audio" / f"{sc['id']}.mp3"),
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-c", "copy",
                        str(OUT / "audio" / f"{sc['id']}.mp3")], check=True)


def stamp(s):
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{sec:06.3f}"


cues, offset = [], 0.0
for sc in narration["scenes"]:
    tm = timing[sc["id"]]
    for i, line in enumerate(sc["lines"]):
        start = offset + tm["starts"][i]
        end = offset + (tm["starts"][i + 1] - tm["pre"][i + 1] if i + 1 < len(tm["starts"]) else tm["dur"])
        cues.append(f"{stamp(start)} --> {stamp(end)}\n{line['caption']}")
    offset += tm["dur"]
has_aid = (HERE / "job-aid.md").exists()
if has_aid:
    shutil.copy(HERE / "job-aid.md", OUT / "job-aid.md")

video = HERE / f"{NAME}.mp4"
if video.exists():  # a page-only piece has no video file
    vtt = OUT / f"{NAME}.vtt"
    vtt.write_text("WEBVTT\n\n" + "\n\n".join(cues) + "\n", encoding="utf-8", newline="\n")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(video),
                    "-i", str(vtt), "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text",
                    "-map_metadata", "-1", "-map_metadata:s", "-1", "-fflags", "+bitexact",
                    "-metadata:s:s:0", "language=eng", "-movflags", "+faststart",
                    str(OUT / video.name)], check=True)

total = round(offset)
both = bool(pages) and video.exists()
parts = [f"# {TITLE}\n\nA narrated explainer, about {total // 60}:{total % 60:02d} long. {ABOUT}"
         + (" It comes in two versions with the same script and voice." if both else "") + "\n"]
if pages:
    parts.append("## The page version\n\nOpen `index.html` in a browser, with the `audio` folder kept beside it. It has\n"
                 "captions you can turn on and off, the transcript beside the player (click a line to play from it),\n"
                 "and a step for each scene. It also works with the sound off: it stops after each scene so you can\n"
                 "read the caption.\n")
if video.exists():
    parts.append(f"## The video file\n\n`{video.name}` plays anywhere a video does and can be shared as a single file. Its\n"
                 f"captions are built in as a track the player can turn on, and the same captions are in `{NAME}.vtt`\n"
                 "for a player that takes a separate captions file.\n")
if has_aid:
    parts.append("## The one-page sheet\n\n`job-aid.md` holds the steps in the order you work, readable without having watched.\n")
(OUT / "README.md").write_text("\n".join(parts), encoding="utf-8", newline="\n")
print("wrote", OUT, sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file() and p.name != MARKER))
