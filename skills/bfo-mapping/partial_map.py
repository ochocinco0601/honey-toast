"""The map so far, while process mapping is still under way: drawn by the listener on each request at
<register>/map-so-far.html and never written as a file, so it is never taken for the checked map (views.html, which
one_canvas.py writes only once capability_views.py --check passes). Every row the check names by table and row is
left out and listed at the top with its message; the rest is drawn. Never raises: a map that cannot be drawn at all
says why. Python standard library only."""
import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PARTIAL = "Partial: process mapping is still under way; rows may change before it is checked."
NAMED = re.compile(r"^([a-z0-9-]+)\.csv (\d+)\b")  # "steps.csv 1: business_subject S999 is not a subject"


def _left_out(R, err):
    """Remove from R each row an error names by table and row number; return the messages of the rows removed, and
    the errors that name no row (kept, listed, and the map drawn without regard to them)."""
    drop, other = {}, []
    for e in err:
        m = NAMED.match(str(e))
        if m and m.group(1) in R and isinstance(R[m.group(1)], list):
            drop.setdefault(m.group(1), set()).add(int(m.group(2)))
        else:
            other.append(str(e))
    said = []
    for table, ns in drop.items():
        rows = R[table]
        R[table] = [r for i, r in enumerate(rows, 1) if i not in ns]
        said += [e for e in err if str(e).startswith(f"{table}.csv ")]
    return said, other


def render(reg):
    reg = pathlib.Path(reg)
    E = html.escape
    try:
        import capability_views as cv
        import one_canvas as oc
        R = cv.load(reg)
        err, warn = cv.check(R)
        said, other = _left_out(R, err)
        M = oc.number_steps(oc.prune(cv.model(R)))
        body = oc.page(M, reg.as_posix(), "drawn live by the listener, never written", (len(err), len(warn)),
                       oc.with_stage_pages(M, oc.stage_docs(reg)))
    except Exception as e:  # noqa: BLE001  (the partial map says why it cannot be drawn; it never fails the page)
        said, other = [], []
        body = f"<p>The map so far cannot be drawn yet: {E(type(e).__name__)}: {E(str(e))[:300]}</p>"
    n = len(said) + len(other)
    items = "".join(f"<li>{E(x)}</li>" for x in said + other)
    head = (f'<div class="partial" style="border:2px solid #b26b00;padding:8px 12px;margin:8px"><b>{E(PARTIAL)}</b>'
            + (f"<p>{n} {'row' if n == 1 else 'rows'} left out, each with what the check says:</p><ul>{items}</ul>"
               if n else "<p>No row left out.</p>") + "</div>")
    if "<body" in body:
        return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + head, body, count=1)
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Map so far</title></head><body>{head}{body}</body></html>"
