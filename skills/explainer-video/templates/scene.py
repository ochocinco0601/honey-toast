"""The drawing for the video file, written with Manim (manim.community).

One function per scene builds its settled frame; one Scene class per scene shows that frame alone
(the stills, rendered with `python -m manim -s -qh scene.py S1Open`); the Explainer class plays
all of them in order, timed from timing.json. `beat(n, ...)` places an animation in the silence
before line n, as the page does; `plus=` places one inside a line. The render FAILS, and writes
timing-check.txt, if any beat is still animating when the voice reaches what it draws.

This example draws the same three scenes as example-explainer.html. Replace both together.
"""
import json
from pathlib import Path

from manim import *

BG = "#F5F3EE"
INK = "#1F1E1C"
MUTED = "#6B6862"
FAINT = "#D9D5CC"
PANEL = "#FFFFFF"
ACCENT = "#1F6F78"
ACCENT_SOFT = "#DCEDEE"
AMBER = "#B7791F"
GOOD = "#2E7D55"
BAD = "#B33A2E"
FONT = "Segoe UI"   # any installed sans-serif; Manim falls back silently if it is missing, so check the stills

config.background_color = BG


def T(s, size=28, color=INK, weight=NORMAL, **kw):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kw)


def box(w, h, fill=PANEL, stroke=FAINT, r=0.18, sw=2):
    return RoundedRectangle(width=w, height=h, corner_radius=r, fill_color=fill, fill_opacity=1,
                            stroke_color=stroke, stroke_width=sw)


def chip(label, w=4.6, filled=True, color=ACCENT):
    t = T(label, 28, color, weight=BOLD)
    b = box(max(w, t.width + 0.6), 0.72, fill=ACCENT_SOFT if filled else PANEL, stroke=color, r=0.14, sw=2.5)
    t.move_to(b).align_to(b, LEFT).shift(RIGHT * 0.3)
    return VGroup(b, t)


# Right and wrong are drawn as paths, never typed: no font carries a tick reliably.
def tick(size=0.32, color=GOOD):
    return VMobject(stroke_color=color, stroke_width=6).set_points_as_corners(
        [[-0.5 * size, 0, 0], [-0.1 * size, -0.4 * size, 0], [0.6 * size, 0.45 * size, 0]])


def cross(size=0.32, color=BAD):
    return VGroup(Line([-0.5 * size, 0.5 * size, 0], [0.5 * size, -0.5 * size, 0]),
                  Line([0.5 * size, 0.5 * size, 0], [-0.5 * size, -0.5 * size, 0])).set_stroke(color, 6)


def strike(mob, color=AMBER):
    return Line(mob.get_left() + LEFT * 0.15, mob.get_right() + RIGHT * 0.15,
                stroke_color=color, stroke_width=6)


# ---- scene 1: open --------------------------------------------------------

def opening():
    title = T("Your subject", 58, weight=BOLD)
    rule = Line(LEFT * 2.2, RIGHT * 2.2, stroke_color=ACCENT, stroke_width=4)
    sub = T("An overview", 38, ACCENT)
    return VGroup(title, rule, sub).arrange(DOWN, buff=0.45).move_to(UP * 0.2)


# ---- scene 2: compare, one frame for before and after ----------------------

def compare_parts():
    frame = box(7.4, 5.2).move_to(DOWN * 0.1)
    corner = frame.get_corner(UL) + RIGHT * 0.6 + DOWN * 0.8

    def bars(color):
        rows = VGroup(*[Rectangle(width=w, height=0.16, fill_color=color, fill_opacity=1, stroke_width=0)
                        for w in (5.0, 4.2, 5.5, 3.4)]).arrange(DOWN, buff=0.34, aligned_edge=LEFT)
        return rows.move_to(corner + DOWN * 1.4, aligned_edge=UL)

    before_t = T("Before", 40, BAD, weight=BOLD).move_to(corner, aligned_edge=LEFT)
    before = VGroup(before_t, cross().move_to(frame.get_corner(UR) + LEFT * 0.9 + DOWN * 0.8), bars(FAINT))
    after_t = T("After", 40, GOOD, weight=BOLD).move_to(corner, aligned_edge=LEFT)
    after = VGroup(after_t, tick().move_to(frame.get_corner(UR) + LEFT * 0.9 + DOWN * 0.8), bars(ACCENT_SOFT))
    return dict(frame=frame, before=before, after=after)


