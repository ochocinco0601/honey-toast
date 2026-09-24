"""Build the trainings' web pages from their markdown, then check them.

    python maintaining/build_pages.py        (from the kit's folder)

Reads every learner .md file in the kit and writes read-in-browser/ with the same
names (.md -> .html; a subfolder's README.md -> index.html). Never edit read-in-browser/ by
hand. The conventions it reads are in maintaining/README.md.
"""
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys

# ---- What a maintainer changes when the kit grows (see maintaining/README.md) ----
PROGRAM_NAME = "GitHub Copilot training"
# The trainings, in the order the home page lists them. Each lives in its own folder with its own
# README.md. "path" lists its units in order: (file in the folder, name in the menu, time). A
# training with no path yet is shown as "coming later". "before" lists pages, by their place in
# the kit, that a learner goes through before unit 1, such as a setup page. "stuck_from" gives the
# first step on a unit that offers "Stuck on this step?"; 1 unless listed.
TRAININGS = [
    {"folder": "getting-started", "name": "Getting started", "level": "Beginner",
     "time": "about an hour and a quarter",
     "path": [("start-here.md", "Start here", "about fifteen minutes"),
              ("lesson-your-files.md", "Your own files", "about thirty minutes"),
              ("lesson-application.md", "An application you do not own",
               "about twenty-five minutes, plus two steps later"),
              ("first-real-chore.md", "Your first real chore", "on your own work, this week")],
     "before": [], "stuck_from": {"start-here.md": 4}},
    {"folder": "skills-in-depth", "name": "Skills, in more depth", "level": "", "time": "", "path": [],
     "before": [], "stuck_from": {}},
    {"folder": "agents", "name": "Agents", "level": "", "time": "", "path": [], "before": [], "stuck_from": {}},
]
# The side menu's groups shared by every page: (group, open by default, [(file, name, anchor)]).
MENU_AFTER = [
    ("Help", True, [("troubleshooting.md", "When you are stuck", "when-you-are-stuck-ask-the-assistant-first"),
                    ("troubleshooting.md", "If something goes wrong", ""),
                    ("faq.md", "Questions", ""),
                    ("glossary.md", "Glossary", "")]),
    ("More", True, [("explanation.md", "Why this assistant is different", ""),
                    ("skills.md", "Your organization's skills (it fills this in)", "")]),
]
# Glossary words linked where first used on a page, and VS Code labels never to link.
GLOSSARY_TERMS = ["Agent mode", "Permission request", "Preview", "Terminal", "Workspace", "Blank",
                  "Check the receipts", "Chore", "Command", "CSV", "Export", "House rules", "Markdown",
                  "New chat", "Skill", "Clone", "Code host", "Connector", "Documentation generator",
                  "Extension", "Git", "Repository", "Mode selector", "Workbench"]
UI_LABELS = ("Add Folder to Workspace", "Clone Git Repository", "Open Recent", "Open Folder", "New File")
# Folders that are not learner pages.
NOT_FOR_LEARNERS = ("facilitator/", "sample-files/", "maintaining/", "read-in-browser/")
# ---- End of what a maintainer changes ----

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, ".."))
OUT_DIR = "read-in-browser"
OUT = os.path.join(KIT, OUT_DIR)
MARKER = re.compile(r"^<!--\s*(frame|tutor)\s*-->$")


def kit_files():
    found = []
    for root, _, files in os.walk(KIT):
        for f in files:
            md = os.path.relpath(os.path.join(root, f), KIT).replace("\\", "/")
            if md.endswith(".md") and not md.startswith(NOT_FOR_LEARNERS):
                found.append(md)
    return sorted(found)


FILES = kit_files()


def out_name(md):
    if "/" in md and md.endswith("/README.md"):
        return md[:-len("README.md")] + "index.html"
    return md[:-3] + ".html"


def rel(from_md, to_path):
    return os.path.relpath(to_path, os.path.dirname(from_md) or ".").replace("\\", "/")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def read(md):
    return io.open(os.path.join(KIT, md), encoding="utf-8").read().replace("\r\n", "\n").split("\n")


def title_of(md):
    first = read(md)[0]
    return first[2:].strip() if first.startswith("# ") else md


def link_href(src, target):
    """A relative markdown link to a kit page becomes a link to its web page."""
    path, _, anchor = target.partition("#")
    if not path:
        return "#" + anchor
    full = os.path.normpath(os.path.join(os.path.dirname(src), path)).replace("\\", "/")
    if full not in FILES:
        return None
    return rel(src, out_name(full)) + ("#" + anchor if anchor else "")


def inline(text, src):
    out = []
    for p in re.split(r"(`[^`]+`|\[[^\]]+\]\([^)]+\))", text):
        if len(p) > 1 and p.startswith("`") and p.endswith("`"):
            inner = p[1:-1]
            if inner.startswith("[YOUR ORGANIZATION"):
                out.append('<span class="org" title="Your organization fills this in">%s</span>' % html.escape(inner))
            elif inner.startswith("[TO BE WRITTEN"):
                out.append('<span class="org" title="Not written yet">%s</span>' % html.escape(inner))
            else:
                out.append("<code>%s</code>" % html.escape(inner))
        elif re.fullmatch(r"\[[^\]]+\]\([^)]+\)", p):
            label, target = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", p).groups()
            href = link_href(src, target)
            shown = inline(label, src)
            out.append('<a href="%s">%s</a>' % (html.escape(href), shown) if href else shown)
        else:
            e = html.escape(p, quote=False)
            out.append(re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e))
    return "".join(out)


def prompt_text(raw, fill):
    shown = html.escape(raw.replace("`", ""), quote=False)
    out = []
    for p in re.split(r"(&lt;.+?&gt;)", shown):
        if p.startswith("&lt;") and p.endswith("&gt;"):
            folder = " data-folder" if fill and p == "&lt;your folder&gt;" else ""
            out.append('<span class="ph"%s>%s</span>' % (folder, p))
        else:
            out.append(p)
    return "".join(out)


BLANK = re.compile(r"\[(YOUR ORGANIZATION|TO BE WRITTEN):[^\]]*\]")


def prompt_block(raw, kind=None):
    if re.fullmatch(r"`%s`" % BLANK.pattern, raw.strip()):
        who = ("Your organization supplies this prompt; until it does, there is nothing to paste here."
               if "YOUR ORGANIZATION" in raw else "This prompt is not written yet, so there is nothing to paste here.")
        return ('<div class="prompt orgprompt"><p class="lab">%s</p>'
                '<div class="t">%s</div></div>' % (who, inline(raw.strip(), "")))
    if kind == "frame":
        return ('<div class="prompt frame"><p class="lab">Write this yourself in the chat, filling in each part:</p>'
                '<div class="t">%s</div></div>' % prompt_text(raw, False))
    first = re.sub(r"[`<>]", "", raw)
    first = first if len(first) <= 40 else first[:40].rsplit(" ", 1)[0] + "…"
    cls = "prompt tutor" if kind == "tutor" else "prompt"
    lab = '<p class="lab">Ask the assistant:</p>' if kind == "tutor" else ""
    return ('<div class="%s">%s<div class="t">%s</div>'
            '<button class="copy" type="button" aria-label="Copy prompt: %s">Copy</button>'
            '<p class="after" hidden>Pasted it? Change the highlighted part in the chat box before you press Enter.</p></div>'
            % (cls, lab, prompt_text(raw, True), html.escape(first)))


