"""Say whether the run read the code its register cites.

Usage: python reading_check.py <register folder>

Every code location a register row cites (`path:line` or `path:first-last`) must have been opened by the run with the
Read tool, its lines inside the part that was read, or be the location of a fact in `fact-base.json` beside the
register, which the code reader produced. A location that is neither is NOT READ, and the run is not done.
`survey.csv` is not a register row: the entry points the survey lists are not owed a read.

The evidence is Claude Code's own record of the sessions, the transcripts it writes for every session and subagent,
never a list the run writes about itself. The run is every session that wrote into the register folder, with the
subagents it launched. A file shown by a shell command does not count: open code with Read. The transcripts are found
under `<config>/projects/<the workspace path with every other character a dash>`, where `<config>` is
CLAUDE_CONFIG_DIR or `~/.claude`, trying the register folder and each folder above it up to, not including, the home
folder or the drive's root, so no session started in the home folder, above it or at a drive's root is read;
BFO_TRANSCRIPTS names one such folder directly.
Exit status 0 only when every cited location is covered.

Unit mode, for a split run: python reading_check.py --unit <unit> [--ws <workspace>] <register folder>

Checks one reading unit of `units/units.csv`. Its tables are `units/<unit>/*.csv` except `files.csv`; its run is the
sessions of the flow worked now that themselves wrote into `units/<unit>/` with Write or Edit, by the tool's resolved
path, as the unit's reader or a fixer of it (provenance.py): never a re-read of an unmatched call, never a session
that only launched them, never by a shell command's text, so one unit's reader is never credited with another's
reading, nor with the judges'. Every cell of the unit's tables must be accounted for by those writes, and every writer
must be a `bfo-unit-reader` subagent, the kit's reader agent, which has no shell (provenance.py); each problem is
named and fails the unit. Code-reader facts count only in files the unit owes, so two units
cut from one deployable are not charged with each other's findings; a call, route, message or write the reader found
there must be cited by one of the unit's rows, or its file listed `not relevant` in `files.csv`. And every file the
unit owes (owed_files) must be read in full: every line inside the unit's Read calls (offset/limit; no limit
reads 2000 lines; parts that together cover the file count), and listed in `files.csv` as `cited` (a row cites it) or
`not relevant` with a reason. Each file falling short is named: not opened, partly read (with the lines not read), not
listed, listed cited but no row cites it, not relevant with no reason. In a flow read by stage with path reading
(path_reading.reading), a file on the path is owed an opening, not every line, and every line a row cites must still
have been read; a file off the path is listed `not read` with the reason `off this stage's path`, is never counted as
read, and no row may cite it.

The files a unit owes (owed_files, the one definition that units.py sizes by and readers.py lists in the reader's
prompt) are those with an extension of EXT below. Not owed: test files while OWE_TESTS is False (it is), and, because
they are not the service's own code, files
under a folder named in SKIP_DIRS (vendored packages, build output, generated code, version-control and tool folders),
minified files and lock files (SKIP_FILES), and binary files (a NUL byte in the first 8 KB). The workspace is --ws when
given; otherwise the nearest folder above the register in which a unit path exists, else the folder above `bfo-work`."""
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths as path_rule  # noqa: E402  (a unit's `paths` is a local name here)
import tables  # noqa: E402
import register_layout as layout  # noqa: E402

EXT =("java|go|cs|js|jsx|ts|tsx|py|kt|kts|clj|cljs|scala|rb|php|rs|c|cc|cpp|h|hpp|swift|ya?ml|xml|properties|sql|"
       "proto|razor|cshtml|json|gradle|toml|conf|ini|sh|ps1|tf|html|vue")
CITE = re.compile(r"(?<![\w./-])((?:[\w.@-]+/)+[\w.@-]+\.(?:" + EXT + r"))(?![\w-])(?::(\d+)(?:-(\d+))?)?")
# A further range of the same file: after `path:range`, each directly following ", n" or ", n-m" (a number
# that is not part of a word or a decimal). "; " separates citations, so it never starts a range.
MORE = re.compile(r", (\d+)(?:-(\d+))?(?![\w-])(?!\.\d)")
KIT_PATHS = ("method/", "register-template/", "reference/", "bfo-work/")
DEFAULT_LIMIT = 2000


