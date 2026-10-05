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
SKILL_VERSION = "1.9"
PROGRAM_NAME = "Training programme"
# Who the learner asks for help, and where they paste a prompt for it.
ASSISTANT = "the assistant"
ASSISTANT_CHAT = "the assistant's chat box"
# Where practice happens when it is not the assistant's chat: the tool, screen or console the
# learner works in. Prompts marked <!-- tool --> are labelled with it.
PRACTICE_PLACE = "the tool"
# True when learners open the kit's folder where the assistant can read it. The "Stuck?" question
# carries the step's own words either way, so it never relies on kit files the assistant lacks.
KIT_OPEN_IN_ASSISTANT = True
# True gives each step a "Stuck on this step?" button that copies a question for ASSISTANT. Set it
# False when the help beside the learner is a person rather than an assistant.
STUCK_BUTTON = True
# The trainings, in the order the home page lists them. Each lives in its own folder with its own
# README.md. "path" lists its units in order: (file in the folder, name in the menu, time). A
# training with no path yet is shown as "coming later". "before" lists pages, by their place in
# the kit, that a learner goes through before unit 1, such as a setup page. "stuck_from" gives the
# first step on a unit that offers "Stuck on this step?"; 1 unless listed. The times are stand-ins:
# replace each with the time computed as maintaining/README.md, "Time estimates", says.
TRAININGS = [
    {"folder": "getting-started", "name": "Getting started", "level": "Beginner",
     "time": "about an hour",
     "path": [("introduction.md", "Introduction", "about five minutes"),
              ("start-here.md", "Start here", "about fifteen minutes"),
              ("lesson-one.md", "The first lesson", "about thirty minutes")],
     "before": [], "stuck_from": {}},
]
# The side menu's groups shared by every page: (group, open by default, [(file, name, anchor)]).
MENU_AFTER = [
    ("Help", True, [("troubleshooting.md", "When you are stuck", "when-you-are-stuck"),
                    ("troubleshooting.md", "Help", ""),
                    ("glossary.md", "Glossary", "")]),
    ("More", True, [("explanation.md", "Background", ""),
                    ("CHANGELOG.md", "What's new", "")]),
]
# Glossary words linked where first used on a page, and on-screen labels never to link.
GLOSSARY_TERMS = ["Check"]
UI_LABELS = ()
# Folders that are not learner pages.
NOT_FOR_LEARNERS = ("facilitator/", "sample-files/", "maintaining/", "read-in-browser/")
# Off by default: the assistant creates the practice files from complete requests on the page, so
# the training needs no download. Set a name, such as "training-files.zip", only when a later
# training truly needs ready-made files: the build then packs the learner pages (as markdown) and
# the practice files beside the web pages, and the request fetches the zip from there.
FILES_ZIP = ""
# ---- End of what a maintainer changes ----

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, ".."))
OUT_DIR = "read-in-browser"
OUT = os.path.join(KIT, OUT_DIR)
MARKER = re.compile(r"^<!--\s*(frame|tutor|tool|note|rate|workbook)\s*-->$")
# Folded content: everything between <!-- more: Label --> and <!-- /more --> opens on request.
MORE_OPEN = re.compile(r"^<!--\s*more:\s*(.+?)\s*-->$")
MORE_CLOSE = re.compile(r"^<!--\s*/more\s*-->$")
# What a learner can say of each objective at the end of a path (see <!-- rate --> in maintaining/README.md).
RATINGS = ("I can do this", "With the page open", "Not yet")
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
    if FILES_ZIP and full == FILES_ZIP:
        return rel(src, FILES_ZIP)
    if not full.endswith(".md") and os.path.isfile(os.path.join(KIT, full)):
        page_dir = os.path.dirname(os.path.join(OUT, out_name(src)))
        if full.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
            # A picture is copied in beside the pages, so it shows wherever the pages are served.
            dest = os.path.join(OUT, full)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(os.path.join(KIT, full), dest)
            return os.path.relpath(dest, page_dir).replace("\\", "/")
        # A practice file: link to it where it sits in the kit.
        return os.path.relpath(os.path.join(KIT, full), page_dir).replace("\\", "/")
    return None


def inline(text, src):
    # Bold first, so bold may wrap a link or span text and a link together.
    if "**" in text:
        parts = re.split(r"\*\*(.+?)\*\*", text)
        return "".join(("<b>%s</b>" if k % 2 else "%s") % inline_parts(p, src) for k, p in enumerate(parts))
    return inline_parts(text, src)


def inline_parts(text, src):
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


def prompt_text(raw):
    return html.escape(raw.replace("`", ""), quote=False)


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
        return ('<div class="prompt frame"><p class="lab">An example to write yours from:</p>'
                '<div class="t">%s</div></div>' % prompt_text(raw))
    first = re.sub(r"[`<>]", "", raw)
    first = first if len(first) <= 40 else first[:40].rsplit(" ", 1)[0] + "…"
    cls = {"tutor": "prompt tutor", "tool": "prompt tool"}.get(kind, "prompt")
    lab = {"tutor": '<p class="lab">Ask %s:</p>' % setting_html(ASSISTANT),
           "tool": '<p class="lab">Paste this into %s:</p>' % setting_html(PRACTICE_PLACE)}.get(kind, "")
    return ('<div class="%s">%s<div class="t">%s</div>'
            '<button class="copy" type="button" aria-label="Copy: %s">Copy</button></div>'
            % (cls, lab, prompt_text(raw), html.escape(first)))


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


LIST_ITEM = re.compile(r"^(- |\d+\.\s)")


def item_html(lines, src):
    h, text, kind = [], [], None

    def flush():
        if text:
            h.append(inline(" ".join(text), src))
            text.clear()
    j = 0
    while j < len(lines):
        ln = lines[j]
        m = MARKER.match(ln)
        if j and LIST_ITEM.match(ln):
            # A list nested inside this item: it and its indented lines render as a list of their own.
            flush()
            block = []
            while j < len(lines) and (LIST_ITEM.match(lines[j]) or lines[j].startswith(" ")):
                block.append(lines[j])
                j += 1
            h.append(render(block, src))
            continue
        j += 1
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
    # A note's or rating's key is the step it sits under and its place there, so rewording a question
    # keeps the learner's answer; renaming the step or reordering its notes does not.
    head, count = "top", {}

    def key(prefix):
        count[head] = count.get(head, 0) + 1
        return "%s-%s-%d" % (prefix, head, count[head])

    def misplaced(what):
        sys.exit("%s: a <!-- %s --> marker must be followed by %s, but the next block is %s. Move the marker "
                 "or remove it." % (src, kind, "a paragraph (the question)" if kind == "note" else "a list", what))
    while i < len(lines):
        ln, s = lines[i], lines[i].strip()
        m = MARKER.match(s)
        if m and kind in ("note", "rate"):
            misplaced("another marker")
        mo, mc = MORE_OPEN.match(s), MORE_CLOSE.match(s)
        if m and m.group(1) == "workbook":
            h.append(WORKBOOK_HERE)
            i += 1
        elif mo:
            h.append('<details class="more"><summary>%s</summary><div class="m">' % html.escape(mo.group(1)))
            i += 1
        elif mc:
            h.append("</div></details>")
            i += 1
        elif m:
            kind = m.group(1)
            i += 1
        elif not s:
            i += 1
        elif s.startswith("```"):
            # A file shown as it is: every line kept, nothing rendered inside it.
            i += 1
            body = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            h.append('<pre class="file"><code>%s</code></pre>' % html.escape("\n".join(body)))
        elif ln.startswith(("## ", "### ", "#### ")):
            if kind in ("note", "rate"):
                misplaced("a heading")
            level = len(ln.split(" ", 1)[0])
            t = ln[level + 1:].strip()
            head = slug(t) or head
            num = re.match(r"^(\d+)\.\s+(.*)$", t)
            if num:
                # A step's number is for screen readers only: on screen, numbers belong to the actions
                # inside a step and to the units in the outline, so a step shows its name alone.
                h.append('<h%d id="%s" class="step"><span class="sr">%s. </span>'
                         '<span class="tt">%s</span></h%d>' % (level, slug(t), num.group(1), inline(num.group(2), src), level))
            else:
                h.append('<h%d id="%s">%s</h%d>' % (level, slug(t), inline(t, src), level))
            i += 1
        elif s.startswith("> "):
            if kind in ("note", "rate"):
                misplaced("a prompt")
            # Consecutive "> " lines are one request, shown and copied one sentence to a line.
            parts = [s[2:]]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("> "):
                parts.append(lines[i].strip()[2:])
                i += 1
            h.append(prompt_block("\n".join(parts), kind))
            kind = None
        elif s.startswith("|"):
            if kind in ("note", "rate"):
                misplaced("a table")
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            h.append(table(rows, src))
        elif ln.startswith("- ") or re.match(r"^\d+\.\s", ln):
            if kind == "note":
                misplaced("a list")
            lkind = "ul" if ln.startswith("- ") else "ol"
            # A numbered list may resume after a prompt or a picture: "4." carries on from 3.
            first = int(re.match(r"^(\d+)\.", ln).group(1)) if lkind == "ol" else 1
            items = []
            while i < len(lines):
                cur = lines[i]
                if not cur.strip():
                    nxt = next((l for l in lines[i + 1:] if l.strip()), "")
                    # A rating list ends at its first blank line, so an ordinary list can follow it.
                    same = kind != "rate" and ((lkind == "ul" and nxt.startswith("- ")) or
                                               (lkind == "ol" and re.match(r"^\d+\.\s", nxt) and not re.match(r"^1\.\s", nxt)))
                    if same:
                        i += 1
                        continue
                    if nxt.startswith("   "):
                        items[-1].append("")
                        i += 1
                        continue
                    break
                mo = re.match(r"^(\d+\.\s+)(.*)$", cur) if lkind == "ol" else None
                if (lkind == "ul" and cur.startswith("- ")) or mo:
                    items.append([mo.group(2) if mo else cur[2:]])
                    width = len(mo.group(1)) if mo else 2
                elif cur.startswith(" "):
                    # Keep indentation beyond the item's own, so a nested list survives.
                    lead = len(cur) - len(cur.lstrip(" "))
                    items[-1].append(cur[min(lead, width):])
                else:
                    break
                i += 1
            if kind == "rate":
                kind = None
                h.append(rating_list(items, src, key("rate")))
                continue
            opening = '<ol start="%d">' % first if first > 1 else "<%s>" % lkind
            h.append("%s%s</%s>" % (opening, "".join("<li>%s</li>" % item_html(it, src) for it in items), lkind))
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("> ", "|", "<!--")) \
                    and not lines[i].startswith(("#", "- ")) and not re.match(r"^\d+\.\s", lines[i]):
                para.append(lines[i].strip())
                i += 1
            text = " ".join(para)
            if kind == "rate":
                misplaced("a paragraph")
            if kind == "note":
                # The paragraph is the question; the box under it keeps the learner's answer.
                kind = None
                nid = key("note")
                shown = inline(text, src)
                h.append('<div class="note" data-note="%s" data-u="%s" data-label="%s"><label for="%s">%s</label>'
                         '<textarea id="%s" rows="3" autocomplete="off"></textarea>%s</div>'
                         % (nid, html.escape(out_name(src)), plain_attr(shown), nid, shown, nid, kept_line(src)))
                continue
            ans = re.match(r"^(Check your answer|Answers):\s*", text)
            if ans:
                if h and h[-1].startswith("<p>") and h[-1].endswith("?</p>"):
                    h[-1] = '<p class="question">' + h[-1][3:]
                h.append('<details class="answer"><summary>Show the answer</summary><div class="a"><p>'
                         '<span class="sr">%s: </span>%s</p></div></details>' % (ans.group(1), inline(text[ans.end():], src)))
                continue
            imp = re.match(r"^(\*\*)?Important:(\*\*)?\s*", text)
            if imp:
                # A fact that, missed, would leave the learner believing something wrong. Rare by design.
                h.append('<div class="callout" role="note"><p><b class="lbl">Important:</b> %s</p></div>'
                         % inline(text[imp.end():], src))
                continue
            chk = re.match(r"^(\*\*)?Check:(\*\*)?\s*", text)
            if chk:
                after = ("**" if chk.group(1) and not chk.group(2) else "") + text[chk.end():]
                # A quiet label in the body's colour, run in with the text; the glossary's meaning of
                # "Check" rides on the label as a tooltip, never as a link inside it.
                meaning = GLOSSARY_DEFS.get("check") if "Check" in GLOSSARY_TERMS else None
                h.append('<div class="check"><p><b class="lbl"%s>Check:</b> %s</p></div>'
                         % (' title="%s"' % html.escape(meaning) if meaning else "", inline(after, src)))
                continue
            whole = text[1:-1] if text.startswith("`Example") and text.endswith("`") and text.count("`") == 2 else text
            ex = re.match(r"^(Example\b[^:`]{0,80}):\s*", whole)
            if ex:
                h.append('<div class="example"><p class="tag">%s<span class="sr">:</span></p><p>%s</p></div>'
                         % (html.escape(ex.group(1), quote=False), inline(whole[ex.end():], src)))
                continue
            h.append("<p>%s</p>" % inline(text, src))
    return "\n".join(h)