def table(rows, src):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], [r for r in cells[1:] if not all(set(c) <= set("-: ") for c in r)]
    th = "".join('<th scope="col">%s</th>' % inline(h, src) for h in head)
    trs = []
    for r in body:
        rid = ' id="%s"' % slug(re.sub(r"[`*]", "", r[0])) if src == "glossary.md" else ""
        tds = ['<th scope="row"%s>%s</th>' % (rid, inline(r[0], src))] + ["<td>%s</td>" % inline(c, src) for c in r[1:]]
        trs.append("<tr>%s</tr>" % "".join(tds))
    return '<div class="tw"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, "".join(trs))


def item_html(lines, src):
    h, text, kind = [], [], None

    def flush():
        if text:
            h.append(inline(" ".join(text), src))
            text.clear()
    for ln in lines:
        m = MARKER.match(ln)
        if m:
            flush()
            kind = m.group(1)
        elif ln == "":
            flush()
            h.append('<div class="gap"></div>')
        elif ln.startswith("> "):
            flush()
            h.append(prompt_block(ln[2:], kind))
            kind = None
        else:
            text.append(ln)
    flush()
    return "".join(h)


def render(lines, src):
    h, i, kind = [], 0, None
    while i < len(lines):
        ln, s = lines[i], lines[i].strip()
        m = MARKER.match(s)
        if m:
            kind = m.group(1)
            i += 1
        elif not s:
            i += 1
        elif ln.startswith(("## ", "### ", "#### ")):
            level = len(ln.split(" ", 1)[0])
            t = ln[level + 1:].strip()
            h.append('<h%d id="%s">%s</h%d>' % (level, slug(t), inline(t, src), level))
            i += 1
        elif s.startswith("> "):
            h.append(prompt_block(s[2:], kind))
            kind = None
            i += 1
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            h.append(table(rows, src))
        elif ln.startswith("- ") or re.match(r"^\d+\.\s", ln):
            lkind = "ul" if ln.startswith("- ") else "ol"
            items = []
            while i < len(lines):
                cur = lines[i]
                if not cur.strip():
                    nxt = next((l for l in lines[i + 1:] if l.strip()), "")
                    same = (lkind == "ul" and nxt.startswith("- ")) or \
                           (lkind == "ol" and re.match(r"^\d+\.\s", nxt) and not re.match(r"^1\.\s", nxt))
                    if same:
                        i += 1
                        continue
                    if nxt.startswith("   "):
                        items[-1].append("")
                        i += 1
                        continue
                    break
                mo = re.match(r"^\d+\.\s+(.*)$", cur) if lkind == "ol" else None
                if (lkind == "ul" and cur.startswith("- ")) or mo:
                    items.append([mo.group(1) if mo else cur[2:]])
                elif cur.startswith(" "):
                    items[-1].append(cur.strip())
                else:
                    break
                i += 1
            h.append("<%s>%s</%s>" % (lkind, "".join("<li>%s</li>" % item_html(it, src) for it in items), lkind))
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("> ", "|", "<!--")) \
                    and not lines[i].startswith(("#", "- ")) and not re.match(r"^\d+\.\s", lines[i]):
                para.append(lines[i].strip())
                i += 1
            text = " ".join(para)
            if re.match(r"^(Check your answer|Answers):", text):
                h.append('<details class="answer"><summary>Show the answer</summary><p>%s</p></details>'
                         % inline(text, src))
                continue
            cls = ' class="check"' if re.match(r"^(\*\*)?Check:", text) else ""
            h.append("<p%s>%s</p>" % (cls, inline(text, src)))
    return "\n".join(h)


def nav_title(md):
    t = title_of(md).replace("How to: ", "")
    return t[:1].upper() + t[1:]


def training_of(md):
    for t in TRAININGS:
        if md.startswith(t["folder"] + "/"):
            return t
    return None


def in_training(t, f):
    return t["folder"] + "/" + f


def recipes_of(t):
    index = in_training(t, "how-to/README.md")
    if index not in FILES:
        return []
    found = []
    for r in read(index):
        m = re.search(r"\]\(([^)]+\.md)\)", r) if r.startswith("| ") else None
        if m and in_training(t, "how-to/" + m.group(1)) in FILES:
            found.append(in_training(t, "how-to/" + m.group(1)))
    return found + [f for f in FILES if f.startswith(in_training(t, "how-to/")) and f != index and f not in found]


for _t in TRAININGS:
    _t["readme"] = in_training(_t, "README.md")
    _t["units"] = [in_training(_t, f) for f, _, _ in _t["path"]]
    _t["recipes"] = recipes_of(_t)
    _t["seq"] = [_t["readme"]] + _t["before"] + _t["units"]
UNITS = {}
for _t in TRAININGS:
    for _n, (_f, _, _time) in enumerate(_t["path"], 1):
        UNITS[in_training(_t, _f)] = (_t, _n, _time)


def menu_for(md):
    t = training_of(md)
    if t and t["path"]:
        groups = [("Home", True, [("README.md", "All trainings", ""), (t["readme"], "Overview", "")]
                   + [(f, nav_title(f), "") for f in t["before"]]),
                  ("The path", True, [(u, "%d. %s" % (n, p[1]), "")
                                      for n, (u, p) in enumerate(zip(t["units"], t["path"]), 1)])]
        if t["recipes"]:
            groups.append(("More practice", False, [(in_training(t, "how-to/README.md"), "All recipes", "")]
                           + [(r, nav_title(r), "") for r in t["recipes"]]))
    else:
        groups = [("Home", True, [("README.md", "All trainings", "")]),
                  ("Trainings", True, [(x["readme"], x["name"] + ("" if x["path"] else " (coming later)"), "")
                                       for x in TRAININGS])]
    return groups + MENU_AFTER


ORDER = ["README.md"]
for _t in TRAININGS:
    _index = [in_training(_t, "how-to/README.md")] if _t["recipes"] else []
    for _f in [_t["readme"]] + _t["before"] + _t["units"] + _index + _t["recipes"]:
        if _f not in ORDER:
            ORDER.append(_f)
for _, _, _items in MENU_AFTER:
    for _f, _, _ in _items:
        if _f not in ORDER:
            ORDER.append(_f)
missing = [f for f in FILES if f not in ORDER]
if missing:
    sys.exit("Not in any menu, so learners cannot reach them: %s. Add each to a training's path or "
             "'before' list in TRAININGS, to MENU_AFTER, or to a training's recipe table." % ", ".join(missing))
absent = [f for f in ORDER if f not in FILES]
if absent:
    sys.exit("In a menu but not found as learner pages: %s" % ", ".join(absent))


def site_nav(md):
    groups = []
    for label, open_default, items in menu_for(md):
        lis, here = [], False
        for target, text, anchor in items:
            href = rel(md, out_name(target)) + ("#" + anchor if anchor else "")
            cur = ' aria-current="page"' if target == md and not anchor else ""
            here = here or bool(cur)
            lis.append('<li><a href="%s"%s>%s</a></li>' % (html.escape(href), cur, html.escape(text)))
        is_open = " open" if (open_default or here) else ""
        groups.append('<li><details%s><summary class="grp">%s</summary><ul>%s</ul></details></li>'
                      % (is_open, html.escape(label), "".join(lis)))
    return '<nav id="side" class="side" aria-label="Contents"><ul>%s</ul></nav>' % "".join(groups)


def inline_toc(rest):
    heads = re.findall(r'<h([23]) id="([^"]+)">(.*?)</h\1>', rest)
    if len(heads) < 3:
        return ""
    lis = "".join('<li class="l%s"><a href="#%s">%s</a></li>' % (lv, i, re.sub(r"<[^>]+>", "", t)) for lv, i, t in heads)
    return '<details class="toc-inline"><summary>On this page</summary><ul>%s</ul></details>' % lis


