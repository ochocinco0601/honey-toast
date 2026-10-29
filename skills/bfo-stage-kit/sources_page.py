"""The sources page: what the run is working from, drawn from the register's files on each request, read-only.

Usage: python sources_page.py <register folder>   write sources.html in the register folder

One row per source the register was made from (sources.csv), each gathered; and one row per source pointed at or found
that could not be reached (RUN.md, *Sources*, the *Still missing* list), with the reason written there. Each row says
whether the person named the source or the run's own search found it (sources.csv `found_by`), and "not recorded"
where a register made before that column says neither. Nothing on the page is claimed beyond what those two files
say. The listener draws it on each request, so it is never behind the files.
Python standard library only."""
import hashlib
import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tables  # noqa: E402

FILE = "sources.html"
HOME = "index.html"
E = html.escape
KIND = {"code": "code", "document": "a document", "person": "notes or answers from a person",
        "tool output": "a tool's output"}
URL = re.compile(r"https?://[^\s<>\"')]+", re.I)  # only an address written with its scheme; a path stays text
FOUND_BY = {"person": "you named it", "run": "found by the run's search"}
TEMPLATE_LINE = "each source pointed at or found that could not be reached"
UNREADABLE = ("Part of the list of sources could not be read just now: it may be mid-save, or saved in a text "
              "format this page does not know. What could be read is below.")


class Unreadable(Exception):
    """sources.csv is there but not all of it is readable text in table form; `rows` holds what could be read."""

    def __init__(self, rows):
        super().__init__("sources.csv could not all be read")
        self.rows = rows


def rows(reg):
    """The rows of sources.csv, or [] when it is missing or holds only its header. Saved as UTF-8 (with or without a
    byte order mark) or in the Windows text format, it is read. Unreadable, carrying what could be read, otherwise."""
    try:
        got, whole = tables.read_rows(pathlib.Path(reg) / "sources.csv")
    except OSError:
        return []
    got = [r for r in got if (r.get("what") or "").strip()]
    if not whole:
        raise Unreadable(got)
    return got


def clean(text):
    """A cell for the person: no source ids, no backticks, a commit id cut to its first 7 characters."""
    t = re.sub(r"\bSRC\d+\b", "", text or "").replace("`", "")
    t = re.sub(r"\b([0-9a-f]{7})[0-9a-f]{1,33}\b", r"\1", t)
    return re.sub(r"\s{2,}", " ", t).strip(" ;,")


def same_source(r):
    """What makes two rows one source: a repository at a commit, or the name with a re-read note dropped."""
    kind = (r.get("kind") or "").strip()
    repo, commit = (r.get("repository") or "").strip(), (r.get("commit") or "").strip()
    if repo:
        return (kind, repo, commit)
    return (kind, re.sub(r"\s*\(re-read[^)]*\)\s*$", "", clean(r.get("what", ""))).lower())


