"""Draw a sample of register rows to be re-read against their code, and say whether the re-read was done.

Usage: python reread.py <register folder> [how many, default 10]      draws the flow worked now's sample
       python reread.py <register folder> --flow <flow id> [how many]  draws an earlier flow's sample again, into its
                                                                      own file, while a later flow is worked
       python reread.py --check <register folder>                     says whether it was done, flow by flow

The sample is audit sampling: rows are drawn from every table that cites code, calls between parts that rest only on
the run's reading (`proposed:`) first, since no cited line states them: they rest on the reading alone. An agent that wrote
none of the rows opens each row's cited lines with the Read tool and writes its verdict in re-read.csv: `says` (the
code does what the row claims), `does not say`, or `unclear`, with the reason. The check passes only when every row
says, the verdicts were written by a session that wrote no other table of the register, and that session opened every
cited line. All three are read from Claude Code's own record of the sessions (reading_check.py finds it). A row that
does not say is fixed where it was written, and the sample is drawn again."""
import csv
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reading_check as rc  # noqa: E402
import paths  # noqa: E402
import tables  # noqa: E402

NOT_ROWS = {"sources", "how-made", "survey", "set-aside", "re-read", "re-read-history", "about"}
FIELDS = ["table", "row", "claim", "citations", "verdict", "reason"]
VERDICTS = {"says", "does not say", "unclear"}


def claim_of(r):
    """A row's whole claim, every cell of it: the re-reader judges all of it."""
    return " ".join(v for v in r.values() if isinstance(v, str))


def key_of(table, r):
    import go
    return go.row_key(table, r)


def taken_before(reg, s):
    """{(table, row)}: the rows the map already held when the flow `s` began (the copy kept then), which are an
    earlier flow's, never this one's; empty for the first flow."""
    import go
    reg = pathlib.Path(reg)
    kept = reg / go.EARLIER
    if not kept.is_dir() or not s:
        return set()
    fid = go.flow_id_of(reg, s)
    names = [s["started_from"]] if s.get("started_from") else [p.name for p in kept.iterdir() if p.is_dir()
                                                               and p.name != fid]
    out = set()
    for name in names:
        for snap in (kept / name).glob("*.csv"):
            with snap.open(encoding="utf-8-sig", newline="") as f:
                out |= {(snap.stem, key_of(snap.stem, r)) for r in csv.DictReader(f)}
    return out


def flow_of_rows(reg, fid):
    """Whether a row of a table is the flow `fid`'s: it names the flow, one of its stages, process steps or moves, or
    it is a part (or a call between parts) that takes part in one of its steps. A row naming none of these (the
    capability's, a remedy no failure of the flow names) is no flow's own."""
    reg = pathlib.Path(reg)

    def rows(t):
        return tables.dicts(reg / f"{t}.csv") if (reg / f"{t}.csv").is_file() else []

    def ids(text):
        return {x.strip() for x in re.split(r"[;,\s]+", text or "") if x.strip()}
    S = {r["stage"] for r in rows("stages") if (r.get("flow") or "").strip() == fid}
    T = {r["step"] for r in rows("steps") if (r.get("stage") or "").strip() in S}
    L = {r["move_id"] for r in rows("lifecycle") if (r.get("flow") or "").strip() == fid}
    P = {r["subject_id"] for r in rows("participation") if (r.get("step") or "").strip() in T}
    FM = [r for r in rows("failure-modes") if ids(r.get("moves")) & L]
    RM = {x for r in FM for x in ids(r.get("remedy"))}
    own = {fid} | S | T | L | P

    def mine(table, r):
        for col in ("flow_id", "flow"):
            if (r.get(col) or "").strip():
                return r[col].strip() == fid
        if (r.get("stage") or "").strip():
            return r["stage"].strip() in S
        if (r.get("step") or "").strip():
            return r["step"].strip() in T
        if table == "lifecycle":
            return r.get("move_id") in L
        if table == "failure-modes":
            return bool(ids(r.get("moves")) & L)
        if table == "remedies":
            return r.get("remedy") in RM
        if table == "subjects":
            return r.get("subject_id") in P or bool(ids(r.get("step_hint")) & T)
        if table == "measure-gaps":
            return (r.get("element") or "").strip() in own
        if table == "agent-system":
            return bool(ids(r.get("serves_business_step")) & T) or r.get("agent") in P
        return (r.get("subject_id") or "").strip() in P
    return mine


