"""Survey the repositories before any deep reading: each service's place, size, entry points and calls, by script.

Usage: python survey.py <register folder> [repository folder ...]

With no repository folders, the code rows of sources.csv name them (`repository`, from the workspace root, which is
two folders above the register folder). Writes survey.csv in the register folder and prints a summary for the plan.
When the repositories are not inside the workspace, the folder that holds them is the one every path is written from,
and it is recorded in code-root.txt (relative to the workspace) so every reader and judge is told that folder.

A service is a folder holding a build manifest (pom.xml, build.gradle, package.json, go.mod, glide.yaml, Gopkg.toml, a
.csproj, pyproject.toml, setup.py, requirements.txt, Pipfile, Gemfile, Cargo.toml) with no build manifest below it and
some source code outside its tests, so a parent build file in a many-service repository is not counted as a service.
A repository with no such folder is one row: a service if it holds source code, otherwise "deployment or
configuration".

A service is named after its folder. When that folder's name is a generic one (src, app, main, ...) and sits deeper
than directly in the repository, as when the build file is in src/cartservice/src, the name is the nearest folder
above it, inside the repository, whose name is not: cartservice. A generic folder directly in the repository
(myapp/server) keeps its own name, since other code addresses it by that name. No two rows share a name: a clash
falls back to the folder's own name, then to its path; a clash neither settles stops the survey, naming the folders.

Lines are non-blank lines of source files; test lines are counted apart. Entry points are lines that start a program
(a main function, a start script, a container's command). A call is the name of another surveyed service written as
an address (http://name, name:port) in a service's files; queue and topic names are not found here, and the walk
reads them. Everything is counted, never estimated: the survey is what the plan's sizes rest on.

Files are listed and opened through Windows' extended-length form, so a file whose full path passes the 260-character
limit is read like any other. A file that still cannot be read, for any reason, is never counted as empty in silence:
it is named with the reason in the `unread_files` column of its service's row and in the printed summary, and that
service's size is short by it."""
import csv
import json
import os
import pathlib
import re
import sys

MANIFESTS = ("pom.xml", "build.gradle", "build.gradle.kts", "package.json", "go.mod", "glide.yaml", "Gopkg.toml",
             "pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "Gemfile", "Cargo.toml")
SOURCE = {".java": "Java", ".kt": "Kotlin", ".groovy": "Groovy", ".scala": "Scala", ".go": "Go", ".js": "JavaScript",
          ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".py": "Python", ".cs": "C#", ".rb": "Ruby",
          ".rs": "Rust", ".php": "PHP", ".c": "C", ".cpp": "C++", ".swift": "Swift",
          ".cbl": "COBOL", ".cob": "COBOL", ".cobol": "COBOL", ".cpy": "COBOL", ".jcl": "JCL", ".pli": "PL/I",
          ".pl1": "PL/I", ".pls": "PL/SQL", ".pks": "PL/SQL", ".pkb": "PL/SQL", ".pck": "PL/SQL", ".plsql": "PL/SQL",
          ".asm": "Assembler", ".rexx": "REXX", ".rex": "REXX", ".jsp": "JSP", ".gvy": "Groovy", ".vb": "Visual Basic",
          ".vbs": "VBScript", ".bas": "Visual Basic", ".pl": "Perl", ".pm": "Perl"}
CONFIG = (".yml", ".yaml", ".properties", ".json", ".env", ".conf", ".toml", ".xml", ".tf", ".ini")
SKIP = {".git", "node_modules", "vendor", "build", "dist", "target", "bin", "obj", "out", ".gradle", ".idea",
        "__pycache__", ".venv", "venv", "bower_components", "coverage"}
TEST = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|src/test)(/|$)|(_test\.go|Test\.java|Tests\.java|Test\.kt|"
                  r"\.test\.[jt]sx?|\.spec\.[jt]sx?|_test\.py|^test_.*\.py|Tests\.cs)$")
ENTRY = re.compile(r"public\s+static\s+void\s+main\s*\(|^func\s+main\s*\(\s*\)|if\s+__name__\s*==\s*['\"]__main__|"
                   r"static\s+(async\s+)?(void|int|Task)\s+Main\s*\(|^\s*(ENTRYPOINT|CMD)\s")