WORKBOOK_HERE = '<div id="workbook-here"></div>'


def workbook_of(t):
    """A training's workbook page, where the notes and ratings from its pages are gathered; None if it has none."""
    wb = in_training(t, "workbook.md") if t else None
    return wb if wb in FILES else None


def kept_line(src):
    wb = workbook_of(page_training(src))
    where = ' It is also in <a href="%s">your workbook</a>.' % rel(src, out_name(wb)) if wb and wb != src else ""
    return '<p class="kept">Kept in this browser only.%s</p>' % where


def plain_attr(shown):
    """Rendered text as a plain attribute value, escaped once."""
    return html.escape(html.unescape(re.sub(r"<[^>]+>", "", shown)))


def radios(name):
    return "".join('<label><input type="radio" name="%s" value="%d" autocomplete="off"> %s</label>'
                   % (name, k, html.escape(r)) for k, r in enumerate(RATINGS))


def rating_list(items, src, base):
    """Each item, usually an objective, with a choice of how sure the learner is of it."""
    rows = []
    for n, it in enumerate(items, 1):
        rid = "%s-%d" % (base, n)
        shown = inline(" ".join(l.strip() for l in it if l.strip()), src)
        rows.append('<li class="note rate" data-note="%s" data-u="%s" data-label="%s"><fieldset><legend>%s</legend>'
                    '<div class="opts">%s</div></fieldset></li>'
                    % (rid, html.escape(out_name(src)), plain_attr(shown), shown, radios(rid)))
    return '<ul class="rates" role="list">%s</ul>%s' % ("".join(rows), kept_line(src))


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
    _t["workbook"] = workbook_of(_t)
UNITS = {}
for _t in TRAININGS:
    for _n, (_f, _, _time) in enumerate(_t["path"], 1):
        UNITS[in_training(_t, _f)] = (_t, _n, _time)


ORDER = ["README.md"]
for _t in TRAININGS:
    _index = [in_training(_t, "how-to/README.md")] if _t["recipes"] else []
    _wb = [_t["workbook"]] if _t["workbook"] else []
    for _f in [_t["readme"]] + _t["before"] + _t["units"] + _index + _t["recipes"] + _wb:
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
    """The steps a unit page lists in its outline, as (id, label); a unit with no numbered steps has one
    entry, ('unit', its name), and lists none. Progress is by unit, never by step."""
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
        start, note = first, "%s, %s" % (html.escape(unit_name(first)), html.escape(first_time))
    return ('<section class="course" aria-label="Your progress">'
            '<p class="meta">%s &middot; %d units &middot; %s</p>'
            '<p class="cta"><a class="btn" id="cta" href="%s">Go to unit 1</a>'
            '<span id="cta-note">%s</span></p></section>'
            % (html.escape(t["level"]), n_units, html.escape(t["time"]), rel(md, out_name(start)), note))


def unit_cards(t, md):
    lis = []
    for n, (target, title, outcome) in enumerate(list_items(md, "## The path", True), 1):
        text = outcome[:1].upper() + outcome[1:]
        lis.append('<li class="unitcard" data-u="%s">'
                   '<span class="un">Unit %d%s</span><a href="%s">%s</a><p class="uo">%s</p>'
                   '<p class="us">Not started</p></li>'
                   % (html.escape(out_name(target)), n,
                      (" &middot; " + html.escape(t["path"][n - 1][2])) if n <= len(t["path"]) else "",
                      html.escape(rel(md, out_name(target))), html.escape(title), inline(text, md)))
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
    return title_of(md)


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def ring(label):
    return ('<span class="oring" aria-hidden="true"><svg viewBox="0 0 32 32"><circle class="trk" cx="16" cy="16" r="13"/>'
            '<circle class="arc" cx="16" cy="16" r="13" transform="rotate(-90 16 16)" stroke-dasharray="0 82" '
            'style="display:none"/></svg><span class="n">%s</span></span>' % label)


def outline(md):
    """The left-hand outline: every training, always, so the learner sees the whole programme; the
    training the page belongs to is open, with its units and their steps. Then the help pages, under More."""
    t = outline_training(md)

    def cur(target):
        return ' aria-current="page"' if target == md else ""

    def link(target, text, count=""):
        mark = ' aria-current="page"' if target == md else (' aria-current="true"' if count and md in t["recipes"] else "")
        return '<li><a href="%s"%s>%s%s</a></li>' % (
            html.escape(rel(md, out_name(target))), mark, html.escape(text),
            '<span class="cnt"><span class="sr">, </span>%s</span>' % count if count else "")
    close = '<button class="oclose" id="oclose" type="button" aria-label="Close the outline">&times;</button>'
    trains = []
    for x in TRAININGS:
        mark = ' aria-current="true"' if x is t else ""
        meta = html.escape(x["level"]) if x["path"] else "Coming later"
        trains.append('<li class="ot ou%s" data-t="%s"><a class="otrow" href="%s"%s><span class="oname">%s</span>'
                      '<span class="sr">, </span><span class="olevel">%s<span class="oprog" data-base=""></span></span></a></li>'
                      % ("" if x["path"] else " later", html.escape(x["folder"]), rel(md, out_name(x["readme"])),
                         mark, html.escape(x["name"]), meta))
    block = ""
    if t:
        head = ('<div class="ohead"><a class="otitle" href="%s"%s>%s</a>'
                '<p class="ototal">%s &middot; %s</p><div class="obar" aria-hidden="true"><span id="obar"></span></div>'
                '<p class="opct" id="opct"></p></div>'
                % (rel(md, out_name(t["readme"])), cur(t["readme"]), html.escape(t["name"]),
                   plural(len(t["units"]), "unit"), html.escape(t["time"])))
        before = "".join(link(f, nav_title(f)) for f in t["before"])
        rows = []
        for n, (u, (_, _, time)) in enumerate(zip(t["units"], t["path"]), 1):
            name = unit_name(u)
            steps = unit_steps(u)
            here = u == md
            base = "" if steps[0][0] == "unit" else " &middot; " + plural(len(steps), "step")
            # One line per unit: its ring and its name. The time and step count are said on the unit's
            # own page and in the row's tooltip; the full line stays for screen readers.
            tip = "Unit %d · %s%s" % (n, time, "" if steps[0][0] == "unit" else " · " + plural(len(steps), "step"))
            row = ('<a class="orow" href="%s"%s>%s<span class="otext" title="%s"><span class="oname">%s</span><span class="otime" aria-hidden="true">%s</span>'
                   '<span class="ometa">Unit %d &middot; %s<span class="oprog" data-base="%s">%s</span></span></span></a>'
                   % (rel(md, out_name(u)), cur(u), ring(n), html.escape(tip), html.escape(name), html.escape(time[:1].upper() + time[1:]), n, html.escape(time),
                      base, base))
            toggle = sub = ""
            if base:
                page = "" if here else rel(md, out_name(u))
                sub = '<ol class="osteps" id="os%d" aria-label="Steps in unit %d">%s</ol>' % (n, n, "".join(
                    '<li><a class="ostep" href="%s#%s" data-id="%s"><span class="odot" aria-hidden="true"></span>'
                    '<span class="olab">%s</span></a></li>' % (page, i, i, label)
                    for i, label in steps))
                toggle = ('<button class="otoggle" type="button" aria-expanded="%s" aria-controls="os%d">'
                          '<span class="sr">Steps in unit %d</span>%s</button>'
                          % ("true" if here else "false", n, n, CHEVRON_SVG))
            rows.append('<li class="ou%s" data-u="%s"><div class="ohd">%s%s</div>%s</li>'
                        % (" current open" if here else "", out_name(u), row, toggle, sub))
        after = ""
        if t["workbook"]:
            after += link(t["workbook"], nav_title(t["workbook"]))
        if t["recipes"]:
            after += link(in_training(t, "how-to/README.md"), "Practice recipes", str(len(t["recipes"])))
        block = ('<div class="ocur">%s%s<ol class="ounits" aria-label="Units in %s">%s</ol>%s</div>'
                 % (head, '<ul class="oextras">%s</ul>' % before if before else "", html.escape(t["name"]),
                    "".join(rows), '<ul class="oextras">%s</ul>' % after if after else ""))
    lis = []
    for _, _, items in MENU_AFTER:
        for f, text, anchor in items:
            href = rel(md, out_name(f)) + ("#" + anchor if anchor else "")
            lis.append('<li><a href="%s"%s>%s</a></li>' % (html.escape(href), cur(f) if not anchor else "", html.escape(text)))
    return ('<nav id="side" class="side" aria-label="Course outline"><div class="otop"><p class="omh" id="oth">Trainings</p>%s</div>'
            '<ol class="otrains" aria-labelledby="oth">%s</ol>%s'
            '<div class="omore"><p class="omh" id="omh">More</p><ul aria-labelledby="omh">%s</ul></div></nav>'
            '<div class="scrim" id="scrim" aria-hidden="true"></div>' % (close, "".join(trains), block, "".join(lis)))


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
        # On a unit, this button is what marks the unit complete (see the script); nothing is ticked per step.
        nudge = ('<p class="nudge" id="nudge" aria-live="polite" data-btn="%s"></p>' % btn) if md in UNITS else ""
        done = ' data-complete="1"' if md in UNITS else ""
        # The end of a path is where a learner looks for what to do next, so the optional recipes are offered there.
        extra = ('<p class="lbl">Optional: <a href="%s">Practice recipes</a>, new tasks that use what this training taught</p>'
                 % rel(md, out_name(in_training(t, "how-to/README.md")))) if not next_ and t["recipes"] else ""
        return ('<nav class="pager" aria-label="What comes next"><div class="nextunit"><p class="lbl">%s</p><h2>%s</h2>'
                '<div class="nextrow"><a class="btn" href="%s"%s>%s%s</a>%s</div>%s%s</div></nav>'
                % (lbl, html.escape(title), href, done, btn, ARROW_SVG, back, extra, nudge))
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
        pid = ' id="pager-next"' if t and md == t["readme"] else ""
        links.append('<a class="next"%s href="%s">Next: %s &rsaquo;</a>' % (pid, rel(md, out_name(next_)), html.escape(nav_title(next_))))
    elif t and md in t["recipes"]:
        # The last recipe would otherwise offer only "Previous"; the training's home is where to go next.
        links.append('<a class="next" href="%s">Back to %s &rsaquo;</a>' % (rel(md, out_name(t["readme"])), html.escape(t["name"])))
    return '<nav class="pager" aria-label="Previous and next page"><div class="nextrow quiet">%s</div></nav>' % "".join(links)


