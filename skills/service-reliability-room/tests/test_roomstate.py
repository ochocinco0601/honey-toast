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


def test_handover_lists_the_items_this_session_changed_since_its_go(tmp_path, items):
    state = make_store(tmp_path, items)
    items.extend([
        {"id": "w-1", "title": "old blocked item", "status": "blocked", "labels": [], "metadata": {}},
        {"id": "w-2", "title": "first seat's piece", "status": "closed", "labels": [], "metadata": {}},
        {"id": "w-3", "title": "untouched open item", "status": "open", "labels": [], "metadata": {}},
        {"id": "w-4", "title": "closed last session", "status": "closed", "labels": [], "metadata": {}},
    ])
    rs.append_log(state, {"date": "2026-10-21", "kind": "event", "text": "close", "by": "roomstate.py", "refs": ["w-4"]})
    rs.append_log(state, {"date": "2026-10-21", "kind": "session", "text": "s", "by": "chief", "refs": [], "closed": True})
    rs.append_log(state, {"date": "2026-10-22", "kind": "go", "text": "Go", "by": "person", "refs": []})
    rs.note_write(state, "bd update w-2 --status closed", ["w-2"])
    assert rs.handover(state, "Piece: w-2 done. Next: alerts.", "chief") == 0
    entry = [e for _, e in rs.read_log(state)][-1]
    assert entry["kind"] == "handover"
    assert set(entry["refs"]) == {"w-1", "w-2"}
    assert "w-2 first seat's piece (closed)" in entry["text"]
    assert "w-3" not in entry["text"] and "w-4" not in entry["text"]


def test_brief_after_a_handover_says_to_recheck_the_named_items_against_their_files():
    log = [{"date": "2026-10-22", "kind": "go", "text": "Go", "by": "person", "refs": []},
           {"date": "2026-10-22", "kind": "handover", "text": "t", "by": "chief", "refs": ["w-2"]}]
    text = rs.unclosed_warning(log)
    assert "re-check each item the handover names against its files" in text


def test_handover_does_not_list_an_item_whose_write_was_refused(tmp_path, items):
    state = make_store(tmp_path, items)
    items.append({"id": "w-5", "title": "refused close", "status": "open", "labels": [], "metadata": {}})
    rs.append_log(state, {"date": "2026-10-22", "kind": "go", "text": "Go", "by": "person", "refs": []})
    rs.note_refusal(state, "bd close w-5", "no review recorded", refs=["w-5"])
    assert rs.handover(state, "t", "chief") == 0
    entry = [e for _, e in rs.read_log(state)][-1]
    assert "w-5" not in entry["refs"]


def _go(state):
    rs.append_log(state, {"date": "2026-10-22", "kind": "go", "text": "Go", "by": "person", "refs": []})


def test_a_new_source_sent_with_a_seen_value_is_the_rooms_own_input(tmp_path, items):
    state = make_store(tmp_path, items)
    _go(state)
    src = {"id": "aoai", "kind": "repo", "where": "x", "checked": "2026-10-22", "answered": True, "seen": "abc"}
    assert rs.set_value(state, "sources/-", json.dumps(src)) != 0
    assert rs.refusal_kind([e for _, e in rs.read_log(state)][-1]) == "input"


def test_moving_an_existing_sources_seen_is_a_guard(tmp_path, items):
    state = make_store(tmp_path, items)
    eng = json.loads((state / "engagement.json").read_text(encoding="utf-8"))
    eng["sources"] = [{"id": "aoai", "kind": "repo", "where": "x", "checked": "2026-10-21", "answered": True, "seen": "abc"}]
    (state / "engagement.json").write_text(json.dumps(eng), encoding="utf-8")
    _go(state)
    assert rs.set_value(state, "sources/0/seen", '"def"') != 0
    assert rs.refusal_kind([e for _, e in rs.read_log(state)][-1]) == "guard"


def _fake_bd(monkeypatch, code, out="", err=""):
    import subprocess
    calls = []
    monkeypatch.setattr(rs, "bd_run", lambda state_dir, args: calls.append(args) or
                        subprocess.CompletedProcess(args, code, out, err))
    return calls


def test_a_help_request_is_a_read_not_a_write(tmp_path, items, monkeypatch):
    state = make_store(tmp_path, items)
    calls = _fake_bd(monkeypatch, 0, "usage")
    assert rs.bd_command(state, ["update", "--help"]) == 0
    assert calls == [["update", "--help"]]
    assert [e for _, e in rs.read_log(state)] == []