def _when(text):
    """A recorded time (ISO 8601, as go.py writes it), or None when the text is not one; a time with no offset is
    read as local."""
    import datetime
    try:
        t = datetime.datetime.fromisoformat((text or "").strip())
    except ValueError:
        return None
    return t if t.tzinfo else t.astimezone()


def corrected_since_report(reg, s):
    """The corrections applied to a row of the flow `s` at or after its report was sent, from corrections-applied.csv:
    [(correction id, table, row key, the row as the map holds it now)]. Each owes the flow's report again; a row that
    cites code is also owed a re-read. Empty while the flow's report is not sent."""
    import go
    reg = pathlib.Path(reg)
    sent = _when((s or {}).get("report_sent"))
    applied = reg / go.APPLIED
    if sent is None or not applied.is_file():
        return []
    mine = flow_of_rows(reg, go.flow_id_of(reg, s))
    out = []
    for c in tables.dicts(applied):
        at = _when(c.get("applied_at"))
        table, key = (c.get("table") or "").strip(), (c.get("row") or "").strip()
        if (c.get("unit") or "").strip():  # a split run's unit row, judged rather than sampled
            continue
        if (c.get("correction_id") or "").startswith("merge-") and (c.get("source") or "").endswith("of a later flow"):
            continue  # a consumer's step_hint grown by a later flow's step: that flow's work, no change to this one
        if at is None or at < sent or not (reg / f"{table}.csv").is_file():
            continue
        r = next((x for x in tables.dicts(reg / f"{table}.csv") if key_of(table, x) == key), None)
        if r is not None and mine(table, r):
            out.append(((c.get("correction_id") or "").strip(), table, key, r))
    return out


def reopened(reg, s):
    """{(table, row key): correction id}: the rows a correction changed after the flow `s`'s report was sent that
    its sample can hold (they cite code, and are its own, not rows the map held when it began), which its sample must
    hold, re-read as they read now, before its re-read passes again."""
    import go
    got = corrected_since_report(reg, s)
    if not got:
        return {}
    can = {(r["table"], r["row"]) for r in candidates(reg, go.flow_id_of(reg, s))}
    return {(t, k): cid for cid, t, k, _ in got if (t, k) in can}


def current_flow(reg):
    import go
    s = go.load(reg)
    return go.flow_id_of(reg, s) if s else None


def sheet_of(reg):
    """The file the flow worked now draws its sample into: re-read.csv for the register's first flow, and
    re-read-<flow id>.csv for each further flow, from its first draw, so no sample is ever moved and the record of who
    wrote its verdicts stays with the file they were written in."""
    import go
    return sheet_for(reg, go.load(reg))


def flow_of_sheet(reg, sheet):
    """The id of the flow whose sample `sheet` is, or None."""
    import go
    reg = pathlib.Path(reg)
    return next((go.flow_id_of(reg, s) for s in go.load_all(reg) if sheet_for(reg, s).name == sheet.name), None)


def sheet_for(reg, s):
    """The sample file of the flow `s` records: re-read.csv for the register's first flow, re-read-<flow id>.csv for
    each further flow."""
    import go
    reg = pathlib.Path(reg)
    records = go.load_all(reg)
    if not s or len(records) <= 1:
        return reg / "re-read.csv"
    first = min(records, key=lambda x: x.get("given") or "")
    if first.get("flow") == s.get("flow"):
        return reg / "re-read.csv"
    return reg / f"re-read-{go.flow_id_of(reg, s) or 'flow'}.csv"


