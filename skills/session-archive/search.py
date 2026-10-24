"""Search archived session logs for words in the user's own messages and Claude's replies.

Leaves out text the harness injects (reminders, hook output) and tool output, which make a
plain grep noisy.

usage: python search.py <archive> "<regex>" [--exclude id8,id8] [--since 2026-09-01] [--until 2026-10-20]
"""
import json
import re
import sys
from pathlib import Path


def user_text(r):
    if r.get("type") != "user" or r.get("isMeta") or r.get("isSidechain"):
        return None
    c = (r.get("message") or {}).get("content")
    if isinstance(c, list):
        if any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
            return None
        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    if not isinstance(c, str) or c.lstrip().startswith(("<", "Caveat:", "[SYSTEM NOTIFICATION", "Another Claude session")):
        return None
    return c


def claude(r):
    if r.get("type") != "assistant" or r.get("isSidechain"):
        return None
    c = (r.get("message") or {}).get("content")
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text") or None
    return None


def logs(archive):
    for f in Path(archive).rglob("*.jsonl"):
        if "subagents" in f.parts or f.parent.name == "_index":
            continue
        yield f


def search(archive, pattern, exclude=(), since="", until="9999"):
    rx = re.compile(pattern, re.I)
    hits = []
    for f in logs(archive):
        for line in open(f, encoding="utf-8", errors="replace"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            sid = (r.get("sessionId") or f.stem)[:8]
            ts = r.get("timestamp") or ""
            if sid in exclude or not (since <= ts[:10] <= until):
                continue
            for who, text in (("you", user_text(r)), ("claude", claude(r))):
                if text and rx.search(text):
                    m = rx.search(text)
                    hits.append({"session": sid, "when": ts[:16], "folder": r.get("cwd"), "who": who,
                                 "text": text[max(0, m.start() - 150):m.end() + 150].replace("\n", " ")})
    return sorted(hits, key=lambda h: h["when"])


def oldest(archive):
    first = []
    for f in logs(archive):
        for line in open(f, encoding="utf-8", errors="replace"):
            try:
                ts = json.loads(line).get("timestamp")
            except (ValueError, AttributeError):
                continue
            if ts:
                first.append(ts)
                break
    return min(first) if first else ""


def main(argv):
    archive, pattern = argv[0], argv[1]
    opts = dict(zip(argv[2::2], argv[3::2]))
    exclude = set(filter(None, opts.get("--exclude", "").split(",")))
    print(f"archive reaches back to {oldest(archive)[:10]}")
    for h in search(archive, pattern, exclude, opts.get("--since", ""), opts.get("--until", "9999")):
        print(f"{h['when']} {h['session']} {h['who']:6} {h['folder']} :: {h['text']}")


if __name__ == "__main__":
    main(sys.argv[1:])
