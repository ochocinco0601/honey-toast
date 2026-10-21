"""Write a video's page, <name>-explainer.html, from its data, and check its captions.

The page's design is page-template.html (the explainer skill's build-page.md, step 8). The
scenes, beats, captions, TIMING block, titles, reading column and the lesson link come from the
video's narration.json, scenes.py and timing.json (explainer.py says what each holds).

Run: python build_page.py <video folder>        (build_audio.py runs this itself after speaking)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explainer  # noqa: E402


def main(folder):
    video = explainer.Video(folder)
    out = explainer.render(video)
    n = explainer.check_captions(video, out)
    print(f"wrote {out.name}: {len(video.ids)} scenes; {n} captions match narration.json")
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
