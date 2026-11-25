"""Reading and writing the split run's CSV files, one helper per shape a caller needs. UTF-8, header row, Python's
csv module (split-run-formats.md). Python standard library only."""
import csv
import io
import pathlib


def decoded(path):
    """(the file's text, whether all of it could be read). UTF-8 with or without a byte order mark; else the Windows
    text format Excel and Notepad save (cp1252); else UTF-8 with each unreadable byte marked. NUL bytes are dropped.
    A missing file raises OSError."""
    data = pathlib.Path(path).read_bytes()
    whole = True
    for enc in ("utf-8-sig", "cp1252"):
        try:
            t = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        t, whole = data.decode("utf-8", errors="replace"), False
    return t.replace("\x00", ""), whole


def read_rows(path):
    """(the rows of a CSV file as dicts, whether all of it could be read). What precedes a malformed line is kept."""
    t, whole = decoded(path)
    rows = []
    try:
        for r in csv.DictReader(io.StringIO(t, newline="")):
            rows.append(r)
    except csv.Error:
        whole = False
    return rows, whole


def dicts(path, encoding="utf-8-sig"):
    """The rows as dicts, or [] when the file is missing."""
    path = pathlib.Path(path)
    if not path.is_file():
        return []
    with path.open(encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))


def table(path):
    """(header, rows in file order with every missing cell blank), or (None, []) when the file is missing."""
    path = pathlib.Path(path)
    if not path.is_file():
        return None, []
    with path.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return list(r.fieldnames or []), [{k: (v or "") for k, v in row.items() if k is not None} for row in r]


def grid(path):
    """(header, body) as lists of cells, ([], []) for an empty file. A missing file raises OSError."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        data = list(csv.reader(f))
    return (data[0], data[1:]) if data else ([], [])


def write_grid(path, header, body):
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([header] + body)


def filled(path):
    """The rows as dicts with blank rows dropped, or None when the file is missing, unreadable, malformed or has no
    data row: for a reader that must never fail on a file another process is writing."""
    try:
        t = pathlib.Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None
    if not t:
        return None
    try:
        rows = [r for r in csv.DictReader(t.splitlines()) if any((v or "").strip() for v in r.values()
                                                                   if isinstance(v, str))]
    except csv.Error:
        return None
    return rows or None


def text(cols, rows, lineterminator="\n"):
    """The CSV text of rows under cols: cells not in cols dropped, missing ones blank."""
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=cols, lineterminator=lineterminator, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return out.getvalue()


def write(path, cols, rows, lineterminator="\n"):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text(cols, rows, lineterminator))
