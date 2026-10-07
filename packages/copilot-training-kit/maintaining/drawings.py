"""The parts every drawing in the kit is made from (maintaining/README.md, "Pictures").

A drawing is a simplified picture of the screen: the tool's real layout, with what the learner acts
on drawn and labelled, text whose wording varies as gray bars, and one mark colour for what the step
names. This file holds the parts that do not depend on the tool. The kit's make_drawings.py builds
the tool's own parts from these, cites each one's source, and composes each drawing.

Every colour is one of the page's tokens, so a drawing put into the page follows its light and dark
themes; the fallbacks are the light theme's values, for a drawing opened on its own.
"""
import html, io, os

STYLE = """<style>
.dg-w{fill:var(--surface,#fff);stroke:var(--rule2,#cdcdcd);stroke-width:1.5}
.dg-c{fill:var(--bg2,#f7f7f7)}
.dg-l{stroke:var(--rule2,#cdcdcd);stroke-width:1.5;fill:none}
.dg-b{fill:var(--rule,#e6e6e6)}
.dg-b2{fill:var(--rule2,#cdcdcd)}
.dg-tn{fill:var(--accent,#0065b3);fill-opacity:.14}
.dg-t{fill:var(--ink,#1b1b1b);font-size:13px}
.dg-tb{fill:var(--ink,#1b1b1b);font-size:13px;font-weight:600}
.dg-s{fill:var(--ink3,#6b6b6b);font-size:11px;letter-spacing:.06em}
.dg-n{fill:var(--ink3,#6b6b6b);font-size:13px}
.dg-ic{fill:none;stroke:var(--ink3,#6b6b6b);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.dg-p{fill:var(--surface,#fff);stroke:var(--rule2,#cdcdcd);stroke-width:1.2}
.dg-btn{fill:var(--accent,#0065b3)}
.dg-btnt{fill:var(--accent-ink,#fff);font-size:13px;font-weight:600}
.dg-btnl{stroke:var(--accent-ink,#fff);stroke-width:1;fill:none}
.dg-m{fill:none;stroke:var(--mark,#bc4c00);stroke-width:3}
.dg-mb{fill:var(--mark,#bc4c00)}
.dg-mt{fill:var(--mark-ink,#fff);font-size:12px;font-weight:600}
.dg-ml{stroke:var(--mark,#bc4c00);stroke-width:1.5;fill:none}
.dg-lab{fill:var(--mark,#bc4c00);font-size:14px;font-weight:600}
.dg-x-req{fill:var(--accent-soft,#eef4fa);stroke:var(--accent,#0065b3)}
.dg-x-card{fill:var(--bg2,#f7f7f7);stroke:var(--ctl,#767676)}
.dg-x-hit{fill:var(--bg2,#f7f7f7);stroke:var(--accent,#0065b3);stroke-width:2}
.dg-x-dim{opacity:.45}
.dg-x-arrow{stroke:var(--accent,#0065b3);stroke-width:2;fill:none}
.dg-x-head{fill:var(--accent,#0065b3)}
.dg-x-faint{stroke:var(--ctl,#767676);stroke-width:1.5;fill:none;stroke-dasharray:4 4}
.dg-x-cap{fill:var(--ink2,#505050);font-size:13px}
</style>"""


def svg(w, h, title, body):
    """A whole drawing. The builder drops the title when it puts the drawing into a page, where the
    picture's text alternative says what it shows."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="presentation">\n<title>%s</title>\n%s\n%s\n</svg>\n'
            % (w, h, title, STYLE, body.strip()))


def frame(x, y, w, h, r=8):
    """A window, panel, dialog or box: the surface colour with a thin edge."""
    return '<rect class="dg-w" x="%d" y="%d" width="%d" height="%d" rx="%d"/>' % (x, y, w, h, r)


def strip(x, y, w, h, r=0):
    """A band of the window's own chrome, such as a title bar or a side bar."""
    return '<rect class="dg-c" x="%d" y="%d" width="%d" height="%d" rx="%d"/>' % (x, y, w, h, r)


def rule(x1, y1, x2, y2):
    """A divider line."""
    return '<line class="dg-l" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (x1, y1, x2, y2)


def bar(x, y, w, h=7, strong=False):
    """Text whose wording varies, drawn as a gray bar; strong for a title or a selected line."""
    return '<rect class="%s" x="%d" y="%d" width="%d" height="%d" rx="2"/>' % ("dg-b2" if strong else "dg-b", x, y, w, h)


def text(x, y, words, bold=False, muted=False, size=None):
    """Words the screen shows, in the screen's words."""
    cls = "dg-n" if muted else ("dg-tb" if bold else "dg-t")
    style = ' style="font-size:%dpx"' % size if size else ""
    return '<text class="%s" x="%d" y="%d"%s>%s</text>' % (cls, x, y, style, html.escape(words))


def heading(x, y, words):
    """A small capitalised panel heading, such as EXPLORER."""
    return '<text class="dg-s" x="%d" y="%d">%s</text>' % (x, y, html.escape(words))


