"""One explainer page from data: the library behind build_page.py, build_audio.py, check_timing.py
and build_publish.py.

A video's folder holds only its data and its build outputs:

  narration.json   what is spoken: `name` (the page is <name>-explainer.html; the folder's name
                   without "-explainer" if absent), `voice speed head gap tail`, the `brief`, a
                   `page` block (below) and `scenes`, each with `id`, `title`, optional `chapter`
                   and `step`, and `lines` (`say`, `caption`, optional `pause`, `stage`)
  scenes.py        what is drawn: BEATS = {scene id: [beat, ...]}; each beat is a dict with `line`,
                   optional `plus`, `outLine`, `outPlus`, `held`, `linear`, and `anim` and `svg`.
                   It builds its SVG with stage.py (shapes) or kitparts.py (a training kit's parts).
  timing.json      written by build_audio.py: each scene's length and its lines' measured starts
  audio/<id>.mp3   written by build_audio.py
  <name>-explainer.html   written by build_page.py; never edited by hand

The `page` block: `kind` ("explainer", the short-piece rules, or "lesson", chapters and no word
ceiling), `title`, optional `h1`, `stage_label`, `standfirst` (text), `summary_html` (the reading
column's HTML), optional `doc_title` (the browser tab's title) and optional `meta_word` (the meta
line's first word; "Video" by default). A training kit's video adds `lesson` (the lesson's path in
the kit, `/`-separated; README.md for an overview of the whole kit), `back_href` (the link from the
video to the lesson's written steps: a plain relative URL, written into the page exactly as given so
the kit's own build can find it) and `kit` (the kit's folder, relative to where the command runs;
read to build, never written into the page), and optionally `palette` ("kit" or "explainer"; "kit"
when `kit` is set).

A kit here is a training kit whose `maintaining/` folder holds `drawings.py` (its drawing parts and
their `STYLE`), `make_drawings.py` (its composed pictures) and `build_pages.py` (its colour tokens,
in a `:root{...}` block and a `:root[data-theme="dark"]{...}` block).

Each scene's `step` is the number of the lesson's step it narrates, or null; `chapter` groups
scenes under a heading in the transcript and a deeper notch in the bar (a video past about six
minutes is split into chapters). The page opens on a scene at `<page>#<scene id>`.
"""
import html
import html.entities
import importlib.util
import json
import re
import sys
from pathlib import Path

BUILDER = Path(__file__).resolve().parent
TEMPLATE = BUILDER / "page-template.html"

RAMP = 0.25       # a beat's fade; shorter than the pause it runs inside
MAX_LEAD = 1.2    # how far a beat reaches back into its line's silence
SLUG = re.compile(r"[a-z0-9-]+$")

# --- the palette ----------------------------------------------------------------------------------
# The explainer's own tokens, light and dark: the palette of a piece with no kit, and the values of
# the tokens the kit has no equivalent for.
EXPLAINER = [
    ("--bg", "#EEEDE8", "#0E1014"), ("--paper", "#FBFAF7", "#1B1F25"), ("--ink", "#14171C", "#ECEEF1"),
    ("--muted", "#5F646B", "#99A0A8"), ("--line", "#CBCED2", "#353B43"), ("--accent", "#1F6F78", "#6FC3CB"),
    ("--accent-soft", "#DCEDEE", "#1D3436"), ("--caution", "#8A5F08", "#DFA62E"),
    ("--caution-ui", "#C8900F", "#DFA62E"), ("--good", "#2E7D55", "#5FBF8C"), ("--bad", "#B33A2E", "#E0847A"),
    ("--surface", "#FBFAF7", "#161A1F"), ("--hover", "#E4E5E0", "#20252C"), ("--line-soft", "#DEDFDB", "#262B32"),
    ("--shadow", "0 1px 2px rgb(20 23 28 / .06), 0 8px 28px -12px rgb(20 23 28 / .22)",
     "0 1px 2px rgb(0 0 0 / .4), 0 10px 30px -14px rgb(0 0 0 / .7)"),
    ("--console-bg", "#1B1E23", "#111418"), ("--console-fg", "#F2F1ED", "#ECEEF1"),
    ("--console-dim", "#A3A9B0", "#9AA1A9"), ("--console-line", "#33383F", "#2B3037"),
    ("--console-hover", "#2A2F36", "#222830"), ("--track-rest", "#666C75", "#5E646C"),
]
KIT_TOKENS = ["--bg", "--bg2", "--surface", "--ink", "--ink2", "--ink3", "--rule", "--rule2", "--accent",
              "--accent-soft", "--accent-ink", "--ctl", "--mark", "--mark-ink"]
