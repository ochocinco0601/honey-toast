"""A time on every step of the run status page's progress list, read from what the run already records:

- the first look: from the person's Start (the say-back's answer) to the brief (PLAN.md written);
- process mapping: the flow's own lines in case-log.jsonl (`flow F<n>: mapping, <sub>` ... `mapped`), as spans that
  leave out the wait at the pick of how far each stage goes, which shows on that decision instead;
- every other step: the changes of its RUN.md row. RUN.md holds no times and many places (the session among them)
  change it, so each draw of the page compares the rows with the last change logged and logs any it has not seen,
  marked `seen`; a time resting on a seen line is shown as "about ... (noticed)", never as exact. The first sight of
  a row records its state only (a baseline), so a step done before the page first looked shows "time not recorded".

Never raises; a time that cannot be read is "time not recorded". Python standard library only."""
import datetime as dt
import json
import pathlib
import re

CASE_LOG = "case-log.jsonl"
FLOW_LINE = re.compile(r"^flow (F\d+): (mapping|mapped|ended)(?:, (.+))?$")


def _when(v):
    try:
        t = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _lines(p):
    out = []
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict):
                    out.append(d)
    except OSError:
        pass
    return out


def _mtime(p):
    try:
        return dt.datetime.fromtimestamp(pathlib.Path(p).stat().st_mtime, dt.timezone.utc)
    except OSError:
        return None


def start_answer(reg):
    """When the person pressed Start (or said it), from the say-back's record; else None."""
    reg = pathlib.Path(reg)
    sb = {}
    try:
        sb = json.loads((reg / "say-back.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    if sb.get("state") == "started" and sb.get("answered"):
        return _when(sb["answered"])
    for name in ("decisions.jsonl", "say-back-decisions.jsonl"):
        got = [_when(d.get("at")) for d in _lines(reg / name) if d.get("kind") == "start"]
        got = [t for t in got if t]
        if got:
            return max(got)
    return None


def mapping_spans(reg, flow):
    """[(start, end or None)] of process mapping for `flow` (F1), leaving out the wait at the pick: a span from the
    first `mapping` line to `mapping, pick` (or `mapped`), then from the first `mapping, <sub>` after the pick to
    `mapped` or `ended`; each re-entry after `mapped` opens another span. Also returns when the pick began, or None."""
    spans, open_at, pick_at = [], None, None
    for d in _lines(pathlib.Path(reg) / CASE_LOG):
        m = FLOW_LINE.match(str(d.get("action") or ""))
        t = _when(d.get("at"))
        if not m or not t or (flow and m.group(1) != flow):
            continue
        state, sub = m.group(2), (m.group(3) or "").strip()
        if state == "mapping" and sub == "pick":
            if open_at is not None:
                spans.append((open_at, t))
                open_at = None
            pick_at = pick_at or t
        elif state == "mapping":
            if open_at is None:
                open_at = t
        elif open_at is not None:
            spans.append((open_at, t))
            open_at = None
    if open_at is not None:
        spans.append((open_at, None))
    return spans, pick_at


def seen_log(reg):
    """Where the page logs the RUN.md changes it noticed: beside the register, never in it, so drawing the page
    writes nothing into the register (its tables' times are read as "written since the go")."""
    reg = pathlib.Path(reg)
    return reg.parent / ".step-changes" / f"{reg.name}.jsonl"


def seen_changes(reg, rows, flow, now):
    """Log each RUN.md row whose status differs from the last one logged for it (a `seen` line, by the listener),
    under the case record's lock; return {row lead: [(status, at, seen)]}, oldest first. The first sight of a row is
    a baseline: its time is never a step's time."""
    reg = pathlib.Path(reg)
    log = seen_log(reg)

    def history():
        got = {}
        both = _lines(reg / CASE_LOG) + _lines(log)  # two files, so put their lines back in time order
        both.sort(key=lambda d: _when(d.get("at")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
        for d in both:
            if d.get("action") != "step" or (flow and d.get("flow") not in (None, flow)):
                continue
            got.setdefault(d.get("row"), []).append((d.get("to"), _when(d.get("at")), bool(d.get("seen")),
                                                     bool(d.get("baseline"))))
        return got

    have = history()
    todo = [(lead, status) for lead, status, *_ in rows if (have.get(lead) or [(None,)])[-1][0] != status]
    if todo and (reg / "RUN.md").is_file():
        try:
            import case
            log.parent.mkdir(parents=True, exist_ok=True)
            with case._Busy(log.parent):
                have = history()  # read again inside the lock: another draw may have logged it already
                with open(log, "a", encoding="utf-8") as fh:
                    for lead, status in todo:
                        prior = have.get(lead)
                        if prior and prior[-1][0] == status:
                            continue
                        entry = {"at": now.astimezone(dt.timezone.utc).isoformat(timespec="seconds"),
                                 "session": None, "action": "step", "flow": flow, "row": lead,
                                 "from": prior[-1][0] if prior else None, "to": status, "seen": True,
                                 "by": "listener"}
                        if not prior:
                            entry["baseline"] = True
                        fh.write(json.dumps(entry) + "\n")
                have = history()
        except Exception:  # noqa: BLE001  (a time is never worth stopping the page for)
            pass
    return {k: [(to, at, seen) for to, at, seen, base in v if not base] for k, v in have.items()}


def _clock(t, tz):
    return t.astimezone(tz).strftime("%H:%M")


def _mins(a, b):
    return max(0, int(round((b - a).total_seconds() / 60)))


def span_text(start, end, now, about=False):
    tz = now.tzinfo
    pre, post = ("about ", " (noticed)") if about else ("", "")
    if start and end:
        return f"{pre}{_clock(start, tz)}-{_clock(end, tz)}{post} · {_mins(start, end)} min"
    if start:
        return f"{pre}since {_clock(start, tz)}{post} · {_mins(start, now)} min so far"
    if end:
        return f"{pre}done by {_clock(end, tz)}{post} · start not recorded"
    return "time not recorded"


def spans_text(spans, now):
    total = sum(_mins(a, b or now) for a, b in spans)
    first, last = spans[0][0], spans[-1][1]
    tz = now.tzinfo
    if last is None:
        return f"since {_clock(spans[-1][0], tz)} · {total} min so far"
    return f"{_clock(first, tz)}-{_clock(last, tz)} · {total} min" + (
        f" ({len(spans)} spans, the wait at the pick left out)" if len(spans) > 1 else "")


def row_span(changes, leads):
    """(start, end, about) of a step from its rows' changes: the first move to doing, the last move to done."""
    start = end = None
    about = False
    for lead in leads:
        for to, at, seen in changes.get(lead) or []:
            if at is None:
                continue
            if to == "doing" and (start is None or at < start):
                start, about = at, about or seen
            if to == "done" and (end is None or at > end):
                end, about = at, about or seen
    return start, end, about
