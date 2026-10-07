"""Word counts of every learner page, for the budgets in README.md under "Writing".

Run from the kit folder: python maintaining/measure.py
Prose words leave out prompts (lines starting "> "), markers and link targets.
"""
import re, sys, os, glob

KIT = sys.argv[1] if len(sys.argv) > 1 else "."
# Folders learners never read: the practice files are not pages, and neither is their note.
NOT_PAGES = ("facilitator", "maintaining", "read-in-browser", "sample-files")
TRAINING_FOLDERS = ["getting-started", "skills-in-depth", "agents"]


def pages():
    """Every learner page, in reading order: the home page, each training (home, units, recipes), then
    the shared help pages."""
    found = []
    for root, dirs, files in os.walk(KIT):
        here = os.path.relpath(root, KIT).replace(os.sep, "/")
        dirs[:] = sorted(d for d in dirs if not (here == "." and d in NOT_PAGES))
        for f in sorted(files):
            if f.endswith(".md"):
                found.append(os.path.relpath(os.path.join(root, f), KIT).replace(os.sep, "/"))

    def key(p):
        folder = p.split("/")[0] if "/" in p else ""
        if p == "README.md":
            return (0, 0, p)
        if folder in TRAINING_FOLDERS:
            t = TRAINING_FOLDERS.index(folder)
            return (1, t, 0 if p.endswith("/README.md") and p.count("/") == 1 else 1, p.count("/"), p)
        return (2, 0, p)
    return sorted(found, key=key)


PAGES = pages()
WORD = re.compile(r"[A-Za-z0-9][\w'.-]*")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def measure(text):
    prose = 0
    prompts = 0
    prompt_words = 0
    runs = []
    cur = 0
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("> "):
            prompts += 1
            prompt_words += len(WORD.findall(s))
            runs.append(cur)
            cur = 0
            continue
        if s.startswith("<!--"):
            continue
        if s.startswith("#"):
            runs.append(cur)
            cur = 0
        n = len(WORD.findall(LINK.sub(r"\1", s)))
        prose += n
        cur += n
    runs.append(cur)
    steps = len(re.findall(r"^## \d", text, flags=re.M))
    pictures = len(re.findall(r"^!\[", text, flags=re.M))
    return prose, steps, prompts, prompt_words, max(runs), pictures


total_words = 0
total_prompts = 0
total_pictures = 0
print("| Page | Prose words | Steps | Prompts | Prompt words | Longest prose run | Pictures |")
print("|---|---|---|---|---|---|---|")
for page in PAGES:
    with open(os.path.join(KIT, page), encoding="utf-8") as f:
        w, s, pr, pw, r, pic = measure(f.read())
    total_words += w
    total_prompts += pr
    total_pictures += pic
    print(f"| {page} | {w} | {s or ''} | {pr} | {pw} | {r} | {pic} |")
print(f"| All learner pages | {total_words} | | {total_prompts} | | | {total_pictures} |")