# Explainer token -> kit token. One table; the page's blocks are written from it.
ALIAS = [("--paper", "--surface"), ("--muted", "--ink3"), ("--line", "--rule2"),
         ("--line-soft", "--rule"), ("--hover", "--bg2"), ("--caution", "--mark"), ("--caution-ui", "--mark")]
KEEP = ["--good", "--bad", "--shadow", "--console-bg", "--console-fg", "--console-dim", "--console-line",
        "--console-hover", "--track-rest"]


def kit_palette(kit):
    """The kit's tokens, light and dark, read from the kit's own page builder."""
    src = (Path(kit) / "maintaining" / "build_pages.py").read_text(encoding="utf-8")
    light = re.search(r"\n:root\{(--bg:.*?)\}", src, re.S).group(1)
    dark = re.search(r'\n:root\[data-theme="dark"\]\{(.*?)\}', src, re.S).group(1)

    def pick(block):
        vals = dict(re.findall(r"(--[\w-]+):([^;]+)", block))
        missing = [t for t in KIT_TOKENS if t not in vals]
        if missing:
            raise SystemExit(f"the kit's build_pages.py no longer defines {missing}")
        return {t: vals[t].strip() for t in KIT_TOKENS}
    return pick(light), pick(dark)


def tokens_css(kit=None):
    own = {n: (lt, dk) for n, lt, dk in EXPLAINER}
    if kit is None:
        light = [(n, lt) for n, lt, _ in EXPLAINER]
        dark = [(n, dk) for n, _, dk in EXPLAINER]
        aliases = []
    else:
        kl, kd = kit_palette(kit)
        light = list(kl.items()) + [(n, own[n][0]) for n in KEEP]
        dark = list(kd.items()) + [(n, own[n][1]) for n in KEEP]
        aliases = [(a, f"var({b})") for a, b in ALIAS]

    def block(pairs, indent="  "):
        return "\n".join(f"{indent}{n}: {v};" for n, v in pairs)
    head = ("/* Generated from one table (builder/explainer.py): "
            + ("the kit's tokens, the explainer's tokens aliased onto them, and the explainer's own "
               "for what the kit has no equivalent for." if kit else "the explainer's tokens.") + " */")
    return (f"{head}\n:root {{\n{block(light)}\n" + (block(aliases) + "\n" if aliases else "") + "}\n"
            f"@media (prefers-color-scheme: dark) {{\n  :root:not([data-theme=\"light\"]) {{\n"
            f"{block(dark, '    ')}\n    color-scheme: dark;\n  }}\n}}\n"
            f":root[data-theme=\"dark\"] {{\n{block(dark)}\n  color-scheme: dark;\n}}")


# --- loading ------------------------------------------------------------------------------------
class Video:
    def __init__(self, folder):
        self.dir = Path(folder).resolve()
        self.spec = json.loads((self.dir / "narration.json").read_text(encoding="utf-8-sig"))
        self.page = self.spec.get("page", {})
        self.scenes = self.spec["scenes"]
        self.ids = [s["id"] for s in self.scenes]
        bad = [i for i in self.ids if not SLUG.match(i)]
        if bad or len(set(self.ids)) != len(self.ids):
            raise SystemExit(f"scene ids must be unique and lowercase [a-z0-9-]: {bad or self.ids}")
        kit = self.page.get("kit")
        self.kit = Path(kit).resolve() if kit else None
        if self.kit and not (self.kit / "maintaining").is_dir():
            raise SystemExit(f"`kit` is {kit!r}, relative to where the command runs, and is not a kit folder")

    @property
    def kind(self):
        return self.page.get("kind", "explainer")

    def timing(self):
        f = self.dir / "timing.json"
        if not f.exists():
            raise SystemExit(f"no timing.json in {self.dir}: run build_audio.py first")
        return json.loads(f.read_text(encoding="utf-8-sig"))

    def beats(self):
        f = self.dir / "scenes.py"
        if not f.exists():
            raise SystemExit(f"no scenes.py in {self.dir}")
        sys.path[:0] = [str(BUILDER), str(self.dir)]
        try:
            spec = importlib.util.spec_from_file_location("video_scenes", f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            del sys.path[:2]
        beats = mod.BEATS
        extra = [k for k in beats if k not in self.ids]
        missing = [i for i in self.ids if not beats.get(i)]
        if extra or missing:
            raise SystemExit(f"scenes.py and narration.json disagree: beats for unknown scenes {extra}, "
                             f"scenes with no beats {missing}")
        return beats

    def page_path(self):
        name = self.spec.get("name") or self.dir.name.removesuffix("-explainer")
        return self.dir / f"{name}-explainer.html"

    def rel(self, p):
        p = Path(p).resolve()
        try:
            return p.relative_to(Path.cwd()).as_posix()
        except ValueError:
            pass
        try:
            # outside the cwd: name it from the skill folder, never by an absolute path
            return p.relative_to(BUILDER.parent.parent).as_posix()
        except ValueError:
            return p.name


# --- writing the page ---------------------------------------------------------------------------
def ascii_html(s):
    """Every non-ASCII character as an HTML entity, named where HTML has a name."""
    out = []
    for ch in s:
        if ord(ch) < 128:
            out.append(ch)
        else:
            name = html.entities.codepoint2name.get(ord(ch))
            out.append(f"&{name};" if name else f"&#{ord(ch)};")
    return "".join(out)


def js_data(obj):
    """Data for the page's script: ASCII (non-ASCII as \\u escapes) and safe inside <script>."""
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":")).replace("</", "<\\/")