def cited_in(text):
    out = []
    for m in CITE.finditer(text):
        path = m.group(1).replace("\\", "/")
        if path.startswith(KIT_PATHS):
            continue
        first = int(m.group(2)) if m.group(2) else None
        last = int(m.group(3)) if m.group(3) else first
        out.append((path, first, last))
        at = m.end()
        while first is not None and (more := MORE.match(text, at)):
            a = int(more.group(1))
            out.append((path, a, int(more.group(2)) if more.group(2) else a))
            at = more.end()
    return out


NOT_CHARGED = {"survey.csv"}  # the first look's inventory of services and entry points, not a register row
SET_ASIDE = "set-aside.csv"  # what the map leaves out: its citations are read, but touch no service


def citations(reg, skip=()):
    """Distinct (path lowercased, first, last) cited anywhere in the register's tables, except survey.csv: the
    survey lists where each service starts, and the files only it names are not owed a read. Tables named in
    `skip` (lowercased file names) are left out too."""
    got = set()
    for p in sorted(pathlib.Path(reg).glob("*.csv")):
        if p.name.lower() in NOT_CHARGED or p.name.lower() in skip:
            continue
        for path, a, b in cited_in(p.read_text(encoding="utf-8", errors="replace")):
            got.add((path.lower(), a, b))
    return got


def slug(path):
    return re.sub(r"[^A-Za-z0-9]", "-", str(pathlib.Path(path).resolve()))


def project_folders(reg, config=None, stop=None):
    named = os.environ.get("BFO_TRANSCRIPTS")
    if named:
        return [pathlib.Path(named)]
    home = pathlib.Path(config or os.environ.get("CLAUDE_CONFIG_DIR") or pathlib.Path.home() / ".claude")
    reg = pathlib.Path(reg).resolve()
    stop = pathlib.Path(stop or pathlib.Path.home()).resolve()
    # Sessions started in the home folder or above it, or at a drive's root, are never read: they are not this
    # run's workspace.
    below = []
    for d in (reg, *reg.parents):
        if d == stop or d in stop.parents or d == d.parent:
            break
        below.append(d)
    return [p for p in (home / "projects" / slug(d) for d in below) if p.is_dir()]


def tool_uses(path):
    """(name, input) of every tool call in transcript `path`, from its assistant records only: other records (an
    api-request-blob) replay the request body and would count each call again."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
                if d.get("type") != "assistant":
                    continue
                content = (d.get("message") or {}).get("content")
            except (ValueError, AttributeError):
                continue
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        yield b.get("name"), b.get("input") or {}


def writes_into(uses, reg):
    r = path_rule.norm(reg)
    for name, inp in uses:
        if name in ("Write", "Edit", "MultiEdit", "NotebookEdit") and path_rule.norm(inp.get("file_path", "")).startswith(r + "/"):
            return True
        if name in ("Bash", "PowerShell") and r in path_rule.norm(inp.get("command", "")).replace("//", "/"):
            return True
    return False


def run_sessions(folders, reg, wrote=None):
    """The run's transcripts: each that wrote into the register, and every subagent of a main session that did."""
    wrote = wrote or writes_into
    chosen = set()
    for folder in folders:
        for main in folder.glob("*.jsonl"):
            subs = list((folder / main.stem / "subagents").glob("*.jsonl"))
            if wrote(tool_uses(main), reg):
                chosen.add(main)
                chosen.update(subs)
            else:
                chosen.update(s for s in subs if wrote(tool_uses(s), reg))
    return sorted(chosen)


def sessions_by_id(reg, folders, wrote=None):
    """The run's sessions found by their ids wherever they were started (judges.run_session_files), outside
    `folders`: each that wrote into the register, and the subagents of each, as run_sessions takes them."""
    if os.environ.get("BFO_TRANSCRIPTS"):
        return []
    wrote = wrote or writes_into
    try:
        import judges
        mains = judges.run_session_files(reg)
    except Exception:  # noqa: BLE001  (no id list: only the register's own project folders are read)
        return []
    inside = [pathlib.Path(f).resolve() for f in folders]
    chosen = set()
    for main in mains:
        if pathlib.Path(main).parent.resolve() in inside:
            continue
        subs = list((main.parent / main.stem / "subagents").glob("*.jsonl"))
        if wrote(tool_uses(main), reg):
            chosen.add(main)
            chosen.update(subs)
        else:
            chosen.update(s for s in subs if wrote(tool_uses(s), reg))
    return sorted(chosen)