# what runs on a mainframe or in a database: a COBOL program, a PL/I main procedure, a JCL job card, a stored procedure
MAINFRAME_ENTRY = re.compile(r"^.{0,7}\s*PROCEDURE\s+DIVISION\b|\bPROC\s+OPTIONS\s*\(\s*MAIN\b|^//\S+\s+JOB\b|"
                             r"^\s*CREATE\s+(OR\s+REPLACE\s+)?(PROCEDURE|PACKAGE\s+BODY|FUNCTION|TRIGGER)\b", re.I)
GENERIC = {"src", "source", "sources", "app", "main", "server", "code"}  # whole folder names, never part of one
FIELDS = ("service", "repository", "path", "kind", "files", "lines", "test_lines", "languages", "entry_points",
          "calls", "called_by", "call_evidence", "unread_files")


def extended(p):
    """`p` as Windows must be given it past the 260-character path limit: `\\\\?\\` and the absolute path (UNC paths
    as `\\\\?\\UNC\\server\\share`). Unchanged elsewhere. Only for touching a file: every path written out stays plain."""
    s = str(p)
    if os.name != "nt" or s.startswith("\\\\?\\"):
        return pathlib.Path(s)
    s = os.path.abspath(s)
    return pathlib.Path("\\\\?\\UNC\\" + s[2:] if s.startswith("\\\\") else "\\\\?\\" + s)


def unread(skipped, p, error):
    """Name a file or folder that could not be read, with the reason, so it is never counted as empty in silence."""
    if skipped is not None:
        skipped.append((pathlib.Path(p), error.strerror or type(error).__name__))


def walk(folder, skipped=None):
    """Every file under `folder` outside SKIP, as plain paths, listed through the extended form."""
    try:
        children = sorted(extended(folder).iterdir())
    except OSError as e:
        unread(skipped, folder, e)
        return
    for c in children:
        p = pathlib.Path(folder) / c.name
        if c.name in SKIP or c.name.startswith(".") and c.is_dir():
            continue
        if c.is_dir():
            yield from walk(p, skipped)
        elif c.is_file():
            yield p


def has_manifest(d):
    d = extended(d)
    return any((d / m).is_file() for m in MANIFESTS) or any(d.glob("*.csproj"))


def services_in(repo):
    """Folders of `repo` holding a build manifest with none below them."""
    long = extended(repo)
    dirs = [d for d in [repo, *(repo / p.relative_to(long) for p in long.rglob("*") if p.is_dir())]
            if not (set(d.relative_to(repo).parts) & SKIP) and has_manifest(d)]
    return [d for d in dirs if not any(o != d and d in o.parents for o in dirs)]


def named(d, repo):
    """The service's name: its folder's name, or, when that is a generic one (src, app, ...) sitting deeper than
    directly in the repository, the nearest folder above it, inside the repository, whose name is not. A generic
    folder directly in the repository (myapp/server) is the service's own name, and so is the repository's."""
    f = d
    while f != repo and f.parent != repo and f.name.lower() in GENERIC:
        f = f.parent
    return f.name


def unique(units, root):
    """Give every row a name no other row has: a clashing name falls back to the folder's own name, then to its path
    with `-` for `/`. A clash none of these settles stops the survey, naming the folders."""
    tries = [lambda u: u["service"], lambda u: u["dir"].name,
             lambda u: u["dir"].relative_to(root).as_posix().replace("/", "-")]
    level = {id(u): 0 for u in units}
    while True:
        seen = {}
        for u in units:
            seen.setdefault(u["service"], []).append(u)
        clashes = [group for group in seen.values() if len(group) > 1]
        if not clashes:
            return
        for group in clashes:
            movable = [u for u in group if level[id(u)] < len(tries) - 1]
            if not movable:
                sys.exit("two folders would be surveyed under one name, " + group[0]["service"] + ": "
                         + ", ".join(u["path"] for u in group) + ". Survey them separately or rename one.")
            for u in movable:
                level[id(u)] += 1
                u["service"] = tries[level[id(u)]](u)


def read(p, skipped=None):
    """The file's text, or None when it cannot be read (and then it is named in `skipped`)."""
    try:
        return extended(p).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        unread(skipped, p, e)
        return None


