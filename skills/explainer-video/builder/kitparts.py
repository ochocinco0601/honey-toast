"""The training kit's drawing parts, for a lesson video's scenes.py.

A lesson screen is drawn by the same calls, with the same arguments, as the picture in its lesson,
so the claims checked for that picture carry over. Each kit function returns one SVG fragment, so
each part can be its own beat; a reveal is the next beat. A picture drawn at its own size is put on
the 960 by 540 stage by one transform, scaled to fit inside the stage's margins:

    import kitparts
    kit = kitparts.load("path/to/your-kit")   # relative to the folder you run from
    pic = kitparts.Picture(700, 440)
    BEATS = {"open-chat": [
        {"line": 0, "anim": "fade", "svg": pic.place(kit.make.window)},
        {"line": 1, "anim": "fade", "svg": pic.place(kit.d.outline(520, 82, 164, 42))},
    ]}

`kit.d` is the kit's drawings.py (frame, strip, bar, text, outline, leader, label, card, arrow...);
`kit.make` is its make_drawings.py (VS Code's own parts, such as chat_box, explorer, agent_control,
and the composed pictures, such as window and perm). Neither file is changed or copied here.

The `.dg-*` stylesheet those parts use goes into the page once (explainer.py does this when any beat
uses a kit class), and the kit's colour tokens are the page's.
"""
import importlib.util
import sys
import types
from pathlib import Path

STAGE_W, STAGE_H, MARGIN = 960, 540, 30


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load(kit_dir):
    """The kit's drawing modules, read from its maintaining/ folder. kit_dir: relative to the cwd."""
    kit_dir = Path(kit_dir)
    maint = kit_dir.resolve() / "maintaining"
    if str(maint) not in sys.path:
        sys.path.insert(0, str(maint))  # make_drawings.py imports drawings by name
    d = _module("drawings", maint / "drawings.py")
    sys.modules.setdefault("drawings", d)
    make = _module("kit_make_drawings", maint / "make_drawings.py")
    return types.SimpleNamespace(d=d, make=make, style=kit_style(kit_dir))


def kit_style(kit_dir):
    """The rules of the kit's drawing stylesheet, without its <style> tags."""
    d = _module("drawings_style", Path(kit_dir).resolve() / "maintaining" / "drawings.py")
    return d.STYLE.replace("<style>", "").replace("</style>", "").strip()


class Picture:
    """A picture drawn at w by h, centred on the stage at the largest scale that keeps the margin."""

    def __init__(self, w, h, margin=MARGIN, scale=None):
        self.w, self.h = w, h
        self.s = scale or min((STAGE_W - 2 * margin) / w, (STAGE_H - 2 * margin) / h)
        self.x = round((STAGE_W - w * self.s) / 2, 2)
        self.y = round((STAGE_H - h * self.s) / 2, 2)

    def place(self, fragment):
        """One part of the picture, in the picture's own coordinates, put on the stage."""
        return '<g transform="translate(%s %s) scale(%s)">%s</g>' % (
            _n(self.x), _n(self.y), _n(round(self.s, 4)), fragment.strip())

    def to_stage(self, x, y, w, h):
        """A rectangle of the picture's coordinates, in the stage's."""
        return (self.x + x * self.s, self.y + y * self.s, w * self.s, h * self.s)


_clips = [0]


def _clip_id(prefix):
    _clips[0] += 1
    return "%s%d" % (prefix, _clips[0])


class Crop:
    """A region (x, y, w, h) of a picture drawn at its own size, scaled to fill the stage inside the
    margin and clipped to the region: a lesson picture cropped to the part a scene is about, so its
    words reach the size rule. `cap` limits the scale."""

    def __init__(self, x, y, w, h, margin=MARGIN, cap=None):
        self.x0, self.y0, self.w, self.h = x, y, w, h
        s = min((STAGE_W - 2 * margin) / w, (STAGE_H - 2 * margin) / h)
        self.s = min(s, cap) if cap else s
        self.x = round((STAGE_W - w * self.s) / 2 - x * self.s, 2)
        self.y = round((STAGE_H - h * self.s) / 2 - y * self.s, 2)

    def place(self, fragment):
        cid = _clip_id("kc")
        return ('<g transform="translate(%s %s) scale(%s)"><clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s"/>'
                '</clipPath><g clip-path="url(#%s)">%s</g></g>') % (
            _n(self.x), _n(self.y), _n(round(self.s, 4)), cid, self.x0, self.y0, self.w, self.h, cid, fragment.strip())

    to_stage = Picture.to_stage