def read_results(path):
    """[(input, ok, message)] of every Read call in transcript `path`, each paired with its tool_result by
    tool_use_id: ok is False when the result is an error (the Read tool refused the file, a hook blocked it), and
    message is the result's own text. A call whose result is not in the transcript is counted as before (no error is
    recorded against it): only a result that says it failed is taken as a failure."""
    calls, results = [], {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
                content = (d.get("message") or {}).get("content")
            except (ValueError, AttributeError):
                continue
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict):
                    continue
                if d.get("type") == "assistant" and b.get("type") == "tool_use" and b.get("name") == "Read":
                    calls.append((b.get("id"), b.get("input") or {}))
                elif d.get("type") == "user" and b.get("type") == "tool_result":
                    c = b.get("content")
                    text = c if isinstance(c, str) else " ".join(
                        x.get("text", "") for x in c or [] if isinstance(x, dict))
                    results[b.get("tool_use_id")] = (not b.get("is_error"), text.strip())
    return [(inp, *results.get(tid, (True, ""))) for tid, inp in calls]


def reads(sessions):
    """{absolute path lowercased: [(first, last), ...]} from the Read calls in the sessions whose result is not an
    error: a Read the tool refused or a hook blocked returned nothing, so it covers no line."""
    got = {}
    for s in sessions:
        for inp, ok, _ in read_results(s):
            if not ok or not inp.get("file_path"):
                continue
            first = int(inp.get("offset") or 1)
            limit = int(inp.get("limit") or DEFAULT_LIMIT)
            got.setdefault(path_rule.norm(inp["file_path"]), []).append((first, first + limit - 1))
    return got


READ_BLOCKED = "read blocked"


def blocked(sessions):
    """{absolute path lowercased: the last failed result's own message} for every file each of whose Reads failed. Its
    cause is not guessed: the message is what the tool or the hook said."""
    tried, good = {}, set()
    for s in sessions:
        for inp, ok, msg in read_results(s):
            if not inp.get("file_path"):
                continue
            key = path_rule.norm(inp["file_path"])
            if ok:
                good.add(key)
            else:
                tried[key] = msg
    return {k: m for k, m in tried.items() if k not in good}


LEAD_KINDS = {"inbound_route", "outbound_http", "grpc_method", "grpc_call", "message_consumer", "message_producer",
              "message_publisher", "message_subscription", "durable_write"}


def fact_base(reg):
    """The code reader's facts, or None when it has not been run."""
    p = pathlib.Path(reg) / "fact-base.json"
    return json.loads(p.read_text(encoding="utf-8")).get("facts", []) if p.is_file() else None


def facts(fb):
    got = {}
    for f in fb or []:
        got.setdefault(path_rule.norm(f.get("file", "")), set()).add(int(f.get("line") or 0))
    return got


def _cites(cited, path, line):
    return any((path == c or path.endswith("/" + c)) and (a is None or a <= line <= b) for c, a, b in cited)


def fast_services(reg):
    """{service lower case} a fast map reads (go.services_read: the picked stages' closure), or None for a register
    that is not mapped fast, or when the go records no services."""
    try:
        import go
        s = go.load(reg) or {}
        if s.get("mapping") != "fast":
            return None
        got = go.services_read(reg, s)
    except Exception:  # noqa: BLE001  (no go or an older one: every cited service's findings are owed, as before)
        return None
    return None if got is None else {n.lower() for n in got}


def unaccounted_leads(reg, fb, cited):
    """Calls, routes, messages and writes the reader found in a service the register cites, that no row cites and
    set-aside.csv does not name: the absences a run settles by reading (reflexion models). A service is touched by
    a citation in any table but set-aside.csv: setting a part aside by citing one of its lines accounts for the
    leads it names and does not make the part one the map touches, so its other leads are not owed a read."""
    touched = citations(reg, skip={SET_ASIDE})
    services = {f.get("service") for f in fb if _cites(touched, path_rule.norm(f.get("file", "")), int(f.get("line") or 0))
                or any(path_rule.norm(f.get("file", "")).endswith("/" + c) or path_rule.norm(f.get("file", "")) == c
                       for c, _, _ in touched)}
    picked = fast_services(reg)
    if picked is not None:  # a fast map reads the picked stages' services only: the others' findings are not owed
        services = {s for s in services if (s or "").lower() in picked}
    aside = pathlib.Path(reg) / SET_ASIDE
    aside = {(p.lower(), a, b) for p, a, b in cited_in(aside.read_text(encoding="utf-8"))} if aside.is_file() else set()
    out = []
    for f in fb:
        path, line = path_rule.norm(f.get("file", "")), int(f.get("line") or 0)
        if f.get("kind") in LEAD_KINDS and f.get("service") in services \
                and not _cites(cited, path, line) and not _cites(aside, path, line):
            out.append(f"{f['kind']} {f.get('file')}:{line}")
    return sorted(set(out))


