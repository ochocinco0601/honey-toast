"""The overview's beats: what is drawn, and when, for each scene of narration.json.

Shapes come from stage.py.
"""
from stage import (ACCENT, AMBER, INK, LINE, MUTED, PAPER, SOFT, arrow_head, box, chip, dim, line,
                   rect, txt)

# The board the trainings are placed on, shared by scenes 3 to 7.
PANELS = (box(40, 60, 420, 420, fill=PAPER, stroke=LINE, sw=1.6, r=10) +
          box(500, 60, 420, 420, fill=PAPER, stroke=LINE, sw=1.6, r=10) +
          txt(66, 110, "Instructions", size=30, weight=700) +
          txt(66, 136, "what you tell it", size=17, fill=MUTED) +
          txt(526, 110, "Tools", size=30, weight=700) +
          txt(526, 136, "what it can do", size=17, fill=MUTED))
REQUEST = chip(66, 168, 300, "your request", outline=True, color=MUTED)
TOOLS = (txt(556, 198, "read a file", size=21) +
         txt(556, 262, "change a file", size=21) +
         txt(556, 326, "run a command", size=21))
GS = chip(66, 232, 300, "Getting started")
SKILLS = chip(66, 296, 300, "Skills")
AGENTS = chip(66, 360, 300, "Custom agents")
LIMITS = (line(548, 255, 698, 255, stroke=AMBER, sw=4) +
          line(548, 319, 718, 319, stroke=AMBER, sw=4) +
          line(534, 232, 534, 342, stroke=AMBER, sw=4) +
          '<path d="M368,383 L480,383 L480,287 L534,287" fill="none" stroke="' + AMBER +
          '" stroke-width="2.4" stroke-dasharray="6 5"/>')

# at-work: a VS Code window, a request, the file it makes, a permission request, an undo.
NEQ = (line(462, 266, 498, 266, stroke=INK, sw=3) + line(462, 288, 498, 288, stroke=INK, sw=3) +
       line(472, 302, 488, 252, stroke=INK, sw=3))
WINDOW = (box(40, 40, 880, 470, fill=PAPER, stroke=LINE, sw=1.6, r=10) +
          '<rect x="41" y="41" width="878" height="28" fill="var(--bg)"/>' +
          txt(480, 60, "Visual Studio Code", size=13, fill=MUTED, anchor="middle") +
          line(240, 69, 240, 509, stroke=LINE, sw=1.6) + line(620, 69, 620, 509, stroke=LINE, sw=1.6) +
          txt(56, 94, "EXPLORER", size=11, fill=MUTED, weight=700, ls="0.06em") +
          txt(56, 122, "my-folder", size=15, weight=700) +
          txt(76, 148, "plan.docx", size=15, fill=MUTED) +
          txt(76, 172, "notes.txt", size=15, fill=MUTED) +
          txt(636, 94, "CHAT", size=11, fill=MUTED, weight=700, ls="0.06em") +
          box(636, 472, 80, 26, fill=PAPER, stroke=MUTED, sw=1.2, r=5) +
          txt(676, 490, "Agent", size=13, anchor="middle"))
REQ = (box(636, 106, 268, 76, fill=SOFT, stroke=SOFT, sw=1, r=8) +
       txt(650, 132, "Write a one-page summary", size=14) +
       txt(650, 152, "of the documents in this", size=14) +
       txt(650, 172, "folder.", size=14))
NEWFILE = (rect(52, 182, 176, 24, SOFT, rx=4) +
           txt(76, 199, "summary.md", size=15, fill=ACCENT, weight=700) +
           txt(262, 94, "summary.md", size=14) + line(262, 101, 344, 101, stroke=ACCENT, sw=2.4) +
           rect(262, 122, 160, 12, INK, opacity=".75") +
           rect(262, 152, 300, 8, LINE) + rect(262, 174, 270, 8, LINE) + rect(262, 196, 320, 8, LINE) +
           rect(262, 218, 220, 8, LINE) + rect(262, 240, 290, 8, LINE))
PERMIT = (box(636, 196, 268, 84, fill=PAPER, stroke=AMBER, sw=2, r=8) +
          txt(652, 224, "Run a command?", size=15, weight=700) +
          rect(652, 240, 78, 28, ACCENT, rx=5) +
          txt(691, 259, "Allow", size=13, weight=700, fill=PAPER, anchor="middle") +
          box(740, 240, 64, 28, fill=PAPER, stroke=MUTED, sw=1.2, r=5) +
          txt(772, 259, "Skip", size=13, anchor="middle"))