def fade_except(*holes, pad=6, opacity=.78):
    """The whole stage faded except each hole (x, y, w, h, in stage units): the kit's way of
    highlighting, the rest faded, for a scene whose subject is one or more parts of its picture."""
    d = "M0 0H%dV%dH0Z" % (STAGE_W, STAGE_H)
    for x, y, w, h in holes:
        d += "M%s %sV%sH%sV%sZ" % (_r(x - pad), _r(y - pad), _r(y + h + pad), _r(x + w + pad), _r(y - pad))
    return '<path fill-rule="evenodd" style="fill:var(--paper);fill-opacity:%s" d="%s"/>' % (opacity, d)


def inset(host, fragment, region, scale, side, gap=22, pad=8):
    """An enlarged composition: `region` (x, y, w, h) of a picture `host` places on the stage (a
    Picture or a Crop), its parts drawn by the same calls (`fragment`, in the picture's coordinates)
    and placed by one transform at `scale` stage units per picture unit, beside its source on `side`
    ("above", "below", "left" or "right") and joined to it by the kit's mark line. For a word the
    narration names that the whole picture draws under the size rule.

    The frame is neutral (--rule2 on --surface): the mark colour stays on the named part inside and
    on the leader. Choose `region` to end at whole parts, never through one. Fade the rest with
    fade_except(source on the stage) in the same beat, so the inset is the one thing at full strength."""
    x, y, w, h = region
    sx, sy, sw, sh = host.to_stage(x, y, w, h)
    W, H = w * scale, h * scale
    if side == "above":
        X, Y = sx + sw / 2 - W / 2, sy - gap - H - pad
    elif side == "below":
        X, Y = sx + sw / 2 - W / 2, sy + sh + gap + pad
    elif side == "left":
        X, Y = sx - gap - W - pad, sy + sh / 2 - H / 2
    else:
        X, Y = sx + sw + gap + pad, sy + sh / 2 - H / 2
    X = min(max(X, 10 + pad), STAGE_W - 10 - pad - W)
    Y = min(max(Y, 10 + pad), STAGE_H - 10 - pad - H)
    # the leader: from the frame's edge facing the source to the source's edge facing the frame
    if side in ("above", "below"):
        lx = min(max(sx + sw / 2, X + 12), X + W - 12)
        a = (lx, Y + H + pad if side == "above" else Y - pad)
        b = (sx + sw / 2, sy if side == "above" else sy + sh)
    else:
        ly = min(max(sy + sh / 2, Y + 12), Y + H - 12)
        a = (X + W + pad if side == "left" else X - pad, ly)
        b = (sx if side == "left" else sx + sw, sy + sh / 2)
    cid = _clip_id("ki")
    return ('<path style="fill:none;stroke:var(--mark);stroke-width:2" d="M%s %sL%s %s"/>' % (_r(a[0]), _r(a[1]), _r(b[0]), _r(b[1])) +
            '<rect x="%s" y="%s" width="%s" height="%s" rx="10" style="fill:var(--surface);stroke:var(--rule2);stroke-width:2"/>' % (
                _r(X - pad), _r(Y - pad), _r(W + 2 * pad), _r(H + 2 * pad)) +
            '<g transform="translate(%s %s) scale(%s)"><clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s"/></clipPath>'
            '<g clip-path="url(#%s)">%s</g></g>' % (_r(X - x * scale), _r(Y - y * scale), _n(scale), cid, x, y, w, h, cid, fragment.strip()))


def _r(v):
    return _n(round(v, 1))


def _n(v):
    return str(int(v)) if float(v).is_integer() else str(v)