def candidates(reg, fid=None):
    """The rows a sample is drawn from: every row that cites code, of the flow `fid` only when it is given."""
    import go
    calls, rest = [], {}
    mine = flow_of_rows(reg, fid) if fid else None
    s = next((x for x in go.load_all(reg) if go.flow_id_of(reg, x) == fid), None) if fid else None
    before = taken_before(reg, s)
    for p in sorted(pathlib.Path(reg).glob("*.csv")):
        if p.stem in NOT_ROWS or p.stem.startswith("re-read"):
            continue
        with p.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if mine and not mine(p.stem, r):
                    continue
                text = " ".join(v for v in r.values() if isinstance(v, str))
                cited = rc.cited_in(text)
                if not cited:
                    continue
                key = key_of(p.stem, r)
                if (p.stem, key) in before:
                    continue  # the map held it when this flow began: an earlier flow's row
                row = {"table": p.stem, "row": key, "claim": claim_of(r),
                       "citations": "; ".join(c + (f":{a}" + (f"-{b}" if b != a else "") if a else "")
                                              for c, a, b in cited)}
                if r.get("from_id") and r.get("to_id") and "proposed" in text:
                    calls.append(row)
                else:
                    rest.setdefault(p.stem, []).append(row)
    queues = list(rest.values())
    order = list(calls)
    while any(queues):
        for q in queues:
            if q:
                order.append(q.pop(0))
    return order


def draw(reg, n=10, fid=None):
    """A fresh sample. A redraw keeps each row the last sample did not bear out, so it is checked again after its fix,
    and fills the rest with rows never drawn before; every earlier draw is kept in re-read-history.csv."""
    import go
    reg = pathlib.Path(reg)
    s = next((x for x in go.load_all(reg) if go.flow_id_of(reg, x) == fid), None) if fid else go.load(reg)
    if fid and s is None:
        raise ValueError(f"no flow {fid} is started in this register")
    sheet = sheet_for(reg, s)
    last = tables.dicts(sheet) if sheet.is_file() else []
    history = reg / "re-read-history.csv"
    if last:
        old = tables.dicts(history)
        tables.write(history, FIELDS, old + last, lineterminator="\r\n")
    seen = {(r["table"], r["row"]) for r in tables.dicts(history)}
    now = claims_now(reg)  # a row not borne out, or one changed since it said so, is drawn again, its verdict cleared
    again = {(r["table"], r["row"]) for r in last if (r.get("verdict") or "").strip().lower() != "says"
             or r.get("claim") not in now.get((r["table"], r["row"]), ())}
    again |= set(reopened(reg, s))  # a row corrected after the flow's report was sent is re-read, sampled or not
    pool = candidates(reg, fid or current_flow(reg))
    rows = [r for r in pool if (r["table"], r["row"]) in again]
    rows += [r for r in pool if (r["table"], r["row"]) not in seen][:max(0, n - len(rows))]
    tables.write(sheet, FIELDS, [dict(r, verdict="", reason="") for r in rows], lineterminator="\r\n")
    return rows


class Result:
    def __init__(self, problems, n, flows=()):
        self.problems, self.n, self.flows = problems, n, list(flows)
        self.passed = not problems

    def lines(self):
        each = [f"Re-read of {name}: " + (f"passed, {n} sampled row(s) borne out" if ok else "NOT DONE")
                for name, ok, n in self.flows]
        if self.passed:
            return [f"Re-read: {self.n} sampled row(s) re-read against their code by an agent that wrote none of "
                    "them, each one borne out: ok"] + each
        return ["Re-read: NOT DONE"] + each + [f"  {p}" for p in self.problems]


def _writes(uses, path):
    p = paths.norm(path)
    return any(name in ("Write", "Edit", "MultiEdit") and paths.norm(inp.get("file_path", "")) == p
               for name, inp in uses)


