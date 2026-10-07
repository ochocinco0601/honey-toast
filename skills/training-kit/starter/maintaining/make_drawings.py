"""The kit's drawings: the tool's own parts, each with its source, and each drawing composed of them.

Run from the kit's folder: python maintaining/make_drawings.py. It writes every drawing into its
training's images folder; then build. The rules are in maintaining/README.md, "Pictures". This file
is the kit's own: a new version of the training-kit skill replaces drawings.py, never this file.

The example below is a stand-in. Replace it with the tool's parts, citing for each the source and
version it was checked against, and the drawings the pages use.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drawings import *  # noqa: E402,F401,F403

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- The tool's parts. Each cites where it was checked: [TO BE WRITTEN: source, version, date] ---


def dialog(x, y, w, h):
    """A stand-in dialog: a title, two lines of message, and two buttons at the foot."""
    return (frame(x, y, w, h) + bar(x + 20, y + 22, 200, 10, strong=True) + bar(x + 20, y + 48, w - 60) +
            bar(x + 20, y + 63, w - 120) + button(x + w - 190, y + h - 46, 80, 30, "Yes") +
            button(x + w - 100, y + h - 46, 80, 30, "Cancel", primary=False))


# --- The drawings ---

example = (dialog(20, 20, 420, 160) + outline(244, 128, 92, 40) + leader([(336, 148), (470, 148)]) +
           label(476, 153, "The button to select"))

DRAWINGS = {
    "getting-started/images/example-dialog.svg": (680, 200, "A dialog with the button to select", example),
}

if __name__ == "__main__":
    write(KIT, DRAWINGS)