def page_toc(rest):
    heads = re.findall(r'<h([23]) id="([^"]+)">(.*?)</h\1>', rest)
    if len(heads) < 3:
        return ""
    lis = "".join('<li class="l%s"><a href="#%s">%s</a></li>' % (lv, i, re.sub(r"<[^>]+>", "", t)) for lv, i, t in heads)
    return '<aside class="toc" aria-label="On this page"><p class="toch">On this page</p><ul>%s</ul></aside>' % lis


def unit_steps(md):
    """The step ids a unit page tracks; a unit with no numbered steps is tracked as one step, 'unit'."""
    heads = re.findall(r'<h([23]) id="([^"]+)">(.*?)</h\1>', render(read(md)[1:], md))
    steps = [(i, re.sub(r"^\d+( of \d+)?\.\s*", "", re.sub(r"<[^>]+>", "", t)))
             for _, i, t in heads if re.match(r"\d", re.sub(r"<[^>]+>", "", t))]
    return steps or [("unit", nav_title(md))]


def list_items(md, heading, numbered):
    """A README's list under a heading: (target page in the kit, link text, the text after the link)."""
    lines = read(md)
    k = lines.index(heading) + 1
    mark = r"\d+\." if numbered else "-"
    items = []
    for ln in lines[k:]:
        if ln.startswith("## "):
            break
        m = re.match(r"^%s\s+\[([^\]]+)\]\(([^)]+)\):?\s*(.*)$" % mark, ln)
        if m:
            target = os.path.normpath(os.path.join(os.path.dirname(md), m.group(2))).replace("\\", "/")
            items.append([target, m.group(1), m.group(3)])
        elif ln.startswith("  ") and items:
            items[-1][2] += " " + ln.strip()
    return items


def course_panel(t, md):
    first, first_time = t["units"][0], t["path"][0][2]
    n_units = len(t["units"])
    if t["before"]:
        start, note = t["before"][0], "It begins with %s, then unit 1" % html.escape(nav_title(t["before"][0]))
    else:
        start, note = first, "Unit 1 of %d, %s" % (n_units, html.escape(first_time))
    return ('<section class="course" aria-label="Your progress">'
            '<p class="meta">%s &middot; %d units &middot; %s &middot; at your own pace</p>'
            '<div class="overall"><div class="bar" aria-hidden="true"><span id="bar"></span></div>'
            '<span id="overall">0 of %d units done</span></div>'
            '<p class="cta"><a class="btn" id="cta" href="%s">Start the training</a>'
            '<span id="cta-note">%s</span></p></section>'
            % (html.escape(t["level"]), n_units, html.escape(t["time"]), n_units, rel(md, out_name(start)), note))


def unit_cards(t, md):
    lis = []
    for n, (target, title, outcome) in enumerate(list_items(md, "## The path", True), 1):
        steps = unit_steps(target)
        text = outcome[:1].upper() + outcome[1:]
        lis.append('<li class="unitcard" data-steps="%s" data-labels="%s">'
                   '<span class="un">Unit %d</span><a href="%s">%s</a><p class="uo">%s</p>'
                   '<p class="us">Not started</p></li>'
                   % (html.escape(json.dumps([s[0] for s in steps])), html.escape(json.dumps([s[1] for s in steps])),
                      n, html.escape(rel(md, out_name(target))), html.escape(title), inline(text, md)))
    return '<ol class="units">%s</ol>' % "".join(lis)


def training_cards():
    lis = []
    for target, title, text in list_items("README.md", "## The trainings", False):
        t = training_of(target)
        ready = bool(t and t["path"])
        label = html.escape(t["level"] or "Available") if ready else ""
        meta = ('<p class="um">%d units &middot; %s</p>' % (len(t["units"]), html.escape(t["time"]))) if ready else ""
        status = '<p class="us">Not started</p>' if ready else ""
        lis.append('<li class="unitcard traincard" data-training="%s">%s<a href="%s">%s</a>'
                   '<p class="uo">%s</p>%s%s</li>'
                   % (html.escape(t["folder"] if t else ""), '<span class="un">%s</span>' % label if label else "",
                      html.escape(out_name(target)), html.escape(title),
                      inline(text[:1].upper() + text[1:], "README.md"), meta, status))
    return '<ul class="units">%s</ul>' % "".join(lis)


def pager(md):
    t = training_of(md)
    links = []
    if md == "README.md":
        first = next((x for x in TRAININGS if x["path"]), None)
        if first:
            links.append('<a class="next" href="%s"><span>Start with</span>%s</a>'
                         % (out_name(first["readme"]), html.escape(first["name"])))
        return '<nav class="pager" aria-label="Previous and next page">%s</nav>' % "".join(links)
    seq = None
    t = t or next((x for x in TRAININGS if md in x["before"]), None)
    if t and md in t["seq"] and t["path"]:
        seq = t["seq"]
    elif t and md.startswith(in_training(t, "how-to/")):
        seq = [in_training(t, "how-to/README.md")] + t["recipes"]
    if seq is None:
        links.append('<a class="prev" href="%s"><span>Back to</span>All trainings</a>' % rel(md, "README.html"))
    else:
        k = seq.index(md)
        if k > 0:
            p = seq[k - 1]
            links.append('<a class="prev" href="%s"><span>Previous</span>%s</a>' % (rel(md, out_name(p)), html.escape(nav_title(p))))
        elif md == t["readme"]:
            links.append('<a class="prev" href="%s"><span>Back to</span>All trainings</a>' % rel(md, "README.html"))
        if k + 1 < len(seq):
            n = seq[k + 1]
            links.append('<a class="next" href="%s"><span>Next</span>%s</a>' % (rel(md, out_name(n)), html.escape(nav_title(n))))
    return '<nav class="pager" aria-label="Previous and next page">%s</nav>' % "".join(links)


def how_to_use():
    return ('<aside class="howto" aria-label="How to use a prompt"><b>Using a prompt:</b> click <b>Copy</b>, '
            'click in the chat box in VS Code, press <kbd>Ctrl</kbd>+<kbd>V</kbd>, change any '
            'blank such as <span class="ph">&lt;your folder&gt;</span> to your own, then press <kbd>Enter</kbd>.</aside>')


def folder_box():
    return ('<div class="setup"><label for="folder">Optional: the name of your own folder for this page, '
            'the one you added to VS Code (not the training folder). The prompts on this page will use it.</label>'
            '<input id="folder" placeholder="your folder&rsquo;s name" autocomplete="off"></div>')


def search_entries(md, title, rest):
    entries = []
    parts = re.split(r'(<h[23] id="[^"]+">.*?</h[23]>)', rest)
    anchor, section = "", ""
    for part in parts:
        m = re.match(r'<h[23] id="([^"]+)">(.*?)</h[23]>', part)
        if m:
            anchor, section = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
            continue
        text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", part))).strip()
        if text or section:
            entries.append({"u": out_name(md) + ("#" + anchor if anchor else ""), "t": title,
                            "s": html.unescape(section), "x": text})
    return entries


TEMPLATE = """<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.
     Source: {source}
     Build: python maintaining/build_pages.py, from the kit's folder (see maintaining/README.md)
-->
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{tabtitle}</title>
<style>
{css}
</style></head><body data-root="{root}" data-training="{tfolder}">
<a class="skip" href="#main">Skip to the page</a>
<header class="top{incourse}">
<button id="menu" class="menu" type="button" aria-controls="side" aria-expanded="false">Menu</button>
<a class="brand prog" href="{home}">{program}</a>{course}
<a class="status" id="status" href="{home}" hidden><span class="sbar" aria-hidden="true"><span id="sbar"></span></span><span id="stext" class="long"></span><span id="sshort" class="short"></span></a>
<div class="search" role="search"><label class="sr" for="q">Search the trainings</label>
<input id="q" type="search" placeholder="Search" autocomplete="off" aria-controls="results">
<ul id="results" class="results" hidden></ul></div>
</header>
<div class="layout">
{nav}
<main id="main" data-steps="{steps}" data-page="{page}" data-stuck-from="{stuckfrom}">
{body}
{pager}
</main>
{toc}
</div>
<div id="say" class="sr" aria-live="polite"></div>
<script src="{root}search-index.js"></script>
<script>
{js}
</script></body></html>
"""

