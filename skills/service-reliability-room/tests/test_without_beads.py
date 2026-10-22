"""The store starts and runs without Beads, minus its work list. Each command is run as a person would run it,
as `python -I roomstate.py ...`, with bd off PATH and $ROOM_BD unset."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
NOTE = "work list unavailable (Beads not installed)"
INIT_NOTE = "Beads not found: the store runs without its work list; install Beads 1.3.0 to add it."


def no_bd_env():
    env = {k: v for k, v in os.environ.items() if k not in ("ROOM_BD", "PATH", "Path")}
    env["PATH"] = str(Path(sys.executable).parent)  # python only: no bd here
    return env


def run(script, *args):
    r = subprocess.run([sys.executable, "-I", str(SKILL_DIR / script), *map(str, args)], capture_output=True,
                       text=True, encoding="utf-8", env=no_bd_env())
    out = r.stdout + r.stderr
    assert "Traceback" not in out, out
    return r.returncode, out


@pytest.fixture
def state(tmp_path):
    return tmp_path / "cap" / "state"


def test_no_bd_on_the_test_path():
    import shutil
    assert shutil.which("bd", path=no_bd_env()["PATH"]) is None


def test_init_without_beads_writes_the_skeleton_and_says_so(state):
    code, out = run("roomstate.py", "init", state)
    assert code == 0, out
    assert INIT_NOTE in out
    assert (state / "engagement.json").is_file()
    assert (state / "log.jsonl").is_file()
    assert not (state / ".beads").exists()
    assert json.loads((state / "engagement.json").read_text(encoding="utf-8"))["journeys"] == []


def test_init_brief_go_set_validate_run_without_beads(state):
    assert run("roomstate.py", "init", state)[0] == 0
    code, out = run("roomstate.py", "brief", state)
    assert code == 0, out
    assert NOTE in out
    asks = out.split("## 4. Asks", 1)[1].split("\n## ", 1)[0]
    assert NOTE in asks and "(0)" not in asks, asks  # no counts that read as "none open"
    code, out = run("roomstate.py", "set", state, "capability", '"payments"')
    assert code == 5, out  # the go gate still holds: no go is logged yet
    code, out = run("roomstate.py", "log", state, "--kind", "go", "--text", "go on the plan", "--by", "person")
    assert code == 0, out
    assert NOTE in out
    code, out = run("roomstate.py", "set", state, "capability", '"payments"')
    assert code == 0, out
    assert NOTE in out
    assert json.loads((state / "engagement.json").read_text(encoding="utf-8"))["capability"] == "payments"
    code, out = run("roomstate.py", "validate", state)
    assert code == 0, out
    assert "valid" in out and NOTE in out
    code, out = run("roomstate.py", "brief", "--short", state)
    assert code == 0, out
    assert NOTE in out
    code, out = run("roomstate.py", "stamp", state, "--text", "closed", "--by", "chief")
    assert code == 0, out
    assert NOTE in out
    code, out = run("roomstate.py", "resume", state.parent)
    assert code == 0, out


def test_handover_and_the_view_run_without_beads(state):
    assert run("roomstate.py", "init", state)[0] == 0
    code, out = run("roomstate.py", "handover", state, "--text", "next: alerts")
    assert code == 0, out
    assert NOTE in out
    code, out = run("roomview.py", state)
    assert code == 0, out
    assert NOTE in (state / "view.html").read_text(encoding="utf-8")


def test_a_bd_command_without_beads_is_a_plain_refusal(state):
    assert run("roomstate.py", "init", state)[0] == 0
    run("roomstate.py", "log", state, "--kind", "go", "--text", "go", "--by", "person")
    code, out = run("roomstate.py", "bd", state, "list")
    assert code != 0
    assert NOTE in out


def test_brief_on_a_missing_store_is_one_plain_line(state):
    code, out = run("roomstate.py", "brief", state)
    assert code != 0
    assert len(out.strip().splitlines()) == 1, out
    assert "engagement.json" in out


def test_the_installing_section_says_the_room_runs_without_beads_and_where_to_get_it():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    install = text.split("## Installing", 1)[1].split("\n## ", 1)[0]
    assert "The room runs without Beads, minus its work list (work items and asks), until Beads is installed." in install
    assert "github.com/gastownhall/beads" in install
    assert "v1.3.0" in install and "checksums.txt" in install and "sha256" in install
    assert "steveyegge" not in text