def sheets(reg):
    """The flow worked now's sample (re-read.csv, while there is one), then each earlier flow's (re-read-<flow>.csv)."""
    reg = pathlib.Path(reg)
    return [p for p in [reg / "re-read.csv"] if p.is_file()] + sorted(
        p for p in reg.glob("re-read-*.csv") if p.stem != "re-read-history")


def check(reg, transcripts=None):
    """Every flow's sample re-read and borne out: the flow worked now's and each earlier flow's, each by an agent
    that wrote none of the register's tables. The run is DONE only when all have passed."""
    reg = pathlib.Path(reg).resolve()
    if not candidates(reg):
        return Result([], 0)
    found = sheets(reg)
    problems = [] if (reg / "re-read.csv").is_file() or found else [
        "no re-read.csv: draw it with reread.py and have an agent that wrote none of the rows judge it"]
    n, flows = 0, []
    import go
    names = {sheet_for(reg, s).name: s.get("flow", "") for s in go.load_all(reg)}
    for sheet in found:
        got = check_sheet(reg, sheet, transcripts)
        n += got.n
        flows.append((names.get(sheet.name, sheet.name), got.passed, got.n))
        lead = "" if sheet.name == "re-read.csv" else f"{sheet.name}: "
        fid = flow_of_sheet(reg, sheet)
        redraw = f" (python reread.py <register> --flow {fid})" if fid else ""
        problems += [lead + p + (redraw if "changed since it was sampled" in p else "") for p in got.problems]
    return Result(problems, n, flows)


MOVED = {"measures": ("source_ref", "alerts", ("alert", "counted_moves"))}  # a migration's column move:
# (the column they followed, the table they moved to, the columns moved), so a row reads as it did before the move
ADDED = {"measures": ("for_flow",)}  # columns a migration added and filled: a row reads as it did before them too


def claims_now(reg):
    """{(table, row): {its claim as the map holds it now}}, for every row a sample could hold: as its columns are now,
    and, for a table whose columns a migration moved to another table, also as it read before the move, so a verdict
    given before a mechanical migration still counts and only a real edit makes it stale."""
    reg = pathlib.Path(reg)
    out = {}
    for p in sorted(reg.glob("*.csv")):
        if p.stem in NOT_ROWS or p.stem.startswith("re-read"):
            continue
        moved = MOVED.get(p.stem)
        away = {}
        if moved and (reg / f"{moved[1]}.csv").is_file():
            with (reg / f"{moved[1]}.csv").open(encoding="utf-8-sig", newline="") as f:
                away = {r.get("handle", ""): r for r in csv.DictReader(f)}
        with p.open(encoding="utf-8-sig", newline="") as f:  # read as the sample was drawn, so an unchanged row matches
            for r in csv.DictReader(f):
                key = (p.stem, key_of(p.stem, r))
                said = out.setdefault(key, set())
                said.add(claim_of(r))
                added = [c for c in ADDED.get(p.stem, ()) if c in r]
                if added:  # as the row read before a migration added the column
                    r = {c: v for c, v in r.items() if c not in added}
                    said.add(claim_of(r))
                if moved and not set(moved[2]) & set(r):
                    before, there = {}, away.get(r.get("handle", ""), {})
                    for col, v in r.items():
                        before[col] = v
                        if col == moved[0]:
                            for m in moved[2]:
                                before[m] = there.get(m, "")
                    said.add(claim_of(before))
    return out


