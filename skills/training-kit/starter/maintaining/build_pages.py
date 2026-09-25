"""Build the trainings' web pages from their markdown, then check them.

    python maintaining/build_pages.py        (from the kit's folder)

Reads every learner .md file in the kit and writes read-in-browser/ with the same
names (.md -> .html; a subfolder's README.md -> index.html). Never edit read-in-browser/ by
hand. The conventions it reads are in maintaining/README.md.
"""
import datetime
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys

# ---- What a maintainer changes when the kit grows (see maintaining/README.md) ----
# A record, not a setting: the version of the training-kit skill that built this kit. It goes into
# each page's generated-file comment only. The kit's own version is the newest entry in CHANGELOG.md.
SKILL_VERSION = "1.0"
PROGRAM_NAME = "Training programme"
# Who the learner asks for help, and where they paste a prompt for it.
ASSISTANT = "the assistant"
ASSISTANT_CHAT = "the assistant's chat box"
# Where practice happens when it is not the assistant's chat: the tool, screen or console the
# learner works in. Prompts marked <!-- tool --> are labelled with it.
PRACTICE_PLACE = "the tool"
# True when learners open the kit's folder where the assistant can read it, so a question can
# name the page and step and the assistant can look them up. False: the question carries the step.
KIT_OPEN_IN_ASSISTANT = True
# True gives each step a "Stuck on this step?" button that copies a question for ASSISTANT. Set it
# False when the help beside the learner is a person rather than an assistant.
STUCK_BUTTON = True
# The trainings, in the order the home page lists them. Each lives in its own folder with its own
# README.md. "path" lists its units in order: (file in the folder, name in the menu, time). A
# training with no path yet is shown as "coming later". "before" lists pages, by their place in
# the kit, that a learner goes through before unit 1, such as a setup page. "stuck_from" gives the
# first step on a unit that offers "Stuck on this step?"; 1 unless listed.
TRAININGS = [
    {"folder": "getting-started", "name": "Getting started", "level": "Beginner",
     "time": "about an hour",
     "path": [("introduction.md", "Introduction", "about five minutes"),
              ("start-here.md", "Start here", "about fifteen minutes"),
              ("lesson-one.md", "The first lesson", "about thirty minutes"),
              ("first-real-task.md", "Your first real task", "on your own work, this week")],
     "before": [], "stuck_from": {}},
]
# The side menu's groups shared by every page: (group, open by default, [(file, name, anchor)]).
MENU_AFTER = [
    ("Help", True, [("troubleshooting.md", "When you are stuck", "when-you-are-stuck"),
                    ("troubleshooting.md", "If something goes wrong", ""),
                    ("faq.md", "Questions", ""),
                    ("glossary.md", "Glossary", "")]),
    ("More", True, [("explanation.md", "Background", ""),
                    ("CHANGELOG.md", "What's new", "")]),
]
# Glossary words linked where first used on a page, and on-screen labels never to link.
GLOSSARY_TERMS = ["Blank", "Check"]
UI_LABELS = ()
# Folders that are not learner pages.
NOT_FOR_LEARNERS = ("facilitator/", "sample-files/", "maintaining/", "read-in-browser/")
# ---- End of what a maintainer changes ----

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, ".."))
OUT_DIR = "read-in-browser"
OUT = os.path.join(KIT, OUT_DIR)
MARKER = re.compile(r"^<!--\s*(frame|tutor|tool)\s*-->$")
TICK_SVG = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
            '<path d="M3 8.5l3 3 7-7"/></svg>')
CHEVRON_SVG = ('<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" '
               'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
ARROW_SVG = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
             '<path d="M6 3l5 5-5 5"/></svg>')


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


CHANGELOG = "CHANGELOG.md"
ENTRY = re.compile(r"^## (\d+\.\d+) - (\d{4}-\d{2}-\d{2}|`\[TO BE WRITTEN:[^\]]*\]`)$")


def kit_version():
    """The kit's version, its date (None while still a placeholder) and the date as written, from the
    newest entry in CHANGELOG.md, which is the first."""
    how = "See 'Versions' in maintaining/README.md."
    if not os.path.isfile(os.path.join(KIT, CHANGELOG)):
        sys.exit("CHANGELOG.md is missing. Every kit has one: learners read it as \"What's new\", and the build "
                 "takes the kit's version from its newest entry. " + how)
    heads = [l.strip() for l in read(CHANGELOG) if l.startswith("## ")]
    entries = [ENTRY.match(h) for h in heads]
    if not entries or not entries[0]:
        sys.exit("The newest entry in CHANGELOG.md must start with a heading like '## 1.2 - 2026-09-24': the "
                 "version, a space, a hyphen, a space, and the date as YYYY-MM-DD. Found: %s. %s"
                 % (heads[0] if heads else "no '## ' heading", how))
    version, raw = entries[0].groups()
    if raw.startswith("`"):
        return version, None, raw
    try:
        day = datetime.date.fromisoformat(raw)
    except ValueError:
        sys.exit("The newest entry in CHANGELOG.md is dated %s, which is not a real date. %s" % (raw, how))
    if day > datetime.date.today():
        sys.exit("The newest entry in CHANGELOG.md is dated %s, which is in the future. Date an entry on the day "
                 "its changes reach learners. %s" % (raw, how))
    later = [e.group(0) for e in entries[1:] if e and not e.group(2).startswith("`") and e.group(2) > raw]
    if later:
        sys.exit("CHANGELOG.md lists its newest entry first, but '%s' is dated after '%s'. %s" % (later[0], heads[0], how))
    return version, raw, raw


KIT_VERSION, KIT_DATE, KIT_DATE_AS_WRITTEN = kit_version()


def git_date(md):
    """The date of the last commit that changed a page, or today when it has changes not yet committed.
    None when git is not installed, the kit is not in a repository, or the page is not tracked."""
    try:
        r = subprocess.run(["git", "-C", KIT, "log", "-1", "--format=%cs", "--", md], capture_output=True, text=True)
        day = r.stdout.strip()
        if r.returncode or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            return None
        changed = subprocess.run(["git", "-C", KIT, "diff", "--quiet", "HEAD", "--", md], capture_output=True)
    except OSError:
        return None
    return datetime.date.today().isoformat() if changed.returncode == 1 else day


PAGE_DATES = {}


def link_href(src, target):
    """A relative markdown link to a kit page becomes a link to its web page."""
    if re.match(r"(https?:|mailto:)", target):
        return target
    path, _, anchor = target.partition("#")
    if not path:
        return "#" + anchor
    full = os.path.normpath(os.path.join(os.path.dirname(src), path)).replace("\\", "/")
    if full in FILES:
        return rel(src, out_name(full)) + ("#" + anchor if anchor else "")
    if not full.endswith(".md") and os.path.isfile(os.path.join(KIT, full)):
        # A picture or practice file: link to it where it sits in the kit.
        page_dir = os.path.dirname(os.path.join(OUT, out_name(src)))
        return os.path.relpath(os.path.join(KIT, full), page_dir).replace("\\", "/")
    return None


def inline(text, src):
    out = []
    for p in re.split(r"(`[^`]+`|!\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\([^)]+\))", text):
        img = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", p)
        if img:
            href = link_href(src, img.group(2))
            out.append('<img src="%s" alt="%s">' % (html.escape(href), html.escape(img.group(1)))
                       if href else html.escape(img.group(1)))
        elif len(p) > 1 and p.startswith("`") and p.endswith("`"):
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
            ext = ' target="_blank" rel="noopener"' if href and re.match(r"https?:", href) else ""
            out.append('<a href="%s"%s>%s</a>' % (html.escape(href), ext, shown) if href else shown)
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
SETTINGS = ("PROGRAM_NAME", "ASSISTANT", "ASSISTANT_CHAT", "PRACTICE_PLACE")


def setting_html(value):
    """A setting still left as a blank shows as a marked blank, as it would in a page."""
    if BLANK.search(value):
        return '<span class="org" title="Your organization fills this in">%s</span>' % html.escape(value)
    return html.escape(value)


