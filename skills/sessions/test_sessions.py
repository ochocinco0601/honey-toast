import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("sessions.py")


def run(config_dir, *args, me=""):
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config_dir), CLAUDE_CODE_SESSION_ID=me)
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True, check=True).stdout


def session(root, pid, sid, name, updated):
    (root / "sessions" / f"{pid}.json").write_text(json.dumps(
        {"pid": pid, "sessionId": sid, "name": name, "status": "idle", "updatedAt": updated, "cwd": "C:\\x\\repo"}))


def log(root, sid, *records):
    d = root / "projects" / "C--x-repo"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")


def test_lists_live_sessions_with_tab_title_and_skips_dead_ones(tmp_path):
    (tmp_path / "sessions").mkdir()
    me = os.getpid()
    session(tmp_path, me, "aaa-111", "repo-a1", 2000)
    log(tmp_path, "aaa-111", {"type": "ai-title", "aiTitle": "Old title"}, {"type": "ai-title", "aiTitle": "Grafana work"})
    session(tmp_path, 999999, "dead-222", "repo-zz", 3000)
    log(tmp_path, "dead-222", {"type": "ai-title", "aiTitle": "Closed one"})

    out = run(tmp_path)

    assert "| 1 | Grafana work | repo-a1 | aaa-111 | idle |" in out
    assert "Old title" not in out
    assert "dead-222" not in out


def test_renamed_tab_wins_over_generated_title(tmp_path):
    (tmp_path / "sessions").mkdir()
    session(tmp_path, os.getpid(), "bbb-333", "repo-b3", 1000)
    log(tmp_path, "bbb-333", {"type": "custom-title", "customTitle": "My rename"}, {"type": "ai-title", "aiTitle": "Generated"})

    assert "| 1 | My rename | repo-b3 | bbb-333 |" in run(tmp_path)


def test_rows_are_numbered_most_recent_first(tmp_path):
    (tmp_path / "sessions").mkdir()
    session(tmp_path, os.getpid(), "old-1", "repo-o1", 1000)
    log(tmp_path, "old-1", {"type": "ai-title", "aiTitle": "Older"})
    session(tmp_path, os.getppid(), "new-2", "repo-n2", 5000)
    log(tmp_path, "new-2", {"type": "ai-title", "aiTitle": "Newer"})

    out = run(tmp_path)

    assert "| 1 | Newer |" in out
    assert "| 2 | Older |" in out


def test_find_by_tab_title_covers_open_and_closed_sessions_and_gives_the_transcript(tmp_path):
    (tmp_path / "sessions").mkdir()
    session(tmp_path, os.getpid(), "open-1", "repo-o1", 1000)
    log(tmp_path, "open-1", {"type": "ai-title", "aiTitle": "Grafana dashboard work"})
    log(tmp_path, "closed-2", {"type": "ai-title", "aiTitle": "Older grafana dashboard pass"})
    log(tmp_path, "other-3", {"type": "ai-title", "aiTitle": "Unrelated"})

    out = run(tmp_path, "find", "grafana dashboard")

    assert "| 1 | Grafana dashboard work | open | repo-o1 | open-1 |" in out
    assert "| 2 | Older grafana dashboard pass | closed |  | closed-2 |" in out
    assert str(tmp_path / "projects" / "C--x-repo" / "open-1.jsonl") in out
    assert "other-3" not in out


def test_find_never_returns_the_session_asking(tmp_path):
    (tmp_path / "sessions").mkdir()
    log(tmp_path, "me-1", {"type": "ai-title", "aiTitle": "Second set of eyes on grafana"})
    log(tmp_path, "them-2", {"type": "ai-title", "aiTitle": "Grafana dashboard work"})

    out = run(tmp_path, "find", "grafana", me="me-1")

    assert "them-2" in out
    assert "me-1" not in out


def test_list_marks_the_session_asking_since_it_often_takes_the_pasted_title(tmp_path):
    (tmp_path / "sessions").mkdir()
    session(tmp_path, os.getpid(), "me-1", "repo-m1", 5000)
    log(tmp_path, "me-1", {"type": "ai-title", "aiTitle": "Session start readout"})
    session(tmp_path, os.getppid(), "them-2", "repo-t2", 1000)
    log(tmp_path, "them-2", {"type": "ai-title", "aiTitle": "Session start readout"})

    out = run(tmp_path, me="me-1")

    assert "| Session start readout (this session, not the one meant) | repo-m1 | me-1 |" in out
    assert "| 2 | Session start readout | repo-t2 | them-2 |" in out


def test_find_says_so_when_no_title_matches(tmp_path):
    (tmp_path / "sessions").mkdir()
    log(tmp_path, "a-1", {"type": "ai-title", "aiTitle": "Something else"})
    assert "No session has a tab title matching" in run(tmp_path, "find", "grafana")


def test_says_so_when_nothing_is_open(tmp_path):
    (tmp_path / "sessions").mkdir()
    assert "No open Claude Code sessions" in run(tmp_path)
