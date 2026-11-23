"""One logged writer for a RUN.md row's status: set_row edits the row and appends the change to case-log.jsonl
({"at", "session", "action": "step", "flow", "row", "from", "to"}), so the run status page times the step exactly
(step_times reads these lines). A change made any other way is still noticed by the page, but only as "about"
(step_times.seen_changes). `python go.py <register> --row "<the row's lead>" --to done|doing` calls this. Python
standard library only."""
import datetime as dt
import json
import pathlib
import re

STATUSES = ("to do", "doing", "done", "blocked", "not picked")


def _flow(reg):
    try:
        return (json.loads((pathlib.Path(reg) / "scope.json").read_text(encoding="utf-8-sig")).get("flow_id")
                or None)
    except (OSError, ValueError):
        return None


ROW = re.compile(r"^\| ([^|\n]*?) \| ([^|\n]*?) \|", re.M)


def statuses(text):
    """{a row's whole lead: its status} of a RUN.md text's status table rows."""
    return {m.group(1).strip(): m.group(2).strip() for m in ROW.finditer(text or "")
            if m.group(1).strip() not in ("Phase", "") and not m.group(1).strip().startswith("---")}


def write(path, text, flow=None, by=None):
    """Write RUN.md's `text` to `path`, logging each row whose status it changes, as set_row logs one. Every kit
    script that rewrites RUN.md writes it through here, so no status change of the kit's goes unlogged."""
    path = pathlib.Path(path)
    before = statuses(path.read_text(encoding="utf-8")) if path.is_file() else {}
    path.write_text(text, encoding="utf-8", newline="\n")
    changed = [(lead, before[lead], to) for lead, to in statuses(text).items()
               if lead in before and before[lead] != to]
    if not changed:
        return
    import case
    when = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    fl = flow or _flow(path.parent)
    for lead, frm, to in changed:
        entry = {"at": when, "session": case.session(), "action": "step", "flow": fl, "row": lead, "from": frm,
                 "to": to}
        if by:
            entry["by"] = by
        case._append(path.parent / case.LOG, entry)


def set_row(reg, lead, status, flow=None, at=None, by=None):
    """Set the RUN.md row whose first cell starts with `lead` to `status`, and log the change. Returns (the row's whole
    lead, its status before), or a reason string when no single row matches or the status is not one of STATUSES.
    Setting a row to the status it holds writes nothing and logs nothing."""
    reg = pathlib.Path(reg)
    if status not in STATUSES:
        return f"the status must be one of {', '.join(STATUSES)}, not {status!r}"
    p = reg / "RUN.md"
    if not p.is_file():
        return "this register has no RUN.md"
    text = p.read_text(encoding="utf-8")
    want = lead.strip()
    found = [m for m in re.finditer(r"^\| ([^|\n]*?) \| ([^|\n]*?) \|", text, re.M)
             if m.group(1).strip().startswith(want) and m.group(1).strip() not in ("Phase", "---")]
    if len(found) != 1:
        return (f"no row of RUN.md starts with {want!r}" if not found else
                f"{len(found)} rows of RUN.md start with {want!r}: give more of the row's lead")
    m = found[0]
    whole, before = m.group(1).strip(), m.group(2).strip()
    if before == status:
        return whole, before
    p.write_text(text[:m.start(2)] + status + text[m.end(2):], encoding="utf-8", newline="\n")
    import case
    when = (at or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc).isoformat(timespec="seconds")
    entry = {"at": when, "session": case.session(), "action": "step", "flow": flow or _flow(reg), "row": whole,
             "from": before, "to": status}
    if by:
        entry["by"] = by
    case._append(reg / case.LOG, entry)
    return whole, before


OPEN = ("to do", "doing")
GO_ROW = "The go on the plan"
MAP_STAMP = re.compile(r"<!-- bfo-map-drawn-for (\{.*?\}) -->")


def map_stamp(flow_id):
    """The line the map's drawing ends with: the flow it was drawn for, so the drawing proves that flow's phases and
    no other's, however the register's files are copied or timed."""
    return f"\n<!-- bfo-map-drawn-for {json.dumps({'flow': flow_id})} -->\n"


def map_flow(text):
    """The flow a drawing was made for, or None for one drawn before drawings carried it."""
    m = MAP_STAMP.search(text or "")
    try:
        return json.loads(m.group(1)).get("flow") if m else None
    except ValueError:
        return None