def no_record(folders, config=None):
    """What the done check says when it finds no session record of the run: where it looked, why a session's record
    can be elsewhere, and what to set BFO_TRANSCRIPTS to."""
    home = pathlib.Path(config or os.environ.get("CLAUDE_CONFIG_DIR") or pathlib.Path.home() / ".claude")
    looked = ", ".join(map(str, folders)) or "no transcript folder for this path"
    return (f"no session record of this run was found (looked in: {looked}). Claude Code keeps a session's record "
            "under the folder the session was started in, and only the register's folder and the folders above it "
            "are searched, so a session started outside the register's folder is not found. Run the kit in Claude "
            "Code started in the workspace, or set BFO_TRANSCRIPTS to the Claude Code project folder of the session "
            f"that ran the reading, {home / 'projects'}{os.sep}<the folder that session was started in, with every "
            "character other than a letter or a digit written as a dash>, and run the check again.")


class Result:
    def __init__(self, cited, covered, by_reader, missing, sessions, folders, leads):
        self.cited, self.covered, self.by_reader = cited, covered, by_reader
        self.missing, self.sessions, self.folders = missing, sessions, folders
        self.leads = leads
        self.unaccounted = len(leads or [])
        self.passed = sessions > 0 and not missing and leads == []
        self.note = ""  # why the code reader did not finish, when the first look recorded it

    def lines(self):
        if not self.sessions:
            return ["Reading: NOT READ: " + no_record(self.folders)]
        head = (f"Reading: {self.covered} of {self.cited} cited code locations covered "
                f"({self.covered - self.by_reader} opened by the run, {self.by_reader} from the code reader), "
                f"from {self.sessions} session record(s)")
        out = [head + (": ok" if not self.missing else
                       f": NOT READ: {len(self.missing)} location(s) cited but never opened by the run")]
        out += [f"  not read: {m}" for m in self.missing[:25]]
        if len(self.missing) > 25:
            out.append(f"  ... and {len(self.missing) - 25} more")
        if self.leads is None:
            out.append("Code reader: NOT RUN: " + (self.note or "no fact-base.json in the register folder; run the "
                                                   "code reader"))
        elif self.leads:
            out.append(f"Code reader: {len(self.leads)} finding(s) in the services this map touches, cited by no row "
                       "and not set aside: read each, then cite it in a row or set it aside with the reason")
            out += [f"  not accounted: {m}" for m in self.leads[:25]]
            if len(self.leads) > 25:
                out.append(f"  ... and {len(self.leads) - 25} more")
        else:
            out.append("Code reader: every finding in the services this map touches is cited or set aside: ok")
        return out


def check(reg, transcripts=None):
    reg = pathlib.Path(reg).resolve()
    folders = [pathlib.Path(transcripts)] if transcripts else project_folders(reg)
    sessions = run_sessions(folders, reg)
    if not transcripts:  # a session started in another folder is found by its id
        sessions = sorted(set(sessions) | set(sessions_by_id(reg, folders)))
    opened = reads(sessions)
    fb = fact_base(reg)
    extracted = facts(fb)
    cited = sorted(citations(reg), key=lambda c: (c[0], c[1] or 0))
    covered, by_reader, missing = _cover(cited, opened, extracted)
    leads = None if fb is None else unaccounted_leads(reg, fb, cited)
    r = Result(len(cited), covered, by_reader, missing, len(sessions), folders, leads)
    r.note = reader_note(reg)
    return r


def reader_note(reg):
    """Why the code reader did not finish on this computer, as the first look recorded it, or nothing."""
    p = pathlib.Path(reg) / layout.CODE_READER_NOTE
    return p.read_text(encoding="utf-8").strip() if p.is_file() else ""


def reader_missing(result):
    """Whether a failed reading check failed because the code reader did not run, not for cited code left unread."""
    return result.leads is None and result.sessions and not result.missing


