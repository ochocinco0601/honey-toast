"""Strip every markdown link that points outside the nine kit pages down to plain
text, so a focused rendering has no dead-ends. Run against the assembled docs dir:

    python neutralize.py <docs_dir>
"""
import os
import re
import sys

docs = sys.argv[1]

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
    if new != text:
        open(full, 'w', encoding='utf-8').write(new)


for root, _, files in os.walk(docs):
    for fn in files:
        if fn.endswith('.md'):
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, docs).replace(os.sep, '/')
            process(full, rel)

print("neutralized outside-kit links")
