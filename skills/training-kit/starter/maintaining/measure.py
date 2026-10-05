"""Word counts of every learner page, for the budgets in README.md under "Writing".

Run from the kit folder: python maintaining/measure.py
Prose words leave out prompts (lines starting "> "), markers and link targets.
"""
import re, sys, os, glob

KIT = sys.argv[1] if len(sys.argv) > 1 else "."
# Every markdown page in the kit except the folders learners never read. The practice files in
# sample-files are not pages: a skill's SKILL.md or a practice note is not measured against a budget.
SKIP = ("facilitator/", "maintaining/", "read-in-browser/", "sample-files/")
PAGES = sorted(
    rel for rel in (
        os.path.relpath(p, KIT).replace(os.sep, "/")
        for p in glob.glob(os.path.join(KIT, "**", "*.md"), recursive=True))
    if not rel.startswith(SKIP)
)
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
    return prose, steps, prompts, prompt_words, max(runs)


total_words = 0
total_prompts = 0
print("| Page | Prose words | Steps | Prompts | Prompt words | Longest prose run |")
print("|---|---|---|---|---|---|")
for page in PAGES:
    with open(os.path.join(KIT, page), encoding="utf-8") as f:
        w, s, pr, pw, r = measure(f.read())
    total_words += w
    total_prompts += pr
    print(f"| {page} | {w} | {s or ''} | {pr} | {pw} | {r} |")
print(f"| All learner pages | {total_words} | | {total_prompts} | | |")