UNDO = ('<path d="M666,210 a8,8 0 1 0 8,-8" fill="none" stroke="' + ACCENT + '" stroke-width="2.6" '
        'stroke-linejoin="round" stroke-linecap="round"/>' +
        '<path d="M670,198 l6,4 l-6,4 z" fill="' + ACCENT + '" stroke="' + ACCENT + '" stroke-width="1" '
        'stroke-linejoin="round" stroke-linecap="round"/>' +
        txt(686, 216, "Restore Checkpoint", size=14, fill=ACCENT, weight=700))

BEATS = {
    "open": [
        {"line": 0, "anim": "up", "svg":
            txt(480, 250, "Learn GitHub Copilot in VS Code", size=44, weight=700, anchor="middle") +
            line(330, 286, 630, 286, stroke=ACCENT, sw=3) +
            txt(480, 330, "An overview", size=26, fill=ACCENT, anchor="middle")},
    ],
    "at-work": [
        {"line": 0, "outLine": 1, "anim": "fade", "svg":
            box(110, 200, 330, 150, fill=PAPER, stroke=LINE, sw=1.6, r=10) +
            txt(275, 282, "Copilot in an office suite", size=21, fill=MUTED, anchor="middle") + NEQ +
            box(520, 200, 330, 150, fill=PAPER, stroke=ACCENT, sw=2.4, r=10) +
            txt(685, 282, "GitHub Copilot in VS Code", size=21, fill=ACCENT, weight=700, anchor="middle")},
        {"line": 1, "anim": "fade", "svg": WINDOW},
        {"line": 2, "anim": "up", "svg": REQ},
        {"line": 2, "plus": 1.6, "outLine": 4, "outPlus": 0.8, "anim": "fade", "svg": NEWFILE},
        {"line": 3, "outLine": 3, "outPlus": 2.5, "anim": "up", "svg": PERMIT},
        {"line": 3, "plus": 1.8, "outLine": 3, "outPlus": 2.5, "anim": "fade",
         "svg": box(647, 235, 88, 38, stroke=ACCENT, sw=3, r=7)},
        {"line": 4, "anim": "fade", "svg": UNDO},
        {"line": 4, "plus": 0.4, "anim": "fade", "svg": box(652, 190, 200, 36, stroke=ACCENT, sw=2.4, r=6)},
    ],
    "frame": [
        {"line": 0, "anim": "fade", "svg": PANELS},
        {"line": 1, "anim": "right", "svg": REQUEST},
        {"line": 2, "anim": "left", "svg": TOOLS},
    ],
    # 4 to 7: the board stays; each scene places one training on it.
    "getting-started": [
        {"line": 0, "held": True, "anim": "fade", "svg": PANELS + REQUEST + TOOLS},
        {"line": 0, "anim": "right", "svg": GS},
    ],
    "skills": [
        {"line": 0, "held": True, "anim": "fade", "svg": PANELS + REQUEST + TOOLS + GS},
        {"line": 0, "anim": "right", "svg": SKILLS},
    ],
    "agents": [
        {"line": 0, "held": True, "anim": "fade", "svg": PANELS + REQUEST + TOOLS + GS + SKILLS},
        {"line": 0, "anim": "right", "svg": AGENTS},
        {"line": 0, "plus": 5.9, "anim": "fade", "svg": LIMITS},
    ],
    "connecting": [
        {"line": 0, "held": True, "anim": "fade",
         "svg": PANELS + REQUEST + TOOLS + GS + SKILLS + AGENTS + dim(LIMITS)},
        {"line": 0, "anim": "left", "svg":
            box(526, 352, 362, 74, fill=SOFT, stroke=ACCENT, sw=2.2, r=8) +
            txt(544, 383, "Connecting your tools", size=19, fill=ACCENT, weight=700) +
            txt(544, 410, "+ tools from GitHub", size=16, fill=ACCENT) +
            line(956, 389, 906, 389, stroke=ACCENT, sw=3) + arrow_head(892, 389, "left", ACCENT)},
    ],
    "start": [
        {"line": 0, "anim": "right", "svg":
            txt(110, 214, "Start here", size=19, fill=AMBER, weight=700) +
            chip(110, 230, 310, "Getting started", h=58, size=24)},
        {"line": 1, "anim": "left", "svg":
            chip(570, 168, 320, "Skills", outline=True, color=MUTED) +
            chip(570, 246, 320, "Custom agents", outline=True, color=MUTED) +
            chip(570, 324, 320, "Connecting your tools", outline=True, color=MUTED) +
            line(424, 259, 552, 191, stroke=MUTED, sw=2.4) + arrow_head(566, 191, "right", MUTED) +
            line(424, 259, 552, 269, stroke=MUTED, sw=2.4) + arrow_head(566, 269, "right", MUTED) +
            line(424, 259, 552, 347, stroke=MUTED, sw=2.4) + arrow_head(566, 347, "right", MUTED)},
    ],
}
