"""Defects a run finds in the kit itself, one line each in the register's kit-findings.md: a code from the fixed
list below, a file of the kit as its version marker lists it, the line, and the kit's version. Nothing else is
ever written. --list prints what each code means.


    python kit_findings.py "<register>" --code <one of the codes --list prints> --file <a file of the kit> --line <n>
    python kit_findings.py --list
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
FILE = "kit-findings.md"
MARKER = "KIT-VERSION.txt"

# The kit's own finding codes and what each means. A finding carries the code alone; the meaning is read here.
CODES = {
    "say-refused-fast-map-stop": "the fast map stop message the kit builds was refused by its own word check",
    "say-refused-map-stop": "the map stop message the kit builds was refused by its own word check",
    "say-refused-agents-lost": "the agents-lost stop message the kit builds was refused by its own word check",
    "say-refused-mapping-held": "the held-mapping choices message the kit builds was refused by its own word check",
    "message-refused": "a message the kit builds was refused by its own word check",
    "script-failed": "a script of the kit stopped with an error on the kit's own output",
    "report-wrong": "a line the kit builds for the person says something the run's own records contradict",
    "refusal-no-way-on": "a refusal of the kit named no step the session is allowed to take",
    "step-loops": "a step of the kit returned the same failure on every call",
    "instruction-missing": "the kit's instructions said nothing for the situation the run was in",
}


def version():
    """The installed kit's release as its version marker records it, `release-<n>` and nothing else; where the kit's
    changelog is one of its listed files, the marker must name the changelog's newest release. None otherwise."""
    import start
    listed = start.marker_files(HERE)
    if listed is None:
        return None
    try:
        head = (HERE / MARKER).read_text(encoding="utf-8").splitlines()[1].split()
    except (OSError, IndexError):
        return None
    if len(head) < 2 or not re.fullmatch(r"release-\d{1,3}(?:\.\d{1,3}){0,2}", head[1]):
        return None
    log = HERE / "CHANGELOG.md"
    if "CHANGELOG.md" in listed:
        if not log.is_file() or start._digest(log) != listed["CHANGELOG.md"]:
            return None
        newest = re.search(r"^## Release (\d+(?:\.\d+)*)", log.read_text(encoding="utf-8"), re.M)
        if not newest or f"release-{newest.group(1)}" != head[1]:
            return None
    return head[1]


def kit_file(name):
    """`name` when it is a file of the kit as its version marker lists it, else None."""
    import start
    if not name:
        return None
    try:
        name = pathlib.Path(name).resolve().relative_to(HERE).as_posix() if pathlib.Path(name).is_absolute() \
            else pathlib.PurePosixPath(name.replace("\\", "/")).as_posix()
    except ValueError:
        return None  # a path outside the kit
    if name.startswith("/") or ":" in name or ".." in name.split("/"):
        return None
    listed = start.marker_files(HERE)
    return name if listed is not None and name in listed and (HERE / name).is_file() else None


def refusal(code, file, line):
    """Why this finding cannot be written, or None."""
    import start
    if start.marker_files(HERE) is None or version() is None:
        return ("this copy of the kit has no version marker it can be checked against, so no finding can be "
                "written")
    if code not in CODES:
        return "the code is one of the kit's own finding codes (kit_findings.py --list); nothing else"
    if kit_file(file) is None:
        return "the file is a file of the kit, as its version marker lists it; nothing else"
    lines = len((HERE / kit_file(file)).read_bytes().splitlines())
    if not isinstance(line, int) or not 1 <= line <= lines:
        return f"the line is a line of that file of the kit, from 1 to {lines}"
    return None


def _lines(reg):
    p = pathlib.Path(reg) / FILE
    return [x for x in p.read_text(encoding="utf-8").splitlines() if x.startswith("- ")] if p.is_file() else []


def record(reg, code, file, line):
    """Append one finding, once: (the file's path, None) or (None, why it was refused). The same code, file and line
    is written once."""
    why = refusal(code, file, line)
    if why:
        return None, why
    file = kit_file(file)
    p = pathlib.Path(reg) / FILE
    key = f"- {code} | {file}:{line} |"
    if any(x.startswith(key) for x in _lines(reg)):
        return p, None
    new = not p.is_file()
    with p.open("a", encoding="utf-8") as f:
        if new:
            f.write("# Problems this run found in the kit itself\n\nPass each line on to whoever gives you the "
                    "kit.\n\n")
        f.write(f"{key} {version()}\n")
    return p, None


def count(reg):
    return len(_lines(reg))


def line(reg):
    """The report's line naming the file, or None when the run wrote none."""
    n = count(reg)
    if not n:
        return None
    p = (pathlib.Path(reg) / FILE).resolve()
    return (f"The run found {n} {'problem' if n == 1 else 'problems'} in the kit itself, written in {p}: one short "
            f"line each. Pass {'it' if n == 1 else 'each line'} on to whoever gives you the kit, so it is fixed "
            "in the next release.")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--list"]:
        for c, meaning in CODES.items():
            print(f"{c}: {meaning}")
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("register")
    ap.add_argument("--code", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--line", required=True, type=int)
    a = ap.parse_args(argv)
    if not pathlib.Path(a.register).is_dir():
        print("REFUSED: the first argument is the run's register folder. Nothing written.")
        return 2
    p, why = record(a.register, a.code, a.file, a.line)
    if why:
        print(f"REFUSED: {why}. Nothing written: record nothing else, and tell the person in plain words that the "
              "kit has a problem the run could not write down.")
        return 2
    print(f"WRITTEN: {p} ({count(a.register)} so far). Carry on with the run, or stop for the person; never change "
          "the kit's own files.")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # a name from a source never crashes a Windows console
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
