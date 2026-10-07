import io, os, re, sys
kit, out = sys.argv[1], sys.argv[2]
bad = 0
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_rulings import ruled_pages
RULED = ruled_pages(kit)

def md_for(page):
    r = os.path.relpath(page, out).replace("\\", "/")
    if r.endswith("/index.html"):
        return r[:-len("index.html")] + "README.md"
    return r[:-5] + ".md"

pages = {}
for root, _, fs in os.walk(out):
    for f in fs:
        if f.endswith(".html"):
            p = os.path.join(root, f)
            pages[os.path.normpath(p)] = io.open(p, encoding="utf-8").read()

for p, full in pages.items():
    h = full.split("<script")[0]
    content = re.split(r'<main id="main"[^>]*>', full, 1)[1].split('<nav class="pager"')[0]
    content = re.sub(r'<details class="toc-inline">.*?</details>', " ", content, flags=re.S)
    content = re.sub(r'<p class="kept">.*?</p>', " ", content, flags=re.S)
    content = re.sub(r'<section class="workbook">.*?</section>', " ", content, flags=re.S)
    md = io.open(os.path.join(kit, md_for(p)), encoding="utf-8").read().replace("\r\n", "\n")
    mdl = md.split("\n")
    # Consecutive "> " lines at the start of a line are one request; an indented one, inside a list, stands alone.
    starts = [i for i, l in enumerate(mdl) if l.startswith("> ") and not (i and mdl[i - 1].startswith("> "))]
    want_prompts = len(starts) + len([l for l in mdl if l.startswith(" ") and l.lstrip().startswith("> ")])
    # A request is short lines, one instruction each, so the learner can read what it asks.
    for i in (starts if md_for(p).replace(os.sep, "/") in RULED else []):
        block = []
        for l in mdl[i:]:
            if not l.lstrip().startswith("> "):
                break
            block.append(l.lstrip()[2:])
        long = [b for b in block if len(b.split()) > 25]
        if len(block) > 8 or long:
            bad += 1
            print("PROMPTLINES", md_for(p), "line %d: a request over 8 lines, or a line over 25 words" % (i + 1))
    want_frames = len(re.findall(r"<!--\s*frame\s*-->", md))
    got_prompts = h.count('class="prompt')
    got_frames = h.count("prompt frame")
    want_li = len(re.findall(r"^\s*(\d+\.|-) ", md, flags=re.M)) - len(re.findall(r"^\s*- ", md, flags=re.M)) + len(re.findall(r"^- ", md, flags=re.M))
    if (want_prompts, want_frames) != (got_prompts, got_frames):
        bad += 1
        print("PROMPTS", os.path.relpath(p, out), want_prompts, got_prompts, want_frames, got_frames)
    for href in re.findall(r'href="([^"]+)"', h):
        if re.match(r"(https?:|mailto:)", href):
            continue
        path, _, anchor = href.partition("#")
        target = os.path.normpath(os.path.join(os.path.dirname(p), path)) if path else p
        if target not in pages and not (path and not path.endswith(".html") and os.path.isfile(target)):
            bad += 1
            print("BROKEN", os.path.relpath(p, out), href)
        elif anchor and ('id="%s"' % anchor) not in pages[target] and anchor != "main":
            bad += 1
            print("ANCHOR", os.path.relpath(p, out), href)
    md_links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", md)
    if len(md_links) != len(re.findall(r'<a href=', content)):
        bad += 1
        print("LINKCOUNT", os.path.relpath(p, out), len(md_links), len(re.findall(r'<a href=', content)),
              "(a link to a page or file that does not exist renders as plain text)")
    md_imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)
    for alt in re.findall(r"!\[([^\]]*)\]\(", md):
        if not alt.strip() or len(alt) > 150:
            bad += 1
            print("ALTTEXT", os.path.relpath(p, out),
                  "a picture needs words in its brackets, 150 characters or fewer:", alt[:60])
    srcs = re.findall(r'<(?:img src|span class="drawing" data-src)="([^"]+)"', content)
    if len(md_imgs) != len(srcs):
        bad += 1
        print("PICTURE", os.path.relpath(p, out), "a picture's file does not exist")
    for s in srcs:
        if not os.path.isfile(os.path.normpath(os.path.join(os.path.dirname(p), s))):
            bad += 1
            print("PICTURE", os.path.relpath(p, out), s)
    ols_md = len(re.findall(r"^\s*1\. ", md, flags=re.M))
    ols_page = content.count("<ol>") + content.count('<ol class="units">')
    if ols_md != ols_page:
        bad += 1
        print("OL", os.path.relpath(p, out), ols_md, ols_page)
    if re.search(r'class="step"><span class="n">', content):
        bad += 1
        print("STEPNUMBER", os.path.relpath(p, out), "a step heading shows its number; only actions and units are numbered on screen")
    for part in re.split(r"<h[23][ >]", content):
        if part.count('class="callout"') > 1:
            bad += 1
            print("CALLOUT", os.path.relpath(p, out), "more than one Important callout in one step")
print("structure problems:", bad)