def cause(result):
    """What a failed reading check says as its reason: the code reader that did not run, when that is why, else
    cited code the run did not read. run_status.report gives the same two reasons in its own words (CHECKS.md)."""
    if reader_missing(result):
        return "the code reader did not run on this computer" + (f" ({result.note})" if result.note else "")
    return "cited code not read by the run"


def _cover(cited, opened, extracted):
    """(covered, by the code reader, [locations not covered]) for the cited locations."""
    covered = by_reader = 0
    missing = []
    for path, first, last in cited:
        spans = [s for p, ss in opened.items() if p.endswith("/" + path) for s in ss]
        if path_rule.covered(first, last, spans):
            covered += 1
            continue
        lines = set().union(*[ls for p, ls in extracted.items() if p == path or p.endswith("/" + path)] or [set()])
        if lines and (first is None or any(first <= n <= last for n in lines)):
            covered += 1
            by_reader += 1
            continue
        missing.append(path + (f":{first}" + (f"-{last}" if last != first else "") if first else ""))
    return covered, by_reader, missing


# ---------------------------------------------------------------- unit mode (split run)
SKIP_DIRS = {"node_modules", "bower_components", "jspm_packages", "vendor", "third_party", "target", "build", "dist",
             "obj", "generated", "generated-sources", "generated-test-sources", "__pycache__", ".git", ".hg", ".svn",
             ".gradle", ".mvn", ".idea", ".vscode", ".venv", "venv", ".tox", ".next", ".nuxt", "coverage",
             ".terraform"}
SKIP_FILES = re.compile(r"(\.min\.[a-z]+|^package-lock\.json|^npm-shrinkwrap\.json)$", re.I)
SOURCE = re.compile(r"\.(?:" + EXT + r")$", re.I)
WRITERS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def writes_into_folder(uses, folder):
    """As writes_into, but a shell command naming `units/orders-10` is not a write into `units/orders-1`."""
    r = path_rule.norm(folder)
    edge = re.compile(re.escape(r) + r"(?![\w.-])")
    for name, inp in uses:
        if name in WRITERS and path_rule.norm(inp.get("file_path", "")).startswith(r + "/"):
            return True
        if name in ("Bash", "PowerShell") and edge.search(path_rule.norm(inp.get("command", "")).replace("//", "/")):
            return True
    return False


def _rel(p):
    p = str(p).replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.rstrip("/")


def unit_paths(reg, unit):
    """The unit's `paths` from units/units.csv, or None when the unit is not listed there."""
    p = pathlib.Path(reg) / layout.UNITS_CSV
    if not p.is_file():
        return None
    for row in tables.dicts(p, encoding="utf-8"):
        if (row.get("unit") or "").strip() == unit:
            return [_rel(x) for x in (row.get("paths") or "").split(";") if _rel(x)]
    return None


def workspace(reg, paths):
    root = layout.code_root(reg)  # where the survey read the code, before any folder above the register
    if root is not None and any((root / p).exists() for p in paths):
        return root
    for d in (reg, *reg.parents):
        if any((d / p).exists() for p in paths):
            return d
    return reg.parent.parent if reg.parent.name == "bfo-work" else reg.parent


def _binary(path):
    try:
        with open(path, "rb") as f:
            return b"\0" in f.read(8192)
    except OSError:
        return True


# Whether a unit owes its test code (survey.TEST: a tests folder, src/test, *Test.java, test_*.py, ...) like any other
# file. False: a reader reads the unit's production code in full, every line, and consults a test
# only where a behaviour in the code is unclear; a test file may be listed in files.csv as `not relevant`, reason
# `test code`. One switch: it sets what is sized (units.py), listed in the reader's prompt and checked, all at once.
OWE_TESTS = False


def is_test(rel):
    """A test file by survey.TEST, the survey's own rule, on its path from the workspace and on its name."""
    import survey
    return bool(survey.TEST.search(rel) or survey.TEST.search(rel.rsplit("/", 1)[-1]))


def owed_files(ws, paths, tests=None):
    """({relative path: absolute path}, [paths not found]): the files a reading unit owes, the one definition its
    sizing (units.py), its reader's prompt (readers.py) and this check all use. Every file under the unit's paths
    with an extension of EXT, but those under a folder in SKIP_DIRS, minified and lock files (SKIP_FILES), binary
    files, and, unless `tests` (default OWE_TESTS), test files (is_test)."""
    ws = pathlib.Path(ws)
    tests = OWE_TESTS if tests is None else tests
    got, absent = source_files(ws, paths)
    return ({r: a for r, a in got.items() if tests or not is_test(r)}, absent)