INDEX = []


NO_LINK = ("a", "code", "h1", "h2", "h3", "h4", "summary", "kbd", "button", "label")


def glossary_defs():
    defs = {}
    for l in read("glossary.md"):
        if l.startswith("| ") and not l.startswith("| Word") and not l.startswith("|---"):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if len(cells) >= 2:
                defs[slug(re.sub(r"[`*]", "", cells[0]))] = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cells[1]).replace("`", "")
    return defs


GLOSSARY_DEFS = glossary_defs()


def link_glossary(md, rest):
    """Link the first use of each glossary term on a page, outside headings, links, code and prompts."""
    if md == "glossary.md":
        return rest
    href = rel(md, "glossary.html")
    todo = {t.lower(): t for t in GLOSSARY_TERMS}
    parts = re.split(r"(<[^>]+>)", rest)
    stack = []
    for n, part in enumerate(parts):
        if part.startswith("<"):
            m = re.match(r"<(/?)([a-z0-9]+)([^>]*)>", part)
            if not m or part.endswith("/>"):
                continue
            closing, tag, attrs = m.groups()
            if closing:
                if tag in stack:
                    while stack and stack.pop() != tag:
                        pass
            else:
                blocked = tag in NO_LINK or 'class="t"' in attrs or 'class="ph' in attrs or 'class="org"' in attrs \
                    or 'class="lab"' in attrs
                if blocked or stack:
                    stack.append(tag)
            continue
        if stack or not todo:
            continue
        masked = part
        for ui in UI_LABELS:
            masked = masked.replace(ui, "\0" * len(ui))
        for key in sorted(list(todo), key=len, reverse=True):
            mo = re.search(r"(?<![\w-])(%s)(?![\w-])" % re.escape(key), masked, flags=re.I)
            if mo and key in todo:
                term = todo.pop(key)
                part = part[:mo.start()] + '<a class="gl" href="%s#%s" title="%s">%s</a>' % (
                    href, slug(term), html.escape(GLOSSARY_DEFS.get(slug(term), "Glossary")), mo.group(1)) + part[mo.end():]
                break
        parts[n] = part
    return "".join(parts)


def write(md):
    lines = read(md)
    title = title_of(md)
    rest = link_glossary(md, render(lines[1:], md))
    INDEX.extend(search_entries(md, title, rest))
    if "data-folder" in rest:
        f = rest.rfind('<div class="prompt', 0, rest.index("data-folder"))
        rest = rest[:f] + folder_box() + rest[f:]
    k = [x for x in (rest.find('<div class="prompt"'), rest.find('<div class="prompt tutor"'),
                     rest.find('<div class="setup"')) if x >= 0]
    if k:
        rest = rest[:min(k)] + how_to_use() + rest[min(k):]
    t = training_of(md)
    if md == "README.md":
        a = rest.index('<h2 id="the-trainings">')
        b = rest.index("<h2", a + 1)
        rest = rest[:a] + '<h2 id="the-trainings">The trainings</h2>\n' + training_cards() + "\n" + rest[b:]
    elif t and t["path"] and md == t["readme"]:
        a = rest.index('<h2 id="the-path">')
        b = rest.index("<h2", a + 1)
        rest = rest[:a] + '<h2 id="the-path">The path</h2>\n' + unit_cards(t, md) + "\n" + rest[b:]
        k = rest.find("<h2")
        rest = rest[:k] + course_panel(t, md) + "\n" + rest[k:]
    unit = ""
    if md in UNITS:
        _, n, time = UNITS[md]
        unit = '<p class="unit" data-unit="%d">Unit %d of %d &middot; %s</p>\n' % (n, n, len(t["units"]), html.escape(time))
    body = unit + "<h1>%s</h1>\n" % inline(title, md) + inline_toc(rest) + rest
    path = os.path.join(OUT, out_name(md))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    root = rel(md, "x")[:-1]
    course = ('<span class="sep" aria-hidden="true">/</span><a class="brand crs" href="%s">%s</a>'
              % (rel(md, out_name(t["readme"])), html.escape(t["name"]))) if t else ""
    doc = TEMPLATE.format(source=md, title=html.escape(title), root=root, program=html.escape(PROGRAM_NAME),
                          tabtitle=html.escape(title if title.startswith(t["name"] if t else PROGRAM_NAME)
                                               else "%s - %s" % (title, t["name"] if t else PROGRAM_NAME)),
                          course=course,
                          incourse=" incourse" if t else "", tfolder=html.escape(t["folder"] if t else ""),
                          home=rel(md, "README.html"), nav=site_nav(md), body=body,
                          pager=pager(md), toc=page_toc(rest), css=CSS, js=JS,
                          steps="1" if md in UNITS else "0", page=html.escape(nav_title(md)),
                          stuckfrom=str(t["stuck_from"].get(md[len(t["folder"]) + 1:], 1) if t else 1))
    io.open(path, "w", encoding="utf-8", newline="\n").write(doc)
    return body.count('class="prompt'), body.count("prompt frame")


