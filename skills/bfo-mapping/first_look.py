"""The first look's reading of every source the person gives that is not code: owed parts listed by script, one
reader per part (or the lead alone, decided by script), a fixed file per part, and a check, from Claude Code's own
transcripts, that every owed part was read and that every spot and name a reader cites is in the source.

Usage: python first_look.py prepare <register>           survey, code reader, fetch and prompts in one command; prints
                                                          every reader's pointer line, to launch in one message
       python first_look.py merge <register>             merge the readers' leads by name (first-look/leads-merged.json)
                                                          and place each name no code holds as unresolved
       python first_look.py fetch <register>             list the owed parts (first-look/parts.csv), convert what
                                                          needs it, and decide single or split (first-look/mode.json)
       python first_look.py prompts <register>           one prompt per owed part (split), or the lead's parts list
       python first_look.py check <register> [--transcripts DIR]   the coverage check; exit 2 on any problem
       python first_look.py names <register>             the names the sources mention that no code holds, unplaced
       python first_look.py holdings <register> --for <phase>       what the sources hold for that phase, with spots

A source row of sources.csv is "other" when its kind is not `code` and it is not the run's own tool output; its
`location` column says where it is: paths relative to the workspace root (several joined by "; "), or
`connector:<connector>:<reference>` for a source fetched through a connector. Python standard library only."""
import csv
import datetime
import html
import io
import json
import os
import pathlib
import re
import sys
import time
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paths  # noqa: E402
import register_layout as layout  # noqa: E402

FL = "first-look"
PARTS = f"{FL}/parts.csv"
MODE = f"{FL}/mode.json"
PLACED = f"{FL}/placed.csv"
CONVERTED = f"{FL}/converted"
COPIES = f"{FL}/sources"
LEAD_PROMPT = "first-look-lead.md"  # prompts/first-look-lead.md: the first-look helper's own prompt
READER_PROMPTS = "first-look"  # prompts/first-look/read-<source>[-<part>].md
READER_TYPE = "bfo-source-reader"
PART_COLS = ("source_id", "part", "reader", "route", "path", "lines", "pages", "chars", "files", "original")
READER_PARTS = 12  # at most this many parts to one reader: a reader's start-up cost is paid once for its share
PLACED_COLS = ("name", "placed_as", "why")
PLACEMENTS = ("used", "unresolved", "set aside")
FOR = ("measures", "alerts", "runbooks", "business context", "owners", "volumes", "architecture", "catalogue",
       "capability", "other")
LEAD_KINDS = ("flow", "stage", "step", "part", "people step", "right outcome")
MERGED = f"{FL}/leads-merged.json"
DEFAULTS = {"first_look_chars": 60000, "first_look_code_lines": 4000, "first_look_readers": 12}
READER_SCALE = (1, 2, 4)  # how far a reader's share may grow, in text and in parts, before parts go unread
PDF_PAGES = 20  # the Read tool's limit of pages per call
TEXT = {".md", ".markdown", ".txt", ".rst", ".adoc", ".json", ".yaml", ".yml", ".csv", ".tsv", ".html", ".htm", ".xml",
        ".rules", ".conf", ".ini", ".toml", ".properties", ".log", ".sql", ".graphql", ".proto", ".j2", ".tpl", ""}
OFFICE = {".docx", ".xlsx", ".pptx"}
IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
POINTER = "Read {} and do exactly what it says. Reply with one line."
ALIVE_MINUTES = 40  # a first-look agent silent longer than this is taken as not alive (shown red on the run status page)


# ---------------------------------------------------------------- small helpers

def rows(path):
    p = pathlib.Path(path)
    if not p.is_file():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path, cols, data):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)


def settings(reg):
    s = dict(DEFAULTS)
    p = pathlib.Path(reg) / layout.SETTINGS
    try:
        got = json.loads(p.read_text(encoding="utf-8-sig")) if p.is_file() else {}
    except ValueError:
        got = {}
    for k in DEFAULTS:
        if got.get(k):
            s[k] = int(got[k])
    return s


def root_of(reg):
    """The workspace root a register sits in: the parent of its work folder, else its own parent."""
    reg = pathlib.Path(reg).resolve()
    return reg.parent.parent if reg.parent.name == "bfo-work" else reg.parent


def site_of(reg):
    reg = pathlib.Path(reg).resolve()
    return reg.parent if reg.parent.name == "bfo-work" else reg


def is_other(r):
    """A source row read by a source reader: not code, and not the run's own output (the survey, the fact base)."""
    kind = (r.get("kind") or "").strip().lower()
    if kind == "code":
        return False
    if kind == "tool output" and (r.get("found_by") or "").strip().lower() == "run":
        return False
    return bool((r.get("source_id") or "").strip())


def locations(r):
    return [x.strip() for x in (r.get("location") or "").split(";") if x.strip()]