def sources(reg, read=None):
    """The rows of sources.csv, one per source: a re-read of a source already listed is not a second source."""
    seen, out = set(), []
    for r in (rows(reg) if read is None else read):
        k = same_source(r)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def missing(reg):
    """[(name, reason)] from RUN.md's *Sources*, the *Still missing* bullet: one per nested bullet under it, or its own
    text when it has none. The template's instruction, "none" and an empty bullet give none."""
    p = pathlib.Path(reg) / "RUN.md"
    try:
        text = tables.decoded(p)[0]
    except OSError:
        return []
    sec = re.search(r"^## Sources\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not sec:
        return []
    lines = sec.group(1).splitlines()
    out, lead, inside = [], None, False
    for line in lines:
        m = re.match(r"^- \*\*Still missing:\*\*\s*(.*)$", line)
        if m:
            inside, lead = True, m.group(1).strip()
            continue
        if not inside:
            continue
        if re.match(r"^- ", line) or (line.strip() and not line.startswith(" ")):
            break
        sub = re.match(r"^\s+[-*] (.*)$", line)
        if sub:
            out.append(sub.group(1).strip())
        elif line.strip() and out:
            out[-1] += " " + line.strip()
        elif line.strip():
            lead += " " + line.strip()
    lead = (lead or "").strip()
    if lead.lower().startswith(TEMPLATE_LINE) or lead.lower().rstrip(".") in ("", "none", "nothing"):
        lead_reason = ""
        if not out:
            return []
    else:
        lead_reason = lead.split(":", 1)[1].strip() if ":" in lead else ""
        if not out:
            out = [lead]
            lead_reason = ""
    found = []
    for item in out:
        name, sep, why = item.rpartition(" — ")
        if not sep:
            name, why = item, lead_reason
        found.append((clean(name).rstrip("."), clean(why).rstrip(".") or "the reason is not recorded"))
    return found


def has_any(reg):
    """True when there is something to list: a source gathered, or one that could not be reached."""
    try:
        return bool(rows(reg)) or bool(missing(reg))
    except Unreadable:
        return True  # the page says it could not be read


def named(text):
    """The source's name, with each web address written with its scheme linked."""
    out, at = [], 0
    for m in URL.finditer(text):
        out += [E(text[at:m.start()]), f'<a href="{E(m.group(0))}" rel="noreferrer">{E(m.group(0))}</a>']
        at = m.end()
    return "".join(out) + E(text[at:])


def render(reg, home_href=None):
    reg = pathlib.Path(reg)
    if home_href is None:
        home_href = HOME if (reg / HOME).is_file() else "/"
    back = "Home" if home_href != "/" else "The run at work"
    try:
        gathered, said = sources(reg), ""
    except Unreadable as e:
        gathered, said = sources(reg, e.rows), f"<p>{E(UNREADABLE)}</p>"
    trs = [f'<tr><td>{named(clean(r.get("what", "")))}</td><td>{E(KIND.get((r.get("kind") or "").strip(), clean(r.get("kind", "")) or "not recorded"))}</td>'
           f'<td>{E(FOUND_BY.get((r.get("found_by") or "").strip().lower(), "not recorded"))}</td>'
           f'<td class="ok">gathered</td></tr>' for r in gathered]
    trs += [f'<tr><td>{named(n)}</td><td>not recorded</td><td></td><td class="bad">could not be reached: {E(w)}</td></tr>'
            for n, w in missing(reg)]
    body = said + (f'<div class="tw"><table><thead><tr><th>Source</th><th>What it is</th><th>How it came</th>'
                   f'<th>State</th></tr></thead>'
                   f'<tbody>{"".join(trs)}</tbody></table></div>' if trs else ("" if said else '<p>No source listed yet.</p>'))
    page = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n     Source: sources.csv and RUN.md in this folder\n"
            "     Builder: sources_page.py\n     Build: python sources_page.py <register folder>\n-->\n"
            "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Sources</title><style>"
            "body{margin:0;background:#F6F5F1;color:#1D1D1B;font:15px/1.5 'Segoe UI',system-ui,sans-serif}"
            ".nav{display:flex;flex-wrap:wrap;gap:6px 18px;background:#FFFFFF;border-bottom:1px solid #DAD7CD;padding:10px 16px;font-size:14px}"
            ".nav a{color:#1F4E8C;text-decoration:none}.nav a:hover{text-decoration:underline}.nav .on{font-weight:600}"
            ".wrap{box-sizing:border-box;max-width:980px;margin:0 auto;padding:18px 16px 48px}"
            ".card{background:#FFFFFF;border:1px solid #DAD7CD;border-radius:8px;padding:16px 20px;display:flex;flex-direction:column;gap:12px}"
            "h1{margin:0;font-size:22px}.mute{color:#5A5850;font-size:13px}a{color:#1F4E8C;overflow-wrap:anywhere}"
            ".tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}"
            "th{text-align:left;color:#5A5850;font-size:12px;padding:6px 8px;border-bottom:1px solid #DAD7CD}"
            "td{padding:6px 8px;border-bottom:1px solid #EEECE5;vertical-align:top;overflow-wrap:anywhere}"
            ".ok{color:#1D1D1B}.bad{color:#8A4B08}"
            "@media (max-width:600px){table,thead,tbody,tr,td{display:block}thead{display:none}"
            "tr{border-bottom:1px solid #DAD7CD;padding:6px 0}td{border:0;padding:2px 0}}"
            "</style></head><body>"
            f'<div class="nav"><a href="{E(home_href)}">{back}</a><span class="on" aria-current="page">Sources</span></div>'
            '<div class="wrap"><div class="card"><h1>Sources</h1>'
            '<div class="mute">What this run is working from: each source gathered so far, and each one pointed at or '
            'found that could not be reached, with why.</div>'
            f"{body}</div></div></body></html>")
    stamp = hashlib.sha256(page.encode("utf-8")).hexdigest()[:16]
    return page.replace('<meta charset="utf-8">', f'<meta charset="utf-8"><meta name="drawn" content="{stamp}">', 1)


def main(argv):
    if len(argv) != 1 or not pathlib.Path(argv[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    import run_lock
    run_lock.guard(pathlib.Path(argv[0]))
    out = pathlib.Path(argv[0]) / FILE
    out.write_text(render(argv[0]), encoding="utf-8", newline="\n")
    print(f"Written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
