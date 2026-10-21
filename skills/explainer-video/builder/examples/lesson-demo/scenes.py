"""A lesson video's beats drawn from the training kit's parts: one part's fragment per beat.

The window is the kit's `window` picture (getting-started/images/vs-code-window.svg), drawn by the
same call, so the claims checked for that picture carry over. Each picture is put on the stage by
one transform (kitparts.Picture); the parts inside it are not redrawn.
"""
import kitparts
from stage import txt, line, ACCENT, MUTED

kit = kitparts.load("packages/copilot-training-kit")
d, make = kit.d, kit.make

WINDOW = kitparts.Picture(700, 440)          # the size of vs-code-window.svg
CHAT = kitparts.Picture(460, 160)

BEATS = {
    "open": [
        {"line": 0, "anim": "up", "svg":
            txt(480, 250, "Make your first request", size=40, weight=700, anchor="middle") +
            line(330, 284, 630, 284, stroke=ACCENT, sw=3) +
            txt(480, 326, "Getting started", size=24, fill=MUTED, anchor="middle")},
    ],
    "open-chat": [
        {"line": 0, "anim": "fade", "svg": WINDOW.place(make.window)},
        {"line": 1, "anim": "fade", "svg": WINDOW.place(d.outline(458, 40, 234, 372))},
    ],
    "request": [
        {"line": 0, "anim": "fade", "svg": CHAT.place(make.chat_box(17, 40, 426, typed="Create a folder called copilot-practice"))},
        {"line": 0, "plus": 1.2, "anim": "fade", "svg": CHAT.place(d.outline(12, 35, 436, 76))},
    ],
}
