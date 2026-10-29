"""Survey the repositories before any deep reading: each service's place, size, entry points and calls, by script.

Usage: python survey.py <register folder> [repository folder ...]

With no repository folders, the code rows of sources.csv name them (`repository`, from the workspace root, which is
two folders above the register folder). Writes survey.csv in the register folder and prints a summary for the plan.

A service is a folder holding a build manifest (pom.xml, build.gradle, package.json, go.mod, glide.yaml, Gopkg.toml, a
.csproj, pyproject.toml, setup.py, requirements.txt, Pipfile, Gemfile, Cargo.toml) with no build manifest below it and
some source code outside its tests, so a parent build file in a many-service repository is not counted as a service.
A repository with no such folder is one row: a service if it holds source code, otherwise "deployment or
configuration".

Lines are non-blank lines of source files; test lines are counted apart. Entry points are lines that start a program
(a main function, a start script, a container's command). A call is the name of another surveyed service written as
an address (http://name, name:port) in a service's files; queue and topic names are not found here, and the walk
reads them. Everything is counted, never estimated: the survey is what the plan's sizes rest on."""
import csv
import json
import pathlib
import re
import sys

MANIFESTS = ("pom.xml", "build.gradle", "build.gradle.kts", "package.json", "go.mod", "glide.yaml", "Gopkg.toml",
             "pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "Gemfile", "Cargo.toml")
SOURCE = {".java": "Java", ".kt": "Kotlin", ".groovy": "Groovy", ".scala": "Scala", ".go": "Go", ".js": "JavaScript",
          ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".py": "Python", ".cs": "C#", ".rb": "Ruby",
          ".rs": "Rust", ".php": "PHP", ".c": "C", ".cpp": "C++", ".swift": "Swift"}
CONFIG = (".yml", ".yaml", ".properties", ".json", ".env", ".conf", ".toml", ".xml", ".tf", ".ini")
SKIP = {".git", "node_modules", "vendor", "build", "dist", "target", "bin", "obj", "out", ".gradle", ".idea",
        "__pycache__", ".venv", "venv", "bower_components", "coverage"}
TEST = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|src/test)(/|$)|(_test\.go|Test\.java|Tests\.java|Test\.kt|"
                  r"\.test\.[jt]sx?|\.spec\.[jt]sx?|_test\.py|^test_.*\.py|Tests\.cs)$")
ENTRY = re.compile(r"public\s+static\s+void\s+main\s*\(|^func\s+main\s*\(\s*\)|if\s+__name__\s*==\s*['\"]__main__|"
                   r"static\s+(async\s+)?(void|int|Task)\s+Main\s*\(|^\s*(ENTRYPOINT|CMD)\s")
FIELDS = ("service", "repository", "path", "kind", "files", "lines", "test_lines", "languages", "entry_points",
          "calls", "called_by", "call_evidence")


def walk(folder):
    for p in sorted(folder.iterdir()):
        if p.name in SKIP or p.name.startswith(".") and p.is_dir():
            continue
        if p.is_dir():
            yield from walk(p)
        elif p.is_file():
            yield p


def has_manifest(d):
    return any((d / m).is_file() for m in MANIFESTS) or any(d.glob("*.csproj"))


def services_in(repo):
    """Folders of `repo` holding a build manifest with none below them."""
    dirs = [d for d in [repo, *(p for p in repo.rglob("*") if p.is_dir())]
            if not (set(d.relative_to(repo).parts) & SKIP) and has_manifest(d)]
    return [d for d in dirs if not any(o != d and d in o.parents for o in dirs)]


def nonblank(p):
    try:
        return sum(1 for line in p.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())
    except OSError:
        return 0


def describe(folder, root, others_of):
    files = [p for p in walk(folder)]
    lines = tests = 0
    langs = {}
    entries = []
    for p in files:
        rel = p.relative_to(folder).as_posix()
        lang = SOURCE.get(p.suffix.lower())
        if lang:
            n = nonblank(p)
            if TEST.search(rel) or TEST.search(p.name):
                tests += n
            else:
                lines += n
                langs[lang] = langs.get(lang, 0) + n
        if lang or p.name == "Dockerfile":
            try:
                for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if ENTRY.search(line):
                        entries.append(f"{p.relative_to(root).as_posix()}:{i}")
                        break
            except OSError:
                pass
        if p.name == "package.json":
            try:
                pkg = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                start = (pkg.get("scripts") or {}).get("start") or pkg.get("main")
                if start:
                    entries.append(f"{p.relative_to(root).as_posix()} (start: {start})")
            except ValueError:
                pass
    return files, lines, tests, langs, entries


def main(argv):
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
        names = [r.get("repository", "").strip() for r in rows if r.get("kind", "").strip() == "code"]
        repos = [(root / n).resolve() for n in dict.fromkeys(n for n in names if n)]
    missing = [r for r in repos if not r.is_dir()]
    if missing:
        sys.exit("not a folder: " + ", ".join(map(str, missing)))
    common = pathlib.Path(*min((r.parts for r in repos), key=len)[:-1]) if len(repos) > 1 else repos[0].parent
    root = root if all(root in r.parents for r in repos) else common

    units = []
    for repo in repos:
        found = [(d, describe(d, root, set())) for d in services_in(repo)]
        found = [(d, x) for d, x in found if x[1] > 0] or [(repo, describe(repo, root, set()))]
        for d, described in found:
            units.append({"service": d.name, "repository": repo.name, "dir": d,
                          "path": d.relative_to(root).as_posix(), "_described": described,
                          "kind": "service" if described[1] > 0 else "deployment or configuration"})
    names = {u["service"] for u in units if u["kind"] == "service"}
    for u in units:
        files, lines, tests, langs, entries = u.pop("_described")
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
                try:
                    text = p.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    continue
                for i, line in enumerate(text, 1):
                    for m in pat.finditer(line):
                        callee = m.group(1) or m.group(2) or m.group(3)
                        if callee not in calls:
                            calls.append(callee)
                            evidence.append(f"{callee} at {p.relative_to(root).as_posix()}:{i}")
        u["calls"] = "; ".join(sorted(calls))
        u["call_evidence"] = "; ".join(evidence)
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
    print(f"written: {reg / 'survey.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
