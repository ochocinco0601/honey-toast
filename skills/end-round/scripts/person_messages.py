"""Print every message the person typed in this session, from its transcript.

Usage: python -I person_messages.py "<a phrase from one of the person's messages>"
Finds the newest transcript under ~/.claude/projects in which the person typed the phrase
and prints the person's own messages, numbered, with their timestamps.
"""
import glob
import json
import os
import re
import sys


def typed_text(d):
    if d.get('type') != 'user' or d.get('isSidechain') or d.get('isMeta'):
        return None
    m = d.get('message') or {}
    c = m.get('content')
    if isinstance(c, list):
        if any(isinstance(b, dict) and b.get('type') == 'tool_result' for b in c):
            return None
        # harness-injected blocks (instructions, reminders) arrive as their own text blocks starting with a tag
        c = '\n'.join(b.get('text', '') for b in c if isinstance(b, dict) and b.get('type') == 'text'
                      and not b.get('text', '').lstrip().startswith('<'))
    if not isinstance(c, str) or not c.strip():
        return None
    t = re.sub(r'(?s)<(system-reminder|ide_selection|ide_opened_file)>.*?</\1>', '', c).strip()
    if not t or t.startswith('<') or t.startswith('Another Claude session sent a message') or t.startswith('[SYSTEM'):
        return None
    return t


def typed_rows(path):
    rows = []
    try:
        lines = open(path, encoding='utf-8', errors='ignore').readlines()
    except OSError:
        return rows
    for line in lines:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        t = typed_text(d)
        if t:
            rows.append((d.get('timestamp', ''), d.get('uuid'), t))
    return rows


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    phrase = sys.argv[1]
    root = os.path.expanduser('~/.claude/projects')
    files = [p for p in glob.glob(root + '/*/*.jsonl')]
    files.sort(key=os.path.getmtime, reverse=True)
    for p in files[:200]:
        # match only the person's own typed messages, never a quotation of them elsewhere
        if not any(phrase in t for _, _, t in typed_rows(p)):
            continue
        # a session that changed folder (e.g. into a worktree) has one file per folder
        parts = glob.glob(root + '/*/' + os.path.basename(p))
        print('transcript:', *parts, sep='\n  ')
        rows = [r for part in parts for r in typed_rows(part)]
        seen = set()
        n = 0
        for ts, uid, t in sorted(rows):
            if uid in seen:
                continue
            seen.add(uid)
            n += 1
            print(f'\n--- {n}  {ts[:16]}\n{t}')
        return
    sys.exit('no transcript contains that phrase')


main()
