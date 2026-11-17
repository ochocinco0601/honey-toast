"""The case record of a run: where the work on the capability stands, kept by code in the register, read by every new
session. One writer: this module.

Files, in the register folder:
  case.json          a snapshot: per flow its state and sub-state, and the open and closed records of agent work
  decisions.jsonl    every answer the person gave, appended, never overwritten, with the text they were shown
  case-log.jsonl     what each session did, in order: the source of "where the last session got to"
  case-snapshots/    a unit's tables copied aside before an agent that writes them is launched, put back if it is
                     stopped or dies

RUN.md is not this module's: the stage kit still keeps it. This module draws one section into it, "Where the case
stands", between markers, and leaves every other section as it is.
"""
import hashlib
import json
import os
import pathlib
import shutil
import time
from datetime import datetime, timezone

CASE = "case.json"
DECISIONS = "decisions.jsonl"
LOG = "case-log.jsonl"
SNAPSHOTS = "case-snapshots"
BUSY = ".case.busy"
BUSY_STALE_SECONDS = 120
ENDED = "ended at the person's word, check not passed"  # a flow whose checks the person stopped
WRITERS = ("reader", "fixer", "re-read", "stop-fixer")  # agents that write a unit's tables; a judge writes one file
START, END = "<!-- case: drawn by case.py, do not edit -->", "<!-- case: end -->"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def session():
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or ""