# ---- scene 3: start --------------------------------------------------------

def start_parts():
    first = chip("The first step", w=5.0).move_to(DOWN * 0.1)
    tag = T("Start here", 26, AMBER, weight=BOLD).next_to(first, UP, buff=0.3, aligned_edge=LEFT)
    return VGroup(tag, first)


# ---- stills: each scene's settled frame -----------------------------------

class S1Open(Scene):
    def construct(self):
        self.add(opening())


class S2Compare(Scene):
    def construct(self):
        p = compare_parts()
        self.add(p["frame"], p["after"])


class S3Start(Scene):
    def construct(self):
        self.add(start_parts())


# ---- the timed piece ------------------------------------------------------

HERE = Path(__file__).parent


class Explainer(Scene):
    """Each beat lands in the silence before the line it illustrates and must finish before that line's first word."""

    def setup(self):
        self.timing = json.loads((HERE / "timing.json").read_text())
        self.late = []

    def begin(self, sid):
        self.sid, self.T, self.t = sid, self.timing[sid], 0.0

    def hold(self, until):
        if until > self.t + 1e-3:
            self.wait(until - self.t)
            self.t = until

    def beat(self, n, *anims, rt=0.5, plus=None):
        starts, pre = self.T["starts"], self.T["pre"]
        if plus is None:
            lead = min(1.2, pre[n] - 0.05)
            target, deadline = starts[n] - lead, starts[n]
            rt = min(rt, lead - 0.05)
        else:
            target = starts[n] + plus
            deadline = starts[n + 1] - self.T["pre"][n + 1] if n + 1 < len(starts) else self.T["dur"] - 0.6
        self.hold(target)
        self.play(*anims, run_time=rt)
        self.t += rt
        if self.t > deadline + 1e-3:
            self.late.append(f"{self.sid} line {n}{'' if plus is None else f' +{plus}'}: ends {self.t:.2f}s, deadline {deadline:.2f}s")

    def finish(self, clear=True):
        if clear:
            self.hold(self.T["dur"] - 0.5)
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)
            self.t += 0.5
        else:
            self.hold(self.T["dur"])

    def construct(self):
        # open
        self.begin("open")
        self.beat(0, FadeIn(opening(), shift=UP * 0.15), rt=1.0)
        self.finish()

        # compare: the before and after crossfade inside one frame, linearly, so the two
        # opacities sum to one and the outgoing copy is never legible under the incoming one
        p = compare_parts()
        self.begin("compare")
        self.beat(0, FadeIn(p["frame"]), FadeIn(p["before"]), rt=1.0)
        self.beat(1, FadeOut(p["before"], rate_func=linear), FadeIn(p["after"], rate_func=linear), rt=0.6)
        # a beat inside the line, for a picture of one phrase ("that same frame")
        self.beat(1, Create(SurroundingRectangle(p["after"][1], color=ACCENT, buff=0.15)), rt=0.4, plus=1.5)
        self.finish()

        # start
        self.begin("start")
        self.beat(0, FadeIn(start_parts(), shift=RIGHT * 0.2), rt=1.0)
        self.finish(clear=False)

        report = HERE / "timing-check.txt"
        report.write_text("\n".join(self.late) + ("\n" if self.late else "every beat finishes before its line\n"))
        if self.late:
            raise SystemExit("LATE BEATS:\n" + "\n".join(self.late))