def page_foot(md):
    """Quiet facts said once, at the foot of every page: when this page last changed, and the kit's
    version, which links to What's new."""
    day = PAGE_DATES.get(md) or KIT_DATE
    updated = '<span>Last updated %s</span>' % day if day else ""
    return ('<footer class="pagefoot">%s<a href="%s">Version %s</a></footer>'
            % (updated, rel(md, out_name(CHANGELOG)), html.escape(KIT_VERSION)))


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
<main id="main" data-steps="{steps}" data-page="{page}" data-stuck-from="{stuckfrom}" data-kit-open="{kitopen}" data-stuck="{stuck}" data-program="{program}" data-assistant="{assistant}" data-chat="{chat}">
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
# Elements never given a glossary link, by class: a prompt's text, a marked blank, and every label the
# page sets on a block (Check, Example, a prompt's "Ask ..." line, a card's unit number or status).
NO_LINK_CLASSES = {"t", "org", "lab", "lbl", "tag", "un", "us", "unit"}
# Glossary terms that are also the name of a label the page draws (see link_glossary).
LABEL_WORDS = ("Check",)


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
    # A term that names one of the page's own labels is explained on the label (its tooltip); in
    # running text the same word is nearly always the ordinary verb ("check which..."), so it is not linked.
    todo = {t.lower(): t for t in GLOSSARY_TERMS if t not in LABEL_WORDS}
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
                cls = re.search(r'class="([^"]*)"', attrs)
                blocked = tag in NO_LINK or bool(cls and set(cls.group(1).split()) & NO_LINK_CLASSES)
                if blocked or stack:
                    stack.append(tag)
            continue
        if stack or not todo:
            continue
        masked = part
        for ui in UI_LABELS + tuple(x["name"] for x in TRAININGS):
            masked = masked.replace(ui, "\0" * len(ui))
        # Every term's first use in this text, plural included, longest term first so a shorter one
        # never claims part of a longer one.
        spans = []
        for key in sorted(todo, key=len, reverse=True):
            for mo in re.finditer(r"(?<![\w-])(%ss?)(?![\w-])" % re.escape(key), masked, flags=re.I):
                if all(mo.end() <= a or mo.start() >= b for a, b, _ in spans):
                    spans.append((mo.start(), mo.end(), key))
                    break
        for a, b, key in sorted(spans, reverse=True):
            term = todo.pop(key)
            part = part[:a] + '<a class="gl" href="%s#%s" title="%s">%s</a>' % (
                href, slug(term), html.escape(GLOSSARY_DEFS.get(slug(term), "Glossary")), part[a:b]) + part[b:]
        parts[n] = part
    return "".join(parts)


NOTES = {}


def gather_notes(rest):
    """A page's notes and ratings, in order, each with the step heading it sits under."""
    found, under = [], ("", "")
    for m in re.finditer(r'<h([23]) id="([^"]+)"[^>]*>(.*?)</h\1>|<(?:div|li) class="(note(?: rate)?)" data-note="([^"]+)" '
                         r'data-u="([^"]+)" data-label="([^"]*)"', rest):
        if m.group(1):
            under = (m.group(2), re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(3)))).strip())
        else:
            found.append({"rate": m.group(4) == "note rate", "id": m.group(5), "u": html.unescape(m.group(6)),
                          "label": html.unescape(m.group(7)), "step": under})
    return found


def workbook_section(t, md):
    """The workbook page's body: every note and rating from the training's pages, under the unit and step
    it came from, with the same boxes, so an answer can be read or changed in either place."""
    parts, n = [], 0
    for page in [t["readme"]] + t["before"] + t["units"] + t["recipes"]:
        notes = NOTES.get(page) or []
        if not notes:
            continue
        head = ("Unit %d: %s" % (UNITS[page][1], unit_name(page))) if page in UNITS else \
            (t["name"] if page == t["readme"] else nav_title(page))
        parts.append('<h2 id="wb-%s">%s</h2>' % (slug(head), html.escape(head)))
        step, rates = None, []
        for e in notes + [None]:
            if rates and (e is None or not e["rate"]):
                parts.append('<ul class="rates" role="list">%s</ul>' % "".join(rates))
                rates = []
            if e is None:
                break
            if (e["step"], e["rate"]) != step:
                step = (e["step"], e["rate"])
                if e["step"][0]:
                    name = "How sure you are of each" if e["rate"] else e["step"][1]
                    parts.append('<h3><a href="%s#%s">%s</a></h3>' % (rel(md, out_name(page)), e["step"][0], html.escape(name)))
            n += 1
            wid = "wb%d" % n
            attrs = 'data-note="%s" data-u="%s"' % (e["id"], html.escape(e["u"]))
            if e["rate"]:
                rates.append('<li class="note rate" %s><fieldset><legend>%s</legend><div class="opts">%s</div></fieldset></li>'
                             % (attrs, html.escape(e["label"]), radios(wid)))
            else:
                parts.append('<div class="note" %s><label for="%s">%s</label>'
                             '<textarea id="%s" rows="3" autocomplete="off"></textarea></div>'
                             % (attrs, wid, html.escape(e["label"]), wid))
    acts = ('<div class="wbacts"><button type="button" class="btn" id="wb-download">Download a copy</button>'
            '<button type="button" class="copy" id="wb-print">Print or save as PDF</button></div>')
    if not parts:
        return '<section class="workbook"><p class="kept">Nothing here yet: this training has no notes to write.</p></section>'
    return '<section class="workbook">%s%s</section>' % (acts, "".join(parts))


