"""Who wrote each table of a split run's reading units, from Claude Code's own transcripts (split-run-formats.md, "Who
wrote a unit's tables").

Usage: python provenance.py <register folder> <unit> [--transcripts DIR]     exit 0 only when every cell is accounted

Writers. Every session that wrote into `units/<unit>/` with Write, Edit or MultiEdit, judged by the tool's resolved
`file_path` (a shell command's text is never read), must be a `bfo-unit-reader` subagent (READER_TYPE: the kit's
agent definition with no shell among its tools): its transcript `<main>/subagents/agent-<id>.jsonl` has beside it
`agent-<id>.meta.json` reading `"agentType":"bfo-unit-reader"`. A main session (the lead's own Write, say), a
`general-purpose` subagent (it carries the shell) or a fork fails the unit; no meta file, or one with no `agentType`, fails it with
"no agent type recorded (Claude Code older than the meta files?)". A writer is one of two kinds:
- the unit's reader or a fixer of it: it wrote under `units/<unit>/` and nowhere else. Its Reads are the unit's reading
  (reading_check.py --unit);
- the re-read of an unmatched call (merge.py): it wrote `units/<a>/calls.csv` and `units/<b>/operations.csv` of one
  other unit and nothing else, changed at most one row of the calls file, and added at most one row to the operations
  file, changing none there. It is credited for provenance and never as either unit's reader. A session that wrote
  only `units/<a>/calls.csv` is the first kind, unless all it changed there is `disputed: ` put at the start of a
  call's claim cell: that is the re-read on the calling side alone, and never a reader either (fixers never write
  the label; `collect` does). A session launched on a re-read's prompt (`readers.py prompt --mode reread`, its first
  message pointing at `prompts/<unit>/reread-<row_id>.md`) is a re-read whatever it wrote within those two files.
Any other set of writes fails every unit it wrote into.
A reader, fixer or re-read whose transcript shows a shell (Bash or PowerShell, whatever it ran) is left out,
and so is one not launched on a prompt a kit script wrote (judges.kit_prompt_problem: its first message must be the
pointer line of a file under prompts/ that readers.py or judges.py wrote, unchanged since): a
writer the lead dictated, inline or in a prompt file it wrote by hand. Its writes are not replayed and its Reads credit
nothing. While anything on disk is unaccounted for, it is named as a problem, with why, and with the relaunch
(`readers.py prompt <reg> <unit> --again`, which calls `undo_breaches`); once a relaunched clean agent's writes account
for every cell, it is only named in a note.

The flow worked now. When a flow of the register is finished (`earlier-flows/<id>/judged/`), only sessions whose first
timestamped transcript line is after the go of the flow worked now (`scope.json` `given`) count, and the replay starts
from the judged snapshot of the latest finished flow (`started_from`, else the latest written). A `given` that is not a
date and time fails every unit, and so does one not later than the go of the finished flow the replay starts from (its
record under `other_flows`, which must hold that go as a date and time): a go backdated with `go.py --given` never lets
a finished flow's sessions count. A finished flow taken up again (go.py take_up_again records `taken_up`) counts only
sessions after the later of its go and that time. No `given` recorded fails every unit too. A finished flow's
pass is its judged snapshot, never re-checked from transcripts that may be gone.

The replay. Each table of the unit but `files.csv` (written whole by each flow's reader, never judged nor a source of
rows) is replayed: from the snapshot, else empty, every successful Write, Edit and MultiEdit of the flow's sessions on
that file, in transcript timestamp order (a write with no timestamp fails the unit: it cannot be ordered); text with the
byte order mark stripped and line endings normalised. An Edit whose old text is not in the file as replayed, nor in it
written out again as Python's csv module writes it, is tried once more on the replayed rows with the unit's recorded
corrections applied (go.py --apply-correction rewrites the file outside any transcript); found there, the replay goes on
from that version, each corrected cell keeping the session that set it before, never credited to the Edit's. Found in
neither, it stops the replay: the file is unaccounted from there, and the session is named. The replayed rows, keyed by
`row_id`, must equal the file on disk, cell by cell, but for:
- a unit correction recorded in corrections-applied.csv (unit, table, row_id): a cell changed, the row removed, or
  a row the person added (go.py --added, which writes it and records their words, refused unless the person typed
  them into a session after the go; a unit cell or removal takes their words the same way), which passes only while it holds
  the content its record holds, later recorded corrections to it applied (a later Edit of it replays as any Edit
  does), and is credited to the person's recorded words. A recorded addition with no words fails: no typed reader or
  fixer wrote the row, and nobody stands behind it. A row added by correction is a row of the flow worked now
  (`current_rows`): judged, and its unit owed the reading check, as any row of that flow is. A unit whose every row
  is accounted for only so fails: no reader of it wrote any of it;
- `collect`'s `disputed: ` label at the start of a row's claim cell (judges.py), when the row's verdicts make it
  disputed. On a finished call the re-read's own label is replayed like any write; the unit freeze's allowance for
  it is go.py's.
Any other cell, whatever wrote it (a shell, a script, another tool), fails the unit, its row and column named. Each cell
keeps the session that last set it (`setter`), so merge.py's re-read check asks who put a `disputed: ` label in place.
"""
import csv
import datetime
import io
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import go  # noqa: E402
import judges  # noqa: E402
import paths  # noqa: E402
import register_layout as layout  # noqa: E402

