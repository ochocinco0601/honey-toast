"""Say whether the run read the code its register cites.

Usage: python reading_check.py <register folder>

Every code location a register row cites (`path:line` or `path:first-last`) must have been opened by the run with the
Read tool, its lines inside the part that was read, or be the location of a fact in `fact-base.json` beside the
register, which the code reader produced. A location that is neither is NOT READ, and the run is not done.

The evidence is Claude Code's own record of the sessions, the transcripts it writes for every session and subagent,
never a list the run writes about itself. The run is every session that wrote into the register folder, with the
subagents it launched. A file shown by a shell command does not count: open code with Read. The transcripts are found
under `<config>/projects/<the workspace path with every other character a dash>`, where `<config>` is
CLAUDE_CONFIG_DIR or `~/.claude`, trying the register folder and each folder above it up to, not including, the home
folder or the drive's root, so no session started in the home folder, above it or at a drive's root is read;
BFO_TRANSCRIPTS names one such folder directly.
Exit status 0 only when every cited location is covered."""
import json
import os
import pathlib
import re
import sys

EXT = ("java|go|cs|js|jsx|ts|tsx|py|kt|kts|clj|cljs|scala|rb|php|rs|c|cc|cpp|h|hpp|swift|ya?ml|xml|properties|sql|"
       "proto|razor|cshtml|json|gradle|toml|conf|ini|sh|ps1|tf|html|vue")
CITE = re.compile(r"(?<![\w./-])((?:[\w.@-]+/)+[\w.@-]+\.(?:" + EXT + r"))(?![\w-])(?::(\d+)(?:-(\d+))?)?")
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
    return out


def citations(reg):
    """Distinct (path lowercased, first, last) cited anywhere in the register's tables."""
    got = set()
    for p in sorted(pathlib.Path(reg).glob("*.csv")):
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
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                content = (json.loads(line).get("message") or {}).get("content")
            except (ValueError, AttributeError):
                continue
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        yield b.get("name"), b.get("input") or {}


def _norm(p):
    return str(p).replace("\\", "/").lower().rstrip("/")


def writes_into(uses, reg):
    r = _norm(reg)
    for name, inp in uses:
        if name in ("Write", "Edit", "MultiEdit", "NotebookEdit") and _norm(inp.get("file_path", "")).startswith(r + "/"):
            return True
        if name in ("Bash", "PowerShell") and r in _norm(inp.get("command", "")).replace("//", "/"):
            return True
    return False


def run_sessions(folders, reg):
    """The run's transcripts: each that wrote into the register, and every subagent of a main session that did."""
    chosen = set()
    for folder in folders:
        for main in folder.glob("*.jsonl"):
            subs = list((folder / main.stem / "subagents").glob("*.jsonl"))
            if writes_into(tool_uses(main), reg):
                chosen.add(main)
                chosen.update(subs)
            else:
                chosen.update(s for s in subs if writes_into(tool_uses(s), reg))
    return sorted(chosen)


def reads(sessions):
    """{absolute path lowercased: [(first, last), ...]} from the Read calls in the sessions."""
    got = {}
    for s in sessions:
        for name, inp in tool_uses(s):
            if name != "Read" or not inp.get("file_path"):
                continue
            first = int(inp.get("offset") or 1)
            limit = int(inp.get("limit") or DEFAULT_LIMIT)
            got.setdefault(_norm(inp["file_path"]), []).append((first, first + limit - 1))
    return got


LEAD_KINDS = {"inbound_route", "outbound_http", "grpc_method", "grpc_call", "message_consumer", "message_producer",
              "message_publisher", "message_subscription", "durable_write"}


def fact_base(reg):
    """The code reader's facts, or None when it has not been run."""
    p = pathlib.Path(reg) / "fact-base.json"
    return json.loads(p.read_text(encoding="utf-8")).get("facts", []) if p.is_file() else None


