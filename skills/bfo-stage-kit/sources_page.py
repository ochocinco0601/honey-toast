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


PATHISH = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]{1,5}|(?:[\w.-]+/)+[\w.-]+)(?![\w/])")
REMOTE = re.compile(r"^\s*url\s*=\s*(\S+)", re.M)
SHA = re.compile(r"[0-9a-f]{7,40}")


def editor_link(path):
    """Opens a file or folder in VS Code."""
    return "vscode://file/" + pathlib.Path(path).resolve().as_posix()


def web_repo(folder, commit):
    """The repository's web address at the commit read, from its git remote; None when it has none."""
    try:
        cfg = (pathlib.Path(folder) / ".git" / "config").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = REMOTE.search(cfg)
    if not m:
        return None
    url = re.sub(r"\.git$", "", re.sub(r"^git@([^:]+):", r"https://\1/", m.group(1)))
    url = re.sub(r"^(https?://)[^/@]*@", r"\1", url)  # never copy a user name, password or token into the page
    if not url.startswith("http"):
        return None
    return f"{url}/tree/{commit}" if SHA.fullmatch(commit or "") else url


def named(text, bases=()):
    """The source's name: each web address written with its scheme linked, and each file or folder it names that
    exists in the workspace or the register folder linked to open in VS Code."""
    spans = [(m.start(), m.end(), m.group(0)) for m in URL.finditer(text)]
    for m in PATHISH.finditer(text):
        if any(a <= m.start() < b for a, b, _ in spans):
            continue
        hit = next((b / m.group(1) for b in bases if (b / m.group(1)).exists()), None)
        if hit:
            spans.append((m.start(1), m.end(1), editor_link(hit)))
    out, at = [], 0
    for a, b, href in sorted(spans):
        if a >= at:
            out += [E(text[at:a]), f'<a href="{E(href)}" rel="noreferrer">{E(text[a:b])}</a>']
            at = b
    return "".join(out) + E(text[at:])


SHORT_KIND = {"code": "Code", "document": "Document", "person": "Person", "tool output": "Tool output"}
SHORT_FOUND = {"person": "You", "run": "The run"}


def items(r, bases):
    """The source's files and folders, each linked: its repository folder, then each existing path its name gives.
    A source naming none is shown by the first clause of its name."""
    what = clean(r.get("what", ""))
    repo, commit = (r.get("repository") or "").strip(), (r.get("commit") or "").strip()
    out, seen = [], set()
    if repo and not bases:
        out.append(E(repo))
    elif repo:
        root = bases[0]
        folder = root / repo
        web = web_repo(folder, commit) if folder.is_dir() else None
        out.append(f'<a href="{E(editor_link(folder))}">{E(repo)}/</a>' if folder.exists() else E(repo))
        if web:
            out[-1] += f' <a class="web" href="{E(web)}" rel="noreferrer">web</a>'
        seen.add(repo.rstrip("/"))
    for m in URL.finditer(what):
        out.append(f'<a href="{E(m.group(0))}" rel="noreferrer">{E(m.group(0))}</a>')
    for m in PATHISH.finditer(what):
        p = m.group(1)
        hit = next((b / p for b in bases if (b / p).exists()), None)
        if hit and p not in seen:
            seen.add(p)
            out.append(f'<a href="{E(editor_link(hit))}">{E(p + ("/" if hit.is_dir() else ""))}</a>')
    if not out:
        out.append(E(re.split(r"[:,(]", what, maxsplit=1)[0].strip() or what))
    return "<br>".join(out)


def version(commit):
    if not commit:
        return '<span class="mute">—</span>'
    if SHA.fullmatch(commit):
        return f"<code>{E(commit[:7])}</code>"
    return '<span class="mute">none</span>'


def git_root(path, stop):
    """The nearest folder at or above `path` holding .git, not above `stop`; None when there is none."""
    p = pathlib.Path(path).resolve()
    stop = pathlib.Path(stop).resolve()
    while True:
        if (p / ".git").exists():
            return p
        if p == stop or p.parent == p:
            return None
        p = p.parent