def write(md):
    lines = read(md)
    title = title_of(md)
    rest = link_glossary(md, render(lines[1:], md))
    NOTES[md] = gather_notes(rest)
    if WORKBOOK_HERE in rest:
        rest = rest.replace(WORKBOOK_HERE, workbook_section(training_of(md), md))
    INDEX.extend(search_entries(md, title, re.sub(r'<p class="kept">.*?</p>|<div class="opts">.*?</div>|'
                                                  r'<div class="wbacts">.*?</div>', " ", rest, flags=re.S)))
    t = training_of(md)
    if md == "README.md":
        a = rest.index('<h2 id="the-trainings">')
        b = rest.find("<h2", a + 1) % (len(rest) + 1)
        rest = rest[:a] + '<h2 id="the-trainings">The trainings</h2>\n' + training_cards() + "\n" + rest[b:]
    elif t and t["path"] and md == t["readme"]:
        a = rest.index('<h2 id="the-path">')
        b = rest.find("<h2", a + 1) % (len(rest) + 1)
        rest = rest[:a] + '<h2 id="the-path">The path</h2>\n' + unit_cards(t, md) + "\n" + rest[b:]
    # Position and progress are said once, in the breadcrumb and the outline; a unit's own
    # steps are listed in the outline, so only long help pages get an "On this page" list.
    landing = md == "README.md" or any(md == x["readme"] for x in TRAININGS)
    # A unit says its own size once, quietly, under its title: the outline keeps to one line per unit.
    size = ""
    if md in UNITS:
        n_steps = unit_steps(md)
        size = '<p class="unit">%s%s</p>\n' % (html.escape(UNITS[md][2][:1].upper() + UNITS[md][2][1:]),
                                                "" if n_steps[0][0] == "unit" else " &middot; " + plural(len(n_steps), "step"))
    body = "<h1>%s</h1>\n" % inline(title, md) + size + ("" if md in UNITS or landing else inline_toc(rest)) + rest
    path = os.path.join(OUT, out_name(md))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    root = rel(md, "x")[:-1]
    ot = outline_training(md)
    doc = TEMPLATE.format(source=md, title=html.escape(title), root=root, program=html.escape(PROGRAM_NAME), assistant=html.escape(ASSISTANT), chat=html.escape(ASSISTANT_CHAT),
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


SLOT = re.compile(r"<[^<>]+>")


def check_prompt_slots():
    """A prompt a learner copies runs as written: no <slot> left for them to fill in. Each one found is
    reported like the other checks' findings, with the page, its line and the slot; returns how many."""
    found = 0
    for md in ORDER:
        for n, line in enumerate(read(md), 1):
            if not re.match(r"^\s*> ", line):
                continue
            for m in SLOT.finditer(line.replace("`", "")):
                found += 1
                print("PROMPTSLOT", md, n, m.group(0))
    print("prompt slots:", found)
    return found


def check_unit_positions():
    """The breadcrumb and the unit's header give its number and time; written by hand on a page, they
    go stale when the path changes, as does "step 3" in running text. Each one found is reported."""
    found = 0
    for md in ORDER:
        for n, line in enumerate(read(md), 1):
            if line.startswith("#"):
                continue
            for m in re.finditer(r"\bUnit \d+ of (?:the path|\d+)|\b[Ss]tep \d+\b", line):
                found += 1
                print("UNITPOSITION", md, n, m.group(0))
    print("hand-written unit positions:", found)
    return found


# The starter's own titles, unit names and step headings. They name a stage of the method, not what the
# learner does there, so a kit is a draft while any is left. "Getting started" is not one: the guide
# names the beginner training that, as published courses do.
STARTER_NAMES = {
    "Training programme", "Start here", "Start here: your first fifteen minutes",
    "The first lesson", "An example recipe",
    "First step", "Second step", "Open what you will practise in", "Try the help beside you",
    "Have the assistant create the practice files", "Produce a first result", "What this unit covered", "Look before you change anything",
    "See it done first", "Do the task", "Check it yourself", "Apply it to a second case"}


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


def check_unit_links():
    """A link that opens a unit uses the unit's title, so a renamed unit can't leave old names behind."""
    bad = []
    for md in FILES:
        for i, ln in enumerate(read(md), 1):
            for m in re.finditer(r"\[([^\]]+)\]\(([^)#\s]+\.md)\)", ln):
                target = os.path.normpath(os.path.join(os.path.dirname(md), m.group(2))).replace("\\", "/")
                if target in UNITS and m.group(1) != title_of(target):
                    bad.append("%s:%d [%s] opens \"%s\"" % (md, i, m.group(1), title_of(target)))
    if bad:
        sys.exit("Links that open a unit must use its title:\n  " + "\n  ".join(bad))


def write_files_zip():
    """The learner pages as markdown and the practice files, packed beside the web pages for a
    request to fetch, when FILES_ZIP is set. Files sit at the top of the zip, so extracting it makes one folder
    named after the zip."""
    import zipfile
    count = 0
    with zipfile.ZipFile(os.path.join(OUT, FILES_ZIP), "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(KIT):
            relroot = os.path.relpath(root, KIT).replace(os.sep, "/")
            dirs[:] = sorted(d for d in dirs if not (relroot == "." and d in ("maintaining", "facilitator", OUT_DIR)))
            for f in sorted(files):
                z.write(os.path.join(root, f), f if relroot == "." else relroot + "/" + f)
                count += 1
    return count


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
        for u, (_, name, _) in zip(t["units"], t["path"]):
            if name != title_of(u):
                sys.exit("TRAININGS names %s \"%s\", but its title is \"%s\". A unit's name is its title; "
                         "make the two the same." % (u, name, title_of(u)))
    check_unit_links()
    for t in TRAININGS:
        if t["recipes"] and not any("(how-to/README.md)" in l for l in read(t["readme"])):
            sys.exit("%s has recipes but its home page, %s, doesn't link them in its text. Add a line under "
                     "the path: Once you finish the path, you can try the [practice recipes](how-to/README.md)."
                     % (t["name"], t["readme"]))
    noted = [md for md in FILES if any(re.fullmatch(r"<!--\s*(note|rate)\s*-->", l.strip()) for l in read(md))]
    for md in noted:
        t = page_training(md)
        if not t or md not in [t["readme"]] + t["before"] + t["units"] + t["recipes"]:
            sys.exit("%s has a note or rating, but only a training's home, units and recipes may: elsewhere no "
                     "workbook gathers it." % md)
        if not t["workbook"]:
            sys.exit("%s has notes or ratings for the learner (%s) but no %s/workbook.md to gather them. Copy the "
                     "starter's getting-started/workbook.md into the folder." % (t["name"], md, t["folder"]))
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
                  "before": [{"u": out_name(b), "name": nav_title(b)} for b in t["before"]],
                  "units": [{"u": out_name(u), "n": n, "name": unit_name(u),
                             "steps": [[i, label] for i, label in unit_steps(u) if i != "unit"]}
                            for n, u in enumerate(t["units"], 1)]} for t in TRAININGS]
    io.open(os.path.join(OUT, "search-index.js"), "w", encoding="utf-8", newline="\n").write(
        "window.KIT_INDEX=" + json.dumps(INDEX, ensure_ascii=False) + ";\n"
        "window.KIT_TRAININGS=" + json.dumps(trainings, ensure_ascii=False) + ";\n")
    print("total prompts: %d; search entries: %d" % (total, len(INDEX)))
    if FILES_ZIP:
        print("files zip: %d files in %s" % (write_files_zip(), FILES_ZIP))
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
    failed = check_prompt_slots() > 0
    failed = check_unit_positions() > 0 or failed
    stray = [(md, n) for md in ORDER for n, line in enumerate(read(md), 1) if "[YOUR ORGANIZATION:" in line]
    for md, n in stray:
        print("ORGBLANK", md, n)
    print("organization fields on learner pages:", len(stray))
    failed = failed or bool(stray)
    for checker in ("check_text.py", "check_structure.py", "check_rulings.py"):
        r = subprocess.run([sys.executable, os.path.join(HERE, checker), KIT, OUT], capture_output=True, text=True)
        problems = [l for l in r.stdout.splitlines() if not l.startswith("OK")]
        print("\n".join(problems))
        failed = failed or r.returncode != 0 or not problems or not problems[-1].endswith(": 0")
    if failed:
        sys.exit("CHECKS FAILED: fix the markdown (never the pages) and build again.")
    print("All checks passed.")