def facts(fb):
    got = {}
    for f in fb or []:
        got.setdefault(_norm(f.get("file", "")), set()).add(int(f.get("line") or 0))
    return got


def _cites(cited, path, line):
    return any((path == c or path.endswith("/" + c)) and (a is None or a <= line <= b) for c, a, b in cited)


def unaccounted_leads(reg, fb, cited):
    """Calls, routes, messages and writes the reader found in a service the register cites, that no row cites and
    set-aside.csv does not name: the absences a run settles by reading (reflexion models)."""
    services = {f.get("service") for f in fb if _cites(cited, _norm(f.get("file", "")), int(f.get("line") or 0))
                or any(_norm(f.get("file", "")).endswith("/" + c) or _norm(f.get("file", "")) == c
                       for c, _, _ in cited)}
    aside = pathlib.Path(reg) / "set-aside.csv"
    aside = {(p.lower(), a, b) for p, a, b in cited_in(aside.read_text(encoding="utf-8"))} if aside.is_file() else set()
    out = []
    for f in fb:
        path, line = _norm(f.get("file", "")), int(f.get("line") or 0)
        if f.get("kind") in LEAD_KINDS and f.get("service") in services \
                and not _cites(cited, path, line) and not _cites(aside, path, line):
            out.append(f"{f['kind']} {f.get('file')}:{line}")
    return sorted(set(out))


def _covered(first, last, spans):
    if first is None:
        return bool(spans)
    line = first
    while line <= last:
        nxt = max((b for a, b in spans if a <= line <= b), default=None)
        if nxt is None:
            return False
        line = nxt + 1
    return True


class Result:
    def __init__(self, cited, covered, by_reader, missing, sessions, folders, leads):
        self.cited, self.covered, self.by_reader = cited, covered, by_reader
        self.missing, self.sessions, self.folders = missing, sessions, folders
        self.leads = leads
        self.unaccounted = len(leads or [])
        self.passed = sessions > 0 and not missing and leads == []

    def lines(self):
        if not self.sessions:
            return ["Reading: NOT READ: no session record of this run was found "
                    f"(looked in: {', '.join(map(str, self.folders)) or 'no transcript folder for this path'}). "
                    "Run the kit in Claude Code from the workspace, or name the folder in BFO_TRANSCRIPTS."]
        head = (f"Reading: {self.covered} of {self.cited} cited code locations covered "
                f"({self.covered - self.by_reader} opened by the run, {self.by_reader} from the code reader), "
                f"from {self.sessions} session record(s)")
        out = [head + (": ok" if not self.missing else
                       f": NOT READ: {len(self.missing)} location(s) cited but never opened by the run")]
        out += [f"  not read: {m}" for m in self.missing[:25]]
        if len(self.missing) > 25:
            out.append(f"  ... and {len(self.missing) - 25} more")
        if self.leads is None:
            out.append("Code reader: NOT RUN: no fact-base.json in the register folder; run the code reader")
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
    opened = reads(sessions)
    fb = fact_base(reg)
    extracted = facts(fb)
    cited = sorted(citations(reg), key=lambda c: (c[0], c[1] or 0))
    covered = by_reader = 0
    missing = []
    for path, first, last in cited:
        spans = [s for p, ss in opened.items() if p.endswith("/" + path) for s in ss]
        if _covered(first, last, spans):
            covered += 1
            continue
        lines = set().union(*[ls for p, ls in extracted.items() if p == path or p.endswith("/" + path)] or [set()])
        if lines and (first is None or any(first <= n <= last for n in lines)):
            covered += 1
            by_reader += 1
            continue
        missing.append(path + (f":{first}" + (f"-{last}" if last != first else "") if first else ""))
    leads = None if fb is None else unaccounted_leads(reg, fb, cited)
    return Result(len(cited), covered, by_reader, missing, len(sessions), folders, leads)


def main(argv):
    if not argv:
        sys.exit(__doc__)
    r = check(argv[0])
    print("\n".join(r.lines()))
    return 0 if r.passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