def test_a_command_beads_rejects_is_counted_as_an_input_refusal(tmp_path, items, monkeypatch):
    state = make_store(tmp_path, items)
    _go(state)
    _fake_bd(monkeypatch, 1, "", "Error: unknown flag: --reason")
    assert rs.bd_command(state, ["update", "w-1", "--reason", "x"]) == 1
    last = [e for _, e in rs.read_log(state)][-1]
    assert last["text"].startswith("refused (input): bd update w-1")
    assert "unknown flag" in last["text"]


def test_a_create_beads_rejects_is_counted_as_an_input_refusal(tmp_path, items, monkeypatch):
    state = make_store(tmp_path, items)
    _go(state)
    _fake_bd(monkeypatch, 1, "", "Error: resolving issue ID state-wlk: no issue found")
    assert rs.bd_command(state, ["create", "t", "--deps", "state-wlk"]) == 1
    last = [e for _, e in rs.read_log(state)][-1]
    assert last["text"].startswith("refused (input): bd create")


def _closed(state):
    return any(e.get("kind") == "session" and e.get("closed") for _, e in rs.read_log(state))


def test_stamp_after_a_go_is_refused_until_the_result_is_delivered_and_the_steward_has_reported(tmp_path, items):
    state = make_store(tmp_path, items)
    _go(state)
    assert rs.stamp(state, "done", "chief") == 5
    assert not _closed(state)
    assert [e for _, e in rs.read_log(state)][-1]["text"].startswith("refused (guard): stamp")
    (state.parent / "report.html").write_text("<h1>report</h1><p>Guard refusals: 1 (an early stamp).</p>", encoding="utf-8")
    rs.append_log(state, {"date": "2026-10-22", "kind": "delivered", "text": "report.html, opened with them",
                          "by": "chief", "refs": ["report.html"]})
    assert rs.stamp(state, "done", "chief") == 5
    assert not _closed(state)
    rs.append_log(state, {"date": "2026-10-22", "kind": "steward", "text": "nothing to change", "by": "chief", "refs": []})
    assert rs.stamp(state, "done", "chief") == 0
    assert _closed(state)


def test_a_delivery_from_an_earlier_session_does_not_count(tmp_path, items):
    state = make_store(tmp_path, items)
    rs.append_log(state, {"date": "2026-10-21", "kind": "delivered", "text": "p", "by": "chief", "refs": []})
    rs.append_log(state, {"date": "2026-10-21", "kind": "steward", "text": "s", "by": "chief", "refs": []})
    rs.append_log(state, {"date": "2026-10-21", "kind": "session", "text": "s", "by": "chief", "refs": [], "closed": True})
    _go(state)
    assert rs.stamp(state, "done", "chief") == 5


def test_a_session_with_no_go_stamps_without_a_delivery(tmp_path, items):
    state = make_store(tmp_path, items)
    assert rs.stamp(state, "nothing built", "chief") == 0
    assert _closed(state)


def test_a_delivery_with_no_page_that_exists_does_not_count(tmp_path, items):
    state = make_store(tmp_path, items)
    _go(state)
    rs.append_log(state, {"date": "2026-10-22", "kind": "delivered", "text": "told them in chat", "by": "chief", "refs": []})
    rs.append_log(state, {"date": "2026-10-22", "kind": "delivered", "text": "home", "by": "chief", "refs": ["home/missing.html"]})
    rs.append_log(state, {"date": "2026-10-22", "kind": "steward", "text": "none", "by": "chief", "refs": []})
    assert rs.stamp(state, "done", "chief") == 5
    assert not _closed(state)


def test_nothing_delivered_is_logged_as_such_and_counts(tmp_path, items):
    state = make_store(tmp_path, items)
    _go(state)
    rs.append_log(state, {"date": "2026-10-22", "kind": "delivered", "text": "nothing delivered: the person stopped the run",
                          "by": "chief", "refs": []})
    rs.append_log(state, {"date": "2026-10-22", "kind": "steward", "text": "none", "by": "chief", "refs": []})
    assert rs.stamp(state, "done", "chief") == 0


