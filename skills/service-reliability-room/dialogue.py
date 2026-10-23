"""Print the chief's conversation with the person from a Claude Code transcript (a session's JSONL).

Read-only. Keeps the person's typed messages and the chief's own text; drops tool calls and results,
thinking, injected reminders and subagent traffic. Says when the person's last message has no answer.

    python -I dialogue.py <transcript.jsonl> [--since <ISO timestamp>]
"""
import argparse
import json
import re
import sys

BLOCKS = re.compile(r"<(system-reminder|browser_instruction)>.*?</\1>", re.S)
INJECTED = ("<system-reminder>", "<local-command", "<command-", "<task-notification>", "<cross-session-message")


def _texts(content):
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return []


def read(path, since=None):
    turns = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            kind = o.get("type")
            if kind not in ("user", "assistant") or o.get("isSidechain") or o.get("isMeta") \
                    or o.get("isCompactSummary") or o.get("isVisibleInTranscriptOnly"):
                continue
            ts = o.get("timestamp") or ""
            if since and ts < since:
                continue
            msg = o.get("message")
            if not isinstance(msg, dict):
                continue
            text = "\n".join(t.strip() for t in (BLOCKS.sub("", x) for x in _texts(msg.get("content"))) if t.strip() and not t.lstrip().startswith(INJECTED))
            if text:
                turns.append({"who": "person" if kind == "user" else "chief", "at": ts, "text": text})
    return turns


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("transcript")
    ap.add_argument("--since")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    turns = read(a.transcript, a.since)
    for t in turns:
        print(f"[{t['at']}] {t['who']}: {t['text']}\n")
    if turns and turns[-1]["who"] == "person":
        print("The person's last message is unanswered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
