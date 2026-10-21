"""Speak one clip per scene, a pause before every line, measure where each line starts, then write
the page from the data.

Silence: `head` before a scene's first line, `tail` after its last, `gap` between lines unless a
line sets its own `pause` (the long tier, where the picture turns). Each scene's clip is normalised
to -16 LUFS. timing.json carries each scene's length, every line's measured start and the silence
before it; the page's TIMING block is written from it, and the build fails if a caption in the
page differs from narration.json.

The word budget (SKILL.md, "The budget in words"):
  - kind "explainer" (the page block's default): over 255 words it warns, over 385 it refuses;
  - kind "lesson": no ceiling. A video past about six minutes is split into chapters (a `chapter`
    on its scenes); it warns for each chapter, or an unchaptered video, over about six minutes,
    by words before speaking and by measured length after.

A scene whose words, pauses and voice are unchanged since its clip was made is not spoken again
(audio/.made.json), so a fix to one scene of a long video re-speaks one scene.

Needs: kokoro-onnx and soundfile in this Python; the two Kokoro model files in the folder named by
the KOKORO_MODELS environment variable (default: a `kokoro-models` folder in your home folder);
ffmpeg on PATH, or imageio-ffmpeg installed in this Python.

Run: python build_audio.py <video folder>     (--count: count the words and stop, needing none of
     the above; --all: speak every scene again)
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explainer  # noqa: E402
import build_page  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
video = explainer.Video(args[0] if args else ".")
spec = video.spec
HERE = video.dir
AUDIO = HERE / "audio"
RATE = 24000
MODELS = Path(os.environ.get("KOKORO_MODELS", Path.home() / "kokoro-models"))
HEAD, GAP, TAIL = spec["head"], spec["gap"], spec["tail"]
VOICE, SPEED = spec.get("voice", "af_heart"), spec.get("speed", 1.0)

TARGET, CEILING = 255, 385          # two and three minutes at af_heart, speed 1.0, these pauses
CHAPTER_WORDS, CHAPTER_SECONDS = 765, 360   # about six minutes (Guo, Kim and Rubin, 2014)


def words(ids):
    return sum(len(l["say"].split()) for s in video.scenes if s["id"] in ids for l in s["lines"])


per_scene = [(s["id"], words([s["id"]])) for s in video.scenes]
total_words = sum(n for _, n in per_scene)
print(f"{total_words} spoken words: " + ", ".join(f"{i} {n}" for i, n in per_scene))
if video.kind == "lesson":
    for name, ids in explainer.chapters(video):
        n = words(ids)
        label = f"chapter {name!r}" if name else "the video (no chapters)"
        if n > CHAPTER_WORDS:
            print(f"  WARNING: {label} has {n} words, about {n / CHAPTER_WORDS * 6:.1f} minutes: "
                  f"split it into chapters of about six minutes")
else:
    print(f"  (about 2:00 at {TARGET}, 3:00 at {CEILING})")
    if total_words > CEILING:
        raise SystemExit(f"over the {CEILING}-word ceiling: cut the scene that serves least of the brief "
                         f"(a lesson video sets \"kind\": \"lesson\" in narration.json's page block)")
    if total_words > TARGET:
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


def seconds(wav):
    with wave.open(str(wav)) as w:
        return w.getnframes() / w.getframerate()


def key(scene):
    """What a scene's clip is made from; unchanged, the clip is reused."""
    made = {"voice": VOICE, "speed": SPEED, "head": HEAD, "gap": GAP, "tail": TAIL,
            "lines": [[l["say"], l.get("pause")] for l in scene["lines"]]}
    return hashlib.sha256(json.dumps(made, sort_keys=True).encode()).hexdigest()


AUDIO.mkdir(exist_ok=True)
WORK = AUDIO / ".work"
WORK.mkdir(exist_ok=True)
made_file = AUDIO / ".made.json"
made = json.loads(made_file.read_text()) if made_file.exists() and "--all" not in sys.argv else {}
old = json.loads((HERE / "timing.json").read_text(encoding="utf-8")) if (HERE / "timing.json").exists() else {}
kokoro = None
timing = {}
for scene in video.scenes:
    sid, k = scene["id"], key(scene)
    if made.get(sid) == k and sid in old and (AUDIO / f"{sid}.mp3").exists():
        timing[sid] = old[sid]
        print(f"{sid:>20}  {timing[sid]['dur']:6.2f}s  unchanged, not spoken again")
        continue
    if kokoro is None:
        if not ((MODELS / "kokoro-v1.0.onnx").exists() and (MODELS / "voices-v1.0.bin").exists()):
            raise SystemExit(f"Kokoro model files not found in {MODELS}: set KOKORO_MODELS to the folder "
                             "holding kokoro-v1.0.onnx and voices-v1.0.bin")
        from kokoro_onnx import Kokoro
        import soundfile
        kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
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
    made[sid] = k
    print(f"{sid:>20}  {timing[sid]['dur']:6.2f}s  starts {starts}")

shutil.rmtree(WORK, ignore_errors=True)
made_file.write_text(json.dumps({s: made[s] for s in video.ids if s in made}, indent=1) + "\n", newline="\n")
(HERE / "timing.json").write_text(json.dumps(timing, indent=1) + "\n", newline="\n")
total = sum(v["dur"] for v in timing.values())
print(f"{'total':>20}  {total:6.2f}s ({int(total // 60)}:{total % 60:04.1f})")
if video.kind == "lesson":
    for name, ids in explainer.chapters(video):
        secs = sum(timing[i]["dur"] for i in ids)
        label = f"chapter {name!r}" if name else "the video (no chapters)"
        print(f"  {label}: {int(secs // 60)}:{secs % 60:04.1f}")
        if secs > CHAPTER_SECONDS:
            print(f"  WARNING: {label} runs past six minutes: split it into chapters")

# The page reads the same numbers, so it is written from them rather than hand-copied, and the
# build fails if a caption in the page differs from narration.json.
if (HERE / "scenes.py").exists():
    build_page.main(HERE)