def prompt_block(raw, kind=None):
    if re.fullmatch(r"`%s`" % BLANK.pattern, raw.strip()):
        who = ("Your organization supplies this prompt; until it does, there is nothing to paste here."
               if "YOUR ORGANIZATION" in raw else "This prompt is not written yet, so there is nothing to paste here.")
        return ('<div class="prompt%s orgprompt"><p class="lab">%s</p>'
                '<div class="t">%s</div></div>' % (" " + kind if kind else "", who, inline(raw.strip(), "")))
    if kind == "frame":
        return ('<div class="prompt frame"><p class="lab">Write this yourself, filling in each part:</p>'
                '<div class="t">%s</div></div>' % prompt_text(raw, False))
    first = re.sub(r"[`<>]", "", raw)
    first = first if len(first) <= 40 else first[:40].rsplit(" ", 1)[0] + "…"
    cls = {"tutor": "prompt tutor", "tool": "prompt tool"}.get(kind, "prompt")
    lab = {"tutor": '<p class="lab">Ask %s:</p>' % setting_html(ASSISTANT),
           "tool": '<p class="lab">Paste this into %s:</p>' % setting_html(PRACTICE_PLACE)}.get(kind, "")
    where = setting_html(PRACTICE_PLACE if kind == "tool" else ASSISTANT_CHAT)
    return ('<div class="%s">%s<div class="t">%s</div>'
            '<button class="copy" type="button" aria-label="Copy: %s">Copy</button>'
            '<p class="after" hidden>Pasted it into %s? Change any highlighted part before you go on.</p></div>'
            % (cls, lab, prompt_text(raw, True), html.escape(first), where))


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
            num = re.match(r"^(\d+)\.\s+(.*)$", t)
            if num:
                # A numbered step: its number in a badge; the full stop stays for screen readers.
                h.append('<h%d id="%s" class="step"><span class="n">%s<span class="sr">.</span></span> '
                         '<span class="tt">%s</span></h%d>' % (level, slug(t), num.group(1), inline(num.group(2), src), level))
            else:
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
            ans = re.match(r"^(Check your answer|Answers):\s*", text)
            if ans:
                if h and h[-1].startswith("<p>") and h[-1].endswith("?</p>"):
                    h[-1] = '<p class="question">' + h[-1][3:]
                h.append('<details class="answer"><summary>Show the answer</summary><div class="a"><p>'
                         '<span class="sr">%s: </span>%s</p></div></details>' % (ans.group(1), inline(text[ans.end():], src)))
                continue
            chk = re.match(r"^(\*\*)?Check:(\*\*)?\s*", text)
            if chk:
                after = ("**" if chk.group(1) and not chk.group(2) else "") + text[chk.end():]
                h.append('<div class="check"><p class="lbl">%s<span>Check</span><span class="sr">:</span></p>'
                         '<p>%s</p></div>' % (TICK_SVG, inline(after, src)))
                continue
            whole = text[1:-1] if text.startswith("`Example") and text.endswith("`") and text.count("`") == 2 else text
            ex = re.match(r"^(Example\b[^:`]{0,80}):\s*", whole)
            if ex:
                h.append('<div class="example"><p class="tag">%s<span class="sr">:</span></p><p>%s</p></div>'
                         % (html.escape(ex.group(1), quote=False), inline(whole[ex.end():], src)))
                continue
            h.append("<p>%s</p>" % inline(text, src))
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
    # Only recipes in the table are reachable: the outline links the table, not each recipe.
    return found


for _t in TRAININGS:
    _t.setdefault("before", [])
    _t.setdefault("stuck_from", {})
    _t["readme"] = in_training(_t, "README.md")
    _t["units"] = [in_training(_t, f) for f, _, _ in _t["path"]]
    _t["recipes"] = recipes_of(_t)
    _t["seq"] = [_t["readme"]] + _t["before"] + _t["units"]
UNITS = {}
for _t in TRAININGS:
    for _n, (_f, _, _time) in enumerate(_t["path"], 1):
        UNITS[in_training(_t, _f)] = (_t, _n, _time)


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
             "'before' list in TRAININGS, to MENU_AFTER, or as a row in a training's recipe table "
             "(how-to/README.md)." % ", ".join(missing))
absent = [f for f in ORDER if f not in FILES]
if absent:
    sys.exit("In a menu but not found as learner pages: %s" % ", ".join(absent))


HEAD = r'<h([23]) id="([^"]+)"[^>]*>(.*?)</h\1>'


def inline_toc(rest):
    """A folded list of a long help page's headings. Unit pages have none: the outline lists their steps."""
    heads = re.findall(HEAD, rest)
    if len(heads) < 3:
        return ""
    lis = "".join('<li class="l%s"><a href="#%s">%s</a></li>' % (lv, i, re.sub(r"<[^>]+>", "", t)) for lv, i, t in heads)
    return '<details class="toc-inline"><summary>On this page</summary><ul>%s</ul></details>' % lis


def unit_steps(md):
    """The step ids a unit page tracks; a unit with no numbered steps is tracked as one step, 'unit'."""
    heads = re.findall(HEAD, render(read(md)[1:], md))
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
        meta = ('<p class="um">%s &middot; %s</p>' % (plural(len(t["units"]), "unit"), html.escape(t["time"]))) if ready else ""
        status = '<p class="us">Not started</p>' if ready else ""
        lis.append('<li class="unitcard traincard" data-training="%s">%s<a href="%s">%s</a>'
                   '<p class="uo">%s</p>%s%s</li>'
                   % (html.escape(t["folder"] if t else ""), '<span class="un">%s</span>' % label if label else "",
                      html.escape(out_name(target)), html.escape(title),
                      inline(text[:1].upper() + text[1:], "README.md"), meta, status))
    return '<ul class="units">%s</ul>' % "".join(lis)


def page_training(md):
    """The training a page belongs to: the one whose folder holds it, or whose 'before' list names it."""
    return training_of(md) or next((x for x in TRAININGS if md in x["before"]), None)


AVAILABLE = [x for x in TRAININGS if x["path"]]


def outline_training(md):
    """The training whose outline a page shows. None: the page shows the programme's trainings instead."""
    t = page_training(md)
    if t:
        return t if t["path"] else None
    return AVAILABLE[0] if len(TRAININGS) == 1 and AVAILABLE else None


def unit_name(md):
    t, n, _ = UNITS[md]
    return t["path"][n - 1][1]


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def ring(label):
    return ('<span class="oring" aria-hidden="true"><svg viewBox="0 0 32 32"><circle class="trk" cx="16" cy="16" r="13"/>'
            '<circle class="arc" cx="16" cy="16" r="13" transform="rotate(-90 16 16)" stroke-dasharray="0 82" '
            'style="display:none"/></svg><span class="n">%s</span></span>' % label)


def outline(md):
    """The left-hand outline: a training's units and their steps, or, where no one training applies,
    the programme's trainings; then the help pages, quietly, under More."""
    t = outline_training(md)

    def cur(target):
        return ' aria-current="page"' if target == md else ""
    close = '<button class="oclose" id="oclose" type="button" aria-label="Close the outline">&times;</button>'
    rows = []
    if t:
        head = ('<div class="ohead"><p class="okicker">%s</p><a class="otitle" href="%s"%s>%s</a>'
                '<p class="ototal">%s &middot; %s</p><div class="obar" aria-hidden="true"><span id="obar"></span></div>'
                '<p class="opct" id="opct"></p>%s</div>'
                % (html.escape(PROGRAM_NAME), rel(md, out_name(t["readme"])), cur(t["readme"]), html.escape(t["name"]),
                   plural(len(t["units"]), "unit"), html.escape(t["time"]), close))
        for n, (u, (_, name, time)) in enumerate(zip(t["units"], t["path"]), 1):
            steps = unit_steps(u)
            here = u == md
            base = "" if steps[0][0] == "unit" else " &middot; " + plural(len(steps), "step")
            row = ('<a class="orow" href="%s"%s>%s<span class="otext"><span class="oname">%s</span>'
                   '<span class="ometa">Unit %d &middot; %s<span class="oprog" data-base="%s">%s</span></span></span></a>'
                   % (rel(md, out_name(u)), cur(u), ring(n), html.escape(name), n, html.escape(time), base, base))
            toggle = sub = ""
            if base:
                page = "" if here else rel(md, out_name(u))
                sub = '<ol class="osteps" id="os%d" aria-label="Steps in unit %d">%s</ol>' % (n, n, "".join(
                    '<li><a class="ostep" href="%s#%s" data-id="%s"><span class="odot" aria-hidden="true"></span>'
                    '<span class="olab">%s<span class="sr ostate"></span></span></a></li>' % (page, i, i, label)
                    for i, label in steps))
                toggle = ('<button class="otoggle" type="button" aria-expanded="%s" aria-controls="os%d">'
                          '<span class="sr">Steps in unit %d</span>%s</button>'
                          % ("true" if here else "false", n, n, CHEVRON_SVG))
            rows.append('<li class="ou%s" data-u="%s"><div class="ohd">%s%s</div>%s</li>'
                        % (" current open" if here else "", out_name(u), row, toggle, sub))
    else:
        head = ('<div class="ohead"><p class="okicker">All trainings</p><a class="otitle" href="%s"%s>%s</a>'
                '<p class="ototal">%s</p>%s</div>'
                % (rel(md, "README.html"), cur("README.md"), html.escape(PROGRAM_NAME),
                   plural(len(TRAININGS), "training"), close))
        for n, x in enumerate(TRAININGS, 1):
            if x["path"]:
                meta = " &middot; ".join(html.escape(p) for p in (x["level"], plural(len(x["units"]), "unit"), x["time"]) if p)
            else:
                meta = "Coming later"
            rows.append('<li class="ou%s" data-t="%s"><div class="ohd"><a class="orow" href="%s"%s>%s'
                        '<span class="otext"><span class="oname">%s</span><span class="ometa">%s'
                        '<span class="oprog" data-base=""></span></span></span></a></div></li>'
                        % ("" if x["path"] else " later", html.escape(x["folder"]), rel(md, out_name(x["readme"])),
                           cur(x["readme"]), ring(n), html.escape(x["name"]), meta))
    more, seen, lis = [], set(), []
    if t:
        more += [(f, nav_title(f), "", "") for f in t["before"]]
        if t["recipes"]:
            more.append((in_training(t, "how-to/README.md"), "Practice recipes", "", str(len(t["recipes"]))))
    for _, _, items in MENU_AFTER:
        more += [(f, text, anchor, "") for f, text, anchor in items]
    if t:
        more.append(("README.md", "All trainings", "", ""))
    for target, text, anchor, count in more:
        if (target, anchor) in seen:
            continue
        seen.add((target, anchor))
        href = rel(md, out_name(target)) + ("#" + anchor if anchor else "")
        mark = ' aria-current="page"' if target == md and not anchor else \
            (' aria-current="true"' if count and md in t["recipes"] else "")
        lis.append('<li><a href="%s"%s>%s%s</a></li>' % (html.escape(href), mark, html.escape(text),
                   '<span class="cnt"><span class="sr">, </span>%s</span>' % count if count else ""))
    return ('<nav id="side" class="side" aria-label="Course outline">%s<ol class="ounits">%s</ol>'
            '<div class="omore"><p class="omh" id="omh">More</p><ul aria-labelledby="omh">%s</ul></div></nav>'
            '<div class="scrim" id="scrim" aria-hidden="true"></div>' % (head, "".join(rows), "".join(lis)))