def current_flow(reg):
    """The id of the flow worked now, or "" with no go recorded."""
    import go
    return go.flow_id_of(reg, go.load(reg)) if (pathlib.Path(reg) / "scope.json").is_file() else ""


def counts_for(reg, made_for):
    """A proof made for `made_for` counts for the flow worked now only when both name the same flow, by a non-empty
    id. A proof that names no flow (made before proofs carried one, or before any go) counts for none: its phase is
    done again, or set by the lead, never inherited."""
    now = current_flow(reg)
    return bool(made_for) and bool(now) and made_for == now


def stage_proof(reg, rel):
    import flow_outputs
    p = pathlib.Path(reg) / rel
    if not (p.is_file() and p.stat().st_size > 0):
        return False
    got = flow_outputs.stamp_of(p.read_text(encoding="utf-8", errors="replace"))
    return counts_for(reg, (got or {}).get("flow"))


def map_proof(reg):
    p = pathlib.Path(reg) / "views.html"
    if not (p.is_file() and p.stat().st_size > 0):
        return False
    return counts_for(reg, map_flow(p.read_text(encoding="utf-8", errors="replace")))


def verdict_this_flow(reg):
    """The done check's stored verdict was made for the flow worked now: an earlier flow's DONE says nothing of it."""
    import run_status
    p = pathlib.Path(reg) / run_status.VERDICT
    try:
        got = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return counts_for(reg, got.get("flow") if isinstance(got, dict) else None)


def proved(reg):
    """{a phase row's opening words: "done"} for each phase whose proof is in the register and was made for the flow
    worked now, read from the files alone, never from a status the lead set: the map drawn proves phases 1 to 3; each
    stage the pick takes that far having its MEASURES.md, ALERT.md or RUNBOOK.md proves 4, 5a or 5b; the done check
    having found the outputs done on the map as it is proves 6. Each proof names the flow it was made for (the
    drawing's and the outputs' stamps, the verdict's flow), never a file time: a proof an earlier flow left proves
    nothing of this one, however the register is copied."""
    import go
    import run_status
    reg = pathlib.Path(reg)
    out = {}
    rows = statuses((reg / "RUN.md").read_text(encoding="utf-8")) if (reg / "RUN.md").is_file() else {}
    if not any(k.startswith(GO_ROW) and v == "done" for k, v in rows.items()):
        return out  # nothing after the go is done before it
    if map_proof(reg):
        out.update({"1 ": "done", "2 ": "done", "3 ": "done"})
    depth = ((go.load(reg) or {}).get("depth") or {}) if (reg / "scope.json").is_file() else {}
    held = run_status.held_runbooks(reg) if depth else set()
    for lead, need, name in (("4 ", ("measure", "alerting", "runbooks"), "MEASURES.md"),
                             ("5a ", ("alerting", "runbooks"), "ALERT.md"), ("5b ", ("runbooks",), "RUNBOOK.md")):
        owed = [f"stage-{s}/{name}" for s, d in depth.items() if d in need]
        if owed and all(stage_proof(reg, f) or f in held for f in owed):
            out[lead] = "done"
    if run_status.outputs_hold(reg) and verdict_this_flow(reg):
        out["6 "] = "done"
    return out


def derived(text, got):
    """RUN.md's `text` with each row still to do or doing that `got` (proved) shows done set done."""
    for lead, status in got.items():
        text = re.sub(r"^(\| " + re.escape(lead) + r"[^|\n]*\| )(?:to do|doing)( \|)", r"\g<1>" + status + r"\2",
                      text, count=1, flags=re.M)
    return text


def reconcile(reg):
    """Write into RUN.md, through the logged writer, every phase its files prove done; never a status the person's
    pick or a block set. Returns the rows it changed. Never raises: the record must not stop a run."""
    p = pathlib.Path(reg) / "RUN.md"
    try:
        if not p.is_file():
            return []
        old = p.read_text(encoding="utf-8")
        new = derived(old, proved(reg))
        if new == old:
            return []
        write(p, new, by="derived from the phase's files")
        return [k for k, v in statuses(new).items() if statuses(old).get(k) != v]
    except Exception:  # noqa: BLE001
        return []