def paths_in(r, bases):
    """The existing files and folders a row's name gives, resolved."""
    out = []
    for m in PATHISH.finditer(clean(r.get("what", ""))):
        hit = next((b / m.group(1) for b in bases if (b / m.group(1)).exists()), None)
        if hit:
            out.append(hit.resolve())
    return out


def source_name(r):
    """A short name for the place a row came from: its name up to the first clause break."""
    what = clean(r.get("what", ""))
    head = re.split(r",|:|\s+as found\b|\s+at commit\b|\s+in this register\b", what, maxsplit=1)[0].strip()
    return re.split(r"\s+\(", head, maxsplit=1)[0].strip() or what


def source_about(r):
    """What the source is, from the parenthesis after its name, when there is one."""
    m = re.match(r"[^(,:]*\(([^)]*)\)", clean(r.get("what", "")))
    return m.group(1).strip() if m else ""


def group(gathered, bases, reg):
    """The places material came from, each with the rows taken from it. Code rows in one git repository are one
    source; without git history, each top folder named in `repository` is a source of its own, so separate
    repositories copied in without history are never merged. A document whose files all sit in a source's folder
    belongs to it. Every other row is a source of its own."""
    root, groups, by_repo = (bases[0] if bases else pathlib.Path(reg).resolve()), [], {}
    for r in gathered:
        repo = (r.get("repository") or "").strip()
        if (r.get("kind") or "").strip() == "code" and repo:
            top = root / pathlib.PurePosixPath(repo.replace("\\", "/")).parts[0]
            home = git_root(root / repo, root) or top.resolve()
            if home not in by_repo:
                by_repo[home] = {"kind": "repository", "home": home, "rows": []}
                groups.append(by_repo[home])
            by_repo[home]["rows"].append(r)
    for r in gathered:
        if r in [x for g in by_repo.values() for x in g["rows"]]:
            continue
        files = paths_in(r, bases)
        home = next((h for h in by_repo if files and all(h == f or h in f.parents for f in files)), None)
        if home is not None and (r.get("kind") or "").strip() == "document":
            by_repo[home]["rows"].append(r)
        else:
            groups.append({"kind": (r.get("kind") or "").strip(), "home": None, "rows": [r]})
    return groups


TYPE = {"repository": "Repository", "code": "Code", "document": "Document", "person": "Person", "tool output": "The run's own analysis"}


NOT_RECORDED = '<span class="mute">not recorded</span>'


def source_row(n, g, bases):
    rows, first = g["rows"], g["rows"][0]
    commits = {(r.get("commit") or "").strip() for r in rows if (r.get("commit") or "").strip()}
    sha = next((c for c in commits if SHA.fullmatch(c)), "")
    if not sha:
        named_commit = (re.search(r"\bcommit ([0-9a-f]{7,40})\b", r.get("what") or "") for r in rows)
        sha = next((m.group(1) for m in named_commit if m), "")
    if g["kind"] == "repository":
        web = web_repo(g["home"], sha)
        link = web or (editor_link(g["home"]) if bases and g["home"].exists() else "")
        nm = source_name(first)
        if nm.lower().startswith("same "):
            nm = g["home"].name
        name = f'<a href="{E(link)}" rel="noreferrer">{E(nm)}</a>' if link else E(nm)
        ver = f"<code>{E(sha[:7])}</code>" if sha else '<span class="mute">not recorded</span>'
    else:
        urls = [m.group(0) for m in URL.finditer(clean(first.get("what", "")))]
        files = paths_in(first, bases)
        link = urls[0] if urls else (editor_link(files[0]) if len(files) == 1 else "")
        nm = source_name(first)
        name = f'<a href="{E(link)}" rel="noreferrer">{E(nm)}</a>' if link else E(nm)
        ver = f"<code>{E(sha[:7])}</code>" if sha else '<span class="mute">not recorded</span>'
    who = "You" if any((r.get("found_by") or "").strip().lower() == "person" for r in rows) else (
        "The run" if any((r.get("found_by") or "").strip().lower() == "run" for r in rows) else "")
    who = E(who) if who else NOT_RECORDED
    taken = "".join(f'<li><div class="it">{items(r, bases)}</div>'
                    + f'<div>{named(clean(r.get("what", "")), bases)}</div>'
                    + (f'<div class="use">{E(clean(r.get("note", "")))}</div>' if clean(r.get("note", "")) else "")
                    + "</li>" for r in rows)
    about = source_about(first)
    if about:
        name += f'<span class="about">{E(about)}</span>'
    return (f'<tr><td class="tgc"><button class="tg" aria-expanded="false" aria-label="Show what was taken">'
            f'<span>▸</span></button></td><td class="n">{n}</td><td class="nm">{name}</td>'
            f'<td>{E(TYPE.get(g["kind"], g["kind"] or "not recorded"))}</td><td>{ver}</td><td>{who}</td></tr>'
            f'<tr class="det" hidden><td></td><td></td><td colspan="4"><ul class="taken">{taken}</ul></td></tr>')


