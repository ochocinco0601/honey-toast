"""Pins the room's name where a session or the person depends on the exact words: the skill's name and triggers,
the compaction hook's path, the handover sentence, the store's schema id and the view's title."""
import json
import re
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR))
import roomstate as rs  # noqa: E402
import roomview  # noqa: E402

TEXT = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
FRONT = TEXT.split("---")[1]


def front_field(name):
    m = re.search(rf"^{name}: (.*)$", FRONT, re.M)
    assert m, f"no {name} in SKILL.md's frontmatter"
    return m.group(1)


def test_the_skill_is_named_for_its_folder():
    assert front_field("name") == "service-reliability-room"
    assert SKILL_DIR.name == "service-reliability-room"


@pytest.mark.parametrize("phrase", [
    '"convene the service reliability room"',
    '"continue the service reliability room on <capability>"',
    '"second engineer for the service reliability room on <capability>"',
    '"update the room"',
])
def test_each_trigger_phrase_is_in_the_description(phrase):
    assert phrase in front_field("description")


def test_the_compaction_hook_runs_this_folders_roomstate():
    assert "matcher: \"compact\"" in FRONT
    assert "$CLAUDE_PROJECT_DIR/.claude/skills/service-reliability-room/roomstate.py" in FRONT
    assert "service reliability room: could not run roomstate.py resume; run brief by hand" in FRONT


def test_the_handover_sentence(tmp_path, monkeypatch, capsys):
    state = tmp_path / "chat-app" / "state"
    state.mkdir(parents=True)
    (state / "engagement.json").write_text(json.dumps({"capability": "Chat app"}), encoding="utf-8")
    monkeypatch.setattr(rs, "bd_items", lambda state_dir: [])
    assert rs.handover(state, "Piece: W3-E1. Next: walk it.", "chief") == 0
    out = capsys.readouterr().out
    assert f"Continue the service reliability room on Chat app; the store is at {state}." in out


def test_the_resume_header_names_the_room():
    assert "A service-reliability-room engagement was left open." in (SKILL_DIR / "roomstate.py").read_text(encoding="utf-8")


def test_the_schema_id():
    assert rs.SCHEMA == "srr-engagement/1"


def test_the_view_title():
    src = (SKILL_DIR / "roomview.py").read_text(encoding="utf-8")
    assert ": service reliability room view</title>" in src
    assert roomview  # imported, so the view module at least loads
