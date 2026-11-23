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
