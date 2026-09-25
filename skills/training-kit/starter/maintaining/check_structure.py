import io, os, re, sys
kit, out = sys.argv[1], sys.argv[2]
bad = 0

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
    md = io.open(os.path.join(kit, md_for(p)), encoding="utf-8").read().replace("\r\n", "\n")
    want_prompts = len(re.findall(r"^\s*> ", md, flags=re.M))
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
    srcs = re.findall(r'<img src="([^"]+)"', content)
    if len(md_imgs) != len(srcs):
        bad += 1
        print("PICTURE", os.path.relpath(p, out), "a picture's file does not exist")
    for s in srcs:
        if not os.path.isfile(os.path.normpath(os.path.join(os.path.dirname(p), s))):
            bad += 1
            print("PICTURE", os.path.relpath(p, out), s)
    ols_md = len(re.findall(r"^1\. ", md, flags=re.M)) + len(re.findall(r"^   1\. ", md, flags=re.M))
    ols_page = content.count("<ol>") + content.count('<ol class="units">')
    if ols_md != ols_page:
        bad += 1
        print("OL", os.path.relpath(p, out), ols_md, ols_page)
print("structure problems:", bad)