def lesson_link(page):
    href = page.get("back_href")
    if not href:
        return ""
    # Written verbatim: a kit's own build may look for href="<back_href>" exactly.
    if re.search(r'[\s"<>&\']', href) or not href.isascii():
        raise SystemExit(f"back_href {href!r} must be a plain relative URL: no spaces, quotes, <, > or &")
    words = "Back to the trainings" if page.get("lesson") == "README.md" else f"Written steps: {page['title']}"
    return (f' <nav class="lessonlink" aria-label="This lesson"><a href="{href}">'
            f'{ascii_html(html.escape(words, quote=False))} <span aria-hidden="true">&rsaquo;</span></a></nav>')


BEAT_KEYS = ("line", "plus", "outLine", "outPlus", "anim", "held", "linear", "svg")


def render(video):
    page, timing, beats = video.page, video.timing(), video.beats()
    data = []
    for sc in video.scenes:
        if sc["id"] not in timing:
            raise SystemExit(f"timing.json has no scene {sc['id']}: run build_audio.py")
        entry = {"id": sc["id"], "lines": [{"caption": l["caption"]} for l in sc["lines"]],
                 "beats": [{k: b[k] for k in BEAT_KEYS if k in b} for b in beats[sc["id"]]]}
        if sc.get("title"):
            entry["title"] = sc["title"]
        if sc.get("chapter"):
            entry["chapter"] = sc["chapter"]
        data.append(entry)
    rows = ",\n".join(f"    {json.dumps(sid)}: {{ dur: {timing[sid]['dur']}, starts: [{', '.join(str(x) for x in timing[sid]['starts'])}],"
                      f" pre: [{', '.join(str(x) for x in timing[sid]['pre'])}] }}" for sid in video.ids)
    uses_kit = any('class="dg-' in b.get("svg", "") for bs in beats.values() for b in bs)
    palette = page.get("palette", "kit" if video.kit else "explainer")
    if (uses_kit or palette == "kit") and not video.kit:
        raise SystemExit("the beats use the kit's drawing parts or palette, but narration.json's page has no `kit`")
    kit_style = ""
    if uses_kit:
        sys.path.insert(0, str(BUILDER))
        import kitparts
        kit_style = "/* The kit's drawing parts (its maintaining/drawings.py), in once. */\n" + kitparts.kit_style(video.kit)
    out = video.page_path()
    build = f"python {video.rel(BUILDER / 'build_page.py')} {video.rel(video.dir)}"
    discovery = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n"
                 f"     Source: {video.rel(video.dir / 'narration.json')}, {video.rel(video.dir / 'scenes.py')}, "
                 f"{video.rel(video.dir / 'timing.json')}\n"
                 f"     Builder: {video.rel(BUILDER / 'build_page.py')} (template {video.rel(TEMPLATE)})\n"
                 f"     Build: {build}\n-->")
    title = page["title"]
    fill = {
        "DISCOVERY": discovery,
        "DOC_TITLE": ascii_html(html.escape(page.get("doc_title", title), quote=False)),
        "TOKENS": tokens_css(video.kit if palette == "kit" else None),
        "KIT_STYLE": kit_style,
        "LESSON_LINK": lesson_link(page),
        "H1": ascii_html(html.escape(page.get("h1", title), quote=False)),
        "KIND": page.get("meta_word", "Video"),
        "NOUN": page.get("meta_word", "Video").lower(),
        "STAGE_LABEL": ascii_html(html.escape(page.get("stage_label",
                                  f"Animated video: {title}. The narration is written out in the transcript."))),
        "STANDFIRST": ascii_html(html.escape(page.get("standfirst", ""), quote=False)),
        "SUMMARY": ascii_html(page.get("summary_html", "")),
        "RAMP": str(RAMP),
        "MAX_LEAD": str(MAX_LEAD),
        "TIMING_ROWS": rows,
        "SCENES_JSON": js_data(data),
    }
    text = TEMPLATE.read_text(encoding="utf-8")
    text = re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: fill[m.group(1)], text)
    if "{{" in text.split("var S = ", 1)[0]:
        raise SystemExit("a placeholder in page-template.html was not filled")
    try:
        text.encode("ascii")
    except UnicodeEncodeError as e:
        raise SystemExit(f"the generated page is not ASCII at {e.start}: {text[e.start - 40:e.start + 10]!r}")
    out.write_text(text, encoding="utf-8", newline="\n")
    return out


