"""List the reading units of a split run: one per deployable, a deployable too large for one reader cut by folder.

Usage: python units.py <register folder> [--unit-lines N]

Reads survey.csv (survey.py) and fact-base.json (the code reader) in the register folder and writes units/units.csv,
in the form split-run-formats.md sets. The first unit is `flow`, the lead's own flow-level tables at the register's
root. Then one unit per surveyed service (survey `kind` `service`: configuration folders are not units), in survey
order. A deployable whose source lines (as the survey counts them: non-blank, outside tests) exceed the unit size is
cut into units `<deployable>-1`, `-2`, ... by folder: whole folders are packed in order, a folder larger than the size
is cut by its own folders, and files directly in a cut folder are a part of their own. The parts together cover every
file of the deployable, so nothing in it goes unread. The unit size is --unit-lines, else `unit_lines` in
run-settings.json, else 4000. The same inputs give the same file.

units.csv only grows, since every flow of the register reads the same units: a later run keeps every row already
listed, as it is and in its order, never cuts again a deployable already listed (whatever its size now), and adds
units only for services not yet listed, after the others."""
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


def survey_services(reg):
    """The surveyed services (survey.csv rows of kind `service`), in survey order; [] with no survey.csv."""
    p = pathlib.Path(reg) / "survey.csv"
    if not p.is_file():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return [s for s in csv.DictReader(f) if (s.get("kind") or "").strip() == "service"]


def derive(reg, size=None, kept=None):
    """The rows units.py writes to units.csv: `kept` (the rows listed already, as they are; [] for a fresh cut) and a
    unit, or a cut of units, for every surveyed service not listed in them."""
    reg = pathlib.Path(reg).resolve()
    ws = reg.parent.parent
    size = unit_lines(reg) if size is None else size
    with (reg / "survey.csv").open(encoding="utf-8-sig", newline="") as f:
        services = list(csv.DictReader(f))
    fb = reg / "fact-base.json"
    facts = json.loads(fb.read_text(encoding="utf-8")).get("facts", []) if fb.is_file() else []

    def facts_in(paths):
        return sum(1 for x in facts if any(x.get("file", "") == p or x.get("file", "").startswith(p.rstrip("/") + "/")
                                           for p in paths))

    kept = [{c: r.get(c) or "" for c in FIELDS} for r in (kept or [])]
    rows = kept if any(r["unit"] == "flow" for r in kept) else [
        dict(unit="flow", deployable="", repository="", paths="", files="", lines="", reader_facts="", calls="",
             called_by="", note="the lead's flow-level tables at the register's root")] + kept
    listed = {r["deployable"].strip() for r in rows if r["unit"] != "flow"}
    for s in services:
        name, path = s["service"].strip(), s["path"].strip()
        if (s.get("kind") or "").strip() != "service" or name in listed:
            continue  # a configuration folder is not a unit; a deployable listed already is never cut again
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
    return rows


def baseline(reg):
    """The units list units.py would have kept: the longest a finished flow left (units.csv only grows), else []."""
    got = []
    # earlier-flows/<id>/judged/units/units.csv: the units list as a finished flow left it
    for p in sorted((pathlib.Path(reg) / "earlier-flows").glob(f"*/judged/{layout.UNITS_CSV}")):
        rows = tables.dicts(p)
        if len(rows) > len(got):
            got = rows
    return got


def _deployable(r):
    return (r.get("deployable") or "").strip() or (r.get("unit") or "").strip()


def _shape(r):
    return ((r.get("unit") or "").strip(), _deployable(r),
            ";".join(p.strip() for p in (r.get("paths") or "").split(";") if p.strip()))


def differences(reg, took=None):
    """How units.csv differs from what units.py derives for the go's scope: for each service the go
    took in (`took`, lower-cased names; None for every surveyed service), the units, their deployable and the paths
    each covers must be exactly those units.py lists, kept rows as a finished flow left them. Lines, files and reader
    facts are not compared: they move whenever the workspace or the code reader's findings do. [] when they match."""
    reg = pathlib.Path(reg)
    services = survey_services(reg)
    names = {(s.get("service") or "").strip().lower(): (s.get("service") or "").strip() for s in services}
    scope = sorted(names) if took is None else sorted(took)
    out = [f"the go took in {n!r}, which survey.csv lists as no service, so units.py lists no unit for it"
           for n in scope if n not in names]
    scope = [n for n in scope if n in names]
    if not scope:
        return out
    listed = tables.dicts(reg / layout.UNITS_CSV)
    want = [_shape(r) for r in derive(reg, kept=baseline(reg)) if _deployable(r).lower() in scope]
    have = [_shape(r) for r in listed if (r.get("unit") or "").strip() != "flow" and _deployable(r).lower() in scope]
    for n in scope:
        w = [x for x in want if x[1].lower() == n]
        h = [x for x in have if x[1].lower() == n]
        if not h:
            out.append(f"{names[n]}, a service the go took in, has no unit in {layout.UNITS_CSV}; units.py lists "
                       + ", ".join(f"{u} ({p})" for u, _, p in w))
        elif sorted(w) != sorted(h):
            out.append(f"the units of {names[n]} are " + ", ".join(f"{u} ({p})" for u, _, p in h)
                       + "; units.py lists " + ", ".join(f"{u} ({p})" for u, _, p in w))
    return out


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if not argv:
        sys.exit(__doc__)
    reg = pathlib.Path(argv[0]).resolve()
    size = int(argv[argv.index("--unit-lines") + 1]) if "--unit-lines" in argv else unit_lines(reg)
    out = reg / layout.UNITS_CSV
    rows = derive(reg, size, tables.dicts(out))
    out.parent.mkdir(exist_ok=True)
    tables.write(out, FIELDS, rows)
    print(f"{len(rows) - 1} reading units of at most {size} lines, plus the flow unit: {out}")
    for r in rows[1:]:
        print(f"- {r['unit']}: {r['lines']} lines, {r['files']} files, {r['reader_facts']} code-reader facts"
              + (f" ({r['note']})" if r["note"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