AGENT_TYPE = "general-purpose"  # a launcher's agent type, and the judges' before the kit's judge agent (judges.py)
# The judges' agent type: the kit's agents/bfo-row-judge.md, whose `tools` list holds no shell, so a judge that cannot
# find a cited file cannot search for it with one and have its verdict thrown away. A register judged before
# it keeps its `general-purpose` judges, held to the same no-shell check.
JUDGE_TYPE = "bfo-row-judge"
JUDGE_TYPES = (JUDGE_TYPE, AGENT_TYPE)
# The type of every agent that writes a unit's tables (a reader, a fixer, a re-read; the unit `flow`'s fixers too):
# the kit's agents/bfo-unit-reader.md, whose `tools` list holds no shell, so such an agent cannot run one at all
# rather than being found to have run one after it finished. Launched by that name (readers.py's launchers).
READER_TYPE = "bfo-unit-reader"
SOURCE_READER_TYPE = "bfo-source-reader"  # the first look's reader of one source that is not code (first_look.py)
NO_TYPE = "no agent type recorded (Claude Code older than the meta files?)"
SNAPSHOT = "the finished flow's judged snapshot"  # the setter of a cell the replay starts with
CORRECTION = "a recorded correction"  # the setter of a cell a recorded correction set
PERSON = "the person, in their recorded words:"  # the setter of a row they added (go.py --added --words)
EDITS = ("Edit", "MultiEdit")

_cache = {}


def forget():
    """Drop the transcripts read so far (each is read again only when it changed on disk)."""
    _cache.clear()


def _session(f):
    st = f.stat()
    key = (str(f), st.st_mtime_ns, st.st_size)
    if key not in _cache:
        _cache[key] = judges.Session(f)
    return _cache[key]


def agent_type(path, want=AGENT_TYPE):
    """(the agent type of the session whose transcript is `path`, None) or (None, why it is not `want`, a type or a
    tuple of types): read from the meta file Claude Code writes beside a subagent's transcript. Fails closed: any other
    type fails."""
    p = pathlib.Path(path)
    if p.parent.name != "subagents":
        return None, "a main session, not a subagent (the lead's own session, say)"
    meta = p.with_name(p.name[:-len(".jsonl")] + ".meta.json") if p.name.endswith(".jsonl") else None
    try:
        got = json.loads(meta.read_text(encoding="utf-8")) if meta else None
    except (OSError, ValueError):
        got = None
    t = got.get("agentType") if isinstance(got, dict) else None
    if not t:
        return None, NO_TYPE
    wanted = (want,) if isinstance(want, str) else tuple(want)
    if t not in wanted:
        why = f"an agent of type {t!r}, not " + " or ".join(repr(w) for w in wanted)
        return t, why + (": a fork has seen the lead's reasoning" if t == "fork" else "")
    return t, None