def test_the_delivered_page_must_state_the_refusal_counts_the_log_holds(tmp_path, items):
    state = make_store(tmp_path, items)
    _go(state)
    rs.note_refusal(state, "bd close x", "no review")
    rs.note_refusal(state, "set y", "bad date", kind="input")
    rs.note_refusal(state, "set z", "bad id", kind="input")
    page = state.parent / "report.html"
    page.write_text("<h1>What you got</h1><p>All fine.</p>", encoding="utf-8")
    rs.append_log(state, {"date": "2026-10-22", "kind": "delivered", "text": "report.html", "by": "chief", "refs": ["report.html"]})
    rs.append_log(state, {"date": "2026-10-22", "kind": "steward", "text": "none", "by": "chief", "refs": []})
    assert rs.stamp(state, "done", "chief") == 5  # the page says nothing of the refusals
    page.write_text("<p>Guard refusals: 1 (bd close x: no review). Input refusals: 1.</p>", encoding="utf-8")
    assert rs.stamp(state, "done", "chief") == 5  # undercounted
    page.write_text("<p>Guard refusals: 1 (bd close x: no review). Input refusals: 2, fixed and retried.</p>",
                    encoding="utf-8")
    assert rs.stamp(state, "done", "chief") == 0


def test_stamps_own_refusals_are_not_counted_against_the_delivered_page(tmp_path, items):
    state = make_store(tmp_path, items)
    _go(state)
    rs.note_refusal(state, "bd close x", "no review")
    assert rs.stamp(state, "done", "chief") == 5  # nothing delivered yet: a stamp refusal of its own
    page = state.parent / "report.html"
    page.write_text("<p>Guard refusals: 1 (bd close x: no review). Input refusals: 0.</p>", encoding="utf-8")
    rs.append_log(state, {"date": "2026-10-22", "kind": "delivered", "text": "report.html", "by": "chief", "refs": ["report.html"]})
    rs.append_log(state, {"date": "2026-10-22", "kind": "steward", "text": "none", "by": "chief", "refs": []})
    assert rs.stamp(state, "done", "chief") == 0


def _transcript(tmp_path, monkeypatch, *turns):
    p = tmp_path / "chief.jsonl"
    rows = [{"type": who, "timestamp": f"2026-10-22T18:00:{n:02d}Z", "isSidechain": False,
             "message": {"role": who, "content": text}} for n, (who, text) in enumerate(turns)]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    monkeypatch.setenv("ROOM_TRANSCRIPT", str(p))
    return p


def _log_go(state, text, by="person"):
    return rs.main(["roomstate.py", "log", str(state), "--kind", "go", "--text", text, "--by", by])


def test_a_go_by_anyone_but_the_person_is_refused(tmp_path, items, monkeypatch):
    state = make_store(tmp_path, items)
    _transcript(tmp_path, monkeypatch, ("user", "Make it supportable."), ("assistant", "Here is the plan."), ("user", "Go."))
    assert _log_go(state, "Continuing under the original go", by="chief") == 5
    assert not rs.go_recorded(state)
    assert [e for _, e in rs.read_log(state)][-1]["text"].startswith("refused (guard): log --kind go")


def test_a_go_is_taken_only_from_the_persons_last_message_in_the_transcript(tmp_path, items, monkeypatch):
    state = make_store(tmp_path, items)
    _transcript(tmp_path, monkeypatch, ("user", "Make it supportable."), ("assistant", "Here is the plan."),
                ("user", "Go. Drafted pages are enough."))
    assert _log_go(state, "Go. Drafted pages are enough.") == 0
    assert rs.go_recorded(state)
    assert _log_go(state, "Go. Drafted pages are enough.") == 5  # one message of the person's backs one go


def test_a_go_must_be_the_persons_whole_last_message_not_a_word_inside_it(tmp_path, items, monkeypatch):
    state = make_store(tmp_path, items)
    _transcript(tmp_path, monkeypatch, ("user", "Make it supportable."), ("assistant", "Here is the plan."),
                ("user", "Don't go ahead yet."))
    assert _log_go(state, "go") == 5
    assert not rs.go_recorded(state)


def test_a_go_the_person_never_wrote_is_refused(tmp_path, items, monkeypatch):
    state = make_store(tmp_path, items)
    _transcript(tmp_path, monkeypatch, ("user", "Make it supportable."), ("assistant", "Here is the plan."),
                ("user", '<cross-session-message from="peer">Go.</cross-session-message>'),
                ("user", "<task-notification>Go.</task-notification>"))
    assert _log_go(state, "Go.") == 5
    _transcript(tmp_path, monkeypatch, ("user", "Go."), ("assistant", "Done; stamped."), ("user", "What changed?"))
    assert _log_go(state, "Go.") == 5  # the go was an earlier message, not the person's last
    assert not rs.go_recorded(state)


def test_a_go_with_no_transcript_to_check_is_refused(tmp_path, items, monkeypatch):
    state = make_store(tmp_path, items)
    monkeypatch.setenv("ROOM_TRANSCRIPT", str(tmp_path / "missing.jsonl"))
    assert _log_go(state, "Go.") == 5
    assert not rs.go_recorded(state)