# --- checks -------------------------------------------------------------------------------------
def page_scenes(text):
    m = re.search(r"\n  var S = (.*?);\n", text)
    if not m:
        raise SystemExit("could not find the scene data (`var S = ...;`) in the page")
    return json.loads(m.group(1).replace("<\\/", "</"))


def check_captions(video, page_file=None):
    """The page's captions, decoded, must equal narration.json's. Returns the count."""
    text = Path(page_file or video.page_path()).read_text(encoding="utf-8")
    got = [l["caption"] for sc in page_scenes(text) for l in sc["lines"]]
    want = [l["caption"] for sc in video.scenes for l in sc["lines"]]
    if got != want:
        for i, (a, b) in enumerate(zip(got + [None] * len(want), want + [None] * len(got))):
            if a != b:
                raise SystemExit(f"page caption {i} differs\n  page: {a!r}\n  json: {b!r}")
    return len(want)


def lead(tm, n):
    return max(0.0, tm["starts"][n] - min(MAX_LEAD, max(0.0, tm["pre"][n] - 0.05)))


def check_timing(video):
    """Every beat finished before the voice reaches what it draws. Returns (report lines, failures)."""
    timing, beats, tail = video.timing(), video.beats(), video.spec["tail"]
    measured = hand = 0
    bad = []
    for sc in video.scenes:
        sid = sc["id"]
        tm = timing[sid]
        nlines = len(tm["starts"])
        if nlines != len(sc["lines"]):
            bad.append(f"{sid}: timing.json has {nlines} lines, narration.json {len(sc['lines'])}: rerun build_audio.py")
            continue
        for b in beats[sid]:
            n, plus = b.get("line"), b.get("plus")
            if not isinstance(n, int) or not (plus is None or isinstance(plus, (int, float))):
                bad.append(f"{sid}: a beat's line is {n!r} and plus {plus!r}; line must be a whole number")
                continue
            if n >= nlines or n < 0:
                bad.append(f"{sid} beat on line {n}: the scene has {nlines} lines")
                continue
            for k in ("outLine",):
                if k in b and not (isinstance(b[k], int) and 0 <= b[k] < nlines):
                    bad.append(f"{sid} beat on line {n}: outLine {b[k]!r} is not a line of the scene")
            if b.get("held"):
                continue  # what the last scene left on screen: shown at once, nothing to land
            if plus is None:
                measured += 1
                at, deadline = lead(tm, n), tm["starts"][n]
                what = f"{sid} line {n} (measured)"
            else:
                hand += 1
                at = tm["starts"][n] + plus
                deadline = (tm["starts"][n + 1] - tm["pre"][n + 1]) if n + 1 < nlines else tm["dur"] - tail
                what = f"{sid} line {n} +{plus} (hand-placed)"
            if at + RAMP > deadline + 1e-9:
                bad.append(f"{what}: ends {at + RAMP:.2f}s, deadline {deadline:.2f}s")
    total = sum(timing[i]["dur"] for i in video.ids)
    pause = (len(video.ids) * (video.spec["head"] + tail)
             + sum(l.get("pause", video.spec["gap"]) for sc in video.scenes for l in sc["lines"][:-1]))
    report = [f"beats: {measured} placed from measurement, {hand} by hand, {measured + hand} checked",
              f"runtime: {total:.1f}s ({int(total // 60)}:{int(total % 60):02d}); "
              f"silence {pause:.1f}s, {pause / total * 100:.0f}% of it"]
    return report, bad


def chapters(video):
    """[(chapter name or None, [scene ids])], in order."""
    out = []
    for sc in video.scenes:
        ch = sc.get("chapter")
        if not out or out[-1][0] != ch:
            out.append((ch, []))
        out[-1][1].append(sc["id"])
    return out