CSS = r"""/* One accent (links and where you are), neutrals for everything else, and green only as the small
   mark on a completed unit. Nothing on the page is louder than the step the reader is doing. */
:root{--bg:#ffffff;--bg2:#f7f7f7;--surface:#ffffff;--ink:#1b1b1b;--ink2:#4f4f4f;--ink3:#6b6b6b;
--rule:#e6e6e6;--rule2:#cdcdcd;--accent:#0065b3;--accent-ink:#ffffff;--accent-soft:#eef4fa;--ok:#107c10;--ok-ink:#ffffff;
--ctl:#8a8a8a;--blank:#f0f0f0;--code:#f4f4f4;--focus:#0065b3;
--shadow:0 1px 2px rgba(0,0,0,.06),0 4px 14px rgba(0,0,0,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--bg:#171717;--bg2:#1e1e1e;--surface:#1f1f1f;--ink:#e6e6e6;--ink2:#bdbdbd;--ink3:#9c9c9c;--rule:#303030;--rule2:#4a4a4a;
--accent:#75b6e7;--accent-ink:#101010;--accent-soft:#1c2630;--ok:#74c474;--ok-ink:#101010;
--ctl:#737373;--blank:#262626;--code:#232323;--focus:#75b6e7;--shadow:0 1px 2px rgba(0,0,0,.4),0 4px 14px rgba(0,0,0,.35)}}
:root[data-theme="dark"]{--bg:#171717;--bg2:#1e1e1e;--surface:#1f1f1f;--ink:#e6e6e6;--ink2:#bdbdbd;--ink3:#9c9c9c;
--rule:#303030;--rule2:#4a4a4a;--accent:#75b6e7;--accent-ink:#101010;--accent-soft:#1c2630;--ok:#74c474;--ok-ink:#101010;
--ctl:#737373;--blank:#262626;--code:#232323;--focus:#75b6e7;--shadow:0 1px 2px rgba(0,0,0,.4),0 4px 14px rgba(0,0,0,.35)}
:root[data-theme="dark"]{color-scheme:dark}:root[data-theme="light"]{color-scheme:light}
:root{--side:var(--bg2);--cur:var(--accent-soft);--field:var(--ctl);--okink:var(--ok-ink);--hdr:52px;--crb:42px}
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
/* site header: the programme's name and search, and nothing louder */
.site{position:sticky;top:0;z-index:30;height:var(--hdr);display:flex;align-items:center;gap:14px;padding:0 20px;
background:var(--surface);border-bottom:1px solid var(--rule)}
.brand{font-weight:600;font-size:1rem;color:var(--ink2);text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.brand:hover{color:var(--ink)}
.menu{display:none;align-items:center;gap:6px;font:inherit;font-size:.875rem;padding:5px 10px;border:1px solid var(--ctl);
border-radius:4px;background:var(--surface);color:var(--ink2);cursor:pointer;flex:none}
.search{position:relative;margin-left:auto;width:min(280px,42vw);flex:none}
.search input{width:100%;height:32px;padding:0 10px 0 30px;font:inherit;font-size:.875rem;color:var(--ink);
background:var(--bg2);border:1px solid var(--ctl);border-radius:4px}
.search input::placeholder{color:var(--ink3);opacity:1}
.search input:hover{border-color:var(--ink3)}
.search svg{position:absolute;left:10px;top:9px;width:14px;height:14px;color:var(--ink3)}
.results{position:absolute;right:0;top:38px;width:min(460px,92vw);max-height:70vh;overflow:auto;margin:0;padding:6px;
list-style:none;z-index:30;background:var(--surface);border:1px solid var(--rule);border-radius:6px;box-shadow:var(--shadow)}
.results li{margin:0}
.results li a{display:block;padding:7px 10px;line-height:1.4;border-radius:4px;color:var(--ink);text-decoration:none}
.results li a:hover,.results li a:focus{background:var(--accent-soft)}
.results .rt{font-weight:600;font-size:.875rem}
.results .rs{font-size:.8rem;color:var(--ink2)}
.results .none{padding:7px 10px;color:var(--ink2);font-size:.875rem}
.iconbtn{flex:none;width:32px;height:32px;display:grid;place-items:center;border:1px solid transparent;border-radius:4px;
background:none;color:var(--ink3);cursor:pointer}
.iconbtn:hover{background:var(--bg2);color:var(--ink)}
.iconbtn svg{width:17px;height:17px}
/* page grid: outline | page */
.layout{display:grid;grid-template-columns:280px minmax(0,1fr)}
.content{--gut:clamp(24px,4.5vw,72px);min-width:0}
/* the outline: one line per unit, a ring that fills when the unit is complete, and space rather than lines */
.side{position:sticky;top:var(--hdr);align-self:start;height:calc(100vh - var(--hdr));overflow:auto;padding:0 0 32px;
background:var(--side);border-right:1px solid var(--rule);font-size:.875rem;line-height:1.4}
.side ol,.side ul{list-style:none;margin:0;padding:0}
.side li{margin:0}
.otop{padding:20px 20px 4px}
.otop .omh{margin:0}
.side .otrains{padding:0 10px 12px}
.otrow{display:flex;align-items:baseline;gap:8px;min-height:36px;padding:7px 10px;border-radius:6px;color:var(--ink);text-decoration:none}
.otrow:hover{background:var(--cur)}
.otrow .oname{font-weight:500}
.olevel{margin-left:auto;font-size:.8rem;color:var(--ink3);white-space:nowrap;text-align:right}
.otrow[aria-current]{background:var(--cur);box-shadow:inset 3px 0 0 var(--accent)}
.otrow[aria-current] .oname{color:var(--accent);font-weight:600}
.ou.later .otrow{color:var(--ink3)}
.ocur{border-top:1px solid var(--rule);margin-top:4px}
.ohead{padding:16px 20px 4px}
.side .oextras{padding:0 20px 8px}
.oextras a{display:flex;align-items:center;gap:8px;min-height:36px;padding:6px 10px;margin:0 -10px;border-radius:6px;
color:var(--ink2);font-size:.875rem;text-decoration:none}
.oextras a:hover{background:var(--cur);color:var(--ink)}
.oextras a[aria-current]{color:var(--accent);font-weight:600}
.oextras .cnt{margin-left:auto;font-size:.8rem;color:var(--ink3)}
.otitle{display:block;font-size:1rem;font-weight:600;color:var(--ink);text-decoration:none;line-height:1.3}
.otitle:hover{text-decoration:underline}
.otitle[aria-current]{color:var(--accent)}
.ototal{margin:2px 0 0;font-size:.8125rem;color:var(--ink3)}
.obar{height:3px;border-radius:2px;background:var(--rule);overflow:hidden;margin:12px 0 6px}
.obar span{display:block;height:100%;width:0;background:var(--ink);transition:width .3s}
.opct{margin:0;font-size:.8rem;color:var(--ink3)}
.opct:empty{display:none}
.ounits{padding:10px 0 6px}
.ohd{display:flex;align-items:center}
.orow{flex:1;min-width:0;display:flex;align-items:center;gap:12px;min-height:44px;padding:8px 4px 8px 20px;
color:var(--ink);text-decoration:none}
.orow:hover .oname{text-decoration:underline}
.orow[aria-current] .oname{color:var(--accent)}
.oring{flex:none;position:relative;width:22px;height:22px}
.oring svg{display:block;width:22px;height:22px}
.oring .trk{fill:none;stroke:var(--ctl);stroke-width:2.5}
.oring .arc{fill:none;stroke:var(--ink);stroke-width:2.5;stroke-linecap:round;transition:stroke-dasharray .3s}
.oring .n{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:600;color:var(--ink3)}
.oring.full{border-radius:50%;background:var(--ok)}
.oring.full svg{display:none}
.oring.full .n{color:var(--okink)}
.ou.later .oring{opacity:.55}
.otext{display:flex;flex-direction:column;min-width:0}
.oname{font-weight:500;line-height:1.35;overflow-wrap:anywhere}
.otime{display:block;font-size:.8125rem;font-weight:400;color:var(--ink3);line-height:1.35}
.ou.current .oname{font-weight:600}
.ometa{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.otoggle{flex:none;width:36px;height:36px;margin-right:10px;display:flex;align-items:center;justify-content:center;
border:0;border-radius:6px;background:none;color:var(--ink3);cursor:pointer;opacity:.8}
.otoggle:hover{background:var(--cur);color:var(--ink);opacity:1}
.otoggle svg{width:14px;height:14px;transition:transform .15s}
.ou.open .otoggle svg{transform:rotate(180deg)}
.osteps{display:none;padding:0 12px 8px 0}
.ou.open .osteps{display:block}
.ostep{position:relative;display:flex;align-items:flex-start;gap:12px;min-height:36px;padding:7px 10px 7px 24px;
border-radius:0 6px 6px 0;color:var(--ink2);text-decoration:none;font-size:.875rem}
.ostep:hover{color:var(--ink)}
.ostep:hover .olab{text-decoration:underline}
.odot{flex:none;position:relative;width:12px;height:12px;margin:4px 5px 0;border-radius:50%;border:1.5px solid var(--field);
background:var(--side)}
.ostep.here{color:var(--accent);font-weight:600}
.ostep.here .odot{border-color:var(--accent)}
.ostep.here .odot{background:var(--accent);box-shadow:inset 0 0 0 2px var(--side)}
.content pre.file{margin:16px 0;padding:14px 16px;overflow-x:auto;background:var(--bg2);border:1px solid var(--rule);border-radius:8px;font:.875rem/1.55 ui-monospace,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
.content pre.file code{background:none;padding:0;font:inherit}
.content .callout{margin:20px 0;padding:12px 16px;border:1px solid var(--accent);border-left-width:4px;border-radius:6px;background:var(--bg2)}
.content .callout p{margin:0}
.content .callout .lbl{color:var(--accent)}
.omore{margin:18px 20px 0;padding-top:14px;border-top:1px solid var(--rule)}
.omh{margin:0 0 4px;font-size:.8rem;font-weight:600;color:var(--ink3)}
.omore a{display:flex;align-items:center;gap:8px;min-height:36px;padding:6px 10px;margin:0 -10px;border-radius:6px;
color:var(--ink2);font-size:.875rem;text-decoration:none}
.omore a:hover{background:var(--cur);color:var(--ink)}
.omore a[aria-current]{color:var(--accent);font-weight:600}
.omore .cnt{margin-left:auto;font-size:.8rem;color:var(--ink3)}
.oclose{display:none}
.scrim{display:none}
/* breadcrumb strip: where you are, in the page's quietest voice */
.crumbs{position:sticky;top:var(--hdr);z-index:18;background:var(--bg);border-bottom:1px solid var(--rule)}
.crumbs .in{max-width:720px;margin:0 var(--gut);height:var(--crb);display:flex;align-items:center;gap:12px}
.crumbs ol{display:flex;align-items:center;min-width:0;flex:1;margin:0;padding:0;list-style:none;font-size:.8rem}
.crumbs li{display:flex;align-items:center;min-width:0;margin:0;white-space:nowrap}
.crumbs li a,.crumbs li span{overflow:hidden;text-overflow:ellipsis}
.crumbs li a{color:var(--ink2);text-decoration:underline;text-decoration-color:var(--ink3);text-underline-offset:3px}
.crumbs li a:hover{color:var(--accent);text-decoration-color:currentColor}
.crumbs li+li::before{content:"";flex:none;width:5px;height:5px;margin:0 9px 0 7px;border-right:1px solid var(--ink3);
border-top:1px solid var(--ink3);transform:rotate(45deg)}
.crumbs li[aria-current] span{color:var(--ink3)}
.unitpos{flex:none;font-size:.8rem;color:var(--ink3);white-space:nowrap}
.unitpos .short{display:none}
.line{position:absolute;left:0;right:0;bottom:-1px;height:2px;background:transparent}
.line span{display:block;height:100%;width:0;background:var(--ink3);transition:width .3s}
/* the page */
main{max-width:720px;margin:0 var(--gut);padding:32px 0 72px;line-height:1.5}
main h1{font-size:2rem;line-height:1.25;font-weight:600;letter-spacing:-.01em;margin:8px 0 4px}
main p.unit{margin:0 0 16px;font-size:.875rem;color:var(--ink3)}
main > h1 + p:not(.unit),main > p.unit + p{font-size:1.0625rem}
main h2{font-size:1.4rem;line-height:1.3;font-weight:600;margin:40px 0 8px}
main h3{font-size:1.125rem;line-height:1.35;font-weight:600;margin:24px 0 8px}
/* steps: a quiet number, then space; no rule between them */
main h2.step{display:flex;gap:12px;align-items:baseline;margin-top:40px}
main h3.step{display:flex;gap:10px;align-items:baseline}
.step .n{flex:none;display:inline-grid;place-items:center;min-width:26px;height:26px;padding:0 5px;border-radius:13px;
font-size:.8rem;font-weight:600;border:1.5px solid var(--ctl);color:var(--ink2);transform:translateY(-3px)}
h3.step .n{min-width:22px;height:22px;font-size:.8rem}
main p{margin:8px 0}
main ul,main ol{padding-left:22px;margin:8px 0}
main li{margin:4px 0}
.gap{height:8px}
code{background:var(--code);border-radius:4px;padding:1px 5px;font-size:.875em;font-family:ui-monospace,Consolas,monospace;overflow-wrap:anywhere}
kbd{border:1px solid var(--field);border-radius:3px;padding:0 4px;font-size:.85em;font-family:inherit}
main img{max-width:100%;height:auto;border:1px solid var(--rule);border-radius:6px}
/* a glossary word: a faint underline, the text's own colour */
a.gl{color:inherit;text-decoration:underline;text-decoration-color:var(--rule2);text-decoration-thickness:1px;
text-underline-offset:4px;cursor:help}
a.gl:hover{color:var(--accent);text-decoration-color:var(--accent)}
/* a blank still to fill: marked as unfinished by a light ground and a dotted line, not a box */
.org{background:var(--blank);border-bottom:1px dotted var(--ink3);padding:0 3px;color:var(--ink2);
-webkit-box-decoration-break:clone;box-decoration-break:clone}
/* a Check: a short label in the body's colour, set off by a thin rule */
.check{margin:12px 0;padding:0 0 0 16px;border-left:2px solid var(--ctl)}
.check p{margin:0}
.check .lbl{font-weight:600;cursor:help}
.example{margin:12px 0;padding:12px 16px;border-radius:6px;background:var(--bg2)}
.example .tag{margin:0 0 4px;font-size:.8rem;font-weight:600;color:var(--ink2)}
.example p{margin:0}
.example p.tag{margin:0 0 4px}
.question{font-weight:600}
details.answer{margin:12px 0;border:1px solid var(--ctl);border-radius:6px;background:var(--surface)}
details.answer summary{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;list-style:none;
font-weight:500;color:var(--accent)}
details.answer summary::-webkit-details-marker{display:none}
details.answer summary::before{content:"";width:6px;height:6px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;
transform:rotate(-45deg);transition:transform .15s}
details.answer[open] summary::before{transform:rotate(45deg)}
details.answer[open] summary{border-bottom:1px solid var(--rule)}
details.answer .a{padding:4px 14px 10px}
details.more{margin:8px 0}
details.more summary{display:inline-flex;align-items:center;gap:8px;cursor:pointer;list-style:none;font-size:.9375rem;
font-weight:500;color:var(--accent)}
details.more summary::-webkit-details-marker{display:none}
details.more summary::before{content:"";width:6px;height:6px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;
transform:rotate(-45deg);transition:transform .15s}
details.more[open] summary::before{transform:rotate(45deg)}
details.more .m{margin-top:6px;padding-left:14px;border-left:2px solid var(--rule)}
.prompt{margin:16px 0;background:var(--code);border-radius:6px;
padding:12px 16px;display:flex;flex-wrap:wrap;gap:8px 12px;align-items:flex-start}
.prompt .t{flex:1 1 260px;white-space:pre-wrap;overflow-wrap:anywhere}
.prompt .lab{flex-basis:100%;margin:0;font-size:.8rem;font-weight:600;color:var(--ink2)}
.prompt.orgprompt{background:var(--blank)}
.prompt.frame{background:var(--code)}
button.copy{font:inherit;font-size:.8rem;font-weight:500;padding:3px 12px;cursor:pointer;border:1px solid var(--ctl);
background:var(--surface);color:var(--ink2);border-radius:4px}
button.copy:hover{border-color:var(--ink3);color:var(--ink)}
button.copy.ok{border-color:var(--ok);color:var(--ok)}
.tw{overflow-x:auto;margin:16px 0}
/* tables: rules between rows only */
table{border-collapse:collapse;width:100%;font-size:1rem}
th,td{border:0;border-bottom:1px solid var(--rule);padding:6px 12px 6px 0;text-align:left;vertical-align:top}
thead th{border-bottom:1px solid var(--rule2);font-weight:600;font-size:.875rem;color:var(--ink2)}
tbody th{font-weight:600}
.toc-inline{margin:4px 0 18px;padding:8px 14px;border:1px solid var(--rule);border-radius:6px;background:var(--surface)}
.toc-inline summary{cursor:pointer;font-weight:600;font-size:.875rem}
.toc-inline ul{list-style:none;margin:6px 0 2px;padding:0}.toc-inline li{margin:3px 0}
.toc-inline li.l3{padding-left:14px}.toc-inline a{text-decoration:none}
/* a step's footer, where offered: the quiet "stuck" link. Steps are never ticked; a unit is completed by its Continue button */
.steprow{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;margin:8px 0 0}
button.stuck{font:inherit;font-size:.8rem;padding:4px 0;border:0;background:none;color:var(--ink2);cursor:pointer;
text-decoration:underline;text-decoration-color:var(--ink3);text-underline-offset:3px;text-align:left}
button.stuck:hover{color:var(--accent);text-decoration-color:currentColor}
button.stuck.ok{color:var(--ok);text-decoration:none;font-weight:600}
/* what comes next */
.pager{margin:48px 0 0}
.nextunit{padding:24px 0 0;border-top:1px solid var(--rule)}
.nextunit .lbl{margin:0 0 4px;font-size:.8rem;color:var(--ink3)}
.nextunit h2{margin:0 0 16px;font-size:1.2rem;border:0;padding:0}
.btn{display:inline-flex;align-items:center;gap:8px;padding:8px 20px;border-radius:4px;font-weight:600;text-decoration:none;
background:var(--accent);color:var(--accent-ink);border:1px solid var(--accent)}
.btn:hover{filter:brightness(1.08);text-decoration:none}
.btn svg{width:14px;height:14px}
.nextrow{display:flex;flex-wrap:wrap;gap:14px 22px;align-items:center}
.nextrow .prev,.nextrow .next{font-size:.875rem;color:var(--ink2);text-decoration:none}
.nextrow .prev:hover,.nextrow .next:hover{color:var(--accent);text-decoration:underline}
.nextrow.quiet{padding-top:20px;border-top:1px solid var(--rule)}
.nextrow.quiet .next{margin-left:auto;font-weight:600;color:var(--accent)}
.pagefoot{max-width:720px;margin:-40px var(--gut) 0;padding:14px 0 32px;display:flex;flex-wrap:wrap;gap:4px 18px;
font-size:.8rem;color:var(--ink3)}
.pagefoot a{margin-left:auto;color:var(--ink3);text-decoration:none}
.pagefoot a:hover{color:var(--accent);text-decoration:underline}
.nudge{margin:14px 0 0;font-size:.8rem;color:var(--ink3)}
.nudge:empty{display:none}
button.undo{font:inherit;font-size:inherit;padding:2px 0;margin-left:4px;border:0;background:none;color:var(--ink3);cursor:pointer;
text-decoration:underline;text-decoration-color:var(--rule2);text-underline-offset:3px}
button.undo:hover{color:var(--accent);text-decoration-color:currentColor}
/* a training's home: progress and resume; the programme's list of trainings */
.course{margin:20px 0 8px;padding:16px 20px 8px;border:1px solid var(--rule);border-radius:8px;background:var(--surface)}
.course .meta{margin:0;font-size:.875rem;color:var(--ink2)}
.overall{display:flex;align-items:center;gap:12px;margin:10px 0 0;font-size:.875rem;color:var(--ink2)}
#overall{white-space:nowrap}
.bar{flex:0 1 260px;min-width:80px;height:4px;border-radius:2px;background:var(--rule);overflow:hidden}
.bar span{display:block;height:100%;width:0;background:var(--ink)}
.cta{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:16px 0 10px}
.cta span{color:var(--ink2);font-size:.875rem}
.units{list-style:none;padding:0;margin:12px 0;display:grid;gap:10px}
main .units{padding-left:0}
.unitcard{position:relative;margin:0;padding:12px 16px;border:1px solid var(--rule);border-radius:6px;background:var(--surface)}
.unitcard:hover{border-color:var(--rule2)}
.unitcard a{font-weight:600;font-size:1rem;text-decoration:none}
.unitcard a::after{content:"";position:absolute;inset:0}
.unitcard .un{display:block;font-size:.8rem;color:var(--ink3)}
.unitcard .uo{margin:4px 0;color:var(--ink2);font-size:1rem}
.unitcard .um{margin:2px 0 0;font-size:.8rem;color:var(--ink3)}
.unitcard .us{margin:0;font-size:.8rem;color:var(--ink3)}
.unitcard.done .us{color:var(--ok)}
/* widths: below about 1000px the outline folds behind the Outline button */
@media (max-width:999.98px){
.menu{display:inline-flex}
.layout{grid-template-columns:minmax(0,1fr)}
.side{position:fixed;left:0;top:var(--hdr);z-index:25;width:min(320px,88vw);transform:translateX(-105%);visibility:hidden;
transition:transform .2s,visibility .2s;box-shadow:4px 0 16px rgba(0,0,0,.15)}
body.nav-open .side{transform:none;visibility:visible;transition:transform .2s}
.scrim{display:block;position:fixed;inset:var(--hdr) 0 0;z-index:24;background:rgba(0,0,0,.35);opacity:0;visibility:hidden;
transition:opacity .2s,visibility .2s}
body.nav-open .scrim{opacity:1;visibility:visible}
.otop{position:relative;padding-right:56px;min-height:40px}
.oclose{display:flex;position:absolute;right:10px;top:8px;width:40px;height:40px;align-items:center;justify-content:center;
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
main h1{font-size:1.65rem}
main h2{font-size:1.25rem;margin-top:32px}
main h2.step{margin-top:32px}
main{padding-top:20px}
}
@media (max-width:420px){.brand{display:none}}
@media (forced-colors:active){.org{border-color:CanvasText}.line span,.obar span{background:Highlight}
.check{border-color:CanvasText}.ostep.here,.omore a[aria-current]{outline:2px solid CanvasText}.oring .arc{stroke:CanvasText}
.odot{forced-color-adjust:none}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
/* notes the learner writes, and how sure they are of each objective: kept in this browser, gathered in the workbook */
.note{margin:12px 0}
.note > label{display:block;margin:0 0 6px}
.note textarea{display:block;width:100%;min-height:76px;padding:8px 10px;font:inherit;line-height:1.5;color:var(--ink);
background:var(--bg);border:1px solid var(--field);border-radius:4px;resize:vertical}
.note textarea:hover{border-color:var(--ink3)}
.kept{margin:4px 0 0;font-size:.8rem;color:var(--ink3)}
main ul.rates{list-style:none;padding:0;margin:12px 0}
.rate{margin:0 0 4px}
.rate fieldset{margin:0;padding:8px 0;border:0;border-bottom:1px solid var(--rule)}
.rate legend{padding:0;margin:0 0 4px}
.rate .opts{display:flex;flex-wrap:wrap;gap:4px 20px;font-size:.875rem;color:var(--ink2)}
.rate .opts label{display:inline-flex;align-items:center;gap:6px;min-height:28px;cursor:pointer}
.rate input{width:16px;height:16px;margin:0;accent-color:var(--accent)}
.wbacts{display:flex;flex-wrap:wrap;gap:12px 16px;align-items:center;margin:20px 0 8px}
.wbacts button.btn{font:inherit;font-weight:600;cursor:pointer}
.wbacts button.copy{font-size:.875rem;padding:7px 14px}
.workbook h3 a{color:inherit;text-decoration:none}
.workbook h3 a:hover{color:var(--accent);text-decoration:underline}
@media print{.site,.side,.scrim,.crumbs,.pager,.pagefoot,.steprow,.wbacts,.kept,.skip{display:none!important}
.layout{display:block}main{max-width:none;margin:0;padding:0}
.note textarea{border:0;padding:0;min-height:0;resize:none;overflow:visible}}"""

