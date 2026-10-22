"""Tests for roomstate.py's validate and refusal logging. Beads is replaced by a stand-in, so no bd install is needed."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import roomstate as rs  # noqa: E402


def make_store(tmp_path, items):
    state = tmp_path / "cap" / "state"
    (state / ".beads").mkdir(parents=True)
    eng = {"schema": rs.SCHEMA, "capability": "c", "intent": "i", "end_point": "e", "home": "h",
           "sources": [], "components": [{"id": "comp", "name": "n", "owner": None, "depends_on": []}],
           "journeys": [{"id": "J1", "name": "j", "components": ["comp"], "judgment_step": False, "rungs": {}}],
           "published": []}
    (state / "engagement.json").write_text(json.dumps(eng), encoding="utf-8")
    return state


@pytest.fixture
def items(monkeypatch):
    found = []
    monkeypatch.setattr(rs, "bd_items", lambda state_dir: found)
    return found


def test_a_second_journey_label_that_does_not_resolve_is_an_error(tmp_path, items):
    items.append({"id": "w-1", "title": "t", "status": "open", "labels": ["journey:J1", "journey:J9", "rung:alerts"],
                  "metadata": {}})
    errors = rs.validate(make_store(tmp_path, items))
    assert any("label journey:J9 does not resolve" in e for e in errors), errors


def test_an_item_belongs_to_at_most_one_journey_and_one_rung(tmp_path, items):
    items.append({"id": "w-1", "title": "t", "status": "open", "labels": ["journey:J1", "journey:J1x", "rung:alerts"],
                  "metadata": {}})
    errors = rs.validate(make_store(tmp_path, items))
    assert any("at most one journey and one rung" in e for e in errors), errors


def test_one_resolving_journey_and_rung_is_valid(tmp_path, items):
    items.append({"id": "w-1", "title": "t", "status": "open", "labels": ["journey:J1", "rung:alerts"], "metadata": {}})
    assert rs.validate(make_store(tmp_path, items)) == []


def test_refusals_are_labelled_by_kind(tmp_path, items):
    state = make_store(tmp_path, items)
    rs.note_refusal(state, "set home", "no go recorded for this session")
    rs.note_refusal(state, "set journeys/0", "the store would not validate", kind="input")
    log = [e for _, e in rs.read_log(state)]
    assert [rs.refusal_kind(e) for e in log] == ["guard", "input"]
    assert log[0]["text"].startswith("refused (guard): set home")
