"""List the Claude Code sessions open on this machine, or find any session by its tab title.

    sessions.py                 open sessions: tab title, messaging name, session ID
    sessions.py find <words>    every session, open or closed, whose tab title matches
"""
import json
import mmap
import os
import sys
from datetime import datetime
from pathlib import Path

CLAUDE = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def alive(pid):
    if sys.platform == "win32":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)  # on Windows this would terminate the process, hence the branch above
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def last_record(m, marker, key):
    i = m.rfind(marker)
    if i < 0:
        return ""
    start = m.rfind(b"\n", 0, i) + 1
    end = m.find(b"\n", i)
    try:
        return json.loads(m[start:end if end >= 0 else len(m)].decode("utf-8", "replace")).get(key) or ""
    except ValueError:
        return ""


def title_of(path):
    # A rename or fork writes custom-title; otherwise the tab shows the latest ai-title.
    try:
        if path.stat().st_size == 0:
            return ""
        with open(path, "rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as m:
            return last_record(m, b'custom-title"', "customTitle") or last_record(m, b'ai-title"', "aiTitle")
    except OSError:
        return ""


def transcripts():
    return {f.stem: f for f in (CLAUDE / "projects").glob("*/*.jsonl")}


def open_sessions():
    rows = []
    for f in (CLAUDE / "sessions").glob("*.json"):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if s.get("sessionId") and alive(int(s.get("pid", 0))):
            rows.append(s)
    return rows


def when(ts):
    if not ts:
        return ""
    t = datetime.fromtimestamp(ts)
    return t.strftime("%H:%M") if t.date() == datetime.now().date() else t.strftime("%m-%d %H:%M")


def cell(text):
    return text.replace("|", "/")


def list_open():
    rows = open_sessions()
    if not rows:
        print("No open Claude Code sessions found on this machine.")
        return
    rows.sort(key=lambda s: s.get("updatedAt") or 0, reverse=True)
    paths = transcripts()
    me = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    print("| # | Tab title | Messaging name | Session ID | Status | Last active | Folder |")
    print("|---|---|---|---|---|---|---|")
    for n, s in enumerate(rows, 1):
        p = paths.get(s["sessionId"])
        title = cell((title_of(p) if p else "") or "(no title yet)")
        if s["sessionId"] == me:
            # A new session's tab is often titled from the title the user pasted into it.
            title += " (this session, not the one meant)"
        print(f"| {n} | {title} | {s.get('name', '')} | {s['sessionId']} | {s.get('status', '')} "
              f"| {when((s.get('updatedAt') or 0) / 1000)} | {Path(s.get('cwd', '')).name} |")


def find(query):
    me = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    live = {s["sessionId"]: s for s in open_sessions()}
    q = " ".join(query.lower().split())
    words = q.split()
    exact, partial = [], []
    for sid, p in transcripts().items():
        if sid == me:
            continue
        title = title_of(p)
        t = " ".join(title.lower().split())
        if not t:
            continue
        if t == q:
            exact.append((sid, p, title))
        elif all(w in t for w in words):
            partial.append((sid, p, title))
    hits = exact or partial
    if not hits:
        print(f'No session has a tab title matching "{query}".')
        return
    hits.sort(key=lambda h: (h[0] not in live, -h[1].stat().st_mtime))
    print("| # | Tab title | State | Messaging name | Session ID | Last written | Transcript |")
    print("|---|---|---|---|---|---|---|")
    for n, (sid, p, title) in enumerate(hits, 1):
        s = live.get(sid)
        print(f"| {n} | {cell(title)} | {'open' if s else 'closed'} | {s.get('name', '') if s else ''} "
              f"| {sid} | {when(p.stat().st_mtime)} | {p} |")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "find":
        find(" ".join(sys.argv[2:]))
    else:
        list_open()