JS = r"""(function(){
function lget(k,d){try{var v=localStorage.getItem(k);return v===null?d:v;}catch(e){return d;}}
function lput(k,v){try{localStorage.setItem(k,v);}catch(e){}}
var say=document.getElementById("say");
/* light or dark: the reader's choice is remembered; otherwise the system's */
var rootEl=document.documentElement, tb=document.getElementById("theme");
var saved=lget("kit.theme",""); if(saved==="light"||saved==="dark") rootEl.setAttribute("data-theme",saved);
function isDark(){var t=rootEl.getAttribute("data-theme");return t?t==="dark":!!(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches);}
function labelTheme(){tb.setAttribute("aria-label",isDark()?"Switch to light theme":"Switch to dark theme");}
labelTheme();
if(window.matchMedia){var mq=matchMedia("(prefers-color-scheme: dark)"); if(mq.addEventListener) mq.addEventListener("change",labelTheme);}
tb.addEventListener("click",function(){var t=isDark()?"light":"dark";rootEl.setAttribute("data-theme",t);lput("kit.theme",t);labelTheme();});
function copyText(b,txt){
  function done(ok){
    b.classList.toggle("ok",ok); var old=b.getAttribute("data-label")||b.textContent; b.setAttribute("data-label",old);
    var okText=b.getAttribute("data-ok");
    b.textContent=ok?(okText||"Copied"):"Copy failed";
    say.textContent=ok?(okText||"Copied."):"Copy failed. Drag across the text to select it, then right-click it and select Copy.";
    setTimeout(function(){b.classList.remove("ok");b.textContent=old;},okText?8000:2500);
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
  copyText(b,b.parentNode.querySelector(".t").textContent);
});
/* a unit's steps: where offered, each ends with the quiet "stuck" link. Nothing is ticked per step:
   a unit is complete when the learner selects the button at its end (Continue, or Back to the training) */
var main=document.getElementById("main"), page=main.getAttribute("data-page");
var heads=[].slice.call(main.querySelectorAll("h2[id],h3[id]")).filter(function(h){return !h.closest(".pager");});
var isUnit=main.getAttribute("data-steps")==="1";
/* A step's words as plain text. innerText needs layout, which a detached copy doesn't have, so
   numbers, bullets and line breaks are written here. */
function plain(c){
  function all(sel){return (c.matches(sel)?[c]:[]).concat([].slice.call(c.querySelectorAll(sel)));}
  all("ol").forEach(function(ol){var i=parseInt(ol.getAttribute("start")||"1",10);
    [].slice.call(ol.children).forEach(function(li){li.insertBefore(document.createTextNode("\n"+(i++)+". "),li.firstChild);});});
  all("ul").forEach(function(ul){
    [].slice.call(ul.children).forEach(function(li){li.insertBefore(document.createTextNode("\n- "),li.firstChild);});});
  all("p,pre,.t").forEach(function(p){p.appendChild(document.createTextNode("\n"));});
  return c.textContent.replace(/[ \t]+\n/g,"\n").replace(/\n{2,}/g,"\n").trim();
}
var steps=isUnit?heads.filter(function(h){return /^\d/.test(h.textContent);}):[];
var pagerEl=main.querySelector(".pager");
if(main.getAttribute("data-stuck")==="1") steps.forEach(function(h){
  var num=(h.textContent.match(/^\d+/)||[""])[0];
  if(+num<+(main.getAttribute("data-stuck-from")||1)) return;
  var lv=+h.tagName[1], next=heads.slice(heads.indexOf(h)+1).filter(function(x){return +x.tagName[1]<=lv;})[0];
  var row=document.createElement("div"); row.className="steprow";
  var s=document.createElement("button"); s.type="button"; s.className="stuck";
  var who=main.getAttribute("data-assistant")||"for help", box=main.getAttribute("data-chat")||"the chat";
  s.textContent="Stuck? Copy a question for "+who;
  s.setAttribute("aria-label","Stuck on step "+num+"? Copy a question about it to ask "+who);
  s.title="Copies a question about this step, for you to paste into "+box;
  s.setAttribute("data-ok","Copied. Paste it into "+box+" and press Enter.");
  s.addEventListener("click",function(){
    /* the question carries the step's own words, so it works whatever folder is open */
    var said=[];
    for(var n=h.nextElementSibling;n&&!n.matches("h2,h3,.steprow,.pager");n=n.nextElementSibling){
      if(n.matches("details,.callout")) continue;
      var c=n.cloneNode(true); [].slice.call(c.querySelectorAll("button,.lab")).forEach(function(x){x.remove();});
      var t=plain(c); if(t) said.push(t);
    }
    var q="I am working through the training \""+((T&&T.name)||main.getAttribute("data-program"))+"\", unit \""+page+"\", step \""+((h.querySelector(".tt")||h).textContent.trim())+"\". The step says:\n\n"+said.join("\n")+"\n\nWhat does it ask me to do, and what should I see? Do not do it for me.";
    copyText(s,q);
  });
  row.appendChild(s);
  (next||pagerEl).insertAdjacentElement("beforebegin",row);
});
/* progress, kept in this browser only: which units are complete ("kit.complete.<page>") and the last
   page and step read in each training ("kit.last.<training home>"). An earlier build's per-step
   progress ("kit.done.<page>") is never read. */
var ROOT=document.body.getAttribute("data-root");
var TRAININGS=(window.KIT_TRAININGS||[]).filter(function(t){return t.units&&t.units.length;});
var OT=document.body.getAttribute("data-outline"), T=TRAININGS.filter(function(t){return t.f===OT;})[0]||null;
function pathOf(u){try{return new URL(ROOT+u,location.href).pathname;}catch(e){return ROOT+u;}}
function isComplete(u){return lget("kit.complete."+pathOf(u),"")==="1";}
function setComplete(u,on){try{if(on) localStorage.setItem("kit.complete."+pathOf(u),"1"); else localStorage.removeItem("kit.complete."+pathOf(u));}catch(e){}}
function getLast(t){
  var v=null; try{v=JSON.parse(lget("kit.last."+pathOf(t.readme),"null"));}catch(e){v=null;}
  return v&&typeof v.u==="string"?v:null;
}
function putLast(t,u,h){lput("kit.last."+pathOf(t.readme),JSON.stringify({u:u,h:h||""}));}
function trainingState(t){
  var s={done:0,units:t.units.map(function(u){return {u:u,ok:isComplete(u.u)};})};
  s.units.forEach(function(r){if(r.ok) s.done++;});
  return s;
}
/* this page, when it is a unit, or a page before unit 1, of the outline's training */
var HERE=null, HEREI=-1;
if(T){
  (T.before||[]).forEach(function(x){if(pathOf(x.u)===location.pathname) HERE=x;});
  T.units.forEach(function(x,i){if(pathOf(x.u)===location.pathname){HERE=x;HEREI=i;}});
  if(HERE) putLast(T,HERE.u,"");
}
function paintRing(ring,frac,all){
  var arc=ring.querySelector(".arc"), C=2*Math.PI*13, n=ring.querySelector(".n");
  if(!n.getAttribute("data-n")) n.setAttribute("data-n",n.textContent);
  arc.setAttribute("stroke-dasharray",(C*frac)+" "+C); arc.style.display=frac>0&&!all?"":"none";
  ring.classList.toggle("full",all); n.textContent=all?"✓":n.getAttribute("data-n");
}
function setProg(li,html){var pr=li.querySelector(".oprog"); if(html===null) pr.textContent=pr.getAttribute("data-base"); else pr.innerHTML=html;}
function units(k){return k+(k===1?" unit":" units");}
function paintOutline(){
  [].forEach.call(document.querySelectorAll(".ou[data-t]"),function(li){
    var t=TRAININGS.filter(function(x){return x.f===li.getAttribute("data-t");})[0]; if(!t) return;
    var s=trainingState(t), N=t.units.length, all=s.done===N;
    var r=li.querySelector(".oring"); if(r) paintRing(r,s.done/N,all);
    setProg(li,all?" &middot; Done":(s.done?" &middot; "+s.done+" of "+units(N)+" done":null));
  });
  if(!T) return null;
  var s=trainingState(T), N=T.units.length;
  [].forEach.call(document.querySelectorAll(".ou[data-u]"),function(li){
    var i=T.units.map(function(u){return u.u;}).indexOf(li.getAttribute("data-u")); if(i<0) return;
    var ok=s.units[i].ok;
    paintRing(li.querySelector(".oring"),ok?1:0,ok);
    setProg(li,ok?" &middot; Completed":null);
  });
  var ob=document.getElementById("obar"), op=document.getElementById("opct");
  if(ob) ob.style.width=(100*s.done/N)+"%";
  if(op) op.textContent=(s.done===N?"✓ All ":"")+s.done+" of "+units(N)+" done";
  return s;
}
function paintCrumbs(s){
  if(!T||!s) return;
  var N=T.units.length, up=document.getElementById("unitpos"), line=document.getElementById("line");
  if(line) line.style.width=(100*s.done/N)+"%";
  if(!up||HEREI<0) return;
  var ok=s.units[HEREI].ok, pos="Unit "+(HEREI+1)+" of "+N;
  document.getElementById("upos-long").textContent=pos+(ok?" · ✓ completed":"");
  document.getElementById("upos-short").textContent=pos+(ok?" ✓":"");
  up.classList.toggle("all",ok);
  up.title=s.done+" of "+units(N)+" done in "+T.name;
}
/* the end of a unit: its button marks the unit complete, then goes on; a completed unit can be undone here */
var nudge=document.getElementById("nudge"), cont=main.querySelector(".pager a[data-complete]");
if(cont&&HEREI>=0) cont.addEventListener("click",function(){setComplete(HERE.u,true);});
function paintNudge(){
  if(!nudge||HEREI<0) return;
  nudge.textContent="";
  if(isComplete(HERE.u)){
    nudge.appendChild(document.createTextNode("You have completed this unit."));
    var b=document.createElement("button"); b.type="button"; b.className="undo"; b.textContent="Mark as not complete";
    b.addEventListener("click",function(){setComplete(HERE.u,false);paint();if(cont) cont.focus();
      say.textContent="Unit "+(HEREI+1)+" marked not complete.";});
    nudge.appendChild(b);
  }else{
    var w=document.createElement("b"); w.textContent=nudge.getAttribute("data-btn");
    nudge.appendChild(document.createTextNode("Selecting "));nudge.appendChild(w);
    nudge.appendChild(document.createTextNode(" marks this unit complete."));
  }
}
/* the programme's home: each training's progress */
function paintTrainCards(){
  [].forEach.call(document.querySelectorAll(".traincard"),function(li){
    var t=TRAININGS.filter(function(x){return x.f===li.getAttribute("data-training");})[0], us=li.querySelector(".us");
    if(!t||!us) return;
    var s=trainingState(t), N=t.units.length, all=s.done===N, going=!all&&(s.done>0||!!getLast(t));
    us.textContent=all?"✓ All "+units(N)+" done":(s.done?s.done+" of "+units(N)+" done":(going?"In progress":"Not started"));
    li.classList.toggle("done",all); li.classList.toggle("going",going);
  });
}
/* a training's home: each unit's state, and where to pick up */
var cards=[].slice.call(document.querySelectorAll(".unitcard:not(.traincard)"));
var cta=document.getElementById("cta"), ctaNote=document.getElementById("cta-note");
var ctaStart=cta?{t:cta.textContent,h:cta.getAttribute("href"),n:ctaNote.textContent}:null;
function paintUnitCards(){
  if(!cards.length||!T) return;
  var s=trainingState(T), N=T.units.length, last=getLast(T);
  var li_=last?T.units.map(function(u){return u.u;}).indexOf(last.u):-1;
  var lb=last?(T.before||[]).filter(function(b){return b.u===last.u;})[0]:null;
  cards.forEach(function(li,k){
    var r=s.units[k]; if(!r) return;
    var going=!r.ok&&k===li_;
    li.querySelector(".us").textContent=r.ok?"✓ Completed":(going?"In progress":"Not started");
    li.classList.toggle("done",r.ok); li.classList.toggle("going",going);
  });
  var ov=document.getElementById("overall"), br=document.getElementById("bar");
  if(ov) ov.textContent=(s.done===N?"✓ All ":"")+s.done+" of "+units(N)+" done";
  if(br) br.style.width=(100*s.done/N)+"%";
  var todo=s.units.map(function(r,k){return r.ok?-1:k;}).filter(function(k){return k>=0;});
  function go(t,h,n){if(!cta) return;cta.textContent=t;cta.setAttribute("href",h);ctaNote.textContent=n;}
  /* the quiet "Next" at the foot of a training's home goes where the button above goes */
  var pn=document.getElementById("pager-next");
  function pnext(h,name){if(pn){pn.setAttribute("href",h);pn.textContent="Next: "+name+" ›";}}
  if(!todo.length){
    go("You have finished the path",ROOT+T.units[N-1].u+"#you-have-finished-the-path","See what you can now do");
    var nt=TRAININGS[TRAININGS.indexOf(T)+1];
    if(nt) pnext(ROOT+nt.readme,nt.name); else pnext(ROOT+"README.html","All trainings");
  }else if(li_>=0&&!s.units[li_].ok){
    var u=T.units[li_], si=-1;
    (u.steps||[]).forEach(function(x,j){if(last.h&&x[0]===last.h) si=j;});
    go("Continue with unit "+(li_+1),ROOT+u.u+(si>=0?"#"+last.h:""),
       "Where you left off: "+(si>=0?"step "+(si+1)+" of "+u.steps.length+", "+u.steps[si][1]:u.name));
    pnext(ROOT+u.u,u.name);
  }else if(lb){
    go("Continue",ROOT+lb.u,"Where you left off: "+lb.name);
    pnext(ROOT+lb.u,lb.name);
  }else if(li_>=0||s.done){
    var k=todo.filter(function(k){return k>li_;})[0]; if(k===undefined) k=todo[0];
    go("Continue with unit "+(k+1),ROOT+T.units[k].u,"Next: "+T.units[k].name);
    pnext(ROOT+T.units[k].u,T.units[k].name);
  }else if(ctaStart) go(ctaStart.t,ctaStart.h,ctaStart.n);
  /* a training's home has no start button (its first unit card is the way in): with nothing done,
     there is nothing to repaint, and going on matters, since the outline and search are set up below */
}
/* notes and ratings, kept in this browser only ("kit.note.<page>#<note>"); the workbook shows the same ones */
var notes=[].slice.call(main.querySelectorAll(".note[data-note]"));
function noteKey(el){return "kit.note."+pathOf(el.getAttribute("data-u"))+"#"+el.getAttribute("data-note");}
function fit(ta){ta.style.height="auto";ta.style.height=Math.max(76,ta.scrollHeight+2)+"px";}
/* fill every box from storage: on load, when the page comes back with Back (the browser may restore an
   older value), and when another page changes an answer */
function fillNotes(){
  notes.forEach(function(el){
    var v=lget(noteKey(el),""), ta=el.querySelector("textarea");
    if(ta){if(ta.value!==v) ta.value=v; fit(ta);}
    else [].forEach.call(el.querySelectorAll("input[type=radio]"),function(r){r.checked=r.value===v;});
  });
}
notes.forEach(function(el){
  var k=noteKey(el), ta=el.querySelector("textarea");
  if(ta) ta.addEventListener("input",function(){lput(k,ta.value);fit(ta);});
  else [].forEach.call(el.querySelectorAll("input[type=radio]"),function(r){
    r.addEventListener("change",function(){if(r.checked) lput(k,r.value);});
  });
});
fillNotes();
window.addEventListener("pageshow",fillNotes);
window.addEventListener("storage",function(e){if(e.key&&e.key.indexOf("kit.note.")===0) fillNotes();});
var wbDown=document.getElementById("wb-download"), wbPrint=document.getElementById("wb-print");
if(wbPrint) wbPrint.addEventListener("click",function(){window.print();});
if(wbDown) wbDown.addEventListener("click",function(){
  var title=((main.querySelector("h1")||{}).textContent||"Workbook")+(T?" - "+T.name:""), out=[];
  [].forEach.call(main.querySelectorAll(".workbook h2,.workbook h3,.workbook .note"),function(el){
    if(el.tagName==="H2"||el.tagName==="H3"){out.push("<"+el.tagName.toLowerCase()+">"+esc(el.textContent)+"</"+el.tagName.toLowerCase()+">");return;}
    var ta=el.querySelector("textarea"), q, a;
    if(ta){q=el.querySelector("label").textContent;a=ta.value;}
    else{q=el.querySelector("legend").textContent;var c=el.querySelector("input:checked");a=c?c.parentNode.textContent.trim():"";}
    out.push("<p><b>"+esc(q)+"</b></p><p class=a>"+(a?esc(a):"<i>Not answered</i>")+"</p>");
  });
  var doc="<!DOCTYPE html><html lang=en><head><meta charset=utf-8><title>"+esc(title)+"</title><style>"+
    "body{font:16px/1.5 system-ui,sans-serif;max-width:720px;margin:32px auto;padding:0 16px;color:#1b1b1b}"+
    "h2{margin:28px 0 6px}h3{margin:18px 0 4px;font-size:1rem}p{margin:4px 0}p.a{white-space:pre-wrap;padding:0 0 8px;border-bottom:1px solid #ddd}"+
    "</style></head><body><h1>"+esc(title)+"</h1><p>"+esc(main.getAttribute("data-program"))+". Saved "+esc(new Date().toLocaleDateString())+".</p>"+
    out.join("")+"</body></html>";
  var a=document.createElement("a"); a.href=URL.createObjectURL(new Blob([doc],{type:"text/html"}));
  a.download=title.replace(/[^\w -]+/g,"").trim().replace(/\s+/g,"-").toLowerCase()+".html";
  document.body.appendChild(a); a.click(); setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},1000);
  say.textContent="Downloaded a copy of your workbook.";
});
function paint(){paintCrumbs(paintOutline());paintNudge();paintTrainCards();paintUnitCards();}
paint();
/* a page brought back with the browser's Back button shows the progress made since */
window.addEventListener("pageshow",function(e){if(e.persisted) paint();});
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
var hereSaved="";
function markHere(){
  if(!hereHeads.length) return;
  var at=hereHeads[0], lim=window.innerHeight*0.35, reached=false;
  hereHeads.forEach(function(h){if(h.getBoundingClientRect().top<=lim){at=h;reached=true;}});
  if(window.innerHeight+window.scrollY>=document.documentElement.scrollHeight-4){at=hereHeads[hereHeads.length-1];reached=true;}
  /* at the top, or in a frame tall enough to show every heading at once, the first step is being read */
  if(window.scrollY<=4){at=hereHeads[0];reached=false;}
  hereLinks.forEach(function(a){var on=a.getAttribute("data-id")===at.id;a.classList.toggle("here",on);
    if(on) a.setAttribute("aria-current","location"); else a.removeAttribute("aria-current");});
  /* remember the step being read, so the training's home can pick up there */
  var h=reached?at.id:"";
  if(HERE&&h!==hereSaved){hereSaved=h;putLast(T,HERE.u,h);}
}
var hereTick=false;
window.addEventListener("scroll",function(){if(!hereTick){hereTick=true;requestAnimationFrame(function(){hereTick=false;markHere();});}},{passive:true});
window.addEventListener("hashchange",markHere);
markHere();
hereLinks.forEach(function(a){a.addEventListener("click",function(){if(document.body.classList.contains("nav-open")) closeNav();});});
var side=document.getElementById("side"), curA=side.querySelector("a[aria-current]");
if(curA){side.scrollTop=Math.max(0,curA.offsetTop-side.clientHeight/2);}
/* a page opened without a step in its address starts at its title, wherever the previous page was scrolled */
function toTop(){
  var t=null; try{t=location.hash&&document.getElementById(decodeURIComponent(location.hash.slice(1)));}catch(e){}
  if(t) return;
  window.scrollTo(0,0);
  var h1=document.querySelector("h1"); if(h1&&h1.scrollIntoView) h1.scrollIntoView({block:"end"});
  window.scrollTo(0,0);
}
try{history.scrollRestoration="manual";}catch(e){}
toTop(); window.addEventListener("load",toTop); window.addEventListener("pageshow",toTop);
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