def _when(text):
    """An aware datetime from a transcript timestamp or a go's `given`, or None."""
    try:
        d = datetime.datetime.fromisoformat(str(text).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.astimezone()


def snapshot_dir(reg):
    """earlier-flows/<id>/judged/ of the latest finished flow, or None when no flow is finished."""
    reg = pathlib.Path(reg)
    s = go.load(reg) or {}
    named = reg / go.EARLIER / str(s.get("started_from") or "") / go.JUDGED
    if s.get("started_from") and named.is_dir():
        return named
    got = [d for d in (reg / go.EARLIER).glob(f"*/{go.JUDGED}") if d.is_dir()] if (reg / go.EARLIER).is_dir() else []
    return max(got, key=lambda d: d.stat().st_mtime) if got else None


def flow_sessions(reg, transcripts=None):
    """([judges.Session] of the flow worked now, [problems]). Every transcript in the folders, read once."""
    reg = pathlib.Path(reg).resolve()
    folders = judges._folders(reg, transcripts)
    every = [_session(f) for folder in folders for f in sorted(folder.rglob("*.jsonl"))]
    problems, start = [], None
    snap = snapshot_dir(reg)
    if snap is not None:
        now = go.load(reg) or {}
        given = (now.get("given") or "").strip()
        start = _when(given) if given else None
        again = str(now.get("taken_up") or "").strip()  # a finished flow taken up again (go.py take_up_again)
        if not given:
            problems.append("no go recorded for the flow worked now (scope.json `given`) while a finished flow is "
                            "kept: the sessions of this flow cannot be told from a finished flow's")
        elif start is None:
            problems.append(f"the go of the flow worked now was given {given!r} (scope.json), not a date and time: "
                            "the sessions of this flow cannot be told from a finished flow's")
        elif again and _when(again) is None:
            problems.append(f"the flow worked now was taken up again at {again!r} (scope.json), not a date and time: "
                            "the sessions of this flow cannot be told from a finished flow's")
        elif start is not None:
            if again and _when(again) > start:
                given, start = again, _when(again)
            problems += _after_the_finished_go(reg, snap.parent.name, given, start)
        if problems:
            every, start = [], None
    if start is not None:
        every = [s for s in every if (_when(s.first) or start) > start]
    return every, problems


def _after_the_finished_go(reg, fid, given, start):
    """[the problem] when the go of the flow worked now (`given`, at `start`) is not later than the go of the finished
    flow `fid` whose snapshot the replay starts from, or that go is not recorded as a date and time: a go backdated
    with `go.py --given` would let the finished flow's sessions count for this one."""
    def ident(s):
        return go.flow_id_of(reg, s) or re.sub(r"[^A-Za-z0-9]+", "-", s.get("flow", "flow")).strip("-")
    others = (go.read_raw(reg) or {}).get(go.OTHER_FLOWS) or {}
    rec = next((s for s in others.values() if isinstance(s, dict) and ident(s) == fid), None)
    was = str((rec or {}).get("given") or "").strip()
    then = _when(was) if was else None
    if then is None:
        return [f"the go of the finished flow {fid} is " + (f"recorded as {was!r}, not a date and time" if was else
                                                           "not recorded (scope.json other_flows)")
                + ": the sessions of the flow worked now cannot be told from that flow's"]
    if start <= then:
        return [f"the go of the flow worked now was given {given!r} (scope.json), not later than the go of the "
                f"finished flow {fid} ({was!r}): that flow's sessions would count for this one"]
    return []


def _plain(text):
    return str(text).lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def _parse(text):
    """(header, {row key: {column: cell}}, [keys used twice]): keyed by `row_id` (else the first column)."""
    data = [r for r in csv.reader(io.StringIO(_plain(text))) if any(c.strip() for c in r)]
    if not data:
        return [], {}, []
    header, out, twice = data[0], {}, []
    col = header.index("row_id") if "row_id" in header else 0
    for cells in data[1:]:
        cells = cells + [""] * (len(header) - len(cells))
        key = cells[col].strip()
        if key in out:
            twice.append(key)
        out[key] = dict(zip(header, cells))
    return header, out, twice


def _canonical(text):
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(r for r in csv.reader(io.StringIO(_plain(text))))
    return out.getvalue()


def _edit(text, old, new, every=False):
    """The text with the Edit applied, or None when its old text is not there."""
    old, new = _plain(old), _plain(new)
    for t in (text, _canonical(text)):
        if old and old in t:
            return t.replace(old, new) if every else t.replace(old, new, 1)
    return None


class Table:
    """One unit table replayed: its rows, who last set each cell, and what each session changed."""

    def __init__(self, name, base_text, fixes=()):
        self.name = name
        self.fixes = list(fixes)  # the unit corrections recorded to this table (go.applied_corrections)
        self.text = _plain(base_text)
        self.header, self.rows, _ = _parse(self.text)
        self.setters = {k: {c: SNAPSHOT for c in r} for k, r in self.rows.items()}
        self.changed = {}  # session: {"changed": set of keys, "added": set, "removed": set}
        self.cells = {}  # session: {(key, column): (before, after)}, the first before and the last after
        self.diverged = None  # the session whose Edit could not be replayed

    @staticmethod
    def _edits(text, name, inp):
        for e in ([inp] if name == "Edit" else inp.get("edits") or []):
            text = _edit(text, e.get("old_string") or "", e.get("new_string") or "", bool(e.get("replace_all")))
            if text is None:
                return None
        return text

    def _corrected(self):
        """(text, rows) of the table as replayed with every recorded correction applied, as go.py's
        --apply-correction writes the file, or None when they change nothing."""
        if not self.fixes or not self.header:
            return None
        rows = {k: go.corrected(self.name, r, self.fixes, key=k) for k, r in self.rows.items()
                if not go.removed(self.fixes, k)}
        for k in dict.fromkeys(f.get("row") for f in self.fixes):
            got = _added(self.name, self.fixes, k)
            if got is not None and k not in rows:
                rows[k] = {c: got.get(c, "") for c in self.header}
        if rows == self.rows:
            return None
        out = io.StringIO()
        w = csv.writer(out, lineterminator="\n")
        w.writerow(self.header)
        w.writerows([r.get(c, "") for c in self.header] for r in rows.values())
        return out.getvalue(), rows

    def apply(self, sess, name, inp):
        if self.diverged is not None:
            return
        if name == "Write":
            text = _plain(inp.get("content") or "")
        else:
            text = self._edits(self.text, name, inp)
            fixed = self._corrected() if text is None else None
            if fixed is not None:  # anchored on what a recorded correction wrote: replay it on the corrected table
                text = self._edits(fixed[0], name, inp)
                if text is not None:  # the corrected cells keep their setters: never credited to this session
                    self.text, self.rows = fixed[0], fixed[1]
                    self.setters = {k: self.setters.get(k) or {c: CORRECTION for c in r} for k, r in self.rows.items()}
            if text is None:
                self.diverged = sess
                return
        header, rows, _ = _parse(text)
        mine = self.changed.setdefault(sess, {"changed": set(), "added": set(), "removed": set()})
        cells = self.cells.setdefault(sess, {})
        for k, r in rows.items():
            before = self.rows.get(k)
            if before is None:
                mine["added"].add(k)
                self.setters[k] = {c: sess for c in r}
                continue
            for c, v in r.items():
                if before.get(c) != v:
                    mine["changed"].add(k)
                    self.setters.setdefault(k, {})[c] = sess
                    cells[(k, c)] = (cells.get((k, c), (before.get(c),))[0], v)
        for k in set(self.rows) - set(rows):
            mine["removed"].add(k)
            self.setters.pop(k, None)
        self.text, self.header, self.rows = text, header, rows


class Unit:
    """The provenance of one unit's tables: `problems` (empty when every cell is accounted for), `readers` (the sessions
    credited with the unit's reading), `rereads`, and each table's replay (`setter`, `cell`)."""

    def __init__(self, unit):
        self.unit = unit
        self.problems, self.readers, self.rereads = [], [], []
        self.breached = []  # readers or fixers that ran a shell, or were launched on a prompt no kit script wrote:
        # their writes and Reads are not counted
        self.why_breached = {}  # session name: why it is not counted
        self.notes = []
        self.tables = {}

    def setter(self, table, key, col):
        t = self.tables.get(table)
        return None if t is None or t.diverged is not None else t.setters.get(key, {}).get(col)

    def cell(self, table, key, col):
        t = self.tables.get(table)
        return None if t is None else (t.rows.get(key) or {}).get(col)


def _name(sess):
    return pathlib.Path(sess.path).stem


def _launched_as_re_read(sess):
    """The session's first message points at a re-read's prompt, <reg>/prompts/<unit>/reread-<row_id>.md."""
    return bool(re.search(r"/prompts/[^/]+/reread-[^/]+\.md and do exactly", getattr(sess, "prompt", None) or ""))


def _is_re_read_kind(sess, reg, unit):
    return _kind(sess, reg, unit)[0] == "re-read"


def _kind(sess, reg, unit):
    """("reader", None), ("re-read", None) or ("breach", why) for a session that wrote into units/<unit>/. A session
    launched on a re-read's prompt (readers.py --mode reread) is a re-read whatever it wrote within its two files;
    any other is told by what it wrote."""
    units = paths.norm(pathlib.Path(reg) / layout.UNITS) + "/"
    mine = paths.norm(layout.unit_dir(reg, unit)) + "/"
    written = {p for _, p in sess.writes}
    if _launched_as_re_read(sess) and all(p.startswith(units) and p.endswith(("/calls.csv", "/operations.csv"))
                                          and p[len(units):].count("/") == 1 for p in written) and len(written) <= 2:
        return "re-read", None
    if all(p.startswith(mine) for p in written):
        return "reader", None
    in_units = {p for p in written if p.startswith(units)}
    folders = {p[len(units):].split("/")[0] for p in in_units}
    calls = [p for p in in_units if p.endswith("/calls.csv")]
    ops = [p for p in in_units if p.endswith("/operations.csv")]
    if (in_units == written and len(in_units) == 2 and len(folders) == 2 and len(calls) == 1 and len(ops) == 1
            and calls[0][len(units):].count("/") == 1 and ops[0][len(units):].count("/") == 1
            and calls[0].rsplit("/", 2)[-2] != ops[0].rsplit("/", 2)[-2]):
        return "re-read", None
    elsewhere = sorted(p for p in written if not p.startswith(mine))
    return "breach", (f"{_name(sess)} wrote into more than its own unit's folder units/{unit}/: "
                      + ", ".join(elsewhere[:3]) + (" ..." if len(elsewhere) > 3 else ""))


def unit(reg, unit_id, transcripts=None):
    """The provenance of units/<unit_id>/ (the module's docstring says what accounts for a cell)."""
    reg = pathlib.Path(reg).resolve()
    sessions, flow_problems = flow_sessions(reg, transcripts)
    out = Unit(unit_id)
    out.problems += flow_problems
    udir = layout.unit_dir(reg, unit_id)
    mine = paths.norm(udir) + "/"
    writers = [s for s in sessions if any(p.startswith(mine) for _, p in s.writes)]
    for s in writers:
        _, why = agent_type(s.path, READER_TYPE)
        if why:
            out.problems.append(f"{_name(s)} wrote into units/{unit_id}/ and is {why}")
        kind, why = _kind(s, reg, unit_id)
        unprompted = judges.kit_prompt_problem(s, reg) if kind != "breach" else None
        if kind == "breach":
            out.problems.append(why)
        elif s.shell:  # a reader, fixer or re-read that ran a shell: relaunched, never counted
            out.breached.append(s)
            out.why_breached[_name(s)] = "ran a shell"
        elif unprompted:  # launched on a prompt the lead wrote: dictated, never counted
            out.breached.append(s)
            out.why_breached[_name(s)] = unprompted[len(_name(s)) + 1:]
        elif kind == "re-read":
            out.rereads.append(s)
        else:
            out.readers.append(s)
    writers = [s for s in writers if s not in out.breached]
    snap = snapshot_dir(reg)
    on_disk = sorted(p for p in udir.glob("*.csv") if p.name.lower() != layout.FILES_CSV) if udir.is_dir() else []
    names = {p.stem for p in on_disk}
    if snap is not None and (snap / layout.UNITS / unit_id).is_dir():
        names |= {p.stem for p in (snap / layout.UNITS / unit_id).glob("*.csv")}
    events = sorted(((judges_when(w), _name(s), i, s, name, p, inp) for s in writers
                     for i, (name, p, inp, w) in enumerate(s.ops) if p.startswith(mine)),
                    key=lambda e: e[:3])
    untimed = sorted({e[1] for e in events if not e[0][0]})
    if untimed:  # it would sort before every timed write, whenever it was made
        out.problems += [f"{n} wrote into units/{unit_id}/ with no timestamp in its transcript: its writes cannot be "
                         "put in order with the others" for n in untimed]
    disputed, rows_on_disk, rows_added = None, 0, 0
    for table in sorted(names):
        base = snap / layout.UNITS / unit_id / f"{table}.csv" if snap is not None else None
        fixes = go.applied_corrections(reg, table, unit_id)
        t = Table(table, base.read_text(encoding="utf-8-sig") if base is not None and base.is_file() else "", fixes)
        target = paths.norm(udir / f"{table}.csv")
        for _, _, _, s, name, p, inp in events:
            if p == target and (name == "Write" or name in EDITS):
                t.apply(s, name, inp)
        out.tables[table] = t
        if t.diverged is not None:
            out.problems.append(f"units/{unit_id}/{table}.csv: an Edit by {_name(t.diverged)} could not be replayed "
                                "(its old text is not in the file as its sessions wrote it): the file is not accounted "
                                "for from there")
            continue
        disk_p = udir / f"{table}.csv"
        header, disk, twice = _parse(disk_p.read_text(encoding="utf-8-sig")) if disk_p.is_file() else ([], {}, [])
        out.problems += [f"units/{unit_id}/{table}.csv: row_id {k} used twice" for k in sorted(set(twice))]
        claim = next((h for h in judges.CLAIMS if h in header), header[1] if len(header) > 1 else None)
        for k, d in disk.items():
            rows_on_disk += 1
            r = t.rows.get(k)
            if r is None and not go.removed(fixes, k):  # added by the person's correction: accepted as recorded
                r = go.added_row(fixes, k)
                said = go.added_words(fixes, k) if r is not None else ""
                if r is not None and not said:  # no typed writer, and nobody's words behind it
                    out.problems.append(f"units/{unit_id}/{table}.csv row {k}: added by a correction recorded with no "
                                        "words from the person, and no typed reader or fixer wrote it")
                    continue
                if r is not None:
                    rows_added += 1
                    t.setters.setdefault(k, {c: f"{PERSON} \"{said}\"" for c in r})
            if r is None:
                out.problems.append(f"units/{unit_id}/{table}.csv row {k}: no session's write accounts for it")
                continue
            r = go.corrected(table, r, fixes, key=k)
            bad = []
            for c in sorted(set(d) | set(r)):
                v, w = d.get(c) or "", r.get(c) or ""
                if v == w:
                    continue
                if c == claim and v == judges.DISPUTED + w:
                    if disputed is None:
                        disputed = judges.disputed_rows(reg, unit_id)
                    if (table, k) in disputed:
                        continue
                bad.append(c)
            if bad:
                out.problems.append(f"units/{unit_id}/{table}.csv row {k}: {', '.join(bad)} not as any session of "
                                    "this flow wrote it, nor a recorded correction")
        for k in sorted(set(t.rows) - set(disk)):
            if not go.removed(fixes, k):
                out.problems.append(f"units/{unit_id}/{table}.csv row {k}: written, and gone from the file with no "
                                    "recorded removal")
    if rows_on_disk and rows_added == rows_on_disk:
        out.problems.append(f"units/{unit_id}/: every row is added by correction (go.py --added) and none written by "
                            "a reader of the unit: a unit is read by its own reader, never built from corrections")
    calls = out.tables.get("calls")
    for s in list(out.readers):  # a session whose one write is a `disputed: ` label on a call is a re-read
        if _labels_only(s, calls, paths.norm(udir / "calls.csv")):
            out.readers.remove(s)
            out.rereads.append(s)
    for s in out.rereads:  # a re-read changes one call row and adds at most one operation, changing none
        for table, t in out.tables.items():
            got = t.changed.get(s)
            if not got:
                continue
            if table == "calls" and len(got["changed"] | got["added"] | got["removed"]) > 1:
                out.problems.append(f"{_name(s)}, a re-read of an unmatched call, changed more than one row of "
                                    f"units/{unit_id}/calls.csv")
            if table == "operations" and (got["changed"] or got["removed"] or len(got["added"]) > 1):
                out.problems.append(f"{_name(s)}, a re-read of an unmatched call, may add one row to "
                                    f"units/{unit_id}/operations.csv and change none")
    for s in out.breached:  # it fails the unit while anything it may have written is on disk; after a relaunch,
        # the clean agent's writes account for every cell, and it is only named
        why = out.why_breached.get(_name(s), "ran a shell")
        if out.problems:
            out.problems.append(f"{_name(s)} {why}: its writes are not counted and its reading credits nothing; "
                                f"relaunch it: readers.py prompt <reg> {unit_id} --mode "
                                f"{'reread' if _is_re_read_kind(s, reg, unit_id) else 'read|fix'} --again")
        else:
            out.notes.append(f"{_name(s)} {why}, and was relaunched: superseded, its writes not counted")
    return out


def undo_breaches(reg, unit_id, transcripts=None):
    """Put back each table of units/<unit_id>/ that a reader or fixer which ran a shell wrote, as the unit's clean
    writers left it (replayed from the finished flow's judged snapshot, else empty, recorded corrections applied and
    recorded removals left out): a table nothing clean wrote is removed, and so is files.csv, which each flow's reader
    writes whole. Returns the names of the sessions undone. Refused when a table's replay stops (an Edit that cannot
    be replayed): it names the table and changes nothing."""
    reg = pathlib.Path(reg).resolve()
    forget()
    u = unit(reg, unit_id, transcripts)
    if not u.breached:
        return []
    udir = layout.unit_dir(reg, unit_id)
    mine = paths.norm(udir) + "/"
    hit = {p[len(mine):] for s in u.breached for _, p in s.writes if p.startswith(mine)}
    tables_ = sorted(n[:-len(".csv")] for n in hit if n.endswith(".csv") and "/" not in n)
    stuck = [t for t in tables_ if t in u.tables and u.tables[t].diverged is not None]
    if stuck:
        raise SystemExit(f"units/{unit_id}/: the clean writes of {', '.join(stuck)} cannot be replayed; nothing undone")
    for table in tables_:
        p = udir / f"{table}.csv"
        t = u.tables.get(table)
        if table == layout.FILES_CSV[:-len(".csv")] or t is None or not t.header:
            p.unlink(missing_ok=True)
            continue
        fixes = go.applied_corrections(reg, table, unit_id)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(t.header)
        for k, r in t.rows.items():
            if not go.removed(fixes, k):
                r = go.corrected(table, r, fixes, key=k)
                w.writerow([r.get(c, "") for c in t.header])
        p.write_text(buf.getvalue(), encoding="utf-8", newline="")
    forget()
    return [_name(s) for s in u.breached]


def _labels_only(sess, calls, target):
    """Session `sess` wrote nothing under units/ but this unit's calls.csv, and its whole change there is
    `disputed: ` put at the start of call claim cells: a re-read of an unmatched call on its calling side, never a
    reader (fixers never write the label: `collect` does)."""
    if calls is None or calls.diverged is not None or {p for _, p in sess.writes} != {target}:
        return False
    got = calls.changed.get(sess) or {}
    cells = calls.cells.get(sess) or {}
    claim = next((h for h in judges.CLAIMS if h in calls.header), None)
    return (bool(cells) and not got.get("added") and not got.get("removed")
            and all(c == claim and after == judges.DISPUTED + (before or "") for (_, c), (before, after) in cells.items()))


def current_rows(reg, unit_id):
    """[(table, row_id)] of the unit's rows of the flow worked now: every row but those the latest finished flow's
    judged snapshot holds as they are now, `disputed: ` labels set aside. The snapshot is the rows as that flow
    finished, its corrections in them; a row added or changed by a correction recorded since is of the flow worked
    now, and judged again."""
    reg = pathlib.Path(reg).resolve()
    udir, snap = layout.unit_dir(reg, unit_id), snapshot_dir(reg)
    out = []
    for p in sorted(udir.glob("*.csv")) if udir.is_dir() else []:
        if p.name.lower() == layout.FILES_CSV:
            continue
        _, now, _ = _parse(p.read_text(encoding="utf-8-sig"))
        kept = snap / layout.UNITS / unit_id / p.name if snap is not None else None
        _, old, _ = _parse(kept.read_text(encoding="utf-8-sig")) if kept is not None and kept.is_file() else ([], {}, [])
        for k, r in now.items():
            was = old.get(k)
            if was is None or _bare(was) != _bare(r):
                out.append((p.stem, k))
    return out


def _added(table, fixes, key):
    """The unit row `key` as its addition by correction recorded it, later recorded corrections applied, or None (no
    addition recorded, or the row's removal recorded since)."""
    got = None if go.removed(fixes, key) else go.added_row(fixes, key)
    return None if got is None else go.corrected(table, got, fixes, key=key)


def _bare(row):
    return {c: judges._strip(v or "") for c, v in row.items()}


def judges_when(when):
    """A sortable time for a write: (its timestamp as an aware datetime's ISO text, or '' when none), its order."""
    ts, order = when
    d = _when(ts) if ts else None
    return (d.astimezone(datetime.timezone.utc).isoformat() if d else "", order)


def main(argv):
    argv = list(argv)
    transcripts = None
    if "--transcripts" in argv:
        i = argv.index("--transcripts")
        transcripts = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    if len(argv) != 2 or transcripts is None and "--transcripts" in sys.argv:
        print(__doc__)
        return 2
    u = unit(argv[0], argv[1], transcripts)
    print(f"Unit {u.unit}: " + ("every cell accounted for" if not u.problems else
                                f"NOT ACCOUNTED: {len(u.problems)} problem(s)"))
    for p in u.problems:
        print("  " + p)
    return 0 if not u.problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
