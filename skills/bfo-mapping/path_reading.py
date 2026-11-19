"""Path reading: a reading unit of a flow read by stage reads the path of the stages taken past mapped only, not every
line (run-settings.json `reading`: `path`, the default; `full` reads every line of every unit, as before).

The starting points of each unit are derived by script from the register alone, never chosen by hand:
1. every file:line the stages' moves cite, in any cell of lifecycle.csv;
2. every operation a move's travels_by names after a service, found in the code reader's inbound facts, else by a
   definition-looking line in the service's code;
3. every route the moves name (`METHOD /path` or `/api/...`), as the code reader's inbound route facts hold it, or as
   text in the named services' code and configuration (its callers, such as a page's request, and its handler);
4. every page or screen the moves come through (a template file such as `client_order_list.html` named in a move),
   located by file name in any unit;
5. every store the unit's code reads or writes (the code reader's durable read and write facts), so the stores and data
   files the path's operations open are read.
A unit of a service read for the stages with none of these starts from its inbound operations (the code reader's
inbound facts in its paths). Usage: python path_reading.py <register folder> [stage id ...]  (prints the JSON)"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import go  # noqa: E402
import register_layout as layout  # noqa: E402
import settings  # noqa: E402
import tables  # noqa: E402

INBOUND = {"inbound_route", "grpc_method", "message_consumer", "message_subscription", "event_binding"}
STORES = {"durable_read", "durable_write"}
CODE = {".go", ".cs", ".py", ".js", ".ts", ".java", ".kt", ".rb", ".php"}
TEXT = CODE | {".html", ".cshtml", ".jsx", ".tsx", ".vue", ".yml", ".yaml", ".properties", ".json", ".xml", ".conf"}
PAGE = re.compile(r"([\w\-./]+\.(?:html|htm|cshtml|razor|jsp|jsx|tsx|vue|aspx|ejs|hbs|mustache|twig|erb))\b", re.I)
CITE = re.compile(r"([\w.\-/]+\.[A-Za-z]{1,6}):(\d+(?:-\d+)?(?:\s*,\s*\d+(?:-\d+)?)*)")
ROUTE = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+(/[\w/{}.\-]*)")
API = re.compile(r"(/api/[\w/.\-]+)")
OPS = re.compile(r"\b([a-z][\w-]*)\s+((?:GET|POST|PUT|DELETE|PATCH)\s+/[\w/{}.\-]*|[A-Z][A-Za-z0-9]+)\b")
OFF_PATH = "off this stage's path"


def reading(reg):
    """`path` when the flow worked now is read by stage (go.BY_STAGE) and run-settings.json `reading` is not `full`;
    else `full`."""
    s = go.load(reg) or {}
    if not s.get(go.BY_STAGE):
        return "full"
    return "full" if str(settings.load(reg).get("reading") or "path").strip().lower() == "full" else "path"


def _files(ws, paths, exts):
    for p in paths:
        base = ws / p
        files = [base] if base.is_file() else [x for x in base.rglob("*") if x.is_file()] if base.is_dir() else []
        for x in files:
            if x.suffix.lower() in exts:
                yield x


def starting_points(reg, ws, stages=None):
    """{unit: {"lines": [file:span], "operations": [{"operation", "at"}], "fallback": bool}} for the units of the
    services the flow reads (go.services_read) and any unit a cited line falls in, for `stages` (default: the stages
    the flow worked now takes past mapped only)."""
    reg, ws = pathlib.Path(reg), pathlib.Path(ws)
    s = go.load(reg) or {}
    stages = set(stages if stages is not None else go.picked_stages(s))
    steps = [r for r in tables.dicts(reg / "steps.csv") if (r.get("stage") or "").strip() in stages]
    mids = {m for st in steps for m in re.findall(r"\bL\d+\b", st.get("source") or "")}
    moves = [r for r in tables.dicts(reg / "lifecycle.csv") if (r.get("move_id") or "").strip() in mids]
    units = [r for r in tables.dicts(reg / layout.UNITS_CSV) if (r.get("unit") or "").strip() not in ("", "flow")]
    upaths = {u["unit"].strip(): [p.strip().rstrip("/") for p in (u.get("paths") or "").split(";") if p.strip()]
              for u in units}
    dep = {u["unit"].strip(): ((u.get("deployable") or "").strip() or u["unit"].strip()).lower() for u in units}
    facts = []
    p = reg / "fact-base.json"
    if p.is_file():
        try:
            facts = json.loads(p.read_text(encoding="utf-8")).get("facts") or []
        except ValueError:
            facts = []

    def unit_of(path):
        path = path.replace("\\", "/")
        best = None
        for u, ps in upaths.items():
            for q in ps:
                if q and (path == q or path.startswith(q + "/")) and (best is None or len(q) > best[1]):
                    best = (u, len(q))
        return best[0] if best else None

    out = {u: {"lines": [], "operations": [], "fallback": False} for u in upaths}

    def add(u, op, at):
        if u and {"operation": op, "at": at} not in out[u]["operations"]:
            out[u]["operations"].append({"operation": op, "at": at})

    text = " ".join(v or "" for m in moves for v in m.values())
    for f, spans in CITE.findall(text):  # 1. the lines the moves cite
        u = unit_of(f)
        if u:
            for sp in re.split(r"\s*,\s*", spans):
                if f"{f}:{sp}" not in out[u]["lines"]:
                    out[u]["lines"].append(f"{f}:{sp}")
    read = go.services_read(reg, s)
    read = set(dep.values()) if read is None else read
    low = text.lower()
    named = {d for d in set(dep.values()) if re.search(rf"\b{re.escape(d)}\b", low) or d.replace("-", " ") in low}
    for m in moves:  # 2. operations travels_by names after a service
        for d, op in OPS.findall(m.get("travels_by") or ""):
            d = d.lower()
            if d not in dep.values():
                continue
            word = op.split()[-1].lower()
            hits = [f"{f['file']}:{f['line']}" for f in facts if f.get("kind") in INBOUND
                    and (f.get("service") or "").lower() == d and word in (f.get("evidence") or "").lower()]
            if not hits:
                for u in [u for u, x in dep.items() if x == d]:
                    for x in _files(ws, upaths[u], CODE):
                        for i, line in enumerate(x.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                            if re.search(rf"\b{re.escape(op.split()[-1])}\s*\(", line) and re.search(
                                    r"\b(def|func|public|async|function|override|Task|static)\b", line):
                                hits.append(f"{x.relative_to(ws).as_posix()}:{i}")
            for h in hits:
                add(unit_of(h.rsplit(":", 1)[0]), f"{d} {op}", h)
    routes = {f"{a} {b}" for a, b in ROUTE.findall(text)} | {r for r in API.findall(text)}
    for f in facts:  # 3. routes the moves name, as the code reader's route facts hold them
        if f.get("kind") == "inbound_route":
            ev = f.get("evidence") or ""
            for r in routes:
                path = r.split()[-1]
                if path and len(path) > 1 and (path in ev or path.rstrip("/") + '"' in ev):
                    add(unit_of(f.get("file") or ""), f"route {r}", f"{f['file']}:{f['line']}")
    for r in sorted(r for r in routes if r.startswith("/api/")):  # 3b. an /api route as text, callers and handler
        pre = r.rsplit("/", 1)[0]
        for u in [u for u, d in dep.items() if d in named]:
            for x in _files(ws, upaths[u], TEXT):
                for i, line in enumerate(x.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                    if r in line or pre + '"' in line or pre + "/**" in line:
                        add(u, f"route {r}", f"{x.relative_to(ws).as_posix()}:{i}")
    for page in sorted(set(PAGE.findall(text))):  # 4. the pages and screens the moves come through
        name = pathlib.PurePosixPath(page).name.lower()
        for u in upaths:
            for x in _files(ws, upaths[u], TEXT):
                if x.name.lower() == name:
                    add(u, f"page {name}", f"{x.relative_to(ws).as_posix()}:1")
    for u, d in dep.items():  # 5. the stores the unit's code opens, for a unit the flow reads
        if d not in read:
            continue
        for f in facts:
            if f.get("kind") in STORES and not f.get("in_test") and unit_of(f.get("file") or "") == u:
                add(u, f"store {f.get('kind')}", f"{f['file']}:{f['line']}")
    res = {}
    for u, d in dep.items():
        e = out[u]
        if d not in read and not e["lines"]:
            continue
        if not e["lines"] and not e["operations"]:
            e["fallback"] = True
            for f in facts:
                if f.get("kind") in INBOUND and not f.get("in_test") and unit_of(f.get("file") or "") == u:
                    add(u, f"{f.get('service')} {f.get('kind')}", f"{f['file']}:{f['line']}")
        res[u] = e
    return res


def path_block(reg, unit, ws, entries=None):
    """The reader prompt's block for path reading, or [] when the unit is read in full."""
    if reading(reg) != "path":
        return []
    s = go.load(reg) or {}
    stages = go.picked_stages(s)
    steps = [r["step"] for r in tables.dicts(pathlib.Path(reg) / "steps.csv") if (r.get("stage") or "") in stages]
    e = (entries if entries is not None else starting_points(reg, ws)).get(unit) or {"lines": [], "operations": [],
                                                                                    "fallback": True}
    starts = [f"- cited line: `{x}`" for x in e["lines"]] + [f"- {o['operation']}: `{o['at']}`" for o in e["operations"]]
    if e.get("fallback"):
        starts.insert(0, "- (no line, operation, route or page of these stages falls in this unit: start from its "
                         "inbound operations)")
    return ["## Read the path of the stages taken further", "",
            f"This run reads the path of stages {', '.join(stages)} (process steps {', '.join(steps)}), not every "
            "line: follow \"When your prompt reads a stage's path\" in your instructions. Write rows only for those "
            "process steps.", "",
            "Where to start (derived by script from the lead's lifecycle and the code reader's findings):",
            "\n".join(starts) or "- (none found: list every file as not read, off this stage's path)", ""]


def main(argv):
    if not argv:
        sys.exit(__doc__)
    reg = pathlib.Path(argv[0]).resolve()
    import judges
    print(json.dumps(starting_points(reg, judges.workspace(reg, None), argv[1:] or None), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
