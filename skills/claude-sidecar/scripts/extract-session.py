"""
Session transcript (JSONL) extraction for the claude-sidecar skill.

Claude Code writes each session to
    ~/.claude/projects/<encoded-folder>/<session-id>.jsonl
(or under $CLAUDE_CONFIG_DIR/projects if that is set). This tool finds those
files and reads them, without assuming which project folder you are in.

Subcommands:
    scan    list recent sessions with their first user message
    search  find sessions whose user/assistant text contains a keyword
    read    print records from one session, with record indices
    watch   stream one line per notable event in a live session, plus
            escalating notices when it goes quiet (for a background monitor)

Usage:
    python extract-session.py scan [--count N] [--project-dir DIR]
    python extract-session.py search KEYWORD [--path-only] [--project-dir DIR]
    python extract-session.py read PATH_OR_SESSION_ID [--from N] [--to N] [--last N]
    python extract-session.py watch PATH_OR_SESSION_ID [--once] [--poll SECONDS]

--exclude defaults to $CLAUDE_CODE_SESSION_ID when the harness sets it, so the
calling session is left out of scan/search results without any shell syntax.
"""

import argparse
import glob
import json
import os
import sys
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:  # Python < 3.7
    pass


def projects_root():
    config = os.environ.get('CLAUDE_CONFIG_DIR')
    if config:
        return os.path.join(os.path.expanduser(config), 'projects')
    return os.path.join(os.path.expanduser('~'), '.claude', 'projects')


def own_session_id():
    return os.environ.get('CLAUDE_CODE_SESSION_ID') or None


def session_files(project_dir=None, exclude=None):
    """All transcripts, newest first. Every project folder unless one is given."""
    if project_dir:
        pattern = os.path.join(os.path.expanduser(project_dir), '*.jsonl')
    else:
        pattern = os.path.join(projects_root(), '*', '*.jsonl')
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if exclude:
        files = [f for f in files
                 if not os.path.basename(f)[:-len('.jsonl')].startswith(exclude)]
    return files


def resolve(target):
    """A path to a transcript, or a session ID (or unique ID prefix) to look up."""
    if os.path.isfile(target):
        return target
    sid = target[:-len('.jsonl')] if target.endswith('.jsonl') else target
    sid = os.path.basename(sid)
    matches = glob.glob(os.path.join(projects_root(), '*', sid + '*.jsonl'))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        sys.exit('ambiguous session id %r - %d transcripts match; give more of it'
                 % (target, len(matches)))
    sys.exit('no transcript found for %r under %s' % (target, projects_root()))


def get_text_from_content(content):
    """Text blocks of a record's content field, joined."""
    if isinstance(content, list):
        return '\n'.join(b.get('text', '') for b in content
                         if isinstance(b, dict) and b.get('type') == 'text')
    if isinstance(content, str):
        return content
    return str(content)


def tool_result_text(block):
    content = block.get('content', '')
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get('type') == 'text':
                parts.append(b.get('text', ''))
            elif isinstance(b, dict) and b.get('type') == 'image':
                parts.append('[Image]')
        return '\n'.join(parts)
    return content if isinstance(content, str) else str(content)


def origin_kind(rec):
    return (rec.get('origin') or {}).get('kind')


def load_records(path):
    records = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
    return records


def typed_text(rec):
    """Text of a user record the person typed, or '' for harness-injected ones."""
    if rec.get('type') != 'user' or rec.get('isCompactSummary') or rec.get('isMeta'):
        return ''
    kind = origin_kind(rec)
    if kind and kind != 'human':
        return ''
    text = get_text_from_content(rec.get('message', {}).get('content', '')).strip()
    if text.startswith(NOT_A_PERSON):
        return ''
    return text