def crumbs(md):
    """Where the page sits, and, on a training's pages, the learner's place and progress in it."""
    t = page_training(md)
    items = []
    if md == "README.md":
        items.append('<li aria-current="page"><span>%s</span></li>' % html.escape(PROGRAM_NAME))
    else:
        items.append('<li class="prog"><a href="%s">%s</a></li>' % (rel(md, "README.html"), html.escape(PROGRAM_NAME)))
        if t and md != t["readme"]:
            items.append('<li><a href="%s">%s</a></li>' % (rel(md, out_name(t["readme"])), html.escape(t["name"])))
            index = in_training(t, "how-to/README.md")
            if md in t["recipes"]:
                items.append('<li><a href="%s">%s</a></li>' % (rel(md, out_name(index)), html.escape(nav_title(index))))
        name = t["name"] if t and md == t["readme"] else (unit_name(md) if md in UNITS else nav_title(md))
        items.append('<li aria-current="page"><span>%s</span></li>' % html.escape(name))
    pos = ""
    if md in UNITS:
        start = "Unit %d of %d" % (UNITS[md][1], len(t["units"]))
        pos = ('<span class="unitpos" id="unitpos"><span class="long" id="upos-long">%s</span>'
               '<span class="short" id="upos-short">%s</span></span>' % (start, start))
    line = '<div class="line" aria-hidden="true"><span id="line"></span></div>' if outline_training(md) else ""
    return ('<nav class="crumbs" aria-label="Breadcrumb"><div class="in"><ol>%s</ol>%s</div>%s</nav>'
            % ("".join(items), pos, line))


def pager(md):
    """A unit (or a setup page before unit 1) ends with what comes next and a Continue button; every other
    page with quiet links to the pages either side of it."""
    t = page_training(md)
    seq = None
    if t and t["path"] and md in t["seq"]:
        seq = t["seq"]
    elif t and md in [in_training(t, "how-to/README.md")] + t["recipes"]:
        seq = [in_training(t, "how-to/README.md")] + t["recipes"]
    k = seq.index(md) if seq else -1
    prev_ = seq[k - 1] if seq and k > 0 else None
    next_ = seq[k + 1] if seq and k + 1 < len(seq) else None
    if t and t["path"] and (md in UNITS or md in t["before"]):
        if next_:
            lbl = ("Next unit: %d of %d &middot; %s" % (UNITS[next_][1], len(t["units"]), html.escape(UNITS[next_][2]))
                   if next_ in UNITS else "Next")
            title, href, btn = (unit_name(next_) if next_ in UNITS else nav_title(next_)), rel(md, out_name(next_)), "Continue"
        else:
            lbl, title, href, btn = "End of the path", t["name"], rel(md, out_name(t["readme"])), "Back to the training"
        back = ""
        if prev_ and not (not next_ and prev_ == t["readme"]):
            text = ("Previous unit: " + unit_name(prev_) if prev_ in UNITS else
                    "Back to " + t["name"] if prev_ == t["readme"] else "Previous: " + nav_title(prev_))
            back = '<a class="prev" href="%s">&lsaquo; %s</a>' % (rel(md, out_name(prev_)), html.escape(text))
        nudge = '<p class="nudge" id="nudge" aria-live="polite"></p>' if md in UNITS else ""
        return ('<nav class="pager" aria-label="What comes next"><div class="nextunit"><p class="lbl">%s</p><h2>%s</h2>'
                '<div class="nextrow"><a class="btn" href="%s">%s%s</a>%s</div>%s</div></nav>'
                % (lbl, html.escape(title), href, btn, ARROW_SVG, back, nudge))
    links = []
    if md == "README.md":
        if AVAILABLE:
            links.append('<a class="next" href="%s">Start with %s &rsaquo;</a>'
                         % (out_name(AVAILABLE[0]["readme"]), html.escape(AVAILABLE[0]["name"])))
    elif seq is None or (k == 0 and md == t["readme"]):
        links.append('<a class="prev" href="%s">&lsaquo; All trainings</a>' % rel(md, "README.html"))
    elif prev_:
        links.append('<a class="prev" href="%s">&lsaquo; Previous: %s</a>' % (rel(md, out_name(prev_)), html.escape(nav_title(prev_))))
    if next_:
        links.append('<a class="next" href="%s">Next: %s &rsaquo;</a>' % (rel(md, out_name(next_)), html.escape(nav_title(next_))))
    return '<nav class="pager" aria-label="Previous and next page"><div class="nextrow quiet">%s</div></nav>' % "".join(links)


def page_foot(md):
    """Quiet facts said once, at the foot of every page: when this page last changed, and the kit's
    version, which links to What's new."""
    day = PAGE_DATES.get(md) or KIT_DATE
    updated = '<span>Last updated %s</span>' % day if day else ""
    return ('<footer class="pagefoot">%s<a href="%s">Version %s &middot; updated %s</a></footer>'
            % (updated, rel(md, out_name(CHANGELOG)), html.escape(KIT_VERSION), inline(KIT_DATE_AS_WRITTEN, CHANGELOG)))


def how_to_use():
    return ('<aside class="howto" aria-label="How to use a prompt"><b>Using a prompt:</b> select <b>Copy</b> '
            'beside it. Then right-click where the page says to paste it (%s, unless it is labelled otherwise) '
            'and select <b>Paste</b>, or press <kbd>Ctrl</kbd>+<kbd>V</kbd>. Change any '
            '<span class="ph">highlighted blank</span> to your own, then go on.</aside>' % setting_html(ASSISTANT_CHAT))


def folder_box():
    return ('<div class="setup"><label for="folder">Optional: the name of your own folder for this page '
            '(not the training&rsquo;s folder). The prompts on this page will use it.</label>'
            '<input id="folder" placeholder="your folder&rsquo;s name" autocomplete="off"></div>')


def search_entries(md, title, rest):
    entries = []
    parts = re.split(r'(<h[23] id="[^"]+"[^>]*>.*?</h[23]>)', rest)
    anchor, section = "", ""
    for part in parts:
        m = re.match(r'<h[23] id="([^"]+)"[^>]*>(.*?)</h[23]>', part)
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
     Built by the training-kit skill, version {skill}