def tint(x, y, w, h, r=7):
    """The accent tint: a selected row, or the learner's own message."""
    return '<rect class="dg-tn" x="%d" y="%d" width="%d" height="%d" rx="%d"/>' % (x, y, w, h, r)


def pill(x, y, w, h=22, r=5):
    """A small outlined control, such as a picker in a toolbar."""
    return '<rect class="dg-p" x="%d" y="%d" width="%d" height="%d" rx="%d"/>' % (x, y, w, h, r)


def button(x, y, w, h, words, primary=True):
    """A button with its label: filled in the accent colour when primary, outlined otherwise."""
    if primary:
        return ('<rect class="dg-btn" x="%d" y="%d" width="%d" height="%d" rx="5"/>'
                '<text class="dg-btnt" x="%d" y="%d">%s</text>') % (x, y, w, h, x + 14, y + h / 2 + 5, html.escape(words))
    return pill(x, y, w, h) + text(x + 14, y + h / 2 + 5, words)


def checkbox(x, y):
    return '<rect class="dg-p" x="%d" y="%d" width="11" height="11" rx="2"/>' % (x, y)


def outline(x, y, w, h, r=5):
    """The mark: what the step names, outlined in the one mark colour."""
    return '<rect class="dg-m" x="%d" y="%d" width="%d" height="%d" rx="%d"/>' % (x, y, w, h, r)


def leader(points):
    """A thin mark-coloured line from an outline to its label, through (x, y) points."""
    return '<path class="dg-ml" d="M%s"/>' % "L".join("%d %d" % p for p in points)


def label(x, y, lines):
    """A label in the page's words, beside a leader's end; one string per line."""
    if isinstance(lines, str):
        lines = [lines]
    return "".join('<text class="dg-lab" x="%d" y="%d">%s</text>' % (x, y + 18 * i, html.escape(t))
                   for i, t in enumerate(lines))


def badge(x, y, n):
    """A numbered badge for an Orient drawing, whose parts are listed under it on the page."""
    return ('<circle class="dg-mb" cx="%d" cy="%d" r="10"/><text class="dg-mt" x="%d" y="%d" '
            'text-anchor="middle">%s</text>') % (x, y, x, y + 4, n)


# Explain drawings show an idea, not the screen: boxes for the things, an accent arrow for what
# happens, a dashed line and faded box for what does not. The mark colour stays for what the
# learner acts on, so an Explain drawing does not use it.

def caption(x, y, words):
    """A small heading over a column of an Explain drawing."""
    return '<text class="dg-x-cap" x="%d" y="%d">%s</text>' % (x, y, html.escape(words))


def card(x, y, w, h, lines, kind="card", bold=False):
    """A box holding one thing; kind 'card', 'hit' (the one that applies), 'req' (the learner's
    request) or 'dim' (one that does not apply). lines: one string or a list."""
    if isinstance(lines, str):
        lines = [lines]
    cls = {"card": "dg-x-card", "dim": "dg-x-card", "hit": "dg-x-hit", "req": "dg-x-req"}[kind]
    out = '<rect class="%s" x="%d" y="%d" width="%d" height="%d" rx="6"/>' % (cls, x, y, w, h)
    top = y + h / 2 - 9 * (len(lines) - 1) + 5
    for i, t in enumerate(lines):
        out += text(x + 12, top + 18 * i, t, bold=bold, size=14)
    return '<g class="dg-x-dim">%s</g>' % out if kind == "dim" else out


def arrow(points):
    """An accent arrow through (x, y) points, with its head at the last one."""
    (x1, y1), (x2, y2) = points[-2], points[-1]
    d = "M" + "L".join("%d %d" % p for p in points[:-1] + [(x2 - 8 if x2 > x1 else x2 + 8 if x2 < x1 else x2,
                                                                y2 - 8 if y2 > y1 and x2 == x1 else y2)])
    if x2 > x1:
        head = "M%d %dL%d %dL%d %dZ" % (x2 - 8, y2 - 5, x2, y2, x2 - 8, y2 + 5)
    elif x2 < x1:
        head = "M%d %dL%d %dL%d %dZ" % (x2 + 8, y2 - 5, x2, y2, x2 + 8, y2 + 5)
    else:
        head = "M%d %dL%d %dL%d %dZ" % (x2 - 5, y2 - 8, x2, y2, x2 + 5, y2 - 8)
    return '<path class="dg-x-arrow" d="%s"/><path class="dg-x-head" d="%s"/>' % (d, head)


def faint(points):
    """A dashed line for a path not taken."""
    return '<path class="dg-x-faint" d="M%s"/>' % "L".join("%d %d" % p for p in points)


def write(kit, drawings):
    """Write each drawing, {"training/images/name.svg": (width, height, title, body)}, under the kit."""
    for path, (w, h, title, body) in drawings.items():
        full = os.path.join(kit, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        io.open(full, "w", encoding="utf-8", newline="\n").write(svg(w, h, title, body))
        print("wrote", path)