def nonblank(p, skipped=None):
    return sum(1 for line in (read(p, skipped) or "").splitlines() if line.strip())


def describe(folder, root, others_of):
    skipped = []
    files = [p for p in walk(folder, skipped)]
    lines = tests = 0
    langs = {}
    entries = []
    for p in files:
        rel = p.relative_to(folder).as_posix()
        lang = SOURCE.get(p.suffix.lower())
        if lang:
            n = nonblank(p, skipped)
            if TEST.search(rel) or TEST.search(p.name):
                tests += n
            else:
                lines += n
                langs[lang] = langs.get(lang, 0) + n
        if lang or p.name == "Dockerfile":
            for i, line in enumerate((read(p, skipped) or "").split("\n"), 1):  # numbered as the Read tool numbers them
                if ENTRY.search(line) or MAINFRAME_ENTRY.search(line):
                    entries.append(f"{p.relative_to(root).as_posix()}:{i}")
                    break
        if p.name == "package.json":
            try:
                pkg = json.loads(read(p, skipped) or "{}")
                start = (pkg.get("scripts") or {}).get("start") or pkg.get("main")
                if start:
                    entries.append(f"{p.relative_to(root).as_posix()} (start: {start})")
            except ValueError:
                pass
    return files, lines, tests, langs, entries, skipped


def record_locations(reg, repos):
    """Write each repository folder the survey was given into sources.csv's `location`, on the code row naming that
    repository whose location is blank, so every later script finds the code where it is. A register whose
    sources.csv has no location column (an earlier kit) is left as it is: code-root.txt still records the folder."""
    import tables
    p = pathlib.Path(reg) / "sources.csv"
    if not p.is_file():
        return
    rows, whole = tables.read_rows(p)
    with p.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        header = next(csv.reader(f), [])
    if not whole or "location" not in header or "repository" not in header:
        return
    by_name = {r.name.lower(): r.as_posix() for r in repos}
    changed = False
    for r in rows:
        name = pathlib.PurePath((r.get("repository") or "").strip().replace("\\", "/")).name.lower()
        if (r.get("kind") or "").strip() == "code" and name in by_name and not (r.get("location") or "").strip():
            r["location"] = by_name[name]
            changed = True
    if changed:
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)