def source_files(ws, paths):
    """{relative path: absolute path} of the source files under the unit's paths, and the paths not found. Use
    owed_files, which applies the decision on test code."""
    got, absent = {}, []
    for p in paths:
        top = ws / p
        if top.is_file():
            cands = [top]
        elif top.is_dir():
            cands = []
            for d, dirs, names in os.walk(top):
                dirs[:] = sorted(x for x in dirs if x.lower() not in SKIP_DIRS)
                cands += [pathlib.Path(d) / n for n in sorted(names)]
        else:
            absent.append(p)
            continue
        for c in cands:
            if SOURCE.search(c.name) and not SKIP_FILES.search(c.name) and not _binary(c):
                got[c.relative_to(ws).as_posix()] = c
    return got, absent


def _line_count(path):
    data = pathlib.Path(path).read_bytes()
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def _gaps(first, last, spans):
    out, line = [], first
    for a, b in sorted(spans):
        if b < line:
            continue
        if a > last:
            break
        if a > line:
            out.append((line, a - 1))
        line = max(line, b + 1)
        if line > last:
            break
    if line <= last:
        out.append((line, last))
    return out


def _under(path, paths):
    return any(path == p or path.startswith(p + "/") for p in paths)


def _same_file(rel, c):
    return rel == c or rel.endswith("/" + c) or c.endswith("/" + rel)


class UnitResult(Result):
    def __init__(self, unit, base, files_total=0, files_full=0, problems=(), error=None, files_path=0, unread=()):
        super().__init__(base.cited, base.covered, base.by_reader, base.missing, base.sessions, base.folders,
                         base.leads)
        self.unit, self.error = unit, error
        self.files_total, self.files_full, self.problems = files_total, files_full, list(problems)
        self.files_path, self.unread = files_path, list(unread)  # path reading: never counted as read in full
        self.passed = self.passed and not self.problems and not error

    def lines(self):
        if self.error:
            return [f"Reading unit {self.unit}: NOT READ: {self.error}"]
        out = [f"Unit {self.unit}. " + x if i == 0 else x for i, x in enumerate(super().lines())]
        if not self.sessions:
            return out + [f"  {p}" for p in self.problems if p.startswith("provenance: ")][:50]
        head = f"Whole files: {self.files_full} of {self.files_total} files read in full"
        if self.files_path:
            head += f", {self.files_path} read along the stage's path (the rest of each named below, not read)"
        out.append(head + (", every file cited or set aside: ok" if not self.problems else
                           f": NOT READ: {len(self.problems)} file problem(s)"))
        out += [f"  {p}" for p in self.problems[:50]]
        if len(self.problems) > 50:
            out.append(f"  ... and {len(self.problems) - 50} more")
        out += [f"  {u}" for u in self.unread[:50]]
        if len(self.unread) > 50:
            out.append(f"  ... and {len(self.unread) - 50} more not read, off this stage's path")
        return out


