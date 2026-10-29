"""List the reading units of a split run: one per deployable, a deployable too large for one reader cut by folder.

Usage: python units.py <register folder> [--unit-lines N]

Reads survey.csv (survey.py) and fact-base.json (the code reader) in the register folder and writes units/units.csv,
in the form split-run-formats.md sets. The first unit is `flow`, the lead's own flow-level tables at the register's
root. Then one unit per surveyed deployable, in survey order. A deployable whose source lines (as the survey counts
them: non-blank, outside tests) exceed the unit size is cut into units `<deployable>-1`, `-2`, ... by folder: whole
folders are packed in order, a folder larger than the size is cut by its own folders, and files directly in a cut
folder are a part of their own. The parts together cover every file of the deployable, so nothing in it goes unread.
The unit size is --unit-lines, else `unit_lines` in run-settings.json, else 4000. The same inputs give the same file."""
import csv
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import survey  # noqa: E402
import settings  # noqa: E402
import tables  # noqa: E402
import register_layout as layout  # noqa: E402

FIELDS = layout.UNITS_COLS


def files_under(p):
    p = pathlib.Path(p)
    if p.is_file():
        return [p]
    return list(survey.walk(p)) if p.is_dir() else []


def source_lines(p, ws):
    n = 0
    for f in files_under(p):
        rel = f.relative_to(ws).as_posix()
        if survey.SOURCE.get(f.suffix.lower()) and not (survey.TEST.search(rel) or survey.TEST.search(f.name)):
            n += survey.nonblank(f)
    return n


def cut(folder, ws, size):
    """Lists of paths (relative to ws), each list one part, together covering every file under folder."""
    parts, cur, cur_n = [], [], 0
    loose = [f for f in sorted(folder.iterdir()) if f.is_file()]
    subs = [d for d in sorted(folder.iterdir()) if d.is_dir() and d.name not in survey.SKIP
            and not d.name.startswith(".")]
    pieces = [(d, source_lines(d, ws)) for d in subs]
    if loose:
        pieces.insert(0, (None, sum(source_lines(f, ws) for f in loose)))
    for d, n in pieces:
        if d is not None and n > size and any(x.is_dir() for x in d.iterdir()):
            if cur:
                parts.append(cur)
                cur, cur_n = [], 0
            parts.extend(cut(d, ws, size))
            continue
        names = [f.relative_to(ws).as_posix() for f in loose] if d is None else [d.relative_to(ws).as_posix()]
        if cur and cur_n + n > size:
            parts.append(cur)
            cur, cur_n = [], 0
        cur += names
        cur_n += n
    if cur:
        parts.append(cur)
    return parts


def joined(parts, ws, size):
    """Neighbouring parts joined while they fit, and a part with no source lines always joined to its neighbour."""
    out = []
    for p in parts:
        n = sum(source_lines(ws / x, ws) for x in p)
        if out and (n == 0 or out[-1][1] == 0 or out[-1][1] + n <= size):
            out[-1] = (out[-1][0] + p, out[-1][1] + n)
        else:
            out.append((p, n))
    return [p for p, _ in out]


def unit_lines(reg):
    """The unit size from run-settings.json; a file that cannot be read as settings gives the default."""
    try:
        s = settings.load(reg)
    except ValueError:
        s = settings.DEFAULTS
    return settings.number(s, "unit_lines")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    reg = pathlib.Path(argv[0]).resolve()
    ws = reg.parent.parent
    size = int(argv[argv.index("--unit-lines") + 1]) if "--unit-lines" in argv else unit_lines(reg)
    with (reg / "survey.csv").open(encoding="utf-8-sig", newline="") as f:
        services = list(csv.DictReader(f))
    fb = reg / "fact-base.json"
    facts = json.loads(fb.read_text(encoding="utf-8")).get("facts", []) if fb.is_file() else []

    def facts_in(paths):
        return sum(1 for x in facts if any(x.get("file", "") == p or x.get("file", "").startswith(p.rstrip("/") + "/")
                                           for p in paths))

    rows = [dict(unit="flow", deployable="", repository="", paths="", files="", lines="", reader_facts="",
                 calls="", called_by="", note="the lead's flow-level tables at the register's root")]
    for s in services:
        name, path = s["service"].strip(), s["path"].strip()
        folder = ws / path
        lines = int(s.get("lines") or 0)
        parts = [[path]] if lines <= size or not folder.is_dir() else joined(cut(folder, ws, size), ws, size)
        for i, paths in enumerate(parts, 1):
            unit = name if len(parts) == 1 else f"{name}-{i}"
            fl = [f for p in paths for f in files_under(ws / p)]
            rows.append(dict(unit=unit, deployable=name, repository=s.get("repository", "").strip(),
                             paths=";".join(paths), files=str(len(fl)),
                             lines=str(lines if len(parts) == 1 else sum(source_lines(ws / p, ws) for p in paths)),
                             reader_facts=str(facts_in(paths)), calls=s.get("calls", "").strip().replace("; ", ";"),
                             called_by=s.get("called_by", "").strip().replace("; ", ";"),
                             note="" if len(parts) == 1 else f"part {i} of {len(parts)} of {name}"))
    out = reg / layout.UNITS_CSV
    out.parent.mkdir(exist_ok=True)
    tables.write(out, FIELDS, rows)
    print(f"{len(rows) - 1} reading units of at most {size} lines, plus the flow unit: {out}")
    for r in rows[1:]:
        print(f"- {r['unit']}: {r['lines']} lines, {r['files']} files, {r['reader_facts']} code-reader facts"
              + (f" ({r['note']})" if r["note"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