def missing_row(n, name, why, bases):
    why = "" if why == "the reason is not recorded" else why
    return (f'<tr><td class="n gapn">{n}</td><td>{named(name, bases)}</td>'
            f'<td>{E(why) if why else "<span class=mute>not recorded</span>"}</td></tr>')


def split_missing(found):
    """A Still-missing bullet written as one sentence of items joined by semicolons is shown one item each."""
    if len(found) != 1:
        return found
    (name, why), parts, depth, cur = found[0], [], 0, ""
    for ch in name:
        depth += ch == "("
        depth -= ch == ")"
        if ch == ";" and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    parts = [p for p in parts + [cur.strip()] if p]
    return [(p[0].upper() + p[1:], why) for p in parts] if len(parts) > 1 else found


def render(reg, home_href=None):
    reg = pathlib.Path(reg)
    in_workspace = reg.resolve().parent.name == "bfo-work"
    bases = (reg.resolve().parent.parent, reg.resolve()) if in_workspace else ()
    if home_href is None:
        home_href = HOME if (reg / HOME).is_file() else "/"
    back = "Home" if home_href != "/" else "All runs"
    import page_style as ps
    up = (f'<a href="{ps.all_systems_href(home_href)}">{ps.ALL_SYSTEMS}</a>'
          if home_href == HOME and ps.all_systems_above(reg) else "")
    try:
        gathered, said = sources(reg), ""
    except Unreadable as e:
        gathered, said = sources(reg, e.rows), f"<p>{E(UNREADABLE)}</p>"
    gaps = split_missing(missing(reg))
    body = said
    groups = group(gathered, bases, reg)
    if groups:
        body += (f'<h2>Gathered <span class="count">{len(groups)}</span></h2><div class="tw"><table>'
                 '<thead><tr><th></th><th>#</th><th>Source</th><th>Type</th><th>Version</th><th>Found by</th>'
                 '</tr></thead><tbody>'
                 + "".join(source_row(i, g, bases) for i, g in enumerate(groups, 1)) + "</tbody></table></div>")
    if gaps:
        k = len(groups)
        body += (f'<h2>Could not be reached <span class="count gapc">{len(gaps)}</span></h2><div class="tw"><table>'
                 '<thead><tr><th>#</th><th>What</th><th>Why</th></tr></thead><tbody>'
                 + "".join(missing_row(k + i, n, w, bases) for i, (n, w) in enumerate(gaps, 1))
                 + "</tbody></table></div>")
    if not body:
        body = "<p>No source listed yet.</p>"
    page = ("<!-- THIS FILE IS GENERATED. DO NOT EDIT DIRECTLY.\n     Source: sources.csv and RUN.md in this folder\n"
            "     Builder: sources_page.py\n     Build: python sources_page.py <register folder>\n-->\n"
            "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Sources</title><style>"
            "body{margin:0;background:#F6F5F1;color:#1D1D1B;font:14px/1.4 'Segoe UI',system-ui,sans-serif}"
            ".nav{display:flex;flex-wrap:wrap;gap:6px 18px;background:#FFFFFF;border-bottom:1px solid #DAD7CD;padding:10px 16px;font-size:14px}"
            ".nav a{color:#1F4E8C;text-decoration:none}.nav a:hover{text-decoration:underline}.nav .on{font-weight:600}"
            ".wrap{box-sizing:border-box;max-width:1280px;margin:0 auto;padding:12px 16px 32px}"
            ".card{background:#FFFFFF;border:1px solid #DAD7CD;border-radius:8px;padding:12px 16px}"
            "h1{margin:0 0 4px;font-size:22px}.mute{color:#5A5850;font-size:13px}a{color:#1F4E8C;overflow-wrap:anywhere}"
            "h2{font-size:15px;margin:14px 0 4px;display:flex;align-items:center;gap:8px}"
            ".count{font-size:12px;font-weight:600;background:#E7EEF7;color:#1F4E8C;border-radius:10px;padding:1px 8px}"
            ".count.gapc{background:#F6E9D8;color:#8A4B08}"
            ".tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}"
            "th{text-align:left;color:#5A5850;font-size:12px;font-weight:600;padding:4px 8px;border-bottom:2px solid #DAD7CD;white-space:nowrap}"
            "td{padding:3px 8px;border-bottom:1px solid #EEECE5;vertical-align:top}tbody tr:hover{background:#FAF9F5}"
            "td.n{color:#1F4E8C;font-weight:600;width:28px}td.gapn{color:#8A4B08}"
            ".it{font-family:Consolas,monospace;font-size:13px;line-height:1.7}.web{font-family:'Segoe UI',sans-serif;font-size:11px;"
            "border:1px solid #C9D6E8;border-radius:4px;padding:0 4px;margin-left:4px;text-decoration:none}"
            "td.nm{font-weight:600}.about{font-weight:400;color:#5A5850;font-size:12.5px;margin-left:8px}"
            "td.tgc{width:20px;padding-right:0}.tg{border:0;background:none;cursor:pointer;color:#1F4E8C;font-size:18px;padding:0 4px;line-height:1}"
            ".tg span{display:inline-block;transition:transform .15s}.tg[aria-expanded=true] span{transform:rotate(90deg)}"
            "tr.det td{background:#FAF9F5;border-bottom:1px solid #DAD7CD}tr.det:hover{background:none}"
            ".taken{margin:0;padding-left:16px;font-size:13px}.taken li{margin:0 0 4px}.use{color:#5A5850;max-width:640px}"
            "code{font:12px Consolas,monospace;background:#F1EFE8;border-radius:4px;padding:1px 5px}"
            "</style></head><body>"
            f'<div class="nav">{up}<a href="{E(home_href)}">{back}</a><span class="on" aria-current="page">Sources</span>{ps.kit_label()}</div>'
            '<div class="wrap"><div class="card"><h1>Sources</h1>'
            '<div class="mute">What this run is working from: each source gathered so far, and each one pointed at or '
            'found that could not be reached, with why.</div>'
            f"{body}</div></div>"
            "<script>document.querySelectorAll('.tg').forEach(function(b){b.addEventListener('click',function(){"
            "var d=b.closest('tr').nextElementSibling,o=b.getAttribute('aria-expanded')==='true';"
            "b.setAttribute('aria-expanded',String(!o));d.hidden=o;});});</script></body></html>")
    stamp = hashlib.sha256(page.encode("utf-8")).hexdigest()[:16]
    return page.replace('<meta charset="utf-8">', f'<meta charset="utf-8"><meta name="drawn" content="{stamp}">', 1)


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
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
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
