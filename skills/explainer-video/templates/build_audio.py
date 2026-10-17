"""Speak one clip per scene, a pause before every line, and measure where each line starts.

Silence: `head` before a scene's first line, `tail` after its last, `gap` between lines unless a
line sets its own `pause` (the long tier, where the picture turns). timing.json carries each
scene's length, every line's measured start, and the silence before it; the page and scene.py
place their beats from those numbers.

Needs: kokoro-onnx and soundfile in this Python; the two Kokoro model files in the folder named by
the KOKORO_MODELS environment variable (default: a `kokoro-models` folder in your home folder);
ffmpeg on PATH, or imageio-ffmpeg installed in this Python.

Run: python build_audio.py            (--count: count the words and stop; needs none of the above)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).parent
AUDIO = HERE / "audio"
WORK = AUDIO / ".work"
RATE = 24000

spec = json.loads((HERE / "narration.json").read_text(encoding="utf-8-sig"))
HEAD, GAP, TAIL = spec["head"], spec["gap"], spec["tail"]

# The word budget, for Kokoro af_heart at speed 1.0 with the default pauses. Change the voice or
# its speed and these move: remeasure on one built piece and change them here.
TARGET, CEILING = 255, 385
per_scene = [(s["id"], sum(len(l["say"].split()) for l in s["lines"])) for s in spec["scenes"]]
words = sum(n for _, n in per_scene)
print(f"{words} spoken words (about 2:00 at {TARGET}, 3:00 at {CEILING}): " + ", ".join(f"{i} {n}" for i, n in per_scene))
if words > CEILING:
    raise SystemExit(f"over the {CEILING}-word ceiling: cut the scene that serves least of the brief")
if words > TARGET:
    print(f"  over the {TARGET}-word target: cut the scene that serves least of the brief, not the pauses")
if "--count" in sys.argv:
    raise SystemExit(0)


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
MODELS = Path(os.environ.get("KOKORO_MODELS", Path.home() / "kokoro-models"))
ONNX, VOICES = MODELS / "kokoro-v1.0.onnx", MODELS / "voices-v1.0.bin"
if not (ONNX.exists() and VOICES.exists()):
    raise SystemExit(f"Kokoro model files not found in {MODELS}: set KOKORO_MODELS to the folder "
                     "holding kokoro-v1.0.onnx and voices-v1.0.bin")

from kokoro_onnx import Kokoro
import soundfile

kokoro = Kokoro(str(ONNX), str(VOICES))
VOICE, SPEED = spec.get("voice", "af_heart"), spec.get("speed", 1.0)
WORK.mkdir(parents=True, exist_ok=True)


def seconds(wav):
    with wave.open(str(wav)) as w:
        return w.getnframes() / w.getframerate()


timing = {}
for scene in spec["scenes"]:
    sid = scene["id"]
    parts, starts, pre, cursor = [], [], [], 0.0
    for n, entry in enumerate(scene["lines"]):
        raw, padded = WORK / f"{sid}-{n}.wav", WORK / f"{sid}-{n}-pad.wav"
        samples, rate = kokoro.create(entry["say"], voice=VOICE, speed=SPEED, lang="en-us")
        soundfile.write(str(raw), samples, rate, subtype="PCM_16")
        last = n == len(scene["lines"]) - 1
        assert not (last and "pause" in entry), f"{sid} line {n}: the last line cannot set `pause`"
        pause = TAIL if last else entry.get("pause", GAP)
        lead = f"adelay={int(HEAD * 1000)}," if n == 0 else ""
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(raw), "-af", f"{lead}apad=pad_dur={pause}",
                        "-ar", str(RATE), "-ac", "1", str(padded)], check=True)
        starts.append(round(cursor + (HEAD if n == 0 else 0), 3))
        pre.append(HEAD if n == 0 else scene["lines"][n - 1].get("pause", GAP))
        cursor += seconds(padded)
        parts.append(padded)
    listing = WORK / f"{sid}.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    out = AUDIO / f"{sid}.wav"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(out)], check=True)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(out), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ac", "1", "-ar", str(RATE), "-b:a", "48k", str(AUDIO / f"{sid}.mp3")], check=True)
    timing[sid] = {"dur": round(seconds(out), 3), "starts": starts, "pre": pre}
    print(f"{sid:>16}  {timing[sid]['dur']:6.2f}s  starts {starts}")

for f in WORK.iterdir():
    f.unlink()
WORK.rmdir()
(HERE / "timing.json").write_text(json.dumps(timing, indent=1) + "\n")
total = sum(v["dur"] for v in timing.values())
print(f"{'total':>16}  {total:6.2f}s ({int(total // 60)}:{total % 60:04.1f})")

# The page reads the same numbers, so the build writes them in rather than leaving a hand-copy to
# drift, and refuses if a caption in the page has drifted from narration.json.
pages = sorted(HERE.glob("*-explainer.html"))
if not pages:
    raise SystemExit(0)  # a video-file-only piece has no page to update
page = pages[0]
html = page.read_text(encoding="utf-8")
rows = ",\n".join(
    f"    {json.dumps(sid)}: {{ dur: {v['dur']}, starts: [{', '.join(str(x) for x in v['starts'])}],"
    f" pre: [{', '.join(str(x) for x in v['pre'])}] }}" for sid, v in timing.items())
block = f"  var TIMING = {{  /* written by build_audio.py from narration.json; do not hand-edit */\n{rows}\n  }};"
new, swapped = re.subn(r"  var TIMING = \{.*?\n  \};", lambda _: block, html, count=1, flags=re.S)
if not swapped:
    raise SystemExit(f"could not find the TIMING block in {page.name}")
want = [line["caption"] for scene in spec["scenes"] for line in scene["lines"]]
got = [m.group(1).replace('\\"', '"') for m in re.finditer(r'caption: "((?:[^"\\]|\\.)*)"', new)]
if got != want:
    for i, (a, b) in enumerate(zip(got + [None] * len(want), want + [None] * len(got))):
        if a != b:
            raise SystemExit(f"page caption {i} differs\n  page: {a!r}\n  json: {b!r}")
page.write_text(new, encoding="utf-8", newline="")
print(f"  wrote TIMING into {page.name}; {len(want)} captions match narration.json")
