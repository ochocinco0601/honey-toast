"""Read Claude Code session transcripts -- the feed every seat reads.

Claude Code writes each session to
    <config>/projects/<encoded-folder>/<session-id>.jsonl
where <config> is $CLAUDE_CONFIG_DIR, or ~/.claude when that is unset. This
module finds a transcript from a session id (or a unique prefix of one) in any
project folder, and renders its records as labelled lines.

Two things here are easy to get wrong and silent when wrong:

  * What the user says while a turn is running is stored as an `attachment`
    record, not a `user` record. A reader that selects on type == "user" drops
    every mid-turn message without a trace. They are labelled USER-MIDTURN.
  * Much of what sits in the user's lane is not the user: messages from other
    sessions, task notifications, hook output, loaded skill bodies. Those are
    labelled INJECTED and are never counted as the user speaking.

  python transcript.py read <session-id|prefix|path> [--last N] [--clean]
  python transcript.py find <session-id|prefix>

--clean drops what a seat must not read: injected records, and the session's
own outbound messages and orchestrator launches, which can carry the very
pre-answer the seats are being scored against.
"""
import argparse
import glob
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def config_root():
    c = os.environ.get("CLAUDE_CONFIG_DIR")
    return os.path.expanduser(c) if c else os.path.join(os.path.expanduser("~"), ".claude")


def projects_root():
    return os.path.join(config_root(), "projects")


def find(target):
    """Path to a transcript, from a path, a session id or a unique id prefix.

    None when nothing matches. Raises ValueError when a prefix is ambiguous.
    """
    if target and os.path.isfile(target):
        return target
    sid = os.path.basename(target[:-len(".jsonl")] if target.endswith(".jsonl") else target)
    if not sid:
        return None
    exact = glob.glob(os.path.join(projects_root(), "*", sid + ".jsonl"))
    if exact:
        return sorted(exact)[0]
    hits = glob.glob(os.path.join(projects_root(), "*", sid + "*.jsonl"))
    if len(hits) > 1:
        raise ValueError("ambiguous session id %r - %d transcripts match; give more of it"
                         % (target, len(hits)))
    return hits[0] if hits else None