def main(argv):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # run with -I, the script's folder is not on it
    import run_lock  # a folder that is not a register (the answers folder, say) is refused, naming the registers
    run_lock.refuse_unless_register(argv)
    if not argv:
        sys.exit(__doc__)
    reg = pathlib.Path(argv[0]).resolve()
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import run_lock  # the register is written by one run at a time
    run_lock.guard(reg)
    root = reg.parent.parent
    if len(argv) > 1:
        repos = [pathlib.Path(a).resolve() for a in argv[1:]]
    else:
        import tables
        rows, whole = tables.read_rows(reg / "sources.csv")  # UTF-8, with or without a byte order mark, or cp1252
        if not whole:
            sys.exit("sources.csv: part of it could not be read. Save it as UTF-8 text and run the survey again.")
        bad = [i for i, r in enumerate(rows, 2) if None in r or (r.get("kind", "").strip() == "code"
                                                                and not (r.get("repository") or "").strip())]
        if bad:
            sys.exit(f"sources.csv rows {', '.join(map(str, bad))}: a code row with no repository, or more fields than "
                     "the header (quote any field holding a comma). Fix them and run the survey again.")
        # a code row's folder: its `location` (absolute, or from the workspace) where recorded, else its name there
        names = [(r.get("location") or "").strip() or r.get("repository", "").strip()
                 for r in rows if r.get("kind", "").strip() == "code"]
        repos = [(root / n).resolve() for n in dict.fromkeys(n for n in names if n)]
    missing = [r for r in repos if not r.is_dir()]
    if missing:
        sys.exit("not a folder: " + ", ".join(r.as_posix() for r in missing) + ". Record where each code repository "
                 "is: its folder in sources.csv's location column (a full path, or from the workspace "
                 f"{root.as_posix()}), or run the survey with the repository folders named.")
    import register_layout as layout
    found = layout.holding_folder(root, repos)
    if found is None:
        sys.exit("the repositories are not in one folder (" + ", ".join(r.as_posix() for r in repos) + "): every "
                 "citation starts with its repository's folder name, so put the repositories side by side in one "
                 "folder (or all under the workspace) and run the survey again.")
    if len(argv) > 1:
        record_locations(reg, repos)
    mark = reg / layout.CODE_ROOT
    if found != root:  # every later agent is told this folder: the code the survey read is where they read it
        mark.write_text(pathlib.Path(os.path.relpath(found, root)).as_posix() + "\n", encoding="utf-8")
    elif mark.is_file():
        mark.unlink()
    root = found

    units = []
    for repo in repos:
        found = [(d, describe(d, root, set())) for d in services_in(repo)]
        found = [(d, x) for d, x in found if x[1] > 0] or [(repo, describe(repo, root, set()))]
        for d, described in found:
            # a folder with no build manifest and no entry point (deployment files and a helper script) is not a service
            runs = has_manifest(d) or bool(described[4])
            units.append({"service": named(d, repo), "repository": repo.name, "dir": d,
                          "path": d.relative_to(root).as_posix(), "_described": described,
                          "kind": "service" if described[1] > 0 and runs else "deployment or configuration"})
    unique(units, root)
    names = {u["service"] for u in units if u["kind"] == "service"}
    for u in units:
        files, lines, tests, langs, entries, skipped = u.pop("_described")
        u.update(files=len(files), lines=lines, test_lines=tests,
                 languages="; ".join(f"{k} {v}" for k, v in sorted(langs.items(), key=lambda kv: -kv[1])),
                 entry_points="; ".join(entries[:3]))
        calls, evidence = [], []
        others = sorted(names - {u["service"]})
        if others:
            alt = "|".join(map(re.escape, others))
            pat = re.compile(r"(?:https?://|//)(" + alt + r")(?![A-Za-z0-9_-])"
                             r"|\b(" + alt + r"):\d{2,5}\b"
                             r"|[Hh]ost(?:name)?\W{0,4}[\"'](" + alt + r")[\"']")
            for p in files:
                if u["kind"] != "service" or not (SOURCE.get(p.suffix.lower()) or p.suffix.lower() in CONFIG):
                    continue
                if TEST.search(p.relative_to(u["dir"]).as_posix()):
                    continue
                text = read(p, skipped)
                if text is None:
                    continue
                for i, line in enumerate(text.split("\n"), 1):
                    for m in pat.finditer(line):
                        callee = m.group(1) or m.group(2) or m.group(3)
                        if callee not in calls:
                            calls.append(callee)
                            evidence.append(f"{callee} at {p.relative_to(root).as_posix()}:{i}")
        u["calls"] = "; ".join(sorted(calls))
        u["call_evidence"] = "; ".join(evidence)
        u["unread_files"] = "; ".join(dict.fromkeys(f"{p.relative_to(root).as_posix()} ({why})"
                                                    for p, why in skipped))
    for u in units:
        u["called_by"] = "; ".join(sorted(v["service"] for v in units
                                          if u["service"] in v["calls"].split("; ")))
    with (reg / "survey.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(units)

    svc = [u for u in units if u["kind"] == "service"]
    total = sum(u["lines"] for u in units)
    print(f"Survey of {len(repos)} repositories: {len(svc)} services, "
          f"{len(units) - len(svc)} deployment or configuration folders; "
          f"{total} lines of source, {sum(u['test_lines'] for u in units)} more of tests, "
          f"{sum(u['files'] for u in units)} files.")
    for u in sorted(units, key=lambda u: -u["lines"]):
        print(f"- {u['service']} ({u['kind']}, {u['path']}): {u['lines']} lines"
              + (f", {u['languages']}" if u["languages"] else "")
              + (f"; calls {u['calls']}" if u["calls"] else "")
              + (f"; called by {u['called_by']}" if u["called_by"] else ""))
    unread_all = [x for u in units for x in u["unread_files"].split("; ") if x]
    if unread_all:
        print(f"The survey could not read {len(unread_all)} file(s), so the sizes, entry points and calls above are "
              f"short by them (survey.csv, column unread_files): {'; '.join(unread_all)}")
    print(f"written: {reg / 'survey.csv'}")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
