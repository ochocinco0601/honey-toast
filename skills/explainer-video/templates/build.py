"""Render the timed scene, join the scene clips from build_audio.py, and mux them into one MP4.

Needs: manim and imageio-ffmpeg in this Python (Manim installs imageio-ffmpeg itself).
Run (after build_audio.py): python build.py [-qh | -ql] [--mux to skip the render and only rejoin the audio]
The video file is named from `name` in narration.json. Speech is normalised to -16 LUFS, the usual
level for spoken video.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
spec = json.loads((HERE / "narration.json").read_text(encoding="utf-8-sig"))
order = [s["id"] for s in spec["scenes"]]


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

args = sys.argv[1:]
if "--mux" not in args:
    quality = next((a for a in args if a.startswith("-q")), "-qh")
    subprocess.run([sys.executable, "-m", "manim", quality, "--disable_caching", str(HERE / "scene.py"), "Explainer",
                    "-o", "silent"], check=True, cwd=HERE)
silent = max((HERE / "media" / "videos" / "scene").rglob("silent.mp4"), key=lambda p: p.stat().st_mtime)

listing = HERE / "audio" / "list.txt"
listing.write_text("".join(f"file '{(HERE / 'audio' / f'{sid}.wav').as_posix()}'\n" for sid in order))
track = HERE / "audio" / "track.wav"
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy",
                str(track)], check=True)

out = HERE / f"{spec['name']}.mp4"
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(silent), "-i", str(track), "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart", str(out)], check=True)
print("wrote", out)