def check_unit(reg, unit, transcripts=None, ws=None):
    """The reading check for one reading unit of a split run (see the module's docstring)."""
    reg = pathlib.Path(reg).resolve()
    folders = [pathlib.Path(transcripts)] if transcripts else project_folders(reg)
    paths = unit_paths(reg, unit)
    if paths is None:
        return UnitResult(unit, Result(0, 0, 0, [], 0, folders, None),
                          error=f"no unit '{unit}' in {reg / layout.UNITS_CSV}")
    udir = layout.unit_dir(reg, unit)
    import provenance  # noqa: E402  (it reads transcripts through judges.py, which imports this module)
    who = provenance.unit(reg, unit, transcripts=folders)
    sessions = [s.path for s in who.readers]
    opened = reads(sessions)
    stopped = blocked(sessions)
    ws = pathlib.Path(ws).resolve() if ws else workspace(reg, paths)
    low = [p.lower() for p in paths]
    wsn = path_rule.norm(ws) + "/"
    fb = fact_base(reg)
    mine = None
    if fb is not None:
        mine = []
        for f in fb:
            shown = _rel(f.get("file", ""))
            shown = shown[len(wsn):] if shown.lower().startswith(wsn) else shown
            if _under(shown.lower(), low):
                mine.append(dict(f, file=shown.lower(), shown=shown))
    cited = set()
    for p in sorted(udir.glob("*.csv")):
        if p.name.lower() != layout.FILES_CSV:
            cited.update((c.lower(), a, b) for c, a, b in cited_in(p.read_text(encoding="utf-8", errors="replace")))
    cited = sorted(cited, key=lambda c: (c[0], c[1] or 0))
    covered, by_reader, missing = _cover(cited, opened, facts(mine))

    listed = {}
    for row in tables.dicts(udir / layout.FILES_CSV, encoding="utf-8"):
        listed[_rel(row.get("path") or "").lower()] = ((row.get("status") or "").strip().lower(),
                                                       (row.get("reason") or "").strip())
    import path_reading  # path reading: a file off the stage's path is listed `not read`, never counted as read
    on_path = path_reading.reading(reg) == "path"
    off_path = {p for p, (s, r) in listed.items() if on_path and s == "not read" and path_reading.OFF_PATH in r}
    aside = {p for p, (s, _) in listed.items() if s == "not relevant"} | off_path
    leads = None
    if mine is not None:
        leads = sorted({f"{f['kind']} {f['shown']}:{int(f.get('line') or 0)}" for f in mine
                        if f.get("kind") in LEAD_KINDS and (OWE_TESTS or not is_test(f["shown"]))
                        and not _cites(cited, f["file"], int(f.get("line") or 0))
                        and f["file"] not in aside})

    files, absent = owed_files(ws, paths)
    problems = [f"provenance: {p}" for p in who.problems]
    problems += [f"unit path not found in the workspace {ws}: {p}" for p in absent]
    if not files and not absent:
        problems.append(f"no source files under the unit's paths in the workspace {ws}: {'; '.join(paths)}")
    full, path_read, unread = 0, 0, []
    for rel, absolute in sorted(files.items()):
        key = rel.lower()
        if key in off_path:  # listed off the stage's path: owes no reading, and no row may cite it
            if any(_same_file(key, c) for c, _, _ in cited):
                problems.append(f"listed not read (off this stage's path), yet a row cites it: {rel}")
            continue
        spans = [s for p, ss in opened.items() if p == path_rule.norm(absolute) or p.endswith("/" + key) for s in ss]
        n = _line_count(absolute)
        gaps = _gaps(1, n, spans) if n else []
        ranges = ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in gaps)
        why = next((m for p, m in stopped.items() if p == path_rule.norm(absolute) or p.endswith("/" + key)), None)
        if not spans and why is not None:
            problems.append(f"{READ_BLOCKED}: {rel}: every Read of it failed; the tool said: {why[:300]}. A reader "
                            "launched again meets the same: the person decides what to do")
        elif not spans:
            problems.append(f"not opened: {rel}")
        elif gaps and not on_path:
            problems.append(f"partly read: {rel}: lines {ranges} not read")
        elif gaps:  # path reading: read along the path, never counted as read in full; its other lines are named
            path_read += 1
            unread.append(f"not read: off this stage's path: {rel}: lines {ranges}")
        else:
            full += 1
        status, reason = listed.get(key, ("", ""))
        if status not in ("cited", "not relevant"):
            problems.append(f"not listed: {rel}" + (f" (status '{status}' is neither cited nor not relevant)"
                                                    if status else ""))
        elif status == "cited" and not any(_same_file(key, c) for c, _, _ in cited):
            problems.append(f"listed cited, no row cites it: {rel}")
        elif status == "not relevant" and not reason:
            problems.append(f"not relevant with no reason: {rel}")
        elif status == "not relevant" and spans and gaps:  # set aside only on a reading of the whole file
            problems.append(f"not relevant, but lines {ranges} were never read: read it whole, or list it not read, "
                            f"off this stage's path: {rel}")
    base = Result(len(cited), covered, by_reader, missing, len(sessions), folders, leads)
    return UnitResult(unit, base, len(files), full, problems, files_path=path_read, unread=unread)


def main(argv):
    if not argv:
        sys.exit(__doc__)
    args, unit, ws = list(argv), None, None
    for flag in ("--unit", "--ws"):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f"{flag} needs a value\n\n" + __doc__)
            value = args[i + 1]
            del args[i:i + 2]
            unit, ws = (value, ws) if flag == "--unit" else (unit, value)
    if len(args) != 1 or (ws and not unit):
        sys.exit(__doc__)
    r = check_unit(args[0], unit, ws=ws) if unit else check(args[0])
    print("\n".join(r.lines()))
    return 0 if r.passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
