"""Tests for dialogue.py: the chief's conversation with the person, read out of a Claude Code transcript."""
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR))
import dialogue  # noqa: E402


def entry(kind, content, ts, **extra):
    return {"type": kind, "timestamp": ts, "isSidechain": False, "message": {"role": kind, "content": content}, **extra}


def write(tmp_path, entries):
    p = tmp_path / "chief.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in entries) + "\nnot json\n", encoding="utf-8")
    return p


def sample(tmp_path):
    return write(tmp_path, [
        entry("user", "Make the payment flow supportable.", "2026-10-22T18:00:00Z"),
        entry("assistant", [{"type": "thinking", "thinking": "hidden"}], "2026-10-22T18:00:01Z"),
        entry("assistant", [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}], "2026-10-22T18:00:02Z"),
        entry("user", [{"type": "tool_result", "tool_use_id": "t1", "content": "noise"}], "2026-10-22T18:00:03Z"),
        entry("assistant", [{"type": "text", "text": "Here is the plan."}], "2026-10-22T18:00:04Z"),
        entry("user", [{"type": "text", "text": "<system-reminder>injected</system-reminder>"}], "2026-10-22T18:00:05Z"),
        entry("user", "meta", "2026-10-22T18:00:06Z", isMeta=True),
        entry("assistant", [{"type": "text", "text": "seat chatter"}], "2026-10-22T18:00:07Z", isSidechain=True),
        entry("user", [{"type": "text", "text": "Where is the result?"}], "2026-10-22T18:05:00Z"),
    ])


def test_keeps_only_the_person_and_the_chiefs_words(tmp_path):
    turns = dialogue.read(sample(tmp_path))
    assert [(t["who"], t["text"]) for t in turns] == [
        ("person", "Make the payment flow supportable."),
        ("chief", "Here is the plan."),
        ("person", "Where is the result?"),
    ]


def test_an_injected_block_before_the_persons_words_is_removed(tmp_path):
    p = write(tmp_path, [entry("user", "<browser_instruction>tool notes</browser_instruction>Do you understand?", "2026-10-22T18:00:00Z")])
    assert [t["text"] for t in dialogue.read(p)] == ["Do you understand?"]


def test_since_drops_earlier_turns(tmp_path):
    turns = dialogue.read(sample(tmp_path), since="2026-10-22T18:00:04Z")
    assert [t["text"] for t in turns] == ["Here is the plan.", "Where is the result?"]


def test_last_person_turn_unanswered_is_flagged(tmp_path, capsys):
    assert dialogue.main([str(sample(tmp_path))]) == 0
    out = capsys.readouterr().out
    assert "Where is the result?" in out
    assert "unanswered" in out


def test_answered_last_turn_is_not_flagged(tmp_path, capsys):
    p = write(tmp_path, [
        entry("user", "Status?", "2026-10-22T18:00:00Z"),
        entry("assistant", [{"type": "text", "text": "Done; the page is open."}], "2026-10-22T18:00:01Z"),
    ])
    assert dialogue.main([str(p)]) == 0
    assert "unanswered" not in capsys.readouterr().out


def test_a_compaction_summary_is_not_the_person_speaking(tmp_path):
    p = write(tmp_path, [
        entry("user", "Make it supportable.", "2026-10-22T18:00:00Z"),
        entry("assistant", [{"type": "text", "text": "Done; the page is report.html."}], "2026-10-22T18:00:01Z"),
        entry("user", "This session is being continued from a previous conversation.", "2026-10-22T18:00:02Z",
              isCompactSummary=True),
        entry("user", "shown only in the transcript", "2026-10-22T18:00:03Z", isVisibleInTranscriptOnly=True),
    ])
    turns = dialogue.read(str(p))
    assert [t["who"] for t in turns] == ["person", "chief"]