-->
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{tabtitle}</title>
<style>
{css}
</style></head><body data-root="{root}" data-training="{tfolder}" data-outline="{ofolder}">
<a class="skip" href="#main">Skip to the page</a>
<header class="site">
<button id="menu" class="menu" type="button" aria-controls="side" aria-expanded="false"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 4h12M2 8h12M2 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>Outline</button>
<a class="brand" href="{home}">{program}</a>
<div class="search" role="search"><label class="sr" for="q">Search the trainings</label>
<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="7" cy="7" r="5"/><path d="M11 11l3.5 3.5"/></svg>
<input id="q" type="search" placeholder="Search" autocomplete="off" aria-controls="results">
<ul id="results" class="results" hidden></ul></div>
<button id="theme" class="iconbtn" type="button" aria-label="Switch to dark theme" title="Switch between light and dark"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10" cy="10" r="7"/><path d="M10 3a7 7 0 0 0 0 14z" fill="currentColor"/></svg></button>
</header>
<div class="layout">
{nav}
<div class="content">
{crumbs}
<main id="main" data-steps="{steps}" data-page="{page}" data-stuck-from="{stuckfrom}" data-kit-open="{kitopen}" data-stuck="{stuck}" data-program="{program}">
{body}
{pager}
</main>
{foot}
</div>
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
                     rest.find('<div class="prompt tool"'), rest.find('<div class="setup"')) if x >= 0]
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
    # Position and progress are said once, in the breadcrumb and the outline; a unit's own
    # steps are listed in the outline, so only long help pages get an "On this page" list.
    landing = md == "README.md" or any(md == x["readme"] for x in TRAININGS)
    body = "<h1>%s</h1>\n" % inline(title, md) + ("" if md in UNITS or landing else inline_toc(rest)) + rest
    path = os.path.join(OUT, out_name(md))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    root = rel(md, "x")[:-1]
    ot = outline_training(md)
    doc = TEMPLATE.format(source=md, title=html.escape(title), root=root, program=html.escape(PROGRAM_NAME),
                          tabtitle=html.escape(title if title.startswith(t["name"] if t else PROGRAM_NAME)
                                               else "%s - %s" % (title, t["name"] if t else PROGRAM_NAME)),
                          tfolder=html.escape(t["folder"] if t else ""), ofolder=html.escape(ot["folder"] if ot else ""),
                          home=rel(md, "README.html"), nav=outline(md), crumbs=crumbs(md), body=body,
                          pager=pager(md), foot=page_foot(md), skill=html.escape(SKILL_VERSION), css=CSS, js=JS,
                          steps="1" if md in UNITS else "0", page=html.escape(nav_title(md)),
                          kitopen="1" if KIT_OPEN_IN_ASSISTANT else "0", stuck="1" if STUCK_BUTTON else "0",
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
    for n, line in enumerate(read("maintaining/build_pages.py"), 1):
        if line.split(" =")[0] in SETTINGS:
            for m in BLANK.finditer(line):
                rows.append(("maintaining/build_pages.py", n, "Settings", m.group(0)))
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


# The starter's own titles, unit names and step headings. They name a stage of the method, not what the
# learner does there, so a kit is a draft while any is left.
STARTER_NAMES = {
    "Training programme", "Getting started", "Start here", "Start here: your first fifteen minutes",
    "The first lesson", "Your first real task", "Your first real task this week", "An example recipe",
    "First step", "Second step", "Open what you will practise in", "Try the help beside you",
    "Produce a first result", "What this unit covered", "Look before you change anything",
    "See it done first", "Do the task", "Check it yourself", "Apply it to a second case", "Pick the task",
    "Do it", "Note what happened", "In two or three days"}


def starter_names_left():
    found = [PROGRAM_NAME] if PROGRAM_NAME in STARTER_NAMES else []
    for t in TRAININGS:
        found += [n for n in [t["name"]] + [p[1] for p in t["path"]] if n in STARTER_NAMES]
    for md in FILES:
        lines = read(md)
        heads = [title_of(md)] + [re.sub(r"^\d+\.\s*", "", ln[3:]).strip() for ln in lines if ln.startswith("## ")]
        found += [h for h in heads if h in STARTER_NAMES]
    return found


def check_step_numbers():
    """Numbered steps on each page run 1, 2, 3 in order, with no gap or repeat."""
    for md in FILES:
        nums = [int(m.group(1)) for m in (re.match(r"^## (\d+)\. ", ln) for ln in read(md)) if m]
        if nums and nums != list(range(1, len(nums) + 1)):
            sys.exit("The numbered steps in %s run %s; they must run 1 to %d in order. Renumber them, and "
                     "check the order still follows the task." % (md, ", ".join(map(str, nums)), len(nums)))


def main():
    check_step_numbers()
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
    for md in ORDER:
        PAGE_DATES[md] = git_date(md)
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
    generic = starter_names_left()
    if generic:
        print("DRAFT: %d titles or headings still carry the starter's stand-in names (%s); rename each for "
              "what the learner does or gets there" % (len(generic), "; ".join(sorted(set(generic))[:6])))
    unwritten = sum(" ".join(read(md)).count("[TO BE WRITTEN") for md in FILES)
    if unwritten:
        print("DRAFT: %d [TO BE WRITTEN] placeholders in learner pages; not ready for learners" % unwritten)
    print("version %s, %s" % (KIT_VERSION, KIT_DATE or "date not written yet"))
    newer = [md for md in ORDER if md != CHANGELOG and KIT_DATE and (PAGE_DATES[md] or "") > KIT_DATE]
    if newer:
        print("NOTE: pages changed after the newest CHANGELOG.md entry (%s): %s. If a change reaches learners, "
              "add an entry for it (see 'Versions' in maintaining/README.md)." % (KIT_DATE, ", ".join(newer)))
    failed = False
    for checker in ("check_text.py", "check_structure.py"):
        r = subprocess.run([sys.executable, os.path.join(HERE, checker), KIT, OUT], capture_output=True, text=True)
        problems = [l for l in r.stdout.splitlines() if not l.startswith("OK")]
        print("\n".join(problems))
        failed = failed or r.returncode != 0 or not problems or not problems[-1].endswith(": 0")
    if failed:
        sys.exit("CHECKS FAILED: fix the markdown (never the pages) and build again.")
    print("All checks passed.")


CSS = r""":root{--bg:#ffffff;--bg2:#f7f7f7;--surface:#ffffff;--ink:#171717;--ink2:#505050;--ink3:#6b6b6b;
--rule:#e1e1e1;--rule2:#c8c8c8;--accent:#0065b3;--accent-ink:#ffffff;--accent-soft:#eaf3fb;--ok:#107c10;--ok-ink:#ffffff;
--ok-soft:#eef7ee;--ph:#fff1b8;--phline:#a8741a;--org:#fff8e1;--code:#f3f3f3;--focus:#0065b3;
--shadow:0 1px 2px rgba(0,0,0,.06),0 4px 14px rgba(0,0,0,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--bg:#171717;--bg2:#1f1f1f;--surface:#202020;--ink:#e6e6e6;--ink2:#b8b8b8;--ink3:#9a9a9a;--rule:#353535;--rule2:#4a4a4a;
--accent:#75b6e7;--accent-ink:#101010;--accent-soft:#1d2a36;--ok:#7fce7f;--ok-ink:#101010;--ok-soft:#1b2a1b;--ph:#4a3d1f;
--phline:#e0b25e;--org:#2b2518;--code:#262626;--focus:#75b6e7;--shadow:0 1px 2px rgba(0,0,0,.4),0 4px 14px rgba(0,0,0,.35)}}
:root[data-theme="dark"]{--bg:#171717;--bg2:#1f1f1f;--surface:#202020;--ink:#e6e6e6;--ink2:#b8b8b8;--ink3:#9a9a9a;
--rule:#353535;--rule2:#4a4a4a;--accent:#75b6e7;--accent-ink:#101010;--accent-soft:#1d2a36;--ok:#7fce7f;--ok-ink:#101010;
--ok-soft:#1b2a1b;--ph:#4a3d1f;--phline:#e0b25e;--org:#2b2518;--code:#262626;--focus:#75b6e7;
--shadow:0 1px 2px rgba(0,0,0,.4),0 4px 14px rgba(0,0,0,.35)}
:root[data-theme="dark"]{color-scheme:dark}:root[data-theme="light"]{color-scheme:light}
:root{--side:var(--bg2);--cur:var(--accent-soft);--field:var(--rule2);--okink:var(--ok-ink);--hdr:54px;--crb:46px}
*{box-sizing:border-box}
html{scroll-padding-top:calc(var(--hdr) + var(--crb) + 14px);-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
font:1rem/1.65 "Segoe UI",SegoeUI,-apple-system,BlinkMacSystemFont,"Helvetica Neue",system-ui,sans-serif}
a{color:var(--accent);text-underline-offset:2px}
a:hover{text-decoration-thickness:2px}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px;border-radius:2px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:-999px;top:8px;background:var(--surface);padding:6px 10px;z-index:40}
.skip:focus{left:8px}
/* site header */
.site{position:sticky;top:0;z-index:30;height:var(--hdr);display:flex;align-items:center;gap:14px;padding:0 20px;
background:var(--surface);border-bottom:1px solid var(--rule)}
.brand{font-weight:600;font-size:1.05rem;color:var(--ink);text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.menu{display:none;align-items:center;gap:6px;font:inherit;font-size:.9rem;padding:5px 12px;border:1px solid var(--rule2);
border-radius:4px;background:var(--surface);color:var(--ink);cursor:pointer;flex:none}
.search{position:relative;margin-left:auto;width:min(320px,42vw);flex:none}
.search input{width:100%;height:34px;padding:0 10px 0 32px;font:inherit;font-size:.9rem;color:var(--ink);
background:var(--bg2);border:1px solid var(--rule2);border-radius:4px}
.search svg{position:absolute;left:10px;top:10px;width:14px;height:14px;color:var(--ink3)}
.results{position:absolute;right:0;top:40px;width:min(460px,92vw);max-height:70vh;overflow:auto;margin:0;padding:6px;
list-style:none;z-index:30;background:var(--surface);border:1px solid var(--rule);border-radius:6px;box-shadow:var(--shadow)}
.results li{margin:0}
.results li a{display:block;padding:7px 10px;line-height:1.4;border-radius:4px;color:var(--ink);text-decoration:none}
.results li a:hover,.results li a:focus{background:var(--accent-soft)}
.results .rt{font-weight:600;font-size:.9rem}
.results .rs{font-size:.8rem;color:var(--ink2)}
.results .none{padding:7px 10px;color:var(--ink2);font-size:.9rem}
.iconbtn{flex:none;width:34px;height:34px;display:grid;place-items:center;border:1px solid transparent;border-radius:4px;
background:none;color:var(--ink2);cursor:pointer}
.iconbtn:hover{background:var(--bg2);color:var(--ink)}
.iconbtn svg{width:18px;height:18px}
/* page grid: outline | page */
.layout{display:grid;grid-template-columns:300px minmax(0,1fr)}
.content{--gut:clamp(24px,4.5vw,72px);min-width:0}
/* the outline */
.side{position:sticky;top:var(--hdr);align-self:start;height:calc(100vh - var(--hdr));overflow:auto;padding:0 0 32px;
background:var(--side);border-right:1px solid var(--rule);font-size:.95rem;line-height:1.4}
.side ol,.side ul{list-style:none;margin:0;padding:0}
.side li{margin:0}
.ohead{padding:22px 20px 18px;border-bottom:1px solid var(--rule)}
.okicker{margin:0 0 2px;font-size:.8rem;color:var(--ink3)}
.otitle{display:block;font-size:1.15rem;font-weight:700;color:var(--ink);text-decoration:none;line-height:1.3}
.otitle:hover{text-decoration:underline}
.otitle[aria-current]{color:var(--accent)}
.ototal{margin:4px 0 0;font-size:.82rem;color:var(--ink2)}
.obar{height:6px;border-radius:3px;background:var(--rule);overflow:hidden;margin:14px 0 8px}
.obar span{display:block;height:100%;width:0;background:var(--ok);transition:width .3s}
.opct{margin:0;font-size:.85rem;font-weight:600;color:var(--ink2)}
.opct:empty{display:none}
.ounits{padding:8px 0}
.ou + .ou{border-top:1px solid var(--rule)}
.ohd{display:flex;align-items:center}
.orow{flex:1;min-width:0;display:flex;align-items:center;gap:14px;min-height:64px;padding:12px 4px 12px 20px;
color:var(--ink);text-decoration:none}
.orow:hover .oname{text-decoration:underline}
.orow[aria-current] .oname{color:var(--accent)}
.oring{flex:none;position:relative;width:30px;height:30px}
.oring svg{display:block;width:30px;height:30px}
.oring .trk{fill:none;stroke:var(--rule2);stroke-width:3}
.oring .arc{fill:none;stroke:var(--ok);stroke-width:3;stroke-linecap:round;transition:stroke-dasharray .3s}
.oring .n{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:700;color:var(--ink2)}
.oring.full{border-radius:50%;background:var(--ok)}
.oring.full svg{display:none}
.oring.full .n{color:var(--okink)}
.ou.later .oring{opacity:.55}
.otext{display:flex;flex-direction:column;min-width:0}
.oname{font-weight:600}
.ou.current .oname{font-weight:700}
.ometa{margin-top:2px;font-size:.82rem;color:var(--ink3)}
.ometa .ok{color:var(--ok);font-weight:600}
.otoggle{flex:none;width:40px;height:40px;margin-right:10px;display:flex;align-items:center;justify-content:center;
border:0;border-radius:6px;background:none;color:var(--ink3);cursor:pointer}
.otoggle:hover{background:var(--cur);color:var(--ink)}
.otoggle svg{transition:transform .15s}
.ou.open .otoggle svg{transform:rotate(180deg)}
.osteps{display:none;position:relative;padding:0 12px 12px 0}
.ou.open .osteps{display:block}
.osteps::before{content:"";position:absolute;left:34px;top:0;bottom:34px;width:2px;background:var(--rule)}
.ostep{position:relative;display:flex;align-items:flex-start;gap:14px;min-height:44px;padding:11px 10px 11px 27px;
border-radius:0 6px 6px 0;color:var(--ink2);text-decoration:none;font-size:.92rem}
.ostep:hover{color:var(--ink)}
.ostep:hover .olab{text-decoration:underline}
.odot{flex:none;position:relative;width:16px;height:16px;margin-top:2px;border-radius:50%;border:2px solid var(--field);
background:var(--side)}
.ostep.done .odot{border-color:var(--ok);background:var(--ok)}
.ostep.done .odot::after{content:"";position:absolute;left:3px;top:0;width:4px;height:8px;border:solid var(--okink);
border-width:0 2px 2px 0;transform:rotate(45deg)}
.ostep.here{color:var(--accent);font-weight:600}
.ostep.here .odot{border-color:var(--accent);box-shadow:0 0 0 3px var(--side),0 0 0 5px var(--accent)}
.ostep.here:not(.done) .odot{background:var(--accent);box-shadow:inset 0 0 0 3px var(--side),0 0 0 0 transparent}
.omore{margin:10px 20px 0;padding-top:16px;border-top:1px solid var(--rule)}
.omh{margin:0 0 6px;font-size:.85rem;font-weight:600;color:var(--ink3)}
.omore a{display:flex;align-items:center;gap:8px;min-height:40px;padding:8px 10px;margin:0 -10px;border-radius:6px;
color:var(--ink2);font-size:.9rem;text-decoration:none}
.omore a:hover{background:var(--cur);color:var(--ink)}
.omore a[aria-current]{background:var(--cur);color:var(--ink);font-weight:600;box-shadow:inset 3px 0 0 var(--accent)}
.omore .cnt{margin-left:auto;font-size:.8rem;color:var(--ink3)}
.oclose{display:none}
.scrim{display:none}
/* breadcrumb strip, carrying position and progress */
.crumbs{position:sticky;top:var(--hdr);z-index:18;background:var(--bg);border-bottom:1px solid var(--rule)}
.crumbs .in{max-width:760px;margin:0 var(--gut);height:var(--crb);display:flex;align-items:center;gap:12px}
.crumbs ol{display:flex;align-items:center;min-width:0;flex:1;margin:0;padding:0;list-style:none;font-size:.875rem}
.crumbs li{display:flex;align-items:center;min-width:0;margin:0;white-space:nowrap}
.crumbs li a,.crumbs li span{overflow:hidden;text-overflow:ellipsis}
.crumbs li a{color:var(--accent);text-decoration:none}
.crumbs li a:hover{text-decoration:underline}
.crumbs li+li::before{content:"";flex:none;width:6px;height:6px;margin:0 10px 0 8px;border-right:1.5px solid var(--ink3);
border-top:1.5px solid var(--ink3);transform:rotate(45deg)}
.crumbs li[aria-current] span{color:var(--ink2)}
.unitpos{flex:none;font-size:.82rem;font-weight:600;color:var(--ink2);white-space:nowrap}
.unitpos .short{display:none}
.unitpos.all{color:var(--ok)}
.line{position:absolute;left:0;right:0;bottom:-1px;height:3px;background:transparent}
.line span{display:block;height:100%;width:0;background:var(--accent);transition:width .3s}
/* the page */
main{max-width:760px;margin:0 var(--gut);padding:28px 0 72px}
main h1{font-size:2.25rem;line-height:1.25;font-weight:600;letter-spacing:-.015em;margin:6px 0 16px}
main > h1 + p{font-size:1.0625rem}
main h2{font-size:1.5rem;line-height:1.3;font-weight:600;margin:52px 0 12px}
main h3{font-size:1.15rem;line-height:1.35;font-weight:600;margin:32px 0 8px}
main h2.step{display:flex;gap:10px;align-items:baseline;margin-top:40px;padding-top:40px;border-top:1px solid var(--rule)}
main h3.step{display:flex;gap:8px;align-items:baseline}
.step .n{flex:none;display:inline-grid;place-items:center;min-width:28px;height:28px;padding:0 6px;border-radius:14px;
font-size:.95rem;background:var(--accent-soft);color:var(--accent);transform:translateY(-2px)}
h3.step .n{min-width:24px;height:24px;font-size:.85rem}
.step.done .n{background:var(--ok);color:var(--ok-ink)}
main p{margin:12px 0}
main ul,main ol{padding-left:22px;margin:12px 0}
main li{margin:8px 0}
.gap{height:8px}
code{background:var(--code);border-radius:4px;padding:1px 5px;font-size:.875em;font-family:ui-monospace,Consolas,monospace;overflow-wrap:anywhere}
kbd{border:1px solid var(--field);border-radius:3px;padding:0 4px;font-size:.85em;font-family:inherit}
main img{max-width:100%;height:auto;border:1px solid var(--rule);border-radius:6px}
a.gl{color:inherit;text-decoration:underline dotted var(--ink3);text-underline-offset:3px;cursor:help}
a.gl:hover{color:var(--accent);text-decoration-color:var(--accent)}
.org{background:var(--org);border:1px dashed var(--phline);border-radius:3px;padding:1px 6px;font-size:.9em;color:var(--ink)}
.ph{background:var(--ph);border-bottom:2px dashed var(--phline);border-radius:3px;padding:0 3px}
.ph.filled{background:none;border-bottom:2px solid var(--phline)}
.check{display:block;margin:18px 0;padding:12px 16px;border:1px solid var(--rule);border-left:4px solid var(--ok);
border-radius:4px;background:var(--ok-soft)}
.check .lbl{display:flex;align-items:center;gap:6px;margin:0 0 4px;font-size:.8125rem;font-weight:700;color:var(--ok);
text-transform:uppercase;letter-spacing:.04em}
.check .lbl svg{width:14px;height:14px;flex:none}
.check .lbl a.gl{color:inherit}
.check p{margin:0}
.example{margin:18px 0;padding:14px 16px;border:1px solid var(--rule);border-radius:6px;background:var(--bg2)}
.example .tag{display:inline-block;margin:0 0 6px;padding:1px 8px;border-radius:10px;font-size:.75rem;font-weight:600;
background:var(--surface);border:1px solid var(--rule2);color:var(--ink2)}
.example p{margin:0}
.example p.tag{margin:0 0 6px}
.question{font-weight:600}
details.answer{margin:16px 0;border:1px solid var(--rule);border-radius:6px;background:var(--surface);box-shadow:var(--shadow)}
details.answer summary{display:flex;align-items:center;gap:10px;padding:12px 16px;cursor:pointer;list-style:none;
font-weight:600;color:var(--accent)}
details.answer summary::-webkit-details-marker{display:none}
details.answer summary::before{content:"";width:7px;height:7px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;
transform:rotate(-45deg);transition:transform .15s}
details.answer[open] summary::before{transform:rotate(45deg)}
details.answer[open] summary{border-bottom:1px solid var(--rule)}
details.answer .a{padding:4px 16px 12px}
.howto{margin:16px 0;padding:10px 14px;border-left:4px solid var(--phline);background:var(--bg2);border-radius:0 4px 4px 0;font-size:.95rem}
.setup{margin:16px 0;padding:12px 14px;background:var(--surface);border:1px solid var(--rule);border-radius:6px}
.setup label{display:block;font-size:.875rem;color:var(--ink2);margin-bottom:5px}
.setup input{width:100%;padding:7px 9px;font:inherit;border:1px solid var(--field);border-radius:4px;background:var(--bg);color:var(--ink)}
.carried{margin:6px 0 0;font-size:.8rem;color:var(--ink2)}
.prompt{margin:16px 0;background:var(--code);border:1px solid var(--rule);border-left:4px solid var(--rule2);border-radius:4px;
padding:12px 16px;display:flex;flex-wrap:wrap;gap:8px 12px;align-items:flex-start}
.prompt .t{flex:1 1 260px;white-space:pre-wrap;overflow-wrap:anywhere}
.prompt .lab{flex-basis:100%;margin:0;font-size:.85rem;font-weight:600;color:var(--ink2)}
.prompt .after{flex-basis:100%;margin:0;font-size:.875rem;color:var(--ink2)}
.prompt.tutor{border-left-color:var(--accent)}
.prompt.tool{border-left-color:var(--ok)}
.prompt.orgprompt{background:var(--org);border:1px dashed var(--phline);border-left:4px dashed var(--phline)}
.prompt.frame{background:var(--bg2);border:1px dashed var(--rule2);border-left:4px solid var(--accent)}
button.copy{font:inherit;font-size:.85rem;font-weight:600;padding:4px 14px;cursor:pointer;border:1px solid var(--rule2);
background:var(--surface);color:var(--ink);border-radius:4px}
button.copy:hover{border-color:var(--ink2)}
button.copy.ok{background:var(--ok);border-color:var(--ok);color:var(--ok-ink)}
.tw{overflow-x:auto;margin:16px 0}
table{border-collapse:collapse;width:100%;font-size:.95rem}
th,td{border:1px solid var(--rule);padding:7px 10px;text-align:left;vertical-align:top}
thead th{background:var(--bg2)}
tbody th{font-weight:600}
.toc-inline{margin:4px 0 18px;padding:8px 14px;border:1px solid var(--rule);border-radius:6px;background:var(--surface)}
.toc-inline summary{cursor:pointer;font-weight:600;font-size:.9rem}
.toc-inline ul{list-style:none;margin:6px 0 2px;padding:0}.toc-inline li{margin:3px 0}
.toc-inline li.l3{padding-left:14px}.toc-inline a{text-decoration:none}
/* a step's footer: mark done, and the quiet "stuck" link */
.steprow{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;margin:26px 0 8px}
button.mark{display:inline-flex;align-items:center;gap:10px;font:inherit;font-size:.9rem;font-weight:600;padding:7px 14px 7px 10px;
cursor:pointer;border:1px solid var(--rule2);border-radius:4px;background:var(--surface);color:var(--ink)}
button.mark:hover{border-color:var(--ink2)}
button.mark .box{flex:none;width:18px;height:18px;border:2px solid var(--ink3);border-radius:3px;display:grid;place-items:center}
button.mark .box svg{width:12px;height:12px;display:none}
button.mark[aria-pressed="true"]{background:var(--ok-soft);border-color:var(--ok);color:var(--ok)}
button.mark[aria-pressed="true"] .box{background:var(--ok);border-color:var(--ok);color:var(--ok-ink)}
button.mark[aria-pressed="true"] .box svg{display:block}
button.unitmark{margin:20px 0 4px}
button.stuck{font:inherit;font-size:.85rem;padding:6px 2px;border:0;background:none;color:var(--ink2);cursor:pointer;
text-decoration:underline;text-decoration-color:var(--rule2);text-underline-offset:3px;text-align:left}
button.stuck:hover{color:var(--accent);text-decoration-color:currentColor}
button.stuck.ok{color:var(--ok);text-decoration:none;font-weight:600}
/* what comes next */
.pager{margin:64px 0 0}
.nextunit{padding:24px 0 0;border-top:1px solid var(--rule)}
.nextunit .lbl{margin:0 0 4px;font-size:.875rem;color:var(--ink2)}
.nextunit h2{margin:0 0 18px;font-size:1.25rem;border:0;padding:0}
.btn{display:inline-flex;align-items:center;gap:8px;padding:9px 22px;border-radius:4px;font-weight:600;text-decoration:none;
background:var(--accent);color:var(--accent-ink);border:1px solid var(--accent)}
.btn:hover{filter:brightness(1.08);text-decoration:none}
.btn svg{width:14px;height:14px}
.nextrow{display:flex;flex-wrap:wrap;gap:14px 22px;align-items:center}
.nextrow .prev,.nextrow .next{font-size:.9rem;color:var(--ink2);text-decoration:none}
.nextrow .prev:hover,.nextrow .next:hover{color:var(--accent);text-decoration:underline}
.nextrow.quiet{padding-top:20px;border-top:1px solid var(--rule)}
.nextrow.quiet .next{margin-left:auto;font-weight:600;color:var(--accent)}
.pagefoot{max-width:760px;margin:-40px var(--gut) 0;padding:14px 0 32px;display:flex;flex-wrap:wrap;gap:4px 18px;
font-size:.82rem;color:var(--ink3)}
.pagefoot a{margin-left:auto;color:var(--ink3);text-decoration:none}
.pagefoot a:hover{color:var(--accent);text-decoration:underline}
.nudge{margin:14px 0 0;font-size:.85rem;color:var(--ink2)}
.nudge:empty{display:none}
/* a training's home: progress and resume; the programme's list of trainings */
.course{margin:20px 0 8px;padding:16px 20px 8px;border:1px solid var(--rule);border-radius:8px;background:var(--surface);box-shadow:var(--shadow)}
.course .meta{margin:0;font-size:.9rem;color:var(--ink2)}
.overall{display:flex;align-items:center;gap:12px;margin:10px 0 0;font-size:.9rem;font-weight:600}
#overall{white-space:nowrap}
.bar{flex:0 1 260px;min-width:80px;height:6px;border-radius:3px;background:var(--rule);overflow:hidden}
.bar span{display:block;height:100%;width:0;background:var(--ok)}
.cta{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:16px 0 10px}
.cta span{color:var(--ink2);font-size:.9rem}
.units{list-style:none;padding:0;margin:12px 0;display:grid;gap:10px}
main .units{padding-left:0}
.unitcard{position:relative;margin:0;padding:12px 16px;border:1px solid var(--rule);border-left:4px solid var(--rule2);
border-radius:6px;background:var(--surface)}
.unitcard:hover{border-color:var(--accent)}
.unitcard a{font-weight:600;font-size:1.05rem;text-decoration:none}
.unitcard a::after{content:"";position:absolute;inset:0}
.unitcard .un{display:block;font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3)}
.unitcard .uo{margin:4px 0;color:var(--ink2);font-size:.95rem}
.unitcard .um{margin:2px 0 0;font-size:.85rem;color:var(--ink2)}
.unitcard .us{margin:0;font-size:.85rem;font-weight:600;color:var(--ink3)}
.unitcard.going{border-left-color:var(--accent)}.unitcard.going .us{color:var(--accent)}
.unitcard.done{border-left-color:var(--ok)}.unitcard.done .us{color:var(--ok)}
/* widths: below about 1000px the outline folds behind the Outline button */
@media (max-width:999.98px){
.menu{display:inline-flex}
.layout{grid-template-columns:minmax(0,1fr)}
.side{position:fixed;left:0;top:var(--hdr);z-index:25;width:min(340px,88vw);transform:translateX(-105%);visibility:hidden;
transition:transform .2s,visibility .2s;box-shadow:4px 0 16px rgba(0,0,0,.15)}
body.nav-open .side{transform:none;visibility:visible;transition:transform .2s}
.scrim{display:block;position:fixed;inset:var(--hdr) 0 0;z-index:24;background:rgba(0,0,0,.35);opacity:0;visibility:hidden;
transition:opacity .2s,visibility .2s}
body.nav-open .scrim{opacity:1;visibility:visible}
.ohead{position:relative;padding-right:56px}
.oclose{display:flex;position:absolute;right:10px;top:14px;width:40px;height:40px;align-items:center;justify-content:center;
border:0;border-radius:6px;background:none;color:var(--ink2);cursor:pointer;font-size:1.4rem;line-height:1}
.oclose:hover{background:var(--cur);color:var(--ink)}
}
@media (max-width:900px){.crumbs li.prog{display:none}.crumbs li.prog+li::before{display:none}
.unitpos .long{display:none}.unitpos .short{display:inline}}
@media (max-width:680px){
.site{gap:8px;padding:0 12px}
.search{width:auto;flex:1}
.results{position:fixed;left:8px;right:8px;top:calc(var(--hdr) - 6px);width:auto}
.content{--gut:16px}
main h1{font-size:1.75rem}
main h2{font-size:1.3rem;margin-top:44px}
main h2.step{margin-top:32px;padding-top:32px}
main{padding-top:20px}
}
@media (max-width:420px){.brand{display:none}}
@media (forced-colors:active){.ph,.org{border-color:CanvasText}.line span{background:Highlight}
.ostep.here,.omore a[aria-current]{outline:2px solid CanvasText}.oring .arc{stroke:CanvasText}.odot{forced-color-adjust:none}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}"""

JS = r"""(function(){
function lget(k,d){try{var v=localStorage.getItem(k);return v===null?d:v;}catch(e){return d;}}
function lput(k,v){try{localStorage.setItem(k,v);}catch(e){}}
var say=document.getElementById("say");
var TICK='<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M2.5 6.3l2.3 2.3L9.6 3.6"/></svg>';
/* light or dark: the reader's choice is remembered; otherwise the system's */
var rootEl=document.documentElement, tb=document.getElementById("theme");
var saved=lget("kit.theme",""); if(saved==="light"||saved==="dark") rootEl.setAttribute("data-theme",saved);
function isDark(){var t=rootEl.getAttribute("data-theme");return t?t==="dark":!!(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches);}
function labelTheme(){tb.setAttribute("aria-label",isDark()?"Switch to light theme":"Switch to dark theme");}
labelTheme();
if(window.matchMedia){var mq=matchMedia("(prefers-color-scheme: dark)"); if(mq.addEventListener) mq.addEventListener("change",labelTheme);}
tb.addEventListener("click",function(){var t=isDark()?"light":"dark";rootEl.setAttribute("data-theme",t);lput("kit.theme",t);labelTheme();});
/* the folder box fills <your folder> in this page's prompts */
var FK="kit.folder", fin=document.getElementById("folder");
function paintFolder(){
  var f=fin?(fin.value||"").trim():"";
  document.querySelectorAll(".ph[data-folder]").forEach(function(p){
    p.textContent=f||"<your folder>"; p.classList.toggle("filled",!!f);});
}
if(fin){
  fin.value=lget(FK,"");
  if(fin.value){var n=document.createElement("p");n.className="carried";
    n.textContent="Filled in from an earlier page. Change it if this page is about a different folder.";
    fin.insertAdjacentElement("afterend",n);}
  fin.addEventListener("input",function(){lput(FK,fin.value);paintFolder();});
}
paintFolder();
function copyText(b,txt,open,after){
  function done(ok){
    b.classList.toggle("ok",ok); var old=b.getAttribute("data-label")||b.textContent; b.setAttribute("data-label",old);
    b.textContent=ok?"Copied":"Copy failed";
    if(after) after.hidden=!(ok&&open);
    say.textContent=ok?(open?"Copied. Change the highlighted part after you paste.":"Copied."):"Copy failed. Drag across the text to select it, then right-click it and select Copy.";
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
/* a unit's steps: each ends with "Mark this step done" and, where offered, the quiet "stuck" link */
var main=document.getElementById("main"), page=main.getAttribute("data-page");
var PK="kit.done."+location.pathname, done={};
try{done=JSON.parse(lget(PK,"{}"))||{};}catch(e){done={};}
var heads=[].slice.call(main.querySelectorAll("h2[id],h3[id]")).filter(function(h){return !h.closest(".pager");});
var isUnit=main.getAttribute("data-steps")==="1";
var steps=isUnit?heads.filter(function(h){return /^\d/.test(h.textContent);}):[];
var marks={}, ub=null, pagerEl=main.querySelector(".pager");
function save(){lput(PK,JSON.stringify(done));}
function markButton(label){
  var b=document.createElement("button"); b.type="button"; b.className="mark"; b.setAttribute("aria-label",label);
  b.innerHTML='<span class="box">'+TICK+'</span><span class="bt"></span>'; return b;
}
steps.forEach(function(h){
  var lv=+h.tagName[1], next=heads.slice(heads.indexOf(h)+1).filter(function(x){return +x.tagName[1]<=lv;})[0];
  var num=(h.textContent.match(/^\d+/)||[""])[0];
  var row=document.createElement("div"); row.className="steprow";
  var b=markButton("Mark step "+num+" done");
  b.addEventListener("click",function(){done[h.id]=!done[h.id];save();paint();
    say.textContent=done[h.id]?"Step "+num+" marked done.":"Step "+num+" marked not done.";});
  row.appendChild(b);
  if(main.getAttribute("data-stuck")==="1" && +num>=+(main.getAttribute("data-stuck-from")||1)){
    var s=document.createElement("button"); s.type="button"; s.className="stuck";
    s.textContent="Stuck on this step?";
    s.setAttribute("aria-label","Stuck on this step? Copy a question to ask for help with step "+num);
    s.title="Copies a question to ask for help";
    s.addEventListener("click",function(){
      var q=main.getAttribute("data-kit-open")==="1"
        ? "I am on step "+num+" of \""+page+"\" in the training folder. What does it ask me to do, and what should I see? Do not do it for me."
        : "I am working through the training \""+main.getAttribute("data-program")+"\", page \""+page+"\", step \""+h.textContent.trim()+"\". I will paste the step's text below. What does it ask me to do, and what should I see? Do not do it for me.";
      copyText(s,q,false,null);
    });
    row.appendChild(s);
  }
  (next||pagerEl).insertAdjacentElement("beforebegin",row);
  marks[h.id]=b;
});
if(isUnit&&!steps.length){
  ub=markButton("Mark this unit done"); ub.classList.add("unitmark");
  ub.addEventListener("click",function(){done.unit=!done.unit;save();paint();
    say.textContent=done.unit?"Unit marked done.":"Unit marked not done.";});
  (main.querySelector("h2")||pagerEl).insertAdjacentElement("beforebegin",ub);
}
/* progress across a training, read from what each unit page saved */
var ROOT=document.body.getAttribute("data-root");
var TRAININGS=(window.KIT_TRAININGS||[]).filter(function(t){return t.units.length;});
var OT=document.body.getAttribute("data-outline"), T=TRAININGS.filter(function(t){return t.f===OT;})[0]||null;
function unitState(u){
  var p=new URL(ROOT+u.u,location.href).pathname, d={};
  try{d=JSON.parse(lget("kit.done."+p,"{}"))||{};}catch(e){}
  return {p:p,d:d,n:u.ids.filter(function(i){return d[i];}).length,of:u.ids.length};
}
function trainingState(t){
  var s={done:0,any:0,frac:0,units:t.units.map(unitState)};
  s.units.forEach(function(r){if(r.n>=r.of) s.done++; if(r.n) s.any++; s.frac+=r.n/r.of;});
  return s;
}
function paintRing(ring,frac,all){
  var arc=ring.querySelector(".arc"), C=2*Math.PI*13, n=ring.querySelector(".n");
  if(!n.getAttribute("data-n")) n.setAttribute("data-n",n.textContent);
  arc.setAttribute("stroke-dasharray",(C*frac)+" "+C); arc.style.display=frac>0?"":"none";
  ring.classList.toggle("full",all); n.textContent=all?"✓":n.getAttribute("data-n");
}
function setProg(li,html){var pr=li.querySelector(".oprog"); if(html===null) pr.textContent=pr.getAttribute("data-base"); else pr.innerHTML=html;}
function paintOutline(){
  [].forEach.call(document.querySelectorAll(".ou[data-t]"),function(li){
    var t=TRAININGS.filter(function(x){return x.f===li.getAttribute("data-t");})[0]; if(!t) return;
    var s=trainingState(t), N=t.units.length, all=s.done===N;
    paintRing(li.querySelector(".oring"),s.frac/N,all);
    setProg(li,all?' &middot; <span class="ok">Done</span>':(s.any?" &middot; "+s.done+" of "+N+" units done":null));
  });
  if(!T) return null;
  var s=trainingState(T), N=T.units.length;
  [].forEach.call(document.querySelectorAll(".ou[data-u]"),function(li){
    var i=T.units.map(function(u){return u.u;}).indexOf(li.getAttribute("data-u")); if(i<0) return;
    var r=s.units[i], all=r.n>=r.of;
    paintRing(li.querySelector(".oring"),r.n/r.of,all);
    setProg(li,all?' &middot; <span class="ok">Done</span>':(r.n?" &middot; "+r.n+" of "+r.of+" done":null));
    [].forEach.call(li.querySelectorAll(".ostep"),function(a){
      var ok=!!r.d[a.getAttribute("data-id")]; a.classList.toggle("done",ok);
      a.querySelector(".ostate").textContent=ok?" (done)":"";
    });
  });
  document.getElementById("obar").style.width=(100*s.frac/N)+"%";
  document.getElementById("opct").textContent=(s.done===N?"✓ All ":"")+s.done+" of "+N+" units done · "+Math.round(100*s.frac/N)+"% complete";
  return s;
}
function paintCrumbs(s){
  if(!T||!s) return;
  var N=T.units.length, up=document.getElementById("unitpos"), line=document.getElementById("line");
  if(line) line.style.width=(100*s.frac/N)+"%";
  if(!up) return;
  var ci=-1; s.units.forEach(function(r,i){if(r.p===location.pathname) ci=i;});
  if(ci<0) return;
  var r=s.units[ci], pos="Unit "+(ci+1)+" of "+N, all=r.n>=r.of, long, short;
  if(r.of===1&&T.units[ci].ids[0]==="unit"){long=pos+(all?" · ✓ done":" · not done yet");short=pos+(all?" ✓":"");}
  else{long=pos+" · "+(all?"✓ all steps done":r.n+" of "+r.of+" steps");short=pos+(all?" ✓":" · "+r.n+"/"+r.of);}
  document.getElementById("upos-long").textContent=long;
  document.getElementById("upos-short").textContent=short;
  up.classList.toggle("all",all);
  up.title=s.done+" of "+N+" units done in "+T.name;
}
function paint(){
  steps.forEach(function(h){
    var d=!!done[h.id], b=marks[h.id];
    h.classList.toggle("done",d);
    b.setAttribute("aria-pressed",String(d));
    b.querySelector(".bt").textContent=d?"Step done":"Mark this step done";
  });
  if(ub){ub.setAttribute("aria-pressed",String(!!done.unit));ub.querySelector(".bt").textContent=done.unit?"Unit done":"Mark this unit done";}
  paintCrumbs(paintOutline());
  var nudge=document.getElementById("nudge");
  if(nudge){
    var left=steps.length?steps.filter(function(h){return !done[h.id];}).length:(done.unit?0:1);
    nudge.textContent=!left?(steps.length?"All steps in this unit are done.":"This unit is done."):
      (steps.length?left+" step"+(left===1?"":"s")+" in this unit not marked done yet.":"This unit is not marked done yet.")+" You can continue anyway and come back.";
  }
}
paint();
/* the programme's home: each training's progress */
[].forEach.call(document.querySelectorAll(".traincard"),function(li){
  var t=TRAININGS.filter(function(x){return x.f===li.getAttribute("data-training");})[0], us=li.querySelector(".us");
  if(!t||!us) return;
  var s=trainingState(t), all=s.done===t.units.length;
  var un=function(k){return k===1?" unit":" units";};
  us.textContent=all?"✓ All "+s.done+un(s.done)+" done":(s.any?s.done+" of "+t.units.length+un(t.units.length)+" done":"Not started");
  li.classList.toggle("done",all); li.classList.toggle("going",s.any>0&&!all);
});
/* a training's home: each unit's progress, and where to resume */
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
      label:j>=0&&ids[j]!=="unit"?"step "+(j+1)+" of "+ids.length+", "+labels[j]:"one step: mark it done when you have done it"};
  });
  var nDone=units.filter(function(u){return u.n>=u.of;}).length;
  var furthest=units.filter(function(u){return u.n>0;}).pop();
  var todo=units.filter(function(u){return u.n<u.of;});
  var nextU=furthest?(furthest.n<furthest.of?furthest:(todo.filter(function(u){return u.k>furthest.k;})[0]||todo[0])):null;
  document.getElementById("overall").textContent=nDone===units.length?"✓ All "+units.length+" units done":nDone+" of "+units.length+" units done";
  document.getElementById("bar").style.width=(100*units.reduce(function(s,u){return s+u.n/u.of;},0)/units.length)+"%";
  var cta=document.getElementById("cta"), note=document.getElementById("cta-note");
  if(nDone===units.length){cta.textContent="You have finished the path";cta.href=cards[units.length-1].querySelector("a").getAttribute("href")+"#you-have-finished-the-path";
    note.textContent="See what you can now do";}
  else if(nextU){cta.textContent="Continue with unit "+(nextU.k+1);cta.href=nextU.href;
    note.textContent="Next: "+nextU.label;}
}
/* the outline: a drawer below about 1000px, units that fold, and a marker that follows the reader down a unit */
var menu=document.getElementById("menu");
function closeNav(){document.body.classList.remove("nav-open");menu.setAttribute("aria-expanded","false");}
menu.addEventListener("click",function(){
  var open=document.body.classList.toggle("nav-open");
  menu.setAttribute("aria-expanded",String(open));
  if(open){var a=document.querySelector(".side a[aria-current]")||document.querySelector(".side a");a&&a.focus();}
});
document.addEventListener("keydown",function(e){
  if(e.key==="Escape"&&document.body.classList.contains("nav-open")){closeNav();menu.focus();}
});
document.getElementById("scrim").addEventListener("click",closeNav);
document.getElementById("oclose").addEventListener("click",function(){closeNav();menu.focus();});
[].forEach.call(document.querySelectorAll(".otoggle"),function(b){
  b.addEventListener("click",function(){var li=b.closest(".ou"), open=li.classList.toggle("open");b.setAttribute("aria-expanded",String(open));});
});
var hereLinks=[].slice.call(document.querySelectorAll(".ou.current .ostep"));
var hereHeads=hereLinks.map(function(a){return document.getElementById(a.getAttribute("data-id"));}).filter(Boolean);
function markHere(){
  if(!hereHeads.length) return;
  var at=hereHeads[0], lim=window.innerHeight*0.35;
  hereHeads.forEach(function(h){if(h.getBoundingClientRect().top<=lim) at=h;});
  if(window.innerHeight+window.scrollY>=document.documentElement.scrollHeight-4) at=hereHeads[hereHeads.length-1];
  hereLinks.forEach(function(a){var on=a.getAttribute("data-id")===at.id;a.classList.toggle("here",on);
    if(on) a.setAttribute("aria-current","location"); else a.removeAttribute("aria-current");});
}
var hereTick=false;
window.addEventListener("scroll",function(){if(!hereTick){hereTick=true;requestAnimationFrame(function(){hereTick=false;markHere();});}},{passive:true});
window.addEventListener("hashchange",markHere);
markHere();
hereLinks.forEach(function(a){a.addEventListener("click",function(){if(document.body.classList.contains("nav-open")) closeNav();});});
var side=document.getElementById("side"), curA=side.querySelector("a[aria-current]");
if(curA){side.scrollTop=Math.max(0,curA.offsetTop-side.clientHeight/2);}
/* search over every page of the kit */
var q=document.getElementById("q"), res=document.getElementById("results");
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
  var idx=window.KIT_INDEX||[], hits=[], weight={};
  words.forEach(function(w){
    var df=idx.filter(function(e){return (e.t+" "+e.s+" "+e.x).toLowerCase().indexOf(w)>=0;}).length;
    weight[w]=Math.log((idx.length+1)/(df+1))+0.1;
  });
  idx.forEach(function(e){
    var sec=e.s.toLowerCase(), pg=e.t.toLowerCase(), body=e.x.toLowerCase(), score=0;
    words.forEach(function(w){
      var s=(sec.indexOf(w)>=0?4:0)+(pg.indexOf(w)>=0?1:0)+(body.indexOf(w)>=0?1:0);
      if(s) score+=s*weight[w];
    });
    if(score) hits.push([score,e]);
  });
  hits.sort(function(a,b){return b[0]-a[0];});
  res.innerHTML=hits.length?hits.slice(0,10).map(function(h){var e=h[1];
    return '<li><a href="'+esc(ROOT+e.u)+'"><span class="rt">'+esc(e.s||e.t)+'</span><br><span class="rs">'+esc((e.s?e.t+": ":"")+snippet(e.x,words))+'</span></a></li>';}).join("")
    :'<li class="none">Nothing found. Try one word from the step you are on, or open <a href="'+esc(ROOT)+'troubleshooting.html">If something goes wrong</a>.</li>';
  res.hidden=false;
  say.textContent=hits.length?hits.length+" results":"No results";
}
q.addEventListener("input",search);
q.addEventListener("keydown",function(e){
  if(e.key==="Enter"){var t=res.querySelector("a");if(t){e.preventDefault();location.href=t.href;}}
  if(e.key==="ArrowDown"){var a=res.querySelector("a");if(a){e.preventDefault();a.focus();}}
  if(e.key==="Escape"){res.hidden=true;}
});
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