def load_records(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def text_of(content):
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    if isinstance(content, str):
        return content
    return ""


def origin_kind(rec):
    return (rec.get("origin") or {}).get("kind")


# A user-lane record the harness produced rather than a person typing. A shape
# rule, not a roster of tags: a roster fails open, silently, on the next kind of
# injected record the harness invents. People do not open a message with "<".
NOT_A_PERSON = ("<", "[Request interrupted", "Another Claude session sent a message",
                "Caveat:")


def person_text(rec):
    """What the person typed in this record, or '' when it is not a person.

    Covers both lanes: ordinary user records, and attachment records holding a
    message sent while a turn was running.
    """
    t = rec.get("type")
    if t == "attachment":
        att = rec.get("attachment") or {}
        if origin_kind(att) != "human":
            return ""
        text = text_of(att.get("prompt", "")).strip()
    elif t == "user" or (t is None and (rec.get("message") or {}).get("role") == "user"):
        if rec.get("isCompactSummary") or rec.get("isMeta") or rec.get("isSidechain"):
            return ""
        kind = origin_kind(rec)
        if kind and kind != "human":
            return ""
        text = text_of((rec.get("message") or {}).get("content", "")).strip()
    else:
        return ""
    if not text or text.startswith(NOT_A_PERSON):
        return ""
    return text


# Outbound traffic a seat must never read. The working session's message to its
# orchestrator, and the command that opened the orchestrator, both sit in the
# session's own transcript as tool calls -- and either can carry the pre-answer.
LAUNCH_MARKS = ("anthropic.claude-code/open", "open_orchestrator", "room orchestrate",
                "room repeat")


def is_outbound(block):
    if not isinstance(block, dict) or block.get("type") != "tool_use":
        return False
    if block.get("name") == "SendMessage":
        return True
    cmd = str((block.get("input") or {}).get("command", ""))
    return any(m in cmd for m in LAUNCH_MARKS)


def render(i, rec, clean=False):
    """One record as labelled lines, or '' when there is nothing to show."""
    t = rec.get("type")
    out = []
    if t == "user":
        content = (rec.get("message") or {}).get("content", "")
        if rec.get("isCompactSummary"):
            return "" if clean else "[%d][SUMMARY] %s" % (i, text_of(content))
        kind = origin_kind(rec)
        if kind and kind != "human":
            label = "INJECTED:%s" % kind
        elif rec.get("isMeta"):
            label = "INJECTED:meta"
        else:
            label = "USER" if person_text(rec) else "INJECTED:harness"
        if clean and label != "USER":
            if isinstance(content, list):
                content = [b for b in content
                           if isinstance(b, dict) and b.get("type") == "tool_result"]
            else:
                content = ""
        if isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    out.append("[%d][%s] %s" % (i, label, b.get("text", "")))
                elif b.get("type") == "tool_result":
                    c = b.get("content", "")
                    out.append("[%d][TOOL_RESULT] %s" % (i, text_of(c) if isinstance(c, list) else c))
        elif isinstance(content, str) and content:
            out.append("[%d][%s] %s" % (i, label, content))
    elif t == "assistant":
        for b in (rec.get("message") or {}).get("content", []) or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text" and b.get("text", "").strip():
                out.append("[%d][ASSISTANT] %s" % (i, b["text"]))
            elif b.get("type") == "tool_use":
                if clean and is_outbound(b):
                    continue
                out.append("[%d][TOOL_CALL:%s] %s" % (
                    i, b.get("name", ""), json.dumps(b.get("input", {}), ensure_ascii=False)))
    elif t == "attachment":
        att = rec.get("attachment") or {}
        kind = origin_kind(att)
        text = text_of(att.get("prompt", "")).strip()
        if kind and text:
            label = "USER-MIDTURN" if person_text(rec) else "INJECTED-MIDTURN:%s" % kind
            if not (clean and label != "USER-MIDTURN"):
                out.append("[%d][%s] %s" % (i, label, text))
    return "\n".join(out)


def window(path, last=120, clean=False):
    recs = load_records(path)
    start = max(0, len(recs) - last) if last else 0
    parts = [render(i, recs[i], clean) for i in range(start, len(recs))]
    return "\n---\n".join(p for p in parts if p)


def person_turns(path):
    """Every line the person typed, in order, across the whole session."""
    out = []
    for i, rec in enumerate(load_records(path)):
        text = person_text(rec)
        if text:
            tag = "USER-MIDTURN" if rec.get("type") == "attachment" else "USER"
            out.append("[%d][%s] %s" % (i, tag, text))
    return out


# --- what is worth waking a watcher for ---------------------------------------

SHELL_WAKE = ("git commit", "git push", "git merge", "git rebase", "git reset",
              "git checkout", "git cherry-pick", "gh issue", "gh pr", "rm -rf",
              "Remove-Item")
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
SHELL_TOOLS = ("Bash", "PowerShell")


def classify(rec):
    """(kind, detail) for a record worth a wake, or None."""
    t = rec.get("type")
    if t == "user" and rec.get("isCompactSummary"):
        return ("COMPACTED", "earlier context was summarised")
    if t in ("user", "attachment"):
        text = person_text(rec)
        if not text:
            return None
        return ("USER-MIDTURN" if t == "attachment" else "USER", text.split("\n")[0][:90])
    if t != "assistant":
        return None
    for c in (rec.get("message") or {}).get("content", []) or []:
        if not isinstance(c, dict) or c.get("type") != "tool_use":
            continue
        name, inp = c.get("name"), c.get("input") or {}
        if name in WRITE_TOOLS:
            return ("EDIT", str(inp.get("file_path", inp.get("notebook_path", "?"))))
        if name in SHELL_TOOLS:
            cmd = " ".join(str(inp.get("command", "")).split())
            if any(w in cmd for w in SHELL_WAKE):
                return ("SHELL", cmd[:100])
        if name == "SendMessage":
            return ("MSG", "to %s" % inp.get("to", "?"))
    return None


def keep_out_of_git(path):
    """Name a feed copy in the .gitignore of the folder it is written to.

    A feed is transcript text, tool results included, and must never outlive the
    host's own retention by landing in a commit. Only this file's name is added,
    so a folder shared with other work is not over-ignored.
    """
    d = os.path.dirname(os.path.abspath(path))
    entry = "/" + os.path.basename(path)
    gi = os.path.join(d, ".gitignore")
    try:
        with open(gi, encoding="utf-8") as f:
            have = f.read()
    except OSError:
        have = ""
    if entry in (l.strip() for l in have.splitlines()):
        return
    with open(gi, "a", encoding="utf-8") as f:
        if not have:
            f.write("# room feed copies - transient transcript text, not for version control\n")
        elif not have.endswith("\n"):
            f.write("\n")
        f.write(entry + "\n")


def main(argv=None):
    p = argparse.ArgumentParser(description="Read a Claude Code session transcript.")
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("read", help="print the last N records, labelled")
    r.add_argument("target", help="session id, unique prefix, or path to a .jsonl")
    r.add_argument("--last", type=int, default=120, help="records to show (0 = all)")
    r.add_argument("--clean", action="store_true",
                   help="drop injected records and outbound messages, as seats get it")
    r.add_argument("--out", help="write the feed to this file (UTF-8) instead of stdout; "
                   "use this rather than shell redirection, which is not UTF-8 everywhere")
    f = sub.add_parser("find", help="print the transcript path for a session id")
    f.add_argument("target")
    a = p.parse_args(argv)
    if a.cmd not in ("read", "find"):
        p.print_help()
        return 2
    try:
        path = find(a.target)
    except ValueError as e:
        print(e)
        return 1
    if not path:
        print("no transcript for %r under %s" % (a.target, projects_root()))
        return 1
    if a.cmd == "find":
        print(path)
        return 0
    body = "Session: %s\n===\n%s\n" % (path, window(path, a.last, a.clean))
    if a.out:
        d = os.path.dirname(os.path.abspath(a.out))
        os.makedirs(d, exist_ok=True)
        keep_out_of_git(a.out)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(body)
        print("feed written: %s (%d bytes)" % (a.out, len(body.encode("utf-8"))))
    else:
        print(body, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