def norm_text(t):
    """Text as the verbatim search compares it: tags stripped, entities decoded, whitespace runs collapsed."""
    t = re.sub(r"<(?:br|p|div|li|tr|h\d)[^>]*>", "\n", t or "", flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip().lower()


def flatten(text):
    """A connector's text, and every string inside it when it is JSON (its escapes undone)."""
    out = [text]
    try:
        d = json.loads(text)
    except (ValueError, TypeError):
        return out

    def walk(x):
        if isinstance(x, str):
            out.append(x)
            try:
                walk(json.loads(x))
            except (ValueError, TypeError):
                pass
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    return out


def pdf_pages(path):
    data = pathlib.Path(path).read_bytes()
    n = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", data))
    return max(n, 1)


def office_text(path):
    """A .docx, .xlsx or .pptx as text: the text runs of its XML parts, one paragraph a line."""
    path = pathlib.Path(path)
    out = []
    with zipfile.ZipFile(path) as z:
        names = sorted(n for n in z.namelist() if n.endswith(".xml") and (
            n.startswith("word/document") or n.startswith("ppt/slides/slide") or n == "xl/sharedStrings.xml"
            or n.startswith("xl/worksheets/sheet")))
        for n in names:
            xml = z.read(n).decode("utf-8", errors="replace")
            xml = re.sub(r"</(?:w:p|a:p|si|row)>", "\n", xml)
            for line in re.sub(r"<[^>]+>", "", xml).splitlines():
                line = html.unescape(line).strip()
                if line:
                    out.append(line)
    return "\n".join(out) + "\n"


def headings(lines):
    """Line numbers (1-based) where a top-level section starts: markdown `#` and `##` headings."""
    return [i + 1 for i, x in enumerate(lines) if re.match(r"^#{1,2}\s+\S", x)]


# ---------------------------------------------------------------- fetch: the owed parts and the mode

def _files_of(p):
    if p.is_dir():
        return sorted(f for f in p.rglob("*") if f.is_file() and not (set(f.relative_to(p).parts) & SKIP_DIRS))
    return [p] if p.is_file() else []


def _cut_text(reg, sid, f, rel, text, ceiling, n0):
    """Parts of one text file: whole when under the ceiling, else cut at its top headings, else by lines; a file of one
    very long line is cut by characters into converted files."""
    lines = text.splitlines()
    if len(text) <= ceiling:
        return [dict(path=rel, lines=f"1-{max(len(lines), 1)}", chars=len(text))]
    if len(lines) <= 2:  # one very long line: offset and limit cannot split it, so it is cut into files here
        out = []
        for k in range(0, len(text), ceiling):
            q = pathlib.Path(reg) / CONVERTED / sid / f"{f.name}.{k // ceiling + 1}.txt"
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_text(text[k:k + ceiling], encoding="utf-8")
            out.append(dict(path=q.resolve().as_posix(), lines="1-1", chars=len(text[k:k + ceiling]), original=rel))
        return out
    starts = [s for s in headings(lines) if s > 1]
    bounds, cur, size = [], 1, 0
    cuts = set(starts)
    for i, line in enumerate(lines, 1):
        if i in cuts and size >= ceiling // 2 and i > cur:
            bounds.append((cur, i - 1))
            cur, size = i, 0
        elif size + len(line) + 1 > ceiling and i > cur:
            bounds.append((cur, i - 1))
            cur, size = i, 0
        size += len(line) + 1
    bounds.append((cur, len(lines)))
    return [dict(path=rel, lines=f"{a}-{b}", chars=sum(len(x) + 1 for x in lines[a - 1:b])) for a, b in bounds]


def owed_parts(reg, ceiling=None):
    """[part row] for every other source of sources.csv, and [(source_id, why)] for the ones that resolve to nothing."""
    reg = pathlib.Path(reg).resolve()
    root = root_of(reg)
    ceiling = ceiling or settings(reg)["first_look_chars"]
    out, bad = [], []
    for r in rows(reg / "sources.csv"):
        if not is_other(r):
            continue
        sid = r["source_id"].strip()
        locs = locations(r)
        if not locs:
            bad.append((sid, "no location: say where it is (a path, or connector:<name>:<reference>)"))
            continue
        made = []
        for loc in locs:
            if loc.lower().startswith("connector:"):
                made.append(dict(route="connector", path=loc, chars=0))
                continue
            p = pathlib.Path(loc)
            p = p if p.is_absolute() else root / p
            files = _files_of(p)
            if not files:
                bad.append((sid, f"{loc} does not exist"))
                continue
            for f in files:
                rel = f.resolve().as_posix()
                ext = f.suffix.lower()
                if ext == ".pdf":
                    n = pdf_pages(f)
                    for a in range(1, n + 1, PDF_PAGES):
                        made.append(dict(route="file", path=rel, pages=f"{a}-{min(a + PDF_PAGES - 1, n)}", chars=0))
                elif ext in OFFICE:
                    try:
                        text = office_text(f)
                    except (zipfile.BadZipFile, OSError, KeyError):
                        bad.append((sid, f"{f.name} could not be converted to text"))
                        continue
                    q = reg / CONVERTED / sid / (f.name + ".txt")
                    q.parent.mkdir(parents=True, exist_ok=True)
                    q.write_text(text, encoding="utf-8")
                    for p2 in _cut_text(reg, sid, q, q.resolve().as_posix(), text, ceiling, len(made)):
                        p2.setdefault("original", rel)
                        made.append(dict(route="file", **p2))
                elif ext in IMAGES:
                    made.append(dict(route="file", path=rel, chars=0))
                else:
                    try:
                        text = f.read_text(encoding="utf-8")
                    except (UnicodeDecodeError, OSError):
                        bad.append((sid, f"{f.name} is not text and cannot be converted"))
                        continue
                    for p2 in _cut_text(reg, sid, f, rel, text, ceiling, len(made)):
                        made.append(dict(route="file", **p2))
        for i, m in enumerate(made, 1):
            m.update(source_id=sid, part="whole" if len(made) == 1 else str(i))
            out.append(m)
    return out, bad


def code_parts(reg):
    """One owed part per repository whose shallow read would be large: the survey's entry points of its services."""
    reg = pathlib.Path(reg).resolve()
    root = root_of(reg)
    by_repo, total = {}, 0
    for r in rows(reg / "survey.csv"):
        if (r.get("kind") or "").strip() != "service":
            continue
        for e in (r.get("entry_points") or "").split(";"):
            e = e.strip()
            if not e:
                continue
            m = re.match(r"^(.*?):(\d+)$", e)
            f, n = (m.group(1), int(m.group(2))) if m else (e, 0)
            total += n
            by_repo.setdefault((r.get("repository") or "").strip() or "code", []).append((root / f).resolve().as_posix())
    return by_repo, total


def window_start(reg):
    """The first look's mark's first `since`, read before anything refreshes it; else now."""
    try:
        import start
        site = site_of(reg)
        for p in (start.run_dir(site) / start.FIRST_LOOK, pathlib.Path(site) / start.FIRST_LOOK):
            if p.is_file():
                m = json.loads(p.read_text(encoding="utf-8"))
                if m.get("since"):
                    return datetime.datetime.fromisoformat(m["since"]).astimezone().isoformat(timespec="seconds")
    except (ImportError, OSError, ValueError):
        pass
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def refresh_mark(reg):
    """A first-look script ran: the mark's second sign of life. Its first `since` is never moved."""
    try:
        import start
        p = start.run_dir(site_of(reg)) / start.FIRST_LOOK
        m = json.loads(p.read_text(encoding="utf-8"))
        m["refreshed_epoch"] = time.time()
        p.write_text(json.dumps(m), encoding="utf-8")
    except (ImportError, OSError, ValueError):
        pass


def fetch(reg):
    """Write first-look/parts.csv and first-look/mode.json; return (mode, the sources that resolve to nothing)."""
    reg = pathlib.Path(reg).resolve()
    win = window_start(reg)  # before the refresh below, so the check's window starts no later than this step
    s = settings(reg)
    parts, bad = owed_parts(reg, s["first_look_chars"])
    by_repo, code_lines = code_parts(reg)
    code = "readers" if code_lines > s["first_look_code_lines"] else "lead"
    if code == "readers":
        for repo, files in sorted(by_repo.items()):
            parts.append(dict(source_id=f"code-{re.sub(r'[^A-Za-z0-9_.-]', '-', repo)}", part="whole", route="code",
                              path=repo, files="; ".join(files), chars=0))
    other_chars = sum(int(p.get("chars") or 0) for p in parts if p["route"] != "code")
    mode = "split" if other_chars > s["first_look_chars"] or code == "readers" else "single"
    over = []
    if mode == "split":
        parts, over = assign_bounded(parts, s["first_look_chars"], s["first_look_readers"])
    else:
        assign_readers(parts, s["first_look_chars"])
    write_rows(reg / PARTS, PART_COLS, parts)
    m = {"mode": mode, "code": code, "window_start": win, "other_chars": other_chars, "code_lines": code_lines,
         "parts": len(parts), "readers": len({p["reader"] for p in parts}) if mode == "split" else 0,
         "reader_cap": s["first_look_readers"],
         "over_budget": [{"source_id": p["source_id"], "part": part_key(p), "path": p.get("path") or "",
                          "chars": int(p.get("chars") or 0)} for p in over],
         "unresolved_sources": [{"source_id": a, "why": b} for a, b in bad],
         "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    (reg / MODE).write_text(json.dumps(m, indent=2), encoding="utf-8")
    refresh_mark(reg)
    return m, bad


def assign_bounded(parts, ceiling, cap):
    """(parts kept, parts over budget): readers never more than `cap`, so all launch at once. A reader's share grows
    (READER_SCALE) before any part is left; past that, readers are kept round-robin across sources, so every source
    keeps a reader before any source gets a second, and the rest is listed as not read."""
    for scale in READER_SCALE:
        assign_readers(parts, ceiling * scale, READER_PARTS * scale)
        if len({p["reader"] for p in parts}) <= cap:
            return parts, []
    by_source = {}
    for p in parts:
        by_source.setdefault(p["source_id"], {}).setdefault(p["reader"], []).append(p)
    queues = [list(rs.values()) for rs in by_source.values()]
    keep, i = [], 0
    while len(keep) < cap and any(queues):
        q = queues[i % len(queues)]
        if q:
            keep.append(q.pop(0))
        i += 1
    kept = [p for batch in keep for p in batch]
    ids = {id(p) for p in kept}
    return kept, [p for p in parts if id(p) not in ids]


def not_read_line(reg):
    """The brief's line on source parts the first look left unread to stay within its readers, or nothing."""
    over = (load_mode(reg) or {}).get("over_budget") or []
    if not over:
        return ""
    n = len({o["source_id"] for o in over})
    return (f"{len(over)} part{'s' if len(over) != 1 else ''} of {n} of the sources given "
            f"{'were' if len(over) != 1 else 'was'} not read in this first look, to keep it within its time; "
            "mapping reads them where a picked stage needs them.")


def assign_readers(parts, ceiling, most=READER_PARTS):
    """Each part's reader: a source's parts share one reader while their text stays under the ceiling and their count
    under `most`; a fetched or code part has its own."""
    by_source = {}
    for p in parts:
        by_source.setdefault(p["source_id"], []).append(p)
    for sid, ps in by_source.items():
        batches, cur, size = [], [], 0
        for p in ps:
            c = int(p.get("chars") or 0)
            if cur and (p["route"] != "file" or cur[0]["route"] != "file" or size + c > ceiling
                        or len(cur) >= most):
                batches.append(cur)
                cur, size = [], 0
            cur.append(p)
            size += c
        if cur:
            batches.append(cur)
        for n, b in enumerate(batches, 1):
            for p in b:
                p["reader"] = sid if len(batches) == 1 else f"{sid}-r{n}"


def load_mode(reg):
    try:
        return json.loads((pathlib.Path(reg) / MODE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def part_key(p):
    return p["source_id"] if p["part"] in ("whole", "") else f"{p['source_id']}-{p['part']}"


def reader_file(reg, p):
    return pathlib.Path(reg).resolve() / FL / f"{part_key(p)}.json"


def prompt_path(reg, p):
    """The prompt of the reader owed part `p`: one per reader, which may read several parts of one source."""
    key = (p.get("reader") or "").strip() or part_key(p)
    return pathlib.Path(reg).resolve() / layout.PROMPTS / READER_PROMPTS / f"read-{key}.md"


# ---------------------------------------------------------------- prompts

FORM = """{"source_id": "", "part": "", "what_it_is": "what the source turned out to be, in a phrase",
 "dated": "the date the source carries, or 'none shown'", "by": "who wrote or owns it, or 'not shown'",
 "leads": [{"kind": "flow | stage | step | part | people step | right outcome", "name": "", "says": "",
            "spot": "page and heading, panel title, ticket key, section", "quote": "the words there, copied exactly",
            "names_in_it": ["service, endpoint, queue, metric or table names, as written"]}],
 "holdings": [{"for": "measures | alerts | runbooks | business context | owners | volumes | architecture | catalogue | capability | other",
               "what": "", "spot": "", "quote": "", "names_in_it": []}],
 "not_read": [{"spot": "", "why": ""}],
 "reason": "only for a file with no leads, holdings or not_read rows: why there is nothing"}"""

NO_CONNECTOR = "no connector tool:"  # a reader's not_read `why` when none of its tools reaches the connector named

READER_TASK = """# Read one source of a business flow observability first look

The run maps the business flows of {system}. Before anything is read in depth, the person is briefed on the flows
found so far and picks where to start. You read one source, or some parts of one, and say what it suggests exists in
the business flows and what it holds for later phases, with the exact spot and the exact words for each. Judge
nothing: a source may be current, out of date or wrong, and the later phases judge it, not you.

- Source: {sid}. Services the code survey found (to recognise them by name): {services}.
- Your parts, each read in full and each with its own file, in this form (JSON):
{parts}

{form}

Rules: copy every `quote` and every `names_in_it` entry exactly as the source has it; a script finds each one in the
source. Read with the Read tool only (a PDF with `pages`), every line of what each part gives (in pieces if it is
long). Use no shell. Write nothing but the files above{copy}. A file with no leads and no holdings needs `what_it_is`
and a `not_read` row or a `reason`. Reply with one line naming each file you wrote."""


def _where(reg, p):
    if p["route"] == "connector":
        return (f"fetch it through the connector it names ({p['path']}); write what the connector returned, as it "
                f"returned it, to `{(reg / COPIES / p['source_id']).as_posix()}/` with the date fetched; if the "
                "connector says it saved the result to a file, Read that file in full. If none of your tools reaches "
                "that connector, fetch nothing: write the part's file with `what_it_is` 'not fetched' and one "
                f"`not_read` row whose `why` begins '{NO_CONNECTOR}' and names the connector")
    if p["route"] == "code":
        return f"repository {p['path']}: read these entry points in full: {p['files']}"
    rng = f" pages {p['pages']}" if p.get("pages") else f" lines {p['lines']}" if p.get("lines") else ""
    return f"read `{p['path']}`{rng}" + (f" (converted from `{p['original']}`)" if p.get("original") else "")


def prompts(reg):
    """Write one reader prompt per owed part (split mode) through write_prompt; return the pointer lines."""
    import judges
    reg = pathlib.Path(reg).resolve()
    m = load_mode(reg)
    if m is None:
        raise SystemExit("REFUSED: run first_look.py fetch first: no first-look/mode.json. Nothing written.")
    if m["mode"] != "split":
        return []
    absent = judges.agent_problem(reg, READER_TYPE, HERE / "agents" / f"{READER_TYPE}.md", "source reader")
    if absent:
        raise SystemExit(f"REFUSED: {absent}. Nothing written.")
    services = sorted({(r.get("service") or "").strip() for r in rows(reg / "survey.csv")
                       if (r.get("kind") or "").strip() == "service" and (r.get("service") or "").strip()})
    system = reg.name
    out, by_reader = [], {}
    for p in rows(reg / PARTS):
        by_reader.setdefault(prompt_path(reg, p), []).append(p)
    for path, ps in by_reader.items():
        sid = ps[0]["source_id"]
        listed = "\n".join(f"  - part {p['part']}: {_where(reg, p)}; write `{reader_file(reg, p).as_posix()}`"
                           for p in ps)
        copy = (f", and your copy of what you fetched under `{(reg / COPIES / sid).as_posix()}/`"
                if any(p["route"] == "connector" for p in ps) else "")
        text = READER_TASK.format(system=reg.name, sid=sid, parts=listed, services=", ".join(services) or "none",
                                  form=FORM, copy=copy)
        out.append(judges.write_prompt(path, text))
    return out


# ---------------------------------------------------------------- transcripts

class Tx:
    """One transcript as the check reads it: its first message, start, agent type, every tool call with its result."""

    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.prompt, self.first = None, None
        self.calls = []  # (id, name, input)
        self.results = {}  # id -> (text, is_error)
        with open(self.path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(d, dict):
                    continue
                if d.get("timestamp") and self.first is None:
                    self.first = _when(d["timestamp"])
                m = d.get("message")
                if not isinstance(m, dict):
                    continue
                c = m.get("content")
                if self.prompt is None and d.get("type") == "user":
                    self.prompt = c if isinstance(c, str) else " ".join(
                        b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")
                for b in c if isinstance(c, list) else []:
                    if not isinstance(b, dict):
                        continue
                    if d.get("type") == "assistant" and b.get("type") == "tool_use":
                        self.calls.append((b.get("id"), b.get("name") or "", b.get("input") or {}))
                    elif d.get("type") == "user" and b.get("type") == "tool_result":
                        rc = b.get("content")
                        text = rc if isinstance(rc, str) else "\n".join(
                            x.get("text", "") for x in rc or [] if isinstance(x, dict))
                        self.results[b.get("tool_use_id")] = (text, bool(b.get("is_error")))

    def ok(self, cid):
        r = self.results.get(cid)
        return r is not None and not r[1]

    def reads(self):
        """[(normalised path, (first, last) lines or None, pages (a, b) or None, result text)] of successful Reads."""
        out = []
        for cid, name, inp in self.calls:
            if name != "Read" or not inp.get("file_path") or not self.ok(cid):
                continue
            pg = None
            if inp.get("pages"):
                m = re.match(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*$", str(inp["pages"]))
                if m:
                    pg = (int(m.group(1)), int(m.group(2) or m.group(1)))
            first = int(inp.get("offset") or 1)
            span = None if pg else (first, first + int(inp.get("limit") or 2000) - 1)
            out.append((paths.norm(inp["file_path"]), span, pg, self.results[cid][0]))
        return out

    def writes(self):
        return [(paths.norm(inp.get("file_path") or ""), inp) for cid, name, inp in self.calls
                if name in ("Write", "Edit", "MultiEdit") and self.ok(cid)]

    def connector(self):
        """[(tool name, result text)] of every successful connector (MCP) call."""
        return [(name, self.results[cid][0]) for cid, name, inp in self.calls
                if name.startswith("mcp__") and self.ok(cid)]


def _when(text):
    try:
        d = datetime.datetime.fromisoformat(str(text).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.astimezone()


def transcripts(reg, given=None):
    import reading_check as rc
    folders = [pathlib.Path(t) for t in (given if isinstance(given, (list, tuple)) else [given])] if given else \
        rc.project_folders(reg)
    out = []
    for folder in folders:
        for f in sorted(pathlib.Path(folder).rglob("*.jsonl")):
            out.append(Tx(f))
    return out


def launched_on(tx, prompt):
    """True when transcript `tx` was launched on the pointer line of `prompt`, unchanged since a kit script wrote it."""
    import judges
    want = POINTER.format(pathlib.Path(prompt).resolve().as_posix())
    got = " ".join(str(tx.prompt or "").split())
    if paths.norm(got) != paths.norm(want):
        return False

    class S:
        path, prompt = tx.path, tx.prompt
    reg = pathlib.Path(prompt).resolve()
    reg = next(p for p in reg.parents if p.name == layout.PROMPTS).parent
    return judges.kit_prompt_problem(S, reg) is None


def agent_type(tx):
    p = tx.path
    if p.parent.name != "subagents":
        return None
    try:
        return json.loads(p.with_name(p.name[:-len(".jsonl")] + ".meta.json").read_text(encoding="utf-8")).get(
            "agentType")
    except (OSError, ValueError):
        return None


def strip_numbers(text):
    """A Read result's text without the line numbers the Read tool puts before each line."""
    return "\n".join(re.sub(r"^\s*\d+[\t→]", "", x) for x in (text or "").splitlines())


# ---------------------------------------------------------------- the check

def _covers(spans, a, b):
    """Lines (or pages) a..b all inside the spans taken together."""
    cur = a
    for x, y in sorted(s for s in spans if s):
        if x > cur:
            return False
        cur = max(cur, y + 1)
        if cur > b:
            return True
    return cur > b


def _form_problems(d, key):
    out = []
    if not isinstance(d, dict):
        return [f"{key}: not a JSON object in the form"]
    if not (d.get("what_it_is") or "").strip():
        out.append(f"{key}: what_it_is is empty")
    for sect in ("leads", "holdings"):
        for i, x in enumerate(d.get(sect) or [], 1):
            if not isinstance(x, dict) or not (x.get("spot") or "").strip() or not (x.get("quote") or "").strip():
                out.append(f"{key}: {sect} {i} has no spot or no quote")
            elif sect == "leads" and x.get("kind") not in LEAD_KINDS:
                out.append(f"{key}: lead {i} has kind {x.get('kind')!r}, not one of {', '.join(LEAD_KINDS)}")
            elif sect == "holdings" and x.get("for") not in FOR:
                out.append(f"{key}: holding {i} is for {x.get('for')!r}, not one of {', '.join(FOR)}")
    if not (d.get("leads") or d.get("holdings")) and not (d.get("not_read") or (d.get("reason") or "").strip()):
        out.append(f"{key}: an empty file needs a not_read row or a reason")
    return out


def _items(text):
    """The item count a connector reports (a search's `total`), or None."""
    for s in flatten(text):
        try:
            d = json.loads(s)
        except (ValueError, TypeError):
            continue
        if isinstance(d, dict) and isinstance(d.get("total"), int):
            return d["total"]
    return None


def _copy_items(folder):
    """Items in a reader's copy: the length of the first list found in each JSON file under it."""
    n = 0
    for f in sorted(pathlib.Path(folder).rglob("*.json")) if pathlib.Path(folder).is_dir() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(d, list):
            n += len(d)
        elif isinstance(d, dict):
            lst = next((v for v in d.values() if isinstance(v, list)), None)
            n += len(lst or [])
    return n


def _source_text(p, writer):
    """The text a reader's quotes are searched in: the file (its converted text), or for a PDF and an image what the
    writer's Reads of it returned."""
    path = pathlib.Path(p["path"])
    if p.get("pages") or path.suffix.lower() in IMAGES:
        return "\n".join(strip_numbers(t) for q, s, pg, t in writer.reads() if q == paths.norm(path))
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _connector_text(writer):
    """What the connector returned, from the writer's own transcript: each result, and for a result Claude Code saved to
    a file, the writer's Reads of that file (the union), with whether those Reads covered the whole file."""
    texts, saved_unread = [], []
    reads = writer.reads()
    for name, text in writer.connector():
        m = re.search(r"([A-Za-z]:[\\/][^\s\"']+|/[^\s\"']+)\.(?:txt|json)", text or "")
        saved = None
        if m and ("saved" in text.lower() or "tool-results" in text.lower()):
            saved = paths.norm(m.group(0))
        if saved:
            got = [(s, t) for q, s, pg, t in reads if q == saved]
            if not got:
                saved_unread.append(m.group(0))
                continue
            try:
                n = len(pathlib.Path(m.group(0)).read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                n = None
            if n is not None and not _covers([s for s, t in got], 1, max(n, 1)):
                saved_unread.append(m.group(0) + " (not read in full)")
                continue
            texts += [strip_numbers(t) for s, t in got]
        else:
            texts.append(text)
    return texts, saved_unread


def check(reg, given=None):
    """Every problem that stops the brief: owed parts not in the form, not read by their owed writer, quotes or names
    not in the source, partial fetches. An empty list when the first look's reading is proven."""
    reg = pathlib.Path(reg).resolve()
    m = load_mode(reg)
    if m is None:
        return ["the first look's fetch step has not run: python first_look.py fetch <register>"]
    parts = rows(reg / PARTS)
    since = _when(m.get("window_start")) or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    txs = [t for t in transcripts(reg, given) if t.first is not None and t.first >= since]
    lead_prompt = reg / layout.PROMPTS / LEAD_PROMPT
    leads = [t for t in txs if launched_on(t, lead_prompt)]
    out = []
    for p in parts:
        key = part_key(p)
        f = reader_file(reg, p)
        if not f.is_file():
            out.append(f"{key}: no reader's file ({f.name}) and no not-read row for it")
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            out.append(f"{key}: {f.name} is not JSON")
            continue
        probs = _form_problems(d, key)
        if probs:
            out += probs
            continue
        split = m["mode"] == "split"
        if split:
            launched = [t for t in txs if launched_on(t, prompt_path(reg, p))]
            owed = [t for t in launched if agent_type(t) == READER_TYPE]
            if launched and not owed:
                out.append(f"{key}: its reader was not a {READER_TYPE} agent")
                continue
        else:
            owed = leads
        copy_text = ""
        if not owed:
            out.append(f"{key}: no transcript of its owed {'reader' if split else 'first-look helper'} in this first "
                       "look (launched on the kit's prompt, after the first look began)")
            continue
        fn = paths.norm(f)
        writers = [t for t in txs if any(q == fn for q, _ in t.writes())]
        strangers = [t for t in writers if t not in owed]
        if strangers:
            out.append(f"{key}: {f.name} was written by {strangers[0].path.stem}, not by its owed "
                       f"{'reader' if split else 'first-look helper'}")
            continue
        mine = [t for t in owed if any(q == fn for q, _ in t.writes())]
        if not mine:
            out.append(f"{key}: its owed {'reader' if split else 'helper'} never wrote {f.name}")
            continue
        w = mine[-1]
        if split:
            mine_files = {paths.norm(reader_file(reg, x)) for x in parts if prompt_path(reg, x) == prompt_path(reg, p)}
            copies = paths.norm(reg / COPIES / p["source_id"])
            off = [q for q, _ in w.writes() if q not in mine_files and not q.startswith(copies + "/")]
            if off:
                out.append(f"{key}: its reader wrote outside its own file and copy: {off[0]}")
                continue
        texts = []
        if p["route"] == "connector":
            if any((r.get("why") or "").strip().lower().startswith(NO_CONNECTOR)
                   for r in d.get("not_read") or [] if isinstance(r, dict)):
                out.append(f"{key}: its reader has no tool for this connector: the lead copies the result Claude "
                           "Code saved, or the person exports the source")
                continue
            got, unread = _connector_text(w)
            if unread:
                out.append(f"{key}: connector result saved and not read: {unread[0]}")
                continue
            if not got:
                out.append(f"{key}: no connector result in its writer's transcript")
                continue
            texts = got
            copy = reg / COPIES / p["source_id"]
            want = next((n for n in (_items(t) for t in got) if n is not None), None)
            if want is not None and _copy_items(copy) < want:
                out.append(f"{key}: partial fetch: the connector reported {want} items and the copy holds "
                           f"{_copy_items(copy)}")
                continue
            copy_text = norm_text(" ".join(x.read_text(encoding="utf-8", errors="replace")
                                           for x in copy.rglob("*") if x.is_file()) if copy.is_dir() else "")
        elif p["route"] == "code":
            owed_files = [x.strip() for x in (p.get("files") or "").split(";") if x.strip()]
            spans = {}
            for q, s, pg, t in w.reads():
                spans.setdefault(q, []).append(s)
            unread = []
            for x in owed_files:
                try:
                    n = len(pathlib.Path(x).read_text(encoding="utf-8", errors="replace").splitlines())
                except OSError:
                    n = 1
                if not _covers(spans.get(paths.norm(x), []), 1, max(n, 1)):
                    unread.append(pathlib.Path(x).name)
            if unread:
                out.append(f"{key}: not read in full: {', '.join(unread)}")
                continue
            texts = [pathlib.Path(x).read_text(encoding="utf-8", errors="replace") for x in owed_files
                     if pathlib.Path(x).is_file()]
        else:
            q = paths.norm(p["path"])
            mine_reads = [(s, pg) for r, s, pg, t in w.reads() if r == q]
            if p.get("pages"):
                a, b = (int(x) for x in p["pages"].split("-"))
                ok = any(pg and pg[0] <= a and pg[1] >= b for s, pg in mine_reads) or _covers(
                    [pg for s, pg in mine_reads if pg], a, b)
            elif pathlib.Path(p["path"]).suffix.lower() in IMAGES:
                ok = bool(mine_reads)
            else:
                a, b = (int(x) for x in (p.get("lines") or "1-1").split("-"))
                ok = _covers([s for s, pg in mine_reads if s], a, b)
            if not ok:
                out.append(f"{key}: not read: {pathlib.Path(p['path']).name}"
                           + (f" pages {p['pages']}" if p.get("pages") else f" lines {p.get('lines')}"))
                continue
            texts = [_source_text(p, w)]
        hay = [norm_text(t) for x in texts for t in flatten(x)]
        missing = []
        for x in (d.get("leads") or []) + (d.get("holdings") or []):
            for s in [x.get("quote") or ""] + list(x.get("names_in_it") or []):
                n = norm_text(s)
                if n and not any(n in h for h in hay):
                    missing.append(s)
                elif n and p["route"] == "connector" and n not in copy_text:
                    missing.append(s + " (in what the connector returned, not in the reader's copy)")
        if missing:
            out.append(f"{key}: not found in the source: {missing[0]!r}" + (
                f" and {len(missing) - 1} more" if len(missing) > 1 else ""))
    return out


# ---------------------------------------------------------------- names, holdings, the brief

def reader_files(reg):
    reg = pathlib.Path(reg).resolve()
    out = []
    for p in rows(reg / PARTS):
        f = reader_file(reg, p)
        try:
            out.append((p, json.loads(f.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            continue
    return out


def code_text(reg):
    """Every text file of the code sources, lowercased, joined: what a name is searched in."""
    reg = pathlib.Path(reg).resolve()
    root = root_of(reg)
    chunks = []
    for r in rows(reg / "sources.csv"):
        if (r.get("kind") or "").strip().lower() != "code":
            continue
        locs = locations(r) or [x for x in [(r.get("repository") or "").strip()] if x]
        for loc in locs:
            p = pathlib.Path(loc)
            for f in _files_of(p if p.is_absolute() else root / p):
                if f.stat().st_size > 2_000_000:
                    continue
                try:
                    chunks.append(f.read_text(encoding="utf-8", errors="ignore").lower())
                except OSError:
                    pass
    return "\n".join(chunks)


def placed(reg):
    return {(r.get("name") or "").strip(): r for r in rows(pathlib.Path(reg) / PLACED)
            if (r.get("placed_as") or "").strip() in PLACEMENTS and (r.get("why") or "").strip()}


def unplaced(reg):
    """Names the sources mention that no code holds, and named sources wholly not read, with no placement."""
    reg = pathlib.Path(reg).resolve()
    names = []
    for p, d in reader_files(reg):
        for x in (d.get("leads") or []) + (d.get("holdings") or []):
            names += [n.strip() for n in x.get("names_in_it") or [] if n.strip()]
    code = code_text(reg)
    got = placed(reg)
    out = [n for n in dict.fromkeys(names) if n.lower() not in code and n not in got]
    m = load_mode(reg) or {}
    out += [f"source:{u['source_id']}" for u in m.get("unresolved_sources") or []
            if f"source:{u['source_id']}" not in got]
    return out


def holdings(reg, phase):
    return [(p["source_id"], x) for p, d in reader_files(reg) for x in d.get("holdings") or [] if x.get("for") == phase]


def brief_problems(reg, o):
    """What stops the capability brief, from the first look's reading: the check, the unplaced names, each flow's
    `seen_in`."""
    reg = pathlib.Path(reg).resolve()
    others = [r for r in rows(reg / "sources.csv") if is_other(r)]
    m = load_mode(reg)
    if m is None:
        return ["the first look's fetch step has not run (python first_look.py fetch <register>): every source the "
                "person gave that is not code is read by it"] if others else []
    out = [f"first look: {x}" for x in check(reg)]
    left = unplaced(reg)
    if left:
        out.append("first look: names the sources mention that no code holds, not yet placed (first-look/placed.csv: "
                   f"used, unresolved or set aside, with why): {', '.join(left[:8])}"
                   + (f" and {len(left) - 8} more" if len(left) > 8 else ""))
    ids = {(r.get("source_id") or "").strip() for r in rows(reg / "sources.csv")}
    for f in (o or {}).get("flows") or []:
        seen = f.get("seen_in") or []
        if not seen:
            out.append(f"flow {f.get('name', '?')}: seen_in is empty (the sources whose leads it rests on)")
        elif any(s not in ids for s in seen):
            out.append(f"flow {f.get('name', '?')}: seen_in names a source not in sources.csv")
    return out


def seen_said(reg, flow):
    """Where a flow was seen, in plain words: the code (a source generated from the code counts as the code), then
    what each other source turned out to be."""
    reg = pathlib.Path(reg).resolve()
    src = {(r.get("source_id") or "").strip(): r for r in rows(reg / "sources.csv")}
    what = {}
    for p, d in reader_files(reg):
        what.setdefault(p["source_id"], (d.get("what_it_is") or "").strip())
    code, other = False, []
    for s in flow.get("seen_in") or []:
        r = src.get(s) or {}
        if (r.get("kind") or "").strip().lower() == "code" or (r.get("derived_from") or "").strip():
            code = True
        elif what.get(s):
            other.append(what[s])
    parts = (["the code"] if code else []) + list(dict.fromkeys(other))
    if not parts:
        return ""
    if len(parts) == 1:
        return ("only in " if not code else "in ") + parts[0]
    return "in " + ", ".join(parts[:-1]) + " and " + parts[-1]


# ---------------------------------------------------------------- one command for the bookkeeping, one for the merge

def _tool(name):
    """A script of the mapping skill: beside this file, or in the mapping skill's folder beside this skill's."""
    for base in (HERE, HERE.parent / "bfo-mapping", HERE / "bfo-mapping"):
        if (base / name).exists():
            return base / name
    return None


def _code_rows(reg):
    return [r for r in rows(pathlib.Path(reg) / "sources.csv") if (r.get("kind") or "").strip().lower() == "code"]


def _survey(reg):
    """Run the survey over the code sources; return its printed summary (or why it did not run)."""
    import subprocess
    if not _code_rows(reg):
        return "survey: no code source listed"
    s = _tool("survey.py")
    p = subprocess.run([sys.executable, str(s), str(reg)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return (p.stdout or "").strip() or (p.stderr or "").strip()


CODE_READER_NOT_RUN = layout.CODE_READER_NOTE
CODE_READER_SECONDS = 90  # run-settings.json `code_reader_seconds`; well inside one foreground command


def _usable(x):
    import shutil
    return x and (os.path.isfile(x) and x or shutil.which(x))


def _run_bounded(cmd, out, err, cwd, env, limit):
    """Run cmd in the foreground; its exit code, or None when it ran past `limit` seconds, in which case it and every
    program it started are stopped (semgrep runs as the reader's child and would otherwise keep scanning)."""
    import signal
    import subprocess
    if os.name == "nt":  # shares the caller's console, so no window opens; taskkill /T needs no process group
        p = subprocess.Popen(cmd, stdout=out, stderr=err, cwd=cwd, env=env)
    else:
        p = subprocess.Popen(cmd, stdout=out, stderr=err, cwd=cwd, env=env, start_new_session=True)
    try:
        return p.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
        else:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
        p.kill()
        p.wait()
        return None


def _semgrep():
    """semgrep's full path: where the code reader itself looks (DFO_SEMGREP, PATH, this Python's scripts folder), then
    the user scripts folder `pip install --user` fills, then the files the installed package lists. None when it is
    not installed for this Python."""
    import importlib.util
    import sysconfig

    usable = _usable
    loc = _tool("fact-extractor/semgrep_bin.py")
    if loc is not None:
        spec = importlib.util.spec_from_file_location("semgrep_bin", loc)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        found = usable(mod.resolve())
        if found:
            return found
    names = ("semgrep.exe", "semgrep") if os.name == "nt" else ("semgrep",)
    for scheme in (f"{os.name}_user", "posix_user", "nt_user"):
        try:
            folder = sysconfig.get_path("scripts", scheme)
        except (KeyError, TypeError, ValueError):
            continue
        for n in names:
            if folder and os.path.isfile(os.path.join(folder, n)):
                return os.path.join(folder, n)
    try:
        import importlib.metadata
        for f in importlib.metadata.distribution("semgrep").files or []:
            if pathlib.PurePath(str(f)).name in names:
                p = pathlib.Path(f.locate()).resolve()
                if p.is_file():
                    return str(p)
    except Exception:
        pass
    return None


def code_reader_line(reg):
    """The brief's line on a code reader that did not run, or that the person chose to go on without, or nothing."""
    p = pathlib.Path(reg) / CODE_READER_NOT_RUN
    return p.read_text(encoding="utf-8").strip() if p.is_file() else ""


READER_STOP = "code-reader-held.json"  # the first look held for the person: its reason, remedy and choices; the
# watchdog and the run status page read run_state's stop.json, written beside it
HELD_NEXT = ("Answer the run's last message in its chat; it lists your choices: fix it and try again, go on without "
             "it, or stop.")
READER_SKIPPED = layout.CODE_READER_SKIPPED  # the person chose to go on without the code reader: {"reason", "words"}
# What going on without the code reader costs, as the kit runs without fact-base.json: the reading plan and the
# path a reader follows take only the lines the steps cite (path_reading.py, fast_map.py plan), not the places the
# code receives, calls and stores; and no check compares the map with that list (fast_map.gaps, reading_check leads).
WITHOUT_COST = ("the readers get no list of where the code receives, calls and stores, so they read more of each "
                "service and take longer, and no check compares the map with that list, so a call they miss is not "
                "flagged")
HELD_LEAD = "The first look is held: the tool that lists the calls and messages in the code would not run on this computer"


def reader_held(reg):
    p = pathlib.Path(reg) / READER_STOP
    try:
        got = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except ValueError:
        return None
    return got if isinstance(got, dict) and got.get("stop") == "code reader" else None


def reader_skipped(reg):
    p = pathlib.Path(reg) / READER_SKIPPED
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except ValueError:
        return None


MORE_TIME = 3  # "try again with more time" gives the code reader this many times as long, applied by the kit


def _hold(reg, reason, remedy, said, more_time=False):
    """Stop the first look for the person: stop.json, and the numbered choices in plain words. Returns the line.
    `reason` is one plain sentence of the kit's own; what the tool printed goes to fact-extractor.log only. A reader
    stopped for time is offered more time as a choice the kit applies itself, never a file to edit."""
    import datetime
    reg = pathlib.Path(reg)
    first = ("1. Try again with more time: I give it longer and run the first look again." if more_time else
             f"1. Fix it and try again: {remedy}. Then tell me, and I run the first look again.")
    text = "\n".join([
        f"{HELD_LEAD}: {reason}. What would you like to do?", "", first,
        f"2. Go on without it: {WITHOUT_COST}.",
        "3. Stop here.", "",
        "Answer with the number, or in your own words."])
    (reg / READER_STOP).write_text(json.dumps({
        "stop": "code reader", "reason": reason, "remedy": remedy, "message": text, "more_time": more_time,
        "choices": ["retry", "without", "stop"], "at": datetime.datetime.now().astimezone().isoformat(
            timespec="seconds")}, indent=1), encoding="utf-8")
    import run_state
    run_state.record_stop(reg, f"{HELD_LEAD}: {reason}.", HELD_NEXT, code="code-reader-held")
    (reg / "fact-base.json").unlink(missing_ok=True)
    (reg / "fact-extractor.log").write_text(said + "\n", encoding="utf-8")
    return said + " HELD for the person (stop.json)."


ANSWERS = {"1": "retry", "2": "without", "3": "stop", "retry": "retry", "without": "without", "stop": "stop"}


def answer(reg, choice, words, test=False):
    """Record the person's answer to the held first look and act on it; returns what to do next."""
    import case
    reg = pathlib.Path(reg).resolve()
    held = reader_held(reg)
    if held is None:
        return "REFUSED: the first look is not held for the code reader. Nothing recorded."
    kind = ANSWERS.get(str(choice).strip().lower())
    if kind is None:
        return "REFUSED: the answer is 1, 2 or 3 (retry, without, stop). Nothing recorded."
    if not (words or "").strip():
        return "REFUSED: --words is required: the person's answer, word for word. Nothing recorded."
    case.decide(reg, "code reader", held.get("message", ""), words, "the person", test=test, choice=kind,
                reason=held.get("reason", ""))
    import run_state
    if kind == "stop":
        held["stopped"] = True
        (reg / READER_STOP).write_text(json.dumps(held, indent=1), encoding="utf-8")
        run_state.record_stop(reg, "The run stopped at the first look, as you chose: the tool that lists the calls and "
                              "messages in the code would not run.", run_state.RESUME, code="first-look-stopped")
        return "STOPPED: the run stops here, as the person chose."
    if kind == "without":
        (reg / READER_SKIPPED).write_text(json.dumps({"reason": held.get("reason", ""), "words": words},
                                                     indent=1), encoding="utf-8")
    if kind == "retry" and held.get("more_time"):  # the kit gives the code reader longer itself
        import settings
        s = settings.load(reg)
        given = int(s.get("code_reader_seconds") or CODE_READER_SECONDS)
        p = reg / layout.SETTINGS
        got = json.loads(p.read_text(encoding="utf-8-sig")) if p.is_file() else {}
        got["code_reader_seconds"] = given * MORE_TIME
        p.write_text(json.dumps(got, indent=1) + "\n", encoding="utf-8")
    (reg / READER_STOP).unlink(missing_ok=True)
    run_state.clear_stop(reg)
    return f'NEXT: run python "{HERE / "first_look.py"}" prepare "{reg}" again.'


def _facts(reg):
    """Run the code reader over the surveyed services, its service map from survey.csv, reading only the repository
    folders of sources.csv's code rows (citations stay relative to the code root), in the foreground within
    `code_reader_seconds`, with semgrep's own folder first on its PATH; write fact-base.json (only when it finished),
    its errors to fact-extractor.log; return a one-line summary. When it cannot run or does not finish, the first look
    is held for the person (_hold); once they chose to go on without it, it is not run and the note says so."""
    import subprocess
    import settings
    reg = pathlib.Path(reg).resolve()
    run = _tool("fact-extractor/run.py")
    svc = [r for r in rows(reg / "survey.csv") if (r.get("kind") or "").strip() == "service"]
    if run is None or not svc:
        return "code reader: nothing to read" if svc else "code reader: no surveyed service"
    root = layout.code_root(reg) if hasattr(layout, "code_root") else root_of(reg)
    pairs = [f"{r['path']}={r['service']}" for r in svc if (r.get("path") or "").strip()]
    marker, base, log = reg / CODE_READER_NOT_RUN, reg / "fact-base.json", reg / "fact-extractor.log"
    skipped = reader_skipped(reg)
    if skipped is not None:
        marker.write_text(f"Code reader not used, as you chose: {skipped.get('reason', '')}. Without it, "
                          f"{WITHOUT_COST}.\n", encoding="utf-8")
        base.unlink(missing_ok=True)
        return f"code reader: not used, by the person's choice ({skipped.get('reason', '')})"
    marker.unlink(missing_ok=True)
    override = os.environ.get("DFO_SEMGREP")
    if override and not _usable(override):
        return _hold(reg, f"the setting DFO_SEMGREP names {override}, which is not there",
                     "correct DFO_SEMGREP to the full path of the semgrep program, or remove it",
                     f"code reader: NOT RUN: DFO_SEMGREP names {override}, which does not exist.")
    exe = _semgrep()
    if exe is None:
        fix = f'run "{sys.executable}" -m pip install semgrep'
        return _hold(reg, "semgrep is not installed for this Python", fix,
                     f"code reader: NOT RUN: semgrep is not installed for {sys.executable} (looked in DFO_SEMGREP, "
                     "PATH, this Python's scripts folder, the user scripts folder and the package's own files).")
    # semgrep's wrapper starts pysemgrep by name from PATH: its own folder (often a scripts folder not on PATH) first
    folder = os.path.dirname(os.path.abspath(exe)) if os.path.isfile(exe) else ""
    path = os.pathsep.join(x for x in (folder, os.environ.get("PATH", "")) if x)
    env = dict(os.environ, DFO_SEMGREP=exe, PATH=path)
    import shutil
    if folder and not shutil.which("pysemgrep", path=path):
        fix = f'run "{sys.executable}" -m pip install --force-reinstall semgrep'
        return _hold(reg, f"semgrep is installed in {folder} but its companion program pysemgrep is not", fix,
                     f"code reader: NOT RUN: {exe} is installed but pysemgrep is in neither its folder nor on PATH.")
    limit = int(settings.load(reg).get("code_reader_seconds") or CODE_READER_SECONDS)
    part = reg / "fact-base.json.part"
    with open(part, "w", encoding="utf-8") as out, open(log, "w", encoding="utf-8") as err:
        targets = [str(p) for p in layout.code_folders(reg).values()]
        code = _run_bounded([sys.executable, str(run), str(root), "--service-map", *pairs,
                             *(["--targets", *targets] if targets else [])], out, err, str(root), env, limit)
    if code is None:
        part.unlink(missing_ok=True)
        return _hold(reg, f"it was stopped after {limit} seconds, before it finished",
                     "give it more time", f"code reader: stopped after {limit} s over {len(pairs)} service(s), it and "
                     "every program it started.", more_time=True)
    if code != 0:
        part.unlink(missing_ok=True)
        said = log.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-1:] if log.is_file() else []
        last = (said[0] if said else "no message")[:200]
        return _hold(reg, "it stopped with an error, which is kept in the run's log",
                     f"see what it said in {log}, put that right (often: run \"{sys.executable}\" -m pip install "
                     "--force-reinstall semgrep)",
                     f"code reader: failed over {len(pairs)} service(s): {last}")
    part.replace(base)
    contract = _tool("fact-extractor/contract.py")
    said = ""
    if contract is not None:
        c = subprocess.run([sys.executable, str(contract), str(root), str(reg / "fact-base.json")], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", cwd=str(root))
        with open(reg / "fact-extractor.log", "a", encoding="utf-8") as f:
            f.write((c.stdout or "") + (c.stderr or ""))
        said = (" Its contract check passed; its reach is in fact-extractor.log." if c.returncode == 0 else
                " Its contract check failed: see fact-extractor.log.")
    return f"code reader: ran over {len(pairs)} service(s).{said}"


def prepare(reg):
    """The first look's bookkeeping in one command: survey, the checks before the code reader (preflight.py), code
    reader, fetch, reader prompts. Return what to print:
    the summary and, in split mode, every reader's pointer line, all to be launched in one message. A code reader
    that cannot run holds the first look here, for the person (STOP and the message)."""
    reg = pathlib.Path(reg).resolve()
    import preflight
    out = [_survey(reg), preflight.before_code_reader(reg)]
    held = preflight.held(reg) or reader_held(reg)
    if held is None:
        out.append(_facts(reg))
        held = reader_held(reg)
    if held is not None:
        out.append("STOP: the first look is held for the person. End here: your final reply is exactly the text after "
                   "MESSAGE:, and nothing else; the session that started you puts it to the person and records their "
                   "answer.")
        out.append("MESSAGE:\n" + held["message"])
        return "\n".join(x for x in out if x)
    m, bad = fetch(reg)
    out.append(f"MODE: {m['mode']} ({m['parts']} owed part(s); other sources {m['other_chars']} characters; code read "
               f"by the {m['code']})")
    for sid, why in bad:
        out.append(f"NOT READABLE: {sid}: {why} (merge places it as unresolved; the brief lists it).")
    if m.get("over_budget"):
        out.append("OVER BUDGET: " + not_read_line(reg))
    if m["mode"] == "split":
        lines = prompts(reg)
        refresh_mark(reg)
        out.append(f"LAUNCH: start all {len(lines)} source readers below in one message, each line as its whole prompt, "
                   f"as a {READER_TYPE} subagent, in the foreground; then run check, names and merge.")
        out += lines
    else:
        out.append(f"NEXT: read each owed part in {PARTS} yourself, with the Read tool only, and write its file in {FL}/ "
                   "in the form; then run check, names and merge.")
    return "\n".join(x for x in out if x)


def _key(name):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).split())


def merge(reg):
    """Merge every reader's leads by kind and name into first-look/leads-merged.json (each with the sources it was
    seen in and the spots), and place each name no code holds as unresolved, with where it was seen, unless already
    placed. Returns the merged record."""
    reg = pathlib.Path(reg).resolve()
    groups, where = {}, {}
    for p, d in reader_files(reg):
        sid = p["source_id"]
        for x in d.get("leads") or []:
            k = (x.get("kind") or "", _key(x.get("name")))
            g = groups.setdefault(k, {"kind": k[0], "name": (x.get("name") or "").strip(), "seen_in": [], "spots": []})
            if sid not in g["seen_in"]:
                g["seen_in"].append(sid)
            g["spots"].append({"source_id": sid, "spot": x.get("spot") or "", "says": x.get("says") or ""})
        for x in (d.get("leads") or []) + (d.get("holdings") or []):
            for n in x.get("names_in_it") or []:
                where.setdefault(n.strip(), f"{sid} at {x.get('spot') or 'its text'}")
    merged = {"flows": [g for g in groups.values() if g["kind"] == "flow"],
              "stages": [g for g in groups.values() if g["kind"] == "stage"],
              "steps": [g for g in groups.values() if g["kind"] in ("step", "people step")],
              "parts": [g for g in groups.values() if g["kind"] == "part"],
              "right_outcomes": [g for g in groups.values() if g["kind"] == "right outcome"],
              "holdings": {ph: len(holdings(reg, ph)) for ph in FOR if holdings(reg, ph)}}
    (reg / MERGED).parent.mkdir(parents=True, exist_ok=True)
    (reg / MERGED).write_text(json.dumps(merged, indent=1), encoding="utf-8")
    have = {(r.get("name") or "").strip(): r for r in rows(reg / PLACED)}
    bad = {f"source:{u['source_id']}": u.get("why") or "" for u in (load_mode(reg) or {}).get("unresolved_sources") or []}
    for n in unplaced(reg):
        why = (f"not readable: {bad[n]}" if n in bad else
               f"named in {where.get(n, 'a source')}; no code in the workspace holds it")
        have[n] = {"name": n, "placed_as": "unresolved", "why": why}
    write_rows(reg / PLACED, PLACED_COLS, list(have.values()))
    return merged


# ---------------------------------------------------------------- liveness, for the first-look mark

def agents_alive(site, given=None, run=None):
    """True while the first-look helper or a source reader of a register in this work folder is working: launched on
    a first-look prompt, not finished, and written within ALIVE_MINUTES. The main session never counts."""
    import judges
    import reading_check as rc
    site = pathlib.Path(site).resolve()
    folders = [pathlib.Path(t) for t in (given if isinstance(given, (list, tuple)) else [given])] if given else \
        rc.project_folders(site)
    pat = re.compile(re.escape(POINTER).replace(re.escape("{}"), "(.+?)"))
    now = time.time()
    for folder in folders:
        for f in pathlib.Path(folder).rglob("*.jsonl"):
            if f.parent.name != "subagents" or now - f.stat().st_mtime > ALIVE_MINUTES * 60:
                continue
            first = judges.session_of(f)
            m = pat.fullmatch(" ".join(str(first[0] or "").split()))
            if not m:
                continue
            target = paths.norm(m.group(1))
            if not target.startswith(paths.norm(site) + "/"):
                continue
            if f"/{layout.PROMPTS}/{READER_PROMPTS}/" not in target and not target.endswith(f"/{LEAD_PROMPT}"):
                continue
            if not first[2]:
                return True
    return False


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = list(argv)
    if args[:1] == ["answer"]:  # answer <register> <1|2|3> --words "<their words>" [--test]
        test = "--test" in args
        args = [a for a in args if a != "--test"]
        words = args[args.index("--words") + 1] if "--words" in args and args.index("--words") + 1 < len(args) else ""
        if len(args) < 3:
            print('usage: first_look.py answer <register> <1|2|3> --words "<their words>"', file=sys.stderr)
            return 2
        import run_lock
        run_lock.guard(pathlib.Path(args[1]).resolve())
        said = answer(args[1], args[2], words, test=test)
        print(said, file=sys.stderr if said.startswith("REFUSED") else sys.stdout)
        return 2 if said.startswith("REFUSED") else 0
    if len(args) < 2 or args[0] not in ("prepare", "fetch", "prompts", "check", "names", "merge", "holdings"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, reg = args[0], pathlib.Path(args[1]).resolve()
    if not (reg / "sources.csv").is_file():
        print(f"REFUSED: {reg} holds no sources.csv. Nothing written.", file=sys.stderr)
        return 2
    if cmd in ("prepare", "fetch", "prompts", "merge"):  # the register is written by one run at a time
        import run_lock
        run_lock.guard(reg)
    if cmd == "prepare":
        print(prepare(reg))
        return 0
    if cmd == "merge":
        m = merge(reg)
        left = unplaced(reg)
        print(f"MERGED: {len(m['flows'])} flow(s), {len(m['stages'])} stage(s), {len(m['steps'])} step(s), "
              f"{len(m['parts'])} part(s) in {MERGED}, each with the sources it was seen in. Names no code holds are "
              f"placed as unresolved in {PLACED}: change any to used or set aside where you know better. Write "
              "orientation.json from the merged leads (each flow's seen_in from them), then brief.py capability.")
        if left:
            print("UNPLACED: " + ", ".join(left))
            return 2
        return 0
    if cmd == "fetch":
        m, bad = fetch(reg)
        print(f"MODE: {m['mode']} (other sources {m['other_chars']} characters; code read by the {m['code']}); "
              f"{m['parts']} owed part(s) in {PARTS}")
        for sid, why in bad:
            print(f"NOT READABLE: {sid}: {why}. Put it to the person at the brief (placed.csv: source:{sid}, "
                  "unresolved), or fix its location and fetch again.")
        if m["mode"] == "split":
            print("NEXT: python first_look.py prompts <register>, then start every bfo-source-reader it prints in one "
                  "message, in the foreground (prepare does fetch and prompts together).")
        else:
            print(f"NEXT: read each owed part in {PARTS} yourself, with the Read tool only, and write its file in "
                  f"{FL}/ in the form; then python first_look.py check <register>.")
        return 0
    if cmd == "prompts":
        lines = prompts(reg)
        refresh_mark(reg)
        print(f"{len(lines)} source reader(s): launch every line below in one message, each as its whole prompt, as a "
              f"{READER_TYPE} subagent, in the foreground.")
        print("\n".join(lines))
        return 0
    if cmd == "check":
        given = None
        if "--transcripts" in args:
            given = args[args.index("--transcripts") + 1]
        probs = check(reg, given)
        refresh_mark(reg)
        if probs:
            print("NOT PROVEN:\n" + "\n".join(f"- {x}" for x in probs))
            return 2
        print("PROVEN: every owed part was read by its owed writer, and every quote and name is in its source.")
        return 0
    if cmd == "names":
        left = unplaced(reg)
        refresh_mark(reg)
        if left:
            print("UNPLACED (place each in first-look/placed.csv: name,placed_as,why; placed_as used, unresolved or "
                  "set aside):\n" + "\n".join(f"- {x}" for x in left))
            return 2
        print("PLACED: every name the sources mention is in the code or placed.")
        return 0
    phase = args[args.index("--for") + 1] if "--for" in args else ""
    if phase not in FOR:
        print(f"REFUSED: --for one of {', '.join(FOR)}.", file=sys.stderr)
        return 2
    for sid, x in holdings(reg, phase):
        print(f"- {sid} at {x.get('spot')}: {x.get('what')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