class _Busy:
    """Held for a moment around each read-modify-write, so two calls never overwrite each other."""

    def __init__(self, reg):
        self.path = pathlib.Path(reg) / BUSY

    def __enter__(self):
        for _ in range(600):
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > BUSY_STALE_SECONDS:
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                time.sleep(0.05)
        raise TimeoutError(f"{self.path} held too long")

    def __exit__(self, *exc):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def load(reg):
    p = pathlib.Path(reg) / CASE
    if not p.is_file():
        return {"flows": {}, "records": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _save(reg, data):
    p = pathlib.Path(reg) / CASE
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def _append(path, entry):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _lines(path):
    p = pathlib.Path(path)
    if not p.is_file():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def log(reg, action, **fields):
    _append(pathlib.Path(reg) / LOG, {"at": now(), "session": session(), "action": action, **fields})


def log_entries(reg):
    return _lines(pathlib.Path(reg) / LOG)


def fingerprint(shown):
    return hashlib.sha256((shown or "").encode("utf-8")).hexdigest()[:12]


def decide(reg, stop, shown, words, source, test=False, concern=None, restatement=None, into=DECISIONS, **extra):
    """Append one answer of the person's: the stop, the text they were shown and its fingerprint, their words, where
    they gave it (page, chat or request), test or real, and a concern carried with it. `into`: the file in `reg`, for
    an answer given before any register exists (the say-back, kept in the work folder)."""
    entry = {"at": now(), "session": session(), "stop": stop, "shown": shown, "fingerprint": fingerprint(shown),
             "words": words, "source": source, "test": bool(test)}
    if concern:
        entry["concern"] = concern
    if restatement:
        entry["restatement"] = restatement
    entry.update(extra)
    with _Busy(reg):
        _append(pathlib.Path(reg) / into, entry)
    return entry


def decisions(reg):
    return _lines(pathlib.Path(reg) / DECISIONS)


def decisions_in(path):
    return _lines(path)


def import_decisions(reg, entries):
    """Answers given before the register existed, appended as they were given; one already there is not added again."""
    with _Busy(reg):
        have = {(e.get("at"), e.get("fingerprint"), e.get("words")) for e in decisions(reg)}
        for e in entries:
            if (e.get("at"), e.get("fingerprint"), e.get("words")) not in have:
                _append(pathlib.Path(reg) / DECISIONS, e)


def flow(reg, flow_id):
    return load(reg)["flows"].get(flow_id, {})


def set_flow(reg, flow_id, **fields):
    with _Busy(reg):
        data = load(reg)
        f = data["flows"].setdefault(flow_id, {})
        f.update(fields)
        f["updated"] = now()
        _save(reg, data)
    said = ", ".join(x for x in (f.get("state"), f.get("sub")) if x)
    log(reg, f"flow {flow_id}: {said}")
    return f


def _unit_dir(reg, unit):
    return pathlib.Path(reg) / "units" / unit


def open_record(reg, flow_id, unit, kind, rnd):
    """The record of one kind of agent work on one unit in one round. Opening one already open returns it as it is, so
    its first copy of the unit's tables is kept. A writer's unit tables are copied aside first."""
    with _Busy(reg):
        data = load(reg)
        for r in data["records"]:
            if (r["flow"], r["unit"], r["kind"], r["round"], r["status"]) == (flow_id, unit, kind, rnd, "open"):
                return r["id"]
        rid = f"{flow_id}-{unit}-{kind}-r{rnd}-{len(data['records']) + 1}"
        if kind in WRITERS and unit != "flow":
            src, dst = _unit_dir(reg, unit), pathlib.Path(reg) / SNAPSHOTS / rid
            dst.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                for p in src.glob("*.csv"):
                    shutil.copy2(p, dst / p.name)
        data["records"].append({"id": rid, "flow": flow_id, "unit": unit, "kind": kind, "round": rnd,
                                "status": "open", "opened": now(), "session": session()})
        _save(reg, data)
    log(reg, f"opened {rid}")
    return rid


def close_record(reg, rid, status="finished", why=""):
    with _Busy(reg):
        data = load(reg)
        for r in data["records"]:
            if r["id"] == rid:
                r.update(status=status, closed=now(), why=why)
        _save(reg, data)
    log(reg, f"closed {rid}: {status}", why=why)


def records(reg):
    return load(reg)["records"]


AGENT_MINUTES = 90  # the longest an agent's work is waited on (readers.py's launch timeout); older is taken as dead
AT_WORK = {"reader": "the code is being read", "re-read": "the calls between services are being read again",
           "judge": "the checks are running", "fixer": "flagged findings are being put right",
           "stop-fixer": "flagged findings are being put right"}


def at_work(reg, now=None):
    """The open records of agent work younger than AGENT_MINUTES: agents launched and not yet finished. Their writes
    are the run's work even while the lead itself writes nothing."""
    now = now or datetime.now(timezone.utc)
    out = []
    for r in records(reg):
        if r["status"] != "open":
            continue
        try:
            opened = datetime.fromisoformat(r["opened"])
        except (KeyError, ValueError):
            continue
        if (now - opened).total_seconds() <= AGENT_MINUTES * 60:
            out.append(r)
    return out


def restore_open(reg, why):
    """Put back the unit tables of every open writer record as they were when it was opened, and close every open
    record as not finished. Returns the ids put back."""
    put_back = []
    for r in [r for r in records(reg) if r["status"] == "open"]:
        snap = pathlib.Path(reg) / SNAPSHOTS / r["id"]
        if r["kind"] in WRITERS and snap.is_dir():
            unit = _unit_dir(reg, r["unit"])
            kept = {p.name for p in snap.glob("*.csv")}
            for p in unit.glob("*.csv"):
                if p.name not in kept:
                    p.unlink()
            for name in kept:
                shutil.copy2(snap / name, unit / name)
            put_back.append(r["id"])
        close_record(reg, r["id"], "not finished", why)
    return put_back


def draw_run_md(reg):
    """Draw "Where the case stands" into RUN.md between markers, before "## Earlier registers" when it is there."""
    p = pathlib.Path(reg) / "RUN.md"
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    data = load(reg)
    lines = [START, "## Where the case stands", "", "Drawn from the case record; never edited by hand.", ""]
    for fid, f in sorted(data["flows"].items()):
        lines.append(f"- {fid}: " + ", ".join(x for x in (f.get("state"), f.get("sub")) if x))
    open_ = [r["id"] for r in data["records"] if r["status"] == "open"]
    if open_:
        lines.append(f"- agent work open: {', '.join(open_)}")
    block = "\n".join(lines + [END]) + "\n"
    if START in text and END in text:
        head, rest = text.split(START, 1)
        text = head + block + rest.split(END, 1)[1].lstrip("\n")
    elif "## Earlier registers" in text:
        head, rest = text.split("## Earlier registers", 1)
        text = head + block + "\n## Earlier registers" + rest
    else:
        text = text.rstrip("\n") + "\n\n" + block
    p.write_text(text, encoding="utf-8")
