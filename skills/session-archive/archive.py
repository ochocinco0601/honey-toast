"""Keep a personal backup of Claude Code session logs, for a set number of days.

Copies only add or refresh; nothing here changes the original logs.
Archive copies older than KEEP_DAYS (counted from the session's last activity) are deleted.

copyfile, not copy2: on Windows, copy2 uses CopyFile2, which locks the source against writes
while it copies, so a live session's appends fail during a copy.

usage: python archive.py [--dry-run]
exit: 0 ran; 2 source folder missing or empty (so a broken setup is not silent)
"""
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ARCHIVE_DIR = Path.home() / "claude-session-archive"
KEEP_DAYS = 70
SOURCE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "projects"
ERRORS = "_archive-errors.log"
STAMP = "_last-archived.txt"


def copy_one(f, target):
    s = f.stat()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + f".{os.getpid()}.part")
    shutil.copyfile(f, tmp)
    os.utime(tmp, ns=(s.st_atime_ns, s.st_mtime_ns))
    os.replace(tmp, target)


def copy_new(src, dst, keep_days=KEEP_DAYS):
    src, dst = Path(src), Path(dst)
    cutoff = time.time() - keep_days * 86400
    copied, failed = 0, []
    for f in src.rglob("*"):
        try:
            if not f.is_file() or f.name.endswith(".part"):
                continue
            s = f.stat()
            if s.st_mtime < cutoff:
                continue
            target = dst / f.relative_to(src)
            if target.exists():
                t = target.stat()
                if t.st_size == s.st_size and int(t.st_mtime) == int(s.st_mtime):
                    continue
            copy_one(f, target)
            copied += 1
        except OSError as e:
            failed.append(f"{datetime.now().isoformat(timespec='seconds')} {f}: {e}")
    if failed:
        dst.mkdir(parents=True, exist_ok=True)
        with open(dst / ERRORS, "a", encoding="utf-8") as fh:
            fh.write("\n".join(failed) + "\n")
    return copied


def expire(dst, keep_days):
    cutoff = time.time() - keep_days * 86400
    removed = 0
    for f in Path(dst).rglob("*"):
        try:
            if not f.is_file() or f.name in (ERRORS, STAMP):
                continue
            stale_part = f.name.endswith(".part") and f.stat().st_mtime < time.time() - 86400
            if stale_part or f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        except OSError:
            continue
    return removed


def run(src, dst, keep_days=KEEP_DAYS):
    c = copy_new(src, dst, keep_days)
    r = expire(dst, keep_days)
    Path(dst).mkdir(parents=True, exist_ok=True)
    (Path(dst) / STAMP).write_text(
        f"{datetime.now().isoformat(timespec='seconds')} copied {c}, expired {r}, keep {keep_days} days\n", encoding="utf-8")
    return c, r


def main(argv):
    if not SOURCE_DIR.is_dir() or not any(SOURCE_DIR.rglob("*.jsonl")):
        print(f"no session logs found under {SOURCE_DIR}", file=sys.stderr)
        sys.exit(2)
    if "--dry-run" in argv:
        n = sum(1 for _ in SOURCE_DIR.rglob("*.jsonl"))
        print(f"would archive from {SOURCE_DIR} ({n} logs) into {ARCHIVE_DIR}, keeping {KEEP_DAYS} days")
        return
    c, r = run(SOURCE_DIR, ARCHIVE_DIR)
    print(f"archived {c} files into {ARCHIVE_DIR}; expired {r} older than {KEEP_DAYS} days")


if __name__ == "__main__":
    main(sys.argv[1:])