def check_sheet(reg, sheet, transcripts=None):
    rows = tables.dicts(sheet)
    problems = []
    now = claims_now(reg)
    stale = set()
    for r in rows:  # a verdict on a row that has changed since it was sampled judged another claim: it does not count
        if r.get("claim") not in now.get((r["table"], r["row"]), ()):
            stale.add((r["table"], r["row"]))
            problems.append(f"{r['table']} {r['row']}: changed since it was sampled, so its verdict no longer counts: "
                            "draw the sample again")
    rows = [r for r in rows if (r["table"], r["row"]) not in stale]
    import go
    fid = flow_of_sheet(reg, sheet)
    s = next((x for x in go.load_all(reg) if go.flow_id_of(reg, x) == fid), None) if fid else None
    held = {(r["table"], r["row"]) for r in rows}
    for (t, k), cid in sorted(reopened(reg, s).items()):
        if (t, k) not in held:
            problems.append(f"{t} {k}: corrected by {cid} after the flow's report was sent, and not re-read since: "
                            f"draw the sample again (python reread.py <register> --flow {fid}), and send the report "
                            "again once it passes")
    for r in rows:
        v = (r.get("verdict") or "").strip().lower()
        if v not in VERDICTS:
            problems.append(f"{r['table']} {r['row']}: no verdict")
        elif v != "says":
            problems.append(f"{r['table']} {r['row']}: {v}: {r.get('reason', '')}")
    folders = [pathlib.Path(transcripts)] if transcripts else rc.project_folders(reg)
    sessions = rc.run_sessions(folders, reg)
    if not sessions:
        return Result(problems + [rc.no_record(folders)], len(rows))
    others = [p for p in reg.glob("*.csv") if not p.stem.startswith("re-read")]
    judges, why_not = [], []
    for s in sessions:
        uses = list(rc.tool_uses(s))
        if not _writes(uses, sheet):
            continue
        wrote = sorted(o.name for o in others if _writes(uses, o))
        shell = any(n in ("Bash", "PowerShell") and paths.norm(reg) in paths.norm(i.get("command", "")) for n, i in uses)
        if wrote:
            why_not.append(f"the session that wrote {sheet.name} also wrote {', '.join(wrote)}, so it is not independent "
                           "of the rows")
        elif shell:
            why_not.append(f"the session that wrote {sheet.name} also ran a shell command naming the register folder, "
                           "which could have written rows unseen; the re-reader runs no shell command on the register")
        else:
            judges.append(s)
    if not judges:
        problems += why_not or [
            f"no session wrote {sheet.name} with the Write or Edit tool: the re-reader writes its verdicts with Write or "
            "Edit (a file written by a shell command, or by hand, cannot be traced to who judged it)"]
    else:
        opened = rc.reads(judges)
        for r in rows:
            for path, a, b in rc.cited_in(r.get("citations", "")):
                spans = [x for p, xs in opened.items() if p.endswith("/" + path.lower()) for x in xs]
                if not paths.covered(a, b, spans):
                    problems.append(f"{r['table']} {r['row']}: the re-reader did not open {path}"
                                    + (f":{a}" if a else ""))
    return Result(problems, len(rows))


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if not argv:
        sys.exit(__doc__)
    if argv[0] == "--check":
        r = check(argv[1])
        print("\n".join(r.lines()))
        return 0 if r.passed else 1
    import run_lock  # the register is written by one run at a time
    fid = None
    if "--flow" in argv:  # an earlier flow's sample, drawn again while a later flow is worked
        i = argv.index("--flow")
        fid = argv[i + 1] if i + 1 < len(argv) else ""
        argv = argv[:i] + argv[i + 2:]
    run_lock.guard(argv[0])
    try:
        rows = draw(argv[0], int(argv[1]) if len(argv) > 1 else 10, fid)
    except ValueError as e:
        print(f"REFUSED: {e}. Nothing written.", file=sys.stderr)
        return 2
    import go
    s = next((x for x in go.load_all(argv[0]) if go.flow_id_of(argv[0], x) == fid), None) if fid else go.load(argv[0])
    print(f"{sheet_for(argv[0], s).name}: {len(rows)} row(s) drawn: the re-reader writes its verdicts in this file")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    sys.exit(main(sys.argv[1:]))
