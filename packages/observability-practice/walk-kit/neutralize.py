"""Prepare the assembled docs for the build: strip every markdown link that points
outside the nine kit pages down to plain text so a focused rendering has no
dead-ends, and fill the render date. Run against the assembled docs dir:

    python neutralize.py <docs_dir>

Every read and write here declares UTF-8, and all page-text rewriting lives here
rather than in the build script. The pages are full of em dashes and arrows, so a
build driven from a shell whose text tools default to a non-UTF-8 codepage would
mangle them; keeping the shell to file operations only makes that impossible.
"""
import datetime
import os
import re
import sys

docs = sys.argv[1]
RENDER_DATE = datetime.date.today().isoformat()

KEPT = {
    "README.md", "the-methodology.md", "how-to-walk-a-question.md",
    "instruments/in-24-first-process-run-plan.md",
    "instruments/in-19-discovery-dialogue-protocol.md",
    "instruments/in-04-service-profile-template.md",
    "instruments/in-05-signal-definition-template.md",
    "instruments/in-06-stakeholder-expectation-template.md",
    "instruments/worked-example-ledger-writer.md",
}

link_re = re.compile(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)')
state_re = re.compile(r'<a href="index\.html#content-state-key">([^<]*)</a>')


def process(full, rel):
    text = open(full, encoding='utf-8').read()
    base = os.path.dirname(rel)

    def repl(m):
        label = m.group(1)
        url = m.group(2).strip().split()[0]
        if url.startswith(('http://', 'https://', 'mailto:', '#')):
            return m.group(0)
        target = url.split('#', 1)[0]
        if target == '':
            return m.group(0)
        resolved = os.path.normpath(os.path.join(base, target)).replace(os.sep, '/')
        return m.group(0) if resolved in KEPT else label

    new = state_re.sub(r'\1', link_re.sub(repl, text))
    new = new.replace('[RENDER DATE]', RENDER_DATE)
    if new != text:
        open(full, 'w', encoding='utf-8').write(new)


for root, _, files in os.walk(docs):
    for fn in files:
        if fn.endswith('.md'):
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, docs).replace(os.sep, '/')
            process(full, rel)

print(f"neutralized outside-kit links; render date {RENDER_DATE}")
