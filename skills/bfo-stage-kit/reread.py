"""Draw a sample of register rows to be re-read against their code, and say whether the re-read was done.

Usage: python reread.py <register folder> [how many, default 10]      draws re-read.csv
       python reread.py --check <register folder>                     says whether it was done

The sample is audit sampling: rows are drawn from every table that cites code, calls between parts that rest only on
the run's reading (`proposed:`) first, since no cited line states them: they rest on the reading alone. An agent that wrote
none of the rows opens each row's cited lines with the Read tool and writes its verdict in re-read.csv: `says` (the
code does what the row claims), `does not say`, or `unclear`, with the reason. The check passes only when every row
says, the verdicts were written by a session that wrote no other table of the register, and that session opened every
cited line. All three are read from Claude Code's own record of the sessions (reading_check.py finds it). A row that
does not say is fixed where it was written, and the sample is drawn again."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reading_check as rc  # noqa: E402
import paths  # noqa: E402
import tables  # noqa: E402

NOT_ROWS = {"sources", "how-made", "survey", "set-aside", "re-read", "re-read-history", "about"}
FIELDS = ["table", "row", "claim", "citations", "verdict", "reason"]
VERDICTS = {"says", "does not say", "unclear"}


def candidates(reg):
    calls, rest = [], {}
    for p in sorted(pathlib.Path(reg).glob("*.csv")):
        if p.stem in NOT_ROWS:
            continue
        with p.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                text = " ".join(v for v in r.values() if isinstance(v, str))
                cited = rc.cited_in(text)
                if not cited:
                    continue
                key = next(iter(r.values()), "")
                row = {"table": p.stem, "row": key, "claim": text[:400],
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


def draw(reg, n=10):
    """A fresh sample. A redraw keeps each row the last sample did not bear out, so it is checked again after its fix,
    and fills the rest with rows never drawn before; every earlier draw is kept in re-read-history.csv."""
    reg = pathlib.Path(reg)
    last = tables.dicts(reg / "re-read.csv")
    history = reg / "re-read-history.csv"
    if last:
        old = tables.dicts(history)
        tables.write(history, FIELDS, old + last, lineterminator="\r\n")
    seen = {(r["table"], r["row"]) for r in tables.dicts(history)}
    again = {(r["table"], r["row"]) for r in last if (r.get("verdict") or "").strip().lower() != "says"}
    pool = candidates(reg)
    rows = [r for r in pool if (r["table"], r["row"]) in again]
    rows += [r for r in pool if (r["table"], r["row"]) not in seen][:max(0, n - len(rows))]
    tables.write(reg / "re-read.csv", FIELDS, [dict(r, verdict="", reason="") for r in rows], lineterminator="\r\n")
    return rows


class Result:
    def __init__(self, problems, n):
        self.problems, self.n = problems, n
        self.passed = not problems

    def lines(self):
        if self.passed:
            return [f"Re-read: {self.n} sampled row(s) re-read against their code by an agent that wrote none of "
                    "them, each one borne out: ok"]
        return ["Re-read: NOT DONE"] + [f"  {p}" for p in self.problems]


def _writes(uses, path):
    p = paths.norm(path)
    return any(name in ("Write", "Edit", "MultiEdit") and paths.norm(inp.get("file_path", "")) == p
               for name, inp in uses)


def check(reg, transcripts=None):
    reg = pathlib.Path(reg).resolve()
    sheet = reg / "re-read.csv"
    if not candidates(reg):
        return Result([], 0)
    if not sheet.is_file():
        return Result(["no re-read.csv: draw it with reread.py and have an agent that wrote none of the rows judge it"], 0)
    rows = tables.dicts(sheet)
    problems = []
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
    others = [p for p in reg.glob("*.csv") if p.stem != "re-read"]
    judges, why_not = [], []
    for s in sessions:
        uses = list(rc.tool_uses(s))
        if not _writes(uses, sheet):
            continue
        wrote = sorted(o.name for o in others if _writes(uses, o))
        shell = any(n in ("Bash", "PowerShell") and paths.norm(reg) in paths.norm(i.get("command", "")) for n, i in uses)
        if wrote:
            why_not.append(f"the session that wrote re-read.csv also wrote {', '.join(wrote)}, so it is not independent "
                           "of the rows")
        elif shell:
            why_not.append("the session that wrote re-read.csv also ran a shell command naming the register folder, "
                           "which could have written rows unseen; the re-reader runs no shell command on the register")
        else:
            judges.append(s)
    if not judges:
        problems += why_not or [
            "no session wrote re-read.csv with the Write or Edit tool: the re-reader writes its verdicts with Write or "
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
    if not argv:
        sys.exit(__doc__)
    if argv[0] == "--check":
        r = check(argv[1])
        print("\n".join(r.lines()))
        return 0 if r.passed else 1
    import run_lock  # the register is written by one run at a time
    run_lock.guard(argv[0])
    rows = draw(argv[0], int(argv[1]) if len(argv) > 1 else 10)
    print(f"re-read.csv: {len(rows)} row(s) drawn")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    sys.exit(main(sys.argv[1:]))