def first_user_text(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                text = typed_text(json.loads(line))
            except Exception:
                continue
            if text:
                return text
    return ''


def describe(path):
    size = os.path.getsize(path)
    mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
    sid = os.path.basename(path)[:-len('.jsonl')]
    project = os.path.basename(os.path.dirname(path))
    return sid, size, mtime, project


# --- scan / search -----------------------------------------------------------

def scan_sessions(count=10, exclude=None, project_dir=None):
    for path in session_files(project_dir, exclude)[:count]:
        sid, size, mtime, project = describe(path)
        first_user, last_assistant, record_count = '', '', 0
        for rec in load_records(path):
            record_count += 1
            if not first_user:
                first_user = typed_text(rec)[:200]
            if rec.get('type') == 'assistant':
                text = get_text_from_content(rec.get('message', {}).get('content', ''))
                if text.strip():
                    last_assistant = text[-150:]
        print(f'{sid} ({size:,} bytes, {record_count} records, modified {mtime})')
        print(f'  Project: {project}')
        print(f'  First: {first_user[:150]}')
        print(f'  Last:  ...{last_assistant[:120]}')
        print()


def search_sessions(keyword, path_only=False, exclude=None, project_dir=None, count=15):
    keyword_lower = keyword.lower()
    for path in session_files(project_dir, exclude)[:count]:
        found = False
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get('type') in ('user', 'assistant'):
                    text = get_text_from_content(rec.get('message', {}).get('content', ''))
                    if keyword_lower in text.lower():
                        found = True
                        break
        if not found:
            continue
        if path_only:
            print(path)
            continue
        sid, size, mtime, project = describe(path)
        print(f'{sid} ({size:,} bytes, modified {mtime})')
        print(f'  Project: {project}')
        print(f'  Path:  {path}')
        print(f'  First: {first_user_text(path)[:200]}')
        print()


# --- read ----------------------------------------------------------------------

def print_record(i, rec):
    t = rec.get('type')

    if t == 'user':
        content = rec.get('message', {}).get('content', '')
        if rec.get('isCompactSummary'):
            print(f'[{i}][SUMMARY] {get_text_from_content(content)}')
            print('---')
            return
        kind = origin_kind(rec)
        # A message from another session, a task notification, or text the harness
        # adds (isMeta: a loaded skill, a reminder) is stored as a user record;
        # label it so it is never read as the person typing.
        if kind and kind != 'human':
            label = f'INJECTED:{kind}'
        elif rec.get('isMeta'):
            label = 'INJECTED:meta'
        else:
            label = 'USER'
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get('type') == 'text':
                    print(f'[{i}][{label}] {block.get("text", "")}')
                elif block.get('type') == 'image':
                    source = block.get('source', {})
                    print(f'[{i}][{label}] [Image: {source.get("url", source.get("media_type", ""))}]')
                elif block.get('type') == 'tool_result':
                    print(f'[{i}][TOOL_RESULT] {tool_result_text(block)}')
        elif isinstance(content, str):
            print(f'[{i}][{label}] {content}')
        print('---')

    elif t == 'assistant':
        content = rec.get('message', {}).get('content', '')
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get('type') == 'text':
                    text = block.get('text', '')
                    if text.strip():
                        print(f'[{i}][ASSISTANT] {text}')
                elif block.get('type') == 'tool_use':
                    inp_str = json.dumps(block.get('input', {}), ensure_ascii=False)
                    print(f'[{i}][TOOL_CALL:{block.get("name", "")}] {inp_str}')
        elif isinstance(content, str) and content.strip():
            print(f'[{i}][ASSISTANT] {content}')
        print('---')

    elif t == 'attachment':
        # A message the person sent while a turn was running is stored here, not
        # as a 'user' record. Dropping it hides everything said mid-turn.
        att = rec.get('attachment', {})
        kind = origin_kind(att)
        if kind:
            text = get_text_from_content(att.get('prompt', ''))
            if text.strip():
                label = 'USER-MIDTURN' if kind == 'human' else f'INJECTED-MIDTURN:{kind}'
                print(f'[{i}][{label}] {text}')
                print('---')

    elif t == 'tool_result':  # older transcript format
        print(f'[{i}][TOOL_RESULT] {get_text_from_content(rec.get("content", ""))}')
        print('---')

    elif t == 'summary':  # older transcript format
        print(f'[{i}][SUMMARY] {rec.get("summary", rec.get("content", ""))}')
        print('---')


def read_session(path, start=None, end=None, last=None):
    """Print records. Lossless: nothing is truncated."""
    records = load_records(path)
    total = len(records)
    print(f'Session: {path}')
    print(f'Total records: {total}')
    print('===')
    if last is not None:
        start, end = max(0, total - last), total
    elif start is not None:
        end = total if end is None else end
    else:
        start, end = max(0, total - 50), total
    for i in range(start, min(end, total)):
        print_record(i, records[i])


# --- watch ---------------------------------------------------------------------

# Escalating, in minutes: a long quiet stretch costs fewer wakes than a short one,
# while the feed never goes fully silent.
PAUSE_STEPS = (5, 15, 30, 60, 120, 240)

# Shell commands worth a wake. Nearly everything else a session runs is reading,
# and a watcher woken on reads stops reading its own feed.
SHELL_WAKE = ('git commit', 'git push', 'git merge', 'git rebase', 'git reset',
              'git checkout', 'git cherry-pick', 'gh issue', 'gh pr', 'rm -rf',
              'Remove-Item')

WRITE_TOOLS = ('Edit', 'Write', 'MultiEdit', 'NotebookEdit')
SHELL_TOOLS = ('Bash', 'PowerShell')

# A user record the harness produced rather than a person typing (hook context,
# reminders, notifications). A shape rule, not a roster: a roster fails silently
# on the next kind the harness invents.
NOT_A_PERSON = ('<', '[Request interrupted')


def person_turn(text_source):
    text = get_text_from_content(text_source).strip()
    if not text or text.startswith(NOT_A_PERSON):
        return None
    return text.split('\n')[0][:90]


def classify(rec):
    """What a record is worth waking a watcher for, or None."""
    kind = rec.get('type')
    if kind == 'user':
        if rec.get('isCompactSummary'):
            return ('COMPACTED', 'earlier context was summarised')
        okind = origin_kind(rec)
        if (okind and okind != 'human') or rec.get('isMeta'):
            return None
        line = person_turn(rec.get('message', {}).get('content'))
        return ('USER', line) if line else None
    if kind == 'attachment':
        att = rec.get('attachment', {})
        if origin_kind(att) == 'human':
            line = person_turn(att.get('prompt', ''))
            return ('USER-MIDTURN', line) if line else None
        return None
    if kind != 'assistant':
        return None
    for c in rec.get('message', {}).get('content', []) or []:
        if not isinstance(c, dict) or c.get('type') != 'tool_use':
            continue
        name, inp = c.get('name'), c.get('input', {}) or {}
        if name in WRITE_TOOLS:
            return ('EDIT', str(inp.get('file_path', inp.get('notebook_path', '?'))))
        if name in SHELL_TOOLS:
            cmd = ' '.join(str(inp.get('command', '')).split())
            if any(w in cmd for w in SHELL_WAKE):
                return ('SHELL', cmd[:100])
        if name == 'SendMessage':
            return ('MSG', 'to %s' % inp.get('to', '?'))
    return None


def pulse(state, records, now):
    """Lines worth waking for, and the state to carry to the next poll."""
    st = dict(state)
    lines = []
    for rec in records:
        got = classify(rec)
        if not got:
            continue
        if st['paused']:
            lines.append('RESUMED after %dm quiet' % round((now - st['last']) / 60.0))
            st['paused'], st['fired'] = False, ()
        lines.append('%s %s' % got)
        st['last'] = now
    if st['last'] is None:
        st['last'] = now
    quiet = (now - st['last']) / 60.0
    due = [s for s in PAUSE_STEPS if quiet >= s and s not in st['fired']]
    if due:
        st['fired'] = tuple(st['fired']) + tuple(due)
        st['paused'] = True
        lines.append('QUIET %dm - no edit, commit or user turn since. This cannot '
                     'tell thinking, blocked, waiting on the user, or closed apart; '
                     'read the stream to find out' % round(quiet))
    return lines, st


def read_new(path, offset):
    """Records appended since the last look, stopping at the last full line."""
    recs = []
    try:
        size = os.path.getsize(path)
    except OSError:
        return recs, offset
    if size < offset:
        offset = 0
    if size == offset:
        return recs, offset
    with open(path, 'rb') as f:
        f.seek(offset)
        blob = f.read()
    tail = blob.rfind(b'\n')
    if tail == -1:
        return recs, offset
    for raw in blob[:tail].splitlines():
        try:
            recs.append(json.loads(raw.decode('utf-8', 'replace')))
        except Exception:
            continue
    return recs, offset + tail + 1


def watch_session(path, once=False, poll=30):
    sid = os.path.basename(path)[:-len('.jsonl')]
    me = own_session_id()
    if me and (sid.startswith(me) or me.startswith(sid)):
        print('refusing: that transcript is this session. A session cannot watch itself.')
        return 1
    # A stream begins at the end: the watcher is told what happens next. A single
    # pass begins at the start, so it shows what the filter would have woken for;
    # from the end it could only ever show nothing, which looks like a clean feed.
    offset = 0 if once else os.path.getsize(path)
    st = {'last': None, 'fired': (), 'paused': False}
    print('ARMED on %s - every further line is something it did, or a silence '
          'worth knowing about' % sid[:8], flush=True)
    while True:
        recs, offset = read_new(path, offset)
        lines, st = pulse(st, recs, time.time())
        for ln in lines:
            print('%s %s' % (sid[:8], ln), flush=True)
        if once:
            return 0
        time.sleep(poll)


# --- CLI -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Session transcript extraction for the claude-sidecar skill')
    sub = parser.add_subparsers(dest='command')
    excl_help = ('Session ID to leave out (default: $CLAUDE_CODE_SESSION_ID, '
                 'i.e. the calling session, when the harness sets it)')

    scan_p = sub.add_parser('scan', help='List recent sessions')
    scan_p.add_argument('--count', type=int, default=10, help='Number of sessions to show')
    scan_p.add_argument('--exclude', default=own_session_id(), help=excl_help)
    scan_p.add_argument('--project-dir', help='Only this transcript folder '
                        '(default: every folder under ~/.claude/projects)')

    read_p = sub.add_parser('read', help='Extract records from a session')
    read_p.add_argument('path', help='Path to a JSONL transcript, or a session ID')
    read_p.add_argument('--from', dest='start', type=int, help='Start record index')
    read_p.add_argument('--to', type=int, help='End record index (exclusive)')
    read_p.add_argument('--last', type=int, help='Read last N records')

    search_p = sub.add_parser('search', help='Find sessions by keyword')
    search_p.add_argument('keyword', help='Keyword to search for')
    search_p.add_argument('--path-only', action='store_true', help='Print only file paths')
    search_p.add_argument('--count', type=int, default=15,
                          help='How many recent sessions to search')
    search_p.add_argument('--exclude', default=own_session_id(), help=excl_help)
    search_p.add_argument('--project-dir', help='Only this transcript folder')

    watch_p = sub.add_parser('watch', help='Stream notable events from a live session')
    watch_p.add_argument('path', help='Path to a JSONL transcript, or a session ID')
    watch_p.add_argument('--once', action='store_true',
                         help='One pass from the start, to check what the filter catches')
    watch_p.add_argument('--poll', type=int, default=30, help='Seconds between looks')

    args = parser.parse_args()
    if args.command == 'scan':
        scan_sessions(args.count, exclude=args.exclude, project_dir=args.project_dir)
    elif args.command == 'read':
        read_session(resolve(args.path), start=args.start, end=args.to, last=args.last)
    elif args.command == 'search':
        search_sessions(args.keyword, args.path_only, exclude=args.exclude,
                        project_dir=args.project_dir, count=args.count)
    elif args.command == 'watch':
        sys.exit(watch_session(resolve(args.path), once=args.once, poll=args.poll))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
