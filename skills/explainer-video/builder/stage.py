"""The stage's drawing helpers, for a video's scenes.py: shapes and text on the 960 by 540 stage.

Each returns an SVG fragment as a string; a beat's `svg` is one or more of them joined. Colours are
the stage tokens (build-page.md, step 8), so a drawing follows the page's light and dark themes.
These are the page's former JavaScript helpers, ported so a scene is data rather than code in the
page; they write the same markup.

For a screen from the training kit, use kitparts.py instead: the kit's own parts, placed on the stage.
"""
import html

INK, MUTED, ACCENT = "var(--ink)", "var(--muted)", "var(--accent)"
CAUTION, GOOD, BAD = "var(--caution)", "var(--good)", "var(--bad)"
LINE, PAPER, SOFT, BG = "var(--line)", "var(--paper)", "var(--accent-soft)", "var(--bg)"
AMBER = CAUTION


def num(v):
    """A number written the way the page's JavaScript wrote it: 198, not 198.0."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def attrs(pairs):
    return "".join(' %s="%s"' % (k, num(v)) for k, v in pairs if v is not None)


def esc(s):
    return html.escape(str(s), quote=False)


def txt(x, y, s, size=24, fill=INK, weight=400, anchor="start", ls=None, cls=None, raw=False):
    """Text: a label on the stage, never the sentence the voice is speaking (SKILL.md)."""
    return "<text%s>%s</text>" % (attrs([("x", x), ("y", y), ("fill", fill), ("font-size", size),
                                         ("font-weight", weight), ("text-anchor", anchor),
                                         ("letter-spacing", ls), ("class", cls)]), s if raw else esc(s))


def tspan(s, fill=None, weight=None):
    return "<tspan%s>%s</tspan>" % (attrs([("fill", fill), ("font-weight", weight)]), esc(s))


def box(x, y, w, h, r=8, fill="none", stroke=LINE, sw=1.6):
    return "<rect%s/>" % attrs([("x", x), ("y", y), ("width", w), ("height", h), ("rx", r),
                               ("fill", fill), ("stroke", stroke), ("stroke-width", sw)])


def rect(x, y, w, h, fill, rx=None, opacity=None):
    """A filled rectangle with no edge, such as a bar standing for a line of text."""
    return "<rect%s/>" % attrs([("x", x), ("y", y), ("width", w), ("height", h), ("rx", rx),
                               ("fill", fill), ("opacity", opacity)])


def line(x1, y1, x2, y2, stroke=LINE, sw=2):
    return "<line%s/>" % attrs([("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2), ("stroke", stroke),
                               ("stroke-width", sw), ("stroke-linecap", "round")])


def circle(cx, cy, r, fill="none", stroke=None, sw=1.6):
    return "<circle%s/>" % attrs([("cx", cx), ("cy", cy), ("r", r), ("fill", fill),
                                 ("stroke", stroke), ("stroke-width", sw)])


def path(d, fill="none", stroke=None, sw=2):
    return "<path%s/>" % attrs([("d", d), ("fill", fill), ("stroke", stroke), ("stroke-width", sw),
                               ("stroke-linejoin", "round"), ("stroke-linecap", "round")])


def tick(x, y, color=GOOD):
    """Right, drawn as a path: no font on any machine has to carry it."""
    return path("M%s,%s L%s,%s L%s,%s" % (num(x), num(y - 5), num(x + 7), num(y + 2), num(x + 19), num(y - 14)),
                stroke=color, sw=3.4)


def cross(x, y, color=BAD):
    """Wrong, drawn as a path."""
    return path("M%s,%s L%s,%s M%s,%s L%s,%s" % (num(x), num(y - 13), num(x + 14), num(y + 1),
                                                  num(x + 14), num(y - 13), num(x), num(y + 1)),
                stroke=color, sw=3.4)


def person(cx, cy, fill=MUTED):
    return circle(cx, cy - 14, 9, fill=fill) + path("M%s,%s a13,13 0 0 1 26,0 z" % (num(cx - 13), num(cy + 8)), fill=fill)


def chip(x, y, w, label, color=ACCENT, outline=False, h=46, size=19):
    """A named thing in a rounded box, tinted, or outlined when it is not yet the subject."""
    return (box(x, y, w, h, fill=PAPER if outline else SOFT, stroke=color, sw=2.2, r=8) +
            txt(x + 18, y + h / 2 + 7, label, size=size, fill=color, weight=700))


def arrow_head(x, y, direction, color=ACCENT):
    d = ("M%s,%s l14,-8 l0,16 z" if direction == "left" else "M%s,%s l-14,-8 l0,16 z") % (num(x), num(y))
    return path(d, fill=color, stroke=color, sw=1)


def dim(svg, opacity=".2"):
    """What stays on screen as context, faded so the new part reads as the subject."""
    return '<g opacity="%s">%s</g>' % (opacity, svg)