def write_blanks():
    """List every marked blank in the training, so presenters know what to fill before sending it."""
    rows = []
    for root, _, files in os.walk(KIT):
        for f in sorted(files):
            md = os.path.relpath(os.path.join(root, f), KIT).replace("\\", "/")
            if not md.endswith(".md") or md.startswith(("maintaining/", OUT_DIR + "/")) or md == "facilitator/BLANKS.md":
                continue
            section = ""
            for n, line in enumerate(read(md), 1):
                if line.startswith("#"):
                    section = line.lstrip("#").strip()
                for m in BLANK.finditer(line):
                    rows.append((md, n, section, m.group(0)))
    rows.sort()
    out = ["# Blanks still to fill", "",
           "Generated by `maintaining/build_pages.py` on every build; do not edit. Each is a place where the",
           "training says `[YOUR ORGANIZATION: ...]` (your organization supplies the answer) or",
           "`[TO BE WRITTEN: ...]` (the training's authors have not written it yet). Fill them in the markdown",
           "and build again; this list shrinks as you go.", "",
           "| File | Line | Section | Blank |", "|---|---|---|---|"]
    out += ["| `%s` | %d | %s | %s |" % (md, n, s.replace("|", "/"), b.replace("|", "/")) for md, n, s, b in rows]
    io.open(os.path.join(KIT, "facilitator", "BLANKS.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    return len(rows)


def main():
    listed = [x for x, _, _ in list_items("README.md", "## The trainings", False)]
    if listed != [t["readme"] for t in TRAININGS]:
        sys.exit("The list under '## The trainings' in README.md (%s) does not match TRAININGS in build_pages.py (%s)."
                 % (", ".join(listed), ", ".join(t["readme"] for t in TRAININGS)))
    for t in TRAININGS:
        if not t["path"]:
            continue
        listed = [x for x, _, _ in list_items(t["readme"], "## The path", True)]
        if listed != t["units"]:
            sys.exit("The list under '## The path' in %s (%s) does not match its path in TRAININGS (%s)."
                     % (t["readme"], ", ".join(listed), ", ".join(t["units"])))
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    total = 0
    for md in ORDER:
        n, frames = write(md)
        total += n
        print("%-52s %2d prompts (%d to write)" % (out_name(md), n, frames))
    trainings = [{"f": t["folder"], "name": t["name"], "readme": out_name(t["readme"]),
                  "units": [{"u": out_name(u), "n": n, "ids": [s[0] for s in unit_steps(u)]}
                            for n, u in enumerate(t["units"], 1)]} for t in TRAININGS]
    io.open(os.path.join(OUT, "search-index.js"), "w", encoding="utf-8", newline="\n").write(
        "window.KIT_INDEX=" + json.dumps(INDEX, ensure_ascii=False) + ";\n"
        "window.KIT_TRAININGS=" + json.dumps(trainings, ensure_ascii=False) + ";\n")
    print("total prompts: %d; search entries: %d" % (total, len(INDEX)))
    print("blanks still to fill: %d, listed in facilitator/BLANKS.md" % write_blanks())
    failed = False
    for checker in ("check_text.py", "check_structure.py"):
        r = subprocess.run([sys.executable, os.path.join(HERE, checker), KIT, OUT], capture_output=True, text=True)
        problems = [l for l in r.stdout.splitlines() if not l.startswith("OK")]
        print("\n".join(problems))
        failed = failed or r.returncode != 0 or not problems or not problems[-1].endswith(": 0")
    if failed:
        sys.exit("CHECKS FAILED: fix the markdown (never the pages) and build again.")
    print("All checks passed.")


CSS = """:root{--bg:#fdfcfa;--surface:#fff;--side:#f6f4f0;--ink:#1b1b1a;--ink2:#54524e;--ink3:#6f6c67;--rule:#e2ded7;
--field:#8a8782;--code:#f3f1ec;--ok:#2f6f43;--okink:#fff;--ph:#fbe9c6;--phline:#a8741a;--org:#fff7e6;--focus:#1f5fbf;
--tutor:#2f5f8a;--accent:#1f5fbf;--cur:#e7eefb}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--bg:#17171a;--surface:#1f1f23;--side:#1b1b1f;--ink:#ececea;--ink2:#b3b1ac;--ink3:#9a978f;--rule:#32323a;--field:#8a8790;
--code:#26262c;--ok:#6fbe8a;--okink:#101012;--ph:#4a3d1f;--phline:#e0b25e;--org:#2b2518;--focus:#8ab4ff;--tutor:#8ab4e0;
--accent:#8ab4ff;--cur:#23304a}}
:root[data-theme="dark"]{--bg:#17171a;--surface:#1f1f23;--side:#1b1b1f;--ink:#ececea;--ink2:#b3b1ac;--ink3:#9a978f;
--rule:#32323a;--field:#8a8790;--code:#26262c;--ok:#6fbe8a;--okink:#101012;--ph:#4a3d1f;--phline:#e0b25e;--org:#2b2518;
--focus:#8ab4ff;--tutor:#8ab4e0;--accent:#8ab4ff;--cur:#23304a}
*{box-sizing:border-box}
html{scroll-padding-top:72px}
body{margin:0;background:var(--bg);color:var(--ink);font:1rem/1.6 -apple-system,Segoe UI,system-ui,sans-serif}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
a{color:var(--accent)}
.skip{position:absolute;left:-999px;top:8px;background:var(--surface);padding:6px 10px;z-index:30}
.skip:focus{left:8px}
.top{position:sticky;top:0;z-index:20;height:56px;display:flex;align-items:center;gap:14px;padding:0 16px;
background:var(--surface);border-bottom:1px solid var(--rule)}
.brand{font-weight:700;font-size:1.05rem;color:var(--ink);text-decoration:none;white-space:nowrap}
.menu{display:none;font:inherit;font-size:.9rem;padding:5px 12px;border:1px solid var(--field);border-radius:4px;
background:var(--surface);color:var(--ink);cursor:pointer}
.search{position:relative;margin-left:auto;width:min(340px,50vw)}
.search input{width:100%;padding:7px 10px;font:inherit;font-size:.9rem;border:1px solid var(--field);border-radius:6px;
background:var(--bg);color:var(--ink)}
.results{position:absolute;right:0;top:42px;width:min(460px,92vw);max-height:70vh;overflow:auto;margin:0;padding:6px;
list-style:none;background:var(--surface);border:1px solid var(--rule);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.15)}
.results li a{display:block;padding:7px 9px;border-radius:5px;color:var(--ink);text-decoration:none}
.results li a:hover,.results li a:focus{background:var(--cur)}
.results .rt{font-weight:600;font-size:.9rem}
.results .rs{font-size:.8rem;color:var(--ink2)}
.results .none{padding:8px 9px;color:var(--ink2);font-size:.9rem}
.layout{display:grid;grid-template-columns:270px minmax(0,1fr) 230px;max-width:1440px;margin:0 auto}
.side{position:sticky;top:56px;align-self:start;height:calc(100vh - 56px);overflow:auto;padding:18px 12px 40px 16px;
background:var(--side);border-right:1px solid var(--rule);font-size:.92rem}
.side ul{list-style:none;margin:0;padding:0}
.side > ul > li{margin-bottom:16px}
.side .grp{display:block;font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);
padding:2px 8px 4px;cursor:pointer;list-style:none}
.side .grp::-webkit-details-marker{display:none}
.side .grp::before{content:"\\25B8";display:inline-block;width:1em;transition:transform .15s}
.side details[open] > .grp::before{transform:rotate(90deg)}
.side a{display:block;padding:4px 8px;border-radius:5px;color:var(--ink);text-decoration:none;line-height:1.35}
.side a:hover{background:var(--cur)}
.side a[aria-current]{background:var(--cur);font-weight:600;box-shadow:inset 3px 0 0 var(--accent)}
main{padding:8px 40px 60px;max-width:820px;width:100%;justify-self:center}
.toc{position:sticky;top:56px;align-self:start;max-height:calc(100vh - 56px);overflow:auto;padding:24px 16px;font-size:.85rem}
.toc .toch{margin:0 0 6px;font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3)}
.toc ul{list-style:none;margin:0;padding:0;border-left:1px solid var(--rule)}
.toc li a{display:block;padding:3px 10px;color:var(--ink2);text-decoration:none;line-height:1.35}
.toc li.l3 a{padding-left:22px}
.toc li a:hover{color:var(--ink)}
h1{font-size:1.9rem;margin:24px 0 12px;letter-spacing:-.01em;line-height:1.25}
h2{font-size:1.35rem;margin:36px 0 8px;padding-bottom:5px;border-bottom:1px solid var(--rule)}
h3{font-size:1.1rem;margin:26px 0 6px}
p{margin:10px 0}
ul,ol{padding-left:24px}li{margin:6px 0}.gap{height:8px}
code{background:var(--code);border-radius:4px;padding:1px 5px;font-size:.875em;font-family:ui-monospace,Consolas,monospace;overflow-wrap:anywhere}
kbd{border:1px solid var(--field);border-radius:3px;padding:0 4px;font-size:.85em;font-family:inherit}
.org{background:var(--org);border:1px dashed var(--phline);border-radius:4px;padding:1px 6px;font-size:.875em;color:var(--ink)}
.howto{margin:12px 0;padding:9px 12px;border-left:4px solid var(--phline);background:var(--surface);font-size:.95rem}
.setup{margin:12px 0;padding:10px 12px;background:var(--surface);border:1px solid var(--rule);border-radius:6px}
.setup label{display:block;font-size:.875rem;color:var(--ink2);margin-bottom:5px}
.setup input{width:100%;padding:7px 9px;font:inherit;border:1px solid var(--field);border-radius:4px;background:var(--bg);color:var(--ink)}
.prompt{margin:10px 0;background:var(--code);border-left:4px solid var(--field);border-radius:4px;padding:10px 12px;
display:flex;flex-wrap:wrap;gap:8px 12px;align-items:flex-start}
.prompt .t{flex:1 1 260px;white-space:pre-wrap;overflow-wrap:anywhere}
.prompt .lab{flex-basis:100%;margin:0;font-size:.8rem;font-weight:600;color:var(--ink2)}
.prompt.tutor{border-left-color:var(--tutor)}
.prompt.orgprompt{background:var(--org);border-left:4px dashed var(--phline)}
.prompt.frame{background:none;border:1px dashed var(--field);border-left:4px dashed var(--field)}
.prompt .after{flex-basis:100%;margin:0;font-size:.875rem;color:var(--ink2)}
.ph{background:var(--ph);border-bottom:2px dashed var(--phline);border-radius:3px;padding:0 2px}
.ph.filled{background:none;border-bottom:2px solid var(--phline)}
button.copy{font:inherit;font-size:.85rem;padding:3px 12px;cursor:pointer;border:1px solid var(--field);
background:var(--surface);color:var(--ink);border-radius:4px}
button.copy:hover{border-color:var(--ink)}
button.copy.ok{background:var(--ok);border-color:var(--ok);color:var(--okink)}
.tw{overflow-x:auto;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.95rem}
th,td{border:1px solid var(--rule);padding:6px 9px;text-align:left;vertical-align:top}
thead th{background:var(--surface)}
tbody th{font-weight:600}
.pager{display:flex;gap:12px;margin-top:48px}
.pager a{flex:1;display:block;padding:12px 14px;border:1px solid var(--rule);border-radius:8px;text-decoration:none;color:var(--ink)}
.pager a:hover{border-color:var(--accent)}
.pager a span{display:block;font-size:.8rem;color:var(--ink2)}
.pager .next{text-align:right;margin-left:auto}
.progress{margin:-4px 0 14px;font-size:.9rem;color:var(--ink2)}
p.check{padding:9px 12px;border-left:4px solid var(--ok);background:var(--surface);border-radius:4px}
.cta{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:22px 0 8px}
.cta .btn{display:inline-block;padding:10px 20px;border-radius:6px;background:var(--accent);color:var(--bg);
font-weight:600;text-decoration:none}
.cta .btn:hover{filter:brightness(1.1)}
.cta span{color:var(--ink2);font-size:.9rem}
button.mark{display:block;margin:16px 0 4px;font:inherit;font-size:.85rem;padding:5px 12px;cursor:pointer;
border:1px solid var(--field);border-radius:4px;background:var(--surface);color:var(--ink)}
button.mark[aria-pressed=true]{background:var(--ok);border-color:var(--ok);color:var(--okink)}
h2.done::after,h3.done::after{content:" \\2713";color:var(--ok)}
.toc a.done::before{content:"\\2713 ";color:var(--ok)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.unit{margin:22px 0 -14px;font-size:.85rem;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:.05em}
.carried{margin:6px 0 0;font-size:.8rem;color:var(--ink2)}
.steprow{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:16px 0 4px}
.steprow button.mark{margin:0}
button.stuck{font:inherit;font-size:.8rem;padding:4px 10px;cursor:pointer;border:1px dashed var(--field);border-radius:4px;
background:none;color:var(--ink2)}
button.stuck.ok{border-style:solid;border-color:var(--ok);color:var(--ok)}
.sidemark{float:right;font-size:.75rem;color:var(--ok);font-weight:600;margin-left:6px}
.toc-inline{display:none;margin:4px 0 14px;padding:6px 12px;border:1px solid var(--rule);border-radius:6px;background:var(--surface)}
.toc-inline summary{cursor:pointer;font-weight:600;font-size:.9rem}
.toc-inline ul{list-style:none;margin:6px 0 2px;padding:0}.toc-inline li{margin:3px 0}
.toc-inline li.l3{padding-left:14px}.toc-inline a{text-decoration:none}
.toc a.here{color:var(--ink);font-weight:600;box-shadow:inset 2px 0 0 var(--accent)}
details.answer{margin:10px 0;padding:8px 12px;border:1px solid var(--rule);border-radius:6px;background:var(--surface)}
details.answer summary{cursor:pointer;font-weight:600;color:var(--accent)}
.course{margin:20px 0 8px;padding:14px 18px 6px;border:1px solid var(--rule);border-radius:10px;background:var(--surface)}
.course .meta{margin:0;font-size:.9rem;color:var(--ink2)}
.overall{display:flex;align-items:center;gap:12px;margin:10px 0 0;font-size:.9rem;font-weight:600}
#overall{white-space:nowrap}
.bar{flex:0 1 260px;min-width:80px;height:8px;border-radius:4px;background:var(--rule);overflow:hidden}
.bar span{display:block;height:100%;width:0;background:var(--ok)}
.course .cta{margin:14px 0 10px}
.units{list-style:none;padding:0;margin:12px 0;display:grid;gap:10px}
.unitcard{position:relative;margin:0;padding:12px 16px;border:1px solid var(--rule);border-left:4px solid var(--rule);
border-radius:8px;background:var(--surface)}
.unitcard:hover{border-color:var(--accent)}
.unitcard a{font-weight:600;font-size:1.05rem;text-decoration:none}
.unitcard a::after{content:"";position:absolute;inset:0}
.unitcard .un{display:block;font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3)}
.unitcard .uo{margin:4px 0;color:var(--ink2);font-size:.95rem}
.unitcard .us{margin:0;font-size:.85rem;font-weight:600;color:var(--ink3)}
.unitcard.going{border-left-color:var(--accent)}.unitcard.going .us{color:var(--accent)}
.unitcard.done{border-left-color:var(--ok)}.unitcard.done .us{color:var(--ok)}
.status{display:flex;align-items:center;gap:8px;padding:4px 8px;border-radius:6px;font-size:.82rem;font-weight:600;
color:var(--ink2);text-decoration:none;white-space:nowrap}
.status:hover{background:var(--cur);color:var(--ink)}
.status[hidden]{display:none}
.sbar{display:block;width:90px;height:6px;border-radius:3px;background:var(--rule);overflow:hidden}
#sbar{display:block;height:100%;width:0;background:var(--ok)}
.status .short{display:none}
.incourse .brand.prog{font-weight:400;color:var(--ink2)}
.top .sep{margin:0 -6px;color:var(--ink3)}
.unitcard .um{margin:2px 0 0;font-size:.85rem;color:var(--ink2)}
@media (max-width:1180px){.layout{grid-template-columns:250px minmax(0,1fr)}.toc{display:none}.toc-inline{display:block}}
@media (max-width:900px){.layout{grid-template-columns:210px minmax(0,1fr)}.side{font-size:.86rem;padding-left:10px}
main{padding:8px 22px 48px}}
@media (max-width:680px){
.menu{display:inline-block}
.layout{grid-template-columns:minmax(0,1fr)}
.side{position:fixed;left:0;top:56px;z-index:15;width:min(300px,85vw);transform:translateX(-105%);visibility:hidden;
transition:transform .2s,visibility .2s;box-shadow:4px 0 16px rgba(0,0,0,.15)}
body.nav-open .side{transform:none;visibility:visible}
main{padding:8px 16px 48px}
.incourse .brand.prog,.incourse .sep{display:none}
.status .long{display:none}.status .short{display:inline}.sbar{width:36px}.top{gap:8px}.status{padding:4px}
.search{width:auto;flex:1}
}
@media (max-width:420px){.brand{display:none}}
@media (forced-colors:active){.ph{border-bottom:2px dashed CanvasText}.org{border:1px dashed CanvasText}
.side a[aria-current]{outline:2px solid CanvasText}}"""

JS = r"""(function(){
var FK="kit.folder";
function lget(k,d){try{var v=localStorage.getItem(k);return v===null?d:v;}catch(e){return d;}}
function lput(k,v){try{localStorage.setItem(k,v);}catch(e){}}
var fin=document.getElementById("folder"), say=document.getElementById("say");
function paint(){
  var f=fin?(fin.value||"").trim():"";
  document.querySelectorAll(".ph[data-folder]").forEach(function(p){
    p.textContent=f||"<your folder>"; p.classList.toggle("filled",!!f);});
}
if(fin){
  fin.value=lget(FK,"");
  if(fin.value){var n=document.createElement("p");n.className="carried";
    n.textContent="Filled in from an earlier page. Change it if this page is about a different folder.";
    fin.insertAdjacentElement("afterend",n);}
  fin.addEventListener("input",function(){lput(FK,fin.value);paint();});
}
paint();
function copyText(b,txt,open,after){
  function done(ok){
    b.classList.toggle("ok",ok); var old=b.getAttribute("data-label")||b.textContent; b.setAttribute("data-label",old);
    b.textContent=ok?"Copied":"Copy failed";
    if(after) after.hidden=!(ok&&open);
    say.textContent=ok?(open?"Copied. Change the highlighted part after you paste.":"Copied."):"Copy failed. Select the text and press Ctrl+C.";
    setTimeout(function(){b.classList.remove("ok");b.textContent=old;},2500);
  }
  function fallback(){
    var ta=document.createElement("textarea");ta.value=txt;ta.setAttribute("readonly","");
    ta.style.position="fixed";ta.style.opacity="0";document.body.appendChild(ta);ta.select();
    var ok=false;try{ok=document.execCommand("copy");}catch(x){}
    document.body.removeChild(ta);b.focus();done(ok);
  }
  if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(function(){done(true);},fallback);
  else fallback();
}
document.addEventListener("click",function(e){
  var b=e.target.closest("button.copy"); if(!b) return;
  var box=b.parentNode;
  var open=[].some.call(box.querySelectorAll(".ph"),function(p){return !p.classList.contains("filled");});
  copyText(b,box.querySelector(".t").textContent,open,box.querySelector(".after"));
});
var main=document.getElementById("main"), page=main.getAttribute("data-page");
var PK="kit.done."+location.pathname, done={};
try{done=JSON.parse(lget(PK,"{}"))||{};}catch(e){}
var heads=[].slice.call(main.querySelectorAll("h2[id],h3[id]"));
var steps=main.getAttribute("data-steps")==="1"?heads.filter(function(h){return /^\d/.test(h.textContent);}):[];
if(steps.length){
  var prog=document.createElement("p"); prog.className="progress"; prog.setAttribute("aria-live","polite");
  main.querySelector("h1").insertAdjacentElement("afterend",prog);
  var paintProgress=function(){
    var n=steps.filter(function(h){return done[h.id];}).length;
    prog.textContent=n+" of "+steps.length+" steps done";
    steps.forEach(function(h){
      var a=document.querySelector('.toc a[href="#'+h.id+'"]'); if(a) a.classList.toggle("done",!!done[h.id]);
      h.classList.toggle("done",!!done[h.id]);
    });
  };
  steps.forEach(function(h){
    var lv=+h.tagName[1], next=heads.slice(heads.indexOf(h)+1).filter(function(x){return +x.tagName[1]<=lv;})[0];
    var row=document.createElement("div"); row.className="steprow";
    var num=(h.textContent.match(/^\d+/)||[""])[0];
    var b=document.createElement("button"); b.type="button"; b.className="mark"; b.setAttribute("aria-label","Mark step "+num+" done");
    var set=function(){b.setAttribute("aria-pressed",String(!!done[h.id]));b.textContent=done[h.id]?"✓ Step done":"Mark this step done";};
    set();
    b.addEventListener("click",function(){done[h.id]=!done[h.id];lput(PK,JSON.stringify(done));set();paintProgress();paintStatus();});
    var s=document.createElement("button"); s.type="button"; s.className="stuck";
    s.textContent="Stuck on this step? Copy a question for the assistant";
    s.setAttribute("aria-label","Stuck on step "+num+"? Copy a question for the assistant");
    s.addEventListener("click",function(){
      copyText(s,"I am on step "+num+" of \""+page+"\" in the training folder. In plain words, what does it ask me to do, and what should I see? Do not do it for me.",false,null);
    });
    row.appendChild(b);
    if(+num>=+(main.getAttribute("data-stuck-from")||1)) row.appendChild(s);
    if(next) next.insertAdjacentElement("beforebegin",row); else main.querySelector(".pager").insertAdjacentElement("beforebegin",row);
  });
  paintProgress();
} else if(main.getAttribute("data-steps")==="1"){
  var ub=document.createElement("button"); ub.type="button"; ub.className="mark unitmark";
  var uset=function(){ub.setAttribute("aria-pressed",String(!!done.unit));ub.textContent=done.unit?"✓ Unit done":"Mark this unit done";};
  uset();
  ub.addEventListener("click",function(){done.unit=!done.unit;lput(PK,JSON.stringify(done));uset();paintStatus();});
  var firstH2=main.querySelector("h2"); (firstH2||main.querySelector(".pager")).insertAdjacentElement("beforebegin",ub);
}
var ROOT=document.body.getAttribute("data-root"), HERE_T=document.body.getAttribute("data-training");
var TRAININGS=(window.KIT_TRAININGS||[]).filter(function(t){return t.units.length;});
if(HERE_T) lput("kit.training",HERE_T);
function unitState(u){
  var p=new URL(ROOT+u.u,location.href).pathname, d={};
  try{d=JSON.parse(lget("kit.done."+p,"{}"))||{};}catch(e){}
  return {p:p,n:u.ids.filter(function(i){return d[i];}).length,of:u.ids.length};
}
function trainingState(t){
  var s={done:0,any:0,frac:0,units:t.units.map(unitState)};
  s.units.forEach(function(r){if(r.n>=r.of) s.done++; if(r.n) s.any++; s.frac+=r.n/r.of;});
  return s;
}
function paintStatus(){
  var sideLinks=[].filter.call(document.querySelectorAll(".side a"),function(x){return x.getAttribute("href").indexOf("#")<0;});
  [].forEach.call(document.querySelectorAll(".traincard"),function(li){
    var t=TRAININGS.filter(function(x){return x.f===li.getAttribute("data-training");})[0], us=li.querySelector(".us");
    if(!t||!us) return;
    var s=trainingState(t), all=s.done===t.units.length;
    us.textContent=all?"✓ All "+s.done+" units done":(s.any?s.done+" of "+t.units.length+" units done":"Not started");
    li.classList.toggle("done",all); li.classList.toggle("going",s.any>0&&!all);
  });
  var T=TRAININGS.filter(function(t){return t.f===(HERE_T||lget("kit.training",""));})[0]||(HERE_T?null:TRAININGS[0]);
  var st=document.getElementById("status"); if(!st||!T) return;
  var s=trainingState(T), cur=null, N=T.units.length;
  T.units.forEach(function(u,i){
    var r=s.units[i], all=r.n>=r.of;
    if(r.p===location.pathname) cur={n:u.n,k:r.n,of:r.of};
    var a=sideLinks.filter(function(x){return new URL(x.href).pathname===r.p;})[0];
    if(!a) return;
    var m=a.querySelector(".sidemark");
    if(!r.n){if(m) m.remove(); return;}
    if(!m){m=document.createElement("span");m.className="sidemark";a.appendChild(m);}
    m.textContent=all?"✓":r.n+"/"+r.of;
    m.setAttribute("title",all?"Done":r.n+" of "+r.of+" steps done");
  });
  var long, short, w, who=HERE_T?"":T.name+": ";
  if(cur&&cur.of===1){long="Unit "+cur.n+" of "+N+(cur.k?" · done":" · not done yet");short=cur.k?"Unit done":"Unit "+cur.n;w=cur.k;}
  else if(cur){long="Unit "+cur.n+" of "+N+" · "+cur.k+" of "+cur.of+" steps done";short=cur.k+"/"+cur.of;w=cur.k/cur.of;}
  else{long=who+(s.done===N?"✓ All ":"")+s.done+" of "+N+" units done";short=s.done+"/"+N;w=s.frac/N;}
  document.getElementById("stext").textContent=long;
  document.getElementById("sshort").textContent=short;
  document.getElementById("sbar").style.width=(100*w)+"%";
  st.href=ROOT+T.readme+"#the-path";
  st.setAttribute("aria-label","Your progress in "+T.name+": "+long+". Go to its path.");
  st.hidden=false;
}
paintStatus();
var cards=[].slice.call(document.querySelectorAll(".unitcard:not(.traincard)"));
if(cards.length){
  var units=cards.map(function(li,k){
    var a=li.querySelector("a"), ids=JSON.parse(li.getAttribute("data-steps")), labels=JSON.parse(li.getAttribute("data-labels"));
    var d={}; try{d=JSON.parse(lget("kit.done."+new URL(a.getAttribute("href"),location.href).pathname,"{}"))||{};}catch(e){}
    var n=ids.filter(function(i){return d[i];}).length, st=li.querySelector(".us");
    li.classList.toggle("done",n>=ids.length); li.classList.toggle("going",n>0&&n<ids.length);
    st.textContent=n>=ids.length?"✓ Done":n?n+" of "+ids.length+" steps done":"Not started";
    var j=ids.findIndex(function(i){return !d[i];});
    return {k:k,n:n,of:ids.length,href:a.getAttribute("href")+(j>=0&&ids[j]!=="unit"?"#"+ids[j]:""),
      label:j>=0&&ids[j]!=="unit"?"step "+(j+1)+" of "+ids.length+", "+labels[j]:"one step: mark it done when you have done the chore"};
  });
  var nDone=units.filter(function(u){return u.n>=u.of;}).length;
  var furthest=units.filter(function(u){return u.n>0;}).pop();
  var todo=units.filter(function(u){return u.n<u.of;});
  var next=furthest?(furthest.n<furthest.of?furthest:(todo.filter(function(u){return u.k>furthest.k;})[0]||todo[0])):null;
  document.getElementById("overall").textContent=nDone===units.length?"✓ All "+units.length+" units done":nDone+" of "+units.length+" units done";
  document.getElementById("bar").style.width=(100*units.reduce(function(s,u){return s+u.n/u.of;},0)/units.length)+"%";
  var cta=document.getElementById("cta"), note=document.getElementById("cta-note");
  if(nDone===units.length){cta.textContent="You have finished the path";cta.href=cards[units.length-1].querySelector("a").getAttribute("href")+"#you-have-finished-the-path";
    note.textContent="See what you can now do";}
  else if(next){cta.textContent="Continue with unit "+(next.k+1);cta.href=next.href;
    note.textContent="Next: "+next.label;}
}
var toclinks=[].slice.call(document.querySelectorAll(".toc a"));
if(toclinks.length&&window.IntersectionObserver){
  var obs=new IntersectionObserver(function(ents){ents.forEach(function(en){
    if(en.isIntersecting){toclinks.forEach(function(a){a.classList.toggle("here",a.getAttribute("href")==="#"+en.target.id);});}
  });},{rootMargin:"-60px 0px -70% 0px"});
  heads.forEach(function(h){obs.observe(h);});
}
var menu=document.getElementById("menu");
menu.addEventListener("click",function(){
  var open=document.body.classList.toggle("nav-open");
  menu.setAttribute("aria-expanded",String(open));
  if(open){var a=document.querySelector(".side a[aria-current]")||document.querySelector(".side a");a&&a.focus();}
});
document.addEventListener("keydown",function(e){
  if(e.key==="Escape"&&document.body.classList.contains("nav-open")){document.body.classList.remove("nav-open");menu.setAttribute("aria-expanded","false");menu.focus();}
});
var side=document.getElementById("side"), cur=side.querySelector("a[aria-current]");
if(cur){side.scrollTop=Math.max(0,cur.offsetTop-side.clientHeight/2);}
var q=document.getElementById("q"), res=document.getElementById("results"), root=document.body.getAttribute("data-root");
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
var STOP=" a an and the to of in on for is it my me i do does did not no can how what why when where which who this that with at or be am are was my your you its it's i'm dont don't doesnt doesn't isnt isn't wont won't ";
function stem(w){return w.length>5?w.replace(/(ing|ed|es|s)$/,""):w;}
function snippet(x,words){
  var lx=x.toLowerCase(), at=-1;
  words.some(function(w){at=lx.indexOf(w);return at>=0;});
  if(at<0) return x.slice(0,110)+(x.length>110?"…":"");
  var s=Math.max(0,at-40); return (s?"…":"")+x.slice(s,s+120)+(s+120<x.length?"…":"");
}
function search(){
  var words=q.value.toLowerCase().replace(/[^a-z0-9.+ ]/g," ").split(/\s+/)
    .filter(function(w){return w.length>2&&STOP.indexOf(" "+w+" ")<0;}).map(stem).filter(Boolean);
  if(!q.value.trim()){res.hidden=true;res.innerHTML="";return;}
  var idx=window.KIT_INDEX||[], hits=[];
  var weight={};
  words.forEach(function(w){
    var df=idx.filter(function(e){return (e.t+" "+e.s+" "+e.x).toLowerCase().indexOf(w)>=0;}).length;
    weight[w]=Math.log((idx.length+1)/(df+1))+0.1;
  });
  idx.forEach(function(e){
    var sec=e.s.toLowerCase(), page=e.t.toLowerCase(), body=e.x.toLowerCase(), score=0;
    words.forEach(function(w){
      var s=(sec.indexOf(w)>=0?4:0)+(page.indexOf(w)>=0?1:0)+(body.indexOf(w)>=0?1:0);
      if(s) score+=s*weight[w];
    });
    if(score) hits.push([score,e]);
  });
  hits.sort(function(a,b){return b[0]-a[0];});
  res.innerHTML=hits.length?hits.slice(0,10).map(function(h){var e=h[1];
    return '<li><a href="'+esc(root+e.u)+'"><span class="rt">'+esc(e.s||e.t)+'</span><br><span class="rs">'+esc((e.s?e.t+": ":"")+snippet(e.x,words))+'</span></a></li>';}).join("")
    :'<li class="none">Nothing found. Try one word, such as <i>error</i>, <i>allow</i> or <i>zip</i>, or open <a href="'+esc(root)+'troubleshooting.html">If something goes wrong</a>.</li>';
  res.hidden=false;
  say.textContent=hits.length?hits.length+" results":"No results";
}
q.addEventListener("input",search);
q.addEventListener("keydown",function(e){if(e.key==="Enter"){var t=res.querySelector("a");if(t){e.preventDefault();location.href=t.href;}}if(e.key==="ArrowDown"){var a=res.querySelector("a");if(a){e.preventDefault();a.focus();}}if(e.key==="Escape"){res.hidden=true;}});
res.addEventListener("keydown",function(e){
  var links=[].slice.call(res.querySelectorAll("a")), i=links.indexOf(document.activeElement);
  if(e.key==="ArrowDown"&&i<links.length-1){e.preventDefault();links[i+1].focus();}
  if(e.key==="ArrowUp"){e.preventDefault();(i>0?links[i-1]:q).focus();}
  if(e.key==="Escape"){res.hidden=true;q.focus();}
});
document.addEventListener("click",function(e){if(!e.target.closest(".search")) res.hidden=true;});
})();"""

if __name__ == "__main__":
    main()
