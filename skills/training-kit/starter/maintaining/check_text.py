import html, io, os, re, sys
kit, out = sys.argv[1], sys.argv[2]
bad = 0

def md_text(t):
    lines = []
    for ln in t.replace("\r\n", "\n").split("\n"):
        s = ln.strip()
        if re.fullmatch(r"<!--\s*(frame|tutor|tool)\s*-->", s):
            continue
        s = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        if re.fullmatch(r"\|?[-:| ]+\|?", s) and "-" in s:
            continue
        s = re.sub(r"^#{1,6} ", "", s)
        s = re.sub(r"^> ", "", s)
        s = re.sub(r"^- ", "", s)
        if re.match(r"^\s*\d+\. ", ln):
            s = re.sub(r"^\d+\. ", "", s)
        if s.startswith("|"):
            s = " ".join(c.strip() for c in s.strip("|").split("|"))
        s = s.replace("**", "").replace("`", "")
        lines.append(s)
    return re.sub(r"\s+", "", " ".join(lines))

for root, _, fs in os.walk(out):
    for f in fs:
        if not f.endswith(".html"):
            continue
        page = os.path.join(root, f)
        md = os.path.join(kit, os.path.relpath(page, out))[:-5] + ".md"
        if f == "index.html":
            md = os.path.join(os.path.dirname(md), "README.md")
        src = io.open(md, encoding="utf-8").read().replace("\r\n", "\n")
        h = io.open(page, encoding="utf-8").read()
        body = re.split(r'<main id="main"[^>]*>', h, 1)[1].split("</main>")[0]
        name = os.path.relpath(page, out)
        # A course's path and the programme's list of trainings are shown as cards: each card must
        # carry its list item's words; the rest of the page is compared word for word as usual.
        for heading, anchor, item_re, tag in (("The path", "the-path", r"^\d+\. (.*(?:\n   .*)*)", "ol"),
                                              ("The trainings", "the-trainings", r"^- (.*(?:\n  .*)*)", "ul")):
            found = re.search(r"\n## %s\n(.*?)(?=\n## )" % heading, src, flags=re.S)
            if not found or '<h2 id="%s">' % anchor not in body:
                continue
            section = found.group(1)
            src = src.replace("## %s\n" % heading + section, "")
            cards = re.search(r'<h2 id="%s">.*?<%s class="units">(.*?)</%s>' % (anchor, tag, tag), body, flags=re.S).group(1)
            card_text = re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", " ", cards))).lower()
            for item in re.findall(item_re, section, flags=re.M):
                piece = md_text(re.sub(r"\[([^\]]+)\]\([^)]+\):?", r"\1", item)).lower()
                if piece not in card_text:
                    bad += 1
                    print("CARD", name, "missing:", piece[:60])
            body = re.sub(r'<h2 id="%s">.*?</%s>' % (anchor, tag), " ", body, count=1, flags=re.S)
        body = re.sub(r'<section class="course".*?</section>', " ", body, flags=re.S)
        want = md_text(src)
        body = re.sub(r'<nav class="pager".*?</nav>', " ", body, flags=re.S)
        body = re.sub(r'<aside class="toc".*?</aside>', " ", body, flags=re.S)
        body = re.sub(r'<details class="toc-inline">.*?</details>', " ", body, flags=re.S)
        body = re.sub(r'<nav class="path"[^>]*>.*?</nav>', " ", body, flags=re.S)
        body = re.sub(r'<div class="setup">.*?</div>', " ", body, flags=re.S)
        body = re.sub(r"<button[^>]*>.*?</button>", " ", body)
        body = re.sub(r'<aside class="howto".*?</aside>', " ", body, flags=re.S)
        body = re.sub(r'<p class="after".*?</p>', " ", body, flags=re.S)
        body = re.sub(r'<p class="lab">.*?</p>', " ", body, flags=re.S)
        body = re.sub(r'<p class="cta">.*?</p>', " ", body, flags=re.S)
        body = re.sub(r'<p class="unit"[^>]*>.*?</p>', " ", body, flags=re.S)
        body = re.sub(r'<summary>.*?</summary>', " ", body, flags=re.S)
        body = re.sub(r'<nav class="foot"[^>]*>.*?</nav>', " ", body, flags=re.S)
        body = re.sub(r'<div id="say".*?</div>', " ", body, flags=re.S)
        got = re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", " ", body)))
        if want == got:
            print("OK  ", os.path.relpath(page, out), len(want), "chars")
        else:
            bad += 1
            i = next((k for k in range(min(len(want), len(got))) if want[k] != got[k]), min(len(want), len(got)))
            print("DIFF", os.path.relpath(page, out), "at", i, "| md:", want[i-30:i+30], "| page:", got[i-30:i+30])
print("pages differing:", bad)
